# Cantera, categorías inferiores y nombres por comunidad

**Estado:** implementado (2026-10-21).

## 1. Por qué Sub-16, Sub-18 y Sub-21

La RFEH organiza competiciones de selecciones autonómicas y clubes en categorías Sub-14, Sub-16, Sub-18 y Sub-21. En el calendario formativo del hockey hierba español se usan habitualmente:

| Categoría | Nombre tradicional | Edad orientativa |
| --- | --- | --- |
| Sub-16 | Cadete | 14-15 años |
| Sub-18 | Juvenil | 16-17 años |
| Sub-21 | Júnior | 18-20 años |

Fuentes consultadas:

- [RFEH — competiciones de selecciones autonómicas](https://historico.rfeh.es/competiciones/)
- [FHCV — CESA Sub-16 Valencia 2026](https://fhcv.es/cesa-sub-16-valencia-2026/)
- [Wikipedia — categorías deportivas por edad](https://es.wikipedia.org/wiki/Categor%C3%ADas_deportivas_por_edad)

La edad exacta depende del año de nacimiento y del reglamento de cada competición. El juego usa una simplificación por edad actual para que la progresión sea legible.

## 2. Cómo se integra en el juego

- Cada club recibe **6 canteranos iniciales**, dos por categoría.
- Cada temporada llegan **3 nuevas incorporaciones** de 14-16 años.
- Los jugadores crecen, mejoran atributos y cambian de categoría al cumplir años.
- A los **21 años** salen de la cantera.
- La pantalla `Cantera` agrupa por **Sub-16 · Cadete**, **Sub-18 · Juvenil** y **Sub-21 · Júnior**.
- Se puede promover al primer equipo o liberar al jugador.
- La academia y el potencial condicionan el desarrollo.

No se simulan todavía ligas juveniles completas: las categorías son una capa de formación y progresión dentro del juego de gestión.

## 3. Nombres por comunidad autónoma

`manager/data/youth_names.json` contiene pools de nombres y apellidos para las 17 comunidades autónomas y un pool común de respaldo.

- Un canterano de **Andalucía** usa nombres como Álvaro, Antonio, Manuel, José, Francisco, Javier, Sergio, Rafael, Pablo, Miguel, Alejandro, Daniel, Adrián, Hugo, Mario, Rubén, Fernando, Alberto, Diego o Iván.
- Un canterano de **Cataluña** puede usar Aleix, Pau, Marc, Nil, Joan, Biel, Arnau, Jan, Pol, Oriol, Roc, Guillem, Ferran, Gerard, Èric, Xavi, Jordi o Sergi.
- Los apellidos también siguen el pool regional: García, Rodríguez, López, Sánchez, Pérez... en Andalucía; Serra, Pujol, Vidal, Roca, Camps... en Cataluña.
- El nombre completo se forma con nombre + dos apellidos del mismo pool.
- Si un club no tiene comunidad reconocida, se usa el pool común.

El objetivo es dar identidad local a la cantera sin pretender representar una distribución estadística real de nombres. En la realidad cada vestuario es diverso; el juego usa los pools como seña de identidad regional.

## 4. Archivos

```text
manager/data/youth_names.json     # pools por comunidad
manager/src/youth.py              # generación, categorías, desarrollo
manager/src/models.py             # TeamState.community y PlayerState.youth_category
manager/web/templates/youth.html  # vista por categorías
manager/src/tests/test_phase4.py  # pruebas de categorías y nombres
```

## 5. Pruebas

Se comprueba que:

- un club andaluz no recibe nombres catalanes del pool;
- todos los nombres y apellidos pertenecen al pool de su comunidad;
- la cantera inicial contiene Sub-16, Sub-18 y Sub-21;
- las edades 14/16/18/21 se mapean correctamente;
- la promoción, el desarrollo y la nueva generación siguen funcionando.

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado actual: **80 tests superados**.

## 6. Próximos pasos

- Ligas juveniles Sub-16/Sub-18/Sub-21 con calendario y resultados.
- Estadísticas históricas de la cantera.
- Migración de nombres en partidas antiguas.
- Pools más amplios y revisión con fuentes demográficas.
