# Spike `unified_mda` — discipline globale non namespacée

**Branche** `spike/unified-mda-global-discipline` · **base** `fix/mda-residual-floor-and-global-disciplines`
(PR #157, elle-même sur `a1bb678c`) · GEMSEO 6.2.0

**Recommandation : architecture confirmée.** Le montage tient. Ce qui manquait était
un point d'accroche (une trentaine de lignes, livrée ici) et non une propriété du
solveur.

Deux réserves, dans cet ordre d'importance :

1. Le risque principal n'était pas la convergence de Gauss-Seidel mais sa *détection* :
   sur la chaîne réelle le résidu MDA était plafonné à ~1,6e-6, au-dessus de toute
   tolérance utile. Défaut préexistant, indépendant du spike, **diagnostiqué et corrigé
   ici** (§ 2) — la cause n'était pas le sentinel NaN mais une discipline qui mutait sa
   propre entrée de couplage en place, écrasant l'itéré précédent du solveur.
2. Il existe un vrai plafond de convexité que **aucun réglage de solveur ne franchit**
   (§ 4). L'accélération repousse le seuil d'un facteur ~2 à 4 sur la chaîne réelle,
   pas à l'infini. Au-delà, il faudra amortir la mise à jour du prix *dans* la
   discipline de marché plutôt que compter sur le MDA.

---

## 1. Assemblage

**Étape 1 (plomberie pure).** `MDAChain` construit sans erreur. `SpikeClearing`
(globale, non namespacée) et les trois `SpikeDemand` régionaux forment **une seule
composante fortement connexe** :

```
disciplines            : EU_SpikeDemand, US_SpikeDemand, APAC_SpikeDemand, SpikeClearing
composante connexe     : les 4
couplages forts        : {EU,US,APAC}:spike_demand, {EU,US,APAC}:spike_price
```

**Étape 2 (cycle réel, 2 régions, chaîne AeroMAPS complète avec `RPKElasticity`).**

```
disciplines dans la chaîne    : 304
composante fortement connexe  : 109 disciplines
SpikeFuelMarket dans la CFC   : oui
disciplines spike dans la CFC : region_{A,B}_SpikeFuelDemand, region_{A,B}_SpikeMarketCarbonTax,
                                SpikeFuelMarket
RPKElasticity dans la même CFC: region_A_RPKElasticity, region_B_RPKElasticity
couplages forts spike         : region_{A,B}:spike_fuel_demand, region_{A,B}:spike_fuel_price
couplages forts de référence  : region_{A,B}:rpk, region_{A,B}:airfare_per_rpk
```

Le cycle bouclé est bien celui visé :

```
{r}:rpk → {r}:spike_fuel_demand → SpikeFuelMarket (toutes régions)
        → {r}:spike_fuel_price → {r}:carbon_tax → DOC énergie → coût total
        → {r}:airfare_per_rpk → RPKElasticity → {r}:rpk
```

GEMSEO absorbe donc `SpikeClearing` **dans la même CFC** que `rpk ↔ airfare_per_rpk`.

> À signaler : sur la base, `unified_mda` n'avait jamais résolu de cycle. Le tutoriel
> deux régions produit `mda_chain.inner_mdas == []` — 167 disciplines, aucune
> composante fortement connexe, chaîne purement séquentielle. Ce spike est le premier
> cas où le mode fait réellement tourner un solveur de couplage.

## 2. Convergence

| cas | itérations | résidu final | tolérance |
|---|---|---|---|
| Étape 1, nominal (`stiffness=0.3`, `gamma=1`, `elasticity=0.5`) | **12** | 1.76e-11 | 1e-10 |
| Étape 2, chaîne réelle, nominal (`price_elasticity=-0.9`) | **22** | 2.94e-11 | 1e-10 |

Étape 1 : l'écart au point fixe analytique est de **2.1e-14** — le solveur trouve la
bonne racine, pas seulement un plateau.

Le chiffre de 22 itérations suppose le correctif décrit ci-dessous. Avant celui-ci, le
même cas s'arrêtait à 38 itérations avec un résidu de 7,06e-7, sur
`max_consecutive_unsuccessful_iterations`.

### Le plancher de résidu à ~1,6e-6 était préexistant

Contrôle décisif — tutoriel `08_use_variable_demand`, **une seule région, AeroMAPS non
modifié**, mêmes réglages que `AeroMAPSProcess` (`tolerance=1e-10`, `MDAGaussSeidel`) :

```
52 disciplines couplées, 19 itérations, résidu final 1.595e-06  →  NON convergé
```

Cause exacte, mesurée sur `_current_residuals` :

```
hydrogen_mean_co2_emission_factor   norme 7.14e+06   (51/51 valeurs NaN)
electric_mean_co2_emission_factor   norme 7.14e+06   (51/51 valeurs NaN)
ask                                 norme 2.05e-02
norme totale 1.01e+07 / échelle 6.33e+12 = 1.59e-06
```

`CustomDataConverter.convert_value_to_array` fait `value.fillna(-999999)`. Une série de
couplage entièrement NaN (ici : ni hydrogène ni électrique dans le scénario) injectait
donc **999999 par élément** dans le vecteur résidu, en permanence.

Le premier réflexe — accuser le sentinel — était faux. Voir la cause réelle ci-dessous.

Diagnostic (`nan_floor_probe.py`, une ligne : `fillna(0.0)` au lieu du sentinel) :

| | stock | NaN neutralisés |
|---|---|---|
| contrôle une région (AeroMAPS non modifié) | 19 it, 1.59e-06 ✗ | **9 it, 1.27e-11 ✓** |
| spike deux régions + marché global | 38 it, 7.06e-07 ✗ | **22 it, 2.94e-11 ✓** |

Comparaison **colonne par colonne** des 1935 sorties du scénario spike, stock contre
neutralisé (`nan_impact_check.py`) :

| | colonnes |
|---|---|
| identiques au bit près | 1196 |
| écart **uniquement** NaN → 0 | 24 |
| numériquement différentes | 715, **toutes à ≤ 8,8e-12 en relatif** |

Aucun écart matériel : les 715 colonnes « différentes » le sont au niveau de l'écart
entre un run arrêté à 7e-7 et un run convergé à 3e-11, pas au niveau de la physique.
Le point fixe était bien atteint ; seule sa *détection* échouait. Bonne nouvelle sur la
validité des scénarios existants, mauvaise sur l'usage du résidu comme critère
d'acceptation.

Les 24 colonnes NaN → 0 sont précisément le motif qui interdit de promouvoir ce
diagnostic en correctif : ce sont les `doc_energy_per_ask_*_{hydrogen,electric}`, où
NaN signifie « sans objet » et non « zéro ».

### Cause racine : une discipline mutait l'itéré précédent du solveur

Le sentinel est censé faire un aller-retour : `fillna(-999999)` à l'entrée,
`where(== -999999, nan)` à la sortie. Mesuré, il ne revenait pas. Sur
`hydrogen_mean_co2_emission_factor` (51/51 NaN), au moment du calcul du résidu :

```
côté sortie (la discipline émet)  : -999999.  -999999.  -999999.
côté entrée  (itéré précédent)    :       0.        0.        0.
résidu                            : -999999.  -999999.  -999999.   (constant, à jamais)
```

**Le sentinel n'était pas en cause.** En traçant l'identité des objets, le côté entrée
et le côté sortie sont *le même objet Python* : `nan=51` en haut de `_iterate_once`,
`nan=0` au moment du résidu, `id()` inchangé. Une discipline réécrivait la série en
place pendant le balayage.

Le coupable : `CO2Emissions` faisait `co2_emission_factor.fillna(0, inplace=True)` sur
une entrée de couplage. Le commentaire disait « *Locally* fill » — mais `inplace=True`
n'a rien de local. GEMSEO capture l'itéré précédent avec `self.io.data.copy()`, une
copie **superficielle** : les `pd.Series` qu'elle contient sont exactement les objets
passés à `compute()`. Muter l'un d'eux réécrit l'instantané que le solveur s'apprête à
différencier.

D'où le résidu constant : le producteur émettait NaN → `-999999`, pendant que le
consommateur avait déjà réécrit l'entrée à `0`. `-999999 - 0 = -999999`, à chaque
itération, pour toujours.

### Correctif

Deux changements, aucun dans `core/gemseo.py`, aucun zéro fictif :

| fichier | changement |
|---|---|
| `impacts/emissions/co2_emissions.py` | `fillna(0, inplace=True)` → `fillna(0)` non mutant |
| `generic_energy_model/bottom_up/production_capacity.py` | `.copy()` avant d'étendre et re-trier une entrée de couplage |

Le second est un bug latent trouvé par le même balayage : `BottomUpCapacity` ajoutait
des « années virtuelles » à `{pathway}_energy_consumption` — une variable de couplage —
puis la re-triait, **en place**. Il ne changeait pas seulement des valeurs, mais la
*longueur* de la série.

| | avant | après |
|---|---|---|
| contrôle mono-région | 19 it, résidu 1,59e-6, **non convergé** | **9 it, 1,27e-11, convergé** |
| spike bi-région + marché global | 38 it, 7,06e-7, **non convergé** | **22 it, 2,94e-11, convergé** |

Et surtout : `hydrogen_mean_co2_emission_factor` **reste NaN** en sortie, 214 colonnes
tout-NaN sont préservées. Comparé au dump « neutralisé » (converged mais sémantiquement
faux), 1877 colonnes identiques, 58 qui ne diffèrent que par un NaN correctement
restauré là où le probe forçait un 0, et **aucune autre différence**.

Le sentinel `-999999` reste donc en place et fonctionne exactement comme prévu :
NaN → sentinel des deux côtés → résidu nul → la variable ne contribue pas.

### Garde-fou

`aeromaps/tests/core/test_mda_input_mutation.py` vérifie l'invariant directement :
après `compute()`, toute valeur reçue par une discipline doit être inchangée en valeur,
longueur et index. Testé dans les deux sens — le test échoue en nommant la discipline
et la variable quand on réintroduit la mutation, et passe une fois corrigée.

## 3. Idempotence

**Vérifiée, au bit près**, aux deux étages.

Étape 1 — trois variantes, toutes identiques au bit près, 12 itérations à chaque fois :
même chaîne réexécutée (cache actif), même chaîne cache vidé, chaîne fraîche vs chaîne
chaude. La raison est que GEMSEO a `warm_start = False` par défaut : chaque `execute()`
repart des `default_input_data`. L'état conservé dans `self.df` entre itérations MDA ne
fuit pas, parce que chaque `compute()` réécrit les colonnes qu'il possède. C'est bien
une convention et non une garantie — mais elle tient sur tout ce qui a été testé ici,
et elle cesserait de tenir si `warm_start` était activé.

Étape 2 — `compute()` répété sur le même process, et process frais : valeurs
**bit-identiques** sur les 1935 colonnes.

**Un défaut trouvé au passage** (corrigé, commit séparé) : `vector_outputs` passait de
1935 à 3870 puis 5805 colonnes sur trois `compute()` successifs. Les deux
`pd.concat` de `_update_data_from_unified_mda` et `_aggregate_regional_outputs`
ajoutaient une copie de chaque colonne au lieu de la rafraîchir. Les *valeurs* étaient
correctes, mais tout `df[col]` en aval finissait par renvoyer un DataFrame. Les deux
modes d'exécution étaient touchés.

## 4. Marge de robustesse — le résultat le plus important

### Étape 1 : seuil de rupture de Gauss-Seidel, et sa prédiction

Balayage par bisection, `elasticity=0.5`, `tolerance=1e-10`, `max_mda_iter=2000`.
`gamma*` est la plus grande valeur qui converge encore.

| `stiffness` | `gamma*` mesuré | `gamma*` théorique (\|g'\|=1) | gain au seuil |
|---|---|---|---|
| 0.1 | 56.13 | 57.35 | 0.989 |
| 0.3 | 20.63 | 21.07 | 0.989 |
| 1.0 | 8.12 | 8.28 | 0.989 |
| 3.0 | 4.42 | 4.50 | 0.989 |
| 10 | 2.98 | 3.03 | 0.989 |
| 30 | 2.47 | 2.50 | 0.989 |
| 100 | 2.22 | 2.24 | 0.989 |

Deux enseignements :

1. **La raideur seule ne casse jamais Gauss-Seidel.** À `gamma=1`, `stiffness=1000`
   converge encore en 34 itérations : le gain de boucle sature juste sous l'élasticité
   (0.495 mesuré pour `elasticity=0.5`), donc sous 1 quoi qu'il arrive. Ce qui tue le
   solveur, c'est la **convexité** de la courbe d'offre (son exposant local), pas son
   niveau.
2. **Le seuil est prédictible à 2 % près** par le critère analytique
   `|g'(x*)| = elasticity × gamma × stiffness · x*^(gamma-1) / (1 + stiffness·x*^gamma) = 1`.
   Autrement dit : **Gauss-Seidel converge tant que `élasticité-prix × exposant local
   de la courbe d'offre < 1`**. C'est une règle utilisable en amont, pas seulement un
   chiffre.

Le mode de rupture est bénin en apparence et dangereux en pratique : ni NaN, ni
exception, ni divergence numérique. Le résidu se stabilise sur un plateau, GEMSEO
s'arrête sur `max_consecutive_unsuccessful_iterations` (8 par défaut) et
`execute()` **retourne normalement un résultat faux**. Il n'y a pas de garde-fou en
aval : ni `AeroMAPSProcess.compute()` ni `MultiRegionalProcess.compute()` ne
consultent le statut de convergence.

### Étape 1 : ce que le damping et l'accélération rachètent

Toutes les configurations en échec sont récupérées, et convergent vers la **vraie**
racine (vérifiée par `brentq`, pas par itération de point fixe) :

| `gamma*` | s=0.3 | s=3 | s=10 |
|---|---|---|---|
| Gauss-Seidel nu | 20.6 | 4.42 | 2.98 |
| + sur-relaxation 0.7 | **114.1** | **15.6** | **7.55** |
| + accélération `Alternate2Delta` | **181.1** | **32.9** | **18.3** |

Sur les cas durs (s=3, γ=4…10 ; s=0.3, γ=20…30), l'accélération converge en **10 à 22
itérations** là où Gauss-Seidel nu stagne, avec une erreur au point fixe comprise entre
2e-16 et 3e-13. `MDAJacobi` — le défaut GEMSEO, qui embarque `Alternate2Delta` — converge
partout en 10 à 12 itérations. **AeroMAPS force `inner_mda_name="MDAGaussSeidel"`,
ce qui désactive cette accélération.**

`MDANewtonRaphson` n'est **pas** disponible en l'état : les wrappers AeroMAPS ne
fournissent pas de jacobienne et le repli par différences finies échoue
(`ValueError: The discipline … was not linearized`). Ce n'est pas bloquant — les deux
autres leviers suffisent largement — mais ce serait un chantier à part entière.

> **Piège de configuration, coûteux.** `MDAChain` ne transmet à ses MDA internes que
> les champs de `BaseMDASettings` (`tolerance`, `max_mda_iter`, `warm_start`,
> `log_convergence`…). `over_relaxation_factor` et `acceleration_method` n'en font pas
> partie : passés en kwargs de `MDAChain`, ils configurent **la chaîne externe
> seulement** et sont silencieusement ignorés par le solveur qui itère réellement. Ils
> doivent passer par `inner_mda_settings`. Un premier balayage a conclu à tort que le
> damping était sans effet à cause de cela.

### Étape 2 : le même balayage sur la chaîne réelle

`tolerance=1e-10`, `max_mda_iter=200`, `MDAGaussSeidel`, NaN neutralisés.

| `stiffness` | `gamma` | statut | itérations | prix 2050 | RPK 2050 |
|---|---|---|---|---|---|
| 0.3 | 1 | convergé | 22 | 238.04 | 3.913e13 |
| 1 | 1 | convergé | 30 | 433.18 | 3.776e13 |
| 3 | 1 | convergé | 45 | 930.09 | 3.467e13 |
| 10 | 1 | convergé | 72 | 2280.92 | 2.841e13 |
| 30 | 1 | convergé | 111 | 4906.14 | 2.114e13 |
| 0.3 | 2 | convergé | 28 | 317.27 | 3.856e13 |
| 0.3 | 4 | convergé | 68 | 643.04 | 3.639e13 |
| 0.3 | 8 | **échec** | 200 | — | — |
| 0.3 | 16 | **échec** | 200 | — | — |
| 3 | 2 | convergé | 78 | 1338.16 | 3.250e13 |
| 3 | 4 | **échec** | 200 | — | — |

Même signature qu'à l'étape 1 : la raideur passe (jusqu'à `stiffness=30` en 111
itérations), la convexité casse. Le seuil réel est plus bas que celui du jouet —
`gamma*` entre 4 et 8 à `stiffness=0.3` (contre ~20.6), entre 2 et 4 à
`stiffness=3` (contre ~4.4) — parce que la boucle `airfare ↔ rpk` ajoute son propre
gain (`price_elasticity = -0.9`) en série avec celui du marché. Le rapport entre les
deux seuils est du même ordre que le rapport des élasticités (0.9 / 0.5), ce qui est
cohérent avec le critère `élasticité × exposant local < 1` du § précédent.

### Étape 2 : les remèdes sur la chaîne réelle

Les cas en échec, repassés avec chaque levier (`tolerance=1e-10`, `max_mda_iter=200`).

| stiffness / gamma | GS nu | relax 0,7 | relax 0,4 | + `Alternate2Delta` | `MDAJacobi` |
|---|---|---|---|---|---|
| 0,3 / 8 | ✗ 3,7e+00 | ✗ 1,2e+00 | ✗ 8,0e-01 | **✓ 87 it, 9,9e-11** | erreur |
| 0,3 / 16 | ✗ 7,4e+00 | ✗ 3,4e+00 | ✗ 6,4e+00 | **✓ 91 it, 5,7e-11** | erreur |
| 3 / 8 | ✗ 3,2e+00 | ✗ 1,4e+00 | ✗ 1,8e+00 | ✗ 6,3e-01 | erreur |

Trois écarts par rapport au jouet, tous à retenir :

1. **La sur-relaxation ne rachète rien sur la chaîne réelle.** À 0,7 comme à 0,4, aucun
   des trois cas ne passe — alors que sur le jouet elle récupérait tout. Le damping
   simple est un mauvais pari ici.
2. **L'accélération, elle, fonctionne** : `Alternate2Delta` fait passer `gamma*` de
   « entre 4 et 8 » à « au moins 16 » à `stiffness=0,3`, en ~90 itérations.
3. **`MDAJacobi` échoue franchement** (`ValueError: array must not contain infs or
   NaNs`) sur les trois cas : il exécute toutes les disciplines depuis le même état et
   traverse des valeurs invalides que Gauss-Seidel ne voit jamais. Basculer sur le
   défaut GEMSEO n'est donc pas une option, malgré ce que suggère le jouet.

Mais le cas `3 / 8` ne passe avec **aucun** levier. **Il y a donc bien un plafond
réel**, et non un simple réglage à trouver. Recommandation opérationnelle :
`MDAGaussSeidel` + `acceleration_method: Alternate2Delta` via `inner_mda_settings`, en
sachant qu'au-delà il faudra changer de formulation — amortir la mise à jour du prix
*dans* la discipline de marché, ou fournir des jacobiennes.

## 5. Rejet par `_wrap_top_level_model`

Condition établie par sondage (`step_criterion5.py`) : ce sont **deux `hasattr` sur
l'instance**, sans aucune notion de « demande explicite ». Un attribut déclaré à
`None` dans `__init__` suffit à faire rejeter.

| modèle sondé | verdict |
|---|---|
| modèle custom nu | accepté |
| + `custom_setup` seul | accepté |
| + `pathways_manager = None` seul | accepté |
| + `pathways_manager = None` **et** `custom_setup` | **rejeté** |
| + `climate_historical_data = None` | **rejeté** |
| + `markets = None` et `custom_setup` (patron markets) | accepté |
| + `fleet_model = None` | accepté |

Trois écarts entre le code et sa docstring :

- La docstring annonce que les modèles de flotte sont rejetés. **Il n'y a aucun test
  sur `fleet_model`** : un tel modèle passe la garde et sera exécuté sans flotte
  injectée.
- **`custom_setup()` n'est jamais appelé** au niveau top-level. Une discipline qui
  construit sa grammaire dynamiquement embarquera le placeholder de son `__init__`.
- **Aucune poignée de configuration n'est injectée** (`markets` ressort intact du
  wrapping).

**Réponse à la question posée** : une discipline globale portant sa propre config YAML
(patron `air_transport/markets/` : registre + Manager + factory) **passe la garde** —
elle n'a ni `pathways_manager` ni `climate_historical_data`. Mais elle ne
fonctionnerait pas pour autant, pour deux raisons indépendantes du rejet : son
`custom_setup()` ne serait pas appelé, et surtout `_build_namespaced_top_level_disciplines`
lui applique `apply_namespace_to_disciplines(…, global_namespace)`, ce qui
transformerait `{r}:fuel_demand` en `overall:{r}:fuel_demand`. **`top_level_models` est
structurellement le mauvais point d'accroche** : il est fait pour consommer les
agrégats, pas pour boucler entre régions.

---

## Questions annexes

### Comment enregistrer une discipline hors namespacing ?

Aucun mécanisme n'existait. `RegionalAggregator` était la seule discipline non
namespacée du système, et elle est câblée en dur dans `_build_top_level_disciplines`.

Un point d'accroche a été ajouté (commit `aaf71547`) : bloc
`regionalisation.global_models`, même structure `standards`/`customs` qu'un bloc
`models` régional. Une discipline globale est enveloppée **sans namespacing** — sa
grammaire est écrite directement en termes namespacés, exactement comme celle de
l'agrégateur. `_wrap_global_model` injecte la liste des régions et le namespace
global, **puis appelle `custom_setup()`**, ce qui permet le patron « registre + YAML
propre au module ». La déclarer en `separate_processes` lève désormais une erreur au
lieu d'être ignorée silencieusement.

### `_coupling_defaults` peut-il être amorcé par une trajectoire calculée ?

**Oui, sans réserve.** `_coupling_defaults` n'est qu'un dict fusionné dans
`default_input_data` du wrapper (`core/gemseo.py`, `update_defaults`), construit dans
`_initialize_df()` où `self.parameters` et l'index annuel sont déjà disponibles. Rien
n'impose une série constante ; c'est une convention des modèles actuels.

Mesuré (`seed_probe.py`, jouet à `stiffness=0.3`, `gamma=15`, tolérance 1e-10) :

| amorce | itérations |
|---|---|
| constante non informée | 125 |
| constante à la solution exacte | **1** |
| trajectoire calculée (rampe) | 125 |
| trajectoire calculée volontairement fausse (×10) | 124 |

L'amorce est bien prise en compte — l'amorce exacte converge en une itération. Mais
**l'amorçage achète de la vitesse, pas de la stabilité.** Au-delà de `gamma* ≈ 20.6`
le point fixe est répulsif et aucune amorce ne convertit ça en convergence. Mesuré à
`gamma=25` :

| amorce | itérations | résidu | x rendu | x vrai |
|---|---|---|---|---|
| constante non informée | 167 | 7.7e-01 | 0.987886 | 0.955329 |
| constante à la solution exacte | 8 | 1.0e+00 | 0.955329 | 0.955329 |
| trajectoire calculée | 11 | 1.1e+00 | 0.955329 | 0.955329 |

Le piège est net : avec une bonne amorce, le solveur **rend la bonne valeur tout en
n'ayant jamais convergé** (résidu 1.0, arrêt sur `max_consecutive_unsuccessful_iterations`).
Sans vérification du statut de convergence en aval, rien ne distingue ce cas d'un
calcul sain — et la ligne du dessus, non informée, rend une valeur fausse de 3 % avec
le même silence. Pour une offre raide, c'est le damping ou l'accélération qu'il faut,
pas une meilleure amorce.

### Autres angles morts de `unified_mda`

1. **Le mode n'avait jamais résolu de cycle** (cf. § 1). Tout ce qui touche au
   solveur y est non testé par construction.
2. **Réglages MDA incohérents entre les modes.** `_setup_unified_mda` utilise
   `tolerance=1e-5` **sans `max_mda_iter`**, donc le défaut GEMSEO de **20
   itérations** — alors que `AeroMAPSProcess` utilise `tolerance=1e-10,
   max_mda_iter=200`. Le nominal de l'étape 2 en demande 22, et 111 à
   `stiffness=30` : le mode multi-régional se serait arrêté avant, en silence.
   Le spike avait proposé un bloc `regionalisation.mda` ; **il a été retiré en
   revue de #157** — les réglages MDA restent sur les objets GEMSEO, réglés depuis
   le notebook, comme le fait `AeroMAPSProcess`. Le spike applique donc les siens
   via `spike_unified_mda/mda_settings.py`. **L'écart de réglage entre les deux
   modes subsiste** : c'est une décision à prendre à part, car l'aligner change les
   résultats des scénarios multi-régionaux existants.

   Corollaire découvert en revue, et c'est un piège GEMSEO à part entière :
   `MDAChain` ne transmet à ses MDA internes que les champs de `BaseMDASettings`
   (`tolerance`, `max_mda_iter`, `warm_start`, `log_convergence`…).
   `over_relaxation_factor` et `acceleration_method` **n'en font pas partie** :
   passés en kwargs de `MDAChain`, ils configurent la chaîne externe et sont
   ignorés par le solveur qui itère réellement. Seul `inner_mda_settings` y mène.
   Et après construction, seules les *propriétés* `inner_mdas[i].over_relaxation_factor`
   / `.acceleration_method` écrivent jusqu'au `RelaxationAcceleration` ; assigner à
   `inner_mdas[i].settings.*` n'a aucun effet. `tolerance` et `max_mda_iter`, eux,
   sont relus à chaque itération et se règlent bien après coup.
3. **Récolte des sorties.** `_update_data_from_unified_mda` ne collectait de
   `local_data` que les clés préfixées `{global_namespace}:`. Les sorties d'une
   discipline globale (préfixées par une région, ou sans préfixe) n'atteignaient
   jamais `data["vector_outputs"]`. Corrigé dans le même commit.
4. **Duplication des colonnes** sur `compute()` répété (§ 3), les deux modes.
5. **Non-convergence silencieuse.** Aucun des deux `compute()` ne vérifie le statut
   du MDA. Combiné au plancher de résidu du § 2, un scénario peut aujourd'hui rendre
   un résultat faux sans qu'aucun signal ne remonte au-delà d'un `WARNING` GEMSEO.
6. L'agrégation `overall:` fonctionne normalement en présence d'une discipline
   globale (`overall:rpk` correct, somme des deux régions).

### Si quelque chose casse : réparable, en combien de temps ?

Rien n'est structurellement bloqué. Chiffrage, du plus urgent au moins :

| chantier | effort |
|---|---|
| Point d'accroche `global_models` | **fait** (PR #157) |
| Duplication des colonnes sur `compute()` répété | **fait** (PR #157) |
| NaN dans les couplages → plancher de résidu | **fait** (§ 2). Deux lignes dans deux modèles, plus un test de non-régression. Ce n'était pas le sentinel : une discipline mutait son entrée de couplage en place et écrasait l'itéré précédent du solveur. `core/gemseo.py` reste inchangé, NaN reste NaN. |
| Faire échouer bruyamment une MDA non convergée | **1 j**. Lire le statut après `execute()` et lever, ou avertir explicitement. |
| Aligner les réglages MDA de `unified_mda` sur `AeroMAPSProcess` | **0.5 j** + revalidation des scénarios existants |
| Exposer damping / accélération et choisir un défaut | **1 j** (`inner_mda_settings` est en place avec les défauts GEMSEO ; il reste à décider du défaut) |
| Jacobiennes pour `MDANewtonRaphson` | **non chiffré, hors périmètre.** Inutile au vu des § 4. |

Soit **une à deux semaines** pour amener `unified_mda` au niveau de fiabilité qu'exige
un module de marché du carburant — dont l'essentiel n'est pas du travail de couplage
mais de l'hygiène de convergence, utile au reste d'AeroMAPS.

---

## Contenu de la branche

Les trois correctifs, indépendants du spike, ont été extraits dans la **PR #157**
(`fix/mda-residual-floor-and-global-disciplines`), sur laquelle cette branche est
maintenant rebasée :

| correctif | contenu |
|---|---|
| `global_models` | point d'accroche non namespacé + récolte des sorties globales |
| duplication | plus de duplication de colonnes sur `compute()` répété |
| mutation d'entrée | plancher de résidu, + test de non-régression |

Il ne reste donc sur cette branche que `spike_unified_mda/` — code jetable, aucune
modification d'AeroMAPS.
Le tutoriel deux régions donne des résultats identiques avant/après dans les deux modes
(CO2 `overall` 2050 = 78.4606), et `pytest aeromaps/tests/core` passe (26/26).

Le diagnostic NaN (`nan_floor_probe.py`) est un **instrument de mesure, pas un
correctif proposé** : il monkey-patche `CustomDataConverter` à l'exécution et ne touche
pas au dépôt.

### Reproduire

```bash
python -m spike_unified_mda.step1_plumbing        # critères 1-2, jouet
python -m spike_unified_mda.step1_criteria 3      # critère 3, jouet
python -m spike_unified_mda.step1_threshold       # critère 4, seuils (long)
python -m spike_unified_mda.step1_remedies        # damping / accélération / Newton
python -m spike_unified_mda.step_criterion5       # critère 5
python -m spike_unified_mda.nan_floor_probe [--neutralise]
python -m spike_unified_mda.nan_impact_check {stock,neutralised,compare}
python -m spike_unified_mda.step2_criteria 1234 --neutralise   # chaîne réelle
python -m spike_unified_mda.step2_remedies
python -m spike_unified_mda.seed_probe
```

Les réglages MDA du scénario spike (`tolerance=1e-10`, `max_mda_iter=200`, damping,
accélération, `inner_mda_name`) sont appliqués par `spike_unified_mda/mda_settings.py`
sur les objets GEMSEO du process, et non par le fichier de configuration.
