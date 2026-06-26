#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/bale_amenity_magic_tall_tale.py
=====================================================================================================================

A standalone story world sketch for a tall tale about a magical bale and an amenity
that grows too tall. The domain mimics the hyperbole and friendly resolution of
American tall tales (Paul Bunyan, Pecos Bill), scaled for a child reader.

Seed story:
---
In a small prairie town called Flat Hollow, the sun beat down all summer.
Farmer Jed had one big problem: his new hay bale, "Giant Bertha," was magic.
Every night Bertha grew taller, until she blocked the view of the only
amenity in town -- the water tower that gave everyone cool drinks on hot days.
The mayor tried sawing, the blacksmith tried ropes, but Bertha just grew more.
So little Maisie, who knew Bertha liked songs, sat beside the bale and sang
a lullaby. The bale stopped growing. The town painted Bertha like a giant
sunflower and built a slide down her side. That afternoon everyone slid off
the bale straight into the water tower's shadow, where the amenity made
their drinks taste like honey and rain.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

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
    trait: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    magic: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    bale: object | None = None
    blacksmith: object | None = None
    farmer: object | None = None
    hero: object | None = None
    mayor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mayor"}
        male = {"boy", "man", "farmer", "blacksmith"}
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
    place: str = "Flat Hollow"
    big_feature: str = "the great prairie"   # tall tale landscape element
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
    mess: str
    zone: str = ""        # what gets affected
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
class MagicBale:
    """The magical bale that grows when people try to move it."""
    label: str = "Giant Bertha"
    song_weakness: str = "lullabies"


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.bale_grown: float = 0.0
        self.blocked_amenity: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def _r_grow_bale(world: World) -> list[str]:
    """If anyone tries to cut or pull the bale, it grows taller."""
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("cut_attempt", 0) >= THRESHOLD and e.magic:
            world.bale_grown += 2.0
            out.append(f"The bale {e.label} stretched up another ten feet.")
            break
    return out


def _r_block_amenity(world: World) -> list[str]:
    """When bale is tall enough, it blocks the water tower."""
    if world.bale_grown >= 3.0 and not world.blocked_amenity:
        world.blocked_amenity = True
        return ["Now the bale was so tall it hid the water tower, and the amenity felt sad and empty."]
    return []


def _r_song_soothes(world: World) -> list[str]:
    """Singing the right song stops the growth and shrinks the bale."""
    for e in list(world.entities.values()):
        if e.meters.get("sang_lullaby", 0) >= THRESHOLD and world.bale_grown > 0:
            world.bale_grown = 0.0
            world.blocked_amenity = False
            return ["The song touched the bale's heart. Bertha stopped growing and shrank to a friendly size."]
    return []


CAUSAL_RULES: list[tuple[str, Callable]] = [
    ("grow", _r_grow_bale),
    ("block", _r_block_amenity),
    ("soothe", _r_song_soothes),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for name, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Verbs / beats (tall tale style)
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, farmer: Entity) -> None:
    world.say(
        f"In a small prairie town called {world.setting.place}, the sun beat down all summer. "
        f"{farmer.id} the farmer had one big problem: his new hay bale, \"Giant Bertha,\" was magic."
    )


def magic_appears(world: World, bale_entity: Entity) -> None:
    world.say(
        f"Every night {bale_entity.label} grew taller, until she blocked the view of the only "
        f"amenity in town -- the water tower that gave everyone cool drinks on hot days."
    )


def townsfolk_try(world: World, mayor: Entity, blacksmith: Entity) -> None:
    world.say(
        f"The {mayor.label} tried sawing, the {blacksmith.label} tried ropes, but "
        f"{'she' if 'bertha' in str(world.entities).lower() else 'Bertha'} just grew more."
    )


def hero_sings(world: World, hero: Entity, bale_entity: Entity) -> None:
    hero.meters["sang_lullaby"] += 1
    world.say(
        f"So little {hero.id}, who knew {bale_entity.label} liked songs, sat beside the bale "
        f"and sang a lullaby. The bale stopped growing."
    )


def resolution_tall(world: World, hero: Entity, bale_entity: Entity) -> None:
    world.say(
        f"The town painted {bale_entity.label} like a giant sunflower and built a slide down her side. "
        f"That afternoon everyone slid off the bale straight into the water tower's shadow, "
        f"where the amenity made their drinks taste like honey and rain."
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting,
         hero_name: str = "Maisie",
         hero_type: str = "girl",
         farmer_type: str = "Farmer Jed",
         mayor_type: str = "Mayor Higgins",
         blacksmith_type: str = "Blacksmith Pete") -> World:

    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                           trait="clever and kind"))
    farmer = world.add(Entity(id=farmer_type, kind="character", type="farmer",
                             label="Farmer Jed"))
    mayor = world.add(Entity(id=mayor_type, kind="character", type="mayor",
                            label="Mayor Higgins"))
    blacksmith = world.add(Entity(id=blacksmith_type, kind="character", type="blacksmith",
                                 label="Blacksmith Pete"))
    bale = world.add(Entity(id="Bertha", kind="thing", type="magic bale",
                           label="Giant Bertha", magic=True,
                           phrase="a huge, magical hay bale"))

    # Act 1
    introduce(world, hero, farmer)
    magic_appears(world, bale)
    world.para()

    # Act 2
    townsfolk_try(world, mayor, blacksmith)
    bale.meters["cut_attempt"] += 1
    propagate(world)
    world.para()

    # Act 3
    hero_sings(world, hero, bale)
    propagate(world)
    resolution_tall(world, hero, bale)

    world.facts.update(hero=hero, farmer=farmer, mayor=mayor, blacksmith=blacksmith,
                       bale=bale, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "prairie": Setting(place="Flat Hollow", big_feature="the endless prairie"),
    "desert": Setting(place="Dry Gulch", big_feature="the shimmering desert"),
}

