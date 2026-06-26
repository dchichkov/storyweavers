#!/usr/bin/env python3
"""
A small mystery-story world about a pie, a cautious clue hunt, and a careful fix.

The seed idea:
- A fresh pie is left to cool.
- Someone or something gnaws at it.
- A child notices the clue, solves the mystery, and prevents more trouble.

This world keeps the narrative close to a gentle cautionary mystery:
- a visible problem appears,
- the characters investigate,
- they identify the cause,
- they solve it with a safer habit or simple tool,
- and the ending proves the change.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    place: str = ""
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    clue: str
    can_gnaw: bool = False
    can_spoil: bool = False
    cautious_of: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.suspects: dict[str, Suspect] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.clues: list[str] = []

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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.suspects = copy.deepcopy(self.suspects)
        w.fired = set(self.fired)
        w.clues = list(self.clues)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"cooling", "watching", "covering"}),
    "pantry": Setting(place="the pantry", indoor=True, affords={"watching", "hiding", "covering"}),
    "porch": Setting(place="the porch", indoor=False, affords={"cooling", "watching", "covering"}),
}

SUSPECTS = {
    "mouse": Suspect(
        id="mouse",
        label="a small mouse",
        clue="tiny teeth marks",
        can_gnaw=True,
        can_spoil=True,
        cautious_of={"cat"},
    ),
    "dog": Suspect(
        id="dog",
        label="a muddy dog",
        clue="a wet nose print",
        can_gnaw=True,
        can_spoil=False,
        cautious_of={"whistle"},
    ),
    "squirrel": Suspect(
        id="squirrel",
        label="a hungry squirrel",
        clue="little scratch marks",
        can_gnaw=True,
        can_spoil=True,
        cautious_of={"window"},
    ),
}

TOOLS = {
    "lid": Tool(
        id="lid",
        label="pie lid",
        phrase="a clear pie lid",
        purpose="cover the pie while it cools",
    ),
    "plate": Tool(
        id="plate",
        label="plate cover",
        phrase="a sturdy plate cover",
        purpose="keep crumbs and paws away",
    ),
    "box": Tool(
        id="box",
        label="box",
        phrase="a cardboard box",
        purpose="hide the pie safely on a higher shelf",
    ),
}

PIES = {
    "apple": "apple pie",
    "berry": "berry pie",
    "pumpkin": "pumpkin pie",
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Zoe", "Ava", "Elsa"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Ben", "Eli"]
TRAITS = ["careful", "curious", "brave", "quiet", "sharp-eyed", "gentle"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    pie: str
    suspect: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def setting_detail(setting: Setting) -> str:
    if setting.place == "the kitchen":
        return "The kitchen smelled sweet, and the warm pie sat on the counter to cool."
    if setting.place == "the pantry":
        return "The pantry was quiet and dim, with shelves full of jars and crumbs."
    return "The porch held the afternoon air, and the pie cooled beside the screen door."


def culprit_sentence(suspect: Suspect, pie_label: str) -> str:
    if suspect.id == "mouse":
        return f"A small mouse had been nibbling the crust."
    if suspect.id == "dog":
        return f"A muddy dog had leaned in for a sneaky bite of the {pie_label}."
    return f"A hungry squirrel had found the {pie_label} first."


def safe_action_sentence(tool: Tool, activity: str) -> str:
    return f"They used {tool.phrase} so the pie could stay safe while it cooled."


def valid_combo(place: str, suspect: str, tool: str) -> bool:
    s = SUSPECTS[suspect]
    t = TOOLS[tool]
    if place not in SETTINGS:
        return False
    if suspect == "dog" and tool == "box":
        return False  # silly mismatch: box doesn't stop a dog at the counter
    if suspect == "mouse" and tool == "plate":
        return True
    if suspect == "mouse" and tool == "lid":
        return True
    if suspect == "squirrel" and tool in {"lid", "box"}:
        return True
    if suspect == "dog" and tool == "lid":
        return True
    return False


def choice_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def pronoun_for_gender(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


# ---------------------------------------------------------------------------
# Narrative simulation
# ---------------------------------------------------------------------------

def tell(setting: Setting, pie_id: str, suspect: Suspect, tool: Tool,
         hero_name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        traits=["little", trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=f"the {parent_type}",
    ))
    pie = world.add(Entity(
        id="pie",
        kind="thing",
        type="pie",
        label="pie",
        phrase=f"a fresh {PIES[pie_id]}",
        caretaker=parent.id,
        place=setting.place,
    ))

    world.facts.update(hero=hero, parent=parent, pie=pie, suspect=suspect, tool=tool, setting=setting)

    hero.memes["curiosity"] = 1
    hero.memes["caution"] = 1

    world.say(f"{hero_name} was a little {trait} {gender} who liked noticing small details.")
    world.say(f"{pronoun_for_gender(gender).capitalize()} loved the smell of {pie.phrase}, especially when it was still warm.")

    world.para()
    world.say(setting_detail(setting))
    world.say(f"But then {hero_name} spotted something odd near the crust: {suspect.clue}.")
    world.say(f"{hero_name} knew a mystery when {pronoun_for_gender(gender)} saw one.")

    world.para()
    world.say(f"{pronoun_for_gender(gender).capitalize()} did not touch the pie right away.")
    world.say(f"Instead, {hero_name} looked carefully around the room and followed the clue.")
    hero.memes["problem_solving"] = 1

    if suspect.id == "mouse":
        world.say("Tiny crumbs led under a cabinet, and a faint scratch on the floor matched the nibble marks.")
    elif suspect.id == "dog":
        world.say("A damp paw print by the door showed that a hungry visitor had come in from outside.")
    else:
        world.say("Little scratch marks pointed toward the open window and the tree branch nearby.")

    world.para()
    world.say(f"{hero_name} told {parent.label} what had happened.")
    world.say(f"Together they chose a careful fix: {safe_action_sentence(tool, tool.purpose)}")
    pie.meters["safe"] = 1
    world.facts["solved"] = True
    world.facts["tool_used"] = tool.id
    world.facts["clue"] = suspect.clue

    world.para()
    if suspect.id == "mouse":
        world.say(f"They found a tiny mouse and gently shooed it toward the pantry door so it would not come back for the pie.")
    elif suspect.id == "dog":
        world.say(f"They wiped the muddy nose print, shut the screen door, and gave the dog a bone far from the counter.")
    else:
        world.say(f"They closed the window before the squirrel could sneak back in, and the branch tapped harmlessly outside.")

    world.say(f"After that, the pie stayed covered and the mystery was solved.")
    world.say(f"At the end, {hero_name} could stand back and smile, because the pie was safe and the clues made sense.")

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    suspect = f["suspect"]
    pie = f["pie"]
    return [
        f"Write a gentle mystery about a child named {hero.id} who notices {suspect.clue} near a {pie.phrase}.",
        f"Tell a child-facing story where someone solves the problem of a gnawed pie by being careful and clever.",
        f"Write a short cautionary mystery in which a pie needs protection and the clue leads to the culprit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    pie = f["pie"]
    suspect = f["suspect"]
    tool = f["tool"]
    gender = "girl" if hero.type == "girl" else "boy"
    qas = [
        QAItem(
            question=f"What mystery did {hero.id} notice in the story?",
            answer=f"{hero.id} noticed that something had gnawed the {pie.phrase} while it was cooling.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem safely?",
            answer=f"{hero.id} looked for clues instead of touching the pie right away, then worked with {parent.label} to use {tool.phrase} and protect it.",
        ),
        QAItem(
            question=f"What clue showed who had nibbled the pie?",
            answer=f"The clue was {suspect.clue}, which helped {hero.id} figure out the cause.",
        ),
    ]
    if suspect.id == "mouse":
        qas.append(QAItem(
            question=f"Who was the culprit behind the gnawed crust?",
            answer="A small mouse was the culprit, and the family shooed it away gently.",
        ))
    elif suspect.id == "dog":
        qas.append(QAItem(
            question=f"Who was the culprit behind the muddy print and the missing bite?",
            answer="A muddy dog was the culprit, and the family kept the door shut afterward.",
        ))
    else:
        qas.append(QAItem(
            question=f"Who was the culprit behind the scratch marks?",
            answer="A hungry squirrel was the culprit, and the family closed the window to keep the pie safe.",
        ))
    qas.append(QAItem(
        question=f"How did {hero.id} feel after the mystery was solved?",
        answer=f"{hero.id} felt glad and proud because the problem was fixed without rushing into trouble.",
    ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    suspect = f["suspect"]
    tool = f["tool"]
    pie = f["pie"]
    out = []
    out.append(QAItem(
        question="Why do people cover a pie while it cools?",
        answer="People cover a pie while it cools so crumbs, bugs, or paws do not get into it before it is ready.",
    ))
    out.append(QAItem(
        question="What does it mean to solve a mystery?",
        answer="To solve a mystery means to look for clues, think carefully, and figure out what caused the problem.",
    ))
    if suspect.id == "mouse":
        out.append(QAItem(
            question="Why can a mouse gnaw food?",
            answer="A mouse can gnaw food because its teeth are made for nibbling and chewing.",
        ))
    if tool.id in {"lid", "plate"}:
        out.append(QAItem(
            question="What is a cover used for?",
            answer="A cover is used to shield food from dirt, hands, or animals so it stays clean.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  clues: {world.clues}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_ok(P) :- setting(P).

needs_cover(Pie) :- pie(Pie).
cautionary_story(P, S, T) :- place_ok(P), suspect(S), tool(T), valid_fix(S, T), needs_cover(pie).

valid_fix(mouse, lid).
valid_fix(mouse, plate).
valid_fix(squirrel, lid).
valid_fix(squirrel, box).
valid_fix(dog, lid).

#show cautionary_story/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("pie", "pie"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solutions() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show cautionary_story/3."))
    return sorted(set(asp.atoms(model, "cautionary_story")))


def python_solutions() -> list[tuple]:
    out = []
    for p in SETTINGS:
        for s in SUSPECTS:
            for t in TOOLS:
                if valid_combo(p, s, t):
                    out.append((p, s, t))
    return sorted(set(out))


def asp_verify() -> int:
    a = set(asp_solutions())
    b = set(python_solutions())
    if a == b:
        print(f"OK: clingo gate matches Python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    tool = args.tool or rng.choice(list(TOOLS))
    pie = args.pie or rng.choice(list(PIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)

    if place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if pie not in PIES:
        raise StoryError("Unknown pie.")

    if args.suspect or args.tool or args.place:
        if not valid_combo(place, suspect, tool):
            raise StoryError(
                f"(No story: the chosen suspect ({suspect}) and tool ({tool}) do not make a plausible cautionary fix at {place}.)"
            )

    name = args.name or choice_name(gender, rng)
    return StoryParams(
        place=place,
        pie=pie,
        suspect=suspect,
        tool=tool,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        params.pie,
        SUSPECTS[params.suspect],
        TOOLS[params.tool],
        params.name,
        params.gender,
        params.parent,
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

CURATED = [
    StoryParams(place="kitchen", pie="apple", suspect="mouse", tool="lid", name="Mina", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="porch", pie="berry", suspect="squirrel", tool="box", name="Theo", gender="boy", parent="father", trait="sharp-eyed"),
    StoryParams(place="kitchen", pie="pumpkin", suspect="dog", tool="lid", name="Nora", gender="girl", parent="mother", trait="curious"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary mystery storyworld about a gnawed pie.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--pie", choices=PIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show cautionary_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sols = asp_solutions()
        print(f"{len(sols)} compatible (place, suspect, tool) triples:\n")
        for p, s, t in sols:
            print(f"  {p:8} {s:9} {t}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.suspect} / {p.tool} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
