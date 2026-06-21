#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/darned_grotty_problem_solving_humor_space_adventure.py
======================================================================================

A small standalone storyworld for a space-adventure flavored problem-solving
tale with a comic, child-facing tone. The seed words are "darned" and "grotty";
the world uses them in a natural way, while the engine model drives the story.

Premise
-------
A tiny crew is stranded in a grotty little moon tunnel with a broken rover,
a stubborn door, and one useful fix hidden in the mess. The crew must laugh a
little, think clearly, and solve the problem together before they can fly on.

This world is intentionally compact:
- typed entities with physical meters and emotional memes
- a forward, state-driven causal engine
- a reasonableness gate for plausible setups
- QA generation from world state, not from rendered English
- a Python/ASP twin for the validity checks

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/darned_grotty_problem_solving_humor_space_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/darned_grotty_problem_solving_humor_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/darned_grotty_problem_solving_humor_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/darned_grotty_problem_solving_humor_space_adventure.py --trace
    python storyworlds/worlds/gpt-5.4-mini/darned_grotty_problem_solving_humor_space_adventure.py --verify
    python storyworlds/worlds/gpt-5.4-mini/darned_grotty_problem_solving_humor_space_adventure.py --show-asp
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
SENSE_MIN = 2
BRAVERY_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    fixable: bool = False
    dusty: bool = False
    sticky: bool = False
    noisy: bool = False
    gives_tool: bool = False
    can_open: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class ShipSetting:
    id: str
    place: str
    style_line: str
    view: str
    problem_noun: str
    ending_image: str


@dataclass
class Problem:
    id: str
    mess: str
    source: str
    clue: str
    nuisance: str
    fix_action: str
    fix_result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    effect: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["stuck"] >= THRESHOLD and ("noise", e.id) not in world.fired:
            world.fired.add(("noise", e.id))
            for char in world.entities.values():
                if char.kind == "character":
                    char.memes["alarm"] += 1
            out.append("__alarm__")
    return out


