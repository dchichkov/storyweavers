#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ecologic_basement_stairs_foreshadowing_pirate_tale.py
======================================================================================

A standalone storyworld for a tiny pirate tale set on basement stairs.

Premise
-------
Two children turn the basement stairs into a pirate ship. The dark stairs need
light, but the story also wants an ecologic choice: use less power, reuse what
they have, and avoid waste. Foreshadowing matters, so the world plants a small
hint early — a damp step, a creaky board, a little drip, or a loose box — and
then pays it off when the pirates head downstairs.

This script follows the storyworld contract:
- typed entities with physical meters and emotional memes
- state-driven narration
- three QA sets generated from world state
- a Python reasonableness gate with an inline ASP twin
- --verify checks parity and does a normal generate smoke test
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    wet: bool = False
    reusable: bool = False
    gives_light: bool = False
    hand_crank: bool = False
    fragile: bool = False

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
    dark_spot: str
    ship_name: str
    clue: str
    ending_image: str
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
class Tool:
    id: str
    label: str
    phrase: str
    eco_score: int
    power: int
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
class Hazard:
    id: str
    label: str
    phrase: str
    risk: str
    spread: int
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
    label: str
    text: str
    fail: str
    sense: int
    power: int
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_damp(world: World) -> list[str]:
    out = []
    stair = world.entities.get("stairs")
    if stair and stair.meters["damp"] >= THRESHOLD and ("damp",) not in world.fired:
        world.fired.add(("damp",))
        for c in world.characters():
            c.memes["caution"] += 1
        out.append("__hint__")
    return out


def _r_slip(world: World) -> list[str]:
    out = []
    stair = world.entities.get("stairs")
    for c in world.characters():
        if c.memes["rush"] < THRESHOLD:
            continue
        if stair and stair.meters["damp"] >= THRESHOLD and ("slip", c.id) not in world.fired:
            world.fired.add(("slip", c.id))
            c.meters["balance"] -= 1
            c.memes["fear"] += 1
            out.append("__slip__")
    return out


CAUSAL_RULES = [Rule("damp", _r_damp), Rule("slip", _r_slip)]


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


def hazard_at_risk(tool: Tool, hazard: Hazard) -> bool:
    return tool.eco_score >= 0 and hazard.spread >= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict_danger(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    sim.get("stairs").meters["damp"] = 1
    _send_down(sim, narrate=False)
    return {"slip": sim.get("hero").memes["fear"] >= THRESHOLD, "damp": sim.get("stairs").meters["damp"]}


def _send_down(world: World, narrate: bool = True) -> None:
    world.get("hero").memes["rush"] += 1
    world.get("stairs").meters["travel"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon, {a.id} and {b.id} turned {setting.place} into "
        f"{setting.ship_name}. A blanket became a sail, a broom became a mast, "
        f"and a cardboard box became treasure."
    )
    world.say(
        f'"Captain {a.id} and Mate {b.id}!" {a.id} cried. "Let\'s hunt the gold below the stairs!"'
    )


def foreshadow(world: World, setting: Setting, hazard: Hazard) -> None:
    world.get("stairs").meters["damp"] = 1
    world.say(
        f"But near {setting.dark_spot}, a small clue waited: {setting.clue}. '
        f'That little sign made the stairs feel less like a game and more like a test.'
    )


def need_light(world: World, a: Entity, tool: Tool) -> None:
    world.say(
        f'{a.id} peered into the dark. "We need a light," {a.pronoun()} said. '
        f'But {tool.label} was the ecologic choice — bright enough, and kinder to power.'
    )


def warn(world: World, b: Entity, a: Entity, hazard: Hazard) -> None:
    pred = predict_danger(world, hazard)
    b.memes["caution"] += 1
    world.facts["predicted_slip"] = pred["slip"]
    world.say(
        f'{b.id} touched the rail and frowned. "{hazard.label} can make the step slick," '
        f"{b.pronoun()} warned. " 
        f'{"I saw it coming from that clue."}'
    )


def choose(world: World, a: Entity, tool: Tool) -> None:
    a.memes["ecologic"] += 1
    world.say(
        f'{a.id} looked at {tool.label} and grinned. "That is the ecologic way," '
        f'{a.pronoun()} said. "No waste, no fuss, and still plenty bright."'
    )


def proceed(world: World, a: Entity, b: Entity, hazard: Hazard) -> None:
    a.memes["rush"] += 1
    if world.get("stairs").meters["damp"] >= THRESHOLD:
        world.say(
            f"They went carefully, and the earlier clue mattered. One foot slowed, '
            f'then the other, so the damp step did not catch them off guard.'
        )
    else:
        world.say(f"They dashed down the stairs like waves chasing a ship.")


def turn(world: World, a: Entity, b: Entity, tool: Tool, hazard: Hazard) -> None:
    if world.get("stairs").meters["damp"] >= THRESHOLD:
        world.say(
            f"At the risky step, {b.id} leaned close and pointed it out before anyone slipped. "
            f"The clue from before had been a warning all along."
        )
    world.say(
        f"{tool.label} lit the way, and the pirates still found the treasure without wasting power."
    )


def ending(world: World, a: Entity, b: Entity, setting: Setting, tool: Tool) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At the bottom, {setting.ending_image}. {a.id} held the {tool.label} steady, "
        f"and {b.id} laughed as the little ship ride ended safely."
    )


