'use strict'

import { usersAPI } from './api.js'
import {
  showAlert, showSpinner, hideSpinner,
  renderSkeletonRows, animateTableRows,
  renderEmptyState, openModal, closeModal,
  getInitials, debounce, requireAuth
} from './utils.js'

let allUsers   = []
let editingId  = null

export function initUsers() {
  if (!requireAuth()) return

  const token = sessionStorage.getItem('cp_token')
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (payload.role !== 'admin') {
      window.location.href = '/pages/dashboard.html'
      return
    }
  } catch {
    window.location.href = '/pages/login.html'
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

  renderSkeletonRows(tbody, 4)

  try {
    allUsers = await usersAPI.getAll()
    renderTable(allUsers)
  } catch (err) {
    showAlert(err.message, 'error')
    renderEmptyState(
      tbody.closest('.card') || tbody.parentElement,
      'Error al cargar usuarios',
      'No se pudo conectar con el servidor.',
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
    renderEmptyState(
      tbody.closest('.card') || tbody.parentElement,
      'Sin usuarios',
      'Crea el primer usuario con el botón de arriba.',
      'ti-users-group'
    )
    return
  }

  tbody.innerHTML = users.map(u => `
    <tr>
      <td>
        <div style="display:flex;align-items:center;gap:10px">
          <div style="width:32px;height:32px;border-radius:50%;background:var(--cp-info-bg);
            display:flex;align-items:center;justify-content:center;
            font-size:11px;font-weight:600;color:var(--cp-blue-main);flex-shrink:0">
            ${getInitials(u.name || u.email)}
          </div>
          <div>
            <div style="font-weight:500;color:var(--cp-blue-main)">${u.name || '—'}</div>
            <div style="font-size:11px;color:var(--cp-text-muted)">${u.email}</div>
          </div>
        </div>
      </td>
      <td>
        <span class="badge ${u.role === 'admin' ? 'badge--warning' : 'badge--info'}">
          ${u.role === 'admin' ? 'Administrador' : 'Comercial'}
        </span>
      </td>
      <td>
        <span class="badge ${u.is_active ? 'badge--success' : 'badge--neutral'}">
          ${u.is_active ? 'Activo' : 'Desactivado'}
        </span>
      </td>
      <td>
        <div style="display:flex;gap:6px">
          <button class="btn btn--sm btn--secondary" onclick="editUser(${u.id})" aria-label="Editar">
            <i class="ti ti-edit btn__icon" aria-hidden="true"></i>
          </button>
          <button class="btn btn--sm ${u.is_active ? 'btn--danger' : 'btn--secondary'}"
            onclick="toggleActive(${u.id}, ${!u.is_active})"
            aria-label="${u.is_active ? 'Desactivar' : 'Activar'}">
            <i class="ti ${u.is_active ? 'ti-user-off' : 'ti-user-check'} btn__icon" aria-hidden="true"></i>
          </button>
        </div>
      </td>
    </tr>`).join('')

  animateTableRows(tbody)
}

function bindSearch() {
  const input = document.getElementById('user-search')
  if (!input) return

  input.addEventListener('input', debounce(() => {
    const q = input.value.toLowerCase().trim()
    const filtered = q
      ? allUsers.filter(u =>
          (u.name  || '').toLowerCase().includes(q) ||
          (u.email || '').toLowerCase().includes(q))
      : allUsers
    renderTable(filtered)
  }, 250))
}

function bindCreateForm() {
  const btn = document.getElementById('create-user-submit')
  if (!btn) return

  btn.addEventListener('click', async () => {
    const name     = document.getElementById('cu-name').value.trim()
    const email    = document.getElementById('cu-email').value.trim()
    const password = document.getElementById('cu-password').value
    const roleName = document.getElementById('cu-role').value

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
      await usersAPI.create({ name, email, password, role_name: roleName })
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

    const name        = document.getElementById('eu-name').value.trim()
    const roleName    = document.getElementById('eu-role').value
    const isActive    = document.getElementById('eu-status').value === 'true'
    const newPassword = document.getElementById('eu-password').value

    if (!name) {
      showAlert('El nombre no puede estar vacío.', 'warning')
      return
    }
    if (newPassword && newPassword.length < 8) {
      showAlert('La contraseña debe tener al menos 8 caracteres.', 'warning')
      return
    }

    const payload = { name, role_name: roleName, is_active: isActive }
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
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
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

window.editUser = function(id) {
  const user = allUsers.find(u => u.id === id)
  if (!user) return

  editingId = id
  document.getElementById('eu-id').value       = id
  document.getElementById('eu-name').value     = user.name || ''
  document.getElementById('eu-role').value     = user.role
  document.getElementById('eu-status').value   = String(user.is_active)
  document.getElementById('eu-password').value = ''
  openModal('edit-user-modal')
  document.getElementById('eu-name')?.focus()
}

window.toggleActive = async function(id, newState) {
  const user  = allUsers.find(u => u.id === id)
  const label = newState ? 'activar' : 'desactivar'
  if (!confirm(`¿Deseas ${label} a "${user?.name || user?.email}"?`)) return

  try {
    await usersAPI.update(id, { is_active: newState })
    showAlert(`Usuario ${newState ? 'activado' : 'desactivado'}.`, 'success')
    await loadUsers()
  } catch (err) {
    showAlert(err.message, 'error')
  }
}