def _r_gross(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["gross"] >= THRESHOLD and ("gross", e.id) not in world.fired:
            world.fired.add(("gross", e.id))
            for char in world.entities.values():
                if char.kind == "character":
                    char.memes["grimace"] += 1
            out.append("__gross__")
    return out


CAUSAL_RULES = [Rule("noise", "social", _r_noise), Rule("gross", "physical", _r_gross)]


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


def hazard_at_risk(problem: Problem, setting: ShipSetting) -> bool:
    return problem.id in PROBLEMS and setting.id in VALID_SETTINGS


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for sid in SETTINGS:
        for pid in PROBLEMS:
            for rid in RESPONSES:
                if problem_is_reasonable(PROBLEMS[pid], SETTINGS[sid], RESPONSES[rid]):
                    combos.append((sid, pid, rid))
    return combos


def problem_is_reasonable(problem: Problem, setting: ShipSetting, response: Response) -> bool:
    return setting.id in {"moon_tunnel", "junk_orbit", "dock_bay"} and response.sense >= SENSE_MIN and problem.id in PROBLEMS


def predict_fix(world: World, tool: Tool, problem: Problem) -> dict:
    sim = world.copy()
    _apply_tool(sim, sim.get("tool"), problem, narrate=False)
    return {"resolved": sim.get("problem").meters["fixed"] >= THRESHOLD, "humor": sum(e.memes["laugh"] for e in sim.entities.values())}


def _apply_tool(world: World, tool: Entity, problem: Problem, narrate: bool = True) -> None:
    world.get("problem").meters["fixed"] += 1
    world.get("problem").meters["gross"] = 0
    world.get("door").meters["stuck"] = 0
    propagate(world, narrate=narrate)


def setup(world: World, setting: ShipSetting, crew1: Entity, crew2: Entity) -> None:
    crew1.memes["curiosity"] += 1
    crew2.memes["curiosity"] += 1
    world.say(f"On {setting.place}, {crew1.id} and {crew2.id} found themselves in {setting.view}.")
    world.say(setting.style_line)
    world.say(f"The trouble was {setting.problem_noun}, and it looked {setting.id.replace('_', ' ')}-grotty.")


def clue(world: World, problem: Problem, crew2: Entity) -> None:
    crew2.memes["worry"] += 1
    world.say(f'{crew2.id} squinted at the mess. "This is a darned {problem.mess} problem," {crew2.pronoun()} said.')
    world.say(f"But {problem.clue}.")


def mismatch(world: World, crew1: Entity) -> None:
    crew1.memes["grin"] += 1
    world.say(f'{crew1.id} tried a very heroic pose. It did not help. The pose was excellent, though.')


def solve(world: World, crew1: Entity, crew2: Entity, tool: Tool, problem: Problem, setting: ShipSetting) -> None:
    crew1.memes["laugh"] += 1
    crew2.memes["laugh"] += 1
    body = tool.text.replace("{problem}", problem.id)
    world.say(f"Then {crew1.id} had an idea. {crew1.pronoun().capitalize()} {body}.")
    world.say(f"{crew2.id} snorted. \"That is the least gloomy rescue I have ever seen,\" {crew2.pronoun()} said.")
    _apply_tool(world, world.get("tool"), problem)
    world.say(f"The {problem.nuisance} stopped at once, and {problem.fix_result}.")
    world.say(f"At last, they could drift onward through {setting.ending_image}.")


def fail(world: World, crew1: Entity, crew2: Entity, response: Response, problem: Problem) -> None:
    world.say(f"{crew1.id} tried the plan, but {response.fail}.")
    world.say(f"{crew2.id} groaned. \"Well, that was officially grotty,\" {crew2.pronoun()} said.")
    world.say("The crew had to call for a tow before the ship could move again.")


SETTINGS = {
    "moon_tunnel": ShipSetting(
        id="moon_tunnel",
        place="the Moon Tunnel",
        style_line="A silver rover sat beside a blinking panel, and the floor was littered with dusty bolts and wobbling snack wrappers.",
        view="a narrow path under the moon",
        problem_noun="a grotty door jam",
        ending_image="a bright line of stars and the rover's little tail-lights",
    ),
    "junk_orbit": ShipSetting(
        id="junk_orbit",
        place="Junk Orbit",
        style_line="Broken satellites drifted like sleepy fish, and a lonely wrench spun slowly past the window.",
        view="a ring of floating scrap",
        problem_noun="a grotty fuel leak",
        ending_image="clean orbit and tidy engine hums",
    ),
    "dock_bay": ShipSetting(
        id="dock_bay",
        place="Dock Bay Nine",
        style_line="The dock smelled like metal soup, and a crane kept squeaking like it had a joke stuck in its throat.",
        view="a busy repair bay",
        problem_noun="a grotty cargo latch",
        ending_image="a gleaming hangar door and one happy launch lane",
    ),
}

PROBLEMS = {
    "door_jam": Problem(
        id="door_jam",
        mess="stuck",
        source="dust",
        clue="the jammed door was stuck because a pile of dust had packed into the hinge",
        nuisance="the stubborn door",
        fix_action="brush out the hinge and use the magnet key",
        fix_result="the door swung open with a cheerful squeak",
        tags={"dust", "door"},
    ),
    "fuel_leak": Problem(
        id="fuel_leak",
        mess="leaky",
        source="goo",
        clue="the fuel line had a tiny split, and a clamp could squeeze it shut",
        nuisance="the leaking tank",
        fix_action="snap on the clamp and wipe away the spill",
        fix_result="the tank stopped leaking and the gauge blinked green",
        tags={"fuel", "leak"},
    ),
    "cargo_latch": Problem(
        id="cargo_latch",
        mess="stuck",
        source="grit",
        clue="a pebble had trapped the latch, and a thin tool could nudge it free",
        nuisance="the jammed cargo hatch",
        fix_action="wiggle the pebble loose and tap the latch",
        fix_result="the hatch popped open and the cargo trays stopped rattling",
        tags={"cargo", "latch"},
    ),
}

TOOLS = {
    "magnet_key": Tool(
        id="magnet_key", label="magnet key", phrase="a magnet key",
        use_line="held up the magnet key and gave the dusty hinge a tidy poke",
        effect="the dust clumped away from the hinge", power=2, tags={"door", "dust"},
    ),
    "clamp": Tool(
        id="clamp", label="clamp", phrase="a clamp",
        use_line="snapped on the clamp and squeezed the split line shut",
        effect="the fuel line pinched tight", power=2, tags={"fuel", "leak"},
    ),
    "nudge_tool": Tool(
        id="nudge_tool", label="nudge tool", phrase="a nudge tool",
        use_line="slid in the nudge tool and flicked the pebble free",
        effect="the latch sprang loose", power=2, tags={"cargo", "latch"},
    ),
    "bubble_patch": Tool(
        id="bubble_patch", label="bubble patch", phrase="a bubble patch",
        use_line="pressed on the bubble patch and smoothed the noisy leak",
        effect="the leak fizzled into silence", power=1, tags={"leak"},
    ),
}

RESPONSES = {
    "think": Response(
        id="think", sense=3, power=3,
        text="thought hard, noticed the clue, and used the right tool in the right place",
        fail="thought hard, but the thought did not get the door unstuck",
        qa_text="thought hard, noticed the clue, and used the right tool in the right place",
        tags={"problem", "thinking"},
    ),
    "laugh_and_fix": Response(
        id="laugh_and_fix", sense=3, power=3,
        text="laughed at the grotty mess, then used the right tool with a careful grin",
        fail="laughed at the grotty mess, but the joke bounced off the broken part",
        qa_text="laughed at the grotty mess, then used the right tool with a careful grin",
        tags={"humor", "problem"},
    ),
    "tap": Response(
        id="tap", sense=2, power=2,
        text="tapped the jam once and gave it a tiny, determined nudge",
        fail="tapped the jam, but it stayed stuck and frowned back",
        qa_text="tapped the jam once and gave it a tiny, determined nudge",
        tags={"problem"},
    ),
    "spray_water": Response(
        id="spray_water", sense=1, power=1,
        text="sprayed water everywhere, which only made the panel sulk",
        fail="sprayed water everywhere, which only made the panel sulk",
        qa_text="sprayed water everywhere, which only made the panel sulk",
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Nova", "Zuri", "Mina", "Pip", "Luna"]
BOY_NAMES = ["Rex", "Toby", "Ari", "Jett", "Milo"]
TRAITS = ["brave", "curious", "quick-thinking", "cheerful", "sensible"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    problem = f["problem_cfg"]
    hero = f["hero"]
    helper = f["helper"]
    return [
        f'Write a space adventure story for a 3-to-5-year-old that includes the words "darned" and "grotty".',
        f"Tell a funny spaceship repair story where {hero.id} and {helper.id} face {setting.problem_noun} and solve it by thinking, not panicking.",
        f"Write a child-friendly moon story where the crew laughs at a grotty problem, finds a clue, and uses {problem.fix_action} to move on.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    setting = f["setting"]
    problem = f["problem_cfg"]
    tool = f["tool_cfg"]
    response = f["response_cfg"]
    qa: list[QAItem] = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {helper.id}, two crew members trying to fix a space problem together. They solve it by staying calm and paying attention to the clue.",
        ),
        QAItem(
            question="What was wrong with the ship or station?",
            answer=f"There was {setting.problem_noun}, and it turned the space trip into a grotty little puzzle. The problem came from {problem.clue}.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used {tool.phrase} and followed the clue instead of guessing. That let them {problem.fix_action}, so the broken part started working again.",
        ),
    ]
    if f.get("solved"):
        qa.append(
            QAItem(
                question=f"Why was {helper.id} laughing near the end?",
                answer=f"{helper.id} was laughing because the fix worked and the situation finally felt silly instead of scary. The crew could see that a clever idea was better than grumbling at the mess.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem_cfg"].tags)
    tags |= set(world.facts["tool_cfg"].tags)
    tags |= set(world.facts["response_cfg"].tags)
    out: list[QAItem] = []
    if "dust" in tags:
        out.append(QAItem("What is dust?", "Dust is made of tiny dry bits that collect on things and can make hinges or corners gritty. It is messy, but usually easy to brush away."))
    if "door" in tags:
        out.append(QAItem("What does a door do?", "A door opens and closes to let people and things pass through. If it gets stuck, something is blocking it."))
    if "fuel" in tags:
        out.append(QAItem("Why should fuel be handled carefully?", "Fuel helps machines run, but it can be dangerous if it leaks or spills. That is why grown-up care and the right fix matter."))
    if "problem" in tags:
        out.append(QAItem("What should you do when something breaks?", "Stop, look closely, and think about the clue. A good fix usually comes from noticing what is really wrong."))
    if "humor" in tags:
        out.append(QAItem("Can a problem story still be funny?", "Yes. A funny story can be about a messy thing, as long as the characters stay kind and solve it safely."))
    return out


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def tell(setting: ShipSetting, problem: Problem, tool: Tool, response: Response,
         hero_name: str, hero_gender: str, helper_name: str, helper_gender: str,
         trait: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["funny"]))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the ship"))
    door = world.add(Entity(id="door", kind="thing", type="door", label=problem.nuisance, stuck=True))
    prob = world.add(Entity(id="problem", kind="thing", type="problem", label=problem.id, fixable=True))
    t = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, gives_tool=True))
    world.facts["setting"] = setting
    world.facts["problem_cfg"] = problem
    world.facts["tool_cfg"] = tool
    world.facts["response_cfg"] = response
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["ship"] = ship
    world.facts["door"] = door
    world.facts["problem"] = prob
    world.facts["tool"] = t

    setup(world, setting, hero, helper)
    world.para()
    clue(world, problem, helper)
    mismatch(world, hero)
    hero.memes["determination"] += 1
    helper.memes["humor"] += 1
    world.para()

    if response.sense < SENSE_MIN:
        world.say(f"{hero.id} reached for a bad idea, but the ship politely refused to cooperate.")
        fail(world, hero, helper, response, problem)
        world.facts["solved"] = False
        return world

    # simple deterministic choice: use the registered tool
    _apply_tool(world, t, problem)
    solve(world, hero, helper, tool, problem, setting)
    world.facts["solved"] = True
    return world


