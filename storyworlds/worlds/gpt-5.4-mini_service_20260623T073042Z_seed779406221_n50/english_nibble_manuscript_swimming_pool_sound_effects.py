#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T073042Z_seed779406221_n50/english_nibble_manuscript_swimming_pool_sound_effects.py
===============================================================================================================================

A small bedtime-story world about an English manuscript in a swimming pool,
with nibbling, sound effects, caution, and gentle repetition.

Seed tale:
---
A child finds an English manuscript by the swimming pool. The pages flutter
near the water while a small nibble-mouse starts nibbling the corner. The child
hears plip-plop and splish-splash, remembers to be careful, and lifts the
manuscript onto a dry chair. The mouse gets a tiny nibble of toast instead, and
the pages are saved.
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
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    details: str


@dataclass
class StoryParams:
    place: str
    manuscript: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "swimming_pool": Setting(
        place="the swimming pool",
        details="The water made little bright ripples, and the deck smelled like summer.",
    )
}

MANUSCRIPTS = {
    "english": {
        "label": "English manuscript",
        "phrase": "a neat English manuscript",
        "pages": "its English pages",
        "topic": "english",
    },
    "nibble": {
        "label": "nibble manuscript",
        "phrase": "a tiny nibble manuscript",
        "pages": "its nibble-marked pages",
        "topic": "nibble",
    },
    "manuscript": {
        "label": "manuscript",
        "phrase": "an old manuscript",
        "pages": "its paper pages",
        "topic": "manuscript",
    },
}

NIBBLE_GEAR = {
    "toast": {
        "label": "toast",
        "phrase": "a little piece of toast",
    },
    "cracker": {
        "label": "cracker",
        "phrase": "a tiny cracker",
    },
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Owen", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a manuscript by a swimming pool.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--manuscript", choices=MANUSCRIPTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, ms) for place in SETTINGS for ms in MANUSCRIPTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.manuscript is None or c[1] == args.manuscript)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, manuscript = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, manuscript=manuscript, child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender)


def tell(place: Setting, manuscript_key: str, child: str, child_gender: str, helper: str, helper_gender: str) -> World:
    world = World(place)
    child_e = world.add(Entity(id=child, kind="character", type=child_gender, label=child))
    helper_e = world.add(Entity(id=helper, kind="character", type=helper_gender, label=helper))
    ms_cfg = MANUSCRIPTS[manuscript_key]
    ms = world.add(Entity(id="manuscript", kind="thing", type="paper", label=ms_cfg["label"], phrase=ms_cfg["phrase"], owner=child))
    mouse = world.add(Entity(id="mouse", kind="character", type="thing", label="little nibble-mouse"))
    mouse.meters["hunger"] = 1.0
    child_e.memes["care"] = 1.0
    helper_e.memes["care"] = 1.0
    ms.meters["wet"] = 0.0
    ms.meters["safe"] = 0.0
    world.say(f"{child} found {ms_cfg['phrase']} beside {world.setting.place}.")
    world.say(f"{world.setting.details} The child held {ms_cfg['label']} close and whispered, \"Careful, careful.\"")
    world.para()
    world.say(f"Then came the soft sounds: plip-plop, splish-splash, and nibble-nibble, nibble-nibble.")
    world.say(f"The little nibble-mouse peeped at {ms_cfg['pages']} and took a tiny nibble at one corner.")
    ms.meters["at_risk"] = 1.0
    ms.memes["worry"] = 1.0
    child_e.memes["worry"] = 1.0
    helper_e.memes["warning"] = 1.0
    world.para()
    world.say(f"{helper} said, \"Careful, careful. The pool is for splashes, not for paper.\"")
    world.say(f"{child} nodded. \"Careful, careful,\" {child} said again, because a kind repeat can help a child remember.")
    ms.location = "dry chair"
    ms.meters["wet"] = 0.0
    ms.meters["safe"] = 1.0
    mouse.phrase = "a little piece of toast"
    mouse.label = "nibble-mouse"
    world.para()
    world.say(f"{child} lifted {ms_cfg['label']} onto a dry chair, away from the water.")
    world.say(f"Plip-plop went the pool, but the pages stayed dry.")
    world.say(f"The nibble-mouse got {NIBBLE_GEAR['toast']['phrase']} instead, and munch-munch went the happy little mouth.")
    world.say(f"At bedtime, {child} kept the {ms_cfg['label']} safe, and the swimming pool listened quietly in the dark.")
    world.facts.update(child=child_e, helper=helper_e, manuscript=ms, mouse=mouse, setting=place, manuscript_key=manuscript_key)
    return world


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    h = world.facts["helper"]
    ms = world.facts["manuscript"]
    return [
        QAItem(question=f"What did {c.id} find near the swimming pool?", answer=f"{c.id} found {ms.phrase} beside the swimming pool."),
        QAItem(question=f"Who told {c.id} to be careful?", answer=f"{h.id} told {c.id} to be careful because paper should stay dry."),
        QAItem(question=f"What happened to the manuscript at the end?", answer=f"{c.id} put the manuscript on a dry chair, so it stayed safe and dry."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does a swimming pool sound like in a bedtime story?", answer="It can sound like plip-plop and splish-splash."),
        QAItem(question="Why should paper stay away from pool water?", answer="Paper can get wet and damaged if it is left near water."),
        QAItem(question="What should you do when someone says careful?", answer="You should slow down, listen, and choose the safe way."),
    ]


def generation_prompts(world: World) -> list[str]:
    ms = world.facts["manuscript"]
    c = world.facts["child"]
    return [
        f'Write a bedtime story for a young child about {c.id}, a swimming pool, and an {ms.label}.',
        f'Write a gentle English story with nibble sounds and a careful ending where {c.id} protects a manuscript by the pool.',
        'Tell a short bedtime tale with repetition, sound effects, and a warning that keeps paper dry near water.',
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} label={e.label}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(place, manuscript) :- place(place), manuscript(manuscript).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MANUSCRIPTS:
        lines.append(asp.fact("manuscript", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.manuscript, params.child, params.child_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="swimming_pool", manuscript="english", child="Mia", child_gender="girl", helper="Leo", helper_gender="boy"),
    StoryParams(place="swimming_pool", manuscript="nibble", child="Noah", child_gender="boy", helper="Ava", helper_gender="girl"),
    StoryParams(place="swimming_pool", manuscript="manuscript", child="Lily", child_gender="girl", helper="Finn", helper_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
