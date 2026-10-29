# Fuentes de staff y junta directiva DHA

**Fecha de corte:** 2026-10-20.
**Ámbito:** solo DHA masculina 2026-27.

Los campos `source` y `confidence` de `staff_dha.json` indican el origen de cada nombre:

- `source: modelo` + `confidence: baja` → nombre inventado para completar el rol. No debe usarse como dato real.
- `source: <web>` + `confidence: media/alta` → nombre encontrado en una fuente pública, pero el rol exacto o la vigencia pueden ser aproximados.
- Los cargos de junta directiva se han estructurado siempre en seis roles (presidente, vicepresidente, secretario, tesorero, vocal de hockey y vocal social). Cuando no había fuente para todos, se han completado con nombres de modelo.

## Fuentes utilizadas

| Club | Dato | Fuente | Confianza |
|---|---|---|---|
| Atlètic Terrassa HC | Presidente: Josep Maria Biosca Bertran | Fundació Damm | Alta |
| CD Terrassa Hockey | Presidente: Gabriel Pirla Teixidó | cdterrassa.cat (junio 2026) | Alta |
| CD Terrassa Hockey | Ramon Rius i Sanllehí, entrenador DHA | cdterrassa.cat | Media |
| Club Egara | Presidente: Josep Ejarque Guillamat | iSquad/RFEH y Mon Terrassa | Alta |
| RC Polo | Junta directiva completa | rcpolo.com/junta-directiva | Alta |
| Junior FC | Junta directiva completa | junior.cat/juntadirectiva | Alta |
| Real Club de Campo | Consejo de Administración | ccvm.es/consejo-de-administracion | Alta |
| Real Club de Campo | Dirección técnica de hockey: Eduardo Aguilar | ccvm.es/deportes/hockey/contacto | Media |
| CH Carpesa | Presidente: Andrés Vallés | yosoynoticia.es | Alta |
| Sanse Complutense | Presidente: Jorge Romero | MARCA | Alta |
| Sanse Complutense | Jorge Donoso, director deportivo | Cadena SER | Media |
| Sardinero HC | Presidente: Pablo Galán Fernández | iSquad | Alta |
| Sardinero HC | Ángel Laso y Manuel González, cuerpo técnico | cantabria.es | Media |
| RS Tenis | Presidente: Eduardo Mora Monte | rstenis.com | Alta |
| UD Taburiente | Suso Martín, entrenador masculino | La Provincia | Media |
| FC Barcelona | Junta directiva: Joan Laporta y nombres de su consejo | fcbarcelona.es | Media |
| FC Barcelona | Staff de hockey hierba | No encontrado con fiabilidad | Modelo |

## Limitaciones

- No hay una base pública completa y actualizada de staff técnico de todos los clubes DHA.
- Los roles de preparador físico, entrenador de porteros, analista, ojeador y fisioterapeuta son, en su mayoría, **modelos** para que el juego funcione.
- La junta directiva puede cambiar después de la fecha de corte.
- Para una versión pública o comercial habría que validar cada nombre con el club y separar claramente dato real de dato de simulación.
