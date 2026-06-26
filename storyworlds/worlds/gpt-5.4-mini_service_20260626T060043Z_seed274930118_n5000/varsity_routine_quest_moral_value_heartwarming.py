#!/usr/bin/env python3
"""
storyworlds/worlds/varsity_routine_quest_moral_value_heartwarming.py
=====================================================================

A small heartwarming story world about a varsity routine that is interrupted
by a little quest, where a moral value turns the day into a kinder ending.

The seed image for this world:
---
A varsity student has a careful routine before practice. One day, a small quest
appears: someone needs help finding a missing item, or a nervous teammate needs
support. The student must choose between staying on schedule and doing the right
thing. In the end, the routine changes just enough to make room for kindness,
and everyone feels closer.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Routine:
    id: str
    name: str
    steps: list[str]
    finish: str
    calm_gain: float = 1.0


@dataclass
class Quest:
    id: str
    name: str
    verb: str
    object_label: str
    need: str
    moral: str
    helper_item: str = ""


@dataclass
class Value:
    id: str
    label: str
    lesson: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    routine: str
    quest: str
    value: str
    name: str
    gender: str
    friend: str
    seed: Optional[int] = None


SETTINGS = {
    "track": Setting(place="the track", affords={"warmup", "quest"}),
    "gym": Setting(place="the gym", affords={"warmup", "quest"}),
    "field": Setting(place="the field", affords={"warmup", "quest"}),
    "hall": Setting(place="the school hall", affords={"warmup", "quest"}),
}

ROUTINES = {
    "warmup": Routine(
        id="warmup",
        name="varsity warmup routine",
        steps=["tied the laces", "stretched quietly", "counted three deep breaths"],
        finish="felt ready for practice",
        calm_gain=1.0,
    ),
    "drills": Routine(
        id="drills",
        name="varsity drill routine",
        steps=["set the cones", "ran the lines", "checked the timer"],
        finish="felt steady and prepared",
        calm_gain=1.0,
    ),
}

QUESTS = {
    "lost_note": Quest(
        id="lost_note",
        name="the lost note quest",
        verb="find",
        object_label="a folded permission note",
        need="the team trip could not start without it",
        moral="responsibility",
        helper_item="backpack pocket",
    ),
    "quiet_friend": Quest(
        id="quiet_friend",
        name="the quiet-friend quest",
        verb="help",
        object_label="a nervous new teammate",
        need="the new teammate was afraid to join in",
        moral="kindness",
        helper_item="bench seat",
    ),
    "lucky_band": Quest(
        id="lucky_band",
        name="the lucky-band quest",
        verb="return",
        object_label="a lucky wrist band",
        need="its owner was looking worried and small",
        moral="loyalty",
        helper_item="locker door",
    ),
}

VALUES = {
    "responsibility": Value(
        id="responsibility",
        label="responsibility",
        lesson="responsibility means taking care of what someone needs, even when the clock is ticking",
    ),
    "kindness": Value(
        id="kindness",
        label="kindness",
        lesson="kindness means making room in your day for another person's feelings",
    ),
    "loyalty": Value(
        id="loyalty",
        label="loyalty",
        lesson="loyalty means staying helpful to your teammate when they need you most",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Ella", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Milo", "Finn", "Owen"]
FRIENDS = ["teammate", "classmate", "rookie", "friend"]


def reasonableness_ok(routine: Routine, quest: Quest, value: Value) -> bool:
    return bool(routine.steps) and quest.moral == value.id


ASP_RULES = r"""
routine_ok(R) :- routine(R).
quest_ok(Q) :- quest(Q).
value_ok(V) :- value(V).

