#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wander_snuff_rabbi_conflict_bedtime_story.py
===========================================================================

A standalone bedtime story world about a sleepy child who wanders after
bedtime, snuffs a light, and gets into a gentle conflict with a rabbi who helps
settle things down.

Seed words: wander, snuff, rabbi
Style: Bedtime Story
Feature: Conflict
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "rabbi": "rabbi"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    bedtime_image: str
    dark_corner: str
    quiet_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    safe: bool = True


@dataclass
class Snuff:
    id: str
    label: str
    phrase: str
    where: str
    lowers_light: bool = True


@dataclass
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    if not child or not parent:
        return out
    sig = ("conflict",)
    if child.memes["defiance"] >= THRESHOLD and child.memes["startled"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        child.memes["conflict"] += 1
        parent.memes["conflict"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict)]


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


def light_source(world: World) -> Entity:
    return world.get("lamp")


def predict_conflict(world: World) -> dict:
    sim = world.copy()
    sim.get("child").memes["defiance"] += 1
    sim.get("child").memes["startled"] += 1
    propagate(sim, narrate=False)
    return {
        "conflict": sim.get("child").memes["conflict"] >= THRESHOLD,
        "light_low": sim.get("lamp").meters["light"] < THRESHOLD,
    }


def do_wander(world: World, child: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    child.meters["steps"] += 1
    world.say(
        f"The little house was sleepy and still. In the soft glow of {setting.place}, "
        f"{child.id} began to wander out of {child.pronoun('possessive')} cozy bed."
    )
    world.say(
        f"Past the blanket hill and the pillow cave, {child.id} heard the {setting.quiet_sound} "
        f"of bedtime settling everywhere."
    )


def do_snuff(world: World, child: Entity, snuff: Snuff) -> None:
    lamp = light_source(world)
    child.memes["defiance"] += 1
    lamp.meters["light"] = max(0.0, lamp.meters["light"] - 1.0)
    lamp.meters["snuffed"] += 1
    world.say(
        f"{child.id} reached the little lamp and {snuff.label} it with a tiny puff. "
        f"At once, the warm light dimmed to a sleepy speck."
    )


def do_rabbi_warn(world: World, rabbi: Entity, child: Entity, setting: Setting) -> None:
    rabbi.memes["calm"] += 1
    world.say(
        f"From the doorway, {rabbi.id} looked up from {rabbi.pronoun('possessive')} book. "
        f'"{child.id}, please come back," {rabbi.pronoun()} said softly. '
        f'"Night is for resting, not for wandering around the dark corners."'
    )
    world.say(
        f"{rabbi.id} pointed to {setting.dark_corner} and the hush that waited there."
    )


def do_child_pushback(world: World, child: Entity) -> None:
    child.memes["startled"] += 1
    world.say(
        f"{child.id} frowned and hugged {child.pronoun('possessive')} blanket. "
        f'"But I was only looking," {child.pronoun()} whispered, sounding cross and sleepy at once.'
    )


def do_parent_firm(world: World, parent: Entity, child: Entity) -> None:
    parent.memes["gentle"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.id} came close, held {child.pronoun('object')} hand, and said, "
        f'"We can look for things in the morning. Right now, we need to keep the room calm."'
    )


def do_settle(world: World, rabbi: Entity, parent: Entity, child: Entity) -> None:
    child.memes["conflict"] = 0.0
    child.memes["rest"] += 1
    world.say(
        f"Then {rabbi.id} smiled like a lantern that never burned too bright. "
        f'"Let us all breathe slowly," {rabbi.pronoun()} said. '
        f'"A good bedtime can wait until the moon is high."'
    )
    world.say(
        f"{child.id} listened, and the tight feeling in {child.pronoun('possessive')} chest loosened."
    )
    world.say(
        f"{parent.id} tucked the blanket back under {child.pronoun('possessive')} chin, and "
        f"{rabbi.id} closed {rabbi.pronoun('possessive')} book with a quiet tap."
    )


def do_end(world: World, child: Entity, setting: Setting) -> None:
    lamp = light_source(world)
    lamp.meters["light"] = 1.0
    child.memes["peace"] += 1
    world.say(
        f"At last, the room was still again. The lamp shone low and kind, and "
        f"{setting.bedtime_image} seemed softer than before."
    )
    world.say(
        f"{child.id} lay back down and drifted off, while the dark corner stayed harmless and far away."
    )


