# Auditoría de clubes · Beta avanzada

Revisión de ubicación, descripción y fuente. Los clubes españoles se contrastaron con iSquad/RFEH, federaciones, Wikipedia y webs oficiales; los internacionales tienen fuente individual (Wikipedia o web oficial) y una descripción específica con ciudad, país, fundación, instalación y liga.

## España · DHA / DHB / 1ª Andaluza

| Club | Liga | Ciudad | Provincia | Comunidad | Fundación | Fuente |
| --- | --- | --- | --- | --- | ---: | --- |
| Atlètic Terrassa HC | DHA | Terrassa | Barcelona | Cataluña | 1952 | RFEH/iSquad |
| CD Terrassa Hockey | DHA | Matadepera | Barcelona | Cataluña | 1910 | https://visitvalles.com/es/portfolio_page/club-deportiu-terrassa-hockey/ |
| CH Carpesa | DHA | Valencia | Valencia | Comunidad Valenciana | 1971 | RFEH/iSquad |
| FC Barcelona | DHA | Barcelona | Barcelona | Cataluña | 1923 | RFEH/iSquad |
| Club Egara | DHA | Terrassa | Barcelona | Cataluña | 1935 | https://egara.es/ |
| RC Polo | DHA | Barcelona | Barcelona | Cataluña | 1897 | RFEH/iSquad |
| Real Club de Campo Villa de Madrid | DHA | Madrid | Madrid | Comunidad de Madrid | 1930 | RFEH/iSquad |
| Sanse Complutense | DHA | San Sebastián de los Reyes | Madrid | Comunidad de Madrid | 1965 | https://es.wikipedia.org/wiki/SPV_Complutense |
| Sardinero Hockey Club | DHA | Santander | Cantabria | Cantabria | 1984 | RFEH/iSquad |
| RS Tenis | DHA | Santander | Cantabria | Cantabria | 1906 | RFEH/iSquad |
| UD Taburiente | DHA | Las Palmas de Gran Canaria | Las Palmas | Canarias | 1980 | RFEH/iSquad |
| Junior FC | DHA | Sant Cugat del Vallès | Barcelona | Cataluña | 1917 | RFEH/iSquad |
| AD Rimas | DHB | Matadepera | Barcelona | Cataluña | — | https://resultadoshockey.isquad.es/equipo.php?seleccion=0&id_equipo=339&id=6308 |
| Aticos Inmobiliaria CH San Fernando | DHB | San Fernando | Cádiz | Andalucía | — | RFEH/iSquad |
| Castelldefels HC | DHB | Castelldefels | Barcelona | Cataluña | — | RFEH/iSquad |
| CD Giner de los Ríos | DHB | Valencia | Valencia | Comunidad Valenciana | 1993 | https://yosoynoticia.es/hockey/giner-de-los-rios-la-gran-familia-del-hockey-en-valencia |
| Club Hockey Madrid - Las Rozas | DHB | Las Rozas | Madrid | Comunidad de Madrid | — | https://www.chmlasrozas.es/es |
| Egara 1935 | DHB | Terrassa | Barcelona | Cataluña | 1935 | https://egara.es/ |
| HC Sant Cugat | DHB | Sant Cugat del Vallès | Barcelona | Cataluña | — | https://resultadoshockey.isquad.es/equipo_movil.php?id_equipo=26&id=6309 |
| Iluro HC | DHB | Mataró | Barcelona | Cataluña | — | https://ilurohc.com/ |
| Línia 22 Stern Motor | DHB | Terrassa | Barcelona | Cataluña | — | https://www.linia22.cat/historia/ |
| Pedralbes HC | DHB | Barcelona | Barcelona | Cataluña | — | https://www.fchockey.cat/club/7 |
| RC Jolaseta | DHB | Getxo | Bizkaia | País Vasco | — | RFEH/iSquad |
| Pozuelo | DHB | Pozuelo de Alarcón | Madrid | Comunidad de Madrid | — | RFEH/iSquad |
| Real Sociedad 1927 | DHB | Madrid | Madrid | Comunidad de Madrid | 1927 | https://resultadoshockey.isquad.es/equipo.php?seleccion=0&id_superficie=1&id_equipo=136&id=5867 |
| SPV | DHB | San Sebastián de los Reyes | Madrid | Comunidad de Madrid | — | https://es.wikipedia.org/wiki/SPV_Complutense |
| Universitat d'Alacant - San Vicente | DHB | San Vicente del Raspeig | Alicante | Comunidad Valenciana | — | RFEH/iSquad |
| Vallès Esportiu | DHB | Terrassa | Barcelona | Cataluña | — | https://athc.cat/category/vallesesportiu/ |
| Club de Hockey San Fernando | 1A | San Fernando | Cádiz | Andalucía | — | RFEH/iSquad |

## Internacional

Se revisaron **70 clubes** de Países Bajos, Bélgica, Alemania, Inglaterra, Argentina e India. Todos tienen `city`, `country`, `history` y `location_verified` en `data/international.json`.

## Corrección destacada

- **CD Giner de los Ríos**: Valencia (Comunidad Valenciana), fundado en 1993 en el Colegio Público Giner de los Ríos de Campanar. Fuente: [YoSoyNoticia](https://yosoynoticia.es/hockey/giner-de-los-rios-la-gran-familia-del-hockey-en-valencia).
- **AD Rimas**: Matadepera (Barcelona), juega en el CD Terrassa C2. Fuente: [RFEH/iSquad](https://resultadoshockey.isquad.es/equipo.php?seleccion=0&id_equipo=339&id=6308).
- **Real Sociedad 1927**: Madrid, Club de Campo Villa de Madrid. Fuente: [RFEH/iSquad](https://resultadoshockey.isquad.es/equipo.php?seleccion=0&id_superficie=1&id_equipo=136&id=5867).
- **Línia 22**: Terrassa, estadi Martí Colomer. Fuente: [Línia 22](https://www.linia22.cat/historia/).
- **Pedralbes HC**: Barcelona, RC Polo. Fuente: [FCHockey](https://www.fchockey.cat/club/7).
- **Iluro HC**: Mataró. Fuente: [Iluro HC](https://ilurohc.com/).
- **HC Sant Cugat**: Sant Cugat del Vallès. Fuente: [RFEH/iSquad](https://resultadoshockey.isquad.es/equipo_movil.php?id_equipo=26&id=6309).
- **SPV / Sanse Complutense**: San Sebastián de los Reyes. Fuente: [Wikipedia](https://es.wikipedia.org/wiki/SPV_Complutense).

## Criterio de aceptación

El test `test_clubs_have_verified_location_and_description` exige ciudad, provincia, historia y ubicación verificada para los 29 clubes españoles; además comprueba que Giner es Valencia y que los 70 clubes internacionales tienen ciudad, país e historia.
