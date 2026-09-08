#!/usr/bin/env python3
"""
A standalone storyworld about an ultra-bright space quest, a foretold
transformation, and a small crew learning that courage can change shape.
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Space:
    name: str
    light: str
    danger: str


@dataclass
class Character:
    name: str
    kind: str
    trait: str
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Starship:
    name: str = "the Little Comet"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    transformed: bool = False
    course: str = "unknown"


@dataclass
class StoryParams:
    name: str
    kind: str
    trait: str
    space: str
    relic: str
    seed: Optional[int] = None


SPACES = {
    "moon": Space("the silver moon", "blue", "a field of drifting stones"),
    "nebula": Space("the violet nebula", "purple", "a storm of bright dust"),
    "asteroid": Space("the quiet asteroid belt", "golden", "a spinning canyon"),
}

KINDS = ["rabbit", "fox", "mouse", "otter", "owl"]
TRAITS = ["curious", "brave", "patient", "kind", "clever"]
RELICS = {
    "crystal": "a singing crystal",
    "compass": "an old star compass",
    "seed": "a silver moon-seed",
    "key": "a tiny golden key",
}
NAMES = {
    "rabbit": ["Luna", "Pip", "Tessa"],
    "fox": ["Rin", "Mira", "Sol"],
    "mouse": ["Nim", "Pax", "Moss"],
    "otter": ["Odo", "Nori", "Bram"],
    "owl": ["Ari", "Vela", "Noor"],
}

QUESTS = [
    {
        "target": "the dark beacon beyond the comet gate",
        "clue": "a row of blue sparks always appeared before the beacon turned",
        "obstacle": "the beacon's shadow folded around the ship",
        "action": "opened the star compass and followed the blue sparks instead of the map",
        "change": "the ship unfolded silver sails and became light enough to slip through the shadow",
        "ending": "the beacon woke and painted a bright road home",
    },
    {
        "target": "the sleeping garden on the far side of the nebula",
        "clue": "warm green motes drifted toward the quietest engine",
        "obstacle": "violet dust covered every window and hid the garden",
        "action": "silenced the engines and listened for the green motes",
        "change": "the ship grew gentle crystal wings that brushed the dust aside",
        "ending": "tiny flowers opened along the garden's silver path",
    },
    {
        "target": "the lost moon bell in the asteroid belt",
        "clue": "three stones chimed whenever the ship chose the safer turn",
        "obstacle": "a spinning canyon blocked the shortest route",
        "action": "steered by the stones' soft music rather than by speed",
        "change": "the ship transformed into a round, glowing lantern",
        "ending": "the moon bell rang, and its warm note guided every traveler home",
    },
]

PROPHECIES = [
    ("an inscription on the launch door", "When the way grows dark, the vessel will become what the journey needs."),
    ("a dream Luna's grandmother once shared", "The smallest traveler may carry the largest light."),
    ("a faded message from an explorer", "Do not force the stars; notice what they are already showing you."),
    ("three dots scratched beside the ship's controls", "A true transformation begins when someone listens."),
]

OPENINGS = [
    "At the edge of the little observatory, a small ship waited beneath a sky crowded with stars.",
    "Luna lived where the night was so clear that children could count the rings of Saturn.",
    "The crew of the Little Comet kept a map of every friendly star and every place still unknown.",
]

DIALOGUES = [
    '"The glow is not a warning," Luna said. "It is a clue."',
    '"Should we turn back?" asked Pip. "Not yet," Luna answered. "The stars are showing us a safer way."',
    '"What if the ship changes?" asked Mira. Luna smiled. "Then we will learn how to fly it."',
]

ENDING_LESSONS = [
    "Luna learned that a quest is not only about reaching a place; it is also about becoming ready for it.",
    "The crew discovered that careful listening can unlock a door that force cannot even find.",
    "From that night on, every small clue was treated as a star of its own.",
]


class World:
    def __init__(self, space: Space) -> None:
        self.space = space
        self.hero: Optional[Character] = None
        self.ship = Starship()
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.ship.meters = {"fuel": 1.0, "distance": 0.0, "adaptability": 0.0}
        self.ship.memes = {"hope": 0.0, "trust": 0.0, "wonder": 0.0}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def foreshadow(world: World) -> None:
    if "foreshadow" in world.fired:
        return
    world.fired.add("foreshadow")
    source, words = world.facts["prophecy"]
    world.say(f"Before launch, {world.hero.name} found {source}. It read: “{words}”")


def scan_clue(world: World) -> None:
    if "scan" in world.fired:
        return
    world.fired.add("scan")
    quest = world.facts["quest"]
    world.ship.meters["distance"] += 0.5
    world.say(f"Near {quest['target']}, the ship's instruments flickered. {quest['clue'].capitalize()}.")


def face_obstacle(world: World) -> None:
    if "obstacle" in world.fired:
        return
    world.fired.add("obstacle")
    quest = world.facts["quest"]
    world.say(f"Then danger filled the view: {quest['obstacle'].capitalize()}. {world.facts['dialogue']}")


def transform(world: World) -> None:
    if "transform" in world.fired:
        return
    if "scan" not in world.fired or "obstacle" not in world.fired:
        raise StoryError("The ship cannot transform before the quest reveals its clue and obstacle.")
    world.fired.add("transform")
    quest = world.facts["quest"]
    world.say(f"Luna remembered the foreshadowing and {quest['action']}.")
    world.say(f"At once, {quest['change'].capitalize()}.")
    world.ship.transformed = True
    world.ship.meters["adaptability"] = 1.0
    world.ship.memes["hope"] = 1.0
    world.ship.memes["trust"] = 1.0
    world.ship.course = quest["target"]


def conclude(world: World) -> None:
    quest = world.facts["quest"]
    if not world.ship.transformed:
        raise StoryError("A quest ending requires the ship's transformation.")
    world.say(
        f"The transformed ship reached {quest['target']}. {quest['ending'].capitalize()} "
        f"{world.hero.name} and the crew flew home beneath the {world.space.light} stars. "
        f"{world.facts['lesson']}"
    )


def build_world(params: StoryParams) -> World:
    world = World(SPACES[params.space])
    world.hero = Character(params.name, params.kind, params.trait)
    key = params.seed if params.seed is not None else sum(ord(c) for c in "|".join(vars(params).values()) if isinstance(c, str))
    world.facts["quest"] = QUESTS[key % len(QUESTS)]
    world.facts["prophecy"] = PROPHECIES[(key // len(QUESTS)) % len(PROPHECIES)]
    world.facts["opening"] = OPENINGS[(key // 7) % len(OPENINGS)]
    world.facts["dialogue"] = DIALOGUES[(key // 11) % len(DIALOGUES)]
    world.facts["lesson"] = ENDING_LESSONS[(key // 13) % len(ENDING_LESSONS)]
    world.facts["relic"] = RELICS[params.relic]
    return world


def tell_story(world: World) -> None:
    hero = world.hero
    quest = world.facts["quest"]
    world.say(f"{world.facts['opening']} {hero.name}, a {hero.trait} little {hero.kind}, was its navigator.")
    world.say(f"The crew planned a quest to {quest['target']}. Their only guide was {world.facts['relic']}.")
    world.para()
    foreshadow(world)
    world.say(f"“We will go together,” {hero.name} told the crew. “Even an ultra-long journey begins with one careful turn.”")
    scan_clue(world)
    world.para()
    face_obstacle(world)
    transform(world)
    world.para()
    conclude(world)
    world.facts.update(
        problem=quest["obstacle"],
        clue=quest["clue"],
        action=quest["action"],
        transformation=quest["change"],
        destination=quest["target"],
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.hero
    return [
        f"Write a space adventure about {hero.name}, an ultra-long quest, and a transforming starship.",
        f"Tell a child-friendly tale in which a foreshadowed transformation helps {hero.name} reach {world.facts['quest']['target']}.",
        f"Write a quest story where a small clue changes the crew's decision.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"What quest did {world.hero.name} and the crew undertake?",
            f"They traveled to {f['destination']}, carrying {f['relic']} as a guide.",
        ),
        QAItem(
            "What clue did the crew notice?",
            f"They noticed that {f['clue']}. This clue helped them choose their next action.",
        ),
        QAItem(
            "How did the starship transform?",
            f"The crew {f['action']}, and then {f['transformation']}. The change let them pass the danger.",
        ),
        QAItem(
            "What proved that the quest succeeded?",
            f"They reached {f['destination']}, where {f['quest']['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a starship?", "A starship is a spacecraft designed to travel through space."),
        QAItem("What is foreshadowing?", "Foreshadowing is an earlier hint about something important that happens later."),
        QAItem("What is a transformation?", "A transformation is a meaningful change in form, ability, or condition."),
        QAItem("Why are clues useful on a quest?", "Clues provide information that helps travelers make safer and wiser choices."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for q in sample.story_qa:
        lines.extend([f"Q: {q.question}", f"A: {q.answer}"])
    lines.append("\n== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.extend([f"Q: {q.question}", f"A: {q.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"space={world.space.name}",
        f"hero={world.hero.name} ({world.hero.kind}, {world.hero.trait})",
        f"destination={world.facts['destination']}",
        f"relic={world.facts['relic']}",
        f"ship.transformed={world.ship.transformed}",
        f"ship.course={world.ship.course}",
        f"ship.meters={world.ship.meters}",
        f"ship.memes={world.ship.memes}",
        f"fired={sorted(world.fired)}",
    ])


ASP_RULES = r"""
space(S) :- space_name(S).
kind(K) :- kind_name(K).
relic(R) :- relic_name(R).
valid(S,K,R) :- space(S), kind(K), relic(R).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("space_name", x) for x in SPACES]
    lines += [asp.fact("kind_name", x) for x in KINDS]
    lines += [asp.fact("relic_name", x) for x in RELICS]
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, k, r) for s in SPACES for k in KINDS for r in RELICS]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program())
    cl = set(asp.atoms(model, "valid"))
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combinations).")
        for seed in range(3):
            p = StoryParams("Luna", "rabbit", "curious", "moon", "crystal", seed)
            if not generate(p).world.ship.transformed:
                return 1
        return 0
    print("MISMATCH between Python and ASP.")
    return 1


@dataclass
class _Args:
    pass


CURATED = [
    StoryParams("Luna", "rabbit", "curious", "moon", "crystal"),
    StoryParams("Mira", "fox", "brave", "nebula", "compass"),
    StoryParams("Nim", "mouse", "patient", "asteroid", "seed"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An ultra space adventure with foreshadowing and transformation.")
    ap.add_argument("--space", choices=SPACES)
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    kind = args.kind or rng.choice(KINDS)
    return StoryParams(
        name=args.name or rng.choice(NAMES[kind]),
        kind=kind,
        trait=args.trait or rng.choice(TRAITS),
        space=args.space or rng.choice(list(SPACES)),
        relic=args.relic or rng.choice(list(RELICS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
    if trace:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid combinations")
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(max(1, args.n)):
            rng = random.Random(base + i)
            p = resolve_params(args, rng)
            p.seed = base + i
            samples.append(generate(p))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
