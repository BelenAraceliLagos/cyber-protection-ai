'use strict'

/* ── DATES ── */
export function formatDate(isoString) {
  if (!isoString) return '—'
  return new Date(isoString).toLocaleDateString('es-CL', {
    day: '2-digit', month: '2-digit', year: 'numeric'
  })
}

export function formatDateTime(isoString) {
  if (!isoString) return '—'
  return new Date(isoString).toLocaleString('es-CL', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

export function timeAgo(isoString) {
  if (!isoString) return '—'
  const diff = Date.now() - new Date(isoString).getTime()
  const mins  = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days  = Math.floor(diff / 86400000)
  if (mins  <  1) return 'Hace un momento'
  if (mins  < 60) return `Hace ${mins} min`
  if (hours < 24) return `Hace ${hours}h`
  if (days  <  2) return 'Ayer'
  return formatDate(isoString)
}

/* ── CURRENCY ── */
export function formatCLP(amount) {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency', currency: 'CLP', maximumFractionDigits: 0
  }).format(amount)
}

/* ── SAFE HTML ── */
export function escapeHtml(value = '') {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  }[char]))
}

export function escapeAttr(value = '') {
  return escapeHtml(value)
}

/* ── ALERTS ── */
let alertContainer = null

function getAlertContainer() {
  if (!alertContainer) {
    alertContainer = document.getElementById('alert-container')
    if (!alertContainer) {
      alertContainer = document.createElement('div')
      alertContainer.id = 'alert-container'
      alertContainer.className = 'alert-container'
      document.body.appendChild(alertContainer)
    }
  }
  return alertContainer
}

export function showAlert(message, type = 'success', duration = 4000) {
  const icons = {
    success: 'ti-circle-check',
    error:   'ti-alert-circle',
    warning: 'ti-alert-triangle',
    info:    'ti-info-circle'
  }

  const el = document.createElement('div')
  el.className = `alert alert--${type}`
  el.innerHTML = `
    <i class="ti ${icons[type] || icons.info} alert__icon" aria-hidden="true"></i>
    <span class="alert__text">${escapeHtml(message)}</span>
    <span class="alert__close" aria-label="Cerrar"><i class="ti ti-x"></i></span>
  `

  const container = getAlertContainer()
  container.appendChild(el)

  el.querySelector('.alert__close').addEventListener('click', () => dismissAlert(el))

  if (duration > 0) {
    setTimeout(() => dismissAlert(el), duration)
  }
}

export function dismissAlert(el) {
  if (!el || el.classList.contains('alert--exit')) return
  el.classList.add('alert--exit')
  el.addEventListener('animationend', () => el.remove(), { once: true })
}

/* ── SPINNER ── */
export function showSpinner(btn, label = 'Cargando...') {
  btn.dataset.originalHtml = btn.innerHTML
  btn.innerHTML = `<i class="ti ti-refresh btn__icon" aria-hidden="true"></i> ${label}`
  btn.classList.add('btn--loading')
  btn.disabled = true
}

export function hideSpinner(btn) {
  btn.innerHTML = btn.dataset.originalHtml || btn.innerHTML
  btn.classList.remove('btn--loading')
  btn.disabled = false
}

/* ── SKELETON TABLE ── */
export function renderSkeletonRows(tbody, cols = 4, rows = 5) {
  const widths = [65, 50, 40, 35, 55, 45]
  tbody.innerHTML = Array.from({ length: rows }, () => `
    <tr class="table--loading">
      ${Array.from({ length: cols }, (_, i) => `
        <td>
          <span class="table__skel skeleton" style="width:${widths[(i + Math.floor(Math.random()*3)) % widths.length]}%"></span>
        </td>`).join('')}
    </tr>`).join('')
}

export function animateTableRows(tbody) {
  const rows = tbody.querySelectorAll('tr')
  rows.forEach((row, i) => {
    row.style.animation = `rowEnter .35s var(--ease-out) ${i * 50}ms both`
  })
}

/* ── MODAL ── */
export function openModal(modalId) {
  const el = document.getElementById(modalId)
  if (el) {
    el.classList.add('modal-backdrop--visible')
    document.body.style.overflow = 'hidden'
  }
}

export function closeModal(modalId) {
  const el = document.getElementById(modalId)
  if (el) {
    el.classList.remove('modal-backdrop--visible')
    document.body.style.overflow = ''
  }
}

/* ── EMPTY STATE ── */
export function renderEmptyState(container, title, desc, iconClass = 'ti-folder-off') {
  container.innerHTML = `
    <div class="empty-state page-enter">
      <div class="empty-state__icon">
        <i class="ti ${iconClass}" aria-hidden="true"></i>
      </div>
      <p class="empty-state__title">${escapeHtml(title)}</p>
      <p class="empty-state__desc">${escapeHtml(desc)}</p>
    </div>`
}

/* ── AUTH GUARD ── */
export function requireAuth() {
  const token = sessionStorage.getItem('cp_token')
  if (!token) {
    window.location.href = '/pages/login.html'
    return false
  }
  return true
}

/* ── DEBOUNCE ── */
export function debounce(fn, delay = 300) {
  let timer
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

/* ── INITIALS ── */
export function getInitials(name = '') {
  return name.trim().split(' ').slice(0, 2).map(w => w[0]?.toUpperCase()).join('')
}
