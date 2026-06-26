#!/usr/bin/env python3
"""
storyworlds/worlds/proclamation_fork_ful_ful_rhyme_lesson_learned_ghost.py
==========================================================================
A small ghost-story world with a proclamation, a fork-ful, rhyme, and a
lesson learned.

Seed tale:
---
On a misty night, a little ghost named Miri floated through the old kitchen
and found a warm berry pie on the table. Miri loved making dramatic
proclamations, so she boomed, "This fork-ful is mine!" The friendly cook
reminded Miri that the pie was for everyone, and that taking without asking
could leave crumbs and tears.

Miri felt embarrassed. Then Miri tried a softer voice and said a rhyming
little line: "If I ask and share, we all get a taste, and nobody ends up in a
sulky waste." The cook smiled, gave Miri a small fork-ful, and everyone shared
the pie. Miri learned that a kind request works better than a spooky decree.

World model:
---
- Entities have physical meters and emotional memes.
- A proclamation can raise boastfulness and tension.
- Trying to snatch a fork-ful without asking can reduce pie and increase worry.
- A gentle apology and shared serving resolve the conflict, proving the lesson.

The story is written as a complete, state-driven ghost tale with a mild rhyme
and an explicit lesson learned image at the end.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "ghost":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old kitchen"
    mood: str = "misty"


@dataclass
class Treat:
    label: str
    phrase: str
    serving: str
    rhyme_word: str
    risk: str


@dataclass
class StoryParams:
    place: str
    treat: str
    ghost_name: str
    cook_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _ghost_raise_boast(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    if ghost.memes.get("boast", 0) >= THRESHOLD and ("boast",) not in world.fired:
        world.fired.add(("boast",))
        ghost.memes["tension"] = ghost.memes.get("tension", 0) + 1
        out.append("The room felt a little chillier after that proclamation.")
    return out


def _snatch_risk(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    treat = world.get("treat")
    cook = world.get("cook")
    if ghost.memes.get("greedy", 0) < THRESHOLD:
        return out
    if treat.meters.get("remaining", 0) <= 0:
        return out
    sig = ("snatch",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treat.meters["remaining"] -= 1
    ghost.memes["guilt"] = ghost.memes.get("guilt", 0) + 1
    cook.memes["worry"] = cook.memes.get("worry", 0) + 1
    out.append("One fork-ful vanished too quickly, and the cook frowned.")
    return out


CAUSAL_RULES = [
    _ghost_raise_boast,
    _snatch_risk,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "kitchen": Setting(place="the old kitchen", mood="misty"),
    "hall": Setting(place="the candlelit hall", mood="foggy"),
    "attic": Setting(place="the attic", mood="quiet"),
}

TREATS = {
    "pie": Treat(
        label="berry pie",
        phrase="a warm berry pie",
        serving="fork-ful",
        rhyme_word="sky",
        risk="crumbly and messy",
    ),
    "pudding": Treat(
        label="vanilla pudding",
        phrase="a bowl of vanilla pudding",
        serving="fork-ful",
        rhyme_word="moon",
        risk="soft and slippery",
    ),
}

GHOST_NAMES = ["Miri", "Lumi", "Pip", "Nova", "Wisp"]
COOK_NAMES = ["Mrs. Lane", "Aunt Dot", "Mr. Finch", "Nina"]


@dataclass
class StoryWorld:
    world: World
    ghost: Entity
    cook: Entity
    treat: Entity
    params: StoryParams


def tell(setting: Setting, treat_cfg: Treat, ghost_name: str, cook_name: str) -> StoryWorld:
    world = World(setting)
    ghost = world.add(Entity(
        id="ghost", kind="character", type="ghost", label=ghost_name,
        meters={"float": 1.0}, memes={"curious": 1.0, "boast": 0.0, "joy": 0.0, "lesson": 0.0},
    ))
    cook = world.add(Entity(
        id="cook", kind="character", type="adult", label=cook_name,
        meters={"care": 1.0}, memes={"worry": 0.0, "kindness": 1.0},
    ))
    treat = world.add(Entity(
        id="treat", kind="thing", type=treat_cfg.label, label=treat_cfg.label,
        phrase=treat_cfg.phrase, owner=cook.id, caretaker=cook.id,
        meters={"remaining": 4.0},
    ))

    # Act 1: setup
    world.say(
        f"On a {setting.mood} night in {setting.place}, {ghost_name} the little ghost "
        f"drifted close to {cook_name}'s table and spotted {treat_cfg.phrase}."
    )
    world.say(
        f"{ghost_name} loved making big proclamations, and the air even hummed when {ghost.pronoun()} began to glow."
    )
    world.say(
        f"{ghost_name} whispered, 'Tonight I want a {treat_cfg.serving} of {treat_cfg.label}.'"
    )

    # Act 2: tension
    world.para()
    ghost.memes["boast"] += 1
    world.say(
        f"Then {ghost_name} boomed, 'I proclaim this {treat_cfg.serving} is mine!'"
    )
    propagate(world)
    ghost.memes["greedy"] = ghost.memes.get("greedy", 0) + 1
    world.say(
        f"{cook_name} blinked and said, 'That pie is for sharing, little ghost. "
        f"If you take a bite without asking, it will end up {treat_cfg.risk}.'"
    )
    propagate(world)

    # Act 3: turn and lesson learned
    world.para()
    ghost.memes["boast"] = 0.0
    ghost.memes["greedy"] = 0.0
    ghost.memes["kindness"] = ghost.memes.get("kindness", 0) + 1
    ghost.memes["lesson"] = 1.0
    cook.memes["worry"] = max(0.0, cook.memes.get("worry", 0.0) - 1.0)
    world.say(
        f"{ghost_name} paused, then said in a softer voice, "
        f"'Please may I have a {treat_cfg.serving}? I do not want to be rude.'"
    )
    world.say(
        f"To make the moment bright, {ghost_name} rhymed, "
        f"'If I ask and share, we all get a taste; no lonely grumps and no pie to waste.'"
    )
    treat.meters["remaining"] -= 1
    ghost.meters["glow"] = ghost.meters.get("glow", 0.0) + 1.0
    ghost.memes["joy"] = ghost.memes.get("joy", 0.0) + 1.0
    world.say(
        f"{cook_name} smiled and sliced a small {treat_cfg.serving} for {ghost_name}. "
        f"Together they shared the rest, and the little ghost learned that a kind request "
        f"works better than a spooky decree."
    )
    world.say(
        f"By the end, the table was warm, the pie was still partly there, and {ghost_name} "
        f"floated away with a happy lesson learned."
    )

    world.facts = {
        "ghost": ghost,
        "cook": cook,
        "treat": treat,
        "setting": setting,
        "treat_cfg": treat_cfg,
        "boast": True,
        "lesson": True,
    }
    return StoryWorld(world=world, ghost=ghost, cook=cook, treat=treat, params=StoryParams(
        place="kitchen" if setting.place == "the old kitchen" else "hall",
        treat="pie" if treat_cfg.label == "berry pie" else "pudding",
        ghost_name=ghost_name,
        cook_name=cook_name,
    ))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for treat in TREATS:
            combos.append((place, treat, "ghost_story"))
    return combos


def generation_prompts(sw: StoryWorld) -> list[str]:
    f = sw.world.facts
    ghost = f["ghost"]
    treat_cfg = f["treat_cfg"]
    return [
        f'Write a gentle ghost story that includes the words "proclamation" and "{treat_cfg.serving}".',
        f"Tell a spooky-but-kind story where {ghost.label} learns a lesson about asking before taking food.",
        f'Write a short children\'s story with a rhyme in it and a happy ending about sharing {treat_cfg.phrase}.',
    ]


def story_qa(sw: StoryWorld) -> list[QAItem]:
    f = sw.world.facts
    ghost = f["ghost"]
    cook = f["cook"]
    treat_cfg = f["treat_cfg"]
    return [
        QAItem(
            question=f"Who made the big proclamation in the story?",
            answer=f"{ghost.label} the little ghost made the big proclamation.",
        ),
        QAItem(
            question=f"What did {ghost.label} want a {treat_cfg.serving} of?",
            answer=f"{ghost.label} wanted a {treat_cfg.serving} of {treat_cfg.label}.",
        ),
        QAItem(
            question=f"What lesson did {ghost.label} learn by the end?",
            answer=f"{ghost.label} learned that asking politely and sharing is better than making a spooky decree.",
        ),
        QAItem(
            question=f"Who helped keep the sharing fair?",
            answer=f"{cook.label} helped by reminding {ghost.label} to ask first and share kindly.",
        ),
    ]


def world_knowledge_qa(sw: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a proclamation?",
            answer="A proclamation is a big, formal announcement spoken so everyone can hear it.",
        ),
        QAItem(
            question="What is a fork-ful?",
            answer="A fork-ful is the amount of food that fits on one fork.",
        ),
        QAItem(
            question="Why do people share dessert?",
            answer="People share dessert so everyone can have a taste and so one person does not take everything.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand how to act better after something happens.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def explain_rejection(place: str, treat: str) -> str:
    return f"(No story: the requested {place}/{treat} combination is not a valid ghost tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(SETTINGS))
    treat = args.treat or rng.choice(sorted(TREATS))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    if treat not in TREATS:
        raise StoryError(f"Unknown treat: {treat}")
    return StoryParams(
        place=place,
        treat=treat,
        ghost_name=args.ghost_name or rng.choice(GHOST_NAMES),
        cook_name=args.cook_name or rng.choice(COOK_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    treat_cfg = TREATS[params.treat]
    sw = tell(setting, treat_cfg, params.ghost_name, params.cook_name)
    return StorySample(
        params=params,
        story=sw.world.render(),
        prompts=generation_prompts(sw),
        story_qa=story_qa(sw),
        world_qa=world_knowledge_qa(sw),
        world=sw.world,
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


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("serving", tid, t.serving))
    lines.append(asp.fact("story_kind", "ghost_story"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_treat(T) :- treat(T).
valid_story(P, T) :- valid_place(P), valid_treat(T), story_kind(ghost_story).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set((p, t, "ghost_story") for (p, t) in asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with proclamation and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--ghost-name")
    ap.add_argument("--cook-name")
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
    StoryParams(place="kitchen", treat="pie", ghost_name="Miri", cook_name="Mrs. Lane"),
    StoryParams(place="hall", treat="pudding", ghost_name="Lumi", cook_name="Mr. Finch"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show valid_story/2."))
        return

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen = set()
        i = 0
        while len(samples) < max(1, args.n) and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
