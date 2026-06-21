#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/interject_summer_seventy_surprise_cautionary_superhero_story.py
================================================================================================

A tiny superhero storyworld built from the seed words:

- interject
- summer
- seventy

Features:
- Surprise
- Cautionary
- Superhero Story

The world simulates a small summer rescue scene: a young hero and a cautious
helper notice a surprising problem, one character tries to rush ahead, the
cautionary voice interjects, and the ending proves what changed in the world.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "heroine"}
        male = {"boy", "father", "man", "hero"}
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
    name: str
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
class HeroTool:
    id: str
    label: str
    force: int
    safe: bool
    phrase: str
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
    label: str
    danger: int
    can_rise: bool
    phrase: str
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
class Response:
    id: str
    power: int
    text: str
    fail: str
    qa_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_heat(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["heat"] < THRESHOLD:
            continue
        sig = ("heat", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if e.id == "Beacon":
            world.get("street").meters["danger"] += 1
            world.get("Hero").memes["fear"] += 1
            world.get("Sidekick").memes["fear"] += 1
            out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("heat", _r_heat)]


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


SETTINGS = {
    "summer": Setting(id="summer", name="summer", detail="the hot summer street"),
}

TOOLS = {
    "shield": HeroTool(
        id="shield",
        label="sun shield",
        force=3,
        safe=True,
        phrase="a bright sun shield",
        tags={"summer", "safe"},
    ),
    "cape": HeroTool(
        id="cape",
        label="cape",
        force=2,
        safe=True,
        phrase="a fluttering cape",
        tags={"hero", "safe"},
    ),
    "sprayer": HeroTool(
        id="sprayer",
        label="sprayer",
        force=1,
        safe=False,
        phrase="a tiny spray wand",
        tags={"risk"},
    ),
}

PROBLEMS = {
    "seventy": Problem(
        id="seventy",
        label="seventy glowing sparks",
        danger=7,
        can_rise=True,
        phrase="seventy glowing sparks",
        tags={"seventy", "surprise"},
    ),
    "sunwheel": Problem(
        id="sunwheel",
        label="a spinning sunwheel",
        danger=5,
        can_rise=True,
        phrase="a spinning sunwheel",
        tags={"summer", "surprise"},
    ),
}

RESPONSES = {
    "steady": Response(
        id="steady",
        power=8,
        text="lifted the sun shield and guided the sparks into a safe glass lantern",
        fail="tried to guide the sparks, but the glare jumped every which way",
        qa_text="lifted the sun shield and guided the sparks into a safe glass lantern",
        tags={"safe"},
    ),
    "net": Response(
        id="net",
        power=6,
        text="snapped a rooftop net over the sparks and held them there until they cooled",
        fail="threw a net, but the sparks slipped under it and kept climbing",
        qa_text="snapped a rooftop net over the sparks and held them there until they cooled",
        tags={"safe"},
    ),
}

HERO_NAMES = ["Nova", "Blaze", "Mira", "Kai", "Ivy", "Ray"]
HELPER_NAMES = ["Pip", "Juno", "Tess", "Finn", "Luna", "Beck"]
TRAITS = ["bold", "careful", "quick", "bright", "steady"]

CURATED = [
    dict(
        setting="summer",
        tool="shield",
        problem="seventy",
        response="steady",
        hero="Nova",
        hero_gender="girl",
        helper="Pip",
        helper_gender="boy",
        parent="guardian",
        trait="careful",
        surprise="the clouds opened into a sky of orange sparks",
    ),
    dict(
        setting="summer",
        tool="cape",
        problem="sunwheel",
        response="net",
        hero="Blaze",
        hero_gender="boy",
        helper="Tess",
        helper_gender="girl",
        parent="guardian",
        trait="steady",
        surprise="a spinning sign bloomed above the market like a firework",
    ),
]


@dataclass
class StoryParams:
    setting: str
    tool: str
    problem: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    surprise: str = ""
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
    for sid in SETTINGS:
        for tid, tool in TOOLS.items():
            for pid, prob in PROBLEMS.items():
                if tool.safe and prob.can_rise:
                    combos.append((sid, tid, pid))
    return combos


def explain_rejection(tool: HeroTool, problem: Problem) -> str:
    return (
        f"(No story: {tool.label} is not a sensible hero tool for {problem.label}. "
        f"Pick a safe tool and a rising problem that can fit a superhero rescue.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero summer storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", default="guardian")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.tool and args.problem:
        if not TOOLS[args.tool].safe or not PROBLEMS[args.problem].can_rise:
            raise StoryError(explain_rejection(TOOLS[args.tool], PROBLEMS[args.problem]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, problem = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        tool=tool,
        problem=problem,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=args.parent,
        trait=trait,
        surprise="",
    )


def predict(world: World, problem_id: str) -> dict:
    sim = world.copy()
    sim.get(problem_id).meters["heat"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("street").meters["danger"],
        "fear": sim.get("Hero").memes["fear"] + sim.get("Sidekick").memes["fear"],
    }


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="Hero", kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id="Sidekick", kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id="Guardian", kind="character", type="adult", role="parent", label=params.parent))
    street = world.add(Entity(id="street", type="street", label="the summer street"))
    beacon = world.add(Entity(id="Beacon", type="problem", label=PROBLEMS[params.problem].label))
    tool = world.add(Entity(id="tool", type="tool", label=TOOLS[params.tool].label))
    response = RESPONSES[params.response]

    hero.memes["hope"] += 1
    helper.memes["caution"] += 1
    world.say(
        f"On a summer afternoon, {params.hero} and {params.helper} flew through "
        f"{SETTINGS[params.setting].name} like a team of bright city heroes."
    )
    world.say(
        f'Then came a surprise: {params.surprise or PROBLEMS[params.problem].phrase}, '
        f'and {params.hero} almost rushed forward at once.'
    )
    world.para()
    pred = predict(world, "Beacon")
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fear"] = pred["fear"]
    if pred["danger"] >= 1:
        world.say(
            f'{params.helper} had to interject. "Wait," {helper.pronoun()} said, '
            f'"that {PROBLEMS[params.problem].label} can grow fast."'
        )
        helper.memes["caution"] += 1
    hero.memes["rush"] += 1
    world.say(
        f'"I can handle it," {params.hero} said, but {params.helper} pointed to '
        f'the heat shimmer and the crowded sidewalk.'
    )
    if params.tool == "sprayer":
        world.say("The little spray wand looked brave, but not brave enough.")
    world.para()
    beacon.meters["heat"] += 1
    beacon.meters["glow"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A bright ring flashed over the block, and {PROBLEMS[params.problem].label} "
        f"began to climb toward the rooftop."
    )
    world.say(f'"{params.hero}!" {params.helper} shouted. "Now!"')
    if response.power >= PROBLEMS[params.problem].danger:
        world.para()
        world.say(
            f"Guardian arrived in a flash and {response.text}."
        )
        world.say(
            "The sparks cooled into tiny gold dots on the lantern glass, and the "
            "street’s danger dropped quiet again."
        )
        world.say(
            f"After that, {params.hero} and {params.helper} stood together under "
            f"the awning, smiling at the safe light."
        )
        hero.memes["relief"] += 1
        helper.memes["relief"] += 1
        world.facts["outcome"] = "contained"
    else:
        world.para()
        world.say(
            f"Guardian arrived in a flash and {response.fail}."
        )
        world.say(
            "The heat spread up the sign, and everyone had to back away to stay safe."
        )
        world.say(
            "The heroes escaped, but the moment turned scary instead of bright."
        )
        world.facts["outcome"] = "burned"
    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        setting=params.setting,
        tool=TOOLS[params.tool],
        problem=PROBLEMS[params.problem],
        response=response,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a superhero story for a young child that uses the word "interject" and takes place in summer.',
        f"Tell a cautionary superhero story where {f['hero'].id} wants to rush toward {f['problem'].label}, but {f['helper'].id} interjects and helps everyone stay safe.",
        f"Write a surprise-filled hero story that includes the word 'seventy' and ends with a calm, safe rescue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    resp = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {f['hero'].id} and {f['helper'].id}, two small heroes in a summer rescue. Their guardian arrives to help when the trouble gets big."),
        ("What surprising thing happened?",
         f"{f['problem'].label.capitalize()} appeared in the summer heat, and it made the street feel suddenly exciting and dangerous. The surprise is what pushed the heroes into action."),
        ("Why did the helper interject?",
         f"{f['helper'].id} interjected because the danger could grow fast. {f['helper'].id} wanted {f['hero'].id} to slow down and choose the safe move instead of rushing in."),
    ]
    if f.get("outcome") == "contained":
        qa.append((
            "How did the story end?",
            f"The guardian used the right rescue method and the danger was contained. The ending image is quiet and bright: the heroes are safe under the awning with the sparks cooled down."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"The rescue method was too weak, so the heat spread and the heroes had to back away. Everyone escaped safely, but the ending is scary and warns that rushing can make trouble worse."
        ))
    qa.append((
        "What did the guardian do?",
        f"Guardian came in quickly and {resp.qa_text}. That helped turn the surprise into a safe ending."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["tool"].tags) | set(f["problem"].tags) | set(f["response"].tags)
    items = []
    if "safe" in tags:
        items.append((
            "What does a shield do in a hero story?",
            "A shield helps block danger so a hero can protect someone or something. In a careful rescue, it gives the hero a safer way to act."
        ))
    if "summer" in tags:
        items.append((
            "What is summer like?",
            "Summer is usually hot and bright, with long sunny days. That heat can make a story feel lively and a little more risky."
        ))
    if "seventy" in tags:
        items.append((
            "What does seventy mean?",
            "Seventy is a number that comes after sixty-nine and before seventy-one. It is a lot more than a few, so it can help show a big crowd or many sparks."
        ))
    return items


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
danger(seventy) :- problem(seventy).
cautionary(interject) :- word(interject).
summer_scene(summer) :- setting(summer).
valid_story(S, T, P) :- setting(S), tool(T), problem(P), safe_tool(T), rising_problem(P).
safe_tool(shield).
safe_tool(cape).
rising_problem(seventy).
rising_problem(sunwheel).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.safe:
            lines.append(asp.fact("safe_tool", tid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.can_rise:
            lines.append(asp.fact("rising_problem", pid))
    lines.append(asp.fact("word", "interject"))
    lines.append(asp.fact("word", "summer"))
    lines.append(asp.fact("word", "seventy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("tool", TOOLS), ("problem", PROBLEMS), ("response", RESPONSES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(HERO_NAMES if gender == "girl" else HELPER_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, problem = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        tool=tool,
        problem=problem,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=args.parent,
        trait=trait,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, tool, problem) combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(StoryParams(**p)))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.problem} in summer ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
