#!/usr/bin/env python3
"""
storyworlds/worlds/machinery_circular_popsicle_kindness_bedtime_story.py
========================================================================

A bedtime-story world about a small, humming machine, a round popsicle mold,
and a gentle act of kindness that turns a sticky problem into a sweet ending.

Seed-inspired premise:
- machinery: a little kitchen machine with a wheel and a quiet motor
- circular: a round mold/tray that makes ring-shaped popsicles
- popsicle: a frozen treat the child wants to share
- kindness: the child chooses to help, share, and soothe instead of snatching

The world model tracks both physical meters and emotional memes:
- machine state: running, jammed, humming, cooling
- physical mess: sticky, cold, spilled
- emotional state: patience, worry, kindness, relief, warmth

The story is intentionally small and classical:
beginning -> a problem with the machine and popsicle ring,
middle -> a gentle conflict over waiting,
ending -> kindness repairs the moment and leaves a calm bedtime image.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    parent_type: str
    place: str
    machine: str
    treat: str
    seed: Optional[int] = None


CHILD_NAMES = ["Mia", "Noah", "Lina", "Theo", "Ava", "Finn", "Nora", "Eli"]
CHILD_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
PLACES = ["the tiny kitchen", "the warm pantry", "the sleepy breakfast nook"]

MACHINES = {
    "spinner": {
        "label": "little spinning machine",
        "phrase": "a little spinning machine with a soft round dial",
        "noise": "hummed softly",
    }
}

TREAT = {
    "label": "popsicle",
    "phrase": "a tray of round popsicles",
    "shape": "circular",
    "detail": "a ring-shaped popsicle",
}


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


def _m(e: Entity, key: str, delta: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _v(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mm(e: Entity, key: str, delta: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def _mv(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _make_world(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        traits=["little", "gentle", "sleepy"],
    ))
    parent = w.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="parent",
    ))
    machine_cfg = MACHINES[params.machine]
    machine = w.add(Entity(
        id="machine",
        type="machine",
        label=machine_cfg["label"],
        phrase=machine_cfg["phrase"],
        caretaker=parent.id,
    ))
    treat = w.add(Entity(
        id="treat",
        type="popsicle",
        label=TREAT["label"],
        phrase=TREAT["phrase"],
        caretaker=parent.id,
    ))
    ring = w.add(Entity(
        id="ring",
        type="tray",
        label="round mold",
        phrase="a circular mold tray",
        owner=machine.id,
    ))
    w.facts.update(
        child=child,
        parent=parent,
        machine=machine,
        treat=treat,
        ring=ring,
        place=params.place,
        params=params,
    )
    return w


def _narrate_setup(w: World) -> None:
    c: Entity = w.facts["child"]
    p: Entity = w.facts["parent"]
    m: Entity = w.facts["machine"]
    t: Entity = w.facts["treat"]
    place: str = w.facts["place"]

    w.say(f"{c.id} was a little {c.type} who lived near {place}.")
    w.say(f"{c.pronoun().capitalize()} liked the quiet night best, when the house felt soft and safe.")
    w.say(f"On the counter sat {m.phrase}, and beside it was {t.phrase}.")
    _mm(c, "kindness", 1)
    _mm(c, "joy", 1)
    w.say(f"{c.id} loved its {TREAT['shape']} shape because {t.label}s looked like little moons for sharing.")
    w.say(f"{p.label.capitalize()} said the machine could make just one more batch before bedtime.")


def _predict_jam(w: World) -> bool:
    # Simple reasonableness gate: if the round mold is sticky and the machine is rushed, it jams.
    return _v(w.facts["machine"], "sticky") >= THRESHOLD or _mv(w.facts["parent"], "rushed") >= THRESHOLD


def _run_machine(w: World) -> None:
    m: Entity = w.facts["machine"]
    t: Entity = w.facts["treat"]
    c: Entity = w.facts["child"]
    p: Entity = w.facts["parent"]

    _m(m, "running", 1)
    _mm(c, "anticipation", 1)
    if _predict_jam(w):
        _m(m, "jammed", 1)
        _mm(c, "worry", 1)
        w.say(f"The little machine started to spin, but its round tray caught on a sticky bit and got jammed.")
        w.say(f"{c.id} frowned. The popsicles would not come out neat and circular now.")
    else:
        _m(m, "cooling", 1)
        w.say(f"The little machine {MACHINES[w.facts['params'].machine]['noise']} and the tray turned in a neat circle.")
        w.say(f"Inside, the popsicles settled into perfect round shapes, cool and sleepy.")
    _mm(p, "care", 1)


def _conflict(w: World) -> None:
    c: Entity = w.facts["child"]
    p: Entity = w.facts["parent"]
    m: Entity = w.facts["machine"]

    if _v(m, "jammed") < THRESHOLD:
        return
    _mm(c, "disappointment", 1)
    _mm(p, "patience", 1)
    w.say(f"{c.id} wanted to tug the tray right away, but {p.label} lifted a gentle hand.")
    w.say(f"\"Wait,\" {p.pronoun()} said. \"If we rush it, the popsicle ring will break.\"")
    _mm(c, "frustration", 1)
    _m(m, "sticky", 1)


def _kindness_turn(w: World) -> None:
    c: Entity = w.facts["child"]
    p: Entity = w.facts["parent"]
    m: Entity = w.facts["machine"]

    if _v(m, "jammed") < THRESHOLD:
        return
    _mm(c, "kindness", 1)
    _mm(c, "patience", 1)
    _mm(p, "relief", 1)
    _m(m, "sticky", -1)
    _m(m, "jammed", -1)
    _m(m, "running", 1)
    _m(m, "cooling", 1)
    w.say(f"{c.id} took a breath and got a damp cloth instead.")
    w.say(f"With small careful circles, {c.pronoun()} wiped the sticky edge clean while {p.pronoun()} held the tray steady.")
    w.say(f"The little machine sighed, turned again, and this time the circular mold moved smoothly.")


def _resolution(w: World) -> None:
    c: Entity = w.facts["child"]
    p: Entity = w.facts["parent"]
    t: Entity = w.facts["treat"]
    m: Entity = w.facts["machine"]

    if _v(m, "cooling") < THRESHOLD:
        return
    _mm(c, "warmth", 1)
    _mm(p, "love", 1)
    _mm(c, "pride", 1)
    w.say(f"At last, the popsicles came free in neat round shapes, cold and shiny like tiny moons.")
    w.say(f"{c.id} shared the first one with {p.label}, and the kitchen felt even warmer than before.")
    w.say(f"By bedtime, the machine was quiet, the tray was clean, and a happy {t.label} waited in the freezer for tomorrow.")


def tell(params: StoryParams) -> World:
    w = _make_world(params)
    _narrate_setup(w)
    w.para()
    _run_machine(w)
    _conflict(w)
    w.para()
    _kindness_turn(w)
    _resolution(w)
    w.facts["resolved"] = True
    return w


def story_qa(world: World) -> list[QAItem]:
    c: Entity = world.facts["child"]
    p: Entity = world.facts["parent"]
    m: Entity = world.facts["machine"]
    t: Entity = world.facts["treat"]
    place: str = world.facts["place"]
    return [
        QAItem(
            question=f"Who helped the little {c.type} at {place} when the machine got sticky?",
            answer=f"{p.label.capitalize()} helped by staying calm, and {c.id} helped by being gentle and patient."
        ),
        QAItem(
            question=f"What went wrong with the machine and the circular treat?",
            answer="The round tray got sticky and jammed, so the popsicles could not come out smoothly at first."
        ),
        QAItem(
            question=f"What did {c.id} do that showed kindness?",
            answer=f"{c.id} got a damp cloth, cleaned the sticky edge, and let the machine turn again instead of tugging."
        ),
        QAItem(
            question=f"What did the popsicles look like at the end?",
            answer=f"They were neat and round, like tiny moons, and they stayed cold and ready for tomorrow."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a popsicle?",
            answer="A popsicle is a frozen sweet treat on a stick or in a mold that people eat when it is cold."
        ),
        QAItem(
            question="What does a machine do?",
            answer="A machine is something made by people that helps do a job, like spinning, mixing, or cooling."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone else."
        ),
        QAItem(
            question="What does circular mean?",
            answer="Circular means round, like a wheel, a ring, or a moon."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    c: Entity = world.facts["child"]
    p: Entity = world.facts["parent"]
    return [
        f"Write a bedtime story about {c.id} and a little machine that makes circular popsicles.",
        f"Tell a gentle story where kindness helps {c.id} and {p.label} fix a sticky kitchen problem.",
        "Make the ending calm, round, and sweet, with a child sharing a popsicle before sleep.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: machinery, circular popsicle, kindness.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--machine", choices=list(MACHINES))
    ap.add_argument("--treat", choices=["popsicle"])
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
    name = args.name or rng.choice(CHILD_NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    place = args.place or rng.choice(PLACES)
    machine = args.machine or "spinner"
    treat = args.treat or "popsicle"
    return StoryParams(name, child_type, parent, place, machine, treat, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


ASP_RULES = r"""
child(C) :- child_name(C).
parent(P) :- parent_type(P).
machine(M) :- machine_kind(M).
treat(T) :- treat_kind(T).

