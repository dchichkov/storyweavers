#!/usr/bin/env python3
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


@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "character"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Clue:
    id: str
    label: str
    place: str
    hidden: bool = False
    found: bool = False
    suspicious: bool = False


@dataclass
class Setting:
    place: str = "the old chow shop"
    vibe: str = "quiet"


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    twist: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.characters: dict[str, Character] = {}
        self.clues: dict[str, Clue] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.fired: set[str] = set()

    def add_character(self, c: Character) -> Character:
        self.characters[c.id] = c
        return c

    def add_clue(self, c: Clue) -> Clue:
        self.clues[c.id] = c
        return c

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.characters = _copy.deepcopy(self.characters)
        w.clues = _copy.deepcopy(self.clues)
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_notice(world: World) -> list[str]:
    out = []
    detective = world.characters["detective"]
    for clue in world.clues.values():
        if clue.found or clue.hidden:
            continue
        clue.found = True
        detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
        out.append(f"{detective.id} spotted a small clue near the {clue.place}.")
        break
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    if world.facts.get("twist_revealed"):
        return out
    if world.characters["helper"].memes.get("nervous", 0) >= 1 and world.facts.get("chow_missing"):
        world.facts["twist_revealed"] = True
        out.append("__twist__")
    return out


RULES = [
    Rule("notice", _r_notice),
    Rule("twist", _r_twist),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__twist__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "shop": Setting(place="the old chow shop", vibe="quiet"),
    "kitchen": Setting(place="the back kitchen", vibe="still"),
    "alley": Setting(place="the narrow alley", vibe="dim"),
}

TWISTS = {
    "helper": "the helper did it",
    "lost": "the chow was hidden all along",
    "swap": "the wrong bowl was served",
}

HELPERS = {
    "cat": ("cat", "a gray cat with green eyes"),
    "chef": ("chef", "a sleepy chef"),
    "neighbor": ("neighbor", "a polite neighbor"),
}

GIRL_NAMES = ["Mina", "Nora", "Ivy", "Lena", "Pia", "Rosa"]
BOY_NAMES = ["Noah", "Eli", "Jude", "Toby", "Miles", "Finn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with chow and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--twist", choices=TWISTS)
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
    return [(p, h, t) for p in SETTINGS for h in HELPERS for t in TWISTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.helper:
        combos = [c for c in combos if c[1] == args.helper]
    if args.twist:
        combos = [c for c in combos if c[2] == args.twist]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, helper, twist = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, name=name, gender=gender, helper=helper, twist=twist)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    detective = world.add_character(Character(
        id=params.name,
        type=params.gender,
        label=params.name,
        role="detective",
        traits=["careful", "curious"],
        memes={"curiosity": 1, "worry": 0},
    ))
    helper_type, helper_label = HELPERS[params.helper]
    helper = world.add_character(Character(
        id="helper",
        type=helper_type,
        label=helper_label,
        role="helper",
        traits=["quiet"],
        memes={"nervous": 0, "kindness": 1},
    ))
    chow = world.add_clue(Clue(id="chow", label="a bowl of chow", place="counter", hidden=False))
    missing = world.add_clue(Clue(id="missing", label="an empty spot on the table", place="table", hidden=False, suspicious=True))

    world.facts.update(detective=detective, helper=helper, chow=chow, missing=missing)
    world.say(f"{detective.id} came to {world.setting.place} because something about the chow felt wrong.")
    world.say(f"The room was quiet, and even the air seemed to hold its breath.")
    world.say(f"On the counter sat {chow.label}, but there was an empty spot where a second bowl should have been.")
    world.say(f"{detective.id} looked at {helper.label} and asked who had touched the chow.")
    helper.memes["nervous"] = 1
    world.say(f"{helper.label} lowered their eyes and said they had only heard a small scrape in the dark.")
    world.facts["chow_missing"] = True
    if params.twist == "helper":
        world.say(f"{detective.id} followed the scrape and found a tiny trail right back to {helper.label}.")
    elif params.twist == "lost":
        world.say(f"{detective.id} checked the shelf, the sink, and the floor, but the chow had been hidden all along.")
    else:
        world.say(f"{detective.id} lifted the tray and saw the wrong bowl sitting in the right place.")
    propagate(world)
    world.say(f"In the end, {detective.id} found the truth: {TWISTS[params.twist]}.")
    if params.twist == "helper":
        world.say(f"It turned out {helper.label} had moved the chow to keep it safe from a nosy cat.")
    elif params.twist == "lost":
        world.say(f"The missing bowl was tucked behind a crate, waiting for someone kind to notice it.")
    else:
        world.say(f"The real chow had been served to the wrong table, and the mix-up was just a sleepy mistake.")
    world.say(f"{detective.id} smiled, and the little mystery settled down like a cat in a warm chair.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = f["detective"]
    return [
        f'Write a short mystery story for a young child that includes the word "chow" and a small twist.',
        f"Tell a gentle mystery about {d.id} looking for chow in {world.setting.place} and discovering that things are not what they first seemed.",
        f"Write a simple detective story where a missing chow clue leads to a surprise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    h = f["helper"]
    return [
        QAItem(question=f"Who was trying to solve the chow mystery?", answer=f"{d.id} was trying to solve it."),
        QAItem(question="What was missing or strange about the chow?", answer="There was an empty spot on the table, so something about the chow was not right."),
        QAItem(question=f"Who helped in the mystery?", answer=f"{h.label} helped by answering questions and pointing toward the truth."),
        QAItem(question="What was the twist at the end?", answer=f"The twist was that {world.facts.get('twist_revealed') and 'the truth came out after a surprise clue' or 'the mystery turned around in a new way'}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is chow?", answer="Chow is food, often something warm and hearty in a bowl."),
        QAItem(question="What does a detective do?", answer="A detective looks for clues and tries to figure out what happened."),
        QAItem(question="What is a twist in a mystery?", answer="A twist is a surprise change that makes the story turn in a new direction."),
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
    for c in world.characters.values():
        lines.append(f"  {c.id}: meters={c.meters} memes={c.memes}")
    for c in world.clues.values():
        lines.append(f"  clue {c.id}: place={c.place} hidden={c.hidden} found={c.found} suspicious={c.suspicious}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
helper_twist :- twist(helper).
lost_twist :- twist(lost).
swap_twist :- twist(swap).
valid_story(P,H,T) :- place(P), helper(H), twist(T).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    StoryParams(place="shop", name="Mina", gender="girl", helper="cat", twist="helper"),
    StoryParams(place="kitchen", name="Noah", gender="boy", helper="chef", twist="lost"),
    StoryParams(place="alley", name="Ivy", gender="girl", helper="neighbor", twist="swap"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
