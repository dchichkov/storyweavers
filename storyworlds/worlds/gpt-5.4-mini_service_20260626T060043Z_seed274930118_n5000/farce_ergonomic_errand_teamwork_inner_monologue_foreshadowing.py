#!/usr/bin/env python3
"""
A small standalone storyworld: a detective-style errand that turns into a
farce, with teamwork, inner monologue, and foreshadowing.

The core premise:
- A small team is trying to complete an ergonomic errand.
- A missing object, a silly misunderstanding, and a chain of tiny accidents
  create a comic mystery.
- The team uses clues, teamwork, and a careful plan to finish the errand.
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
# Basic model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    route: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Errand:
    id: str
    goal: str
    object_label: str
    object_phrase: str
    clue: str
    mishap: str
    foreshadow: str
    twist: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    purpose: str
    helps: set[str] = field(default_factory=set)
    ergonomic: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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

        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "office": Setting(place="the small office", route="the hallway", affords={"search", "run"}),
    "museum": Setting(place="the quiet museum", route="the side corridor", affords={"search", "run"}),
    "library": Setting(place="the old library", route="the reading room", affords={"search", "run"}),
    "market": Setting(place="the corner market", route="the narrow aisle", affords={"search", "run"}),
}

ERRANDS = {
    "parcel": Errand(
        id="parcel",
        goal="deliver the parcel",
        object_label="parcel",
        object_phrase="a wrapped parcel with a blue ribbon",
        clue="a blue ribbon",
        mishap="the parcel went missing",
        foreshadow="the ribbon had been peeking from under the desk all morning",
        twist="the parcel had been tucked into the ergonomic chair pocket by mistake",
        keyword="errand",
        tags={"errand", "parcel", "delivery"},
    ),
    "receipt": Errand(
        id="receipt",
        goal="find the receipt",
        object_label="receipt",
        object_phrase="a folded receipt with a coffee stain",
        clue="a coffee stain",
        mishap="the receipt vanished",
        foreshadow="the stain had matched the one on the notebook all day",
        twist="the receipt had been used as a bookmark by the detective's helper",
        keyword="errand",
        tags={"errand", "receipt", "paper"},
    ),
    "key": Errand(
        id="key",
        goal="return the key",
        object_label="key",
        object_phrase="a small brass key",
        clue="a brass shine",
        mishap="the key was nowhere in sight",
        foreshadow="the shine had flashed near the lamp before the lunch break",
        twist="the key had slipped into the pocket of the ergonomic satchel",
        keyword="errand",
        tags={"errand", "key", "search"},
    ),
}

TOOLS = {
    "satchel": Tool(
        id="satchel",
        label="an ergonomic satchel",
        purpose="carry clues without hurting anyone's shoulder",
        helps={"key", "parcel"},
        ergonomic=True,
    ),
    "lamp": Tool(
        id="lamp",
        label="a bright desk lamp",
        purpose="spot tiny clues",
        helps={"receipt", "key"},
        ergonomic=False,
    ),
    "cart": Tool(
        id="cart",
        label="a rolling cart",
        purpose="move a parcel without dropping it",
        helps={"parcel"},
        ergonomic=False,
    ),
}

PEOPLE = [
    ("Mina", "girl", ["careful", "quick-eyed"]),
    ("Toby", "boy", ["lively", "patient"]),
    ("June", "girl", ["clever", "gentle"]),
    ("Perry", "boy", ["serious", "kind"]),
]

HELPERS = [
    ("assistant", "the assistant"),
    ("doorman", "the doorman"),
    ("clerk", "the clerk"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% An errand is solvable when a setting affords searching and a suitable tool helps.
solvable(E) :- errand(E), afford_search(S), suitable(T,E), ergonomic_ok(E,T).

% A tool is suitable when its help-tags overlap the errand tags.
suitable(T,E) :- tool(T), errand(E), helps(T,Tag), tag(E,Tag).

% Ergonomic tools always qualify; other tools only qualify if the errand is light.
ergonomic_ok(_,T) :- ergonomic(T).
ergonomic_ok(E,T) :- tool(T), errand(E), not ergonomic(T), light(E).

% A valid story is one errand in one setting with at least one helper and one tool.
valid_story(S,E) :- setting(S), errand(E), solvable(E), helper(_), tool(_).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("afford_search", sid))
    for eid, e in ERRANDS.items():
        lines.append(asp.fact("errand", eid))
        for tag in sorted(e.tags):
            lines.append(asp.fact("tag", eid, tag))
        if eid in {"receipt"}:
            lines.append(asp.fact("light", eid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.ergonomic:
            lines.append(asp.fact("ergonomic", tid))
        for tag in sorted(t.helps):
            lines.append(asp.fact("helps", tid, tag))
    for _, helper in HELPERS:
        lines.append(asp.fact("helper", helper))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set((sid, eid) for sid in SETTINGS for eid in valid_errands())
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} valid stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story parameters and world logic
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    errand: str
    name: str
    role: str
    helper: str
    tool: str
    seed: Optional[int] = None


def valid_errands() -> list[str]:
    return [eid for eid in ERRANDS]


def reasonableness_gate(setting: Setting, errand: Errand, tool: Tool) -> bool:
    return True if tool.ergoonomic if False else True


def check_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.errand not in ERRANDS:
        raise StoryError("Unknown errand.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.role not in {"detective", "helper"}:
        raise StoryError("Unknown role.")
    if params.helper not in {h for h, _ in HELPERS}:
        raise StoryError("Unknown helper.")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    errand = ERRANDS[params.errand]
    tool = TOOLS[params.tool]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name, kind="character", type="detective",
        label=params.name, traits=["small", "careful", "curious"],
        meters={"tired": 0.0}, memes={"worry": 0.0, "focus": 1.0, "hope": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper, kind="character", type="helper",
        label=f"the {params.helper}", traits=["helpful"],
        meters={"tired": 0.0}, memes={"worry": 0.0, "teamwork": 1.0},
    ))
    object_ent = world.add(Entity(
        id=errand.id, kind="thing", type=errand.object_label, label=errand.object_label,
        phrase=errand.object_phrase, owner=hero.id, carried_by=None, location=setting.place,
    ))
    tool_ent = world.add(Entity(
        id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.label,
        owner=hero.id, carried_by=hero.id, location=setting.place,
    ))

    world.facts.update(hero=hero, helper=helper, object=object_ent, tool=tool_ent, errand=errand)

    # Setup
    world.say(f"{hero.id} was a tiny detective with a notebook and a very serious face.")
    world.say(f"Today, {hero.id} had an errand: to {errand.goal} at {setting.place}.")
    world.say(f"{hero.id} noticed {errand.foreshadow}, and that detail stayed in {hero.pronoun('possessive')} mind.")
    world.say(f"In {hero.pronoun('possessive')} inner monologue, {hero.id} thought, "
              f"'{errand.clue} does not appear by accident.'")

    world.para()

    # Conflict
    world.say(f"Then came the problem: {errand.mishap}.")
    world.say(f"{hero.id} looked around and thought, 'If the {errand.object_label} is hidden, "
              f"I need clues, not panic.'")
    world.say(f"{helper.id} arrived with {tool.label}, saying it could {tool.purpose}.")
    world.say(f"The little team checked the {setting.route} together, one careful step at a time.")

    # Farce beat
    if errand.id == "parcel":
        world.say("A bump made the lamp wobble, and the ribbon tied itself around a chair leg like it was helping solve the case.")
    elif errand.id == "receipt":
        world.say("A page slipped open, and the coffee stain on the note looked exactly like a tiny moustache.")
    else:
        world.say("A drawer clicked shut by itself, and everyone stared at it as if it had tried to give an alibi.")

    world.para()

    # Resolution
    world.say(f"{hero.id} followed {errand.clue}, and {helper.id} held the lamp steady.")
    world.say(f"Together, they found that {errand.twist}.")
    world.say(f"{hero.id} felt the worry melt away and thought, 'A clue is just a clue until someone works with me.'")
    world.say(f"So the team finished the errand, and {hero.id} left {setting.place} with a lighter step and a tidy notebook.")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A and story formatting
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    errand: Errand = f["errand"]
    return [
        f"Write a short detective-style story for a child about an errand, teamwork, and a silly mix-up involving {errand.keyword}.",
        f"Tell a farce with inner monologue and foreshadowing where a small detective tries to {errand.goal}.",
        f"Write a gentle mystery where a helper brings an ergonomic tool and the team solves a comic problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    errand: Errand = f["errand"]
    setting: Setting = world.setting
    tool: Entity = f["tool"]

    return [
        QAItem(
            question=f"What errand did {hero.id} have at {setting.place}?",
            answer=f"{hero.id} had to {errand.goal} at {setting.place}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the search?",
            answer=f"{helper.id} helped {hero.id}, and the two of them worked as a team.",
        ),
        QAItem(
            question=f"What tool made the search easier?",
            answer=f"{tool.label} made the search easier because it helped them look carefully without getting in the way.",
        ),
        QAItem(
            question=f"What detail hinted at the solution before the problem was solved?",
            answer=f"The story foreshadowed the answer when {errand.foreshadow}.",
        ),
        QAItem(
            question=f"How did the story turn from trouble into success?",
            answer=f"The team followed clues, found that {errand.twist}, and finished the errand together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ergonomic mean?",
            answer="Ergonomic means made to fit the body comfortably and make a task easier or safer.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help one another and work together toward the same goal.",
        ),
        QAItem(
            question="What is a detective story?",
            answer="A detective story is a mystery where someone looks for clues to solve a problem or find out what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def valid_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    errand = args.errand or rng.choice(list(ERRANDS))
    name = args.name or rng.choice([p[0] for p in PEOPLE])
    role = args.role or "detective"
    helper = args.helper or rng.choice([h[0] for h in HELPERS])
    tool = args.tool or rng.choice(list(TOOLS))
    return StoryParams(setting=setting, errand=errand, name=name, role=role, helper=helper, tool=tool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = valid_params(args, rng)
    check_params(params)
    tool = TOOLS[params.tool]
    if params.errand == "parcel" and tool.id not in {"satchel", "cart"}:
        raise StoryError("This errand needs a more useful tool.")
    return params


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style errand farce with teamwork and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["detective", "helper"])
    ap.add_argument("--helper", choices=[h[0] for h in HELPERS])
    ap.add_argument("--tool", choices=TOOLS)
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


CURATED = [
    StoryParams(setting="office", errand="parcel", name="Mina", role="detective", helper="assistant", tool="satchel"),
    StoryParams(setting="museum", errand="receipt", name="Toby", role="detective", helper="doorman", tool="lamp"),
    StoryParams(setting="library", errand="key", name="June", role="detective", helper="clerk", tool="satchel"),
]

def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_valid_errands() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show solvable/1."))
    return sorted(set(asp.atoms(model, "solvable")))

def asp_program_show() -> str:
    return asp_program("#show valid_story/2.\n#show solvable/1.")

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solvable/1.\n#show valid_story/2."))
        sols = sorted(set(asp.atoms(model, "solvable")))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(sols)} solvable errands; {len(stories)} valid stories")
        for item in stories:
            print(item)
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
            except StoryError as e:
                print(e)
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
