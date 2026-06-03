'use strict'

import { clientsAPI, servicesAPI, proposalsAPI } from './api.js'
import { showAlert, showSpinner, hideSpinner, requireAuth } from './utils.js'

// ── Categorías ────────────────────────────────────────────────────────
const CATEGORIAS_ORDEN = [
  '🛡  Detección y Respuesta',
  '🔑  Gestión de Identidades y Accesos',
  '☁  Protección de Infraestructura',
  '⚖  Cumplimiento y Gobernanza',
  '🎓  Capacitación y Desarrollo Seguro',
]
const KEYWORDS = {
  '🛡  Detección y Respuesta': ['incident','response','soc','monitoreo','vulnerability','pentest','penetration','forensi','threat','detección','deteccion','respuesta','brecha','intrusion','siem','edr','xdr','alerta','hunting','phishing','ransomware','tabletop','simulacro'],
  '🔑  Gestión de Identidades y Accesos': ['iam','identidad','identity','acceso','access','mfa','autenticacion','autenticación','privileged','pam','zero trust','parche','patch','contraseña','password','directorio','ldap','sso'],
  '☁  Protección de Infraestructura': ['cloud','nube','aws','azure','gcp','firewall','red','network','endpoint','backup','recuperacion','recuperación','drp','infraestructura','servidor','server','segmentacion','segmentación','vpn','email','correo','devsecops','ssdlc'],
  '⚖  Cumplimiento y Gobernanza': ['cumplimiento','compliance','iso','normativa','ley','gdpr','gobernanza','governance','audit','auditoria','auditoría','legal','regulatorio','certificacion','certificación','política','politica','riesgo','risk','dpia','privacidad','vciso','sgsi','bcp','continuidad','dpo','gap'],
  '🎓  Capacitación y Desarrollo Seguro': ['capacitacion','capacitación','training','awareness','simulacion','simulación','desarrollo','development','sast','dast','reporte','dashboard','kpi','concientizacion','concientización','taller','conocimiento'],
}

function categorizar(nombre, desc) {
  const txt = ((nombre||'')+(desc||'')).toLowerCase()
  let best = CATEGORIAS_ORDEN[0], score = 0
  for (const [cat, kws] of Object.entries(KEYWORDS)) {
    const s = kws.reduce((a, k) => a + (txt.includes(k) ? 1 : 0), 0)
    if (s > score) { score = s; best = cat }
  }
  return best
}

function agrupar(servicios) {
  const g = {}
  for (const c of CATEGORIAS_ORDEN) g[c] = []
  for (const s of servicios) {
    const c = categorizar(s.name, s.description)
    g[c].push(s)
  }
  return g
}

// ── Estado ────────────────────────────────────────────────────────────
let clientes      = []
let servicios     = []
let seleccionados = new Set()
let clienteSel    = null

// ── Init ──────────────────────────────────────────────────────────────
export async function initQuotes() {
  if (!requireAuth()) return
  await Promise.all([cargarClientes(), cargarServicios()])
  bindCliente()
  bindBotones()
  bindModal()
}

async function cargarClientes() {
  try {
    clientes = await clientsAPI.getAll()
    const sel = document.getElementById('q-cliente')
    if (!sel) return
    sel.innerHTML = '<option value="">— Selecciona un cliente —</option>' +
      clientes.map(c => `<option value="${c.id}">${c.company_name} · ${c.contact_name}</option>`).join('')
    sel.addEventListener('change', () => {
      const id = parseInt(sel.value)
      clienteSel = clientes.find(c => c.id === id) || null
      actualizarInfo()
      actualizarBotones()
    })
  } catch (e) { showAlert('Error cargando clientes', 'error') }
}

function bindCliente() {
  const input = document.getElementById('q-cliente-search')
  const sel   = document.getElementById('q-cliente')
  if (!input || !sel) return
  input.addEventListener('input', () => {
    const q = input.value.toLowerCase()
    Array.from(sel.options).forEach(o => {
      o.hidden = !!o.value && !o.text.toLowerCase().includes(q)
    })
  })
}

async function cargarServicios() {
  try {
    servicios = await servicesAPI.getAll()
    renderCatalogo()
  } catch (e) { showAlert('Error cargando servicios', 'error') }
}

