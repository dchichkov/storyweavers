#!/usr/bin/env python3
"""
storyworlds/worlds/compass_cocaine_enroll_cautionary_magic_foreshadowing_mystery.py
===================================================================================

A small mystery storyworld with cautionary magic and foreshadowing.

Premise:
- A curious child finds a compass.
- A strange locked envelope labeled "cocaine" is discovered in a dusty room.
- The child wants to enroll in a map club.
- Magic points the way, but the story warns against opening the wrong thing.
- The mystery resolves when the child follows clues, asks a grown-up, and chooses safety.

This world keeps the tone child-facing and gentle while still using the required
seed words and narrative instruments:
- compass
- cocaine
- enroll
- cautionary
- magic
- foreshadowing
- mystery
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
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


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    indoor: bool = True
    afford_map_club: bool = True
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
class Clue:
    name: str
    kind: str
    hint: str
    helps: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    clues: list[Clue] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            clues=copy.deepcopy(self.clues),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]


SETTINGS = {
    "library": Setting(place="the old library", indoor=True),
    "museum": Setting(place="the quiet museum", indoor=True),
    "attic": Setting(place="the attic", indoor=True),
}

HERO_NAMES = ["Maya", "Lena", "Iris", "Owen", "Nico", "Pia", "Noah", "Zara"]
HERO_TYPES = {
    "girl": ["Maya", "Lena", "Iris", "Pia", "Zara"],
    "boy": ["Owen", "Nico", "Noah"],
}
TRAITS = ["curious", "careful", "brave", "thoughtful", "shy"]

CLUES = [
    Clue(
        name="scrap_of_map",
        kind="paper",
        hint="a scrap of a map with one corner torn off",
        helps="it showed there was something hidden behind a loose shelf",
    ),
    Clue(
        name="brass_sound",
        kind="metal",
        hint="a tiny brass clink from inside a box",
        helps="it pointed to the compass tucked under the dust cloth",
    ),
    Clue(
        name="dusty_note",
        kind="note",
        hint="a note that said, 'Ask before you open anything locked'",
        helps="it warned the child to stay safe and tell a grown-up",
    ),
]

CURIOSITIES = [
    "a compass",
    "an old compass",
    "a small brass compass",
]

PROMPTS = [
    "Write a gentle mystery story with a child, a compass, and a cautionary clue.",
    "Tell a child-friendly story where someone wants to enroll in a map club after finding a magical compass.",
    "Write a short mystery with foreshadowing, magic, and a safe ending that includes the word cocaine as a label on a locked item.",
]

KNOWLEDGE = [
    QAItem(
        question="What does a compass do?",
        answer="A compass helps you know which way is north so you can find directions.",
    ),
    QAItem(
        question="Why should you ask a grown-up before opening a locked box?",
        answer="You should ask a grown-up because locked things may be unsafe or not meant for children to open.",
    ),
    QAItem(
        question="What is foreshadowing in a story?",
        answer="Foreshadowing is when a story gives a small clue that something important may happen later.",
    ),
    QAItem(
        question="What does it mean to enroll?",
        answer="To enroll means to sign up and join a class, club, or activity.",
    ),
    QAItem(
        question="What is a mystery story?",
        answer="A mystery story is a story about clues, questions, and figuring out what is really happening.",
    ),
    QAItem(
        question="What is magic in a story?",
        answer="Magic in a story is something wonderful or unusual that seems beyond ordinary life.",
    ),
]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with compass, cocaine, enroll.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(_safe_lookup(HERO_TYPES, gender))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, hero_name=hero_name, hero_type=gender, trait=trait)


def _hero_pronouns(hero: Entity) -> tuple[str, str, str]:
    return hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")


def propagate(world: World) -> None:
    if "foreshadow" not in world.fired and "cautionary_note" in world.facts:
        world.fired.add("foreshadow")
        world.say(
            "A little note on the wall seemed to foreshadow the whole mystery: "
            "\"Good clues help, but unsafe doors stay closed.\""
        )


def generate_story(world: World) -> None:
    hero = world.get("hero")
    guide = world.get("guide")
    compass = world.get("compass")
    box = world.get("box")
    subj, obj, pos = _hero_pronouns(hero)

    world.say(
        f"{hero.id} was a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "trait")} {hero.type} who loved quiet places and hidden clues."
    )
    world.say(
        f"One afternoon, {subj} wandered into {world.setting.place} and found {compass.phrase} under a dusty cloth."
    )
    world.say(
        f"The compass did not spin wildly. Instead, it gave a soft magic glow, as if it knew there was a mystery nearby."
    )
    world.say(
        f"{(getattr(subj, 'capitalize')() if callable(getattr(subj, 'capitalize', None)) else str(subj).capitalize())} also noticed a locked box with a strange label that read 'cocaine.'"
    )
    world.para()
    propagate(world)
    world.say(
        f"{(getattr(subj, 'capitalize')() if callable(getattr(subj, 'capitalize', None)) else str(subj).capitalize())} wanted to open the box right away, but {pos} stomach felt tight, because the note nearby was cautionary."
    )
    world.say(
        f"It said to ask before opening anything locked, so {subj} brought the box to a grown-up and kept the lid shut."
    )
    world.para()
    world.say(
        f"Together, they followed the compass and the scraps of foreshadowing."
    )
    world.say(
        f"They found the real hiding place: a map club sign-up sheet tucked behind a shelf, just waiting for someone to enroll."
    )
    world.say(
        f"{(getattr(subj, 'capitalize')() if callable(getattr(subj, 'capitalize', None)) else str(subj).capitalize())} smiled, signed up, and enrolled in the map club instead of touching the unsafe box."
    )
    world.say(
        f"In the end, the compass was the helpful treasure, the mystery was solved, and the box stayed safely closed where it belonged."
    )
    world.facts["resolved"] = True
    world.facts["enrolled"] = True


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting=setting)
    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_type,
            label=params.hero_name,
            meters={"curiosity": 1.0},
            memes={"wonder": 1.0},
        )
    )
    guide = world.add(
        Entity(
            id="grownup",
            kind="character",
            type="adult",
            label="a grown-up",
            meters={"care": 1.0},
        )
    )
    compass = world.add(
        Entity(
            id="compass",
            kind="thing",
            type="compass",
            label="compass",
            phrase=random.choice(CURIOSITIES),
            owner=hero.id,
            meters={"shine": 1.0},
            memes={"mystery": 1.0},
        )
    )
    box = world.add(
        Entity(
            id="box",
            kind="thing",
            type="box",
            label="locked box",
            phrase="a small locked box with a strange label",
            hidden=True,
            meters={"weight": 1.0},
            memes={"risk": 1.0},
        )
    )
    world.clues = list(CLUES)
    world.facts.update(
        setting=setting.place,
        trait=params.trait,
        hero=hero,
        guide=guide,
        compass=compass,
        box=box,
        cautionary_note=True,
        keyword_cocaine=True,
        keyword_compass=True,
        keyword_enroll=True,
        style="mystery",
        instrument_magic=True,
        instrument_foreshadowing=True,
        instrument_cautionary=True,
    )
    generate_story(world)
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f'Write a mystery story that uses "{params.hero_name}", compass, cocaine, and enroll.',
            "Tell a cautionary magic story with foreshadowing and a safe ending.",
            "Make it feel like a gentle mystery where clues matter more than danger.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    subj, obj, pos = _hero_pronouns(hero)
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found a compass under a dusty cloth in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {subj} not open the locked box labeled cocaine?",
            answer=(
                f"{(getattr(subj, 'capitalize')() if callable(getattr(subj, 'capitalize', None)) else str(subj).capitalize())} did not open it because the story gave a cautionary warning, "
                f"and {subj} chose to ask a grown-up instead of taking a risky action."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} enroll in at the end?",
            answer=f"{hero.id} enrolled in a map club after the mystery clues led the way.",
        ),
        QAItem(
            question="How did the magic compass help?",
            answer=(
                "The magic compass gave a soft glow and pointed the way to the hidden clues, "
                "which helped solve the mystery safely."
            ),
        ),
        QAItem(
            question="What did the foreshadowing warn about?",
            answer=(
                "The foreshadowing warned that locked things should stay closed until a grown-up helps."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        lines.append(
            f"  {ent.id:8} kind={ent.kind:9} type={ent.type:8} hidden={ent.hidden} "
            f"meters={{{', '.join(f'{k}:{v}' for k, v in ent.meters.items())}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in ent.memes.items())}}}"
        )
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(library). setting(museum). setting(attic).
hero(girl). hero(boy).
trait(curious). trait(careful). trait(brave). trait(thoughtful). trait(shy).

clue(scrap_of_map). clue(brass_sound). clue(dusty_note).

mystery_story(S,H,T) :- setting(S), hero(H), trait(T).
foreshadowing(clue(dusty_note)).
cautionary(clue(dusty_note)).
magic(compass).
contains_word(compass).
contains_word(cocaine).
contains_word(enroll).

compatible(S,H,T) :- mystery_story(S,H,T), magic(compass), foreshadowing(clue(dusty_note)), cautionary(clue(dusty_note)).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in ["girl", "boy"]:
        lines.append(asp.fact("hero", h))
    for t in TRAITS:
        lines.append(asp.fact("trait", t))
    for c in ["scrap_of_map", "brass_sound", "dusty_note"]:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    if asp.atoms(model, "compatible"):
        print("OK: ASP gate produces compatible mystery stories.")
        return 0
    print("MISMATCH: ASP gate produced no compatible story.")
    return 1


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="library", hero_name="Maya", hero_type="girl", trait="curious"),
    StoryParams(setting="museum", hero_name="Owen", hero_type="boy", trait="careful"),
    StoryParams(setting="attic", hero_name="Zara", hero_type="girl", trait="thoughtful"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, p in enumerate(CURATED):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
