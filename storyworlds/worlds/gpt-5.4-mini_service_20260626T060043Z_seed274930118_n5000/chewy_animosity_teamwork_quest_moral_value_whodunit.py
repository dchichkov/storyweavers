#!/usr/bin/env python3
"""
A tiny whodunit-style story world about a missing chewy treat, a growing
animosity, and a teamwork quest that turns suspicion into a moral lesson.

The premise is intentionally small and classical: one beloved chewy dessert
goes missing from a kitchen, the characters investigate clues, and the story
ends with a fair reveal plus a repaired relationship.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    clue: str
    warmth: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    alibi: str
    clue_left: str
    can_hold: bool = True


@dataclass
class StoryParams:
    room: str
    culprit: str
    dessert: str
    detective: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ROOMS = {
    "kitchen": Room("the kitchen", "a dusting of crumbs near the counter", "warm"),
    "pantry": Room("the pantry", "a sticky trail by the flour tin", "quiet"),
    "dining_room": Room("the dining room", "a tiny napkin with a corner folded twice", "bright"),
}

SUSPECTS = {
    "brother": Suspect(
        id="brother",
        label="older brother",
        type="boy",
        motive="he had been eyeing the last treat all afternoon",
        alibi="he said he was stacking cups in the next room",
        clue_left="a floury thumbprint on the table",
    ),
    "sister": Suspect(
        id="sister",
        label="little sister",
        type="girl",
        motive="she wanted something sweet before supper",
        alibi="she said she was coloring at the window",
        clue_left="a pink crayon tucked behind a chair",
    ),
    "cat": Suspect(
        id="cat",
        label="the cat",
        type="thing",
        motive="it liked warm crumbs and anything buttery",
        alibi="it could not speak, only blink slowly",
        clue_left="paw prints on the floor",
    ),
    "parent": Suspect(
        id="parent",
        label="the parent",
        type="mother",
        motive="she had hidden the dessert to cool it",
        alibi="she remembered putting it on the top shelf",
        clue_left="a clean plate under a tea towel",
        can_hold=True,
    ),
}

DESSERTS = {
    "cookie": {
        "label": "cookie",
        "phrase": "one chewy oatmeal cookie",
        "taste": "chewy and sweet",
        "crumbly": False,
    },
    "bar": {
        "label": "bar",
        "phrase": "a chewy lemon bar",
        "taste": "soft in the middle with a bright, sweet edge",
        "crumbly": False,
    },
    "brownie": {
        "label": "brownie",
        "phrase": "one chewy brownie square",
        "taste": "fudgy and chewy",
        "crumbly": False,
    },
}

NAMES = ["Mia", "Leo", "Nina", "Ben", "Ava", "Noah", "Lena", "Eli"]
HELPER_NAMES = ["Pip", "June", "Tess", "Owen", "Ada", "Iris"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A room clue can point to a suspect if their clue matches the room.
possible(Culprit) :- clue(Culprit, _).

% The real culprit is the one whose motive and clue fit the scene.
real_culprit(Culprit) :- motive(Culprit, _), clue(Culprit, _).

% Teamwork resolves the case if the detective and helper both contribute.
teamwork_case :- contributed(detective), contributed(helper).

% Moral value is learned when the culprit confesses and the dessert is shared.
moral_value :- confess(Culprit), share_after(Culprit).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        lines.append(asp.fact("room_clue", rid, room.clue))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("motive", sid, s.motive))
        lines.append(asp.fact("clue", sid, s.clue_left))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show suspect/1."))
    asp_suspects = {a[0] for a in asp.atoms(model, "suspect")}
    py_suspects = set(SUSPECTS.keys())
    if asp_suspects == py_suspects:
        print(f"OK: clingo facts cover {len(py_suspects)} suspects.")
        return 0
    print("MISMATCH between ASP and Python suspect sets.")
    print("only in asp:", sorted(asp_suspects - py_suspects))
    print("only in python:", sorted(py_suspects - asp_suspects))
    return 1


# ---------------------------------------------------------------------------
# Behavior and narrative helpers
# ---------------------------------------------------------------------------

def suspiciousness(world: World, suspect: Entity) -> float:
    return suspect.memes.get("suspicion", 0.0) + suspect.meters.get("crumbs", 0.0)


def pick_culprit(world: World, culprit_id: str) -> Entity:
    return world.get(culprit_id)


def investigate(world: World, detective: Entity, helper: Entity, culprit: Entity, dessert: Entity) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"On a quiet evening in {world.room.name}, {dessert.label} vanished from the counter."
    )
    world.say(
        f"{detective.id} narrowed {detective.pronoun('possessive')} eyes and said the case smelled of crumbs, "
        f"while {helper.id} looked for clues with careful hands."
    )


def assign_animosity(world: World, culprit: Entity, detective: Entity, helper: Entity) -> None:
    culprit.memes["animosity"] += 1
    detective.memes["doubt"] += 1
    helper.memes["doubt"] += 1
    world.say(
        f"{culprit.id} grew prickly under the questions, and a little animosity settled between the suspect and the investigators."
    )


def search_room(world: World, detective: Entity, helper: Entity, culprit: Entity) -> None:
    detective.meters["search"] += 1
    helper.meters["search"] += 1
    world.say(
        f"The pair followed the trail: first the crumb-dust near the counter, then the clue in the corner."
    )
    world.say(
        f"{helper.id} spotted {culprit.memes.get('clue', 0) and 'something odd' or 'a clue'} and {detective.id} compared it to the suspects' stories."
    )


def reveal(world: World, detective: Entity, helper: Entity, culprit: Entity, dessert: Entity) -> None:
    culprit.memes["guilt"] += 1
    culprit.memes["animosity"] = 0.0
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"At last, the clue fit: {culprit.id} had tucked {dessert.label} away to keep it safe, then forgotten to say so."
    )
    world.say(
        f"{detective.id} stepped back instead of scolding, and {helper.id} asked for the truth in a kinder voice."
    )


def teamwork(world: World, detective: Entity, helper: Entity, culprit: Entity, dessert: Entity) -> None:
    detective.memes["trust"] += 1
    helper.memes["trust"] += 1
    culprit.memes["trust"] += 1
    world.say(
        f"The three of them worked together to return the {dessert.label} to the table, cut it fairly, and share the first sweet bite."
    )
    world.say(
        f"{culprit.id} apologized, {detective.id} forgave {culprit.pronoun('object')}, and everyone agreed that solving a mystery was better when it ended kindly."
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(room: Room, culprit_id: str, dessert_id: str, detective_name: str, helper_name: str) -> World:
    world = World(room)

    detective = world.add(Entity(
        id=detective_name, kind="character", type="girl" if detective_name in {"Mia", "Ava", "Nina", "Lena"} else "boy",
        meters={"search": 0.0}, memes={"curiosity": 0.0, "doubt": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type="girl" if helper_name in {"June", "Tess", "Ada", "Iris"} else "boy",
        meters={"search": 0.0}, memes={"curiosity": 0.0, "doubt": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    culprit_spec = SUSPECTS[culprit_id]
    culprit = world.add(Entity(
        id=culprit_id, kind="character", type=culprit_spec.type,
        meters={"crumbs": 1.0}, memes={"animosity": 0.0, "guilt": 0.0, "trust": 0.0},
    ))
    dessert_spec = DESSERTS[dessert_id]
    dessert = world.add(Entity(
        id="dessert", kind="thing", type=dessert_spec["label"], label=dessert_spec["label"],
        phrase=dessert_spec["phrase"], owner=culprit.id,
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        culprit=culprit,
        dessert=dessert,
        culprit_spec=culprit_spec,
        room=room,
    )

    investigate(world, detective, helper, culprit, dessert)
    world.para()
    assign_animosity(world, culprit, detective, helper)
    search_room(world, detective, helper, culprit)
    world.para()
    reveal(world, detective, helper, culprit, dessert)
    teamwork(world, detective, helper, culprit, dessert)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA and prose generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    culprit = f["culprit_spec"]
    dessert = f["dessert"]
    return [
        f'Write a short whodunit for a young child about a missing {dessert.label} and a clue in {world.room.name}.',
        f"Tell a mystery story where {f['detective'].id} and {f['helper'].id} solve a case with teamwork, then learn a moral value.",
        f'Write a simple story that includes the word "chewy" and ends with a fair answer instead of a blame game.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    culprit = f["culprit_spec"]
    dessert = f["dessert"]
    detective = f["detective"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What vanished in {world.room.name}?",
            answer=f"A {dessert.phrase} vanished, which made the room feel like the start of a mystery.",
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"{detective.id} and {helper.id} helped solve it by looking at clues together instead of arguing.",
        ),
        QAItem(
            question=f"Why was there animosity during the search?",
            answer=f"There was a little animosity because the suspect was tense under questions and the others were unsure who had moved the dessert.",
        ),
        QAItem(
            question=f"What made the story end kindly?",
            answer=f"It ended kindly because the truth came out, the dessert was shared fairly, and everyone chose teamwork over blame.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together and help each other solve a problem or finish a job.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good lesson about how to treat other people, like being honest, fair, or kind.",
        ),
        QAItem(
            question="What does chewy mean?",
            answer="Chewy means food is soft and a little tough to bite through, so you have to chew it more.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"{e.id} ({e.type}): " + ", ".join(parts))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(room="kitchen", culprit="brother", dessert="cookie", detective="Mia", helper="Pip"),
    StoryParams(room="pantry", culprit="sister", dessert="bar", detective="Leo", helper="June"),
    StoryParams(room="dining_room", culprit="parent", dessert="brownie", detective="Nina", helper="Tess"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small chewy whodunit story world.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--dessert", choices=DESSERTS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
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
    room = args.room or rng.choice(list(ROOMS))
    culprit = args.culprit or rng.choice(list(SUSPECTS))
    dessert = args.dessert or rng.choice(list(DESSERTS))
    detective = args.detective or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != detective])
    if culprit == "parent" and room == "kitchen" and dessert == "cookie" and args.helper is None:
        pass
    return StoryParams(room=room, culprit=culprit, dessert=dessert, detective=detective, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], params.culprit, params.dessert, params.detective, params.helper)
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


def asp_show_program() -> str:
    return asp_program("#show suspect/1.\n#show room/1.\n#show room_clue/2.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show suspect/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show suspect/1."))
        suspects = sorted(set(asp.atoms(model, "suspect")))
        print(f"{len(suspects)} suspects encoded in ASP.")
        for s in suspects:
            print(" ", s[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective} investigates {p.culprit} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
