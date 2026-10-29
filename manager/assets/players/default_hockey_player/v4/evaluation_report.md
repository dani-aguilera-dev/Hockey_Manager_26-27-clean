# Evaluación de producción · Jugador v4

**Fecha:** 2026-10-29  
**Asset:** `default_hockey_player_v4`  
**Alcance:** jugador low-poly estilizado para Hockey Manager, renderizado en tiempo real.  
**Resultado:** **PASS** para integración técnica en producción.

## 1. Gate técnico

| Criterio | Objetivo | Resultado | Estado |
| --- | ---: | ---: | --- |
| Triángulos LOD0 | ≤ 25.000 | **17.196** | PASS |
| Triángulos LOD1 | ≤ 10.000 | **8.598** | PASS |
| Triángulos LOD2 | ≤ 5.000 | **4.291** | PASS |
| Materiales del jugador | ≤ 12 | **10** | PASS |
| UVs | ≥ 1 | **1 UVMap** | PASS |
| Influencias máximas | ≤ 4 | **2** | PASS |
| Vértices sin peso | 0 | **0** | PASS |
| Aristas interiores no-manifold | 0 | **0** | PASS |
| Vértices sueltos | 0 | **0** | PASS |
| Huesos | 21 | **21** | PASS |
| Acciones exportadas | ≥ 4 | **4** | PASS |
| Skin en GLB | 1 | **1** | PASS |
| Joints del skin | 21 | **21** | PASS |
| Colisión | cápsula | **508 tris** | PASS |
| Texturas | 512×512 | **13 mapas** | PASS |

## 2. Métricas de malla

| Malla | Vértices | Caras | Triángulos | Materiales | UV | Peso máx. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `Player_v4` | 10.348 | 9.487 | 17.196 | 10 | 1 | 2 |
| `Stick_v4` | 928 | 910 | 1.828 | 4 | 1 | 1 |
| `Ball_v4` | 458 | 480 | 912 | 2 | 1 | estático |
| `Player_v4_LOD1` | 4.962 | 8.598 | 8.598 | 10 | 1 | 3 |
| `Player_v4_LOD2` | 2.669 | 4.291 | 4.291 | 10 | 1 | 3 |
| `Collision_Capsule` | 260 | 274 | 508 | 0 | 1 | estático |

## 3. Rig y animación

- Armature: `Rig Humanoide`, **21 huesos**.
- Cadena: root → hips → spine → chest → neck → head; brazos L/R; piernas L/R; hueso `stick` hijo de `hand.L`.
- Acciones:
  - `Idle` · frames 1–120
  - `Run` · frames 1–30
  - `Pass` · frames 1–30
  - `Shoot` · frames 1–24
- Animaciones in-place, sin root motion; el controlador del juego mueve el personaje.
- No hay facial rig, IK de manos ni simulación de tela; no son necesarios para el alcance de manager y quedan como mejora opcional.

## 4. Validación GLB

| Archivo | Tamaño | Mallas | Materiales | Imágenes | Skin | Joints | Animaciones |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `default_hockey_player_v4.glb` | 2.447 KB | 3 | 12 | 12 | 1 | 21 | Idle, Pass, Run, Shoot |
| `default_hockey_player_v4_LOD1.glb` | 1.705 KB | 1 | 10 | 10 | 1 | 21 | Idle, Pass, Run, Shoot |
| `default_hockey_player_v4_LOD2.glb` | 1.520 KB | 1 | 10 | 10 | 1 | 21 | Idle, Pass, Run, Shoot |
| `player_v4_collision.glb` | 37 KB | 1 | 0 | 0 | 0 | 0 | — |

## 5. Aristas de contorno

El jugador tiene **3.108 aristas de contorno**; no son aristas interiores no-manifold. Corresponden a aberturas intencionales de prendas (bajo de camiseta, cuello, bocamangas), textos/decalcomanías planos y algunas costuras. El LOD1 tiene 934 y el LOD2 671. El stick tiene 16 en los extremos abiertos.

**Decisión:** aceptadas como geometría abierta de prendas/decalcomanías. No hay aristas interiores no-manifold en LOD0, LOD1 ni LOD2.

## 6. Evidencia visual

- `default_hockey_player_v4.png` · render principal.
- `renders/front.png`, `back.png`, `side.png`, `three_quarter.png` · turnaround.
- `animations_preview.png` · contact sheet de las cuatro acciones.
- `animations.mp4` · preview encadenado Idle → Run → Pass → Shoot.

## 7. Limitaciones conocidas

- Estilizado low-poly, no realismo AAA.
- Texturas de 512 px; para primeros planos de héroe se recomienda una variante 1K/2K.
- Sin facial rig, sin simulación de tela y sin IK de manos.
- El stick es una pieza estilizada de lectura visual; no es una réplica reglamentaria a escala.
- Las animaciones son un set base de cuatro clips; recepción, tackle y celebración quedan para una siguiente iteración.

## 8. Veredicto

**PASS técnico para producción del manager.** El asset está listo para importarse en el motor con LODs, colisión y cuatro animaciones. La siguiente revisión recomendada es de arte final (resolución de texturas y pulido de animaciones), no un bloqueo de integración.
