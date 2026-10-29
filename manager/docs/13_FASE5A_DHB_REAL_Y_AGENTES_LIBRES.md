# Fase 5A — DHB real y agentes libres

**Estado:** implementado (2026-10-21).

---

## 1. Agentes libres

La Primera Andaluza no se simula. Para no dejar jugadores atrapados en una liga que no existe en el juego:

- el club de 1ª Andaluza desaparece del mundo simulado;
- **todos sus jugadores pasan al mercado como agentes libres**;
- su `team_name` pasa a ser `Agente libre`;
- se pueden fichar sin pagar traspaso, solo salario y contrato;
- aparecen en la búsqueda del mercado.

Esto deja 28 clubes activos: 12 DHA + 16 DHB.

---

## 2. DHB con formato real

La DHB ya no es una liga única de 16 equipos. Ahora tiene:

### Fase 1

- 16 equipos repartidos en **dos grupos de 8**.
- Doble vuelta: 14 jornadas por grupo.
- 112 partidos en total.

### Fase 2

- Los **4 primeros de cada grupo** forman el Grupo A.
- Los **4 últimos de cada grupo** forman el Grupo B.
- Una vuelta de 7 jornadas (56 partidos).
- Se arrastran los puntos de la fase 1.
- Total: 21 jornadas.

### Final Four y ascenso

- Final Four entre los cuatro primeros del Grupo A.
- Ascienden a DHA los **dos primeros del Grupo A**.
- Descienden de DHA los dos últimos (incluyendo el playout).
- La DHB no desciende a 1ª Andaluza porque esa liga no se simula.

### Si tu club está en DHB

- Juegas las 14 jornadas de la fase de grupos.
- Al terminar, se dividen los grupos y juegas la fase 2.
- La clasificación muestra tu grupo.
- Puedes ascender a DHA al terminar entre los dos primeros del Grupo A.

---

## 3. Interacción con DHA

- Si estás en DHA, la DHB se simula en segundo plano al final de temporada para decidir qué dos equipos suben.
- Si estás en DHB, la DHA se simula en segundo plano para decidir qué dos bajan.
- El playout de DHA sigue existiendo.

---

## 4. Archivos

- `manager/src/season.py`: fases DHB, ascensos, descensos y simulación de fondo.
- `manager/src/models.py`: `free_agents`, `dhb_phase`, `dhb_groups`, `dhb_group`.
- `manager/src/market.py`: fichajes de agentes libres.
- `manager/src/calendar.py`: calendario de ida o ida/vuelta.
- `manager/src/ui.py`: etiquetas de grupo y mercado.

---

## 5. Pruebas

`manager/src/tests/test_market.py` cubre:

- agentes libres de 1ª Andaluza;
- fichaje sin traspaso;
- creación de los dos grupos DHB;
- fase 2 con 168 partidos totales.

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado actual: **80 tests superados**.

---

## 6. Copa del Rey

- **8 equipos: los 8 mejores de DHA al acabar la primera vuelta.**
- **La DHB no participa.**
- Cuartos, semifinal, tercer/cuarto puesto y final a partido único en un fin de semana.
- Empate → shootout.
- El campeón recibe 50.000 € y confianza para la junta.
- La Copa no cuenta para la clasificación de liga.

## 7. EHL

- Torneo europeo de final a ocho.
- Participan los dos primeros de DHA, el campeón de Copa si es DHA y cinco clubes europeos modelo.
- Cuadro de cuartos, semifinal y final.
- Se simula al final de la temporada y el campeón aparece en el resumen.
- Si tu club se clasifica, aparece entre los participantes.

## 8. Pendiente de Fase 5A

- Descenso DHB → 1ª Andaluza (requiere simular esa liga).
- Sorteo de Copa con cabezas de serie.
- EHL interactiva con partidos en directo.
