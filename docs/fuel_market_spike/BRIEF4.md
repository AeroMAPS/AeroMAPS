# Module de marché des carburants — étape 1
## Brief pour Claude Code · semaine du 21 septembre 2026

**Dépôt :** AeroMAPS · **Base :** branche de travail courante, correctifs de convergence inclus (dernière référence connue : `fix/mda-convergence-strictness` @ `b74b8e12`) · **Branche à créer :** `feat/fuel-clearing-step1`

**À lire avant de commencer (fournis avec ce brief) :**
- `saf_market_skeleton.py` et `test_rampup.py` : références de formulation. **Ne pas les reprendre tels quels** : ils décrivent une variante à capacité endogène qui n'est pas celle de l'étape 1 (décision 4).
- `spike_unified_mda/BRIEF1.md` et le rapport du spike : motif de discipline globale déjà validé.

---

## 0. Objet

Ajouter à AeroMAPS un **nouveau mode d'utilisation**, dans lequel un marché détermine les volumes et les prix des carburants, au lieu de l'allocation par mandat exogène (`EnergyUseChoice`).

**Le mode actuel n'est pas remplacé.** Il reste le mode par défaut, strictement inchangé : `EnergyUseChoice`, parts de carburant comme variables de décision, contrainte de ramp-up de l'optimisation. Les deux modes coexistent et répondent à des questions différentes : les parts optimales d'un côté, l'effet d'une politique de l'autre.

Étape 1 : deux régions, une filière durable et le kérosène, mandat exogène, pénalité libératoire, ramp-up.

Questions auxquelles la semaine doit répondre :
1. Le marché reproduit-il l'allocation actuelle quand on lui donne les mêmes parts comme mandat ?
2. La boucle trafic reste-t-elle stable une fois le marché branché, et pour quelles valeurs du paramètre de saturation `n` ?
3. Comment les prix se comportent-ils quand le mandat devient inatteignable ?

**Hors périmètre, ne pas élargir :**
- flux entre régions ;
- plus d'une filière durable, matrice d'éligibilité ;
- instruments autres que mandat et pénalité ;
- coût du capital endogène ;
- version myope ;
- neuf régions ;
- optimisation dans le nouveau mode.

---

## 1. Décisions actées — ne pas rouvrir

