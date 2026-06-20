#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/volley_annual_irish_problem_solving_detective_story.py
=====================================================================================

A standalone storyworld for a small detective tale set around an annual Irish
volleyball event. The world stays tiny and classical: a few typed entities, a
few state changes, a mystery that can be reasoned about, and a solution that
changes what the children see and do.

Seed words required by the request are woven into the simulation:
- volley
- annual
- irish

The domain is a child-facing detective story with problem solving: something
goes missing at the annual Irish fair, clues are gathered, a suspect is tested
against the world model, and the real fix restores the event.
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
QA_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    annual: bool
    irish: bool
    sport: str
    crowd: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Mystery:
    id: str
    clue_kind: str
    missing_item: str
    found_place: str
    cause: str
    solution: str
    target_kind: str
    evidence: str
    danger: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    use: str
    gives_answer: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    report = world.get("report")
    if report.meters["missing"] >= THRESHOLD and ("worry", "crowd") not in world.fired:
        world.fired.add(("worry", "crowd"))
        for c in world.characters():
            c.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    report = world.get("report")
    clue = world.get("clue")
    if report.meters["missing"] >= THRESHOLD and clue.meters["noticed"] >= THRESHOLD and ("clue", "seen") not in world.fired:
        world.fired.add(("clue", "seen"))
        world.get("detective").memes["focus"] += 1
        out.append("__clue__")
    return out


def _r_solution(world: World) -> list[str]:
    out: list[str] = []
    case = world.get("case")
    if case.meters["solved"] >= THRESHOLD and ("solution", "relief") not in world.fired:
        world.fired.add(("solution", "relief"))
        for c in world.characters():
            c.memes["relief"] += 1
        out.append("__solution__")
    return out


CAUSAL_RULES = [_r_worry, _r_clue, _r_solution]


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


def clue_predicts_solution(world: World, mystery: Mystery, tool: Tool) -> bool:
    sim = world.copy()
    simulate_search(sim, mystery, tool, narrate=False)
    return sim.get("case").meters["solved"] >= THRESHOLD


def simulate_search(world: World, mystery: Mystery, tool: Tool, narrate: bool = True) -> None:
    detective = world.get("detective")
    assistant = world.get("assistant")
    case = world.get("case")
    report = world.get("report")
    clue = world.get("clue")
    suspect = world.get("suspect")
    if tool.gives_answer:
        clue.meters["noticed"] += 1
        case.meters["solved"] += 1
        report.meters["missing"] = 0
        world.get("problem").meters["fixed"] += 1
    else:
        detective.memes["puzzled"] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "clubhouse": Setting("clubhouse", "the clubhouse field", True, True, "volley", "a happy crowd"),
    "green": Setting("green", "the village green", True, True, "volley", "families and neighbours"),
}

MYSTERIES = {
    "lost_ball": Mystery(
        "lost_ball",
        clue_kind="sand",
        missing_item="the red volley ball",
        found_place="under the snack table",
        cause="it rolled during the prize game",
        solution="look under the snack table",
        target_kind="ball",
        evidence="a trail of red dust",
        danger="the players could not start the next volley game",
    ),
    "missing_rope": Mystery(
        "missing_rope",
        clue_kind="chalk",
        missing_item="the jump rope",
        found_place="behind the bench",
        cause="someone moved it to keep the path clear",
        solution="check behind the bench",
        target_kind="rope",
        evidence="white chalk near the bench",
        danger="the team could not set up the practice lane",
    ),
    "lost_whistle": Mystery(
        "lost_whistle",
        clue_kind="paper",
        missing_item="the coach's whistle",
        found_place="in the towel basket",
        cause="it was tucked away with the clean towels",
        solution="search the towel basket",
        target_kind="whistle",
        evidence="a note on the towel hook",
        danger="the annual match could not begin on time",
    ),
}

TOOLS = {
    "magnifier": Tool("magnifier", "a magnifying glass", "study tiny clues"),
    "map": Tool("map", "a hand-drawn map", "follow the path of clues"),
    "label": Tool("label", "the right label list", "match clues to the owner", True),
    "ask": Tool("ask", "kind questions", "ask people where things were", True),
}

