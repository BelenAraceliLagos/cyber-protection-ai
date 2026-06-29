'use strict'

import { showAlert, requireAuth, escapeHtml, escapeAttr } from './utils.js'

import { BASE_URL } from './config.js'

function getToken() {
  const token = sessionStorage.getItem('cp_token')
  if (!token) return ''

  // Verificar si el token expiró
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const ahora   = Math.floor(Date.now() / 1000)
    if (payload.exp && payload.exp < ahora) {
      // Token expirado — limpiar y redirigir
      sessionStorage.removeItem('cp_token')
      showAlert('Tu sesión expiró. Redirigiendo al login...', 'warning')
      setTimeout(() => { window.location.href = '/pages/login.html' }, 2000)
      return ''
    }
  } catch(e) { /* token malformado */ }

  return token
}

function showSpinner(btn, txt) {
  if (!btn) return
  btn._orig    = btn.innerHTML
  btn.disabled = true
  btn.innerHTML = `<i class="ti ti-loader-2 is-spinning"></i> ${txt}`
}
function hideSpinner(btn) {
  if (!btn) return
  btn.disabled  = false
  if (btn._orig) btn.innerHTML = btn._orig
}

// ── Estado global ─────────────────────────────────────────────────────
let archivosSeleccionados = []
let resultadosExtraidos   = []
let logosSeleccionados    = {}   // { idx: path }

// Cache de BD para comparar
let bdClientes  = []   // [{id, company_name, email}]
let bdServicios = []   // [{id, name}]

// ══════════════════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════════════════
export async function initIngestion() {
  if (!requireAuth()) return

  // Esperar que el token esté disponible (puede tardar unos ms en sessionStorage)
  await new Promise(r => setTimeout(r, 150))

  // Cargar BD en paralelo (silencioso si falla)
  await Promise.all([cargarClientesBD(), cargarServiciosBD()])

  bindDropzone()
  bindAnalizar()
  bindGuardarTodos()
}

// ── Cargar datos de BD para comparación ───────────────────────────────
async function cargarClientesBD() {
  try {
    const r = await fetch(`${BASE_URL}/clients`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (r.ok) bdClientes = await r.json()
  } catch (e) { console.warn('No se pudo cargar clientes de BD:', e) }
}

async function cargarServiciosBD() {
  try {
    const r = await fetch(`${BASE_URL}/services`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (r.ok) bdServicios = await r.json()
  } catch (e) { console.warn('No se pudo cargar servicios de BD:', e) }
}

// ── Comparadores ──────────────────────────────────────────────────────
function clienteExisteEnBD(company_name) {
  if (!company_name) return null
  const q = company_name.toLowerCase().trim()
  return bdClientes.find(c =>
    c.company_name.toLowerCase().trim().includes(q) ||
    q.includes(c.company_name.toLowerCase().trim())
  ) || null
}

function servicioExisteEnBD(nombre) {
  if (!nombre) return null
  const q = nombre.toLowerCase().trim()
  return bdServicios.find(s =>
    s.name.toLowerCase().trim() === q ||
    s.name.toLowerCase().trim().includes(q) ||
    q.includes(s.name.toLowerCase().trim())
  ) || null
}

// ══════════════════════════════════════════════════════════════════════
// DROPZONE
// ══════════════════════════════════════════════════════════════════════
function bindDropzone() {
  const drop   = document.getElementById('ing-drop')
  const input  = document.getElementById('ing-file-input')
  const btnSel = document.getElementById('ing-select-btn')
  if (!drop || !input || !btnSel) return

  btnSel.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); input.value = ''; input.click() })
  input.addEventListener('change', e => { if (e.target.files.length) agregarArchivos(Array.from(e.target.files)) })
  drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('ing-drop--over') })
  drop.addEventListener('dragleave', e => { e.preventDefault(); drop.classList.remove('ing-drop--over') })
  drop.addEventListener('drop', e => {
    e.preventDefault(); drop.classList.remove('ing-drop--over')
    if (e.dataTransfer?.files.length) agregarArchivos(Array.from(e.dataTransfer.files))
  })
  drop.addEventListener('click', e => {
    if (e.target === btnSel || btnSel.contains(e.target)) return
    input.value = ''; input.click()
  })
}

