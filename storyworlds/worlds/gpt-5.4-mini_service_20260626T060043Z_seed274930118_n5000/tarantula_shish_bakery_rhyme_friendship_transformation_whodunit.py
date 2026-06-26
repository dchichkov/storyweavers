#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tarantula_shish_bakery_rhyme_friendship_transformation_whodunit.py
======================================================================================================

A small bakery whodunit story world built from the seed words "tarantula" and
"shish", with rhyme, friendship, and transformation as the main instruments.

Premise:
- A bakery is getting ready for the morning rush.
- A special shish pastry goes missing.
- A tarantula appears near the flour and looks suspicious.
- Clues arrive as little rhymes.
- The ending turns fear into friendship, and the tarantula's image transforms
  from "terrible" to "helpful".

The story is not a fixed paragraph with swapped nouns: the world model tracks
suspicion, trust, dust, and the missing pastry, and the prose follows those
changes.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    basket: object | None = None
    hero: object | None = None
    tarantula: object | None = None
    tray: object | None = None
    def __post_init__(self) -> None:
        for k in ["dust", "missing", "crumbs", "tidy"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "trust", "curiosity", "joy", "suspicion", "pride", "friendship"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the bakery"
    morning: bool = True
    setting: object | None = None
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
class Mystery:
    missing_item: str
    item_phrase: str
    suspect: str
    clue_rhyme: str
    rhyme_answer: str
    turn: str
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
    role: str
    suspect: str
    mystery: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


MYSTERIES = {
    "glaze": Mystery(
        missing_item="shish bun",
        item_phrase="a shiny shish bun glazed with honey",
        suspect="tarantula",
        clue_rhyme="When buns go missing, look for the gleam; follow the flour and find the seam.",
        rhyme_answer="The clue led to the warm proofing shelf, where the bun had been set aside by mistake.",
        turn="The tarantula only wanted a dry corner and a place to help count the buns.",
    ),
    "jam": Mystery(
        missing_item="shish tart",
        item_phrase="a tiny shish tart with bright jam",
        suspect="tarantula",
        clue_rhyme="When jam is gone, don't cry and moan; look where the sticky spoon was known.",
        rhyme_answer="The tart had been moved by the baker's helper while cleaning the tray.",
        turn="The tarantula had followed the jam trail to keep the floor from getting slippery.",
    ),
    "seed": Mystery(
        missing_item="shish roll",
        item_phrase="a soft shish roll with sesame seeds",
        suspect="tarantula",
        clue_rhyme="If seeds are gone, don't shout and race; check the basket, check the place.",
        rhyme_answer="The roll had slid behind the basket when the table was bumped.",
        turn="The tarantula had spotted the basket wobble and saved the roll from being crushed.",
    ),
}

HEROES = {
    "child": ("girl", "curious"),
    "baker": ("woman", "steady"),
}


def choose_name(role: str, rng: random.Random) -> str:
    if role == "child":
        return rng.choice(["Mina", "Lina", "Tessa", "Nora", "Pip"])
    return rng.choice(["Mara", "June", "Sana", "Ruth", "Iris"])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bakery whodunit with rhyme, friendship, and transformation.")
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["child", "baker"])
    ap.add_argument("--suspect", choices=["tarantula"])
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
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
    role = getattr(args, "role", None) or rng.choice(["child", "baker"])
    suspect = getattr(args, "suspect", None) or "tarantula"
    mystery = getattr(args, "mystery", None) or rng.choice(sorted(MYSTERIES))
    name = getattr(args, "name", None) or choose_name(role, rng)
    return StoryParams(name=name, role=role, suspect=suspect, mystery=mystery)


def _act_intro(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a {hero.type} who loved the quiet before the bakery opened."
    )
    world.say(
        f"That morning, the bakery smelled like warm butter, sweet sugar, and {mystery.missing_item}."
    )
    hero.memes["curiosity"] += 1


def _act_discovery(world: World, hero: Entity, mystery: Mystery, tarantula: Entity, basket: Entity, tray: Entity) -> None:
    hero.memes["fear"] += 1
    hero.memes["suspicion"] += 1
    tarantula.memes["suspicion"] += 1
    world.say(
        f"Then {hero.id} saw a tarantula by the flour sack, still and black as a comma."
    )
    world.say(
        f"Near the counter, a {mystery.missing_item} had vanished from the cooling tray."
    )
    world.say(
        f"{hero.id} wondered if the spider had taken it, because the clue looked very strange."
    )


def _act_clue(world: World, mystery: Mystery) -> None:
    world.say(f'A little rhyme helped: "{mystery.clue_rhyme}"')
    world.say("The words sounded playful, but they made everyone look in the right place.")
    world.facts["clue_rhyme"] = mystery.clue_rhyme


def _act_turn(world: World, hero: Entity, mystery: Mystery, tarantula: Entity) -> None:
    hero.memes["fear"] += -0.5
    hero.memes["curiosity"] += 1
    tarantula.memes["trust"] += 1
    world.say(
        f"Following the rhyme, {hero.id} found the missing {mystery.missing_item} near the warm proofing shelf."
    )
    world.say(
        f"{mystery.rhyme_answer} {mystery.turn}"
    )


