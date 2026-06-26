#!/usr/bin/env python3
"""
A standalone storyworld for a tiny detective-story domain with flashback and
mystery-solving beats.

This world builds a small simulated case:
- someone finds a strange clue involving miso
- a "goner" object or lead seems lost for good
- a dinosaur toy or statue becomes relevant
- a flashback reveals a past event that changes the investigation
- the detective solves the mystery through a causal turn, not by swapping nouns

The story stays classical and self-contained: setup, clue, flashback, reveal,
and resolution.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    clue_spots: set[str] = field(default_factory=set)
    supports_flashback: bool = True


@dataclass
class Case:
    mystery: str
    clue: str
    reveal: str
    solved_by: str
    flashback_scene: str
    flashback_truth: str
    suspect: str
    innocent: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "school_hall": Setting(place="the school hall", clue_spots={"locker", "bench", "poster"}),
    "museum_room": Setting(place="the museum room", clue_spots={"display case", "stool", "map"}),
    "backyard": Setting(place="the backyard", clue_spots={"sandbox", "shed", "flower pot"}),
    "kitchen": Setting(place="the kitchen", clue_spots={"table", "sink", "cupboard"}),
}

# A small mystery case built around the seed words.
CASES = {
    "miso": Case(
        mystery="the missing miso jar",
        clue="a tiny brown smear on the table",
        reveal="the jar had tipped into a lunch bag",
        solved_by="checking the lunch bag",
        flashback_scene="the morning snack spill",
        flashback_truth="the sidekick had borrowed the jar for pretend soup and forgotten to put it back",
        suspect="the hungry cat",
        innocent="the cat",
    ),
    "goner": Case(
        mystery="the goner note",
        clue="a torn scrap with one wet corner",
        reveal="the note was stuck under the bench all along",
        solved_by="lifting the bench cushion",
        flashback_scene="the windy walk home",
        flashback_truth="the note blew off the detective's pocket and landed near the bench",
        suspect="the janitor",
        innocent="the janitor",
    ),
    "dinosaur": Case(
        mystery="the missing dinosaur toy",
        clue="green dust on the shelf",
        reveal="the toy was inside a costume box",
        solved_by="opening the costume box",
        flashback_scene="the dress-up parade",
        flashback_truth="the sidekick hid the dinosaur toy as a prize and then forgot the hiding spot",
        suspect="the museum guard",
        innocent="the guard",
    ),
}

HERO_NAMES = ["Mina", "Nia", "Toby", "Leo", "Ada", "Milo", "June", "Pia"]
SIDEKICK_NAMES = ["Ben", "Sage", "Ivy", "Noah", "Ruby", "Eli", "Maya", "Owen"]
TRAITS = ["careful", "curious", "patient", "sharp", "brave"]

ASP_RULES = r"""
% A mystery is solvable when the setting has a clue spot and the case clue can be found there.
has_clue_spot(P) :- place(P), clue_spot(P, _).

solvable(C, P) :- case(C), place(P), has_clue_spot(P), clue_for(C, _).

% Flashback is allowed only when the case supports it.
can_flashback(C) :- case(C), flashback(C, _).
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def case_for(mystery: str) -> Case:
    if mystery not in CASES:
        raise StoryError(f"Unknown mystery '{mystery}'.")
    return CASES[mystery]


def place_for(name: str) -> Setting:
    if name not in SETTINGS:
        raise StoryError(f"Unknown place '{name}'.")
    return SETTINGS[name]


def build_case_text(case: Case, hero: Entity, sidekick: Entity, setting: Setting) -> list[str]:
    return [
        f"{hero.noun().capitalize()} was a small detective at {setting.place}.",
        f"{hero.pronoun('subject').capitalize()} and {sidekick.noun()} were working on {case.mystery}.",
        f"The first clue was {case.clue}, and it made the whole room feel like a puzzle.",
    ]


def narrate_flashback(world: World, case: Case, hero: Entity, sidekick: Entity) -> None:
    world.para()
    world.say(
        f"Then {hero.pronoun('subject').capitalize()} remembered a flashback: "
        f"{case.flashback_scene}."
    )
    world.say(
        f"In that memory, {case.flashback_truth}. "
        f"That was the piece that had gone missing from the story."
    )


def solve_mystery(world: World, case: Case, hero: Entity, sidekick: Entity) -> None:
    world.para()
    world.say(
        f"{hero.pronoun('subject').capitalize()} stopped staring at the clue and looked where it could hide."
    )
    world.say(
        f"So {hero.pronoun('subject')} tried {case.solved_by}, and the answer popped into place."
    )
    world.say(
        f"The mystery was solved: {case.reveal}."
    )
    world.say(
        f"{hero.noun().capitalize()} smiled, and {sidekick.noun()} laughed because the case was no longer a goner."
    )


