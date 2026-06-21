'use strict'

import { BASE_URL } from './config.js'

function getToken() {
  return sessionStorage.getItem('cp_token')
}

function setToken(token) {
  sessionStorage.setItem('cp_token', token)
}

function removeToken() {
  sessionStorage.removeItem('cp_token')
}

async function request(method, endpoint, body = null) {
  const headers = { 'Content-Type': 'application/json' }

  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const config = { method, headers }
  if (body) config.body = JSON.stringify(body)

  let response

  try {
    response = await fetch(`${BASE_URL}${endpoint}`, config)
  } catch {
    throw new Error('No se pudo conectar con el servidor. Verifica tu conexión.')
  }

  if (response.status === 401) {
    removeToken()
    window.location.href = '/pages/login.html'
    return
  }

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || `Error ${response.status}`)
  }

  const text = await response.text()
  return text ? JSON.parse(text) : null
}

/* ── AUTH ── */
export const authAPI = {
  login(email, password) { return request('POST', '/auth/login', { email, password }) },
  getMe()                { return request('GET',  '/auth/me') },
  updateMe(data)         { return request('PUT',  '/auth/me', data) },
}

/* ── CLIENTS ── */
export const clientsAPI = {
  getAll()         { return request('GET',    '/clients') },
  create(data)     { return request('POST',   '/clients/', data) },
  update(id, data) { return request('PUT',    `/clients/${id}`, data) },
  delete(id)       { return request('DELETE', `/clients/${id}`) }
}

/* ── SERVICES ── */
export const servicesAPI = {
  getAll()         { return request('GET',    '/services/') },
  create(data)     { return request('POST',   '/services/', data) },
  update(id, data) { return request('PUT',    `/services/${id}`, data) },
  delete(id)       { return request('DELETE', `/services/${id}`) }
}

/* ── REPORT (Ollama) ── */
export const reportAPI = {
  generate(quoteId)        { return request('POST', '/reports/generate', { quote_id: quoteId }) },
  update(id, content)      { return request('PUT',  `/reports/${id}`, { content }) },
  exportPdf(id)            { return request('POST', `/reports/${id}/export`) }
}

/* ── USERS (admin) ── */
export const usersAPI = {
  getAll()         { return request('GET',    '/users') },
  create(data)     { return request('POST',   '/users/', data) },
  update(id, data) { return request('PUT',    `/users/${id}`, data) },
  delete(id)       { return request('DELETE', `/users/${id}`) }
}

/* ── IMPORT ── */
export const importAPI = {
  uploadFile(formData) {
    const token = getToken()
    return fetch(`${BASE_URL}/import/quotes`, {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      body: formData
    }).then(r => r.json())
  }
}

export { getToken, setToken, removeToken }

/* ── PROPOSALS ── */
export const proposalsAPI = {
  generate(data) {
    // Descarga directa del PDF
    const token = getToken()
    return fetch(`${BASE_URL}/proposals/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify(data)
    })
  },
  preview(clienteId, serviceIds) {
    return request('GET', `/proposals/preview/${clienteId}?service_ids=${serviceIds.join(',')}`)
  },
  getCompanies: async () => {

  const token = sessionStorage.getItem('cp_token')

  const res = await fetch(
    `${BASE_URL}/companies/`,
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  )

  if (!res.ok) {
    throw new Error(
      `Error companies ${res.status}`
    )
  }

  return res.json()
}
}
