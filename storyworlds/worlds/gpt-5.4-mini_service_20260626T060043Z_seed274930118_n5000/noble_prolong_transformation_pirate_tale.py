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

ASP_RULES = r"""
% A pirate tale is valid when there is a noble wish, a transformation, and a
resolution that changes the captain's state in a believable way.
hero(H) :- pirate(H).
crew(C) :- sailor(C).
place(P) :- harbor(P).
place(P) :- isle(P).

valid_story(H, P, T, M) :- pirate(H), place(P), transformation(T), motive(M),
                           fitting_transformation(H, T, M).
"""


@dataclass
class StoryParams:
    harbor: str
    hero_name: str
    hero_title: str
    crew_name: str
    transformation: str
    motive: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    title: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    forms: list[str] = field(default_factory=list)
    transformed_from: Optional[str] = None
    transformed_into: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self, harbor: str) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


HARBORS = {
    "brineport": "Brineport",
    "moonwharf": "Moon Wharf",
    "saltcove": "Salt Cove",
    "crownharbor": "Crown Harbor",
}

TRANSFORMATIONS = {
    "stormglass": {
        "name": "storm-glass change",
        "from": "a weather-beaten pirate captain",
        "to": "a shining sea-captain of glass and silver",
        "turn": "when the lighthouse struck the captain with a bright blue beam",
    },
    "golden_shell": {
        "name": "golden-shell change",
        "from": "a dusty pirate child",
        "to": "a small guardian with a shell-bright coat",
        "turn": "when the shell in the captain's pocket began to glow",
    },
    "tide_rose": {
        "name": "tide-rose change",
        "from": "a rough old pirate",
        "to": "a noble sailor with a rose-red sash",
        "turn": "when a tide rose high and wrapped the captain in warm foam",
    },
}

