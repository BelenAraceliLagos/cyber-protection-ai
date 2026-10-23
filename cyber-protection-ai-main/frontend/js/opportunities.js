'use strict'
import {
  requireAuth, showAlert, openModal, closeModal,
  escapeHtml, escapeAttr
} from './utils.js'

/**
 * opportunities.js — Módulo de Oportunidades de Venta
 */

import { BASE_URL } from './config.js'
function getToken() { return sessionStorage.getItem('cp_token') }

async function apiFetch(path, opts = {}) {
  const token = getToken()
  const res = await fetch(BASE_URL + path, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...opts,
  })
  if (res.status === 401) { window.location.href = '/pages/login.html'; return null }
  if (res.status === 204) return null
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

// ── Estado ─────────────────────────────────────────────────────────────────
const state = {
  pipeline:  {},
  metricas:  {},
  allOpps:   [],
  clientes:  [],
  companies: [],
  companyFilter: null,   // null = todas las empresas
  selOppId:  null,
  editingId: null,
}

const ETAPA_LABEL = {
  prospecto:   'Prospecto',
  propuesta:   'Propuesta',
  negociacion: 'Negociación',
  aprobacion:  'Aprobación',
  ganado:      'Ganado ✓',
  perdido:     'Perdido',
}
const ETAPA_ORDER = ['prospecto','propuesta','negociacion','aprobacion','ganado','perdido']
const TIPO_LABEL  = {
  reunion:           'Reunión',
  entrega_propuesta: 'Entrega propuesta',
  seguimiento:       'Seguimiento',
  negociacion:       'Negociación',
  firma:             'Firma contrato',
  inicio_servicio:   'Inicio servicio',
  otro:              'Otro',
}

// ── Init ───────────────────────────────────────────────────────────────────
export async function initOpportunities() {
  if (!requireAuth()) return
  await loadClientes()
  await loadCompanies()
  await loadPipeline()
  bindTabs()
  bindButtons()
  bindCompanyFilter()
}

async function loadClientes() {
  try {
    state.clientes = await apiFetch('/clients/') || []
    const sel = document.getElementById('f-cliente')
    if (sel) sel.innerHTML = state.clientes
      .map(c => `<option value="${Number(c.id)}">${escapeHtml(c.company_name || '')}</option>`)
      .join('')
  } catch (e) { console.error('loadClientes', e) }
}

async function loadCompanies() {
  try {
    state.companies = await apiFetch('/companies/') || []
    const sel = document.getElementById('f-company')
    if (sel) sel.innerHTML = '<option value="">— Sin asignar —</option>' + state.companies
      .map(c => `<option value="${Number(c.id)}">${escapeHtml(c.name || '')}</option>`)
      .join('')

    const filterBar = document.getElementById('kanban-company-filter')
    if (filterBar) {
      filterBar.innerHTML = `<button type="button" class="kcf-pill kcf-pill--active" data-company="">Todas las empresas</button>` +
        state.companies.map(c => `<button type="button" class="kcf-pill" data-company="${Number(c.id)}">${escapeHtml(c.name || '')}</button>`).join('')
    }
  } catch (e) { console.error('loadCompanies', e) }
}

function bindCompanyFilter() {
  const filterBar = document.getElementById('kanban-company-filter')
  if (!filterBar) return
  filterBar.addEventListener('click', (e) => {
    const btn = e.target.closest('.kcf-pill')
    if (!btn) return
    filterBar.querySelectorAll('.kcf-pill').forEach(p => p.classList.remove('kcf-pill--active'))
    btn.classList.add('kcf-pill--active')
    const val = btn.dataset.company
    state.companyFilter = val ? Number(val) : null
    loadPipeline()
  })
}

async function loadPipeline() {
  try {
    const qs = state.companyFilter ? `?company_id=${state.companyFilter}` : ''
    const data = await apiFetch(`/opportunities/pipeline${qs}`)
    if (!data) return
    state.pipeline = data.pipeline || {}
    state.metricas = data.metricas || {}
    state.allOpps  = ETAPA_ORDER.flatMap(e => state.pipeline[e] || [])
    renderDashboard()
    renderKanban()
    populateGanttSelect()
    const sub = document.getElementById('opp-subtitle')
    if (sub) sub.textContent =
      `${state.metricas.total_activas || 0} deals activos · ${state.metricas.valor_pipeline_uf || 0} UF/mes en pipeline`
  } catch (e) { console.error('loadPipeline', e) }
}

// ── Tabs ───────────────────────────────────────────────────────────────────
function bindTabs() {
  document.querySelectorAll('.opp-tab').forEach(btn => {
    btn.addEventListener('click', () => showTab(btn.dataset.tab))
  })
  showTab('dashboard')
}

function showTab(id) {
  ;['dashboard','kanban','gantt'].forEach(t => {
    const el = document.getElementById('tab-' + t)
    if (!el) return
    if (t === id) {
      el.classList.remove('opp-tab-panel--hidden')
    } else {
      el.classList.add('opp-tab-panel--hidden')
    }
  })
  document.querySelectorAll('.opp-tab').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === id)
  )
}

