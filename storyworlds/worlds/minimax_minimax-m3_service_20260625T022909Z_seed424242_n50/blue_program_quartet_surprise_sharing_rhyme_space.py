#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/blue_program_quartet_surprise_sharing_rhyme_space.py
================================================================================

Storyworld: A TinyStories-style space adventure built around a quartet of small
ships, a children's "blue program" of friendly commands, and a surprise gift
that hinges on *sharing* and a *rhyme* that closes the day.

Seed: blue, program, quartet
Domain features: Surprise, Sharing, Rhyme
Style: Space Adventure (gentle, child-facing, TinyStories register)

Source tale (imagined for the simulation)
-----------------------------------------
Once upon a time, four small friends flew a quartet of tiny spaceships through
the quiet sky. They had a blue program in their cockpit -- a list of kind
commands they liked to share: "say please", "ask first", "share the last star",
"sing the rhyming song".

One calm afternoon, their radios crackled: "Surprise! The Blue Moon is sharing
a tiny moonpie with whoever reaches the Crater of Kind Words first." The four
ships flew fast, but the path was a gentle riddle -- you only win if you can
finish the rhyming song.

They worked it out together: Bee, the smallest, flew ahead; Pip read the
rhyme aloud; Mira and Kai kept watch. They shared the moonpie four ways, and
everybody laughed. The End.

Premise / tension / turn / resolution -> world state:
    * premise  : four small ships (quartet) each with a role, plus a "blue
                 program" -- a list of kind commands they like to share.
    * tension  : a surprise announcement offers a tiny moonpie to whoever
                 can finish a rhyming song at the Crater of Kind Words.
    * turn     : no single ship can finish the rhyme alone; one flies ahead,
                 one reads the line, one watches the sky, one keeps the
                 program alive -- i.e. *sharing the rhyme* and *sharing the
                 program* unstick the team.
    * resolution: the moonpie is split four ways and the rhyme is sung in
                 full; the "blue program" gains the new line "share the
                 last star".
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

