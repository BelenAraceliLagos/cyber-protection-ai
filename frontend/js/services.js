'use strict'

import { servicesAPI } from './api.js'
import {
  showAlert, showSpinner, hideSpinner,
  renderSkeletonRows, animateTableRows,
  renderEmptyState, openModal, closeModal,
  debounce, requireAuth
} from './utils.js'

let allServices = []
let editingId   = null

export async function initServices() {
  if (!requireAuth()) return
  await loadServices()
  bindSearch()
  bindForm()
  bindModalClose()
  document.getElementById('new-service-btn')
    ?.addEventListener('click', openNewServiceModal)
}

async function loadServices() {
  const tbody = document.getElementById('services-tbody')
  if (!tbody) return

  renderSkeletonRows(tbody, 4)

  try {
    allServices = await servicesAPI.getAll()
    renderTable(allServices)
  } catch (err) {
    showAlert(err.message, 'error')
    renderEmptyState(
      tbody.closest('.card') || tbody.parentElement,
      'Error al cargar servicios',
      'No se pudo conectar con el servidor.',
      'ti-briefcase'
    )
  }
}

function renderTable(services) {
  const tbody = document.getElementById('services-tbody')
  const count = document.getElementById('services-count')
  if (!tbody) return

  if (count) count.textContent =
    `${services.length} servicio${services.length !== 1 ? 's' : ''}`

  if (!services.length) {
    renderEmptyState(
      tbody.closest('.card') || tbody.parentElement,
      'Sin servicios aún',
      'Agrega tu primer servicio con el botón de arriba.',
      'ti-briefcase'
    )
    return
  }

  tbody.innerHTML = services.map(s => `
    <tr>
      <td>
        <div style="font-weight:500;color:var(--cp-blue-main)">${s.name}</div>
        <div style="font-size:11px;color:var(--cp-text-muted);margin-top:2px">
          ${s.description || '—'}
        </div>
      </td>
      <td>
        <span style="font-weight:600;color:var(--cp-blue-main)">
          ${s.base_price > 0 ? s.base_price.toFixed(1) + ' UF' : 'A convenir'}
        </span>
      </td>
      <td>
        <span class="badge ${s.active ? 'badge--success' : 'badge--neutral'}">
          ${s.active ? 'Activo' : 'Inactivo'}
        </span>
      </td>
      <td>
        <div style="display:flex;gap:6px">
          <button class="btn btn--sm btn--secondary"
            onclick="editService(${s.id})" aria-label="Editar">
            <i class="ti ti-edit btn__icon" aria-hidden="true"></i>
          </button>
          <button class="btn btn--sm btn--danger"
            onclick="deleteService(${s.id}, '${s.name.replace(/'/g, "\\'")}')">
            <i class="ti ti-trash btn__icon" aria-hidden="true"></i>
          </button>
        </div>
      </td>
    </tr>`).join('')

  animateTableRows(tbody)
}

function bindSearch() {
  const input = document.getElementById('service-search')
  if (!input) return

  input.addEventListener('input', debounce(() => {
    const q = input.value.toLowerCase().trim()
    const filtered = q
      ? allServices.filter(s =>
          s.name.toLowerCase().includes(q) ||
          (s.description || '').toLowerCase().includes(q))
      : allServices
    renderTable(filtered)
  }, 250))
}

function bindForm() {
  const form = document.getElementById('service-form')
  const btn  = document.getElementById('service-submit')
  if (!form) return

  form.addEventListener('submit', async (e) => {
    e.preventDefault()

    const data = {
      name:        document.getElementById('sf-name').value.trim(),
      description: document.getElementById('sf-description').value.trim() || null,
      base_price:  parseFloat(document.getElementById('sf-price').value) || 0,
      active:      document.getElementById('sf-active').value === 'true',
    }

    if (!data.name) {
      showAlert('El nombre del servicio es obligatorio.', 'warning')
      return
    }

    showSpinner(btn, editingId ? 'Guardando...' : 'Creando...')

    try {
      if (editingId) {
        await servicesAPI.update(editingId, data)
        showAlert('Servicio actualizado correctamente.', 'success')
      } else {
        await servicesAPI.create(data)
        showAlert('Servicio creado correctamente.', 'success')
      }
      closeModal('service-modal')
      form.reset()
      editingId = null
      await loadServices()
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
      editingId = null
      document.getElementById('service-form')?.reset()
      const title = document.getElementById('service-modal-title')
      if (title) title.textContent = 'Nuevo servicio'
    })
  })

  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', e => {
      if (e.target === backdrop) {
        closeModal(backdrop.id)
        editingId = null
      }
    })
  })
}

window.openNewServiceModal = function () {
  editingId = null
  document.getElementById('service-form')?.reset()
  document.getElementById('sf-active').value = 'true'
  const title = document.getElementById('service-modal-title')
  if (title) title.textContent = 'Nuevo servicio'
  openModal('service-modal')
  document.getElementById('sf-name')?.focus()
}

window.editService = function (id) {
  const s = allServices.find(x => x.id === id)
  if (!s) return

  editingId = id
  document.getElementById('service-modal-title').textContent = 'Editar servicio'
  document.getElementById('sf-name').value        = s.name
  document.getElementById('sf-description').value = s.description || ''
  document.getElementById('sf-price').value       = s.base_price
  document.getElementById('sf-active').value      = String(s.active)
  openModal('service-modal')
  document.getElementById('sf-name')?.focus()
}

window.deleteService = async function (id, name) {
  if (!confirm(`¿Eliminar "${name}"? Esta acción no se puede deshacer.`)) return

  try {
    await servicesAPI.delete(id)
    showAlert('Servicio eliminado.', 'success')
    await loadServices()
  } catch (err) {
    showAlert(err.message, 'error')
  }
}
