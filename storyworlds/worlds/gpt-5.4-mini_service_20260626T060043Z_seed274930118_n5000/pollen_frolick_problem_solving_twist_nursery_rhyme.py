#!/usr/bin/env python3
"""
A small storyworld about pollen, frolicking, and a nursery-rhyme style problem
solving twist.

Seed tale shape:
- A child and a friend frolick in a flower field.
- Pollen makes the child sneeze and upset their plans.
- They solve the problem by using a scarf, turning the trouble into a game.
- A small twist: the scarf also helps them notice the bees, leading to a kinder
  ending where they share the flowers without stirring so much pollen.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    aid: object | None = None
    bee: object | None = None
    friend: object | None = None
    hero: object | None = None
    pollen: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
    place: str
    outdoors: bool = True
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    effect: str
    keyword: str
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
class Aid:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    prep: str
    twist: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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


def _r_sneeze(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("pollen", 0) < THRESHOLD:
            continue
        sig = ("sneeze", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fluster"] = ent.memes.get("fluster", 0) + 1
        out.append(f"{ent.id} sneezed and blinked at the bright, floaty air.")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    for aid in list(world.entities.values()):
        if aid.kind != "aid":
            continue
        if hero.meters.get("pollen", 0) < THRESHOLD:
            continue
        if "pollen" not in aid.helps:
            continue
        sig = ("help", aid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["pollen"] = 0
        hero.memes["calm"] = hero.memes.get("calm", 0) + 1
        out.append(f"{aid.label.capitalize()} made the sneezes settle down.")
    return out


def _r_twist(world: World) -> list[str]:
    hero = world.get("hero")
    bee = world.get("bee")
    if hero.memes.get("calm", 0) < THRESHOLD:
        return []
    sig = ("twist",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bee.memes["friendly"] = bee.memes.get("friendly", 0) + 1
    return ["__twist__"]


CAUSAL_RULES = [_r_sneeze, _r_help, _r_twist]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(s for s in sents if s != "__twist__")
    if narrate:
        for s in out:
            world.say(s)
    return out


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("causes", aid, a.effect))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for hid, h in AIDS.items():
        lines.append(asp.fact("aid", hid))
        for x in sorted(h.helps):
            lines.append(asp.fact("helps", hid, x))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", hid, c))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A) :- affords(S, A), tag(A, pollen).
good_aid(Aid, A) :- helps(Aid, pollen), activity(A).
twist(H) :- valid(_, A), good_aid(_, A), tag(A, frolick).
#show valid/2.
#show twist/1.
"""


@dataclass
class StoryParams:
    place: str
    activity: str
    aid: str
    name: str
    gender: str
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


SETTINGS = {
    "meadow": Setting(place="the meadow", outdoors=True, affords={"frolick"}),
    "orchard": Setting(place="the orchard", outdoors=True, affords={"frolick"}),
    "garden": Setting(place="the garden", outdoors=True, affords={"frolick"}),
}

ACTIVITIES = {
    "frolick": Activity(
        id="frolick",
        verb="frolick among the flowers",
        gerund="frolicking among the flowers",
        rush="skip through the blooms",
        effect="pollen",
        keyword="pollen",
        tags={"pollen", "frolick"},
    ),
}

AIDS = {
    "scarf": Aid(
        id="scarf",
        label="a soft scarf",
        helps={"pollen"},
        covers={"nose", "mouth"},
        prep="wrap the scarf around a little nose",
        twist="noticed the bees before they buzzed too near",
    )
}

