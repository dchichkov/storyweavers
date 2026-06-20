#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/excite_functional_bad_ending_inner_monologue_heartwarming.py
=============================================================================================

A small storyworld about a child, a cherished little project, and a warmly told
bad ending with inner monologue.

Premise
-------
A child is excited to make something functional for someone they love. The
work almost succeeds, but a hidden flaw makes the result fail at the end. The
story stays heartwarming because the child cares, thinks through the problem in
their head, and tries kindly to help anyway.

This world is self-contained and stdlib-only, with a Python reasonableness gate
and an inline ASP twin for parity checks.
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
from typing import Optional

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
    age: int = 0
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
class Item:
    id: str
    label: str
    function: str
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Fix:
    id: str
    label: str
    power: int
    text: str
    fail: str
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
class Scene:
    id: str
    place: str
    opening: str
    need: str
    ending_image: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
@dataclass
class StoryParams:
    scene: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    item: str
    fix: str
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


SCENES = {
    "rainy_window": Scene(
        "rainy_window",
        "the window seat",
        "The rain tapped the glass while the room smelled like warm toast and crayons.",
        "The child wanted to help someone see the garden from the window seat.",
        "At the end, the little helper sat by the window with a brave, soft smile.",
        {"rain", "window"},
    ),
    "broken_box": Scene(
        "broken_box",
        "the kitchen table",
        "Sunlight lay across the kitchen table, and a half-finished project waited there.",
        "The child wanted the project to be functional before dinner.",
        "At the end, the table was still tidy, but the project was not the one they hoped for.",
        {"kitchen", "project"},
    ),
    "night_light": Scene(
        "night_light",
        "the bedside rug",
        "A lamp glowed gently while the hallway stayed quiet and sleepy.",
        "The child wanted to make the night more comfortable for a loved one.",
        "At the end, the room held a small, tender quiet instead of a happy fix.",
        {"night", "lamp"},
    ),
}

ITEMS = {
    "lamp": Item("lamp", "little lamp", "give light", fragile=True),
    "cart": Item("cart", "toy cart", "carry snacks", fragile=False),
    "button_box": Item("button_box", "button box", "make sounds", fragile=True),
}

FIXES = {
    "tape": Fix("tape", "tape", 2, "pressed the loose piece down with careful tape",
                "pressed on the loose piece, but it slipped free again", {"repair"}),
    "glue": Fix("glue", "glue", 3, "held the broken part still and mended it with glue",
                "used glue, but the crack stayed open", {"repair"}),
    "string": Fix("string", "string", 1, "tied the pieces together with string and a patient knot",
                  "tied it with string, but the knot would not hold", {"repair"}),
}

CHILD_NAMES = ["Mia", "Lina", "Noah", "Eli", "Ava", "June", "Owen", "Levi"]
HELPER_NAMES = ["Grandma", "Grandpa", "Mom", "Dad", "Aunt May", "Uncle Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for iid, item in ITEMS.items():
            if "project" in scene.tags and item.fragile:
                for fid in FIXES:
                    combos.append((sid, iid, fid))
            elif "window" in scene.tags and iid == "lamp":
                for fid in FIXES:
                    combos.append((sid, iid, fid))
            elif "night" in scene.tags and iid in {"lamp", "button_box"}:
                for fid in FIXES:
                    combos.append((sid, iid, fid))
    return combos


def reasonableness_gate(scene: Scene, item: Item) -> bool:
    return (scene.id == "broken_box" and item.fragile) or (
        scene.id == "rainy_window" and item.id == "lamp"
    ) or (scene.id == "night_light" and item.id in {"lamp", "button_box"})


def fix_succeeds(fix: Fix, item: Item) -> bool:
    return fix.power >= (3 if item.fragile else 2)


def outcome_of(params: StoryParams) -> str:
    return "bad_ending"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming bad-ending story world.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "woman", "man"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in CHILD_NAMES if n != avoid] if gender in {"girl", "boy"} else HELPER_NAMES
    if not pool:
        pool = CHILD_NAMES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.item and not reasonableness_gate(SCENES[args.scene], ITEMS[args.item]):
        raise StoryError("That item does not fit the scene well enough for a believable story.")
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.item is None or c[1] == args.item)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, item, fix = rng.choice(sorted(combos))
    cg = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, cg)
    hg = args.helper_gender or rng.choice(["woman", "man"])
    helper = args.helper or _pick_name(rng, "girl" if hg == "woman" else "boy")
    return StoryParams(scene, child, cg, helper, hg, item, fix)


