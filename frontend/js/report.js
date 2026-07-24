'use strict'

import { clientsAPI, servicesAPI, proposalsAPI } from './api.js'
import { showAlert, showSpinner, hideSpinner, requireAuth, escapeHtml, escapeAttr } from './utils.js'
import { CATEGORIAS_ORDEN, agrupar, categorizar } from './categories.js'

// ── Estado ────────────────────────────────────────────────────────────
let clientes      = []
let servicios     = []
let companies     = []
let seleccionados = new Set()
let clienteSel    = null
let companySel    = null
let logoBase64    = null

// ── Init ──────────────────────────────────────────────────────────────
export async function initReport() {

  console.log("REPORT INIT")

  if (!requireAuth()) return

  await Promise.all([
    cargarClientes(),
    cargarServicios(),
    cargarCompanies()
  ])

  bindCliente()
  bindCompany()
  bindLogo()
  bindGenerar()
  bindServiciosModal()
  bindPreviewToggle()
  updatePreview()
}

async function cargarClientes() {
  try {
    clientes = await clientsAPI.getAll()
    const sel = document.getElementById('r-cliente')
    if (!sel) return
    sel.innerHTML = '<option value="">— Selecciona —</option>' +
      clientes.map(c =>
        `<option value="${Number(c.id) || 0}">${escapeHtml(c.company_name || '')} · ${escapeHtml(c.contact_name || '')}</option>`
      ).join('')
  } catch (e) { showAlert('Error cargando clientes', 'error') }
}

async function cargarServicios() {
  try {
    servicios = await servicesAPI.getAll()
    renderCatalogo()
  } catch (e) { showAlert('Error cargando servicios', 'error') }
}

async function cargarCompanies() {

  try {

    console.log("entrando cargarCompanies")

    companies = await proposalsAPI.getCompanies()

    console.log("companies:", companies)

    const sel = document.getElementById('r-company')

    if (!sel) return

    sel.innerHTML =
      '<option value="">— Selecciona empresa —</option>' +
      companies.map(c =>
        `
        <option value="${c.id}">
          ${escapeHtml(c.name)}
        </option>
        `
      ).join('')


  } catch(e) {

    console.error("ERROR companies", e)
    showAlert(
      "Error cargando empresas emisoras",
      "error"
    )
  }
}


function bindCompany(){

  const sel =
    document.getElementById('r-company')

  if(!sel) return

  sel.addEventListener(
    'change',
    ()=>{

      const id = Number(sel.value)

      companySel =
        companies.find(c=>c.id===id)
        || null
      updatePreview()
    }
  )
}

function bindCliente() {
  const sel    = document.getElementById('r-cliente')
  const search = document.getElementById('r-cliente-search')
  if (!sel) return

  sel.addEventListener('change', () => {
    const id = parseInt(sel.value)
    clienteSel = clientes.find(c => c.id === id) || null
    actualizarBoton()
    updatePreview()
  })
  search?.addEventListener('input', () => {
    const q = search.value.toLowerCase()
    Array.from(sel.options).forEach(o => {
      o.hidden = !!o.value && !o.text.toLowerCase().includes(q)
    })
  })
}

function renderCatalogo() {
  const cont = document.getElementById('r-catalogo')
  if (!cont) return
  const grupos = agrupar(servicios)
  cont.innerHTML = ''

  for (const [cat, srvs] of Object.entries(grupos)) {
    if (!srvs.length) continue
    const bloque = document.createElement('div')
    bloque.className = 'r-categoria'
    bloque.innerHTML = `
      <div class="r-categoria__header" onclick="rToggleCat(this)">
        <span class="r-categoria__nombre">${escapeHtml(cat)}</span>
        <span class="badge badge--info badge--xs">${srvs.length}</span>
        <button class="r-categoria__sel-all btn btn--xs btn--secondary"
          onclick="event.stopPropagation();rSelAll('${cat.replace(/'/g,"\\'")}')">
          Todos
        </button>
        <i class="ti ti-chevron-down"></i>
      </div>
      <div class="r-categoria__body">
        ${srvs.map(s => {
          const serviceId = Number(s.id) || 0
          return `
          <label class="r-servicio" data-cat="${escapeAttr(cat)}">
            <input type="checkbox" class="r-servicio__check"
              value="${serviceId}" onchange="rCheck(${serviceId}, this.checked)">
            <div>
              <div class="r-servicio__nombre">${escapeHtml(s.name || '')}</div>
              ${s.description
                ? `<div class="r-servicio__desc">${escapeHtml(s.description.split('|')[0].trim().slice(0,80))}...</div>`
                : ''}
            </div>
          </label>`
        }).join('')}
      </div>`
    cont.appendChild(bloque)
  }
}

