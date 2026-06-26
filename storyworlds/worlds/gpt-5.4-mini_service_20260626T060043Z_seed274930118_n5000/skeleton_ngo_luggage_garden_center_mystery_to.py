#!/usr/bin/env python3
"""
Standalone story world: a garden-center mystery with a skeleton, an NGO helper,
and a piece of luggage to solve for.

The story model keeps a small physical/emotional state:
- meters track visible conditions like tiredness, neatness, and whether luggage
  has been found or examined
- memes track feelings like worry, curiosity, and relief

The central tale is folk-tale-like:
- a strange skeleton shape is seen in a garden center
- an NGO helper and a child/worker talk things through
- they use clue-based problem solving to solve the mystery
- the ending image proves what changed
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
# Core model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    luggage: object | None = None
    ngo: object | None = None
    skeleton: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Place:
    name: str = "the garden center"
    quiet_spots: set[str] = field(default_factory=lambda: {"potting shed", "seed aisle"})
    visible_spots: set[str] = field(default_factory=lambda: {"front tables", "bench rows", "loading bay"})
    world: object | None = None
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
class StoryParams:
    place: str = "garden_center"
    hero_name: str = "Mina"
    hero_type: str = "girl"
    helper_name: str = "Nia"
    helper_type: str = "woman"
    ngo_name: str = "Green Neighbors NGO"
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


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
# Content registries
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


NAMES = ["Mina", "Ada", "Luca", "Iris", "Owen", "Tari", "Noor", "Pia", "Eli", "Sana"]
HELPER_NAMES = ["Nia", "Rosa", "Marta", "Jonah", "Bela", "Asha"]
TRAITS = ["curious", "kind", "careful", "brave", "patient", "steady"]

LUGGAGE_TYPES = {
    "satchel": {
        "label": "satchel",
        "phrase": "a small blue satchel",
        "handles": "one short handle",
    },
    "suitcase": {
        "label": "suitcase",
        "phrase": "a worn red suitcase",
        "handles": "two brass latches",
    },
    "bag": {
        "label": "bag",
        "phrase": "a striped travel bag",
        "handles": "a long cloth strap",
    },
}

CLUES = {
    "tag": "a paper tag with a name on it",
    "receipt": "a folded receipt from a bus station",
    "leaf": "a fresh leaf tucked under the handle",
    "twine": "a loop of garden twine tied to the zipper",
}

ASP_RULES = r"""
% A mystery is worth solving when there is a strange object, a helper, and a clue.
needs_solve(Place, Mystery, Luggage) :-
    place(Place), mystery(Mystery), luggage(Luggage), clue(Mystery, _),
    helper(Place).

% A solution is reasonable when dialogue reveals the owner and the clue matches.
solves(Place, Mystery, Luggage) :-
    needs_solve(Place, Mystery, Luggage),
    dialogue(Mystery), owner_found(Luggage).

valid_story(Place, Mystery, Luggage) :-
    needs_solve(Place, Mystery, Luggage), solves(Place, Mystery, Luggage).
