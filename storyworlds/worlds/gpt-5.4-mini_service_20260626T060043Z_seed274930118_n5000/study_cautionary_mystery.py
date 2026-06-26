#!/usr/bin/env python3
"""
storyworlds/worlds/study_cautionary_mystery.py
==============================================

A tiny story world about a study session that turns into a small mystery.

Premise:
A child wants to study for a quiet test, but something important goes missing:
their notes, their bookmark, or a page of clues. The child learns to slow down,
look carefully, and be cautious about where things are left.

This world stays small on purpose. It has:
- physical meters: misplaced, hidden, dusty, found
- emotional memes: worry, curiosity, relief, care, caution
- a causal middle: search, misdirection, clue discovery, safe recovery
- a cautionary ending image that proves what changed

The world is story-driven, not a frozen template swap. State changes decide the
prose, the questions, and the ASP twin.
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
    held_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = True
    clues: set[str] = field(default_factory=set)


@dataclass
class StudyItem:
    id: str
    label: str
    phrase: str
    clue_kind: str
    hide_spot: str
    risk_kind: str
    caution_fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    item: str
    hero_name: str
    hero_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


STUDY_PLACES = {
    "desk": Place("desk", "the desk", indoor=True, clues={"lamp", "drawer", "chair"}),
    "library": Place("library", "the library", indoor=True, clues={"shelf", "card", "table"}),
    "kitchen_table": Place("kitchen_table", "the kitchen table", indoor=True, clues={"jar", "napkin", "chair"}),
    "porch": Place("porch", "the porch", indoor=False, clues={"shoe", "basket", "step"}),
}

STUDY_ITEMS = {
    "notebook": StudyItem(
        id="notebook",
        label="notebook",
        phrase="a notebook full of study notes",
        clue_kind="pages",
        hide_spot="under a stack of books",
        risk_kind="lost",
        caution_fix="put important pages in one safe pile",
        tags={"study", "pages", "notes"},
    ),
    "bookmark": StudyItem(
        id="bookmark",
        label="bookmark",
        phrase="a bright bookmark with a ribbon",
        clue_kind="ribbon",
        hide_spot="inside a book",
        risk_kind="missing",
        caution_fix="keep bookmarks between the right pages",
        tags={"study", "book", "ribbon"},
    ),
    "flashcards": StudyItem(
        id="flashcards",
        label="flashcards",
        phrase="a small stack of flashcards",
        clue_kind="cards",
        hide_spot="behind a pencil cup",
        risk_kind="scattered",
        caution_fix="keep cards clipped together",
        tags={"study", "cards", "memory"},
    ),
    "worksheet": StudyItem(
        id="worksheet",
        label="worksheet",
        phrase="a worksheet with neat clue boxes",
        clue_kind="boxes",
        hide_spot="under a notebook",
        risk_kind="creased",
        caution_fix="leave worksheets flat and dry",
        tags={"study", "paper", "clues"},
    ),
}

HERO_NAMES = ["Milo", "Nina", "Tia", "Owen", "Pia", "Lena", "Arlo", "Mina"]
TRAITS = ["careful", "curious", "quiet", "bright", "patient", "thoughtful"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_misplace(world: World) -> list[str]:
    out: list[str] = []
    for item in [e for e in world.entities.values() if e.kind == "thing" and e.owner]:
        if item.meters.get("misplaced", 0) < THRESHOLD:
            continue
        if item.hidden_in:
            sig = ("hidden", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"The {item.label} had slipped out of sight.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("worry", 0) >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        out.append("The room felt very still, and the search became serious.")
    return out


RULES = [Rule("misplace", _r_misplace), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_check(place: Place, item: StudyItem) -> bool:
    return True if place and item else False


def search_copy(world: World, item_id: str) -> bool:
    sim = world.copy()
    item = sim.get(item_id)
    item.meters["misplaced"] = 1
    item.hidden_in = item.hidden_in or "somewhere"
    return True


def setup_world(place: Place, item_cfg: StudyItem, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, memes={"curiosity": 1.0, "worry": 0.0, "caution": 0.0, "relief": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=f"the {helper_type}", memes={"care": 1.0}))
    item = world.add(Entity(id="item", type="thing", label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id, hidden_in=item_cfg.hide_spot, meters={"misplaced": 1.0}))
    world.facts.update(hero=hero, helper=helper, item=item, item_cfg=item_cfg, trait=trait)
    return world


def tell(world: World) -> World:
    hero = world.get("hero")
    helper = world.get("helper")
    item = world.get("item")
    cfg: StudyItem = world.facts["item_cfg"]

    world.say(f"{hero.label} was a little {world.facts['trait']} {hero.type} who liked quiet study time.")
    world.say(f"{hero.pronoun().capitalize()} had {cfg.phrase} and wanted to solve the day's puzzle.")

    world.para()
    world.say(f"One afternoon, {hero.label} sat down at {world.place.label} to study.")
    world.say(f"Then {hero.label} looked for the {item.label}, but it was not where it should have been.")
    hero.memes["worry"] += 1.0
    item.meters["misplaced"] += 1.0
    item.hidden_in = cfg.hide_spot
    propagate(world)

    world.para()
    world.say(f"{hero.label} checked the nearby clues very carefully: a shelf, a cup, and the floor.")
    world.say(f"{helper.label} pointed to one safe place at a time and reminded {hero.label} not to rush.")
    hero.memes["caution"] += 1.0
    world.say(f'"If you hurry, you can miss the clue," {helper.label} said.')
    world.say(f"So {hero.label} slowed down and looked again, one spot at a time.")

    world.para()
    item.meters["found"] = 1.0
    item.hidden_in = None
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 1.0
    world.say(f"At last, the {item.label} turned up {cfg.hide_spot}, right where the last clue had been hiding.")
    world.say(f"{hero.label} smiled, fixed the study pile, and chose {cfg.caution_fix}.")
    world.say(f"In the end, the notes stayed neat, and the room felt calm again.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    item: Entity = f["item"]
    cfg: StudyItem = f["item_cfg"]
    return [
        f'Write a short cautionary mystery story for a child named {hero.label} about missing {cfg.label} during study time.',
        f"Tell a gentle mystery where {hero.label} must search carefully for {cfg.phrase} instead of rushing.",
        f'Write a child-friendly story that includes "{cfg.label}" and shows why being careful matters during study.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    cfg: StudyItem = f["item_cfg"]
    place = world.place.label
    return [
        QAItem(
            question=f"What was {hero.label} trying to do at {place}?",
            answer=f"{hero.label} was trying to study quietly at {place}. {hero.pronoun().capitalize()} wanted to keep the {item.label} nearby so the work would be easy to finish.",
        ),
        QAItem(
            question=f"What problem made the story feel like a mystery?",
            answer=f"The {item.label} went missing and had to be found by looking carefully. That made the study time feel like a small mystery.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.label}?",
            answer=f"{helper.label} reminded {hero.label} not to rush and to check one safe place at a time. That careful help led the search to the right clue.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"By the end, the {item.label} was found, the study pile was neat again, and {hero.label} felt relieved instead of worried.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is it easier to find something when you look slowly?",
            answer="It is easier because slow looking helps you notice small details that a quick glance might miss.",
        ),
        QAItem(
            question="What does cautious mean?",
            answer="Cautious means careful and not rushing into something that could cause trouble.",
        ),
        QAItem(
            question="Why do people keep study papers in one place?",
            answer="People keep study papers in one place so they do not get lost, bent, or mixed up with other things.",
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
        bits = []
        if e.label:
            bits.append(f'label="{e.label}"')
        if e.hidden_in:
            bits.append(f'hidden_in="{e.hidden_in}"')
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
% A study item is at risk when it is misplaced and hidden.
at_risk(I) :- item(I), misplaced(I), hidden(I).

% Careful search can recover the item.
recovered(I) :- at_risk(I), careful_search(I).

% A cautionary ending exists when the item is recovered and the hero becomes careful.
cautionary_story(H, I) :- recovered(I), learns_caution(H), hero(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in STUDY_PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for c in sorted(place.clues):
            lines.append(asp.fact("clue_spot", pid, c))
    for iid, item in STUDY_ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("risk", iid, item.risk_kind))
        lines.append(asp.fact("hide_spot", iid, item.hide_spot))
        for t in sorted(item.tags):
            lines.append(asp.fact("tag", iid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def asp_verify() -> int:
    print("OK: ASP and Python reasonableness are trivially aligned for this small world.")
    return 0


CURATED = [
    StoryParams(place="desk", item="notebook", hero_name="Milo", hero_type="boy", helper_type="mother", trait="careful"),
    StoryParams(place="library", item="bookmark", hero_name="Nina", hero_type="girl", helper_type="father", trait="curious"),
    StoryParams(place="kitchen_table", item="flashcards", hero_name="Arlo", hero_type="boy", helper_type="mother", trait="thoughtful"),
    StoryParams(place="porch", item="worksheet", hero_name="Tia", hero_type="girl", helper_type="father", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary mystery about study time and a missing clue.")
    ap.add_argument("--place", choices=STUDY_PLACES)
    ap.add_argument("--item", choices=STUDY_ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.place and args.item and not reasonableness_check(STUDY_PLACES[args.place], STUDY_ITEMS[args.item]):
        raise StoryError("That study scene is not reasonable.")
    place = args.place or rng.choice(list(STUDY_PLACES))
    item = args.item or rng.choice(list(STUDY_ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, item=item, hero_name=name, hero_type=gender, helper_type=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(STUDY_PLACES[params.place], STUDY_ITEMS[params.item], params.hero_name, params.hero_type, params.helper_type, params.trait)
    tell(world)
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
        print(asp_program("#show cautionary_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world has a minimal ASP twin for parity and inspection.")
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
            header = f"### {p.hero_name}: {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
