import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import type { LivePayload } from '../types'

type Vec2 = [number, number]

const FORMATIONS: Record<string, Vec2[]> = {
  '4-3-3': [[-44, 0], [-30, -18], [-30, -6], [-30, 6], [-30, 18], [-15, -12], [-15, 0], [-15, 12], [5, -16], [5, 0], [5, 16]],
  '4-4-2': [[-44, 0], [-30, -18], [-30, -6], [-30, 6], [-30, 18], [-15, -18], [-15, -6], [-15, 6], [-15, 18], [5, -8], [5, 8]],
  '3-4-3': [[-44, 0], [-30, -12], [-30, 0], [-30, 12], [-15, -18], [-15, -6], [-15, 6], [-15, 18], [5, -16], [5, 0], [5, 16]],
  '3-3-3-1': [[-44, 0], [-30, -12], [-30, 0], [-30, 12], [-15, -18], [-15, 0], [-15, 18], [4, -18], [4, 0], [4, 18], [16, 0]],
  '5-3-2': [[-44, 0], [-30, -22], [-30, -11], [-30, 0], [-30, 11], [-30, 22], [-15, -12], [-15, 0], [-15, 12], [5, -8], [5, 8]],
}

const fallbackPositions = FORMATIONS['4-3-3']

function mirror(position: Vec2): Vec2 {
  return [-position[0], position[1]]
}

function addLine(parent: THREE.Object3D, points: Vec2[], color: number, opacity = 0.75) {
  const geometry = new THREE.BufferGeometry().setFromPoints(points.map(([x, z]) => new THREE.Vector3(x, 0.03, z)))
  const line = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color, transparent: true, opacity }))
  parent.add(line)
}

function addCircle(parent: THREE.Object3D, x: number, z: number, radius: number, color: number) {
  const points: Vec2[] = []
  for (let i = 0; i <= 32; i += 1) {
    const angle = (i / 32) * Math.PI * 2
    points.push([x + Math.cos(angle) * radius, z + Math.sin(angle) * radius])
  }
  addLine(parent, points, color, 0.7)
}

function createPlayer(color: number, accent: number) {
  const group = new THREE.Group()
  const body = new THREE.Mesh(
    new THREE.CylinderGeometry(0.9, 0.7, 2.2, 10),
    new THREE.MeshStandardMaterial({ color, roughness: 0.62, metalness: 0.05 }),
  )
  body.position.y = 1.2
  group.add(body)
  const head = new THREE.Mesh(
    new THREE.SphereGeometry(0.55, 10, 8),
    new THREE.MeshStandardMaterial({ color: accent, roughness: 0.55 }),
  )
  head.position.y = 2.65
  group.add(head)
  return group
}

