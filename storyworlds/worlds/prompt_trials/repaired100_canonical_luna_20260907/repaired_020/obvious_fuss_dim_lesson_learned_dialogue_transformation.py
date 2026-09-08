#!/usr/bin/env python3
"""
A small whodunit storyworld about an obvious clue, a fuss-dim lantern, and a
lesson learned through honest dialogue and transformation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str = "the little museum"
    lamp_bright: bool = False


@dataclass
class StoryParams:
    place: str = "museum"
    hero: str = "Luna"
    friend: str = "Pip"
    keeper: str = "Mara"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ARCS = [
    {
        "object": "the silver moon badge",
        "home": "a glass case beside the entrance",
        "clue": "a neat trail of blue chalk dust led from the case to the puppet stage",
        "fear": "someone had taken the badge on purpose",
        "truth": "Pip had borrowed it to make a moon for a puppet show, then hid it beneath a cloth",
        "action": "lifted the cloth and returned the badge to its case",
        "lesson": "An obvious clue is worth following, but it is not proof of guilt.",
        "ending": "the badge shone in its case while the puppet moon glowed on stage",
    },
    {
        "object": "the tiny brass key",
        "home": "a locked drawer under the map table",
        "clue": "one bright thread stretched from the drawer to a basket of costumes",
        "fear": "the drawer had been opened by a sneaky visitor",
        "truth": "Mara had used the key for a sorting game and a costume sleeve had caught the thread",
        "action": "followed the thread, found the key in the basket, and closed the drawer",
        "lesson": "A fuss can make a small mistake look like a grand mystery.",
        "ending": "the key rested in its drawer while the costumes waited neatly on their hooks",
    },
    {
        "object": "the painted acorn token",
        "home": "a bowl on the reading table",
        "clue": "a line of crumbs pointed toward the old storybook shelf",
        "fear": "a hungry thief had taken the token",
        "truth": "a mouse had nudged the bowl while chasing crumbs, and the token had rolled behind a book",
        "action": "moved the book, found the token, and swept the crumbs away",
        "lesson": "Before blaming a person, check whether a small creature or a loose object made the trail.",
        "ending": "the token sat in its bowl while the mouse disappeared safely beneath the garden door",
    },
]

OPENINGS = [
    "Rain ticked against the tall windows as",
    "Just before closing time,",
    "Under a pale afternoon sun,",
    "While the visitors whispered through the galleries,",
]

SUSPENSE = [
    "The clue looked so obvious that everyone began to fuss at once.",
    "A tiny mystery grew large because nobody stopped to ask a calm question.",
    "The room went quiet, except for the fuss-dim lantern blinking above the door.",
]


def tell_story(params: StoryParams) -> World:
    if params.hero == params.friend or params.hero == params.keeper:
        raise StoryError("The hero, friend, and keeper must have different names.")
    world = World(Place())
    hero = world.add(Entity(params.hero, "character", "child", params.hero))
    friend = world.add(Entity(params.friend, "character", "child", params.friend))
    keeper = world.add(Entity(params.keeper, "character", "adult", params.keeper))
    hero.memes["curiosity"] = 1.0
    friend.memes["worry"] = 1.0
    keeper.memes["patience"] = 1.0

    arc = ARCS[(params.seed or 0) % len(ARCS)]
    opening = OPENINGS[((params.seed or 0) // len(ARCS)) % len(OPENINGS)]
    suspense = SUSPENSE[((params.seed or 0) // 3) % len(SUSPENSE)]

    world.say(
        f"{opening} {params.hero} visited {world.place.name} with {params.friend}. "
        f"{params.keeper} was checking {arc['home']} when they noticed that {arc['object']} was gone."
    )
    world.para()
    world.say(
        f"{params.hero} pointed to an obvious clue: {arc['clue']}. {suspense} "
        f"{params.friend} worried that {arc['fear']}."
    )
    world.facts["missing"] = arc["object"]
    world.facts["clue"] = arc["clue"]
    world.facts["fear"] = arc["fear"]

    world.say(
        f'"Let us ask before we accuse," said {params.hero}. '
        f'"But what if the clue tells us everything?" asked {params.friend}. '
        f'"It tells us where to look, not whom to blame," said {params.keeper}.'
    )
    world.para()
    world.say(
        f"They followed the clue together and discovered that {arc['truth']}. "
        f"{params.friend} took a slow breath, and the fuss-dim lantern stopped blinking as "
        f"{params.keeper} switched it to a steady glow."
    )
    world.say(f"They {arc['action']}.")
    hero.memes["wisdom"] = 1.0
    friend.memes["relief"] = 1.0
    keeper.memes["trust"] = 1.0
    world.place.lamp_bright = True
    world.facts["truth"] = arc["truth"]
    world.facts["lesson"] = arc["lesson"]

    world.para()
    world.say(
        f"{params.hero} repeated the lesson learned: “{arc['lesson']}” "
        f"{params.friend} nodded and apologized for the fuss. The small investigation had "
        f"transformed the group from quick guessers into careful helpers."
    )
    world.say(
        f"At closing time, {arc['ending']}. The fuss-dim lantern now shone clearly, "
        f"and {params.hero} left knowing that a good detective listens as well as looks."
    )
    world.facts["ending"] = arc["ending"]
    return world


NAMES = ["Luna", "Nia", "Milo", "Tess", "Oren", "Pip"]
KEEPERS = ["Mara", "Ari", "June", "Sol"]
FRIENDS = ["Pip", "Nia", "Milo", "Tess"]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle whodunit with an obvious clue and a fuss-dim lantern.",
        f"Tell how someone discovers what happened to {world.facts['missing']} without blaming the wrong person.",
        "Write a child-facing mystery featuring Lesson Learned, Dialogue, and Transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"What was missing from the little museum?",
            f"The missing object was {f['missing']}.",
        ),
        QAItem(
            "What obvious clue did the investigators notice?",
            f"They noticed that {f['clue']}.",
        ),
        QAItem(
            "What did the group fear at first?",
            f"They feared that {f['fear']}.",
        ),
        QAItem(
            "What did the clue really lead them to understand?",
            f"They discovered that {f['truth']}.",
        ),
        QAItem(
            "What lesson did the characters learn?",
            f"They learned that {f['lesson']}",
        ),
        QAItem(
            "How did the characters change by the ending?",
            "They transformed from quick guessers into careful helpers who listened before blaming.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a whodunit?", "A whodunit is a mystery story about discovering who caused an unusual event."),
        QAItem("What is a clue?", "A clue is a detail that helps people understand what happened."),
        QAItem("Why should people avoid blaming someone too quickly?", "A clue may point toward an answer without proving who is responsible."),
    ]


ASP_RULES = r"""
tension_from_missing :- missing_object.
clue_available :- tension_from_missing.
careful_question :- clue_available.
truth_found :- careful_question.
lesson_learned :- truth_found.
transformed :- lesson_learned.
lamp_steady :- transformed.
#show transformed/0.
#show lamp_steady/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("missing_object"),
        asp.fact("obvious_clue"),
        asp.fact("fuss_dim"),
    ])


def asp_program(show: str = "#show transformed/0.\n#show lamp_steady/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(asp.atoms(model, "transformed") + asp.atoms(model, "lamp_steady"))


def asp_verify() -> int:
    expected = [(), ()]
    actual = asp_outcome()
    if actual == expected:
        print("OK: ASP and Python agree that the characters transform and the lantern steadies.")
        return 0
    print(f"MISMATCH: python={expected} asp={actual}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fuss-dim whodunit storyworld.")
    parser.add_argument("--place", choices=["museum"], default=None)
    parser.add_argument("--hero", choices=NAMES, default=None)
    parser.add_argument("--friend", choices=FRIENDS, default=None)
    parser.add_argument("--keeper", choices=KEEPERS, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend_choices = [x for x in FRIENDS if x != hero]
    friend = args.friend or rng.choice(friend_choices)
    keeper_choices = [x for x in KEEPERS if x not in {hero, friend}]
    keeper = args.keeper or rng.choice(keeper_choices)
    return StoryParams(
        place=args.place or "museum",
        hero=hero,
        friend=friend,
        keeper=keeper,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  lamp_bright={world.place.lamp_bright}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_outcome())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(seed=base_seed))]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
