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
| Dataset | Canadian National Fire Database, fire points, version of 2026-08-11, layer `NFDB_point_20260811`, 448,618 fires with year, month, location, size in hectares, cause code (`CAUSE`, values H, N and U), fire type (`FIRE_TYPE`) and prescribed flag (`PRESCRIBED`). The publisher's citation reads "Canadian Forest Service. Canadian National Fire Database – Agency Fire Data. Natural Resources Canada, Canadian Forest Service, Northern Forestry Centre, Edmonton, Alberta." |
| Publisher | Natural Resources Canada, Canadian Forest Service |
| Link | https://cwfis.cfs.nrcan.gc.ca/ha/nfdb, the catalogue record https://cwfis.cfs.nrcan.gc.ca/en/catalogue/results/7355c08f-1590-41cc-a751-8856afaa5959 and the file https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_shp.zip |
| Licence | Open Government Licence, Canada |
| Retrieved | 2026-11-03, 42 MB; metadata PDF and README read 2026-11-04 |
| Local path | `02.inputs/nfdb/raw/NFDB_point_shp.zip` |
| Read by | `zones`, which places every fire of 2001 to 2024 in its ecological zone, soil class, land cover class and province and caches the sums by year, zone, soil, cover, cause, type, month and province as `02.inputs/ipcc/fires-by-stratum.csv`, and keeps the fires of 1,000 ha or more with their cause for the map |

### IPCC default soil classes

| Field | Entry |
|---|---|
| Dataset | IPCC default soil classes derived from the Harmonized World Soil Data Base (Ver. 1.1), 5 arc-minute global raster, 4320 × 2160, EPSG:4326, Idrisi raster `SOIL_TYPE.rst` with sidecar `SOIL_TYPE.RDC` converted to `soil_type.tif`. Legend from the sidecar, 1 Organic, 2 Sandy Soils, 3 Wetland Soils, 4 Volcanic Soils, 5 Spodic Soils, 6 High Activity Clay Soils, 7 Low Activity Clay Soils, 8 Other Areas, 0 background |
| Publisher | ISRIC World Soil Information, Batjes (2010), Report 2009/02b |
| Link | No retrieval link was recorded at delivery. The file was copied from an earlier local copy of the same raster, whose own manifest records the same absence. The report is cited as `batjes2010ipcc` |
| Licence | Not recorded |
| Retrieved | Copied 2026-11-04 |
| Local path | `02.inputs/ipcc/raw/soil_type.tif` and `SOIL_TYPE.RDC`, with the Canada crop committed as `02.inputs/ipcc/soil-type-canada.tif` (34 kB) because the raw file has no public link |
| Read by | `zones` for the soil class of every fire and for panels (c) and (f) of the strata map |

### MODIS land cover

| Field | Entry |
|---|---|
| Dataset | MODIS/Terra+Aqua Land Cover Type Yearly L3 Global 500m SIN Grid V061, MCD12Q1, band `LC_Type1` (IGBP classes), year 2023, exported at 2 km in EPSG:4326 over −141.5 to −52 degrees longitude and 41 to 84 degrees latitude |
| Publisher | NASA Land Processes Distributed Active Archive Center, Friedl and Sulla-Menashe (2022), through the Google Earth Engine collection `MODIS/061/MCD12Q1` |
| Link | https://doi.org/10.5067/MODIS/MCD12Q1.061 and https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD12Q1 |
| Licence | NASA data, no restriction on use |
| Retrieved | 2026-11-04 through the Earth Engine Python API, project `manuscripts-personal` |
| Local path | `02.inputs/ipcc/mcd12q1-2023-canada.tif` (709 kB), committed because a rebuild needs an Earth Engine account; the `zones` chunk rebuilds it through `reticulate` only when it is missing |
| Read by | `zones` for the land cover class of every fire and for panels (c) to (e) of the strata map |

### MODIS burned area

| Field | Entry |
|---|---|
| Dataset | MODIS/Terra+Aqua Burned Area Monthly L3 Global 500m SIN Grid V061, MCD64A1, bands `BurnDate` and `Uncertainty`, every month of 2001 to 2024, summed by IGBP class of the yearly MCD12Q1 map and by ecological zone group within the GAUL 2015 boundary of Canada, inside Earth Engine |
| Publisher | NASA Land Processes Distributed Active Archive Center, Giglio et al. (2022), through the Google Earth Engine collection `MODIS/061/MCD64A1` |
| Link | https://doi.org/10.5067/MODIS/MCD64A1.061 and https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD64A1 |
| Licence | NASA data, no restriction on use |
| Retrieved | 2026-11-04 through the Earth Engine Python API, project `manuscripts-personal`, as direct calls on 96 boxes with all 24 years per call, each box cached under `02.inputs/faostat/raw/mcd64a1-tiles/` |
| Local path | `02.inputs/faostat/mcd64a1-burned-by-class.csv`, committed because a rebuild needs an Earth Engine account; the `faostat-burned` chunk rebuilds it through `reticulate` only when it is missing |
| Read by | `faostat-burned` for the burned area of FAO's method by item, year and zone group, against the hectares FAOSTAT published |

