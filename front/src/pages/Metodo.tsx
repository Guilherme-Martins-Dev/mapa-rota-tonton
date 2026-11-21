import { useT } from '../i18n/useIdioma'
import { Tx } from '../ui/Tx'

/** Página de método: o que o back-end faz, em ordem. Texto corrido, largura de leitura. */
export default function Metodo() {
  const t = useT()
  return (
    <main className="texto">
      <h1>{t('metodoTitulo')}</h1>

      {t('metodo').map((s) => (
        <section key={s.h}>
          <h2>{s.h}</h2>
          <p><Tx>{s.p}</Tx></p>
        </section>
      ))}

      <h2>{t('metodoDados')}</h2>
      <p>{t('avisoDados')} {t('metodoDadosTexto')}</p>
    </main>
  )
}
