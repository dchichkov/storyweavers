#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/possess_destine_mystery_to_solve_moral_value.py
================================================================================

A small standalone storyworld built from the seed words "possess" and "destine".

Premise
-------
A child finds a puzzling missing item, follows clues, and learns a moral value
through a twist. The prose is lightly rhyming, child-facing, and driven by a
simulated world state rather than a frozen paragraph.

The domain is intentionally tiny:
- one child
- one caring helper
- one missing prized object
- one misleading clue
- one twist reveal
- one moral ending

The story should feel like a short rhyming mystery: a little problem, a search,
a reveal, and a gentle lesson.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class MysteryThing:
    id: str
    label: str
    use: str
    owner: str
    hidden_place: str
    clue: str
    rhyme_word: str
    value: str
    twist_reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    mystery: str
    place: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    mystery = world.facts.get("mystery_cfg")
    if not mystery:
        return out
    item = world.get("mystery_item")
    if item.meters["hidden"] < THRESHOLD:
        return out
    sig = ("worry", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["worry"] += 1
    world.get("helper").memes["care"] += 1
    out.append(f"The air felt strange, and the little mystery began to sing.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hide_item(world: World, item: Entity) -> None:
    item.meters["hidden"] = 1.0
    propagate(world, narrate=False)


def can_solve(world: World, clue: str, mystery: MysteryThing) -> bool:
    return clue == mystery.clue


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for hero in HEROES:
        for mystery in MYSTERIES:
            if can_solve(World(), mystery.clue, mystery):
                combos.append((hero, mystery.id))
    return combos


def solve_mystery(world: World, hero: Entity, helper: Entity, mystery: MysteryThing) -> None:
    hero.memes["curious"] += 1
    world.say(
        f"{hero.id} found a clue near the {mystery.hidden_place}, and wondered what it could be."
    )
    world.say(
        f'"I shall {mystery.value}," said {helper.id}, "for kind hearts help the day."'
    )
    if mystery.rhyme_word:
        world.say(
            f"The clue had a tune and a tiny rhyme, a trail of {mystery.rhyme_word} through time."
        )
    if mystery.value == "possess":
        world.say(
            f"{hero.id} did not boast, nor brag, nor hiss; {hero.id} learned that sharing is better than possess."
        )
    else:
        world.say(
            f"{hero.id} knew what {mystery.value} meant in the end, and called the helper a truest friend."
        )


def twist(world: World, hero: Entity, helper: Entity, mystery: MysteryThing) -> None:
    world.say(
        f"Then came the twist: the missing thing was not lost at all."
    )
    world.say(
        f"It had been tucked where {helper.id} would place it with care, waiting for a surprise to share."
    )
    world.say(
        f"{helper.id} smiled and showed the hiding spot, and {hero.id} laughed to find the knot."
    )


def moral(world: World, hero: Entity, helper: Entity, mystery: MysteryThing) -> None:
    hero.memes["lesson"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"In the end, {hero.id} learned the golden part: a fair, kind choice makes a happy heart."
    )
    world.say(
        f"When people share what they can and do what they should, even a mystery ends all good."
    )
    world.say(
        f"So {hero.id} kept the lesson close and light: be honest, be gentle, and do what is right."
    )


def tell(params: StoryParams) -> World:
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery choice.")
    if params.hero not in HEROES:
        raise StoryError("Unknown hero choice.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper choice.")
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id=params.parent, kind="character", type="mother", role="parent", label="the parent"))
    mystery = MYSTERIES[params.mystery]
    item = world.add(Entity(id="mystery_item", kind="thing", type="thing", label=mystery.label, attrs={"use": mystery.use}))
    hide_item(world, item)

    world.facts.update(hero=hero, helper=helper, parent=parent, mystery_cfg=mystery, item=item, place=params.place)
    world.say(
        f"At {params.place}, {hero.id} had a wish to {mystery.value}, and a heart that dared to dream."
    )
    world.say(
        f"But the {mystery.label} was gone, or so it did seem."
    )
    world.para()
    world.say(
        f"{helper.id} peered around with a careful eye, while {parent.id} said, \"Let's look nearby.\""
    )
    world.say(
        f"Under the bench by the window, a clue appeared, small and bright, with a little rhyme to steer the night."
    )
    world.para()
    solve_mystery(world, hero, helper, mystery)
    world.para()
    twist(world, hero, helper, mystery)
    world.para()
    moral(world, hero, helper, mystery)
    world.facts["outcome"] = "solved"
    return world


