'use strict'

/**
 * categories.js — Categorización de servicios (fuente única de verdad).
 * Usado por services.js y report.js para que ambos módulos muestren
 * exactamente las mismas categorías y conteos.
 */

export const CATEGORIAS_ORDEN = [
  '🛡  Detección y Respuesta',
  '🔑  Gestión de Identidades y Accesos',
  '☁  Protección de Infraestructura',
  '⚖  Cumplimiento y Gobernanza',
  '🎓  Capacitación y Desarrollo Seguro',
]

export const KEYWORDS = {
  '🛡  Detección y Respuesta': [
    'incident','response','soc','monitoreo','vulnerability','pentest','penetration',
    'forensi','threat','detección','deteccion','respuesta','brecha','intrusion',
    'siem','edr','xdr','alerta','hunting','phishing','ransomware','tabletop','simulacro',
  ],
  '🔑  Gestión de Identidades y Accesos': [
    'iam','identidad','identity','acceso','access','mfa','autenticacion','autenticación',
    'privileged','pam','zero trust','parche','patch','contraseña','password',
    'directorio','ldap','sso',
  ],
  '☁  Protección de Infraestructura': [
    'cloud','nube','aws','azure','gcp','firewall','red','network','endpoint','backup',
    'recuperacion','recuperación','drp','infraestructura','servidor','server',
    'segmentacion','segmentación','vpn','email','correo','devsecops','ssdlc',
  ],
  '⚖  Cumplimiento y Gobernanza': [
    'cumplimiento','compliance','iso','normativa','ley','gdpr','gobernanza','governance',
    'audit','auditoria','auditoría','legal','regulatorio','certificacion','certificación',
    'política','politica','riesgo','risk','dpia','privacidad','vciso','sgsi','bcp',
    'continuidad','dpo','gap',
  ],
  '🎓  Capacitación y Desarrollo Seguro': [
    'capacitacion','capacitación','training','awareness','simulacion','simulación',
    'desarrollo','development','sast','dast','reporte','dashboard','kpi',
    'concientizacion','concientización','taller','conocimiento',
  ],
}

/**
 * Determina la categoría de un servicio según su nombre + descripción,
 * eligiendo la categoría cuyas keywords aparecen con mayor frecuencia.
 */
export function categorizar(nombre, desc) {
  const txt = ((nombre || '') + (desc || '')).toLowerCase()
  let best = CATEGORIAS_ORDEN[0], score = 0
  for (const [cat, kws] of Object.entries(KEYWORDS)) {
    const s = kws.reduce((a, k) => a + (txt.includes(k) ? 1 : 0), 0)
    if (s > score) { score = s; best = cat }
  }
  return best
}

/**
 * Agrupa una lista de servicios { name, description, ... } por categoría.
 * Retorna un objeto { [categoria]: Service[] } respetando CATEGORIAS_ORDEN.
 */
export function agrupar(servicios) {
  const g = {}
  for (const c of CATEGORIAS_ORDEN) g[c] = []
  for (const s of servicios) {
    const c = categorizar(s.name, s.description)
    g[c].push(s)
  }
  return g
}
