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
  bindRutInput()
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
    const companyMeta = c.rut ? `RUT ${c.rut} · ${email}` : email
    const contactMeta = c.contact_position ? `${contactName} · ${c.contact_position}` : contactName

    return `
      <tr>
        <td>
          <div class="entity-cell">
            <div class="entity-cell__avatar">
              ${escapeHtml(getInitials(companyName))}
            </div>
            <div>
              <div class="entity-cell__title">${escapeHtml(companyName)}</div>
              <div class="entity-cell__meta">${escapeHtml(companyMeta)}</div>
            </div>
          </div>
        </td>
        <td>${escapeHtml(contactMeta)}</td>
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
          (c.company_name || '').toLowerCase().includes(q) ||
          (c.business_name || '').toLowerCase().includes(q) ||
          (c.rut || '').toLowerCase().includes(q) ||
          (c.contact_name || '').toLowerCase().includes(q) ||
          (c.contact_position || '').toLowerCase().includes(q) ||
          (c.email || '').toLowerCase().includes(q) ||
          (c.industry || '').toLowerCase().includes(q) ||
          (c.city || '').toLowerCase().includes(q) ||
          (c.region || '').toLowerCase().includes(q))
      : allClients
    renderTable(filtered)
  }, 250))
}


// ── RUT helpers ────────────────────────────────────────────────────────
function cleanRut(v) { return v.replace(/[.\-]/g, '').toUpperCase().trim() }

function calcDv(body) {
  let sum = 0, mul = 2
  for (let i = body.length - 1; i >= 0; i--) {
    sum += parseInt(body[i]) * mul
    mul = mul === 7 ? 2 : mul + 1
  }
  const r = 11 - (sum % 11)
  return r === 11 ? '0' : r === 10 ? 'K' : String(r)
}

function formatRut(raw) {
  const clean = cleanRut(raw)
  if (clean.length < 2) return null
  const body = clean.slice(0, -1)
  const dv   = clean.slice(-1)
  if (!/^[0-9]+$/.test(body)) return null
  // Agregar puntos cada 3 dígitos desde la derecha
  let formatted = ''
  for (let i = 0; i < body.length; i++) {
    const pos = body.length - 1 - i
    formatted = body[pos] + formatted
    if (i > 0 && i % 3 === 2 && pos > 0) formatted = '.' + formatted
  }
  return formatted + '-' + dv
}

function isValidRut(raw) {
  const clean = cleanRut(raw)
  if (clean.length < 2) return false
  const body = clean.slice(0, -1)
  const dv   = clean.slice(-1)
  if (!/^[0-9]+$/.test(body)) return false
  return calcDv(body) === dv
}

function bindRutInput() {
  const input    = document.getElementById('f-rut')
  const hint     = document.getElementById('f-rut-hint')
  const preview  = document.getElementById('f-rut-preview')
  const previewT = document.getElementById('f-rut-preview-text')
  const errEl    = document.getElementById('f-rut-error')
  const errText  = document.getElementById('f-rut-error-text')
  if (!input) return

  input.addEventListener('input', () => {
    const val = input.value.trim()
    if (!val) {
      hint.style.display    = ''
      preview.style.display = 'none'
      errEl.style.display   = 'none'
      input.style.borderColor = ''
      return
    }
    const clean = cleanRut(val)
    if (clean.length >= 7) {
      if (isValidRut(clean)) {
        const formatted = formatRut(clean)
        hint.style.display    = 'none'
        preview.style.display = ''
        previewT.textContent  = 'RUT válido: ' + formatted
        errEl.style.display   = 'none'
        input.style.borderColor = '#16a34a'
      } else {
        hint.style.display    = 'none'
        preview.style.display = 'none'
        errEl.style.display   = ''
        errText.textContent   = 'Dígito verificador incorrecto. Revisa el RUT.'
        input.style.borderColor = '#dc2626'
      }
    } else {
      hint.style.display    = ''
      preview.style.display = 'none'
      errEl.style.display   = 'none'
      input.style.borderColor = ''
    }
  })
}
function bindForm() {
  const form = document.getElementById('client-form')
  const btn  = document.getElementById('client-submit')
  if (!form) return

  form.addEventListener('submit', async (e) => {
    e.preventDefault()
    const data = {
      company_name:      document.getElementById('f-company').value.trim(),
      rut:               document.getElementById('f-rut').value.trim() || null,
      business_name:     document.getElementById('f-business-name').value.trim() || null,
      address:           document.getElementById('f-address').value.trim() || null,
      city:              document.getElementById('f-city').value.trim() || null,
      region:            document.getElementById('f-region').value.trim() || null,
      country:           document.getElementById('f-country').value.trim() || 'Chile',
      website:           document.getElementById('f-website').value.trim() || null,
      contact_name:      document.getElementById('f-contact').value.trim(),
      email:             document.getElementById('f-email').value.trim(),
      phone:             document.getElementById('f-phone').value.trim() || null,
      contact_position:  document.getElementById('f-contact-position').value.trim() || null,
      contact_phone:     document.getElementById('f-contact-phone').value.trim() || null,
      industry:          document.getElementById('f-industry').value.trim() || null,
      lifecycle_stage:   document.getElementById('f-lifecycle')?.value || 'lead',
      origen:            document.getElementById('f-origen')?.value || null,
      notes:             document.getElementById('f-notes').value.trim() || null,
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
      const country = document.getElementById('f-country')
      if (country) country.value = 'Chile'
      document.getElementById('modal-title').textContent = 'Nuevo cliente'
    })
  })
}

window.editClient = function(id) {
  const client = allClients.find(c => c.id === id)
  if (!client) return

  editingId = id
  document.getElementById('modal-title').textContent = 'Editar cliente'
  document.getElementById('f-company').value          = client.company_name || ''
  document.getElementById('f-rut').value              = client.rut || ''
  document.getElementById('f-business-name').value    = client.business_name || ''
  document.getElementById('f-address').value          = client.address || ''
  document.getElementById('f-city').value             = client.city || ''
  document.getElementById('f-region').value           = client.region || ''
  document.getElementById('f-country').value          = client.country || 'Chile'
  document.getElementById('f-website').value          = client.website || ''
  document.getElementById('f-contact').value          = client.contact_name || ''
  document.getElementById('f-contact-position').value = client.contact_position || ''
  document.getElementById('f-email').value            = client.email || ''
  document.getElementById('f-phone').value            = client.phone || ''
  document.getElementById('f-contact-phone').value    = client.contact_phone || ''
  document.getElementById('f-industry').value         = client.industry || ''
  if (document.getElementById('f-lifecycle')) document.getElementById('f-lifecycle').value = client.lifecycle_stage || 'lead'
  if (document.getElementById('f-origen'))    document.getElementById('f-origen').value    = client.origen || ''
  document.getElementById('f-notes').value            = client.notes || ''
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
  const country = document.getElementById('f-country')
  if (country) country.value = 'Chile'
  const title = document.getElementById('modal-title')
  if (title) title.textContent = 'Nuevo cliente'
  // Reset RUT hints
  const rutInput = document.getElementById('f-rut')
  if (rutInput) {
    rutInput.style.borderColor = ''
    document.getElementById('f-rut-hint').style.display    = ''
    document.getElementById('f-rut-preview').style.display = 'none'
    document.getElementById('f-rut-error').style.display   = 'none'
  }
  openModal('client-modal')
}
