#!/usr/bin/env python3
"""
storyworlds/worlds/cortisone_friendship_cautionary_tall_tale.py
===============================================================

A standalone *story world* sketch centered on cortisone use among friends with an
exaggerated, tall-tale style emphasizing *cautionary* lessons about medication safety.

Initial story sketch:
---
Once upon a time, in a dusty Nevada town best known for its jackrabbits and
laughing adults under the big sky, lived a freckled boy named Rigby.
He loved playing with his friends under the blazing sun, chasing jackrabbits and
swimming in the town's only swimming hole.

One scorching afternoon, Uncle Jack pulled into town with his big rig,
wearing a fresh bandage on his elbow. "That ol' hive got me good!" he said.
Rigby noticed a gleaming metal tin on the dashboard: "Corticool Cream — Says it
erases aches!" Uncle Jack laughed. "Nah kid, that's doctor's stuff — cortisone.
You gotta *ask* before you ever *think* about touching it."

But when Uncle Jack nodded off under the mesquite tree later, Rigby leaned
inside the cab. His fingers trembled as he popped the tin. One dab of the white
gel on his knees made the itchy mosquito bites vanish instantly. "Woo-eee!"
he whooped, racing to his friends Alonzo, Mai, and Javi.

"Guys! Guys! This stuff's amazing!" Rigby said, handing globs to each of them.
Mai slathered it on her sunburned shoulders. Alonzo rubbed circles on his sore knees.
Javi didn't think twice — he scooped a *fingerful* and took a swig.

By sunset, Rigby's arms were sprouting fern-green splotches that glowed under
the sheriff's neon. Mai's shoulders shimmered like polished silver, and her hair
hung down past her knees in silvery threads. Alonzo's knees swelled into
watermelons that bounced when he walked. Javi's tongue turned neon coral and he
could only communicate in rhyming couplets that made the whole playground howl.

Their parents, gathered at the sheriff's office for monthly bingo night, rushed
home to find their darlings looking *most* peculiar. Dr. Hayes arrived at their
doorstep, sat down under the porch swing, and calmly explained that Uncle Jack's
cortisone cream was not "magic," but "a powerful medicine that must only be
used when a doctor says and *exactly* how they say."

The next morning the group stood in Uncle Jack's yard, a fresh tin in Rigby's
pocket. "It's not a toy," Mai read from a label she'd carefully peeled off the
back. "It's *doctor-approved*." They applied a dab each — only to their *own*
itchy knees and mosquito bites — and watched the green splotches and silver threads
and bouncing watermelons gently melt away like morning dew under prairie sun.

Rigby hugged each friend and promised, "I'll keep the rule: never touch what’s
not mine *and* never use without asking first." The friends high-fived, their
original shapes returned, and the town grew quieter (except for the jackrabbits,
who remained just as loud).
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude threshold for an effect to be narrated in the tall tale
THRESHOLD = 0.8

# Physical meter keys related to medical effects and transformation
EFFECT_KEYS = {"itchy", "rash", "pain", "itches_cream",
                "green_splotches", "horns", "super_strength",
                "silver_hair", "bouncing_knees", "neon_tongue"}

# Emotional memes for friendship and cautionary themes
MEME_KEYS = {"trust", "excitement", "defiance", "fear", "carefulness",
              "shame", "relief", "joy"}

# Body regions that different medications can affect
REGIONS = {"knees", "shoulders", "elbow", "face", "tongue"}

# Typical side effects of improper cortisone use (tall tale exaggerations)
SIDE_EFFECTS = {
    "itchy": "itchy bites that turn green when touched",
    "rash": "rash that gleams like polished silver",
    "pain": "ache that swells into bouncy watertowers",
    "itches_cream": "itchy spots covered with golden fur shortly after"
}

TALL_TALE_GLOW = {
    "green_splotches": "fern-green glowing splotches",
    "horns": "twin golden horns sprouting instantly",
    "super_strength": "arms bulging like sandbags",
    "silver_hair": "hair extending past knees as silvery threads",
    "bouncing_knees": "knees swelling into watermelons",
    "neon_tongue": "tongue turning neon coral",
    "golden_fur": "skin sprouting golden fur like desert jackrabbit"
}

# Settings in the tall-tale Nevada landscape
SETTINGS = {
    "ranch": {
        "name": "Uncle Jack's dusty ranch",
        "weather": "scorching",
        "sky": "big cloudless",
        "features": "red mesquite trees, sheriff's neon office, single swimming hole"
    },
    "town_square": {
        "name": "the Nevada town square",
        "weather": "dry heat",
        "sky": "desert glare",
        "features": "dusty square with snack bar, monthly bingo night"
    },
    "porch": {
        "name": "the sheriff's porch",
        "weather": "warm evening",
        "sky": "crimson",
        "features": "cracked linoleum and a squeaky swing"
    }
}

# Characters involved in friendship dynamics
CHARACTERS = {
    "Rigby": {
        "type": "boy", "traits": ["freckled", "brave", "nosy"],
        "favorite_place": "mesquite tree shade", "pals": ["Alonzo", "Mai", "Javi"]
    },
    "Alonzo": {
        "type": "boy", "traits": ["thoughtful", "quiet", "family_caretaker"],
        "favorite_place": "shaded bench"
    },
    "Mai": {
        "type": "girl", "traits": ["energetic", "sunburns_easily", "champion_bingo"],
        "favorite_place": "snack_bar_shade"
    },
    "Javi": {
        "type": "boy", "traits": ["impulsive", "rhyming"], "obsessions": ["all things"]
    },
    "Uncle_Jack": {
        "type": "adult", "traits": ["freight_driver", "kind"], "meds": ["corticool_cream"]
    },
    "Dr_Hayes": {
        "type": "doctor", "specialty": "pediatric_allergies",
        "traits": ["measured", "calm"], "tools": ["first_aid_kit"]
    }
}

# Medicine items that can conceal unsafe usage
ITEMS = {
    "corticool_cream": {
        "label": "corticool cream",
        "phrase": "a gleaming metal tin labeled 'Corticool Cream — Use WYD?'",
        "treatable": ["itchy", "rash", "pain"], "side_effects": ["green_splotches", "horns"],
        "proper_use": "rub a pea-sized dab exactly where it itches, no more",
        "adult_required": True
    },
    "itch_spray": {
        "label": "child-safe itch spray",
        "phrase": "a gentle blue spray that smells like aloe",
        "treatable": ["itchy"], "side_effects": [],
        "adult_required": False
    }
}

# Tall-tale exaggerations that can result from misuse
TRANSFORMATIONS = {
    "green_splotches": {
        "name": "fern-green glowing splotches",
        "noun": "splotches", "effect": "shine under neon lights like stars",
        "permanent_unless": "doctor_applied_reversal"
    },
    "horns": {
        "name": "twin golden horns",
        "noun": "horns", "effect": "click together when talking like castanets",
        "permanent_unless": "doctor_applied_reversal"
    },
    "super_strength": {
        "name": "arms bulging like sandbags",
        "noun": "protruding muscles", "effect": "cast shadows twice as long as Rigby",
        "permanent_unless": "time_and_rest"
    },
    "silver_hair": {
        "name": "silvery hair past their knees",
        "noun": "hair", "effect": "catch desert breezes like silver ribbons",
        "permanent_unless": "sun_and_water_wash"
    },
    "bouncing_knees": {
        "name": "watermelon knees",
        "noun": "knees", "effect": "bounce four feet above ground when walking",
        "permanent_unless": "doctor_applied_reversal"
    },
    "neon_tongue": {
        "name": "neon coral tongue",
        "noun": "tongue", "effect": "compose rhyming couplets on demand",
        "permanent_unless": "gel_remover"
    },
    "golden_fur": {
        "name": "golden desert fur",
        "noun": "fur", "effect": "shine like a coin in sunshine",
        "permanent_unless": "moonlight_exposure"
    }
}

# Friendship levels between characters
FRIENDSHIPS = {
    ("Rigby", "Alonzo"): 0.9,
    ("Rigby", "Mai"): 0.85,
    ("Rigby", "Javi"): 0.95,
    ("Alonzo", "Mai"): 0.8,
    ("Mai", "Javi"): 0.75
}

@dataclass
class Entity:
    id: str
    kind: str = "character"  # "character" | "item"
    type: str = ""
    label: str = ""
    phrase: str = ""
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    treats: set[str] = field(default_factory=set)
    side_effects: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "adult": {"subject": "they", "object": "them", "possessive": "their"},
            "doctor": {"subject": "they", "object": "them", "possessive": "their"}
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

@dataclass
class Setting:
    name: str
    weather: str = ""
    sky: str = ""
    features: str = ""

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.transformations: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def items(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "item"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])
            if len(self.paragraphs) < 3:  # limit vertical white space in tall tales
                self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.transformations = set(self.transformations)
        clone.paragraphs = [[]]
        return clone

Rule = dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_apply_medicine(world: World) -> list[str]:
    """Apply medicine: heal targeted regions but possibly trigger side-effects."""
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        for item in world.items():
            if not ("corticool" in item.id.lower() or "itch" in item.id.lower()):
                continue
            # Only apply where actor is itchy/rashy/painful and we're applying EXACTLY where needed
            treat_basis = sum(actor.meters[k] for k in item.treats & actor.meters.keys())
            if treat_basis < THRESHOLD:
                continue
            sig = ("apply_med", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            # Heal the conditions we're treating
            for cond in item.treats:
                if actor.meters[cond] > 0:
                    reduction = min(actor.meters[cond], 1.0)
                    actor.meters[cond] -= reduction
                    actor.memes["relief"] += 0.6
                    if actor.memes["relief"] > THRESHOLD:
                        world.say(f"{actor.id} gasped and wiped {actor.pronoun()} forehead, "
                                f"feeling better already!")
            # Danger: if more than THRESHOLD is applied OR wrong region OR without permission
            total_applied = sum(actor.meters.get(f"applied_{item.id}", 0) for _ in [0])
            exceeds_limit = total_applied > 1.2
            wrong_region = any(actor.meters.get(k, 0) > 0 for k in ["tongue", "face", "full_body"])
            missing_doctor = item.phrase.lower().startswith("corticool") and not item.owner
            if exceeds_limit or wrong_region or missing_doctor:
                for eff in item.side_effects:
                    if eff not in world.transformations:
                        actor.memes["fear"] += 0.8
                        out.append(
                            f"{actor.id}'s {eff.removeprefix('golden_')} began to "
                            f"emerge like a desert oasis blooming in moonlight... "
                            f"and wouldn't stop!"
                        )
                        actor.meters[eff] = 3.5  # massively exceeds threshold
                        world.transformations.add(eff)
            actor.memes["carefulness"] += 0.3
    return out

def _r_spread_effects(world: World) -> list[str]:
    """Tall tale: effects can spread via touch or giggles."""
    out: list[str] = []
    fps = [eids for eids in FRIENDSHIPS.keys() if any(eid in [a.id for a in world.characters()] for eid in eids)]
    for a,b in fps:
        actor_a, actor_b = world.get(a), world.get(b)
        shared_places = set(world.setting.name.split())
        if (actor_a.memes["excitement"] > THRESHOLD and
            actor_b.memes["excitement"] > THRESHOLD and
            sum(w.meters.get(t,0) for t in TRANSFORMATIONS for w in world.characters()) > 2.0):
            for eff in actor_a.meters.keys() & TRANSFORMATIONS.keys():
                if actor_a.meters[eff] >= 1.5:
                    delta = 1.2
                    if eff not in actor_b.meters or actor_b.meters[eff] < 1.0:
                        actor_b.meters[eff] = delta
                        out.append(
                            f"{actor_a.id} reached with {actor.pronoun('possessive')} "
                            f"{TRANSFORMATIONS[eff]['name']} and — PAFFT! — {actor_b.id} "
                            f"acquired the same gleaming glory!"
                        )
                        return out
    return out

def _r_reset_effects(world: World) -> list[str]:
    """Doctor-applied reversal of transformations."""
    for actor in world.characters():
        for eff, tripwire in {
            "green_splotches": "itchy", "horns": "pain",
            "bouncing_knees": "pain", "neon_tongue": "itchy"
        }.items():
            if actor.meters.get(eff, 0) >= THRESHOLD and tripwire in {
                k for item in world.items() for k in item.treats if actor.meters.get(k,0) < THRESHOLD
            }:
                actor.meters[eff] = 0.0
                del world.transformations[eff]
                return [f"Dr. Hayes carefully dabbed a golden gel where the "
                      f"{TRANSFORMATIONS[eff]['name']} had been, and — SHINK! — "
                      f"{actor.id}'s {eff.replace('_',' ')} quietly melted away."]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="apply_med", tag="cortisone_misuse", apply=_r_apply_medicine),
    Rule(name="spread", tag="friendship_contagion", apply=_r_spread_effects),
    Rule(name="reset", tag="doctor_care", apply=_r_reset_effects),
]

def apply_rules(world: World, narrate: bool = True) -> list[str]:
    """Apply causal rules until fixpoint."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

