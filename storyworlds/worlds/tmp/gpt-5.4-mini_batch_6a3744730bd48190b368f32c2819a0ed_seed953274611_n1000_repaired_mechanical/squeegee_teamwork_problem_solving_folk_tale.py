#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/squeegee_teamwork_problem_solving_folk_tale.py
===============================================================================

A tiny folk-tale storyworld about a child, a helper, a stubborn mess, and a
shared tool: a squeegee. The story keeps a clear classical shape:

- a simple need appears,
- the characters try a poor solution,
- teamwork and problem solving find a better way,
- the ending image shows the place made right again.

The world is small on purpose. It generates one of a few compatible scenarios
and simulates the change in state so the prose is driven by the world model, not
a frozen paragraph with swapped nouns.

Run:
    python storyworlds/worlds/gpt-5.4-mini/squeegee_teamwork_problem_solving_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/squeegee_teamwork_problem_solving_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4-mini/squeegee_teamwork_problem_solving_folk_tale.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
METER_KEYS = {"wetness", "stubbornness", "trust", "relief", "pride", "mess", "shine"}

HERO_NAMES = ["Mira", "Nell", "Oren", "Pip", "Suri", "Tomas", "Wren", "Ari"]
HELPER_NAMES = ["Gran", "Auntie", "Uncle", "Old Ben", "Moss", "Hana"]
PLACES = ["the mill path", "the market steps", "the barn floor", "the village well", "the bakehouse lane"]
PROBLEMS = {
    "flooded_steps": {
        "problem": "the stone steps were slick with rainwater",
        "mess": "wetness",
        "need": "dry the steps before anyone slipped",
        "ending": "the steps shone dry in the sun",
        "risk": "slipping on the stones",
    },
    "muddy_door": {
        "problem": "the front door had a thick coat of mud",
        "mess": "mess",
        "need": "clear the mud before it dried hard",
        "ending": "the door stood clean and bright again",
        "risk": "tracking mud into the house",
    },
    "foggy_window": {
        "problem": "the shop window had gone foggy with steam",
        "mess": "shine",
        "need": "wipe the glass so people could see the candles inside",
        "ending": "the window sparkled clear as a pond",
        "risk": "buyers missing the candles",
    },
}

TOOLS = {
    "cloth": {
        "label": "a soft cloth",
        "job": "rub the surface by hand",
        "weak": True,
        "better": False,
    },
    "broom": {
        "label": "a broom",
        "job": "sweep at the mess",
        "weak": True,
        "better": False,
    },
    "squeegee": {
        "label": "the squeegee",
        "job": "draw the water away in long clean strokes",
        "weak": False,
        "better": True,
    },
    "bucket": {
        "label": "a bucket",
        "job": "carry water from one place to another",
        "weak": True,
        "better": False,
    },
}

HELP_ACTIONS = {
    "hold": "hold the far side steady",
    "fetch": "fetch the tool from the shed",
    "guide": "guide the blade along the stone",
    "wipe": "wipe the last shining streaks away",
}

