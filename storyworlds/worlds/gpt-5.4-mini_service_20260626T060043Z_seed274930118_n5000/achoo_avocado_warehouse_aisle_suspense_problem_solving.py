#!/usr/bin/env python3
"""
A small detective-style storyworld set in a warehouse aisle.

Premise:
A careful detective is helping in a warehouse aisle when a strange sneeze
("achoo") and a dropped avocado create a puzzling mess. The detective must
notice clues, solve the problem, and end with a surprising reveal that
changes what everyone understands about the aisle.

The world is intentionally compact:
- physical state: dust, dropped items, blocked path, cleaned aisle
- emotional state: worry, suspicion, relief, surprise
- story arc: setup -> suspense -> problem solving -> surprise resolution
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

# -----------------------------------------------------------------------------
# Core world model
# -----------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the warehouse aisle"
    affords: set[str] = field(default_factory=lambda: {"search", "inspect", "carry", "clean"})


@dataclass
class Suspect:
    id: str
    label: str
    clue_word: str
    suspicious: bool = False


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    risk: str
    location: str
    carried: bool = False


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    suspects: dict[str, Suspect] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_object(self, o: ObjectThing) -> ObjectThing:
        self.objects[o.id] = o
        return o

    def add_suspect(self, s: Suspect) -> Suspect:
        self.suspects[s.id] = s
        return s

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "StoryState":
        import copy
        clone = StoryState(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.objects = copy.deepcopy(self.objects)
        clone.suspects = copy.deepcopy(self.suspects)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _m(entity: Entity, key: str, delta: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + delta


def _e(entity: Entity, key: str, delta: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + delta


# -----------------------------------------------------------------------------
# Reasoning and causal rules
# -----------------------------------------------------------------------------

def clue_present(state: StoryState) -> bool:
    return "avocado" in state.objects and "achoo" in state.facts


def blocked_aisle(state: StoryState) -> bool:
    return state.objects["avocado"].location == state.setting.place and state.objects["avocado"].risk == "slip"


def solve_problem(state: StoryState, detective: Entity, helper: Entity) -> bool:
    if state.facts.get("solved"):
        return True
    avocado = state.objects["avocado"]
    if avocado.location != state.setting.place:
        return False

    # Detective notices dust + sneeze + avocado -> follows the clues.
    _e(detective, "focus", 1)
    _e(detective, "suspicion", 1)
    state.say(
        f"{detective.id} narrowed {detective.pronoun('possessive')} eyes. "
        f"The sneeze, the green spot, and the shiny pit looked connected."
    )

    # Helper reveals the missing piece.
    if state.suspects["worker"].suspicious:
        _e(helper, "nervous", 1)

    state.say(
        f"Then {helper.id} pointed to the top shelf and said, "
        f"\"The avocado was in a crate, but the box tipped when I sneezed: achoo!\""
    )
    state.facts["cause"] = "crate tipped after sneeze"
    state.facts["solved"] = True
    return True


# -----------------------------------------------------------------------------
# Story beat functions
# -----------------------------------------------------------------------------

def introduce(state: StoryState, detective: Entity, helper: Entity) -> None:
    state.say(
        f"{detective.id} was a careful detective in {state.setting.place}, "
        f"where every crumb could be a clue."
    )
    state.say(
        f"{helper.id} worked beside {detective.pronoun('object')} and kept the aisle neat."
    )


def setup_mystery(state: StoryState, detective: Entity) -> None:
    avocado = state.objects["avocado"]
    _e(detective, "curiosity", 1)
    _e(detective, "worry", 1)
    state.say(
        f"Near a stack of boxes, {detective.id} spotted a green avocado on the floor."
    )
    state.say(
        f"The fruit had rolled into the aisle, and a faint dusty puff hung in the air."
    )
    state.say(
        f'"Achoo!" came from somewhere behind the shelves, and that made the whole place feel secret.'
    )
    state.facts["achoo"] = True
    avocado.location = state.setting.place


def build_suspense(state: StoryState, detective: Entity, helper: Entity) -> None:
    _e(detective, "suspense", 1)
    helper.meters["blocked_path"] = 1
    state.say(
        f"{detective.id} crouched by the crate. A torn label, a green smear, and one missing cart wheel "
        f"sat like clues in a puzzle book."
    )
    state.say(
        f"No one wanted to step on the avocado and make the aisle slippery."
    )
    state.say(
        f"{helper.id} whispered that a delivery would arrive soon, so the problem had to be solved fast."
    )


def reveal_surprise(state: StoryState, detective: Entity, helper: Entity) -> None:
    state.say(
        f"At last, {detective.id} pulled the loose label free and matched it to the crate on the top shelf."
    )
    state.say(
        f"The surprise was simple: the avocado was not lost at all. It belonged in a sample box for the morning display."
    )
    state.say(
        f"The sneeze had startled the stack, and the box had tipped just enough to drop the fruit into the aisle."
    )
    state.facts["surprise"] = "avocado belonged to display box"


def clean_up(state: StoryState, detective: Entity, helper: Entity) -> None:
    avocado = state.objects["avocado"]
    state.say(
        f"{detective.id} and {helper.id} picked up the avocado, wiped the floor, and set the crate back straight."
    )
    avocado.location = "display shelf"
    avocado.risk = "safe"
    helper.meters["blocked_path"] = 0
    _e(detective, "relief", 1)
    _e(helper, "relief", 1)
    state.say(
        f"By the end, the aisle shone again, and the mystery had turned into a tidy laugh."
    )


def tell_story(state: StoryState, detective: Entity, helper: Entity) -> StoryState:
    introduce(state, detective, helper)
    state.para()
    setup_mystery(state, detective)
    build_suspense(state, detective, helper)
    state.para()
    solve_problem(state, detective, helper)
    reveal_surprise(state, detective, helper)
    clean_up(state, detective, helper)
    state.facts.update(
        detective=detective,
        helper=helper,
        setting=state.setting,
        avocado=state.objects["avocado"],
    )
    return state


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------

SETTING = Setting()

DETECTIVE_TYPES = ["girl", "boy"]
DETECTIVE_NAMES = ["Mina", "Leo", "Nia", "Owen", "Iris", "Theo"]
HELPER_NAMES = ["Rae", "Bo", "June", "Milo", "Tess", "Sam"]

AVOCADO_CASES = {
    "crate": ObjectThing(
        id="avocado",
        label="avocado",
        phrase="a ripe avocado",
        risk="slip",
        location="top shelf",
    ),
}

SUSPECT_CASES = {
    "worker": Suspect(id="worker", label="warehouse worker", clue_word="crate", suspicious=True),
}

TRAITS = ["careful", "curious", "brave", "patient", "sharp-eyed"]


# -----------------------------------------------------------------------------
# Params
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str
    name2: str
    detective_type: str
    trait: str
    seed: Optional[int] = None


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------

def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    detective: Entity = f["detective"]
    return [
        'Write a short detective story in a warehouse aisle that includes the word "achoo" and an avocado.',
        f"Tell a suspenseful, child-friendly mystery where {detective.id} solves the avocado problem in {world.setting.place}.",
        "Write a story with a clue, a careful solution, and a surprising reveal near a warehouse shelf.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    d: Entity = world.facts["detective"]
    h: Entity = world.facts["helper"]
    avocado: ObjectThing = world.facts["avocado"]
    cause = world.facts.get("cause", "something tipped the crate")
    return [
        QAItem(
            question="Where does the story happen?",
            answer="It happens in a warehouse aisle, where boxes, shelves, and carts can hide clues.",
        ),
        QAItem(
            question=f"What was the clue that worried {d.id}?",
            answer=f"{d.id} noticed an avocado on the floor, a dusty puff in the air, and the sneeze, \"achoo,\" that hinted something had tipped over.",
        ),
        QAItem(
            question=f"How did {d.id} solve the problem?",
            answer=f"{d.id} followed the clues, listened to {h.id}, and learned that {cause}. Then they cleaned the aisle and put the avocado back where it belonged.",
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer="The avocado was not lost at all. It belonged in a display box, so the mystery was really a small accident, not a big theft.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues, asks questions, and tries to figure out what happened.",
        ),
        QAItem(
            question="Why can an avocado be slippery?",
            answer="An avocado can be slippery because its skin is smooth and the fruit can roll easily on the floor.",
        ),
        QAItem(
            question="What does 'achoo' mean?",
            answer="Achoo is the sound people make when they sneeze.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
% A small declarative twin of the Python reasonableness gate.
% There is a mystery if an avocado is on the aisle floor and a sneeze happened.
mystery(aisle, avocado) :- in_place(avocado, aisle), sneeze(achoo).

% The detective can solve it if there is a helper and a crate clue.
solvable(aisle, avocado) :- mystery(aisle, avocado), has_helper, crate_clue.

% The surprise is that the avocado belonged to a display box.
surprise(aisle, avocado) :- solvable(aisle, avocado), display_box.
#show mystery/2.
#show solvable/2.
#show surprise/2.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("in_place", "avocado", "aisle"),
        asp.fact("sneeze", "achoo"),
        asp.fact("has_helper"),
        asp.fact("crate_clue"),
        asp.fact("display_box"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery/2. #show solvable/2. #show surprise/2."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number and a.type != a.type.String else (a.number if a.type == a.type.Number else a.string) for a in sym.arguments)) for sym in model)
    expected = {("mystery", ("aisle", "avocado")), ("solvable", ("aisle", "avocado")), ("surprise", ("aisle", "avocado"))}
    if atoms == expected:
        print("OK: ASP twin matches the Python mystery structure.")
        return 0
    print("MISMATCH:", sorted(atoms))
    return 1


# -----------------------------------------------------------------------------
# CLI, resolve, generate, emit
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld in a warehouse aisle with a sneeze and an avocado.")
    ap.add_argument("--name")
    ap.add_argument("--name2")
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
    return StoryParams(
        name=args.name or rng.choice(DETECTIVE_NAMES),
        name2=args.name2 or rng.choice([n for n in HELPER_NAMES if n != args.name]),
        detective_type=rng.choice(DETECTIVE_TYPES),
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    state = StoryState(SETTING)
    detective = state.add_entity(Entity(id=params.name, kind="character", type=params.detective_type))
    helper = state.add_entity(Entity(id=params.name2, kind="character", type="worker"))
    state.add_object(AVOCADO_CASES["crate"])
    state.add_suspect(SUSPECT_CASES["worker"])

    state = tell_story(state, detective, helper)
    story = state.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(state),
        story_qa=story_qa(state),
        world_qa=world_knowledge_qa(state),
        world=state,
    )


def dump_trace(world: StoryState) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits) if bits else 'empty'}")
    for o in world.objects.values():
        lines.append(f"{o.id}: location={o.location} risk={o.risk}")
    lines.append(f"facts={world.facts}")
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
    StoryParams(name="Mina", name2="Rae", detective_type="girl", trait="careful"),
    StoryParams(name="Leo", name2="Bo", detective_type="boy", trait="curious"),
    StoryParams(name="Iris", name2="Tess", detective_type="girl", trait="sharp-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery/2. #show solvable/2. #show surprise/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery/2. #show solvable/2. #show surprise/2."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
