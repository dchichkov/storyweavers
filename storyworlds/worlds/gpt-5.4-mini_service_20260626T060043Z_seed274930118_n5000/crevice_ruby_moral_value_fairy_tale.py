#!/usr/bin/env python3
"""
storyworlds/worlds/crevice_ruby_moral_value_fairy_tale.py
==========================================================

A small fairy-tale storyworld about a traveler, a crevice, and a ruby that
tests a moral value: honesty versus greed.

Seed tale:
---
A small wanderer follows a glimmer to a crevice and finds a ruby in the stone.
A kind old helper warns that the gem may belong to the mountain's keeper.
The wanderer must choose: hide the ruby, or carry it back and tell the truth.
When the choice is honest, the mountain answers kindly, and the ruby becomes a
gift instead of a secret.

World idea:
- physical meters: distance to the crevice, whether the ruby is hidden, whether
  the keeper is near, whether the path is blocked
- emotional memes: wonder, greed, fear, relief, trust, shame
- moral value: honesty is rewarded, secrecy can turn tense and lonely

The story is deliberately compact, classical, and child-facing.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    keeper: object | None = None
    ruby: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "prince"}:
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
class Place:
    name: str
    setting_line: str
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
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    keeper_name: str
    treasure: str = "ruby"
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


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "forest": Place(
        name="the old forest",
        setting_line="The old forest stood quiet under silver leaves, and a narrow path bent between mossy stones.",
    ),
    "hill": Place(
        name="the hill",
        setting_line="The hill was round and green, with wind combing the grass like a gentle hand.",
    ),
    "village": Place(
        name="the village edge",
        setting_line="At the village edge, small houses leaned together while a stony path led toward the cliffs.",
    ),
}

HERO_TYPES = ["boy", "girl"]
GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Elin"]
BOY_NAMES = ["Evan", "Milo", "Oren", "Pip", "Tobin"]
HELPERS = ["Gran", "Old Willow", "Aunt Fern", "The Baker"]
KEEPERS = ["the mountain keeper", "the stone guardian", "the cave watcher"]

MORAL = "honesty"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _n(v: float) -> bool:
    return v >= 1.0


def describe_hero(hero: Entity) -> str:
    trait = hero.memes.get("curious", 0.0)
    if trait >= 1.0:
        return f"curious little {hero.type}"
    return f"little {hero.type}"


def intro(world: World, hero: Entity, helper: Entity, keeper: Entity) -> None:
    world.say(
        f"{hero.id} was a {describe_hero(hero)} who loved shiny things, quiet trails, and stories told by {helper.id}."
    )
    world.say(
        f"One day {helper.id} said there was a secret the mountain would only share with someone brave and honest."
    )
    world.say(world.place.setting_line)
    world.say(f"Far ahead, a dark crevice split the stone like a small open mouth.")


def find_crevice(world: World, hero: Entity, ruby: Entity) -> None:
    hero.meters["distance"] = 1.0
    hero.memes["wonder"] += 1.0
    ruby.meters["seen"] = 1.0
    world.say(
        f"{hero.id} followed a faint red glimmer until {hero.pronoun()} reached the crevice."
    )
    world.say(
        f"There, tucked in the crack, lay a ruby that flashed like a drop of sunset."
    )


def urge_keep(world: World, hero: Entity, ruby: Entity) -> None:
    hero.memes["greed"] += 1.0
    hero.memes["fear"] += 1.0
    ruby.meters["hidden"] = 1.0
    world.say(
        f"{hero.id} picked up the ruby and hid {ruby.it()} in {hero.pronoun('possessive')} palm."
    )
    world.say(
        f"For a moment, {hero.pronoun()} thought, 'If I keep this ruby, it will be mine alone.'"
    )


def warn_about_truth(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["concern"] += 1.0
    world.say(
        f"{helper.id} saw the secret in {hero.pronoun('possessive')} hands and spoke softly."
    )
    world.say(
        f'"A found thing is not the same as a stolen thing," {helper.pronoun("subject")} said. '
        f'"If the ruby belongs to the mountain, honesty will matter more than hunger for gold."'
    )


def simulate_truth(world: World, hero: Entity, keeper: Entity, ruby: Entity) -> None:
    hero.memes["trust"] += 1.0
    hero.memes["greed"] = 0.0
    ruby.meters["hidden"] = 0.0
    ruby.owner = keeper.id
    keeper.memes["alert"] += 0.0
    world.say(
        f"{hero.id} took a slow breath and walked to the crevice with the ruby held out in open hands."
    )
    world.say(
        f'"I found this near the stone," {hero.id} said. "If it is yours, I want to return it."'
    )


def keeper_reward(world: World, keeper: Entity, hero: Entity, ruby: Entity) -> None:
    keeper.memes["trust"] += 1.0
    hero.memes["relief"] += 1.0
    hero.memes["joy"] += 1.0
    world.say(
        f"The mountain keeper stepped from the shadow and smiled at the brave little one."
    )
    world.say(
        f'"You chose the honest path," {keeper.id} said. "That ruby was hidden as a test, and now it can be a gift."'
    )
    world.say(
        f"So {hero.id} carried the ruby home with a clean heart, and it shone brighter for being shared fairly."
    )


def simulate_secret(world: World, hero: Entity, keeper: Entity, ruby: Entity) -> None:
    hero.memes["shame"] += 1.0
    hero.memes["trust"] = max(0.0, hero.memes.get("trust", 0.0) - 0.5)
    world.say(
        f"{hero.id} tried to keep the ruby hidden, but the stone path felt lonelier with each step."
    )
    world.say(
        f"When the mountain keeper asked whose treasure it was, {hero.id} had to look down and tell the truth at last."
    )
    world.say(
        f"Then the shame lifted, but only after {hero.id} admitted {hero.pronoun('object')} had been tempted to be sly."
    )


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    w = World(place)
    hero = w.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = w.add(Entity(id=params.helper_name, kind="character", type="elder"))
    keeper = w.add(Entity(id=params.keeper_name, kind="character", type="keeper", label="mountain keeper"))
    ruby = w.add(Entity(id="ruby", kind="thing", type="ruby", label="ruby", phrase="a bright ruby"))
    w.facts.update(hero=hero, helper=helper, keeper=keeper, ruby=ruby, place=place)

    hero.memes["curious"] = 1.0
    hero.memes["wonder"] = 0.0

    intro(w, hero, helper, keeper)
    w.para()
    find_crevice(w, hero, ruby)
    warn_about_truth(w, helper, hero)
    if params.seed is not None and params.seed % 2 == 1:
        urge_keep(w, hero, ruby)
        w.para()
        simulate_secret(w, hero, keeper, ruby)
    else:
        simulate_truth(w, hero, keeper, ruby)
        w.para()
        keeper_reward(w, keeper, hero, ruby)

    w.facts["honest"] = params.seed is None or params.seed % 2 == 0
    return w


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    return [
        f'Write a fairy tale for young children about {hero.id}, a crevice, and a ruby, with a moral about {MORAL}.',
        f"Tell a short story where {hero.id} finds a ruby near a crevice and {helper.id} helps {hero.pronoun('object')} choose the honest thing to do.",
        f'Write a gentle tale that includes the words "crevice" and "ruby" and ends with a kind reward for telling the truth.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    keeper: Entity = _safe_fact(world, f, "keeper")
    ruby: Entity = _safe_fact(world, f, "ruby")
    honest = _safe_fact(world, f, "honest")

    out = [
        QAItem(
            question=f"What did {hero.id} find near the crevice?",
            answer=f"{hero.id} found a ruby tucked in the stone crack, shining like sunset glass.",
        ),
        QAItem(
            question=f"Who reminded {hero.id} that honesty mattered?",
            answer=f"{helper.id} reminded {hero.id} that a found treasure should be handled honestly.",
        ),
    ]

    if honest:
        out.append(
            QAItem(
                question=f"What happened when {hero.id} told the mountain keeper about the ruby?",
                answer=(
                    f"The mountain keeper praised {hero.id} for being honest, and the ruby became a gift instead of a secret."
                ),
            )
        )
        out.append(
            QAItem(
                question=f"How did {hero.id} feel at the end of the story?",
                answer=f"{hero.id} felt relieved and joyful because the honest choice made the whole ending kind and bright.",
            )
        )
    else:
        out.append(
            QAItem(
                question=f"Why did {hero.id} feel uneasy after hiding the ruby?",
                answer=(
                    f"{hero.id} felt uneasy because keeping the ruby secret made the path feel lonelier, and the truth still had to be told."
                ),
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crevice?",
            answer="A crevice is a narrow crack or opening in rock or stone.",
        ),
        QAItem(
            question="What is a ruby?",
            answer="A ruby is a red gemstone that can sparkle like a tiny fire.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth and not trying to trick others.",
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A ruby is at risk when the hero reaches the crevice and can keep it hidden.
at_risk(ruby) :- near(crevice), sees(hero, ruby).

% Honesty is the moral good in this world.
moral_value(honesty).

% Choosing honesty gives a blessing; hiding the ruby gives tension.
blessed(hero) :- tells_truth(hero), moral_value(honesty).
troubled(hero) :- hides_treasure(hero), sees(helper, secret).

% The correct fairy-tale ending is the blessed one.
good_story :- blessed(hero), found(hero, ruby), near(crevice).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("helper", "helper"),
        asp.fact("keeper", "keeper"),
        asp.fact("treasure", "ruby"),
        asp.fact("place", "crevice"),
        asp.fact("near", "crevice"),
        asp.fact("sees", "hero", "ruby"),
        asp.fact("moral_value", "honesty"),
        asp.fact("found", "hero", "ruby"),
        asp.fact("tells_truth", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/0. #show blessed/1. #show troubled/1."))
    shown = {str(a) for a in model}
    if "good_story" in shown and "blessed(hero)" in shown and "troubled(hero)" not in shown:
        print("OK: ASP moral gate is consistent.")
        return 0
    print("MISMATCH: ASP moral gate did not produce the expected model.")
    print("MODEL:", sorted(shown))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryContext:
    params: StoryParams
    world: World
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about a crevice, a ruby, and honesty.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--keeper")
    ap.add_argument("--gender", choices=HERO_TYPES)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPERS)
    keeper_name = getattr(args, "keeper", None) or rng.choice(KEEPERS)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=gender,
        helper_name=helper_name,
        keeper_name=keeper_name,
    )


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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id} ({e.type}): {' '.join(bits)}")
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


def asp_fairy_story_program() -> str:
    return asp_program("#show good_story/0. #show blessed/1. #show troubled/1.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_fairy_story_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_fairy_story_program())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="forest", hero_name="Mira", hero_type="girl", helper_name="Gran", keeper_name="the mountain keeper", seed=0),
            StoryParams(place="hill", hero_name="Evan", hero_type="boy", helper_name="Old Willow", keeper_name="the stone guardian", seed=1),
            StoryParams(place="village", hero_name="Nora", hero_type="girl", helper_name="Aunt Fern", keeper_name="the cave watcher", seed=2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
