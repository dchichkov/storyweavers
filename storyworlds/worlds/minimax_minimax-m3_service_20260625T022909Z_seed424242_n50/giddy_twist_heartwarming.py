#!/usr/bin/env python3
"""
storyworlds/worlds/giddy_twist_heartwarming.py
==============================================

A standalone *story world* sketch for "The Giddy Twist" tale and close,
constraint-checked variations of it.

Initial story (used to build a world model):
---
Once upon a time, there was a little giddy boy named Theo. He loved helping
in the kitchen and tasting every sweet thing he could reach. One day, his
grandma baked a tall lemon cake with bright frosting on top.

Theo was so giddy about the cake that he tried to peek into the oven, but
his grandma gently pulled him back. "The cake has to rest before we cut it,"
she said with a smile. Theo pouted, then hugged her, and together they set
the table.

When the cake finally came out, Theo carried it proudly to the porch. On
the way, his little sister Mia raced past on her new scooter and bumped
the plate. The cake slid sideways, the frosting smeared, and Theo gasped.
His grandma knelt down and showed him the smear shaped like a soft little
heart. They laughed, cut the cake, and shared it with Mia, and the porch
filled with warm light.

Causal state updates:
---
    do baking              -> baker.<flour_mess> += 1
    helper sneaks a taste  -> helper.tasted += 1        (joy / curiosity)
    plate gets bumped      -> cake.<topple_mess> += 1   (frosting smear)
    smear shaped like heart-> cake.celebrate += 1       (heartwarming turn)

Scripted social/emotional beats:
---
    helper pouts at wait   -> helper.<meme:patience> - 1, <meme:giddiness> += 1
    grandma reframes smear -> helper.<meme:giddiness> += 1, baker.<meme:love> += 1
    sibling bumps the plate-> sibling.<meme:speed> += 1, cake.<topple_mess> += 1
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
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# A "mess" is anything that soils the thing being carried.
MESS_KINDS = {"floury", "frosting", "jammy", "chocolaty", "sugary"}

# Body / object regions that can get messed by baking spills.
REGIONS = {"hands", "apron", "plate", "cake_top", "frosting"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, grandma, mom, dad, cake, plate ...
    label: str = ""                # short reference, e.g. "cake", "plate"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""               # hands | apron | plate | cake_top | frosting
    sweet: bool = False            # a baked sweet whose top can be smudged
    guards: set[str] = field(default_factory=set)   # mess kinds this item neutralizes
    plural: bool = False

    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "grandma", "mom", "mother", "woman", "sister"}
        male = {"boy", "grandpa", "dad", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad",
                "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the kitchen"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Bake:
    """The thing being baked (and the verb forms around it)."""
    id: str
    noun: str            # "cake", "cookies", "pie"
    article: str         # "a" or "an" for "a tall lemon cake"
    size: str            # "tall", "round", "little"
    flavor: str          # "lemon", "berry", "chocolate"
    top: str             # "bright frosting", "dusty sugar", "ruby jam"
    baked_verb: str      # "baked", "made", "whipped up"
    carried_verb: str    # "carried", "brought", "balanced"
    sweet_kind: str      # mess kind on top: "frosting", "sugary", "jammy"
    tags: set[str] = field(default_factory=set)


@dataclass
class Bump:
    """What causes the twist -- an external jolt to the carried plate."""
    id: str
    mover: str           # who/what moves through: "raced past on her new scooter"
    noise: str           # sound it makes: "skittered across the porch"
    smear_shape: str     # what the smear looks like: "a soft little heart"
    sibling_type: str    # "sister" or "brother"
    tags: set[str] = field(default_factory=set)


@dataclass
class Apron:
    """Protective gear that covers the helper's torso."""
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str            # body of the offer: "tie on your apron first"
    tail: str            # closing clause: "tied on the apron"
    plural: bool = False


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def carried_by(self, eid: str) -> Optional[Entity]:
        owner = self.entities[eid].owner
        return self.entities.get(owner) if owner else None

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_smear(world: World) -> list[str]:
    """Cake top gets bumped -> smear on the frosting."""
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["topple"] < THRESHOLD or not item.sweet:
            continue
        sig = ("smear", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["smear"] += 1
        out.append(f"{item.label_word.capitalize() if item.label_word else item.label} slid sideways.")
    return out


def _r_celebrate(world: World) -> list[str]:
    """A smeared cake is reframed -> heartwarming turn."""
    for item in world.entities.values():
        if not item.sweet or item.meters["smear"] < THRESHOLD:
            continue
        if item.meters["celebrate"] >= THRESHOLD:
            continue
        sig = ("celebrate", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["celebrate"] += 1
        return ["__celebrate__"]
    return []


def _r_workload(world: World) -> list[str]:
    """A mess on the cake top -> baker has more cleanup."""
    out: list[str] = []
    for item in world.entities.values():
        if not item.sweet or item.meters["smear"] < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("workload", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] += 1
        out.append(f"That would mean a little more cleanup for {caretaker.label_word}.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="smear", tag="physical", apply=_r_smear),
    Rule(name="celebrate", tag="social", apply=_r_celebrate),
    Rule(name="workload", tag="physical", apply=_r_workload),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__celebrate__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def smear_applies(bake: Bake, bump: Bump) -> bool:
    """The bump is a real risk for this bake only if the bake has a top
    (frosting, sugar, or jam) that the mover can smear."""
    return bump.id in {"scooter", "dog_chase", "kite_pull"} and bake.sweet_kind in {"frosting", "sugary", "jammy"}


def select_apron(bake: Bake) -> Optional[Apron]:
    """Apron must guard the bake's sweet_kind AND cover hands or apron region."""
    for apron in APRONS:
        if bake.sweet_kind in apron.guards and ({"hands", "apron"} & apron.covers):
            return apron
    return None


def predict_smear(world: World, helper: Entity, bake_id: str, bump_id: str) -> dict:
    sim = world.copy()
    _do_bump(sim, sim.get(bake_id), BUMP[bump_id], narrate=False)
    cake = sim.entities.get(bake_id)
    return {
        "smeared": bool(cake and cake.meters["smear"] >= THRESHOLD),
        "celebrate": bool(cake and cake.meters["celebrate"] >= THRESHOLD),
    }


# ---------------------------------------------------------------------------
# Verbs.
# ---------------------------------------------------------------------------
def _do_bake(world: World, baker: Entity, bake: Bake, narrate: bool = True) -> None:
    if bake.id not in world.setting.affords:
        return
    baker.meters["floury"] += 1
    baker.memes["joy"] += 1
    propagate(world, narrate=narrate)


def _do_bump(world: World, cake: Entity, bump: Bump, narrate: bool = True) -> None:
    cake.meters["topple"] += 1
    cake.meters[bake_sweet_kind(cake.id)] = cake.meters.get(bake_sweet_kind(cake.id), 0)
    propagate(world, narrate=narrate)


def bake_sweet_kind(cake_id: str) -> str:
    """Look up the bake entry to learn its sweet_kind."""
    for bake in BAKES.values():
        if bake.id + "_bake" == cake_id or bake.id == cake_id:
            return bake.sweet_kind
    return "frosting"


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who noticed every sweet thing nearby.")


def loves_baking(world: World, hero: Entity, bake: Bake) -> None:
    hero.memes["love_bake"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved helping in the kitchen and "
        f"tasting every {bake.flavor} {bake.noun} {hero.pronoun()} could reach."
    )


def bakes(world: World, baker: Entity, hero: Entity, bake: Bake, bake_entity: Entity) -> None:
    baker.memes["care"] += 1
    world.say(
        f"One day, {hero.id}'s {baker.label_word} {bake.baked_verb} "
        f"{bake.article} {bake.size} {bake.flavor} {bake.noun} with {bake.top} on top."
    )


def sneak_taste(world: World, hero: Entity) -> None:
    hero.meters["tasted"] += 1
    hero.memes["giddiness"] += 1
    world.say(
        f"Theo-like and giddy, {hero.id} tried to peek a finger into the bowl."
    )


def wait_warning(world: World, baker: Entity, hero: Entity, bake: Bake) -> bool:
    """The baker foresees the smear (via forward simulation) and asks for patience."""
    pred = predict_smear(world, hero, bake.id + "_bake", "scooter")
    if not pred["smeared"]:
        return False
    world.facts["predicted_smear"] = True
    world.say(
        f'"{bake.noun.capitalize()} has to rest before we cut it," '
        f'{hero.pronoun("possessive")} {baker.label_word} said with a warm smile.'
    )
    return True


def pout(world: World, hero: Entity, bake: Bake) -> None:
    hero.memes["patience"] = max(0.0, hero.memes.get("patience", 0.0) - 1)
    hero.memes["giddiness"] += 1
    world.say(
        f"{hero.id} pouted and crossed {hero.pronoun('possessive')} arms, "
        f"so {hero.pronoun('possessive')} {next((e for e in world.entities.values() if e.kind == 'character' and e.id != hero.id), Entity(id='Baker')).label_word} "
        f"hugged {hero.pronoun('object')} and they set the table together."
    )


def carry_cake(world: World, hero: Entity, bake: Bake, cake: Entity, baker: Entity) -> None:
    world.say(
        f"When the {bake.noun} finally came out, {hero.id} {bake.carried_verb} "
        f"it proudly toward the porch."
    )


def twist(world: World, hero: Entity, sibling: Entity, bump: Bump, bake: Bake, cake: Entity) -> None:
    sibling.memes["speed"] += 1
    cake.meters["topple"] += 1
    world.say(
        f"On the way, {sibling.pronoun('possessive')} little {sibling.type} "
        f"{bump.mover}, and the plate {bump.noise}."
    )
    propagate(world, narrate=False)


def reveal(world: World, baker: Entity, hero: Entity, bake: Bake, bump: Bump, cake: Entity) -> bool:
    """The heartwarming reframe: the smear looks like something lovely."""
    cake.meters["celebrate"] = cake.meters.get("celebrate", 0.0)
    if cake.meters["smear"] < THRESHOLD:
        return False
    world.say(
        f"{hero.id} gasped, but {hero.pronoun('possessive')} {baker.label_word} "
        f"knelt down and showed {hero.pronoun('object')} that the smear on top "
        f"looked just like {bump.smear_shape}."
    )
    hero.memes["giddiness"] += 1
    baker.memes["love"] += 1
    hero.memes["joy"] += 1
    return True


def apron_offer(world: World, baker: Entity, hero: Entity, bake: Bake) -> Optional[Apron]:
    apron = select_apron(bake)
    if apron is None:
        return None
    apr_ent = world.add(Entity(
        id=apron.id, type="gear", label=apron.label,
        owner=hero.id, caretaker=baker.id,
        covers=set(apron.covers), guards=set(apron.guards), plural=apron.plural,
    ))
    world.say(
        f'"{baker.label_word.capitalize()}, let\'s {apron.prep} before we taste '
        f'the {bake.noun} together," {baker.label_word} said.'
    )
    return apron


def share(world: World, hero: Entity, baker: Entity, sibling: Entity, bake: Bake) -> None:
    hero.memes["joy"] += 1
    baker.memes["love"] += 1
    sibling.memes["giddiness"] += 1
    world.say(
        f"They laughed, cut the {bake.noun}, and shared it with {sibling.id}. "
        f"The porch filled with warm light, and the {bake.size} {bake.flavor} "
        f"{bake.noun} tasted even sweeter for the waiting."
    )


# ---------------------------------------------------------------------------
# The screenplay: a small three-act shape driven by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, bake: Bake, bump: Bump,
         hero_name: str = "Theo", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None,
         baker_type: str = "grandma",
         sibling_name: str = "Mia", sibling_type: str = "sister") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "giddy"] + (hero_traits or ["curious", "stubborn"]),
    ))
    baker = world.add(Entity(id="Baker", kind="character", type=baker_type, label="the baker"))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_type, label="the sibling"))

    cake = world.add(Entity(
        id=bake.id + "_bake", type=bake.noun, label=bake.noun,
        phrase=f"{bake.article} {bake.size} {bake.flavor} {bake.noun} with {bake.top} on top",
        owner=hero.id, caretaker=baker.id,
        region="cake_top", sweet=True,
    ))
    plate = world.add(Entity(
        id="plate", type="plate", label="plate",
        owner=hero.id, caretaker=baker.id, region="plate",
    ))

    # Act 1 -- setup
    introduce(world, hero)
    loves_baking(world, hero, bake)
    bakes(world, baker, hero, bake, cake)
    _do_bake(world, baker, bake)

    # Act 2 -- conflict and wait
    world.para()
    sneak_taste(world, hero)
    wait_warning(world, baker, hero, bake)
    pout(world, hero, bake)

    # Act 3 -- the twist and the heartwarming reframe
    world.para()
    carry_cake(world, hero, bake, cake, baker)
    twist(world, hero, sibling, bump, bake, cake)
    if reveal(world, baker, hero, bake, bump, cake):
        share(world, hero, baker, sibling, bake)

    world.facts.update(
        hero=hero, baker=baker, sibling=sibling, bake=bake, bump=bump,
        cake=cake, setting=setting,
        smeared=cake.meters["smear"] >= THRESHOLD,
        celebrated=cake.meters["celebrate"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"cake", "cookies", "pie"}),
    "porch": Setting(place="the porch", indoor=False, affords={"cake", "pie"}),
    "garden": Setting(place="the garden", indoor=False, affords={"cookies", "pie"}),
}

