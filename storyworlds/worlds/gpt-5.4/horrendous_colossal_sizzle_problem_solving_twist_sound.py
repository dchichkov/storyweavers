#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/horrendous_colossal_sizzle_problem_solving_twist_sound.py
====================================================================================

A standalone story world for a tiny Space Adventure tale built from the seed
words "horrendous", "colossal", and "sizzle", with Problem Solving, a Twist,
and Sound Effects.

Premise
-------
A child explorer and a small robot reach a beacon station in a faraway place.
Something at the beacon has gone wrong. The child hears a scary noise and sees
a huge shadow, so the trouble feels like a horrendous space-monster problem.
But the world model keeps the story honest: the beacon has a concrete fault,
only the right repair tool can fix it, and once the repair works the twist is
revealed -- the "monster" was a helpful rescue device or machine all along.

Run it
------
    python storyworlds/worlds/gpt-5.4/horrendous_colossal_sizzle_problem_solving_twist_sound.py
    python storyworlds/worlds/gpt-5.4/horrendous_colossal_sizzle_problem_solving_twist_sound.py --place ice_ring --fault frozen_switch --tool warm_patch
    python storyworlds/worlds/gpt-5.4/horrendous_colossal_sizzle_problem_solving_twist_sound.py --fault dust_panel --tool warm_patch
    python storyworlds/worlds/gpt-5.4/horrendous_colossal_sizzle_problem_solving_twist_sound.py --all
    python storyworlds/worlds/gpt-5.4/horrendous_colossal_sizzle_problem_solving_twist_sound.py --qa --json
    python storyworlds/worlds/gpt-5.4/horrendous_colossal_sizzle_problem_solving_twist_sound.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    sky: str
    ground: str
    affords: set[str]
    shadow_label: str
    shadow_truth: str
    launch_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fault:
    id: str
    label: str
    problem_line: str
    symptom_sound: str
    cause_text: str
    repair_need: str
    repair_result: str
    hot: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fixes: set[str]
    action_text: str
    repair_sound: str
    safe_result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tool_fits(fault: Fault, tool: Tool) -> bool:
    return fault.id in tool.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        for fid in sorted(place.affords):
            fault = FAULTS[fid]
            for tid, tool in TOOLS.items():
                if tool_fits(fault, tool):
                    combos.append((pid, fid, tid))
    return sorted(combos)


def explain_rejection(place: Optional[Place], fault: Fault, tool: Tool) -> str:
    if place is not None and fault.id not in place.affords:
        choices = ", ".join(sorted(place.affords))
        return (
            f"(No story: {place.name} does not use the '{fault.id}' beacon problem here. "
            f"Try one of: {choices}.)"
        )
    return (
        f"(No story: {tool.label} does not honestly fix {fault.label}. "
        f"This world only allows repair tools that match the real problem.)"
    )


def introduce(world: World, hero: Entity, bot: Entity, place: Place) -> None:
    hero.memes["wonder"] += 1
    bot.memes["helpfulness"] += 1
    world.say(
        f"{hero.id} and {bot.id} bounced out of their little shuttle at {place.name}. "
        f"Above them, {place.sky}. Under their boots, {place.ground}."
    )
    world.say(
        f"They had come to wake the old beacon tower, a silver post that blinked to lost ships."
    )


def discover_problem(world: World, hero: Entity, bot: Entity, fault: Fault) -> None:
    beacon = world.get("beacon")
    beacon.meters["broken"] += 1
    beacon.meters["signal"] = 0.0
    if fault.hot:
        beacon.meters["heat"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"But when {hero.id} pressed the blue start button, {fault.problem_line}"
    )
    world.say(
        f'"{fault.symptom_sound}!" went the tower. {bot.id} tilted {bot.pronoun("possessive")} round head.'
    )


def predict_and_fear(world: World, hero: Entity, bot: Entity, place: Place, fault: Fault) -> None:
    hero.memes["worry"] += 1
    world.facts["monster_guess"] = True
    world.say(
        f"Then a shadow slid across the ground -- so big it looked colossal. "
        f"{place.launch_sound} echoed behind a ridge."
    )
    world.say(
        f'"That is a horrendous space monster," {hero.id} whispered.'
    )
    world.say(
        f'But {bot.id} beeped softly. "{fault.cause_text}. We can solve one thing at a time."'
    )


