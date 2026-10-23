# Céleste pour Home Assistant

> Éphémérides du Soleil, de la Lune, des planètes, des astéroïdes et des comètes, et temps astronomique,
> sous forme de capteurs Home Assistant.

![HACS](https://img.shields.io/badge/HACS-personnalisé-orange)
![Licence](https://img.shields.io/badge/Licence-MIT-green)
![Vérifications](https://github.com/Greg50100/Celeste_HA/actions/workflows/ci.yml/badge.svg)

**Projet actif** · fait partie de la famille Ganymede : [site web](https://greg50100.github.io/personnal-site/) ·
[application Android](https://github.com/Greg50100/Ganymede) · [Céleste (bureau)](https://github.com/Greg50100/Celeste_App)

Céleste réunit les deux intégrations d'astronomie précédentes : celle-ci (service en ligne de l'IMCCE) et
[ha-meeus-astronomy](https://github.com/Greg50100/ha-meeus-astronomy) (jour julien et calendrier de Jean Meeus).

---

## Trois types de suivi

| Type | Source | Réseau | Mise à jour |
|------|--------|--------|-------------|
| **Soleil, Lune ou planète** | Calcul local avec [Astronomy Engine](https://github.com/cosinekitty/astronomy), le même moteur que le site Ganymede | Non | Toutes les minutes |
| **Autre objet** (astéroïde, comète, satellite naturel) | Service [Miriade de l'IMCCE](https://ssp.imcce.fr/webservices/miriade/) (Observatoire de Paris) | Oui | Toutes les heures |
| **Temps astronomique** | Calendrier de Jean Meeus et Astronomy Engine | Non | Toutes les minutes |

Pour une planète, les options permettent de passer du calcul local au service de l'IMCCE.

## Entités créées

**Soleil, Lune, planètes (calcul local)**

- Hauteur, azimut, constellation
- Lever, passage au méridien, coucher (horodatages du jour, en UTC)
- Magnitude, élongation, distance, angle de phase et fraction éclairée
- Lune : nom de la phase, âge, distance en km
- Capteurs binaires : **Au-dessus de l'horizon** (« **Jour** » pour le Soleil) et **Visibilité** (élongation de plus de 15°
  et, si réglé, magnitude sous un seuil)

**Autre objet (IMCCE)** : magnitude, élongation, distance, angle de phase, vitesse radiale et capteur de visibilité.

**Temps astronomique** : jour julien, jour julien modifié, jours depuis J2000, jour de la semaine, jour de l'année,
temps sidéral local et de Greenwich, équation du temps.

## Services

| Service | Rôle | Exemple de réponse |
|---------|------|--------------------|
| `celeste.convert_to_julian_day` | Date grégorienne (TU) → jour julien | `julian_day: 2461336.5`, `day_of_week: vendredi` |
| `celeste.convert_to_gregorian` | Jour julien → date grégorienne (TU) | `formatted: 2000-01-01 12:00:00.00` |

Les deux services renvoient une réponse (« Réponse uniquement ») : utilisez-les dans un script avec `response_variable`.

```yaml
action: celeste.convert_to_julian_day
data:
  year: 2026
  month: 10
  day: 23
response_variable: jj
```

## Exemples d'automatisations

```yaml
# Allumer l'éclairage extérieur quand le Soleil se couche
triggers:
  - trigger: state
    entity_id: binary_sensor.celeste_soleil_jour
    to: "off"
actions:
  - action: light.turn_on
    target:
      entity_id: light.terrasse
```

```yaml
# Prévenir quand Jupiter se lève au-dessus de l'horizon la nuit
triggers:
  - trigger: state
    entity_id: binary_sensor.celeste_jupiter_au_dessus_de_l_horizon
    to: "on"
conditions:
  - condition: state
    entity_id: binary_sensor.celeste_soleil_jour
    state: "off"
actions:
  - action: notify.notify
    data:
      message: "Jupiter est levée."
```

Les identifiants d'entités dépendent du nom de l'appareil : vérifiez-les dans Paramètres → Appareils et services.

## Installation

### Avec HACS

1. HACS → menu ⋮ → **Dépôts personnalisés** → ajoutez `https://github.com/Greg50100/Celeste_HA`, catégorie **Intégration**.
2. Recherchez **Céleste**, installez, puis redémarrez Home Assistant.
3. Paramètres → Appareils et services → **Ajouter une intégration** → **Céleste**.

### À la main

Copiez `custom_components/celeste` dans le dossier `custom_components` de votre configuration, puis redémarrez.

## Migration

**Depuis ha-meeus-astronomy** : supprimez l'intégration « Meeus Astronomical Algorithms », installez Céleste et ajoutez
une entrée **Temps astronomique**. Les services deviennent `celeste.convert_to_julian_day` et
`celeste.convert_to_gregorian` (mêmes paramètres). Le jour de la semaine est maintenant en français.

**Depuis Céleste 0.1** : les entrées existantes continuent d'utiliser l'IMCCE. Pour passer au calcul local (sans réseau,
mise à jour chaque minute, nouvelles entités), ouvrez les options de l'entrée et choisissez **Calcul local**.

## Développement

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
pytest
```

L'intégration continue lance les tests, la validation **hassfest** de Home Assistant et la validation **HACS**.

## Crédits

- Calcul local : [Astronomy Engine](https://github.com/cosinekitty/astronomy), Don Cross, licence MIT.
- Éphémérides en ligne : [IMCCE, service Miriade](https://ssp.imcce.fr/webservices/miriade/).
- Calendrier : Jean Meeus, *Astronomical Algorithms*, 2e édition, chapitre 7.

## Licence

Projet distribué sous licence MIT : voir le fichier [`LICENSE`](LICENSE).
