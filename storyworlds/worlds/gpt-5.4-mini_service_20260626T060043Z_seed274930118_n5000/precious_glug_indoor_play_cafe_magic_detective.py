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

THEMES = ("precious", "glug")
LOCATIONS = ("indoor play cafe",)
TOOLS = ("magic magnifying glass", "magic notebook", "magic lantern")
CHARACTER_TYPES = ("girl", "boy")
ADULT_TYPES = ("mom", "dad", "aunt", "uncle")
PRIZES = (
    ("precious marble", "marble"),
    ("precious sticker star", "sticker star"),
    ("precious toy key", "toy key"),
)
CLUES = (
    ("glug under the table", "under the table"),
    ("glug near the cup station", "near the cup station"),
    ("glug by the snack shelf", "by the snack shelf"),
)

ASP_RULES = r"""
location(indoor_play_cafe).
theme(precious).
theme(glug).

case(C) :- clue(C).
mystery(C) :- clue(C), has_glug(C).
solved(C) :- mystery(C), magic_tool(T), uses(T,C), reveal(C).
safe(C) :- solved(C), returns_precious(C).

#show case/1.
#show mystery/1.
#show solved/1.
#show safe/1.
"""


@dataclass
class StoryParams:
    place: str = "indoor play cafe"
    child_name: str = "Mina"
    child_type: str = "girl"
    adult_type: str = "mom"
    prize: str = "precious marble"
    prize_label: str = "marble"
    clue: str = "glug under the table"
    clue_spot: str = "under the table"
    tool: str = "magic magnifying glass"
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self) -> None:
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


