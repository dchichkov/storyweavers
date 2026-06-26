#!/usr/bin/env python3
"""
storyworlds/worlds/rung_sharing_tall_tale.py
============================================

A small story world in a tall-tale key: one shining rung, two thirsty-for-adventure
kids, and the old frontier lesson that a thing can feel bigger when it is shared.

Premise:
- A hero finds a mighty rung and wants it for themself.
- A friend needs the rung too, because it is the only safe step to reach a goal.
- A grownup warns that keeping the rung alone will stall the whole plan.
- The hero learns to share by taking turns, and the rung becomes a bridge.

State model:
- The rung has physical meters: steadiness, shine, and wear.
- The characters have physical meters: height, reach, and step.
- The characters also have memes: greed, trust, joy, and generosity.
- Sharing changes the world: the rung becomes steadier through use, not less;
  the characters become more trusted and less cross, and the goal is reached.

Style:
- Tall-tale narration, but grounded in simulated state.
- Concrete outcomes, simple causality, child-facing prose.
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
    worn_by: Optional[str] = None
    plural: bool = False
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
    place: str
    sky: str
    goal: str


@dataclass
class StoryParams:
    setting: str
    name: str
    gender: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about sharing a rung.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


SETTINGS = {
    "barnyard": Setting(place="the barnyard", sky="golden", goal="apple"),
    "hilltop": Setting(place="the hilltop", sky="windy", goal="kite"),
    "riverbank": Setting(place="the riverbank", sky="bright", goal="lantern"),
}

GIRL_NAMES = ["Mabel", "Nell", "Ruby", "Hazel", "Ivy"]
BOY_NAMES = ["Hank", "Otis", "Bram", "Jasper", "Cliff"]
FRIENDS = ["sister", "brother", "cousin", "pal", "neighbor"]


def _make_world(setting: Setting, name: str, gender: str, friend: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label=name,
        meters={"step": 2.0, "reach": 1.0},
        memes={"greed": 0.0, "trust": 0.0, "joy": 0.5, "generosity": 0.0},
    ))
    buddy = world.add(Entity(
        id="Friend",
        kind="character",
        type="boy" if gender == "girl" else "girl",
        label=f"the {friend}",
        meters={"step": 1.5, "reach": 1.5},
        memes={"greed": 0.0, "trust": 0.5, "joy": 0.5, "generosity": 0.0},
    ))
    rung = world.add(Entity(
        id="rung",
        kind="thing",
        type="rung",
        label="a ladder rung",
        phrase="a stout ladder rung as wide as a cornbread plate",
        owner=hero.id,
        meters={"steadiness": 1.0, "shine": 1.0, "wear": 0.0},
        memes={"pride": 1.0},
    ))
    world.facts.update(hero=hero, buddy=buddy, rung=rung)
    return world


def _narrate_setup(world: World) -> None:
    hero = world.facts["hero"]
    buddy = world.facts["buddy"]
    rung = world.facts["rung"]
    s = world.setting
    world.say(
        f"{hero.id} was a little {hero.type} with a big heart and a pair of quick feet."
    )
    world.say(
        f"One day at {s.place}, {hero.id} found {rung.phrase} gleaming like a slice of sunrise."
    )
    world.say(
        f"{hero.id} wanted {rung.it()} all to themself, but {buddy.label} had a tall need and a small grin."
    )


def _warn(world: World) -> None:
    hero = world.facts["hero"]
    buddy = world.facts["buddy"]
    rung = world.facts["rung"]
    goal = world.setting.goal
    world.say(
        f'"If you keep that rung to yourself," said {buddy.label}, '
        f'"we may never reach the {goal} up yonder."'
    )
    hero.memes["greed"] += 1.0
    hero.memes["trust"] += 0.0
    world.say(
        f"{hero.id} hugged the rung tighter, and the big sky seemed to wait and listen."
    )
    if hero.memes["greed"] >= THRESHOLD:
        world.say(
            f"{hero.id} tried to stand on the rung alone, but a lonely rung is a wobbling thing."
        )


def _share(world: World) -> None:
    hero = world.facts["hero"]
    buddy = world.facts["buddy"]
    rung = world.facts["rung"]
    goal = world.setting.goal

    hero.memes["generosity"] += 1.0
    hero.memes["greed"] = 0.0
    hero.memes["trust"] += 1.0
    buddy.memes["trust"] += 1.0
    buddy.memes["joy"] += 0.5
    rung.meters["steadiness"] += 0.5
    rung.meters["wear"] += 0.2

    world.say(
        f"Then {hero.id} said, 'You can have the next turn on the rung, and I can have the one after that.'"
    )
    world.say(
        f"So {hero.id} and {buddy.label} shared the rung like two birds sharing one warm fence rail."
    )
    world.say(
        f"Each took a turn stepping up, and each turn made the rung feel steadier, not smaller."
    )
    world.say(
        f"At last they reached the {goal}, and the sky looked so bright it could have been painted with laughter."
    )
    world.say(
        f"{hero.id} kept the rung only by sharing it, and that was the tallest trick of all."
    )


def tell(setting: Setting, name: str, gender: str, friend: str) -> World:
    world = _make_world(setting, name, gender, friend)
    _narrate_setup(world)
    world.para()
    _warn(world)
    world.para()
    _share(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    goal = world.setting.goal
    return [
        f'Write a tall-tale story for a young child about "{hero.id}" and a shared rung.',
        f"Tell a funny, gentle story where {hero.id} learns to share a rung so {hero.id} and {f['buddy'].label} can reach the {goal}.",
        f"Write a short story with a big-sounding rung, a turn-taking problem, and a happy shared ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    buddy = world.facts["buddy"]
    goal = world.setting.goal
    return [
        QAItem(
            question=f"Why did {hero.id} first want the rung to themself?",
            answer=f"{hero.id} thought the rung was a wonderful treasure and wanted to keep that shining rung all to themself at first.",
        ),
        QAItem(
            question=f"What did {buddy.label} say would happen if the rung was not shared?",
            answer=f"{buddy.label} said they might never reach the {goal} up high unless the rung was shared.",
        ),
        QAItem(
            question=f"How did {hero.id} and {buddy.label} use the rung in the end?",
            answer=f"They took turns on the rung, and that sharing helped them reach the {goal} together.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after sharing?",
            answer=f"{hero.id} felt proud, kinder, and much happier once the rung was shared instead of guarded.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rung?",
            answer="A rung is one of the bar-shaped steps on a ladder that you can hold or stand on to climb upward.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something too, or taking turns so more than one person can enjoy it.",
        ),
        QAItem(
            question="Why is turn-taking helpful?",
            answer="Turn-taking is helpful because it lets everyone get a fair chance without making the fun stop for others.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: meters={{{', '.join(f'{k}: {v:.1f}' for k, v in e.meters.items())}}} "
            f"memes={{{', '.join(f'{k}: {v:.1f}' for k, v in e.memes.items())}}}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(setting=setting, name=name, gender=gender, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.name, params.gender, params.friend)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
#show shared/2.
#show ready/1.

shared(hero, buddy) :- wants(hero, rung), needs(buddy, goal), not hoards(hero, rung).
ready(goal) :- shared(hero, buddy), goal_needed(goal).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("goal_needed", s.goal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show ready/1."))
    _ = asp.atoms(model, "ready")
    print("OK: ASP program loads and solves.")
    return 0


CURATED = [
    StoryParams(setting="barnyard", name="Mabel", gender="girl", friend="brother"),
    StoryParams(setting="hilltop", name="Hank", gender="boy", friend="sister"),
    StoryParams(setting="riverbank", name="Ivy", gender="girl", friend="cousin"),
]


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
        print(asp_program("#show ready/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show shared/2.\n#show ready/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
