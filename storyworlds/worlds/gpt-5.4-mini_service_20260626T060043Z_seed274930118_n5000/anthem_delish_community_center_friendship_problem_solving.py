#!/usr/bin/env python3
"""
A small pirate-style storyworld set in a community center.

Premise:
A crew of children is preparing a cheerful anthem for a community center gathering.
A tasty delish snack goes missing, feelings get tangled, and friendship plus problem
solving turns the day around. The ending shows a transformation in both mood and
how the community center feels.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str = "the community center"
    vibe: str = "bright and busy"


@dataclass
class Treasure:
    label: str
    phrase: str
    delight: str
    owner_role: str = "friend"


@dataclass
class Trouble:
    label: str
    verb: str
    risk: str
    fix: str
    transformation: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


@dataclass
class StoryParams:
    name: str
    friend: str
    role: str
    trouble: str
    seed: Optional[int] = None


SETTINGS = {
    "community_center": Place(name="the community center", vibe="warm and busy"),
}

TROUBLES = {
    "missing_snack": Trouble(
        label="missing delish snack",
        verb="find the missing snack",
        risk="the party would feel gloomy without the snack",
        fix="share clues and look together",
        transformation="the snack table became a happy feast table",
    ),
    "broken_anthem": Trouble(
        label="crooked anthem sheet",
        verb="fix the anthem",
        risk="the crew could not sing together if the words were jumbled",
        fix="sort the verses and sing line by line",
        transformation="the hall rang like a proud ship at sea",
    ),
    "torn_banner": Trouble(
        label="torn banner",
        verb="repair the banner",
        risk="the room would lose its welcome",
        fix="patch the banner with ribbon and tape",
        transformation="the hall looked new and grand",
    ),
}

NAMES = ["Maya", "Tessa", "Noah", "Ari", "Nina", "Theo", "Luca", "Iris"]
FRIENDS = ["mate", "pal", "shipmate", "friend", "crewmate"]
ROLES = ["captain", "helper", "singer", "lookout", "planner"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-style friendship and problem solving in a community center.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--trouble", choices=list(TROUBLES))
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
    trouble = args.trouble or rng.choice(list(TROUBLES))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    role = args.role or rng.choice(ROLES)
    return StoryParams(name=name, friend=friend, role=role, trouble=trouble)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS["community_center"])
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.name, traits=["brave", "kind"]))
    friend = world.add(Entity(id="friend", kind="character", type="child", label=params.friend, traits=["loyal"]))
    treasure = world.add(Entity(id="treasure", type="snack", label="delish snack", phrase="a delish snack tray"))
    anthem = world.add(Entity(id="anthem", type="song", label="anthem", phrase="a proud anthem sheet"))

    t = TROUBLES[params.trouble]
    world.facts.update(hero=hero, friend=friend, treasure=treasure, anthem=anthem, trouble=t, params=params)

    hero.memes["hope"] = 1
    friend.memes["loyalty"] = 1
    world.say(f"In the {world.place.name}, {hero.label} and their {params.friend} stood like small pirates in a bright harbor.")
    world.say(f"They were ready for an anthem, a cheer of courage that could lift every heart in the hall.")
    if params.trouble == "broken_anthem":
        world.say(f"But the anthem page had gone crooked, and the words leaned like a ship in rough wind.")
    else:
        world.say(f"Yet a {t.label} made the day wobble, and the room lost a bit of its sparkle.")

    world.para()
    hero.memes["trouble"] = 1
    friend.memes["support"] = 1
    world.say(f"{hero.label} did not give up. {hero.label.capitalize()} told {params.friend} they would solve it together, mate by mate.")
    if params.trouble == "missing_snack":
        world.say(f"They searched the tables, the benches, and the game shelf until they found crumbs near the craft corner.")
        world.say(f"That clue showed them the snack had been moved, not lost forever.")
    elif params.trouble == "broken_anthem":
        world.say(f"They smoothed the anthem sheet, traced the lines with a finger, and sang one line at a time.")
        world.say(f"Friendship kept the tune steady, even when the paper had been messy.")
    else:
        world.say(f"They patched the torn banner with ribbon, holding one side while the other side pressed flat.")
        world.say(f"It was a slow job, but their steady hands made the fix feel like a voyage worth taking.")

    world.para()
    hero.memes["joy"] = 2
    friend.memes["joy"] = 2
    hero.memes["transformation"] = 1
    world.say(f"At last, the {t.transformation}.")
    world.say(f"The friends laughed, and the community center felt different now—warmer, braver, and more like a shared ship.")
    world.say(f"They sang the anthem together, and the delish snack was shared with everyone after the work was done.")
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    t = world.facts["trouble"]
    return [
        f'Write a short pirate-style story set in a community center with an anthem and a delish snack.',
        f"Tell a child-friendly tale where {p.name} and a {p.friend} solve a {t.label} problem with friendship.",
        f"Write a story about a brave little crew whose anthem helps transform the community center.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    t = world.facts["trouble"]
    return [
        QAItem(
            question=f"Who worked together in the community center?",
            answer=f"{p.name} and their {p.friend} worked together like a tiny pirate crew.",
        ),
        QAItem(
            question=f"What problem needed problem solving?",
            answer=f"They had to deal with a {t.label} so the day could go right again.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The community center transformed into a warmer, happier place, and everyone could sing the anthem and share the delish snack.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an anthem?",
            answer="An anthem is a special song people sing together to show pride, friendship, or celebration.",
        ),
        QAItem(
            question="What does delish mean?",
            answer="Delish means very tasty and delicious.",
        ),
        QAItem(
            question="What is a community center?",
            answer="A community center is a place where people gather for activities, games, meals, and events.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {e.label:16} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_present(H) :- hero(H).
friend_present(F) :- friend(F).
problem_solving(T) :- trouble(T).
transformed(C) :- setting(C), solved(_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", "community_center")]
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
    lines.append(asp.fact("anthem", "anthem"))
    lines.append(asp.fact("delish", "delish"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show trouble/1."))
        if model is None:
            print("OK: ASP available.")
        else:
            print("OK: ASP program loaded.")
        return 0
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1


CURATED = [
    StoryParams(name="Maya", friend="mate", role="captain", trouble="missing_snack"),
    StoryParams(name="Noah", friend="crewmate", role="lookout", trouble="broken_anthem"),
    StoryParams(name="Iris", friend="pal", role="planner", trouble="torn_banner"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show trouble/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show trouble/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.trouble} in the community center"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
