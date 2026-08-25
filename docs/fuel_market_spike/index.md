# Spike `unified_mda` et marché du carburant — dossier

Tous les documents produits entre le 19 et le 25 août 2026 autour du spike
`unified_mda` (discipline globale non namespacée) et de sa suite côté marché du
carburant. Ils sont rassemblés ici pour ne plus vivre à la racine du dépôt ou dans
`spike_unified_mda/`.

Ce dossier est **exclu du site mkdocs** (`exclude_docs` dans `mkdocs.yml`) : ce sont des
notes de travail internes, pas de la documentation utilisateur. Retirer les deux lignes
d'`exclude_docs` suffit à les publier.

## Les documents

| document | langue | ce qu'il établit |
|---|---|---|
| [RAPPORT.md](RAPPORT.md) | fr | Le rapport du spike lui-même : assemblage, convergence, idempotence, marge de robustesse, rejet par `_wrap_top_level_model`. **Verdict : architecture confirmée**, il manquait un point d'accroche (`regionalisation.global_models`), pas une propriété du solveur. `RAPPORT.html` en est le rendu. |
| [BRIEF1.md](BRIEF1.md) | en | D'où vient la sortie de domaine et quelle forme a la divergence. La ligne exacte qui fabrique le NaN, pourquoi l'airfare devient négatif, et le tableau chiffré des « totality fixes » — dont deux sont implémentés dans la PR #157. |
| [BRIEF2.md](BRIEF2.md) | en | `dD/dp_SAF` en forme close, validée à 0,000 % contre le MDA convergé. Deux constats structurels : `d alpha / d p_SAF` est identiquement nul dans le code actuel, et la « fonction d'offre » n'est pas un coefficient de pass-through. |
| [BRIEF3.md](BRIEF3.md) | en | Contrat d'I/O pour remplacer `EnergyUseChoice` par un module de marché : une seule famille de variables à émettre, un invariant de somme que rien ne vérifie, et ce qu'un marché devra apporter qu'aucune variable ne porte aujourd'hui (rareté contraignante, délai de construction, prix de clearing, learning). |
| [RECAP-2026-08-25.md](RECAP-2026-08-25.md) | fr | Récapitulatif d'avancement, destiné au suivi de projet : ce qui a été trouvé, ce qui a été corrigé, l'état des PR et ce qui reste ouvert. |
| [KEROSENE-SELECTIVITY-BUG-MEMO.md](KEROSENE-SELECTIVITY-BUG-MEMO.md) | en | Memo de bug indépendant du spike, sur la même famille de sujets (carburants) : la sélectivité kérosène était ignorée **et** inversée dans le modèle bottom-up. Corrigé par la PR #158. |

## Deux conclusions ont été révisées en cours de route

À lire avant de citer un chiffre pris dans une version antérieure :

- **RAPPORT § 4** — les cas durs ne convergent pas, ils partent en NaN. Le sentinel NaN
  se différenciant avec lui-même à zéro, le solveur annonçait la convergence sur un état
  sans valeurs. L'accélération n'achète que de la vitesse à l'intérieur du domaine, elle
  ne déplace pas le plafond, qui est plus bas qu'annoncé au départ.
- **BRIEF1 § 4.3** — la moyenne DOC dans une année sans trafic n'est pas zéro. Ce qui est
  indéfini, c'est la pondération, pas l'intensité ; ces années prennent la moyenne non
  pondérée.

## Base de mesure

La branche du spike est rebasée sur `fix/mda-convergence-strictness`, c'est-à-dire sur
les correctifs qu'elle a elle-même fait remonter. Un chiffre a bougé avec cette base :
la composante fortement connexe de l'étape 2 compte **113** disciplines et non 109,
parce que le passage des subventions et taxes carburant au tarif crée de nouveaux
couplages. Convergence inchangée (18 itérations, résidu 6,4e-11). Les briefs, mesurés
avant ce correctif, citent 109.

## Où vit le code

- `spike_unified_mda/` — le code du spike, jetable, aucune modification d'AeroMAPS :
  disciplines jouet, scénario deux régions, scripts d'étape et scripts de mesure des
  briefs 1 et 2. La section « Reproduire » de chaque document donne les commandes.
- Les correctifs, eux, sont dans AeroMAPS et suivis par la **PR #157**
  (`fix/mda-residual-floor-and-global-disciplines`, empilée avec
  `fix/mda-convergence-strictness`) et la **PR #158**
  (`fix/bottom-up-kerosene-selectivity`).
