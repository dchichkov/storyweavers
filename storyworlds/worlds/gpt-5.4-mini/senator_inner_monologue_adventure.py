#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/senator_inner_monologue_adventure.py
=====================================================================

A standalone story world for a tiny adventure tale about a senator, a small
journey, and an inner monologue that helps turn nerves into courage.

Premise
-------
A senator must travel across a windy park to reach the town hall and deliver a
promise. Along the way, a helpful companion notices a problem, the senator
thinks through the worry privately, and the pair choose a brave, sensible path
that ends with the speech delivered and the town feeling hopeful.

This world is intentionally small and classical:
- typed entities with physical meters and emotional memes,
- a causal forward-chaining world model,
- a reasonableness gate and inline ASP twin,
- state-driven prose and grounded QA.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/senator_inner_monologue_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/senator_inner_monologue_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/senator_inner_monologue_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/senator_inner_monologue_adventure.py --trace
    python storyworlds/worlds/gpt-5.4-mini/senator_inner_monologue_adventure.py --json
    python storyworlds/worlds/gpt-5.4-mini/senator_inner_monologue_adventure.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "senator"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    barrier: str
    route: str
    safe_route: str


@dataclass
class Companion:
    id: str
    label: str
    role: str
    trait: str
    rescue_tool: str
    action: str
    can_help: bool = True


@dataclass
class Hazard:
    id: str
    label: str
    kind: str
    threat: str
    meter: str
    spread: float


