<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="left">
      <div class="content">
        <div class="logo-big">REBORN</div>
        <h2>Reborn System<br />个人管理后台</h2>
        <p>为自己搭一个顺手的管理面板，权限、数据、日常事务，一目了然。</p>
        <div class="features">
          <div><span class="dot"></span>极简权限体系，自己用不啰嗦</div>
          <div><span class="dot"></span>清爽的数据看板，想看什么自己定</div>
          <div><span class="dot"></span>模块化设计，功能按需增减</div>
          <div><span class="dot"></span>开源可改，想怎么折腾都行</div>
        </div>
      </div>
    </div>

    <!-- 右侧登录区 -->
    <div class="right">
      <div class="header">
        <h3>账户登录</h3>
        <p>请输入您的账户信息以继续</p>
      </div>
      <el-form
        :model="form"
        :rules="rules"
        ref="formRef"
        label-position="top"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名 / 邮箱"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
          />
        </el-form-item>
        <div class="form-row">
          <label><input type="checkbox" checked /> 保持登录状态</label>
          <a href="javascript:void(0)" @click="notifyTodo">忘记密码？</a>
        </div>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="login-btn"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>
      <div class="divider">其他登录方式</div>
      <div class="socials">
        <a href="javascript:void(0)" @click="notifyTodo" title="GitHub">🐙</a>
        <a href="javascript:void(0)" @click="notifyTodo" title="微信">💬</a>
        <a href="javascript:void(0)" @click="notifyTodo" title="钉钉">📋</a>
      </div>
      <div class="copyright">© 2026 Reborn System</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = ref({ username: '', password: '' })

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function notifyTodo() {
  ElMessage.info('暂未开发')
}

async function handleLogin() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.login(form.value.username, form.value.password)
      ElMessage.success('登录成功')
      const redirect = (route.query.redirect as string) || '/dashboard'
      router.push(redirect)
    } catch (e: any) {
      if (e?.config) return
      ElMessage.error(e?.message || '登录失败，请稍后重试')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.login-page {
  min-height: 100vh;
  display: flex;
  color: #1f2937;
}

/* 左侧品牌区 */
.left {
  flex: 1;
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 60px;
  color: #fff;
  position: relative;
  overflow: hidden;
}
.left::before {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  top: -100px;
  left: -100px;
}
.left::after {
  content: '';
  position: absolute;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.04);
  bottom: -80px;
  right: -60px;
}
.left .content {
  position: relative;
  z-index: 1;
  max-width: 520px;
}
.left .logo-big {
  font-size: 56px;
  font-weight: 800;
  letter-spacing: 4px;
  margin-bottom: 24px;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}
.left h2 {
  font-size: 32px;
  font-weight: 600;
  line-height: 1.4;
  margin-bottom: 20px;
}
.left p {
  font-size: 15px;
  line-height: 1.8;
  opacity: 0.88;
}
.left .features {
  margin-top: 40px;
  display: grid;
  gap: 14px;
}
.left .features div {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  opacity: 0.9;
}
.left .features .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fff;
  opacity: 0.8;
}

/* 右侧登录区 */
.right {
  width: 520px;
  background: #fff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 60px;
}
.right .header {
  margin-bottom: 40px;
}
.right .header h3 {
  font-size: 26px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}
.right .header p {
  font-size: 14px;
  color: #6b7280;
}

/* 覆盖 Element Plus 表单项间距 */
:deep(.el-form-item) {
  margin-bottom: 20px;
}
:deep(.el-form-item__label) {
  font-size: 13px;
  color: #374151;
  font-weight: 500;
  padding-bottom: 8px;
}
:deep(.el-input__wrapper) {
  height: 44px;
  border-radius: 8px;
  background: #f9fafb;
  box-shadow: 0 0 0 1px #e5e7eb inset;
  transition: all 0.2s;
}
:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #d1d5db inset;
}
:deep(.el-input__wrapper.is-focus) {
  background: #fff;
  box-shadow: 0 0 0 1px #3b82f6 inset, 0 0 0 3px rgba(59, 130, 246, 0.1);
}
:deep(.el-input__inner) {
  font-size: 14px;
  color: #1f2937;
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
  font-size: 13px;
}
.form-row label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #6b7280;
  cursor: pointer;
  user-select: none;
}
.form-row a {
  color: #3b82f6;
  text-decoration: none;
}
.form-row a:hover {
  text-decoration: underline;
}

.login-btn {
  width: 100%;
  height: 46px;
  background: #111827 !important;
  border: none !important;
  border-radius: 8px !important;
  color: #fff !important;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 4px;
  transition: all 0.2s;
}
.login-btn:hover {
  background: #1f2937 !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.divider {
  margin: 28px 0 20px;
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
  position: relative;
}
.divider::before,
.divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 42%;
  height: 1px;
  background: #e5e7eb;
}
.divider::before {
  left: 0;
}
.divider::after {
  right: 0;
}
.socials {
  display: flex;
  gap: 12px;
  justify-content: center;
}
.socials a {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  text-decoration: none;
  transition: all 0.2s;
  font-size: 18px;
}
.socials a:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}
.copyright {
  margin-top: 36px;
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
}
</style>