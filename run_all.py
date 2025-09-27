from extraction.extract_argo import fetch_argo_data
from extraction.extract_sst import fetch_sst_data
from extraction.extract_bgc import fetch_bgc_data

if __name__ == "__main__":
    fetch_argo_data()
    fetch_sst_data()
    fetch_bgc_data()
