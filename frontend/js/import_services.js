'use strict'

import { servicesAPI } from './api.js'
import { showAlert, showSpinner, hideSpinner } from './utils.js'

// ── Parsear precio "50–150" → promedio, "N/D" → 0 ────────────────────
function parsePrice(raw) {
  if (!raw || String(raw).trim() === 'N/D' || String(raw).trim() === 'N/A') return 0
  const clean = String(raw).replace(/[^0-9.\-–]/g, '')
  const sep = clean.includes('–') ? '–' : '-'
  if (clean.includes(sep)) {
    const parts = clean.split(sep).map(Number).filter(n => !isNaN(n) && n > 0)
    if (parts.length >= 2) return Math.round((parts[0] + parts[1]) / 2 * 10) / 10
    if (parts.length === 1) return parts[0]
  }
  const num = parseFloat(clean)
  return isNaN(num) ? 0 : num
}

// ── Leer Excel con SheetJS ────────────────────────────────────────────
async function readExcel(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result)
        const wb   = XLSX.read(data, { type: 'array' })

        const sheetName = wb.SheetNames.find(n =>
          n.toLowerCase().includes('cat') ||
          n.toLowerCase().includes('serv')
        ) || wb.SheetNames[0]

        const ws   = wb.Sheets[sheetName]
        const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: null })

        // Encontrar fila de encabezado
        let headerIdx = -1
        for (let i = 0; i < rows.length; i++) {
          const cell0 = rows[i][0] ? String(rows[i][0]).trim() : ''
          const cell1 = rows[i][1] ? String(rows[i][1]).toLowerCase() : ''
          if (cell0 === '#' || cell1.includes('servicio') || cell1.includes('assessment')) {
            headerIdx = i
            break
          }
        }
        if (headerIdx === -1) throw new Error('No se encontró la fila de encabezado')

        const header  = rows[headerIdx]
        const iNombre = header.findIndex(h => h && String(h).toLowerCase().includes('servicio'))
        const iDesc   = header.findIndex(h => h && String(h).toLowerCase().includes('descri'))
        const iPrecio = header.findIndex(h => h && String(h).toLowerCase().includes('valor'))
        const iModal  = header.findIndex(h => h && String(h).toLowerCase().includes('modal'))

        const services = []
        for (let i = headerIdx + 1; i < rows.length; i++) {
          const row = rows[i]
          if (!row || !row[0]) continue
          const num = parseInt(String(row[0]).trim(), 10)
          if (isNaN(num)) continue
          const nombre = iNombre >= 0 ? row[iNombre] : null
          if (!nombre || typeof nombre !== 'string' || !nombre.trim()) continue

          const descripcion = iDesc >= 0 && row[iDesc] ? String(row[iDesc]).trim() : null
          const modalidad   = iModal >= 0 && row[iModal] ? ` | Modalidad: ${String(row[iModal]).trim()}` : ''
          const descFinal   = descripcion ? descripcion + modalidad : modalidad.trim() || null

          services.push({
            name:        nombre.trim(),
            description: descFinal,
            base_price:  parsePrice(iPrecio >= 0 ? row[iPrecio] : null),
            active:      true,
          })
        }

        resolve(services)
      } catch (err) {
        reject(err)
      }
    }
    reader.onerror = () => reject(new Error('Error leyendo el archivo'))
    reader.readAsArrayBuffer(file)
  })
}

// ── Detectar duplicados comparando con BD ────────────────────────────
async function detectarDuplicados(serviciosExcel) {
  const existentes = await servicesAPI.getAll()
  const nombresExistentes = new Set(
    existentes.map(s => s.name.toLowerCase().trim())
  )

  const nuevos      = []
  const duplicados  = []

  for (const srv of serviciosExcel) {
    if (nombresExistentes.has(srv.name.toLowerCase().trim())) {
      duplicados.push(srv.name)
    } else {
      nuevos.push(srv)
    }
  }

  return { nuevos, duplicados }
}

// ── Importar al backend ───────────────────────────────────────────────
export async function importarServiciosExcel(serviciosNuevos, onProgress) {
  if (!serviciosNuevos.length) throw new Error('No hay servicios nuevos para importar')

  let creados = 0, errores = 0
  const fallos = []

  for (let i = 0; i < serviciosNuevos.length; i++) {
    try {
      await servicesAPI.create(serviciosNuevos[i])
      creados++
    } catch (err) {
      errores++
      fallos.push(serviciosNuevos[i].name)
    }
    if (onProgress) onProgress(i + 1, serviciosNuevos.length)
  }

  return { total: serviciosNuevos.length, creados, errores, fallos }
}

