#!/usr/bin/env python3
"""
Standalone story world: a tiny insect, a vintage object, and a moral made real.

A fairy-tale simulation about Luna, a careful young beetle, who finds a vintage
brass music box. Its sound effects awaken a materialized moral value: honesty
becomes a visible golden thread. The story's state changes through speaking,
choosing, and repairing rather than through a fixed paragraph.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
    detail: str


@dataclass
class StoryParams:
    hero_name: str
    companion_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


SETTING = Setting(
    place="the moonlit glasshouse",
    detail="a forgotten glasshouse where silver vines curled around cracked shelves",
)

NAMES = ["Luna", "Pip", "Clover", "Mira", "Tansy", "Nell", "Bram", "Dew"]
COMPANIONS = ["Moth", "Bumble", "Wren", "Sable", "Flicker", "Poppy", "Thimble"]

QUESTS = [
    {
        "id": "music_box",
        "object": "a vintage brass music box",
        "sound": "Ting-ting! Whirr-whirr!",
        "appearance": "its lid shone like a little sun beneath the dust",
        "temptation": "hide it beneath a leaf and call it her treasure",
        "owner": "the old gardener who had once kept the glasshouse bright",
        "proof": "a faded name card tucked under its velvet lining",
        "repair": "polished the brass, rewound the spring, and carried it to the gardener's cottage",
        "ending": "the music box played beside the gardener's teacup while moonlight danced on its lid",
        "moral": "Honesty may cost a little at first, but it returns a greater treasure: trust.",
    },
    {
        "id": "silver_thimble",
        "object": "a vintage silver thimble",
        "sound": "Clink-clink! Tink!",
        "appearance": "it glittered like a tiny helmet in a nest of moss",
        "temptation": "wear it as a crown and pretend the glasshouse had chosen her",
        "owner": "the seamstress who lived beyond the rosemary wall",
        "proof": "three blue threads still caught inside its rim",
        "repair": "followed the thread trail and returned the thimble before the seamstress finished her evening dress",
        "ending": "the thimble rested on the seamstress's finger as she stitched a bright pocket for Luna",
        "moral": "A beautiful find becomes more beautiful when it is returned to the one who needs it.",
    },
    {
        "id": "tin_lantern",
        "object": "a vintage tin lantern",
        "sound": "Click! Fuff! Hummm!",
        "appearance": "its star-shaped holes sprinkled the floor with pale dots",
        "temptation": "claim it as a palace lamp and leave the dark path unlit",
        "owner": "the night watchman who guarded every small creature",
        "proof": "a brass badge bearing the watchman's crescent mark",
        "repair": "told the watchman where she found it and helped carry it back to the gate",
        "ending": "the lantern glowed over the gate while safe golden stars appeared on the path",
        "moral": "Keeping what belongs to everyone can leave the whole community in the dark.",
    },
    {
        "id": "wooden_whistle",
        "object": "a vintage wooden whistle",
        "sound": "Peep! Peep-peep!",
        "appearance": "its carved bird looked ready to flutter from the handle",
        "temptation": "blow it loudly and make every creature obey her call",
        "owner": "the meadow shepherd who used it to guide lost lambs",
        "proof": "a small painted lamb matched the shepherd's blue cloak",
        "repair": "carried it across the clover field and gave it back before dusk",
        "ending": "the shepherd blew one gentle note, and the flock came home in a soft woolly wave",
        "moral": "A gift has its proper purpose, and respecting that purpose is a form of kindness.",
    },
]

OPENINGS = [
    "At the first silver hour of evening, {hero} went searching for fallen petals.",
    "When the moon rose over the garden wall, {hero} followed a trail of blue moth dust.",
    "On a night when the roses held drops of light, {hero} crept into the old glasshouse.",
    "Before the fireflies began their lantern dance, {hero} promised to tidy the forgotten shelves.",
]

REFLECTIONS = [
    '"The shine made me want to keep it," {hero} confessed. "The truth helped me see whom it belonged to."',
    '{companion} nodded. "A small creature can make a large promise, and keep it."',
    '{hero} watched the golden thread fade into warm light. "Now I know that goodness is not only a word."',
    'They agreed that a treasure was safest when it rested with the one who could use it well.',
]


ASP_RULES = r"""
found(X,O) :- discovers(X,O).
tempted(X,O) :- found(X,O), desires(X,O).
honest(X,O) :- found(X,O), speaks_truth(X,O), returns(X,O).
moral_value(honesty) :- honest(_, _).
materialized(honesty) :- moral_value(honesty), hears_sound(_, _).
valid_story(X) :- honest(X,_), materialized(honesty).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("character", "luna"),
            asp.fact("character", "companion"),
            asp.fact("insect", "luna"),
            asp.fact("vintage", "treasure"),
            asp.fact("discovers", "luna", "treasure"),
            asp.fact("desires", "luna", "treasure"),
            asp.fact("speaks_truth", "luna", "treasure"),
            asp.fact("returns", "luna", "treasure"),
            asp.fact("hears_sound", "companion", "treasure"),
            asp.fact("feature", "moral_value"),
            asp.fact("feature", "sound_effects"),
        ]
    )


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    quest = rng.choice(QUESTS)
    opening = rng.choice(OPENINGS)
    reflection = rng.choice(REFLECTIONS)
    world = World(SETTING)

    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type="insect",
            label="small beetle",
            meters={"distance": 0.0, "brightness": 0.0},
            memes={"curiosity": 1.0, "greed": 0.0, "honesty": 0.0, "courage": 0.0, "relief": 0.0},
        )
    )
    companion = world.add(
        Entity(
            id=params.companion_name,
            kind="character",
            type="moth",
            label="silver moth",
            meters={"distance": 0.0},
            memes={"friendship": 1.0, "wisdom": 1.0, "worry": 0.0},
        )
    )
    treasure = world.add(
        Entity(
            id="treasure",
            type="vintage_object",
            label=quest["object"],
            meters={"dust": 1.0, "working": 0.0},
            memes={"mystery": 1.0, "belonging": 0.0},
        )
    )
    thread = world.add(
        Entity(
            id="golden_thread",
            type="moral_value",
            label="a golden thread of honesty",
            meters={"glow": 0.0},
            memes={"truth": 0.0, "trust": 0.0},
        )
    )
    world.facts.update(
        hero=hero,
        companion=companion,
        treasure=treasure,
        thread=thread,
        quest=quest,
        opening=opening,
        reflection=reflection,
        discovered=False,
        truth_told=False,
        returned=False,
        moral_materialized=False,
    )
    return world


