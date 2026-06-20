#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bale_stub_lesson_learned_bedtime_story.py
=========================================================================

A small bedtime-style storyworld about a child, a hay bale, a stubbed toe,
and a gentle lesson learned.

Premise:
- A child wants to make a cozy bedtime play-space with a hay bale.
- The room is dim, and a stubbed toe turns the game from exciting to upset.
- A calm grown-up helps, the child learns to clear the path and use a safer
  light, and bedtime ends warm and peaceful.

The story is intentionally simple and state-driven: physical meters track the
bale and the toe-stub injury, while emotional memes track worry, comfort, pride,
and the lesson learned. The ending image proves what changed: the path is clear,
the child is calm, and bedtime is ready.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    dim: str
    bedtime: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    in_place: str
    shape: str
    hard: bool = False
    soft: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Lesson:
    id: str
    sense: int
    action: str
    fix: str
    closing: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    setting: str
    bale: str
    stub: str
    lesson: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["hurt"] >= THRESHOLD and ("worry", "child") not in world.fired:
        world.fired.add(("worry", "child"))
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_comfort(world: World) -> list[str]:
    out = []
    child = world.get("child")
    parent = world.get("parent")
    if child.memes["worry"] < THRESHOLD or ("comfort", "child") in world.fired:
        return out
    world.fired.add(("comfort", "child"))
    parent.memes["comfort"] += 1
    child.memes["comfort"] += 1
    out.append("__comfort__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("comfort", "social", _r_comfort)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def lesson_possible(lesson: Lesson, bale: ObjectCfg, stub: ObjectCfg) -> bool:
    return lesson.sense >= 2 and bale.hard and stub.soft


def choose_lesson() -> Lesson:
    return LESSONS["nightlight"]


def bump_stub(world: World, child: Entity, stub: Entity) -> None:
    child.meters["hurt"] += 1
    child.memes["surprise"] += 1
    stub.meters["bumped"] += 1
    propagate(world, narrate=False)


def calm_fix(world: World, parent: Entity, child: Entity, lesson: Lesson) -> None:
    child.memes["calm"] += 1
    parent.memes["calm"] += 1
    world.say(
        f'{parent.label_word.capitalize()} sat beside {child.id} and said, '
        f'"That was a good lesson to learn. {lesson.fix}."'
    )


def clean_path(world: World, child: Entity, bale: Entity, stub: Entity) -> None:
    child.memes["pride"] += 1
    child.meters["hurt"] = 0.0
    bale.meters["moved"] += 1
    stub.meters["covered"] += 1
    world.say(
        f"{child.id} carefully moved the {bale.label} to the side and tucked "
        f"a soft rug over the {stub.label}."
    )


def bedtime_close(world: World, child: Entity, parent: Entity, setting: Setting, lesson: Lesson) -> None:
    child.memes["safety"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"After that, the room felt peaceful again. {setting.bedtime} {lesson.closing} "
        f"{child.id} climbed into bed with a small smile."
    )


def tell(setting: Setting, bale: ObjectCfg, stub: ObjectCfg, lesson: Lesson,
         child_name: str = "Mila", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type,
                              role="parent", label="the parent"))
    bale_ent = world.add(Entity(id="bale", type="thing", label=bale.label,
                                attrs={"shape": bale.shape}, hard=bale.hard))
    stub_ent = world.add(Entity(id="stub", type="thing", label=stub.label,
                                attrs={"shape": stub.shape}, soft=stub.soft))

    child.memes["curiosity"] = 1
    parent.memes["calm"] = 1

    world.say(
        f"At {setting.place}, {child.id} wanted one last cozy game before bed."
    )
    world.say(
        f"{child.id} saw {bale.phrase} near the dim corner and thought it would "
        f"make a perfect little hideout."
    )
    world.say(
        f"But the floor had a {stub.label} tucked in the shadow, and the room was "
        f"sleepy-dark."
    )

    world.para()
    child.memes["want"] += 1
    world.say(
        f'{child.id} tiptoed toward the bale, then winced hard. "{lesson.action}," '
        f'{child.pronoun()} whispered.'
    )
    bump_stub(world, child, stub_ent)
    world.say(
        f"{child.id} hugged {child.pronoun('possessive')} foot and looked up, a little teary."
    )

    world.para()
    calm_fix(world, parent, child, lesson)
    clean_path(world, child, bale_ent, stub_ent)
    bedtime_close(world, child, parent, setting, lesson)

    world.facts.update(
        child=child,
        parent=parent,
        bale=bale_ent,
        stub=stub_ent,
        setting=setting,
        lesson=lesson,
        hurt=child.meters["hurt"] >= THRESHOLD,
        lesson_learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "barn": Setting("barn", "the little barn room", "dim", "The lamp glowed low by the quilt.",
                    tags={"barn", "bedtime"}),
    "loft": Setting("loft", "the warm loft", "dim", "The blanket was already fluffed on the bed.",
                    tags={"loft", "bedtime"}),
}

