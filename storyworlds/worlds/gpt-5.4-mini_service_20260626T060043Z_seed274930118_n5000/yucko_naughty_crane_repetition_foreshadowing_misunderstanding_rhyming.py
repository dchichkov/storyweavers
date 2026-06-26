#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/yucko_naughty_crane_repetition_foreshadowing_misunderstanding_rhyming.py
=====================================================================================================================

A tiny rhyming storyworld about a crane, a misunderstanding, and a neat little
turn from naughty behavior to a kinder ending.

The world is built from a short source-tale premise:
- a small crane wants attention
- a child hears "yucko" and thinks the crane is bad
- repeated rhymes and repeated actions build tension
- foreshadowing hints that the crane is actually trying to help
- a misunderstanding is cleared up by a simple, child-facing explanation
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
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
        if self.type in {"child", "girl", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"crane"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    crane_name: str = "Yucko"
    place: str = "the yard"
    object: str = "a red wagon"
    helper: str = "a broom"
    rhyme_word: str = "boom"


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    fired: set[str] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "yard": "the yard",
    "dock": "the dock",
    "school": "the school gate",
}

OBJECTS = {
    "wagon": "a red wagon",
    "bucket": "a blue bucket",
    "kite": "a bright kite",
}

HELPERS = {
    "broom": "a broom",
    "rope": "a rope",
    "ladder": "a ladder",
}

RHYMES = {
    "boom": ("boom", "room", "gloom"),
    "sway": ("sway", "play", "day"),
    "glow": ("glow", "show", "snow"),
}


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for obj in OBJECTS:
            for helper in HELPERS:
                combos.append((place, obj, helper))
    return combos


