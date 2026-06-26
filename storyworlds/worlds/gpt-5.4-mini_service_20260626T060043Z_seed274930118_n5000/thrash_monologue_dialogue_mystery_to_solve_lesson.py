#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thrash_monologue_dialogue_mystery_to_solve_lesson.py
====================================================================================================

A small adventure storyworld about a mystery, a thrash of bad guesses,
dialogue with a helper, and a lesson learned at the end.

Premise:
- A child explorer loses something important during a windy outing.
- The explorer thrashes through a few wrong ideas.
- A friend and a clue help solve the mystery.
- The ending proves the lesson was learned.

This world models physical meters and emotional memes, and includes:
- Dialogue
- Mystery to Solve
- Lesson Learned
- Adventure style with a concrete setting and a causal turn
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    weather: str
    mystery_kind: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Quest:
    id: str
    object_label: str
    object_phrase: str
    object_kind: str
    hiding_place: str
    risky_action: str
    thrash_action: str
    monologue_line: str
    lesson: str


@dataclass
class StoryParams:
    setting: str
    quest: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "harbor": Setting(
        place="the windy harbor",
        weather="windy",
        mystery_kind="lost item",
        clues=["rope knot", "dock shadow", "salt trail"],
    ),
    "forest": Setting(
        place="the pine forest",
        weather="breezy",
        mystery_kind="lost item",
        clues=["pine needles", "bent fern", "crumbled bark"],
    ),
    "cave": Setting(
        place="the mossy cave mouth",
        weather="cool",
        mystery_kind="lost item",
        clues=["wet pebble", "echo spot", "moss smear"],
    ),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        object_label="lantern",
        object_phrase="a small brass lantern",
        object_kind="lantern",
        hiding_place="behind a loose crate",
        risky_action="reach into the dark corner",
        thrash_action="thrash through the dock piles",
        monologue_line="Maybe I dropped it by the crate... no, wait, maybe the gulls carried it off!",
        lesson="Look carefully before you worry.",
    ),
    "map": Quest(
        id="map",
        object_label="map",
        object_phrase="a folded treasure map",
        object_kind="map",
        hiding_place="under a flat stone",
        risky_action="scramble over the sharp rocks",
        thrash_action="thrash around the trail bends",
        monologue_line="The map must be somewhere close, unless the wind played a trick on me!",
        lesson="A calm search finds more than a wild rush.",
    ),
    "compass": Quest(
        id="compass",
        object_label="compass",
        object_phrase="a bright little compass",
        object_kind="compass",
        hiding_place="inside a hollow stump",
        risky_action="push past the thorny brush",
        thrash_action="thrash through the brush",
        monologue_line="My compass cannot truly vanish... can it?",
        lesson="Small clues matter when the answer is hidden.",
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    return [(s, q) for s in SETTINGS for q in QUESTS]


def explain_rejection(setting: str, quest: str) -> str:
    if setting not in SETTINGS or quest not in QUESTS:
        return "(No story: unknown setting or quest.)"
    return ""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a mystery to solve, dialogue, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--trait")
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
    combos = valid_combos()
    if args.setting and args.quest and (args.setting, args.quest) not in combos:
        raise StoryError(explain_rejection(args.setting, args.quest))
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.name or rng.choice(["Mia", "Leo", "Nora", "Theo", "Ava", "Finn"])
    helper_name = args.helper or rng.choice(["Jules", "Pip", "Rae", "Oli", "June", "Kai"])
    trait = args.trait or rng.choice(["curious", "brave", "restless", "clever", "stubborn"])
    return StoryParams(setting=setting, quest=quest, hero_name=hero_name, hero_type=hero_type,
                       helper_name=helper_name, helper_type=helper_type, trait=trait)


def _do_thrashing(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["thrash"] = hero.meters.get("thrash", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(f"{hero.id} started to {quest.thrash_action}, but that only stirred up more worry.")


def _solve_mystery(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    helper.memes["helpfulness"] = helper.memes.get("helpfulness", 0) + 1
    world.say(f'{helper.id} pointed and said, "Look there — I think it went {quest.hiding_place}."')
    world.say(f'{hero.id} blinked, then said, "{quest.monologue_line}"')
    world.say(f"Together they searched the clue trail and found {quest.object_phrase} exactly where the helper guessed.")


def tell(setting: Setting, quest: Quest, hero_name: str, hero_type: str, helper_name: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["friendly", "quick-eyed"]))
    object_ent = world.add(Entity(
        id=quest.id,
        type=quest.object_kind,
        label=quest.object_label,
        phrase=quest.object_phrase,
        owner=hero.id,
        carries=helper.id,
    ))

    world.say(f"{hero.id} was a little {trait} {hero_type} who loved adventure at {setting.place}.")
    world.say(f"One day, {hero.id} noticed that {hero.pronoun('possessive')} {quest.object_label} was missing.")
    world.say(f"{hero.id} and {helper.id} looked under stones, near crates, and beside the clue trail.")
    world.para()
    world.say(f"{hero.id} wanted to {quest.risky_action}, but that felt too wild and too dark.")
    _do_thrashing(world, hero, quest)
    world.say(f"Then {hero.id} whispered a monologue to {hero.pronoun('object')}: \"{quest.monologue_line}\"")
    world.para()
    world.say(f'{helper.id} said, "Slow down. What clue did you see first?"')
    world.say(f'{hero.id} said, "I saw the {setting.clues[0]}. Maybe that means something."')
    _solve_mystery(world, hero, helper, quest)
    world.para()
    world.say(f"{hero.id} smiled and learned the lesson: {quest.lesson}")
    world.say(f"At the end, {hero.id} carried {object_ent.label} home and the wind felt friendly again.")

    world.facts.update(
        hero=hero,
        helper=helper,
        object=object_ent,
        quest=quest,
        setting=setting,
        solved=True,
        lesson=quest.lesson,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    setting = f["setting"]
    return [
        f'Write a short adventure story for a child about {hero.id}, a lost {quest.object_label}, and a mystery to solve at {setting.place}.',
        f'Include dialogue, a worried monologue, and a lesson learned about {quest.lesson.lower()} in a simple adventure tale.',
        f"Tell a story where {hero.id} thrashes in worry, then calms down and solves the mystery with a friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} need to solve at {setting.place}?",
            answer=f"{hero.id} needed to solve the mystery of the missing {quest.object_label}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the search started to feel hard?",
            answer=f"{helper.id} helped {hero.id} by pointing to a clue and searching with patience.",
        ),
        QAItem(
            question=f"What did {hero.id} do before finding the answer?",
            answer=f"{hero.id} thrashed through a few wrong ideas and then slowed down to think.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at the end?",
            answer=f"{hero.id} learned that {quest.lesson.lower()}",
        ),
    ]


WORLD_KNOWLEDGE = {
    "lantern": ("What does a lantern do?", "A lantern gives light so people can see in dark places."),
    "map": ("What is a map?", "A map is a picture that shows where places are and how to get there."),
    "compass": ("What does a compass do?", "A compass helps you find direction."),
    "thrash": ("What does it mean to thrash around?", "To thrash around means to move wildly without control."),
    "lesson": ("What is a lesson?", "A lesson is something useful you learn from what happens."),
    "dialogue": ("What is dialogue?", "Dialogue is when characters talk to each other in a story."),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    q = world.facts["quest"].id
    out = []
    if q in WORLD_KNOWLEDGE:
        out.append(QAItem(*WORLD_KNOWLEDGE[q]))
    out.append(QAItem(*WORLD_KNOWLEDGE["dialogue"]))
    out.append(QAItem(*WORLD_KNOWLEDGE["thrash"]))
    out.append(QAItem(*WORLD_KNOWLEDGE["lesson"]))
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,Q) :- setting(S), quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(setting="harbor", quest="lantern", hero_name="Mia", hero_type="girl",
                    helper_name="Kai", helper_type="boy", trait="curious"),
        StoryParams(setting="forest", quest="map", hero_name="Leo", hero_type="boy",
                    helper_name="June", helper_type="girl", trait="brave"),
        StoryParams(setting="cave", quest="compass", hero_name="Ava", hero_type="girl",
                    helper_name="Pip", helper_type="boy", trait="stubborn"),
    ]


CURATED = build_curated()


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
        params.trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for s, q in asp_valid_combos():
            print(f"  {s:8} {q:8}")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.quest} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
