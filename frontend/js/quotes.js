'use strict'

import {
  quotesAPI,
  clientsAPI,
  servicesAPI
} from './api.js'

import {
  showAlert,
  requireAuth
} from './utils.js'

let clients = []
let services = []

export async function initQuotes() {

  if (!requireAuth()) return

  await loadClients()
  await loadServices()
  await loadQuotes()

  bindForm()
}

async function loadClients() {

  const select = document.getElementById(
    'quote-client'
  )

  if (!select) return

  clients = await clientsAPI.getAll()

  select.innerHTML =
    '<option value="">Seleccione cliente</option>' +
    clients.map(client => `
      <option value="${client.id}">
        ${client.company_name}
      </option>
    `).join('')
}

async function loadServices() {

  const container = document.getElementById(
    'services-container'
  )

  if (!container) return

  services = await servicesAPI.getAll()

  container.innerHTML = services.map(service => `
    <label style="display:block;margin-bottom:10px">

      <input
        type="checkbox"
        class="service-check"
        value="${service.id}"
      >

      ${service.name}

      ($${service.base_price})

    </label>
  `).join('')
}

async function loadQuotes() {

  const tbody = document.querySelector(
    '#quotes-table tbody'
  )

  if (!tbody) return

  const quotes = await quotesAPI.getAll()

  tbody.innerHTML = quotes.map(q => {

    const client = clients.find(
      c => c.id === q.client_id
    )

    return `
      <tr>
        <td>${q.id}</td>

        <td>
          ${client
            ? client.company_name
            : 'Cliente eliminado'}
        </td>

        <td>$${q.total}</td>

        <td>${q.status}</td>

        <td>
          <button
            onclick="deleteQuote(${q.id})"
            class="btn btn--danger"
          >
            Eliminar
          </button>
        </td>
      </tr>
    `
  }).join('')
}

function bindForm() {

  const form = document.getElementById(
    'quote-form'
  )

  if (!form) return

  form.addEventListener(
    'submit',
    async (e) => {

      e.preventDefault()

      const clientId = Number(
        document.getElementById(
          'quote-client'
        ).value
      )

      const selectedServices = [
        ...document.querySelectorAll(
          '.service-check:checked'
        )
      ]

      if (
        !clientId ||
        selectedServices.length === 0
      ) {
        showAlert(
          'Seleccione cliente y al menos un servicio',
          'warning'
        )
        return
      }

      const items = selectedServices.map(
        checkbox => ({
          service_id: Number(
            checkbox.value
          ),
          quantity: 1
        })
      )

      try {

        await quotesAPI.create({
          client_id: clientId,
          items
        })

        showAlert(
          'Cotización creada',
          'success'
        )

        form.reset()

        await loadQuotes()

      } catch (err) {

        showAlert(
          err.message,
          'error'
        )

      }

    }
  )
}

window.deleteQuote = async function(id) {

  if (
    !confirm(
      '¿Eliminar esta cotización?'
    )
  ) return

  try {

    await quotesAPI.delete(id)

    showAlert(
      'Cotización eliminada',
      'success'
    )

    await loadQuotes()

  } catch (err) {

    showAlert(
      err.message,
      'error'
    )

  }
}