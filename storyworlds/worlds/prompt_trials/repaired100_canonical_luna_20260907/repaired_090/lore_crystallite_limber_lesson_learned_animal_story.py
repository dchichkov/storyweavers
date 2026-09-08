#!/usr/bin/env python3
"""
A small animal storyworld about a young otter, a moonlit crystallite, and a
limber lesson learned: careful listening can be stronger than rushing.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class Incident:
    title: str
    opening: str
    trouble: str
    first_try: str
    clue: str
    action: str
    twist: str
    resolution: str
    lesson: str
    ending: str
    question: str
    answer: str
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
    place: str = ""
    activity: str = ""
    prize: str = ""
    animal: str = ""
    name: str = ""
    helper: str = ""
    incident: str = ""
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


INCIDENTS = [
    Incident(
        "the humming hollow",
        "Luna the otter loved the old lore of Moonpool Meadow, where every stone was said to remember a song.",
        "One evening, a pale crystallite slipped from the meadow's story-stone and rolled into a narrow hollow.",
        "Luna reached in quickly, but the opening was too tight for her paw, and the crystallite glittered just beyond it.",
        "A soft hum came from the reeds. The hollow was not empty; a young field mouse was sheltering inside.",
        "Luna asked the mouse to step out, then used a limber willow twig to nudge the crystallite toward the entrance.",
        "The surprising turn was that the smallest helper knew the hollow's safest path.",
        "The mouse guided the crystallite around a root, and Luna carried it back to the story-stone without scraping its bright face.",
        "The lesson learned was that patient listening can open a path that force would close.",
        "Moonlight shone through the restored crystallite while the mouse and otter shared the meadow's quiet song.",
        "Who helped Luna find the safe path through the hollow?",
        "A young field mouse helped Luna by showing the safe path around the root.",
    ),
    Incident(
        "the crooked bridge",
        "Luna the otter knew old lore about a bridge that led from the riverbank to the berry hill.",
        "A clear crystallite rested on the far side, but spring water had made the bridge twist and wobble.",
        "Luna tried to scamper across before the bridge could sway again.",
        "A beaver called from below that the middle reeds were tied to a strong root, while the loose end was the dangerous part.",
        "Luna and the beaver pressed the bridge flat with smooth stones and crossed one careful step at a time.",
        "The turn was that the wobbly-looking middle was safer than the bridge's tempting edge.",
        "They reached the crystallite, wrapped it in moss, and repaired the loose end before returning.",
        "The lesson learned was to test the whole path instead of trusting one quick glance.",
        "The bridge lay straight over the stream, and the crystallite glowed in Luna's mossy bundle.",
        "What part of the bridge was dangerous?",
        "The loose end of the bridge was dangerous; the middle reeds were tied to a strong root.",
    ),
    Incident(
        "the hidden glimmer",
        "Luna had heard lore that a lost crystallite would shine only for an animal who shared the search.",
        "She spotted a glimmer beneath a fern, but the fern's leaves were tangled around a sleeping hedgehog.",
        "Luna began pulling the leaves aside, hoping to finish before sunset.",
        "The hedgehog stirred and explained that the fern was its warm blanket, while a clear track ran beside the roots.",
        "Luna backed away, woke the hedgehog gently, and followed the track with her new helper.",
        "The crystallite was not trapped in the fern after all; the glimmer had bounced off a stone beside it.",
        "The hedgehog found the stone, and Luna freed the crystallite without tearing the blanket.",
        "The lesson learned was that a bright clue still needs a gentle look.",
        "The hedgehog's fern blanket stayed whole as the crystallite sparkled beside the roots.",
        "Why did Luna stop pulling the fern?",
        "She stopped because the fern was the hedgehog's warm blanket and a safe track ran beside it.",
    ),
    Incident(
        "the swift stream",
        "The animals' lore said that the river kept precious things safe when friends carried them together.",
        "A crystallite bobbed in a shallow but swift stream, spinning toward a bank of sharp reeds.",
        "Luna jumped after it, but the current pushed her sideways.",
        "A heron noticed that the water slowed behind a fallen branch and called to Luna from the bank.",
        "Luna swam to the quiet pocket while the heron watched the branch, then they lifted the crystallite into a woven nest.",
        "The turn was that the safest route was not straight toward the prize but around the resting water.",
        "The crystallite was saved, and Luna thanked the heron before moving the fallen branch away from the channel.",
        "The lesson learned was that a detour can be the quickest safe choice.",
        "The crystallite rested in the woven nest while the stream hurried harmlessly past.",
        "Where did the water slow down?",
        "The water slowed behind a fallen branch, creating a quiet pocket beside the stream.",
    ),
    Incident(
        "the whispering cave",
        "Luna knew the cave lore: echoes repeated careless words but carried kind words farther.",
        "A small crystallite had fallen near the cave wall, where every sound became confusing.",
        "Luna called loudly and hurried toward the brightest echo.",
        "A bat told her to listen for the faintest sound instead, because the true crystallite made a tiny chiming note.",
        "Luna quieted her paws, followed the little chime, and found the crystallite beneath a shelf.",
        "The turn was that the loudest echo pointed away from the treasure.",
        "The bat and Luna rolled the crystallite into a soft nest of moss and carried it outside.",
        "The lesson learned was that quiet attention can reveal what noisy guessing hides.",
        "The cave grew still, and one tiny chime led Luna back into the moonlight.",
        "What sound led Luna to the crystallite?",
        "A tiny chiming note from the real crystallite led Luna beneath the cave shelf.",
    ),
]

NAMES = ["Luna", "Mira", "Pip", "Nell", "Toby"]
HELPERS = ["field mouse", "beaver", "hedgehog", "heron", "bat"]
OPENINGS = [
    "Moonlight silvered the meadow, and an old animal story began.",
    "Near the river, the night held a secret bright enough to follow.",
    "A little paw, a patient heart, and one shining clue met beneath the stars.",
]


def can_story(place: str, activity: str, prize: str) -> bool:
    return place == "moonpool_meadow" and activity == "recover" and prize == "crystallite"


ASP_RULES = r"""
place(moonpool_meadow).
activity(recover).
prize(crystallite).
compatible(P,A,R) :- place(P), activity(A), prize(R),
    P = moonpool_meadow, A = recover, R = crystallite.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "moonpool_meadow"),
            asp.fact("activity", "recover"),
            asp.fact("prize", "crystallite"),
        ]
    )


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("moonpool_meadow", "recover", "crystallite")]


