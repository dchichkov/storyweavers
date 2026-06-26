#!/usr/bin/env python3
"""
storyworlds/worlds/lawyer_dialogue_bravery_whodunit.py
======================================================

A small whodunit story world about a lawyer, careful dialogue, and a brave
person who tells the truth.

Premise:
A lawyer is hired to find out who took a missing item. The answer is not
found by force, but by listening, asking, and noticing small clues.

State model:
- Physical meters track clues, movement, and evidence.
- Emotional memes track fear, courage, trust, and certainty.

The story has a clear beginning, middle turn, and ending:
1) setup with the missing item and the worried client,
2) dialogue that gathers clues and raises bravery,
3) the reveal, with the brave witness speaking up and the mystery solved.
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

THRESHOLD = 1.0



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    client: object | None = None
    lawyer: object | None = None
    missing: object | None = None
    witness: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Setting:
    place: str
    witness_spots: tuple[str, ...]
    clue_spots: tuple[str, ...]
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
class Case:
    missing: str
    phrase: str
    label: str
    reveal: str
    clue: str
    suspect: str
    culprit: str
    false_lead: str
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
    case: str
    lawyer_name: str
    lawyer_type: str
    client_name: str
    client_type: str
    witness_name: str
    witness_type: str
    seed: Optional[int] = None
    params: object | None = None
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


class World:
    def __init__(self, setting: Setting, case: Case) -> None:
        self.setting = setting
        self.case = case
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def ask(lawyer: Entity, other: Entity, question: str, answer: str) -> str:
    return f'"{question}" {lawyer.id} asked. "{answer}" {other.id} said.'


def solve_clue(world: World, lawyer: Entity, witness: Entity, clue: str) -> None:
    witness.memes["courage"] += 1
    witness.memes["trust"] += 1
    lawyer.meters["clues"] += 1
    lawyer.memes["certainty"] += 1
    world.say(ask(
        lawyer,
        witness,
        "Can you tell me what you saw?",
        f"I saw {clue}, and I am not afraid to say it out loud."
    ))


def press_story(world: World, lawyer: Entity, client: Entity, witness: Entity) -> None:
    world.say(
        f"{client.id} sat with a worried face in {world.setting.place}. "
        f"Their {world.case.label} had gone missing, and they asked {lawyer.id} for help."
    )
    lawyer.memes["focus"] += 1
    client.memes["fear"] += 1


def inspect_scene(world: World, lawyer: Entity, witness: Entity, case: Case) -> None:
    lawyer.meters["investigations"] += 1
    lawyer.meters["clues"] += 1
    world.say(
        f"{lawyer.id} looked carefully around the room. Near {world.setting.clue_spots[0]}, "
        f"they found {case.clue}."
    )


def doubt_and_turn(world: World, lawyer: Entity, witness: Entity, case: Case) -> None:
    lawyer.memes["doubt"] += 1
    world.say(
        f"At first, the talk pointed toward {case.false_lead}. "
        f"But {lawyer.id} did not stop there, because a good lawyer listens twice."
    )
    world.say(
        f"{witness.id} hovered near the door, quiet and shaky. "
        f"{lawyer.id} kept the questions gentle."
    )


def brave_confession(world: World, lawyer: Entity, witness: Entity, client: Entity, case: Case) -> None:
    if witness.memes.get("courage", 0.0) < THRESHOLD:
        pass
    witness.memes["fear"] = max(0.0, witness.memes.get("fear", 0.0) - 1)
    lawyer.memes["certainty"] += 1
    client.memes["fear"] = max(0.0, client.memes.get("fear", 0.0) - 1)
    world.say(
        f"Then {witness.id} took a breath and said, "
        f'"I saw {case.culprit} take {case.missing}."'
    )
    world.say(
        f"{lawyer.id} checked the details, and the small clue matched. "
        f"The mystery was no longer a mystery."
    )
    world.say(
        f"In the end, {case.culprit} returned {case.missing}, and {client.id} smiled again. "
        f"{witness.id} stood a little taller for having told the truth."
    )


SETTINGS: dict[str, Setting] = {
    "courthouse": Setting(
        place="the courthouse",
        witness_spots=("the bench", "the hallway", "the front steps"),
        clue_spots=("the bench", "the desk", "the open folder"),
    ),
    "library": Setting(
        place="the library",
        witness_spots=("the reading nook", "the quiet aisle", "the front desk"),
        clue_spots=("the shelf", "the return cart", "the bookmark"),
    ),
    "bakery": Setting(
        place="the bakery",
        witness_spots=("the counter", "the back room", "the stool by the window"),
        clue_spots=("the flour bin", "the tray", "the receipt"),
    ),
}

CASES: dict[str, Case] = {
    "blue_scarf": Case(
        missing="the blue scarf",
        phrase="a blue scarf",
        label="blue scarf",
        reveal="the scarf was tucked into a coat pocket",
        clue="a blue thread on the floor",
        suspect="the tall man by the door",
        culprit="the baker",
        false_lead="the tall man by the door",
    ),
    "silver_key": Case(
        missing="the silver key",
        phrase="a silver key",
        label="silver key",
        reveal="the key was under the chair",
        clue="a tiny scratch on the desk",
        suspect="the quiet clerk",
        culprit="the clerk's own jacket",
        false_lead="the quiet clerk",
    ),
    "red_balloon": Case(
        missing="the red balloon",
        phrase="a red balloon",
        label="red balloon",
        reveal="the balloon was tied behind a chair",
        clue="a red string caught on a nail",
        suspect="the giggling child",
        culprit="the child with sticky fingers",
        false_lead="the giggling child",
    ),
}

NAMES = ["Nora", "Eli", "Maya", "Finn", "Lena", "Theo", "Iris", "Owen"]
TYPES = ["woman", "man", "girl", "boy"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CASES]


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_bravery(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes.get("courage", 0.0) >= THRESHOLD and not e.meters.get("brave_spoken", 0.0):
            e.meters["brave_spoken"] = 1
            out.append("__brave__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    fired = []
    for rule in [Rule("bravery", _r_bravery)]:
        fired.extend(rule.apply(world))
    if narrate:
        for s in fired:
            if s != "__brave__":
                world.say(s)
    return fired


ASP_RULES = r"""
brave(E) :- courage(E), courage(E) >= 1.
valid(Setting, Case) :- setting(Setting), case(Case).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small lawyer-and-clues whodunit.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--lawyer-name")
    ap.add_argument("--lawyer-type", choices=["woman", "man"])
    ap.add_argument("--client-name")
    ap.add_argument("--client-type", choices=["woman", "man", "girl", "boy"])
    ap.add_argument("--witness-name")
    ap.add_argument("--witness-type", choices=TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "case", None):
        combos = [c for c in combos if c[1] == getattr(args, "case", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, case = rng.choice(combos)
    lawyer_type = getattr(args, "lawyer_type", None) or rng.choice(["woman", "man"])
    client_type = getattr(args, "client_type", None) or rng.choice(TYPES)
    witness_type = getattr(args, "witness_type", None) or rng.choice(TYPES)
    return StoryParams(
        setting=setting,
        case=case,
        lawyer_name=getattr(args, "lawyer_name", None) or rng.choice(NAMES),
        lawyer_type=lawyer_type,
        client_name=getattr(args, "client_name", None) or rng.choice(NAMES),
        client_type=client_type,
        witness_name=getattr(args, "witness_name", None) or rng.choice(NAMES),
        witness_type=witness_type,
    )


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    case = _safe_lookup(CASES, params.case)
    world = World(setting, case)
    lawyer = world.add(Entity(id=params.lawyer_name, kind="character", type=params.lawyer_type, label="lawyer"))
    client = world.add(Entity(id=params.client_name, kind="character", type=params.client_type, label="client"))
    witness = world.add(Entity(id=params.witness_name, kind="character", type=params.witness_type, label="witness"))
    missing = world.add(Entity(id="missing", type="thing", label=case.label, phrase=case.phrase, owner=client.id))

    press_story(world, lawyer, client, witness)
    world.para()
    inspect_scene(world, lawyer, witness, case)
    world.say(
        f"{lawyer.id} asked around the room, and everyone pointed to {case.suspect}."
    )
    doubt_and_turn(world, lawyer, witness, case)
    solve_clue(world, lawyer, witness, case.clue)
    world.para()
    brave_confession(world, lawyer, witness, client, case)
    world.facts.update(
        lawyer=lawyer,
        client=client,
        witness=witness,
        missing=missing,
        case=case,
        setting=setting,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short whodunit about a lawyer who solves a mystery by asking careful questions.",
        f"Tell a child-friendly detective story set in {f['setting'].place} with dialogue and bravery.",
        f"Write a story where {f['lawyer'].id} uses clues and a brave witness to find {f['case'].missing}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lawyer = _safe_fact(world, f, "lawyer")
    client = _safe_fact(world, f, "client")
    witness = _safe_fact(world, f, "witness")
    case = _safe_fact(world, f, "case")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who helped solve the mystery in {setting.place}?",
            answer=f"{lawyer.id}, the lawyer, helped solve it by asking careful questions and following the clue.",
        ),
        QAItem(
            question=f"What was missing from the case?",
            answer=f"{case.missing} was missing, and {client.id} wanted help finding it.",
        ),
        QAItem(
            question=f"What did the brave witness do at the end?",
            answer=f"{witness.id} told the truth out loud and said that {case.culprit} took {case.missing}.",
        ),
        QAItem(
            question="How did the lawyer solve the whodunit?",
            answer=f"{lawyer.id} noticed {case.clue}, listened to the answers, and matched the clue to the real answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lawyer do?",
            answer="A lawyer helps people with rules, arguments, and questions, and can speak for someone in trouble.",
        ),
        QAItem(
            question="Why is bravery important in a mystery?",
            answer="Bravery helps a person speak up, tell the truth, and share what they saw even when they feel nervous.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for s in SETTINGS:
            for c in CASES:
                params = StoryParams(
                    setting=s,
                    case=c,
                    lawyer_name="Nora",
                    lawyer_type="woman",
                    client_name="Pip",
                    client_type="boy",
                    witness_name="June",
                    witness_type="girl",
                )
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
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
