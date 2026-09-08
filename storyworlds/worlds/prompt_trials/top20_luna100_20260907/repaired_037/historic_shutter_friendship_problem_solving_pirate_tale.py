#!/usr/bin/env python3
"""
A small pirate-tale world about an historic harbor shutter, friendship, and
problem solving.

Seed tale:
A young pirate found an historic wooden shutter hanging crooked on an old
harbor tower. When a storm threatened to tear it away, the pirate tried to fix
it alone, but the heavy shutter slipped. A friend noticed the loose hinge and
suggested using a rope, a barrel, and teamwork. Together they secured the
shutter before the rain, learning that good friends solve hard problems by
sharing ideas.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    historic: bool = True


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    place: str
    pirate_name: str
    friend_name: str
    incident: int = 0
    opening: int = 0
    dialogue: int = 0
    solution: int = 0
    ending: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "harbor_tower": Setting(
        place="the historic harbor tower",
        affords={"shutter", "rope", "barrel"},
    ),
    "old_lighthouse": Setting(
        place="the historic lighthouse",
        affords={"shutter", "rope", "barrel"},
    ),
    "captain_house": Setting(
        place="the historic captain's house",
        affords={"shutter", "rope", "barrel"},
    ),
}

PIRATE_NAMES = ["Luna", "Mara", "Finn", "Tessa", "Cove", "Pip"]
FRIEND_NAMES = ["Beau", "Nell", "Jory", "Wren", "Kai", "Mina"]

INCIDENTS = [
    {
        "sight": "the old shutter banging against the tower wall",
        "risk": "a rising storm could rip it from its hinges",
        "mistake": "pull the shutter down alone",
        "clue": "one iron hinge had slipped while the lower hinge still held",
        "cause": "the upper hinge pin had worked loose",
        "lesson": "a hard job becomes safer when friends inspect it together",
        "ending": "The historic shutter rested squarely against the tower, ready for another calm morning.",
    },
    {
        "sight": "a striped shutter swinging above the moonlit harbor",
        "risk": "the swinging wood might fall across the narrow dock",
        "mistake": "climb up and catch it with bare hands",
        "clue": "the shutter moved most whenever a gust filled the torn sailcloth nearby",
        "cause": "wind was tugging the sailcloth against a loose hook",
        "lesson": "solving a problem begins with noticing what makes it move",
        "ending": "The striped shutter stayed still while lanterns glowed along the safe dock.",
    },
    {
        "sight": "a faded blue shutter creaking beside the lighthouse lamp",
        "risk": "rain could soak the lamp room if the shutter opened wider",
        "mistake": "jam a sword between the boards",
        "clue": "the latch was sound, but the wall hook had twisted sideways",
        "cause": "the old hook had turned in its wooden socket",
        "lesson": "the best tool is the one that fits the real problem",
        "ending": "The blue shutter clicked shut, and the lighthouse beam swept peacefully over the sea.",
    },
    {
        "sight": "a carved shutter trembling over the captain's doorway",
        "risk": "the heavy panel could crush the flower boxes below",
        "mistake": "lift it before clearing the boxes",
        "clue": "the boxes blocked the bottom edge and made the panel seem heavier",
        "cause": "the shutter needed space before it could be moved safely",
        "lesson": "clearing a path can be part of fixing a problem",
        "ending": "The carved shutter guarded the doorway while the flower boxes bloomed beneath it.",
    },
]

OPENINGS = [
    "At sunset, young pirate {pirate} sailed into {place}, where gulls cried over the copper sea.",
    "The tide was turning beneath {place} when pirate {pirate} spotted something unusual.",
    "A salty wind curled through {place}, and {pirate} was checking the old buildings before supper.",
    "Pirate {pirate} and a small crew boat reached {place} just as the sky darkened.",
]

DIALOGUES = [
    '"I can fix it before the storm," said {pirate}. "Not alone," replied {friend}. "Let us study the hinge first."',
    '"Hold fast!" cried {pirate}. "I am holding," said {friend}, "but we need a plan, not just stronger arms."',
    '"My rope will help," said {friend}. "{pirate}, tell me where to tie it."',
    '"I thought pirates solved everything with courage," said {pirate}. "Courage also means asking a friend for an idea," answered {friend}.',
]

SOLUTIONS = [
    "They looped a stout rope around the shutter, rolled a barrel beneath its lower edge, and raised the loose side together.",
    "One friend steadied the barrel while the other tied the rope above the hinge, making a safe brace before touching the shutter.",
    "They moved the boxes away, placed the barrel under the panel, and used the rope to guide the shutter instead of wrestling with it.",
    "They secured the sailcloth, tested the hinge, and tied the shutter gently while both friends watched for each other's signal.",
]

ENDINGS = [
    '"We did not need one hero," said {friend}. "We needed two careful friends," {pirate} agreed.',
    '"A shared plan is treasure," said {pirate}, as the storm clouds sailed past the harbor.',
    '"Next time we ask before we pull," promised {pirate}. {friend} smiled. "That is how a crew stays strong."',
    "The friends bumped elbows, and even the grumpy gull seemed to approve of their clever work.",
]


ASP_RULES = r"""
#show valid/2.
setting(harbor_tower). setting(old_lighthouse). setting(captain_house).
historic(harbor_tower). historic(old_lighthouse). historic(captain_house).
affords(harbor_tower,shutter). affords(harbor_tower,rope). affords(harbor_tower,barrel).
affords(old_lighthouse,shutter). affords(old_lighthouse,rope). affords(old_lighthouse,barrel).
affords(captain_house,shutter). affords(captain_house,rope). affords(captain_house,barrel).
valid(P, shutter) :- historic(P), affords(P, shutter).
valid(P, rope) :- historic(P), affords(P, rope).
valid(P, barrel) :- historic(P), affords(P, barrel).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("setting", key))
        if setting.historic:
            lines.append(asp.fact("historic", key))
        for item in sorted(setting.affords):
            lines.append(asp.fact("affords", key, item))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple]:
    return sorted(
        (place, item)
        for place, setting in SETTINGS.items()
        for item in setting.affords
        if setting.historic
    )


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo - py))
    print("  only in python:", sorted(py - clingo))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.pirate_name == params.friend_name:
        raise StoryError("The pirate and friend must have different names.")

    setting = SETTINGS[params.place]
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    world = StoryState(setting)

    pirate = world.add(Entity(
        id=params.pirate_name,
        kind="character",
        type="pirate",
        memes={"courage": 0.7, "patience": 0.3},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="friend",
        memes={"friendship": 0.8, "problem_solving": 0.8},
    ))
    shutter = world.add(Entity(
        id="historic_shutter",
        type="shutter",
        label="the historic shutter",
        owner="harbor_keepers",
        meters={"weight": 8.0, "height": 2.0},
        memes={"importance": 0.9},
    ))
    rope = world.add(Entity(
        id="rope",
        type="tool",
        label="a stout rope",
        meters={"length": 6.0},
    ))
    barrel = world.add(Entity(
        id="barrel",
        type="tool",
        label="a wooden barrel",
        meters={"height": 0.8},
    ))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        pirate=pirate.id, place=setting.place
    ))
    world.say(f"There they saw {incident['sight']}.")
    world.say(
        f"The old wood was historic, but the danger was fresh: {incident['risk']}."
    )
    world.say(
        f'{pirate.id} reached for the shutter. "I will {incident["mistake"]}," '
        f'{pirate.id} declared.'
    )

    world.para()
    world.say(DIALOGUES[params.dialogue % len(DIALOGUES)].format(
        pirate=pirate.id, friend=friend.id
    ))
    world.say(f"Together they stepped back and looked closely. They noticed that {incident['clue']}.")
    world.say(
        f"{friend.id} pointed to the rope and barrel. "
        f'"If we use both, the shutter will not have to fight us," {friend.id} said.'
    )
    world.say(SOLUTIONS[params.solution % len(SOLUTIONS)])
    world.say(
        f"They counted together: one, two, three. The rope held, the barrel bore the weight, "
        f"and the shutter swung safely into place."
    )

    world.para()
    world.say(
        f"The storm arrived with a roar, but the shutter stayed firm because {incident['cause']} "
        f"had been repaired and braced."
    )
    world.say(
        f'"We solved it by listening," {friend.id} said. '
        f'"And by trusting each other," {pirate.id} replied.'
    )
    world.say(
        ENDINGS[params.ending % len(ENDINGS)].format(
            pirate=pirate.id, friend=friend.id
        )
    )
    world.say(
        f"They secured the rope and barrel for the next crew, then sailed home beneath a clearing sky. "
        f"{incident['ending']}"
    )

    world.facts.update(
        pirate=pirate,
        friend=friend,
        shutter=shutter,
        rope=rope,
        barrel=barrel,
        incident=incident,
        place=setting.place,
        repaired=True,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a pirate tale about {f['pirate'].id} finding {f['incident']['sight']}.",
        f"Tell a friendship story where {f['pirate'].id} and {f['friend'].id} solve the shutter problem together.",
        f"Write a child-friendly historic harbor adventure with dialogue, a rope, a barrel, and teamwork.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    pirate = f["pirate"].id
    friend = f["friend"].id
    return [
        QAItem(
            question="What historic object caused the problem?",
            answer=f"The problem centered on the historic shutter at {f['place']}. It was heavy and loose in the stormy wind.",
        ),
        QAItem(
            question=f"What did {pirate} first want to do?",
            answer=f"{pirate} first wanted to {incident['mistake']}, but that would have been unsafe to do alone.",
        ),
        QAItem(
            question=f"How did {friend} help solve the problem?",
            answer=f"{friend} helped by studying the clue and suggesting a rope and barrel so the shutter could be supported and guided safely.",
        ),
        QAItem(
            question="Why did the friends use a rope and a barrel?",
            answer="The rope steadied the shutter while the barrel supported its heavy lower edge, so the friends could move it without wrestling with it.",
        ),
        QAItem(
            question=f"What did {pirate} learn about friendship?",
            answer=f"{pirate} learned that {incident['lesson']}. Sharing ideas made the repair safer and stronger.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a wooden or metal panel that can cover a window or opening.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important or connected to the past.",
        ),
        QAItem(
            question="Why can teamwork help with a difficult repair?",
            answer="Teamwork can help because people can notice different clues, share tools, and make a heavy or risky job safer.",
        ),
    ]


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


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:18} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  facts: repaired={world.facts.get('repaired')}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    pirate = args.name or rng.choice(PIRATE_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != pirate])
    return StoryParams(
        place=place,
        pirate_name=pirate,
        friend_name=friend,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        solution=rng.randrange(len(SOLUTIONS)),
        ending=rng.randrange(len(ENDINGS)),
    )


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
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate tale world about an historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        values = asp_valid()
        print(f"{len(values)} valid combinations:\n")
        for place, item in values:
            print(f"  {place:18} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                pirate_name="Luna",
                friend_name="Beau",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            attempt += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