def _noise_word() -> str:
    return random.choice(("glug", "gloop", "plip"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: a precious clue, a glug, and a little magic in an indoor play cafe.")
    ap.add_argument("--place", choices=[p for p in LOCATIONS], default=None)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=list(ADULT_TYPES))
    ap.add_argument("--prize", choices=[p[0] for p in PRIZES])
    ap.add_argument("--tool", choices=list(TOOLS))
    ap.add_argument("--clue", choices=[c[0] for c in CLUES])
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
    prize, prize_label = rng.choice(PRIZES)
    clue, clue_spot = rng.choice(CLUES)
    child_type = args.gender or rng.choice(CHARACTER_TYPES)
    child_name = args.name or rng.choice(["Mina", "Theo", "Nina", "Ari", "Ivy", "Leo"])
    adult_type = args.adult or rng.choice(ADULT_TYPES)
    tool = args.tool or rng.choice(TOOLS)
    if args.prize:
        for p, label in PRIZES:
            if p == args.prize:
                prize, prize_label = p, label
                break
    if args.clue:
        for c, spot in CLUES:
            if c == args.clue:
                clue, clue_spot = c, spot
                break
    if args.place and args.place != "indoor play cafe":
        raise StoryError("This storyworld only supports an indoor play cafe.")
    if args.tool and "magic" not in args.tool:
        raise StoryError("The detective solution needs a magic tool.")
    return StoryParams(
        place="indoor play cafe",
        child_name=child_name,
        child_type=child_type,
        adult_type=adult_type,
        prize=prize,
        prize_label=prize_label,
        clue=clue,
        clue_spot=clue_spot,
        tool=tool,
    )


def tell(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    adult = w.add(Entity(id="adult", kind="character", type=params.adult_type, label=f"the {params.adult_type}"))
    prize = w.add(Entity(id="prize", type="thing", label=params.prize_label, phrase=params.prize, owner=child.id, caretaker=adult.id, location="pocket"))
    clue = w.add(Entity(id="clue", type="thing", label="glug", phrase=params.clue, location=params.clue_spot))
    tool = w.add(Entity(id="tool", type="thing", label=params.tool, phrase=params.tool, owner=child.id))

    child.memes["curiosity"] = 1
    child.memes["mystery"] = 1
    prize.meters["precious"] = 1
    clue.meters["glug"] = 1

    w.say(f"{child.id} was a little {child.type} who loved puzzles, clues, and quiet footsteps.")
    w.say(f"At the {params.place}, {child.id} carried a {params.prize} that felt very precious.")
    w.say(f"{child.id} also kept a {params.tool}, because a detective liked to notice everything.")

    w.para()
    w.say(f"One afternoon in the {params.place}, a strange { _noise_word() } sounded from {params.clue_spot}.")
    w.say(f"{child.id} frowned. That glug did not belong in a cozy play cafe.")
    w.say(f'"Did you hear that?" {child.id} asked {params.adult_type}.')

    w.para()
    w.say(f"{params.adult_type.capitalize()} nodded and pointed at the spot. " 
          f'"Let\'s solve it carefully," {params.adult_type} said.')
    w.say(f"{child.id} shone the {params.tool} toward {params.clue_spot}. The magic beam caught a shiny trail.")
    w.say(f"Behind a tipped cup, {child.id} found the {params.prize} stuck in a little puddle of juice.")
    w.say(f"The glug was only the cup dribbling after someone bumped it.")

    w.para()
    child.memes["relief"] = 1
    child.memes["pride"] = 1
    prize.location = child.id
    w.say(f"{child.id} wiped the {params.prize_label} clean and put it back in a safe pocket.")
    w.say(f'The mystery was solved, the glug stopped, and {child.id} smiled like a real detective.')
    w.say(f"At the end, the indoor play cafe was calm again, and the precious prize was safe.")

    w.facts.update(
        child=child,
        adult=adult,
        prize=prize,
        clue=clue,
        tool=tool,
        params=params,
        solved=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short detective story for a child in an "{p.place}" that includes the word "{THEMES[0]}".',
        f"Tell a gentle mystery where {p.child_name} hears a {THEMES[1]} and uses a {p.tool} to solve it.",
        f"Write a cozy indoor play cafe story about a precious lost thing, a clue, and a magical solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    adult = world.facts["adult"]
    prize = world.facts["prize"]
    clue = world.facts["clue"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {child.id}, a little {child.type} detective in the {p.place}.",
        ),
        QAItem(
            question=f"What made the mystery start?",
            answer=f"A strange glug sounded from {clue.location}, which made {child.id} look for the cause.",
        ),
        QAItem(
            question=f"What precious thing needed to be found?",
            answer=f"The precious thing was {p.prize}, and it ended up safe again after the mystery was solved.",
        ),
        QAItem(
            question=f"How did {child.id} solve the problem?",
            answer=f"{child.id} used a {p.tool} with magic to look carefully, found the hidden {p.prize_label}, and learned the glug was only a dripping cup.",
        ),
        QAItem(
            question=f"Who helped {child.id} during the case?",
            answer=f"{adult.id} helped by staying calm, pointing to the clue, and encouraging careful detective work.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an indoor play cafe?",
            answer="An indoor play cafe is a place inside where children can play, explore, and have snacks away from the weather.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="Why can magic be useful in a story?",
            answer="Magic can help a character notice hidden things or solve problems in a special storybook way.",
        ),
        QAItem(
            question="What does precious mean?",
            answer="Precious means very special and worth taking good care of.",
        ),
        QAItem(
            question="What might a glug sound like?",
            answer="A glug sounds like a wet, bubbly dripping noise, such as a cup or bottle making little spills.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "indoor_play_cafe"),
        asp.fact("theme", "precious"),
        asp.fact("theme", "glug"),
    ]
    for _, spot in CLUES:
        lines.append(asp.fact("clue", spot.replace(" ", "_")))
    for tool in TOOLS:
        lines.append(asp.fact("magic_tool", tool.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe/1.\n#show solved/1.\n#show mystery/1.\n"))
    shown = asp.atoms(model, "safe")
    if shown:
        print("OK: ASP program is runnable.")
        return 0
    print("MISMATCH: ASP program produced no safe case.")
    return 1


def asp_cases() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show safe/1.\n#show solved/1.\n#show mystery/1.\n"))
    return sorted(set(asp.atoms(model, "safe")))


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
    StoryParams(child_name="Mina", child_type="girl", adult_type="mom", prize="precious marble", prize_label="marble", clue="glug under the table", clue_spot="under the table", tool="magic magnifying glass"),
    StoryParams(child_name="Theo", child_type="boy", adult_type="dad", prize="precious sticker star", prize_label="sticker star", clue="glug near the cup station", clue_spot="near the cup station", tool="magic notebook"),
    StoryParams(child_name="Ivy", child_type="girl", adult_type="aunt", prize="precious toy key", prize_label="toy key", clue="glug by the snack shelf", clue_spot="by the snack shelf", tool="magic lantern"),
]


def resolve_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = resolve_params(args, rng)
    if args.name:
        params.child_name = args.name
    if args.gender:
        params.child_type = args.gender
    return params


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe/1.\n#show solved/1.\n#show mystery/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP case support is available for this world.")
        for row in asp_cases():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_from_args(args, random.Random(seed))
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
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: precious/glug at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