// ── Botones globales ───────────────────────────────────────────────────────
function bindButtons() {
  document.getElementById('btn-nueva-opp')
    ?.addEventListener('click', openNewOppModal)
  document.getElementById('btn-save-opp')
    ?.addEventListener('click', saveOpportunity)
  document.getElementById('btn-cancel-opp')
    ?.addEventListener('click', () => closeModal('opp-modal'))
  document.getElementById('btn-close-opp-modal')
    ?.addEventListener('click', () => closeModal('opp-modal'))
  document.getElementById('btn-save-ms')
    ?.addEventListener('click', saveMilestone)
  document.getElementById('btn-cancel-ms')
    ?.addEventListener('click', () => closeModal('milestone-modal'))
  document.getElementById('btn-close-ms-modal')
    ?.addEventListener('click', () => closeModal('milestone-modal'))
  document.getElementById('add-milestone-btn')
    ?.addEventListener('click', openMilestoneModal)
  document.getElementById('gantt-opp-select')
    ?.addEventListener('change', renderGanttView)
  document.getElementById('gsub-opp')
    ?.addEventListener('click', () => showGanttSub('opp'))
  document.getElementById('gsub-general')
    ?.addEventListener('click', () => showGanttSub('general'))
  document.getElementById('btn-save-lost')
    ?.addEventListener('click', () => confirmLost(true))
  document.getElementById('btn-skip-lost')
    ?.addEventListener('click', () => confirmLost(false))
  document.getElementById('btn-close-lost-modal')
    ?.addEventListener('click', () => confirmLost(false))

  ;['opp-modal','milestone-modal'].forEach(id => {
    const el = document.getElementById(id)
    if (el) el.addEventListener('click', e => { if (e.target === el) closeModal(id) })
  })
}

// ════════════════════════════════════════════════════════════════════════════
// DASHBOARD
// ════════════════════════════════════════════════════════════════════════════
function renderDashboard() {
  const m = state.metricas
  setText('m-total',   m.total_activas ?? 0)
  setText('m-valor',   (m.valor_pipeline_uf ?? 0) + ' UF')
  setText('m-prob',    (m.probabilidad_promedio ?? 0) + '%')
  setText('m-ganadas', m.total_ganadas ?? 0)
  renderFunnel()
  renderUpcoming()
}

function renderFunnel() {
  const cont = document.getElementById('funnel-container')
  if (!cont) return
  const ETAPAS = [
    { key: 'prospecto',   label: 'Prospecto',     color: '#85B7EB' },
    { key: 'propuesta',   label: 'Propuesta',      color: '#378ADD' },
    { key: 'negociacion', label: 'Negociación',    color: '#185FA5' },
    { key: 'aprobacion',  label: 'Aprobación',     color: '#0C447C' },
    { key: 'ganado',      label: 'Cerrado ganado', color: '#1D9E75' },
  ]
  const counts = ETAPAS.map(e => (state.pipeline[e.key] || []).length)
  const maxC   = Math.max(1, ...counts)

  cont.innerHTML = ETAPAS.map((e, i) => {
    const pct = Math.round((counts[i] / maxC) * 100)
    return `
      <div class="funnel-row">
        <span class="funnel-lbl">${e.label}</span>
        <div class="funnel-bg">
          <div class="funnel-fill" style="background:${e.color};width:${pct}%">${counts[i]}</div>
        </div>
      </div>`
  }).join('')
}

function renderUpcoming() {
  const cont = document.getElementById('upcoming-container')
  if (!cont) return
  const now   = new Date(); now.setHours(0,0,0,0)
  const limit = new Date(now.getTime() + 7 * 86400000)
  const MESES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

  const items = []
  state.allOpps.forEach(opp => {
    ;(opp.hitos || []).forEach(h => {
      if (!h.fecha_inicio || h.completado) return
      const d = new Date(h.fecha_inicio)
      if (d >= now && d <= limit) items.push({ opp, hito: h, fecha: d })
    })
  })
  items.sort((a, b) => a.fecha - b.fecha)

  if (!items.length) {
    cont.innerHTML = '<div class="empty-state empty-state--sm">Sin hitos en los próximos 7 días</div>'
    return
  }
  const COLORS = {
    reunion:           ['#E1F5EE','#0F6E56'],
    entrega_propuesta: ['#FAEEDA','#854F0B'],
    firma:             ['#EAF3DE','#3B6D11'],
    default:           ['#E6F1FB','#185FA5'],
  }
  cont.innerHTML = items.slice(0, 5).map(({ opp, hito, fecha }) => {
    const [bg, fg] = COLORS[hito.tipo] || COLORS.default
    return `
      <div class="upcoming-item">
        <div class="upcoming-date" style="background:${bg};color:${fg}">
          <span class="mes">${MESES[fecha.getMonth()]}</span>
          <span class="dia">${fecha.getDate()}</span>
        </div>
        <div class="txt">
          <p>${escapeHtml(hito.titulo || '')}</p>
          <small>${escapeHtml(opp.titulo || opp.cliente_nombre || '')} · ${escapeHtml(TIPO_LABEL[hito.tipo] || hito.tipo || '')}</small>
        </div>
      </div>`
  }).join('')
}

// ════════════════════════════════════════════════════════════════════════════
// KANBAN
// ════════════════════════════════════════════════════════════════════════════
function renderKanban() {
  const board = document.getElementById('kanban-board')
  if (!board) return
  board.innerHTML = ETAPA_ORDER.map(etapa => {
    const cards     = state.pipeline[etapa] || []
    const cardsHtml = cards.length
      ? cards.map(dealCard).join('')
      : '<div class="empty-state empty-state--compact">Sin deals</div>'
    return `
      <div class="kanban-col" data-etapa="${etapa}">
        <div class="kanban-col-hdr">
          ${ETAPA_LABEL[etapa]}<span class="cnt">${cards.length}</span>
        </div>
        <div class="kanban-col-body" data-etapa="${etapa}">
          ${cardsHtml}
        </div>
        <button class="kanban-add" data-etapa="${etapa}">+ Agregar</button>
      </div>`
  }).join('')

  board.querySelectorAll('.deal-card').forEach(card => {
    card.addEventListener('click', () => selectDeal(Number(card.dataset.id)))
    card.addEventListener('dragstart', (e) => {
      card.classList.add('dragging')
      e.dataTransfer.setData('text/plain', card.dataset.id)
      e.dataTransfer.effectAllowed = 'move'
    })
    card.addEventListener('dragend', () => card.classList.remove('dragging'))
  })
  board.querySelectorAll('.kanban-add').forEach(btn =>
    btn.addEventListener('click', () => openNewOppModalWithEtapa(btn.dataset.etapa))
  )

  // ── Drop zones: cada columna acepta la tarjeta arrastrada ──
  board.querySelectorAll('.kanban-col').forEach(col => {
    col.addEventListener('dragover', (e) => {
      e.preventDefault()
      e.dataTransfer.dropEffect = 'move'
      col.classList.add('drag-over')
    })
    col.addEventListener('dragleave', () => col.classList.remove('drag-over'))
    col.addEventListener('drop', async (e) => {
      e.preventDefault()
      col.classList.remove('drag-over')
      const oppId    = Number(e.dataTransfer.getData('text/plain'))
      const newEtapa = col.dataset.etapa
      if (!oppId || !newEtapa) return
      const opp = state.allOpps.find(o => o.id === oppId)
      if (!opp || opp.etapa === newEtapa) return
       if (newEtapa === 'perdido') {
        openLostModal(oppId)
      } else {
        await moveOpportunityToEtapa(oppId, newEtapa)
      }
    })
  })
}

