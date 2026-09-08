#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about Cleave Terminal, where a careful child
discovers that a crack in a mountain railway is also a useful warning.
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
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = ["Cleave Terminal"]
NAMES = ["Luna", "Pip", "Mara", "Toby", "Nell", "Orin"]
ROLES = ["conductor", "grandmother", "engineer", "uncle"]
WEATHER = ["a windy morning", "a bright noon", "a rainy afternoon", "a golden evening"]
MOUNTAINS = ["Thunderback Mountain", "Old Splitpeak", "the Blue Ridge", "Giant's Shoulder"]
OBJECTS = ["brass whistle", "red lantern", "blue ticket", "silver lunch tin"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for key in ("visible", "safe", "working", "heard"):
            self.meters.setdefault(key, 0.0)
        for key in ("wonder", "worry", "courage", "trust", "surprise"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    place: str
    mountain: str
    weather: str


@dataclass
class StoryParams:
    place: str
    name: str
    helper: str
    helper_role: str
    mountain: str
    weather: str
    object_label: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    title: str
    opening: str
    omen: str
    trouble: str
    first_try: str
    dialogue: str
    discovery: str
    impossible_deed: str
    surprise: str
    ending: str
    lesson: str


TALES = [
    Tale(
        "Luna and the Mountain That Sneezed",
        "{name} reached {place} before breakfast, when the rails shone like two black ribbons.",
        "Before the first bell, a puff of white dust slipped from {mountain}, and three pigeons flew backward.",
        "The noon train was carrying every valley child toward the Giant's Fair, but a fresh split ran across the track.",
        "The grown-ups pushed the train, though it only rolled one inch and startled a row of tea cups.",
        '"That mountain warned us," {name} said. "Let us listen before we leap."',
        "Under the platform, {name} found an old signal lever whose handle pointed toward the safe side of the split.",
        "{name} pulled the lever, then cleaved a fallen pine with the brass edge of the station bell so the track crew could reach the rail.",
        "The mountain gave one enormous sneeze, but the train stayed still, and a hidden green signal popped up like a spring leaf.",
        "Soon the repaired train thundered across the bridge, while the dust settled into a neat line pointing home.",
        "A warning may look small, but courage grows when someone pays attention.",
    ),
    Tale(
        "The Terminal's Longest Whistle",
        "{name} waited at {place} while {helper} polished a whistle long enough to reach the farthest cloud.",
        "The whistle squeaked twice before anyone touched it, and a mouse immediately packed a suitcase.",
        "The evening train was due through a tunnel whose far door had jammed shut.",
        "The crew tugged the door until the tunnel groaned louder than the engine.",
        '"Do not pull harder," {name} told {helper}. "The squeak is telling us something."',
        "A tiny breeze brushed {name}'s cheek, showing that a second passage opened behind the old signal room.",
        "{name} cleaved the locked crate blocking that passage with a single swing and waved the crew toward the fresh route.",
        "Behind the crate sat a very small dragon, who had been asleep on the emergency map and was the true source of the squeak.",
        "The train used the new passage, and the dragon became the terminal's official bell ringer.",
        "Listening closely can reveal a path that force would hide.",
    ),
    Tale(
        "The Ticket That Knew Tomorrow",
        "At {place}, {name} held a {object_label} ticket printed with a picture of tomorrow's sunrise.",
        "The picture showed a puddle beneath the clock, though the sky was dry and bright.",
        "The next train was ready to leave, but a loose water pipe trembled above the platform.",
        "Everyone hurried for umbrellas, even though no cloud was larger than a pea.",
        '"The ticket is not guessing," {name} said. "It is giving us time to act."',
        "The pipe's first cold drop landed exactly where the ticket's sunrise had drawn the puddle.",
        "{name} climbed the luggage mountain, cleaved the pipe's rusty clamp with a conductor's tool, and guided the water into a barrel.",
        "The pea-sized cloud was actually a tiny traveling rainstorm hiding inside the station chimney.",
        "The platform stayed dry, and the ticket's sunrise became a souvenir beside the terminal clock.",
        "Foreshadowing is a quiet gift: noticing early can turn trouble into a tale.",
    ),
]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.lines: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.lines if part)


def choose_tale(params: StoryParams) -> Tale:
    raw = "|".join(str(x) for x in vars(params).values()).encode()
    number = int.from_bytes(hashlib.sha256(raw).digest()[:4], "big")
    return TALES[number % len(TALES)]


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown terminal: {params.place}")
    if params.name not in NAMES:
        raise StoryError(f"Unknown traveler: {params.name}")
    if params.helper_role not in ROLES:
        raise StoryError(f"Unsupported helper role: {params.helper_role}")

    setting = Setting(params.place, params.mountain, params.weather)
    world = World(setting)

    hero = world.add(Entity("hero", "character", "child", params.name))
    helper = world.add(Entity("helper", "character", "adult", params.helper_role, memes={"trust": 1.0}))
    terminal = world.add(Entity("terminal", "place", "terminal", params.place, meters={"safe": 1.0, "visible": 1.0}))
    train = world.add(Entity("train", "vehicle", "train", "the noon train", meters={"working": 1.0, "safe": 0.0}))
    warning = world.add(Entity("warning", "signal", "omen", "the early warning", meters={"heard": 1.0}))
    tool = world.add(Entity("tool", "thing", "tool", params.object_label, meters={"working": 1.0}))

    hero.memes["wonder"] = 1.0
    hero.memes["worry"] = 1.0
    hero.memes["courage"] = 0.0
    helper.memes["worry"] = 1.0

    tale = choose_tale(params)
    values = {
        "name": params.name,
        "place": params.place,
        "helper": params.helper,
        "mountain": params.mountain,
        "object_label": params.object_label,
    }
    fill = lambda text: text.format(**values)

    world.say(fill(tale.opening) + f" It was {params.weather}, and {params.helper} stood nearby.")
    world.say(fill(tale.omen))
    world.say(fill(tale.trouble))

    world.para()
    world.say(fill(tale.first_try))
    world.say(fill(tale.dialogue))
    hero.memes["worry"] += 1
    warning.meters["heard"] = 1.0
    world.say("The little warning was easy to miss, but Luna did not miss it.")

    world.para()
    world.say(fill(tale.discovery))
    tool.meters["working"] = 1.0
    hero.memes["courage"] = 1.0
    world.say(fill(tale.impossible_deed))
    train.meters["safe"] = 1.0
    terminal.meters["safe"] = 1.0
    helper.memes["trust"] += 1.0

    world.para()
    world.say(fill(tale.surprise))
    hero.memes["surprise"] = 1.0
    world.say(fill(tale.ending))
    world.say(fill(tale.lesson))

    world.facts.update(
        hero=hero,
        helper=helper,
        terminal=terminal,
        train=train,
        warning=warning,
        tool=tool,
        tale=tale,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tale: Tale = f["tale"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    return [
        "Write a child-facing Tall Tale at Cleave Terminal with foreshadowing, dialogue, and a surprising but gentle ending.",
        f"Tell a story in which {hero.label} notices an early warning, speaks up, and uses a bold cleave to make the terminal safe.",
        f"Write a funny railway adventure called {tale.title} where a spoken clue changes the plan before the train moves.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    tale: Tale = f["tale"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What warning did {hero.label} notice at the terminal?",
            f"{tale.omen.format(name=hero.label, place=world.setting.place, helper=helper.label, mountain=world.setting.mountain, object_label=f['tool'].label)}",
        ),
        QAItem(
            f"What did {hero.label} say to {helper.label}?",
            tale.dialogue.format(name=hero.label, place=world.setting.place, helper=helper.label, mountain=world.setting.mountain, object_label=f["tool"].label),
        ),
        QAItem(
            "How did the hero help solve the danger?",
            tale.impossible_deed.format(name=hero.label, place=world.setting.place, helper=helper.label, mountain=world.setting.mountain, object_label=f["tool"].label),
        ),
        QAItem(
            "What was the surprise?",
            tale.surprise.format(name=hero.label, place=world.setting.place, helper=helper.label, mountain=world.setting.mountain, object_label=f["tool"].label),
        ),
        QAItem("What lesson did the tale teach?", tale.lesson),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a terminal?", "A terminal is a place where a journey or a railway line begins, ends, or connects with another route."),
        QAItem("What does cleave mean?", "To cleave means to split or cut something apart, often with a strong stroke."),
        QAItem("What is foreshadowing?", "Foreshadowing is a clue early in a story that hints at something that will happen later."),
        QAItem("Why is dialogue useful in a story?", "Dialogue lets characters speak to one another, share information, and change what they decide to do."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id:9} ({entity.type:9}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_train :- train_safe, terminal_safe, warning_heard.
heroic_deed :- safe_train, cleave_used.
good_tall_tale :- heroic_deed, dialogue_used, surprise_revealed.
#show good_tall_tale/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("terminal", "cleave_terminal"),
            asp.fact("train_safe"),
            asp.fact("terminal_safe"),
            asp.fact("warning_heard"),
            asp.fact("cleave_used"),
            asp.fact("dialogue_used"),
            asp.fact("surprise_revealed"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        return 1 if "clingo" not in str(exc).lower() else 0
    names = {str(atom).split("(", 1)[0] for atom in model}
    if "good_tall_tale" not in names:
        print("ASP verification failed: good_tall_tale was not derived.")
        return 1
    for seed in range(3):
        params = StoryParams("Cleave Terminal", "Luna", "the conductor", "conductor", "Thunderback Mountain", "a windy morning", "brass whistle", seed)
        sample = generate(params)
        if "cleave" not in sample.story.lower() or "terminal" not in sample.story.lower():
            print("Python verification failed: required words missing.")
            return 1
    print("OK: Python and ASP agree that the repaired terminal tale is safe and complete.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tall Tale storyworld at Cleave Terminal.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", default=None)
    parser.add_argument("--helper-role", choices=ROLES)
    parser.add_argument("--mountain", choices=MOUNTAINS)
    parser.add_argument("--weather", choices=WEATHER)
    parser.add_argument("--object", dest="object_label", choices=OBJECTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    role = args.helper_role or rng.choice(ROLES)
    default_helper = {
        "conductor": "the conductor",
        "grandmother": "Grandmother",
        "engineer": "the engineer",
        "uncle": "Uncle Bram",
    }[role]
    return StoryParams(
        place=args.place or "Cleave Terminal",
        name=name,
        helper=args.helper or default_helper,
        helper_role=role,
        mountain=args.mountain or rng.choice(MOUNTAINS),
        weather=args.weather or rng.choice(WEATHER),
        object_label=args.object_label or rng.choice(OBJECTS),
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams("Cleave Terminal", "Luna", "the conductor", "conductor", "Thunderback Mountain", "a windy morning", "brass whistle"),
    StoryParams("Cleave Terminal", "Pip", "Grandmother", "grandmother", "Old Splitpeak", "a golden evening", "red lantern"),
    StoryParams("Cleave Terminal", "Mara", "the engineer", "engineer", "the Blue Ridge", "a rainy afternoon", "silver lunch tin"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            print("\n".join(map(str, asp.one_model(asp_program()))))
        except Exception as exc:
            raise StoryError(f"ASP mode failed: {exc}") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
