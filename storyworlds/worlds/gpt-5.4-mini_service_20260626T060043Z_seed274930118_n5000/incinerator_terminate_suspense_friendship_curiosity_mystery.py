#!/usr/bin/env python3
"""
storyworlds/worlds/incinerator_terminate_suspense_friendship_curiosity_mystery.py
=================================================================================

A small mystery-leaning storyworld about curiosity, friendship, and a mystery
near an old incinerator.

Premise:
- Two friends are near a place with an old incinerator.
- A strange sound and a missing object create suspense.
- Curiosity pushes them to investigate.

Turn:
- The friends follow clues, notice a safer path, and realize the mystery is not
  dangerous at all.
- They use a simple action to terminate the suspense: they stop the machine's
  noisy cycle and recover the missing item.

Resolution:
- The friends share the win, the tension drops, and the final image proves the
  mystery has been solved.

This world intentionally keeps the cast and situation small, with one clear
mystery and one clear emotional arc.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool = False
    has_incinerator: bool = False
    mood: str = "quiet"


@dataclass
class Clue:
    kind: str
    text: str
    reveals: str


@dataclass
class Mystery:
    id: str
    title: str
    sound: str
    missing: str
    harmless_truth: str
    fix: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "yard": Setting(place="the yard behind the old school", indoor=False, has_incinerator=True, mood="still"),
    "garden": Setting(place="the community garden", indoor=False, has_incinerator=True, mood="windy"),
    "dump": Setting(place="the little town recycling lot", indoor=False, has_incinerator=True, mood="echoing"),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        title="The Mystery of the Tin Bell",
        sound="a tinny ring",
        missing="a small tin bell",
        harmless_truth="The bell was caught on a wire near the incinerator door.",
        fix="turn off the fan and gently free the bell",
    ),
    "ribbon": Mystery(
        id="ribbon",
        title="The Mystery of the Blue Ribbon",
        sound="a soft flutter",
        missing="a blue ribbon from a kite",
        harmless_truth="The ribbon had blown into a crack beside the incinerator.",
        fix="open the side hatch and pull the ribbon free",
    ),
    "badge": Mystery(
        id="badge",
        title="The Mystery of the Lost Badge",
        sound="a tiny clink",
        missing="a bright metal badge",
        harmless_truth="The badge had slid under a loose grate near the incinerator.",
        fix="lift the grate and recover the badge",
    ),
}

NAMES = ["Mia", "Noah", "Lena", "Owen", "Ivy", "Eli", "June", "Theo"]
TRAITS = ["curious", "gentle", "brave", "patient", "careful"]
GENDERS = ["girl", "boy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the setting has an incinerator and the mystery has
% a harmless truth that can be reached by a simple fix.
reasonable(Place, Mystery) :- setting(Place), has_incinerator(Place), mystery(Mystery).

% Curiosity and friendship are the emotional arc.
arc(Place, Mystery) :- reasonable(Place, Mystery), clueable(Mystery), fixable(Mystery).

% Keep the declarative twin close to the Python gate.
valid_story(Place, Mystery) :- arc(Place, Mystery).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_incinerator:
            lines.append(asp.fact("has_incinerator", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clueable", mid))
        lines.append(asp.fact("fixable", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/2."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story params and helpers
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    friend: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in SETTINGS for m in MYSTERIES if SETTINGS[p].has_incinerator]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with an incinerator, curiosity, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(combos)
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, friend=friend, gender=gender, trait=trait)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"curiosity": 0.0}, memes={"curiosity": 0.0, "suspense": 0.0, "friendship": 0.0}))
    friend = world.add(Entity(id=params.friend, kind="character", type="girl" if params.gender == "boy" else "boy", meters={"curiosity": 0.0}, memes={"curiosity": 0.0, "suspense": 0.0, "friendship": 0.0}))
    mystery = MYSTERIES[params.mystery]
    clue = Clue(kind=params.mystery, text=mystery.sound, reveals=mystery.harmless_truth)
    world.facts.update(hero=hero, friend=friend, mystery=mystery, clue=clue, setting=world.setting)

    world.say(f"{hero.id} and {friend.id} were walking through {world.setting.place} when they heard {clue.text} near the old incinerator.")
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    hero.meters["curiosity"] += 1
    friend.meters["curiosity"] += 1
    world.say(f"{hero.id}, who was especially {params.trait}, looked at {friend.id} and whispered that the sound felt like a mystery.")

    world.para()
    world.say(f"Then they noticed something missing: {mystery.missing}. That made the air feel quiet and suspenseful.")
    hero.memes["suspense"] += 1
    friend.memes["suspense"] += 1
    world.say(f"{friend.id} said they should not guess too fast, so the two friends searched carefully instead of running off.")

    world.para()
    world.say(f"They followed the tiny clue to a crack beside the incinerator, where the truth was harmless: {mystery.harmless_truth}")
    world.say(f"{hero.id} and {friend.id} worked together to {mystery.fix}, and that helped terminate the suspense right away.")
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    hero.memes["suspense"] = 0.0
    friend.memes["suspense"] = 0.0
    world.say(f"In the end, the friends held up {mystery.missing} together, smiling beside the quiet incinerator.")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    return [
        f'Write a short mystery story for a child that includes the word "{mystery_word(m)}" and the idea of friendship.',
        f"Tell a gentle suspense story about {f['hero'].id} and {f['friend'].id} solving {m.title}.",
        f"Write a simple story where curiosity leads two friends to an incinerator, and the mystery ends safely.",
    ]


def mystery_word(m: Mystery) -> str:
    return "incinerator"


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who heard the strange sound near the incinerator?",
            answer=f"{hero.id} and {friend.id} heard it together in {setting.place}.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful?",
            answer=f"The suspense came from the missing {mystery.missing} and the strange sound near the incinerator.",
        ),
        QAItem(
            question=f"How did the friends solve the mystery?",
            answer=f"They found that {mystery.harmless_truth.lower()} Then they {mystery.fix}, which terminated the suspense.",
        ),
        QAItem(
            question=f"What did friendship help them do?",
            answer=f"Friendship helped {hero.id} and {friend.id} stay calm, search carefully, and solve the mystery together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, learn, and ask questions about something new.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about another person, helping each other, and working together kindly.",
        ),
        QAItem(
            question="What is an incinerator?",
            answer="An incinerator is a machine or place that burns waste very hotly and safely when it is used by adults.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to end something or stop it completely.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in SETTINGS:
            for m in MYSTERIES:
                params = StoryParams(place=p, mystery=m, name="Mia", friend="Noah", gender="girl", trait="curious")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 and not args.all else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
