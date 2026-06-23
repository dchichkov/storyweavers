#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/continuous_work_teamwork_detective_story.py
==============================================================================================================

A small detective-story world about a team of helpers doing continuous work to
solve a missing-item case.

Seed premise:
- A child or small detective team notices a puzzle.
- The clues keep changing, so the work must be continuous.
- Teamwork helps the detectives gather evidence, test ideas, and find the answer.
- The ending should show a physical change: the missing thing is found, fixed,
  or put back where it belongs.

The world uses typed entities with physical meters and emotional memes, a
forward-chaining causal rule engine, a reasonableness gate, and an inline ASP
twin for parity checks.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    helper: str = ""
    location: str = ""
    portable: bool = False
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


@dataclass
class Place:
    id: str
    label: str
    clue_kind: str
    continuous_hint: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    label: str
    phrase: str
    missing_phrase: str
    suspicious_phrase: str
    clue_kind: str
    place_ok: set[str] = field(default_factory=set)
    requires_teamwork: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_phrase: str
    helps_with: set[str] = field(default_factory=set)


@dataclass
class TeamMove:
    id: str
    label: str
    phrase: str
    result_phrase: str
    fixes: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues_seen: int = 0

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.clues_seen = self.clues_seen
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_continuous_clue(world: World) -> list[str]:
    out: list[str] = []
    detective = world.facts["detective"]
    case = world.facts["case"]
    clue_tool = world.facts["tool"]
    if detective.memes["focus"] < THRESHOLD:
        return out
    sig = ("continuous_clue", case.id, clue_tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.meters["clues"] += 1
    detective.memes["confidence"] += 0.5
    world.clues_seen += 1
    out.append(
        f"{detective.id} noticed one more clue, and the work stayed continuous."
    )
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    team = world.facts["team"]
    case = world.facts["case"]
    if team.memes["helping"] < THRESHOLD:
        return out
    sig = ("teamwork", case.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    team.meters["done"] += 1
    team.memes["trust"] += 1
    out.append("The team shared clues, and their teamwork made the search faster.")
    return out


def _r_find_missing(world: World) -> list[str]:
    out: list[str] = []
    case = world.facts["case"]
    item = world.facts["missing"]
    if case.meters["solved"] >= THRESHOLD or item.meters["found"] >= THRESHOLD:
        return out
    if world.clues_seen < 2:
        return out
    sig = ("found", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["found"] += 1
    case.meters["solved"] += 1
    out.append(f"At last, the missing {item.label} turned up where everyone could see it.")
    return out


CAUSAL_RULES = [
    Rule("continuous_clue", "physical", _r_continuous_clue),
    Rule("teamwork", "social", _r_teamwork),
    Rule("find_missing", "physical", _r_find_missing),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_matches(place: Place, case: Case, tool: Tool, move: TeamMove) -> bool:
    return case.clue_kind == place.clue_kind and case.clue_kind in tool.helps_with and case.clue_kind in move.fixes


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for case_id, case in CASES.items():
            if place_id not in case.place_ok:
                continue
            for tool_id, tool in TOOLS.items():
                for move_id, move in MOVES.items():
                    if clue_matches(place, case, tool, move):
                        combos.append((place_id, case_id, tool_id, move_id))
    return combos


@dataclass
class StoryParams:
    place: str
    case: str
    tool: str
    move: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None


PLACES = {
    "library": Place(
        id="library",
        label="the library",
        clue_kind="quiet",
        continuous_hint="The quiet kept changing as pages turned and footsteps faded.",
        affords={"quiet"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        clue_kind="crumbs",
        continuous_hint="The crumbs kept appearing one by one near the table.",
        affords={"crumbs"},
    ),
    "playroom": Place(
        id="playroom",
        label="the playroom",
        clue_kind="tracks",
        continuous_hint="The floor showed tracks that stretched from toy to toy.",
        affords={"tracks"},
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        clue_kind="mud",
        continuous_hint="The mud held tiny prints, and more prints appeared after every step.",
        affords={"mud"},
    ),
}

CASES = {
    "missing_book": Case(
        id="missing_book",
        label="book",
        phrase="a missing storybook",
        missing_phrase="the storybook was gone",
        suspicious_phrase="a page was left open on the table",
        clue_kind="quiet",
        place_ok={"library"},
    ),
    "missing_cookie": Case(
        id="missing_cookie",
        label="cookie",
        phrase="a missing cookie tin",
        missing_phrase="the cookie tin was empty",
        suspicious_phrase="crumbs were scattered near the chair",
        clue_kind="crumbs",
        place_ok={"kitchen"},
    ),
    "missing_train": Case(
        id="missing_train",
        label="train",
        phrase="a missing toy train",
        missing_phrase="the toy train had rolled away",
        suspicious_phrase="little tracks crossed the rug",
        clue_kind="tracks",
        place_ok={"playroom"},
    ),
    "missing_boot": Case(
        id="missing_boot",
        label="boot",
        phrase="a missing muddy boot",
        missing_phrase="one boot was missing from the mat",
        suspicious_phrase="muddy prints led toward the flower bed",
        clue_kind="mud",
        place_ok={"garden"},
    ),
}

TOOLS = {
    "notebook": Tool(
        id="notebook",
        label="a notebook",
        phrase="a small notebook",
        use_phrase="wrote the clues in a small notebook",
        helps_with={"quiet", "crumbs", "tracks", "mud"},
    ),
    "lamp": Tool(
        id="lamp",
        label="a bright lamp",
        phrase="a bright lamp",
        use_phrase="shone a bright lamp over the clues",
        helps_with={"quiet", "crumbs", "tracks", "mud"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="a magnifier",
        phrase="a magnifier",
        use_phrase="looked closely with a magnifier",
        helps_with={"quiet", "crumbs", "tracks", "mud"},
    ),
}

MOVES = {
    "search_together": TeamMove(
        id="search_together",
        label="searching together",
        phrase="searched together",
        result_phrase="kept looking side by side",
        fixes={"quiet", "crumbs", "tracks", "mud"},
    ),
    "compare_notes": TeamMove(
        id="compare_notes",
        label="comparing notes",
        phrase="compared notes",
        result_phrase="put the clues together on one page",
        fixes={"quiet", "crumbs", "tracks", "mud"},
    ),
}

NAMES_GIRL = ["Mina", "Nora", "Lena", "Ivy", "Mia", "Ruby"]
NAMES_BOY = ["Eli", "Noah", "Theo", "Finn", "Owen", "Max"]
TRAITS = ["careful", "curious", "patient", "bright", "steady"]

CURATED = [
    StoryParams(place="library", case="missing_book", tool="magnifier", move="compare_notes",
                detective_name="Mina", detective_gender="girl",
                helper_name="Eli", helper_gender="boy",
                adult_name="Mr. Lane", adult_gender="man"),
    StoryParams(place="kitchen", case="missing_cookie", tool="notebook", move="search_together",
                detective_name="Noah", detective_gender="boy",
                helper_name="Ruby", helper_gender="girl",
                adult_name="Mom", adult_gender="woman"),
    StoryParams(place="playroom", case="missing_train", tool="lamp", move="compare_notes",
                detective_name="Ivy", detective_gender="girl",
                helper_name="Theo", helper_gender="boy",
                adult_name="Dad", adult_gender="man"),
    StoryParams(place="garden", case="missing_boot", tool="magnifier", move="search_together",
                detective_name="Finn", detective_gender="boy",
                helper_name="Mina", helper_gender="girl",
                adult_name="Aunt Jo", adult_gender="woman"),
]


def explain_rejection(place: Place, case: Case) -> str:
    return f"(No story: {case.label} does not fit {place.label}; choose a matching place and case.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det, helper, case, place, tool, move = f["detective"], f["helper"], f["case"], f["place"], f["tool"], f["move"]
    return [
        f'Write a detective story for a 3-to-5-year-old that uses the words "continuous" and "work".',
        f"Tell a gentle mystery where {det.id} and {helper.id} solve a missing {case.label} at {place.label} by doing continuous work together.",
        f"Write a short teamwork detective story where the clues keep changing, but {det.id} keeps working until the missing {case.label} is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, helper, adult = f["detective"], f["helper"], f["adult"]
    case, place, tool, move = f["case"], f["place"], f["tool"], f["move"]
    qa = [
        QAItem(
            question=f"What kind of story did {det.id} and {helper.id} have in {place.label}?",
            answer=f"It was a detective story about a missing {case.label} and a team that kept working until the answer showed up. They stayed on the case instead of giving up.",
        ),
        QAItem(
            question=f"What made the search need continuous work?",
            answer=f"The clue kept shifting around {place.label}, so one quick look was not enough. {det.id} had to keep checking again and again until the clue made sense.",
        ),
        QAItem(
            question=f"How did {det.id} and {helper.id} use teamwork?",
            answer=f"They shared clues, compared notes, and stayed side by side. That teamwork helped them notice the same pattern from two different angles.",
        ),
        QAItem(
            question=f"What did {tool.label} help them do?",
            answer=f"{tool.use_phrase}, which made the small clues easier to spot. It helped the team stay careful and keep their work moving.",
        ),
        QAItem(
            question=f"Who helped when the case was solved?",
            answer=f"{adult.id} helped by listening to the detectives and letting them finish their search. At the end, the adult saw that their steady work had paid off.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The missing {case.label} was found, and the search was no longer messy or uncertain. The team ended with the clues in order and the case solved.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {f["place"].clue_kind, f["case"].clue_kind}
    tags.add("teamwork")
    out: list[QAItem] = []
    if "quiet" in tags:
        out.append(QAItem(
            question="Why do detectives sometimes work quietly?",
            answer="Detectives work quietly so they can notice tiny details without missing them. Soft steps and careful listening help them catch clues.",
        ))
    if "crumbs" in tags:
        out.append(QAItem(
            question="What are crumbs?",
            answer="Crumbs are little pieces of food that fall off a snack or cookie. They can leave a trail that helps someone figure out where food was moved.",
        ))
    if "tracks" in tags:
        out.append(QAItem(
            question="What are tracks?",
            answer="Tracks are marks left behind by something that moved. They can show which way a toy or a person went.",
        ))
    if "mud" in tags:
        out.append(QAItem(
            question="Why are muddy prints easy to see?",
            answer="Muddy prints stand out because wet mud leaves a clear shape on the floor or ground. That makes them useful clues.",
        ))
    out.append(QAItem(
        question="What is teamwork?",
        answer="Teamwork means people help each other and share the work. When a team works together, they can solve a problem faster and more carefully.",
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  clues seen: {world.clues_seen}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def tell(place: Place, case: Case, tool: Tool, move: TeamMove, detective_name: str,
         detective_gender: str, helper_name: str, helper_gender: str,
         adult_name: str, adult_gender: str) -> World:
    world = World(place)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender,
                                 role="detective", traits=["steady"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper", traits=["curious"]))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender,
                             role="adult", traits=["helpful"]))
    missing = world.add(Entity(id="missing", type="thing", label=case.label, phrase=case.phrase,
                               owner=adult.id, hidden=True, portable=True))
    clue = world.add(Entity(id="clue", type="thing", label=f"{case.clue_kind} clue",
                            phrase=case.suspicious_phrase, location=place.label, portable=False))

    detective.memes["focus"] = 1.0
    helper.memes["helping"] = 1.0
    helper.memes["trust"] = 1.0
    adult.memes["calm"] = 1.0

    world.facts = {
        "detective": detective,
        "helper": helper,
        "adult": adult,
        "missing": missing,
        "clue": clue,
        "place": place,
        "case": case,
        "tool": tool,
        "move": move,
    }

    world.say(f"{detective.id} and {helper.id} came to {place.label} because {case.missing_phrase}.")
    world.say(place.continuous_hint)
    world.say(f"{detective.id} saw {case.suspicious_phrase}, and {helper.id} said they should keep working until the clue made sense.")
    world.para()
    detective.memes["focus"] += 1
    helper.memes["helping"] += 1
    world.say(f"{detective.id} used {tool.phrase} and {move.phrase}.")
    propagate(world, narrate=True)
    if missing.meters["found"] >= THRESHOLD:
        world.para()
        detective.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say(f"{adult.id} smiled when they saw the {case.label} back in view, and the team finished the work together.")
        world.say(f"By the end, {case.label} was no longer missing; it sat right where it belonged.")
    else:
        world.para()
        world.say(f"They kept searching, and the case stayed open for one more careful look.")
    world.facts["solved"] = case.meters["solved"] >= THRESHOLD
    return world


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("clue_kind", pid, p.clue_kind))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("case_clue", cid, c.clue_kind))
        for p in sorted(c.place_ok):
            lines.append(asp.fact("case_place", cid, p))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for k in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, k))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        for k in sorted(m.fixes):
            lines.append(asp.fact("fixes", mid, k))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,T,M) :- place(P), case(C), tool(T), move(M),
                  case_place(C,P), clue_kind(P,K), case_clue(C,K),
                  helps(T,K), fixes(M,K).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    ok = True
    if python_set != clingo_set:
        ok = False
        print("MISMATCH between ASP and Python valid_combos():")
        print(" only in python:", sorted(python_set - clingo_set))
        print(" only in clingo:", sorted(clingo_set - python_set))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, case=None, tool=None, move=None), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective teamwork story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--adult-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy", "mother", "father", "woman", "man"])
    ap.add_argument("--helper-gender", choices=["girl", "boy", "mother", "father", "woman", "man"])
    ap.add_argument("--adult-gender", choices=["woman", "man", "mother", "father"])
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
              if (args.place is None or c[0] == args.place)
              and (args.case is None or c[1] == args.case)
              and (args.tool is None or c[2] == args.tool)
              and (args.move is None or c[3] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, case, tool, move = rng.choice(sorted(combos))
    if args.detective_gender:
        dg = args.detective_gender
    else:
        dg = rng.choice(["girl", "boy"])
    if args.helper_gender:
        hg = args.helper_gender
    else:
        hg = "boy" if dg == "girl" else "girl"
    ag = args.adult_gender or rng.choice(["woman", "man"])
    det_name = args.detective_name or rng.choice(NAMES_GIRL if dg in {"girl", "woman", "mother"} else NAMES_BOY)
    helper_name = args.helper_name or rng.choice([n for n in (NAMES_GIRL if hg in {"girl", "woman", "mother"} else NAMES_BOY) if n != det_name])
    adult_name = args.adult_name or rng.choice(["Mom", "Dad", "Aunt May", "Mr. Lane", "Ms. Bell"])
    return StoryParams(
        place=place,
        case=case,
        tool=tool,
        move=move,
        detective_name=det_name,
        detective_gender=dg,
        helper_name=helper_name,
        helper_gender=hg,
        adult_name=adult_name,
        adult_gender=ag,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    case = CASES[params.case]
    tool = TOOLS[params.tool]
    move = MOVES[params.move]
    if params.place not in place.id:
        pass
    if params.place not in case.place_ok or not clue_matches(place, case, tool, move):
        raise StoryError("Invalid story parameters for this detective world.")
    world = tell(place, case, tool, move, params.detective_name, params.detective_gender,
                 params.helper_name, params.helper_gender, params.adult_name, params.adult_gender)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
