'use strict'

/**
 * import_services.js — Importar el catálogo de servicios desde Excel.
 *
 * Funciona en dos pasos, siempre con el mismo archivo:
 *   1. VISTA PREVIA  → POST /ingestion/catalogo/preview   (no guarda nada)
 *   2. CONFIRMAR     → POST /ingestion/catalogo/confirmar (guarda las filas válidas)
 *
 * Toda la lectura y validación del Excel la hace el backend.
 */

import { getToken } from './api.js'
import { BASE_URL } from './config.js'
import { showAlert, showSpinner, hideSpinner, escapeHtml } from './utils.js'

const ETIQUETA_CAMPO = {
  name:        'nombre',
  description: 'descripción',
  modalidad:   'modalidad',
  base_price:  'precio',
  active:      'estado',
}

const ACCION = {
  nuevo:       { texto: 'Nuevo',       clase: 'badge--success' },
  actualiza:   { texto: 'Actualiza',   clase: 'badge--info'    },
  sin_cambios: { texto: 'Sin cambios', clase: 'badge--neutral' },
  error:       { texto: 'Error',       clase: 'badge--error'   },
}

// ── Llamada al backend ────────────────────────────────────────────────
async function enviarArchivo(ruta, archivo) {
  const formData = new FormData()
  formData.append('archivo', archivo)

  const token = getToken()
  let respuesta
  try {
    respuesta = await fetch(`${BASE_URL}${ruta}`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })
  } catch {
    throw new Error('No se pudo conectar con el servidor.')
  }

  const datos = await respuesta.json().catch(() => ({}))
  if (!respuesta.ok) {
    const detalle = typeof datos.detail === 'string' ? datos.detail : `Error ${respuesta.status}`
    throw new Error(detalle)
  }
  return datos
}

// ── Dibujar la vista previa ───────────────────────────────────────────
function detalleFila(f) {
  const partes = []
  if (f.errores.length) {
    partes.push(...f.errores.map(e => `<div class="imp-err">${escapeHtml(e)}</div>`))
  }
  if (f.avisos.length) {
    partes.push(...f.avisos.map(a => `<div class="imp-aviso">${escapeHtml(a)}</div>`))
  }
  if (f.accion === 'actualiza') {
    const campos = f.cambios.map(c => ETIQUETA_CAMPO[c] || c).join(', ')
    partes.push(`<div class="imp-meta">Cambia: ${escapeHtml(campos)}</div>`)
  }
  if (f.accion === 'nuevo' && f.datos) {
    const precio = Number(f.datos.base_price).toFixed(1)
    partes.push(`<div class="imp-meta">${escapeHtml(f.datos.modalidad)} · ${precio} UF</div>`)
  }
  return partes.join('') || '—'
}

