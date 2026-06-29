'use strict'

/**
 * companies.js — Módulo de Empresas Emisoras.
 */

import { BASE_URL } from './config.js'
import { requireAuth, showAlert, escapeHtml, openModal, closeModal } from './utils.js'

// ── Estado ──────────────────────────────────────────────────────────────
let companies       = []
let editingId       = null       // null = nueva empresa
let uploadCompanyId = null
let uploadType      = 'portada'  // 'portada' | 'interior' | 'logo'

// ── Init ─────────────────────────────────────────────────────────────────
export async function initCompanies() {
  requireAuth()
  bindButtons()
  await loadCompanies()
}

// ── API helpers ───────────────────────────────────────────────────────────
function getToken() {
  return sessionStorage.getItem('cp_token') || ''
}

async function api(method, path, body = null) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`
  }
  const opts = { method, headers }
  if (body) opts.body = JSON.stringify(body)
  const res = await fetch(`${BASE_URL}${path}`, opts)
  if (!res.ok) {
    const d = await res.json().catch(() => ({}))
    throw new Error(d.detail || `Error ${res.status}`)
  }
  const txt = await res.text()
  return txt ? JSON.parse(txt) : null
}

async function uploadImage(companyId, type, file) {
  const fd = new FormData()
  fd.append('image_type', type)
  fd.append('file', file)
  const res = await fetch(`${BASE_URL}/companies/${companyId}/upload-image`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${getToken()}` },
    body: fd
  })
  if (!res.ok) {
    const d = await res.json().catch(() => ({}))
    throw new Error(d.detail || `Error ${res.status}`)
  }
  return res.json()
}

// El endpoint /companies/image-preview es público → <img src> puede cargarlo directamente
function previewSrc(path) {
  if (!path) return ''
  return `${BASE_URL}/companies/image-preview?path=${encodeURIComponent(path)}`
}

// ── Cargar y renderizar ───────────────────────────────────────────────────
async function loadCompanies() {
  try {
    companies = await api('GET', '/companies/')
    renderGrid()
  } catch (e) {
    showAlert('Error cargando empresas: ' + e.message, 'error')
  }
}

function renderGrid() {
  const grid  = document.getElementById('companies-grid')
  const empty = document.getElementById('companies-empty')
  if (!grid) return

  if (!companies.length) {
    grid.innerHTML = ''
    if (empty) empty.style.display = 'flex'
    return
  }
  if (empty) empty.style.display = 'none'

  grid.innerHTML = companies.map(c => cardHtml(c)).join('')

  // Bind botones de tarjeta
  grid.querySelectorAll('[data-action]').forEach(btn => {
    btn.addEventListener('click', onCardAction)
  })
}

function cardHtml(c) {
  const logoHtml = c.logo_path
    ? `<img class="co-avatar" src="${previewSrc(c.logo_path)}" alt="logo" onerror="this.style.display='none'">`
    : `<div class="co-avatar co-avatar--icon"><i class="ti ti-building"></i></div>`

  const badge = c.active
    ? `<span class="co-badge co-badge--on">Activa</span>`
    : `<span class="co-badge co-badge--off">Inactiva</span>`

  const colorsRow = (c.primary_color || c.secondary_color || c.content_color)
    ? `<div class="co-colors">
        ${c.primary_color   ? `<span class="co-dot" style="background:${c.primary_color}" title="Portada: ${c.primary_color}"></span>` : ''}
        ${c.secondary_color ? `<span class="co-dot" style="background:${c.secondary_color}" title="Banner: ${c.secondary_color}"></span>` : ''}
        ${c.content_color   ? `<span class="co-dot" style="background:${c.content_color}" title="Contenido: ${c.content_color}"></span>` : ''}
        <span class="co-colors__label">${[c.primary_color, c.secondary_color, c.content_color].filter(Boolean).join(' / ')}</span>
      </div>`
    : `<span class="co-colors__label co-colors__label--none">Sin colores definidos</span>`

  const thumbPortada  = thumbHtml(c.portada_path,  'Portada')
  const thumbInterior = thumbHtml(c.interior_path, 'Interior')

  const toggleLabel = c.active ? 'Desactivar' : 'Activar'
  const toggleIcon  = c.active ? 'ti-eye-off'  : 'ti-eye'

  return `
<article class="co-card ${c.active ? '' : 'co-card--off'}" data-id="${c.id}">
  <div class="co-card__head">
    ${logoHtml}
    <div class="co-card__info">
      <span class="co-card__name">${escapeHtml(c.name)}</span>
      ${badge}
    </div>
  </div>
  ${colorsRow}
  <div class="co-thumbs">
    ${thumbPortada}
    ${thumbInterior}
  </div>
  <div class="co-card__foot">
    <button class="btn btn--sm btn--secondary" data-action="upload" data-id="${c.id}" type="button">
      <i class="ti ti-upload"></i> Imágenes
    </button>
    <button class="btn btn--sm btn--secondary" data-action="layout" data-id="${c.id}" type="button">
      <i class="ti ti-layout"></i> Diseño
    </button>
    <button class="btn btn--sm btn--secondary" data-action="edit" data-id="${c.id}" type="button">
      <i class="ti ti-edit"></i> Editar
    </button>
    <button class="btn btn--sm btn--ghost ${c.active ? 'btn--danger' : ''}"
            data-action="toggle" data-id="${c.id}" data-active="${c.active}" type="button">
      <i class="ti ${toggleIcon}"></i> ${toggleLabel}
    </button>
  </div>
</article>`
}

