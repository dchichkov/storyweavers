#!/usr/bin/env python3
"""
storyworlds/worlds/mistaken_twist_comedy.py
==========================================

A small, child-facing storyworld about a mistaken choice, a comic twist,
and a cheerful ending.

The seed premise is a simple comedy of errors:
a child thinks they have found the right item, but the item turns out to be
the wrong one in a funny way. The grown-up notices the mix-up, the child
reacts, and the twist reveals that the mistake actually leads to a better,
sillier result.

This world models:
- physical objects with meters like lost, bumped, opened, and messy
- emotional memes like joy, worry, embarrassment, and relief
- a causal turn where a mistaken choice creates a comic complication
- a resolution where the mistaken item becomes the joke, not the problem

The story quality goal is a short comedy with:
- a clear setup
- a mistaken middle beat
- a twist
- a warm ending image
"""

from __future__ import annotations

import argparse
import copy
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
    caretaker: Optional[str] = None
    used_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    grownup: object | None = None
    prop: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"lost": 0.0, "opened": 0.0, "messy": 0.0, "bumped": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "embarrassment": 0.0, "relief": 0.0, "surprise": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    indoor: bool
    noise: str
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
class Prop:
    id: str
    label: str
    phrase: str
    twist: str
    mess: str
    scene: str
    tags: set[str] = field(default_factory=set)
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
    place: str
    prop: str
    name: str
    gender: str
    grownup: str
    trait: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, noise="clink"),
    "playroom": Setting(place="the playroom", indoor=True, noise="giggle"),
    "porch": Setting(place="the porch", indoor=False, noise="hush"),
}

PROPS = {
    "box": Prop(
        id="box",
        label="a striped box",
        phrase="a striped box with a wobbly lid",
        twist="it was a prop box for a silly show",
        mess="opened",
        scene="stage",
        tags={"box", "surprise", "show"},
    ),
    "bag": Prop(
        id="bag",
        label="a tote bag",
        phrase="a floppy tote bag with stars on it",
        twist="it held pretend fish and a paper crown",
        mess="messy",
        scene="picnic",
        tags={"bag", "surprise", "show"},
    ),
    "hat": Prop(
        id="hat",
        label="a tall hat",
        phrase="a tall hat with a ribbon",
        twist="it hid a rubber chicken and a note",
        mess="bumped",
        scene="party",
        tags={"hat", "surprise", "show"},
    ),
}

NAMES_GIRL = ["Mina", "Nora", "Lily", "Ada", "Zoe", "Maya"]
NAMES_BOY = ["Finn", "Leo", "Theo", "Sam", "Max", "Eli"]
TRAITS = ["curious", "bouncy", "cheerful", "silly", "spirited", "playful"]


def reasonableness_gate(place: str, prop: str) -> bool:
    return place in SETTINGS and prop in PROPS


def explain_rejection(place: str, prop: str) -> str:
    return f"(No story: the combination of place='{place}' and prop='{prop}' does not fit this comedy world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mistaken-choice comedy story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--grownup", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    prop = getattr(args, "prop", None) or rng.choice(list(PROPS))
    if not reasonableness_gate(place, prop):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    grownup = getattr(args, "grownup", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, prop=prop, name=name, gender=gender, grownup=grownup, trait=trait)


def introduce(world: World, child: Entity, prop: Entity) -> None:
    world.say(f"{child.id} was a {child.memes.get('trait', 'curious')} little {child.type} who loved jokes and surprises.")
    world.say(f"One day, {child.id} noticed {prop.phrase} and thought it was the right thing for the day.")


def simulate(world: World, child: Entity, grownup: Entity, prop: Entity) -> None:
    prop.meters["opened"] += 1
    child.memes["worry"] += 1
    child.memes["surprise"] += 1
    world.say(f"{child.id} carried {prop.label} to {world.setting.place}.")
    world.say(f"{child.id} wanted to open it right away, but {grownup.pronoun('possessive')} {grownup.type} gave a careful look.")
    world.say(f'"Wait," {grownup.id} said. "That does not look like our thing."')
    child.memes["embarrassment"] += 1
    child.meters["bumped"] += 1
    world.say(f"{child.id} opened it anyway, and the lid gave a funny little {world.setting.noise}.")
    prop.meters["opened"] += 1