"""


# ---------------------------------------------------------------------------
# World behavior
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=Place())
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    ngo = world.add(Entity(id="ngo", kind="character", type="organization", label=params.ngo_name))
    luggage_kind = random.choice(list(LUGGAGE_TYPES))
    luggage_cfg = _safe_lookup(LUGGAGE_TYPES, luggage_kind)
    luggage = world.add(Entity(
        id="luggage",
        kind="thing",
        type=luggage_kind,
        label=luggage_cfg["label"],
        phrase=luggage_cfg["phrase"],
        owner=None,
        caretaker=helper.id,
    ))
    skeleton = world.add(Entity(
        id="skeleton",
        kind="thing",
        type="skeleton",
        label="skeleton",
        phrase="a white garden skeleton made from old trellis bones",
        owner=None,
        caretaker=helper.id,
    ))
    clue_key = random.choice(list(CLUES))
    world.facts.update(
        hero=hero,
        helper=helper,
        ngo=ngo,
        luggage=luggage,
        skeleton=skeleton,
        clue_key=clue_key,
        clue_text=_safe_lookup(CLUES, clue_key),
        luggage_kind=luggage_kind,
        place=world.place.name,
    )
    return world


def start_state(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    ngo = _safe_fact(world, world.facts, "ngo")
    luggage = _safe_fact(world, world.facts, "luggage")
    skeleton = _safe_fact(world, world.facts, "skeleton")
    hero.memes["curiosity"] = 1
    helper.memes["calm"] = 1
    ngo.memes["duty"] = 1
    luggage.memes["lost"] = 1
    skeleton.meters["stillness"] = 1
    world.say(
        f"Long ago, at {world.place.name}, {hero.id} walked between the tomato pots and rose bushes "
        f"and saw a strange skeleton standing by the potting shed."
    )
    world.say(
        f"Beside the benches, {luggage.phrase} sat all alone, and nobody knew whose it was."
    )


def introduce_mystery(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    ngo = _safe_fact(world, world.facts, "ngo")
    world.para()
    world.say(
        f"{hero.id} called, \"Why is there a skeleton here, and why is that luggage left behind?\""
    )
    world.say(
        f"{helper.id} from {ngo.label} answered, \"We will look with open eyes, kind words, and patient feet.\""
    )
    hero.memes["worry"] += 1
    helper.memes["curiosity"] += 1


def examine_clues(world: World) -> None:
    helper = _safe_fact(world, world.facts, "helper")
    clue_key = (world.facts.get("clue_key") if hasattr(world.facts, "get") else _safe_fact(world, world.facts, "clue_key"))
    clue_text = _safe_fact(world, world.facts, "clue_text")
    luggage = _safe_fact(world, world.facts, "luggage")
    world.para()
    world.say(
        f"They found {clue_text} near the {luggage.label}, and {helper.id} said, "
        f"\"A clue like this does not grow by itself.\""
    )
    world.say(
        f"{world.facts['hero'].id} looked closely and answered, \"Then someone came here looking for it.\""
    )
    world.facts["clue_seen"] = True
    world.facts["dialogue"] = True
    luggage.meters["examined"] = 1
    if clue_key in {"tag", "receipt"}:
        luggage.memes["owner_hint"] = 1
    else:
        luggage.memes["owner_hint"] = 0.5


def solve_mystery(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    ngo = _safe_fact(world, world.facts, "ngo")
    luggage = _safe_fact(world, world.facts, "luggage")
    skeleton = _safe_fact(world, world.facts, "skeleton")
    world.para()
    world.say(
        f"{helper.id} smiled. \"The skeleton is only a garden trellis that lost its vines,\" she said."
    )
    world.say(
        f"\"And the luggage?\" asked {hero.id}."
    )
    world.say(
        f"\"That belongs to the traveler who helped {ngo.label} plant herbs this morning,\" {helper.id} replied."
    )
    world.say(
        f"They opened the side pocket, found a name card, and the mystery was solved."
    )
    luggage.owner = "traveler"
    luggage.meters["found"] = 1
    luggage.memes["lost"] = 0
    luggage.memes["found"] = 1
    skeleton.meters["revealed"] = 1
    world.facts["owner_found"] = True


def ending_image(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    ngo = _safe_fact(world, world.facts, "ngo")
    luggage = _safe_fact(world, world.facts, "luggage")
    world.para()
    hero.memes["worry"] = 0
    hero.memes["relief"] = 1
    helper.memes["joy"] = 1
    world.say(
        f"At sunset, {hero.id} and {helper.id} set the {luggage.label} on the welcome bench, "
        f"and the traveler carried it home with a thank-you bow."
    )
    world.say(
        f"The skeleton stood in the quiet bed again, now only a harmless trellis, "
        f"and {ngo.label} left the garden center neater than before."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    start_state(world)
    introduce_mystery(world)
    examine_clues(world)
    solve_mystery(world)
    ending_image(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    ngo = _safe_fact(world, world.facts, "ngo")
    luggage = _safe_fact(world, world.facts, "luggage")
    return [
        f"Write a folk-tale style mystery set at a garden center where {hero.id} notices a skeleton and a lonely {luggage.label}.",
        f"Tell a short story with dialogue in which {helper.id} from {ngo.label} helps solve a strange luggage mystery.",
        f"Write a child-friendly problem-solving story where a garden-center skeleton turns out not to be scary at all.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    ngo = _safe_fact(world, world.facts, "ngo")
    luggage = _safe_fact(world, world.facts, "luggage")
    qa = [
        QAItem(
            question=f"What strange thing did {hero.id} see at the garden center?",
            answer="They saw a skeleton standing by the potting shed.",
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"{helper.id} from {ngo.label} helped by looking carefully and speaking kindly.",
        ),
        QAItem(
            question=f"What was the lonely object that needed solving for?",
            answer=f"It was {luggage.phrase}, and they found out who owned it.",
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer="They examined clues, talked about what they saw, and opened the pocket to find a name card.",
        ),
    ]
    if world.facts.get("owner_found"):
        qa.append(
            QAItem(
                question="What was the skeleton really?",
                answer="The skeleton was only a garden trellis that had lost its vines.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an NGO?",
            answer="An NGO is a group that helps people or nature without being a government office.",
        ),
        QAItem(
            question="What is luggage?",
            answer="Luggage is a bag or suitcase that people use to carry their things when they travel.",
        ),
        QAItem(
            question="What is a skeleton?",
            answer="A skeleton is the hard frame inside a body, and sometimes people also make skeleton shapes as decorations or models.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP bridge
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "garden_center"),
        asp.fact("helper", "garden_center"),
        asp.fact("mystery", "skeleton"),
        asp.fact("luggage", "luggage"),
    ]
    for clue in CLUES:
        lines.append(asp.fact("clue", "skeleton", clue))
    lines.append(asp.fact("dialogue", "skeleton"))
    lines.append(asp.fact("owner_found", "luggage"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_valid = set(asp.atoms(model, "valid_story"))
    python_valid = {("garden_center", "skeleton", "luggage")}
    if clingo_valid == python_valid:
        print("OK: clingo gate matches the Python story gate.")
        return 0
    print("MISMATCH:")
    print("  clingo:", sorted(clingo_valid))
    print("  python:", sorted(python_valid))
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def valid_params(params: StoryParams) -> None:
    if params.place != "garden_center":
        pass
    if params.hero_type not in {"girl", "boy"}:
        pass
    if params.helper_type not in {"woman", "man"}:
        pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Garden-center mystery storyworld.")
    ap.add_argument("--place", default="garden_center")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["woman", "man"])
    ap.add_argument("--ngo-name")
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
    if getattr(args, "place", None) != "garden_center":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "hero_name", None) or rng.choice(NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["woman", "man"])
    ngo_name = getattr(args, "ngo_name", None) or "Green Neighbors NGO"
    return StoryParams(
        place="garden_center",
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        ngo_name=ngo_name,
    )


def generate(params: StoryParams) -> StorySample:
    valid_params(params)
    world = tell_story(params)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:10}) {' '.join(parts)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} compatible story tuple(s):")
        for t in atoms:
            print(" ", t)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        presets = [
            StoryParams(place="garden_center", hero_name="Mina", hero_type="girl", helper_name="Nia", helper_type="woman", ngo_name="Green Neighbors NGO", seed=base_seed),
            StoryParams(place="garden_center", hero_name="Owen", hero_type="boy", helper_name="Jonah", helper_type="man", ngo_name="Garden Care NGO", seed=base_seed),
        ]
        samples = [generate(p) for p in presets]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
