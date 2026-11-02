# aiscii

Miniaplicación de generación de arte ASCII con IA para la práctica UD1 de
Explotación de Servicios de Procesamiento y Analítica de Datos.

**Estado:** backend implementado y tests simulados comprobados en la VM; pendiente
de una prueba real con GoModel. Este README es provisional y se actualizará con los
comandos y resultados comprobados en cada hito. Integrantes y aportaciones:
pendientes de identificar.

## Alcance

Una pantalla con un formulario: el usuario describe un objeto o una escena
sencilla, pulsa «Generar» y recibe un dibujo ASCII. El resultado se mostrará con
fuente monoespaciada, conservando espacios y saltos de línea.

La aplicación tendrá validación de entrada, indicador de carga y mensajes de
error comprensibles. No tendrá base de datos, historial ni funciones adicionales.

## Arquitectura prevista

- Frontend: React, TypeScript y Tailwind CSS, con Vite para desarrollo y compilación.
- Backend: Python con FastAPI. Recibe la descripción, consulta una API externa de
  IA y devuelve el dibujo en JSON. El proveedor será GoModel, mediante un endpoint
  compatible con OpenAI Chat Completions; el modelo se configura por variable de entorno.
- Autenticación: Clerk, con validación del token en el backend desde el hito de autenticación.
- Vercel: frontend y backend serverless dentro de un único proyecto.
- AWS EC2: una imagen y un contenedor Docker con el frontend compilado y FastAPI.

Contrato previsto de la operación principal:

```text
POST /api/generar
Entrada: {"descripcion": "un gato sentado"}
Salida:  {"ascii": "...dibujo con saltos de línea..."}
```

Se añadirá `GET /api/health` para comprobar que el backend responde.
La clave del proveedor de IA permanecerá en el servidor.

## Entorno de trabajo y pruebas

Los archivos se preparan en este repositorio. La ejecución y las pruebas de
desarrollo se harán en la VM `espad`, accesible mediante dos saltos SSH:

```text
Equipo de trabajo → port12 (portátil) → espad (VM)
```

Acceso comprobado el 02/11/2026 con el usuario `jcfdzz`. Herramientas detectadas
en la VM: Python 3.13.5, Node.js 20.19.2, npm, Git y Docker. La instalación de
dependencias del backend está comprobada. La ejecución de Docker todavía no se ha verificado.

## Backend: estructura y ejecución en la VM

Todo lo específico del backend se encuentra en `backend/`:

```text
backend/
├── __init__.py
├── main.py                 # Endpoints y validación de entrada
├── gen.py                  # Petición a GoModel y tratamiento de errores
├── requirements.txt        # Dependencias de ejecución
├── requirements-dev.txt    # Dependencias para tests
└── tests/
    └── test_backend.py     # Proveedor simulado, sin consumo de API
```

La configuración común del proyecto se encuentra en `.env.example`, en la raíz.
En la VM se crean también `backend/.venv/` y `.env` (en la raíz), excluidos de Git.
Los comandos siguientes se ejecutan en `espad`, desde `~/aiscii`.

### Instalación

Acceder desde el equipo que tiene configurado el alias `port12`:

```bash
ssh port12
ssh espad
cd ~/aiscii
```

Crear un entorno virtual aislado e instalar las dependencias, incluidos los tests:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
```

Versiones directas utilizadas: FastAPI 0.162.0, Uvicorn 0.54.0, HTTPX 0.28.1,
python-dotenv 1.2.4 y pytest 9.2.0, con Python 3.13.5.

### Variables de entorno

| Variable | Finalidad | Carácter | Lugar y momento de uso |
| --- | --- | --- | --- |
| `AI_BASE_URL` | URL base de GoModel, con `/v1` si procede y sin `/chat/completions` | Configuración de servidor | Backend, ejecución |
| `AI_API_KEY` | Clave de acceso a GoModel | Secreto | Backend, ejecución |
| `AI_MODEL` | Identificador del modelo disponible en GoModel | Configuración de servidor | Backend, ejecución |

Crear el archivo privado y editarlo directamente en la VM, sin escribir claves
en comandos ni publicarlas en capturas:

```bash
cp -n .env.example .env
chmod 600 .env
nano .env
```

El backend añade `/chat/completions` a `AI_BASE_URL` y envía la clave en la
cabecera `Authorization: Bearer ...`. Usa `model`, `messages` y `max_tokens`
siguiendo el formato de [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).
La compatibilidad concreta del modelo con GoModel queda pendiente de la prueba real.

### Arranque

```bash
backend/.venv/bin/python -m uvicorn backend.main:app --env-file .env --host 127.0.0.1 --port 8000
```

Uvicorn es el servidor que ejecuta FastAPI. `--env-file` carga las variables
privadas en el proceso. Este comando escucha solo dentro de la VM. Se detiene
con `Ctrl+C`. Desde otra terminal en la misma VM:

```bash
curl -sS http://127.0.0.1:8000/api/health
curl -sS http://127.0.0.1:8000/api/generar \
  -H 'Content-Type: application/json' \
  -d '{"descripcion":"un gato sentado"}'
