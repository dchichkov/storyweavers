#!/usr/bin/env python3
"""
storyworlds/worlds/gasp_breaker_obey_sharing_rhyme_whodunit.py
==============================================================

A small whodunit-style story world about a missing shared thing, a careful clue
trail, a breaker-box mishap, and a tidy reveal.

Seed tale:
---
At school, Mina and Oren were sharing crayons and singing a rhyme for fun.
Then there was a gasp. The lights went out. Everyone looked at the breaker.
Mina wanted to obey the teacher and stay calm, but Oren noticed tiny clues:
a smudge near the breaker, a dropped ribbon, and the rhyme ending in a snap.
Who had turned the lights off? It turned out the room had not been haunted at
all; the breaker had tripped when a jammed fan pulled too much power, and the
teacher fixed it while the children shared the flashlight and finished the rhyme.

This script models:
- typed entities with physical meters and emotional memes
- a tiny causal world: sharing, clues, breaker trip, suspicion, reveal
- a reasonableness gate and an inline ASP twin
- complete child-facing story prose plus QA
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man", "principal"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    detail: str
    afford: set[str] = field(default_factory=set)


@dataclass
class SharedThing:
    id: str
    label: str
    phrase: str
    ownerless: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Breaker:
    id: str
    label: str
    phrase: str
    can_trip: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_gasp(world: World) -> list[str]:
    out = []
    if world.get("room").meters["dark"] < THRESHOLD:
        return out
    sig = ("gasp",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["fear"] += 0.5
    out.append("A gasp rose in the room.")
    return out


def _r_trip(world: World) -> list[str]:
    out = []
    fan = world.entities.get("fan")
    breaker = world.entities.get("breaker")
    if not fan or not breaker:
        return out
    if fan.meters["power"] < 1.0 or fan.attrs.get("jammed") != True:
        return out
    sig = ("trip",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    breaker.meters["tripped"] = 1
    world.get("room").meters["dark"] = 1
    out.append("The breaker had tripped.")
    return out


def _r_clue(world: World) -> list[str]:
    out = []
    if world.get("room").meters["dark"] < THRESHOLD:
        return out
    clue = world.entities.get("clue")
    if clue and clue.meters["noticed"] < THRESHOLD:
        sig = ("clue",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        clue.meters["noticed"] = 1
        out.append("A tiny clue waited by the wall.")
    return out


CAUSAL_RULES = [
    Rule("gasp", "social", _r_gasp),
    Rule("trip", "physical", _r_trip),
    Rule("clue", "story", _r_clue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_trip(world: World) -> bool:
    sim = world.copy()
    fan = sim.get("fan")
    fan.attrs["jammed"] = True
    fan.meters["power"] = 1
    propagate(sim, narrate=False)
    return sim.get("breaker").meters["tripped"] >= THRESHOLD


@dataclass
class StoryParams:
    place: str
    child1: str
    child2: str
    teacher: str
    shared: str
    clue: str
    breaker_mode: str
    rhyme: str
    seed: Optional[int] = None


PLACES = {
    "classroom": Place("classroom", "the classroom", "a bright room with a low hum", {"sharing", "rhyme", "breaker"}),
    "art_room": Place("art_room", "the art room", "a table full of paper scraps and crayons", {"sharing", "rhyme", "breaker"}),
}

SHARED_THINGS = {
    "crayons": SharedThing("crayons", "crayons", "a little box of crayons", True, True, {"sharing"}),
    "cookies": SharedThing("cookies", "cookies", "a plate of cookies", True, True, {"sharing"}),
}

BREAKERS = {
    "breaker_box": Breaker("breaker_box", "breaker box", "the breaker box", True, {"breaker"}),
}

CLUES = {
    "ribbon": Clue("ribbon", "ribbon", "a red ribbon", "It matched the art project by the table.", {"rhyme", "sharing"}),
    "smudge": Clue("smudge", "smudge", "a dark smudge", "It pointed toward the fan and the breaker.", {"breaker"}),
}

RHYMES = {
    "ding": "ding and sing, the light will swing",
    "tap": "tap and clap, then solve the map",
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for shared in SHARED_THINGS:
            for clue in CLUES:
                combos.append((place, shared, clue))
    return combos


def reasonableness_check(place: str, shared: str, clue: str, breaker_mode: str) -> None:
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if shared not in SHARED_THINGS:
        raise StoryError("Unknown shared thing.")
    if clue not in CLUES:
        raise StoryError("Unknown clue.")
    if breaker_mode not in {"trip", "stuck"}:
        raise StoryError("Unknown breaker mode.")


def tell(place: Place, shared: SharedThing, clue: Clue, rhyme: str,
         child1: str = "Mina", child2: str = "Oren", teacher: str = "Ms. Vale",
         breaker_mode: str = "trip") -> World:
    world = World(place)
    room = world.add(Entity("room", type="room", label=place.label))
    room.meters["dark"] = 0
    room.memes["curiosity"] = 0

    a = world.add(Entity(child1, kind="character", type="girl", role="observer", label=child1))
    b = world.add(Entity(child2, kind="character", type="character", role="helper", label=child2))
    t = world.add(Entity(teacher, kind="character", type="teacher", role="adult", label=teacher))
    fan = world.add(Entity("fan", type="thing", label="fan"))
    breaker = world.add(Entity("breaker", type="thing", label="breaker box"))
    clue_ent = world.add(Entity("clue", type="thing", label=clue.label))

    a.memes["sharing"] = 1
    b.memes["sharing"] = 1
    a.memes["obey"] = 1
    b.memes["obey"] = 1
    fan.attrs["jammed"] = (breaker_mode == "trip")
    fan.meters["power"] = 1
    world.facts["rhyme"] = rhyme
    world.facts["shared"] = shared
    world.facts["clue"] = clue

    world.say(f"{a.id} and {b.id} were sharing {shared.phrase} in {place.label}.")
    world.say(f"They sang a little rhyme: '{rhyme}'.")
    world.para()
    world.say(f"Then came a gasp. The lights blinked, and the room went dim.")
    room.meters["dark"] = 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{b.id} obeyed {t.id} and stayed calm.")
    if clue.id == "ribbon":
        world.say(f"{a.id} spotted {clue.phrase}. {clue.reveal}")
    else:
        world.say(f"{a.id} spotted {clue.phrase}. {clue.reveal}")
    world.say(f"At the wall, the {breaker.label_word} was the answer.")
    if breaker_mode == "trip":
        breaker.meters["tripped"] = 1
        world.say(f"{t.id} fixed the {breaker.label_word}, and the lights came back.")
        a.memes["relief"] += 1
        b.memes["relief"] += 1
        room.meters["dark"] = 0
        world.para()
        world.say(f"The friends shared a flashlight and finished their rhyme together.")
    else:
        breaker.meters["tripped"] = 0
        world.say(f"But the breaker was not the answer after all.")
        world.para()
        world.say(f"{t.id} checked the fan, found it jammed, and set things right.")
        a.memes["relief"] += 1
        b.memes["relief"] += 1
        room.meters["dark"] = 0
        world.say(f"After that, they shared the crayons again and laughed softly.")
    world.facts.update(child1=a, child2=b, teacher=t, room=room, breaker=breaker, fan=fan)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly whodunit about {f['child1'].id} and {f['child2'].id} sharing {f['shared'].label} when a gasp and a breaker mystery happen.",
        f"Tell a short mystery story with sharing and rhyme where the breaker trips, the children obey the teacher, and the clue points to the fan.",
        f"Write a simple detective story for a small child that includes the words gasp, breaker, obey, sharing, and rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, t = f["child1"], f["child2"], f["teacher"]
    shared, clue = f["shared"], f["clue"]
    return [
        QAItem(
            question=f"Who were the story children sharing {shared.label}?",
            answer=f"{a.id} and {b.id} were sharing {shared.label}.",
        ),
        QAItem(
            question=f"What did {b.id} do when the lights went out?",
            answer=f"{b.id} obeyed {t.id} and stayed calm.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"{clue.phrase} helped point toward the answer.",
        ),
        QAItem(
            question="What was the answer to the mystery?",
            answer="The breaker had tripped, and the teacher fixed it after checking the fan.",
        ),
        QAItem(
            question=f"How did the story end after {t.id} helped?",
            answer="The lights came back, and the children shared again and finished their rhyme.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a breaker?", "A breaker is a safety switch that can trip to protect the lights."),
        QAItem("What does obey mean?", "Obey means to listen and do what a grown-up asks you to do."),
        QAItem("What does sharing mean?", "Sharing means letting someone else use or enjoy something too."),
        QAItem("What is a rhyme?", "A rhyme is a little poem or song where the words sound alike at the end."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        parts.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(parts)


ASP_RULES = r"""
place(P) :- room(P).
shared(S) :- share(S).
clue(C) :- clue_item(C).
breaker(B) :- breaker_item(B).

