


## Despliegue

### Ejecutar en local
En dos terminales ejecuta:
```bash
backend/.venv/bin/python -m uvicorn backend.main:app --env-file .env
```
```bash
cd frontend && npm run dev
``` 
Luego visita http://localhost:5173 para acceder a la aplicación.

### Ejecutar en local con Docker

### Desplegar en Vercel
Con Vercel CLI instalado inicia sesion y vincula el proyecto:
```bash
vercel login
vercel link
```
Añade las variables de entorno y compruebalas:
```bash
vercel env add AI_BASE_URL production
vercel env add AI_API_KEY production --sensitive
vercel env add AI_MODEL production
vercel env add CLERK_PUBLISHABLE_KEY production
vercel env add CLERK_SECRET_KEY production --sensitive
vercel env add CLERK_AUTHORIZED_PARTIES production

vercel env ls production
```
