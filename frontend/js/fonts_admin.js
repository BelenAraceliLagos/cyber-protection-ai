'use strict'

// Panel de fuentes personalizadas: subir, listar y eliminar fuentes .ttf/.otf
// para usarlas en el Editor de diseño. Al subir una fuente con el mismo
// nombre de una ya existente, se completa esa misma fuente (por ejemplo,
// subir primero Regular y más tarde agregar Negrita).

import { fontsAPI } from './api.js'
import { showAlert, escapeHtml } from './utils.js'

export async function initFontsAdmin(containerId = 'fonts-panel') {
  const container = document.getElementById(containerId)
  if (!container) return

  container.innerHTML = `
    <div class="fonts-upload-card">
      <div class="fonts-upload-card__title">Subir fuente nueva</div>
      <div class="fonts-upload-card__row">
        <div class="fonts-field">
          <label class="form__label">Nombre de la fuente</label>
          <input type="text" id="ff-name" class="form__input" placeholder="Ej: Montserrat">
        </div>
        <div class="fonts-field">
          <label class="form__label">Archivo Regular (.ttf/.otf)</label>
          <input type="file" id="ff-regular" accept=".ttf,.otf">
        </div>
        <div class="fonts-field">
          <label class="form__label">Archivo Negrita (.ttf/.otf)</label>
          <input type="file" id="ff-bold" accept=".ttf,.otf">
        </div>
      </div>
      <span class="ed-hint">Puedes subir solo uno de los dos archivos ahora, y agregar el otro más tarde con el mismo nombre — se completará la misma fuente.</span>
      <button type="button" class="btn btn--primary btn--sm" id="ff-upload-btn" style="margin-top:0.75rem;">
        <i class="ti ti-upload"></i> Subir fuente
      </button>
    </div>

    <table class="import-sync-table" style="margin-top:1.5rem;">
      <thead>
        <tr><th>Fuente</th><th>Regular</th><th>Negrita</th><th></th></tr>
      </thead>
      <tbody id="ff-list">
        <tr><td colspan="4">Cargando...</td></tr>
      </tbody>
    </table>
  `

  async function refresh() {
    const tbody = document.getElementById('ff-list')
    try {
      const fonts = await fontsAPI.list()
      if (!fonts.length) {
        tbody.innerHTML = '<tr><td colspan="4">Aún no has subido ninguna fuente.</td></tr>'
        return
      }
      tbody.innerHTML = fonts.map(f => `
        <tr data-id="${f.id}">
          <td>${escapeHtml(f.name)}</td>
          <td>${f.has_regular ? '<i class="ti ti-check" style="color:#1A6B3A"></i>' : '<i class="ti ti-minus" style="color:var(--cp-text-muted)"></i>'}</td>
          <td>${f.has_bold ? '<i class="ti ti-check" style="color:#1A6B3A"></i>' : '<i class="ti ti-minus" style="color:var(--cp-text-muted)"></i>'}</td>
          <td><button type="button" class="btn btn--ghost btn--sm ff-delete-btn" data-id="${f.id}" data-name="${escapeHtml(f.name)}"><i class="ti ti-trash"></i></button></td>
        </tr>
      `).join('')

      tbody.querySelectorAll('.ff-delete-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          if (!confirm(`¿Eliminar la fuente "${btn.dataset.name}"? Esto no se puede deshacer.`)) return
          try {
            await fontsAPI.remove(btn.dataset.id)
            showAlert('Fuente eliminada', 'success')
            refresh()
          } catch (err) {
            showAlert('Error al eliminar: ' + err.message, 'error')
          }
        })
      })
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="4">Error al cargar: ${escapeHtml(err.message)}</td></tr>`
    }
  }

  document.getElementById('ff-upload-btn').addEventListener('click', async () => {
    const name = document.getElementById('ff-name').value.trim()
    const regular = document.getElementById('ff-regular').files[0]
    const bold = document.getElementById('ff-bold').files[0]

    if (!name) { showAlert('Escribe un nombre para la fuente', 'error'); return }
    if (!regular && !bold) { showAlert('Sube al menos un archivo (Regular o Negrita)', 'error'); return }

    const formData = new FormData()
    formData.append('name', name)
    if (regular) formData.append('regular', regular)
    if (bold) formData.append('bold', bold)

    const btn = document.getElementById('ff-upload-btn')
    btn.disabled = true
    try {
      await fontsAPI.upload(formData)
      showAlert(`Fuente "${name}" guardada`, 'success')
      document.getElementById('ff-name').value = ''
      document.getElementById('ff-regular').value = ''
      document.getElementById('ff-bold').value = ''
      refresh()
    } catch (err) {
      showAlert('Error al subir: ' + err.message, 'error')
    } finally {
      btn.disabled = false
    }
  })

  refresh()
}
