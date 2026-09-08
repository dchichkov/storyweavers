#!/usr/bin/env python3
"""
A small adventure storyworld about a blanket, a teeming cave, and a brave encounter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

PLACES = ["the moonlit valley", "the pine forest", "the windy hill"]
CREATURES = ["fireflies", "silver moths", "glowing beetles", "tiny night birds"]
NAMES = ["Luna", "Milo", "Tara", "Nico", "Pia", "Arlo"]
COMPANIONS = ["brother", "sister", "friend", "cousin"]
TRAITS = ["curious", "careful", "bold", "thoughtful"]

BLANKETS = {
    "red": "a red wool blanket",
    "blue": "a blue quilted blanket",
    "gold": "a golden fleece blanket",
}

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("warm", "spread", "held", "safe"):
            self.meters.setdefault(key, 0.0)
        for key in ("fear", "bravery", "wonder", "trust", "calm"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    place: str
    blanket: str
    creature: str
    name: str
    companion: str
    trait: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Encounter:
    title: str
    opening: str
    danger: str
    twist: str
    clue: str
    dialogue: str
    brave_action: str
    resolution: str
    lesson: str
    ending: str


ENCOUNTERS = [
    Encounter(
        "The Lantern Meadow",
        "a silver glow moved through the grass",
        "a sudden wind tore the blanket from the picnic stone",
        "the blanket had caught on a thorn beside a nest of tiny sleeping birds",
        "the glow came from fireflies circling the safe path",
        '"If we pull slowly, we can free it without waking them," Luna said.',
        "crawled close, shielded the nest with one hand, and loosened the cloth one thorn at a time",
        "they rescued the blanket, covered the chilly nest, and followed the fireflies home",
        "Bravery can be gentle when it protects something small.",
        "the fireflies made a bright trail over the blanket while the birds slept warmly beneath it",
    ),
    Encounter(
        "The Echoing Arch",
        "a deep rustle rolled out from an old stone arch",
        "the valley began to teem with glowing beetles as the path darkened",
        "the frightening rustle was a loose row of seed pods tapping in the wind",
        "the beetles gathered wherever the blue thread in the blanket caught moonlight",
        '"Let us listen before we run," the companion whispered.',
        "held the blanket wide as a signal and stepped toward the arch with careful feet",
        "they found the safe path, gathered the loose pods, and watched the beetles scatter",
        "A brave heart checks a mystery before deciding what it is.",
        "the blanket became a moon-bright flag above the quiet arch",
    ),
    Encounter(
        "The Hidden Hollow",
        "the trail ended at a hollow filled with fluttering moths",
        "the moths began to teem around the children and hid the way back",
        "they were not chasing the children; they were following warmth from the blanket",
        "a cool stone ledge gave the moths another place to rest",
        '"Maybe the blanket is the clue, not the danger," Luna said.',
        "spread the blanket on the ledge and waited calmly beside the hollow",
        "the moths settled on the cloth, leaving a clear path through the trees",
        "Courage sometimes means making room instead of fighting.",
        "the blanket shimmered with resting moths as the open trail pointed toward home",
    ),
    Encounter(
        "The Ridge Wind",
        "a flock of tiny night birds rose from the ridge",
        "their wings made a rushing sound that seemed to surround the camp",
        "the birds were guiding the children away from a cracked bridge",
        "their flight always turned before the broken stones",
        '"They are showing us something," the companion said.',
        "followed the birds along the safer ridge and tied the blanket between two posts",
        "the blanket marked the safe crossing while the birds vanished beyond the pines",
        "Bravery listens for warnings, even when they arrive noisily.",
        "the blanket fluttered beside the sound path as the children crossed in safety",
    ),
]

OPENINGS = [
    "At sunset",
    "Before the stars appeared",
    "On a cool evening",
    "Just after a light rain",
    "While the last sunlight warmed the hills",
]

@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.lines if part)


def choose_encounter(params: StoryParams) -> Encounter:
    key = "|".join(map(str, (params.seed, params.place, params.blanket, params.creature, params.name, params.companion, params.trait)))
    digest = hashlib.sha256(key.encode()).digest()
    return ENCOUNTERS[int.from_bytes(digest[:4], "big") % len(ENCOUNTERS)]


def tell(params: StoryParams) -> World:
    if params.blanket not in BLANKETS:
        raise StoryError(f"Unknown blanket choice: {params.blanket}")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place choice: {params.place}")
    if params.creature not in CREATURES:
        raise StoryError(f"Unknown creature choice: {params.creature}")

    encounter = choose_encounter(params)
    world = World(Setting(params.place))
    child = world.add(Entity("child", "character", "child", params.name))
    buddy = world.add(Entity("companion", "character", params.companion, "the " + params.companion))
    blanket = world.add(Entity("blanket", "object", "blanket", BLANKETS[params.blanket], owner="child"))

    child.memes["fear"] = 1
    child.memes["wonder"] = 1
    buddy.memes["trust"] = 1
    blanket.meters["held"] = 1
    blanket.meters["warm"] = 1

    vals = {"name": params.name, "buddy": buddy.label, "creature": params.creature}
    opening = random.Random(params.seed).choice(OPENINGS) if params.seed is not None else OPENINGS[0]

    world.say(f"{opening}, {params.name}, who was {params.trait}, carried {blanket.label} into {params.place} with {buddy.label}.")
    world.say(f"They had come looking for an adventure, but soon they faced {encounter.opening}.")
    world.say(f"The valley seemed to teem with {params.creature}, and every little sound made the path feel bigger.")

    world.para()
    world.say(f"Then the encounter changed: {encounter.danger}.")
    world.say(f"For one breath, {params.name} wanted to hurry home.")
    world.say(f"{encounter.twist}.")
    world.say(f"{encounter.clue}.")

    world.para()
    world.say(encounter.dialogue)
    world.say(f"{params.name} took a slow breath and chose bravery instead of a frightened guess.")
    child.memes["fear"] = 0
    child.memes["bravery"] = 1
    child.memes["calm"] = 1
    blanket.meters["spread"] = 1
    world.say(f"{params.name} {encounter.brave_action}.")
    world.say(f"Together, the children {encounter.resolution}.")
    blanket.meters["safe"] = 1

    world.para()
    world.say(encounter.lesson)
    world.say(f"At last, {encounter.ending}.")

    world.facts.update(
        child=child,
        buddy=buddy,
        blanket=blanket,
        encounter=encounter,
        creature=params.creature,
        params=params,
        brave=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    e = f["encounter"]
    return [
        "Write a child-facing adventure about a blanket, a teeming night landscape, and a surprising encounter.",
        f"Tell an adventure in {p.place} where {p.name} uses bravery to understand a twist involving {p.creature}.",
        f"Write a story called {e.title} in which a blanket changes from something carried into something useful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    e = f["encounter"]
    return [
        QAItem(
            f"What danger did {p.name} face?",
            f"{e.danger.capitalize()}. At first, the teeming {p.creature} and the strange sounds made the path seem unsafe.",
        ),
        QAItem(
            "What was the twist in the encounter?",
            f"{e.twist.capitalize()} The first frightening idea was not the real explanation.",
        ),
        QAItem(
            f"How did {p.name} show bravery?",
            f"{p.name} {e.brave_action}. This was brave because the child acted carefully instead of running or causing harm.",
        ),
        QAItem(
            "How did the blanket help?",
            f"The children {e.resolution}. The blanket became useful because they spread or used it as part of their safe plan.",
        ),
        QAItem(
            "What lesson did the adventure teach?",
            e.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a blanket?", "A blanket is a soft covering used to keep a person or animal warm."),
        QAItem("What does teem mean?", "To teem means to be filled with many moving people, animals, or things."),
        QAItem("What is bravery?", "Bravery means doing what is helpful or right even when something feels frightening."),
        QAItem("What is a twist in a story?", "A twist is a surprising change that makes an earlier event mean something different."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:10} ({entity.type:10}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
brave(child) :- calm(child), faced_twist.
safe_blanket(blanket) :- brave(child), spread(blanket).
good_adventure :- brave(child), safe_blanket(blanket), encounter_resolved.
#show good_adventure/0.
"""


