#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/direction_bad_ending_rhyme_problem_solving_fable.py
===================================================================================

A small fable-like storyworld about a direction sign, a rhyme-loving problem,
and a choice that goes wrong. The world simulates a tiny cast, their physical
state in meters, their feelings in memes, and a simple causal arc:

- a traveler needs direction,
- a showy rhyme leads them astray,
- a practical helper offers problem solving,
- but in the bad-ending branch, the traveler still ignores the help,
- and the ending image proves what changed.

The stories are intentionally brief, child-facing, concrete, and state-driven.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"bird", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



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
    terrain: str
    danger: str
    safe_path: str
    lost_path: str

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
    word: str
    rhyme: str
    lure: str
    wrong_turn: str
    effect: str
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
class Guide:
    id: str
    label: str
    method: str
    warning: str
    rescue_attempt: str
    usable: bool = True
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "forest": Setting("forest", "the deep wood", "leafy paths", "the north trail", "the mossy path", "the stone path"),
    "meadow": Setting("meadow", "the bright meadow", "open grass", "the east lane", "the narrow lane", "the wide road"),
    "river": Setting("river", "the riverbank", "wet reeds", "the bend in the bank", "the safe bridge path", "the slippery bank"),
}

PROBLEMS = {
    "echo": Problem("echo", "direction", "lection", "a singing echo", "follow the rhyme", "wander farther away", {"rhyme", "direction"}),
    "moth": Problem("moth", "direction", "affection", "a dancing moth song", "follow the flutter", "circle in confusion", {"rhyme"}),
    "wind": Problem("wind", "direction", "situation", "a breezy tune", "trust the tune", "lose the trail", {"rhyme", "direction"}),
}

GUIDES = {
    "map": Guide("map", "a little map", "look for the marked path", "Look for the sign, not the song.", "study the turn and choose the safe path", True, {"problem_solving"}),
    "stones": Guide("stones", "stacked stones", "count the stone trail", "The stones point the way.", "follow the stones one by one", True, {"problem_solving"}),
    "ask": Guide("ask", "a wise rabbit", "ask the rabbit for help", "Ask first, then walk.", "ask for direction and listen carefully", True, {"problem_solving"}),
}

