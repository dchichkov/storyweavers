#!/usr/bin/env python3
"""
storyworlds/worlds/itch_dim_hijklmnop_drool_suspense_detective_story.py
=======================================================================

A small detective-style story world with suspenseful clue tracing.

Seed tale used to shape the simulation:
---
A child detective finds a dim hallway, a sticky trail of drool, and a note that
says "hijklmnop." Something is missing, and the clues feel strange. The detective
follows the clues, notices an itchy old sweater on a chair, and learns that the
family dog hid the missing treat under the couch after sniffing it out.
---

This world models a tiny mystery:
- a detective wants to solve a missing-item case,
- suspense grows as clues are found,
- the final turn identifies the culprit and the hidden item,
- the ending proves the state change by returning the item and easing worry.

The seed words are used as literal clue-language and as the mystery's odd tone:
"itch-dim", "hijklmnop", and "drool".
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
    hidden_in: Optional[str] = None
    found: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "detective_girl"}
        male = {"boy", "man", "father", "dad", "detective_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the house"
    dimness: float = 1.0
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    gives_suspense: float = 1.0
    reveals: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    clue_match: str = ""
    hiding_place: str = ""
    nervousness: float = 0.0


@dataclass
class StoryParams:
    setting: str
    detective_name: str
    detective_gender: str
    suspect: str
    hidden_item: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.clues_found: list[str] = []
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.clues_found = list(self.clues_found)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _find_clue(world: World, clue_id: str) -> None:
    clue = world.get(clue_id)
    if clue.found:
        return
    clue.found = True
    world.clues_found.append(clue_id)
    world.entities["detective"].memes["suspense"] = max(
        world.entities["detective"].memes.get("suspense", 0.0), clue.gives_suspense
    )


def _raise_suspense(world: World, amount: float) -> None:
    d = world.entities["detective"]
    d.memes["suspense"] = d.memes.get("suspense", 0.0) + amount


def _solve_case(world: World) -> None:
    if world.facts.get("solved"):
        return
    world.facts["solved"] = True
    detective = world.get("detective")
    suspect = world.get(world.facts["suspect"])
    item = world.get(world.facts["hidden_item"])
    item.hidden_in = None
    item.found = True
    detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1
    detective.memes["suspense"] = 0.0
    suspect.memes["nervousness"] = 0.0


SETTINGS = {
    "house": Setting(place="the old house", dimness=0.7, indoors=True, affords={"search"}),
    "hallway": Setting(place="the dim hallway", dimness=1.0, indoors=True, affords={"search"}),
    "kitchen": Setting(place="the quiet kitchen", dimness=0.5, indoors=True, affords={"search"}),
}

HIDDEN_ITEMS = {
    "cookie": "a missing cookie",
    "toy": "a missing toy car",
    "key": "a little brass key",
}

SUSPECTS = {
    "dog": Suspect(
        id="dog",
        label="the family dog",
        type="dog",
        clue_match="drool",
        hiding_place="under the couch",
        nervousness=0.0,
    ),
    "cat": Suspect(
        id="cat",
        label="the cat",
        type="cat",
        clue_match="itch-dim",
        hiding_place="behind the curtain",
        nervousness=0.0,
    ),
}

CLUES = {
    "drool": Clue(
        id="drool",
        label="a line of drool",
        phrase="a sticky line of drool",
        gives_suspense=1.0,
        reveals="dog",
        tags={"drool"},
    ),
    "code": Clue(
        id="code",
        label='the note that said "hijklmnop"',
        phrase='a crumpled note with the word "hijklmnop"',
        gives_suspense=1.2,
        reveals="hidden_item",
        tags={"hijklmnop"},
    ),
    "itch": Clue(
        id="itch",
        label="an itch-dim sweater on a chair",
        phrase="an itch-dim sweater that scratched the chair",
        gives_suspense=0.8,
        reveals="cat",
        tags={"itch-dim"},
    ),
}


GENDER_NAMES = {
    "girl": ["Maya", "Nora", "Lena", "Zoe", "Ruby"],
    "boy": ["Noah", "Eli", "Theo", "Finn", "Max"],
}


def investigate(world: World, detective: Entity, clue: Clue) -> None:
    _raise_suspense(world, clue.gives_suspense)
    _find_clue(world, clue.id)
    if clue.id == "drool":
        world.say("A shiny trail of drool glimmered in the dim light, and that made the case feel closer and stranger.")
    elif clue.id == "code":
        world.say('The detective found a note in the shadows. It said "hijklmnop," as if someone had tried to hide a secret in plain sight.')
    elif clue.id == "itch":
        world.say("On a chair sat an itch-dim sweater, fuzzy and odd, and it seemed like the room itself was warning of a trick.")
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1


def follow_suspect(world: World, suspect: Suspect) -> None:
    world.get("detective").memes["suspense"] = max(world.get("detective").memes.get("suspense", 0.0), 1.5)
    world.say(
        f"The clues led the detective toward {suspect.label}, and {suspect.label} looked nervous in the hush of the {world.setting.place}."
    )


def reveal(world: World, suspect: Suspect, item: Entity) -> None:
    world.say(
        f"At last, the detective looked under the couch and found {item.phrase}. {suspect.label} had tucked it there after sniffing it out."
    )
    world.say(
        f"The mystery made sense now: the drool, the strange hijklmnop note, and the itch-dim sweater all pointed to a silly hiding place, not a bad plan."
    )
    _solve_case(world)


def tell(setting: Setting, detective_name: str, detective_gender: str, suspect_id: str, hidden_item_id: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=detective_gender,
        label=detective_name,
        meters={"feet": 0.0},
        memes={"curiosity": 0.0, "suspense": 0.0, "relief": 0.0},
    ))
    suspect = SUSPECTS[suspect_id]
    item_label = HIDDEN_ITEMS[hidden_item_id]
    item = world.add(Entity(
        id="hidden_item",
        kind="thing",
        type=hidden_item_id,
        label=item_label.split()[-1],
        phrase=item_label,
        hidden_in=suspect.hiding_place,
        found=False,
    ))
    world.add(Entity(
        id=suspect.id,
        kind="character",
        type=suspect.type,
        label=suspect.label,
        memes={"nervousness": suspect.nervousness},
    ))
    world.add(Entity(
        id="drool",
        kind="thing",
        type="clue",
        label="drool",
        phrase=CLUES["drool"].phrase,
        found=False,
    ))
    world.add(Entity(
        id="code",
        kind="thing",
        type="clue",
        label="hijklmnop",
        phrase=CLUES["code"].phrase,
        found=False,
    ))
    world.add(Entity(
        id="itch",
        kind="thing",
        type="clue",
        label="itch-dim",
        phrase=CLUES["itch"].phrase,
        found=False,
    ))

    world.facts.update(
        detective=detective,
        suspect=suspect.id,
        hidden_item=item.id,
        setting=setting,
        solved=False,
    )

    world.say(
        f"{detective.label} was a little detective who loved quiet questions and careful footsteps in {setting.place}."
    )
    world.say(
        f"One dim evening, {detective.label} noticed that something was missing, and the room felt just suspenseful enough to make every sound matter."
    )

    world.para()
    investigate(world, detective, world.get("drool"))
    follow_suspect(world, suspect)

    world.para()
    investigate(world, detective, world.get("code"))
    investigate(world, detective, world.get("itch"))

    world.para()
    reveal(world, suspect, item)
    detective.memes["suspense"] = 0.0
    world.say(
        f"{detective.label} smiled when the missing item was safe again, and the dim room felt cozy instead of mysterious."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    suspect = f["suspect"]
    item = f["hidden_item"]
    return [
        'Write a short suspenseful detective story for a young child that includes "hijklmnop" and "drool".',
        f"Tell a gentle detective mystery where {detective.label} follows clues to find {world.get(item).phrase}.",
        "Write a child-friendly mystery with a dim room, a strange note, and a surprising but harmless culprit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective = world.facts["detective"]
    suspect = world.facts["suspect"]
    item = world.facts["hidden_item"]
    det = detective.label
    item_phrase = world.get(item).phrase
    suspect_label = world.get(suspect).label
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {det}, and {det} carefully followed the clues through the dim room.",
        ),
        QAItem(
            question=f"What was missing in the mystery?",
            answer=f"The missing thing was {item_phrase}. It was hidden for a while, but the detective found it in the end.",
        ),
        QAItem(
            question='What did the note say?',
            answer='The note said "hijklmnop," which made the mystery feel odd and suspenseful.',
        ),
        QAItem(
            question=f"Who turned out to be part of the clue trail?",
            answer=f"{suspect_label} was part of the clue trail, because the drool and hiding place pointed that way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does drool mean?",
            answer="Drool is a little bit of spit that can drip from an animal's mouth.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that makes you wonder what will happen next.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to solve a mystery.",
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
        bits = []
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.found:
            bits.append("found=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  clues_found: {world.clues_found}")
    lines.append(f"  solved: {world.facts.get('solved')}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue becomes available when the story registers it as a clue.
clue(C) :- registered_clue(C).

% Suspense rises from odd clues; the strongest clue can lead to the solution.
raises_suspense(C) :- clue(C), clue_tag(C, susp).

% The dog is a plausible culprit when drool is present.
culprit(dog) :- clue_tag(drool, drool).

% The hidden item is found when the note and the culprit's hiding place both matter.
solved(Item, Suspect) :- culprit(Suspect), clue_tag(code, code), clue_tag(itch, itch), hidden_item(Item).

#show clue/1.
#show culprit/1.
#show solved/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CLUES:
        lines.append(asp.fact("registered_clue", cid))
    lines.append(asp.fact("clue_tag", "drool", "drool"))
    lines.append(asp.fact("clue_tag", "code", "code"))
    lines.append(asp.fact("clue_tag", "itch", "itch"))
    lines.append(asp.fact("hidden_item", "cookie"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solve_atoms() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/2.\n#show culprit/1.\n"))
    return sorted(set(asp.atoms(model, "solved"))), sorted(set(asp.atoms(model, "culprit")))


def asp_verify() -> int:
    solved_atoms, culprit_atoms = asp_solve_atoms()
    ok = ("dog",) in culprit_atoms and ("cookie", "dog") in solved_atoms
    if ok:
        print("OK: ASP twin matches the story's clue logic.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected culprit/solution.")
    print("culprit:", culprit_atoms)
    print("solved:", solved_atoms)
    return 1


CURATED = [
    StoryParams(
        setting="hallway",
        detective_name="Maya",
        detective_gender="girl",
        suspect="dog",
        hidden_item="cookie",
    ),
    StoryParams(
        setting="house",
        detective_name="Noah",
        detective_gender="boy",
        suspect="dog",
        hidden_item="toy",
    ),
    StoryParams(
        setting="kitchen",
        detective_name="Lena",
        detective_gender="girl",
        suspect="dog",
        hidden_item="key",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny suspenseful detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--hidden-item", choices=HIDDEN_ITEMS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    hidden = args.hidden_item or rng.choice(list(HIDDEN_ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDER_NAMES[gender])
    return StoryParams(setting=setting, detective_name=name, detective_gender=gender, suspect=suspect, hidden_item=hidden)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.detective_name, params.detective_gender, params.suspect, params.hidden_item)
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
        print(asp_program("#show solved/2.\n#show culprit/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show culprit/1.\n#show solved/2.\n"))
        print("culprit:", sorted(set(asp.atoms(model, "culprit"))))
        print("solved:", sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.detective_name}: {p.setting}, suspect={p.suspect}, item={p.hidden_item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
