#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a temporary ban, gentle foreshadowing,
and a simple change of heart.

Premise:
A child really wants to do something cozy and ordinary, but a parent has put a
temporary ban on it because of a practical concern. Tiny clues in the room and
the child's routine foreshadow why the rule exists. The story turns when the
child handles the problem in a sensible way, the ban is lifted, and the ending
image shows the new, safer routine.

The world is deliberately small:
- one child
- one parent
- one banned activity
- one practical reason
- one workaround / fix

The prose should feel child-facing and slice-of-life, not fairy-tale. The
foreshadowing is the tiny clue that lets the reader understand the ban before
the reveal.
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
# World data
# ---------------------------------------------------------------------------

@dataclass
class Person:
    id: str
    kind: str = "character"
    role: str = "child"  # child | parent
    label: str = ""
    name: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role == "child":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "he", "object": "him", "possessive": "his"}[case]

    def possessive_name(self) -> str:
        return f"{self.name}'s"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    object_phrase: str
    place_phrase: str
    trigger: str
    ban_reason: str
    tiny_clue: str
    fix_action: str
    ending_image: str
    keyword: str


@dataclass
class HouseholdItem:
    id: str
    label: str
    phrase: str
    owner: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    child: Person
    parent: Person
    activity: Activity
    banned: bool = True
    clue_seen: bool = False
    fix_done: bool = False
    items: dict[str, HouseholdItem] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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

CHILD_NAMES = ["Mina", "Pico", "Luna", "Sami", "Tessa", "Nico", "Iris", "Owen"]
PARENT_NAMES = ["Mom", "Dad"]

ACTIVITIES = {
    "cookies": Activity(
        id="cookies",
        verb="have a cookie",
        gerund="snacking on cookies",
        object_phrase="a little plate of cookies",
        place_phrase="at the kitchen table",
        trigger="the jar was almost empty",
        ban_reason="it was nearly time for dinner",
        tiny_clue="the cookie jar sat high on the shelf, and only three crumbs were left on the plate",
        fix_action="washed their hands, set out a fresh plate, and waited until after dinner",
        ending_image="the jar stayed closed until the table was ready",
        keyword="cookie",
    ),
    "screen": Activity(
        id="screen",
        verb="watch a show",
        gerund="watching shows",
        object_phrase="the bright tablet",
        place_phrase="on the couch",
        trigger="the battery was low and the room was getting sleepy",
        ban_reason="their eyes needed a rest",
        tiny_clue="the tablet's battery bar glowed red, and the charger already waited by the sofa",
        fix_action="plugged in the charger and picked a picture book instead",
        ending_image="the tablet rested on its charger like it knew the rule too",
        keyword="tablet",
    ),
    "muddy_shoes": Activity(
        id="muddy_shoes",
        verb="run outside with muddy shoes",
        gerund="dashing around in muddy shoes",
        object_phrase="the favorite shoes by the door",
        place_phrase="in the hallway",
        trigger="rain had left the steps slick and brown",
        ban_reason="the floor had just been swept clean",
        tiny_clue="a wet towel waited by the mat, and a row of clean footprints ended at the door",
        fix_action="changed into slippers and left the muddy shoes on the mat",
        ending_image="the clean floor shone again beside the doorway",
        keyword="shoes",
    ),
    "bell": Activity(
        id="bell",
        verb="ring the little bell",
        gerund="playing with the bell",
        object_phrase="the shiny doorbell toy",
        place_phrase="by the front window",
        trigger="the baby across the hall was napping",
        ban_reason="quiet time was still going on",
        tiny_clue="a tiny note on the fridge said QUIET TIME, and even the cat was curled up asleep",
        fix_action="waited until nap time ended and then rang it once, very softly",
        ending_image="the hallway stayed calm, and later the bell made one happy ding",
        keyword="bell",
    ),
}

SETTINGS = {
    "apartment": "their apartment",
    "house": "their house",
    "kitchen": "the kitchen",
    "living_room": "the living room",
}

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    child_name: str
    parent_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid if an activity is banned for a practical reason,