HEROES = {
    "Mina": ("girl",),
    "Noah": ("boy",),
    "Luna": ("girl",),
    "Eli": ("boy",),
}

HELPERS = {
    "Nora": ("girl",),
    "Ari": ("boy",),
    "Maya": ("girl",),
    "Theo": ("boy",),
}

MYSTERIES = {
    "badge": MysteryThing(
        id="badge",
        label="silver badge",
        use="possess",
        owner="Parent",
        hidden_place="toy box",
        clue="badge",
        rhyme_word="glad",
        value="possess",
        twist_reveal="It belonged to the parent all along.",
        tags={"mystery", "possess"},
    ),
    "star": MysteryThing(
        id="star",
        label="paper star",
        use="destine",
        owner="Parent",
        hidden_place="bookshelf",
        clue="star",
        rhyme_word="bright",
        value="destine",
        twist_reveal="It had been saved for a special note.",
        tags={"mystery", "destine"},
    ),
    "song": MysteryThing(
        id="song",
        label="tiny song card",
        use="destine",
        owner="Parent",
        hidden_place="piano bench",
        clue="song",
        rhyme_word="long",
        value="destine",
        twist_reveal="It was meant for a birthday surprise.",
        tags={"mystery", "destine"},
    ),
}


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery_cfg"]
    return [
        f'Write a short rhyming mystery story for a young child that includes the words "{mystery.value}" and "{mystery.id}".',
        f"Tell a gentle rhyming story where {f['hero'].id} follows a clue, solves a small mystery, and learns a moral value.",
        f"Write a surprise story with a twist ending about a missing {mystery.label} that teaches honesty and kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery_cfg"]
    item = f["item"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to figure out?",
            answer=f"{hero.id} was trying to solve the mystery of the missing {mystery.label}. The clue near the hiding place helped {hero.id} see what was really going on.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the missing thing was not really lost. It had been tucked away by {helper.id} with care, so the surprise could be shared at the right time.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer="The story taught a moral value: be honest, be gentle, and share what you can. That kind of choice turns a worry into a happy ending.",
        ),
        QAItem(
            question=f"Did {hero.id} ever get the mystery item back?",
            answer=f"Yes. The {item.label} was found, and the mystery was solved in a kind way. The ending showed that a careful search and a good heart can both matter.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to possess something?",
            answer="To possess something means to own it or hold it as yours. In a story, that word can matter when someone wants to keep something safe and fair.",
        ),
        QAItem(
            question="What does destine mean?",
            answer="Destine means meant for a certain future or purpose. It suggests that something is waiting for the right moment to happen.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle that does not make sense at first. You use clues and thinking to solve it.",
        ),
        QAItem(
            question="Why do stories sometimes use a twist?",
            answer="A twist changes what the reader expects. It makes the story surprising, but it still fits the clues when you look back.",
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story_params() -> list[StoryParams]:
    out = []
    for hero in HEROES:
        for helper in HELPERS:
            if hero == helper:
                continue
            for mystery in MYSTERIES:
                out.append(StoryParams(
                    hero=hero,
                    hero_gender=HEROES[hero][0],
                    helper=helper,
                    helper_gender=HELPERS[helper][0],
                    parent="Parent",
                    mystery=mystery,
                    place="the sunny library",
                ))
    return out


ASP_RULES = r"""
chosen_mystery(M) :- mystery(M).
solved :- clue(C), mystery_clue(C), chosen_mystery(M), mystery_clue(M).
twist :- solved.
moral :- twist.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("mystery_clue", m.clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery/1."))
    return 0 if model is not None else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming mystery storyworld.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--place")
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
    hero = args.hero or rng.choice(list(HEROES))
    helper_choices = [h for h in HELPERS if h != hero]
    helper = args.helper or rng.choice(helper_choices)
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    place = args.place or rng.choice(["the sunny library", "the garden bench", "the cozy hall"])
    return StoryParams(
        hero=hero,
        hero_gender=HEROES[hero][0],
        helper=helper,
        helper_gender=HELPERS[helper][0],
        parent="Parent",
        mystery=mystery,
        place=place,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES:
        raise StoryError("Unknown hero.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show mystery/1."))
        return
    if args.verify:
        sample = generate(StoryParams(
            hero="Mina",
            hero_gender="girl",
            helper="Nora",
            helper_gender="girl",
            parent="Parent",
            mystery="badge",
            place="the sunny library",
        ))
        emit(sample)
        sys.exit(asp_verify())
    if args.asp:
        print("mysteries:", ", ".join(MYSTERIES))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in valid_story_params()[:5]]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
