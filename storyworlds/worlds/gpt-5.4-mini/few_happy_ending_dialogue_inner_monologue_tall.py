#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/few_happy_ending_dialogue_inner_monologue_tall.py
=================================================================================

A tiny standalone story world about a few brave helpers, a tall tale problem,
inner monologue, dialogue, and a happy ending.

Domain premise:
- A child and a few companions try to solve a small but dramatic problem in a
  barn, tower, dock, or market.
- The hero thinks aloud privately, speaks with a helper, chooses a sensible tool,
  and ends with a vivid proof of success.
- The story is written in a tall-tale flavor, but the world model is concrete:
  typed entities, physical meters, emotional memes, and state-driven turns.

This script follows the Storyweavers storyworld contract:
- stdlib only
- imports storyworlds/results.py eagerly
- supports --trace, --qa, --json, --asp, --verify, --show-asp, -n, --all,
  --seed, and normal default generation
- includes Python validity checks plus an inline ASP twin
- generates prompts, grounded story Q&A, and world-knowledge Q&A from state
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"trouble": 0.0, "fixed": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"hope": 0.0, "worry": 0.0, "joy": 0.0})

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
    tall_thing: str
    sound: str
    light: str
    tag: str

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
    source: str
    danger: str
    fix_noun: str
    fix_verb: str
    spill: str
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
class Helper:
    id: str
    label: str
    tool: str
    power: int
    action: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    helper: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    parent: str
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


SETTINGS = {
    "barn": Setting("barn", "the barn", "hayloft beam", "the creak of boards", "a sliver of lamp-light", "barn"),
    "tower": Setting("tower", "the old tower", "spiral stair", "the wind's whistle", "moonlight in a window", "tower"),
    "dock": Setting("dock", "the dock by the river", "ladder pole", "the slap of water", "sun glitter on the waves", "dock"),
    "market": Setting("market", "the market square", "sign pole", "the chatter of merchants", "bright flags overhead", "market"),
}

PROBLEMS = {
    "stuck": Problem("stuck", "a stuck gate", "a gate that will not budge", "the path is blocked", "lever", "pry", "a heavy shove", {"barn", "tower", "dock", "market"}),
    "dark": Problem("dark", "a dark passage", "a dark passage that swallows light", "the way feels spooky", "lantern", "light", "a lonely echo", {"barn", "tower"}),
    "drift": Problem("drift", "a drifting boat", "a small boat drifting loose", "it may float away", "rope", "tie", "a splash and a bob", {"dock"}),
    "crate": Problem("crate", "a toppled crate", "a toppled crate blocking the stall", "the goods are trapped", "wheel", "roll", "a clattering tumble", {"market", "barn"}),
}

HELPERS = {
    "lever": Helper("lever", "a long lever", "lever", 3, "heave it aside", {"stuck"}),
    "lantern": Helper("lantern", "a bright lantern", "lantern", 2, "brighten the dark passage", {"dark"}),
    "rope": Helper("rope", "a sturdy rope", "rope", 3, "lasso the boat and hold it close", {"drift"}),
    "wheel": Helper("wheel", "a wagon wheel", "wheel", 2, "roll the crate clear", {"crate"}),
}

