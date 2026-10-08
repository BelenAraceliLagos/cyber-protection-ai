-- restore_real_data.sql
-- Restaura los datos reales extraídos de bd_23_07.dump (BD anterior)
-- Generado automáticamente. Seguro de correr más de una vez (ON CONFLICT DO NOTHING).
BEGIN;

-- clients (10 filas)
INSERT INTO clients (id, company_name, contact_name, email, phone, industry, notes, rut, business_name, address, city, region, country, website, contact_position, contact_phone, lifecycle_stage, origen, created_at, lifecycle_auto) VALUES ('1', 'empresa S.A', 'Carlos', 'esdf@sdf.com', NULL, 'Construcción', NULL, NULL, NULL, NULL, NULL, NULL, 'Chile', NULL, NULL, NULL, 'cliente', 'referido', '2026-07-22 23:58:29.938636-04', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO clients (id, company_name, contact_name, email, phone, industry, notes, rut, business_name, address, city, region, country, website, contact_position, contact_phone, lifecycle_stage, origen, created_at, lifecycle_auto) VALUES ('2', 'Universidad Mayor', 'Juanita Perez', 'juanita@umayor.cl', '+56912344444', 'Educación', 'Cliente de prueba', '7.755.566-8', NULL, 'San Pio X 2422', 'Santiago', 'Metropolitana de Santiago', 'Chile', 'https://umayor.cl', 'Coordinadora', '988776655', 'cliente', 'referido', '2026-07-22 23:58:29.938636-04', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO clients (id, company_name, contact_name, email, phone, industry, notes, rut, business_name, address, city, region, country, website, contact_position, contact_phone, lifecycle_stage, origen, created_at, lifecycle_auto) VALUES ('3', 'XmartLab', 'gonzalo paredes', 'gonzalo@xmartlab.com', '990991292', 'Tecnología', NULL, '76.712.589-5', 'xmartlab limitada', 'huelen 10, oficina 2022', 'providencia', 'Metropolitana de Santiago', 'Chile', 'xmartlab.cl', 'CEO', NULL, 'cliente', 'referido', '2026-07-22 23:58:29.938636-04', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO clients (id, company_name, contact_name, email, phone, industry, notes, rut, business_name, address, city, region, country, website, contact_position, contact_phone, lifecycle_stage, origen, created_at, lifecycle_auto) VALUES ('4', 'Puerto Terrestre Los Andes', 'Juan pablo Garrido', 'jgarrido@ptla.cl', '+56966096300', 'Otro', NULL, '99.594.180-5', 'ouerto terrestre los andes sociedad concecionaria S.A.', NULL, NULL, 'Valparaíso', 'Chile', NULL, 'Gerente Ciberseguridad.', NULL, 'cliente', 'referido', '2026-07-22 23:58:29.938636-04', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO clients (id, company_name, contact_name, email, phone, industry, notes, rut, business_name, address, city, region, country, website, contact_position, contact_phone, lifecycle_stage, origen, created_at, lifecycle_auto) VALUES ('7', 'Viña Luis Felipe Edwards', 'Karina Martinez', 'kmartinez@atcom.cl', '977200008', 'Manufactura', NULL, '76.084.980-4', 'VIÑA LUIS FELIPE EDWARDS S.R.L', 'CANDELARIA GOYENECHEA 3900 DPTO. 403 STGO', 'VITACURA', 'Metropolitana de Santiago', 'Chile', 'https://www.lfewines.com/', 'KAM', NULL, 'cliente', 'email_marketing', '2026-07-22 23:58:29.938636-04', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO clients (id, company_name, contact_name, email, phone, industry, notes, rut, business_name, address, city, region, country, website, contact_position, contact_phone, lifecycle_stage, origen, created_at, lifecycle_auto) VALUES ('5', 'SERCOTEC', 'Christian Soza', 'christian@nltsecure.com', '9455146661', 'Gobierno', NULL, '82.174.900-K', 'Servicio de Cooperación Técnica', 'Huérfanos 1117, Piso 9', 'santiago', 'Metropolitana de Santiago', 'Chile', 'www.sercotec.cl', 'ARQUITECTO LIDER IT', NULL, 'oportunidad', 'busqueda_organica', '2026-07-22 23:58:29.938636-04', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO clients (id, company_name, contact_name, email, phone, industry, notes, rut, business_name, address, city, region, country, website, contact_position, contact_phone, lifecycle_stage, origen, created_at, lifecycle_auto) VALUES ('6', 'Clinica  Oftamologica ISV', 'Karina Martinez', 'kmartinez@atcom.cl', '977200008', 'Salud', NULL, '78.660.200-9', 'CLINICA OFTALMOLOGICA ISV LIMITADA', '4 NORTE 1330', 'VINA DEL MAR, VALPARAÍSO,', 'Valparaíso', 'Chile', 'xmartlab.cl', 'KAM', NULL, 'promotor', 'redes_sociales', '2026-07-22 23:58:29.938636-04', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO clients (id, company_name, contact_name, email, phone, industry, notes, rut, business_name, address, city, region, country, website, contact_position, contact_phone, lifecycle_stage, origen, created_at, lifecycle_auto) VALUES ('9', 'BNC Chile', 'Christian Soza', 'christian@nltsecure.com', '9455146661', NULL, NULL, '60.203.000-8', NULL, NULL, 'santiago', NULL, 'Chile', NULL, 'ARQUITECTO LIDER IT', NULL, 'oportunidad', 'evento', '2026-07-22 23:58:29.938636-04', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO clients (id, company_name, contact_name, email, phone, industry, notes, rut, business_name, address, city, region, country, website, contact_position, contact_phone, lifecycle_stage, origen, created_at, lifecycle_auto) VALUES ('10', 'mar del sur', 'Christian Soza', 'christian@nltsecure.com', '9455146661', 'Retail', NULL, '83.610.800-0', 'MAR DEL SUR SPA', NULL, 'santiago', 'Metropolitana de Santiago', 'Chile', NULL, 'ARQUITECTO LIDER IT', NULL, 'lead', 'evento', '2026-07-22 23:58:29.938636-04', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO clients (id, company_name, contact_name, email, phone, industry, notes, rut, business_name, address, city, region, country, website, contact_position, contact_phone, lifecycle_stage, origen, created_at, lifecycle_auto) VALUES ('8', 'Empresas Valmar', 'Cristian Silva', 'nicolas.gonzalez@nltsecure.com', '977200008', 'Construcción', NULL, '96.598.690-1', 'Inversiones Valmar Limitada', 'CANDELARIA GOYENECHEA 3900 DPTO. 403 STGO', 'talcahuano', 'Biobío', 'Chile', 'https://www.valmar.cl/', 'KAM', NULL, 'cliente', 'evento', '2026-07-22 23:58:29.938636-04', 't') ON CONFLICT (id) DO NOTHING;

-- companies (4 filas) — se omite created_at (no existe en el modelo actual)
INSERT INTO companies (id, name, logo_path, portada_path, interior_path, background_path, primary_color, secondary_color, content_color, portada_config, active, rut, direccion, telefono, notas_valores, formas_pago, modalidad_proyecto, modalidad_consultoria, banco, datos_bancarios) VALUES ('4', 'Atcom', NULL, 'C:\Users\kofra\OneDrive\Documentos\PRACTICA_CIBERPROTECTION\cyber-protection-ai-main\backend\assets\companies\company_4\base_portada.png', 'C:\Users\kofra\OneDrive\Documentos\PRACTICA_CIBERPROTECTION\cyber-protection-ai-main\backend\assets\companies\company_4\base_interior.png', NULL, '#ffffff', '#0a0046', '#ffffff', '{"banner": {"font": "segoe", "size": 26, "weight": 700, "y_start": 8, "bg_color": "#0a0046", "text_color": "#ffffff", "line_height": 1.1}, "cuerpo": {"font": "segoe", "size": 12, "color": "#1A2B5F", "weight": 400, "x_start": 46, "y_start": 16, "line_height": 1.5}, "titulo": {"x": 35, "y": 59, "font": "segoe", "size": 34, "align": "center", "color": "#ffffff", "width": 150, "weight": 700, "line_height": 1.15}, "objetivo": {"x": 40, "y": 105, "font": "segoe", "size": 11, "align": "left", "color": "#ffffff", "weight": 400, "line_height": 1.4}, "logo_cliente": {"x": 81, "y": 148, "width": 60, "height": 34}}'::json, 't', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL) ON CONFLICT (id) DO NOTHING;
INSERT INTO companies (id, name, logo_path, portada_path, interior_path, background_path, primary_color, secondary_color, content_color, portada_config, active, rut, direccion, telefono, notas_valores, formas_pago, modalidad_proyecto, modalidad_consultoria, banco, datos_bancarios) VALUES ('1', 'NTL Secure', 'string', 'C:\Users\kofra\OneDrive\Documentos\PRACTICA_CIBERPROTECTION\cyber-protection-ai-main\backend\assets\companies\company_1\base_portada.png', 'assets/companies/company_1/base_interior.png', 'string', '#000000', '#f9ab2b', '#000000', '{"banner": {"size": 26, "weight": 700, "y_start": 11, "bg_color": "#f9ab2b", "text_color": "#000000"}, "cuerpo": {"size": 10.5, "color": "#000000", "weight": 400, "x_start": 32, "y_start": 18}, "titulo": {"x": 20, "y": 125, "size": 24, "align": "left", "color": null, "width": 95, "weight": 700}, "objetivo": {"x": 20, "y": 161, "size": 15, "align": "left", "color": null, "width": 93, "weight": 400}, "logo_cliente": {"x": 150, "y": 217, "width": 40, "height": 27}}'::json, 't', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL) ON CONFLICT (id) DO NOTHING;
INSERT INTO companies (id, name, logo_path, portada_path, interior_path, background_path, primary_color, secondary_color, content_color, portada_config, active, rut, direccion, telefono, notas_valores, formas_pago, modalidad_proyecto, modalidad_consultoria, banco, datos_bancarios) VALUES ('3', 'Cyberlabs', NULL, 'C:\Users\kofra\OneDrive\Documentos\PRACTICA_CIBERPROTECTION\cyber-protection-ai-main\backend\assets\companies\company_3\base_portada.png', 'C:\Users\kofra\OneDrive\Documentos\PRACTICA_CIBERPROTECTION\cyber-protection-ai-main\backend\assets\companies\company_3\base_interior.png', NULL, '#ffffff', '#22c9c6', '#000000', '{"banner": {"font": "segoe", "size": 26, "weight": 700, "y_start": 3, "bg_color": "#22c9c6", "text_color": "#000000", "line_height": 1.1}, "cuerpo": {"font": "segoe", "size": 11, "color": "#012e00", "weight": 400, "x_start": 34, "y_start": 10, "line_height": 2.2}, "titulo": {"x": 31, "y": 52, "font": "questrial", "size": 39, "align": "center", "color": null, "width": 150, "weight": 700, "line_height": 1.15}, "objetivo": {"x": 31, "y": 103, "font": "times", "size": 16, "align": "center", "color": null, "weight": 400, "line_height": 2.2}, "logo_cliente": {"x": 81, "y": 204, "width": 60, "height": 34}}'::json, 't', '77777777-7', 'direccion de cyberlabs-777', '+56912345678', 'valor neto con iva', 'en oro', '99% inicial, 1% entregable', 'facturacion por dia', 'banco galaxia', 'cuenta n°1') ON CONFLICT (id) DO NOTHING;
INSERT INTO companies (id, name, logo_path, portada_path, interior_path, background_path, primary_color, secondary_color, content_color, portada_config, active, rut, direccion, telefono, notas_valores, formas_pago, modalidad_proyecto, modalidad_consultoria, banco, datos_bancarios) VALUES ('2', 'Cyber-Protection', 'assets/companies/company_2/logo.png', 'assets/companies/company_2/base_portada.png', 'assets/companies/company_2/base_interior.png', 'assets/companies/company_2/background.png', '#155FCF', '#8EE3C8', '#155FCF', '{"banner": {"size": 24, "weight": 700, "y_start": 24, "bg_color": "#8EE3C8", "text_color": "#155FCF"}, "cuerpo": {"size": 10.5, "color": "#155FCF", "weight": 400, "x_start": 37, "y_start": 32}, "titulo": {"x": 8, "y": 48, "size": 42, "align": "left", "color": null, "width": 120, "weight": 700}, "objetivo": {"x": 11, "y": 152, "size": 19, "align": "left", "color": null, "width": 100, "weight": 400}, "logo_cliente": {"x": 139, "y": 229, "width": 56, "height": 41}}'::json, 't', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL) ON CONFLICT (id) DO NOTHING;

-- services (48 filas)
INSERT INTO services (id, name, description, base_price, active) VALUES ('1', 'GAP Analysis ISO 27001 / 27002', 'Evaluación sistemática de brechas entre controles actuales y los 93 controles del Anexo A de ISO/IEC 27001:2022. Identifica nivel de madurez y prioridades de implementación. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('2', 'Gap Analysis Ley Marco Ciberseguridad (Ley 21.663)', 'Diagnóstico de cumplimiento frente a la Ley Marco 21.663 y requisitos de la ANCI. Evaluación de controles preventivos, detectivos y correctivos para OIVs y servicios esenciales. | Modalidad: Proyecto', '214.5', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('5', 'Evaluación CIS Controls v8', 'Auditoría de controles CIS (18 grupos) para determinar nivel de implementación y priorizar acciones de mejora. Incluye herramienta de evaluación CIS CAT. | Modalidad: Proyecto', '150', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('7', 'vCISO / Virtual CISO', 'Director de Seguridad de la Información (CISO) virtual. Gobernanza estratégica, plan director de ciberseguridad, gestión de riesgos, supervisión de proveedores, representación ante ANCI. Modalidad mensual recurrente. | Modalidad: Recurrente Mensual', '145.5', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('8', 'SGSI – Implementación Sistema de Gestión de Seguridad de la Información', 'Diseño, documentación e implementación completa de un SGSI: política marco, alcance, SoA, PTR, procedimientos, BCP, DRP. Incluye 4 fases (Plan-Do-Check-Act) con acompañamiento a certificación ISO 27001. | Modalidad: Proyecto', '261', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('10', 'Alineación Empresa a Ley Marco Ciberseguridad + vCISO', 'Servicio combinado: Assessment inicial de cumplimiento Ley 21.663 (3 meses / 20hh mensuales) + acompañamiento mensual vCISO. Incluye representación ante ANCI con poder de firma digital. | Modalidad: Recurrente Mensual', '595', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('16', 'Cumplimiento Ley Marco Ciberseguridad (Ley 21.663) – OIV', 'Acompañamiento integral para Operadores de Importancia Vital (OIV). Incluye diagnóstico, diseño del protocolo de reporte rápido (3 y 24 horas), taller de remediación ITGC, y gestión ante ANCI. | Modalidad: Proyecto', '540', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('6', 'Auditoría de Cumplimiento Integral (Assessment Ofensivo + Normativo)', 'Combina GAP Analysis normativo (Ley 21.663) con pruebas de Ethical Hacking para validar que las políticas declaradas sean efectivas ante un ataque real. Entrega mapa de riesgos cruzado. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('9', 'Plan Director de Ciberseguridad', 'Definición de la hoja de ruta estratégica de ciberseguridad alineada al negocio. Priorización de inversiones según riesgo real. Incluye gestión de Quick Wins y mejoras estructurales a mediano plazo. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('15', 'Ethical Hacking – Remediación de Gaps', 'Servicio de remediación basado en hallazgos de ethical hacking previo. Foco en gaps identificados, configuraciones críticas y validación de controles implementados. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('17', 'Cumplimiento Ley Protección de Datos Personales (Ley 21.719)', 'Hoja de ruta de adecuación a la nueva Ley 21.719 (Chile). RAT (Registro de Actividades de Tratamiento), políticas de implementación, cláusulas NDA y descriptor de cargo DPO. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('18', 'DPO – Delegado de Protección de Datos', 'Servicio de Delegado de Protección de Datos (DPO) externo. Supervisión del cumplimiento normativo en materia de datos personales, gestión del RAT, NDA y comunicaciones regulatorias. | Modalidad: Recurrente Mensual', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('19', 'Análisis Técnico-Legal PSE', 'Análisis legal-técnico para Proveedores de Servicios Esenciales (PSE). Revisión de obligaciones bajo Ley Marco, gestión de contratos de cadena de suministro y alineación con SLAs regulatorios. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('29', 'Programa de Concienciación y Cultura de Ciberseguridad', 'Programas de formación diseñados para preparar organizaciones frente a ciberamenazas. Charlas, talleres interactivos, plataformas de entrenamiento online. Mejora cultura de seguridad interna. | Modalidad: Recurrente', '45', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('30', 'Capacitación Ley Marco Ciberseguridad', 'Sesión formativa (2 horas) sobre alcance, obligaciones y sanciones de la Ley 21.663. Dirigida a directivos, ejecutivos y equipos TI. Entrega material de referencia. | Modalidad: Taller One-Shot', '45', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('32', 'Incident Response (IR) – Respuesta a Incidentes', 'Servicio de respuesta a incidentes de seguridad. Protocolos anti-exfiltración, contención, erradicación y recuperación. Incluye 7 horas de atención cronológica ante incidentes reales. | Modalidad: Servicio On-demand', '90', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('42', 'Ethical Hacking – Enfoque Caja Blanca (White Box)', 'El servicio de Ethical Hacking bajo la modalidad de Caja Blanca (White Box), también conocido como auditoría de código o auditoría integral, representa el nivel más exhaustivo de evaluación de seguridad. En este enfoque, el equipo de especialistas cuenta con acceso total y transparente a la información del objetivo, incluyendo el código fuente, diagramas de arquitectura, configuraciones de red, bases de datos y credenciales de todos los niveles de privilegio.

Esta modalidad elimina las restricciones de tiempo y visibilidad que tendría un atacante tradicional, permitiendo una inspección profunda y quirúrgica del diseño y la lógica interna de los sistemas. Es el enfoque ideal para aplicaciones críticas, infraestructuras complejas y entornos donde se requiere garantizar el máximo nivel de seguridad desde su núcleo.

2. Objetivos del Servicio
Garantizar la máxima cobertura: Evaluar el 100% de la superficie de ataque, incluyendo rutas ocultas, APIs internas y funciones administrativas que no son visibles desde el exterior.

Identificar vulnerabilidades de lógica y diseño: Detectar fallos arquitectónicos y errores en la lógica de negocio que las herramientas automatizadas o las pruebas de Caja Negra/Gris no pueden identificar.

Evaluar la calidad y seguridad del código fuente: Identificar malas prácticas de programación, uso de librerías obsoletas, credenciales "quemadas" (hardcoded) en el código y manejo inseguro de datos sensibles.

Acelerar la remediación: Proporcionar a los equipos de desarrollo la ubicación exacta (línea de código o configuración específica) donde reside la vulnerabilidad, optimizando los tiempos de corrección.

3. Metodologías y Estándares de Referencia
La auditoría se ejecuta bajo un marco metodológico riguroso, combinando estándares de pruebas de penetración con guías específicas de revisión de código fuente:

OWASP Top 10 y OWASP ASVS (Application Security Verification Standard): Además del Top 10, se incorpora el ASVS para establecer un nivel de confianza técnico estandarizado sobre la seguridad de las aplicaciones a nivel de código y arquitectura.

CWE/SANS Top 25 (Common Weakness Enumeration): Referencia fundamental para evaluar e identificar los errores de software más peligrosos y extendidos a nivel de programación.

PTES (Penetration Testing Execution Standard): Guía estructurada para la ejecución de la prueba técnica, adaptando la fase de inteligencia al análisis profundo de la documentación y el código provisto.

OSSTMM (Open Source Security Testing Methodology Manual): Estándar empleado para validar las medidas de seguridad físicas, lógicas y de comunicaciones con un enfoque cuantitativo.

4. Fases de Ejecución
El proceso de Caja Blanca integra técnicas de análisis estático y dinámico para una evaluación holística:

Revisión de Arquitectura y Modelado de Amenazas: Análisis detallado de los diagramas de red, flujos de datos y diseño del sistema para identificar posibles vectores de ataque desde el diseño (Security by Design).

Análisis Estático (SAST) y Revisión Manual de Código: Inspección del código fuente mediante herramientas avanzadas combinadas con el análisis humano experto para detectar fallos de seguridad (inyecciones, desbordamientos, criptografía débil).

Análisis Dinámico (DAST / IAST): Pruebas de seguridad sobre la aplicación o sistema en ejecución, interactuando con todos los niveles de privilegio (desde anónimo hasta administrador global).

Explotación de Vulnerabilidades: Validación empírica de los hallazgos identificados en el código y la arquitectura para confirmar su viabilidad e impacto real en el negocio.

Análisis de Hallazgos y Estrategia de Remediación: Correlación de vulnerabilidades estáticas y dinámicas para estructurar planes de corrección precisos a nivel de desarrollo e infraestructura.

5. Entregables
La documentación entregada está diseñada para alinear las necesidades del negocio con las operaciones de desarrollo (DevSecOps) e infraestructura:

Reporte Ejecutivo: Resumen directivo que expone el nivel de madurez de la seguridad del código/infraestructura, el riesgo residual y recomendaciones estratégicas para la mejora continua.

Reporte Técnico de Código y Vulnerabilidades: Documento exhaustivo que detalla cada hallazgo con su métrica de criticidad (CVSS). Incluye referencias exactas a las líneas de código afectadas, fragmentos del código vulnerable, evidencias de explotación (PoC) y fragmentos de código seguro (Secure Coding) recomendados para su solución directa.', '200', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('43', 'Ethical Hacking – Enfoque Caja Gris (Gray Box)', 'El servicio de Ethical Hacking bajo la modalidad de Caja Gris (Gray Box) está diseñado para simular un ataque realista desde la perspectiva de un usuario interno malintencionado o un atacante externo que ha logrado vulnerar el perímetro inicial y ha obtenido acceso parcial a la infraestructura o aplicaciones de la organización (por ejemplo, credenciales de usuario de bajo privilegio).

A diferencia de las pruebas de Caja Negra, en este enfoque el equipo de auditores recibe información parcial sobre la arquitectura del sistema y accesos de nivel estándar. Esto permite optimizar el tiempo de la auditoría, focalizando los esfuerzos en la identificación profunda de vulnerabilidades, la evaluación de la segregación de funciones, el escalamiento de privilegios y el movimiento lateral dentro de la red o aplicación.

2. Objetivos del Servicio
Evaluar el impacto real: Determinar el nivel de daño que podría causar un atacante con acceso limitado a los sistemas.

Validar la segregación de accesos: Comprobar la efectividad de los controles de autorización y autenticación.

Identificar vectores de escalamiento: Detectar configuraciones deficientes o vulnerabilidades que permitan a un usuario estándar adquirir privilegios administrativos.

Reducir falsos positivos: Al contar con contexto interno, se maximiza la precisión de los hallazgos reportados frente a una prueba a ciegas.

3. Metodologías y Estándares de Referencia
La ejecución de este servicio se rige estrictamente por las mejores prácticas y metodologías reconocidas internacionalmente en la industria de la ciberseguridad, garantizando un enfoque exhaustivo, medible y repetible:

OWASP Top 10 (Open Worldwide Application Security Project): Utilizado como estándar principal para la evaluación de aplicaciones web y APIs, asegurando la identificación de los riesgos críticos más actuales (inyecciones, fallos de autenticación, exposición de datos sensibles, etc.).

PTES (Penetration Testing Execution Standard): Define el marco de trabajo estructurado para las fases de la prueba, desde la fase de pre-acuerdo hasta la entrega de resultados y remediación.

OSSTMM (Open Source Security Testing Methodology Manual): Aplicado para cuantificar la seguridad operativa y asegurar una validación técnica rigurosa de las infraestructuras y controles de telecomunicaciones.

NIST SP 800-115: Guía técnica para la evaluación de la seguridad de la información, proporcionando directrices sobre la planificación y ejecución de las pruebas técnicas.

4. Fases de Ejecución
El proceso se estructura en fases definidas para garantizar una cobertura total sin afectar la continuidad operativa del negocio:

Inteligencia y Modelado de Amenazas: Revisión de la información parcial suministrada (arquitectura, roles, credenciales base) para diseñar vectores de ataque personalizados.

Análisis de Vulnerabilidades: Uso de herramientas automatizadas y técnicas manuales para identificar brechas de seguridad en las plataformas, sistemas operativos o aplicaciones expuestas al rol asumido.

Explotación (Exploitation): Verificación controlada de las vulnerabilidades descubiertas para descartar falsos positivos y confirmar el riesgo real.

Post-Explotación: Intentos controlados de escalamiento de privilegios (vertical y horizontal), exfiltración simulada de datos sensibles y evaluación de la capacidad de persistencia, simulando el comportamiento de una amenaza avanzada.

Análisis y Reporte: Consolidación de hallazgos, evaluación del riesgo (impacto vs. probabilidad) y desarrollo de estrategias de mitigación.

5. Entregables
Al finalizar la ejecución, se entregarán los siguientes documentos, diseñados para satisfacer tanto a las gerencias estratégicas como a los equipos técnicos:

Reporte Ejecutivo: Documento de alto nivel, libre de jerga técnica compleja, que expone el nivel de riesgo global, el impacto potencial para el negocio y un resumen de las recomendaciones estratégicas.

Reporte Técnico: Documento detallado que incluye la descripción exhaustiva de cada vulnerabilidad encontrada, la evidencia de la explotación (Pruebas de Concepto - PoC), la categorización del riesgo (basada en CVSS) y las instrucciones técnicas paso a paso para su remediación o mitigación.', '200', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('27', 'Plan de Recuperación ante Desastres (DRP/DRaaS)', 'Business Continuity y Disaster Recovery as a Service (BC/DRaaS). Diseño del DRP, definición de RTO/RPO, pruebas de restauración, procedimientos de activación. Solución integral para recuperación rápida. | Modalidad: Proyecto + Servicio', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('31', 'Talleres de Transferencia de Conocimiento (M365 / Cloud Security)', 'Dos sesiones prácticas orientadas a la administración y operación segura de M365 y Azure Entra ID. Transferencia de capacidades al equipo TI interno para auto-sustentabilidad operativa. | Modalidad: Taller', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('36', 'Auditoría de Infraestructura (Firewall, Red, Cloud)', 'Revisión técnica de configuraciones de seguridad perimetral (NG-Firewalls, SDWAN, ZTNA, WAF). Evaluación de redes, segmentación, acceso privilegiado y políticas de control de cambios. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('38', 'Email Security (Protección de Correo Electrónico)', 'Seguridad robusta para correos electrónicos: bloqueo de phishing, malware y spam. SPF/DKIM/DMARC, políticas anti-phishing, protección avanzada Exchange Online. Reducción de superficie de ataque. | Modalidad: Recurrente Mensual', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('39', 'SSDLC / DevSecOps', 'Integración de seguridad en el ciclo de vida del desarrollo de software (SSDLC). Revisión de código, análisis de vulnerabilidades en pipelines CI/CD, formación de desarrolladores en seguridad. | Modalidad: Proyecto / Recurrente', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('26', 'Plan de Continuidad de Negocio (BCP)', 'Diseño e implementación del Business Continuity Plan. Identificación de procesos críticos, análisis BIA, estrategias de continuidad, pruebas y mantenimiento. Alineado con ISO 22301. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('28', 'Inventario de Activos y Clasificación de Información', 'Levantamiento de inventario de endpoints, servidores y activos críticos. Clasificación de información por criticidad. Base para la gestión de riesgos y definición de alcance SGSI. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('48', 'Implementacion PAM  -  IT/OT', 'Servicio de Evaluación e Implementación de PAM para Entornos Convergentes IT/OT
Objetivo del Servicio:
Asegurar, controlar y auditar el acceso privilegiado a los activos críticos en infraestructuras donde convergen las redes corporativas (IT) y las redes de operación industrial (OT), mitigando el riesgo de movimiento lateral, accesos no autorizados de terceros y compromisos de credenciales, sin interrumpir la disponibilidad operativa.
Fase 1: Levantamiento Previo de Arquitectura IT/OT (Fase Crítica)
El éxito de PAM en OT depende de no romper los procesos industriales. Esta fase inicial establece la línea base técnica y operativa.
* Mapeo de Redes y Modelo Purdue: Análisis de la segmentación actual entre IT y OT. Identificación de la Zona Desmilitarizada Industrial (IDMZ) y validación de flujos de red.
* Descubrimiento de Activos y Cuentas (Discovery): Identificación de cuentas locales, de dominio, genéricas, hardcodeadas y de servicio en sistemas SCADA, HMI, PLC, estaciones de ingeniería y servidores de planta.
* Evaluación de Accesos de Terceros: Mapeo de cómo los proveedores (OEMs, mantenedores) ingresan actualmente a la red OT (VPNs directas, TeamViewer, etc.).
* Análisis de Restricciones Operativas: Identificación de sistemas legacy que no soportan agentes, políticas de rotación de contraseñas u otros controles estándar de IT.
Fase 2: Diseño de la Solución y Gobernanza (Nivel Cero Confianza)
* Diseño de Arquitectura Bastión/Jump Server: Definición de la infraestructura de intermediación de sesiones en la IDMZ para evitar conexiones directas desde IT o Internet hacia OT.
* Definición de Políticas de Acceso (Least Privilege): Creación de perfiles de acceso basados en roles (Ingeniero de Planta, Administrador de Red, Proveedor Externo).
* Estrategia de Bóveda (Vaulting) y Rotación: Diseño de políticas de custodia de credenciales. Excepción OT: Definición de cuentas estáticas donde la rotación automática genere riesgos de indisponibilidad en procesos críticos de control continuo.
Fase 3: Implementación Técnica y Despliegue Estructurado
* Despliegue del Vault y Aislamiento de Sesión: Implementación de la bóveda digital y los servidores de salto.
* Aplicación de MFA Contextual: Implementación de Autenticación Multifactor para ingresar al entorno PAM desde IT/Internet. (Nota: Generalmente se evita requerir MFA dentro de los niveles más bajos de OT -Niveles 1 y 2- para no retrasar respuestas a emergencias físicas).
* Integración Agentless: Configuración de conectividad hacia activos OT utilizando protocolos nativos (RDP, SSH, VNC) a través del portal PAM, eliminando la necesidad de instalar agentes en sistemas operativos obsoletos o no soportados.
Fase 4: Monitoreo, Auditoría y Transferencia
* Grabación de Sesiones: Activación de registro en video y keystrokes (donde aplique) de todas las sesiones privilegiadas hacia OT.
* Integración con SOC/SIEM: Envío de logs de acceso, elevación de privilegios y alertas de comportamiento anómalo al centro de operaciones.
Capacitación y Handover: Transferencia de conocimiento a los operadores de planta y administradores de ciberseguridad
Entregables Formales del Servicio
Al finalizar el proyecto de evaluación e implementación, el cliente recibirá el siguiente set documental, estructurado tanto para ingeniería como para auditoría gerencial:
Documento de Arquitectura y Topología IT/OT: Mapeo actualizado de las redes, destacando la ubicación estratégica de la bóveda de contraseñas y los proxies de sesión, respetando el Modelo Purdue.
Matriz de Accesos y Privilegios (Roles OT): Documento vivo que define los perfiles de acceso autorizados, excepciones aplicadas a sistemas legacy y flujos de aprobación requeridos para operaciones críticas.
Runbook de Operación y Administración PAM: Procedimientos estándar (SOPs) para la gestión diaria, incorporación de nuevas cuentas (onboarding), respuesta a alertas de salto de bóveda y procedimientos de "Romper el Cristal" (Break-Glass) para emergencias operativas en planta.
Dossier de Cumplimiento (NIST CSF 2.0 y ANCI): Un informe ejecutivo, listo para ser adjuntado a la documentación del Sistema de Gestión de Seguridad de la Información (SGSI), que cruza los controles implementados con los marcos regulatorios exigidos.', '600', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('49', 'evaluación integral de seguridad en sistemas de IA y agentes autónomos,', '📌 Objetivo del Servicio
Proporcionar una evaluación integral de seguridad en sistemas de IA y agentes autónomos, identificando vulnerabilidades críticas y proponiendo controles técnicos y organizativos para mitigar riesgos.

🛠️ Alcance Técnico
El servicio cubre los siguientes aspectos:

Uso de modelos LLM: Evaluación de riesgos de entrenamiento, inferencia y despliegue.

Prompt injection: Análisis de vectores de ataque y pruebas de manipulación de entradas.

Protección de datos en inferencia: Validación de mecanismos de anonimización y control de acceso.

Exfiltración de información: Pruebas de extracción de datos sensibles desde el modelo.

Model leakage / data leakage: Evaluación de riesgos de filtrado de parámetros y datasets.

Seguridad en pipelines MLOps: Revisión de CI/CD, control de versiones y seguridad de artefactos.

Control de decisiones autónomas: Validación de límites de autonomía y políticas de gobernanza.

Validación de outputs: Pruebas de consistencia, veracidad y detección de contenido tóxico.

Gestión de identidades y permisos: Auditoría de autenticación, autorización y trazabilidad.

📑 Metodología
Basada en el enfoque de OWASP AI Security Testing Guide:

Identificación de activos críticos: Modelos, datasets, pipelines, agentes.

Análisis de amenazas: Uso de STRIDE y MITRE ATLAS para IA.

Pruebas de seguridad específicas:

Inyección de prompts maliciosos.

Extracción de datos sensibles mediante queries adversarias.

Validación de outputs frente a políticas de seguridad.

Simulación de ataques en pipelines MLOps.

Evaluación de controles existentes: Cifrado, RBAC, auditoría, monitoreo.

Informe técnico: Riesgos priorizados, evidencias de pruebas y recomendaciones.

🧪 Casos de Prueba Concretos
Prompt Injection Test: Enviar instrucciones ocultas en inputs para verificar si el modelo las ejecuta.

Data Exfiltration Test: Intentar recuperar datos sensibles del entrenamiento mediante queries diseñadas.

Model Leakage Test: Evaluar si parámetros internos pueden ser inferidos por un atacante.

MLOps Pipeline Attack Simulation: Inyección de código en etapas de CI/CD para comprobar aislamiento.

Autonomous Agent Control Test: Forzar decisiones fuera de política definida y validar mecanismos de contención.

Output Validation Test: Generar respuestas con contenido tóxico o falso para verificar filtros.

📊 Entregables
Informe técnico con hallazgos y evidencias.

Matriz de riesgos priorizados (según impacto y probabilidad).

Recomendaciones de mitigación alineadas con OWASP.

Plan de mejora continua para seguridad en IA.', '600', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('50', 'Evaluación de Madurez NIST CSF 2.0', 'Levantamiento de madurez de controles de seguridad frente al framework NIST Cybersecurity Framework 2.0. Identifica brechas y genera hoja de ruta. | Modalidad: Proyecto', '114.5', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('51', 'Pentesting Web / Aplicaciones (PTaaS)', 'Detección de fallos en aplicaciones web y APIs orientadas al cliente. Modalidad PTaaS (Pentesting as a Service) para revisión continua. Cubre OWASP Top 10 y vulnerabilidades lógicas. | Modalidad: Proyecto / Recurrente', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('52', 'Simulación de Phishing y Ransomware', 'Ejercicios de ingeniería social automatizados basados en IA para evaluar respuesta organizacional. Campañas de phishing simulado, evaluación de conciencia y reporte de resultados por área. | Modalidad: Campaña Periódica', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('53', 'MDR – Managed Detection & Response (CyberSpectrum)', 'Servicio MDR con plataforma Security Data Lake 100% cloud. +1.200 algoritmos AI, SOAR con ML, inteligencia de amenazas, caza de amenazas (Threat Hunting). Listo para operar en días, no meses. | Modalidad: Recurrente Mensual', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('54', 'Ciberinteligencia y Prevención de Fraude (CyberSpectrum PROTECTION)', 'Monitoreo activo de datos sensibles en Surface, Deep y Dark Web. Inteligencia de amenazas en tiempo real, prevención de fraude digital y protección de marca. En alianza con Apura Cybercorp. | Modalidad: Recurrente Mensual', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('55', 'Gestión de Vulnerabilidades y Remediación', 'Identificación y remediación proactiva de vulnerabilidades antes que se conviertan en amenazas. Incluye escaneo periódico, clasificación por criticidad y plan de remediación priorizado. | Modalidad: Recurrente Mensual', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('56', 'Pentesting Externo / Interno', 'Pruebas de penetración controladas sobre infraestructura crítica y perímetros de red (externo e interno). Identifica vulnerabilidades explotables antes que actores maliciosos. Entrega informe de hallazgos y remediación. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('57', 'Auditoría de Firewalls, Switches y Redes', 'Revisión integral de configuraciones: firewalls NG, switches, controladores inalámbricos, telefonía IP. Identifica reglas excesivamente abiertas, falta de segmentación, trazabilidad. Entrega roadmap de compliance. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('58', 'Política de Hardening y Configuración Segura', 'Diseño e implementación de políticas de hardening para servidores, estaciones de trabajo y dispositivos de red. Basado en benchmarks CIS y estándares NIST. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('59', 'SOC as a Service / CyberSOC 24×7', 'Centro de Operaciones de Seguridad gestionado. Monitoreo 24/7 de servidores, redes, seguridad perimetral y nube. +60 expertos en guardia. Gestión automática de tickets y reportes mensuales. | Modalidad: Recurrente Mensual', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('60', 'NOC – Network Operations Center (CyberSpectrum CORE)', 'Monitoreo inteligente de infraestructura, administración remota y soporte 24/7. Análisis de comportamiento, gestión de firewalls, 2FA, protección email y endpoint. Atención multicanal con agente AI. | Modalidad: Recurrente Mensual', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('61', 'Consultoría de Diagnóstico Integral y AWS Assessment', 'El servicio de Consultoría de Diagnóstico Integral y AWS Assessment es una evaluación experta diseñada para analizar en profundidad el estado actual de plataformas digitales y modelos de crowdfunding. Su propósito es identificar oportunidades críticas de mejora técnica, operativa y de negocio, asegurando que la plataforma sea escalable, segura, rentable y esté alineada con las mejores prácticas de la industria.

El servicio no solo diagnostica los componentes tecnológicos (con especial foco en la infraestructura sobre AWS), sino que integra la visión del modelo operativo y la experiencia de los usuarios finales (emisores e inversionistas), facilitando el alineamiento de todas las áreas estratégicas de la organización.

2. Objetivos del Servicio
Objetivos Generales:
Realizar un diagnóstico de 360 grados de la plataforma para identificar brechas y oportunidades de mejora en:

Arquitectura tecnológica y uso eficiente de la nube (AWS).

Experiencia de Usuario (UX).

Seguridad de la información.

Escalabilidad de la plataforma.

Desempeño operativo.

Alineamiento normativo y con estándares de la industria.

Objetivos Específicos:

Análisis Multidimensional: Evaluar los aspectos tecnológicos, operativos y comerciales que impactan directamente en la rentabilidad y escalabilidad del producto.

Priorización Estratégica: Clasificar las iniciativas de mejora descubiertas en función de su impacto, esfuerzo, nivel de riesgo, urgencia y dependencias técnicas/operativas.

Planificación Táctica (Roadmap): Construir una hoja de ruta equilibrada que combine victorias tempranas (quick wins) de corto plazo con definiciones estructurales de mediano y largo plazo.

Plan de Trabajo Ejecutable: Definir un plan de acción detallado que asigne responsables, hitos, entregables y puntos de decisión clave.

Alineamiento Organizacional: Consolidar una agenda común de ejecución que integre las visiones de la Directiva, Tecnología, Producto, Operaciones y Negocio.

3. Alcance y Líneas de Trabajo
El assessment se abordará de manera integrada mediante tres líneas de trabajo principales:

Línea 1: Optimización de AWS y Arquitectura Tecnológica: Revisión profunda de la infraestructura cloud, identificando fugas de presupuesto (FinOps), cuellos de botella en la arquitectura, brechas de seguridad y validación de la capacidad de escalamiento bajo demanda.

Línea 2: Revisión del Modelo Operativo y Delivery: Análisis de los procesos internos que soportan la plataforma, metodologías de entrega de software, despliegue y desempeño operativo general.

Línea 3: Rediseño del Ciclo Comercial y UX: Evaluación del recorrido del cliente (Customer Journey) para los perfiles de inversionistas y emisores, proponiendo mejoras en la experiencia de usuario que faciliten la conversión y retención.

4. Propuesta Metodológica (Enfoque de Trabajo)
La consultoría se ejecutará bajo un marco de trabajo ágil y colaborativo, dividido en las siguientes fases:

Fase de Levantamiento (Discovery): Entrevistas con stakeholders clave (Directiva, TI, Producto, Negocio) y recopilación de documentación, arquitectura y flujos de usuario actuales.

Fase de Análisis y Evaluación (Assessment): Auditoría técnica de la infraestructura (AWS), revisión de código/arquitectura, análisis heurístico de UX y mapeo de procesos operativos.

Fase de Diagnóstico y Priorización: Consolidación de hallazgos, evaluación de riesgos e impacto, y construcción de la matriz de priorización.

Fase de Diseño de Hoja de Ruta: Elaboración del plan de trabajo ejecutable y alineamiento final con la mesa directiva para la transferencia de resultados.

5. Entregables Esperados
Al finalizar la consultoría, se hará entrega de:

Reporte de Diagnóstico Integral: Documento detallado con los hallazgos en Arquitectura, AWS, Seguridad, UX y Operaciones.

Matriz de Priorización de Iniciativas: Tablero de evaluación (Impacto vs. Esfuerzo/Riesgo) con las brechas identificadas.

Hoja de Ruta (Roadmap): Cronograma estratégico de iniciativas a corto (quick wins) y mediano plazo.

Plan de Trabajo Ejecutable: Documento táctico con responsables, hitos, y acciones correctivas recomendadas.

(Nota para la elaboración de tu propuesta: A continuación, debes completar las siguientes secciones con los datos específicos de tu empresa para cumplir al 100% con las bases de la licitación)', '1000', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('62', 'Evaluación y Alineamiento NERC CIP bajo el Estándar del Coordinador Eléctrico Nacional (CEN)', 'Este servicio está diseñado estrictamente para abordar los requerimientos indicados, centrándose en la evaluación, control y mejora de la ciberseguridad para 4 plantas fotovoltaicas de gran escala, garantizando el cumplimiento del Estándar de Ciberseguridad del Sector Eléctrico Nacional exigido por el CEN.

El diseño del servicio considera además que el cumplimiento de estos controles sectoriales pavimenta el camino para las futuras exigencias de infraestructura crítica bajo la Ley de Marco de Ciberseguridad (Ley 21.663) y las directrices de la Agencia Nacional de Ciberseguridad (ANCI).

Objetivo del Servicio
Ejecutar un assessment integral basado en los controles específicos de la norma NERC CIP requeridos, identificando brechas de cumplimiento, evaluando el nivel de madurez actual de los activos OT/IT de las 4 plantas fotovoltaicas y estableciendo un plan de remediación táctico y estratégico.

Estructura y Fases del Servicio
El servicio se divide en fases operativas alineadas directamente con los controles CIP solicitados:

Fase 1: Identificación y Categorización de Activos (CIP-002)
La base del estándar del CEN es comprender qué activos son críticos para la operación de las plantas fotovoltaicas.

Actividades:

Levantamiento e inventario de los Sistemas Cibernéticos (Sistemas de Control, SCADA, inversores, RTUs, etc.) en las 4 plantas.

Aplicación de la metodología de categorización (Impacto Alto, Medio, Bajo) según las directrices del CEN y CIP-002.

Definición clara del alcance y de las instalaciones afectadas por los controles posteriores.

Fase 2: Gobernanza y Protección de la Información (CIP-003 y CIP-011)
Revisión de los controles de gestión que sustentan la ciberseguridad operativa y la protección de datos sensibles.

Actividades CIP-003 (Gestión de Seguridad):

Revisión y/o diseño de políticas de seguridad aplicables a los sistemas de control de las plantas.

Evaluación de los controles de acceso físico y lógico de alto nivel.

Revisión de los planes de concienciación en ciberseguridad para el personal de planta.

Actividades CIP-011 (Protección de la Información):

Identificación de la Información del Sistema Cibernético (CSI) que requiere protección (ej. diagramas de red, configuraciones de inversores).

Evaluación de los procedimientos de almacenamiento, transmisión y destrucción segura de la información crítica.

Fase 3: Arquitectura, Perímetro y Fortalecimiento (CIP-005 y CIP-007)
Análisis técnico de la topología de red y las medidas de protección implementadas en los componentes individuales.

Actividades CIP-005 (Perímetros de Seguridad Electrónica):

Revisión de la segmentación de red entre los entornos corporativos (IT) y de operación de las plantas (OT).

Evaluación de los Puntos de Acceso Electrónico (EAP) y configuración de firewalls/equipos de borde.

Análisis de los controles de Acceso Remoto Interactivo (VPNs, MFA) para proveedores y operadores.

Actividades CIP-007 (Gestión de Seguridad de Sistemas):

Revisión del hardening (bastionado) de servidores, estaciones de ingeniería y HMI.

Evaluación de la gestión de parches de seguridad y actualizaciones de firmware en equipos de las 4 plantas.

Análisis de la gestión de puertos, servicios lógicos y control de código malicioso (antivirus/EDR en entornos compatibles).

Fase 4: Resiliencia, Respuesta y Recuperación (CIP-008 y CIP-009)
Preparación de las plantas fotovoltaicas para resistir y recuperarse ante un evento cibernético, minimizando el impacto en la generación.

Actividades CIP-008 (Respuesta a Incidentes):

Revisión de los Planes de Respuesta a Incidentes de Ciberseguridad (CSIRP) específicos para los entornos OT de las plantas.

Evaluación de los flujos de comunicación y notificación de incidentes (incluyendo reportes al CEN/CSIRT).

Actividades CIP-009 (Planes de Recuperación):

Análisis de los planes de contingencia y recuperación ante desastres (DRP) para sistemas críticos.

Evaluación de las estrategias y rutinas de respaldo (backups) de configuraciones de controladores, SCADA e históricos, comprobando pruebas de restauración.

Entregables del Servicio
Informe de Assessment y Brechas (Gap Analysis): Documento detallado que contrasta el estado actual de las 4 plantas fotovoltaicas contra los requisitos del Estándar de Ciberseguridad del CEN y los controles NERC CIP (002, 003, 005, 007, 008, 009, 011).

Inventario y Categorización de Activos: Matriz final de activos críticos visada y categorizada.

Matriz de Riesgos y Plan de Remediación (Roadmap): Plan de acción priorizado por nivel de riesgo y criticidad operativa, incluyendo recomendaciones tecnológicas y de procesos para cerrar las brechas identificadas.

Acompañamiento Estratégico Ejecutivo: Presentación de resultados orientada a la gerencia y a los responsables regulatorios, facilitando la toma de decisiones presupuestarias y de ingeniería.', '1000', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('63', 'Assessment de Seguridad M365 / Azure Entra ID', 'Evaluación integral de configuraciones en entornos Microsoft 365 y Azure Entra ID: MFA, PIM, RBAC, DLP, Exchange, SharePoint, Teams, OneDrive. Alineación con ISO 27001, NIST CSF y CIS Controls v8. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('64', 'Forense Digital (DFIR)', 'Digital Forensics and Incident Response. Análisis forense post-incidente, preservación de evidencia, cadena de custodia, reconstrucción de eventos. Equipo bilingüe con cobertura en 8 países. | Modalidad: Proyecto / On-demand', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('65', 'Tabletop Latinoamericano (Multi-país / Multi-sede)', 'Ejercicio tabletop de alcance regional para empresas con operaciones en múltiples países de Latinoamérica. Coordina respuesta entre sedes y evalúa comunicación inter-organizacional ante incidentes. | Modalidad: Taller One-Shot', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('66', 'Threat Intelligence y Threat Hunting', 'Búsqueda proactiva de amenazas en la infraestructura y fuentes de inteligencia pública/privada. Más de 700 integraciones y 1.200+ playbooks. Monitoreo en Dark Web para detección temprana. | Modalidad: Recurrente', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('67', 'Endpoint Protection (EDR/MDR/XDR/DLP)', 'Protección avanzada de dispositivos finales mediante tecnologías EDR, MDR, XDR y DLP. Prevención, detección y respuesta a amenazas en tiempo real. Administración remota incluida. | Modalidad: Recurrente Mensual', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('68', 'Ejercicio Tabletop de Ciberseguridad', 'Simulacro de crisis de ciberseguridad en formato taller de mesa. Evalúa protocolos de respuesta, comunicación y toma de decisiones del equipo directivo frente a escenarios de ataque realistas (ransomware, APT, etc.). | Modalidad: Taller One-Shot', '1003', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('69', 'Saneamiento de Identidades Post-Incidente', 'Reset forzado y auditoría de privilegios de cuentas comprometidas. Revisión de tokens de acceso residuales, análisis de persistencia del atacante y cierre de vectores de entrada identificados. | Modalidad: Proyecto', '100', 't') ON CONFLICT (id) DO NOTHING;
INSERT INTO services (id, name, description, base_price, active) VALUES ('70', 'Ethical Hacking – Enfoque Caja Negra (Black Box)', 'Mapear la superficie de ataque: Identificar activos digitales, subdominios, servicios expuestos y fugas de información (OSINT) que la organización podría desconocer que están públicos.

Evaluar la resiliencia del perímetro: Comprobar la eficacia de los controles de seguridad perimetrales (Firewalls, WAF, IPS/IDS) frente a ataques externos no autenticados.

Medir la capacidad de respuesta (Blue Team): Poner a prueba los sistemas de monitorización y la capacidad de alerta del equipo de seguridad o SOC interno ante un ataque sigiloso y progresivo.

Prevenir compromisos iniciales: Identificar vulnerabilidades críticas en la frontera de la red que sirvan como punto de entrada (Initial Access) para comprometer la red interna.

3. Metodologías y Estándares de Referencia
Para asegurar que la simulación de ataque sea exhaustiva, realista y controlada, el servicio se alinea con los siguientes estándares de la industria:

OWASP Top 10 (Open Worldwide Application Security Project): Empleado para la evaluación de aplicaciones web y APIs expuestas a internet, buscando brechas críticas que no requieran autenticación previa.

PTES (Penetration Testing Execution Standard): Proporciona la estructura base de la prueba, haciendo un énfasis particular en sus fases de recolección de información (OSINT) y modelado de amenazas externas.

OSSTMM (Open Source Security Testing Methodology Manual): Aplicado para evaluar de manera cuantitativa la seguridad física, humana (si se incluye ingeniería social) y de las telecomunicaciones expuestas.

NIST SP 800-115: Estándar técnico utilizado como guía para la ejecución sistemática de escaneos y pruebas de penetración sobre la infraestructura externa.

4. Fases de Ejecución
La metodología se desarrolla de manera progresiva, imitando la cadena de ataque o "Kill Chain" de un adversario real:

Reconocimiento e Inteligencia (OSINT): Búsqueda pasiva y activa de información pública sobre la organización, correos electrónicos corporativos expuestos, fugas de contraseñas previas y mapeo de la infraestructura tecnológica externa.

Escaneo y Enumeración: Interacción directa con los servidores y servicios expuestos para identificar puertos abiertos, versiones de software, topología de red pública y posibles puntos de entrada.

Análisis de Vulnerabilidades: Evaluación de los servicios descubiertos en busca de configuraciones por defecto, falta de parches, o vulnerabilidades conocidas (CVEs) y zero-days.

Explotación (Exploitation): Lanzamiento de ataques controlados para intentar quebrar las defensas perimetrales y obtener acceso no autorizado a los sistemas o datos expuestos.

Análisis y Reporte: Documentación del impacto de las vulnerabilidades explotadas, limpieza de rastros (si aplica) y generación de las recomendaciones preventivas y correctivas.

5. Entregables
La auditoría concluye con la entrega de documentación formal estructurada para facilitar la toma de decisiones gerenciales y la mitigación técnica inmediata:

Reporte Ejecutivo: Documento dirigido a la alta dirección que expone de forma clara la postura de seguridad externa, los riesgos para el negocio (riesgo reputacional, financiero u operativo) y un plan de acción estratégico.

Reporte Técnico: Detalle granular de cada vulnerabilidad identificada en el perímetro, evidencias de la explotación exitosa (Pruebas de Concepto - PoC), calificación de riesgo bajo el estándar CVSS y guías precisas para la remediación por parte de los equipos de TI y seguridad.', '90', 't') ON CONFLICT (id) DO NOTHING;

-- custom_fonts (1 fila)
INSERT INTO custom_fonts (id, name, css_key, regular_path, bold_path, created_at) VALUES ('1', 'questrial', 'questrial', 'C:\Users\kofra\OneDrive\Documentos\PRACTICA_CIBERPROTECTION\cyber-protection-ai-main\backend\assets\fonts\custom\questrial_regular.ttf', NULL, '2026-07-06 18:36:15.280366-04') ON CONFLICT (id) DO NOTHING;

-- opportunities (7 filas) — se omiten industria, pdf_path, service_ids_str, creado_en, actualizado_en (no existen en el modelo actual)
INSERT INTO opportunities (id, cliente_id, company_id, titulo, etapa, probabilidad, valor_uf, plazo_meses, notas, created_at, updated_at) VALUES ('4', '5', '1', 'Sercotec VCISO', 'prospecto', '50', '20', NULL, '', '2026-07-22 23:58:29.938636-04', '2026-07-23 00:48:16.737408-04') ON CONFLICT (id) DO NOTHING;
INSERT INTO opportunities (id, cliente_id, company_id, titulo, etapa, probabilidad, valor_uf, plazo_meses, notas, created_at, updated_at) VALUES ('7', '8', '1', 'Assessment de Ciberseguridad para Infraestructura con Agentes  de IA', 'prospecto', '50', '800', '12', '', '2026-07-22 23:58:29.938636-04', '2026-07-23 12:25:50.817279-04') ON CONFLICT (id) DO NOTHING;
INSERT INTO opportunities (id, cliente_id, company_id, titulo, etapa, probabilidad, valor_uf, plazo_meses, notas, created_at, updated_at) VALUES ('5', '7', '2', 'VIÑA LFE PAM VCISO', 'prospecto', '60', '100', '12', 'KAM KARINA', '2026-07-22 23:58:29.938636-04', '2026-07-23 12:25:52.137246-04') ON CONFLICT (id) DO NOTHING;
INSERT INTO opportunities (id, cliente_id, company_id, titulo, etapa, probabilidad, valor_uf, plazo_meses, notas, created_at, updated_at) VALUES ('6', '6', '4', 'Clinica  Oftamologica  ISV', 'prospecto', '100', '120', NULL, '', '2026-07-22 23:58:29.938636-04', '2026-07-23 12:25:53.766239-04') ON CONFLICT (id) DO NOTHING;
INSERT INTO opportunities (id, cliente_id, company_id, titulo, etapa, probabilidad, valor_uf, plazo_meses, notas, created_at, updated_at) VALUES ('3', '4', '2', 'ptla', 'prospecto', '30', '480', NULL, '', '2026-07-22 23:58:29.938636-04', '2026-07-23 12:25:54.378601-04') ON CONFLICT (id) DO NOTHING;
INSERT INTO opportunities (id, cliente_id, company_id, titulo, etapa, probabilidad, valor_uf, plazo_meses, notas, created_at, updated_at) VALUES ('2', '3', NULL, 'vciso ley marco AGFA', 'prospecto', '30', '60', NULL, '', '2026-07-22 23:58:29.938636-04', '2026-07-23 12:25:55.015791-04') ON CONFLICT (id) DO NOTHING;
INSERT INTO opportunities (id, cliente_id, company_id, titulo, etapa, probabilidad, valor_uf, plazo_meses, notas, created_at, updated_at) VALUES ('1', '1', '2', 'ethical salud', 'prospecto', '30', '200', NULL, '', '2026-07-22 23:58:29.938636-04', '2026-07-23 12:25:55.629367-04') ON CONFLICT (id) DO NOTHING;

-- Usuario admin (el dump anterior no traía ninguno, se crea manualmente)
-- Contraseña real: admin123.  (hash bcrypt generado con passlib, compatible con tu backend)
-- Se usa INSERT...WHERE NOT EXISTS en vez de ON CONFLICT porque no confirmamos
-- si la columna email tiene una restricción unique en el modelo actual.
INSERT INTO users (name, email, hashed_password, role)
SELECT 'Admin', 'admin@cyberprotection.cl', '$2b$12$DfN4UGU6qGeOhI7BuI80Muuy4x.gdgpF3Y.iZLf3HZC03DVaRRUp.', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@cyberprotection.cl');

-- Reiniciar secuencias de autoincremento
SELECT setval(pg_get_serial_sequence('clients', 'id'), COALESCE((SELECT MAX(id) FROM clients), 1));
SELECT setval(pg_get_serial_sequence('companies', 'id'), COALESCE((SELECT MAX(id) FROM companies), 1));
SELECT setval(pg_get_serial_sequence('services', 'id'), COALESCE((SELECT MAX(id) FROM services), 1));
SELECT setval(pg_get_serial_sequence('custom_fonts', 'id'), COALESCE((SELECT MAX(id) FROM custom_fonts), 1));
SELECT setval(pg_get_serial_sequence('opportunities', 'id'), COALESCE((SELECT MAX(id) FROM opportunities), 1));
SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1));

COMMIT;