'use strict'

import { initSidebar } from './sidebar.js'
import { clientsAPI, servicesAPI } from './api.js'
import { showAlert } from './utils.js'

// Mock / Benchmark Data for Ley 21.719 Checklist
const CHECKLIST_ITEMS = [
  { id: 1, art: "Art. 13 - Legitimidad", req: "Contar con base legal probada o consentimiento explícito e informado para cada tratamiento", impact: "Alta", status: "cumplido", serviceId: 1, serviceName: "Asesoría en Cumplimiento & Privacidad" },
  { id: 2, art: "Art. 14 - Datos Sensibles", req: "Prohibición de tratamiento de datos sensibles salvo autorización expresa o ley especial", impact: "Alta", status: "cumplido", serviceId: 1, serviceName: "Asesoría en Cumplimiento & Privacidad" },
  { id: 3, art: "Art. 16 - Derechos ARCOP", req: "Mecanismo gratuito y expedito para ejercicio de Acceso, Rectificación, Cancelación, Oposición y Portabilidad", impact: "Alta", status: "proceso", serviceId: 2, serviceName: "Desarrollo Portal de Derechos ARCOP" },
  { id: 4, art: "Art. 18 - Notificación de Brechas", req: "Obligación de notificar brechas de seguridad a la Agencia y a los titulares en un plazo máximo de 72h", impact: "Alta", status: "nocumplido", serviceId: 3, serviceName: "Plan de Respuesta a Incidentes (IR Retainer)" },
  { id: 5, art: "Art. 20 - Medidas de Seguridad", req: "Implementación de medidas técnicas de seguridad (cifrado, control de acceso, trazabilidad)", impact: "Alta", status: "cumplido", serviceId: 4, serviceName: "Pentesting & Evaluación de Vulnerabilidades" },
  { id: 6, art: "Art. 22 - Delegado de Protección (DPO)", req: "Designación de un Oficial de Protección de Datos cuando la actividad principal lo requiera", impact: "Media", status: "nocumplido", serviceId: 5, serviceName: "DPO as a Service (Oficial de Privacidad)" },
  { id: 7, art: "Art. 25 - Evaluación de Impacto (EIPD)", req: "Realización de EIPD previa en tratamientos de alto riesgo o biométricos", impact: "Media", status: "proceso", serviceId: 1, serviceName: "Evaluación de Impacto (EIPD)" },
  { id: 8, art: "Art. 28 - Transferencia Internacional", req: "Garantías de nivel adecuado o cláusulas contractuales tipo en flujo transfronterizo", impact: "Media", status: "cumplido", serviceId: 1, serviceName: "Auditoría de Contratos & DPAs" },
  { id: 9, art: "Art. 31 - Registro de Tratamientos (RAT)", req: "Mantener un Registro de Actividades de Tratamiento (RoPA) actualizado disponible para la autoridad", impact: "Media", status: "proceso", serviceId: 1, serviceName: "Elaboración de RAT / RoPA" },
  { id: 10, art: "Art. 35 - Capacitación de Personal", req: "Programa continuo de concientización y seguridad de la información para colaboradores", impact: "Baja", status: "nocumplido", serviceId: 6, serviceName: "Concientización & Simulación Phishing" }
]

