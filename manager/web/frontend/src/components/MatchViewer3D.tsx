import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import type { LivePayload } from '../types'

type Vec2 = [number, number]

type PlayerEntity = {
  group: THREE.Group
  body: THREE.Mesh
  leftArm: THREE.Group
  rightArm: THREE.Group
  leftLeg: THREE.Group
  rightLeg: THREE.Group
  base: Vec2
  velocity: THREE.Vector3
  side: number
  phase: number
  name: string
}

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

function makeLabel(text: string) {
  const canvas = document.createElement('canvas')
  canvas.width = 256
  canvas.height = 48
  const context = canvas.getContext('2d')
  if (context) {
    context.fillStyle = 'rgba(4,12,22,.72)'
    context.fillRect(0, 0, canvas.width, canvas.height)
    context.font = 'bold 21px sans-serif'
    context.fillStyle = '#e9f4ff'
    context.textAlign = 'center'
    context.textBaseline = 'middle'
    context.fillText(text.slice(0, 20), canvas.width / 2, canvas.height / 2)
  }
  const texture = new THREE.CanvasTexture(canvas)
  texture.minFilter = THREE.LinearFilter
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false })
  const sprite = new THREE.Sprite(material)
  sprite.scale.set(4.5, 0.85, 1)
  sprite.position.y = 3.8
  return sprite
}

function createPlayer(name: string, color: number, accent: number) {
  const group = new THREE.Group()
  const kit = new THREE.MeshStandardMaterial({ color, roughness: 0.58, metalness: 0.06 })
  const skin = new THREE.MeshStandardMaterial({ color: accent, roughness: 0.55 })
  const dark = new THREE.MeshStandardMaterial({ color: 0x182435, roughness: 0.7 })

  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.62, 1.65, 10), kit)
  body.position.y = 1.45
  group.add(body)

  const head = new THREE.Mesh(new THREE.SphereGeometry(0.48, 10, 8), skin)
  head.position.y = 2.65
  group.add(head)

  const leftArm = new THREE.Group()
  const rightArm = new THREE.Group()
  for (const [arm, x] of [[leftArm, -0.85], [rightArm, 0.85]] as Array<[THREE.Group, number]>) {
    const limb = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.13, 0.95, 7), skin)
    limb.position.y = -0.45
    arm.position.set(x, 2.1, 0)
    arm.add(limb)
    group.add(arm)
  }

  const leftLeg = new THREE.Group()
  const rightLeg = new THREE.Group()
  for (const [leg, x] of [[leftLeg, -0.35], [rightLeg, 0.35]] as Array<[THREE.Group, number]>) {
    const limb = new THREE.Mesh(new THREE.CylinderGeometry(0.21, 0.16, 1.25, 7), dark)
    limb.position.y = -0.62
    leg.position.set(x, 0.92, 0)
    leg.add(limb)
    group.add(leg)
  }

  group.add(makeLabel(name))
  return { group, body, leftArm, rightArm, leftLeg, rightLeg }
}

