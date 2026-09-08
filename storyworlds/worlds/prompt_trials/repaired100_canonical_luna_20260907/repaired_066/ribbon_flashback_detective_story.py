#!/usr/bin/env python3
"""
A small detective storyworld about a missing ribbon, solved with a flashback.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)


@dataclass
class DetectiveWorld:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    detective_name: str
    detective_type: str
    friend_name: str
    ribbon_color: str
    location: str
    case_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    flashback_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


DETECTIVES = ["Luna", "Milo", "Ivy", "Theo", "Nora", "Sam"]
FRIENDS = ["Pip", "Ada", "Ben", "Joy", "Max"]
COLORS = ["red", "blue", "gold", "green", "purple"]
LOCATIONS = ["the old library", "the school garden", "the town clock room", "the rainy train station"]
OPENINGS = [
    "{detective} found the empty hook just before dusk.",
    "The case began when {detective} noticed a bright clue missing from its place.",
    "Rain tapped the windows as {detective} entered {location}.",
    "At the edge of {location}, {detective} saw a box with its lid open.",
]
DIALOGUES = [
    '"Tell me exactly what you saw," {detective} said.',
    '"A mystery needs patient eyes," {detective} told {friend}.',
    '"Do not guess yet," {friend} replied. "Let us follow the clues."',
    '"The ribbon did not vanish by magic," {detective} said. "Someone moved it for a reason."',
]
CASES = [
    {
        "object": "the mayor's welcome bell",
        "problem": "the ribbon tied to the bell had disappeared",
        "clue": "three damp blue threads led from the hook toward a side door",
        "suspect": "the caretaker",
        "flashback": "A gust had lifted the ribbon from the bell, and the caretaker caught it before it fell into a puddle.",
        "action": "followed the threads through the side door and found muddy footprints beside a drying rack",
        "resolution": "the ribbon had been hung to dry after being saved from the rain",
        "image": "the bell shone again with the ribbon tied in a careful double bow",
        "lesson": "a missing thing may be part of a helpful choice, not a harmful one",
    },
    {
        "object": "the museum's tiny sailing ship",
        "problem": "its bright ribbon flag was gone",
        "clue": "a loose knot lay beside a trail of sawdust",
        "suspect": "the night guard",
        "flashback": "The night guard had removed the ribbon when a splintered mast began to crack.",
        "action": "examined the knot, traced the sawdust, and opened the repair cupboard",
        "resolution": "the ribbon was safe inside the cupboard while the ship's mast was being fixed",
        "image": "the little ship sailed beneath its restored ribbon flag",
        "lesson": "careful evidence can turn suspicion into understanding",
    },
    {
        "object": "the festival lantern",
        "problem": "its ribbon disappeared before the evening parade",
        "clue": "a silver button glittered under the bench where the lantern had rested",
        "suspect": "the parade drummer",
        "flashback": "The drummer had borrowed the ribbon to mark a loose lantern handle.",
        "action": "matched the button to the drummer's costume and checked the lantern cart",
        "resolution": "the ribbon was tied around the loose handle so nobody would carry it unsafely",
        "image": "the lantern glowed above the street with its ribbon fluttering beside the handle",
        "lesson": "a clue is strongest when it explains both what happened and why",
    },
    {
        "object": "the baker's prize cake",
        "problem": "the ribbon around its box was missing",
        "clue": "a line of flour crossed the counter and ended by the cold pantry",
        "suspect": "the delivery child",
        "flashback": "The delivery child had moved the ribbon away from a dripping shelf.",
        "action": "followed the flour line and found the ribbon tucked beneath a dry tray",
        "resolution": "the ribbon had been protected from a spill before the cake was carried away",
        "image": "the cake box rested on a dry table with the ribbon returned in a neat loop",
        "lesson": "a flashback can reveal the kind reason hidden behind a puzzling action",
    },
]


def valid_combo(params: StoryParams) -> bool:
    if not params.detective_name.strip():
        raise StoryError("detective name cannot be empty")
    if not params.friend_name.strip():
        raise StoryError("friend name cannot be empty")
    if params.ribbon_color not in COLORS:
        raise StoryError("ribbon color must be one of the registered colors")
    if params.location not in LOCATIONS:
        raise StoryError("location is not part of this small detective world")
    return True


def tell(params: StoryParams) -> DetectiveWorld:
    valid_combo(params)
    case = CASES[params.case_id % len(CASES)]
    world = DetectiveWorld()
    detective = world.add(Entity(
        "detective", "child", params.detective_name,
        meters={"attention": 1.0, "memory": 0.5},
        memes={"curiosity": 1.0, "courage": 0.5},
    ))
    friend = world.add(Entity(
        "friend", "helper", params.friend_name,
        meters={"patience": 1.0},
        memes={"trust": 1.0},
    ))
    ribbon = world.add(Entity(
        "ribbon", "clue", f"{params.ribbon_color} ribbon",
        meters={"wet": 0.0, "visible": 1.0},
        memes={"importance": 1.0},
        props={"color": params.ribbon_color},
    ))
    world.add(Entity(
        "case_object", "object", case["object"],
        meters={"safe": 0.0},
        memes={"value": 1.0},
    ))
    world.facts.update(
        case=case,
        detective=detective,
        friend=friend,
        ribbon=ribbon,
        location=params.location,
        flashback_used=False,
        solved=False,
    )

    world.say(OPENINGS[params.opening_id % len(OPENINGS)].format(
        detective=params.detective_name, location=params.location,
    ))
    world.say(f"The mystery concerned {case['object']}: {case['problem']}.")
    world.say(f"{params.detective_name} studied the empty place and wondered whether {case['suspect']} had taken it.")
    world.para()

    world.say(DIALOGUES[params.dialogue_id % len(DIALOGUES)].format(
        detective=params.detective_name, friend=params.friend_name,
    ))
    world.say(f'"I saw {case["clue"]}," {params.friend_name} answered.')
    world.say(f'"Then we have a trail, not a guess," {params.detective_name} said.')
    world.say(f"They searched {params.location} without touching anything that did not belong to them.")
    world.para()

    world.say(f"At the side of the room, {params.detective_name} remembered a small detail from earlier that day.")
    world.say(f"FLASHBACK: {case['flashback']}")
    world.facts["flashback_used"] = True
    world.facts["flashback"] = case["flashback"]
    detective.memes["courage"] += 1.0
    world.say(f'"The ribbon was moved to protect something," {params.detective_name} said.')
    world.say(f'"And the clue can show us where," {params.friend_name} replied.')
    world.para()

    world.say(f"{params.detective_name} {case['action']}.")
    world.say(f"The memory fit every clue: {case['resolution']}.")
    world.say(f'"We should ask before blaming anyone," {params.friend_name} said.')
    world.say(f'"You are right," {params.detective_name} replied. "The case is solved."')
    ribbon.meters["visible"] = 1.0
    ribbon.meters["wet"] = 0.0
    world.facts["solved"] = True
    world.para()

    world.say(f"At last, {case['resolution']}.")
    world.say(f"{case['image']}.")
    world.say(f"{params.detective_name} learned that {case['lesson']}.")
    return world


ASP_RULES = r"""
seen_clue(detective) :- clue_found(detective).
remembered(detective) :- flashback(detective).
solved :- seen_clue(detective), remembered(detective), safe(ribbon).
#show seen_clue/1.
#show remembered/1.
#show solved/0.
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp
    return "\n".join([
        asp.fact("clue_found", "detective"),
        asp.fact("flashback", "detective"),
        asp.fact("safe", "ribbon"),
    ])