async function moveOpportunityToEtapa(oppId, newEtapa) {
  try {
    await apiFetch(`/opportunities/${oppId}`, {
      method: 'PATCH',
      body: JSON.stringify({ etapa: newEtapa }),
    })
    await loadPipeline()
  } catch (e) {
    showAlert('No se pudo mover la oportunidad: ' + e.message, 'error')
  }
}
let lostOppId = null

function openLostModal(oppId) {
  lostOppId = oppId
  setVal('lost-motivo', '')
  setVal('lost-detalle', '')
  openModal('lost-modal')
}

async function confirmLost(conDatos) {
  if (!lostOppId) return
  const body = { etapa: 'perdido' }
  if (conDatos) {
    const motivo  = document.getElementById('lost-motivo')?.value || ''
    const detalle = document.getElementById('lost-detalle')?.value.trim() || ''
    if (motivo)  body.motivo_cierre  = motivo
    if (detalle) body.detalle_cierre = detalle
  }
  const id = lostOppId
  lostOppId = null
  closeModal('lost-modal')
  try {
    await apiFetch(`/opportunities/${id}`, { method: 'PATCH', body: JSON.stringify(body) })
    await loadPipeline()
  } catch (e) {
    showAlert('No se pudo mover la oportunidad: ' + e.message, 'error')
  }
}
function dealCard(opp) {
  const oppId = Number(opp.id) || 0
  const prob  = Number(opp.probabilidad) || 0
  let pill = prob >= 70 ? 'p-alta' : prob >= 45 ? 'p-media' : 'p-baja'
  if (opp.etapa === 'ganado')  pill = 'p-verde'
  if (opp.etapa === 'perdido') pill = 'p-rojo'
  const isSel = opp.id === state.selOppId
  const prox  = (opp.hitos || [])
    .filter(h => !h.completado && h.fecha_inicio)
    .sort((a, b) => new Date(a.fecha_inicio) - new Date(b.fecha_inicio))[0]
  const hitoTxt = prox
    ? `<i class="ti ti-calendar opp-icon--xs" aria-hidden="true"></i> ${escapeHtml(TIPO_LABEL[prox.tipo] || prox.tipo || '')} — ${fmtDate(prox.fecha_inicio)}`
    : 'Sin hito agendado'
  let lostTag = ''
  if (opp.etapa === 'perdido') {
    const motivo = opp.motivo_cierre || 'Sin motivo'
    const fecha  = opp.closed_at ? fmtDate(opp.closed_at) : 'sin fecha'
    lostTag = `<div class="dc-meta"><i class="ti ti-circle-x opp-icon--xs" aria-hidden="true"></i> ${escapeHtml(motivo)} · ${escapeHtml(fecha)}</div>`
  }
  const prevTag = (opp.etapa !== 'perdido' && opp.motivo_previo)
    ? `<div class="dc-meta">Antes perdida por: ${escapeHtml(opp.motivo_previo)}</div>`
    : ''
  const companyTag = opp.company_nombre
    ? `<span class="dc-company">${escapeHtml(opp.company_nombre)}</span>`
    : ''
  return `
    <div class="deal-card${isSel ? ' sel' : ''}" data-id="${oppId}" draggable="true">
      <div class="dc-nombre">${escapeHtml(opp.titulo || opp.cliente_nombre || '')}</div>
      ${companyTag}
      <div class="dc-meta">${hitoTxt}</div>
      ${lostTag}${prevTag}
      ${Number(opp.valor_uf) > 0
        ? `<div class="dc-uf"><i class="ti ti-currency-dollar opp-icon--xs" aria-hidden="true"></i> ${escapeHtml(String(opp.valor_uf))} UF/mes</div>`
        : ''}
      <span class="prob-pill ${pill}">${prob}%</span>
    </div>`
}

function selectDeal(id) {
  state.selOppId = id
  renderKanban()
  const opp = state.allOpps.find(o => o.id === id)
  if (opp) renderDealDetail(opp)
}

