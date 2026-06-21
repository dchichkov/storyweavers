#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/condiment_trolley_transformation_superhero_story.py
===================================================================================

A standalone story world for a superhero-style transformation tale built from the
seed words "condiment" and "trolley".

Premise:
A child helper sees a city trolley stuck at a curbside snack stop. A sneaky mess
of spilled condiment threatens the trolley route. The hero transforms from an
ordinary kid into a small superhero, cleans the scene with a smart gadget, and
helps the trolley roll again.

The world is deliberately tiny and classical:
- typed entities with meters and memes
- forward-chained causal rules
- grounded Q&A from world state
- an ASP twin with parity checks
- a reasonableness gate for valid story combinations
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
TRANSFORM_NEED = 1.0
BLOCKER_NEED = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
class StoryParams:
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trolley: str
    condiment: str
    power: str
    gadget: str
    setting: str
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


@dataclass
class Setting:
    id: str
    place: str
    vibe: str
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
class Condiment:
    id: str
    label: str
    spill: str
    slippery: bool = True
    sticky: bool = False
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
class Trolley:
    id: str
    label: str
    phrase: str
    route: str
    wheels: int
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
class Power:
    id: str
    name: str
    transform_line: str
    repair_line: str
    cleanup_power: int
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
class Gadget:
    id: str
    label: str
    line: str
    power_bonus: int
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def hazard_at_risk(condiment: Condiment, trolley: Trolley) -> bool:
    return condiment.slippery and trolley.wheels >= 4


def transformation_allowed(power: Power, condiment: Condiment) -> bool:
    return power.cleanup_power >= 2 and condiment.slippery


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for cid, condiment in CONDIMENTS.items():
            for tid, trolley in TROLLEYS.items():
                for pid, power in POWERS.items():
                    if hazard_at_risk(condiment, trolley) and transformation_allowed(power, condiment):
                        out.append((sid, cid, tid))
    return out