def inspect(world: World, hero: Entity, bot: Entity, fault: Fault, tool: Tool) -> None:
    hero.memes["courage"] += 1
    bot.memes["trust"] += 1
    world.say(
        f"{hero.id} knelt beside the beacon and looked carefully. "
        f"{bot.id} pointed a tiny lamp at {fault.repair_need}."
    )
    world.say(
        f'"Hand me {tool.phrase}," {hero.id} said. {bot.id} rolled it over at once.'
    )


def repair(world: World, hero: Entity, fault: Fault, tool: Tool) -> None:
    beacon = world.get("beacon")
    beacon.meters["broken"] = 0.0
    beacon.meters["signal"] += 1
    beacon.meters["fixed"] += 1
    if fault.hot:
        beacon.meters["heat"] = 0.0
    hero.memes["courage"] += 1
    hero.memes["relief"] += 1
    world.facts["repair_sound"] = tool.repair_sound
    world.say(
        f"{tool.action_text} {tool.repair_sound} The little sound skipped through the cold air."
    )
    world.say(
        f"At once, {fault.repair_result} {tool.safe_result}"
    )


def reveal_twist(world: World, hero: Entity, bot: Entity, place: Place) -> None:
    beacon = world.get("beacon")
    beacon.meters["truth_light"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["wonder"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"The beacon flashed bright gold across the dark rocks. "
        f"In that light, the colossal shadow stopped looking like teeth and claws."
    )
    world.say(
        f"It was only {place.shadow_truth}. {place.shadow_label.capitalize()} had made the booming sound when it opened."
    )
    world.say(
        f'{hero.id} laughed. "So the horrendous monster was helping us all along!"'
    )


def ending(world: World, hero: Entity, bot: Entity, place: Place) -> None:
    world.say(
        f"Soon the tower winked to the sky again, and friendly ships could find {place.name}."
    )
    world.say(
        f"{hero.id} and {bot.id} stood in the glow, small under the stars but brave inside."
    )


def tell(
    place: Place,
    fault: Fault,
    tool: Tool,
    hero_name: str = "Nia",
    hero_type: str = "girl",
    bot_name: str = "Pip",
) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    bot = world.add(Entity(id=bot_name, kind="character", type="robot", role="helper"))
    beacon = world.add(Entity(id="beacon", kind="thing", type="beacon", label="beacon tower"))

    introduce(world, hero, bot, place)
    world.para()
    discover_problem(world, hero, bot, fault)
    predict_and_fear(world, hero, bot, place, fault)
    world.para()
    inspect(world, hero, bot, fault, tool)
    repair(world, hero, fault, tool)
    world.para()
    reveal_twist(world, hero, bot, place)
    ending(world, hero, bot, place)

    world.facts.update(
        hero=hero,
        bot=bot,
        beacon=beacon,
        place=place,
        fault=fault,
        tool=tool,
        solved=beacon.meters["fixed"] >= THRESHOLD,
        twist_revealed=beacon.meters["truth_light"] >= THRESHOLD,
        scary_sound=place.launch_sound,
    )
    return world


PLACES = {
    "moon": Place(
        "moon",
        "the Moon Crater Plain",
        "the stars looked close enough to tap",
        "gray dust puffed around every hop",
        {"dust_panel", "loose_cable"},
        "rescue balloon",
        "the beacon's folded rescue balloon, rising round and silver behind the ridge",
        '"WHOOOMP!"',
        tags={"space", "moon", "beacon"},
    ),
    "red_dunes": Place(
        "red_dunes",
        "the Red Dune Station",
        "a red sky glimmered behind tiny moons",
        "soft rust-colored sand curled around the tower legs",
        {"dust_panel", "loose_cable"},
        "solar sail",
        "the station's giant solar sail, snapping open to catch light",
        '"FWAPP!"',
        tags={"space", "planet", "beacon"},
    ),
    "ice_ring": Place(
        "ice_ring",
        "the Ice Ring Outpost",
        "blue stars shivered over a white arch of ice",
        "the ground sparkled like sugar and glass",
        {"frozen_switch", "loose_cable"},
        "mapping kite",
        "the outpost's mapping kite, unfolding in the wind like a silver wing",
        '"BROOONG!"',
        tags={"space", "ice", "beacon"},
    ),
}

FAULTS = {
    "dust_panel": Fault(
        "dust_panel",
        "dusty solar wings",
        "red dust covered the beacon's solar wings, and the light blinked weaker and weaker",
        "Kzzzt",
        "the beacon cannot drink sunlight through all that dust",
        "the dusty solar wings",
        "the clean panels caught the light again",
        hot=False,
        tags={"dust", "solar", "problem"},
    ),
    "loose_cable": Fault(
        "loose_cable",
        "a loose spark cable",
        "one spark cable hung crooked, and a bright line kept jumping from metal to metal",
        "Bzzap",
        "the power cable is loose, and loose power makes the tower jumpy",
        "the loose spark cable",
        "the wild spark stopped dancing",
        hot=True,
        tags={"cable", "spark", "problem"},
    ),
    "frozen_switch": Fault(
        "frozen_switch",
        "a frozen switch",
        "a clear shell of ice trapped the beacon's start switch, and the tower would not wake",
        "Tik-tik-tik",
        "the start switch is frozen shut, so the tower cannot move",
        "the frozen start switch",
        "the ice slid away from the switch",
        hot=False,
        tags={"ice", "switch", "problem"},
    ),
}

TOOLS = {
    "brush": Tool(
        "brush",
        "brush",
        "the small moon brush",
        {"dust_panel"},
        "Nia swept the dust away in shining arcs.",
        '"Swish-swish!"',
        "The tower stopped coughing and began to hum.",
        tags={"brush", "cleaning"},
    ),
    "clip": Tool(
        "clip",
        "star clip",
        "the bright star clip",
        {"loose_cable"},
        "Nia snapped the cable into place with the star clip.",
        '"Click! Sizzle!"',
        "The hot spark vanished, and the metal cooled down.",
        tags={"clip", "repair"},
    ),
    "warm_patch": Tool(
        "warm_patch",
        "warm patch",
        "the orange warm patch",
        {"frozen_switch"},
        "Nia pressed the warm patch gently against the ice.",
        '"Sizzle!"',
        "A tiny river of melt-water ran down, and the switch sprang free.",
        tags={"warm", "repair"},
    ),
}

GIRL_NAMES = ["Nia", "Mira", "Zuri", "Tala", "Luma", "Ava"]
BOY_NAMES = ["Orin", "Milo", "Tao", "Finn", "Eli", "Noah"]
BOT_NAMES = ["Pip", "Dot", "Bloop", "Zing", "Rori"]


@dataclass
class StoryParams:
    place: str
    fault: str
    tool: str
    hero_name: str
    hero_type: str
    bot_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "beacon": [
        (
            "What does a beacon do?",
            "A beacon sends out light or signals so travelers can find the right place. In space stories, a beacon helps ships know where to go.",
        )
    ],
    "solar": [
        (
            "What is a solar panel?",
            "A solar panel catches light and turns it into power. If it gets covered with dust, it cannot do its job as well.",
        )
    ],
    "cable": [
        (
            "Why is a loose cable a problem?",
            "A loose cable cannot carry power safely. It can make sparks, flickers, and machines that do not work the right way.",
        )
    ],
    "ice": [
        (
            "Why can ice stop a switch from moving?",
            "Ice can trap a button or switch in place. Until the ice melts, the part cannot move the way it should.",
        )
    ],
    "brush": [
        (
            "What is a brush good for in a machine problem?",
            "A brush can sweep away dust and grit from a surface. That helps when the real problem is dirt blocking something important.",
        )
    ],
    "clip": [
        (
            "What does a clip do?",
            "A clip can hold something in the right place. In a repair, it can keep a cable from slipping loose again.",
        )
    ],
    "warm": [
        (
            "What does warmth do to ice?",
            "Warmth melts ice into water. That is why a warm patch can free something that is frozen shut.",
        )
    ],
    "moon": [
        (
            "What is the Moon like in stories?",
            "The Moon is often shown as dusty, rocky, and bright under the stars. It feels quiet, so every little sound seems bigger.",
        )
    ],
    "planet": [
        (
            "What is a dune?",
            "A dune is a hill of loose sand. Wind can move sand around and pile it into soft ridges.",
        )
    ],
    "space": [
        (
            "Why do sounds feel dramatic in a space adventure story?",
            "Story sounds help readers feel surprise and danger. A loud 'WHOOOMP!' or 'Sizzle!' can make a small problem feel huge until the characters understand it.",
        )
    ],
}
KNOWLEDGE_ORDER = ["beacon", "solar", "cable", "ice", "brush", "clip", "warm", "moon", "planet", "space"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    fault = f["fault"]
    tool = f["tool"]
    return [
        'Write a short Space Adventure for a 3-to-5-year-old that includes the words "horrendous", "colossal", and "sizzle".',
        f"Tell a gentle problem-solving story where {hero.id} repairs a beacon at {place.name} after a {fault.label} causes trouble.",
        f"Write a space story with sound effects, a scary-looking twist, and a happy reveal where {tool.label} solves the real problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    bot = f["bot"]
    place = f["place"]
    fault = f["fault"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young space explorer, and {bot.id}, the little helper robot. Together they went to wake the beacon at {place.name}.",
        ),
        (
            "What problem did they find at the beacon?",
            f"They found {fault.label}. That stopped the beacon from working the right way, so the tower made a worrying sound instead of shining clearly.",
        ),
        (
            f"Why did {hero.id} think something scary was nearby?",
            f"{hero.id} heard {place.launch_sound} and saw a shadow so big it looked colossal. Because the beacon was already broken, the noise felt even more frightening and {hero.pronoun()} guessed it might be a horrendous monster.",
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} used {tool.phrase} on {fault.repair_need}. That worked because {tool.label} matches the real problem instead of only looking impressive.",
        ),
    ]
    if f["solved"]:
        qa.append(
            (
                "What was the twist at the end?",
                f"The huge shadow was not a monster at all. It was {place.shadow_truth}, and the beacon light helped {hero.id} see the truth.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The beacon worked again and friendly ships could find the outpost. {hero.id} ended the story feeling brave because {hero.pronoun()} stayed calm, solved the real problem, and learned the scary shape was only something helpful.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"beacon", "space"}
    place = world.facts["place"]
    fault = world.facts["fault"]
    tool = world.facts["tool"]
    if place.id == "moon":
        tags.add("moon")
    if place.id == "red_dunes":
        tags.add("planet")
    if fault.id == "dust_panel":
        tags.add("solar")
    if fault.id == "loose_cable":
        tags.add("cable")
    if fault.id == "frozen_switch":
        tags.add("ice")
    if tool.id == "brush":
        tags.add("brush")
    if tool.id == "clip":
        tags.add("clip")
    if tool.id == "warm_patch":
        tags.add("warm")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon", "dust_panel", "brush", "Nia", "girl", "Pip"),
    StoryParams("red_dunes", "loose_cable", "clip", "Milo", "boy", "Dot"),
    StoryParams("ice_ring", "frozen_switch", "warm_patch", "Tala", "girl", "Bloop"),
    StoryParams("ice_ring", "loose_cable", "clip", "Orin", "boy", "Zing"),
]


ASP_RULES = r"""
compatible_tool(F,T) :- tool(T), fixes(T,F).
valid(P,F,T) :- place(P), fault(F), tool(T), affords(P,F), compatible_tool(F,T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for fid in sorted(place.affords):
            lines.append(asp.fact("affords", pid, fid))
    for fid in FAULTS:
        lines.append(asp.fact("fault", fid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for fid in sorted(tool.fixes):
            lines.append(asp.fact("fixes", tid, fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "horrendous" not in sample.story or "colossal" not in sample.story:
            raise StoryError("(Verify: smoke test story did not render expected seeded words.)")
        print("OK: smoke-test story generation worked.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure story world: a child repairs a beacon, solves a problem, and discovers a surprising twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--fault", choices=FAULTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero", help="override hero name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--bot", help="override robot name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, fault, tool) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.fault:
        place = PLACES[args.place]
        fault = FAULTS[args.fault]
        if fault.id not in place.affords:
            tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
            raise StoryError(explain_rejection(place, fault, tool))
    if args.fault and args.tool:
        fault = FAULTS[args.fault]
        tool = TOOLS[args.tool]
        if not tool_fits(fault, tool):
            place = PLACES[args.place] if args.place else None
            raise StoryError(explain_rejection(place, fault, tool))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.fault is None or c[1] == args.fault)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, fault_id, tool_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    bot_name = args.bot or rng.choice(BOT_NAMES)
    return StoryParams(place_id, fault_id, tool_id, hero_name, gender, bot_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        FAULTS[params.fault],
        TOOLS[params.tool],
        params.hero_name,
        params.hero_type,
        params.bot_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, fault, tool) combos:\n")
        for place, fault, tool in combos:
            print(f"  {place:10} {fault:14} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.place} / {p.fault} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
