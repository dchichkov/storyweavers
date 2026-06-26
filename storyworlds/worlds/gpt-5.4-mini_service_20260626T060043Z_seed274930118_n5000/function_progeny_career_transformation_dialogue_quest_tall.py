#!/usr/bin/env python3
"""
Tall-tale storyworld: a strange career quest built around function, progeny, and transformation.

A child-facing, state-driven story domain where a young hero inherits a peculiar function,
meets a famous progeny, and must choose a new career by completing a quest. A transformation
and a dialogue scene turn the tale toward a satisfying ending.
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
class Character:
    id: str
    kind: str = "character"
    title: str = ""
    role: str = ""
    kindred: str = ""
    career: str = ""
    home: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class World:
    place: str
    sky: str
    road: str
    characters: dict[str, Character] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)

    def add(self, c: Character) -> Character:
        self.characters[c.id] = c
        return c

    def say(self, lines: list[str], text: str) -> None:
        lines.append(text)


@dataclass
class StoryParams:
    place: str
    function: str
    progeny: str
    career: str
    name: str
    mentor: str
    mood: str
    seed: Optional[int] = None


PLACES = {
    "hilltown": {"place": "the hilltown", "sky": "golden", "road": "a winding road up the hill"},
    "riverbend": {"place": "the riverbend", "sky": "blue", "road": "a dusty road beside the water"},
    "dusty_crossing": {"place": "the dusty crossing", "sky": "amber", "road": "the long road between barns"},
}

FUNCTIONS = {
    "function": {
        "name": "the family function",
        "job": "ringing the old brass bell",
        "risk": "losing its bright chime",
        "burst": "rang so hard the windows sang",
    },
    "function_of_weather": {
        "name": "the weather function",
        "job": "calling the clouds to gather",
        "risk": "spilling rain on the parade",
        "burst": "called thunder like a drum",
    },
    "function_of_maps": {
        "name": "the map function",
        "job": "showing every hidden road",
        "risk": "tearing the paper on a sharp turn",
        "burst": "unfolded like a kite in the wind",
    },
}

PROGENY = {
    "progeny": {
        "name": "the famous progeny",
        "title": "the mayor's child",
        "gift": "a knack for finding lost things",
        "voice": "bright as a tin whistle",
    },
    "progeny_of_circus": {
        "name": "the circus progeny",
        "title": "the ringmaster's child",
        "gift": "walking a rope without wobbling",
        "voice": "loud as a trumpet",
    },
    "progeny_of_baker": {
        "name": "the baker's progeny",
        "title": "the baker's child",
        "gift": "smelling a pie from a mile away",
        "voice": "sweet as cinnamon",
    },
}

CAREERS = {
    "lamplighter": {
        "name": "lamplighter",
        "tool": "a long brass pole",
        "task": "lighting each streetlamp before dark",
        "uniform": "a soot-black coat",
    },
    "riverguide": {
        "name": "river guide",
        "tool": "a painted oar",
        "task": "steering visitors through the bends",
        "uniform": "a bright red sash",
    },
    "clockmender": {
        "name": "clockmender",
        "tool": "a tiny silver wrench",
        "task": "listening for the tick that had gone crooked",
        "uniform": "a vest full of pockets",
    },
}

MOODS = {
    "proud": "proud",
    "nervous": "nervous",
    "curious": "curious",
    "stubborn": "stubborn",
}

TRAIT_NAMES = [
    "Pip", "Milo", "June", "Nell", "Bram", "Tess", "Otis", "Wren", "Faye", "Jory"
]


def build_world(params: StoryParams) -> World:
    setting = PLACES[params.place]
    w = World(place=setting["place"], sky=setting["sky"], road=setting["road"])
    hero = w.add(Character(id=params.name, title="small hero", role="apprentice"))
    hero.kindred = params.progeny
    hero.career = params.career
    mentor = w.add(Character(id=params.mentor, title="old mentor", role="guide"))
    mentor.kindred = "mentor"
    mentor.career = "storykeeper"
    w.facts.update(params=params, hero=hero, mentor=mentor)
    return w


def tell_story(world: World) -> str:
    f = world.facts
    p: StoryParams = f["params"]
    hero: Character = f["hero"]
    mentor: Character = f["mentor"]
    fn = FUNCTIONS[p.function]
    pg = PROGENY[p.progeny]
    cr = CAREERS[p.career]

    lines: list[str] = []
    world.say(lines, f"At {world.place}, under a {world.sky} sky, {hero.id} was a little apprentice with a big dream.")
    world.say(lines, f"Everyone knew {hero.id} carried {fn['name']} in the family, and it had the job of {fn['job']}.")
    world.say(lines, f"But one bright morning, the old function began to wobble and nearly forgot its own tune, so {hero.id} felt a great worry in {hero.possessive()} chest.")
    world.say(lines, f"Then came {pg['name']}, {pg['title']}, whose gift was {pg['gift']} and whose voice was {pg['voice']}.")
    world.say(lines, f'"If your function is shaking," said {pg["name"]}, "maybe it wants a different career."')
    world.say(lines, f"{hero.id} stared down the {world.road} and decided on a quest: learn {cr['name']} work before sunset.")
    world.say(lines, f"{mentor.id}, the old guide, handed over {cr['tool']} and said, 'A career is not just a job. It is a way to help the whole town.'")
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    hero.meters["resolve"] = hero.meters.get("resolve", 0) + 1
    world.say(lines, f"So {hero.id} marched off, {cr['tool']} in hand, to do {cr['task']}.")
    hero.meters["quest_progress"] = 1
    world.say(lines, f"The first test came fast: the old function {fn['burst']}, and the air filled with noise.")
    world.say(lines, f"Instead of panicking, {hero.id} listened, counted three heartbeats, and turned the burst into a steady rhythm.")
    hero.meters["quest_progress"] = 2
    hero.meters["transformation"] = 1
    hero.career = cr["name"]
    hero.role = "new worker"
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 2
    world.say(lines, f"That was the transformation. The wobble became a strength, and the old trouble became a new skill.")
    world.say(lines, f"At last, {hero.id} came home wearing {cr['uniform']}, still carrying the family function, but now with a brand-new career.")
    world.say(lines, f"{pg['name']} clapped, {mentor.id} smiled, and the town cheered because the quest had made one small life feel as wide as a county road.")
    world.say(lines, f"By nightfall, the function was steady, the progeny was laughing, and {hero.id} had become the best {cr['name']} anyone had ever seen.")
    return "\n\n".join(lines)


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a tall tale for children about a {p.mood} child who inherits a function and meets a famous progeny.",
        f"Tell a quest story where {p.name} must choose a new career after a strange transformation.",
        f"Make a playful legend about {p.name}, {p.mentor}, and a career that helps the town.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero: Character = world.facts["hero"]
    mentor: Character = world.facts["mentor"]
    fn = FUNCTIONS[p.function]
    pg = PROGENY[p.progeny]
    cr = CAREERS[p.career]
    return [
        QAItem(
            question=f"What was {hero.id} trying to learn on the quest?",
            answer=f"{hero.id} was trying to learn how to do the work of a {cr['name']} and help the town."
        ),
        QAItem(
            question=f"Who told {hero.id} that the shaken function might want a different career?",
            answer=f"{pg['name']} said that, and the advice helped {hero.id} start the quest."
        ),
        QAItem(
            question=f"What changed when the transformation happened?",
            answer=f"The old wobble became a steady skill, and {hero.id} changed from an unsure apprentice into a confident {cr['name']}."
        ),
        QAItem(
            question=f"What was the family function doing at the end?",
            answer=f"It was steady again, doing {fn['job']} without wobbling."
        ),
        QAItem(
            question=f"Who gave {hero.id} the tool for the new job?",
            answer=f"{mentor.id} gave {hero.id} {cr['tool']} and the chance to begin the new career."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a long search or journey to reach a goal, like finding something important or learning a new skill."
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change that turns one state into another, like shy becoming brave or broken becoming useful."
        ),
        QAItem(
            question="What is a career?",
            answer="A career is the kind of work a person does to help others and make a living over time."
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is talking between characters in a story."
        ),
    ]


ASP_RULES = r"""
quest_ready(H) :- hero(H), has_function(H), meets_progeny(H), hears_advice(H).
transformed(H) :- quest_ready(H), career_chosen(H).
successful(H) :- transformed(H), steady_function(H).
#show quest_ready/1.
#show transformed/1.
#show successful/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("has_function", "hero"))
    lines.append(asp.fact("meets_progeny", "hero"))
    lines.append(asp.fact("hears_advice", "hero"))
    lines.append(asp.fact("career_chosen", "hero"))
    lines.append(asp.fact("steady_function", "hero"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set((a.name, tuple(x.name if x.type != x.type.Number else x.number for x in a.arguments)) for a in model)
    expected = {
        ("quest_ready", ("hero",)),
        ("transformed", ("hero",)),
        ("successful", ("hero",)),
    }
    if atoms == expected:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH in ASP parity.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.function not in FUNCTIONS:
        raise StoryError("Unknown function.")
    if params.progeny not in PROGENY:
        raise StoryError("Unknown progeny.")
    if params.career not in CAREERS:
        raise StoryError("Unknown career.")
    if params.name.strip() == "":
        raise StoryError("Hero name must not be empty.")
    if params.mentor.strip() == "":
        raise StoryError("Mentor name must not be empty.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    function = args.function or rng.choice(sorted(FUNCTIONS))
    progeny = args.progeny or rng.choice(sorted(PROGENY))
    career = args.career or rng.choice(sorted(CAREERS))
    name = args.name or rng.choice(TRAIT_NAMES)
    mentor = args.mentor or rng.choice(["Aunt Dot", "Uncle Bram", "Old Nettle", "Captain Reed"])
    mood = args.mood or rng.choice(sorted(MOODS))
    params = StoryParams(
        place=place,
        function=function,
        progeny=progeny,
        career=career,
        name=name,
        mentor=mentor,
        mood=mood,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = tell_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for c in world.characters.values():
        lines.append(f"{c.id}: title={c.title} role={c.role} career={c.career} meters={c.meters} memes={c.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about function, progeny, and career.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--function", choices=sorted(FUNCTIONS))
    ap.add_argument("--progeny", choices=sorted(PROGENY))
    ap.add_argument("--career", choices=sorted(CAREERS))
    ap.add_argument("--name")
    ap.add_argument("--mentor")
    ap.add_argument("--mood", choices=sorted(MOODS))
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
    StoryParams(place="hilltown", function="function", progeny="progeny", career="lamplighter", name="Pip", mentor="Aunt Dot", mood="curious"),
    StoryParams(place="riverbend", function="function_of_weather", progeny="progeny_of_baker", career="riverguide", name="June", mentor="Uncle Bram", mood="proud"),
    StoryParams(place="dusty_crossing", function="function_of_maps", progeny="progeny_of_circus", career="clockmender", name="Bram", mentor="Old Nettle", mood="nervous"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", sorted(str(a) for a in model))
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(rng_base + i))
            params.seed = rng_base + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.function} / {p.progeny} / {p.career}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