function thumbHtml(path, label) {
  if (path) {
    return `
    <div class="co-thumb">
      <img src="${previewSrc(path)}" alt="${label}"
           onerror="this.parentElement.classList.add('co-thumb--empty');this.remove()">
      <span class="co-thumb__lbl">${label}</span>
    </div>`
  }
  return `
  <div class="co-thumb co-thumb--empty">
    <i class="ti ti-file-off"></i>
    <span class="co-thumb__lbl">${label}</span>
  </div>`
}

// ── Acciones de tarjeta ───────────────────────────────────────────────────
function onCardAction(e) {
  e.stopPropagation()
  const btn    = e.currentTarget
  const action = btn.dataset.action
  const id     = Number(btn.dataset.id)

  if (action === 'edit')   openEditModal(id)
  if (action === 'upload') openUploadModal(id)
  if (action === 'layout') {
    window.location.href = `editor.html?id=${id}`
  }
  if (action === 'toggle') toggleActive(id, btn.dataset.active === 'true')
}

async function toggleActive(id, currentActive) {
  try {
    await api('PUT', `/companies/${id}`, { active: !currentActive })
    showAlert(currentActive ? 'Empresa desactivada' : 'Empresa activada', 'success')
    await loadCompanies()
  } catch (e) {
    showAlert('Error: ' + e.message, 'error')
  }
}

// ── Modal Crear / Editar ──────────────────────────────────────────────────
function openNewModal() {
  editingId = null
  document.getElementById('modal-company-title').textContent = 'Nueva empresa'
  document.getElementById('form-company').reset()
  setColorValue('fc-primary',   '#155FCF')
  setColorValue('fc-secondary', '#8EE3C8')
  setColorValue('fc-content',   '#1A2B5F')
  openModal('modal-company')
}

function openEditModal(id) {
  const c = companies.find(x => x.id === id)
  if (!c) return
  editingId = id
  document.getElementById('modal-company-title').textContent = 'Editar empresa'
  document.getElementById('fc-name').value = c.name || ''
  setColorValue('fc-primary',   c.primary_color   || '#155FCF')
  setColorValue('fc-secondary', c.secondary_color || '#8EE3C8')
  setColorValue('fc-content',   c.content_color   || '#1A2B5F')
  openModal('modal-company')
}

function setColorValue(pickerId, hex) {
  const picker = document.getElementById(pickerId)
  const text   = document.getElementById(pickerId + '-hex')
  if (picker) picker.value = hex
  if (text)   text.value   = hex
}

