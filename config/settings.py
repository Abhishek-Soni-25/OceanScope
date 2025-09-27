import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

ARGO_DIR = os.path.join(DATA_DIR, "argo")
SST_DIR = os.path.join(DATA_DIR, "sst")
BGC_DIR = os.path.join(DATA_DIR, "bgc")

# Extraction URLs
ARGO_URL = "https://data-argo.ifremer.fr/geo/indian_ocean/2025/09/"
SST_URL = "https://osi-saf.ifremer.fr/sst/l3c/indian/meteosat/2025/270/"
BGC_URL = "https://data-argo.ifremer.fr/dac/incois/"

# Ensure directories exist
for folder in [ARGO_DIR, SST_DIR, BGC_DIR]:
    os.makedirs(folder, exist_ok=True)
