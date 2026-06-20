#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tomorrow_surprise_happy_ending_transformation_bedtime_story.py
================================================================================================

A tiny bedtime storyworld about a child, a promised tomorrow surprise, and a
gentle transformation that makes the night feel safe and magical.

The domain is intentionally small: a child, a parent, a bedtime object, and a
surprise that arrives tomorrow. The simulated state matters: the child begins
sleepy and curious, the parent promises a surprise, the child waits, and on
tomorrow the surprise transforms the ordinary bedtime object into something cozy
and comforting.

The story aims for a bedtime-story tone: soft, concrete, child-facing, and
calmly happy.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    pronoun_kind: str = "it"
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.pronoun_kind == "she":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.pronoun_kind == "he":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Surprise:
    id: str
    label: str
    promise: str
    reveal: str
    transforms_into: str
    glow: str
    comfort: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    bedtime_object: str
    surprise: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_tomorrow(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    room = world.get("room")
    if child.memes["waiting"] >= THRESHOLD and (("tomorrow",) not in world.fired):
        world.fired.add(("tomorrow",))
        child.memes["hope"] += 1
        room.meters["night"] = 0.0
        out.append("__tomorrow__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    surprise = world.get("surprise")
    object_ent = world.get("bedtime_object")
    if surprise.memes["revealed"] >= THRESHOLD and ("transform",) not in world.fired:
        world.fired.add(("transform",))
        object_ent.label = surprise.attrs["transformed_label"]
        object_ent.traits.append("glowing")
        object_ent.meters["cozy"] += 1
        out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("tomorrow", _r_tomorrow), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(surprise: Surprise, child_name: str, child_gender: str,
         parent_name: str, parent_gender: str, bedtime_object_label: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type="child",
                             pronoun_kind=child_gender, role="child",
                             traits=["sleepy", "curious"]))
    parent = world.add(Entity(id=parent_name, kind="character", type="parent",
                              pronoun_kind=parent_gender, role="parent",
                              label="the parent"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    obj = world.add(Entity(id="bedtime_object", type="thing",
                           label=bedtime_object_label, attrs={"base_label": bedtime_object_label}))
    s = world.add(Entity(id="surprise", type="thing", label=surprise.label,
                         attrs={"transformed_label": surprise.transforms_into}))
    child.memes["sleepy"] = 1.0
    child.memes["curious"] = 1.0
    room.meters["night"] = 1.0

    world.say(
        f"At bedtime, {child.id} curled up under the blanket and looked at {obj.label_word}."
    )
    world.say(
        f'{parent.id} smiled and whispered, "Tomorrow I have a surprise for you."'
    )
    world.say(
        f"{child.id} yawned, but the promise made {child.pronoun('possessive')} eyes bright."
    )

    world.para()
    child.memes["waiting"] += 1
    world.say(
        f"{child.id} waited very patiently. All through the quiet night, {child.id} "
        f"kept thinking about {surprise.label}."
    )

    world.para()
    surprise.memes["revealed"] += 1
    child.memes["joy"] += 1
    world.say(
        f"Then tomorrow came, and {parent.id} brought out {surprise.promise}."
    )
    world.say(
        f"{surprise.reveal} It was a lovely change, soft and warm and made just for bedtime."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{child.id} smiled a big sleepy smile and hugged {parent.pronoun('object')}."
    )
    world.say(
        f"Now {obj.label_word} was {object_ent.label_word}, and the room glowed with a cozy light."
    )
    world.say(
        f"{child.id} drifted off happily, feeling safe, loved, and ready for sweet dreams."
    )

    world.facts.update(
        child=child,
        parent=parent,
        surprise=s,
        bedtime_object=obj,
        surprise_cfg=surprise,
        outcome="happy",
        transformed=obj.label != bedtime_object_label,
    )
    return world


THEMES = {
    "moonflower": Surprise(
        "moonflower",
        "a tiny seed packet",
        "a tiny seed packet",
        "Inside was a moonflower seed.",
        "the seed grew into a glowing moonflower lamp",
        "glowed like a little moon",
        "it made the room feel warm and safe",
        tags={"surprise", "tomorrow", "transformation", "bedtime"},
    ),
    "nightlight": Surprise(
        "nightlight",
        "a wrapped nightlight",
        "a wrapped nightlight",
        "Inside was a small shape with a ribbon.",
        "the little plain lamp turned into a star-shaped nightlight",
        "shone softly like a star",
        "it chased away the dark corners",
        tags={"surprise", "tomorrow", "transformation", "bedtime"},
    ),
    "blanket": Surprise(
        "blanket",
        "a folded blanket",
        "a folded blanket",
        "Inside was a secret note and a ribbon.",
        "the blanket turned into a patchwork cuddle blanket",
        "felt like a warm hug",
        "it made bedtime extra cozy",
        tags={"surprise", "tomorrow", "transformation", "bedtime"},
    ),
}

CHILD_NAMES = ["Mia", "Lily", "Noah", "Eli", "Ava", "Theo"]
PARENT_NAMES = ["Mom", "Dad", "Mama", "Papa"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for child in CHILD_NAMES:
        for sid in THEMES:
            for base in ["pillow", "lamp", "blanket"]:
                combos.append((child, sid, base))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld about tomorrow's surprise.")
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--surprise", choices=THEMES)
    ap.add_argument("--bedtime-object", choices=["pillow", "lamp", "blanket"])
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


def explain_rejection() -> str:
    return "(No story: this bedtime surprise would not make a clear transformation.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surprise and args.surprise not in THEMES:
        raise StoryError(explain_rejection())
    surprise = args.surprise or rng.choice(sorted(THEMES))
    child = args.child or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    bed = args.bedtime_object or rng.choice(["pillow", "lamp", "blanket"])
    gender = rng.choice(["she", "he"])
    parent_gender = "she" if parent in {"Mom", "Mama"} else "he"
    return StoryParams(child=child, child_gender=gender, parent=parent,
                       parent_gender=parent_gender, bedtime_object=bed,
                       surprise=surprise)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.surprise], params.child, params.child_gender,
                 params.parent, params.parent_gender, params.bedtime_object)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    surprise = f["surprise_cfg"]
    return [
        f"Write a bedtime story that includes the word tomorrow and ends with a happy surprise.",
        f"Tell a gentle story where {f['child'].id} waits for {surprise.label} and the ordinary bedtime object transforms into something cozy.",
        f"Write a soft story for a child about tomorrow, surprise, and transformation.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    surprise = f["surprise_cfg"]
    obj = f["bedtime_object"]
    return [
        ("What did the parent promise?",
         f"{parent.id} promised a surprise for tomorrow, so {child.id} had something sweet to think about at bedtime."),
        ("What happened tomorrow?",
         f"{surprise.reveal} The surprise transformed the ordinary bedtime object into something cozy and magical."),
        ("How did the story end?",
         f"It ended happily, with {child.id} feeling safe, loved, and sleepy in the glowing room."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["surprise_cfg"].tags)
    return [
        ("What does tomorrow mean?",
         "Tomorrow means the day after today. It is the next day you will wake up to."),
        ("What is a surprise?",
         "A surprise is something unexpected that makes someone wonder and smile."),
        ("What is a transformation?",
         "A transformation is when something changes into something new."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
surprise(S) :- theme(S).
valid(C, S, B) :- child(C), surprise(S), base(B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for c in CHILD_NAMES:
        lines.append(asp.fact("child", c))
    for s in THEMES:
        lines.append(asp.fact("theme", s))
    for b in ["pillow", "lamp", "blanket"]:
        lines.append(asp.fact("base", b))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            child=None, parent=None, surprise=None, bedtime_object=None
        ), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


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
    StoryParams("Mia", "she", "Mom", "she", "pillow", "moonflower"),
    StoryParams("Noah", "he", "Dad", "he", "lamp", "nightlight"),
    StoryParams("Ava", "she", "Mama", "she", "blanket", "blanket"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
