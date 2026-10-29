# Diseño de interfaz web

**Estado:** implementado en la alpha web (2026-10-21).

Este documento recoge la investigación, las decisiones de color, la jerarquía visual y la checklist de usabilidad aplicadas a la web de Hockey Manager. No es una maqueta teórica: cada decisión tiene su equivalente en `manager/web/static/style.css` y en las plantillas.

---

## 1. Investigación con Brave

Consultas realizadas con la API de Brave:

- *football manager UI design dashboard usability dark theme color palette*
- *sports management game interface design principles data dense dashboard*
- *best dark dashboard color palette sports app green accent accessibility*
- *club crest badges football manager UI design*

Ideas que se incorporaron:

| Fuente | Idea aplicada |
| --- | --- |
| [SGX Studio — Sports Data UX](https://sgx.studio/sports-data-ux-design-making-complex-stats-digestible/) | Modelo **Bite / Snack / Meal**: primero el titular, después el contexto y por último el detalle. |
| [AdminLTE — Dashboard Color Schemes](https://adminlte.io/blog/best-admin-dashboard-color-schemes/) | Superficies oscuras en capas, un acento de marca separado de los colores semánticos y contraste WCAG AA. |
| [AdminLTE — Dark Dashboard Templates](https://adminlte.io/blog/dark-dashboard-templates/) | Evitar negro puro; usar bordes elevados en lugar de sombras en modo oscuro. |
| [Sports Dashboard Design — Lollypop](https://lollypop.design/blog/2019/november/dashboard-design-in-the-sports-industry/) | La densidad de datos necesita jerarquía, no acumulación de tablas. |
| [Dashboard Design Principles — UXPilot](https://uxpilot.ai/blogs/dashboard-design-principles) | Menos ruido, acciones principales visibles y estados vacíos claros. |

Conclusión: un juego de gestión no debe parecer una hoja de cálculo. Debe permitir **leer el estado del club en segundos**, **decidir en pocos clics** y **profundizar solo cuando el usuario quiera**.

---

## 2. Principios de producto

1. **Bite:** el dashboard responde de un vistazo a “¿cómo voy?”. Ticker de última hora, próximo partido, posición y caja.
2. **Snack:** noticias, clasificación corta, jugadores clave, moral y confianza de la junta.
3. **Meal:** plantilla completa, atributos, mercado, calendario, Copa y partes de partido.
4. **La identidad importa:** foto del jugador, escudo del club, posición y arquetipo siempre visibles.
5. **Una acción principal por pantalla:** jugar, guardar el once, entrenar, ofertar.
6. **Nada importante depende solo del color:** los badges llevan texto; las formas V/E/D se leen sin distinguir colores.

---

## 3. Paleta

La interfaz es **dark-first**, pensada para sesiones largas y para que las fotos y los escudos destaquen.

### Tokens

| Token | Hex | Uso |
| --- | --- | --- |
| `--bg` | `#0b1220` | Fondo de página |
| `--panel` | `#121d31` | Tarjetas |
| `--panel2` | `#17243b` | Superficie elevada, badges y botones secundarios |
| `--line` | `#263650` | Bordes y separadores |
| `--text` | `#e8eef8` | Texto principal |
| `--muted` | `#a4b6d2` | Texto secundario |
| `--accent` | `#ffb020` | Acción primaria y marca |
| `--accent2` | `#5aa9ff` | Enlaces e información |
| `--ok` | `#43d17c` | Éxito |
| `--warn` | `#ffcc66` | Aviso |
| `--danger` | `#ff6b6b` | Error, lesión, sanción |
| `--focus` | `#ffd166` | Anillo de foco |

### Por qué ámbar y no verde como color primario

El verde ya significa “éxito” en el juego. Si el botón principal también fuese verde, el usuario no sabría si un elemento es una acción o un estado. Se reservó el verde para éxito y se eligió **ámbar hockey** como acento de marca. El azul queda para enlaces e información, y el rojo para riesgo.

### Contraste comprobado

Ratios calculados con luminancia relativa WCAG:

| Combinación | Ratio |
| --- | ---: |
| Texto principal sobre fondo | 16.06:1 |
| Texto secundario sobre tarjeta | 8.19:1 |
| Texto secundario sobre fondo | 9.09:1 |
| Ámbar sobre fondo | 10.24:1 |
| Texto oscuro sobre botón ámbar | 9.37:1 |
| Enlace azul sobre fondo | 7.63:1 |
| Peligro sobre tarjeta | 6.07:1 |
| Éxito sobre tarjeta | 8.55:1 |
| Aviso sobre tarjeta | 11.30:1 |

Todos los pares principales superan **WCAG AA** (4.5:1) y la mayoría superan **AAA** (7:1).

### Tipografía y escala

- Sistema: `system-ui`, Segoe UI, Roboto, Arial.
- Texto base: 15 px.
- Títulos: 28/24/20/16 px.
- Texto auxiliar: 12 px con contraste alto; no se usa texto de 10 px para información decisiva.
- Cifras clave (OVR, presupuesto, marcador) con peso 800/900.

### Espaciado y superficies

- Tarjetas con radio 14 px, borde de 1 px y gradiente vertical suave.
- En modo oscuro se evita la sombra dura; la elevación se comunica con borde y superficie más clara.
- Rejillas responsive: `auto-fill` para fichas de jugador, 2 columnas para contexto y 3 para KPIs.

---

## 4. Jerarquía por pantalla

### Dashboard

- **Ticker de última hora** con la noticia principal.
- **Próximo partido** con escudos, jornada, estadio y acciones.
- **Portada** con noticias generadas desde el estado.
- **Estado del club**, jugadores clave y clasificación corta.
- Accesos rápidos e inbox.

### Plantilla

- Agrupada por **Portero, Defensa, Medio, Delantero**.
- Cada ficha muestra foto, nombre, posición, arquetipo, OVR, edad, fatiga y contrato.
- La ficha individual abre el detalle completo con barras de atributos.

### Táctica

- Pizarrón de 11 slots en filas de portería, defensa, medio y ataque.
- Cada slot muestra foto, posición, arquetipo, OVR y fatiga.
- Selector filtrado a los 14 jugadores con mejor encaje para esa posición.
- Botón de autoalineación y banquillo visual.
- Aviso visual si un jugador queda fuera de su posición.
- Al cambiar de formación, el once se autoalinea para no mezclar slots.
- Ya no hay una tabla de 30 checkboxes.

### Mercado

- Fichas de jugador con foto, club, posición, arquetipo, OVR ojeado y precio.
- Escudo del club propietario.
- Ficha individual con informe de ojeador, oferta y atributos.

### Partido

- Marcador con escudos, posesión y cuarto/minuto.
- Previa con forma, goleadores, bajas y aforo.
- Directo con estadísticas, comentario, once, cambios y táctica.
- Parte final con escudos y contexto.

### Noticias

- Motor determinista que genera previas, resultados, liderato, mercado, enfermería, cantera, scouting, afición, junta y Copa.
- Cada noticia puede llevar escudo o foto de jugador.
- No depende de medios externos ni de acceso a Internet.

---

## 5. Escudos y fotos

### Fotos de jugadores

- 976/976 jugadores tienen foto local.
- Se leen de `archivo_original` en el CSV de atributos.
- Se sirven con `send_from_directory` desde `jugadores/`, sin copiar archivos a `static`.
- Fallback: avatar con iniciales si falta la imagen.
- Crédito visible en la ficha: las fotos proceden de iSquad; los datos, de RFEH/iSquad y del modelo propio.

### Escudos

- Se descargaron **29 escudos oficiales de iSquad** (28 clubes activos + 1ª Andaluza) con `tools/fetch_isquad_crests.py`.
- El script localiza cada equipo por su `id_equipo`, descarga el escudo de la cabecera, elimina el fondo blanco a transparente y guarda un PNG de 320 px.
- `crest_src()` prioriza `<club>.png`; los SVG estilizados quedan como respaldo y se pueden regenerar con `tools/generate_crests.py`.
- Se usan en dashboard, plantilla, tabla, Copa, previa, directo, parte, mercado, nuevo juego y fin de temporada.
- Crédito: escudos y fotos proceden de iSquad; los datos, de RFEH/iSquad y del modelo propio.

Para sustituir un escudo por uno oficial:

```text
manager/web/static/crests/cd-terrassa.png
```

No hace falta cambiar código.

---

## 6. Usabilidad

### Implementado

- Enlace **“Saltar al contenido”**.
- `:focus-visible` con anillo de 3 px.
- Navegación sticky con scroll horizontal en móvil.
- Formularios con `<label>` asociado.
- Tablas con cabeceras y scroll en pantallas pequeñas.
- Botones con área mínima de 44 px en móvil.
- `prefers-reduced-motion` respetado.
- Texto alternativo en fotos y escudos; escudos decorativos con `alt=""` cuando el nombre está al lado.
- Badges de posición con texto, no solo color.
- Estados de lesión/sanción con texto además del color.
- Mensajes flash con categoría (`success`, `danger`, `warning`).
- Guardado visible en la barra superior y menú de juego global con guardar, cargar, volver, menú principal y opciones.
- Autoalineación para quien no quiera ajustar 11 selects.
- Selectores de táctica limitados por encaje para reducir carga cognitiva.

### Pendiente para una auditoría formal

- Prueba con lector de pantalla (NVDA/VoiceOver) en todas las pantallas.
- Navegación completa solo con teclado en el editor de once.
- Modo claro opcional.
- Atajos de teclado y paleta de comandos.
- Tests automatizados de contraste en CI.
- Auditoría con usuarios reales.

No se afirma “100 %” en el sentido de certificación: se afirma que la base cumple los criterios razonables de WCAG AA y que queda una auditoría formal pendiente.

### Bug encontrado al revisar la interfaz

La prueba visual del pizarrón detectó que el once automático se devolvía en orden de prioridad (portero, centrales, delanteros, laterales, medios) y la plantilla lo emparejaba con los slots por índice. El resultado era un once con delanteros en puestos de central. Se corrigió en `TeamState.auto_lineup()` guardando cada jugador en el índice de su slot y se añadió una prueba de regresión.

---

## 7. Archivos

```text
manager/
  src/news.py                    # noticias generadas
  web/app.py                     # rutas, helpers de foto/escudo
  web/templates/
    base.html
    dashboard.html
    news.html
    squad.html
    player.html
    tactics.html
    market.html
    market_player.html
    match_preview.html
    match_live.html
    match_report.html
    new_game.html
    macros.html
  web/static/style.css
  web/static/crests/*.svg
  web/static/avatar.svg
```

---

## 8. Próximos pasos recomendados

1. Revisar permisos de uso de los escudos oficiales y acreditarlos en la publicación.
2. Modo claro con los mismos tokens semánticos.
3. Editor de once con arrastrar y soltar, manteniendo los selects como alternativa accesible.
4. Comparador de jugadores y filtros guardados en mercado.
5. Cronología visual del partido con minutos clave.
6. Paleta de comandos (`Ctrl/Cmd + K`) para navegar sin ratón.
7. Auditar con lector de pantalla y usuarios.
