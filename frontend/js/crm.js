import { requireAuth, showAlert, escapeHtml } from './utils.js'
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

let chartTiempo = null
let chartFuente = null

export async function initCrm() {
  if (!requireAuth()) return
  await loadDashboard()
}

async function loadDashboard() {
  try {
    const data = await apiFetch('/crm/dashboard')
    if (!data) return

    renderMetricas(data.metricas || {})
    renderChartTiempo(data.oportunidades_por_mes || [])
    renderChartFuente(data.oportunidades_por_fuente || [])
    renderContactos(data.contactos_recientes || [])
  } catch (e) {
    console.error('loadDashboard CRM', e)
    showAlert('No se pudo cargar el panel CRM: ' + e.message, 'error')
  }
}

function setText(id, val) {
  const el = document.getElementById(id)
  if (el) el.textContent = val
}

function renderMetricas(m) {
  setText('crm-m-total', m.total_contactos ?? 0)
  setText('crm-m-leads', m.leads ?? 0)
  setText('crm-m-opp', m.oportunidades_stage ?? 0)
  setText('crm-m-clientes', m.clientes ?? 0)
  setText('crm-m-promotores', m.promotores ?? 0)

  const sub = document.getElementById('crm-subtitle')
  if (sub) {
    sub.textContent =
      `${m.oportunidades_activas ?? 0} oportunidades activas · ` +
      `${m.valor_pipeline_uf ?? 0} UF/mes en pipeline`
  }
}

const MES_LABEL = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

function fmtMes(clave) {
  // clave viene como "AAAA-MM"
  const [anio, mes] = (clave || '').split('-')
  const idx = parseInt(mes, 10) - 1
  return MES_LABEL[idx] ? `${MES_LABEL[idx]} ${anio}` : clave
}

function renderChartTiempo(rows) {
  const canvas = document.getElementById('crm-chart-tiempo')
  if (!canvas || typeof Chart === 'undefined') return
  const labels = rows.map(r => fmtMes(r.mes))
  const valores = rows.map(r => r.cantidad)

  if (chartTiempo) chartTiempo.destroy()
  chartTiempo = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Oportunidades creadas',
        data: valores,
        borderColor: '#155FCF',
        backgroundColor: 'rgba(21,95,207,0.12)',
        fill: true,
        tension: 0.3,
        pointRadius: 3,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
    }
  })
}

const FUENTE_COLORS = ['#155FCF', '#22C9C6', '#F5A623', '#8B5CF6', '#EF4444', '#10B981', '#94A3B8']

function renderChartFuente(rows) {
  const canvas = document.getElementById('crm-chart-fuente')
  if (!canvas || typeof Chart === 'undefined') return
  const labels = rows.map(r => r.origen)
  const valores = rows.map(r => r.cantidad)
  const colors = labels.map((_, i) => FUENTE_COLORS[i % FUENTE_COLORS.length])

  if (chartFuente) chartFuente.destroy()

  if (!rows.length) {
    canvas.parentElement.innerHTML = '<div class="empty-state">Sin datos de origen todavía</div>'
    return
  }

  chartFuente = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Oportunidades',
        data: valores,
        backgroundColor: colors,
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
    }
  })
}

function fmtFecha(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('es-CL', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const ETAPA_PILL = {
  lead: 'crm-pill--lead',
  oportunidad: 'crm-pill--opp',
  cliente: 'crm-pill--cliente',
  promotor: 'crm-pill--promotor',
}

function renderContactos(rows) {
  const tbody = document.getElementById('crm-contactos-tbody')
  if (!tbody) return

  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Sin contactos todavía</td></tr>'
    return
  }

  tbody.innerHTML = rows.map(c => `
    <tr>
      <td>${escapeHtml(c.company_name || '')}</td>
      <td>${escapeHtml(c.contact_name || '')}</td>
      <td><span class="crm-pill ${ETAPA_PILL[c.lifecycle_stage] || 'crm-pill--lead'}">${escapeHtml(c.lifecycle_label || 'Lead')}</span></td>
      <td>${escapeHtml(c.origen || '—')}</td>
      <td>${escapeHtml(c.country || '—')}</td>
      <td>${fmtFecha(c.created_at)}</td>
    </tr>
  `).join('')
}
