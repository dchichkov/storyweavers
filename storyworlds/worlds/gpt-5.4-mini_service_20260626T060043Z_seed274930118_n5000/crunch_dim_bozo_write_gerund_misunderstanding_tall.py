#!/usr/bin/env python3
"""
Story world: a tall-tale misunderstanding about a bozo who means well.

Premise:
- A bozo-story character has a habit of crunching things in a dim old room.
- The bozo is asked to write, but misunderstands the task and writes with a
  writing-thing that makes a mess rather than a story.
- A helper notices the confusion, explains the difference, and the bozo finishes
  the real writing in a brighter, calmer way.

Style:
- Tall-tale flavor: big feelings, vivid physical details, and a satisfying
  correction of the misunderstanding.
- The story is driven by state changes: dimness, crunching, confusion, tool use,
  and resolution.

Seed words:
- crunch-dim
- bozo
- write-gerund

Feature:
- Misunderstanding
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
        if self.type in {"bozo", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    dim: bool = False
    noisy: bool = False


@dataclass
class Tool:
    id: str
    label: str
    use: str
    wrong_use: str
    supports: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    tool: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "barn": Place("the barn", dim=True, noisy=True),
    "attic": Place("the attic", dim=True, noisy=False),
    "workroom": Place("the workroom", dim=False, noisy=True),
    "porch": Place("the porch", dim=False, noisy=False),
}

TOOLS = {
    "chalk": Tool(
        id="chalk",
        label="a stick of chalk",
        use="write with chalk",
        wrong_use="crunch on chalk",
        supports={"write"},
    ),
    "quill": Tool(
        id="quill",
        label="a long quill",
        use="write with a quill",
        wrong_use="crunch on the feather",
        supports={"write"},
    ),
    "paintbrush": Tool(
        id="paintbrush",
        label="a big paintbrush",
        use="paint signs with a brush",
        wrong_use="crunch on the bristles",
        supports={"paint"},
    ),
}

HEROES = [
    ("Bozo Ben", "bozo"),
    ("Bozo Bea", "bozo"),
    ("Bozo Bub", "bozo"),
]

HELPERS = [
    ("Mira", "girl"),
    ("Toby", "boy"),
    ("Pip", "boy"),
    ("Nell", "girl"),
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _add(world: World, eid: str, kind: str, typ: str, label: str) -> Entity:
    return world.add(Entity(id=eid, kind=kind, type=typ, label=label))


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero_name, hero_type = next(item for item in HEROES if item[0] == params.hero)
    helper_name, helper_type = next(item for item in HELPERS if item[0] == params.helper)
    tool = TOOLS[params.tool]

    hero = _add(world, "hero", "character", hero_type, hero_name)
    helper = _add(world, "helper", "character", helper_type, helper_name)
    utensil = _add(world, "tool", "thing", "tool", tool.label)

    world.facts.update(
        hero=hero,
        helper=helper,
        tool=tool,
        place=place,
        tool_entity=utensil,
    )

    # Setup
    if place.dim:
        world.say(
            f"In {place.name}, the light was so dim that even the dust motes looked sleepy."
        )
    else:
        world.say(
            f"In {place.name}, the air was bright enough to make every speck of dust look like a tiny star."
        )
    world.say(
        f"There lived {hero.label}, a cheerful bozo with a heart as big as a hay wagon."
    )
    world.say(
        f"{hero.label} loved to {tool.use}, and when nobody was looking, {hero.pronoun()} liked to {tool.wrong_use} just to hear a funny crunch."
    )

    # Misunderstanding
    world.para()
    world.say(
        f"One day, {helper.label} handed {hero.pronoun('object')} the {tool.label} and said, "
        f"\"Please write the name of the fair on the board.\""
    )
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1
    world.say(
        f"{hero.label} nodded so hard that his hat nearly flew away, but {hero.pronoun()} misunderstood the whole thing."
    )
    world.say(
        f"Instead of writing letters, {hero.pronoun()} tried to {tool.wrong_use} on the chalkboard, and the board went crunch-dim under the awkward little mess."
    )

    # Tension
    world.para()
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0.0) + 1
    world.say(
        f"{helper.label} blinked twice, then laughed a gentle laugh and said, "
        f"\"Oh, I meant write with it, not wrestle it.\""
    )
    world.say(
        f"{hero.label}'s cheeks warmed as red as apples in July, because the bozo had been trying to do the right thing in the wrong way."
    )
    world.say(
        f"The misunderstanding was as plain as a fencepost in a parade: {hero.label} needed help, not scolding."
    )

    # Resolution
    world.para()
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    world.say(
        f"{helper.label} showed {hero.pronoun('object')} how to hold the {tool.label} just so, and the dim room seemed to brighten by a whole lantern-load."
    )
    if "write" in tool.supports:
        world.say(
            f"Then {hero.label} wrote the fair's name in long, neat letters, and the words stood there proud and straight like fence posts after a storm."
        )
    else:
        world.say(
            f"Then {hero.label} found a better tool for the job and wrote the fair's name in careful letters."
        )
    world.say(
        f"By the end, the board was useful, {helper.label} was smiling, and {hero.label} was no longer crunching anything at all—just grinning like a lantern in the dark."
    )

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    tool = f["tool"]
    place = f["place"]
    return [
        f'Write a short tall-tale story about {hero.label}, a bozo in {place.name}, who must use {tool.label} to write but first misunderstands the request.',
        f"Tell a child-friendly story where {helper.label} helps {hero.label} fix a funny misunderstanding about writing.",
        f"Write a whimsical story with the words crunch, dim, and write, ending with a clear correction and a happy finish.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    tool: Tool = f["tool"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"Where did {hero.label} have the misunderstanding?",
            answer=f"{hero.label} had the misunderstanding in {place.name}.",
        ),
        QAItem(
            question=f"What did {helper.label} ask {hero.label} to do?",
            answer=f"{helper.label} asked {hero.label} to write the name of the fair on the board.",
        ),
        QAItem(
            question=f"What did {hero.label} do first by mistake?",
            answer=f"At first, {hero.label} tried to {tool.wrong_use} instead of writing with the tool.",
        ),
        QAItem(
            question=f"How was the misunderstanding fixed?",
            answer=f"{helper.label} explained the task kindly and showed {hero.label} how to use {tool.label} for writing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bozo in a story like this?",
            answer="A bozo is a silly, clownish character who can be funny, kind, and a little clumsy.",
        ),
        QAItem(
            question="What does it mean to misunderstand something?",
            answer="To misunderstand something means to hear or think about it the wrong way, even when someone was trying to be clear.",
        ),
        QAItem(
            question="Why is writing useful?",
            answer="Writing is useful because it can share names, signs, notes, and messages that people need to read.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when a bozo, a helper, a place, and a writing-support tool exist.
valid_story(H, P, T) :- hero(H), place(P), tool(T), supports(T, write).

% The misunderstanding beats are represented declaratively too.
misunderstanding(H) :- hero(H), crunch_dim(H), wants_to_write(H), wrong_use(H).

resolved(H) :- misunderstanding(H), helper_explains(H), learns_write(H).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.dim:
            lines.append(asp.fact("dim", place_id))
        if place.noisy:
            lines.append(asp.fact("noisy", place_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for s in sorted(tool.supports):
            lines.append(asp.fact("supports", tool_id, s))
    for hero_name, _ in HEROES:
        lines.append(asp.fact("hero", hero_name))
        lines.append(asp.fact("crunch_dim", hero_name))
        lines.append(asp.fact("wants_to_write", hero_name))
        lines.append(asp.fact("wrong_use", hero_name))
        lines.append(asp.fact("helper_explains", hero_name))
        lines.append(asp.fact("learns_write", hero_name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(h[0], p, t) for h, _ in HEROES for p in PLACES for t in TOOLS if "write" in TOOLS[t].supports}
    if clingo_set == python_set:
        print(f"OK: ASP matches Python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("clingo only:", sorted(clingo_set - python_set))
    print("python only:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.hero and args.hero not in [h for h, _ in HEROES]:
        raise StoryError("Unknown hero.")
    if args.helper and args.helper not in [h for h, _ in HELPERS]:
        raise StoryError("Unknown helper.")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("Unknown tool.")

    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    helper = args.helper or rng.choice([h for h, _ in HELPERS if h != hero])
    tool = args.tool or rng.choice(list(TOOLS))

    if not TOOLS[tool].supports:
        raise StoryError("The chosen tool cannot support a writing story.")
    return StoryParams(place=place, hero=hero, helper=helper, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e)
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: a bozo, a misunderstanding, and a writing fix.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--hero", choices=[h for h, _ in HEROES])
    ap.add_argument("--helper", choices=[h for h, _ in HELPERS])
    ap.add_argument("--tool", choices=list(TOOLS))
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


CURATED = [
    StoryParams(place="barn", hero="Bozo Ben", helper="Mira", tool="chalk"),
    StoryParams(place="attic", hero="Bozo Bea", helper="Nell", tool="quill"),
    StoryParams(place="workroom", hero="Bozo Bub", helper="Toby", tool="chalk"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
