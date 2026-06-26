#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/gore_foreshadowing_transformation_fable.py
==============================================================================================================================

A standalone *story world* sketch for a fable-like tale involving gore, foreshadowing, and transformation.

Seed story (used to build a world model):
---
In a quiet forest, there lived a proud fox named Felix who wore a bright red coat. 
Felix loved to hunt and show off his kills. One day, an old badger told Felix: 
"The forest repays pride with pain." Felix laughed and continued his hunt.

That evening, Felix chased a rabbit into a hunter's trap. The steel jaws snapped shut on 
his leg, tearing flesh and splintering bone. Felix screamed as blood soaked his beautiful 
red coat. He lay there all night, bleeding and alone.

The next morning, the old badger found Felix. The badger said: "Your pride has cost you 
your leg, but not your life." Using herbs and spider silk, the badger bound Felix's wound. 
Felix's leg healed, but he walked with a limp forever. His red coat was stained with 
gore and never looked the same.

From that day on, Felix limped through the forest, hunting only what he needed. 
He kept the scar as a warning against pride.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make shared containers importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
GORE_KINDS = {"bleeding", "mangled", "scarred"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "creature"
    type: str = "fox"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    # Physical and emotional meters
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"fox", "badger", "wolf", "stag"}
        female = {"vixen", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the quiet forest"
    affords: set[str] = field(default_factory=set)


@dataclass
class Omen:
    """Foreshadowing device: a sign or prophecy."""
    id: str
    phrase: str
    warning: str
    keyword: str = "omen"


@dataclass
class Injury:
    """A gory injury with lasting consequences."""
    location: str     # leg, flank, eye, ear
    severity: str     # minor, severe, crippling
    scar: str         # how it looks healed
    gore_desc: str    # the gory description
    transforms: str   # what changes in the creature


@dataclass
class Transformation:
    """The moral lesson sealed by the injury."""
    before: str       # old behavior
    after: str        # new behavior
    lesson: str       # the fable's moral


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.omen: Optional[Omen] = None
        self.injury: Optional[Injury] = None
        self.transformation: Optional[Transformation] = None
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def creatures(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "creature"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.omen = self.omen
        clone.injury = self.injury
        clone.transformation = self.transformation
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules: gore, punishment, and transformation
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_gore(world: World) -> list[str]:
    """Apply gore when a creature enters a trap or gets punished."""
    out = []
    for creature in world.creatures():
        if creature.meters["in_trap"] >= THRESHOLD and creature.meters["gore"] < THRESHOLD:
            injury = world.injury
            if injury:
                creature.meters["gore"] += 1
                creature.meters["bleeding"] += 1
                for kind in GORE_KINDS:
                    creature.meters[kind] += 1
                sig = ("gore", creature.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append(injury.gore_desc)
    return out


def _r_omen_fulfilled(world: World) -> list[str]:
    """The omen comes true after the gore."""
    out = []
    for creature in world.creatures():
        if creature.meters["gore"] >= THRESHOLD and creature.memes["warned"] >= THRESHOLD:
            sig = ("omen", creature.id)
            if sig not in world.fired:
                world.fired.add(sig)
                if world.omen:
                    out.append(f'The words of the {world.omen.warning} echoed in the air.')
    return out


def _r_transformation(world: World) -> list[str]:
    """The creature transforms after healing."""
    out = []
    for creature in world.creatures():
        if creature.meters["healed"] >= THRESHOLD and creature.memes["pride"] > 0:
            sig = ("transform", creature.id)
            if sig not in world.fired:
                world.fired.add(sig)
                creature.memes["pride"] = 0
                creature.memes["wisdom"] += 1
                if world.transformation:
                    out.append(world.transformation.after)
    return out


CAUSAL_RULES = [
    Rule(name="gore", apply=_r_gore),
    Rule(name="omen_fulfilled", apply=_r_omen_fulfilled),
    Rule(name="transformation", apply=_r_transformation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            if s != "__marker__":
                world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(place="the quiet forest", affords={"hunt", "chase"}),
    "meadow": Setting(place="the golden meadow", affords={"hunt", "chase"}),
    "marsh": Setting(place="the dark marsh", affords={"hunt"}),
}

OMENS = [
    Omen(
        id="badger_omen",
        phrase="The forest repays pride with pain.",
        warning="a grizzled badger",
        keyword="omen",
    ),
    Omen(
        id="owl_omen",
        phrase="What shines bright will bleed bright.",
        warning="a wise old owl",
        keyword="omen",
    ),
    Omen(
        id="crow_omen",
        phrase="The proudest coat stains the deepest.",
        warning="a watching crow",
        keyword="omen",
    ),
]

INJURIES = [
    Injury(
        location="leg",
        severity="crippling",
        scar="a jagged scar ran down his leg, fur never growing back",
        gore_desc=(
            "The steel jaws snapped shut on his leg, tearing flesh and "
            "splintering bone. Blood soaked his beautiful coat in a "
            "spreading stain of crimson gore."
        ),
        transforms="His pride was replaced by a quiet limp.",
    ),
    Injury(
        location="flank",
        severity="severe",
        scar="a pale streak across his side where the fur stayed white",
        gore_desc=(
            "The trap's teeth bit deep into his flank, ripping open "
            "skin and muscle. Gore poured down his side, matting the fur "
            "into wet red clumps."
        ),
        transforms="He never ran as fast again, but he learned to walk softly.",
    ),
    Injury(
        location="ear",
        severity="minor",
        scar="a missing tip on his left ear, forever nicked",
        gore_desc=(
            "The snare wire cut through his ear like a hot blade. "
            "Blood dripped onto the leaves, each drop a small red coin "
            "of pain. The gore was slight but the shame was deep."
        ),
        transforms="He listened more and boasted less after that day.",
    ),
]

TRANSFORMATIONS = [
    Transformation(
        before="He hunted and showed off his kills with pride.",
        after="He limped through the forest, hunting only what he needed, the gore-stained scar a warning against pride.",
        lesson="Pride invites pain; humility heals.",
    ),
    Transformation(
        before="She wore her beauty like a trophy and mocked the slow.",
        after="She moved through the shadows, silent and watchful, her torn flank a constant reminder of what speed costs.",
        lesson="The fastest runner stumbles hardest.",
    ),
    Transformation(
        before="He took what he wanted and laughed at the weak.",
        after="He shared his kill with the old and the young, and the others noticed the change in his walk.",
        lesson="Strength without kindness is just a trap waiting to spring.",
    ),
]

NAMES = ["Felix", "Runa", "Kael", "Vix", "Briar", "Ash", "Cinder", "Moss", "Thorn", "Fern"]
TRAITS = ["proud", "swift", "cunning", "beautiful", "bold", "sly", "quick"]
CREATURE_TYPES = ["fox", "vixen"]


# ---------------------------------------------------------------------------
# Prediction and reasonableness gates
# ---------------------------------------------------------------------------
def omen_fits(omen: Omen, creature: Entity) -> bool:
    """Check the omen matches the creature's flaw."""
    if creature.memes["pride"] >= THRESHOLD and "pride" in omen.warning.lower():
        return True
    if creature.memes["beauty"] >= THRESHOLD and "bright" in omen.phrase.lower():
        return True
    if creature.memes["cunning"] >= THRESHOLD and "proud" in omen.phrase.lower():
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    """(setting, omen_id, injury_location) combos that make sense."""
    combos = []
    for setting_id in SETTINGS:
        for omen in OMENS:
            for injury in INJURIES:
                combos.append((setting_id, omen.id, injury.location))
    return combos


# ---------------------------------------------------------------------------
# Story engine verbs
# ---------------------------------------------------------------------------
def introduce(world: World, creature: Entity) -> None:
    world.say(
        f"In {world.setting.place}, there lived a {creature.type} named "
        f"{creature.id} who was known for {creature.traits[0]} ways."
    )


def show_off(world: World, creature: Entity) -> None:
    creature.memes["pride"] += 1
    creature.memes[creature.traits[0]] += 1
    world.say(
        f"{creature.id} loved to hunt and show off {creature.pronoun('possessive')} "
        f"kills, wearing {creature.pronoun('possessive')} bright red coat like a trophy."
    )


def foretell_omen(world: World, creature: Entity, omen: Omen) -> None:
    world.omen = omen
    creature.memes["warned"] += 1
    world.add(Entity(
        id=f"prophet_{omen.id}",
        kind="creature",
        type="badger",
        label="the badger",
    ))
    world.say(
        f'One day, {omen.warning} told {creature.id}: '
        f'"{omen.phrase}" {creature.id} laughed and continued '
        f"{creature.pronoun('possessive')} hunt."
    )


def chase_prey(world: World, creature: Entity) -> None:
    world.say(
        f"That evening, {creature.id} chased a rabbit through the undergrowth, "
        f"ignoring every sign of danger."
    )


def trap_creature(world: World, creature: Entity, injury: Injury) -> None:
    world.injury = injury
    creature.meters["in_trap"] += 1
    world.say(
        f"A hunter's trap lay hidden beneath the leaves. The "
        f"steel jaws snapped shut on {creature.pronoun('possessive')} "
        f"{injury.location}."
    )
    propagate(world)


def suffer_gore(world: World, creature: Entity) -> None:
    world.say(
        f"{creature.id} screamed as gore soaked {creature.pronoun('possessive')} "
        f"beautiful red coat. {creature.pronoun().capitalize()} lay there all night, "
        f"bleeding and alone."
    )
    propagate(world)


def rescue(world: World, creature: Entity, omen: Omen) -> None:
    world.say(
        f"The next morning, {omen.warning} found {creature.id}. "
        f'"Your pride has cost you, but not your life," the old creature said.'
    )
    world.say(
        f"Using herbs and spider silk, the healer bound {creature.pronoun('possessive')} "
        f"wound. {creature.id}'s {world.injury.location} healed, but "
        f"{creature.pronoun()} walked with a limp forever."
    )
    creature.meters["healed"] += 1
    propagate(world)


def seal_transformation(world: World, creature: Entity, transformation: Transformation) -> None:
    world.transformation = transformation
    propagate(world)
    world.say(transformation.after)
    world.say(f'{transformation.lesson} — so the {creature.type} kept '
              f'{creature.pronoun("possessive")} scar as a warning.')


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, omen: Omen, injury: Injury, transformation: Transformation,
         creature_name: str = "Felix", creature_type: str = "fox",
         creature_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    traits = creature_traits or ["proud", "swift"]
    creature = world.add(Entity(
        id=creature_name,
        kind="creature",
        type=creature_type,
        traits=traits,
    ))
    creature.memes["pride"] = 1.0
    creature.memes[traits[0]] = 1.0

    # Act 1: Introduction and omen
    introduce(world, creature)
    show_off(world, creature)
    foretell_omen(world, creature, omen)

    # Act 2: The fall
    world.para()
    chase_prey(world, creature)
    trap_creature(world, creature, injury)
    suffer_gore(world, creature)

    # Act 3: Transformation
    world.para()
    rescue(world, creature, omen)
    seal_transformation(world, creature, transformation)

    world.facts.update(
        creature=creature,
        omen=omen,
        injury=injury,
        transformation=transformation,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    omen: str
    injury_location: str
    transformation: str
    name: str
    creature_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["creature"]
    o = f["omen"]
    t = f["transformation"]
    return [
        f'Write a fable about a {c.type} named {c.id} who learns about humility through gore.',
        f"Tell a story where an omen foretells a painful transformation for a proud {c.type}.",
        f'Create a folk tale using the words "{c.id}", "{o.keyword}", and "scar".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["creature"]
    o = f["omen"]
    inj = f["injury"]
    t = f["transformation"]
    p, sub, pos = c.pronoun("subject"), c.pronoun("object"), c.pronoun("possessive")

    qa = [
        QAItem(
            question=f"Who lived in {world.setting.place} and was known for {pos} proud ways?",
            answer=(
                f"A {c.type} named {c.id} lived in {world.setting.place}. "
                f"{p.capitalize()} was proud and loved to show off."
            ),
        ),
        QAItem(
            question=f"What did the old {o.warning} tell {c.id} before the injury?",
            answer=(
                f'The old creature said: "{o.phrase}" This was the omen that '
                f"foreshadowed what would happen."
            ),
        ),
        QAItem(
            question=f"How did {c.id} get hurt, and what gore followed?",
            answer=(
                f"{c.id} stepped into a hunter's trap. The steel jaws bit into "
                f"{pos} {inj.location}. {inj.gore_desc.split('.')[0]}."
            ),
        ),
    ]

    if c.memes["wisdom"] >= THRESHOLD:
        qa.append(QAItem(
            question=f"How did {c.id} change after the injury healed?",
            answer=(
                f"{p.capitalize()} was no longer proud. {t.after} "
                f"The scar stayed as a lesson."
            ),
        ))

    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an omen in a story?",
            answer="An omen is a sign or warning that something bad or important will happen later.",
        ),
        QAItem(
            question="Why do scars sometimes stay forever?",
            answer="When a wound is deep enough, the body cannot replace all the damaged tissue, so a scar forms. In stories, scars remind characters of past mistakes.",
        ),
        QAItem(
            question="What does a fable teach?",
            answer="A fable is a short story that teaches a moral lesson, often with animals as characters.",
        ),
        QAItem(
            question="Why is gore used in serious stories?",
            answer="Gore shows the real cost of mistakes and makes the transformation feel earned and painful, not magical.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable domain: an omen, gore, and transformation.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--omen", choices=[o.id for o in OMENS])
    ap.add_argument("--injury", choices=[i.location for i in INJURIES])
    ap.add_argument("--transformation-id", type=int, choices=list(range(len(TRANSFORMATIONS))))
    ap.add_argument("--creature-type", choices=["fox", "vixen"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    setting_id = args.setting or rng.choice(list(SETTINGS))
    omen_id = args.omen or rng.choice([o.id for o in OMENS])
    injury_loc = args.injury or rng.choice([i.location for i in INJURIES])
    trans_idx = args.transformation_id if args.transformation_id is not None else rng.randint(0, len(TRANSFORMATIONS) - 1)
    name = args.name or rng.choice(NAMES)
    ctype = args.creature_type or rng.choice(CREATURE_TYPES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        omen=omen_id,
        injury_location=injury_loc,
        transformation=TRANSFORMATIONS[trans_idx].lesson,
        name=name,
        creature_type=ctype,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    omen = next(o for o in OMENS if o.id == params.omen)
    injury = next(i for i in INJURIES if i.location == params.injury_location)
    trans = next(t for t in TRANSFORMATIONS if t.lesson == params.transformation)
    world = tell(setting, omen, injury, trans, params.name, params.creature_type, [params.trait])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        w = sample.world
        print("\n--- world model state ---")
        for e in w.entities.values():
            m = {k: v for k, v in {**e.meters, **e.memes}.items() if v}
            print(f"  {e.id:8} ({e.type:8}) {dict(m)}")
    if qa:
        print()
        for label, items in [("Prompts", sample.prompts),
                              ("Story QA", sample.story_qa),
                              ("World QA", sample.world_qa)]:
            print(f"== {label} ==")
            for item in items:
                if hasattr(item, 'question'):
                    print(f"Q: {item.question}\nA: {item.answer}\n")
                else:
                    print(f"- {item}")


def main():
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    CURATED = [
        StoryParams("forest", "badger_omen", "leg", TRANSFORMATIONS[0].lesson, "Felix", "fox", "proud"),
        StoryParams("meadow", "owl_omen", "flank", TRANSFORMATIONS[1].lesson, "Runa", "vixen", "swift"),
        StoryParams("marsh", "crow_omen", "ear", TRANSFORMATIONS[2].lesson, "Kael", "fox", "cunning"),
    ]

    samples = []
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
        header = f"### {sample.params.name}: {sample.params.omen} at {sample.params.setting}" if args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