function renderDealDetail(opp) {
  const oppId = Number(opp.id) || 0
  const panel = document.getElementById('deal-detail-panel')
  if (!panel) return
  panel.classList.add('show')
  const cli       = state.clientes.find(c => c.id === opp.cliente_id)
  const etapaKey  = opp.etapa === 'ganado' ? 'ganado' : opp.etapa === 'perdido' ? 'perdido' : 'activo'
  const pillClass = `p-${opp.etapa === 'ganado' ? 'verde' : opp.etapa === 'perdido' ? 'rojo' : 'media'}`
  const barClass  = `dd-bar__fill--${etapaKey}`

  const valorMensual = Number(opp.valor_uf) || 0
  const plazo         = opp.plazo_meses ? Number(opp.plazo_meses) : null
  const valorTotal     = plazo ? valorMensual * plazo : null
  const probabilidad   = Math.max(0, Math.min(100, Number(opp.probabilidad) || 0))
   let cierreHtml = ''
  if (opp.etapa === 'perdido') {
    const motivo  = opp.motivo_cierre || 'Sin motivo'
    const fecha   = opp.closed_at ? new Date(opp.closed_at).toLocaleDateString('es-CL') : 'Sin fecha'
    const detalle = opp.detalle_cierre
      ? `<p class="deal-note">${escapeHtml(opp.detalle_cierre)}</p>`
      : ''
    cierreHtml = `
      <div class="dd-field"><i class="ti ti-circle-x" aria-hidden="true"></i>
        <div><span class="dd-field__lbl">Motivo de pérdida</span><span class="dd-field__val">${escapeHtml(motivo)}</span></div>
      </div>
      <div class="dd-field"><i class="ti ti-calendar" aria-hidden="true"></i>
        <div><span class="dd-field__lbl">Fecha de cierre</span><span class="dd-field__val">${escapeHtml(fecha)}</span></div>
      </div>
      ${detalle}`
  } else if (opp.motivo_previo) {
    cierreHtml = `<p class="deal-note">Antes perdida por: ${escapeHtml(opp.motivo_previo)}</p>`
  }

  panel.innerHTML = `
    <div class="dd-card">
      <div class="dd-card__header">
        <div>
          <p class="dd-card__title">${escapeHtml(opp.titulo || '')}</p>
          <span class="prob-pill ${pillClass}">${escapeHtml(ETAPA_LABEL[opp.etapa] || opp.etapa || '')}</span>
        </div>
        <div class="dd-card__value">
          <p class="dd-card__value-main">${escapeHtml(String(valorMensual))} UF<span>/mes</span></p>
          <p class="dd-card__value-sub">${plazo ? `${plazo} meses &middot; ${escapeHtml(String(valorTotal))} UF total` : 'Plazo sin especificar'}</p>
        </div>
      </div>

      <div class="dd-card__prob">
        <div class="dd-card__prob-row">
          <span>Probabilidad de cierre</span>
          <span class="dd-card__prob-num">${probabilidad}%</span>
        </div>
        <div class="dd-bar"><div class="dd-bar__fill ${barClass}" style="width:${probabilidad}%"></div></div>
      </div>

      <div class="dd-card__fields">
        <div class="dd-field"><i class="ti ti-building" aria-hidden="true"></i>
          <div><span class="dd-field__lbl">Cliente</span><span class="dd-field__val">${escapeHtml(opp.cliente_nombre || '—')}</span></div>
        </div>
        <div class="dd-field"><i class="ti ti-briefcase" aria-hidden="true"></i>
          <div><span class="dd-field__lbl">Industria</span><span class="dd-field__val">${escapeHtml(cli?.industry || '—')}</span></div>
        </div>
        <div class="dd-field"><i class="ti ti-user" aria-hidden="true"></i>
          <div><span class="dd-field__lbl">Contacto</span><span class="dd-field__val">${escapeHtml(cli?.contact_name || '—')}</span></div>
        </div>
        <div class="dd-field"><i class="ti ti-mail" aria-hidden="true"></i>
          <div><span class="dd-field__lbl">Email</span><span class="dd-field__val dd-field__val--accent">${escapeHtml(cli?.email || '—')}</span></div>
        </div>
      </div>
      ${cierreHtml ? `<div class="dd-card__fields">${cierreHtml}</div>` : ''}
      ${opp.notas ? `<p class="deal-note">${escapeHtml(opp.notas)}</p>` : ''}

      <div class="dd-card__actions">
        <button class="btn btn--secondary btn--sm" id="dp-edit">
          <i class="ti ti-edit btn__icon" aria-hidden="true"></i> Editar
        </button>
        <button class="btn btn--secondary btn--sm" id="dp-gantt">
          <i class="ti ti-timeline btn__icon" aria-hidden="true"></i> Ver Gantt
        </button>
        <button class="btn btn--sm btn--danger-soft dd-card__del" id="dp-del">
          <i class="ti ti-trash btn__icon" aria-hidden="true"></i> Eliminar
        </button>
      </div>
    </div>`

  panel.querySelector('#dp-edit') .addEventListener('click', () => openEditOppModal(oppId))
  panel.querySelector('#dp-gantt').addEventListener('click', () => goToGantt(oppId))
  panel.querySelector('#dp-del')  .addEventListener('click', () => deleteOpp(oppId))
}

// ════════════════════════════════════════════════════════════════════════════
// GANTT
// ════════════════════════════════════════════════════════════════════════════
function populateGanttSelect() {
  const sel = document.getElementById('gantt-opp-select')
  if (!sel) return
  const prev = sel.value
  sel.innerHTML = '<option value="">— Selecciona una oportunidad —</option>' +
    state.allOpps.map(o =>
      `<option value="${Number(o.id)}">${escapeHtml(o.titulo || o.cliente_nombre || '')}</option>`
    ).join('')
  if (prev) { sel.value = prev; renderGanttView() }
}

