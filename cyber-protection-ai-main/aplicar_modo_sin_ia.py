"""
aplicar_modo_sin_ia.py  —  Modo sin IA + textos editables por servicio (D-11)

Uso (desde la carpeta cyber-protection-ai-main, donde están backend/ y frontend/):
    python aplicar_modo_sin_ia.py

- Es IDEMPOTENTE: si ya se aplicó, avisa y no duplica nada.
- Cada cambio verifica que el texto original exista EXACTAMENTE una vez;
  si tu archivo cambió y no coincide, se detiene sin tocar ese archivo.
- Guarda copia de cada archivo en ../_respaldo_parches/sin_ia/ (fuera del proyecto) antes de modificarlo.
"""
import shutil, sys
from pathlib import Path

RAIZ = Path.cwd()
errores = []
aplicados = 0
omitidos = 0


def parchar(ruta, cambios):
    """cambios: lista de (marca, viejo, nuevo). 'marca' es un texto que sólo
    existe si el cambio ya fue aplicado."""
    global aplicados, omitidos
    p = RAIZ / ruta
    if not p.exists():
        errores.append(f"{ruta}: no existe")
        return
    txt = p.read_text(encoding="utf-8")
    original = txt
    for marca, viejo, nuevo in cambios:
        if marca in txt:
            omitidos += 1
            continue
        n = txt.count(viejo)
        if n != 1:
            errores.append(f"{ruta}: se esperaba 1 coincidencia y hay {n} para: {viejo[:60]!r}")
            return  # no tocar este archivo
        txt = txt.replace(viejo, nuevo)
        aplicados += 1
    if txt != original:
        bak = RAIZ.parent / "_respaldo_parches" / "sin_ia" / ruta
        if not bak.exists():
            bak.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, bak)
        p.write_text(txt, encoding="utf-8")
        print(f"  ✔ {ruta}")


# ───────────────────────── BACKEND ─────────────────────────
parchar("backend/app/models/service.py", [(
    "texto_descripcion",
    "    modalidad = Column(String)\n",
    "    modalidad = Column(String)\n\n"
    "    # Textos editables para el informe (modo sin IA, D-11)\n"
    "    texto_descripcion = Column(Text)\n"
    "    texto_justificacion = Column(Text)\n"
    "    texto_beneficio = Column(Text)\n",
)])

parchar("backend/app/schemas/service.py", [(
    "texto_descripcion",
    "    modalidad: Optional[str] = None\n",
    "    modalidad: Optional[str] = None\n"
    "    texto_descripcion: Optional[str] = None\n"
    "    texto_justificacion: Optional[str] = None\n"
    "    texto_beneficio: Optional[str] = None\n",
)])

parchar("backend/app/routers/service.py", [
    ("TEXTOS_EDITABLES",
     "    db_service.modalidad = service.modalidad\n",
     "    db_service.modalidad = service.modalidad\n"
     "    # Los textos sólo se tocan si el cliente los envió (así un PUT parcial\n"
     "    # —por ejemplo activar/desactivar— no borra los textos guardados).\n"
     "    TEXTOS_EDITABLES = ('texto_descripcion', 'texto_justificacion', 'texto_beneficio')\n"
     "    for campo in TEXTOS_EDITABLES:\n"
     "        if campo in service.model_fields_set:\n"
     "            setattr(db_service, campo, getattr(service, campo))\n"),
    ("def proponer_textos",
     '@router.delete(\n    "/{service_id}"\n)',
     '''from pydantic import BaseModel as _BaseModel


class ProponerTextosRequest(_BaseModel):
    name: str
    description: str | None = None
    modalidad: str | None = None


@router.post("/generar-textos")
def proponer_textos(
    body: ProponerTextosRequest,
    current_user: User = Depends(require_admin)
):
    """Propone (NO guarda) los 3 textos del servicio usando IA local.
    La persona los revisa en el formulario y recién ahí los guarda."""
    from app.services.textos_servicio_ia import proponer_textos_servicio
    try:
        return proponer_textos_servicio(body.name, body.description or "", body.modalidad or "")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.delete(
    "/{service_id}"
)'''),
])

