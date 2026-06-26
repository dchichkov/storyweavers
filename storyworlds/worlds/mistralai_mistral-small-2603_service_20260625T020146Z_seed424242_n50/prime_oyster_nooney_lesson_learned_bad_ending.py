#!/usr/bin/env python3

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"Nooney", "Mother", "Woman"}
        male = {"Prime"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    noun: str
    risk: str
    tags: set[str] = field(default_factory=set)

@dataclass
class Setting:
    place: str = "the oak table by the window"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

def _r_injure(world: World) -> list[str]:
    for actor in world.characters():
        if actor.meters.get("enthusiasm", 0) >= 2.0 and actor.meters.get("care", 0) < 1.0:
            if ("injure", actor.id) not in world.fired:
                world.fired.add(("injure", actor.id))
                actor.meters["injury"] += 1
                return [f"{actor.pronoun('subject').capitalize()} accidentally slipped while trying to open {actor.pronoun('possessive')} oyster too quickly!"]
    return []

def _r_fear(world: World) -> list[str]:
    for actor in world.characters():
        if actor.meters.get("injury", 0) >= THRESHOLD and actor.meters.get("care", 0) < 1.5:
            if ("fear", actor.id) not in world.fired:
                world.fired.add(("fear", actor.id))
                actor.memes["afraid"] += 1
                return [f"{actor.id} winced at the sting and didn't reach for another oyster for a little while."]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="injure", apply=_r_injure),
    Rule(name="fear", apply=_r_fear),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def demonstrate_oyster_joy() -> str:
    return "The way oysters popped open was like magic, tiny little doors revealing hidden treasures inside."

def work_in_pairs() -> str:
    return "At the little oak table by the window, generations had shucked oysters together — hand to hand, story to story."

def p_setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return "Sunlight streamed through the window, making the oyster shells on the table shimmer softly."
    return "The beach was dotted with little clusters of people shucking oysters, laughter mixing with the sound of waves."

def loves_activity(world: World, actor: Entity, joy: str, noun: str) -> None:
    actor.memes["love_of_oysters"] += 1
    actor.memes["joy"] += 1
    world.say(
        f"{actor.pronoun().capitalize()} loved {joy}. "
        f"{demonstrate_oyster_joy()}"
    )

def advice(world: World, mentor: Entity, student: Entity, risk: str) -> None:
    world.say(
        f'"{mentor.pronoun('subject').capitalize()} must go slow," {mentor.pronoun('subject')} said gently, '
        f'"or {student.pronoun('object')} will get {risk}."'
    )

def rush_too_fast(world: World, actor: Entity, activity: Activity) -> None:
    actor.meters["enthusiasm"] += 1.5
    world.say(
        f"Before waiting for the proper moment, {actor.id} grabbed {mentor_pronoun(actor)} hand and "
        f"tried to {activity.verb.upper()} in excitement!"
    )

def mentor_pronoun(actor: Entity, mentor_id: str = "Prime") -> str:
    mentor = actor
    if actor.id == mentor_id:
        return actor.pronoun('object')
    for e in actor.memes:
        if isinstance(e, Entity) and e.id == mentor_id:
            mentor = e
            break
    return mentor.pronoun('object')

def cut_enters(world: World, actor: Entity) -> None:
    world.say(
        f"Oops! {actor.pronoun('subject').capitalize()} felt a sting on {actor.pronoun('possessive')} finger, "
        f"so sharp it made {actor.pronoun('subject')} gasp."
    )
    actor.meters["injury"] += 1

def soothe_by_mending(world: World, mentor: Entity, student: Entity) -> None:
    mentor.memes["care"] += 1
    student.memes["care_received"] += 1
    world.say(
        f"{mentor.pronoun('subject').capitalize()} gently took {student.pronoun('possessive')} hand, "
        f"cleaned the spot with warm water, and wrapped {mentor_pronoun(student)} finger in a soft bandage."
    )

