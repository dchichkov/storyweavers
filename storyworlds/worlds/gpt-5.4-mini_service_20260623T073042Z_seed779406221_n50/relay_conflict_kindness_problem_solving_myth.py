#!/usr/bin/env python3
"""
storyworlds/worlds/relay_conflict_kindness_problem_solving_myth.py
=================================================================

A standalone myth-style story world about a relay race in a small village:
conflict rises when the baton is lost or blocked, kindness steadies the runners,
and problem solving restores the relay. The world simulates typed entities with
physical meters and emotional memes, then renders a complete child-facing story.

The seed image behind this world:
---
In an old village, a relay race is held between the river hill and the red gate.
Two young runners carry a bright baton blessed by the elder. One runner grows
angry when the path is blocked, but the other answers with kindness and a clever
plan: clear the track, share the pace, and pass the baton again. The village
cheers as the relay finishes, and the lesson is that strength without kindness
cannot finish the journey.

This world is intentionally small and constraint-checked:
- one relay event in one mythic setting
- one clear conflict turn
- one kindness turn
- one problem-solving resolution
- endings prove what changed in the world state

It supports the standard Storyweavers interface:
build_parser(), resolve_params(), generate(), emit(), main()
and includes a Python reasonableness gate plus an inline ASP twin.
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
    title: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "goddess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "god"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    path: str
    feat: str
    cheer: str


@dataclass
class Relay:
    name: str
    baton: str
    block: str
    fix: str
    ending: str


@dataclass
class StoryParams:
    setting: str
    relay: str
    runner1: str
    runner1_gender: str
    runner2: str
    runner2_gender: str
    elder: str
    seed: Optional[int] = None


SETTINGS = {
    "river_gate": Setting("the river hill", "the stone path", "the river wind", "the village"),
    "sun_ring": Setting("the sun ring", "the bright lane", "the warm dust", "the field"),
    "oak_bridge": Setting("the oak bridge", "the narrow bridge path", "the old roots", "the village"),
}

RELAYS = {
    "baton_run": Relay(
        name="relay",
        baton="a bright baton",
        block="a fallen branch",
        fix="move the branch and share the pace",
        ending="the baton crossed the last hand in time",
    ),
}

NAMES_GIRL = ["Mira", "Nia", "Lina", "Sera", "Ari"]
NAMES_BOY = ["Taro", "Jai", "Rin", "Oren", "Pax"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


def _init_world(world: World, p: StoryParams) -> tuple[Entity, Entity, Entity]:
    r1 = world.add(Entity(id=p.runner1, kind="character", type=p.runner1_gender, label=p.runner1, role="runner"))
    r2 = world.add(Entity(id=p.runner2, kind="character", type=p.runner2_gender, label=p.runner2, role="runner"))
    elder = world.add(Entity(id=p.elder, kind="character", type="elder", label=p.elder, role="elder"))
    for e in (r1, r2, elder):
        e.meters.setdefault("speed", 0.0)
        e.meters.setdefault("blocked", 0.0)
        e.meters.setdefault("passed", 0.0)
        e.meters.setdefault("finish", 0.0)
        e.meters.setdefault("helped", 0.0)
        e.memes.setdefault("conflict", 0.0)
        e.memes.setdefault("kindness", 0.0)
        e.memes.setdefault("resolve", 0.0)
        e.memes.setdefault("joy", 0.0)
    return r1, r2, elder


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if world.entities["runner1"].meters["blocked"] >= THRESHOLD and "block_conflict" not in world.fired:
        world.fired.add("block_conflict")
        world.entities["runner1"].memes["conflict"] += 1
        world.entities["runner2"].memes["conflict"] += 1
        out.append("The blocked path stirred anger between the runners.")
    if world.entities["runner2"].memes["kindness"] >= THRESHOLD and "kind_help" not in world.fired:
        world.fired.add("kind_help")
        world.entities["runner1"].memes["resolve"] += 1
        world.entities["runner2"].memes["resolve"] += 1
        out.append("Kindness steadied both runners.")
    if world.entities["runner1"].memes["resolve"] >= THRESHOLD and world.entities["runner2"].memes["resolve"] >= THRESHOLD:
        if "finish" not in world.fired:
            world.fired.add("finish")
            world.entities["runner1"].meters["finish"] = 1.0
            world.entities["runner2"].meters["finish"] = 1.0
            world.entities["runner1"].memes["joy"] += 1
            world.entities["runner2"].memes["joy"] += 1
            out.append("The relay at last found its finish.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_combos() -> list[tuple[str, str]]:
    return [(s, r) for s in SETTINGS for r in RELAYS]


def reason_ok(setting: str, relay: str) -> bool:
    return setting in SETTINGS and relay in RELAYS


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for r in RELAYS:
        lines.append(asp.fact("relay", r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,R) :- setting(S), relay(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic relay story world with conflict, kindness, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relay", choices=RELAYS)
    ap.add_argument("--runner1")
    ap.add_argument("--runner1-gender", choices=["girl", "boy"])
    ap.add_argument("--runner2")
    ap.add_argument("--runner2-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.relay is None or c[1] == args.relay)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, relay = rng.choice(combos)
    r1_gender = args.runner1_gender or rng.choice(["girl", "boy"])
    r2_gender = args.runner2_gender or ("boy" if r1_gender == "girl" else "girl")
    r1 = args.runner1 or rng.choice(NAMES_GIRL if r1_gender == "girl" else NAMES_BOY)
    r2_pool = [n for n in (NAMES_GIRL if r2_gender == "girl" else NAMES_BOY) if n != r1]
    r2 = args.runner2 or rng.choice(r2_pool)
    elder = args.elder or rng.choice(["the elder", "the wise elder", "old Maia"])
    return StoryParams(setting=setting, relay=relay, runner1=r1, runner1_gender=r1_gender,
                       runner2=r2, runner2_gender=r2_gender, elder=elder)


def tell(setting: Setting, relay: Relay, p: StoryParams) -> World:
    world = World(setting)
    r1, r2, elder = _init_world(world, p)
    world.say(
        f"At {setting.place}, {r1.name} and {r2.name} entered the relay like two small heroes. "
        f"{elder.name} watched from the edge while the village listened to the wind."
    )
    world.say(
        f"Their task was simple and old: carry {relay.baton} along {setting.path} and bring it home."
    )
    world.para()
    world.say(
        f"But {setting.feat} shook the path, and a {relay.block} lay ahead."
    )
    r1.meters["blocked"] += 1
    r1.memes["conflict"] += 1
    r2.memes["conflict"] += 1
    world.say(
        f"{r1.name} grew angry and wanted to shove ahead alone, while {r2.name} feared the relay would fail."
    )
    world.para()
    r2.memes["kindness"] += 1
    world.say(
        f"Then {r2.name} spoke with kindness: \"We can solve this together.\""
    )
    world.say(
        f"{r2.name} helped move the branch, and the two runners shared the pace so neither one stumbled."
    )
    r1.meters["blocked"] = 0.0
    r1.meters["passed"] = 1.0
    r2.meters["passed"] = 1.0
    r1.memes["resolve"] += 1
    r2.memes["resolve"] += 1
    propagate(world, narrate=False)
    world.say(
        f"With the path clear, {r1.name} passed {relay.baton} to {r2.name}, and {r2.name} carried it to the finish."
    )
    world.say(
        f"{relay.ending.capitalize()}, and the village cheered because kindness had turned conflict into a way forward."
    )
    world.facts.update(
        setting=setting, relay=relay, runner1=r1, runner2=r2, elder=elder,
        blocked=True, resolved=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about {f["runner1"].name} and {f["runner2"].name} racing a relay at {f["setting"].place}, where a problem blocks the path and kindness helps them solve it.',
        f"Tell a gentle mythic story where two runners face conflict on a relay path, then use kindness and problem solving to finish together.",
        f'Write a child-friendly myth about a relay, a blocked road, and a wise ending where the runners carry the baton home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    r1 = f["runner1"]
    r2 = f["runner2"]
    setting = f["setting"]
    relay = f["relay"]
    return [
        QAItem(
            question=f"Who was the relay story about?",
            answer=f"It was about {r1.name} and {r2.name}, two runners who tried to carry {relay.baton} home.",
        ),
        QAItem(
            question=f"What problem made the runners upset?",
            answer=f"A {relay.block} blocked {setting.path}, so the race could not continue until they solved the problem.",
        ),
        QAItem(
            question=f"How did kindness help in the story?",
            answer=f"{r2.name} spoke kindly and helped move the branch, which steadied both runners and made it easier to keep going.",
        ),
        QAItem(
            question=f"How was the relay finished?",
            answer=f"The runners cleared the path, passed {relay.baton} again, and reached the finish together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a relay?", answer="A relay is a race where runners pass a baton from one runner to another."),
        QAItem(question="Why is kindness useful when people argue?", answer="Kindness can calm angry feelings and help people work together."),
        QAItem(question="What is problem solving?", answer="Problem solving means noticing what is wrong and finding a good way to fix it."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if not reason_ok(params.setting, params.relay):
        raise StoryError("Invalid params for this story world.")
    world = tell(SETTINGS[params.setting], RELAYS[params.relay], params)
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for s, r in asp_valid_combos():
            print(f"  {s} {r}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting=s, relay=r, runner1="Mira", runner1_gender="girl",
                                         runner2="Taro", runner2_gender="boy", elder="the elder"))
                   for s, r in valid_combos()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
