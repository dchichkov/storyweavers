#!/usr/bin/env python3
"""
storyworlds/worlds/automobile_beat_mystery_to_solve_bedtime_story.py
====================================================================

A small bedtime-story world about a child, a little automobile, and a quiet
mystery that gets solved before sleep.

Premise:
- A child loves a small automobile toy that can make a soft beat.
- At bedtime, the beat goes missing or sounds odd.
- The child and a helper follow clues in the room.
- They solve the mystery by finding the cause and restoring the gentle beat.

This world keeps the prose child-facing, concrete, and state-driven: the mystery
is not a frozen paragraph with swapped nouns, but a simulated problem that is
introduced, investigated, and resolved by changing world state.

Includes:
- typed entities with meters and memes
- a reasonableness gate for the mystery setup
- inline ASP twin rules for parity verification
- story, Q&A, trace, JSON, and ASP CLI modes
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
# Core world constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

ROOMS = {
    "bedroom": {
        "label": "the bedroom",
        "cozy": True,
        "affords": {"listen", "search"},
    },
    "hall": {
        "label": "the hall",
        "cozy": False,
        "affords": {"listen", "search"},
    },
    "playroom": {
        "label": "the playroom",
        "cozy": True,
        "affords": {"listen", "search", "play"},
    },
}

OBJECTS = {
    "toycar": {
        "label": "toy automobile",
        "phrase": "a little red automobile toy",
        "kind": "toy",
        "type": "automobile",
        "can_beat": True,
        "can_hide": False,
    },
    "musicbox": {
        "label": "music box",
        "phrase": "a small music box with a twinkly lid",
        "kind": "thing",
        "type": "music_box",
        "can_beat": True,
        "can_hide": False,
    },
    "pillow": {
        "label": "pillow",
        "phrase": "a soft pillow",
        "kind": "thing",
        "type": "pillow",
        "can_beat": False,
        "can_hide": True,
    },
    "blanket": {
        "label": "blanket",
        "phrase": "a blanket with stars on it",
        "kind": "thing",
        "type": "blanket",
        "can_beat": False,
        "can_hide": True,
    },
}

HELPERS = {
    "mom": {"label": "mom", "type": "mother"},
    "dad": {"label": "dad", "type": "father"},
    "grandma": {"label": "grandma", "type": "grandmother"},
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ava", "Zoe"],
    "boy": ["Leo", "Finn", "Theo", "Noah", "Eli"],
}

TRAITS = ["sleepy", "curious", "gentle", "brave", "patient"]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    room: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noise": 0.0, "search": 0.0, "comfort": 0.0, "beat": 0.0, "hidden": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "curiosity": 0.0, "relief": 0.0, "love": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Mystery:
    source: str
    clue: str
    solution: str
    solved_by: str


@dataclass
class World:
    room: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    mystery: Optional[Mystery] = None

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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.mystery = copy.deepcopy(self.mystery)
        return clone


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(room: str, object_id: str, cause: str) -> bool:
    return room in ROOMS and object_id in OBJECTS and cause in {"hidden_under", "misplaced", "stuck", "sleepy_noise"}


def explain_rejection(room: str, object_id: str, cause: str) -> str:
    return (
        f"(No story: this bedtime mystery needs a believable clue and a gentle solution. "
        f"The chosen setup '{room}/{object_id}/{cause}' does not make a child-sized mystery.)"
    )


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def _narrate_setup(world: World, child: Entity, helper: Entity, toy: Entity) -> None:
    world.say(
        f"At bedtime, {child.id} hugged {child.pronoun('possessive')} {toy.label} and listened for its soft beat."
    )
    world.say(
        f"{child.id} loved the little automobile because it sounded like a tiny heartbeat in the dark."
    )
    world.say(
        f"{child.id}'s {helper.label} tucked the blanket close and smiled at the sleepy room."
    )


def _mystery_starts(world: World, child: Entity, toy: Entity, cause: str) -> None:
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    toy.meters["beat"] = 0.0
    if cause == "hidden_under":
        toy.meters["hidden"] = 1.0
        world.say(
            f"Then the beat went missing. The little automobile was still there, but it had slipped under the pillow."
        )
    elif cause == "misplaced":
        toy.meters["hidden"] = 1.0
        world.say(
            f"Then the beat went missing. The little automobile was not on the bedside table anymore."
        )
    elif cause == "stuck":
        toy.meters["noise"] = 1.0
        world.say(
            f"Then the beat sounded stuck, like a tiny wheel was bumping on one spot again and again."
        )
    else:
        toy.meters["noise"] = 1.0
        world.say(
            f"Then the beat sounded sleepy and uneven, like the room itself was whispering instead of tapping."
        )


def _investigate(world: World, child: Entity, helper: Entity, toy: Entity, cause: str) -> None:
    child.meters["search"] += 1
    world.para()
    world.say(
        f"{child.id} whispered, 'Where did the beat go?' and {helper.id} said, 'Let's look carefully.'"
    )
    if cause in {"hidden_under", "misplaced"}:
        world.say(
            f"They checked the bed, the rug, and the shelf. At last, {child.id} found the little automobile under the pillow."
        )
    elif cause == "stuck":
        world.say(
            f"They listened closely and heard the tiny wheel tapping against a stuck blanket corner."
        )
    else:
        world.say(
            f"They listened closely and noticed the toy had been wound too tightly before bedtime."
        )


def _solve(world: World, child: Entity, helper: Entity, toy: Entity, cause: str) -> None:
    child.memes["relief"] += 1
    helper.meters["comfort"] += 1
    toy.meters["beat"] = 1.0
    toy.meters["noise"] = 0.0
    toy.meters["hidden"] = 0.0
    world.para()
    if cause == "hidden_under":
        world.say(
            f"{helper.id} lifted the pillow, and the little automobile appeared at once. The soft beat came back right away."
        )
    elif cause == "misplaced":
        world.say(
            f"{helper.id} found the little automobile on the dresser and carried it back. Its gentle beat returned in the cozy dark."
        )
    elif cause == "stuck":
        world.say(
            f"{helper.id} nudged the blanket away from the wheel, and the tiny tap-tap sounded smooth again."
        )
    else:
        world.say(
            f"{helper.id} let the toy rest for a moment, then wound it just enough. The beat became slow and kind again."
        )
    world.say(
        f"{child.id} smiled, hugged {child.pronoun('possessive')} {toy.label}, and listened until sleep felt close."
    )


# ---------------------------------------------------------------------------
# Tell / generate
# ---------------------------------------------------------------------------
def tell(room: str, child_name: str, child_type: str, helper_key: str, object_id: str, cause: str, trait: str) -> World:
    world = World(room)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    helper = world.add(Entity(id=HELPERS[helper_key]["label"], kind="character", type=HELPERS[helper_key]["type"], label=HELPERS[helper_key]["label"]))
    toy = world.add(Entity(
        id=object_id,
        kind=OBJECTS[object_id]["kind"],
        type=OBJECTS[object_id]["type"],
        label=OBJECTS[object_id]["label"],
        phrase=OBJECTS[object_id]["phrase"],
    ))
    world.facts.update(
        child=child,
        helper=helper,
        toy=toy,
        room=room,
        cause=cause,
        trait=trait,
        object_id=object_id,
    )

    _narrate_setup(world, child, helper, toy)
    _mystery_starts(world, child, toy, cause)
    _investigate(world, child, helper, toy, cause)
    _solve(world, child, helper, toy, cause)
    world.mystery = Mystery(source=object_id, clue=cause, solution="restored_beat", solved_by=helper.id)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
CAUSES = {
    "hidden_under": "hidden under the pillow",
    "misplaced": "moved to the wrong place",
    "stuck": "stuck against a blanket corner",
    "sleepy_noise": "too sleepy and uneven",
}

CURATED = [
    dict(room="bedroom", object_id="toycar", cause="hidden_under", child_name="Mia", child_type="girl", helper_key="mom", trait="curious"),
    dict(room="playroom", object_id="toycar", cause="stuck", child_name="Leo", child_type="boy", helper_key="dad", trait="gentle"),
    dict(room="bedroom", object_id="musicbox", cause="misplaced", child_name="Nora", child_type="girl", helper_key="grandma", trait="patient"),
]

# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    room: str
    object_id: str
    cause: str
    child_name: str
    child_type: str
    helper_key: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story about a child and an automobile whose soft beat leads to a mystery to solve.',
        f"Tell a gentle story where {f['child'].id} notices a problem with a {f['toy'].label} and solves it with {f['helper'].id}.",
        f'Write a calm bedtime tale in which the word "beat" matters and the little automobile is part of the mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    toy = f["toy"]
    room = f["room"]
    cause = f["cause"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"What did {child.id} love at bedtime?",
            answer=f"{child.id} loved {child.pronoun('possessive')} {toy.label}, a little automobile with a soft beat.",
        ),
        QAItem(
            question=f"Why did the story become a mystery in {ROOMS[room]['label']}?",
            answer=f"The mystery began when the beat of the {toy.label} changed because it was {CAUSES[cause]}.",
        ),
        QAItem(
            question=f"How did {trait} {child.id} solve the problem with {helper.id}?",
            answer=f"{child.id} and {helper.id} looked carefully, found the cause, and brought back the gentle beat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an automobile?",
            answer="An automobile is a vehicle with wheels that people use to travel on roads.",
        ),
        QAItem(
            question="What does beat mean in a bedtime story?",
            answer="A beat is a steady tapping rhythm, like a soft thump or tick that repeats again and again.",
        ),
        QAItem(
            question="Why is bedtime a good time for a gentle story?",
            answer="Bedtime is a quiet time, so a calm story can help a child relax and feel ready to sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid mystery needs a room, an object, and a plausible cause.
valid_story(R, O, C) :- room(R), object(O), cause(C), reasonable(R, O, C).

% A toy automobile can carry a beat if it is the right object.
has_beat(O) :- object(O), automobile(O).

% A mystery is solvable when the cause can be observed and the helper can fix it.
solvable(C) :- cause(C), observable(C), fixable(C).

reasonable(R, O, C) :- cozy_room(R), has_beat(O), solvable(C).
#show valid_story/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for r, meta in ROOMS.items():
        lines.append(asp.fact("room", r))
        if meta["cozy"]:
            lines.append(asp.fact("cozy_room", r))
    for o, meta in OBJECTS.items():
        lines.append(asp.fact("object", o))
        if meta["type"] == "automobile":
            lines.append(asp.fact("automobile", o))
        if meta["can_beat"]:
            lines.append(asp.fact("can_beat", o))
    for c in CAUSES:
        lines.append(asp.fact("cause", c))
        lines.append(asp.fact("observable", c))
        lines.append(asp.fact("fixable", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set((r, o, c) for r in ROOMS for o in OBJECTS for c in CAUSES if valid_combo(r, o, c))
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid mystery setups.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generate / trace
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(ROOMS))
    object_id = args.object_id or rng.choice(list(OBJECTS))
    cause = args.cause or rng.choice(list(CAUSES))
    if not valid_combo(room, object_id, cause):
        raise StoryError(explain_rejection(room, object_id, cause))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(NAMES[child_type])
    helper_key = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        room=room,
        object_id=object_id,
        cause=cause,
        child_name=child_name,
        child_type=child_type,
        helper_key=helper_key,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        params.room,
        params.child_name,
        params.child_type,
        params.helper_key,
        params.object_id,
        params.cause,
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
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  mystery: {world.mystery}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world about an automobile, a beat, and a mystery to solve."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--object-id", choices=OBJECTS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story setups:\n")
        for r, o, c in combos:
            print(f"  {r:9} {o:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(**cfg)) for cfg in CURATED]
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.object_id} in {p.room} ({p.cause})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
