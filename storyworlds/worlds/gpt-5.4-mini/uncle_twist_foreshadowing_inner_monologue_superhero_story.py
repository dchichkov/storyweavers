#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/uncle_twist_foreshadowing_inner_monologue_superhero_story.py
=============================================================================================

A standalone story world about a child, an uncle, and a superhero-style rescue
that uses foreshadowing, inner monologue, and a twist to drive the turn.

Domain premise
--------------
A child and an uncle play superheroes in a neighborhood at dusk. The child wants
to help with a "big mission," notices little clues that something is up, and
narrates a worried inner monologue. The apparent mystery turns into a twist:
the uncle's strange behavior was not villainy at all, but careful preparation
for a real, small-scale rescue. The story ends with a concrete image that proves
what changed.

This world is modeled with typed entities, physical meters, and emotional memes.
State changes, not a frozen paragraph, determine the prose.
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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"uncle": "uncle", "mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    label: str
    place: str
    evening_detail: str
    sound: str

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
    clue: str
    label: str
    hidden_reason: str
    foreshadow: str
    trigger: str
    twist_hint: str
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
class RescueTool:
    id: str
    label: str
    phrase: str
    use: str
    power: int
    sense: int
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
class Outcome:
    id: str
    text: str
    effect: str
    ending: str
    qa_text: str
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