async function submitCompanyForm(e) {
  e.preventDefault()
  const name      = document.getElementById('fc-name').value.trim()
  const primary   = document.getElementById('fc-primary-hex').value.trim() || null
  const secondary = document.getElementById('fc-secondary-hex').value.trim() || null
  const content   = document.getElementById('fc-content-hex').value.trim() || null

  if (!name) { showAlert('El nombre es obligatorio', 'error'); return }

  const payload = { name, primary_color: primary, secondary_color: secondary, content_color: content }
  try {
    if (editingId) {
      await api('PUT', `/companies/${editingId}`, payload)
      showAlert('Empresa actualizada', 'success')
    } else {
      await api('POST', '/companies/', payload)
      showAlert('Empresa creada', 'success')
    }
    closeModal('modal-company')
    await loadCompanies()
  } catch (e) {
    showAlert('Error: ' + e.message, 'error')
  }
}

// ── Modal Upload Imágenes ─────────────────────────────────────────────────
function openUploadModal(id) {
  uploadCompanyId = id
  const c = companies.find(x => x.id === id)
  document.getElementById('modal-upload-title').textContent =
    c ? `Imágenes — ${escapeHtml(c.name)}` : 'Subir imágenes de plantilla'
  setActiveTab('portada')
  clearPreview()
  openModal('modal-upload')
}

function setActiveTab(type) {
  uploadType = type
  document.querySelectorAll('.upload-tab').forEach(t => {
    const isActive = t.dataset.type === type
    t.classList.toggle('upload-tab--active', isActive)
    t.setAttribute('aria-pressed', isActive ? 'true' : 'false')
  })
  const labels = {
    portada:  'Portada (base_portada.png) — imagen A4 de fondo para la primera página',
    interior: 'Interior (base_interior.png) — imagen A4 de fondo para páginas interiores',
    logo:     'Logo — logotipo de la empresa que aparece en el PDF'
  }
  const el = document.getElementById('upload-type-label')
  if (el) {
    // Mantener el ícono de info y actualizar solo el texto
    const icon = el.querySelector('i')
    el.textContent = labels[type] || ''
    if (icon) el.prepend(icon)
  }
  clearPreview()
}

function clearPreview() {
  const preview = document.getElementById('upload-preview')
  const input   = document.getElementById('upload-file')
  if (preview) { preview.src = ''; preview.classList.remove('upload-zone__preview--visible') }
  if (input)   input.value = ''
}

function onFileSelected(e) {
  const file = e.target.files[0]
  if (!file) return
  const preview = document.getElementById('upload-preview')
  const reader  = new FileReader()
  reader.onload = ev => {
    preview.src = ev.target.result
    preview.classList.add('upload-zone__preview--visible')
  }
  reader.readAsDataURL(file)
}

async function submitUpload() {
  const file = document.getElementById('upload-file')?.files[0]
  if (!file) { showAlert('Selecciona una imagen primero', 'error'); return }
  if (!uploadCompanyId) return

  const btn = document.getElementById('btn-upload-confirm')
  btn.disabled = true
  btn.innerHTML = '<i class="ti ti-loader"></i> Subiendo…'

  try {
    await uploadImage(uploadCompanyId, uploadType, file)
    showAlert('✅ Imagen subida correctamente', 'success')
    closeModal('modal-upload')
    await loadCompanies()
  } catch (e) {
    showAlert('Error: ' + e.message, 'error')
  } finally {
    btn.disabled = false
    btn.innerHTML = '<i class="ti ti-upload"></i> Subir imagen'
  }
}

// ── Color pickers ─────────────────────────────────────────────────────────
function bindColorPickers() {
  ;[['fc-primary', 'fc-primary-hex'], ['fc-secondary', 'fc-secondary-hex'], ['fc-content', 'fc-content-hex']].forEach(([pid, hid]) => {
    const picker = document.getElementById(pid)
    const hex    = document.getElementById(hid)
    if (!picker || !hex) return
    picker.addEventListener('input', () => { hex.value = picker.value })
    hex.addEventListener('input', () => {
      if (/^#[0-9A-Fa-f]{6}$/.test(hex.value)) picker.value = hex.value
    })
  })
}

// ── Drag & Drop ───────────────────────────────────────────────────────────
function bindDropZone() {
  const zone = document.getElementById('upload-zone')
  if (!zone) return
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('upload-zone--over') })
  zone.addEventListener('dragleave', () => zone.classList.remove('upload-zone--over'))
  zone.addEventListener('drop', e => {
    e.preventDefault()
    zone.classList.remove('upload-zone--over')
    const file = e.dataTransfer.files[0]
    if (!file) return
    const dt = new DataTransfer()
    dt.items.add(file)
    document.getElementById('upload-file').files = dt.files
    onFileSelected({ target: { files: [file] } })
  })
}

