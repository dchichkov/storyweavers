#!/usr/bin/env python3
"""
Storyworld: granola, weenie, quest, sharing, conflict, heartwarming.

A small child-facing simulation about two friends on a little quest who argue
over snacks, then find a warm and caring way to share.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    landmark: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    start: str
    turn: str
    finish: str
    need: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    shareable: bool
    messy: bool
    tag: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []
        self.quest_active = False

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.quest_active = self.quest_active
        return w


@dataclass
class StoryParams:
    setting: str
    quest: str
    hero: str
    friend: str
    seed: Optional[int] = None


SETTINGS = {
    "sunny_path": Setting(place="the sunny path", landmark="a little bridge", afford={"quest"}),
    "garden_gate": Setting(place="the garden gate", landmark="a red bench", afford={"quest"}),
    "park_loop": Setting(place="the park path", landmark="a round fountain", afford={"quest"}),
}

QUESTS = {
    "lost_map": Quest(
        id="lost_map",
        goal="find the lost map",
        start="look for the lost map",
        turn="could not agree on what to carry",
        finish="found the map and went home smiling",
        need="a helper",
        reward="a happy finish",
        tags={"quest", "sharing", "conflict", "heartwarming"},
    ),
    "picnic_path": Quest(
        id="picnic_path",
        goal="reach the picnic spot",
        start="walk to the picnic spot",
        turn="wondered who should hold the snack basket",
        finish="arrived just in time for lunch",
        need="a shared snack",
        reward="a cozy lunch",
        tags={"quest", "sharing", "conflict", "heartwarming"},
    ),
}

SNACKS = {
    "granola": Snack(
        id="granola",
        label="granola",
        phrase="a crunchy granola bar",
        shareable=True,
        messy=False,
        tag="granola",
    ),
    "weenie": Snack(
        id="weenie",
        label="weenie",
        phrase="a warm weenie in a bun",
        shareable=True,
        messy=True,
        tag="weenie",
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Lena", "Mila", "Ivy", "Ruby"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Theo", "Finn", "Leo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming quest storyworld with granola and weenie.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(s, q) for s in SETTINGS for q in QUESTS]


def reasonableness_gate(setting: str, quest: str) -> None:
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if "quest" not in SETTINGS[setting].afford:
        raise StoryError("That setting does not support a quest.")
    if not QUESTS[quest].shareable if False else False:
        raise StoryError("Invalid quest.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    return StoryParams(setting=setting, quest=quest, hero=hero, friend=friend)


def _init_char(world: World, name: str, gender: str) -> Entity:
    return world.add(Entity(id=name, kind="character", type=gender, label=name, meters={"tired": 0.0}, memes={"joy": 0.0, "care": 0.0, "conflict": 0.0, "sharing": 0.0}))


def _narrate_intro(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    world.say(f"One day, {hero.id} and {friend.id} went to {world.setting.place} near {world.setting.landmark}.")
    world.say(f"They were on a little {quest.goal} quest, and both of them wanted to help.")


def _narrate_snacks(world: World, hero: Entity, friend: Entity) -> None:
    world.say(f"{hero.id} carried {SNACKS['granola'].phrase}, and {friend.id} carried {SNACKS['weenie'].phrase}.")
    world.say("The snacks smelled nice, and both friends felt proud of their careful little lunch.")


def _cause_conflict(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    hero.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    hero.memes["conflict"] += 1
    friend.memes["conflict"] += 1
    world.say(f"Then the quest turned tricky, because they {quest.turn}.")
    world.say(f"{hero.id} wanted the granola bar, and {friend.id} wanted the weenie, so they both frowned.")


def _resolve(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    hero.memes["conflict"] = 0.0
    friend.memes["conflict"] = 0.0
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(f"After a tiny pause, {hero.id} broke the granola bar in half and gave one piece to {friend.id}.")
    world.say(f"{friend.id} smiled and offered the weenie right back, so they shared both snacks together.")
    world.say("That made the path feel warm and friendly again.")
    world.say(f"At the end, they {world.facts['quest'].finish}.")


def generate_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    world = World(setting)
    hero_gender = "girl" if params.hero in GIRL_NAMES else "boy"
    friend_gender = "girl" if params.friend in GIRL_NAMES else "boy"
    hero = _init_char(world, params.hero, hero_gender)
    friend = _init_char(world, params.friend, friend_gender)
    world.facts["quest"] = quest
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["snack1"] = SNACKS["granola"]
    world.facts["snack2"] = SNACKS["weenie"]

    _narrate_intro(world, hero, friend, quest)
    world.para()
    _narrate_snacks(world, hero, friend)
    world.para()
    _cause_conflict(world, hero, friend, quest)
    world.para()
    _resolve(world, hero, friend)
    return world


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    return [
        f"Write a heartwarming story about a small quest with granola and a weenie.",
        f"Tell a child-friendly story where two friends disagree during a {q.goal} quest and then learn to share.",
        f"Write a gentle story about sharing snacks, conflict, and a happy ending on a quest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    quest: Quest = world.facts["quest"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {friend.id} go on their quest?",
            answer=f"They went to {world.setting.place} near {world.setting.landmark}.",
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} want to do on the quest?",
            answer=f"They wanted to {quest.goal}, and they both tried to help.",
        ),
        QAItem(
            question="What caused the conflict between the two friends?",
            answer="They could not agree on the snacks, so both of them got grumpy for a moment.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer="They shared the granola and the weenie instead of fighting about them.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is granola?",
            answer="Granola is a crunchy snack made from oats, nuts, and other tasty bits.",
        ),
        QAItem(
            question="What is a weenie?",
            answer="A weenie is a small sausage, often eaten in a bun as a simple snack or meal.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you.",
        ),
        QAItem(
            question="Why can conflict happen?",
            answer="Conflict can happen when people want the same thing and do not agree right away.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"setting={world.setting.place}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_story(S,Q) :- setting(S), quest(Q).
valid_story(S,Q) :- quest_story(S,Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python:", sorted(py))
    print("clingo:", sorted(asp_set))
    return 1


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="sunny_path", quest="lost_map", hero="Maya", friend="Owen"),
    StoryParams(setting="garden_gate", quest="picnic_path", hero="Leo", friend="Nina"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
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
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
