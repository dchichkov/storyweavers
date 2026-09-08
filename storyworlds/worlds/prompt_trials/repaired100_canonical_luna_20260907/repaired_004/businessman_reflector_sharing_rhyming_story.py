#!/usr/bin/env python3
"""
A small rhyming storyworld about a businessman, a reflector, and the
difference sharing can make on a dark road.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
    name: str
    town: str
    mood: str
    seed: Optional[int] = None


SETTING = Setting(
    place="a bright little town",
    affords={"business", "reflection", "sharing", "kindness"},
)

NAMES = ["Luna", "Milo", "Nora", "Pip", "Tessa", "Arlo"]
TOWNS = ["Meadowtown", "Sunbeam", "Cloverfield", "Moonbridge"]
MOODS = ["cheerful", "thoughtful", "patient", "hopeful"]

OPENINGS = [
    "In {town}, where the shop bells chimed and the street lamps shone, lived {name}, a {mood} businessman with a busy mind.",
    "There once was a businessman named {name}, who sold bright plans beneath the morning sun in the lively town of {town}.",
    "In a town called {town}, {name} wore a neat coat and carried a careful book, for {name} was a businessman who liked every number just so.",
]

OBSTACLES = [
    {
        "problem": "A thick evening fog rolled over the market road.",
        "risk": "Without a clear marker, travelers could miss the turn and stumble into a ditch.",
        "clue": "a small reflector that flashed whenever the moon touched it",
        "action": "{name} lifted the reflector high so everyone could see the safe road.",
        "result": "The reflector blinked bright, and the travelers followed its friendly light.",
        "ending": "The reflector twinkled like a tiny star beside the road.",
        "answer": "A thick evening fog covered the market road, making the safe turn hard to see.",
    },
    {
        "problem": "A delivery cart lost a wheel near the bridge.",
        "risk": "The boxes might spill before they reached the waiting families.",
        "clue": "a sturdy reflector tucked beside the cart",
        "action": "{name} used the reflector to signal for help while neighbors gathered around.",
        "result": "The neighbors lifted together, and the wheel slipped safely back into place.",
        "ending": "The reflector shone from the cart as every box reached its rightful door.",
        "answer": "A delivery cart lost a wheel near the bridge.",
    },
    {
        "problem": "The town's only lantern went dark before the evening market.",
        "risk": "People might hurry through the dark and bump into one another.",
        "clue": "a polished reflector that could send a bright signal across the square",
        "action": "{name} shared the reflector with the lantern keeper and the market children.",
        "result": "They caught the moonlight and guided it from stall to stall.",
        "ending": "Moonlight danced from the reflector while the market smiled below.",
        "answer": "The town's only lantern went dark before the evening market.",
    },
    {
        "problem": "Rain washed away the painted sign at the fork.",
        "risk": "A wrong turn could send the shoppers far from home.",
        "clue": "a red reflector still fixed to the old signpost",
        "action": "{name} shared the reflector's bright signal while friends rebuilt the sign.",
        "result": "The sign stood again, and the red reflector marked the right path.",
        "ending": "The red reflector glowed beside the new sign after the rain.",
        "answer": "Rain washed away the painted sign at the fork.",
    },
]

MORALS = [
    "A business grows brightest when its good tools and good fortune are shared.",
    "A little light becomes a great guide when caring hands pass it around.",
    "Sharing does not make a gift smaller; it makes the safe road wider.",
]

RHYME_LINES = [
    '"Share what you can, and help where you may," said {helper}. "A shared little light can brighten the way."',
    '"Do not keep every good thing near," said {helper}. "Pass it along, and the road grows clear."',
    '"One hand can point, and two hands can mend," said {helper}. "A shared bright tool can help every friend."',
]

HELPERS = ["the baker", "a young cyclist", "the bridge keeper", "a market girl"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        ("town", "businessman", "reflector"),
        ("town", "businessman", "sharing"),
        ("town", "reflector", "sharing"),
    ]


def build_world(params: StoryParams) -> World:
    if params.name not in NAMES:
        raise StoryError(f"unknown businessman name: {params.name}")
    if params.town not in TOWNS:
        raise StoryError(f"unknown town: {params.town}")
    if params.mood not in MOODS:
        raise StoryError(f"unknown mood: {params.mood}")

    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum((i + 1) * ord(c) for i, c in enumerate(
            f"{params.name}:{params.town}:{params.mood}"
        ))
    rng = random.Random(stable_seed)
    obstacle = rng.choice(OBSTACLES)
    helper = rng.choice(HELPERS)
    rhyme = rng.choice(RHYME_LINES)
    moral = rng.choice(MORALS)

    world = World(SETTING)
    businessman = world.add(Entity(
        "businessman", "person", params.name,
        meters={"energy": 1.0, "risk": 0.0},
        memes={"worry": 0.0, "generosity": 0.0, "joy": 0.0},
    ))
    reflector = world.add(Entity(
        "reflector", "tool", "a silver reflector",
        meters={"brightness": 1.0, "usefulness": 0.0},
        memes={"shared": 0.0},
    ))
    helper_entity = world.add(Entity(
        "helper", "neighbor", helper,
        meters={"distance": 1.0},
        memes={"trust": 0.0},
    ))

    world.facts.update(
        businessman=businessman,
        reflector=reflector,
        helper=helper,
        obstacle=obstacle,
        moral=moral,
        rhyme=rhyme,
    )

    world.say(OPENINGS[rng.randrange(len(OPENINGS))].format(
        town=params.town,
        name=params.name,
        mood=params.mood,
    ))
    world.say(
        f"{params.name} carried a little silver reflector in a satchel, "
        "for a wise businessman watched not only his coins, but also the road around him."
    )
    world.say(
        f"Each morning {params.name} said, \"A bright plan is fine, but a kind plan should shine.\""
    )
    world.para()

    businessman.meters["risk"] = 1.0
    businessman.memes["worry"] = 1.0
    world.say(obstacle["problem"])
    world.say(obstacle["risk"])
    world.say(
        f"{params.name} held the reflector close and whispered, "
        "\"It can help me, but it should not help me alone.\""
    )
    world.say(rhyme.format(helper=helper))
    world.para()

    reflector.meters["usefulness"] = 1.0
    reflector.memes["shared"] = 1.0
    businessman.memes["generosity"] = 1.0
    helper_entity.memes["trust"] = 1.0
    world.say(
        f"Then {params.name} noticed {obstacle['clue']}. "
        f"{params.name} chose to share it instead of keeping it hidden."
    )
    world.say(obstacle["action"].format(name=params.name))
    world.say(obstacle["result"])
    world.say(
        f"The {helper} smiled. \"Your reflector helped us, and our helping helped you.\""
    )
    world.para()

    businessman.meters["risk"] = 0.0
    businessman.memes["worry"] = 0.0
    businessman.memes["joy"] = 1.0
    reflector.meters["usefulness"] = 2.0
    world.say(
        f"At last, the road was safe and the work was done. "
        f"{params.name} saw that sharing had turned one small tool into help for the whole town."
    )
    world.say(f"{obstacle['ending']}")
    world.say(f"{params.name} tucked away the empty satchel and sang: \"{moral}\"")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle rhyming story about a businessman who shares a reflector.',
        f"Tell a child-friendly story set in {world.setting.place} where {f['businessman'].label} solves a problem through sharing.",
        f"Write a rhyming tale in which a reflector helps people because it is shared, not hidden.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    businessman = f["businessman"]
    obstacle = f["obstacle"]
    return [
        QAItem(
            question="Who was the main character?",
            answer=f"{businessman.label} was the businessman at the center of the story.",
        ),
        QAItem(
            question="What problem appeared?",
            answer=obstacle["answer"],
        ),
        QAItem(
            question="What did the businessman share?",
            answer="He shared a small silver reflector so other people could use its bright signal.",
        ),
        QAItem(
            question="How did sharing change the situation?",
            answer=f"Sharing the reflector helped everyone respond together: {obstacle['result']}",
        ),
        QAItem(
            question="What lesson did the businessman learn?",
            answer=f["moral"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reflector?",
            answer="A reflector is a bright surface or tool that sends light back so it can be seen.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something that you have.",
        ),
        QAItem(
            question="Why can a reflector help on a dark road?",
            answer="A reflector can catch light and make a person, bicycle, sign, or path easier to see.",
        ),
        QAItem(
            question="What does a businessman do?",
            answer="A businessman organizes or sells goods and services as part of a business.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:14} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "town"),
        asp.fact("entity", "businessman"),
        asp.fact("entity", "reflector"),
        asp.fact("feature", "sharing"),
        asp.fact("has_role", "businessman", "businessman"),
        asp.fact("has_tool", "businessman", "reflector"),
        asp.fact("supports", "reflector", "sharing"),
    ])


ASP_RULES = r"""
valid_story(town, businessman, reflector) :-
    setting(town),
    entity(businessman),
    entity(reflector),
    has_role(businessman, businessman),
    has_tool(businessman, reflector).