def asp_program(params: Optional[StoryParams] = None, show: str = "") -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {str(atom) for atom in model}
    if not any(atom.startswith("solved") for atom in names):
        print("MISMATCH: ASP detective twin did not solve the case.")
        return 1
    for params in sample_params():
        sample = generate(params)
        if not sample.world or not sample.world.facts["solved"]:
            print("MISMATCH: generated detective story was not solved.")
            return 1
    print("OK: Python and ASP detective reasoning agree.")
    return 0


def generation_prompts(world: DetectiveWorld) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a child-friendly detective story about {case['problem']} in {world.facts['location']}.",
        "Use a flashback to reveal why the missing ribbon was moved.",
        "Include clues, a back-and-forth dialogue, a fair investigation, and a concrete solved ending.",
    ]


def story_qa(world: DetectiveWorld) -> list[QAItem]:
    case = world.facts["case"]
    detective = world.facts["detective"].label
    friend = world.facts["friend"].label
    return [
        QAItem(
            f"What was missing in {detective}'s case?",
            f"The missing item was the {world.facts['ribbon'].label} connected with {case['object']}: {case['problem']}.",
        ),
        QAItem(
            "What clue guided the investigation?",
            f"The clue was that {case['clue']}. It gave the detectives a physical trail to follow.",
        ),
        QAItem(
            "What did the flashback reveal?",
            f"The flashback revealed that {case['flashback']}",
        ),
        QAItem(
            f"How did {detective} and {friend} solve the mystery?",
            f"{detective} {case['action']}. Their memory explained why the ribbon had been moved: {case['resolution']}.",
        ),
        QAItem(
            "How did the story end?",
            f"It ended with {case['image']}. The ribbon was safe, and the mystery was solved without unfairly blaming anyone.",
        ),
    ]


