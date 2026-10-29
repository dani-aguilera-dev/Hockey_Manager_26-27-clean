# Negociaciones

**Estado:** primera actualización implementada (2026-10-27).

## 1. Problema del sistema anterior

El mercado resolvía casi todo en una sola acción:

- oferta de compra → aceptar o rechazar;
- oferta recibida → aceptar o rechazar;
- renovación → aceptar o rechazar;
- sin contraofertas;
- sin rondas;
- sin paciencia;
- sin historial de la negociación;
- sin separar lo que pide el club de lo que pide el jugador.

Eso hacía que negociar fuera pulsar un botón y esperar una tirada, no una conversación.

## 2. Modelo nuevo

Cada negociación guarda:

```text
id, kind, status
player_id, player_name
club_id, club_name
round, max_rounds, patience
offer { fee, salary, years }
ask { fee, salary, years }
counter { fee, salary, years }
message
history[]
created, updated
```

Estados:

- `open`: hay una contraoferta sobre la mesa;
- `accepted`: acuerdo cerrado;
- `pending_window`: acuerdo cerrado, pendiente de apertura del mercado;
- `rejected`: la otra parte se ha cansado o ha rechazado;
- `walked`: el usuario se ha retirado.

## 3. Compra de jugadores

`start_transfer_negotiation` calcula dos exigencias separadas:

- **club vendedor**: precio de traspaso;
- **jugador**: salario anual.

El club pide más si el jugador es clave; pide menos si está en la lista de traspaso. El jugador pide más si su salario actual es alto, si es joven o si tiene buen rendimiento; pide menos si la relación con el entrenador es buena.

El usuario puede:

- aceptar la contraoferta;
- enviar otra contraoferta;
- retirarse.

Si se superan las rondas, la negociación se cierra.

## 4. Renovaciones

La renovación usa el mismo esquema:

- el jugador calcula su salario exigido;
- el usuario puede aceptar, contraofertar o retirarse;
- al aceptar, se actualiza salario y contrato;
- la operación queda en el historial del mercado.

## 5. Ofertas recibidas

Ahora una oferta recibida permite **contraofertar**:

- si el comprador puede pagar y la cifra es razonable, acepta;
- si no puede pagar, indica su límite;
- si la cifra es alta, responde con una contraoferta;
- la oferta se actualiza para que el usuario pueda aceptarla después.

## 6. Interfaz

- `MarketPlayer`: negociación por rondas, contraoferta, aceptar y retirarse.
- `Offers`: campo de contraoferta por cada oferta recibida.
- `Renew`: contraoferta salarial y aceptación.
- `Market`: tarjeta de negociaciones abiertas.

## 7. Persistencia y compatibilidad

`GameState.negotiations` se guarda en SQLite y tiene valor por defecto para partidas antiguas.

Las funciones antiguas (`make_transfer_offer`, `renew_contract`, `accept_incoming_offer`) se mantienen para no romper partidas ni tests. La interfaz nueva usa las funciones de `negotiation.py`.

## 8. Pendiente

- comisiones de agentes;
- cláusulas de rescisión y porcentajes de futura venta;
- cesiones;
- límite de masa salarial;
- aprobación de la junta para operaciones grandes;
- contraofertas de la IA con personalidad y paciencia variable;
- negociación de patrocinios y staff.

## 9. Pruebas

- compra con contraoferta y aceptación;
- retirada de negociación;
- renovación con contraoferta;
- contraoferta a una oferta recibida;
- persistencia de negociaciones;
- flujo API de negociación.
