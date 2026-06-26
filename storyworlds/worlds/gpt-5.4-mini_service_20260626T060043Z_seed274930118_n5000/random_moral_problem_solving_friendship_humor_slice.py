#!/usr/bin/env python3
"""
A small slice-of-life story world about friendship, a little problem, and a
moral choice that can go gently right.

Premise:
- A child notices a small problem during an ordinary day.
- A friend wants to help, but a choice must be made about honesty, kindness,
  and fixing the mess without making it bigger.
- The ending proves something changed in the world: the problem is solved, the
  friendship holds, and the room feels lighter.

This world is intentionally small and constraint-checked. It only generates
stories where:
- the problem is real,
- there is a believable helper/friendship path,
- the moral choice is about returning, admitting, sharing, or repairing,
- the humor comes from a concrete, harmless, physical mishap or misunderstanding.
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
class Thing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Friend:
    id: str
    label: str
    kind: str = "character"
    type: str = "child"
    pronoun: str = "they"
    possessive: str = "their"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    afford: str


@dataclass
class Trouble:
    id: str
    title: str
    problem: str
    action: str
    mistake: str
    fix: str
    moral: str
    humor: str
    outcome: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    trouble: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Thing | Friend] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "classroom": Setting("the classroom", "share"),
    "playground": Setting("the playground", "share"),
    "kitchen": Setting("the kitchen", "borrow"),
    "library": Setting("the library", "return"),
}

TROUBLES = {
    "lost_marker": Trouble(
        id="lost_marker",
        title="lost marker",
        problem="a bright marker went missing from the art bin",
        action="find the marker",
        mistake="the marker had rolled into a silly place",
        fix="look in the cookie jar, where it got stuck by accident",
        moral="being honest about a mistake helps everyone fix it faster",
        humor="the marker was wearing a crumby disguise",
        outcome="the marker was returned to the art bin",
        tags={"problem", "friendship", "honesty", "humor"},
    ),
    "spilled_snack": Trouble(
        id="spilled_snack",
        title="spilled snack",
        problem="a bowl of crackers tipped over under the table",
        action="clean it up",
        mistake="the crackers had scattered like tiny ships",
        fix="use a napkin, then a broom, then a careful hand",
        moral="when you spill something, saying so right away is kinder than hiding it",
        humor="one cracker slid under a chair like it was in a race",
        outcome="the floor was swept clean again",
        tags={"problem", "kindness", "sharing", "humor"},
    ),
    "mixed_up_bag": Trouble(
        id="mixed_up_bag",
        title="mixed-up bag",
        problem="two lunch bags got swapped by accident",
        action="sort out the bags",
        mistake="both names looked too similar in a hurry",
        fix="read the labels slowly and switch them back",
        moral="taking a slow second look can be a very good kind choice",
        humor="one bag had a banana peeking out like a little yellow hat",
        outcome="each child got the right lunch bag back",
        tags={"problem", "moral", "friendship", "humor"},
    ),
    "broken_crayon": Trouble(
        id="broken_crayon",
        title="broken crayon",
        problem="a blue crayon snapped in half during drawing time",
        action="make the drawing work anyway",
        mistake="the broken pieces looked too small to do much",
        fix="use both pieces and make the crack part of the drawing",
        moral="a mistake does not have to ruin the whole picture",
        humor="the crayon looked like it had a surprised face",
        outcome="the picture became a funny rocket with a cracked window",
        tags={"problem", "creativity", "friendship", "humor"},
    ),
}

HEROES = [
    ("Mina", "she", "her"),
    ("Owen", "he", "his"),
    ("Tessa", "she", "her"),
    ("Leo", "he", "his"),
    ("Nico", "he", "his"),
    ("Pia", "she", "her"),
]

FRIENDS = [
    ("June", "she", "her"),
    ("Sam", "they", "their"),
    ("Ben", "he", "his"),
    ("Lia", "she", "her"),
    ("Max", "he", "his"),
    ("Rin", "they", "their"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with friendship, problem solving, and humor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    trouble = args.trouble or rng.choice(list(TROUBLES))
    hero = args.hero or rng.choice([h[0] for h in HEROES])
    friend = args.friend or rng.choice([f[0] for f in FRIENDS])
    if hero == friend:
        raise StoryError("The hero and friend must be different children.")
    return StoryParams(setting=setting, trouble=trouble, hero=hero, friend=friend)


def _pick_child(name: str, table) -> Friend:
    for row in table:
        if row[0] == name:
            return Friend(id=row[0], label=row[0], pronoun=row[1], possessive=row[2])
    raise StoryError(f"Unknown child name: {name}")


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    trouble = TROUBLES[params.trouble]
    hero = _pick_child(params.hero, HEROES)
    friend = _pick_child(params.friend, FRIENDS)
    world = World(setting)
    world.facts.update(setting=setting, trouble=trouble, hero=hero, friend=friend)

    prop = {
        "lost_marker": Thing("marker", label="marker", phrase="a bright red marker", owner=hero.id, location="floor"),
        "spilled_snack": Thing("crackers", label="crackers", phrase="a bowl of crackers", owner=friend.id, location="table"),
        "mixed_up_bag": Thing("bag", label="lunch bag", phrase="a lunch bag", owner=hero.id, location="bench"),
        "broken_crayon": Thing("crayon", label="crayon", phrase="a blue crayon", owner=friend.id, location="desk"),
    }[trouble.id]
    world.add(hero)
    world.add(friend)
    world.add(prop)

    hero.memes["curious"] = 1.0
    hero.memes["care"] = 1.0
    friend.memes["care"] = 1.0

    world.say(
        f"{hero.id} was in {setting.place}, where the day felt ordinary and calm. "
        f"{friend.id} was there too, and the two of them had the easy kind of friendship that makes small things feel safe."
    )
    world.say(
        f"Then a little problem popped up: {trouble.problem}. "
        f"It was the kind of mix-up that made everyone pause for a second."
    )
    world.para()
    world.say(
        f"{hero.id} and {friend.id} looked at the mess together. "
        f"{trouble.humor.capitalize()}, which made them both snort a little, because even a serious moment can wobble into a silly one."
    )
    world.say(
        f"{hero.id} wanted to {trouble.action}, but the first idea was not enough on its own. "
        f"So {hero.id} slowed down, noticed {trouble.mistake}, and thought about what would be the honest thing to do."
    )
    world.para()
    world.say(
        f"Together they chose to {trouble.fix}. "
        f"{friend.id} helped without taking over, and {hero.id} admitted what had happened instead of pretending it was fine."
    )
    world.say(
        f"That was the moral part of the day: {trouble.moral}. "
        f"Because they spoke up and helped each other, {trouble.outcome}, and the room felt lighter again."
    )

    world.facts["resolved"] = True
    world.facts["tro"] = trouble
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trouble: Trouble = f["trouble"]
    hero: Friend = f["hero"]
    friend: Friend = f["friend"]
    return [
        f"Write a gentle slice-of-life story about {hero.id} and {friend.id} solving a small problem at {world.setting.place}.",
        f"Tell a child-friendly story where honesty and friendship help fix {trouble.problem}.",
        f"Write a short story with a funny little mishap, a kind choice, and a happy repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    trouble: Trouble = f["trouble"]
    hero: Friend = f["hero"]
    friend: Friend = f["friend"]
    return [
        QAItem(
            question=f"What problem came up for {hero.id} and {friend.id}?",
            answer=f"The problem was that {trouble.problem}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} solve it?",
            answer=f"They worked together and chose to {trouble.fix}.",
        ),
        QAItem(
            question=f"What was the moral of the story?",
            answer=trouble.moral.capitalize() + ".",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    trouble: Trouble = f["trouble"]
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring relationship where people help, listen, and have fun together.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to figure out a way to make the trouble smaller or go away.",
        ),
        QAItem(
            question="Why can a small mistake feel funny?",
            answer="A small mistake can feel funny when nobody is hurt and the mix-up looks a little silly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.location:
            bits.append(f"location={ent.location}")
        lines.append(f"{ent.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(classroom).
setting(playground).
setting(kitchen).
setting(library).

trouble(lost_marker).
trouble(spilled_snack).
trouble(mixed_up_bag).
trouble(broken_crayon).

solvable(S, T) :- setting(S), trouble(T).
#show solvable/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/2."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    py = sorted((s, t) for s in SETTINGS for t in TROUBLES)
    cl = asp_valid()
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH:")
    print("Python only:", sorted(set(py) - set(cl)))
    print("Clingo only:", sorted(set(cl) - set(py)))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in TROUBLES]


def resolve_all(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    combos = valid_combos()
    out: list[StoryParams] = []
    for setting, trouble in combos:
        out.append(StoryParams(
            setting=setting,
            trouble=trouble,
            hero=rng.choice([h[0] for h in HEROES]),
            friend=rng.choice([f[0] for f in FRIENDS]),
            seed=None,
        ))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solvable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible combinations:")
        for s, t in combos:
            print(f"  {s:11} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = resolve_all(args, random.Random(base_seed))
        for i, p in enumerate(params_list):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
