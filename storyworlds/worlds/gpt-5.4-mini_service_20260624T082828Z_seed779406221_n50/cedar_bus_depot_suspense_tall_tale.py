#!/usr/bin/env python3
"""
Storyworld: cedar bus depot suspense tall tale.

A small, classical simulation about a bus depot, a cedar box, a waiting child,
and a suspenseful choice that ends with a reveal.

The premise:
- A child arrives at a bus depot with a cherished cedar keepsake.
- A tall-tale style suspense builds around a missing ticket, a ticking clock,
  and a stranger who might be helping or hiding something.
- The resolution proves what changed in the world, not just in the wording.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    at_risk_from: str
    region: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueCfg:
    id: str
    label: str
    phrase: str
    explains: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    object: str
    clue: str
    name: str
    gender: str
    relative: str
    trait: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    tick: int = 0

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.tick = self.tick
        return clone


SETTINGS = {
    "bus depot": Place(id="bus_depot", label="the bus depot", indoors=True, tags={"bus", "depot", "suspense"}),
}

OBJECTS = {
    "cedar_box": ObjectCfg(
        id="cedar_box",
        label="cedar box",
        phrase="a small cedar box tied with blue twine",
        at_risk_from="lost",
        region="hands",
        tags={"cedar"},
    ),
    "ticket": ObjectCfg(
        id="ticket",
        label="ticket",
        phrase="a bus ticket with a bright red stripe",
        at_risk_from="missing",
        region="pocket",
        tags={"bus"},
    ),
    "lantern": ObjectCfg(
        id="lantern",
        label="lantern",
        phrase="a brass lantern",
        at_risk_from="dark",
        region="hands",
        tags={"suspense"},
    ),
}

CLUES = {
    "cedar_note": ClueCfg(
        id="cedar_note",
        label="cedar note",
        phrase="a cedar-scented note tucked under the twine",
        explains="the box was meant for the station clerk",
        tags={"cedar"},
    ),
    "lost_ticket": ClueCfg(
        id="lost_ticket",
        label="lost ticket",
        phrase="a ticket stub under the bench",
        explains="the child had dropped the ticket while hurrying",
        tags={"bus"},
    ),
    "lantern_help": ClueCfg(
        id="lantern_help",
        label="lantern help",
        phrase="the lantern light catching a silver corner",
        explains="the ticket had slid behind the timetable board",
        tags={"suspense"},
    ),
}

NAMES = ["Mabel", "June", "Nora", "Iris", "Bea", "Tom", "Owen", "Finn"]
TRAITS = ["brave", "curious", "stubborn", "bright-eyed", "steady", "bold"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cedar bus depot suspense tall tale.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--relative", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
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
    place = args.place or "bus depot"
    obj = args.object_name or "cedar_box"
    clue = args.clue or rng.choice(["cedar_note", "lost_ticket", "lantern_help"])
    gender = args.gender or rng.choice(["girl", "boy"])
    relative = args.relative or rng.choice(["mother", "father", "aunt", "uncle"])
    name = args.name or rng.choice([n for n in NAMES if (gender == "girl") == (n in {"Mabel", "June", "Nora", "Iris", "Bea"})] or NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, object=obj, clue=clue, name=name, gender=gender, relative=relative, trait=trait)


def _pronoun_word(gender: str) -> str:
    return "she" if gender == "girl" else "he"


def _poss_word(gender: str) -> str:
    return "her" if gender == "girl" else "his"


def _obj_word(gender: str) -> str:
    return "her" if gender == "girl" else "him"


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    relative = world.add(Entity(id="relative", kind="character", type=params.relative, label=f"the {params.relative}"))
    obj_cfg = OBJECTS[params.object]
    clue_cfg = CLUES[params.clue]
    cedar = world.add(Entity(id="cedar_box", type="box", label=obj_cfg.label, phrase=obj_cfg.phrase, owner=child.id, meters={"safe": 1.0}, memes={"hope": 1.0}))
    ticket = world.add(Entity(id="ticket", type="ticket", label="ticket", phrase=OBJECTS["ticket"].phrase, owner=child.id, meters={"found": 0.0}, memes={"worry": 0.0}))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern", phrase=OBJECTS["lantern"].phrase, owner="clerk", meters={"lit": 0.0}))
    world.facts.update(child=child, relative=relative, cedar=cedar, ticket=ticket, lantern=lantern, clue=clue_cfg, obj_cfg=obj_cfg, place=place)

    child.memes["hope"] = 1.0
    child.memes["worry"] = 0.0
    world.say(f"{child.id} came to {place.label} with a cedar box tucked tight in { _poss_word(params.gender)} hands.")
    world.say(f"{_pronoun_word(params.gender).capitalize()} was a {params.trait} little {params.gender} who could hear a whisper from a mile away.")
    world.say(f"{_pronoun_word(params.gender).capitalize()} needed to meet {relative.label} before the last bus sighed and rolled out.")

    world.para()
    world.say(f"But the bus depot had a long, creaky way of making even a simple minute feel like a thunderstorm in a teacup.")
    child.memes["worry"] += 1.0
    ticket.meters["found"] = 0.0
    world.say(f"{child.id} patted {_poss_word(params.gender)} pocket. No ticket.")
    world.say(f"The cedar box was still safe, but the clock over the window ticked like a tiny horse galloping through the rafters.")

    world.para()
    if clue_cfg.id == "cedar_note":
        child.memes["worry"] += 1.0
        world.say(f"Then a cedar-scented note peeked from under the blue twine: {clue_cfg.phrase}.")
        world.say(f"It said {clue_cfg.explains}, and that made the little mystery grow taller than a barn on stilts.")
        ticket.meters["found"] += 0.5
    elif clue_cfg.id == "lost_ticket":
        world.say(f"Under a bench, {child.id} spotted {clue_cfg.phrase}.")
        world.say(f"The stub matched the missing place where a ticket should be, and the worry jumped like a frog on a drum.")
        ticket.meters["found"] += 1.0
        child.memes["worry"] -= 0.5
    else:
        child.memes["worry"] += 0.5
        world.say(f"{relative.label} lifted a brass lantern, and {clue_cfg.phrase} flashed across the floorboards.")
        world.say(f"It showed that {clue_cfg.explains}, right where the depot was darkest and the suspense was thick as molasses.")
        lantern.meters["lit"] = 1.0
        ticket.meters["found"] += 1.0

    world.para()
    if ticket.meters.get("found", 0.0) < THRESHOLD:
        world.say(f"{child.id} searched behind the timetable board, under the seat, and beside the sandwich stand.")
        world.say(f"At last, {relative.label} came close and asked, “What is it, kid?”")
        world.say(f"{child.id} held up the cedar box. Inside, hidden under the lining, was the bus ticket all along.")
        ticket.meters["found"] = 1.0
        child.memes["worry"] = 0.0
        child.memes["relief"] = 1.0
        world.say(f"The depot seemed to breathe out, and even the ceiling fan looked relieved.")
    else:
        world.say(f"{child.id} found the ticket before the fear could grow teeth.")
        child.memes["relief"] = 1.0
        child.memes["worry"] = 0.0

    world.say(f"{relative.label} laughed a great, rolling laugh and said the cedar box had been the safest hiding place in town.")
    world.say(f"Together they boarded the last bus with the cedar box in hand and the ticket where it belonged, while the depot lights blinked like patient stars.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a short tall-tale style story for a child named {child.id} at a bus depot that includes the word "cedar".',
        f"Tell a suspenseful story where {child.id} worries about a missing ticket, but a cedar box and a helpful relative lead to a happy ending.",
        "Write a child-facing story set in a bus depot where a small mystery is solved before the last bus leaves.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, relative, clue = f["child"], f["relative"], f["clue"]
    return [
        QAItem(
            question=f"Where did {child.id} go with the cedar box?",
            answer=f"{child.id} went to the bus depot with a cedar box tucked in {child.pronoun('possessive')} hands.",
        ),
        QAItem(
            question=f"What was the big worry in the story?",
            answer=f"The big worry was a missing bus ticket, which made the wait feel suspenseful at the depot.",
        ),
        QAItem(
            question=f"How did {child.id} and {relative.label} solve the mystery?",
            answer=(
                "They found the ticket by following the clue in the story. "
                "The cedar box helped reveal where the ticket had been hidden, and then they could board the bus."
            ),
        ),
        QAItem(
            question=f"What was special about the clue?",
            answer=f"The clue was {clue.phrase}, and it pointed to what was really going on in the depot.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cedar?",
            answer="Cedar is a kind of tree that has fragrant wood often used for boxes, chests, and closets.",
        ),
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses stop, rest, and wait for people to ride them.",
        ),
        QAItem(
            question="What does suspense mean?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something important is not yet known.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(bus_depot).
tag(bus_depot,bus).
tag(bus_depot,depot).
tag(bus_depot,suspense).

object(cedar_box).
object(ticket).
object(lantern).

valid_story(P,O,C) :- place(P), object(O), object(C).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "bus_depot")]
    for obj in OBJECTS:
        lines.append(asp.fact("object", obj))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("bus_depot", o, c) for o in OBJECTS for c in CLUES}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    if py - cl:
        print(" only in Python:", sorted(py - cl))
    return 1


def explain_rejection() -> str:
    return "(No story: this tiny world only supports the bus depot, cedar box, and suspenseful ticket mystery.)"


def valid_combo(params: StoryParams) -> bool:
    return params.place == "bus depot" and params.object in OBJECTS and params.clue in CLUES


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params):
        raise StoryError(explain_rejection())
    world = tell(params)
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


CURATED = [
    StoryParams(place="bus depot", object="cedar_box", clue="cedar_note", name="Mabel", gender="girl", relative="aunt", trait="brave"),
    StoryParams(place="bus depot", object="cedar_box", clue="lost_ticket", name="Tom", gender="boy", relative="father", trait="curious"),
    StoryParams(place="bus depot", object="cedar_box", clue="lantern_help", name="Iris", gender="girl", relative="mother", trait="steady"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or "bus depot",
        object=args.object_name or "cedar_box",
        clue=args.clue or rng.choice(list(CLUES)),
        name=args.name or rng.choice(NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        relative=args.relative or rng.choice(["mother", "father", "aunt", "uncle"]),
        trait=rng.choice(TRAITS),
    )


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
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name}: cedar suspense at the bus depot"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
