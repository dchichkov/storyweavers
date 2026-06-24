#!/usr/bin/env python3
"""
storyworlds/worlds/flounder_nutrition_offer_teamwork_happy_ending_repetition.py
===============================================================================

A small slice-of-life storyworld about a flounder who needs a kind offer,
some nutrition, and a little teamwork before everything feels right again.

Seed-tale sketch:
---
Flounder was a small, tired fish who kept floundering when it was time to
choose a snack. He did not feel very strong, and he did not want the same
plain food again.

One morning, a friend made a better offer: "Let's make a meal with good
nutrition." Flounder tried a bite, wrinkled his nose, and said no. His friend
offered again, this time with help from another fish. They worked together,
broke the food into smaller pieces, and offered it again.

Flounder tasted it, smiled, and finally ate enough to feel brave and bright.

Causal state updates:
---
    skipping a meal            -> hunger += 1, energy -= 1
    eating nutritious food     -> hunger -= 2, energy += 2, joy += 1
    a friend makes an offer    -> trust += 1
    repeated kind offers       -> resistance softens
    teamwork prepares food     -> offer quality improves
    accepting the offer        -> joy += 1, worry -= 1

Narrative instruments:
---
    Teamwork
    Repetition
    Happy Ending

Style:
---
    Slice of Life
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fish", "flounder"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    nutrition: int
    softness: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    offer_line: str
    teamwork_line: str
    retry_line: str


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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    setting: str
    snack: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "tidepool": Setting(place="the tide pool", mood="calm", affords={"snack", "teamwork"}),
    "aquarium": Setting(place="the aquarium tank", mood="quiet", affords={"snack", "teamwork"}),
    "kitchen": Setting(place="the kitchen table", mood="cozy", affords={"snack", "teamwork"}),
}

SNACKS = {
    "seaweed": Snack(
        id="seaweed",
        label="seaweed strips",
        phrase="thin seaweed strips",
        nutrition=2,
        softness=1,
        tags={"nutrition", "green"},
    ),
    "shrimp": Snack(
        id="shrimp",
        label="tiny shrimp bits",
        phrase="tiny shrimp bits",
        nutrition=3,
        softness=2,
        tags={"nutrition", "protein"},
    ),
    "pellets": Snack(
        id="pellets",
        label="fish pellets",
        phrase="small fish pellets",
        nutrition=2,
        softness=3,
        tags={"nutrition", "simple"},
    ),
}

HELPERS = {
    "marina": Helper(
        id="Marina",
        label="Marina",
        offer_line="made a gentle offer",
        teamwork_line="asked for teamwork",
        retry_line="tried the offer again, with smaller pieces",
    ),
    "otto": Helper(
        id="Otto",
        label="Otto",
        offer_line="made a careful offer",
        teamwork_line="called for a second set of helping fins",
        retry_line="offered it again, a little slower this time",
    ),
    "nina": Helper(
        id="Nina",
        label="Nina",
        offer_line="made a kind offer",
        teamwork_line="showed how teamwork could help",
        retry_line="offered the snack once more",
    ),
}

FLOUNDER_NAMES = ["Flounder", "Finn", "Pip", "Milo", "Toby"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life story about flounder, nutrition, offer, teamwork, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    snack = args.snack or rng.choice(list(SNACKS))
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(setting=setting, snack=snack, helper=helper)


def _init_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    flounder = world.add(Entity(
        id="Flounder",
        kind="character",
        type="flounder",
        label="Flounder",
        meters={"hunger": 2.0, "energy": 1.0},
        memes={"worry": 1.0, "joy": 0.0, "trust": 0.0, "resistance": 1.0},
    ))
    helper = world.add(Entity(
        id=HELPERS[params.helper].id,
        kind="character",
        type="fish",
        label=HELPERS[params.helper].label,
        meters={"patience": 2.0},
        memes={"kindness": 2.0},
    ))
    snack = world.add(Entity(
        id=params.snack,
        kind="thing",
        type="snack",
        label=SNACKS[params.snack].label,
        phrase=SNACKS[params.snack].phrase,
        owner=helper.id,
        helper=flounder.id,
        meters={"nutrition": 0.0, "preparedness": 0.0},
    ))
    world.facts.update(flounder=flounder, helper=helper, snack=snack, params=params)
    return world


def _skip_meal(world: World) -> None:
    f = world.facts["flounder"]
    f.meters["hunger"] += 1
    f.meters["energy"] -= 1
    f.memes["worry"] += 1


def _offer(world: World) -> None:
    f = world.facts["flounder"]
    h = world.facts["helper"]
    f.memes["trust"] += 1
    f.memes["resistance"] += 0.25
    world.say(
        f"{h.label} made an offer: \"Would you like something with good nutrition?\""
    )


def _try_bite(world: World) -> None:
    f = world.facts["flounder"]
    f.memes["resistance"] += 1
    f.memes["worry"] += 0.25
    world.say(
        f"Flounder tried a tiny bite, but the first piece was too big, so {f.pronoun()} "
        f"floundered and shook {f.pronoun('possessive')} head."
    )


def _teamwork(world: World) -> None:
    h = world.facts["helper"]
    snack = world.facts["snack"]
    snack.meters["preparedness"] += 1
    snack.meters["nutrition"] += SNACKS[snack.id].nutrition
    world.say(
        f"{h.label} asked for teamwork, and together they broke the {snack.label} into smaller pieces."
    )


def _offer_again(world: World) -> None:
    f = world.facts["flounder"]
    h = world.facts["helper"]
    f.memes["resistance"] = max(0.0, f.memes["resistance"] - 1.0)
    f.memes["trust"] += 0.5
    world.say(
        f"{h.label} {HELPERS[world.facts['params'].helper].retry_line}, and this time the offer felt easier to accept."
    )


def _eat(world: World) -> None:
    f = world.facts["flounder"]
    snack = world.facts["snack"]
    f.meters["hunger"] = max(0.0, f.meters["hunger"] - 2.0)
    f.meters["energy"] += 2.0
    f.memes["joy"] += 2.0
    f.memes["worry"] = max(0.0, f.memes["worry"] - 1.0)
    world.say(
        f"Flounder finally ate the little pieces of {snack.phrase}, and the good nutrition filled {f.pronoun('object')} up."
    )
    world.say(
        f"{f.pronoun().capitalize()} looked brighter after that, as if the day had found its gentle rhythm again."
    )


def tell_story(params: StoryParams) -> World:
    world = _init_world(params)
    f = world.facts["flounder"]
    h = world.facts["helper"]
    snack = world.facts["snack"]

    world.say(
        f"{f.label} was a small flounder living near {world.setting.place}, and {f.pronoun()} felt a little wobbly when {f.pronoun('possessive')} tummy was empty."
    )
    world.say(
        f"{f.label} loved quiet days, but today {f.pronoun()} needed some nutrition."
    )
    world.para()
    _skip_meal(world)
    world.say(
        f"{h.label} noticed the wobble and made an offer to share {snack.phrase}."
    )
    _offer(world)
    _try_bite(world)
    world.para()
    _teamwork(world)
    _offer_again(world)
    _eat(world)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    snack = SNACKS[params.snack]
    helper = HELPERS[params.helper]
    return [
        "Write a small slice-of-life story about a flounder who needs nutrition and gets a kind offer.",
        f"Tell a gentle story where {helper.label} makes an offer and teamwork helps Flounder enjoy {snack.label}.",
        f"Write a happy ending story with repetition: an offer is tried, improved, and finally accepted.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    f = world.facts["flounder"]
    h = world.facts["helper"]
    snack = world.facts["snack"]
    return [
        QAItem(
            question="Why did Flounder need help?",
            answer="Flounder had skipped enough food to feel wobbly and low on energy, so a kind offer of nutrition would help."
        ),
        QAItem(
            question=f"What offer did {h.label} make?",
            answer=f"{h.label} offered {snack.phrase} and invited Flounder to try it."
        ),
        QAItem(
            question="How did teamwork change the snack?",
            answer=f"Teamwork broke the snack into smaller pieces, which made the offer easier for Flounder to accept."
        ),
        QAItem(
            question="What repetition happened in the story?",
            answer=f"The offer was tried, refused once, and then offered again in a smaller, gentler way."
        ),
        QAItem(
            question="How did the story end?",
            answer="Flounder ate the snack, felt stronger, and the day ended happily and calmly."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is nutrition?",
            answer="Nutrition is the helpful stuff in food that gives a body energy and helps it stay strong."
        ),
        QAItem(
            question="What is an offer?",
            answer="An offer is when someone kindly suggests something or gives a choice."
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when two or more helpers work together to do something better."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} {e.type:8} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="tidepool", snack="seaweed", helper="marina"),
    StoryParams(setting="aquarium", snack="shrimp", helper="otto"),
    StoryParams(setting="kitchen", snack="pellets", helper="nina"),
]


ASP_RULES = r"""
flounder_needs_help(F) :- character(F), hunger(F,H), H >= 2.
kind_offer(H,F) :- helper(H), flounder(F), trust(F,T), T >= 1.
teamwork_ready(H,F,S) :- kind_offer(H,F), snack(S), preparedness(S,P), P >= 1.
happy_end(F) :- flounder_needs_help(F), trust(F,T), T >= 1, joy(F,J), J >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
    for sid, sn in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("nutrition", sid, sn.nutrition))
        lines.append(asp.fact("softness", sid, sn.softness))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    models = asp.solve(asp_program("#show happy_end/1."), models=1)
    ok = bool(models)
    if ok:
        print("OK: ASP gate produced a happy end model.")
        return 0
    print("MISMATCH: ASP gate did not produce a happy end model.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
        print(asp_program("#show happy_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show happy_end/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.snack} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