window.rToggleCat = function(h) {
  const b = h.nextElementSibling
  const i = h.querySelector('i')
  b.classList.toggle('r-categoria__body--open')
  i.classList.toggle('ti-chevron-up')
  i.classList.toggle('ti-chevron-down')
}
window.rSelAll = function(cat) {
  const checks = document.querySelectorAll(`.r-servicio[data-cat="${cat}"] .r-servicio__check`)
  const all = Array.from(checks).every(c => c.checked)
  checks.forEach(c => { c.checked = !all; rCheck(parseInt(c.value), !all) })
}
window.rCheck = function(id, on) {
  if (on) seleccionados.add(id); else seleccionados.delete(id)
  const el = document.getElementById('r-contador')
  if (el) el.textContent = seleccionados.size > 0
    ? `${seleccionados.size} servicio${seleccionados.size > 1 ? 's' : ''} seleccionado${seleccionados.size > 1 ? 's' : ''}`
    : 'Ningún servicio seleccionado'
  actualizarBoton()
  updateServiciosBoxSummary()
  updatePreview()
}

// ── Caja resumen de servicios (abre el modal) ──────────────────────────
function updateServiciosBoxSummary() {
  const el = document.getElementById('r-servicios-box-summary')
  if (!el) return
  el.textContent = seleccionados.size > 0
    ? `${seleccionados.size} servicio${seleccionados.size > 1 ? 's' : ''} seleccionado${seleccionados.size > 1 ? 's' : ''}`
    : 'Ningún servicio seleccionado'
}

function bindServiciosModal() {
  const box     = document.getElementById('r-servicios-box')
  const overlay = document.getElementById('r-modal-overlay')
  const closeBtn = document.getElementById('r-modal-close')
  const doneBtn  = document.getElementById('r-modal-done')
  const search   = document.getElementById('r-modal-search')
  if (!box || !overlay) return

  const open  = () => { overlay.style.display = 'flex' }
  const close = () => { overlay.style.display = 'none' }

  box.addEventListener('click', open)
  box.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open() } })
  closeBtn?.addEventListener('click', close)
  doneBtn?.addEventListener('click', close)
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close() })

  search?.addEventListener('input', () => {
    const q = search.value.toLowerCase().trim()
    document.querySelectorAll('#r-catalogo .r-categoria').forEach(bloque => {
      let anyVisible = false
      bloque.querySelectorAll('.r-servicio').forEach(row => {
        const match = !q || row.textContent.toLowerCase().includes(q)
        row.style.display = match ? '' : 'none'
        if (match) anyVisible = true
      })
      bloque.style.display = anyVisible ? '' : 'none'
      if (q && anyVisible) {
        bloque.querySelector('.r-categoria__body')?.classList.add('r-categoria__body--open')
        const icon = bloque.querySelector('.r-categoria__header i')
        icon?.classList.add('ti-chevron-up')
        icon?.classList.remove('ti-chevron-down')
      }
    })
  })
}