def tell(setting: Setting, hero_name: str, mate_name: str, tool: Tool, hazard: Hazard, response: Response) -> World:
    w = World()
    hero = w.add(Entity(id="hero", kind="character", type="boy", label=hero_name))
    mate = w.add(Entity(id="mate", kind="character", type="girl", label=mate_name))
    stairs = w.add(Entity(id="stairs", type="place", label="the basement stairs"))
    w.add(Entity(id="lantern", type="thing", label=tool.label, gives_light=True, reusable=True, hand_crank=True))
    w.add(Entity(id="drip", type="thing", label=hazard.label, wet=True, fragile=True))
    intro(w, hero, mate, setting)
    foreshadow(w, setting, hazard)
    w.para()
    need_light(w, hero, tool)
    warn(w, mate, hero, hazard)
    choose(w, hero, tool)
    proceed(w, hero, mate, hazard)
    w.para()
    turn(w, hero, mate, tool, hazard)
    ending(w, hero, mate, setting, tool)
    w.facts.update(hero=hero, mate=mate, setting=setting, tool=tool, hazard=hazard, response=response)
    return w


SETTINGS = {
    "basement_stairs": Setting(
        id="basement_stairs",
        place="the basement stairs",
        dark_spot="the step halfway down",
        ship_name="a pirate ship",
        clue="a little drip had left one step shiny and wet",
        ending_image="the stairs felt like a safe little harbor, with the treasure box waiting below",
    )
}

