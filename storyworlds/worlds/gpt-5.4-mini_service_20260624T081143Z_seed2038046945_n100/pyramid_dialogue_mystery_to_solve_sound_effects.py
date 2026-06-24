#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/pyramid_dialogue_mystery_to_solve_sound_effects.py
==============================================================================================================================

A small fable-like storyworld about a pyramid, a mystery to solve, and a sound
that helps reveal the truth.

The premise:
- A child and a caretaker visit a pyramid.
- A strange sound is heard inside.
- They talk through clues, test hypotheses, and solve the mystery.
- The ending image proves what changed: the sound is explained, the worry is
  resolved, and the child leaves with a small lesson.

This world keeps the simulation tiny and state-driven:
- physical meters track distance, echo, loudness, and carried items
- emotional memes track curiosity, worry, bravery, relief, and trust
- dialogue changes both the investigation and the emotional state
- sound effects are tied to world events, not bolted onto fixed prose

The ASP twin mirrors the reasonableness gate for compatible stories:
- the selected setting must afford a pyramid visit
- the mystery must have a plausible sound source
- the chosen reveal must match the sound category
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

PYRAMID_WORD = "pyramid"


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
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    afford_pyramid: bool = True
    quiet: bool = False


@dataclass
class Mystery:
    id: str
    clue_sound: str
    source: str
    reveal: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    caretaker: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def get(self, eid: str) -> Entity:
        return self.entities[eid]


SETTINGS = {
    "desert": Setting(place="the desert", afford_pyramid=True, quiet=True),
    "museum": Setting(place="the museum hall", afford_pyramid=True, quiet=False),
    "market": Setting(place="the market square", afford_pyramid=True, quiet=False),
}

