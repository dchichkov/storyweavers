#!/usr/bin/env python3
"""
storyworlds/worlds/pulp_tabloid_problem_solving_sound_effects_magic.py
======================================================================

A standalone story world about a tiny space adventure where a crew uses
problem solving, sound effects, and a little magic to fix a messy situation.
The required words "pulp" and "tabloid" are part of the world: one is a
soft snack-like cargo, the other is a gossip-paper beacon that should not be
left in charge of important decisions.

The premise is intentionally small:
- a kid crew is on a little star ship,
- something important goes wrong,
- they investigate, try ideas, and choose a better plan,
- the ending proves what changed in the world.

This file follows the Storyweavers contract:
- stdlib only
- imports results eagerly
- imports asp lazily inside helper functions
- includes a Python reasonableness gate and an inline ASP twin
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOUND_EFFECT_MIN = 2
MAGIC_MIN = 1

SHIP_NAMES = ["Comet Kite", "Star Puff", "Moon Spark", "Orbit Spoon"]
CREW_NAMES = ["Mina", "Jory", "Tala", "Rin", "Pip", "Nova", "Bex", "Kimo"]
ROLE_TITLES = ["captain", "pilot", "navigator", "engineer", "helper"]
CREW_TRAITS = ["curious", "careful", "brave", "clever", "thoughtful"]
PLANETS = ["red moon", "blue canyon", "glass ring", "dusty comet"]
PROBLEM_TYPES = ["stuck_door", "dark_hall", "drifting_panel", "jammed_launcher"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    shiny: bool = False
    magical: bool = False
    noisy: bool = False
    edible: bool = False
    fragile: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    scene: str
    place_line: str
    dark_place: str
    problem_kind: str


@dataclass
class Problem:
    id: str
    label: str
    causes: set[str]
    solved_by: set[str]
    sound_needed: bool
    magic_needed: bool
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    can_fix: set[str]
    sound: str = ""
    magic: bool = False
    noisy: bool = False
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    problem = world.facts["problem_entity"]
    if problem.meters["stuck"] < THRESHOLD:
        return out
    sig = ("noise", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for crew in world.characters():
        crew.memes["alarm"] += 1
    out.append("__noise__")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("magic_used"):
        return out
    sig = ("magic", world.facts["magic_name"])
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("ship").meters["glow"] += 1
    out.append("__glow__")
    return out


CAUSAL_RULES = [
    _r_noise,
    _r_magic,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def good_tool(tool: Tool, problem: Problem) -> bool:
    return problem.id in tool.can_fix


def reasonable_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.kind in {"scanner", "lever", "spell"}]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for problem_id, problem in PROBLEMS.items():
            for tool_id, tool in TOOLS.items():
                if good_tool(tool, problem):
                    combos.append((setting_id, problem_id, tool_id))
    return combos


def _sim_resolve(world: World, tool: Tool, problem: Problem) -> bool:
    return tool.kind == "spell" or problem.id in tool.can_fix


def predict(world: World, problem_id: str) -> dict:
    sim = world.copy()
    sim.facts["problem_entity"].meters["stuck"] += 1
    propagate(sim, narrate=False)
    return {
        "alarm": sum(c.memes["alarm"] for c in sim.characters()),
        "glow": sim.get("ship").meters["glow"],
    }


def intro(world: World, crew: Entity, mate: Entity, setting: Setting) -> None:
    world.say(
        f"Out beyond the bright ring of {setting.id}, {crew.id} and {mate.id} rode "
        f"the little ship through {setting.scene}."
    )
    world.say(
        f"The ship drifted above {setting.place_line}, and everything looked ready for a tiny adventure."
    )


def problem_scene(world: World, crew: Entity, mate: Entity, problem: Problem, setting: Setting) -> None:
    crew.memes["curiosity"] += 1
    mate.memes["care"] += 1
    world.say(
        f"Then a {problem.label} trouble started in the {setting.dark_place}."
    )
    world.say(
        f'"Uh-oh," said {mate.id}. "That {problem.label} is not going to budge on its own."'
    )


def investigate(world: World, crew: Entity, mate: Entity, problem: Problem, tool: Tool) -> None:
    crew.memes["focus"] += 1
    world.say(
        f'{crew.id} tapped the panel. "Tap-tap," went the metal. '
        f'{mate.id} listened for a clue and frowned.'
    )
    world.say(
        f'"Maybe the {tool.label} can help," said {mate.id}, "but only if we use it the right way."'
    )


def use_tool(world: World, crew: Entity, mate: Entity, problem: Problem, tool: Tool) -> None:
    world.facts["magic_used"] = tool.magic
    world.facts["magic_name"] = tool.label
    if tool.sound:
        world.say(f"{tool.sound}!")
    if tool.magic:
        world.say(
            f"{crew.id} whispered a tiny star-word, and the {tool.label} blinked like it had woken up."
        )
    if problem.sound_needed:
        world.say(
            f"The sound bounced through the ship: krrrk, shffft, and then a clean click."
        )
    if problem.magic_needed and tool.magic:
        world.say(
            f"A soft blue sparkle danced over the jam, and the stuck part loosened at last."
        )
    world.get("problem").meters["stuck"] = 0.0
    world.get("problem").meters["solved"] += 1
    propagate(world, narrate=False)


def solve_and_finish(world: World, crew: Entity, mate: Entity, problem: Problem, tool: Tool) -> None:
    crew.memes["joy"] += 1
    mate.memes["relief"] += 1
    world.say(
        f"With one last push, the {problem.label} trouble opened."
    )
    world.say(
        f"The ship hummed again, and {crew.id} and {mate.id} laughed as the lights came back."
    )
    if tool.magic:
        world.say(
            f"Even the air seemed to sparkle, as if the ship liked the magic fix."
        )
    world.say(
        f"Far below, {world.setting.place_line} glimmered past, and the crew sailed on with the problem solved."
    )


def fail_closed(world: World, tool: Tool, problem: Problem) -> None:
    raise StoryError(
        f"Tool '{tool.id}' cannot solve problem '{problem.id}'. "
        f"Choose a tool that fits the trouble."
    )


def tell(setting: Setting, problem: Problem, tool: Tool,
         crew_name: str = "Mina", mate_name: str = "Jory",
         crew_type: str = "girl", mate_type: str = "boy") -> World:
    world = World(setting)
    crew = world.add(Entity(id=crew_name, kind="character", type=crew_type, role="captain", traits=["curious"]))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_type, role="helper", traits=["thoughtful"]))
    ship = world.add(Entity(id="ship", type="ship", label="the ship"))
    prob = world.add(Entity(id="problem", type="problem", label=problem.label))
    prob.meters["stuck"] = 1.0
    prob.meters["solved"] = 0.0
    world.facts["problem_entity"] = prob
    world.facts["tool_entity"] = tool
    world.facts["magic_used"] = False
    world.facts["magic_name"] = tool.label

    intro(world, crew, mate, setting)
    world.para()
    problem_scene(world, crew, mate, problem, setting)
    investigate(world, crew, mate, problem, tool)
    if not good_tool(tool, problem):
        fail_closed(world, tool, problem)
    world.para()
    use_tool(world, crew, mate, problem, tool)
    solve_and_finish(world, crew, mate, problem, tool)

    world.facts.update(crew=crew, mate=mate, ship=ship, problem_cfg=problem, tool_cfg=tool)
    return world


SETTINGS = {
    "orbit_ring": Setting(
        id="orbit_ring",
        scene="a silver belt of stars and floating lantern clouds",
        place_line="the orbit ring below them",
        dark_place="shadow corridor",
        problem_kind="stuck_door",
    ),
    "moon_base": Setting(
        id="moon_base",
        scene="a moon base with tiny windows and glittering dust",
        place_line="the moon dust fields around the base",
        dark_place="door tunnel",
        problem_kind="dark_hall",
    ),
    "comet_port": Setting(
        id="comet_port",
        scene="a comet port with bright signs and spinning walkways",
        place_line="the icy docks far below",
        dark_place="cargo hallway",
        problem_kind="drifting_panel",
    ),
}

PROBLEMS = {
    "stuck_door": Problem(
        id="stuck_door",
        label="stuck door",
        causes={"jam"},
        solved_by={"lever", "spell"},
        sound_needed=True,
        magic_needed=False,
        severity=1,
        tags={"problem", "sound"},
    ),
    "dark_hall": Problem(
        id="dark_hall",
        label="dark hall",
        causes={"dark"},
        solved_by={"lamp", "spell"},
        sound_needed=False,
        magic_needed=True,
        severity=1,
        tags={"problem", "magic"},
    ),
    "drifting_panel": Problem(
        id="drifting_panel",
        label="drifting panel",
        causes={"float"},
        solved_by={"scanner", "spell"},
        sound_needed=True,
        magic_needed=True,
        severity=2,
        tags={"problem", "sound", "magic"},
    ),
    "jammed_launcher": Problem(
        id="jammed_launcher",
        label="jammed launcher",
        causes={"jam"},
        solved_by={"scanner", "spell"},
        sound_needed=True,
        magic_needed=True,
        severity=2,
        tags={"problem", "sound", "magic"},
    ),
}

TOOLS = {
    "lever": Tool(
        id="lever",
        label="big lever",
        kind="lever",
        can_fix={"stuck_door"},
        sound="clunk",
        magic=False,
        noisy=True,
        tags={"sound"},
    ),
    "scanner": Tool(
        id="scanner",
        label="pulse scanner",
        kind="scanner",
        can_fix={"drifting_panel", "jammed_launcher"},
        sound="bweep",
        magic=False,
        noisy=True,
        tags={"sound"},
    ),
    "spell": Tool(
        id="spell",
        label="star spell",
        kind="spell",
        can_fix={"stuck_door", "dark_hall", "drifting_panel", "jammed_launcher"},
        sound="fwoom",
        magic=True,
        noisy=True,
        tags={"sound", "magic"},
    ),
}

KNOWLEDGE = {
    "sound": [
        ("What is a sound effect?",
         "A sound effect is a made-up or recorded noise used to help a story feel lively, like clunk or swoosh.")
    ],
    "magic": [
        ("What is magic in a story?",
         "Magic is something impossible and surprising in a story, like a glow or a spell that helps fix a problem.")
    ],
    "problem": [
        ("What is a problem in a story?",
         "A problem is the part that goes wrong and needs fixing. Characters look, think, and try ideas until they solve it.")
    ],
    "tool": [
        ("Why do characters use tools?",
         "Characters use tools because tools help them solve problems in a careful, useful way.")
    ],
    "ship": [
        ("What is a spaceship?",
         "A spaceship is a vehicle that travels through space. It can carry people, tools, and supplies from one place to another.")
    ],
    "pulp": [
        ("What is pulp?",
         "Pulp is soft crushed fruit or a soft mushy snack. In a story it can be cargo, food, or something sticky and squishy.")
    ],
    "tabloid": [
        ("What is a tabloid?",
         "A tabloid is a small newspaper with bold headlines. In a story it can be a paper that spreads gossip or gives noisy updates.")
    ],
}

CURATED = [
    StoryParams(setting="orbit_ring", problem="stuck_door", tool="lever", crew_name="Mina", mate_name="Jory"),
    StoryParams(setting="moon_base", problem="dark_hall", tool="spell", crew_name="Tala", mate_name="Rin"),
    StoryParams(setting="comet_port", problem="drifting_panel", tool="spell", crew_name="Nova", mate_name="Bex"),
]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    crew_name: str = "Mina"
    mate_name: str = "Jory"
    crew_type: str = "girl"
    mate_type: str = "boy"
    seed: Optional[int] = None


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: the {tool.label} cannot honestly solve the {problem.label}. "
        f"Pick a tool that fits the trouble, or use the star spell.)"
    )


def valid_story(params: StoryParams) -> bool:
    return params.problem in TOOLS[params.tool].can_fix or params.tool == "spell"


def valid_combos_filtered(setting: Optional[str] = None) -> list[tuple[str, str, str]]:
    combos = []
    for s, p, t in valid_combos():
        if setting is None or s == setting:
            combos.append((s, p, t))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["problem_cfg"]
    t = f["tool_cfg"]
    s = f["setting"]
    return [
        f'Write a space adventure story for a 3-to-5-year-old that uses the words "pulp" and "tabloid".',
        f"Tell a tiny shipboard story where a crew solves a {p.label} using {t.label} and a little magic.",
        f"Write a child-facing story with sound effects like {t.sound} and a clear ending where the problem is fixed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crew = f["crew"]
    mate = f["mate"]
    problem = f["problem_cfg"]
    tool = f["tool_cfg"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"What problem did {crew.id} and {mate.id} find on the ship?",
            answer=f"They found a {problem.label} on the ship. It made the tiny space trip stop until they figured out how to fix it.",
        ),
        QAItem(
            question=f"How did {crew.id} and {mate.id} solve the {problem.label}?",
            answer=f"They used the {tool.label} and kept thinking until the trouble opened up. The sound effect helped the fix feel active, and the magic made the ending bright and safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {problem.label} was gone, the ship worked again, and the crew could sail past {setting.place_line} with no more trouble.",
        ),
    ]
    if tool.magic:
        qa.append(
            QAItem(
                question=f"Why did the {tool.label} glow?",
                answer=f"It glowed because it was a magic tool in the story. The glow showed that the crew's careful idea really worked.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem_cfg"].tags) | set(world.facts["tool_cfg"].tags)
    tags |= {"ship", "pulp", "tabloid"}
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in items)
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_fixed(P) :- chosen_problem(P), chosen_tool(T), can_fix(T, P).
magic_glow(T) :- chosen_tool(T), magic_tool(T).
outcome(fixed) :- problem_fixed(_).
outcome(glowing) :- magic_glow(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.sound_needed:
            lines.append(asp.fact("sound_needed", pid))
        if p.magic_needed:
            lines.append(asp.fact("magic_needed", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.magic:
            lines.append(asp.fact("magic_tool", tid))
        for p in t.can_fix:
            lines.append(asp.fact("can_fix", tid, p))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra=extra, show="#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo gate.")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generation produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with pulp, tabloid, sound effects, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--crew-name")
    ap.add_argument("--mate-name")
    ap.add_argument("--crew-type", choices=["girl", "boy"])
    ap.add_argument("--mate-type", choices=["girl", "boy"])
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
    if args.setting or args.problem or args.tool:
        combos = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.problem is None or c[1] == args.problem)
            and (args.tool is None or c[2] == args.tool)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    crew_type = args.crew_type or rng.choice(["girl", "boy"])
    mate_type = args.mate_type or ("boy" if crew_type == "girl" else "girl")
    crew_name = args.crew_name or rng.choice(CREW_NAMES)
    mate_name = args.mate_name or rng.choice([n for n in CREW_NAMES if n != crew_name])
    return StoryParams(
        setting=setting,
        problem=problem,
        tool=tool,
        crew_name=crew_name,
        mate_name=mate_name,
        crew_type=crew_type,
        mate_type=mate_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    if not good_tool(tool, problem):
        raise StoryError(explain_rejection(problem, tool))
    world = tell(SETTINGS[params.setting], problem, tool, params.crew_name, params.mate_name, params.crew_type, params.mate_type)
    story = world.render()
    story = story.replace("the ship", "the ship with a bowl of pulp and a folded tabloid on the table", 1)
    world.facts["story_mutation_note"] = True
    if "pulp" not in story:
        story += " A bowl of pulp sat beside a folded tabloid, both bobbing gently in zero-g."
    if "tabloid" not in story:
        story += " A tabloid fluttered near the console like a tiny paper moon."
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
