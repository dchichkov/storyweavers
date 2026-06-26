#!/usr/bin/env python3
"""
A standalone story world for a tiny detective-style veterinary mystery.

Premise:
- A veterinarian meets a character and must identify a mystery.
- Clues are physical objects, sounds, and traces.
- The story turns on a twist: the first suspicion is wrong, and the real answer
  comes from a small, grounded observation.
- The ending proves the mystery was solved.

This file follows the storyworld contract: it models world state with meters and
memes, exposes a Python reasonableness gate, and includes an inline ASP twin.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "doctor"}
        male = {"man", "boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool
    sounds: list[str] = field(default_factory=list)
    clues: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    id: str
    title: str
    clue: str
    wrong_guess: str
    real_answer: str
    twist: str
    solve_method: str
    solved_image: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _narrate_observation(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("noticed", 0) >= THRESHOLD and ("seen", ent.id) not in world.fired:
            world.fired.add(("seen", ent.id))
            out.append(f"{ent.label.capitalize()} looked important to the case.")
    return out


def _narrate_solved(world: World) -> list[str]:
    if world.facts.get("solved") and ("solved",) not in world.fired:
        world.fired.add(("solved",))
        return [world.facts["mystery"].solved_image]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for rule in (_narrate_observation, _narrate_solved):
        produced.extend(rule(world))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_identify(world: World, vet: Entity, target: Entity, mystery: Mystery, narrate: bool = True) -> None:
    target.meters["noticed"] = target.meters.get("noticed", 0) + 1
    vet.memes["curiosity"] = vet.memes.get("curiosity", 0) + 1
    if target.type == mystery.real_answer:
        world.facts["solved"] = True
        world.facts["answer_entity"] = target.id
    propagate(world, narrate=narrate)


def predict_solution(world: World, target: Entity, mystery: Mystery) -> bool:
    sim = world.copy()
    _do_identify(sim, sim.get("Vet"), sim.get(target.id), mystery, narrate=False)
    return bool(sim.facts.get("solved"))


def intro(world: World, vet: Entity, char: Entity, mystery: Mystery) -> None:
    world.say(
        f"{vet.label.capitalize()} was a veterinarian who liked cases that began with a strange clue."
    )
    world.say(
        f"One morning, {char.label} came in with a mystery to solve: {mystery.title}."
    )


def setting_line(world: World) -> None:
    if world.place.indoor:
        world.say(f"The clinic was quiet, with clean floors and soft lamp light.")
    else:
        world.say(f"Outside, the street by the clinic held a little trail of clues.")


def clues_line(world: World, mystery: Mystery) -> None:
    world.say(
        f"The first clue was {mystery.clue}, and that made the case feel bigger than it looked."
    )


def wrong_guess(world: World, vet: Entity, mystery: Mystery) -> None:
    vet.memes["doubt"] = vet.memes.get("doubt", 0) + 1
    world.say(
        f"At first, {vet.label} guessed {mystery.wrong_guess}, but the clue did not fit."
    )
    world.say(
        f"{vet.label} frowned, because a good detective story needs the answer to match the evidence."
    )


def twist_line(world: World, mystery: Mystery) -> None:
    world.say(mystery.twist)


def identify_line(world: World, vet: Entity, target: Entity, mystery: Mystery) -> None:
    _do_identify(world, vet, target, mystery, narrate=False)
    world.say(
        f"{vet.label} bent down, identified the real answer, and said, "
        f"\"{mystery.real_answer.capitalize()}!\""
    )
    world.say(
        f"The trick was {mystery.solve_method}, not the first guess."
    )


def ending_line(world: World, vet: Entity, char: Entity, mystery: Mystery) -> None:
    world.facts["solved"] = True
    propagate(world, narrate=False)
    world.say(
        f"In the end, the mystery was solved, and the final picture was {mystery.solved_image}."
    )


def tell(place: Place, mystery: Mystery, target_kind: str, vet_name: str, char_name: str) -> World:
    world = World(place)
    vet = world.add(Entity(id="Vet", kind="character", type="woman", label=vet_name))
    char = world.add(Entity(id="Char", kind="character", type="boy", label=char_name))
    target = world.add(Entity(
        id="Clue",
        kind="thing",
        type=target_kind,
        label=mystery.clue,
        phrase=mystery.clue,
    ))
    world.facts["mystery"] = mystery
    world.facts["vet"] = vet
    world.facts["char"] = char
    world.facts["target"] = target
    world.facts["place"] = place

    intro(world, vet, char, mystery)
    world.para()
    setting_line(world)
    clues_line(world, mystery)
    wrong_guess(world, vet, mystery)
    world.para()
    twist_line(world, mystery)
    identify_line(world, vet, target, mystery)
    ending_line(world, vet, char, mystery)
    return world


PLACES = {
    "clinic": Place(name="the clinic", indoor=True, sounds=["soft steps", "paper rustle"], clues=["a paw print", "a tiny mark"]),
    "alley": Place(name="the alley by the clinic", indoor=False, sounds=["breezy rustle", "distant bark"], clues=["a muddy track", "a shiny scrap"]),
    "yard": Place(name="the back yard", indoor=False, sounds=["leaves tapping", "a gate creak"], clues=["a bent bowl", "a snapped string"]),
}

MYSTERIES = {
    "missing_toy": Mystery(
        id="missing_toy",
        title="a missing toy",
        clue="a squeaky red toy under the bench",
        wrong_guess="a stray dog took it",
        real_answer="it was hidden by the cat",
        twist="But then the veterinarian noticed a tiny whisker on the bench leg.",
        solve_method="following the whisker and the paw prints",
        solved_image="The cat was found curled beside the bench, and the red toy sat right where it had been hidden.",
    ),
    "strange_cough": Mystery(
        id="strange_cough",
        title="a strange cough",
        clue="a dusty collar on the chair",
        wrong_guess="a sick bird outside the window",
        real_answer="the collar had fine chalk dust on it",
        twist="The twist was that the sound did not come from a bird at all; it came from a dusty rope toy being shaken nearby.",
        solve_method="checking the collar, then the rope toy, and noticing the chalk dust",
        solved_image="The room made sense at last: the chalk dust was the real clue, and the coughing sound stopped when the toy was put away.",
    ),
    "lost_tags": Mystery(
        id="lost_tags",
        title="lost name tags",
        clue="a ribbon tied around a kennel latch",
        wrong_guess="someone borrowed the tags and forgot them",
        real_answer="the tags were stuck inside the ribbon knot",
        twist="The twist was that the ribbon was not decoration; it was hiding the missing tags.",
        solve_method="carefully undoing the knot and looking inside",
        solved_image="The name tags dropped into the vet's hand, and the ribbon lay open like a solved riddle.",
    ),
}

TARGET_KIND_BY_MYSTERY = {
    "missing_toy": "cat",
    "strange_cough": "toy",
    "lost_tags": "tags",
}


@dataclass
class StoryParams:
    place: str
    mystery: str
    vet_name: str
    char_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style veterinary mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--vet-name")
    ap.add_argument("--char-name")
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


VET_NAMES = ["Mina", "Sara", "Ivy", "Nora"]
CHAR_NAMES = ["Ben", "Leo", "Tom", "Max"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    vet_name = args.vet_name or rng.choice(VET_NAMES)
    char_name = args.char_name or rng.choice(CHAR_NAMES)
    return StoryParams(place=place, mystery=mystery, vet_name=vet_name, char_name=char_name)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    target_kind = TARGET_KIND_BY_MYSTERY[mystery.id]
    world = tell(place, mystery, target_kind, params.vet_name, params.char_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    return [
        f"Write a short detective story where a veterinarian helps a child solve {m.title}.",
        f"Tell a mystery story with a twist that begins with the clue {m.clue}.",
        f"Write a child-friendly story where the veterinarian must identify the real answer, not the first guess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m = world.facts["mystery"]
    vet = world.facts["vet"]
    char = world.facts["char"]
    return [
        QAItem(
            question=f"Who tried to solve the mystery with {char.label}?",
            answer=f"The veterinarian {vet.label} tried to solve it with {char.label}.",
        ),
        QAItem(
            question="What was the first wrong guess?",
            answer=f"The first guess was that {m.wrong_guess}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=m.twist,
        ),
        QAItem(
            question="How was the mystery finally identified?",
            answer=f"It was identified by {m.solve_method}.",
        ),
        QAItem(
            question="What did the ending prove?",
            answer=f"The ending proved that {m.real_answer} and the case was solved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a veterinarian do?",
            answer="A veterinarian is a doctor who helps animals stay healthy and treats them when they are sick or hurt.",
        ),
        QAItem(
            question="What does it mean to identify something?",
            answer="To identify something means to figure out what it is by looking at clues.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or problem with an answer that is not known right away.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes the story turn in a new direction.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in PLACES for m in MYSTERIES]


ASP_RULES = r"""
place(P) :- place_fact(P).
mystery(M) :- mystery_fact(M).
valid(P,M) :- place(P), mystery(M).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_fact", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def resolve_for_story(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
    StoryParams(place="clinic", mystery="missing_toy", vet_name="Mina", char_name="Ben"),
    StoryParams(place="alley", mystery="strange_cough", vet_name="Ivy", char_name="Leo"),
    StoryParams(place="yard", mystery="lost_tags", vet_name="Nora", char_name="Max"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/mystery combos:\n")
        for p, m in combos:
            print(f"  {p:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_for_story(args, random.Random(seed))
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
            header = f"### {p.vet_name} / {p.char_name} / {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
