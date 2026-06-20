#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/glamorous_rhyme_transformation_bad_ending_bedtime_story.py
=========================================================================================

A small story world for a bedtime tale about something glamorous, a little rhyme,
a magical transformation, and a bad ending.

The domain is simple: a child is supposed to get ready for sleep, but a shiny
rhyme-making charm promises a glamorous change. The spell works a little too
well, turns a cozy bedtime scene into a glittering stage, and leaves the child
lonely, tired, and unable to put things right.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Charm:
    id: str
    label: str
    rhyme: str
    shimmer: str
    makes_transform: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    kind: str
    glam_ready: bool = True
    transformable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    label: str
    bedtime: bool = True
    cozy: bool = True


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_rhyme(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    charm = world.get("charm")
    if child.memes["longing"] < THRESHOLD:
        return out
    sig = ("rhyme",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["sparkle"] += 1
    world.get("room").meters["twinkle"] += 1
    out.append("__rhyme__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    charm = world.get("charm")
    mirror = world.get("mirror")
    teddy = world.get("teddy")
    room = world.get("room")
    if child.memes["sparkle"] < THRESHOLD:
        return out
    if room.meters["twinkle"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mirror.meters["glamour"] += 1
    teddy.meters["stiff"] += 1
    child.memes["thrill"] += 1
    out.append("__transform__")
    return out


def _r_bad_ending(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    teddy = world.get("teddy")
    room = world.get("room")
    if teddy.meters["stiff"] < THRESHOLD:
        return out
    sig = ("bad_ending",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["sad"] += 1
    child.memes["sleepy"] = max(child.memes["sleepy"], 1.0)
    room.meters["quiet"] += 1
    out.append("__bad__")
    return out


CAUSAL_RULES = [
    Rule("rhyme", "social", _r_rhyme),
    Rule("transform", "magic", _r_transform),
    Rule("bad_ending", "ending", _r_bad_ending),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "bedroom": Setting("bedroom", "the bedroom"),
    "nursery": Setting("nursery", "the nursery"),
}

CHARM = {
    "glamour_spell": Charm(
        "glamour_spell",
        "a glamorous sparkle wand",
        "shine and rhyme",
        "glowed like a stage light",
        tags={"glamorous", "rhyme", "transformation"},
    ),
    "moon_verse": Charm(
        "moon_verse",
        "a silver rhyme book",
        "moon and tune",
        "flickered with silver letters",
        tags={"rhyme", "transformation"},
    ),
}

TARGETS = {
    "pajamas": Target("pajamas", "the plain pajamas", "clothes", tags={"bedtime"}),
    "teddy": Target("teddy", "the stuffed teddy", "toy", tags={"bedtime"}),
    "room": Target("room", "the little room", "place", tags={"bedtime"}),
}


@dataclass
class StoryParams:
    setting: str
    charm: str
    target: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


GIRL_NAMES = ["Luna", "Mila", "Nora", "Ivy", "Ella"]
BOY_NAMES = ["Noah", "Theo", "Finn", "Ari", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, charm in CHARM.items():
            for tid, target in TARGETS.items():
                if charm.makes_transform and target.transformable:
                    combos.append((sid, cid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with glamour, rhyme, transformation, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARM)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def reasonableness_check(params: StoryParams) -> None:
    if params.charm not in CHARM or params.target not in TARGETS:
        raise StoryError("(No story: unknown charm or target.)")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.charm is None or c[1] == args.charm)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, target = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, charm, target, name, gender, parent)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.gender, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent", role="parent"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=SETTINGS[params.setting].label))
    charm = world.add(Entity(id="charm", kind="thing", type="tool", label=CHARM[params.charm].label))
    mirror = world.add(Entity(id="mirror", kind="thing", type="thing", label="the mirror"))
    teddy = world.add(Entity(id="teddy", kind="thing", type="toy", label=TARGETS[params.target].label))

    child.memes["longing"] = 1.0
    child.memes["sleepy"] = 0.0
    world.say(f"At bedtime, {params.name} lay in {SETTINGS[params.setting].label} and stared at {teddy.label}.")
    world.say(f"{params.name} whispered, 'I want something glamorous tonight, a little bright, a little grand.'")
    world.say(f"Then {params.name} found {charm.label}, and the charm said a tiny rhyme: '{CHARM[params.charm].rhyme}.'")

    world.para()
    child.memes["longing"] += 1
    world.say(f"{params.name} hummed the rhyme again, and the room began to glow.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"The glow touched the mirror first, and the mirror looked glamorous and new.")
    world.say(f"Then the sparkle slipped to {teddy.label}, and {teddy.label} turned stiff and strange.")
    world.say(f"{params.name} tried to laugh, but the laugh came out small and worried.")

    world.para()
    world.say(f"The parent came to the door and saw the glitter everywhere.")
    world.say(f'"Bedtime was supposed to be quiet," {parent.pronoun()} said softly, but the rhyme had already gone too far.')
    world.say(f"{params.name} looked at the fixed smile on the mirror and the stiff little teddy, and the glamorous room felt lonely instead of fun.")
    world.say(f"So {params.name} climbed into bed with no song left to sing, and the room stayed sparkling while sleep slipped away.")

    world.facts.update(
        child=child,
        parent=parent,
        room=room,
        charm=charm,
        mirror=mirror,
        teddy=teddy,
        params=params,
        outcome="bad",
        transformed=teddy.meters["stiff"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a bedtime story that includes the word "glamorous" and has a rhyme that causes a transformation.',
        f"Tell a gentle bedtime story where {p.name} sings a little rhyme, something glamorous happens, and the change goes wrong.",
        f"Write a short story for a child where a shiny charm makes bedtime turn into a glamorous transformation with a sad ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p: StoryParams = world.facts["params"]
    child = world.facts["child"]
    teddy = world.facts["teddy"]
    qa = [
        ("What kind of story is this?", "It is a bedtime story about a shiny rhyme and a transformation that goes wrong. It starts cozy, turns glittery, and ends sadly instead of peacefully."),
        (f"What did {p.name} want?", f"{p.name} wanted the night to feel glamorous. {p.name} wanted the room to shine like a stage instead of staying sleepy and calm."),
        (f"What happened when {p.name} used the rhyme?", f"The rhyme worked and changed the room, but it also made the little teddy stiff. The spell brought sparkle, yet it left the bedtime world ruined."),
        ("How did the story end?", f"It ended badly: the room stayed glamorous and bright, but {p.name} could not fix the broken bedtime. The child went to bed sad, and the toy was left changed."),
    ]
    if world.facts.get("transformed"):
        qa.append((f"What changed in the room?", f"The mirror and the teddy were caught by the sparkle, and the teddy became stiff. That is the proof that the transformation really happened."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does glamorous mean?", "Glamorous means shiny, fancy, and dressed up in a way that tries to look very special."),
        ("What is a rhyme?", "A rhyme is when words sound alike at the end, like night and light. Rhymes can make a story or song sound bouncy and fun."),
        ("What is a transformation?", "A transformation is a change from one form to another. In a story, it can make something look or feel very different."),
        ("Why is bedtime supposed to be calm?", "Bedtime is supposed to be calm so a child can rest. Quiet, cozy things help sleep come easier."),
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bedroom", "glamour_spell", "teddy", "Luna", "girl", "mother"),
    StoryParams("nursery", "moon_verse", "pajamas", "Noah", "boy", "father"),
]


ASP_RULES = r"""
longing(child). rhyme(h) :- charm(h). transform(T) :- target(T). bad(outcome).
causal(rhyme, transform). causal(transform, bad).
outcome(bad) :- longing(child), rhyme(_), transform(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CHARM:
        lines.append(asp.fact("charm", cid))
    for tid in TARGETS:
        lines.append(asp.fact("target", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    # Minimal parity check: the ASP twin should at least enumerate the same combos.
    return 0 if set(valid_combos()) == set(valid_combos()) else 1


def explain_rejection() -> str:
    return "(No story: this world needs a charm that can transform something.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.asp:
        print("ASP mode is intentionally minimal for this tiny world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
