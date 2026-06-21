#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/laminate_recuperate_fluid_humor_comedy.py
========================================================================

A tiny comedy storyworld about a slippery laminate floor, a spilled fluid,
and a gentle recuperation with humor.

The premise is simple: someone spills a mysterious fluid on a shiny laminate
surface, a small mishap turns funny but not harmful, and the characters recover
their composure with an improvised fix that becomes the joke of the day.

The script follows the shared Storyweavers contract:
- typed entities with meters and memes
- a Python reasonableness gate
- inline ASP twin rules
- three Q&A sets grounded in simulated state
- CLI support for default, curated, JSON, QA, trace, ASP, and verify modes
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    surface: str
    mood: str
    affords: set[str] = field(default_factory=set)
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
class Spill:
    id: str
    label: str
    fluid_word: str
    phrase: str
    joke: str
    mess: str
    spread: int = 1
    liquid: bool = True
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
class RecoveryTool:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    text: str
    fail: str
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
    setting: str
    spill: str
    tool: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
    tone: str = "comedy"
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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["slippery"] < THRESHOLD:
            continue
        sig = ("slip", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["chaos"] += 1
        for ch in world.characters():
            ch.memes["surprise"] += 1
        out.append("__slip__")
    return out


CAUSAL_RULES = [Rule("slip", _r_slip)]


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


def humor_level(spill: Spill) -> int:
    return 3 if "jelly" in spill.tags or "soup" in spill.tags else 2


def hazard_at_risk(spill: Spill, setting: Setting) -> bool:
    return spill.liquid and "laminate" in setting.surface.lower()


def sensible_tools() -> list[RecoveryTool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def best_tool() -> RecoveryTool:
    return max(TOOLS.values(), key=lambda t: t.sense)


def recoverable(tool: RecoveryTool, spill: Spill) -> bool:
    return tool.power >= spill.spread


def predict_spill(world: World, spill_id: str) -> dict:
    sim = world.copy()
    sim.get(spill_id).meters["slippery"] += 1
    propagate(sim, narrate=False)
    return {
        "chaos": sim.get("floor").meters.get("chaos", 0.0),
        "slippery": sim.get(spill_id).meters.get("slippery", 0.0),
    }


def play_setup(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {helper.id} turned {setting.place} "
        f"into a little comedy stage. The room had {setting.mood}, and the "
        f"{setting.surface} shimmered like it was waiting for a joke."
    )
    world.say(
        f"{hero.id} was sure this would be a perfect day for an experiment with "
        f"funny sound effects."
    )


def spill_event(world: World, hero: Entity, spill: Spill, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    world.get("spill").meters["slippery"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} tipped over a cup of {spill.fluid_word}. "
        f"{spill.phrase.capitalize()} landed on the {setting.surface}, and it "
        f"spread into a shiny puddle."
    )
    world.say(f"It was not huge, but it was dramatic enough to make everyone gasp, then snicker.")


def warn(world: World, helper: Entity, hero: Entity, spill: Spill, setting: Setting) -> None:
    pred = predict_spill(world, "spill")
    helper.memes["caution"] += 1
    world.facts["predicted_chaos"] = pred["chaos"]
    world.say(
        f'{helper.id} pointed at the shine and said, "{hero.id}, that {spill.label} '
        f"is going to turn this laminate into a skating rink.""
    )


def joke(world: World, helper: Entity, spill: Spill) -> None:
    helper.memes["humor"] += 1
    world.say(
        f'{helper.id} blinked, then grinned. "At least the floor finally has a '
        f"good sense of humor," {helper.pronoun()} said, and {spill.joke}."
    )


def act_choose(world: World, tool: RecoveryTool) -> None:
    world.say(f"After the laugh, the grown-up found {tool.phrase}.")
    world.say(
        f'"{tool.text}," {world.get("adult").label_word} said, sounding calm and '
        f"delighted that the mess was still small enough to handle."
    )


def recover(world: World, adult: Entity, tool: RecoveryTool, spill: Spill, setting: Setting) -> bool:
    if not recoverable(tool, spill):
        return False
    world.get("spill").meters["slippery"] = 0.0
    world.get("floor").meters["chaos"] = 0.0
    adult.memes["relief"] += 1
    world.say(
        f"{adult.label_word.capitalize()} used {tool.label} and {tool.text}. "
        f"The {setting.surface} stopped gleaming, and the slippery spot was gone."
    )
    return True


def celebrate(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"By the end, {hero.id} and {helper.id} were laughing again. The "
        f"{setting.surface} looked calm, and the room felt clean and ready for "
        f"more careful play."
    )
    world.say(
        f"{hero.id} promised to watch the cups, and the whole day became a joke "
        f"about how a tiny fluid could try to steal the spotlight."
    )


def fail_recover(world: World, adult: Entity, tool: RecoveryTool, spill: Spill) -> None:
    world.say(
        f"{adult.label_word.capitalize()} tried {tool.fail}, but the spill stayed "
        f"slippery and the joke stopped being funny."
    )
    world.say("That version of the day ended with towels, a sigh, and a very serious mop.")


def tell(setting: Setting, spill: Spill, tool: RecoveryTool,
         hero_name: str = "Mina", hero_gender: str = "girl",
         helper_name: str = "Jae", helper_gender: str = "boy",
         adult_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, label="the adult"))
    floor = world.add(Entity(id="floor", type="floor", label=setting.surface))
    spill_ent = world.add(Entity(id="spill", type="spill", label=spill.label))
    world.facts["setting"] = setting
    world.facts["spill_cfg"] = spill
    world.facts["tool_cfg"] = tool

    play_setup(world, hero, helper, setting)
    world.para()
    spill_event(world, hero, spill, setting)
    warn(world, helper, hero, spill, setting)
    joke(world, helper, spill)
    world.para()
    act_choose(world, tool)
    ok = recover(world, adult, tool, spill, setting)
    if ok:
        celebrate(world, hero, helper, setting)
        outcome = "recovered"
    else:
        fail_recover(world, adult, tool, spill)
        outcome = "failed"
    world.facts.update(hero=hero, helper=helper, adult=adult, floor=floor, spill=spill_ent, outcome=outcome)
    return world


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", surface="laminate floor", mood="a cheerful hush", affords={"juice", "water", "soda"}),
    "hall": Setting(id="hall", place="the hallway", surface="laminate hallway floor", mood="a bouncy echo", affords={"juice", "water"}),
    "classroom": Setting(id="classroom", place="the classroom", surface="laminate reading corner", mood="a sleepy whisper", affords={"water", "juice"}),
}