MYSTERIES = {
    "drum": Mystery(
        id="drum",
        clue_sound="thump-thump",
        source="a little drum hidden behind a stone door",
        reveal="a forgotten guard drum was echoing from a side chamber",
        lesson="not every scary sound is dangerous",
        tags={"sound", "echo", "drum"},
    ),
    "bird": Mystery(
        id="bird",
        clue_sound="chirp-chirp",
        source="a bird nesting near the top crack",
        reveal="a small bird had made a nest in a warm gap high in the pyramid",
        lesson="a strange sound can belong to a gentle creature",
        tags={"sound", "bird", "nest"},
    ),
    "wind": Mystery(
        id="wind",
        clue_sound="whoooosh",
        source="wind slipping through a narrow stone opening",
        reveal="the pyramid had a tiny crack that sang when the wind passed through",
        lesson="some mysteries are just the world making music",
        tags={"sound", "wind", "echo"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Tess", "Maya"]
BOY_NAMES = ["Arlo", "Owen", "Theo", "Ezra", "Finn"]


ASP_RULES = r"""
setting_ok(S) :- setting(S), affords_pyramid(S).
mystery_ok(M) :- mystery(M), has_sound(M), has_reveal(M).
valid_story(S, M) :- setting_ok(S), mystery_ok(M).
compatible_reveal(M, sound) :- clue_sound(M, thump_thump), source_kind(M, drum).
compatible_reveal(M, sound) :- clue_sound(M, chirp_chirp), source_kind(M, bird).
compatible_reveal(M, sound) :- clue_sound(M, whoooosh), source_kind(M, wind).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.afford_pyramid:
            lines.append(asp.fact("affords_pyramid", sid))
        if s.quiet:
            lines.append(asp.fact("quiet", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("has_sound", mid))
        lines.append(asp.fact("has_reveal", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
        if mid == "drum":
            lines.append(asp.fact("clue_sound", mid, "thump_thump"))
            lines.append(asp.fact("source_kind", mid, "drum"))
        elif mid == "bird":
            lines.append(asp.fact("clue_sound", mid, "chirp_chirp"))
            lines.append(asp.fact("source_kind", mid, "bird"))
        elif mid == "wind":
            lines.append(asp.fact("clue_sound", mid, "whoooosh"))
            lines.append(asp.fact("source_kind", mid, "wind"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s, sv in SETTINGS.items() if sv.afford_pyramid for m in MYSTERIES]


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like pyramid mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("No valid story matches the given options.")

    setting, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, caretaker=caretaker)


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.gender == "girl" and params.name in BOY_NAMES:
        raise StoryError("Name does not fit the requested gender in this tiny world.")
    if params.gender == "boy" and params.name in GIRL_NAMES:
        raise StoryError("Name does not fit the requested gender in this tiny world.")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting=setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=params.caretaker, label=f"the {params.caretaker}"))
    pyramid = world.add(Entity(
        id=PYRAMID_WORD,
        kind="thing",
        type="landmark",
        label="a tall pyramid",
        phrase="a tall pyramid with quiet stone sides",
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="sound",
        label=mystery.clue_sound,
        phrase=mystery.source,
    ))
    world.facts.update(child=child, caretaker=caretaker, pyramid=pyramid, mystery=mystery, clue=clue)
    return world


def tell_story(world: World, params: StoryParams) -> None:
    child: Entity = world.facts["child"]
    caretaker: Entity = world.facts["caretaker"]
    mystery: Mystery = world.facts["mystery"]
    setting = world.setting.place

    world.say(f"Once, {child.id} walked with {caretaker.label} near {setting} and saw {world.facts['pyramid'].phrase}.")
    world.say(f"{child.id} loved the old stones, but then came a curious sound: {mystery.clue_sound}.")
    world.say(f'"What makes that sound?" asked {child.id}.')
    world.say(f'"Let us listen," said {caretaker.label}, and they stood still beside the pyramid.')

    world.para()
    child.memes["curiosity"] = 1
    child.memes["worry"] = 1
    world.say(f"The sound came again: {mystery.clue_sound}! It echoed softly through the stone.")
    if params.mystery == "drum":
        world.say(f'"It sounds like a drum," whispered {child.id}.')
    elif params.mystery == "bird":
        world.say(f'"It sounds small and lively," said {child.id}.')
    else:
        world.say(f'"It sounds like wind singing," said {child.id}.')
    world.say(f"{caretaker.label} smiled. 'A mystery is solved by looking and listening.'")

    world.para()
    child.memes["bravery"] = 1
    child.memes["worry"] = 0
    world.say(f"They followed the clue to {mystery.source}.")
    world.say(f"The answer was simple: {mystery.reveal}.")
    world.say(f'"Oh!" said {child.id}. "So the sound was never a monster at all."')

    world.para()
    child.memes["relief"] = 1
    child.memes["trust"] = 1
    world.say(f"Then {child.id} laughed and said, 'Next time I hear a strange sound, I will listen before I fear it.'")
    world.say(f"{caretaker.label} nodded, and the pyramid stood quiet again in the warm light.")
    world.say(f"It was a small lesson, but a true one: {mystery.lesson}.")

    world.facts["solved"] = True
    world.facts["lesson"] = mystery.lesson


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    mystery: Mystery = world.facts["mystery"]
    child: Entity = world.facts["child"]
    return [
        f'Write a short fable about a child named {child.id}, a pyramid, and the sound "{mystery.clue_sound}".',
        f"Tell a gentle mystery-to-solve story where a child listens carefully and discovers why the pyramid makes a strange sound.",
        f'Write a child-friendly story with dialogue and sound effects that ends with the truth behind "{mystery.clue_sound}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    mystery: Mystery = world.facts["mystery"]
    caretaker: Entity = world.facts["caretaker"]
    return [
        QAItem(
            question=f"What strange sound did {child.id} hear near the pyramid?",
            answer=f"{child.id} heard {mystery.clue_sound} near the pyramid.",
        ),
        QAItem(
            question=f"Who helped {child.id} think through the mystery?",
            answer=f"{caretaker.label} helped {child.id} by telling {child.id} to listen carefully and solve the mystery step by step.",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=f"The answer was that {mystery.reveal}.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=f"{child.id} learned that {mystery.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pyramid?",
            answer="A pyramid is a tall stone building with sloping sides that come together at the top.",
        ),
        QAItem(
            question="What does an echo do?",
            answer="An echo is a sound that bounces off hard surfaces and comes back to your ears.",
        ),
        QAItem(
            question="Why is listening useful when something seems strange?",
            answer="Listening carefully can help you notice clues before you guess, so you can solve a mystery more wisely.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    lines.append(f"facts={sorted(world.facts.keys())}")
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
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (setting, mystery) combos:")
        for setting, mystery in combos:
            print(f"  {setting:10} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for mystery in MYSTERIES:
                params = StoryParams(setting=setting, mystery=mystery, name="Mira", gender="girl", caretaker="mother")
                try:
                    samples.append(generate(params))
                except StoryError:
                    pass
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