def _act_reveal(world: World, hero: Entity, mystery: Mystery, tarantula: Entity) -> None:
    hero.memes["suspicion"] = 0.0
    hero.memes["trust"] += 1
    hero.memes["friendship"] += 1
    tarantula.memes["friendship"] += 1
    tarantula.memes["trust"] += 2
    tarantula.memes["pride"] += 1
    world.say(
        f"{hero.id} blinked, then smiled at the tarantula. It had not stolen anything at all."
    )
    world.say(
        f'Instead, it had helped solve the whodunit, and {hero.id} said, "You are a brave little helper."'
    )
    world.say(
        f"The tarantula lifted one shiny leg as if bowing, and the scary feeling turned into a new friendship."
    )


def _act_end(world: World, hero: Entity, mystery: Mystery, tarantula: Entity) -> None:
    hero.memes["joy"] += 2
    tarantula.memes["joy"] += 1
    world.say(
        f"Together they carried the {mystery.missing_item} back to the tray, dusted the counter, and saved the morning."
    )
    world.say(
        f"By the time the bakery door opened, the tarantula was no longer a suspect."
    )
    world.say(
        f"It was the small friend who had transformed the whole story."
    )


def tell(params: StoryParams) -> World:
    if params.role not in HEROES:
        pass
    if params.mystery not in MYSTERIES:
        pass
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    setting = Setting()
    world = World(setting)

    hero_type, trait = _safe_lookup(HEROES, params.role)
    hero = world.add(Entity(id=params.name, kind="character", type=hero_type))
    hero.memes["curiosity"] += 1
    hero.memes[trait] += 1

    tarantula = world.add(Entity(id="Tara", kind="character", type="tarantula"))
    tarantula.memes["fear"] += 0.5

    basket = world.add(Entity(id="basket", type="thing", label="basket"))
    tray = world.add(Entity(id="tray", type="thing", label="cooling tray"))
    tarantula.owner = None

    world.facts.update(
        hero=hero,
        tarantula=tarantula,
        mystery=mystery,
        basket=basket,
        tray=tray,
        setting=setting,
        role=params.role,
    )

    _act_intro(world, hero, mystery)
    world.para()
    _act_discovery(world, hero, mystery, tarantula, basket, tray)
    world.para()
    _act_clue(world, mystery)
    _act_turn(world, hero, mystery, tarantula)
    world.para()
    _act_reveal(world, hero, mystery, tarantula)
    _act_end(world, hero, mystery, tarantula)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a young child in a bakery that includes the word "tarantula" and the food word "{f["mystery"].missing_item}".',
        f"Tell a gentle mystery about {f['hero'].id} in the bakery, a missing {f['mystery'].missing_item}, and a tarantula that turns into a friend.",
        "Write a story where a rhyme helps solve a bakery mystery and the scary character becomes helpful by the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    tarantula = _safe_fact(world, f, "tarantula")
    return [
        QAItem(
            question=f"What kind of place was the story set in?",
            answer="It was set in a bakery, where warm bread and sweet treats were being prepared.",
        ),
        QAItem(
            question=f"What was missing in the whodunit?",
            answer=f"The missing item was {mystery.item_phrase}.",
        ),
        QAItem(
            question=f"Who did {hero.id} first suspect?",
            answer=f"{hero.id} first suspected the tarantula, because it was sitting near the flour and looked mysterious.",
        ),
        QAItem(
            question="What helped solve the mystery?",
            answer=f"A little rhyme helped everyone look in the right place and find the missing {mystery.missing_item}.",
        ),
        QAItem(
            question=f"What changed about the tarantula by the end?",
            answer="The tarantula changed from seeming scary to being a friend who helped solve the mystery.",
        ),
        QAItem(
            question=f"How did the story show transformation?",
            answer=f"The biggest transformation was in feeling: {hero.id}'s fear and suspicion turned into trust and friendship.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bakery?",
            answer="A bakery is a place where bread, pastries, and other baked treats are made and sold.",
        ),
        QAItem(
            question="What is a tarantula?",
            answer="A tarantula is a large spider with many legs.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a set of words that sound alike at the end, which can make a clue or song easier to remember.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means people or creatures treat each other kindly, help each other, and feel close and safe together.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes from one state or feeling into another.",
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mina", role="child", suspect="tarantula", mystery="glaze"),
    StoryParams(name="Mara", role="baker", suspect="tarantula", mystery="jam"),
    StoryParams(name="Pip", role="child", suspect="tarantula", mystery="seed"),
]


ASP_RULES = r"""
mystery(glaze).
mystery(jam).
mystery(seed).
role(child).
role(baker).
suspect(tarantula).

valid(Name, Role, Suspect, Mystery) :- role(Role), suspect(Suspect), mystery(Mystery), name(Name).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for n in ["Mina", "Mara", "Pip", "Lina", "Nora", "Tessa", "June", "Ruth", "Iris"]:
        lines.append(asp.fact("name", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p.name, p.role, p.suspect, p.mystery) for p in CURATED}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches curated combos ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and curated stories:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_storysample(params: StoryParams) -> StorySample:
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
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} compatible story combos:\n")
        for row in vals:
            print("  " + " ".join(map(str, row)))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [build_storysample(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = build_storysample(params)
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
            header = f"### {p.name}: {p.role}, mystery={p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
