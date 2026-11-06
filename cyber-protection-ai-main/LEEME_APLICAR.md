# Paquete: modo sin IA + funcionamiento sin Internet

Todo se aplica desde la carpeta `cyber-protection-ai-main` (donde están `backend/` y `frontend/`).

## Antes de empezar
1. Haga `git add .` / `git commit` / `git push` de lo que ya tiene pendiente (así puede volver atrás con git si algo falla).
2. Cierre el backend (cierre todas las ventanas de `start_pcp.bat`).

## Pasos
1. Descomprima este zip **dentro** de `cyber-protection-ai-main` (aceptar "combinar carpetas").
   Aparecen archivos nuevos (migración 0007, `textos_sin_ia.py`, `textos_servicio_ia.py`, `frontend/assets/vendor/`) y los dos scripts `.py`.
2. `python aplicar_modo_sin_ia.py`  → debe terminar con ✅
3. `python aplicar_offline.py`      → debe terminar con ✅ (o con una lista de referencias externas que me muestra)
4. Inicie `start_pcp.bat` (aplica la migración 0007 sola en el paso 3 del script).
5. En el navegador: Ctrl+F5 en cada página.
6. Borre los dos scripts `.py` de la carpeta cuando termine (no son parte del sistema). Los respaldos quedaron en `../_respaldo_parches/`.

## Qué probar (5 minutos)
- Servicios → editar uno → bloque "Textos del informe": escribir a mano y Guardar; recargar y verificar que quedó.
- Mismo bloque → "Generar con IA" (con Ollama corriendo) → propone textos → editar → Guardar.
- Generar informe → marcar **"Generar sin IA"** → debe bajar el PDF en segundos, usando el texto guardado.
- Generar informe sin marcar nada (con IA) → igual que antes.
- Con Ollama apagado y SIN marcar: debe preguntar "¿generar sin IA?" en vez de mostrar error.
- Sin Internet: desconecte el WiFi, Ctrl+F5: la letra y los íconos deben verse igual.