function agregarArchivos(nuevos) {
  const ok = /\.(pdf|docx?|xlsx?|txt|jpe?g|png|gif|webp)$/i
  for (const f of nuevos) {
    if (!ok.test(f.name)) { showAlert(`Formato no soportado: ${f.name}`, 'warning'); continue }
    if (!archivosSeleccionados.some(x => x.name === f.name && x.size === f.size))
      archivosSeleccionados.push(f)
  }
  renderCola()
}

function renderCola() {
  const cola = document.getElementById('ing-queue')
  const btn  = document.getElementById('ing-analizar-btn')
  if (!cola) return
  cola.innerHTML = archivosSeleccionados.map((f, i) => `
    <div class="ing-file">
      <i class="ti ${icoExt(f.name)} ing-file__icon"></i>
      <span class="ing-file__name" title="${escapeAttr(f.name)}">${escapeHtml(f.name)}</span>
      <span class="ing-file__size">${(f.size/1024).toFixed(1)} KB</span>
      <button class="ing-file__remove" onclick="window.removeFile(${i})"><i class="ti ti-x"></i></button>
    </div>`).join('')
  if (btn) btn.disabled = !archivosSeleccionados.length
}

function icoExt(nombre) {
  const e = (nombre.split('.').pop()||'').toLowerCase()
  if (e === 'pdf') return 'ti-file-type-pdf'
  if (['docx','doc'].includes(e)) return 'ti-file-type-docx'
  if (['xlsx','xls'].includes(e)) return 'ti-file-spreadsheet'
  if (['jpg','jpeg','png','gif','webp'].includes(e)) return 'ti-photo'
  return 'ti-file-text'
}

window.removeFile = function(idx) { archivosSeleccionados.splice(idx,1); renderCola() }

