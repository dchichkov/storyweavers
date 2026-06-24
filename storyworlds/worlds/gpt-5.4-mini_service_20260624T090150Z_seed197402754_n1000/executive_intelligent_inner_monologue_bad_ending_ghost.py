#!/usr/bin/env python3
"""
A small storyworld for a ghost-story-style office tale with an executive hero,
an intelligent inner monologue, and a bad ending.

The world is deliberately tiny and state-driven:
- An executive works late in a quiet office tower.
- Strange signs suggest a ghost is present.
- The hero reasons through the threat with an inner monologue.
- The office can be secured, or the ghost can claim the final scene.
- The requested domain includes a bad ending, so the generated story resolves
  into loss rather than safety.

This file follows the Storyweavers standalone world contract.
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
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    hidden: bool = False
    spooky: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"executive"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the office tower"
    dark: bool = True
    silent: bool = True


@dataclass
class Threat:
    id: str
    name: str
    signs: list[str]
    takes: list[str]
    ending: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "office": Setting(place="the office tower", dark=True, silent=True),
    "corner": Setting(place="the corner office", dark=True, silent=True),
    "lobby": Setting(place="the empty lobby", dark=True, silent=True),
}

THREATS = {
    "ghost": Threat(
        id="ghost",
        name="a ghost",
        signs=["a cold draft", "a thin tapping in the glass", "a pale shape in the window"],
        takes=["the lights", "the elevator call button", "the executive's courage"],
        ending="The ghost stayed, and the office never felt warm again.",
    ),
    "shadow": Threat(
        id="shadow",
        name="a shadow with no owner",
        signs=["a long black smear on the wall", "a chair that moved by itself", "a whisper under the desk"],
        takes=["the quiet", "the hallway light", "the executive's nerve"],
        ending="The shadow swallowed the room, and no one found the missing files.",
    ),
}

CHARACTER_NAMES = ["Mara", "Iris", "Helen", "Clara", "June", "Nina"]
TRAITS = ["executive", "intelligent", "careful", "ambitious", "tired", "sharp"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    threat: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="executive",
        label=params.name,
        traits=["executive", params.trait, "intelligent"],
        meters={"fatigue": 0.0, "fear": 0.0, "resolve": 0.0},
        memes={"doubt": 0.0, "focus": 0.0, "panic": 0.0},
    ))
    threat = world.add(Entity(
        id=params.threat,
        kind="thing",
        type=params.threat,
        label=THREATS[params.threat].name,
        spooky=True,
        hidden=True,
        meters={"presence": 0.0},
    ))
    world.facts.update(hero=hero, threat=threat, threat_def=THREATS[params.threat])
    return world


def _inner_monologue(world: World, hero: Entity, clue: str) -> None:
    hero.memes["focus"] += 1
    hero.memes["doubt"] += 1
    world.say(
        f"{hero.label} stood still and listened. {hero.pronoun().capitalize()} thought, "
        f"'{clue} That means this is real, and real things have patterns.'"
    )


def _advance_fear(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.meters["fear"] += amount
    hero.meters["fatigue"] += 0.5
    if hero.meters["fear"] >= THRESHOLD:
        hero.memes["panic"] += 1


def _bad_turn(world: World, hero: Entity, threat: Entity) -> None:
    hero.meters["resolve"] += 1
    world.say(
        f"{hero.label} checked the hallway, the elevator, and the locked file cabinet. "
        f"{hero.pronoun().capitalize()} was intelligent enough to see the trap, but the trap was already closing."
    )
    world.say(
        f"In {hero.pronoun('possessive')} mind, {hero.label} counted the facts one by one: "
        f"the cold draft, the tapping glass, the missing light."
    )
    world.say(
        f"{hero.label} tried to call for help, but the phone only breathed static."
    )
    threat.hidden = False
    world.say(
        f"Then {threat.label} appeared at the far end of the office, and every screen went black."
    )
    _advance_fear(world, hero, 1.0)


def _ending(world: World, hero: Entity, threat: Entity) -> None:
    hero.meters["resolve"] += 0.5
    world.say(
        f"{hero.label} kept thinking anyway. {hero.pronoun().capitalize()} told {hero.pronoun('object')}self that a smart person could still lose if the room was cruel enough."
    )
    world.say(
        f"{THREATS[threat.type].ending}"
    )
    world.say(
        f"By morning, {hero.label}'s chair was empty, and the desk lamp still glowed beside the cold window."
    )


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    hero = world.get(params.name)
    threat = world.get(params.threat)
    threat_def = THREATS[params.threat]

    # Act 1: late work and a first eerie sign.
    world.say(
        f"{hero.label} was an intelligent executive who stayed late at {world.setting.place} because the quarterly report was not finished."
    )
    world.say(
        f"The building was dark and quiet, and the air felt thin enough to hold a secret."
    )
    world.say(
        f"Near the glass wall, {threat_def.signs[0]} made {hero.pronoun('possessive')} shoulders tighten."
    )

    # Act 2: inner monologue and escalating signs.
    world.para()
    _inner_monologue(world, hero, "A draft in a sealed room does not happen by accident.")
    _advance_fear(world, hero, 0.5)
    world.say(
        f"{hero.label} walked to the elevator, but {threat_def.signs[1]} answered with a soft, lonely knock."
    )
    world.say(
        f"{hero.label} thought, 'If I can name the pattern, I can beat it.'"
    )
    _advance_fear(world, hero, 0.5)
    world.say(
        f"At the desk, {threat_def.signs[2]} floated where no person should have stood."
    )

    # Act 3: the attempt to reason fails.
    world.para()
    _bad_turn(world, hero, threat)
    _ending(world, hero, threat)

    world.facts.update(
        setting=params.setting,
        threat=params.threat,
        name=params.name,
        trait=params.trait,
        fear=hero.meters["fear"],
        resolve=hero.meters["resolve"],
        panic=hero.memes["panic"] >= THRESHOLD,
        ending="bad",
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    threat = world.facts["threat_def"]
    return [
        f"Write a short ghost story about an intelligent executive named {hero.label} who works late in a dark office tower.",
        f"Tell a spooky story where {hero.label} notices {threat.name}, thinks hard about what is happening, and still cannot escape the final haunting.",
        f"Write a child-friendly ghost story with an inner monologue, an office setting, and a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    threat = world.facts["threat_def"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, an intelligent executive who is working late at {world.setting.place}.",
        ),
        QAItem(
            question=f"What first strange sign made {hero.label} feel uneasy?",
            answer=f"The first strange sign was {threat.signs[0]}. It made the office feel haunted before the ghost fully appeared.",
        ),
        QAItem(
            question=f"What did {hero.label} keep doing inside {hero.label}'s own mind?",
            answer=f"{hero.label} kept thinking carefully and trying to name the pattern, because {hero.label} was intelligent and wanted to understand the danger.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly: {THREATS[world.facts['threat']].ending}",
        ),
    ]
    if world.facts.get("panic"):
        qa.append(
            QAItem(
                question=f"Why did {hero.label} start to panic?",
                answer=f"{hero.label} started to panic after the signs kept coming, the phone filled with static, and the ghost appeared at the far end of the office.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an executive?",
            answer="An executive is a person who makes important decisions and helps run a company or office.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a story about a spooky spirit or unexplained haunting.",
        ),
        QAItem(
            question="Why do people get nervous in a dark office at night?",
            answer="People can feel nervous because darkness makes rooms seem unfamiliar, and small sounds can seem spooky.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private thinking a character does inside their own mind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The story is valid when an executive is placed in a haunted office setting
% with a spooky threat and a clear bad ending.
setting(office).
setting(corner).
setting(lobby).

hero_type(executive).
trait(intelligent).

threat(ghost).
threat(shadow).

valid_story(S, T) :- setting(S), threat(T).
haunted_story(S, T) :- valid_story(S, T), hero_type(executive), trait(intelligent).
bad_ending(S, T) :- haunted_story(S, T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in THREATS:
        lines.append(asp.fact("threat", t))
    lines.append(asp.fact("hero_type", "executive"))
    lines.append(asp.fact("trait", "intelligent"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(s, t) for s in SETTINGS for t in THREATS}
    found = set(asp_valid_combos())
    if found == expected:
        print(f"OK: ASP matches Python gate ({len(found)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("only in ASP:", sorted(found - expected))
    print("only in Python:", sorted(expected - found))
    return 1


def python_valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in THREATS]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with an executive, intelligence, inner monologue, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--name", choices=CHARACTER_NAMES)
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
    combos = python_valid_combos()
    setting = args.setting or rng.choice(sorted(SETTINGS))
    threat = args.threat or rng.choice(sorted(THREATS))
    if (setting, threat) not in combos:
        raise StoryError("No valid story matches the requested setting and threat.")
    name = args.name or rng.choice(CHARACTER_NAMES)
    trait = args.trait or rng.choice([t for t in TRAITS if t != "executive"])
    return StoryParams(setting=setting, threat=threat, name=name, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.spooky:
            bits.append("spooky=True")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  paragraphs={len([p for p in world.paragraphs if p])}")
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
        print(asp_program("#show valid_story/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for s, t in combos:
            print(f"  {s} / {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for s in SETTINGS:
            for t in THREATS:
                p = StoryParams(
                    setting=s,
                    threat=t,
                    name=CHARACTER_NAMES[0],
                    trait="intelligent",
                )
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
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
