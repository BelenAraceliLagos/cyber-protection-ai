'use strict'

import { authAPI, setToken, removeToken } from './api.js'
import { showAlert, showSpinner, hideSpinner, requireAuth } from './utils.js'

export function initLogin() {
  const form       = document.getElementById('login-form')
  const emailEl    = document.getElementById('login-email')
  const passEl     = document.getElementById('login-password')
  const submitBtn  = document.getElementById('login-submit')
  const togglePass = document.getElementById('toggle-password')
  const backdrop   = document.getElementById('login-modal')
  const openBtn    = document.getElementById('open-login-modal')
  const closeBtn   = document.getElementById('close-login-modal')

  if (!form) return

  if (sessionStorage.getItem('cp_token')) {
    window.location.href = '/pages/dashboard.html'
    return
  }

  const openModal  = () => { backdrop?.classList.add('modal-backdrop--visible'); emailEl?.focus() }
  const closeModal = () => backdrop?.classList.remove('modal-backdrop--visible')

  openBtn?.addEventListener('click', openModal)
  closeBtn?.addEventListener('click', closeModal)
  backdrop?.addEventListener('click', (e) => { if (e.target === backdrop) closeModal() })
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal() })

  if (togglePass && passEl) {
    togglePass.addEventListener('click', () => {
      const isText = passEl.type === 'text'
      passEl.type = isText ? 'password' : 'text'
      togglePass.querySelector('i').className = isText ? 'ti ti-eye' : 'ti ti-eye-off'
    })
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault()

    const email    = emailEl?.value.trim()
    const password = passEl?.value

    if (!email || !password) {
      showAlert('Ingresa tu correo y contraseña.', 'warning')
      return
    }

    showSpinner(submitBtn, 'Ingresando...')

    try {
      const data = await authAPI.login(email, password)
      setToken(data.access_token)
      window.location.href = '/pages/dashboard.html'
    } catch (err) {
      showAlert(err.message || 'Credenciales incorrectas.', 'error')
    } finally {
      hideSpinner(submitBtn)
    }
  })
}

export function initLogout() {
  const btn = document.getElementById('logout-btn')
  if (!btn) return

  btn.addEventListener('click', () => {
    removeToken()
    window.location.href = '/pages/login.html'
  })
}

export function loadUserInfo() {
  requireAuth()
  const raw = sessionStorage.getItem('cp_token')
  if (!raw) return

  try {
    const payload = JSON.parse(atob(raw.split('.')[1]))
    const nameEl  = document.getElementById('sidebar-username')
    const roleEl  = document.getElementById('sidebar-role')
    const initEl  = document.getElementById('sidebar-initials')

    if (nameEl)  nameEl.textContent  = payload.name  || payload.email || 'Usuario'
    if (roleEl)  roleEl.textContent  = payload.role  === 'admin' ? 'Administrador' : 'Comercial'
    if (initEl)  initEl.textContent  = (payload.name || payload.email || 'U').substring(0, 2).toUpperCase()
  } catch {
    /* token malformed — ignore */
  }
}
