import { createRoot } from 'react-dom/client'
import { ClerkProvider } from '@clerk/react'
import App from './App'
import './style.css'

const clavePublicable = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

createRoot(document.getElementById('root')!).render(
  clavePublicable ? (
    <ClerkProvider
      publishableKey={clavePublicable}
      afterSignOutUrl="/"
      signInFallbackRedirectUrl="/"
      signUpFallbackRedirectUrl="/"
      appearance={{
        variables: {
          colorPrimary: '#4ade80',
          colorBackground: '#262626',
          colorForeground: '#f5f5f5',
        },
      }}
    >
      <App />
    </ClerkProvider>
  ) : (
    <main className="mx-auto max-w-2xl px-5 py-12">
      <h1 className="font-mono text-4xl font-bold">aiscii</h1>
      <p role="alert" className="mt-4 text-red-400">El inicio de sesión no está configurado.</p>
    </main>
  ),
)
