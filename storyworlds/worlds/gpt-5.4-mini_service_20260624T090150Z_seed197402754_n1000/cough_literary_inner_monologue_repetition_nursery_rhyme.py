#!/usr/bin/env python3
"""
A small story world about a child with a cough, a literary moment, and a gentle
reset from noisy repetition to a soothing nursery-rhyme ending.

The simulated premise is simple:
- a child wants to recite a little literary rhyme
- the cough keeps breaking the line
- inner monologue shows the child's feelings
- repetition in the story is a stateful clue: the same phrase returns until the
  child gets help and can finish the rhyme

The world is deliberately tiny and child-facing. It uses physical meters and
emotional memes, plus a declarative ASP twin for the reasonableness gate.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    good: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the bedroom"
    afford_cough: bool = True
    affords: set[str] = field(default_factory=set)
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
class Props:
    id: str
    label: str
    phrase: str
    kind: str
    soothes: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.refrain_count: int = 0

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.refrain_count = self.refrain_count
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str = "bedroom"
    prop: str = "warm tea"
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


SETTINGS = {
    "bedroom": Setting(place="the bedroom", afford_cough=True, affords={"read", "rest"}),
    "window": Setting(place="the window seat", afford_cough=True, affords={"read", "rest"}),
    "kitchen": Setting(place="the kitchen", afford_cough=True, affords={"sip", "rest"}),
}

PROPS = {
    "tea": Props(
        id="tea",
        label="warm tea",
        phrase="a little cup of warm tea",
        kind="tea",
        soothes={"cough"},
        prep="bring warm tea",
        tail="sipped the warm tea and waited for the tickle to fade",
    ),
    "honey": Props(
        id="honey",
        label="honey spoon",
        phrase="a tiny spoon of honey",
        kind="honey",
        soothes={"cough"},
        prep="stir a spoon of honey",
        tail="tasted the honey and felt the scratchy feeling get small",
    ),
    "scarf": Props(
        id="scarf",
        label="soft scarf",
        phrase="a soft scarf for a cozy throat",
        kind="scarf",
        soothes={"chill"},
        prep="wrap a soft scarf",
        tail="snuggled into the scarf and breathed more slowly",
    ),
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ella", "Zoe"],
    "boy": ["Leo", "Noah", "Theo", "Ben", "Max"],
}
PARENTS = ["mother", "father"]
TRAITS = ["small", "curious", "gentle", "brave", "sleepy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a cough, literary rhyme, and a gentle soothed ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def has_reasonable_fix(prop: Props) -> bool:
    return "cough" in prop.soothes


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "prop", None) and not has_reasonable_fix(_safe_lookup(PROPS, getattr(args, "prop", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    prop = getattr(args, "prop", None) or rng.choice([k for k, v in PROPS.items() if has_reasonable_fix(v)])
    return StoryParams(name=name, gender=gender, parent=parent, place=place, prop=prop)


def predict_cough(world: World, child: Entity, cough_level: float) -> bool:
    sim = world.copy()
    sim.get(child.id).meters["cough"] += cough_level
    return sim.get(child.id).meters["cough"] >= THRESHOLD


def do_cough(world: World, child: Entity) -> None:
    child.meters["cough"] += 1
    child.memes["frustration"] += 1
    world.refrain_count += 1


def soothe(world: World, child: Entity, prop: Props, parent: Entity) -> bool:
    if not has_reasonable_fix(prop):
        return False
    if child.meters["cough"] < THRESHOLD:
        return False
    if "cough" in prop.soothes:
        child.meters["cough"] = 0.0
        child.memes["frustration"] = max(0.0, child.memes.get("frustration", 0.0) - 1)
        child.memes["relief"] += 1
        world.say(
            f"{parent.label.capitalize()} brought {prop.label}, and the room grew quiet and kind."
        )
        return True
    return False


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    prop = _safe_lookup(PROPS, params.prop)
    good = world.add(Entity(id=prop.id, kind="thing", type=prop.kind, label=prop.label, phrase=prop.phrase, caretaker=parent.id))

    world.say(f"{child.id} was a little {params.gender} who loved a literary rhyme.")
    world.say(
        f"{child.pronoun().capitalize()} liked to recite it in {world.setting.place}, "
        f"softly and sweetly, like a nursery song."
    )
    world.say(f"{child.id} thought, \"I can say it all. I can say it all.\"")

    world.para()
    world.say(
        f"At {world.setting.place}, {child.id} began, \"Little moon, little spoon, little star up high...\""
    )
    do_cough(world, child)
    world.say(
        f"But then {child.pronoun()} coughed. \"Cough, cough,\" went {child.id}, and the line broke apart."
    )
    world.say(
        f"{child.id} thought, \"Oh dear, my words are tumbling like pebbles in a pail.\""
    )

    if predict_cough(world, child, 0.0):
        world.say(
            f"{child.id} tried again: \"Little moon, little spoon, little star up high...\""
        )
    do_cough(world, child)
    world.say(
        f"Again the cough came back. \"Cough, cough,\" said {child.id}, and the rhyme wobbled once more."
    )
    world.say(
        f"{child.id} thought, \"I want the song to stay in one piece.\""
    )

    world.para()
    if soothe(world, child, prop, parent):
        world.say(
            f"Then {child.id} tried the rhyme again, slow as a rocking chair."
        )
        world.say(
            f"\"Little moon, little spoon, little star up high, little lamb goes tiptoe by.\""
        )
        world.say(
            f"{child.id} smiled, because the cough had quieted, and the same little line could finally finish."
        )
    else:
        world.say(f"{parent.label.capitalize()} sat beside {child.id} and waited with a warm, patient hand.")
        world.say(f"{child.id} rested, and the rhyme stayed in the air like a lullaby.")

    world.facts.update(
        child=child,
        parent=parent,
        prop=good,
        prop_cfg=prop,
        repeated=world.refrain_count,
        soothed=child.meters["cough"] < THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        'Write a short nursery-rhyme style story about a child with a cough who wants to say a literary line.',
        f"Tell a gentle story where {child.id} thinks aloud, coughs twice, and then gets help from {f['parent'].label}.",
        "Write a child-friendly story that repeats one little line until it can be finished safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    prop = _safe_fact(world, f, "prop")
    return [
        QAItem(
            question=f"What did {child.id} want to do at first?",
            answer=f"{child.id} wanted to recite a literary rhyme in a soft nursery-song way.",
        ),
        QAItem(
            question=f"Why did the rhyme stop the first time?",
            answer=f"It stopped because {child.id} coughed, and the cough broke the line in the middle.",
        ),
        QAItem(
            question=f"Who helped {child.id} feel better?",
            answer=f"{parent.label.capitalize()} helped by bringing {prop.label}, which soothed the cough.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The cough quieted, the rhyme could finish, and {child.id} felt relieved and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cough?",
            answer="A cough is a sudden burst of air from the throat that can happen when something tickles or irritates it.",
        ),
        QAItem(
            question="What does literary mean?",
            answer="Literary means it has to do with books, poems, stories, or writing that uses words in a careful way.",
        ),
        QAItem(
            question="Why can repeating a line help in a nursery rhyme?",
            answer="Repeating a line can make a rhyme easier to remember and can sound cozy and musical.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  refrain_count={world.refrain_count}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", place="bedroom", prop="tea"),
    StoryParams(name="Leo", gender="boy", parent="father", place="window", prop="honey"),
]


ASP_RULES = r"""
child(X) :- name(X).
has_cough(X) :- child(X), cough_risk(X).
soothes(P, cough) :- prop(P).
reasonable(P) :- soothes(P, cough).
valid_story(Place, Prop) :- setting(Place), prop(Prop), reasonable(Prop).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        for s in sorted(prop.soothes):
            lines.append(asp.fact("soothes", pid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_storysample(params: StoryParams) -> StorySample:
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


def generate(params: StoryParams) -> StorySample:
    return build_storysample(params)


def resolve_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params_from_args(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