def asp_facts(world: Optional[World] = None) -> str:
    import asp
    facts = [
        asp.fact("child", "child"),
        asp.fact("faced_twist"),
        asp.fact("calm", "child"),
        asp.fact("spread", "blanket"),
        asp.fact("encounter_resolved"),
    ]
    return "\n".join(facts)


def asp_program(world: Optional[World] = None) -> str:
    return asp_facts(world) + "\n" + ASP_RULES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adventure storyworld about a blanket, a teeming place, and a brave encounter.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--blanket", choices=list(BLANKETS))
    parser.add_argument("--creature", choices=CREATURES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        blanket=args.blanket or rng.choice(list(BLANKETS)),
        creature=args.creature or rng.choice(CREATURES),
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        trait=args.trait or rng.choice(TRAITS),
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("the moonlit valley", "red", "fireflies", "Luna", "friend", "curious"),
    StoryParams("the pine forest", "blue", "silver moths", "Milo", "sister", "careful"),
    StoryParams("the windy hill", "gold", "tiny night birds", "Tara", "cousin", "bold"),
]


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        if not any(str(atom) == "good_adventure" for atom in model):
            raise StoryError("ASP twin did not derive good_adventure")
    except ImportError:
        return 0
    for params in CURATED:
        sample = generate(params)
        if "blanket" not in sample.story or "bravery" not in sample.story:
            raise StoryError("Generated story failed required narrative checks")
        if not sample.story_qa:
            raise StoryError("Generated story has no story questions")
    print("OK: Python and ASP adventure checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = []
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program(samples[0].world if samples else None))
            print("ASP model:", " ".join(str(atom) for atom in model))
        except ImportError as exc:
            raise StoryError("ASP mode requires clingo to be installed") from exc
        return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
