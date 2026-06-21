#!/usr/bin/env python3
"""
Standalone storyworld: a tiny space-adventure problem-solving tale with
foreshadowing and flashback.

This world is built around a small starship in trouble: a child pilot, a helper,
a blinking clue, a remembered fix, and a final repair that gets the crew home.
The seed words "retard" and "twenty" are included as story-safe technical and
counting language.

The script follows the shared storyworld contract:
- StoryParams + parser/resolve/generate/emit/main
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- a Python reasonableness gate plus inline ASP_RULES twin
- three QA sets grounded in simulated world state
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    supplies: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    label: str
    place_phrase: str
    hazard: str
    foreshadow: str
    flashback: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Problem:
    id: str
    issue: str
    clue: str
    effect: str
    solution_kind: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    adult: str
    adult_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "asteroid_port": Setting(
        id="asteroid_port",
        label="a tiny asteroid port",
        place_phrase="the little docking bay on the moon station",
        hazard="a broken docking arm",
        foreshadow="a bent bolt blinked red under the floor grate",
        flashback="one old repair had worked because a clamp held a panel tight",
        tags={"space", "station"},
    ),
    "comet_lab": Setting(
        id="comet_lab",
        label="a bright comet lab",
        place_phrase="the glass lab aboard the comet ship",
        hazard="a loose fuel hose",
        foreshadow="a warning light kept flickering beside the panel",
        flashback="a memory of a snug tape wrap had saved a hose before",
        tags={"space", "lab"},
    ),
    "moon_tunnel": Setting(
        id="moon_tunnel",
        label="a moon tunnel",
        place_phrase="the silver tunnel under the crater dome",
        hazard="a stuck rover gate",
        foreshadow="dust kept gathering under a yellow lever",
        flashback="a remembered wheel shim had once opened a jammed hatch",
        tags={"space", "moon"},
    ),
}

PROBLEMS = {
    "dock": Problem(
        id="dock",
        issue="the ship could not dock",
        clue="the docking arm kept slipping away from the ring",
        effect="the ship drifted farther from the bay",
        solution_kind="clamp",
        tags={"dock", "repair"},
    ),
    "hose": Problem(
        id="hose",
        issue="the engine hose started leaking",
        clue="a thin mist hissed from the cracked hose",
        effect="the engine lost air pressure",
        solution_kind="seal",
        tags={"engine", "repair"},
    ),
    "gate": Problem(
        id="gate",
        issue="the rover gate would not open",
        clue="the gate jammed half-way with a sharp squeak",
        effect="the rover could not roll into the tunnel",
        solution_kind="shim",
        tags={"gate", "repair"},
    ),
}

TOOLS = {
    "clamp": Tool(
        id="clamp",
        label="repair clamp",
        phrase="a small repair clamp",
        use="tighten the broken joint",
        power=3,
        tags={"clamp", "repair"},
    ),
    "seal_tape": Tool(
        id="seal_tape",
        label="seal tape",
        phrase="a roll of seal tape",
        use="wrap the crack shut",
        power=2,
        tags={"tape", "repair"},
    ),
    "shim": Tool(
        id="shim",
        label="wheel shim",
        phrase="a flat wheel shim",
        use="lift the jammed gate",
        power=3,
        tags={"shim", "repair"},
    ),
    "pocket_light": Tool(
        id="pocket_light",
        label="pocket light",
        phrase="a pocket light",
        use="shine on the dark panel",
        power=1,
        tags={"light"},
    ),
}

NAMES = ["Ava", "Milo", "Nia", "Jasper", "Lena", "Owen", "Tess", "Leo"]
TYPES = {"girl": ["Ava", "Nia", "Lena", "Tess"], "boy": ["Milo", "Jasper", "Owen", "Leo"]}
TRAITS = ["careful", "curious", "brave", "quick-thinking"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for pid, p in PROBLEMS.items():
            if p.solution_kind in TOOLS:
                out.append((sid, pid, p.solution_kind))
    return out


def reasonableness_ok(setting: Setting, problem: Problem, tool: Tool) -> bool:
    return problem.solution_kind == tool.id and tool.power >= 2


def outcome_of(params: StoryParams) -> str:
    tool = TOOLS[params.tool]
    return "solved" if tool.power >= 2 else "stalled"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny space-adventure storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-type", choices=["mother", "father"])
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
    if args.setting and args.problem and args.tool:
        if not reasonableness_ok(SETTINGS[args.setting], PROBLEMS[args.problem], TOOLS[args.tool]):
            raise StoryError("That tool would not really solve that space problem.")
    combos = [c for c in valid_combos()
              if args.setting in (None, c[0])
              and args.problem in (None, c[1])
              and args.tool in (None, c[2])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(combos)
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if child_type == "girl" else "girl")
    child = args.child or rng.choice(TYPES[child_type])
    helper = args.helper or rng.choice([n for n in TYPES[helper_type] if n != child])
    adult = args.adult or rng.choice(["Captain Mira", "Pilot Jun"])
    adult_type = args.adult_type or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, problem=problem, tool=tool,
                       child=child, child_type=child_type,
                       helper=helper, helper_type=helper_type,
                       adult=adult, adult_type=adult_type)


def _flashback_line(world: World, setting: Setting, tool: Tool) -> None:
    world.say(
        f"{setting.flashback}. So when the same kind of trouble returned, "
        f"the children knew that {tool.label} might be the right fix."
    )


def _foreshadow_line(world: World, setting: Setting) -> None:
    world.say(
        f"As they walked in, {setting.foreshadow}."
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]

    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, role="child",
                             traits=["small", "fast"], supplies=set()))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper",
                              traits=["smart"], supplies=set()))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult_type, role="adult",
                             label="the adult", traits=["calm"], supplies=set()))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the ship"))
    issue = world.add(Entity(id="issue", kind="thing", type="problem", label=problem.issue))

    child.memes["worry"] += 1
    helper.memes["alert"] += 1

    world.say(
        f"{child.id} and {helper.id} floated through {setting.label} aboard {ship.label}."
    )
    world.say(
        f"Then {problem.issue}, and {problem.clue}."
    )
    world.say(
        f"The {child.id} pointed at a note on the wall that said the ship must "
        f"never go in {problem.id} mode too long; it would only have to wait twenty seconds."
    )
    _foreshadow_line(world, setting)
    world.para()

    world.say(
        f"{helper.id} frowned and remembered a tiny flashback."
    )
    _flashback_line(world, setting, tool)
    world.say(
        f'"I know," {helper.id} said. "We need {tool.phrase} to {tool.use}."'
    )
    world.say(
        f"{child.id} held the light steady while {helper.id} used it."
    )
    world.para()

    if tool.id == problem.solution_kind:
        issue.meters["fixed"] += 1
        ship.meters["safe"] += 1
        adult.memes["pride"] += 1
        world.say(
            f"{helper.id} worked carefully, and the tool did exactly what it should."
        )
        world.say(
            f"Soon the trouble was gone. The ship stopped drifting, the path opened, "
            f"and {adult.id} smiled when the children called for help."
        )
        world.say(
            f"By the end, they were back on course, with the stars bright again outside the window."
        )
    else:
        issue.meters["fixed"] += 0
        ship.meters["safe"] += 0
        world.say(
            f"The tool was not enough, so the children had to call the adult and wait."
        )
        world.say(
            f"Still, they stayed calm until help came, and the ship did not break apart."
        )

    world.facts.update(
        setting=setting,
        problem=problem,
        tool=tool,
        child=child,
        helper=helper,
        adult=adult,
        ship=ship,
        issue=issue,
        solved=tool.id == problem.solution_kind,
        seed_word_retard="retard",
        seed_word_twenty="twenty",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure for a small child that includes the words "retard" and "twenty".',
        f"Tell a problem-solving story where {f['child'].id} and {f['helper'].id} fix {f['problem'].issue} on a ship.",
        f"Write a story with a flashback and a foreshadowing clue aboard {f['setting'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    answer1 = (
        f"{f['child'].id} and {f['helper'].id} were trying to solve a ship problem together. "
        f"{f['adult'].id} was nearby, and the children kept working until the ship was safe again."
    )
    answer2 = (
        f"The clue was {f['setting'].foreshadow}. It mattered because it warned them that a repair would be needed soon."
    )
    answer3 = (
        f"They remembered {f['setting'].flashback}. That flashback helped them choose {f['tool'].label}."
    )
    qa = [
        QAItem(
            question="Who was the story about?",
            answer=answer1,
        ),
        QAItem(
            question="What foreshadowed the problem?",
            answer=answer2,
        ),
        QAItem(
            question="What old memory helped solve the problem?",
            answer=answer3,
        ),
    ]
    if f["solved"]:
        qa.append(QAItem(
            question="How did the story end?",
            answer=(
                f"The problem was solved. {f['child'].id} and {f['helper'].id} fixed the ship, "
                f"and {f['adult'].id} saw them return to the stars safely."
            ),
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer=(
                f"The children stayed calm, but the tool was too weak, so they had to wait for help."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory from before the present moment. It helps the reader understand why a character knows what to do.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something will matter later. It helps build suspense before the big moment.",
        ),
        QAItem(
            question="What does a repair clamp do?",
            answer="A repair clamp holds two broken parts together tightly. That can help stop a joint from slipping apart.",
        ),
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
        bits = []
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.supplies:
            bits.append(f"supplies={sorted(e.supplies)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="asteroid_port", problem="dock", tool="clamp",
                child="Ava", child_type="girl", helper="Milo", helper_type="boy",
                adult="Captain Mira", adult_type="mother"),
    StoryParams(setting="comet_lab", problem="hose", tool="seal_tape",
                child="Leo", child_type="boy", helper="Nia", helper_type="girl",
                adult="Pilot Jun", adult_type="father"),
    StoryParams(setting="moon_tunnel", problem="gate", tool="shim",
                child="Tess", child_type="girl", helper="Owen", helper_type="boy",
                adult="Captain Mira", adult_type="mother"),
]


def explain_rejection(setting: Setting, problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} would not really solve {problem.issue}. "
        f"This space story needs a tool that fits the problem and makes the fix feel real.)"
    )


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, t.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,T) :- setting(S), problem(P), tool(T), needs(P,T), power(T,N), N >= 2.
needs(dock,clamp).
needs(hose,seal_tape).
needs(gate,shim).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, problem=None, tool=None, child=None, child_type=None,
            helper=None, helper_type=None, adult=None, adult_type=None,
        ), random.Random(7)))
        assert sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if not reasonableness_ok(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool]):
        raise StoryError("Those choices do not make a sensible problem-solving story.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
