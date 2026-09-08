#!/usr/bin/env python3
"""
A small Adventure storyworld about a fantastic gate, a missing piece of
knowledge, and reconciliation between two friends.
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
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carrying: Optional[str] = None
    open: bool = False
    repaired: bool = False


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Adventure:
    id: str
    opening: str
    obstacle: str
    clue: str
    turn: str
    ending: str


@dataclass
class StoryParams:
    name: str
    friend_name: str
    animal: str
    friend_animal: str
    adventure: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

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


SETTING = Setting(
    place="the Moonlit Valley",
    affords={"adventure", "gate", "knowledge", "reconciliation", "fantastic"},
)

ADVENTURES = {
    "gate_reconciliation": Adventure(
        id="gate_reconciliation",
        opening="At the edge of the Moonlit Valley stood a fantastic silver gate with stars moving inside its bars.",
        obstacle="The gate would not open because its two moon keys had been turned in opposite directions.",
        clue="A stone inscription said that the gate opened only when its travelers shared what they truly knew.",
        turn="When the friends admitted that each had hidden a different part of the map, the moon keys began to glow together.",
        ending="The gate opened onto a bright trail, and the friends stepped through side by side, no longer guarding secrets from each other.",
    ),
    "whispering_pass": Adventure(
        id="whispering_pass",
        opening="Beyond the Moonlit Valley, a fantastic gate guarded a whispering mountain pass.",
        obstacle="The gate repeated every unkind word the friends had spoken during their journey and stayed shut.",
        clue="A blue feather showed them that honest words could change the echoes into music.",
        turn="They apologized for blaming one another and named the help each friend had given.",
        ending="The gate sang open, and a warm wind carried their repaired friendship up the mountain path.",
    ),
    "garden_of_glass": Adventure(
        id="garden_of_glass",
        opening="A fantastic gate of clear glass blocked the path to a garden where floating flowers hummed.",
        obstacle="The gate reflected each friend alone, so neither could find the latch.",
        clue="Tiny letters on the frame revealed that the latch appeared only when two reflections touched.",
        turn="The friends stopped arguing over who should lead and placed their hands on the same shining panel.",
        ending="Their reflections joined, the glass gate opened, and the floating flowers welcomed them with gentle bells.",
    ),
}


NAMES = ["Luna", "Mina", "Taro", "Pip", "Nori", "Jasper"]
ANIMALS = ["fox", "rabbit", "otter", "badger", "raccoon", "deer"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adventure world about knowledge, a fantastic gate, and reconciliation."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend-name", choices=NAMES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--friend-animal", choices=ANIMALS)
    parser.add_argument("--adventure", choices=sorted(ADVENTURES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    friend_choices = [n for n in NAMES if n != name]
    friend_name = args.friend_name or rng.choice(friend_choices)
    animal = args.animal or rng.choice(ANIMALS)
    friend_animal = args.friend_animal or rng.choice([a for a in ANIMALS if a != animal])
    return StoryParams(
        name=name,
        friend_name=friend_name,
        animal=animal,
        friend_animal=friend_animal,
        adventure=args.adventure or rng.choice(sorted(ADVENTURES)),
    )


def tell(params: StoryParams) -> World:
    if params.adventure not in ADVENTURES:
        raise StoryError("That adventure is not part of the fantastic gate world.")
    if params.name == params.friend_name:
        raise StoryError("The traveler and friend must have different names.")
    if params.animal == params.friend_animal:
        raise StoryError("The two friends must be different kinds of animals.")

    adventure = ADVENTURES[params.adventure]
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        label=params.name,
        meters={"curiosity": 1.0, "trust": 0.0},
        memes={"worry": 1.0, "courage": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_animal,
        label=params.friend_name,
        meters={"knowledge": 1.0, "trust": 0.0},
        memes={"hurt": 1.0, "kindness": 0.0},
    ))
    gate = world.add(Entity(
        id="fantastic_gate",
        type="gate",
        label="the fantastic gate",
        meters={"alignment": 0.0},
        memes={"magic": 1.0},
        open=False,
    ))
    moon_key = world.add(Entity(
        id="moon_key",
        type="key",
        label="the moon key",
        meters={"useful": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, gate=gate, key=moon_key, adventure=adventure, params=params)

    world.say(adventure.opening)
    world.say(
        f"{hero.id} the {hero.type} wanted to explore, while {friend.id} the {friend.type} "
        "wanted to be certain they knew the safe path."
    )
    world.para()
    world.say(f"{hero.id} hurried to the latch, but {friend.id} pulled them back.")
    world.say(f'"Wait," said {friend.id}. "We do not know enough yet."')
    world.say(f'"I know we can solve it," answered {hero.id}, "but I need you with me."')
    world.say(adventure.obstacle)
    world.say(adventure.clue)
    world.say(
        f"{friend.id} confessed that they had kept one map mark secret, and "
        f"{hero.id} admitted they had guessed instead of asking."
    )
    friend.meters["trust"] = 1.0
    friend.memes["hurt"] = 0.0
    friend.memes["kindness"] = 1.0
    hero.meters["trust"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["courage"] = 1.0
    world.fired.add("truth_shared")
    world.say(adventure.turn)
    gate.meters["alignment"] = 1.0
    gate.open = True
    gate.repaired = True
    world.fired.add("reconciliation")
    world.say(
        f"Together they fitted the moon key into the gate. The silver bars folded apart, "
        f"and {hero.id} thanked {friend.id} for knowing when to slow down."
    )
    world.para()
    world.say(adventure.ending)
    world.say(
        f"From then on, {hero.id} and {friend.id} agreed that knowledge was strongest "
        "when friends shared it instead of keeping it behind a locked gate."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    adventure = world.facts["adventure"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f"Write an Adventure about {hero.id} and {friend.id} finding a fantastic gate.",
        f"Tell a story in which the friends must share what they know to open the gate.",
        f"Write a reconciliation adventure ending with this image: {adventure.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    adventure: Adventure = world.facts["adventure"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why could {hero.id} and {friend.id} not open the fantastic gate at first?",
            answer=adventure.obstacle,
        ),
        QAItem(
            question="What did the inscription or clue teach the friends?",
            answer=adventure.clue,
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} admit to each other?",
            answer=f"They admitted that {friend.id} had hidden part of the map and {hero.id} had guessed instead of asking.",
        ),
        QAItem(
            question="How did reconciliation change the adventure?",
            answer=f"The friends apologized, shared what they knew, and worked together so the gate could open.",
        ),
        QAItem(
            question="What proved that the gate had opened?",
            answer=adventure.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gate?",
            answer="A gate is a movable barrier that can open or close an entrance.",
        ),
        QAItem(
            question="What does fantastic mean?",
            answer="Fantastic means wonderfully unusual, magical, or full of imagination.",
        ),
        QAItem(
            question="What does it mean to know something?",
            answer="To know something means to understand or be sure about it because of learning or experience.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by speaking honestly, listening, and repairing trust.",
        ),
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting journey involving a challenge, discovery, or surprising event.",
        ),
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
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        if entity.open:
            state.append("open=True")
        if entity.repaired:
            state.append("repaired=True")
        lines.append(f"  {entity.id:16} ({entity.type:10}) {' '.join(state)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combo(name: str, friend: str, adventure: str) -> bool:
    return name != friend and adventure in ADVENTURES


ASP_RULES = r"""
valid_story(N,F,A) :-
    name(N), friend(F), adventure(A),
    N != F,
    reconciliation(A),
    fantastic_gate(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in NAMES:
        lines.append(asp.fact("name", name))
        lines.append(asp.fact("friend", name))
    for adventure in ADVENTURES:
        lines.append(asp.fact("adventure", adventure))
        lines.append(asp.fact("reconciliation", adventure))
        lines.append(asp.fact("fantastic_gate", adventure))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {
        (name, friend, adventure)
        for name in NAMES
        for friend in NAMES
        for adventure in ADVENTURES
        if valid_combo(name, friend, adventure)
    }
    if actual == expected:
        print(f"OK: clingo gate matches python gate ({len(expected)} combos).")
        for params in CURATED:
            generate(params)
        print("OK: generated stories passed.")
        return 0
    print("MISMATCH between clingo and Python.")
    print("only in clingo:", sorted(actual - expected))
    print("only in python:", sorted(expected - actual))
    return 1


CURATED = [
    StoryParams("Luna", "Mina", "fox", "otter", "gate_reconciliation", 0),
    StoryParams("Pip", "Nori", "rabbit", "badger", "whispering_pass", 1),
    StoryParams("Taro", "Jasper", "raccoon", "deer", "garden_of_glass", 2),
]


def build_story_from_args(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    seen = set()
    index = 0
    while len(samples) < args.n:
        params = resolve_params(args, random.Random(base_seed + index))
        params.seed = base_seed + index
        index += 1
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combinations.")
        for combo in combos[:20]:
            print(combo)
        return

    samples = [generate(params) for params in CURATED] if args.all else build_story_from_args(args)
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
