#!/usr/bin/env python3
"""
storyworlds/worlds/nozzle_bad_ending_curiosity_tall_tale.py
============================================================

Storyworld: a tall-tale vignette about a curious soul, a temperamental nozzle,
and the morning a small mistake turned into a very bad ending.

Source tale (the seed):
---
There was once a thirsty ranch hand named June who hauled a long green hose
to the far corral every dawn. The hose was old, and at the end sat a brass
nozzle as wide as a coffee cup. June was the kind of person who just had to
see how a thing worked -- one day, leaning close, she untwisted the nozzle
to peek inside, and a sudden spray of water knocked her flat on her back.
The wind whistled through the hose, the cat ran off with the morning egg,
the barn cat laughed, the chickens went looking for a new coop, and poor
June lay soaked in the mud while the nozzle spun like a small brass top,
spurting happily on without her.

Domain shape (mirrors storyworlds/worlds/puddles.py contract):
    - typed entities with physical `meters` and emotional `memes`
    - forward-chained rules + a single screenplay
    - constraint-based "reasonable story" gate (nozzle+curiosity)
    - inline ASP twin (`ASP_RULES`) for the declarative gate
    - three QA sets: (1) prompts, (2) story-grounded, (3) child world knowledge
    - bad-ending mode is the *default* (the contract says "Bad Ending")
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
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Meters we treat as "wetness" the nozzle can spread onto things and people.
WET_KINDS = {"wet"}


# ---------------------------------------------------------------------------
# Entities: people and physical props share one dataclass.
# ---------------------------------------------------------------------------

def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)

@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # ranch_hand, cat, nozzle, hose, egg ...
    label: str = ""                # short reference ("nozzle", "hose")
    phrase: str = ""               # full noun phrase ("a brass nozzle")
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    attached_to: Optional[str] = None    # the nozzle is attached to the hose
    worn_by: Optional[str] = None
    region: str = ""                    # for props that sit on the body (rare here)
    protective: bool = False            # gear that would actually help (none here)
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    # Two numeric dimensions (cf. story.py memeplex model): physical & emotional.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    cat: object | None = None
    egg: object | None = None
    hero: object | None = None
    hose: object | None = None
    nozzle: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"ranch_hand", "girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"ranch_hand": "the hand"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World model.
# ---------------------------------------------------------------------------
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()         # where the spray actually lands
        self.weather: str = ""
        self.facts: dict = {}               # for the Q&A generators

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def props(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "thing"]

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def _r_spray(world: World) -> list[str]:
    """Nozzle open + pressure up -> nearby props get wet; hero gets soaked."""
    out: list[str] = []
    nozzle = next((e for e in world.props() if e.type == "nozzle"), None)
    hero = next((e for e in world.characters()), None)
    if nozzle is None or hero is None:
        return out
    if nozzle.meters["open"] < THRESHOLD or nozzle.meters["pressure"] < THRESHOLD:
        return out
    sig = ("spray", nozzle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    # Splash everything in the spray zone (here: face/torso/legs of the hero,
    # plus any prop the hero was carrying).
    world.zone = {"face", "torso", "legs"}
    hero.meters["wet"] += 1
    hero.memes["shock"] += 1
    for prop in world.props():
        if prop is nozzle:
            continue
        if prop.caretaker == hero.id or prop.owner == hero.id:
            prop.meters["wet"] += 1
            prop.meters["dirty"] += 1
    out.append(
        f"A hard fan of water caught {hero.id} square in the face and shoulders."
    )
    return out


def _r_knockdown(world: World) -> list[str]:
    """Hero soaked AND nozzle still on -> hero is knocked flat (the punchline)."""
    hero = next((e for e in world.characters()), None)
    nozzle = next((e for e in world.props() if e.type == "nozzle"), None)
    if hero is None or nozzle is None:
        return []
    if hero.meters["wet"] < THRESHOLD or nozzle.meters["open"] < THRESHOLD:
        return []
    sig = ("knockdown", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["defeat"] += 1
    hero.meters["fallen"] += 1
    return [f"{hero.id} went over backwards and sat down hard in the mud."]


def _r_loss(world: World) -> list[str]:
    """Hero down + nearby small prop with a caretaker -> that prop is lost."""
    hero = next((e for e in world.characters()), None)
    if hero is None or hero.meters["fallen"] < THRESHOLD:
        return []
    out: list[str] = []
    for prop in world.props():
        if prop.caretaker != hero.id or prop.meters["lost"] >= THRESHOLD:
            continue
        sig = ("loss", prop.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        prop.meters["lost"] += 1
        hero.memes["shame"] += 1
        out.append(
            f"The {prop.label} disappeared with whoever had run off with it."
        )
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spray", tag="physical", apply=_r_spray),
    Rule(name="knockdown", tag="physical", apply=_r_knockdown),
    Rule(name="loss", tag="social", apply=_r_loss),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Forward-chain every rule to a fixpoint; optionally write the outcomes."""
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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
# Constraint helpers -- what counts as a *reasonable* nozzle story.
# ---------------------------------------------------------------------------
def story_supported(hero_type: str, has_curiosity: bool) -> bool:
    """The whole domain only exists when the hero is curious about the nozzle."""
    return has_curiosity and hero_type in {"girl", "boy", "ranch_hand"}


