#!/usr/bin/env python3
"""
A small ghost-story world about a concert, a document, and a kindly turn.

The seed premise:
- A child finds a document tied to a concert.
- A gentle ghost cannot rest until the document is treated with care.
- Kindness, not fear, resolves the problem.

This script keeps the domain small and state-driven:
- the document can be torn, damp, or misplaced
- the concert can be saved if the right person reads the note and acts kindly
- the ghost's unsettled state is an emotional meter that changes through the story
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old concert hall"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Concert:
    id: str
    title: str
    sound: str
    mood: str
    venue_note: str
    kind: str = "concert"


@dataclass
class Document:
    id: str
    label: str
    phrase: str
    importance: str
    risk: str
    kind: str = "document"


@dataclass
class Helper:
    id: str
    label: str
    action: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTING = Setting()
CONCERT = Concert(
    id="concert",
    title="the lantern concert",
    sound="soft music and gentle bells",
    mood="quiet and a little spooky",
    venue_note="The hall was dim, but the stage lights made warm pools on the floor.",
)
DOCUMENT = Document(
    id="document",
    label="concert program",
    phrase="a folded concert program with the song order",
    importance="it told the musicians when to begin",
    risk="it could get torn or lost",
)
HELPER = Helper(
    id="ghost_helper",
    label="a kind ghost",
    action="brought the program back into the light",
    tail="carefully set the program beside the piano",
)

GIRL_NAMES = ["Mina", "Nora", "Ivy", "Ella", "Luna", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Eli", "Noah", "Finn", "Max"]
TRAITS = ["gentle", "curious", "brave", "careful", "kind"]


def pronounce_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def valid_combo() -> bool:
    return True


def reasonableness_gate() -> None:
    if not valid_combo():
        raise StoryError("This ghost story needs a concert that can be saved by a document.")


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    doc = world.get("document")
    if not child:
        return out
    if child.meters.get("rush", 0.0) < THRESHOLD:
        return out
    if doc.meters.get("lost", 0.0) >= THRESHOLD:
        return out
    sig = ("scatter", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    doc.meters["lost"] = 1.0
    out.append("The folded program slipped from the child's hand and vanished under a chair.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    doc = world.get("document")
    if doc.meters.get("lost", 0.0) < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["unease"] += 1
    out.append("A kind little ghost drifted near the stage, uneasy because the concert program was missing.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    ghost = world.get("ghost")
    doc = world.get("document")
    if not child or doc.meters.get("found", 0.0) < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["unease"] = 0.0
    ghost.memes["gratitude"] = 1.0
    out.append("When the child picked the program up gently, the ghost grew bright and still.")
    return out


CAUSAL_RULES = [_r_scatter, _r_worry, _r_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def tell(name: str, gender: str, parent: str, trait: str) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={"rush": 0.0}, memes={"joy": 0.0}))
    guardian = world.add(Entity(id="parent", kind="character", type=parent, label=f"the {parent}"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="a kind ghost", memes={"unease": 1.0}))
    program = world.add(Entity(
        id="document",
        type="document",
        label=DOCUMENT.label,
        phrase=DOCUMENT.phrase,
        owner=name,
        caretaker="parent",
        meters={"lost": 0.0, "found": 0.0},
    ))
    world.facts.update(child=child, guardian=guardian, ghost=ghost, program=program,
                       trait=trait, concert=CONCERT, document=DOCUMENT)

    world.say(f"{name} was a little {trait} {gender} who came to {CONCERT.title}.")
    world.say(f"{CONCERT.venue_note} Everyone waited for {CONCERT.sound}, and {name} held {name}'s {DOCUMENT.label}.")
    world.say(f"{DOCUMENT.importance.capitalize()}. {DOCUMENT.risk.capitalize()}")

    world.para()
    world.say(f"At the concert, {name} wanted to run closer to the stage.")
    child.meters["rush"] += 1.0
    child.memes["curiosity"] = 1.0
    propagate(world)

    world.para()
    world.say(f"{name} bent down, found the {DOCUMENT.label}, and held it with two careful hands.")
    program.meters["found"] = 1.0
    propagate(world)

    world.para()
    world.say(f"The ghost smiled, and the music started just as the program was handed to the pianist.")
    child.memes["joy"] = 1.0
    child.memes["kindness"] = 1.0
    world.say(f"{HELPER.tail.capitalize()}.")
    world.say(f"{name} stayed to hear the full concert, and the little ghost finally looked at peace.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    trait = f["trait"]
    return [
        f'Write a short ghost story for a young child about a concert and a document, with kindness at the center.',
        f"Tell a gentle story where {child.id} is a {trait} child who finds a concert program and helps a ghost.",
        f'Write a simple story with the words "concert" and "document" that ends with someone choosing a kind action.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["guardian"]
    ghost = f["ghost"]
    program = f["program"]
    trait = f["trait"]
    qa = [
        QAItem(
            question=f"Who is the story about at the concert?",
            answer=f"The story is about {child.id}, a little {trait} {child.type}, and {parent.label}.",
        ),
        QAItem(
            question=f"What document did {child.id} find near the stage?",
            answer=f"{child.id} found the {DOCUMENT.label}, a folded paper that told the musicians the song order.",
        ),
        QAItem(
            question=f"Why did the ghost seem upset at first?",
            answer=f"The ghost was uneasy because the {DOCUMENT.label} was missing, and without it the concert could not begin smoothly.",
        ),
        QAItem(
            question=f"What did {child.id} do to help in a kind way?",
            answer=f"{child.id} picked up the {DOCUMENT.label} gently and gave it back so the concert could continue.",
        ),
    ]
    if ghost.memes.get("gratitude", 0.0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"How did the ghost feel at the end?",
            answer=f"The ghost felt peaceful and grateful after {child.id} handled the {DOCUMENT.label} with kindness.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a concert?",
            answer="A concert is a musical performance where people listen to songs played or sung for an audience.",
        ),
        QAItem(
            question="What is a document?",
            answer="A document is a piece of paper or digital file that keeps important information written down.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means treating someone gently, helping them, and trying to make them feel safe or happy.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky spirit character in a story, and it can be scary or friendly depending on the tale.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "concert_hall"),
        asp.fact("affords", "concert_hall", "concert"),
        asp.fact("affords", "concert_hall", "document"),
        asp.fact("topic", "kindness"),
        asp.fact("event", "concert"),
        asp.fact("object", "document"),
        asp.fact("emotion", "kindness"),
        asp.fact("spooky_style", "ghost_story"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
event_domain(concert_hall, concert, document, kindness).

document_relevant(D) :- object(D), topic(kindness).
concert_saved :- event(concert), object(document), emotion(kindness).
ghost_settled :- concert_saved.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show concert_saved/0. #show ghost_settled/0.")
    model = asp.one_model(program)
    atoms = {(sym.name, len(sym.arguments)) for sym in model}
    expected = {("concert_saved", 0), ("ghost_settled", 0)}
    if atoms == expected:
        print("OK: ASP gate matches the Python story premise.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: a concert, a document, and kindness.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or pronounce_name(gender, rng)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show concert_saved/0. #show ghost_settled/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story: a concert can be saved when kindness and the document are both present.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            name="Mina",
            gender="girl",
            parent="mother",
            trait="kind",
            seed=base_seed,
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
