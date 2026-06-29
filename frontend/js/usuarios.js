'use strict'

import { usersAPI } from './api.js'
import {
  showAlert, showSpinner, hideSpinner,
  renderSkeletonRows, animateTableRows,
  renderEmptyState, openModal, closeModal,
  getInitials, debounce, requireAuth, escapeHtml
} from './utils.js'

let allUsers = []
let editingId = null
let currentUserId = null

function roleLabel(role) {
  return role === 'admin' ? 'Administrador' : 'Comercial'
}

function isAdminToken() {
  const token = sessionStorage.getItem('cp_token')
  if (!token) return false

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    currentUserId = Number(payload.sub)
    return payload.role === 'admin'
  } catch {
    return false
  }
}

export function initUsers() {
  if (!requireAuth()) return

  if (!isAdminToken()) {
    window.location.href = '/pages/dashboard.html'
    return
  }

  loadUsers()
  bindSearch()
  bindCreateForm()
  bindEditForm()
  bindModalClose()

  document.getElementById('new-user-btn')?.addEventListener('click', openCreateModal)
}

async function loadUsers() {
  const tbody = document.getElementById('users-tbody')
  if (!tbody) return

  renderSkeletonRows(tbody, 3)

  try {
    allUsers = await usersAPI.getAll()
    renderTable(allUsers)
  } catch (err) {
    showAlert(err.message, 'error')
    renderEmptyState(
      tbody.closest('.card') || tbody.parentElement,
      'Error al cargar usuarios',
      'No se pudo obtener la lista de usuarios.',
      'ti-users-group'
    )
  }
}

function renderTable(users) {
  const tbody = document.getElementById('users-tbody')
  const count = document.getElementById('users-count')
  if (!tbody) return

  if (count) count.textContent = `${users.length} usuario${users.length !== 1 ? 's' : ''}`

  if (!users.length) {
    tbody.innerHTML = ''
    renderEmptyState(
      tbody.closest('.card') || tbody.parentElement,
      'Sin usuarios',
      'Crea el primer usuario con el botón de arriba.',
      'ti-users-group'
    )
    return
  }

  tbody.innerHTML = users.map(user => {
    const name = user.name || 'Sin nombre'
    const email = user.email || ''
    const isCurrentUser = Number(user.id) === currentUserId

    return `
      <tr>
        <td>
          <div class="users-table__person">
            <div class="users-table__avatar">${escapeHtml(getInitials(name || email) || 'U')}</div>
            <div>
              <div class="users-table__name">${escapeHtml(name)}</div>
              <div class="users-table__email">${escapeHtml(email)}</div>
            </div>
          </div>
        </td>
        <td>
          <span class="badge ${user.role === 'admin' ? 'badge--warning' : 'badge--info'}">
            ${roleLabel(user.role)}
          </span>
        </td>
        <td>
          <div class="users-table__actions">
            <button class="btn btn--sm btn--secondary" data-user-edit="${user.id}" aria-label="Editar usuario">
              <i class="ti ti-edit btn__icon" aria-hidden="true"></i>
            </button>
            <button class="btn btn--sm btn--danger" data-user-delete="${user.id}" ${isCurrentUser ? 'disabled' : ''} aria-label="Eliminar usuario">
              <i class="ti ti-trash btn__icon" aria-hidden="true"></i>
            </button>
          </div>
        </td>
      </tr>`
  }).join('')

  tbody.querySelectorAll('[data-user-edit]').forEach(btn => {
    btn.addEventListener('click', () => openEditModal(Number(btn.dataset.userEdit)))
  })

  tbody.querySelectorAll('[data-user-delete]').forEach(btn => {
    btn.addEventListener('click', () => deleteUser(Number(btn.dataset.userDelete)))
  })

  animateTableRows(tbody)
}

function bindSearch() {
  const input = document.getElementById('user-search')
  if (!input) return

  input.addEventListener('input', debounce(() => {
    const q = input.value.toLowerCase().trim()
    const filtered = q
      ? allUsers.filter(user =>
          (user.name || '').toLowerCase().includes(q) ||
          (user.email || '').toLowerCase().includes(q) ||
          roleLabel(user.role).toLowerCase().includes(q))
      : allUsers
    renderTable(filtered)
  }, 250))
}

