#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/name_gondola_compact_problem_solving_rhyme_pirate.py
=====================================================================================

A compact storyworld in a pirate-tale style about a child, a gondola, and a
name plaque that gets lost, bent, or muddled. The story always reaches a small
problem-solving turn and ends with a child-friendly rhyme.

Seed words:
- name
- gondola
- compact

Style:
- Pirate Tale

Features:
- Problem Solving
- Rhyme
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    sound: str
    water: str
    breeze: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Problem:
    id: str
    title: str
    cause: str
    consequence: str
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
class Solution:
    id: str
    title: str
    method: str
    result: str
    rhyme: str
    power: int
    sense: int
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "canal": Setting("canal", "a moonlit canal", "the water tapped the docks", "water", "a salt breeze"),
    "harbor": Setting("harbor", "the harbor", "ropes creaked on the mast", "water", "a brisk breeze"),
    "isle": Setting("isle", "a tiny island harbor", "the gulls sang over the pier", "water", "a warm breeze"),
}

PROBLEMS = {
    "lost_name": Problem("lost_name", "a lost name plaque", "the plaque slipped from the gondola rail", "no one knew whose gondola it was", {"name", "gondola"}),
    "split_rope": Problem("split_rope", "a split rope loop", "the rope frayed near the knot", "the gondola could not stay tidy on the dock", {"gondola"}),
    "bent_compact": Problem("bent_compact", "a bent compact sign", "the compact sign got bent in the wind", "the label could not be read from the pier", {"compact", "name"}),
}

SOLUTIONS = {
    "paint_name": Solution(
        id="paint_name",
        title="paint a fresh name",
        method="painted the name again in bold black letters",
        result="the name shone clear on the gondola side",
        rhyme="A bright new name, a steady aim; the pirate boat could keep its claim.",
        power=1,
        sense=3,
        tags={"name", "gondola"},
    ),
    "tighten_rope": Solution(
        id="tighten_rope",
        title="tighten the rope",
        method="tied the rope tighter with a neat little knot",
        result="the gondola sat firm beside the dock",
        rhyme="A tidy knot, a careful shot; the little boat would wobble not.",
        power=2,
        sense=3,
        tags={"gondola"},
    ),
    "wax_compact": Solution(
        id="wax_compact",
        title="smooth the compact sign",
        method="smoothed the compact sign with a bit of wax and a cloth",
        result="the short sign gleamed and could be read again",
        rhyme="A compact sign, now clear and fine; the words came back in a shiny line.",
        power=1,
        sense=2,
        tags={"compact", "name"},
    ),
}

NAMES = ["Mira", "Ned", "Pip", "Lina", "Jory", "Tess", "Bram", "Iris"]
TRAITS = ["brave", "quick", "cheerful", "clever", "curious"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    solution: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    captain: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for sol in SOLUTIONS.values():
                if p in {"lost_name", "bent_compact"} and sol.tags & PROBLEMS[p].tags:
                    combos.append((s, p, sol.id))
                elif p == "split_rope" and sol.id == "tighten_rope":
                    combos.append((s, p, sol.id))
    return combos


def reasonableness_ok(problem: Problem, solution: Solution) -> bool:
    return bool(problem.tags & solution.tags) or (problem.id == "split_rope" and solution.id == "tighten_rope")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.solution:
        if args.problem not in PROBLEMS or args.solution not in SOLUTIONS:
            raise StoryError("Unknown problem or solution.")
        if not reasonableness_ok(PROBLEMS[args.problem], SOLUTIONS[args.solution]):
            raise StoryError("That solution does not actually fix that problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, solution = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    captain = args.captain or rng.choice(["Captain", "Bosun", "Old Salt"])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        problem=problem,
        solution=solution,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        captain=captain,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a compact problem-solving rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--captain")
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


def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    solution = SOLUTIONS[params.solution]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero", attrs={"trait": "curious"}))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", attrs={"trait": "clever"}))
    gondola = world.add(Entity(id="gondola", kind="thing", type="boat", label="gondola", tags={"gondola"}))
    nameplate = world.add(Entity(id="name", kind="thing", type="sign", label="name", tags={"name"}))
    compact = world.add(Entity(id="compact", kind="thing", type="sign", label="compact", tags={"compact"}))
    world.facts.update(problem=problem, solution=solution, hero=hero, helper=helper, gondola=gondola, nameplate=nameplate, compact=compact)
    return world


