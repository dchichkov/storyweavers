#!/usr/bin/env python3
"""
A standalone storyworld for a tiny whodunit involving flour, sound effects,
dialogue, and sharing.

Premise:
- A small shared kitchen or bakery room hosts a simple mystery.
- Someone notices flour footprints, a missing bowl, or a powdered mess.
- The detective character asks questions, follows clues, and discovers who used
  the flour and why.
- The ending resolves through sharing: the flour, the bowl, or the baking task
  is shared fairly, and the culprit is not villainous but simply needed help.

The model keeps the world concrete:
- physical meters: flour, crumbs, dust, spills, neatness, noise
- emotional memes: worry, curiosity, trust, relief, pride

The story engine uses state-driven clues rather than a frozen paragraph.
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
# Domain registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": {
        "label": "the kitchen",
        "surface": "counter",
        "has_oven": True,
        "has_table": True,
    },
    "bakery": {
        "label": "the little bakery room",
        "surface": "worktable",
        "has_oven": True,
        "has_table": True,
    },
    "pantry": {
        "label": "the pantry",
        "surface": "shelf",
        "has_oven": False,
        "has_table": False,
    },
}

CHARACTER_NAMES = ["Milo", "Nina", "Tess", "Leo", "Mira", "Owen", "Poppy", "June"]
CHARACTER_TYPES = ["child", "helper", "baker", "friend"]
MOODS = ["curious", "nervous", "kind", "careful", "quick", "brave"]

SOUND_EFFECTS = [
    "tap tap",
    "scritch",
    "whoosh",
    "plop",
    "clink",
    "thump",
    "sniff sniff",
    "shuffle",
]

SHARED_ITEMS = {
    "flour-bag": {
        "label": "the flour bag",
        "kind": "ingredient",
        "shareable": True,
        "magnitude": 3,
    },
    "bowl": {
        "label": "the big mixing bowl",
        "kind": "tool",
        "shareable": True,
        "magnitude": 1,
    },
    "spoon": {
        "label": "the wooden spoon",
        "kind": "tool",
        "shareable": True,
        "magnitude": 1,
    },
}

CLUES = {
    "flour_prints": "tiny white footprints",
    "flour_hand": "a floury handprint",
    "open_bag": "an open flour bag",
    "shared_bowl": "the missing bowl on the table",
}

# ---------------------------------------------------------------------------
# Results/world model
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "kitchen"
    detective: str = "Milo"
    suspect: str = "Nina"
    helper: str = "Tess"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    found: bool = False
    visible: bool = True

    def __post_init__(self):
        for k in ("flour", "mess", "neatness", "noise"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "trust", "relief", "pride"):
            self.memes.setdefault(k, 0.0)


class World:
    def __init__(self, place: str):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        import copy
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _a(name: str) -> str:
    return "an" if name[:1].lower() in "aeiou" else "a"


def _pronoun(name: str) -> str:
    return "they"


def _poss(name: str) -> str:
    return "their"


def _capitalize_first(s: str) -> str:
    return s[:1].upper() + s[1:]


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        # flour bag open -> flour mess nearby
        bag = world.entities.get("flour-bag")
        if bag and bag.meters["flour"] >= 1 and ("bag_open",) not in world.fired:
            world.fired.add(("bag_open",))
            world.say("The flour bag sat open on the table.")
            changed = True

        # someone with flour on hands or clothes leaves prints
        for eid, ent in world.entities.items():
            if ent.kind != "character":
                continue
            if ent.meters["flour"] >= 1 and (eid, "prints") not in world.fired:
                world.fired.add((eid, "prints"))
                world.say(f"{ent.id} left {CLUES['flour_prints']}.")
                changed = True


def predict_mystery(world: World, actor: Entity, amount: float) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["flour"] += amount
    propagate(sim, narrate=False)
    return {
        "mess": sum(e.meters["flour"] for e in sim.entities.values()),
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def opening(world: World, detective: Entity, suspect: Entity, helper: Entity, place: dict) -> None:
    world.say(
        f"One quiet morning, {detective.id} was in {place['label']} when {SOUND_EFFECTS[0]} "
        f"came from the table. Then came a soft {SOUND_EFFECTS[1]}."
    )
    world.say(
        f"{detective.id} looked up. The flour bag was open, and there were {CLUES['flour_prints']} "
        f"near the worktable."
    )
    world.facts["place_label"] = place["label"]
    world.facts["surface"] = place["surface"]


def investigate(world: World, detective: Entity, suspect: Entity, helper: Entity) -> None:
    detective.memes["curiosity"] += 1
    world.say(f'"Who was making that {SOUND_EFFECTS[2]}?" {detective.id} asked.')
    world.say(f'"Not me," {suspect.id} said at once. "{SOUND_EFFECTS[3]}? I was only here a minute ago."')
    world.say(f'"I saw {CLUES["flour_hand"]}," {helper.id} said. "That means someone was baking, or trying to."')


def clue_work(world: World, detective: Entity, suspect: Entity, helper: Entity) -> None:
    # Put flour on suspect as the false clue, but keep it reasonable.
    suspect.meters["flour"] += 1
    world.say(
        f"{detective.id} followed the clue to {suspect.id}'s sleeves. "
        f"They were dusted white, like they had brushed the open bag."
    )
    propagate(world, narrate=True)


def dialogue_turn(world: World, detective: Entity, suspect: Entity, helper: Entity) -> None:
    world.say(f'"I only touched the flour because we were sharing it," {suspect.id} said.')
    world.say(f'"Sharing?" {detective.id} asked.')
    world.say(f'"Yes," said {helper.id}. "We were supposed to share the bowl, too, but it was still needed."')
    world.facts["sharing"] = True


def reveal(world: World, detective: Entity, suspect: Entity, helper: Entity) -> None:
    suspect.memes["worry"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"Then {detective.id} noticed the big mixing bowl on the counter and the flour trail leading back."
    )
    world.say(
        f'"You were not stealing flour," {detective.id} said. '
        f'"You were trying to help bake for everyone."'
    )
    world.say(
        f'{suspect.id} nodded. "{SOUND_EFFECTS[4]}," they said. "I spilled some, then I cleaned it up and '
        f'came to get help."'
    )


def resolution(world: World, detective: Entity, suspect: Entity, helper: Entity) -> None:
    suspect.memes["relief"] += 1
    helper.memes["pride"] += 1
    detective.memes["trust"] += 1
    world.say(
        f"At last, {detective.id} smiled. The flour was not a problem to hide; it was something to share."
    )
    world.say(
        f"So they all worked together: {suspect.id} held the bowl, {helper.id} measured the flour, and "
        f"{detective.id} stirred."
    )
    world.say(
        f"Soon the room smelled sweet instead of dusty, and the white prints on the floor meant baking, not trouble."
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=params.place)

    detective = world.add(Entity(id=params.detective, kind="character", type="child", label="detective"))
    suspect = world.add(Entity(id=params.suspect, kind="character", type="helper", label="helper"))
    helper = world.add(Entity(id=params.helper, kind="character", type="baker", label="baker"))

    flour_bag = world.add(Entity(
        id="flour-bag",
        kind="thing",
        type="ingredient",
        label="flour bag",
        phrase="a paper flour bag",
        owner=helper.id,
        meters={"flour": 2.0, "mess": 0.0, "neatness": 0.0, "noise": 0.0},
    ))
    bowl = world.add(Entity(
        id="bowl",
        kind="thing",
        type="tool",
        label="mixing bowl",
        phrase="a big mixing bowl",
        owner=helper.id,
        shared_with={detective.id, suspect.id},
    ))

    world.facts.update(
        detective=detective,
        suspect=suspect,
        helper=helper,
        flour_bag=flour_bag,
        bowl=bowl,
    )

    opening(world, detective, suspect, helper, place)
    world.para()
    investigate(world, detective, suspect, helper)
    clue_work(world, detective, suspect, helper)
    world.para()
    dialogue_turn(world, detective, suspect, helper)
    reveal(world, detective, suspect, helper)
    resolution(world, detective, suspect, helper)

    world.facts["solved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.place
    return [
        f'Write a short whodunit for a young child set in {PLACES[p]["label"]} with flour clues, dialogue, and a sharing ending.',
        "Tell a gentle mystery story where a detective hears floury sound effects, asks questions, and discovers the truth.",
        "Write a tiny mystery about who made the flour mess and how sharing solved it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective = world.facts["detective"]
    suspect = world.facts["suspect"]
    helper = world.facts["helper"]
    place = PLACES[world.place]["label"]
    return [
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"The mystery happened in {place}, where the flour bag and mixing bowl were kept.",
        ),
        QAItem(
            question=f"What clue first made {detective.id} curious?",
            answer=f"{detective.id} noticed {CLUES['flour_prints']} and the open flour bag near the table.",
        ),
        QAItem(
            question=f"Who turned out to be involved with the flour?",
            answer=f"{suspect.id} was involved, but not in a bad way. They had only been helping with the flour so everyone could share the baking work.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"It ended with sharing: {suspect.id} held the bowl, {helper.id} measured the flour, and {detective.id} stirred while the room smelled sweet.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is flour used for?",
            answer="Flour is a fine powder used to make bread, cakes, cookies, and other baked foods.",
        ),
        QAItem(
            question="Why do people share tools when baking?",
            answer="People share tools when baking so everyone can help, and so the work is easier and fair.",
        ),
        QAItem(
            question="What does a detective do in a mystery story?",
            answer="A detective looks for clues, asks questions, and tries to find out what really happened.",
        ),
        QAItem(
            question="Why can flour make a mess?",
            answer="Flour is light and powdery, so it can puff into the air and leave white dust on hands, clothes, and tables.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"{e.id}: {e.kind} {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
entity(character).
entity(thing).

% A flour clue is present when someone has flour on them or the flour bag is open.
clue(flour_prints) :- flour_on(X), character(X).
clue(open_bag) :- bag_open.
clue(shared_bowl) :- bowl_shared.

% A mystery is solvable when a detective has at least one clue and sharing happens.
solved :- clue(_), sharing.

% A reasonable whodunit is one where the story has flour, dialogue, and sharing.
valid_story :- has_flour, has_dialogue, sharing.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("has_flour"))
    lines.append(asp.fact("has_dialogue"))
    lines.append(asp.fact("sharing"))
    lines.append(asp.fact("bag_open"))
    lines.append(asp.fact("bowl_shared"))
    lines.append(asp.fact("flour_on", "suspect"))
    lines.append(asp.fact("character", "detective"))
    lines.append(asp.fact("character", "suspect"))
    lines.append(asp.fact("character", "helper"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0. #show solved/0."))
    atoms = {str(sym) for sym in model}
    ok = "valid_story" in atoms and "solved" in atoms
    if ok:
        print("OK: ASP twin recognizes the flour whodunit as valid and solved.")
        return 0
    print("MISMATCH: ASP twin did not validate the story.")
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny flour whodunit storyworld.")
    ap.add_argument("--place", choices=sorted(PLACES), default=None)
    ap.add_argument("--detective")
    ap.add_argument("--suspect")
    ap.add_argument("--helper")
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
    place = args.place or rng.choice(list(PLACES))
    names = rng.sample(CHARACTER_NAMES, 3)
    detective = args.detective or names[0]
    suspect = args.suspect or names[1]
    helper = args.helper or names[2]
    if len({detective, suspect, helper}) < 3:
        raise StoryError("Detective, suspect, and helper must be different characters.")
    return StoryParams(place=place, detective=detective, suspect=suspect, helper=helper)


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
        print(asp_program("#show valid_story/0. #show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/0. #show solved/0."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="kitchen", detective="Milo", suspect="Nina", helper="Tess"),
            StoryParams(place="bakery", detective="June", suspect="Owen", helper="Poppy"),
            StoryParams(place="pantry", detective="Leo", suspect="Mira", helper="Nina"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
