#!/usr/bin/env python3
"""A gentle bedtime storyworld about a pound, a clarinet, and a magical trap."""

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
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("weight", "sound", "danger", "warmth", "distance"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "wonder", "trust", "calm", "joy"):
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

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


@dataclass
class StoryParams:
    place: str
    child: str
    companion: str
    bedtime_object: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    title: str
    opening: str
    trap_clue: str
    false_guess: str
    safe_test: str
    magic_rule: str
    repair: str
    ending: str
    lesson: str


TALES = [
    Tale(
        "The Moonlit Pound",
        "At bedtime, the moon painted a silver path across the quiet garden.",
        "three round marks beside the old pound stone",
        "the moon had dropped a heavy coin there",
        "counted the marks from the porch without stepping into the dark grass",
        "the pound stone opened only when a kind song was played and no one reached for a hidden prize",
        "played one soft clarinet note while the grown-up lifted the loose garden board",
        "the marks belonged to a hedgehog, and the pound stone became a warm seat for morning tea",
        "Magic is safest when wonder waits for careful hands.",
    ),
    Tale(
        "The Clarinet Under the Quilt",
        "The house was settling for sleep when a tiny melody curled from the blanket basket.",
        "a brass glimmer and a little trapdoor beneath the quilt",
        "a fairy had hidden a treasure under the bed",
        "listened from the doorway and checked the floorboards with a lamp",
        "the clarinet could wake the quilt's stars, but only a gentle player could close the trap",
        "held the clarinet steady while the child played three quiet notes",
        "the trapdoor shut, the stars rested, and the melody became a sleepy hum",
        "A soft question can turn a frightening surprise into a safe discovery.",
    ),
    Tale(
        "The Pound of Starlight",
        "Before the last good-night kiss, a blue spark winked beside the pillow.",
        "a small silver trap marked with a pound sign",
        "the spark was a button that must be pressed",
        "placed a book beside it as a boundary and asked the night nurse for help",
        "the magic trap gathered wishes that were spoken kindly, but it snapped at greedy fingers",
        "the companion played a lullaby on the clarinet while the child named one grateful wish",
        "the trap changed into a night-light and no one was pinched",
        "Wonder grows brighter when kindness leads and curiosity follows.",
    ),
    Tale(
        "The Quiet Pound Bell",
        "Rain whispered on the roof while the bedroom waited for its story.",
        "a pound-shaped shadow beneath the window",
        "a giant creature was tapping outside",
        "looked through the curtain with a trusted companion instead of opening the window",
        "the shadow vanished when a clarinet note matched the rain's rhythm",
        "closed the curtain, moved the lamp, and played from the safe side of the room",
        "the shadow became a coat on a peg, and the room felt ordinary again",
        "A careful check can make a scary shape small.",
    ),
    Tale(
        "The Trap at Pillow Hill",
        "The bedtime blanket rose like a hill, and something shiny blinked at its peak.",
        "a brass trap hidden in the blanket fold",
        "the shiny thing was a crown to grab quickly",
        "used a wooden ruler to lift the fold while staying beside the bed",
        "the trap opened into a pocket of stars only for someone who shared the music",
        "let the companion hold the ruler and played the clarinet softly",
        "the stars floated into a jar, and the blanket settled without a snap",
        "Sharing the work makes magic gentler.",
    ),
]


CHILDREN = ["Luna", "Milo", "Nora", "Ari", "Pia", "Theo"]
COMPANIONS = ["Grandma", "Papa", "Aunt Mira", "Uncle Sol", "Mama", "Baba"]
OBJECTS = ["blue blanket", "wooden moon", "star pillow", "silver night-light"]
PLACES = ["the moonlit bedroom", "the little house at the garden edge", "the attic bedroom", "the room beneath the round window"]


def choose_tale(seed: Optional[int]) -> Tale:
    if seed is None:
        return TALES[0]
    return TALES[seed % len(TALES)]


