#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/bale_amenity_magic_tall_tale.py
======================================================================================================

A standalone *story world* sketch in the Tall Tale style for a small domain
about a bale, an amenity, and a touch of Magic.

Initial story (used to build the world model):
---
Way out past the windmill and the wide blue creek, old Hettie Mae kept a
single bale of golden hay on a wagon behind her porch. She called it the
"Welcome Bale," because every traveler who passed by got a free seat, a
cool drink, and the kind of tall tale that turned a hot afternoon into a
holiday.

One summer, the creek ran low and the town pump began to groan. There was
no amenity anywhere -- no shade, no bench, no cup of cold water -- and the
folk who came down the road grew tired and cross. Hettie Mae scratched her
chin and said, "Well, that is a sorry state of affairs, and I have just
the thing."

She rolled the Welcome Bale down to the crossroads, propped it under the
old oak, and set a tin cup on top. Then she whispered a Magic word her
grandmother had taught her, and the bale began to do something it had
never done before: it made itself useful.

First it gave the traveler a seat when their legs ached. Then it tipped
its top to pour a cup of cold sweet water when their throat was dry.
Then it told a tale so tall that the wind itself stopped to listen, and
the traveler laughed so hard the ache and the thirst both ran away.

Word spread across the county. By the end of the week, every road that
led to Hettie Mae's crossroads had a friendly bench again, and the
people remembered that a kind amenity and a Magic story could mend a
hard day quicker than any well bucket ever could.

Causal state updates:
---
    do help                  -> bale.<amenity> += 1
                                actor.cheer += 1
    bale used for traveler   -> bale.wear += 1
    bale.tell -> tale        -> crowd.amusement += 1   (the teller shortens the day)
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Amenity kinds the bale can offer.
AMENITY_KINDS = {"seat", "shade", "drink", "tale"}

# Crowd roles at the crossroads.
ROLES = {"traveler", "child", "farmer", "neighbor", "elder"}