| # | Décision | Raison |
|---|---|---|
| 0 | **Nouveau mode d'utilisation**, à côté du mode actuel, qui reste le défaut et n'est pas modifié | Les deux modes répondent à des questions différentes |
| 1 | Un seul calcul sur tout l'horizon prospectif, vectorisé (anticipation parfaite) | Cohérent avec AeroMAPS ; le ramp-up couple les années entre elles |
| 2 | Programme convexe résolu par un solveur dédié (`cvxpy` + Clarabel) dans `compute()`. Ni sous-boucle de couplage, ni sous-scénario d'optimisation GEMSEO | Prix = multiplicateurs natifs, précision certifiée, résultat indépendant du point de départ |
| 3 | Ramp-up endogène, écrit comme contrainte du programme, **sur la production** | Dans le nouveau mode, les volumes sont des résultats : la vérification a posteriori par l'optimiseur n'y a plus de levier |
| 4 | Capacité `K` **exogène** à l'étape 1 ; elle ne sert qu'à la saturation | Le coût top-down est un coût complet : une capacité sans coût propre ferait dégénérer un ramp-up sur la capacité en enveloppe indépendante de la production réelle |
| 5 | Saturation souple : coût marginal `c·(1 + γ·(q/K)^n)` à la place d'une contrainte de capacité dure | Une contrainte dure rend les prix en escalier et déstabilise la boucle trafic |
| 6 | Coût d'entrée : `{p}_mean_mfsp` du modèle `top-down`. Lever une erreur si `cost_model != "top-down"` | Le modèle bottom-up lit les volumes : boucle volume → prix → volume |
| 7 | Pénalité libératoire toujours présente (variable d'écart). Le volume couvert par la pénalité est une sortie | Sans elle, un mandat inatteignable rend le problème infaisable |
| 8 | Coût du capital exogène | Reporté à une deuxième version |
| 9 | Zéros, jamais de NaN, dans toutes les sorties | Un motif de NaN qui bouge avec la solution casse le solveur de couplage |
| 10 | Tarification : `market_mfsp = (1 − w)·coût_production + w·prix_marginal`, avec `w` le θ du plan de route v3. `w = 0` reproduit la tarification actuelle | À `w = 0` et paramètres lâches, le nouveau mode doit redonner les résultats du mode actuel : c'est le test de cohérence entre les deux |
| 11 | Échecs bruyants : assertions qui lèvent, aucun avertissement rendu muet | L'aval ne détecte pas seul une rupture de bilan |

---

## 2. J1 — Préalables et inventaire

### 2.1 Correctif bloquant

Dans `core/multi_regional_process.py`, `_setup_unified_mda` (vers la ligne 707) construit la chaîne avec `tolerance = 1e-5` et sans `max_mda_iter`, donc avec 20 itérations. Les cas raides du banc en demandent 46.

À faire :
- rendre les deux réglables ;
- aligner leurs défauts sur ceux de `separate_processes` (correctif #157) ;
- ajouter un test qui échoue avant le correctif et passe après ;
- corriger le CHANGELOG, qui affirme que le correctif couvrait déjà ce mode.

C'est la seule modification de code partagé par les deux modes. Vérifier qu'elle ne change aucun résultat du mode actuel : suite de tests existante verte, sans modification.

### 2.2 Vérifications

- La pull request de corrections et la correction de sélectivité du kérosène sont-elles mergées ? Sinon, s'arrêter et le signaler.
- Les scripts du banc appellent `warnings.filterwarnings("ignore")` à l'import. Ajouter `warnings.resetwarnings()` dans tout script utilisé cette semaine.

### 2.3 Inventaire à rendre (court fichier `INVENTORY.md`)

1. **La contrainte de ramp-up actuelle** utilisée par l'optimisation : nom, fichier, formule exacte. Préciser :
   - si elle porte sur des parts ou sur des volumes ;
   - si c'est une croissance relative ou un incrément de part ;
   - la valeur de la limite et l'amorce éventuelle.
2. **Les variables de décision** de parts de carburant, et comment la contrainte ci-dessus s'y rattache.
3. **Les sorties d'`EnergyUseChoice`** et, pour chacune, les disciplines qui la lisent. Le marché devra émettre exactement celles qui sont lues, sous le même nom et dans la même unité.
4. **Le nom de la demande énergétique totale** par région qu'`EnergyUseChoice` consomme.
5. **Le traitement des années historiques** par `EnergyUseChoice`. Le marché n'agit que sur les années prospectives ; les années historiques doivent être recopiées à l'identique.
6. **Le motif de discipline globale** du spike (`model_type="custom"`, noms construits dans `custom_setup()`) et la restriction de `_wrap_top_level_model()` (vers la ligne 386) sur les modèles qui réclament `pathways_manager`. Le marché en a-t-il besoin ? Si oui, passer la liste des filières par configuration.
7. **Comment AeroMAPS définit aujourd'hui ses modes d'utilisation** (configuration, construction du processus). Le nouveau mode suit la même convention plutôt que d'en inventer une.

### 2.4 Jeu d'entrée de référence

Un run de référence à deux régions :
- configuration du banc N-régions, sauf indication contraire ;
- **parts de carburant fixées, non optimisées** ;
- `cost_model="top-down"`.

Exporter, pour chaque région × année prospective :
- la demande énergétique totale ;
- `{p}_mean_mfsp` par filière ;
- les volumes alloués par filière (sorties d'`EnergyUseChoice`) ;
- `{at}_mean_mfsp` par type d'avion ;
- la production durable de la dernière année historique, qui sert de condition initiale du ramp-up.

Format : parquet + `metadata.json` (commit, configuration, unités). Emplacement : `tests/fixtures/fuel_clearing/`.

---

## 3. J2–J3 — Le noyau `clear_market`

### 3.1 Principe

Une **fonction pure** : tableaux numpy en entrée, tableaux numpy en sortie, aucun import d'AeroMAPS. C'est ce code que `FuelClearing.compute()` appellera tel quel ; il n'y a donc pas de modèle séparé à recoller plus tard.

Entrées et sorties sont regroupées en `dataclass`. Choisir l'emplacement en cohérence avec l'arborescence des modèles, par exemple `.../fuel_clearing/kernel.py`.

Dimensions : `R` régions, `P` carburants, `T` années prospectives.

**Entrées**

| Nom | Forme | Sens |
|---|---|---|
| `demand` | R×T | demande énergétique totale |
| `cost` | R×P×T | coût de production par unité d'énergie |
| `is_sustainable` | P | compte pour le mandat |
| `mandate_share` | R×T | part minimale de durable |
| `buyout_price` | R×T | pénalité libératoire par unité manquante |
| `capacity` | R×P×T | K exogène ; `inf` pour le kérosène |
| `sat_gamma` | R×P | intensité de la saturation |
| `sat_n` | scalaire | raideur de la saturation |
| `rampup_form` | `"relative"` ou `"share_increment"` | forme choisie d'après l'inventaire 2.3.1 |
| `rampup_limit` | R×P | g (forme relative) ou Δ (incrément de part) |
| `rampup_seed` | R×P | amorce, forme relative seulement |
| `q_init` | R×P | production de la dernière année historique |
| `discount_rate` | scalaire | actualisation intertemporelle |
| `pricing_weight` | scalaire | `w` de la décision 10 |

**Sorties**

| Nom | Forme | Sens |
|---|---|---|
| `volume` | R×P×T | production = consommation (pas de flux à l'étape 1) |
| `unmet` | R×T | volume couvert par la pénalité |
| `energy_price` | R×T | multiplicateur du bilan énergétique |
| `compliance_price` | R×T | multiplicateur du mandat, toujours ≤ `buyout_price` |
| `rampup_price` | R×P×T | multiplicateur de la contrainte de ramp-up |
| `marginal_price` | R×P×T | `energy_price + compliance_price·is_sustainable` |
| `market_mfsp` | R×P×T | règle de la décision 10 |
| `rent` | R×P×T | `(marginal_price − coût_unitaire_moyen)·volume`, avec `coût_unitaire_moyen = c·(1 + γ/(n+1)·(q/K)^n)` |
| `diagnostics` | — | statut, temps de calcul, correction de fermeture, élasticité (option 3.4) |

### 3.2 Programme

```
min  Σ_t δ_t · [ Σ_{r,p} ( c·q + c·γ·K/(n+1)·(q/K)^(n+1) )  +  Σ_r B·x ]

s.c. Σ_p q[r,p,t]                      = D[r,t]             bilan énergétique
     Σ_{p durable} q[r,p,t] + x[r,t]   ≥ m[r,t]·D[r,t]      mandat
     ramp-up, filières durables seulement, avec q[r,p,-1] = q_init :
       "relative"         q[r,p,t]        ≤ seed + (1+g)·q[r,p,t-1]
       "share_increment"  q[r,p,t]/D[r,t] ≤ q[r,p,t-1]/D[r,t-1] + Δ
     q ≥ 0,  x ≥ 0
```

L'actualisation vaut `δ_t = (1 + discount_rate)^(−t)`. Le terme de saturation est omis quand `K = inf`.

Avec K exogène, le terme de saturation est une puissance de q multipliée par une constante (`cp.power(q, n+1)`), convexe pour n ≥ 0. Il n'y a aucun cône à construire à la main.

**Points de mise en œuvre**

- **Mise à l'échelle.** Diviser les énergies par `D_ref = demand.max()` et les coûts par une référence (coût moyen du kérosène) avant le calcul ; remettre à l'échelle après. Les multiplicateurs se remettent à l'échelle par le facteur de coût ; le vérifier sur le cas analytique 3.3.a.
- **Prix courants.** Diviser les multiplicateurs par δ_t.
- **Signes.** Les conventions de `cvxpy` sur les égalités sont piégeuses : les fixer par le test analytique, pas par la documentation.
- **Solveur.** Clarabel, tolérances resserrées (ordre de 1e-9). Tout statut autre que `optimal`, y compris `optimal_inaccurate`, lève une exception avec diagnostic.
- **Aucun démarrage à chaud.** Chaque appel repart de zéro, pour que la sortie ne dépende que des entrées.
- **Fermeture exacte du bilan.** Après le calcul, recalculer le kérosène comme `D − Σ autres`, pour un bilan exact au MJ près. Mais **lever** si la correction appliquée dépasse la tolérance du solveur rapportée à D : la fermeture absorbe du bruit numérique, jamais une erreur.
- **Comportement attendu, pas un bogue.** Avec l'anticipation parfaite et un ramp-up qui mord, le programme peut produire du durable au-delà du mandat dans les premières années, pour préparer les mandats suivants. Le signaler dans le rapport.

### 3.3 Tests (`pytest`)

a. **Cas analytique** — 1 région, 1 année, saturation connue. On doit trouver `energy_price` = coût du kérosène, et `compliance_price` = coût marginal du durable au volume du mandat − coût du kérosène. Ce test fixe les signes et la mise à l'échelle.

b. **Bilan** — exact après fermeture, correction sous la tolérance.

c. **Reproduction** — sur le jeu d'entrée 2.4, avec mandat = parts de référence, K très grand, ramp-up lâche et pénalité élevée. Les volumes doivent égaler la référence à 1e-6 près en relatif. Si le durable est moins cher que le kérosène une année donnée, un écart est attendu et correct : le documenter.

d. **Pénalité** — avec un ramp-up serré et un mandat inatteignable : statut optimal, `unmet > 0`, et `compliance_price == buyout_price` sur les années concernées.

e. **Ramp-up** — la croissance réalisée reste sous la limite partout (assertion). En forme relative sans amorce, une filière à zéro reste à zéro : un test documente ce verrou.

f. **Continuité des prix** — balayer un facteur multiplicatif du mandat, 200 points de 0,5 à 2. `compliance_price` ne doit pas sauter entre deux points voisins : l'écart reste borné par une constante × le pas. Enregistrer la figure.

g. **Déterminisme** — deux appels identiques donnent des sorties identiques au bit près, y compris si un appel différent s'intercale.

h. **Zéros** — aucune NaN, dans aucun cas de test.

i. **Échelle** — demande × 1000 donne volumes × 1000 et prix inchangés.

j. **Temps de calcul** — rapporter le temps pour 2 régions, et pour un cas synthétique de 9 régions × 10 filières × 35 ans sans flux, pour anticiper la suite.

### 3.4 Élasticité diagnostique

Option `compute_elasticity=False` par défaut. Si elle est activée :
- lancer un second calcul avec `demand × (1 + 1e-3)` ;
- sortir `d ln(prix moyen livré) / d ln(demande)` par région × année.

Cette élasticité est **évaluée au point de fonctionnement** : la nommer ainsi partout. Le prix moyen livré est la moyenne des `market_mfsp` pondérée par les volumes.

---

## 4. J4–J5 — Branchement dans la chaîne

### 4.1 Discipline `FuelClearing`

- Discipline globale, sur le motif validé par le spike.
- Lit, pour chaque région `r` :
  - `{r}:{p}_mean_mfsp` ;
  - la demande énergétique totale (nom trouvé à l'inventaire 2.3.4) ;
  - les paramètres de la section 3, déclarés comme paramètres de scénario selon le mécanisme existant.
- Écrit, pour chaque région :
  - `{r}:{p}_market_mfsp` ;
  - `{r}:{p}_energy_consumption` et `{r}:{p}_energy_production` ;
  - toutes les sorties d'`EnergyUseChoice` lues en aval (inventaire 2.3.3).
- Années historiques recopiées à l'identique (inventaire 2.3.5).

### 4.2 Le nouveau mode

Un mode d'utilisation à part entière, activé par configuration selon la convention trouvée à l'inventaire 2.3.7 (à défaut, une option `fuel_market`, à `false` par défaut). Le mode actuel reste le défaut et n'est pas touché.

Dans le nouveau mode :
- `EnergyUseChoice` n'est pas instancié ;
- `EnergyCarriersMeans` lit `{p}_market_mfsp` au lieu de `{p}_mean_mfsp`. C'est un changement de nom d'entrée, sans aucune modification de logique ;
- les parts de carburant ne sont pas des variables de décision, et la contrainte de ramp-up de l'optimisation n'est pas utilisée ;
- lever une erreur si `cost_model != "top-down"`.

**Garde-fou :** la suite de tests existante passe sans modification, et un run de référence du mode actuel est identique au bit près avant et après la branche.

### 4.3 Assertions après convergence

Vérifier le bilan énergétique par région × année, et la cohérence du facteur d'émission avec les volumes. Ces identités portent sur un couplage : les vérifier après convergence de la chaîne, pas dans `compute()`.

### 4.4 Premier run couplé

Deux régions, boucle trafic fermée, `w = 0`, paramètres du test 3.3.c. La sortie doit coïncider avec le run de référence du mode actuel à la tolérance de couplage près. Rapporter les itérations et le résidu final.

### 4.5 Mesures pour le rapport

1. **Compromis sur `n`.**
   - Grille : `n` ∈ {2, 4, 6, 8, 12, 16}, deux niveaux de K (lâche, serré), `w` ∈ {0, 1}.
   - La raideur ne peut affecter la boucle trafic qu'à `w > 0`, puisqu'à `w = 0` le prix transmis est le coût de production.
   - Relever : convergence oui ou non, itérations, résidu final, cycle limite détecté, élasticité au point de fonctionnement.
   - Rendre un tableau et une figure.
2. **Régimes de prix.**
   - Facteur multiplicatif du mandat de 0,5 à 2, ramp-up à la valeur trouvée à l'inventaire.
   - Relever : `compliance_price`, `unmet`, années où le ramp-up mord, `rampup_price`, prix moyen livré, trafic.
   - Rendre une figure.
3. **Optionnel — relaxation.** Le facteur de relaxation du mode unifié est fixé à 1,0 sans réglage possible. S'il est simple de le rendre configurable, refaire le cas le plus raide de la mesure 1 avec 1,0, 0,7 et 0,4.

---

## 5. Règles de travail

- **Priorités si le temps manque :** section 2, puis section 3, puis 4.1 à 4.4, puis 4.5.
- **Doute sur le code existant :** s'arrêter et signaler plutôt que deviner.
- **Commits :** petits, nommés par étape.
- **Rapport final :** `fuel_clearing_step1/REPORT.md`, avec ce qui marche, les mesures, les écarts à ce brief et leur raison.

## 6. Critères de fin de semaine

- [ ] Correctif `_setup_unified_mda` mergé, test à l'appui
- [ ] `INVENTORY.md` et jeu d'entrée de référence
- [ ] Noyau et tests 3.3.a à 3.3.i verts
- [ ] Nouveau mode opérationnel ; mode actuel strictement inchangé (tests existants verts sans modification) ; premier run couplé qui retrouve les résultats du mode actuel
- [ ] Mesures 4.5.1 et 4.5.2, avec figures
