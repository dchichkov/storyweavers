#!/usr/bin/env python3
"""
A standalone story world about a tiny society of helpers, a repeated procedure,
a little mystery, and a touch of magic.

The seed image:
---
In a small town, everyone followed a daily procedure to keep the lantern square
tidy. One morning, three silver spoons kept disappearing from the tea table
before the bell rang. The mayor blamed a squirrel, the baker blamed the wind,
and the librarian insisted it had to be magic. The children repeated the same
search route again and again, laughing each time they found only crumbs and
dust. At last, they noticed the missing spoons were not stolen at all: they had
been tucked into the songbook by a forgetful magician who liked to borrow shiny
things for his tricks.

World design:
- A small society with roles, shared routines, and local rules.
- A procedure that can be followed, interrupted, and repaired.
- A mystery that is solved by patient repetition and careful notice.
- Humor from mistaken guesses and social bickering.
- Magic that is real, but ordinary enough to fit the town's life.
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

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

ROLES = ["mayor", "baker", "librarian", "guard", "child", "magician", "scribe"]
PLACES = ["lantern square", "tea hall", "market lane", "library steps", "clockyard"]
OBJECTS = ["spoons", "keys", "chalk", "bells", "buttons", "seals"]
MAGIC_METHODS = ["vanish trick", "glimmer spell", "mirror charm", "floating knot", "sparkle swap"]
MISTAKEN_THEORIES = [
    "a squirrel did it",
    "the wind carried it away",
    "the cat must have taken it",
    "someone was being silly",
    "the moon was playing a joke",
]

HUMOR_BEATS = [
    "Everyone talked at once, which made the mystery feel even funnier.",
    "The guard looked under his hat even though he had already checked it twice.",
    "The baker searched the bread box and found only crumbs and a very confused crumb.",
    "The librarian whispered that books never lie, then sneezed on a bookmark.",
]

REPEAT_PHRASES = [
    "again and again",
    "one more careful time",
    "for the third slow walk",
    "step by step",
]


# ---------------------------------------------------------------------------
# Shared data containers
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noticed": 0.0, "missing": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "amusement": 0.0, "certainty": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "lantern square"
    indoors: bool = False
    routine_name: str = "the morning procedure"


@dataclass
class Procedure:
    name: str
    steps: list[str]
    repeat_count: int
    clue_place: str
    clue_object: str
    magic_method: str
    suspicion: str


@dataclass
class Society:
    name: str
    roles: list[str]
    shared_rule: str


class World:
    def __init__(self, setting: Setting, society: Society, procedure: Procedure) -> None:
        self.setting = setting
        self.society = society
        self.procedure = procedure
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_steps: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_steps.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting, self.society, self.procedure)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story state and causal rules
# ---------------------------------------------------------------------------

def _r_notice(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue_id")
    if not clue:
        return out
    obj = world.get(clue)
    if obj.meters["noticed"] >= THRESHOLD:
        return out
    sig = ("notice", clue)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obj.meters["noticed"] = 1.0
    out.append(f"At last, someone noticed {obj.label} hiding where it should not have been.")
    return out


def _r_repeated_search(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("search_rounds", 0) < world.procedure.repeat_count:
        return out
    if world.facts.get("solution_spoken"):
        return out
    sig = ("solve", world.procedure.clue_object)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["solution_spoken"] = True
    out.append("After the same careful search was repeated one more time, the answer finally clicked.")
    return out


def _r_society_murmur(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("murmur_done"):
        return out
    if world.facts.get("theory_count", 0) < 3:
        return out
    world.facts["murmur_done"] = True
    out.append("The whole little society murmured, because everyone had a different guess.")
    return out


CAUSAL_RULES = [_r_notice, _r_repeated_search, _r_society_murmur]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(place: str, obj: str, method: str) -> bool:
    return place in PLACES and obj in OBJECTS and method in MAGIC_METHODS


def explain_rejection(place: str, obj: str, method: str) -> str:
    return (
        f"(No story: the chosen pieces do not fit this mystery. "
        f"Try a place from {sorted(PLACES)}, an object from {sorted(OBJECTS)}, "
        f"and a magic method from {sorted(MAGIC_METHODS)}.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def opening_line(world: World, hero: Entity, object_ent: Entity) -> str:
    return (
        f"In {world.setting.place}, {hero.label} kept the town's little procedure "
        f"as carefully as a clock keeps time, but {object_ent.label} had gone missing."
    )


def repeated_search_line(round_no: int, phrase: str) -> str:
    return f"They searched {phrase}, following the same route round {round_no}."


def humorous_theory_line(theory: str) -> str:
    return f"First, the grown-ups guessed that {theory}."


def magic_clue_line(method: str, obj: str, place: str) -> str:
    return (
        f"Then the magician laughed and admitted that {method} had not stolen {obj} at all; "
        f"it had only nudged the shiny thing into an unexpected place near {place}."
    )


def resolution_line(hero: Entity, object_ent: Entity) -> str:
    return (
        f"At the end, {hero.label} put {object_ent.label} back where the procedure expected it, "
        f"and the square felt orderly again."
    )


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short mystery story for a child about a town procedure, a missing object, and a magical mistake.",
        f"Tell a gentle story set in {f['place']} where the people argue, search repeatedly, and solve the puzzle.",
        f"Write a humorous story where {f['object_label']} is found after the same search is done again and again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    object_ent: Entity = f["object"]
    qa = [
        QAItem(
            question=f"What was missing from {world.setting.place} at the start of the story?",
            answer=f"{object_ent.label.capitalize()} was missing, and that made the morning procedure feel strange.",
        ),
        QAItem(
            question=f"Who kept guessing about the missing {object_ent.label}?",
            answer=(
                f"The mayor, the baker, the librarian, and the guard all offered guesses, "
                f"which made the mystery funny as well as confusing."
            ),
        ),
        QAItem(
            question=f"What helped solve the mystery in the end?",
            answer=(
                f"Careful repetition helped. The same search was done again and again until "
                f"{hero.label} noticed the clue and the magician admitted the truth."
            ),
        ),
        QAItem(
            question=f"Why did the town laugh before the mystery was solved?",
            answer=(
                f"Because everyone kept making different guesses, and some of those guesses were silly, "
                f"like blaming a squirrel or the wind."
            ),
        ),
    ]
    if f.get("solution_spoken"):
        qa.append(
            QAItem(
                question=f"Where had the magical clue hidden {object_ent.label}?",
                answer=(
                    f"The clue had tucked {object_ent.label} near {f['place_detail']}, "
                    f"after a magical trick accidentally moved it there."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a procedure?",
            answer=(
                "A procedure is a set of steps people follow in the same order so a job can be done "
                "carefully and safely."
            ),
        ),
        QAItem(
            question="What is a society?",
            answer=(
                "A society is a group of people who live together and share rules, jobs, and daily routines."
            ),
        ),
        QAItem(
            question="Why can repetition help when something is missing?",
            answer=(
                "Repetition helps because doing the search again can reveal a detail that was easy to miss the first time."
            ),
        ),
        QAItem(
            question="Why do people laugh in a funny mystery?",
            answer=(
                "People laugh when guesses are surprising or silly, especially when everyone is trying hard to be serious."
            ),
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the chosen pieces belong to the registries.
valid_story(P,O,M) :- place(P), object(O), magic(M), gate(P,O,M).

% The mystery becomes solvable when the object is noticed after repeated search.
solved(P,O) :- valid_story(P,O,_), repeated_search(P,O), noticed(O).

% Humor emerges when at least three mistaken theories are spoken.
funny(P,O) :- valid_story(P,O,_), theory_count(P,O,N), N >= 3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for m in MAGIC_METHODS:
        lines.append(asp.fact("magic", m))
    for p in PLACES:
        for o in OBJECTS:
            for m in MAGIC_METHODS:
                if valid_story(p, o, m):
                    lines.append(asp.fact("gate", p, o, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    clingo_set = set(asp_valid_stories())
    python_set = {
        (p, o, m)
        for p in PLACES
        for o in OBJECTS
        for m in MAGIC_METHODS
        if valid_story(p, o, m)
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_story() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_story():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story world generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    object: str
    magic: str
    hero_name: str
    hero_role: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    setting = Setting(place=params.place, indoors=False, routine_name="the morning procedure")
    society = Society(
        name="lantern town",
        roles=["mayor", "baker", "librarian", "guard", "child", "magician"],
        shared_rule="everyone repeats the town procedure before breakfast",
    )
    procedure = Procedure(
        name="missing-object procedure",
        steps=["count", "search", "guess", "search again", "reveal"],
        repeat_count=3,
        clue_place="the songbook",
        clue_object=params.object,
        magic_method=params.magic,
        suspicion="something magical happened",
    )
    world = World(setting, society, procedure)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="child",
        label=params.hero_name,
    ))
    hero.memes["curiosity"] = 1.0

    mayor = world.add(Entity(id="mayor", kind="character", type="mayor", label="the mayor"))
    baker = world.add(Entity(id="baker", kind="character", type="baker", label="the baker"))
    librarian = world.add(Entity(id="librarian", kind="character", type="librarian", label="the librarian"))
    guard = world.add(Entity(id="guard", kind="character", type="guard", label="the guard"))
    magician = world.add(Entity(id="magician", kind="character", type="magician", label="the magician"))

    obj = world.add(Entity(
        id="object",
        kind="thing",
        type=params.object,
        label=params.object,
        phrase=f"the missing {params.object}",
        owner="tea hall",
        keeper="mayor",
        location=params.place,
        plural=params.object.endswith("s"),
    ))
    obj.meters["missing"] = 1.0

    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="songbook",
        label="the songbook",
        phrase="the magician's songbook",
        owner="magician",
        location="library steps",
    ))

    world.facts.update(
        hero=hero,
        object=obj,
        clue_id=clue.id,
        place=params.place,
        object_label=params.object,
        place_detail=world.procedure.clue_place,
    )
    return world


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    obj: Entity = world.facts["object"]
    magician: Entity = world.get("magician")
    mayor = world.get("mayor")
    baker = world.get("baker")
    librarian = world.get("librarian")
    guard = world.get("guard")

    world.say(opening_line(world, hero, obj))
    world.say(
        f"The town liked its {world.society.shared_rule}, so everyone gathered in {world.setting.place} to check the steps."
    )
    world.say(f"Then the {obj.label} was gone, and the missing space looked oddly bright.")

    world.para()
    world.say(f"The mayor said that {random.choice(MISTAKEN_THEORIES)}.")
    world.say(f"The baker said that {random.choice(MISTAKEN_THEORIES)}.")
    world.say(f"The librarian said that {random.choice(MISTAKEN_THEORIES)}.")
    world.say(f"The guard said that {random.choice(MISTAKEN_THEORIES)}.")
    world.facts["theory_count"] = 4
    world.facts["murmur_done"] = False
    propagate(world)

    world.para()
    for round_no in range(1, world.procedure.repeat_count + 1):
        phrase = REPEAT_PHRASES[(round_no - 1) % len(REPEAT_PHRASES)]
        world.say(repeated_search_line(round_no, phrase))
        world.facts["search_rounds"] = round_no
    world.say(random.choice(HUMOR_BEATS))
    world.say(f"{hero.label} stopped, looked twice, and noticed that the clue felt too tidy for a random mess.")
    propagate(world)

    world.para()
    world.say(
        f"At last, the magician scratched his head and admitted that {world.procedure.magic_method} had been part of a joke."
    )
    world.say(
        magic_clue_line(world.procedure.magic_method, obj.label, world.procedure.clue_place)
    )
    world.say(
        f"He had tucked the {obj.label} into {world.procedure.clue_place} while practicing a performance."
    )
    world.say(resolution_line(hero, obj))

    obj.meters["missing"] = 0.0
    obj.meters["clean"] = 1.0
    hero.memes["amusement"] += 1.0
    mayor.memes["certainty"] += 1.0
    baker.memes["amusement"] += 1.0
    librarian.memes["curiosity"] += 1.0
    guard.memes["certainty"] += 1.0
    magician.memes["worry"] += 1.0

    world.facts["solution_spoken"] = True


def generation_story(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="lantern square", object="spoons", magic="glimmer spell", hero_name="Mina", hero_role="child"),
    StoryParams(place="tea hall", object="keys", magic="floating knot", hero_name="Toby", hero_role="child"),
    StoryParams(place="library steps", object="chalk", magic="mirror charm", hero_name="Nia", hero_role="child"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery story world with procedure, society, humor, magic, and repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--magic", choices=MAGIC_METHODS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["child"])
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
    place = args.place or rng.choice(PLACES)
    obj = args.object_ or rng.choice(OBJECTS)
    magic = args.magic or rng.choice(MAGIC_METHODS)
    if not valid_story(place, obj, magic):
        raise StoryError(explain_rejection(place, obj, magic))
    name = args.name or rng.choice(["Mina", "Toby", "Nia", "Lio", "Pia", "Rae"])
    role = args.role or "child"
    return StoryParams(place=place, object=obj, magic=magic, hero_name=name, hero_role=role)


def generate(params: StoryParams) -> StorySample:
    return generation_story(params)


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
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (place, object, magic) combos:\n")
        for place, obj, magic in combos:
            print(f"  {place:14} {obj:10} {magic}")
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
            header = f"### {p.hero_name}: {p.object} at {p.place} ({p.magic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