# ---------------------------------------------------------------------------
# Entities: characters and the magical bale share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # bale, traveler, child, farmer, neighbor, elder
    label: str = ""                # short reference, e.g. "bale", "the traveler"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    role: str = ""                 # one of ROLES (for characters at the crossroads)
    owner: Optional[str] = None
    plural: bool = False
    # Two numeric dimensions, treated uniformly.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional / social

    def pronoun(self, case: str = "subject") -> str:
        female = {"child": "girl", "elder": "elder"}
        male = {"child": "boy"}
        # Bale itself uses "it" pronouns.
        if self.type == "bale":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        # Crowds of travelers/neighbors use they/them.
        if self.type in {"traveler", "neighbor", "farmer", "crowd"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        g = self.type
        if g in {"girl", "woman", "hettie", "elder"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if g in {"boy", "man", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the crossroads"            # the crossroads, the porch, the oak, the creek
    scene: str = "open"                      # open | porch | shade
    affords: set[str] = field(default_factory=set)   # which amenities the bale can give here


@dataclass
class Amenity:
    """One helpful thing the bale can offer (kind = seat | shade | drink | tale)."""
    id: str
    kind: str            # one of AMENITY_KINDS
    noun: str            # "a cool seat", "a splash of cold water"
    verb: str            # what the bale does: "settled down into a bench"
    need: str            # what ails the traveler: "aching legs"
    fixes: str           # how the traveler feels after: "rested"
    tags: set[str] = field(default_factory=set)


@dataclass
class Magic:
    """A small enchantment the bale learns in this story."""
    id: str
    word: str            # the whispered word: "Welcome"
    twist: str           # what changes: "the bale began to do what was needed"
    glow: str            # a one-line image: "the straw shone soft and warm"
    tags: set[str] = field(default_factory=set)


@dataclass
class Bale:
    """The friendly bale at the heart of the tale."""
    id: str = "bale"
    label: str = "the Welcome Bale"
    phrase: str = "a single golden bale of hay"
    keeper: str = "Hettie Mae"
    traits: list[str] = field(default_factory=lambda: ["golden", "round", "patient"])
    plural: bool = False


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        # The currently active amenity (so rules know what the bale is doing).
        self.active_amenity: Optional[str] = None
        # Facts recorded during the screenplay, read back by the Q&A generators.
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
        clone.active_amenity = self.active_amenity
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_help(world: World) -> list[str]:
    """bale.active_amenity -> bale.<kind> += 1, bale.wear += 1, actor.cheer += 1."""
    out: list[str] = []
    bale = world.entities.get("bale")
    if bale is None or world.active_amenity is None:
        return out
    kind = world.active_amenity
    sig = ("help", kind)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bale.meters[kind] += 1
    bale.meters["wear"] += 1
    for actor in world.characters():
        actor.memes["cheer"] += 1
    out.append(
        f"The bale was glad to help, and a little straw fell like a smile."
    )
    return out


def _r_tale_amusement(world: World) -> list[str]:
    """bale.tale given -> crowd.amusement += 1 (the tall tale does its work)."""
    out: list[str] = []
    bale = world.entities.get("bale")
    if bale is None or bale.meters["tale"] < THRESHOLD:
        return out
    sig = ("tale", "amusement")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for actor in world.characters():
        actor.memes["amusement"] += 1
    out.append("The crowd laughed so hard the wind itself stopped to listen.")
    return out


def _r_keeper_pride(world: World) -> list[str]:
    """keeper helped three folks -> keeper.pride += 1."""
    out: list[str] = []
    bale = world.entities.get("bale")
    if bale is None:
        return out
    if bale.meters["seat"] + bale.meters["shade"] + bale.meters["drink"] + bale.meters["tale"] < 3:
        return out
    keeper = world.entities.get(bale.owner or "")
    if keeper is None:
        return out
    sig = ("keeper", "pride")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keeper.memes["pride"] += 1
    return []  # narrated inline by the screenplay; keep prose focused


CAUSAL_RULES: list[Rule] = [
    Rule(name="help", tag="physical", apply=_r_help),
    Rule(name="tale_amusement", tag="social", apply=_r_tale_amusement),
    Rule(name="keeper_pride", tag="social", apply=_r_keeper_pride),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* amenity for this bale+place.
# ---------------------------------------------------------------------------
def amenity_fits(amenity: Amenity, setting: Setting) -> bool:
    """Can this amenity actually happen at this place?"""
    return amenity.kind in setting.affords


def magic_fits(magic: Magic, bale: Bale) -> bool:
    """Every Magic spell is OK for the Welcome Bale; reserved hook."""
    return bool(bale.label)


def select_amenity(setting: Setting, bale: Bale, rng: random.Random) -> Amenity:
    pool = [a for a in AMENITIES if amenity_fits(a, setting)]
    if not pool:
        raise StoryError(f"(No amenity fits the {setting.place}.)")
    # The bale's first trick should be a seat -- we want at least one body amenity
    # before the tall tale resolves things.
    rng.shuffle(pool)
    return rng.choice(pool[:1] + sorted(pool, key=lambda a: 0 if a.kind == "seat" else 1)[:2])


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting) -> str:
    if setting.scene == "porch":
        return f"The {setting.place.removeprefix('the ')} was shaded by a tin roof, and a kettle hummed."
    if setting.place == "the creek":
        return "The creek was low, and the bed of stones caught the afternoon sun."
    if setting.place == "the oak":
        return "The old oak spread wide over the crossroads, and its leaves made a slow green shade."
    return f"{setting.place.capitalize()} was wide open to the sky, and the wind had nowhere to hide."


def introduce(world: World, keeper: Entity, bale: Entity) -> None:
    trait = " ".join(t for t in bale.traits if t != "patient")
    world.say(
        f"Way out past the windmill and the wide blue creek, {keeper.id} kept "
        f"{bale.phrase} on a wagon behind her porch."
    )
    world.say(
        f"She called it \"{bale.label},\" because every traveler who passed by "
        f"got a free seat, a cool drink, and the kind of tall tale that turned "
        f"a hot afternoon into a holiday."
    )


def town_problem(world: World, setting: Setting) -> None:
    world.say(
        f"One summer, the creek ran low and the town pump began to groan."
    )
    world.say(
        f"There was no amenity to speak of at {setting.place} -- no shade, no "
        f"bench, no cup of cold water -- and the folk who came down the road "
        f"grew tired and cross."
    )


def keeper_decides(world: World, keeper: Entity) -> None:
    keeper.memes["thought"] += 1
    world.say(
        f"{keeper.id} scratched her chin and said, \"Well, that is a sorry "
        f"state of affairs, and I have just the thing.\""
    )


def roll_bale(world: World, keeper: Entity, bale: Entity, setting: Setting) -> None:
    bale.meters["moves"] += 1
    world.say(
        f"She rolled the {bale.label} down to {setting.place}, propped it "
        f"under the shade, and set a tin cup on top."
    )


def magic_works(world: World, bale: Entity, magic: Magic) -> None:
    bale.memes["enchanted"] += 1
    bale.memes["magic"] += 1
    world.say(
        f"Then she whispered the word \"{magic.word}\" her grandmother had "
        f"taught her, and {magic.glow}."
    )
    world.say(f"The bale {magic.twist}.")


def offer_amenity(world: World, bale: Entity, amenity: Amenity,
                  traveler: Entity, setting: Setting) -> None:
    world.active_amenity = amenity.kind
    world.facts["featured_amenity"] = amenity.kind
    traveler.memes["need"] += 1
    traveler.meters["tired"] += 1
    world.say(
        f"When a traveler came down the road with {amenity.need}, the bale "
        f"{amenity.verb}, and {amenity.noun} was waiting."
    )
    propagate(world, narrate=False)


def feel_better(world: World, traveler: Entity, amenity: Amenity) -> None:
    traveler.memes["need"] = 0.0
    traveler.meters["tired"] = 0.0
    traveler.memes["cheer"] += 1
    world.say(
        f"The traveler felt {amenity.fixes} and tipped their hat to the "
        f"{bale_label(world)}."
    )


def bale_label(world: World) -> str:
    bale = world.entities.get("bale")
    return bale.label if bale else "bale"


def tall_tale(world: World, bale: Entity, amenity: Amenity, magic: Magic) -> None:
    world.active_amenity = "tale"
    world.facts["featured_amenity"] = "tale"
    world.say(
        f"Then the bale did its favorite trick: it told a tale so tall that "
        f"{magic.glow}, and the traveler laughed so hard the ache and the "
        f"thirst both ran away."
    )
    propagate(world, narrate=False)


def news_spreads(world: World, bale: Entity, setting: Setting) -> None:
    bale.memes["fame"] += 1
    world.say(
        f"Word spread across the county. By the end of the week, every road "
        f"that led to {setting.place} had a friendly bench again."
    )


def coda(world: World, keeper: Entity, bale: Entity) -> None:
    keeper.memes["pride"] += 1
    bale.memes["pride"] += 1
    world.say(
        f"The people remembered that a kind amenity and a Magic story could "
        f"mend a hard day quicker than any well bucket ever could."
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, amenity: Amenity, magic: Magic,
         bale: Bale, keeper_name: str = "Hettie Mae",
         traveler_role: str = "traveler") -> World:
    world = World(setting)

    keeper = world.add(Entity(
        id=keeper_name, kind="character", type="hettie",
        label="the keeper", traits=["kind", "quiet", "knowing"],
    ))
    bale_ent = world.add(Entity(
        id=bale.id, kind="thing", type="bale",
        label=bale.label, phrase=bale.phrase,
        owner=keeper.id, traits=bale.traits, plural=False,
    ))
    traveler = world.add(Entity(
        id="Traveler", kind="character", type=traveler_role,
        label="the traveler", role=traveler_role,
        traits=["weary", "polite"],
    ))
    bale_ent.owner = keeper.id

    # Act 1 -- the welcome bale and the friendly custom.
    introduce(world, keeper, bale_ent)

    # Act 2 -- the town's drought of amenities, the keeper's spell.
    world.para()
    town_problem(world, setting)
    setting_detail_line = setting_detail(setting)
    world.say(setting_detail_line)
    keeper_decides(world, keeper)
    roll_bale(world, keeper, bale_ent, setting)
    magic_works(world, bale_ent, magic)

    # Act 3 -- the bale offers what is needed, then tells a tall tale.
    world.para()
    offer_amenity(world, bale_ent, amenity, traveler, setting)
    feel_better(world, traveler, amenity)
    tall_tale(world, bale_ent, amenity, magic)

    world.para()
    news_spreads(world, bale_ent, setting)
    coda(world, keeper, bale_ent)

    world.facts.update(
        keeper=keeper, bale=bale_ent, traveler=traveler,
        amenity=amenity, magic=magic, setting=setting,
        bale_cfg=bale, featured_amenity=world.facts.get("featured_amenity"),
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "crossroads": Setting(place="the crossroads", scene="open",
                          affords={"seat", "shade", "drink", "tale"}),
    "oak": Setting(place="the oak", scene="shade",
                   affords={"seat", "shade", "tale"}),
    "porch": Setting(place="the porch", scene="porch",
                     affords={"seat", "drink", "tale"}),
    "creek": Setting(place="the creek", scene="open",
                     affords={"shade", "drink", "tale"}),
}

AMENITIES = [
    Amenity(
        id="seat", kind="seat",
        noun="a cool seat out of the breeze",
        verb="settled itself into a friendly bench",
        need="aching legs",
        fixes="rested",
        tags={"seat", "rest"},
    ),
    Amenity(
        id="shade", kind="shade",
        noun="a soft pocket of shade",
        verb="lifted its top to make a parasol",
        need="a sunburnt neck",
        fixes="cooler",
        tags={"shade", "cool"},
    ),
    Amenity(
        id="drink", kind="drink",
        noun="a tin cup of cold sweet water",
        verb="tipped a cup from its crown",
        need="a dry throat",
        fixes="refreshed",
        tags={"drink", "water"},
    ),
    Amenity(
        id="tale", kind="tale",
        noun="a story taller than the windmill",
        verb="opened like a book of bright words",
        need="a heavy afternoon",
        fixes="lighter",
        tags={"tale", "tall tale"},
    ),
]

MAGICS = [
    Magic(
        id="welcome", word="Welcome",
        twist="began to do what was needed",
        glow="the straw shone soft and warm",
        tags={"welcome"},
    ),
    Magic(
        id="kindly", word="Kindly",
        twist="listened for the need before it acted",
        glow="a calm hum rose out of the hay",
        tags={"kindly"},
    ),
    Magic(
        id="share", word="Share",
        twist="gave a little of itself to whoever passed",
        glow="a golden thread of light stitched the air",
        tags={"share"},
    ),
]

KEEPERS = ["Hettie Mae", "Aunt Cora", "Miss Della", "Old Josie", "Widow Pearl"]
TRAVELER_ROLES = ["traveler", "child", "farmer", "neighbor", "elder"]
BALE_TRAITS = ["golden", "round", "patient", "sturdy", "sun-warmed"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(setting, amenity, magic) triples that pass the reasonableness constraint."""
    combos = []
    for sid, s in SETTINGS.items():
        for a in AMENITIES:
            if amenity_fits(a, s):
                for m in MAGICS:
                    combos.append((sid, a.id, m.id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    setting: str
    amenity: str
    magic: str
    keeper: str
    traveler_role: str
    bale_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bale": [
        ("What is a bale of hay?",
         "A bale of hay is a big bundle of dried grass that has been tied "
         "tight so it can be stored, moved, and given to farm animals to eat."),
    ],
    "amenity": [
        ("What is an amenity?",
         "An amenity is something helpful that makes a place more comfortable, "
         "like a bench, a cup of water, or a patch of shade on a hot day."),
    ],
    "magic": [
        ("What does 'magic' mean in a story?",
         "In a story, magic is a special power or charm that can do things the "
         "everyday world cannot, like making a bale of hay pour a drink or "
         "tell a tale on its own."),
    ],
    "tall tale": [
        ("What is a tall tale?",
         "A tall tale is a story that makes small things sound huge and funny, "
         "the way fishermen brag about the fish that got away. It is told for "
         "laughs and wonder, not to be taken literally."),
    ],
    "seat": [
        ("Why is a seat an amenity?",
         "A seat is an amenity because it gives tired travelers a place to rest "
         "their legs and feel welcome."),
    ],
    "shade": [
        ("Why is shade helpful on a hot day?",
         "Shade is helpful on a hot day because it blocks the sun, so people "
         "and animals can stay cooler under it."),
    ],
    "drink": [
        ("Why is a drink of water an amenity?",
         "A drink of water is an amenity because it helps a thirsty traveler "
         "feel better and keeps them going on the road."),
    ],
    "tale": [
        ("Why do people tell tales at the side of the road?",
         "People tell tales at the side of the road to pass the time, to cheer "
         "each other up, and to make a long afternoon feel shorter and brighter."),
    ],
    "welcome": [
        ("What does it mean to feel welcome?",
         "To feel welcome means to feel like a place is glad you came and "
         "wants to make you comfortable while you are there."),
    ],
    "kindly": [
        ("What does it mean to act kindly?",
         "To act kindly is to do gentle, helpful things for other people "
         "without being asked."),
    ],
    "share": [
        ("What does it mean to share?",
         "To share is to give a part of what you have to someone else, so "
         "they can use it too."),
    ],
}
KNOWLEDGE_ORDER = ["bale", "amenity", "magic", "tall tale",
                   "seat", "shade", "drink", "tale",
                   "welcome", "kindly", "share"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    bale, keeper, amenity, magic = f["bale"], f["keeper"], f["amenity"], f["magic"]
    return [
        f'Write a short story for a 5-to-8-year-old in the Tall Tale style '
        f'on the theme "a bale, an amenity, a magic kindness" that includes '
        f'the word "{bale.label}".',
        f'Tell a warm Tall Tale where a kind keeper named {keeper.id} uses a '
        f'Magic word ({magic.word}) on a golden bale of hay so that weary '
        f'travelers at {f["setting"].place} are offered {amenity.noun} when '
        f'they need it.',
        f'Write a simple story that uses the nouns "bale" and "amenity" and '
        f'ends with a community remembering that kindness and a Magic story '
        f'can mend a hard day.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    bale, keeper, amenity, magic, traveler = (
        f["bale"], f["keeper"], f["amenity"], f["magic"], f["traveler"]
    )
    setting = f["setting"]
    place = setting.place
    sub, obj, pos = (bale.pronoun("subject"), bale.pronoun("object"), bale.pronoun("possessive"))
    keep_pos = keeper.pronoun("possessive")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"What was the friendly bale of hay used for at {place}, and "
                f"who kept it on the wagon behind the porch?"
            ),
            answer=(
                f"It was called the {bale.label}, and {keeper.id} kept it on a "
                f"wagon behind the porch so any traveler could stop, rest, "
                f"and hear a kind tale."
            ),
        ),
        QAItem(
            question=(
                f"What was missing at {place} that made the townsfolk tired "
                f"and cross in the story about the {bale.label}?"
            ),
            answer=(
                f"There was no amenity at {place} -- no shade, no bench, no "
                f"cup of cold water -- and the folk who came down the road "
                f"grew tired and cross because of it."
            ),
        ),
        QAItem(
            question=(
                f"How did {keeper.id} use the Magic word to make the bale "
                f"helpful at {place}?"
            ),
            answer=(
                f"{keeper.id} whispered the word \"{magic.word}\" her "
                f"grandmother had taught her, and {magic.glow}. The bale "
                f"{magic.twist}."
            ),
        ),
    ]
    # Featured-amenity question (varies with which one we picked).
    if amenity.id in {"seat", "shade", "drink", "tale"}:
        qa.append(QAItem(
            question=(
                f"What did the {bale.label} do for the traveler who came "
                f"down the road with {amenity.need}?"
            ),
            answer=(
                f"The bale {amenity.verb}, and {amenity.noun} was waiting. "
                f"The traveler felt {amenity.fixes} and tipped their hat."
            ),
        ))
    qa.append(QAItem(
        question=(
            f"How did the community feel at the end of the tale about the "
            f"{bale.label} and the Magic word \"{magic.word}\"?"
        ),
        answer=(
            f"They felt welcome and proud. By the end of the week, every "
            f"road that led to {place} had a friendly bench again, and the "
            f"people remembered that a kind amenity and a Magic story could "
            f"mend a hard day."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = {"bale", "amenity", "magic", "tall tale", f["amenity"].kind, f["magic"].id}
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
# CLI / trace
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        setting="crossroads", amenity="seat", magic="welcome",
        keeper="Hettie Mae", traveler_role="traveler", bale_trait="golden",
    ),
    StoryParams(
        setting="oak", amenity="shade", magic="kindly",
        keeper="Aunt Cora", traveler_role="farmer", bale_trait="sun-warmed",
    ),
    StoryParams(
        setting="porch", amenity="drink", magic="share",
        keeper="Miss Della", traveler_role="child", bale_trait="round",
    ),
    StoryParams(
        setting="creek", amenity="tale", magic="welcome",
        keeper="Old Josie", traveler_role="elder", bale_trait="patient",
    ),
    StoryParams(
        setting="crossroads", amenity="tale", magic="share",
        keeper="Widow Pearl", traveler_role="neighbor", bale_trait="sturdy",
    ),
]


def explain_rejection(amenity: Amenity, setting: Setting) -> str:
    return (f"(No story: {amenity.kind} doesn't fit {setting.place} -- "
            f"this amenity only works at {sorted(s for s, ss in SETTINGS.items() if amenity.kind in ss.affords)}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# Inline rules + registry-derived facts so the two can never drift.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% An amenity fits a setting when the setting affords its kind.
amenity_fits(A, S) :- amenity(A, K), affords(S, K).

% Every Magic spell is OK for the Welcome Bale; reserved hook.
magic_fits(M, B) :- magic(M), bale(B).

% A (setting, amenity, magic) triple is a valid story when the amenity fits
% the setting and the magic fits the bale.
valid(S, A, M) :- amenity_fits(A, S), magic_fits(M, bale).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for k in sorted(s.affords):
            lines.append(asp.fact("affords", sid, k))
    for a in AMENITIES:
        lines.append(asp.fact("amenity", a.id, a.kind))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", a.id, t))
    for m in MAGICS:
        lines.append(asp.fact("magic", m.id))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", m.id, t))
    lines.append(asp.fact("bale", "bale"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (setting, amenity, magic) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
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
        description='Story world sketch: a bale, an amenity, a Magic kindness. '
                    'Tall Tale style. Unspecified choices are picked at random (seeded).')
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--amenity", choices=[a.id for a in AMENITIES])
    ap.add_argument("--magic", choices=[m.id for m in MAGICS])
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--traveler-role", choices=TRAVELER_ROLES)
    ap.add_argument("--bale-trait", choices=BALE_TRAITS)
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
    """Fill in any unspecified choices at random, keeping the combo reasonable."""
    if args.amenity and args.setting:
        a = next(am for am in AMENITIES if am.id == args.amenity)
        if not amenity_fits(a, SETTINGS[args.setting]):
            raise StoryError(explain_rejection(a, SETTINGS[args.setting]))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.amenity is None or c[1] == args.amenity)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, amenity, magic = rng.choice(sorted(combos))
    keeper = args.keeper or rng.choice(KEEPERS)
    traveler_role = args.traveler_role or rng.choice(TRAVELER_ROLES)
    bale_trait = args.bale_trait or rng.choice(BALE_TRAITS)
    return StoryParams(
        setting=setting,
        amenity=amenity,
        magic=magic,
        keeper=keeper,
        traveler_role=traveler_role,
        bale_trait=bale_trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    setting = SETTINGS[params.setting]
    amenity = next(a for a in AMENITIES if a.id == params.amenity)
    magic = next(m for m in MAGICS if m.id == params.magic)
    bale = Bale()
    bale.traits = ["golden", "round", params.bale_trait]
    world = tell(setting, amenity, magic, bale,
                 keeper_name=params.keeper, traveler_role=params.traveler_role)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, amenity, magic) combos:\n")
        for setting, amenity, magic in triples:
            print(f"  {setting:11} {amenity:8} {magic}")
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
            header = f"### {p.keeper}: {p.amenity} at {p.setting} (magic: {p.magic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