GIRL_NAMES = ["Mina", "Luna", "Poppy", "Tia", "Nora"]
BOY_NAMES = ["Finn", "Otto", "Milo", "Jasper", "Theo"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            combos.append((place, act))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pollen and frolicking in a nursery-rhyme style tale.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if getattr(args, "activity", None) and getattr(args, "activity", None) != "frolick":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    aid = getattr(args, "aid", None) or "scarf"
    return StoryParams(place=place, activity=activity, aid=aid, name=name, gender=gender)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    friend = world.add(Entity(id="friend", kind="character", type="child", label="the little friend"))
    bee = world.add(Entity(id="bee", kind="character", type="bee", label="the bee"))
    pollen = world.add(Entity(id="pollen", type="pollen", label="pollen"))
    aid = world.add(Entity(id="aid", kind="aid", type="aid", label=_safe_lookup(AIDS, params.aid).label))

    world.facts.update(hero=hero, friend=friend, bee=bee, pollen=pollen, aid=aid,
                       setting=world.setting, activity=_safe_lookup(ACTIVITIES, params.activity))

    world.say(f"Little {hero.label} and the little friend went to {world.setting.place}.")
    world.say(f"They loved to {_safe_lookup(ACTIVITIES, params.activity).gerund}, and the day was bright as a bell.")
    world.say("The flowers waved like tiny faces, and the air smelled sweet and warm.")

    world.para()
    hero.meters["pollen"] = 1
    friend.meters["pollen"] = 0
    world.say(f"But pollen drifted up and tickled {hero.label}'s nose.")
    world.say(f"{hero.label} tried to {_safe_lookup(ACTIVITIES, params.activity).rush}, yet a sneeze went \"ah-choo!\"")
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then the little friend said, \"Let's use {aid.label} and make a game of it.\"")
    world.say(f"They did just that: {_safe_lookup(AIDS, params.aid).prep}, and the sneezes grew small.")
    aid.meters["pollen"] = 0
    propagate(world, narrate=True)

    world.para()
    world.say(f"Twist and turn, the bee buzzed near and did not mind at all.")
    world.say(f"Because the scarf kept the pollen down, {hero.label} could {_safe_lookup(ACTIVITIES, params.activity).gerund} again.")
    world.say(f"And the bee led them to a patch of flowers with less fluff and more sunny laughter.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    act = _safe_fact(world, world.facts, "activity")
    return [
        f'Write a nursery-rhyme style story about pollen and a child named {hero.label} who wants to {act.verb}.',
        f"Tell a short problem-solving story where {hero.label} meets pollen trouble, then finds a gentle fix.",
        f'Write a rhyme-like tale that includes "{act.keyword}" and ends with a small twist involving a bee.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    act = _safe_fact(world, world.facts, "activity")
    aid = _safe_fact(world, world.facts, "aid")
    return [
        QAItem(
            question=f"What did {hero.label} want to do in the meadow?",
            answer=f"{hero.label} wanted to {act.verb}, because the flowers looked like a grand game.",
        ),
        QAItem(
            question="What problem made the frolicking pause?",
            answer="Pollen floated into the air and tickled the child's nose, so the sneezes began.",
        ),
        QAItem(
            question=f"What helped solve the pollen problem?",
            answer=f"{aid.label} helped by keeping the pollen off the child's nose and mouth.",
        ),
        QAItem(
            question="What was the twist at the end?",
            answer="The bee stayed friendly and guided them to a gentler patch of flowers, so play could go on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pollen?",
            answer="Pollen is a fine yellow powder from flowers that bees often carry around.",
        ),
        QAItem(
            question="Why can pollen make someone sneeze?",
            answer="Pollen can tickle the nose and make it feel itchy, which can cause sneezing.",
        ),
        QAItem(
            question="What does a scarf do in cool weather or dusty air?",
            answer="A scarf can wrap around the neck, nose, or mouth and help keep little bits out.",
        ),
        QAItem(
            question="Why do bees visit flowers?",
            answer="Bees visit flowers to gather nectar and pollen, which helps them and helps the flowers too.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.kind:8}) meters={e.meters} memes={e.memes}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    py_asp = {(a, b) for a, b in py_set}
    if asp_set == py_asp:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_asp))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(place="meadow", activity="frolick", aid="scarf", name="Mina", gender="girl"),
    StoryParams(place="orchard", activity="frolick", aid="scarf", name="Finn", gender="boy"),
    StoryParams(place="garden", activity="frolick", aid="scarf", name="Poppy", gender="girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, act in combos:
            print(f"  {place:8} {act:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
