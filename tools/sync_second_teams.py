"""Sincroniza los segundos equipos regionales con iSquad y el Excel.

- Añade una ficha por cada equipo filial que el Excel identifica en una liga
  regional (aunque no tenga plantilla pública).
- Descarga la plantilla masculina de iSquad cuando existe.
- No duplica jugadores: descarta cualquier nombre que ya aparezca en otra
  plantilla (primer equipo, filial o categoría superior).
"""

from __future__ import annotations

import csv
import json
import re
import time
import unicodedata
from pathlib import Path

from fetch_lower_divisions import fetch, parse_roster, team_gender, team_page_url

ROOT = Path(__file__).resolve().parents[1]
LOWER = ROOT / "tools" / "lower_divisions_players.csv"
PLAYERS = ROOT / "tools" / "player_attributes_v2.csv"
REGIONAL = ROOT / "manager" / "data" / "regional_teams.json"

# Equipos filiales regionales. Los que tienen id_equipo/id_torneo están en
# iSquad; los demás se dejan documentados pero sin inventar plantilla.
SECOND_TEAMS = [
    # Liga Norte
    {
        "id": "reg-real-club-jolaseta-b",
        "name": "REAL CLUB JOLASETA B",
        "club": "Real Club Jolaseta",
        "parent_club": "RC Jolaseta",
        "league": "1N",
        "league_text": "Primera División Masculina - Liga Norte",
        "city": "Getxo",
        "community": "País Vasco",
        "province": "Bizkaia",
        "id_equipo": 3936,
        "id_torneo": 9450,
    },
    {
        "id": "reg-rst-magdalena",
        "name": "RST MAGDALENA",
        "club": "Real Sociedad de Tenis de La Magdalena",
        "parent_club": "RS Tenis",
        "league": "1N",
        "league_text": "Primera División Masculina - Liga Norte",
        "city": "Santander",
        "community": "Cantabria",
        "province": "Cantabria",
        "id_equipo": 3956,
        "id_torneo": 9450,
    },
    {
        "id": "reg-sardinero-hc-b",
        "name": "SARDINERO HC B",
        "club": "Sardinero Hockey Club",
        "parent_club": "Sardinero HC",
        "league": "1N",
        "league_text": "Primera División Masculina - Liga Norte",
        "city": "Santander",
        "community": "Cantabria",
        "province": "Cantabria",
        "id_equipo": 3958,
        "id_torneo": 9450,
    },
    # Andalucía
    {
        "id": "san-fernando-andaluza",
        "name": "CLUB DE HOCKEY SAN FERNANDO B",
        "base_name": "Club de Hockey San Fernando",
        "club": "Club Hockey San Fernando",
        "parent_club": "Aticos Inmobiliaria CH San Fernando",
        "league": "1A",
        "league_text": "Campeonato de Andalucía - Primera División Masculina",
        "city": "San Fernando",
        "community": "Andalucía",
        "province": "Cádiz",
        "id_equipo": 3939,
        "id_torneo": 9429,
        "existing": True,
    },
    {
        "id": "reg-chp-benalmadena-b",
        "name": "CHP BENALMÁDENA B",
        "club": "Club Hockey Polideportivo Benalmádena",
        "parent_club": "RH Privé Benalmádena",
        "league": "1A",
        "league_text": "Campeonato de Andalucía - Primera División Masculina",
        "city": "Benalmádena",
        "community": "Andalucía",
        "province": "Málaga",
        "id_equipo": 4065,
        "id_torneo": 9429,
    },
    # Madrid
    {
        "id": "reg-ch-madrid-las-rozas-azul",
        "name": "CLUB HOCKEY MADRID-LAS ROZAS AZUL",
        "club": "Club Hockey Madrid - Las Rozas",
        "parent_club": "CH Madrid-Las Rozas",
        "league": "1M",
        "league_text": "Primera División Masculina Hierba - Liga Madrid",
        "city": "Las Rozas de Madrid",
        "community": "Madrid",
        "province": "Madrid",
        "id_equipo": 195,
        "id_torneo": 9436,
    },
    {
        "id": "reg-ch-madrid-las-rozas-blanco",
        "name": "CLUB HOCKEY MADRID-LAS ROZAS BLANCO",
        "club": "Club Hockey Madrid - Las Rozas",
        "parent_club": "CH Madrid-Las Rozas",
        "league": "1M",
        "league_text": "Primera División Masculina Hierba - Liga Madrid",
        "city": "Las Rozas de Madrid",
        "community": "Madrid",
        "province": "Madrid",
        "id_equipo": 2070,
        "id_torneo": 9436,
    },
    {
        "id": "reg-pozuelo-b",
        "name": "POZUELO B",
        "club": "Club Hockey Pozuelo",
        "parent_club": "Pozuelo",
        "league": "1M",
        "league_text": "Primera División Masculina Hierba - Liga Madrid",
        "city": "Pozuelo de Alarcón",
        "community": "Madrid",
        "province": "Madrid",
        "id_equipo": 3985,
        "id_torneo": 9436,
    },
    {
        "id": "reg-real-sociedad-1927-a",
        "name": "REAL SOCIEDAD 1927 A",
        "club": "Real Club de Campo Villa de Madrid",
        "parent_club": "Real Club de Campo",
        "league": "1M",
        "league_text": "Primera División Masculina Hierba - Liga Madrid",
        "city": "Madrid",
        "community": "Madrid",
        "province": "Madrid",
        "id_equipo": 4032,
        "id_torneo": 9436,
    },
    {
        "id": "reg-real-sociedad-1927-b",
        "name": "REAL SOCIEDAD 1927 B",
        "club": "Real Club de Campo Villa de Madrid",
        "parent_club": "Real Club de Campo",
        "league": "1M",
        "league_text": "Primera División Masculina Hierba - Liga Madrid",
        "city": "Madrid",
        "community": "Madrid",
        "province": "Madrid",
        "id_equipo": 4145,
        "id_torneo": 9436,
    },
    {
        "id": "reg-sanse-complutense-b",
        "name": "SANSE COMPLUTENSE B",
        "club": "Sanse Complutense Club de Hockey",
        "parent_club": "Sanse Complutense",
        "league": "1M",
        "league_text": "Primera División Masculina Hierba - Liga Madrid",
        "city": "San Sebastián de los Reyes",
        "community": "Madrid",
        "province": "Madrid",
        "id_equipo": 293,
        "id_torneo": 9436,
    },
    # Canarias
    {
        "id": "reg-ud-taburiente-b",
        "name": "UD TABURIENTE B",
        "club": "Unión Deportiva Taburiente",
        "parent_club": "UD Taburiente",
        "league": "1C",
        "league_text": "Campeonato de Canarias - 1ª División Masculina",
        "city": "Las Palmas de Gran Canaria",
        "community": "Canarias",
        "province": "Las Palmas",
        "id_equipo": 395,
        "id_torneo": 9400,
    },
    # Comunidad Valenciana (FHCV; sin ficha iSquad)
    {
        "id": "reg-ch-carpesa-b",
        "name": "CH CARPESA B",
        "club": "Club Hockey Carpesa",
        "parent_club": "CH Carpesa",
        "league": "1V",
        "league_text": "1ª División Masculina Hockey Hierba (FHCV)",
        "city": "Carpesa (Valencia)",
        "community": "Comunidad Valenciana",
        "province": "Valencia",
        "source": "FHCV",
    },
    {
        "id": "reg-valencia-ch-1924",
        "name": "VALENCIA CH 1924",
        "club": "Valencia Club de Hockey",
        "parent_club": "Valencia CH",
        "league": "1V",
        "league_text": "1ª División Masculina Hockey Hierba (FHCV)",
        "city": "Valencia",
        "community": "Comunidad Valenciana",
        "province": "Valencia",
        "source": "FHCV",
    },
    # Cataluña (FCH; sin ficha iSquad)
    {
        "id": "reg-cd-terrassa-b",
        "name": "CD TERRASSA B",
        "club": "Club Deportivo Terrassa Hockey",
        "parent_club": "CD Terrassa",
        "league": "SUP",
        "league_text": "Superlliga Catalana Masculina",
        "city": "Terrassa",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
    {
        "id": "reg-ehc",
        "name": "EHC",
        "club": "Club Egara",
        "parent_club": "Club Egara",
        "league": "SUP",
        "league_text": "Superlliga Catalana Masculina",
        "city": "Terrassa",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
    {
        "id": "reg-atletic-terrassa-b",
        "name": "ATLÈTIC TERRASSA B",
        "club": "Atlètic Terrassa Hockey Club",
        "parent_club": "Atlètic Terrassa",
        "league": "SUP",
        "league_text": "Superlliga Catalana Masculina",
        "city": "Terrassa",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
    {
        "id": "reg-egara-1935-sup",
        "name": "EGARA 1935 B",
        "club": "Club Egara",
        "parent_club": "Club Egara",
        "league": "SUP",
        "league_text": "Superlliga Catalana Masculina",
        "city": "Terrassa",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
    {
        "id": "reg-valles-esportiu",
        "name": "VALLÈS ESPORTIU B",
        "club": "Atlètic Terrassa Hockey Club",
        "parent_club": "Atlètic Terrassa",
        "league": "SUP",
        "league_text": "Superlliga Catalana Masculina",
        "city": "Terrassa",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
    {
        "id": "reg-fc-barcelona-b",
        "name": "FC BARCELONA B",
        "club": "Futbol Club Barcelona",
        "parent_club": "FC Barcelona",
        "league": "SUP",
        "league_text": "Superlliga Catalana Masculina",
        "city": "Barcelona",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
    {
        "id": "reg-diagonal-hc",
        "name": "DIAGONAL HC",
        "club": "Reial Club de Polo de Barcelona",
        "parent_club": "RC Polo",
        "league": "SUP",
        "league_text": "Superlliga Catalana Masculina",
        "city": "Barcelona",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
    # Primera Catalana
    {
        "id": "reg-atletic-1952",
        "name": "ATLETIC 1952",
        "club": "Atlètic Terrassa Hockey Club",
        "parent_club": "Atlètic Terrassa",
        "league": "CAT1",
        "league_text": "Campionat de Catalunya 1ª Masculina (Primera Catalana)",
        "city": "Terrassa",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
    {
        "id": "reg-can-salas",
        "name": "CAN SALAS",
        "club": "Atlètic Terrassa Hockey Club",
        "parent_club": "Atlètic Terrassa",
        "league": "CAT1",
        "league_text": "Campionat de Catalunya 1ª Masculina (Primera Catalana)",
        "city": "Terrassa",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
    {
        "id": "reg-rc-polo-b",
        "name": "RC POLO B",
        "club": "Reial Club de Polo de Barcelona",
        "parent_club": "RC Polo",
        "league": "CAT1",
        "league_text": "Campionat de Catalunya 1ª Masculina (Primera Catalana)",
        "city": "Barcelona",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
    {
        "id": "reg-hc-sant-cugat-b",
        "name": "HC SANT CUGAT B",
        "club": "Hoquei Club Sant Cugat",
        "parent_club": "HC Sant Cugat",
        "league": "CAT1",
        "league_text": "Campionat de Catalunya 1ª Masculina (Primera Catalana)",
        "city": "Sant Cugat del Vallès",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
    {
        "id": "reg-club-egara-b",
        "name": "CLUB EGARA B",
        "club": "Club Egara",
        "parent_club": "Club Egara",
        "league": "CAT1",
        "league_text": "Campionat de Catalunya 1ª Masculina (Primera Catalana)",
        "city": "Terrassa",
        "community": "Cataluña",
        "province": "Barcelona",
        "source": "FCH",
    },
]


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def main() -> None:
    rows = list(csv.DictReader(LOWER.open(encoding="utf-8-sig")))
    fieldnames = list(rows[0].keys())
    used_names = set()
    with PLAYERS.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            name = norm(row.get("jugador", ""))
            if name:
                used_names.add(name)

    metadata = json.loads(REGIONAL.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in metadata}
    by_name = {norm(item["name"]): item for item in metadata}
    added: list[dict] = []

    for team in SECOND_TEAMS:
        item = by_id.get(team["id"]) or by_name.get(norm(team["name"]))
        meta = {
            "id": team["id"],
            "name": team["name"],
            "club": team["club"],
            "league": team["league"],
            "league_text": team["league_text"],
            "city": team.get("city", ""),
            "community": team.get("community", ""),
            "province": team.get("province", ""),
            "stadium_name": "",
            "stadium_capacity": 300,
            "is_second_team": True,
            "parent_club": team["parent_club"],
            "base_name": team.get("base_name", ""),
            "source": team.get("source", "iSquad"),
        }
        if item is None:
            metadata.append(meta)
            by_id[team["id"]] = meta
            by_name[norm(team["name"])] = meta
        else:
            item.update({key: value for key, value in meta.items() if key != "id"})

        if "id_equipo" not in team or team.get("existing"):
            print(f"METADATA {team['name']} (sin descarga; ficha existente o fuente federativa)")
            continue

        url = team_page_url(team)
        try:
            html = fetch(url)
            gender = team_gender(html)
            players = parse_roster(html)
        except Exception as exc:
            print(f"ERROR {team['name']}: {exc}")
            continue
        print(f"{team['name']}: género={gender}, jugadores={len(players)}")
        if gender != "M":
            print("  descartado: la ficha no es masculina")
            continue
        for player in players:
            name_key = norm(player["name"])
            if not name_key or name_key in used_names:
                continue
            used_names.add(name_key)
            row = {key: "" for key in fieldnames}
            row.update(
                {
                    "liga": team["league_text"],
                    "liga_code": team["league"],
                    "equipo": team["name"],
                    "club": team["club"],
                    "perfil": player["profile"],
                    "jugador": player["name"],
                    "edad": player["age"],
                    "goles": player["goals"],
                    "goles_num": player["goals"],
                    "imagen_url": player["photo_remote"],
                    "team_url": url,
                    "imagen_ok": bool(player["photo_remote"]),
                    "pos": "",
                    "src": "Estimada",
                    "conf": "Baja",
                    "pos_fecha": "2026-10-27",
                    "pos_nota": "Segundo equipo; posición estimada. Ficha masculina iSquad.",
                    "source_team_id": team["id_equipo"],
                }
            )
            added.append(row)
        time.sleep(0.15)

    REGIONAL.write_text(json.dumps(metadata, ensure_ascii=False, indent=1), encoding="utf-8")
    with LOWER.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writerows(added)
    print(f"\nJugadores añadidos: {len(added)}")
    print(f"Equipos regionales documentados: {len(metadata)}")


if __name__ == "__main__":
    main()
