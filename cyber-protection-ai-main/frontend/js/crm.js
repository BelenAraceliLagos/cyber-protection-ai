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

// Instancias globales de gráficos para permitir la destrucción y re-renderizado
let chartTiempo = null
let chartFuente = null
let chartServiciosMes = null
let chartServiciosTotal = null
let chartContratadosMes = null
let chartContratadosTotal = null

let refreshInterval = null
const REFRESH_MS = 45000  // Refresco automático cada 45s

export async function initCrm() {
  if (!requireAuth()) return
  await cargarTodo()
  bindPeriodSelector()
  bindAutoRefresh()
  bindBotonActualizar()
}

async function cargarTodo() {
  await loadDashboard()
  await loadAnalytics()
  marcarUltimaActualizacion()
}

function marcarUltimaActualizacion() {
  const el = document.getElementById('crm-last-update')
  if (el) el.textContent = `Actualizado ${new Date().toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`
}

function bindBotonActualizar() {
  const btn = document.getElementById('crm-refresh-btn')
  if (!btn) return
  btn.addEventListener('click', async () => {
    btn.classList.add('crm-refresh-btn--spinning')
    await cargarTodo()
    btn.classList.remove('crm-refresh-btn--spinning')
  })
}

function bindAutoRefresh() {
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      cargarTodo()
      _iniciarIntervalo()
    } else {
      _detenerIntervalo()
    }
  })
  if (document.visibilityState === 'visible') _iniciarIntervalo()
}

function _iniciarIntervalo() {
  _detenerIntervalo()
  refreshInterval = setInterval(cargarTodo, REFRESH_MS)
}

function _detenerIntervalo() {
  if (refreshInterval) clearInterval(refreshInterval)
  refreshInterval = null
}

async function loadDashboard() {
  try {
    const data = await apiFetch('/crm/dashboard')
    if (!data) return

    renderMetricas(data.metricas || {})
    renderChartTiempo(data.oportunidades_por_mes || [])
    renderChartFuente(data.oportunidades_por_fuente || [])

    // 1. Cotizados
    renderChartServiciosMes('crm-chart-servicios-mes', data.servicios_mas_cotizados_por_mes || {})
    renderChartServiciosTotal('crm-chart-servicios-total', data.servicios_mas_cotizados_total || [])

    // 2. Contratados
    window.crmContratadosMensual = data.servicios_mas_contratados_por_mes || {}
    window.crmContratadosTrimestral = data.servicios_mas_contratados_trimestral || {}
    window.crmContratadosCuatrimestral = data.servicios_mas_contratados_cuatrimestral || {}

    renderContratadosPeriodo('mensual')
    renderChartContratadosTotal('crm-chart-contratados-total', data.servicios_mas_contratados_total || [])

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

const MES_LABEL = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

function fmtMes(clave) {
  const [anio, mes] = (clave || '').split('-')
  const idx = parseInt(mes, 10) - 1
  return MES_LABEL[idx] ? `${MES_LABEL[idx]} ${anio}` : clave
}

function fmtPeriodo(clave) {
  if (!clave) return ''
  if (clave.includes('-Q')) {
    const [anio, q] = clave.split('-Q')
    return `T${q} ${anio}`
  }
  if (clave.includes('-C')) {
    const [anio, c] = clave.split('-C')
    return `C${c} ${anio}`
  }
  return fmtMes(clave)
}

const FUENTE_COLORS = ['#155FCF', '#22C9C6', '#F5A623', '#8B5CF6', '#EF4444', '#10B981', '#94A3B8']
const SERVICIO_COLORS = [
  '#155FCF', '#22C9C6', '#F5A623', '#8B5CF6',
  '#EF4444', '#10B981', '#EC4899', '#6366F1',
  '#14B8A6', '#F97316'
]

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

function renderChartFuente(rows) {
  const canvas = document.getElementById('crm-chart-fuente')
  if (!canvas || typeof Chart === 'undefined') return
  const labels = rows.map(r => r.origen)
  const valores = rows.map(r => r.cantidad)
  const colors = labels.map((_, i) => FUENTE_COLORS[i % FUENTE_COLORS.length])

  if (chartFuente) chartFuente.destroy()

  if (!rows.length) {
    if (canvas.parentElement) {
      canvas.parentElement.innerHTML = '<div class="empty-state">Sin datos de origen todavía</div>'
    }
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

// ── 1. COTIZADOS POR MES ────────────────────────────────────────────────
function renderChartServiciosMes(canvasId, data) {
  const canvas = document.getElementById(canvasId)
  if (!canvas || typeof Chart === 'undefined') return
  if (!data || !data.meses || !data.datasets || !data.datasets.length) {
    if (canvas.parentElement) {
      canvas.parentElement.innerHTML = '<div class="empty-state">Sin datos de servicios cotizados por mes</div>'
    }
    return
  }

  const labels = data.meses.map(fmtMes)
  const datasets = data.datasets.map((ds, idx) => ({
    label: ds.label,
    data: ds.data,
    backgroundColor: SERVICIO_COLORS[idx % SERVICIO_COLORS.length],
    borderRadius: 4,
    stack: 'servicios',
  }))

  if (chartServiciosMes) chartServiciosMes.destroy()
  chartServiciosMes = new Chart(canvas, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } },
        tooltip: {
          callbacks: {
            label: (context) => `${context.dataset.label}: ${context.raw} unidad(es)`
          }
        }
      },
      scales: {
        x: { stacked: true },
        y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } }
      }
    }
  })
}