function dibujarVista(contenedor, archivo, informe) {
  const r = informe.resumen
  const visibles = informe.filas.filter(f => f.accion !== 'sin_cambios')

  const tarjeta = (valor, etiqueta, extra = '') => `
    <div class="import-summary__card ${extra}">
      <div class="import-summary__value">${valor}</div>
      <div class="import-summary__label">${etiqueta}</div>
    </div>`

  contenedor.innerHTML = `
    <style>
      .imp-tabla-wrap { max-height: 420px; overflow: auto; margin-top: 12px; }
      .imp-err   { color: #c62828; font-size: 12px; }
      .imp-aviso { color: #b26a00; font-size: 12px; font-weight: 600; }
      .imp-meta  { color: var(--cp-text-muted); font-size: 12px; }
      .imp-fila-error { background: #fff5f5; }
    </style>

    <div class="import-file-info">
      <i class="ti ti-file-spreadsheet import-file-info__icon"></i>
      <div>
        <div class="import-file-info__title">${escapeHtml(archivo.name)}</div>
        <div class="import-file-info__meta">${r.total} filas leídas — vista previa, todavía no se guardó nada</div>
      </div>
    </div>

    <div class="import-summary">
      ${tarjeta(r.nuevo, 'Nuevos')}
      ${tarjeta(r.actualiza, 'Se actualizan')}
      ${tarjeta(r.sin_cambios, 'Sin cambios', 'import-summary__card--muted')}
      ${tarjeta(r.error, 'Con error', r.error ? 'import-summary__card--warning' : 'import-summary__card--muted')}
    </div>

    ${r.error ? `<div class="imp-err" style="margin-bottom:8px">
      Las filas con error NO se guardarán. Corrígelas en el Excel y vuelve a subirlo si las necesitas.</div>` : ''}

    ${visibles.length ? `
      <div class="imp-tabla-wrap">
        <table class="import-sync-table">
          <thead><tr><th>Fila</th><th>Servicio</th><th>Acción</th><th>Detalle</th></tr></thead>
          <tbody>
            ${visibles.map(f => `
              <tr class="${f.accion === 'error' ? 'imp-fila-error' : ''}">
                <td>${f.fila}</td>
                <td>${escapeHtml(f.nombre || '(sin nombre)')}</td>
                <td><span class="badge ${ACCION[f.accion].clase}">${ACCION[f.accion].texto}</span></td>
                <td>${detalleFila(f)}</td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>` : `
      <div class="import-empty">
        <i class="ti ti-circle-check import-empty__icon"></i>
        Todo está al día: no hay nada que importar.
      </div>`}

    ${r.sin_cambios ? `<div class="imp-meta" style="margin-top:8px">
      ${r.sin_cambios} servicio${r.sin_cambios !== 1 ? 's' : ''} sin cambios (no se muestran).</div>` : ''}`
}

// ── UI ────────────────────────────────────────────────────────────────
export function initImportServices() {
  const dropzone  = document.getElementById('import-dropzone')
  const fileInput = document.getElementById('import-file-input')
  const btnSelect = document.getElementById('import-select-btn')
  const btnImport = document.getElementById('import-confirm-btn')
  const preview   = document.getElementById('import-preview')
  const progress  = document.getElementById('import-progress')

  if (!dropzone) return
  if (progress) progress.style.display = 'none'

  let archivoActual = null
  const textoBoton = '<i class="ti ti-upload btn__icon"></i> Importar servicios'

  btnSelect?.addEventListener('click', () => fileInput?.click())

  dropzone.addEventListener('dragover', e => {
    e.preventDefault()
    dropzone.classList.add('import-dropzone--over')
  })
  dropzone.addEventListener('dragleave', () =>
    dropzone.classList.remove('import-dropzone--over'))
  dropzone.addEventListener('drop', e => {
    e.preventDefault()
    dropzone.classList.remove('import-dropzone--over')
    if (e.dataTransfer.files[0]) revisarArchivo(e.dataTransfer.files[0])
  })
  fileInput?.addEventListener('change', e => {
    if (e.target.files[0]) revisarArchivo(e.target.files[0])
  })

  function reiniciar() {
    archivoActual = null
    btnImport.disabled = true
    btnImport.innerHTML = textoBoton
    preview.style.display = 'none'
    if (fileInput) fileInput.value = ''
  }

  async function revisarArchivo(archivo) {
    if (!/\.xlsx$/i.test(archivo.name)) {
      showAlert('Solo se aceptan archivos Excel (.xlsx).', 'warning')
      return
    }

    archivoActual = null
    btnImport.disabled = true
    preview.style.display = 'block'
    preview.innerHTML = `
      <div class="import-file-info">
        <i class="ti ti-loader import-file-info__icon"></i>
        <div>
          <div class="import-file-info__title">${escapeHtml(archivo.name)}</div>
          <div class="import-file-info__meta">Revisando el archivo...</div>
        </div>
      </div>`

    try {
      const informe = await enviarArchivo('/ingestion/catalogo/preview', archivo)
      dibujarVista(preview, archivo, informe)

      const r = informe.resumen
      if (r.se_puede_guardar) {
        archivoActual = archivo
        btnImport.disabled = false
        btnImport.innerHTML =
          `<i class="ti ti-upload btn__icon"></i> Guardar ${r.nuevo} nuevo${r.nuevo !== 1 ? 's' : ''} y ${r.actualiza} actualización${r.actualiza !== 1 ? 'es' : ''}`
      } else {
        btnImport.innerHTML = textoBoton
      }
    } catch (err) {
      showAlert(err.message, 'error')
      reiniciar()
    }
  }

  btnImport?.addEventListener('click', async () => {
    if (!archivoActual) return
    if (!confirm('¿Guardar estos cambios en el catálogo de servicios?')) return

    showSpinner(btnImport, 'Guardando...')
    try {
      const res = await enviarArchivo('/ingestion/catalogo/confirmar', archivoActual)
      showAlert(
        `Listo: ${res.creados} servicio(s) creado(s), ${res.actualizados} actualizado(s)` +
        (res.omitidos ? `, ${res.omitidos} omitido(s).` : '.'),
        'success', 8000
      )
      reiniciar()
    } catch (err) {
      showAlert(err.message, 'error')
    } finally {
      hideSpinner(btnImport)
      if (!archivoActual) btnImport.disabled = true
    }
  })
}
