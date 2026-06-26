#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a child, a genie, and a missing thing
found through conversation, careful noticing, and one quiet wish.

This world models a tiny home scene where something ordinary has gone missing
under or near a linoleum floor, and a friendly genie helps the characters solve
the mystery without turning the day into high adventure.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    caretaker: Optional[str] = None
    location: str = ""
    hidden_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)
    mood: str = "quiet"


@dataclass
class Mystery:
    missing: str
    clue_place: str
    reveal_place: str
    solved_by: str
    reason: str
    hint: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mystery: Mystery):
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting, self.mystery)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affordances={"talk", "search", "wish"}, mood="quiet"),
    "hall": Setting(place="the hall", affordances={"talk", "search", "wish"}, mood="soft"),
    "porch": Setting(place="the porch", affordances={"talk", "search", "wish"}, mood="afternoon"),
}

MYSTERIES = {
    "cup": Mystery(
        missing="cup",
        clue_place="under the linoleum mat",
        reveal_place="beside the sink",
        solved_by="lifting the linoleum corner and looking under the mat",
        reason="the cup had rolled while they were talking",
        hint="a faint clink from the floor",
    ),
    "keys": Mystery(
        missing="keys",
        clue_place="near the linoleum seam",
        reveal_place="in a coat pocket",
        solved_by="following the little scrap of paper the genie pointed to",
        reason="someone had tucked the keys away and forgotten",
        hint="a tiny jingle near the floor",
    ),
    "spoon": Mystery(
        missing="spoon",
        clue_place="by the linoleum edge",
        reveal_place="inside a cereal bowl",
        solved_by="checking the breakfast spots one by one",
        reason="the spoon had slipped into the wrong bowl",
        hint="a silver shine by the floorboard",
    ),
}

HERO_NAMES = ["Mina", "Noah", "Lia", "Ben", "Sara", "Owen", "Ivy", "Eli"]
HELPER_NAMES = ["Juno", "Paz", "Rina", "Tari", "Milo", "Zuri"]
TRAITS = ["curious", "gentle", "thoughtful", "quiet", "patient", "bright"]


def validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.hero_type == params.helper_type:
        raise StoryError("The hero and helper need different roles for the dialogue to feel natural.")


def name_for(type_name: str, rng: random.Random, pool: list[str]) -> str:
    return rng.choice(pool)


def select_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("genie" if hero_type != "genie" else "boy")
    if helper_type == hero_type:
        helper_type = "genie"
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    params = StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )
    validate_params(params)
    return params


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting, mystery)

    hero = world.add(Entity(
        id="hero", kind="character", type=params.hero_type, label=params.hero_name,
        traits=["little", "curious", "gentle"], meters={"attention": 1.0}, memes={"worry": 0.0, "hope": 0.0},
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type="genie", label=params.helper_name,
        traits=["friendly", "patient"], meters={"spark": 1.0}, memes={"care": 1.0},
    ))
    home = world.add(Entity(
        id="home", kind="place", type="home", label=setting.place,
    ))
    missing = world.add(Entity(
        id="missing", kind="thing", type=mystery.missing, label=mystery.missing,
        owner=hero.id, caretaker=hero.id, hidden_in=mystery.clue_place,
        meters={"lost": 1.0, "found": 0.0}, memes={"importance": 1.0},
    ))
    linoleum = world.add(Entity(
        id="linoleum", kind="thing", type="linoleum", label="linoleum",
        phrase="the smooth linoleum floor", meters={"clean": 1.0}, memes={"noticed": 0.0},
    ))
    willow = world.add(Entity(
        id="willow", kind="thing", type="willow", label="willow",
        phrase="the willow tree by the window", meters={"still": 1.0}, memes={"calm": 1.0},
    ))
    genie = world.add(Entity(
        id="genie", kind="character", type="genie", label=params.helper_name,
        traits=["gentle", "sparkly"], meters={"magic": 1.0}, memes={"kindness": 1.0},
    ))
    world.entities["helper"] = genie

    world.facts.update(hero=hero, helper=genie, missing=missing, linoleum=linoleum, willow=willow, home=home)
    return world


def detect_clue(world: World) -> bool:
    miss = world.get("missing")
    if miss.hidden_in == world.mystery.clue_place:
        world.get("linoleum").memes["noticed"] += 1
        return True
    return False


def reveal_missing(world: World) -> None:
    miss = world.get("missing")
    miss.hidden_in = world.mystery.reveal_place
    miss.meters["found"] = 1.0
    miss.meters["lost"] = 0.0


