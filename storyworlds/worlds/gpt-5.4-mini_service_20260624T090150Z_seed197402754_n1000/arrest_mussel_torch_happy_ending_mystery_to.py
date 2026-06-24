#!/usr/bin/env python3
"""
storyworlds/worlds/arrest_mussel_torch_happy_ending_mystery_to.py
===================================================================

A small whodunit-style story world about a missing torch, a mussel clue, and a
careful arrest that leads to a happy ending.

Seed tale:
---
On a foggy evening by the harbor, a lantern-torch went missing from the pier
shed. A clever child and a kind officer searched for clues. They found a wet
mussel shell near the rocks, then a trail of brine drops leading to a sneaky
thief. The thief had tried to hide the torch, but the truth came out. The
officer made an arrest, the torch was returned, and everyone learned that
telling the truth is safer than taking what is not yours.

This world keeps the whodunit shape:
- a mystery to solve
- clues that change the investigation state
- a cautious reveal and arrest
- a happy ending
- a moral value: honesty matters
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

METER = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "officer"}
        male = {"boy", "father", "man", "guard", "detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the harbor"
    mood: str = "foggy"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    culprit_kind: str
    culprit_trait: str
    moral: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []
        self.mystery_solved = False
        self.arrest_made = False
        self.clue_found = False
        self.culprit_identified = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        c.mystery_solved = self.mystery_solved
        c.arrest_made = self.arrest_made
        c.clue_found = self.clue_found
        c.culprit_identified = self.culprit_identified
        return c


def _say_state(world: World, tag: str) -> None:
    world.trace.append(f"[{tag}]")


def _find_clue(world: World) -> None:
    if world.clue_found:
        return
    clue = world.get("mussel_shell")
    clue.hidden_in = None
    clue.meters["found"] = 1
    clue.memes["importance"] = 1
    world.clue_found = True
    world.say("Near the wet rocks, the child noticed a small mussel shell stuck in the mud.")


def _read_clue(world: World) -> None:
    if not world.clue_found or world.culprit_identified:
        return
    world.culprit_identified = True
    world.say("The shell made sense of the puzzle, because it matched the briny trail beside the pier.")
    world.say("That trail pointed straight to the lantern room, where someone had tried to hide the torch.")


def _reveal_culprit(world: World) -> None:
    culprit = world.get("culprit")
    torch = world.get("torch")
    if not world.culprit_identified or world.mystery_solved:
        return
    culprit.memes["nervous"] = 1
    culprit.memes["guilt"] = 1
    torch.hidden_in = None
    torch.owner = "harbor"
    world.mystery_solved = True
    world.say(f"The culprit was {culprit.label}, who had taken the torch to keep it for {culprit.pronoun('object')}self.")
    world.say("When the truth came out, the room went quiet, and the stolen torch was finally found.")


def _arrest(world: World) -> None:
    officer = world.get("officer")
    culprit = world.get("culprit")
    if not world.mystery_solved or world.arrest_made:
        return
    culprit.memes["caught"] = 1
    officer.memes["duty"] = 1
    world.arrest_made = True
    world.say(f"{officer.label} made an arrest, and the sneaky thief had to hand over the torch.")
    world.say("The officer said that being honest from the start would have been kinder for everyone.")


def _happy_ending(world: World) -> None:
    if not world.arrest_made:
        return
    child = world.get("child")
    officer = world.get("officer")
    torch = world.get("torch")
    torch.owner = "harbor"
    torch.meters["returned"] = 1
    child.memes["relief"] = 1
    officer.memes["calm"] = 1
    world.say(
        f"In the end, the harbor glowed again when the torch was returned to its hook, "
        f"and {child.label} smiled at the bright, safe light."
    )
    world.say(
        f"{officer.label} thanked {child.label} for paying close attention, and the mystery ended with a happy dinner by the water."
    )


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        before = (world.clue_found, world.culprit_identified, world.mystery_solved, world.arrest_made)
        _find_clue(world)
        _read_clue(world)
        _reveal_culprit(world)
        _arrest(world)
        _happy_ending(world)
        after = (world.clue_found, world.culprit_identified, world.mystery_solved, world.arrest_made)
        if after != before:
            changed = True


SETTINGS = {
    "harbor": Setting(place="the harbor", mood="foggy", affords={"search", "arrest"}),
    "pier": Setting(place="the pier", mood="foggy", affords={"search", "arrest"}),
    "lighthouse": Setting(place="the lighthouse", mood="misty", affords={"search", "arrest"}),
}

MYSTERIES = {
    "torch": Mystery(
        id="torch_case",
        missing="torch",
        clue="mussel shell",
        culprit_kind="character",
        culprit_trait="sneaky",
        moral="telling the truth is better than stealing",
    ),
}

NAMES = ["Mina", "Nico", "Ivy", "Owen", "June", "Eli"]
OFFICERS = ["Officer Reed", "Officer Lane", "Officer Cole"]
CULPRITS = ["Pip", "Cora", "Jett", "Milo"]
TRAITS = ["careful", "curious", "patient"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    officer: str
    culprit: str
    trait: str
    seed: Optional[int] = None


def reasonableness_check(setting: Setting, mystery: Mystery) -> None:
    if "search" not in setting.affords or "arrest" not in setting.affords:
        raise StoryError("That setting cannot plausibly support both a search and an arrest.")
    if mystery.id != "torch_case":
        raise StoryError("Only the torch mystery is supported in this world.")


def tell(setting: Setting, mystery: Mystery, hero_name: str, officer_name: str, culprit_name: str, trait: str) -> World:
    world = World(setting)

    child = world.add(Entity(
        id="child",
        kind="character",
        type="girl" if hero_name in {"Mina", "Ivy", "June"} else "boy",
        label=hero_name,
        traits=["little", trait],
    ))
    officer = world.add(Entity(
        id="officer",
        kind="character",
        type="officer",
        label=officer_name,
        traits=["kind", "steady"],
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type="boy" if culprit_name in {"Pip", "Jett", "Milo"} else "girl",
        label=culprit_name,
        traits=["sneaky", mystery.culprit_trait],
    ))
    torch = world.add(Entity(
        id="torch",
        type="thing",
        label="torch",
        phrase="a bright harbor torch",
        owner="harbor",
        hidden_in="lantern room",
        meters={"missing": 1},
    ))
    shell = world.add(Entity(
        id="mussel_shell",
        type="thing",
        label="mussel shell",
        phrase="a small wet mussel shell",
        hidden_in="mud",
        meters={"hidden": 1},
        memes={"importance": 0},
    ))

    world.facts.update(
        hero=child,
        officer=officer,
        culprit=culprit,
        torch=torch,
        shell=shell,
        mystery=mystery,
        setting=setting,
    )

    world.say(f"On a {setting.mood} evening at {setting.place}, {hero_name} helped look for a missing torch.")
    world.say(f"{hero_name} was {trait} and wanted to solve the mystery the right way.")
    world.say(f"{officer_name} promised to help, because every clue mattered.")
    world.para()
    world.say("First they searched the muddy stones by the water, where the tide had left little surprises behind.")
    propagate(world)
    world.para()
    world.say(f"Then the clue fit together, and {culprit_name} could no longer hide what had happened.")
    propagate(world)
    world.para()
    if world.arrest_made:
        world.say("The harbor quieted down, and the bright torch was safe again.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child that uses the words "torch" and "mussel" and ends with an arrest.',
        f"Tell a mystery story where {f['hero'].label} and {f['officer'].label} solve a missing torch case with a mussel clue.",
        f"Write a happy-ending detective story at {f['setting'].place} about a torch, a mussel shell, and telling the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["hero"]
    officer = f["officer"]
    culprit = f["culprit"]
    torch = f["torch"]
    return [
        QAItem(
            question=f"What mystery did {child.label} try to solve at {f['setting'].place}?",
            answer=f"{child.label} tried to solve the mystery of the missing torch.",
        ),
        QAItem(
            question="What clue helped solve the case?",
            answer="A small mussel shell helped solve the case because it pointed to the place where the torch had been hidden.",
        ),
        QAItem(
            question=f"Who made the arrest when the truth was clear?",
            answer=f"{officer.label} made the arrest after the culprit was identified.",
        ),
        QAItem(
            question=f"What happened to the torch in the end?",
            answer="The torch was returned to the harbor and the light shone safely again.",
        ),
        QAItem(
            question="What moral value did the story show?",
            answer="The story showed that telling the truth is better than stealing and hiding what does not belong to you.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mussel?",
            answer="A mussel is a shellfish that lives in water and has a hard shell.",
        ),
        QAItem(
            question="What is a torch used for?",
            answer="A torch gives off light so people can see in the dark.",
        ),
        QAItem(
            question="What does an officer do?",
            answer="An officer helps keep people safe and can arrest someone who breaks the rules.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
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
        bits = []
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"flags: clue_found={world.clue_found} culprit_identified={world.culprit_identified} mystery_solved={world.mystery_solved} arrest_made={world.arrest_made}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(harbor).
setting(pier).
setting(lighthouse).
affords(harbor,search). affords(harbor,arrest).
affords(pier,search). affords(pier,arrest).
affords(lighthouse,search). affords(lighthouse,arrest).

mystery(torch_case).
missing(torch_case,torch).
clue(torch_case,mussel_shell).
moral(torch_case,honesty).

valid_story(S,torch_case) :- setting(S), affords(S,search), affords(S,arrest).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("moral", mid, "honesty"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, "torch_case") for s in SETTINGS if "search" in SETTINGS[s].affords and "arrest" in SETTINGS[s].affords}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world about a torch, a mussel clue, and an arrest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--officer", choices=OFFICERS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or "torch"
    reasonableness_check(SETTINGS[setting], MYSTERIES[mystery])
    name = args.name or rng.choice(NAMES)
    officer = args.officer or rng.choice(OFFICERS)
    culprit = args.culprit or rng.choice(CULPRITS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, officer=officer, culprit=culprit, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.name, params.officer, params.culprit, params.trait)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            p = StoryParams(setting=setting, mystery="torch", name=NAMES[0], officer=OFFICERS[0], culprit=CULPRITS[0], trait=TRAITS[0])
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