// ── 2. COTIZADOS TOTAL ──────────────────────────────────────────────────
function renderChartServiciosTotal(canvasId, rows) {
  const canvas = document.getElementById(canvasId)
  if (!canvas || typeof Chart === 'undefined') return
  if (!rows || !Array.isArray(rows) || !rows.length) {
    if (canvas.parentElement) {
      canvas.parentElement.innerHTML = '<div class="empty-state">Sin servicios cotizados aún</div>'
    }
    return
  }

  const labels = rows.map(r => r.servicio)
  const cantidades = rows.map(r => r.cantidad_total)
  const colors = labels.map((_, i) => SERVICIO_COLORS[i % SERVICIO_COLORS.length])

  if (chartServiciosTotal) chartServiciosTotal.destroy()
  chartServiciosTotal = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Cantidad cotizada',
        data: cantidades,
        backgroundColor: colors,
        borderRadius: 5
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => {
              const row = rows[context.dataIndex]
              return `Cotizado ${row.cantidad_total} unidad(es) (${row.cotizaciones_count} cotizaciones) — ${row.monto_total_uf} UF`
            }
          }
        }
      },
      scales: {
        x: { beginAtZero: true, ticks: { precision: 0 } }
      }
    }
  })
}

// ── 3. CONTRATADOS POR MES ──────────────────────────────────────────────
function renderChartContratadosMes(canvasId, data) {
  const canvas = document.getElementById(canvasId)
  if (!canvas || typeof Chart === 'undefined') return
  const periodos = data.meses || data.periodos || []
  if (!data || !periodos.length || !data.datasets || !data.datasets.length) {
    if (canvas.parentElement) {
      canvas.parentElement.innerHTML = '<div class="empty-state">Sin datos de servicios contratados para este periodo</div>'
    }
    return
  }

  const labels = periodos.map(fmtPeriodo)
  const datasets = data.datasets.map((ds, idx) => ({
    label: ds.label,
    data: ds.data,
    backgroundColor: SERVICIO_COLORS[idx % SERVICIO_COLORS.length],
    borderRadius: 4,
    stack: 'servicios',
  }))

  if (chartContratadosMes) chartContratadosMes.destroy()
  chartContratadosMes = new Chart(canvas, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } },
        tooltip: {
          callbacks: {
            label: (context) => `${context.dataset.label}: ${context.raw} unidad(es) contratada(s)`
          }
        }
      },
      scales: {
        x: { stacked: true },
        y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } }
      }
    }
  })
}

