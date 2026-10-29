# Referencias y decisiones de diseño · Jugador v4

## Referencias consultadas

### Hockey y equipamiento

- [Wikipedia · Field hockey](https://en.wikipedia.org/wiki/Field_hockey): reglas, equipamiento del jugador de campo y diferencia con el portero.
- [ResearchGate · Typical poses for 4 different actions of a hockey player](https://www.researchgate.net/figure/Typical-poses-for-4-different-actions-of-a-hockey-player_fig4_319283989): poses de referencia para acciones y lectura del stick.
- [PubMed · Morphological characteristics of elite male field hockey players](https://pubmed.ncbi.nlm.nih.gov/1861485/): referencia antropométrica de **176,3 cm y 75,2 kg** para un jugador de élite.
- [Olympics · Hockey stick size, weight and length](https://www.olympics.com/en/news/field-hockey-stick-size-weight-length): el stick no debe superar **105 cm** ni **737 g**; el conjunto debe pasar por un anillo de **51 mm**.
- [Dimensions.com · Field hockey stick](https://www.dimensions.com/element/field-hockey-stick): proporciones de cabeza, splice y mango.
- [Reddit r/Fieldhockey · Beginner to field hockey](https://www.reddit.com/r/Fieldhockey/comments/1krdnmj/beginner_to_field_hockey/): las espinilleras van bajo las medias; las medias forman parte del kit.
- [MimiSports · Field hockey team packages](https://mimisports.com/products/team-packages/field-hockey-team-packages/): jersey, shorts/skort, medias sobre espinilleras y tejidos técnicos.
- [STX · Field hockey stick sizing](https://stx.com/pages/field-hockey-stick-sizing-chart): lectura de tallas y proporción del stick.

### Pipeline de personaje de videojuego

- [Juego Studio · 3D game modeling services](https://www.juegostudio.com/game-art-services/modeling): retopología, UVs, PBR, rig, LODs y especificación técnica.
- [Tripo · Game character models: creation, optimization & best practices](https://www.tripo3d.ai/blog/explore/game-character-models): topología game-ready, PBR, LODs y presupuesto de rendimiento.
- [Video Game Development Authority · Character and environment modeling](https://videogamedevelopmentauthority.com/character-and-environment-modeling/): flujo sculpt → retopo → UV → texturas → rig → LOD.

## Decisiones aplicadas

1. **Silueta estilizada, no simulación antropométrica exacta.** La referencia de 176,3 cm se usó para proporciones; el asset final mide 1,954 m por legibilidad y presencia en cámara.
2. **Equipamiento de jugador de campo.** Jersey azul/orange/blanco de San Fernando, shorts, medias sobre espinilleras, botas de turf, guante de mano izquierda y stick.
3. **Medias sobre espinilleras.** Se eliminaron las placas externas de la v3; la protección queda implícita bajo la media, como en el kit real.
4. **Stick de dos manos.** El jugador mantiene las dos manos cerca del stick; el hueso `stick` cuelga de `hand.L` y la animación mueve el conjunto con el torso.
5. **Rig de 21 huesos.** Presupuesto suficiente para un jugador de manager: root, hips, spine, chest, neck, head, brazos/manos, piernas/pies y stick.
6. **LODs 50 % / 25 %.** LOD0 17.196 tris, LOD1 8.598, LOD2 4.291; todos conservan skin y UVs.
7. **PBR de 512 px.** Mapas de color con variación sutil de tejido, piel, goma, carbono y metal; empaquetados para que el GLB sea autocontenido.
8. **Colisión separada.** Cápsula de 508 tris para el controlador, sin mezclarla con la malla visual.
9. **Sin assets de terceros.** La geometría, los materiales y las texturas se generaron en Blender/Python para este proyecto. Las imágenes de referencia se consultaron solo como estudio y no se incluyen en el asset.

## Lectura rápida de referencias frente al asset

| Elemento | Referencia | Implementación |
| --- | --- | --- |
| Altura | 176,3 cm élite | 1,954 m estilizado |
| Stick | ≤105 cm, ≤737 g | Stick estilizado de dos manos; se prioriza la lectura visual |
| Balón | ~7,2 cm | 7,5 cm |
| Espinilleras | Bajo la media | Medias limpias sobre protección implícita |
| Kit | Jersey/shorts/medias | Azul/orange/blanco San Fernando |
| Pipeline | Retopo, UV, PBR, LOD, rig | Malla unificada, UVs, 13 texturas, 2 LODs, 21 huesos |