export default function MatchViewer3D({ data }: { data: LivePayload }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const dataRef = useRef(data)
  const playersRef = useRef<Array<{ group: THREE.Group; base: Vec2; side: number; phase: number }>>([])
  const ballRef = useRef<THREE.Mesh | null>(null)

  useEffect(() => {
    dataRef.current = data
  }, [data])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    } catch {
      container.innerHTML = '<div class="match-viewer-fallback">Tu navegador no permite WebGL.</div>'
      return
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    renderer.domElement.dataset.testid = 'match-viewer-canvas'
    renderer.domElement.setAttribute('aria-label', 'Visor 3D del partido')
    container.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    scene.fog = new THREE.FogExp2(0x07101d, 0.012)
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 220)
    camera.position.set(0, 58, 55)
    camera.lookAt(0, 0, 0)

    scene.add(new THREE.HemisphereLight(0xd9f4ff, 0x16261b, 2.4))
    const key = new THREE.DirectionalLight(0xffffff, 2.8)
    key.position.set(-30, 55, 30)
    scene.add(key)
    const fill = new THREE.DirectionalLight(0x7fb8ff, 1.0)
    fill.position.set(35, 30, -30)
    scene.add(fill)

    const pitch = new THREE.Mesh(
      new THREE.PlaneGeometry(100, 60),
      new THREE.MeshStandardMaterial({ color: 0x3d8b4b, roughness: 0.9 }),
    )
    pitch.rotation.x = -Math.PI / 2
    scene.add(pitch)

    addLine(scene, [[-50, -30], [50, -30], [50, 30], [-50, 30], [-50, -30]], 0xe6f5e8)
    addLine(scene, [[0, -30], [0, 30]], 0xe6f5e8)
    addCircle(scene, 0, 0, 9, 0xe6f5e8)
    addLine(scene, [[-50, -18], [-42, -18], [-42, 18], [-50, 18]], 0xe6f5e8)
    addLine(scene, [[50, -18], [42, -18], [42, 18], [50, 18]], 0xe6f5e8)

    const goalMaterial = new THREE.MeshStandardMaterial({ color: 0xf1f5f8, roughness: 0.5 })
    for (const side of [-1, 1]) {
      const goal = new THREE.Mesh(new THREE.BoxGeometry(1.2, 3.2, 10), goalMaterial)
      goal.position.set(side * 50.5, 1.6, 0)
      scene.add(goal)
    }

    const ball = new THREE.Mesh(
      new THREE.SphereGeometry(0.65, 14, 10),
      new THREE.MeshStandardMaterial({ color: 0xf7f7ef, roughness: 0.35 }),
    )
    ball.position.y = 0.7
    scene.add(ball)
    ballRef.current = ball

    const homeFormation = FORMATIONS[data.tactics.formation] || fallbackPositions
    const awayFormation = fallbackPositions
    const players: Array<{ group: THREE.Group; base: Vec2; side: number; phase: number }> = []
    const homeLine = data.user_side === 0 ? data.line : []
    const awayLine = data.user_side === 1 ? data.line : []
    for (let index = 0; index < 11; index += 1) {
      const home = createPlayer(0x2f8fe8, 0xd8a06a)
      const away = createPlayer(0xff9d2e, 0xd8a06a)
      const h = homeFormation[index] || fallbackPositions[index]
      const a = mirror(awayFormation[index] || fallbackPositions[index])
      home.position.set(h[0], 0, h[1])
      away.position.set(a[0], 0, a[1])
      home.scale.setScalar(homeLine[index] ? 1.1 : 0.95)
      away.scale.setScalar(awayLine[index] ? 1.1 : 0.95)
      scene.add(home, away)
      players.push({ group: home, base: h, side: 0, phase: index * 0.7 })
      players.push({ group: away, base: a, side: 1, phase: index * 0.9 + 1 })
    }
    playersRef.current = players

    const resize = () => {
      const width = container.clientWidth || 800
      const height = container.clientHeight || 360
      renderer.setSize(width, height, false)
      camera.aspect = width / height
      camera.updateProjectionMatrix()
    }
    const observer = new ResizeObserver(resize)
    observer.observe(container)
    resize()

    let frame = 0
    const clock = new THREE.Clock()
    const animate = () => {
      frame = requestAnimationFrame(animate)
      const t = clock.getElapsedTime()
      const current = dataRef.current
      const latest = current.events?.[current.events.length - 1]
      const attackingSide = latest?.team_id === current.home.id ? 0 : latest?.team_id === current.away.id ? 1 : null
      const ballX = attackingSide === 0 ? 28 : attackingSide === 1 ? -28 : Math.sin(t * 0.7) * 7
      const ballZ = Math.sin(t * 1.3) * 10
      if (ballRef.current) {
        ballRef.current.position.x += (ballX - ballRef.current.position.x) * 0.035
        ballRef.current.position.z += (ballZ - ballRef.current.position.z) * 0.035
        ballRef.current.position.y = 0.7 + Math.abs(Math.sin(t * 2.2)) * 0.25
      }
      for (const player of playersRef.current) {
        const direction = player.side === 0 ? 1 : -1
        const advance = attackingSide === player.side ? 3.5 : 0
        const sway = Math.sin(t * 1.4 + player.phase) * 1.8
        player.group.position.x = player.base[0] + direction * advance + sway
        player.group.position.z = player.base[1] + Math.cos(t * 1.1 + player.phase) * 1.2
        player.group.position.y = Math.abs(Math.sin(t * 2.4 + player.phase)) * 0.12
      }
      renderer.render(scene, camera)
    }
    animate()

    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      renderer.dispose()
      container.removeChild(renderer.domElement)
    }
  }, [])

  return (
    <div className="match-viewer-3d" ref={containerRef} data-testid="match-viewer-3d">
      <div className="match-viewer-badge">3D · MatchEngine</div>
    </div>
  )
}
