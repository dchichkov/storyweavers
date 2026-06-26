#!/usr/bin/env python3
"""
storyworlds/worlds/hosta_tinkle_bugle_school_moral_value_lesson.py
===================================================================

A small slice-of-life story world set in school.

Seed image:
- A child tends a hosta plant for a school project.
- A tiny tinkle-bell on a bugle-like instrument makes a mistake in music class.
- The child must choose between hiding the mishap and admitting it.

The story world keeps the action concrete and causal:
- physical state: dirt, water, sound, and object handling
- emotional state: pride, worry, honesty, relief
- Moral Value / Lesson Learned: honesty helps repair small mistakes

This world is designed to feel like a calm school-day story rather than a big
adventure: a small mistake, a truthful choice, and a gentle ending image.
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "dirty": 0.0, "noise": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "honesty": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class School:
    place: str = "the school"
    garden: str = "the school garden"
    music_room: str = "the music room"


@dataclass
class Hosta:
    label: str = "hosta"
    phrase: str = "a small hosta plant in a clay pot"
    smell: str = "fresh"
    needs_water: bool = True


@dataclass
class Bugle:
    label: str = "bugle"
    phrase: str = "a shiny bugle with a tiny tinkle bell"
    sound: str = "bright"
    bell: str = "tinkle"


@dataclass
class StoryParams:
    place: str = "school"
    child_name: str = "Mina"
    child_gender: str = "girl"
    adult_name: str = "Ms. Park"
    seed: Optional[int] = None


class World:
    def __init__(self, school: School) -> None:
        self.school = school
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.school)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    hosta = world.get("hosta")
    bugle = world.get("bugle")
    bucket = world.get("water_bucket")

    if child.meters["dirty"] >= THRESHOLD and "dirty_hands" not in world.fired:
        world.fired.add("dirty_hands")
        child.memes["worry"] += 1
        out.append(f"{child.id} noticed {child.pronoun('possessive')} hands were dirty.")

    if bugle.meters["noise"] >= THRESHOLD and "loud_bugle" not in world.fired:
        world.fired.add("loud_bugle")
        child.memes["worry"] += 1
        out.append("The bugle gave a loud, wobbling note that made the room feel too busy.")

    if bucket.meters["wet"] >= THRESHOLD and hosta.meters["wet"] < THRESHOLD and "watered" not in world.fired:
        world.fired.add("watered")
        hosta.meters["wet"] += 1
        out.append("The hosta soaked up the water and looked perkier right away.")

    if child.memes["honesty"] >= THRESHOLD and "truth_told" not in world.fired:
        world.fired.add("truth_told")
        child.memes["relief"] += 1
        child.memes["worry"] = 0
        out.append("Once the truth was out, the worry began to loosen.")

    if narrate:
        for line in out:
            world.say(line)
    return out


def predict_mishap(world: World) -> dict[str, bool]:
    sim = world.copy()
    child = sim.get("child")
    bugle = sim.get("bugle")
    child.meters["dirty"] += 1
    bugle.meters["noise"] += 1
    propagate(sim, narrate=False)
    return {
        "would_be_messy": child.memes["worry"] >= THRESHOLD,
        "would_be_loud": bugle.meters["noise"] >= THRESHOLD,
    }


def school_day_intro(world: World, child: Entity, adult: Entity, hosta: Entity, bugle: Entity) -> None:
    world.say(
        f"{child.id} was a thoughtful little {child.type} who liked neat classroom corners and "
        f"quiet jobs that could be finished well."
    )
    world.say(
        f"At {world.school.place}, {child.id} was caring for {hosta.phrase} for a class project, "
        f"and {bugle.phrase} waited nearby for music time."
    )
    world.say(
        f"{child.id} liked how the hosta's leaves looked calm and cool, and the bugle's tiny bell "
        f"made a soft tinkle when it moved."
    )


def school_tension(world: World, child: Entity, adult: Entity, hosta: Entity, bugle: Entity) -> None:
    world.para()
    world.say(
        f"During the day, {child.id} carried the hosta toward {world.school.garden} and hoped "
        f"to water {child.pronoun('object')} before class."
    )
    world.say(
        f"Then, in the music room, {child.id} reached for the bugle and gave it a little shake."
    )
    child.meters["dirty"] += 1
    bugle.meters["noise"] += 1
    child.memes["pride"] += 1
    world.say(
        f"The tinkle bell chimed louder than expected, and a few heads turned."
    )
    propagate(world)
    child.memes["worry"] += 1
    world.say(
        f"{child.id} felt a small pinch of worry, because {child.pronoun('possessive')} hands were dusty "
        f"and the sound had become a bit too bright."
    )
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"{adult.id} looked over and asked gently, 'What happened there, {child.id}?'"
        )


def lesson_and_resolution(world: World, child: Entity, adult: Entity, hosta: Entity, bugle: Entity) -> None:
    world.para()
    child.memes["honesty"] += 1
    world.say(
        f"{child.id} took a breath and said, 'I shook the bugle too hard, and I made a mess.'"
    )
    world.say(
        f"{adult.id} nodded and smiled. 'Thank you for telling the truth. That is a good lesson learned.'"
    )
    world.say(
        f"Together they wiped the bugle's bell, washed {child.pronoun('possessive')} hands, and poured water "
        f"for the hosta."
    )
    bucket = world.get("water_bucket")
    bucket.meters["wet"] += 1
    hosta.meters["wet"] += 1
    propagate(world)
    world.say(
        f"By the end, the hosta stood a little taller, the bugle was quiet again, and {child.id} felt "
        f"brighter for being honest."
    )
    world.say(
        f"The Moral Value was simple: telling the truth helps fix small mistakes, and a calm school day "
        f"can still end with a happy smile."
    )


def tell(params: StoryParams) -> World:
    school = School()
    world = World(school)

    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    adult = world.add(Entity(id="adult", kind="character", type="adult", label=params.adult_name))
    hosta = world.add(Entity(id="hosta", type="plant", label="hosta", phrase="a small hosta plant in a clay pot"))
    bugle = world.add(Entity(id="bugle", type="instrument", label="bugle", phrase="a shiny bugle with a tiny tinkle bell"))
    bucket = world.add(Entity(id="water_bucket", type="thing", label="watering bucket", phrase="a little blue watering bucket"))

    world.facts.update(child=child, adult=adult, hosta=hosta, bugle=bugle, bucket=bucket)
    school_day_intro(world, child, adult, hosta, bugle)
    school_tension(world, child, adult, hosta, bugle)
    lesson_and_resolution(world, child, adult, hosta, bugle)
    return world


SETTINGS = {"school": School()}
NAMES = ["Mina", "Arin", "Lena", "Noah", "Tess", "Eli", "Rae", "Owen"]
ADULTS = ["Ms. Park", "Mr. Lee", "Ms. Kim", "Mr. Chen"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "school":
        raise StoryError("This world is set at school only.")
    if not params.child_name:
        raise StoryError("A child name is required.")


ASP_RULES = r"""
child(c1).
adult(a1).
thing(hosta).
thing(bugle).
thing(bucket).

