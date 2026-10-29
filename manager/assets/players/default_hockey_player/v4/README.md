# Jugador v4 · asset de producción

Jugador de hockey hierba estilizado, low-poly y game-ready para Hockey Manager. La v4 sustituye al blockout de v1/v2/v3 con una malla unificada, ropa y equipamiento reorganizados, texturas PBR, LODs, colisión y un set de animaciones exportado.

## Archivos principales

```text
default_hockey_player_v4.glb          # LOD0 jugador + stick + balón + skin + animaciones
default_hockey_player_v4_LOD1.glb     # LOD1 ~50 %
default_hockey_player_v4_LOD2.glb     # LOD2 ~25 %
player_v4_collision.glb               # cápsula de colisión
default_hockey_player_v4.blend        # escena editable
default_hockey_player_v4.png          # render principal
animations.mp4                        # Idle → Run → Pass → Shoot
animations_preview.png                # contact sheet
animations/                           # clips individuales
renders/                              # front, back, side, three_quarter
textures/materials/                   # 13 texturas PBR de 512×512
asset_manifest.json                   # inventario, hashes y validación
evaluation_report.md                  # gate técnico de producción
references.md                         # fuentes y decisiones de diseño
```

## Especificaciones

- Unidades: metros.
- Altura del jugador: **1,954 m** (proporción estilizada).
- Balón: **7,5 cm** de diámetro.
- LOD0: **10.348 vértices / 17.196 triángulos / 10 materiales**.
- LOD1: **4.962 vértices / 8.598 triángulos**.
- LOD2: **2.669 vértices / 4.291 triángulos**.
- Texturas: **13 mapas PNG de 512×512**, empaquetados en el `.blend` y exportados en el GLB.
- Rig: **21 huesos**.
- Acciones: `Idle`, `Run`, `Pass`, `Shoot`.
- Colisión: cápsula de **508 triángulos**.

## Rig

```text
root
└─ hips
   ├─ spine
   │  └─ chest
   │     ├─ neck
   │     │  └─ head
   │     ├─ shoulder.L → upper_arm.L → forearm.L → hand.L → stick
   │     └─ shoulder.R → upper_arm.R → forearm.R → hand.R
   ├─ thigh.L → shin.L → foot.L
   └─ thigh.R → shin.R → foot.R
```

El jugador, el stick y el balón son mallas separadas. El jugador y el stick están skinneados al mismo armature; el balón es un prop estático.

## Animaciones

| Acción | Rango | Uso |
| --- | --- | --- |
| `Idle` | 1–120 | respiración y microbalanceo |
| `Run` | 1–30 | zancada in-place |
| `Pass` | 1–30 | giro de tronco y golpeo de pase |
| `Shoot` | 1–24 | armado y golpeo |

## Integración

- Importar el GLB con escala 1.0; el export de Blender usa glTF Y-up.
- El origen está a nivel de suelo.
- Usar `default_hockey_player_v4_LOD1.glb` y `LOD2` para distancias medias/cortas; comparten armature y nombres de acciones.
- `player_v4_collision.glb` es una cápsula independiente para el controlador.
- El material del jugador usa texturas de 512 px; para una versión de héroe se puede subir a 1K/2K sin cambiar la topología.

## Estado de producción

El asset pasa el gate técnico documentado en `evaluation_report.md`: sin vértices sin peso, sin aristas interiores no-manifold, máximo 2 influencias por vértice, UVs presentes, skin de 21 joints y cuatro animaciones en el GLB. Las aristas de contorno abiertas son las aberturas intencionales de prendas y textos/decalcomanías, no defectos interiores.

Sigue siendo un personaje **estilizado low-poly**, no un actor AAA realista: no tiene facial rig, simulación de tela ni IK de manos. Para el alcance del manager es un asset de producción; una revisión de arte final puede subir texturas a 1K y añadir animaciones de recepción/tackle/celebración.
