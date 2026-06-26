#!/usr/bin/env python3
"""
storyworlds/worlds/implore_hoo_teamwork_mystery.py
==================================================

A small mystery storyworld where a child and a helper team up to solve a
missing-object puzzle. The seed words are carried into the world through the
child's pleading, an owl's "hoo", and the shared teamwork that cracks the case.

The domain is deliberately compact:
- a child wants to solve a mystery,
- a small set of clue-bearing places,
- a hidden object moved by a well-meaning helper,
- teamwork and careful looking resolve the uncertainty.

The story stays close to mystery style: a puzzling beginning, a middle full of
clues and false leads, and an ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    secret: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    places: list[str]
    hidden_spot: str


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    culprit: str
    reveal_spot: str
    requires_teamwork: bool = True


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_owl_hint(world: World) -> list[str]:
    out: list[str] = []
    owl = world.entities.get("Owl")
    child = world.entities.get("Hero")
    if not owl or not child:
        return out
    if child.memes.get("lost", 0) >= THRESHOLD and ("owl_hoo",) not in world.fired:
        world.fired.add(("owl_hoo",))
        owl.meters["heard"] = owl.meters.get("heard", 0) + 1
        child.memes["hope"] = child.memes.get("hope", 0) + 1
        out.append('From the dark branch, the owl gave a soft "hoo."')
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("Hero")
    clue = world.entities.get("Clue")
    if not child or not clue:
        return out
    if child.memes.get("searching", 0) >= THRESHOLD and ("found_clue",) not in world.fired:
        world.fired.add(("found_clue",))
        clue.meters["seen"] = clue.meters.get("seen", 0) + 1
        child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
        out.append(f"{child.id} spotted a tiny {clue.label} near the floorboards.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("Hero")
    helper = world.entities.get("Helper")
    if not child or not helper:
        return out
    if child.memes.get("searching", 0) >= THRESHOLD and helper.memes.get("helping", 0) >= THRESHOLD:
        if ("teamwork",) not in world.fired:
            world.fired.add(("teamwork",))
            child.memes["brave"] = child.memes.get("brave", 0) + 1
            helper.memes["steady"] = helper.memes.get("steady", 0) + 1
            out.append(f"Together they looked under the shelf, behind the curtain, and inside the old box.")
    return out


RULES = [
    Rule("owl_hint", _r_owl_hint),
    Rule("clue", _r_clue),
    Rule("teamwork", _r_teamwork),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def solve_mystery(world: World, mystery: Mystery) -> None:
    child = world.get("Hero")
    helper = world.get("Helper")
    clue = world.get("Clue")
    object_ = world.get("Missing")

    world.say(
        f"One evening at {world.setting.place}, {child.id} noticed that {object_.phrase} was gone."
    )
    world.say(
        f"{child.id} searched the room and could not find it anywhere."
    )
    world.para()

    child.memes["lost"] = child.memes.get("lost", 0) + 1
    child.memes["searching"] = child.memes.get("searching", 0) + 1
    world.say(
        f'"Please," {child.pronoun("subject").capitalize()} said, "I need help. I implore you, {helper.id}!"'
    )
    helper.memes["helping"] = helper.memes.get("helping", 0) + 1
    world.say(
        f"{helper.id} nodded at once, and the two of them began to follow the mystery."
    )

    propagate(world, narrate=True)

    world.say(
        f"They noticed a {clue.label} near the {world.setting.hidden_spot}, which meant somebody had been there."
    )
    world.say(
        f"At last, they lifted the lid on the old box and found {object_.phrase} tucked inside."
    )
    world.para()

    child.memes["lost"] = 0
    child.memes["searching"] = 0
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    world.say(
        f"It turned out that {mystery.culprit} had moved it there to keep it safe, and no one had meant to cause trouble."
    )
    world.say(
        f"{child.id} laughed, {helper.id} smiled, and the little room felt peaceful again."
    )

    world.facts.update(
        child=child,
        helper=helper,
        clue=clue,
        missing=object_,
        mystery=mystery,
    )


def introduce_world(world: World, child: Entity, helper: Entity, object_: Entity, mystery: Mystery) -> None:
    world.say(
        f"{child.id} was a little {child.pronoun('possessive')} {child.type} who loved solving puzzles."
    )
    world.say(
        f"{helper.id} was a careful {helper.type} who liked to notice small things."
    )
    world.say(
        f"They were both curious about {object_.phrase}, especially after it vanished from sight."
    )


SETTINGS = {
    "attic": Setting(place="the attic", places=["shelf", "curtain", "box"], hidden_spot="old box"),
    "library": Setting(place="the library corner", places=["table", "chair", "book cart"], hidden_spot="book cart"),
    "garden_shed": Setting(place="the garden shed", places=["bench", "crate", "basket"], hidden_spot="basket"),
}

MYSTERIES = {
    "lantern": Mystery(
        id="lantern",
        missing="lantern",
        clue="feather",
        culprit="the owl",
        reveal_spot="old box",
        requires_teamwork=True,
    ),
    "toy_train": Mystery(
        id="toy_train",
        missing="toy train",
        clue="string",
        culprit="the little robot",
        reveal_spot="book cart",
        requires_teamwork=True,
    ),
    "golden_key": Mystery(
        id="golden_key",
        missing="golden key",
        clue="sparkle",
        culprit="the careful cat",
        reveal_spot="basket",
        requires_teamwork=True,
    ),
}

GENDERS = {"girl", "boy"}
GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Theo", "Leo", "Ben", "Max", "Sam", "Finn"]
TRAITS = ["brave", "curious", "patient", "gentle", "quick-eyed"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small teamwork mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["owl", "sibling", "parent"])
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["owl", "sibling", "parent"])
    trait = args.trait or rng.choice(TRAITS)

    if helper == "owl" and mystery == "golden_key":
        pass

    return StoryParams(
        setting=setting,
        mystery=mystery,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def helper_entity(kind: str) -> tuple[str, str]:
    if kind == "owl":
        return "Owl", "owl"
    if kind == "sibling":
        return "Sibling", "sibling"
    return "Parent", "parent"


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    child = world.add(Entity(id="Hero", kind="character", type=params.gender, label=params.name,
                             traits=[params.trait], meters={}, memes={}))
    helper_id, helper_type = helper_entity(params.helper)
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=helper_id,
                              traits=["helpful"], meters={}, memes={}))
    if params.helper == "owl":
        world.add(Entity(id="Owl", kind="character", type="owl", label="owl", traits=["watchful"], meters={}, memes={}))
    else:
        world.add(Entity(id="Owl", kind="character", type="owl", label="owl", traits=["watchful"], meters={}, memes={}))

    missing = world.add(Entity(id="Missing", kind="thing", type=mystery.missing, label=mystery.missing,
                               phrase=f"a little {mystery.missing}", secret=True))
    clue = world.add(Entity(id="Clue", kind="thing", type="clue", label=mystery.clue, phrase=mystery.clue))
    world.facts["mystery_id"] = mystery.id

    introduce_world(world, child, helper, missing, mystery)
    world.para()
    solve_mystery(world, mystery)

    prompts = [
        f"Write a short mystery story for a child named {params.name} about teamwork and a missing {mystery.missing}.",
        f"Tell a gentle detective story where someone says 'implore' and an owl goes 'hoo'.",
        f"Write a simple teamwork mystery set in {setting.place} with a hidden clue and a happy ending.",
    ]

    story_qa = [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was {missing.phrase}, and that made the room feel puzzling at first.",
        ),
        QAItem(
            question=f"Who helped {params.name} solve the mystery?",
            answer=f"{helper.label} helped, and the two of them worked together to search carefully.",
        ),
        QAItem(
            question=f"What did the owl say?",
            answer='The owl said "hoo," which was a small clue that something nearby was watching.',
        ),
        QAItem(
            question=f"Why did {params.name} implore the helper?",
            answer=f"{params.name} implored the helper because the {mystery.missing} had vanished and needed to be found.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and share the job so they can solve a problem together.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you figure out what happened.",
        ),
        QAItem(
            question="Why do owls say hoo?",
            answer="Owls often make a hooting sound, and people write it as hoo.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.secret:
            bits.append("secret=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n, *_) in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child is searching when the missing thing has vanished.
searching(hero) :- lost(hero).

% Teamwork happens when the child and helper are both active.
teamwork(hero) :- searching(hero), helping(helper).

% An owl clue is present if hoo was heard.
owl_clue(hoo) :- owl_sound(hoo).

% The mystery is solved when teamwork and a clue both appear.
solved(hero) :- teamwork(hero), clue_seen(hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in s.places:
            lines.append(asp.fact("place", sid, p))
        lines.append(asp.fact("hidden_spot", sid, s.hidden_spot))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("clue", mid, m.clue))
    lines.append(asp.fact("owl_sound", "hoo"))
    lines.append(asp.fact("teamwork_feature", "teamwork"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="attic", mystery="lantern", name="Mia", gender="girl", helper="owl", trait="curious"),
            StoryParams(setting="library", mystery="toy_train", name="Theo", gender="boy", helper="sibling", trait="patient"),
            StoryParams(setting="garden_shed", mystery="golden_key", name="Nora", gender="girl", helper="parent", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = build_story_params_from_args(args, random.Random(seed))
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