function renderCatalogo() {
  const cont = document.getElementById('q-catalogo')
  if (!cont) return
  const grupos = agrupar(servicios)
  cont.innerHTML = ''

  for (const [cat, srvs] of Object.entries(grupos)) {
    if (!srvs.length) continue
    const bloque = document.createElement('div')
    bloque.className = 'q-categoria'
    bloque.innerHTML = `
      <div class="q-categoria__header" onclick="toggleCategoria(this)">
        <span class="q-categoria__nombre">${cat}</span>
        <span class="q-categoria__count badge badge--info">${srvs.length}</span>
        <button class="q-categoria__sel-all btn btn--xs btn--secondary"
          onclick="event.stopPropagation();seleccionarCategoria('${cat.replace(/'/g,"\\'")}')">
          Seleccionar todos
        </button>
        <i class="ti ti-chevron-down q-categoria__chevron"></i>
      </div>
      <div class="q-categoria__body">
        ${srvs.map(s => `
          <label class="q-servicio" data-cat="${cat.replace(/"/g,'&quot;')}">
            <input type="checkbox" class="q-servicio__check"
              value="${s.id}" onchange="onCheckServicio(${s.id}, this.checked)">
            <div class="q-servicio__info">
              <div class="q-servicio__nombre">${s.name}</div>
              ${s.description ? `<div class="q-servicio__desc">${s.description.split('|')[0].trim()}</div>` : ''}
            </div>
            <div class="q-servicio__precio">
              ${s.base_price > 0 ? s.base_price.toFixed(1)+' UF' : 'A convenir'}
            </div>
          </label>`).join('')}
      </div>`
    cont.appendChild(bloque)
  }
}

window.toggleCategoria = function(header) {
  const body = header.nextElementSibling
  const icon = header.querySelector('.q-categoria__chevron')
  body.classList.toggle('q-categoria__body--open')
  icon.classList.toggle('ti-chevron-up')
  icon.classList.toggle('ti-chevron-down')
}
window.seleccionarCategoria = function(cat) {
  const checks = document.querySelectorAll(`.q-servicio[data-cat="${cat}"] .q-servicio__check`)
  const all = Array.from(checks).every(c => c.checked)
  checks.forEach(c => { c.checked = !all; onCheckServicio(parseInt(c.value), !all) })
}
window.onCheckServicio = function(id, on) {
  if (on) seleccionados.add(id); else seleccionados.delete(id)
  actualizarContador()
  actualizarBotones()
}

function actualizarContador() {
  const el = document.getElementById('q-contador')
  if (el) el.textContent = seleccionados.size > 0
    ? `${seleccionados.size} servicio${seleccionados.size > 1 ? 's' : ''} seleccionado${seleccionados.size > 1 ? 's' : ''}`
    : 'Ningún servicio seleccionado'
}

function actualizarInfo() {
  const el = document.getElementById('q-cliente-info')
  if (!el) return
  if (clienteSel) {
    el.style.display = 'block'
    el.innerHTML = `
      <div style="font-size:11px;color:var(--cp-text-muted);margin-bottom:2px">Cliente seleccionado</div>
      <div style="font-weight:600;color:var(--cp-blue-main)">${clienteSel.company_name}</div>
      <div style="font-size:12px;color:var(--cp-text-muted)">${clienteSel.contact_name}</div>
      ${clienteSel.industry ? `<div style="font-size:11px;color:var(--cp-text-muted)">Industria: ${clienteSel.industry}</div>` : ''}`
  } else {
    el.style.display = 'none'
  }
}

function actualizarBotones() {
  const ok       = clienteSel && seleccionados.size > 0
  const btnSimple = document.getElementById('q-generar-simple')
  const btnIA     = document.getElementById('q-generar-ia')
  if (btnSimple) btnSimple.disabled = !ok
  if (btnIA)     btnIA.disabled     = !ok
}

// ── Descarga PDF ──────────────────────────────────────────────────────
async function generarPDF(usarIA, titulo, antecedente = '') {
  if (!clienteSel || !seleccionados.size) return

  const nombreArchivo = usarIA
    ? `Informe_Preventa_${clienteSel.company_name.replace(/\s+/g,'_')}.pdf`
    : `Propuesta_${clienteSel.company_name.replace(/\s+/g,'_')}.pdf`

  const resp = await proposalsAPI.generate({
    cliente_id:      clienteSel.id,
    service_ids:     Array.from(seleccionados),
    titulo_proyecto: titulo,
    antecedente:     antecedente,
    usar_ia:         usarIA,
  })

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err.detail || `Error ${resp.status}`)
  }

  const blob = await resp.blob()
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = nombreArchivo
  a.click()
  URL.revokeObjectURL(url)
}

