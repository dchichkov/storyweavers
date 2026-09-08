#!/usr/bin/env python3
"""
A comic little storyworld about a matey, a nuclear-powered glance, and the
moral value of telling the truth before a silly machine makes a grand mess.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "results.py").is_file()
)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


MATEYS = ["Pip", "Luna", "Milo", "Nell", "Toby", "Rae"]
ADULTS = ["Aunt Bea", "Dr. Moss", "Captain June", "Uncle Sol"]
PLACES = ["the town fair", "the seaside lab", "the library hall", "the moon museum"]
OBJECTS = ["a brass teapot", "a purple umbrella", "a rubber chicken", "a silver spoon"]
ARCS = [
    {
        "setup": "show off a new nuclear-powered honesty lantern",
        "trouble": "the lantern flashed whenever someone made a boast",
        "lie": "the matey insisted that the flashing was part of the demonstration",
        "clue": "the lantern stayed dark when a plain truth was spoken",
        "turn": "admitted that the first boast had started the flashing",
        "fix": "they changed the lantern to reward honest answers with a gentle glow",
        "ending": "the lantern glowed softly while everyone told one true, funny thing",
        "joke": "The rubber chicken received the first honest compliment and looked deeply surprised.",
        "question": "Is the lantern judging us?",
        "reply": "Maybe not judging. Maybe it is asking us to be honest.",
    },
    {
        "setup": "test a nuclear-powered glance machine",
        "trouble": "one glance made every nearby hat spin like a tiny planet",
        "lie": "the matey claimed not to have looked at the machine",
        "clue": "the hats stopped spinning when the matey covered both eyes",
        "turn": "confessed that one curious glance had switched the machine on",
        "fix": "they placed a big red button beside the machine so glances could be announced",
        "ending": "the hats spun only when everyone shouted, 'Ready, glance!'",
        "joke": "Aunt Bea's hat spun so neatly that it seemed to be applying for a job as a helicopter.",
        "question": "Who gave the machine the troublesome glance?",
        "reply": "I did, matey. I was curious, and I should have said so.",
    },
    {
        "setup": "present a nuclear-powered kindness meter",
        "trouble": "it gave a huge beep whenever someone grabbed the best snack",
        "lie": "the matey blamed the beep on a hungry floorboard",
        "clue": "the beep stopped when the snack was shared",
        "turn": "admitted taking the largest cookie without asking",
        "fix": "they made a sharing plate and let the meter celebrate fair choices",
        "ending": "the meter played a cheerful tune as every person received a cookie",
        "joke": "The floorboard was relieved to be cleared of the accusation and requested a crumb.",
        "question": "Why did the kindness meter beep?",
        "reply": "It beeped because I took the biggest cookie without sharing first.",
    },
]


@dataclass
class StoryParams:
    matey: str
    adult: str
    place: str
    object: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Matey nuclear glance moral-value comedy.")
    parser.add_argument("--matey", choices=MATEYS)
    parser.add_argument("--adult", choices=ADULTS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", choices=OBJECTS)
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
    return StoryParams(
        matey=args.matey or rng.choice(MATEYS),
        adult=args.adult or rng.choice(ADULTS),
        place=args.place or rng.choice(PLACES),
        object=args.object or rng.choice(OBJECTS),
    )


def build_world(params: StoryParams) -> World:
    world = World(params)
    world.add(Entity("matey", "character", params.matey, "child", memes={"curiosity": 1.0}))
    world.add(Entity("adult", "character", params.adult, "helper", memes={"patience": 1.0}))
    world.add(
        Entity(
            "machine",
            "thing",
            "nuclear glance machine",
            "machine",
            meters={"energy": 0.0, "danger": 0.0},
            memes={"fairness": 0.0},
        )
    )
    return world


def generate_story(world: World) -> None:
    p = world.params
    matey = world.entities["matey"]
    adult = world.entities["adult"]
    machine = world.entities["machine"]
    index = (p.seed or 0) % len(ARCS)
    arc = ARCS[index]

    world.say(
        f"At {p.place}, {p.matey} arrived with {p.adult} and a very serious-looking {p.object}. "
        f"They had come to {arc['setup']}."
    )
    world.say(
        f"The contraption was nuclear-powered, which sounded impressive, although its safety label "
        f"mostly said, 'Please do not poke this with a spoon.'"
    )

    world.para()
    world.say(
        f"{p.matey} leaned close for one quick glance. Then {arc['trouble']}."
    )
    machine.meters["energy"] = 1.0
    machine.meters["danger"] = 0.8
    matey.memes["worry"] = 1.0
    world.say(f"{p.adult} asked, '{arc['question']}'")
    world.say(f"{p.matey} answered, '{arc['reply']}'")
    world.say(f"For a moment, {arc['lie']}.")
    world.facts["misunderstanding"] = True

    world.para()
    world.say(f"But {arc['clue']}.")
    world.say(
        f"{p.adult} crouched beside the machine. 'A careful glance can teach us something,' "
        f"{p.adult} said. 'A truthful answer can teach us even more.'"
    )
    world.say(f"{p.matey} took a breath and {arc['turn']}.")
    world.say(
        f"The machine quieted at once. {p.matey} learned the moral value of honesty: "
        f"telling the truth can stop a small worry before it grows into a giant silly problem."
    )
    matey.memes["honesty"] = 1.0
    machine.meters["danger"] = 0.1
    world.say(arc["joke"])

    world.para()
    world.say(f"Together, {p.matey} and {p.adult} {arc['fix']}.")
    world.say(f"Their new rule was simple: look carefully, speak honestly, and share the responsibility.")
    world.say(f"At last, {arc['ending']}.")
    world.say(
        f"{p.matey} gave the nuclear machine one final respectful glance, then stepped back. "
        f"{p.adult} applauded, and the {p.object} received no further duties that day."
    )
    matey.memes["pride"] = 1.0
    adult.memes["trust"] = 1.0
    machine.meters["energy"] = 0.3
    world.facts.update(
        {
            "setup": arc["setup"],
            "trouble": arc["trouble"],
            "lie": arc["lie"],
            "clue": arc["clue"],
            "turn": arc["turn"],
            "fix": arc["fix"],
            "ending": arc["ending"],
            "moral_value": "honesty",
            "settled": True,
        }
    )


def generate(params: StoryParams) -> StorySample:
    if params.matey == params.adult:
        raise StoryError("The matey and adult must have different names.")
    if not params.place or not params.object:
        raise StoryError("A place and an object are required.")
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a comedy about {params.matey}, a matey, and a nuclear glance at {params.place}.",
            "Show how a funny problem teaches the moral value of honesty.",
            "Include a brief spoken exchange that changes what the child decides to do.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            f"What was {p.matey} doing at {p.place}?",
            f"{p.matey} was helping to {f['setup']}.",
        ),
        QAItem(
            "What caused the funny trouble?",
            f"The trouble happened when {f['trouble']}.",
        ),
        QAItem(
            f"What did {p.matey} learn?",
            f"{p.matey} learned the moral value of honesty: {f['moral_value']} can stop a small worry before it becomes a bigger problem.",
        ),
        QAItem(
            "How was the problem fixed?",
            f"Together, the characters {f['fix']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does matey mean?",
            "Matey is a friendly word for a companion or friend, often used in a playful sailor style.",
        ),
        QAItem(
            "What is a glance?",
            "A glance is a quick look at something.",
        ),
        QAItem(
            "What is a moral value?",
            "A moral value is a principle that helps someone choose a good and responsible action, such as honesty or kindness.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.kind:9}) {entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
matey(matey).
machine(nuclear_machine).
feature(nuclear).
feature(glance).
moral_value(honesty).
comedy.
story_domain(matey, nuclear, glance).
good_turn(honesty) :- moral_value(honesty).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("matey", "matey"),
            asp.fact("machine", "nuclear_machine"),
            asp.fact("feature", "nuclear"),
            asp.fact("feature", "glance"),
            asp.fact("moral_value", "honesty"),
            asp.fact("comedy"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(
        asp_program(
            "#show story_domain/3.\n#show good_turn/1.\n#show moral_value/1."
        )
    )
    domains = set(asp.atoms(model, "story_domain"))
    turns = set(asp.atoms(model, "good_turn"))
    values = set(asp.atoms(model, "moral_value"))
    expected = {("matey", "nuclear", "glance")}
    if domains == expected and turns == {("honesty",)} and values == {("honesty",)}:
        for seed in range(5):
            sample = generate(
                StoryParams(
                    matey=MATEYS[seed % len(MATEYS)],
                    adult=ADULTS[seed % len(ADULTS)],
                    place=PLACES[seed % len(PLACES)],
                    object=OBJECTS[seed % len(OBJECTS)],
                    seed=seed,
                )
            )
            if not sample.story or "honest" not in sample.story.lower():
                print("Generated-story verification failed.")
                return 1
        print("OK: ASP parity and generated stories verified.")
        return 0
    print("Mismatch between ASP and Python facts.")
    return 1


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for prompt in sample.prompts:
            print(f"P: {prompt}")
        print()
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams("Luna", "Aunt Bea", "the town fair", "a rubber chicken", 0),
    StoryParams("Pip", "Dr. Moss", "the seaside lab", "a brass teapot", 1),
    StoryParams("Milo", "Captain June", "the moon museum", "a silver spoon", 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            raise SystemExit(1)
        model = asp.one_model(
            asp_program("#show story_domain/3.\n#show good_turn/1.")
        )
        print(f"story_domain={asp.atoms(model, 'story_domain')}")
        print(f"good_turn={asp.atoms(model, 'good_turn')}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 50)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + offset)
            params = resolve_params(args, rng)
            params.seed = base_seed + offset
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.matey} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
