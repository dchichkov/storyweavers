#!/usr/bin/env python3
"""
Standalone storyworld: Essential Mystery to Solve Quest Detective Story.

A small detective-style world where a child detective follows an essential clue,
asks questions, gathers a few facts, and solves a gentle mystery by completing a
quest. The simulated state drives the prose: clues, suspicion, location, and the
final reveal all change the story.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    places: list[str]
    weather: str = ""


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    essential: bool = False
    leads_to: str = ""


@dataclass
class Quest:
    id: str
    goal: str
    action: str
    end_image: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.trace)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SETTINGS = {
    "library": Setting(place="the old library", places=["front desk", "reading nook", "back room"]),
    "garden": Setting(place="the quiet garden", places=["gate", "path", "shed"]),
    "station": Setting(place="the little station", places=["platform", "ticket window", "bench"]),
    "museum": Setting(place="the small museum", places=["hall", "desk", "storage room"]),
}

CLUES = {
    "receipt": Clue(
        id="receipt",
        label="receipt",
        phrase="a small paper receipt with a smudge of blue ink",
        location="desk",
        essential=True,
        leads_to="key",
    ),
    "key": Clue(
        id="key",
        label="key",
        phrase="a brass key tied with red string",
        location="reading nook",
        essential=True,
        leads_to="box",
    ),
    "box": Clue(
        id="box",
        label="box",
        phrase="a little locked box tucked behind books",
        location="back room",
        essential=True,
        leads_to="missing_note",
    ),
    "note": Clue(
        id="note",
        label="note",
        phrase="a folded note with one missing corner",
        location="path",
        essential=False,
        leads_to="answer",
    ),
}

QUESTS = {
    "find_owner": Quest(
        id="find_owner",
        goal="find the owner of the missing item",
        action="follow the clues",
        end_image="the missing item back in the right hands",
    ),
    "find_map": Quest(
        id="find_map",
        goal="find the hidden map",
        action="search the clues",
        end_image="the map opened flat on the table",
    ),
    "find_toy": Quest(
        id="find_toy",
        goal="find the lost toy",
        action="trace the trail",
        end_image="the toy sitting safely on its shelf",
    ),
}

HERO_NAMES = ["Mina", "Ellis", "June", "Rory", "Tess", "Noah", "Ivy", "Milo"]
SIDEKICK_NAMES = ["Pip", "Lena", "Ollie", "Sage", "Perry", "Nia"]
TRAITS = ["careful", "curious", "brave", "patient", "bright", "sharp"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    clue: str
    quest: str
    name: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story world helpers
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting=setting)

    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="child", label=params.sidekick))
    clue = CLUES[params.clue]
    quest = QUESTS[params.quest]

    world.facts.update(hero=hero, sidekick=sidekick, clue=clue, quest=quest)

    hero.memes["curiosity"] = 1.0
    hero.memes["determination"] = 1.0
    sidekick.memes["helpful"] = 1.0

    world.say(f"{hero.id} was a {params.trait} little detective who loved solving mysteries.")
    world.say(f"One day, {hero.id} and {sidekick.id} had an essential quest: they wanted to {quest.action} and {quest.goal}.")
    world.say(f"The first clue was {clue.phrase}.")

    # Act 2: the clue points to a place, and the detective follows it.
    world.say(f"{hero.id} looked at the clue and noticed it pointed toward the {clue.location}.")
    world.say(f"So {hero.id} and {sidekick.id} went to {world.setting.place} to search the {clue.location}.")

    # Simulated discovery
    found: list[str] = [clue.id]
    if clue.essential:
        world.facts["essential_clue"] = clue.id
        world.say(f"That clue was essential; without it, the mystery would not move forward.")
    next_clue = CLUES.get(clue.leads_to) if clue.leads_to in CLUES else None

    if next_clue:
        found.append(next_clue.id)
        world.say(f"Behind the first clue, they found {next_clue.phrase}.")
        world.say(f"{hero.id} knew this was the kind of clue that could unlock the whole case.")

    # Resolution depends on quest type.
    if params.quest == "find_owner":
        owner_name = "Mrs. Bell"
        world.facts["answer"] = owner_name
        world.say(f"At last, the clues led them to {owner_name}, who had been looking everywhere for the missing item.")
        world.say(f"{hero.id} gave it back, and the worry on {owner_name}'s face disappeared.")
        world.say(f"In the end, the mystery was solved, and the essential clue had done its job.")
    elif params.quest == "find_map":
        world.facts["answer"] = "the hidden map"
        world.say("The locked box opened with a soft click, and inside was the hidden map.")
        world.say(f"{sidekick.id} held the corner while {hero.id} unfolded it carefully.")
        world.say(f"By solving the mystery step by step, they finished the quest and found the map.")
    else:
        world.facts["answer"] = "the lost toy"
        world.say("The trail ended at a shelf in the back room, where the lost toy was waiting.")
        world.say(f"{hero.id} smiled, because the quest was over and the toy was safe again.")
        world.say(f"The essential clue had led them straight to the answer.")

    world.say(f"The final image was {quest.end_image}.")
    world.facts["found"] = found
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue"]
    quest: Quest = f["quest"]
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    return [
        f'Write a short detective story for children that includes the word "essential" and a clue called "{clue.label}".',
        f"Tell a mystery story where {hero.id} and {sidekick.id} must {quest.action} to {quest.goal}.",
        f"Write a gentle quest story that starts with a clue and ends with {quest.end_image}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    clue: Clue = f["clue"]
    quest: Quest = f["quest"]
    answer = f["answer"]

    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {hero.id}, who was curious and careful about solving the mystery.",
        ),
        QAItem(
            question=f"What was the essential clue?",
            answer=f"The essential clue was {clue.phrase}. It mattered because it helped the case move forward.",
        ),
        QAItem(
            question=f"What quest did {hero.id} and {sidekick.id} try to finish?",
            answer=f"They tried to {quest.action} so they could {quest.goal}.",
        ),
        QAItem(
            question=f"What answer did the clues lead them to?",
            answer=f"The clues led them to {answer}. That is how they solved the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery or find something lost.",
        ),
        QAItem(
            question="What does essential mean?",
            answer="Essential means very important, or something you really need.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(library;garden;station;museum).
clue(receipt;key;box;note).
quest(find_owner;find_map;find_toy).

essential(receipt).
essential(key).
essential(box).

leads(receipt,key).
leads(key,box).
leads(box,answer).
leads(note,answer).

solvable(P,C,Q) :- place(P), clue(C), quest(Q), essential(C), leads(C,_).
show_solvable(P,C,Q) :- solvable(P,C,Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CLUES.values():
        lines.append(asp.fact("clue", c.id))
        if c.essential:
            lines.append(asp.fact("essential", c.id))
        if c.leads_to:
            lines.append(asp.fact("leads", c.id, c.leads_to))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solvable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show show_solvable/3."))
    return sorted(set(asp.atoms(model, "show_solvable")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_solvable())
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(asp_set)} combinations).")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in asp:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Validation and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for clue in CLUES:
            if not CLUES[clue].essential:
                continue
            for quest in QUESTS:
                combos.append((place, clue, quest))
    return combos


def explain_rejection(clue: Clue) -> str:
    if not clue.essential:
        return f"(No story: the clue '{clue.label}' is not essential, so this world does not build a true mystery around it.)"
    return "(No story: that combination does not make a reasonable detective quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Essential mystery quest detective story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.clue and not CLUES[args.clue].essential:
        raise StoryError(explain_rejection(CLUES[args.clue]))
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.clue is None or c[1] == args.clue)
        and (args.quest is None or c[2] == args.quest)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, quest = rng.choice(filtered)
    name = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, quest=quest, name=name, sidekick=sidekick, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label}")
    lines.append(f"setting: {world.setting.place}")
    lines.append(f"facts: {sorted(world.facts.keys())}")
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


def valid_storyworlds_from_asp() -> list[tuple]:
    return asp_solvable()


CURATED = [
    StoryParams(place="library", clue="receipt", quest="find_owner", name="Mina", sidekick="Pip", trait="sharp"),
    StoryParams(place="museum", clue="key", quest="find_map", name="June", sidekick="Sage", trait="curious"),
    StoryParams(place="garden", clue="box", quest="find_toy", name="Rory", sidekick="Nia", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show show_solvable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_storyworlds_from_asp()
        print(f"{len(combos)} solvable combinations:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
