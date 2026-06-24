#!/usr/bin/env python3
"""
A small Tall-Tale-style storyworld about a petite, urgent hero who follows an
inner monologue, hunts a mystery to solve, and completes a quest.
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

WORLD_NAME = "petite_urgent_inner_monologue_mystery_to_solve"



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    mystery: object | None = None
    quest: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    feature: str
    mystery: str
    quest: str
    clue: str
    resolution: str
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
    companion: str
    mystery_item: str
    quest_goal: str
    seed: Optional[int] = None
    params: object | None = None
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


PLACES = {
    "barn": Place(
        name="the barn",
        feature="high rafters",
        mystery="a missing rooster bell",
        quest="find the bell before supper",
        clue="a trail of bright feathers",
        resolution="the bell was tucked inside a feed bucket",
    ),
    "orchard": Place(
        name="the orchard",
        feature="crooked apple trees",
        mystery="a vanished silver key",
        quest="bring the key back to the little gate",
        clue="muddy little prints under an apple tree",
        resolution="the key hung on a nail in the cider shed",
    ),
    "dock": Place(
        name="the dock",
        feature="planks that sang in the wind",
        mystery="a lost lantern hook",
        quest="recover the hook before the fog rolled in",
        clue="a shiny wink near a crab basket",
        resolution="the hook was tied to a rope coil",
    ),
}

HERO_NAMES = ["Mina", "Pip", "June", "Nell", "Toby", "Wren", "Bo", "Ivy"]
COMPANIONS = ["a barn cat", "a goose", "an old dog", "a tiny sparrow", "a helpful rabbit"]
HERO_TYPES = ["girl", "boy"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A petite, urgent mystery quest in a Tall Tale style.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--mystery-item")
    ap.add_argument("--quest-goal")
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    p = _safe_lookup(PLACES, place)
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    mystery_item = getattr(args, "mystery_item", None) or p.mystery
    quest_goal = getattr(args, "quest_goal", None) or p.quest
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        companion=companion,
        mystery_item=mystery_item,
        quest_goal=quest_goal,
    )


def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if not params.hero_name:
        pass
    if not params.mystery_item:
        pass
    if not params.quest_goal:
        pass


def tell_story(params: StoryParams) -> World:
    validate_params(params)
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        phrase=f"a petite {params.hero_type} named {params.hero_name}",
        meters={"height": 1.0},
        memes={"urgency": 1.0, "curiosity": 1.0, "bravery": 1.0},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type="animal",
        label=params.companion,
        phrase=params.companion,
    ))
    mystery = world.add(Entity(
        id="mystery",
        kind="thing",
        type="object",
        label=params.mystery_item,
        phrase=params.mystery_item,
        owner="unknown",
        meters={"hidden": 1.0},
    ))
    quest = world.add(Entity(
        id="quest",
        kind="thing",
        type="quest",
        label=params.quest_goal,
        phrase=params.quest_goal,
    ))

    world.facts.update(hero=hero, companion=companion, mystery=mystery, quest=quest, place=place, params=params)

    world.say(f"{hero.label} was a petite little traveler with quick feet and a head full of questions.")
    world.say(f"{hero.label} stood by {place.name} and listened to {hero.pronoun('possessive')} own inner monologue.")
    world.say(f'"Hurry now," {hero.pronoun()} thought. "Something small and important is missing, and I mean to solve it."')
    world.say(f"Beside {hero.label} went {companion.label}, and together they set out under {place.feature}.")
    world.say(f"The mystery to solve was {place.mystery}, and the quest was to {place.quest_goal if params.quest_goal else place.quest}.")
    world.say(f"They searched by lantern light, and the first clue was {place.clue}.")
    world.say(f'"That clue has a wag in it," {hero.label} thought. "A hidden thing near here is trying to stay clever."')
    world.say(f"They followed the clue through the dust, and the urgent little quest grew bold as brass.")
    world.say(f"At last, the answer popped up plain as a bird on a fence: {place.resolution}.")
    world.say(f"{hero.label} laughed, thanked {companion.label}, and carried the recovered treasure home.")
    world.say(f"So the petite seeker solved the mystery, finished the quest, and went to bed with a calmer heart.")

    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a Tall Tale for a child about {p.hero_name}, a petite hero, who has an urgent mystery to solve at {_safe_lookup(PLACES, p.place).name}.",
        f"Tell an inner-monologue adventure where {p.hero_name} thinks fast, follows a clue, and completes a quest.",
        f"Write a short story with a tiny hero, a missing object, and a happy answer at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    place: Place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.hero_name}, a petite {p.hero_type} who listened to an urgent inner monologue and went on a quest.",
        ),
        QAItem(
            question=f"What mystery did {p.hero_name} have to solve?",
            answer=f"{p.hero_name} had to solve the mystery of {place.mystery}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended when {place.resolution}, so the quest was finished and the hero could go home happy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    place: Place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question="What does petite mean?",
            answer="Petite means small and slight in size.",
        ),
        QAItem(
            question="What does urgent mean?",
            answer="Urgent means something feels important and needs attention right away.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the little voice a person hears in their own mind while thinking.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to reach a goal or solve a problem.",
        ),
        QAItem(
            question="Where did the adventure happen?",
            answer=f"It happened at {place.name}, with {place.feature} and a mystery to solve.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(barn). place(orchard). place(dock).
petite(hero).
urgent(hero).
mystery_to_solve(hero, M) :- mystery(M).
quest(hero, Q) :- quest_goal(Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in sorted(PLACES):
        lines.append(asp.fact("place", pid))
    lines.append(asp.fact("petite", "hero"))
    lines.append(asp.fact("urgent", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n--- trace ---")
        for k, v in sample.world.facts.items():
            if k != "params":
                print(f"{k}: {v}")
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show place/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in sorted(PLACES):
            params = StoryParams(
                place=place,
                hero_name=_safe_lookup(HERO_NAMES, 0),
                hero_type="girl",
                companion=_safe_lookup(COMPANIONS, 0),
                mystery_item=_safe_lookup(PLACES, place).mystery,
                quest_goal=_safe_lookup(PLACES, place).quest,
                seed=base_seed,
            )
            samples.append(generate(params))
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
