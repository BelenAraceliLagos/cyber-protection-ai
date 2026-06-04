'use strict'

import { reportAPI, quotesAPI } from './api.js'
import { showAlert, showSpinner, hideSpinner, requireAuth } from './utils.js'

export async function initReport() {
  if (!requireAuth()) return

  await loadQuoteSelector()
  bindGenerateBtn()
  bindExportBtn()
}

async function loadQuoteSelector() {
  const select = document.getElementById('report-quote-select')
  if (!select) return

  try {
    const quotes = await quotesAPI.getAll()
    if (!quotes.length) {
      select.innerHTML = '<option value="">Sin cotizaciones disponibles</option>'
      return
    }
    select.innerHTML = `<option value="">Selecciona una cotización...</option>` +
      quotes.map(q => `<option value="${q.id}">${q.client_name} — ${q.title || 'Cotización #' + q.id}</option>`).join('')
  } catch (err) {
    showAlert('No se pudieron cargar las cotizaciones.', 'error')
  }
}

function bindGenerateBtn() {
  const btn     = document.getElementById('generate-btn')
  const select  = document.getElementById('report-quote-select')
  const spinner = document.getElementById('ollama-spinner')
  const result  = document.getElementById('report-result')
  const editor  = document.getElementById('report-editor')

  if (!btn) return

  btn.addEventListener('click', async () => {
    const quoteId = select?.value
    if (!quoteId) {
      showAlert('Selecciona una cotización primero.', 'warning')
      return
    }

    showSpinner(btn, 'Generando...')
    if (spinner) {
      spinner.style.display = 'flex'
      resetProgressBar()
    }
    if (result) result.style.display = 'none'

    try {
  const data = await reportAPI.generate(quoteId)

  if (spinner) spinner.style.display = 'none'
  if (result) result.style.display = 'block'

  if (editor) {
    editor.value = data.generated_text || ''
    editor.dataset.quoteId = quoteId
    editor.classList.add('page-enter')
  }

  showAlert(
    'Informe generado correctamente.',
    'success'
  )
    } catch (err) {
      if (spinner) spinner.style.display = 'none'
      showAlert(err.message || 'Error al generar el informe.', 'error')
    } finally {
      hideSpinner(btn)
    }
  })
}

function bindExportBtn() {
  const btn    = document.getElementById('export-btn')
  const editor = document.getElementById('report-editor')
  if (!btn) return

  btn.addEventListener('click', async () => {
    const reportId = editor?.dataset.reportId
    const content  = editor?.value

    if (!reportId) {
      showAlert('Primero genera un informe.', 'warning')
      return
    }

    showSpinner(btn, 'Exportando PDF...')

    try {
      await reportAPI.update(reportId, content)
      const data = await reportAPI.exportPdf(reportId)
      if (data?.url) window.open(data.url, '_blank')
      showAlert('PDF generado correctamente.', 'success')
    } catch (err) {
      showAlert(err.message || 'Error al exportar el PDF.', 'error')
    } finally {
      hideSpinner(btn)
    }
  })
}

function resetProgressBar() {
  const bar = document.getElementById('ollama-progress-bar')
  if (!bar) return
  bar.style.animation = 'none'
  bar.offsetHeight
  bar.style.animation = 'progressIndeterminate 28s linear forwards'
}