BAKES = {
    "cake": Bake(
        id="cake",
        noun="cake",
        article="a",
        size="tall",
        flavor="lemon",
        top="bright frosting",
        baked_verb="baked",
        carried_verb="carried",
        sweet_kind="frosting",
        tags={"frosting", "cake"},
    ),
    "cookies": Bake(
        id="cookies",
        noun="cookies",
        article="some",
        size="little",
        flavor="berry",
        top="dusty sugar",
        baked_verb="made",
        carried_verb="balanced",
        sweet_kind="sugary",
        tags={"sugar", "cookies"},
    ),
    "pie": Bake(
        id="pie",
        noun="pie",
        article="a",
        size="round",
        flavor="berry",
        top="ruby jam",
        baked_verb="whipped up",
        carried_verb="brought",
        sweet_kind="jammy",
        tags={"jam", "pie"},
    ),
}

BUMPS = {
    "scooter": Bump(
        id="scooter",
        mover="raced past on her new scooter",
        noise="skittered across the porch",
        smear_shape="a soft little heart",
        sibling_type="sister",
        tags={"scooter"},
    ),
    "dog_chase": Bump(
        id="dog_chase",
        mover="chased the puppy through the yard",
        noise="jiggled under the helper's hands",
        smear_shape="a little smiley face",
        sibling_type="brother",
        tags={"dog"},
    ),
    "kite_pull": Bump(
        id="kite_pull",
        mover="ran after a bright kite",
        noise="tilted in the helper's arms",
        smear_shape="a soft little star",
        sibling_type="sister",
        tags={"kite"},
    ),
}

