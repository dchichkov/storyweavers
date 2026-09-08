#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a fabulous sound effect.

Luna is preparing an ordinary afternoon snack when a little sound effect
escapes from a toy recorder. The sound seems fabulous, but the story turns on
a simple choice: listen carefully, ask for help, and use the sound to make a
quiet moment welcoming rather than noisy.
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
    parent for parent in Path(__file__).resolve().parents
    if (parent / "storyworlds" / "results.py").is_file()
)
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: Optional[str] = None


@dataclass
class Setting:
    place: str
    landmark: str
    ordinary_activity: str


@dataclass
class SoundArc:
    id: str
    sound: str
    source: str
    problem: str
    first_guess: str
    clue: str
    action: str
    effect: str
    final_image: str
    lesson: str


@dataclass
class StoryParams:
    name: str
    companion: str
    place: str
    sound_style: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, arc: SoundArc) -> None:
        self.setting = setting
        self.arc = arc
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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


SETTINGS = {
    "kitchen window": Setting(
        place="the kitchen window",
        landmark="the round table",
        ordinary_activity="cutting apples for an afternoon snack",
    ),
    "front step": Setting(
        place="the front step",
        landmark="the blue flowerpot",
        ordinary_activity="sorting buttons into a little jar",
    ),
    "laundry room": Setting(
        place="the laundry room",
        landmark="the warm basket of towels",
        ordinary_activity="folding towels into a neat stack",
    ),
}

NAMES = ["Luna", "Mara", "Nia", "Toby", "Owen", "Pia"]
COMPANIONS = ["Grandma", "Ari", "Dad", "Mina", "Uncle Sol"]
SOUND_STYLES = ["bright", "bouncy", "soft", "sparkly"]

ARCS = [
    SoundArc(
        id="teapot_chime",
        sound="ting-a-ling",
        source="a toy recorder beside the tea tin",
        problem="the same bright note kept sounding whenever the table shook",
        first_guess="a tiny fairy was hiding under the table",
        clue="the note stopped whenever the recorder's loose button was held down",
        action="held the button gently and tapped the recorder once",
        effect="the sound became a small welcome chime instead of a startling rattle",
        final_image="Each visitor heard one clear ting-a-ling before taking a warm apple slice.",
        lesson="a fabulous sound becomes useful when someone listens to what makes it happen",
    ),
    SoundArc(
        id="sock_rain",
        sound="pitter-patter",
        source="a wooden rain stick in the laundry basket",
        problem="the noise made everyone think water was leaking",
        first_guess="a pipe had burst behind the wall",
        clue="the floor stayed dry while the sound followed the basket",
        action="lifted the rain stick out and turned it slowly over a towel",
        effect="the worried room changed into a pretend rainy afternoon",
        final_image="The folded towels became hills while pitter-patter played above them.",
        lesson="a careful check can turn a worry into an ordinary bit of fun",
    ),
    SoundArc(
        id="step_bell",
        sound="plonk-plonk",
        source="a loose bell tied to the blue flowerpot",
        problem="every footstep made the dog bark at the empty path",
        first_guess="someone unfamiliar was walking up the steps",
        clue="the bell moved even when the wind touched the flowerpot",
        action="untied the bell and placed it beside the welcome mat",
        effect="the dog settled, and the bell invited people in without startling him",
        final_image="The bell gave one friendly plonk as the evening visitor wiped her shoes.",
        lesson="moving a noisy thing to the right place can help everyone feel calm",
    ),
    SoundArc(
        id="button_buzz",
        sound="brrr-pop",
        source="a button jar with one springy lid",
        problem="the sudden buzz made the buttons jump across the table",
        first_guess="a beetle had crawled into the jar",
        clue="the lid bounced each time the jar was nudged",
        action="put a cloth beneath the jar and closed its lid slowly",
        effect="the buttons stayed safe, and the funny buzz became a signal to pause",
        final_image="Whenever someone reached for a button, the jar gave a tiny brrr-pop.",
        lesson="a small change in the way we handle things can make a big sound gentle",
    ),
    SoundArc(
        id="window_whoosh",
        sound="whooo-sh",
        source="a paper wind spinner by the open window",
        problem="the deep whoosh covered the sound of a friend calling from outside",
        first_guess="a storm was rushing down the street",
        clue="the clouds were still while the spinner turned in the draft",
        action="moved the spinner higher and opened the window a little less",
        effect="the room kept its fabulous breeze sound and made room for voices",
        final_image="The spinner whispered whooo-sh while the friends talked clearly below it.",
        lesson="sharing space means making room for both wonder and ordinary voices",
    ),
]

OPENINGS = [
    "On a very ordinary afternoon",
    "After lunch, when the house was settling down",
    "Just before the first snack plate was ready",
    "While sunlight rested on the floor",
    "At the quiet part of the day",
]

PAUSES = [
    "Luna stopped with one apple slice in her hand",
    "Luna held still beside the table",
    "Luna looked up from the little pile",
    "Luna put down what she was carrying",
]

