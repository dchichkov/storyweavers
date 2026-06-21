#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rung_bad_ending_fairy_tale.py
==============================================================

A small standalone storyworld in a fairy-tale key.

Seed premise
------------
A curious child or young heir climbs a magical ladder or tower "rung" by rung
to reach something shining high above. A warning comes, but the climb continues.
The ladder fails, the helper cannot save the day, and the ending is bad:
the treasure is lost, the climb is over, and the lesson remains.

This world keeps the story child-facing and concrete, but models the turn as
state change: height, strain, trust, warning, fracture, and loss.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/rung_bad_ending_fairy_tale.py
    python storyworlds/worlds/gpt-5.4-mini/rung_bad_ending_fairy_tale.py --qa
    python storyworlds/worlds/gpt-5.4-mini/rung_bad_ending_fairy_tale.py --verify
    python storyworlds/worlds/gpt-5.4-mini/rung_bad_ending_fairy_tale.py --all
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman"}
        male = {"boy", "prince", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Tale:
    id: str
    place: str
    tower: str
    prize: str
    prize_phrase: str
    rung_word: str = "rung"
    warning: str = ""
    ending: str = ""


@dataclass
class ClimbGear:
    id: str
    label: str
    helps: str
    safe: bool = True


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wear(world: World) -> list[str]:
    out: list[str] = []
    climber = world.entities.get("climber")
    ladder = world.entities.get("ladder")
    if not climber or not ladder:
        return out
    if climber.meters.get("height", 0.0) < THRESHOLD:
        return out
    sig = ("wear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    climber.memes["daring"] = climber.memes.get("daring", 0.0) + 1
    ladder.meters["strain"] = ladder.meters.get("strain", 0.0) + 1
    out.append("__strain__")
    return out


def _r_fracture(world: World) -> list[str]:
    ladder = world.entities.get("ladder")
    if not ladder:
        return []
    if ladder.meters.get("strain", 0.0) < THRESHOLD:
        return []
    sig = ("fracture",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ladder.meters["broken"] = ladder.meters.get("broken", 0.0) + 1
    world.get("hall").meters["danger"] = world.get("hall").meters.get("danger", 0.0) + 1
    world.get("climber").memes["fear"] = world.get("climber").memes.get("fear", 0.0) + 1
    return ["__crack__"]


CAUSAL_RULES = [
    Rule("wear", "physical", _r_wear),
    Rule("fracture", "physical", _r_fracture),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def can_reach_prize(tale: Tale) -> bool:
    return tale.prize_phrase.startswith("high") or tale.prize_phrase.startswith("above")


def is_reasonable(tale: Tale, gear: ClimbGear) -> bool:
    return gear.safe and can_reach_prize(tale)


def predict_break(world: World, climb: int) -> dict:
    sim = world.copy()
    sim.get("climber").meters["height"] = float(climb)
    propagate(sim, narrate=False)
    return {
        "broken": sim.get("ladder").meters.get("broken", 0.0) >= THRESHOLD,
        "danger": sim.get("hall").meters.get("danger", 0.0),
    }


def introduce(world: World, hero: Entity, helper: Entity, tale: Tale) -> None:
    world.say(
        f"Once in a small fairy-tale kingdom, {hero.id} lived in a bright hall "
        f"beneath {tale.tower}. {hero.id} loved the shining thing hidden above the beams."
    )
    world.say(
        f"{helper.id} was there too, watching the old ladder and its long wooden {tale.rung_word}s."
    )


def tempt(world: World, hero: Entity, tale: Tale) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(
        f'"I can reach it," said {hero.id}. "{tale.rung_word.capitalize()} by {tale.rung_word}, I will climb."'
    )


def warn(world: World, helper: Entity, hero: Entity, tale: Tale) -> None:
    pred = predict_break(world, 1)
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1
    world.facts["predicted_break"] = pred["broken"]
    world.say(
        f'{helper.id} frowned and touched the wood. "{hero.id}, the ladder is old. '
        f'One weak {tale.rung_word} can snap."'
    )
    world.say(f'"Please stay down," {helper.id} begged.')


def climb(world: World, hero: Entity, steps: int, tale: Tale) -> None:
    hero.meters["height"] = float(steps)
    world.say(
        f"{hero.id} ignored the warning and climbed higher, {tale.rung_word} by {tale.rung_word}, "
        f"until the hall felt small below."
    )
    propagate(world, narrate=False)


def crack_and_fall(world: World, hero: Entity, helper: Entity, tale: Tale) -> None:
    ladder = world.get("ladder")
    ladder.meters["broken"] = 1.0
    hero.meters["fall"] = 1.0
    world.say(
        f"Then there came a sharp crack. A {tale.rung_word} split, the ladder buckled, and "
        f"{hero.id} tumbled down through the dust."
    )
    world.say(f"{helper.id} cried out, but the broken wood could not catch {hero.id}.")


def bad_ending(world: World, hero: Entity, helper: Entity, tale: Tale) -> None:
    hero.memes["regret"] = hero.memes.get("regret", 0.0) + 1
    helper.memes["sadness"] = helper.memes.get("sadness", 0.0) + 1
    world.say(
        f"In the end, the shining prize was lost in the dark above, and the hall was only "
        f"splinters and tears."
    )
    world.say(
        f"{hero.id} learned too late that some doors in fairy tales should stay closed, "
        f"and some {tale.rung_word}s should never be climbed too fast."
    )


def tell(tale: Tale, gear: ClimbGear) -> World:
    world = World()
    hero = world.add(Entity(id="Ayla", kind="character", type="girl", role="climber"))
    helper = world.add(Entity(id="Merrin", kind="character", type="woman", role="helper"))
    ladder = world.add(Entity(id="ladder", label="the ladder", meters={"strain": 0.0, "broken": 0.0}))
    hall = world.add(Entity(id="hall", label="the hall", meters={"danger": 0.0}))
    prize = world.add(Entity(id="prize", label=tale.prize, kind="thing"))

    world.facts.update(tale=tale, gear=gear, hero=hero, helper=helper, ladder=ladder, hall=hall, prize=prize)

    introduce(world, hero, helper, tale)
    world.para()
    tempt(world, hero, tale)
    warn(world, helper, hero, tale)
    world.para()
    climb(world, hero, steps=2, tale=tale)
    crack_and_fall(world, hero, helper, tale)
    world.para()
    bad_ending(world, hero, helper, tale)
    return world


TALES = {
    "tower": Tale(
        id="tower",
        place="the castle hall",
        tower="the glass tower",
        prize="a silver bird",
        prize_phrase="high above the rafters",
        rung_word="rung",
        warning="the old ladder can snap",
        ending="bad",
    ),
    "well": Tale(
        id="well",
        place="the old courtyard",
        tower="the wishing well",
        prize="a golden coin",
        prize_phrase="above the well rope",
        rung_word="rung",
        warning="the stone lip is slick",
        ending="bad",
    ),
    "tree": Tale(
        id="tree",
        place="the orchard",
        tower="the tall apple tree",
        prize="a red apple crown",
        prize_phrase="high in the branches",
        rung_word="rung",
        warning="the branch is brittle",
        ending="bad",
    ),
}

GEAR = {
    "none": ClimbGear(id="none", label="no gear", helps="nothing", safe=True),
    "gloves": ClimbGear(id="gloves", label="soft gloves", helps="better grip", safe=True),
}

NAMES = ["Ayla", "Mina", "Elsie", "Nora", "Iris", "Talia"]
HELPERS = ["Merrin", "Brida", "The Queen", "The Old Nurse"]


@dataclass
class StoryParams:
    tale: str
    hero: str
    helper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(tale="tower", hero="Ayla", helper="Merrin", seed=1),
    StoryParams(tale="well", hero="Mina", helper="Brida", seed=2),
    StoryParams(tale="tree", hero="Elsie", helper="The Old Nurse", seed=3),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(t, "none", "bad") for t in TALES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale storyworld with a bad ending.")
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--gear", choices=GEAR)
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
    tale = args.tale or rng.choice(list(TALES))
    if tale not in TALES:
        raise StoryError("Unknown tale.")
    gear = args.gear or "none"
    if gear not in GEAR:
        raise StoryError("Unknown gear.")
    if not is_reasonable(TALES[tale], GEAR[gear]):
        raise StoryError("This story only works when the prize is really high enough to tempt a climb.")
    hero = rng.choice(NAMES)
    helper = rng.choice(HELPERS)
    return StoryParams(tale=tale, hero=hero, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tale = f["tale"]
    return [
        f"Write a fairy tale with a rung, a warning, and a bad ending in {tale.tower}.",
        f"Tell a small fairy tale where {f['hero'].id} climbs {tale.rung_word} by {tale.rung_word} and the ladder breaks.",
        f"Write a child-facing fairy tale that includes the word rung and ends sadly after a dangerous climb.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tale = f["tale"]
    hero = f["hero"]
    helper = f["helper"]
    return [
        ("Who tried to climb the ladder?",
         f"{hero.id} tried to climb the ladder to reach the shining prize above."),
        ("What warning did the helper give?",
         f"{helper.id} warned that the ladder was old and that one weak rung could snap. "
         f"The warning was meant to keep the climb safe."),
        ("How did the story end?",
         f"It ended badly. The ladder broke, {hero.id} fell, and the shining prize stayed lost above."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a rung?",
         "A rung is one of the crosspieces on a ladder or a climbing frame. You put your foot on it when you climb."),
        ("Why can an old ladder be dangerous?",
         "Old wood can get weak and break. If a ladder breaks, someone can fall and get hurt."),
        ("What should you do if something looks unsafe to climb?",
         "You should stop and call a grown-up for help. It is safer to stay on the ground."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {', '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
climb(X) :- hero(X).
warning(X) :- helper(X).
bad_ending :- climb(X), warning(Y).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("hero", "ayla"), asp.fact("helper", "merrin")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show climb/1. #show warning/1."))
        _ = model
    except Exception as e:
        print(f"ASP unavailable or failed: {e}")
        return 1
    print("OK: ASP smoke test ran.")
    return 0


def generate(params: StoryParams) -> StorySample:
    tale = TALES.get(params.tale)
    if tale is None:
        raise StoryError("Invalid tale.")
    gear = GEAR["none"]
    world = tell(tale, gear)
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
    if args.show_asp:
        print(asp_program("#show hero/1. #show helper/1."))
        return
    if args.verify:
        rc = asp_verify()
        # normal generate/emit smoke test
        sample = generate(CURATED[0])
        emit(sample)
        if not sample.story:
            rc = 1
        sys.exit(rc)
    if args.asp:
        print(asp_program("#show hero/1. #show helper/1."))
        return
    seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = [generate(CURATED[0])] if not args.all else [generate(p) for p in CURATED]
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