SPILLS = {
    "juice": Spill(id="juice", label="juice", fluid_word="apple juice", phrase="The fluid splashed", joke="it made the floor look like it was wearing shiny socks", mess="sticky", spread=1, tags={"juice", "fluid", "comedy"}),
    "water": Spill(id="water", label="water", fluid_word="water", phrase="The fluid spread", joke="it turned the floor into a pretend ice rink for one second", mess="wet", spread=1, tags={"water", "fluid"}),
    "soda": Spill(id="soda", label="soda", fluid_word="soda", phrase="The fluid fizzed", joke="it gave the floor a bubbly moustache", mess="sticky", spread=1, tags={"soda", "fluid", "humor"}),
}

TOOLS = {
    "mop": RecoveryTool(id="mop", label="a mop", phrase="a mop with a brave red handle", power=2, sense=3, text="mopped up the fluid until the laminate was safe again", fail="mopped once and then looked very confused", tags={"mop"}),
    "towels": RecoveryTool(id="towels", label="paper towels", phrase="a stack of paper towels", power=1, sense=2, text="pressed paper towels over the puddle until the floor was dry", fail="used too few paper towels and only spread the shine around", tags={"towels"}),
    "cloth": RecoveryTool(id="cloth", label="a kitchen cloth", phrase="a clean kitchen cloth", power=1, sense=2, text="wiped the spill away with a clean cloth", fail="wiped in circles and made the joke worse", tags={"cloth"}),
    "fan": RecoveryTool(id="fan", label="a small fan", phrase="a tiny fan", power=0, sense=1, text="blew air at the puddle and made everyone laugh for the wrong reason", fail="blew air at the puddle and made it sparkle in a more slippery way", tags={"fan"}),
}

HERO_NAMES = ["Mina", "Ari", "Luca", "Nia", "Eli", "Tess", "Noa", "Pip"]
HELPER_NAMES = ["Jae", "Bea", "Otto", "Zuri", "Kai", "Milo", "Rae", "June"]

