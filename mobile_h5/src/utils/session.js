export function getSession() {
  const params = new URLSearchParams(window.location.search)
  const session = params.get('session')
  if (session) {
    localStorage.setItem('session_token', session)
  }
  return localStorage.getItem('session_token') || ''
}

export function getApiBase() {
  return window.location.origin
}