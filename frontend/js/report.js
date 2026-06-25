'use strict'

import { clientsAPI, servicesAPI, proposalsAPI } from './api.js'
import { showAlert, showSpinner, hideSpinner, requireAuth, escapeHtml, escapeAttr } from './utils.js'
import { CATEGORIAS_ORDEN, agrupar } from './categories.js'

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
}

function actualizarBoton() {
  const btn  = document.getElementById('r-generar-btn')
  const sinIA = document.getElementById('r-sin-ia')?.checked
  if (!btn) return
  const ok = clienteSel && seleccionados.size > 0
  btn.disabled = !ok
  btn.innerHTML = ok
    ? `<i class="ti ti-${sinIA ? 'file-download' : 'sparkles'} btn__icon"></i> ${sinIA ? 'Generar PDF' : 'Generar con IA'}`
    : '<i class="ti ti-sparkles btn__icon"></i> Generar informe con IA'
}

// ── Pasos de progreso ─────────────────────────────────────────────────
function setStep(id, estado) {
  // estado: 'active' | 'done' | ''
  const el = document.getElementById(id)
  if (!el) return
  el.className = 'ia-step' + (estado ? ` ia-step--${estado}` : '')
}
function resetSteps() {
  ['step-intro','step-riesgo','step-justif','step-valor','step-conclusion','step-pdf']
    .forEach(id => setStep(id, ''))
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
      prog.style.display = 'block'
      resetSteps()
    }

    // Simular progreso visual (el backend procesa en secuencia)
    let stepTimer = null
    if (usarIA) {
      const pasos = [
        ['step-intro',      1500],
        ['step-riesgo',     7000],
        ['step-justif',    13000],
        ['step-valor',     19000],
        ['step-conclusion',24000],
        ['step-pdf',       29000],
      ]
      let prev = null
      pasos.forEach(([id, delay]) => {
        setTimeout(() => {
          if (prev) setStep(prev, 'done')
          setStep(id, 'active')
          prev = id
        }, delay)
      })
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

      // Marcar todos como done
      if (usarIA) {
        ['step-intro','step-riesgo','step-justif','step-valor','step-conclusion','step-pdf']
          .forEach(id => setStep(id, 'done'))
      }

      // Descargar PDF
      const blob   = await resp.blob()
      const url    = URL.createObjectURL(blob)
      const a      = document.createElement('a')
      const nombre = clienteSel.company_name.replace(/\s+/g,'_')
      a.href       = url
      a.download   = `Informe_Preventa_${nombre}.pdf`
      a.click()
      URL.revokeObjectURL(url)

      showAlert(
        `✅ Informe generado${usarIA ? ' con IA' : ''} para ${clienteSel.company_name}`,
        'success', 6000
      )

    } catch (err) {
      showAlert('Error: ' + err.message, 'error')
      resetSteps()
    } finally {
      hideSpinner(btn)
      if (!sinIA?.checked) prog.style.display = 'none'
      actualizarBoton()
    }
  })
}
