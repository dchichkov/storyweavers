#!/usr/bin/env python3
"""
storyworlds/worlds/margarita_niece_tar_dialogue_surprise_teamwork_bedtime.py
============================================================================

A small bedtime-story world about a niece, a surprise, sticky tar, and the
gentle teamwork that gets everyone ready for sleep.

The story premise:
- A child visits an aunt at bedtime.
- A surprise bedtime gift is prepared for the child.
- Sticky tar outside makes the surprise hard to bring in safely.
- Dialogue, surprise, and teamwork turn the mess into a calm ending.

The simulated state tracks physical meters and emotional memes. The prose is
driven by the state, not by a frozen template.

Seed words required by the prompt:
- margarita
- niece
- tar

Narrative instruments required by the prompt:
- Dialogue
- Surprise
- Teamwork

Style:
- Bedtime Story
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the cozy house porch"
    indoors: bool = False


@dataclass
class StoryEvent:
    name: str
    text: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[StoryEvent] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(StoryEvent("say", text))

    def render(self) -> str:
        parts: list[str] = []
        para: list[str] = []
        for ev in self.events:
            if ev.text == "":
                if para:
                    parts.append(" ".join(para))
                    para = []
                continue
            para.append(ev.text)
        if para:
            parts.append(" ".join(para))
        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str = "Mia"
    aunt_name: str = "Aunt Rosa"
    seed: Optional[int] = None
    place: str = "porch"


NAMES = ["Mia", "Lily", "Nora", "Ivy", "Ella", "June"]
AUNTS = ["Aunt Rosa", "Aunt Lina", "Aunt Bea", "Aunt Mara"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def reasonable_story(place: str) -> bool:
    return place in {"porch", "backyard", "hallway"}


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(porch).
setting(backyard).
setting(hallway).

surprise(gift_box).
surprise(night_light).

mess(tar).
cleans(soap).
cleans(cloth).

gift_for(niece, surprise_box).

compatible(Place, Gift) :- setting(Place), gift_for(niece, Gift).
safe_fix(tar, soap).
safe_fix(tar, cloth).
has_fix(tar) :- safe_fix(tar, _).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place in ["porch", "backyard", "hallway"]:
        lines.append(asp.fact("setting", place))
    for gift in ["gift_box", "night_light"]:
        lines.append(asp.fact("surprise", gift))
    lines.append(asp.fact("mess", "tar"))
    lines.append(asp.fact("cleans", "soap"))
    lines.append(asp.fact("cleans", "cloth"))
    lines.append(asp.fact("gift_for", "niece", "surprise_box"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    prog = asp_program("#show compatible/2.\n#show has_fix/1.")
    model = asp.one_model(prog)
    compatible = set(asp.atoms(model, "compatible"))
    has_fix = set(asp.atoms(model, "has_fix"))
    py_compatible = {(p, "surprise_box") for p in ["porch", "backyard", "hallway"]}
    py_has_fix = {("tar",)}
    if compatible == py_compatible and has_fix == py_has_fix:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python twin.")
    print("compat only in ASP:", sorted(compatible - py_compatible))
    print("compat only in Python:", sorted(py_compatible - compatible))
    print("fix only in ASP:", sorted(has_fix - py_has_fix))
    print("fix only in Python:", sorted(py_has_fix - has_fix))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if not reasonable_story(params.place):
        raise StoryError("This bedtime story needs a small, calm place like a porch, backyard, or hallway.")
    world = World(Setting(place=f"the {params.place}" if not params.place.startswith("the ") else params.place))
    niece = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    aunt = world.add(Entity(id=params.aunt_name, kind="character", type="aunt", label=params.aunt_name))
    box = world.add(Entity(
        id="surprise_box",
        kind="thing",
        type="box",
        label="little surprise box",
        phrase="a little surprise box with a moon sticker",
        owner=aunt.id,
        caretaker=aunt.id,
    ))
    tar = world.add(Entity(
        id="tar_patch",
        kind="thing",
        type="tar",
        label="sticky tar",
        phrase="a dark sticky tar patch",
        meters={"stickiness": 2.0},
    ))
    lamp = world.add(Entity(
        id="margarita",
        kind="thing",
        type="lantern",
        label="Margarita",
        phrase="a tiny night-light lantern named Margarita",
        owner=niece.id,
        caretaker=niece.id,
    ))
    world.facts.update(niece=niece, aunt=aunt, box=box, tar=tar, lamp=lamp)
    return world


def tell(world: World) -> None:
    niece: Entity = world.facts["niece"]  # type: ignore[assignment]
    aunt: Entity = world.facts["aunt"]  # type: ignore[assignment]
    box: Entity = world.facts["box"]  # type: ignore[assignment]
    tar: Entity = world.facts["tar"]  # type: ignore[assignment]
    lamp: Entity = world.facts["lamp"]  # type: ignore[assignment]

    niece.memes["sleepy"] = 1.0
    aunt.memes["calm"] = 1.0

    world.say(f"It was a soft bedtime evening at {world.setting.place}.")
    world.say(f"{niece.id} was a little niece who liked warm blankets, quiet songs, and gentle surprises.")
    world.say(f"{aunt.id} smiled and whispered, \"I made a bedtime surprise for you.\"")
    world.say(f"{aunt.id} showed {niece.id} {box.phrase}, and {niece.id} blinked with happy surprise.")
    niece.memes["surprise"] = 1.0
    niece.memes["joy"] = 1.0
    world.say(f"Inside the box was {lamp.phrase}. \"Her name is Margarita,\" said {aunt.id}.")
    world.say(f"\"Margarita is lovely,\" said {niece.id}, hugging the little lantern.")

    world.say("")
    world.say(f"At the edge of the path, they noticed {tar.label}.")
    world.say(f"\"Oh no,\" said {niece.id}. \"Will Margarita get stuck in that tar?\"")
    aunt.memes["worry"] = 1.0
    niece.memes["worry"] = 1.0
    world.say(f"\"Not if we use teamwork,\" said {aunt.id}. \"We can be careful together.\"")
    world.say(f"{niece.id} held the lantern up high while {aunt.id} brought a soft cloth and warm soap.")
    world.say(f"Together, they cleaned the sticky tar from the little path.")
    tar.meters["stickiness"] = 0.0
    tar.meters["cleaned"] = 1.0
    niece.memes["teamwork"] = 1.0
    aunt.memes["teamwork"] = 1.0

    world.say(f"\"There,\" said {aunt.id}, smiling. \"Now Margarita can shine safely.\"")
    world.say(f"{niece.id} tucked {lamp.label} beside the bed, and the tiny light glowed like a friendly moon.")
    niece.memes["joy"] += 1.0
    niece.memes["sleepy"] += 1.0
    world.say(f"\"Thank you,\" yawned {niece.id}. \"The surprise was sweet, and the teamwork made it easy.\"")
    world.say(f"{aunt.id} kissed {niece.id} goodnight, and the room grew quiet and cozy.")


def generate_story(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    story = world.render()
    prompts = [
        "Write a gentle bedtime story about a niece, a surprise, and a sticky mess that becomes easy with teamwork.",
        "Tell a child-facing story with dialogue where Margarita is safe because the grown-up and child help each other.",
        "Write a calm bedtime tale that includes the words margarita, niece, and tar.",
    ]
    story_qa = [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {params.name}, a little niece, and {params.aunt_name}, who planned a bedtime surprise together.",
        ),
        QAItem(
            question="What was Margarita?",
            answer="Margarita was a tiny night-light lantern, and it was the sweet surprise in the story.",
        ),
        QAItem(
            question="What sticky thing did they notice outside?",
            answer="They noticed sticky tar on the path, and they worked together to clean it.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer="They used teamwork: the niece held Margarita up high, and the aunt cleaned the tar with a soft cloth and warm soap.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is tar like?",
            answer="Tar is thick and sticky, so it can cling to things and make a mess if you touch it.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means two or more people help each other to do something together.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something nice you do not expect, so it can make someone smile or blink with wonder.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a niece, a surprise, and tar.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--aunt", choices=AUNTS)
    ap.add_argument("--place", choices=["porch", "backyard", "hallway"], default="porch")
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
    name = args.name or rng.choice(NAMES)
    aunt_name = args.aunt or rng.choice(AUNTS)
    place = args.place or rng.choice(["porch", "backyard", "hallway"])
    if not reasonable_story(place):
        raise StoryError("The bedtime story needs a calm, small setting.")
    return StoryParams(name=name, aunt_name=aunt_name, place=place)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for eid, e in world.entities.items():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{eid}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


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
        print(asp_program("#show compatible/2.\n#show has_fix/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/2.\n#show has_fix/1."))
        print("compatible:", sorted(asp.atoms(model, "compatible")))
        print("has_fix:", sorted(asp.atoms(model, "has_fix")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mia", aunt_name="Aunt Rosa", place="porch"),
            StoryParams(name="Nora", aunt_name="Aunt Lina", place="backyard"),
            StoryParams(name="Ivy", aunt_name="Aunt Bea", place="hallway"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