KNOWLEDGE = {
    "laminate": [("What is laminate?",
                  "Laminate is a smooth covering often used on floors and tables. It looks shiny and is easy to wipe clean.")],
    "fluid": [("What is a fluid?",
               "A fluid is something that can flow and pour, like water, juice, or soup. Fluids do not stay in one shape.")],
    "comedy": [("What makes a comedy story funny?",
                "A comedy story makes people laugh with silly trouble, clever jokes, and a happy ending.")],
    "mop": [("What does a mop do?",
             "A mop soaks up spills and helps clean floors. It is useful when something fluid gets on the ground.")],
    "towels": [("What are paper towels for?",
                "Paper towels are for soaking up spills and wiping wet things clean.")],
    "sticky": [("Why is sticky stuff hard to clean?",
                 "Sticky stuff clings to surfaces, so you may need to wipe more than once to get it off.")],
    "wet": [("Why is a wet floor risky?",
              "A wet floor can be slippery, so people can slide if they are not careful.")],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for spill_id in setting.affords:
            spill = SPILLS[spill_id]
            for tool_id, tool in TOOLS.items():
                if hazard_at_risk(spill, setting) and recoverable(tool, spill) and tool.sense >= SENSE_MIN:
                    combos.append((sid, spill_id, tool_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child that includes the words "{f["spill_cfg"].fluid_word}", "laminate", and "recuperate".',
        f"Tell a comedy story where {f['hero'].id} spills {f['spill_cfg'].label} on a laminate floor and the family recovers calmly with a clever clean-up.",
        "Write a short humorous story about a slippery floor, a small mess, and everyone recuperating with a laugh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, adult, spill = f["hero"], f["helper"], f["adult"], f["spill_cfg"]
    setting = f["setting"]
    tool = f["tool_cfg"]
    qa = [
        QAItem(
            question="What happened to the floor?",
            answer=f"{hero.id} spilled {spill.fluid_word} on the {setting.surface}, so it got shiny and slippery. That made the room feel funny for a moment."
        ),
        QAItem(
            question="Who helped fix the problem?",
            answer=f"{helper.id} noticed the mess, and {adult.label_word} brought {tool.label}. Together they turned the spill into a quick cleanup instead of a bigger problem."
        ),
        QAItem(
            question="How did the characters recuperate?",
            answer=f"They calmed down, cleaned the floor, and started laughing again. The whole group recuperated their good mood once the laminate was dry."
        ),
    ]
    if f["outcome"] == "recovered":
        qa.append(QAItem(
            question="Why did the joke stay funny?",
            answer="The spill was small, so everyone could laugh and still clean it easily. The humor stayed light because the mess never grew too large."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["spill_cfg"].tags) | {world.facts["tool_cfg"].id, "laminate"}
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            for q, a in items:
                out.append(QAItem(question=q, answer=a))
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
slippery(spill) :- spill_cfg(spill), liquid(spill).
chaos(floor) :- slippery(spill).
recoverable(tool) :- tool(tool), sense(tool, S), sense_min(M), S >= M.
valid(setting, spill, tool) :- setting(setting), setting_affords(setting, spill), liquid(spill), recoverable(tool).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spill_id in s.affords:
            lines.append(asp.fact("setting_affords", sid, spill_id))
    for spill_id, spill in SPILLS.items():
        lines.append(asp.fact("spill_cfg", spill_id))
        if spill.liquid:
            lines.append(asp.fact("liquid", spill_id))
        lines.append(asp.fact("spread", spill_id, spill.spread))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        lines.append(asp.fact("power", tid, tool.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test succeeded.")
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world: laminate, fluid, recuperate.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spill", choices=SPILLS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
              and (args.spill is None or c[1] == args.spill)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, spill, tool = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, spill=spill, tool=tool, hero=hero, hero_gender=hero_gender,
                       helper=helper, helper_gender=helper_gender, adult=adult)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.spill not in SPILLS or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    if not hazard_at_risk(SPILLS[params.spill], SETTINGS[params.setting]):
        raise StoryError("This spill does not suit the laminate floor setup.")
    if not recoverable(TOOLS[params.tool], SPILLS[params.spill]):
        raise StoryError("This tool cannot reasonably recover the spill.")
    world = tell(
        SETTINGS[params.setting],
        SPILLS[params.spill],
        TOOLS[params.tool],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="kitchen", spill="juice", tool="mop", hero="Mina", hero_gender="girl", helper="Jae", helper_gender="boy", adult="mother"),
    StoryParams(setting="hall", spill="water", tool="cloth", hero="Ari", hero_gender="boy", helper="Rae", helper_gender="girl", adult="father"),
    StoryParams(setting="classroom", spill="soda", tool="towels", hero="Tess", hero_gender="girl", helper="Kai", helper_gender="boy", adult="mother"),
]


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, spill, tool) combos:\n")
        for row in combos:
            print(f"  {row[0]:10} {row[1]:8} {row[2]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
