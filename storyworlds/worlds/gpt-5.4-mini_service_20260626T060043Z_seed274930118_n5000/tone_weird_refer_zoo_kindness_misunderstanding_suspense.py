#!/usr/bin/env python3
"""
A standalone story world for a zoo whodunit with kindness, misunderstanding,
and suspense.

A small source tale behind this world:
A child visits the zoo with a bright striped snack box. A weird note on the
bench makes it seem like someone took the box. The child suspects the penguin,
then the monkey, then the zookeeper. But the real answer is gentler: a kind
keeper moved the box to feed a frightened baby animal, and the note was only
a mix-up. The child learns to ask first, not accuse first.

The world model tracks physical state with meters and social state with memes.
The story is driven by what actually happens: who is nearby, what is missing,
which clue appears, who acts kindly, and how the misunderstanding clears.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    clues: set[str] = field(default_factory=set)
    animals: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    misread_as: str
    true_move: str
    clue: str
    resolution: str
    risk_meme: str = "suspense"
    kindness_gain: str = "kindness"


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_misunderstanding(world: World) -> list[str]:
    out = []
    child = world.facts["child"]
    if child.memes.get("suspense", 0.0) < THRESHOLD:
        return out
    clue = world.facts["mystery"].clue
    sig = ("clue", clue)
    if sig not in world.fired:
        world.fired.add(sig)
        child.memes["misunderstanding"] = child.memes.get("misunderstanding", 0.0) + 1
        out.append(f"{clue.capitalize()} made the wrong answer feel close.")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    helper = world.facts["helper"]
    animal = world.facts["animal"]
    if helper.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("kindness", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.memes["safe"] = animal.memes.get("safe", 0.0) + 1
    out.append(f"{helper.pronoun('subject').capitalize()} moved gently so the small animal would not feel chased.")
    return out


def _r_resolution(world: World) -> list[str]:
    out = []
    child = world.facts["child"]
    helper = world.facts["helper"]
    if child.memes.get("misunderstanding", 0.0) < THRESHOLD:
        return out
    if helper.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("resolve", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["suspense"] = 0.0
    child.memes["kindness"] = child.memes.get("kindness", 0.0) + 1
    out.append("The strange clue finally made sense.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_misunderstanding, _r_kindness, _r_resolution):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    mystery: str
    seed: Optional[int] = None


PLACES = {
    "zoo_main": Place(
        id="zoo_main",
        label="the zoo",
        clues={"weird note", "tiny muddy print", "quiet squeak"},
        animals={"penguin", "monkey", "fox"},
    )
}

MYSTERIES = {
    "snackbox": Mystery(
        id="snackbox",
        missing="a striped snack box",
        misread_as="the monkey took it",
        true_move="the keeper moved it to the nursery",
        clue="a weird note",
        resolution="the snack box was only borrowed to feed a baby meerkat",
    ),
    "red_hat": Mystery(
        id="red_hat",
        missing="a red sun hat",
        misread_as="the penguin stole it",
        true_move="the zookeeper hung it on a gate",
        clue="a tiny muddy print",
        resolution="the hat had been set aside for the lost-and-found table",
    ),
    "blue_ball": Mystery(
        id="blue_ball",
        missing="a blue rubber ball",
        misread_as="the fox ran away with it",
        true_move="the keeper rolled it into the vet room",
        clue="a quiet squeak",
        resolution="the ball was used to calm a nervous otter",
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Tess", "Nora", "Lina"]
BOY_NAMES = ["Owen", "Finn", "Jasper", "Theo", "Milo"]
HELPER_NAMES = ["Rae", "Nico", "Maya", "Pip"]
TRAITS = ["curious", "gentle", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(PLACES["zoo_main"].id, mid) for mid in MYSTERIES]


def explain_rejection(mystery: Mystery) -> str:
    return f"(No story: this mystery has no kind explanation.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A zoo whodunit about a misunderstanding that turns into kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--parent", choices=["keeper", "zookeeper"], default="keeper")
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
    place = args.place or "zoo_main"
    mystery_id = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    helper_type = args.parent
    if place != "zoo_main":
        raise StoryError("(No story: the zoo whodunit is only set at the main zoo.)")
    return StoryParams(
        place=place,
        child_name=name,
        child_type=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        mystery=mystery_id,
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place)

    child = world.add(Entity(
        id=params.child_name, kind="character", type=params.child_type,
        traits=["little", "observer"],
        meters={"suspense": 0.0},
        memes={"suspense": 0.0, "kindness": 0.0, "misunderstanding": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name, kind="character", type=params.helper_type,
        label="the zoo keeper",
        meters={"kindness": 1.0},
        memes={"kindness": 1.0},
    ))
    animal = world.add(Entity(
        id="animal", kind="character", type="animal", label="a small animal",
        meters={"safe": 0.0},
        memes={"safe": 0.0},
    ))
    missing = world.add(Entity(
        id="missing", kind="thing", type="thing", label=mystery.missing,
        owner=child.id,
    ))

    world.facts.update(child=child, helper=helper, animal=animal, missing=missing, mystery=mystery)

    world.say(
        f"{child.id} came to the zoo with a bright face and a sharp eye for clues."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} loved the odd little tone of the place, "
        f"where every gate squeaked and every shadow seemed weird enough to refer to later."
    )
    world.say(
        f"Then {child.id} noticed that {mystery.missing} was gone."
    )
    world.say(
        f"That was the start of a hush of suspense."
    )
    world.para()

    child.memes["suspense"] += 1
    helper.memes["kindness"] += 1
    child.meters["suspense"] += 1
    propagate(world, narrate=True)

    world.say(
        f"{child.id} first thought {mystery.misread_as}."
    )
    world.say(
        f"{child.id} pointed toward the pen, but {helper.id} shook {helper.pronoun('possessive')} head and said, "
        f"'{mystery.clue} means we should look again.'"
    )
    world.para()

    world.say(
        f"At last, the clue led them to the answer: {mystery.true_move}."
    )
    world.say(
        f"It was not a mean trick at all, only a mix-up full of kindness."
    )
    world.say(
        f"{mystery.resolution.capitalize()}."
    )
    world.para()

    propagate(world, narrate=True)
    world.say(
        f"{child.id} smiled, because the zoo was still strange, but it was no longer scary."
    )
    world.say(
        f"Now {child.id} knew that asking kindly could solve a mystery better than accusing fast."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    return [
        f'Write a whodunit story for a young child set in a zoo, using the words "tone", "weird", and "refer".',
        f"Tell a suspenseful story where {child.id} thinks {mystery.missing} was taken, but the answer is a kind misunderstanding.",
        f"Write a gentle zoo mystery that ends with kindness solving the case.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What did {child.id} think had happened to {mystery.missing}?",
            answer=f"{child.id} thought {mystery.misread_as}.",
        ),
        QAItem(
            question=f"Who helped {child.id} look again instead of guessing too fast?",
            answer=f"{helper.id}, the zoo keeper, helped by pointing to {mystery.clue}.",
        ),
        QAItem(
            question="What solved the mystery in the end?",
            answer=f"The mystery was solved when everyone saw that {mystery.resolution.lower()}, so the trouble was only a misunderstanding.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a zoo?",
            answer="A zoo is a place where people can visit and look at animals that live there or are cared for there.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing gentle actions that help someone else feel safe, seen, or cared for.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something is true, but the real answer is different.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when a story has a mystery to solve.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_suspense(C) :- child(C), suspense(C).
misunderstanding(C) :- child(C), child_suspense(C), clue_seen(C).
kind_fix(H) :- helper(H), kind(H).
resolved(C) :- child(C), misunderstanding(C), kind_fix(_).
#show child_suspense/1.
#show misunderstanding/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("child", "c1"))
    lines.append(asp.fact("helper", "h1"))
    lines.append(asp.fact("suspense", "c1"))
    lines.append(asp.fact("kind", "h1"))
    lines.append(asp.fact("clue_seen", "c1"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    asp_set = set(asp.atoms(model, "resolved"))
    py_set = {("c1",)}
    if asp_set == py_set:
        print("OK: clingo gate matches Python gate.")
        return 0
    print("MISMATCH")
    print("asp:", sorted(asp_set))
    print("py:", sorted(py_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.asp:
        print("ASP mode is available for parity checks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for mid in MYSTERIES:
            params = StoryParams(
                place="zoo_main",
                child_name="Mina",
                child_type="girl",
                helper_name="Rae",
                helper_type="keeper",
                mystery=mid,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
