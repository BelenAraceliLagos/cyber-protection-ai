'use strict'

import { authAPI } from './api.js'
import { showAlert, showSpinner, hideSpinner, openModal, closeModal } from './utils.js'

function injectModal() {
  if (document.getElementById('profile-modal')) return

  const el = document.createElement('div')
  el.innerHTML = `
    <div class="modal-backdrop" id="profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-modal-title">
      <div class="modal">
        <div class="modal__header">
          <h2 class="modal__title" id="profile-modal-title">Mi perfil</h2>
          <button class="modal__close" id="close-profile-modal" aria-label="Cerrar">
            <i class="ti ti-x" aria-hidden="true"></i>
          </button>
        </div>
        <div class="modal__body">
          <div class="profile-summary">
            <div id="profile-avatar-big" class="profile-summary__avatar">??</div>
            <div id="profile-email-display" class="profile-summary__email">-</div>
          </div>
          <form id="profile-form" novalidate>
            <div class="form__group">
              <label for="p-name">Nombre</label>
              <input type="text" id="p-name" placeholder="Tu nombre completo">
            </div>
            <div class="divider"></div>
            <p class="profile-password-note">
              Cambiar contraseña — deja en blanco si no quieres cambiarla
            </p>
            <div class="form__group">
              <label for="p-current-pass">Contraseña actual</label>
              <div class="password-field">
                <input type="password" id="p-current-pass" class="password-field__input" placeholder="Tu contraseña actual">
                <button type="button" class="password-field__toggle" data-toggle="p-current-pass">
                  <i class="ti ti-eye"></i>
                </button>
              </div>
            </div>
            <div class="form__group">
              <label for="p-new-pass">Nueva contraseña</label>
              <div class="password-field">
                <input type="password" id="p-new-pass" class="password-field__input" placeholder="Mínimo 8 caracteres">
                <button type="button" class="password-field__toggle" data-toggle="p-new-pass">
                  <i class="ti ti-eye"></i>
                </button>
              </div>
            </div>
            <div class="form__group">
              <label for="p-confirm-pass">Confirmar nueva contraseña</label>
              <div class="password-field">
                <input type="password" id="p-confirm-pass" class="password-field__input" placeholder="Repite la nueva contraseña">
                <button type="button" class="password-field__toggle" data-toggle="p-confirm-pass">
                  <i class="ti ti-eye"></i>
                </button>
              </div>
            </div>
          </form>
        </div>
        <div class="modal__footer">
          <button class="btn btn--secondary" id="cancel-profile-btn">Cancelar</button>
          <button class="btn btn--primary" id="save-profile-btn">
            <i class="ti ti-check btn__icon" aria-hidden="true"></i>
            Guardar cambios
          </button>
        </div>
      </div>
    </div>`
  document.body.appendChild(el.firstElementChild)
}

export function initProfileModal() {
  injectModal()

  const modal      = document.getElementById('profile-modal')
  const avatarBtn  = document.getElementById('sidebar-initials')
  const closeBtn   = document.getElementById('close-profile-modal')
  const cancelBtn  = document.getElementById('cancel-profile-btn')
  const saveBtn    = document.getElementById('save-profile-btn')
  const nameInput  = document.getElementById('p-name')
  const curPass    = document.getElementById('p-current-pass')
  const newPass    = document.getElementById('p-new-pass')
  const confirmPass = document.getElementById('p-confirm-pass')

  function getInitials(value = '') {
    return value
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map(part => part[0]?.toUpperCase())
      .join('') || '??'
  }

  function renderUser(user) {
    const displayName = user?.name || user?.email || ''
    nameInput.value = user?.name || ''
    document.getElementById('profile-avatar-big').textContent = getInitials(displayName)
    document.getElementById('profile-email-display').textContent = user?.email || ''

    const sidebarName = document.getElementById('sidebar-username')
    const sidebarRole = document.getElementById('sidebar-role')
    const sidebarInitials = document.getElementById('sidebar-initials')

    if (sidebarName) sidebarName.textContent = displayName || 'Usuario'
    if (sidebarRole) sidebarRole.textContent = user?.role === 'admin' ? 'Administrador' : 'Comercial'
    if (sidebarInitials) sidebarInitials.textContent = getInitials(displayName)
  }

  async function open() {
    curPass.value = ''
    newPass.value = ''
    confirmPass.value = ''
    openModal('profile-modal')
    nameInput.value = 'Cargando...'
    nameInput.disabled = true

    try {
      const user = await authAPI.getMe()
      renderUser(user)
      nameInput.disabled = false
      nameInput.focus()
    } catch (err) {
      closeModal('profile-modal')
      showAlert(err.message || 'No se pudo cargar el perfil.', 'error')
      nameInput.disabled = false
    }
  }

  function close() { closeModal('profile-modal') }

  if (avatarBtn) {
    avatarBtn.setAttribute('role', 'button')
    avatarBtn.setAttribute('tabindex', '0')
    avatarBtn.setAttribute('aria-label', 'Editar perfil')
    avatarBtn.setAttribute('title', 'Editar perfil')
    avatarBtn.addEventListener('click', open)
    avatarBtn.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        open()
      }
    })
  }
  closeBtn?.addEventListener('click', close)
  cancelBtn?.addEventListener('click', close)
  modal?.addEventListener('click', (e) => { if (e.target === modal) close() })
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal?.classList.contains('modal-backdrop--visible')) close()
  })

  modal?.querySelectorAll('[data-toggle]').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.toggle)
      if (!input) return
      const isText = input.type === 'text'
      input.type = isText ? 'password' : 'text'
      btn.querySelector('i').className = isText ? 'ti ti-eye' : 'ti ti-eye-off'
    })
  })

  saveBtn?.addEventListener('click', async () => {
    const name   = nameInput.value.trim()
    const curP   = curPass.value
    const newP   = newPass.value
    const confP  = confirmPass.value

    if (!name) { showAlert('El nombre no puede estar vacío.', 'warning'); return }

    if (newP || confP || curP) {
      if (!curP)          { showAlert('Ingresa tu contraseña actual para cambiarla.', 'warning'); return }
      if (newP.length < 8) { showAlert('La nueva contraseña debe tener al menos 8 caracteres.', 'warning'); return }
      if (newP !== confP)  { showAlert('Las contraseñas nuevas no coinciden.', 'warning'); return }
    }

    showSpinner(saveBtn, 'Guardando...')

    try {
      const body = { name }
      if (newP) { body.current_password = curP; body.new_password = newP }

      const updatedUser = await authAPI.updateMe(body)
      renderUser(updatedUser)
      showAlert('Perfil actualizado correctamente.', 'success')
      close()
    } catch (err) {
      showAlert(err.message, 'error')
    } finally {
      hideSpinner(saveBtn)
    }
  })
}
