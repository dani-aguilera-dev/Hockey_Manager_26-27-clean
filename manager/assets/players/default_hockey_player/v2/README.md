# Jugador v2 · rig humanoide

- `default_hockey_player_v2.blend`: escena editable con armature.
- `default_hockey_player_v2.glb`: exportación con jerarquía de huesos.
- `default_hockey_player_v2.png`: render 1200x1400.

## Rig

21 huesos: root, hips, spine, chest, neck, head, shoulder/upper_arm/forearm/hand L/R, thigh/shin/foot L/R y stick.

Los objetos están vinculados a huesos mediante `parent_type='BONE'`. La siguiente fase es skinning con pesos para deformación orgánica y animaciones de carrera, pase y tiro.