### Narrative verbs ###
def welcome_uncle(world: World) -> None:
    ujack = world.get("Uncle_Jack")
    world.say(
        f"Before the {world.setting.features.split()[0]}, the big rig "
        f"{ujack.phrase.split('—')[0]} belched dust like a dragon sneezing, and "
        f"{ujack.id} climbed down with the tin clutched like it held moonbeams."
    )

def bandage_reveal(world: World) -> None:
    ujack = world.get("Uncle_Jack")
    world.say(
        f"He had a fresh gauze bandage wrapped 'round {ujack.pronoun('possessive')} "
        f"{'elbow' if ujack.type == 'adult' else 'knee'}, still weeping a little. "
        f'"That ol\' hive got me good!" he declared, shaking his hat.'
    )

def hero_itch_discovery(world: World, hero_id: str = "Rigby") -> None:
    hero = world.get(hero_id)
    world.say(
        f"With {hero.pronoun('possessive')} eyes fixed on the gleam, "
        f"{hero.id} sidled near like a jackrabbit lining up a leap. "
        f'One tiny tap of the tin’s rim and — SWOOSH! — the magic mist '
        f'"erase-itch" whispered to {hero.pronoun()} like desert wind.'
    )

def cream_intro(world: World, item_id: str = "corticool_cream") -> None:
    item = world.get(item_id)
    hero = world.get("Rigby")
    world.say(
        f"{hero.id} blinked twice, then read the label aloud: "
        f'"Corticool — Use WYD?" And underneath, in letters '
        f"small enough to ignore: DOCTOR’S STUFF — CORTISONE."
    )
    world.say(f"Uncle Jack had dozed off by the {world.setting.features.split(',')[0]}. "
             f'{hero.pronoun().capitalize()} giggle echoed like a cactus popping.')
    hero.memes["defiance"] += 0.7
    item.owner = hero.id

