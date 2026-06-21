#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/extensive_guava_basin_problem_solving_repetition_transformation.py
=================================================================================================

A standalone storyworld for a small mystery about an extensive search,
a guava clue, and a basin that changes the shape of the answer.

The world is built around three story instruments:

- Problem solving: a child notices a mystery, tests clues, and reasons it out.
- Repetition: the child repeats a careful action or phrase, which matters to the
  solution and helps the narration feel patterned.
- Transformation: something plain becomes useful, or something hidden becomes
  visible, by the end.

The tone stays child-facing and a little mysterious, but the outcome is warm and
clear. The story always begins with a puzzling absence, moves through a search,
and ends with a concrete image proving what changed.
"""

from __future__ import annotations

import argparse
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"notice": 0.0, "mess": 0.0, "clarity": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "worry": 0.0, "relief": 0.0})

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
    place: str
    shadows: str
    detail: str
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
class Clue:
    id: str
    word: str
    phrase: str
    reveals: str
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
class Problem:
    id: str
    mystery: str
    search: str
    repeated_action: str
    repeated_line: str
    transformed_end: str
    solved_by: str
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
class StoryParams:
    setting: str
    problem: str
    clue: str
    hero: str = "Mina"
    hero_gender: str = "girl"
    helper: str = "Dad"
    helper_gender: str = "boy"
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "garden": Setting(id="garden", place="the garden", shadows="the old fig tree",
                      detail="The path curled around a stone basin near the back wall."),
    "courtyard": Setting(id="courtyard", place="the courtyard", shadows="the bright archway",
                         detail="A shallow basin sat beside a row of climbing vines."),
    "museum": Setting(id="museum", place="the little museum yard", shadows="the long bench",
                      detail="There was a basin under the signboard, plain and overlooked."),
}

CLUES = {
    "guava": Clue(id="guava", word="guava", phrase="a guava peel", reveals="the sweet scent was fresh",
                  tags={"guava", "fruit"}),
    "leaf": Clue(id="leaf", word="leaf", phrase="a wet leaf", reveals="the shape matched the lid of the basin",
                 tags={"leaf"}),
    "string": Clue(id="string", word="string", phrase="a loop of string", reveals="someone had tied and retied it",
                   tags={"string"}),
}

PROBLEMS = {
    "missing_water": Problem(
        id="missing_water",
        mystery="the basin was empty",
        search="find where the water had gone",
        repeated_action="looked again",
        repeated_line="Mina looked again, and again, and again.",
        transformed_end="the empty basin became a mirror for the sky",
        solved_by="finding the hidden drain stop",
        tags={"basin", "mystery"},
    ),
    "strange_smell": Problem(
        id="strange_smell",
        mystery="the garden smelled sweet and odd",
        search="find the source of the smell",
        repeated_action="sniffed again",
        repeated_line="Mina sniffed again, and again, and again.",
        transformed_end="the smell changed from puzzling to plain when the peel was moved",
        solved_by="finding the guava peel",
        tags={"guava", "mystery"},
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ava", "Iris"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Milo", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, problem in PROBLEMS.items():
            for cid, clue in CLUES.items():
                if sid == "museum" and pid == "strange_smell" and cid == "guava":
                    combos.append((sid, pid, cid))
                elif sid != "museum":
                    combos.append((sid, pid, cid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: an extensive mystery search, a guava clue, and a basin transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    if args.setting == "museum" and args.problem == "strange_smell" and args.clue != "guava":
        raise StoryError("The museum story needs the guava clue so the smell can be explained.")
    setting, problem, clue = rng.choice(sorted(combos))
    hero = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice(["Dad", "Mom", "Aunt Rae"])
    hero_gender = "girl" if hero in GIRL_NAMES else "boy"
    helper_gender = "boy" if helper == "Dad" else "girl"
    return StoryParams(setting=setting, problem=problem, clue=clue, hero=hero,
                       hero_gender=hero_gender, helper=helper, helper_gender=helper_gender)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    clue = CLUES[params.clue]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="solver"))
    helper = world.add(Entity(id=params.helper, kind="character",
                              type="boy" if params.helper_gender == "boy" else "girl",
                              role="helper", label=params.helper))
    basin = world.add(Entity(id="basin", kind="thing", type="thing", label="basin", role="object"))
    clue_ent = world.add(Entity(id=clue.id, kind="thing", type="thing", label=clue.word, role="clue"))
    hero.memes["curiosity"] += 1
    hero.meters["notice"] += 1

    world.say(f"{hero.id} wandered into {setting.place}. Something about it felt unusual.")
    world.say(f"{problem.mystery.capitalize()}. {setting.detail}")
    world.say(f'{hero.id} peered at the basin and said, "{problem.search.capitalize()}."')

    world.para()
    world.say(f"{problem.repeated_line} The quiet repetition helped {hero.id} notice tiny changes.")
    if clue.word == "guava":
        world.say(f"Then {clue.phrase} gave off a clue. {clue.reveals}.")
    else:
        world.say(f"Then {clue.phrase} gave off a clue. {clue.reveals}.")
    hero.meters["notice"] += 1
    world.facts["repetition"] = problem.repeated_line

    world.para()
    if problem.id == "missing_water":
        basin.meters["clarity"] += 1
        basin.attrs["hidden_drain"] = True
        world.say(f"{hero.id} listened to the basin, moved the stopper, and the answer clicked into place.")
        world.say(f"The drain was open all along, so the basin changed from empty trouble to a bright, still mirror.")
    else:
        basin.meters["clarity"] += 1
        world.say(f"{hero.id} followed the sweet smell, lifted the guava peel, and uncovered the reason at once.")
        world.say(f"The scent faded, and the whole yard changed from puzzling to ordinary again.")

    world.para()
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(f"{helper.id} smiled at the careful answer.")
    world.say(f"In the end, {problem.transformed_end}, and {hero.id} knew the mystery had been solved.")

    world.facts.update(
        hero=hero, helper=helper, setting=setting, problem=problem, clue=clue, basin=basin,
        solved=True, repeated_line=problem.repeated_line
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the words "extensive", "{f["clue"].word}", and "basin".',
        f"Tell a story where {f['hero'].id} makes an extensive search, repeats a careful action, and solves a small mystery.",
        f"Write a mystery with a guava clue and a basin that changes from puzzling to understood by the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue"]
    problem = f["problem"]
    setting = f["setting"]
    basin = f["basin"]
    return [
        QAItem(
            question="What was the mystery in the story?",
            answer=f"The mystery was {problem.mystery}. {hero.id} treated it like a careful puzzle and kept looking until the answer appeared.",
        ),
        QAItem(
            question="Why did the repeated action matter?",
            answer=f"{hero.id} repeated the search line {f['repeated_line']}. That repetition helped {hero.id} notice the small clue and stay focused on the problem.",
        ),
        QAItem(
            question="How was the basin transformed?",
            answer=f"At first the basin seemed like part of the trouble, but in the end it became useful and clear. The basin turned into a still, bright answer instead of a blank mystery.",
        ),
        QAItem(
            question="Who helped solve the mystery?",
            answer=f"{helper.id} was there, but the main solving came from {hero.id}'s careful noticing. {helper.id} smiled when the answer was found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is guava?",
            answer="Guava is a fruit with a sweet smell and taste. People can notice it by its scent even before they see it.",
        ),
        QAItem(
            question="What is a basin?",
            answer="A basin is a bowl-like container or hollow place that can hold water or other things. It can also be an ordinary object in a scene that hides a clue.",
        ),
        QAItem(
            question="What does extensive mean?",
            answer="Extensive means very large or wide-reaching. An extensive search covers many places instead of only one small spot.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,C) :- setting(S), problem(P), clue(C), not invalid_combo(S,P,C).
invalid_combo("museum","strange_smell",C) :- clue(C), C != guava.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(valid_combos()) != set(asp_valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify passed, and normal generation/emit smoke test succeeded.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="garden", problem="missing_water", clue="leaf", hero="Mina", hero_gender="girl", helper="Dad", helper_gender="boy"),
    StoryParams(setting="courtyard", problem="strange_smell", clue="guava", hero="Nora", hero_gender="girl", helper="Mom", helper_gender="girl"),
    StoryParams(setting="museum", problem="strange_smell", clue="guava", hero="Eli", hero_gender="boy", helper="Aunt Rae", helper_gender="girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, clue = rng.choice(sorted(combos))
    hero = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice(["Dad", "Mom", "Aunt Rae"])
    hero_gender = "girl" if hero in GIRL_NAMES else "boy"
    helper_gender = "boy" if helper == "Dad" else "girl"
    return StoryParams(setting=setting, problem=problem, clue=clue, hero=hero,
                       hero_gender=hero_gender, helper=helper, helper_gender=helper_gender)


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
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
