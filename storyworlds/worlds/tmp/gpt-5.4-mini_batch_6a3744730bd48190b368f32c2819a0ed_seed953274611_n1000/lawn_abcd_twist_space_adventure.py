#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lawn_abcd_twist_space_adventure.py
===================================================================

A standalone storyworld for a small space-adventure tale on a backyard lawn:
two kids build a pretend launch site, a mysterious "abcd" signal leads them
toward a hidden twist, and the ending proves what changed in the world.

The story stays state-driven: meters track physical conditions like dust, signal,
and launch readiness; memes track feelings like wonder, worry, and pride.
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
WONDER_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    scene: str
    ground: str
    sky: str
    open_sky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    phrase: str
    clue: str
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SpaceGear:
    id: str
    label: str
    phrase: str
    use_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    signal: str
    gear: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
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
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    rover = world.entities.get("rover")
    if rover and rover.meters["rolling"] >= THRESHOLD and ("dust", "rover") not in world.fired:
        world.fired.add(("dust", "rover"))
        world.get("lawn").meters["sparkle"] += 1
        out.append("Tiny silver dust puffed up from the lawn.")
    return out


def _r_wonder(world: World) -> list[str]:
    out: list[str] = []
    sig = world.entities.get("signal")
    if sig and sig.meters["glow"] >= THRESHOLD and ("wonder", "kids") not in world.fired:
        world.fired.add(("wonder", "kids"))
        for kid in world.entities.values():
            if kid.role in {"child1", "child2"}:
                kid.memes["wonder"] += 1
        out.append("The strange light made the children stare with round eyes.")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    sig = world.entities.get("signal")
    if sig and sig.meters["decoded"] >= THRESHOLD and ("twist", "signal") not in world.fired:
        world.fired.add(("twist", "signal"))
        world.get("pod").meters["open"] += 1
        out.append("__twist__")
    return out


CAUSAL_RULES = [Rule("dust", _r_dust), Rule("wonder", _r_wonder), Rule("twist", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "lawn": Place(id="lawn", label="the lawn", scene="a bright backyard launch pad", ground="grass", sky="blue sky", open_sky=True, tags={"lawn", "space"}),
}

SIGNALS = {
    "abcd": Signal(id="abcd", label="abcd", phrase="the code abcd", clue="four glowing letters", twist="a hidden pod under the lawn", tags={"abcd", "code", "twist"}),
}

GEAR = {
    "binoculars": SpaceGear(id="binoculars", label="binoculars", phrase="a pair of binoculars", use_line="used the binoculars to scan the grass"),
    "radio": SpaceGear(id="radio", label="radio", phrase="a little radio", use_line="clicked the radio and heard a beep-beep reply"),
    "ramp": SpaceGear(id="ramp", label="ramp", phrase="a cardboard ramp", use_line="set the ramp by the toy rover"),
}

GIRL_NAMES = ["Luna", "Mia", "Zoe", "Ava", "Nia"]
BOY_NAMES = ["Max", "Leo", "Sam", "Noah", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("lawn", "abcd", gear) for gear in GEAR]


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "lawn"), asp.fact("signal", "abcd")]
    for gid in GEAR:
        lines.append(asp.fact("gear", gid))
    lines.append(asp.fact("twist_signal", "abcd"))
    lines.append(asp.fact("valid", "lawn", "abcd", gid) if False else "")
    return "\n".join(l for l in lines if l)