# Order matters: more specific gear first.
APRONS = [
    Apron(
        id="pastry_apron",
        label="a tidy pastry apron",
        covers={"hands", "apron"},
        guards={"frosting", "sugary"},
        prep="tie on your pastry apron first",
        tail="tied on the pastry apron",
    ),
    Apron(
        id="berry_apron",
        label="a berry-print apron",
        covers={"hands", "apron"},
        guards={"jammy", "frosting"},
        prep="put on the berry apron first",
        tail="tied on the berry apron",
    ),
    Apron(
        id="play_apron",
        label="an old play apron",
        covers={"hands", "apron"},
        guards={"frosting", "sugary", "jammy", "chocolaty", "floury"},
        prep="go get the old play apron first",
        tail="fetched the old play apron",
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Theo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["playful", "curious", "stubborn", "cheerful", "spirited", "lively"]
BAKERS = ["grandma", "grandpa", "mom", "dad"]
SIBLING_TYPES = ["sister", "brother"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, bake, bump) triples that pass the reasonableness constraint."""
    combos = []
    for place, setting in SETTINGS.items():
        for bake_id in setting.affords:
            bake = BAKES[bake_id]
            for bump_id, bump in BUMPS.items():
                if smear_applies(bake, bump) and select_apron(bake):
                    combos.append((place, bake_id, bump_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    bake: str
    bump: str
    name: str
    gender: str
    baker: str
    sibling_name: str
    sibling_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "frosting": [("What is frosting?",
                  "Frosting is a soft, sweet topping that bakers spread on cakes "
                  "to make them look pretty and taste extra sweet.")],
    "sugar": [("Why does sugar make things taste sweet?",
               "Sugar tastes sweet because the tiny crystals dissolve on your "
               "tongue and send a sweet signal to your brain.")],
    "jam": [("What is jam?",
              "Jam is fruit that has been cooked with sugar until it becomes "
              "thick and spreadable, like a glossy topping.")],
    "scooter": [("What is a scooter?",
                 "A scooter is a small wheeled ride that you push with one foot "
                 "and steer with the handlebars.")],
    "dog": [("Why do dogs like to chase things?",
             "Dogs like to chase things because they love to run and play, and "
             "a fast-moving toy looks like a fun game to them.")],
    "kite": [("What makes a kite fly?",
              "A kite flies when the wind blows against its flat surface and "
              "lifts it up into the sky while you hold the string.")],
    "patience": [("What does it mean to be patient?",
                  "Being patient means waiting calmly for something good, even "
                  "when it feels slow.")],
}
KNOWLEDGE_ORDER = ["frosting", "sugar", "jam", "scooter", "dog", "kite", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, baker, bake, bump = f["hero"], f["baker"], f["bake"], f["bump"]
    kw = bake.flavor or bake.noun
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "giddy helper, '
        f'a wait, a sweet twist" that includes the word "{kw}".',
        f"Tell a gentle story where a {hero.type} named {hero.id} is giddy to "
        f"help with a {bake.flavor} {bake.noun}, has to wait, and ends with a "
        f"sweet surprise shaped like {bump.smear_shape}.",
        f'Write a simple story that uses the noun "{bake.noun}" and ends with '
        f"a porch filled with warm light after a small accident.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, baker, sibling, bake, bump = f["hero"], f["baker"], f["sibling"], f["bake"], f["bump"]
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    bw = baker.label_word
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    sm = bake.size
    fl = bake.flavor
    top = bake.top
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} helps in {place} with a "
                f"{sm} {fl} {bake.noun}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {bw}. They bake a {sm} {fl} {bake.noun} together, with "
                f"{top} on top."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do in {place} before the "
                f"{fl} {bake.noun} came out of the oven?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved helping in the kitchen "
                f"and tasting every {fl} {bake.noun} {sub} could reach. That "
                f"wish made the waiting tricky."
            ),
        ),
        QAItem(
            question=(
                f"What new {bake.noun} did {hero.id}'s {bw} make for the "
                f"{trait} {hero.type} before the porch surprise?"
            ),
            answer=(
                f"{pos.capitalize()} {bw} {bake.baked_verb} {bake.article} {sm} "
                f"{fl} {bake.noun} with {top} on top. {hero.id} loved the look "
                f"of it and wanted to taste it right away."
            ),
        ),
    ]
    if f.get("smeared"):
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {bw} ask for patience about the {fl} "
                f"{bake.noun} before the {bump.id} surprise at {place}?"
            ),
            answer=(
                f"{pos.capitalize()} {bw} knew the {bake.noun} needed to rest "
                f"before they cut it, so the top would stay pretty. The wait "
                f"let the {fl} flavor settle in."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did the {bump.id} twist change the {fl} {bake.noun} that "
                f"{trait} {hero.id} was carrying on the porch?"
            ),
            answer=(
                f"As {hero.id} carried the {bake.noun} toward the porch, "
                f"{sibling.id} {bump.mover} and the plate {bump.noise}. The "
                f"{bake.noun} slid sideways and the top smudged."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {hero.id}'s {bw} turn the smeared {fl} {bake.noun} "
                f"into a heartwarming moment at {place}?"
            ),
            answer=(
                f"{bw.capitalize()} knelt down and showed {hero.id} that the "
                f"smear on top looked just like {bump.smear_shape}. That soft "
                f"shape made the accident feel like a sweet gift."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after the {fl} {bake.noun} "
                f"surprise on the porch with {sibling.id}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} felt giddy and warm after the "
                f"{bump.smear_shape} surprise. They laughed, cut the {bake.noun}, "
                f"and shared it with {sibling.id} in the porch light."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["bake"].tags) | set(f["bump"].tags) | {"patience"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.sweet:
            bits.append(f"sweet_kind={e.region}")
        lines.append(f"  {e.id:14} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen",
        bake="cake",
        bump="scooter",
        name="Theo",
        gender="boy",
        baker="grandma",
        sibling_name="Mia",
        sibling_type="sister",
        trait="giddy",
    ),
    StoryParams(
        place="garden",
        bake="cookies",
        bump="dog_chase",
        name="Lily",
        gender="girl",
        baker="grandpa",
        sibling_name="Ben",
        sibling_type="brother",
        trait="curious",
    ),
    StoryParams(
        place="porch",
        bake="pie",
        bump="kite_pull",
        name="Zoe",
        gender="girl",
        baker="mom",
        sibling_name="Ava",
        sibling_type="sister",
        trait="playful",
    ),
    StoryParams(
        place="kitchen",
        bake="cake",
        bump="dog_chase",
        name="Finn",
        gender="boy",
        baker="dad",
        sibling_name="Max",
        sibling_type="brother",
        trait="lively",
    ),
    StoryParams(
        place="garden",
        bake="pie",
        bump="scooter",
        name="Nora",
        gender="girl",
        baker="grandma",
        sibling_name="Eli",
        sibling_type="brother",
        trait="cheerful",
    ),
]


def explain_rejection(bake: Bake, bump: Bump) -> str:
    if not smear_applies(bake, bump):
        return (f"(No story: {bump.mover} doesn't actually smear a "
                f"{bake.noun} with {bake.top}. Try a bake with a soft top "
                f"like frosting, sugar, or jam.)")
    if not select_apron(bake):
        return (f"(No story: no apron in the catalog guards {bake.top} on the "
                f"helper's hands. The compromise must actually cover the "
                f"at-risk top, so this argument is rejected.)")
    return "(No story: this combination doesn't satisfy the story constraints.)"


def explain_sibling(bump: Bump, sibling_type: str) -> str:
    return (f"(No story: bump '{bump.id}' expects a {bump.sibling_type} sibling, "
            f"not a {sibling_type}. Try --sibling-type {bump.sibling_type}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A smear is plausible when the bake has a soft top AND the bump can jostle it.
smear_applies(B, M) :- bake_top(B, T), bump_kind(M, T).

% Apron is a compatible fix only when it guards the bake's top AND covers hands.
protects(A, B, M) :- apron(A), smear_applies(B, M),
                     apron_guards(A, T), bake_top(B, T),
                     apron_covers(A, "hands").
has_fix(B, M) :- protects(_, B, M).

valid(Place, B, M) :- affords(Place, B), smear_applies(B, M), has_fix(B, M).
valid_story(Place, B, M, S) :- valid(Place, B, M), sibling_for(M, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for b in sorted(s.affords):
            lines.append(asp.fact("affords", pid, b))
    for bid, b in BAKES.items():
        lines.append(asp.fact("bake", bid))
        lines.append(asp.fact("bake_top", bid, b.sweet_kind))
        for tag in sorted(b.tags):
            lines.append(asp.fact("bake_tag", bid, tag))
    for mid, m in BUMPS.items():
        lines.append(asp.fact("bump", mid))
        lines.append(asp.fact("bump_kind", mid, "frosting"))
        lines.append(asp.fact("bump_kind", mid, "sugary"))
        lines.append(asp.fact("bump_kind", mid, "jammy"))
        lines.append(asp.fact("sibling_for", mid, m.sibling_type))
        for tag in sorted(m.tags):
            lines.append(asp.fact("bump_tag", mid, tag))
    for a in APRONS:
        lines.append(asp.fact("apron", a.id))
        for t in sorted(a.guards):
            lines.append(asp.fact("apron_guards", a.id, t))
        for r in sorted(a.covers):
            lines.append(asp.fact("apron_covers", a.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a giddy helper, a wait, a sweet twist. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--bake", choices=BAKES)
    ap.add_argument("--bump", choices=BUMPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--baker", choices=BAKERS)
    ap.add_argument("--name")
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-type", choices=SIBLING_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bake and args.bump:
        bake, bump = BAKES[args.bake], BUMPS[args.bump]
        if not (smear_applies(bake, bump) and select_apron(bake)):
            raise StoryError(explain_rejection(bake, bump))
    if args.bump and args.sibling_type and args.sibling_type != BUMPS[args.bump].sibling_type:
        raise StoryError(explain_sibling(BUMPS[args.bump], args.sibling_type))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.bake is None or c[1] == args.bake)
              and (args.bump is None or c[2] == args.bump)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, bake_id, bump_id = rng.choice(sorted(combos))
    bake, bump = BAKES[bake_id], BUMPS[bump_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    baker = args.baker or rng.choice(BAKERS)
    sibling_name = args.sibling_name or rng.choice(
        [n for n in (GIRL_NAMES if bump.sibling_type == "sister" else BOY_NAMES) if n != name]
        or GIRL_NAMES + BOY_NAMES
    )
    sibling_type = args.sibling_type or bump.sibling_type
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, bake=bake_id, bump=bump_id,
        name=name, gender=gender, baker=baker,
        sibling_name=sibling_name, sibling_type=sibling_type, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], BAKES[params.bake], BUMPS[params.bump],
                 params.name, params.gender, [params.trait, "stubborn"],
                 params.baker, params.sibling_name, params.sibling_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, bake, bump) combos "
              f"({len(stories)} with sibling):\n")
        for place, bake, bump in triples:
            siblings = sorted(s for (pl, bk, bp, s) in stories
                               if (pl, bk, bp) == (place, bake, bump))
            print(f"  {place:9} {bake:8} {bump:11}  [{', '.join(siblings)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.bake} at {p.place} (bump: {p.bump})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