// ── 4. CONTRATADOS TOTAL ────────────────────────────────────────────────
function renderChartContratadosTotal(canvasId, rows) {
  const canvas = document.getElementById(canvasId)
  if (!canvas || typeof Chart === 'undefined') return
  if (!rows || !Array.isArray(rows) || !rows.length) {
    if (canvas.parentElement) {
      canvas.parentElement.innerHTML = '<div class="empty-state">Sin servicios contratados aún</div>'
    }
    return
  }

  const labels = rows.map(r => r.servicio)
  const cantidades = rows.map(r => r.cantidad_total)
  const colors = labels.map((_, i) => SERVICIO_COLORS[i % SERVICIO_COLORS.length])

  if (chartContratadosTotal) chartContratadosTotal.destroy()
  chartContratadosTotal = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Cantidad contratada',
        data: cantidades,
        backgroundColor: colors,
        borderRadius: 5
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => {
              const row = rows[context.dataIndex]
              return `Contratado ${row.cantidad_total} unidad(es) (${row.cotizaciones_count} ventas) — ${row.monto_total_uf} UF`
            }
          }
        }
      },
      scales: {
        x: { beginAtZero: true, ticks: { precision: 0 } }
      }
    }
  })
}

// ── CONTACTOS RECIENTES ────────────────────────────────────────────────
function renderContactos(list) {
  const tbody = document.getElementById('crm-contactos-tbody')
  if (!tbody) return
  if (!list.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Sin contactos recientes</td></tr>'
    return
  }

  tbody.innerHTML = list.map(c => `
    <tr>
      <td><strong>${escapeHtml(c.company_name || 'Sin empresa')}</strong></td>
      <td>${escapeHtml(c.contact_name || '')}</td>
      <td><span class="crm-badge crm-badge--${escapeHtml(c.lifecycle_stage)}">${escapeHtml(c.lifecycle_label)}</span></td>
      <td>${escapeHtml(c.industry || '-')}</td>
      <td>${c.created_at ? new Date(c.created_at).toLocaleDateString('es-CL') : '-'}</td>
    </tr>
  `).join('')
}

// ── Analítica avanzada: embudo, tasa de victoria, forecast, empresas, alertas ──
async function loadAnalytics() {
  try {
    const data = await apiFetch('/crm/analytics')
    if (!data) return
    renderEmbudo(data.embudo || [])
    renderWinrate(data.tasa_victoria || {})
    renderForecast(data.forecast_ponderado_uf || 0)
    renderPorEmpresa(data.por_empresa || [])
    renderEstancadas(data.estancadas || [], data.dias_umbral_estancamiento || 14)
    renderValorGanado(data.valor_ganado || {})
    renderConversionEtapas(data.conversion_entre_etapas || [])
    renderLtv(data.ltv || {})
    renderIngresosVertical(data.ingresos_por_vertical || [])
    renderCicloVentaVertical(data.ciclo_venta_por_vertical || [], data.ciclo_venta_promedio_general_dias || 0)
    
    // Render leads no convertidos y KPIs adicionales
    renderLeadsNoConvertidos(data.leads_no_convertidos || [])
    setText('crm-m-conversion-rate', (data.tasa_conversion_leads_clientes ?? 0) + '%')
    setText('crm-m-perdidas', (data.ventas_perdidas_uf ?? 0) + ' UF')
    setText('crm-m-proyeccion', (data.proyeccion_trimestral_uf ?? 0) + ' UF')

    if (data.servicios_mas_cotizados_por_mes) renderChartServiciosMes(data.servicios_mas_cotizados_por_mes)
    if (data.servicios_mas_cotizados_total) renderChartServiciosTotal(data.servicios_mas_cotizados_total)
  } catch (e) {
    console.error('loadAnalytics CRM', e)
  }
}

function renderConversionEtapas(rows) {
  const cont = document.getElementById('crm-conversion-etapas')
  if (!cont) return
  if (!rows.length) { cont.innerHTML = '<div class="empty-state empty-state--compact">Sin datos todavía</div>'; return }
  cont.innerHTML = rows.map(r => `
    <div class="crm-conv-row">
      <span class="crm-conv-row__lbl">${escapeHtml(r.de_etapa)} → ${escapeHtml(r.a_etapa)}</span>
      <span class="crm-conv-row__pct ${r.pct >= 50 ? 'crm-conv-row__pct--good' : 'crm-conv-row__pct--bad'}">${r.pct}%</span>
    </div>
  `).join('')
}