ASP_RULES = r"""
need_help(S) :- problem(S).
good_tool(squeegee).
bad_tool(cloth).
bad_tool(broom).
bad_tool(bucket).

solves(squeegee, flooded_steps).
solves(squeegee, muddy_door).
solves(squeegee, foggy_window).

needs_two_people(flooded_steps).
needs_two_people(muddy_door).
needs_two_people(foggy_window).

valid_scene(S, T) :- problem(S), solves(T, S), good_tool(T).
"""


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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    problem: str
    tool: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    place: str
    seed: Optional[int] = None
    use_two_people: bool = True
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def apply_rules(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for ent in list(world.entities.values()):
            if ent.meters["wetness"] >= THRESHOLD and ("wet_spread", ent.id) not in world.fired:
                world.fired.add(("wet_spread", ent.id))
                changed = True
                world.get("place").meters["danger"] += 1
                world.get("hero").memes["worry"] += 1
                world.get("helper").memes["worry"] += 1
            if ent.meters["mess"] >= THRESHOLD and ("mess_spread", ent.id) not in world.fired:
                world.fired.add(("mess_spread", ent.id))
                changed = True
                world.get("place").meters["tiredness"] += 1


def predict(problem_id: str, tool_id: str) -> dict:
    w = build_world(silent=True, params=StoryParams(
        problem=problem_id, tool=tool_id, hero="Mira", hero_type="girl",
        helper="Gran", helper_type="woman", place="the mill path"
    ))
    return {
        "solved": w.facts["solved"],
        "rescued": w.facts["rescued"],
    }


def story_for(problem: dict, tool: dict, params: StoryParams) -> World:
    w = build_world(silent=False, params=params)
    return w


def build_world(*, silent: bool, params: StoryParams) -> World:
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.place not in PLACES:
        raise StoryError("Unknown place.")

    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]

    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    place = world.add(Entity(id="place", kind="place", type="place", label=params.place))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool["label"]))
    hero.memes["hope"] += 1
    helper.memes["calm"] += 1

    world.say(
        f"Long ago, in {params.place}, {hero.id} and {helper.id} found that {problem['problem']}."
    )
    world.say(
        f'The little trouble was serious, because it could mean {problem["risk"]}.'
    )

    world.para()
    hero.memes["stubbornness"] += 1
    helper.memes["trust"] += 1
    world.say(f'{hero.id} said, "I can fix it myself with {tool["label"]}."')
    world.say(
        f'But {helper.id} shook {helper.pronoun("possessive")} head and said, '
        f'"That will only {tool["job"]}, not truly solve it."'
    )

    world.para()
    if params.tool != "squeegee":
        hero.memes["disappointment"] += 1
        helper.memes["thoughtful"] += 1
        world.say(
            f"So the two of them looked again. They tried to make do, but the trouble stayed."
        )
        world.say(
            f'At last {helper.id} said, "We need a better answer, not a quicker one."'
        )
        world.facts.update(solved=False, rescued=False, tool=tool_ent, problem=problem)
        return world

    hero.memes["trust"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"Then {helper.id} fetched {tool['label']}, and {hero.id} held one side while "
        f"{helper.id} held the other."
    )
    world.say(
        f"Together they used it to {tool['job']}, and in two careful turns the problem was gone."
    )
    world.say(
        f'By sunset, {problem["ending"]}.'
    )
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.facts.update(solved=True, rescued=True, tool=tool_ent, problem=problem)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, "squeegee") for p in PROBLEMS for t in TOOLS if t == "squeegee"]


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_scene/2."))
    return sorted(set(asp.atoms(model, "valid_scene")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("python:", sorted(py))
        print("clingo:", sorted(cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about teamwork, problem solving, and a squeegee.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["woman", "man"])
    ap.add_argument("--place", choices=PLACES)
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
    problem = args.problem or rng.choice(list(PROBLEMS))
    tool = args.tool or "squeegee"
    if tool != "squeegee":
        raise StoryError("This storyworld only tells a true teamwork story with a squeegee.")
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    place = args.place or rng.choice(PLACES)
    return StoryParams(problem=problem, tool=tool, hero=hero, hero_type=hero_type,
                       helper=helper, helper_type=helper_type, place=place)


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["problem"]
    return [
        QAItem(question="What was the trouble in the story?", answer=f"The trouble was that {p['problem']}. The children had to solve it so the place could be safe again."),
        QAItem(question="How did the two characters solve the problem?", answer="They worked side by side and used the squeegee together. One held it steady while the other helped guide it, so the water was cleared away."),
        QAItem(question="What changed by the end?", answer=f"By the end, {p['ending']}. The place looked calm and clean again, which proved their teamwork worked."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a squeegee for?", answer="A squeegee is a tool with a flat edge for pushing water away from a surface. People use it when they want glass or stone to dry cleanly."),
        QAItem(question="Why is teamwork useful?", answer="Teamwork is useful because two people can each do part of a hard job. When they combine their efforts, they often solve the problem faster and better."),
        QAItem(question="What does a good problem solver do first?", answer="A good problem solver looks at the trouble carefully before acting. Then they choose the tool or plan that truly fits the problem."),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    world = build_world(silent=False, params=params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a folk-tale-style story about teamwork and problem solving that includes the word squeegee.",
            f"Tell a short story where {params.hero} and {params.helper} work together to fix a stubborn mess with a squeegee.",
            "Make the ending show the place made clean again after careful cooperation.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            m = {k: v for k, v in e.meters.items() if v}
            mm = {k: v for k, v in e.memes.items() if v}
            if m:
                bits.append(f"meters={dict(m)}")
            if mm:
                bits.append(f"memes={dict(mm)}")
            if e.label:
                bits.append(f"label={e.label}")
            if e.role:
                bits.append(f"role={e.role}")
            print(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if qa:
        print()
        print("== Q&A ==")
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}\n")


CURATED = [
    StoryParams(problem="flooded_steps", tool="squeegee", hero="Mira", hero_type="girl",
                helper="Gran", helper_type="woman", place="the village well"),
    StoryParams(problem="muddy_door", tool="squeegee", hero="Pip", hero_type="boy",
                helper="Old Ben", helper_type="man", place="the bakehouse lane"),
    StoryParams(problem="foggy_window", tool="squeegee", hero="Suri", hero_type="girl",
                helper="Hana", helper_type="woman", place="the market steps"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_scene/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible scenes:")
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