def _r_worry(world: World) -> list[str]:
    out = []
    kid = world.get("kid")
    if kid.memes["worry"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        kid.memes["fear"] += 1
        out.append("__inner__")
    return out


def _r_alert(world: World) -> list[str]:
    out = []
    if world.get("lantern").meters["ready"] >= THRESHOLD and ("alert",) not in world.fired:
        world.fired.add(("alert",))
        world.get("uncle").memes["calm"] += 1
        out.append("__clue__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("worry", "social", _r_worry),
    Rule("alert", "physical", _r_alert),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(mystery: Mystery, tool: RescueTool) -> bool:
    return tool.sense >= SENSE_MIN and mystery.id in {"lost_kitten", "stuck_balloon", "blocked_door"}


def good_tools() -> list[RescueTool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def _predict(world: World, mystery: Mystery, tool: RescueTool) -> dict:
    sim = world.copy()
    _do_mystery(sim, sim.get("kid"), mystery, narrate=False)
    _do_rescue(sim, sim.get("uncle"), sim.get("kid"), mystery, tool, narrate=False)
    return {
        "resolved": sim.get("problem").meters["fixed"] >= THRESHOLD,
        "fear": sim.get("kid").memes["fear"],
    }


def _do_mystery(world: World, kid: Entity, mystery: Mystery, narrate: bool = True) -> None:
    kid.meters["alert"] += 1
    kid.memes["worry"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, kid: Entity, uncle: Entity, setting: Setting) -> None:
    kid.memes["joy"] += 1
    world.say(
        f"At {setting.place}, {kid.id} and {uncle.id} played superheroes while "
        f"{setting.sound} drifted through the air."
    )
    world.say(
        f"{setting.evening_detail} made the street look like it was waiting for a rescue."
    )


def foreshadow(world: World, kid: Entity, mystery: Mystery) -> None:
    world.say(
        f"{kid.id} noticed a small clue: {mystery.foreshadow}. "
        f"That clue made the day feel a little mysterious."
    )
    world.say(
        f"In {kid.id}'s head, one thought kept spinning: maybe something big was hiding nearby."
    )


def inner_monologue(world: World, kid: Entity, mystery: Mystery) -> None:
    kid.memes["worry"] += 1
    world.say(
        f'In {kid.id}\'s mind, the question got louder: "What if {mystery.hidden_reason}?"'
    )
    world.say(
        f"{kid.id} clenched {kid.pronoun('possessive')} tiny fists and tried to look brave."
    )


def clue_move(world: World, uncle: Entity, mystery: Mystery) -> None:
    uncle.meters["mystery"] += 1
    world.say(
        f"{uncle.id} kept glancing at {mystery.label}, and {kid_name(world)} wondered why."
    )
    world.say(
        f"{uncle.id} said, \"Stay close. A hero always watches the edges first.\""
    )


def kid_name(world: World) -> str:
    return world.get("kid").id


def twist_turn(world: World, uncle: Entity, mystery: Mystery, tool: RescueTool) -> None:
    world.say(
        f"Then the twist arrived: {uncle.id} was not hiding a villain plan at all. "
        f"{uncle.id} had been carrying {tool.phrase} for the rescue."
    )
    world.say(
        f"{mystery.twist_hint} The odd pause, the careful look, and the quiet pockets all made sense now."
    )


def rescue(world: World, uncle: Entity, kid: Entity, mystery: Mystery, tool: RescueTool) -> None:
    world.get("problem").meters["fixed"] += 1
    kid.memes["worry"] = 0.0
    kid.memes["joy"] += 1
    uncle.memes["pride"] += 1
    world.say(
        f"{uncle.id} used {tool.phrase} to {tool.use}, and the little crisis ended."
    )
    world.say(
        f"{tool.label.capitalize()} gave a bright, steady glow, and the danger stopped moving."
    )


def reveal(world: World, uncle: Entity, kid: Entity, mystery: Mystery, tool: RescueTool) -> None:
    world.say(
        f"{uncle.id} knelt down and grinned. \"I wanted you to notice the clue,\" "
        f"{uncle.id} said. \"That way you'd learn how a hero thinks before acting.\""
    )
    world.say(
        f"{kid.id}'s cheeks warmed with relief, because {mystery.label} had never been a trap."
    )


def ending(world: World, kid: Entity, uncle: Entity, setting: Setting, outcome: Outcome) -> None:
    if outcome.id == "happy":
        world.say(
            f"By the end, {kid.id} stood beside {uncle.id} with {outcome.ending}, "
            f"and the street looked safe and shiny again."
        )
    else:
        world.say(
            f"By the end, {kid.id} and {uncle.id} were safe, even though {outcome.effect}."
        )


def tell(setting: Setting, mystery: Mystery, tool: RescueTool, outcome: Outcome,
         kid_name_text: str = "Milo", kid_gender: str = "boy",
         uncle_name: str = "Uncle Ben") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name_text, kind="character", type=kid_gender, role="hero"))
    uncle = world.add(Entity(id=uncle_name, kind="character", type="uncle", role="uncle"))
    world.add(Entity(id="problem", type="problem", label=mystery.label))
    world.add(Entity(id="lantern", type="tool", label=tool.label))
    world.get("lantern").meters["ready"] = 1
    world.facts["mystery"] = mystery
    world.facts["tool"] = tool
    world.facts["setting"] = setting

    introduce(world, kid, uncle, setting)
    world.para()
    foreshadow(world, kid, mystery)
    inner_monologue(world, kid, mystery)
    clue_move(world, uncle, mystery)
    world.para()
    _do_mystery(world, kid, mystery)
    twist_turn(world, uncle, mystery, tool)
    rescue(world, uncle, kid, mystery, tool)
    reveal(world, uncle, kid, mystery, tool)
    world.para()
    ending(world, kid, uncle, setting, outcome)
    world.facts["outcome"] = outcome
    return world


SETTINGS = {
    "dusk_block": Setting("dusk_block", "the block", "on the sidewalk by the corner store",
                          "The sky was turning purple", "a soft siren hummed far away"),
    "rooftop": Setting("rooftop", "the rooftop garden", "on the rooftop garden",
                       "The sunset painted the chimneys gold", "a helicopter thumped overhead"),
    "alley": Setting("alley", "the alley", "in the alley behind the bakery",
                      "The lamps were flicking on one by one", "a scooter buzzed past"),
}

MYSTERIES = {
    "lost_kitten": Mystery(
        "lost_kitten",
        clue="a tiny paw print on the curb",
        label="the little paw print",
        hidden_reason="a lost kitten was trapped behind the storage gate",
        foreshadow="a faint mew came from behind the fence",
        trigger="a kitten call",
        twist_hint="The paw print matched the kitten, not a monster.",
        tags={"kitten", "clue", "twist"},
    ),
    "stuck_balloon": Mystery(
        "stuck_balloon",
        clue="a red ribbon fluttering from the tree",
        label="the red ribbon",
        hidden_reason="a balloon had snagged on the branches",
        foreshadow="something red kept bobbing above the leaves",
        trigger="a balloon rescue",
        twist_hint="The ribbon belonged to a balloon, not a bad guy.",
        tags={"balloon", "clue", "twist"},
    ),
    "blocked_door": Mystery(
        "blocked_door",
        clue="a thin line of light under the basement door",
        label="the basement door",
        hidden_reason="a trapped neighbor needed help opening the jammed door",
        foreshadow="a worried knock thumped from downstairs",
        trigger="a door rescue",
        twist_hint="The closed door was a problem to solve, not a secret lair.",
        tags={"door", "clue", "twist"},
    ),
}

TOOLS = {
    "lantern": RescueTool("lantern", "lantern", "a small lantern", "light the way", 3, 3, {"light"}),
    "flashlight": RescueTool("flashlight", "flashlight", "a bright flashlight", "light the dark corner", 3, 3, {"light"}),
    "rope": RescueTool("rope", "rope", "a loop of rope", "pull the gate open", 2, 2, {"rope"}),
    "gloves": RescueTool("gloves", "gloves", "a pair of gloves", "lift the stuck lid", 2, 2, {"gloves"}),
    "water": RescueTool("water", "water bottle", "a bottle of water", "cool the hot pavement", 1, 1, {"water"}),
}

OUTCOMES = {
    "happy": Outcome("happy", "the rescue worked", "everything was fixed", "the lantern beam on the sidewalk",
                     "The rescue worked, and the lantern beam shone like a badge."),
    "soft": Outcome("soft", "the rescue took time", "the problem was only partly solved", "the street still looked worried",
                    "The rescue took time, but the heroes kept trying."),
}

CURATED = [
    StoryParams("dusk_block", "lost_kitten", "lantern", "Milo", "boy", "Uncle Ben"),
    StoryParams("rooftop", "stuck_balloon", "flashlight", "Ivy", "girl", "Uncle Ray"),
    StoryParams("alley", "blocked_door", "rope", "Nora", "girl", "Uncle Tom"),
]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    kid_name: str
    kid_gender: str
    uncle_name: str
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
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for tid, tool in TOOLS.items():
                if reasonableness_gate(mystery, tool):
                    combos.append((sid, mid, tid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery"]
    tool = f["tool"]
    kid = world.get("kid")
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the word "uncle" and a twist.',
        f"Tell a story where {kid.id} suspects something big is happening, notices {mystery.clue}, and finds out {tool.label} was meant for a rescue.",
        f"Write a gentle superhero story with foreshadowing and an inner monologue, ending with a safe rescue and a kind uncle.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mystery = f["mystery"]
    tool = f["tool"]
    kid = world.get("kid")
    uncle = world.get("uncle")
    qa = [
        ("Who is the story about?",
         f"It is about {kid.id} and {uncle.id}, who were pretending to be superheroes together."),
        ("What clue did {0} notice?".format(kid.id),
         f"{kid.id} noticed {mystery.clue}. That small clue made {kid.id} wonder if something mysterious was happening."),
        ("What did {0} think in {0}'s head?".format(kid.id),
         f"{kid.id} worried that {mystery.hidden_reason}. That inner thought made the story feel tense before the twist."),
        ("What was the twist?",
         f"The twist was that {uncle.id} was not hiding a bad secret. {uncle.id} had {tool.phrase} ready to help with the rescue."),
        ("How did the story end?",
         f"It ended safely, with {kid.id} and {uncle.id} standing together after the problem was fixed. The final image proves the rescue worked."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["tool"].tags)
    out = []
    if "kitten" in tags:
        out.append(("Why do kittens sometimes need help?", "Kittens can be small and get stuck in places they cannot climb out of by themselves. A grown-up can help them safely."))
    if "balloon" in tags:
        out.append(("Why can a balloon get stuck in a tree?", "A balloon can drift upward when the wind carries it away. If it catches on branches, it can stay stuck until someone reaches it."))
    if "door" in tags:
        out.append(("What does a flashlight do?", "A flashlight makes a bright beam so people can see in the dark without any flame."))
    if "light" in tags:
        out.append(("Why do heroes carry lights at dusk?", "At dusk it gets hard to see corners, gates, and steps. A light helps a hero watch carefully and stay safe."))
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(mystery: Mystery, tool: RescueTool) -> str:
    if tool.sense < SENSE_MIN:
        return f"(No story: {tool.label} is too weak a rescue tool for this superhero story.)"
    return f"(No story: {mystery.label} and {tool.label} do not make a good small rescue scene.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A superhero story world with uncle, foreshadowing, inner monologue, and a twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--kid-name")
    ap.add_argument("--kid-gender", choices=["boy", "girl"])
    ap.add_argument("--uncle-name")
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
    if args.tool and args.mystery:
        if not reasonableness_gate(MYSTERIES[args.mystery], TOOLS[args.tool]):
            raise StoryError(explain_rejection(MYSTERIES[args.mystery], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool = rng.choice(sorted(combos))
    kid_gender = args.kid_gender or rng.choice(["boy", "girl"])
    kid_name = args.kid_name or rng.choice(["Milo", "Ivy", "Nora", "Finn", "Lena"])
    uncle_name = args.uncle_name or rng.choice(["Uncle Ben", "Uncle Ray", "Uncle Tom", "Uncle Jax"])
    return StoryParams(setting, mystery, tool, kid_name, kid_gender, uncle_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], TOOLS[params.tool],
                 OUTCOMES["happy"], params.kid_name, params.kid_gender, params.uncle_name)
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


ASP_RULES = r"""
valid(S, M, T) :- setting(S), mystery(M), tool(T), sense(T, V), sense_min(Min), V >= Min, reason_ok(M, T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for mid in MYSTERIES:
        lines.append(asp.fact("reason_ok", mid, "lantern"))
        lines.append(asp.fact("reason_ok", mid, "flashlight"))
        lines.append(asp.fact("reason_ok", mid, "rope"))
        lines.append(asp.fact("reason_ok", mid, "gloves"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("dusk_block", "lost_kitten", "lantern", "Milo", "boy", "Uncle Ben"),
    StoryParams("rooftop", "stuck_balloon", "flashlight", "Ivy", "girl", "Uncle Ray"),
    StoryParams("alley", "blocked_door", "rope", "Nora", "girl", "Uncle Tom"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        if args.all:
            p = sample.params
            header = f"### {p.kid_name} and {p.uncle_name}: {p.mystery} at {p.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
