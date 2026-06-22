#!/usr/bin/env python3
"""
storyworlds/worlds/chatter_kitchen_kindness_heartwarming.py
===========================================================

A small standalone storyworld set in a kitchen, built from a heartwarming seed
about chatter and kindness. The world simulates a child helping another person
in a busy kitchen, where the noisy chatter starts as a distraction and becomes
part of a gentle, shared solution.

The model tracks physical meters and emotional memes on typed entities. State
changes drive the prose: crumbs fall, tea cools, voices rise, kindness settles,
and the ending image proves what changed.

Seed tale:
---
In a kitchen full of chatter, a child notices a tired parent trying to finish
a small breakfast before work. The toaster is stuck, the spoon keeps slipping,
and the child wants to help. Instead of making a mess or arguing over the noise,
the child fetches a towel, slides a plate over, and tidies the counter. The
parent smiles, thanks the child, and the kitchen grows calm and warm again.
Kindness turns the chatter into a shared, happy moment.
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
    can_help: bool = False
    can_spill: bool = False
    can_noise: bool = False
    can_clean: bool = False
    can_share: bool = False

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


@dataclass
class KitchenScene:
    id: str
    name: str
    mood: str
    table: str
    counter: str
    sink: str
    breakfast: str
    tidy_image: str
    chatter_image: str
    can_steam: bool = True
    can_spill: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpfulThing:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)
    can_clean: bool = False
    can_share: bool = False


@dataclass
class Resolution:
    id: str
    sense: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out = []
    kitchen = world.facts.get("scene")
    if not kitchen:
        return out
    for ent in world.entities.values():
        if ent.meters["spilled"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kitchen.meters["mess"] += 1
        kitchen.meters["noise"] += 1
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["overwhelm"] += 1
        out.append("__spill__")
    return out


def _r_help(world: World) -> list[str]:
    out = []
    helper = world.facts.get("child")
    adult = world.facts.get("adult")
    if not helper or not adult:
        return out
    if helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("help", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    adult.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.facts["helped"] = True
    out.append("__help__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("help", _r_help)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for child in CHILDREN:
            for adult in ADULTS:
                combos.append((scene, child, adult))
    return combos


@dataclass
class StoryParams:
    scene: str
    child: str
    adult: str
    helper: str
    cleanup_tool: str
    resolution: str
    seed: Optional[int] = None


SCENES = {
    "kitchen": KitchenScene(
        id="kitchen",
        name="the kitchen",
        mood="busy and warm",
        table="the little table",
        counter="the counter",
        sink="the sink",
        breakfast="toast and jam",
        tidy_image="the counter shone again",
        chatter_image="the chatter bounced off the tiles",
        tags={"kitchen", "noise", "mess"},
    )
}

CHILDREN = {
    "Mila": Entity(
        id="Mila",
        kind="character",
        type="girl",
        role="child",
        traits=["kind", "curious"],
        can_help=True,
    ),
    "Ben": Entity(
        id="Ben",
        kind="character",
        type="boy",
        role="child",
        traits=["kind", "quick"],
        can_help=True,
    ),
}

ADULTS = {
    "Mom": Entity(
        id="Mom",
        kind="character",
        type="mother",
        role="adult",
        traits=["tired", "gentle"],
    ),
    "Dad": Entity(
        id="Dad",
        kind="character",
        type="father",
        role="adult",
        traits=["busy", "warm"],
    ),
}

HELPERS = {
    "towel": HelpfulThing(
        id="towel",
        label="towel",
        phrase="a clean towel",
        use="wipe up the spill",
        can_clean=True,
        tags={"towel", "clean"},
    ),
    "tray": HelpfulThing(
        id="tray",
        label="tray",
        phrase="a sturdy tray",
        use="carry breakfast safely",
        can_share=True,
        tags={"tray", "share"},
    ),
}

RESOLUTIONS = {
    "kind_help": Resolution(
        id="kind_help",
        sense=3,
        text="tidied the counter, slid a towel under the dripping mug, and "
             "helped carry the breakfast to the table",
        fail="tried to help, but the breakfast stayed messy",
        qa_text="tidied the counter and helped carry the breakfast to the table",
        tags={"kindness", "help", "towel", "tray"},
    )
}


def scene_entity(scene: KitchenScene) -> Entity:
    e = Entity(
        id=scene.id,
        kind="place",
        type="room",
        label=scene.name,
        traits=[scene.mood],
        can_spill=scene.can_spill,
    )
    e.meters["mess"] = 0.0
    e.meters["noise"] = 0.0
    return e


def setup_world(params: StoryParams) -> World:
    world = World()
    scene = scene_entity(SCENES[params.scene])
    world.add(scene)
    child = world.add(copy.deepcopy(CHILDREN[params.child]))
    adult = world.add(copy.deepcopy(ADULTS[params.adult]))
    helper = world.add(copy.deepcopy(HELPERS[params.helper]))
    tool = world.add(copy.deepcopy(HELPERS[params.cleanup_tool]))
    world.facts.update(
        scene=scene,
        child=child,
        adult=adult,
        helper=helper,
        cleanup_tool=tool,
        resolution=RESOLUTIONS[params.resolution],
        scene_cfg=SCENES[params.scene],
        helped=False,
    )
    child.memes["kindness"] = 1.0
    child.memes["curiosity"] = 1.0
    adult.memes["warmth"] = 1.0
    adult.memes["stress"] = 1.0
    return world


def introduce(world: World) -> None:
    scene = world.facts["scene_cfg"]
    child = world.facts["child"]
    adult = world.facts["adult"]
    helper = world.facts["helper"]
    world.say(
        f"In {scene.name}, there was chatter everywhere while {child.id} and "
        f"{adult.id} prepared {scene.breakfast}."
    )
    world.say(
        f"The chatter made the room feel lively, and {child.id} noticed that "
        f"{adult.id} looked a little tired."
    )
    world.say(
        f"{child.id} saw {helper.phrase} on the counter and wanted to help."
    )


def build_turn(world: World) -> None:
    scene = world.facts["scene_cfg"]
    child = world.facts["child"]
    adult = world.facts["adult"]
    helper = world.facts["helper"]
    child.memes["kindness"] += 1
    adult.memes["stress"] += 1
    world.say(
        f"Then the spoon slipped, and a small spill spread across {scene.counter}."
    )
    world.say(
        f'The kitchen got even busier, but {child.id} did not complain. '
        f'Instead, "{child.id}, would you hand me {helper.phrase}?" {adult.id} asked.'
    )
    world.say(
        f'{child.id} nodded at once. The chatter stayed soft, and kindness took the lead.'
    )


def resolve(world: World) -> None:
    scene = world.facts["scene_cfg"]
    child = world.facts["child"]
    adult = world.facts["adult"]
    helper = world.facts["cleanup_tool"]
    res = world.facts["resolution"]
    child.memes["kindness"] += 1
    child.meters["helped"] += 1
    world.get("kitchen").meters["mess"] += 1
    world.get("kitchen").meters["noise"] += 1
    world.say(
        f"{child.id} used {helper.phrase} to {res.text}."
    )
    world.say(
        f"{adult.id} smiled, thanked {child.id}, and the little kitchen felt calm again."
    )
    world.say(
        f"By the end, {scene.tidy_image}, and the chatter sounded happy instead of rushed."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    world.para()
    build_turn(world)
    world.para()
    resolve(world)
    return world


def knowledge_questions() -> dict[str, list[tuple[str, str]]]:
    return {
        "chatter": [(
            "What is chatter?",
            "Chatter is lots of quick talking or sound from voices. In a kitchen, it can make the room feel busy but also cheerful."
        )],
        "kindness": [(
            "What is kindness?",
            "Kindness means noticing what someone needs and helping in a gentle way. It can make a hard moment feel warmer and safer."
        )],
        "kitchen": [(
            "What is a kitchen for?",
            "A kitchen is a room where people make food, wash dishes, and share meals together."
        )],
        "towel": [(
            "What can a towel do in a kitchen?",
            "A towel can wipe up spills and dry wet things. It helps keep the counter clean."
        )],
        "tray": [(
            "Why use a tray?",
            "A tray helps carry things safely so they do not tip over or spill."
        )],
    }


def prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene_cfg"]
    child = f["child"]
    adult = f["adult"]
    return [
        f"Write a heartwarming story about chatter in {scene.name} where {child.id} helps {adult.id} with a small spill.",
        f"Tell a gentle kitchen story that includes the word chatter and shows kindness turning a busy moment into a happy one.",
        f"Write a child-friendly story set in a kitchen where someone notices a tired grown-up and helps with a towel or tray.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene = f["scene_cfg"]
    child = f["child"]
    adult = f["adult"]
    return [
        QAItem(
            question=f"Why did {child.id} decide to help in the kitchen?",
            answer=f"{child.id} saw that {adult.id} was tired and that the kitchen was getting messy. Kindness made {child.id} want to help right away.",
        ),
        QAItem(
            question=f"What changed after {child.id} brought the towel?",
            answer=f"The spill became easier to clean, and {adult.id} could finish breakfast without feeling so rushed. The kitchen grew calmer because the help was gentle and timely.",
        ),
        QAItem(
            question=f"How did the story end in {scene.name}?",
            answer=f"It ended with the counter tidy, {adult.id} smiling, and the chatter sounding cheerful instead of stressful. That ending shows kindness turning the whole morning warmer.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    items: list[QAItem] = []
    for tag, pairs in knowledge_questions().items():
        if tag == "chatter" or tag == "kindness" or tag == "kitchen":
            items.extend(QAItem(question=q, answer=a) for q, a in pairs)
    if world.facts["helper"].id == "towel":
        items.extend(QAItem(question=q, answer=a) for q, a in knowledge_questions()["towel"])
    if world.facts["cleanup_tool"].id == "tray":
        items.extend(QAItem(question=q, answer=a) for q, a in knowledge_questions()["tray"])
    return items


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.kind != "place" and e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(scene: KitchenScene, helper: HelpfulThing) -> str:
    return f"(No story: {helper.label} does not fit this kitchen kindness scene.)"


def valid_story_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for c in CHILDREN:
            for a in ADULTS:
                combos.append((s, c, a))
    return combos


ASP_RULES = r"""
valid(S,C,A) :- scene(S), child(C), adult(A).
kind_help(C,A) :- child(C), adult(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid in CHILDREN:
        lines.append(asp.fact("child", cid))
    for aid in ADULTS:
        lines.append(asp.fact("adult", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_story_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming kitchen storyworld of chatter and kindness.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--cleanup-tool", choices=HELPERS, dest="cleanup_tool")
    ap.add_argument("--resolution", choices=RESOLUTIONS)
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
    combos = valid_story_combos()
    if args.scene or args.child or args.adult:
        combos = [
            c for c in combos
            if (args.scene is None or c[0] == args.scene)
            and (args.child is None or c[1] == args.child)
            and (args.adult is None or c[2] == args.adult)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, child, adult = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    cleanup_tool = args.cleanup_tool or rng.choice(sorted(HELPERS))
    resolution = args.resolution or "kind_help"
    return StoryParams(
        scene=scene,
        child=child,
        adult=adult,
        helper=helper,
        cleanup_tool=cleanup_tool,
        resolution=resolution,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.child not in CHILDREN:
        raise StoryError("Unknown child.")
    if params.adult not in ADULTS:
        raise StoryError("Unknown adult.")
    if params.helper not in HELPERS or params.cleanup_tool not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.resolution not in RESOLUTIONS:
        raise StoryError("Unknown resolution.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible kitchen story combos:")
        for s, c, a in asp_valid_combos():
            print(f"  {s:8} {c:8} {a}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for scene, child, adult in valid_story_combos():
            samples.append(generate(StoryParams(
                scene=scene,
                child=child,
                adult=adult,
                helper="towel",
                cleanup_tool="tray",
                resolution="kind_help",
            )))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