// ── Botones ───────────────────────────────────────────────────────────
function bindBotones() {
  // Botón simple — genera sin preguntar
  const btnSimple = document.getElementById('q-generar-simple')
  btnSimple?.addEventListener('click', async () => {
    const titulo = document.getElementById('q-titulo')?.value.trim()
      || `Propuesta ${clienteSel.company_name}`
    showSpinner(btnSimple, 'Generando...')
    try {
      await generarPDF(false, titulo)
      showAlert(`✅ Propuesta generada para ${clienteSel.company_name}`, 'success', 5000)
    } catch (e) {
      showAlert('Error: ' + e.message, 'error')
    } finally {
      hideSpinner(btnSimple)
    }
  })

  // Botón IA — abre modal de confirmación
  const btnIA = document.getElementById('q-generar-ia')
  btnIA?.addEventListener('click', () => {
    if (!clienteSel || !seleccionados.size) return
    // Pre-rellenar modal
    const tituloInput = document.getElementById('q-titulo')?.value.trim()
    const modalTitulo = document.getElementById('modal-titulo')
    if (modalTitulo) modalTitulo.value = tituloInput || `Informe de Preventa — ${clienteSel.company_name}`

    // Mostrar resumen en modal
    const resumen = document.getElementById('modal-resumen')
    if (resumen) resumen.innerHTML = `
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <div style="flex:1;min-width:120px;padding:10px;background:var(--cp-bg-soft);border-radius:8px;text-align:center">
          <div style="font-size:20px;font-weight:700;color:var(--cp-blue-main)">${seleccionados.size}</div>
          <div style="font-size:11px;color:var(--cp-text-muted)">servicios</div>
        </div>
        <div style="flex:2;min-width:180px;padding:10px;background:var(--cp-bg-soft);border-radius:8px">
          <div style="font-weight:600;color:var(--cp-blue-main)">${clienteSel.company_name}</div>
          <div style="font-size:12px;color:var(--cp-text-muted)">${clienteSel.contact_name}</div>
          ${clienteSel.industry ? `<div style="font-size:11px;color:var(--cp-text-muted)">${clienteSel.industry}</div>` : ''}
        </div>
      </div>`

    document.getElementById('modal-ia').style.display = 'flex'
  })
}

// ── Modal de confirmación IA ──────────────────────────────────────────
function bindModal() {
  // Cerrar
  document.getElementById('modal-ia-close')?.addEventListener('click', cerrarModal)
  document.getElementById('modal-ia-cancelar')?.addEventListener('click', cerrarModal)
  document.getElementById('modal-ia')?.addEventListener('click', e => {
    if (e.target === document.getElementById('modal-ia')) cerrarModal()
  })

  // Confirmar generación con IA
  const btnConfirmar = document.getElementById('modal-ia-confirmar')
  btnConfirmar?.addEventListener('click', async () => {
    const titulo     = document.getElementById('modal-titulo')?.value.trim()
      || `Informe de Preventa — ${clienteSel.company_name}`
    const antecedente = document.getElementById('modal-antecedente')?.value.trim() || ''

    showSpinner(btnConfirmar, 'Generando con IA...')
    document.getElementById('modal-ia-cancelar').disabled = true

    // Progreso de pasos
    const pasos = ['modal-step-1','modal-step-2','modal-step-3','modal-step-4','modal-step-5','modal-step-6']
    const tiempos = [0, 6000, 12000, 18000, 23000, 28000]
    tiempos.forEach((t, i) => {
      setTimeout(() => {
        pasos.forEach((id, j) => {
          const el = document.getElementById(id)
          if (!el) return
          if (j < i)  el.className = 'modal-step modal-step--done'
          if (j === i) el.className = 'modal-step modal-step--active'
          if (j > i)  el.className = 'modal-step'
        })
      }, t)
    })

    document.getElementById('modal-progress').style.display = 'block'

    try {
      await generarPDF(true, titulo, antecedente)
      showAlert(`✅ Informe con IA generado para ${clienteSel.company_name}`, 'success', 6000)
      cerrarModal()
    } catch (e) {
      showAlert('Error generando informe: ' + e.message, 'error')
    } finally {
      hideSpinner(btnConfirmar)
      document.getElementById('modal-ia-cancelar').disabled = false
      document.getElementById('modal-progress').style.display = 'none'
      pasos.forEach(id => {
        const el = document.getElementById(id)
        if (el) el.className = 'modal-step'
      })
    }
  })
}

function cerrarModal() {
  document.getElementById('modal-ia').style.display = 'none'
}
