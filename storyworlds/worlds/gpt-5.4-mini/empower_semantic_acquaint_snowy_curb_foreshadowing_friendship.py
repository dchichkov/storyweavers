#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/empower_semantic_acquaint_snowy_curb_foreshadowing_friendship.py
==================================================================================================

A small animal-story world set at a snowy curb, built from the seed words
"empower", "semantic", and "acquaint". The premise is a friendship-driven
mystery: two neighborhood animals notice odd clues in the snow, a shy one gets
encouraged, and together they solve what happened.

The story is intentionally tiny and classical: a clear beginning, a foreshadowed
mystery, a collaborative turn, and an ending image that proves the change.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "they", "object": "them", "possessive": "their"}
        return mapping[case]


@dataclass
class Character:
    id: str
    animal: str
    name: str
    timid: bool = False
    curious: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    snowy: bool = True
    curb: bool = True


@dataclass
class Clue:
    id: str
    label: str
    meaning: str
    foreshadows: str


@dataclass
class Mystery:
    id: str
    missing: str
    owner: str
    found_by: str
    reveal: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.characters: dict[str, Character] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_character(self, ch: Character) -> Character:
        self.characters[ch.id] = ch
        return ch

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.characters = copy.deepcopy(self.characters)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_footprints(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("track_visible") and not world.facts.get("track_spoken"):
        world.facts["track_spoken"] = True
        out.append("Fresh little prints curled away from the curb like a clue waiting to be read.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("friendship_shift") and not world.facts.get("friendship_spoken"):
        world.facts["friendship_spoken"] = True
        out.append("The shy friend stood a little taller after being encouraged.")
    return out


def _r_solution(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery_solved") and not world.facts.get("solution_spoken"):
        world.facts["solution_spoken"] = True
        out.append("The missing thing was found, safe and sound.")
    return out


CAUSAL_RULES = [
    Rule("footprints", "clue", _r_footprints),
    Rule("kindness", "friendship", _r_kindness),
    Rule("solution", "mystery", _r_solution),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_solution(world: World) -> dict:
    sim = world.copy()
    _inspect_clue(sim, narrate=False)
    return {"solved": sim.facts.get("mystery_solved", False), "hope": sim.facts.get("hope", 0)}


def _inspect_clue(world: World, narrate: bool = True) -> None:
    world.facts["track_visible"] = True
    propagate(world, narrate=narrate)


def _encourage(world: World, helper: Character, shy: Character) -> None:
    shy.memes["courage"] += 1
    helper.memes["care"] += 1
    world.facts["friendship_shift"] = True
    world.say(
        f"{helper.name} leaned close and said, 'You can do this. We will look together.'"
    )


def _explain_semantics(world: World, helper: Character, shy: Character, clue: Clue) -> None:
    shy.memes["understanding"] += 1
    world.say(
        f"{helper.name} said the clue was more than just a mark in the snow; it had semantic meaning, because it pointed somewhere."
    )
    world.say(
        f"That meaning helped {shy.name} acquaint {shy.pronoun('object')}self with the trail and follow it with a steady step."
    )


def _solve(world: World, mystery: Mystery) -> None:
    world.facts["mystery_solved"] = True
    world.say(
        f"At the end of the trail, they found {mystery.owner}'s {mystery.missing}, just where the snowy curb had led them."
    )
    world.say(mystery.reveal)


def tell(place: Place, clue: Clue, mystery: Mystery,
         helper_name: str = "Milo", helper_animal: str = "mouse",
         shy_name: str = "Pip", shy_animal: str = "rabbit") -> World:
    world = World()
    helper = world.add_character(Character(id=helper_name, animal=helper_animal, name=helper_name))
    shy = world.add_character(Character(id=shy_name, animal=shy_animal, name=shy_name, timid=True))
    curb = world.add_entity(Entity(id=place.id, kind="place", type="curb", label=place.label))
    clue_ent = world.add_entity(Entity(id=clue.id, kind="thing", type="clue", label=clue.label))
    world.facts.update(place=place, clue=clue, mystery=mystery, helper=helper, shy=shy, curb=curb, clue_ent=clue_ent)

    world.say(
        f"On a snowy curb beside the road, {helper.name} the {helper.animal} and {shy.name} the {shy.animal} found a tiny clue in the snow."
    )
    world.say(
        f"It was {clue.label}, and it looked small now but promising, as if it had been left there on purpose."
    )
    world.say(
        f"{helper.name} said it might be a mystery to solve, and {shy.name} nodded, though {shy.name} stayed close to the warm hedge."
    )
    world.say(
        f"Earlier, they had noticed {clue.foreshadows}; now that little sign felt important."
    )

    world.para()
    _inspect_clue(world)
    if not world.facts.get("track_spoken"):
        world.say("The snow held its breath, waiting for them to notice.")
    _encourage(world, helper, shy)
    _explain_semantics(world, helper, shy, clue)

    world.para()
    world.facts["hope"] = 1
    pred = predict_solution(world)
    if pred["solved"]:
        world.facts["hope"] += 1
    world.say(
        f"Together they followed the trail, because kindness made the shy one braver and the clue made sense once they looked closely."
    )
    _solve(world, mystery)

    world.para()
    helper.memes["joy"] += 1
    shy.memes["joy"] += 1
    world.say(
        f"After that, {shy.name} stood beside {helper.name} at the curb without hiding, and the two friends laughed into the falling snow."
    )
    world.say(
        f"The mystery was gone, but the friendship stayed, bright as the white curb and warm as a shared scarf."
    )

    world.facts["ended_together"] = True
    world.facts["place_label"] = place.label
    world.facts["predicted"] = pred
    return world


PLACES = {
    "snowy_curb": Place("snowy_curb", "the snowy curb"),
}

CLUES = {
    "ribbon": Clue("ribbon", "a blue ribbon", "something important had been carried nearby", "a blue ribbon had been tied to the fence earlier"),
    "bell": Clue("bell", "a little brass bell", "someone or something had jingled past", "a faint jingle had passed the curb before dawn"),
    "mitten": Clue("mitten", "a red mitten", "someone had lost a warm thing in the snow", "a matching mitten had been missing from a porch rail"),
}

MYSTERIES = {
    "lost_mitten": Mystery("lost_mitten", "red mitten", "Mrs. Wren", "the hedge", "Mrs. Wren smiled because the mitten could go back home and keep a wing warm.") ,
    "lost_bell": Mystery("lost_bell", "brass bell", "the sled", "the curb", "The bell rang once in the cold air, and everyone knew the little mystery was solved."),
    "lost_ribbon": Mystery("lost_ribbon", "blue ribbon", "the nest", "the fence", "The ribbon fluttered like a tiny flag, and the neighbors cheered for the clever pair."),
}

HELPER_NAMES = ["Milo", "Luna", "Toby", "Nina", "Otis", "Roo"]
SHY_NAMES = ["Pip", "Bean", "Dot", "June", "Puck", "Mira"]
ANIMALS = ["mouse", "rabbit", "fox", "squirrel", "bird", "hedgehog"]


@dataclass
class StoryParams:
    place: str
    clue: str
    mystery: str
    helper_name: str
    helper_animal: str
    shy_name: str
    shy_animal: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("snowy_curb", clue, mystery) for clue in CLUES for mystery in MYSTERIES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world set at a snowy curb with a friendship mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
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


ASP_RULES = r"""
valid(P, C, M) :- place(P), clue(C), mystery(M).
solved :- chose_clue(C), clue(C), clue_meaning(C, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_meaning", cid, c.meaning))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, mystery = rng.choice(sorted(combos))
    helper_name = rng.choice(HELPER_NAMES)
    shy_name = rng.choice([n for n in SHY_NAMES if n != helper_name])
    helper_animal = rng.choice(ANIMALS)
    shy_animal = rng.choice([a for a in ANIMALS if a != helper_animal])
    return StoryParams(place, clue, mystery, helper_name, helper_animal, shy_name, shy_animal)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue, mystery = f["clue"], f["mystery"]
    return [
        f'Write an animal story set at a snowy curb that includes the words "empower", "semantic", and "acquaint".',
        f"Tell a friendship mystery where {f['helper'].name} helps {f['shy'].name} solve a small clue about {clue.label}.",
        f"Write a gentle winter story in which a shy animal is empowered by a friend and both learn what the clue means.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    helper = f["helper"]
    shy = f["shy"]
    clue = f["clue"]
    mystery = f["mystery"]
    return [
        QAItem(
            question="Who are the main friends in the story?",
            answer=f"The main friends are {helper.name}, the {helper.animal}, and {shy.name}, the {shy.animal}. They stay together through the whole mystery and help each other feel brave.",
        ),
        QAItem(
            question="Why did the clue matter?",
            answer=f"The clue mattered because it was not just a thing in the snow; it had semantic meaning and pointed the friends toward the missing {mystery.missing}. That meaning helped them understand where to look next.",
        ),
        QAItem(
            question="How did the shy friend change?",
            answer=f"{shy.name} started out close to the hedge and a little timid, but {helper.name} encouraged {shy.name} and helped {shy.name} acquaint {shy.name.lower()}self with the trail. By the end, {shy.name} was walking beside {helper.name} without hiding.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"They followed the clue through the snow and found the missing {mystery.missing} where the trail ended. After that, the missing thing could go back home, so the little mystery was solved cleanly and kindly.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does empower mean?",
            answer="To empower someone is to help them feel stronger, braver, and ready to do something they were unsure about before.",
        ),
        QAItem(
            question="What does semantic mean?",
            answer="Semantic means about meaning. A semantic clue helps you understand what something is trying to tell you.",
        ),
        QAItem(
            question="What does acquaint mean?",
            answer="To acquaint someone with something is to help them get to know it. You can acquaint a friend with a trail, a place, or a new idea.",
        ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    for c in world.characters.values():
        meters = {k: v for k, v in c.meters.items() if v}
        memes = {k: v for k, v in c.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {c.id:12} (animal ) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("snowy_curb", "ribbon", "lost_ribbon", "Milo", "mouse", "Pip", "rabbit"),
    StoryParams("snowy_curb", "bell", "lost_bell", "Luna", "fox", "Bean", "bird"),
    StoryParams("snowy_curb", "mitten", "lost_mitten", "Toby", "squirrel", "Mira", "hedgehog"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], MYSTERIES[params.mystery], params.helper_name, params.helper_animal, params.shy_name, params.shy_animal)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, c, m in combos:
            print(f"  {p:12} {c:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
