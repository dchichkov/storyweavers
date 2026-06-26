#!/usr/bin/env python3
"""
A compact tall-tale storyworld about an occasion, a reason, and a hen with a surprise.

Premise:
- A family is preparing for a small occasion.
- A hen keeps following a reason of its own: it wants a warm nest, a safe perch, and a quiet place.
- The surprise is an unexpected egg delivery that changes the mood of the day.

This world is designed to stay classical and state-driven:
- physical meters track things like carried items, warmth, and fullness
- emotional memes track surprise, worry, pride, and relief
- the story text is generated from the world state, not from a fixed paragraph with swapped names

It also includes an inline ASP twin for the reasonableness gate and registry parity.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when the script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Occasion:
    id: str
    label: str
    place: str
    reason: str
    weather: str = ""


@dataclass
class Surprise:
    id: str
    label: str
    reveal: str
    value: str


@dataclass
class StoryParams:
    occasion: str
    reason: str
    hen: str
    name: str
    caretaker: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------

class World:
    def __init__(self, occasion: Occasion) -> None:
        self.occasion = occasion
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

    def copy(self) -> "World":
        import copy
        clone = World(self.occasion)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

OCCASIONS = {
    "birthday": Occasion(
        id="birthday",
        label="a birthday picnic",
        place="the yard",
        reason="to celebrate a new candle day",
        weather="sunny",
    ),
    "harvest": Occasion(
        id="harvest",
        label="a harvest supper",
        place="the barn porch",
        reason="to thank the fields for their gifts",
        weather="golden",
    ),
    "visit": Occasion(
        id="visit",
        label="a family visit",
        place="the front porch",
        reason="to welcome faraway cousins",
        weather="breezy",
    ),
}

HENS = {
    "speckle": {"phrase": "a speckled hen with bright eyes", "label": "Speckle"},
    "goldie": {"phrase": "a gold-feathered hen with a proud strut", "label": "Goldie"},
    "pepper": {"phrase": "a peppery hen with a twitchy tail", "label": "Pepper"},
}

SURPRISES = {
    "egg": Surprise(
        id="egg",
        label="a warm surprise egg",
        reveal="a warm egg tucked under the straw",
        value="a fresh egg",
    ),
    "feather": Surprise(
        id="feather",
        label="a silver feather",
        reveal="a silver feather shining in the hay",
        value="a shiny feather",
    ),
}

NAMES = ["Mabel", "Tess", "Ruby", "Nina", "Willa", "June", "Sadie", "Lena"]
CARETTAKERS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["cheerful", "curious", "spirited", "patient", "lively"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def reasonableness_ok(occasion: Occasion, hen_key: str) -> bool:
    return occasion.id in OCCASIONS and hen_key in HENS


def explain_rejection(occasion_key: str, hen_key: str) -> str:
    if occasion_key not in OCCASIONS:
        return "(No story: that occasion is not part of this little world.)"
    if hen_key not in HENS:
        return "(No story: that hen is not part of this little world.)"
    return "(No story: the chosen tale would not have a clear surprise or reason.)"


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, hen: Entity, surprise: Surprise) -> None:
    world.say(
        f"{child.id} was a {child.memes.get('trait', 'cheerful')} child who liked big small-day things."
    )
    world.say(
        f"Nearby lived {hen.label}, {hen.phrase}, and everyone knew {hen.pronoun('subject')} had a mind of {hen.pronoun('possessive')} own."
    )
    world.say(
        f"There was a reason for the fuss: the family was having {world.occasion.label} because {world.occasion.reason}."
    )
    world.say(
        f"That morning, {child.id} kept hoping for a kind little surprise."
    )
    world.facts["surprise_label"] = surprise.label


def prepare(world: World, child: Entity, caretaker: Entity, hen: Entity) -> None:
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    caretaker.memes["busy"] = caretaker.memes.get("busy", 0) + 1
    world.say(
        f"{caretaker.label.capitalize()} set out cups and bread, while {child.id} ran to check the straw nest."
    )
    world.say(
        f"{hen.label} waddled after the warmest spot in the yard, as if {hen.pronoun('subject')} had a reason all her own."
    )


def hen_finds_reason(world: World, hen: Entity) -> None:
    hen.meters["nest_warmth"] = hen.meters.get("nest_warmth", 0) + 1
    hen.memes["calm"] = hen.memes.get("calm", 0) + 1
    world.say(
        f"{hen.label} found the straw nest just right. {hen.pronoun('subject').capitalize()} settled in with a soft cluck, quiet as a pillow."
    )


def surprise_reveal(world: World, child: Entity, caretaker: Entity, hen: Entity, surprise: Surprise) -> None:
    child.memes["surprise"] = child.memes.get("surprise", 0) + 1
    caretaker.memes["surprise"] = caretaker.memes.get("surprise", 0) + 1
    hen.meters["full"] = hen.meters.get("full", 0) + 1
    world.say(
        f"Then came the surprise: in the nest was {surprise.reveal}."
    )
    world.say(
        f"{child.id} blinked twice and laughed so hard the fence seemed to shake."
    )
    world.say(
        f"{caretaker.label.capitalize()} smiled, because the hen had done the day a grand favor."
    )


def ending(world: World, child: Entity, caretaker: Entity, hen: Entity, surprise: Surprise) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 2
    caretaker.memes["relief"] = caretaker.memes.get("relief", 0) + 1
    hen.memes["pride"] = hen.memes.get("pride", 0) + 1
    world.say(
        f"At {world.occasion.place}, the celebration went on with {surprise.value} in a little bowl, and {hen.label} pecked near the feet of the happy crowd."
    )
    world.say(
        f"The reason for the day stayed the same, but the surprise made it shine brighter."
    )
    world.say(
        f"By sunset, {child.id} was still grinning, {caretaker.label} was still thanking the hen, and {hen.label} looked as tall as a barn door."
    )


def tell_story(occasion: Occasion, hen_key: str, surprise: Surprise,
               child_name: str = "Mabel", caretaker_role: str = "mother",
               trait: str = "cheerful") -> World:
    world = World(occasion)
    child = world.add(Entity(id=child_name, kind="character", type="girl", label=child_name))
    child.memes["trait"] = trait
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_role, label=caretaker_role))
    hen_data = HENS[hen_key]
    hen = world.add(Entity(id=hen_data["label"], kind="animal", type="hen", label=hen_data["label"], phrase=hen_data["phrase"]))

    introduce(world, child, hen, surprise)
    world.para()
    prepare(world, child, caretaker, hen)
    hen_finds_reason(world, hen)
    world.para()
    surprise_reveal(world, child, caretaker, hen, surprise)
    ending(world, child, caretaker, hen, surprise)

    world.facts.update(
        child=child,
        caretaker=caretaker,
        hen=hen,
        surprise=surprise,
        occasion=occasion,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    hen = f["hen"]
    occ = f["occasion"]
    return [
        f'Write a small tall-tale story about {child.id}, {hen.label}, and a surprise at {occ.label}.',
        f"Tell a child-friendly tall tale where the reason for the day is {occ.reason} and a hen turns out to be the biggest surprise.",
        f"Write a short, playful story set at {occ.place} that includes a hen, a reason, and an unexpected surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caretaker = f["caretaker"]
    hen = f["hen"]
    occ = f["occasion"]
    surprise = f["surprise"]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {child.id}, the hen named {hen.label}, and the surprise they found at {occ.place}.",
        ),
        QAItem(
            question=f"Why was the family having {occ.label}?",
            answer=f"They were having {occ.label} because {occ.reason}.",
        ),
        QAItem(
            question=f"What was the surprise in the nest?",
            answer=f"The surprise was {surprise.reveal}.",
        ),
        QAItem(
            question=f"How did {child.id} feel when the surprise appeared?",
            answer=f"{child.id} felt surprised first and then very happy, because the little surprise made the whole day feel brighter.",
        ),
        QAItem(
            question=f"Why did the hen matter so much in the story?",
            answer=f"{hen.label} mattered because {hen.pronoun('subject')} followed a quiet reason of {hen.pronoun('possessive')} own and led everyone to the surprise.",
        ),
        QAItem(
            question=f"Who thanked the hen at the end?",
            answer=f"{caretaker.label.capitalize()} thanked the hen, and {child.id} was still smiling beside {heroic_phrase(child, hen)}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hen?",
            answer="A hen is a grown female chicken. Hens often scratch the ground, cluck softly, and sit on eggs to keep them warm.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something you did not expect. It can make people gasp, laugh, or smile wide.",
        ),
        QAItem(
            question="Why do eggs need warmth?",
            answer="Eggs need warmth so the little chick inside can stay safe and grow.",
        ),
    ]


def heroic_phrase(child: Entity, hen: Entity) -> str:
    return f"{child.id} and {hen.label}"


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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
occasion_ok(O) :- occasion(O).
hen_ok(H) :- hen(H).
valid_story(O, H) :- occasion_ok(O), hen_ok(H), surprise(S), compatible(O, H, S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for oid in OCCASIONS:
        lines.append(asp.fact("occasion", oid))
    for hid in HENS:
        lines.append(asp.fact("hen", hid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for oid in OCCASIONS:
        for hid in HENS:
            for sid in SURPRISES:
                lines.append(asp.fact("compatible", oid, hid, sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for oid in OCCASIONS:
        for hid in HENS:
            for sid in SURPRISES:
                combos.append((oid, hid, sid))
    return combos


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about an occasion, a reason, a hen, and a surprise.")
    ap.add_argument("--occasion", choices=OCCASIONS)
    ap.add_argument("--reason", choices=["birthday", "harvest", "visit"])
    ap.add_argument("--hen", choices=HENS)
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=CARETTAKERS)
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
    occ_key = args.occasion or rng.choice(sorted(OCCASIONS))
    reason_key = args.reason or occ_key
    hen_key = args.hen or rng.choice(sorted(HENS))
    if not reasonableness_ok(OCCASIONS[occ_key], hen_key):
        raise StoryError(explain_rejection(occ_key, hen_key))
    name = args.name or rng.choice(NAMES)
    caretaker = args.caretaker or rng.choice(CARETTAKERS)
    return StoryParams(
        occasion=occ_key,
        reason=reason_key,
        hen=hen_key,
        name=name,
        caretaker=caretaker,
    )


def generate(params: StoryParams) -> StorySample:
    occasion = OCCASIONS[params.occasion]
    surprise = SURPRISES["egg"] if params.reason in {"birthday", "harvest"} else SURPRISES["feather"]
    world = tell_story(
        occasion=occasion,
        hen_key=params.hen,
        surprise=surprise,
        child_name=params.name,
        caretaker_role=params.caretaker,
        trait="cheerful",
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for occ, hen in sorted(set(combos)):
            print(f"  {occ:10} {hen}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for occ in OCCASIONS:
            for hen in HENS:
                p = StoryParams(occasion=occ, reason=occ, hen=hen, name="Mabel", caretaker="mother")
                samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
