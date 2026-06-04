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
          <div style="display:flex;flex-direction:column;align-items:center;margin-bottom:var(--space-lg)">
            <div id="profile-avatar-big"
              style="width:64px;height:64px;border-radius:50%;background:var(--cp-blue-mid);
                display:flex;align-items:center;justify-content:center;
                font-size:22px;font-weight:600;color:var(--cp-cyan);margin-bottom:var(--space-sm)">??</div>
            <div id="profile-email-display" style="font-size:13px;color:var(--cp-text-muted)">-</div>
          </div>
          <form id="profile-form" novalidate>
            <div class="form__group">
              <label for="p-name">Nombre</label>
              <input type="text" id="p-name" placeholder="Tu nombre completo">
            </div>
            <div class="divider"></div>
            <p style="font-size:12px;font-weight:500;color:var(--cp-text-muted);margin-bottom:var(--space-md)">
              Cambiar contraseña — deja en blanco si no quieres cambiarla
            </p>
            <div class="form__group">
              <label for="p-current-pass">Contraseña actual</label>
              <div style="position:relative">
                <input type="password" id="p-current-pass" placeholder="Tu contraseña actual" style="padding-right:40px">
                <button type="button" data-toggle="p-current-pass"
                  style="position:absolute;right:10px;top:50%;transform:translateY(-50%);
                    width:28px;height:28px;display:flex;align-items:center;justify-content:center;
                    color:var(--cp-text-muted);background:none;border:none;cursor:pointer">
                  <i class="ti ti-eye"></i>
                </button>
              </div>
            </div>
            <div class="form__group">
              <label for="p-new-pass">Nueva contraseña</label>
              <div style="position:relative">
                <input type="password" id="p-new-pass" placeholder="Mínimo 8 caracteres" style="padding-right:40px">
                <button type="button" data-toggle="p-new-pass"
                  style="position:absolute;right:10px;top:50%;transform:translateY(-50%);
                    width:28px;height:28px;display:flex;align-items:center;justify-content:center;
                    color:var(--cp-text-muted);background:none;border:none;cursor:pointer">
                  <i class="ti ti-eye"></i>
                </button>
              </div>
            </div>
            <div class="form__group">
              <label for="p-confirm-pass">Confirmar nueva contraseña</label>
              <div style="position:relative">
                <input type="password" id="p-confirm-pass" placeholder="Repite la nueva contraseña" style="padding-right:40px">
                <button type="button" data-toggle="p-confirm-pass"
                  style="position:absolute;right:10px;top:50%;transform:translateY(-50%);
                    width:28px;height:28px;display:flex;align-items:center;justify-content:center;
                    color:var(--cp-text-muted);background:none;border:none;cursor:pointer">
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

  function getPayload() {
    try { return JSON.parse(atob(sessionStorage.getItem('cp_token').split('.')[1])) }
    catch { return {} }
  }

  function open() {
    const payload = getPayload()
    nameInput.value    = payload.name  || ''
    curPass.value      = ''
    newPass.value      = ''
    confirmPass.value  = ''
    const initials = (payload.name || payload.email || '??').substring(0, 2).toUpperCase()
    document.getElementById('profile-avatar-big').textContent    = initials
    document.getElementById('profile-email-display').textContent = payload.email || ''
    openModal('profile-modal')
    nameInput.focus()
  }

  function close() { closeModal('profile-modal') }

  avatarBtn?.addEventListener('click', open)
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

      await authAPI.updateMe(body)
      showAlert('Perfil actualizado. Volviendo a iniciar sesión...', 'success')
      close()
      setTimeout(() => {
        sessionStorage.removeItem('cp_token')
        window.location.href = '/pages/login.html'
      }, 2000)
    } catch (err) {
      showAlert(err.message, 'error')
    } finally {
      hideSpinner(saveBtn)
    }
  })
}