% the child notices a clue, and the child finds a reasonable fix.
valid_story(P, A) :- place(P), activity(A), banned(A), practical(A), clue(A), fix(A).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES.values():
        lines.append(asp.fact("activity", a.id))
        lines.append(asp.fact("banned", a.id))
        lines.append(asp.fact("practical", a.id))
        lines.append(asp.fact("clue", a.id))
        lines.append(asp.fact("fix", a.id))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set((p, a) for p in SETTINGS for a in ACTIVITIES)
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid story pairs.")
        return 0
    print("Mismatch between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1

# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    activity = ACTIVITIES[params.activity]
    child = Person(id=params.child_name, role="child", label="the child", name=params.child_name)
    parent = Person(id=params.parent_name, role="parent", label="the parent", name=params.parent_name)
    world = World(child=child, parent=parent, activity=activity)
    world.items["plate"] = HouseholdItem(id="plate", label="plate", phrase="a little plate", owner=parent.id)
    world.items["tablet"] = HouseholdItem(id="tablet", label="tablet", phrase="the bright tablet", owner=child.id)
    world.items["shoes"] = HouseholdItem(id="shoes", label="shoes", phrase="the favorite shoes", owner=child.id)
    world.facts.update(
        place=params.place,
        activity=activity,
        child=child,
        parent=parent,
        banned=True,
        clue=activity.tiny_clue,
        fix=activity.fix_action,
    )
    return world

def narrate_intro(world: World) -> None:
    c, p, a = world.child, world.parent, world.activity
    world.say(f"{c.name} was a small, busy child who liked ordinary days to feel special.")
    world.say(f"{c.pronoun().capitalize()} wanted to {a.verb}, especially {a.place_phrase}.")
    world.say(f"But {p.name} had put a ban on it for now because {a.ban_reason}.")

def narrate_foreshadow(world: World) -> None:
    a = world.activity
    world.para()
    world.say(f"There were little clues all around {SETTINGS['kitchen'] if world.facts.get('place') == 'kitchen' else 'home'}: {a.tiny_clue}.")
    world.say(f"{world.child.name} noticed the clue and guessed the rule was not random at all.")
    world.clue_seen = True

def narrate_conflict(world: World) -> None:
    c, p, a = world.child, world.parent, world.activity
    world.para()
    world.say(f"{c.name} still wanted to {a.verb}.")
    world.say(f"{p.name} gently shook {p.pronoun('possessive')} head and reminded {c.name} about the ban.")
    world.say(f"For a moment, {c.name} felt a little sulky, because wanting something and waiting for it are not the same thing.")

def narrate_turn(world: World) -> None:
    c, p, a = world.child, world.parent, world.activity
    world.para()
    world.say(f"Then {c.name} had an idea.")
    world.say(f"Instead of pushing the rule aside, {c.name} did the sensible thing: {a.fix_action}.")
    world.fix_done = True
    world.banned = False
    world.say(f"{p.name} smiled, because that was exactly the kind of careful choice {p.name} had hoped for.")

def narrate_resolution(world: World) -> None:
    c, p, a = world.child, world.parent, world.activity
    world.para()
    world.say(f"With the problem handled, the ban could be lifted.")
    world.say(f"At last, {c.name} got to {a.verb}, and it felt nicer because {c.name} had waited patiently first.")
    world.say(f"By the end, {a.ending_image}, and {p.name} looked pleased to see the day back in its easy, peaceful rhythm.")

def generate_world(params: StoryParams) -> World:
    world = build_world(params)
    narrate_intro(world)
    narrate_foreshadow(world)
    narrate_conflict(world)
    narrate_turn(world)
    narrate_resolution(world)
    return world

# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    a = world.activity
    c = world.child
    p = world.parent
    place = world.facts["place"]
    return [
        f"Write a slice-of-life story about {c.name} at {SETTINGS.get(place, place)} where {p.name} has banned {a.verb} for a practical reason.",
        f"Tell a gentle story with foreshadowing: include the clue that explains why {c.name} cannot {a.verb} right away.",
        f"Write a short child-friendly story where a temporary ban is lifted after {c.name} makes a sensible choice.",
    ]

def story_qa(world: World) -> list[QAItem]:
    c, p, a = world.child, world.parent, world.activity
    return [
        QAItem(
            question=f"Why did {p.name} ban {c.name} from {a.verb} at first?",
            answer=f"{p.name} banned it because {a.ban_reason}. It was a practical rule, not a mean one.",
        ),
        QAItem(
            question=f"What clue foreshadowed the reason for the ban?",
            answer=f"The clue was that {a.tiny_clue}. That helped explain why the rule mattered.",
        ),
        QAItem(
            question=f"What did {c.name} do instead of ignoring the ban?",
            answer=f"{c.name} chose the careful fix: {a.fix_action}. That showed patience and helped solve the problem.",
        ),
        QAItem(
            question=f"How did the story end for {c.name}?",
            answer=f"The ban was lifted, and {c.name} got to {a.verb} after handling things the right way.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    a = world.activity
    return [
        QAItem(
            question="What is a ban?",
            answer="A ban is a rule that says something should not happen for a while.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story drops a small clue that hints at something important later.",
        ),
        QAItem(
            question=f"Why might {a.id.replace('_', ' ')} be a bad idea in a home?",
            answer=f"It can be messy, noisy, or tiring depending on the situation, so a parent may ask for a safer or quieter choice first.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a ban and a small foreshadowed fix.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--child-name", dest="child_name")
    ap.add_argument("--parent-name", dest="parent_name")
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

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    activity = args.activity or rng.choice(list(ACTIVITIES.keys()))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    return StoryParams(place=place, activity=activity, child_name=child_name, parent_name=parent_name)

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

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        print(f"child={sample.world.child.name}, parent={sample.world.parent.name}, activity={sample.world.activity.id}")
        print(f"banned={sample.world.banned}, clue_seen={sample.world.clue_seen}, fix_done={sample.world.fix_done}")
    if qa:
        print()
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_stories()
        print(f"{len(pairs)} valid story pairs:")
        for p, a in pairs:
            print(f"  {p} / {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    params_list: list[StoryParams] = []
    if args.all:
        for p in SETTINGS:
            for a in ACTIVITIES:
                params_list.append(StoryParams(place=p, activity=a, child_name="Mina", parent_name="Mom"))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params_list.append(resolve_params(args, rng))

    samples = [generate(p) for p in params_list]

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
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
