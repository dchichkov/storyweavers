#!/usr/bin/env python3
"""
storyworlds/worlds/satellite_sound_effects_suspense_superhero_story.py
======================================================================

A small superhero story world about a satellite, a looming problem, and a
last-second rescue with sound effects and suspense.

Premise:
- A hero guards a city from trouble in the sky.
- A satellite is the important thing to protect.
- A villainous jammer or storm can throw the satellite off course.
- The hero hears clues, acts fast, and saves the day.

The model is intentionally tiny and constraint-checked:
- If the threat does not genuinely endanger the satellite, no story is generated.
- If the hero's tool cannot plausibly solve the problem, the combination is rejected.
- The story text is driven by state changes in the simulated world, including
  suspense, sound effects, and a concrete ending image proving what changed.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    worn_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Threat:
    id: str
    label: str
    action: str
    clue: str
    sound: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    action: str
    sound: str
    guards: set[str]
    fixes: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "rooftop": Setting(place="the rooftop", indoors=False, affords={"fly", "scan", "aim"}),
    "city_harbor": Setting(place="the city harbor", indoors=False, affords={"fly", "scan", "aim"}),
    "tower_lab": Setting(place="the tower lab", indoors=True, affords={"scan", "repair", "aim"}),
}

HERO_NAMES = ["Nova", "Flash", "Astra", "Comet", "Mira", "Bolt"]
SIDEKICK_NAMES = ["Pip", "Tess", "Juno", "Rex", "Milo"]
VILLAINS = ["Doctor Static", "The Whisper", "Captain Crackle"]
HEROTYPES = ["girl", "boy"]

THREATS = {
    "jammer": Threat(
        id="jammer",
        label="a jammer",
        action="jam the satellite signal",
        clue="a tinny buzz in the headset",
        sound="BZZZT!",
        danger="its signal would go fuzzy",
        tags={"satellite", "signal", "sound"},
    ),
    "storm": Threat(
        id="storm",
        label="a storm cloud",
        action="push the satellite off course",
        clue="a rolling rumble in the clouds",
        sound="KRAAASH!",
        danger="its orbit would wobble",
        tags={"satellite", "orbit", "storm"},
    ),
    "laser": Threat(
        id="laser",
        label="a sky laser",
        action="overheat the satellite panels",
        clue="a sharp red blink on the horizon",
        sound="ZZZIIIP!",
        danger="its panels would start to fail",
        tags={"satellite", "heat", "light"},
    ),
}

TOOLS = {
    "shield": Tool(
        id="shield",
        label="a shimmer shield",
        action="cover the satellite",
        sound="WHOOOM!",
        guards={"jammer", "storm", "laser"},
        fixes={"signal", "orbit", "heat"},
        tags={"shield", "satellite"},
    ),
    "tether": Tool(
        id="tether",
        label="a magnetic tether",
        action="pull the satellite back into place",
        sound="CLANK!",
        guards={"storm"},
        fixes={"orbit"},
        tags={"tether", "satellite"},
    ),
    "filter": Tool(
        id="filter",
        label="a signal filter",
        action="clean up the signal",
        sound="BEEP-BEEP!",
        guards={"jammer"},
        fixes={"signal"},
        tags={"filter", "satellite"},
    ),
}

CURATED = [
    ("rooftop", "jammer", "shield"),
    ("city_harbor", "storm", "tether"),
    ("tower_lab", "laser", "shield"),
]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    threat: str
    tool: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    villain: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def threat_endangers_satellite(threat: Threat) -> bool:
    return "satellite" in threat.tags


def tool_can_fix(threat: Threat, tool: Tool) -> bool:
    if threat.id not in tool.guards:
        return False
    if threat.id == "jammer":
        return "signal" in tool.fixes
    if threat.id == "storm":
        return "orbit" in tool.fixes
    if threat.id == "laser":
        return "heat" in tool.fixes
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for threat_id, threat in THREATS.items():
            if not threat_endangers_satellite(threat):
                continue
            for tool_id, tool in TOOLS.items():
                if tool_can_fix(threat, tool):
                    combos.append((place, threat_id, tool_id))
    return combos


def explain_rejection(threat: Threat, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not plausibly solve {threat.label} in a way "
        f"that protects the satellite.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def predict(world: World, threat: Threat, tool: Tool) -> dict:
    sim = world.copy()
    satellite = sim.get("satellite")
    if threat.id == "jammer":
        satellite.meters["signal_risk"] += 1
    elif threat.id == "storm":
        satellite.meters["orbit_risk"] += 1
    elif threat.id == "laser":
        satellite.meters["heat_risk"] += 1
    fixed = tool_can_fix(threat, tool)
    return {
        "at_risk": any(v >= 1 for v in satellite.meters.values()),
        "fixed": fixed,
    }


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    threat = THREATS[params.threat]
    tool = TOOLS[params.tool]
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="child", label=params.sidekick_name))
    villain = world.add(Entity(id="villain", kind="character", type="adult", label=params.villain))
    satellite = world.add(Entity(
        id="satellite",
        kind="thing",
        type="satellite",
        label="satellite",
        phrase="the city satellite",
        caretaker="hero",
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type=tool.id,
        label=tool.label,
        phrase=tool.label,
        owner="hero",
    ))

    # Act 1
    world.say(f"{hero.label} was the city's superhero, and {satellite.label} glittered high above the streets.")
    world.say(f"{sidekick.label} listened for trouble, because the sky could turn strange in a blink.")
    world.say(f"{hero.label} loved calm mornings, but {villain.label} was never far from a sneaky plan.")

    # Act 2
    world.para()
    if setting.indoors:
        world.say(f"Inside {setting.place}, the screens went quiet, then one monitor flashed a warning.")
    else:
        world.say(f"Out at {setting.place}, the wind held still for one scary second.")
    world.say(f"{threat.sound} went the warning as {threat.clue} drifted through the air.")
    satellite.memes["suspense"] = 1
    satellite.meters["risk"] = 1
    world.say(f"{villain.label} tried to {threat.action}, and that could make {satellite.label} {threat.danger}.")
    world.say(f"{hero.label} narrowed their eyes and whispered, 'Not tonight.'")

    # Act 3
    world.para()
    if tool.id == "shield":
        world.say(f"{tool.sound} went the {tool.label} as {hero.label} threw it over the glowing satellite feed.")
        satellite.meters["signal_risk"] = 0
        satellite.meters["orbit_risk"] = 0
        satellite.meters["heat_risk"] = 0
        satellite.memes["suspense"] = 0
        world.say(f"The screen steadied, the lines stopped shaking, and {satellite.label} shone steady again.")
    elif tool.id == "tether":
        world.say(f"{tool.sound} went the {tool.label} as {hero.label} snapped it into a sky hook.")
        satellite.meters["orbit_risk"] = 0
        satellite.memes["suspense"] = 0
        world.say(f"The satellite eased back into place with a smooth little hum.")
    elif tool.id == "filter":
        world.say(f"{tool.sound} went the {tool.label} as {sidekick.label} tuned the signal by the second.")
        satellite.meters["signal_risk"] = 0
        satellite.memes["suspense"] = 0
        world.say(f"The static melted away, and the message came through clear and bright.")

    world.say(f"At the end, {satellite.label} blinked safely overhead, and the hero's cape snapped in the quiet air.")

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        villain=villain,
        satellite=satellite,
        threat=threat,
        tool=tool,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child that includes the word "satellite".',
        f"Tell a suspenseful superhero tale where {f['hero'].label} must stop {f['villain'].label} from {f['threat'].action}.",
        f"Write a child-friendly story with sound effects like {f['threat'].sound} and a brave rescue using {f['tool'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    sidekick = f["sidekick"].label
    villain = f["villain"].label
    threat = f["threat"]
    tool = f["tool"]
    sat = f["satellite"].label
    return [
        QAItem(
            question=f"Who was trying to cause trouble for the {sat}?",
            answer=f"{villain} was trying to cause trouble, and {hero} had to stop it.",
        ),
        QAItem(
            question=f"What sound warned that something was wrong?",
            answer=f"The story used the sound {threat.sound} to show the danger coming near the satellite.",
        ),
        QAItem(
            question=f"How did {hero} help the {sat} in the end?",
            answer=f"{hero} used {tool.label} so the danger could not hurt the satellite anymore.",
        ),
        QAItem(
            question=f"Who listened for trouble with {hero}?",
            answer=f"{sidekick} listened for trouble and stayed close while the hero saved the day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a satellite?",
            answer="A satellite is an object that goes around a planet and can carry signals, pictures, or other helpful information.",
        ),
        QAItem(
            question="Why do heroes use tools in a rescue?",
            answer="Heroes use tools so they can solve a problem safely and stop danger without making things worse.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important is about to happen and you want to know what comes next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
threat(T) :- threat_name(T).
tool(U) :- tool_name(U).

endangers(T) :- threat_tag(T, satellite).

fixes(U, T) :- tool_fixes(U, T), tool_guards(U, T).

valid_combo(P, T, U) :- place(P), threat(T), tool(U), endangers(T), fixes(U, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for t in THREATS.values():
        lines.append(asp.fact("threat_name", t.id))
        for tag in sorted(t.tags):
            lines.append(asp.fact("threat_tag", t.id, tag))
    for u in TOOLS.values():
        lines.append(asp.fact("tool_name", u.id))
        for g in sorted(u.guards):
            lines.append(asp.fact("tool_guards", u.id, g))
        for f in sorted(u.fixes):
            lines.append(asp.fact("tool_fixes", u.id, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python on {len(py)} combos.")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with satellite suspense and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--gender", choices=HEROTYPES)
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.threat is None or c[1] == args.threat)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, threat_id, tool_id = rng.choice(sorted(filtered))
    hero_type = args.gender or rng.choice(HEROTYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick or rng.choice(SIDEKICK_NAMES)
    villain = args.villain or rng.choice(VILLAINS)
    return StoryParams(
        place=place,
        threat=threat_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        villain=villain,
    )


def generate(params: StoryParams) -> StorySample:
    threat = THREATS[params.threat]
    tool = TOOLS[params.tool]
    if not (threat_endangers_satellite(threat) and tool_can_fix(threat, tool)):
        raise StoryError(explain_rejection(threat, tool))
    world = build_world(params)
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
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_combo/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, threat, tool in CURATED:
            params = StoryParams(
                place=place,
                threat=threat,
                tool=tool,
                hero_name="Nova",
                hero_type="girl",
                sidekick_name="Pip",
                villain="Doctor Static",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.threat} with {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
