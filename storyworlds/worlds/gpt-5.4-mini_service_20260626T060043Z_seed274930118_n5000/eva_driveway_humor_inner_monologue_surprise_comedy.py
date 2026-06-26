#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/eva_driveway_humor_inner_monologue_surprise_comedy.py
===============================================================================================================================

A small comedic storyworld about Eva in the driveway.

Premise:
- Eva is trying to do a silly trick with a rolling toy in the driveway.
- She has an inner monologue that sounds much braver than she feels.
- A surprise makes the plan wobble, but the comedy ends in a friendly recovery.

The world is intentionally tiny: one child, one driveway, one prop, one surprise,
and a few state variables that drive the prose and Q&A.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    carried: bool = False
    broken: bool = False

    def __post_init__(self) -> None:
        for k in ("steady", "mess", "funny", "surprise", "relief", "worry", "pride"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)


@dataclass
class Setting:
    place: str = "the driveway"
    texture: str = "slightly sloped"
    noise: str = "a warm afternoon hum"


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Eva"
    prop: str = "scooter"
    surprise: str = "the little toy car in the driveway starts rolling by itself"
    helper: str = "Dad"
    weather: str = "sunny"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

SETTING = Setting()

PROPS = {
    "scooter": {
        "label": "scooter",
        "phrase": "a wobbly little scooter with one loud wheel",
        "risk": "wobble",
    },
    "wagon": {
        "label": "wagon",
        "phrase": "a red wagon that squeaked at every turn",
        "risk": "roll",
    },
    "ball": {
        "label": "ball",
        "phrase": "a bright ball that loved bouncing away",
        "risk": "bounce",
    },
}

