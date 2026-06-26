#!/usr/bin/env python3
"""
A standalone story world for a tiny rhyming tale about duty, a mason,
sharing, and a little bit of magic.

The world is built as a small causal simulation:
- a mason has a duty to finish a wall before dusk
- a magic stone or charm can help, but only if it is shared kindly
- the story turns when the mason chooses teamwork over keeping the magic
- the ending proves the change in the world state: the duty is done, and the
  shared magic leaves everyone calmer and happier
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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "mason"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    has_sand: bool = False
    has_stones: bool = True
    has_dusk: bool = True


@dataclass
class Tool:
    id: str
    label: str
    helps: str
    shared: bool = True
    sparkle: str = "sparkly"


@dataclass
class StoryParams:
    place: str
    tool: str
    name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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


def rhymes(word: str) -> str:
    return {
        "duty": "beauty",
        "stone": "glow alone",
        "share": "care",
        "magic": "classic",
        "wall": "all",
        "bright": "light",
    }.get(word, word)


def meter_story(world: World, mason: Entity, helper: Entity, tool: Tool) -> None:
    mason.memes["duty"] = 1.0
    world.say(
        f"Mason was a mason with a duty to build the little wall by dusk. "
        f"He tapped each stone in a tidy tune, because work can hum like a song."
    )
    world.say(
        f"At his side, {helper.id} brought {tool.label}, a {tool.sparkle} bit of magic that made the mortar sing."
    )
    world.facts["duty"] = "build the wall"
    world.facts["tool"] = tool.id


def maybe_share(world: World, mason: Entity, helper: Entity, tool: Tool) -> None:
    mason.memes["want_keep"] = 1.0
    world.para()
    world.say(
        f"Mason first held the magic close. He liked the bright glow, and he liked the show. "
        f"But the wall was wide, and the work was real; one pair of hands could not finish the deal."
    )
    world.say(
        f"{helper.id} asked, “Can we share?” and Mason paused in the air. "
        f"Then he nodded once, with a kind little grin, and passed the magic in."
    )
    mason.memes["share"] = 1.0
    helper.memes["share"] = 1.0
    world.facts["shared"] = True


def finish_wall(world: World, mason: Entity, helper: Entity, tool: Tool) -> None:
    world.para()
    mason.meters["wall"] = 1.0
    helper.meters["wall"] = 1.0
    mason.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    world.say(
        f"Together they set stone on stone, and the magic made the mortar flow. "
        f"The wall rose tall, neat, and bright, a sturdy little line of light."
    )
    world.say(
        f"By dusk the duty was done. Mason smiled at the sum: when friends share a helping charm, "
        f"small hands can do a big day's work with warm, calm arms."
    )
    world.facts["done"] = True
    world.facts["ending_image"] = "a tidy wall glowing in the dusk"


def build_world(place: Place, tool: Tool, name: str, helper_name: str) -> World:
    world = World(place)
    mason = world.add(Entity(id=name, kind="character", type="mason", label="mason"))
    helper = world.add(Entity(id=helper_name, kind="character", type="child", label="helper"))
    world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.label, owner=name))
    meter_story(world, mason, helper, tool)
    maybe_share(world, mason, helper, tool)
    finish_wall(world, mason, helper, tool)
    world.facts.update(mason=mason, helper=helper, place=place, tool_def=tool)
    return world


PLACES = {
    "yard": Place(name="the sunny yard"),
    "square": Place(name="the little square"),
    "garden": Place(name="the garden lane"),
}

TOOLS = {
    "glimmer": Tool(id="glimmer", label="a glimmering charm", helps="helps mortar glow", sparkle="magic"),
    "chalk": Tool(id="chalk", label="a magic chalk stick", helps="helps lines stay straight", sparkle="magic"),
    "bell": Tool(id="bell", label="a tiny silver bell", helps="keeps rhythm", sparkle="magic"),
}


NAMES = ["Mason", "Milo", "Eli", "Noah", "Theo"]
HELPERS = ["Luna", "Mia", "June", "Ava", "Nina"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in PLACES for t in TOOLS]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("magic", tid))
        lines.append(asp.fact("shared", tid))
    for pid in PLACES:
        for tid in TOOLS:
            lines.append(asp.fact("valid", pid, tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T) :- place(P), tool(T), magic(T), shared(T).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming story world about duty, a mason, sharing, and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    combos = valid_combos()
    place = args.place or rng.choice(sorted(PLACES))
    tool = args.tool or rng.choice(sorted(TOOLS))
    if (place, tool) not in combos:
        raise StoryError("No valid story matches those choices.")
    return StoryParams(
        place=place,
        tool=tool,
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(PLACES[params.place], TOOLS[params.tool], params.name, params.helper_name)
    story = world.render()
    prompts = [
        "Write a short rhyming story about a mason who has a duty to build a wall and learns to share a magic helper.",
        f"Tell a child-friendly story in {params.place} about {params.name}, a mason, who shares magic to finish an important duty.",
        "Write a gentle rhyme where a small job becomes easier when someone chooses sharing over keeping the magic to themself.",
    ]
    story_qa = [
        QAItem(
            question=f"What duty did {params.name} have in the story?",
            answer=f"{params.name} had the duty to build the little wall before dusk.",
        ),
        QAItem(
            question=f"Why did {params.name} start to worry before the wall was finished?",
            answer="The wall was wide, and one pair of hands was not enough to finish it alone.",
        ),
        QAItem(
            question=f"What changed when {params.name} shared the magic?",
            answer=f"When {params.name} shared the magic, the work became easier, and the wall was finished on time.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving someone else a turn, a piece, or some help instead of keeping everything for yourself.",
        ),
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is a special, pretend power that can make unusual things happen.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


CURATED = [
    StoryParams(place="yard", tool="glimmer", name="Mason", helper_name="Luna"),
    StoryParams(place="square", tool="chalk", name="Milo", helper_name="Mia"),
    StoryParams(place="garden", tool="bell", name="Eli", helper_name="June"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