// ── Vista previa de lo que se va a generar ─────────────────────────────
function updatePreview() {
  const clienteEl  = document.getElementById('r-preview-cliente')
  const empresaEl  = document.getElementById('r-preview-empresa')
  const countEl    = document.getElementById('r-preview-count')
  const chipsEl    = document.getElementById('r-preview-chips')
  const toggleEl   = document.getElementById('r-preview-toggle')
  const detailEl   = document.getElementById('r-preview-detail')
  if (!clienteEl) return

  clienteEl.textContent = clienteSel ? clienteSel.company_name : 'Selecciona un cliente'
  empresaEl.textContent = companySel ? companySel.name : 'Empresa emisora'
  countEl.textContent = `${seleccionados.size} servicio${seleccionados.size !== 1 ? 's' : ''}`

  if (!seleccionados.size) {
    chipsEl.innerHTML = '<span class="report-chip report-chip--muted">Ningún servicio seleccionado</span>'
    toggleEl.style.display = 'none'
    detailEl.style.display = 'none'
    detailEl.innerHTML = ''
    return
  }

  // Agrupar seleccionados por categoría (para los chips resumen y el detalle)
  const grupos = {} // { categoria: [servicio, ...] }
  seleccionados.forEach(id => {
    const s = servicios.find(x => Number(x.id) === id)
    if (!s) return
    const catRaw = categorizar(s.name, s.description)
    const cat = catRaw.replace(/^\S+\s+/, '') // quita el emoji inicial
    if (!grupos[cat]) grupos[cat] = []
    grupos[cat].push(s)
  })

  chipsEl.innerHTML = Object.entries(grupos)
    .map(([cat, list]) => `<span class="report-chip">${escapeHtml(cat)} · ${list.length}</span>`)
    .join('')

  toggleEl.style.display = 'inline-flex'
  detailEl.innerHTML = Object.entries(grupos).map(([cat, list]) => `
    <div class="report-preview__detail-group">
      <div class="report-preview__detail-cat">${escapeHtml(cat)}</div>
      ${list.map(s => `<div class="report-preview__detail-item"><i class="ti ti-check"></i> ${escapeHtml(s.name || '')}</div>`).join('')}
    </div>
  `).join('')
}

function bindPreviewToggle() {
  const toggleEl = document.getElementById('r-preview-toggle')
  const detailEl = document.getElementById('r-preview-detail')
  if (!toggleEl || !detailEl) return
  toggleEl.addEventListener('click', () => {
    const open = detailEl.style.display !== 'none'
    detailEl.style.display = open ? 'none' : 'block'
    toggleEl.classList.toggle('report-preview__toggle--open', !open)
    toggleEl.innerHTML = open
      ? '<i class="ti ti-chevron-down"></i> Ver servicios seleccionados'
      : '<i class="ti ti-chevron-up"></i> Ocultar servicios seleccionados'
  })
}

function actualizarBoton() {
  const btn  = document.getElementById('r-generar-btn')
  const sinIA = document.getElementById('r-sin-ia')?.checked
  if (!btn) return
  const ok = clienteSel && seleccionados.size > 0
  btn.disabled = !ok
  btn.innerHTML = ok
    ? `<i class="ti ti-${sinIA ? 'file-download' : 'sparkles'} btn__icon"></i> ${sinIA ? 'Generar PDF' : 'Generar informe'}`
    : '<i class="ti ti-sparkles btn__icon"></i> Generar informe'
}

// ── Cronómetro real (no simula etapas ni porcentajes inventados) ──────
let progressTimerInterval = null
let progressStartTime = null

function startProgressTimer() {
  progressStartTime = Date.now()
  const timeEl = document.getElementById('r-progress-time')
  if (timeEl) timeEl.textContent = '00:00'
  progressTimerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - progressStartTime) / 1000)
    const mm = String(Math.floor(elapsed / 60)).padStart(2, '0')
    const ss = String(elapsed % 60).padStart(2, '0')
    if (timeEl) timeEl.textContent = `${mm}:${ss}`
  }, 1000)
}

function stopProgressTimer(finalLabel) {
  if (progressTimerInterval) clearInterval(progressTimerInterval)
  progressTimerInterval = null
  const labelEl = document.getElementById('r-progress-label')
  if (labelEl && finalLabel) labelEl.textContent = finalLabel

  const totalSeconds = progressStartTime ? Math.floor((Date.now() - progressStartTime) / 1000) : 0
  const mm = Math.floor(totalSeconds / 60)
  const ss = totalSeconds % 60
  return {
    seconds: totalSeconds,
    text: mm > 0 ? `${mm}m ${ss}s` : `${ss}s`,
  }
}