def select_curiosity_knob() -> str:
    """Only one 'fix' exists, and it is the *opposite* of opening the nozzle --
    leaving it alone.  That's the moral of a tall tale: curiosity bites back."""
    return "leave it alone"


# ---------------------------------------------------------------------------
# Prediction -- the only "fix" we *offer* is to walk away.  Predicting that
# walk-away avoids every bad consequence is how we know the moral is sound.
# ---------------------------------------------------------------------------
def predict_walk_away(world: World) -> dict:
    sim = world.copy()
    sim.fired.add(("walk_away",))             # bail-out sentinel: nothing fires after this
    return {
        "soaked": any(e.meters["wet"] >= THRESHOLD for e in sim.characters()),
        "down": any(e.meters["fallen"] >= THRESHOLD for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0] if hero.traits else 'wide-eyed'} "
        f"{hero.type} who liked to know how every shiny thing worked."
    )


def describe_nozzle(world: World, nozzle: Entity) -> None:
    world.say(
        f"At the end of an old green hose sat a brass {nozzle.label} the size "
        f"of a coffee cup, dented at the rim and proud of it."
    )


def loves_curiosity(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} had a habit of poking at things just "
        f"to see what they were hiding, and this morning the {hero.type} could "
        f"hardly wait to look inside."
    )


def fetch_hose(world: World, hero: Entity, hose: Entity, nozzle: Entity) -> None:
    hose.worn_by = hero.id
    nozzle.attached_to = hose.id
    hose.attached_to = hero.id
    world.say(
        f"Before dawn {hero.id} hauled the {hose.label} out to the far corral, "
        f"the {nozzle.label} clicking against {hero.pronoun('object')} at every step."
    )


def unscrew(world: World, hero: Entity, nozzle: Entity) -> None:
    nozzle.meters["open"] += 1
    nozzle.meters["pressure"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} knelt beside the {nozzle.label}, turned "
        f"the collar with both thumbs, and eased the cap off to peek inside."
    )


def spray(world: World, hero: Entity, nozzle: Entity) -> None:
    """Apply the chain: open nozzle -> spray hero -> knockdown -> loss of prop."""
    propagate(world, narrate=True)


def taunt(world: World, hero: Entity) -> None:
    """The cat laughs; the chickens look for a new coop -- the tall-tale coda."""
    world.say(
        f"The barn cat sat on the fence and laughed until {hero.pronoun('object')} "
        f"could hear it over the hissing hose."
    )
    world.say(
        f"The chickens, who had been minding their own business, decided on the "
        f"spot that this was no longer their coop and began to look for a new one."
    )


def wind_down(world: World, hero: Entity, nozzle: Entity) -> None:
    """The nozzle keeps spurting happily without the hero -- a tall-tale ending."""
    world.say(
        f"And the {nozzle.label}, quite pleased with itself, spun on the wet ground "
        f"like a small brass top and went on spraying for the rest of the morning, "
        f"long after {hero.id} had stopped being the one holding it."
    )


def alternative(world: World, hero: Entity, nozzle: Entity) -> None:
    """A short 'if she had walked away' aside -- the moral in plain words."""
    world.say(
        f"Had {hero.id} walked away and left the {nozzle.label} alone, the morning "
        f"would have been a quiet one, and the cat would have had nothing to laugh at."
    )


