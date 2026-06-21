#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/smarten_geology_narrative_teamwork_fairy_tale.py
=================================================================================

A standalone fairy-tale story world for a tiny geology-and-teamwork tale.

Premise:
- A young helper, a careful elder, and a talking stone-cartographer work together
  to "smarten" a rough path before a festival.
- Their geology lesson is physical: rock, soil, slope, pebble, and water all have
  measurable effects in the world model.
- The team must choose the right route and the right materials to keep a bridge
  safe before the story's closing image.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld
- typed entities with meters and memes
- reasonableness gate with inline ASP twin
- three Q&A sets grounded in world state
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
METER_KEYS = ("wet", "loose", "stable", "pulled", "built", "smartened", "sounded")
MEME_KEYS = ("curiosity", "care", "trust", "joy", "worry", "teamwork", "pride")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "mother"}
        male = {"boy", "man", "king", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    feature: str
    slope: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    risk: str
    source: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class TeamPlan:
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
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_rain(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["wet"] < THRESHOLD:
            continue
        sig = ("rain", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.type in {"bridge", "path", "stair"}:
            ent.meters["loose"] += 1
            ent.meters["stable"] = max(0.0, ent.meters["stable"] - 0.5)
            out.append(f"The wet stones grew slick beneath {ent.label_word}.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    helpers = [e for e in world.characters() if e.memes["teamwork"] >= THRESHOLD]
    if len(helpers) < 2:
        return out
    sig = ("teamwork", tuple(sorted(h.id for h in helpers)))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for h in helpers:
        h.memes["joy"] += 0.5
        h.memes["pride"] += 0.5
    out.append("Together, they felt strong enough to solve the hard thing.")
    return out


CAUSAL_RULES = [Rule("rain", _r_rain), Rule("teamwork", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(problem: Problem, setting: Setting) -> bool:
    return "bridge" in setting.tags and problem.id in {"mudslide", "loose_rocks", "flooded_path"}


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.safe]


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: len(t.tags))


def repair_power(tool: Tool, setting: Setting, delay: int) -> int:
    base = 3 if "bridge" in setting.tags else 2
    return base + delay + (1 if "wood" in tool.tags else 0)


def is_safe(tool: Tool, setting: Setting, delay: int) -> bool:
    return repair_power(tool, setting, delay) >= 3 and tool.safe


def predict(world: World, tool_id: str, problem_id: str) -> dict:
    sim = world.copy()
    _apply_problem(sim, sim.get("bridge"), PROBLEMS[problem_id], narrate=False)
    _use_tool(sim, sim.get(tool_id), PROBLEMS[problem_id], narrate=False)
    return {
        "bridge_stable": sim.get("bridge").meters["stable"] >= THRESHOLD,
        "bridge_loose": sim.get("bridge").meters["loose"] >= THRESHOLD,
    }


def _apply_problem(world: World, bridge: Entity, problem: Problem, narrate: bool = True) -> None:
    bridge.meters["wet"] += 1
    bridge.meters["loose"] += 1
    if narrate:
        propagate(world, narrate=True)


def _use_tool(world: World, tool: Entity, problem: Problem, narrate: bool = True) -> None:
    bridge = world.get("bridge")
    bridge.meters["stable"] += 1
    bridge.meters["loose"] = max(0.0, bridge.meters["loose"] - 1)
    bridge.meters["smartened"] += 1
    for c in world.characters():
        c.memes["teamwork"] += 1
    if narrate:
        world.say(tool.attrs.get("text", "They worked together and set things right."))


def opening(world: World, hero: Entity, elder: Entity, sage: Entity, setting: Setting) -> None:
    world.say(
        f"Once in a small valley, {hero.id} and {elder.id} came to {setting.place}. "
        f"{setting.detail}"
    )
    world.say(
        f"There, a wise stone-sage named {sage.id} watched over the old crossing."
    )
    hero.memes["curiosity"] += 1
    elder.memes["care"] += 1
    sage.memes["trust"] += 1


def trouble(world: World, hero: Entity, elder: Entity, problem: Problem, setting: Setting) -> None:
    world.say(
        f"But the {problem.label} had made the way unsafe. {problem.phrase} "
        f"{problem.risk}, and even the birds kept to the trees."
    )
    world.say(
        f"{hero.id} wanted to smarten the crossing for the village fair, so "
        f"{hero.pronoun()} knelt to study the stones. {elder.id} held up a lantern "
        f"and listened."
    )
    hero.memes["worry"] += 1
    elder.memes["worry"] += 1


def talk(world: World, hero: Entity, elder: Entity, sage: Entity, problem: Problem) -> None:
    world.say(
        f'"We should not rush," said {elder.id}. "The geology here tells a story. '
        f'If we know the slope and the soil, we can choose the right fix."'
    )
    world.say(
        f'{sage.id} nodded. "That is the heart of every good narrative: '
        f'listen first, then act together."'
    )
    world.say(
        f'{hero.id} touched a pebble and smiled. "Then let us learn the hill and '
        f'smarten it."'
    )
    hero.memes["teamwork"] += 1
    elder.memes["teamwork"] += 1
    sage.memes["teamwork"] += 1


def choose_tool(world: World, tool: Tool) -> None:
    world.say(
        f"They fetched {tool.phrase}, because {tool.use}. It was the sort of tool "
        f"that made a careful plan feel possible."
    )


def repair(world: World, hero: Entity, elder: Entity, sage: Entity, tool: Tool, problem: Problem) -> None:
    bridge = world.get("bridge")
    bridge.meters["stable"] += 1
    bridge.meters["loose"] = max(0.0, bridge.meters["loose"] - 1)
    bridge.meters["smartened"] += 1
    for c in (hero, elder, sage):
        c.memes["teamwork"] += 1
        c.memes["joy"] += 0.5
    world.say(
        f"Together they used {tool.phrase} to smarten the bridge. "
        f"{tool.text.replace('{problem}', problem.label)}"
    )


def ending(world: World, hero: Entity, elder: Entity, sage: Entity, setting: Setting) -> None:
    world.say(
        f"By dusk, the bridge stood firm, and the village could cross to the fair. "
        f"{hero.id} laughed, {elder.id} carried the last plank, and {sage.id} "
        f"glowed like an old moon over the river."
    )
    world.say(
        f"The little valley had its narrative finished at last: not a broken path, "
        f"but a smartened one, made safe by teamwork."
    )


def tell(setting: Setting, problem: Problem, tool: Tool,
         hero_name: str = "Elin", hero_gender: str = "girl",
         elder_name: str = "Marek", elder_gender: str = "boy",
         sage_name: str = "Pebble", sage_gender: str = "thing",
         delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    sage = world.add(Entity(id=sage_name, kind="character", type=sage_gender, role="sage"))
    bridge = world.add(Entity(id="bridge", type="bridge", label="the bridge"))
    bridge.meters["stable"] = 1
    opening(world, hero, elder, sage, setting)
    world.para()
    trouble(world, hero, elder, problem, setting)
    talk(world, hero, elder, sage, problem)
    world.para()
    choose_tool(world, tool)
    _apply_problem(world, bridge, problem)
    if is_safe(tool, setting, delay):
        repair(world, hero, elder, sage, tool, problem)
        ending(world, hero, elder, sage, setting)
        outcome = "safe"
    else:
        world.say(
            f"But the fix was too small for the slippery stones. The bridge stayed shaky, "
            f"and the fair had to wait."
        )
        outcome = "unsafe"
    world.facts.update(hero=hero, elder=elder, sage=sage, bridge=bridge, setting=setting,
                       problem=problem, tool=tool, delay=delay, outcome=outcome)
    return world


SETTINGS = {
    "river": Setting(id="river", place="the river crossing", detail="The water sang below the planks.", feature="river", slope="steep", tags={"bridge", "water"}),
    "hill": Setting(id="hill", place="the hill path", detail="The path climbed in a bright twist above the reeds.", feature="hill", slope="slanted", tags={"bridge", "stone"}),
}

PROBLEMS = {
    "mudslide": Problem(id="mudslide", label="mudslide", phrase="A slick wash of mud", risk="made the stones loose", source="rain", fix_hint="drain the water away", tags={"mud", "water"}),
    "loose_rocks": Problem(id="loose_rocks", label="loose rocks", phrase="Pebbles had spilled from the slope", risk="made the steps wobble", source="wind", fix_hint="pack the edges with strong stone", tags={"stone", "slope"}),
    "flooded_path": Problem(id="flooded_path", label="flooded path", phrase="The lower boards were wet and shining", risk="made the crossing slippery", source="rain", fix_hint="set a drier route", tags={"water", "wood"}),
}

TOOLS = {
    "drainage": Tool(id="drainage", label="drainage stones", phrase="drainage stones", use="they guide water away from the path", tags={"water", "stone"}),
    "mortar": Tool(id="mortar", label="mortar and trowels", phrase="mortar and trowels", use="they can bind loose stones into a firmer line", tags={"stone", "wood"}),
    "planks": Tool(id="planks", label="fresh planks", phrase="fresh planks", use="they can make a stronger walk across the wet part", tags={"wood", "bridge"}),
    "ribbon": Tool(id="ribbon", label="festival ribbon", phrase="festival ribbon", use="it is pretty, but it does not hold a bridge together", safe=False, tags={"pretty"}),
}

HERO_NAMES = ["Elin", "Tess", "Mira", "Nora", "Lina"]
ELDER_NAMES = ["Marek", "Borin", "Sela", "Ivo", "Hilda"]
SAGE_NAMES = ["Pebble", "Slate", "Glimmer", "Gravel", "Quartz"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    hero: str
    hero_gender: str
    elder: str
    elder_gender: str
    sage: str
    sage_gender: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="river", problem="mudslide", tool="drainage", hero="Elin", hero_gender="girl", elder="Marek", elder_gender="boy", sage="Pebble", sage_gender="thing", delay=0),
    StoryParams(setting="hill", problem="loose_rocks", tool="mortar", hero="Mira", hero_gender="girl", elder="Hilda", elder_gender="girl", sage="Slate", sage_gender="thing", delay=0),
    StoryParams(setting="river", problem="flooded_path", tool="planks", hero="Lina", hero_gender="girl", elder="Borin", elder_gender="boy", sage="Quartz", sage_gender="thing", delay=1),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if not hazard_at_risk(problem, setting):
                continue
            for tid, tool in TOOLS.items():
                if tool.safe and is_safe(tool, setting, 0):
                    combos.append((sid, pid, tid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale about a village bridge where the words "smarten", "geology", and "narrative" appear naturally.',
        f"Tell a story where {f['hero'].id}, {f['elder'].id}, and {f['sage'].id} work together to smarten a broken crossing.",
        f"Write a child-friendly fairy tale about geology and teamwork that ends with the bridge safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    elder: Entity = f["elder"]  # type: ignore[assignment]
    sage: Entity = f["sage"]  # type: ignore[assignment]
    problem: Problem = f["problem"]  # type: ignore[assignment]
    tool: Tool = f["tool"]  # type: ignore[assignment]
    bridge: Entity = f["bridge"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question="Who worked together in the story?",
            answer=f"{hero.id}, {elder.id}, and {sage.id} worked together as a team. They listened to one another and shared the job instead of trying to solve it alone.",
        ),
        QAItem(
            question="Why did they need to fix the bridge?",
            answer=f"The {problem.label} made the crossing unsafe, so the bridge was loose and slippery. They wanted the village to cross safely for the fair.",
        ),
        QAItem(
            question="How did they smarten the bridge?",
            answer=f"They used {tool.phrase} to make the bridge steadier again. That choice matched the problem, so the stones could hold together and the path became safer.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The bridge ended the story stable instead of shaky. The village could cross, and the last image is of everyone walking over a smartened bridge together.",
        ),
    ]
    if f.get("outcome") == "safe":
        qa.append(QAItem(
            question="Was the plan successful?",
            answer="Yes. Their careful teamwork was strong enough, so the repair held and the bridge stayed safe for the ending.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags) | set(world.facts["tool"].tags)  # type: ignore[index]
    out: list[QAItem] = []
    if "water" in tags:
        out.append(QAItem(
            question="What does water do to loose stones?",
            answer="Water can make loose stones slippery and easier to move. That is why drainage or another dry fix can matter so much.",
        ))
    if "stone" in tags:
        out.append(QAItem(
            question="What can strong stone help with?",
            answer="Strong stone can help hold a path or bridge together. Builders use it when they want a crossing to feel firmer and safer.",
        ))
    if "wood" in tags:
        out.append(QAItem(
            question="What are planks used for?",
            answer="Planks are long pieces of wood that can make a walkway or bridge. They help people step across a gap without sinking into the water.",
        ))
    out.append(QAItem(
        question="What is geology?",
        answer="Geology is the study of rocks, soil, and the ground itself. It helps people understand why hills, stones, and paths behave the way they do.",
    ))
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
        bits = [f"{e.type}"]
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, setting: Setting) -> str:
    return f"(No story: {problem.label} does not fit this place well enough to create a sensible teamwork repair.)"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    return f"(Refusing tool '{tool_id}': {tool.label} is pretty, but not a good repair tool for a bridge.)"


ASP_RULES = r"""
hazard(P,S) :- problem(P), setting(S).
safe_tool(T) :- tool(T), safe(T).
valid(S,P,T) :- hazard(P,S), safe_tool(T), setting_id(S), problem_id(P), tool_id(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_id", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_id", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool_id", tid))
        if tool.safe:
            lines.append(asp.fact("safe", tid))
    for sid, setting in SETTINGS.items():
        if "bridge" in setting.tags:
            for pid, problem in PROBLEMS.items():
                if hazard_at_risk(problem, setting):
                    lines.append(asp.fact("problem", pid))
                    lines.append(asp.fact("setting", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale geology teamwork storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
    ap.add_argument("--sage")
    ap.add_argument("--sage-gender", choices=["thing"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.tool and not TOOLS[args.tool].safe:
        raise StoryError(explain_tool(args.tool))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting,
        problem=problem,
        tool=tool,
        hero=args.hero or rng.choice(HERO_NAMES),
        hero_gender=args.hero_gender or "girl",
        elder=args.elder or rng.choice(ELDER_NAMES),
        elder_gender=args.elder_gender or "boy",
        sage=args.sage or rng.choice(SAGE_NAMES),
        sage_gender="thing",
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("(Invalid params: unknown setting/problem/tool.)")
    if not TOOLS[params.tool].safe:
        raise StoryError(explain_tool(params.tool))
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool],
                 hero_name=params.hero, hero_gender=params.hero_gender,
                 elder_name=params.elder, elder_gender=params.elder_gender,
                 sage_name=params.sage, sage_gender=params.sage_gender,
                 delay=params.delay)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(" ".join(map(str, row)))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
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