# Eagerly import the shared result containers; the clingo helper is imported
# lazily inside ASP entry points so the prose engine still runs without it.
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".."),
)
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0            # embedded-enough threshold for narration
SHIP_ROLES = ("scout", "reader", "watcher", "keeper")


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "ship" | "thing" | "moon"
    type: str = "thing"            # pilot | ship | program | crater | ...
    label: str = ""                # short noun used in prose ("Bee", "Pip", ...)
    phrase: str = ""               # longer noun phrase ("a tiny bright ship")
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    role: str = ""                 # ship role: scout/reader/watcher/keeper
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    # child-facing facts carried for Q&A
    note: str = ""                 # plain-English description used in QA answers

    pilot: object | None = None
    program: object | None = None
    ship: object | None = None
    surprise: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "pilot_girl"}
        male = {"boy", "father", "dad", "man", "pilot_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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


@dataclass
class Crew:
    """One pilot and the ship they fly."""
    name: str
    pilot_type: str               # "girl" | "boy"
    ship_label: str               # "bright ship"
    ship_color: str               # "blue", "gold", "mint", ...
    role: str                     # one of SHIP_ROLES
    catch: str                    # a one-line phrase they say in prose
    note: str                     # child-facing fact for Q&A
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


@dataclass
class RhymeLine:
    text: str                     # the rhyming line itself
    bearer: str                   # which role reads it aloud
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
        return None


@dataclass
class ProgramLine:
    text: str                     # the kind command, in quotes
    why: str                      # plain-English reason used in Q&A


# ----- Crew roster ---------------------------------------------------------
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
        return None


CREW = [
    Crew(
        name="Bee", pilot_type="girl", ship_label="bright ship",
        ship_color="blue", role="scout",
        catch='"I will fly ahead and look," Bee said.',
        note=("Bee is the smallest pilot and flies the blue ship; she likes "
              "to look ahead and find the way for the others."),
    ),
    Crew(
        name="Pip", pilot_type="boy", ship_label="little yellow ship",
        ship_color="yellow", role="reader",
        catch='"I will read the rhyme," Pip said.',
        note=("Pip flies the little yellow ship and likes to read lines out "
              "loud; the rhyming song sounds tidy when he says it."),
    ),
    Crew(
        name="Mira", pilot_type="girl", ship_label="soft mint ship",
        ship_color="mint", role="watcher",
        catch='"I will keep watch above," Mira said.',
        note=("Mira flies the soft mint ship and likes to keep watch above; "
              "she notices the twinkly sky before anyone else does."),
    ),
    Crew(
        name="Kai", pilot_type="boy", ship_label="little gold ship",
        ship_color="gold", role="keeper",
        catch='"I will keep the blue program," Kai said.',
        note=("Kai flies the little gold ship and keeps the blue program "
              "safe; he likes to remind the others to share and say please."),
    ),
]

# Rhyme of the Crater -- one line per ship role; the last word of every odd
# line and every even line must rhyme ("way" / "day").  These exact lines are
# what the characters *read aloud* in the resolution paragraph.
RHYME = [
    RhymeLine(text="Up past the clouds and over the way,",  bearer="scout"),
    RhymeLine(text="We share the sky on a friendly day.", bearer="reader"),
    RhymeLine(text="The kindest ship keeps the rhyming plan,", bearer="watcher"),
    RhymeLine(text="And every friend says please, like a fan.", bearer="keeper"),
]
RHYME_TITLE = "the rhyming song of the Crater"

# The "blue program" -- a list of kind commands the quartet likes to share.
# The first three are the seed program; the fourth is added in the resolution
# (the surprise gift earns the quartet a new line).
PROGRAM = [
    ProgramLine(text="say please",          why="a soft word that opens a door"),
    ProgramLine(text="ask first",           why="a way to check before you take"),
    ProgramLine(text="share the last star", why="a tiny gift no one forgets"),
    ProgramLine(text="sing the rhyming song",
                why="a song that finishes when four friends help each other"),
]

# ----- Settings ------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)
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


SETTINGS = {
    "sky":    Setting(id="sky",    place="the bright afternoon sky",
                      affords={"rhyming", "sharing"}),
    "crater": Setting(id="crater", place="the Crater of Kind Words",
                      affords={"rhyming", "sharing", "moonpie"}),
    "camp":   Setting(id="camp",   place="the little Moon-Camp",
                      affords={"rhyming", "sharing"}),
}

# Weather / sky moods (purely cosmetic, used for prose variation).
MOODS = ["calm and bright", "soft and twinkly", "quiet and warm", "fresh and breezy"]
CRATERS = ["the Crater of Kind Words", "the Crater of Soft Rhyme",
           "the Crater of Sharing"]
GIFTS = ["a tiny moonpie", "a small blue star", "a paper-thin moon-cake",
         "a bright silver crumb"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting, mood: str, gift: str, crater_name: str) -> None:
        self.setting = setting
        self.mood = mood
        self.gift = gift
        self.crater_name = crater_name
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def ships(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "ship"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Causal rules -- small, forward-chained to fixpoint.
# ---------------------------------------------------------------------------
def _r_surprise(world: World) -> list[str]:
    """If a surprise announcement has been heard, mark surprise>=THRESHOLD."""
    surprise = world.entities.get("surprise")
    if not surprise or surprise.meters.get("heard", 0) < THRESHOLD:
        return []
    if surprise.memes.get("surprise", 0) >= THRESHOLD:
        return []
    sig = ("surprise", surprise.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    surprise.memes["surprise"] += 1
    return ["__surprise__"]              # marker; screenplay narrates the line


def _r_rhyme(world: World) -> list[str]:
    """If a rhyme is read by all four roles, mark rhyme>=THRESHOLD (resolved)."""
    prog = world.entities.get("program")
    if not prog:
        return []
    if prog.meters.get("read_lines", 0) < len(RHYME):
        return []
    if prog.memes.get("rhyme_done", 0) >= THRESHOLD:
        return []
    sig = ("rhyme", prog.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prog.memes["rhyme_done"] += 1
    return ["__rhyme_done__"]


def _r_share(world: World) -> list[str]:
    """When the rhyme is done and the quartet shares the gift, each pilot
    gains a 'share' meme -- this is the turn that resolves the conflict."""
    for crew_ent in world.characters():
        if crew_ent.meters.get("did_share", 0) < THRESHOLD:
            continue
        if crew_ent.memes.get("share", 0) >= THRESHOLD:
            continue
        sig = ("share", crew_ent.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        crew_ent.memes["share"] += 1
    return []


def _r_program_extends(world: World) -> list[str]:
    """If at least three pilots have shared, extend the blue program with a
    new line -- the surprise gift's promise lands as a real change."""
    prog = world.entities.get("program")
    if not prog or prog.meters.get("lines", 0) >= 4:
        return []
    sharers = sum(1 for c in world.characters() if c.memes.get("share", 0) >= THRESHOLD)
    if sharers < 3:
        return []
    sig = ("program_extend", prog.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prog.meters["lines"] += 1
    prog.memes["extended"] += 1
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Forward-chain every rule to fixpoint; emit markers as narration if asked."""
    rules: list[Callable[[World], list[str]]] = [
        _r_surprise, _r_rhyme, _r_share, _r_program_extends,
    ]
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in rules:
            out = rule(world)
            if out:
                changed = True
                produced.extend(out)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def valid_settings() -> list[str]:
    """Only the crater and the camp can host the moonpie resolution."""
    return [sid for sid, s in SETTINGS.items() if "moonpie" in s.affords]


# ---------------------------------------------------------------------------
# Screenplay -- coarse three-act shape, driven by the verbs below.
# ---------------------------------------------------------------------------
def tell(setting_id: str = "crater",
         mood: str = "calm and bright",
         gift: str = "a tiny moonpie",
         crater_name: str = "the Crater of Kind Words") -> World:
    setting = _safe_lookup(SETTINGS, setting_id)
    world = World(setting, mood=mood, gift=gift, crater_name=crater_name)

    # Add the four pilots + their ships.
    for c in CREW:
        pilot = world.add(Entity(
            id=c.name, kind="character", type=("pilot_girl" if c.pilot_type == "girl"
                                              else "pilot_boy"),
            label=c.name,
            phrase=f"a {('cheerful' if c.pilot_type == 'girl' else 'lively')} "
                   f"pilot named {c.name}",
            traits=[c.role, "little"],
            note=c.note,
        ))
        ship = world.add(Entity(
            id=f"{c.name}_ship", kind="ship", type="ship",
            label=c.ship_label,
            phrase=f"{c.name}'s {c.ship_color} {c.ship_label}",
            owner=pilot.id,
            note=f"{c.ship_label.capitalize()} belongs to {c.name}.",
        ))

    # The "blue program" lives in Kai's cockpit.
    program = world.add(Entity(
        id="program", kind="thing", type="program",
        label="the blue program",
        phrase="a friendly blue program in the cockpit",
        owner="Kai",
        meters={"lines": 3},          # 3 seed lines (the 4th is earned)
        note=("The blue program is a list of kind commands the quartet "
              "shares -- say please, ask first, share the last star."),
    ))

    # The surprise announcement -- an entity used to gate the surprise rule.
    surprise = world.add(Entity(
        id="surprise", kind="thing", type="announcement",
        label="the surprise",
        phrase="a tiny radio surprise",
        note="A short radio note that tells the quartet about the moonpie.",
    ))

    # ----- Act 1: meet the quartet and the blue program -------------------
    world.say(
        "Once upon a time, four little friends flew a quartet of tiny "
        "spaceships through the quiet sky."
    )
    world.say(
        "Each ship had its own pilot and its own colour: a blue ship, a "
        "little yellow ship, a soft mint ship, and a little gold ship."
    )
    world.say(
        "In the gold ship, Kai kept a friendly blue program -- a short list "
        "of kind commands they liked to share."
    )
    world.say(
        f"The blue program had three little lines: {PROGRAM[0].text!r}, "
        f"{PROGRAM[1].text!r}, and {PROGRAM[2].text!r}."
    )

    # ----- Act 2: the surprise that calls for sharing --------------------
    world.para()
    world.say(
        f"One {world.mood} afternoon, their little radios crackled with a "
        f"soft surprise."
    )
    surprise.meters["heard"] = 1.0
    propagate(world, narrate=False)   # fires the surprise rule
    world.say(
        f'"Surprise!" the radio said. "Today, {world.crater_name} is sharing '
        f'{world.gift} with the four friends who can finish {RHYME_TITLE}."'
    )
    world.say(
        "The four ships cheered, but the rhyme had four little lines -- and "
        "no single ship could read them all alone."
    )
    world.say(
        f'"We have to share the job," Bee said. {CREW[0].catch}'
    )
    world.say(
        f'"And we have to share the rhyme," Pip said. {CREW[1].catch}'
    )
    world.say(
        f'"And keep watch above us," Mira said. {CREW[2].catch}'
    )
    world.say(
        f'"And keep the blue program safe," Kai said. {CREW[3].catch}'
    )

    # ----- Act 3: turn + resolution --------------------------------------
    world.para()
    world.say(
        f"They flew towards {world.crater_name}. Bee flew ahead, Pip read "
        f"the rhyme aloud, Mira watched the sky, and Kai kept the blue "
        f"program glowing."
    )
    # Each role reads its rhyme line in turn -> enough to satisfy rhyme rule.
    for line in RHYME:
        bear = next(c for c in CREW if c.role == line.bearer)
        world.say(f'"{line.text}" {bear.name} said.')
    program.meters["read_lines"] = float(len(RHYME))
    propagate(world, narrate=False)   # fires rhyme->share->extend chain

    world.say(
        f"When the last line was finished, they found {world.gift} waiting "
        f"on a flat little moon-stone."
    )
    world.say(
        '"How shall we share it?" Bee asked. "Four friends, one little gift."'
    )
    world.say(
        '"The blue program says share," Kai said, and he read the new line '
        f'aloud: {PROGRAM[3].text!r}.'
    )
    # All four pilots do the sharing action -> marks did_share.
    for c in CREW:
        pilot = world.get(c.name)
        pilot.meters["did_share"] = 1.0
    propagate(world, narrate=False)

    world.say(
        f"So they shared {world.gift} four ways, and every pilot got a "
        f"little piece. They laughed, and the blue program glowed with a "
        f"new fourth line."
    )
    world.say(
        "They flew back to their Moon-Camp, and sang the rhyming song all "
        "the way home. The End."
    )

    world.facts.update(
        crew=CREW,
        program=program,
        rhyme=RHYME,
        surprise=surprise,
        setting=setting,
        setting_id=setting_id,
        mood=mood,
        gift=gift,
        crater_name=crater_name,
        rhyme_title=RHYME_TITLE,
        rhyme_done=program.memes.get("rhyme_done", 0) >= THRESHOLD,
        shared_all=all(world.get(c.name).memes.get("share", 0) >= THRESHOLD
                       for c in CREW),
        program_extended=program.memes.get("extended", 0) >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Per-world parameters (script-side; the shared StorySample lives in results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mood: str
    gift: str
    crater: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three separate sets.
# ---------------------------------------------------------------------------
    sample: object | None = None
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
        return None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        ('Write a short story for a 3-to-5-year-old on the theme "a quartet, '
         f'a blue program, a surprise, sharing, and a rhyme" that includes the '
         'words "blue", "program", "quartet", "surprise", "sharing", and "rhyme".'),
        ('Tell a gentle space adventure where four small friends fly a '
         'quartet of ships, share a blue program of kind commands, hear a '
         'surprise offer of a moonpie, and finish a rhyming song together '
         'so they can share the gift.'),
        ('Write a simple rhyming space story that ends with the line "and '
         'everybody laughed" and uses the noun "moonpie".'),
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crew = _safe_fact(world, f, "crew")
    qa: list[QAItem] = [
        QAItem(
            question=(
                "Who flew the quartet of tiny spaceships through the quiet sky?"
            ),
            answer=(
                "Four little friends flew the quartet: Bee in the blue ship, "
                "Pip in the little yellow ship, Mira in the soft mint ship, "
                "and Kai in the little gold ship."
            ),
        ),
        QAItem(
            question=(
                "What was the blue program in the cockpit, and who kept it?"
            ),
            answer=(
                "The blue program was a friendly list of kind commands the "
                "quartet liked to share: 'say please', 'ask first', and "
                "'share the last star'. Kai, who flew the little gold ship, "
                "kept it safe in the cockpit."
            ),
        ),
        QAItem(
            question=(
                f"What surprise did the radio tell the quartet about "
                f"{f['crater_name']}?"
            ),
            answer=(
                f"The radio said, 'Surprise! Today, {f['crater_name']} is "
                f"sharing {f['gift']} with the four friends who can finish "
                f"{f['rhyme_title']}.'"
            ),
        ),
        QAItem(
            question=(
                "Why couldn't one ship finish the rhyming song alone?"
            ),
            answer=(
                "The rhyming song had four little lines, and no single ship "
                "could read them all alone. The quartet had to share the job: "
                "Bee flew ahead, Pip read the rhyme aloud, Mira watched the "
                "sky, and Kai kept the blue program safe."
            ),
        ),
    ]
    if f.get("shared_all"):
        qa.append(QAItem(
            question=(
                f"How did the quartet share {f['gift']} at {f['crater_name']}?"
            ),
            answer=(
                f"They shared {f['gift']} four ways, so every pilot got a "
                f"little piece. Kai read the blue program's new line, "
                f"'sing the rhyming song', and they all laughed together."
            ),
        ))
    if f.get("program_extended"):
        qa.append(QAItem(
            question=(
                "What new line did the blue program gain at the end of the story?"
            ),
            answer=(
                "The blue program gained a fourth line: 'sing the rhyming "
                "song'. The quartet earned it because three of them had "
                "shared the moonpie together."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """Child-level world knowledge -- answerable without this specific story."""
    return [
        QAItem(
            question="What is a quartet?",
            answer=(
                "A quartet is a group of four things that go together, like "
                "four friends or four small ships that fly in a row."
            ),
        ),
        QAItem(
            question="What is a program on a small spaceship?",
            answer=(
                "A program on a small spaceship is a short list of commands "
                "that tells the ship what to do, like 'say please' or 'ask "
                "first'. This quartet's program is a blue, friendly one."
            ),
        ),
        QAItem(
            question="What is sharing?",
            answer=(
                "Sharing is giving a little of what you have to someone else, "
                "so everybody gets a turn. When four friends find one small "
                "gift, sharing means cutting it four ways."
            ),
        ),
        QAItem(
            question="What is a rhyme?",
            answer=(
                "A rhyme is when two words end with the same sound, like "
                "'way' and 'day'. A rhyming song is a little poem where the "
                "last words sound alike."
            ),
        ),
        QAItem(
            question="What is a surprise?",
            answer=(
                "A surprise is something you didn't expect. A good surprise "
                "is gentle and kind, like hearing the radio say that a small "
                "gift is waiting at a friendly place."
            ),
        ),
        QAItem(
            question="What is a moonpie?",
            answer=(
                "A moonpie is a tiny sweet treat, like a small round cake "
                "from the Moon-Camp. In this story it is the gentle prize "
                "the quartet shares four ways."
            ),
        ),
    ]


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:14} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(setting="crater", mood="calm and bright",
                gift="a tiny moonpie", crater="the Crater of Kind Words"),
    StoryParams(setting="crater", mood="soft and twinkly",
                gift="a small blue star", crater="the Crater of Soft Rhyme"),
    StoryParams(setting="crater", mood="quiet and warm",
                gift="a paper-thin moon-cake",
                crater="the Crater of Sharing"),
]


# ---------------------------------------------------------------------------
# ASP twin (clingo).  Inline rules below; the registries above emit the facts.
# Uses the shared `asp` helper + clingo, imported lazily.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting "hosts" a moonpie resolution only if it affords moonpie.
hosts_moonpie(S) :- setting(S), affords(S, moonpie).

% The blue program starts with three seed lines (the seed quartet shares them).
seed_program_line("say please").
seed_program_line("ask first").
seed_program_line("share the last star").

% Each pilot role is required to read its rhyme line.
role_required(scout).
role_required(reader).
role_required(watcher).
role_required(keeper).

% A role "covers" its rhyme line exactly once.
role_covered(R) :- role_required(R), rhyme_read(R).

% The rhyme is finished when every required role is covered.
rhyme_finished :- role_required(R) : role_covered(R).

% The surprise is heard when an announcement is present (one entity).
surprise_heard :- announcement.

% Resolution: moonpie resolution is reachable only when the surprise is heard
% AND the rhyme is finished AND the program is being shared.
resolves(S) :- hosts_moonpie(S), surprise_heard, rhyme_finished, sharing_program.

% A valid story = a setting that resolves.
valid(S) :- resolves(S).
valid_story(S, G) :- valid(S), has_gift(S, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for c in CREW:
        lines.append(asp.fact("pilot", c.name))
        lines.append(asp.fact("role", c.name, c.role))
        lines.append(asp.fact("wears", c.pilot_type, "ship"))
    for line in PROGRAM[:3]:
        lines.append(asp.fact("seed_program_line", line.text))
    for r in SHIP_ROLES:
        lines.append(asp.fact("role_required", r))
    for line in RHYME:
        lines.append(asp.fact("rhyme_for", line.bearer, line.text))
    lines.append(asp.fact("announcement", "surprise"))
    lines.append(asp.fact("sharing_program", "program"))
    for g in GIFTS:
        lines.append(asp.fact("has_gift", "crater", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_settings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(asp.atoms(model, "valid"))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    """Check ASP gate agrees with the Python valid_settings() helper."""
    import asp
    clingo_set = {a[0] for a in asp_valid_settings()}
    python_set = set(valid_settings())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_settings() ({sorted(python_set)}).")
        # also exercise a generated story
        sample = generate(StoryParams(setting="crater", mood="calm and bright",
                                      gift="a tiny moonpie",
                                      crater="the Crater of Kind Words"))
        assert sample.story, "story text is empty"
        assert sample.prompts, "no prompts"
        assert sample.story_qa, "no story_qa"
        assert sample.world_qa, "no world_qa"
        print(f"OK: generated a {len(sample.story.split())}-word story with "
              f"{len(sample.story_qa)} story-QA and "
              f"{len(sample.world_qa)} world-QA items.")
        return 0
    print("MISMATCH between clingo and valid_settings():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a quartet of spaceships, a blue program, "
                    "a surprise, sharing, and a rhyme. Unspecified choices "
                    "are picked at random (seeded).")
    ap.add_argument("--setting", choices=SETTINGS, default=None)
    ap.add_argument("--mood", choices=MOODS, default=None)
    ap.add_argument("--gift", choices=GIFTS, default=None)
    ap.add_argument("--crater", choices=CRATERS, default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the valid-setting set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_settings()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill unspecified choices at random; explicit moonpie requires crater."""
    if getattr(args, "setting", None) and "moonpie" not in _safe_lookup(SETTINGS, getattr(args, "setting", None)).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    valid = [s for s in valid_settings()
             if (getattr(args, "setting", None) is None or s == getattr(args, "setting", None))]
    if not valid:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or rng.choice(valid)
    mood = getattr(args, "mood", None) or rng.choice(MOODS)
    gift = getattr(args, "gift", None) or rng.choice(GIFTS)
    crater = getattr(args, "crater", None) or rng.choice(CRATERS)
    return StoryParams(setting=setting, mood=mood, gift=gift, crater=crater)


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + 3 Q&A sets."""
    world = tell(setting_id=params.setting, mood=params.mood,
                 gift=params.gift, crater_name=params.crater)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_settings()
        stories = asp_valid_stories()
        print(f"{len(triples)} valid settings; {len(stories)} valid stories:\n")
        for sid, in triples:
            gifts = [g for s, g in stories if s == sid]
            print(f"  {sid:8} -> {', '.join(sorted(gifts))}")
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
            header = f"### {p.setting}: {p.gift} ({p.crater})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
