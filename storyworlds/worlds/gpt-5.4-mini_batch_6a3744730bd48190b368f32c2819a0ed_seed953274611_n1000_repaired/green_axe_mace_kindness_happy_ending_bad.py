#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_green_axe_mace_kindness_happy_ending_bad.py
============================================================================

A small superhero story world about a child hero, a stolen green gadget, a choice
between an axe and a mace, and a kindness turn that can lead to either a happy
ending or a bad ending depending on the hero's choices and timing.

The world keeps the story tiny and classical:
- a hero patrols a city block
- a troublemaker threatens something precious
- the hero can choose force, kindness, or both
- kindness can de-escalate; violence can backfire
- a happy ending shows repair and trust
- a bad ending shows damage, regret, and a harder lesson

It includes the seed words green, axe, and mace, and supports both a gentle
resolution and a darker one. The story text is driven by world state: meters for
physical damage and memes for emotions.
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
KINDNESS_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    color: str = ""
    tool: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Tool:
    id: str
    noun: str
    color: str
    kind: str  # "axe" or "mace"
    force: int
    kindness: int
    safe: bool = False
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
class Threat:
    id: str
    noun: str
    danger: int
    breaks: str
    can_be_repaired: bool = True
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
class StoryParams:
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    tool: str
    threat: str
    ending: str
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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_fear(world: World) -> list[str]:
    out = []
    if world.get("city").meters["danger"] >= THRESHOLD:
        for eid in ("hero", "helper"):
            world.get(eid).memes["fear"] += 1
        sig = ("fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__fear__")
    return out


def _r_damage(world: World) -> list[str]:
    out = []
    if world.get("threat").meters["damage"] < THRESHOLD:
        return out
    sig = ("damage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("city").meters["damage"] += 1
    out.append("__damage__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("damage", _r_damage)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


TOOLS = {
    "green_axe": Tool(id="green_axe", noun="green axe", color="green", kind="axe", force=3, kindness=0, safe=False),
    "green_mace": Tool(id="green_mace", noun="green mace", color="green", kind="mace", force=4, kindness=0, safe=False),
    "kindness_shield": Tool(id="kindness_shield", noun="kind words", color="green", kind="kindness", force=0, kindness=4, safe=True),
}

THREATS = {
    "broken_bridge": Threat(id="broken_bridge", noun="broken bridge", danger=2, breaks="the bridge railing"),
    "stuck_gate": Threat(id="stuck_gate", noun="stuck gate", danger=3, breaks="the front gate"),
    "stolen_seed": Threat(id="stolen_seed", noun="stolen green seed", danger=2, breaks="the garden box"),
}

HEROES = ["Nova", "Piper", "Milo", "Zara", "Arlo", "Mina"]
HELPERS = ["Bee", "Jax", "Luna", "Theo", "June", "Kai"]
PARENT_TYPES = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tool in TOOLS:
        for threat in THREATS:
            for ending in ("happy", "bad"):
                if tool == "kindness_shield" and ending == "bad":
                    continue
                combos.append((tool, threat, ending))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with green tools and a kindness turn.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--ending", choices=["happy", "bad"])
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
    if args.tool and args.ending == "bad" and args.tool == "kindness_shield":
        raise StoryError("Kind words do not create the bad-ending action here.")
    combos = [c for c in valid_combos()
              if (args.tool is None or c[0] == args.tool)
              and (args.threat is None or c[1] == args.threat)
              and (args.ending is None or c[2] == args.ending)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tool, threat, ending = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != hero])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender,
                       parent=parent, tool=tool, threat=threat, ending=ending)


def _build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}", role="parent"))
    city = world.add(Entity(id="city", kind="place", label="the city block"))
    threat = world.add(Entity(id="threat", kind="thing", label=THREATS[params.threat].noun))
    tool = TOOLS[params.tool]
    hero.memes["brave"] = 1
    helper.memes["kindness"] = 1 if tool == "kindness_shield" else 0
    world.facts.update(hero=hero, helper=helper, parent=parent, city=city, threat=threat, tool=tool, params=params)
    return world


