'use strict'

import { removeToken } from './api.js'

const COLLAPSED_KEY = 'cp_sidebar_collapsed'

export function initSidebar() {
  const sidebar     = document.getElementById('sidebar')
  const overlay     = document.getElementById('sidebar-overlay')
  const hamburger   = document.getElementById('hamburger')
  const collapseBtn = document.getElementById('sidebar-collapse-btn')
  const collapseIcon = document.getElementById('sidebar-collapse-icon')

  if (!sidebar) return

  const isDesktop = () => window.innerWidth >= 768

  function setCollapsed(collapsed) {
    sidebar.classList.toggle('sidebar--collapsed', collapsed)
    localStorage.setItem(COLLAPSED_KEY, collapsed ? '1' : '0')
    if (collapseIcon) {
      collapseIcon.className = collapsed
          ? 'ti ti-layout-sidebar-left-expand'
          : 'ti ti-layout-sidebar-left-collapse'
    }
  }

  function openMobile() {
    sidebar.classList.add('sidebar--open')
    if (overlay) overlay.classList.add('sidebar-overlay--visible')
    document.body.style.overflow = 'hidden'
  }

  function closeMobile() {
    sidebar.classList.remove('sidebar--open')
    if (overlay) overlay.classList.remove('sidebar-overlay--visible')
    document.body.style.overflow = ''
  }

  if (hamburger) {
    hamburger.addEventListener('click', () => {
      if (sidebar.classList.contains('sidebar--open')) closeMobile()
      else openMobile()
    })
  }

  if (overlay) overlay.addEventListener('click', closeMobile)

  if (collapseBtn) {
    collapseBtn.addEventListener('click', () => {
      const willCollapse = !sidebar.classList.contains('sidebar--collapsed')
      setCollapsed(willCollapse)
    })
  }

  // Al hacer clic en cualquier parte del sidebar colapsado también lo expande
  sidebar.addEventListener('click', (e) => {
    if (
        isDesktop() &&
        sidebar.classList.contains('sidebar--collapsed') &&
        !e.target.closest('#sidebar-collapse-btn')
    ) {
      setCollapsed(false)
    }
  })

  const wasCollapsed = localStorage.getItem(COLLAPSED_KEY) === '1'
  if (isDesktop() && wasCollapsed) setCollapsed(true)

  window.addEventListener('resize', () => {
    if (isDesktop()) closeMobile()
  })

  ensureSidebarLogout()
  bindLogout()
  injectAdminItems()
  highlightActiveItem()
}


function ensureSidebarLogout() {
  const userBlock = document.querySelector('.sidebar__user')
  if (!userBlock || userBlock.querySelector('.sidebar__logout')) return

  const button = document.createElement('button')
  button.type = 'button'
  button.className = 'sidebar__logout sidebar__label'
  button.id = 'logout-btn-sidebar'
  button.setAttribute('aria-label', 'Cerrar sesion')
  button.setAttribute('title', 'Cerrar sesion')
  button.dataset.logout = 'true'
  button.innerHTML = '<i class="ti ti-logout" aria-hidden="true"></i>'
  userBlock.appendChild(button)
}

function bindLogout() {
  const buttons = document.querySelectorAll('[data-logout], #logout-btn-sidebar, #logout-btn-mobile, #logout-btn-desktop, #logout-btn')
  buttons.forEach(button => {
    if (button.dataset.logoutBound === 'true') return
    button.dataset.logoutBound = 'true'
    button.addEventListener('click', () => {
      removeToken()
      window.location.href = '/pages/login.html'
    })
  })
}

function injectAdminItems() {
  const token = sessionStorage.getItem('cp_token')
  if (!token) return
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (payload.role !== 'admin') return
  } catch { return }

  const nav = document.querySelector('.sidebar__nav')
  if (!nav || nav.querySelector('[href="usuarios.html"]')) return

  const divider = nav.querySelector('.sidebar__divider')
  const item = document.createElement('a')
  item.href = 'usuarios.html'
  item.className = 'sidebar__item'
  item.setAttribute('aria-label', 'Usuarios')
  item.innerHTML = '<i class="ti ti-users-group" aria-hidden="true"></i><span class="sidebar__label">Usuarios</span>'
  nav.insertBefore(item, divider)
}

function highlightActiveItem() {
  const current = window.location.pathname.split('/').pop()
  document.querySelectorAll('.sidebar__item').forEach(item => {
    const href = item.getAttribute('href') || ''
    if (href.includes(current) && current !== '') {
      item.classList.add('sidebar__item--active')
    } else {
      item.classList.remove('sidebar__item--active')
    }
  })
}