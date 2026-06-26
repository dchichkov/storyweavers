#!/usr/bin/env python3
"""
A bedtime-story world about a small mystery to solve, a careful lesson learned,
and one important ounce of something that matters.

Premise:
- A child helper and a gentle grown-up are preparing a cozy bedtime treat.
- One tiny ounce is missing from the recipe.
- The child must solve the mystery by noticing clues, asking questions, and
  learning that careful measuring keeps everyone happy.

The simulated world tracks:
- meters: quantities, location clues, and whether the treat is complete
- memes: worry, curiosity, relief, pride, and kindness

The output story is authored from simulated state rather than from a frozen
template, and the turn/resolution depends on the mystery being solved.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    cozy_detail: str


@dataclass
class Mystery:
    id: str
    missing_label: str
    unit: str
    amount: float
    clue_room: str
    clue_item: str
    lesson: str


@dataclass
class StoryParams:
    room: str
    mystery: str
    hero_name: str
    hero_type: str
    grownup_type: str
    seed: Optional[int] = None


ROOMS = {
    "kitchen": Room(name="the kitchen", cozy_detail="a warm lamp glowed over the table"),
    "pantry": Room(name="the pantry", cozy_detail="the shelves smelled like oats and cinnamon"),
    "bedroom": Room(name="the bedroom", cozy_detail="the quilt was soft and the moonlight was pale"),
}

MYSTERIES = {
    "honey": Mystery(
        id="honey",
        missing_label="a tiny ounce of honey",
        unit="ounce",
        amount=1.0,
        clue_room="pantry",
        clue_item="sticky spoon",
        lesson="careful measuring helps a recipe turn out right",
    ),
    "cocoa": Mystery(
        id="cocoa",
        missing_label="an ounce of cocoa",
        unit="ounce",
        amount=1.0,
        clue_room="kitchen",
        clue_item="brown dust on the counter",
        lesson="good helpers check the bowl before they guess",
    ),
    "butter": Mystery(
        id="butter",
        missing_label="an ounce of butter",
        unit="ounce",
        amount=1.0,
        clue_room="pantry",
        clue_item="a butter wrapper",
        lesson="small things matter when you are baking with love",
    ),
}

NAMES = ["Mina", "Leo", "Nora", "Toby", "June", "Eli", "Luna", "Ivy"]
TRAITS = ["curious", "gentle", "careful", "sleepy", "brave", "patient"]


class World:
    def __init__(self, room: Room, mystery: Mystery) -> None:
        self.room = room
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.room, self.mystery)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    child = world.entities["child"]
    bowl = world.entities["bowl"]
    if child.memes.get("curiosity", 0.0) >= THRESHOLD and "notice_clue" not in world.fired:
        world.fired.add("notice_clue")
        child.memes["confidence"] = child.memes.get("confidence", 0.0) + 1
        out.append(f"{child.id} noticed the little clue on the table.")
    if bowl.meters.get("missing", 0.0) >= THRESHOLD and "solve_mystery" not in world.fired:
        world.fired.add("solve_mystery")
        child.memes["relief"] = child.memes.get("relief", 0.0) + 1
        out.append("The missing ounce was found.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    mystery = MYSTERIES[params.mystery]
    world = World(room, mystery)

    child = world.add(Entity(
        id="child", kind="character", type=params.hero_type, label=params.hero_name,
        meters={"kindness": 1.0}, memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0},
        location=room.name,
    ))
    grownup = world.add(Entity(
        id="grownup", kind="character", type=params.grownup_type, label="grown-up",
        meters={"kindness": 1.0}, memes={"calm": 1.0, "worry": 0.0},
        location=room.name,
    ))
    bowl = world.add(Entity(
        id="bowl", type="bowl", label="mixing bowl",
        meters={"missing": mystery.amount, "fullness": 0.0}, location=room.name,
    ))
    spoon = world.add(Entity(
        id="spoon", type="spoon", label="small spoon",
        meters={"sticky": 0.0}, location=mystery.clue_room,
    ))
    clue = world.add(Entity(
        id="clue", type="clue", label=mystery.clue_item,
        meters={"noticed": 0.0}, location=mystery.clue_room,
    ))

    world.facts.update(child=child, grownup=grownup, bowl=bowl, spoon=spoon, clue=clue)
    return world


def tell(world: World) -> None:
    child = world.facts["child"]
    grownup = world.facts["grownup"]
    bowl = world.facts["bowl"]
    clue = world.facts["clue"]
    mystery = world.mystery

    world.say(f"In {world.room.name}, {world.room.cozy_detail}.")
    world.say(f"{child.label} was a {next((t for t in ['curious','gentle','careful','sleepy','brave','patient'] if t), 'curious')} little {child.type} who loved bedtime treats.")
    world.say(f"{grownup.label.capitalize()} smiled and said, “We need {mystery.missing_label} for the recipe.”")
    world.say(f"{child.label} peered into the bowl, where the mixture waited with one tiny gap.")

    world.para()
    child.memes["worry"] += 1
    world.say(f"“Where did it go?” {child.label} whispered.")
    world.say(f"“Let’s solve the mystery together,” said the grown-up. “Look for the clue, and tell me what you notice.”")
    world.say(f"{child.label} tiptoed toward {world.entities['spoon'].location}, because the shiny spoon had something sticky on it.")
    world.facts["clue_found"] = True
    clue.meters["noticed"] = 1.0
    world.facts["clue_item"] = clue.label
    propagate(world, narrate=True)

    world.para()
    if mystery.clue_room == "pantry":
        world.say(f"{child.label} said, “I think the spoon touched the pantry jar.”")
    else:
        world.say(f"{child.label} said, “I think the counter holds the answer.”")
    world.say(f"The grown-up nodded. “You found it. One ounce was used early, and that is why the bowl looked shy.”")
    bowl.meters["missing"] = 0.0
    bowl.meters["fullness"] = 1.0
    child.memes["joy"] += 1
    child.memes["confidence"] = child.memes.get("confidence", 0.0) + 1
    grownup.memes["worry"] = 0.0
    grownup.memes["calm"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"{grownup.label.capitalize()} stirred the bowl and said, “You helped me find the missing ounce.”")
    world.say(f"{child.label} smiled. “So the lesson is {mystery.lesson}.”")
    world.say(f"“That’s right,” said the grown-up. “And now we can bake and rest easy.”")
    world.say(f"By the time the moon looked in the window, the recipe was complete and the little mystery was put to bed.")
    world.facts["solved"] = True


def generation_prompts(world: World) -> list[str]:
    m = world.mystery
    c = world.facts["child"]
    return [
        f'Write a bedtime story about a child who finds a missing {m.unit} in the kitchen.',
        f"Tell a gentle mystery where {c.label} asks questions, follows a clue, and learns a lesson about measuring.",
        f'Create a cozy story with dialogue that includes "{m.missing_label}" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    grownup = world.facts["grownup"]
    mystery = world.mystery
    room = world.room.name
    return [
        QAItem(
            question=f"What mystery did {child.label} help solve in {room}?",
            answer=f"{child.label} helped solve the mystery of {mystery.missing_label}.",
        ),
        QAItem(
            question=f"What did {child.label} notice that helped solve the problem?",
            answer=f"{child.label} noticed {world.facts['clue_item']} and realized it pointed to the missing ounce.",
        ),
        QAItem(
            question="What lesson was learned by the end?",
            answer=f"The lesson was that {mystery.lesson}.",
        ),
        QAItem(
            question=f"How did the grown-up and {child.label} feel at the end?",
            answer=f"They felt calm and happy because the recipe was complete and the mystery was solved together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ounce?",
            answer="An ounce is a small unit used to measure ingredients or other small amounts.",
        ),
        QAItem(
            question="Why do people measure ingredients carefully?",
            answer="People measure ingredients carefully so a recipe tastes right and comes out the way they hoped.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first, so people look for clues to solve it.",
        ),
        QAItem(
            question="Why is dialogue helpful in a story?",
            answer="Dialogue lets characters speak to each other, which makes their feelings and ideas easy to follow.",
        ),
        QAItem(
            question="What makes a bedtime story feel cozy?",
            answer="A bedtime story feels cozy when it has gentle language, a calm ending, and a safe, warm feeling.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} loc={e.location} meters={meters} memes={memes}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(r, m) for r in ROOMS for m in MYSTERIES]


def explain_rejection(room: str, mystery: str) -> str:
    return f"(No story: the room '{room}' and mystery '{mystery}' do not form a valid bedtime scene.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: an ounce-sized mystery to solve.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(ROOMS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    grownup_type = args.grownup or rng.choice(["mother", "father"])
    hero_name = args.name or rng.choice(NAMES)
    return StoryParams(room=room, mystery=mystery, hero_name=hero_name, hero_type=hero_type, grownup_type=grownup_type)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


ASP_RULES = r"""
room(kitchen;pantry;bedroom).
mystery(honey;cocoa;butter).

valid(R,M) :- room(R), mystery(M).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [asp.fact("room", r) for r in ROOMS] +
        [asp.fact("mystery", m) for m in MYSTERIES]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(room="kitchen", mystery="honey", hero_name="Mina", hero_type="girl", grownup_type="mother"),
    StoryParams(room="pantry", mystery="cocoa", hero_name="Leo", hero_type="boy", grownup_type="father"),
    StoryParams(room="bedroom", mystery="butter", hero_name="Luna", hero_type="girl", grownup_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for r, m in asp_valid_combos():
            print(r, m)
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            if args.room and args.mystery:
                pass
            if (params.room, params.mystery) not in valid_combos():
                raise StoryError(explain_rejection(params.room, params.mystery))
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
