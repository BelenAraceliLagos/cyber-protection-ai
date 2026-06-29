'use strict'

import {
  requireAuth, showAlert, openModal, closeModal,
  escapeHtml
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
  await loadPipeline()
  bindTabs()
  bindButtons()
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

async function loadPipeline() {
  try {
    const data = await apiFetch('/opportunities/pipeline')
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
      <div class="kanban-col">
        <div class="kanban-col-hdr">
          ${ETAPA_LABEL[etapa]}<span class="cnt">${cards.length}</span>
        </div>
        ${cardsHtml}
        <button class="kanban-add" data-etapa="${etapa}">+ Agregar</button>
      </div>`
  }).join('')

  board.querySelectorAll('.deal-card').forEach(card =>
    card.addEventListener('click', () => selectDeal(Number(card.dataset.id)))
  )
  board.querySelectorAll('.kanban-add').forEach(btn =>
    btn.addEventListener('click', () => openNewOppModalWithEtapa(btn.dataset.etapa))
  )
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
  return `
    <div class="deal-card${isSel ? ' sel' : ''}" data-id="${oppId}">
      <div class="dc-nombre">${escapeHtml(opp.titulo || opp.cliente_nombre || '')}</div>
      <div class="dc-meta">${hitoTxt}</div>
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
  const pillClass = `p-${opp.etapa === 'ganado' ? 'verde' : opp.etapa === 'perdido' ? 'rojo' : 'media'}`
  panel.innerHTML = `
    <h3>
      ${escapeHtml(opp.titulo || '')}
      <span class="prob-pill prob-pill--spaced ${pillClass}">${escapeHtml(ETAPA_LABEL[opp.etapa] || opp.etapa || '')}</span>
    </h3>
    <div class="detail-grid">
      <div><div class="di-lbl">Cliente</div><div class="di-val">${escapeHtml(opp.cliente_nombre || '—')}</div></div>
      <div><div class="di-lbl">Valor</div><div class="di-val">${escapeHtml(String(opp.valor_uf || 0))} UF/mes</div></div>
      <div><div class="di-lbl">Probabilidad</div><div class="di-val">${escapeHtml(String(opp.probabilidad || 0))}%</div></div>
      <div><div class="di-lbl">Contacto</div><div class="di-val">${escapeHtml(cli?.contact_name || '—')}</div></div>
      <div><div class="di-lbl">Email</div><div class="di-val">${escapeHtml(cli?.email || '—')}</div></div>
      <div><div class="di-lbl">Industria</div><div class="di-val">${escapeHtml(cli?.industry || '—')}</div></div>
    </div>
    ${opp.notas ? `<p class="deal-note">${escapeHtml(opp.notas)}</p>` : ''}
    <div class="deal-actions">
      <button class="btn btn--secondary btn--sm" id="dp-edit">
        <i class="ti ti-edit btn__icon" aria-hidden="true"></i> Editar
      </button>

      <button class="btn btn--secondary btn--sm" id="dp-gantt">
        <i class="ti ti-timeline btn__icon" aria-hidden="true"></i> Ver Gantt
      </button>
      <button class="btn btn--sm btn--danger-soft" id="dp-del">
        <i class="ti ti-trash btn__icon" aria-hidden="true"></i> Eliminar
      </button>
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

  if (!hitos.length) {
    cont.innerHTML = '<div class="empty-state empty-state--lg">Sin hitos. Haz clic en <strong>+ Agregar hito</strong> para comenzar.</div>'
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
        </td>
        <td class="gantt-cell gantt-cell--timeline" colspan="${weeks.length}" style="min-width:${weeks.length*44}px">
          <div class="gantt-today-line" style="left:${todayPct}%"></div>
          ${h.fecha_inicio
            ? `<div class="gantt-bar ${barClass}" style="${barStyle}">${escapeHtml((h.titulo||'').substring(0,18))}</div>`
            : ''}
        </td>
      </tr>`
  }).join('')

  cont.innerHTML = `
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
  setVal('f-etapa', 'prospecto'); setVal('f-prob', 30); setVal('f-valor', 0)
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
  setVal('f-etapa',   opp.etapa        || 'prospecto')
  setVal('f-prob',    opp.probabilidad || 30)
  setVal('f-valor',   opp.valor_uf     || 0)
  setVal('f-notas',   opp.notas        || '')
  openModal('opp-modal')
}

async function saveOpportunity() {
  const titulo = document.getElementById('f-titulo')?.value.trim()
  const cliId  = parseInt(document.getElementById('f-cliente')?.value)
  if (!titulo) return showAlert('El título es obligatorio.', 'error')
  if (!cliId)  return showAlert('Selecciona un cliente.', 'error')

  const body = {
    cliente_id:   cliId,
    titulo,
    etapa:        document.getElementById('f-etapa')?.value  || 'prospecto',
    probabilidad: parseInt(document.getElementById('f-prob')?.value)   || 30,
    valor_uf:     parseFloat(document.getElementById('f-valor')?.value) || 0,
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
