"""Drinking-water quality — best-effort, France only (Hub'Eau).

France publishes tap-water sampling results via Hub'Eau `qualite_eau_potable`,
keyed by INSEE commune code (periodic samples, not continuous). We map the area's
postal code → INSEE commune(s) via geo.api.gouv.fr, pull recent results for a few
headline parameters, and summarise latest value + limit + overall compliance.

DE/BE have no unified open API → fetch_water returns None (dashboard shows a note).
"""
import requests

GEO_URL = "https://geo.api.gouv.fr/communes"
HUBEAU = "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/resultats_dis"

# key, name-substrings to match, regulatory limit, fallback unit
PARAMS = [
    ("nitrates", ["Nitrates"], 50.0, "mg/L"),
    ("hardness", ["hydrotimétrique", "Dureté"], None, "°f"),
    ("ph", ["pH"], None, ""),
    ("ecoli", ["Escherichia coli"], 0.0, "n/100mL"),
    ("coliforms", ["coliformes"], 0.0, "n/100mL"),
]


def _get(url, params):
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _insee_codes(postal):
    j = _get(GEO_URL, {"codePostal": postal, "fields": "code,nom"})
    return [(c["code"], c.get("nom", "")) for c in (j or [])]


def fetch_water(area, max_results=400):
    if area.get("country") != "FR":
        return None
    codes = _insee_codes(area["postalCode"])
    if not codes:
        return None
    code, nom = codes[0]
    j = _get(HUBEAU, {"code_commune": code, "size": max_results, "sort": "desc",
                      "fields": "libelle_parametre,resultat_numerique,libelle_unite,"
                                "date_prelevement,conclusion_conformite_prelevement"})
    data = j.get("data", [])
    if not data:
        return None

    params_out = []
    for key, needles, limit, unit in PARAMS:
        rows = [d for d in data
                if d.get("resultat_numerique") is not None
                and any(n.lower() in (d.get("libelle_parametre") or "").lower() for n in needles)]
        if not rows:
            continue
        rows.sort(key=lambda d: d.get("date_prelevement") or "", reverse=True)
        latest = rows[0]
        trend = [[r["date_prelevement"][:10], round(float(r["resultat_numerique"]), 3)]
                 for r in rows[:12]][::-1]
        params_out.append({"key": key, "label": latest["libelle_parametre"],
                           "value": round(float(latest["resultat_numerique"]), 3),
                           "unit": latest.get("libelle_unite") or unit, "limit": limit,
                           "date": latest["date_prelevement"][:10], "trend": trend})

    conf = [d["conclusion_conformite_prelevement"] for d in data
            if d.get("conclusion_conformite_prelevement")]
    conform = sum(1 for c in conf if "conforme" in c.lower() and "non conforme" not in c.lower())
    dates = [d["date_prelevement"][:10] for d in data if d.get("date_prelevement")]
    return {"source": "Hub'Eau — qualité de l'eau potable", "commune": nom, "insee": code,
            "compliance_pct": round(100 * conform / len(conf), 1) if conf else None,
            "n_samples": len(data),
            "sampled_span": [min(dates), max(dates)] if dates else None,
            "parameters": params_out}


if __name__ == "__main__":
    import json
    print(json.dumps(fetch_water({"country": "FR", "postalCode": "12400", "name": "x"}), indent=2, ensure_ascii=False)[:1200])
