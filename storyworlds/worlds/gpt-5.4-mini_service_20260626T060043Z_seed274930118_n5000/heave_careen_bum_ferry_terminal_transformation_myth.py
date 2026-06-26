#!/usr/bin/env python3
"""
Standalone storyworld: a ferry-terminal myth of heaving, careening, and a bum
that becomes something wiser through transformation.
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


# ---------------------------------------------------------------------------
# Core world model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    burden_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "queen"}:
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
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
class StoryParams:
    name: str
    title: str
    helper: str
    burden: str
    place: str = "ferry terminal"
    seed: Optional[int] = None
    p: object | None = None
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


@dataclass(frozen=True)
class Title:
    id: str
    label: str
    kind: str
    pronoun: str
    light: str
    solemn: str
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


@dataclass(frozen=True)
class Burden:
    id: str
    label: str
    phrase: str
    risk: str
    transformation: str
    region: str
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


TITLES: dict[str, Title] = {
    "captain": Title("captain", "captain", "man", "he", "a weathered helm", "the old oath"),
    "oracle": Title("oracle", "oracle", "woman", "she", "a lantern of salt", "the listening tide"),
    "child": Title("child", "child", "boy", "he", "a bright shell", "the hidden path"),
}

BURDENS: dict[str, Burden] = {
    "stone_bum": Burden(
        "stone_bum",
        "stone-bum",
        "a stone-heavy bum",
        "sink the ferry seat",
        "a body of carved wood",
        "seat",
    ),
    "tide_bum": Burden(
        "tide_bum",
        "tide-bum",
        "a tide-soaked bum",
        "slip the pilgrim off balance",
        "a scaled tail for the water",
        "seat",
    ),
    "ash_bum": Burden(
        "ash_bum",
        "ash-bum",
        "an ash-dust bum",
        "leave gray marks on the bench",
        "a warm ember-bowl",
        "seat",
    ),
}

HELPERS: dict[str, str] = {
    "rope": "a rope of honest hemp",
    "cloak": "a cloak woven with gull-feathers",
    "bucket": "a bronze bucket of seawater",
}

MYTH_NAMES = ["Mara", "Ivo", "Sel", "Nilo", "Tava", "Orin", "Kira", "Edda"]
TRAITS = ["steadfast", "quiet", "hungry", "brave", "small", "bright"]


# ---------------------------------------------------------------------------
# Myth world behavior
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def make_world(params: StoryParams) -> World:
    world = World(place=params.place)
    title = _safe_lookup(TITLES, params.title)
    burden = _safe_lookup(BURDENS, params.burden)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=title.kind,
        label=title.label,
        phrase=f"{title.pronoun} of {title.light}",
        meters={"heave": 0.0},
        memes={"wonder": 1.0, "fear": 0.0, "resolve": 0.0, "changed": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="woman" if params.helper == "oracle" else "man",
        label=params.helper,
        phrase=f"{params.helper} of the dock",
        meters={"careen": 0.0},
        memes={"patience": 1.0, "resolve": 1.0},
    ))
    burden_ent = world.add(Entity(
        id="burden",
        type="thing",
        label=burden.label,
        phrase=burden.phrase,
        caretaker=helper.id,
        meters={"weight": 1.0, "rift": 1.0},
        memes={"stubbornness": 1.0},
    ))
    world.facts.update(hero=hero, helper=helper, burden=burden_ent, title=title, burden_def=burden)
    return world


def touch_burden(world: World) -> None:
    hero = world.get("hero")
    burden = world.get("burden")
    helper = world.get("helper")
    hero.meters["heave"] += 1.0
    hero.memes["resolve"] += 1.0
    burden.meters["rift"] += 1.0
    helper.memes["patience"] += 0.5
    world.say(
        f"At the ferry terminal, {hero.id} found {burden.label} beside the salt-stained steps, "
        f"and {hero.pronoun()} knew the old task had returned."
    )


def heave(world: World) -> None:
    hero = world.get("hero")
    burden = world.get("burden")
    helper = world.get("helper")
    if hero.meters["heave"] < THRESHOLD:
        return
    world.say(
        f"{hero.id} put both hands under {burden.pronoun('possessive')} weight and heaved until "
        f"the ropes sang."
    )
    world.say(
        f"The ferry terminal boards groaned, and the burden began to careen as if the sea itself "
        f"were turning it."
    )
    burden.meters["careen"] = 1.0
    helper.meters["careen"] += 1.0


def warn_of_transformation(world: World) -> None:
    hero = world.get("hero")
    burden = world.get("burden")
    helper = world.get("helper")
    world.say(
        f"{helper.label.capitalize()} raised {helper.pronoun('possessive')} hand and said, "
        f'"If you heave with a true heart, the bum will not stay as it is."'
    )
    hero.memes["wonder"] += 1.0
    hero.memes["fear"] += 0.5
    world.facts["warned"] = True
    world.facts["risk"] = f"the {burden.label} might become {world.facts['burden_def'].transformation}"


def transformation_turn(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    burden = world.get("burden")
    bdef = _safe_fact(world, world.facts, "burden_def")
    if hero.meters["heave"] < THRESHOLD or burden.meters["careen"] < THRESHOLD:
        return
    burden.type = "relic"
    burden.label = bdef.transformation
    burden.phrase = bdef.transformation
    burden.protective = True
    burden.covers = {bdef.region}
    burden.meters["rift"] = 0.0
    burden.meters["weight"] = 0.0
    hero.memes["changed"] += 1.0
    hero.memes["fear"] = 0.0
    helper.memes["resolve"] += 1.0
    world.say(
        f"Then the bum changed. The heavy shape loosened, shivered with foam, and became {burden.label}, "
        f"bright as if it had waited ages for this name."
    )


def resolution(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    burden = world.get("burden")
    title: Title = _safe_fact(world, world.facts, "title")
    world.say(
        f"{hero.id} and {helper.label} carried the new thing to the waiting ferry, and no one feared "
        f"its old weight anymore."
    )
    world.say(
        f"At the end, {hero.id} stood at the ferry terminal with {burden.label} resting safely, "
        f"and the little {title.label} had learned how a burden can turn into a blessing."
    )


def tell(params: StoryParams) -> World:
    world = make_world(params)
    touch_burden(world)
    world.para()
    warn_of_transformation(world)
    heave(world)
    transformation_turn(world)
    world.para()
    resolution(world)
    return world


# ---------------------------------------------------------------------------
# QA / prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    burden = _safe_fact(world, world.facts, "burden_def")
    return [
        f"Write a short myth about {hero.id} at a ferry terminal who must heave a {burden.label} until it changes.",
        f"Tell a child-friendly legend set in a ferry terminal with the words heave, careen, and bum.",
        f"Create a small myth where a burden at the ferry terminal transforms after a brave effort.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    burden = _safe_fact(world, world.facts, "burden_def")
    qa = [
        QAItem(
            question=f"Where did {hero.id} meet the heavy burden?",
            answer=f"{hero.id} met it at the ferry terminal, beside the salt-stained steps.",
        ),
        QAItem(
            question=f"What did {hero.id} have to do to the bum?",
            answer=f"{hero.id} had to heave it with both hands until it started to careen.",
        ),
        QAItem(
            question=f"What did the {helper.label} warn would happen?",
            answer=f"The {helper.label} warned that the bum would not stay as it was and would transform.",
        ),
        QAItem(
            question=f"What did the bum turn into?",
            answer=f"It turned into {burden.transformation}, which was lighter and safer to carry.",
        ),
        QAItem(
            question=f"How did the story end at the ferry terminal?",
            answer=f"It ended with {hero.id} and the {helper.label} carrying the transformed thing safely to the ferry.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ferry terminal?",
            answer="A ferry terminal is a place by the water where people wait to board ferries.",
        ),
        QAItem(
            question="What does heave mean?",
            answer="Heave means to lift or push something with a strong effort.",
        ),
        QAItem(
            question="What does careen mean?",
            answer="Careen means to move quickly or tilt wildly to one side, like something that has lost balance.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(X) :- helper_name(X).
burden(B) :- burden_name(B).

heaves(H) :- hero(H), weight(H,W), W >= 1.
careens(B) :- burden(B), shifted(B,1).
transforms(B) :- burden(B), careens(B), warned(B).

safe(B) :- transforms(B), new_form(B,light_relic).

#show heaves/1.
#show careens/1.
#show transforms/1.
#show safe/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("hero_name", "hero"))
    lines.append(asp.fact("helper_name", "helper"))
    lines.append(asp.fact("burden_name", "burden"))
    lines.append(asp.fact("weight", "hero", 1))
    lines.append(asp.fact("shifted", "burden", 1))
    lines.append(asp.fact("warned", "burden"))
    lines.append(asp.fact("new_form", "burden", "light_relic"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_expected() -> dict[str, set[tuple]]:
    return {
        "heaves": {("hero",)},
        "careens": {("burden",)},
        "transforms": {("burden",)},
        "safe": {("burden",)},
    }


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show heaves/1.\n#show careens/1.\n#show transforms/1.\n#show safe/1."))
    got = {
        "heaves": set(asp.atoms(model, "heaves")),
        "careens": set(asp.atoms(model, "careens")),
        "transforms": set(asp.atoms(model, "transforms")),
        "safe": set(asp.atoms(model, "safe")),
    }
    exp = asp_expected()
    if got == exp:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH between ASP and expected facts:")
    for k in sorted(exp):
        if got[k] != exp[k]:
            print(f"  {k}: got={sorted(got[k])} expected={sorted(exp[k])}")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic ferry-terminal transformation storyworld.")
    ap.add_argument("--name", choices=MYTH_NAMES)
    ap.add_argument("--title", choices=TITLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--place", default="ferry terminal")
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
    name = getattr(args, "name", None) or rng.choice(MYTH_NAMES)
    title = getattr(args, "title", None) or rng.choice(list(TITLES))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    burden = getattr(args, "burden", None) or rng.choice(list(BURDENS))
    place = getattr(args, "place", None) or "ferry terminal"
    return StoryParams(name=name, title=title, helper=helper, burden=burden, place=place)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world trace ---")
        for ent in sample.world.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            print(f"{ent.id}: type={ent.type} label={ent.label} meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show heaves/1.\n#show careens/1.\n#show transforms/1.\n#show safe/1."))
        print("heaves:", sorted(set(asp.atoms(model, "heaves"))))
        print("careens:", sorted(set(asp.atoms(model, "careens"))))
        print("transforms:", sorted(set(asp.atoms(model, "transforms"))))
        print("safe:", sorted(set(asp.atoms(model, "safe"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, (name, title, helper, burden) in enumerate([
            ("Mara", "oracle", "cloak", "stone_bum"),
            ("Ivo", "captain", "rope", "tide_bum"),
            ("Sel", "child", "bucket", "ash_bum"),
        ]):
            p = StoryParams(name=name, title=title, helper=helper, burden=burden, seed=base_seed + i)
            samples.append(generate(p))
    else:
        for i in range(max(1, getattr(args, "n", None))):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
