#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/popsicle_suspense_dialogue_repetition_myth.py
==============================================================================

A standalone storyworld for a small mythic tale about a popsicle on a hot day:
a child carries a fragile frozen treat through a tense journey, speaks with a
guide, repeats a warning or a prayer-like refrain, and reaches a satisfying
ending image that proves what changed.

The world is intentionally tiny and classical:
- typed entities with meters and memes
- a short causal model that drives the prose
- a reasonableness gate
- an inline ASP twin and Python parity check
- grounded prompts and QA from simulated state, not from rendered text
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
MELT_RISK_MIN = 1.0
SUSPENSE_MIN = 1.0


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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "priestess"}
        male = {"boy", "father", "dad", "man", "guide"}
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
    place: str
    sun: str
    shade: str
    route: str
    shrine: str
    air: str
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
class Treat:
    id: str
    flavor: str
    phrase: str
    color: str
    coolness: int
    sacred_name: str
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
class Carrier:
    id: str
    title: str
    line: str
    caution: str
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
class Threat:
    id: str
    heat: int
    shadow: str
    omen: str
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
class Rescue:
    id: str
    skill: int
    line: str
    ending: str
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
        c.facts = copy.deepcopy(self.facts)
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


def _r_melt(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["melting"] < THRESHOLD:
            continue
        sig = ("melt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "popsicle" in world.entities:
            world.get("popsicle").meters["drip"] += 1
        if "hero" in world.entities:
            world.get("hero").memes["worry"] += 1
        if "guide" in world.entities:
            world.get("guide").memes["worry"] += 1
        out.append("__heat__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    popsicle = world.entities.get("popsicle")
    if not hero or not popsicle:
        return out
    if hero.memes["panic"] < THRESHOLD or popsicle.meters["drip"] < THRESHOLD:
        return out
    sig = ("drop",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    popsicle.meters["fallen"] += 1
    out.append("__drop__")
    return out


CAUSAL_RULES = [Rule("melt", _r_melt), Rule("drop", _r_drop)]


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


def heat_at_risk(treat: Treat, threat: Threat) -> bool:
    return treat.coolness > 0 and threat.heat >= MELT_RISK_MIN


def best_rescue() -> Rescue:
    return max(RESCUES.values(), key=lambda r: r.skill)


def can_save(treat: Treat, threat: Threat, rescue: Rescue, delay: int) -> bool:
    return rescue.skill >= threat.heat + delay


def reasonables() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TREATS:
            for h in THREATS:
                if heat_at_risk(TREATS[t], THREATS[h]):
                    combos.append((s, t, h))
    return combos


def simulate_heat(world: World, delay: int) -> None:
    world.get("popsicle").meters["melting"] += 1 + delay
    world.get("sun").meters["hot"] += 1
    propagate(world, narrate=False)


def predict(world: World, delay: int) -> dict:
    sim = world.copy()
    simulate_heat(sim, delay)
    return {
        "melting": sim.get("popsicle").meters["melting"] >= THRESHOLD,
        "drip": sim.get("popsicle").meters["drip"],
        "fallen": sim.get("popsicle").meters["fallen"] >= THRESHOLD,
    }


def begin(world: World, hero: Entity, guide: Entity, setting: Setting, treat: Treat) -> None:
    world.say(
        f"In the old {setting.place}, beneath {setting.shade}, {hero.id} carried "
        f"a {treat.flavor} popsicle as if it were a small star."
    )
    world.say(
        f"{guide.id} lifted a hand. \"Do not hurry,\" {guide.pronoun()} said. "
        f"\"Do not hurry. The sun listens, and the sun is hungry.\""
    )


def repetition(world: World, hero: Entity, guide: Entity) -> None:
    hero.memes["hope"] += 1
    guide.memes["guard"] += 1
    world.say(
        f"\"Hold it high,\" {guide.id} said. \"Hold it high.\""
    )
    world.say(
        f"\"I will,\" {hero.id} answered, and the words came back like an echo. "
        f"\"I will.\""
    )


def suspense(world: World, hero: Entity, treat: Treat, threat: Threat) -> None:
    hero.memes["suspense"] += 1
    world.say(
        f"But the road ahead shone with {threat.shadow}, and the {treat.sacred_name} "
        f"began to shine with a thin wet glow."
    )
    world.say(
        f"One drop, then another. One drop, then another. The child looked down, "
        f"and the popsicle grew smaller in the hand."
    )


def warn(world: World, guide: Entity, hero: Entity, treat: Treat, threat: Threat) -> None:
    pred = predict(world, 0)
    guide.memes["caution"] += 1
    world.facts["predicted"] = pred
    world.say(
        f"\"The heat is waking it,\" {guide.id} said. \"If it wakes too much, it will "
        f"slip. If it slips, we chase. If we chase, we lose the blessing.\""
    )
    world.say(
        f"\"Then we do not lose it,\" {hero.id} whispered. \"Then we do not lose it.\""
    )


def save(world: World, guide: Entity, hero: Entity, treat: Treat, rescue: Rescue) -> None:
    hero.memes["panic"] = 0
    hero.memes["joy"] += 1
    world.get("popsicle").meters["melting"] = 0
    world.get("popsicle").meters["drip"] = 0
    world.get("popsicle").meters["steady"] += 1
    world.say(
        f"At the shrine's cool stone bowl, {guide.id} {rescue.line}, and the heat "
        f"broke on the shade like a wave on black rock."
    )
    world.say(
        f"The {treat.sacred_name} stayed whole long enough to matter."
    )


def ending(world: World, hero: Entity, treat: Treat, setting: Setting, rescue: Rescue) -> None:
    world.say(
        f"By nightfall, {hero.id} held the last bright bite over {setting.route}, "
        f"and the popsicle was no longer a threat but a calm red ribbon in the dark."
    )
    world.say(
        f"{rescue.ending}."
    )


def tell(setting: Setting, treat: Treat, threat: Threat, carrier: Carrier, rescue: Rescue,
         hero_name: str = "Mira", guide_name: str = "Orin", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", role="hero"))
    guide = world.add(Entity(id=guide_name, kind="character", type="guide", role="guide"))
    sun = world.add(Entity(id="sun", kind="thing", type="sun", label="the sun"))
    popsicle = world.add(Entity(id="popsicle", kind="thing", type="treat", label="popsicle"))
    world.facts.update(setting=setting, treat=treat, threat=threat, carrier=carrier,
                       rescue=rescue, delay=delay, hero=hero, guide=guide)

    begin(world, hero, guide, setting, treat)
    world.para()
    repetition(world, hero, guide)
    suspense(world, hero, treat, threat)
    warn(world, guide, hero, treat, threat)
    world.para()
    if can_save(treat, threat, rescue, delay):
        save(world, guide, hero, treat, rescue)
        ending(world, hero, treat, setting, rescue)
        outcome = "saved"
    else:
        world.get("popsicle").meters["melting"] += threat.heat + delay
        world.get("popsicle").meters["fallen"] += 1
        world.say(
            f"The small treasure slipped at last. \"Wait!\" cried {guide.id}. \"Wait!\""
        )
        world.say(
            f"Still, the child caught only a sticky stick and a cold memory, while "
            f"the bright block of color ran down the hand like sunset."
        )
        world.say(
            f"After that, {hero.id} bowed to the lesson and carried the lesson more "
            f"carefully than the treat."
        )
        outcome = "lost"

    world.facts["outcome"] = outcome
    world.facts["ignited"] = world.get("popsicle").meters["drip"] >= THRESHOLD
    return world


SETTINGS = {
    "sunroad": Setting(
        id="sunroad",
        place="sun-road",
        sun="the noon sun",
        shade="an old cedar gate",
        route="the amber road",
        shrine="the cool shrine",
        air="hot",
    ),
    "harbor": Setting(
        id="harbor",
        place="harbor steps",
        sun="the white sun",
        shade="a stone wall",
        route="the blue steps",
        shrine="the shell shrine",
        air="bright",
    ),
}

TREATS = {
    "berry": Treat(
        id="berry",
        flavor="berry",
        phrase="a berry popsicle",
        color="red",
        coolness=2,
        sacred_name="frozen blessing",
        tags={"popsicle", "cool", "berry"},
    ),
    "mango": Treat(
        id="mango",
        flavor="mango",
        phrase="a mango popsicle",
        color="gold",
        coolness=2,
        sacred_name="sun-gold blessing",
        tags={"popsicle", "cool", "mango"},
    ),
    "mint": Treat(
        id="mint",
        flavor="mint",
        phrase="a mint popsicle",
        color="green",
        coolness=3,
        sacred_name="green frost",
        tags={"popsicle", "cool", "mint"},
    ),
}

THREATS = {
    "noon": Threat(id="noon", heat=1, shadow="noon glare", omen="the sun at its highest", tags={"heat"}),
    "festival": Threat(id="festival", heat=2, shadow="festival torches", omen="the bright crowd", tags={"heat"}),
}

CARERS = {
    "guide": Carrier(id="guide", title="guide", line="held out a cup of shade", caution="slowly", tags={"guide"}),
}

RESCUES = {
    "shadebowl": Rescue(
        id="shadebowl",
        skill=3,
        line="placed the popsicle in a bowl of shade and turned the child toward the shrine",
        ending="The blessing survived because someone chose shade before panic",
        tags={"shade", "save"},
    ),
    "clothwrap": Rescue(
        id="clothwrap",
        skill=2,
        line="wrapped the popsicle in a cool cloth and set it under the gate",
        ending="The little frost held on because the cloth and the shade worked together",
        tags={"cloth", "save"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Sera", "Nia", "Tala", "Iris"]
BOY_NAMES = ["Orin", "Kai", "Juno", "Pax", "Ren", "Timo"]
TRAITS = ["brave", "careful", "curious", "gentle"]
@dataclass
class StoryParams:
    setting: str
    treat: str
    threat: str
    carrier: str
    rescue: str
    hero_name: str = "Mira"
    hero_gender: str = "girl"
    guide_name: str = "Orin"
    delay: int = 0
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


CURATED = [
    StoryParams(
        setting="sunroad", treat="berry", threat="festival", carrier="guide", rescue="shadebowl",
        hero_name="Mira", hero_gender="girl" if False else "girl", guide_name="Orin", delay=0
    ),
    StoryParams(
        setting="harbor", treat="mint", threat="noon", carrier="guide", rescue="clothwrap",
        hero_name="Timo", hero_gender="boy" if False else "boy", guide_name="Nia", delay=1
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TREATS:
            for h in THREATS:
                combos.append((s, t, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic popsicle storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
              and (args.treat is None or c[1] == args.treat)
              and (args.threat is None or c[2] == args.threat)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treat, threat = rng.choice(sorted(combos))
    rescue = args.rescue or rng.choice(sorted(RESCUES))
    hero_gender = rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    guide_name = args.guide or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(
        setting=setting, treat=treat, threat=threat, carrier="guide", rescue=rescue,
        hero_name=hero_name, hero_gender=hero_gender, guide_name=guide_name, delay=delay
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.treat not in TREATS or params.threat not in THREATS or params.rescue not in RESCUES:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], TREATS[params.treat], THREATS[params.threat],
                 CARERS[params.carrier], RESCUES[params.rescue], params.hero_name,
                 params.guide_name, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a mythic suspense story that includes the word popsicle, with dialogue and a repeated warning.",
        f"Tell a short myth where {f['hero'].id} carries a popsicle through heat, speaks with {f['guide'].id}, and chooses the safer path.",
        "Write a child-sized legend about something small and cold surviving a hot journey.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    treat = f["treat"]
    setting = f["setting"]
    outcome = f["outcome"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, who carried a popsicle through an old mythic place. {guide.id} walked beside {hero.pronoun('object')} and helped guide the way."),
        ("What was the danger?",
         f"The heat could melt the popsicle before the journey was finished. That is why the story keeps warning about the sun and the slipping treat."),
        ("What did the guide say more than once?",
         f"The guide repeated the warning to slow down and hold the treat high. The repeated words made the danger feel close and made the child listen."),
    ]
    if outcome == "saved":
        qa.append((
            "How did the story end?",
            f"The popsicle stayed whole long enough to matter, and the child reached the shrine with it still cool. The ending image shows shade winning over heat."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"The popsicle melted and slipped away, leaving only a sticky stick and a lesson. The child kept going, but the treat was gone."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a popsicle?",
         "A popsicle is a frozen treat on a stick. People eat it when they want something cold and sweet."),
        ("Why does heat matter to a popsicle?",
         "Heat makes a popsicle melt. If the day is too hot, the cold treat gets soft and drippy very quickly."),
        ("What does shade do?",
         "Shade blocks some sunlight and helps things stay cooler. It can give a small, weak relief from strong heat."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
heat_risk(T,H) :- treat(T), threat(H), heat(H,HH), HH >= 1.
saved :- rescue(R), skill(R,S), delay(D), threat(H), heat(H,HH), S >= HH + D.
outcome(saved) :- saved.
outcome(lost) :- not saved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("coolness", tid, t.coolness))
    for hid, h in THREATS.items():
        lines.append(asp.fact("threat", hid))
        lines.append(asp.fact("heat", hid, h.heat))
    for rid, r in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("skill", rid, r.skill))
    lines.append(asp.fact("delay", 0))
    lines.append(asp.fact("delay", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    _ = asp.atoms(model, "outcome")
    # Smoke test ordinary generation.
    sample = generate(CURATED[0])
    if not sample.story:
        raise StoryError("Smoke test failed.")
    py = set(reasonables())
    return 0 if py else 1


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
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
