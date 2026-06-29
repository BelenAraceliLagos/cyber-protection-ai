'use strict'

import { servicesAPI } from './api.js'
import {
  showAlert, showSpinner, hideSpinner,
  openModal, closeModal,
  debounce, requireAuth, escapeHtml, escapeAttr
} from './utils.js'
import { CATEGORIAS_ORDEN, agrupar } from './categories.js'

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
  const cont = document.getElementById('services-categorias')
  if (!cont) return

  cont.innerHTML = '<div class="empty-state">Cargando servicios...</div>'

  try {
    allServices = await servicesAPI.getAll()
    renderCategorias(allServices)
  } catch (err) {
    showAlert(err.message, 'error')
    cont.innerHTML = `
      <div class="empty-state page-enter">
        <div class="empty-state__icon"><i class="ti ti-briefcase" aria-hidden="true"></i></div>
        <p class="empty-state__title">Error al cargar servicios</p>
        <p class="empty-state__desc">No se pudo conectar con el servidor.</p>
      </div>`
  }
}

// ── Render por categorías (igual que el módulo "Generar informe") ─────────
function renderCategorias(services) {
  const cont  = document.getElementById('services-categorias')
  const count = document.getElementById('services-count')
  if (!cont) return

  // El contador total SIEMPRE refleja allServices.length, no el filtrado
  if (count) count.textContent =
    `${allServices.length} servicio${allServices.length !== 1 ? 's' : ''}`

  if (!services.length) {
    cont.innerHTML = `
      <div class="empty-state page-enter">
        <div class="empty-state__icon"><i class="ti ti-search-off" aria-hidden="true"></i></div>
        <p class="empty-state__title">Sin resultados</p>
        <p class="empty-state__desc">No hay servicios que coincidan con tu búsqueda.</p>
      </div>`
    return
  }

  const grupos = agrupar(services)
  cont.innerHTML = ''

  for (const cat of CATEGORIAS_ORDEN) {
    const srvs = grupos[cat]
    if (!srvs.length) continue

    const bloque = document.createElement('div')
    bloque.className = 'svc-categoria'
    bloque.innerHTML = `
      <div class="svc-categoria__header" data-toggle-cat>
        <span class="svc-categoria__nombre">${escapeHtml(cat)}</span>
        <span class="badge badge--info badge--xs">${srvs.length}</span>
        <i class="ti ti-chevron-down" aria-hidden="true"></i>
      </div>
      <div class="svc-categoria__body table-wrapper">
        <table class="table">
          <thead>
            <tr>
              <th>Servicio</th>
              <th>Precio base</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            ${srvs.map(filaServicio).join('')}
          </tbody>
        </table>
      </div>`
    cont.appendChild(bloque)
  }

  // Header click → toggle abierto/cerrado
  cont.querySelectorAll('[data-toggle-cat]').forEach(header => {
    header.addEventListener('click', () => {
      header.nextElementSibling?.classList.toggle('svc-categoria__body--open')
      header.classList.toggle('svc-categoria__header--open')
    })
    // Abrir todas por defecto
    header.nextElementSibling?.classList.add('svc-categoria__body--open')
    header.classList.add('svc-categoria__header--open')
  })

  // Acciones editar / eliminar
  cont.querySelectorAll('[data-service-edit]').forEach(btn => {
    btn.addEventListener('click', () => editService(Number(btn.dataset.serviceEdit)))
  })
  cont.querySelectorAll('[data-service-delete]').forEach(btn => {
    btn.addEventListener('click', () =>
      deleteService(Number(btn.dataset.serviceDelete), btn.dataset.serviceName || ''))
  })
}

function filaServicio(s) {
  const id    = Number(s.id) || 0
  const name  = s.name || ''
  const price = Number(s.base_price) > 0 ? `${Number(s.base_price).toFixed(1)} UF` : 'A convenir'

  return `
    <tr>
      <td>
        <div class="entity-cell__title">${escapeHtml(name)}</div>
        <div class="entity-cell__meta">${escapeHtml(s.description || '—')}</div>
      </td>
      <td><span class="entity-cell__title">${escapeHtml(price)}</span></td>
      <td>
        <span class="badge ${s.active ? 'badge--success' : 'badge--neutral'}">
          ${s.active ? 'Activo' : 'Inactivo'}
        </span>
      </td>
      <td>
        <div class="table-actions">
          <button class="btn btn--sm btn--secondary" data-service-edit="${id}" aria-label="Editar">
            <i class="ti ti-edit btn__icon" aria-hidden="true"></i>
          </button>
          <button class="btn btn--sm btn--danger" data-service-delete="${id}" data-service-name="${escapeAttr(name)}">
            <i class="ti ti-trash btn__icon" aria-hidden="true"></i>
          </button>
        </div>
      </td>
    </tr>`
}

// ── Búsqueda (sin romper el DOM en resultados vacíos) ──────────────────────
function bindSearch() {
  const input = document.getElementById('service-search')
  if (!input) return

  input.addEventListener('input', debounce(() => {
    const q = (input.value || '').toLowerCase().trim()
    const filtered = q
      ? allServices.filter(s =>
          (s.name || '').toLowerCase().includes(q) ||
          (s.description || '').toLowerCase().includes(q))
      : allServices
    renderCategorias(filtered)
  }, 250))
}

// ── Formulario crear / editar ──────────────────────────────────────────────
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

function openNewServiceModal() {
  editingId = null
  document.getElementById('service-form')?.reset()
  document.getElementById('sf-active').value = 'true'
  const title = document.getElementById('service-modal-title')
  if (title) title.textContent = 'Nuevo servicio'
  openModal('service-modal')
  document.getElementById('sf-name')?.focus()
}

function editService(id) {
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

async function deleteService(id, name) {
  if (!confirm(`¿Eliminar "${name}"? Esta acción no se puede deshacer.`)) return

  try {
    await servicesAPI.delete(id)
    showAlert('Servicio eliminado.', 'success')
    await loadServices()
  } catch (err) {
    showAlert(err.message, 'error')
  }
}