def tell(world: World, params: StoryParams) -> None:
    p = PROBLEMS[params.problem]
    s = SOLUTIONS[params.solution]
    hero = world.get(params.hero)
    helper = world.get(params.helper)
    world.say(
        f"On a bright tide, {hero.id} and {helper.id} came to {world.setting.place}. "
        f"{world.setting.sound} and the little gondola waited by the post."
    )
    world.say(
        f'{"Captain"} {params.hero} tipped a finger at the boat. "Our {p.title} has us in a twist," '
        f'said {helper.id}. "The {p.consequence}."'
    )
    world.para()
    world.say(
        f"{hero.id} peered close and found the trouble: {p.cause}. "
        f"{helper.id} nodded. " 
        f'"We need a tidy fix," {helper.id} said, "and not a mighty trick."'
    )
    world.say(
        f"{hero.id} rummaged in a compact little chest and chose to {s.method}. "
        f"{helper.id} held the lantern steady and hummed a sea-song rhyme."
    )
    world.para()
    world.say(
        f"At last, {s.result}. {helper.id} laughed, and the boat looked proud as a gull."
    )
    world.say(f'"{s.rhyme}" sang {hero.id}, and the harbor answered back in time.')
    world.facts["outcome"] = "fixed"


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    s = world.facts["solution"]
    return [
        f'Write a pirate tale for a young child that uses the words "name", "gondola", and "compact".',
        f"Tell a short story where a child on a gondola spots {p.title} and solves it with a compact, clever fix.",
        f"Write a rhyming pirate story where the problem is solved by {s.method}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["problem"]
    s = world.facts["solution"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question="What was the problem in the story?",
            answer=f"The problem was {p.title}. It happened because {p.cause}, so the gondola could not be read or trusted until someone fixed it.",
        ),
        QAItem(
            question="How did they solve it?",
            answer=f"{hero.id} and {helper.id} solved it by {s.method}. That worked because it matched the problem and made the gondola clear and ready again.",
        ),
        QAItem(
            question=f"Why did {helper.id} help?",
            answer=f"{helper.id} helped because the little boat needed a careful fix. Together they could see the problem, choose a sensible plan, and finish the job safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gondola?",
            answer="A gondola is a small boat that rides on water. In a pirate tale, it can carry people, ropes, and signs from one dock to another.",
        ),
        QAItem(
            question="What does compact mean?",
            answer="Compact means small and neatly packed together. A compact thing fits in a small space and is easy to carry.",
        ),
        QAItem(
            question="Why do pirates like clear names on boats?",
            answer="Clear names help people know which boat is which. That makes it easier to find the right boat, keep track of it, and give it back to the right crew.",
        ),
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
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,R) :- setting(S), problem(P), solution(R), fixes(P,R).
fixes(lost_name, paint_name).
fixes(lost_name, wax_compact).
fixes(bent_compact, wax_compact).
fixes(split_rope, tighten_rope).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for r in SOLUTIONS:
        lines.append(asp.fact("solution", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos() vs ASP.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params_impl(args, rng)


def resolve_params_impl(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.solution:
        if args.problem not in PROBLEMS or args.solution not in SOLUTIONS:
            raise StoryError("Unknown problem or solution.")
        if not reasonableness_ok(PROBLEMS[args.problem], SOLUTIONS[args.solution]):
            raise StoryError("That solution does not actually fix that problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, solution = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    captain = args.captain or rng.choice(["Captain", "Bosun", "Old Salt"])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(setting=setting, problem=problem, solution=solution, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, captain=captain)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.solution not in SOLUTIONS:
        raise StoryError("Invalid params.")
    world = _make_world(params)
    tell(world, params)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="canal", problem="lost_name", solution="paint_name", hero="Mira", hero_gender="girl", helper="Ned", helper_gender="boy", captain="Captain"),
            StoryParams(setting="harbor", problem="split_rope", solution="tighten_rope", hero="Pip", hero_gender="boy", helper="Tess", helper_gender="girl", captain="Bosun"),
            StoryParams(setting="isle", problem="bent_compact", solution="wax_compact", hero="Lina", hero_gender="girl", helper="Jory", helper_gender="boy", captain="Old Salt"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
