#!/usr/bin/env python3
"""
Cadet Inner Monologue story world.

A small heartwarming simulation about a cadet who is nervous about a first
mission, thinks through the problem in an inner monologue, and ends up helping
someone kindly.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "mentor", "cadet"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    cue: str
    risk: str
    zone: set[str]
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperGear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    offer: str
    ending: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_lines: list[str] = []

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.label in {"helmet", "gloves", "jacket"} and region in getattr(item, "covers", set())
                   for item in self.worn_items(actor))


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    mentor: str
    mood: str
    seed: Optional[int] = None


PLACES = {
    "dock": Place("dock", "the docking bay", {"ship", "arrival"}),
    "classroom": Place("classroom", "the training room", {"lesson", "practice"}),
    "garden": Place("garden", "the station garden", {"plants", "care"}),
    "hangar": Place("hangar", "the hangar", {"ship", "repair"}),
}

TASKS = {
    "signal": Task(
        id="signal",
        verb="fix the blinking signal lamp",
        gerund="repairing the signal lamp",
        cue="the lamp kept flickering",
        risk="the lamp could go dark again",
        zone={"hands"},
        needs={"gloves"},
        tags={"ship", "repair"},
    ),
    "seedlings": Task(
        id="seedlings",
        verb="carry the tiny seedlings",
        gerund="carrying seedlings carefully",
        cue="the little pots looked wobbly",
        risk="the seedlings could tip over",
        zone={"hands"},
        needs={"crate"},
        tags={"plants", "care"},
    ),
    "map": Task(
        id="map",
        verb="pin the star map in place",
        gerund="pinning the star map neatly",
        cue="the map kept curling at the corners",
        risk="the map could wrinkle",
        zone={"hands"},
        needs={"clip"},
        tags={"lesson", "practice"},
    ),
    "toolbox": Task(
        id="toolbox",
        verb="haul the toolbox to the shelf",
        gerund="hauling a toolbox",
        cue="the toolbox was heavier than expected",
        risk="someone could strain their back",
        zone={"back", "hands"},
        needs={"strap"},
        tags={"repair", "ship"},
    ),
}

GEAR = [
    HelperGear("gloves", "a pair of soft gloves", {"hands"}, {"repair"}, "put on soft gloves first", "went to fetch the gloves"),
    HelperGear("crate", "a sturdy little crate", {"hands"}, {"care"}, "use a sturdy little crate", "went to get the crate"),
    HelperGear("clip", "a small silver clip", {"hands"}, {"lesson", "practice"}, "use a small silver clip", "went to get the clip"),
    HelperGear("strap", "a padded strap", {"back", "hands"}, {"ship", "repair"}, "put on a padded strap", "went to get the strap"),
]

HERO_NAMES = ["Mina", "Iris", "Noa", "Etta", "Lena", "Tori", "Aria"]
MENTOR_NAMES = ["Captain Vale", "Commander Sun", "Instructor Kestrel", "Lieutenant Wren"]
MOODS = ["nervous", "hopeful", "careful", "quiet", "brave"]


def _m(emotion: str, value: float = 1.0) -> dict[str, float]:
    return {emotion: value}


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for task_id, task in TASKS.items():
            if task.tags & place.tags:
                out.append((place_id, task_id))
    return out


def reasonableness_gate(place_id: str, task_id: str) -> bool:
    place = PLACES[place_id]
    task = TASKS[task_id]
    return bool(task.tags & place.tags)


def pick_gear(task: Task) -> Optional[HelperGear]:
    for gear in GEAR:
        if task.id in gear.guards or any(tag in gear.guards for tag in task.tags):
            if task.zone.issubset(gear.covers):
                return gear
    return None


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for tag in sorted(place.tags):
            lines.append(asp.fact("place_tag", pid, tag))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(task.tags):
            lines.append(asp.fact("task_tag", tid, tag))
        for region in sorted(task.zone):
            lines.append(asp.fact("task_zone", tid, region))
        for need in sorted(task.needs):
            lines.append(asp.fact("task_needs", tid, need))
    for gid, gear in {g.id: g for g in GEAR}.items():
        lines.append(asp.fact("gear", gid))
        for region in sorted(gear.covers):
            lines.append(asp.fact("gear_covers", gid, region))
        for tag in sorted(gear.guards):
            lines.append(asp.fact("gear_guards", gid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Task) :- place(Place), task(Task), place_tag(Place,Tag), task_tag(Task,Tag).
need_fix(Task,Gear) :- task(Task), gear(Gear), task_needs(Task,Need), gear_guards(Gear,Need).
covers_task(Task,Gear) :- task(Task), gear(Gear), task_zone(Task,R), gear_covers(Gear,R), need_fix(Task,Gear).
valid_story(Place,Task,Gear) :- valid(Place,Task), covers_task(Task,Gear).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming cadet story world with inner monologue.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--hero")
    ap.add_argument("--mentor", choices=sorted({m for m in MENTOR_NAMES}))
    ap.add_argument("--mood", choices=MOODS)
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
    combos = valid_combos()
    if args.place and args.task and not reasonableness_gate(args.place, args.task):
        raise StoryError("That task does not fit that place.")
    filtered = [c for c in combos if (not args.place or c[0] == args.place) and (not args.task or c[1] == args.task)]
    if not filtered:
        raise StoryError("No valid story matches those options.")
    place, task = rng.choice(filtered)
    hero = args.hero or rng.choice(HERO_NAMES)
    mentor = args.mentor or rng.choice(MENTOR_NAMES)
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(place=place, task=task, hero=hero, mentor=mentor, mood=mood)


def _do_task(world: World, hero: Entity, task: Task, gear: Optional[Entity], narrate: bool = True) -> None:
    hero.meters[task.id] = hero.meters.get(task.id, 0.0) + 1.0
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1.0
    if gear:
        gear.worn_by = hero.id
    if narrate:
        world.say(f"{hero.id} took a breath and started {task.gerund}.")


def generate_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    world = World(place)
    hero = world.add(Entity(params.hero, kind="character", type="cadet", label=params.hero))
    mentor = world.add(Entity(params.mentor, kind="character", type="mentor", label=params.mentor))
    gear_def = pick_gear(task)
    gear = None
    if gear_def:
        gear = world.add(Entity(gear_def.id, type="gear", label=gear_def.label, plural=gear_def.plural))
        gear.covers = set(gear_def.covers)  # type: ignore[attr-defined]

    hero.memes.update(nervous=1.0, kindness=1.0, hope=1.0)
    mentor.memes.update(warmth=1.0)

    world.say(f"{hero.id} was a cadet at {place.label}.")
    world.say(f"{hero.id} felt {params.mood}, because {task.cue}.")
    world.say(f"Inside {hero.id}'s head, a small voice said, \"You can do this one careful step at a time.\"")
    world.para()
    world.say(f"At {place.label}, {task.cue}. {hero.id} wanted to {task.verb}, but {hero.pronoun('possessive')} hands were shaking.")
    world.say(f"{hero.id}'s inner monologue whispered, \"Slow down. Look closely. Help first.\"")
    if gear:
        world.say(f"{mentor.id} smiled and said, \"How about we {gear_def.offer}?\"")
        world.say(f"{hero.id} listened to the quiet thought in {hero.pronoun('possessive')} head and nodded.")
        world.say(f"They {gear_def.ending}, and {hero.id} could work without making a mess.")
    else:
        world.say(f"{mentor.id} stayed beside {hero.id} and reminded {hero.id} to use slow hands.")
    world.para()
    _do_task(world, hero, task, gear, narrate=False)
    hero.memes["nervous"] = max(0.0, hero.memes["nervous"] - 1.0)
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    if gear:
        world.say(f"Soon {hero.id} was {task.gerund}, and {hero.id} smiled because the task looked gentle and neat.")
    else:
        world.say(f"Soon {hero.id} finished the work carefully, and the place stayed calm.")
    world.say(f"{mentor.id} said, \"That was thoughtful.\"")
    world.say(f"{hero.id} thought, \"I was scared, but kindness made my hands steadier.\"")
    world.say(f"By the end, {hero.id} stood taller, and {place.label} felt a little warmer.")
    world.facts.update(hero=hero, mentor=mentor, task=task, gear=gear, place=place, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    place = f["place"]
    return [
        f"Write a heartwarming story about a cadet named {hero.id} at {place.label} who needs to {task.verb}.",
        f"Tell a gentle story where {hero.id}'s inner monologue helps {hero.id} stay calm while {task.gerund}.",
        f"Write a child-friendly story about a cadet, a careful helper, and a small brave decision at {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    task = f["task"]
    gear = f.get("gear")
    place = f["place"]
    qa = [
        QAItem(
            question=f"Who was the cadet in the story?",
            answer=f"The cadet was {hero.id}. {hero.id} worked at {place.label} and kept thinking calmly to help get started.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {place.label}?",
            answer=f"{hero.id} wanted to {task.verb}. The job felt big at first, but {hero.id} kept listening to the quiet inner voice.",
        ),
        QAItem(
            question=f"How did {mentor.id} help {hero.id}?",
            answer=f"{mentor.id} stayed close, spoke kindly, and offered steady help so {hero.id} could keep going without worry.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"What helped {hero.id} do the work carefully?",
            answer=f"{gear.label.capitalize()} helped {hero.id}. With that support, {hero.id} could finish the task neatly and safely.",
        ))
    qa.append(QAItem(
        question=f"How did {hero.id} feel at the end?",
        answer=f"{hero.id} felt proud and calmer at the end, because the work was done and the kindness in the room made everything feel warm.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cadet?",
            answer="A cadet is a person who is learning to do a job or serve in a team, usually by practicing and taking lessons.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking you do in your own mind when you think through a problem or encourage yourself.",
        ),
        QAItem(
            question="What does heartwarming mean?",
            answer="Heartwarming means it makes people feel gentle, happy, and cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="dock", task="signal", hero="Mina", mentor="Captain Vale", mood="nervous"),
    StoryParams(place="garden", task="seedlings", hero="Iris", mentor="Instructor Kestrel", mood="careful"),
    StoryParams(place="classroom", task="map", hero="Noa", mentor="Commander Sun", mood="hopeful"),
    StoryParams(place="hangar", task="toolbox", hero="Etta", mentor="Lieutenant Wren", mood="quiet"),
]


def asp_facts_public() -> str:
    return asp_facts()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = CURATED
    else:
        params_list = []
        seen = set()
        i = 0
        while len(params_list) < args.n and i < args.n * 40 + 40:
            i += 1
            rng = random.Random(base_seed + i)
            try:
                p = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            if p.seed is None:
                p.seed = base_seed + i
            key = (p.place, p.task, p.hero, p.mentor, p.mood)
            if key in seen:
                continue
            seen.add(key)
            params_list.append(p)

    for p in params_list:
        samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


if __name__ == "__main__":
    main()
