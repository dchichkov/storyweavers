#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/literate_spill_circulate_mystery_to_solve_superhero.py
======================================================================================

A standalone story world for a tiny superhero mystery.

Seed words and style:
- literate
- spill
- circulate
- Mystery to Solve
- Superhero Story

Core premise:
A young hero, a careful sidekick, and a kind mentor notice a strange spill
that keeps circling back through the city. The clue is read in a literate way:
from signs, notes, and patterns in the world. The mystery is solved when the
team follows the circulating trail to its source and fixes the cause.

This script is deliberately small and classical: typed entities, physical meters
and emotional memes, a forward-chained rule engine, a reasonableness gate, a
Python/ASP twin, and state-driven prose with QA grounded in the simulated world.
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
SENSE_MIN = 2
BRAVERY_INIT = 6.0


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
class HeroStyle:
    id: str
    city: str
    title: str
    team_name: str
    patrol: str
    ending: str

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
class Mystery:
    id: str
    spill_name: str
    spill_kind: str
    source_phrase: str
    trail_phrase: str
    clue_phrase: str
    fix_phrase: str
    hidden_source: str
    spread_phrase: str
    circulating_image: str
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
class Tool:
    id: str
    label: str
    use_phrase: str
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
        return clone

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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    mystery = world.facts["mystery"]
    if source.meters["leaking"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role in {"hero", "sidekick"}:
            e.memes["alarm"] += 1
    world.get("street").meters["mess"] += 1
    out.append(f"The {mystery.spill_name} kept spreading from curb to curb.")
    return out


def _r_circulate(world: World) -> list[str]:
    out: list[str] = []
    if world.get("street").meters["mess"] < THRESHOLD:
        return out
    sig = ("circulate",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("trail").meters["circling"] += 1
    world.get("note").meters["readable"] += 1
    out.append("The clue kept circling through the blocks like it wanted to be read.")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["understanding"] < THRESHOLD:
        return out
    sig = ("solve",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("source").meters["leaking"] = 0.0
    world.get("street").meters["mess"] = 0.0
    hero.memes["pride"] += 1
    out.append("The mystery made sense at last, and the city grew calm again.")
    return out


CAUSAL_RULES = [
    Rule("spill", "physical", _r_spill),
    Rule("circulate", "physical", _r_circulate),
    Rule("solve", "social", _r_solve),
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


def reasonableness_ok(mystery: Mystery, tool: Tool) -> bool:
    return mystery.spill_kind in {"ink", "paint", "syrup"} and tool.id in {"map", "magnifier", "notebook"}


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.id in {"map", "magnifier", "notebook"}]


def predict_mystery(world: World) -> dict:
    sim = world.copy()
    _cause_spill(sim, narrate=False)
    return {
        "mess": sim.get("street").meters["mess"],
        "circling": sim.get("trail").meters["circling"],
    }


def _cause_spill(world: World, narrate: bool = True) -> None:
    src = world.get("source")
    src.meters["leaking"] = 1.0
    src.meters["spilled"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, style: HeroStyle, hero: Entity, sidekick: Entity, mentor: Entity) -> None:
    hero.memes["hope"] += 1
    sidekick.memes["curiosity"] += 1
    world.say(
        f"In {style.city}, {hero.id} wore {hero.pronoun('possessive')} mask and watched over {style.patrol} with {sidekick.id}. "
        f"{mentor.id} said they were the {style.team_name}, and the team always looked for clues with kind, literate eyes."
    )


def mystery_setup(world: World, mystery: Mystery, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"Then a strange {mystery.spill_name} appeared near the library steps. "
        f"It was sticky, bright, and nobody knew where it came from."
    )
    world.say(
        f'{sidekick.id} pointed at the marks. "This is a mystery to solve," {sidekick.pronoun()} said. '
        f"{hero.id} nodded because the trail looked like it wanted a smart reader."
    )


def read_clues(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    hero.memes["understanding"] += 1
    sidekick.memes["trust"] += 1
    world.say(
        f"{hero.id} looked closely at the signs, the chalk mark, and the torn receipt. "
        f"Being literate meant reading every clue, not just guessing."
    )
    world.say(
        f"{sidekick.id} read the little arrows aloud, and the arrows seemed to {mystery.circulating_image}."
    )


def warn_and_track(world: World, mentor: Entity, hero: Entity, mystery: Mystery, tool: Tool) -> None:
    pred = predict_mystery(world)
    mentor.memes["calm"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    world.facts["predicted_circling"] = pred["circling"]
    world.say(
        f'{mentor.id} smiled and said, "{hero.id}, this clue will keep {mystery.circulating_image} until we follow the source." '
        f"Then {mentor.pronoun()} handed over {tool.label}."
    )


def follow_trail(world: World, hero: Entity, sidekick: Entity, mystery: Mystery, tool: Tool) -> None:
    hero.memes["understanding"] += 1
    sidekick.memes["brave"] += 1
    world.say(
        f"The two heroes followed the {mystery.spill_name} past the bakery, the bus stop, and the old mural. "
        f"{tool.use_phrase.capitalize()} helped them see that the clues were not random at all."
    )


def reveal_source(world: World, mystery: Mystery) -> None:
    src = world.get("source")
    src.label = mystery.hidden_source
    world.say(
        f"At the last corner, they found the source: {mystery.hidden_source}. "
        f"A loose lid had been leaking all morning, and the spill had been circulating with every breeze and footstep."
    )


def fix_problem(world: World, mentor: Entity, mystery: Mystery) -> None:
    world.get("source").meters["leaking"] = 0.0
    world.get("street").meters["mess"] = 0.0
    mentor.memes["pride"] += 1
    world.say(
        f"{mentor.id} cleaned up the spill, sealed the lid, and thanked the team for bringing the clue home. "
        f"By evening, the blocks were bright again and the mystery was solved."
    )


def ending_image(world: World, style: HeroStyle, hero: Entity, sidekick: Entity) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"{style.ending.capitalize()}. {hero.id} and {sidekick.id} stood under the streetlamp, the map folded neatly away, "
        f"and the city looked quiet and safe."
    )


def tell(style: HeroStyle, mystery: Mystery, tool: Tool,
         hero_name: str = "Nova", hero_gender: str = "girl",
         sidekick_name: str = "Spark", sidekick_gender: str = "boy",
         mentor_name: str = "Captain Sage", mentor_gender: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=["brave", "literate"]))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_gender, role="sidekick", traits=["curious"]))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_gender, role="mentor", traits=["calm"]))
    world.add(Entity(id="street", type="place"))
    world.add(Entity(id="trail", type="thing"))
    world.add(Entity(id="note", type="thing"))
    source = world.add(Entity(id="source", type="thing", label="a sealed can"))
    world.facts["mystery"] = mystery
    world.facts["tool"] = tool

    introduce(world, style, hero, sidekick, mentor)
    world.para()
    mystery_setup(world, mystery, hero, sidekick)
    read_clues(world, hero, sidekick, mystery)
    warn_and_track(world, mentor, hero, mystery, tool)
    world.para()
    follow_trail(world, hero, sidekick, mystery, tool)
    reveal_source(world, mystery)
    propagate(world, narrate=True)
    fix_problem(world, mentor, mystery)
    ending_image(world, style, hero, sidekick)
    world.facts.update(hero=hero, sidekick=sidekick, mentor=mentor, source=source, style=style, outcome="solved")
    return world


