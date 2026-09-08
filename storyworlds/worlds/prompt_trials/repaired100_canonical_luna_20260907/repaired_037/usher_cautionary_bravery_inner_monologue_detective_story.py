#!/usr/bin/env python3
"""
A small detective-story world about an usher, a missing brass key, careful
bravery, and an inner voice that learns to separate clues from guesses.
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

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    place: str
    usher_name: str
    child_name: str
    seed: Optional[int] = None
    case: int = 0
    opening: int = 0
    thought: int = 0
    warning: int = 0
    discovery: int = 0


SETTINGS = {
    "theater": Setting("the old theater", {"usher", "key", "aisle"}),
    "museum": Setting("the town museum", {"usher", "key", "gallery"}),
    "concert_hall": Setting("the concert hall", {"usher", "key", "balcony"}),
}

USHER_NAMES = ["Luna", "Mara", "Iris", "Nell", "June", "Tessa"]
CHILD_NAMES = ["Pip", "Theo", "Mina", "Ollie", "Bea", "Sam"]

CASES = [
    {
        "clue": "a single blue feather beside the locked costume-room door",
        "guess": "someone had slipped away with the theater's oldest costume",
        "urge": "push the door open and chase whoever had left the feather",
        "sound": "a faint knock came from behind the door",
        "evidence": "the feather was dry, but a row of damp footprints led toward the side entrance",
        "test": "They kept the door closed, marked the feather with a paper ticket, and checked the footprints from the public aisle.",
        "truth": "a stage pigeon had dropped the feather, while the damp footprints belonged to the custodian carrying a mop",
        "repair": "The custodian dried the floor, and the usher returned the feather to a small box of harmless stage props.",
        "lesson": "a clue can be real without proving the scariest guess",
        "ending": "When the last lamp dimmed, the blue feather rested safely in its box beneath the theater's golden sign.",
    },
    {
        "clue": "a brass key glinting under the third row",
        "guess": "a hidden thief had dropped the key while escaping",
        "urge": "crawl beneath the seats and grab it before the thief returned",
        "sound": "the balcony railing gave a sharp little click",
        "evidence": "the key wore a paper tag marked STORAGE, and dust around it was undisturbed",
        "test": "They stood in the aisle, called for the manager, and used a broom to draw the key into the light.",
        "truth": "the manager had misplaced the storage key during the afternoon cleanup",
        "repair": "The manager checked the tag, locked the storage room, and thanked the usher for not crawling into the dark.",
        "lesson": "bravery can mean choosing a safe method instead of making a fast move",
        "ending": "The brass key hung on its proper hook while the usher swept a bright, clear aisle for the morning crowd.",
    },
    {
        "clue": "three silver tickets arranged in a crooked line near the gallery",
        "guess": "a secret detective had left a code",
        "urge": "follow the tickets alone into the closed gallery",
        "sound": "a curtain rustled where no audience sat",
        "evidence": "all three tickets had the same torn corner, and a draft slipped beneath the gallery door",
        "test": "They photographed the line, stayed beside the open entrance, and asked the caretaker about the draft.",
        "truth": "wind from a loose vent had pushed tickets from a recycling basket",
        "repair": "The caretaker fixed the vent and placed the tickets in the recycling bin.",
        "lesson": "a brave detective checks the whole scene before entering a risky place",
        "ending": "The repaired vent was quiet, and the silver tickets became a neat stack instead of a secret code.",
    },
    {
        "clue": "a red thread caught on the velvet rope",
        "guess": "a masked visitor had escaped through the side hall",
        "urge": "run after the thread before the trail vanished",
        "sound": "a doorknob turned once and stopped",
        "evidence": "the thread matched the repair cloth on a nearby seat, and the rope's clasp was loose",
        "test": "They held the rope steady, called to the manager, and examined the cloth without crossing the boundary.",
        "truth": "the loose rope clasp had pulled a thread from the seat-repair cloth",
        "repair": "The manager tightened the clasp and stitched the seat while the usher kept visitors on the safe path.",
        "lesson": "respecting a boundary helps everyone investigate without creating a new problem",
        "ending": "The velvet rope stood straight again, and the red thread disappeared into a careful stitch.",
    },
]

OPENINGS = [
    "The evening crowd had just settled when {usher}, the theater usher, noticed something unusual in {place}.",
    "Rain tapped the windows of {place} as {usher} checked the aisles before closing time.",
    "At the start of the final show, {usher} carried a flashlight through {place} and watched for anything out of place.",
    "The house lights glowed softly in {place}. Usher {usher} was helping {child} find a quiet seat when a mystery appeared.",
    "Near the end of the performance, {usher} and {child} heard the building settle around {place}.",
]

THOUGHTS = [
    "Luna's inner voice whispered, 'A strange clue is a question, not an answer.'",
    "Inside, Luna thought, 'My fear is loud, but the evidence can speak more clearly.'",
    "Luna told herself, 'Being brave does not mean rushing toward danger. It means making a wise next step.'",
    "Her inner detective murmured, 'Notice first. Decide second.'",
    "Luna breathed slowly and thought, 'I can feel worried and still act carefully.'",
]

WARNINGS = [
    '"Stay beside me," {usher} said. "We will investigate, but we will not enter a dark place alone."',
    '"A real detective protects people and clues," {usher} explained. "Let us ask for help before we touch anything."',
    '"Courage is not chasing every shadow," said {usher}. "Courage is choosing the safe plan."',
    '"We can be curious from the aisle," {usher} told {child}. "The boundary stays where it is."',
    '"First we observe, then we report, then we test," {usher} said.',
]

DISCOVERIES = [
    "The two detectives compared the clue with the nearby objects and wrote down only what they could truly see.",
    "They counted three quiet breaths, then looked again without adding any new guesses.",
    "They used the flashlight from the open aisle, keeping their hands and feet away from the uncertain place.",
    "They asked the nearest grown-up what had been moved during the afternoon.",
    "They listened once more, but they did not let the strange sound choose their actions.",
]


ASP_RULES = r"""
#show valid/2.
setting(theater). setting(museum). setting(concert_hall).
affords(theater,usher). affords(theater,key). affords(theater,aisle).
affords(museum,usher). affords(museum,key). affords(museum,gallery).
affords(concert_hall,usher). affords(concert_hall,key). affords(concert_hall,balcony).
valid(P,Thing) :- setting(P), affords(P,Thing).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", name, affordance))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, thing) for place, setting in SETTINGS.items() for thing in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo - py))
    print("  only in python:", sorted(py - clingo))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}.")
    if not params.usher_name.strip() or not params.child_name.strip():
        raise StoryError("The usher and child must both have names.")
    if params.usher_name == params.child_name:
        raise StoryError("The usher and child must have different names.")

    setting = SETTINGS[params.place]
    case = CASES[params.case % len(CASES)]
    world = StoryState(setting)

    usher = world.add(Entity(
        params.usher_name, "character", "usher",
        traits=["observant", "responsible"],
        meters={"distance_from_risk": 1.0},
        memes={"caution": 1.0, "bravery": 0.5},
    ))
    child = world.add(Entity(
        params.child_name, "character", "child",
        traits=["curious"],
        meters={"distance_from_risk": 1.0},
        memes={"curiosity": 1.0},
    ))
    manager = world.add(Entity(
        "Manager", "character", "manager",
        traits=["helpful"],
        memes={"trust": 1.0},
    ))
    clue = world.add(Entity(
        "clue", "thing", "evidence",
        label=case["clue"],
        owner=None,
        meters={"distance_from_risk": 0.8},
        memes={"uncertainty": 1.0},
    ))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        usher=usher.id, child=child.id, place=setting.place
    ))
    world.say(f"Near the aisle, they found {case['clue']}.")
    world.say(
        f'"Maybe {case["guess"]}," {child.id} whispered. '
        f'"Maybe," {usher.id} replied, "but a detective needs more than a guess."'
    )

    world.para()
    world.say(f"Then {case['sound']}. {child.id} wanted to {case['urge']}.")
    world.say(WARNINGS[params.warning % len(WARNINGS)].format(
        usher=usher.id, child=child.id
    ))
    world.say(THOUGHTS[params.thought % len(THOUGHTS)].replace("Luna", usher.id))
    world.say(DISCOVERIES[params.discovery % len(DISCOVERIES)])
    world.say(f"From the safe place, they noticed that {case['evidence']}.")
    world.say(case["test"])
    world.facts["tension"] = True
    world.facts["danger_avoided"] = True

    world.para()
    world.say(
        f"{manager.id} arrived after {usher.id} called for help. "
        f'"You did the right thing by staying back," {manager.id} said.'
    )
    world.say(f'"The evidence points to this: {case["truth"]}."')
    world.say(case["repair"])
    world.say(
        f'"I felt scared, but I still made a careful choice," {child.id} said. '
        f'"That is brave," {usher.id} answered.'
    )
    world.say(
        f"{case['lesson'].capitalize()}. "
        f"{usher.id} placed the clue in its proper record and checked the aisle once more."
    )
    world.say(case["ending"])

    world.facts.update(
        usher=usher,
        child=child,
        manager=manager,
        clue=clue,
        case=case,
        place=setting.place,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a detective story about usher {f['usher'].id} investigating {f['case']['clue']}.",
        f"Tell a cautionary story in which {f['usher'].id} shows bravery by choosing a safe investigation.",
        f"Write a child-facing mystery at {f['place']} with dialogue, inner monologue, and a peaceful resolution.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    usher = f["usher"].id
    child = f["child"].id
    case = f["case"]
    return [
        QAItem(
            question=f"Who investigated the mystery?",
            answer=f"{usher}, the usher, investigated it with {child}. {usher} kept the investigation careful and safe.",
        ),
        QAItem(
            question=f"What did {child} first want to do?",
            answer=f"{child} wanted to {case['urge']}. {usher} stopped the risky plan and suggested observing from a safe place.",
        ),
        QAItem(
            question="What evidence helped solve the case?",
            answer=f"They noticed that {case['evidence']}. That clue showed that {case['truth']}.",
        ),
        QAItem(
            question="How did the characters show bravery?",
            answer=f"They showed bravery by staying calm, asking for help, and testing the clue safely instead of rushing into danger.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=f"It taught that {case['lesson']}. Careful bravery helped protect both the people and the evidence.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What does an usher do?",
            answer="An usher helps people find seats, keeps walkways orderly, and helps a venue stay welcoming and safe.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a piece of information or evidence that helps someone understand what happened.",
        ),
        QAItem(
            question="What is brave caution?",
            answer="Brave caution means facing a problem while choosing careful actions that reduce danger.",
        ),
    ]


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


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) "
            f"traits={entity.traits} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    usher_name = args.name or rng.choice(USHER_NAMES)
    child_name = args.child or rng.choice(CHILD_NAMES)
    if usher_name == child_name:
        alternatives = [name for name in CHILD_NAMES if name != usher_name]
        child_name = rng.choice(alternatives)
    return StoryParams(
        place=place,
        usher_name=usher_name,
        child_name=child_name,
        case=rng.randrange(len(CASES)),
        opening=rng.randrange(len(OPENINGS)),
        thought=rng.randrange(len(THOUGHTS)),
        warning=rng.randrange(len(WARNINGS)),
        discovery=rng.randrange(len(DISCOVERIES)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective story world about an usher, caution, and bravery."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--child")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        values = asp_valid()
        print(f"{len(values)} valid combinations:\n")
        for place, affordance in values:
            print(f"  {place:14} {affordance}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                usher_name=f"{place.title()}Usher",
                child_name=f"{place.title()}Child",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            attempt += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

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
