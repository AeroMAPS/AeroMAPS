# AeroMAPS — État des lieux : rendre la `start_year` flexible

**Statut :** Draft | **Créé :** 2026-04-20

---

## 1. Contexte

La "start_year" d'un scénario recouvre en réalité **trois bornes couplées** définies dans [aeromaps/resources/data/parameters.json](aeromaps/resources/data/parameters.json) :

| Paramètre | Valeur actuelle | Rôle |
|---|---|---|
| `climate_historic_start_year` | 1940 | Début de l'historique climat (émissions CO2, NOx, H2O, etc.) |
| `historic_start_year` | 2000 | Début de l'historique transport aérien (RPK, ASK, …) |
| `prospection_start_year` | 2020 | Début de la période prospective |
| `end_year` | 2050 | Fin du scénario |

L'objectif est de pouvoir faire varier ces bornes (notamment `prospection_start_year` et `historic_start_year`) sans casser les modèles.

---

## 2. Données d'entrée figées

### 2.1 Vecteurs `*_init` (taille 20, implicitement 2000→2019)

Dans [parameters.json:6-149](aeromaps/resources/data/parameters.json#L6-L149) :

- `rpk_init`, `ask_init`, `rtk_init`, `pax_init`, `freight_init`, `energy_consumption_init`, `total_aircraft_distance_init`

Ces listes sont converties en `pd.Series` indexées sur `range(historic_start_year, prospection_start_year)` dans [utils/functions.py:93-105](aeromaps/utils/functions.py#L93-L105) et rééchantillonnées dans [core/process.py:1599-1651](aeromaps/core/process.py#L1599-L1651).

**Implication :** si on change `historic_start_year` ou `prospection_start_year`, il faut fournir autant de valeurs que la nouvelle plage — mais la structure de `parameters.json` n'expose pas d'index explicite (contrairement aux JSON de partitionnement).

### 2.2 CSV climat historique

[temperature_historical_dataset.csv](aeromaps/resources/climate_data/temperature_historical_dataset.csv) — années 1940→2019 codées en dur. Lecture dans [core/process.py:1532-1574](aeromaps/core/process.py#L1532-L1574), consommation dans :
- [co2_emissions.py:382-386](aeromaps/models/impacts/emissions/co2_emissions.py#L382-L386)
- [impacts/climate/climate.py:116-154](aeromaps/models/impacts/climate/climate.py#L116)

### 2.3 Partitionnement

[utils/functions.py:206-251](aeromaps/utils/functions.py#L206-L251) : `for k in range(0, 20)` + accès `[19]` (= 2019) en dur.

---

## 3. Paramètres scalaires nommés `_2019`

~15 clés portent 2019 dans leur nom (`short_range_energy_share_2019`, `world_co2_emissions_2019`, `carbon_offset_baseline_level_vs_2019_*`, etc.). Le nom encode l'année de référence, ce qui crée un couplage implicite.

**Pistes :** renommer en `*_reference` ou `*_base_year` + stocker l'année de référence, ou dériver dynamiquement depuis `prospection_start_year - 1`.

---

## 4. Accès `.loc[year]` en dur dans les modèles

**~105 occurrences** de `.loc[2019]`, `.loc[2020]`, `(k - 2019)` dans 8 fichiers :

| Fichier | # occ. | Notes |
|---|---|---|
| [aircraft_efficiency.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py) | ~50 | Patchs COVID `.loc[2020]=.loc[2019]`, calibration initiale |
| [rpk.py](aeromaps/models/air_transport/air_traffic/rpk.py) | 9 | |
| [price_elasticity.py](aeromaps/models/air_transport/air_traffic/price_elasticity.py) | 9 | |
| [carbon_offset.py:74-80](aeromaps/models/impacts/emissions/carbon_offset.py#L74-L80) | 9 | Baseline emissions 2019 |
| [short_range_distribution.py:80](aeromaps/models/air_transport/air_traffic/short_range_distribution.py#L80) | 9 | `reference_years = [2019, 2030, 2040, end_year]` |
| [load_factor.py:58-69](aeromaps/models/air_transport/aircraft_fleet_and_operations/load_factor/load_factor.py#L58-L69) | 7 | `load_factor_2019`, `(k-2019)`, override COVID 2020 |
| [carbon_budget.py](aeromaps/models/sustainability_assessment/climate/carbon_budget.py) | 6 | Budget carbone 2020-2050 |
| [fleet_model.py:914-921](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py#L914-L921) | 6 | Ratio énergie/ASK en 2019 |

Sémantiquement, la plupart correspondent à "année pivot" = `prospection_start_year - 1`. Un TODO explicite existe déjà dans [comparison.py:48](aeromaps/models/sustainability_assessment/climate/comparison.py#L48).

---

## 5. Spécificité COVID

Le patch `.loc[2020]` (load_factor, aircraft_efficiency) suppose que `prospection_start_year == 2020`. Exemple dans [load_factor.py:58-69](aeromaps/models/air_transport/aircraft_fleet_and_operations/load_factor/load_factor.py#L58-L69) :

```python
load_factor_2019 = self.df.loc[2019, "load_factor"]
...
for k in range(self.prospection_start_year, self.end_year + 1):
    self.df.loc[k, "load_factor"] = a * (k - 2019) ** 2 + b * (k - 2019) + load_factor_2019
# Covid-19 : à refaire proprement
self.df.loc[2020, "load_factor"] = covid_load_factor_2020
```

À rendre conditionnel au cas `prospection_start_year == 2020`, ou à généraliser à une liste d'années/valeurs de correction.

---

## 6. Notebooks et publications

Plages d'années codées en dur :
- `np.arange(2020, 2055, 5)` (run_opt_B*.ipynb)
- `range(2019, 2071)` (tsas_2025, ecats_2026)
- `range(2000, 2051)` (main.ipynb optim)

Choix à faire : paramétrer ou accepter comme "snapshots publication" figés.

---

## 7. Synthèse des chantiers

Par ordre suggéré :

1. **Format de `parameters.json`** : introduire un index `years` explicite pour les `*_init` (comme le fait déjà le JSON de partitionnement via `other_vector_data.years`).
2. **Renommer `*_2019` → `*_reference`** (ou `*_base_year`) + centraliser la résolution via `prospection_start_year - 1`.
3. **Purger les `.loc[2019]` / `(k - 2019)` / `[19]`** au profit de `prospection_start_year - 1` / bornes paramétrées.
4. **Rendre le patch COVID conditionnel** (skip si `prospection_start_year != 2020`, ou liste d'overrides year→value en paramètre).
5. **Données climat historiques** : vérifier la troncature/extension dynamique selon `climate_historic_start_year` (le code gère déjà le reindex dans `_format_input_vectors`, mais à tester sur des bornes non-1940).
6. **`create_partitioning`** : remplacer `range(0, 20)` et `[19]` par des bornes issues des paramètres.
7. **Notebooks de publication** : décider cas par cas (figer vs paramétrer).

### Points de vigilance

- Volume le plus lourd : [aircraft_efficiency.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py) (~50 occurrences).
- Point le plus sensible fonctionnellement : gestion COVID + calibration prospective initialisée sur l'année pivot.
- Les conventions de nommage `*_2019` fuitent vers les JSON utilisateurs et les notebooks → migration avec alias de compatibilité à prévoir.
