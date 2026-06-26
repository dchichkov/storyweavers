#!/usr/bin/env python3
"""
storyworlds/worlds/duck_strong_dialogue_kindness_heartwarming.py
=================================================================

A heartwarming story world about a duck, strength, and kind dialogue.

Premise:
A small duck wants to do something brave and heavy on its own.

Tension:
The task is a little too hard, so the duck worries it is not strong enough.

Turn:
A friend speaks kindly, offers help, and the duck answers with honest words.

Resolution:
They solve the problem together, and the duck feels strong in a new way:
not only in muscles, but also in kindness and trust.

This world keeps the prose child-facing and concrete. The physical model tracks
weight, strain, and assistance. The emotional model tracks worry, courage,
kindness, and pride. Dialogue matters: the story changes because the characters
speak to each other gently and make a shared plan.

Seed words:
- duck
- strong

Features:
- Dialogue
- Kindness

Style:
- Heartwarming
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
    helper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    basket: object | None = None
    duck: object | None = None
    friend: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"duck", "girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Scene:
    place: str
    task: str
    goal: str
    heavy: bool
    kindness_tag: str
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
class StoryParams:
    scene: str
    duck_name: str
    friend_kind: str
    friend_name: str
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


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        other = World(self.scene)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


SCENES = {
    "pond": Scene(
        place="the pond",
        task="carry a basket of shiny reeds to the nest",
        goal="bring the reeds home",
        heavy=True,
        kindness_tag="help",
    ),
    "path": Scene(
        place="the muddy path",
        task="pull a little wheelbarrow full of apples",
        goal="get the apples to the pantry",
        heavy=True,
        kindness_tag="share",
    ),
    "dock": Scene(
        place="the wooden dock",
        task="drag a sailcloth into place",
        goal="cover the little boat",
        heavy=True,
        kindness_tag="lift",
    ),
}

DUCK_NAMES = ["Daisy", "Milo", "Pip", "Luna", "Penny", "Toby", "Clover", "Sunny"]
FRIEND_NAMES = ["Nia", "Bea", "Ollie", "Sam", "Jun", "Iris", "Noah", "Mina"]
FRIEND_KINDS = ["swan", "otter", "goose", "rabbit", "turtle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming duck story world.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--duck-name")
    ap.add_argument("--friend-kind", choices=FRIEND_KINDS)
    ap.add_argument("--friend-name")
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


def _valid_combo(scene: Scene) -> bool:
    return scene.heavy


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scene = getattr(args, "scene", None) or rng.choice(list(SCENES))
    if not _valid_combo(_safe_lookup(SCENES, scene)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    duck_name = getattr(args, "duck_name", None) or rng.choice(DUCK_NAMES)
    friend_kind = getattr(args, "friend_kind", None) or rng.choice(FRIEND_KINDS)
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(scene=scene, duck_name=duck_name, friend_kind=friend_kind, friend_name=friend_name)


def _story_intro(world: World, duck: Entity, friend: Entity, basket: Entity) -> None:
    scene = world.scene
    world.say(
        f"{duck.id} was a small duck who wanted to be strong enough to do big jobs."
    )
    world.say(
        f"One morning at {scene.place}, {duck.id} looked at {basket.phrase} and said, "
        f"\"I can do this all by myself.\""
    )
    world.say(
        f"{friend.id} smiled and said, \"You are already brave, and bravery can ask for help.\""
    )


def _strain_task(world: World, duck: Entity, basket: Entity) -> None:
    duck.meters["strain"] += 1
    duck.memes["worry"] += 1
    basket.meters["load"] += 1
    world.say(
        f"{duck.id} tried to {world.scene.task}, but the load felt too heavy."
    )
    world.say(
        f"\"I'm not strong enough,\" {duck.pronoun('subject')} whispered."
    )


def _kind_reply(world: World, friend: Entity, duck: Entity) -> None:
    friend.memes["kindness"] += 1
    duck.memes["courage"] += 1
    world.say(
        f"{friend.id} paddled closer and said, \"You do not have to do it alone.\""
    )
    world.say(
        f"\"Will you stay with me?\" {duck.id} asked."
    )
    world.say(
        f"\"Of course,\" {friend.id} said. \"We can be strong together.\""
    )


def _shared_solution(world: World, duck: Entity, friend: Entity, basket: Entity) -> None:
    duck.memes["joy"] += 1
    friend.memes["joy"] += 1
    duck.memes["worry"] = 0
    basket.meters["load"] = 0
    world.say(
        f"So {duck.id} took one handle and {friend.id} took the other."
    )
    world.say(
        f"They lifted the basket together and carried it all the way to the nest."
    )
    world.say(
        f"{duck.id} laughed and said, \"I feel strong now.\""
    )
    world.say(
        f"{friend.id} answered, \"You were strong when you asked kindly, too.\""
    )


def tell(scene: Scene, duck_name: str, friend_kind: str, friend_name: str) -> World:
    world = World(scene)
    duck = world.add(Entity(id=duck_name, kind="character", type="duck"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_kind))
    basket = world.add(Entity(
        id="basket",
        type="basket",
        label="basket",
        phrase=f"a basket full of shiny reeds",
        owner=duck.id,
    ))

    world.say(
        f"{duck.id} found {basket.phrase} near {scene.place}."
    )
    _story_intro(world, duck, friend, basket)
    world.para()
    _strain_task(world, duck, basket)
    _kind_reply(world, friend, duck)
    world.para()
    _shared_solution(world, duck, friend, basket)

    world.facts = {
        "duck": duck,
        "friend": friend,
        "basket": basket,
        "scene": scene,
    }
    return world


SETTINGS = SCENES


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for scene_name in SETTINGS:
        for friend_kind in FRIEND_KINDS:
            out.append((scene_name, "duck", friend_kind))
    return out


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SCENES, params.scene), params.duck_name, params.friend_kind, params.friend_name)
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
    duck = _safe_fact(world, f, "duck")
    friend = _safe_fact(world, f, "friend")
    scene = _safe_fact(world, f, "scene")
    return [
        f'Write a heartwarming story about a duck named {duck.id} who wants to be strong at {scene.place}.',
        f'Write a short child-friendly story where {duck.id} and {friend.id} use kind dialogue to solve a heavy problem.',
        f"Tell a simple story in which a duck learns that being strong can include asking for help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    duck: Entity = _safe_fact(world, f, "duck")
    friend: Entity = _safe_fact(world, f, "friend")
    scene: Scene = _safe_fact(world, f, "scene")
    return [
        QAItem(
            question=f"What did {duck.id} want to do at {scene.place}?",
            answer=f"{duck.id} wanted to {scene.task} and be strong enough to do it.",
        ),
        QAItem(
            question=f"Why did {duck.id} feel worried?",
            answer=f"{duck.id} felt worried because the task was heavy and seemed too hard to do alone.",
        ),
        QAItem(
            question=f"What kind thing did {friend.id} say to {duck.id}?",
            answer=f"{friend.id} said that {duck.id} did not have to do it alone and that they could be strong together.",
        ),
        QAItem(
            question=f"How did {duck.id} and {friend.id} finish the job?",
            answer=f"They shared the load, lifted it together, and carried it to {scene.place} successfully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be strong?",
            answer="Being strong means having enough power to do hard things, and it can also mean being brave and steady.",
        ),
        QAItem(
            question="Why is kindness important in a conversation?",
            answer="Kindness helps people feel safe, heard, and willing to work together.",
        ),
        QAItem(
            question="Why can two helpers be better than one?",
            answer="Two helpers can share a heavy job, so each one carries less and the job feels easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Scene, duck, FriendKind) :- scene(Scene), friend_kind(FriendKind).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for scene_name in SETTINGS:
        lines.append(asp.fact("scene", scene_name))
    for fk in FRIEND_KINDS:
        lines.append(asp.fact("friend_kind", fk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(scene="pond", duck_name="Daisy", friend_kind="otter", friend_name="Nia"),
    StoryParams(scene="path", duck_name="Pip", friend_kind="goose", friend_name="Bea"),
    StoryParams(scene="dock", duck_name="Luna", friend_kind="turtle", friend_name="Iris"),
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.duck_name} in {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