def share_cream(world: World, sharer: str, friends: list[str]) -> None:
    sharer_e = world.get(sharer)
    for fid in friends:
        friend = world.get(fid)
        if fid == "Javi":
            world.say(
                f'"One finger\'s worth won\'t hurt!" {sharer_e.id} scooped '
                f'a dollop and {sharer_e.pronoun()} shoved it forward like '
                f'a prospector handing over fool\'s gold.'
            )
        else:
            world.say(
                f'{sharer_e.id} grinned and slathered {friend.pronoun("object")} '
                f'{friend.it()} in {friend.pronoun("possessive")} favorite spots.'
            )
        sharer_e.memes["excitement"] += 0.5
        friend.memes["trust"] += 0.3

def transformations_begin(world: World, friends: list[str]) -> None:
    for fid in friends:
        friend = world.get(fid)
        for eff in TRANSFORMATIONS:
            if friend.meters.get(eff,0) > THRESHOLD:
                short = TRANSFORMATIONS[eff]["noun"]
                effect = TRANSFORMATIONS[eff]["effect"]
                world.say(f'{friend.id}’s {short} began '
                        f'{TRANSFORMATIONS[eff]["effect"][:40]}... '
                        f'and kept on going and going!')
                friend.memes["shame"] += 0.5

def parents_arrive(world: World) -> None:
    world.say(
        "Their parents, gathered at the sheriff's office for monthly bingo night, "
        "rushed home to find their darlings looking most peculiar."
    )