// ── UI ────────────────────────────────────────────────────────────────
export function initImportServices() {
  const dropzone    = document.getElementById('import-dropzone')
  const fileInput   = document.getElementById('import-file-input')
  const btnSelect   = document.getElementById('import-select-btn')
  const btnImport   = document.getElementById('import-confirm-btn')
  const preview     = document.getElementById('import-preview')
  const progress    = document.getElementById('import-progress')
  const progressBar = document.getElementById('import-progress-bar')
  const progressTxt = document.getElementById('import-progress-txt')

  if (!dropzone) return

  let serviciosNuevos    = []
  let serviciosDuplicados = []

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
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0])
  })
  fileInput?.addEventListener('change', e => {
    if (e.target.files[0]) handleFile(e.target.files[0])
  })

  async function handleFile(file) {
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      showAlert('Solo se aceptan archivos Excel (.xlsx o .xls)', 'warning')
      return
    }

    // Reset
    serviciosNuevos     = []
    serviciosDuplicados = []
    btnImport.disabled  = true
    preview.style.display = 'block'
    preview.innerHTML = `
      <div class="import-file-info">
        <i class="ti ti-loader import-file-info__icon"></i>
        <div>
          <div class="import-file-info__title">${file.name}</div>
          <div class="import-file-info__meta">Analizando y verificando duplicados...</div>
        </div>
      </div>`

    try {
      // 1. Leer Excel
      const todosLosServicios = await readExcel(file)
      if (!todosLosServicios.length) throw new Error('No se detectaron servicios en el archivo')

      // 2. Comparar con BD
      const resultado = await detectarDuplicados(todosLosServicios)
      serviciosNuevos     = resultado.nuevos
      serviciosDuplicados = resultado.duplicados

      // 3. Mostrar resumen con detalle de duplicados
      const hayDuplicados = serviciosDuplicados.length > 0
      const hayNuevos     = serviciosNuevos.length > 0

      preview.innerHTML = `
        <div class="import-file-info">
          <i class="ti ti-file-spreadsheet import-file-info__icon"></i>
          <div>
            <div class="import-file-info__title">${file.name}</div>
            <div class="import-file-info__meta">
              ${todosLosServicios.length} servicios en el archivo
            </div>
          </div>
        </div>

        <!-- Resumen de conteos -->
        <div class="import-summary">
          <div class="import-summary__card">
            <div class="import-summary__value">${serviciosNuevos.length}</div>
            <div class="import-summary__label">Nuevos a importar</div>
          </div>
          <div class="import-summary__card ${hayDuplicados ? 'import-summary__card--warning' : 'import-summary__card--muted'}">
            <div class="import-summary__value ${hayDuplicados ? 'import-summary__value--warning' : 'import-summary__value--muted'}">
              ${serviciosDuplicados.length}
            </div>
            <div class="import-summary__label">Ya existen en BD</div>
          </div>
        </div>

        ${hayNuevos ? `
          <!-- Preview de nuevos -->
          <div class="import-sample">
            <div class="import-sample__title">
              Primeros 3 servicios nuevos:
            </div>
            ${serviciosNuevos.slice(0, 3).map(s => `
              <div class="import-sample-row">
                <span class="import-sample-name">${s.name}</span>
                <span class="import-sample-price">
                  ${s.base_price > 0 ? s.base_price + ' UF' : 'A convenir'}
                </span>
              </div>`).join('')}
          </div>` : ''}

        ${hayDuplicados ? `
          <!-- Detalle de duplicados -->
          <details class="import-duplicates">
            <summary class="import-duplicates__summary">
              <i class="ti ti-alert-triangle"></i>
              ${serviciosDuplicados.length} servicio${serviciosDuplicados.length > 1 ? 's' : ''} ya existe${serviciosDuplicados.length === 1 ? '' : 'n'} — se omitirán
            </summary>
            <div class="import-duplicates__list">
              ${serviciosDuplicados.map(n => `
                <div class="import-duplicates__item">
                  <i class="ti ti-x import-duplicates__icon"></i>${n}
                </div>`).join('')}
            </div>
          </details>` : ''}

        ${!hayNuevos ? `
          <div class="import-empty">
            <i class="ti ti-circle-check import-empty__icon"></i>
            Todos los servicios ya están en la base de datos. No hay nada que importar.
          </div>` : ''}`

      if (hayNuevos) {
        btnImport.disabled = false
        btnImport.innerHTML = `<i class="ti ti-upload btn__icon"></i> Importar ${serviciosNuevos.length} servicio${serviciosNuevos.length > 1 ? 's' : ''} nuevo${serviciosNuevos.length > 1 ? 's' : ''}`
      }

    } catch (err) {
      showAlert('Error al leer el archivo: ' + err.message, 'error')
      preview.style.display = 'none'
    }
  }

  // Confirmar importación — solo los nuevos
  btnImport?.addEventListener('click', async () => {
    if (!serviciosNuevos.length) return

    showSpinner(btnImport, 'Importando...')
    progress.style.display = 'block'

    try {
      const result = await importarServiciosExcel(serviciosNuevos, (done, total) => {
        const pct = Math.round((done / total) * 100)
        if (progressBar) progressBar.style.width = pct + '%'
        if (progressTxt) progressTxt.textContent = `${done} / ${total}`
      })

      const msgDup = serviciosDuplicados.length
        ? ` (${serviciosDuplicados.length} ya existían y se omitieron)`
        : ''

      if (result.errores === 0) {
        showAlert(`✅ ${result.creados} servicios importados correctamente.${msgDup}`, 'success', 7000)
      } else {
        showAlert(
          `Importados ${result.creados} de ${result.total}. ${result.errores} fallaron.${msgDup}`,
          'warning', 8000
        )
      }

      // Reset
      preview.style.display = 'none'
      progress.style.display = 'none'
      serviciosNuevos     = []
      serviciosDuplicados = []
      if (fileInput) fileInput.value = ''

    } catch (err) {
      showAlert('Error al importar: ' + err.message, 'error')
    } finally {
      hideSpinner(btnImport)
      btnImport.disabled = true
      btnImport.innerHTML = '<i class="ti ti-upload btn__icon"></i> Importar servicios'
    }
  })
}