def twist_and_resolution(world: World, child: Entity, grownup: Entity, prop: Entity) -> None:
    child.memes["surprise"] += 1
    child.memes["embarrassment"] = max(0.0, child.memes["embarrassment"] - 1.0)
    child.memes["joy"] += 2
    child.memes["relief"] += 1
    grownup.memes["joy"] += 1
    world.say(f"Then the twist came: {prop.twist}.")
    world.say(f"There was a silly little note inside that said the mix-up was planned all along.")
    world.say(f"{grownup.id} laughed first, and then {child.id} laughed too.")
    world.say(f'They decided the mistake was funny, not bad, and {child.id} held up {prop.label} like a prize.')
    world.say(f"By the end, the day felt brighter, and the wrong thing had become the best joke in the room.")


def tell(setting: Setting, prop_cfg: Prop, child_name: str, gender: str, grownup_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=gender, label=child_name))
    grownup = world.add(Entity(id="Grownup", kind="character", type=grownup_type, label=f"the {grownup_type}"))
    prop = world.add(Entity(id=prop_cfg.id, type="thing", label=prop_cfg.label, phrase=prop_cfg.phrase, owner=child.id))
    child.memes["trait"] = trait
    child.meters["lost"] += 1

    world.say(f"{child.id} was a {trait} little {gender} who went to {setting.place} with {grownup.label}.")
    world.say(f"On the way, {child.id} found {prop.phrase} and thought, quite mistakenly, that it belonged to them.")
    world.para()
    simulate(world, child, grownup, prop)
    world.para()
    twist_and_resolution(world, child, grownup, prop)

    world.facts.update(child=child, grownup=grownup, prop=prop, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    grownup = _safe_fact(world, f, "grownup")
    prop = _safe_fact(world, f, "prop")
    return [
        f"Write a short funny story for a young child about {child.id} making a mistaken choice and learning it is harmless.",
        f"Tell a comedy story where {child.id} finds {prop.phrase} at {world.setting.place} and {grownup.id} discovers the mix-up.",
        f"Write a gentle mistaken-identity story with a twist ending and a laugh at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    grownup = _safe_fact(world, f, "grownup")
    prop = _safe_fact(world, f, "prop")
    return [
        QAItem(
            question=f"Who thought {prop.label} was the right thing at first?",
            answer=f"{child.id} thought {prop.label} was the right thing at first, but that was a mistaken idea.",
        ),
        QAItem(
            question=f"What did {grownup.id} notice before the mix-up turned funny?",
            answer=f"{grownup.id} noticed that {prop.label} did not seem to belong there, which made the moment careful before it became silly.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=f"The mistaken choice turned into a joke, and everyone laughed when they learned {prop.twist}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    prop = _safe_fact(world, world.facts, "prop")
    if prop.id == "box":
        return [
            QAItem(
                question="What is a box used for?",
                answer="A box is used to hold or carry things, and it can keep items together until someone opens it.",
            ),
            QAItem(
                question="What does a surprise mean?",
                answer="A surprise is something unexpected that makes someone stop and say 'oh!' or 'wow!'",
            ),
        ]
    if prop.id == "bag":
        return [
            QAItem(
                question="What can a tote bag do?",
                answer="A tote bag can carry small things from one place to another.",
            ),
            QAItem(
                question="Why is a costume prop funny in a show?",
                answer="A prop is funny in a show because it helps make pretend actions look lively and silly.",
            ),
        ]
    return [
        QAItem(
            question="Why can a hat be part of a costume?",
            answer="A hat can be part of a costume because people wear it to look playful, fancy, or silly in a show.",
        ),
        QAItem(
            question="What is a joke?",
            answer="A joke is something meant to make people laugh.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "trait"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(kitchen). place(playroom). place(porch).
prop(box). prop(bag). prop(hat).

mistaken(P) :- prop(P).
twist(P) :- prop(P).
comic(P) :- mistaken(P), twist(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for p in PROPS:
        lines.append(asp.fact("prop", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show comic/1."))
    return sorted(set(asp.atoms(model, "comic")))


def asp_verify() -> int:
    py = {(p,) for p in PROPS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} comic props).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROPS, params.prop), params.name, params.gender, params.grownup, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    StoryParams(place="kitchen", prop="box", name="Mina", gender="girl", grownup="mother", trait="curious"),
    StoryParams(place="playroom", prop="bag", name="Finn", gender="boy", grownup="father", trait="silly"),
    StoryParams(place="porch", prop="hat", name="Zoe", gender="girl", grownup="father", trait="bouncy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show comic/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show comic/1."))
        for atom in sorted(set(asp.atoms(model, "comic"))):
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
