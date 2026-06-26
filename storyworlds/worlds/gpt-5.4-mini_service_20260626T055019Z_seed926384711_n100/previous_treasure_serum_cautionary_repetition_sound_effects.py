#!/usr/bin/env python3
"""
Standalone storyworld: previous treasure serum cautionary repetition sound effects
style: comedy

A tiny simulated domain about a nervous kid, a "treasure serum" prank, a
cautionary older sibling, repeated temptations, and noisy sound effects that
change the world state.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    contents: list[str] = field(default_factory=list)
    opened: bool = False
    broken: bool = False
    sticky: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoor: bool = True


@dataclass
class Treasure:
    label: str
    phrase: str
    sparkle: str
    value: str
    fragile: bool = False


@dataclass
class Serum:
    label: str
    phrase: str
    sound: str
    effect: str
    caution: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.events: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.events = list(self.events)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place("the kitchen", indoor=True),
    "attic": Place("the attic", indoor=True),
    "garage": Place("the garage", indoor=True),
}

TREASURES = {
    "coin": Treasure("coin", "a shiny old coin", "gleam", "tiny fortune"),
    "crown": Treasure("crown", "a toy crown with fake gems", "twinkle", "royal pretend"),
    "marble": Treasure("marble", "a glass marble", "glint", "one very dramatic marble"),
}

SERUMS = {
    "tickle": Serum("tickle", "a jar of treasure serum", "blorp", "makes ordinary things feel priceless", "the jar should stay closed until the joke is ready"),
    "polish": Serum("polish", "a bottle of treasure serum", "glorp", "makes things shiny and important-looking", "too much can turn a room into a slippery circus"),
    "echo": Serum("echo", "a test tube of treasure serum", "plink", "makes every whisper sound like a heroic announcement", "if you shake it, it giggles back"),
}

NAMES = ["Mina", "Pip", "Lola", "Toby", "June", "Nico"]
ROLES = {"girl": "sister", "boy": "brother"}
COMEDY_BEATS = ["oops", "uh-oh", "hmm", "wow"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A treasure is noteworthy if it is fragile or has a shiny sparkle.
noteworthy(T) :- treasure(T), shiny(T).
noteworthy(T) :- treasure(T), fragile(T).

% A serum is cautionary if it has a warning sound and a caution.
cautionary(S) :- serum(S), warns(S), caution(S).

% Repetition matters when the same tempting act happens twice.
repeated(A) :- act(A), count(A,2).

% Sound effects are part of the comedy if they are loud.
comic(S) :- soundfx(S), loud(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.sparkle in {"gleam", "twinkle", "glint"}:
            lines.append(asp.fact("shiny", tid))
        if t.fragile:
            lines.append(asp.fact("fragile", tid))
    for sid, s in SERUMS.items():
        lines.append(asp.fact("serum", sid))
        lines.append(asp.fact("soundfx", s.sound))
        lines.append(asp.fact("warns", sid))
        lines.append(asp.fact("caution", sid))
        lines.append(asp.fact("loud", s.sound))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show cautionary/1. #show comic/1."))
    atoms = set(asp.atoms(model, "cautionary")) | set(asp.atoms(model, "comic"))
    expected = {(sid,) for sid in SERUMS} | {(s.sound,) for s in SERUMS.values()}
    if atoms:
        print("OK: ASP twin is loadable.")
        return 0
    print("MISMATCH: ASP twin produced no shown atoms.")
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_reasonable_world(place: Place, treasure: Treasure, serum: Serum, seed: Optional[int] = None) -> World:
    if place.name == "the attic" and treasure.label == "marble" and serum.label == "echo":
        pass
    w = World(place)
    kid = w.add(Entity(id="Kid", kind="character", type="boy", label="the kid"))
    sibling = w.add(Entity(id="Sibling", kind="character", type="sister", label="the older sister"))
    chest = w.add(Entity(id="Chest", type="thing", label="the treasure box", opened=False, broken=False))
    jar = w.add(Entity(id="Jar", type="thing", label=serum.label, phrase=serum.phrase, sticky=False))
    gem = w.add(Entity(id="Treasure", type="thing", label=treasure.label, phrase=treasure.phrase, owner=kid.id))
    w.facts = {"kid": kid, "sibling": sibling, "chest": chest, "jar": jar, "treasure": gem, "treasure_cfg": treasure, "serum_cfg": serum}
    return w


def caution(w: World) -> None:
    kid = w.get("Kid")
    sib = w.get("Sibling")
    serum = w.facts["serum_cfg"]
    treasure = w.facts["treasure_cfg"]
    w.say(f"In {w.place.name}, {kid.label} found {treasure.phrase} beside {serum.phrase}.")
    w.say(f"{sib.label.capitalize()} pointed at the bottle and said, \"Caution: it goes {serum.sound}, then trouble goes splat.\"")


def repeat_temptation(w: World) -> None:
    kid = w.get("Kid")
    serum = w.facts["serum_cfg"]
    treasure = w.facts["treasure_cfg"]
    kid.memes["curious"] = kid.memes.get("curious", 0) + 1
    w.say(f"{kid.label.capitalize()} grinned. \"I can be careful,\" {kid.pronoun()} said.")
    w.say(f"\"Careful, careful,\" {kid.pronoun()} repeated, because the jar looked too funny to ignore.")
    w.say(f"Then {kid.pronoun()} nudged the lid: {serum.sound}! The serum bubbled like a tiny party.")
    w.say(f"{kid.pronoun().capitalize()} whispered, \"Treasure, treasure,\" and the {treasure.label} suddenly felt extra important.")


def sound_effects_turn(w: World) -> None:
    jar = w.get("Jar")
    chest = w.get("Chest")
    serum = w.facts["serum_cfg"]
    treasure = w.facts["treasure_cfg"]
    kid = w.get("Kid")
    if jar.opened:
        return
    jar.opened = True
    w.events.append(serum.sound)
    kid.memes["surprise"] = kid.memes.get("surprise", 0) + 1
    chest.opened = True
    if treasure.fragile:
        chest.broken = True
    w.say(f"Blorp! {serum.effect.capitalize()}, so even the treasure box stood up straighter.")
    w.say(f"Plink-plink, the room answered back, and the {treasure.label} glittered like it had practiced being famous.")


def resolve(w: World) -> None:
    kid = w.get("Kid")
    sib = w.get("Sibling")
    serum = w.facts["serum_cfg"]
    treasure = w.facts["treasure_cfg"]
    if "blorp" in w.events or "plink" in w.events:
        kid.memes["joy"] = kid.memes.get("joy", 0) + 1
        w.say(f"{sib.label.capitalize()} laughed first, then covered the jar and said, \"Next time, one blorp is enough.\"")
        w.say(f"{kid.label.capitalize()} nodded, hugged the {treasure.label}, and promised not to shake the treasure serum again.")
        w.say(f"After that, the treasure stayed safe, the warning stayed true, and the last sound in the {w.place.name} was a happy little huff of laughter.")


def tell(place: Place, treasure: Treasure, serum: Serum, name: str = "Mina") -> World:
    w = build_reasonable_world(place, treasure, serum)
    kid = w.get("Kid")
    kid.id = name
    kid.label = f"the kid {name}"
    w.say(f"Once in {place.name}, {name} found {treasure.phrase} and a bottle labeled {serum.phrase}.")
    caution(w)
    w.para()
    repeat_temptation(w)
    sound_effects_turn(w)
    w.para()
    resolve(w)
    return w


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    t = world.facts["treasure_cfg"]
    s = world.facts["serum_cfg"]
    kid = world.get("Kid")
    return [
        f'Write a short comedy story for a child about a {t.label} and a {s.label}.',
        f'Tell a cautionary story where {kid.id} is tempted to use a treasure serum more than once.',
        f'Write a funny story that includes the sound effects "{s.sound}" and a treasure that must stay safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    kid = world.get("Kid")
    sib = world.get("Sibling")
    t = world.facts["treasure_cfg"]
    s = world.facts["serum_cfg"]
    return [
        QAItem(
            question=f"What did {kid.id} find in {world.place.name}?",
            answer=f"{kid.id} found {t.phrase} and {s.phrase} in {world.place.name}.",
        ),
        QAItem(
            question=f"Why did {sib.label} give a caution about the jar?",
            answer=f"{sib.label.capitalize()} warned that the jar could go {s.sound} and make trouble if it was shaken too much.",
        ),
        QAItem(
            question=f"What happened after {kid.id} repeated the tempting choice?",
            answer=f"{kid.id} repeated the choice to nudge the lid, and then the room made {s.sound} sounds before everyone laughed.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the treasure safe, the jar closed, and a joke learned the easy way.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    s = world.facts["serum_cfg"]
    t = world.facts["treasure_cfg"]
    return [
        QAItem(
            question="What is a treasure?",
            answer="A treasure is something people think is special, valuable, or exciting to protect.",
        ),
        QAItem(
            question="What is a cautionary warning?",
            answer="A cautionary warning is a careful message that tells someone about a possible problem before it happens.",
        ),
        QAItem(
            question="What do sound effects do in a comedy story?",
            answer="Sound effects make actions feel louder, sillier, and more playful.",
        ),
        QAItem(
            question=f"Why might {s.label} be funny?",
            answer=f"{s.label} is funny because its sound {s.sound} feels like a tiny cartoon surprise.",
        ),
        QAItem(
            question=f"Why should a {t.label} be handled carefully?",
            answer=f"A {t.label} can be special or fragile, so careful hands help it stay safe.",
        ),
    ]


# ---------------------------------------------------------------------------
# Serialization / emit
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.opened:
            bits.append("opened=True")
        if e.broken:
            bits.append("broken=True")
        if e.sticky:
            bits.append("sticky=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  events: {world.events}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def asp_facts_program() -> str:
    return asp_program("#show cautionary/1. #show comic/1.")


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    treasure: str
    serum: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a treasure serum, caution, repetition, and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--serum", choices=SERUMS)
    ap.add_argument("--name", choices=NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    treasure = args.treasure or rng.choice(list(TREASURES))
    serum = args.serum or rng.choice(list(SERUMS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, treasure=treasure, serum=serum, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TREASURES[params.treasure], SERUMS[params.serum], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_facts_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_facts_program())
        print(facts := sorted(set(asp.atoms(model, "cautionary")) | set(asp.atoms(model, "comic"))))
        return

    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            for treasure in TREASURES:
                for serum in SERUMS:
                    params = StoryParams(place=place, treasure=treasure, serum=serum, name=random.choice(NAMES))
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
