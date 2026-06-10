'use strict'

import { clientsAPI } from './api.js'
import {
  showAlert, showSpinner, hideSpinner,
  renderSkeletonRows, animateTableRows,
  renderEmptyState, openModal, closeModal,
  formatDate, getInitials, debounce, requireAuth, escapeHtml, escapeAttr
} from './utils.js'

let allClients = []
let editingId  = null

export async function initClients() {
  if (!requireAuth()) return
  await loadClients()
  bindSearch()
  bindForm()
  bindModalClose()
}

async function loadClients() {
  const tbody = document.getElementById('clients-tbody')
  if (!tbody) return

  renderSkeletonRows(tbody, 5)

  try {
    allClients = await clientsAPI.getAll()
    renderTable(allClients)
  } catch (err) {
    showAlert(err.message, 'error')
    renderEmptyState(tbody.closest('.table-wrapper') || tbody.parentElement,
      'Error al cargar clientes', 'No se pudo conectar con el servidor.')
  }
}

function renderTable(clients) {
  const tbody = document.getElementById('clients-tbody')
  const count = document.getElementById('clients-count')
  if (!tbody) return

  if (count) count.textContent = `${clients.length} cliente${clients.length !== 1 ? 's' : ''}`

  if (!clients.length) {
    renderEmptyState(
      tbody.closest('.card') || tbody.parentElement,
      'Sin clientes aún',
      'Agrega tu primer cliente potencial con el botón de arriba.',
      'ti-users'
    )
    return
  }

  tbody.innerHTML = clients.map(c => {
    const id = Number(c.id) || 0
    const companyName = c.company_name || ''
    const email = c.email || '—'
    const contactName = c.contact_name || '—'

    return `
      <tr>
        <td>
          <div class="entity-cell">
            <div class="entity-cell__avatar">
              ${escapeHtml(getInitials(companyName))}
            </div>
            <div>
              <div class="entity-cell__title">${escapeHtml(companyName)}</div>
              <div class="entity-cell__meta">${escapeHtml(email)}</div>
            </div>
          </div>
        </td>
        <td>${escapeHtml(contactName)}</td>
        <td>${escapeHtml(c.industry || '—')}</td>
        <td>${escapeHtml(c.phone || '—')}</td>
        <td>
          <div class="table-actions">
            <button class="btn btn--sm btn--secondary" data-client-edit="${id}" aria-label="Editar">
              <i class="ti ti-edit btn__icon" aria-hidden="true"></i>
            </button>
            <button class="btn btn--sm btn--danger" data-client-delete="${id}" data-client-name="${escapeAttr(companyName)}">
              <i class="ti ti-trash btn__icon" aria-hidden="true"></i>
            </button>
          </div>
        </td>
      </tr>`
  }).join('')

  tbody.querySelectorAll('[data-client-edit]').forEach(btn => {
    btn.addEventListener('click', () => editClient(Number(btn.dataset.clientEdit)))
  })
  tbody.querySelectorAll('[data-client-delete]').forEach(btn => {
    btn.addEventListener('click', () => deleteClient(Number(btn.dataset.clientDelete), btn.dataset.clientName || ''))
  })

  animateTableRows(tbody)
}

function bindSearch() {
  const input = document.getElementById('client-search')
  if (!input) return

  input.addEventListener('input', debounce(() => {
    const q = input.value.toLowerCase().trim()
    const filtered = q
      ? allClients.filter(c =>
          c.company_name.toLowerCase().includes(q) ||
          c.contact_name.toLowerCase().includes(q) ||
          (c.industry || '').toLowerCase().includes(q))
      : allClients
    renderTable(filtered)
  }, 250))
}

function bindForm() {
  const form = document.getElementById('client-form')
  const btn  = document.getElementById('client-submit')
  if (!form) return

  form.addEventListener('submit', async (e) => {
    e.preventDefault()
    const data = {
      company_name:  document.getElementById('f-company').value.trim(),
      contact_name:  document.getElementById('f-contact').value.trim(),
      email:         document.getElementById('f-email').value.trim(),
      phone:         document.getElementById('f-phone').value.trim() || null,
      industry:      document.getElementById('f-industry').value.trim() || null,
      notes:         document.getElementById('f-notes').value.trim() || null,
    }

    if (!data.company_name || !data.contact_name || !data.email) {
      showAlert('Empresa, contacto y correo son obligatorios.', 'warning')
      return
    }

    showSpinner(btn, editingId ? 'Guardando...' : 'Creando...')

    try {
      if (editingId) {
        await clientsAPI.update(editingId, data)
        showAlert('Cliente actualizado correctamente.', 'success')
      } else {
        await clientsAPI.create(data)
        showAlert('Cliente creado correctamente.', 'success')
      }
      closeModal('client-modal')
      form.reset()
      editingId = null
      await loadClients()
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
      document.getElementById('client-form')?.reset()
      document.getElementById('modal-title').textContent = 'Nuevo cliente'
    })
  })
}

window.editClient = function(id) {
  const client = allClients.find(c => c.id === id)
  if (!client) return

  editingId = id
  document.getElementById('modal-title').textContent = 'Editar cliente'
  document.getElementById('f-company').value  = client.company_name
  document.getElementById('f-contact').value  = client.contact_name
  document.getElementById('f-email').value    = client.email
  document.getElementById('f-phone').value    = client.phone || ''
  document.getElementById('f-industry').value = client.industry || ''
  document.getElementById('f-notes').value    = client.notes || ''
  openModal('client-modal')
}

window.deleteClient = async function(id, name) {
  if (!confirm(`¿Eliminar a "${name}"? Esta acción no se puede deshacer.`)) return

  try {
    await clientsAPI.delete(id)
    showAlert('Cliente eliminado.', 'success')
    await loadClients()
  } catch (err) {
    showAlert(err.message, 'error')
  }
}

window.openNewClientModal = function() {
  editingId = null
  document.getElementById('client-form')?.reset()
  const title = document.getElementById('modal-title')
  if (title) title.textContent = 'Nuevo cliente'
  openModal('client-modal')
}