### FAO GAUL country boundary

| Field | Entry |
|---|---|
| Dataset | Global Administrative Unit Layers 2015, level 0, the country boundary the FAOSTAT fires note names, feature `ADM0_NAME = Canada` |
| Publisher | FAO, through the Google Earth Engine collection `FAO/GAUL/2015/level0` |
| Link | https://developers.google.com/earth-engine/datasets/catalog/FAO_GAUL_2015_level0 |
| Licence | FAO, for non-commercial use as the catalogue states |
| Retrieved | 2026-11-04 inside Earth Engine; nothing is downloaded |
| Read by | `faostat-burned` as the summing region |

### FBP fuel types

| Field | Entry |
|---|---|
| Dataset | CFFDRS Fire Behaviour Prediction (FBP) Fuel Types, Canada, 250 m, 2026 release, `FBP_FuelTypes_Canada_2026_250m.tiff`, classified from the Spatialized Canadian National Forest Inventory, the ecozones of Canada and the National Burned Area Composite. The raster carries no legend; its codes were read from the catalogue's map service (`public:cffdrs_fbp_fuel_types`, GetFeatureInfo) on 2026-11-04: 1 to 7 C-1 to C-7, 11 D-1 leafless aspen, 13 D-1/D-2 aspen, 31 O-1a matted grass, 101 non-fuel, 102 water, 105 vegetated non-fuel, 415, 625, 650 and 675 M-1/M-2 boreal mixedwood at 15, 25, 50 and 75 per cent conifer |
| Publisher | Natural Resources Canada, Canadian Forest Service, Northern Forestry Centre |
| Link | https://cwfis.cfs.nrcan.gc.ca/en/catalogue/results/b7cc58d4-4b16-4a3a-8131-3ae370d4d6e6 and the file https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/current/FBP_FuelTypes_Canada_2026_250m.tiff |
| Licence | Open Government Licence, Canada |
| Retrieved | 2026-11-04, 49 MB, with the 2024 metadata PDFs, the CIFFC colour standard and the 2014 metadata beside it |
| Local path | `02.inputs/nrcan/raw/FBP_FuelTypes_Canada_2026_250m.tiff` |
| Read by | `national` |

### Peatland map of Canada

| Field | Entry |
|---|---|
| Dataset | Distribution of peatlands in Canada using National Forest Inventory forest structure and ancillary land cover data (2011), classified peatland map `ClassPeatMap_2020_EPSG_3978.tif`, 250 m, classes 0 not peat, 1 open bog, 2 open poor fen, 3 open rich fen, 4 treed bog, 5 treed poor fen, 6 treed rich fen, 7 forested bog, 8 forested poor fen, 9 forested rich fen |
| Publisher | Natural Resources Canada, Canadian Forest Service, Webster et al. (2018) |
| Link | https://open.canada.ca/data/en/dataset/62d63169-7739-4515-9178-8f628c32a9d4 and the file http://ftp.maps.canada.ca/pub/nrcan_rncan/Forestry-industry_Industrie-forestiere/peatlands/ClassPeatMap_2020_EPSG_3978.tif; method https://doi.org/10.1186/s13021-018-0105-5 |
| Licence | Open Government Licence, Canada |
| Retrieved | 2026-11-04, 19 MB |
| Local path | `02.inputs/nrcan/raw/ClassPeatMap_2020_EPSG_3978.tif` |
| Read by | `national` |

### National Burned Area Composite statistics

| Field | Entry |
|---|---|
| Dataset | National Burned Area Composite (NBAC), summary statistics by year and administrative unit, 1972 to 2025, version of 2026-05-13, `NBAC_summarystats_1972_to_2025_20260513.xlsx`, sheet `sumstats_admin_name`, column `CANADA` in adjusted hectares |
| Publisher | Natural Resources Canada, Canadian Forest Service |
| Link | https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/ and the file https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/NBAC_summarystats_1972_to_2025_20260513.xlsx |
| Licence | Open Government Licence, Canada |
| Retrieved | 2026-11-04, 4.4 MB |
| Local path | `02.inputs/nrcan/raw/NBAC_summarystats_1972_to_2025_20260513.xlsx` |
| Read by | `national` |

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