BALES = {
    "hay": ObjectCfg("hay", "hay bale", "a hay bale by the wall", "near the bed", "round", hard=True,
                     tags={"bale", "hay"}),
    "straw": ObjectCfg("straw", "straw bale", "a straw bale under the window", "near the chair", "square",
                       hard=True, tags={"bale", "straw"}),
}

STUBS = {
    "toy": ObjectCfg("toy", "stubbed toe", "a tiny toy stump on the floor", "on the floor", "stub", soft=True,
                     tags={"stub", "toe"}),
    "bench": ObjectCfg("bench", "bench leg", "a short bench leg in the dark", "by the rug", "stub", soft=False,
                      tags={"stub"}),
}

LESSONS = {
    "nightlight": Lesson("nightlight", 3, "That floor had a sneaky little stub",
                         "They turned on the nightlight and made the path clear before playing again",
                         "Now the path glowed soft and safe, and bedtime felt easy again.",
                         tags={"lesson", "bedtime"}),
    "careful_steps": Lesson("careful_steps", 2, "That was a hard little stub",
                            "They slowed down, used the lamp, and moved the bale first",
                            "Now every step was careful, and the room stayed cozy.",
                            tags={"lesson", "bedtime"}),
}

GIRL_NAMES = ["Mila", "Nina", "Lena", "Ada", "Ruby"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Finn", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for bid, b in BALES.items():
            for tid, t in STUBS.items():
                if lesson_possible(choose_lesson(), b, t):
                    combos.append((sid, bid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: bale, stub, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bale", choices=BALES)
    ap.add_argument("--stub", choices=STUBS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    return "(No story: this bedtime setup has no sensible lesson to learn.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lesson and args.lesson not in LESSONS:
        raise StoryError("(No story: unknown lesson.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.bale is None or c[1] == args.bale)
              and (args.stub is None or c[2] == args.stub)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, bale, stub = rng.choice(sorted(combos))
    lesson = args.lesson or "nightlight"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, bale, stub, lesson, name, gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "bale" and "stub".',
        f"Tell a gentle lesson-learned story where {f['child'].id} meets a {f['bale'].label} and a {f['stub'].label} near bedtime.",
        f"Write a cozy story where a child learns to be careful after stubbing a toe in the dim room.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, bale, stub, lesson = f["child"], f["parent"], f["bale"], f["stub"], f["lesson"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {child.pronoun('possessive')} {parent.label_word}."),
        ("What happened in the dim room?",
         f"{child.id} bumped into the {stub.label} and hurt {child.pronoun('possessive')} foot. That was the moment that changed the play time into a lesson."),
        ("What did the grown-up help with?",
         f"{parent.label_word.capitalize()} helped {child.id} calm down, move the {bale.label}, and make the path safe again."),
        ("What lesson did the child learn?",
         f"{lesson.fix}. That way, the room was safer before bedtime, and {child.id} could rest without worrying about the floor."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["bale"].tags) | set(f["stub"].tags) | set(f["lesson"].tags)
    qa = []
    if "bale" in tags:
        qa.append(("What is a bale?",
                    "A bale is a big bundled stack of hay or straw tied together so it stays in one shape."))
    if "stub" in tags:
        qa.append(("What does stubbed toe mean?",
                    "A stubbed toe means you hit your toe against something hard. It can hurt a lot for a little while."))
    if "lesson" in tags:
        qa.append(("Why is a lesson learned story helpful?",
                    "It helps children remember a safer choice for next time. The story shows what changed and why it matters."))
    return qa


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,B,T) :- setting(S), bale(B), stub(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BALES:
        lines.append(asp.fact("bale", bid))
    for tid in STUBS:
        lines.append(asp.fact("stub", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def tell_sample(params: StoryParams) -> World:
    return tell(SETTINGS[params.setting], BALES[params.bale], STUBS[params.stub],
                LESSONS[params.lesson], params.child_name, params.child_gender, params.parent_type)


def generate(params: StoryParams) -> StorySample:
    world = tell_sample(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("barn", "hay", "toy", "nightlight", "Mila", "girl", "mother"),
    StoryParams("loft", "straw", "bench", "careful_steps", "Owen", "boy", "father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
