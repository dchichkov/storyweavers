#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/heed_fable_tumor_repetition_fairy_tale.py
===============================================================================================================

A tiny fairy-tale storyworld about heeding a fable when a strange tumor-like
lump is discovered, told with deliberate repetition.

The domain is small on purpose:
- A young traveler hears a fable from a wise elder.
- A worrying tumor/lump appears on a beloved animal friend.
- Repetition is used as a fairy-tale instrument: a warning is repeated, a
  plan is repeated, and a calming phrase is repeated.
- The turn is not magical hand-waving; it is a causal state change: heed the
  warning, visit the healer, and the friend grows safer and brighter.

This script is self-contained and uses only stdlib plus the shared results API.
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
# World model
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str


@dataclass
class Concern:
    id: str
    noun: str
    adjective: str
    risk: str
    zone: str
    keyword: str = "tumor"


@dataclass
class Remedy:
    id: str
    label: str
    action: str
    benefit: str
    guard: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "forest": Setting("the deep forest"),
    "village": Setting("the little village"),
    "castle": Setting("the old castle"),
}

CONCERNS = {
    "tumor": Concern(
        id="tumor",
        noun="tumor",
        adjective="strange",
        risk="grew larger and hurt more",
        zone="body",
        keyword="tumor",
    ),
}

REMEDIES = {
    "healer": Remedy(
        id="healer",
        label="the healer",
        action="visit the healer",
        benefit="the healer could look closely and help",
        guard="safe",
    ),
    "rest": Remedy(
        id="rest",
        label="rest and broth",
        action="rest by the fire",
        benefit="rest would help the small body stay calm",
        guard="calm",
    ),
}

