#!/usr/bin/env python3
"""
A standalone story world for a small mythic suspense tale about a raccoon,
a sacred drug (treated here as a healing medicine/potion), and a tense choice
that resolves through wisdom rather than force.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    guardian_name: str
    guardian_type: str
    item: str
    seed: Optional[int] = None


@dataclass
class Place:
    id: str
    label: str
    mood: str
    hiding: str


@dataclass
class Ingredient:
    id: str
    label: str
    phrase: str
    danger: str
    cure: str
    clue: str


PLACES = {
    "moon_forest": Place("moon_forest", "the moonlit forest", "silver and hushed", "under the roots"),
    "river_temple": Place("river_temple", "the river temple", "wet and echoing", "behind the shrine"),
    "hill_clearing": Place("hill_clearing", "the hill clearing", "open and windy", "inside a stone bowl"),
}

INGREDIENTS = {
    "drug": Ingredient(
        id="drug",
        label="holy drug",
        phrase="a small vial of healing drug",
        danger="a bitter curse was spreading",
        cure="could calm the curse",
        clue="the vial was cold as river glass",
    ),
    "moon_salt": Ingredient(
        id="moon_salt",
        label="moon salt",
        phrase="a pinch of moon salt",
        danger="the moon path was fading",
        cure="could keep the lantern bright",
        clue="the salt glittered like frost",
    ),
    "ember_leaf": Ingredient(
        id="ember_leaf",
        label="ember leaf",
        phrase="an ember leaf wrapped in cloth",
        danger="the fire altar was going dark",
        cure="could warm a sleeping heart",
        clue="the leaf smelled like autumn smoke",
    ),
}

GIRL_NAMES = ["Mira", "Nia", "Luna", "Sera", "Ari"]
BOY_NAMES = ["Rowan", "Eli", "Taro", "Finn", "Joss"]
GUARDIANS = [
    ("sage", "sage"),
    ("mother", "mother"),
    ("father", "father"),
    ("priest", "priest"),
]


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    item = INGREDIENTS[params.item]
    world = World(setting=place.label)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        role="seeker",
        meters={"courage": 1.0},
        memes={"awe": 1.0, "worry": 1.0},
    ))
    guardian = world.add(Entity(
        id=params.guardian_name,
        kind="character",
        type=params.guardian_type,
        role="guardian",
        meters={"age": 1.0},
        memes={"worry": 1.0, "wisdom": 1.0},
    ))
    relic = world.add(Entity(
        id=item.id,
        kind="thing",
        type="medicine",
        label=item.label,
        phrase=item.phrase,
        owner=guardian.id,
        caretaker=guardian.id,
    ))

    # Act I
    world.say(
        f"In {place.label}, where the air was {place.mood}, "
        f"{hero.id} heard an old tale of {item.label}."
    )
    world.say(
        f"The people said {item.phrase} was kept close because {item.danger}."
    )
    world.say(
        f"{hero.id} longed to help {guardian.id}, who guarded the medicine like a star in the dark."
    )

    # Act II
    world.para()
    world.say(
        f"One night, when the lamps were thin and the wind whispered under the trees, "
        f"{relic.label} vanished from its hiding place {place.hiding}."
    )
    world.say(
        f"{hero.id} saw a tiny trail of ash, and {hero.pronoun('possessive')} heart beat fast."
    )
    world.say(
        f"If the medicine was lost too long, {item.cure} could not happen in time."
    )
    world.say(
        f"{guardian.id} looked at the empty place and said, "
        f"\"This is a dangerous silence.\""
    )

    # Suspense beat
    world.say(
        f"{hero.id} followed the clue into the dark, where every shadow looked like a racoon."
    )
    world.say(
        f"Then a real racoon appeared on a branch, holding the vial with careful paws."
    )
    world.facts["racoon_found"] = True
    world.facts["medicine_lost"] = True
    world.facts["item"] = item.id
    world.facts["hero"] = hero.id
    world.facts["guardian"] = guardian.id
    world.facts["place"] = place.id

    # Turn
    world.para()
    world.say(
        f"The racoon did not snarl. It only stared at the moon, as if it had been sent by an older spell."
    )
    world.say(
        f"{hero.id} remembered the tale: the forest tested the kind and frightened the same way."
    )
    world.say(
        f"Softly, {hero.id} offered a berry cake and a bowl of water."
    )
    world.say(
        f"The racoon lowered the vial at once, for it had been hungry, not cruel."
    )
    world.say(
        f"Under the branches, the medicine glimmered again, and the night felt less sharp."
    )

    # Act III
    world.para()
    world.say(
        f"{guardian.id} held {relic.phrase} to the lantern and saw it was still safe."
    )
    world.say(
        f"{hero.id} carried the vial home, and {guardian.id} said the old cure could begin."
    )
    world.say(
        f"By dawn, the sick child in the temple slept easier, and the fear in the hall had faded."
    )
    world.say(
        f"The racoon returned to the roots with its berry cake, while the moon kept watch above the trees."
    )
    world.say(
        f"That was how the forest learned that a patient heart can solve a night full of suspense."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic suspense story for children that includes the word "drug" and a racoon.',
        f"Tell a gentle story where {f['hero']} searches for a lost medicine in {PLACES[f['place']].label}.",
        f"Write a small myth about a racoon, a sacred remedy, and a brave choice in the dark.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    guardian = world.facts["guardian"]
    place = PLACES[world.facts["place"]].label
    item = INGREDIENTS[world.facts["item"]]
    return [
        QAItem(
            question=f"Who looked for the lost medicine?",
            answer=f"{hero} looked for the lost medicine in {place}.",
        ),
        QAItem(
            question=f"What did the racoon carry?",
            answer=f"The racoon carried {item.phrase}.",
        ),
        QAItem(
            question=f"Why was everyone worried?",
            answer=f"Everyone was worried because the healing drug had vanished and the cure needed it.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"The problem was solved when {hero} offered food kindly, and the racoon gave back the vial.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a racoon?",
            answer="A racoon is a small wild animal with clever paws and a bandit-like face mask.",
        ),
        QAItem(
            question="What is a drug in this story?",
            answer="In this story, the drug is a healing medicine or potion, not a toy.",
        ),
        QAItem(
            question="What does suspense mean?",
            answer="Suspense means feeling tense and wondering what will happen next.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story that explains a mysterious world with magic, symbols, or great deeds.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(moon_forest). place(river_temple). place(hill_clearing).

ingredient(drug). ingredient(moon_salt). ingredient(ember_leaf).

feature(suspense).
style(myth).

hero_can_search(P) :- place(P).
lost_item(I) :- ingredient(I).
story_ok(P, I) :- hero_can_search(P), lost_item(I), feature(suspense), style(myth).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in INGREDIENTS:
        lines.append(asp.fact("ingredient", iid))
    lines.append(asp.fact("feature", "suspense"))
    lines.append(asp.fact("style", "myth"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    atoms = set(asp.atoms(model, "story_ok"))
    expected = {(p, i) for p in PLACES for i in INGREDIENTS}
    if atoms == expected:
        print(f"OK: ASP parity matches Python registry ({len(atoms)} combinations).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("ASP only:", sorted(atoms - expected))
    print("Python only:", sorted(expected - atoms))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    item = args.item or rng.choice(sorted(INGREDIENTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    guardian_type = args.guardian_type or rng.choice([g[0] for g in GUARDIANS])
    guardian_name = args.guardian_name or guardian_type.capitalize()
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        guardian_name=guardian_name,
        guardian_type=guardian_type,
        item=item,
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("\n== Story QA ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("\n== World QA ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic suspense story world with a racoon and a healing drug.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(INGREDIENTS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--guardian-name")
    ap.add_argument("--guardian-type", choices=["sage", "mother", "father", "priest"])
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


CURATED = [
    StoryParams("moon_forest", "Mira", "girl", "Sage", "sage", "drug", 1),
    StoryParams("river_temple", "Rowan", "boy", "Mother", "mother", "moon_salt", 2),
    StoryParams("hill_clearing", "Luna", "girl", "Father", "father", "ember_leaf", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show story_ok/2."))
        atoms = sorted(set(asp.atoms(model, "story_ok")))
        print(f"{len(atoms)} story combinations:\n")
        for p, i in atoms:
            print(f"  {p:14} {i}")
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        for idx in range(args.n):
            rng = random.Random(base_seed + idx)
            params = resolve_params(args, rng)
            params.seed = base_seed + idx
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
