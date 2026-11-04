# Input data

Every third-party dataset the manuscript reads is listed here with its publisher, the link it was retrieved from, its licence and the date it was retrieved. The same name and link sit in a comment directly above the manuscript line that reads the file, so the next reader can fetch it without opening this page.

Raw downloads stay out of git under `02.inputs/<source>/raw/`, and the manuscript fetches each one inside a guarded chunk that downloads only when the file is missing. Derived tables the manuscript writes go to `03.outputs/TBL/` and are committed.

## Sources

Each source takes one entry in this form.

| Field | Entry |
|---|---|
| Dataset | Full name as the publisher gives it |
| Publisher | Agency or data centre |
| Link | Landing page, and the DOI as an https link where one exists |
| Licence | Licence name |
| Retrieved | ISO date |
| Local path | `02.inputs/<source>/raw/<file>` |
| Read by | Manuscript chunk label |

### Canada land use tables

| Field | Entry |
|---|---|
| Dataset | Table 6-1, Net Greenhouse Gas Flux Estimates in the Land Use, Land-Use Change and Forestry Sector, All Inventory Years, by province and territory, National Inventory Report 1990–2024 |
| Publisher | Environment and Climate Change Canada |
| Link | https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/E-LULUCF/?lang=en |
| Licence | Open Government Licence, Canada |
| Retrieved | 2026-10-21 |
| Local path | `02.inputs/eccc/raw/table-6-1.xlsx` |
| Read by | `analysis` |

### FAO global ecological zones

| Field | Entry |
|---|---|
| Dataset | Global Ecological Zones (second edition), GEZ 2010, ESRI shapefile `gez_2010_wgs84` |
| Publisher | Food and Agriculture Organization of the United Nations, Forestry Department |
| Link | https://data.apps.fao.org/catalog/dataset/2fb209d0-fd34-4e5e-a3d8-a13c241eb61b and the file https://storage.googleapis.com/fao-maps-catalog-data/uuid/2fb209d0-fd34-4e5e-a3d8-a13c241eb61b/resources/gez2010.zip. Method report FAO (2012), Forest Resources Assessment Working Paper 179, https://www.fao.org/4/ap861e/ap861e00.pdf |
| Licence | FAO catalogue entry states "copyright"; used here for the map and the burned area by zone only |
| Retrieved | 2026-11-03 |
| Local path | `02.inputs/ipcc/raw/gez2010.zip` |
| Read by | `zones` |

### IPCC climate zones

| Field | Entry |
|---|---|
| Dataset | IPCC Climate Zones from the 2019 Refinement, Figure 3A.5.1 of Volume 4 Chapter 3, recreated at 0.5 degree from CRU TS 3.25 by Matthew Lewis, version 0.1.0 |
| Publisher | Zenodo |
| Link | https://doi.org/10.5281/zenodo.7303808 |
| Licence | CC BY 4.0 |
| Retrieved | 2026-11-03 |
| Local path | `02.inputs/ipcc/raw/IPCC_Climate_Zones_ts_3.25.tif`, with its colour map and README beside it |
| Read by | `zones` |

### Canadian National Fire Database polygons

| Field | Entry |
|---|---|
| Dataset | Canadian National Fire Database, fire polygons, current version of 2025-06-30, layers `NFDB_poly_1972to2020_20250630` and `NFDB_poly_2021to2024_20250630` |
| Publisher | Natural Resources Canada, Canadian Forest Service |
| Link | https://cwfis.cfs.nrcan.gc.ca/ha/nfdb and the file https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_poly/current_version/NFDB_poly.zip |
| Licence | Open Government Licence, Canada |
| Retrieved | 2026-10-21, streamed through GDAL's vsicurl without a local copy, 778 MB on the server |
| Local path | none, the `analysis` chunk reads the two layers' attribute tables over the network and caches `02.inputs/nfdb/area-burned-by-province.csv` |
| Read by | `analysis` for the area burned by province |

### Canadian National Fire Database points

| Field | Entry |
|---|---|
| Dataset | Canadian National Fire Database, fire points, version of 2026-08-11, layer `NFDB_point_20260811`, 448,618 fires with year, location and size in hectares |
| Publisher | Natural Resources Canada, Canadian Forest Service |
| Link | https://cwfis.cfs.nrcan.gc.ca/ha/nfdb and the file https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_shp.zip |
| Licence | Open Government Licence, Canada |
| Retrieved | 2026-11-03, 42 MB |
| Local path | `02.inputs/nfdb/raw/NFDB_point_shp.zip` |
| Read by | `zones` for the area burned by ecological zone, cached as `02.inputs/ipcc/burned-area-by-zone.csv`, and for the fires of 1,000 ha or more on the map |

### IPCC 2024 expert meeting report

| Field | Entry |
|---|---|
| Dataset | Report of the IPCC Expert Meeting on Reconciling Anthropogenic Land Use Emissions, Ispra, 9 to 11 July 2024 |
| Publisher | IPCC Task Force on National Greenhouse Gas Inventories, published by IGES, Hayama |
| Link | https://www.ipcc-nggip.iges.or.jp/public/mtdocs/pdfiles/2407_EM_Land_Report.pdf |
| Licence | IPCC copyright, quoted under citation |
| Retrieved | 2026-11-03 |
| Local path | `04.references/literature/ipcc-2024-em/IPCC-2024-EM-Land-Report.pdf` |
| Read by | cited as `ipcc2024reconciling` |
