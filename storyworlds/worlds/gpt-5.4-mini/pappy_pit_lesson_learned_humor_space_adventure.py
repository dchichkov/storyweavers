#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pappy_pit_lesson_learned_humor_space_adventure.py
=================================================================================

A standalone storyworld for a small Space Adventure tale about a crew on a moon,
a tricky pit, a funny mistake, and a lesson learned about slowing down and asking
for help. The domain is intentionally tiny: a child astronaut, pappy, a pit, a
glitchy rover, and a safe rescue. Stories are state-driven, with physical meters
and emotional memes shaping the prose.

The seed words are honored in the world model and rendered story:
- pappy
- pit

The style leans toward a playful space adventure with humor and a clear lesson
learned ending.
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

    tags: set[str] = field(default_factory=set)

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
        return {"father": "pappy", "mother": "mama"}.get(self.type, self.label or self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    sky: str
    adventure: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    danger: str
    laugh: str
    fix_hint: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    safe: bool
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    pit = world.entities.get("pit")
    if not pit or pit.meters["trapped"] < THRESHOLD:
        return out
    sig = ("alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["worry"] += 1
    out.append("__alarm__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    pit = world.entities.get("pit")
    if not pit or pit.meters["trapped"] < THRESHOLD:
        return out
    if "pappy" not in world.entities:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("pappy").memes["pride"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("alarm", "social", _r_alarm),
    Rule("relief", "social", _r_relief),
]


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


def hazard(problem: Problem) -> bool:
    return problem.risky


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.safe]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, prob in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if hazard(prob) and tool.safe and pid in tool.helps:
                    combos.append((sid, pid, tid))
    return combos


def reasonableness_gate(problem: Problem, tool: Tool) -> bool:
    return hazard(problem) and tool.safe and problem.id in tool.helps


def pit_severity(delay: int) -> int:
    return 1 + delay


def can_rescue(tool: Tool, delay: int) -> bool:
    return len(tool.helps) >= pit_severity(delay)


def predict(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get("crew"), PROBLEMS[problem_id], narrate=False)
    return {"trapped": sim.get("pit").meters["trapped"] >= THRESHOLD}


def _do_problem(world: World, crew: Entity, problem: Problem, narrate: bool = True) -> None:
    crew.meters["mistake"] += 1
    world.get("pit").meters["trapped"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, crew: Entity, pappy: Entity, setting: Setting) -> None:
    crew.memes["joy"] += 1
    world.say(
        f"On a bright moon morning, {crew.id} and {pappy.label_word} rolled across "
        f"{setting.place} in a little rover. {setting.adventure}"
    )
    world.say(
        f"The stars winked over the camp, and the {setting.sky} sky made everything "
        f"feel like a joke waiting to happen."
    )


def notice_pit(world: World, crew: Entity, pappy: Entity, problem: Problem) -> None:
    world.say(
        f"Then {crew.id} spotted {problem.label} -- a deep {problem.label} in the dust, "
        f"{problem.danger}."
    )
    world.say(
        f'"Look at that!" {crew.id} laughed. "{problem.laugh}"'
    )


def rush_toward(world: World, crew: Entity, problem: Problem) -> None:
    crew.memes["impulse"] += 1
    world.say(
        f"{crew.id} leaned forward and wanted to zip closer for a peek."
    )
    world.say(
        f'Even the rover gave a tiny beep, as if it knew that was a funny but bad idea.'
    )


def warn(world: World, pappy: Entity, crew: Entity, problem: Problem) -> None:
    pred = predict(world, "pit")
    crew.memes["warning"] += 1
    world.facts["predicted_trapped"] = pred["trapped"]
    world.say(
        f'"Easy now," {pappy.label_word} said. "That {problem.label} is tricky. '
        f'It can swallow a wheel before you can count to two."'
    )


def defy(world: World, crew: Entity) -> None:
    crew.memes["defiance"] += 1
    world.say(f"But {crew.id} was curious and kept edging closer anyway.")


def trap(world: World, problem: Problem) -> None:
    _do_problem(world, world.get("crew"), problem)
    world.say(
        f'The rover lurched, the dust dropped away, and with a sudden "WHUMP!" '
        f'one wheel sank into the {problem.label}.'
    )


def alarm(world: World, crew: Entity, pappy: Entity, problem: Problem) -> None:
    world.say(f'"Pappy!" {crew.id} yelled. "The {problem.label} got us!"')
    world.say(f'"Hold on, kiddo!"')


def rescue(world: World, pappy: Entity, tool: Tool, problem: Problem, delay: int) -> bool:
    if not can_rescue(tool, delay):
        return False
    world.get("pit").meters["trapped"] = 0.0
    body = "stretched out the rescue hook and pulled the rover free"
    world.say(
        f"{pappy.label_word.capitalize()} came running and {body}."
    )
    world.say(
        f"The wheel popped loose with a comical boing, and the whole rover bounced "
        f"back onto safe ground."
    )
    return True


def lesson(world: World, pappy: Entity, crew: Entity, problem: Problem) -> None:
    crew.memes["lesson"] += 1
    crew.memes["relief"] += 1
    world.say("For a second, nobody talked.")
    world.say(
        f"Then {pappy.label_word.capitalize()} ruffled {crew.id}'s hair and said, "
        f'"Funny ideas are fine, but not every pit wants a visit. The lesson is to '
        f'slow down and ask for help before you race in."'
    )
    world.say(
        f'{crew.id} nodded, grinning sheepishly. "Got it," {crew.id} said. '
        f'"Next time I will not drive into the moon hole."'
    )


def ending(world: World, crew: Entity, pappy: Entity, setting: Setting) -> None:
    crew.memes["pride"] += 1
    world.say(
        f"Then the rover rolled on beside {pappy.label_word}, both of them laughing "
        f"under the {setting.sky} sky."
    )
    world.say(
        f"The little ship kept going, safer and wiser than before."
    )


def tell(setting: Setting, problem: Problem, tool: Tool,
         crew_name: str = "Nova", crew_gender: str = "girl",
         pappy_gender: str = "father", delay: int = 0) -> World:
    world = World()
    crew = world.add(Entity(id=crew_name, kind="character", type=crew_gender, role="crew"))
    pappy = world.add(Entity(id="pappy", kind="character", type=pappy_gender, label="pappy", role="helper"))
    pit = world.add(Entity(id="pit", type="thing", label="pit"))
    world.facts["setting"] = setting
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["delay"] = delay

    open_scene(world, crew, pappy, setting)
    world.para()
    notice_pit(world, crew, pappy, problem)
    rush_toward(world, crew, problem)
    warn(world, pappy, crew, problem)
    defy(world, crew)
    trap(world, problem)
    alarm(world, crew, pappy, problem)
    world.para()
    ok = rescue(world, pappy, tool, problem, delay)
    if not ok:
        raise StoryError("This pit story needs a rescue tool that can actually pull the rover free.")
    lesson(world, pappy, crew, problem)
    world.para()
    ending(world, crew, pappy, setting)

    world.facts.update(
        crew=crew, pappy=pappy, pit=pit, outcome="rescued",
        trapped=pit.meters["trapped"] >= THRESHOLD,
        learned=crew.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moonbase": Setting("moonbase", "the moonbase yard", "silver", "This was supposed to be a quick practice drive."),
    "cratercamp": Setting("cratercamp", "the crater camp road", "blue", "They were heading toward the radio tower with snacks and maps."),
    "starport": Setting("starport", "the starport lane", "golden", "The little rover was on its way to bring lunch to the launch pad."),
}

PROBLEMS = {
    "pit": Problem("pit", "pit", "It looked shallow from far away, but it had a sneaky drop inside.", "moon sandwich", "It could grab a wheel and stop the rover", True, {"pit"}),
    "craterhole": Problem("craterhole", "crater hole", "It hid in the dust like a gap in a cookie.", "spaceship scoop", "It could snatch a wheel in one silly second", True, {"pit"}),
}

TOOLS = {
    "hook": Tool("hook", "rescue hook", "a long rescue hook", True, {"pit"}, {"hook"}),
    "tether": Tool("tether", "tether line", "a strong tether line", True, {"pit"}, {"tether"}),
    "net": Tool("net", "tow net", "a tow net", True, {"pit"}, {"net"}),
}

GIRL_NAMES = ["Nova", "Mia", "Zoe", "Ava", "Luna", "Iris"]
BOY_NAMES = ["Finn", "Leo", "Max", "Jett", "Theo", "Nico"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    crew_name: str
    crew_gender: str
    pappy_gender: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a playful space adventure story that includes the words "pappy" and "{f["problem"].label}", and ends with a lesson learned.',
        f"Tell a funny moon rescue story where {f['crew'].id} almost drives into a {f['problem'].label}, but {f['pappy'].label_word} helps.",
        f'Write a child-friendly space story about a rover, a pit, and a grown-up who teaches "slow down and ask for help."',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    crew, pappy, prob = f["crew"], f["pappy"], f["problem"]
    qa = [
        ("Who is the story about?",
         f"It is about {crew.id} and pappy on a moon adventure. The little rover, the pit, and the rescue are the main parts of the trouble."),
        ("What made the rover stop?",
         f"The rover got stuck in the {prob.label}. It sank into the hole with a funny WHUMP, and then pappy had to pull it free."),
        ("What lesson did they learn?",
         f"They learned to slow down and ask for help before rushing into a pit. That way the adventure stays funny, safe, and under control."),
    ]
    if f.get("trapped"):
        qa.append((
            "Why did pappy need the rescue tool?",
            f"The pit trapped a wheel, so pappy used the rescue tool to pull the rover out. It was the right kind of help for a moon hole like that."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pit?",
         "A pit is a hole in the ground. If a wheel falls into one, the vehicle can get stuck until someone helps."),
        ("Who is pappy?",
         "Pappy is a father or grandpa-like grown-up in this story. He knows how to help when something goes wrong."),
        ("Why should you slow down in space adventures?",
         "Because fast choices can cause trouble, especially near holes or cliffs. Slowing down gives you time to notice danger and ask for help."),
    ]


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moonbase", "pit", "hook", "Nova", "girl", "father", 0),
    StoryParams("cratercamp", "craterhole", "tether", "Finn", "boy", "father", 1),
    StoryParams("starport", "pit", "net", "Mia", "girl", "father", 0),
]


def explain_rejection(problem: Problem, tool: Tool) -> str:
    if not problem.risky:
        return "(No story: that pit is not actually a danger in this world.)"
    if not tool.safe:
        return f"(Refusing tool '{tool.id}': it is not a safe rescue tool.)"
    return "(No story: this rescue tool does not fit the pit problem.)"


def outcome_of(params: StoryParams) -> str:
    return "rescued" if can_rescue(TOOLS[params.tool], params.delay) else "stuck"


ASP_RULES = r"""
problem_risky(P) :- problem(P), risky(P).
tool_safe(T) :- tool(T), safe(T).
compatible(S, P, T) :- setting(S), problem(P), tool(T), problem_risky(P), tool_safe(T), helps(T, P).
outcome(rescued) :- chosen_tool(T), chosen_delay(D), power(T, P), P >= 1 + D.
outcome(stuck) :- chosen_tool(T), chosen_delay(D), power(T, P), P < 1 + D.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.risky:
            lines.append(asp.fact("risky", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.safe:
            lines.append(asp.fact("safe", tid))
        lines.append(asp.fact("power", tid, len(t.helps)))
        for help_id in sorted(t.helps):
            lines.append(asp.fact("helps", tid, help_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_tool", params.tool), asp.fact("chosen_delay", params.delay)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    p, c = set(valid_combos()), set(asp_valid_combos())
    if p == c:
        print(f"OK: gate matches valid_combos() ({len(p)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("python-only:", sorted(p - c))
        print("clingo-only:", sorted(c - p))
    cases = list(CURATED)
    for s in range(20):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
        except StoryError:
            pass
    if all(asp_outcome(p) == outcome_of(p) for p in cases):
        print(f"OK: outcome matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcomes.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about pappy, a pit, humor, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--pappy-gender", dest="pappy_gender", choices=["father", "man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    pappy_gender = args.pappy_gender or "father"
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(setting, problem, tool, name, gender, pappy_gender, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool],
                 params.crew_name, params.crew_gender, params.pappy_gender, params.delay)
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
        print(asp_program("", "#show compatible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, p, t in combos:
            print(f"  {s:10} {p:12} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.crew_name} and pappy: {p.problem} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
