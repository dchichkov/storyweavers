#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/insinuate_rhyme_mystery_to_solve_transformation_bedtime.py
==============================================================================================================================

A small bedtime storyworld about a child, a gentle mystery to solve, and a
transformative turn from worry to comfort.

Core premise:
- A sleepy child hears a tiny rhyme at bedtime.
- The rhyme seems to insinuate that something important is missing.
- The child follows clues, solves the mystery, and the room transforms from
  uneasy to cozy.

This world is intentionally small and classical:
- one setting
- one child
- one caretaker
- one missing bedtime object
- one clue trail driven by rhyming lines
- one emotional transformation at the end

The story is generated from simulated state, not from a frozen paragraph.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    bedtime: bool = True
    quiet: bool = True


@dataclass
class Mystery:
    id: str
    clue_rhyme: str
    missing_label: str
    missing_phrase: str
    found_where: str
    solves_with: str
    transformation: str
    is_soft: bool = True


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the bedroom"),
    "nursery": Setting(place="the nursery"),
    "attic-room": Setting(place="the little attic room"),
}

MYSTERIES = {
    "lost-lullaby": Mystery(
        id="lost-lullaby",
        clue_rhyme="If the pillow sighs and the night grows dim, check under the moonbeam's brim.",
        missing_label="music box key",
        missing_phrase="a tiny music box key",
        found_where="under the pillow",
        solves_with="a careful lift of the pillow",
        transformation="the room feels calmer and the lullaby can play again",
    ),
    "blanket-shadow": Mystery(
        id="blanket-shadow",
        clue_rhyme="If a blanket looks like a dragon's tail, peek where soft folds hide the trail.",
        missing_label="blanket corner",
        missing_phrase="one soft blanket corner",
        found_where="tucked beside the bed",
        solves_with="a gentle tug and a sleepy smile",
        transformation="the blankets become a safe nest instead of a scary shape",
    ),
    "star-sticker": Mystery(
        id="star-sticker",
        clue_rhyme="If a star goes missing from the dark blue sky, look where the sleepy socks lie.",
        missing_label="star sticker",
        missing_phrase="one little star sticker",
        found_where="stuck on a sock",
        solves_with="a tiny peel and a quiet giggle",
        transformation="the sky wall becomes bright again and the dark looks friendly",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Nora", "Ella", "Ruby"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Owen", "Theo", "Milo"]
TRAITS = ["curious", "gentle", "brave", "sleepy", "careful", "dreamy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- room(S).
mystery(M) :- mystery_id(M).
compatible(S, M) :- setting(S), mystery(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("room", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_id", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {(s, m) for s in SETTINGS for m in MYSTERIES}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches Python compatibility ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python compatibility:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def reasonableness_gate(setting: str, mystery: str) -> None:
    if setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {setting})")
    if mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {mystery})")


def predict_resolution(world: World, child: Entity, mystery: Mystery) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["worry"] = sim.get(child.id).memes.get("worry", 0.0) + 1.0
    found = True
    calm = 1.0
    return {"found": found, "calm": calm, "transformed": True}


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str, caretaker_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_type, label=f"the {caretaker_type}", meters={}, memes={}))
    item = world.add(Entity(
        id="missing",
        kind="thing",
        type="thing",
        label=mystery.missing_label,
        phrase=mystery.missing_phrase,
        owner=child.id,
        caretaker=caretaker.id,
    ))

    child.memes["sleepiness"] = 1.0
    child.memes["wonder"] = 1.0
    caretaker.memes["tenderness"] = 1.0
    world.facts.update(child=child, caretaker=caretaker, item=item, mystery=mystery, setting=setting, trait=trait)

    world.say(f"{hero_name} was a little {trait} {hero_type} who was almost ready for sleep.")
    world.say(f"{hero_name} liked bedtime because the room felt soft and warm, and {caretaker.label_word if hasattr(caretaker, 'label_word') else caretaker.type} always tucked the blankets just right.")
    world.say(f"One night, a tiny rhyme began to drift through {setting.place}.")

    world.para()
    world.say(f'"{mystery.clue_rhyme}"')
    child.memes["worry"] = 1.0
    child.memes["mystery"] = 1.0
    world.say(f"{hero_name} listened closely. The rhyme seemed to insinuate that something was not quite right.")
    world.say(f"{hero_name} whispered, \"A mystery to solve? At bedtime?\"")

    world.para()
    world.say(f"{hero_name} looked around with sleepy eyes and found a clue near the bed.")
    world.say(f"{hero_name} followed the clue {mystery.solves_with}, and soon found {mystery.missing_phrase} {mystery.found_where}.")
    child.meters["searching"] = 1.0
    child.memes["focus"] = 1.0

    world.para()
    world.say(f"{hero_name} brought it to {caretaker.label if caretaker.label else caretaker.type}.")
    world.say(f"That was the answer to the bedtime mystery.")
    child.memes["joy"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["peace"] = 1.0
    caretaker.memes["relief"] = 1.0
    world.say(f"With the missing {mystery.missing_label} back where it belonged, {mystery.transformation}.")
    world.say(f"The little room transformed from puzzly and tense into cozy and calm, and {hero_name} could drift off smiling.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        f'Write a bedtime story for a small child where a rhyme seems to insinuate a mystery to solve.',
        f"Tell a gentle story about {child.id} in {setting.place} who hears a clue rhyme and finds {mystery.missing_phrase}.",
        f'Write a cozy bedtime tale that includes the words "insinuate", "rhyme", "mystery to solve", and "transformation".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    caretaker: Entity = f["caretaker"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"What kind of story is this about {child.id} at {setting.place}?",
            answer=f"It is a cozy bedtime story about {trait} {child.type} {child.id}, a soft mystery to solve, and a calm ending.",
        ),
        QAItem(
            question=f"What did the rhyme seem to insinuate during the story?",
            answer=f"The rhyme seemed to insinuate that something important was missing, so {child.id} knew there was a mystery to solve.",
        ),
        QAItem(
            question=f"What was the missing thing that {child.id} found?",
            answer=f"{child.id} found {mystery.missing_phrase}, and that was the answer to the bedtime mystery.",
        ),
        QAItem(
            question=f"How did the story transform by the end?",
            answer=f"The story transformed from puzzly and a little tense into cozy and calm, because the missing {mystery.missing_label} was found.",
        ),
        QAItem(
            question=f"Who helped {child.id} after the clue was solved?",
            answer=f"{caretaker.label if caretaker.label else caretaker.type} was there to listen, smile, and welcome the answer when {child.id} returned with the missing piece.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a line or phrase with matching sounds at the end, which often makes a story feel musical and easy to remember.",
        ),
        QAItem(
            question="What does insinuate mean?",
            answer="To insinuate means to suggest something in a gentle, not-so-direct way.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that needs clues and careful thinking to understand or solve.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new state, like a worried room becoming cozy and safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="bedroom", mystery="star-sticker", name="Lily", gender="girl", caretaker="mother", trait="curious"),
    StoryParams(setting="nursery", mystery="lost-lullaby", name="Leo", gender="boy", caretaker="father", trait="gentle"),
    StoryParams(setting="attic-room", mystery="blanket-shadow", name="Mia", gender="girl", caretaker="mother", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime storyworld about rhyme, mystery, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    reasonableness_gate(setting, mystery)

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, caretaker=caretaker, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        params.name,
        params.gender,
        params.caretaker,
        params.trait,
    )
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


def asp_verify_story() -> int:
    # Exercise generated stories as part of verification: ensure every curated
    # sample produces non-empty prose and a clear transformation ending.
    for p in CURATED:
        s = generate(p)
        if not s.story.strip():
            print("ERROR: empty story")
            return 1
        if "transformed" not in s.story.lower() and "transform" not in s.story.lower():
            print("ERROR: story lacks transformation language")
            return 1
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify_story())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible (setting, mystery) pairs:\n")
        for s, m in pairs:
            print(f"  {s:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