round(T) :- treat_shape(T,circular).
kind_act(C) :- kindness(C).
jammed :- sticky(machine), running(machine), round(treat), circular_mold.
resolved :- jammed, kind_act(child).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in CHILD_NAMES:
        lines.append(asp.fact("child_name", n))
    for t in CHILD_TYPES:
        lines.append(asp.fact("child_type", t))
    for p in PARENT_TYPES:
        lines.append(asp.fact("parent_type", p))
    for pl in PLACES:
        lines.append(asp.fact("place", pl))
    for mk in MACHINES:
        lines.append(asp.fact("machine_kind", mk))
    lines.append(asp.fact("treat_kind", "popsicle"))
    lines.append(asp.fact("treat_shape", "popsicle", "circular"))
    lines.append(asp.fact("circular_mold"))
    lines.append(asp.fact("kindness", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0.\n#show jammed/0."))
    atoms = {(s.name, len(s.arguments)) for s in model}
    ok = ("resolved", 0) in atoms
    if ok:
        print("OK: ASP twin recognizes the kindness resolution.")
        return 0
    print("MISMATCH: ASP twin did not derive resolved.")
    return 1


CURATED = [
    StoryParams("Mia", "girl", "mother", "the tiny kitchen", "spinner", "popsicle"),
    StoryParams("Noah", "boy", "father", "the warm pantry", "spinner", "popsicle"),
    StoryParams("Nora", "girl", "mother", "the sleepy breakfast nook", "spinner", "popsicle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < args.n * 50 + 50:
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
