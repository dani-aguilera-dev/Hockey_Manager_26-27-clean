import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import type { GameState } from '../types'

interface GameContextValue {
  game: GameState | null
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
  applyState: (state: GameState) => void
}

const GameContext = createContext<GameContextValue | null>(null)

export function GameProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const [game, setGame] = useState<GameState | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.get<GameState>('/state')
      setGame(data)
    } catch (err) {
      if (err instanceof ApiError && err.code === 'no_game') {
        navigate('/', { replace: true })
        return
      }
      setError(err instanceof Error ? err.message : 'No se pudo cargar la partida.')
    } finally {
      setLoading(false)
    }
  }, [navigate])

  useEffect(() => {
    void load()
  }, [load])

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get<GameState>('/state')
      setGame(data)
    } catch (err) {
      if (err instanceof ApiError && err.code === 'no_game') {
        navigate('/', { replace: true })
        return
      }
      setError(err instanceof Error ? err.message : 'No se pudo actualizar la partida.')
    }
  }, [navigate])

  const applyState = useCallback((state: GameState) => setGame(state), [])

  return (
    <GameContext.Provider value={{ game, loading, error, refresh, applyState }}>
      {children}
    </GameContext.Provider>
  )
}

export function useGame() {
  const value = useContext(GameContext)
  if (!value) throw new Error('useGame must be used inside GameProvider')
  return value
}