// ══════════════════════════════════════════════════════════════════════
// ANALIZAR
// ══════════════════════════════════════════════════════════════════════
function bindAnalizar() {
  const btn = document.getElementById('ing-analizar-btn')
  if (!btn) return

  btn.addEventListener('click', async () => {
    if (!archivosSeleccionados.length) return

    // Verificar si hay documentos (no solo imágenes) que necesitan IA
    const necesitaIA = archivosSeleccionados.some(f =>
      !f.name.match(/\.(jpe?g|png|gif|webp)$/i)
    )

    // Si hay documentos, verificar que Ollama esté activo primero
    if (necesitaIA) {
      showSpinner(btn, 'Verificando Ollama...')
      try {
        const check = await fetch(`${BASE_URL}/ingestion/check-ollama`, {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        })
        const estado = await check.json()

        if (!estado.disponible) {
          hideSpinner(btn)
          mostrarModalOllama('no_activo')
          return
        }
        if (!estado.gemma_listo) {
          hideSpinner(btn)
          mostrarModalOllama('sin_modelo')
          return
        }
      } catch(e) {
        hideSpinner(btn)
        mostrarModalOllama('no_activo')
        return
      }
    }

    // Proceder con el análisis
    showSpinner(btn, `Analizando ${archivosSeleccionados.length} archivo(s)...`)
    document.getElementById('ing-resultados').style.display = 'none'

    const fd = new FormData()
    for (const f of archivosSeleccionados) fd.append('files', f)

    try {
      const token = getToken()
      if (!token) throw new Error('Sesión expirada. Recarga la página e inicia sesión nuevamente.')

      const r = await fetch(`${BASE_URL}/ingestion/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: fd
      })
      if (!r.ok) {
        const errData = await r.json().catch(() => ({}))
        if (r.status === 401) {
          sessionStorage.removeItem('cp_token')
          setTimeout(() => { window.location.href = '/pages/login.html' }, 2000)
          throw new Error('Sesión expirada. Redirigiendo al login...')
        }
        throw new Error(errData.detail || `Error del servidor (${r.status})`)
      }

      const data = await r.json()
      resultadosExtraidos = data.archivos || []

      await Promise.all([cargarClientesBD(), cargarServiciosBD()])

      renderResultados()
      document.getElementById('ing-resultados').style.display = 'block'
      showAlert(`✅ ${resultadosExtraidos.length} archivo(s) analizados correctamente.`, 'success', 5000)

    } catch (e) {
      showAlert('Error al analizar: ' + e.message, 'error')
    } finally {
      hideSpinner(btn)
    }
  })
}

// ── Modal Ollama no disponible ────────────────────────────────────────
function mostrarModalOllama(motivo) {
  document.getElementById('modal-ollama')?.remove()

  const esSinModelo = motivo === 'sin_modelo'
  const titulo = esSinModelo ? 'Modelo Gemma no encontrado' : 'Ollama no está disponible'
  const desc   = esSinModelo
    ? 'Ollama está activo pero necesita descargar el modelo Gemma para analizar documentos.'
    : 'Para analizar documentos históricos necesitas tener Ollama corriendo con el modelo Gemma.'

  const modal = document.createElement('div')
  modal.id = 'modal-ollama'
  modal.className = 'ollama-modal'
  modal.innerHTML = `
    <div class="ollama-modal__dialog">
      <div class="ollama-modal__header">
        <div class="ollama-modal__icon">${esSinModelo ? '📦' : '⚠️'}</div>
        <div>
          <div class="ollama-modal__title">${titulo}</div>
          <div class="ollama-modal__desc">${desc}</div>
        </div>
      </div>
      <div class="ollama-modal__body">
        ${!esSinModelo ? `
          <div class="ollama-modal__hint">
            1. Abre una nueva terminal y ejecuta:
          </div>
          <div class="ollama-modal__code ollama-modal__code--serve">
            ollama serve
          </div>` : ''}
        <div class="ollama-modal__hint">
          ${esSinModelo ? 'Ejecuta en la terminal:' : '2. Si no tienes el modelo Gemma:'}
        </div>
        <div class="ollama-modal__code">
          ollama pull gemma3:4b
        </div>
        <div class="ollama-modal__note">
          💡 Las imágenes PNG/JPG no necesitan Ollama — puedes subirlas sin iniciar el servicio.
        </div>
      </div>
      <div class="ollama-modal__actions">
        <button onclick="document.getElementById('modal-ollama').remove()"
          class="btn btn--secondary btn--sm">Cerrar</button>
        <button onclick="window.reintentarConOllama()" class="btn btn--primary btn--sm">
          <i class="ti ti-refresh btn__icon"></i>Ya inicié Ollama — reintentar
        </button>
      </div>
    </div>`

  document.body.appendChild(modal)
  modal.addEventListener('click', e => { if (e.target === modal) modal.remove() })
}

window.reintentarConOllama = function() {
  document.getElementById('modal-ollama')?.remove()
  setTimeout(() => document.getElementById('ing-analizar-btn')?.click(), 300)
}

// ══════════════════════════════════════════════════════════════════════
// RENDERIZAR RESULTADOS CON COMPARACIÓN EN TIEMPO REAL
// ══════════════════════════════════════════════════════════════════════
function renderResultados() {
  const lista = document.getElementById('ing-resultados-lista')
  if (!lista) return
  lista.innerHTML = ''
  resultadosExtraidos.forEach((res, idx) => renderTarjeta(lista, res, idx))
}

// ── Tarjeta simplificada para imágenes (solo asset) ──────────────────
function renderTarjetaImagen(container, res, idx) {
  const imgPath = res.tmp_path || res.logo_path || ''
  const nombre  = res.nombre_archivo || 'imagen'
  // Pre-rellenar nombre: quitar extensión y separadores
  const nombreSugerido = nombre
    .replace(/\.(png|jpe?g|gif|webp)$/i, '')
    .replace(/[-_]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

  const div = document.createElement('div')
  div.className = 'ing-resultado'
  div.id = `resultado-${idx}`
  // Guardar ruta en dataset para acceder sin onclick params
  div.dataset.imgPath = imgPath

  div.innerHTML = `
    <div class="ing-resultado__header">
      <i class="ti ti-photo ing-file__icon ing-file__icon--image"></i>
      <span class="ing-resultado__title">${escH(nombre)}</span>
      <span class="ing-badge ing-badge--image">🖼️ Logo / Imagen</span>
      ${res.size_kb ? `<span class="ing-muted">${res.size_kb} KB</span>` : ''}
    </div>
    <div class="ing-resultado__body">

      <div class="ing-image-preview">
        <img class="ing-image-preview__img" src="${BASE_URL}/ingestion/logo-preview?path=${encodeURIComponent(imgPath)}"
          onerror="this.style.display='none'">
        <div>
          <div class="ing-image-preview__title">Vista previa del logo</div>
          <div class="ing-muted ing-muted--md">
            Se guardará en
            <code class="ing-code-inline">assets/logo_nombre_empresa.jpg</code>
          </div>
        </div>
      </div>

      <div class="campo-grupo campo-grupo--spaced">
        <label class="campo-label">Nombre de empresa</label>
        <input class="campo-input img-empresa-input"
          placeholder="Ej: Apprecio, UNAB, Banco Estado..."
          value="${escH(nombreSugerido)}">
        <div class="ing-form-hint">
          El archivo quedará como <code>logo_nombre_empresa.jpg</code> en la carpeta
          <code>assets/</code> dentro de tu proyecto
        </div>
      </div>

      <div class="ing-inline-actions">
        <button type="button" class="btn btn--secondary btn--sm img-descartar-btn">
          <i class="ti ti-x btn__icon"></i>Descartar
        </button>
        <button type="button" class="btn btn--sm btn--ai-gradient img-guardar-btn">
          <i class="ti ti-device-floppy"></i>
          Guardar en assets
        </button>
      </div>
    </div>`

  container.appendChild(div)

  // ── Eventos directos en el DOM (sin onclick inline) ───────────────
  div.querySelector('.img-descartar-btn').addEventListener('click', () => div.remove())

  div.querySelector('.img-guardar-btn').addEventListener('click', async () => {
    const btn     = div.querySelector('.img-guardar-btn')
    const empresa = div.querySelector('.img-empresa-input')?.value.trim()
    const path    = div.dataset.imgPath

    if (!empresa) {
      showAlert('Ingresa el nombre de la empresa para nombrar el archivo', 'warning')
      div.querySelector('.img-empresa-input')?.focus()
      return
    }

    const origHTML = btn.innerHTML
    btn.disabled   = true
    btn.innerHTML  = '<i class="ti ti-loader-2 is-spinning"></i> Guardando...'

    try {
      const token = getToken()
      if (!token) throw new Error('Sesión expirada. Recarga e inicia sesión.')

      const r = await fetch(`${BASE_URL}/ingestion/save-logo`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body:    JSON.stringify({ tmp_path: path, nombre_empresa: empresa })
      })

      if (r.status === 401) {
        sessionStorage.removeItem('cp_token')
        window.location.href = '/pages/login.html'
        return
      }

      let data = {}
      try { data = await r.json() } catch(e) {}

      if (!r.ok) {
        throw new Error(data.detail || `Error del servidor (${r.status})`)
      }

      // Marcar como guardado
      div.style.opacity = '0.55'
      div.style.pointerEvents = 'none'
      div.querySelector('.ing-resultado__header')
        ?.insertAdjacentHTML('beforeend',
          '<span class="ing-saved-badge ing-saved-badge--strong">✅ Guardado</span>')

      showAlert(`✅ Logo guardado como: ${data.nombre_archivo} — disponible en assets/`, 'success', 7000)

    } catch (e) {
      showAlert('Error al guardar: ' + e.message, 'error')
      btn.disabled  = false
      btn.innerHTML = origHTML
    }
  })
}

function renderTarjeta(container, res, idx) {
  // ── Imágenes: flujo simplificado de solo guardar como asset ──────
  if (res.tipo === 'imagen') {
    renderTarjetaImagen(container, res, idx)
    return
  }

  const datos   = res.datos || {}
  const cliente = datos.cliente || {}
  const srvs    = datos.servicios || []
  const conf    = datos.confianza || 'baja'

  const confClass = `ing-confidence--${conf}`
  const confLabel = { alta: '✅ Alta', media: '⚠️ Media', baja: '❌ Baja' }[conf] || conf

  // ── Verificar cliente en BD ────────────────────────────────────────
  const clienteBD = clienteExisteEnBD(cliente.company_name)
  const clienteBadge = clienteBD
    ? `<span class="ing-badge ing-badge--existing">
        ♻️ Ya existe en BD (id:${clienteBD.id})
       </span>`
    : cliente.company_name
      ? `<span class="ing-badge ing-badge--new">
          ✨ Cliente nuevo
         </span>`
      : ''

  // ── Verificar servicios en BD ─────────────────────────────────────
  const srvsConEstado = srvs.map(s => ({
    ...s,
    enBD: servicioExisteEnBD(s.nombre)
  }))
  const nuevos     = srvsConEstado.filter(s => !s.enBD).length
  const existentes = srvsConEstado.filter(s =>  s.enBD).length

  const srvsJson = JSON.stringify(srvsConEstado)

  const div = document.createElement('div')
  div.className = 'ing-resultado'
  div.id = `resultado-${idx}`

  div.innerHTML = `
    <div class="ing-resultado__header">
      <i class="ti ${icoExt(res.nombre_archivo)} ing-file__icon"></i>
      <span class="ing-resultado__title">${res.nombre_archivo}</span>
      <span class="ing-confidence ${confClass}">Confianza: ${confLabel}</span>
      ${res.size_kb ? `<span class="ing-muted">${res.size_kb} KB</span>` : ''}
    </div>
    <div class="ing-resultado__body">
      ${datos.error ? `
        <div class="ing-error-box">
          <i class="ti ti-alert-triangle"></i> ${datos.error}
        </div>` : `

        ${datos.proveedor_detectado ? `
          <div class="ing-warning-box">
            <i class="ti ti-alert-triangle ing-warning-box__icon"></i>
            Proveedor detectado (NO es el cliente): <strong>${escH(datos.proveedor_detectado)}</strong>
          </div>` : ''}

        <!-- DATOS DEL CLIENTE -->
        <div class="ing-section">
          <div class="ing-section__header">
            <span class="ing-section__title">DATOS DEL CLIENTE</span>
            ${clienteBadge}
          </div>
          ${clienteBD ? `
            <div class="ing-existing-client">
              <i class="ti ti-user-check ing-existing-client__icon"></i>
              <div>
                <strong>${escH(clienteBD.company_name)}</strong> ya existe en la base de datos.
                Solo se completarán los campos que estén vacíos actualmente.
              </div>
            </div>` : ''}
          <div class="campo-grid">
            <div class="campo-grupo">
              <label class="campo-label">Empresa *</label>
              <input class="campo-input" id="res-${idx}-company"
                value="${escH(cliente.company_name||'')}" placeholder="Nombre de la empresa">
            </div>
            <div class="campo-grupo">
              <label class="campo-label">Contacto</label>
              <input class="campo-input" id="res-${idx}-contact"
                value="${escH(cliente.contact_name||'')}" placeholder="Nombre del contacto">
            </div>
            <div class="campo-grupo">
              <label class="campo-label">Email</label>
              <input class="campo-input" id="res-${idx}-email"
                value="${escH(cliente.email||'')}" placeholder="email@empresa.cl">
            </div>
            <div class="campo-grupo">
              <label class="campo-label">Teléfono</label>
              <input class="campo-input" id="res-${idx}-phone"
                value="${escH(cliente.phone||'')}" placeholder="+56 9 ...">
            </div>
            <div class="campo-grupo">
              <label class="campo-label">Industria</label>
              <input class="campo-input" id="res-${idx}-industry"
                value="${escH(cliente.industry||'')}" placeholder="Sector o rubro">
            </div>
            <div class="campo-grupo">
              <label class="campo-label">Notas</label>
              <input class="campo-input" id="res-${idx}-notes"
                value="${escH(cliente.notes||'')}" placeholder="Contexto adicional">
            </div>
          </div>
          ${datos.contexto ? `
            <div class="ing-context">
              <strong>Contexto extraído:</strong> ${escH(datos.contexto)}
            </div>` : ''}
        </div>

        <!-- LOGOS EXTRAÍDOS -->
        ${res.logos_extra && res.logos_extra.length ? `
          <div class="ing-section">
            <div class="ing-logo-title">
              LOGOS DETECTADOS EN EL DOCUMENTO — selecciona el del cliente
            </div>
            <div class="ing-logo-grid" id="logos-${idx}">
              ${res.logos_extra.map((lpath, li) => `
                <div class="logo-opcion ing-logo-option" id="logo-opcion-${idx}-${li}"
                  data-result-idx="${idx}" data-logo-idx="${li}" data-logo-path="${escapeAttr(lpath)}">
                  <img src="${BASE_URL}/ingestion/logo-preview?path=${encodeURIComponent(lpath)}"
                    class="ing-logo-option__img"
                    onerror="this.parentElement.style.opacity='0.3'">
                  <span class="ing-logo-option__label">Logo ${li+1}</span>
                </div>`).join('')}
              <div class="ing-logo-option ing-logo-option--empty" data-result-idx="${idx}" data-logo-idx="-1" data-logo-path="">
                <i class="ti ti-x"></i>Ninguno
              </div>
            </div>
            <div id="logo-sel-${idx}" class="ing-logo-status">Sin logo seleccionado</div>
          </div>` : ''}

        <!-- SERVICIOS DETECTADOS CON ESTADO -->
        ${srvsConEstado.length ? `
          <div>
            <div class="ing-services-header">
              <span class="ing-services-header__title">
                SERVICIOS DETECTADOS
              </span>
              ${nuevos > 0 ? `<span class="ing-badge ing-badge--new">✨ ${nuevos} nuevo(s)</span>` : ''}
              ${existentes > 0 ? `<span class="ing-badge ing-badge--neutral">♻️ ${existentes} ya en BD</span>` : ''}
            </div>
            <div class="srv-lista">
              ${srvsConEstado.map((s, si) => `
                <div class="srv-item ${s.enBD ? 'srv-item--muted' : ''}">
                  <input type="checkbox" id="srv-${idx}-${si}"
                    ${s.enBD ? '' : 'checked'}
                    ${s.enBD ? 'title="Ya existe en BD"' : ''}>
                  <span class="srv-item__nombre">${escH(s.nombre)}</span>
                  ${s.enBD
                    ? `<span class="ing-badge ing-badge--neutral ing-badge--compact">
                        ♻️ En BD
                       </span>`
                    : `<span class="ing-badge ing-badge--new ing-badge--compact">
                        ✨ Nuevo
                       </span>`}
                  ${s.precio_uf
                    ? `<span class="srv-item__precio">${s.precio_uf} UF</span>`
                    : ''}
                </div>`).join('')}
            </div>
            ${existentes > 0 ? `
              <div class="ing-help-text">
                Los servicios marcados como "En BD" están desmarcados por defecto para evitar duplicados.
              </div>` : ''}
          </div>` : `
          <div class="ing-empty-text">
            No se detectaron servicios en este archivo.
          </div>`}

        <!-- ACCIONES -->
        <div class="ing-result-actions">
          <button class="btn btn--secondary btn--sm"
            onclick="window.descartarResultado(${idx})">Descartar</button>
          <button class="btn btn--primary btn--sm"
            onclick="window.guardarResultado(${idx})"
            data-srvs='${escapeAttr(srvsJson)}'
            data-logo="${escapeAttr(res.logo_path||'')}">
            <i class="ti ti-device-floppy btn__icon"></i>Guardar en BD
          </button>
        </div>`}
    </div>`

  container.appendChild(div)

  div.querySelectorAll('[data-logo-idx]').forEach(option => {
    option.addEventListener('click', () => {
      window.seleccionarLogo(
        Number(option.dataset.resultIdx),
        Number(option.dataset.logoIdx),
        option.dataset.logoPath || ''
      )
    })
  })
}

// ══════════════════════════════════════════════════════════════════════
// LOGO SELECTOR
// ══════════════════════════════════════════════════════════════════════
window.seleccionarLogo = function(idx, logoIdx, logoPath) {
  document.querySelectorAll(`#logos-${idx} .logo-opcion`).forEach(el => {
    el.style.borderColor = 'var(--cp-border)'; el.style.background = 'white'
  })
  const lbl = document.getElementById(`logo-sel-${idx}`)
  if (logoIdx >= 0) {
    const el = document.getElementById(`logo-opcion-${idx}-${logoIdx}`)
    if (el) { el.style.borderColor = '#6366f1'; el.style.background = '#eef2ff' }
    logosSeleccionados[idx] = logoPath
    if (lbl) lbl.textContent = `✅ Logo ${logoIdx+1} seleccionado como logo del cliente`
  } else {
    delete logosSeleccionados[idx]
    if (lbl) lbl.textContent = 'Sin logo seleccionado'
  }
}

// ══════════════════════════════════════════════════════════════════════
// GUARDAR
// ══════════════════════════════════════════════════════════════════════
window.guardarResultado = async function(idx) {
  const btn      = document.querySelector(`#resultado-${idx} [onclick*="guardarResultado"]`)
  const srvsJson = btn?.dataset.srvs || '[]'
  const logoPath = logosSeleccionados[idx] || btn?.dataset.logo || ''

  let srvsOriginales = []
  try { srvsOriginales = JSON.parse(srvsJson) } catch(e) {}

  const cliente = {
    company_name: document.getElementById(`res-${idx}-company`)?.value.trim()  || null,
    contact_name: document.getElementById(`res-${idx}-contact`)?.value.trim()  || null,
    email:        document.getElementById(`res-${idx}-email`)?.value.trim()    || null,
    phone:        document.getElementById(`res-${idx}-phone`)?.value.trim()    || null,
    industry:     document.getElementById(`res-${idx}-industry`)?.value.trim() || null,
    notes:        document.getElementById(`res-${idx}-notes`)?.value.trim()    || null,
  }

  if (!cliente.company_name) {
    showAlert('El nombre de la empresa es obligatorio', 'warning')
    document.getElementById(`res-${idx}-company`)?.focus()
    return
  }

  // Solo guardar servicios marcados con checkbox
  const servicios = srvsOriginales
    .filter((s, si) => document.getElementById(`srv-${idx}-${si}`)?.checked)
    .map(s => ({ nombre: s.nombre, descripcion: s.descripcion||null, precio_uf: s.precio_uf||null }))

  if (btn) showSpinner(btn, 'Guardando...')

  try {
    const r = await fetch(`${BASE_URL}/ingestion/confirm`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
      body:    JSON.stringify({ cliente, servicios, crear_servicios: true, logo_tmp_path: logoPath||null })
    })
    if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail || `Error ${r.status}`)

    const data = await r.json()

    // Marcar tarjeta como completada
    const tarjeta = document.getElementById(`resultado-${idx}`)
    if (tarjeta) {
      tarjeta.style.opacity = '0.5'
      tarjeta.style.pointerEvents = 'none'
      tarjeta.querySelector('.ing-resultado__header')
        ?.insertAdjacentHTML('beforeend',
          '<span class="ing-saved-badge">✅ Guardado</span>')
    }

    // Actualizar cache local para futuras comparaciones
    if (data.accion_cliente === 'creado') {
      bdClientes.push({ id: data.cliente_id, company_name: cliente.company_name, email: cliente.email })
    }
    for (const nombre of (data.servicios_creados || [])) {
      bdServicios.push({ id: Date.now(), name: nombre })
    }

    const msg = `${data.accion_cliente === 'creado' ? '✅ Cliente creado' : '✅ Cliente actualizado'}: ${data.cliente_nombre}` +
      (data.servicios_creados?.length ? `. ${data.servicios_creados.length} servicio(s) nuevo(s) agregados.` : '') +
      (data.logo_guardado ? ' Logo guardado en assets.' : '')
    showAlert(msg, 'success', 7000)

  } catch (e) {
    showAlert('Error al guardar: ' + e.message, 'error')
  } finally {
    if (btn) hideSpinner(btn)
  }
}

