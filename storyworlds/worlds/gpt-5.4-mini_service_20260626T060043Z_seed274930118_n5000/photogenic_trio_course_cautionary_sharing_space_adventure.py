#!/usr/bin/env python3
"""
storyworlds/worlds/photogenic_trio_course_cautionary_sharing_space_adventure.py
================================================================================

A small space-adventure storyworld about a photogenic trio, a course through
space, and a cautionary lesson about sharing equipment and space.

The seed idea:
---
A photogenic trio of young space explorers set out on a course to map a new
asteroid lane. They were cheerful and eager to take pictures of the stars.
But their shared ship had only one good camera, one snack kit, and one power
tablet. The trio learned that if they took turns and shared the gear, they could
stay safe and finish the course together.

World premise:
---
- The story follows exactly three crew members.
- They travel on a course from one location to another.
- One cautionary problem creates tension: a shared resource is in danger of
  being monopolized, misplaced, or drained.
- The resolution is a concrete sharing action that restores progress and safety.

Physics / emotion model:
---
- Entities have meters and memes.
- Meters track physical quantities like fuel, charge, distance, and possession.
- Memes track emotional states like worry, trust, pride, relief, and fairness.
- Story text is driven by state changes, not by a frozen template.
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
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    start: str
    end: str
    view: str


@dataclass
class Course:
    id: str
    label: str
    hazard: str
    caution: str
    distance: int
    kind: str


@dataclass
class SharedItem:
    id: str
    label: str
    phrase: str
    use: str
    fragile: bool = False
    charge: int = 0


@dataclass
class StoryParams:
    setting: str
    course: str
    item: str
    crew1: str
    crew2: str
    crew3: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, course: Course) -> None:
        self.setting = setting
        self.course = course
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting, self.course)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_share_item(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("shared")
    if item.meters.get("shared_use", 0) < THRESHOLD:
        return out
    # Sharing resolves overuse and restores trust.
    sig = ("shared", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for c in world.characters():
        c.memes["trust"] = c.memes.get("trust", 0) + 1
        c.memes["fairness"] = c.memes.get("fairness", 0) + 1
    item.meters["overheated"] = 0
    out.append("They took turns, and the little ship was calm again.")
    return out


def _r_caution(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("shared")
    if item.meters.get("held_too_long", 0) < THRESHOLD:
        return out
    sig = ("caution", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    leader = world.get("leader")
    leader.memes["worry"] = leader.memes.get("worry", 0) + 1
    out.append("The captain gave a cautionary look at the too-busy hands.")
    return out


CAUSAL_RULES = [
    _r_caution,
    _r_share_item,
]


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


SETTINGS = {
    "dock": Setting(place="the bright launch dock", start="dock", end="orbit", view="the station lights"),
    "lane": Setting(place="the quiet comet lane", start="lane", end="the relay tower", view="the blue stars"),
    "ring": Setting(place="the ring of small moons", start="ring", end="the safe marker buoy", view="the silver dust"),
}

COURSES = {
    "survey": Course(id="survey", label="survey course", hazard="drift", caution="keep watch for drifting rocks", distance=3, kind="map"),
    "delivery": Course(id="delivery", label="delivery course", hazard="spin", caution="do not lose the cargo tray", distance=4, kind="carry"),
    "photo": Course(id="photo", label="photogenic course", hazard="glare", caution="share the camera so everyone gets a turn", distance=5, kind="photo"),
}

SHARED_ITEMS = {
    "camera": SharedItem(id="camera", label="camera", phrase="a tiny silver camera", use="take pictures", fragile=True),
    "snacks": SharedItem(id="snacks", label="snack kit", phrase="a snack kit with three wrappers", use="eat between stops"),
    "tablet": SharedItem(id="tablet", label="power tablet", phrase="a bright power tablet", use="keep the ship powered", charge=3),
}

NAMES = ["Nova", "Pip", "Sol", "Mira", "Tala", "Juno", "Kai", "Rin", "Zed", "Nia"]
TRAITS = ["photogenic", "brave", "careful", "cheerful", "curious", "daring"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about a photogenic trio and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--course", choices=COURSES)
    ap.add_argument("--item", choices=SHARED_ITEMS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--name3")
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
    course = args.course or rng.choice([c for c in COURSES if c in {"photo", "survey", "delivery"}])
    item = args.item or ("camera" if course == "photo" else rng.choice(list(SHARED_ITEMS)))
    if course == "photo" and item != "camera":
        raise StoryError("The photogenic course needs the camera story to make sense.")
    crew = [args.name1, args.name2, args.name3]
    names = [n or rng.choice(NAMES) for n in crew]
    if len(set(names)) != 3:
        raise StoryError("The trio needs three different crew members.")
    return StoryParams(setting=setting, course=course, item=item, crew1=names[0], crew2=names[1], crew3=names[2])


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    course = COURSES[params.course]
    item_cfg = SHARED_ITEMS[params.item]
    world = World(setting, course)
    leader = world.add(Entity(id="leader", kind="character", type="captain", label="captain", role="leader"))
    a = world.add(Entity(id="crew1", kind="character", type="crew", label=params.crew1, role="crew"))
    b = world.add(Entity(id="crew2", kind="character", type="crew", label=params.crew2, role="crew"))
    c = world.add(Entity(id="crew3", kind="character", type="crew", label=params.crew3, role="crew"))
    shared = world.add(Entity(
        id="shared",
        kind="thing",
        type=item_cfg.label,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=leader.id,
        plural=False,
    ))
    shared.meters["charge"] = item_cfg.charge
    world.facts.update(leader=leader, crew=[a, b, c], shared=shared, setting=setting, course=course, item=item_cfg)
    return world


def intro(world: World) -> None:
    crew = world.facts["crew"]
    item = world.facts["shared"]
    course = world.facts["course"]
    world.say(
        f"On {world.setting.place}, a photogenic trio—{crew[0].label}, {crew[1].label}, and {crew[2].label}—"
        f"prepared for the {course.label}."
    )
    world.say(
        f"They loved the way {world.setting.view} glittered, and {item.phrase} was the one thing they all wanted to use."
    )


def tension(world: World) -> None:
    item = world.facts["shared"]
    crew = world.facts["crew"]
    course = world.facts["course"]
    item.meters["held_too_long"] = 1
    crew[0].memes["pride"] = crew[0].memes.get("pride", 0) + 1
    crew[1].memes["worry"] = crew[1].memes.get("worry", 0) + 1
    crew[2].memes["worry"] = crew[2].memes.get("worry", 0) + 1
    world.say(
        f"{crew[0].label} kept the {item.label} a little too long while the ship drifted onto the {course.hazard}y part of the route."
    )
    world.say(
        f"{crew[1].label} and {crew[2].label} glanced at the controls, because {course.caution}."
    )
    propagate(world, narrate=True)


def turn_and_resolve(world: World) -> None:
    item = world.facts["shared"]
    crew = world.facts["crew"]
    course = world.facts["course"]
    item.meters["shared_use"] = 1
    world.say(
        f"Then {crew[1].label} suggested a simple sharing plan: one took the picture, one watched the map, and one held the ship steady."
    )
    item.meters["held_too_long"] = 0
    propagate(world, narrate=True)
    for c in crew:
        c.memes["relief"] = c.memes.get("relief", 0) + 1
    world.say(
        f"The trio smiled in turn, and the {course.label} ended with three bright faces and one safe, happy ship."
    )


def generate_story(params: StoryParams) -> StorySample:
    world = make_world(params)
    intro(world)
    world.para()
    tension(world)
    world.para()
    turn_and_resolve(world)
    story = world.render()
    prompts = [
        f"Write a short space adventure story about a photogenic trio on a {world.course.label} who must share a {world.facts['shared'].label}.",
        f"Tell a cautionary story where three young explorers learn to share {world.facts['shared'].phrase} while traveling through space.",
        f"Write a child-friendly adventure with a trio, a course, and a happy sharing lesson among the stars.",
    ]
    story_qa = [
        QAItem(
            question=f"Who went on the {world.course.label}?",
            answer=f"The story is about {world.facts['crew'][0].label}, {world.facts['crew'][1].label}, and {world.facts['crew'][2].label}, a photogenic trio of space explorers.",
        ),
        QAItem(
            question=f"What was the shared item in the ship?",
            answer=f"They shared {world.facts['shared'].phrase}, which they needed for the adventure.",
        ),
        QAItem(
            question="Why did the captain look worried?",
            answer=f"The captain worried because one crew member held the {world.facts['shared'].label} too long, and the course was heading into a risky part of space.",
        ),
        QAItem(
            question="How did the trio fix the problem?",
            answer="They took turns sharing the equipment, which kept the ship safe and helped everyone stay calm.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does it mean to share something?",
            answer="To share something means to let other people use it too, so everyone gets a fair turn.",
        ),
        QAItem(
            question="What is a course in space?",
            answer="A course is the planned path a ship follows when it travels from one place to another.",
        ),
        QAItem(
            question="Why can caution be important on a space trip?",
            answer="Caution matters because space can have drift, glare, or other hazards, so careful choices help keep everyone safe.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
course_story(Setting, Course, Item) :- setting(Setting), course(Course), shared_item(Item).
photogenic_trio(A, B, C) :- crew(A), crew(B), crew(C), A != B, A != C, B != C.
needs_sharing(Course, Item) :- course(Course), shared(Item), caution(Course).
valid_story(Setting, Course, Item) :- course_story(Setting, Course, Item), needs_sharing(Course, Item).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in COURSES.items():
        lines.append(asp.fact("course", cid))
        lines.append(asp.fact("caution", cid))
        lines.append(asp.fact("hazard", cid, c.hazard))
    for iid in SHARED_ITEMS:
        lines.append(asp.fact("shared_item", iid))
        lines.append(asp.fact("shared", iid))
    for name in NAMES:
        lines.append(asp.fact("crew", name.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(s, c, i) for s in SETTINGS for c in COURSES for i in SHARED_ITEMS if not (c == "photo" and i != "camera")}
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python set ({len(python_set)} combos).")
        return 0
    print("Mismatch between clingo and Python sets.")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        combos = []
        for s in SETTINGS:
            for c in COURSES:
                for i in SHARED_ITEMS:
                    if c == "photo" and i != "camera":
                        continue
                    combos.append(StoryParams(s, c, i, "Nova", "Pip", "Sol"))
        samples = [generate(p) for p in combos]
    else:
        samples = []
        seen: set[str] = set()
        for idx in range(max(args.n, 1) * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + idx))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + idx
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
            if len(samples) >= args.n:
                break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