compatible(R,Q,V) :- routine_ok(R), quest_ok(Q), value_ok(V), quest_moral(Q,V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, r in ROUTINES.items():
        lines.append(asp.fact("routine", rid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_moral", qid, q.moral))
    for vid, v in VALUES.items():
        lines.append(asp.fact("value", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _routine_act(world: World, hero: Entity, routine: Routine) -> None:
    hero.meters["calm"] += routine.calm_gain
    hero.memes["focus"] += 1
    world.say(
        f"Every morning, {hero.id} kept a varsity routine that began with small, careful steps."
    )
    world.say(
        f"{hero.pronoun().capitalize()} {routine.steps[0]}, then {routine.steps[1]}, and finally {routine.steps[2]}."
    )


def _quest_appears(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    hero.memes["duty"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"Just as practice was about to begin, a little quest appeared: {friend.id} needed {quest.object_label}."
    )
    world.say(f"{quest.need.capitalize()}, so the day suddenly felt much bigger than a timetable.")


def _weigh_choice(world: World, hero: Entity, routine: Routine, quest: Quest, value: Value) -> None:
    hero.memes["tension"] += 1
    world.say(
        f"{hero.id} glanced at the clock and worried that stopping would break the whole routine."
    )
    world.say(
        f"But {hero.pronoun('possessive')} heart kept saying that {value.label} mattered more than being perfectly on time."
    )


def _help_friend(world: World, hero: Entity, friend: Entity, quest: Quest, value: Value) -> None:
    friend.memes["worry"] = 0.0
    friend.memes["gratitude"] += 1
    hero.memes["kindness"] += 1
    hero.meters["busy"] += 1
    world.say(
        f"{hero.id} chose to help. {hero.pronoun().capitalize()} looked in the right places, and soon {quest.object_label} turned up."
    )
    world.say(
        f"{friend.id} smiled so wide that the whole hallway seemed warmer."
    )
    world.say(
        f"That was the heart of {value.label}: one careful choice that made another child feel safe."
    )


def _finish(world: World, hero: Entity, routine: Routine, quest: Quest, value: Value) -> None:
    hero.memes["pride"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"After that, {hero.id} still made it back for practice, only now the varsity routine had room for a kinder beginning."
    )
    world.say(
        f"{hero.pronoun().capitalize()} {routine.finish}, and {quest.object_label} was safe where it belonged."
    )
    world.say(
        f"By the end, the day felt gentle and bright, because {value.label} had quietly won."
    )


def tell(setting: Setting, routine: Routine, quest: Quest, value: Value,
         hero_name: str, hero_type: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id="Friend", kind="character", type=friend_type, label="friend"))

    _routine_act(world, hero, routine)
    world.para()
    _quest_appears(world, hero, friend, quest)
    _weigh_choice(world, hero, routine, quest, value)
    world.para()
    _help_friend(world, hero, friend, quest, value)
    _finish(world, hero, routine, quest, value)

    world.facts.update(
        hero=hero,
        friend=friend,
        routine=routine,
        quest=quest,
        value=value,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    value = f["value"]
    return [
        f'Write a heartwarming short story about a varsity student whose routine is interrupted by {quest.name}.',
        f"Tell a gentle story where {hero.id} has to choose between a practice routine and {value.label}.",
        f'Write a child-friendly story with a small quest, a moral value, and a warm ending at {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    value = f["value"]
    friend = f["friend"]
    return [
        QAItem(
            question=f"What kind of student is {hero.id} in the story?",
            answer=f"{hero.id} is a varsity student with a careful routine before practice.",
        ),
        QAItem(
            question=f"What was the little quest that interrupted the day?",
            answer=f"The quest was {quest.name}, and it asked {hero.id} to deal with {quest.object_label}.",
        ),
        QAItem(
            question=f"What moral value helped {hero.id} make the right choice?",
            answer=f"{value.label.capitalize()} helped {hero.id} choose to help {friend.id} first.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} helped with the quest, still returned to practice, and the day ended with a warmer feeling than before.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does varsity mean?",
            answer="Varsity usually means a school's main team, made up of students who train and play for their school.",
        ),
        QAItem(
            question="What is a routine?",
            answer="A routine is a set of steps someone does again and again in the same order.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or mission that takes effort to complete, even if it is small.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good lesson about how to treat people, such as kindness, loyalty, or responsibility.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(self for self, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="gym", routine="warmup", quest="quiet_friend", value="kindness", name="Mina", gender="girl", friend="teammate"),
    StoryParams(place="track", routine="drills", quest="lost_note", value="responsibility", name="Theo", gender="boy", friend="rookie"),
    StoryParams(place="hall", routine="warmup", quest="lucky_band", value="loyalty", name="Ava", gender="girl", friend="friend"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for routine in ROUTINES:
            for quest in QUESTS:
                if QUESTS[quest].moral in VALUES:
                    out.append((place, routine, quest))
    return out


def explain_invalid(quest: Quest, value: Value) -> str:
    return f"(No story: {quest.name} needs the moral value {quest.moral}, not {value.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming varsity routine story world with a small quest and a moral value."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--routine", choices=ROUTINES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend", choices=FRIENDS)
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
    if args.quest and args.value and QUESTS[args.quest].moral != args.value:
        raise StoryError(explain_invalid(QUESTS[args.quest], VALUES[args.value]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.routine is None or c[1] == args.routine)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, routine, quest = rng.choice(sorted(combos))
    value = QUESTS[quest].moral
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(place=place, routine=routine, quest=quest, value=value, name=name, gender=gender, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ROUTINES[params.routine],
        QUESTS[params.quest],
        VALUES[params.value],
        params.name,
        params.gender,
        params.friend,
    )
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
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
            header = f"### {p.name}: {p.routine} / {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
