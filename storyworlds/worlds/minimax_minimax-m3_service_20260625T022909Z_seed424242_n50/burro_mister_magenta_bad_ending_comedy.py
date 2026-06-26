#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/burro_mister_magenta_bad_ending_comedy.py
==============================================================================================================

A standalone *story world* sketch for "The Burro Who Wore Magenta" -- a
short, farcical tale told in a Comedy register with a deliberately
unresolved, *bad* ending.  The world model drives the prose; the bad
ending is a property of the simulation (a stubborn burro who refuses
the magenta cautionary sign) rather than a frozen last paragraph.

Initial story (used to build the world model):
---
There once was a stubborn little burro named Mister, who lived on a
bright ranch called Magenta Farm.  The ranch had a famous rule: any
burro who walked through the mud by the Magenta Pond would end up
covered from nose to hooves in the brightest, clingiest magenta
muck the world had ever seen.  Every burro on the ranch had been
splashed at least once, and they all wore a little sign on a string
that warned about it.  Mister's sign said so.  The other burros
wore it.  The chickens wore theirs.  Even the old dog wore his.

Mister, being a burro of great confidence and very small caution,
looked at his sign one sunny morning and brayed, "Mister does not
need a sign!"  He shook it off his neck, tossed it into a bush, and
tromped straight toward the Magenta Pond, where the mud was, as
always, absolutely, impossibly magenta.

"Please do not do that," said the wise old goose, who had been
warning burros for many seasons.  "I have read the sign too, and
it is true."

But Mister did not listen, because Mister never listened.  He
galloped (well, trotted very fast) straight to the pond, kicked up
his heels, and SPLASH.  A great wave of magenta mud arced into
the air and came down on Mister's head, his ears, his back, his
tail, and his brand-new straw hat.  The hat dripped magenta for
three days.  The chickens laughed.  The dog laughed.  The goose
gave a long, slow, disappointed sigh.

Mister tried to hide under a barrel, but the barrel was already
magenta.  He tried to roll in the hay, but the hay came out magenta
on the other side.  He tried to wade into the little creek to wash
it off, but the creek ran uphill that day (it was a strange
morning), and he just ended up even more magenta.  The other
burros gathered around, and they did not say, "Oh, you poor
thing."  They said, "Mister, we *told* you about the sign."  And
Mister, who was now entirely, absurdly, drippingly magenta, had
nothing to say at all, because he had ignored the sign, and the
sign was right, and the magenta was not coming off.

Causal state updates (the simulated version of the same tale):
---
    do mud splash         -> actor.magenta  += 1
                             actor.dripping += 1
    actor magenta + creek  -> actor.magenta  += 1   (creek fails / uphill water)
    actor magenta + hat    -> hat.magenta    += 1, hat.costly += 1
    actor magenta + barrel -> actor.magenta  += 1   (barrel is already magenta)
    actor magenta + hay    -> hay.magenta    += 1   (hay is ruined on the other side)
    ignore sign + muddy    -> actor.magenta  += 1, actor.taught += 0   (no learning)
    warn issued            -> actor.ignoring += 1
    "we told you"          -> actor.taught   stays at 0   (bad ending: nothing learned)

The point of the simulation is that the bad ending is *generated*:
Mister ends the story dripping magenta, the hat is ruined, the
hay is ruined, the barrel is ruined, the burros chorus in, and
nobody -- not even Mister -- has figured anything out.  That is
why the seed words say "Bad Ending" and "Comedy": the comedy is
the *badness* of the ending, not a triumphant one.
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

