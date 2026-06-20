#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/practical_hold_vertical_teamwork_fable.py
=========================================================================

A standalone storyworld for a tiny fable about practical teamwork: two small
characters face a vertical problem, choose a practical way to help each other,
and end with a clear change in the world.

Seed words:
- practical
- hold
- vertical

Style:
- Fable
- Teamwork
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"goat", "she-goat", "doe", "mule"}
        male = {"goat-buck", "buck", "rooster", "fox", "donkey", "mule"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



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
    vertical: bool
    detail: str

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
class Problem:
    id: str
    need: str
    obstacle: str
    risk: str
    vertical: bool = True

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
class TeamMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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
@dataclass
class StoryParams:
    setting: str
    problem: str
    move: str
    helper: str
    lead: str
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


SETTINGS = {
    "hill": Setting("hill", "the hill path", True, "A steep path rose above the river."),
    "wall": Setting("wall", "the stone wall", True, "Tall stones made a vertical climb."),
    "tree": Setting("tree", "the old tree", True, "Its trunk went straight up to the sky."),
}

PROBLEMS = {
    "apple": Problem("apple", "reach the ripe apple", "a high branch", "the fruit might fall"),
    "bell": Problem("bell", "ring the village bell", "the bell rope", "the bell was far above their heads"),
    "lantern": Problem("lantern", "hang the lantern safely", "the hook", "the light could drop and break"),
}

MOVES = {
    "stack": TeamMove("stack", 3, 3, "stacked together in the practical way", "tried to stretch alone, but could not reach",
                      "stacked together in the practical way and reached it at last"),
    "pole": TeamMove("pole", 2, 2, "held a long pole steady for each other", "pulled and wobbled, but the pole slipped",
                     "held a long pole steady for each other until the job was done"),
    "lift": TeamMove("lift", 3, 3, "lifted one another carefully", "lifted too fast and only tipped the basket",
                     "lifted one another carefully and solved the problem"),
}

NAMES = ["Mina", "Tobin", "Lio", "Pera", "Rook", "Nia", "Sage", "Kellan"]
KIND_NAMES = {
    "fox": ("fox", "fox"),
    "goat": ("goat", "goat"),
    "mule": ("mule", "mule"),
    "donkey": ("donkey", "donkey"),
    "rooster": ("rooster", "rooster"),
}

KNOWLEDGE = {
    "practical": [("What does practical mean?",
                   "Practical means useful and sensible. A practical idea helps solve a real problem.")],
    "vertical": [("What does vertical mean?",
                  "Vertical means standing straight up and down, like a ladder or a tree trunk.")],
    "teamwork": [("What is teamwork?",
                  "Teamwork is when people help each other and work together to do something hard.")],
    "hold": [("What does it mean to hold something steady?",
               "It means to keep it still so it will not wobble or fall.")],
    "fable": [("What is a fable?",
                "A fable is a short story that teaches a lesson, often with animals as the characters.")],
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        if not s.vertical:
            continue
        for pid, p in PROBLEMS.items():
            if not p.vertical:
                continue
            for mid, m in MOVES.items():
                if m.sense >= 2:
                    out.append((sid, pid, mid))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("vertical_problem", pid))
    for mid, mv in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("sense", mid, mv.sense))
        lines.append(asp.fact("power", mid, mv.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, M) :- setting(S), problem(P), vertical_problem(P), move(M), sense(M, N), sense_min(K), N >= K.
chosen(S, P, M) :- valid(S, P, M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    if ok:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combinations.")
        return 1
    params = CURATED[0]
    try:
        sample = generate(params)
        assert sample.story
        print("OK: smoke test generated a story.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about practical teamwork on a vertical challenge.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--helper", choices=NAMES)
    ap.add_argument("--kind", choices=list(KIND_NAMES))
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
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, move = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    return StoryParams(setting=setting, problem=problem, move=move, helper=helper, lead=hero)


def _build_world(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    move = MOVES[params.move]
    hero = world.add(Entity(params.lead, kind="character", type="goat", role="lead", traits=["practical"]))
    helper = world.add(Entity(params.helper, kind="character", type="goat", role="helper", traits=["steady"]))
    world.add(Entity("place", type="place", label=setting.place))
    world.facts.update(setting=setting, problem=problem, move=move, hero=hero, helper=helper)
    hero.memes["hope"] = 1.0
    helper.memes["trust"] = 1.0
    world.say(f"Once there was a practical little goat named {hero.id}, and {helper.id} was a steady friend.")
    world.say(f"They came to {setting.place}, where {setting.detail} {problem.obstacle} made the task hard.")
    world.para()
    world.say(f"{hero.id} wanted to {problem.need}, but {problem.risk}.")
    world.say(f"{helper.id} nodded, because together they could think of a better way.")
    world.para()
    world.say(f'“Let us be practical,” said {hero.id}. “We can {move.text}.”')
    world.say(f"So they did: {move.qa_text}.")
    hero.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    world.say(f"The {setting.id} seemed less steep after that, and the two friends smiled at the clever result.")
    world.say("The fable ended with a lesson: the practical way is often the one that uses teamwork.")
    world.facts["outcome"] = "successful"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a child that includes the words "practical", "hold", and "vertical".',
        f"Tell a teamwork story where {f['hero'].id} and {f['helper'].id} face a vertical problem at {f['setting'].place} and solve it in a practical way.",
        f"Write a short animal fable where two friends hold something steady and work together to reach a high place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, setting, problem, move = f["hero"], f["helper"], f["setting"], f["problem"], f["move"]
    return [
        QAItem(question="Who is the story about?",
               answer=f"It is about {hero.id} and {helper.id}, two friends who had to solve a hard problem together."),
        QAItem(question="What problem did they face?",
               answer=f"They had to {problem.need}, and the problem was high up on something vertical. That made teamwork useful."),
        QAItem(question="How did they solve it?",
               answer=f"They chose a practical plan and {move.qa_text}. They worked together instead of trying to manage alone."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for tag in ["practical", "hold", "vertical", "teamwork", "fable"]:
        if tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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


CURATED = [
    StoryParams("hill", "apple", "stack", "Mina", "Tobin"),
    StoryParams("wall", "bell", "pole", "Rook", "Nia"),
    StoryParams("tree", "lantern", "lift", "Sage", "Kellan"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible (setting, problem, move) combos:\n")
        for s, p, m in models:
            print(f"  {s:8} {p:8} {m}")
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
            header = f"### {p.lead} & {p.helper}: {p.move} on {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
