#!/usr/bin/env python3
"""
storyworlds/worlds/woman_surprise_bravery_rhyme_nursery_rhyme.py
=================================================================

A tiny nursery-rhyme storyworld about a woman, a surprise, a brave choice,
and a little rhyme that helps everyone through the moment.

Premise:
- A woman is preparing a small surprise for a child or neighbor.
- Something interrupts the plan: a noise, a missed step, or a lost object.
- She feels a pinch of worry, then chooses a brave, careful action.
- A short rhyme becomes the story's repeating helper and ending note.

The simulation is stateful: the woman's physical situation, the surprise object,
and her emotional meters all change before the final prose is rendered.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    mood: str
    props: tuple[str, ...]


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    risk: str
    helps_with: str
    hint: str
    rhyme_line: str


@dataclass
class StoryParams:
    setting: str
    surprise: str
    name: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.rhyme: list[str] = []

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
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, mood="warm", props=("table", "spoon", "cup")),
    "garden": Setting(place="the garden", indoor=False, mood="bright", props=("gate", "rose", "stone")),
    "porch": Setting(place="the porch", indoor=False, mood="soft", props=("step", "mat", "lantern")),
}

SURPRISES = {
    "cake": Surprise(
        id="cake",
        label="cake",
        phrase="a tiny cake with pink icing",
        risk="the candle might tip",
        helps_with="a happy birthday",
        hint="sweet and neat",
        rhyme_line="A cake for a day, a cake for a cheer,",
    ),
    "gift": Surprise(
        id="gift",
        label="gift",
        phrase="a small wrapped gift with a blue bow",
        risk="the paper might tear",
        helps_with="a kind hello",
        hint="tied up tight",
        rhyme_line="A gift in a wrap, a gift in a bow,",
    ),
    "lantern": Surprise(
        id="lantern",
        label="lantern",
        phrase="a little paper lantern with stars",
        risk="the string might slip",
        helps_with="a cozy evening",
        hint="glowing light",
        rhyme_line="A lantern a-shine, a lantern aloft,",
    ),
}

NAMES = ["Mabel", "Nina", "Clara", "Elsie", "Ruby", "Mina", "Lena", "June"]
ROLES = ["mother", "aunt", "woman"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    surprise = SURPRISES[params.surprise]
    world = World(setting)
    woman = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.role,
        traits=["gentle", "brave"],
        meters={"steps": 0.0, "care": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "bravery": 0.0, "joy": 0.0},
    ))
    thing = world.add(Entity(
        id=surprise.id,
        type="surprise",
        label=surprise.label,
        phrase=surprise.phrase,
        owner=woman.id,
        meters={"safe": 1.0, "ready": 0.0},
        memes={"spark": 1.0},
    ))
    world.facts.update(woman=woman, surprise=thing, surprise_cfg=surprise, setting=setting)
    return world


def prepare(world: World) -> None:
    woman: Entity = world.facts["woman"]  # type: ignore[assignment]
    surprise: Entity = world.facts["surprise"]  # type: ignore[assignment]
    cfg: Surprise = world.facts["surprise_cfg"]  # type: ignore[assignment]
    woman.meters["care"] += 1
    surprise.meters["ready"] += 1
    world.say(f"{woman.id} lived by {world.setting.place} and planned {surprise.phrase}.")
    world.say(f"The day was {world.setting.mood}, and the little surprise was {cfg.hint}.")
    world.rhyme.append(cfg.rhyme_line)


def interrupt(world: World) -> None:
    woman: Entity = world.facts["woman"]  # type: ignore[assignment]
    surprise: Entity = world.facts["surprise"]  # type: ignore[assignment]
    cfg: Surprise = world.facts["surprise_cfg"]  # type: ignore[assignment]
    woman.memes["worry"] += 1
    world.say(f"Then came a small trouble: {cfg.risk}.")
    world.say(f"{woman.id} paused, and her heart went thump, then hum.")
    if world.setting.indoor:
        world.say(f"The kitchen was small, and the table looked close to the edge.")
    else:
        world.say(f"The air outside stirred the {world.setting.props[0]} and the {world.setting.props[1]}.")
    surprise.meters["safe"] = 0.5


def brave_choice(world: World) -> None:
    woman: Entity = world.facts["woman"]  # type: ignore[assignment]
    surprise: Entity = world.facts["surprise"]  # type: ignore[assignment]
    cfg: Surprise = world.facts["surprise_cfg"]  # type: ignore[assignment]
    woman.memes["bravery"] += 1
    woman.memes["worry"] = 0.0
    surprise.meters["safe"] = 1.0
    woman.meters["steps"] += 2
    world.say(f"But {woman.id} took a brave breath and chose the careful way.")
    world.say(f"She moved the surprise to a safe spot, and the little plan was saved.")
    world.say(f"That was bravery: not loud and wild, but quiet, kind, and steady.")
    world.say(f"It helped bring {cfg.helps_with} close at hand.")


def ending_rhyme(world: World) -> None:
    woman: Entity = world.facts["woman"]  # type: ignore[assignment]
    surprise: Entity = world.facts["surprise"]  # type: ignore[assignment]
    cfg: Surprise = world.facts["surprise_cfg"]  # type: ignore[assignment]
    woman.memes["joy"] += 1
    world.para()
    world.say(f"{cfg.rhyme_line} {woman.id} smiled, and the moment felt soft and warm.")
    world.say(f"The {surprise.label} stayed safe, and the brave heart stayed bright.")
    world.say(f"{woman.id} hummed a rhyme and tucked the surprise in place.")


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    prepare(world)
    world.para()
    interrupt(world)
    world.para()
    brave_choice(world)
    ending_rhyme(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    woman: Entity = world.facts["woman"]  # type: ignore[assignment]
    cfg: Surprise = world.facts["surprise_cfg"]  # type: ignore[assignment]
    return [
        f"Write a nursery-rhyme style story about {woman.id}, a surprise, and a brave choice.",
        f"Tell a gentle story where {woman.id} prepares {cfg.phrase} and uses a small rhyme to stay brave.",
        f"Write a child-friendly rhyme about {world.setting.place}, surprise, and bravery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    woman: Entity = world.facts["woman"]  # type: ignore[assignment]
    surprise: Entity = world.facts["surprise"]  # type: ignore[assignment]
    cfg: Surprise = world.facts["surprise_cfg"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who planned the surprise in the story?",
            answer=f"{woman.id} planned the surprise. She cared for it and kept it safe.",
        ),
        QAItem(
            question=f"What was the surprise?",
            answer=f"The surprise was {surprise.phrase}. It was meant to make {cfg.helps_with} feel special.",
        ),
        QAItem(
            question=f"What did {woman.id} do when trouble came?",
            answer=f"She took a brave breath, chose the careful way, and moved the surprise to a safe spot.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a little rhyme, a safe surprise, and {woman.id} feeling happy and brave.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    cfg: Surprise = world.facts["surprise_cfg"]  # type: ignore[assignment]
    out = [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing a hard or scary thing carefully, even when you feel worried.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something hidden or unexpected that is revealed at just the right time.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a part of a poem or song where the endings sound alike and fun.",
        ),
    ]
    if cfg.id == "cake":
        out.append(QAItem(
            question="Why is a candle on a cake something to watch?",
            answer="A candle can tip or make a mess if it is bumped, so people keep it steady and safe.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A surprise is valid in a setting if the setting can hold it safely.
valid_story(S, Su, Name) :- setting(S), surprise(Su), person(Name).

% Bravery appears when the woman can face the trouble and keep the surprise safe.
brave_plan(Name, Su) :- person(Name), surprise(Su), safe_surprise(Su).

% Nursery-rhyme stories always end with a rhyme line when the plan is brave.
rhyme_end(Name, Su) :- brave_plan(Name, Su).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for p in s.props:
            lines.append(asp.fact("prop", sid, p))
    for suid, su in SURPRISES.items():
        lines.append(asp.fact("surprise", suid))
        lines.append(asp.fact("safe_surprise", suid))
    for name in NAMES:
        lines.append(asp.fact("person", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3. #show brave_plan/2. #show rhyme_end/2."))
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    expected = {("valid_story", 3), ("brave_plan", 2), ("rhyme_end", 2)}
    if atoms == expected:
        print("OK: ASP twin produced the expected predicates.")
        return 0
    print("MISMATCH in ASP twin.")
    print("Got:", sorted(atoms))
    print("Expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: woman, surprise, bravery, rhyme.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    role = args.role or "woman"
    name = args.name or rng.choice(NAMES)
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.surprise and args.surprise not in SURPRISES:
        raise StoryError("Unknown surprise.")
    return StoryParams(setting=setting, surprise=surprise, name=name, role=role)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3. #show brave_plan/2. #show rhyme_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(setting=s, surprise=u, name=n, role=r)
            for s in sorted(SETTINGS)
            for u in sorted(SURPRISES)
            for n in NAMES[:1]
            for r in ["woman"]
        ]
        samples = [generate(p) for p in combos]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {idx + 1}: {p.name} in {p.setting} with {p.surprise}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