# Make the shared result containers importable when this script is run
# directly: add the package dir (storyworlds/) to sys.path so ``results``
# resolves regardless of the current directory.
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# Threshold at which an accumulated effect is "embedded enough" to narrate.
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------

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
    kind: str = "thing"             # "character" | "thing"
    type: str = "thing"             # burro, goose, dog, chicken, hat, sign, ...
    label: str = ""                 # short reference, e.g. "hat", "barrel"
    phrase: str = ""                # full noun phrase, e.g. "a brand-new straw hat"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    # Two numeric dimensions, treated uniformly (cf. the puddles world model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional / social
    plural: bool = False            # "chickens" -> them, "hat" -> it

    already_magenta: bool = False
    advisor: object | None = None
    barrel: object | None = None
    burros: object | None = None
    chickens: object | None = None
    dog: object | None = None
    hat: object | None = None
    hay: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"goose", "hen", "chicken", "cow", "ewe"}
        male = {"burro", "dog", "rooster", "ram", "bull", "stallion", "tom"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Parametrization knobs.
# ---------------------------------------------------------------------------
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
    place: str = "Magenta Farm"
    intro: str = ""                 # the opening line of place description
    feature: str = "magenta mud"    # what makes this place dangerous
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
class Mischief:
    """A messy thing the burro loves and is warned about."""
    id: str
    verb: str                       # "splash in the magenta mud"
    gerund: str                     # "splashing in the magenta mud"
    rush: str                       # "gallop straight to the magenta mud"
    splash_sound: str              # "SPLASH"
    cost: str                       # "covered from nose to hooves in magenta muck"
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


@dataclass
class Object:
    """A physical prop that the splash ruins, gets ruined in turn, or both."""
    id: str
    label: str                      # "hat"
    phrase: str                     # "a brand-new straw hat"
    type: str
    plural: bool = False
    already_magenta: bool = False   # the barrel: "barrel is already magenta"
    ruin: str = ""                  # how the burro's attempt to clean ruins the prop


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
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
        self.fired: set[tuple] = set()        # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.outcome: str = "bad"             # the comedy contract: this stays "bad"

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (the warner's prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.outcome = self.outcome
        clone.paragraphs = [[]]                # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
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


def _r_actor_splash(world: World) -> list[str]:
    """actor messy >= 1 (the splash hit him) -> dripping, magenta."""
    for actor in world.characters():
        if actor.meters["magenta"] < THRESHOLD:
            continue
        out: list[str] = []
        if actor.meters["dripping"] < THRESHOLD:
            sig = ("drip", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.meters["dripping"] += 1
        # Already-magenta hat: if the burro is wearing the hat when drenched,
        # the hat becomes magenta and costly (a straw hat is hard to clean).
        hat = world.entities.get("hat")
        if hat and hat.meters["magenta"] < THRESHOLD:
            hat.meters["magenta"] += 1
            hat.meters["costly"] += 1
        return out
    return []


def _r_creek(world: World) -> list[str]:
    """actor magenta + tried creek -> more magenta, NOT less (bad ending)."""
    for actor in world.characters():
        if actor.meters["magenta"] < THRESHOLD:
            continue
        if actor.memes["tried_creek"] < THRESHOLD:
            continue
        sig = ("creek", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["magenta"] += 1            # the creek made it worse
        return []
    return []


def _r_barrel(world: World) -> list[str]:
    """actor magenta + tried barrel -> the barrel is already magenta, no hiding."""
    for actor in world.characters():
        if actor.meters["magenta"] < THRESHOLD:
            continue
        if actor.memes["tried_barrel"] < THRESHOLD:
            continue
        sig = ("barrel", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["magenta"] += 1
        return []
    return []


def _r_hay(world: World) -> list[str]:
    """actor magenta + tried hay -> the hay comes out magenta on the other side."""
    for actor in world.characters():
        if actor.meters["magenta"] < THRESHOLD:
            continue
        if actor.memes["tried_hay"] < THRESHOLD:
            continue
        sig = ("hay", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["magenta"] += 1
        return []
    return []


# The bad-ending rule: even after the chorus of "we told you so", the burro
# does not learn.  The meme stays at zero.  We just record that the chorus
# has been issued so the screenplay can narrate the *absence* of a moral.
def _r_chorus(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["chorus_issued"] < THRESHOLD:
            continue
        if actor.memes["taught"] >= THRESHOLD:
            continue                              # (will never fire -- by design)
        sig = ("chorus", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        return []
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="actor_splash", tag="physical", apply=_r_actor_splash),
    Rule(name="creek", tag="physical", apply=_r_creek),
    Rule(name="barrel", tag="physical", apply=_r_barrel),
    Rule(name="hay", tag="physical", apply=_r_hay),
    Rule(name="chorus", tag="social", apply=_r_chorus),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
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


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting) -> str:
    if setting.intro:
        return setting.intro
    return (
        f"{setting.place} had a famous rule: any burro who walked through the "
        f"{setting.feature} would end up covered from nose to hooves in the "
        f"brightest, clingiest mess the ranch had ever seen."
    )


def introduce(world: World, hero: Entity, advisor: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "stubborn")
    world.say(
        f"There once was a stubborn little {hero.type} named {hero.id}, who "
        f"lived on a bright ranch called {world.setting.place}."
    )
    world.say(setting_detail(world.setting))


def every_burro_wore_a_sign(world: World, hero: Entity) -> None:
    world.say(
        f"Every {hero.type} on the ranch wore a little sign on a string that "
        f"warned about the {world.setting.feature}."
    )
    world.say(f"{hero.id}'s sign said so. The other burros wore theirs.")


def shake_off_sign(world: World, hero: Entity) -> None:
    """The comedy turn: ignore the warning."""
    hero.memes["ignoring"] += 1
    world.say(
        f"{hero.id}, being a {hero.type} of great confidence and very small "
        f"caution, looked at his sign one sunny morning and brayed, "
        f'"{hero.id} does not need a sign!"'
    )
    world.say(f"He shook it off his neck, tossed it into a bush, and tromped straight toward the {world.setting.feature}.")


def advisor_warns(world: World, advisor: Entity, mischief: Mischief) -> None:
    advisor.memes["warned"] += 1
    hero = world.get("Mister")
    hero.memes["warned"] += 1
    world.say(
        f'"{mischief.verb.capitalize() if not mischief.verb else 'Please do not do that,'}", '
        f"said the wise old {advisor.type}, who had been warning burros for many seasons. "
        f'"I have read the sign too, and it is true."'
    )


def defy(world: World, hero: Entity, mischief: Mischief) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But {hero.id} did not listen, because {hero.id} never listened. "
        f"He galloped (well, trotted very fast) straight to the {world.setting.feature}, "
        f"where the {mischief.id} was, as always, absolutely, impossibly magenta."
    )


def splash(world: World, hero: Entity, mischief: Mischief) -> None:
    """The defining simulation step: the splash hits the burro and the hat."""
    hero.meters["magenta"] += 1
    hat = world.entities.get("hat")
    if hat and hat.owner == hero.id:
        hat.meters["magenta"] += 1
        hat.meters["costly"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{mischief.splash_sound}. A great wave of magenta mud arced into the "
        f"air and came down on {hero.pronoun('possessive')} head, "
        f"{hero.pronoun('possessive')} ears, {hero.pronoun('possessive')} back, "
        f"{hero.pronoun('possessive')} tail, and {hero.pronoun('possessive')} "
        f"brand-new straw hat. The hat dripped magenta for three days."
    )


def onlookers_see(world: World) -> None:
    """The chickens, the dog, the goose: they laugh, the goose sighs."""
    chickens = world.entities.get("chickens")
    dog = world.entities.get("dog")
    goose = world.entities.get("goose")
    if chickens:
        chickens.memes["amused"] += 1
    if dog:
        dog.memes["amused"] += 1
    if goose:
        goose.memes["amused"] += 1
    world.say(
        f"The {chickens.label if chickens else 'chickens'} laughed. "
        f"The {dog.label if dog else 'dog'} laughed. "
        f"The {goose.label if goose else 'goose'} gave a long, slow, "
        f"disappointed sigh."
    )


def try_barrel(world: World, hero: Entity) -> None:
    hero.memes["tried_barrel"] += 1
    barrel = world.entities.get("barrel")
    if barrel:
        barrel.meters["magenta"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} tried to hide under the {barrel.label if barrel else 'barrel'}, "
        f"but the {barrel.label if barrel else 'barrel'} was already magenta."
    )


def try_hay(world: World, hero: Entity) -> None:
    hero.memes["tried_hay"] += 1
    hay = world.entities.get("hay")
    if hay:
        hay.meters["magenta"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} tried to roll in the {hay.label if hay else 'hay'}, but the "
        f"{hay.label if hay else 'hay'} came out magenta on the other side."
    )


def try_creek(world: World, hero: Entity) -> None:
    hero.memes["tried_creek"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} tried to wade into the little creek to wash it off, but the "
        f"creek ran uphill that day (it was a strange morning), and "
        f"{hero.pronoun('subject')} just ended up even more magenta."
    )


def chorus_issued(world: World, hero: Entity) -> None:
    """The bad-ending beat: the other burros chorus in, Mister learns nothing."""
    hero.memes["chorus_issued"] += 1
    propagate(world, narrate=False)
    burros = world.entities.get("burros")
    if burros:
        burros.memes["amused"] += 1
    world.say(
        f"The other {burros.label if burros else 'burros'} gathered around, and they did not say, "
        f'"Oh, you poor thing."'
    )
    world.say(
        f'They said, "{hero.id}, we told you about the sign."'
    )


def final_image(world: World, hero: Entity) -> None:
    """The bad ending: Mister has nothing to say, the magenta is not coming off."""
    world.outcome = "bad"
    world.say(
        f"And {hero.id}, who was now entirely, absurdly, drippingly magenta, had "
        f"nothing to say at all, because {hero.pronoun('subject')} had ignored "
        f"the sign, and the sign was right, and the magenta was not coming off."
    )


# ---------------------------------------------------------------------------
# The screenplay: a strict three-act shape, driven by the verbs above.
# The bad ending is *baked in* by the order of the verbs; no override path.
# ---------------------------------------------------------------------------
def tell(setting: Setting, mischief: Mischief, hat_cfg: Object, hero_name: str = "Mister",
         advisor_type: str = "goose") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type="burro",
        traits=["little", "stubborn", "confident"],
    ))
    advisor = world.add(Entity(
        id="Advisor", kind="character", type=advisor_type,
        label=f"the wise old {advisor_type}", traits=["patient", "long-suffering"],
    ))
    chickens = world.add(Entity(
        id="chickens", kind="character", type="chicken",
        label="chickens", plural=True, traits=["merry"],
    ))
    dog = world.add(Entity(
        id="dog", kind="character", type="dog",
        label="dog", traits=["old", "watchful"],
    ))
    burros = world.add(Entity(
        id="burros", kind="character", type="burro",
        label="burros", plural=True, traits=["knowing"],
    ))
    hat = world.add(Entity(
        id="hat", type=hat_cfg.type, label=hat_cfg.label,
        phrase=hat_cfg.phrase, owner=hero.id, plural=hat_cfg.plural,
    ))
    barrel = world.add(Entity(
        id="barrel", type="barrel", label="barrel",
        phrase="an old rain barrel", already_magenta=True,
    ))
    hay = world.add(Entity(
        id="hay", type="hay", label="hay", plural=False,
        phrase="a pile of fresh hay",
    ))

    # Act 1 -- setup: who, where, the rule, the sign.
    introduce(world, hero, advisor)
    every_burro_wore_a_sign(world, hero)

    # Act 2 -- the warning and the splash.
    world.para()
    shake_off_sign(world, hero)
    advisor_warns(world, advisor, mischief)
    defy(world, hero, mischief)
    splash(world, hero, mischief)
    onlookers_see(world)

    # Act 3 -- the three failed clean-up attempts (each makes it worse).
    world.para()
    try_barrel(world, hero)
    try_hay(world, hero)
    try_creek(world, hero)

    # The bad ending: chorus + silence.  The burros do not save Mister.
    world.para()
    chorus_issued(world, hero)
    final_image(world, hero)

    # Record facts for Q&A generators (grounded in the simulated world).
    world.facts.update(
        hero=hero, advisor=advisor, chickens=chickens, dog=dog, burros=burros,
        hat=hat, barrel=barrel, hay=hay, mischief=mischief, setting=setting,
        outcome=world.outcome,
        ignored=hero.memes["ignoring"] >= THRESHOLD,
        warned=hero.memes["warned"] >= THRESHOLD,
        magenta=hero.meters["magenta"] >= THRESHOLD,
        hat_magenta=hat.meters["magenta"] >= THRESHOLD,
        chorus=hero.memes["chorus_issued"] >= THRESHOLD,
        learned=hero.memes["taught"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "magenta_farm": Setting(
        place="Magenta Farm",
        intro=("Magenta Farm had a famous rule: any burro who walked through "
               "the magenta mud by the Magenta Pond would end up covered from "
               "nose to hooves in the brightest, clingiest muck the ranch had "
               "ever seen."),
        feature="magenta mud",
    ),
    "rose_ranch": Setting(
        place="Rose Ranch",
        intro=("Rose Ranch was bright with paint, and the front gate was always "
               "splattered with the leftover pink from the painting bees. The "
               "rule there was simple: a burro who runs through the painting "
               "yard comes out pink from ears to hooves."),
        feature="pink paint yard",
    ),
    "tangerine_track": Setting(
        place="Tangerine Track",
        intro=("Tangerine Track was famous for its orange-juice field, and the "
               "rule on the sign said, plain as could be, that any burro who "
               "galloped through the juice would come out tangerine and sticky."),
        feature="tangerine juice",
    ),
}

MISCHIEFS = {
    "magenta_mud": Mischief(
        id="magenta mud",
        verb="splash in the magenta mud",
        gerund="splashing in the magenta mud",
        rush="gallop straight to the magenta mud",
        splash_sound="SPLASH",
        cost="covered from nose to hooves in magenta muck",
    ),
    "pink_paint": Mischief(
        id="pink paint",
        verb="run through the pink paint",
        gerund="running through the pink paint",
        rush="race straight into the paint yard",
        splash_sound="SPLAT",
        cost="covered from nose to hooves in pink paint",
    ),
    "tangerine_juice": Mischief(
        id="tangerine juice",
        verb="gallop through the tangerine juice",
        gerund="galloping through the tangerine juice",
        rush="gallop straight into the juice",
        splash_sound="GLUG-GLUG",
        cost="covered from nose to hooves in tangerine juice",
    ),
}

OBJECTS = {
    "hat": Object(
        id="hat", label="hat", type="hat",
        phrase="a brand-new straw hat", plural=False,
    ),
    "blanket": Object(
        id="blanket", label="blanket", type="blanket",
        phrase="a brand-new wool blanket", plural=False,
    ),
    "saddle": Object(
        id="saddle", label="saddle", type="saddle",
        phrase="a brand-new leather saddle", plural=False,
    ),
}

ADVISORS = {
    "goose": "goose",
    "dog": "dog",
    "rooster": "rooster",
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Jack", "Finn", "Noah", "Eli", "Theo"]
DONKEY_NAMES = ["Mister", "Nibs", "Pedro", "Donk", "Beans", "Otis", "Biscuit", "Marble"]


def valid_combos() -> list[tuple[str, str, str]]:
    """Every (setting, mischief, object) triple is reasonable for this world --
    the bad-ending is the *style* of the story, not a constraint on inputs."""
    return [
        (s, m, o)
        for s in SETTINGS
        for m in MISCHIEFS
        for o in OBJECTS
    ]


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce one story (deterministic given these)."""
    place: str
    mischief: str
    obj: str
    name: str
    advisor: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.  These are answerable WITHOUT
# the story; they explain the *elements* the world is built from.
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


KNOWLEDGE = {
    "burro": [("What is a burro?",
               "A burro is a small donkey, with a soft coat, long ears, and a "
               "loud, funny bray that sounds a little like laughter.")],
    "magenta": [("What color is magenta?",
                 "Magenta is a bright purply-pink color, like a really strong "
                 "raspberry mixed with a little bit of purple.")],
    "sign": [("Why do people put up signs that say things?",
              "Signs are short messages that warn or remind you about "
              "something important, so you do not forget the rule.")],
    "goose": [("What is special about a goose?",
               "A goose is a large bird that honks loudly and is known for "
               "being brave and bossy, especially when it is protecting its "
               "friends.")],
    "mud": [("Why does mud stick to a coat?",
             "Mud sticks to a coat because it is wet and a little bit sticky, "
             "so it clings to fur and straw and straw hats until it dries.")],
    "hat": [("Why is a straw hat easy to ruin?",
              "A straw hat is woven from dry grass, and once wet paint or mud "
              "gets in the weave, it stains the strands and is very hard to "
              "wash out.")],
    "barrel": [("What is a rain barrel for?",
                "A rain barrel catches rainwater that runs off a roof, so the "
                "water can be used later for the garden.")],
    "bad_ending": [("What is a bad ending in a funny story?",
                    "A bad ending in a funny story is when the hero does not "
                    "learn a lesson and ends up in a silly, messy situation "
                    "that everyone can laugh about together.")],
    "comedy": [("What makes a story a comedy?",
                "A comedy is a story full of silly mishaps, big reactions, and "
                "absurd problems, where the fun is in the mess, not in a "
                "perfect ending.")],
}
KNOWLEDGE_ORDER = ["burro", "magenta", "sign", "goose", "mud", "hat",
                   "barrel", "bad_ending", "comedy"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, mischief, setting = f["hero"], f["mischief"], f["setting"]
    hat = _safe_fact(world, f, "hat")
    return [
        f'Write a short, funny story for a 4-to-6-year-old on the theme "a '
        f'stubborn burro ignores a warning sign and ends up a mess" that '
        f'includes the word "{mischief.id}".',
        f"Tell a comedic tale where a burro named {hero.id} lives on "
        f"{setting.place}, ignores a sign that warns about the {mischief.id}, "
        f"and gets thoroughly, comically, irreparably messy.",
        f'Write a small comedy with a deliberately bad ending in which a '
        f"burro ends the story dripping with {mischief.id.split()[0]} and "
        f"ruins {hero.pronoun('possessive')} {hat.label} in the process.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, advisor, mischief, setting = f["hero"], f["advisor"], f["mischief"], f["setting"]
    hat = _safe_fact(world, f, "hat")
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about at {setting.place} when the warning "
                f"sign is being ignored?"
            ),
            answer=(
                f"It is about a stubborn little burro named {hero.id} who "
                f"lives on a ranch called {setting.place}. {hero.id} ignores "
                f"the warning sign that all the other burros wear."
            ),
        ),
        QAItem(
            question=(
                f"What did the wise old {advisor.type} say to {hero.id} before "
                f"the splash in the {mischief.id}?"
            ),
            answer=(
                f"The wise old {advisor.type}, who had been warning burros for "
                f"many seasons, told {hero.id} not to do it, and reminded "
                f"{obj} that the sign was true."
            ),
        ),
        QAItem(
            question=(
                f"What happened to {hero.id}'s {hat.label} when the wave of "
                f"{mischief.id} came down?"
            ),
            answer=(
                f"The {hat.label} was drenched in {mischief.id} and dripped for "
                f"three days. It became a costly, hard-to-clean mess, and "
                f"{hero.id} never got it clean again."
            ),
        ),
        QAItem(
            question=(
                f"Why did the {f['chickens'].label}, the {f['dog'].label}, and "
                f"the {advisor.type} all react after the splash?"
            ),
            answer=(
                f"The {f['chickens'].label} laughed, the {f['dog'].label} "
                f"laughed, and the {advisor.type} gave a long, slow, "
                f"disappointed sigh. They had all seen the sign too, and "
                f"they knew what the splash would do."
            ),
        ),
    ]
    if f.get("chorus"):
        qa.append(QAItem(
            question=(
                f"What did the other {f['burros'].label} say to {hero.id} at "
                f"the end of the story, and did {sub} learn a lesson?"
            ),
            answer=(
                f"The other {f['burros'].label} gathered around and said, "
                f'"{hero.id}, we told you about the sign." {hero.id} had '
                f"nothing to say at all, because the lesson was missed, and "
                f"the {mischief.id} was not coming off. The ending is a bad "
                f"one -- that is the joke of the story."
            ),
        ))
    qa.append(QAItem(
        question=(
            f"What kind of ending does the {hero.id} story have, and why is "
            f"it funny?"
        ),
        answer=(
            f"It has a bad ending, on purpose. {hero.id} ends up dripping with "
            f"{mischief.id}, with a ruined {hat.label}, and without a lesson "
            f"learned, and that is exactly what makes the comedy work."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = {"burro", "magenta", "sign", "goose", "mud", "hat", "barrel",
            "bad_ending", "comedy"}
    if f.get("advisor") and f["advisor"].type in ("goose", "dog", "rooster"):
        tags.add(f["advisor"].type)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
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
        if e.already_magenta:
            bits.append("already_magenta=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  outcome: {world.outcome}  (comedy contract: always 'bad')")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="magenta_farm",
        mischief="magenta_mud",
        obj="hat",
        name="Mister",
        advisor="goose",
    ),
    StoryParams(
        place="rose_ranch",
        mischief="pink_paint",
        obj="blanket",
        name="Nibs",
        advisor="dog",
    ),
    StoryParams(
        place="tangerine_track",
        mischief="tangerine_juice",
        obj="saddle",
        name="Pedro",
        advisor="rooster",
    ),
]


def explain_rejection(_mischief: Mischief, _obj: Object) -> str:
    # This world accepts every (mischief, object) combination -- the bad ending
    # is the style, not a constraint.  Still, surface a clear message for the
    # case where future refactors introduce one.
    return "(No story: an internal check on this world rejected the choice. Try another.)"


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# The rules are inline below; the facts are generated from the registries
# above so the two cannot drift.  Uses the shared ``asp`` helper + clingo,
# imported lazily so the prose engine still runs without clingo installed.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Every (setting, mischief, object) triple is reasonable here -- the bad
% ending is the style of every story, not a constraint.  We still model the
% elements as facts so the clingo twin is a real counterpart of the Python
% world, and the genre contract can be queried (outcome=bad for every combo).
ok_setting(S)         :- setting(S).
ok_mischief(M)        :- mischief(M).
ok_object(O)          :- object(O).
valid(S, M, O)        :- ok_setting(S), ok_mischief(M), ok_object(O).
always_bad_ending(S, M, O) :- valid(S, M, O).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for mid in MISCHIEFS:
        lines.append(asp.fact("mischief", mid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for adv in ADVISORS:
        lines.append(asp.fact("advisor", adv))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (setting, mischief, object) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_bad_endings() -> list[tuple]:
    """Every valid combo is also a bad-ending combo (the genre contract)."""
    import asp
    model = asp.one_model(asp_program("#show always_bad_ending/3."))
    return sorted(set(asp.atoms(model, "always_bad_ending")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        # And: every combo is also flagged as a bad ending (genre contract).
        bad_set = set(asp_bad_endings())
        if bad_set == python_set:
            print(f"OK: clingo gate matches valid_combos() "
                  f"({len(clingo_set)} combos); genre=bad_ending holds for all.")
            return 0
        print("MISMATCH: clingo bad-ending set != valid_combos():")
        if bad_set - python_set:
            print("  only flagged bad in clingo:", sorted(bad_set - python_set))
        if python_set - bad_set:
            print("  missing from clingo bad-ending:", sorted(python_set - bad_set))
        return 1
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md).
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a stubborn burro, a magenta mud, a "
                    "bad comedic ending. Unspecified choices are picked at "
                    "random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mischief", choices=MISCHIEFS)
    ap.add_argument("--obj", choices=OBJECTS)
    ap.add_argument("--advisor", choices=ADVISORS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in unspecified choices at random.  The bad ending is the style --
    it is *not* a user-settable option, so there is no StoryError for it."""
    if getattr(args, "mischief", None) and getattr(args, "obj", None):
        mischief, obj = _safe_lookup(MISCHIEFS, getattr(args, "mischief", None)), _safe_lookup(OBJECTS, getattr(args, "obj", None))
        if not (mischief and obj):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mischief", None) is None or c[1] == getattr(args, "mischief", None))
              and (getattr(args, "obj", None) is None or c[2] == getattr(args, "obj", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, mischief, obj = rng.choice(list(combos))
    advisor = getattr(args, "advisor", None) or rng.choice(sorted(ADVISORS))
    name = getattr(args, "name", None) or rng.choice(DONKEY_NAMES)
    return StoryParams(
        place=place,
        mischief=mischief,
        obj=obj,
        name=name,
        advisor=advisor,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MISCHIEFS, params.mischief),
                 _safe_lookup(OBJECTS, params.obj), params.name, params.advisor)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, mischief, object) combos "
              f"(genre contract: every one ends badly on purpose):\n")
        for place, mischief, obj in triples:
            print(f"  {place:14} {mischief:18} {obj:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mischief} at {p.place} (obj: {p.obj})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