// ── Bind global ───────────────────────────────────────────────────────────
function bindButtons() {
  // Botón nueva empresa
  document.getElementById('btn-new-company')
    ?.addEventListener('click', openNewModal)
  document.getElementById('btn-new-company-2')
    ?.addEventListener('click', openNewModal)

  // Form empresa
  document.getElementById('form-company')
    ?.addEventListener('submit', submitCompanyForm)

  // Botones data-close-modal
  document.querySelectorAll('[data-close-modal]').forEach(btn =>
    btn.addEventListener('click', () => closeModal(btn.dataset.closeModal))
  )

  // Cerrar con Escape
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeModal('modal-company')
      closeModal('modal-upload')
    }
  })

  // Tabs upload — delegación en el contenedor para mayor robustez
  document.getElementById('modal-upload')?.addEventListener('click', e => {
    const tab = e.target.closest('.upload-tab')
    if (tab && tab.dataset.type) {
      e.stopPropagation()
      setActiveTab(tab.dataset.type)
    }
  })

  // File input
  document.getElementById('upload-file')
    ?.addEventListener('change', onFileSelected)

  // Confirmar upload
  document.getElementById('btn-upload-confirm')
    ?.addEventListener('click', submitUpload)

  bindColorPickers()
  bindDropZone()
  initLayoutEditor()
}

/* ═══════════════════════════════════════════════
   EDITOR DISEÑO — OPCIÓN 1
   Canvas izquierda (grande) + sidebar derecha
   Timing: MutationObserver detecta cuando el modal
   es visible antes de renderizar bloques
═══════════════════════════════════════════════ */

const A4W = 210, A4H = 297

let ED = {
  company:  null,
  page:     'portada',
  block:    'titulo',
  section:  'banner',
  drag:     false,
  dragOff:  {x:0,y:0},
}

let edCfg = {}

const ED_DEF = {
  portada: {
    titulo:       {x:28, y:88,  size:34, weight:700, align:'left', color:null},
    objetivo:     {x:28, y:130, size:11, weight:400, align:'left', color:null},
    logo_cliente: {x:130, y:160},
  },
  contenido: {
    banner: {y_start:45, size:26, weight:700, bg_color:null, text_color:null},
    cuerpo: {y_start:75, size:10.5, weight:400, color:null},
  }
}

// ── Abrir ───────────────────────────────────────
function openLayoutEditor(id) {
  const c = companies.find(x => x.id === id)
  if (!c) return
  ED.company = c
  const s = c.portada_config || {}
  edCfg = {
    portada: {
      titulo:       {...ED_DEF.portada.titulo,       ...(s.titulo       ||{})},
      objetivo:     {...ED_DEF.portada.objetivo,     ...(s.objetivo     ||{})},
      logo_cliente: {...ED_DEF.portada.logo_cliente, ...(s.logo_cliente ||{})},
    },
    contenido: {
      banner: {...ED_DEF.contenido.banner, ...(s.banner||{})},
      cuerpo: {...ED_DEF.contenido.cuerpo, ...(s.cuerpo||{})},
    }
  }
  document.getElementById('ed-title').textContent = `Diseño — ${escapeHtml(c.name)}`
  openModal('modal-editor')

  // Esperar a que el modal sea visible y el canvas tenga dimensiones reales
  setTimeout(() => {
    const canvas = document.getElementById('ed-canvas')
    console.log('[Editor] canvas offsetWidth:', canvas?.offsetWidth, 'offsetHeight:', canvas?.offsetHeight)
    // Asegurar que el canvas es el containing block de los bloques
    if (canvas) {
      if (canvas.offsetHeight < 200) canvas.style.height = '420px'
      canvas.style.overflow  = 'hidden'
      canvas.style.position  = 'relative'
      // transform crea un nuevo containing block, rompiendo la herencia del modal fixed
      canvas.style.transform = 'translateZ(0)'
      // Mover los bloques al canvas si no son hijos directos
      ;['ed-block-titulo','ed-block-objetivo','ed-block-logo'].forEach(id => {
        const block = document.getElementById(id)
        if (block && block.parentElement !== canvas) {
          canvas.appendChild(block)
        }
      })
    }
    edSwitchPage('portada')
  }, 200)
}