const DOC_TEMPLATES = {
  pol_priv: `POLÍTICA GENERAL DE PRIVACIDAD Y TRATAMIENTO DE DATOS PERSONALES
[EMPRESA CLIENTE OBJETIVO]

1. OBJETIVO Y ALCANCE
La presente política establece los estándares de protección de datos personales aplicados por [EMPRESA CLIENTE OBJETIVO], en estricto cumplimiento con la Ley de Protección de Datos Personales de Chile (Ley 21.719 / 19.628).

2. PRINCIPIOS RECTORES
- Legitimidad y Lealtad: Los datos serán tratados únicamente con base legal válida.
- Finalidad: Tratamiento limitado exclusivamente a los fines informados.
- Proporcionalidad: Solo se recolectarán los datos estrictamente necesarios.

3. DERECHOS DE LOS TITULARES (ARCOP)
Los titulares podrán ejercer sus derechos de Acceso, Rectificación, Cancelación, Oposición y Portabilidad enviando una solicitud a privacidad@[empresa].cl.`,

  clausula_cons: `CLÁUSULA DE CONSENTIMIENTO INFORMADO PARA TRATAMIENTO DE DATOS
Mediante la aceptación del presente documento, declaro autorizar expresamente a [EMPRESA CLIENTE OBJETIVO] para recolectar y tratar mis datos personales con la finalidad de gestionar la relación contractual y comercial.

Tengo conocimiento de que puedo revocar este consentimiento en cualquier momento y ejercer mis derechos ARCOP de acuerdo a la Ley 21.719.`,

  notif_brecha: `PROTOCOLO DE GESTIÓN Y NOTIFICACIÓN DE BRECHAS DE SEGURIDAD
1. DETECCIÓN: Ante la sospecha o confirmación de una brecha que comprometa datos personales, el equipo detectante informará de inmediato al CISO / DPO.
2. EVALUACIÓN (T+2 Horas): Determinación del nivel de riesgo para los derechos de los titulares.
3. NOTIFICACIÓN A LA AGENCIA (T+72 Horas): Comunicación formal a la Agencia de Protección de Datos y al CSIRT Nacional conteniendo descripción del incidente y medidas correctivas.`,

  dpa_contrato: `ACUERDO DE ENCARGADO DE TRATAMIENTO DE DATOS (DPA)
Entre [EMPRESA CLIENTE OBJETIVO] (Responsable) y EL PROVEEDOR (Encargado).
El Encargado se compromete a:
a) Tratar los datos únicamente siguiendo instrucciones documentadas del Responsable.
b) Implementar medidas de seguridad técnicas y organizativas equivalentes a ISO 27001.
c) Notificar cualquier brecha de seguridad en un plazo no mayor a 24 horas.`
}

document.addEventListener('DOMContentLoaded', () => {
  initSidebar()
  initTabs()
  loadClients()
  renderChecklist()
  initFineCalculator()
  initDocGenerator()
  initQuoteConvert()
})

/* ── TAB NAVIGATION ── */
function initTabs() {
  const tabBtns = document.querySelectorAll('.ciso-tab-btn')
  const tabContents = document.querySelectorAll('.ciso-tab-content')

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab
      tabBtns.forEach(b => b.classList.remove('active'))
      tabContents.forEach(c => c.classList.remove('active'))

      btn.classList.add('active')
      const targetEl = document.getElementById(target)
      if (targetEl) targetEl.classList.add('active')
    })
  })
}

/* ── LOAD CLIENTS ── */
async function loadClients() {
  const select = document.getElementById('ciso-client-select')
  if (!select) return

  try {
    const clients = await clientsAPI.getAll()
    if (clients && clients.length > 0) {
      select.innerHTML = ''
      clients.forEach(c => {
        const opt = document.createElement('option')
        opt.value = c.id
        opt.textContent = `${c.company_name} (${c.industry || 'General'})`
        select.appendChild(opt)
      })
    }
  } catch (e) {
    console.log('Usando clientes de prueba local para CISO Assistant.')
  }

  select.addEventListener('change', () => {
    const companyName = select.options[select.selectedIndex].text.split(' (')[0]
    showAlert(`Empresa seleccionada para diagnóstico: ${companyName}`, 'info')
    recalculateScore()
  })
}

/* ── CHECKLIST RENDER & SCORE CALCULATION ── */
function renderChecklist() {
  const tbody = document.getElementById('checklist-tbody')
  if (!tbody) return

  tbody.innerHTML = ''

  CHECKLIST_ITEMS.forEach(item => {
    const tr = document.createElement('tr')
    tr.innerHTML = `
      <td><strong>${item.art}</strong></td>
      <td style="max-width:320px;">${item.req}</td>
      <td><span class="badge-status badge-status--${item.impact === 'Alta' ? 'danger' : 'warning'}">${item.impact}</span></td>
      <td>
        <select class="chk-status-select" data-id="${item.id}" style="padding:4px 8px; font-size:0.85rem;">
          <option value="cumplido" ${item.status === 'cumplido' ? 'selected' : ''}>✅ Cumplido</option>
          <option value="proceso" ${item.status === 'proceso' ? 'selected' : ''}>⏳ En Proceso</option>
          <option value="nocumplido" ${item.status === 'nocumplido' ? 'selected' : ''}>❌ No Cumplido</option>
        </select>
      </td>
      <td>
        <span style="font-size:0.85rem; color:var(--cp-blue-main);"><i class="ti ti-shield"></i> ${item.serviceName}</span>
      </td>
    `
    tbody.appendChild(tr)
  })

  document.querySelectorAll('.chk-status-select').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const id = parseInt(e.target.dataset.id)
      const found = CHECKLIST_ITEMS.find(x => x.id === id)
      if (found) found.status = e.target.value
      recalculateScore()
    })
  })

  const resetBtn = document.getElementById('btn-reset-checklist')
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      recalculateScore()
      showAlert('Score recalculado con éxito.', 'success')
    })
  }
}

