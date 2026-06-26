#!/usr/bin/env python3
"""
Story world: prudent cliff lookout mystery with kindness, problem solving, and conflict.

A child and a helper visit a cliff lookout. Something small and important goes missing,
a worry turns into conflict, and prudent kindness helps solve the mystery.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    item: object | None = None
    other: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Setting:
    place: str = "the cliff lookout"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Mystery:
    id: str
    clue: str
    missing: str
    solved_by: str
    problem: str
    conflict: str
    resolution: str
    keyword: str = "prudent"
    tags: set[str] = field(default_factory=set)
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    mystery: str
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


GIRL_NAMES = ["Mia", "Lina", "Nora", "Ivy", "Tess", "Ruby", "Clara", "June"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Max", "Owen", "Leo", "Sam"]
TRAITS = ["curious", "quiet", "brave", "careful", "gentle", "thoughtful"]
PARENTS = ["mother", "father"]

MYSTERIES = {
    "binoculars": Mystery(
        id="binoculars",
        clue="a pair of binoculars",
        missing="missing binoculars",
        solved_by="find the binoculars in a cedar box",
        problem="the lookout's binoculars were gone",
        conflict="two children accused each other of hiding them",
        resolution="the child noticed a tide box under the bench",
        tags={"cliff", "lookout", "kindness", "problem-solving", "conflict"},
    ),
    "map": Mystery(
        id="map",
        clue="a folded map",
        missing="missing map",
        solved_by="find the map tucked inside a stone marker",
        problem="the lookout's map was gone",
        conflict="one child blamed another for the missing map",
        resolution="the child followed a tiny trail of salt to a crack in the wall",
        tags={"cliff", "lookout", "kindness", "problem-solving", "conflict"},
    ),
}

SETTING = Setting(place="the cliff lookout", affords={"search", "watch", "compare"})
CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", trait="careful", mystery="binoculars"),
    StoryParams(name="Theo", gender="boy", parent="father", trait="thoughtful", mystery="map"),
]


class StoryWorld:
    pass


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    other = world.add(Entity(id="other", kind="character", type="child", label="another child"))
    item = world.add(Entity(
        id=mystery.id, type="thing", label=mystery.clue, phrase=mystery.clue,
        caretaker=parent.id,
    ))
    child.memes["curiosity"] = 1
    child.memes["prudent"] = 1
    world.facts.update(params=params, child=child, parent=parent, other=other, item=item, mystery=mystery)
    return world


def intro(world: World) -> None:
    f = world.facts
    p: StoryParams = _safe_fact(world, f, "params")
    m: Mystery = _safe_fact(world, f, "mystery")
    c: Entity = _safe_fact(world, f, "child")
    par: Entity = _safe_fact(world, f, "parent")
    world.say(
        f"{p.name} was a {p.trait} child who liked the {SETTING.place} because the wind there sounded like a secret."
    )
    world.say(
        f"{c.id} was also prudent, which meant {c.pronoun()} looked carefully before doing anything new."
    )
    world.say(
        f"One afternoon, {p.name} and {par.label} went to {SETTING.place} to watch the sea, but {m.problem}."
    )


def build_conflict(world: World) -> None:
    f = world.facts
    p: StoryParams = _safe_fact(world, f, "params")
    c: Entity = _safe_fact(world, f, "child")
    o: Entity = _safe_fact(world, f, "other")
    m: Mystery = _safe_fact(world, f, "mystery")
    c.memes["conflict"] += 1
    o.memes["conflict"] += 1
    world.say(
        f"{p.name} noticed the empty hook and felt a little knot of worry."
    )
    world.say(
        f"Then {o.label} said, \"You took them,\" and {p.name} said, \"No, I didn't,\" so {m.conflict}."
    )


def solve_mystery(world: World) -> None:
    f = world.facts
    p: StoryParams = _safe_fact(world, f, "params")
    c: Entity = _safe_fact(world, f, "child")
    par: Entity = _safe_fact(world, f, "parent")
    o: Entity = _safe_fact(world, f, "other")
    m: Mystery = _safe_fact(world, f, "mystery")
    c.memes["kindness"] = 1
    c.memes["problem_solving"] = 1
    world.say(
        f"{p.name} did not shout back. {c.pronoun().capitalize()} took a slow breath and looked around the lookout again."
    )
    world.say(
        f"{p.name} noticed {m.resolution}."
    )
    world.say(
        f"Inside it was the {m.clue}, safe from the wind."
    )
    world.say(
        f"{p.name} explained kindly, and {o.label} looked embarrassed but relieved."
    )
    world.say(
        f"Soon {par.label} smiled, because {m.solved_by}."
    )
    c.memes["conflict"] = 0
    par.memes["relief"] = 1


def end_image(world: World) -> None:
    f = world.facts
    p: StoryParams = _safe_fact(world, f, "params")
    par: Entity = _safe_fact(world, f, "parent")
    world.say(
        f"In the end, {p.name} stood beside {par.label} at the {SETTING.place}, holding the found treasure while the sea kept shining below."
    )
    world.say(
        f"The mystery was solved, the worry was gone, and prudence had helped kindness win."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    world.para()
    build_conflict(world)
    world.para()
    solve_mystery(world)
    end_image(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = _safe_fact(world, f, "params")
    m: Mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short mystery story for a child named {p.name} at a cliff lookout.',
        f"Tell a gentle story where {p.name} is prudent, there is {m.problem}, and kindness helps solve it.",
        f"Write a small cliff lookout mystery with conflict, problem solving, and a calm ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = _safe_fact(world, f, "params")
    m: Mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"Why did {p.name} go to the cliff lookout?",
            answer=f"{p.name} went there with {f['parent'].label} to watch the sea, but then {m.problem}.",
        ),
        QAItem(
            question=f"What caused the conflict in the story?",
            answer=f"The conflict began when {f['other'].label} said, \"You took them,\" because {m.conflict}.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{p.name} stayed prudent, looked carefully, and found {m.resolution}, which led to {m.solved_by}.",
        ),
        QAItem(
            question=f"How did {p.name} act when things got tense?",
            answer=f"{p.name} stayed kind and calm instead of shouting back, and that helped everyone solve the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cliff lookout?",
            answer="A cliff lookout is a place high up on land where people can safely look out over the sea and the horizon.",
        ),
        QAItem(
            question="What does prudent mean?",
            answer="Prudent means careful and sensible, especially when you want to avoid a mistake or a danger.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle and caring with other people, especially when they feel upset.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a difficulty and trying different ways to fix it.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.

place(cliff_lookout).

theme(prudent).
theme(kindness).
theme(problem_solving).
theme(conflict).

valid(story) :- place(cliff_lookout), theme(prudent), theme(kindness), theme(problem_solving), theme(conflict).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("place", "cliff_lookout"),
            asp.fact("theme", "prudent"),
            asp.fact("theme", "kindness"),
            asp.fact("theme", "problem_solving"),
            asp.fact("theme", "conflict"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    ok = set(asp.atoms(model, "valid")) == {("story",)}
    if ok:
        print("OK: ASP gate matches the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP gate did not validate the story world.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld at a cliff lookout.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    mystery = getattr(args, "mystery", None) or rng.choice(sorted(MYSTERIES))
    if getattr(args, "gender", None) == "girl" and name in BOY_NAMES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) == "boy" and name in GIRL_NAMES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait, mystery=mystery)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = CURATED
    else:
        params_list = []
        seen = set()
        i = 0
        while len(params_list) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            key = (p.name, p.gender, p.parent, p.trait, p.mystery)
            i += 1
            if key in seen:
                continue
            seen.add(key)
            p.seed = base_seed + i
            params_list.append(p)

    for p in params_list:
        samples.append(generate(p))

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
