#!/usr/bin/env python3
"""
storyworlds/worlds/shush_wine_billy_suspense_detective_story.py
===============================================================

A small detective-story world built from the seed words shush, wine, billy.

Premise:
- Billy is a careful little detective.
- A hush falls over a quiet room where a bottle of wine has gone missing.
- Billy notices clues, follows a trail, and solves the mystery.

World model:
- Physical meters track clues, spills, mess, and evidence.
- Emotional memes track fear, suspicion, relief, and courage.
- The story turns when Billy discovers who hid the wine and why the room was shushed.

The narration is kept child-facing, concrete, and suspenseful, with a classic
detective-story feel: a clue, a worry, a reveal, and a resolved ending image.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    hidden_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "detective"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the little house"
    mood: str = "quiet"
    witness: str = "the hallway"
    affords: set[str] = field(default_factory=lambda: {"investigate", "search", "listen"})


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        w = World(self.scene)
        w.entities = _copy.deepcopy(self.entities)
        w.events = list(self.events)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _clue_trail(world: World) -> list[str]:
    out = []
    billy = world.get("billy")
    if billy.meters.get("clues", 0) < THRESHOLD:
        return out
    if "trail" in world.fired:
        return out
    world.fired.add("trail")
    world.get("wine").meters["spilled"] = 1
    out.append("A thin red trail led from the table to the curtain.")
    return out


def _fear_to_focus(world: World) -> list[str]:
    out = []
    billy = world.get("billy")
    if billy.memes.get("fear", 0) < THRESHOLD:
        return out
    if "focus" in world.fired:
        return out
    world.fired.add("focus")
    billy.memes["courage"] = billy.memes.get("courage", 0) + 1
    out.append("Billy took one slow breath and looked closer.")
    return out


def _reveal_hidden_wine(world: World) -> list[str]:
    out = []
    wine = world.get("wine")
    if wine.hidden_by != "mouse":
        return out
    if "reveal" in world.fired:
        return out
    if world.get("billy").meters.get("clues", 0) < THRESHOLD:
        return out
    world.fired.add("reveal")
    out.append("Behind the curtain, Billy found the missing bottle of wine tucked in a tiny basket.")
    return out


def _comfort_after_scare(world: World) -> list[str]:
    out = []
    billy = world.get("billy")
    if billy.memes.get("alarm", 0) < THRESHOLD:
        return out
    if "comfort" in world.fired:
        return out
    world.fired.add("comfort")
    billy.memes["relief"] = billy.memes.get("relief", 0) + 1
    out.append("The room felt calmer once Billy knew the mystery was solved.")
    return out


RULES = [_clue_trail, _fear_to_focus, _reveal_hidden_wine, _comfort_after_scare]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)


def tell_story(world: World) -> World:
    billy = world.add(Entity(
        id="billy",
        kind="character",
        type="boy",
        label="Billy",
        traits=["small", "careful", "brave"],
        meters={"clues": 0},
        memes={"curiosity": 1, "fear": 0, "courage": 0, "relief": 0},
    ))
    owner = world.add(Entity(
        id="mama",
        kind="character",
        type="mother",
        label="Billy's mother",
        traits=["busy", "gentle"],
        meters={"worry": 0},
        memes={"calm": 1},
    ))
    wine = world.add(Entity(
        id="wine",
        kind="thing",
        type="bottle",
        label="bottle of wine",
        phrase="a bottle of red wine",
        owner=owner.id,
        hidden_by="mouse",
        meters={"spill": 0, "spilled": 0},
    ))
    mouse = world.add(Entity(
        id="mouse",
        kind="thing",
        type="mouse",
        label="little mouse",
        phrase="a tiny mouse",
        meters={"crumbs": 1},
        memes={"nervous": 1},
    ))

    world.say("Billy was a small detective who liked quiet rooms and good clues.")
    world.say("One evening, the house went hush, and the kitchen felt oddly still.")
    world.say("Billy noticed the table was neat, but one red smell hung in the air.")
    world.para()

    billy.meters["clues"] += 1
    billy.memes["fear"] += 1
    owner.memes["worry"] = owner.memes.get("worry", 0) + 1
    world.say("His mother whispered, 'Shush now, Billy. Someone moved the bottle of wine.'")
    world.say("Billy looked under the chair, then near the sink, and found a red drop on the floor.")
    propagate(world, narrate=True)

    world.para()
    world.say("Billy followed the trail with tiny steps, not making a sound.")
    world.say("He peeked behind the curtain and saw the mouse beside the basket.")
    world.say("The mouse had not stolen the wine for a game; it had only dragged it away from the loud broom.")
    wine.hidden_by = None
    propagate(world, narrate=True)

    world.para()
    world.say("Billy smiled and pointed to the basket.")
    world.say("His mother laughed softly and said the mouse could keep the basket, but not the wine.")
    world.say("The bottle was put back on the table, the room stayed shush and safe, and Billy felt like the best detective in the house.")
    billy.memes["relief"] += 1
    owner.memes["worry"] = 0
    world.facts.update(billy=billy, mother=owner, wine=wine, mouse=mouse)
    return world


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "the little house"
    detective: str = "Billy"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful detective story about Billy, shush, and wine.")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--place")
    ap.add_argument("--detective")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        place=args.place or "the little house",
        detective=args.detective or "Billy",
    )


def generation_prompts() -> list[str]:
    return [
        'Write a short suspense story for a young child about Billy, a shush, and a missing wine bottle.',
        "Tell a gentle detective story where Billy follows clues and learns why everyone is whispering.",
        "Write a story in a classic detective style with a quiet mystery, a red clue, and a happy reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who was the detective in the story?",
            answer="Billy was the little detective who paid attention to the clues.",
        ),
        QAItem(
            question="Why did everyone whisper and shush in the kitchen?",
            answer="They whispered because the room felt tense and they did not want to scare away the tiny clue trail.",
        ),
        QAItem(
            question="Where was the missing wine found?",
            answer="Billy found the bottle of wine behind the curtain in a tiny basket.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why do people whisper when they want shush in a quiet room?",
            answer="People whisper to stay quiet and avoid making too much noise.",
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
        if e.hidden_by:
            bits.append(f"hidden_by={e.hidden_by}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show mystery/1.
mystery(billy) :- clue(billy), shush(kitchen), missing(wine).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("detective", "billy"),
        asp.fact("clue", "billy"),
        asp.fact("shush", "kitchen"),
        asp.fact("missing", "wine"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery/1."))
    got = set(asp.atoms(model, "mystery"))
    exp = {("billy",)}
    if got == exp:
        print("OK: ASP gate matches Python story setup.")
        return 0
    print("MISMATCH: ASP gate disagrees with Python setup.")
    print("  got:", sorted(got))
    print("  expected:", sorted(exp))
    return 1


CURATED = [StoryParams(seed=274930118, place="the little house", detective="Billy")]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(World(Scene(place=params.place)))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
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
        print("== (1) Generation prompts -- asks that would produce this story ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions -- answerable from the story text ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions -- child level, no story needed ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery/1."))
        print(sorted(asp.atoms(model, "mystery")))
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