function renderGanttView() {
  const sel  = document.getElementById('gantt-opp-select')
  const id   = parseInt(sel?.value)
  const btn  = document.getElementById('add-milestone-btn')
  const cont = document.getElementById('gantt-container')
  if (!id) {
    btn?.classList.add('opp-add-milestone--hidden')
    if (cont) cont.innerHTML = '<div class="empty-state">Selecciona una oportunidad para ver su carta Gantt</div>'
    return
  }
  state.selOppId = id
  btn?.classList.remove('opp-add-milestone--hidden')

  const opp   = state.allOpps.find(o => o.id === id)
  if (!opp || !cont) return
  const hitos = opp.hitos || []
  const valorMensual = Number(opp.valor_uf) || 0
  const plazo        = opp.plazo_meses ? Number(opp.plazo_meses) : null
  const valorTotal   = plazo ? valorMensual * plazo : null
  const colorEtapa   = opp.etapa === 'ganado' ? 'p-verde' : opp.etapa === 'perdido' ? 'p-rojo' : 'p-media'

  let cierreTxt = ''
  if (opp.etapa === 'perdido') {
    const f = opp.closed_at ? new Date(opp.closed_at).toLocaleDateString('es-CL') : 'sin fecha'
    cierreTxt = `Perdida el ${escapeHtml(f)} · Motivo: ${escapeHtml(opp.motivo_cierre || 'Sin motivo')}`
    if (opp.detalle_cierre) cierreTxt += ` · ${escapeHtml(opp.detalle_cierre)}`
  } else if (opp.etapa === 'ganado') {
    const f = opp.closed_at ? new Date(opp.closed_at).toLocaleDateString('es-CL') : 'sin fecha'
    cierreTxt = `Ganada el ${escapeHtml(f)}`
  }

  const cabeceraHtml = `
    <details class="dd-card" style="margin-bottom:14px; padding:16px 20px; font-size:1.05rem;">
      <summary style="cursor:pointer; display:flex; flex-wrap:wrap; gap:16px; align-items:center; font-size:1.15rem;">
        <strong style="font-size:1.4rem;">${escapeHtml(opp.titulo || '')}</strong>
        <span class="prob-pill ${colorEtapa}">${escapeHtml(ETAPA_LABEL[opp.etapa] || opp.etapa || '')}</span>
        ${opp.company_nombre ? `<span class="dc-company">${escapeHtml(opp.company_nombre)}</span>` : ''}
        <span>${escapeHtml(String(valorMensual))} UF/mes</span>
        <span>${Number(opp.probabilidad) || 0}%</span>
        ${opp.etapa === 'perdido' ? '<span style="color:#B91C1C;font-weight:600;">Perdida</span>' : ''}
        <small style="margin-left:auto;color:#64748b;">ver detalle ▾</small>
      </summary>
      <div class="dd-card__fields" style="margin-top:10px;">
        <div class="dd-field"><i class="ti ti-building" aria-hidden="true"></i>
          <div><span class="dd-field__lbl">Cliente</span><span class="dd-field__val">${escapeHtml(opp.cliente_nombre || '—')}</span></div>
        </div>
        <div class="dd-field"><i class="ti ti-cash" aria-hidden="true"></i>
          <div><span class="dd-field__lbl">Valor total</span><span class="dd-field__val">${plazo ? `${plazo} meses · ${escapeHtml(String(valorTotal))} UF` : 'Plazo sin especificar'}</span></div>
        </div>
      </div>
      ${cierreTxt ? `<p class="deal-note">${cierreTxt}</p>` : ''}
    </details>`

  if (!hitos.length) {
    cont.innerHTML = cabeceraHtml + '<div class="empty-state empty-state--lg">Sin hitos. Haz clic en <strong>+ Agregar hito</strong> para comenzar.</div>'
    return
  }

  const today = new Date(); today.setHours(0,0,0,0)
  let minD = new Date(today); minD.setDate(today.getDate() - 14)
  let maxD = new Date(today); maxD.setDate(today.getDate() + 60)
  hitos.forEach(h => {
    if (h.fecha_inicio) { const d = new Date(h.fecha_inicio); if (d < minD) minD = d }
    if (h.fecha_fin)    { const d = new Date(h.fecha_fin);    if (d > maxD) maxD = d }
  })
  minD.setDate(minD.getDate() - 7)
  maxD.setDate(maxD.getDate() + 14)

  const weeks = []
  const cur   = new Date(minD)
  while (cur <= maxD) { weeks.push(new Date(cur)); cur.setDate(cur.getDate() + 7) }

  const MES       = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
  const rangeDays = (maxD - minD) / 86400000
  const pct       = d => ((new Date(d) - minD) / 86400000) / rangeDays * 100
  const todayPct  = pct(today)

  const weekHdrs = weeks.map(w => {
    const isHoy = w <= today && today < new Date(w.getTime() + 7*86400000)
    return `<th class="${isHoy ? 'hoy-col' : ''}">${w.getDate()} ${MES[w.getMonth()]}</th>`
  }).join('')

  const rows = hitos.map(h => {
    let barClass = 'bar-planned'
    if (h.completado) barClass = h.tipo === 'inicio_servicio' ? 'bar-success' : 'bar-done'
    else if (h.fecha_inicio && new Date(h.fecha_inicio) < today) barClass = 'bar-pending'

    let barStyle = ''
    if (h.fecha_inicio) {
      const sp = Math.max(0, pct(h.fecha_inicio))
      const ep = h.fecha_fin ? Math.min(100, pct(h.fecha_fin)) : sp + (100/weeks.length)
      barStyle = `left:${sp}%;width:${Math.max(ep-sp, 3.5)}%`
    }
    const statusTxt = h.completado ? 'Completado'
      : (h.fecha_inicio && new Date(h.fecha_inicio) < today ? 'Pendiente' : 'Proyectado')

    return `
      <tr>
        <td class="hito-lbl">
          <div class="hl-name">${escapeHtml(h.titulo || '')}</div>
          <div class="hl-sub">${escapeHtml(TIPO_LABEL[h.tipo] || h.tipo || '')} · ${statusTxt}</div>
          <div class="hl-sub">${h.fecha_inicio ? escapeHtml(fmtDate(h.fecha_inicio)) : 'Sin fecha'}${h.fecha_fin ? ' → ' + escapeHtml(fmtDate(h.fecha_fin)) : ''}</div>
        </td>
        <td class="gantt-cell gantt-cell--timeline" colspan="${weeks.length}" style="min-width:${weeks.length*44}px">
          <div class="gantt-today-line" style="left:${todayPct}%"></div>
          ${h.fecha_inicio
            ? `<div class="gantt-bar ${barClass}" style="${barStyle}">${escapeHtml((h.titulo||'').substring(0,18))}</div>`
            : ''}
        </td>
      </tr>`
  }).join('')

  cont.innerHTML = cabeceraHtml + `
    <div class="gantt-wrap">
      <table class="gantt-tbl">
        <thead><tr><th class="gantt-heading--label">Hito</th>${weekHdrs}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`
}

function goToGantt(id) {
  showTab('gantt')
  const sel = document.getElementById('gantt-opp-select')
  if (sel) { sel.value = id; renderGanttView() }
}

