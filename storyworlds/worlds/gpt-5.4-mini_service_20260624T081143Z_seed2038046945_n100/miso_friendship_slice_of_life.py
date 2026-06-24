#!/usr/bin/env python3
"""
Storyworld: miso friendship slice-of-life

A small, self-contained storyworld about a child, a little mishap, and a
friendship-centered fix. The world is grounded in a quiet daily-life setting:
a kitchen, a shared snack, a small spill, and a gentle repair of feelings.

The seed word is "miso"; the narrative instrument is friendship, and the style
leans slice-of-life: ordinary actions, concrete objects, and a calm ending that
shows what changed.
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

# World constants
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "hurt": 0.0, "kindness": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str


@dataclass
class Snack:
    label: str
    phrase: str
    region: str = "table"


@dataclass
class StoryParams:
    place: str
    action: str
    snack: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affordances={"miso"}),
    "dining_room": Setting(place="the dining room", affordances={"miso"}),
    "tiny_cafe": Setting(place="the little cafe", affordances={"miso"}),
}

ACTIONS = {
    "miso": Action(
        id="miso",
        verb="stir the miso soup",
        gerund="stirring miso soup",
        rush="reach for the spoon too fast",
        mess="splash",
        soil="splattered",
        keyword="miso",
    )
}

SNACKS = {
    "miso": Snack(label="miso soup", phrase="a warm bowl of miso soup"),
}

HERO_NAMES = ["Mina", "Haru", "Sora", "Nori", "Kiko", "Tao", "Aki", "Momo"]
FRIEND_NAMES = ["Jun", "Aya", "Rin", "Yuki", "Noa", "Emi", "Kai", "Rei"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about miso and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    action = args.action or "miso"
    snack = args.snack or "miso"
    if action not in SETTINGS[place].affordances:
        raise StoryError("That place does not support this quiet miso story.")
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, action=action, snack=snack, hero=hero, friend=friend)


def _story_sentence(*parts: str) -> str:
    return " ".join(parts)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.hero))
    friend = world.add(Entity(id="friend", kind="character", type="child", label=params.friend))
    bowl = world.add(Entity(id="bowl", type="bowl", label="bowl", phrase="a small bowl", caretaker=hero.id))
    table = world.add(Entity(id="table", type="table", label="table", phrase="the table"))
    spoon = world.add(Entity(id="spoon", type="spoon", label="spoon", phrase="a wooden spoon", owner=hero.id))

    action = ACTIONS[params.action]
    snack = SNACKS[params.snack]

    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.label} and {friend.label} sat at {world.setting.place} together, "
        f"happy to share {snack.phrase}."
    )
    world.say(
        f"{hero.label} liked the rich smell of miso, and {friend.label} smiled because quiet afternoons felt nice."
    )

    world.para()
    world.say(
        f"{hero.label} wanted to {action.verb}, but when {hero.pronoun()} tried to "
        f"{action.rush}, the spoon bumped the bowl and {action.soil} a little soup onto the table."
    )
    bowl.meters["mess"] += 1
    table.meters["mess"] += 1
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"{friend.label} did not laugh. {friend.label} leaned closer and said they could clean it up together."
    )

    world.para()
    hero.memes["hurt"] += 0.5
    hero.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"So {hero.label} wiped the table with a napkin while {friend.label} held the bowl steady."
    )
    world.say(
        f"After that, {hero.label} stirred more slowly, and the warm miso smelled even better than before."
    )
    world.say(
        f"By the end, the table was clean, the soup was safe, and the two friends were laughing softly again."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        bowl=bowl,
        table=table,
        spoon=spoon,
        action=action,
        snack=snack,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    action = f["action"]
    snack = f["snack"]
    return [
        f"Write a gentle slice-of-life story about {hero.label} and {friend.label} sharing {snack.phrase}.",
        f"Tell a short friendship story where someone wants to {action.verb} and a small spill gets cleaned up kindly.",
        f"Write a child-friendly story that includes miso, a shared table, and friends helping each other after a tiny mess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    snack = f["snack"]
    action = f["action"]
    return [
        QAItem(
            question=f"Who shared the miso soup at {world.setting.place}?",
            answer=f"{hero.label} and {friend.label} shared {snack.phrase} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do with the soup?",
            answer=f"{hero.label} wanted to {action.verb}.",
        ),
        QAItem(
            question="What happened when the spoon moved too fast?",
            answer="The spoon bumped the bowl and a little soup splashed onto the table.",
        ),
        QAItem(
            question=f"How did the friendship help after the spill?",
            answer=f"{friend.label} stayed calm, and {hero.label} cleaned the table while {friend.label} held the bowl steady.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is miso?",
            answer="Miso is a savory paste made from fermented soybeans, often used to make soup.",
        ),
        QAItem(
            question="Why do friends help clean a spill?",
            answer="Friends help clean a spill because it makes the problem smaller and keeps the shared space nice for everyone.",
        ),
        QAItem(
            question="What is a slice-of-life story?",
            answer="A slice-of-life story is about an ordinary moment from daily life, like sharing food, talking, or helping after a small mistake.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
valid_story(Place, Action, Snack) :- place(Place), action(Action), snack(Snack), affords(Place, Action).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for action in sorted(setting.affordances):
            lines.append(asp.fact("affords", place, action))
    for action in ACTIONS:
        lines.append(asp.fact("action", action))
    for snack in SNACKS:
        lines.append(asp.fact("snack", snack))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, a, s) for p in SETTINGS for a in ACTIONS for s in SNACKS if a in SETTINGS[p].affordances}
    ap = set(asp_valid())
    if py == ap:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - ap))
    print("asp-only:", sorted(ap - py))
    return 1


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:6} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="kitchen", action="miso", snack="miso", hero="Mina", friend="Jun"),
    StoryParams(place="dining_room", action="miso", snack="miso", hero="Haru", friend="Aya"),
    StoryParams(place="tiny_cafe", action="miso", snack="miso", hero="Sora", friend="Rin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
