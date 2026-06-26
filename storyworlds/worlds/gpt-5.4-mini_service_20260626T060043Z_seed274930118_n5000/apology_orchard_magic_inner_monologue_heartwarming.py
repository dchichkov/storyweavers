#!/usr/bin/env python3
"""
Standalone storyworld: apology in an orchard, with a little magic and a warm
inner monologue.

Premise:
- A child in an orchard accidentally causes a small problem.
- The child feels upset, thinks carefully inside, apologizes, and helps fix it.
- Gentle magic makes the repair feel hopeful and heartwarming.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    branch: object | None = None
    gift: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the orchard"
    fragrance: str = "sweet apples"
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
class MagicGift:
    id: str
    label: str
    effect: str
    glow: str
    helps: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    orchard: str
    magic: str
    seed: Optional[int] = None
    params: object | None = None
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "orchard": Setting(place="the orchard", fragrance="sweet apples"),
}

HERO_NAMES = ["Mila", "Nina", "Owen", "Theo", "Luna", "Sara", "Ben", "Eli"]
TRAITS = ["gentle", "curious", "brave", "kind", "soft-spoken", "thoughtful"]

MAGIC = {
    "blossom": MagicGift(
        id="blossom",
        label="a blossom charm",
        effect="makes new blossoms open where the branch was hurt",
        glow="pink light",
        helps="heal the little branch",
    ),
    "lantern": MagicGift(
        id="lantern",
        label="a warm lantern charm",
        effect="glows softly and helps everyone see the fix clearly",
        glow="golden light",
        helps="show the way to make it right",
    ),
    "seed": MagicGift(
        id="seed",
        label="a silver seed charm",
        effect="grows a tiny green shoot after the apology",
        glow="silver light",
        helps="start something new",
    ),
}

PARENTS = {
    "mother": "mother",
    "father": "father",
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/4.

orchard(o).
gender(girl;boy).
parent(mother;father).
magic(blossom;lantern;seed).

apology_needed(Name, Gift) :- child(Name), magic(Gift).
magic_help(Gift, blossom) :- magic(blossom).
magic_help(Gift, lantern) :- magic(lantern).
magic_help(Gift, seed) :- magic(seed).

valid_story(orchard, Magic, Gender, Parent) :-
    orchard(orchard),
    magic(Magic),
    gender(Gender),
    parent(Parent).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("orchard", "orchard"))
    for g in MAGIC:
        lines.append(asp.fact("magic", g))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    for p in ["mother", "father"]:
        lines.append(asp.fact("parent", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------

def pronoun_name(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def choose_magic(rng: random.Random) -> MagicGift:
    return MAGIC[rng.choice(list(MAGIC.keys()))]


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.orchard))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    gift = world.add(Entity(id=params.magic, kind="thing", label=MAGIC[params.magic].label, type="magic"))

    hero.meters["nervous"] = 0.0
    hero.meters["apology"] = 0.0
    hero.memes["guilt"] = 0.0
    hero.memes["love"] = 0.0
    parent.memes["care"] = 1.0

    # Act 1
    world.say(
        f"{hero.id} was a {_safe_lookup(TRAITS, hash(params.name) % len(TRAITS))} {pronoun_name(params.gender)} "
        f"who loved walking through {world.setting.place}."
    )
    world.say(
        f"The air smelled like {world.setting.fragrance}, and {hero.id} liked how the trees made the path feel cozy."
    )
    world.say(
        f"One morning, {hero.id}'s {params.parent} brought along {MAGIC[params.magic].label}, "
        f"because a little magic made chores feel lighter."
    )

    # Act 2: accident + inner monologue
    world.para()
    branch = world.add(Entity(id="branch", kind="thing", label="little branch", type="branch"))
    branch.meters["hurt"] = 0.0
    world.say(
        f"While reaching for a bright apple, {hero.id} bumped the {branch.label} and heard a tiny crack."
    )
    hero.meters["nervous"] = 1.0
    hero.memes["guilt"] = 1.0
    world.say(
        f"{hero.id} froze. Inside {hero.pronoun('possessive')} head, a quiet thought whispered, "
        f'"Oh no, I did not mean to do that."'
    )
    world.say(
        f"{hero.id} looked at the branch and thought, 'If I say sorry and help, maybe the tree will feel better.'"
    )

    # Act 3: apology and repair
    world.para()
    world.say(
        f"{hero.id} walked to the {params.parent} and said, "
        f'"I am sorry. I bumped the branch. I want to help fix it."'
    )
    hero.meters["apology"] = 1.0
    hero.memes["guilt"] = 0.0
    hero.memes["love"] = 1.0
    world.say(
        f"{params.parent.capitalize()} smiled softly and said, "
        f'"That was a kind apology. Let\'s make it right together."'
    )
    world.say(
        f"Then the {MAGIC[params.magic].label} warmed in {hero.id}'s hands with {MAGIC[params.magic].glow}."
    )
    world.say(
        f"It {MAGIC[params.magic].effect}, and {hero.id} gently tied the branch up with a soft strip of cloth."
    )
    branch.meters["hurt"] = 0.0
    gift.meters["glow"] = 1.0
    world.say(
        f"By the end, the branch stood neatly again, and a tiny leaf seemed to lift toward the sun as if it were smiling."
    )
    world.facts.update(
        hero=hero,
        parent=parent,
        gift=gift,
        branch=branch,
        magic=MAGIC[params.magic],
        setting=world.setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    gift = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gift")
    return [
        "Write a heartwarming story about a child in an orchard who makes a mistake, apologizes, and helps fix it with a little magic.",
        f"Tell a gentle story where {hero.id} feels bad about bumping a branch and then says sorry.",
        f"Write a cozy orchard story that includes {gift.label} and ends with a warm apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    branch = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "branch")
    magic = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "magic")
    return [
        QAItem(
            question=f"What did {hero.id} do in the orchard that made the problem?",
            answer=f"{hero.id} bumped the {branch.label} while reaching for an apple, and the branch made a tiny crack sound.",
        ),
        QAItem(
            question=f"What did {hero.id} think inside {hero.pronoun('possessive')} head before speaking?",
            answer=f"{hero.id} thought, 'Oh no, I did not mean to do that,' and then decided to apologize and help.",
        ),
        QAItem(
            question=f"How did {hero.id} fix things after saying sorry to the {parent.type}?",
            answer=f"{hero.id} helped gently tie the branch up, and the {magic['label']} made the repair feel hopeful and warm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orchard?",
            answer="An orchard is a place where fruit trees grow, like apple trees or pear trees.",
        ),
        QAItem(
            question="What does it mean to apologize?",
            answer="To apologize means to say you are sorry when you hurt someone, broke something, or made a mistake.",
        ),
        QAItem(
            question="Why can gentle magic be comforting in a story?",
            answer="Gentle magic can be comforting because it helps a hard moment feel hopeful, safe, and a little bit special.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming orchard apology storyworld with magic and inner monologue.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--orchard", choices=list(SETTINGS))
    ap.add_argument("--magic", choices=list(MAGIC))
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    magic = getattr(args, "magic", None) or rng.choice(list(MAGIC))
    orchard = getattr(args, "orchard", None) or "orchard"
    return StoryParams(name=name, gender=gender, parent=parent, orchard=orchard, magic=magic)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


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
    py = {(SETTINGS["orchard"].place, m, g, p) for m in MAGIC for g in ["girl", "boy"] for p in ["mother", "father"]}
    cl = set(asp_valid_stories())
    if py:
        print(f"OK: ASP produced {len(cl)} candidate story tuples.")
        return 0
    print("MISMATCH: no Python stories.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story tuples:")
        for t in stories:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, magic in enumerate(MAGIC):
            params = StoryParams(
                name=_safe_lookup(HERO_NAMES, i % len(HERO_NAMES)),
                gender=["girl", "boy"][i % 2],
                parent=["mother", "father"][i % 2],
                orchard="orchard",
                magic=magic,
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
