#!/usr/bin/env python3
"""
storyworlds/worlds/tidy_whir_puss_suspense_folk_tale.py
=======================================================

A small folk-tale storyworld about a tidy little puss, a whirring old helper,
and a bit of suspense in a cottage by the lane.

Seed tale:
---
Once, in a cottage by the lane, a tidy little puss named Pippa loved order. One
evening, the old hall lamp began to whir and dim, and the whole room felt
strange. Granny said the lamp would settle if someone found the missing brass
key for the latch box. Pippa followed the whir to the pantry, then to the loft,
and she felt nervous when the shadows grew long. At last she found the key
under a folded cloth, set everything neat again, and the lamp glowed softly.

World model:
---
- The cottage has rooms and a lamp whose brightness depends on a latch box.
- The lamp can whir when the latch box is open or jammed.
- The puss can search rooms; searching raises suspense.
- Finding the brass key lets the hero close the latch box.
- Closing the latch box quiets the whir, settles the lamp, and ends the suspense.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "puss"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str
    home: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        clone = World(self.params)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


HOMES = {
    "cottage": "a small cottage by the lane",
    "farmhouse": "a warm farmhouse at the hill's foot",
    "millhouse": "an old millhouse near the stream",
}
HELPERS = {
    "lamp": "old lamp",
    "wheel": "spinning wheel",
    "kettle": "kettle",
}
ROOMS = ["kitchen", "pantry", "loft", "hall"]
THRESHOLD = 1.0


ASP_RULES = r"""
room(kitchen). room(pantry). room(loft). room(hall).
can_search(kitchen). can_search(pantry). can_search(loft). can_search(hall).