GIRL_NAMES = ["Mira", "Nell", "Ruby", "Ada", "Clara", "Faye"]
BOY_NAMES = ["Otis", "Bo", "Cal", "Wes", "Jonah", "Pip"]
TRAITS = ["bold", "curious", "quick-witted", "sturdy", "bright-eyed"]
COMRADES = ["the donkey", "a small dog", "a barn cat", "the goose"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p, prob in PROBLEMS.items():
            if s in prob.tags:
                for h, hel in HELPERS.items():
                    if p in hel.tags:
                        out.append((s, p, h))
    return out


def reasonableness(problem: Problem, helper: Helper) -> bool:
    return problem.id in helper.tags and helper.power >= 2


def tidy_word() -> str:
    return "few"


def tell(setting: Setting, problem: Problem, helper: Helper, hero: Entity, companion: Entity, parent: Entity) -> World:
    world = World()
    hero.memes["hope"] = 1.0
    companion.memes["hope"] = 1.0
    world.add(hero)
    world.add(companion)
    world.add(parent)
    world.add(Entity("setting", type="place", label=setting.place))
    world.add(Entity("problem", type="thing", label=problem.label))
    world.add(Entity("helper", type="tool", label=helper.label))
    world.say(f"On a bright day with a tall wind and a few clouds, {hero.id} and {companion.id} went to {setting.place}.")
    world.say(f"'{setting.sound},' said {companion.id}, staring up at the {setting.tall_thing}. 'That looks like a giant story waiting to happen.'")
    world.say(f"{hero.id} smiled, but inside {hero.pronoun('subject')} thought, 'If that {problem.label} stays, the day will stay stuck.'")
    world.para()
    world.say(f"They found {problem.source}, and it made the air feel {problem.danger}.")
    world.say(f"'{problem.label_word if False else problem.label.capitalize()} needs help,' said {companion.id}.")
    world.say(f"'{helper.label.capitalize()} time,' {hero.id} murmured, because {hero.pronoun('subject')} knew a little tool could stand up to a big mess.")
    world.say(f"Their parent laughed and said, '{hero.id}, you have the eyes of a captain and the heart of a lamb.'")
    world.para()
    world.say(f"{hero.id} lifted {helper.tool if helper.tool else helper.label}, and {companion.id} held steady.")
    world.say(f"They used it to {helper.action}, and the trouble began to shrink.")
    world.say(f"The {problem.spill} gave way, the path opened, and the tall place seemed to bow just a little.")
    world.para()
    hero.memes["joy"] += 2
    companion.memes["joy"] += 2
    world.get("problem").meters["trouble"] = 0.0
    world.get("problem").meters["fixed"] = 1.0
    world.say(f"By sunset, the way was clear, the {setting.light} glowed gold, and even {parent.id} cheered.")
    world.say(f"'{tidy_word()} brave folks can make a mighty change,' {parent.id} said. '{hero.id}, you did it.'")
    world.say(f"So the {companion.id} hopped once, the {hero.id} grinned, and the whole place felt lighter than a feather.")
    world.facts.update(setting=setting, problem=problem, helper=helper, hero=hero, companion=companion, parent=parent, outcome="happy")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale style story that includes the word "{tidy_word()}" and has a happy ending.',
        f"Tell a story where {f['hero'].id} and {f['companion'].id} solve {f['problem'].label} with {f['helper'].label}.",
        f"Write a child-friendly tall tale with dialogue and a private thought, ending in relief and celebration.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, c, p, helper = f["hero"], f["companion"], f["problem"], f["helper"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {h.id} and {c.id}, who faced {p.label} together. {h.id} was the one who listened closely and chose the helper."),
        QAItem(question="What did the hero think before acting?", answer=f"{h.id} thought that if {p.label} stayed, the day would stay stuck. That private thought helped {h.id} choose {helper.label} instead of giving up."),
        QAItem(question="How did the problem get fixed?", answer=f"They used {helper.label} to {helper.action}, and that made the trouble shrink. The path opened after that, so the ending could be happy."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a lever for?", "A lever helps a person move or lift something heavy by giving extra help and reach."),
        QAItem("What is a lantern for?", "A lantern gives light in a dark place without making a big fuss."),
        QAItem("What does it mean when a story has a happy ending?", "A happy ending means the problem gets fixed, the characters are safe, and the last image feels bright and peaceful."),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type}) meters={meters} memes={memes} label={e.label}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,H) :- setting(S), problem(P), helper(H), problem_tag(P,S), helper_tag(H,P), helper_power(H,N), N >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("problem_tag", "stuck", sid))
        lines.append(asp.fact("problem_tag", "dark", sid))
        lines.append(asp.fact("problem_tag", "crate", sid))
        lines.append(asp.fact("problem_tag", "drift", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_tag", hid, next(iter(h.tags))))
        lines.append(asp.fact("helper_power", hid, h.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, helper=None, hero=None, hero_gender=None, companion=None, companion_gender=None, parent=None, seed=None), random.Random(1)))
        _ = sample.story
    except Exception:
        traceback.print_exc()
        print("Smoke test failed.")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale story world with few, dialogue, inner monologue, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, helper = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice([n for n in (BOY_NAMES if companion_gender == "boy" else GIRL_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, problem, helper, hero, hero_gender, companion, companion_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], HELPERS[params.helper],
                 Entity(params.hero, kind="character", type=params.hero_gender, role="hero"),
                 Entity(params.companion, kind="character", type=params.companion_gender, role="companion"),
                 Entity(params.parent, kind="character", type=params.parent, role="parent"))
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
    StoryParams("barn", "stuck", "lever", "Mira", "girl", "Bo", "boy", "mother"),
    StoryParams("tower", "dark", "lantern", "Otis", "boy", "Ruby", "girl", "father"),
    StoryParams("dock", "drift", "rope", "Nell", "girl", "Cal", "boy", "mother"),
    StoryParams("market", "crate", "wheel", "Wes", "boy", "Faye", "girl", "father"),
]


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
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