NAMES_GIRL = ["Aoife", "Mia", "Nora", "Lily", "Sinead", "Eva"]
NAMES_BOY = ["Finn", "Eamon", "Leo", "Tom", "Cian", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(sid, mid, tid) for sid in SETTINGS for mid in MYSTERIES for tid in TOOLS]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    detective: str
    detective_gender: str
    assistant: str
    assistant_gender: str
    guide: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with annual Irish problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--assistant")
    ap.add_argument("--assistant-gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting or args.mystery or args.tool:
        combos = [c for c in combos
                  if (args.setting is None or c[0] == args.setting)
                  and (args.mystery is None or c[1] == args.mystery)
                  and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool = rng.choice(sorted(combos))
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    ag = args.assistant_gender or ("boy" if dg == "girl" else "girl")
    detective = args.detective or _pick_name(rng, dg)
    assistant = args.assistant or _pick_name(rng, ag)
    guide = args.guide or rng.choice(["the coach", "a helper", "the keeper"])
    return StoryParams(setting, mystery, tool, detective, dg, assistant, ag, guide)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    world = World(setting)
    detective = world.add(Entity("detective", "character", params.detective_gender, params.detective, role="detective"))
    assistant = world.add(Entity("assistant", "character", params.assistant_gender, params.assistant, role="assistant"))
    guide = world.add(Entity("guide", "character", "adult", params.guide, role="guide"))
    report = world.add(Entity("report", "thing", "report", mystery.missing_item, attrs={"mystery": mystery.id}))
    clue = world.add(Entity("clue", "thing", "clue", mystery.clue_kind))
    suspect = world.add(Entity("suspect", "character", "adult", "the puzzled groundskeeper", role="suspect"))
    case = world.add(Entity("case", "thing", "case", "the mystery case"))
    problem = world.add(Entity("problem", "thing", "problem", mystery.danger))

    world.say(
        f"On the annual Irish volley day, {detective.id} and {assistant.id} arrived at {setting.place}. "
        f"The crowd was ready for the big volley match, but something was wrong."
    )
    world.say(
        f"{detective.id} noticed that {mystery.missing_item} was gone, and {mystery.evidence} sat nearby like a quiet clue."
    )
    world.para()
    world.say(
        f'"This is a case for us," said {detective.id}. {assistant.id} nodded, and together they began to {tool.use}.'
    )
    if tool.gives_answer:
        world.say(
            f"They used {tool.label} to ask the right questions and compare each clue with the list at hand."
        )
    else:
        world.say(
            f"They used {tool.label} to study the clues one by one, even the tiny ones hidden in the grass."
        )
    world.say(
        f"{mystery.danger.capitalize()}, so they kept looking until the trail pointed to {mystery.solution}."
    )
    simulate_search(world, mystery, tool, narrate=True)
    world.para()
    if case.meters["solved"] >= THRESHOLD:
        world.say(
            f"At last, they found {mystery.missing_item} {mystery.found_place}. "
            f"It had only been tucked away, not stolen, and the problem was solved."
        )
        world.say(
            f"{guide.label_word.capitalize()} smiled, the players cheered, and the annual volley game began at last."
        )
        world.say(
            f"{detective.id} and {assistant.id} stood by the line, happy to see the Irish crowd laughing again."
        )
    else:
        world.say(
            f"The case stayed unsolved, and the game could not begin."
        )
    world.facts.update(
        detective=detective,
        assistant=assistant,
        guide=guide,
        report=report,
        clue=clue,
        suspect=suspect,
        case=case,
        problem=problem,
        mystery=mystery,
        tool=tool,
        outcome="solved" if case.meters["solved"] >= THRESHOLD else "unsolved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a detective story about an annual Irish volley day where {f['mystery'].missing_item} goes missing and the children solve the problem.",
        f"Tell a child-friendly mystery set at the annual Irish volley event, where {f['detective'].id} uses clues to find what was lost.",
        f"Write a short problem-solving story that includes the words annual, Irish, and volley, and ends with the game starting again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    detective: Entity = f["detective"]
    assistant: Entity = f["assistant"]
    qa = [
        ("What kind of story is this?",
         f"It is a detective story about solving a small problem at an annual Irish volley day. The children do not give up; they follow clues until the missing thing is found."),
        ("What was missing?",
         f"{mystery.missing_item} was missing. That was the problem that stopped the game from starting."),
        ("How did the children solve it?",
         f"They looked carefully at the evidence and used {f['tool'].label} to search the right place. In the end, they found it where the clue said it would be."),
    ]
    if f["outcome"] == "solved":
        qa.append((
            f"Why did {detective.id} and {assistant.id} keep searching?",
            f"They knew the game could not begin until the missing item was found. Their careful searching turned a confusing problem into a solved one."
        ))
        qa.append((
            "How did the story end?",
            f"The annual volley game began again, and the crowd could cheer. The ending shows the problem was fixed, not just noticed."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a detective?",
         "A detective is a person who looks for clues and figures out what happened."),
        ("What does annual mean?",
         "Annual means it happens once every year."),
        ("What does Irish mean?",
         "Irish means it is from Ireland, or connected to Ireland and its people."),
        ("What is a volley in sport?",
         "A volley is a quick hit or pass in a game, often before the ball touches the ground."),
    ]


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
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.annual:
            lines.append(asp.fact("annual", sid))
        if s.irish:
            lines.append(asp.fact("irish", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing_item", mid, m.missing_item.replace(" ", "_")))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, T) :- setting(S), mystery(M), tool(T).
solved :- chosen_tool(T), helpful(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, tool=None, detective=None, detective_gender=None, assistant=None, assistant_gender=None, guide=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams("clubhouse", "lost_ball", "magnifier", "Aoife", "girl", "Finn", "boy", "the coach"),
    StoryParams("green", "missing_rope", "map", "Nora", "girl", "Eamon", "boy", "a helper"),
    StoryParams("clubhouse", "lost_whistle", "ask", "Cian", "boy", "Mia", "girl", "the keeper"),
]


def explain_rejection() -> str:
    return "(No story: the requested combination does not support a solvable detective problem.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting or args.mystery or args.tool:
        combos = [c for c in combos
                  if (args.setting is None or c[0] == args.setting)
                  and (args.mystery is None or c[1] == args.mystery)
                  and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, mystery, tool = rng.choice(sorted(combos))
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    ag = args.assistant_gender or ("boy" if dg == "girl" else "girl")
    detective = args.detective or _pick_name(rng, dg)
    assistant = args.assistant or _pick_name(rng, ag)
    guide = args.guide or rng.choice(["the coach", "a helper", "the keeper"])
    return StoryParams(setting, mystery, tool, detective, dg, assistant, ag, guide)


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective} and {p.assistant}: {p.setting} / {p.mystery} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
