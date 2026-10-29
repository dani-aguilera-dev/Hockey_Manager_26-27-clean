# Staff y finanzas (Fase 2B)

**Estado:** implementado (2026-10-20).

**Ámbito:** DHA masculina 2026-27.

---

## 1. Staff

Cada club DHA tiene siete roles de staff:

| Rol | Efecto en el juego |
|---|---|
| Segundo entrenador | Plan automático de entrenamiento y calidad de la charla delegada |
| Preparador físico | Sesiones físicas, fatiga y prevención de lesiones |
| Entrenador de porteros | Set pieces y desarrollo de porteros |
| Analista de rendimiento | Vídeo, preparación del rival y decisiones |
| Ojeador | Reservado para la fase de mercado |
| Fisioterapeuta | Recuperación de lesiones y sesiones de recuperación |
| Director deportivo | Reservado para contratos y mercado |

### Cómo se usa

- El **plan automático** de entrenamiento usa el rating del segundo entrenador.
- La **delegación de la charla** usa el rating del segundo entrenador.
- El **preparador físico** mejora las sesiones físicas y reduce el riesgo.
- El **fisioterapeuta** mejora la recuperación.
- El **analista** mejora el vídeo y el bonus de preparación del rival.
- El **entrenador de porteros** mejora set pieces y trabajo de porteros.

### Pantalla

En el dashboard:

```text
S. Staff y junta directiva
```

Muestra:

- rol, nombre, rating, salario y fuente;
- efectos del staff;
- junta directiva completa;
- objetivo y confianza de la junta.

---

## 2. Junta directiva

Cada club tiene seis roles:

- Presidente.
- Vicepresidente.
- Secretario.
- Tesorero.
- Vocal de hockey.
- Vocal social.

### Datos reales y modelo

- Los nombres con `source` distinto de `modelo` vienen de webs oficiales, iSquad, prensa o fundaciones.
- Los nombres con `source: modelo` son inventados para completar el rol.
- `manager/data/staff_dha_sources.md` documenta las fuentes y limitaciones.
- No se ha encontrado una fuente pública completa y actualizada para todos los staff técnicos; por eso muchos preparadores, analistas y ojeadores son modelos.

**Importante:** no usar esta base como dato oficial de staff real sin validación de cada club.

---

## 3. Finanzas

### Conceptos

- **Caja:** dinero operativo disponible. Paga viajes, salarios y gastos.
- **Presupuesto de fichajes:** cantidad reservada para el mercado; no se gasta todavía.
- **Masa salarial:** suma anual de salarios de jugadores y staff.
- **Patrocinio:** ingreso estimado por jornada.
- **Taquilla:** ingreso de los partidos en casa.
- **Viajes:** coste logístico de los desplazamientos.

### Cierre de jornada

Después de cada jornada:

```text
Caja final = caja inicial
           + taquilla
           + patrocinio
           - salarios de jugadores
           - salarios de staff
           - viajes
```

- La taquilla y los viajes ya se aplican durante el partido.
- El cierre añade patrocinio y descuenta salarios.
- Se guarda un registro de los últimos movimientos.
- Si la caja queda en negativo, baja la confianza de la junta.

### Pantalla

En el dashboard:

```text
6. Finanzas
```

Muestra:

- caja actual;
- presupuesto de fichajes;
- masa salarial de jugadores y staff;
- coste salarial por jornada;
- patrocinio por jornada;
- taquilla, patrocinio, salarios y viajes acumulados;
- balance de temporada;
- últimos movimientos;
- confianza de junta y afición.

---

## 4. Archivos

- `manager/data/staff_dha.json`: staff y junta de los 12 clubes DHA.
- `manager/data/staff_dha_sources.md`: fuentes y confianza.
- `manager/src/finance.py`: patrocinio, salarios y cierre de jornada.
- `manager/src/models.py`: `StaffMember`, `BoardMember`, salarios y campos financieros.
- `manager/src/training.py`: efectos del staff en el entrenamiento.
- `manager/src/ui.py`: pantallas de staff y finanzas.

---

## 5. Pruebas

`manager/src/tests/test_staff_finance.py` cubre:

- staff y junta cargados en los 12 clubes DHA;
- salarios de jugadores ajustados al presupuesto;
- cierre financiero de jornada;
- resumen financiero;
- protección contra doble cierre.

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado actual: **80 tests superados**.

---

## 6. Limitaciones

- No hay mercado de fichajes ni contratación/despido de staff.
- El ojeador y el director deportivo todavía no tienen efecto activo.
- Los salarios son una estimación proporcional al nivel de los jugadores.
- El patrocinio es un modelo, no un contrato real.
- La junta directiva no toma decisiones dinámicas más allá de la confianza.
- Parte del staff y de la junta son nombres de modelo, no datos oficiales.