STYLE = HeroStyle(
    "superhero",
    "Bright Harbor",
    "the Night Readers",
    "patrol team",
    "patrolled the avenue",
    "They smiled at the clean sidewalk and the solved mystery",
)

MYSTERIES = {
    "ink": Mystery(
        "ink", "ink spill", "ink",
        "a toppled pen jar", "the trail of dots", "the library clue", "wipe the floor",
        "an open fountain pen", "keep circling back",
        "curled around the block like a ribbon",
        tags={"ink", "library"},
    ),
    "paint": Mystery(
        "paint", "paint spill", "paint",
        "a fallen art tub", "the blue streaks", "the art clue", "mop the steps",
        "an open paint bucket", "keep circling back",
        "twisted around corners like a blue snake",
        tags={"paint", "art"},
    ),
    "syrup": Mystery(
        "syrup", "syrup spill", "syrup",
        "a tipped breakfast bottle", "the sweet trail", "the diner clue", "clean the counter",
        "an open syrup bottle", "keep circling back",
        "glimmered and spun in the sunlight",
        tags={"syrup", "diner"},
    ),
}

TOOLS = {
    "map": Tool("map", "a city map", "The map pointed the team in the right direction", tags={"map"}),
    "magnifier": Tool("magnifier", "a magnifying glass", "The magnifying glass made the tiny marks easy to read", tags={"magnifier"}),
    "notebook": Tool("notebook", "a notebook", "The notebook helped them write down every clue", tags={"notebook"}),
    "hose": Tool("hose", "a hose", "A hose could spray water, but it was not the right clue-reading tool", tags={"hose"}),
}

HERO_NAMES = ["Nova", "Ruby", "Kai", "Mina", "Jett", "Iris"]
SIDEKICK_NAMES = ["Spark", "Pip", "Dash", "Luna", "Bolt"]
MENTOR_NAMES = ["Captain Sage", "Ms. Lantern", "Professor Vale", "Guardian Bright"]