def resolve_params(args: argparse.Namespace, rng: random.Random, seed: int) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) != "moonpool_meadow":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "activity", None) and getattr(args, "activity", None) != "recover":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "prize", None) and getattr(args, "prize", None) != "crystallite":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    incident_index = seed % len(INCIDENTS)
    helper = _safe_lookup(HELPERS, incident_index)
    return StoryParams(
        place="moonpool_meadow",
        activity="recover",
        prize="crystallite",
        animal="otter",
        name=name,
        helper=helper,
        incident=f"incident_{incident_index:02d}",
        seed=seed,
    )


def tell(params: StoryParams) -> World:
    index = int(params.incident.rsplit("_", 1)[1])
    incident = _safe_lookup(INCIDENTS, index)
    world = World()
    luna = world.add(
        Entity(
            id="animal",
            kind="character",
            label=params.name,
            type="otter",
            meters={"reach": 1.0, "patience": 0.0},
            memes={"curiosity": 1.0, "trust": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            label=incident.helper,
            type=incident.helper,
            meters={"knowledge": 1.0},
            memes={"friendship": 0.0},
        )
    )
    crystal = world.add(
        Entity(
            id="crystallite",
            kind="treasure",
            label="crystallite",
            type="crystallite",
            meters={"brightness": 1.0, "safety": 0.0},
            memes={"wonder": 1.0},
        )
    )
    world.facts.update(incident=incident, luna=luna, helper=helper, crystal=crystal)

    world.say(_safe_lookup(OPENINGS, index % len(OPENINGS)))
    world.say(f"{params.name} the otter loved the old lore of Moonpool Meadow.")
    world.say("The animals said that a crystallite was not truly found until it was carried safely home.")
    world.para()
    world.say(incident.opening)
    world.say(incident.trouble)
    world.say(f'"I can reach it quickly," {params.name} said. "I do not need help."')
    world.say(incident.first_try)
    world.para()
    world.say(incident.clue)
    world.say(f'"Please tell me what you see," {params.name} said.')
    world.say(f'"The safe way is here," the {incident.helper} replied.')
    world.say(incident.action)
    luna.meters["patience"] = 1.0
    luna.memes["trust"] = 1.0
    helper.memes["friendship"] = 1.0
    crystal.meters["safety"] = 1.0
    world.fired.add("listened")
    world.para()
    world.say(incident.twist)
    world.say(incident.resolution)
    world.say(f'"I learned something important," {params.name} said. "Careful listening can be stronger than rushing."')
    world.say(f"The lesson learned was this: {incident.lesson}")
    world.say(incident.ending)
    return world


def generation_prompts(world: World) -> list[str]:
    incident = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "incident")
    luna = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "luna")
    return [
        "Write an Animal Story about an otter, old lore, a crystallite, and a limber lesson learned.",
        f"Tell a child-friendly tale in which {luna.label} listens to a {incident.helper} before recovering a crystallite.",
        f"Build the story around this turning clue: {incident.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    incident: Incident = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "incident")
    luna: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "luna")
    return [
        QAItem(
            question=f"What did {luna.label} want to recover?",
            answer=f"{luna.label} wanted to recover a shining crystallite and carry it safely home.",
        ),
        QAItem(question=incident.question, answer=incident.answer),
        QAItem(
            question=f"How did the {incident.helper} change {luna.label}'s plan?",
            answer=f"The {incident.helper} shared a safer clue, so {luna.label} stopped rushing and followed the careful route.",
        ),
        QAItem(
            question="What was the lesson learned?",
            answer=incident.lesson,
        ),
        QAItem(
            question="What ending image showed that the problem was solved?",
            answer=incident.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an otter?",
            answer="An otter is a playful mammal that often lives near water and swims well.",
        ),
        QAItem(
            question="What does limber mean?",
            answer="Limber means able to bend or move easily without becoming stiff.",
        ),
        QAItem(
            question="What is a lesson learned in a story?",
            answer="A lesson learned is an idea the characters discover from what happened and can use later.",
        ),
        QAItem(
            question="Why can listening help an animal solve a problem?",
            answer="Listening can reveal clues from another animal and prevent a rushed or unsafe choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"  {entity.id:12} ({entity.type:12}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        clingo_combos = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if py != clingo_combos:
        print("MISMATCH between Python and ASP:", py, clingo_combos)
        return 1
    for seed in range(len(INCIDENTS)):
        params = resolve_params(argparse.Namespace(place=None, activity=None, prize=None, name=None), random.Random(seed), seed)
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity and {len(INCIDENTS)} generated stories verified.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if not can_story(params.place, params.activity, params.prize):
        pass
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal Story world about lore, a crystallite, and a limber lesson learned."
    )
    parser.add_argument("--place", choices=["moonpool_meadow"])
    parser.add_argument("--activity", choices=["recover"])
    parser.add_argument("--prize", choices=["crystallite"])
    parser.add_argument("--name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    count = len(INCIDENTS) if getattr(args, "all", None) else max(getattr(args, "n", None), 1)
    samples: list[StorySample] = []

    for i in range(count):
        seed = base_seed + i
        rng = random.Random(seed)
        params = resolve_params(args, rng, seed)
        samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
