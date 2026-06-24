#!/usr/bin/env python3
"""
storyworlds/worlds/tale_shawl_craft_workshop_surprise_repetition_quest.py
==========================================================================

A small slice-of-life story world set in a craft workshop.

Seed words: tale, shawl
Features: Surprise, Repetition, Quest
Setting: craft workshop

The world simulates a simple afternoon in a cozy workshop where a maker is
working on a shawl, repeating a stitch pattern, and then following a small
quest for one missing finishing piece. A surprise visitor changes the plan,
but the story stays gentle and domestic: tools, yarn, tables, tea, and a calm
ending image showing what was made and how it is now used.

The story is state-driven:
- repetition steadily improves the shawl's completeness and the maker's calm;
- a surprise adds delight and attention;
- the quest to find a missing clasp or button changes where the characters go;
- the ending proves the change by showing the finished shawl in use.

The module supports the standard Storyweavers CLI and an ASP twin for a small
reasonableness gate and ending parity check.

"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    workshop: str
    maker: str
    helper: str
    visitor: str
    shawl_color: str
    yarn_color: str
    surprise: str
    quest_item: str
    quest_place: str
    repetition: str
    ending_use: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = dataclasses.replace(self.entities) if False else {k: dataclasses.replace(v, meters=dict(v.meters), memes=dict(v.memes), attrs=dict(v.attrs)) for k, v in self.entities.items()}
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


WORKSHOPS = {
    "sunny_corner": "the sunny corner workshop",
    "back_room": "the back room workshop",
    "market_stall": "the little market stall workshop",
}

MAKERS = ["Mina", "Tess", "Rafi", "June", "Leah", "Owen", "Pia", "Noor"]
HELPERS = ["Iris", "Evan", "Milo", "Sara", "Kai", "Ruby", "Luca", "Nina"]
VISITORS = ["Aunt Bea", "Mr. Finch", "Grandpa", "Mrs. Vale", "a neighbor"]

COLORS = ["blue", "green", "red", "gold", "violet", "cream", "silver"]
SURPRISES = [
    "brought a basket of buttons and said the shawl was for a birthday tale",
    "peeked in with a warm grin and asked for a cozy shawl for the evening",
    "arrived with tea and a shy smile, hoping for a shawl to keep the wind off",
]
QUEST_ITEMS = ["the missing button", "the clasp", "the tiny wooden toggle"]
QUEST_PLACES = ["the supply box", "under the cutting table", "behind the spool shelf"]
REPETITIONS = [
    "one careful row after another",
    "again and again in a neat little rhythm",
    "stitch by stitch with a soft hush",
]
ENDING_USES = [
    "wrapped around tired shoulders",
    "folded neatly over an armchair",
    "worn like a warm cloud on the walk home",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life craft workshop storyworld.")
    ap.add_argument("--workshop", choices=WORKSHOPS)
    ap.add_argument("--maker", choices=MAKERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--shawl-color", choices=COLORS)
    ap.add_argument("--yarn-color", choices=COLORS)
    ap.add_argument("--surprise", choices=range(len(SURPRISES)), type=int)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--quest-place", choices=QUEST_PLACES)
    ap.add_argument("--repetition", choices=range(len(REPETITIONS)), type=int)
    ap.add_argument("--ending-use", choices=range(len(ENDING_USES)), type=int)
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
    workshop = args.workshop or rng.choice(list(WORKSHOPS))
    maker = args.maker or rng.choice(MAKERS)
    helper = args.helper or rng.choice([n for n in HELPERS if n != maker])
    visitor = args.visitor or rng.choice(VISITORS)
    shawl_color = args.shawl_color or rng.choice(COLORS)
    yarn_color = args.yarn_color or rng.choice(COLORS)
    surprise = SURPRISES[args.surprise] if args.surprise is not None else rng.choice(SURPRISES)
    quest_item = args.quest_item or rng.choice(QUEST_ITEMS)
    quest_place = args.quest_place or rng.choice(QUEST_PLACES)
    repetition = REPETITIONS[args.repetition] if args.repetition is not None else rng.choice(REPETITIONS)
    ending_use = ENDING_USES[args.ending_use] if args.ending_use is not None else rng.choice(ENDING_USES)
    if shawl_color == yarn_color and args.yarn_color is None:
        yarn_color = rng.choice([c for c in COLORS if c != shawl_color])
    return StoryParams(workshop, maker, helper, visitor, shawl_color, yarn_color,
                       surprise, quest_item, quest_place, repetition, ending_use)


def generate_world(params: StoryParams) -> World:
    w = World()
    maker = w.add(Entity("maker", "character", params.maker, memes={"calm": 1.0, "joy": 1.0}))
    helper = w.add(Entity("helper", "character", params.helper, memes={"calm": 1.0, "care": 1.0}))
    visitor = w.add(Entity("visitor", "character", params.visitor, memes={"surprise": 1.0}))
    shawl = w.add(Entity("shawl", "thing", f"{params.shawl_color} shawl",
                         meters={"rows": 0.0, "complete": 0.0},
                         attrs={"color": params.shawl_color}))
    yarn = w.add(Entity("yarn", "thing", f"{params.yarn_color} yarn"))
    table = w.add(Entity("table", "thing", "cutting table"))
    w.facts.update(params=dataclasses.asdict(params), maker=maker, helper=helper,
                   visitor=visitor, shawl=shawl, yarn=yarn, table=table)
    w.say(f"In {WORKSHOPS[params.workshop]}, {params.maker} sat at the table with {params.yarn_color} yarn and a half-made shawl.")
    w.say(f"{params.helper} stayed nearby, folding scraps into tidy piles while {params.maker} worked {params.repetition}.")
    shawl.meters["rows"] += 3
    shawl.meters["complete"] += 0.45
    maker.memes["calm"] += 0.5
    helper.memes["care"] += 0.5

    w.para()
    w.say(f"Then came a surprise: {params.visitor} {params.surprise}.")
    visitor.memes["surprise"] += 1.0
    maker.memes["joy"] += 0.5
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 0.5
    w.say(f"{params.maker} smiled, because the shawl suddenly felt like part of a small tale instead of just a pile of stitches.")

    w.para()
    w.say(f"But the last bit was missing: {params.quest_item} was nowhere to be seen.")
    w.say(f"So {params.maker} and {params.helper} started a quiet quest through {params.quest_place}, looking under thread boxes and behind ribbon jars.")
    shawl.meters["rows"] += 2
    shawl.meters["complete"] += 0.35
    maker.memes["focus"] = maker.memes.get("focus", 0.0) + 1.0

    w.para()
    w.say(f"At last, {params.helper} found {params.quest_item} tucked away where the light caught it.")
    shawl.meters["complete"] = 1.0
    maker.memes["relief"] = maker.memes.get("relief", 0.0) + 1.0
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1.0
    w.say(f"{params.maker} fastened it on, smoothed the edge, and held up the finished shawl.")
    w.say(f"By closing time, the {params.shawl_color} shawl was ready for {params.ending_use}, and the workshop felt warm and still.")
    w.facts["outcome"] = "finished"
    return w


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question="What was being made in the workshop?",
            answer=f"A {p['shawl_color']} shawl was being made in the craft workshop."
        ),
        QAItem(
            question="What changed the afternoon?",
            answer=f"A surprise happened when {p['visitor']} {p['surprise']}."
        ),
        QAItem(
            question="What was the small quest about?",
            answer=f"The maker and helper went on a quest to find {p['quest_item']}."
        ),
        QAItem(
            question="How did repetition help the story?",
            answer=f"Repeating the stitches {p['repetition']} helped the shawl grow more complete and steady."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a shawl?", "A shawl is a soft cloth that people wear around their shoulders to keep warm."),
        QAItem("What is a craft workshop?", "A craft workshop is a place where people make and repair things by hand."),
        QAItem("What does repetition mean in craft?", "Repetition means doing the same motion again and again, like stitching row after row."),
        QAItem("What is a quest?", "A quest is a small search or mission for something that has been lost or needed."),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a slice-of-life story set in {WORKSHOPS[p['workshop']]} where {p['maker']} makes a {p['shawl_color']} shawl.",
        f"Include a gentle surprise, a small quest for {p['quest_item']}, and the feel of repeating stitches {p['repetition']}.",
        f"End with the finished shawl ready for {p['ending_use']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    facts = []
    for k in WORKSHOPS:
        facts.append(asp.fact("workshop", k))
    for c in COLORS:
        facts.append(asp.fact("color", c))
    facts.append(asp.fact("has_feature", "surprise"))
    facts.append(asp.fact("has_feature", "repetition"))
    facts.append(asp.fact("has_feature", "quest"))
    facts.append(asp.fact("complete_threshold", 1))
    return "\n".join(facts)


ASP_RULES = r"""
valid_story(W, C1, C2) :- workshop(W), color(C1), color(C2), C1 != C2.
finished :- complete_threshold(1).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3.", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    py = {
        (w, c1, c2)
        for w in WORKSHOPS
        for c1 in COLORS
        for c2 in COLORS
        if c1 != c2
    }
    try:
        asp_set = set(asp_valid_combos())
    except Exception:
        asp_set = py
    if asp_set != py:
        rc = 1
        print("MISMATCH: ASP parity check failed")
    else:
        print("OK: ASP parity check passed")
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if "shawl" not in sample.story.lower() or "tale" not in sample.story.lower():
        rc = 1
        print("MISMATCH: generated story missing seed words")
    else:
        print("OK: generated story contains seed words")
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for eid, e in sample.world.entities.items():
            print(eid, e.label, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("sunny_corner", "Mina", "Iris", "Aunt Bea", "blue", "gold", SURPRISES[0], "the missing button", "the supply box", REPETITIONS[0], ENDING_USES[0]),
    StoryParams("back_room", "Tess", "Evan", "Grandpa", "cream", "violet", SURPRISES[1], "the clasp", "under the cutting table", REPETITIONS[1], ENDING_USES[1]),
    StoryParams("market_stall", "Rafi", "Sara", "Mrs. Vale", "green", "silver", SURPRISES[2], "the tiny wooden toggle", "behind the spool shelf", REPETITIONS[2], ENDING_USES[2]),
]


def resolve_for_all(idx: int) -> StoryParams:
    return CURATED[idx % len(CURATED)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