// ── Switch pestaña ───────────────────────────────
function edSwitchPage(page) {
  ED.page = page
  document.querySelectorAll('.ed-page-tab').forEach(t =>
    t.classList.toggle('ed-tab--active', t.dataset.page === page))
  document.getElementById('ed-panel-portada').style.display  = page==='portada'   ? '' : 'none'
  document.getElementById('ed-panel-contenido').style.display = page==='contenido' ? '' : 'none'

  if (page === 'portada') {
    edLoadCanvas()
    edSetBlock('titulo')
  } else {
    edRenderContent()
    edSetSection('banner')
  }
}

/* ══════════════════ PORTADA ════════════════════ */

function edLoadCanvas() {
  const bg = document.getElementById('ed-bg')
  if (ED.company.portada_path) {
    bg.src = `${BASE_URL}/companies/image-preview?path=${encodeURIComponent(ED.company.portada_path)}`
    bg.style.display = 'block'
  } else {
    bg.src = ''
    bg.style.display = 'none'
  }
  edRenderAllBlocks()
}

function edRenderAllBlocks() {
  if (!edCfg.portada) return
  ;['titulo','objetivo','logo_cliente'].forEach(k => edPosBlock(k))
  edStyleBlock('titulo')
  edStyleBlock('objetivo')
}

function edPosBlock(key) {
  const id = key==='logo_cliente' ? 'ed-block-logo' : `ed-block-${key}`
  const el = document.getElementById(id)
  if (!el) return
  if (!edCfg.portada || !edCfg.portada[key]) return
  const cfg    = edCfg.portada[key]
  const canvas = document.getElementById('ed-canvas')
  if (!canvas) return
  const cr = canvas.getBoundingClientRect()
  const xPx = Math.round(cfg.x / A4W * cr.width)
  const yPx = Math.round(cfg.y / A4H * cr.height)
  // Usar fixed + offset del canvas para posicionar dentro del canvas
  // independiente del modal fixed
  el.style.position = 'fixed'
  el.style.left = Math.round(cr.left + xPx) + 'px'
  el.style.top  = Math.round(cr.top  + yPx) + 'px'
  el.style.zIndex = '9999'
}

function edStyleBlock(key) {
  if (key==='logo_cliente') return
  const el = document.getElementById(`ed-block-${key}`)
  if (!el) return
  const content = el.querySelector('.ed-btext')
  if (!content) return
  const cfg    = edCfg.portada[key]
  const canvas = document.getElementById('ed-canvas')
  const pxMm   = canvas.offsetWidth / A4W

  const fs = (cfg.size * pxMm * 0.3528)
  content.style.fontSize   = fs.toFixed(1) + 'px'
  content.style.fontWeight = cfg.weight
  content.style.textAlign  = cfg.align
  content.style.maxWidth   = Math.round(pxMm * 130) + 'px'
  content.style.lineHeight = '1.1'

  const col = cfg.color || ED.company.primary_color || '#ffffff'
  content.style.color = col
  content.style.textShadow = _lum(col) > 0.45
    ? '0 1px 5px rgba(0,0,0,0.9), 0 0 10px rgba(0,0,0,0.6)'
    : '0 1px 2px rgba(0,0,0,0.3)'
}

function _lum(hex) {
  try {
    const h=hex.replace('#','')
    const r=parseInt(h.slice(0,2),16)/255, g=parseInt(h.slice(2,4),16)/255, b=parseInt(h.slice(4,6),16)/255
    const l=c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4
    return .2126*l(r)+.7152*l(g)+.0722*l(b)
  } catch{return .5}
}

