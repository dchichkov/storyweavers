#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/frost_bravery_folk_tale.py
==========================================================

A small folk-tale storyworld about frost, bravery, and a village task gone
wrong before turning right again.

Premise:
- A child is asked to cross a frosty place to get or deliver something needed.
- The cold is a real obstacle, and fear is a real emotional force.
- Bravery is the turning point: the child acts anyway, usually with a helper,
  a tool, or a wiser route.

The world is intentionally tiny and classical:
- typed entities with meters and memes
- causal state drives narration
- a reasonableness gate plus an ASP twin
- three Q&A sets grounded in world state, not rendered text

Run it:
    python storyworlds/worlds/gpt-5.4-mini/frost_bravery_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/frost_bravery_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/frost_bravery_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/frost_bravery_folk_tale.py --verify
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
BRAVERY_MIN = 2


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
    warm: bool = False
    carries: bool = False
    can_clear: bool = False
    can_cross: bool = False
    gives_lamp: bool = False

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
class Crossing:
    id: str
    place: str
    adjective: str
    risk: str
    obstacle: str
    path: str
    width: str
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
class HelpAction:
    id: str
    sense: int
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
    tag: str
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


def _r_frost(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["cold"] < THRESHOLD:
            continue
        sig = ("frost", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.kind == "character":
            ent.memes["shiver"] += 1
        out.append("__cold__")
    return out


def _r_courage(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    helper = world.facts.get("helper")
    if not hero or not helper:
        return out
    if hero.memes["bravery"] >= BRAVERY_MIN and helper.memes["trust"] >= 1:
        sig = ("courage", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["hope"] += 1
        helper.memes["hope"] += 1
        out.append("__courage__")
    return out


CAUSAL_RULES = [Rule("frost", "physical", _r_frost), Rule("courage", "social", _r_courage)]


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


def frosty_at_risk(crossing: Crossing, tool: Tool) -> bool:
    return "frost" in crossing.tags and "warm" in tool.tags


def sensible_actions() -> list[HelpAction]:
    return [a for a in HELP.values() if a.sense >= BRAVERY_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for cid, c in CROSSINGS.items():
        for tid, t in TOOLS.items():
            if frosty_at_risk(c, t):
                combos.append((cid, tid, "cross"))
    return combos


def predict(world: World, crossing_id: str) -> dict:
    sim = world.copy()
    hero = sim.facts["hero"]
    _cross(sim, hero, sim.facts["crossing"], narrate=False)
    return {"cold": hero.meters["cold"], "fear": hero.memes["fear"]}


def _cross(world: World, hero: Entity, crossing: Crossing, narrate: bool = True) -> None:
    hero.meters["cold"] += 1
    hero.memes["fear"] += 1
    propagate(world, narrate=narrate)


def tell_opening(world: World, hero: Entity, helper: Entity, crossing: Crossing) -> None:
    hero.memes["bravery"] += 2
    helper.memes["trust"] += 1
    world.say(
        f"On a clear morning, {hero.id} and {helper.id} went to {crossing.place}, "
        f"where the {crossing.adjective} ground held a hush of frost."
    )
    world.say(
        f"{hero.id} was the sort of child who listened to the wind and still took one more step."
    )


def need(world: World, hero: Entity, crossing: Crossing) -> None:
    world.say(
        f"But the {crossing.obstacle} made the path look sharp and white, and {hero.id} knew it was a hard way to cross."
    )
    world.say(f'"We need a way through," {hero.id} said.')


def warn(world: World, helper: Entity, hero: Entity, crossing: Crossing, tool: Tool) -> None:
    pred = predict(world, crossing.id)
    helper.memes["care"] += 1
    world.facts["predicted_cold"] = pred["cold"]
    world.say(
        f'{helper.id} put on a brave face. "That frost will bite your feet and slow you down, '
        f'but we can choose {tool.phrase} and keep going."'
    )


def hesitate(world: World, hero: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(f"{hero.id} took a breath and looked back once, but the road ahead was still calling.")


def choose(world: World, hero: Entity, helper: Entity, tool: Tool, crossing: Crossing) -> None:
    hero.memes["bravery"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then {hero.id} held tight to {tool.phrase}, and {helper.id} walked beside {hero.pronoun('object')}."
    )


def brave_cross(world: World, hero: Entity, helper: Entity, tool: Tool, crossing: Crossing, action: HelpAction) -> None:
    hero.meters["cold"] = 0.0
    hero.memes["fear"] = 0.0
    helper.memes["relief"] += 1
    world.say(
        f"They used {tool.phrase}. {action.text.replace('{crossing}', crossing.place)}."
    )
    world.say(
        f"The frost stayed on the stones, but it did not win. {hero.id} crossed with a steady heart."
    )


def brave_fail(world: World, hero: Entity, helper: Entity, tool: Tool, crossing: Crossing, action: HelpAction) -> None:
    hero.meters["cold"] += 1
    hero.memes["fear"] += 2
    world.say(
        f"They tried {tool.phrase}, but {action.fail.replace('{crossing}', crossing.place)}."
    )
    world.say(
        f"Even so, {helper.id} kept close, and {hero.id} learned that bravery can mean turning back and trying again."
    )


def ending(world: World, hero: Entity, helper: Entity, crossing: Crossing, action: HelpAction, success: bool) -> None:
    if success:
        world.say(
            f"At last the two of them reached the other side, rosy-cheeked and laughing, while the frost glittered harmlessly behind them."
        )
    else:
        world.say(
            f"They went home together with numb noses and wiser minds, and the next day they came back with a better plan."
        )


def tell(crossing: Crossing, tool: Tool, action: HelpAction, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, parent_type: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    ice = world.add(Entity(id="path", type="place", label=crossing.place))
    ice.meters["cold"] = 1.0

    hero.memes["bravery"] = 3.0
    helper.memes["trust"] = 2.0
    world.facts.update(hero=hero, helper=helper, parent=parent, crossing=crossing, tool=tool, action=action)

    tell_opening(world, hero, helper, crossing)
    world.para()
    need(world, hero, crossing)
    warn(world, helper, hero, crossing, tool)
    hesitate(world, hero)
    choose(world, hero, helper, tool, crossing)
    world.para()

    success = action.power >= 1
    if success:
        brave_cross(world, hero, helper, tool, crossing, action)
    else:
        brave_fail(world, hero, helper, tool, crossing, action)
    ending(world, hero, helper, crossing, action, success)

    world.facts["outcome"] = "success" if success else "fail"
    return world


CROSSINGS = {
    "bridge": Crossing(
        id="bridge",
        place="the old stone bridge",
        adjective="frosty",
        risk="slip",
        obstacle="the slick stones",
        path="the bridge",
        width="narrow",
        tags={"frost", "bridge"},
    ),
    "hill": Crossing(
        id="hill",
        place="the hill path",
        adjective="white with frost",
        risk="slip",
        obstacle="the frozen grass",
        path="the path",
        width="wide",
        tags={"frost", "hill"},
    ),
    "well": Crossing(
        id="well",
        place="the well road",
        adjective="cold and pale",
        risk="shiver",
        obstacle="the thin rime",
        path="the road",
        width="narrow",
        tags={"frost", "road"},
    ),
}

TOOLS = {
    "boots": Tool(id="boots", label="wool boots", phrase="the wool boots", effect="warm", tags={"warm", "feet"}),
    "cloak": Tool(id="cloak", label="a thick cloak", phrase="the thick cloak", effect="warm", tags={"warm", "body"}),
    "lantern": Tool(id="lantern", label="a lantern", phrase="the lantern", effect="light", tags={"light"}),
}

HELP = {
    "steady": HelpAction(
        id="steady",
        sense=3,
        power=2,
        text="the boots warmed their feet, and the road seemed less sharp",
        fail="the boots were not enough for such a cold road",
        qa_text="warmed their feet and made the road easier to face",
    ),
    "cloak": HelpAction(
        id="cloak",
        sense=3,
        power=2,
        text="the cloak wrapped around them like a soft little tent of courage",
        fail="the cloak flapped in the wind and could not stop the frost",
        qa_text="wrapped them in warmth so they could keep walking",
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Tess", "Lena", "Ada", "Ona"]
BOY_NAMES = ["Finn", "Jory", "Pavel", "Oren", "Milo", "Drew"]
TRAITS = ["bold", "curious", "careful", "bright", "lively"]


@dataclass
class StoryParams:
    crossing: str
    tool: str
    action: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str = "bold"
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
    ap = argparse.ArgumentParser(description="Frost and bravery folk tale storyworld.")
    ap.add_argument("--crossing", choices=CROSSINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--action", choices=HELP)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.tool and args.crossing:
        if not frosty_at_risk(CROSSINGS[args.crossing], TOOLS[args.tool]):
            raise StoryError("That tool does not meaningfully help with this frosty crossing.")
    combos = [c for c in valid_combos()
              if args.crossing is None or c[0] == args.crossing]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    crossing, tool, action = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        crossing=crossing,
        tool=tool,
        action=action,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a 3-to-5-year-old that includes the word "frost" and shows bravery on {f["crossing"].place}.',
        f"Tell a small village story where {f['hero'].id} meets frost, feels fear, and keeps going with {f['helper'].id}'s help.",
        f'Write a gentle tale about {f["hero"].id} learning that bravery means walking through the cold with help, not pretending the frost is gone.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    crossing: Crossing = f["crossing"]
    action: HelpAction = f["action"]
    qas = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, who faces the frost with {helper.id}. The helper stays beside {hero.pronoun('object')} so the path feels less scary.",
        ),
        QAItem(
            question="What made the crossing hard?",
            answer=f"The {crossing.obstacle} and the frost made the way hard. The cold was real, so the child had a reason to feel nervous before being brave.",
        ),
        QAItem(
            question="What changed when the child kept going?",
            answer=f"{hero.id} grew steadier and the fear dropped away. Bravery changed the moment from nervousness into a safe finish on the other side.",
        ),
    ]
    if f.get("outcome") == "success":
        qas.append(QAItem(
            question="How did they get across?",
            answer=f"They used {action.qa_text}. That gave {hero.id} enough warmth and courage to cross without letting the frost win.",
        ))
    else:
        qas.append(QAItem(
            question="What happened if the first try was not enough?",
            answer=f"They had to stop and think again. Even then, the helper stayed close, and that is still a kind of bravery.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is frost?",
            answer="Frost is a thin layer of ice crystals that forms when things get very cold. It can make roads and stones slippery and sharp-looking.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone feels afraid but does the helpful thing anyway. It is not the same as not being scared.",
        ),
        QAItem(
            question="Why do people wear warm clothes in cold weather?",
            answer="Warm clothes help keep heat close to the body. That makes cold places easier and safer to walk through.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(crossing="bridge", tool="boots", action="steady", hero="Mira", hero_gender="girl", helper="Finn", helper_gender="boy", parent="mother", trait="bold"),
    StoryParams(crossing="hill", tool="cloak", action="cloak", hero="Oren", hero_gender="boy", helper="Lena", helper_gender="girl", parent="father", trait="careful"),
    StoryParams(crossing="well", tool="boots", action="steady", hero="Tess", hero_gender="girl", helper="Drew", helper_gender="boy", parent="mother", trait="lively"),
]


def explain_rejection(crossing: Crossing, tool: Tool) -> str:
    return f"(No story: {tool.label} does not fit this frosty crossing in a meaningful way.)"


def outcome_of(params: StoryParams) -> str:
    return "success" if HELP[params.action].power >= 1 else "fail"


ASP_RULES = r"""
frosty(C,P) :- crossing(C), tool(P), crossing_tag(C,frost), tool_tag(P,warm).
valid(C,P,A) :- frosty(C,P), action(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid, c in CROSSINGS.items():
        lines.append(asp.fact("crossing", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("crossing_tag", cid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tg in sorted(t.tags):
            lines.append(asp.fact("tool_tag", tid, tg))
    for aid in HELP:
        lines.append(asp.fact("action", aid))
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
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
        print("OK: normal generation/emit smoke test passed.")
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.crossing not in CROSSINGS or params.tool not in TOOLS or params.action not in HELP:
        raise StoryError("Invalid story parameters.")
    world = tell(
        CROSSINGS[params.crossing],
        TOOLS[params.tool],
        HELP[params.action],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
        params.parent,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
