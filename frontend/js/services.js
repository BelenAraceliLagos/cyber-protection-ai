'use strict'

import { servicesAPI } from './api.js'
import {
  showAlert,
  requireAuth
} from './utils.js'

let allServices = []

export async function initServices() {
  if (!requireAuth()) return

  bindForm()
  await loadServices()
}

async function loadServices() {

  const tbody = document.querySelector(
    '#services-table tbody'
  )

  if (!tbody) return

  try {

    allServices = await servicesAPI.getAll()

    tbody.innerHTML = allServices.map(service => `
  <tr>
    <td>${service.id}</td>
    <td>${service.name}</td>
    <td>$${service.base_price}</td>
    <td>${service.active ? 'Activo' : 'Inactivo'}</td>
    <td>
      <button onclick="editService(${service.id})">
        Editar
      </button>

      <button onclick="deleteService(${service.id})">
        Eliminar
      </button>
    </td>
  </tr>
`).join('')

  } catch (err) {

    showAlert(
      err.message || 'Error cargando servicios',
      'error'
    )

  }
}

function bindForm() {

  const form = document.getElementById(
    'service-form'
  )

  if (!form) return

  form.addEventListener(
    'submit',
    async (e) => {

      e.preventDefault()

      const data = {
        name: document
          .getElementById('service-name')
          .value
          .trim(),

        description: document
          .getElementById('service-description')
          .value
          .trim(),

        base_price: Number(
          document
            .getElementById('service-price')
            .value
        )
      }

      try {

        await servicesAPI.create(data)

        showAlert(
          'Servicio creado correctamente',
          'success'
        )

        form.reset()

        await loadServices()

      } catch (err) {

        showAlert(
          err.message || 'Error creando servicio',
          'error'
        )

      }

    }
  )
}

window.deleteService = async function(id) {

  if (!confirm('¿Eliminar servicio?')) {
    return
  }

  try {

    await servicesAPI.delete(id)

    showAlert(
      'Servicio eliminado',
      'success'
    )

    await loadServices()

  } catch (err) {

    showAlert(
      err.message || 'Error eliminando servicio',
      'error'
    )

  }

}


window.editService = async function(id) {

  const service = allServices.find(
    s => s.id === id
  )

  if (!service) return

  const newName = prompt(
    'Nombre',
    service.name
  )

  if (!newName) return

  const newPrice = prompt(
    'Precio',
    service.base_price
  )

  if (!newPrice) return

  try {

    await servicesAPI.update(
      id,
      {
        name: newName,
        description: service.description,
        base_price: Number(newPrice)
      }
    )

    showAlert(
      'Servicio actualizado',
      'success'
    )

    await loadServices()

  } catch (err) {

    showAlert(
      err.message || 'Error actualizando servicio',
      'error'
    )

  }

}