"""Lightning ground-flash density (Ng) + surge-protection guidance.

Ng (flashes/km²/yr) is what NF C 15-100 (FR) uses to decide whether a surge
protector (parafoudre / SPD) is required; DE (VDE 0100) and BE (RGIE/AREI) have
their own rules. The ideal source is the NASA LIS/OTD satellite flash-density
climatology (global grid), but GHRC is Earthdata-gated / unreachable from the
pipeline host, so we use published climatology values per area with a country
fallback. **Indicative** — France's official regulatory Ng is the Météorage AQ map.

Advisory only: the definitive SPD requirement also depends on the supply type
(overhead vs. underground) and any lightning-protection system, which we don't know.
"""

# Ng (flashes/km²/yr) — indicative, from LIS/OTD climatology & national maps.
_AREA_NG = {
    "DE-39576": 0.8,   # Stendal, northern Germany — low
    "FR-12400": 2.0,   # Aveyron, S Massif Central — moderate
    "BE-1160": 1.5,    # Brussels — moderate
}
_COUNTRY_NG = {"DE": 1.0, "FR": 2.0, "BE": 1.5, "NL": 1.0, "ES": 2.5, "IT": 3.0}
_DEFAULT_NG = 1.5


def _risk(ng):
    return "low" if ng < 1.0 else "moderate" if ng <= 2.5 else "high"


def _guidance(country, ng):
    high, moderate = ng > 2.5, ng >= 1.0
    if country == "FR":
        std = "NF C 15-100 §534"
        if high:
            spd = "likely required"
            note = ("A type-2 surge protector (parafoudre) is generally warranted at this "
                    "lightning density, and mandatory when the installation is fed by an overhead line.")
        elif moderate:
            spd = "recommended"
            note = ("A type-2 surge protector (parafoudre) is recommended; it becomes mandatory "
                    "if the installation is fed by an overhead line.")
        else:
            spd = "optional"
            note = ("Low lightning density — a surge protector is advisable but not generally "
                    "mandatory (required if a lightning-protection system is present).")
    elif country == "DE":
        std, spd = "VDE 0100-443/534", "required"
        note = ("In Germany a type-2 SPD is effectively mandatory in new/renovated installations "
                "(VDE 0100-443/534), largely independent of Ng.")
    elif country == "BE":
        std = "RGIE / AREI"
        spd = "recommended" if moderate else "optional"
        note = "Belgium (RGIE/AREI): surge protection is recommended; check the current AREI edition for mandatory cases."
    else:
        std = "local wiring standard"
        spd = "recommended" if moderate else "optional"
        note = "Check the local wiring standard for surge-protection requirements."
    return std, spd, note


def fetch_lightning(area):
    aid = area.get("areaId", "")
    country = area.get("country")
    ng = _AREA_NG.get(aid, _COUNTRY_NG.get(country, _DEFAULT_NG))
    std, spd, note = _guidance(country, ng)
    return {
        "ng": ng, "unit": "flashes/km²/yr", "risk_level": _risk(ng),
        "standard": std, "spd_indication": spd, "note": note,
        "source": "Indicative — LIS/OTD satellite climatology & national lightning maps "
                  "(not the official regulatory value).",
    }


if __name__ == "__main__":
    import json
    for a in [{"areaId": "DE-39576", "country": "DE"},
              {"areaId": "FR-12400", "country": "FR"},
              {"areaId": "BE-1160", "country": "BE"}]:
        print(a["areaId"], json.dumps(fetch_lightning(a), ensure_ascii=False))