def tell(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    parent = world.get("parent")
    city = world.get("city")
    threat = world.get("threat")
    tool = TOOLS[params.tool]
    hero.memes["hope"] += 1
    world.say(f"{hero.label_word} and {helper.label_word} watched over {city.label_word} on a bright afternoon.")
    world.say(f"Their special thing was a {tool.color} {tool.kind if tool.kind in ('axe','mace') else 'shield'}, and its name was {tool.noun}.")
    world.say(f"Then a trouble came: {threat.label_word} was causing problems near {THREATS[params.threat].breaks}.")
    world.para()
    if params.ending == "happy":
        if tool.safe:
            hero.memes["kindness"] += tool.kindness
            helper.memes["trust"] += 1
            world.say(f"{helper.label_word} took a deep breath and spoke kindly instead of striking.")
            world.say(f"That gentle choice calmed everyone, and the problem eased without a smash.")
            world.say(f"{parent.label_word.capitalize()} smiled and helped repair {THREATS[params.threat].breaks} with steady hands.")
            world.say(f"In the end, the little heroes used the green help in their hearts, and the city block felt safe again.")
        else:
            hero.memes["kindness"] += 1
            world.say(f"{hero.label_word} held up the {tool.noun} but chose not to swing it at once.")
            world.say(f"Instead, {hero.label_word} used kindness first: a warning, a wave, and a promise to help.")
            world.say(f"The troublemaker backed away, and {parent.label_word} fixed {THREATS[params.threat].breaks} before anyone got hurt.")
            world.say(f"The green tool stayed in the hero's hands, and the day ended with a proud smile.")
    else:
        world.say(f"{hero.label_word} grabbed the {tool.noun} and rushed in too fast.")
        world.say(f"The swing made a loud crack, but it also startled {helper.label_word} and pushed the danger wider.")
        threat_ent = world.get("threat")
        threat_ent.meters["damage"] += THREATS[params.threat].danger
        world.get("city").meters["danger"] += THREATS[params.threat].danger
        propagate(world, narrate=False)
        world.say(f"{parent.label_word.capitalize()} shouted for both children to step back.")
        world.say(f"By the time they listened, {THREATS[params.threat].breaks} was hurt badly, and the block looked sad and messy.")
        world.say(f"The hero learned that a fast swing is not the same thing as true bravery.")


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    tell(world, params)
    story = world.render()
    prompts = [
        f"Write a superhero story that includes the words green, axe, and mace.",
        f"Tell a child-friendly superhero story where {params.hero} faces {THREATS[params.threat].noun} and learns a lesson about kindness.",
        f"Write a story with either a happy ending or a bad ending, depending on whether the hero uses kindness first.",
    ]
    story_qa = [
        QAItem(
            question="What problem did the hero face?",
            answer=f"The hero faced {THREATS[params.threat].noun}. It was causing trouble near {THREATS[params.threat].breaks}, so the hero had to choose what to do next."
        ),
        QAItem(
            question="Why was kindness important in the happy ending?",
            answer="Kindness helped calm the moment before it got worse. That made room for repair and a safer ending."
        ) if params.ending == "happy" else QAItem(
            question="What went wrong in the bad ending?",
            answer="The hero moved too fast and used force before thinking. That made the trouble spread and left more damage behind."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with a clear image of what changed: either the city was repaired and safe again, or the damage was worse and the hero had to learn from it."
        ),
    ]
    world_qa = [
        QAItem(
            question="What color is the special tool in this world?",
            answer="It is green. The story keeps that color visible because it is part of the hero's special gear."
        ),
        QAItem(
            question="What is the difference between an axe and a mace?",
            answer="An axe has a blade for chopping, while a mace has a heavy head for striking. In stories, both can look dramatic, but they are not kind choices by themselves."
        ),
        QAItem(
            question="What does kindness do in a superhero story?",
            answer="Kindness can calm people, make them listen, and create a safer way to solve a problem. It often saves a story from becoming more hurtful."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
tool(axe).
tool(mace).
tool(kindness_shield).

ending(happy).
ending(bad).

valid(Tool, Threat, Ending) :- tool(Tool), threat(Threat), ending(Ending).
kindness_only(kindness_shield).
safe_end(kindness_shield, happy).
unsafe_end(axe, bad).
unsafe_end(mace, bad).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for thr in THREATS:
        lines.append(asp.fact("threat", thr))
    for e in ("happy", "bad"):
        lines.append(asp.fact("ending", e))
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
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        rc = 1
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            s = generate(StoryParams(hero="Nova", hero_gender="girl", helper="Bee", helper_gender="boy", parent="mother", tool="green_axe", threat="broken_bridge", ending="happy"))
            emit(s)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def generate_random_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.tool is None or c[0] == args.tool)
              and (args.threat is None or c[1] == args.threat)
              and (args.ending is None or c[2] == args.ending)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tool, threat, ending = rng.choice(sorted(combos))
    return resolve_params(argparse.Namespace(
        hero=args.hero, hero_gender=args.hero_gender, helper=args.helper, helper_gender=args.helper_gender,
        parent=args.parent, tool=tool, threat=threat, ending=ending
    ), rng)


def valid_combos() -> list[tuple[str, str, str]]:
    return [c for c in ((t, h, e) for t in TOOLS for h in THREATS for e in ("happy", "bad"))
            if not (c[0] == "kindness_shield" and c[2] == "bad")]


CURATED = [
    StoryParams(hero="Nova", hero_gender="girl", helper="Bee", helper_gender="boy", parent="mother", tool="green_axe", threat="broken_bridge", ending="happy"),
    StoryParams(hero="Milo", hero_gender="boy", helper="June", helper_gender="girl", parent="father", tool="green_mace", threat="stuck_gate", ending="bad"),
    StoryParams(hero="Zara", hero_gender="girl", helper="Kai", helper_gender="boy", parent="mother", tool="kindness_shield", threat="stolen_seed", ending="happy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != hero])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(PARENT_TYPES)
    tool = args.tool or rng.choice(list(TOOLS))
    threat = args.threat or rng.choice(list(THREATS))
    ending = args.ending or rng.choice(["happy", "bad"])
    if tool == "kindness_shield" and ending == "bad":
        raise StoryError("Kind words are not used for the bad-ending branch here.")
    return StoryParams(hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, parent=parent, tool=tool, threat=threat, ending=ending)


def build_from_params(params: StoryParams) -> StorySample:
    if params.tool not in TOOLS or params.threat not in THREATS or params.ending not in {"happy", "bad"}:
        raise StoryError("Invalid StoryParams.")
    world = _build_world(params)
    tell(world, params)
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for t, h, e in combos:
            print(t, h, e)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
