#!/usr/bin/env python3
"""
A heartwarming dining-room quest about deciding with care.

Darling is a small golden dog who must choose whether to chase a dropped silver
spoon or help finish setting the table before Grandma arrives. Her inner
monologue, a little suspense, and a loving choice turn an ordinary dining room
into a brave adventure.
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    name: str
    helper: str
    quest: str
    suspense: str
    monologue: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Quest:
    opening: str
    danger: str
    clue: str
    action: str
    result: str


@dataclass(frozen=True)
class Suspense:
    warning: str
    wait: str
    reveal: str


@dataclass(frozen=True)
class InnerMonologue:
    thought: str
    decision: str
    lesson: str


QUESTS = {
    "silver_spoon": Quest(
        opening="a silver spoon slipped from the table and skittered beneath the sideboard",
        danger="A candle flame trembled near the tablecloth, and the spoon was resting close to the dangling cloth",
        clue="a cool draft whispered from the open window",
        action="nudged the spoon away from the cloth, then barked toward the kitchen",
        result="the spoon was safely retrieved and the candle was moved well back from the tablecloth",
    ),
    "missing_napkin": Quest(
        opening="the last blue napkin vanished just before the family supper",
        danger="A gust from the open window was lifting the napkin toward a bowl of warm soup",
        clue="one corner of blue cloth fluttered beneath the piano bench",
        action="crawled beneath the bench and pulled the napkin free with careful teeth",
        result="the napkin was rescued before it could fall into the soup",
    ),
    "rolling_apple": Quest(
        opening="a red apple rolled beneath the long dining table",
        danger="It was heading toward the doorway, where a visiting toddler might step on it",
        clue="a bright red shine appeared between two chair legs",
        action="blocked the apple with one paw and called the nearest grown-up with a soft bark",
        result="the apple was placed in the fruit bowl before anyone could stumble",
    ),
    "lost_ring": Quest(
        opening="a tiny ring disappeared beside the place where Grandma would sit",
        danger="The ring might be swept away when the room was tidied after dinner",
        clue="something glittered under the edge of the table runner",
        action="held still and pointed with her nose until the missing ring was noticed",
        result="the ring was returned to Grandma's hand before the first guest arrived",
    ),
    "fallen_card": Quest(
        opening="a handmade welcome card slipped from the mantel",
        danger="A passing draft was carrying it toward the wet footprints by the door",
        clue="the card's yellow corner peeked from behind a chair",
        action="caught the card gently and carried it to the dry center of the table",
        result="the welcome card stayed bright and ready for the family's guest",
    ),
}

SUSPENSES = {
    "clock": Suspense(
        warning="The old clock ticked loudly while the room waited.",
        wait="For one long moment, no one knew whether the next sound would be a crash or a bark.",
        reveal="Then the clock gave a gentle chime, and the danger was gone.",
    ),
    "rain": Suspense(
        warning="Rain began tapping the windows like tiny impatient fingers.",
        wait="The family held their breath as the wind pushed once more at the curtains.",
        reveal="The rain softened just as the room became safe.",
    ),
    "footsteps": Suspense(
        warning="Soft footsteps sounded in the hall, growing closer.",
        wait="Darling had only a heartbeat to decide before the visitor opened the door.",
        reveal="The door opened onto a smiling Grandma, not a frightening surprise.",
    ),
    "candle": Suspense(
        warning="The candle made a little golden pool that wavered across the plates.",
        wait="Darling watched the flame lean toward the tablecloth.",
        reveal="The flame stood straight again after the grown-up moved it.",
    ),
    "silence": Suspense(
        warning="The dining room became so quiet that Darling could hear her own paws.",
        wait="She waited, listening for the small clue hidden beneath the larger sounds.",
        reveal="A tiny scrape answered from beneath the furniture.",
    ),
}

MONOLOGUES = {
    "kind": InnerMonologue(
        thought="I want the shiny thing, but everyone needs a safe table.",
        decision="Darling decided that helping first would make the celebration brighter.",
        lesson="She learned that a loving choice can be brave even when nobody is clapping yet.",
    ),
    "patient": InnerMonologue(
        thought="If I hurry, I may make the trouble bigger. I can be gentle.",
        decision="Darling decided to wait, watch, and use the smallest helpful movement.",
        lesson="She learned that patience is not standing still; it is choosing carefully.",
    ),
    "courage": InnerMonologue(
        thought="The room feels large, but the people I love are close by.",
        decision="Darling decided to make one clear sound and keep trying until someone heard.",
        lesson="She learned that courage can sound like a small bark in a quiet room.",
    ),
    "sharing": InnerMonologue(
        thought="This quest is not only mine. Someone else may know the safest answer.",
        decision="Darling decided to ask for help instead of pretending she could do everything alone.",
        lesson="She learned that sharing a problem gives love more hands to hold it.",
    ),
    "trust": InnerMonologue(
        thought="I can trust my careful eyes, and I can trust my family to listen.",
        decision="Darling decided to point out the danger and let the grown-ups finish the rescue.",
        lesson="She learned that trust grows when everyone does the part they can do well.",
    ),
}

ENDINGS = {
    "candlelight": "When supper began, candlelight shone on Darling's golden ears as Grandma scratched her chin.",
    "warm_roll": "The baker's warm roll was divided, and Darling received the tiniest piece at the table's edge.",
    "blue_napkin": "The rescued blue napkin rested beneath a vase, bright as a little piece of sky.",
    "chair": "Darling curled beneath Grandma's chair, where every happy voice felt close.",
    "toast": "Before the first toast, everyone thanked Darling for helping make the room safe.",
    "window": "The rain cleared from the window, and the dining room glowed like a welcoming heart.",
}

NAMES = ["Darling", "Pip", "Honey", "Mabel", "Sunny", "Tilly"]
HELPERS = ["her mother", "her grandfather", "her aunt", "her older brother"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming dining-room quest storyworld.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--suspense", choices=SUSPENSES)
    parser.add_argument("--monologue", choices=MONOLOGUES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    chosen = {
        "name": args.name or rng.choice(NAMES),
        "helper": args.helper or rng.choice(HELPERS),
        "quest": args.quest or rng.choice(tuple(QUESTS)),
        "suspense": args.suspense or rng.choice(tuple(SUSPENSES)),
        "monologue": args.monologue or rng.choice(tuple(MONOLOGUES)),
        "ending": args.ending or rng.choice(tuple(ENDINGS)),
    }
    return StoryParams(**chosen)


def tell(params: StoryParams) -> World:
    quest = QUESTS[params.quest]
    suspense = SUSPENSES[params.suspense]
    monologue = MONOLOGUES[params.monologue]

    world = World()
    darling = world.add(Entity("darling", "character", "dog", params.name, "dining room"))
    helper = world.add(Entity("helper", "character", "person", params.helper, "dining room"))
    table = world.add(Entity("table", "furniture", "table", "the dining table", "dining room"))
    candle = world.add(Entity("candle", "object", "candle", "the candle", "dining room"))

    world.facts.update(
        darling=darling,
        helper=helper,
        table=table,
        candle=candle,
        quest=quest,
        suspense=suspense,
        monologue=monologue,
        resolved=False,
    )

    darling.meters["curiosity"] = 1.0
    darling.memes["love"] = 1.0
    table.meters["stability"] = 1.0

    world.say(
        f"One evening, {params.name} waited in the dining room while {params.helper} "
        "set the table for a very special supper."
    )
    world.say(
        f"The plates gleamed, the chairs stood straight, and a small candle glowed "
        "near the center of the table."
    )
    world.say(f"Then {quest.opening}.")
    world.para()

    world.say(quest.danger + ".")
    world.say(suspense.warning)
    world.say(suspense.wait)
    world.say(f"{params.name} thought, “{monologue.thought}”")
    world.say(f"{params.name} also noticed that {quest.clue}.")
    world.para()

    darling.memes["worry"] = 1.0
    darling.memes["care"] = 1.0
    world.say(monologue.decision)
    world.say(f"She {quest.action}.")
    world.say(f"{params.helper.capitalize()} followed her signal and helped.")
    world.say(f"Together, they made sure that {quest.result}.")
    world.say(suspense.reveal)
    world.para()

    darling.memes["worry"] = 0.0
    darling.memes["relief"] = 1.0
    world.facts["resolved"] = True
    world.facts["changed_fact"] = quest.result
    world.say(
        f"{params.helper.capitalize()} hugged {params.name} and said, "
        f"“You helped us decide what mattered, darling.”"
    )
    world.say(monologue.lesson)
    world.say(ENDINGS[params.ending])
    world.say("The dining room filled with warm voices, and Darling felt exactly where she belonged.")
    return world


def generation_prompts(world: World) -> list[str]:
    darling = world.facts["darling"]
    quest = world.facts["quest"]
    return [
        f"Write a heartwarming dining-room quest in which {darling.label} must decide how to help.",
        f"Include an inner monologue as {darling.label} faces this danger: {quest.danger}.",
        "Build suspense with a small household danger, then end with a loving family image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    darling = world.facts["darling"]
    helper = world.facts["helper"]
    quest = world.facts["quest"]
    monologue = world.facts["monologue"]
    return [
        QAItem(
            question=f"What quest did {darling.label} face in the dining room?",
            answer=f"{darling.label} had to respond when {quest.opening}. The danger was that {quest.danger.lower()}.",
        ),
        QAItem(
            question=f"What did {darling.label} think before making a decision?",
            answer=f"{darling.label} thought, “{monologue.thought}” She was worried, but she also cared about keeping the family safe.",
        ),
        QAItem(
            question=f"How did {darling.label} solve the problem?",
            answer=f"{darling.label} {quest.action}. With help from {helper.label}, {quest.result}.",
        ),
        QAItem(
            question="What did Darling learn?",
            answer=monologue.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dining room?",
            answer="A dining room is a room where people gather to eat meals together.",
        ),
        QAItem(
            question="Why should a candle be kept away from a tablecloth?",
            answer="A candle should be kept away from a tablecloth because an open flame can set cloth on fire.",
        ),
        QAItem(
            question="Why is asking for help a good choice?",
            answer="Asking for help is good because another person may have the strength, knowledge, or careful view needed to solve a problem safely.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type}, location={entity.location}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')}")
    lines.append(f"  changed_fact={world.facts.get('changed_fact')}")
    return "\n".join(lines)


ASP_RULES = r"""
place(dining_room).
feature(quest).
feature(inner_monologue).
feature(suspense).
style(heartwarming).
valid_domain(dining_room,quest,inner_monologue,suspense,heartwarming).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "dining_room"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "suspense"),
            asp.fact("style", "heartwarming"),
        ]
    )