parchar("backend/app/routers/proposal.py", [
    ("OPCIONAL",
     "Ollama es OBLIGATORIO. Sin IA no se genera ningún documento.",
     "La IA local (Ollama) es OPCIONAL: por defecto se usa (usar_ia=True); con\n"
     "usar_ia=False el informe se arma con los textos guardados en cada servicio\n"
     "y plantillas fijas (modo sin IA, D-11)."),
    ("textos_sin_ia",
     "from app.services.generate_proposal import generar_propuesta\n",
     "from app.services.generate_proposal import generar_propuesta\n"
     "from app.services.textos_sin_ia import generar_textos_plantilla, construir_justificacion\n"),
    ("usar_ia: bool = True",
     "    company_id: Optional[int] = None\n",
     "    company_id: Optional[int] = None\n"
     "    usar_ia: bool = True   # False = modo sin IA (no requiere Ollama)\n"),
    ("descripcion_fija",
     '''        servicios_pdf.append({
            "nombre": s.name,
            "descripcion": s.description or "",
            "base_price": s.base_price,
        })''',
     '''        guardado = (getattr(s, "texto_descripcion", None) or "").strip()
        servicios_pdf.append({
            "nombre": s.name,
            "descripcion": guardado or s.description or "",
            # True = texto escrito/aprobado por una persona: la IA no lo reescribe
            "descripcion_fija": bool(guardado),
            "base_price": s.base_price,
        })'''),
    ("texto_beneficio",
     '"valor_agregado": valor,',
     '"valor_agregado": (getattr(s, "texto_beneficio", None) or "").strip() or valor,'),
    ("generar_textos_plantilla(",
     '''    try:
        textos = generar_textos_completos(
            empresa_cliente=cliente.company_name,
            empresa_emisora=company.name,
            industria=cliente.industry or "tecnología",
            servicios=[s.name for s in servicios],
            antecedente=request.antecedente or "",
            contacto=cliente.contact_name or ""
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama no disponible: {str(e)}. Inicia Ollama con 'ollama serve' antes de generar."
        )
''',
     '''    info_servicios = [
        {"nombre": s.name,
         "texto_justificacion": (getattr(s, "texto_justificacion", None) or "").strip()}
        for s in servicios
    ]
    if request.usar_ia:
        try:
            textos = generar_textos_completos(
                empresa_cliente=cliente.company_name,
                empresa_emisora=company.name,
                industria=cliente.industry or "tecnología",
                servicios=[s.name for s in servicios],
                antecedente=request.antecedente or "",
                contacto=cliente.contact_name or ""
            )
        except RuntimeError as e:
            # 503: el frontend ofrece continuar en modo sin IA
            raise HTTPException(
                status_code=503,
                detail=f"IA no disponible: {str(e)}. Puede generar el informe sin IA."
            )
    else:
        textos = generar_textos_plantilla(
            empresa_cliente=cliente.company_name,
            empresa_emisora=company.name,
            industria=cliente.industry or "tecnología",
            servicios=[s.name for s in servicios],
            antecedente=request.antecedente or "",
            contacto=cliente.contact_name or "",
            servicios_info=info_servicios,
        )

    # Si TODOS los servicios tienen justificación guardada, manda lo escrito por
    # la persona también en modo IA (en modo sin IA ya se aplicó arriba).
    if request.usar_ia and all(i["texto_justificacion"] for i in info_servicios):
        textos["justificacion_servicios"] = construir_justificacion(
            info_servicios, cliente.company_name, cliente.industry or "tecnología"
        )
'''),
    ("usar_ia=request.usar_ia",
     "generar_propuesta(data, output_path)\n",
     "generar_propuesta(data, output_path, usar_ia=request.usar_ia)\n"),
])

