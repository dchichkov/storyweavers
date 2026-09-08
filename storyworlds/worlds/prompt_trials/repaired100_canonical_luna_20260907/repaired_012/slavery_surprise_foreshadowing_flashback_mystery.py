#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class MysteryWorld:
    village: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    investigator_name: str
    child_name: str
    village: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mara", "Nia", "Tess", "Iris", "Sol", "Ada", "June"]
CHILD_NAMES = ["Eli", "Pip", "Noah", "Milo", "Sami", "Bea", "Toby", "Kit"]
VILLAGES = ["Willowmere", "Bell Hollow", "Mistvale", "Candlewick"]


ARCS = [
    {
        "key": "blue_ribbon",
        "premise": (
            "In the quiet village of {village}, investigator {investigator} found a blue ribbon tied to an empty gate. "
            "The gate belonged to an old house where records of slavery had once been hidden."
        ),
        "foreshadowing": (
            "All morning, a tiny bell rang whenever the wind touched the gate. Beneath it, someone had scratched a single word: remember."
        ),
        "problem": (
            "That night, the village archive lost its oldest ledger. A frightened child named {child} said a shadow had carried it toward the abandoned house."
        ),
        "flashback": (
            "Long ago, {investigator}'s grandmother had shown them that same blue ribbon in a family box. She had whispered, \"People were forced to work here, but their names must never disappear.\""
        ),
        "turn": (
            "{investigator} realized the ribbon was not a clue left by a thief. It marked a loose floorboard beneath the old bell, where the ledger had been placed for safekeeping."
        ),
        "dialogue": (
            "\"I saw the shadow hide the book,\" {child} said. \"Did you see a face?\" asked {investigator}. "
            "\"No, but I heard someone say the names should be safe.\""
        ),
        "resolution": (
            "Together they lifted the board and found the ledger wrapped in cloth. The supposed thief was the retired archivist, who had moved it after a leak began dripping onto the pages."
        ),
        "ending": (
            "At dawn, the ledger rested in a dry glass case. The blue ribbon hung beside it, and every recorded name could still be read."
        ),
        "problem_fact": "the oldest ledger about slavery disappeared from the village archive",
        "clue_fact": "a blue ribbon and the word remember pointed toward the old bell",
        "flashback_fact": "the investigator remembered a warning that forced workers' names must be preserved",
        "action_fact": "the investigator and child searched beneath the loose floorboard",
        "outcome_fact": "the ledger was safely recovered and its names were protected",
    },
    {
        "key": "locked_room",
        "premise": (
            "{investigator} was examining a locked room in {village}, where a museum displayed objects connected to the history of slavery. "
            "A young helper named {child} noticed fresh dust on the keyhole."
        ),
        "foreshadowing": (
            "Before the mystery began, three floorboards had creaked in a row, although nobody stood on them. A candle flame also bent toward the locked room."
        ),
        "problem": (
            "By evening, a small box of letters had vanished from inside the room, yet the lock had never turned. The letters belonged to people who had resisted being treated as property."
        ),
        "flashback": (
            "A memory returned to {investigator}: years earlier, the museum keeper had explained that the hidden wall panel was built by a carpenter who had escaped slavery and later taught others to read."
        ),
        "turn": (
            "{investigator} tested the wall beside the candle. The warm air revealed a narrow opening, and the missing box had been slid through it from the next room."
        ),
        "dialogue": (
            "\"The lock is innocent,\" said {child}. \"Then what moved the letters?\" asked {investigator}. "
            "\"The warm air did not move them,\" {child} answered. \"Someone used the hidden panel.\""
        ),
        "resolution": (
            "They found the museum keeper in the next room, repairing a broken case. She had moved the letters when rain entered through the roof, but had forgotten to tell anyone."
        ),
        "ending": (
            "The letters returned to their case behind clean glass. Outside, the three creaking boards were repaired, and the candle burned straight."
        ),
        "problem_fact": "a box of historical letters vanished from a locked museum room",
        "clue_fact": "dust, creaking boards, and a bending candle hinted at a hidden wall panel",
        "flashback_fact": "the investigator remembered the panel's connection to an escaped carpenter",
        "action_fact": "they followed warm air and searched the wall beside the candle",
        "outcome_fact": "the letters were recovered without blaming the lock",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.investigator_name, params.child_name, params.village))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big"))


def _validate(params: StoryParams) -> None:
    if not params.investigator_name.strip() or not params.child_name.strip():
        raise StoryError("Investigator and child names must not be empty.")
    if params.investigator_name == params.child_name:
        raise StoryError("The investigator and child must have different names.")
    if params.village not in VILLAGES:
        raise StoryError(f"Unknown village: {params.village}")


