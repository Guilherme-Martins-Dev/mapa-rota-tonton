import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { IdiomaProvedor } from './i18n/Provedor'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <IdiomaProvedor>
      <App />
    </IdiomaProvedor>
  </StrictMode>,
)
