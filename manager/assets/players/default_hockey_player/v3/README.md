# Jugador v3 · cuerpo, skinning y animaciones

Archivos:

- `default_hockey_player_v3.blend`: escena editable con `Body_Skin` y `Rig Humanoide`.
- `default_hockey_player_v3.glb`: exportación con piel de 21 joints y cuatro animaciones.
- `default_hockey_player_v3.png`: render principal 1200x1400.
- `animations_preview.png`: contact sheet de Idle, Run, Pass y Shoot.
- `animations.mp4`: vídeo combinado de las cuatro animaciones.
- `animations/`: clips individuales `idle.mp4`, `run.mp4`, `pass.mp4` y `shoot.mp4`.

## Rig

21 huesos:

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

## Skinning

`Body_Skin` agrupa la piel visible del cuerpo y usa un modificador Armature con pesos suaves entre los dos huesos más cercanos. Las piezas de equipamiento y ropa siguen vinculadas a huesos para mantener el aspecto low-poly.

## Animaciones

| Acción | Frames | Uso |
| --- | --- | --- |
| `Idle` | 1–120 | respiración y balanceo mínimo |
| `Run` | 1–30 | zancada con piernas y balanceo de cadera |
| `Pass` | 1–30 | giro de tronco para pase |
| `Shoot` | 1–24 | armado y golpeo |

El GLB se exportó con `export_animation_mode='ACTIONS'`; contiene una piel con 21 joints y las cuatro animaciones.
