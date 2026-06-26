#!/usr/bin/env python3
"""
storyworlds/worlds/dell_bin_rhyme_sound_effects_fable.py
=========================================================

A small fable-like storyworld about a child, a busy dell, and a bin
that must be used wisely. The story carries rhyme and sound effects,
and it simulates a concrete change in the world: waste goes into the
right bin, the dell stays neat, and the hero learns a small lesson.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dell"
    rhyme_words: tuple[str, str] = ("hill", "still")


@dataclass
class Action:
    id: str
    verb: str
    noise: str
    change: str
    risk: str
    echo: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BinType:
    id: str
    label: str
    accepts: set[str]
    rhyme: str
    sound: str


@dataclass
class StoryParams:
    action: str
    bin: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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


ACTIONS = {
    "peel": Action(
        id="peel",
        verb="peel fruit",
        noise="snip-snap",
        change="mushy",
        risk="sticky peels",
        echo="snap, snap, snip",
        tags={"food", "messy"},
    ),
    "paper": Action(
        id="paper",
        verb="tear paper scraps",
        noise="rip-rip",
        change="fluttery",
        risk="little paper bits",
        echo="rip, rip, tap",
        tags={"paper", "messy"},
    ),
    "shell": Action(
        id="shell",
        verb="crack nuts open",
        noise="clack-clack",
        change="crunchy",
        risk="crumbs",
        echo="clack, clack, crack",
        tags={"nuts", "messy"},
    ),
}

BINS = {
    "compost": BinType(
        id="compost",
        label="compost bin",
        accepts={"food"},
        rhyme="slow",
        sound="plop",
    ),
    "paper": BinType(
        id="paper",
        label="paper bin",
        accepts={"paper"},
        rhyme="near",
        sound="swish",
    ),
    "snack": BinType(
        id="snack",
        label="snack bin",
        accepts={"nuts"},
        rhyme="track",
        sound="clink",
    ),
}

HEROES = [
    ("Ava", "girl"),
    ("Milo", "boy"),
    ("Nia", "girl"),
    ("Theo", "boy"),
    ("Mina", "girl"),
    ("Owen", "boy"),
]

TRAITS = ["kind", "curious", "gentle", "brave", "patient", "careful"]


def rhyming_line(action: Action, setting: Setting, bin_type: BinType) -> str:
    a, b = setting.rhyme_words
    return f"In the {setting.place.removeprefix('the ')}, near the {a} and the {b}, the {bin_type.label} waited bright."


def noise_line(action: Action) -> str:
    return f"{action.noise}! {action.echo}! The little sound danced through the air."


def can_use_bin(action: Action, bin_type: BinType) -> bool:
    if action.id == "peel":
        return "food" in bin_type.accepts
    if action.id == "paper":
        return "paper" in bin_type.accepts
    if action.id == "shell":
        return "nuts" in bin_type.accepts
    return False


def build_setting() -> Setting:
    return Setting(place="the dell", rhyme_words=("hill", "still"))


def tell(params: StoryParams) -> World:
    world = World(build_setting())
    action = ACTIONS[params.action]
    bin_type = BINS[params.bin]

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    guide = world.add(Entity(id="Guide", kind="character", type=params.guide, label=params.guide))
    bin_ent = world.add(Entity(id=bin_type.id, type="bin", label=bin_type.label, phrase=bin_type.label))

    hero.memes["curiosity"] = 1.0
    hero.memes["responsibility"] = 0.0
    world.facts.update(hero=hero, guide=guide, action=action, bin=bin_type)

    world.say(
        f"{hero.id} was a {params.trait} child who liked the quiet dell, "
        f"where the grass went soft and the stream went low."
    )
    world.say(
        f"{hero.id} loved to {action.verb}, and every time {hero.pronoun()} did, "
        f"there came a merry {action.noise}."
    )
    world.say(rhyming_line(action, world.setting, bin_type))

    world.para()
    world.say(
        f"One day, {hero.id} found {action.risk} on the path."
    )
    world.say(noise_line(action))
    hero.memes["wanting"] = 1.0
    hero.meters[action.id] = 1.0
    world.events.append("mess-started")

    if can_use_bin(action, bin_type):
        world.say(
            f"{guide.id} pointed to the {bin_type.label} and said, "
            f"\"Tidy in, no pity out.\""
        )
        world.say(
            f"{hero.id} listened, and the {action.risk} went {bin_type.sound}! into the bin."
        )
        hero.meters[f"kept_{action.id}_tidy"] = 1.0
        bin_ent.meters["full"] = 1.0
        world.events.append("used-correct-bin")
        hero.memes["responsibility"] = 1.0
    else:
        raise StoryError("This bin does not fit the action in a reasonable fable.")

    world.para()
    world.say(
        f"By sunset, the dell stayed clean and the path stayed neat."
    )
    world.say(
        f"{hero.id} smiled, for a small good choice can make a big good place."
    )
    world.say(
        f"And so the lesson went: take care, make share, and keep the dell fair."
    )
    world.events.append("lesson-learned")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    b = f["bin"]
    return [
        f'Write a short fable for a child about a dell, a {b.label}, and the sound "{action.noise}".',
        f"Tell a rhyme-filled story where {hero.id} learns to use the {b.label} after a messy moment.",
        f"Write a gentle story with sound effects that ends with the dell staying tidy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    b = f["bin"]
    guide = f["guide"]
    return [
        QAItem(
            question=f"What did {hero.id} love to do in the dell?",
            answer=f"{hero.id} loved to {action.verb}, and it made a cheerful {action.noise} sound.",
        ),
        QAItem(
            question=f"What did {guide.id} point to when {hero.id} needed help?",
            answer=f"{guide.id} pointed to the {b.label}, because it was the right place for {action.risk}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer="The mess went into the bin, and the dell stayed clean and peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    action = f["action"]
    b = f["bin"]
    out = [
        QAItem(
            question="What is a dell?",
            answer="A dell is a small valley or hollow place, often green and quiet.",
        ),
        QAItem(
            question="What is a bin for?",
            answer="A bin is for putting things away, especially trash or sorting things neatly.",
        ),
    ]
    if action.id == "peel":
        out.append(QAItem(
            question="What is compost for?",
            answer="Compost is for food scraps and other natural bits that can break down over time.",
        ))
    if b.id == "paper":
        out.append(QAItem(
            question="Why can paper go in a paper bin?",
            answer="Paper can be collected together so it can be reused or recycled.",
        ))
    return out


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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  events: {world.events}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for tag in sorted(a.tags):
            lines.append(asp.fact("tag", aid, tag))
    for bid, b in BINS.items():
        lines.append(asp.fact("bin", bid))
        for kind in sorted(b.accepts):
            lines.append(asp.fact("accepts", bid, kind))
    return "\n".join(lines)


ASP_RULES = r"""
need_bin(A,B) :- action(A), bin(B), tag(A,K), accepts(B,K).
valid(A,B) :- need_bin(A,B).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_pairs() -> list[tuple[str, str]]:
    return [("peel", "compost"), ("paper", "paper"), ("shell", "snack")]


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_pairs())
    b = set(valid_pairs())
    if a == b:
        print(f"OK: clingo gate matches valid_pairs() ({len(a)} pairs).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld about a dell and a bin.")
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--bin", dest="bin_name", choices=BINS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    pairs = valid_pairs()
    if args.action and args.bin_name and (args.action, args.bin_name) not in pairs:
        raise StoryError("That action and bin do not match in this fable world.")
    valid = [p for p in pairs if (args.action is None or p[0] == args.action) and (args.bin_name is None or p[1] == args.bin_name)]
    if not valid:
        raise StoryError("No valid action/bin pair matches the given options.")
    action, bin_name = rng.choice(valid)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice([n for n, g in HEROES if g == gender])
    guide = args.guide or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(action=action, bin=bin_name, name=name, gender=gender, guide=guide, trait=trait)


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
    StoryParams(action="peel", bin="compost", name="Ava", gender="girl", guide="mother", trait="kind"),
    StoryParams(action="paper", bin="paper", name="Milo", gender="boy", guide="father", trait="curious"),
    StoryParams(action="shell", bin="snack", name="Nia", gender="girl", guide="father", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible action/bin pairs:")
        for a, b in pairs:
            print(f"  {a:8} -> {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
