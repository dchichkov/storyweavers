#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/progeny_choice_happy_ending_sharing_whodunit.py
==============================================================================

A small standalone storyworld about a gentle mystery: someone notices missing
treats, asks careful questions, and discovers that the "culprit" was actually a
choice to share. The story always ends happily, with the children and the small
progeny in the yard eating together.

Seed words:
- progeny
- choice

Features:
- Happy ending
- Sharing

Style:
- Whodunit
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Setting:
    id: str
    place: str
    scene: str
    mystery_nook: str
    time_phrase: str
    weather: str = ""


@dataclass
class Mystery:
    id: str
    missing: str
    clue_one: str
    clue_two: str
    found_by: str
    culprit_reason: str
    shared_food: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    label: str
    verb: str
    effect: str
    success: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_gather_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["missing"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.entities.values():
            if c.kind == "character":
                c.memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_gather_fear)]


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


SETTINGS = {
    "yard": Setting("yard", "the yard", "the little yard", "the berry nook", "that morning", "mild"),
    "garden": Setting("garden", "the garden", "the bright garden", "the cabbage patch", "that afternoon", "warm"),
}

MYSTERIES = {
    "berries": Mystery(
        id="berries",
        missing="the berries",
        clue_one="a line of tiny crumbs",
        clue_two="soft little footprints",
        found_by="the birdhouse",
        culprit_reason="the baby birds were hungry",
        shared_food="a bowl of blueberries",
        tags={"food", "bird", "sharing"},
    ),
    "cookies": Mystery(
        id="cookies",
        missing="the cookies",
        clue_one="a sprinkle of sugar",
        clue_two="a tin lid left open",
        found_by="the porch step",
        culprit_reason="the chicks were pecking for a snack",
        shared_food="a plate of crackers",
        tags={"food", "chick", "sharing"},
    ),
}

CHOICES = {
    "share": Choice(
        id="share",
        label="share",
        verb="share",
        effect="placed the food in the middle so everyone could reach it",
        success="shared it kindly and made the mystery feel friendly",
        tags={"sharing", "kind"},
    )
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Theo", "Max"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    choice: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, c) for s in SETTINGS for m in MYSTERIES for c in CHOICES]


def explain_rejection() -> str:
    return "(No story: this world only tells a gentle whodunit that ends with sharing.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle whodunit storyworld about a small mystery and a sharing choice."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
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
    combos = valid_combos()
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(explain_rejection())
    setting, mystery, choice = rng.choice(combos)
    detective_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if detective_gender == "girl" else "girl"
    detective = args.detective or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != detective])
    return StoryParams(setting=setting, mystery=mystery, choice=choice,
                       detective=detective, detective_gender=detective_gender,
                       helper=helper, helper_gender=helper_gender)


def tell(setting: Setting, mystery: Mystery, choice: Choice,
         detective: str, detective_gender: str,
         helper: str, helper_gender: str) -> World:
    world = World(setting)
    d = world.add(Entity(id=detective, kind="character", type=detective_gender, role="detective"))
    h = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.missing))
    nest = world.add(Entity(id="nest", type="thing", label=mystery.found_by))
    d.memes["curiosity"] += 1
    h.memes["curiosity"] += 1

    world.say(
        f"{d.id} and {h.id} were in {setting.place} on {setting.time_phrase}. "
        f"{setting.scene}"
    )
    world.say(
        f"Then {d.id} looked around and frowned. {mystery.missing.capitalize()} were gone."
    )
    world.para()
    world.say(
        f"{d.id} searched like a tiny detective. Near {setting.mystery_nook}, {mystery.clue_one} and {mystery.clue_two} answered the first question."
    )
    clue.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{h.id} whispered, "Who took them?"'
    )
    world.say(
        f"{d.id} followed the trail to {mystery.found_by}. There, the small progeny had found the treats first because {mystery.culprit_reason}."
    )
    world.para()
    world.say(
        f"{d.id} had a choice. Instead of scolding anyone, {d.pronoun()} {choice.verb}ed {mystery.shared_food} and {choice.effect}."
    )
    world.say(
        f"The little ones tucked in happily, and the mystery turned out to be a sharing story after all."
    )
    world.say(
        f"At the end, everyone smiled, and the progeny of the yard and the two children ate together."
    )

    world.facts.update(
        setting=setting,
        mystery=mystery,
        choice=choice,
        detective=d,
        helper=h,
        outcome="shared",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit-style story for a young child that includes the words "{f["mystery"].missing.split()[-1].lower()}" and "choice", and ends with sharing.',
        f"Tell a gentle mystery where {f['detective'].id} asks who took the missing treats, then chooses to share with the small progeny instead of getting upset.",
        "Write a happy-ending story about a child detective who solves a tiny mystery by sharing food kindly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("What was missing?", f"The missing thing was {f['mystery'].missing}. That was the mystery everyone noticed at the start."),
        ("How was the mystery solved?", f"{f['detective'].id} followed the clues to the little progeny by {f['mystery'].found_by}. Then {f['detective'].id} made a kind choice and shared {f['mystery'].shared_food}, which solved the problem happily."),
        ("Why was it a happy ending?", "Nobody was blamed or hurt. The children shared food, the little ones ate too, and everyone ended the story smiling together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does progeny mean?", "Progeny means children or offspring. It can mean the young ones that come after the parent animals or people."),
        ("What is a choice?", "A choice is a decision between two or more things. You make a choice when you decide what to do."),
        ("What is sharing?", "Sharing means giving some of what you have to someone else or letting others use it too. It is a kind way to help everyone enjoy something together."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,C) :- setting(S), mystery(M), choice(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        print("MISMATCH: ASP gate differs from valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    mystery = MYSTERIES.get(params.mystery)
    choice = CHOICES.get(params.choice)
    if not setting or not mystery or not choice:
        raise StoryError("Invalid params for this storyworld.")
    world = tell(setting, mystery, choice, params.detective, params.detective_gender,
                 params.helper, params.helper_gender)
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
    StoryParams(setting="yard", mystery="berries", choice="share", detective="Mia", detective_gender="girl", helper="Ben", helper_gender="boy"),
    StoryParams(setting="garden", mystery="cookies", choice="share", detective="Leo", detective_gender="boy", helper="Nora", helper_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{s} {m} {c}" for s, m, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
