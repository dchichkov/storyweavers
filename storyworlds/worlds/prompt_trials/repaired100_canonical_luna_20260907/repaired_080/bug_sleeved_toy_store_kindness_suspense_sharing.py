#!/usr/bin/env python3
"""
Standalone storyworld: a bug, a sleeved toy, kindness, suspense, and sharing.

A small toy-store story in which a child finds a tiny bug near a sleeved toy,
chooses kindness over panic, and shares a careful solution with the shopkeeper.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class ToyStore:
    name: str = "Button & Bell Toys"
    place: str = "the toy store"
    counter: str = "the wooden counter"
    aisle: str = "the stuffed-animal aisle"


@dataclass
class World:
    store: ToyStore
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            raise StoryError(f"Unknown entity: {eid}")
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    child_name: str
    keeper_name: str
    toy_name: str = "Moon-Mouse"
    scenario: int = 0
    opening: int = 0
    suspense: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


CHILD_NAMES = ["Luna", "Milo", "Nia", "Tessa", "Owen", "Priya", "Sam", "Wren"]
KEEPER_NAMES = ["Ms. Ada", "Mr. Ben", "Rosa", "Theo", "June", "Mara"]
TOY_NAMES = ["Moon-Mouse", "Button Bear", "Cloud Fox", "Pocket Robot", "Sunny Pup"]

SCENARIOS = [
    {
        "sleeve": "a clear paper sleeve",
        "toy_detail": "a tiny silver bell sewn under its paw",
        "bug": "a little green beetle",
        "hiding_place": "beneath the edge of the display shelf",
        "clue": "a neat trail of crumbs led from the store's open back door",
        "kind_action": "covered the beetle with a cup and slid a postcard underneath it",
        "sharing": "showed the shopkeeper the crumbs and carried the beetle to a safe patch of clover outside",
        "result": "the toy stayed clean, and the beetle crawled into the grass",
        "image": "the bug disappeared among clover leaves while the sleeved toy's silver bell gave one soft chime",
        "lesson": "Kindness can make room for small creatures and careful people at the same time.",
    },
    {
        "sleeve": "a blue cardboard sleeve",
        "toy_detail": "a stitched orange scarf",
        "bug": "a sleepy ladybug",
        "hiding_place": "behind a row of wooden trains",
        "clue": "warm sunlight fell in a bright stripe beside the front window",
        "kind_action": "asked everyone to pause and placed a folded receipt beside the ladybug",
        "sharing": "shared the clue with the keeper and guided the ladybug onto a leaf from the window box",
        "result": "the ladybug left the toy safely and rested in the warm light",
        "image": "the ladybug opened its red wings beside the window while the sleeved toy waited neatly on its hook",
        "lesson": "Sharing what you notice can turn suspense into a gentle plan.",
    },
    {
        "sleeve": "a red cloth sleeve",
        "toy_detail": "two floppy ears tied with yellow thread",
        "bug": "a tiny brown moth",
        "hiding_place": "inside the shadow of the wrapping-paper basket",
        "clue": "the moth kept turning toward the store's round lamp",
        "kind_action": "dimmed the lamp with the keeper and held a small box open near the basket",
        "sharing": "explained the moth's movement to another customer and carried the box to the evening garden",
        "result": "the moth flew away without anyone touching its delicate wings",
        "image": "the moth circled the garden lamp while the red-sleeved toy smiled from the quiet counter",
        "lesson": "Kindness grows when a person shares both space and attention.",
    },
    {
        "sleeve": "a striped plastic sleeve",
        "toy_detail": "a pocket filled with pretend stars",
        "bug": "a black-and-gold beetle",
        "hiding_place": "under a low basket of building blocks",
        "clue": "one block had a fresh speck of garden soil on it",
        "kind_action": "knelt down, warned the nearby children, and made a calm path with two blocks",
        "sharing": "shared the soil clue with the keeper and helped move the basket away from the door",
        "result": "the beetle found the open doorway while the children watched quietly",
        "image": "the beetle crossed the last block and vanished beneath the store's flowerpot",
        "lesson": "When suspense makes a moment feel big, kindness helps everyone move carefully.",
    },
    {
        "sleeve": "a soft yellow sleeve",
        "toy_detail": "a button nose that shone like a penny",
        "bug": "a small blue fly",
        "hiding_place": "near the ribbon spool at the wrapping station",
        "clue": "the fly followed the smell of a sweet fruit sticker",
        "kind_action": "moved the sticker away and opened the back window instead of swatting",
        "sharing": "told the keeper why the window would help and invited a waiting child to watch from a safe distance",
        "result": "the fly buzzed out, and the wrapping table became calm again",
        "image": "sunlight rested on the yellow sleeve as the last blue blur zipped toward the window",
        "lesson": "A shared explanation can be kinder than a quick reaction.",
    },
]

OPENINGS = [
    "On a quiet Saturday morning, the toy store smelled of cardboard, wool, and cinnamon from the bakery next door.",
    "Just after the bell above the toy-store door rang, sunlight made bright squares across the floor.",
    "Luna visited the toy store on an ordinary afternoon when nothing seemed likely to surprise anyone.",
    "The toy store was between two busy moments, so even the wooden trains seemed to be listening.",
    "Rain tapped the toy-store window while customers browsed slowly through the colorful aisles.",
]

SUSPENSE_LINES = [
    "Then something moved where the toys were supposed to stay still.",
    "For one long second, nobody could tell whether the small shape was a loose thread or a living thing.",
    "The store became very quiet, and the little movement seemed louder than the doorbell.",
    "Everyone leaned closer, but the shadow slipped away before anyone could name it.",
    "A tiny rustle came from below the display, and the waiting made the moment feel enormous.",
]

DIALOGUES = [
    '"I see a bug," said {child}. "Can we help it without hurting it?"',
    '"Please wait," {child} told the keeper. "Let us look before we touch anything."',
    '"It might be scared too," said {child}. "I can share what I noticed."',
    '"Do you think the clue can show us the way outside?" asked {child}.',
    '"We can make a little path," {child} said. "Everyone can give it room."',
]

ENDINGS = [
    "The next customer bought a puzzle, and the store returned to its gentle Saturday hum.",
    "Before leaving, the children made a tiny sign that said, “Small visitors need kindness too.”",
    "The keeper laughed softly and put a clean leaf beside the door for the next little traveler.",
    "No one had to be loud or quick; the careful plan had been enough.",
    "At closing time, the toy store felt ordinary again, which was another way of saying safe.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a slice-of-life toy-store story about kindness, suspense, and sharing."
    )
    parser.add_argument("--child-name")
    parser.add_argument("--keeper-name")
    parser.add_argument("--toy-name", default=None)
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
    return StoryParams(
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        keeper_name=args.keeper_name or rng.choice(KEEPER_NAMES),
        toy_name=args.toy_name or rng.choice(TOY_NAMES),
        scenario=rng.randrange(len(SCENARIOS)),
        opening=rng.randrange(len(OPENINGS)),
        suspense=rng.randrange(len(SUSPENSE_LINES)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    world = World(ToyStore())
    child = world.add(
        Entity(
            id="Child",
            kind="character",
            type="person",
            label=params.child_name,
            location="aisle",
            memes={"kindness": 0.0, "curiosity": 1.0},
        )
    )
    keeper = world.add(
        Entity(
            id="Keeper",
            kind="character",
            type="person",
            label=params.keeper_name,
            location="counter",
            memes={"patience": 1.0},
        )
    )
    toy = world.add(
        Entity(
            id="SleevedToy",
            type="toy",
            label=params.toy_name,
            location="display shelf",
            meters={"protected": 1.0},
        )
    )
    bug = world.add(
        Entity(
            id="Bug",
            type="bug",
            label="the bug",
            location="display shelf",
            meters={"safe": 0.0, "outside": 0.0},
            memes={"fear": 1.0},
        )
    )
    world.facts.update(child=child, keeper=keeper, toy=toy, bug=bug, params=params)
    return world


def _move_bug_outside(world: World) -> None:
    bug = world.get("Bug")
    if ("bug_outside",) in world.fired:
        return
    bug.location = "flowerpot outside"
    bug.meters["safe"] = 1.0
    bug.meters["outside"] = 1.0
    bug.memes["fear"] = 0.0
    world.fired.add(("bug_outside",))


def propagate(world: World) -> None:
    child = world.get("Child")
    bug = world.get("Bug")
    if child.memes.get("kindness", 0.0) >= THRESHOLD and bug.meters.get("outside", 0.0) >= THRESHOLD:
        child.memes["sharing"] = 1.0


def tell(world: World) -> None:
    params: StoryParams = world.facts["params"]
    child = world.get("Child")
    keeper = world.get("Keeper")
    toy = world.get("SleevedToy")
    bug = world.get("Bug")
    scenario = SCENARIOS[params.scenario % len(SCENARIOS)]
    world.facts["scenario"] = scenario

    world.say(OPENINGS[params.opening % len(OPENINGS)])
    world.say(
        f"{child.label} was looking at {toy.label}, a toy with {scenario['toy_detail']}, "
        f"when {child.pronoun if hasattr(child, 'pronoun') else 'they'} noticed the toy's {scenario['sleeve']}."
    )
    world.say(
        f"The sleeve kept the toy clean on the display shelf, but {scenario['bug']} was {scenario['hiding_place']}."
    )

    world.para()
    bug.meters["noticed"] = 1.0
    world.say(SUSPENSE_LINES[params.suspense % len(SUSPENSE_LINES)])
    world.say(
        f"{child.label} held still. The bug moved once, then stopped beside the sleeve."
    )
    world.say(
        DIALOGUES[params.dialogue % len(DIALOGUES)].format(child=child.label, keeper=keeper.label)
    )
    world.say(
        f"{keeper.label} came from the counter, and together they watched without poking the bug. "
        f"The first clue was that {scenario['clue']}."
    )

    world.para()
    child.memes["kindness"] = 1.0
    world.say(
        f"Instead of swatting or grabbing, {child.label} {scenario['kind_action']}. "
        f"{keeper.label} held the toy shelf steady so the sleeved toy would not fall."
    )
    world.say(
        f"They shared the clue with one another and made a plan: {child.label} would give the bug room, "
        f"while {keeper.label} opened a safe route."
    )
    world.say(f"Then they {scenario['sharing']}.")
    _move_bug_outside(world)
    toy.meters["protected"] = 1.0
    propagate(world)
    world.say(f"As a result, {scenario['result']}.")

    world.para()
    world.say(
        f"The suspense melted away because kindness had guided their hands, and sharing had helped everyone understand what to do."
    )
    world.say(f"In the final picture, {scenario['image']}.")
    world.say(ENDINGS[params.ending % len(ENDINGS)])
    world.facts.update(
        resolved=True,
        clue=scenario["clue"],
        kindness_action=scenario["kind_action"],
        sharing_action=scenario["sharing"],
        ending_image=scenario["image"],
    )


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write a slice-of-life story for children about {params.child_name} finding a bug near a sleeved toy in a toy store.",
        f"Tell a gentle toy-store story using kindness, suspense, and sharing. The bug's clue is: {scenario['clue']}.",
        f"Show how {params.child_name} and the shopkeeper solve the bug's problem without hurting it or damaging {params.toy_name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    toy = world.get("SleevedToy")
    bug = world.get("Bug")
    return [
        QAItem(
            question="Where did the story take place?",
            answer="The story took place in a toy store, among shelves of toys and a wrapping counter.",
        ),
        QAItem(
            question=f"What did {params.child_name} notice?",
            answer=f"{params.child_name} noticed {scenario['bug']} near {toy.label}, which was protected by {scenario['sleeve']}.",
        ),
        QAItem(
            question="What clue helped explain why the bug was there?",
            answer=f"The clue was that {scenario['clue']}. This helped the child and the keeper make a calm plan.",
        ),
        QAItem(
            question=f"How did {params.child_name} show kindness?",
            answer=f"{params.child_name} showed kindness when {scenario['kind_action']}. The action protected the bug instead of frightening or hurting it.",
        ),
        QAItem(
            question="How did sharing help solve the problem?",
            answer=f"The child and the keeper shared what they noticed, and then they {scenario['sharing']}.",
        ),
        QAItem(
            question="How did the ending show that the suspense was over?",
            answer=f"In the ending, {scenario['image']}. The bug was safe, and the sleeved toy remained protected.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bug?",
            answer="A bug is a small living creature, such as a beetle, ladybug, fly, or moth.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means treating people and living things with care and trying not to cause harm.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving information, space, objects, or help so others can take part or understand.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
        QAItem(
            question="Why might a toy have a sleeve?",
            answer="A toy might have a sleeve to keep it clean, protected, or ready for display.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        details = []
        if entity.location:
            details.append(f"location={entity.location}")
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {' '.join(details) if details else '(quiet)'}")
    return "\n".join(lines)


ASP_RULES = r"""
kind_action :- kindness, bug_noticed.
shared_plan :- kind_action, sharing.
safe_bug :- shared_plan, outside.
protected_toy :- sleeved, safe_bug.
resolved :- safe_bug, protected_toy.
#show kind_action/0.
#show shared_plan/0.
#show safe_bug/0.
#show protected_toy/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("kindness"),
            asp.fact("bug_noticed"),
            asp.fact("sharing"),
            asp.fact("sleeved"),
            asp.fact("outside"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    required = {"kind_action/0", "shared_plan/0", "safe_bug/0", "protected_toy/0", "resolved/0"}
    model = asp.one_model(asp_program())
    actual = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    if not required.issubset(actual):
        missing = ", ".join(sorted(required - actual))
        raise StoryError(f"ASP parity failed; missing atoms: {missing}")
    sample = generate(
        StoryParams(
            child_name="Luna",
            keeper_name="Ms. Ada",
            toy_name="Moon-Mouse",
            scenario=0,
            opening=0,
            suspense=0,
            dialogue=0,
            ending=0,
        )
    )
    required_phrases = ["bug", "sleeved", "kindness", "sharing"]
    lowered = sample.story.lower()
    missing_text = [phrase for phrase in required_phrases if phrase not in lowered]
    if missing_text:
        raise StoryError(f"Generated story parity failed; missing words: {', '.join(missing_text)}")
    print("OK: ASP twin is present, parity facts hold, and a generated story was exercised.")
    return 0


def asp_valid() -> str:
    return asp_program()


CURATED = [
    StoryParams(
        child_name="Luna",
        keeper_name="Ms. Ada",
        toy_name="Moon-Mouse",
        scenario=0,
        opening=0,
        suspense=0,
        dialogue=0,
        ending=0,
    ),
    StoryParams(
        child_name="Milo",
        keeper_name="Rosa",
        toy_name="Cloud Fox",
        scenario=1,
        opening=2,
        suspense=3,
        dialogue=1,
        ending=2,
    ),
    StoryParams(
        child_name="Nia",
        keeper_name="Theo",
        toy_name="Pocket Robot",
        scenario=3,
        opening=4,
        suspense=1,
        dialogue=4,
        ending=4,
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_valid())
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        target = max(0, args.n)
        while len(samples) < target and index < max(target * 50, 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.child_name} at {sample.params.toy_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
