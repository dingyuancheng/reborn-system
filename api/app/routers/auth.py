import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import User, UserLoginLog
from app.redis_client import create_session, delete_session, get_session, kick_user_sessions
from app.schemas.auth_schemas import (
    LoginRequest, LoginResponse, LogoutResponse, ServerConfigResponse,
)
from app.schemas.user_schemas import UserOut
from app.security import verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _extract_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return ""


def _detect_device_type(user_agent: str) -> str:
    if not user_agent:
        return "desktop"
    ua = user_agent.lower()
    mobile_keywords = (
        "android", "iphone", "ipad", "ipod", "windows phone",
        "blackberry", "mobile", "webos", "symbian", "opera mini",
        "opera mobi", "iemobile", "kindle", "silk", "meego",
        "maemo", "bada", "tizen", "ucweb", "mqqbrowser",
        "micromessenger", "alipayclient", "dingtalk", "feishu", "lark",
        "okhttp", "capacitor", "cordova", "reactnative", "flutter",
    )
    if any(k in ua for k in mobile_keywords):
        return "mobile"
    return "desktop"


def _extract_device_info(user_agent: str) -> str:
    if not user_agent:
        return "未知"
    import re
    ua = user_agent.lower()

    def _ver(regex_pattern: str) -> str:
        m = re.search(regex_pattern, user_agent, re.IGNORECASE)
        if m:
            return f" {m.group(1)}"
        return ""

    doubao_v = _ver(r"doubao/([\d.]+)")
    quark_v = _ver(r"quark/([\d.]+)")
    uc_v = _ver(r"ucbrowser/([\d.]+)")
    maxthon_v = _ver(r"maxthon/([\d.]+)")
    qq_v = _ver(r"qqbrowser/([\d.]+)")
    wx_v = _ver(r"micromessenger/([\d.]+)")
    edge_v = _ver(r"edg/([\d.]+)")
    opera_v = _ver(r"opr/([\d.]+)")
    firefox_v = _ver(r"firefox/([\d.]+)")
    chrome_v = _ver(r"chrome/([\d.]+)")
    safari_v = _ver(r"version/([\d.]+)")
    okhttp_v = _ver(r"okhttp/([\d.]+)")

    # 优先匹配特定品牌浏览器（这些 UA 里通常也包含 chrome，必须先判断）
    if "doubao" in ua:
        return f"豆包浏览器{doubao_v}"
    if "quark" in ua:
        return f"夸克浏览器{quark_v}"
    if "ucbrowser" in ua or " ucbrowser" in ua:
        return f"UC浏览器{uc_v}"
    if "360" in ua or "qihoobook" in ua or "se 2.x" in ua:
        return "360浏览器"
    if "lbbrowser" in ua:
        return "猎豹浏览器"
    if "theworld" in ua:
        return "世界之窗浏览器"
    if "maxthon" in ua:
        return f"傲游浏览器{maxthon_v}"
    if "sogou" in ua:
        return "搜狗浏览器"
    if "qqbrowser" in ua:
        return f"QQ浏览器{qq_v}"
    if "micromessenger" in ua:
        return f"微信内置浏览器{wx_v}"
    if "alipayclient" in ua:
        return "支付宝内置浏览器"
    if "dingtalk" in ua:
        return "钉钉内置浏览器"
    if "feishu" in ua or "lark" in ua:
        return "飞书内置浏览器"

    # 移动端 App
    if "android" in ua:
        return "Android App"
    if "iphone" in ua or "ipad" in ua:
        return "iOS App"
    if "capacitor" in ua:
        return "Capacitor WebView"

    # 桌面浏览器（注意顺序：Edge 基于 Chrome，要先判 Edge）
    if "edg/" in ua:
        return f"Edge 浏览器{edge_v}"
    if "opr/" in ua or "opera" in ua:
        return f"Opera 浏览器{opera_v}"
    if "firefox" in ua:
        return f"Firefox 浏览器{firefox_v}"
    if "chrome" in ua or "crios" in ua:
        return f"Google Chrome{chrome_v}"
    if "safari" in ua:
        return f"Safari 浏览器{safari_v}"

    # 调试工具
    if "postman" in ua:
        return "Postman"
    if "curl" in ua:
        return "curl"
    if "python-requests" in ua or "httpx" in ua:
        return "Python 脚本"
    if "okhttp" in ua:
        return f"OkHttp{okhttp_v}"

    return "Web Browser"