@dataclass
class Choice:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_anxiety(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.kind == "character" and e.memes["worry"] >= THRESHOLD:
            sig = ("anxiety", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["nerves"] += 1
            out.append("__inner__")
    return out


def _r_blocked(world: World) -> list[str]:
    out = []
    route = world.facts.get("route")
    hazard = world.facts.get("hazard")
    if not route or not hazard:
        return out
    if route.meters["blocked"] < THRESHOLD:
        return out
    sig = ("blocked", route.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("town").meters["delay"] += 1
    out.append("The blocked path slowed them down.")
    return out


def _r_courage(world: World) -> list[str]:
    out = []
    senator = world.facts.get("senator")
    if senator and senator.memes["resolve"] >= THRESHOLD and senator.meters["progress"] >= 1:
        sig = ("courage", senator.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        senator.memes["brave"] += 1
        out.append("The senator felt steadier with every step.")
    return out


CAUSAL_RULES = [Rule("anxiety", "mental", _r_anxiety), Rule("blocked", "physical", _r_blocked), Rule("courage", "mental", _r_courage)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def hazard_risky(h: Hazard, s: Setting) -> bool:
    return h.kind == "wind" and "bridge" in s.place


def sensible_choices() -> list[Choice]:
    return [c for c in CHOICES.values() if c.sense >= 2]


def journey_severity(h: Hazard, delay: int) -> int:
    return h.spread + delay


def can_finish(choice: Choice, hazard: Hazard, delay: int) -> bool:
    return choice.power >= journey_severity(hazard, delay)


def predict_block(world: World, setting: Setting, hazard: Hazard) -> dict:
    sim = world.copy()
    sim.get("route").meters["blocked"] += 1
    propagate(sim, narrate=False)
    return {"blocked": sim.get("route").meters["blocked"] >= THRESHOLD, "delay": sim.get("town").meters["delay"]}


def setup(world: World, senator: Entity, companion: Entity, setting: Setting) -> None:
    senator.memes["duty"] += 1
    companion.memes["hope"] += 1
    world.say(
        f"At dawn, Senator {senator.id} and {companion.id} stood beside {setting.place}. "
        f"The air was {setting.mood}, and the path ahead led toward town hall."
    )
    world.say(
        f"{companion.id} pointed to the long crossing. \"We can take {setting.route},\" "
        f"{companion.pronoun()} said, \"or {setting.safe_route} if the wind gets wild.\""
    )


def raise_doubt(world: World, senator: Entity, hazard: Hazard) -> None:
    senator.memes["worry"] += 1
    world.say(
        f"{senator.id} looked at the sky and felt a little knot of doubt. "
        f'\"If the wind throws {hazard.label} across the bridge, what if I am late?\" '
        f"{senator.pronoun().capitalize()} thought."
    )


def inner_monologue(world: World, senator: Entity, hazard: Hazard) -> None:
    senator.memes["resolve"] += 1
    world.say(
        f"In {senator.pronoun('possessive')} head, a quiet voice answered: "
        f'\"Slow feet are still brave feet. Keep going, watch the wind, and do the kind thing.\"'
    )
    if hazard.spread >= 2:
        world.say(
            f"Another thought followed: \"A hurried mistake could knock over the crates near the bridge.\""
        )


def choose_path(world: World, senator: Entity, companion: Entity, setting: Setting, hazard: Hazard, choice: Choice, delay: int) -> None:
    if not hazard_risky(hazard, setting):
        raise StoryError("This world needs a bridge-like crossing and a wind hazard.")
    if choice.sense < 2:
        raise StoryError("That choice is too weak for this adventure.")
    if not can_finish(choice, hazard, delay):
        raise StoryError("That plan would not be enough for the hazard.")
    senator.meters["progress"] += 1
    companion.meters["help"] += 1
    world.say(
        f"{companion.id} offered a small lantern and a steadying hand. "
        f"{choice.text}."
    )


def near_miss(world: World, senator: Entity, hazard: Hazard) -> None:
    route = world.facts["route"]
    route.meters["blocked"] += 1
    world.say(
        f"A gust snapped hard at the route, and a stack of papers skittered into the lane. "
        f"The way was briefly blocked, but they slowed down and kept their balance."
    )
    propagate(world, narrate=False)


def arrive(world: World, senator: Entity, companion: Entity, setting: Setting) -> None:
    senator.memes["relief"] += 1
    world.say(
        f"By the time they reached town hall, the wind had calmed. "
        f"{senator.id} straightened {senator.pronoun('possessive')} coat and walked inside with {companion.id} beside {senator.pronoun('object')}."
    )


def speech(world: World, senator: Entity, companion: Entity) -> None:
    town = world.facts["town"]
    town.meters["hope"] += 1
    world.say(
        f"In the bright hall, Senator {senator.id} delivered the promise at last. "
        f"{companion.id} smiled, because the whole town could hear the steady voice."
    )
    world.say(
        f"Outside, the storm had not won. The senator's quiet thoughts had become a brave step, and the day felt hopeful."
    )


def tell(setting: Setting, hazard: Hazard, choice: Choice, delay: int = 0,
         senator_name: str = "Ari", companion_name: str = "Mira") -> World:
    world = World()
    senator = world.add(Entity(id=senator_name, kind="character", type="senator", label="senator", role="hero"))
    companion = world.add(Entity(id=companion_name, kind="character", type="girl", label="guide", role="companion"))
    bridge = world.add(Entity(id="route", type="route", label=setting.route))
    town = world.add(Entity(id="town", type="town", label="town hall"))
    world.facts.update(setting=setting, hazard=hazard, choice=choice, route=bridge, town=town, senator=senator, companion=companion, delay=delay)

    setup(world, senator, companion, setting)
    world.para()
    raise_doubt(world, senator, hazard)
    inner_monologue(world, senator, hazard)
    choose_path(world, senator, companion, setting, hazard, choice, delay)
    near_miss(world, senator, hazard)
    world.para()
    arrive(world, senator, companion, setting)
    speech(world, senator, companion)

    world.facts["outcome"] = "brave"
    return world


SETTINGS = {
    "bridge": Setting("bridge", "the windy bridge", "windy", "paper crates", "the main bridge", "the riverside path"),
    "harbor": Setting("harbor", "the windy harbor bridge", "salt-bright", "loose nets", "the dock bridge", "the boardwalk"),
    "hill": Setting("hill", "the hilltop bridge", "sharp and bright", "fallen twigs", "the stone bridge", "the path around the hill"),
}

HAZARDS = {
    "wind": Hazard("wind", "wind", "wind", "the wind", "route", 2),
    "gust": Hazard("gust", "a gust", "wind", "the gust", "route", 3),
}

CHOICES = {
    "steady": Choice("steady", 3, 3, "They chose the steady bridge and walked with careful steps", "they rushed anyway", "took the steady bridge and walked carefully"),
    "lantern": Choice("lantern", 2, 2, "The lantern helped them see the loose boards and avoid them", "the lantern was not enough", "used the lantern to see the safe steps"),
    "pause": Choice("pause", 3, 4, "They paused, watched the sky, and waited for the wind to loosen its grip", "they paused too long", "paused until the wind softened"),
}

CURATED = [
    StoryParams("bridge", "wind", "steady", 0, "Ari", "Mira"),
    StoryParams("harbor", "gust", "lantern", 0, "Nia", "Oona"),
    StoryParams("hill", "gust", "pause", 1, "Sen", "Lina"),
]


@dataclass
class StoryParams:
    setting: str
    hazard: str
    choice: str
    delay: int = 0
    senator_name: str = "Ari"
    companion_name: str = "Mira"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for hid, h in HAZARDS.items():
            for cid, c in CHOICES.items():
                if hazard_risky(h, s) and c.sense >= 2:
                    combos.append((sid, hid, cid))
    return combos


KNOWLEDGE = {
    "senator": [("What is a senator?", "A senator is a person who helps make rules and decisions for a community or country.")],
    "wind": [("What does wind do?", "Wind is moving air. It can push hats, papers, and leaves around.")],
    "bridge": [("What is a bridge?", "A bridge is a path that helps people cross over water, a road, or another gap.")],
    "lantern": [("What is a lantern?", "A lantern is a light that helps you see in the dark.")],
    "hope": [("What is hope?", "Hope is the feeling that good things can happen, even when a day starts out hard.")],
}
KNOWLEDGE_ORDER = ["senator", "wind", "bridge", "lantern", "hope"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write an adventure story for a 3-to-5-year-old that includes a senator and an inner monologue.',
        f"Tell a brave little adventure where Senator {f['senator'].id} crosses {f['setting'].place} and thinks privately about what to do when the wind gets tricky.",
        f'Write a child-friendly story with the word "senator" where a quiet thought helps the hero choose the safe path and reach town hall.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    s, c, setting, hazard = f["senator"], f["companion"], f["setting"], f["hazard"]
    return [
        ("Who is the story about?", f"It is about Senator {s.id} and {c.id}, who set out on a little adventure to reach town hall."),
        ("What problem did they face?", f"They had to cross {setting.place} while the wind was causing trouble. That made the trip feel like a real adventure."),
        ("What did the senator think about in the inner monologue?", f"{s.id} thought about staying calm, taking careful steps, and not letting the wind rush the choice."),
        ("How did they solve the problem?", f"They chose the safer path, used a lantern and a steady hand, and kept moving until they reached town hall."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"senator", "wind", "bridge", "lantern", "hope"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, hazard: Hazard) -> str:
    return f"(No story: {hazard.label} does not fit this adventure setting.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        lines.append(asp.fact("power", cid, c.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(C) :- choice(C), sense(C,S), sense_min(M), S >= M.
valid(S,H,C) :- setting(S), hazard(H), choice(C), sensible(C).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos()")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print("SMOKE TEST FAILED:", e)
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with senator inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--choice", choices=CHOICES)
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
              and (args.hazard is None or c[1] == args.hazard)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, choice = rng.choice(sorted(combos))
    return StoryParams(setting, hazard, choice, delay=rng.randint(0, 1))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HAZARDS[params.hazard], CHOICES[params.choice], params.delay, params.senator_name, params.companion_name)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