def validate_world(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    quest = world.facts["quest"]
    if hero.id == companion.id:
        raise StoryError("The insect and companion must have different names.")
    if not quest["object"].startswith("a vintage"):
        raise StoryError("Every quest must contain a vintage material object.")
    if not quest["sound"]:
        raise StoryError("Every vintage object needs a sound effect.")


def tell_beginning(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    quest = world.facts["quest"]
    world.say(world.facts["opening"].format(hero=hero.id))
    world.say(
        f"{hero.id} was a tiny insect with bright black eyes, and {companion.id} was a silver moth "
        f"who knew every whisper of {world.setting.place}. {world.setting.detail.capitalize()}."
    )
    world.say(
        f"Under a crooked shelf, {hero.id} found {quest['object']}. "
        f"{quest['appearance'].capitalize()}."
    )
    world.say(f"{quest['sound']} The old object gave a shivery little song.")
    hero.meters["brightness"] += 1
    world.facts["discovered"] = True


def tell_temptation(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    quest = world.facts["quest"]
    hero.memes["greed"] += 1
    world.say(
        f"{hero.id} imagined that the treasure might belong to her. She planned to "
        f"{quest['temptation']}."
    )
    world.say(
        f'"It is lovely," said {companion.id}, "but lovely things can still belong to someone else."'
    )
    world.say(
        f'"How can we know?" asked {hero.id}. "{quest["proof"].capitalize()}."'
    )
    world.say(
        f'"Then we must follow the clue," said {companion.id}. "A true treasure leaves a true trail."'
    )
    world.facts["proof"] = quest["proof"]


def tell_turn(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    treasure = world.facts["treasure"]
    thread = world.facts["thread"]
    quest = world.facts["quest"]

    hero.memes["greed"] = max(0.0, hero.memes["greed"] - 1.0)
    hero.memes["honesty"] += 1.0
    hero.memes["courage"] += 1.0
    treasure.meters["dust"] = 0.0
    treasure.meters["working"] = 1.0
    treasure.memes["belonging"] = 1.0
    world.say(
        f"{hero.id} brushed away the dust and discovered {quest['proof']}. "
        f"She understood that the treasure had a story before it had caught her eye."
    )
    world.say(
        f'"I found this, and it is not mine," {hero.id} said clearly. '
        f'"I will return it."'
    )
    world.say(
        f"{companion.id} fluttered in a happy circle. {quest['sound']} "
        "This time the sound seemed to answer her honest words."
    )
    thread.meters["glow"] = 1.0
    thread.memes["truth"] = 1.0
    thread.memes["trust"] = 1.0
    world.say(
        "From the music curled a golden thread. It floated through the air, "
        "then became a small shining ribbon between the two friends."
    )
    world.facts["truth_told"] = True
    world.facts["moral_materialized"] = True


def tell_resolution(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    quest = world.facts["quest"]

    hero.memes["honesty"] += 1.0
    hero.memes["relief"] += 1.0
    world.say(
        f"Following the golden thread, {hero.id} {quest['repair']}. "
        f"The rightful owner welcomed the vintage treasure with grateful hands."
    )
    world.say(world.facts["reflection"].format(hero=hero.id, companion=companion.id))
    world.say(
        f"{quest['moral']} "
        f"At last, {quest['ending']}. "
        f"{hero.id} and {companion.id} returned to the glasshouse with lighter hearts."
    )
    world.facts["returned"] = True
    world.facts["ending"] = quest["ending"]
    world.facts["moral"] = quest["moral"]


def generate_story_world(params: StoryParams) -> World:
    world = build_world(params)
    validate_world(world)
    tell_beginning(world)
    tell_temptation(world)
    tell_turn(world)
    tell_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    quest = world.facts["quest"]
    return [
        "Write a gentle Fairy Tale about an insect who finds a vintage treasure and learns a moral value.",
        f"Show how {hero.id} hears the sound effects of {quest['object']} and chooses honesty instead of ownership.",
        f"Materialize the moral value as a golden thread, then end with {quest['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    quest = world.facts["quest"]
    return [
        QAItem(
            question=f"What did {hero.id} discover in the glasshouse?",
            answer=f"{hero.id} discovered {quest['object']}, a vintage treasure whose sound effects made the discovery feel magical."
        ),
        QAItem(
            question=f"Why did {hero.id} first want to keep the object?",
            answer=f"{hero.id} wanted to keep it because {quest['temptation']}. Its shine and music made ownership tempting."
        ),
        QAItem(
            question=f"What clue helped {hero.id} learn whom the treasure belonged to?",
            answer=f"The clue was that {quest['proof']}. This connected the vintage object to its rightful owner."
        ),
        QAItem(
            question=f"What did {companion.id} tell {hero.id} to do?",
            answer=f"{companion.id} told {hero.id} to follow the true clue and return the object rather than keep something that belonged to someone else."
        ),
        QAItem(
            question="How did the moral value become material?",
            answer="When the insect honestly promised to return the treasure, a golden thread curled out of its music and became a shining ribbon. Honesty was made visible."
        ),
        QAItem(
            question=f"How was the vintage treasure repaired or returned?",
            answer=f"{hero.id} {quest['repair']}. The action brought the object back to the person who could use it."
        ),
        QAItem(
            question="What moral did the Fairy Tale teach?",
            answer=quest["moral"]
        ),
        QAItem(
            question="What changed at the ending?",
            answer=f"The treasure was with its rightful owner, and {quest['ending']}. The insect returned home with trust and relief instead of secret greed."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an insect?",
            answer="An insect is a small animal with six legs, a body divided into parts, and often wings or feelers."
        ),
        QAItem(
            question="What does vintage mean?",
            answer="Vintage describes an older object valued for its history, style, or careful workmanship."
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a principle that helps someone choose a kind, fair, or honest action."
        ),
        QAItem(
            question="Why can sound effects help a fairy tale?",
            answer="Sound effects make a magical event easier to imagine and can show that the world is responding to a character's choice."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_verify() -> int:
    if not asp_valid():
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import asp

        model = asp.one_model(asp_program())
        valid = asp.atoms(model, "valid_story")
    except Exception as exc:
        print(f"MISMATCH: ASP verification failed: {exc}")
        return 1
    if not valid:
        print("MISMATCH: ASP found no valid story.")
        return 1
    sample = generate(StoryParams("Luna", "Moth", seed=7))
    if not sample.story or "golden thread" not in sample.story:
        print("MISMATCH: generated story did not exercise the moral turn.")
        return 1
    print("OK: Python and ASP story gates pass; generated story exercised.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Fairy Tale world about an insect, a vintage treasure, and a materialized moral."
    )
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--companion-name", choices=COMPANIONS)
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
    hero = args.hero_name or rng.choice(NAMES)
    choices = [name for name in COMPANIONS if name != hero]
    companion = args.companion_name or rng.choice(choices)
    if hero == companion:
        raise StoryError("Hero and companion names must differ.")
    return StoryParams(hero_name=hero, companion_name=companion)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {entity.id:14} ({entity.type:14}) {' '.join(parts)}")
    lines.append(f"  discovered={world.facts['discovered']}")
    lines.append(f"  truth_told={world.facts['truth_told']}")
    lines.append(f"  moral_materialized={world.facts['moral_materialized']}")
    lines.append(f"  returned={world.facts['returned']}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} compatible stories:")
        for value in values:
            print(f"  {value}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            ("Luna", "Moth"),
            ("Clover", "Bumble"),
            ("Mira", "Wren"),
            ("Tansy", "Sable"),
        ]
        samples = [
            generate(StoryParams(hero, companion, seed=base_seed + i))
            for i, (hero, companion) in enumerate(presets)
        ]
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1
            if index > target * 100:
                raise StoryError("Could not produce enough distinct story variants.")

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