function renderLtv(ltv) {
  setText('crm-ltv-promedio', `${ltv.promedio_uf ?? 0} UF`)
  setText('crm-ltv-sub', `sobre ${ltv.clientes_con_ventas ?? 0} cliente(s) con al menos una venta ganada`)

  const cont = document.getElementById('crm-ltv-lista')
  if (!cont) return
  const rows = ltv.por_cliente || []
  if (!rows.length) { cont.innerHTML = '<div class="empty-state">Sin ventas ganadas todavía</div>'; return }
  const max = Math.max(...rows.map(r => r.valor_uf), 1)
  cont.innerHTML = rows.map(r => `
    <div class="crm-valor-row">
      <span class="crm-valor-row__lbl">${escapeHtml(r.cliente_nombre || '—')}</span>
      <div class="crm-valor-row__bar-wrap">
        <div class="crm-valor-row__bar" style="width:${Math.max(6, r.valor_uf / max * 100)}%"></div>
      </div>
      <span class="crm-valor-row__val">${r.valor_uf} UF</span>
    </div>
  `).join('')
}

function renderIngresosVertical(rows) {
  const cont = document.getElementById('crm-vertical-ingresos')
  if (!cont) return
  if (!rows.length) { cont.innerHTML = '<div class="empty-state empty-state--compact">Sin datos todavía</div>'; return }
  const max = Math.max(...rows.map(r => r.valor_uf), 1)
  cont.innerHTML = rows.map(r => `
    <div class="crm-valor-row">
      <span class="crm-valor-row__lbl">${escapeHtml(r.industria || 'Sin especificar')}</span>
      <div class="crm-valor-row__bar-wrap">
        <div class="crm-valor-row__bar" style="width:${Math.max(6, r.valor_uf / max * 100)}%"></div>
      </div>
      <span class="crm-valor-row__val">${r.valor_uf} UF</span>
    </div>
  `).join('')
}

function renderCicloVentaVertical(rows, promedioGeneral) {
  setText('crm-ciclo-venta', promedioGeneral ? `${promedioGeneral} días` : '—')
  const tbody = document.getElementById('crm-vertical-ciclo-tbody')
  if (!tbody) return
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="3" class="empty-state">Sin oportunidades cerradas todavía</td></tr>'
    return
  }
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${escapeHtml(r.industria || 'Sin especificar')}</td>
      <td>${r.dias_promedio} días</td>
      <td>${r.cantidad_deals}</td>
    </tr>
  `).join('')
}

function renderValorGanado(v) {
  setText('crm-valor-total', `${v.total_uf ?? 0} UF`)
  renderValorLista('crm-valor-empresa', v.por_empresa || [], r => r.company_nombre || 'Sin asignar')
  renderValorLista('crm-valor-cliente', v.por_cliente || [], r => r.cliente_nombre || '—')
  renderValorLista('crm-valor-plazo', v.por_plazo || [], r => r.plazo_label || 'Sin especificar')
}

function renderValorLista(contId, rows, getLabel) {
  const cont = document.getElementById(contId)
  if (!cont) return
  if (!rows.length) { cont.innerHTML = '<div class="empty-state empty-state--compact">Sin datos todavía</div>'; return }
  const max = Math.max(...rows.map(r => r.valor_uf), 1)
  cont.innerHTML = rows.map(r => `
    <div class="crm-valor-row">
      <span class="crm-valor-row__lbl">${escapeHtml(getLabel(r))}</span>
      <div class="crm-valor-row__bar-wrap">
        <div class="crm-valor-row__bar" style="width:${Math.max(6, r.valor_uf / max * 100)}%"></div>
      </div>
      <span class="crm-valor-row__val">${r.valor_uf} UF</span>
    </div>
  `).join('')
}

function renderEmbudo(rows) {
  const cont = document.getElementById('crm-embudo')
  if (!cont) return
  if (!rows.length) { cont.innerHTML = '<div class="empty-state">Sin datos todavía</div>'; return }

  const max = Math.max(...rows.map(r => r.cantidad), 1)
  cont.innerHTML = rows.map(r => `
    <div class="crm-funnel-row">
      <span class="crm-funnel-row__lbl">${escapeHtml(r.etapa_label)}</span>
      <div class="crm-funnel-row__bar-wrap">
        <div class="crm-funnel-row__bar" style="width:${Math.max(6, r.cantidad / max * 100)}%"></div>
      </div>
      <span class="crm-funnel-row__val">${r.cantidad} <small>(${r.pct}%)</small></span>
    </div>
  `).join('')
}

function renderWinrate(w) {
  setText('crm-winrate', `${w.tasa_pct ?? 0}%`)
  setText('crm-winrate-sub', `${w.ganadas ?? 0} ganadas · ${w.perdidas ?? 0} perdidas`)
}

function renderForecast(valor) {
  setText('crm-forecast', `${valor} UF/mes`)
}

function renderPorEmpresa(rows) {
  const tbody = document.getElementById('crm-empresa-tbody')
  if (!tbody) return
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Sin datos todavía</td></tr>'
    return
  }
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${escapeHtml(r.company_nombre || 'Sin asignar')}</td>
      <td>${r.total}</td>
      <td>${r.ganadas}</td>
      <td>${r.tasa_victoria_pct}%</td>
      <td>${r.valor_ganado_uf}</td>
    </tr>
  `).join('')
}