async def _write_login_log(
    db: AsyncSession,
    *,
    username: str,
    user_id: Any = None,
    nickname: str | None = None,
    login_result: int = 1,
    fail_reason: str | None = None,
    request: Request | None = None,
) -> None:
    ip = _extract_client_ip(request) if request else ""
    user_agent = request.headers.get("user-agent", "") if request else ""
    device_info = _extract_device_info(user_agent)
    log = UserLoginLog(
        user_id=user_id,
        username=username,
        nickname=nickname,
        login_result=login_result,
        fail_reason=fail_reason,
        ip=ip,
        user_agent=user_agent[:1000] if user_agent else None,
        device_info=device_info,
    )
    db.add(log)
    await db.commit()


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.username == payload.username, User.deleted == False)
    )
    user = result.scalar_one_or_none()

    password_ok = False
    if user and user.password:
        password_ok = verify_password(payload.password, user.password)

    if user is None or not password_ok:
        await _write_login_log(
            db, username=payload.username, login_result=0,
            fail_reason="用户名或密码错误", request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if user.status != 1:
        await _write_login_log(
            db, username=payload.username, user_id=user.id,
            nickname=user.nickname, login_result=0,
            fail_reason="账号已被禁用", request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    if user.ban_flag:
        await _write_login_log(
            db, username=payload.username, user_id=user.id,
            nickname=user.nickname, login_result=0,
            fail_reason=f"账号已被封禁，解封时间：{user.ban_time or '永久'}，原因：{user.ban_reason or '未说明'}",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"账号已被封禁，解封时间：{user.ban_time or '永久'}，原因：{user.ban_reason or '未说明'}",
        )

    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    device_info = _extract_device_info(user_agent)
    device_type = _detect_device_type(user_agent)

    await db.execute(
        update(User).where(User.id == user.id).values(
            last_login_ip=client_ip,
            last_login_time=func.now(),
        )
    )
    await db.commit()
    await db.refresh(user)

    user_out = UserOut.model_validate(user)

    login_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
    session_payload: dict[str, Any] = {
        "userId": str(user.id),
        "username": user.username,
        "nickname": user.nickname or user.username,
        "avatar": user.avatar or "",
        "familyId": str(user.family_id) if user.family_id else None,
        "adminFlag": user.admin_flag,
        "banFlag": user.ban_flag,
        "ip": client_ip,
        "device": device_info,
        "deviceType": device_type,
        "userAgent": user_agent[:500] if user_agent else "",
        "loginTime": login_time_str,
        "lastActiveTime": login_time_str,
    }
    session_id = await create_session(session_payload)

    await kick_user_sessions(
        user_id=str(user.id),
        exclude_session_id=session_id,
        device_type=device_type,
        reason="账号已在其他设备登录",
    )

    await _write_login_log(
        db, username=user.username, user_id=user.id,
        nickname=user.nickname or user.username, login_result=1,
        request=request,
    )

    return LoginResponse(
        message="登录成功",
        session_id=session_id,
        user=user_out,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: dict[str, Any] = Depends(get_current_user),
    x_session_id: str = Header(None),
):
    sid = x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="缺少会话标识")
    await delete_session(sid)
    return LogoutResponse()


@router.get("/me", response_model=UserOut)
async def me(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == current_user["userId"], User.deleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserOut.model_validate(user)


@router.get("/session-info")
async def session_info(current_user: dict[str, Any] = Depends(get_current_user)):
    return current_user


@router.get("/server-config", response_model=ServerConfigResponse)
async def server_config():
    return ServerConfigResponse()