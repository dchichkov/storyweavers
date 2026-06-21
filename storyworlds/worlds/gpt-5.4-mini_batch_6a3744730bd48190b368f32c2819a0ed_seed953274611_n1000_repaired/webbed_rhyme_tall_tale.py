#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/webbed_rhyme_tall_tale.py
==========================================================

A standalone story world for a tall-tale yarn about a little marsh town,
a webbed-footed helper, a stubborn snag, and a rhyming rescue.

The domain is small on purpose:
- a traveler crosses a marsh
- a webbed companion predicts trouble in the mud
- a too-bold shortcut causes a snag
- a tall-tale fix gets everyone home in rhyme
- the ending image proves what changed

This script follows the shared storyworld contract:
- stdlib only
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py inside ASP helpers
- build_parser / resolve_params / generate / emit / main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- three Q&A sets grounded in world state
- inline ASP twin plus Python reasonableness gate
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
    webbed: bool = False
    can_rhyme: bool = False
    helper: bool = False

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Locale:
    id: str
    name: str
    weather: str
    has_mud: bool
    has_moon_path: bool
    rhyme_word: str
    imagery: str
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
class Path:
    id: str
    label: str
    risky: bool
    snags: bool
    deep_mud: bool
    rhyme_end: str
    meter: int
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
    sense: int
    power: int
    rhyme_line: str
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
class StoryParams:
    locale: str
    path: str
    tool: str
    traveler_name: str
    traveler_gender: str
    helper_name: str
    helper_gender: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_mud(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["sunk"] < THRESHOLD:
            continue
        sig = ("mud", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["alarm"] += 1
        world.get("traveler").memes["worry"] += 1
        world.get("helper").memes["warning"] += 1
        out.append("__mud__")
    return out


def _r_loss(world: World) -> list[str]:
    if world.get("pack").meters["lost"] >= THRESHOLD and (("loss",) not in world.fired):
        world.fired.add(("loss",))
        world.get("traveler").memes["sad"] += 1
        return ["__loss__"]
    return []


CAUSAL_RULES = [Rule("mud", _r_mud), Rule("loss", _r_loss)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_gate(locale: Locale, path: Path, tool: Tool) -> bool:
    return locale.has_mud and path.risky and tool.power >= path.meter


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: t.sense)


def predict_sink(world: World, path_id: str) -> dict:
    sim = world.copy()
    _take_shortcut(sim, sim.get(path_id), narrate=False)
    return {
        "sunk": sim.get("boots").meters["sunk"] >= THRESHOLD,
        "lost": sim.get("pack").meters["lost"] >= THRESHOLD,
    }


def _take_shortcut(world: World, path_ent: Entity, narrate: bool = True) -> None:
    path_ent.meters["traveled"] += 1
    if path_ent.attrs.get("snags"):
        world.get("boots").meters["sunk"] += 1
        world.get("pack").meters["lost"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, traveler: Entity, helper: Entity, locale: Locale, path: Path) -> None:
    traveler.memes["spark"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Once in {locale.name}, where the reeds leaned low and the moonpath gleamed, "
        f"{traveler.id} and {helper.id} set out in a tall-tale frame."
    )
    world.say(
        f"{locale.imagery} {traveler.id} had {traveler.pronoun('possessive')} boots, "
        f"and {helper.id} had a chin as keen as a bean."
    )
    world.say(
        f'They meant to cross {path.label}, where a rhyme could climb and a rumor could chime.'
    )


def needs_way(world: World, helper: Entity, locale: Locale) -> None:
    world.say(
        f"But the marsh was a mush and the fog was a hush; even {locale.rhyme_word} felt "
        f"as dull as a stump in a rush."
    )
    world.say(f'"We need a way," said {helper.id}, "or night will win the day."')


def tempt(world: World, traveler: Entity, path: Path) -> None:
    traveler.memes["bold"] += 1
    world.say(
        f'"I know a short cut," {traveler.id} cried, "right past the snag and the slosh on the side."'
    )
    world.say("A tale got tall and the moon got small, and the shortcut sounded best of all.")


def warn(world: World, helper: Entity, traveler: Entity, tool: Tool, path: Path) -> None:
    pred = predict_sink(world, "path")
    helper.memes["warning"] += 1
    world.facts["predicted"] = pred
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. "{tool.label.capitalize()} is the smart way, '
        f"for webbed feet know where the water will stay."
        f" If we rush that cut, we'll end in a rut."'
    )
    if pred["sunk"]:
        world.say("That shortcut looked slick, but the mud would stick quick.")


def take_shortcut(world: World, traveler: Entity, path: Path) -> None:
    world.say(f"So {traveler.id} took the shortcut anyway, quick as a wink and bold as hay.")
    _take_shortcut(world, world.get("path"))
    if path.snags:
        world.say(
            f"The ground went spidery and mean, and the webbed boots went in up to the seam."
        )


def alarm(world: World, helper: Entity, traveler: Entity, path: Path) -> None:
    world.say(f'"{traveler.id}!" {helper.id} shouted, "The mud's got you bound!"')


def rescue(world: World, helper: Entity, tool: Tool, traveler: Entity, path: Path, locale: Locale) -> None:
    traveler.meters["stuck"] = 0.0
    world.get("boots").meters["sunk"] = 0.0
    world.get("pack").meters["lost"] = 0.0
    world.say(
        f"{helper.id} came loping and singing, and {tool.rhyme_line}."
    )
    world.say(
        f"In one grand sweep, {helper.id} used {tool.phrase} and pulled {traveler.id} free from the deep."
    )
    world.say(
        f"The mud gave way with a squelch and a sway, and the moonpath opened as clear as day."
    )


def lesson(world: World, traveler: Entity, helper: Entity, tool: Tool) -> None:
    traveler.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"For a blink they sat still, then laughed at the thrill. "
        f'"A rhyme and a reason can beat muddy treason," said {helper.id}.'
    )
    world.say(
        f'"And webbed feet are neat when the marsh is complete," answered {traveler.id}, "but not every road is a treat."'
    )
    world.say(
        f"So they promised to call for the gleam of {tool.label}, not tumble and blunder and split every seam."
    )


def ending(world: World, traveler: Entity, helper: Entity, tool: Tool, locale: Locale) -> None:
    traveler.memes["joy"] += 1
    world.say(
        f"By dawn they were home, with no more to roam; {traveler.id} still had {traveler.pronoun('possessive')} boots, "
        f"and {helper.id} still had the tune of the road."
    )
    world.say(
        f"The marsh kept its mud, but the pair kept their cud -- their clever old habit of picking the good."
    )
    world.say(
        f"And that is the way in {locale.name}: when the going grows grim, a rhyme and a tool can carry you through."
    )


def tell(locale: Locale, path: Path, tool: Tool,
         traveler_name: str = "Milo", traveler_gender: str = "boy",
         helper_name: str = "Mara", helper_gender: str = "girl") -> World:
    world = World()
    traveler = world.add(Entity(id=traveler_name, kind="character", type=traveler_gender, role="traveler",
                                webbed=True, can_rhyme=False, attrs={"locale": locale.id}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper",
                              webbed=False, can_rhyme=True, helper=True, attrs={"locale": locale.id}))
    world.add(Entity(id="path", type="path", label=path.label, attrs={"snags": path.snags}))
    world.add(Entity(id="boots", type="gear", label="boots"))
    world.add(Entity(id="pack", type="thing", label="pack"))

    opening(world, traveler, helper, locale, path)
    needs_way(world, helper, locale)
    world.para()
    tempt(world, traveler, path)
    warn(world, helper, traveler, tool, path)

    if not reasonableness_gate(locale, path, tool):
        world.say("No story: the tools and trail don't make a fair old fable.")
    else:
        if path.snags:
            take_shortcut(world, traveler, path)
            world.para()
            alarm(world, helper, traveler, path)
            rescue(world, helper, tool, traveler, path, locale)
            lesson(world, traveler, helper, tool)
            world.para()
            ending(world, traveler, helper, tool, locale)
        else:
            world.say("The road was too smooth for a true trouble tale.")
    world.facts.update(
        traveler=traveler, helper=helper, locale=locale, path=path, tool=tool,
        stuck=world.get("boots").meters["sunk"] >= THRESHOLD,
        lost=world.get("pack").meters["lost"] >= THRESHOLD,
    )
    return world


LOCALES = {
    "marsh": Locale(
        id="marsh",
        name="Mossy Marsh",
        weather="misty",
        has_mud=True,
        has_moon_path=True,
        rhyme_word="moon",
        imagery="There were cattails like candles and frogs like fiddlers.",
    ),
    "bayou": Locale(
        id="bayou",
        name="Blue Bayou",
        weather="warm",
        has_mud=True,
        has_moon_path=True,
        rhyme_word="bay",
        imagery="There were cypress knees like dozing giants and lilies like plates.",
    ),
    "fen": Locale(
        id="fen",
        name="Fiddler Fen",
        weather="foggy",
        has_mud=True,
        has_moon_path=True,
        rhyme_word="glen",
        imagery="There were willows like whiskers and dragonflies like sparks.",
    ),
}

PATHS = {
    "snag": Path(id="snag", label="the snaggy shortcut", risky=True, snags=True, deep_mud=True, rhyme_end="in a rut", meter=1),
    "slog": Path(id="slog", label="the long slog", risky=True, snags=False, deep_mud=False, rhyme_end="on time", meter=1),
    "pool": Path(id="pool", label="the moonlit pool edge", risky=True, snags=True, deep_mud=True, rhyme_end="in a squelch", meter=1),
}

TOOLS = {
    "pole": Tool(id="pole", label="pole", phrase="a long marsh pole", sense=3, power=2, rhyme_line="he jabbed the mud with a steady old pole"),
    "plank": Tool(id="plank", label="plank", phrase="a wide plank", sense=2, power=1, rhyme_line="she bridged the slough with a strong little plank"),
    "lantern": Tool(id="lantern", label="lantern", phrase="a bright lantern", sense=3, power=2, rhyme_line="the lantern shone on the frog-brown stone"),
    "rope": Tool(id="rope", label="rope", phrase="a braided rope", sense=4, power=3, rhyme_line="the rope gave a tug and the muck gave a shrug"),
}

TRAITS = ["brave", "curious", "bright", "nimble", "cheery"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for lid, locale in LOCALES.items():
        for pid, path in PATHS.items():
            for tid, tool in TOOLS.items():
                if reasonableness_gate(locale, path, tool):
                    combos.append((lid, pid, tid))
    return combos


def explain_rejection(locale: Locale, path: Path, tool: Tool) -> str:
    if not locale.has_mud:
        return "(No story: this tall tale needs mud enough to snag a boot.)"
    if not path.risky:
        return "(No story: a flat path won't give us a proper marshy mishap.)"
    if tool.power < path.meter:
        return f"(No story: {tool.label} is too small a fix for {path.label}.)"
    return "(No story: this combination doesn't make a real marsh ruckus.)"


def explain_tool(rid: str) -> str:
    t = TOOLS[rid]
    better = " / ".join(x.id for x in sensible_tools())
    return f"(Refusing tool '{rid}': sense={t.sense} < {SENSE_MIN}. Try: {better}.)"


def outcome_of(params: StoryParams) -> str:
    return "rescued" if reasonableness_gate(LOCALES[params.locale], PATHS[params.path], TOOLS[params.tool]) else "no_story"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story that includes the word "webbed" and a marsh crossing in rhyme.',
        f"Tell a rhyming adventure where {f['traveler'].id} with webbed feet gets stuck in mud and {f['helper'].id} rescues {f['traveler'].pronoun('object')} with a smart tool.",
        f"Write a child-friendly marsh tale with a bold traveler, a clever helper, and a rescue that ends in rhyme.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    t, h, loc, path, tool = f["traveler"], f["helper"], f["locale"], f["path"], f["tool"]
    qa = [
        ("Who is the story about?",
         f"It is about {t.id} and {h.id}, a marshy pair in {loc.name}. {t.id} has webbed feet, and {h.id} is the clever helper who keeps the tale moving."),
        ("What went wrong on the shortcut?",
         f"{t.id} took the snaggy shortcut and got stuck in the mud. The path was rough, so the boots sank and the pack was lost."),
        ("How did they get out?",
         f"{h.id} used {tool.phrase} and pulled {t.id} free. That worked because the tool had enough power for the muddy snag."),
        ("How did the story end?",
         f"They made it home safe, and {t.id} learned to trust {h.id}'s good advice. The marsh stayed muddy, but their feet were clean enough to keep wandering another day."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"webbed", "mud", f["tool"].id}
    out = []
    if "webbed" in tags:
        out.append(("What does webbed mean?",
                    "Webbed feet have skin between the toes, like a duck's foot. That shape helps in water and mud, where wide feet can push and paddle more easily."))
    if "mud" in tags:
        out.append(("What is mud?",
                    "Mud is wet dirt. It is slippery, sticky, and likes to hold onto boots and paws."))
    if f["tool"].id == "rope":
        out.append(("What is a rope for?",
                    "A rope is for tying, tugging, and pulling. A strong rope can help move something that is stuck."))
    elif f["tool"].id == "pole":
        out.append(("What is a pole for?",
                    "A pole is a long stick you can poke, push, or lever with. It helps when the ground is too muddy to step on safely."))
    elif f["tool"].id == "plank":
        out.append(("What is a plank for?",
                    "A plank is a flat board you can lay down to make a bridge. It helps you step over wet or soft ground without sinking."))
    elif f["tool"].id == "lantern":
        out.append(("What is a lantern for?",
                    "A lantern gives light in the dark. It helps travelers see where the safe path is at night."))
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.webbed:
            bits.append("webbed=True")
        if e.can_rhyme:
            bits.append("can_rhyme=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
risky_path(P) :- path(P), snags(P).
mud_hazard(L,P) :- locale(L), risky_path(P), has_mud(L).
valid(L,P,T) :- mud_hazard(L,P), tool(T), sense(T,S), sense_min(M), S >= M, power(T,Pw), meter(P,Mt), Pw >= Mt.
rescued(L,P,T) :- valid(L,P,T).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for lid, loc in LOCALES.items():
        lines.append(asp.fact("locale", lid))
        if loc.has_mud:
            lines.append(asp.fact("has_mud", lid))
    for pid, p in PATHS.items():
        lines.append(asp.fact("path", pid))
        if p.snags:
            lines.append(asp.fact("snags", pid))
        lines.append(asp.fact("meter", pid, p.meter))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
        lines.append(asp.fact("power", tid, t.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_rescued() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show rescued/3."))
    return sorted(set(asp.atoms(model, "rescued")))


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()) == set(asp_valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    smoke = generate(resolve_params(argparse.Namespace(locale=None, path=None, tool=None, traveler_name=None, traveler_gender=None, helper_name=None, helper_gender=None, seed=None), random.Random(777)))
    if not smoke.story:
        print("MISMATCH: smoke test produced empty story.")
        rc = 1
    else:
        print("OK: smoke story generated.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale marsh storyworld with rhyme and webbed feet.")
    ap.add_argument("--locale", choices=LOCALES)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--traveler-name")
    ap.add_argument("--traveler-gender", choices=["boy", "girl"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = ["Milo", "Tess", "Bram", "Mara", "Jeb", "Luna", "Otis", "Penny"]
    if gender == "boy":
        pool = ["Milo", "Bram", "Jeb", "Otis"]
    else:
        pool = ["Tess", "Mara", "Luna", "Penny"]
    pool = [n for n in pool if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))
    combos = [c for c in valid_combos()
              if (args.locale is None or c[0] == args.locale)
              and (args.path is None or c[1] == args.path)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    locale, path, tool = rng.choice(sorted(combos))
    traveler_gender = args.traveler_gender or rng.choice(["boy", "girl"])
    helper_gender = args.helper_gender or ("girl" if traveler_gender == "boy" else "boy")
    traveler_name = args.traveler_name or _pick_name(rng, traveler_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=traveler_name)
    return StoryParams(
        locale=locale,
        path=path,
        tool=tool,
        traveler_name=traveler_name,
        traveler_gender=traveler_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.locale not in LOCALES or params.path not in PATHS or params.tool not in TOOLS:
        raise StoryError("Invalid params.")
    world = tell(
        LOCALES[params.locale],
        PATHS[params.path],
        TOOLS[params.tool],
        params.traveler_name,
        params.traveler_gender,
        params.helper_name,
        params.helper_gender,
    )
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


CURATED = [
    StoryParams(locale="marsh", path="snag", tool="rope", traveler_name="Milo", traveler_gender="boy", helper_name="Mara", helper_gender="girl"),
    StoryParams(locale="bayou", path="pool", tool="pole", traveler_name="Otis", traveler_gender="boy", helper_name="Tess", helper_gender="girl"),
    StoryParams(locale="fen", path="snag", tool="lantern", traveler_name="Penny", traveler_gender="girl", helper_name="Bram", helper_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show rescued/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
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