function edSetBlock(key) {
  ED.block = key
  // Tabs sidebar
  document.querySelectorAll('.ed-block-tab').forEach(t =>
    t.classList.toggle('ed-tab--active', t.dataset.block===key))
  // Highlight canvas
  ;['titulo','objetivo','logo'].forEach(k =>
    document.getElementById(`ed-block-${k}`)?.classList.remove('ed-block--active'))
  const id = key==='logo_cliente' ? 'ed-block-logo' : `ed-block-${key}`
  document.getElementById(id)?.classList.add('ed-block--active')
  // Mostrar/ocultar controles de tipografía
  const noLogo = key!=='logo_cliente'
  document.getElementById('ed-typo-panel').style.display  = noLogo ? '' : 'none'
  document.getElementById('ed-color-panel').style.display = noLogo ? '' : 'none'
  edSyncControls()
}

function edSyncControls() {
  const cfg = edCfg.portada[ED.block]
  if (!cfg) return
  _sv('ed-x', cfg.x)
  _sv('ed-y', cfg.y)
  if (ED.block!=='logo_cliente') {
    _sv('ed-size', cfg.size)
    const w=document.getElementById('ed-weight'); if(w) w.value=cfg.weight
    document.querySelectorAll('.ed-align-btn').forEach(b=>
      b.classList.toggle('ed-tab--active', b.dataset.align===(cfg.align||'left')))
    _sc('ed-block-color', cfg.color||ED.company.primary_color||'#ffffff')
  }
}

/* ══════════════════ CONTENIDO ══════════════════ */

function edRenderContent() {
  const wrap = document.getElementById('ed-content-preview')
  if (!wrap) return
  const b = edCfg.contenido.banner
  const c = edCfg.contenido.cuerpo
  const bbg  = b.bg_color    || ED.company.secondary_color || '#8EE3C8'
  const btxt = b.text_color  || ED.company.content_color   || '#1A2B5F'
  const ctxt = c.color       || ED.company.content_color   || '#1A2B5F'
  const bY   = (b.y_start||45)
  const cY   = (c.y_start||75)
  const src  = ED.company.interior_path
    ? `${BASE_URL}/companies/image-preview?path=${encodeURIComponent(ED.company.interior_path)}` : ''

  wrap.innerHTML = `
  <div style="position:relative;min-height:300px;border-radius:6px;overflow:hidden;border:1px solid var(--cp-border)">
    ${src
      ? `<img src="${src}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0.35;pointer-events:none">`
      : '<div style="position:absolute;inset:0;background:#e0e0e0"></div>'}
    <div style="position:absolute;left:0;right:0;top:${bY}%;background:${bbg};padding:8px 14px;font-family:\'Segoe UI\',Arial,sans-serif;font-size:${Math.max(10,b.size*.55)}px;font-weight:${b.weight};color:${btxt}">
      Título de sección
    </div>
    <div style="position:absolute;left:8%;right:4%;top:${cY}%">
      <p style="font-family:\'Segoe UI\',Arial,sans-serif;font-size:${Math.max(8,c.size*1.1)}px;font-weight:600;color:${ctxt};margin:0 0 5px">Subtítulo del servicio</p>
      <p style="font-family:\'Segoe UI\',Arial,sans-serif;font-size:${Math.max(7,c.size)}px;font-weight:${c.weight};color:${ctxt};line-height:1.4;opacity:.9;margin:0">Así se verá el cuerpo de texto en las páginas interiores del PDF.</p>
    </div>
  </div>`
}

function edSetSection(sec) {
  ED.section = sec
  document.querySelectorAll('.ed-content-tab').forEach(t=>
    t.classList.toggle('ed-tab--active', t.dataset.section===sec))
  document.getElementById('ed-sec-banner').style.display = sec==='banner' ? '' : 'none'
  document.getElementById('ed-sec-cuerpo').style.display = sec==='cuerpo' ? '' : 'none'
  if (sec==='banner') {
    const b=edCfg.contenido.banner
    _sv('ed-b-y', b.y_start||45)
    _sv('ed-b-size', b.size)
    const w=document.getElementById('ed-b-weight'); if(w) w.value=b.weight
    _sc('ed-b-bg',   b.bg_color   ||ED.company.secondary_color||'#8EE3C8')
    _sc('ed-b-text', b.text_color ||ED.company.content_color  ||'#1A2B5F')
  } else {
    const c=edCfg.contenido.cuerpo
    _sv('ed-c-y', c.y_start||75)
    _sv('ed-c-size', c.size)
    const w=document.getElementById('ed-c-weight'); if(w) w.value=c.weight
    _sc('ed-c-color', c.color||ED.company.content_color||'#1A2B5F')
  }
}