SURPRISES = {
    "toy_car": {
        "text": "the little toy car in the driveway starts rolling by itself",
        "kind": "roll",
    },
    "dog": {
        "text": "the neighbor's tiny dog trots in and sniffs the prop",
        "kind": "sniff",
    },
    "breeze": {
        "text": "a sneaky breeze nudges the prop toward the street",
        "kind": "push",
    },
    "chalk": {
        "text": "a hidden rainbow of chalk appears under the wheels",
        "kind": "discover",
    },
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.
#show surprise_match/2.

valid(P, S) :- prop(P), surprise(S), compatible(P, S).
surprise_match(P, S) :- valid(P, S).

compatible(scooter, toy_car).
compatible(wagon, breeze).
compatible(ball, chalk).
compatible(wagon, toy_car).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PROPS:
        lines.append(asp.fact("prop", p))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    lines.append(asp.fact("compatible", "scooter", "toy_car"))
    lines.append(asp.fact("compatible", "wagon", "breeze"))
    lines.append(asp.fact("compatible", "ball", "chalk"))
    lines.append(asp.fact("compatible", "wagon", "toy_car"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_pairs())
    ap = set(asp_valid_pairs())
    if py == ap:
        print(f"OK: ASP matches python ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and python:")
    if py - ap:
        print("  only in python:", sorted(py - ap))
    if ap - py:
        print("  only in ASP:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def valid_pairs() -> list[tuple[str, str]]:
    pairs = []
    for p in PROPS:
        for s in SURPRISES:
            if (p, s) in {("scooter", "toy_car"), ("wagon", "breeze"), ("ball", "chalk"), ("wagon", "toy_car")}:
                pairs.append((p, s))
    return pairs


def choose_pair(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    pairs = valid_pairs()
    if args.prop:
        pairs = [p for p in pairs if p[0] == args.prop]
    if args.surprise:
        pairs = [p for p in pairs if p[1] == args.surprise]
    if not pairs:
        raise StoryError("No valid prop/surprise pair matches the given options.")
    return rng.choice(sorted(pairs))


def build_world(params: StoryParams) -> World:
    w = World(SETTING)
    prop_cfg = PROPS[params.prop]
    surprise_cfg = SURPRISES[params.surprise]

    eva = w.add(Entity(id="Eva", kind="character", label="Eva"))
    helper = w.add(Entity(id=params.helper, kind="character", label=params.helper))
    prop = w.add(Entity(id=params.prop, label=prop_cfg["label"], phrase=prop_cfg["phrase"], owner=eva.id))
    surprise = w.add(Entity(id=params.surprise, label=params.surprise, phrase=surprise_cfg["text"]))

    w.facts.update(eva=eva, helper=helper, prop=prop, surprise=surprise, params=params)
    return w


def predict_surprise(world: World, prop: Entity, surprise: Entity) -> dict:
    sim = world.copy()
    sim.get(prop.id).meters["steady"] += 0.5
    if prop.id == "scooter" and surprise.id == "toy_car":
        sim.get(prop.id).meters["surprise"] += 1
        sim.get(prop.id).meters["worry"] += 1
    elif prop.id == "wagon" and surprise.id == "breeze":
        sim.get(prop.id).meters["surprise"] += 1
        sim.get(prop.id).meters["worry"] += 1
    elif prop.id == "ball" and surprise.id == "chalk":
        sim.get(prop.id).meters["funny"] += 1
    return {
        "surprising": sim.get(prop.id).meters["surprise"] >= 1,
        "funny": sim.get(prop.id).meters["funny"] >= 1,
    }


def apply_joke(world: World, eva: Entity, prop: Entity) -> None:
    if "joke" in world.fired:
        return
    world.fired.add("joke")
    eva.memes["funny"] += 1
    prop.meters["funny"] += 1
    world.say(
        f"Eva took a breath and told herself, \"If this gets silly, I will be sillily prepared.\" "
        f"That thought made her grin."
    )


def enact_story(world: World) -> None:
    eva = world.get("Eva")
    helper = world.get("Dad")
    prop = world.get(world.facts["params"].prop)
    surprise = world.get(world.facts["params"].surprise)
    params: StoryParams = world.facts["params"]

    world.say(
        f"Eva stood in {world.setting.place}, where the pavement had a warm little tilt and the air made a humming sound."
    )
    world.say(
        f"She loved her {prop.label}, especially because it looked ready for comedy even when it was standing still."
    )
    world.say(
        f"Her head filled with a grand inner monologue: \"Today I will be smooth, speedy, and a tiny bit legendary.\""
    )

    world.para()
    world.say(
        f"Then Eva nudged the {prop.label} forward. The {prop.label} was not as smooth as her imagination had promised."
    )
    apply_joke(world, eva, prop)
    pred = predict_surprise(world, prop, surprise)
    if pred["surprising"]:
        prop.meters["surprise"] += 1
        eva.memes["worry"] += 1
        world.say(
            f"Just then, {surprise.phrase}. Eva blinked so hard her eyebrows nearly clapped."
        )
        world.say(
            f'Her inner voice squeaked, "That is absolutely not in my plan, but it is kind of hilarious."'
        )
        helper.memes["pride"] += 1
        world.say(
            f"{helper.label} laughed, not meanly, but in the way that says the joke is on the moment, not on Eva."
        )
        if params.prop == "scooter" and params.surprise == "toy_car":
            prop.meters["steady"] += 1
            eva.memes["relief"] += 1
            world.say(
                f"Eva held the scooter steady while the toy car zipped past like it had its own secret mission."
            )
        elif params.prop == "wagon" and params.surprise == "breeze":
            prop.meters["steady"] += 1
            eva.memes["relief"] += 1
            world.say(
                f"Eva parked the wagon with one hand and used the other to catch it before the breeze could boss it around."
            )
        elif params.prop == "ball" and params.surprise == "chalk":
            prop.meters["funny"] += 1
            eva.memes["relief"] += 1
            world.say(
                f"Eva stared at the chalky surprise, then drew a silly face beside it so the driveway looked like it was giggling."
            )
        else:
            eva.memes["relief"] += 1
            world.say(
                f"Eva paused, took a careful breath, and turned the surprise into part of the bit."
            )

    world.para()
    world.say(
        f"By the end, Eva was still in the driveway, but now her grin was bigger than the wobble."
    )
    world.say(
        f"The {prop.label} sat a little steadier, the surprise had become the punchline, and the whole driveway felt like it was smiling back."
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts(sample: StorySample) -> list[str]:
    p = sample.params
    return [
        f'Write a short comedy story for a young child about Eva in the driveway with a {p.prop}.',
        f'Write a story where an inner monologue helps Eva handle a surprise in the driveway.',
        f'Create a gentle funny story in which Eva expects one thing but a surprise changes the moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    prop = world.get(p.prop)
    surprise = world.get(p.surprise)
    return [
        QAItem(
            question="Where does the story happen?",
            answer=f"It happens in the driveway, where Eva is trying to keep her {prop.label} steady.",
        ),
        QAItem(
            question="What was Eva thinking to herself before things changed?",
            answer='Eva was telling herself that she would be smooth, speedy, and a tiny bit legendary.',
        ),
        QAItem(
            question="What surprise interrupted Eva's plan?",
            answer=f"The surprise was that {surprise.phrase}.",
        ),
        QAItem(
            question="How did Eva react to the surprise?",
            answer="She blinked, then decided it was funny instead of scary, and she kept going.",
        ),
        QAItem(
            question="How did the story end?",
            answer="Eva ended up smiling in the driveway, with the surprise turned into part of the joke.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a driveway?",
            answer="A driveway is the place beside a home where cars can park or roll in and out.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice inside your head that tells you what you think and feel.",
        ),
        QAItem(
            question="Why can surprise be funny in a comedy story?",
            answer="Surprise can be funny when something unexpected happens and the character reacts in a playful way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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


# ---------------------------------------------------------------------------
# Generation / emit / CLI
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    enact_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(StorySample(params=params, story="", world=world)),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 3) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 3) for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        lines.append(f"{ent.id}: {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedic storyworld about Eva in the driveway.")
    ap.add_argument("--name", default="Eva")
    ap.add_argument("--prop", choices=sorted(PROPS))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
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
    prop, surprise = choose_pair(args, rng)
    if args.name and args.name != "Eva":
        name = args.name
    else:
        name = "Eva"
    return StoryParams(
        seed=args.seed,
        name=name,
        prop=prop,
        surprise=surprise,
        helper="Dad",
        weather="sunny",
    )


CURATED = [
    StoryParams(name="Eva", prop="scooter", surprise="toy_car", helper="Dad", weather="sunny"),
    StoryParams(name="Eva", prop="wagon", surprise="breeze", helper="Dad", weather="sunny"),
    StoryParams(name="Eva", prop="ball", surprise="chalk", helper="Dad", weather="sunny"),
]


def asp_verify_report() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2.\n#show surprise_match/2."))
        return
    if args.verify:
        sys.exit(asp_verify_report())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        pairs = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(pairs)} valid prop/surprise pairs:")
        for p, s in pairs:
            print(f"  {p} + {s}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = seed
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.prop} + {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