TOOLS = {
    "hand_crank_lantern": Tool(
        id="hand_crank_lantern",
        label="a hand-crank lantern",
        phrase="a hand-crank lantern",
        eco_score=3,
        power=3,
        tags={"ecologic", "light"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="a flashlight",
        phrase="a flashlight",
        eco_score=2,
        power=2,
        tags={"light"},
    ),
}

HAZARDS = {
    "damp_step": Hazard(
        id="damp_step",
        label="the damp step",
        phrase="a damp step",
        risk="slip",
        spread=2,
        tags={"wet", "foreshadowing"},
    )
}

RESPONSES = {
    "slow_down": Response(
        id="slow_down",
        label="slow down and hold the rail",
        text="slowly held the rail and crossed the stairs one careful step at a time",
        fail="tried to rush, but the wet step nearly sent them sliding",
        sense=3,
        power=3,
        tags={"safe"},
    ),
    "call_grownup": Response(
        id="call_grownup",
        label="call a grown-up",
        text="called a grown-up, who dried the step and made the path safe",
        fail="waited too long, and the little slip happened anyway",
        sense=3,
        power=4,
        tags={"safe"},
    ),
    "ignore": Response(
        id="ignore",
        label="ignore it",
        text="ignored the wet step",
        fail="ignored the wet step and made everything worse",
        sense=1,
        power=0,
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn"]
TRAITS = ["curious", "bold", "careful", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    tool: str
    hazard: str
    response: str
    hero_name: str
    mate_name: str
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
            for hid, hazard in HAZARDS.items():
                if hazard_at_risk(tool, hazard):
                    combos.append((sid, tid, hid))
    return combos


def explain_rejection(tool: Tool, hazard: Hazard) -> str:
    return (
        f"(No story: {tool.label} and {hazard.label} do not support a strong "
        f"foreshadowing turn in this tiny world. Pick the basement stairs hazard.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny pirate tale on basement stairs with ecologic foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--mate")
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.tool and args.hazard and not hazard_at_risk(TOOLS[args.tool], HAZARDS[args.hazard]):
        raise StoryError(explain_rejection(TOOLS[args.tool], HAZARDS[args.hazard]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, hazard = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_name = args.name or rng.choice(BOY_NAMES)
    mate_name = args.mate or rng.choice(GIRL_NAMES)
    return StoryParams(setting=setting, tool=tool, hazard=hazard, response=response, hero_name=hero_name, mate_name=mate_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a 3-to-5-year-old set on {f["setting"].place} that includes the word "ecologic".',
        f"Tell a story where {f['hero'].id} and {f['mate'].id} play pirates on the basement stairs, notice a clue first, and then make the ecologic choice for light.",
        f"Write a foreshadowing story on the basement stairs where a small wet clue matters later, and the ending feels safe and smart.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, setting, tool, hazard = f["hero"], f["mate"], f["setting"], f["tool"], f["hazard"]
    answers = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {mate.id}, two children who turned the basement stairs into a pirate ship. The tale follows how they found a safe way to keep playing.",
        ),
        QAItem(
            question="What clue foreshadowed trouble?",
            answer=f"A little drip had left one step shiny and wet. That clue mattered later because the damp step could make someone slip.",
        ),
        QAItem(
            question="What did the children choose for light?",
            answer=f"They chose {tool.label}, which was the ecologic choice. It gave them light without wasting much power.",
        ),
        QAItem(
            question="Why did the warning matter?",
            answer=f"{mate.id} noticed the damp step before they rushed down. That warning mattered because the earlier clue had already shown that the stairs were slick.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the pirate pair reaching the bottom safely and laughing beside the treasure box. The stairs became a safe little harbor instead of a risky path.",
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ecologic mean in a story like this?",
            answer="It means making a choice that wastes less power or fewer resources. An ecologic choice is kinder to the world and still gets the job done.",
        ),
        QAItem(
            question="Why is a damp step dangerous?",
            answer="A damp step can be slippery, so a foot may slide on it. On stairs, a slide can make someone fall.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint before something important happens later. The hint helps the reader notice the danger or the change coming.",
        ),
        QAItem(
            question="Why is a hand-crank lantern a good pirate light?",
            answer="A hand-crank lantern gives light without needing lots of batteries or extra electricity. That makes it a useful ecologic choice for a play adventure.",
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.tool not in TOOLS or params.hazard not in HAZARDS or params.response not in RESPONSES:
        raise StoryError("(Invalid params: unknown setting/tool/hazard/response.)")
    response = RESPONSES[params.response]
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    world = tell(SETTINGS[params.setting], params.hero_name, params.mate_name, TOOLS[params.tool], HAZARDS[params.hazard], response)
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


ASP_RULES = r"""
valid(S,T,H) :- setting(S), tool(T), hazard(H), eco_ok(T), risky(T,H).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
outcome(safe) :- chosen_response(R), chosen_tool(T), chosen_hazard(H), sensible(R), eco_ok(T), risky(T,H).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("eco_ok", tid))
        lines.append(asp.fact("power", tid, t.power))
        lines.append(asp.fact("eco_score", tid, t.eco_score))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("risky", "hand_crank_lantern", hid))
        lines.append(asp.fact("risky", "flashlight", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from valid_combos().")
    if {r.id for r in sensible_responses()} == set(asp_sensible()):
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH: sensible responses differ.")
    try:
        sample = generate(StoryParams(setting="basement_stairs", tool="hand_crank_lantern", hazard="damp_step", response="slow_down", hero_name="Tom", mate_name="Mia"))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(setting="basement_stairs", tool="hand_crank_lantern", hazard="damp_step", response="slow_down", hero_name="Tom", mate_name="Mia"),
    StoryParams(setting="basement_stairs", tool="flashlight", hazard="damp_step", response="call_grownup", hero_name="Ben", mate_name="Lily"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
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
