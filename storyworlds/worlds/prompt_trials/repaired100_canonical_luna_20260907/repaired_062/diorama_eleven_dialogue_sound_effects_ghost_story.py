#!/usr/bin/env python3
"""
A gentle ghost story about an eleven-piece diorama, a mysterious sound,
and two friends who learn that a haunting may be asking for help.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"courage": 0.5, "curiosity": 0.5})
    memes: dict[str, float] = field(default_factory=lambda: {"trust": 0.0, "worry": 0.0})
    inventory: list[str] = field(default_factory=list)


@dataclass
class Diorama:
    title: str
    pieces: list[str]
    missing_piece: str
    drawer: str
    haunted: bool = False
    repaired: bool = False
    glow: float = 0.0
    meters: dict[str, float] = field(default_factory=lambda: {"completeness": 10.0})
    memes: dict[str, float] = field(default_factory=lambda: {"memory": 1.0, "sadness": 0.0})


@dataclass
class Setting:
    place: str = "the old town museum"
    description: str = "a narrow room where moonlight silvered the glass cases"


@dataclass
class StoryParams:
    place: str = "the old town museum"
    hero_name: str = "Luna"
    friend_name: str = "Theo"
    scenario_id: int = 0
    dialogue_mode: int = 0
    sound_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    title: str
    pieces: tuple[str, ...]
    missing_piece: str
    problem: str
    clue: str
    discovery: str
    repair: str
    resolution: str
    ending: str
    lesson: str


SCENARIOS = (
    Scenario(
        "The Moonlit Village",
        ("clock tower", "red house", "stone bridge", "tiny river", "owl", "baker", "lamp", "cart", "willow", "cat", "silver moon"),
        "silver moon",
        "At exactly eleven o'clock, the little clock tower inside the display began to strike, though its hands had not moved.",
        "A pale tapping came from the empty place above the village.",
        "The ghost was not trying to frighten anyone; it was looking for the moon piece that had fallen behind the case.",
        "They lifted the back panel, found the silver moon in a dusty drawer, and fastened it above the rooftops.",
        "When the moon returned, the clock gave one soft chime and the cold air became warm.",
        "Even a frightening mystery may be a lonely memory asking to be completed.",
    ),
    Scenario(
        "The Harbor in a Box",
        ("lighthouse", "sailboat", "dock", "fisher", "seagull", "barrel", "rope", "bell", "cloud", "wave", "lost lantern"),
        "lost lantern",
        "At eleven each night, a bell rang inside the harbor diorama, followed by a whisper from the dark.",
        "The whisper always came after the tiny lighthouse went dark.",
        "A keeper's ghost was searching for the lantern that had once guided a model boat home.",
        "They placed a new paper lantern beside the lighthouse and repaired its loose golden thread.",
        "The bell rang once more, and the ghost's whisper changed into a grateful sigh.",
        "Care can guide a lost memory back to shore.",
    ),
    Scenario(
        "The Winter Fair",
        ("carousel", "snowman", "child", "drummer", "blue tent", "horse", "bell", "tree", "skate", "star", "red mitten"),
        "red mitten",
        "A tiny drummer beat by itself at eleven, and frost spread across the glass.",
        "One empty hand on the child figure pointed toward the floor.",
        "The ghost belonged to a child who had lost a mitten at the fair and never found it.",
        "They tucked a red mitten beside the child and placed the missing hand back on its peg.",
        "The drummer stopped, the frost melted, and a small laugh floated through the room.",
        "A remembered kindness can warm a very old winter.",
    ),
)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, eid: str, entity: object) -> object:
        self.entities[eid] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def dialogue(mode: int, hero: Person, friend: Person) -> tuple[str, str]:
    lines = (
        (
            f'"Did you hear that?" {hero.name} whispered.',
            f'"I did," said {friend.name}. "Let us look before we run."',
        ),
        (
            f'"The sound came from the diorama," said {hero.name}.',
            f'"Then the diorama may be telling us what is wrong," replied {friend.name}.',
        ),
        (
            f'"I am frightened," {hero.name} admitted.',
            f'"So am I," said {friend.name}, "but we can be frightened and careful together."',
        ),
        (
            f'"Ghosts do not always want to hurt us," said {hero.name}.',
            f'"Perhaps this one wants to be heard," answered {friend.name}.',
        ),
    )
    return lines[mode % len(lines)]


def sound_effect(mode: int) -> str:
    effects = (
        "Tock... tock... tock...",
        "Tap, tap, tap!",
        "Whoooosh!",
        "Clink... clink...",
        "Rattle-rattle!",
    )
    return effects[mode % len(effects)]


def tell(params: StoryParams) -> World:
    if not params.hero_name.strip() or not params.friend_name.strip():
        raise StoryError("hero and friend names must not be empty")
    if params.hero_name == params.friend_name:
        raise StoryError("hero and friend must have different names")

    setting = Setting(place=params.place)
    world = World(setting)
    hero = world.add("hero", Person(params.hero_name, "young museum helper"))
    friend = world.add("friend", Person(params.friend_name, "careful visitor"))
    scenario = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    diorama = world.add(
        "diorama",
        Diorama(
            title=scenario.title,
            pieces=list(scenario.pieces),
            missing_piece=scenario.missing_piece,
            drawer="a shallow wooden drawer beneath the case",
            haunted=True,
        ),
    )

    hero.meters["curiosity"] = 0.9
    friend.meters["courage"] = 0.8
    hero.memes["worry"] = 0.4
    friend.memes["trust"] = 0.4

    world.say(
        f"At {setting.place}, Luna's friend {friend.name} stayed late to dust an eleven-piece diorama called "
        f"'{scenario.title}'."
    )
    world.say(
        f"The tiny scene held {', '.join(scenario.pieces[:-1])}, and {scenario.pieces[-1]}. "
        "Moonlight lay across the glass like a thin white road."
    )
    world.say(f"Then the museum clock pointed to eleven. {sound_effect(params.sound_mode)}")
    world.say(scenario.problem)

    world.para()
    first, second = dialogue(params.dialogue_mode, hero, friend)
    world.say(first)
    world.say(second)
    world.say(f"They listened again. {sound_effect((params.sound_mode + 1) % 5)}")
    world.say(f"{scenario.clue} {scenario.discovery}")
    world.events.extend(["midnight_sound", "dialogue_started", "clue_found"])

    world.para()
    world.say(f"{hero.name} held the flashlight while {friend.name} carefully opened {diorama.drawer}.")
    world.say(f"Behind an old label, they found the {scenario.missing_piece}.")
    world.say(f'"There you are," said {hero.name}.')
    world.say(f'"Let us put you back where you belong," said {friend.name}.')
    world.say(scenario.repair)

    diorama.pieces.append(diorama.missing_piece)
    diorama.repaired = True
    diorama.haunted = False
    diorama.glow = 1.0
    diorama.meters["completeness"] = 11.0
    diorama.memes["sadness"] = 0.0
    hero.meters["courage"] = 1.0
    friend.meters["courage"] = 1.0
    hero.memes["worry"] = 0.0
    friend.memes["trust"] = 1.0
    world.events.extend(["missing_piece_found", "diorama_repaired", "ghost_reassured"])

    world.para()
    world.say(scenario.resolution)
    world.say(f"{hero.name} and {friend.name} stood quietly until the last little sound faded.")
    endings = (
        f"By morning, {scenario.ending}",
        f"The museum grew peaceful again. {scenario.ending}",
        f"Before they left, {scenario.ending}",
        f"From then on, every visitor could see that {scenario.ending}",
    )
    world.say(endings[params.ending_mode % len(endings)])
    world.say(f"They both understood the lesson: {scenario.lesson}")

    world.facts.update(
        hero=hero,
        friend=friend,
        diorama=diorama,
        scenario=scenario,
        problem=scenario.problem,
        clue=scenario.clue,
        discovery=scenario.discovery,
        repair=scenario.repair,
        resolution=scenario.resolution,
        ending=scenario.ending,
        lesson=scenario.lesson,
        missing_piece=scenario.missing_piece,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story about an eleven-piece diorama called '{f['diorama'].title}'.",
        f"Describe how the characters solve this haunting: {f['problem']}",
        f"Use dialogue and a sound effect to reveal that {f['discovery']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Person = f["hero"]
    friend: Person = f["friend"]
    return [
        QAItem(
            question=f"What happened at eleven in the museum?",
            answer=f"At eleven, {f['problem']}",
        ),
        QAItem(
            question=f"What clue helped {hero.name} and {friend.name} understand the ghost?",
            answer=f"The clue was that {f['clue']} It showed them that {f['discovery']}",
        ),
        QAItem(
            question=f"How did the two friends repair the diorama?",
            answer=f"They found the {f['missing_piece']} and {f['repair']}",
        ),
        QAItem(
            question="What changed after the missing piece was returned?",
            answer=f"The haunting ended peacefully: {f['resolution']}",
        ),
        QAItem(
            question="What lesson did the friends learn?",
            answer=f"They learned that {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a diorama?",
            answer="A diorama is a small three-dimensional scene arranged inside a box or display case.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a spirit or strange haunting, often with a mystery to solve.",
        ),
        QAItem(
            question="Why can dialogue help a story?",
            answer="Dialogue lets characters exchange knowledge, feelings, and decisions in their own words.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are written or spoken sounds, such as 'Tap, tap!' or 'Whoooosh!', that help readers imagine an event.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
complete(D) :- diorama(D), repaired(D).
quiet(D) :- complete(D), not haunted(D).
helped(H,F) :- hero(H), friend(F), repaired(diorama).
brave(H) :- hero(H), helped(H,_,).
brave(F) :- friend(F), helped(_,F).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("diorama", "diorama"),
            asp.fact("hero", "hero"),
            asp.fact("friend", "friend"),
            asp.fact("repaired", "diorama"),
        ]
    )


def asp_program(show: str = "#show complete/1. #show quiet/1. #show helped/2. #show brave/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Eleven-piece diorama ghost story world.")
    parser.add_argument("--place", default=None)
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
        place=args.place or rng.choice(["the old town museum", "the moonlit library", "the village gallery"]),
        hero_name=rng.choice(["Luna", "Mara", "Nell", "Ivy"]),
        friend_name=rng.choice(["Theo", "Sam", "Robin", "Jules"]),
        scenario_id=rng.randrange(len(SCENARIOS)),
        dialogue_mode=rng.randrange(4),
        sound_mode=rng.randrange(5),
        ending_mode=rng.randrange(4),
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


def dump_trace(world: World) -> str:
    hero: Person = world.entities["hero"]
    friend: Person = world.entities["friend"]
    diorama: Diorama = world.entities["diorama"]
    return "\n".join(
        [
            "--- world trace ---",
            f"place: {world.setting.place}",
            f"hero: {hero.name} meters={hero.meters} memes={hero.memes}",
            f"friend: {friend.name} meters={friend.meters} memes={friend.memes}",
            f"diorama: title={diorama.title!r} pieces={len(diorama.pieces)} repaired={diorama.repaired} haunted={diorama.haunted}",
            f"events: {world.events}",
        ]
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


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    expected = {
        ("diorama",),
    }
    if set(asp.atoms(model, "complete")) != expected:
        print("MISMATCH: ASP did not derive a complete diorama.")
        return 1
    if ("hero", "friend") not in set(asp.atoms(model, "helped")):
        print("MISMATCH: ASP did not derive teamwork.")
        return 1
    sample = generate(
        StoryParams(
            place="the old town museum",
            hero_name="Luna",
            friend_name="Theo",
            scenario_id=0,
            seed=1,
        )
    )
    if "diorama" not in sample.story.lower() or "eleven" not in sample.story.lower():
        print("MISMATCH: generated story lacks required domain facts.")
        return 1
    if not sample.world.facts["diorama"].repaired:
        print("MISMATCH: Python world was not repaired.")
        return 1
    print("OK: ASP and Python parity verified.")
    return 0


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
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program())
        print("complete:", asp.atoms(model, "complete"))
        print("quiet:", asp.atoms(model, "quiet"))
        print("helped:", asp.atoms(model, "helped"))
        print("brave:", asp.atoms(model, "brave"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(place="the old town museum", hero_name="Luna", friend_name="Theo", scenario_id=i, seed=base_seed)
            for i in range(len(SCENARIOS))
        ]
        samples = [generate(params) for params in params_list]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + i)))
            for i in range(max(1, args.n))
        ]

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