window.guardarImagen = async function(idx, imgPath) {
  const btn     = document.getElementById(`img-btn-${idx}`)
  const empresa = document.getElementById(`img-${idx}-empresa`)?.value.trim()

  if (!empresa) {
    showAlert('Ingresa el nombre de la empresa para nombrar el archivo', 'warning')
    document.getElementById(`img-${idx}-empresa`)?.focus()
    return
  }

  const origText = btn?.innerHTML
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="ti ti-loader-2 is-spinning"></i> Guardando...' }

  try {
    const token = getToken()
    const r = await fetch(`${BASE_URL}/ingestion/save-logo`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body:    JSON.stringify({ tmp_path: imgPath, nombre_empresa: empresa })
    })
    if (!r.ok) {
      const e = await r.json().catch(() => ({}))
      throw new Error(e.detail || `Error ${r.status}`)
    }
    const data = await r.json()

    // Marcar como guardado
    const tarjeta = document.getElementById(`resultado-${idx}`)
    if (tarjeta) {
      tarjeta.style.opacity = '0.5'
      tarjeta.style.pointerEvents = 'none'
      tarjeta.querySelector('.ing-resultado__header')
        ?.insertAdjacentHTML('beforeend',
          '<span class="ing-saved-badge">✅ Guardado</span>')
    }
    showAlert(`✅ Logo guardado como: ${data.nombre_archivo}`, 'success', 6000)

  } catch(e) {
    showAlert('Error al guardar: ' + e.message, 'error')
    if (btn) { btn.disabled = false; btn.innerHTML = origText }
  }
}

window.descartarResultado = function(idx) {
  document.getElementById(`resultado-${idx}`)?.remove()
}

// ── Guardar todos ─────────────────────────────────────────────────────
function bindGuardarTodos() {
  document.getElementById('ing-guardar-todos-btn')?.addEventListener('click', async () => {
    const botones = document.querySelectorAll('.ing-resultado .btn--primary:not(:disabled)')
    for (const btn of botones) { btn.click(); await new Promise(r => setTimeout(r, 1000)) }
  })
}

// ── Helpers escape ────────────────────────────────────────────────────
function escH(s) {
  return escapeHtml(s)
}
function escA(s) {
  return escapeAttr(s)
}