function recalculateScore() {
  const total = CHECKLIST_ITEMS.length
  let scorePoints = 0
  let pendingCount = 0

  CHECKLIST_ITEMS.forEach(item => {
    if (item.status === 'cumplido') scorePoints += 100
    else if (item.status === 'proceso') scorePoints += 40
    else pendingCount++
  })

  const finalScore = Math.round(scorePoints / total)
  const scoreVal = document.getElementById('kpi-score-val')
  const gapsVal = document.getElementById('kpi-gaps-val')

  if (scoreVal) scoreVal.textContent = `${finalScore}%`
  if (gapsVal) gapsVal.textContent = `${pendingCount} Pendientes`
}

/* ── FINE SIMULATION CALCULATOR ── */
function initFineCalculator() {
  const simType = document.getElementById('fine-sim-type')
  const chk1 = document.getElementById('chk-agr1')
  const chk2 = document.getElementById('chk-agr2')
  const chk3 = document.getElementById('chk-agr3')
  const totalDisplay = document.getElementById('sim-fine-total')

  function calculateFine() {
    if (!simType || !totalDisplay) return
    let base = 5000
    if (simType.value === 'grave') base = 10000
    if (simType.value === 'gravisima') base = 20000

    let multiplier = 1.0
    if (chk1 && chk1.checked) multiplier += 0.15
    if (chk2 && chk2.checked) multiplier += 0.25
    if (chk3 && chk3.checked) multiplier += 0.20

    const totalUTM = Math.round(base * multiplier)
    totalDisplay.textContent = `${totalUTM.toLocaleString('es-CL')} UTM`
  }

  if (simType) simType.addEventListener('change', calculateFine)
  if (chk1) chk1.addEventListener('change', calculateFine)
  if (chk2) chk2.addEventListener('change', calculateFine)
  if (chk3) chk3.addEventListener('change', calculateFine)
}

/* ── DOCUMENT GENERATOR ── */
function initDocGenerator() {
  const select = document.getElementById('doc-template-select')
  const preview = document.getElementById('doc-preview-text')
  const copyBtn = document.getElementById('btn-copy-doc')

  function updateDocText() {
    if (!select || !preview) return
    const key = select.value
    const clientSelect = document.getElementById('ciso-client-select')
    const companyName = clientSelect ? clientSelect.options[clientSelect.selectedIndex].text.split(' (')[0] : 'Empresa Cliente'
    const rawText = DOC_TEMPLATES[key] || ''
    preview.textContent = rawText.replace(/\[EMPRESA CLIENTE OBJETIVO\]/g, companyName)
  }

  if (select) select.addEventListener('change', updateDocText)
  updateDocText()

  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      if (preview) {
        navigator.clipboard.writeText(preview.textContent)
        showAlert('Documento copiado al portapapeles.', 'success')
      }
    })
  }
}

/* ── QUOTE CONVERSION INTEGRATION ── */
function initQuoteConvert() {
  const btn = document.getElementById('btn-convert-quote')
  if (!btn) return

  btn.addEventListener('click', () => {
    const pendingServices = CHECKLIST_ITEMS
      .filter(x => x.status !== 'cumplido')
      .map(x => x.serviceId)

    const uniqueServiceIds = [...new Set(pendingServices)].join(',')
    const clientSelect = document.getElementById('ciso-client-select')
    const clientId = clientSelect ? clientSelect.value : '1'

    showAlert('Redirigiendo a Generación de Propuestas con los servicios requeridos preseleccionados...', 'info')
    setTimeout(() => {
      window.location.href = `report.html?cliente_id=${clientId}&services=${uniqueServiceIds}`
    }, 1200)
  })
}