export default function MatchViewer3D({ data }: { data: LivePayload }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const dataRef = useRef(data)
  const playersRef = useRef<PlayerEntity[]>([])
  const ballRef = useRef<THREE.Mesh | null>(null)
  const debugRef = useRef({ frames: 0, collisions: 0, goals: 0, lastEvent: '', ballSpeed: 0 })
  const lastEventRef = useRef('')
  const homeColor = 0x2f8fe8
  const awayColor = 0xff9d2e

  useEffect(() => {
    dataRef.current = data
  }, [data])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })
    } catch {
      container.innerHTML = '<div class="match-viewer-fallback">Tu navegador no permite WebGL.</div>'
      return
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    renderer.domElement.dataset.testid = 'match-viewer-canvas'
    renderer.domElement.setAttribute('aria-label', 'Simulación 3D del partido')
    container.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    scene.fog = new THREE.FogExp2(0x07101d, 0.011)
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

    const pitch = new THREE.Mesh(new THREE.PlaneGeometry(100, 60), new THREE.MeshStandardMaterial({ color: 0x3d8b4b, roughness: 0.9 }))
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

    const ball = new THREE.Mesh(new THREE.SphereGeometry(0.62, 14, 10), new THREE.MeshStandardMaterial({ color: 0xf7f7ef, roughness: 0.35 }))
    ball.position.set(2.5, 0.62, 0)
    ball.userData.velocity = new THREE.Vector3(7.5, 0, 0.5)
    scene.add(ball)
    ballRef.current = ball

    const formation = FORMATIONS[data.tactics.formation] || fallbackPositions
    const homeLine = data.user_side === 0 ? data.line : []
    const awayLine = data.user_side === 1 ? data.line : []
    const players: PlayerEntity[] = []
    for (let index = 0; index < 11; index += 1) {
      const homePosition = formation[index] || fallbackPositions[index]
      const awayPosition = mirror(formation[index] || fallbackPositions[index])
      const homeName = homeLine[index]?.name || `Local ${index + 1}`
      const awayName = awayLine[index]?.name || `Visitante ${index + 1}`
      const home = createPlayer(homeName, homeColor, 0xd8a06a)
      const away = createPlayer(awayName, awayColor, 0xd8a06a)
      home.group.position.set(homePosition[0], 0, homePosition[1])
      away.group.position.set(awayPosition[0], 0, awayPosition[1])
      scene.add(home.group, away.group)
      players.push({ ...home, base: homePosition, velocity: new THREE.Vector3(), side: 0, phase: index * 0.7, name: homeName })
      players.push({ ...away, base: awayPosition, velocity: new THREE.Vector3(), side: 1, phase: index * 0.9 + 1, name: awayName })
    }
    playersRef.current = players
    ;(debugRef.current as any).players = players.length
    ;(window as any).__matchViewer3D = debugRef.current

    const resize = () => {
      const width = container.clientWidth || 800
      const height = container.clientHeight || 380
      renderer.setSize(width, height, false)
      camera.aspect = width / height
      camera.updateProjectionMatrix()
    }
    const observer = new ResizeObserver(resize)
    observer.observe(container)
    resize()

    let frame = 0
    const clock = new THREE.Clock()
    let elapsed = 0
    const animate = () => {
      frame = requestAnimationFrame(animate)
      const dt = Math.min(0.05, Math.max(0.001, clock.getDelta()))
      elapsed += dt
      const current = dataRef.current
      const latest = current.events?.[current.events.length - 1]
      const eventKey = latest ? `${latest.type}-${latest.minute}-${latest.team_id}-${latest.player_id}` : ''
      if (eventKey !== lastEventRef.current) {
        lastEventRef.current = eventKey
        debugRef.current.lastEvent = eventKey
        if (latest?.team_id && ballRef.current) {
          const direction = latest.team_id === current.home.id ? 1 : -1
          const velocity = ballRef.current.userData.velocity as THREE.Vector3
          if (latest.type === 'goal') {
            debugRef.current.goals += 1
            ballRef.current.position.set(0, 0.62, 0)
            velocity.set(direction * 6, 0, 1.5)
          } else if (latest.type === 'pc' || latest.type === 'stroke' || latest.type === 'chance') {
            ballRef.current.position.set(direction * 26, 0.62, 0)
            velocity.set(direction * 12, 1.8, Math.sin(elapsed * 2) * 3)
          }
        }
      }

      const attackingSide = latest?.team_id === current.home.id ? 0 : latest?.team_id === current.away.id ? 1 : null
      const ballVelocity = ball.userData.velocity as THREE.Vector3
      ballVelocity.y -= 9.8 * dt
      ball.position.addScaledVector(ballVelocity, dt)
      ballVelocity.x *= 0.992
      ballVelocity.z *= 0.992
      if (ball.position.y < 0.62) {
        ball.position.y = 0.62
        ballVelocity.y = Math.abs(ballVelocity.y) * 0.58
      }
      if (Math.abs(ball.position.x) > 49.2) {
        if (Math.abs(ball.position.z) < 5.2) {
          debugRef.current.goals += 1
          ball.position.set(0, 0.62, 0)
          ballVelocity.set(0, 0, 0)
        } else {
          ball.position.x = Math.sign(ball.position.x) * 49.2
          ballVelocity.x *= -0.7
        }
      }
      if (Math.abs(ball.position.z) > 29.2) {
        ball.position.z = Math.sign(ball.position.z) * 29.2
        ballVelocity.z *= -0.7
      }

      for (const player of players) {
        const direction = player.side === 0 ? 1 : -1
        const attacking = attackingSide === player.side
        const targetX = player.base[0] + direction * (attacking ? 4.5 : -1.5)
        const targetZ = player.base[1] + (player.base[1] > 0 ? -1 : 1) * 0.8
        const desiredX = targetX + (ball.position.x - targetX) * 0.035
        const desiredZ = targetZ + (ball.position.z - targetZ) * 0.045
        player.velocity.x += (desiredX - player.group.position.x) * 0.42 * dt
        player.velocity.z += (desiredZ - player.group.position.z) * 0.42 * dt
        player.velocity.multiplyScalar(0.9)
        player.group.position.x = Math.max(-47, Math.min(47, player.group.position.x + player.velocity.x * dt))
        player.group.position.z = Math.max(-27, Math.min(27, player.group.position.z + player.velocity.z * dt))
        const speed = player.velocity.length()
        const swing = Math.sin(elapsed * 8 + player.phase) * Math.min(0.75, speed * 0.16)
        player.leftLeg.rotation.x = swing
        player.rightLeg.rotation.x = -swing
        player.leftArm.rotation.x = -swing * 0.8
        player.rightArm.rotation.x = swing * 0.8
        player.body.position.y = 1.45 + Math.abs(Math.sin(elapsed * 8 + player.phase)) * Math.min(0.09, speed * 0.02)
      }

      for (let i = 0; i < players.length; i += 1) {
        for (let j = i + 1; j < players.length; j += 1) {
          const a = players[i]
          const b = players[j]
          const dx = a.group.position.x - b.group.position.x
          const dz = a.group.position.z - b.group.position.z
          const distance = Math.hypot(dx, dz)
          if (distance > 0 && distance < 2.15) {
            const push = (2.15 - distance) * 0.5
            const nx = dx / distance
            const nz = dz / distance
            a.group.position.x += nx * push
            a.group.position.z += nz * push
            b.group.position.x -= nx * push
            b.group.position.z -= nz * push
            debugRef.current.collisions += 1
          }
        }
        const dx = players[i].group.position.x - ball.position.x
        const dz = players[i].group.position.z - ball.position.z
        if (Math.hypot(dx, dz) < 1.15 && ball.position.y < 2.2) {
          const distance = Math.max(0.1, Math.hypot(dx, dz))
          ballVelocity.x = (dx / distance) * 9 + players[i].velocity.x * 0.3
          ballVelocity.z = (dz / distance) * 9 + players[i].velocity.z * 0.3
          ballVelocity.y = 1.2
          debugRef.current.collisions += 1
        }
      }

      debugRef.current.frames += 1
      debugRef.current.ballSpeed = ballVelocity.length()
      renderer.render(scene, camera)
    }
    animate()

    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      renderer.dispose()
      if (container.contains(renderer.domElement)) container.removeChild(renderer.domElement)
    }
  }, [])

  const latest = data.events?.[data.events.length - 1]
  return (
    <div className="match-viewer-3d" ref={containerRef} data-testid="match-viewer-3d">
      <div className="match-viewer-ui" data-testid="match-viewer-ui">
        <div className="match-viewer-score"><b>{data.home.name}</b><span>{data.score[0]} - {data.score[1]}</span><b>{data.away.name}</b></div>
        <div className="match-viewer-meta"><span>{data.quarter}º cuarto</span><span>{data.minute}′</span><span>{data.finished ? 'Finalizado' : 'En directo'}</span></div>
        <div className="match-viewer-event">{latest ? latest.text : 'Partido en juego'}</div>
      </div>
      <div className="match-viewer-badge">3D · MatchEngine</div>
    </div>
  )
}