def tell_story(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    missing = world.get("missing")
    linoleum = world.get("linoleum")
    willow = world.get("willow")
    mystery = world.mystery
    place = world.setting.place

    world.say(
        f"{hero.label} was a little {hero.type} with a quiet way of looking closely at rooms."
    )
    world.say(
        f"One afternoon at {place}, {hero.label} noticed that the {missing.label} was gone."
    )
    world.say(
        f"{hero.label} looked at the smooth {linoleum.label} floor and then up at the willow by the window, "
        f"as if both might know a secret."
    )

    world.para()
    hero.memes["worry"] += 1.0
    world.say(
        f'"Where did my {missing.label} go?" {hero.label} asked, in that small voice kids use when they really hope someone has a clue.'
    )
    world.say(
        f'"Let us ask the room," said the genie {helper.label}, because a gentle mystery is easier when two pairs of eyes are watching.'
    )

    world.para()
    world.say(
        f"They checked the table, the sill, and the basket near the door. Nothing there helped."
    )
    if detect_clue(world):
        world.say(
            f"Then {hero.label} heard {mystery.hint} from the floor, and the genie knelt beside the linoleum seam."
        )
    world.say(
        f'"Maybe the answer is close," {helper.label} said. "Sometimes a thing is not far away; it is just hiding where we forgot to look."'
    )

    world.para()
    hero.memes["hope"] += 1.0
    world.say(
        f"{hero.label} smiled a little. The willow leaves brushed the window, quiet as a secret shared by a friend."
    )
    world.say(
        f'Together they tried {mystery.solved_by}, and that was enough to solve it.'
    )
    reveal_missing(world)
    world.say(
        f'They found the {missing.label} at {mystery.reveal_place} because {mystery.reason}.'
    )
    world.say(
        f"{hero.label} laughed, the genie smiled, and the little room felt tidy again."
    )

    world.facts["solved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    missing = f["missing"]
    return [
        f'Write a slice-of-life story for a young child about a genie, linoleum, and willow, with a small mystery to solve.',
        f"Tell a gentle dialogue story where {hero.label} asks {helper.label} to help find a missing {missing.label}.",
        f"Write a short story in which a child follows a clue near the linoleum and learns a calm secret from the room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    missing = f["missing"]
    return [
        QAItem(
            question=f"What was missing from the room?",
            answer=f"The {missing.label} was missing.",
        ),
        QAItem(
            question=f"Who helped {hero.label} solve the mystery?",
            answer=f"The genie {helper.label} helped {hero.label} solve it.",
        ),
        QAItem(
            question=f"Where did they look for a clue?",
            answer=f"They looked near the linoleum floor and listened for a small clue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a genie in stories?",
            answer="A genie is a magical helper in stories who can grant wishes or give helpful surprises.",
        ),
        QAItem(
            question="What is linoleum?",
            answer="Linoleum is a smooth floor material that people often use in kitchens and other busy rooms.",
        ),
        QAItem(
            question="What is a willow tree like?",
            answer="A willow tree often has long, hanging branches that look soft and graceful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_resolution(world: World) -> str:
    missing = world.get("missing")
    return (
        f"(No story: the mystery is not really solvable in this configuration, "
        f"because the {missing.label} must be plausibly hidden near the linoleum clue.)"
    )


ASP_RULES = r"""
clue_seen(M) :- missing(M), clue_place(M, P), at(hero, P), near(hero, P).
solved(M) :- clue_seen(M), reveal(M, R), reasoned_about(hero, M), hidden_at(M, R).
valid_story(S, M) :- setting(S), mystery(M), clue_place(M, _), reveal(M, _), solved(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing_kind", mid, m.missing))
        lines.append(asp.fact("clue_place", mid, m.clue_place))
        lines.append(asp.fact("reveal", mid, m.reveal_place))
    lines.append(asp.fact("at", "hero", "home"))
    lines.append(asp.fact("near", "hero", "home"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    ours = {(s, m) for s in SETTINGS for m in MYSTERIES}
    clingo_set = set(asp_valid_stories())
    if clingo_set == ours:
        print(f"OK: clingo parity matches Python ({len(ours)} stories).")
        return 0
    print("MISMATCH between clingo and Python parity.")
    print("only in clingo:", sorted(clingo_set - ours))
    print("only in python:", sorted(ours - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life genie, linoleum, and willow mystery stories.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["genie", "girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return select_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
    StoryParams(setting="kitchen", mystery="cup", hero_name="Mina", hero_type="girl", helper_name="Juno", helper_type="genie"),
    StoryParams(setting="hall", mystery="keys", hero_name="Noah", hero_type="boy", helper_name="Paz", helper_type="genie"),
    StoryParams(setting="porch", mystery="spoon", hero_name="Ivy", hero_type="girl", helper_name="Rina", helper_type="genie"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} / {p.mystery} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
