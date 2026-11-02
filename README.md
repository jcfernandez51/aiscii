


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
Crea un .env a partir de .env.example con los valores adecuados y despliega:
```bash
docker compose up -d
```
Por defecto la imagen construida sirve la aplicacion en el puerto 8080.

### Desplegar en Vercel (vercel cli)
Con Vercel CLI instalado inicia sesion y vincula el proyecto:
```bash
vercel login
vercel link
```
Añade las variables de entorno:
```bash
vercel env add AI_BASE_URL production
vercel env add AI_API_KEY production --sensitive
vercel env add AI_MODEL production
vercel env add CLERK_PUBLISHABLE_KEY production
vercel env add CLERK_SECRET_KEY production --sensitive
vercel env add CLERK_AUTHORIZED_PARTIES production
```
Compruebalas:
```bash
vercel env ls production
```
Despliega:
```bash
vercel --prod
```

### Desplegar en EC2 (aws-cli)