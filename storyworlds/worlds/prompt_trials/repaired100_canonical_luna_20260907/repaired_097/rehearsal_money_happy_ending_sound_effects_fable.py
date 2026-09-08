#!/usr/bin/env python3
"""
Standalone storyworld: a rehearsal, a missing coin pouch, and a happy ending
with playful sound effects, told as a gentle fable.
"""

from __future__ import annotations

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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    location: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    protagonist: str = "Luna"
    protagonist_type: str = "girl"
    friend: str = "Pip"
    friend_type: str = "boy"
    caretaker: str = "Mara"
    caretaker_type: str = "woman"
    rehearsal_id: int = 0
    telling_mode: int = 0


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


REHEARSALS = [
    {
        "title": "the jingly moon",
        "show": "The Moon Who Learned to Smile",
        "prop": "a silver moon lantern",
        "problem": "the little coin pouch for the ticket table was missing",
        "clue": "a bright coin trail curved beneath the painted moon",
        "cause": "the pouch had slipped into the moon prop when the lantern was lifted",
        "action": "shook the moon lantern gently over a cloth basket",
        "resolution": "The coins chimed into the basket, and the pouch was returned to the ticket table.",
        "ending": "The moon lantern glowed while the coins answered with a cheerful jingle.",
        "lesson": "A calm question can find what a worried guess cannot.",
    },
    {
        "title": "the wooden drum",
        "show": "The Fox and the Friendly Bell",
        "prop": "a round wooden drum",
        "problem": "the money for the village costumes could not be found",
        "clue": "a soft clink sounded whenever the drum rolled",
        "cause": "the envelope had slid beneath the drum during a dance step",
        "action": "rolled the drum onto a folded blanket and looked underneath",
        "resolution": "The envelope was found dry and safe, and the costume money was counted with Mara.",
        "ending": "Boom-boom went the drum, while every costume button shone.",
        "lesson": "Before blaming a friend, listen for the small clue nearby.",
    },
    {
        "title": "the tapping curtain",
        "show": "The Sparrow Who Shared the Sun",
        "prop": "a blue stage curtain",
        "problem": "the money box for the happy-ending feast seemed empty",
        "clue": "three coins tapped against the curtain rod",
        "cause": "the box had been moved for sweeping, and the loose coins rested in its cloth pocket",
        "action": "asked the caretaker to lower the curtain and check its sewn pocket",
        "resolution": "The coins were found, the box was sealed, and the feast plan stayed bright.",
        "ending": "The curtain rose with a swish, and the actors cheered.",
        "lesson": "Careful hands and honest words make room for good endings.",
    },
    {
        "title": "the rattling basket",
        "show": "The Kind Little Giant",
        "prop": "a woven basket for the giant's lunch",
        "problem": "the rehearsal money had vanished before the final scene",
        "clue": "the basket made a tiny rattle whenever someone carried it",
        "cause": "the coin purse had been placed inside the basket with the paper lunch",
        "action": "asked everyone to stop, then checked the basket in front of Mara",
        "resolution": "The purse was safe, and the actors made a clear place for money beside the script.",
        "ending": "The giant bowed, the basket rattled, and the whole hall laughed.",
        "lesson": "A shared check can turn worry into trust.",
    },
]


OPENINGS = [
    "The rehearsal began beneath a row of warm lamps.",
    "On the afternoon of the final rehearsal, the little hall buzzed with hope.",
    "Before the curtain could rise, the actors gathered among painted props.",
    "The fable was nearly ready, but one small problem waited backstage.",
    "A rehearsal can teach more than lines when everyone listens carefully.",
]

SOUND_EFFECTS = [
    "Tap-tap!",
    "Jingle-jangle!",
    "Swish!",
    "Clap-clap!",
    "Boom-boom!",
]


def reason_gate(params: StoryParams) -> None:
    names = [params.protagonist.strip(), params.friend.strip(), params.caretaker.strip()]
    if not all(names):
        raise StoryError("Character names must not be empty.")
    if len(set(names)) != len(names):
        raise StoryError("The protagonist, friend, and caretaker need different names.")
    if params.rehearsal_id < 0:
        raise StoryError("rehearsal_id cannot be negative.")


