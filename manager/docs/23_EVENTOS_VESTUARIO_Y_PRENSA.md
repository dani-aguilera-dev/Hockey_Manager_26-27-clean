# Eventos, vestuario y prensa

**Estado:** implementado (2026-10-22).

## 1. Relación con los jugadores

Cada jugador tiene una relación individual con el entrenador:

```text
PlayerState.relationship: 0-100
```

Etiquetas:

- 80-100: Muy cercana.
- 60-79: Buena.
- 40-59: Normal.
- 20-39: Fría.
- 0-19: Mala.

La relación:

- se muestra en la ficha del jugador y en el vestuario;
- influye ligeramente en la selección del once;
- cambia con conversaciones, prensa y decisiones disciplinarias;
- se conserva al guardar la partida.

## 2. Eventos de vestuario y vida cotidiana

El diario del club puede generar:

- lesiones deportivas con distintos diagnósticos;
- enfermedades;
- asuntos familiares;
- roces entre compañeros;
- apariciones en prensa;
- incidentes fuera del club;
- citaciones judiciales;
- rumores y movimientos de mercado;
- entrenamientos y cambios de forma;
- noticias de liga, Copa y EHL.

Ejemplo de incidente:

> El jugador se vio envuelto en una pelea a la salida de una discoteca. El club abre un expediente interno y recibe una citación judicial; queda apartado hasta que se aclare el caso.

Se guarda como baja con motivo **Citación judicial**, no solo como una sanción genérica.

## 3. Conversaciones

El vestuario permite hablar de:

- minutos;
- contrato;
- ambiente del grupo;
- disciplina;
- familia;
- prensa;
- conflictos con compañeros.

Las respuestas pueden modificar:

- moral;
- forma;
- cohesión;
- relación con el entrenador;
- confianza de la junta;
- afición;
- suspensión;
- caja del club mediante multas.

## 4. Rueda de prensa

La previa incluye cinco bloques:

1. El partido.
2. Declaraciones del entrenador rival.
3. Presión por los resultados.
4. Estado del vestuario y bajas.
5. Objetivo de la junta.

El entrenador rival tiene nombre y una declaración generada según el rival y la jornada. La rueda de prensa aparece también enlazada desde la previa del partido.

## 5. Archivos

```text
manager/src/daily.py
manager/src/press.py
manager/src/models.py
manager/web/app.py
manager/web/templates/chat.html
manager/web/templates/press.html
manager/web/templates/match_preview.html
manager/web/templates/player.html
manager/src/tests/test_events_relationships.py
```

## 6. Pruebas

- Un incidente fuera del club genera baja, motivo legal, evento e inbox.
- La rueda incluye entrenador rival y declaración.
- Las respuestas de prensa pueden modificar la relación con un jugador.
- El chat aplica efectos de moral, relación, suspensión y caja.
- Los tests existentes de partido, mercado y calendario siguen pasando.

Resultado actual: **80 tests superados**.

## 7. Limitaciones

- Los incidentes legales son ficción del juego y se resuelven como partidos de baja, sin un sistema judicial completo.
- Las conversaciones no tienen árboles infinitos; hay varias ramas y respuestas.
- La relación no sustituye a la moral: son dos capas distintas.
- Las ruedas de prensa se generan por contexto y no por noticias externas reales.
