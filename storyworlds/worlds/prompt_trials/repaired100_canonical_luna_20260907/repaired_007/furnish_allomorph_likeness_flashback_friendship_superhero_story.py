#!/usr/bin/env python3
"""
A small storyworld about a child superhero, a friendship, and a flashback.

The unusual seed words become concrete story objects:
- furnish: a bright rescue room needs furnishing before the town's celebration
- allomorph: a shape-shifting badge has several forms
- likeness: a portrait helps a friend recognize the hero's true kindness
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def phrase(self) -> str:
        return self.label


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Arc:
    key: str
    danger: str
    furnishing: str
    flashback: str
    ending: str


PLACES = {
    "rooftop_rescue_hall": Place("rooftop_rescue_hall", "the rooftop rescue hall", {"city", "high"}),
    "moonlit_library": Place("moonlit_library", "the moonlit library", {"city", "quiet"}),
    "sunrise_station": Place("sunrise_station", "the sunrise station", {"city", "bright"}),
}

NAMES = {
    "boy": ["Luna", "Milo", "Theo", "Jasper"],
    "girl": ["Luna", "Maya", "Iris", "Nia"],
}

ARCS = (
    Arc(
        "windy_hall",
        "a gust tore the welcome banner loose and sent chairs skittering toward the open edge",
        "a strong bench, two soft cushions, and a row of glowing lamps",
        "She remembered how her friend had once shared the last dry blanket during a storm.",
        "The hall became a warm rescue room, and the two friends watched the city lights sparkle below.",
    ),
    Arc(
        "runaway_cart",
        "a supply cart rolled down the sloping floor toward a stack of glass jars",
        "a low shelf, a bright rug, and a cupboard for every rescue tool",
        "She remembered her friend saying, “A brave helper never has to work alone.”",
        "The jars stayed safe, and the furnished station shone like a little star.",
    ),
    Arc(
        "shadow_signal",
        "a dark cloud covered the signal mirror just as a lost puppy barked below",
        "a tall stool, a round table, and a red blanket for tired rescuers",
        "She remembered the day her friend had followed her tiny flashlight through a scary tunnel.",
        "The mirror flashed a friendly beam, and the puppy found its way home.",
    ),
    Arc(
        "bridge_bell",
        "the warning bell jammed while a loose plank trembled over the garden bridge",
        "a sturdy rail, a wooden chest, and a cheerful sign for visitors",
        "She remembered that friendship was not a cape; it was a hand held out at the right time.",
        "The bridge stood firm, the bell rang clear, and everyone crossed safely.",
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    hero_gender: str = "girl"
    friend_gender: str = "boy"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES[hero_gender])
    choices = [name for name in NAMES[friend_gender] if name != hero]
    friend = args.friend or rng.choice(choices)
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        hero_name=hero,
        friend_name=friend,
        hero_gender=hero_gender,
        friend_gender=friend_gender,
    )


def valid_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hero_gender not in NAMES or params.friend_gender not in NAMES:
        raise StoryError("Hero and friend must use a supported gender.")
    if not params.hero_name.strip() or not params.friend_name.strip():
        raise StoryError("Hero and friend need names.")
    if params.hero_name.casefold() == params.friend_name.casefold():
        raise StoryError("The hero and friend need different names.")


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity("hero", "character", params.hero_name, "hero"))
    friend = world.add(Entity("friend", "character", params.friend_name, "friend"))
    badge = world.add(Entity("badge", "object", "the allomorph badge", "tool"))
    portrait = world.add(Entity("portrait", "object", "the likeness portrait", "clue"))
    arc = ARCS[random.Random(params.seed if params.seed is not None else 0).randrange(len(ARCS))]

    hero.memes["hope"] = 1
    friend.memes["trust"] = 1
    badge.meters["forms"] = 3
    portrait.meters["clarity"] = 1

    world.say(f"In {place.label}, {params.hero_name} wore a silver cape and helped {params.friend_name} furnish the new rescue room.")
    world.say(f"They carried {arc.furnishing} through the bright doorway.")
    world.para()

    world.say(f"Then {arc.danger}.")
    world.say(f'"I can fix it alone!" cried {params.hero_name}.')
    world.say(f'"You do not have to," answered {params.friend_name}. "Friends make a stronger team."')
    world.para()

    friend.memes["trust"] += 1
    hero.memes["courage"] += 1
    badge.meters["active"] = 1
    world.say("The allomorph badge changed from a star to a shield, then to a shining key.")
    world.say(f"{params.hero_name} used the shield to block the danger while {params.friend_name} used the key to open the safe supply closet.")
    world.say(f"That brave teamwork brought back a flashback: {arc.flashback}")
    world.para()

    hero.meters["helped"] = 1
    friend.meters["helped"] = 1
    hero.memes["joy"] = 1
    friend.memes["joy"] = 1
    portrait.meters["seen"] = 1
    world.say(f"On the wall, {portrait.label} showed {params.hero_name} and {params.friend_name} smiling side by side.")
    world.say(f"The likeness reminded {params.hero_name} that a superhero is known not only by a cape, but by the friends {params.hero_name} protects.")
    world.say(arc.ending)

    world.facts.update(
        hero=hero,
        friend=friend,
        badge=badge,
        portrait=portrait,
        arc=arc,
        danger=arc.danger,
        furnishing=arc.furnishing,
        flashback=arc.flashback,
        ending=arc.ending,
        solved=True,
        friendship=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly superhero story about friendship, a flashback, and an allomorph badge.",
        f"Tell how {f['hero'].phrase} and {f['friend'].phrase} solved this danger: {f['danger']}.",
        f"Show why the likeness portrait and the furnished rescue room matter at {world.place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What danger did the superhero and friend face?",
            f"They faced a danger when {f['danger']}.",
        ),
        QAItem(
            "How did friendship help solve the problem?",
            f"{f['hero'].phrase} and {f['friend'].phrase} shared the work. The badge became useful forms, so one friend protected the scene while the other opened the safe supply closet.",
        ),
        QAItem(
            "What did the flashback teach the hero?",
            f"The flashback reminded the hero that {f['flashback']} That memory helped the hero accept friendship instead of trying to work alone.",
        ),
        QAItem(
            "What showed that the rescue room had changed?",
            f"The room was furnished with {f['furnishing']}, and {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an allomorph?",
            "An allomorph is a different form or shape of something that keeps the same basic purpose.",
        ),
        QAItem(
            "What is a likeness?",
            "A likeness is a picture or appearance that looks like a person or thing.",
        ),
        QAItem(
            "Why can friendship help during a hard task?",
            "Friendship can bring trust, ideas, and shared effort, so people do not have to face a hard task alone.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---", f"place: {world.place.label}"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
    lines.append(f"facts: solved={world.facts.get('solved')} friendship={world.facts.get('friendship')}")
    return "\n".join(lines)


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


ASP_RULES = r"""
dangerous(D) :- danger(D).
forms(badge,3).
can_change(badge) :- forms(badge,N), N >= 3.
friendship :- friend(F), trusts(F,hero).
solved :- can_change(badge), friendship, portrait(likeness).
outcome(rescue) :- solved.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("danger", "loose_banner"),
            asp.fact("friend", "friend"),
            asp.fact("trusts", "friend", "hero"),
            asp.fact("portrait", "likeness"),
            asp.fact("badge", "badge"),
        ]
    )


def asp_program(show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if not asp.atoms(model, "outcome"):
            print("ASP parity failed: no rescue outcome.")
            return 1
        params = StoryParams("rooftop_rescue_hall", "Luna", "Milo", seed=3)
        sample = generate(params)
        if not sample.story or not sample.world.facts["solved"]:
            print("Generation parity failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: Python and ASP smoke tests passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    valid_params(params)
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
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero friendship storyworld.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--hero-gender", choices=["boy", "girl"])
    parser.add_argument("--friend-gender", choices=["boy", "girl"])
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
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print(asp.atoms(asp.one_model(asp_program()), "outcome"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams("rooftop_rescue_hall", "Luna", "Milo", "girl", "boy", base_seed),
            StoryParams("moonlit_library", "Maya", "Iris", "girl", "girl", base_seed + 1),
            StoryParams("sunrise_station", "Theo", "Nia", "boy", "girl", base_seed + 2),
        ]
        samples = [generate(params) for params in presets]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
