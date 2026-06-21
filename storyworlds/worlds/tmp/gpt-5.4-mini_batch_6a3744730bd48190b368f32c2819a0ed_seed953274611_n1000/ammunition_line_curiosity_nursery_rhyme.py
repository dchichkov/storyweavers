#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ammunition_line_curiosity_nursery_rhyme.py
===========================================================================

A small nursery-rhyme-style story world about a curious child, a drawn line,
and a dangerous box of ammunition that must stay untouched.

The world is intentionally tiny:
- a child discovers a forbidden box of ammunition,
- curiosity pulls them toward a line on the floor,
- a careful grown-up predicts the risk and redirects the child,
- the ending proves what changed by replacing danger with a safe counting game.

This file is standalone and uses only the standard library plus the shared
storyworld result/ASP helpers from Storyweavers.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CURIOUS_MIN = 1.0


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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Box:
    id: str
    label: str
    phrase: str
    forbidden_word: str
    makes_sharp: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Line:
    id: str
    label: str
    phrase: str
    safe_side: str
    risky_side: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


BOXES = {
    "ammunition": Box(
        id="ammunition",
        label="ammunition",
        phrase="a box of ammunition",
        forbidden_word="ammunition",
        makes_sharp=True,
        tags={"ammunition", "danger"},
    ),
}

LINES = {
    "chalkline": Line(
        id="chalkline",
        label="line",
        phrase="a bright chalk line on the floor",
        safe_side="one side of the line",
        risky_side="the other side of the line",
        tags={"line", "curiosity"},
    ),
}

CHARMS = {
    "peek": Charm(
        id="peek",
        label="look",
        phrase="a peek with the eyes, not the hands",
        use="look with the eyes",
        tags={"curiosity", "safe"},
    ),
    "counting_stones": Charm(
        id="counting_stones",
        label="counting stones",
        phrase="three smooth counting stones",
        use="count the stones",
        tags={"safe", "play"},
    ),
}

GROWNUPS = {"mother", "father"}
CHILD_NAMES = ["Mia", "Noah", "Lily", "Theo", "Eva", "Ben"]


def _r_warning(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    line = world.get("line")
    if child.memes["curiosity"] >= CURIOUS_MIN and child.meters["danger_seen"] >= THRESHOLD:
        sig = ("warning",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            out.append(f"{line.label_word.capitalize()} seemed to hum with mystery.")
    return out


def _r_keep_safe(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    grownup = world.get("grownup")
    if child.memes["curiosity"] >= CURIOUS_MIN and child.memes["trust"] >= THRESHOLD:
        sig = ("safe",)
        if sig not in world.fired:
            world.fired.add(sig)
            grownup.memes["care"] += 1
            out.append("A safe idea could answer the curious question.")
    return out


RULES = [_r_warning, _r_keep_safe]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
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
    return produced


def predict_risk(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["danger_seen"] += 1
    child.memes["curiosity"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("box").meters["opened"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"],
    }


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for box_id in BOXES:
        for line_id in LINES:
            for charm_id in CHARMS:
                combos.append((box_id, line_id, charm_id))
    return combos


@dataclass
class StoryParams:
    box: str
    line: str
    charm: str
    child: str
    child_gender: str
    grownup: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme story world about curiosity, a line, and ammunition."
    )
    ap.add_argument("--box", choices=BOXES)
    ap.add_argument("--line", choices=LINES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=sorted(GROWNUPS))
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
    if args.box and args.box not in BOXES:
        raise StoryError("Unknown box.")
    if args.line and args.line not in LINES:
        raise StoryError("Unknown line.")
    if args.charm and args.charm not in CHARMS:
        raise StoryError("Unknown charm.")
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Unknown gender.")

    filtered = [c for c in combos
                if (not args.box or c[0] == args.box)
                and (not args.line or c[1] == args.line)
                and (not args.charm or c[2] == args.charm)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    box, line, charm = rng.choice(filtered)
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.name or rng.choice(CHILD_NAMES)
    grownup = args.grownup or rng.choice(sorted(GROWNUPS))
    return StoryParams(box=box, line=line, charm=charm, child=child, child_gender=gender, grownup=grownup)


def tell(params: StoryParams) -> World:
    if params.box not in BOXES or params.line not in LINES or params.charm not in CHARMS:
        raise StoryError("Invalid params.")
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child, role="child"))
    grownup = world.add(Entity(id="grownup", kind="character", type=params.grownup, label=params.grownup.capitalize(), role="grownup"))
    box = world.add(Entity(id="box", kind="thing", type="box", label=BOXES[params.box].label))
    line = world.add(Entity(id="line", kind="thing", type="line", label=LINES[params.line].label))

    child.memes["curiosity"] = 2.0
    child.memes["trust"] = 1.0
    child.meters["danger_seen"] = 1.0

    world.say(
        f"Little {child.id} found {BOXES[params.box].phrase} near {LINES[params.line].phrase}."
    )
    world.say(
        f"{child.id} sang, \"What lies behind the line?\" and {child.pronoun()} leaned to peep."
    )

    world.para()
    pred = predict_risk(world)
    world.facts["predicted"] = pred
    world.say(
        f"{grownup.label_word.capitalize()} came soft and said, "
        f"\"{BOXES[params.box].forbidden_word} is not for play, child dear; "
        f"stay by {LINES[params.line].safe_side} and leave the box there.\""
    )
    child.memes["curiosity"] += 1
    child.memes["trust"] += 1

    world.para()
    world.say(
        f"{child.id} nodded, then chose {CHARMS[params.charm].phrase}."
    )
    world.say(
        f"They kept to {LINES[params.line].safe_side}, and the box stayed shut."
    )
    world.say(
        f"By and by, {child.id} counted stones and hummed a nursery tune while the line stayed just a line."
    )

    world.facts.update(
        child=child,
        grownup=grownup,
        box=box,
        line=line,
        charm=CHARMS[params.charm],
        outcome="safe",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a nursery-rhyme-style story about curiosity, a line, and a forbidden box of ammunition.',
        f'Tell a gentle story where {world.facts["child"].id} wonders about the line but leaves the ammunition alone.',
        'Write a short child-facing story that includes the words "ammunition" and "line" and ends safely.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    grownup = world.facts["grownup"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, a curious child, and {grownup.label_word.capitalize()}, who helps keep things safe."),
        ("What did the child want to know?",
         f"{child.id} wanted to know what lay beyond the line. That curiosity was strong, so the grown-up answered it with a safer idea."),
        ("Why did the grown-up stop the child?",
         f"{grownup.label_word.capitalize()} stopped the child because the box held ammunition, and that is not a toy. The line was a safe place to pause and think."),
    ]


def world_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is ammunition?",
         "Ammunition is something that belongs with a weapon. It is dangerous and should only be handled by trained adults and kept far from play."),
        ("What is a line?",
         "A line is a mark that can show where to stop, wait, or count. In stories for children, a line often helps keep play safe."),
        ("What does curiosity mean?",
         "Curiosity means wanting to learn more and see what is there. It can be good when it leads to safe questions and careful choices."),
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
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:7} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(B,L,C) :- box(B), line(L), charm(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for b in BOXES:
        lines.append(asp.fact("box", b))
    for l in LINES:
        lines.append(asp.fact("line", l))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    import traceback

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception:
        traceback.print_exc()
        return 1
    print("OK: verification smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_qa(world)],
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


CURATED = [
    StoryParams(box="ammunition", line="chalkline", charm="peek", child="Mia", child_gender="girl", grownup="mother"),
    StoryParams(box="ammunition", line="chalkline", charm="counting_stones", child="Theo", child_gender="boy", grownup="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
