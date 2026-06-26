#!/usr/bin/env python3
"""
storyworlds/worlds/morphodite_sharing_magic_space_adventure.py
==============================================================

A standalone *story world* sketch for the "Morphodite Sharing Magic" tale
and close, *constraint-checked* variations of it.

Initial story (used to build the world model):
---
Once upon a time there was a little space explorer named Pip. Pip lived on
a small silver moon and loved watching the sky from a soft crater. One day,
a kind grown-up baked a moonberry pie and saved a single glowing moonberry
for Pip in a tiny pouch. Pip loved that berry; it tasted like starlight
and smelled like a quiet wish.

One quiet evening, a morphodite drifted down from the soft sky. A morphodite
is a fluffy creature that can change its shape whenever it wants. Today it
wore the shape of a small cloud, then a kitten, then a tiny moon, and at
last it sat down near Pip and looked very shy.

"Where is your home?" Pip asked.
"I have no home yet," the morphodite said. "I am still looking for the
right place to land."
Pip looked at the moonberry, the most precious thing Pip owned. The
morphodite looked so very small and alone.

"Would you like half?" Pip asked, holding out the moonberry.
The morphodite had never been offered anything before. Its eyes grew round
as it took a small taste, and right then something magical happened. The
sky glowed, the morphodite slowly changed into the shape of a small kind
friend with paws like cotton, and it sang a song that smelled like rain.
A tiny star drifted down from the sky and landed softly in front of Pip.

Pip and the morphodite became the very best of friends, and from that day
on they shared every small adventure on the little silver moon.

Causal state updates:
---
    hero offers treasure   -> morph.memes["joy"] += 1
                              morph.memes["shyness"] -> 0
                              treasure.meters["shared"] += 1
    morph joyful + shared  -> morph.meters["magic_flow"] += 1
    magic_flow fixpoint    -> morph.meters["true_shape"] += 1
    true_shape fixpoint    -> hero.meters["star"] += 1
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

# Make the shared result containers importable when this script is run directly
# (``python storyworlds/worlds/morphodite_sharing_magic_space_adventure.py``):
# add the package dir (storyworlds/) to the path so ``results`` resolves.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, morphodite, berry, song, ...
    label: str = ""                # short reference, e.g. "the morphodite"
    phrase: str = ""               # full noun phrase, e.g. "a glowing moonberry"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    keeper: Optional[str] = None   # who keeps the magical promise
    precious: bool = False         # treasured enough to warrant sharing
    edible: bool = False           # a treat the hero can offer half of
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "fairy"}
        male = {"boy", "father", "grandfather", "man", "wizard"}
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
                "grandmother": "grandma", "grandfather": "grandpa"}.get(
            self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    detail: str = ""               # setting-specific prose detail
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    """The way the hero shares with the morphodite."""
    id: str
    verb: str            # after "would you like to ...": "share a moonberry"
    gerund: str          # after "by sharing ..."        : "sharing a moonberry"
    noun: str            # the thing being offered
    kind: str            # "treat" | "song" | "light" | "story"
    gift: str            # the morphodite's magic response
    tags: set[str] = field(default_factory=set)
    keyword: str = ""    # topic word for generation prompts


@dataclass
class Treasure:
    """The precious thing the hero offers to share."""
    label: str
    phrase: str
    type: str
    kind: str            # matches Activity.kind
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Morphodite:
    """The shape-changing visitor whose magic responds to sharing."""
    id: str
    label: str
    phrase: str
    start_shape: str     # shape it wears on arrival
    true_shape: str      # shape it becomes after the magic
    color: str           # color of its sky / fur
    song: str            # the magic song it sings
    gives: str           # what it sends back into the world
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    # -- narration helpers --------------------------------------------------
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
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_magic_flow(world: World) -> list[str]:
    """morphodite joyful AND treasure shared -> magic_flow accumulates."""
    out: list[str] = []
    for morph in world.characters():
        if morph.type != "morphodite":
            continue
        if morph.memes["joy"] < THRESHOLD:
            continue
        for treasure in world.entities.values():
            if not treasure.precious:
                continue
            if treasure.meters["shared"] < THRESHOLD:
                continue
            sig = ("magic_flow", morph.id, treasure.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            morph.meters["magic_flow"] += 1
            out.append("A soft glow began to gather around the morphodite.")
    return out


def _r_find_shape(world: World) -> list[str]:
    """magic_flow fixpoint -> morphodite finds its true shape."""
    out: list[str] = []
    for morph in world.characters():
        if morph.type != "morphodite":
            continue
        if morph.meters["magic_flow"] < THRESHOLD:
            continue
        sig = ("true_shape", morph.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        morph.meters["true_shape"] += 1
        morph.memes["shyness"] = 0.0
        out.append("__find_shape__")
    return out


def _r_star_fall(world: World) -> list[str]:
    """morphodite in true_shape -> a small star lands for the hero."""
    for morph in world.characters():
        if morph.type != "morphodite":
            continue
        if morph.meters["true_shape"] < THRESHOLD:
            continue
        sig = ("star_fall", morph.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.characters():
            if ch.type != "morphodite":
                ch.meters["star"] += 1
        return ["__star_fall__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="magic_flow", tag="magic", apply=_r_magic_flow),
    Rule(name="find_shape", tag="magic", apply=_r_find_shape),
    Rule(name="star_fall", tag="physical", apply=_r_star_fall),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* offering for this world.
# ---------------------------------------------------------------------------
def treasure_matches(activity: Activity, treasure: Treasure) -> bool:
    """Would this treasure actually be the right thing to offer for this share?"""
    return activity.kind == treasure.kind


def select_morph(activity: Activity, treasure: Treasure) -> Optional[Morphodite]:
    """Pick a morphodite whose magic gift best suits this share.

    In this world every morphodite responds to every kind of sharing, so the
    pick is just the first morphodite.  The function exists to keep the API
    aligned with the constraint gate even though all morphodites support."""
    return MORPHODITES[0] if MORPHODITES else None


# ---------------------------------------------------------------------------
# Prediction: the hero runs the world model forward to foresee the magic.
# ---------------------------------------------------------------------------
def predict_magic(world: World, hero_id: str, treasure_id: str,
                  activity: Activity) -> dict:
    """Simulate the offering silently and report whether magic blooms."""
    sim = world.copy()
    hero = sim.get(hero_id)
    treasure = sim.get(treasure_id)
    morph = next((e for e in sim.characters() if e.type == "morphodite"), None)
    if morph is None:
        return {"magic_flow": 0.0, "true_shape": 0.0, "star": 0.0}
    morph.memes["joy"] += 1
    treasure.meters["shared"] += 1
    propagate(sim, narrate=False)
    return {
        "magic_flow": morph.meters["magic_flow"],
        "true_shape": morph.meters["true_shape"],
        "star": sum(e.meters["star"] for e in sim.characters()
                    if e.type != "morphodite"),
    }


# ---------------------------------------------------------------------------
# Verbs.
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting, morph_def: Morphodite) -> str:
    if setting.detail:
        return (f"{setting.place.capitalize()} was quiet, and {setting.detail}. "
                f"The {morph_def.color} sky shimmered softly above.")
    return f"{setting.place.capitalize()} was quiet, and the {morph_def.color} sky shimmered softly above."


def introduce(world: World, hero: Entity, setting: Setting) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    desc = f"little {trait} {hero.type}".strip()
    world.say(
        f"{hero.id} was a {desc} who lived on {setting.place} and loved "
        f"watching the sky."
    )


def loves_treasure(world: World, hero: Entity, treasure: Entity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"One day, a kind grown-up gave {hero.id} {treasure.phrase}, and "
        f"{hero.id} carried {treasure.it()} in a soft pouch close to "
        f"{hero.pronoun('possessive')} heart."
    )
    world.say(
        f"{hero.id} loved {treasure.it()} because {treasure.it()} tasted "
        f"and smelled like a small piece of the sky."
    )


def morphodite_arrives(world: World, morph: Entity, morph_def: Morphodite) -> None:
    morph.memes["shyness"] += 1
    hero = world.facts["hero"]
    world.say(
        f"One quiet evening, a soft {morph_def.start_shape} drifted down "
        f"from the {morph_def.color} sky and sat near {hero.id}."
    )
    world.say(
        f"It was a morphodite, a kind of creature that can change its shape "
        f"whenever it wants, but it looked very small and shy."
    )


def morphodite_explains(world: World, morph: Entity) -> None:
    morph.memes["shyness"] += 1
    world.say(
        f'"I am still looking for the right place to land," the morphodite '
        f'said softly. "I have no home yet."'
    )


def hero_hesitates(world: World, hero: Entity, treasure: Entity) -> None:
    hero.memes["hesitate"] += 1
    world.say(
        f"{hero.id} looked at {hero.pronoun('possessive')} {treasure.label}, "
        f"the most precious thing {hero.pronoun()} owned, and wondered if "
        f"{hero.pronoun()} should share."
    )


def hero_offers(world: World, hero: Entity, morph: Entity,
                treasure: Entity, activity: Activity) -> None:
    hero.memes["sharing"] += 1
    morph.memes["surprise"] += 1
    world.say(
        f'"Would you like to {activity.verb} with me?" {hero.id} asked, '
        f'holding out the {treasure.label}.'
    )


def morphodite_takes(world: World, morph: Entity, treasure: Entity,
                     activity: Activity) -> None:
    morph.memes["joy"] += 1
    morph.memes["shyness"] = max(0.0, morph.memes["shyness"] - 1)
    treasure.meters["shared"] += 1
    world.say(
        f"The morphodite had never been offered anything before, and its "
        f"eyes grew round as it took a small taste."
    )
    propagate(world, narrate=False)


def magic_blooms(world: World, morph: Entity, morph_def: Morphodite) -> None:
    if morph.meters["true_shape"] < THRESHOLD:
        return
    hero = world.facts["hero"]
    world.say(
        f"Right then, something magical happened. The {morph_def.color} sky "
        f"glowed, and the morphodite slowly changed into {morph_def.true_shape}, "
        f"with kind eyes and a warm smile."
    )
    world.say(
        f"The morphodite sang {morph_def.song}, and {morph_def.gives} "
        f"softly drifted down from the sky and landed right in front of "
        f"{hero.id}."
    )


def become_friends(world: World, hero: Entity, morph: Entity,
                   morph_def: Morphodite) -> None:
    hero.memes["joy"] += 1
    morph.memes["joy"] += 1
    hero.memes["friend"] += 1
    morph.memes["friend"] += 1
    treasure = world.facts["treasure"]
    world.say(
        f"{hero.id} smiled and hugged the new friend, and from that day on, "
        f"{hero.pronoun()} and the morphodite shared every small adventure "
        f"on {world.setting.place}."
    )
    world.say(
        f"The {treasure.label} stayed a little smaller, but the sky felt "
        f"a lot bigger, and that was the very best kind of magic."
    )


# ---------------------------------------------------------------------------
# Verb: do_share (the action of offering, used by prediction).
# ---------------------------------------------------------------------------
def _do_share(world: World, hero: Entity, treasure: Entity,
              activity: Activity, narrate: bool = True) -> None:
    morph = next((e for e in world.characters() if e.type == "morphodite"), None)
    if morph is None:
        return
    if activity.id not in world.setting.affords:
        return
    treasure.meters["shared"] += 1
    morph.memes["joy"] += 1
    propagate(world, narrate=narrate)


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, treasure_cfg: Treasure,
         morph_def: Morphodite, hero_name: str = "Pip",
         hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "kind"]),
    ))
    morph = world.add(Entity(
        id="Morphodite", kind="character", type="morphodite",
        label="the morphodite", traits=["shy"],
    ))
    treasure = world.add(Entity(
        id="Treasure", type=treasure_cfg.type, label=treasure_cfg.label,
        phrase=treasure_cfg.phrase, owner=hero.id,
        precious=True, edible=(treasure_cfg.kind == "treat"),
        plural=treasure_cfg.plural,
    ))

    # Make hero/morph/treasure reachable from verbs even before the end-of-tell
    # facts block is filled in.
    world.facts["hero"] = hero
    world.facts["morph"] = morph
    world.facts["treasure"] = treasure

    # Act 1 -- setup: who the hero is, where they live, the treasure they love.
    introduce(world, hero, setting)
    loves_treasure(world, hero, treasure)

    # Act 2 -- conflict: the morphodite arrives shy, the hero isn't sure.
    world.para()
    morphodite_arrives(world, morph, morph_def)
    morphodite_explains(world, morph)
    hero_hesitates(world, hero, treasure)

    # Act 3 -- resolution: the hero offers, the morphodite takes, magic blooms.
    world.para()
    hero_offers(world, hero, morph, treasure, activity)
    morphodite_takes(world, morph, treasure, activity)
    magic_blooms(world, morph, morph_def)
    become_friends(world, hero, morph, morph_def)

    world.facts.update(activity=activity, setting=setting,
                       morph_def=morph_def, treasure_cfg=treasure_cfg,
                       shared=treasure.meters["shared"] >= THRESHOLD,
                       magic=morph.meters["true_shape"] >= THRESHOLD)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "moon": Setting(
        place="the little silver moon",
        detail="soft craters held silver dust",
        affords={"treat", "song", "light", "story"},
    ),
    "comet": Setting(
        place="the friendly comet's path",
        detail="the comet trailed a glow of pastel lights",
        affords={"treat", "song", "light", "story"},
    ),
    "starstation": Setting(
        place="the tiny star-station",
        detail="warm windows looked out onto swirling stars",
        affords={"treat", "song", "light", "story"},
    ),
    "nebula": Setting(
        place="the gentle nebula grove",
        detail="soft pink and blue clouds drifted close",
        affords={"treat", "song", "light", "story"},
    ),
}

ACTIVITIES = {
    "treat": Activity(
        id="treat",
        verb="share a moonberry",
        gerund="sharing a moonberry",
        noun="moonberry",
        kind="treat",
        gift="a small star",
        tags={"treat", "share"},
        keyword="moonberry",
    ),
    "song": Activity(
        id="song",
        verb="sing a little star-song",
        gerund="singing a star-song",
        noun="star-song",
        kind="song",
        gift="a glowing note of music",
        tags={"song", "share"},
        keyword="star-song",
    ),
    "light": Activity(
        id="light",
        verb="share a piece of starlight",
        gerund="sharing starlight",
        noun="piece of starlight",
        kind="light",
        gift="a tiny lantern of its own",
        tags={"light", "share"},
        keyword="starlight",
    ),
    "story": Activity(
        id="story",
        verb="tell a tiny space story",
        gerund="telling a space story",
        noun="space story",
        kind="story",
        gift="a small constellation",
        tags={"story", "share"},
        keyword="space story",
    ),
}

TREASURES = {
    "moonberry": Treasure(
        label="moonberry",
        phrase="a glowing moonberry in a tiny pouch",
        type="berry",
        kind="treat",
    ),
    "star_cookie": Treasure(
        label="star cookie",
        phrase="a sugar-dusted star cookie",
        type="cookie",
        kind="treat",
    ),
    "star_song": Treasure(
        label="star-song",
        phrase="a small star-song hummed at bedtime",
        type="song",
        kind="song",
    ),
    "starlight": Treasure(
        label="starlight",
        phrase="a pinch of warm starlight in a jar",
        type="light",
        kind="light",
    ),
    "comet_tale": Treasure(
        label="comet tale",
        phrase="a short tale about a wandering comet",
        type="story",
        kind="story",
    ),
}

MORPHODITES = [
    Morphodite(
        id="cloud",
        label="cloud morphodite",
        phrase="a soft cloud morphodite",
        start_shape="cloud",
        true_shape="a small kind friend with paws like cotton",
        color="soft white",
        song="a song that smelled like rain",
        gives="a tiny star",
        tags={"cloud"},
    ),
    Morphodite(
        id="kitten",
        label="kitten morphodite",
        phrase="a tiny kitten morphodite",
        start_shape="kitten",
        true_shape="a gentle friend with a silver tail",
        color="silver",
        song="a purr that sounded like a lullaby",
        gives="a small constellation",
        tags={"kitten"},
    ),
    Morphodite(
        id="moonlet",
        label="moonlet morphodite",
        phrase="a tiny moon morphodite",
        start_shape="moon",
        true_shape="a friend whose laugh made craters smile",
        color="pale gold",
        song="a hum that twinkled like night",
        gives="a glowing note of music",
        tags={"moonlet"},
    ),
]

CHILD_NAMES = ["Pip", "Bex", "Nix", "Tomo", "Luma", "Ari", "Suki", "Ren",
               "Kiri", "Yuki"]
TRAITS = ["curious", "kind", "gentle", "brave", "thoughtful", "soft-spoken"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, activity, treasure) triples that pass the constraint gate."""
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in sorted(setting.affords):
            act = ACTIVITIES[act_id]
            for treasure_id, treasure in TREASURES.items():
                if treasure_matches(act, treasure):
                    combos.append((place, act_id, treasure_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    activity: str
    treasure: str
    morphodite: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "morphodite": [("What is a morphodite?",
                    "A morphodite is a soft, fluffy creature that can change "
                    "its shape whenever it wants, taking the form of clouds, "
                    "kittens, moons, or anything gentle.")],
    "share": [("Why is sharing kind?",
               "Sharing is kind because it gives a friend something they "
               "were missing, and it makes both people feel warm inside.")],
    "magic": [("What is magic in a story?",
               "Magic in a story is a special surprise that happens when "
               "someone does something gentle, brave, or kind.")],
    "moonberry": [("What is a moonberry?",
                    "A moonberry is a sweet, glowing berry that tastes like "
                    "starlight and is found in small silver pouches.")],
    "star": [("Where do stars come from?",
              "Stars come from tiny bits of warm light that gather up high "
              "in the sky and twinkle for us to see.")],
    "constellation": [("What is a constellation?",
                       "A constellation is a pattern made by a group of "
                       "stars that seem to form a picture together.")],
    "lullaby": [("What is a lullaby?",
                 "A lullaby is a soft song that helps someone feel sleepy "
                 "and safe at bedtime.")],
    "shy": [("What does shy mean?",
             "Shy means feeling a little quiet or unsure around new people, "
             "until something gentle helps you feel brave.")],
    "space": [("What is space?",
               "Space is the great, soft darkness above the sky where stars, "
               "moons, and comets travel in slow, glowing paths.")],
    "comet": [("What is a comet?",
               "A comet is a traveler of space that drifts through the sky "
               "leaving a long, glowing tail behind it.")],
    "nebula": [("What is a nebula?",
                "A nebula is a soft cloud of colored light in space, where "
                "new stars are sometimes born.")],
}
KNOWLEDGE_ORDER = ["morphodite", "share", "magic", "moonberry", "star",
                   "constellation", "lullaby", "shy", "space", "comet",
                   "nebula"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, morph_def, act, treasure_cfg = (f["hero"], f["morph_def"],
                                          f["activity"], f["treasure_cfg"])
    kw = act.keyword or act.kind
    return [
        f'Write a short, gentle space adventure for a 3-to-5-year-old on '
        f'the theme "sharing brings magic" that uses the word "{kw}".',
        f'Tell a story where a small explorer named {hero.id} meets a '
        f'{morph_def.label} who is shy, and they {act.verb}, and magic '
        f'blooms between them.',
        f'Write a TinyStories-style story about a morphodite who changes '
        f'shape and a child who learns that the kindest thing to do is '
        f'share.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, morph, morph_def = f["hero"], f["morph"], f["morph_def"]
    treasure, act = f["treasure"], f["activity"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    trait = next((t for t in hero.traits if t != "little"), "curious")
    place = world.setting.place
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who lives on {place} and meets a shy {morph_def.label}?"
            ),
            answer=(
                f"A little {trait} {hero.type} named {hero.id} lives on "
                f"{place} and meets a {morph_def.label} that drifts down "
                f"from the {morph_def.color} sky."
            ),
        ),
        QAItem(
            question=(
                f"What precious thing does {hero.id} carry on {place} before "
                f"the {morph_def.label} arrives?"
            ),
            answer=(
                f"{hero.id} carries {treasure.phrase}, and loves "
                f"{treasure.it()} because {treasure.it()} tastes and smells "
                f"like a piece of the sky."
            ),
        ),
        QAItem(
            question=(
                f"Why did the {morph_def.label} look shy when it landed near "
                f"{hero.id} on {place}?"
            ),
            answer=(
                f"The morphodite was shy because it had no home yet and was "
                f"still looking for the right place to land."
            ),
        ),
    ]
    if f.get("shared"):
        qa.append(QAItem(
            question=(
                f"What did {hero.id} offer the {morph_def.label} on {place} "
                f"that started the magic?"
            ),
            answer=(
                f"{hero.id} offered to {act.verb}, and the morphodite took a "
                f"small taste because it had never been offered anything "
                f"before."
            ),
        ))
    if f.get("magic"):
        qa.append(QAItem(
            question=(
                f"What magic happened after {hero.id} shared "
                f"{pos} {treasure.label} with the {morph_def.label}?"
            ),
            answer=(
                f"The {morph_def.color} sky glowed, the morphodite changed "
                f"into {morph_def.true_shape}, and {morph_def.song} sent "
                f"{morph_def.gives} softly down to {hero.id}."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {hero.id} and the {morph_def.label} feel at the "
                f"end of their first meeting on {place}?"
            ),
            answer=(
                f"{hero.id} and the morphodite became friends, and from that "
                f"day on they shared every small adventure together on "
                f"{place}."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags: set[str] = {"morphodite", "share", "magic", "space"}
    tags.add(f["activity"].kind)
    place = f["setting"].place
    if "moon" in place:
        tags.add("moonberry")
    if "comet" in place:
        tags.add("comet")
    if "nebula" in place:
        tags.add("nebula")
    if f["treasure_cfg"].kind == "treat":
        tags.add("moonberry")
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


# ---------------------------------------------------------------------------
# CLI / trace.
# ---------------------------------------------------------------------------
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
        if e.precious:
            bits.append("precious")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moon", activity="treat", treasure="moonberry",
                morphodite="cloud", name="Pip", gender="girl", trait="kind"),
    StoryParams(place="starstation", activity="song", treasure="star_song",
                morphodite="kitten", name="Bex", gender="boy",
                trait="thoughtful"),
    StoryParams(place="comet", activity="light", treasure="starlight",
                morphodite="moonlet", name="Nix", gender="girl",
                trait="gentle"),
    StoryParams(place="nebula", activity="story", treasure="comet_tale",
                morphodite="cloud", name="Tomo", gender="boy",
                trait="curious"),
    StoryParams(place="moon", activity="treat", treasure="star_cookie",
                morphodite="moonlet", name="Luma", gender="girl",
                trait="brave"),
]


def explain_rejection(activity: Activity, treasure: Treasure) -> str:
    return (f"(No story: the morphodite can respond to {activity.gerund}, but "
            f"{treasure.label} is a {treasure.kind} offering, which does not "
            f"match. Try a treasure of the same kind, e.g. a {activity.kind} "
            f"treasure.)")


def explain_morph(morph_id: str) -> str:
    valid = ", ".join(m.id for m in MORPHODITES)
    return (f"(No morphodite with id {morph_id!r}; try one of: {valid}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- declarative twin of the reasonableness gate.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A treasure fits an activity when their share kinds match.
fits(A, T) :- activity_kind(A, K), treasure_kind(T, K).

% A place hosts the share when it affords it; valid = (place, act, treasure)
% with both place-affords-activity and act-treasure-kind-match.
valid(Place, A, T) :- affords(Place, A), fits(A, T).

% In this world every morphodite responds to every share, so a valid story
% is any (place, activity, treasure, morphodite) with a valid combo.
valid_story(Place, A, T, M) :- valid(Place, A, T), morphodite(M).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("activity_kind", aid, a.kind))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("treasure_kind", tid, t.kind))
        if t.plural:
            lines.append(asp.fact("treasure_plural", tid))
    for m in MORPHODITES:
        lines.append(asp.fact("morphodite", m.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, activity, treasure) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    """(place, activity, treasure, morphodite) -- morph-aware compatible stories."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() "
              f"({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a morphodite, a sharing, a small "
                    "magic. Unspecified choices are picked at random "
                    "(seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--morphodite", choices=[m.id for m in MORPHODITES])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1,
                    help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true",
                    help="render the curated set instead")
    ap.add_argument("--trace", action="store_true",
                    help="dump world-model state")
    ap.add_argument("--qa", action="store_true",
                    help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true",
                    help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if args.activity and args.treasure:
        act, tr = ACTIVITIES[args.activity], TREASURES[args.treasure]
        if not treasure_matches(act, tr):
            raise StoryError(explain_rejection(act, tr))
    if args.morphodite and args.morphodite not in {m.id for m in MORPHODITES}:
        raise StoryError(explain_morph(args.morphodite))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, treasure_id = rng.choice(sorted(combos))
    morph_id = args.morphodite or rng.choice([m.id for m in MORPHODITES])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, treasure=treasure_id,
        morphodite=morph_id, name=name, gender=gender, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    morph_def = next(m for m in MORPHODITES if m.id == params.morphodite)
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 TREASURES[params.treasure], morph_def,
                 params.name, params.gender,
                 [params.trait, "gentle"])
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
        print(f"{len(triples)} compatible (place, activity, treasure) combos "
              f"({len(stories)} with morphodite):\n")
        for place, act, treasure in triples:
            morphs = sorted({m for (pl, a, tr, m) in stories
                             if (pl, a, tr) == (place, act, treasure)})
            print(f"  {place:13} {act:6} {treasure:11}  "
                  f"[{', '.join(morphs)}]")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2,
                             ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (f"### {p.name}: sharing a {p.treasure} with a "
                      f"{p.morphodite} morphodite at {p.place}")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