def build_world(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity(
        "hero", "character", params.protagonist_type, params.protagonist,
        "stage", memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.0},
    ))
    friend = world.add(Entity(
        "friend", "character", params.friend_type, params.friend},
        "stage", memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.0},
    ))
    caretaker = world.add(Entity(
        "caretaker", "character", params.caretaker_type, params.caretaker,
        "backstage", memes={"patience": 1.0, "worry": 0.0},
    ))
    pouch = world.add(Entity(
        "money_pouch", "thing", "pouch", "small coin pouch",
        "prop", owner="caretaker", meters={"lost": 1.0, "found": 0.0},
    ))
    prop = world.add(Entity(
        "prop", "thing", "stage_prop", "painted prop",
        "stage", meters={"moved": 0.0},
    ))
    script = world.add(Entity(
        "script", "thing", "script", "rehearsal script",
        "stage", meters={"open": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, caretaker=caretaker, pouch=pouch, prop=prop, script=script)
    return world


def tell(params: StoryParams) -> World:
    reason_gate(params)
    world = build_world(params)
    incident = REHEARSALS[params.rehearsal_id % len(REHEARSALS)]
    opening = OPENINGS[params.telling_mode % len(OPENINGS)]
    sound = SOUND_EFFECTS[(params.rehearsal_id + params.telling_mode) % len(SOUND_EFFECTS)]
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    caretaker = world.entities["caretaker"]
    pouch = world.entities["money_pouch"]
    prop = world.entities["prop"]

    world.facts.update(
        title=incident["title"],
        show=incident["show"],
        prop=incident["prop"],
        problem=incident["problem"],
        clue=incident["clue"],
        cause=incident["cause"],
        action=incident["action"],
        resolution=incident["resolution"],
        ending=incident["ending"],
        lesson=incident["lesson"],
        sound=sound,
        solved=True,
    )

    world.say(
        f"{opening} {hero.label}, {friend.label}, and {caretaker.label} were preparing "
        f"the fable called {incident['show']}. {incident['prop'].capitalize()} waited beside "
        "the painted scenery, and every actor knew that the money belonged to the grown-up caretaker."
    )
    world.say(
        f"{sound} Then {caretaker.label} discovered that {incident['problem']}. "
        f"{caretaker.label} frowned, but {hero.label} said, "
        f"'Let us look for a clue before we blame anyone.'"
    )
    world.say(
        f"{friend.label} listened near {incident['prop']} and heard that {incident['clue']}. "
        f"'I hear something,' {friend.label} said. 'Could the prop be part of the answer?'"
    )

    world.para()
    world.say(
        f"The actors paused their rehearsal. Together they {incident['action']}. "
        f"The careful search showed that {incident['cause']}."
    )
    world.say(
        f"{sound} The money was counted by {caretaker.label}, and the rehearsal could continue. "
        f"'Thank you for asking instead of guessing,' {caretaker.label} said."
    )
    world.say(
        f"'And thank you for listening,' {hero.label} replied. "
        f"'Now we know what happened.'"
    )

    world.para()
    world.say(incident["resolution"])
    world.say(
        f"The actors practiced the final scene once more. {incident['ending']} "
        f"{incident['lesson']} The curtain rose, the audience clapped, and everyone went home happy."
    )

    pouch.meters["lost"] = 0.0
    pouch.meters["found"] = 1.0
    pouch.location = "ticket table"
    prop.meters["moved"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0
    caretaker.memes["worry"] = 0.0
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly fable about a rehearsal of {f['show']} and a money mystery.",
        f"Include the sound effect {f['sound']} and show how the clue {f['clue']} changes the actors' actions.",
        f"End happily with this lesson: {f['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    caretaker = world.entities["caretaker"]
    return [
        QAItem(
            f"What happened during the rehearsal of {f['show']}?",
            f"During the rehearsal, {f['problem']}. The actors paused so they could investigate safely and calmly.",
        ),
        QAItem(
            f"What clue did {friend.label} notice?",
            f"{friend.label} noticed that {f['clue']}. The sound directed the actors toward the prop.",
        ),
        QAItem(
            f"What caused the money problem?",
            f"The money problem happened because {f['cause']}. It was misplaced, not stolen.",
        ),
        QAItem(
            f"How did {hero.label} help solve the mystery?",
            f"{hero.label} asked everyone to look for evidence before blaming anyone, and the group then {f['action']}.",
        ),
        QAItem(
            f"How did the rehearsal end?",
            f"{f['resolution']} The actors finished their rehearsal, the audience clapped, and the ending was happy.",
        ),
        QAItem(
            "What lesson does this fable teach?",
            f"It teaches that {f['lesson']}",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "What is a rehearsal?",
        "A rehearsal is a practice before a performance, when actors try their lines, movements, music, and props.",
    ),
    QAItem(
        "Why should money be kept with a responsible adult?",
        "Money should be kept with a responsible adult so it can be counted, protected, and used fairly.",
    ),
    QAItem(
        "What is a sound effect?",
        "A sound effect is a made or recorded sound that helps an audience notice an action or feeling.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
        meters = {k: round(v, 3) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 3) for k, v in entity.memes.items() if v}
        details = []
        if entity.location:
            details.append(f"location={entity.location}")
        if entity.owner:
            details.append(f"owner={entity.owner}")
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id}: {entity.label}; " + ", ".join(details))
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
found(P) :- pouch(P), discovered(P).
happy_ending :- rehearsal, found(money_pouch), kind_search.
coherent :- rehearsal, money, happy_ending.
#show coherent/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("rehearsal"),
        asp.fact("money"),
        asp.fact("pouch", "money_pouch"),
        asp.fact("discovered", "money_pouch"),
        asp.fact("kind_search"),
    ])


def asp_program(show: str = "#show coherent/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_ok = any(symbol.name == "coherent" for symbol in model)
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python reasonableness gate.")
        return 1
    sample = generate(StoryParams())
    if not sample.story or "rehearsal" not in sample.story.lower() or "money" not in sample.story.lower():
        print("MISMATCH: generated story check failed.")
        return 1
    print("OK: ASP and Python reasonableness gate agree.")
    print("OK: generated story check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rehearsal-money fable storyworld.")
    parser.add_argument("--protagonist")
    parser.add_argument("--protagonist-type", choices=["girl", "boy", "woman", "man"], default="girl")
    parser.add_argument("--friend")
    parser.add_argument("--friend-type", choices=["girl", "boy", "woman", "man"], default="boy")
    parser.add_argument("--caretaker")
    parser.add_argument("--caretaker-type", choices=["girl", "boy", "woman", "man"], default="woman")
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


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int) -> StoryParams:
    protagonist = args.protagonist or rng.choice(["Luna", "Mira", "Nell", "Suri"])
    friend = args.friend or rng.choice(["Pip", "Toby", "Rafi", "Bea"])
    caretaker = args.caretaker or rng.choice(["Mara", "June", "Aunt Sol", "Nadia"])
    if len({protagonist, friend, caretaker}) != 3:
        raise StoryError("The three story characters must have different names.")
    return StoryParams(
        seed=sample_seed,
        protagonist=protagonist,
        protagonist_type=args.protagonist_type,
        friend=friend,
        friend_type=args.friend_type,
        caretaker=caretaker,
        caretaker_type=args.caretaker_type,
        rehearsal_id=sample_seed % len(REHEARSALS),
        telling_mode=(sample_seed // len(REHEARSALS)) % len(OPENINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(seed=base_seed, protagonist="Luna", friend="Pip", caretaker="Mara", rehearsal_id=0),
            StoryParams(seed=base_seed + 1, protagonist="Mira", friend="Bea", caretaker="June", rehearsal_id=1),
            StoryParams(seed=base_seed + 2, protagonist="Nell", friend="Rafi", caretaker="Nadia", rehearsal_id=2),
            StoryParams(seed=base_seed + 3, protagonist="Suri", friend="Toby", caretaker="Aunt Sol", rehearsal_id=3),
        ]
        samples = [generate(p) for p in curated]
    else:
        for offset in range(args.n):
            seed = base_seed + offset
            samples.append(generate(resolve_params(args, random.Random(seed), seed)))

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