def lesson_learned(world: World, doctor_id: str = "Dr_Hayes") -> None:
    doc = world.get(doctor_id)
    world.say(
        f'{doc.id.title()} sat down on the porch swing, calm as creosote after rain. '
        f'"Medicine is not a bonbon," they began. "Cortisone is a powerful tool '
        f'that must only be used when a doctor says — with a pen — and exactly '
        f'how they say with that pen. DO NOT grab it from the dashboard like '
        f'a candy wrapper!" The group gulped, their knees knocking like castanets.'
    )
    doc.memes["carefulness"] += 1.0

def proper_rub(world: World, hero_id: str = "Rigby", cream_id: str = "itch_spray") -> None:
    hero = world.get(hero_id)
    cream = world.get(cream_id)
    world.say(
        f"{hero.id} pulled the {cream.label} from {hero.pronoun('possessive')} pocket "
        f"(safe, small, doctor-lined) and read the tiny print aloud. With gentle "
        f"dabs on each {', '.join(cream.treats) if cream.treats else 'own knees'}, "
        f"the original glow faded like ink in river sand."
    )
    for cond in cream.treats:
        for e in world.characters():
            e.meters[cond] = 0.0
    for eff in list(world.transformations):
        world.get(hero.id).meters[eff] = max(0.0, world.get(hero.id).meters.get(eff,0)-0.8)
    hero.memes["relief"] = 1.2
    world.say(
        f"{hero.id} hugged each friend tight and promised, "
        f'"I\'ll keep the rule: never touch what’s not mine *and* '
        f'never use without asking first!"'
    )

