#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/saxophone_dirt_dim_individual_repetition_inner_monologue.py
===========================================================================================

A small superhero storyworld: a child-sidekick, a soot-dim alley clue, and a
single unexpected individual who changes the mission. The world leans on
repetition, inner monologue, and a twist ending, while still behaving like a
tiny simulation rather than a frozen paragraph.

Seed words: saxophone, dirt-dim, individual
Features: Repetition, Inner Monologue, Twist
Style: Superhero Story
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
DARK_MIN = 1.0


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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    id: str
    place: str
    dim: str
    glow: str
    sounds: str
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
    source: str
    source_phrase: str
    clue: str
    risk: str
    truth: str
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
    effect: str
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
class Twist:
    id: str
    reveal: str
    new_goal: str
    ending_image: str
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    haze = world.entities.get("haze")
    if not hero or not haze:
        return out
    if hero.meters["attention"] < THRESHOLD:
        return out
    if haze.meters["dirt_dim"] < THRESHOLD:
        return out
    sig = ("smudge",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    out.append("__repeat__")
    return out


def _r_truth(world: World) -> list[str]:
    clue = world.entities.get("clue")
    if not clue:
        return []
    if clue.meters["revealed"] < THRESHOLD:
        return []
    sig = ("truth",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("city").meters["safe"] += 1
    return []


CAUSAL_RULES = [Rule("smudge", _r_smudge), Rule("truth", _r_truth)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(problem: Problem, tool: Tool) -> bool:
    return "dim" in problem.tags and "clean" in tool.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, p in PROBLEMS.items():
            for tid, t in TOOLS.items():
                if is_reasonable(p, t):
                    combos.append((sid, pid, tid))
    return combos


def _predict(world: World, problem: Problem) -> dict:
    sim = world.copy()
    simulate_misread(sim, narrate=False)
    return {"worry": sim.get("hero").memes["worry"]}


def simulate_misread(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    hero.meters["attention"] += 1
    hero.meters["breath"] += 1
    hero.memes["focus"] += 1
    if narrate:
        world.say(
            f"{hero.id} narrowed {hero.pronoun('possessive')} eyes and thought, "
            f'"One more look. One more look."'
        )
    haze = world.get("haze")
    haze.meters["dirt_dim"] += 1
    propagate(world, narrate=narrate)


def reveal_twist(world: World, twist: Twist, individual: Entity) -> None:
    world.say(twist.reveal)
    individual.meters["seen"] += 1
    individual.memes["relief"] += 1
    world.say(
        f"It turned out the individual was not a menace at all, but a lost music"
        f" teacher who had been carrying the saxophone case through the dirt-dim"
        f" alley."
    )


def rescue(world: World, tool: Tool, problem: Problem, twist: Twist, individual: Entity) -> None:
    world.say(
        f"{tool.phrase.capitalize()} came next, and {tool.effect}."
    )
    world.say(
        f"{problem.truth} The alley cleared, the saxophone stayed safe, and the"
        f" individual could point the way toward the hidden rehearsal room."
    )
    world.say(
        f"{twist.ending_image}"
    )


def tell(setting: Setting, problem: Problem, tool: Tool, twist: Twist,
         hero_name: str = "Nova", hero_type: str = "girl",
         helper_name: str = "Quill", helper_type: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    city = world.add(Entity(id="city", type="place", label=setting.place))
    haze = world.add(Entity(id="haze", type="thing", label="the alley haze", tags=problem.tags))
    clue = world.add(Entity(id="clue", type="thing", label="the saxophone case", tags={"saxophone"}))
    individual = world.add(Entity(id="individual", kind="character", type="woman", label="the individual", role="mystery"))
    world.facts["setting"] = setting
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["twist"] = twist
    world.facts["individual"] = individual

    hero.meters["attention"] += 1
    hero.memes["determination"] += 1
    helper.memes["faith"] += 1

    world.say(
        f"On patrol above {setting.place}, {hero_name} listened for trouble and for "
        f"the bright note of a saxophone."
    )
    world.say(
        f"Again and again, {hero_name} told {hero.pronoun('object')}self, "
        f'"Follow the dim. Follow the dim. Follow the dim."'
    )
    world.say(
        f"Below, the {problem.source_phrase} looked dirt-dim, and that made the "
        f"whole block feel wrong."
    )
    world.say(
        f'{helper_name} pointed. "Something is moving in there."'
    )
    world.say(
        f"{hero_name} thought, 'If I rush in, I may miss the truth. If I wait, I may "
        f"find it.'"
    )

    world.para()
    simulate_misread(world)
    world.say(
        f"{hero_name} took one careful step after another. The dirt-dim patch kept "
        f"getting darker, and the worry kept getting louder."
    )
    if _predict(world, problem)["worry"] >= THRESHOLD:
        world.say(
            f"Inside {hero_name}'s head, a tiny voice whispered, 'This feels like a trap. "
            f"But traps do not usually sound like a saxophone.'"
        )

    world.para()
    reveal_twist(world, twist, individual)
    world.say(
        f"{helper_name} blinked. '{problem.truth}'"
    )
    world.say(
        f"That was the twist: the suspicious individual was only carrying the thing "
        f"because someone had dropped it."
    )
    world.say(
        f"{hero_name} listened to the last echo and decided to help instead of chase."
    )

    world.para()
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, tags=tool.tags))
    tool_ent.meters["use"] += 1
    if is_reasonable(problem, tool):
        world.say(
            f"{hero_name} used {tool.phrase}, and {tool.effect}."
        )
        rescue(world, tool, problem, twist, individual)
    else:
        raise StoryError("unreasonable tool/problem combination")

    world.facts.update(
        hero=hero, helper=helper, city=city, haze=haze, clue=clue, tool_ent=tool_ent,
        outcome="twist", problem=problem, tool=tool, setting=setting, twist=twist,
    )
    return world


SETTINGS = {
    "rooftops": Setting(id="rooftops", place="the moonlit rooftops", dim="blue", glow="silver", sounds="wind and sirens"),
    "alley": Setting(id="alley", place="the narrow alley", dim="gray", glow="yellow", sounds="dripping pipes"),
    "museum": Setting(id="museum", place="the old museum hall", dim="dusty", glow="gold", sounds="echoes"),
}

PROBLEMS = {
    "haze": Problem(
        id="haze",
        source="dirt-dim",
        source_phrase="a dirt-dim smear near the fire escape",
        clue="dirty footprints",
        risk="It can hide clues and make a hero chase the wrong shadow.",
        truth="It was only a trail of soot from the saxophone case.",
        tags={"dim", "dirt", "individual"},
    ),
    "echo": Problem(
        id="echo",
        source="dirt-dim",
        source_phrase="a dirt-dim blur under the stairs",
        clue="a soft hum",
        risk="It can make one person look like three.",
        truth="It was only dust and a shiny brass case.",
        tags={"dim", "dirt"},
    ),
}

TOOLS = {
    "lamp": Tool(id="lamp", label="signal lamp", phrase="the signal lamp", effect="the alley glowed clean and bright", tags={"clean"}),
    "wash": Tool(id="wash", label="hose rinse", phrase="a quick hose rinse", effect="the dirt washed away from the brass", tags={"clean"}),
}

TWISTS = {
    "teacher": Twist(
        id="teacher",
        reveal="Then the mystery individual raised one hand and sang a tiny tuning note.",
        new_goal="escort the teacher home",
        ending_image="At the end, the saxophone shone in the light, and the alley felt like a stage again.",
        tags={"twist", "individual"},
    )
}

GIRL_NAMES = ["Nova", "Ivy", "Aria", "Mina", "Zia"]
BOY_NAMES = ["Quill", "Tate", "Jules", "Pax", "Luca"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    twist: str
    hero_name: str = "Nova"
    hero_gender: str = "girl"
    helper_name: str = "Quill"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with saxophone, dirt-dim, individual, repetition, inner monologue, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    twist = args.twist or rng.choice(sorted(TWISTS))
    if args.hero_gender == "girl":
        hero_name = args.hero_name or rng.choice(GIRL_NAMES)
    elif args.hero_gender == "boy":
        hero_name = args.hero_name or rng.choice(BOY_NAMES)
    else:
        hero_name = args.hero_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    if args.helper_gender == "girl":
        helper_name = args.helper_name or rng.choice(GIRL_NAMES)
    elif args.helper_gender == "boy":
        helper_name = args.helper_name or rng.choice(BOY_NAMES)
    else:
        helper_name = args.helper_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(setting=setting, problem=problem, tool=tool, twist=twist,
                       hero_name=hero_name, hero_gender=args.hero_gender or "girl",
                       helper_name=helper_name, helper_gender=args.helper_gender or "boy")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Problem = f["problem"]
    t: Twist = f["twist"]
    return [
        f'Write a superhero story that includes the words "saxophone", "{p.source}", and "individual".',
        f"Tell a story where a hero hears a saxophone in a dirt-dim place, suspects one individual, and then learns the truth with a twist.",
        f"Write a child-friendly superhero tale with repetition, an inner monologue, and a twist ending about helping an individual near a saxophone case.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prob: Problem = f["problem"]
    twist: Twist = f["twist"]
    individual: Entity = f["individual"]
    return [
        QAItem(
            question="What made the hero suspicious?",
            answer=f"The hero saw a dirt-dim smear and a dark little shape near the saxophone case. That made it look like one individual might be causing trouble."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The suspicious individual was not a villain at all. The person was a lost music teacher, so the hero switched from chasing to helping."
        ),
        QAItem(
            question="How did the hero think during the story?",
            answer=f"The hero repeated the same plan in their head and kept listening: 'Follow the dim. Follow the dim. Follow the dim.' That inner monologue helped them slow down and notice the truth."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a saxophone?",
            answer="A saxophone is a brass instrument that makes a rich, loud sound when someone blows into it and presses its keys."
        ),
        QAItem(
            question="What does dirt-dim mean here?",
            answer="It means dark with dirt or soot, like a place that looks gray and messy instead of bright and clean."
        ),
        QAItem(
            question="What does it mean to be an individual?",
            answer="An individual is one single person. In this story, it matters because the hero is trying to figure out whether one person is friend or foe."
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:9} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="alley", problem="haze", tool="lamp", twist="teacher",
                hero_name="Nova", hero_gender="girl", helper_name="Quill", helper_gender="boy"),
    StoryParams(setting="museum", problem="echo", tool="wash", twist="teacher",
                hero_name="Ivy", hero_gender="girl", helper_name="Tate", helper_gender="boy"),
]


def explain_rejection() -> str:
    return "(No story: this combo would not create a believable dirt-dim superhero twist.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if "dim" in p.tags:
            lines.append(asp.fact("dim_problem", pid))
        if "dirt" in p.tags:
            lines.append(asp.fact("dirt_problem", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if "clean" in t.tags:
            lines.append(asp.fact("clean", tid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,T) :- setting(S), problem(P), tool(T), dim_problem(P), dirt_problem(P), clean(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and Python gates.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: default generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, table in (("setting", SETTINGS), ("problem", PROBLEMS), ("tool", TOOLS), ("twist", TWISTS)):
        if getattr(params, key) not in table:
            raise StoryError(f"invalid {key}: {getattr(params, key)}")
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        TWISTS[params.twist],
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
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
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