def build_world(params: StoryParams) -> World:
    if params.ending not in {"bad", "safe"}:
        raise StoryError("ending must be either 'bad' or 'safe'")
    if params.child == params.companion:
        raise StoryError("the child and companion must be different characters")

    tale = choose_tale(params.seed)
    world = World(place=params.place)

    child = world.add(Entity(
        id="child",
        kind="character",
        type="sleepy child",
        label=params.child,
        memes={"worry": 0.45, "wonder": 0.8, "trust": 0.7},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type="trusted companion",
        label=params.companion,
        memes={"calm": 0.9, "trust": 0.9},
    ))
    clarinet = world.add(Entity(
        id="clarinet",
        kind="instrument",
        type="clarinet",
        label="small clarinet",
        owner=companion.id,
        meters={"sound": 0.35, "warmth": 0.2},
    ))
    trap = world.add(Entity(
        id="trap",
        kind="object",
        type="magic trap",
        label="brass trap",
        meters={"danger": 0.8, "weight": 1.0},
        memes={"worry": 0.7, "wonder": 0.9},
    ))
    pound = world.add(Entity(
        id="pound",
        kind="symbol",
        type="pound mark",
        label="pound sign",
        meters={"weight": 0.2},
    ))

    world.facts.update(
        tale=tale,
        child=child,
        companion=companion,
        clarinet=clarinet,
        trap=trap,
        pound=pound,
        resolved=params.ending == "safe",
        ending=params.ending,
        safe_choice=params.ending == "safe",
    )

    world.say(tale.opening)
    world.say(f"In {params.place}, {params.child} tucked the {params.bedtime_object} close and noticed {tale.trap_clue}.")
    world.say(f'"Could it be a treasure trap?" {params.child} whispered.')
    world.say(f'"It might be magic, but we will not touch it yet," said {params.companion}. "Tell me what you see."')
    world.say(f"{params.child} described the clue: {tale.trap_clue}. The pound-shaped mark made the mystery seem important.")
    world.say(f'"My first guess is that {tale.false_guess}," said {params.child}.')
    world.say(f'"A guess is only a beginning," replied {params.companion}. "Let us use a safe test: we will {tale.safe_test}."')

    if params.ending == "safe":
        world.say(f"They followed the rule of the magic: {tale.magic_rule}.")
        world.say(f"The companion lifted the clarinet, and {params.child} helped from the safe side. Together they {tale.repair}.")
        world.say(f"The trap gave a quiet click instead of a snap. {tale.ending}.")
        world.say(f'"{tale.lesson}" {params.child} said.')
        child.memes.update(worry=0.0, calm=1.0, joy=0.9)
        companion.memes["joy"] = 0.8
        trap.meters["danger"] = 0.0
        clarinet.meters["sound"] = 0.55
    else:
        world.say(f"{params.child} forgot the warning and reached toward the trap before the safe test was finished.")
        world.say('The brass jaws snapped shut on the edge of the bedtime blanket, and the clarinet fell silent.')
        world.say(f"{params.companion} pulled the blanket free and said, " + '"That was a bad ending for a curious hand. Next time, we pause and ask first."')
        world.say("The magic dimmed instead of helping. At last, the companion secured the trap in a box, and the room grew quiet again.")
        world.say("No one was hurt, but the lovely bedtime surprise was lost because rushing had closed it.")
        world.say('"A safe ending needs patience," the companion said, while the child nodded sleepily.')
        child.memes.update(worry=0.8, calm=0.35, joy=0.1)
        companion.memes["trust"] = 0.7
        trap.meters["danger"] = 1.0
        clarinet.meters["sound"] = 0.0

    world.say(f"At last, {params.child} rested beside the {params.bedtime_object}, while the {params.companion} kept the {params.clarinet if False else 'clarinet'} nearby for morning.")
    return world


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]
    return [
        'Write a child-facing bedtime story containing the words "pound," "clarinet," and "trap."',
        f'Tell a magical bedtime tale in which {world.facts["child"].label} learns why a trap should not be touched before asking for help.',
        f'Use dialogue and the clue "{tale.trap_clue}" to show a safe choice or a clearly explained bad ending.',
    ]


