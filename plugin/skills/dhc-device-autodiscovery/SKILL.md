---
name: dhc-device-autodiscovery
description: Discover physical smart-home devices from on-site gateways (the OpenCCU XML API and a Philips Hue bridge on the site's LAN) and emit inventory CSVs (the Portal's import format) plus product images, which go into a seller's catalogue on the digitalhome.cloud marketplace (ADR 0016). Trigger this skill for "auto-discover devices", "fetch inventory from CCU", "scan the Hue bridge", "add a new device type to the catalogue", "rerun the inventory", "put the discovered devices into the marketplace", or when extending `build_inventory_from_openccu.py`, `build_inventory_from_huebridge.py`, `download_device_images.py`, or `upload_catalogue_images.py` under `experimental/catalogue/`. Do NOT trigger for editing single marketplace articles in the Portal (Inventory → Marketplace), nor for the A-Box / SmartHome instance work that lives in the Designer's design page.
---

# DHC Device Auto-Discovery

This skill owns the **physical-device discovery → inventory CSV + images →
marketplace** pipeline that lives under `experimental/catalogue/`. It exists so that a real
site (currently DLAB5, but designed to generalise) can produce ready-to-import
marketplace articles and matching product images without hand-typing each
model into the Portal's article form.

## When to use this skill

Trigger on any of:

- "Auto-discover the devices on this network."
- "Fetch the inventory from the CCU / Hue bridge / KNX line."
- "Add a new device type to the catalogue."
- "Re-run the inventory now that we paired a new Hue light."
- "Upload the catalogue images to S3."
- "Why is `HmIP-XYZ` showing up as `Unknown` brand?"
- Edits to any file in `experimental/catalogue/build_inventory_*.py`,
  `download_device_images.py`, `upload_catalogue_images.py`, the per-site
  CSVs, or `images/`.

Do **not** trigger for:

