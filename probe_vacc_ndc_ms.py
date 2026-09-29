"""Probe: COVID-19 vaccination in MarketScan drug claims, labeler-prefix rule vs product-level NDCs.

Product list (labeler-product, 9 digits) from AMA CPT Appendix Q (codes 91300-91317) and
NC Medicaid 2023-2024 COVID-19 vaccine guidelines (codes 91304, 91318-91322).
Aggregates only; any count below 11 is printed as "<11".
"""

import duckdb
import pandas as pd

MS_DIR = "/N/project/Marketscan1/parquet"
R = "results/ms"
PROD = [
    "592671000",
    "592671025",
    "592670304",
    "592671404",
    "592671055",
    "592670565",
    "592670078",
    "592670609",
    "000692025",
    "807770273",
    "807770100",
    "807770282",
    "807770279",
    "807770283",
    "807770275",
    "596760580",
    "806310100",
    "806311000",
    "592674315",
    "592674331",
    "000692362",
    "000692377",
    "807770287",
    "807770102",
    "806310105",
]
con = duckdb.connect()
c = pd.read_csv(f"{R}/01_covid_cohort.csv", usecols=["person_id", "covid_index_date"])
mp = pd.read_csv(
    f"{R}/08_regression_base.csv", usecols=["person_id"]
).person_id.unique()
c = c[c.person_id.isin(mp)]  # matched persons only
con.register("coh", c)
u = " UNION ALL ".join(
    f"SELECT ENROLID AS person_id, SVCDATE AS d, LPAD(CAST(NDCNUM AS VARCHAR), 11, '0') AS ndc "
    f"FROM read_parquet('{MS_DIR}/mscan_{y}_d.parquet')"
    for y in ("2021", "2022", "2023")
)
plist = ",".join(f"'{p}'" for p in PROD)
d = con.sql(f"""
WITH x AS (SELECT * FROM ({u}) WHERE person_id IN (SELECT person_id FROM coh)
           AND (SUBSTR(ndc,1,5) IN ('59267','80777','59676','80631','00069')))
SELECT x.person_id, x.d, x.ndc, SUBSTR(x.ndc,1,9) AS prod,
       CAST(coh.covid_index_date AS DATE) AS idx
FROM x JOIN coh USING (person_id)""").df()
d["old"] = d.ndc.str[:5].isin(["59267", "80777", "59676"])
d["new"] = d["prod"].isin(PROD)
d["pre"] = pd.to_datetime(d.d) <= pd.to_datetime(d.idx)
M = lambda n: str(int(n)) if n >= 11 else "<11"
pre = d[d.pre]
old_p = set(pre.person_id[pre.old])
new_p = set(pre.person_id[pre.new])
print("matched persons:", len(c))
print("vaccinated before index, old prefix rule:", M(len(old_p)))
print("vaccinated before index, product rule:", M(len(new_p)))
print("old only (misclassified as vaccinated):", M(len(old_p - new_p)))
print("new only (missed by old rule, e.g. 00069 Comirnaty):", M(len(new_p - old_p)))
nv = (
    pre[pre.old & ~pre.new]
    .groupby("prod")
    .person_id.nunique()
    .sort_values(ascending=False)
)
print("top non-vaccine products matched by the old rule (persons):")
for k, v in nv.head(15).items():
    print("  ", k, M(v))
