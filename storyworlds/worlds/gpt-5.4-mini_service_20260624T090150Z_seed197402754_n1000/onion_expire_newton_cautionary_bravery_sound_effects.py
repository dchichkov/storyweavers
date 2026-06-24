#!/usr/bin/env python3
"""
Standalone storyworld: Onion, Expire, Newton
=============================================

A small superhero-style story world about a brave helper, a cautionary warning,
and a spoiled lunch. The key turning point is whether Newton notices the
onion's warning signs before it expires, then uses bravery and sound effects to
fix the problem.

This world keeps the simulation simple but state-driven:
- physical meters: freshness, stink, power, noise, hunger
- emotional memes: caution, bravery, relief, worry, pride
- one child-sized hero, one helper, one food item, and one small problem

The generated story should always have:
- a setup with Newton and a fresh onion
- a cautionary warning about expiration
- a brave response with sound effects
- a resolution image showing what changed
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["freshness", "stink", "power", "noise", "hunger"]:
            self.meters.setdefault(k, 0.0)
        for k in ["caution", "bravery", "relief", "worry", "pride", "alarm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    setting: str
    name: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": "the kitchen",
    "apartment": "the apartment",
    "lab": "the tiny lab",
    "rooftop": "the rooftop garden",
}

NAMES = ["Newton", "Nina", "Milo", "Maya", "Theo", "Tessa"]
HELPERS = ["mother", "father", "big sister", "big brother", "neighbor"]

ASP_RULES = r"""
hero(H) :- named(H, _).
expired(O) :- food(O), freshness(O, F), F < 1.
warns(H, O) :- hero(H), onion(O), expired(O), cautionary(O).
needs_fix(O) :- expired(O), onion(O).
brave(H) :- hero(H), bravery(H, B), B >= 1.
solves(H, O) :- brave(H), needs_fix(O), sound_effects(H).
valid_story(S, N, H) :- setting(S), named(N, "Newton"), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines += [asp.fact("named", n, n) for n in NAMES]
    lines += [asp.fact("helper", h) for h in HELPERS]
    lines += [asp.fact("cautionary", "onion")]
    lines += [asp.fact("bravery", "Newton")]
    lines += [asp.fact("sound_effects", "Newton")]
    lines += [asp.fact("onion", "onion")]
    lines += [asp.fact("food", "onion")]
    lines += [asp.fact("expired_food", "onion")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _r_expire(world: World) -> list[str]:
    out = []
    onion = world.get("onion")
    if onion.meters["freshness"] < THRESHOLD and ("expire",) not in world.fired:
        world.fired.add(("expire",))
        onion.meters["stink"] += 2
        onion.memes["alarm"] += 1
        out.append("The onion had started to expire, and a sharp smell curled into the air.")
    return out


def _r_warning(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    onion = world.get("onion")
    if onion.meters["stink"] >= THRESHOLD and hero.memes["caution"] < THRESHOLD:
        sig = ("warn",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["caution"] += 1
        hero.memes["worry"] += 1
        out.append("Newton frowned, because the smell was a cautionary clue that something was going bad.")
    return out


def _r_bravery(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    onion = world.get("onion")
    helper = world.get("helper")
    if hero.memes["caution"] >= THRESHOLD and hero.memes["bravery"] < THRESHOLD:
        sig = ("brave",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["bravery"] += 1
        hero.meters["power"] += 1
        onion.meters["freshness"] += 1
        onion.meters["stink"] = max(0.0, onion.meters["stink"] - 2)
        hero.meters["noise"] += 1
        out.append(f'Newton said, "Zap! Whirr! Swoosh!" and rushed to save the onion with {helper.label}.')
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    onion = world.get("onion")
    if hero.memes["bravery"] >= THRESHOLD and onion.meters["stink"] < THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        hero.memes["relief"] += 1
        hero.memes["pride"] += 1
        out.append("The onion stopped smelling sour, and Newton stood tall like a tiny superhero.")
    return out


RULES = [_r_expire, _r_warning, _r_bravery, _r_relief]


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


def tell(setting: str, name: str, helper: str) -> World:
    w = World(setting=setting)
    hero = w.add(Entity(id="hero", kind="character", type="boy", label=name))
    side = w.add(Entity(id="helper", kind="character", type=helper.replace(" ", "_"), label=helper))
    onion = w.add(Entity(id="onion", kind="thing", type="onion", label="onion", phrase="a little onion"))
    onion.meters["freshness"] = 2.0
    hero.meters["hunger"] = 1.0
    hero.memes["caution"] = 0.0
    hero.memes["bravery"] = 0.0

    w.say(f"{name} was a tiny superhero who lived in {setting}.")
    w.say(f"One morning, {name} found {onion.phrase} on the table, and it looked bright and ready.")
    w.say(f"{name} loved helping in a careful way, and {helper} liked watching that brave little spark.")

    w.para()
    w.say(f"Then the onion sat too long in the warm room.")
    onion.meters["freshness"] = 0.0
    propagate(w, narrate=True)

    w.para()
    w.say(f"{name} sniffed the air, made a careful face, and listened to the cautionary smell.")
    propagate(w, narrate=True)

    w.para()
    w.say(f"{name} raised {name}'s chin, took a brave breath, and shouted, \"Zap! Whirr! Swoosh!\"")
    propagate(w, narrate=True)

    w.para()
    w.say(f"In the end, the onion was safe again, {name} felt proud, and the kitchen smelled fresh instead of sharp.")
    w.facts.update(hero=hero, helper=side, onion=onion, setting=setting, name=name)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child named {f["name"]} in {f["setting"]} about an onion that may expire.',
        f"Tell a cautionary but brave story where {f['name']} notices a bad smell, uses sound effects, and helps save the onion.",
        f'Write a gentle hero story that includes the words "onion", "expire", and "Newton".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    onion = f["onion"]
    return [
        QAItem(
            question=f"Who is the hero of the story?",
            answer=f"The hero is {hero.label}, a tiny superhero who pays attention to careful warning signs.",
        ),
        QAItem(
            question="Why did Newton become worried about the onion?",
            answer="Newton became worried because the onion started to expire and gave off a sharp smell.",
        ),
        QAItem(
            question=f"What sound effects did {hero.label} use to help?",
            answer=f"{hero.label} used the sound effects \"Zap! Whirr! Swoosh!\" while helping save the onion.",
        ),
        QAItem(
            question=f"Who was with {hero.label} when the problem was fixed?",
            answer=f"{helper.label} was there, and together they helped the onion turn from smelly back to safe.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="By the end, the onion smelled fresh again and Newton felt proud instead of worried.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when food expires?",
            answer="When food expires, it is no longer fresh and may start to smell bad or go wrong.",
        ),
        QAItem(
            question="What is a cautionary warning?",
            answer="A cautionary warning is a sign that helps someone stop and think before a problem gets worse.",
        ),
        QAItem(
            question="Why do sound effects make a hero story fun?",
            answer="Sound effects make the action feel lively, like the hero is really moving and working hard.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when something feels a little scary or hard.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld about an onion that may expire.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    name = args.name or "Newton"
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.name, params.helper)
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


CURATED = [
    StoryParams(setting="kitchen", name="Newton", helper="mother"),
    StoryParams(setting="apartment", name="Newton", helper="father"),
    StoryParams(setting="lab", name="Newton", helper="neighbor"),
]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    seen = set(asp.atoms(model, "valid_story"))
    want = {(k, "Newton", h) for k in SETTINGS for h in HELPERS}
    if seen == want:
        print(f"OK: ASP parity matches ({len(seen)} stories).")
        return 0
    print("MISMATCH between ASP and Python expectation:")
    print("  ASP:", sorted(seen))
    print("  PY :", sorted(want))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        for s in stories:
            print(s)
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
