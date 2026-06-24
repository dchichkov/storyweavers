#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T073613Z_seed779406221_n50/shorts_nipple_curiosity_teamwork_detective_story.py
===============================================================================================================

A small standalone story world for a child-friendly detective tale about
curiosity and teamwork. Two young sleuths follow clues through a tiny neighborhood
case: a pair of missing shorts, a loose bicycle nipple cap, and a trail of
careful observations that lead to a kind, complete resolution.

The world models typed entities with physical meters and emotional memes, uses a
forward-chaining causal trace, and includes a lightweight ASP twin for parity
checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""
    found_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little street"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    hint: str
    location: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    location: str
    owner_kind: str = "child"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helper: str
    fixes: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.entities.get("detective")
    if not seeker:
        return out
    if seeker.memes.get("curiosity", 0) < THRESHOLD:
        return out
    sig = ("search",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.meters["search"] = 1
    out.append("The detective kept looking carefully for a clue.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("detective")
    b = world.entities.get("helper")
    if not a or not b:
        return out
    if a.memes.get("teamwork", 0) < THRESHOLD or b.memes.get("teamwork", 0) < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["trust"] = a.memes.get("trust", 0) + 1
    b.memes["trust"] = b.memes.get("trust", 0) + 1
    out.append("The two helpers worked side by side like a tiny detective team.")
    return out


CAUSAL_RULES = [_r_search, _r_teamwork]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about curiosity and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


@dataclass
class StoryParams:
    setting: str
    case: str
    prize: str
    tool: str
    name: str
    helper_name: str
    seed: Optional[int] = None


SETTINGS = {
    "street": Setting(place="the little street", affords={"search", "repair"}),
    "schoolyard": Setting(place="the schoolyard", affords={"search", "repair"}),
    "garden": Setting(place="the garden path", affords={"search", "repair"}),
}

CASES = {
    "missing_shorts": Clue(id="clue1", label="the missing shorts", hint="a small cloth clue", location="under a bench"),
    "lost_note": Clue(id="clue2", label="the lost note", hint="a paper clue", location="near a gate"),
    "tiny_gap": Clue(id="clue3", label="the tiny gap", hint="a broken-place clue", location="by a bicycle"),
}

PRIZES = {
    "shorts": Prize(id="shorts", label="shorts", phrase="a pair of blue shorts", location="on a clothesline"),
    "badge": Prize(id="badge", label="badge", phrase="a shiny detective badge", location="in a pocket"),
    "ball": Prize(id="ball", label="ball", phrase="a red rubber ball", location="under a chair"),
}

TOOLS = {
    "magnifier": Tool(id="magnifier", label="magnifying glass", phrase="a magnifying glass", helper="look closer", fixes="shows small clues"),
    "notes": Tool(id="notes", label="notebook", phrase="a little notebook", helper="write clues down", fixes="keeps clues in order"),
    "pump": Tool(id="pump", label="bicycle pump", phrase="a bicycle pump", helper="check the wheel", fixes="reaches the tiny nipple valve"),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Lena", "Zoe", "Ivy"]
BOY_NAMES = ["Leo", "Max", "Ben", "Theo", "Sam", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CASES:
            for p in PRIZES:
                if p == "shorts" and c == "missing_shorts":
                    out.append((s, c, p))
                if p == "ball" and c == "lost_note":
                    out.append((s, c, p))
                if p == "badge" and c == "tiny_gap":
                    out.append((s, c, p))
    return out


def explain_rejection(case: Clue, prize: Prize) -> str:
    return f"(No story: {case.label} does not fit a case about {prize.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.case is None or c[1] == args.case)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, case, prize = rng.choice(sorted(combos))
    tool = args.tool or ("pump" if case == "tiny_gap" else rng.choice(sorted(TOOLS)))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    return StoryParams(setting=setting, case=case, prize=prize, tool=tool, name=name, helper_name=helper)


def tell(setting: Setting, case: Clue, prize: Prize, tool: Tool, name: str, helper_name: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id="detective", kind="character", type="girl" if name in GIRL_NAMES else "boy", label=name))
    helper = world.add(Entity(id="helper", kind="character", type="girl" if helper_name in GIRL_NAMES else "boy", label=helper_name))
    clue = world.add(Entity(id="clue", label=case.label, location=case.location))
    prize_ent = world.add(Entity(id="prize", label=prize.label, location=prize.location, owner="child"))
    tool_ent = world.add(Entity(id="tool", label=tool.label, location="the toolbox"))

    detective.memes["curiosity"] = 1
    detective.memes["teamwork"] = 1
    helper.memes["teamwork"] = 1

    world.say(f"{name} was a little detective who loved curiosity and teamwork.")
    world.say(f"One day, {name} and {helper_name} got a case about {case.label} and a pair of {prize.label}.")
    world.say(f"They followed clues through {setting.place}, because a good detective does not give up when something goes missing.")

    world.para()
    world.say(f"{name} spotted a clue near {case.location}. It was {case.hint}, and it made {name} curious.")
    world.say(f"{helper_name} helped {name} look again, so they could work as a team.")
    propagate(world)

    world.para()
    if case.id == "clue3":
        world.say(f"At a bicycle, they found a tiny nipple valve that had come loose.")
        world.say(f"{tool.phrase} helped them check the wheel, and {helper_name} held the light steady.")
        prize_ent.location = "back with the bicycle owner"
    else:
        world.say(f"Under the bench, they found the missing clue and noticed where the {prize.label} belonged.")
        prize_ent.location = "back where it belonged"

    world.para()
    detective.memes["joy"] = 1
    helper.memes["joy"] = 1
    world.say(f"In the end, {name} and {helper_name} solved the case together.")
    if prize.id == "shorts":
        world.say(f"The missing shorts went back on the clothesline, and the whole street looked neat again.")
    elif prize.id == "ball":
        world.say(f"The red ball rolled safely home, and the friends smiled at their tidy notes.")
    else:
        world.say(f"The shiny badge stayed safe in its pocket, and the little detectives grinned at each other.")

    world.facts.update(detective=detective, helper=helper, clue=clue, prize=prize_ent, tool=tool_ent, case=case, prize_cfg=prize, tool_cfg=tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child about {f["case"].label} and {f["prize_cfg"].label}, with curiosity and teamwork.',
        f"Tell a child-friendly mystery where {f['detective'].label} and {f['helper'].label} search for {f['prize_cfg'].phrase} using clues.",
        f'Write a simple detective tale that includes the words "{f["prize_cfg"].label}" and "nipple" and ends with teamwork.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"].label
    h = f["helper"].label
    case = f["case"].label
    prize = f["prize_cfg"].label
    return [
        QAItem(question=f"Who are the story's detectives?", answer=f"The story is about {d} and {h}, two small detectives who solved a case together."),
        QAItem(question=f"What were they looking for?", answer=f"They were looking for {prize}, and they followed clues to figure out where it belonged."),
        QAItem(question=f"Why did they keep searching?", answer=f"They stayed curious and worked as a team, so they kept looking until the mystery was solved."),
        QAItem(question=f"What clue did they notice in the case about {case}?", answer=f"They noticed a helpful clue, and that clue pointed them toward the right place."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(question="What does a detective do?", answer="A detective looks closely at clues and asks careful questions to solve a mystery."),
        QAItem(question="What is curiosity?", answer="Curiosity is the wish to learn more, notice details, and keep asking questions."),
        QAItem(question="What is teamwork?", answer="Teamwork means people help each other and do a job together."),
    ]
    if f["prize_cfg"].label == "shorts":
        out.append(QAItem(question="What are shorts?", answer="Shorts are short pants that people wear when the weather is warm.")) 
    out.append(QAItem(question="What is a nipple valve on a bicycle?", answer="A nipple valve is a tiny part on a bicycle wheel where air goes in, and it helps keep the tire full and round."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,P) :- setting(S), case(C), prize(P).
contains_short(C) :- case(C), C = missing_shorts.
contains_nipple(C) :- case(C), C = tiny_gap.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CASES:
        lines.append(asp.fact("case", c))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


CURATED = [
    StoryParams(setting="street", case="missing_shorts", prize="shorts", tool="magnifier", name="Mia", helper_name="Leo"),
    StoryParams(setting="schoolyard", case="lost_note", prize="ball", tool="notes", name="Ben", helper_name="Ava"),
    StoryParams(setting="garden", case="tiny_gap", prize="badge", tool="pump", name="Nora", helper_name="Theo"),
]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        if e.memes or e.meters:
            lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} location={e.location}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CASES[params.case], PRIZES[params.prize], TOOLS[params.tool], params.name, params.helper_name)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        print(asp_valid_combos())
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            samples.append(generate(p))
    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
