#!/usr/bin/env python3
"""
storyworlds/worlds/rafter_flashback_surprise_adventure.py
=========================================================

A standalone story world for a small Adventure tale set around a rafter.

Premise:
A child adventurer climbs into a quiet loft or barn and wants to explore the
rafters. A memory from an earlier trip explains why the child is careful, and a
surprise in the beams turns caution into a small rescue.

The world keeps track of:
- who is exploring
- what the child carries
- which place is being explored
- what surprise is hidden in the rafters
- whether the remembered lesson helps prevent a fall or solve the problem

The story is generated from simulated state rather than a fixed paragraph.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    discovered: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    sheltered: bool
    rafter_kind: str
    smell: str


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    need: str
    reward: str


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    help_text: str


@dataclass
class StoryParams:
    setting: str
    surprise: str
    artifact: str
    name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "barn": Setting(place="the old barn", sheltered=True, rafter_kind="wooden rafters", smell="hay"),
    "loft": Setting(place="the loft", sheltered=True, rafter_kind="dusty rafters", smell="dust"),
    "shed": Setting(place="the shed", sheltered=True, rafter_kind="low rafters", smell="paint"),
    "attic": Setting(place="the attic", sheltered=True, rafter_kind="crossed rafters", smell="books"),
}

SURPRISES = {
    "nest": Surprise(
        id="nest",
        label="a tiny nest",
        phrase="a tiny nest tucked between the beams",
        need="a safe place",
        reward="the baby bird can stay warm",
    ),
    "map": Surprise(
        id="map",
        label="a folded map",
        phrase="a folded map wedged by a nail",
        need="careful hands",
        reward="it can show the hidden path",
    ),
    "balloon": Surprise(
        id="balloon",
        label="a red balloon",
        phrase="a red balloon tied to a string",
        need="a steady grip",
        reward="it can lead the way upward",
    ),
    "lantern": Surprise(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern resting on a board",
        need="someone brave",
        reward="it can light the dark corner",
    ),
}

ARTIFACTS = {
    "hook": Artifact(
        id="hook",
        label="a small hook",
        phrase="a small hook with a bright string",
        help_text="it can pull the surprise down without a big reach",
    ),
    "ladder": Artifact(
        id="ladder",
        label="a short ladder",
        phrase="a short ladder with steady rungs",
        help_text="it can help the child climb safely",
    ),
    "glove": Artifact(
        id="glove",
        label="a pair of gloves",
        phrase="a pair of gloves that fit snugly",
        help_text="they keep rough wood from scratching hands",
    ),
}

TRAITS = ["curious", "brave", "lively", "careful", "spirited", "adventurous"]
NAMES = ["Maya", "Leo", "Nina", "Toby", "Ivy", "Ezra", "Lena", "Owen"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def detect_flashback(world: World, hero: Entity, artifact: Entity) -> None:
    hero.memes["memory"] = hero.memes.get("memory", 0.0) + 1
    world.say(
        f"As {hero.id} looked up at the {world.setting.rafter_kind}, "
        f"{hero.pronoun('subject') if False else ''}"
    )


def _pronoun(entity: Entity, case: str = "subject") -> str:
    female = {"girl", "woman", "mother", "daughter"}
    male = {"boy", "man", "father", "son"}
    if entity.type in female:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if entity.type in male:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def _name_or_pronoun(hero: Entity, case: str = "subject") -> str:
    return hero.id if case == "subject" else _pronoun(hero, case)


def narrate_flashback(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} paused, because the last time {hero.id} had climbed too fast, "
        f"{_pronoun(hero, 'subject')} had bumped {_pronoun(hero, 'possessive')} head on a beam."
    )
    world.say(
        f"That memory made {hero.id} slow down and watch each step."
    )
    hero.memes["careful"] = hero.memes.get("careful", 0.0) + 1


def discover_surprise(world: World, hero: Entity, surprise: Surprise) -> None:
    surprise_ent = world.add(Entity(
        id=surprise.id,
        kind="thing",
        type="surprise",
        label=surprise.label,
        phrase=surprise.phrase,
    ))
    surprise_ent.discovered = True
    world.facts["surprise"] = surprise
    world.say(
        f"Then, with one hand on the beam, {hero.id} spotted {surprise.phrase}."
    )
    world.say(
        f"It was a surprise, but not a bad one."
    )


def solve_surprise(world: World, hero: Entity, surprise: Surprise, artifact: Artifact) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"{hero.id} used {artifact.phrase} to help."
    )
    world.say(
        f"That way, the {surprise.label} could be handled safely, and {surprise.reward}."
    )


def tell(setting: Setting, surprise: Surprise, artifact: Artifact, name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="boy" if name in {"Leo", "Toby", "Ezra", "Owen"} else "girl"))
    hero.memes["curiosity"] = 1.0
    hero.memes["bravery"] = 1.0
    hero.meters["up"] = 0.0

    tool = world.add(Entity(
        id=artifact.id,
        kind="thing",
        type="tool",
        label=artifact.label,
        phrase=artifact.phrase,
        carried_by=hero.id,
    ))

    world.say(
        f"{hero.id} was a {trait} little adventurer who loved quiet places with rafters to explore."
    )
    world.say(
        f"{_pronoun(hero, 'subject').capitalize()} brought {artifact.phrase} and went to {setting.place}."
    )
    world.say(
        f"The {setting.place.removeprefix('the ')} smelled like {setting.smell}, and the rafters looked high and mysterious."
    )
    world.para()

    hero.meters["up"] += 1
    world.say(
        f"{hero.id} climbed up slowly, holding the wood with careful fingers."
    )
    narrate_flashback(world, hero)
    world.say(
        f"Because of that flashback, {hero.id} moved more carefully than before."
    )
    world.para()

    discover_surprise(world, hero, surprise)
    solve_surprise(world, hero, surprise, artifact)
    world.say(
        f"In the end, {hero.id} came down smiling, and the rafters seemed friendly instead of scary."
    )

    world.facts.update(
        hero=hero,
        artifact=artifact,
        surprise=surprise,
        setting=setting,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    artifact: Artifact = f["artifact"]
    surprise: Surprise = f["surprise"]
    setting: Setting = f["setting"]
    return [
        f'Write a short Adventure story for a young child about {hero.id} exploring {setting.place} and finding {surprise.label}.',
        f"Tell a story where a flashback helps {hero.id} stay safe around the rafters in {setting.place}.",
        f"Write a gentle surprise adventure that includes {artifact.label}, a rafter, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    artifact: Artifact = f["artifact"]
    surprise: Surprise = f["surprise"]
    setting: Setting = f["setting"]
    trait: str = f["trait"]
    return [
        QAItem(
            question=f"Where did {hero.id} go to explore the rafters?",
            answer=f"{hero.id} went to {setting.place}, where the rafters were high and quiet.",
        ),
        QAItem(
            question=f"What helped {hero.id} stay careful before reaching the surprise?",
            answer=f"A flashback helped {hero.id} remember to slow down and watch each step.",
        ),
        QAItem(
            question=f"What did {hero.id} find in the rafters?",
            answer=f"{hero.id} found {surprise.phrase}.",
        ),
        QAItem(
            question=f"How did {artifact.label} help in the story?",
            answer=f"{artifact.label.capitalize()} helped because {artifact.help_text}.",
        ),
        QAItem(
            question=f"What kind of child was {hero.id}?",
            answer=f"{hero.id} was a {trait} little adventurer.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rafter?",
            answer="A rafter is a long beam that helps hold up a roof.",
        ),
        QAItem(
            question="Why should someone be careful in a loft or attic?",
            answer="They should be careful because the floor and beams can be high, dusty, or hard to balance on.",
        ),
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback shows something that happened earlier, so the reader understands why a character acts a certain way.",
        ),
        QAItem(
            question="What is a surprise in an adventure story?",
            answer="A surprise is something unexpected that changes what the character does next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    surprise: str
    artifact: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with rafters, flashback, and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    artifact = args.artifact or rng.choice(list(ARTIFACTS))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, surprise=surprise, artifact=artifact, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SURPRISES[params.surprise], ARTIFACTS[params.artifact], params.name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"{e.id}: {', '.join(bits)}")
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


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.sheltered:
            lines.append(asp.fact("sheltered", sid))
        lines.append(asp.fact("smell", sid, s.smell))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
    return "\n".join(lines)


ASP_RULES = r"""
% Tiny declarative twin: a story is reasonable when a surprise and a helper exist.
has_surprise(S) :- surprise(S).
has_artifact(A) :- artifact(A).
valid_story(Place, Surprise, Artifact) :- setting(Place), has_surprise(Surprise), has_artifact(Artifact).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:  # pragma: no cover
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/3."))
    combos = sorted(set(asp.atoms(model, "valid_story")))
    py = sorted((p, s, a) for p in SETTINGS for s in SURPRISES for a in ARTIFACTS)
    if combos == py:
        print(f"OK: ASP gate matches Python ({len(combos)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", combos[:10])
    print("PY :", py[:10])
    return 1


CURATED = [
    StoryParams(setting="barn", surprise="nest", artifact="hook", name="Maya", trait="curious"),
    StoryParams(setting="loft", surprise="map", artifact="glove", name="Leo", trait="careful"),
    StoryParams(setting="attic", surprise="lantern", artifact="ladder", name="Nina", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for place, surprise, artifact in combos:
            print(place, surprise, artifact)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
            header = f"### {p.name}: {p.setting} / {p.surprise} / {p.artifact}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