parchar("backend/app/services/generate_proposal.py", [(
    'not srv.get("descripcion_fija")',
    "if isinstance(desc, str) and len(desc.strip()) > 20:",
    'if isinstance(desc, str) and len(desc.strip()) > 20 and not srv.get("descripcion_fija"):',
)])

# ───────────────────────── FRONTEND ─────────────────────────
parchar("frontend/js/api.js", [(
    "proponerTextos",
    "  delete(id)       { return request('DELETE', `/services/${id}`) }\n}",
    "  delete(id)       { return request('DELETE', `/services/${id}`) },\n"
    "  proponerTextos(data) { return request('POST', '/services/generar-textos', data) }\n}",
)])

parchar("frontend/pages/services.html", [(
    'id="sf-texto-descripcion"',
    '''        <div class="form__group">
          <label for="sf-price">Precio base (UF)</label>''',
    '''        <fieldset class="form__group" style="border:1px solid var(--cp-border);border-radius:8px;padding:12px">
          <legend style="padding:0 6px;font-size:13px">Textos del informe (opcionales)</legend>
          <p style="font-size:12px;margin:0 0 8px;opacity:.8">
            Si los escribe aquí, el informe los usa tal cual (con o sin IA). Si los deja vacíos,
            el informe usa la IA (modo "Con IA") o una plantilla genérica (modo "Sin IA").
          </p>
          <label for="sf-texto-descripcion">Descripción para el informe</label>
          <textarea id="sf-texto-descripcion" rows="3" class="form__input"></textarea>
          <label for="sf-texto-justificacion" style="margin-top:8px;display:block">Justificación comercial</label>
          <textarea id="sf-texto-justificacion" rows="2" class="form__input"></textarea>
          <label for="sf-texto-beneficio" style="margin-top:8px;display:block">Beneficio estratégico (matriz de valor)</label>
          <textarea id="sf-texto-beneficio" rows="2" class="form__input"></textarea>
          <button type="button" class="btn btn--secondary" id="sf-generar-textos" style="margin-top:10px">
            <i class="ti ti-sparkles btn__icon" aria-hidden="true"></i>
            Generar con IA (propone, usted edita y guarda)
          </button>
        </fieldset>

        <div class="form__group">
          <label for="sf-price">Precio base (UF)</label>''',
)])

parchar("frontend/js/services.js", [
    ("texto_descripcion:",
     "      modalidad:   document.getElementById('sf-modalidad').value.trim() || null,\n",
     "      modalidad:   document.getElementById('sf-modalidad').value.trim() || null,\n"
     "      texto_descripcion:   document.getElementById('sf-texto-descripcion').value.trim() || null,\n"
     "      texto_justificacion: document.getElementById('sf-texto-justificacion').value.trim() || null,\n"
     "      texto_beneficio:     document.getElementById('sf-texto-beneficio').value.trim() || null,\n"),
    ("sf-texto-descripcion').value   =",
     "  document.getElementById('sf-modalidad').value   = s.modalidad || ''\n",
     "  document.getElementById('sf-modalidad').value   = s.modalidad || ''\n"
     "  document.getElementById('sf-texto-descripcion').value   = s.texto_descripcion || ''\n"
     "  document.getElementById('sf-texto-justificacion').value = s.texto_justificacion || ''\n"
     "  document.getElementById('sf-texto-beneficio').value     = s.texto_beneficio || ''\n"),
    ("function bindGenerarTextos",
     "function bindForm() {\n",
     '''function bindGenerarTextos() {
  const btn = document.getElementById('sf-generar-textos')
  if (!btn) return
  btn.addEventListener('click', async () => {
    const name = document.getElementById('sf-name').value.trim()
    if (!name) {
      showAlert('Escriba primero el nombre del servicio.', 'warning')
      return
    }
    const hayTexto = ['sf-texto-descripcion', 'sf-texto-justificacion', 'sf-texto-beneficio']
      .some(id => document.getElementById(id).value.trim())
    if (hayTexto && !confirm('Ya hay textos escritos. ¿Reemplazarlos por la propuesta de la IA?')) return

    showSpinner(btn, 'Generando...')
    try {
      const r = await servicesAPI.proponerTextos({
        name,
        description: document.getElementById('sf-description').value.trim() || null,
        modalidad:   document.getElementById('sf-modalidad').value.trim() || null,
      })
      document.getElementById('sf-texto-descripcion').value   = r.texto_descripcion || ''
      document.getElementById('sf-texto-justificacion').value = r.texto_justificacion || ''
      document.getElementById('sf-texto-beneficio').value     = r.texto_beneficio || ''
      showAlert('Propuesta lista: revísela, edítela y presione Guardar.', 'success')
    } catch (err) {
      showAlert('La IA no está disponible: ' + err.message + '. Puede escribir los textos a mano.', 'error')
    } finally {
      hideSpinner(btn)
    }
  })
}

function bindForm() {
  bindGenerarTextos()
'''),
])