/* ══════════════════ DRAG ═══════════════════════ */

function edInitDrag() {
  ;['titulo','objetivo','logo'].forEach(shortKey => {
    const key = shortKey==='logo' ? 'logo_cliente' : shortKey
    const el  = document.getElementById(`ed-block-${shortKey}`)
    if (!el) return
    el.addEventListener('mousedown', e => {
      if (e.button!==0) return
      e.preventDefault()
      edSetBlock(key)
      ED.drag = true
      const canvas = document.getElementById('ed-canvas')
      const cr = canvas.getBoundingClientRect()
      const er = el.getBoundingClientRect()
      ED.dragOff.x = e.clientX - er.left
      ED.dragOff.y = e.clientY - er.top
      const onMove = e => {
        if (!ED.drag) return
        const xMm = Math.max(0, Math.min(Math.round((e.clientX-cr.left-ED.dragOff.x)/cr.width*A4W),  A4W-5))
        const yMm = Math.max(0, Math.min(Math.round((e.clientY-cr.top -ED.dragOff.y)/cr.height*A4H), A4H-5))
        edCfg.portada[key].x = xMm
        edCfg.portada[key].y = yMm
        edPosBlock(key)
        _sv('ed-x', xMm)
        _sv('ed-y', yMm)
      }
      const onUp = () => {
        ED.drag = false
        document.removeEventListener('mousemove', onMove)
        document.removeEventListener('mouseup',   onUp)
      }
      document.addEventListener('mousemove', onMove)
      document.addEventListener('mouseup',   onUp)
    })
    el.addEventListener('click', () => edSetBlock(key))
  })
}

/* ══════════════════ GUARDAR ════════════════════ */

async function edSave() {
  if (!ED.company) return
  const btn = document.getElementById('ed-save-btn')
  btn.disabled=true; btn.innerHTML='<i class="ti ti-loader"></i> Guardando…'
  const payload = {
    portada_config: {
      titulo:       edCfg.portada.titulo,
      objetivo:     edCfg.portada.objetivo,
      logo_cliente: edCfg.portada.logo_cliente,
      banner:       edCfg.contenido.banner,
      cuerpo:       edCfg.contenido.cuerpo,
    }
  }
  if (edCfg.portada.titulo.color)         payload.primary_color   = edCfg.portada.titulo.color
  if (edCfg.contenido.banner.bg_color)    payload.secondary_color = edCfg.contenido.banner.bg_color
  if (edCfg.contenido.banner.text_color)  payload.content_color   = edCfg.contenido.banner.text_color
  else if (edCfg.contenido.cuerpo.color)  payload.content_color   = edCfg.contenido.cuerpo.color
  try {
    await api('PUT', `/companies/${ED.company.id}`, payload)
    showAlert('✅ Diseño guardado', 'success')
    closeModal('modal-editor')
    await loadCompanies()
  } catch(e) {
    showAlert('Error: '+e.message, 'error')
  } finally {
    btn.disabled=false
    btn.innerHTML='<i class="ti ti-device-floppy"></i> Guardar diseño'
  }
}

/* ══════════════════ BIND ═══════════════════════ */

