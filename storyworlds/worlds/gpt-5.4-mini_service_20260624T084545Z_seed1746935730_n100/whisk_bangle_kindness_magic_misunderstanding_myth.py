#!/usr/bin/env python3
"""
A small myth-style storyworld about a child, a whisk, a bangle, and a kind
misunderstanding that turns magical.

The source tale behind this world:
A little helper in a village finds a silver bangle in a shrine and thinks it was
left as a warning. The child uses a whisk to stir moon-soup for the temple
keepers, but the bangle begins to glow when the child is kind to a worried old
goat and shares the last sweet berry. The elders explain that the bangle was not
a threat at all: it was a blessing meant to wake when someone chose kindness.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    goat: object | None = None
    hero: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        for k in ["glow", "dust", "full", "safe", "tired"]:
            self.meters.setdefault(k, 0.0)
        for k in ["kindness", "magic", "misunderstanding", "fear", "relief", "curiosity", "hope"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    sacred: bool = False
    affords: set[str] = field(default_factory=set)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    helper: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Charm:
    id: str
    label: str
    phrase: str
    worn_on: str
    glows_for: set[str] = field(default_factory=set)
    omen: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_bangle_glow(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        for thing in list(world.entities.values()):
            if thing.worn_by != e.id:
                continue
            if thing.id == "bangle" and e.memes["kindness"] >= THRESHOLD and thing.meters["glow"] < THRESHOLD:
                sig = ("glow", e.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                thing.meters["glow"] = 1.0
                e.memes["magic"] += 1
                out.append(f"The silver bangle grew warm on {e.id}'s wrist.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["misunderstanding"] >= THRESHOLD and e.memes["kindness"] >= THRESHOLD:
            sig = ("relief", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["relief"] += 1
            e.memes["misunderstanding"] = 0.0
            out.append(f"At last, {e.id}'s worry loosened like a knot in wet cloth.")
    return out


CAUSAL_RULES = [Rule("bangle_glow", _r_bangle_glow), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_bangle(world: World, actor: Entity) -> bool:
    sim = world.copy()
    sim.get(actor.id).memes["kindness"] += 1
    propagate(sim, narrate=False)
    return sim.get("bangle").meters["glow"] >= THRESHOLD


SETTINGS = {
    "temple": Setting(place="the moon temple", sacred=True, affords={"stir", "bring", "share"}),
    "well": Setting(place="the old moonwell", sacred=True, affords={"stir", "bring", "share"}),
    "village": Setting(place="the hill village", sacred=False, affords={"stir", "bring", "share"}),
}

TOOLS = {
    "whisk": Tool(
        id="whisk",
        label="whisk",
        phrase="a small bright whisk",
        action="stir the moon-soup",
        helper=True,
    ),
}

CHARMS = {
    "bangle": Charm(
        id="bangle",
        label="bangle",
        phrase="a silver bangle with tiny stars",
        worn_on="wrist",
        glows_for={"kindness"},
        omen="a blessing for a gentle hand",
    ),
}


@dataclass
class StoryParams:
    setting: str
    name: str
    age_word: str
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


NAMES = ["Mira", "Nia", "Luma", "Tavi", "Sela", "Arin", "Pia", "Kiri"]
AGE_WORDS = ["little", "young", "small", "bright-eyed"]


def mythic_opening(world: World, hero: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} was known as a {hero.memes.get('age_word', 'little')} helper "
        f"who listened carefully to elders and bells."
    )


def describe_charm(world: World, hero: Entity, charm: Entity) -> None:
    hero.memes["curiosity"] += 1
    charm.worn_by = hero.id
    world.say(
        f"One morning, {hero.id} found {charm.phrase} resting in the shrine grass."
    )
    world.say(
        f"{hero.id} thought the bangle might be an omen, so {hero.pronoun('subject')} held it very still."
    )


def use_whisk(world: World, hero: Entity, tool: Entity) -> None:
    hero.meters["tired"] += 1
    world.say(
        f"Then {hero.id} took up {tool.phrase} and used it to {tool.action} for the temple keepers."
    )
    world.say(
        f"The soup swirled pale and foamy, and the whisk sang softly against the bowl."
    )


def misunderstanding(world: World, hero: Entity) -> None:
    hero.memes["misunderstanding"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"When the bangle gave off a small flash, {hero.id} stepped back, thinking the old shrine was warning {hero.pronoun('object')} away."
    )


def kindness_turn(world: World, hero: Entity, goat: Entity) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f"Near the gate, a worried goat was stuck beside a thorny vine, and {hero.id} knelt to help without being asked."
    )
    world.say(
        f"{hero.id} brushed the vine aside, shared the last sweet berry, and let the goat drink first from the cup."
    )
    goat.meters["safe"] = 1.0
    propagate(world, narrate=True)


def ending(world: World, hero: Entity, charm: Entity) -> None:
    if charm.meters["glow"] >= THRESHOLD:
        world.say(
            f"The bangle shimmered like a tiny moon, and the elders smiled, because it had been a blessing all along."
        )
        world.say(
            f"{hero.id} laughed then, knowing the shrine had not sent a warning at all; it had answered {hero.pronoun('possessive')} kindness."
        )
    else:
        world.say(f"{hero.id} went on with a gentle heart, and the quiet shrine seemed less lonely than before.")


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.name, kind="character", type="girl"))
    hero.memes["age_word"] = 1.0
    hero.memes["kindness"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["misunderstanding"] = 0.0
    hero.memes["age_word"] = params.age_word

    goat = world.add(Entity(id="goat", kind="character", type="thing"))
    tool = world.add(Entity(id="whisk", type="tool", label="whisk", phrase=TOOLS["whisk"].phrase))
    charm = world.add(Entity(id="bangle", type="charm", label="bangle", phrase=CHARMS["bangle"].phrase))

    mythic_opening(world, hero)
    world.say(f"{hero.id} loved the old stories of moonlight, helpers, and gifts that chose the right heart.")
    world.para()
    describe_charm(world, hero, charm)
    use_whisk(world, hero, tool)
    misunderstanding(world, hero)
    world.para()
    kindness_turn(world, hero, goat)
    world.para()
    ending(world, hero, charm)

    world.facts.update(hero=hero, goat=goat, tool=tool, charm=charm, setting=world.setting)
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short myth for a small child about {hero.id}, a whisk, and a silver bangle.',
        f"Tell a gentle story where {hero.id} thinks a bangle is an omen, but kindness changes the meaning.",
        f"Create a simple mythic tale that includes a whisk, a bangle, magic, and a misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    return [
        QAItem(
            question=f"What did {hero.id} use to stir the moon-soup?",
            answer="The child used a small bright whisk to stir the moon-soup for the temple keepers.",
        ),
        QAItem(
            question=f"Why did {hero.id} think the bangle was a warning at first?",
            answer="The child saw the bangle flash and misunderstood it, so the child thought the shrine was warning them away.",
        ),
        QAItem(
            question=f"What changed the meaning of the bangle in the end?",
            answer="Kindness changed everything: when the child helped the worried goat and shared the last sweet berry, the bangle began to glow with magic.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whisk for?",
            answer="A whisk is a tool with thin wires that helps stir food, beat eggs, or mix things smoothly.",
        ),
        QAItem(
            question="What is a bangle?",
            answer="A bangle is a bracelet, usually a hard ring worn around the wrist.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, share, and be gentle with someone or something.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What is magic in a myth?",
            answer="In a myth, magic is a special power or wonder that makes something amazing happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v and not isinstance(v, str)}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% If the child is kind, the bangle can glow.
glows(bangle) :- kind(hero), bangle_item(bangle).

% A misunderstanding resolves when kindness and magic meet.
resolved(hero) :- kind(hero), glows(bangle).

#show glows/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.sacred:
            lines.append(asp.fact("sacred", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    lines.append(asp.fact("tool", "whisk"))
    lines.append(asp.fact("bangle_item", "bangle"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("kind", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show glows/1.\n#show resolved/1."))
    atoms = {f"{sym.name}({','.join(str(a) for a in sym.arguments)})" for sym in model}
    expected = {"glows(bangle)", "resolved(hero)"}
    if atoms == expected:
        print("OK: ASP gate matches the Python reasonableness story.")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("  asp:", sorted(atoms))
    print("  py :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of a whisk, a bangle, kindness, magic, and misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--age-word", choices=AGE_WORDS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, n, a) for s in SETTINGS for n in NAMES for a in AGE_WORDS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    age_word = getattr(args, "age_word", None) or rng.choice(AGE_WORDS)
    return StoryParams(setting=setting, name=name, age_word=age_word)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
    StoryParams(setting="temple", name="Mira", age_word="little"),
    StoryParams(setting="well", name="Luma", age_word="young"),
    StoryParams(setting="village", name="Tavi", age_word="bright-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show glows/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show glows/1.\n#show resolved/1."))
        print(" ".join(f"{sym.name}({','.join(str(a) for a in sym.arguments)})" for sym in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