function bindCreateForm() {
  const btn = document.getElementById('create-user-submit')
  if (!btn) return

  btn.addEventListener('click', async () => {
    const name = document.getElementById('cu-name').value.trim()
    const email = document.getElementById('cu-email').value.trim()
    const password = document.getElementById('cu-password').value
    const role = document.getElementById('cu-role').value

    if (!name || !email || !password) {
      showAlert('Nombre, correo y contraseña son obligatorios.', 'warning')
      return
    }

    if (password.length < 8) {
      showAlert('La contraseña debe tener al menos 8 caracteres.', 'warning')
      return
    }

    showSpinner(btn, 'Creando...')
    try {
      await usersAPI.create({ name, email, password, role })
      showAlert('Usuario creado correctamente.', 'success')
      closeModal('create-user-modal')
      document.getElementById('create-user-form').reset()
      await loadUsers()
    } catch (err) {
      showAlert(err.message, 'error')
    } finally {
      hideSpinner(btn)
    }
  })
}

function bindEditForm() {
  const btn = document.getElementById('edit-user-submit')
  if (!btn) return

  btn.addEventListener('click', async () => {
    if (!editingId) return

    const name = document.getElementById('eu-name').value.trim()
    const email = document.getElementById('eu-email').value.trim()
    const role = document.getElementById('eu-role').value
    const newPassword = document.getElementById('eu-password').value

    if (!name || !email) {
      showAlert('Nombre y correo son obligatorios.', 'warning')
      return
    }

    if (newPassword && newPassword.length < 8) {
      showAlert('La contraseña debe tener al menos 8 caracteres.', 'warning')
      return
    }

    const payload = { name, email, role }
    if (newPassword) payload.new_password = newPassword

    showSpinner(btn, 'Guardando...')
    try {
      await usersAPI.update(editingId, payload)
      showAlert('Usuario actualizado correctamente.', 'success')
      closeModal('edit-user-modal')
      editingId = null
      await loadUsers()
    } catch (err) {
      showAlert(err.message, 'error')
    } finally {
      hideSpinner(btn)
    }
  })
}

function bindModalClose() {
  document.querySelectorAll('[data-close-modal]').forEach(el => {
    el.addEventListener('click', () => {
      closeModal(el.dataset.closeModal)
      if (el.dataset.closeModal === 'create-user-modal') {
        document.getElementById('create-user-form')?.reset()
      }
      if (el.dataset.closeModal === 'edit-user-modal') {
        editingId = null
        document.getElementById('edit-user-form')?.reset()
      }
    })
  })

  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', event => {
      if (event.target === backdrop) {
        closeModal(backdrop.id)
        editingId = null
      }
    })
  })
}

function openCreateModal() {
  document.getElementById('create-user-form')?.reset()
  openModal('create-user-modal')
  document.getElementById('cu-name')?.focus()
}

function openEditModal(id) {
  const user = allUsers.find(item => Number(item.id) === Number(id))
  if (!user) return

  editingId = id
  document.getElementById('eu-id').value = user.id
  document.getElementById('eu-name').value = user.name || ''
  document.getElementById('eu-email').value = user.email || ''
  document.getElementById('eu-role').value = user.role || 'user'
  document.getElementById('eu-password').value = ''
  openModal('edit-user-modal')
  document.getElementById('eu-name')?.focus()
}

async function deleteUser(id) {
  const user = allUsers.find(item => Number(item.id) === Number(id))
  if (!user) return

  if (Number(user.id) === currentUserId) {
    showAlert('No puedes eliminar tu propio usuario.', 'warning')
    return
  }

  if (!confirm(`¿Eliminar a "${user.name || user.email}"? Esta acción no se puede deshacer.`)) return

  try {
    await usersAPI.delete(id)
    showAlert('Usuario eliminado correctamente.', 'success')
    await loadUsers()
  } catch (err) {
    showAlert(err.message, 'error')
  }
}