function initLayoutEditor() {
  edInitDrag()

  document.querySelectorAll('.ed-page-tab').forEach(t =>
    t.addEventListener('click', ()=>edSwitchPage(t.dataset.page)))
  document.querySelectorAll('.ed-block-tab').forEach(t =>
    t.addEventListener('click', ()=>edSetBlock(t.dataset.block)))
  document.querySelectorAll('.ed-content-tab').forEach(t =>
    t.addEventListener('click', ()=>edSetSection(t.dataset.section)))

  _br('ed-x',    v=>{edCfg.portada[ED.block].x=v; edPosBlock(ED.block)})
  _br('ed-y',    v=>{edCfg.portada[ED.block].y=v; edPosBlock(ED.block)})
  _br('ed-size', v=>{if(ED.block!=='logo_cliente'){edCfg.portada[ED.block].size=v; edStyleBlock(ED.block)}})

  document.getElementById('ed-weight')?.addEventListener('change', e=>{
    if(ED.block!=='logo_cliente'){edCfg.portada[ED.block].weight=Number(e.target.value); edStyleBlock(ED.block)}
  })
  document.querySelectorAll('.ed-align-btn').forEach(btn=>btn.addEventListener('click',()=>{
    document.querySelectorAll('.ed-align-btn').forEach(b=>b.classList.remove('ed-tab--active'))
    btn.classList.add('ed-tab--active')
    if(ED.block!=='logo_cliente'){edCfg.portada[ED.block].align=btn.dataset.align; edStyleBlock(ED.block)}
  }))
  _bc('ed-block-color', v=>{if(ED.block!=='logo_cliente'){edCfg.portada[ED.block].color=v; edStyleBlock(ED.block)}})

  _br('ed-b-y',    v=>{edCfg.contenido.banner.y_start=v;  edRenderContent()})
  _br('ed-b-size', v=>{edCfg.contenido.banner.size=v;     edRenderContent()})
  document.getElementById('ed-b-weight')?.addEventListener('change',e=>{edCfg.contenido.banner.weight=Number(e.target.value); edRenderContent()})
  _bc('ed-b-bg',   v=>{edCfg.contenido.banner.bg_color=v;   edRenderContent()})
  _bc('ed-b-text', v=>{edCfg.contenido.banner.text_color=v; edRenderContent()})

  _br('ed-c-y',    v=>{edCfg.contenido.cuerpo.y_start=v;  edRenderContent()})
  _br('ed-c-size', v=>{edCfg.contenido.cuerpo.size=v;     edRenderContent()})
  document.getElementById('ed-c-weight')?.addEventListener('change',e=>{edCfg.contenido.cuerpo.weight=Number(e.target.value); edRenderContent()})
  _bc('ed-c-color',v=>{edCfg.contenido.cuerpo.color=v;    edRenderContent()})

  // Presets de color
  document.getElementById('modal-editor')?.addEventListener('click', e=>{
    const btn=e.target.closest('.ed-preset')
    if(!btn) return
    const col=btn.dataset.color, tgt=btn.dataset.target
    if(!col) return
    if(tgt){_sc(tgt,col); document.getElementById(tgt)?.dispatchEvent(new Event('input'))}
    else   {_sc('ed-block-color',col); document.getElementById('ed-block-color')?.dispatchEvent(new Event('input'))}
  })

  document.getElementById('ed-reset-block')?.addEventListener('click',()=>{
    edCfg.portada[ED.block]={...ED_DEF.portada[ED.block]}
    edPosBlock(ED.block); edStyleBlock(ED.block); edSyncControls()
  })
  document.getElementById('ed-save-btn')?.addEventListener('click', edSave)
  window.addEventListener('resize',()=>{if(ED.page==='portada') edRenderAllBlocks()})
}

/* ══════════════════ HELPERS ════════════════════ */
function _sv(id,v){const r=document.getElementById(id),n=document.getElementById(id+'-num');if(r)r.value=v;if(n)n.value=v}
function _br(id,cb){const r=document.getElementById(id),n=document.getElementById(id+'-num');const s=v=>{const x=parseFloat(v);if(r)r.value=x;if(n)n.value=x;cb(x)};r?.addEventListener('input',e=>s(e.target.value));n?.addEventListener('input',e=>s(e.target.value))}
function _sc(id,hex){const p=document.getElementById(id),t=document.getElementById(id+'-hex');if(p)p.value=hex;if(t)t.value=hex}
function _bc(id,cb){const p=document.getElementById(id),t=document.getElementById(id+'-hex');const s=v=>{if(p)p.value=v;if(t)t.value=v;cb(v)};p?.addEventListener('input',e=>s(e.target.value));t?.addEventListener('input',e=>{if(/^#[0-9A-Fa-f]{6}$/.test(e.target.value))s(e.target.value)})}
