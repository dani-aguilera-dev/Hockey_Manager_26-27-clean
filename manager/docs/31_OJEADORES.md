# Ojeadores de mercado

La pestaña **Ojeador** del mercado ofrece una lectura guiada del mercado para
que no haya que construir una búsqueda desde cero. El mercado manual sigue
disponible en el resto de pestañas.

## Qué tiene en cuenta

- presupuesto de fichajes y caja;
- nivel medio del once;
- edad media de la plantilla;
- carencias por línea: portería, defensa, medio y ataque;
- salario que puede asumir el club;
- rendimiento: rating, partidos, goles y asistencias;
- potencial y edad;
- si el jugador está en venta;
- liga y club de origen;
- rating del ojeador contratado.

## Enfoques

- **Equilibrado**.
- **Cubrir carencias**.
- **Jóvenes con proyección**.
- **Rendimiento inmediato**.
- **Oportunidades de mercado**.
- **Salto de calidad**.

También se puede filtrar por edad máxima y posición.

## Confianza

El ojeador contratado (`scout`) mejora la confianza del informe. Si no hay un
especialista, el club usa una red provisional de ojeadores con rating 55. La
recomendación sigue siendo válida, pero el margen de error es mayor.

## Fit score

Cada objetivo recibe una puntuación de encaje y razones legibles:

- cubre una carencia;
- sube el nivel del once;
- entra en presupuesto;
- tiene potencial;
- aporta experiencia;
- tiene salario asumible;
- está en el escaparate.

El jugador se puede abrir desde la recomendación y negociar desde su ficha
general.

## API

`GET /api/scouting?focus=equilibrado&max_age=25&position=Medio`

Devuelve contexto del club, necesidades, ojeador y recomendaciones con fit
score, razones, precio, salario y datos del jugador.

## Tests

Cobertura: presupuesto, nivel, necesidades, filtros de edad/posición y enfoques.

Total actual: **100 tests**.