function renderEstancadas(rows, umbral) {
  const tbody = document.getElementById('crm-estancadas-tbody')
  const badge = document.getElementById('crm-alertas-count')
  if (badge) badge.textContent = rows.length
  if (!tbody) return

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">Ninguna oportunidad lleva ${umbral}+ días sin movimiento 🎉</td></tr>`
    return
  }
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${escapeHtml(r.titulo || '')}</td>
      <td>${escapeHtml(r.cliente_nombre || '')}</td>
      <td><span class="crm-pill crm-pill--opp">${escapeHtml(r.etapa_label || '')}</span></td>
      <td class="crm-dias-estancada">${r.dias_sin_movimiento} días</td>
      <td>${r.valor_uf ?? 0}</td>
    </tr>
  `).join('')
}

function bindPeriodSelector() {
  const container = document.querySelector('.crm-period-selector')
  if (!container) return
  if (container.dataset.bound) return
  container.dataset.bound = 'true'
  container.addEventListener('click', (e) => {
    const btn = e.target.closest('button')
    if (!btn) return
    container.querySelectorAll('button').forEach(b => b.classList.remove('active'))
    btn.classList.add('active')
    const period = btn.dataset.period
    renderContratadosPeriodo(period)
  })
}

function renderContratadosPeriodo(period) {
  let dataset = {}
  if (period === 'mensual') {
    dataset = window.crmContratadosMensual || {}
  } else if (period === 'trimestral') {
    dataset = window.crmContratadosTrimestral || {}
  } else if (period === 'cuatrimestral') {
    dataset = window.crmContratadosCuatrimestral || {}
  }
  renderChartContratadosMes('crm-chart-contratados-mes', dataset)
}

function renderLeadsNoConvertidos(list) {
  const countBadge = document.getElementById('crm-leads-no-convertidos-count')
  if (countBadge) countBadge.textContent = list.length
  
  const tbody = document.getElementById('crm-leads-no-convertidos-tbody')
  if (!tbody) return
  
  if (!list.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Ningún lead recurrente sin conversión</td></tr>'
    return
  }
  
  tbody.innerHTML = list.map(c => `
    <tr>
      <td><strong>${escapeHtml(c.company_name || 'Sin empresa')}</strong></td>
      <td>${escapeHtml(c.contact_name || '')}</td>
      <td>${escapeHtml(c.email || '')}</td>
      <td><span class="crm-badge crm-badge--opp" style="background: #FEE2E2; color: #B91C1C; font-weight: 700; border-radius: 999px; padding: 2px 8px;">${c.num_quotations} cotizaciones</span></td>
      <td style="font-weight: 600;">${c.total_quoted_uf} UF</td>
      <td>${c.last_quotation_date ? new Date(c.last_quotation_date).toLocaleDateString('es-CL') : '-'}</td>
      <td>
        <div style="display: flex; gap: 4px; flex-wrap: wrap;">
          ${(c.services_quoted || []).map(s => `<span class="crm-pill crm-pill--lead" style="font-size: 0.7rem; padding: 1px 6px;">${escapeHtml(s)}</span>`).join('')}
        </div>
      </td>
    </tr>
  `).join('')
}