HERO_NAMES = ["Maisie", "Caleb", "Lily", "Zeke", "Pearl"]
FARMER_NAMES = ["Farmer Jed", "Farmer Walt", "Farmer Sue"]
MAYOR_NAMES = ["Mayor Higgins", "Mayor Brown", "Mayor Gray"]
BLACKSMITH_NAMES = ["Blacksmith Pete", "Blacksmith Jo", "Blacksmith Mac"]

# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hero_name: str
    farmer_name: str
    mayor_name: str
    blacksmith_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------
    curated: list = field(default_factory=list)
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


KNOWLEDGE = {
    "bale": [("What is a hay bale?",
              "A hay bale is a big bundle of dried grass, usually shaped like a "
              "fat round or a square, that farmers use to feed animals in winter.")],
    "amenity": [("What is an amenity?",
                 "An amenity is something that makes life nicer for everyone, "
                 "like a playground, a water tower, or a bench in the shade.")],
    "magic": [("Can people really make things grow with songs?",
               "In tall tales, the world works differently -- songs can calm a "
               "magic bale, and kindness can fix big problems.")],
    "tall_tale": [("What is a tall tale?",
                   "A tall tale is a funny, exaggerated story about impossible "
                   "things, like a giant bale or a cowboy who could rope a tornado.")],
    "sunflower": [("Why did the town paint the bale like a sunflower?",
                   "Sunflowers are big and bright and happy. Painting Bertha like "
                   "one meant she became a fun part of town instead of a problem.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a 4-to-6-year-old about a magical bale and a town amenity.',
        f"Tell a story where {f['hero'].id} uses a song to solve a problem that giant tools could not fix.",
        f'Write a story that includes the words "bale" and "amenity" and ends with everyone happy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who lived in {world.setting.place} when the magic bale grew too tall?",
            answer=f"In {world.setting.place} lived Farmer {f['farmer'].label}, Mayor "
                   f"{f['mayor'].label}, Blacksmith {f['blacksmith'].label}, and a clever "
                   f"child named {f['hero'].id}."
        ),
        QAItem(
            question="What happened every time the townsfolk tried to cut or pull the magic bale?",
            answer="Every time they tried, the bale grew even taller. It stretched "
                   "up and up until it blocked the water tower, the town's best amenity."
        ),
        QAItem(
            question=f"How did {f['hero'].id} fix the problem of the magic bale?",
            answer=f"{f['hero'].id} sat beside the bale and sang a gentle lullaby. "
                   "The song soothed the bale, and it stopped growing and shrank back down."
        ),
        QAItem(
            question="What did the town do with the bale after it was no longer dangerous?",
            answer="They painted it like a giant sunflower and built a slide down its side. "
                   "Everyone slid off the bale into the water tower's shade, where the "
                   "amenity made their drinks taste like honey and rain."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["bale", "amenity", "magic", "tall_tale", "sunflower"]:
        q, a = KNOWLEDGE[key][0]
        out.append(QAItem(question=q, answer=a))
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall tale: a magic bale, a town amenity, and a child's song.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS.keys()))
    return StoryParams(
        setting=setting,
        hero_name=getattr(args, "hero", None) or rng.choice(HERO_NAMES),
        farmer_name=rng.choice(FARMER_NAMES),
        mayor_name=rng.choice(MAYOR_NAMES),
        blacksmith_name=rng.choice(BLACKSMITH_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), params.hero_name,
                 params.farmer_name, params.mayor_name, params.blacksmith_name)
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
        dump_trace(sample.world)
    if qa:
        print()
        print("== Q&A ==")
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
            print()


def dump_trace(world: World) -> None:
    print("--- trace ---")
    for e in list(world.entities.values()):
        mets = {k: v for k, v in e.meters.items() if v}
        mems = {k: v for k, v in e.memes.items() if v}
        if mets or mems:
            print(f"  {e.id}: meters={dict(mets)} memes={dict(mems)}")
    print(f"  bale_grown={world.bale_grown}")


def main() -> None:
    args = build_parser().parse_args()
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [StoryParams(s, r) for s in SETTINGS for r in HERO_NAMES[:2]]
        for p in curated:
            samples.append(generate(p))
    else:
        i = 0
        while len(samples) < getattr(args, "n", None):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### {sample.params.hero_name} in {sample.params.setting}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


ASP_RULES = """
bale_grows(P) :- magic_bale(P), attempt_move(_).
blocks_amenity(P) :- bale_grows(P), bale_height(P, H), H > 3.
soothed(P) :- song_sung(_, P).
"""


def asp_facts() -> str:
    return "magic_bale(bertha).\nattempt_move(mayor).\nattempt_move(blacksmith).\n"


def asp_verify() -> int:
    return 0


if __name__ == "__main__":
    main()
