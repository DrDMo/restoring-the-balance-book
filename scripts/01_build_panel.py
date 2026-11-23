"""Build the country-year panel (carried forward from Volume 2; to be extended for Volume 3).

Inputs (RTB_DATA_ROOT/raw):
  unz/V-Dem-CY-Full+Others-v14.csv   V-Dem Country-Year v14
  vdem_ert/ert.csv                    V-Dem ERT v16
Output (RTB_DATA_ROOT/processed):
  vdem_panel.parquet                  1990-2023 country-years, selected variables
"""

from __future__ import annotations

import pandas as pd

from restoring_the_balance.paths import PROC_DIR, RAW_DIR, ensure_dir

ACC = ["v2x_veracc_osp", "v2x_horacc_osp", "v2x_diagacc_osp"]
COMPONENTS = [
    "v2x_jucon",
    "v2xlg_legcon",
    "v2juhcind",
    "v2xel_frefair",
    "v2psparban",
    "v2psbars",
    "v2x_freexp_altinf",
    "v2mecenefm",
    "v2xcs_ccsi",
    "v2x_libdem",
    "v2x_liberal",
]
CONVERSION = ["v2exrescon", "v2jupoatck", "v2jupack"]
GATEKEEPING = ["v2xps_party", "v2cacamps", "v2exhoshog", "v2ex_hosw"]
CONTROLS = ["e_gdppc", "e_pop", "e_regionpol_6C"]


def main() -> None:
    cols = (
        ["country_name", "country_text_id", "country_id", "year", "v2x_regime"]
        + ["v2x_polyarchy", "v2x_polyarchy_codelow", "v2x_polyarchy_codehigh"]
        + [f"{v}{s}" for v in ACC for s in ("", "_codelow", "_codehigh")]
        + [f"{v.replace('_osp', '')}{s}" for v in ACC for s in ("", "_codelow", "_codehigh")]
        + COMPONENTS
        + CONVERSION
        + GATEKEEPING
        + CONTROLS
    )
    vdem = pd.read_csv(
        RAW_DIR / "unz" / "V-Dem-CY-Full+Others-v14.csv", usecols=cols, low_memory=False
    )
    vdem = vdem[(vdem.year >= 1990) & (vdem.year <= 2023)]

    ert = pd.read_csv(RAW_DIR / "vdem_ert" / "ert.csv", low_memory=False)
    ert = ert[
        [
            "country_text_id",
            "year",
            "aut_ep",
            "aut_ep_id",
            "aut_ep_start_year",
            "dem_ep",
            "reg_type",
        ]
    ]

    panel = vdem.merge(ert, on=["country_text_id", "year"], how="left", validate="one_to_one")
    panel = panel.sort_values(["country_text_id", "year"]).reset_index(drop=True)

    ensure_dir(PROC_DIR)
    panel.to_parquet(PROC_DIR / "vdem_panel.parquet", index=False)
    print(
        f"vdem_panel: {len(panel):,} country-years, {panel.country_text_id.nunique()} countries, "
        f"{panel.year.min()}-{panel.year.max()}; ERT matched {panel.aut_ep.notna().mean():.1%}"
    )


if __name__ == "__main__":
    main()
