import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, RotateCcw, Save } from 'lucide-react'
import { api } from '../lib/api'
import { useToast } from '../context/ToastContext'
import { Button, Card, LoadingBlock, Logo, Notice, PageHeader } from '../components/ui'

interface Prefs {
  text_size: 'normal' | 'large'
  compact: boolean
  confirm_exit: boolean
}

export default function Options({ embedded = false }: { embedded?: boolean }) {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [prefs, setPrefs] = useState<Prefs>({ text_size: 'normal', compact: false, confirm_exit: true })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get<{ prefs: Prefs }>('/options')
      .then(({ data }) => setPrefs(data.prefs))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar los ajustes.', 'danger'))
      .finally(() => setLoading(false))
  }, [toast])

  useEffect(() => {
    document.body.classList.toggle('text-large', prefs.text_size === 'large')
    document.body.classList.toggle('compact', prefs.compact)
  }, [prefs])

  async function save() {
    setSaving(true)
    try {
      const { data } = await api.post<{ prefs: Prefs }>('/options', prefs)
      setPrefs(data.prefs)
      toast('Ajustes guardados.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudieron guardar los ajustes.', 'danger')
    } finally {
      setSaving(false)
    }
  }

  async function reset() {
    try {
      const { data } = await api.post<{ prefs: Prefs }>('/options', { reset: true })
      setPrefs(data.prefs)
      toast('Ajustes restablecidos.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudieron restablecer los ajustes.', 'danger')
    }
  }

  if (loading) return embedded ? <LoadingBlock label="Cargando ajustes…" /> : <div className="app-loading"><Logo /><LoadingBlock label="Cargando ajustes…" /></div>

  const body = (
    <>
      <Card>
        <div className="option-block">
          <h3>Tamaño del texto</h3>
          <p className="small">Aumenta el tamaño base de toda la interfaz.</p>
          <div className="stack-sm">
            <label className="option-card">
              <input type="radio" name="text_size" checked={prefs.text_size === 'normal'} onChange={() => setPrefs({ ...prefs, text_size: 'normal' })} />
              <span><b>Normal</b><br /><span>14 px · densidad estándar</span></span>
            </label>
            <label className="option-card">
              <input type="radio" name="text_size" checked={prefs.text_size === 'large'} onChange={() => setPrefs({ ...prefs, text_size: 'large' })} />
              <span><b>Grande</b><br /><span>16 px · más cómodo en pantallas grandes</span></span>
            </label>
          </div>
        </div>
        <div className="option-block">
          <h3>Densidad</h3>
          <label className="checkline"><input type="checkbox" checked={prefs.compact} onChange={(event) => setPrefs({ ...prefs, compact: event.target.checked })} /> Modo compacto</label>
          <p className="small" style={{ marginTop: 5 }}>Reduce el espacio de tarjetas y fichas.</p>
        </div>
        <div className="option-block">
          <h3>Seguridad</h3>
          <label className="checkline"><input type="checkbox" checked={prefs.confirm_exit} onChange={(event) => setPrefs({ ...prefs, confirm_exit: event.target.checked })} /> Confirmar al salir de una partida</label>
        </div>
        <div className="actions mt-2">
          <Button variant="primary" icon={Save} onClick={save} loading={saving}>Guardar ajustes</Button>
          <Button icon={RotateCcw} onClick={reset}>Restablecer</Button>
        </div>
      </Card>
      <Notice tone="info">Los ajustes se aplican a la sesión web actual. La partida se guarda automáticamente al avanzar el calendario.</Notice>
    </>
  )

  if (embedded) {
    return (
      <>
        <PageHeader eyebrow="Ajustes" title="La interfaz, a tu medida." subtitle="Preferencias de lectura y comportamiento de la partida." actions={<Button icon={ArrowLeft} onClick={() => navigate('/game')}>Volver al club</Button>} />
        {body}
      </>
    )
  }

  return (
    <div className="landing">
      <div className="landing-inner" style={{ maxWidth: 860 }}>
        <header className="landing-header">
          <Logo />
          <Button variant="ghost" icon={ArrowLeft} onClick={() => navigate(-1)}>Volver</Button>
        </header>
        <div className="eyebrow">Ajustes</div>
        <h1 style={{ fontSize: 38 }}>La interfaz, a tu medida.</h1>
        <p className="landing-sub" style={{ marginBottom: 22 }}>Preferencias de lectura y comportamiento de la partida.</p>
        {body}
      </div>
    </div>
  )
}
