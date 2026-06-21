#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sillydilly_precede_repetition_foreshadowing_curiosity_space_adventure.py
========================================================================================================

A tiny storyworld in a space-adventure mode for the seed words and instruments:
"sillydilly", "precede", repetition, foreshadowing, and curiosity.

Premise:
- Two kids on a small ship hear a strange repeated sound.
- A curious check reveals a silly problem before it becomes serious.
- The story repeats a key phrase, plants a clue, and ends with a bright proof of change.

This file is self-contained except for the shared result containers and the
lazy ASP helper imported only in ASP modes.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Ship:
    id: str
    label: str
    hall: str
    window: str
    deck: str
    repeat_sound: str
    clue: str
    curiosity_item: str
    safe_fix: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    flags: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    ship: str
    crew: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    adult: str
    clue_item: str
    fix: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    ship = world.get("ship")
    for e in world.characters():
        if e.meters["alarm"] >= THRESHOLD and ("alarm", e.id) not in world.fired:
            world.fired.add(("alarm", e.id))
            ship.meters["tension"] += 1
            out.append("__alarm__")
    return out


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    ship = world.get("ship")
    if ship.meters["repeat"] < THRESHOLD:
        return out
    if ("repeat", ship.id) in world.fired:
        return out
    world.fired.add(("repeat", ship.id))
    for e in world.characters():
        e.memes["curiosity"] += 1
    ship.meters["tension"] += 1
    out.append("__repeat__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm), Rule("repeat", "social", _r_repeat)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def _do_noise(world: World, ship: Ship, narrate: bool = True) -> None:
    world.get("ship").meters["repeat"] += 1
    world.get("ship").meters["oddness"] += 1
    world.get("ship").meters["clue"] += 1
    propagate(world, narrate=narrate)


def predict_noise(world: World, ship: Ship) -> dict:
    sim = world.copy()
    _do_noise(sim, ship, narrate=False)
    return {"tension": sim.get("ship").meters["tension"], "oddness": sim.get("ship").meters["oddness"]}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SHIPS:
        for clue in CLUES:
            for fix in FIXES:
                if clue.reveals == fix.solves:
                    combos.append((s.id, clue.id, fix.id))
    return combos


def explain_rejection(clue: "Clue", fix: "Fix") -> str:
    return (
        f"(No story: the clue '{clue.label}' does not point to the same problem "
        f"that '{fix.label}' fixes. This world only tells stories where curiosity "
        f"can honestly solve the mystery.)"
    )


def tell(ship: Ship, clue: "Clue", fix: "Fix", child1: str, child1_gender: str,
         child2: str, child2_gender: str, adult: str, crew: str) -> World:
    world = World()
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, role="curious"))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, role="helper"))
    captain = world.add(Entity(id=adult, kind="character", type="adult", role="adult", label="the captain"))
    ship_ent = world.add(Entity(id="ship", type="ship", label=ship.label))
    ship_ent.meters["tension"] = 0.0

    world.say(
        f"{a.id} and {b.id} floated aboard {ship.label}, a little space ship with "
        f"{ship.hall}, {ship.window}, and {ship.deck}."
    )
    world.say(
        f'The ship made a tiny sound: "{ship.repeat_sound}" Then it made it again: '
        f'"{ship.repeat_sound}"'
    )
    world.say(
        f'{a.id} tilted {a.pronoun("possessive")} head. "That sound is so '
        f'sillydilly," {a.id} said.'
    )
    world.say(
        f'{b.id} laughed. "Sillydilly, sillydilly," {b.id} said, because the sound '
        f'kept coming back.'
    )

    world.para()
    world.say(
        f"{ship.clue} peeked from behind a panel, and that was the clue that "
        f"came before the trouble."
    )
    world.say(
        f"{a.id}'s curiosity grew. {a.id} wanted to look first, because curiosity "
        f"often precedes a good idea."
    )
    world.say(
        f"{b.id} pointed at the clue item and asked what it meant, while the ship "
        f"gave one more soft {ship.repeat_sound}."
    )

    world.para()
    pred = predict_noise(world, ship)
    a.meters["alarm"] += 1
    world.facts["prediction"] = pred
    world.facts["clue"] = clue
    world.facts["fix"] = fix
    world.facts["ship"] = ship
    world.facts["adult"] = captain
    world.facts["children"] = (a, b)
    world.say(
        f"{a.id} opened the panel and found {clue.label}. That was the thing "
        f"that had been making the sillydilly sound."
    )
    world.say(
        f"It was not dangerous, just stuck in a funny way, but {a.id} wanted to "
        f"check before anything else happened."
    )
    _do_noise(world, ship, narrate=False)
    world.say(
        f"The ship hummed again, and the clue made sense at once."
    )

    world.para()
    world.say(
        f"{captain.id} came over and smiled. In a calm voice, {captain.id} used "
        f"{fix.label} to {fix.action}."
    )
    world.say(
        f"At once, the sillydilly sound stopped. The ship got quieter, and the "
        f"tension in the air went away."
    )
    world.say(
        f"{a.id} and {b.id} repeated their new rule: when a clue appears, look "
        f"carefully first, then ask a grown-up if needed."
    )

    world.para()
    world.say(
        f"At the end, {ship.label} sailed on with {ship.safe_fix}, a steady glow "
        f"from the console, and two curious kids grinning at the stars."
    )

    world.facts["outcome"] = "solved"
    return world


@dataclass
class Clue:
    id: str
    label: str
    reveals: str


