#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/category_travel_problem_solving_inner_monologue_space.py
========================================================================================================

A small space-adventure storyworld about travel, a problem on the way, and a
careful inner-monologue fix.

The premise is simple: a young traveler is on a trip between space places when
something practical goes wrong. The traveler thinks through the problem, uses
a tool or clue, and keeps going with a changed state at the end.

The world is intentionally tiny and classical:
- one traveler
- one destination
- one travel problem
- one problem-solving tool or method
- one emotional arc that is narrated through inner monologue

The prose is authored from simulated state, not from a frozen template.
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    usable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    travel_kind: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    noun: str
    verb: str
    symptom: str
    risk: str
    meter: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    fixes: set[str]
    needed: set[str]


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _update_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _update_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _r_problem(world: World) -> list[str]:
    out: list[str] = []
    pilot = world.get("traveler")
    prob = world.facts["problem"]
    if pilot.meters.get(prob.meter, 0.0) < THRESHOLD:
        return out
    sig = ("problem", prob.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _update_meme(pilot, "worry", 1.0)
    _update_meme(pilot, "focus", 1.0)
    out.append(f"{pilot.pronoun().capitalize()} had to slow down and think.")
    return out


def _r_tool_fix(world: World) -> list[str]:
    out: list[str] = []
    pilot = world.get("traveler")
    prob = world.facts["problem"]
    tool = world.facts.get("tool")
    if not tool:
        return out
    if pilot.meters.get(prob.meter, 0.0) < THRESHOLD:
        return out
    if tool.id in world.fired:
        return out
    if prob.id not in tool.fixes:
        return out
    if prob.id == "lost_signal" and pilot.meters.get("signal", 0.0) < THRESHOLD:
        return out
    world.fired.add(tool.id)
    _update_meter(pilot, prob.meter, -1.0)
    _update_meme(pilot, "worry", -1.0)
    _update_meme(pilot, "relief", 1.0)
    out.append(f"The {tool.label} gave {pilot.pronoun('possessive')} plan a way through.")
    return out


CAUSAL_RULES = [_r_problem, _r_tool_fix]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    lines: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)


SETTINGS = {
    "moon_lane": Setting(place="the moon lane", travel_kind="moon trip", afford={"low_fuel", "lost_signal"}),
    "asteroid_gate": Setting(place="the asteroid gate", travel_kind="gate crossing", afford={"stuck_door", "lost_signal"}),
    "skyport": Setting(place="the skyport", travel_kind="dock trip", afford={"stuck_door", "low_fuel"}),
    "ring_route": Setting(place="the ring route", travel_kind="ring travel", afford={"lost_signal", "low_fuel"}),
}

PROBLEMS = {
    "low_fuel": Problem(
        id="low_fuel",
        noun="fuel",
        verb="run low on fuel",
        symptom="the engine light blinked orange",
        risk="the ship would drift too slowly to reach the next station",
        meter="fuel",
    ),
    "stuck_door": Problem(
        id="stuck_door",
        noun="door",
        verb="get stuck",
        symptom="the hatch would not open all the way",
        risk="the ship could not move to the next dock",
        meter="door",
    ),
    "lost_signal": Problem(
        id="lost_signal",
        noun="signal",
        verb="fade out",
        symptom="the map went fuzzy and quiet",
        risk="the traveler could not tell which path was safe",
        meter="signal",
    ),
}

TOOLS = {
    "backup_fuel_cell": Tool(
        id="backup_fuel_cell",
        label="backup fuel cell",
        phrase="a small backup fuel cell",
        action="swap in",
        fixes={"low_fuel"},
        needed=set(),
    ),
    "patch_kit": Tool(
        id="patch_kit",
        label="patch kit",
        phrase="a little patch kit",
        action="press on",
        fixes={"stuck_door"},
        needed=set(),
    ),
    "star_map": Tool(
        id="star_map",
        label="star map",
        phrase="a folded star map",
        action="follow",
        fixes={"lost_signal"},
        needed=set(),
    ),
}

GIRL_NAMES = ["Ari", "Mina", "Luna", "Zia", "Nia", "Rin"]
BOY_NAMES = ["Oren", "Kai", "Jace", "Tobin", "Eli", "Nico"]
TRAITS = ["curious", "careful", "brave", "quiet", "steady", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prob in setting.afford:
            for tool_id, tool in TOOLS.items():
                if prob in tool.fixes:
                    combos.append((place, prob, tool_id))
    return combos


def choose_gendered_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    prob = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    world = World(setting)
    traveler = world.add(Entity(id="traveler", kind="character", type=params.gender, label=params.name))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion, label="the shipmate"))
    tool_ent = world.add(Entity(id="tool", kind="thing", type=tool.id, label=tool.label, phrase=tool.phrase, usable=True))
    tool_ent.carried_by = traveler.id
    tool_ent.owner = traveler.id
    if prob.id == "lost_signal":
        _update_meter(traveler, "signal", 1.0)
    elif prob.id == "low_fuel":
        _update_meter(traveler, "fuel", 1.0)
    elif prob.id == "stuck_door":
        _update_meter(traveler, "door", 1.0)
    world.facts = {"traveler": traveler, "companion": companion, "problem": prob, "tool": tool}
    world.say(f"{traveler.label} was on {setting.travel_kind} to {setting.place}.")
    world.say(f"{traveler.label} liked trips because every new place felt like a tiny planet of its own.")
    world.say(f"{traveler.label} carried {tool.phrase} just in case.")
    world.para()
    world.say(f"Halfway there, {prob.symptom}.")
    _update_meter(traveler, prob.meter, 1.0)
    _update_meme(traveler, "worry", 1.0)
    world.say(f"{traveler.label} looked at the controls and thought, \"{prob.risk}.\"")
    world.say(f"{traveler.label} listened to {params.gender == 'girl' and 'her' or 'his'} own careful inner voice: \"Breathe. Look. Fix one thing at a time.\"")
    propagate(world, narrate=True)
    world.para()
    if prob.id == "low_fuel":
        world.say(f"{traveler.label} checked the gauge, then swapped in the backup cell.")
        world.say(f"The engine hummed again, and the ship stopped wobbling.")
    elif prob.id == "stuck_door":
        world.say(f"{traveler.label} studied the seam, pressed the patch kit into the latch, and gave it a firm twist.")
        world.say(f"The hatch slid open with a soft click.")
    elif prob.id == "lost_signal":
        world.say(f"{traveler.label} unfolded the star map and matched the bright dots to the route.")
        world.say(f"The fuzzy path became clear again.")
    _update_meme(traveler, "pride", 1.0)
    _update_meme(companion, "relief", 1.0)
    world.say(f"In the end, {traveler.label} reached {setting.place}, and the trip felt easier because {traveler.label} had solved the problem instead of panicking.")
    world.say(f"{traveler.label} smiled at the quiet sky and felt a little bigger inside.")
    return world


