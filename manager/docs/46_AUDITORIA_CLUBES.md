# Auditoría de clubes · Beta avanzada

Revisión de ubicación, descripción y fuente individual. Los 29 clubes españoles y los 70 internacionales tienen `source_url`, `description_verified` y una descripción específica con ciudad, país, fundación, instalación y liga.

## España · DHA / DHB / 1ª Andaluza

| Club | Liga | Ciudad | Provincia | Comunidad | Fundación | Fuente individual |
| --- | --- | --- | --- | --- | ---: | --- |
| Atlètic Terrassa HC | DHA | Terrassa | Barcelona | Cataluña | 1952 | https://es.wikipedia.org/wiki/Atl%C3%A8tic_Terrassa_Hockey_Club |
| CD Terrassa Hockey | DHA | Matadepera | Barcelona | Cataluña | 1910 | https://visitvalles.com/es/portfolio_page/club-deportiu-terrassa-hockey/ |
| CH Carpesa | DHA | Valencia | Valencia | Comunidad Valenciana | 1971 | https://resultadoshockey.isquad.es/equipo.php?id_equipo=3926&id=9359 |
| FC Barcelona | DHA | Barcelona | Barcelona | Cataluña | 1923 | https://es.wikipedia.org/wiki/F%C3%BAtbol_Club_Barcelona_%28hockey_hierba%29 |
| Club Egara | DHA | Terrassa | Barcelona | Cataluña | 1935 | https://egara.es/ |
| RC Polo | DHA | Barcelona | Barcelona | Cataluña | 1897 | https://es.wikipedia.org/wiki/Real_Club_de_Polo |
| Real Club de Campo Villa de Madrid | DHA | Madrid | Madrid | Comunidad de Madrid | 1930 | https://es.wikipedia.org/wiki/Real_Club_de_Campo_Villa_de_Madrid |
| Sanse Complutense | DHA | San Sebastián de los Reyes | Madrid | Comunidad de Madrid | 1965 | https://es.wikipedia.org/wiki/SPV_Complutense |
| Sardinero Hockey Club | DHA | Santander | Cantabria | Cantabria | 1984 | https://es.wikipedia.org/wiki/Sardinero_Hockey_Club |
| RS Tenis | DHA | Santander | Cantabria | Cantabria | 1906 | https://es.wikipedia.org/wiki/Real_Sociedad_de_Tenis_de_La_Magdalena |
| UD Taburiente | DHA | Las Palmas de Gran Canaria | Las Palmas | Canarias | 1980 | https://es.wikipedia.org/wiki/Uni%C3%B3n_Deportiva_Taburiente |
| Junior FC | DHA | Sant Cugat del Vallès | Barcelona | Cataluña | 1917 | https://resultadoshockey.isquad.es/equipo.php?id_equipo=22&id=9359 |
| AD Rimas | DHB | Matadepera | Barcelona | Cataluña | — | https://resultadoshockey.isquad.es/equipo.php?seleccion=0&id_equipo=339&id=6308 |
| Aticos Inmobiliaria CH San Fernando | DHB | San Fernando | Cádiz | Andalucía | — | https://resultadoshockey.isquad.es/equipo.php?seleccion=0&id_superficie=1&id_equipo=3891&id=9367 |
| Castelldefels HC | DHB | Castelldefels | Barcelona | Cataluña | — | https://resultadoshockey.isquad.es/equipo.php?id_equipo=2934&id=9368 |
| CD Giner de los Ríos | DHB | Valencia | Valencia | Comunidad Valenciana | 1993 | https://yosoynoticia.es/hockey/giner-de-los-rios-la-gran-familia-del-hockey-en-valencia |
| Club Hockey Madrid - Las Rozas | DHB | Las Rozas | Madrid | Comunidad de Madrid | — | https://www.chmlasrozas.es/es |
| Egara 1935 | DHB | Terrassa | Barcelona | Cataluña | 1935 | https://egara.es/ |
| HC Sant Cugat | DHB | Sant Cugat del Vallès | Barcelona | Cataluña | — | https://resultadoshockey.isquad.es/equipo_movil.php?id_equipo=26&id=6309 |
| Iluro HC | DHB | Mataró | Barcelona | Cataluña | — | https://ilurohc.com/ |
| Línia 22 Stern Motor | DHB | Terrassa | Barcelona | Cataluña | — | https://www.linia22.cat/historia/ |
| Pedralbes HC | DHB | Barcelona | Barcelona | Cataluña | — | https://www.fchockey.cat/club/7 |
| RC Jolaseta | DHB | Getxo | Bizkaia | País Vasco | — | https://es.wikipedia.org/wiki/Real_Club_Jolaseta |
| Pozuelo | DHB | Pozuelo de Alarcón | Madrid | Comunidad de Madrid | — | https://es.wikipedia.org/wiki/Club_Hockey_Pozuelo |
| Real Sociedad 1927 | DHB | Madrid | Madrid | Comunidad de Madrid | 1927 | https://resultadoshockey.isquad.es/equipo.php?seleccion=0&id_superficie=1&id_equipo=136&id=5867 |
| SPV | DHB | San Sebastián de los Reyes | Madrid | Comunidad de Madrid | — | https://es.wikipedia.org/wiki/SPV_Complutense |
| Universitat d'Alacant - San Vicente | DHB | San Vicente del Raspeig | Alicante | Comunidad Valenciana | — | https://resultadoshockey.isquad.es/equipo.php?id_equipo=1868&id=9368 |
| Vallès Esportiu | DHB | Terrassa | Barcelona | Cataluña | — | https://athc.cat/category/vallesesportiu/ |
| Club de Hockey San Fernando | 1A | San Fernando | Cádiz | Andalucía | — | https://es.wikipedia.org/wiki/Club_de_Hockey_San_Fernando |

## Internacional

Se revisaron **70 clubes** de Países Bajos, Bélgica, Alemania, Inglaterra, Argentina e India. Todos tienen `city`, `country`, `history`, `source_url` y `description_verified` en `data/international.json`.

Fuentes: Wikipedia del club o web oficial de cada entidad; para franquicias de la Hockey India League, la web oficial de la competición.

## Correcciones destacadas

- **CD Giner de los Ríos**: Valencia (Comunidad Valenciana), fundado en 1993 en el Colegio Público Giner de los Ríos de Campanar. Fuente: [YoSoyNoticia](https://yosoynoticia.es/hockey/giner-de-los-rios-la-gran-familia-del-hockey-en-valencia).
- **Santa Bárbara Hockey Club**: Gonnet, La Plata (Buenos Aires), fundado en 1974. Fuente: [Wikipedia](https://es.wikipedia.org/wiki/Santa_B%C3%A1rbara_Hockey_Club).
- **Royal HC Namur**: Namur, fundado en 1912. Fuente: [Hockey Namur](https://www.hockeynamur.be/).
- **Münchner SC**: Múnich, fundado en 1896. Fuente: [Münchner Sportclub](https://www.muenchner-sportclub.de/).
- **Royal Herakles HC**: Lier, fundado en 1921. Fuente: [Herakles](http://www.herakles.be).

## Criterio de aceptación

El test `test_clubs_have_verified_location_and_description` exige que los 29 clubes españoles y los 70 internacionales tengan ciudad, país/provincia, historia específica, `source_url` y `description_verified`. También comprueba el caso Giner y que las historias internacionales tengan contenido suficiente.
