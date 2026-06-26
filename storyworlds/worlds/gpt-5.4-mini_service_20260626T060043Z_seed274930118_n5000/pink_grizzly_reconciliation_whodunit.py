#!/usr/bin/env python3
"""
A small whodunit-style storyworld about a missing pink ribbon, a grizzly
suspect, and a reconciliation that turns suspicion into understanding.

The world is intentionally tiny: one scene, a few typed entities, physical
state (meters) and emotional state (memes), and a detective-like resolution
driven by clues rather than frozen prose.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core entities
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    surfaces: list[str]
    clues: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    suspect: str
    suspect_type: str
    missing_item: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
ROOMS = {
    "lobby": Room(
        name="the lodge lobby",
        surfaces=["floor", "bench", "doormat"],
        clues=["pink thread", "wet pawprint", "dusty shelf"],
    ),
    "porch": Room(
        name="the front porch",
        surfaces=["steps", "railing", "mat"],
        clues=["pink ribbon", "mud trail", "scratch mark"],
    ),
    "workroom": Room(
        name="the workroom",
        surfaces=["table", "crate", "lamp"],
        clues=["pink paint speck", "folded note", "fur tuft"],
    ),
}

HERO_NAMES = ["Nina", "Milo", "Tess", "Jun", "Pia", "Owen"]
HELPER_NAMES = ["Aunt Bea", "Mr. Finch", "Captain Rose", "Mina"]
SUSPECT_NAMES = ["Grizzly", "Grizz", "Old Grizzly", "Griz"]

MISSING_ITEMS = {
    "ribbon": ("a pink ribbon", "ribbon"),
    "scarf": ("a pink scarf", "scarf"),
    "badge": ("a pink badge", "badge"),
}

TRACE_CLUES = {
    "ribbon": ["pink thread", "wet pawprint"],
    "scarf": ["pink ribbon", "mud trail"],
    "badge": ["pink paint speck", "folded note"],
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    room = ROOMS[params.place]
    world = World(room)

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type))
    suspect = world.add(Entity(id=params.suspect, kind="character", type=params.suspect_type))
    item_label, item_short = MISSING_ITEMS[params.missing_item]
    missing = world.add(Entity(
        id="missing",
        type="thing",
        label=item_short,
        phrase=item_label,
        owner=hero.id,
        caretaker=helper.id,
        location=room.name,
    ))

    # Physical state
    suspect.meters["fur"] = 1.0
    suspect.meters["mess"] = 0.0
    hero.memes["worry"] = 0.0
    helper.memes["calm"] = 1.0
    suspect.memes["embarrassment"] = 0.0
    suspect.memes["lonely"] = 0.0

    world.facts.update(hero=hero, helper=helper, suspect=suspect, missing=missing)
    world.facts["item_label"] = item_label
    world.facts["item_short"] = item_short
    return world


def clue_for_item(missing_item: str) -> list[str]:
    return TRACE_CLUES[missing_item]


def initial_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    missing: Entity = f["missing"]

    world.say(
        f"{hero.id} was a little curious {hero.type} who loved tidy rooms and tiny mysteries."
    )
    world.say(
        f"One morning at {world.room.name}, {hero.id} noticed that {missing.phrase} was gone."
    )
    world.say(
        f"{helper.id} knelt by the bench and said, \"Let's look carefully before we guess.\""
    )
    world.para()
    world.say(
        f"{hero.id} found a clue on the floor: {clue_for_item(world.facts['item_short'])[0]}."
    )
    world.say(
        f"Near the doormat sat {suspect.id}, the grizzly {suspect.type}, with a worried look and muddy paws."
    )
    world.say(
        f"{hero.id} narrowed {hero.pronoun('possessive')} eyes and thought the grizzly {suspect.type} must have taken it."
    )
    hero.memes["worry"] += 1.0
    suspect.memes["embarrassment"] += 1.0
    suspect.memes["lonely"] += 0.5


def inspect_clues(world: World) -> None:
    f = world.facts
    suspect: Entity = f["suspect"]
    helper: Entity = f["helper"]
    missing: Entity = f["missing"]

    world.say(
        f"{helper.id} pointed to the pink thread and then to the wet pawprint."
    )
    world.say(
        f"\"Those marks are clues,\" {helper.id} said. \"They do not prove who meant harm.\""
    )
    world.say(
        f"{hero_name(world)} noticed that the thread was snagged on a low nail by the door, not hidden away."
    )
    world.say(
        f"{suspect.id} lifted one paw and showed a strip of pink stuck to the fur."
    )
    suspect.meters["trace_pink"] = 1.0
    suspect.memes["embarrassment"] += 0.5
    world.facts["clue_set"] = set(clue_for_item(world.facts["item_short"]))
    world.facts["false_suspicion"] = True


def hero_name(world: World) -> str:
    return world.facts["hero"].id


def reveal(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    missing: Entity = f["missing"]

    world.say(
        f"Then {helper.id} noticed a tiny folded note on the shelf: the ribbon had been used to tie a wet bundle of papers together."
    )
    world.say(
        f"{hero.id} looked back at {suspect.id} and saw the truth: the grizzly {suspect.type} had not stolen {missing.it()}."
    )
    world.say(
        f"The pink ribbon had been borrowed to save the papers from the damp floor, and it had slipped off near the door."
    )
    world.facts["culprit"] = "accident"
    world.facts["reconciled"] = True


def reconcile(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    missing: Entity = f["missing"]

    suspect.memes["embarrassment"] = max(0.0, suspect.memes["embarrassment"] - 1.0)
    suspect.memes["lonely"] = max(0.0, suspect.memes["lonely"] - 0.5)
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    helper.memes["calm"] = 2.0

    world.say(
        f"{hero.id} blushed and said sorry for jumping to the wrong answer."
    )
    world.say(
        f"{suspect.id} gave a small grizzly huff, then nudged the ribbon back with a muddy paw."
    )
    world.say(
        f"{helper.id} smiled and helped {hero.id} tie {missing.it()} to the note again, this time with a dry string."
    )
    world.say(
        f"By the end, the grizzly {suspect.type} was not a suspect anymore, but a helper, and the pink ribbon was safe in plain sight."
    )


def tell_story(world: World) -> None:
    initial_story(world)
    world.para()
    inspect_clues(world)
    world.para()
    reveal(world)
    reconcile(world)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def validate_params(params: StoryParams) -> None:
    if params.place not in ROOMS:
        raise StoryError("The mystery needs a known place.")
    if params.missing_item not in MISSING_ITEMS:
        raise StoryError("The missing item must be one the world knows how to hide.")
    if not params.hero or not params.helper or not params.suspect:
        raise StoryError("The story needs a hero, a helper, and a suspect.")
    if params.hero == params.suspect:
        raise StoryError("The hero and the suspect must be different characters.")
    if params.helper == params.suspect:
        raise StoryError("The helper and the suspect must be different characters.")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A missing item can be found if there is a clue, a suspect, and a reconciliation.
found(Item) :- clue(Item,_), suspect(_), reconciliation.

% The suspect is cleared when the clue set matches the item and the hero apologizes.
cleared(S) :- suspect(S), clue(match), apology, reconciliation.

% A valid mystery is one where there is exactly one missing item and the ending reconciles.
valid_story(Place, Item) :- place(Place), missing(Item), reconciliation, clue(Item,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in ROOMS:
        lines.append(asp.fact("place", name))
    for item, (_, short) in MISSING_ITEMS.items():
        lines.append(asp.fact("missing", short))
        for clue in TRACE_CLUES[short]:
            lines.append(asp.fact("clue", short, clue))
        lines.append(asp.fact("item", short))
    lines.append(asp.fact("reconciliation"))
    lines.append(asp.fact("apology"))
    lines.append(asp.fact("clue", "match"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program("#show valid_story/2."), models=0)
    asp_set = set()
    for model in models:
        asp_set.update(asp.atoms(model, "valid_story"))
    py_set = {(p.place, MISSING_ITEMS[p.missing_item][1]) for p in CURATED}
    if asp_set == py_set:
        print(f"OK: ASP matches curated story types ({len(asp_set)} cases).")
        return 0
    print("MISMATCH between ASP and curated domain.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(ROOMS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["woman", "man"])
    suspect_type = args.suspect_type or "bear"
    missing_item = args.missing_item or rng.choice(list(MISSING_ITEMS))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    suspect = args.suspect or rng.choice(SUSPECT_NAMES)
    params = StoryParams(
        place=place,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        suspect=suspect,
        suspect_type=suspect_type,
        missing_item=missing_item,
    )
    validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = setup_world(params)
    tell_story(world)

    hero = world.facts["hero"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    missing = world.facts["missing"]

    prompts = [
        f"Write a short whodunit story about a missing {missing.phrase} and a grizzly suspect.",
        f"Tell a gentle mystery where {hero.id} and {helper.id} solve what happened to the {missing.label}.",
        f"Write a child-friendly reconciliation story using the words pink and grizzly.",
    ]

    story_qa = [
        QAItem(
            question=f"What went missing in {world.room.name}?",
            answer=f"{missing.phrase} went missing from {world.room.name}, which made {hero.id} start looking for clues.",
        ),
        QAItem(
            question=f"Who did {hero.id} first suspect?",
            answer=f"{hero.id} first suspected {suspect.id}, the grizzly {suspect.type}, because of the muddy paws and pink thread.",
        ),
        QAItem(
            question=f"What solved the mystery in the end?",
            answer=f"The clue on the shelf and the wet bundle of papers solved it, showing the ribbon had only been borrowed and then dropped.",
        ),
        QAItem(
            question=f"How did the story end for {suspect.id}?",
            answer=f"{suspect.id} was cleared and reconciled with {hero.id}, so the grizzly {suspect.type} ended the story as a helper instead of a suspect.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset with each other and make peace again.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what really happened.",
        ),
        QAItem(
            question="Why can muddy paws matter in a mystery?",
            answer="Muddy paws can matter because they can leave tracks that show where someone walked.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="porch",
        hero="Nina",
        hero_type="girl",
        helper="Aunt Bea",
        helper_type="woman",
        suspect="Grizzly",
        suspect_type="bear",
        missing_item="ribbon",
    ),
    StoryParams(
        place="lobby",
        hero="Milo",
        hero_type="boy",
        helper="Mr. Finch",
        helper_type="man",
        suspect="Grizz",
        suspect_type="bear",
        missing_item="scarf",
    ),
    StoryParams(
        place="workroom",
        hero="Tess",
        hero_type="girl",
        helper="Captain Rose",
        helper_type="woman",
        suspect="Old Grizzly",
        suspect_type="bear",
        missing_item="badge",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a pink clue and a grizzly suspect.")
    ap.add_argument("--place", choices=ROOMS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["woman", "man"])
    ap.add_argument("--suspect")
    ap.add_argument("--suspect-type", choices=["bear"])
    ap.add_argument("--missing-item", choices=MISSING_ITEMS)
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
    return build_params(args, rng)


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.hero} / {p.missing_item} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
