#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {
        "distance": 0.0,
        "visibility": 0.0,
        "fullness": 0.0,
        "safety": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "worry": 0.0,
        "trust": 0.0,
        "humor": 0.0,
        "caution": 0.0,
        "relief": 0.0,
    })


@dataclass
class StoryParams:
    detective: str
    detective_type: str
    usher: str
    usher_type: str
    suspect: str
    suspect_type: str
    gland: str
    auditorium: str
    scenario_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS = [
    {
        "object": "the brass comedy mask",
        "problem": "the mask vanished from the locked display before the evening play",
        "clue": "a sticky yellow smear beneath the display shelf",
        "false_clue": "a trail of glitter leading toward the costume cupboard",
        "method": "Luna compared the smear with the custard served backstage and checked which prop boxes had been opened",
        "culprit": "the stingy stage manager, Mr. Pinch",
        "reason": "he had hidden the mask so he would not have to lend it to the children's comedy",
        "ending": "the mask winked from the prop table while the audience laughed at Mr. Pinch's very serious apology",
        "lesson": "saving a little trouble by hiding the truth usually creates a much bigger mess",
        "joke": "A detective who follows glitter may end up solving a dance recital instead of a mystery.",
    },
    {
        "object": "the golden ticket box",
        "problem": "the box disappeared from the auditorium office during rehearsal",
        "clue": "three dry popcorn kernels beside a loose ventilation grate",
        "false_clue": "a muddy shoeprint under the front row",
        "method": "Luna measured the shoeprint, then followed the popcorn from the office to the narrow service passage",
        "culprit": "the stingy ticket keeper, Mrs. Quibble",
        "reason": "she had tucked the box away because she wanted to keep every last ticket for herself",
        "ending": "the tickets were shared at the doors, and Mrs. Quibble had to sit in the back with a very small seat",
        "lesson": "fair sharing keeps a crowd happier than clever hoarding",
        "joke": "The ticket keeper had counted so carefully that she forgot people were not numbers.",
    },
    {
        "object": "the conductor's silver baton",
        "problem": "the baton vanished before the orchestra's big finale",
        "clue": "a tiny feather caught in the handle's velvet case",
        "false_clue": "a loud sneeze from the balcony",
        "method": "Luna traced the feather to the costume rack and found that one bird costume had a baton-shaped bulge",
        "culprit": "the stingy costume painter, Bram",
        "reason": "he had borrowed the baton as a handle for a paint pot and was afraid to admit it",
        "ending": "the baton returned to the conductor, while Bram painted a proper handle on his pot",
        "lesson": "borrowing without asking can turn a small shortcut into a public muddle",
        "joke": "Bram claimed the baton was a paintbrush, but it had been conducting dust all afternoon.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautious auditorium whodunit.")
    parser.add_argument("--detective")
    parser.add_argument("--detective-type")
    parser.add_argument("--usher")
    parser.add_argument("--usher-type")
    parser.add_argument("--suspect")
    parser.add_argument("--suspect-type")
    parser.add_argument("--gland")
    parser.add_argument("--auditorium")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        detective=args.detective or rng.choice(["Luna", "Milo", "Nora", "Pip"]),
        detective_type=args.detective_type or rng.choice(["rabbit", "mouse", "fox", "badger"]),
        usher=args.usher or rng.choice(["Tess", "Ollie", "Bea", "Rufus"]),
        usher_type=args.usher_type or rng.choice(["otter", "duck", "squirrel", "hedgehog"]),
        suspect=args.suspect or rng.choice(["Mr. Pinch", "Mrs. Quibble", "Bram", "Captain Thrift"]),
        suspect_type=args.suspect_type or rng.choice(["weasel", "crow", "goat", "mole"]),
        gland=args.gland or rng.choice(["the laugh gland", "the echo gland", "the tickle gland"]),
        auditorium=args.auditorium or rng.choice([
            "the Moonbeam Auditorium",
            "the Old Red Auditorium",
            "the Riverside Auditorium",
        ]),
        scenario_index=rng.randrange(len(SCENARIOS)),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    if params.detective == params.suspect:
        raise StoryError("The detective and suspect must have different names.")
    if not params.detective.strip() or not params.auditorium.strip():
        raise StoryError("Detective and auditorium names cannot be empty.")

    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    world = World(Setting(params.auditorium))
    detective = world.add(Entity("detective", "animal", params.detective, params.detective_type))
    usher = world.add(Entity("usher", "animal", params.usher, params.usher_type))
    suspect = world.add(Entity("suspect", "animal", params.suspect, params.suspect_type))
    gland = world.add(Entity("gland", "body_part", params.gland, "gland", owner=detective.id))
    missing = world.add(Entity("missing", "prop", scenario["object"], "theater_prop"))
    world.facts.update(
        detective=detective,
        usher=usher,
        suspect=suspect,
        gland=gland,
        missing=missing,
        scenario=scenario,
    )

    detective.memes["caution"] = 1
    usher.memes["worry"] = 1
    suspect.memes["worry"] = 1

    world.say(
        f"At {params.auditorium}, {params.detective} the {params.detective_type} "
        f"was practicing careful detective work with {params.usher} the {params.usher_type}."
    )
    world.say(
        f"Just before the curtain rose, {params.usher} cried, "
        f'"The {scenario["object"]} is gone!" The auditorium grew quiet except for one nervous cough.'
    )
    world.say(
        f"{params.detective} touched {params.gland}, the little gland that made every joke feel extra funny, "
        f"but remembered that a laugh was not proof."
    )
    world.para()

    world.say(
        f"The case seemed simple: {scenario['problem']}. "
        f"{params.suspect}, the {params.suspect_type}, pointed toward the nearest exit."
    )
    world.say(
        f'"It must be a stranger," said {params.suspect}. '
        f'"Or perhaps a very tall squirrel wearing shoes."'
    )
    world.say(
        f'"A funny guess is still only a guess," {params.detective} replied. '
        f'"We will look, listen, and touch nothing that does not belong to us."'
    )
    world.say(f"Near the display, {scenario['false_clue']}.")
    detective.memes["caution"] += 1
    detective.meters["visibility"] = 0.4
    world.para()

    world.say(
        f"Then {params.detective} noticed {scenario['clue']}. "
        f"The clue was small, but it connected the missing {scenario['object']} to the backstage passage."
    )
    world.say(
        f"{params.usher} asked, '"Can we open the boxes?" '
        f'"Only with permission," said {params.detective}. "A careful mystery leaves no new mystery behind."'
    )
    world.say(f"With the usher's help, {scenario['method']}.")
    missing.meters["distance"] = 1
    missing.meters["visibility"] = 1
    detective.memes["trust"] += 1
    world.para()

    world.say(
        f"The search ended beside {params.suspect}'s workbench. "
        f"There sat the missing {scenario['object']}, covered by a cloth."
    )
    world.say(
        f'"I did not steal it," {params.suspect} muttered. '
        f'"I only hid it because {scenario["reason"][0].lower() + scenario["reason"][1:]}"'
    )
    world.say(
        f"{params.detective} answered, 'Hiding something that belongs to everyone is still wrong. "
        f"Please return it and tell the truth before the play begins.'"
    )
    suspect.memes["worry"] = 0
    suspect.memes["relief"] = 1
    missing.meters["safety"] = 1
    missing.meters["fullness"] = 1
    world.say(f"{params.suspect} nodded and carried it back. {scenario['ending']}.")
    world.para()

    world.say(
        f"The audience never learned every nervous detail, but {params.usher} did learn the important part: "
        f"{scenario['lesson']}."
    )
    world.say(
        f"{params.detective}'s {params.gland} gave one tiny giggle when the lights came up. "
        f"{scenario['joke']}"
    )
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    world.log("clue_verified=true")
    world.log("object_returned=true")
    world.log("caution_used=true")
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    detective = world.facts["detective"]
    return [
        f"Write a child-friendly whodunit in an auditorium where {detective.label} follows evidence instead of guesses.",
        f"Tell a cautious mystery about {scenario['object']} disappearing and being returned honestly.",
        "Include gentle humor, a brief dialogue exchange, and a clear consequence for hiding the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = world.facts["scenario"]
    detective = world.facts["detective"]
    usher = world.facts["usher"]
    suspect = world.facts["suspect"]
    return [
        QAItem(
            f"What disappeared from the auditorium?",
            f"The {scenario['object']} disappeared before the performance, so the characters had to find it safely.",
        ),
        QAItem(
            f"What clue did {detective.label} follow?",
            f"{detective.label} followed {scenario['clue']}, which connected the missing prop to the backstage passage.",
        ),
        QAItem(
            f"Why did {suspect.label} hide the object?",
            f"{suspect.label} hid it because {scenario['reason'][0].lower() + scenario['reason'][1:]}.",
        ),
        QAItem(
            f"How did {usher.label} help solve the mystery?",
            f"{usher.label} helped search carefully while respecting permission, and the usher helped return the object without damaging anything.",
        ),
        QAItem(
            "What lesson did the mystery teach?",
            f"It taught that {scenario['lesson']}. The returned prop and honest explanation proved the lesson.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an auditorium?",
            "An auditorium is a large room where people gather to watch performances, hear music, or listen to speakers.",
        ),
        QAItem(
            "What is a gland?",
            "A gland is a body part that makes and releases a substance the body uses. In this story, the silly gland is imaginary and adds humor.",
        ),
        QAItem(
            "What does stingy mean?",
            "Stingy means unwilling to share or spend what one has, even when sharing would be fair or helpful.",
        ),
        QAItem(
            "Why should a detective check clues carefully?",
            "A detective should check clues carefully because a guess can blame the wrong person, while evidence can reveal what really happened.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = [f"type={entity.type}"]
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(details))
    lines.extend(world.trace_log)
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
entity(detective).
entity(usher).
entity(suspect).
entity(missing_prop).
clue_checked.
object_returned.
cautious_search.
truth_told.

solved :- clue_checked, object_returned, cautious_search, truth_told.
safe_ending :- solved.
#show solved/0.
#show safe_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("clue_checked"),
        asp.fact("object_returned"),
        asp.fact("cautious_search"),
        asp.fact("truth_told"),
    ])


def asp_program(show: str = "#show solved/0. #show safe_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"solved/0", "safe_ending/0"}
    if names != expected:
        print(f"MISMATCH: {sorted(names)} != {sorted(expected)}")
        return 1
    rng = random.Random(17)
    for _ in range(5):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if "disappeared" not in sample.story or "returned" not in sample.story:
            print("MISMATCH: generated story lacks a complete mystery arc")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "rabbit", "Tess", "otter", "Mr. Pinch", "weasel", "the laugh gland", "the Moonbeam Auditorium", 0),
    StoryParams("Milo", "mouse", "Bea", "squirrel", "Mrs. Quibble", "crow", "the echo gland", "the Old Red Auditorium", 1),
    StoryParams("Nora", "fox", "Ollie", "duck", "Bram", "goat", "the tickle gland", "the Riverside Auditorium", 2),
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
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