def tall_tale_open() -> str:
    return ("Once upon a time, in a dusty Nevada town best known for its jackrabbits "
            "and laughing adults under the big sky,")

### Parameters & Registry ###
@dataclass
class StoryParams:
    setting: str
    medicine: str
    hero: str
    friends: list[str]
    doctor: str
    seed: Optional[int] = None

HERO_NAMES = ["Rigby", "Javi", "Alonzo", "Mai", "Noemi", "Tomas"]
KID_NAMES   = ["Alonzo", "Mai", "Javi", "Noemi", "Luz", "Milo"]
DOCTOR_NAME = "Dr_Hayes"

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story of cortisone misuse among friends near Reno."
    )
    ap.add_argument("--setting", choices=list(SETTINGS.keys()), help="Nevada landscape")
    ap.add_argument("--medicine", choices=list(ITEMS.keys()), help="cream item")
    ap.add_argument("--hero", choices=HERO_NAMES, help="main child")
    ap.add_argument("--friends", nargs="+", choices=KID_NAMES,
                   help="friend group to involve")
    ap.add_argument("--doctor", choices=[DOCTOR_NAME],
                   help="medical authority to teach the lesson")
    ap.add_argument("-n", type=int, default=1,
                   help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true",
                   help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="emit the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                   help="list valid (setting,medicine,group) combos via clingo")
    ap.add_argument("--verify", action="store_true",
                   help="check ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                   help="emit the inline ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    # Curated combos: each setting supports corticool_cream and kid-safe itch_spray;
    # hero must be the one who discovers cream; friends must be plausible playmates.
    curated = [
        StoryParams(setting="ranch", medicine="corticool_cream",
                   hero="Rigby", friends=["Alonzo","Mai"], doctor=DOCTOR_NAME),
        StoryParams(setting="town_square", medicine="corticool_cream",
                   hero="Javi", friends=["Mai","Luz"], doctor=DOCTOR_NAME),
        StoryParams(setting="porch", medicine="itch_spray",
                   hero="Alonzo", friends=["Rigby","Tomas"], doctor=DOCTOR_NAME)
    ]
    if args.all:
        return curated[rng.randint(0, len(curated)-1)]

    if (args.setting and args.medicine and
        args.setting in SETTINGS and
        any(g.startswith("corticool") for g in [args.medicine])):
        if not args.hero:
            args.hero = rng.choice([k for k,v in CHARACTERS.items()
                                 if v["type"] in ["boy","girl"]])
        if not args.friends:
            kids = set(KID_NAMES) - {args.hero}
            args.friends = rng.sample(list(kids), rng.randint(2,3))
        return StoryParams(
            setting=args.setting, medicine=args.medicine,
            hero=args.hero, friends=args.friends, doctor=args.doctor or DOCTOR_NAME
        )
    # Default random draw from curated
    return curated[rng.randint(0, len(curated)-1)]

def generate(params: StoryParams) -> StorySample:
    # Initialize world
    setting_def = Setting(**SETTINGS[params.setting])
    world = World(setting_def)
    world.facts.update(params=params, transformations={})

    # Add core entities
    world.add(Entity(id="Uncle_Jack", kind="character", type="adult",
                 label="Uncle_Jack", phrase=ITEMS["corticool_cream"]["phrase"],
                 traits=CHARACTERS["Uncle_Jack"]["traits"]))
    world.add(Entity(id=params.doctor, kind="character", type="doctor",
                 label="Dr. Hayes", phrase="the pediatrician’s gold stethoscope"))

    # Medicine appears only on dashboard when adult is present
    if "corticool" in params.medicine:
        med_def = ITEMS[params.medicine].copy()
        world.add(Entity(id=params.medicine, kind="item",
                     label=med_def["label"], phrase=med_def["phrase"],
                     treats=med_def["treatable"], side_effects=med_def["side_effects"]))

    # Hero and friends
    hero_def = CHARACTERS[params.hero]
    hero = world.add(Entity(id=params.hero, kind="character", type=hero_def["type"],
                         label=params.hero, traits=hero_def["traits"]))
    for fid in params.friends:
        friend_def = CHARACTERS[fid]
        world.add(Entity(id=fid, kind="character", type=friend_def["type"],
                     label=fid, traits=friend_def["traits"]))

    # Act 1: discovery
    apply_rules(world)  # baseline initialization
    world.para()
    world.say(tall_tale_open())
    world.say(f"lived a freckled {hero_def['type']} named {params.hero}.")
    world.para()

    welcome_uncle(world)
    bandage_reveal(world)
    hero_itch_discovery(world, params.hero)
    cream_intro(world, params.medicine)

    # Apply initial medicine attempt (narrate side effects if they arise)
    medication = world.get(params.medicine)
    hero.meters["applied_corticool_cream"] = 1.1
    apply_rules(world)

    # Act 2: spread mischief among friends
    world.para()
    share_cream(world, params.hero, params.friends)
    apply_rules(world)
    transformations_begin(world, params.friends)
    parents_arrive(world)

    # Doctor’s arrival and lesson
    world.para()
    world.add(Entity(id=params.doctor+"_arrives", kind="npc", phrase="silent sedan"))
    lesson_learned(world, params.doctor)

    # Act 3: proper revival session
    world.para()
    proper_rub(world, params.hero, "itch_spray")

    # Record facts
    for char in world.characters():
        for eff in char.meters.keys() & TRANSFORMATIONS.keys():
            if char.meters[eff] >= THRESHOLD:
                world.facts.setdefault("transformed", []).append(char.id)
    world.facts.update(
        hero=hero.id,
        friends=params.friends,
        doctor=params.doctor,
        medicine=params.medicine,
        original_shapes_restored= ("transformed" not in world.facts or not world.facts["transformed"])
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world
    )

def generation_prompts(world: World) -> list[str]:
    return [
        'Write an exaggerated, tall-tale style story for 4–7-year-olds '
        'about misusing a grown-up’s cream, then finding a safer plan.',
        'Tell a Nevada desert story where kids play with "magic" cortisone '
        'cream and suffer cartoonish side effects before learning a cautionary rule.',
        'Compose a 3–5 short-paragraph story that uses "jackrabbit" and '
        'ends with everyone cheering after original shapes return.'
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    qa: list[QAItem] = [
        QAItem(
            question="Who discovered the cream and shared it with friends near Reno?",
            answer=f'"{f["hero"]}" is the freckled {CHARACTERS[f["hero"]]["type"]} '
                   f'who first noticed Uncle Jack’s gleaming tin of corticool cream.'
        ),
        QAItem(
            question="What happened when each friend used the cream?",
            answer=(
                "Rigby’s arms sprouted fern-green glowing splotches. "
                "Mai’s shoulders turned shiny like polished silver threads. "
                "Javi’s tongue turned neon coral and rhymed nonstop."
            ) if "transformed" in f else
            "Nothing dramatic—everyone kept their original shapes."
        ),
        QAItem(
            question="How did Dr. Hayes help the kids after their odd changes?",
            answer=(
                f'Dr. {f["doctor"]} calmly explained that cortisone must '
                f'only be used "when a doctor says — with a pen — '
                f'and exactly how they say with that pen."'
            )
        )
    ]
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What should you do before using someone’s medicine?",
            answer="Ask the adult who owns it and read the label carefully."
        ),
        QAItem(
            question="How can medicine sometimes help and sometimes hurt?",
            answer="It helps the spot it’s meant for, but if used wrong it "
                  "can cause new problems; that’s why doctors give careful rules."
        )
    ]

# ASP Twin – declarative gate for cautionary tale safety rules
ASP_RULES = r"""
% A medicine is safe only when used under adult supervision
is_safe(S, H, M) :- setting(S), hero(H), medicine(M),
            adult_supervise(M, A), owner(M, A).

% A transformation blooms when a side-effect key exceeds threshold
has_transform(Id, Eff) :- character(Id), transformation(Eff),
                         meters(Id, Eff, Val), Val >= 0.8.

% A valid story requires proper supervision and may include transformations
valid_story(S,H,M,F) :- setting(S), hero(H), medicine(M), friend_of(F,H),
                          is_safe(S,H,M), has_transform(_,_).
"""

def asp_facts() -> str:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import asp
    lines: list[str] = []
    # settings
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("weather", sid, s["weather"]))
        lines.append(asp.fact("sky", sid, s["sky"]))
    # characters
    for cid, c in CHARACTERS.items():
        lines.append(asp.fact("character", cid))
        lines.append(asp.fact("type", cid, c["type"]))
        if c["type"] in ["boy","girl"]:
            lines.append(asp.fact("friend_of", cid, "Rigby"))
    # items
    for mid, it in ITEMS.items():
        lines.append(asp.fact("medicine", mid))
        for t in it["treatable"]:
            lines.append(asp.fact("treatable", mid, t))
        for e in it["side_effects"]:
            lines.append(asp.fact("side_effect", mid, e))
        if it.get("adult_required"):
            lines.append(asp.fact("adult_required", mid))
    # transformations
    for eff, tx in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", eff))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set([("ranch","corticool_cream", "Rigby", "Alonzo")])
    if clingo_set == python_set:
        print(f"OK: clingo gate and Python agree ({len(clingo_set)} combos).")
        return 0
    print("ASP mismatch!")
    return 1

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        lines = ["---- model state ----"]
        for eid, e in sample.world.entities.items():
            meters = {k:v for k,v in e.meters.items() if v}
            if meters:
                lines.append(f"{eid:10} meters={meters}")
        print("\n".join(lines))
    if qa and (sample.story_qa or sample.world_qa):
        print("\nStory Q&A:")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}\nA: {qa.answer}\n")
        print("World knowledge Q&A:")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}\nA: {qa.answer}\n")

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        import sys
        sys.exit(asp_verify())
    base_seed = args.seed or random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(resolve_params(args, rng)) for _ in range(3)]
    else:
        seen = set()
        for _ in range(args.n * 50 or 50):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, rng)
            params.seed = (base_seed + len(samples)) or base_seed
            sample = generate(params)
            skey = tuple([a.lower() for a in sample.story.split()[:20]])
            if skey in seen:
                continue
            seen.add(skey)
            samples.append(sample)
            if len(samples) >= args.n:
                break

    if args.json:
        import json
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2,
                          ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### Tall Tale {i+1}: {s.params.hero} and friends"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
