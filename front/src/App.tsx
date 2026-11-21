import { BrowserRouter, Link, NavLink, Route, Routes } from 'react-router-dom'
import { ConteudoOculto } from './components/ConteudoOculto'
import { useIdioma, useT } from './i18n/useIdioma'
import Construcao from './pages/Construcao'
import Explorar from './pages/Explorar'
import Home from './pages/Home'
import Metodo from './pages/Metodo'
import { alternarTema, useTema } from './theme/tema'

/** Alterna claro/escuro: um carro derrapa pela tela e as marcas dos pneus revelam o tema novo. O ícone mostra o tema para onde se vai. */
function BotaoTema() {
  const t = useT()
  const tema = useTema()
  const rotulo = tema === 'dark' ? t('temaParaClaro') : t('temaParaEscuro')
  return (
    <button type="button" className="barra__botao" aria-label={rotulo} title={rotulo} onClick={() => void alternarTema()}>
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
        {tema === 'dark' ? (
          <>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
          </>
        ) : (
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        )}
      </svg>
    </button>
  )
}

/** Alterna português/inglês. O rótulo acessível diz a ação, na língua de destino. */
function BotaoIdioma() {
  const t = useT()
  const { idioma, setIdioma } = useIdioma()
  return (
    <button
      type="button"
      className="barra__botao barra__botao--texto"
      lang={idioma === 'pt' ? 'en' : 'pt'}
      aria-label={t('idiomaTroca')}
      title={t('idiomaTroca')}
      onClick={() => setIdioma(idioma === 'pt' ? 'en' : 'pt')}
    >
      {t('idiomaSigla')}
    </button>
  )
}

export default function App() {
  const t = useT()
  return (
    <BrowserRouter>
      <header className="barra">
        <Link to="/" className="marca" aria-label={t('marca')}>
          <span className="marca__longa">{t('marca')}</span>
          <span className="marca__curta" aria-hidden="true">{t('marcaCurta')}</span>
        </Link>
        <nav aria-label={t('navPrincipal')}>
          <NavLink to="/mapa">{t('navMapa')}</NavLink>
          <NavLink to="/metodo">{t('navMetodo')}</NavLink>
          <NavLink to="/construcao">{t('navConstrucao')}</NavLink>
          <BotaoIdioma />
          <BotaoTema />
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/mapa" element={<Explorar />} />
        <Route path="/metodo" element={<Metodo />} />
        <Route path="/construcao" element={<Construcao />} />
      </Routes>
      <ConteudoOculto />
    </BrowserRouter>
  )
}