// ════════════════════════════════════════════════════════════════════════════
// MODALES
// ════════════════════════════════════════════════════════════════════════════
function openNewOppModal() {
  state.editingId = null
  setText('opp-modal-title', 'Nueva oportunidad')
  setVal('f-titulo', ''); setVal('f-notas', '')
  setVal('f-company', state.companyFilter || '')
  setVal('f-etapa', 'prospecto'); setVal('f-prob', 30); setVal('f-valor', 0); setVal('f-plazo', '')
  openModal('opp-modal')
}

function openNewOppModalWithEtapa(etapa) {
  openNewOppModal()
  setVal('f-etapa', etapa)
}

function openEditOppModal(id) {
  const opp = state.allOpps.find(o => o.id === id)
  if (!opp) return
  state.editingId = id
  setText('opp-modal-title', 'Editar oportunidad')
  setVal('f-titulo',  opp.titulo       || '')
  setVal('f-cliente', opp.cliente_id   || '')
  setVal('f-company', opp.company_id   || '')
  setVal('f-etapa',   opp.etapa        || 'prospecto')
  setVal('f-prob',    opp.probabilidad ?? 30)
  setVal('f-valor',   opp.valor_uf     || 0)
  setVal('f-plazo',   opp.plazo_meses  || '')
  setVal('f-notas',   opp.notas        || '')
  openModal('opp-modal')
}

async function saveOpportunity() {
  const titulo = document.getElementById('f-titulo')?.value.trim()
  const cliId  = parseInt(document.getElementById('f-cliente')?.value)
  if (!titulo) return showAlert('El título es obligatorio.', 'error')
  if (!cliId)  return showAlert('Selecciona un cliente.', 'error')
  const probRaw = parseInt(document.getElementById('f-prob')?.value)
  const probabilidad = Number.isNaN(probRaw) ? 30 : Math.min(100, Math.max(0, probRaw))

  const body = {
    cliente_id:   cliId,
    company_id:   document.getElementById('f-company')?.value ? Number(document.getElementById('f-company').value) : null,
    titulo,
    etapa:        document.getElementById('f-etapa')?.value  || 'prospecto',
    probabilidad,
    valor_uf:     parseFloat(document.getElementById('f-valor')?.value) || 0,
    plazo_meses:  document.getElementById('f-plazo')?.value ? Number(document.getElementById('f-plazo').value) : null,
    notas:        document.getElementById('f-notas')?.value.trim() || '',
  }
  try {
    if (state.editingId) {
      await apiFetch(`/opportunities/${state.editingId}`, { method: 'PATCH', body: JSON.stringify(body) })
    } else {
      await apiFetch('/opportunities/', { method: 'POST', body: JSON.stringify(body) })
    }
    closeModal('opp-modal')
    showAlert('Oportunidad guardada correctamente.')
    await loadPipeline()
  } catch (e) { showAlert('Error: ' + e.message, 'error') }
}

function openMilestoneModal() {
  setVal('ms-titulo', ''); setVal('ms-desc', '')
  setVal('ms-inicio', ''); setVal('ms-fin',  '')
  setVal('ms-tipo', 'reunion'); setVal('ms-estado', 'false')
  setVal('ms-importancia', 'Normal')
  openModal('milestone-modal')
}

async function saveMilestone() {
  const id = state.selOppId
  if (!id) return showAlert('Selecciona una oportunidad primero.', 'error')
  const titulo = document.getElementById('ms-titulo')?.value.trim()
  if (!titulo) return showAlert('El título del hito es obligatorio.', 'error')
  const fi   = document.getElementById('ms-inicio')?.value
  const ff   = document.getElementById('ms-fin')?.value
  const body = {
    tipo:         document.getElementById('ms-tipo')?.value    || 'reunion',
    titulo,
    descripcion:  document.getElementById('ms-desc')?.value.trim() || '',
    completado:   document.getElementById('ms-estado')?.value === 'true',
    importancia:  document.getElementById('ms-importancia')?.value || 'Normal',
    fecha_inicio: fi ? new Date(fi).toISOString() : null,
    fecha_fin:    ff ? new Date(ff).toISOString() : null,
  }
  try {
    await apiFetch(`/opportunities/${id}/milestones`, { method: 'POST', body: JSON.stringify(body) })
    closeModal('milestone-modal')
    showAlert('Hito agregado.')
    await loadPipeline()
    renderGanttView()
  } catch (e) { showAlert('Error: ' + e.message, 'error') }
}

async function generatePDF(id) {
  if (!confirm('¿Generar propuesta PDF con IA para esta oportunidad?')) return
  showAlert('Generando PDF... esto puede tardar unos segundos.', 'info')
  try {
    const res = await fetch(`${BASE_URL}/opportunities/${id}/generate-pdf`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
      body:    JSON.stringify({ usar_ia: true, antecedente: '' }),
    })
    if (!res.ok) throw new Error(await res.text())
    const blob = await res.blob()
    const url  = URL.createObjectURL(blob)
    const a    = Object.assign(document.createElement('a'), { href: url, download: `propuesta_${id}.pdf` })
    document.body.appendChild(a); a.click(); a.remove()
    URL.revokeObjectURL(url)
    showAlert('PDF descargado correctamente.')
    await loadPipeline()
  } catch (e) { showAlert('Error generando PDF: ' + e.message, 'error') }
}

async function deleteOpp(id) {
  if (!confirm('¿Eliminar esta oportunidad? Esta acción no se puede deshacer.')) return
  try {
    await apiFetch(`/opportunities/${id}`, { method: 'DELETE' })
    state.selOppId = null
    document.getElementById('deal-detail-panel')?.classList.remove('show')
    showAlert('Oportunidad eliminada.')
    await loadPipeline()
  } catch (e) { showAlert('Error: ' + e.message, 'error') }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val }