def make_story(world: World, params: StoryParams) -> World:
    case = case_for(params.mystery)
    setting = place_for(params.place)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=params.sidekick_type, label=params.sidekick_name))
    clue = world.add(Entity(id="clue", type="thing", label=case.clue, phrase=case.clue))
    case_obj = world.add(Entity(id="case", type="thing", label=case.mystery, phrase=case.mystery))
    dinosaur = world.add(Entity(id="dinosaur", type="thing", label="dinosaur toy", phrase="a little dinosaur toy"))

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        clue=clue,
        case=case_obj,
        dinosaur=dinosaur,
        case_data=case,
        setting=setting,
    )

    # Act 1
    for line in build_case_text(case, hero, sidekick, setting):
        world.say(line)
    world.say(
        f"{hero.noun().capitalize()} noticed something odd: the clue did not match the obvious suspect."
    )

    # Act 2
    narrate_flashback(world, case, hero, sidekick)
    world.say(
        f"Now the miso stain, the goner note, and the dinosaur toy all seemed to point in different directions."
    )
    world.say(
        f"But {hero.pronoun('subject')} knew detectives should not trust the first guess."
    )

    # Act 3
    solve_mystery(world, case, hero, sidekick)
    world.say(
        f"At the end, {hero.noun()} put the clue back in the open and the room felt calm again."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(sample: StorySample) -> list[str]:
    p = sample.params
    case = CASES[p.mystery]
    return [
        f"Write a short detective story for a young child about {p.hero_name} solving {case.mystery} at {SETTINGS[p.place].place}, with a flashback and a clear ending.",
        f"Tell a gentle mystery story that uses the words miso, goner, and dinosaur, and ends with the case solved.",
        f"Write a simple detective tale where a clue leads to a flashback and then to the solution.",
    ]


def story_questions(sample: StorySample) -> list[QAItem]:
    p = sample.params
    case = CASES[p.mystery]
    hero = sample.world.facts["hero"]
    sidekick = sample.world.facts["sidekick"]
    setting = sample.world.facts["setting"]

    return [
        QAItem(
            question=f"Where did {p.hero_name} work on the mystery?",
            answer=f"{p.hero_name} worked on the mystery at {setting.place}.",
        ),
        QAItem(
            question=f"What clue started the case?",
            answer=f"The case started with {case.clue}.",
        ),
        QAItem(
            question=f"What did the flashback reveal?",
            answer=f"The flashback showed that {case.flashback_truth}.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"It was solved by {case.solved_by}.",
        ),
        QAItem(
            question=f"Why was the case no longer a goner at the end?",
            answer=f"Because {p.hero_name} found the hidden answer and solved {case.mystery}.",
        ),
        QAItem(
            question=f"Who helped {p.hero_name} in the story?",
            answer=f"{sidekick.label} helped by staying with {p.hero_name} during the investigation.",
        ),
    ]


def world_questions(sample: StorySample) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that shows something from before the current moment.",
        ),
        QAItem(
            question="Why do clues matter?",
            answer="Clues matter because they can help someone figure out what really happened.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question that does not have an answer yet, so someone has to investigate.",
        ),
        QAItem(
            question="What is miso?",
            answer="Miso is a savory food paste or soup base made from fermented soybeans.",
        ),
        QAItem(
            question="What is a dinosaur?",
            answer="A dinosaur was a huge animal that lived long ago.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for spot in sorted(setting.clue_spots):
            lines.append(asp.fact("clue_spot", pid, spot))
        if setting.supports_flashback:
            lines.append(asp.fact("flashback_place", pid))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("clue_for", cid, case.clue))
        lines.append(asp.fact("flashback", cid, case.flashback_scene))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # Very small parity check: every case/place should be solvable in places with clue spots.
    model = asp.one_model(asp_program("#show solvable/2."))
    asp_pairs = set(asp.atoms(model, "solvable"))
    py_pairs = {(cid, pid) for cid in CASES for pid, s in SETTINGS.items() if s.clue_spots}
    if asp_pairs == py_pairs:
        print(f"OK: ASP parity matches ({len(asp_pairs)} solvable pairs).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP only:", sorted(asp_pairs - py_pairs))
    print("Python only:", sorted(py_pairs - asp_pairs))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(CASES))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place '{place}'.")
    if mystery not in CASES:
        raise StoryError(f"Unknown mystery '{mystery}'.")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type or ("boy" if hero_type == "girl" else "girl")
    return StoryParams(
        place=place,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(place_for(params.place))
    world = make_story(world, params)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(StorySample(params=params, story="", world=world)),
        story_qa=story_questions(StorySample(params=params, story="", world=world)),
        world_qa=world_questions(StorySample(params=params, story="", world=world)),
        world=world,
    )
    return sample


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for line in world.trace:
        lines.append(line)
    lines.append("--- entities ---")
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.kind}/{e.type} {e.label!r}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-story world with flashback and mystery solving.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(CASES))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-type", choices=["girl", "boy"])
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
        print(asp_program("#show solvable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solvable/2."))
        pairs = sorted(set(asp.atoms(model, "solvable")))
        print(f"{len(pairs)} solvable pairs")
        for cid, pid in pairs:
            print(f"{cid} @ {pid}")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for mystery in CASES:
                params = StoryParams(
                    place=place,
                    mystery=mystery,
                    hero_name=rng.choice(HERO_NAMES),
                    hero_type=rng.choice(["girl", "boy"]),
                    sidekick_name=rng.choice(SIDEKICK_NAMES),
                    sidekick_type=rng.choice(["girl", "boy"]),
                    seed=args.seed,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 20, 20):
            attempts += 1
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = args.seed
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