- Editing `repos/portal/src/components/DeviceModelForm.js` or
  `DeviceCatalogue.js` (the Portal's Marketplace tab).
- A-Box / instance-data work (devices placed in a SmartHome design — that's
  the Designer's design page, not the catalogue).
- Editing the T-Box (Brick + DHC-core ontology — use
  `dhc-ontology-explorer` for that).

## Where files live

```
experimental/catalogue/
  build_inventory_from_openccu.py    # HomeMatic CCU3 (<ccu-host>)
  build_inventory_from_huebridge.py  # Philips Hue bridge (<hue-host>)
  download_device_images.py          # pulls device PNGs from the CCU
  upload_catalogue_images.py         # RETIRED: wrote public/catalogue/, nothing reads it
  device-inventory-DLAB5.csv         # CCU rows, one per physical device
  device-inventory-DLAB5-hue.csv     # Hue rows: the lights and the bridge
  device-inventory-template.csv      # schema reference (do not modify)
  images/                            # local PNG mirror
```

Each script is **stdlib-only Python 3** by intent — no `pip install` needed.

## Schema

All inventory CSVs share an 18-column header (see
`experimental/catalogue/device-inventory-template.csv` for the canonical
order). Two columns are load-bearing for downstream consumption:

| Column        | Source of truth                                                                                       |
|---------------|-------------------------------------------------------------------------------------------------------|
| `category`    | One of the **DeviceCategory enum IDs** declared in `repos/core/amplify/data/resource.ts`              |
| `deviceType`  | One of the **sub-type labels** declared in `repos/designer/src/constants/deviceTypes.js`              |

Five enum IDs are available today:

```
COMPUTING_IT, CONTROLLERS_AUTOMATION, FACILITIES_APPLIANCES,
MEDIA_COMMUNICATION, SECURITY_MONITORING
```

Sub-type labels per category are listed in `DEVICE_CATEGORIES[*].subTypes[*].label`.
When you add a new device type to either catalogue dict, the
`(category, deviceType)` pair **must** match those constants — that's what
the Portal's article form writes back and what the marketplace stores as
`dhp:category` / `dhp:deviceType` (the shapes allow only the known categories).

## Canonical mapping cheat sheet (current)

| What the device does                              | category                  | deviceType            |
|---------------------------------------------------|---------------------------|-----------------------|
| Thermostat, radiator valve, climate sensor        | FACILITIES_APPLIANCES     | HVAC Systems          |
| Hub, gateway, central control unit, push-button   | CONTROLLERS_AUTOMATION    | Smart Home Hubs       |
| Switch, dimmer, plug, light, blind/shutter, power | FACILITIES_APPLIANCES     | Power Management      |
| Smoke, motion, contact, weather, siren            | SECURITY_MONITORING       | Environmental Sensors |

The DHC app taxonomy is intentionally coarse (it's an IT-asset-style
classification, not a smart-home device-level one). Brick semantic anchors live
in the `compatibleClasses` column instead (e.g. `brick:Dimmer;brick:Light`).
If the user asks "where's the Lighting category?" — there isn't one; lights map
to `Power Management` because they are driven through it.

## Capability flags

`DeviceModelForm` exposes four flat booleans (see `CAPS` in the form):

| Flag                      | Means                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------|
| `hasActorCapability`      | Drives a physical output (relay, dimmer, motor, siren, valve, light)                      |
| `hasSensorCapability`     | Reports environmental or input state (contact, motion, button, power, temperature)        |
| `hasControllerCapability` | Coordinates other devices autonomously (gateway, hub, thermostat with its own schedule)   |
| `hasIOTCapability`        | **Wireless / IP-reachable** — the device is connectable over a wireless protocol or IP (Zigbee, Z-Wave, WiFi, BLE, BidCos-RF, HmIP, Thread, etc.). Tick this on essentially every device discovered through these auto-discovery flows, because they only see devices that came in over a wireless gateway. |

The current `DEVICE_TYPE_CATALOGUE` / `HUE_MODEL_CATALOGUE` dicts only carry
`actor` / `sensor` / `controller` keys and the inventory CSV header has no
`hasIOTCapability` column. **Next time the scripts are extended**, add:

1. An `"iot": True` key per entry in both catalogue dicts (default `True` for
   anything coming off these gateways).
2. A `hasIOTCapability` column to `CSV_HEADER` (positioned next to the other
   capability booleans, before `serialNumber`).
3. The corresponding `"true"/"false"` cell in `row_for_device` / `row_for_light` /
   `row_for_bridge`.

Until that lands, an admin registering an auto-discovered model through
`DeviceModelForm` should manually tick the **IOT** checkbox.

## End-to-end flow

```bash
cd experimental/catalogue

# 1) HomeMatic CCU3 — sid is short-lived; pull a fresh one from the WebUI:
python3 build_inventory_from_openccu.py \
    --sid '@<XMLAPI-SESSION-ID>@' \
    --output device-inventory-DLAB5.csv \
    --smarthome-id DE-DEMO

# 2) Philips Hue bridge — first time, mint a username (press Link button):
python3 build_inventory_from_huebridge.py --mint
# Then for every subsequent run, reuse that username:
python3 build_inventory_from_huebridge.py \
    --key <USERNAME> \
    --output device-inventory-DLAB5-hue.csv

# 3) Pull the CCU-shipped product images (sourced from /config/img/devices/250/):
python3 download_device_images.py --output-dir images

```

### 4) Into the marketplace

The device catalogue is the **marketplace** (ADR 0016): one catalogue graph
per seller, edited by that seller's editors (Cognito group `market-<seller>`,
with an authenticator app). The old `DeviceModel` table and its
`public/catalogue/devices/…` files are retired, so **`upload_catalogue_images.py`
has no reader any more — do not run it.**

1. The CSVs are already in the Portal's import format (same columns as
   `repos/portal/src/utils/csvTemplate.js`). In the Portal: Inventory →
   **Import**, upload the CSV, then **Stage 1** saves each model as an
   article of a seller you edit (usually `digitalhome-cloud`, the curated
   catalogue; a dhc-admin creates it under Marketplace → **Sellers**, kind
   *platform*, and names its editors). Stage 2 then records the devices of
   the active home, each pointing at its article's IRI.
2. Images: in the Stage 1 form (or later, Marketplace → Modify) pick the PNG
   from `images/`. The Portal uploads it by its SHA-256 to
   `public/market/<seller>/sha256/<hash>.png`; the first image is the
   thumbnail. A file the seller already has is not sent again.

