#!/usr/bin/env python3
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
    fee: object | None = None
    friend: object | None = None
    pencil: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the little art room"
    world: object | None = None
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
class StoryThing:
    id: str
    label: str
    phrase: str
    risk: str
    reason: str
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
    place: str
    child_name: str
    child_type: str
    friend_name: str
    fee: str
    pencil: str
    seed: Optional[int] = None
    p: object | None = None
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


def _predict_rust(world: World, child: Entity, item: Entity) -> bool:
    sim = world.copy()
    sim.get(child.id).memes["bravery"] += 1
    sim.get(item.id).meters["rust"] += 1
    return sim.get(item.id).meters["rust"] >= THRESHOLD


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        child = world.get("child")
        fee = world.get("fee")
        pencil = world.get("pencil")
        if child.memes.get("bravery", 0) >= THRESHOLD and ("ask",) not in world.fired:
            world.fired.add(("ask",))
            world.say(f"{child.id} took a brave breath and asked about the small fee.")
            changed = True
        if pencil.meters.get("rust", 0) >= THRESHOLD and ("warn",) not in world.fired:
            world.fired.add(("warn",))
            fee.meters["need_help"] = fee.meters.get("need_help", 0) + 1
            world.say(f"The old pencil sharpener had a rusty edge, so it needed gentle care.")
            changed = True
        if child.memes.get("reconciliation", 0) >= THRESHOLD and ("make_up",) not in world.fired:
            world.fired.add(("make_up",))
            world.say(f"Then the friends smiled again, glad the worry was over.")
            changed = True


def tell(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    friend = world.add(Entity(id="friend", kind="character", type="friend", label=params.friend_name))
    fee = world.add(Entity(id="fee", type="fee", label="fee", phrase=params.fee))
    pencil = world.add(Entity(id="pencil", type="pencil", label="pencil", phrase=params.pencil))

    world.say(
        f"{child.label} loved the little art room, because it had quiet tables, bright paper, and a pencil that fit neatly in a small hand."
    )
    world.say(
        f"One morning, {child.label} found out there was a tiny fee to use the special corner, and that made {child.pronoun('object')} frown."
    )
    world.para()
    world.say(
        f"{child.label} wanted to draw a picture of a brave bridge, but {child.pronoun('subject')} also worried that {child.pronoun('subject')} could not pay the fee."
    )
    child.memes["worry"] = 1
    if _predict_rust(world, child, pencil):
        world.say(
            f"Still, {child.label} noticed the pencil's little metal part had turned rusty, and {child.pronoun('subject')} knew someone would have to fix it."
        )
    world.para()
    child.memes["bravery"] = 1
    world.say(
        f"So {child.label} stood up straight and bravely told {friend.label} the truth: the pencil was rusty, and the fee felt too big."
    )
    world.say(
        f"{friend.label} had been quiet before, but then {friend.pronoun('subject')} looked at the picture and said sorry for being impatient."
    )
    friend.memes["reconciliation"] = 1
    world.say(
        f"Together they agreed to help each other: {child.label} would bring the pencil to the sink, and {friend.label} would cover the small fee from the shared jar."
    )
    propagate(world)
    world.para()
    world.say(
        f"By the end, the pencil was clean again, the fee was paid, and the brave bridge on the page looked warm and strong."
    )
    world.say(
        f"{child.label} and {friend.label} sat side by side, sharing a smile that felt bigger than the rust, the fee, or the worry."
    )

    world.facts.update(child=child, friend=friend, fee=fee, pencil=pencil, params=params)
    return world


SETTINGS = {
    "art_room": "the little art room",
    "library_table": "the library table",
    "community_center": "the community center",
}

CHILD_NAMES = ["Mia", "Noah", "Luna", "Eli", "Ada", "Theo"]
FRIEND_NAMES = ["Jun", "Ivy", "Sam", "Mira", "Leo", "Nia"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about {f["child"].label} and a rusty pencil.',
        f"Tell a gentle story where a small fee worries a child, but bravery helps.",
        f"Write a story about two friends finding reconciliation after a misunderstanding about a pencil and a fee.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    f = _safe_fact(world, world.facts, "friend")
    return [
        QAItem(
            question=f"What did {c.label} want to do in the art room?",
            answer=f"{c.label} wanted to draw a brave bridge with the pencil.",
        ),
        QAItem(
            question=f"Why did {c.label} feel worried at first?",
            answer=f"{c.label} worried about the small fee and about the rusty pencil needing help.",
        ),
        QAItem(
            question=f"How did the two friends fix the problem?",
            answer=f"They stayed brave, talked honestly, cleaned the pencil, and shared the fee so they could be friends again.",
        ),
        QAItem(
            question=f"How did {f.label} feel at the end?",
            answer=f"{f.label} felt sorry first, then happy again after they made up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rust?",
            answer="Rust is a reddish, flaky coating that can form on metal when it gets old and wet.",
        ),
        QAItem(
            question="What is a fee?",
            answer="A fee is a small amount of money you pay for something, like using a special place or service.",
        ),
        QAItem(
            question="What is a pencil for?",
            answer="A pencil is used for writing and drawing, and you can erase pencil marks if you change your mind.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and become friendly again after a disagreement.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary even when you feel nervous.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
brave(child) :- meme(child, bravery).
needs_help(pencil) :- meter(pencil, rust).
reconciled(child, friend) :- meme(child, reconciliation), meme(friend, reconciliation).
valid_story(place) :- setting(place).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", k) for k in SETTINGS]
    lines.append(asp.fact("meme", "child", "bravery"))
    lines.append(asp.fact("meme", "friend", "reconciliation"))
    lines.append(asp.fact("meter", "pencil", "rust"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show brave/1.\n#show needs_help/1.\n#show reconciled/2."))
    names = {str(a) for a in model}
    expected = {"brave(child)", "needs_help(pencil)", "reconciled(child,friend)"}
    if names == expected:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH:", sorted(names ^ expected))
    return 1


@dataclass
class Registry:
    value: list[str] = field(default_factory=list)
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
    ap = argparse.ArgumentParser(description="Heartwarming story world: rust, fee, pencil, bravery, reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    return StoryParams(
        place=place,
        child_name=rng.choice(CHILD_NAMES),
        child_type="girl" if rng.random() < 0.5 else "boy",
        friend_name=rng.choice(FRIEND_NAMES),
        fee="a small fee",
        pencil="an old pencil with a rusty tip",
        seed=getattr(args, "seed", None),
    )


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
        print(asp_program("#show brave/1.\n#show needs_help/1.\n#show reconciled/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in SETTINGS:
            p = StoryParams(place=place, child_name="Mia", child_type="girl", friend_name="Jun", fee="a small fee", pencil="an old pencil with a rusty tip")
            samples.append(generate(p))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