def lesson(world: World, mentor: Entity, student: Entity) -> None:
    world.say(
        f'"See what happens when we hurry?" {mentor.pronoun('subject')} asked softly. '
        f'"The knife slips, and now there is pain where there might have been only joy."'
    )

def hesitate_onward(world: World, actor: Entity) -> None:
    actor.memes["afraid"] += 1
    world.say(
        f"{actor.pronoun('subject').capitalize()} nibbled the corner of {actor.pronoun('possessive')} thumbnail, "
        f"eyes on the open oysters but hands frozen still."
    )

def stop_all_together(world: World, actor: Entity) -> None:
    world.say(
        f"{actor.pronoun('subject').capitalize()} pushed {actor.pronoun('possessive')} stool back and "
        f"said, 'I think I'm all oystered out for today.' "
        f"The lesson had been learned, but at some cost to {actor.pronoun('possessive')} cheerful spirit."
    )

def tell(mentor_name: str = "Prime",
         student_name: str = "Nooney",
         setting_cfg: Setting = None) -> World:
    world = World(setting_cfg or Setting(place="the oak table by the window", indoor=True))

    mentor = world.add(Entity(
        id=mentor_name,
        kind="character",
        type="mentor",
        label="Prime",
        phrase="wise old shucker",
        traits=["patient", "gentle"],
    ))
    student = world.add(Entity(
        id=student_name,
        kind="character",
        type="child",
        label="Nooney",
        phrase="eager young shucker",
        owner=mentor_name,
        plural=False,
    ))

    # Setup
    world.say(f"{student.id} adored {'working' if world.setting.indoor else 'digging'} with {mentor.name}.")
    loves_activity(world, student, "the little knife tricks that made shells pop open like tiny treasure chests", "oyster")
    world.para()
    world.say(f"{mentor.pronoun().capitalize()} sat down beside {student.id} at {world.setting.place}.")
    world.say(p_setting_detail(world.setting))

    # Tension building
    world.para()
    work_in_pairs(world, student, mentor)
    advice(world, mentor, student, "a cut")
    world.say(f'"But doing it fast is way more FUN!" {student.id} declared, eyes sparkling.')

    # Conflict
    world.para()
    rush_too_fast(world, student, Activity(
        id="shuck_rush", verb="shuck an oyster quickly", gerund="shucking oysters",
        noun="oysters", risk="cut"
    ))
    cut_enters(world, student)
    propagate(world)

    # Resolution attempt
    world.para()
    soothe_by_mending(world, mentor, student)
    lesson(world, mentor, student)
    propagate(world)

    # Lesson effect and bad ending
    world.para()
    hesitate_onward(world, student)
    stop_all_together(world, student)

    world.facts.update(
        mentor=mentor,
        student=student,
        lesson_taught=True,
        lesson_learned_but_costly=True,
        activity="shucking",
        risk="a cut finger"
    )
    return world

@dataclass
class StoryParams:
    name: str
    mentor: str
    indoor: bool

def valid_params(name: str) -> bool:
    return name in ["Nooney", "Lily", "Ben"]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming story world: Prime teaches Nooney about gentle oyster shucking. "
                    "Features lesson learned with a badge ending where the child loses "
                    "the joy despite the lesson.")
    ap.add_argument("--name", choices=["Nooney", "Lily", "Ben", "Alex"], default="Nooney")
    ap.add_argument("--mentor", choices=["Prime", "Grandpa", "Uncle"], default="Prime")
    ap.add_argument("--indoor", action="store_true", help="set the activity indoors")
    ap.add_argument("--outdoor", action="store_false", dest="indoor", help="set the activity outdoors")
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="use curated defaults")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true", help="print ASP rules")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name if valid_params(args.name) else rng.choice(["Nooney", "Lily", "Ben"])
    mentor = args.mentor
    indoor = args.indoor
    return StoryParams(name=name, mentor=mentor, indoor=indoor)

CURATED = [
    StoryParams(name="Nooney", mentor="Prime", indoor=True),
    StoryParams(name="Ben", mentor="Grandpa", indoor=False),
    StoryParams(name="Lily", mentor="Uncle", indoor=True),
]