ASP_RULES = r"""
valid(P,S,G) :- place(P), signal(S), gear(G), twist_signal(S), P = lawn.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure lawn storyworld with a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--name2")
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
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.signal and args.signal not in SIGNALS:
        raise StoryError("Unknown signal.")
    if args.gear and args.gear not in GEAR:
        raise StoryError("Unknown gear.")
    place = args.place or "lawn"
    signal = args.signal or "abcd"
    gear = args.gear or rng.choice(list(GEAR))
    c1 = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    c2 = args.name2 or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != c1])
    g1 = "girl" if c1 in GIRL_NAMES else "boy"
    g2 = "girl" if c2 in GIRL_NAMES else "boy"
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, signal=signal, gear=gear, child1=c1, child1_gender=g1, child2=c2, child2_gender=g2, parent=parent)


def _starter_line(world: World, p: StoryParams) -> None:
    world.say(
        f"On a bright afternoon, {p.child1} and {p.child2} turned the lawn into a space base. "
        f"They made a launch pad in the grass and dreamed of stars."
    )
    world.say(f"Then {p.child1} found {SIGNALS[p.signal].clue} blinking near the garden gate.")


def _decode(world: World, p: StoryParams) -> None:
    sig = world.get("signal")
    sig.meters["glow"] += 1
    sig.meters["decoded"] += 1
    world.say(
        f'"Look!" {p.child2} said. "It spells {SIGNALS[p.signal].label}." '
        f"{p.child1} leaned closer, and the letters shimmered like little stars."
    )


def _twist_reveal(world: World, p: StoryParams) -> None:
    pod = world.get("pod")
    pod.meters["open"] += 1
    world.say(
        f"With a soft click, the lawn split into a tiny round hatch. "
        f"Under the grass sat a silver pod that had been waiting all along."
    )
    world.say(
        f'Inside was a map for a moon garden, and a note that said, '
        f'"The lawn was the landing pad."'
    )


def _launch_finish(world: World, p: StoryParams, gear: SpaceGear) -> None:
    for kid in ("child1", "child2"):
        world.get(kid).memes["pride"] += 1
    world.say(
        f"{p.parent.capitalize()} smiled and handed them {gear.phrase}. "
        f"{gear.use_line.capitalize()}, and the signal turned out to be a guide instead of a warning."
    )
    world.say(
        f"By sunset, the children were sending their toy rover across the lawn, "
        f"as if it were rolling on the moon."
    )


def tell(params: StoryParams) -> World:
    w = World()
    p = params
    w.add(Entity(id="lawn", kind="place", type="place", label="the lawn", tags={"lawn", "space"}))
    w.add(Entity(id="signal", kind="thing", type="signal", label=SIGNALS[p.signal].label, tags=SIGNALS[p.signal].tags))
    w.add(Entity(id="pod", kind="thing", type="pod", label="silver pod"))
    w.add(Entity(id="rover", kind="thing", type="rover", label="toy rover"))
    c1 = w.add(Entity(id="child1", kind="character", type=p.child1_gender, role="child1", label=p.child1))
    c2 = w.add(Entity(id="child2", kind="character", type=p.child2_gender, role="child2", label=p.child2))
    parent = w.add(Entity(id="parent", kind="character", type=p.parent, label=p.parent))
    gear = w.add(Entity(id="gear", kind="thing", type="gear", label=GEAR[p.gear].label))

    c1.memes["hope"] += 1
    c2.memes["hope"] += 1

    _starter_line(w, p)
    w.para()
    _decode(w, p)
    w.get("signal").meters["glow"] += 1
    w.get("rover").meters["rolling"] += 1
    propagate(w)
    w.para()
    _twist_reveal(w, p)
    _launch_finish(w, p, GEAR[p.gear])

    w.facts.update(params=p, gear=GEAR[p.gear], signal=SIGNALS[p.signal], place=PLACES[p.place], outcome="twist")
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a space-adventure story for a 3-to-5-year-old that includes the words "lawn" and "abcd".',
        f"Tell a story where {p.child1} and {p.child2} explore the lawn like a launch pad and discover what abcd means.",
        f"Write a short space adventure with a twist ending in which a backyard lawn hides a surprising message.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {p.child1} and {p.child2}, two kids who turned the lawn into a space base. They found the code abcd and followed it to a surprise."),
        QAItem(question="What was the twist?", answer="The twist was that the lawn was not just grass. It was also a hidden landing pad, and a silver pod was tucked under it the whole time."),
        QAItem(question="What did the children do at the end?", answer="They used the gear, solved the clue, and kept playing with their toy rover. The ending shows the lawn had become part of their space adventure."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a lawn?", answer="A lawn is a flat area of grass near a house or building. It can be a place to play or pretend."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise change that makes you rethink what was happening before. It should still make sense when you look back at the clues."),
        QAItem(question="What is a signal?", answer="A signal is a sign or message that tells you something. In a story, it can guide characters toward what to do next."),
    ]


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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lawn", signal="abcd", gear="binoculars", child1="Luna", child1_gender="girl", child2="Max", child2_gender="boy", parent="mother"),
    StoryParams(place="lawn", signal="abcd", gear="radio", child1="Mia", child1_gender="girl", child2="Leo", child2_gender="boy", parent="father"),
]


def valid_params(p: StoryParams) -> bool:
    return p.place == "lawn" and p.signal == "abcd" and p.gear in GEAR


def asp_verify() -> int:
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"FAILED: generate smoke test crashed: {e}")
        return 1
    py = {("lawn", "abcd", g) for g in GEAR}
    cl = set(asp_valid_combos())
    if cl != py:
        print("MISMATCH in ASP/Python combos")
        print("python:", sorted(py))
        print("clingo:", sorted(cl))
        return 1
    print("OK: smoke test passed and ASP/Python parity matched.")
    return 0


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_params(params):
        raise StoryError("Invalid story parameters for this world.")
    return build_story(params)


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
        print("compatible stories:")
        for row in asp_valid_combos():
            print(row)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
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

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