@dataclass
class Fix:
    id: str
    label: str
    solves: str
    action: str


SHIPS = [
    Ship(
        id="comet",
        label="the Comet",
        hall="a moonlit hallway",
        window="a round bubble window",
        deck="a bouncy silver deck",
        repeat_sound="sillydilly",
        clue="A tiny blinking sticker",
        curiosity_item="sticker",
        safe_fix="a clean, humming path",
    ),
    Ship(
        id="starling",
        label="the Starling",
        hall="a narrow hallway with blue lights",
        window="a window full of stars",
        deck="a bright observation deck",
        repeat_sound="sillydilly",
        clue="A loose panel that flashed",
        curiosity_item="panel",
        safe_fix="a quiet, shining route",
    ),
]

CLUES = [
    Clue(id="sticker", label="a tiny blinking sticker", reveals="sticker"),
    Clue(id="panel", label="a loose panel that flashed", reveals="panel"),
]

FIXES = [
    Fix(id="tighten", label="a small wrench", solves="panel", action="tighten the loose panel"),
    Fix(id="remove_sticker", label="a soft cloth", solves="sticker", action="lift off the blinking sticker"),
]


GIRL_NAMES = ["Mia", "Ava", "Luna", "Nia", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Max", "Eli"]
TRAITS = ["curious", "bright", "careful", "cheerful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ship = f["ship"]
    return [
        f'Write a space-adventure story for a 3-to-5-year-old that includes the word "sillydilly".',
        f'Write a story where curiosity precedes a helpful fix on {ship.label}, and a grown-up solves a small mystery.',
        f'Write a repeated, foreshadowed space story where kids hear "{ship.repeat_sound}" again and again before they find the clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["children"]
    ship: Ship = f["ship"]
    clue: Clue = f["clue"]
    fix: Fix = f["fix"]
    return [
        QAItem(
            question="Why did the children keep hearing the strange sound?",
            answer=f"They heard it because something on {ship.label} was stuck in a silly way. The repeated sound was a clue that preceded the fix.",
        ),
        QAItem(
            question=f"What did {a.id} do when the clue appeared?",
            answer=f"{a.id} looked carefully first because {a.id} was curious. That curiosity helped them find the real problem before it grew into a bigger worry.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"The captain used {fix.label} to {fix.action}. After that, the sillydilly sound stopped and the ship became quiet again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to look, ask, and learn about something new. It helps you notice clues and understand what is happening.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue before something important happens. It helps the reader get ready for the next event.",
        ),
        QAItem(
            question="Why do stories repeat a word sometimes?",
            answer="Repeating a word can make it feel catchy and important. It can also help readers remember the clue or sound that matters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(ship="comet", crew="crew", child1="Mina", child1_gender="girl", child2="Bo", child2_gender="boy", adult="Captain Ray", clue_item="sticker", fix="remove_sticker", seed=1),
    StoryParams(ship="starling", crew="crew", child1="Leo", child1_gender="boy", child2="Nia", child2_gender="girl", adult="Captain Zed", clue_item="panel", fix="tighten", seed=2),
]


def _choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    ship = args.ship or rng.choice(list({s.id for s in SHIPS}))
    clue = args.clue or rng.choice(list({c.id for c in CLUES}))
    fix = args.fix or rng.choice(list({f.id for f in FIXES}))
    if clue == "sticker" and fix == "tighten":
        raise StoryError(explain_rejection(CLUES[0], FIXES[0]))
    if clue == "panel" and fix == "remove_sticker":
        raise StoryError(explain_rejection(CLUES[1], FIXES[1]))
    c1g = args.child1_gender or rng.choice(["girl", "boy"])
    c2g = args.child2_gender or ("boy" if c1g == "girl" else "girl")
    child1 = args.child1 or _choose_name(rng, c1g)
    child2 = args.child2 or _choose_name(rng, c2g)
    adult = args.adult or "Captain" + " " + rng.choice(["Ray", "Nova", "Juno", "Vale"])
    return StoryParams(ship=ship, crew="crew", child1=child1, child1_gender=c1g, child2=child2, child2_gender=c2g, adult=adult, clue_item=clue, fix=fix)


def generate(params: StoryParams) -> StorySample:
    ship = next((s for s in SHIPS if s.id == params.ship), None)
    clue = next((c for c in CLUES if c.id == params.clue_item), None)
    fix = next((f for f in FIXES if f.id == params.fix), None)
    if not ship or not clue or not fix:
        raise StoryError("Invalid story parameters.")
    if clue.reveals != fix.solves:
        raise StoryError(explain_rejection(clue, fix))
    world = tell(ship, clue, fix, params.child1, params.child1_gender, params.child2, params.child2_gender, params.adult, params.crew)
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


def asp_facts() -> str:
    import asp
    lines = []
    for s in SHIPS:
        lines.append(asp.fact("ship", s.id))
    for c in CLUES:
        lines.append(asp.fact("clue", c.id))
        lines.append(asp.fact("reveals", c.id, c.reveals))
    for f in FIXES:
        lines.append(asp.fact("fix", f.id))
        lines.append(asp.fact("solves", f.id, f.solves))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,F) :- ship(S), clue(C), fix(F), reveals(C,R), solves(F,R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate/emit smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with repetition, foreshadowing, and curiosity.")
    ap.add_argument("--ship", choices=[s.id for s in SHIPS])
    ap.add_argument("--clue", choices=[c.id for c in CLUES])
    ap.add_argument("--fix", choices=[f.id for f in FIXES])
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--n", type=int, default=1)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