ASP_RULES = r"""
sound_event(S) :- source(S).
heard(S) :- sound_event(S), attentive.
checked(S) :- heard(S), attentive.
helpful(S) :- checked(S), moved_to_safe_place.
calm_room :- helpful(sound_source).
#show sound_event/1.
#show heard/1.
#show checked/1.
#show helpful/1.
#show calm_room/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("source", "sound_source"),
            asp.fact("attentive"),
            asp.fact("moved_to_safe_place"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show calm_room/0."))
    if any(atom.name == "calm_room" for atom in model):
        print("OK: ASP predicts a helpful sound event.")
        return 0
    print("MISMATCH: ASP did not predict a helpful sound event.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fabulous slice-of-life story with sound effects."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--sound-style", choices=SOUND_STYLES)
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
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        place=args.place or rng.choice(list(SETTINGS)),
        sound_style=args.sound_style or rng.choice(SOUND_STYLES),
        seed=None,
    )


def choose_arc(params: StoryParams) -> SoundArc:
    value = sum(ord(char) for char in f"{params.name}|{params.place}|{params.sound_style}")
    return ARCS[value % len(ARCS)]


def tell(params: StoryParams) -> World:
    arc = choose_arc(params)
    setting = SETTINGS[params.place]
    world = World(setting, arc)

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="child",
            label=params.name,
            location=setting.place,
            memes={"curiosity": 1.0, "care": 1.0},
        )
    )
    companion = world.add(
        Entity(
            id="companion",
            kind="character",
            type="adult",
            label=params.companion,
            location=setting.place,
            memes={"patience": 1.0},
        )
    )
    source = world.add(
        Entity(
            id="sound_source",
            kind="thing",
            type="sound-maker",
            label=arc.source,
            location=setting.place,
            owner=hero.id,
            meters={"noisy": 1.0},
        )
    )
    room = world.add(
        Entity(
            id="room",
            kind="place",
            type="ordinary-place",
            label=setting.place,
            meters={"calm": 1.0},
        )
    )

    world.facts.update(
        hero=hero,
        companion=companion,
        source=source,
        room=room,
        opening=OPENINGS[
            (params.seed if params.seed is not None else len(params.name)) % len(OPENINGS)
        ],
        pause=PAUSES[
            (params.seed if params.seed is not None else len(params.place)) % len(PAUSES)
        ],
    )

    world.say(
        f"{world.facts['opening']}, {hero.label} was {setting.ordinary_activity} "
        f"at {setting.place}."
    )
    world.say(
        f"The day felt plain and pleasant until {arc.sound} came from {arc.source}."
    )

    world.para()
    hero.memes["curiosity"] += 1.0
    world.say(
        f"{world.facts['pause']}. The fabulous {arc.sound} sounded again, and "
        f"{arc.problem}."
    )
    world.say(
        f'"Maybe {arc.first_guess}," said {hero.label}. '
        f'"Let us check before we worry," replied {companion.label}.'
    )
    world.say(
        f"{companion.label} pointed out that {arc.clue}."
    )

    world.para()
    hero.meters["listened"] = 1.0
    world.say(
        f"{hero.label} listened closely instead of making the noise louder."
    )
    world.say(
        f'"I hear where it starts now," said {hero.label}. '
        f'"Then we know what to try," said {companion.label}.'
    )
    world.say(f"{hero.label} {arc.action}.")
    source.meters["noisy"] = 0.0
    source.meters["useful"] = 1.0
    room.meters["calm"] = 1.0
    world.fired.add("checked_sound")
    world.say(f"The change worked: {arc.effect}.")

    world.para()
    world.say(
        f"The afternoon stayed ordinary, but it no longer felt quite so plain. "
        f"{arc.final_image}"
    )
    world.say(
        f"{hero.label} smiled because {arc.lesson}. "
        f"{companion.label} smiled too, and the next sound had room to be heard."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    arc = world.arc
    hero = world.facts["hero"]
    return [
        f"Write a slice-of-life story about {hero.label} hearing the fabulous sound effect {arc.sound}.",
        f"Tell a gentle everyday story in {world.setting.place} where someone checks why {arc.sound} is happening.",
        f"Write a child-facing story showing that {arc.lesson}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    arc = world.arc
    return [
        QAItem(
            question=f"What was {hero.label} doing when the sound began?",
            answer=f"{hero.label} was {world.setting.ordinary_activity} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What caused the sound effect {arc.sound}?",
            answer=f"The sound came from {arc.source}. The clue was that {arc.clue}.",
        ),
        QAItem(
            question=f"How did {hero.label} and {companion.label} solve the problem?",
            answer=f"{hero.label} listened carefully, and then {hero.label} {arc.action}.",
        ),
        QAItem(
            question="How did the ending show that the situation had changed?",
            answer=f"{arc.effect} {arc.final_image}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a sound made to suggest an action, object, place, or feeling.",
        ),
        QAItem(
            question="Why is listening carefully useful?",
            answer="Listening carefully can reveal where a sound comes from and help someone choose a safe, helpful response.",
        ),
        QAItem(
            question="What does fabulous mean?",
            answer="Fabulous means wonderfully impressive, delightful, or extraordinary.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        if entity.location:
            details.append(f"location={entity.location}")
        lines.append(
            f"{entity.id}: {entity.type} {entity.label} {' '.join(details)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Luna", "Grandma", "kitchen window", "bright", 11),
    StoryParams("Mara", "Ari", "front step", "bouncy", 22),
    StoryParams("Toby", "Dad", "laundry room", "soft", 33),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show calm_room/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show calm_room/0."))
        print("calm room:", any(atom.name == "calm_room" for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(100, target * 30):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