parchar("frontend/pages/report.html", [(
    'id="r-sin-ia"',
    "      <!-- Progreso + Generar -->\n",
    '''      <!-- Modo de generación -->
      <div class="report-generate-row" style="margin-bottom:8px">
        <label style="display:flex;gap:8px;align-items:flex-start;font-size:14px;cursor:pointer">
          <input type="checkbox" id="r-sin-ia" style="margin-top:3px">
          <span>
            <strong>Generar sin IA</strong>
            <span style="display:block;font-size:12px;opacity:.8">
              Por defecto el informe usa IA (recomendado). Marque esta opción para usar los textos
              guardados en cada servicio y plantillas fijas: es inmediato y no requiere Ollama.
            </span>
          </span>
        </label>
      </div>

      <!-- Progreso + Generar -->
''',
)])

parchar("frontend/js/report.js", [
    ("usar_ia: usarIA,",
     "        usar_ia: true,\n",
     "        usar_ia: usarIA,\n"),
    ("iaNoDisponible",
     "        throw new Error(err.detail || `Error ${resp.status}`)\n",
     "        const e = new Error(err.detail || `Error ${resp.status}`)\n"
     "        if (resp.status === 503 && usarIA) e.iaNoDisponible = true\n"
     "        throw e\n"),
    ("ofrecer_sin_ia",
     "      const tiempoInfo = usarIA ? stopProgressTimer('Error') : { seconds: 0, text: '' }\n",
     "      const tiempoInfo = usarIA ? stopProgressTimer('Error') : { seconds: 0, text: '' }\n"
     "      if (err.iaNoDisponible) { // ofrecer_sin_ia\n"
     "        if (confirm('La IA no está disponible en este momento.\\n\\n¿Desea generar el informe SIN IA (con los textos guardados y plantillas)?')) {\n"
     "          if (sinIA) sinIA.checked = true\n"
     "          setTimeout(() => btn.click(), 0)\n"
     "        }\n"
     "        return\n"
     "      }\n"),
])

# ───────────────────── Archivos nuevos (ya vienen en el zip) ─────────────────────
for nuevo in ("backend/migrations/0007_textos_servicio.sql",
              "backend/app/services/textos_sin_ia.py",
              "backend/app/services/textos_servicio_ia.py"):
    if not (RAIZ / nuevo).exists():
        errores.append(f"{nuevo}: falta (copie el zip dentro de la carpeta del proyecto primero)")

print(f"\nCambios aplicados: {aplicados} · ya estaban: {omitidos}")
if errores:
    print("\n❌ PROBLEMAS (nada de esto se modificó):")
    for e in errores:
        print("  -", e)
    sys.exit(1)
print("✅ Listo. Siguiente: reinicie el backend (start_pcp.bat) y pruebe.")