def story_intro(world: World) -> str:
    traveler = world.facts["traveler"]
    setting = world.setting
    return f"{traveler.label} was on a {setting.travel_kind} to {setting.place}."


def tell(params: StoryParams) -> World:
    return build_world(params)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    traveler = f["traveler"]
    prob = f["problem"]
    tool = f["tool"]
    return [
        f"Write a short space-adventure story about {traveler.label} traveling through space and solving a problem with {tool.label}.",
        f"Tell a child-friendly story where a traveler on {world.setting.travel_kind} notices {prob.symptom} and thinks carefully before acting.",
        "Write a tiny science-fiction story with inner monologue, a travel problem, and a practical fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    traveler = f["traveler"]
    prob = f["problem"]
    tool = f["tool"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Where was {traveler.label} traveling?",
            answer=f"{traveler.label} was traveling through space toward {place}.",
        ),
        QAItem(
            question=f"What problem showed up during the trip?",
            answer=f"The problem was that {prob.verb}, and {prob.symptom}.",
        ),
        QAItem(
            question=f"What helped {traveler.label} fix the trouble?",
            answer=f"{traveler.label} used {tool.phrase} to solve the problem.",
        ),
        QAItem(
            question=f"How did {traveler.label} deal with the problem inside {traveler.pronoun('possessive')} head?",
            answer=f"{traveler.label} stayed calm, thought step by step, and used careful inner monologue to choose a fix.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the trip was back on track and {traveler.label} felt proud and relieved.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "fuel": [(
        "What does fuel do for a spaceship?",
        "Fuel gives a spaceship the energy it needs to move through space.",
    )],
    "door": [(
        "Why is a stuck door a problem on a ship?",
        "A stuck door can block the path, so people or cargo cannot move where they need to go.",
    )],
    "signal": [(
        "What is a signal in space travel?",
        "A signal is a message or connection that helps a ship know where it is or hear instructions.",
    )],
    "map": [(
        "What does a map help you do?",
        "A map helps you find your way from one place to another.",
    )],
    "space": [(
        "What is space like?",
        "Space is very big and dark, with stars, planets, and wide open distances.",
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    prob = world.facts["problem"]
    tool = world.facts["tool"]
    tags = {prob.meter, "space", "map" if prob.id == "lost_signal" else prob.id}
    if tool.id == "star_map":
        tags.add("signal")
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
traveler(T) :- person(T).
problem(P) :- issue(P).
tool(T) :- device(T).

needs_fix(T, P) :- traveler(T), problem(P), meter_of(P, M), has_meter(T, M), M >= 1.
can_fix(T, P) :- needs_fix(T, P), tool(Tool), fixes(Tool, P).

compatible_place(Place, Prob, Tool) :- setting(Place), afford(Place, Prob), fixes(Tool, Prob).
valid_story(Place, Prob, Tool) :- compatible_place(Place, Prob, Tool).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for prob in sorted(setting.afford):
            lines.append(asp.fact("afford", sid, prob))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("issue", pid))
        lines.append(asp.fact("meter_of", pid, prob.meter))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("device", tid))
        for prob in sorted(tool.fixes):
            lines.append(asp.fact("fixes", tid, prob))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space travel storyworld with problem solving and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["friend", "pilot", "mechanic"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.problem and args.tool and args.problem not in TOOLS[args.tool].fixes:
        raise StoryError("That tool does not solve that travel problem.")
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.problem is None or c[1] == args.problem)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, prob, tool = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_gendered_name(gender, rng)
    companion = args.companion or rng.choice(["friend", "pilot", "mechanic"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=prob, tool=tool, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="moon_lane", problem="low_fuel", tool="backup_fuel_cell", name="Ari", gender="girl", companion="pilot", trait="careful"),
    StoryParams(place="asteroid_gate", problem="stuck_door", tool="patch_kit", name="Kai", gender="boy", companion="mechanic", trait="clever"),
    StoryParams(place="ring_route", problem="lost_signal", tool="star_map", name="Luna", gender="girl", companion="friend", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