Bulk image upload from a script is not there yet: it would have to go
through the `marketUploads` mutation as an editor (the PUTs are bound to the
file's SHA-256), not to S3 directly.

## Gateway gotchas

### OpenCCU (<ccu-host>)

- The XML API addon **requires a session ID** issued by the WebUI. URL-encoding
  the literal `@` characters that bookend it breaks the call — `quote(sid,
  safe="@")` is what makes it work (see the `fetch_xml` helper).
- VIR-* device types are CCU-internal proxies for off-CCU equipment (Philips
  Hue lights via the hue addon). They're filtered out via
  `SKIP_DEVICE_TYPE_PREFIXES = ("VIR-",)` because the real devices are
  discovered directly from the Hue bridge — keeping both would double-count
  every Hue light.
- The CCU also serves official eQ-3 product images at
  `/config/img/devices/250/<numeric-typecode>_<device-type-lowercase>.png`.
  Filenames for the 16 covered types are mapped explicitly in
  `download_device_images.py::CCU_IMAGE_FILENAME` because the typecode is not
  derivable from the `device_type` string. Eight HmIP/HM types currently lack
  a CCU-shipped image — drop a manually-sourced PNG into `images/<device_type>.png`
  and the upload script will pick it up on next run.

### Philips Hue (<hue-host>)

- The username/API key is a long-lived bearer token issued via
  `POST /api` while the **physical Link button** on the bridge is lit. It
  survives bridge reboots but not factory resets.
- Save the minted key somewhere durable — the script does not persist it.
  A gitignored `.env.dlab5` next to the scripts is fine; do **not** commit it.
- The bridge serves no unauthenticated product images. The `meethue.com`
  product-image endpoint that looks promising actually returns the same SPA
  HTML for every modelid. Hue + innr cover PNGs must be sourced manually
  today and dropped into `images/<modelid>.png`.

## Extending the catalogues

When a new device pairs with the gateway and shows up as `Unknown` brand /
empty fields:

1. Identify the `device_type` (CCU) or `modelid` (Hue) in the CSV.
2. Add an entry to `DEVICE_TYPE_CATALOGUE` (in
   `build_inventory_from_openccu.py`) or `HUE_MODEL_CATALOGUE` (in
   `build_inventory_from_huebridge.py`).
3. Choose `(category, deviceType)` from the canonical constants
   (`repos/core/amplify/data/resource.ts` + `repos/designer/src/constants/deviceTypes.js`).
   Use the cheat sheet above as default.
4. Add a Brick `compatibleClasses` value (semicolon-separated). The Brick
   class hierarchy lives in `repos/core/schema/tbox/Brick+extensions.ttl`.
5. Re-run the relevant fetcher, then import the refreshed CSV (step 4). An
   article that already exists opens prefilled in Stage 1; saving merges
   your change into the seller's current catalogue.

When a new CCU `device_type` ships an image:

1. Find the filename in `https://github.com/jens-maus/occu/tree/master/WebUI/www/config/img/devices/250/`.
2. Add the mapping to `CCU_IMAGE_FILENAME` in `download_device_images.py`.
3. Re-run `download_device_images.py` and attach the new image to the
   article (step 4).

## Non-goals

- **Writing the marketplace directly** — by design. This skill stops at the
  CSV and the local images; a seller's editor brings them in through the
  Portal (step 4), where the merge, the SHACL shapes and the version checks
  apply. Never write `market/graphs/` or `public/market/` in S3 by hand.
- **A-Box / instance-data writes** — instance rows belong to the SmartHome
  design owned by the Designer's design page.
- **Per-tenant or per-SmartHome inventory uploads** — the `--smarthome-id`
  flag on the CCU script is informational only (stamped in stderr log); the
  CSVs and S3 paths are catalogue-scoped, not tenant-scoped.
- **Cross-gateway de-duplication** beyond the VIR-* prefix filter. If a
  device is reachable via multiple gateways (e.g. paired to both CCU and Hue),
  it will appear in both CSVs and that's deliberate — each gateway's view is
  authoritative for what *it* can control.

## Related skills and code

- **Portal `DeviceModelForm.js` / `utils/market.js`** — the article form
  and the marketplace calls; the form remembers the
  last-used `Category` + `Device type` in-session
  (`lastUsedCategory` / `lastUsedDeviceType` module locals).
- **`dhc-amplify-gen2`** skill — when extending the marketplace: the
  vocabulary and SHACL shapes in `repos/core/schema/market/` (a new fact this
  discovery flow should fill goes there first, then
  `scripts/sync-market-shapes.mjs`).
- **`dhc-ontology-explorer`** skill — when changing what `compatibleClasses`
  values are even valid (Brick + DHC-core ontology authoring).