def make_story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    companion: Entity = world.facts["companion"]
    tale: Tale = world.facts["tale"]
    if world.facts["ending"] == "safe":
        result = f"{tale.ending}. The child stayed safe because they followed this rule: {tale.lesson}"
    else:
        result = "The child rushed and caused a bad ending: the trap caught the blanket and the magic faded. Nobody was hurt, but the bedtime surprise was lost."
    return [
        QAItem(
            f"What did {child.label} notice at bedtime?",
            f"{child.label} noticed {tale.trap_clue}. A pound-shaped mark made the strange object seem magical.",
        ),
        QAItem(
            f"What did {companion.label} tell {child.label} to do?",
            f"{companion.label} told {child.label} not to touch the trap yet and to {tale.safe_test}.",
        ),
        QAItem(
            "How did the clarinet matter to the magic?",
            f"The clarinet provided the gentle music required by the magic rule: {tale.magic_rule}",
        ),
        QAItem(
            "How did the story end?",
            result,
        ),
    ]


def make_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a pound sign?", "A pound sign is the symbol #. In this story it is a mysterious mark, not a command to touch a trap."),
        QAItem("What is a clarinet?", "A clarinet is a woodwind instrument played by blowing gently through a mouthpiece and pressing its keys."),
        QAItem("Why can a trap be dangerous?", "A trap can move suddenly and pinch or catch something. People should stop, keep back, and ask a trusted adult for help."),
        QAItem("What makes this a bedtime story?", "It has a quiet nighttime setting, gentle magical wonder, caring dialogue, and an ending that helps the listener feel ready for sleep."),
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
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"ending: {world.facts['ending']}")
    lines.append(f"resolved: {world.facts['resolved']}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=make_story_qa(world),
        world_qa=make_world_qa(world),
        world=world,
    )


HEROES = CHILDREN
COMPANION_NAMES = COMPANIONS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Magical bedtime storyworld about a pound, clarinet, and trap.")
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
    child = rng.choice(CHILDREN)
    companion = rng.choice([name for name in COMPANIONS if name != child])
    return StoryParams(
        place=rng.choice(PLACES),
        child=child,
        companion=companion,
        bedtime_object=rng.choice(OBJECTS),
        ending=rng.choice(["safe", "safe", "bad"]),
    )


ASP_RULES = r"""
theme(pound).
theme(clarinet).
theme(trap).
style(bedtime_story).
feature(magic).
feature(bad_ending).
safe_choice :- theme(trap), feature(magic), feature(dialogue), careful_test.
gentle_music :- theme(clarinet), safe_choice.
resolved :- safe_choice, gentle_music.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("theme", "pound"),
            asp.fact("theme", "clarinet"),
            asp.fact("theme", "trap"),
            asp.fact("style", "bedtime_story"),
            asp.fact("feature", "magic"),
            asp.fact("feature", "bad_ending"),
            asp.fact("feature", "dialogue"),
            asp.fact("careful_test"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        symbols = asp.one_model(asp_program("#show safe_choice/0.\n#show gentle_music/0.\n#show resolved/0."))
        names = {symbol.name for symbol in symbols}
        required = {"safe_choice", "gentle_music", "resolved"}
        if not required.issubset(names):
            return 1
    except Exception:
        return 1

    safe = generate(
        StoryParams(
            place=PLACES[0],
            child="Luna",
            companion="Grandma",
            bedtime_object=OBJECTS[0],
            ending="safe",
            seed=0,
        )
    )
    bad = generate(
        StoryParams(
            place=PLACES[0],
            child="Milo",
            companion="Papa",
            bedtime_object=OBJECTS[1],
            ending="bad",
            seed=1,
        )
    )
    if safe.world is None or not safe.world.facts["resolved"]:
        return 1
    if bad.world is None or bad.world.facts["resolved"]:
        return 1
    for sample in (safe, bad):
        if not all(word in sample.story.lower() for word in ("pound", "clarinet", "trap")):
            return 1
        if not sample.story_qa or not sample.world_qa:
            return 1
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program("#show safe_choice/0.\n#show gentle_music/0.\n#show resolved/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(PLACES[0], "Luna", "Grandma", OBJECTS[0], "safe", 0),
            StoryParams(PLACES[1], "Milo", "Papa", OBJECTS[1], "safe", 1),
            StoryParams(PLACES[2], "Nora", "Aunt Mira", OBJECTS[2], "bad", 2),
            StoryParams(PLACES[3], "Ari", "Uncle Sol", OBJECTS[3], "safe", 3),
            StoryParams(PLACES[0], "Pia", "Mama", OBJECTS[0], "bad", 4),
        ]
    else:
        params_list = []
        for offset in range(max(0, args.n)):
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