def world_knowledge_qa(world: DetectiveWorld) -> list[QAItem]:
    return [
        QAItem("What does a detective do?", "A detective studies clues, asks careful questions, and connects evidence to what happened."),
        QAItem("What is a flashback?", "A flashback is a story moment that shows an earlier event so the present mystery becomes clearer."),
        QAItem("What is a ribbon?", "A ribbon is a narrow strip of cloth used for tying, decorating, marking, or carrying a message."),
        QAItem("Why should people avoid guessing too quickly?", "Waiting for evidence helps people understand the truth and prevents unfair blame."),
    ]


def sample_params() -> list[StoryParams]:
    return [
        StoryParams("Luna", "girl", "Pip", "red", LOCATIONS[0], 0, 0, 0, 0, 0),
        StoryParams("Milo", "boy", "Ada", "blue", LOCATIONS[1], 1, 1, 1, 1, 1),
        StoryParams("Ivy", "girl", "Ben", "gold", LOCATIONS[2], 2, 2, 2, 2, 2),
        StoryParams("Theo", "boy", "Joy", "green", LOCATIONS[3], 3, 3, 3, 3, 3),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A ribbon flashback detective storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--color", choices=COLORS)
    parser.add_argument("--location", choices=LOCATIONS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        detective_name=args.name or rng.choice(DETECTIVES),
        detective_type="girl" if (args.name or rng.choice(["girl", "boy"])) in {"Luna", "Ivy", "Nora"} else "boy",
        friend_name=args.friend or rng.choice(FRIENDS),
        ribbon_color=args.color or rng.choice(COLORS),
        location=args.location or rng.choice(LOCATIONS),
        case_id=rng.randrange(len(CASES)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        flashback_id=rng.randrange(4),
        ending_id=rng.randrange(4),
        seed=args.seed,
    )


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: DetectiveWorld) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: meters={entity.meters} memes={entity.memes} props={entity.props}"
        )
    lines.append(f"  facts: {world.facts}")
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
        print(asp_program(show="#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print("\n".join(map(str, asp.one_model(asp_program()))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in sample_params()]
    else:
        samples = []
        seen = set()
        for index in range(max(args.n, 1) * 20):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
            header = f"### {sample.params.detective_name}: the {sample.params.ribbon_color} ribbon"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
