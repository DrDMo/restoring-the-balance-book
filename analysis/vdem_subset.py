"""Extract the V-Dem Country-Year v14 columns used by this book (writes data/processed/vdem_subset.parquet).
Input: V-Dem-CY-Full+Others-v14.csv from https://v-dem.net (placed in $RTB_DATA/raw/vdem_cy/)."""
import os
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("RTB_DATA", ROOT / "data"))
COLS = ['country_name', 'country_text_id', 'country_id', 'year', 'v2x_polyarchy', 'v2x_libdem', 'v2x_freexp_altinf', 'v2xel_frefair', 'v2x_elecoff', 'v2x_jucon', 'v2xlg_legcon', 'v2elmulpar', 'v2eltvrexo', 'v2elturnhog', 'v2elturnhos', 'v2psoppaut', 'v2exnamhos', 'v2exhoshog', 'v2exnamhog', 'v2ex_hosw', 'v2juhcind', 'v2juncind', 'v2juhccomp', 'v2jucomp', 'v2cacamps', 'v2cagenmob', 'v2cademmob', 'v2caautmob', 'v2x_regime', 'v2x_veracc', 'v2x_veracc_codelow', 'v2x_veracc_codehigh', 'v2x_veracc_osp', 'v2x_diagacc', 'v2x_diagacc_codelow', 'v2x_diagacc_codehigh', 'v2x_diagacc_osp', 'v2x_horacc', 'v2x_horacc_codelow', 'v2x_horacc_codehigh', 'v2x_horacc_osp', 'v2x_ex_military', 'v2xnp_pres', 'v2x_corr', 'v2xcs_ccsi', 'v2xex_elecreg', 'v2xps_party', 'e_regionpol_6C', 'e_gdppc', 'e_pop']

if __name__ == "__main__":
    v = pd.read_csv(DATA / "raw/vdem_cy/V-Dem-CY-Full+Others-v14.csv", usecols=COLS, low_memory=False)[COLS]
    (ROOT / "data/processed").mkdir(parents=True, exist_ok=True)
    v.to_parquet(ROOT / "data/processed/vdem_subset.parquet")
    print(v.shape)
