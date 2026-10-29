# Fase 3 — Mercado, contratos y multi-temporada

**Estado:** implementado (2026-10-20).

Incluye el mercado de fichajes, contratos, contratación de staff, mercado IA y transición entre temporadas con ascensos y descensos.

---

## 1. Ventanas de mercado

- **Verano:** antes del primer partido de la temporada.
- **Invierno:** al llegar a la jornada 12, antes de jugarla.
- **Cerrado:** el resto del tiempo.

En el dashboard:

```text
M. Mercado y contratos
```

Si está cerrado, la pantalla lo indica y no permite operar.

---

## 2. Buscar jugadores

La búsqueda muestra:

- nombre, club, posición y edad;
- overall estimado por el ojeador;
- valor de mercado;
- precio de salida;
- salario actual;
- contrato.

El **ojeador** reduce el margen de error del overall: un ojeador mejor da una horquilla más estrecha.

Al seleccionar un jugador:

- informe de ojeador;
- oferta de traspaso;
- salario anual;
- años de contrato.

El club vendedor y el jugador pueden rechazar la oferta si el precio o el salario no les convencen.

---

## 3. Ofertas recibidas

Los clubes IA pueden ofrecer dinero por tus jugadores.

- Puedes aceptar o rechazar.
- Si aceptas, el jugador se marcha, entra el dinero en caja y se actualiza su contrato.
- El mercado IA también mueve jugadores entre clubes rivales.

---

## 4. Contratos y renovaciones

Cada jugador tiene:

- salario anual;
- fecha de contrato.

Puedes renovar en cualquier momento desde `Mercado y contratos → Renovar contratos`.

Si un contrato vence al final de la temporada y no lo renuevas, el jugador sale del club. Para evitar plantillas vacías, la dirección deportiva incorpora canteranos de relleno.

---

## 5. Staff: contratar y despedir

En `S. Staff y junta directiva`:

- `[H]` contratar un rol libre;
- `[F]` despedir a un miembro;
- los candidatos tienen rating, salario y contrato;
- la prima de contratación y la indemnización salen de caja.

El segundo entrenador sigue afectando al plan automático y a la charla. Los demás roles afectan al entrenamiento y a la preparación.

---

## 6. Multi-temporada

Al terminar la temporada puedes pulsar `[C]` para continuar.

### Qué ocurre

- Se actualizan ascensos y descensos.
- Los jugadores envejecen un año.
- Los contratos vencidos dejan libre al jugador.
- Se generan canteranos para completar plantillas.
- Se resetean estadísticas, fatiga, lesiones y sanciones.
- Se genera el calendario de la nueva temporada.
- Se abre el mercado de verano.

### DHA y DHB

- **DHA:** 12 equipos, 22 jornadas, Final Four y playout.
- **DHB:** 16 equipos, dos grupos de 8, segunda fase y 21 jornadas totales.
- La DHB se juega con formato de dos fases; la 1ª Andaluza no se simula.
- Si tu club desciende, la siguiente temporada se juega en DHB y puedes intentar volver a DHA.

### Ascensos y descensos

- DHA: baja el 12º; el 11º juega playout.
- DHB: suben los dos primeros.
- Si el playout lo gana un equipo DHB, suben dos equipos DHB y bajan 11º y 12º.
- Si el 11º se mantiene, solo baja el 12º y sube el campeón DHB.

---

## 7. Archivos

- `manager/src/market.py`: mercado, ofertas, contratos, staff y mercado IA.
- `manager/src/season.py`: multi-temporada, ascensos, descensos, canteranos y calendario.
- `manager/src/calendar.py`: calendario genérico para DHA y DHB.
- `manager/src/ui.py`: pantallas de mercado, contratos y staff.
- `manager/src/tests/test_market.py`: pruebas del mercado y multi-temporada.

---

## 8. Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado actual: **80 tests superados**.

---

## 9. Limitaciones

- No hay cesiones, cláusulas de rescisión, agentes ni primas por objetivos.
- El mercado IA es una simulación simplificada.
- La DHB no reproduce la fase de grupos real.
- Los canteranos de relleno son genéricos.
- No hay negociación de patrocinios ni contratos comerciales.
- Las decisiones de la junta siguen siendo limitadas.