def asp_program(show: str = "#show valid_domain/5.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_domain() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_domain"))


def valid_domain() -> set[tuple]:
    return {("dining_room", "quest", "inner_monologue", "suspense", "heartwarming")}


def asp_verify() -> int:
    py = valid_domain()
    clingo_values = asp_valid_domain()
    if py == clingo_values:
        print("OK: ASP and Python domain gates match.")
        sample = generate(
            StoryParams(
                name="Darling",
                helper="her mother",
                quest="silver_spoon",
                suspense="candle",
                monologue="kind",
                ending="candlelight",
            )
        )
        if sample.story and sample.world and sample.world.facts["resolved"]:
            print("OK: generated story resolves its quest.")
            return 0
        print("FAIL: generated story did not resolve.")
        return 1
    print("MISMATCH between ASP and Python domain gates.")
    print("Python:", sorted(py))
    print("ASP:", sorted(clingo_values))
    return 1


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


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


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
        print()
        print(dump_trace(sample.world))
    if qa:
        for prompt in sample.prompts:
            print()
            print(f"[Prompt] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print()
            print(show_qa_item(item))


CURATED = [
    StoryParams(
        name="Darling",
        helper="her mother",
        quest="silver_spoon",
        suspense="candle",
        monologue="kind",
        ending="candlelight",
    ),
    StoryParams(
        name="Honey",
        helper="her grandfather",
        quest="lost_ring",
        suspense="footsteps",
        monologue="patient",
        ending="chair",
    ),
    StoryParams(
        name="Mabel",
        helper="her aunt",
        quest="fallen_card",
        suspense="rain",
        monologue="sharing",
        ending="window",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("Compatible domain:")
        for item in sorted(asp_valid_domain()):
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
            seed = base_seed + index
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            params.seed = seed
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