place(school).

at(child, school).
at(adult, school).

lesson(honesty).
value(honesty).

mishap(child, bugle) :- shook(child, bugle), loud(bugle).
repair(child, bugle) :- told_truth(child), cleaned(bugle), washed_hands(child), watered(hosta).

moral_value(honesty) :- told_truth(child).
lesson_learned(child, honesty) :- repair(child, bugle).

shown_story :- moral_value(honesty), lesson_learned(child, honesty).
#show moral_value/1.
#show lesson_learned/2.
#show shown_story/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "school"))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("adult", "adult"))
    lines.append(asp.fact("thing", "hosta"))
    lines.append(asp.fact("thing", "bugle"))
    lines.append(asp.fact("thing", "bucket"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shown_story/0."))
    atoms = {str(sym) for sym in model}
    ok = "shown_story" in atoms
    if ok:
        print("OK: ASP model produced the story twin.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected story atom.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life school story world with hosta, tinkle, and bugle.")
    ap.add_argument("--place", choices=list(SETTINGS), default="school")
    ap.add_argument("--name")
    ap.add_argument("--adult")
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
    if args.place != "school":
        raise StoryError("This world can only happen at school.")
    return StoryParams(
        place="school",
        child_name=args.name or rng.choice(NAMES),
        child_gender="girl" if rng.random() < 0.5 else "boy",
        adult_name=args.adult or rng.choice(ADULTS),
        seed=args.seed,
    )


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    a = world.facts["adult"]
    return [
        "Write a gentle slice-of-life school story about a hosta plant, a tinkle bell, and a bugle.",
        f"Tell a calm school-day story where {c.label} learns a lesson after making a small mistake with the bugle.",
        f"Write a short story for children about {c.label} and {a.label} choosing honesty and care at school.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    a = world.facts["adult"]
    hosta = world.facts["hosta"]
    bugle = world.facts["bugle"]
    return [
        QAItem(
            question=f"What was {c.label} caring for at school?",
            answer=f"{c.label} was caring for a hosta plant in a clay pot as a class project.",
        ),
        QAItem(
            question=f"What made the music room feel a little too loud?",
            answer=f"The bugle's tiny tinkle bell chimed louder than {c.label} expected.",
        ),
        QAItem(
            question=f"What did {a.label} praise as a good lesson learned?",
            answer="Telling the truth and fixing a small mistake was the lesson learned.",
        ),
        QAItem(
            question=f"What happened to the hosta by the end of the story?",
            answer="The hosta got watered and stood a little taller by the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hosta?",
            answer="A hosta is a leafy garden plant that often grows in shady places and has broad green leaves.",
        ),
        QAItem(
            question="What is a bugle?",
            answer="A bugle is a brass instrument that makes bright, clear notes when someone blows into it.",
        ),
        QAItem(
            question="What does a tinkle bell sound like?",
            answer="A tinkle bell makes a small, light ringing sound, like a tiny chime.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show shown_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show moral_value/1. #show lesson_learned/2."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 20):
        seed = base_seed + i
        i += 1
        try:
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
        except StoryError as err:
            print(err)
            return
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
