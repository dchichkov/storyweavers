#!/usr/bin/env python3
"""
A small rhyming storyworld about excitement, a wandering hobo, and a saddle.

The old word "hobo" is used here only as a historical story label for a
traveler who rides from place to place; the traveler is treated with dignity.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"trail": 0.0})
    memes: dict[str, float] = field(
        default_factory=lambda: {"excitement": 0.0, "worry": 0.0, "courage": 0.0}
    )


@dataclass
class Object:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: {"wear": 0.0})
    memes: dict[str, float] = field(
        default_factory=lambda: {"trust": 0.0, "value": 0.0}
    )


@dataclass
class World:
    setting: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    people: dict[str, Person] = field(default_factory=dict)
    objects: dict[str, Object] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    traveler_name: str = "Rowan"
    horse_name: str = "Comet"
    saddle_name: str = "red saddle"
    setting: str = "moonlit meadow"


@dataclass(frozen=True)
class Twist:
    key: str
    sign: str
    mistaken_belief: str
    discovery: str
    repair: str
    lesson: str
    ending: str


NAMES = ["Luna", "Mara", "Nia", "Tess", "Ivy", "Pia"]
TRAVELERS = ["Rowan", "Eli", "Sage", "Robin", "Jules"]
HORSES = ["Comet", "Daisy", "Star", "Clover", "Pebble"]
SADDLES = ["red saddle", "blue saddle", "patchwork saddle", "silver-trimmed saddle"]

TWISTS = [
    Twist(
        key="bell",
        sign="a tiny bell jingled beneath the saddle flap",
        mistaken_belief="the saddle had slipped loose and would tumble into the grass",
        discovery="the bell was tied to a hidden strap, and its ringing marked the safest trail",
        repair="fastened the strap and followed the bell's cheerful beat over the soft ground",
        lesson="a frightening sound may be a helpful sign when it is examined calmly",
        ending="the bell chimed beside the saddle while moonlight silvered the meadow",
    ),
    Twist(
        key="map",
        sign="a folded map peeked from the saddle's worn pocket",
        mistaken_belief="the map pointed toward a dangerous ravine",
        discovery="the map was upside down, and its bright line led to a warm stable",
        repair="turned the map around, then helped guide the horse along the marked path",
        lesson="a new view can turn a scary puzzle into a clear direction",
        ending="the map rested in the saddle pocket as the stable lantern glowed gold",
    ),
    Twist(
        key="feather",
        sign="a blue feather clung to the saddle's buckle",
        mistaken_belief="a storm bird had carried away the traveler's lucky charm",
        discovery="the feather marked a low branch where the charm had caught",
        repair="lifted the branch together and returned the charm to its little cord",
        lesson="following a small clue can solve a problem without a grand chase",
        ending="the blue feather waved from the branch while the charm shone below",
    ),
    Twist(
        key="loose_stitch",
        sign="one bright stitch trailed from the saddle like a tiny red road",
        mistaken_belief="the whole saddle was tearing apart",
        discovery="the stitch had snagged on a thorn and only its loose end needed freeing",
        repair="held the leather steady while the traveler pulled the thread gently away",
        lesson="careful hands can protect something better than hurried strength",
        ending="the neat saddle rested on a rail, its red stitch tucked safely in place",
    ),
]

OPENINGS = [
    "At dusk, moonlight poured like milk across the meadow",
    "When the first star blinked above the trail",
    "On a breezy evening beside the old barn",
    "Just as the sunset painted the clouds peach and gold",
]

DIALOGUES = [
    (
        '"I feel a storm of excitement!" {hero} cried.',
        '"Then let us make our excitement useful," said {traveler}.',
    ),
    (
        '"What if the saddle is in trouble?" {hero} asked.',
        '"We can look before we leap," replied {traveler}.',
    ),
    (
        '"My thoughts are galloping faster than Comet," said {hero}.',
        '"Give each thought one slow step," answered {traveler}.',
    ),
]


def build_world(params: StoryParams) -> World:
    if params.setting != "moonlit meadow":
        raise StoryError("This storyworld only supports the moonlit meadow setting.")
    if len({params.hero_name, params.traveler_name, params.horse_name}) < 3:
        raise StoryError("The child, traveler, and horse must have different names.")
    world = World(setting=params.setting)
    hero = Person(params.hero_name, "young helper")
    traveler = Person(params.traveler_name, "wandering traveler")
    horse = Person(params.horse_name, "gentle horse")
    saddle = Object(params.saddle_name, "saddle")
    saddle.memes["trust"] = 1.0
    saddle.memes["value"] = 1.0
    world.people.update(
        hero=hero,
        traveler=traveler,
        horse=horse,
    )
    world.objects["saddle"] = saddle
    world.facts.update(hero=hero, traveler=traveler, horse=horse, saddle=saddle)
    return world


def narrate(world: World, seed: int) -> None:
    rng = random.Random(seed ^ 0xB17A5E)
    hero: Person = world.facts["hero"]
    traveler: Person = world.facts["traveler"]
    horse: Person = world.facts["horse"]
    saddle: Object = world.facts["saddle"]
    twist = rng.choice(TWISTS)
    opening = rng.choice(OPENINGS)
    hero_line, traveler_line = rng.choice(DIALOGUES)
    thought = rng.choice(
        [
            "What if excitement is a spark, not a storm?",
            "I can listen to my worry without letting it steer.",
            "A brave heart can move slowly.",
            "Perhaps the smallest clue is the one I need.",
        ]
    )
    method = rng.choice(
        [
            "counted three breaths and checked each buckle in turn",
            "walked one careful circle around the horse",
            "asked the traveler to explain what had changed",
            "held the lantern low and followed the clue without tugging it",
        ]
    )

    world.facts.update(twist=twist, thought=thought, method=method)
    hero.memes["excitement"] = 1.0
    traveler.memes["courage"] = 1.0

    world.say(f"{opening}, and {hero.name} met {traveler.name} by the trail.")
    world.say(
        f"{traveler.name} was a hobo in the old storybook sense: a respectful name "
        "for a traveler who moved from place to place with care."
    )
    world.say(
        f"The traveler stood beside {horse.name}, whose {saddle.name} shone "
        "like a sunset sewn to leather."
    )
    world.say(
        f"{hero.name} felt a fizz of excitement, for {traveler.name} had promised "
        f"a moonlit ride toward the quiet barn."
    )
    world.say(f"Then {twist.sign}, and the happy plan gave a sudden fright.")

    world.para()
    world.say(hero_line.format(hero=hero.name, traveler=traveler.name))
    world.say(f"Inside, {hero.name} thought, “{thought}”")
    world.say(f"In a rush, {hero.name} believed {twist.mistaken_belief}.")
    hero.memes["worry"] = 1.0
    world.say(
        "The horse stamped once, the tall grass swayed, and the saddle creaked "
        "as if it, too, had a secret to say."
    )
    world.say(traveler_line.format(hero=hero.name, traveler=traveler.name))
    world.say(f"Together they {method}.")

    world.para()
    world.say(
        f"That careful pause revealed the twist: {twist.discovery}."
    )
    hero.memes["courage"] = 1.0
    saddle.memes["trust"] = 2.0
    world.say(f"{hero.name} helped {traveler.name} {twist.repair}.")
    world.say(
        f"The excitement returned, but now it danced with patience instead of panic."
    )
    world.say(f"{hero.name} learned that {twist.lesson}.")
    world.say(
        f"At the barn, {twist.ending}; {horse.name} gave a soft, "
        "contented nicker, and the night felt safe again."
    )


def generation_prompts(world: World) -> list[str]:
    hero: Person = world.facts["hero"]
    traveler: Person = world.facts["traveler"]
    saddle: Object = world.facts["saddle"]
    return [
        f"Write a rhyming children's story about {hero.name}, {traveler.name}, excitement, and a {saddle.name}.",
        "Include an inner monologue that changes a hasty choice into a careful one.",
        "Build toward a clear twist, then end with a concrete peaceful image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Person = world.facts["hero"]
    traveler: Person = world.facts["traveler"]
    horse: Person = world.facts["horse"]
    saddle: Object = world.facts["saddle"]
    twist: Twist = world.facts["twist"]
    thought: str = world.facts["thought"]
    return [
        QAItem(
            question=f"Who did {hero.name} meet beside the trail?",
            answer=f"{hero.name} met {traveler.name}, a traveling hobo in the old storybook sense, beside the trail.",
        ),
        QAItem(
            question=f"What was {horse.name} wearing?",
            answer=f"{horse.name} was wearing the {saddle.name}.",
        ),
        QAItem(
            question=f"What did {hero.name} think inside?",
            answer=f"{hero.name} thought, “{thought}” and used that thought to slow down.",
        ),
        QAItem(
            question="What was the story's twist?",
            answer=f"The twist was that {twist.discovery}.",
        ),
        QAItem(
            question=f"What did {hero.name} learn?",
            answer=f"{hero.name} learned that {twist.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a saddle?",
            answer="A saddle is a padded seat fitted onto a horse or another riding animal.",
        ),
        QAItem(
            question="What is excitement?",
            answer="Excitement is a strong, lively feeling that can make someone eager for what may happen next.",
        ),
        QAItem(
            question="Why should a worried person pause before acting?",
            answer="Pausing gives a worried person time to notice facts, ask for help, and choose a safer action.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters or reader thought was true.",
        ),
        QAItem(
            question="How is the word hobo used in this story?",
            answer="It is used as an old storybook label for a traveler who moves from place to place, not as an insult or stereotype.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
setting(moonlit_meadow).
traveling(traveler).
has_saddle(horse).
excited(hero).
worried(hero).
pauses(hero).
careful(hero).
twist_revealed(hero).
safe_arrival(hero).

calm_choice(hero) :- excited(hero), worried(hero), pauses(hero), careful(hero).
good_ending(hero) :- twist_revealed(hero), safe_arrival(hero), calm_choice(hero).

#show calm_choice/1.
#show good_ending/1.
#show has_saddle/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "moonlit_meadow"),
            asp.fact("traveling", "traveler"),
            asp.fact("has_saddle", "horse"),
            asp.fact("excited", "hero"),
            asp.fact("worried", "hero"),
            asp.fact("pauses", "hero"),
            asp.fact("careful", "hero"),
            asp.fact("twist_revealed", "hero"),
            asp.fact("safe_arrival", "hero"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show calm_choice/1.\n#show good_ending/1.\n#show has_saddle/1."
        )
    )
    actual = {(sym.name, tuple(str(a) for a in sym.arguments)) for sym in model}
    expected = {
        ("calm_choice", ("hero",)),
        ("good_ending", ("hero",)),
        ("has_saddle", ("horse",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python facts.")
        print("ASP atoms:", sorted(actual))
        print("Expected:", sorted(expected))
        return 1
    sample = generate(StoryParams(seed=17))
    if not sample.story or "saddle" not in sample.story.lower():
        print("Generated story exercise failed.")
        return 1
    print("OK: ASP gate matches Python story facts and generated story.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming moonlit story about excitement, a hobo, and a saddle."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--traveler", choices=TRAVELERS)
    parser.add_argument("--horse", choices=HORSES)
    parser.add_argument("--saddle", dest="saddle_name", choices=SADDLES)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    traveler = args.traveler or rng.choice(TRAVELERS)
    horse = args.horse or rng.choice(HORSES)
    if len({hero, traveler, horse}) < 3:
        horse = next(name for name in HORSES if name not in {hero, traveler})
    return StoryParams(
        seed=args.seed,
        hero_name=hero,
        traveler_name=traveler,
        horse_name=horse,
        saddle_name=args.saddle_name or rng.choice(SADDLES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world, params.seed if params.seed is not None else 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for person in world.people.values():
        lines.append(
            f"{person.name}: role={person.role} meters={dict(person.meters)} "
            f"memes={dict(person.memes)}"
        )
    for obj in world.objects.values():
        lines.append(
            f"{obj.name}: kind={obj.kind} meters={dict(obj.meters)} "
            f"memes={dict(obj.memes)}"
        )
    return "\n".join(lines)


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
        print(
            asp_program(
                "#show calm_choice/1.\n#show good_ending/1.\n#show has_saddle/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show calm_choice/1.\n#show good_ending/1.\n#show has_saddle/1."
            )
        )
        for symbol in model:
            print(symbol)
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(
                seed=base_seed,
                hero_name="Luna",
                traveler_name="Rowan",
                horse_name="Comet",
                saddle_name="red saddle",
            ),
            StoryParams(
                seed=base_seed + 1,
                hero_name="Mara",
                traveler_name="Sage",
                horse_name="Daisy",
                saddle_name="patchwork saddle",
            ),
            StoryParams(
                seed=base_seed + 2,
                hero_name="Tess",
                traveler_name="Robin",
                horse_name="Star",
                saddle_name="blue saddle",
            ),
            StoryParams(
                seed=base_seed + 3,
                hero_name="Ivy",
                traveler_name="Jules",
                horse_name="Clover",
                saddle_name="silver-trimmed saddle",
            ),
        ]
        samples = [generate(params) for params in params_list]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
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
