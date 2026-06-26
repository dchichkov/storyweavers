#!/usr/bin/env python3
"""
Storyworld: Tablet Darn Happy Ending Superhero Story

A small simulation of a superhero mishap where a child hero's tablet is
endangered during a rescue, then protected and repaired through a kind,
state-driven turn toward a happy ending.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    hero: object | None = None
    sidekick: object | None = None
    tablet: object | None = None
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
class Scene:
    place: str
    danger: str
    rescue: str
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
class Gear:
    id: str
    label: str
    protects: set[str]
    fix: str
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


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    place: str
    danger: str
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


THRESHOLD = 1.0


SCENES = {
    "rooftop": Scene(
        place="the sunny rooftop",
        danger="wind",
        rescue="catch the runaway kite",
    ),
    "street": Scene(
        place="the quiet street",
        danger="rain",
        rescue="help the lost robot cross the road",
    ),
    "park": Scene(
        place="the city park",
        danger="mud",
        rescue="save the ducklings from the puddle path",
    ),
}

GEAR = [
    Gear(id="cape", label="a bright cape", protects={"wind"}, fix="the cape kept it from fluttering away"),
    Gear(id="boots", label="sturdy boots", protects={"mud"}, fix="the boots kept the feet clean"),
    Gear(id="case", label="a padded case", protects={"rain"}, fix="the case kept the tablet dry"),
]

HERO_NAMES = ["Nova", "Milo", "Pip", "Aria", "Zane", "Luna"]
SIDEKICK_NAMES = ["Bea", "Toby", "Nia", "Ollie", "June", "Finn"]


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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


def _narrate_intro(world: World, hero: Entity, sidekick: Entity, tablet: Entity) -> None:
    world.say(
        f"{hero.id} was a little superhero with a brave grin and a knack for helping people."
    )
    world.say(
        f"{hero.id} and {sidekick.id} loved solving problems together, and {hero.id} carried "
        f"{hero.pronoun('possessive')} tablet everywhere because it held maps, notes, and rescue plans."
    )
    world.say(
        f"That tablet was very important, and {hero.id} never wanted anything to happen to it."
    )


def _start_rescue(world: World, hero: Entity, sidekick: Entity) -> None:
    world.para()
    world.say(
        f"One afternoon at {world.scene.place}, a small alarm rang out. "
        f"{hero.id} spotted trouble and said, \"Darn, we have to go now!\""
    )
    world.say(
        f"Without wasting a second, {hero.id} and {sidekick.id} hurried toward {world.scene.rescue}."
    )


def _risk_tablet(world: World, hero: Entity, tablet: Entity) -> None:
    danger = world.scene.danger
    if danger == "wind":
        tablet.meters["blown"] += 1
        hero.memes["worry"] += 1
        world.say(
            f"The wind tugged at {hero.pronoun('possessive')} bag, and {hero.id} gasped as {hero.pronoun('possessive')} tablet wobbled near the edge."
        )
    elif danger == "rain":
        tablet.meters["wet"] += 1
        hero.memes["worry"] += 1
        world.say(
            f"Rain spots began to fall, and {hero.id} worried because {hero.pronoun('possessive')} tablet could get wet."
        )
    else:
        tablet.meters["smeared"] += 1
        hero.memes["worry"] += 1
        world.say(
            f"The muddy path splashed up, and {hero.id} worried because {hero.pronoun('possessive')} tablet could get dirty."
        )


def _helper_turn(world: World, sidekick: Entity, hero: Entity, tablet: Entity) -> Optional[Gear]:
    world.say(
        f"{sidekick.id} pointed at {hero.pronoun('possessive')} tablet and said, \"We can still be fast, but we should protect it first.\""
    )
    danger = world.scene.danger
    gear = next((g for g in GEAR if danger in g.protects), None)
    if not gear:
        pass
    world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=hero.id,
    ))
    world.say(
        f"{hero.id} nodded, slipped on {gear.label}, and smiled because {gear.fix}."
    )
    return gear


def _finish_rescue(world: World, hero: Entity, sidekick: Entity, tablet: Entity, gear: Gear) -> None:
    tablet.meters["safe"] += 1
    hero.memes["worry"] = 0
    hero.memes["joy"] = 1
    world.para()
    world.say(
        f"Then {hero.id} dashed in, finished {world.scene.rescue}, and saved the day."
    )
    world.say(
        f"At the end, {hero.id}'s tablet stayed safe, {sidekick.id} cheered, and the city felt bright again."
    )
    world.say(
        f"It was a happy ending: the hero kept the tablet, the rescue worked, and {hero.id} still got to say, \"Darn, that was close!\" with a proud smile."
    )


def tell(params: StoryParams) -> World:
    scene = _safe_lookup(SCENES, params.place)
    world = World(scene)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["brave", "kind"],
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type=params.sidekick_type,
        traits=["quick", "helpful"],
    ))
    tablet = world.add(Entity(
        id="tablet",
        kind="thing",
        type="tablet",
        label="tablet",
        phrase="a bright rescue tablet",
        owner=hero.id,
        caretaker=hero.id,
    ))

    _narrate_intro(world, hero, sidekick, tablet)
    _start_rescue(world, hero, sidekick)
    _risk_tablet(world, hero, tablet)
    gear = _helper_turn(world, sidekick, hero, tablet)
    if gear is None:
        pass
    _finish_rescue(world, hero, sidekick, tablet, gear)

    world.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "tablet": tablet,
        "gear": gear,
        "scene": scene,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    scene: Scene = _safe_fact(world, f, "scene")
    return [
        f"Write a short superhero story for a child where {hero.id} protects a tablet during a rescue at {scene.place}.",
        f"Tell a happy-ending story in which {hero.id} and {sidekick.id} save the day while keeping a tablet safe.",
        f"Write a gentle superhero story that includes the word 'darn' and ends with a safe, cheerful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    tablet: Entity = _safe_fact(world, f, "tablet")
    scene: Scene = _safe_fact(world, f, "scene")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little superhero who worked with {sidekick.id}.",
        ),
        QAItem(
            question=f"Why did {hero.id} say 'Darn'?",
            answer=f"{hero.id} said 'Darn' because there was trouble at {scene.place} and the rescue had to happen quickly.",
        ),
        QAItem(
            question=f"Why was the tablet important?",
            answer=f"The tablet was important because it held rescue plans, and {hero.id} wanted it to stay safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily, with the rescue finished and the tablet still safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tablet?",
            answer="A tablet is a small computer with a flat screen that people can tap to read, draw, or play.",
        ),
        QAItem(
            question="What does darn mean?",
            answer="Darn is a mild word people say when something goes wrong or feels frustrating.",
        ),
        QAItem(
            question="Why do superheroes wear gear?",
            answer="Superheroes wear gear to stay safe and to help them do hard jobs better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(parts))
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
sidekick(S) :- sidekick_name(S).
tablet(t).
danger(D) :- danger_name(D).
protects(cape, wind).
protects(boots, mud).
protects(case, rain).
needs_protection(t, D) :- danger(D).
happy_ending :- rescue_done, tablet_safe.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("hero_name", "hero"),
        asp.fact("sidekick_name", "sidekick"),
        asp.fact("tablet_name", "tablet"),
        asp.fact("danger_name", "wind"),
        asp.fact("danger_name", "rain"),
        asp.fact("danger_name", "mud"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show happy_ending/0."))
    has = any(sym.name == "happy_ending" for sym in model)
    if has:
        print("OK: ASP gate can derive the happy ending.")
        return 0
    print("MISMATCH: ASP gate failed to derive the happy ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with a tablet and a happy ending.")
    ap.add_argument("--place", choices=SCENES.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SCENES))
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    sidekick_name = getattr(args, "sidekick_name", None) or rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    hero_type = "boy" if hero_name in {"Milo", "Zane"} else "girl"
    sidekick_type = "boy" if sidekick_name in {"Toby", "Ollie", "Finn"} else "girl"
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
        place=place,
        danger={"rooftop": "wind", "street": "rain", "park": "mud"}[place],
    )


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
        print(asp_program("#show happy_ending/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show happy_ending/0."))
        print("ASP model atoms:", model)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in SCENES:
            params = StoryParams(
                hero_name=_safe_lookup(HERO_NAMES, 0),
                hero_type="girl",
                sidekick_name=_safe_lookup(SIDEKICK_NAMES, 0),
                sidekick_type="girl",
                place=place,
                danger={"rooftop": "wind", "street": "rain", "park": "mud"}[place],
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
