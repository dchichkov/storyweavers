#!/usr/bin/env python3
"""
storyworlds/worlds/majority_butt_bad_ending_surprise_whodunit.py
================================================================

A standalone story world for a small whodunit domain about a clubhouse vote,
a missing button, and a surprising culprit.

The seed tale behind this world:
A tidy little clubhouse has a mystery. The town kids vote by majority on who
should guard the snack shelf, but by morning the brass button from the captain's
coat is gone. A clever child follows clues around a chair, a crumb trail, and a
scuffed floor, and the surprise ending reveals the button thief. The ending is
bad because the wrong choice leaves the room in chaos anyway.

This script models:
- a small cast of typed entities with meters and memes,
- a short detective story driven by evidence state,
- a Python reasonableness gate and an inline ASP twin,
- QA sets grounded in the generated story and general world knowledge.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = True


@dataclass
class Suspect:
    id: str
    name: str
    role: str
    clue: str
    guilty: bool = False
    motive: str = ""


@dataclass
class StoryParams:
    place: str
    detective: str
    helper: str
    suspect: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.suspects: dict[str, Suspect] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_suspect(self, sus: Suspect) -> Suspect:
        self.suspects[sus.id] = sus
        return sus

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def majority_choice(options: list[str], rng: random.Random) -> str:
    counts: dict[str, int] = {o: 0 for o in options}
    ballots = [rng.choice(options) for _ in range(5)]
    for b in ballots:
        counts[b] += 1
    best = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return best


PLACES = {
    "clubhouse": Place("the clubhouse", indoors=True),
    "library": Place("the library", indoors=True),
    "boathouse": Place("the boathouse", indoors=True),
}

DETECTIVES = [
    ("Mina", "girl"),
    ("Leo", "boy"),
    ("Nora", "girl"),
    ("Owen", "boy"),
]

HELPERS = [
    ("Pip", "boy"),
    ("June", "girl"),
    ("Tess", "girl"),
    ("Max", "boy"),
]

SUSPECTS = [
    Suspect(id="chef", name="Mrs. Wren", role="caretaker", clue="flour on apron", guilty=False, motive="wanted the button for sewing"),
    Suspect(id="runner", name="Toby", role="messenger", clue="mud on shoes", guilty=False, motive="was only bringing tea"),
    Suspect(id="cat", name="Socks", role="cat", clue="tiny tooth mark", guilty=True, motive="liked shiny things"),
    Suspect(id="judge", name="Mr. Bell", role="leader", clue="ink on fingers", guilty=False, motive="was writing the vote count"),
]

CLUES = {
    "button": "a brass button from the captain's coat",
    "crumbs": "a line of crackers crumbs",
    "chair": "a chair with a scuffed front leg",
    "thread": "a loose gold thread caught on the rug",
}


def explain_invalid(clue: str, suspect: Suspect) -> str:
    if clue == "button" and suspect.id != "cat":
        return "(No story: the brass button mystery only works when the tiny tooth mark points to the cat culprit.)"
    return "(No story: this combination does not produce a clear whodunit turn.)"


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in PLACES:
        for d, _ in DETECTIVES:
            for h, _ in HELPERS:
                for s in SUSPECTS:
                    if s.id == "cat":
                        out.append((p, d, h, s.id))
    return out


@dataclass
class Rule:
    name: str
    def apply(self, world: World) -> list[str]:
        return []


def _detective_notices(world: World) -> list[str]:
    if world.facts.get("noticed"):
        return []
    if world.facts.get("clue_seen"):
        world.facts["noticed"] = True
        return ["The detective noticed the clue."]
    return []


def _majority_vote(world: World) -> list[str]:
    if world.facts.get("voted"):
        return []
    world.facts["voted"] = True
    world.facts["majority"] = world.facts.get("majority", "")
    return ["The kids chose by majority."]


RULES = [Rule("detective_notices"), Rule("majority_vote")]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            if rule.name == "detective_notices":
                res = _detective_notices(world)
            else:
                res = _majority_vote(world)
            if res:
                changed = True


def tell(place: Place, detective: str, helper: str, suspect: Suspect, clue: str) -> World:
    world = World(place)
    det = world.add(Entity(id=detective, kind="character", type="boy" if detective in {"Leo", "Owen"} else "girl"))
    hp = world.add(Entity(id=helper, kind="character", type="boy" if helper in {"Pip", "Max"} else "girl"))
    cat = world.add(Entity(id=suspect.id, kind="character", type="cat"))
    world.add_suspect(suspect)

    world.say(f"At {place.name}, {det.id} was the one everyone called when a mystery got stuck.")
    world.say(f"{hp.id} helped {det.pronoun('object')} line up the clues, because the room was full of whispers and one very missing button.")

    world.para()
    world.say(f"That afternoon, the kids picked the guard by majority, and {det.id} won the vote.")
    world.say(f"Then somebody gasped: {clue} had vanished from the captain's coat, right where it had been shining all morning.")

    world.para()
    world.say(f"{det.id} crouched beside the chair and saw {world.facts.setdefault('clue_seen', True) or 'the clue'}.")
    world.say(f"There was a scuffed leg, a little trail of crumbs, and a tiny mark that looked like teeth.")
    world.say(f"{hp.id} pointed under the table and whispered that the clue led toward {cat.id}.")

    world.para()
    world.say(f"The surprise was that {suspect.name}, the quiet cat, had slipped away with the brass button.")
    world.say(f"{cat.id} had knocked it loose while batting at the chair leg, then carried it off like treasure.")
    world.say(f"{det.id} found the button under a cushion, but the bad ending was already waiting: the vote had gone wrong, the snack shelf was untended, and crackers were scattered everywhere.")

    world.facts.update(
        detective=det,
        helper=hp,
        suspect=cat,
        clue=clue,
        guilty=suspect.guilty,
        place=place,
        majority="guard the snack shelf",
        ending="bad",
        surprise=True,
    )
    propagate(world)
    return world


def build_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child about a majority vote, a missing button, and a surprising cat culprit.',
        f"Tell a mystery story set in {world.place.name} where {f['detective'].id} follows crumbs, a chair scuff, and a tiny tooth mark.",
        f"Write a simple surprise ending story that includes the word 'majority' and ends badly after the clue is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"].id
    helper = f["helper"].id
    culprit = f["suspect"].id
    return [
        QAItem(
            question="Who was the detective in the mystery?",
            answer=f"The detective was {det}, who watched the room, followed the clues, and tried to solve the missing button case."
        ),
        QAItem(
            question="What did the kids decide by majority?",
            answer=f"They decided by majority to let {det} guard the snack shelf."
        ),
        QAItem(
            question="What was the missing thing in the story?",
            answer=f"The missing thing was {f['clue']}, a shiny brass button from the captain's coat."
        ),
        QAItem(
            question="Who turned out to be the surprising culprit?",
            answer=f"The surprise culprit was {culprit}, the quiet cat, who had taken the button."
        ),
        QAItem(
            question="Why was the ending bad?",
            answer="The mystery was solved, but the room was still messy and the snack shelf was left in trouble, so the ending felt bad instead of tidy."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does majority mean?",
            answer="Majority means more than half. In a vote, the choice with the most votes wins."
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a piece of information that helps solve a mystery."
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader tries to figure out who did it."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


ASP_RULES = r"""
is_majority_choice(X) :- vote(X, N), N = #max { M : vote(_, M) }.
mystery(T) :- clue(T), suspect(T).
surprise_culprit(cat) :- guilty(cat).
bad_ending :- solved, messy_room.
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("vote", "guard_snack_shelf", 3),
        asp.fact("clue", "button"),
        asp.fact("suspect", "cat"),
        asp.fact("guilty", "cat"),
        asp.fact("solved"),
        asp.fact("messy_room"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit world with a majority vote and a surprise cat culprit.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective", choices=[d for d, _ in DETECTIVES])
    ap.add_argument("--helper", choices=[h for h, _ in HELPERS])
    ap.add_argument("--suspect", choices=[s.id for s in SUSPECTS])
    ap.add_argument("--clue", choices=CLUES)
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
    if args.suspect and args.suspect != "cat":
        raise StoryError(explain_invalid(args.clue or "button", next(s for s in SUSPECTS if s.id == args.suspect)))
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.detective:
        combos = [c for c in combos if c[1] == args.detective]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if args.suspect:
        combos = [c for c in combos if c[3] == args.suspect]
    if not combos:
        raise StoryError("(No valid mystery combination matches those options.)")
    place, detective, helper, suspect = rng.choice(sorted(combos))
    clue = args.clue or "button"
    return StoryParams(place=place, detective=detective, helper=helper, suspect=suspect, clue=clue)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    suspect = next(s for s in SUSPECTS if s.id == params.suspect)
    world = tell(place, params.detective, params.helper, suspect, CLUES[params.clue])
    return StorySample(
        params=params,
        story=build_story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}")
    for k, v in world.facts.items():
        if k in {"detective", "helper", "suspect"}:
            continue
        lines.append(f"{k}: {v}")
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
    StoryParams(place="clubhouse", detective="Mina", helper="Pip", suspect="cat", clue="button"),
    StoryParams(place="library", detective="Leo", helper="June", suspect="cat", clue="button"),
    StoryParams(place="boathouse", detective="Nora", helper="Max", suspect="cat", clue="button"),
]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0. #show surprise_culprit/1."))
    atoms = set((sym.name, tuple(arg.name if arg.type != 2 else arg.string for arg in sym.arguments)) for sym in model)
    expected = {("surprise_culprit", ("cat",))}
    if atoms and expected.issubset(atoms):
        print("OK: ASP twin is wired.")
        return 0
    print("MISMATCH: ASP twin did not produce expected atoms.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bad_ending/0. #show surprise_culprit/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible mystery: majority vote, missing button, surprise cat culprit.")
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
