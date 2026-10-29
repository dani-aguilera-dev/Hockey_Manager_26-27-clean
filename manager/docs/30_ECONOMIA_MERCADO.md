# Economía, marca y mercado global

Esta actualización convierte la economía en una capa de gestión con marca,
patrocinadores, taquilla, merchandising y campañas, y transforma el mercado en
un espacio único para jugadores, agentes libres y empleados de todas las ligas.

## Marca y patrocinios

`manager/src/commercial.py` calcula el **brand score** con:

- nivel de la competición;
- posición en la tabla;
- confianza de la afición y de la junta;
- academia;
- calidad de los cinco mejores jugadores;
- forma reciente;
- acuerdos de patrocinio activos;
- reputación comercial acumulada.

### Patrocinadores

Los acuerdos tienen:

- categoría: equipación, estadio, formación, salud, energía, banca, tecnología,
  alimentación, movilidad o seguros;
- nivel: local, regional, nacional o global;
- importe anual, pago por jornada, prima de firma y duración;
- requisito de marca;
- fecha de finalización y estado.

Las ofertas se generan según la marca y el momento del club. Se pueden firmar o
rechazar. Los acuerdos activos pagan cada jornada y suben la marca.

### Taquilla y merchandising

- El precio de la entrada se puede ajustar entre 8 y 40 €.
- Un precio alto reduce ligeramente la asistencia y puede enfriar la afición.
- El merchandising aporta ingresos por jornada ligados a la afición.
- Las campañas de marca cuestan caja y mejoran marca/afición.

### Staff comercial

Se añaden dos roles:

- **Director comercial**.
- **Responsable de marketing**.

Aparecen en el mercado de empleados y en la gestión del staff.

## Mercado global

`manager/src/market.py` ahora busca en **todas las ligas** del juego. Un club de
DHA puede fichar en Países Bajos, Bélgica, Alemania, Inglaterra, Argentina o
India, y los clubes internacionales pueden fichar entre sí.

### Filtros

- búsqueda por nombre, club, arquetipo o posición;
- liga;
- club;
- posición;
- edad mínima y máxima;
- overall mínimo y máximo;
- valor máximo;
- atributo concreto y mínimo;
- solo jugadores en venta;
- agentes libres;
- staff por rol, rating y salario.

### Agentes libres

El mercado separa a los jugadores sin club y permite negociar su firma sin
traspaso. Los agentes libres de 1ª Andaluza siguen entrando en el mercado.

### Staff

El mercado de empleados genera candidatos **ficticios** coherentes con la
categoría del club, con rol, rating, salario y contrato. Se pueden filtrar y
contratar.

### Ventas y lista de traspaso

Cada jugador propio puede:

- ponerse en venta;
- fijar un precio de salida;
- retirarse del mercado.

Durante las simulaciones diarias pueden llegar ofertas o no. La probabilidad
depende de:

- si está en la lista;
- su overall y rating;
- goles y rendimiento;
- edad;
- liga y valor de mercado;
- presupuesto de los clubes compradores.

Las ofertas caducan, se pueden aceptar o rechazar y se guardan en el historial.
La venta actualiza presupuesto, plantilla, liga del jugador y estado de la lista.

### Negociación

La ficha general del jugador se abre antes que el panel de negociación. La
negociación muestra edad, liga, rendimiento, contrato, presupuesto, precio de
salida, salario mínimo y una lectura del contexto de la operación.

## API

- `GET /api/commercial`
- `POST /api/commercial/offers/<id>`
- `POST /api/commercial/ticket`
- `POST /api/commercial/campaign`
- `GET /api/market` con filtros por query string.
- `POST /api/market/list/<player_id>`
- `POST /api/market/staff/hire`
- `GET /api/market/offers`
- `POST /api/market/offers/<offer_id>`

## Tests

Cobertura nueva:

- marca, patrocinios y campañas;
- mercado global y filtros avanzados;
- lista de traspaso y ofertas durante la simulación;
- staff ficticio contratable;
- ingresos comerciales en la contabilidad de jornada.

Total actual: **100 tests**.
