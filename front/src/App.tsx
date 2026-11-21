import { BrowserRouter, Link, NavLink, Route, Routes } from 'react-router-dom'
import Explorar from './pages/Explorar'
import Home from './pages/Home'
import Metodo from './pages/Metodo'

export default function App() {
  return (
    <BrowserRouter>
      <header className="barra">
        <Link to="/" className="marca">Rotas de Messejana</Link>
        <nav aria-label="Principal">
          <NavLink to="/mapa">Mapa</NavLink>
          <NavLink to="/metodo">Método</NavLink>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/mapa" element={<Explorar />} />
        <Route path="/metodo" element={<Metodo />} />
      </Routes>
    </BrowserRouter>
  )
}
