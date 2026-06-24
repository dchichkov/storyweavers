#!/usr/bin/env python3
"""
A small adventure storyworld about a traveler, a mysterious clue, and a
subsequent choice made after talking it through.

The domain is intentionally tiny:
- One explorer wants to follow a trail.
- Something mysterious is found.
- The explorer thinks to themselves, speaks with a helper, and solves the puzzle.
- The ending shows what changed in the world.

Features used:
- Inner Monologue
- Mystery to Solve
- Dialogue
- Adventure style
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    has_tunnel: bool = False
    has_gate: bool = False
    has_lamp: bool = False


@dataclass
class Clue:
    name: str
    riddle: str
    answer: str
    next_step: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
    "harbor": Setting(
        place="the old harbor",
        detail="A narrow lane ran between crates, ropes, and salt-bright stone.",
        has_tunnel=True,
    ),
    "ruins": Setting(
        place="the vine-covered ruins",
        detail="Broken arches leaned over a quiet courtyard full of echoes.",
        has_gate=True,
    ),
    "cave": Setting(
        place="the glowing cave",
        detail="The cave walls shimmered like they had swallowed moonlight.",
        has_lamp=True,
    ),
}

CLUES = {
    "shell": Clue(
        name="shell",
        riddle="a tiny shell that hummed when held up to the wind",
        answer="the shell was pointing toward a hidden door",
        next_step="listen to the tunnel wall",
    ),
    "map": Clue(
        name="map",
        riddle="a torn map with one corner marked in red ink",
        answer="the red mark showed where the key was hidden",
        next_step="follow the red mark",
    ),
    "lantern": Clue(
        name="lantern",
        riddle="a lantern that flickered only when the air moved",
        answer="the flicker meant a draft was coming from behind the stones",
        next_step="look for a draft",
    ),
}

HERO_NAMES = ["Ari", "Mina", "Toby", "Lena", "Noah", "Iris"]
HELPER_NAMES = ["Pip", "Rae", "Juno", "Bea", "Tess", "Otto"]


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------

def build_story(setting: Setting, clue: Clue, hero_name: str, hero_type: str,
                helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    mystery = world.add(Entity(
        id="mystery",
        kind="thing",
        type="mystery",
        label="mystery",
        phrase=clue.riddle,
    ))

    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["resolve"] = 0.0
    hero.meters["progress"] = 0.0

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["clue"] = clue
    world.facts["mystery"] = mystery

    # Act 1: setup
    world.say(
        f"{hero.id} set out for {setting.place}, because adventure always seemed to call from places like that."
    )
    world.say(setting.detail)
    world.say(
        f"Near the path, {hero.id} found {clue.riddle}. That made {hero.pronoun('object')} stop and think."
    )

    # Inner monologue
    world.para()
    world.say(
        f"Inside {hero.pronoun('possessive')} head, {hero.id} wondered, "
        f'"What is this trying to tell me, and should I keep going?"'
    )
    hero.memes["worry"] += 1.0
    hero.memes["curiosity"] += 1.0

    # Dialogue
    world.say(
        f"{helper.id} came over and said, \"You look stuck. What did you find?\""
    )
    world.say(
        f'"I found {clue.riddle}," {hero.id} said. "{clue.answer} maybe, but I am not sure."'
    )
    world.say(
        f'{helper.id} pointed and said, "Then the next step is simple: {clue.next_step}."'
    )

    # Act 2: mystery deepens then resolves
    world.para()
    hero.memes["resolve"] += 1.0
    hero.meters["progress"] += 1.0
    world.say(
        f"{hero.id} listened carefully. The idea fit the clue, so the mystery began to make sense."
    )
    if setting.has_tunnel:
        world.say(
            f"{hero.id} and {helper.id} walked to the tunnel wall, and there they found a small hidden seam."
        )
    elif setting.has_gate:
        world.say(
            f"{hero.id} and {helper.id} searched the gate, and behind one loose stone they found the latch."
        )
    else:
        world.say(
            f"{hero.id} and {helper.id} followed the moving air, and it led them to a crack in the rock."
        )

    # Resolution
    world.para()
    world.say(
        f"At last, {hero.id} pushed the right place, and the secret path opened with a soft click."
    )
    world.say(
        f"{helper.id} grinned and said, \"We solved it together.\""
    )
    world.say(
        f"{hero.id} smiled too, because the mystery was no longer strange; it had become a safe, clear way forward."
    )

    world.facts["solved"] = True
    world.facts["ending"] = "opened"
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    return [
        f'Write an adventure story with the word "subsequent" about {hero.id} and {helper.id} solving a mystery.',
        f"Tell a short story where {hero.id} finds {clue.riddle} and then talks with {helper.id} before choosing the next step.",
        f'Write a child-friendly mystery story with inner monologue, dialogue, and a subsequent clue that leads to a hidden path.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    setting: Setting = world.setting

    return [
        QAItem(
            question=f"What did {hero.id} find at {setting.place}?",
            answer=f"{hero.id} found {clue.riddle} at {setting.place}. That clue started the mystery."
        ),
        QAItem(
            question=f"What did {hero.id} think about before talking to {helper.id}?",
            answer=(
                f"{hero.id} wondered what the clue meant and whether to keep going. "
                f"That was {hero.pronoun('possessive')} inner monologue."
            ),
        ),
        QAItem(
            question=f"How did {helper.id} help solve the mystery?",
            answer=(
                f"{helper.id} listened, pointed to the next step, and helped {hero.id} "
                f"see where the clue was leading."
            ),
        ),
        QAItem(
            question="What happened after they solved the mystery?",
            answer=(
                f"A hidden path opened, and the two friends could move forward with the problem solved."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer=(
                "A mystery is something confusing or unknown that people try to figure out by looking, thinking, and asking questions."
            ),
        ),
        QAItem(
            question="What is inner monologue?",
            answer=(
                "Inner monologue is the quiet voice inside your head when you think about what to do next."
            ),
        ),
        QAItem(
            question="What is dialogue?",
            answer=(
                "Dialogue is when characters talk to each other in a story."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- place(S).
clue(C) :- clue_name(C).
mystery_solved(S, C) :- setting(S), clue(C), has_dialogue(S), has_inner_monologue(S), next_step_leads_forward(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue_name", cid))
        lines.append(asp.fact("next_step_leads_forward", cid))
    lines.append(asp.fact("has_dialogue", "story"))
    lines.append(asp.fact("has_inner_monologue", "story"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_solved/2."))
    atoms = set(asp.atoms(model, "mystery_solved"))
    py = {(sid, cid) for sid in SETTINGS for cid in CLUES}
    if atoms == py:
        print(f"OK: ASP gate matches Python registry coverage ({len(py)} combinations).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP only:", sorted(atoms - py))
    print("Python only:", sorted(py - atoms))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: inner monologue, dialogue, and a mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("--helper-type", choices=["girl", "boy"], default="boy")
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
    clue = args.clue or rng.choice(list(CLUES))
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(
        setting=setting,
        clue=clue,
        hero_name=hero_name,
        hero_type=args.hero_type,
        helper_name=helper_name,
        helper_type=args.helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(
        SETTINGS[params.setting],
        CLUES[params.clue],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = ", ".join(f"{k}={v}" for k, v in e.meters.items() if v)
        memes = ", ".join(f"{k}={v}" for k, v in e.memes.items() if v)
        bits = [b for b in [meters and f"meters[{meters}]", memes and f"memes[{memes}]"] if b]
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_solved/2."))
        atoms = sorted(set(asp.atoms(model, "mystery_solved")))
        print(f"{len(atoms)} mystery combinations:")
        for sid, cid in atoms:
            print(f"  {sid} + {cid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sid in SETTINGS:
            for cid in CLUES:
                params = StoryParams(
                    setting=sid,
                    clue=cid,
                    hero_name=HERO_NAMES[0],
                    hero_type=args.hero_type,
                    helper_name=HELPER_NAMES[0],
                    helper_type=args.helper_type,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            p = sample.params
            print(f"### variant {idx + 1}: {p.hero_name} at {p.setting} with {p.clue}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
