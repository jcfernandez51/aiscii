import { useState } from 'react'
import type { FormEvent } from 'react'

const ideas = [
  'un pato',
  'un gato sentado',
  'un cohete',
  'una taza de café',
  'un velero',
  'un castillo',
  'una mariposa',
  'un robot simpático',
  'una montaña con un sol',
  'un cactus',
  'una bicicleta',
  'un pez',
]

export default function App() {
  const [descripcion, setDescripcion] = useState('')
  const [dibujo, setDibujo] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  async function generar(texto: string) {
    if (cargando) return
    if (!texto.trim() || texto.length > 200) {
      setError('Escribe una descripción de entre 1 y 200 caracteres.')
      return
    }

    setCargando(true)
    setError('')
    setDibujo('')

    try {
      const respuesta = await fetch('/api/generar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ descripcion: texto.trim() }),
        signal: AbortSignal.timeout(35000),
      })

      let datos
      try {
        datos = await respuesta.json()
      } catch {
        throw new Error('El servidor ha devuelto una respuesta inválida.')
      }

      if (!respuesta.ok) {
        throw new Error(
          typeof datos?.detail === 'string'
            ? datos.detail
            : 'No se ha podido generar el dibujo. Inténtalo de nuevo.',
        )
      }
      if (typeof datos?.ascii !== 'string' || !datos.ascii.trim()) {
        throw new Error('La respuesta recibida no contiene un dibujo válido.')
      }
      setDibujo(datos.ascii)
    } catch (fallo) {
      if (fallo instanceof DOMException) {
        setError('La petición ha tardado demasiado. Inténtalo de nuevo.')
      } else if (fallo instanceof TypeError) {
        setError('No se puede conectar con el servidor. Inténtalo de nuevo.')
      } else {
        setError(fallo instanceof Error ? fallo.message : 'No se ha podido generar el dibujo.')
      }
    } finally {
      setCargando(false)
    }
  }

  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    void generar(descripcion)
  }

  function probarSuerte() {
    const idea = ideas[Math.floor(Math.random() * ideas.length)]
    setDescripcion(idea)
    void generar(idea)
  }

  return (
    <main className="mx-auto max-w-2xl px-5 py-12 sm:py-20">
      <header className="mb-8">
        <h1 className="font-mono text-4xl font-bold tracking-tight">aiscii</h1>
        <p className="mt-2 text-slate-600">Describe una idea y conviértela en arte ASCII.</p>
      </header>

      <form onSubmit={enviar}>
        <label htmlFor="descripcion" className="mb-2 block font-medium">
          ¿Qué quieres dibujar?
        </label>
        <textarea
          id="descripcion"
          name="descripcion"
          value={descripcion}
          onChange={(evento) => setDescripcion(evento.target.value)}
          maxLength={200}
          required
          rows={3}
          disabled={cargando}
          aria-describedby="contador"
          placeholder="Por ejemplo: un pato nadando"
          className="block w-full resize-y rounded-lg border border-slate-300 bg-white p-3 outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-700/20 disabled:opacity-60"
        />
        <p id="contador" className="mt-1 text-right text-sm text-slate-500">
          {descripcion.length}/200
        </p>

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={cargando || !descripcion.trim()}
            className="rounded-lg bg-teal-800 px-5 py-2.5 font-medium text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Generar
          </button>
          <button
            type="button"
            onClick={probarSuerte}
            disabled={cargando}
            className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Voy a tener suerte
          </button>
        </div>
      </form>

      {error && <p role="alert" className="mt-5 text-red-700">{error}</p>}

      <section aria-labelledby="resultado" aria-busy={cargando} className="mt-8">
        <h2 id="resultado" className="mb-3 font-medium">Tu dibujo</h2>
        <div aria-live="polite" className="min-h-48 rounded-lg border border-slate-200 bg-white p-5">
          {cargando ? (
            <p role="status" className="text-slate-500">Generando dibujo…</p>
          ) : dibujo ? (
            <pre className="overflow-x-auto whitespace-pre font-mono text-sm leading-5">{dibujo}</pre>
          ) : (
            <p className="text-slate-500">Tu dibujo aparecerá aquí.</p>
          )}
        </div>
      </section>
    </main>
  )
}
