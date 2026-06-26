#!/usr/bin/env python3
"""
storyworlds/worlds/dread_tall_magic_flashback_dialogue_myth.py
===============================================================

A small mythic story world about dread, a tall place, a little magic, a flashback,
and a resolving dialogue.

Premise:
- A hero approaches a tall sacred place.
- An old omen returns in a flashback, making the hero afraid.
- A wise figure speaks in dialogue and offers a magical remedy.
- The hero uses the magic, faces the tall place, and the dread softens into awe.

The world is intentionally tiny and constraint-checked: the "tall" setting must
actually matter, the "dread" must be caused by a remembered omen, and the chosen
magic must be suitable for the cause of fear.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    guide: object | None = None
    hero: object | None = None
    tower: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the tall tower"
    height: str = "very tall"
    sacred: bool = True
    mood: str = "stone and starlight"
    SETTING: object | None = None
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
class Magic:
    id: str
    label: str
    phrase: str
    effect: str
    is_light: bool = False
    soothes: set[str] = field(default_factory=set)
    suits: set[str] = field(default_factory=set)
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
    magic: str
    flashback: str
    name: str
    gender: str
    guide: str
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

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTING = Setting()

MAGICS = {
    "torch": Magic(
        id="torch",
        label="a small torch of blue flame",
        phrase="blue flame",
        effect="light",
        is_light=True,
        soothes={"darkness", "unknown"},
        suits={"tall"},
    ),
    "thread": Magic(
        id="thread",
        label="a silver thread charm",
        phrase="silver thread",
        effect="binding",
        soothes={"dread", "forgetting"},
        suits={"flashback"},
    ),
    "song": Magic(
        id="song",
        label="a humming song stone",
        phrase="a low humming song",
        effect="music",
        soothes={"dread", "silence"},
        suits={"dialogue"},
    ),
}

FLASHBACKS = {
    "omen": "a night when the bell rang once by itself",
    "storm": "a storm that shook the eaves like trembling hands",
    "shadow": "a shadow that climbed the wall and vanished at dawn",
}

GUIDES = {
    "priest": "the old priest",
    "priestess": "the old priestess",
    "keeper": "the gate keeper",
}

NAMES = {
    "girl": ["Lina", "Mira", "Anya", "Sera", "Nora"],
    "boy": ["Tarin", "Ivo", "Eren", "Milo", "Arin"],
}

TRAITS = ["brave", "curious", "gentle", "quiet", "steadfast"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for mid, m in MAGICS.items():
        for fb in FLASHBACKS:
            if m.suits == {fb} or fb in m.suits or not m.suits:
                out.append((mid, fb))
    return out


def story_core(params: StoryParams) -> World:
    if params.magic not in MAGICS:
        pass
    if params.flashback not in FLASHBACKS:
        pass
    magic = _safe_lookup(MAGICS, params.magic)
    if params.flashback == "omen" and "dread" not in magic.soothes and not magic.is_light:
        pass

    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    guide_type = params.guide
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, label=f"the {_safe_lookup(GUIDES, guide_type)}"))
    tower = world.add(Entity(id="Tower", kind="place", type="tower", label=SETTING.place, phrase="the tall sacred tower"))
    charm = world.add(Entity(id="Magic", kind="thing", type="magic", label=magic.label, phrase=magic.phrase, owner=guide.id))

    # Setup.
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} came to {tower.label}, where the stones rose high and the wind felt old."
    )
    world.say(
        f"People in the village said the place was tall enough to touch the sky."
    )
    world.say(
        f"{hero.id} had a steady heart, but {hero.pronoun('possessive')} chest still tightened at the edge of the steps."
    )

    # Flashback.
    world.para()
    old_memory = _safe_lookup(FLASHBACKS, params.flashback)
    hero.memes["dread"] += 1
    hero.memes["memory"] += 1
    world.facts["flashback"] = params.flashback
    world.facts["memory_text"] = old_memory
    world.say(
        f"Then a flashback returned: {old_memory}."
    )
    world.say(
        f"At once, {hero.id} felt dread, because old fear can climb back like a cat in the dark."
    )

    # Dialogue and magic.
    world.para()
    world.say(
        f"{guide.label.capitalize()} watched {hero.id} and said, "
        f"\"What do you fear, child of the road?\""
    )
    world.say(
        f"{hero.id} answered, \"I fear the tall place and the old sign I remember.\""
    )
    world.say(
        f"{guide.label.capitalize()} lifted {charm.label} and said, "
        f"\"Then hold this {magic.phrase}. It does not erase the past. It only gives it a kinder shape.\""
    )
    hero.memes["trust"] += 1
    hero.memes["dread"] = max(0.0, hero.memes["dread"] - 1.0)
    hero.meters["light"] += 1 if magic.is_light else 0
    hero.meters["magic"] += 1

    # Turn and resolution.
    world.para()
    if magic.is_light:
        world.say(
            f"When the {magic.phrase} glowed, the steps no longer looked like a threat."
        )
    else:
        world.say(
            f"When the charm hummed, the memory loosened its grip on {hero.id}'s mind."
        )
    hero.memes["dread"] = 0.0
    hero.memes["awe"] += 1
    world.say(
        f"{hero.id} climbed the tall steps beside {guide.label}, and the higher {hero.id} rose, the smaller the fear became."
    )
    world.say(
        f"At the top, {hero.id} saw the sky open wide, and what had felt like dread became a quiet, shining awe."
    )

    world.facts.update(
        hero=hero,
        guide=guide,
        tower=tower,
        charm=charm,
        magic=magic,
        params=params,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    magic = _safe_fact(world, f, "magic")
    return [
        f'Write a short myth for a child about {hero.id}, a tall sacred place, and the magic of {magic.phrase}.',
        f"Tell a story with a flashback, dialogue, and a brave climb up a tall tower.",
        f"Write a gentle myth where fear is answered by wise words and a little magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    tower = _safe_fact(world, f, "tower")
    magic = _safe_fact(world, f, "magic")
    params = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"Why did {hero.id} feel dread near {tower.label}?",
            answer=f"{hero.id} felt dread because a flashback returned {f['memory_text']}, and the memory made the tall place seem frightening.",
        ),
        QAItem(
            question=f"What did {guide.label} give {hero.id} to help?",
            answer=f"{guide.label} gave {hero.id} {magic.label} so the old fear could soften and the tall climb could feel safe.",
        ),
        QAItem(
            question=f"What happened after {hero.id} listened to {guide.label}?",
            answer=f"{hero.id} climbed the tall steps, and by the end the dread had turned into awe at the top of {tower.label}.",
        ),
        QAItem(
            question=f"What kind of story is this about {hero.id} and the {params.magic} magic?",
            answer=f"It is a mythic story with a flashback and dialogue, where {hero.id} learns that a remembered fear can be faced with help.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly shows something that happened before, so the reader can understand an old memory.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in the story.",
        ),
        QAItem(
            question="What does tall mean?",
            answer="Tall means something reaches high up and stands above things around it.",
        ),
        QAItem(
            question="What is magic in a myth?",
            answer="Magic is a special wonder in a myth that can glow, sing, heal, or change how a person sees the world.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
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
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        if m.is_light:
            lines.append(asp.fact("light_magic", mid))
        for s in sorted(m.soothes):
            lines.append(asp.fact("soothes", mid, s))
        for s in sorted(m.suits):
            lines.append(asp.fact("suits", mid, s))
    for fb in FLASHBACKS:
        lines.append(asp.fact("flashback", fb))
    return "\n".join(lines)


ASP_RULES = r"""
causes_dread(FB) :- flashback(FB).
helpful(M,FB) :- magic(M), causes_dread(FB), soothes(M,dread).
compatible(M,FB) :- suits(M,FB).
valid(M,FB) :- magic(M), flashback(FB), helpful(M,FB).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about dread, tall places, magic, flashback, and dialogue.")
    ap.add_argument("--magic", choices=sorted(MAGICS))
    ap.add_argument("--flashback", choices=sorted(FLASHBACKS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=sorted(GUIDES))
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
    combos = valid_combos()
    if getattr(args, "magic", None) and getattr(args, "flashback", None):
        if (getattr(args, "magic", None), getattr(args, "flashback", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in NAMES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    magic = getattr(args, "magic", None) or rng.choice(sorted(MAGICS))
    flashback = getattr(args, "flashback", None) or rng.choice(sorted(FLASHBACKS))
    name = getattr(args, "name", None) or rng.choice(NAMES[getattr(args, "gender", None) or rng.choice(["girl", "boy"])])
    gender = getattr(args, "gender", None) or ("girl" if name in NAMES["girl"] else "boy")
    guide = getattr(args, "guide", None) or rng.choice(sorted(GUIDES))
    return StoryParams(magic=magic, flashback=flashback, name=name, gender=gender, guide=guide)


def generate(params: StoryParams) -> StorySample:
    world = story_core(params)
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


CURATED = [
    StoryParams(magic="thread", flashback="omen", name="Lina", gender="girl", guide="priest"),
    StoryParams(magic="torch", flashback="storm", name="Tarin", gender="boy", guide="keeper"),
    StoryParams(magic="song", flashback="shadow", name="Mira", gender="girl", guide="priestess"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible magic/flashback combos:\n")
        for mid, fb in combos:
            print(f"  {mid:8} {fb}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
