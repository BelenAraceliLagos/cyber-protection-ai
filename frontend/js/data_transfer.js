'use strict'

// Panel de sincronización de datos: exporta/importa cada módulo como
// archivo JSON, para compartir información entre entornos (ej. entre
// colaboradores) sin depender de dumps SQL ni de Alembic.

import { dataTransferAPI } from './api.js'
import { showAlert, escapeHtml } from './utils.js'

const MODULES = [
  { key: 'companies',     label: 'Empresas' },
  { key: 'services',      label: 'Servicios' },
  { key: 'users',         label: 'Usuarios' },
  { key: 'clients',       label: 'Clientes' },
  { key: 'opportunities', label: 'Oportunidades' },
  { key: 'quotations',    label: 'Cotizaciones' },
]

function downloadJson(filename, obj) {
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function readJsonFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = e => {
      try { resolve(JSON.parse(e.target.result)) }
      catch (err) { reject(new Error('El archivo no es un JSON válido')) }
    }
    reader.onerror = () => reject(new Error('No se pudo leer el archivo'))
    reader.readAsText(file)
  })
}

function reportSummary(rep) {
  if (!rep) return ''
  const parts = []
  if (rep.insertados)   parts.push(`${rep.insertados} nuevos`)
  if (rep.actualizados) parts.push(`${rep.actualizados} actualizados`)
  if (rep.omitidos)     parts.push(`${rep.omitidos} omitidos`)
  if (!parts.length) parts.push('sin cambios')
  let msg = parts.join(', ')
  if (rep.errores && rep.errores.length) {
    msg += ` — ${rep.errores.length} advertencia(s)`
  }
  return msg
}

export function initDataTransfer(containerId = 'sync-panel') {
  const container = document.getElementById(containerId)
  if (!container) return

  container.innerHTML = `
    <div class="import-sync-header">
      <button type="button" class="btn btn--secondary" id="sync-export-all">
        <i class="ti ti-download btn__icon"></i> Exportar todo
      </button>
      <label class="btn btn--primary" for="sync-import-all-input" style="cursor:pointer;">
        <i class="ti ti-upload btn__icon"></i> Importar todo
      </label>
      <input type="file" id="sync-import-all-input" accept=".json" style="display:none;">
    </div>
    <table class="import-sync-table">
      <thead>
        <tr><th>Módulo</th><th>Exportar</th><th>Importar</th><th>Resultado</th></tr>
      </thead>
      <tbody>
        ${MODULES.map(m => `
          <tr data-module="${m.key}">
            <td>${escapeHtml(m.label)}</td>
            <td><button type="button" class="btn btn--secondary btn--sm sync-export-btn" data-module="${m.key}">
                  <i class="ti ti-download"></i>
                </button></td>
            <td>
              <label class="btn btn--secondary btn--sm" style="cursor:pointer;">
                <i class="ti ti-upload"></i>
                <input type="file" class="sync-import-input" data-module="${m.key}" accept=".json" style="display:none;">
              </label>
            </td>
            <td class="sync-result" data-module="${m.key}">—</td>
          </tr>`).join('')}
      </tbody>
    </table>
  `

  container.querySelectorAll('.sync-export-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const module = btn.dataset.module
      try {
        const data = await dataTransferAPI.exportModule(module)
        downloadJson(`${module}.json`, data)
        showAlert(`Exportado ${module}.json`, 'success')
      } catch (err) {
        showAlert('Error al exportar: ' + err.message, 'error')
      }
    })
  })

  container.querySelectorAll('.sync-import-input').forEach(input => {
    input.addEventListener('change', async (e) => {
      const module = input.dataset.module
      const file = e.target.files[0]
      if (!file) return
      const resultCell = container.querySelector(`.sync-result[data-module="${module}"]`)
      try {
        const data = await readJsonFile(file)
        const result = await dataTransferAPI.importModule(module, data)
        const rep = result[module]
        if (resultCell) resultCell.textContent = reportSummary(rep)
        showAlert(`Importación de ${module} completa: ${reportSummary(rep)}`, 'success', 7000)
      } catch (err) {
        showAlert('Error al importar: ' + err.message, 'error')
        if (resultCell) resultCell.textContent = 'error'
      } finally {
        input.value = ''
      }
    })
  })

  document.getElementById('sync-export-all')?.addEventListener('click', async () => {
    try {
      const data = await dataTransferAPI.exportAll()
      downloadJson('sync_completo.json', data)
      showAlert('Exportado sync_completo.json', 'success')
    } catch (err) {
      showAlert('Error al exportar: ' + err.message, 'error')
    }
  })

  document.getElementById('sync-import-all-input')?.addEventListener('change', async (e) => {
    const file = e.target.files[0]
    if (!file) return
    try {
      const data = await readJsonFile(file)
      const results = await dataTransferAPI.importAll(data)
      MODULES.forEach(m => {
        const resultCell = container.querySelector(`.sync-result[data-module="${m.key}"]`)
        if (resultCell && results[m.key]) resultCell.textContent = reportSummary(results[m.key])
      })
      showAlert('Importación completa. Revisa los resultados por módulo.', 'success', 7000)
    } catch (err) {
      showAlert('Error al importar: ' + err.message, 'error')
    } finally {
      e.target.value = ''
    }
  })
}
