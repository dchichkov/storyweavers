#!/usr/bin/env python3
"""
Standalone storyworld: the loud breaking in the quiet workshop.

A child-friendly whodunit about a sudden crash, careful problem solving,
reconciliation, and the moral value of checking evidence before blaming.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "the village workshop"
    protagonist: str = "Luna"
    protagonist_type: str = "girl"
    companion: str = "Theo"
    companion_type: str = "boy"
    caretaker: str = "Mara"
    caretaker_type: str = "woman"
    case_id: int = 0
    telling_mode: int = 0


CASES = [
    {
        "title": "the cracked blue lantern",
        "premise": "A loud bang shook the workshop just before the evening fair.",
        "problem": "the blue lantern on the repair table had broken, and its glass shade lay in bright pieces",
        "clue": "a line of floury paw prints leading from the pantry to the table",
        "false_step": "Mara suspected Theo because he had been carrying a toolbox nearby",
        "cause": "a curious kitten had bumped the table while chasing a loose ribbon",
        "action": "followed the paw prints, checked the ribbon, and asked everyone what they had seen",
        "resolution": "The kitten was found safely behind a basket, and Mara replaced the lantern's shade with a spare one",
        "ending": "When the fair began, the repaired lantern cast a calm blue pool of light",
    },
    {
        "title": "the broken music box",
        "premise": "A loud clatter burst from the shelf during a quiet afternoon.",
        "problem": "the workshop music box had broken, and its little wooden dancer had fallen off",
        "clue": "a trail of brass buttons beneath the shelf and one button missing from a coat",
        "false_step": "Luna thought Theo had knocked it over while reaching for a jar",
        "cause": "a gust through the open window had pulled a coat against the shelf",
        "action": "matched the buttons, closed the window, and examined the shelf without touching the sharp pieces",
        "resolution": "Mara repaired the dancer, and Theo admitted that his coat had been hanging too close",
        "ending": "The music box played softly while the coat hung safely on its peg",
    },
    {
        "title": "the shattered clay bird",
        "premise": "A loud crack came from the back room while everyone prepared paint.",
        "problem": "a clay bird made for the children's table had broken on the floor",
        "clue": "a wet green paintbrush resting beneath the open cupboard door",
        "false_step": "Mara blamed Luna because Luna had chosen the green paint",
        "cause": "the cupboard door had swung down and nudged the drying bird",
        "action": "compared the paint mark with the door edge and tested the hinge with an adult",
        "resolution": "Luna and Mara apologized to each other, and they repaired the bird with gold-colored clay",
        "ending": "The golden seam made the little bird look ready to fly",
    },
    {
        "title": "the noisy falling stack",
        "premise": "A loud crash sent a stack of wooden blocks across the floor.",
        "problem": "the tallest block tower had broken apart before the puzzle contest",
        "clue": "one round wheel wedged under the lowest shelf",
        "false_step": "Theo accused Luna of pulling the tablecloth",
        "cause": "a toy cart had rolled into the shelf and shaken the blocks",
        "action": "retraced the cart's path and placed a wooden stop by the wheel",
        "resolution": "The friends rebuilt the tower together and agreed to keep wheels away from the display",
        "ending": "The new tower stood firm beside the quiet, stopped cart",
    },
]


OPENINGS = [
    "Whodunits often begin with a sound before they reveal a reason.",
    "The workshop had been peaceful until one noisy clue broke the calm.",
    "Everyone heard the crash, but hearing a sound was not the same as knowing its cause.",
    "A small mystery waited among the tools, shelves, and scattered pieces.",
]


LESSONS = [
    "Evidence is kinder and wiser than a quick accusation.",
    "Solving a problem together can repair trust as well as broken things.",
    "A mistake becomes easier to mend when people tell the truth and listen.",
    "Good detectives ask what happened before deciding who is at fault.",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    location: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        from collections import defaultdict
        self.meters = defaultdict(float, self.meters)
        self.memes = defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def reason_gate(params: StoryParams) -> None:
    if not params.place.strip():
        raise StoryError("place must not be empty")
    names = [params.protagonist, params.companion, params.caretaker]
    if any(not name.strip() for name in names):
        raise StoryError("character names must not be empty")
    if len(set(name.casefold() for name in names)) != len(names):
        raise StoryError("protagonist, companion, and caretaker need different names")
    if params.protagonist_type not in {"girl", "boy", "woman", "man"}:
        raise StoryError("unsupported protagonist type")
    if params.companion_type not in {"girl", "boy", "woman", "man"}:
        raise StoryError("unsupported companion type")
    if params.caretaker_type not in {"girl", "boy", "woman", "man"}:
        raise StoryError("unsupported caretaker type")


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(
        "hero", "character", params.protagonist_type, params.protagonist,
        params.place, memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.0},
    ))
    companion = world.add(Entity(
        "companion", "character", params.companion_type, params.companion,
        params.place, memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.0},
    ))
    caretaker = world.add(Entity(
        "caretaker", "character", params.caretaker_type, params.caretaker,
        params.place, memes={"worry": 0.0, "trust": 0.0},
    ))
    broken = world.add(Entity(
        "broken_object", "object", "repairable", "the broken object",
        params.place, meters={"broken": 1.0, "dangerous_shards": 1.0},
    ))
    clue = world.add(Entity(
        "clue", "thing", "clue", "the first clue", params.place,
        meters={"noticed": 0.0},
    ))
    world.facts.update(
        hero=hero,
        companion=companion,
        caretaker=caretaker,
        broken=broken,
        clue=clue,
        solved=False,
        reconciled=False,
    )
    return world


def tell(params: StoryParams) -> World:
    reason_gate(params)
    case = CASES[params.case_id % len(CASES)]
    lesson = LESSONS[(params.case_id + params.telling_mode) % len(LESSONS)]
    opening = OPENINGS[params.telling_mode % len(OPENINGS)]
    world = build_world(params)
    hero = world.get("hero")
    companion = world.get("companion")
    caretaker = world.get("caretaker")
    broken = world.get("broken_object")
    clue = world.get("clue")

    world.facts.update(
        title=case["title"],
        premise=case["premise"],
        problem=case["problem"],
        clue_text=case["clue"],
        false_step=case["false_step"],
        cause=case["cause"],
        action=case["action"],
        resolution=case["resolution"],
        ending=case["ending"],
        lesson=lesson,
    )

    world.say(
        f"In {params.place}, {hero.label} and {companion.label} were helping "
        f"{caretaker.label} prepare for the evening."
    )
    world.say(
        f"{opening} {case['premise']} "
        f"The sound was loud enough to make every spoon on the wall tremble."
    )
    world.say(
        f"When the echoes faded, {case['problem']}. "
        f"{caretaker.label} looked worried, and the broken pieces glittered on the floor."
    )

    world.para()
    world.say(
        f"{case['false_step']}. "
        f"'Wait,' said {hero.label}. 'We know something broke, but we do not yet know who caused it.'"
    )
    world.say(
        f"{companion.label} pointed toward the floor. "
        f"'Look at this: {case['clue']}.'"
    )
    clue.meters["noticed"] = 1.0
    hero.memes["curiosity"] += 1.0
    companion.memes["trust"] += 1.0
    world.say(
        f"{caretaker.label} took a breath. 'You are right. Let us solve the problem before we blame anyone.'"
    )
    world.say(
        f"Together they {case['action']}. The clues showed that {case['cause']}."
    )

    world.para()
    broken.meters["broken"] = 0.0
    broken.meters["dangerous_shards"] = 0.0
    world.facts["solved"] = True
    world.facts["reconciled"] = True
    world.facts["culprit"] = "an accident, not a person to blame"
    world.say(case["resolution"])
    world.say(
        f"'I am sorry I guessed so quickly,' said {caretaker.label}. "
        f"'I should have listened to the clues.'"
    )
    world.say(
        f"'And I am sorry I left the danger so close to the shelf,' said {companion.label}. "
        f"'Next time I will help keep the path clear.'"
    )
    world.say(
        f"{hero.label} smiled. 'Then we have solved two things: the mystery and the hurt feelings.'"
    )
    caretaker.memes["worry"] = 0.0
    caretaker.memes["trust"] += 1.0
    hero.memes["trust"] += 1.0
    companion.memes["trust"] += 1.0
    world.say(f"The moral value was simple: {lesson}")
    world.say(case["ending"])
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a child-friendly whodunit about {facts['title']} in a village workshop.",
        f"Show how {facts['hero'].label} and {facts['companion'].label} solve the loud breaking mystery using {facts['clue_text']}.",
        f"End with reconciliation and the moral value that {facts['lesson'].lower()}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    caretaker = f["caretaker"]
    return [
        QAItem(
            f"What loud event began the mystery of {f['title']}?",
            f"{f['premise']} The sound revealed that {f['problem']}.",
        ),
        QAItem(
            f"What clue did {companion.label} notice?",
            f"{companion.label} noticed {f['clue_text']}. That clue helped the group test the cause instead of relying on a guess.",
        ),
        QAItem(
            "How did the characters solve the problem?",
            f"They {f['action']}. This showed that {f['cause']}.",
        ),
        QAItem(
            f"How did {caretaker.label} and the others reconcile?",
            f"{caretaker.label} apologized for guessing, and {companion.label} admitted a part of the accident that could be prevented. They listened to each other and worked together to repair the damage.",
        ),
        QAItem(
            f"What moral value did {hero.label} learn?",
            f"{f['lesson']} The story shows that careful problem solving can repair trust as well as broken objects.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "What is a whodunit?",
        "A whodunit is a mystery story in which characters use clues to discover what happened.",
    ),
    QAItem(
        "Why should people check evidence before blaming someone?",
        "Checking evidence helps people find the true cause and prevents unfair accusations.",
    ),
    QAItem(
        "What does reconciliation mean?",
        "Reconciliation means repairing a relationship after people listen, apologize, and make things right.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 3) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 3) for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:12} ({entity.type:10}) "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
broken(O) :- repairable(O), damaged(O).
solved :- broken(broken_object), clue_found, cause_checked.
reconciled :- solved, apology_given, promise_made.
coherent :- solved, reconciled.

#show coherent/0.
#show solved/0.
#show reconciled/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("repairable", "broken_object"),
        asp.fact("damaged", "broken_object"),
        asp.fact("clue_found"),
        asp.fact("cause_checked"),
        asp.fact("apology_given"),
        asp.fact("promise_made"),
    ])


def asp_program(show: str = "#show coherent/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = {symbol.name for symbol in model}
    expected = {"coherent", "solved", "reconciled"}
    if not expected.issubset(atoms):
        print("MISMATCH between ASP and Python story gate.")
        return 1
    sample = generate(StoryParams())
    if not sample.story or "mystery" not in sample.story.lower():
        print("MISMATCH: generated story check failed.")
        return 1
    if not any(item.answer for item in sample.story_qa):
        print("MISMATCH: story QA check failed.")
        return 1
    print("OK: ASP and Python reasonableness gate agree.")
    print("OK: generated story and QA checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A loud-breaking reconciliation whodunit storyworld."
    )
    parser.add_argument("--place", default="the village workshop")
    parser.add_argument("--protagonist")
    parser.add_argument("--protagonist-type", choices=["girl", "boy", "woman", "man"], default="girl")
    parser.add_argument("--companion")
    parser.add_argument("--companion-type", choices=["girl", "boy", "woman", "man"], default="boy")
    parser.add_argument("--caretaker")
    parser.add_argument("--caretaker-type", choices=["girl", "boy", "woman", "man"], default="woman")
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


def resolve_params(
    args: argparse.Namespace, rng: random.Random, sample_seed: int
) -> StoryParams:
    protagonist = args.protagonist or rng.choice(["Luna", "Nia", "Mira", "Sasha"])
    companion = args.companion or rng.choice(["Theo", "Pip", "Arlo", "Ben"])
    caretaker = args.caretaker or rng.choice(["Mara", "Aunt Jo", "Rina", "Tess"])
    if len({protagonist.casefold(), companion.casefold(), caretaker.casefold()}) != 3:
        raise StoryError("the three character names must be different")
    return StoryParams(
        seed=args.seed,
        place=args.place,
        protagonist=protagonist,
        protagonist_type=args.protagonist_type,
        companion=companion,
        companion_type=args.companion_type,
        caretaker=caretaker,
        caretaker_type=args.caretaker_type,
        case_id=sample_seed % len(CASES),
        telling_mode=(sample_seed // len(CASES)) % len(OPENINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        raise SystemExit(asp_verify())

    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(seed=base_seed, protagonist="Luna", companion="Theo", caretaker="Mara", case_id=0),
            StoryParams(seed=base_seed + 1, protagonist="Mira", companion="Pip", caretaker="Rina", case_id=1),
            StoryParams(seed=base_seed + 2, protagonist="Nia", companion="Arlo", caretaker="Tess", case_id=2),
            StoryParams(seed=base_seed + 3, protagonist="Sasha", companion="Ben", caretaker="Aunt Jo", case_id=3),
        ]
        samples = [generate(item) for item in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n:
            sample_seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
            params.seed = sample_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", " ".join(str(symbol) for symbol in model))
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