function setVal(id, val)  { const el = document.getElementById(id); if (el) el.value = val }
function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-CL', { day: '2-digit', month: 'short' })
}
function renderGanttGeneral() {
  const opps = state.allOpps
  const activas  = opps.filter(o => o.etapa !== 'ganado' && o.etapa !== 'perdido')
  const ganadas  = opps.filter(o => o.etapa === 'ganado')
  const perdidas = opps.filter(o => o.etapa === 'perdido')
  const suma = lista => Math.round(lista.reduce((s, o) => s + (Number(o.valor_uf) || 0), 0) * 10) / 10

  const hoy = new Date(); hoy.setHours(0, 0, 0, 0)
  const limite = new Date(hoy.getTime() + 7 * 86400000)
  let hitosPend = 0, hitosProx = 0
  opps.forEach(o => (o.hitos || []).forEach(h => {
    if (h.completado) return
    hitosPend++
    if (h.fecha_inicio) {
      const d = new Date(h.fecha_inicio)
      if (d >= hoy && d <= limite) hitosProx++
    }
  }))

  const caja = (valor, etiqueta) =>
    `<div class="metric-box"><div class="metric-box__val">${valor}</div><div class="metric-box__lbl">${etiqueta}</div></div>`

  const cont = document.getElementById('gg-metricas')
  if (cont) cont.innerHTML =
    caja(opps.length, 'Oportunidades') +
    caja(activas.length, 'Activas') +
    caja(ganadas.length, 'Ganadas') +
    caja(perdidas.length, 'Perdidas') +
    caja(suma(activas) + ' UF', 'En juego (UF/mes)') +
    caja(suma(ganadas) + ' UF', 'Ganado (UF/mes)') +
    caja(suma(perdidas) + ' UF', 'Perdido (UF/mes)') +
    caja(hitosPend, 'Hitos pendientes') +
    caja(hitosProx, 'Hitos próx. 7 días')
}

