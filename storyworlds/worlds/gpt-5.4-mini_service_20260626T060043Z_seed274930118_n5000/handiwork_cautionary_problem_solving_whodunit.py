#!/usr/bin/env python3
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

TOOLS = ["hammer", "paintbrush", "glue", "scissors", "tape", "needle"]
MATERIALS = ["wood", "cloth", "paper", "cardboard"]
PLACES = {
    "shed": {"tools", "wood", "tape", "hammer"},
    "workroom": {"tools", "paintbrush", "glue", "scissors"},
    "kitchen table": {"paper", "tape", "glue"},
    "porch": {"cloth", "needle", "scissors"},
}
HERO_NAMES = ["Nina", "Owen", "Maya", "Eli", "June", "Toby", "Iris", "Finn"]
HELPER_NAMES = ["Grandma", "Grandpa", "Aunt Bea", "Uncle Sol", "Mom", "Dad"]
SUSPECT_NAMES = ["Milo", "Bea", "Remy", "Pia", "Noah", "Tess"]
TRAITS = ["careful", "curious", "patient", "brave", "steady", "clever"]


@dataclass
class StoryParams:
    place: str
    craft: str
    missing_item: str
    hero: str
    helper: str
    suspect: str
    trait: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    found: bool = False
    damaged: bool = False


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.clues: list[str] = []

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small handiwork whodunit with caution and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--craft", choices=["birdhouse", "kite", "puppet", "lantern"])
    ap.add_argument("--missing-item", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
    ap.add_argument("--trait", choices=TRAITS)
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


def _validate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("That place does not exist in this little workshop world.")
    if params.missing_item not in PLACES[params.place]:
        raise StoryError(f"No honest mystery can happen there: the {params.missing_item} is not in the {params.place}.")
    if params.hero == params.suspect:
        raise StoryError("The hero and the suspect must be different people.")
    if params.helper == params.hero:
        raise StoryError("The helper cannot be the hero in this whodunit.")
    if params.craft == "lantern" and params.missing_item == "needle":
        raise StoryError("That craft does not need a needle in this world.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    craft = args.craft or rng.choice(["birdhouse", "kite", "puppet", "lantern"])
    missing_item = args.missing_item or rng.choice(sorted(PLACES[place]))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    suspect = args.suspect or rng.choice([n for n in SUSPECT_NAMES if n != hero and n != helper])
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(place, craft, missing_item, hero, helper, suspect, trait)
    _validate(params)
    return params


def asp_facts() -> str:
    import asp
    lines = []
    for place, items in PLACES.items():
        lines.append(asp.fact("place", place))
        for item in sorted(items):
            lines.append(asp.fact("has", place, item))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for c in ["birdhouse", "kite", "puppet", "lantern"]:
        lines.append(asp.fact("craft", c))
    return "\n".join(lines)


ASP_RULES = r"""
needs(birdhouse,hammer).
needs(birdhouse,wood).
needs(kite,scissors).
needs(kite,tape).
needs(puppet,needle).
needs(puppet,cloth).
needs(lantern,glue).
needs(lantern,paper).

mystery(P,C) :- place(P), craft(C), needs(C,I), not has(P,I).
solve(P,C) :- mystery(P,C).
#show mystery/2.
#show solve/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show mystery/2.")
    model = asp.one_model(program)
    if model is None:
        print("MISMATCH: no ASP model.")
        return 1
    print("OK: ASP program loads and solves.")
    return 0


def _craft_needs(craft: str) -> list[str]:
    return {
        "birdhouse": ["hammer", "wood"],
        "kite": ["scissors", "tape"],
        "puppet": ["needle", "cloth"],
        "lantern": ["glue", "paper"],
    }[craft]


def generate_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.hero, kind="character", type="child", label=params.hero, memes={"curiosity": 1}))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", label=params.helper, memes={"calm": 1}))
    suspect = world.add(Entity(id=params.suspect, kind="character", type="child", label=params.suspect, memes={"nervous": 1}))
    missing = world.add(Entity(id=params.missing_item, type="tool", label=params.missing_item, owner=hero.id, found=False))
    world.facts.update(hero=hero, helper=helper, suspect=suspect, missing=missing, params=params)

    world.say(
        f"{hero.id} was a {params.trait} child who loved handiwork, especially making a {params.craft}. "
        f"At {params.place}, the table was set with thread, scraps, and a tidy row of tools."
    )
    world.say(
        f"But when it was time to begin, the {params.missing_item} was gone."
    )
    world.para()

    world.say(
        f"{hero.id} frowned and looked around the {params.place}. "
        f"The room felt like a little mystery, and {helper.id} said, "
        f"\"Let's not guess too fast. First we look for clues.\""
    )
    world.clues.append(f"{params.missing_item} was not on the table")
    world.clues.append(f"small marks near {params.suspect}")
    world.clues.append(f"a careful trail toward the {params.place}")
    if params.missing_item in ("scissors", "needle"):
        world.clues.append("the missing thing could hurt someone if left out")
    else:
        world.clues.append("the missing thing could slow the work if not found")
    world.say(
        f"{params.suspect} had been nearby, so {hero.id} watched closely and saw a tiny clue: "
        f"a trail leading past {params.suspect}'s chair."
    )
    world.say(
        f"{helper.id} did not scold. Instead, {helper.id} showed how to search with open hands, "
        f"checking baskets, shelves, and under the table."
    )
    world.para()

    if params.missing_item == "needle":
        world.say(
            f"Under the table, {hero.id} found the needle tucked safely in a pin cushion. "
            f"It had been moved there so no one would get poked."
        )
        missing.found = True
    elif params.missing_item == "scissors":
        world.say(
            f"Behind a folded cloth, {hero.id} found the scissors. "
            f"They had been put down carefully after cutting, so no one would snip a sleeve by mistake."
        )
        missing.found = True
    elif params.missing_item == "hammer":
        world.say(
            f"In the shed corner, {hero.id} found the hammer beside the wood. "
            f"It had rolled away when someone reached for a nail."
        )
        missing.found = True
    elif params.missing_item == "glue":
        world.say(
            f"Near the water cup, {hero.id} found the glue. "
            f"It had been moved away from the edge so it would not tip over and make a sticky mess."
        )
        missing.found = True
    else:
        world.say(
            f"Under a bright scrap of paper, {hero.id} found the {params.missing_item}. "
            f"It had simply been left in the wrong place."
        )
        missing.found = True

    world.say(
        f"{params.suspect} looked worried, but the clue was kind, not mean. "
        f"It showed that the missing tool had only been misplaced."
    )
    world.para()

    needs = _craft_needs(params.craft)
    caution = "careful" if params.missing_item in ("needle", "scissors", "hammer") else "steady"
    world.say(
        f"{helper.id} gave a small cautionary lesson: \"Handiwork is easier when tools are used and returned with care.\" "
        f"Then {hero.id} sorted the pieces, {params.suspect} handed over the scraps, and the work began again."
    )
    world.say(
        f"With the {params.missing_item} back in place, {hero.id} made the last part of the {params.craft} step by step: "
        f"{' and '.join(needs)}."
    )
    if params.craft == "birdhouse":
        ending = "Soon the little birdhouse stood straight and neat, with a round doorway and a safe roof."
    elif params.craft == "kite":
        ending = "Soon the kite had a strong frame and a bright tail, ready to catch the wind."
    elif params.craft == "puppet":
        ending = "Soon the puppet had stitched hands and a smiling face that could wave at everyone."
    else:
        ending = "Soon the lantern glowed softly, its paper sides shining like a tiny moon."
    world.say(
        f"{ending} {hero.id} smiled, because the mystery was solved and the handiwork was finished without a fuss."
    )
    world.facts["resolved"] = True
    world.facts["caution"] = caution


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short whodunit about a missing {p.missing_item} in a little handiwork scene.",
        f"Tell a child-friendly mystery where {p.hero} solves the problem of the missing {p.missing_item} while making a {p.craft}.",
        f"Write a cautionary story in a workshop where careful searching fixes a small mistake and the craft can continue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question=f"What was missing at {p.place}?",
            answer=f"The missing thing was the {p.missing_item}, which made the handiwork stop for a moment.",
        ),
        QAItem(
            question=f"How did {p.hero} solve the problem?",
            answer=f"{p.hero} solved it by searching calmly with {p.helper}, following clues, and finding the {p.missing_item} in the right place.",
        ),
        QAItem(
            question=f"Why was this story cautionary?",
            answer=f"It showed that tools should be used carefully and put back where they belong, so no one gets hurt and the work can keep going.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question="What is handiwork?",
            answer="Handiwork is work you make with your hands, like building, sewing, cutting, or gluing things together.",
        ),
        QAItem(
            question="Why should tools be put back after use?",
            answer="Tools should be put back so they do not get lost, break, or hurt someone who reaches for them later.",
        ),
        QAItem(
            question=f"What does a {p.missing_item} help with?",
            answer=f"A {p.missing_item} helps with the kind of job that needs it, and using the right tool makes the work safer and easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== Prompts ==")
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.kind == "character":
            bits.append(f"memes={e.memes}")
        if e.type == "tool":
            bits.append(f"found={e.found}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    lines.append(f"clues={world.clues}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params.place)
    generate_story(world, params)
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


def asp_verify_wrapper() -> int:
    try:
        return asp_verify()
    except Exception as e:
        print(f"ASP verify failed: {e}")
        return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solve/2."))
        return
    if args.verify:
        sys.exit(asp_verify_wrapper())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery/2.\n#show solve/2."))
        print("ASP solved:", [str(a) for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("shed", "birdhouse", "hammer", "Nina", "Grandma", "Milo", "careful"),
            StoryParams("workroom", "kite", "scissors", "Owen", "Mom", "Bea", "curious"),
            StoryParams("porch", "puppet", "needle", "Maya", "Aunt Bea", "Remy", "patient"),
            StoryParams("kitchen table", "lantern", "glue", "Iris", "Dad", "Pia", "steady"),
        ]
        for p in curated:
            _validate(p)
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                p = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