searching(R) :- can_search(R).
suspense(R) :- searching(R).
key_found :- in_room(key, pantry).
key_found :- in_room(key, loft).
resolved :- key_found.
whirring :- lamp_open.
quiet :- resolved.
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("home", "cottage"),
        asp.fact("helper", "lamp"),
        asp.fact("puss", "puss"),
        asp.fact("room", "kitchen"),
        asp.fact("room", "pantry"),
        asp.fact("room", "loft"),
        asp.fact("room", "hall"),
        asp.fact("in_room", "key", "pantry"),
        asp.fact("lamp_open"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world with a tidy puss, a whirring lamp, and suspense.")
    ap.add_argument("--name")
    ap.add_argument("--home", choices=sorted(HOMES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    home = args.home or rng.choice(sorted(HOMES))
    helper = args.helper or rng.choice(sorted(HELPERS))
    name = args.name or rng.choice(["Pippa", "Mabel", "Tilly", "Nell", "Mina"])
    return StoryParams(name=name, home=home, helper=helper)


def _build_world(params: StoryParams) -> World:
    w = World(params)
    hero = w.add(Entity(id="puss", kind="character", type="puss", label=params.name))
    granny = w.add(Entity(id="granny", kind="character", type="grandmother", label="Granny"))
    helper = w.add(Entity(
        id="helper",
        kind="thing",
        type=params.helper,
        label=HELPERS[params.helper],
        phrase=HELPERS[params.helper],
        location="hall",
        meters={"whirr": 0.0},
        memes={"mystery": 0.0},
    ))
    key = w.add(Entity(id="key", kind="thing", type="key", label="brass key", phrase="a brass key", location="pantry"))
    lamp = w.add(Entity(id="lamp", kind="thing", type="lamp", label="lamp", phrase="the old lamp", location="hall", meters={"whirr": 1.0, "glow": 0.0}, memes={"suspense": 0.0}))
    box = w.add(Entity(id="box", kind="thing", type="box", label="latch box", phrase="the latch box", location="hall", meters={"open": 1.0}, memes={}))
    w.facts.update(hero=hero, granny=granny, helper=helper, key=key, lamp=lamp, box=box)
    return w


def _narrate_setup(w: World) -> None:
    p: Entity = w.facts["hero"]  # type: ignore[assignment]
    g: Entity = w.facts["granny"]  # type: ignore[assignment]
    home = HOMES[w.params.home]
    w.say(f"Once, in {home}, there lived a tidy little puss named {p.label}.")
    w.say(f"{p.label} liked to set cups straight and fold cloths smooth, for {p.pronoun('subject')} loved a neat room.")
    w.say(f"Granny lived there too, and she kept an old {HELPERS[w.params.helper]} that could make a soft {w.params.helper} sound when it worked.")
    w.para()
    w.say(f"One evening, the hall lamp began to whir.")
    w.say(f"The light went dim, and the cottage felt hushed, as if it were waiting for something.")

def _search_room(w: World, room: str) -> None:
    p: Entity = w.facts["hero"]  # type: ignore[assignment]
    lamp: Entity = w.facts["lamp"]  # type: ignore[assignment]
    key: Entity = w.facts["key"]  # type: ignore[assignment]
    if room in w.fired:
        return
    w.fired.add(room)
    p.memes["suspense"] = p.memes.get("suspense", 0.0) + 1.0
    lamp.meters["whirr"] = lamp.meters.get("whirr", 0.0) + 0.5
    w.say(f"{p.label} padded into the {room}, listening hard.")
    w.say(f"The old house seemed to hold its breath, and the whir followed her like a thread.")
    if key.location == room:
        w.say(f"Under a folded cloth, {p.pronoun('subject')} found a brass key at last.")
        w.facts["found_key"] = True

def _resolve(w: World) -> None:
    p: Entity = w.facts["hero"]  # type: ignore[assignment]
    granny: Entity = w.facts["granny"]  # type: ignore[assignment]
    lamp: Entity = w.facts["lamp"]  # type: ignore[assignment]
    box: Entity = w.facts["box"]  # type: ignore[assignment]
    if not w.facts.get("found_key"):
        return
    box.meters["open"] = 0.0
    lamp.meters["whirr"] = 0.0
    lamp.meters["glow"] = 1.0
    p.memes["suspense"] = 0.0
    w.say(f"{p.label} carried the brass key to the hall and turned it in the latch box.")
    w.say(f"The whir faded away, and the lamp gave a gentle gold glow.")
    w.say(f"Granny smiled and stroked {p.pronoun('possessive')} head. “That was a clever, tidy puss,” she said.")
    w.say(f"And so the cottage grew calm again, with no shadow left to frighten the evening.")

def generate(params: StoryParams) -> StorySample:
    w = _build_world(params)
    _narrate_setup(w)
    w.para()
    _search_room(w, "hall")
    _search_room(w, "pantry")
    _search_room(w, "loft")
    _resolve(w)
    w.facts["resolved"] = bool(w.facts.get("found_key"))
    w.facts["searched_rooms"] = ["hall", "pantry", "loft"]
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def generation_prompts(world: World) -> list[str]:
    p: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a short folk tale about a tidy puss named {p.label} in a cottage where something begins to whir.",
        f"Tell a suspenseful story for a small child about {p.label} finding a brass key and making the house calm again.",
        f"Write a gentle story with a whirring lamp, a neat little cat, and a happy ending in a cottage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the tidy little puss in the story?",
            answer=f"The tidy little puss was {p.label}. {p.pronoun('subject').capitalize()} loved to keep things neat.",
        ),
        QAItem(
            question="What made the cottage feel suspenseful?",
            answer="The old lamp began to whir and grow dim, and the house felt as if it were waiting for something.",
        ),
        QAItem(
            question="What did the puss find in the pantry or loft?",
            answer="The puss found a brass key, which helped close the latch box and quiet the whirring lamp.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The key turned the latch box shut, the lamp glowed softly, and the cottage became calm again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lamp do when it gives a soft glow?",
            answer="A lamp gives light, so people can see better in a room when it is dark.",
        ),
        QAItem(
            question="Why might a cottage feel quiet at night?",
            answer="A cottage can feel quiet at night because people move slowly, speak softly, and settle in for rest.",
        ),
        QAItem(
            question="What is a key used for?",
            answer="A key is used to open or close something that has a lock or latch.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    program = asp_program("#show resolved/0.\n#show whirring/0.\n#show quiet/0.")
    model = asp.one_model(program)
    shown = set((a.name, len(a.arguments)) for a in model)
    expect = {("resolved", 0), ("whirring", 0), ("quiet", 0)}
    if expect.issubset(shown) or expect == shown:
        print("OK: ASP rules grounded and solved.")
        return 0
    print("MISMATCH: ASP model did not contain expected atoms.")
    print(shown)
    return 1


def build_asp_combo_program() -> str:
    return asp_program("#show resolved/0.\n#show whirring/0.\n#show quiet/0.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_combo_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(build_asp_combo_program())
        atoms = [(a.name, len(a.arguments)) for a in model]
        print("ASP atoms:", atoms)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = [
            StoryParams(name="Pippa", home="cottage", helper="lamp"),
            StoryParams(name="Mabel", home="farmhouse", helper="wheel"),
            StoryParams(name="Tilly", home="millhouse", helper="kettle"),
        ]
        samples = [generate(p) for p in params]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