mystery(P,S,C) :- place(P), shared(S), clue(C).
solved(P) :- mystery(P,S,C), breaker(B).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("room", p))
    for s in SHARED_THINGS:
        lines.append(asp.fact("share", s))
    for c in CLUES:
        lines.append(asp.fact("clue_item", c))
    for b in BREAKERS:
        lines.append(asp.fact("breaker_item", b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery/3."))
    asp_set = set(asp.atoms(model, "mystery"))
    py_set = set((p, s, c) for p, s, c in valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world about sharing, rhyme, and a breaker mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--shared", choices=SHARED_THINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--breaker", choices=["trip", "stuck"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if args.shared:
        combos = [c for c in combos if c[1] == args.shared]
    if args.clue:
        combos = [c for c in combos if c[2] == args.clue]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, shared, clue = rng.choice(sorted(combos))
    breaker_mode = args.breaker or "trip"
    return StoryParams(place, "Mina", "Oren", "Ms. Vale", shared, clue, breaker_mode)


def generate(params: StoryParams) -> StorySample:
    reasonableness_check(params.place, params.shared, params.clue, params.breaker_mode)
    world = tell(PLACES[params.place], SHARED_THINGS[params.shared], CLUES[params.clue], RHYMES["ding"], params.child1, params.child2, params.teacher, params.breaker_mode)
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
        print(asp_program("#show mystery/3.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery/3."))
        for t in asp.atoms(model, "mystery"):
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for p, s, c in valid_combos():
            params = StoryParams(p, "Mina", "Oren", "Ms. Vale", s, c, "trip")
            samples.append(generate(params))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
