#!/usr/bin/env python3
"""
storyworlds/worlds/eldest_dialogue_whodunit.py
==============================================

A small whodunit-style story world with dialogue, an eldest sibling, and a
tiny simulated mystery.

Premise:
- A household object goes missing.
- The eldest child notices clues, asks questions, and follows the trail.
- A careful reveal shows who moved the object and why.

The simulation tracks:
- physical meters: location, hiddenness, evidence, mess, recovered
- emotional memes: worry, suspicion, confidence, relief, guilt

The prose is driven by those state changes rather than a fixed template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Typed world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    atmosphere: str


@dataclass
class Mystery:
    item: str
    item_phrase: str
    item_location: str
    culprit_role: str
    culprit_reason: str
    clue_location: str
    clue_kind: str
    solved_line: str
    dialogue_hint: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    eldest_name: str
    eldest_type: str
    sibling_name: str
    sibling_type: str
    parent_name: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", atmosphere="bright morning light"),
    "hallway": Setting(place="the hallway", atmosphere="quiet shadows"),
    "living_room": Setting(place="the living room", atmosphere="soft lamplight"),
    "garden_shed": Setting(place="the garden shed", atmosphere="dusty daylight"),
}

MYSTERIES = {
    "jam_jar": Mystery(
        item="jam jar",
        item_phrase="the strawberry jam jar",
        item_location="the top shelf",
        culprit_role="younger sibling",
        culprit_reason="to reach the crackers",
        clue_location="the step stool",
        clue_kind="sticky fingerprints",
        solved_line="The eldest found the jam jar beside the crackers on the counter.",
        dialogue_hint="I only wanted toast.",
    ),
    "blue_key": Mystery(
        item="blue key",
        item_phrase="the little blue key",
        item_location="the sewing basket",
        culprit_role="parent",
        culprit_reason="to open the garden shed",
        clue_location="the back pocket of an apron",
        clue_kind="a thread of blue paint",
        solved_line="The eldest found the blue key hooked to an apron loop.",
        dialogue_hint="I forgot I tucked it there.",
    ),
    "paper_bird": Mystery(
        item="paper bird",
        item_phrase="the folded paper bird",
        item_location="the windowsill",
        culprit_role="eldest sibling",
        culprit_reason="to dry a message and keep it safe",
        clue_location="the windowsill curtain",
        clue_kind="a crease shaped like a wing",
        solved_line="The eldest found the paper bird hidden behind a curtain clip.",
        dialogue_hint="I was keeping it safe.",
    ),
}

ELDEST_NAMES = ["Ari", "Mina", "Jules", "Nora", "Theo", "Lena", "Owen", "Iris"]
SIBLING_NAMES = ["Pip", "Milo", "Bea", "Tess", "Noah", "June", "Kit", "Eli"]
PARENT_NAMES = ["Mara", "Jon", "Sera", "Cal", "Ivy", "Ben"]
TYPES = {"girl": "girl", "boy": "boy", "mother": "mother", "father": "father"}

SETTING_KEYS = list(SETTINGS)
MYSTERY_KEYS = list(MYSTERIES)


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def _vague_worry(world: World, eldest: Entity, mystery: Mystery) -> None:
    eldest.memes["worry"] = eldest.memes.get("worry", 0.0) + 1
    world.say(
        f"{eldest.id} noticed that {mystery.item_phrase} was missing, and a small knot of worry tightened in {eldest.pronoun('possessive')} chest."
    )


def _ask_question(world: World, speaker: Entity, listener: Entity, question: str) -> None:
    speaker.memes["confidence"] = speaker.memes.get("confidence", 0.0) + 1
    world.say(f'"{question}" {speaker.id} asked {listener.pronoun("object")}.')


def _answer(world: World, speaker: Entity, text: str) -> None:
    speaker.memes["worry"] = max(0.0, speaker.memes.get("worry", 0.0) - 0.25)
    world.say(f'"{text}" {speaker.id} said.')


def _follow_clue(world: World, eldest: Entity, mystery: Mystery) -> None:
    eldest.meters["evidence"] = eldest.meters.get("evidence", 0.0) + 1
    world.say(
        f"{eldest.id} looked at {mystery.clue_location}, where {mystery.clue_kind} gave the first careful clue."
    )


def _reveal(world: World, eldest: Entity, culprit: Entity, mystery: Mystery) -> None:
    eldest.meters["solution"] = eldest.meters.get("solution", 0.0) + 1
    eldest.memes["confidence"] = eldest.memes.get("confidence", 0.0) + 1
    culprit.memes["guilt"] = culprit.memes.get("guilt", 0.0) + 1
    culprit.meters["hidden"] = 0.0
    mystery_item = world.get(mystery.item)
    mystery_item.hidden = False
    mystery_item.meters["recovered"] = 1.0
    world.say(
        f'"I think I know," {eldest.id} said. "{mystery.solved_line}"'
    )
    world.say(
        f'{culprit.id} blinked, then sighed. "{mystery.dialogue_hint}"'
    )
    world.say(
        f"With that, the mystery settled: the missing {mystery.item} was back where it belonged, and the room felt lighter."
    )
    eldest.memes["relief"] = eldest.memes.get("relief", 0.0) + 1
    culprit.memes["guilt"] = max(0.0, culprit.memes["guilt"] - 0.5)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    eldest = world.add(Entity(id=params.eldest_name, kind="character", type=params.eldest_type, role="eldest"))
    sibling = world.add(Entity(id=params.sibling_name, kind="character", type=params.sibling_type, role="sibling"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type=params.parent_type, role="parent"))

    item = world.add(Entity(
        id=mystery.item,
        kind="thing",
        type="thing",
        label=mystery.item,
        phrase=mystery.item_phrase,
        hidden=True,
    ))

    if mystery.culprit_role == "younger sibling":
        culprit = sibling
    elif mystery.culprit_role == "parent":
        culprit = parent
    else:
        culprit = eldest

    # Act 1: setup
    world.say(
        f"In {setting.place}, {setting.atmosphere} made every corner feel like it might be hiding a secret."
    )
    world.say(
        f"{eldest.id} was the eldest child, the one who always noticed when a quiet thing was out of place."
    )
    _vague_worry(world, eldest, mystery)

    world.para()

    # Act 2: dialogue and clues
    _ask_question(world, eldest, sibling, f"Did you see {mystery.item_phrase} anywhere?")
    if mystery.culprit_role == "younger sibling":
        _answer(world, sibling, "No, but I saw sticky spots near the step stool.")
    elif mystery.culprit_role == "parent":
        _answer(world, sibling, "I didn't touch it, but I heard someone moving around the apron.")
    else:
        _answer(world, sibling, "I only saw a little folded shadow on the windowsill.")

    world.say(
        f"{eldest.id} listened carefully, because in a whodunit every small sentence can matter."
    )
    _follow_clue(world, eldest, mystery)

    if mystery.culprit_role == "younger sibling":
        world.say(
            f"Then {eldest.id} turned to {parent.id} and asked, \"Who used the step stool this morning?\""
        )
        _answer(world, parent, "It was only for reaching the crackers.")
    elif mystery.culprit_role == "parent":
        world.say(
            f"Then {eldest.id} noticed a thread of blue paint on the apron loop and looked up at {parent.id}."
        )
        _answer(world, parent, "I forgot I tucked the key there.")
    else:
        world.say(
            f"Then {eldest.id} spotted the curtain clip and the careful crease of folded paper."
        )
        _answer(world, sibling, "I was keeping it safe.")
    world.para()

    # Act 3: solution
    world.say(
        f"{eldest.id} took one more look at the room, connected the clue, and stepped forward with calm confidence."
    )
    _reveal(world, eldest, culprit, mystery)

    world.facts.update(
        eldest=eldest,
        sibling=sibling,
        parent=parent,
        culprit=culprit,
        item=item,
        mystery=mystery,
        setting=setting,
        solved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    eldest: Entity = f["eldest"]  # type: ignore[assignment]
    sibling: Entity = f["sibling"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    return [
        f'Write a short whodunit for a child where the eldest, {eldest.id}, solves a missing {mystery.item} mystery with dialogue.',
        f"Tell a gentle mystery story in {f['setting'].place} where {eldest.id} asks questions, {sibling.id} gives a clue, and {parent.id} answers plainly.",
        f'Write a dialogue-driven story that begins with a missing {mystery.item} and ends with the eldest explaining who moved it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    eldest: Entity = f["eldest"]  # type: ignore[assignment]
    sibling: Entity = f["sibling"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    culprit: Entity = f["culprit"]  # type: ignore[assignment]

    qa = [
        QAItem(
            question=f"Who was the eldest child in the story?",
            answer=f"{eldest.id} was the eldest child, and {eldest.pronoun('subject')} was the one who kept asking careful questions.",
        ),
        QAItem(
            question=f"What was missing at the start of the mystery?",
            answer=f"The missing thing was {mystery.item_phrase}. That is what made {eldest.id} start looking for clues.",
        ),
        QAItem(
            question=f"What clue helped {eldest.id} notice where to look next?",
            answer=f"The clue was {mystery.clue_kind} near {mystery.clue_location}. It pointed {eldest.id} toward the person who had moved the {mystery.item}.",
        ),
        QAItem(
            question=f"Who turned out to have moved the {mystery.item}?",
            answer=f"{culprit.id} turned out to be the one who moved it, because {culprit.pronoun('subject')} needed it {mystery.culprit_reason}.",
        ),
    ]

    if culprit.id == sibling.id:
        qa.append(
            QAItem(
                question=f"Why did {sibling.id} take the {mystery.item}?",
                answer=f"{sibling.id} took it {mystery.culprit_reason}, and that is why the object ended up in the wrong place.",
            )
        )
    elif culprit.id == parent.id:
        qa.append(
            QAItem(
                question=f"Why did {parent.id} move the {mystery.item}?",
                answer=f"{parent.id} moved it {mystery.culprit_reason}, but forgot to put it back right away.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"Why did the eldest hide the {mystery.item}?",
                answer=f"{eldest.id} hid it {mystery.culprit_reason}, which is why the mystery was tricky even for the eldest.",
            )
        )

    qa.append(
        QAItem(
            question=f"How did the story end?",
            answer=f"The story ended with the missing {mystery.item} back in place, and the room felt calm again.",
        )
    )
    return qa


WORLD_KNOWLEDGE = {
    "eldest": [
        QAItem(
            question="What does eldest mean?",
            answer="The eldest person in a family is the oldest child.",
        ),
        QAItem(
            question="Why might an eldest child notice a mystery first?",
            answer="An eldest child may notice first because they often pay attention to little changes at home.",
        ),
    ],
    "whodunit": [
        QAItem(
            question="What is a whodunit story?",
            answer="A whodunit is a mystery story where people ask questions to figure out who did something.",
        ),
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters speak directly and their words appear in quotes.",
        ),
    ],
    "clue": [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for key in ["eldest", "whodunit", "dialogue", "clue"] for q in WORLD_KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story parameter resolution
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Dialogue-driven eldest whodunit storyworld.")
    ap.add_argument("--setting", choices=SETTING_KEYS)
    ap.add_argument("--mystery", choices=MYSTERY_KEYS)
    ap.add_argument("--eldest-name")
    ap.add_argument("--eldest-type", choices=["girl", "boy"])
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-type", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(SETTING_KEYS)
    mystery = args.mystery or rng.choice(MYSTERY_KEYS)
    m = MYSTERIES[mystery]
    if args.eldest_type and args.sibling_type and args.eldest_type == args.sibling_type:
        raise StoryError("The eldest and the sibling should be different children, so give them different types or names.")
    eldest_name = args.eldest_name or rng.choice(ELDEST_NAMES)
    sibling_name = args.sibling_name or rng.choice([n for n in SIBLING_NAMES if n != eldest_name])
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    eldest_type = args.eldest_type or rng.choice(["girl", "boy"])
    sibling_type = args.sibling_type or ("boy" if eldest_type == "girl" else "girl")
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        mystery=mystery,
        eldest_name=eldest_name,
        eldest_type=eldest_type,
        sibling_name=sibling_name,
        sibling_type=sibling_type,
        parent_name=parent_name,
        parent_type=parent_type,
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
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
        print("\n--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(kitchen).
setting(hallway).
setting(living_room).
setting(garden_shed).

mystery(jam_jar).
mystery(blue_key).
mystery(paper_bird).

eldest_type(girl).
eldest_type(boy).
sibling_type(girl).
sibling_type(boy).
parent_type(mother).
parent_type(father).

% A story is valid when the chosen setting and mystery exist.
valid_story(S, M) :- setting(S), mystery(M).

% ASP twin of the Python registry; intended as a simple parity check.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_pairs() -> list[tuple]:
    return sorted((s, m) for s in SETTINGS for m in MYSTERIES)


def asp_verify() -> int:
    py = set(python_valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: ASP matches Python registry ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python registry:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Curated samples
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("kitchen", "jam_jar", "Ari", "girl", "Pip", "boy", "Mara", "mother"),
    StoryParams("hallway", "blue_key", "Theo", "boy", "Bea", "girl", "Jon", "father"),
    StoryParams("living_room", "paper_bird", "Nora", "girl", "Milo", "boy", "Sera", "mother"),
]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id} ({e.role or e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid setting/mystery pairs:")
        for s, m in pairs:
            print(f"  {s:12} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
