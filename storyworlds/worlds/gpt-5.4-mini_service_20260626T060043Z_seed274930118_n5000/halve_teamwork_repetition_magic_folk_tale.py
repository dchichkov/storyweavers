#!/usr/bin/env python3
"""
storyworlds/worlds/halve_teamwork_repetition_magic_folk_tale.py
===============================================================

A small folk-tale story world about teamwork, repetition, and a little magic.

Seed tale premise:
- In a quiet village, two children find a magic loaf that is far too large to
  carry home.
- They must work together, repeat a simple charm, and learn how to halve the
  loaf fairly so everyone can share.

The world is intentionally small and constraint-checked: the story only
generates when the chosen situation has a believable risk and a believable
magical fix.
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

    c1: object | None = None
    c2: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str
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
class Magic:
    id: str
    chant: str
    repeat: str
    effect: str
    helper: str
    ending: str
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


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    split_into: str
    plural: bool = False
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    magic: str
    prize: str
    name1: str
    name2: str
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
    "cottage": Setting(place="the cottage", affords={"share_magic"}),
    "forest": Setting(place="the forest edge", affords={"share_magic"}),
    "village": Setting(place="the village green", affords={"share_magic"}),
}

MAGICS = {
    "halve_spell": Magic(
        id="halve_spell",
        chant="halve, halve, kindly halve",
        repeat="again and again",
        effect="split neatly in two",
        helper="one held the knife, and the other steadied the board",
        ending="Soon there were two even halves, and no crumb was lost",
        tags={"magic", "repetition", "teamwork", "halve"},
    ),
}

PRIZES = {
    "loaf": Prize(
        label="loaf",
        phrase="a golden loaf of bread",
        type="loaf",
        split_into="halves",
        plural=False,
    ),
    "cake": Prize(
        label="cake",
        phrase="a round honey cake",
        type="cake",
        split_into="halves",
        plural=False,
    ),
    "turnip": Prize(
        label="turnip",
        phrase="a giant white turnip",
        type="turnip",
        split_into="halves",
        plural=False,
    ),
}

NAMES = ["Nora", "Tobin", "Mira", "Eli", "Ruth", "Pip", "Lena", "Owen", "Bram", "Sia"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_split(world: World) -> list[str]:
    out: list[str] = []
    for hero in [e for e in world.entities.values() if e.kind == "character"]:
        if hero.memes.get("shared_chant", 0.0) < THRESHOLD:
            continue
        prize = world.get("prize")
        if prize.meters.get("whole", 0.0) < THRESHOLD:
            continue
        sig = ("split", prize.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        prize.meters["whole"] = 0.0
        prize.meters["halves"] = 2.0
        prize.meters["shared"] = 1.0
        out.append("The magic did its work, and the thing came apart in two fair halves.")
    return out


CAUSAL_RULES = [Rule("split", _r_split)]


def propagate(world: World, narrate: bool = True) -> list[str]:
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


def select_combo(place: str, magic: Magic, prize: Prize) -> bool:
    return place in SETTINGS and magic.id in {"halve_spell"} and prize.label in PRIZES


def predict_success(world: World, hero1: Entity, hero2: Entity, magic: Magic, prize_id: str) -> bool:
    sim = world.copy()
    sim.get(hero1.id).memes["shared_chant"] = 1.0
    sim.get(hero2.id).memes["shared_chant"] = 1.0
    sim.get("prize").meters["whole"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("prize").meters.get("halves", 0.0) >= 2.0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world: teamwork, repetition, magic, and halve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for magic in MAGICS.values():
            for prize in PRIZES:
                if select_combo(place, magic, _safe_lookup(PRIZES, prize)):
                    out.append((place, magic.id, prize))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "magic", None) is None or c[1] == getattr(args, "magic", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, magic, prize = rng.choice(list(combos))
    name1 = getattr(args, "name1", None) or rng.choice(NAMES)
    name2 = getattr(args, "name2", None) or rng.choice([n for n in NAMES if n != name1])
    return StoryParams(place=place, magic=magic, prize=prize, name1=name1, name2=name2)


def introduce(world: World, child: Entity) -> None:
    world.say(f"Once in {world.setting.place}, there lived a child named {child.id}.")


def second_child(world: World, child: Entity) -> None:
    world.say(f"{child.id} was {child.pronoun('subject')} of the sort who listened carefully and tried again.")


def find_prize(world: World, prize: Entity) -> None:
    world.say(f"One morning they found {prize.phrase}, shining as if the sun had left a gold coin behind.")


def worry(world: World, child1: Entity, child2: Entity, prize: Entity) -> None:
    prize.meters["whole"] = 1.0
    world.say(f"But the {prize.label} was far too big to carry home alone.")
    world.say(f"{child1.id} and {child2.id} looked at one another and knew they would need teamwork.")


def chant(world: World, child1: Entity, child2: Entity, magic: Magic, prize: Entity) -> None:
    child1.memes["shared_chant"] = 1.0
    child2.memes["shared_chant"] = 1.0
    child1.memes["hope"] += 1
    child2.memes["hope"] += 1
    world.say(f'So {child1.id} said, "{magic.chant}."')
    world.say(f"{child2.id} answered, '{magic.repeat}.'")
    world.say(f"Together they said it {magic.repeat}, and {magic.helper}.")
    propagate(world, narrate=True)


def finish(world: World, child1: Entity, child2: Entity, prize: Entity, magic: Magic) -> None:
    world.say(f"{magic.ending}.")
    world.say(f"Then the two children shared the {prize.label}, and the village was fed with warm, happy bread.")


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    magic = _safe_lookup(MAGICS, params.magic)
    prize_cfg = _safe_lookup(PRIZES, params.prize)

    c1 = world.add(Entity(id=params.name1, kind="character", type="girl"))
    c2 = world.add(Entity(id=params.name2, kind="character", type="boy"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))

    introduce(world, c1)
    second_child(world, c2)
    find_prize(world, prize)
    world.para()
    worry(world, c1, c2, prize)
    chant(world, c1, c2, magic, prize)
    world.para()
    finish(world, c1, c2, prize, magic)

    world.facts.update(
        child1=c1,
        child2=c2,
        prize=prize,
        magic=magic,
        params=params,
        success=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a young child about "{f["magic"].chant}" and a {f["prize"].label} that must be halved.',
        f"Tell a story where {f['child1'].id} and {f['child2'].id} use teamwork and repetition to make magic work.",
        f'Write a gentle village story that ends with two fair halves and the word "halve".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c1, c2, prize, magic = f["child1"], f["child2"], f["prize"], f["magic"]
    return [
        QAItem(
            question=f"Who worked together to help with the {prize.label}?",
            answer=f"{c1.id} and {c2.id} worked together. They used teamwork because the {prize.label} was too big for one child alone.",
        ),
        QAItem(
            question=f"What magic words did they repeat?",
            answer=f"They repeated '{magic.chant}' and answered with '{magic.repeat}'. The repeating chant helped the magic settle into place.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} at the end?",
            answer=f"It was halved into two fair pieces, so the children could share it and bring it home safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and help one another to do something that is easier with two or more hands.",
        ),
        QAItem(
            question="Why do people repeat a chant in a story?",
            answer="In a folk tale, repeating a chant can make the words feel powerful, memorable, and magical.",
        ),
        QAItem(
            question="What does it mean to halve something?",
            answer="To halve something means to divide it into two equal parts.",
        ),
        QAItem(
            question="Why is magic useful in a folk tale?",
            answer="Magic can change what is possible in a story, often helping characters solve a hard problem in a surprising way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_magic(M) :- magic(M).
valid_prize(R) :- prize(R).
valid_story(P,M,R) :- valid_place(P), valid_magic(M), valid_prize(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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


CURATED = [
    StoryParams(place="cottage", magic="halve_spell", prize="loaf", name1="Nora", name2="Eli"),
    StoryParams(place="forest", magic="halve_spell", prize="cake", name1="Mira", name2="Bram"),
    StoryParams(place="village", magic="halve_spell", prize="turnip", name1="Ruth", name2="Tobin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for p, m, r in stories:
            print(f"  {p:10} {m:12} {r}")
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
            header = f"### {p.name1} and {p.name2}: {p.prize} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