// ── Generar ───────────────────────────────────────────────────────────
// ── Logo del cliente ────────────────────────────────────────────────
function bindLogo() {
  const input     = document.getElementById('r-logo-input')
  const dropArea  = document.getElementById('logo-drop-area')
  const emptyEl   = document.getElementById('logo-empty')
  const previewEl = document.getElementById('logo-preview')
  const imgEl     = document.getElementById('logo-img-preview')
  const removeBtn = document.getElementById('logo-remove')
  if (!input) return

  function loadFile(file) {
    if (!file || !file.type.startsWith('image/')) {
      showAlert('Solo se aceptan imágenes PNG, JPG o SVG.', 'warning')
      return
    }
    if (file.size > 2 * 1024 * 1024) {
      showAlert('El logo no debe superar 2MB.', 'warning')
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      logoBase64 = e.target.result
      imgEl.src  = logoBase64
      emptyEl.style.display   = 'none'
      previewEl.style.display = 'flex'
      dropArea.style.borderStyle = 'solid'
      dropArea.style.borderColor = 'var(--cp-blue-main)'
    }
    reader.readAsDataURL(file)
  }

  input.addEventListener('change', () => { if (input.files[0]) loadFile(input.files[0]) })

  removeBtn?.addEventListener('click', () => {
    logoBase64 = null
    input.value = ''
    imgEl.src   = ''
    emptyEl.style.display   = 'flex'
    previewEl.style.display = 'none'
    dropArea.style.borderStyle = 'dashed'
    dropArea.style.borderColor = ''
  })

  // Drag & drop
  dropArea.addEventListener('dragover', (e) => { e.preventDefault(); dropArea.classList.add('drag-over') })
  dropArea.addEventListener('dragleave', () => dropArea.classList.remove('drag-over'))
  dropArea.addEventListener('drop', (e) => {
    e.preventDefault()
    dropArea.classList.remove('drag-over')
    const file = e.dataTransfer.files[0]
    if (file) loadFile(file)
  })
}

function bindGenerar() {
  const btn  = document.getElementById('r-generar-btn')
  const sinIA = document.getElementById('r-sin-ia')
  const prog = document.getElementById('r-progress')

  sinIA?.addEventListener('change', actualizarBoton)

  btn?.addEventListener('click', async () => {
    if (!clienteSel || !seleccionados.size) return

    const usarIA   = !sinIA?.checked
    const titulo   = document.getElementById('r-titulo')?.value.trim()
      || `Informe de Preventa — ${clienteSel.company_name}`
    const contexto = document.getElementById('r-antecedente')?.value.trim() || ''

    showSpinner(btn, usarIA ? 'Iniciando IA...' : 'Generando...')
    if (usarIA) {
      prog.style.display = 'flex'
      startProgressTimer()
    }

    try {
      const resp = await proposalsAPI.generate({

        cliente_id: clienteSel.id,

        service_ids: Array.from(seleccionados),

        titulo_proyecto: titulo,

        antecedente: contexto,

        usar_ia: true,

        logo_base64: logoBase64 || null,

        company_id: companySel?.id || null

      })

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || `Error ${resp.status}`)
      }

      // Marcar completado
      let tiempoInfo = { seconds: 0, text: '' }
      if (usarIA) tiempoInfo = stopProgressTimer('Completado')

      // Descargar PDF
      const blob   = await resp.blob()
      const url    = URL.createObjectURL(blob)
      const a      = document.createElement('a')
      const nombre = clienteSel.company_name.replace(/\s+/g,'_')
      a.href       = url
      a.download   = `Informe_Preventa_${nombre}.pdf`
      a.click()
      URL.revokeObjectURL(url)

      const sufijoTiempo = usarIA ? ` — generado en ${tiempoInfo.text}` : ''
      showAlert(
        `✅ Informe generado${usarIA ? ' con IA' : ''} para ${clienteSel.company_name}${sufijoTiempo}`,
        'success', 8000
      )

      if (usarIA) {
        console.log(
          `[Generar Informe] Completado en ${tiempoInfo.seconds}s (${tiempoInfo.text}) — ` +
          `cliente: ${clienteSel.company_name}, servicios: ${seleccionados.size}, modelo backend: ver terminal uvicorn`
        )
      }

      if (usarIA) {
        console.log(
          `[Generar Informe] Completado en ${tiempoInfo.seconds}s (${tiempoInfo.text}) — ` +
          `cliente: ${clienteSel.company_name}, servicios: ${seleccionados.size}, modelo backend: ver terminal uvicorn`
        )
      }

    } catch (err) {
      const tiempoInfo = usarIA ? stopProgressTimer('Error') : { seconds: 0, text: '' }
      showAlert(
        `Error: ${err.message}${usarIA ? ` (tras ${tiempoInfo.text})` : ''}`,
        'error'
      )
      if (usarIA) {
        console.log(`[Generar Informe] Falló tras ${tiempoInfo.seconds}s (${tiempoInfo.text}) — error: ${err.message}`)
      }
    } finally {
      hideSpinner(btn)
      if (!sinIA?.checked) prog.style.display = 'none'
      actualizarBoton()
    }
  })
}
