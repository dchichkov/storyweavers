#!/usr/bin/env python3
"""
A small whodunit storyworld about a pup, a missing sequence, and a useful flashback.

The world tracks a child detective, a pup, numbered clue cards, a missing bell,
and emotional changes from confusion to confidence.  The mystery is resolved
when a flashback reveals the pup's harmless role in hiding the final clue.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAME_POOL = ["Luna", "Milo", "Nina", "Theo", "Pip", "Zara", "Ivy", "Owen"]
PUP_POOL = ["Biscuit", "Pepper", "Waffles", "Teddy", "Clover", "Button"]
PLACE_POOL = ["the old playroom", "the village library", "the school hall", "the garden shed"]
OBJECT_POOL = ["a brass bell", "a silver key", "a red ribbon", "a blue marble"]
HELPER_POOL = ["Mara", "Ben", "Aunt Jo", "the librarian"]

CASES = [
    {
        "object": "a brass bell",
        "sequence": ["red card", "blue card", "green card", "gold card"],
        "opening": "Luna was arranging four clue cards for the library's mystery game.",
        "purpose": "ring the brass bell when the cards formed the right sequence",
        "missing": "the gold card was gone",
        "clue": "a tiny smear of library dust curved toward the reading rug",
        "flashback": "Earlier, Biscuit had chased a rolling pencil under that rug and nudged the gold card behind its edge.",
        "reveal": "Luna lifted the rug and found the gold card beside the pencil.",
        "ending": "The brass bell rang, and Biscuit wagged as if he had solved the case himself.",
        "lesson": "a remembered detail can turn a suspicion into a fair clue",
    },
    {
        "object": "a silver key",
        "sequence": ["circle card", "star card", "moon card", "sun card"],
        "opening": "Milo was preparing a secret-box puzzle in the old playroom.",
        "purpose": "use the silver key when the picture cards formed the right sequence",
        "missing": "the moon card had vanished",
        "clue": "a damp paw print rested beside the toy chest",
        "flashback": "Earlier, Pepper had carried a wet toy past the chest and brushed the moon card beneath its lid.",
        "reveal": "Milo opened the toy chest and found the moon card under the lid.",
        "ending": "The silver key turned, and Pepper received the first pat at the solved mystery.",
        "lesson": "a flashback is useful when it explains what a clue could not",
    },
    {
        "object": "a red ribbon",
        "sequence": ["one dot", "two dots", "three dots", "four dots"],
        "opening": "Nina was setting up a treasure hunt in the school hall.",
        "purpose": "tie the red ribbon to the final sign after reading the dots in sequence",
        "missing": "the three-dot card was missing",
        "clue": "a bright thread caught on the handle of a supply cupboard",
        "flashback": "Earlier, Waffles had squeezed past the cupboard while dragging a scarf, and the card had slipped through the open door.",
        "reveal": "Nina opened the cupboard and found the three-dot card beneath the scarf.",
        "ending": "The red ribbon fluttered from the treasure sign while Waffles proudly guarded the empty cupboard.",
        "lesson": "a small thread can connect a present clue to an earlier moment",
    },
    {
        "object": "a blue marble",
        "sequence": ["leaf card", "rain card", "cloud card", "sun card"],
        "opening": "Theo was solving a garden-shed riddle before the afternoon rain.",
        "purpose": "place the blue marble in the riddle's cup when the weather cards were in sequence",
        "missing": "the cloud card was not on the table",
        "clue": "a little hollow marked the dust beneath the puppy blanket",
        "flashback": "Earlier, Teddy had burrowed under the blanket after a thunderclap, pushing the cloud card into the hollow.",
        "reveal": "Theo folded back the blanket and found the cloud card in the dust.",
        "ending": "The blue marble clicked into its cup just as the first rain tapped the roof.",
        "lesson": "remembering a frightened helper's movement can solve a quiet mystery",
    },
    {
        "object": "a silver key",
        "sequence": ["feather card", "stone card", "leaf card", "shell card"],
        "opening": "Ivy was leading a whodunit game beside the garden shed.",
        "purpose": "unlock the small evidence box after placing the nature cards in sequence",
        "missing": "the shell card had disappeared",
        "clue": "three grains of sand led toward the porch steps",
        "flashback": "Earlier, Clover had shaken a sandy blanket, and the shell card had slid beneath the lowest step.",
        "reveal": "Ivy knelt by the step and pulled out the shell card.",
        "ending": "The silver key opened the evidence box, which held a biscuit for Clover.",
        "lesson": "a kind detective checks memories before blaming anyone",
    },
    {
        "object": "a brass bell",
        "sequence": ["first moon", "second moon", "third moon", "full moon"],
        "opening": "Zara was arranging moon cards for a nighttime puzzle in the playroom.",
        "purpose": "ring the brass bell after placing the moon cards in sequence",
        "missing": "the third moon card was nowhere to be seen",
        "clue": "a faint jingle came from the basket of soft toys",
        "flashback": "Earlier, Button had leaped into the basket when the door creaked, and the card had landed beneath his blanket.",
        "reveal": "Zara lifted the blanket and found the third moon card beside Button's paw.",
        "ending": "The brass bell chimed softly, and Button blinked at the solved case.",
        "lesson": "sound, memory, and patience can work together",
    },
]


@dataclass
class StoryParams:
    name: str = "Luna"
    pup: str = "Biscuit"
    place: str = "the old playroom"
    helper: str = "Mara"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "clues", "cards"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "curiosity", "trust", "relief", "confidence"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
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


def _seed_number(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return int.from_bytes(
        f"{params.name}|{params.pup}|{params.place}|{params.helper}".encode(),
        "little",
    )


def tell_world(params: StoryParams) -> World:
    rng = random.Random(_seed_number(params))
    case = CASES[_seed_number(params) % len(CASES)]
    thinking = rng.choice([
        "Luna kept her detective notebook open and checked each clue twice.",
        "The detective tried not to let a dramatic theory outrun the evidence.",
        "A good mystery, the child remembered, needed patience more than suspicion.",
    ])
    w = World(place=params.place)
    child = w.add(Entity(params.name, "character", params.name))
    pup = w.add(Entity("pup", "animal", params.pup))
    cards = w.add(Entity("cards", "object", "the clue cards"))
    helper = w.add(Entity("helper", "character", params.helper))
    child.meters["cards"] = 4
    child.memes["curiosity"] = 2
    w.facts.update(params=params, case=case, thinking=thinking, child=child, pup=pup, helper=helper)

    w.say(f"In {params.place}, {case['opening']}")
    w.say(f"The plan was to {case['purpose']}.")
    w.say(thinking)
    w.para()

    child.memes["worry"] = 2
    child.memes["trust"] = 1
    w.say(f"But when {params.name} checked the table, {case['missing']}.")
    w.say(f"The three cards still there read {case['sequence'][0]}, {case['sequence'][1]}, and {case['sequence'][2]}.")
    w.say(f"That left a mystery to solve: who had moved the missing card, and why?")
    w.say(f"{params.name} noticed that {case['clue']}.")
    w.say(f"The pup, {params.pup}, sat nearby with a hopeful wag.")
    w.para()

    w.say(f'{params.name} asked, "Did you see what happened, {params.pup}?"')
    w.say(f'{params.helper} answered, "Before we accuse anyone, remember where {params.pup} went earlier."')
    w.say(f"{params.name} paused. A flashback returned: {case['flashback']}")
    w.say(f'"That memory changes the case," {params.name} said. "Let us follow the clue carefully."')
    w.say(f"{params.name} and {params.helper} searched together while {params.pup} watched.")
    child.memes["worry"] = 1
    child.memes["confidence"] = 2
    child.meters["clues"] = 3
    w.para()

    w.say(case["reveal"])
    w.say(f'{params.pup} barked once. "{params.pup} did not steal it," {params.name} said. "The card was moved by accident."')
    w.say(f'{params.helper} smiled. "Now put the sequence back together."')
    w.say(f"{params.name} arranged the cards as {', '.join(case['sequence'])}.")
    w.say(case["ending"])
    child.memes["worry"] = 0
    child.memes["relief"] = 3
    child.memes["confidence"] = 4
    child.meters["cards"] = 4
    w.facts.update(
        resolved=True,
        culprit="no culprit; the card was moved accidentally",
        clue=case["clue"],
        flashback=case["flashback"],
        solution=case["reveal"],
        sequence=case["sequence"],
        lesson=case["lesson"],
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    case = world.facts["case"]
    return [
        f"Write a child-friendly whodunit in which {p.name} and the pup {p.pup} solve a missing-card mystery in {p.place}.",
        f"Use a flashback, a conflict, and the sequence {', '.join(case['sequence'])} to explain why the missing {case['sequence'][-1]}.",
        f"Show {p.name} changing from suspicion to trust after speaking with {p.helper} and finding the concrete final clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    case = world.facts["case"]
    return [
        QAItem(
            f"What was {p.name} trying to do?",
            f"{p.name} was trying to {case['purpose']}.",
        ),
        QAItem(
            "What mystery had to be solved?",
            f"{case['missing'].capitalize()}, so the sequence could not be completed.",
        ),
        QAItem(
            f"What did the flashback reveal about {p.pup}?",
            f"It revealed that {case['flashback']}",
        ),
        QAItem(
            "How was the conflict resolved?",
            f"{case['reveal']} The card had been moved accidentally, not stolen, and the sequence was restored.",
        ),
        QAItem(
            "What changed for the detective?",
            f"The detective learned that {case['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a sequence?",
            "A sequence is an order in which things happen or are arranged.",
        ),
        QAItem(
            "What is a flashback?",
            "A flashback is a return to an earlier event that helps explain what is happening now.",
        ),
        QAItem(
            "Why should a detective check evidence?",
            "A detective should check evidence so a guess does not unfairly blame someone.",
        ),
        QAItem(
            "Why can a pup move an object without stealing it?",
            "A pup may move an object while playing or hiding, without understanding that the object is important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {text}" for i, text in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id} ({entity.kind}) meters={meters} memes={memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% The sequence can be restored when every card is present.
complete_sequence(Case) :- card_count(Case, N), found_cards(Case, N).

% A fair mystery has a clue and a flashback explaining the clue.
fair_mystery(Case) :- has_clue(Case), has_flashback(Case), accidental_move(Case).

solved(Case) :- complete_sequence(Case), fair_mystery(Case).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("card_count", "case", 4),
        asp.fact("found_cards", "case", 4),
        asp.fact("has_clue", "case"),
        asp.fact("has_flashback", "case"),
        asp.fact("accidental_move", "case"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show solved/1."))
    actual = set(asp.atoms(model, "solved"))
    expected = {("case",)}
    if actual != expected:
        print(f"MISMATCH: ASP={sorted(actual)} Python={sorted(expected)}")
        return 1
    for seed in range(12):
        sample = generate(StoryParams(seed=seed))
        if not sample.world or not sample.world.facts.get("resolved"):
            print(f"MISMATCH: generated story {seed} did not resolve")
            return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pup whodunit with a flashback and a restored sequence.")
    parser.add_argument("--name", choices=NAME_POOL)
    parser.add_argument("--pup", choices=PUP_POOL)
    parser.add_argument("--place", choices=PLACE_POOL)
    parser.add_argument("--helper", choices=HELPER_POOL)
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
        name=args.name or rng.choice(NAME_POOL),
        pup=args.pup or rng.choice(PUP_POOL),
        place=args.place or rng.choice(PLACE_POOL),
        helper=args.helper or rng.choice(HELPER_POOL),
    )


def validate_params(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if not params.pup.strip():
        raise StoryError("pup must not be empty")
    if params.name == params.pup:
        raise StoryError("the detective and pup need different names")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as err:
            raise SystemExit(f"ASP unavailable: {err}")
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(asp.atoms(model, "solved")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, case in enumerate(CASES):
            samples.append(
                generate(
                    StoryParams(
                        name=NAME_POOL[index % len(NAME_POOL)],
                        pup=PUP_POOL[index % len(PUP_POOL)],
                        place=PLACE_POOL[index % len(PLACE_POOL)],
                        helper=HELPER_POOL[index % len(HELPER_POOL)],
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                if index > max(args.n * 100, 100):
                    break
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