function showGanttSub(cual) {
  const general = cual === 'general'
  const g = document.getElementById('gantt-general')
  const o = document.getElementById('gantt-por-opp')
  if (g) g.style.display = general ? '' : 'none'
  if (o) o.style.display = general ? 'none' : ''
  const bo = document.getElementById('gsub-opp')
  const bg = document.getElementById('gsub-general')
  if (bo) bo.className = 'btn btn--sm ' + (general ? 'btn--secondary' : 'btn--primary')
  if (bg) bg.className = 'btn btn--sm ' + (general ? 'btn--primary' : 'btn--secondary')
  if (general) { renderGanttGeneral(); renderGanttTimeline() }
}
function renderGanttTimeline() {
  const cont = document.getElementById('gg-timeline')
  if (!cont) return

  const filtroEstado = document.getElementById('gg-filtro-estado')?.value || ''
  const filtroEmpresa = document.getElementById('gg-filtro-empresa')?.value || ''

  const estadoDe = o => o.etapa === 'ganado' ? 'ganado' : o.etapa === 'perdido' ? 'perdido' : 'activo'
  const lista = state.allOpps.filter(o =>
    (!filtroEstado || estadoDe(o) === filtroEstado) &&
    (!filtroEmpresa || String(o.company_id || '') === filtroEmpresa)
  )

  const empresasOpts = '<option value="">Todas las empresas</option>' +
    state.companies.map(c => `<option value="${Number(c.id)}" ${String(c.id) === filtroEmpresa ? 'selected' : ''}>${escapeHtml(c.name || '')}</option>`).join('')
  const filtrosHtml = `
    <div style="display:flex; gap:10px; margin-bottom:14px; flex-wrap:wrap;">
      <select id="gg-filtro-estado">
        <option value="" ${!filtroEstado ? 'selected' : ''}>Todos los estados</option>
        <option value="activo" ${filtroEstado === 'activo' ? 'selected' : ''}>Activas</option>
        <option value="ganado" ${filtroEstado === 'ganado' ? 'selected' : ''}>Ganadas</option>
        <option value="perdido" ${filtroEstado === 'perdido' ? 'selected' : ''}>Perdidas</option>
      </select>
      <select id="gg-filtro-empresa">${empresasOpts}</select>
    </div>`

  if (!lista.length) {
    cont.innerHTML = filtrosHtml + '<div class="empty-state">No hay oportunidades con ese filtro</div>'
    bindGanttFiltros()
    return
  }

  const hoy = new Date(); hoy.setHours(0, 0, 0, 0)
  const DIA = 86400000
  const inicioDe = o => o.created_at ? new Date(o.created_at) : hoy
  const finDe = o => o.closed_at ? new Date(o.closed_at) : hoy

  let minD = new Date(Math.min(...lista.map(o => inicioDe(o).getTime()), hoy.getTime()))
  let maxD = new Date(Math.max(...lista.map(o => finDe(o).getTime()), hoy.getTime()))
  lista.forEach(o => (o.hitos || []).forEach(h => {
    if (h.fecha_inicio) {
      const d = new Date(h.fecha_inicio)
      if (d < minD) minD = d
      if (d > maxD) maxD = d
    }
  }))
  minD = new Date(minD.getTime() - 5 * DIA)
  maxD = new Date(maxD.getTime() + 10 * DIA)
  const rango = (maxD - minD) / DIA
  const pct = d => Math.max(0, Math.min(100, ((new Date(d) - minD) / DIA) / rango * 100))

  const COLOR = { activo: '#378ADD', ganado: '#1D9E75', perdido: '#DC2626' }
  const MES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

  const marcasMes = []
  const m = new Date(minD.getFullYear(), minD.getMonth() + 1, 1)
  while (m <= maxD) {
    marcasMes.push(`<div style="position:absolute; left:${pct(m)}%; top:0; bottom:0; border-left:1px dashed #CBD5E1; padding-left:4px; font-size:0.8rem; color:#64748B;">${MES[m.getMonth()]} ${m.getFullYear()}</div>`)
    m.setMonth(m.getMonth() + 1)
  }
   const marcasSemana = []
  const s = new Date(minD)
  s.setDate(s.getDate() + ((8 - s.getDay()) % 7))
  while (s <= maxD) {
    marcasSemana.push(`<div style="position:absolute; left:${pct(s)}%; top:12px; bottom:0; border-left:1px dotted #E2E8F0; padding-left:3px; font-size:0.7rem; color:#94A3B8;">${s.getDate()}</div>`)
    s.setDate(s.getDate() + 7)
  }
  const filas = lista.map(o => {
    const est = estadoDe(o)
    const ini = pct(inicioDe(o))
    const fin = Math.max(pct(finDe(o)), ini + 1.5)
    const dias = Math.max(0, Math.round((finDe(o) - inicioDe(o)) / DIA))
    const detalle = est === 'perdido'
      ? `Perdida: ${o.motivo_cierre || 'Sin motivo'}${o.detalle_cierre ? ' — ' + o.detalle_cierre : ''}`
      : est === 'ganado' ? 'Ganada' : 'En curso'
    const tip = `${o.titulo || ''} · ${dias} días · ${detalle}`
    const fmtLarga = iso => iso ? new Date(iso).toLocaleDateString('es-CL', { day: '2-digit', month: 'short' }) : '—'
    const fechasTxt = est === 'activo'
      ? `Creada ${fmtLarga(o.created_at)} → en curso`
      : `Creada ${fmtLarga(o.created_at)} → cerrada ${fmtLarga(o.closed_at)}`
    const ETIQ = { activo: 'Activa', ganado: 'Ganada', perdido: 'Perdida' }
    const valorTxt = `${Number(o.valor_uf) || 0} UF/mes`
    const motivoTxt = est === 'perdido' ? (o.motivo_cierre || 'Sin motivo') : ''

    const bandera = est !== 'activo' && o.closed_at
      ? `<div title="${escapeAttr(detalle)}" style="position:absolute; left:${pct(o.closed_at)}%; top:2px; font-size:1.3rem; color:${COLOR[est]}; transform:translateX(-4px); white-space:nowrap;">⚑ <span style="font-size:0.8rem; font-weight:600;">${escapeHtml(o.motivo_cierre || (est === 'ganado' ? 'Ganada' : 'Sin motivo'))}</span></div>`
      : ''

    const puntos = (o.hitos || []).filter(h => h.fecha_inicio).map((h, i) => {
      const arriba = i % 2 === 1
      const posY = arriba ? 'bottom:calc(50% + 10px)' : 'top:calc(50% + 10px)'
      return `<div title="${escapeAttr((h.titulo || '') + ' · ' + (TIPO_LABEL[h.tipo] || h.tipo || '') + ' · ' + fmtDate(h.fecha_inicio))}" style="position:absolute; left:${pct(h.fecha_inicio)}%; top:50%; width:14px; height:14px; margin:-7px 0 0 -7px; border-radius:50%; background:#fff; border:3px solid #0F172A;"></div>
       <div style="position:absolute; left:${pct(h.fecha_inicio)}%; ${posY}; transform:translateX(-50%); font-size:0.72rem; color:#334155; white-space:nowrap;">${escapeHtml((h.titulo || '').slice(0, 26))} · ${escapeHtml(fmtDate(h.fecha_inicio))}</div>`
    }).join('')

    return `
      <div class="gg-fila" data-opp="${Number(o.id)}" style="display:flex; align-items:center; border-bottom:1px solid #E2E8F0; cursor:pointer;" title="${escapeAttr(tip)}">
        <div style="width:220px; padding:12px; flex-shrink:0;">
          <div style="font-weight:600;">${escapeHtml(o.titulo || '')}</div>
          <div style="font-size:0.8rem; color:#64748B;">${escapeHtml(o.cliente_nombre || '')} · ${dias} días</div>
          <div style="font-size:0.78rem; color:#475569;">${escapeHtml(fechasTxt)}</div>
        </div>
        <div style="position:relative; flex:1; height:56px;">
          <div style="position:absolute; left:${ini}%; width:${fin - ini}%; top:18px; height:20px; border-radius:10px; background:${COLOR[est]}; opacity:0.85;"></div>
          ${bandera}${puntos}
        </div>
      <div style="width:150px; padding:8px 12px; flex-shrink:0; text-align:right; font-size:0.85rem;">
          <div style="font-weight:600; color:${COLOR[est]};">${ETIQ[est]}</div>
          <div>${escapeHtml(valorTxt)}</div>
          <div style="color:#64748B;">${dias} días</div>
        </div>
      </div>`
  }).join('')

  cont.innerHTML = filtrosHtml + `
    <div style="display:flex;">
      <div style="width:220px; flex-shrink:0;"></div>
      <div style="position:relative; flex:1; height:34px;">${marcasMes.join('')}${marcasSemana.join('')}</div>
    </div>
    <div style="position:relative;">
      ${filas}
      <div style="position:absolute; left:calc(220px + (100% - 220px) * ${pct(hoy) / 100}); top:0; bottom:0; border-left:2px solid #DC2626; pointer-events:none;" title="Hoy"></div>
    </div>
    <div style="display:flex; gap:18px; margin-top:12px; font-size:0.85rem;">
      <span><span style="color:#378ADD;">■</span> Activa</span>
      <span><span style="color:#1D9E75;">■</span> Ganada</span>
      <span><span style="color:#DC2626;">■</span> Perdida</span>
      <span>⚑ Cierre</span>
      <span>● Hito</span>
      <span style="color:#DC2626;">| Hoy</span>
    </div>`

  bindGanttFiltros()
  cont.querySelectorAll('.gg-fila').forEach(fila => {
    fila.addEventListener('click', () => {
      showGanttSub('opp')
      goToGantt(Number(fila.dataset.opp))
    })
  })
}

function bindGanttFiltros() {
  document.getElementById('gg-filtro-estado')?.addEventListener('change', renderGanttTimeline)
  document.getElementById('gg-filtro-empresa')?.addEventListener('change', renderGanttTimeline)
}