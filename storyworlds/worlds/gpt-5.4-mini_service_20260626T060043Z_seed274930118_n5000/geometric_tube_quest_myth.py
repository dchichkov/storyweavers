#!/usr/bin/env python3
"""
storyworlds/worlds/geometric_tube_quest_myth.py
================================================

A tiny myth-style storyworld about a quest for a geometric tube: a hero, a
problem, a wise guide, and a change in the world state that ends the story.

The domain is intentionally small and constraint-checked. The hero travels with
a sacred tube whose shape matters: circles can pass through rings, triangles can
fit only certain gates, and the wrong tube cannot complete the quest. The plot
turns when the hero learns how to align the tube with the right ancient marker.

Seed words: geometric, tube
Style: myth
Feature: quest
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    shape: str = ""
    size: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.id in {"Ari", "Mira", "Ila"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    name: str
    place_phrase: str
    ancient_mark: str
    has_gate: bool = True


@dataclass
class Tube:
    label: str
    shape: str
    gloss: str
    fits_mark: set[str]
    sacred: bool = True


@dataclass
class Quest:
    goal: str
    needed_mark: str
    danger: str
    reveal: str
    reward: str


class World:
    def __init__(self, setting: Setting, quest: Quest) -> None:
        self.setting = setting
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "stone_hall": Setting(
        name="stone hall",
        place_phrase="the stone hall",
        ancient_mark="spiral",
    ),
    "sun_temple": Setting(
        name="sun temple",
        place_phrase="the sun temple",
        ancient_mark="circle",
    ),
    "river_cave": Setting(
        name="river cave",
        place_phrase="the river cave",
        ancient_mark="triangle",
    ),
}

QUESTS = {
    "seal_gate": Quest(
        goal="seal the gate",
        needed_mark="circle",
        danger="the gate would stay open",
        reveal="the tube could only seal the gate when its ring matched the mark",
        reward="the hall became quiet again",
    ),
    "wake_spring": Quest(
        goal="wake the spring",
        needed_mark="triangle",
        danger="the spring would remain asleep",
        reveal="the tube had to point at the carved triangle before water could rise",
        reward="clear water sang through the old stones",
    ),
    "find_star_map": Quest(
        goal="find the star map",
        needed_mark="spiral",
        danger="the path would stay confused",
        reveal="the tube had to rest on the spiral stone so the hidden map could appear",
        reward="the path opened like a remembered song",
    ),
}

TUBES = {
    "golden_tube": Tube(label="golden tube", shape="circle", gloss="bright with a gold sheen", fits_mark={"circle"}),
    "blue_tube": Tube(label="blue tube", shape="triangle", gloss="blue as deep dusk", fits_mark={"triangle"}),
    "silver_tube": Tube(label="silver tube", shape="spiral", gloss="silver and old", fits_mark={"spiral"}),
}

HERO_NAMES = ["Ari", "Mira", "Ila", "Rheo", "Talan", "Sera"]
GUIDE_NAMES = ["Nim", "Orin", "Elda", "Pavo"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    tube: str
    hero: str
    guide: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _shape_name(shape: str) -> str:
    return {"circle": "round", "triangle": "triangular", "spiral": "spiraling"}.get(shape, shape)


def build_story(setting: Setting, quest: Quest, tube: Tube, hero_name: str, guide_name: str) -> World:
    world = World(setting, quest)
    hero = world.add(Entity(id=hero_name, kind="character", label=hero_name, location=setting.place_phrase))
    guide = world.add(Entity(id=guide_name, kind="character", label=guide_name, location=setting.place_phrase))
    tube_ent = world.add(Entity(id="tube", kind="thing", label=tube.label, shape=tube.shape, owner=hero.id, carried_by=hero.id, location=setting.place_phrase))

    hero.memes["duty"] = 1.0
    hero.memes["hope"] = 1.0
    guide.memes["watchful"] = 1.0

    world.say(
        f"In {setting.place_phrase}, {hero.id} began a quiet quest to {quest.goal}. "
        f"At {hero.pronoun('possessive')} side shone a {tube.gloss}, a {tube.label} that the elders called sacred."
    )
    world.say(
        f"The old tales said the way would not open by strength alone. "
        f"It would open only when the {tube.label} met the {setting.ancient_mark} mark hidden in the stone."
    )

    world.para()
    world.say(
        f"{guide.id} led {hero.id} deeper into the hall, where the wind sounded like distant drums. "
        f"{hero.id} lifted the {tube.label} and pressed it toward the first carved stone, but the fit was wrong."
    )
    hero.memes["worry"] = 1.0
    world.say(
        f"That meant {quest.danger}, and the old chamber stayed silent."
    )

    world.para()
    world.say(
        f"Then {guide.id} pointed to the ancient {setting.ancient_mark} and whispered, "
        f"\"Not every shape answers every door.\""
    )
    if tube.shape in tube.fits_mark and setting.ancient_mark == quest.needed_mark:
        world.say(
            f"{hero.id} turned the {tube.label} until its {_shape_name(tube.shape)} edge matched the mark. "
            f"The stone gave a soft hum, like a sleeping drum remembering its name."
        )
        hero.memes["hope"] += 1.0
        hero.memes["worry"] = 0.0
        tube_ent.location = setting.ancient_mark
        world.facts["aligned"] = True
        world.say(
            f"At once, {quest.reveal}. {quest.reward}. "
            f"{hero.id} smiled, and {guide.id} bowed to the bright little triumph."
        )
    else:
        world.say(
            f"{hero.id} tried every angle, but the {tube.label} would not answer the mark. "
            f"The quest remained unfinished."
        )
        world.facts["aligned"] = False

    world.facts.update(
        hero=hero,
        guide=guide,
        tube=tube_ent,
        setting=setting,
        quest=quest,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A quest is valid when the tube's shape matches the needed mark.
valid_story(S, Q, T) :- setting(S), quest(Q), tube(T),
                        setting_needs(S, M), tube_fits(T, M),
                        quest_needs(Q, M).

% The turn is successful only when the alignment happens.
aligned(S, Q, T) :- valid_story(S, Q, T).

% A quest is completed when alignment occurs.
completed(S, Q, T) :- aligned(S, Q, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_needs", sid, s.ancient_mark))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_needs", qid, q.needed_mark))
    for tid, t in TUBES.items():
        lines.append(asp.fact("tube", tid))
        lines.append(asp.fact("tube_fits", tid, t.shape))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            for tid, tube in TUBES.items():
                if quest.needed_mark == setting.ancient_mark and tube.shape == quest.needed_mark and tube.shape in tube.fits_mark:
                    combos.append((sid, qid, tid))
    return combos


def explain_rejection(setting: Setting, quest: Quest, tube: Tube) -> str:
    return (
        f"(No story: the {tube.label} is {_shape_name(tube.shape)}, but this quest needs "
        f"the {quest.needed_mark} mark in {setting.place_phrase}. The shapes do not align, "
        f"so the myth cannot resolve honestly.)"
    )


# ---------------------------------------------------------------------------
# Narration / QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth about a quest in {f["setting"].place_phrase} with a {f["tube"].label}.',
        f"Tell a child-friendly legend where {f['hero'].id} must learn why the {f['tube'].label} only works with the right shape.",
        f'Write a simple story using the words "geometric" and "tube" and ending with a quest being completed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    quest: Quest = f["quest"]
    setting: Setting = f["setting"]
    tube: Entity = f["tube"]
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do in {setting.place_phrase}?",
            answer=f"{hero.id} was trying to {quest.goal}. The quest belonged to the old stone place and needed the right shape to finish.",
        ),
        QAItem(
            question=f"Why did the first try with the {tube.label} fail?",
            answer=f"It failed because the {tube.label} did not match the ancient {setting.ancient_mark} mark at first, so the door of the quest stayed closed.",
        ),
        QAItem(
            question=f"Who helped {hero.id} understand the quest?",
            answer=f"{guide.id} helped by pointing out that not every shape answers every door. That hint led {hero.id} to the right alignment.",
        ),
    ]
    if world.facts.get("aligned"):
        qa.append(
            QAItem(
                question=f"How did the quest end?",
                answer=f"{hero.id} matched the {tube.label} to the right mark, the stone hummed, and the quest ended with {quest.reward}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does geometric mean?",
            answer="Geometric means shaped by lines, angles, circles, triangles, and other forms you can draw or build.",
        ),
        QAItem(
            question="What is a tube?",
            answer="A tube is a long hollow shape with an opening inside. It can carry air, water, or little objects through its center.",
        ),
        QAItem(
            question="What is a quest in a myth?",
            answer="A quest is a long search or journey in a story, often where a hero must solve a hard problem or find something special.",
        ),
    ]


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
        bits = []
        if e.shape:
            bits.append(f"shape={e.shape}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic quest about a geometric tube and the right ancient shape.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tube", choices=TUBES)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--guide", choices=GUIDE_NAMES)
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
    combos = [c for c in valid_combos()
              if args.setting in (None, c[0])
              and args.quest in (None, c[1])
              and args.tube in (None, c[2])]
    if not combos:
        if args.setting and args.quest and args.tube:
            raise StoryError(explain_rejection(SETTINGS[args.setting], QUESTS[args.quest], TUBES[args.tube]))
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, tube = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    return StoryParams(setting=setting, quest=quest, tube=tube, hero=hero, guide=guide)


def generate(params: StoryParams) -> StorySample:
    world = build_story(SETTINGS[params.setting], QUESTS[params.quest], TUBES[params.tube], params.hero, params.guide)
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
    StoryParams(setting="sun_temple", quest="seal_gate", tube="golden_tube", hero="Ari", guide="Nim"),
    StoryParams(setting="river_cave", quest="wake_spring", tube="blue_tube", hero="Mira", guide="Elda"),
    StoryParams(setting="stone_hall", quest="find_star_map", tube="silver_tube", hero="Rheo", guide="Orin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.hero}: {p.quest} with {p.tube} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
