#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/rock_dim_subtract_bolognese_foreshadowing_suspense_misunderstanding.py
===============================================================================================

A small whodunit-style story world built from the seed words:
- rock-dim
- subtract
- bolognese

The domain follows a tiny kitchen mystery: a dim rock-shaped paperweight, a pot of
bolognese, a subtraction worksheet, and a mistaken assumption that turns into a
gentle reveal.

Narrative instruments used:
- Foreshadowing: a small clue appears before it matters.
- Suspense: someone notices something missing and worries about what happened.
- Misunderstanding: the wrong person is blamed until the clue is read correctly.

This script is self-contained and uses the shared StorySample / QAItem /
StoryError containers from storyworlds/results.py. It also includes an inline ASP
twin of the Python reasonableness gate.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bolognese: object | None = None
    clue: object | None = None
    hero: object | None = None
    paperweight: object | None = None
    sidekick: object | None = None
    subtract_sheet: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


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


@dataclass
class Setting:
    place: str
    afford: set[str]
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
class ObjectSpec:
    label: str
    phrase: str
    kind: str
    hidden_place: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class StoryParams:
    setting: str
    hero: str
    sidekick: str
    suspect: str
    clue_object: str
    seed: Optional[int] = None
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", afford={"bolognese", "subtract"}),
    "dining_room": Setting(place="the dining room", afford={"bolognese", "subtract"}),
    "school_table": Setting(place="the classroom table", afford={"subtract"}),
}

OBJECTS = {
    "bowl": ObjectSpec(label="bowl", phrase="a wide white bowl", kind="thing", hidden_place="sink"),
    "spoon": ObjectSpec(label="spoon", phrase="a small silver spoon", kind="thing", hidden_place="drawer"),
    "worksheet": ObjectSpec(label="worksheet", phrase="a math worksheet with subtraction problems", kind="paper", hidden_place="folder"),
    "paperweight": ObjectSpec(label="paperweight", phrase="a rock-dim paperweight shaped like a little stone", kind="thing", hidden_place="desk"),
}

CHARACTERS = {
    "Nina": "girl",
    "Owen": "boy",
    "Mara": "girl",
    "Toby": "boy",
}

SUSPECTS = ["Nina", "Owen", "Mara", "Toby"]

# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combo(setting: str, clue_object: str) -> bool:
    if setting not in SETTINGS or clue_object not in OBJECTS:
        return False
    if clue_object == "worksheet":
        return True
    if clue_object == "paperweight":
        return setting in {"kitchen", "dining_room"}
    return False