def tell(scene: Scene, item: Item, fix: Fix, child: Entity, helper: Entity) -> World:
    world = World()
    world.add_entity(child)
    world.add_entity(helper)
    target = world.add_item(copy.deepcopy(item))
    child.memes["excitement"] += 1
    child.memes["love"] += 1
    child.memes["monologue"] += 1

    world.say(f"{scene.opening} {child.id} was excited to make {target.label} functional.")
    world.say(f"In {child.pronoun('possessive')} head, {child.id} thought, 'If this works, {helper.id} will smile so big.'")
    world.say(f"{child.id} wanted {target.label} to do {target.function}, because {scene.need}")

    world.para()
    world.say(f"{helper.id} watched kindly while {child.id} tried to fix the broken piece.")
    world.say(f"{child.id} carefully {fix.text}.")
    if fix_succeeds(fix, target):
        target.meters["working"] = 1
        child.memes["hope"] += 1
        world.say(f"For a tiny moment, the {target.label} seemed ready to help.")
    else:
        target.meters["working"] = 0
        target.meters["broken"] = 1
        world.say(f"For a tiny moment, it almost looked right.")

    world.para()
    if fix_succeeds(fix, target):
        world.say(f"Then the hidden crack gave way, and the {target.label} fell apart anyway.")
        world.say(f"{child.id}'s face went still. In {child.pronoun('possessive')} heart, {child.id} whispered, 'I tried so hard.'")
        world.say(f"{helper.id} hugged {child.id} close and said the gentle truth: sometimes caring is not the same as fixing.")
        world.say(f"{scene.ending_image} The best part was the hug, even though the little project did not last.")
    else:
        world.say(f"The piece never held, and the {target.label} stayed unusable.")
        world.say(f"{child.id} blinked fast and thought, 'Maybe love can be enough, even when the project fails.'")
        world.say(f"{helper.id} smiled with sad kindness and tucked the broken parts away.")
        world.say(f"{scene.ending_image} The room was quiet, and the unfinished work sat between them like a small rain cloud.")

    world.facts.update(
        scene=scene, item=target, fix=fix, child=child, helper=helper,
        outcome="bad_ending", success=fix_succeeds(fix, target)
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the words "excite" and "functional" about {f["child"].id} trying to help with a small fix.',
        f"Tell a gentle story where {f['child'].id} feels excited to make {f['item'].label} functional, but the ending is sad and kind.",
        f"Write a story with inner monologue in which a child thinks about fixing something for {f['helper'].id}, and the fix does not last.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, item = f["child"], f["helper"], f["item"]
    qs = [
        QAItem(
            question=f"Why was {child.id} so excited?",
            answer=f"{child.id} was excited because {child.pronoun('subject')} wanted to make the {item.label} functional for {helper.id}. In {child.pronoun('possessive')} head, that meant helping someone {child.id} cared about."
        ),
        QAItem(
            question=f"What did {child.id} think about while working?",
            answer=f"{child.id} thought that if the fix worked, {helper.id} would be happy. That hopeful inner thought kept {child.id} trying even when the job was hard."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly, because the fix did not last and the {item.label} still broke. Still, the ending stayed warm because {helper.id} hugged {child.id} and cared about the effort."
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does functional mean?",
               "Functional means something works the way it is supposed to. If a toy or tool is functional, it can do its job."),
        QAItem("What is an inner monologue?",
               "An inner monologue is the voice of thoughts inside someone's head. It is what a character thinks but does not say out loud."),
        QAItem("What does excite mean?",
               "To excite someone means to make them feel eager, lively, or thrilled about something."),
        QAItem("Why can a broken thing be disappointing?",
               "A broken thing cannot do its job, so the person who cared about it may feel sad or frustrated. Even then, kindness can still make the moment feel gentle."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) memes={dict(e.memes)}")
    for i in world.items.values():
        lines.append(f"  {i.id:8} (item   ) meters={dict(i.meters)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("broken_box", "Mia", "girl", "Mom", "woman", "button_box", "glue"),
    StoryParams("rainy_window", "Noah", "boy", "Grandma", "woman", "lamp", "tape"),
    StoryParams("night_light", "Ava", "girl", "Dad", "man", "button_box", "string"),
]


def explain_rejection(scene: Scene, item: Item) -> str:
    return f"(No story: {item.label} does not fit {scene.place} well enough for a believable setup.)"


ASP_RULES = r"""
valid(S, I, F) :- scene(S), item(I), fix(F), reasonable(S, I).
bad_ending(S, I, F) :- valid(S, I, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        for tag in sorted(scene.tags):
            lines.append(asp.fact("scene_tag", sid, tag))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.fragile:
            lines.append(asp.fact("fragile", iid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    for sid, iid, fid in valid_combos():
        lines.append(asp.fact("reasonable", sid, iid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH in the gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    scene = SCENES[params.scene]
    item = ITEMS[params.item]
    fix = FIXES[params.fix]
    child = Entity(params.child, kind="character", type=params.child_gender, role="child")
    helper = Entity(params.helper, kind="character", type=params.helper_gender, role="helper")
    world = tell(scene, item, fix, child, helper)
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
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