def tell(setting: Setting, snuff: Snuff, light: Light, child_name: str, child_type: str,
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    rabbi = world.add(Entity(id="Rabbi", kind="character", type="rabbi", role="helper", label="the rabbi"))
    lamp = world.add(Entity(id="lamp", kind="thing", type="light", label=light.label))
    lamp.meters["light"] = 1.0

    world.facts.update(setting=setting, snuff=snuff, light=light, child=child, parent=parent, rabbi=rabbi)

    do_wander(world, child, setting)
    world.para()
    do_snuff(world, child, snuff)
    do_rabbi_warn(world, rabbi, child, setting)
    do_child_pushback(world, child)
    do_parent_firm(world, parent, child)
    world.para()
    do_settle(world, rabbi, parent, child)
    do_end(world, child, setting)

    world.facts.update(
        conflict=child.memes["conflict"] >= THRESHOLD,
        peaceful=child.memes["peace"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "nursery": Setting("nursery", "the nursery", "the moon on the wall", "the dark corner by the toy shelf", "the hush of blankets", {"bedtime"}),
    "hall": Setting("hall", "the hallway", "the little clock on the dresser", "the shadow by the stair", "the hush of slippers", {"bedtime"}),
    "study": Setting("study", "the study", "the lamp on the desk", "the tall bookshelf shadow", "the hush of pages turning", {"bedtime"}),
}

SNUFFS = {
    "puff": Snuff("puff", "snuffed", "snuffed", "with a tiny puff"),
    "soft_breath": Snuff("soft_breath", "blew out", "blew out", "with one soft breath"),
    "hand_wave": Snuff("hand_wave", "waved away", "waved away", "with a quick hand wave"),
}

LIGHTS = {
    "lamp": Light("lamp", "lamp", "a little lamp", "glowed warm and low"),
    "nightlight": Light("nightlight", "night-light", "a night-light", "shined like a tiny moon"),
    "candleless": Light("candleless", "reading light", "a reading light", "stayed gentle and bright"),
}

GIRL_NAMES = ["Mira", "Lina", "Noa", "Ada", "Tali"]
BOY_NAMES = ["Eli", "Noam", "Ilan", "Ari", "Jonah"]


@dataclass
class StoryParams:
    setting: str
    snuff: str
    light: str
    child_name: str
    child_type: str
    parent_type: str = "mother"
    seed: Optional[int] = None


KNOWLEDGE = {
    "wander": [("What does it mean to wander?",
                "To wander means to walk around without a set path, often slowly and curiously.")],
    "snuff": [("What does snuff mean?",
               "To snuff a light means to put it out or make it go dim.")],
    "rabbi": [("What is a rabbi?",
               "A rabbi is a Jewish teacher and community leader who helps people learn and think about kindness.")],
    "bedtime": [("Why is bedtime important?",
                 "Bedtime helps bodies and minds rest so they can feel better in the morning.")],
    "conflict": [("What is a conflict?",
                  "A conflict is a little disagreement or struggle between people who want different things.")],
    "lamp": [("What is a lamp?",
               "A lamp is a light that helps a room stay bright, often by a bed or on a table.")],
}
KNOWLEDGE_ORDER = ["wander", "snuff", "rabbi", "bedtime", "conflict", "lamp"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, n, l) for s in SETTINGS for n in SNUFFS for l in LIGHTS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    return [
        f'Write a gentle bedtime story for a 4-year-old that includes the words "wander", "snuff", and "rabbi".',
        f"Tell a bedtime story set in {setting.place} where a sleepy child wanders out of bed, snuffs the lamp, and a rabbi helps settle a small conflict.",
        f'Write a calm story with a conflict that ends in a safe, sleepy ending and uses the word "{f["snuff"].label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    rabbi: Entity = f["rabbi"]
    setting: Setting = f["setting"]
    snuff: Snuff = f["snuff"]
    qa = [
        QAItem("Who is the story about?", f"It is about {child.id}, {parent.label_word}, and the rabbi. The story follows a sleepy bedtime moment that turns into a small conflict."),
        QAItem("What did the child do first?", f"{child.id} began to wander out of bed. That made the room feel less settled and started the bedtime trouble."),
        QAItem("What happened when the child snuffed the light?", f"The lamp grew dim and the room got darker. That made the walk through the quiet room feel a little more tense."),
        QAItem("How did the conflict get calmer?", f"The rabbi spoke softly, the parent stayed firm, and {child.id} listened. Those calm words helped the child stop pushing back and settle down."),
        QAItem("How did the story end?", f"It ended with {child.id} back in bed and the lamp glowing low and kind. The room returned to a peaceful bedtime feeling."),
    ]
    if f.get("conflict"):
        qa.append(QAItem("Why was there conflict in the story?", f"There was conflict because {child.id} wanted to keep wandering, but the rabbi and {parent.label_word} wanted {child.id} to come back to bed. They wanted different things, so the room felt tense for a little while."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"wander", "snuff", "rabbi", "bedtime", "conflict", "lamp"}
    items: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            q, a = KNOWLEDGE[key][0]
            items.append(QAItem(q, a))
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
    StoryParams("nursery", "puff", "lamp", "Mira", "girl", "mother"),
    StoryParams("hall", "soft_breath", "nightlight", "Eli", "boy", "father"),
    StoryParams("study", "hand_wave", "candleless", "Tali", "girl", "mother"),
]


def explain_rejection() -> str:
    return "(No story: this bedtime world always needs a light to snuff and a calm conflict to resolve.)"


ASP_RULES = r"""
conflict(child,parent) :- defiance(child), startled(child).
valid(S,N,L) :- setting(S), snuff(N), light(L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for n in SNUFFS:
        lines.append(asp.fact("snuff", n))
    for l in LIGHTS:
        lines.append(asp.fact("light", l))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos disagree.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and story smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world with wander, snuff, rabbi, and a gentle conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snuff", choices=SNUFFS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.setting and args.snuff and args.light is None:
        pass
    setting = args.setting or rng.choice(list(SETTINGS))
    snuff = args.snuff or rng.choice(list(SNUFFS))
    light = args.light or rng.choice(list(LIGHTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, snuff, light, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SNUFFS[params.snuff], LIGHTS[params.light], params.child_name, params.child_type, params.parent_type)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, n, l in combos:
            print(f"  {s:10} {n:12} {l}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