def explain_rejection(setting: str, clue_object: str) -> str:
    if setting not in SETTINGS:
        return "(No story: that setting is not part of this little mystery world.)"
    if clue_object not in OBJECTS:
        return "(No story: that object is not part of this little mystery world.)"
    return (
        f"(No story: a {_safe_lookup(OBJECTS, clue_object).label} does not fit this case in {_safe_lookup(SETTINGS, setting).place}. "
        "The clue needs to be something that can plausibly go missing, be noticed, and matter to the mystery.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World()
    setting = _safe_lookup(SETTINGS, params.setting)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=_safe_lookup(CHARACTERS, params.hero),
        label=params.hero,
        meters={"worry": 0.0},
        memes={"curiosity": 2.0, "suspicion": 0.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick,
        kind="character",
        type=_safe_lookup(CHARACTERS, params.sidekick),
        label=params.sidekick,
        meters={"worry": 0.0},
        memes={"helpfulness": 2.0},
    ))
    suspect = world.add(Entity(
        id=params.suspect,
        kind="character",
        type=_safe_lookup(CHARACTERS, params.suspect),
        label=params.suspect,
        meters={"worry": 0.0},
        memes={"nervousness": 0.0},
    ))
    clue = world.add(Entity(
        id=params.clue_object,
        kind="thing",
        type=_safe_lookup(OBJECTS, params.clue_object).kind,
        label=_safe_lookup(OBJECTS, params.clue_object).label,
        phrase=_safe_lookup(OBJECTS, params.clue_object).phrase,
        owner=params.hero,
    ))

    bolognese = world.add(Entity(
        id="bolognese",
        kind="thing",
        type="food",
        label="pot",
        phrase="a simmering pot of bolognese",
        owner=params.hero,
        meters={"simmer": 1.0, "spilled": 0.0},
    ))
    subtract_sheet = world.add(Entity(
        id="subtract_sheet",
        kind="thing",
        type="paper",
        label="worksheet",
        phrase="a subtraction worksheet",
        owner=params.sidekick,
        meters={"missing": 0.0},
    ))
    paperweight = world.add(Entity(
        id="rock_dim",
        kind="thing",
        type="thing",
        label="paperweight",
        phrase="a rock-dim paperweight",
        owner=params.hero,
        hidden_in="desk",
        meters={"noticed": 0.0},
    ))

    # Store references
    world.facts.update(
        setting=setting,
        hero=hero,
        sidekick=sidekick,
        suspect=suspect,
        clue=clue,
        bolognese=bolognese,
        subtract_sheet=subtract_sheet,
        paperweight=paperweight,
    )

    # Setup and foreshadowing
    world.say(
        f"{hero.id} liked quiet evenings in {setting.place}, especially when {bolognese.phrase} "
        f"bubbled on the stove and the room smelled warm and rich."
    )
    if params.clue_object == "paperweight":
        world.say(
            f"On the desk sat {paperweight.phrase}; its shadow looked dim, like a small stone hiding a secret."
        )
    else:
        world.say(
            f"On the table lay {subtract_sheet.phrase}, and one problem was already circled in pencil."
        )
    world.say(
        f"{params.sidekick} came by to help, while {params.suspect} stayed near the doorway with a careful look."
    )

    world.para()

    # Suspense
    if params.clue_object == "worksheet":
        world.say(
            f"Then {params.sidekick} blinked at the table. One subtraction page was gone."
        )
        suspect.meters["worry"] += 1
        hero.meters["worry"] += 1
        world.say(
            f"{params.sidekick} frowned. 'Who moved the worksheet?' {params.sidekick} asked, and the kitchen went still."
        )
    else:
        world.say(
            f"Then the little rock-dim paperweight was not where it should have been."
        )
        hero.meters["worry"] += 1
        suspect.meters["worry"] += 1
        world.say(
            f"{params.hero} looked from the desk to the floor. 'It was right here,' {hero.pronoun()} whispered."
        )

    # Misunderstanding
    world.say(
        f"{params.suspect} pointed at {params.sidekick}. 'I saw you near the table,' {params.suspect} said."
    )
    suspect.memes["suspicion"] += 1
    hero.memes["suspicion"] += 1
    world.say(
        f"{params.sidekick} stared back. 'I only touched the spoon,' {params.sidekick} said, sounding hurt."
    )

    world.para()

    # The clue resolves the misunderstanding
    if params.clue_object == "worksheet":
        world.say(
            f"{params.hero} noticed something small: a trail of red sauce dots led from the stove to the folder."
        )
        world.say(
            f"Inside the folder, the missing worksheet sat flat and safe, with one damp corner from the steam."
        )
        world.say(
            f"{params.suspect} looked again and blushed. The page had not been stolen; it had simply been tucked away to keep it clean."
        )
    else:
        world.say(
            f"{params.sidekick} lifted the dish towel and found the rock-dim paperweight beneath it."
        )
        world.say(
            f"{params.sidekick} had hidden it there only to wipe the counter, then forgotten to put it back."
        )
        world.say(
            f"{params.suspect} lowered their hand. 'So nobody took it?' {params.suspect} asked, sounding relieved."
        )

    # Resolution image
    hero.memes["suspicion"] = 0.0
    suspect.memes["suspicion"] = 0.0
    hero.meters["worry"] = 0.0
    suspect.meters["worry"] = 0.0
    sidekick.meters["worry"] = 0.0
    world.say(
        f"At last, the table was in order again: the bolognese simmered, the clue was back in sight, and everyone laughed at the small mistake."
    )

    world.facts["resolved_by"] = "hidden_place" if params.clue_object == "worksheet" else "dish_towel"
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short whodunit-style story set in {setting.place} that includes the words "rock-dim", "subtract", and "bolognese".',
        f"Tell a gentle mystery where {f['hero'].id} and {f['sidekick'].id} think something went missing, but the answer turns out to be a misunderstanding.",
        f"Write a child-friendly suspense story in {setting.place} with a foreshadowed clue and a calm reveal at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    suspect: Entity = _safe_fact(world, f, "suspect")
    clue: Entity = _safe_fact(world, f, "clue")
    setting: Setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"Where does the mystery happen?",
            answer=f"It happens in {setting.place}, where the bolognese is cooking and the clue is supposed to stay nearby.",
        ),
        QAItem(
            question=f"What made the room feel important at the beginning?",
            answer=f"The simmering bolognese, the quiet table, and the little clue made the scene feel like something careful was about to happen.",
        ),
        QAItem(
            question=f"What did {sidekick.id} think was missing?",
            answer=f"{sidekick.id} thought {clue.label} was missing, which made the room feel tense for a moment.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {suspect.id} feel worried?",
            answer=f"They worried because the clue had disappeared from where it belonged, and each person started wondering who had moved it.",
        ),
        QAItem(
            question=f"What was the misunderstanding in the story?",
            answer=f"The misunderstanding was that people thought someone had taken the clue on purpose, but it had only been tucked away while the counter was being cleaned.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"It was solved when the hidden clue was found in its safe place, showing that nobody had stolen it.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The clue was found, the worry went away, and everyone laughed once they saw the small mistake clearly.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is bolognese?",
        answer="Bolognese is a rich, meat-based sauce that is often served with pasta.",
    ),
    QAItem(
        question="What does subtract mean in math?",
        answer="Subtract means to take one number away from another.",
    ),
    QAItem(
        question="What is a clue in a mystery story?",
        answer="A clue is a small piece of information that helps people figure out what happened.",
    ),
    QAItem(
        question="What does suspense mean in a story?",
        answer="Suspense is the worried, waiting feeling that happens when you do not know what will happen next.",
    ),
    QAItem(
        question="What is a misunderstanding?",
        answer="A misunderstanding happens when people think the wrong thing because they do not have all the facts yet.",
    ),
    QAItem(
        question="What does foreshadowing do?",
        answer="Foreshadowing gives a small hint early in the story about something that will matter later.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(kitchen).
setting(dining_room).
setting(school_table).

affords(kitchen,bolognese).
affords(kitchen,subtract).
affords(dining_room,bolognese).
affords(dining_room,subtract).
affords(school_table,subtract).

object(bowl).
object(spoon).
object(worksheet).
object(paperweight).

can_be_clue(worksheet).
can_be_clue(paperweight).

valid_story(S,O) :- setting(S), object(O), can_be_clue(O), affords(S,subtract).
valid_story(S,O) :- setting(S), object(O), can_be_clue(O), affords(S,bolognese), S != school_table.
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(setting.afford):
            lines.append(asp.fact("affords", sid, act))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
        if oid in {"worksheet", "paperweight"}:
            lines.append(asp.fact("can_be_clue", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(valid_combos())
    asp_set = set(asp_valid_stories())
    mapped = set((s, o) for (s, o) in asp_set if valid_combo(s, o))
    if mapped == expected:
        print(f"OK: ASP and Python agree on {len(expected)} valid story layouts.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(expected))
    print("asp:", sorted(mapped))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for clue in OBJECTS:
            if valid_combo(setting, clue):
                combos.append((setting, clue))
    return combos


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
NAMES = ["Nina", "Owen", "Mara", "Toby"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about a missing clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--sidekick", choices=NAMES)
    ap.add_argument("--suspect", choices=NAMES)
    ap.add_argument("--clue-object", choices=OBJECTS)
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
    clue_object = getattr(args, "clue_object", None) or rng.choice(list(OBJECTS))
    if not valid_combo(setting, clue_object):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    names = NAMES[:]
    hero = getattr(args, "hero", None) or rng.choice(names)
    names = [n for n in names if n != hero]
    sidekick = getattr(args, "sidekick", None) or rng.choice(names)
    if sidekick == hero:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    names = [n for n in names if n != sidekick]
    suspect = getattr(args, "suspect", None) or rng.choice(names)
    if suspect in {hero, sidekick}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, hero=hero, sidekick=sidekick, suspect=suspect, clue_object=clue_object)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:14} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="kitchen", hero="Nina", sidekick="Owen", suspect="Mara", clue_object="worksheet"),
    StoryParams(setting="dining_room", hero="Mara", sidekick="Toby", suspect="Nina", clue_object="paperweight"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for setting, clue in asp_valid_stories():
            print(setting, clue)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.setting} | {p.hero} | {p.clue_object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
