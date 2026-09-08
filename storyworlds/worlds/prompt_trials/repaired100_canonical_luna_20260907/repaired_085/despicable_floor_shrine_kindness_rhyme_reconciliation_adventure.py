#!/usr/bin/env python3
"""A child-safe adventure about repairing a neglected floor shrine."""

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
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("dust", "damage", "risk", "distance"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "hope", "kindness", "trust", "joy"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.events.append(line)

    def render(self) -> str:
        return " ".join(self.events)


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    shrine_name: str
    token: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Quest:
    name: str
    neglect: str
    clue: str
    obstacle: str
    task: str
    rhyme: str
    repair: str
    ending: str
    lesson: str


QUESTS = [
    Quest(
        "the dusty lantern",
        "dust covered the little floor shrine, and its lantern would not shine",
        "a clean crescent on the floor showed where a kindness token had recently rested",
        "a loose stair plank blocked the shortest path",
        "crossed the old hall by stepping only on the marked stones",
        "Kind hands clear the way; bright hearts save the day.",
        "swept the shrine, mended the lantern, and placed the token where every traveler could see it",
        "the lantern cast a warm star across the polished floor",
        "A place can look despicable when it is neglected, but care can begin its repair.",
    ),
    Quest(
        "the cracked bowl",
        "the shrine's blue offering bowl was cracked and ringed with mud",
        "a trail of tiny blue beads led from the bowl toward the garden gate",
        "rainwater had turned the flagstones into a slippery maze",
        "followed the bead trail with a rope between them",
        "Step with care, show kindness there; repair can turn despair to fair.",
        "washed the bowl, gathered the beads, and set a dry stone beneath it",
        "the shrine reflected the evening sky while the garden gate clicked shut",
        "Reconciliation starts when people protect what both sides value.",
    ),
    Quest(
        "the fallen ribbon",
        "a faded ribbon lay beneath the shrine, tangled with weeds and leaves",
        "one stitched word, welcome, remained bright on the ribbon",
        "a gust had scattered the shrine's small markers across the courtyard",
        "retrieved each marker without stepping on the painted path",
        "Find what is lost, whatever the cost; kindness shows no one is lost.",
        "tied the ribbon above the shrine and returned the markers in a careful circle",
        "children followed the circle to leave notes of thanks for one another",
        "Listening for a welcoming message can mend a quarrel better than blame.",
    ),
    Quest(
        "the silent bell",
        "the shrine bell had gone silent beneath a blanket of grit",
        "a tiny clapper rested beside a footprint pointing toward the market wall",
        "a crowded cart had rolled across the passage",
        "asked the cart keeper to help move it before searching",
        "Ask, then mend; make peace your friend.",
        "cleaned the bell and thanked the cart keeper for moving the cart",
        "one clear chime crossed the courtyard, and two former arguers smiled",
        "Kindness makes room for reconciliation.",
    ),
]


HEROES = ["Luna", "Mara", "Tavi", "Nell", "Pip", "Sora"]
COMPANIONS = ["Bram", "Iris", "Jo", "Kian", "Milo", "Rhea"]
TOKENS = ["a carved moon", "a green bead", "a copper leaf", "a painted pebble"]
SHRINES = ["the Wayfarer's Shrine", "the Little Lantern Shrine", "the Courtyard Shrine"]


def choose_quest(seed: Optional[int]) -> Quest:
    if seed is None:
        return QUESTS[0]
    return QUESTS[seed % len(QUESTS)]


def validate(params: StoryParams) -> None:
    if params.hero == params.companion:
        raise StoryError("The hero and companion must have different names.")
    if not params.place.strip():
        raise StoryError("The shrine needs a named place.")
    if not params.token.strip():
        raise StoryError("The kindness token cannot be empty.")


def tell_story(params: StoryParams) -> World:
    validate(params)
    quest = choose_quest(params.seed)
    world = World(params.place)

    hero = world.add(Entity(params.hero, "character", "young adventurer", params.hero))
    companion = world.add(Entity(params.companion, "character", "helpful companion", params.companion))
    shrine = world.add(Entity("shrine", "place", "floor shrine", params.shrine_name))
    token = world.add(Entity("token", "object", "kindness token", params.token, owner=params.hero))
    floor = world.add(Entity("floor", "place", "stone floor", "old courtyard floor"))

    hero.memes.update(worry=0.5, hope=0.7)
    companion.memes.update(worry=0.4, trust=0.7)
    shrine.meters.update(dust=0.9, damage=0.7, risk=0.4)
    floor.meters.update(dust=0.5, risk=0.3)

    world.say(f"At the edge of {params.place}, {params.hero} found {params.shrine_name} on the old floor.")
    world.say(f"It looked despicable: {quest.neglect}.")
    world.say(f"{params.companion} arrived with {params.token} tucked in a cloth pouch.")
    world.say(
        f'"Someone must have forgotten this place," {params.hero} said. '
        f'"Maybe someone simply needs a chance to make it right," {params.companion} replied.'
    )
    world.say(f"Then {params.hero} noticed that {quest.clue}.")
    world.say(f'"The clue gives us a path," said {params.hero}. "We will not rush into danger."')
    world.say(f"Their first challenge was that {quest.obstacle}.")
    world.say(f"Together they {quest.task}, while {params.companion} called out each safe step.")
    world.say(f"At the shrine, {params.hero} spoke the rhyme: “{quest.rhyme}”")
    world.say(f"The rhyme made them laugh, but it also gave them courage to work gently.")
    world.say(f"They {quest.repair}.")
    world.say(
        f"A caretaker named Eda appeared from the market wall. "
        f'"I thought you were here to scold me," Eda said. '
        f'"We came to help, not blame," {params.companion} answered.'
    )
    world.say(
        f"Eda admitted that she had left the shrine untended while caring for a sick neighbor. "
        f"{params.hero} offered the {params.token}, and Eda promised to tend the shrine with them."
    )
    world.say(f"This reconciliation changed the courtyard: {quest.ending}.")
    world.say(f"{quest.lesson} {params.hero} and {params.companion} left with dusty hands and peaceful hearts.")

    hero.memes.update(worry=0.0, hope=1.0, kindness=1.0, joy=1.0)
    companion.memes.update(worry=0.0, trust=1.0, kindness=1.0)
    shrine.meters.update(dust=0.0, damage=0.1, risk=0.0)
    floor.meters.update(dust=0.1, risk=0.0)

    world.facts.update(
        quest=quest,
        hero=hero,
        companion=companion,
        shrine=shrine,
        token=token,
        floor=floor,
        reconciled=True,
        safe=True,
        features=["kindness", "rhyme", "reconciliation"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    quest: Quest = world.facts["quest"]
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    return [
        'Write a child-safe adventure using the words "despicable," "floor," and "shrine."',
        f"Tell how {hero.label} and {companion.label} repair {quest.name} through kindness and reconciliation.",
        f"Include a spoken rhyme: “{quest.rhyme}” and make it help the adventurers continue safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    quest: Quest = world.facts["quest"]
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    token: Entity = world.facts["token"]
    return [
        QAItem(
            "Where did the adventure begin?",
            f"It began at {world.place}, where {hero.label} found {world.facts['shrine'].label} on an old floor.",
        ),
        QAItem(
            "Why did the shrine look despicable?",
            f"It looked despicable because {quest.neglect}.",
        ),
        QAItem(
            f"How did {hero.label} and {companion.label} handle the obstacle?",
            f"They {quest.task}, choosing a careful route instead of taking an unsafe shortcut.",
        ),
        QAItem(
            "What did the rhyme do?",
            f"The rhyme, “{quest.rhyme}” gave them courage and reminded them to use kindness while repairing the shrine.",
        ),
        QAItem(
            "How did reconciliation change the ending?",
            "The caretaker explained why the shrine had been neglected, and the adventurers offered help instead of blame. They agreed to care for it together.",
        ),
        QAItem(
            "What happened to the kindness token?",
            f"{hero.label} offered {token.label} to the caretaker, and it became part of the renewed shrine.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a shrine?",
            "A shrine is a small place set aside for remembering, welcoming, or showing respect. People should treat it gently.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is the work of repairing trust after a disagreement or hurt. Listening, apologizing, and helping can support it.",
        ),
        QAItem(
            "Why is kindness useful during an adventure?",
            "Kindness helps people cooperate, notice who needs help, and solve problems without creating new ones.",
        ),
        QAItem(
            "What is a rhyme?",
            "A rhyme is a pattern of words with similar sounds, often used in songs, poems, and memorable sayings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *sample.prompts, "", "== story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"place: {world.place}"]
    for entity in world.entities.values():
        meters = {key: round(value, 2) for key, value in entity.meters.items() if value}
        memes = {key: round(value, 2) for key, value in entity.memes.items() if value}
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"quest: {world.facts['quest'].name}")
    lines.append("reconciled: true")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adventure storyworld about a repaired floor shrine.")
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
    hero = rng.choice(HEROES)
    companion = rng.choice([name for name in COMPANIONS if name != hero])
    return StoryParams(
        place="Moonbridge Courtyard",
        hero=hero,
        companion=companion,
        shrine_name=rng.choice(SHRINES),
        token=rng.choice(TOKENS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


ASP_RULES = r"""
place(moonbridge_courtyard).
theme(despicable).
theme(floor).
theme(shrine).
feature(kindness).
feature(rhyme).
feature(reconciliation).
style(adventure).
safe_path :- place(moonbridge_courtyard), feature(kindness).
repaired_shrine :- theme(shrine), feature(reconciliation), safe_path.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("place", "moonbridge_courtyard"),
        asp.fact("theme", "despicable"),
        asp.fact("theme", "floor"),
        asp.fact("theme", "shrine"),
        asp.fact("feature", "kindness"),
        asp.fact("feature", "rhyme"),
        asp.fact("feature", "reconciliation"),
        asp.fact("style", "adventure"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        symbols = asp.one_model(
            asp_program(
                "#show safe_path/0.\n#show repaired_shrine/0."
            )
        )
        names = {symbol.name for symbol in symbols}
        expected = {"safe_path", "repaired_shrine"}
        if not expected.issubset(names):
            return 1
    except Exception:
        return 1

    params = StoryParams(
        place="Moonbridge Courtyard",
        hero="Luna",
        companion="Bram",
        shrine_name="the Wayfarer's Shrine",
        token="a carved moon",
        seed=0,
    )
    sample = generate(params)
    required = ("despicable", "floor", "shrine", "kindness", "rhyme", "reconciliation")
    if not all(word in sample.story.lower() for word in required):
        return 1
    if not sample.world or not sample.world.facts.get("reconciled"):
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program("#show safe_path/0.\n#show repaired_shrine/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams("Moonbridge Courtyard", "Luna", "Bram", SHRINES[0], TOKENS[0], seed=index)
            for index in range(len(QUESTS))
        ]
    else:
        params_list = []
        for offset in range(max(1, args.n)):
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            params_list.append(params)

    samples = [generate(params) for params in params_list]

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