def explain_rejection(place: str, obj: str, helper: str) -> str:
    return (
        f"(No story: the chosen place/object/helper combination would not give "
        f"the crane a believable way to cause a misunderstanding and then fix it.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(params=params)
    child = world.add(Entity(id="child", kind="character", type="child", label=params.name))
    crane = world.add(Entity(id="crane", kind="character", type="crane", label=params.crane_name))
    obj = world.add(Entity(id="object", kind="thing", type=params.object.split()[-1], label=params.object))
    helper = world.add(Entity(id="helper", kind="thing", type=params.helper.split()[-1], label=params.helper))

    world.facts.update(child=child, crane=crane, obj=obj, helper=helper)
    return world


def rhyming_line(word1: str, word2: str, word3: str) -> str:
    return f"{word1.capitalize()} and {word2} and {word3} all rang like a bell."


def tell_story(world: World) -> None:
    p = world.params
    child = world.get("child")
    crane = world.get("crane")
    obj = world.get("object")
    helper = world.get("helper")

    crane.memes["naughty"] = 1
    crane.memes["helpful"] = 0
    child.memes["worry"] = 0
    child.memes["confusion"] = 0

    # Setup with repetition.
    world.say(
        f"At {p.place}, little {p.name} saw {p.crane_name} by {obj.label}."
    )
    world.say(
        f'"Yucko, yucko," {p.name} said, for the crane had a naughty look and a tricky walk.'
    )
    world.say(
        f'"Yucko, yucko," the child said again, and the crane gave a tiny hop and a crooked nod.'
    )
    world.say(
        f"{rhyming_line('clack', 'stack', 'back')} It was a day that liked to echo back."
    )

    # Foreshadowing.
    world.para()
    world.say(
        f"Near a corner of {p.place}, {helper.label} leaned where {obj.label} could be reached."
    )
    world.say(
        f"The crane kept glancing that way, then at {obj.label}, then at {p.name}."
    )
    world.say(
        f"That little look was a clue: the crane was not mean, only clumsy and keen."
    )

    # Misunderstanding.
    world.para()
    child.memes["confusion"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{p.name} thought, 'Naughty crane! You want to make a mess and ruin my day.'"
    )
    world.say(
        f"The crane shook its wings and said, 'No, no, no, I mean to help in a row!'"
    )
    world.say(
        f"But {p.name} heard the wrong thing and stepped back with a frown."
    )

    # Turn: repeated action reveals intent.
    world.para()
    crane.meters["reach"] = 1
    crane.meters["care"] = 1
    world.say(
        f"Then the crane tried again and again, with a tap and a clap and a careful spin."
    )
    world.say(
        f"It nudged {helper.label} toward {obj.label}, showing the child the plan inside."
    )
    world.say(
        f"At last {p.name} saw the trick: the crane was using {helper.label} to lift {obj.label} up."
    )

    # Resolution.
    world.para()
    crane.memes["helpful"] = 1
    crane.memes["naughty"] = 0
    child.memes["confusion"] = 0
    child.memes["worry"] = 0
    world.say(
        f"{p.name} laughed and said, 'Oh! You were helping, not being nasty and jumping around.'"
    )
    world.say(
        f"The crane gave a proud little twirl, and {obj.label} came free with a happy clatter."
    )
    world.say(
        f"Now the yard was calm and bright; the naughty look was only a misunderstood sight."
    )

    world.facts["resolved"] = True
    world.facts["misunderstanding"] = True
    world.facts["rhymed"] = True
    world.facts["repetition"] = True
    world.facts["foreshadowing"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f'Write a short rhyming story for a young child about a crane named {p.crane_name}, a misunderstanding, and a kind ending.',
        f'Tell a story that repeats "yucko" a few times, then reveals that the crane was helping with {p.object}.',
        f'Write a gentle story with foreshadowing, repetition, and a playful rhyme at {p.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Why did {p.name} call the crane yucko at first?",
            answer=(
                f"{p.name} called the crane yucko because the crane looked naughty and strange at first, "
                f"so {p.name} misunderstood its funny moves."
            ),
        ),
        QAItem(
            question=f"What clue showed that the crane was not actually naughty?",
            answer=(
                f"The clue was that the crane kept looking at {world.get('helper').label} and {world.get('object').label}. "
                f"That foreshadowed a helpful plan."
            ),
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"At the end, {p.name} understood that the crane was helping, not causing trouble. "
                f"The misunderstanding disappeared and everyone felt better."
            ),
        ),
        QAItem(
            question=f"How did repetition help the story?",
            answer=(
                f"The story repeated 'yucko, yucko' and repeated the crane's careful tries, which made the moment feel more lively and important."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crane?",
            answer="A crane is a long-necked bird, or sometimes a machine that lifts heavy things. In this story, the crane is a bird.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about what is happening.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means saying or doing something again to make it stand out and feel memorable.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue early in a story that hints at what will happen later.",
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% place(P). object(O). helper(H). crane(C).

% A misunderstanding occurs when the child sees naughty signals but the crane is actually helping.
misunderstanding(C, K) :- child(C), crane(K), naughty_signal(K), helpful_intent(K).

% Repetition is modeled as a visible repeated call.
repetition(C) :- repeats(C, W), W = yucko.

% Foreshadowing is a clue that points to the helper and the object.
foreshadowing(K) :- crane(K), looks_toward_helper(K), looks_toward_object(K).

% The story is reasonable if it has all three story features.
valid_story(P, O, H) :- place(P), object(O), helper(H),
                        repetition(_), foreshadowing(_), misunderstanding(_, _).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))

    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("crane", "crane"))
    lines.append(asp.fact("naughty_signal", "crane"))
    lines.append(asp.fact("helpful_intent", "crane"))
    lines.append(asp.fact("repeats", "child", "yucko"))
    lines.append(asp.fact("looks_toward_helper", "crane"))
    lines.append(asp.fact("looks_toward_object", "crane"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for obj in OBJECTS:
            for helper in HELPERS:
                combos.append((place, obj, helper))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.object is None or c[1] == args.object)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, obj, helper = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Mina", "Lena", "Toby", "Pip", "Nia"])
    crane_name = args.crane_name or rng.choice(["Yucko", "Hugo", "Cricky", "Pogo"])
    rhyme_word = rng.choice(sorted(RHYMES))
    return StoryParams(
        seed=None,
        name=name,
        crane_name=crane_name,
        place=PLACES[place],
        object=OBJECTS[obj],
        helper=HELPERS[helper],
        rhyme_word=rhyme_word,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld about yucko, naughty crane, repetition, foreshadowing, and misunderstanding."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--crane-name")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, obj, helper in combos:
            print(f"  {place:5} {obj:6} {helper:6}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, obj, helper in valid_combos():
            params = StoryParams(
                seed=base_seed,
                name="Mina",
                crane_name="Yucko",
                place=PLACES[place],
                object=OBJECTS[obj],
                helper=HELPERS[helper],
                rhyme_word="boom",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.crane_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
