#!/usr/bin/env python3
"""
storyworlds/worlds/disappoint_twist_sound_effects_pirate_tale.py
================================================================

A small pirate-tale story world about a hopeful crew, a loud clue, a twist,
and a disappointment that turns into a better ending.

The seed idea:
---
A young pirate crew expects a shiny treasure chest to open with a cheer.
Instead, the chest makes a strange sound, the first guess is wrong, and the
crew feels disappointed. Then they notice a twist: the "treasure" is not gold
at all, but a kind rescue with a message that sends them toward a better find.

This world keeps the story child-facing, concrete, and state-driven:
- physical meters track things like treasure, distance, and noise
- emotional memes track hope, worry, disappoint, relief, and trust
- the story is produced from simulated world state rather than a frozen template
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
    leader: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sea: bool = True
    soundscape: str = "waves"


@dataclass
class Twist:
    id: str
    clue_sound: str
    wrong_guess: str
    reveal: str
    turn_label: str
    fix_label: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    value: str
    at_sea: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


THRESHOLD = 1.0


def _name_for(entity: Entity) -> str:
    return entity.label or entity.id


def _article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def _sound_line(twist: Twist) -> str:
    return f"{twist.clue_sound}! {twist.clue_sound}!"


def _set_emotion(e: Entity, key: str, value: float) -> None:
    e.memes[key] = value


def _bump(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def _bump_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", sea=True, soundscape="waves"),
    "cove": Setting(place="the hidden cove", sea=True, soundscape="surf"),
    "island": Setting(place="the little island", sea=True, soundscape="wind"),
}

TWISTS = {
    "seaglass": Twist(
        id="seaglass",
        clue_sound="clang-clink",
        wrong_guess="a chest full of gold",
        reveal="a bag of smooth sea-glass and a map tucked under it",
        turn_label="the shiny surprise",
        fix_label="the true clue",
    ),
    "message_in_bottle": Twist(
        id="message_in_bottle",
        clue_sound="tap-tap",
        wrong_guess="a bottle that only looked empty",
        reveal="a message from a lost friend asking for help",
        turn_label="the quiet surprise",
        fix_label="the kind message",
    ),
    "rescue_bell": Twist(
        id="rescue_bell",
        clue_sound="ding-ding",
        wrong_guess="a bell for a treasure room",
        reveal="a bell rope tied to a small boat that needed a rescue",
        turn_label="the brave surprise",
        fix_label="the rescue plan",
    ),
}

PRIZES = {
    "chest": Prize(
        id="chest",
        label="treasure chest",
        phrase="a shiny treasure chest with a brass latch",
        type="chest",
        value="gold",
    ),
    "bottle": Prize(
        id="bottle",
        label="glass bottle",
        phrase="a clear glass bottle with a cork",
        type="bottle",
        value="message",
    ),
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a small lantern wrapped in rope",
        type="lantern",
        value="signal",
    ),
}

HERO_NAMES = ["Mina", "Cora", "Pip", "Jules", "Nina", "Finn"]
CREW_NAMES = ["Toby", "Rae", "Milo", "Lena", "Beau", "Sailor"]


@dataclass
class StoryParams:
    setting: str
    twist: str
    prize: str
    hero: str
    crew: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TWISTS:
            for p in PRIZES:
                # keep the world tight: every story must have a disappointment
                # and a twist that changes the meaning of the sound clue.
                if t == "seaglass" and p == "chest":
                    combos.append((s, t, p))
                elif t == "message_in_bottle" and p == "bottle":
                    combos.append((s, t, p))
                elif t == "rescue_bell" and p == "lantern":
                    combos.append((s, t, p))
    return combos


def reasonableness_gate(setting: str, twist: str, prize: str) -> bool:
    return (setting, twist, prize) in valid_combos()


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S,T,P) :- setting(S), twist(T), prize(P), match(S,T,P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for s, t, p in valid_combos():
        lines.append(asp.fact("match", s, t, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def _introduce(world: World, hero: Entity, crew: Entity) -> None:
    world.say(
        f"{hero.label} was a little pirate who sailed with {crew.label} and loved a good mystery."
    )
    _bump(hero, "hope", 1)
    _bump(hero, "curiosity", 1)


def _setup(world: World, hero: Entity, crew: Entity, prize: Entity) -> None:
    world.say(
        f"One bright day at {world.setting.place}, {hero.label} and {crew.label} found {_article(prize.label)} {prize.label}."
    )
    world.say(f"It looked special: {prize.phrase}.")
    prize.owner = hero.id
    _bump_meter(prize, "hidden", 1)
    _bump(hero, "hope", 1)
    _bump(hero, "excitement", 1)


def _sound_and_guess(world: World, hero: Entity, crew: Entity, prize: Entity, twist: Twist) -> None:
    world.para()
    world.say(
        f"Then the box gave a {twist.clue_sound} sound, and the crew leaned in to listen."
    )
    world.say(_sound_line(twist))
    world.say(
        f"{hero.label} guessed it was {twist.wrong_guess}, and {crew.label} nodded so fast their hats wobbled."
    )
    _bump(hero, "expectation", 1)
    _bump(crew, "expectation", 1)


def _disappoint(world: World, hero: Entity, crew: Entity, prize: Entity, twist: Twist) -> None:
    world.say(
        f"But when the lid opened, there was no gold at all."
    )
    world.say(
        f"That made {hero.label} feel disappointed for a moment."
    )
    _bump(hero, "disappoint", 1)
    _bump(hero, "worry", 1)
    _bump(crew, "worry", 1)
    _bump_meter(prize, "revealed", 1)


def _twist_reveal(world: World, hero: Entity, crew: Entity, prize: Entity, twist: Twist) -> None:
    world.para()
    world.say(
        f"Then came the twist: inside was {twist.reveal}."
    )
    world.say(
        f"{twist.fix_label.capitalize()} changed everything, because the sound had been a clue, not a trick."
    )
    _bump(hero, "surprise", 1)
    _bump(hero, "trust", 1)
    _bump(hero, "relief", 1)
    _bump(hero, "disappoint", -1)
    _bump(crew, "relief", 1)


def _finish(world: World, hero: Entity, crew: Entity, prize: Entity, twist: Twist) -> None:
    world.say(
        f"{hero.label} smiled, tucked the clue away, and said they could follow it to something better."
    )
    world.say(
        f"Soon the crew sailed on with a new plan, and the little pirate's heart felt light again."
    )
    _set_emotion(hero, "disappoint", 0.0)
    _bump(hero, "joy", 1)
    _bump(crew, "joy", 1)
    prize.meters["opened"] = 1.0


def generate_world(params: StoryParams) -> World:
    if not reasonableness_gate(params.setting, params.twist, params.prize):
        raise StoryError("No story: this setting, twist, and prize do not fit the pirate-tale clue pattern.")

    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type="girl", label=params.hero))
    crew = world.add(Entity(id="crew", kind="character", type="pirate", label=params.crew, plural=True))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))
    twist = TWISTS[params.twist]

    _introduce(world, hero, crew)
    _setup(world, hero, crew, prize)
    _sound_and_guess(world, hero, crew, prize, twist)
    _disappoint(world, hero, crew, prize, twist)
    _twist_reveal(world, hero, crew, prize, twist)
    _finish(world, hero, crew, prize, twist)

    world.facts.update(hero=hero, crew=crew, prize=prize, twist=twist, params=params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a short pirate story for a small child that includes the word '{p.twist}' and a surprise sound.",
        f"Tell a gentle pirate tale where {p.hero} expects treasure, hears a clue, feels disappointed, and then learns the real meaning.",
        f"Write a simple story about a pirate crew at {world.setting.place} where a twist changes an upset moment into a better plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    crew: Entity = world.facts["crew"]  # type: ignore[assignment]
    prize: Entity = world.facts["prize"]  # type: ignore[assignment]
    twist: Twist = world.facts["twist"]  # type: ignore[assignment]
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {hero.label} feel disappointed in the story?",
            answer=f"{hero.label} felt disappointed because the first guess was wrong and the chest did not hold the gold they expected.",
        ),
        QAItem(
            question=f"What sound did the clue make before the twist was revealed?",
            answer=f"The clue made a {twist.clue_sound} sound, and the story even repeated it like a little sea-song.",
        ),
        QAItem(
            question=f"What was the twist in the pirate tale?",
            answer=f"The twist was that the treasure was not gold at all; it was {twist.reveal}.",
        ),
        QAItem(
            question=f"How did the ending change after the disappointing moment?",
            answer=f"After the disappointing moment, {hero.label} understood the clue, felt relief, and sailed on with a new plan from {world.setting.place}.",
        ),
        QAItem(
            question=f"Who sailed with {hero.label} in the story?",
            answer=f"{crew.label} sailed with {hero.label}, and together they listened closely to the sound clue.",
        ),
        QAItem(
            question=f"What object did they open near {world.setting.place}?",
            answer=f"They opened a {prize.label} near {params.setting.replace('_', ' ')}, and that opened the way to the twist.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate crew?",
            answer="A pirate crew is a group of sailors who travel together on a boat and work as a team.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you figure something out.",
        ),
        QAItem(
            question="Why can a sound be important in a story?",
            answer="A sound can be important because it can warn people, hide a secret, or help them notice a new clue.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with a disappointing twist and sound clues.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--crew")
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.twist is None or c[1] == args.twist)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("No valid pirate-tale combination matches the given options.")
    setting, twist, prize = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    crew = args.crew or rng.choice(CREW_NAMES)
    return StoryParams(setting=setting, twist=twist, prize=prize, hero=hero, crew=crew)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, twist, prize) combos:\n")
        for s, t, p in combos:
            print(f"  {s:10} {t:20} {p:10}")
        return

    if args.all:
        curated = [
            StoryParams(setting="harbor", twist="seaglass", prize="chest", hero="Mina", crew="Toby"),
            StoryParams(setting="cove", twist="message_in_bottle", prize="bottle", hero="Cora", crew="Rae"),
            StoryParams(setting="island", twist="rescue_bell", prize="lantern", hero="Pip", crew="Milo"),
        ]
        samples = [generate(p) for p in curated]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
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
            header = f"### {p.hero}: {p.twist} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