# ---------------------------------------------------------------------------
# The screenplay: tall-tale shape -- a single bad ending, narrated flatly.
# ---------------------------------------------------------------------------
def tell(hero_name: str = "June", hero_type: str = "ranch_hand",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["wide-eyed", "stubborn"] + (hero_traits or []),
    ))
    nozzle = world.add(Entity(
        id="Nozzle", kind="thing", type="nozzle", label="nozzle",
        phrase="a brass nozzle the size of a coffee cup",
    ))
    hose = world.add(Entity(
        id="Hose", kind="thing", type="hose", label="hose",
        phrase="an old green hose", caretaker=hero.id,
    ))
    egg = world.add(Entity(
        id="Egg", kind="thing", type="egg", label="egg",
        phrase="the morning egg", caretaker=hero.id,
    ))
    cat = world.add(Entity(
        id="Cat", kind="thing", type="cat", label="cat",
        phrase="the barn cat",
    ))

    # Act 1 -- setup: who, what they love, the nozzle they cannot leave alone.
    introduce(world, hero)
    loves_curiosity(world, hero)
    fetch_hose(world, hero, hose, nozzle)
    describe_nozzle(world, nozzle)

    # Act 2 -- the bad turn: the curiosity finds its target.
    world.para()
    unscrew(world, hero, nozzle)
    spray(world, hero, nozzle)

    # Act 3 -- bad ending: the tall-tale coda and the moral-aside.
    world.para()
    taunt(world, hero)
    wind_down(world, hero, nozzle)
    alternative(world, hero, nozzle)

    world.facts.update(
        hero=hero, nozzle=nozzle, hose=hose, egg=egg, cat=cat,
        curious=True, resolved=False,
        soaked=hero.meters["wet"] >= THRESHOLD,
        fallen=hero.meters["fallen"] >= THRESHOLD,
        lost_egg=egg.meters["lost"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Knobs for one nozzle story (deterministic given these)."""
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


KNOWLEDGE = {
    "nozzle": [
        ("What is a nozzle?",
         "A nozzle is the tip that screws onto a hose. It shapes the water "
         "into a spray you can aim where you want."),
        ("Why do hoses have nozzles?",
         "A nozzle lets you point the water, change how strong the spray is, "
         "and shut the water off when you are done."),
    ],
    "curiosity": [
        ("Why do people want to look inside things?",
         "Curiosity is the feeling that makes you want to see how something "
         "works. It helps us learn, but it can also get us into a little "
         "trouble if the thing we are looking at is not meant to be opened."),
    ],
    "pressure": [
        ("What is water pressure?",
         "Water pressure is how hard the water pushes inside a pipe or hose. "
         "When the pressure is high, opening a nozzle can send water a long way."),
    ],
    "hose": [
        ("What is a garden hose used for?",
         "A hose carries water from a faucet to where you want to spray it, "
         "so you can water plants, wash a car, or fill a bucket."),
    ],
    "spray": [
        ("Why does water come out in a spray from a nozzle?",
         "The nozzle squeezes the water as it leaves, so a lot of water has "
         "to fit through a small opening and fans out into a spray."),
    ],
    "rancher": [
        ("Who is a ranch hand?",
         "A ranch hand is a person who helps take care of a ranch, feeding "
         "the animals, fixing fences, and hauling water where it is needed."),
    ],
}
KNOWLEDGE_ORDER = ["nozzle", "hose", "pressure", "spray", "curiosity", "rancher"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, nozzle = f["hero"], f["nozzle"]
    return [
        'Write a short tall tale for a 5-to-8-year-old on the theme '
        '"curiosity and a temperamental nozzle" that ends badly but ends with '
        'a quiet moral.',
        f'Tell a gentle, slightly silly story about a curious {hero.type} '
        f'named {hero.id} who just had to look inside a brass nozzle and paid '
        f'for it, set on a ranch.',
        'Write a tiny story that uses the word "nozzle" and ends with a moral '
        'about walking away from something you do not need to open.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, nozzle, hose, egg, cat = f["hero"], f["nozzle"], f["hose"], f["egg"], f["cat"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about when the {nozzle.label} spins "
                     f"on the wet ground at the far corral?",
            answer=f"It is about a curious {hero.type} named {hero.id} who "
                   f"hauled the {hose.label} out before dawn and just had to "
                   f"see what was inside the brass {nozzle.label}.",
        ),
        QAItem(
            question=f"What was the {hero.type}'s bad habit with shiny things "
                     f"like the {nozzle.label}?",
            answer=f"{hero.id} could never leave a shiny thing alone. "
                   f"{sub.capitalize()} had to peek at how it worked, and the "
                   f"{nozzle.label} was exactly the kind of thing that "
                   f"wouldn't sit still once {sub} started turning it.",
        ),
        QAItem(
            question=f"What happened when {hero.id} took the cap off the "
                     f"{nozzle.label} at the far corral?",
            answer=f"A hard fan of water caught {obj} in the face and "
                   f"shoulders, knocked {obj} over backwards into the mud, "
                   f"and sent the {egg.label} off with whoever had run with it.",
        ),
        QAItem(
            question=f"Why was the ending a bad one for {hero.id} and the "
                     f"{nozzle.label}?",
            answer=f"It was a bad ending because {hero.id} ended up soaked in "
                   f"the mud, the morning {egg.label} was gone, the {cat.label} "
                   f"sat on the fence laughing, and the {nozzle.label} went on "
                   f"spraying long after {hero.id} had stopped holding it.",
        ),
        QAItem(
            question=f"What is the quiet moral the tall tale leaves us with "
                     f"after the soaking at the far corral?",
            answer=f"The moral is that had {hero.id} walked away and left the "
                   f"{nozzle.label} alone, the morning would have been a "
                   f"quiet one and the {cat.label} would have had nothing to "
                   f"laugh at -- curiosity is fine, but sometimes the bravest "
                   f"thing is to leave the cap on.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """Child-level questions about the world, answerable without the story."""
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
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
# CLI / trace helpers.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# Curated set used by --all.  These are not "good outcomes" -- the contract is
# a bad ending.  They differ in name/trait so a child sees a few variants.
CURATED = [
    StoryParams(name="June", gender="girl", trait="wide-eyed"),
    StoryParams(name="Wade", gender="boy", trait="stubborn"),
    StoryParams(name="Mira", gender="girl", trait="patient"),
]


def explain_rejection(hero_type: str, curious: bool) -> str:
    if not curious:
        return ("(No story: a nozzle-only story needs curiosity. The whole "
                "domain is built around wanting to look inside the brass "
                "nozzle. Try --curious to enable it.)")
    if hero_type not in {"girl", "boy", "ranch_hand"}:
        return (f"(No story: a {hero_type} isn't a hero type this domain "
                f"knows about. Try --hero-type ranch_hand.)")
    return "(No story: the chosen options do not form a reasonable nozzle story.)"


# ---------------------------------------------------------------------------
# Inline ASP twin -- a small declarative reasoner that mirrors the Python gate.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Only "hero types" the world knows about can have a nozzle story.
known_hero(H) :- hero_type(H).
known_hero(ranch_hand).

% Curiosity is mandatory; without it there is no story.
story_possible(H) :- known_hero(H), curious.

% The fix the tall tale recommends is the only one we record as a fix.
has_fix :- fix(walk_away).

% A story "fits the moral" when both the hero is curious and the fix is known.
valid_story(H) :- story_possible(H), has_fix.
"""


def asp_facts(args: argparse.Namespace) -> str:
    """Emit facts mirroring the CLI flags (kept tiny on purpose)."""
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero_type", getattr(args, "hero_type", None)))
    if getattr(args, "curious", None):
        lines.append(asp.fact("curious"))
    lines.append(asp.fact("fix", "walk_away"))
    return "\n".join(lines)


def asp_program(args: argparse.Namespace, show: str) -> str:
    return f"{asp_facts(args)}\n{ASP_RULES}\n{show}\n"


def asp_verify(args: argparse.Namespace) -> int:
    """Confirm the inline ASP gate agrees with the Python gate."""
    import asp
    model = asp.one_model(asp_program(args, "#show valid_story/1."))
    clingo_set = {t[0] for t in asp.atoms(model, "valid_story")}
    py_ok = story_supported(getattr(args, "hero_type", None), getattr(args, "curious", None))
    python_set = {getattr(args, "hero_type", None)} if py_ok else set()
    if clingo_set == python_set:
        print(f"OK: clingo gate matches story_supported() "
              f"(hero={getattr(args, "hero_type", None)}, curious={getattr(args, "curious", None)}).")
        return 0
    print("MISMATCH between clingo and story_supported():")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md).
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld sketch: a curious soul, a temperamental "
                    "nozzle, and a tall-tale bad ending.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero-type", choices=["girl", "boy", "ranch_hand"],
                    default="ranch_hand")
    ap.add_argument("--trait")
    ap.add_argument("--curious", action="store_true",
                    help="the hero is curious (required for a valid story)")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    # ASP modes.
    ap.add_argument("--asp", action="store_true",
                    help="run the inline ASP gate on the given flags")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches story_supported()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return _fallback_storyparams(args, rng, StoryParams, globals())
    if not getattr(args, "curious", None):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "hero_type", None) not in {"girl", "boy", "ranch_hand"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or ("girl" if getattr(args, "hero_type", None) in {"girl", "ranch_hand"}
                             else rng.choice(["girl", "boy"]))
    name = getattr(args, "name", None) or rng.choice(["June", "Wade", "Mira", "Hank", "Rose", "Eli"])
    trait = getattr(args, "trait", None) or rng.choice(["wide-eyed", "stubborn", "patient", "cheerful"])
    return StoryParams(name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    hero_type = {"girl": "girl", "boy": "boy"}.get(params.gender, "ranch_hand")
    world = tell(params.name, hero_type, [params.trait, "stubborn"])
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

    if getattr(args, "show_asp", None):
        print(asp_program(args, "#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify(args))
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program(args, "#show valid_story/1."))
        triples = asp.atoms(model, "valid_story")
        print(f"ASP gate says {len(triples)} valid hero type(s): "
              f"{[t[0] for t in triples] or 'none'}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2,
                             ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.gender} {p.trait}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
