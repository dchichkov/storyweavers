#!/usr/bin/env python3
"""
storyworlds/worlds/seek_irritable_solicit_twist_tall_tale.py
=============================================================

A small Tall Tale-style story world about a seeker, an irritable helper,
a solicited clue, and a twist that changes what the search means.

The seed suggests a classic tall tale shape:
- someone seeks a missing thing,
- someone becomes irritable,
- they solicit help or advice,
- a Twist reveals the sought thing was closer than expected,
- the ending proves the change in state.

This world models a little frontier-style search story with a well-placed
twist. It keeps the prose concrete and state-driven: the seeker has a goal,
the helper has a mood, the search consumes time and effort, the clue changes
what they believe, and the resolution changes the emotional and physical state
of the world.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    feature: str
    wide: bool = True


@dataclass
class SearchTask:
    id: str
    verb: str
    gerund: str
    clue_word: str
    effort: str
    misbelief: str
    found_where: str
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    location: str
    surprise_location: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    seeker_name: str
    seeker_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "mesa": Place(name="the mesa", feature="a red cliff path"),
    "canyon": Place(name="the canyon", feature="a long echoing gulch"),
    "riverbend": Place(name="the river bend", feature="a muddy bank"),
    "prairie": Place(name="the prairie", feature="a wind-brushed stretch of grass"),
    "town": Place(name="the little town", feature="a crooked main street"),
}

TASKS = {
    "seek_star": SearchTask(
        id="seek_star",
        verb="seek the lost star lantern",
        gerund="seeking the lost star lantern",
        clue_word="star",
        effort="searched high and low",
        misbelief="it had slipped beyond the far ridge",
        found_where="in the wagon all along",
        twist="the lantern was already packed under a quilt",
        tags={"seek", "star", "lantern", "twist"},
    ),
    "seek_calf": SearchTask(
        id="seek_calf",
        verb="seek the runaway calf",
        gerund="seeking the runaway calf",
        clue_word="calf",
        effort="followed tracks and hoofprints",
        misbelief="it had wandered clear off the map",
        found_where="behind the water trough",
        twist="the calf was sleeping in the shade near home",
        tags={"seek", "calf", "twist"},
    ),
    "seek_hat": SearchTask(
        id="seek_hat",
        verb="seek the missing hat",
        gerund="seeking the missing hat",
        clue_word="hat",
        effort="looked under fences and barrels",
        misbelief="a windstorm had carried it to another county",
        found_where="on the seeker's own head",
        twist="the hat was perched on the seeker all along",
        tags={"seek", "hat", "twist"},
    ),
    "seek_song": SearchTask(
        id="seek_song",
        verb="seek the old river song",
        gerund="seeking the old river song",
        clue_word="song",
        effort="asked the whole town for a clue",
        misbelief="only the oldest folks knew it anymore",
        found_where="inside the helper's humming",
        twist="the song was hidden in the helper's own humming",
        tags={"seek", "song", "twist"},
    ),
}

PRIZES = {
    "lantern": Prize(
        id="lantern",
        label="star lantern",
        phrase="a shiny star lantern",
        location="wagon",
        surprise_location="wagon",
    ),
    "calf": Prize(
        id="calf",
        label="calf",
        phrase="a small runaway calf",
        location="field",
        surprise_location="water trough",
    ),
    "hat": Prize(
        id="hat",
        label="hat",
        phrase="a tall hat with a bright band",
        location="head",
        surprise_location="head",
    ),
    "song": Prize(
        id="song",
        label="song",
        phrase="an old river song",
        location="mouth",
        surprise_location="humming",
    ),
}


SEEKER_NAMES = ["Clara", "Mose", "June", "Toby", "Nell", "Eli", "Ruby", "Hank"]
HELPER_NAMES = ["Dot", "Jeb", "Martha", "Silas", "Ivy", "Cal", "Pru", "Orrin"]
SEEKER_TYPES = ["girl", "boy"]
HELPER_TYPES = ["woman", "man", "aunt", "uncle"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> tuple[World, Entity, Entity, SearchTask, Prize]:
    world = World(PLACES[params.place])
    seeker = world.add(Entity(
        id=params.seeker_name, kind="character", type=params.seeker_type, label=params.seeker_name
    ))
    helper = world.add(Entity(
        id=params.helper_name, kind="character", type=params.helper_type, label=params.helper_name
    ))
    task = TASKS[params.task]
    prize = PRIZES[params.prize]
    target = world.add(Entity(
        id=prize.id,
        kind="thing",
        type=prize.id,
        label=prize.label,
        phrase=prize.phrase,
        owner=seeker.id,
        location=prize.location,
    ))
    world.facts.update(seeker=seeker, helper=helper, task=task, prize=target)
    return world, seeker, helper, task, target


def intro(world: World, seeker: Entity, task: SearchTask, prize: Entity) -> None:
    world.say(
        f"{seeker.id} was the sort of child who could seek a clue the way a hound seeks a trail, "
        f"and that day {seeker.pronoun()} was after {prize.phrase}."
    )
    world.say(
        f"{seeker.pronoun().capitalize()} loved {task.gerund}, especially when the world looked big enough "
        f"to hide a whole secret."
    )


def trouble(world: World, seeker: Entity, helper: Entity, task: SearchTask, prize: Entity) -> None:
    seeker.memes["determination"] = seeker.memes.get("determination", 0) + 1
    helper.memes["irritable"] = helper.memes.get("irritable", 0) + 1
    world.say(
        f"At {world.place.name}, {seeker.id} {task.effort} while {helper.id} grew irritable from the long day."
    )
    world.say(
        f"{helper.id} sighed, stomped once, and said that the thing was probably {task.misbelief}."
    )


def solicit(world: World, seeker: Entity, helper: Entity, task: SearchTask) -> None:
    seeker.memes["hope"] = seeker.memes.get("hope", 0) + 1
    world.say(
        f"Still, {seeker.id} decided to solicit {helper.id} for one more idea."
    )
    world.say(
        f'"If you know anything about {task.clue_word}, tell me plain," {seeker.id} said, '
        f"and {helper.id} narrowed {helper.pronoun('possessive')} eyes like a gate latch in a storm."
    )


def twist(world: World, seeker: Entity, helper: Entity, task: SearchTask, prize: Entity) -> None:
    helper.memes["irritable"] = max(helper.memes.get("irritable", 0) - 1, 0)
    seeker.memes["surprise"] = seeker.memes.get("surprise", 0) + 1
    world.say(
        f"Then came the Twist: {task.twist}."
    )
    if task.id == "seek_hat":
        prize.location = "head"
        world.say(
            f"{seeker.id} reached up and found the hat resting right where the sun could see it."
        )
    elif task.id == "seek_calf":
        prize.location = "water trough"
        world.say(
            f"{seeker.id} peeked behind the water trough and found the calf curled up like a sleepy cookie."
        )
    elif task.id == "seek_star":
        prize.location = "wagon"
        world.say(
            f"{seeker.id} lifted the quilt in the wagon and there it was, shining like a lamp in a pocket of night."
        )
    else:
        prize.location = "humming"
        world.say(
            f"{seeker.id} listened to {helper.id} hum and heard the old song hiding inside the tune."
        )


def resolution(world: World, seeker: Entity, helper: Entity, task: SearchTask, prize: Entity) -> None:
    seeker.memes["joy"] = seeker.memes.get("joy", 0) + 1
    helper.memes["irritable"] = 0
    world.para()
    if task.id == "seek_hat":
        end = f"{seeker.id} tipped {prize.label} with a grin and laughed at {prize.pronoun('possessive')} own forgetfulness."
    elif task.id == "seek_calf":
        end = f"{seeker.id} led the calf home, and the little beast followed like it had been invited to supper."
    elif task.id == "seek_star":
        end = f"{seeker.id} carried the star lantern into the dusk, and the whole wagon camp looked brighter for it."
    else:
        end = f"{seeker.id} learned the song by heart, and soon the whole town was humming it on the wind."
    world.say(
        f"{helper.id}'s irritable face softened, because the search had ended with the thing found and the air made light again."
    )
    world.say(end)


def tell_story(params: StoryParams) -> World:
    world, seeker, helper, task, prize = setup_world(params)
    intro(world, seeker, task, prize)
    world.para()
    trouble(world, seeker, helper, task, prize)
    solicit(world, seeker, helper, task)
    twist(world, seeker, helper, task, prize)
    resolution(world, seeker, helper, task, prize)
    world.facts.update(
        seeker=seeker,
        helper=helper,
        task=task,
        prize=prize,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    task = f["task"]
    prize = f["prize"]
    return [
        f'Write a Tall Tale story about a child who will {task.verb}, gets an irritable helper, '
        f'and must solicit a clue that leads to a twist.',
        f"Tell a big, playful story where {seeker.id} asks {helper.id} for help finding {prize.label}, "
        f"and the answer turns out to be closer than anyone thought.",
        f'Write a short frontier tale using the words "seek", "irritable", and "solicit", '
        f"and end with a surprise that changes the search.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker: Entity = f["seeker"]
    helper: Entity = f["helper"]
    task: SearchTask = f["task"]
    prize: Entity = f["prize"]
    return [
        QAItem(
            question=f"What was {seeker.id} trying to do at {world.place.name}?",
            answer=f"{seeker.id} was trying to {task.verb}, and the whole tale followed that search.",
        ),
        QAItem(
            question=f"Why was {helper.id} irritable?",
            answer=f"{helper.id} was irritable because the day was long, the search went on, and the answer did not come quickly.",
        ),
        QAItem(
            question=f"Why did {seeker.id} solicit {helper.id} for help?",
            answer=f"{seeker.id} solicited {helper.id} because {seeker.pronoun()} still needed a clue about {prize.label}.",
        ),
        QAItem(
            question=f"What was the Twist in the story?",
            answer=f"The Twist was that {task.twist}, so the thing they wanted had been much closer than they thought.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {seeker.id} finding {prize.label}, {helper.id} no longer irritable, and the search turning into relief and laughter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to seek something?",
            answer="To seek something means to look for it carefully because you want to find it.",
        ),
        QAItem(
            question="What does irritable mean?",
            answer="Irritable means cranky or easily bothered, like someone who is tired or has had a hard day.",
        ),
        QAItem(
            question="What does it mean to solicit help?",
            answer="To solicit help means to ask for help or advice.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you thought was happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a seeker can seek a prize at a place and there is a twist.
valid_story(Place, Task, Prize) :- place(Place), task(Task), prize(Prize),
                                  fits(Task, Prize), happens_at(Task, Place).

% The twist should expose that the prize is closer than believed.
twist_ok(Task) :- twist(Task).

% A valid story needs a sought object, an irritable helper, and a solicited clue.
complete(Task) :- seeks(Task), irritable_helper(Task), solicit(Task), twist_ok(Task).

valid_combo(Place, Task, Prize) :- valid_story(Place, Task, Prize), complete(Task).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("seeks", tid))
        lines.append(asp.fact("solicit", tid))
        lines.append(asp.fact("twist", tid))
        lines.append(asp.fact("fits", tid, task.clue_word))
        for tag in sorted(task.tags):
            lines.append(asp.fact("tag", tid, tag))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("fits", prize.id, prize.label))
    for tid in TASKS:
        lines.append(asp.fact("irritable_helper", tid))
    for place in PLACES:
        for tid in TASKS:
            lines.append(asp.fact("happens_at", tid, place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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


# ---------------------------------------------------------------------------
# Reasonableness / validation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for task in TASKS:
            for prize in PRIZES:
                combos.append((place, task, prize))
    return combos


def explain_rejection(msg: str) -> str:
    return f"(No story: {msg})"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    task = args.task or rng.choice(list(TASKS))
    prize = args.prize or rng.choice(list(PRIZES))
    if (place, task, prize) not in valid_combos():
        raise StoryError(explain_rejection("invalid combination"))
    seeker_type = args.seeker_type or rng.choice(SEEKER_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    seeker_name = args.seeker_name or rng.choice(SEEKER_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if seeker_name == helper_name:
        helper_name = helper_name + "y"
    return StoryParams(
        place=place,
        task=task,
        prize=prize,
        seeker_name=seeker_name,
        seeker_type=seeker_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: type={e.type} label={e.label!r} location={e.location!r} "
            f"meters={e.meters} memes={e.memes}"
        )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale story world: seek, irritable, solicit, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--seeker-name")
    ap.add_argument("--seeker-type", choices=SEEKER_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


CURATED = [
    StoryParams(place="mesa", task="seek_hat", prize="hat", seeker_name="Clara", seeker_type="girl", helper_name="Silas", helper_type="man"),
    StoryParams(place="canyon", task="seek_calf", prize="calf", seeker_name="Mose", seeker_type="boy", helper_name="Dot", helper_type="woman"),
    StoryParams(place="riverbend", task="seek_star", prize="lantern", seeker_name="June", seeker_type="girl", helper_name="Jeb", helper_type="uncle"),
    StoryParams(place="town", task="seek_song", prize="song", seeker_name="Toby", seeker_type="boy", helper_name="Martha", helper_type="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos[:20]:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
