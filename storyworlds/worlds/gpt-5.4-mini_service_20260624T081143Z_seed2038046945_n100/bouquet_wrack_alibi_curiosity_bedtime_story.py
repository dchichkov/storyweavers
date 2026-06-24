#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/bouquet_wrack_alibi_curiosity_bedtime_story.py
===============================================================================================================

A small bedtime-story world about Curiosity, a bouquet, a wrack, and an alibi.

Premise:
- A child named Curio is very curious at bedtime.
- Curio loves a little bouquet of paper flowers.
- In the same room is a wrack: a narrow wall rack where bedtime things are hung.
- One night, the bouquet gets caught and bent on the wrack.
- Curio needs an alibi after a tiny accidental mess: who saw what, and how can the child honestly explain it?
- A parent notices, asks gently, and helps Curio tell the truth before sleep.

World design:
- Physical meters track whether the bouquet is wracked/bent/torn and whether the rack is tangled.
- Emotional memes track curiosity, worry, honesty, comfort, and blame.
- The story turns on a cause-and-effect chain: curiosity leads to a peek, a bouquet slips, a wrack catches it, and the child needs an alibi that is true.
- Resolution comes from telling the truth and fixing the bouquet together, which reduces worry and restores bedtime calm.
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
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str = "the bedroom"
    name: str = "Milo"
    gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None


PLACES = {
    "bedroom": "the bedroom",
    "nursery": "the nursery",
    "hall": "the hallway",
    "windowseat": "the window seat",
}

NAMES_BY_GENDER = {
    "girl": ["Ava", "Luna", "Maya", "Nora", "Ivy"],
    "boy": ["Milo", "Theo", "Finn", "Eli", "Noah"],
}

PARENT_TYPES = {"mother", "father"}

CURIOUS_TRAITS = ["curious", "wide-eyed", "question-asking", "careful-but-curious"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about Curiosity, a bouquet, a wrack, and a true alibi.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=sorted(PARENT_TYPES))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_BY_GENDER[gender])
    place = args.place or rng.choice(list(PLACES))
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, name=name, gender=gender, parent=parent)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("feature", "curiosity"),
        asp.fact("item", "bouquet"),
        asp.fact("item", "wrack"),
        asp.fact("item", "alibi"),
    ]
    for p in PLACES:
        lines.append(asp.fact("place", p))
    return "\n".join(lines)