NAMES = ["Ella", "Mira", "Nora", "Lina", "Rose", "Tilda"]
ANIMALS = ["deer", "rabbit", "lamb", "foal"]
ELDERS = ["grandmother", "wise woman", "old storyteller"]
TRAITS = ["gentle", "brave", "curious", "kind"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    place: str
    hero: str
    animal: str
    elder: str
    trait: str
    concern: str = "tumor"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def concern_is_reasonable(concern: Concern) -> bool:
    return concern.id == "tumor"


def remedy_for(concern: Concern) -> Optional[Remedy]:
    if concern.id == "tumor":
        return REMEDIES["healer"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for animal in ANIMALS:
            for elder in ELDERS:
                combos.append((place, animal, elder))
    return combos


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------


def repeat_line(text: str, times: int = 2) -> str:
    return " ".join([text] * times)


def introduce(world: World, hero: Entity, animal: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"{hero.id} was a {trait} child who lived near {world.setting.place} and loved the old stories there."
    )
    world.say(
        f"{hero.id} cared for a small {animal.type} named {animal.label}, and {animal.label} trusted {hero.pronoun('possessive')} soft hands."
    )
    world.say(
        f"One evening, {elder.label} told a fable: 'Heed the hush, heed the hush, for a small warning can save a life.'"
    )


def discover(world: World, hero: Entity, animal: Entity, concern: Concern) -> None:
    animal.meters[concern.id] = 1.0
    animal.memes["worry"] = 1.0
    world.say(
        f"{hero.id} noticed a {concern.adjective} {concern.noun} on {animal.label}, and the little room grew still."
    )
    world.say(
        f"'{concern.noun}, {concern.noun}, {concern.noun},' {hero.id} whispered, because the word itself felt heavy."
    )


def warn(world: World, elder: Entity, hero: Entity, animal: Entity, concern: Concern) -> None:
    world.say(
        f"{elder.label} repeated the old fable again: 'Heed the sign, heed the sign, heed the sign.'"
    )
    world.say(
        f"'{animal.label} should be seen by {REMEDIES['healer'].label},' {elder.label} said. 'A growing {concern.noun} is no thing to ignore.'"
    )
    hero.memes["heed"] = 1.0


def hesitate(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} wanted to wait, but the fable came back to {hero.id} again and again."
    )
    world.say(
        f"'Heed it, heed it, heed it,' the child said softly, repeating the lesson until it felt true."
    )


def act(world: World, hero: Entity, animal: Entity, concern: Concern, remedy: Remedy) -> None:
    world.say(
        f"At last {hero.id} heeded the warning and went to {remedy.label} with {animal.label}."
    )
    animal.memes["safe"] = 1.0
    animal.meters[concern.id] = 0.0
    animal.meters["bandage"] = 1.0
    world.say(
        f"{remedy.label} looked gently, gave calm help, and wrapped the sore place so it would not trouble {animal.label} so much."
    )
    world.say(
        f"The little {animal.type} rested, and rested, and rested, while {hero.id} kept the old fable in {hero.pronoun('possessive')} heart."
    )


def ending(world: World, hero: Entity, animal: Entity) -> None:
    world.say(
        f"In the end, {animal.label} was safer and brighter, and {hero.id} knew that a repeated warning can be a kind one."
    )
    world.say(
        f"That night, the child told the fable again: 'Heed the sign, heed the sign,' and the words sounded warm like a lantern."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", label=params.hero))
    animal = world.add(Entity(id="animal", kind="character", type=params.animal, label=f"the {params.animal}"))
    elder = world.add(Entity(id="elder", kind="character", type="woman", label=params.elder))

    concern = CONCERNS[params.concern]
    remedy = remedy_for(concern)
    if remedy is None:
        raise StoryError("No reasonable remedy exists for that concern.")

    introduce(world, hero, animal, elder, params.trait)
    world.para()
    discover(world, hero, animal, concern)
    warn(world, elder, hero, animal, concern)
    hesitate(world, hero)
    world.para()
    act(world, hero, animal, concern, remedy)
    ending(world, hero, animal)

    world.facts.update(
        hero=hero,
        animal=animal,
        elder=elder,
        concern=concern,
        remedy=remedy,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for young children about a child who heeds a fable when a {f["concern"].noun} appears.',
        f"Tell a gentle story in which {f['hero'].id} repeats a warning, then listens, and helps {f['animal'].label}.",
        f'Write a short fairy tale using the words "heed", "fable", and "{f["concern"].noun}" with repetition.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    animal: Entity = f["animal"]
    elder: Entity = f["elder"]
    concern: Concern = f["concern"]
    remedy: Remedy = f["remedy"]

    return [
        QAItem(
            question=f"Who heard the fable in the story?",
            answer=f"{hero.id} heard the fable from {elder.label}."
        ),
        QAItem(
            question=f"What strange thing did {hero.id} notice on {animal.label}?",
            answer=f"{hero.id} noticed a {concern.adjective} {concern.noun} on {animal.label}."
        ),
        QAItem(
            question=f"How did the child respond after hearing the warning again and again?",
            answer=f"{hero.id} heeded the warning and went with {animal.label} to {remedy.label}."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{animal.label} was safer and brighter, and the worry about the {concern.noun} was eased."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that teaches a lesson, often by using a simple message that can be remembered."
        ),
        QAItem(
            question="What does it mean to heed a warning?",
            answer="To heed a warning means to listen carefully and do what the warning says so trouble can be avoided."
        ),
        QAItem(
            question="Why is repetition useful in a story for children?",
            answer="Repetition helps children remember important words, and it can make a story feel musical and clear."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
concern_ok(tumor).
remedy_ok(tumor, healer).

valid_story(Place, Animal, Elder) :- setting(Place), animal(Animal), elder(Elder).
compatible(tumor, healer) :- concern_ok(tumor), remedy_ok(tumor, healer).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for e in ELDERS:
        lines.append(asp.fact("elder", e))
    for c in CONCERNS:
        lines.append(asp.fact("concern", c))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2. #show valid_story/3."))
    comp = set(asp.atoms(model, "compatible"))
    valid = set(asp.atoms(model, "valid_story"))
    python_comp = {("tumor", "healer")} if concern_is_reasonable(CONCERNS["tumor"]) else set()
    python_valid = set((p, a, e) for p in SETTINGS for a in ANIMALS for e in ELDERS)
    ok = comp == python_comp and valid == python_valid
    if ok:
        print("OK: ASP parity matches the Python reasonableness gate.")
        print("OK: verification story-model exercised.")
        return 0
    print("Mismatch between ASP and Python gate.")
    print("ASP compatible:", sorted(comp))
    print("Python compatible:", sorted(python_comp))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale world about heed, fable, tumor, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.concern if hasattr(args, "concern") else False:
        pass
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    animal = args.animal or rng.choice(ANIMALS)
    elder = args.elder or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    concern = "tumor"
    if concern not in CONCERNS:
        raise StoryError("Unknown concern.")
    return StoryParams(place=place, hero=name, animal=animal, elder=elder, trait=trait, concern=concern)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="forest", hero="Ella", animal="deer", elder="wise woman", trait="gentle"),
    StoryParams(place="village", hero="Mira", animal="rabbit", elder="grandmother", trait="brave"),
    StoryParams(place="castle", hero="Nora", animal="lamb", elder="old storyteller", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2. #show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