MOTIVES = {
    "save_map": "save the lost map before the tide swallowed it",
    "free_crew": "free the crew from a jammed chain below deck",
    "return_crown": "return a stolen crown to its rightful island hall",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a noble transformation.")
    ap.add_argument("--harbor", choices=sorted(HARBORS))
    ap.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    ap.add_argument("--motive", choices=sorted(MOTIVES))
    ap.add_argument("--name")
    ap.add_argument("--crew-name")
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


def asp_facts() -> str:
    import asp
    lines = []
    for h in HARBORS:
        lines.append(asp.fact("harbor", h))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", t))
    for m in MOTIVES:
        lines.append(asp.fact("motive", m))
    lines.append(asp.fact("fitting_transformation", "captain", "stormglass", "save_map"))
    lines.append(asp.fact("fitting_transformation", "child", "golden_shell", "free_crew"))
    lines.append(asp.fact("fitting_transformation", "old_pirate", "tide_rose", "return_crown"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/4.")
    model = asp.one_model(program)
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    python_set = {
        ("captain", "stormglass", "save_map"),
        ("child", "golden_shell", "free_crew"),
        ("old_pirate", "tide_rose", "return_crown"),
    }
    if set(atoms) == python_set:
        print(f"OK: clingo gate matches reasonableness set ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("clingo:", sorted(set(atoms)))
    print("python:", sorted(python_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    harbor = args.harbor or rng.choice(sorted(HARBORS))
    transformation = args.transformation or rng.choice(sorted(TRANSFORMATIONS))
    motive = args.motive or rng.choice(sorted(MOTIVES))
    if args.transformation and args.motive:
        allowed = {
            ("stormglass", "save_map"),
            ("golden_shell", "free_crew"),
            ("tide_rose", "return_crown"),
        }
        if (args.transformation, args.motive) not in allowed:
            raise StoryError("This transformation does not honestly fit that pirate trouble.")
    hero_name = args.name or rng.choice(["Nell", "Jory", "Mara"])
    crew_name = args.crew_name or rng.choice(["Boatswain Blue", "First Mate Finn", "Old Kit"])
    hero_title = rng.choice(["noble captain", "brave sailor", "sharp-eyed pirate"])
    return StoryParams(
        harbor=harbor,
        hero_name=hero_name,
        hero_title=hero_title,
        crew_name=crew_name,
        transformation=transformation,
        motive=motive,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(HARBORS[params.harbor])
    trans = TRANSFORMATIONS[params.transformation]
    motive = MOTIVES[params.motive]

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        label=params.hero_name,
        title=params.hero_title,
        meters={"salt": 1.0, "weariness": 1.0},
        memes={"hope": 1.0, "noble": 1.0},
        forms=[trans["from"]],
    ))
    crew = world.add(Entity(
        id=params.crew_name,
        kind="character",
        label=params.crew_name,
        title="crew mate",
        meters={"worry": 1.0},
        memes={"trust": 1.0},
    ))
    world.facts.update(hero=hero, crew=crew, trans=trans, motive=motive)

    world.say(
        f"In {world.harbor}, there was {hero.label}, a {hero.title} with a noble heart and a hat full of salt."
    )
    world.say(
        f"{hero.label} and {crew.label} sailed for one good reason: to {motive}."
    )
    world.para()
    world.say(
        f"But the sea was tricky, and the plan could not be rushed. {hero.label} chose to prolong the search until the tide changed, "
        f"because a noble promise was worth waiting for."
    )
    world.say(
        f"Then {trans['turn']}. In a blink, {hero.label} became {trans['to']}."
    )
    hero.meters["weariness"] = 0.0
    hero.memes["hope"] += 2.0
    hero.transformed_into = trans["to"]
    hero.forms.append(trans["to"])
    crew.memes["trust"] += 1.0

    world.para()
    if params.motive == "save_map":
        world.say(
            f"With bright new eyes, {hero.label} found the map tucked in a barnacle crack."
        )
        world.say(
            f"{crew.label} cheered as the map was saved, dry and safe."
        )
    elif params.motive == "free_crew":
        world.say(
            f"The new captain's glass hands slipped the chain apart, and the crew came free."
        )
        world.say(
            f"{crew.label} laughed, because the ship could finally breathe again."
        )
    else:
        world.say(
            f"The rose-red sash made {hero.label} stand tall as the crown was carried back to the hall."
        )
        world.say(
            f"By sunset, the island had its crown, and the pirates had honor."
        )

    world.para()
    world.say(
        f"At last, {hero.label} looked over the shining water, still noble, but changed for good."
    )
    world.say(
        f"The harbor wind smelled of salt, and the crew knew this was the kind of tale worth telling twice."
    )

    story = world.render()
    prompts = [
        f'Write a pirate tale for young children about "{params.hero_name}", a noble sailor, and a surprising transformation.',
        f"Tell a short story in a pirate style where someone at {world.harbor} must {motive} and the search is prolonged until the right moment.",
        f"Write a gentle adventure story with pirates, a noble choice, and the word \"prolong\".",
    ]
    story_qa = [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.label}, a {hero.title} in {world.harbor} who stays noble even when the sea is hard.",
        ),
        QAItem(
            question=f"Why did {hero.label} prolong the search?",
            answer=f"{hero.label} prolonged the search because the tide and the danger made it wiser to wait, and a noble promise needed the right moment.",
        ),
        QAItem(
            question=f"What changed when the transformation happened?",
            answer=f"{hero.label} changed from {trans['from']} into {trans['to']}, and that new form helped finish the pirate trouble.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does a harbor give a ship?",
            answer="A harbor gives a ship a safe place to rest, load, and wait out rough water.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
        QAItem(
            question="What does noble mean?",
            answer="Noble means good, honorable, and brave in a way that helps others.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.title:
            bits.append(f"title={e.title}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.forms:
            bits.append(f"forms={e.forms}")
        if e.transformed_into:
            bits.append(f"transformed_into={e.transformed_into}")
        lines.append(f"  {e.id:16} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(items)} compatible story combos:\n")
        for row in items:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("brineport", "Nell", "noble captain", "Boatswain Blue", "stormglass", "save_map"),
            StoryParams("moonwharf", "Jory", "brave sailor", "Old Kit", "golden_shell", "free_crew"),
            StoryParams("saltcove", "Mara", "sharp-eyed pirate", "First Mate Finn", "tide_rose", "return_crown"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