valid_story(town, businessman, sharing) :-
    setting(town),
    entity(businessman),
    feature(sharing),
    has_role(businessman, businessman).

valid_story(town, reflector, sharing) :-
    setting(town),
    entity(reflector),
    feature(sharing),
    supports(reflector, sharing).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected == actual:
        print(f"OK: ASP gate matches Python gate ({len(actual)} combinations).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("Only in ASP:", sorted(actual - expected))
    print("Only in Python:", sorted(expected - actual))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    town = args.town or rng.choice(TOWNS)
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(name=name, town=town, mood=mood)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Meadowtown", "thoughtful"),
    StoryParams("Milo", "Sunbeam", "cheerful"),
    StoryParams("Nora", "Cloverfield", "patient"),
    StoryParams("Pip", "Moonbridge", "hopeful"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming story about a businessman, a reflector, and sharing."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--town", choices=TOWNS)
    parser.add_argument("--mood", choices=MOODS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return

    if args.verify:
        try:
            status = asp_verify()
        except ImportError as exc:
            print(f"ASP verification unavailable: {exc}")
            status = 1
        if status == 0:
            for params in CURATED:
                sample = generate(params)
                if not sample.story.strip():
                    print("Generated story was empty.")
                    status = 1
                    break
                if "businessman" not in sample.story.lower():
                    print("Generated story omitted businessman.")
                    status = 1
                    break
                if "reflector" not in sample.story.lower():
                    print("Generated story omitted reflector.")
                    status = 1
                    break
        raise SystemExit(status)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, params in enumerate(CURATED):
            params.seed = base_seed + i
            samples.append(generate(params))
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
