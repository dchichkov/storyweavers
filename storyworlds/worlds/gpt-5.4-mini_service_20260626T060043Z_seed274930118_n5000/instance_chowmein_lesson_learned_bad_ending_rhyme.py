#!/usr/bin/env python3
"""
A tiny pirate-tale story world about a chowmein caper, a lesson learned, and
a bad ending told with a rhyme.

The seed idea:
- A pirate crew is on a small ship.
- A hungry pirate notices a hot bowl of chowmein.
- Someone warns them to wait.
- The pirate rushes anyway, the bowl spills, and the meal is lost.
- The ending is "bad" in the sense that nobody gets the chowmein, but the
  pirate learns to ask first and to mind the deck.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports shared results eagerly
- lazy ASP import
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: str = ""
    captain: object | None = None
    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pirate", "boy", "man", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
class Setting:
    place: str = "the little ship"
    affords: set[str] = field(default_factory=set)
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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


@dataclass
class Rule:
    name: str
    apply: callable
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


def _apply_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("clumsy", 0.0) < THRESHOLD and actor.meters.get("rush", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("hot_chowmein", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.owner != actor.id or item.worn_by != actor.id:
                continue
            if item.region not in world.zone:
                continue
            sig = ("spill", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1.0
            item.meters["saucy"] = item.meters.get("saucy", 0.0) + 1.0
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got saucy and dirty.")
    return out


def _apply_empty_belly(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("hunger", 0.0) < THRESHOLD:
            continue
        sig = ("hunger", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["grumpy"] = actor.memes.get("grumpy", 0.0) + 1.0
        out.append(f"{actor.id}'s belly rumbled louder than the gulls.")
    return out


CAUSAL_RULES = [
    Rule("spill", _apply_spill),
    Rule("empty_belly", _apply_empty_belly),
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


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        pass
    world.zone = set(action.zone)
    actor.meters[action.mess] = actor.meters.get(action.mess, 0.0) + 1.0
    actor.meters["hot_chowmein"] = actor.meters.get("hot_chowmein", 0.0) + 1.0
    actor.meters["rush"] = actor.meters.get("rush", 0.0) + 1.0
    propagate(world, narrate=narrate)


def predict_spill(world: World, actor: Entity, action: Action, prize_id: str) -> bool:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.fired = set(world.fired)
    sim.zone = set(world.zone)
    sim.facts = dict(world.facts)
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters.get("dirty", 0.0) >= THRESHOLD


def chorus(word: str, line: str) -> str:
    return f"{line} — {word}, chowmein, on the brine."


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"On a little ship with a swaying mast, {hero.id} was a {', '.join(hero.traits)} pirate who loved a full belly."
    )


def craving(world: World, hero: Entity, action: Action) -> None:
    hero.meters["hunger"] = hero.meters.get("hunger", 0.0) + 1.0
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1.0
    world.say(
        f"{hero.pronoun().capitalize()} sniffed the air and grinned, because the galley smelled like {action.keyword}."
    )


def set_out(world: World, hero: Entity, action: Action, prize: Entity) -> None:
    world.say(
        f"Near the rail, a warm bowl of {prize.phrase} waited, and {hero.id} wanted to {action.verb} right away."
    )


def warn(world: World, captain: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    if not predict_spill(world, hero, action, prize.id):
        return False
    world.say(
        f"\"Wait, matey,\" said {captain.id}. \"If you rush now, that {prize.label} will spill on the deck.\""
    )
    return True


def ignore_warning(world: World, hero: Entity, action: Action) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1.0
    world.say(f"But {hero.id} had a hungry blink and tried to {action.rush}.")


def slip_and_spill(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["oops"] = hero.memes.get("oops", 0.0) + 1.0
    world.say(
        f"{hero.id} slipped on the wet plank, and the bowl tipped over in a brown-and-golden splash."
    )
    world.say(
        f"The chowmein slid under a barrel, and the gulls pecked at the noodles before anyone could catch them."
    )


def lesson(world: World, captain: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1.0
    world.say(
        f"{hero.id} hung {hero.pronoun('possessive')} head and listened when {captain.id} said,"
        f" \"A fast bite can make a sad sight; ask first, and keep your feet light.\""
    )
    world.say(
        f"So the crew ate plain ship biscuit instead, and {hero.id} learned to wait for the next pot of {prize.label}."
    )


SETTINGS = {
    "ship": Setting(place="the little ship", affords={"chowmein"}),
}

ACTIONS = {
    "chowmein": Action(
        id="chowmein",
        verb="eat the chowmein",
        gerund="eating chowmein",
        rush="dash to the galley",
        mess="sticky",
        soil="spilled",
        zone={"deck"},
        keyword="chowmein",
        tags={"food", "noodles", "mess"},
    ),
}

PRIZES = {
    "chowmein": Prize(
        label="chowmein",
        phrase="a steaming bowl of chowmein",
        type="bowl",
        region="deck",
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Tess"]
BOY_NAMES = ["Bram", "Jory", "Finn"]
PIRATE_TRAITS = ["brisk", "greedy", "cheeky", "sunburnt"]


@dataclass(frozen=True)
class Incident:
    title: str
    premise: str
    warning: str
    mistake: str
    consequence: str
    evidence: str
    repair: str
    lesson: str
    ending: str
    rhyme: tuple[str, str]


INCIDENTS = [
    Incident(
        title="the rolling-bowl supper",
        premise="The cook set a covered bowl of chowmein in a rack until the ship stopped rocking.",
        warning="the deck was tilting and the hot bowl needed to stay in its rack",
        mistake="unlatched the rack and tried to carry the bowl alone",
        consequence="A swell rolled the bowl into an empty wash tub. Supper was too cold and soggy to serve.",
        evidence="a line of sauce pointed from the open latch to the tub",
        repair="scrubbed the tub, secured the latch, and helped the cook label a safe cooling shelf",
        lesson="waiting for a steady deck protects both people and food",
        ending="Moonlight shone through the clean, empty rack while everyone shared dry crackers",
        rhyme=("Latch the rack before waves attack", "Wait for the bell, and supper goes well"),
    ),
    Incident(
        title="the missing supper bell",
        premise="Chowmein waited beneath a lid while the cook searched for the brass supper bell.",
        warning="no food could be served until clean bowls were set and every crewmate had washed up",
        mistake="rang a tin cup and announced supper before the table was ready",
        consequence="The uncovered pot cooled while the crew formed the wrong line, so the cook saved it for tomorrow instead.",
        evidence="the real bell was hanging behind a freshly washed apron",
        repair="returned the cup, found the bell, and wrote a simple serving checklist with the cook",
        lesson="pretending a job is finished can waste the work everyone was protecting",
        ending="The true bell hung silent above a neat table, but every plate remained empty that night",
        rhyme=("A borrowed clang can steer things wrong", "Check what is true before calling the crew"),
    ),
    Incident(
        title="the salt-spray window",
        premise="The galley window stood open to cool a fresh pan of chowmein without anyone touching it.",
        warning="the weather vane showed that spray would soon blow through the window",
        mistake="ignored the vane and wedged the window wider for a stronger breeze",
        consequence="A salty gust splashed the pan, and the cook discarded the spoiled supper.",
        evidence="wet salt crystals glittered only on the sill and the near side of the pan",
        repair="closed the window, wiped the galley, and helped fit a screened cooling shelf indoors",
        lesson="curiosity should lead to checking signs, not brushing them aside",
        ending="The dry screen clicked into place as the untouched plates were stacked away",
        rhyme=("Read the vane before wind and rain", "A careful eye keeps supper dry"),
    ),
    Incident(
        title="the knotted serving rope",
        premise="The cook planned to lower sealed portions of chowmein to a watch crew on the dock.",
        warning="the serving rope had to be tested with a practice weight before carrying food",
        mistake="trusted a fancy-looking knot and skipped the practice test",
        consequence="The sealed carrier dropped onto the dock and cracked, so none of its food could be served.",
        evidence="the loose rope end showed that the knot had never been tucked through its final loop",
        repair="kept everyone back, fetched the cook, and practiced the correct knot with an empty carrier",
        lesson="confidence is not a substitute for a safe test",
        ending="A sound practice knot held an empty bucket above the dock where supper should have been",
        rhyme=("Test every knot before lifting the pot", "Practice it right before cargo takes flight"),
    ),
    Incident(
        title="the painted menu mix-up",
        premise="Two covered pans sat apart: mild chowmein for the crew and a marked pan for a crewmate with food allergies.",
        warning="only the cook could move the pans because their labels kept each meal safe",
        mistake="swapped the bright lids to make the table look more colorful",
        consequence="The cook could no longer prove which pan was safe, so both meals had to be set aside.",
        evidence="matching paint smudges showed exactly when the lids had been exchanged",
        repair="admitted the swap, cleaned the table, and helped make large labels that stayed with each pan",
        lesson="food labels protect people and must never be treated as decorations",
        ending="Two bold new labels dried beside two closed pans that nobody ate from",
        rhyme=("Keep labels in place for each person's case", "When markings stay clear, safe supper is near"),
    ),
    Incident(
        title="the galley shortcut",
        premise="A narrow galley aisle led past a tray of cooling chowmein to the supper table.",
        warning="a coil of clean rope blocked the aisle and needed to be put away before anyone carried food",
        mistake="stepped over the coil instead of asking a deckhand to clear it",
        consequence="A serving tray tipped onto the floor. The cook threw the food away rather than serve it.",
        evidence="one sandal print crossed the rope beside the fallen tray",
        repair="marked the spill, called the cook, and helped clear and mop the aisle without touching the hot pan",
        lesson="a short delay is better than an unsafe shortcut",
        ending="The mopped boards gleamed, and an empty serving spoon rested across the cold stove",
        rhyme=("Clear the way before trays sway", "Slow feet keep a meal complete"),
    ),
    Incident(
        title="the gull-proof cover",
        premise="A covered bowl of chowmein cooled on a high galley counter while gulls circled outside.",
        warning="the fitted cover had to remain closed until the cook returned",
        mistake="lifted the cover to show a friend the curly noodles",
        consequence="A gull swooped through the hatch and pecked the food, making the whole bowl unsafe to eat.",
        evidence="one white feather lay beside the shifted cover",
        repair="shooed the gull from a distance, shut the hatch, and helped the cook sanitize the counter",
        lesson="sharing a look is not worth uncovering protected food",
        ending="The scrubbed counter smelled of soap while the gull watched an empty bowl from the mast",
        rhyme=("Cover the fare when gulls fill the air", "Guard every bite by closing it tight"),
    ),
    Incident(
        title="the cracked ladle",
        premise="The cook left chowmein warming safely and asked the crew to set out clean serving tools.",
        warning="a ladle with a split handle belonged in the repair bin, not beside the food",
        mistake="hid the crack with ribbon and placed the ladle on the table",
        consequence="The handle snapped before serving. The ladle fell into the pan, and supper was discarded.",
        evidence="the loose ribbon revealed the old split beneath it",
        repair="told the truth, carried the broken tool to the repair bin, and checked every replacement with the cook",
        lesson="hiding damage turns a small problem into a larger one",
        ending="A sturdy clean ladle waited for tomorrow beside the ribbonless repair bin",
        rhyme=("Never disguise a crack from wise eyes", "Name what is wrong, and tools stay strong"),
    ),
    Incident(
        title="the lantern-shadow race",
        premise="Lantern shadows stretched across the deck while chowmein stayed covered in the galley.",
        warning="the captain had ended running games because the evening deck was damp",
        mistake="challenged a friend to race the longest shadow toward the galley door",
        consequence="The racers struck the supper cart. Its covered pot stayed shut, but the wheels bent and dinner could not be delivered.",
        evidence="two sliding footprints ended beside the crooked front wheel",
        repair="checked that everyone was unhurt, fetched the captain, and helped chock the cart for repair",
        lesson="a fun idea belongs in a place where it cannot spoil someone else's work",
        ending="Two still shadows lay across the deck beside the bent cart and its cooling pot",
        rhyme=("Race in the light where the footing is right", "On boards that are wet, choose quiet play yet"),
    ),
    Incident(
        title="the false spice clue",
        premise="A fragrant bowl of chowmein waited for a tasting by the cook, who kept every spice jar clearly marked.",
        warning="nobody should season the finished dish without permission",
        mistake="guessed that an unmarked shaker held pepper and sprinkled it into the bowl",
        consequence="The shaker held bitter cleaning powder for the stove, so the cook discarded the food immediately.",
        evidence="a faded brush symbol on the shaker matched the cleaning cupboard",
        repair="closed the galley, told the cook, and helped move every cleaning supply away from ingredients",
        lesson="unknown substances must never be guessed at or put near food",
        ending="The locked cleaning cupboard clicked shut as the empty supper bowls cooled",
        rhyme=("If labels are slight, stop and ask what is right", "Never taste or pour what you are not sure"),
    ),
    Incident(
        title="the leaky rain barrel",
        premise="The crew carried a sealed pot of chowmein below deck before a rainstorm arrived.",
        warning="a dripping barrel had made the storage floor slippery and the route was closed",
        mistake="removed the warning rope to fetch a favorite spoon from the closed room",
        consequence="The returning cook slipped but kept hold of the sealed pot; dinner was delayed until it was no longer safe to serve.",
        evidence="fresh drops led from the barrel to the place where the warning rope had been moved",
        repair="apologized, restored the rope, and brought towels while an adult repaired the barrel",
        lesson="safety barriers matter even when the thing you want seems close",
        ending="Rain tapped the hatch above a roped-off floor and a sealed pot bound for the waste pail",
        rhyme=("Leave the rope where warning signs spoke", "A spoon can wait when the floor is not straight"),
    ),
    Incident(
        title="the captain's portion count",
        premise="The cook counted equal covered portions of chowmein for a crew returning from a long watch.",
        warning="each bowl had a name card so nobody would be left without supper",
        mistake="took a second covered bowl and hid it behind a flour sack",
        consequence="The search lasted too long, and the hidden portion passed its safe serving time.",
        evidence="a corner of the missing name card stuck out beneath the sack",
        repair="returned the bowl unopened, admitted the choice, and helped record every discarded portion",
        lesson="taking more than one's share can leave everyone with less",
        ending="One crossed-out name card remained on the table beside the unopened bowl that had to be thrown away",
        rhyme=("Count every share and leave each one there", "More for just one can mean supper for none"),
    ),
]


TELLING_MODES = [
    ("At dawn, the ship's log opened on", "The clue changed a boast into a question."),
    ("One windy afternoon brought", "For once, the loudest pirate listened first."),
    ("The quietest watch of the week began with", "The deck went quiet while the evidence did the talking."),
    ("Just before the supper bell came", "A quick plan failed, but a careful look explained why."),
    ("Under a sky striped pink and gray waited", "What seemed unlucky had begun with one avoidable choice."),
    ("The crew would long remember", "Nobody needed a villain; they needed the truth."),
    ("A page titled 'Lessons Learned' described", "The smallest clue proved more useful than the biggest guess."),
    ("Between two rolling waves unfolded", "An honest answer arrived after an unwise action."),
    ("The cook's empty supper board later recorded", "The bad ending was already taking shape before anyone noticed."),
    ("A gull on the mast witnessed", "The rhyme came later; first came the consequence."),
]


@dataclass
class StoryParams:
    setting: str
    action: str
    prize: str
    name: str
    role: str
    captain: str
    trait: str
    seed: Optional[int] = None
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


def build_story(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    seed = params.seed if params.seed is not None else 0
    incident = INCIDENTS[seed % len(INCIDENTS)]
    opening, turn = TELLING_MODES[(seed // len(INCIDENTS)) % len(TELLING_MODES)]
    girl = params.name in GIRL_NAMES
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if girl else "boy",
        traits=[params.trait, "pirate"],
    ))
    captain = world.add(Entity(
        id=params.captain,
        kind="character",
        type="captain",
        traits=["old", "steady", "captain"],
    ))
    prize = world.add(Entity(
        id="bowl",
        type="bowl",
        label="chowmein",
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        owner=hero.id,
        caretaker=captain.id,
        region="galley",
    ))
    hero.meters["hunger"] = 1.0
    hero.memes["impatience"] = 1.0

    world.say(
        f"{opening} {incident.title}. On the little ship, {params.name} was a {params.trait} young pirate, "
        f"and {params.captain} was the steady captain on watch. {incident.premise}"
    )
    world.say(
        f"The smell of chowmein curled through the galley. {params.name}'s stomach rumbled, but "
        f"{params.captain} warned that {incident.warning}."
    )

    world.para()
    world.say(
        f"\"I can manage one tiny shortcut,\" said {params.name}. Then {hero.pronoun()} "
        f"{incident.mistake}. {turn}"
    )
    world.say(f"The choice had a real cost. {incident.consequence}")
    world.say(
        f"\"Stop and look,\" said {params.captain}. Together they noticed that {incident.evidence}. "
        f"{params.name} understood how {hero.pronoun('possessive')} own choice had caused the trouble."
    )

    world.para()
    world.say(
        f"Without tasting or rescuing any unsafe food, {params.name} {incident.repair}. "
        f"This became one instance in the ship's lesson book. "
        f"\"My lesson learned is that {incident.lesson},\" {hero.pronoun()} said."
    )
    world.say(
        f"It was a bad ending for supper, not for the crew: everyone was safe, but there was no chowmein to eat. "
        f"{incident.ending}."
    )
    world.say(f"{incident.rhyme[0]}; {incident.rhyme[1]}. Yo-ho, that was the rhyme!")

    hero.meters["hunger"] = 2.0
    hero.memes["lesson"] = 1.0
    hero.memes["honesty"] = 1.0
    prize.meters["unservable"] = 1.0
    world.fired.add(("incident", incident.title))
    world.facts.update(
        hero=hero,
        captain=captain,
        prize=prize,
        action=_safe_lookup(ACTIONS, params.action),
        incident=incident,
        warning=incident.warning,
        consequence=incident.consequence,
        evidence=incident.evidence,
        repair=incident.repair,
        lesson=incident.lesson,
        ending=incident.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "action")
    incident: Incident = f["incident"]
    return [
        f'Write a child-friendly pirate tale called "{incident.title}" that includes "{act.keyword}" and ends in rhyme.',
        f"Tell how {hero.id} caused a supper problem when {hero.pronoun()} {incident.mistake}, then learned a grounded lesson.",
        f"Make a safe bad-ending ship story with this consequence: {incident.consequence} End with the image: {incident.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    captain: Entity = _safe_fact(world, f, "captain")
    prize: Entity = _safe_fact(world, f, "prize")
    incident: Incident = f["incident"]
    qa = [
        QAItem(
            question=f"What unsafe or unfair shortcut did {hero.id} take?",
            answer=f"{hero.id} {incident.mistake}. That choice set the supper problem in motion.",
        ),
        QAItem(
            question=f"What warning did {captain.id} give before the trouble?",
            answer=f"{captain.id} warned that {incident.warning}. {hero.id} acted before following that warning.",
        ),
        QAItem(
            question=f"What evidence explained the trouble in {incident.title}?",
            answer=f"They found that {incident.evidence}. It connected {hero.id}'s choice to what happened.",
        ),
        QAItem(
            question=f"How did {hero.id} respond after the chowmein could not be served?",
            answer=f"{hero.id} {incident.repair}. The repair did not include eating or saving unsafe food.",
        ),
        QAItem(
            question=f"What lesson was learned from the bad ending?",
            answer=f"{hero.id} learned that {incident.lesson}. Everyone stayed safe even though the {prize.label} was not served.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "food": [
        QAItem(
            question="What is chowmein?",
            answer="Chowmein is a noodle dish that is often cooked with vegetables and sauce.",
        )
    ],
    "noodles": [
        QAItem(
            question="What are noodles?",
            answer="Noodles are long, thin strips of dough that people cook and eat in many meals.",
        )
    ],
    "mess": [
        QAItem(
            question="Why is a spilled bowl messy?",
            answer="A spilled bowl makes a mess because food can slide, splash, and stick where it should not be.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    out: list[QAItem] = []
    for tag in ["food", "noodles", "mess"]:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this pirate world only supports chowmein on the ship.)"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("ship", "chowmein", "chowmein")]


CURATED = [
    StoryParams(setting="ship", action="chowmein", prize="chowmein", name="Mira", role="pirate", captain="Capn Wren", trait="cheeky"),
    StoryParams(setting="ship", action="chowmein", prize="chowmein", name="Bram", role="pirate", captain="Captain Salt", trait="brisk"),
]


ASP_RULES = r"""
valid(S,A,P) :- setting(S), action(A), prize(P), affords(S,A), match(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("match", pid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with chowmein, rhyme, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["pirate"])
    ap.add_argument("--captain")
    ap.add_argument("--trait", choices=PIRATE_TRAITS)
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
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or "ship"
    action = getattr(args, "action", None) or "chowmein"
    prize = getattr(args, "prize", None) or "chowmein"
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    role = getattr(args, "role", None) or "pirate"
    captain = getattr(args, "captain", None) or rng.choice(["Captain Salt", "Capn Wren", "Old Hook"])
    trait = getattr(args, "trait", None) or rng.choice(PIRATE_TRAITS)
    return StoryParams(setting=setting, action=action, prize=prize, name=name, role=role, captain=captain, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