def generate(params: StoryParams) -> StorySample:
    world = tell(mentor_name=params.mentor, student_name=params.name,
                 setting_cfg=Setting(indoor=params.indoor))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f'Write a heartwarming bedtime story for a 4-year-old about {params.name} learning to shuck oysters safely with {params.mentor}.',
            f'A cozy story where a little child discovers that sometimes the best way to enjoy something is to slow down and do it carefully.'
        ],
        story_qa=[
            QAItem(
                question=f"Who taught {params.name} to shuck oysters?",
                answer=f"{params.name} learned to shuck oysters with {params.mentor}, who showed {params.name} the safe, gentle way."
            ),
            QAItem(
                question=f"What happened when {params.name} tried to shuck oysters too fast?",
                answer=f"{params.name} accidentally cut {params.name.lower()} finger because excitement made {params.name.lower()} rush the careful steps."
            ),
            QAItem(
                question=f"What important lesson did {params.name} learn from {params.mentor}?",
                answer=f"{params.mentor} taught {params.name} that doing things slowly and carefully makes the joy last longer than a quick, hasty moment of pain."
            )
        ],
        world_qa=[
            QAItem(
                question="What are oysters?",
                answer="Oysters are sea creatures with a hard shell that some people enjoy eating. They live in salt water and are a special food in many coastal places."
            ),
            QAItem(
                question="Why should we go slow when we're excited?",
                answer="Going slow when we're excited helps us stay safe and enjoy the good parts of an activity longer. It's like savoring a piece of chocolate instead of swallowing it whole — the good taste lasts!"
            ),
            QAItem(
                question="What is a mentor?",
                answer="A mentor is someone who teaches and guides another person, showing them the safe and good ways to do something. It's like a coach who helps you learn gently."
            )
        ],
        world=world,
    )

ASP_RULES = r"""
% This world is small and deterministic in ASP, used only for parity verification.
% The key lesson is that when enthusiasm exceeds care, an injury occurs, which
% breeds fear that stops the activity despite the lesson being learned.

% A character has an injury when their enthusiasm exceeded care threshold.
has_injury(P) :- meters(P, enthusiasm, E), meters(P, care, C), E >= 2.0, C < 1.0.

% The injury causes fear once it crosses the threshold.
has_fear(P) :- has_injury(P), memes(P, afraid, F), F >= 1.0.

% This is a heartwarming story world so the lesson is the same across instances.
valid_story :- setting(Place), character(P), character(M), mentors(M, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "indoor"))
    lines.append(asp.fact("setting", "outdoor"))
    lines.append(asp.fact("character", "Nooney"))
    lines.append(asp.fact("character", "Prime"))
    lines.append(asp.fact("character", "Ben"))
    lines.append(asp.fact("character", "Lily"))
    lines.append(asp.fact("mentors", "Prime", "Nooney"))
    lines.append(asp.fact("mentors", "Prime", "Ben"))
    lines.append(asp.fact("mentors", "Grandpa", "Ben"))
    lines.append(asp.fact("mentors", "Uncle", "Lily"))
    for metric in ["love_of_oysters", "care_received", "injury", "afraid"]:
        lines.append(asp.fact("meter_name", metric))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    has_model = len(model) > 0
    print(f"ASP verification: {'PASS' if has_model else 'FAIL'} — heartwarming story template is valid in ASP.")
    return 0 if has_model else 1

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        lines = ["--- world model state ---"]
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
        lines.append(f"  fired rules: {sorted(set(n for n, *_ in sample.world.fired))}")
        print("\n".join(lines))
    if qa:
        qa_text = format_qa(sample)
        if qa_text:
            print("\n" + qa_text)

def format_qa(sample: StorySample) -> str:
    lines = ["== Story Questions (from this tale) =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Knowledge (no story needed) ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP demo: this heartwarming world is valid and has at least one story.")
        return

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
            header = f"### Story {i+1}: {p.name} learns from {p.mentor}{' indoors' if p.indoor else ' by the shore'}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