@dataclass
@dataclass
class StoryParams:
    style: str
    mystery: str
    tool: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    mentor_name: str
    mentor_gender: str
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
    for s in [STYLE.id]:
        for m in MYSTERIES:
            for t in TOOLS:
                if reasonableness_ok(MYSTERIES[m], TOOLS[t]):
                    combos.append((s, m, t))
    return combos


def explain_rejection(mystery: Mystery, tool: Tool) -> str:
    return (
        f"(No story: the mystery involves a {mystery.spill_kind} spill, but {tool.label} is not a good clue-reading tool. "
        f"Try the map, magnifying glass, or notebook so the heroes can solve the mystery in a sensible way.)"
    )


def explain_tool_rejection(tool_id: str) -> str:
    return (
        f"(Refusing tool '{tool_id}': this story needs a tool that helps read clues, not one that merely sprays or wipes. "
        f"Try map, magnifier, or notebook.)"
    )


ASP_RULES = r"""
valid(S, M, T) :- style(S), mystery(M), tool(T), sensible_tool(T), spill_kind(M, K), clue_tool(T).
outcome(solved) :- hero_reads_clues, trail_circulates, source_fixed.
trail_circulates :- spill_source, spill_present.
hero_reads_clues :- literate_hero, clue_tool_used.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("style", STYLE.id))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("spill_kind", mid, m.spill_kind))
        lines.append(asp.fact("spill_source", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tid in {"map", "magnifier", "notebook"}:
            lines.append(asp.fact("sensible_tool", tid))
            lines.append(asp.fact("clue_tool", tid))
    lines.append(asp.fact("literate_hero"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(style=None, mystery=None, tool=None,
                                                           hero_name=None, hero_gender=None,
                                                           sidekick_name=None, sidekick_gender=None,
                                                           mentor_name=None, mentor_gender=None),
                                         random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about a literate mystery with a circulating spill.")
    ap.add_argument("--style", choices=[STYLE.id])
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--mentor-name")
    ap.add_argument("--mentor-gender", choices=["woman", "man", "girl", "boy"])
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
    if args.tool and args.tool not in {"map", "magnifier", "notebook"}:
        raise StoryError(explain_tool_rejection(args.tool))
    combos = [c for c in valid_combos()
              if (args.style is None or c[0] == args.style)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, mystery, tool = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    mentor_gender = args.mentor_gender or rng.choice(["woman", "man"])
    return StoryParams(
        style=STYLE.id,
        mystery=mystery,
        tool=tool,
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        hero_gender=hero_gender,
        sidekick_name=args.sidekick_name or rng.choice([n for n in SIDEKICK_NAMES if n != args.hero_name]),
        sidekick_gender=sidekick_gender,
        mentor_name=args.mentor_name or rng.choice(MENTOR_NAMES),
        mentor_gender=mentor_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    return [
        f'Write a superhero story that uses the words "literate", "spill", and "circulate" and includes a mystery to solve.',
        f"Tell a kid-friendly superhero story where the heroes read clues carefully to solve the {m.spill_name}.",
        f"Write a story in which a clever team follows a clue that keeps circulating until they find the source.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    mentor: Entity = f["mentor"]
    return [
        QAItem(question="Who solved the mystery?", answer=f"{hero.id} and {sidekick.id} solved it together with help from {mentor.id}. They read the clues carefully and followed the trail to the source."),
        QAItem(question="What made the story a mystery to solve?", answer=f"A strange {m.spill_name} showed up with no clear source. The team had to read the clues and trace the spill until they found where it started."),
        QAItem(question=f"What did {hero.id} need to do to solve it?", answer=f"{hero.id} needed to be literate and study the signs, notes, and trail. Reading carefully helped {hero.pronoun('object')} notice the pattern that kept circulating through the city."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does literate mean?", answer="Literate means able to read and understand words, signs, and clues."),
        QAItem(question="What is a spill?", answer="A spill is something that has been tipped or poured out where it does not belong."),
        QAItem(question="What does circulate mean?", answer="Circulate means to move around and keep going from place to place."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(STYLE.id, "ink", "map", "Nova", "girl", "Spark", "boy", "Captain Sage", "woman"),
    StoryParams(STYLE.id, "paint", "magnifier", "Kai", "boy", "Luna", "girl", "Professor Vale", "man"),
    StoryParams(STYLE.id, "syrup", "notebook", "Mina", "girl", "Bolt", "boy", "Ms. Lantern", "woman"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        STYLE, MYSTERIES[params.mystery], TOOLS[params.tool],
        params.hero_name, params.hero_gender,
        params.sidekick_name, params.sidekick_gender,
        params.mentor_name, params.mentor_gender,
    )
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