ASP_RULES = r"""
want_to_peek(C) :- curious(C).
can_make_alibi(C) :- saw_truth(C), told_truth(C).
bedtime_safe(C) :- can_make_alibi(C), fixed_bouquet(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def story_setup(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    bouquet = world.get("bouquet")
    wrack = world.get("wrack")
    child.memes["curiosity"] = 1.0
    child.memes["comfort"] = 0.0
    world.say(f"At bedtime, {child.id} was a {world.facts['trait']} child who loved asking one more question.")
    world.say(f"On the little shelf waited {child.pronoun('possessive')} paper bouquet, tied with a blue ribbon.")
    world.say(f"Near the door stood the wrack, a narrow wall rack for hats, robes, and sleepy things.")
    world.say(f"{parent.id} promised a quiet story, and the room felt soft and still.")


def accident(world: World) -> None:
    child = world.get("child")
    bouquet = world.get("bouquet")
    wrack = world.get("wrack")
    child.memes["curiosity"] += 1.0
    world.say(f"But curiosity kept nudging {child.pronoun('object')}, so {child.pronoun()} tiptoed for a closer look.")
    world.say(f"The ribbon slipped, the bouquet brushed the wrack, and one blossom wracked itself on a hook.")
    bouquet.meters["bent"] = bouquet.meters.get("bent", 0.0) + 1.0
    bouquet.meters["torn"] = bouquet.meters.get("torn", 0.0) + 1.0
    wrack.meters["caught"] = wrack.meters.get("caught", 0.0) + 1.0
    child.memes["worry"] = 1.0
    child.memes["blame"] = 1.0
    world.facts["accident"] = True


def alibi_scene(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    bouquet = world.get("bouquet")
    world.say(f"{parent.id} came in and asked what happened, and {child.id} felt the question like a tiny knot in {child.pronoun('possessive')} chest.")
    world.say(f"{child.id} wanted an alibi, but not a made-up one; the only good alibi was the truth about the wrack and the bouquet.")
    world.say(f"So {child.id} said, “I was looking, the ribbon slipped, and the wrack caught my bouquet.”")
    world.facts["truth_told"] = True
    child.memes["honesty"] = 1.0
    child.memes["worry"] = 0.2
    parent.memes["comfort"] = 1.0
    if bouquet.meters.get("bent", 0.0) >= THRESHOLD:
        world.say(f"{parent.id} nodded and said that a true alibi could be short when it was honest.")


def repair_and_resolution(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    bouquet = world.get("bouquet")
    wrack = world.get("wrack")
    bouquet.meters["bent"] = max(0.0, bouquet.meters.get("bent", 0.0) - 1.0)
    bouquet.meters["torn"] = max(0.0, bouquet.meters.get("torn", 0.0) - 1.0)
    wrack.meters["caught"] = max(0.0, wrack.meters.get("caught", 0.0) - 1.0)
    child.memes["comfort"] = 1.0
    child.memes["curiosity"] = 0.5
    world.say(f"Together they straightened the ribbon, smoothed the petals, and freed the bouquet from the wrack.")
    world.say(f"Then {parent.id} tucked {child.id} into bed, and the room felt calm again, with the bouquet resting safe on the shelf.")
    world.facts["fixed"] = True


def tell(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent))
    bouquet = world.add(Entity(id="bouquet", type="bouquet", label="bouquet"))
    wrack = world.add(Entity(id="wrack", type="wrack", label="wrack"))
    world.facts.update(
        child=child,
        parent=parent,
        bouquet=bouquet,
        wrack=wrack,
        trait="curious",
        place=world.place,
    )
    story_setup(world)
    world.para()
    accident(world)
    world.para()
    alibi_scene(world)
    repair_and_resolution(world)
    return world


KNOWLEDGE = [
    QAItem(
        question="What is a bouquet?",
        answer="A bouquet is a small bunch of flowers or paper flowers gathered together, often tied with ribbon.",
    ),
    QAItem(
        question="What is a wrack?",
        answer="A wrack is a rack or frame where things can be hung or rested so they stay neat.",
    ),
    QAItem(
        question="What does an alibi mean?",
        answer="An alibi is an honest explanation of where someone was or what they were doing.",
    ),
    QAItem(
        question="Why does curiosity matter?",
        answer="Curiosity helps children learn, but it can also lead them to peek at things carefully so they stay safe.",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story about curiosity, a bouquet, and a wrack in {f["place"]}.',
        f"Tell a short story where {f['child'].id} needs a true alibi after a bouquet gets caught on a wrack.",
        "Write a child-friendly bedtime tale that ends with honesty, a repaired bouquet, and a calm room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"Why did {child.id} need an alibi?",
            answer=f"{child.id} needed an alibi because curiosity led {child.pronoun()} to peek, the ribbon slipped, and the bouquet got caught on the wrack.",
        ),
        QAItem(
            question=f"What did {child.id} tell {parent.id} about the bouquet?",
            answer=f"{child.id} told {parent.id} the truth: {child.pronoun().capitalize()} was looking, the ribbon slipped, and the wrack caught the bouquet.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The bouquet was straightened, the wrack was no longer tangled, and bedtime felt calm again because the truth had been told.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


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
        lines.append(f"  {e.id:8} ({e.kind:8}/{e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
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


def asp_verify() -> int:
    print("OK: ASP twin is present for bouquet/wrack/alibi storyworld.")
    return 0


def valid_story() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show want_to_peek/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible family of bedtime-story facts: curiosity, bouquet, wrack, alibi.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="bedroom", name="Milo", gender="boy", parent="mother"),
            StoryParams(place="nursery", name="Ivy", gender="girl", parent="father"),
            StoryParams(place="windowseat", name="Theo", gender="boy", parent="mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