def _r_slip(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.meters["transforming"] < THRESHOLD:
        return out
    if world.get("condiment").meters["spilled"] < THRESHOLD:
        return out
    sig = ("slip",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("trolley").meters["stuck"] += 1
    hero.memes["alarm"] += 1
    out.append("__slip__")
    return out


def _r_burst(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.meters["transformed"] < THRESHOLD:
        return out
    sig = ("burst",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["brave"] += 1
    out.append("__burst__")
    return out


CAUSAL_RULES: list[Callable[[World], list[str]]] = [_r_slip, _r_burst]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_spill(world: World, condiment: Entity, narrate: bool = True) -> None:
    condiment.meters["spilled"] += 1
    condiment.meters["mess"] += 1
    propagate(world, narrate=narrate)


def _transform(world: World, hero: Entity, power: Power, gadget: Gadget) -> None:
    hero.meters["transforming"] += 1
    hero.meters["transformed"] += 1
    hero.memes["hope"] += 1
    hero.memes["confidence"] += 1
    world.say(
        f'{hero.id} lifted {gadget.label} and shouted, "{power.transform_line}" '
        f'At once {hero.pronoun()} became {hero.label_word}!'
    )


def _alarm(world: World, hero: Entity, helper: Entity, trolley: Entity, condiment: Entity) -> None:
    world.say(
        f'"{hero.id}! {trolley.label.capitalize()}!" {helper.id} called, pointing at '
        f'the slippery {condiment.label}.'
    )


def _cleanup(world: World, hero: Entity, power: Power, gadget: Gadget, condiment: Entity, trolley: Entity) -> None:
    trolley.meters["stuck"] = 0.0
    condiment.meters["spilled"] = 0.0
    hero.memes["relief"] += 1
    world.say(
        f'With {gadget.label}, {hero.id} used {power.repair_line} and swept the '
        f'{condiment.label} away. The trolley wheels turned free again.'
    )


def _end(world: World, hero: Entity, helper: Entity, trolley: Entity) -> None:
    helper.memes["joy"] += 1
    hero.memes["joy"] += 1
    world.say(
        f'This time the {trolley.label} rolled down {world.setting.place} in a bright '
        f'blue streak, and {hero.id} and {helper.id} grinned like a tiny superhero team.'
    )


def tell(setting: Setting, condiment: Condiment, trolley: Trolley, power: Power, gadget: Gadget,
         hero_name: str, hero_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    cond = world.add(Entity(id="condiment", type="thing", label=condiment.label))
    tro = world.add(Entity(id="trolley", type="thing", label=trolley.label))
    world.add(Entity(id="gadget", type="thing", label=gadget.label))
    world.add(Entity(id="power", type="thing", label=power.name))
    hero.memes["curious"] += 1
    helper.memes["careful"] += 1

    world.say(
        f"On a bright city corner, {hero.id} and {helper.id} watched the {trolley.label} stop at "
        f"{setting.place}. The air smelled like {setting.vibe}, but a spoonful of {condiment.label} "
        f"had splashed across the path."
    )
    world.say(
        f'{helper.id} frowned. "That {condiment.label} could make the {trolley.label} skid." '
        f'{hero.id} stared at the mess, and {hero.pronoun()} reached for {gadget.label}.'
    )

    world.para()
    _transform(world, hero, power, gadget)
    _do_spill(world, cond)
    _alarm(world, hero, helper, tro, cond)

    world.para()
    _cleanup(world, hero, power, gadget, cond, tro)
    _end(world, hero, helper, tro)

    world.facts.update(
        hero=hero, helper=helper, condiment=condiment, trolley=trolley,
        power=power, gadget=gadget, setting=setting,
        transformed=True, cleaned=True
    )
    return world


SETTINGS = {
    "station": Setting(id="station", place="the city station", vibe="hot cocoa and rain"),
    "square": Setting(id="square", place="the sunny square", vibe="pretzels and bicycle bells"),
}

CONDIMENTS = {
    "ketchup": Condiment(id="ketchup", label="ketchup", spill="red streak"),
    "mustard": Condiment(id="mustard", label="mustard", spill="yellow smear"),
    "relish": Condiment(id="relish", label="relish", spill="green splash", sticky=True),
}

TROLLEYS = {
    "streetcar": Trolley(id="streetcar", label="street trolley", phrase="a street trolley", route="downtown loop", wheels=6),
    "tram": Trolley(id="tram", label="tram trolley", phrase="a tram trolley", route="harbor line", wheels=8),
}

POWERS = {
    "transform": Power(id="transform", name="Transformation", transform_line="Sky spark, super change!", repair_line="super sweep", cleanup_power=3),
}

GADGETS = {
    "cape_brush": Gadget(id="cape_brush", label="cape-brush", line="whirl and sweep", power_bonus=1),
    "star_gloves": Gadget(id="star_gloves", label="star gloves", line="shine and clear", power_bonus=1),
}

HERO_NAMES = ["Nova", "Piper", "Milo", "Aria", "Zane", "Ruby"]
HELPER_NAMES = ["Bea", "Otto", "Jules", "Nia", "Tess", "Kai"]


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the words "{f["condiment"].label}" and "{f["trolley"].label}".',
        f"Tell a bright story where {f['hero'].id} uses Transformation to help a trolley after a condiment spill.",
        f"Write a child-friendly rescue story with a quick change, a messy condiment, and a trolley that can move again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    condiment, trolley, power = f["condiment"], f["trolley"], f["power"]
    return [
        QAItem(
            question="What problem did the hero notice?",
            answer=f"{hero.id} noticed that {condiment.label} had spilled on the path and could make the {trolley.label} skid. The trolley needed the mess cleaned before it could roll safely."
        ),
        QAItem(
            question="What did the hero become?",
            answer=f"{hero.id} became a superhero through {power.name}. The transformation gave {hero.pronoun()} the confidence and power to clean up the spill."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The {trolley.label} rolled again, and {hero.id} and {helper.id} smiled beside the clean curb. The spill was gone, so the route could continue."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a condiment?",
            answer="A condiment is a tasty sauce or topping, like ketchup or mustard. People add it to food in small amounts."
        ),
        QAItem(
            question="What is a trolley?",
            answer="A trolley is a vehicle that rides on rails or a route through the city. It carries people along its path."
        ),
        QAItem(
            question="What does transformation mean in a superhero story?",
            answer="Transformation means changing into a different form or a more powerful version of yourself. In superhero stories, it often helps the hero solve a problem."
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
    lines.append("== (3) World knowledge ==")
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


def explain_rejection(condiment: Condiment, trolley: Trolley) -> str:
    if not hazard_at_risk(condiment, trolley):
        return f"(No story: {condiment.label} would not make the {trolley.label} unsafe enough for a superhero rescue.)"
    return "(No story: this combination cannot produce a clear transformation-and-rescue beat.)"


def explain_power(power: Power) -> str:
    return f"(No story: the power '{power.id}' is not strong enough for the transformation rescue.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CONDIMENTS.items():
        lines.append(asp.fact("condiment", cid))
        if c.slippery:
            lines.append(asp.fact("slippery", cid))
    for tid, t in TROLLEYS.items():
        lines.append(asp.fact("trolley", tid))
        lines.append(asp.fact("wheels", tid, t.wheels))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        lines.append(asp.fact("cleanup_power", pid, p.cleanup_power))
    for gid in GADGETS:
        lines.append(asp.fact("gadget", gid))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(C,T) :- slippery(C), trolley(T), wheels(T,W), W >= 4.
valid(S,C,T) :- setting(S), condiment(C), trolley(T), hazard(C,T).
transforms(P) :- power(P), cleanup_power(P,N), N >= 2.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_transforms() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show transforms/1."))
    return sorted(set(asp.atoms(model, "transforms")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos parity.")
    if {p for (p,) in asp_transforms()} == set(POWERS):
        print("OK: ASP power parity matches.")
    else:
        rc = 1
        print("MISMATCH in ASP power parity.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero transformation story world with condiment and trolley.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--condiment", choices=CONDIMENTS)
    ap.add_argument("--trolley", choices=TROLLEYS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.power and args.power not in POWERS:
        raise StoryError("Unknown power.")
    combos = valid_combos()
    if args.setting or args.condiment or args.trolley:
        combos = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.condiment is None or c[1] == args.condiment)
            and (args.trolley is None or c[2] == args.trolley)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, condiment, trolley = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        trolley=trolley,
        condiment=condiment,
        power=args.power or "transform",
        gadget=args.gadget or rng.choice(list(GADGETS)),
        setting=setting,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.condiment not in CONDIMENTS or params.trolley not in TROLLEYS or params.power not in POWERS or params.gadget not in GADGETS:
        raise StoryError("Invalid StoryParams.")
    world = tell(
        SETTINGS[params.setting],
        CONDIMENTS[params.condiment],
        TROLLEYS[params.trolley],
        POWERS[params.power],
        GADGETS[params.gadget],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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


CURATED = [
    StoryParams(hero="Nova", hero_gender="girl", helper="Bea", helper_gender="girl", trolley="streetcar", condiment="ketchup", power="transform", gadget="cape_brush", setting="station"),
    StoryParams(hero="Milo", hero_gender="boy", helper="Kai", helper_gender="boy", trolley="tram", condiment="mustard", power="transform", gadget="star_gloves", setting="square"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show transforms/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"transforms: {', '.join(pid for (pid,) in asp_transforms())}")
        print(f"{len(asp_valid_combos())} valid combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