CURATED = [
    StoryParams(setting="moon_tunnel", problem="door_jam", tool="magnet_key", response="think", hero="Nova", hero_gender="girl", helper="Rex", helper_gender="boy", trait="curious"),
    StoryParams(setting="junk_orbit", problem="fuel_leak", tool="clamp", response="laugh_and_fix", hero="Milo", hero_gender="boy", helper="Zuri", helper_gender="girl", trait="cheerful"),
    StoryParams(setting="dock_bay", problem="cargo_latch", tool="nudge_tool", response="tap", hero="Luna", hero_gender="girl", helper="Ari", helper_gender="boy", trait="sensible"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with humor and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{args.response}': it is too silly and not reasonable enough.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, response = rng.choice(sorted(combos))
    tool = args.tool or {
        "door_jam": "magnet_key",
        "fuel_leak": "clamp",
        "cargo_latch": "nudge_tool",
    }[problem]
    prob = PROBLEMS[problem]
    if tool not in TOOLS:
        raise StoryError("(Unknown tool.)")
    if tool == "bubble_patch" and problem != "fuel_leak":
        raise StoryError("This tool only makes sense for a leak.")
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, problem=problem, tool=tool, response=response, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS.get(params.setting, SETTINGS["moon_tunnel"]),
        PROBLEMS.get(params.problem, PROBLEMS["door_jam"]),
        TOOLS.get(params.tool, TOOLS["magnet_key"]),
        RESPONSES.get(params.response, RESPONSES["think"]),
        params.hero, params.hero_gender, params.helper, params.helper_gender, params.trait,
    )
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


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,P,R) :- setting(S), problem(P), response(R), sensible(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, tool=None, response=None, hero=None, hero_gender=None, helper=None, helper_gender=None, trait=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection(response: Response) -> str:
    return f"(Refusing response '{response.id}': it scores too low on common sense.)"


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
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