TRAVELERS = [
    ("Milo", "boy"),
    ("Nina", "girl"),
    ("Pip", "bird"),
    ("Tara", "girl"),
    ("Bram", "boy"),
]


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    guide: str
    traveler: str
    traveler_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for pid, p in PROBLEMS.items():
            for gid, g in GUIDES.items():
                if "direction" in p.tags and g.usable and "problem_solving" in g.tags:
                    combos.append((sid, pid, gid))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if "direction" in p.tags:
            lines.append(asp.fact("needs_direction", pid))
    for gid, g in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        if g.usable:
            lines.append(asp.fact("usable", gid))
        if "problem_solving" in g.tags:
            lines.append(asp.fact("problem_solving", gid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,G) :- setting(S), problem(P), guide(G), needs_direction(P), usable(G), problem_solving(G).
"""


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable-like storyworld about direction, rhyme, and bad choices.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--type", choices=["boy", "girl", "bird"])
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
              and (args.guide is None or c[2] == args.guide)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, pid, gid = rng.choice(sorted(combos))
    traveler = args.name or rng.choice([n for n, _ in TRAVELERS])
    ttype = args.type or dict(TRAVELERS).get(traveler, rng.choice(["boy", "girl", "bird"]))
    return StoryParams(sid, pid, gid, traveler, ttype)


def _setup(world: World, traveler: Entity, setting: Setting, problem: Problem) -> None:
    traveler.memes["curiosity"] = 1.0
    world.say(f"{traveler.id} went into {setting.place} where {setting.terrain} rustled softly.")
    world.say(f"{traveler.id} was looking for {setting.safe_path}, but {setting.danger} made the way hard to see.")
    world.say(f"Then a sly little rhyme came drifting by: “{problem.rhyme}, {problem.rhyme}!”")


def _tempt(world: World, traveler: Entity, problem: Problem) -> None:
    traveler.memes["interest"] = 1.0
    world.say(f"The rhyme was {problem.lure}, and {traveler.id} forgot to look at the path.")
    world.say(f'"Maybe this song knows the way," {traveler.id} said, and {traveler.pronoun()} stepped toward {problem.wrong_turn}.')


def _warn(world: World, guide: Entity, problem: Problem, setting: Setting) -> None:
    guide.memes["care"] = 1.0
    world.say(f'{guide.label} tried to help. "{guide.attrs["warning"]}" {guide.pronoun()} called.')
    world.say(f"{guide.id} pointed to {setting.safe_path} and showed how to choose direction without guessing.")


def _bad_turn(world: World, traveler: Entity, problem: Problem, setting: Setting) -> None:
    traveler.meters["lost"] = 1.0
    traveler.memes["pride"] = 1.0
    world.say(f"But {traveler.id} stayed on {problem.wrong_turn} anyway.")
    world.say(f"The rhyme led {traveler.pronoun('object')} to {setting.lost_path}, where {problem.effect}.")
    world.say(f"By dusk, {traveler.id} had no clear direction left, only a tired heart and a dim trail.")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    guide_cfg = GUIDES[params.guide]
    traveler = world.add(Entity(id=params.traveler, kind="character", type=params.traveler_type, role="traveler"))
    guide = world.add(Entity(id="Guide", kind="character", type="rabbit", label=guide_cfg.label, role="guide", attrs={"warning": guide_cfg.warning}))
    world.add(Entity(id="path", type="path", label=setting.safe_path))
    _setup(world, traveler, setting, problem)
    world.para()
    _tempt(world, traveler, problem)
    _warn(world, guide, problem, setting)
    world.para()
    _bad_turn(world, traveler, problem, setting)
    world.para()
    world.say(f"In the end, the wise lesson was plain: a pretty rhyme is not the same as direction.")
    world.say(f"If the path is hard to see, a good question is better than a clever song.")
    world.facts.update(setting=setting, problem=problem, guide=guide_cfg, traveler=traveler, outcome="bad")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small fable for a child that includes the word "{f["problem"].word}" and a rhyming clue that goes wrong.',
        f"Tell a problem-solving fable where a traveler needs direction, hears a rhyme, and makes a bad choice anyway.",
        f"Write a story about {f['traveler'].id} learning that a song is not the same as direction.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    t = f["traveler"]
    p = f["problem"]
    s = f["setting"]
    g = f["guide"]
    return [
        QAItem(question="Who was the story about?", answer=f"It was about {t.id}, who needed direction in {s.place}."),
        QAItem(question="What problem caused trouble?", answer=f"A rhyme about {p.word} distracted {t.id} and made the choice go wrong."),
        QAItem(question=f"What did {g.label} try to do?", answer=f"{g.label.capitalize()} tried to help by giving a better way to think about direction. The help was practical, but {t.id} did not follow it."),
        QAItem(question="How did the story end?", answer=f"It ended badly. {t.id} ended up lost, and the ending image shows that the safe path was left behind."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is direction?", answer="Direction is the way something should go. It helps you choose where to walk next."),
        QAItem(question="What is a rhyme?", answer="A rhyme is a sound pattern in words where the endings match or nearly match."),
        QAItem(question="What does problem solving mean?", answer="Problem solving means thinking carefully about a trouble and choosing a useful way to fix or handle it."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("forest", "echo", "map", "Milo", "boy"),
    StoryParams("meadow", "moth", "stones", "Nina", "girl"),
    StoryParams("river", "wind", "ask", "Pip", "bird"),
]


def generate(params: StoryParams) -> StorySample:
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


def outcome_of(params: StoryParams) -> str:
    return "bad"


def asp_verify() -> int:
    import asp
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    rc = 0
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        print("MISMATCH in the gate:")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