```

La primera petición devuelve `{"status":"ok"}`. La segunda consume la API real
si las variables están configuradas. La respuesta JSON conserva el dibujo en
el campo `ascii`; sus saltos de línea aparecen escapados como `\n`.

### Validación y errores

Se acepta una descripción de 1 a 500 caracteres después de quitar espacios
exteriores. La petición al proveedor tiene un timeout de 30 segundos y solicita
un máximo de 1500 tokens de salida. El prompt pide un dibujo pequeño de hasta
60 columnas y 25 líneas; estas dimensiones son una indicación al modelo.
Se rechazan respuestas vacías, mayores de 8000 caracteres o con caracteres
distintos de ASCII imprimible y saltos de línea.

| HTTP | Significado |
| --- | --- |
| 422 | Entrada inválida; no se consulta al proveedor |
| 503 | Falta alguna variable de configuración |
| 502 | Error del proveedor o respuesta inválida |
| 504 | Tiempo de espera agotado |

No se devuelven al usuario los mensajes internos ni el cuerpo del error de
GoModel. Clerk se incorporará en su hito; esta versión todavía no tiene autenticación.

### Tests y comprobaciones

```bash
backend/.venv/bin/python -m pytest backend/tests -q
```

Ejecutado en `espad` el 02/11/2026: **7 passed**, sin warnings. Hay tres
escenarios con variantes: petición válida, entrada inválida y errores del
proveedor (HTTP, timeout y formato). Las llamadas HTTP al proveedor se simulan;
no se necesitan credenciales ni se consume cuota real.

También se ha arrancado Uvicorn temporalmente en la VM: salud `200`, entrada
inválida `422` y configuración ausente `503`. El proceso de comprobación se
detuvo al terminar.

La petición válida comprueba también URL, cabecera de autenticación, modelo,
descripción y conservación de espacios del dibujo. La entrada inválida comprueba
que no se llama al proveedor. En los errores se verifica que no se filtran sus detalles.

Pendiente para cerrar `v0.1-backend`: configurar GoModel y comprobar una
generación real. No se ha creado ni publicado el tag.

## Hitos y versiones

Cada tag se creará al comprobar el hito y apuntará al commit correspondiente.
Después se publicará en GitHub junto con los commits. Esta tabla es un plan;
no acredita que los tags o despliegues existan.

| Fase | Comprobación de cierre | Tag previsto |
| --- | --- | --- |
| 0. Preparación | Alcance, proveedor, configuración inicial y plan de documentación | `v0.0-preparacion` |
| 1. Backend | Tests con proveedor simulado y petición real controlada en la VM | `v0.1-backend` |
| 2. Frontend | Formulario conectado y flujo completo probado en la VM | `v0.2-frontend` |
| 3. Vercel | SPA y API funcionando en un proyecto, con operaciones reales de CLI | `v0.3-vercel` |
| 4. Clerk | Sesión válida, cierre de sesión y rechazo de petición sin token en Vercel | `v0.4-auth` |
| 5. Docker | Un contenedor completo probado en la VM, incluida autenticación | `v0.5-docker` |
| 6. AWS | EC2 verificada desde fuera, operación y documentación final completas | `v1.0-aws` |

## Plan de documentación

El destinatario es el profesorado o cualquier compañero que necesite reproducir
y comprobar el despliegue. Se toma como referencia [Diátaxis](https://diataxis.fr/)
para organizar las instrucciones, la referencia de configuración y las
explicaciones dentro de este único README.

Al cerrar cada hito, los integrantes actualizarán los comandos realmente
ejecutados, su entorno, el resultado y los problemas encontrados. El reparto
individual se indicará cuando se identifiquen los integrantes.

El README final incluirá instalación, versiones, tabla de variables públicas y
privadas con su momento de uso, Vercel CLI, Clerk, Docker, EC2, tests, logs,
reinicio, actualización y retirada de recursos. Se recogerán evidencias en
`evidencias/` y se enlazarán aquí explicando qué demuestra cada una.

Se utilizarán Markdown y su vista previa, tablas, enlaces relativos, capturas
revisadas para ocultar secretos y Git para mantener la documentación.
Solo se documentarán comprobaciones realizadas; no se publicarán claves,
tokens, archivos `.env` privados ni credenciales AWS.
