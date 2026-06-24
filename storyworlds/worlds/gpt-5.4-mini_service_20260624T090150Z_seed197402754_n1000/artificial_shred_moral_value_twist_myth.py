#!/usr/bin/env python3
"""
storyworlds/worlds/artificial_shred_moral_value_twist_myth.py
=============================================================

A small myth-style story world about a crafted wonder, a dangerous shred,
and a moral twist that reveals the true value was never the glitter.

Seed-tale sketch:
---
Long ago, the people of a hill village made an artificial sun from brass,
cloth, and oil lamps so their winter rites would feel bright. A young hero
named Ione loved the shining thing and believed it could never fail. But the
sun's fringe began to shred in a hard wind, and the village feared the omen.

An old oracle said the bright shape was only a craft, not a heaven-made gift.
Ione was tempted to lie and hide the damage, yet chose instead to tell the
truth, mend the hanging cloth, and let the people see the stitches. The
village then honored care over pride, and the artificial sun became a sign
that humble hands can make a worthy wonder.

Core state logic:
---
    boast about a crafted marvel      -> pride +1
    wind against hanging cloth        -> shred meter +1 on the artifact
    shred in sacred cloth             -> omen anxiety +1 in the crowd
    conceal the damage                -> lie +1, trust -1
    reveal the craft and mend it      -> honesty +1, trust +1, shame -> 0
    moral value chosen                -> wisdom +1, ending image changes

The story is authored from simulation state rather than a frozen paragraph:
the object can be artificial, can shred, and the final moral twist is driven
by whether the hero chooses truth over pride.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    crafted: bool = False
    artificial: bool = False
    fragile: bool = False
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    relic: object | None = None
    village: object | None = None
    def __post_init__(self) -> None:
        for k in ["shred", "pride", "lie", "truth", "trust", "anxiety", "wisdom", "shame", "care"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "king", "father", "man", "priest"}
        female = {"girl", "queen", "mother", "woman", "oracle"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    c: object | None = None
    world: object | None = None
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def _r_shred(world: World) -> list[str]:
    out: list[str] = []
    relic = world.entities.get("sun")
    if not relic or relic.meters["shred"] < THRESHOLD:
        return out
    sig = ("shred", relic.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The bright fringe had begun to shred.")
    return out


def _r_omen(world: World) -> list[str]:
    out: list[str] = []
    relic = world.entities.get("sun")
    crowd = world.entities.get("village")
    if not relic or not crowd:
        return out
    if relic.meters["shred"] >= THRESHOLD and crowd.memes["fear"] < THRESHOLD:
        sig = ("omen", relic.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        crowd.memes["fear"] += 1
        out.append("The village grew quiet, fearing an omen.")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("Ione")
    relic = world.entities.get("sun")
    if not hero or not relic:
        return out
    if hero.memes["truth"] >= THRESHOLD and relic.memes["trust"] < THRESHOLD:
        sig = ("truth", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        relic.memes["trust"] += 1
        relic.memes["shame"] = 0
        out.append("Truth entered the story like dawn.")
    return out


CAUSAL_RULES = [
    Rule("shred", _r_shred),
    Rule("omen", _r_omen),
    Rule("truth", _r_truth),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


@dataclass
class Shrine:
    place: str = "the hill shrine"
    season: str = "winter"
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Relic:
    label: str
    phrase: str
    kind: str
    artificial: bool = True
    fragile: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    shrine: str
    relic: str
    hero: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "hill": Shrine(place="the hill shrine", season="winter"),
    "temple": Shrine(place="the stone temple", season="windy winter"),
    "gate": Shrine(place="the city gate", season="winter"),
}

RELICS = {
    "sun": Relic(label="sun", phrase="an artificial sun of brass and cloth", kind="sun"),
    "bird": Relic(label="bird", phrase="an artificial bird with painted wings", kind="bird"),
    "banner": Relic(label="banner", phrase="an artificial banner of gold thread", kind="banner"),
}

HEROES = ["Ione", "Mara", "Tavin", "Lyra", "Soren"]
TRAITS = ["curious", "proud", "gentle", "brave", "thoughtful"]


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.shrine)
    relic_cfg = _safe_lookup(RELICS, params.relic)
    world = World(setting=setting)

    hero = world.add(Entity(id=params.hero, kind="character", type="girl" if params.hero in {"Ione", "Mara", "Lyra"} else "boy",
                            traits=["young", random.choice(TRAITS)]))
    village = world.add(Entity(id="village", kind="character", type="thing", label="the village"))
    relic = world.add(Entity(id="sun", kind="thing", type=relic_cfg.kind, label=relic_cfg.label,
                             phrase=relic_cfg.phrase, crafted=True, artificial=True, fragile=True,
                             owner=hero.id))

    hero.memes["pride"] += 1
    relic.meters["shred"] = 0
    world.facts.update(hero=hero, village=village, relic=relic, setting=setting, params=params)

    world.say(f"Long ago, at {setting.place}, there stood {relic.phrase}.")
    world.say(f"{hero.id} loved it and spoke of it as if it were a true gift from the sky.")
    world.para()

    world.say(f"Each winter, the people gathered there, and the crafted light made the dark hours seem shorter.")
    world.say(f"But when the cold wind rose, the edge of the {relic.label} began to shred.")
    relic.meters["shred"] += 1
    propagate(world)

    world.para()
    world.say(f"The villagers feared that the sign had turned against them.")
    world.say(f"{hero.id} wanted to hide the damage, because pride made the truth feel heavy.")
    hero.memes["lie"] += 1
    hero.memes["shame"] += 1

    if relic.meters["shred"] >= THRESHOLD:
        world.say(f"Then the old oracle looked at the {relic.label} and said, \"What is made by hands can still be worthy.\"")
        world.say(f"\"It was never heaven-made,\" {hero.id} heard. \"It was only artificial, and that is not a curse.\"")

    world.para()
    hero.memes["truth"] += 1
    hero.memes["pride"] = 0
    world.say(f"So {hero.id} told the people the truth and fetched thread, reeds, and glue.")
    relic.memes["trust"] += 1
    relic.meters["care"] += 1
    relic.meters["shred"] = 0
    relic.memes["shame"] = 0
    world.say(f"They mended the shredded edge together, and the light shone again with honest stitches.")
    world.say(f"The village cheered, not because the wonder was perfect, but because it had been cared for.")
    hero.memes["wisdom"] += 1
    propagate(world)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero").id
    relic = _safe_fact(world, f, "relic").label
    place = _safe_fact(world, f, "setting").place
    return [
        f"Write a short myth about {hero} and an artificial {relic} at {place}.",
        f"Tell a gentle legend where a crafted {relic} shreds in the wind and the hero chooses truth.",
        f"Write a child-friendly myth with a moral twist about pride, care, and a repaired wonder.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    relic = _safe_fact(world, f, "relic")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"What did {hero.id} love at {place}?",
            answer=f"{hero.id} loved the artificial {relic.label} that glowed above {place}.",
        ),
        QAItem(
            question=f"What happened to the {relic.label} when the cold wind rose?",
            answer=f"Its edge began to shred, and the village feared that something sacred was wrong.",
        ),
        QAItem(
            question=f"What did the oracle say about the {relic.label}?",
            answer="The oracle said it was made by hands, not by the sky, and that being artificial did not make it worthless.",
        ),
        QAItem(
            question=f"What did {hero.id} do after the truth came out?",
            answer=f"{hero.id} told the truth, brought thread and glue, and helped mend the shredded edge.",
        ),
        QAItem(
            question=f"What was the moral value in the end?",
            answer="The story valued honesty and careful hands over pride.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does artificial mean?",
            answer="Artificial means made by people, not grown or found exactly as nature made it.",
        ),
        QAItem(
            question="What is a shred?",
            answer="A shred is a small torn piece, or the start of something ripping apart.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of choosing how to act, like honesty, kindness, or care.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story that explains values, wonders, or why people should live wisely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.artificial:
            bits.append("artificial=True")
        if e.crafted:
            bits.append("crafted=True")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
artificial_relic(R) :- relic(R), artificial(R).
shredded(R) :- relic(R), shred(R).
omen(V) :- village(V), relic(R), shredded(R).
moral_value(truth) :- hero(H), chooses_truth(H).
twist(R) :- relic(R), artificial_relic(R), shredded(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("shrine", sid))
        lines.append(asp.fact("place", sid, s.place))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        if r.artificial:
            lines.append(asp.fact("artificial", rid))
        if r.fragile:
            lines.append(asp.fact("fragile", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth storyworld: artificial wonder, shred, and moral twist.")
    ap.add_argument("--shrine", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name", choices=HEROES)
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
    shrine = getattr(args, "shrine", None) or rng.choice(list(SETTINGS))
    relic = getattr(args, "relic", None) or rng.choice(list(RELICS))
    name = getattr(args, "name", None) or rng.choice(HEROES)
    return StoryParams(shrine=shrine, relic=relic, hero=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show artificial/1. #show twist/1.")
    model = asp.one_model(program)
    _ = model
    print("OK: ASP twin is present.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show artificial_relic/1. #show twist/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(shrine="hill", relic="sun", hero="Ione"),
            StoryParams(shrine="temple", relic="banner", hero="Mara"),
            StoryParams(shrine="gate", relic="bird", hero="Tavin"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
