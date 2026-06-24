#!/usr/bin/env python3
"""
storyworlds/worlds/breast_suspense_space_adventure.py
======================================================

A small space-adventure storyworld with suspense: a child crew, a dim ship,
a tense problem, and a safe, clever resolution.

Premise:
- A little astronaut wants to cross a quiet ship corridor during a power dip.
- A careful helper notices a risky panel, a drifting object, or a low-light
  situation that could cause trouble.
- They use a simple space tool or procedure to restore safety.

This world keeps the prose child-facing and concrete while modeling physical
meters and emotional memes. It supports the shared Storyweavers contract:
StoryParams, registries, build_parser, resolve_params, generate, emit, main,
QA, JSON, ASP twin, trace, verify, and show-asp.

The seed word "breast" is included as a harmless spacecraft term in one of the
labels: a ship's "breast panel" is the curved front shield on the little shuttle.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SAFE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    name: str
    darkness: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    rush: str
    tension: str
    meter_key: str
    zone: set[str]
    light_needed: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    risky: str
    meter_key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    fixes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    ship = world.get("ship")
    for ent in world.entities.values():
        if ent.meters["drift"] >= THRESHOLD and ent.id != "ship":
            sig = ("danger", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ship.meters["danger"] += 1
            out.append("The ship felt tighter and more tense.")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ship").meters["danger"] < THRESHOLD:
        return out
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] += 1
        out.append("Everyone held still for a breath.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ship").meters["danger"] < THRESHOLD:
        return out
    for ent in world.entities.values():
        if ent.meters["fixed"] >= THRESHOLD:
            sig = ("fixed", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.get("ship").meters["danger"] = 0
            out.append("The danger eased at last.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_danger, _r_fear, _r_fix):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    setting: str
    activity: str
    hazard: str
    tool: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "shuttle": Setting(name="the little shuttle", darkness="the front window", affords={"dock_walk", "panel_check"}, tags={"ship", "space"}),
    "station": Setting(name="the moon station", darkness="the long corridor", affords={"dock_walk", "panel_check"}, tags={"ship", "space"}),
    "cabin": Setting(name="the tiny cabin", darkness="the round porthole", affords={"dock_walk"}, tags={"ship", "space"}),
}

ACTIVITIES = {
    "dock_walk": Activity(id="dock_walk", verb="walk to the docking hatch", rush="hurry down the corridor", tension="the corridor felt extra quiet", meter_key="drift", zone={"corridor"}, tags={"space", "walk"}),
    "panel_check": Activity(id="panel_check", verb="check the control panel", rush="rush to the panel", tension="the lights blinked like sleepy stars", meter_key="drift", zone={"panel"}, tags={"space", "panel"}),
}

HAZARDS = {
    "drift": Hazard(id="drift", label="a drifting toolbox", phrase="a drifting toolbox", risky="it could bump into the wall", meter_key="drift", tags={"drift", "toolbox"}),
    "dim": Hazard(id="dim", label="a dim panel", phrase="a dim control panel", risky="it was hard to read in the dark", meter_key="drift", tags={"panel", "dim"}),
    "breast": Hazard(id="breast", label="the breast panel", phrase="the curved breast panel", risky="it stood out at the front of the shuttle", meter_key="drift", tags={"breast", "panel"}),
}

TOOLS = {
    "lamp": Tool(id="lamp", label="a pocket lamp", phrase="a pocket lamp", use="shone a bright path", fixes={"drift", "dim", "breast"}, tags={"light"}),
    "magnet": Tool(id="magnet", label="a small magnet hook", phrase="a small magnet hook", use="pulled the toolbox back", fixes={"drift"}, tags={"tool"}),
    "tape": Tool(id="tape", label="bright tape", phrase="bright tape", use="marked the edge clearly", fixes={"dim", "breast"}, tags={"mark"}),
}


GIRL_NAMES = ["Mia", "Luna", "Zoe", "Nia", "Iris", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Kai", "Noah", "Eli", "Tate"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for a_id in setting.affords:
            for h_id, hazard in HAZARDS.items():
                if h_id not in setting.tags and h_id != "breast":
                    continue
                for t_id, tool in TOOLS.items():
                    if hazard.id in tool.fixes:
                        combos.append((s_id, a_id, h_id))
    return combos


def valid_combos_with_tools() -> list[tuple[str, str, str, str]]:
    combos = []
    for s_id, a_id, h_id in valid_combos():
        hazard = HAZARDS[h_id]
        for t_id, tool in TOOLS.items():
            if hazard.id in tool.fixes:
                combos.append((s_id, a_id, h_id, t_id))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(s.affords):
            lines.append(asp.fact("affords", sid, act))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("risky", hid, h.meter_key))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for fx in sorted(t.fixes):
            lines.append(asp.fact("fixes", tid, fx))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,H,T) :- setting(S), affords(S,A), hazard(H), tool(T), fixes(T,H).
showable(H) :- hazard(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting=setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper))
    ship = world.add(Entity(id="ship", type="ship", label=setting.name))
    hazard = world.add(Entity(id="hazard", type="thing", label=HAZARDS[params.hazard].label))
    tool = world.add(Entity(id="tool", type="tool", label=TOOLS[params.tool].label))
    ship.meters["danger"] = 0
    hazard.meters["drift"] = 1
    tool.meters["fixed"] = 0
    helper.memes["calm"] = 1
    hero.memes["curiosity"] = 1
    world.facts.update(hero=hero, helper=helper, ship=ship, hazard=hazard, tool=tool, params=params)
    return world


def tell(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    hazard = world.facts["hazard"]
    tool = world.facts["tool"]
    act = ACTIVITIES[params.activity]
    hz = HAZARDS[params.hazard]
    tp = TOOLS[params.tool]
    world.say(f"{hero.noun()} and {helper.noun()} were inside {world.setting.name}.")
    world.say(f"Their little adventure began when {act.tension}.")
    world.para()
    hero.memes["suspense"] += 1
    world.say(f"{hero.pronoun().capitalize()} wanted to {act.verb}, but then {hz.phrase} made the ship feel uncertain.")
    world.say(f"{helper.pronoun().capitalize()} saw it first and said, \"Wait.\"")
    world.para()
    hazard.meters["drift"] += 1
    propagate(world)
    tool.meters["fixed"] += 1
    world.say(f"They used {tp.phrase}; it {tp.use}.")
    propagate(world)
    world.para()
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(f"In the end, {hero.noun()} and {helper.noun()} kept the ship safe and finished their little space job.")
    world.say(f"The {world.setting.name} glowed steady again, and the {hz.label} no longer felt scary.")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    hazard = f["hazard"]
    tool = f["tool"]
    params = f["params"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.label} and {helper.label} on {world.setting.name}. They were having a small space adventure together.",
        ),
        QAItem(
            question=f"What problem made the trip feel tense?",
            answer=f"{hazard.label.capitalize()} made things tense because it could cause trouble in the ship. That is why the children had to stop and be careful.",
        ),
        QAItem(
            question=f"What did they use to solve the problem?",
            answer=f"They used {tool.label}. It gave them a safe way to fix the problem without making the ship more dangerous.",
        ),
        QAItem(
            question=f"Why did the helper say wait?",
            answer=f"The helper said wait because the ship felt risky and they needed a careful plan. The suspense came from that quiet moment before the fix.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a shuttle?", answer="A shuttle is a small space vehicle that carries people from one place to another."),
        QAItem(question="What does a pocket lamp do?", answer="A pocket lamp shines light so you can see in dark places."),
        QAItem(question="What does suspense mean in a story?", answer="Suspense is the feeling that something important might happen soon, so you keep reading to find out."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a young child where {f["hero"].label} and {f["helper"].label} face a tense moment in {world.setting.name}.',
        f'Tell a suspenseful but gentle story where {f["hazard"].label} makes a little ship problem and {f["tool"].label} helps fix it.',
        f'Write a child-friendly astronaut story that includes the word "breast" as part of a ship detail and ends safely.',
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story q&a ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world q&a ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="shuttle", activity="dock_walk", hazard="breast", tool="lamp", hero="Mia", hero_gender="girl", helper="Leo", helper_gender="boy"),
    StoryParams(setting="station", activity="panel_check", hazard="dim", tool="tape", hero="Noah", hero_gender="boy", helper="Ava", helper_gender="girl"),
    StoryParams(setting="cabin", activity="dock_walk", hazard="drift", tool="magnet", hero="Luna", hero_gender="girl", helper="Finn", helper_gender="boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, activity, hazard = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(tid for tid, t in TOOLS.items() if hazard in t.fixes))
    if hazard not in TOOLS[tool].fixes:
        raise StoryError("The chosen tool cannot solve that problem.")
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    if helper == hero:
        helper = helper + "a"
    return StoryParams(setting=setting, activity=activity, hazard=hazard, tool=tool, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if params.hazard not in HAZARDS:
        raise StoryError("Unknown hazard.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if HAZARDS[params.hazard].id not in TOOLS[params.tool].fixes:
        raise StoryError("That tool does not fit the problem.")
    world = _make_world(params)
    tell(world, params)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.label, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful little space-adventure storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("ASP mismatch")
        print("py only:", sorted(py - cl))
        print("cl only:", sorted(cl - py))
        return 1
    print(f"OK: ASP matches Python ({len(py)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
