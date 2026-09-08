#!/usr/bin/env python3
"""
A small superhero storyworld about a yoyo, a favorite pastime, twilight,
and a misunderstanding that becomes a cautionary lesson.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class Setting:
    id: str
    label: str
    affordances: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str = "rooftop"
    hero: str = "Luna"
    friend: str = "Pip"
    pastime: str = "yoyo"
    twilight_event: str = "signal"
    lesson: str = "caution"
    ending: str = "lantern"
    seed: Optional[int] = None


SETTINGS = {
    "rooftop": Setting(
        "rooftop",
        "the Moonbeam rooftop",
        {"practice", "watch", "signal"},
    ),
    "courtyard": Setting(
        "courtyard",
        "the Starbridge courtyard",
        {"practice", "watch", "signal"},
    ),
}

PASTIMES = {
    "yoyo": {
        "label": "yoyo",
        "verb": "practice yoyo tricks",
        "gerund": "practicing yoyo tricks",
        "danger": "a fast yoyo string can whip across a walkway",
        "safe_action": "lowered the yoyo and made a clear circle around the practice spot",
    }
}

TWILIGHT_EVENTS = {
    "signal": {
        "warning": "a blinking light appeared beyond the chimneys",
        "clue": "the light flashed in the same rhythm as the rooftop beacon",
        "truth": "the blinking light was a maintenance lamp, not a trapped child",
    },
    "shadow": {
        "warning": "a tall shadow moved beside the water tank",
        "clue": "the shadow stretched whenever the last sunlight shifted",
        "truth": "the tall shadow belonged to a flag on the tank",
    },
}

ENDINGS = {
    "lantern": "At last, Luna hung a bright lantern beside the practice circle, and the yoyo spun like a tiny moon beneath it.",
    "beacon": "The rooftop beacon glowed again, while Luna's yoyo rested safely in her palm before its next brave spin.",
    "stars": "When the first stars appeared, Luna and Pip shared the yoyo turn by turn, careful enough to make every loop shine.",
}

HERO_NAMES = ["Luna", "Maya", "Zara", "Nia"]
FRIEND_NAMES = ["Pip", "Theo", "Milo", "Aya"]


def validate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.pastime not in PASTIMES:
        raise StoryError(f"Unknown pastime: {params.pastime}")
    if params.twilight_event not in TWILIGHT_EVENTS:
        raise StoryError(f"Unknown twilight event: {params.twilight_event}")
    if params.ending not in ENDINGS:
        raise StoryError(f"Unknown ending: {params.ending}")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must have different names.")


def build_world(params: StoryParams, rng: random.Random) -> World:
    validate(params)
    setting = SETTINGS[params.setting]
    event = TWILIGHT_EVENTS[params.twilight_event]
    pastime = PASTIMES[params.pastime]
    world = World(setting)

    hero = world.add(Entity(
        params.hero,
        "hero",
        f"Captain {params.hero}",
        meters={"balance": 1.0, "attention": 0.0},
        memes={"confidence": 1.0, "worry": 0.0},
    ))
    friend = world.add(Entity(
        params.friend,
        "friend",
        params.friend,
        meters={"distance": 0.0},
        memes={"trust": 1.0, "worry": 0.0},
    ))
    yoyo = world.add(Entity(
        "yoyo",
        "object",
        "a red-and-gold yoyo",
        meters={"speed": 0.0, "risk": 0.0},
        memes={"importance": 1.0},
        owner=hero.id,
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        yoyo=yoyo,
        event=event,
        pastime=pastime,
        ending=ENDINGS[params.ending],
        twist=rng.choice([
            "The evening breeze tugged at the rooftop flags.",
            "The city lights blinked awake below the roof.",
            "A cool blue hush settled over the chimneys.",
        ]),
    )

    world.say(
        f"At the edge of {setting.label}, {hero.id} wore a silver cape and practiced "
        f"{pastime['gerund']} as the city turned purple."
    )
    world.say(
        f"{friend.id} watched from beside the safety rail while the red-and-gold yoyo "
        f"whirled down and climbed back into {hero.id}'s hand."
    )
    world.say(world.facts["twist"])
    world.para()

    world.say(
        f"Just then, {event['warning']}. {hero.id} saw {event['clue']} and mistook it for "
        f"a secret distress signal."
    )
    hero.memes["worry"] += 1.0
    yoyo.meters["risk"] += 1.0
    world.say(
        f'"Someone needs my help!" {hero.id} cried. "I must go now!"'
    )
    world.say(
        f'"Wait," {friend.id} said. "Did you check what the light is saying?"'
    )
    world.say(
        f'"I saw a flash. That is enough," {hero.id} answered, gripping the yoyo string.'
    )
    world.para()

    world.say(
        f"{hero.id} hurried toward the roof's far corner, but the yoyo string stretched "
        f"across the practice path."
    )
    yoyo.meters["speed"] += 1.0
    hero.meters["attention"] += 1.0
    world.say(
        f"{friend.id} stepped back and raised both hands. \"Captain, your yoyo is crossing "
        f"the walkway. A rescue must not create a new danger.\""
    )
    world.say(
        f"Those words made {hero.id} stop. {hero.id} lowered the yoyo, made a clear circle, "
        f"and looked again."
    )
    hero.memes["worry"] = 0.0
    hero.meters["attention"] += 1.0
    yoyo.meters["risk"] = 0.0

    world.say(
        f"The blinking light was {event['truth']}. It was not a cry for help at all."
    )
    world.say(
        f'"I misunderstood the signal," {hero.id} admitted. "Next time I will look, listen, '
        f"and ask before I dash.\""
    )
    world.say(
        f'"That is how a real hero keeps everyone safe," {friend.id} said.'
    )
    world.para()

    hero.memes["confidence"] += 1.0
    friend.memes["trust"] += 1.0
    world.say(
        f"Together they marked the practice circle with chalk. {hero.id} returned to "
        f"{pastime['gerund']}, this time keeping the string inside the bright boundary."
    )
    world.say(world.facts["ending"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story for children about {f['hero'].id}, a yoyo, and a twilight misunderstanding at {world.setting.label}.",
        f"Show how {f['hero'].id} learns that courage needs caution when {f['event']['warning']}.",
        f"Include a short dialogue between {f['hero'].id} and {f['friend'].id}, then end with this image: {f['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    friend = f["friend"].id
    event = f["event"]
    pastime = f["pastime"]
    return [
        QAItem(
            "What pastime was the hero enjoying?",
            f"{hero} was enjoying {pastime['gerund']} with a red-and-gold yoyo on {world.setting.label}.",
        ),
        QAItem(
            "What did the hero misunderstand at twilight?",
            f"{hero} misunderstood {event['clue']} and thought it was a secret distress signal.",
        ),
        QAItem(
            "How did the friend help?",
            f"{friend} asked {hero} to check the signal and pointed out that the yoyo string had crossed the walkway.",
        ),
        QAItem(
            "What cautionary lesson did the hero learn?",
            f"{hero} learned to look, listen, and ask before rushing to help, because a rescue should not create a new danger.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "Why can twilight make things harder to identify?",
        "Twilight leaves less light, so shadows and distant signals can be mistaken for something else.",
    ),
    QAItem(
        "What is a yoyo?",
        "A yoyo is a small toy that travels down and back up a string when someone guides it.",
    ),
    QAItem(
        "What makes a superhero story safe for children?",
        "A child-friendly superhero story shows brave action together with careful choices, teamwork, and responsibility.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"setting: {world.setting.label}"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = build_world(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


ASP_RULES = r"""
setting(rooftop).
setting(courtyard).
pastime(yoyo).
twilight(signal).
twilight(shadow).
object(yoyo).
needs_caution(yoyo).
misunderstanding(signal).
misunderstanding(shadow).
safe_action(look_listen_ask).
valid_story(S, P, T) :- setting(S), pastime(P), twilight(T), misunderstanding(T), needs_caution(P), safe_action(look_listen_ask).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "rooftop"),
        asp.fact("setting", "courtyard"),
        asp.fact("pastime", "yoyo"),
        asp.fact("twilight", "signal"),
        asp.fact("twilight", "shadow"),
        asp.fact("object", "yoyo"),
        asp.fact("needs_caution", "yoyo"),
        asp.fact("misunderstanding", "signal"),
        asp.fact("misunderstanding", "shadow"),
        asp.fact("safe_action", "look_listen_ask"),
    ])


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (setting, "yoyo", event)
        for setting in SETTINGS
        for event in TWILIGHT_EVENTS
    ]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_values = set(valid_combos())
    asp_values = set(asp_valid_combos())
    if python_values == asp_values:
        for params in (
            StoryParams(setting="rooftop", twilight_event="signal", seed=1),
            StoryParams(setting="courtyard", twilight_event="shadow", seed=2),
        ):
            sample = generate(params)
            if not sample.story or "yoyo" not in sample.story:
                print("Verification failed: generated story was incomplete.")
                return 1
        print(f"OK: ASP/Python parity holds for {len(asp_values)} combinations.")
        return 0
    print("ASP/Python mismatch.")
    print("Only in ASP:", sorted(asp_values - python_values))
    print("Only in Python:", sorted(python_values - asp_values))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(HERO_NAMES),
        friend=args.friend or rng.choice(FRIEND_NAMES),
        pastime=args.pastime or "yoyo",
        twilight_event=args.twilight_event or rng.choice(list(TWILIGHT_EVENTS)),
        lesson="caution",
        ending=args.ending or rng.choice(list(ENDINGS)),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-friendly superhero storyworld about a yoyo at twilight."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--pastime", choices=PASTIMES, default="yoyo")
    parser.add_argument("--twilight-event", choices=TWILIGHT_EVENTS)
    parser.add_argument("--ending", choices=ENDINGS)
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
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combinations = [
            ("rooftop", "signal"),
            ("rooftop", "shadow"),
            ("courtyard", "signal"),
            ("courtyard", "shadow"),
        ]
        for index, (setting, event) in enumerate(combinations):
            params = StoryParams(
                setting=setting,
                hero=HERO_NAMES[index % len(HERO_NAMES)],
                friend=FRIEND_NAMES[index % len(FRIEND_NAMES)],
                pastime="yoyo",
                twilight_event=event,
                ending=list(ENDINGS)[index % len(ENDINGS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.asp:
        print(json.dumps({"valid_combinations": asp_valid_combos()}, indent=2))
        return

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
