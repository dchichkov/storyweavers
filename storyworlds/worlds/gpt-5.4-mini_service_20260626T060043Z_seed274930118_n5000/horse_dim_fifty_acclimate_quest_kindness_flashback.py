#!/usr/bin/env python3
"""
storyworlds/worlds/horse_dim_fifty_acclimate_quest_kindness_flashback.py
========================================================================

A small comedy storyworld about a child, a horse-dim place, a fifty-step quest,
kindness, and a flashback that helps someone acclimate.

Premise:
- A child named Pip is asked to lead a tiny pony through a horse-dim hallway.
- The hallway is too dim for the pony at first, so Pip must complete a silly
  quest: gather fifty glow-pebbles and set them along the path.
- Pip remembers a flashback to an older fear of dark corners, then learns how
  kindness, lanterns, and patient practice help everyone acclimate.
- The ending proves what changed: the pony enters the dim place calmly, the
  hallway is brighter, and Pip feels proud instead of worried.

This file follows the storyworld contract:
- stdlib-only script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify compares ASP and Python parity and exercises generated stories
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    dimness: int
    horse_dim: bool
    afford: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    count: int
    shiny: bool = False


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    count: int = 1


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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "horse_dim_hall": Place(
        name="the horse-dim hallway",
        dimness=7,
        horse_dim=True,
        afford={"quest", "acclimate", "kindness", "flashback"},
    ),
    "lantern_room": Place(
        name="the lantern room",
        dimness=3,
        horse_dim=False,
        afford={"quest", "kindness", "flashback"},
    ),
    "stable_corner": Place(
        name="the stable corner",
        dimness=8,
        horse_dim=True,
        afford={"quest", "acclimate", "kindness", "flashback"},
    ),
}

QUESTS = {
    "fifty_pebbles": QuestItem(
        id="fifty_pebbles",
        label="fifty glow-pebbles",
        phrase="fifty glow-pebbles",
        count=50,
        shiny=True,
    ),
    "fifty_buttons": QuestItem(
        id="fifty_buttons",
        label="fifty bright buttons",
        phrase="fifty bright buttons",
        count=50,
        shiny=True,
    ),
}

AIDS = {
    "lanterns": Aid(
        id="lanterns",
        label="lanterns",
        phrase="a row of lanterns",
        helps={"acclimate", "quest"},
        count=5,
    ),
    "cookies": Aid(
        id="cookies",
        label="cookies",
        phrase="two cookies in a pocket tin",
        helps={"kindness", "flashback"},
        count=2,
    ),
}

HERO_NAMES = ["Pip", "Mina", "Otis", "Nia", "Bert"]
HORSE_NAMES = ["Biscuit", "Comet", "Pebble", "Muffin", "Sunny"]
ADULT_NAMES = ["Aunt June", "Mr. Vale", "Mama", "Dad", "Ms. Fern"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    aid: str
    hero_name: str
    horse_name: str
    adult_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is reasonable when the place can host it and the aid helps acclimate.
reasonable(Place, Quest, Aid) :- place(Place), quest(Quest), aid(Aid),
                                  afford(Place, quest), afford(Place, acclimate),
                                  quest_count(Quest, 50),
                                  helps(Aid, acclimate).

% The comedy story requires the horse-dim condition and a kindness beat.
story_ok(Place, Quest, Aid) :- reasonable(Place, Quest, Aid), horse_dim(Place),
                               helps(Aid, kindness).

#show reasonable/3.
#show story_ok/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.horse_dim:
            lines.append(asp.fact("horse_dim", pid))
        for a in sorted(p.afford):
            lines.append(asp.fact("afford", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_count", qid, q.count))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for h in sorted(a.helps):
            lines.append(asp.fact("helps", aid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_models(predicate: str, arity: int) -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(f"#show {predicate}/{arity}."))
    return sorted(set(asp.atoms(model, predicate)))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_models("reasonable", 3))
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for quest_id, quest in QUESTS.items():
            for aid_id, aid in AIDS.items():
                if place.horse_dim and quest.count == 50 and "acclimate" in aid.helps:
                    combos.append((place_id, quest_id, aid_id))
    return combos


def explain_rejection(place_id: str, quest_id: str, aid_id: str) -> str:
    place = PLACES[place_id]
    quest = QUESTS[quest_id]
    aid = AIDS[aid_id]
    if not place.horse_dim:
        return f"(No story: {place.name} is not horse-dim enough for this comedy premise.)"
    if quest.count != 50:
        return "(No story: this story wants a fifty-step quest, so the number must be fifty.)"
    if "acclimate" not in aid.helps:
        return "(No story: the aid must help someone acclimate, or the turn does not work.)"
    return "(No story: this combination does not make a clean quest-to-kindness turn.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _r_acclimate(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    horse = world.get("horse")
    if hero.meters.get("practice", 0.0) >= THRESHOLD and horse.meters.get("calm", 0.0) >= THRESHOLD:
        sig = ("acclimated",)
        if sig not in world.fired:
            world.fired.add(sig)
            _meme(horse, "relief", 1)
            _meme(hero, "pride", 1)
            out.append("The pony settled into the dim hallway like it had always belonged there.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_acclimate,):
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    aid = AIDS[params.aid]
    world = World(place)

    hero = world.add(Entity(id="hero", kind="character", type="boy", label=params.hero_name))
    horse = world.add(Entity(id="horse", kind="animal", type="horse", label=params.horse_name))
    adult = world.add(Entity(id="adult", kind="character", type="adult", label=params.adult_name))

    world.facts.update(hero=hero, horse=horse, adult=adult, place=place, quest=quest, aid=aid)

    # Act 1: setup
    world.say(
        f"{hero.label} had a silly job at {place.name}: help {horse.label} "
        f"acclimate to the horse-dim dark."
    )
    world.say(
        f"The grown-up grinned and handed over a quest: find {quest.phrase} and place them in a line."
    )
    world.say(
        f"{hero.label} laughed, because fifty was a very large number for a very small pair of shoes."
    )

    # Act 2: struggle + flashback
    world.para()
    _meme(hero, "doubt", 1)
    _meme(horse, "nervous", 1)
    world.say(
        f"{horse.label} peeked at the hallway and blinked as if the shadows had told a bad joke."
    )
    world.say(
        f"{hero.label} started the quest, but the first pebble rolled under a bench and made a tiny clink."
    )
    world.say(
        f"That sound tugged a flashback loose: once, {hero.label} had hidden behind a coat rack "
        f"and sworn the dark was full of sneaky socks."
    )
    _meme(hero, "flashback", 1)
    world.say(
        f"{hero.label} snorted at the memory. 'Those socks were probably just socks,' {hero.pronoun()} said."
    )

    # Act 3: kindness and acclimate
    world.para()
    world.say(
        f"The adult brought {aid.phrase}, because kindness is often just the right thing with pockets."
    )
    world.say(
        f"Together they set up lanterns, then counted {quest.count} glow-pebbles one by one."
    )
    _meter(hero, "practice", 1)
    _meter(horse, "calm", 1)
    _meme(hero, "kindness", 1)
    _meme(adult, "kindness", 1)
    world.say(
        f"{hero.label} said, 'We can go slow. The hallway does not have to win.'"
    )
    world.say(
        f"{horse.label} sniffed a lantern, took one brave step, then another, and stopped looking offended."
    )
    propagate(world, narrate=True)
    world.say(
        f"At last, {horse.label} walked through the horse-dim hallway without fuss, "
        f"and {hero.label} finished the fifty-pebble quest with a proud grin."
    )
    world.say(
        f"The dark was still dim, but nobody minded anymore; even the shadows seemed to be trying harder."
    )
    return world


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for young children about a "{f["place"].name}" and a quest for fifty things.',
        f"Tell a comedy about {f['hero'].label} helping {f['horse'].label} acclimate to a horse-dim hallway with kindness.",
        f"Write a short, child-friendly story that includes a flashback, a quest, and fifty glow-pebbles.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    horse = f["horse"]
    adult = f["adult"]
    place = f["place"]
    quest = f["quest"]
    aid = f["aid"]

    return [
        QAItem(
            question=f"What was {hero.label} trying to help {horse.label} do?",
            answer=f"{hero.label} was trying to help {horse.label} acclimate to the horse-dim hallway.",
        ),
        QAItem(
            question=f"What was the quest in the story?",
            answer=f"The quest was to find and place {quest.phrase} in a line.",
        ),
        QAItem(
            question=f"Why did the grown-up bring {aid.phrase}?",
            answer=f"The grown-up brought {aid.phrase} because the story needed kindness and a way to help everyone acclimate.",
        ),
        QAItem(
            question=f"What did {hero.label} remember in the flashback?",
            answer=f"{hero.label} remembered hiding behind a coat rack and feeling sure the dark was full of sneaky socks.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {horse.label} walking through {place.name} calmly and {hero.label} finishing the fifty-pebble quest with a proud grin.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to acclimate?",
            answer="To acclimate means to get used to something gradually, so it feels less strange or scary.",
        ),
        QAItem(
            question="Why can kindness help in a hard moment?",
            answer="Kindness can help because gentle help, patience, and encouragement make a problem feel smaller.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened earlier.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return story_prompts(world)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:6} ({e.kind:8}) {e.label:12} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({sig[0] for sig in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        place="horse_dim_hall",
        quest="fifty_pebbles",
        aid="lanterns",
        hero_name="Pip",
        horse_name="Biscuit",
        adult_name="Aunt June",
    ),
    StoryParams(
        place="stable_corner",
        quest="fifty_buttons",
        aid="cookies",
        hero_name="Mina",
        horse_name="Comet",
        adult_name="Ms. Fern",
    ),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_ids = list(PLACES)
    quest_ids = list(QUESTS)
    aid_ids = list(AIDS)

    if args.place and args.quest and args.aid:
        if (args.place, args.quest, args.aid) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.quest, args.aid))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.aid is None or c[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, quest, aid = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    horse_name = args.horse_name or rng.choice(HORSE_NAMES)
    adult_name = args.adult_name or rng.choice(ADULT_NAMES)
    return StoryParams(place=place, quest=quest, aid=aid, hero_name=hero_name, horse_name=horse_name, adult_name=adult_name)


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy storyworld: horse-dim, fifty, acclimate, quest, kindness, flashback."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--horse-name")
    ap.add_argument("--adult-name")
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


def asp_valid_combos() -> list[tuple]:
    return asp_models("reasonable", 3)


def asp_valid_stories() -> list[tuple]:
    return asp_models("story_ok", 3)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible combos ({len(stories)} story_ok models):\n")
        for place, quest, aid in combos:
            print(f"  {place:16} {quest:16} {aid:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