def tell(params: StoryParams) -> MysteryWorld:
    _validate(params)
    rng = _rng_for(params)
    arc = ARCS[rng.randrange(len(ARCS))]
    world = MysteryWorld(params.village)
    investigator = world.add(
        Entity(
            id=params.investigator_name,
            kind="character",
            type="investigator",
            label="investigator",
            meters={"attention": 1.0},
            memes={"curiosity": 1.0},
        )
    )
    child = world.add(
        Entity(
            id=params.child_name,
            kind="character",
            type="helper",
            label="child helper",
            meters={"courage": 1.0},
            memes={"trust": 1.0},
        )
    )
    ledger = world.add(Entity(id="ledger", type="historical_record", label="record of names"))
    ledger.memes["protected"] = 0.0

    beats = [
        arc["premise"].format(
            investigator=investigator.id, child=child.id, village=params.village
        ),
        arc["foreshadowing"].format(
            investigator=investigator.id, child=child.id, village=params.village
        ),
        arc["problem"].format(
            investigator=investigator.id, child=child.id, village=params.village
        ),
        arc["flashback"].format(
            investigator=investigator.id, child=child.id, village=params.village
        ),
        arc["dialogue"].format(
            investigator=investigator.id, child=child.id, village=params.village
        ),
        arc["turn"].format(
            investigator=investigator.id, child=child.id, village=params.village
        ),
        arc["resolution"].format(
            investigator=investigator.id, child=child.id, village=params.village
        ),
        arc["ending"].format(
            investigator=investigator.id, child=child.id, village=params.village
        ),
    ]
    for index, beat in enumerate(beats):
        if index:
            world.para()
        world.say(beat)

    ledger.memes["protected"] = 1.0
    world.facts = {
        "arc": arc["key"],
        "investigator": investigator.id,
        "child": child.id,
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "flashback": arc["flashback_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
        "problem_event": beats[2],
        "flashback_event": beats[3],
        "turn_event": beats[5],
        "resolution_event": beats[6],
    }
    return world


def generate_prompts(world: MysteryWorld) -> list[str]:
    return [
        "Write a child-friendly mystery about preserving the names of people harmed by slavery.",
        f"Tell a mystery in {world.village} using a surprise, a foreshadowed clue, and a flashback.",
        "Write a respectful historical mystery where careful questions solve a disappearance without rushing to blame.",
    ]


def story_qa(world: MysteryWorld) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What disappeared in the mystery?",
            answer=f["problem_event"],
        ),
        QAItem(
            question="What earlier memory helped the investigator?",
            answer=f["flashback_event"],
        ),
        QAItem(
            question="What clue foreshadowed the surprise?",
            answer=f["clue"],
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{f['turn_event']} {f['resolution_event']}",
        ),
    ]


def world_knowledge_qa(world: MysteryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What was slavery?",
            answer="Slavery was a cruel system in which people were forced to work and were denied freedom and control over their own lives. It was wrong, and many people resisted it.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue early in a story that hints at something important later.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that returns to an earlier time to reveal a memory or past event.",
        ),
        QAItem(
            question="What is a surprise in a mystery?",
            answer="A surprise is an unexpected discovery that changes what the characters think is happening.",
        ),
    ]


def dump_trace(world: MysteryWorld) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {entity.id:14} ({entity.type:18}) {' '.join(parts)}")
    lines.append(f"  village={world.village}")
    lines.append(f"  arc={world.facts.get('arc', '')}")
    lines.append("  historical_record_protected=True")
    return "\n".join(lines)


ASP_RULES = r"""
valid_mystery :-
    theme(slavery),
    feature(surprise),
    feature(foreshadowing),
    feature(flashback),
    style(mystery),
    record_protected.

record_protected :- outcome(recovered_record).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("theme", "slavery"),
            asp.fact("feature", "surprise"),
            asp.fact("feature", "foreshadowing"),
            asp.fact("feature", "flashback"),
            asp.fact("style", "mystery"),
            asp.fact("outcome", "recovered_record"),
            asp.fact("record_protected"),
        ]
    )


def asp_program(show: str = "#show valid_mystery/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if not any(symbol.name == "valid_mystery" for symbol in model):
        print("MISMATCH: ASP twin rejected the mystery.")
        return 1
    params = StoryParams("Luna", "Eli", "Willowmere", seed=12)
    sample = generate(params)
    required = ("surprise", "foreshadow", "memory", "slavery")
    lowered = sample.story.lower()
    if not all(word in lowered for word in required):
        print("MISMATCH: generated story lacks a required narrative element.")
        return 1
    print("OK: ASP and Python recognize the slavery-history mystery.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery world about preserving names and history."
    )
    parser.add_argument("--investigator-name")
    parser.add_argument("--child-name")
    parser.add_argument("--village", choices=VILLAGES)
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
    investigator = args.investigator_name or rng.choice(NAMES)
    choices = [name for name in CHILD_NAMES if name != investigator]
    child = args.child_name or rng.choice(choices)
    village = args.village or rng.choice(VILLAGES)
    return StoryParams(investigator, child, village)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("1 compatible mystery pattern: slavery history + surprise + foreshadowing + flashback")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("Luna", "Eli", "Willowmere", seed=101),
            StoryParams("Mara", "Pip", "Bell Hollow", seed=202),
            StoryParams("Iris", "Noah", "Mistvale", seed=303),
            StoryParams("Tess", "Bea", "Candlewick", seed=404),
        ]
        samples = [generate(params) for params in params_list]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
