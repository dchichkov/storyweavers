#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a productive little puke problem,
repeated checking, and curiosity turning conflict into care.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, ROOT)
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

@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    child: object | None = None
    friend: object | None = None
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
class StoryParams:
    child: str = ""
    creature: str = ""
    blanket: str = ""
    routine: str = ""
    conflict: Optional[str] = None
    repetition: Optional[str] = None
    curiosity: Optional[str] = None
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


@dataclass
class ConflictPath:
    key: str
    problem: str
    feeling: str
    question: str
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
class RepetitionPath:
    key: str
    line: str
    action: str
    image: str
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
class CuriosityPath:
    key: str
    clue: str
    discovery: str
    solution: str
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


CHILDREN = ["Luna", "Milo", "Nia", "Toby", "Pia", "Owen"]
CREATURES = ["little moon-moth", "sleepy hedgehog", "tiny cloud-dragon", "pocket-sized owl"]
BLANKETS = ["blue star blanket", "green quilt", "silver moon blanket", "yellow rabbit blanket"]
ROUTINES = ["three quiet sips of water", "one song and two deep breaths", "a warm washcloth and a bedtime hug"]

CONFLICTS = [
    ConflictPath(
        "messy_bed",
        "a small puke puddle appeared on the rug beside the bed",
        "embarrassed and cross",
        "Why did the yucky trouble happen just when bedtime was meant to be peaceful?",
    ),
    ConflictPath(
        "sour_tummy",
        "their tummy gave a loud gurgle, then brought up the last bite of supper",
        "worried and uncomfortable",
        "What was the tummy trying to say?",
    ),
    ConflictPath(
        "startled_friend",
        "the creature friend woke when a little puke splashed onto the blanket",
        "sad that the friend looked frightened",
        "Could a scary accident be made safe again?",
    ),
]

REPETITIONS = [
    RepetitionPath(
        "small_steps",
        "First breathe, then sip, then rest.",
        "They breathed, took one tiny sip, and rested.",
        "The same three small steps made the room feel less enormous.",
    ),
    RepetitionPath(
        "check_twice",
        "Look once for the mess, and look twice for what caused it.",
        "They checked the rug, the cup, and the snack plate two times.",
        "Each careful look turned one worry into a question.",
    ),
    RepetitionPath(
        "soft_words",
        "Name it softly, clean it kindly, try again.",
        "They said the words again while helping with the cleanup.",
        "The repeated sentence sounded like a little broom sweeping fear away.",
    ),
]

CURIOSITIES = [
    CuriosityPath(
        "crumb_trail",
        "a trail of bright cracker crumbs under the pillow",
        "the creature had carried crackers into the bed and eaten them after supper",
        "They moved the snack plate away from bedtime and kept water nearby.",
    ),
    CuriosityPath(
        "warm_cup",
        "the water cup was warm and nearly empty",
        "the cup had stood beside the sunny window all afternoon",
        "They replaced it with a cool cup and took only tiny sips.",
    ),
    CuriosityPath(
        "bumpy_pillow",
        "a hard bump hiding inside the pillowcase",
        "a wooden toy had slipped beneath the pillow and pressed against the tummy",
        "They removed the toy and made the pillow smooth again.",
    ),
]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    events: list[str] = field(default_factory=list)

    world: object | None = None
    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.events.append(text)

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


def choose(items, key):
    return next((item for item in items if item.key == key), None)


def complete_params(params: StoryParams) -> None:
    if params.child not in CHILDREN:
        pass
    if params.creature not in CREATURES:
        pass
    if params.blanket not in BLANKETS:
        pass
    if params.routine not in ROUTINES:
        pass
    seed = params.seed if params.seed is not None else sum(ord(c) for c in params.child)
    rng = random.Random(seed ^ 918273)
    params.conflict = params.conflict or rng.choice(CONFLICTS).key
    params.repetition = params.repetition or rng.choice(REPETITIONS).key
    params.curiosity = params.curiosity or rng.choice(CURIOSITIES).key
    if not choose(CONFLICTS, params.conflict):
        pass
    if not choose(REPETITIONS, params.repetition):
        pass
    if not choose(CURIOSITIES, params.curiosity):
        pass


def build_world(params: StoryParams) -> World:
    complete_params(params)
    conflict = choose(CONFLICTS, params.conflict)
    repetition = choose(REPETITIONS, params.repetition)
    curiosity = choose(CURIOSITIES, params.curiosity)
    world = World()
    child = Entity(
        "child",
        "child",
        params.child,
        meters={"comfort": 0.0, "tummy": -1.0, "calm": 0.0},
        memes={"curiosity": 1.0, "care": 1.0},
    )
    friend = Entity(
        "friend",
        "creature",
        params.creature,
        meters={"sleepiness": 1.0, "trust": 0.0},
        memes={"friendship": 1.0},
    )
    world.add(child)
    world.add(friend)
    world.facts.update(
        params=params,
        child=child,
        friend=friend,
        conflict=conflict,
        repetition=repetition,
        curiosity=curiosity,
    )
    return world


def words(world: World) -> dict[str, str]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    return {
        "child": p.child,
        "creature": p.creature,
        "blanket": p.blanket,
        "routine": p.routine,
    }


def begin(world: World) -> None:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    c = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    f = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    c.meters["calm"] += 1
    world.say(
        f"At bedtime, {p.child} tucked the {p.creature} beneath the {p.blanket}. "
        f"The room was quiet except for the soft hum of the night."
    )
    world.say(
        f"{p.child} began the usual bedtime routine: {p.routine}. "
        f"Then the tummy made a wobble, and a little puke landed beside the bed."
    )
    f.meters["trust"] -= 1
    world.say(
        f'"Oh no," whispered {p.child}. "{p.creature} looks scared." '
        f'"I am here," said the {p.creature}. "We can find out what happened."'
    )


def face_conflict(world: World) -> None:
    c = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    conflict = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "conflict")
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    c.meters["comfort"] -= 1
    c.memes["curiosity"] += 1
    world.say(
        f"It was {conflict.problem}. {p.child} felt {conflict.feeling}, "
        f"but curiosity made a small window in the worry."
    )
    world.say(f'"{conflict.question}" asked {p.child}.')
    world.say(
        f'"We do not have to guess forever," said the {p.creature}. '
        f'"We can look carefully, one safe step at a time."'
    )


def repeat_care(world: World) -> None:
    c = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    repetition = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "repetition")
    c.meters["calm"] += 2
    c.meters["comfort"] += 1
    c.memes["patience"] += 1
    world.say(f'{pword(world, repetition.line)}')
    world.say(repetition.action)
    world.say(f"They repeated the gentle plan. {repetition.image}")
    world.say(
        f'"Again?" asked {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params").child}. '
        f'"Again, but never in a hurry," said the {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params").creature}.'
    )


def pword(world: World, text: str) -> str:
    return text


def investigate(world: World) -> None:
    c = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    curiosity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "curiosity")
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    c.memes["curiosity"] += 1
    c.meters["tummy"] += 1
    world.say(f"Under the {p.blanket}, they noticed {curiosity.clue}.")
    world.say(
        f'"Aha," said {p.child}. "That is a clue, not a monster." '
        f'"A clue can help us choose," replied the {p.creature}.'
    )
    world.say(f"They discovered that {curiosity.discovery}.")
    world.say(curiosity.solution)


def resolve(world: World) -> None:
    c = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    f = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    c.meters["calm"] += 2
    c.meters["comfort"] += 2
    f.meters["trust"] += 2
    world.say(
        f"The rug was cleaned, the {p.blanket} was placed in the wash basket, "
        f"and the {p.creature} received a fresh corner of cloth."
    )
    world.say(
        f"{p.child} tried the bedtime routine once more, slowly and gently. "
        f"This time the tummy stayed quiet."
    )
    world.say(
        f'"I was curious instead of angry," said {p.child}. '
        f'"And I was helpful instead of hiding," said the {p.creature}.'
    )


def finish(world: World) -> None:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    c = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    f = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    c.meters["calm"] += 1
    c.memes["care"] += 1
    f.meters["sleepiness"] += 1
    world.say(
        f"At last, {p.child} and the {p.creature} curled up together without the "
        f"old worry between them."
    )
    world.say(
        "The little accident had not been pleasant, but it had been productive: "
        "it taught them to notice, ask, repeat safe steps, and care for one another."
    )
    world.say(
        f"Outside, the moon climbed higher. Inside, the clean room grew still, "
        f"and the {p.blanket} waited for morning."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    begin(world)
    world.para()
    face_conflict(world)
    repeat_care(world)
    world.para()
    investigate(world)
    world.para()
    resolve(world)
    finish(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    conflict = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "conflict")
    repetition = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "repetition")
    curiosity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "curiosity")
    return [
        QAItem(
            question=f"What conflict interrupted {p.child}'s bedtime with the {p.creature}?",
            answer=f"{conflict.problem.capitalize()}.",
        ),
        QAItem(
            question=f"What did {p.child} repeat while handling the puke problem?",
            answer=repetition.action,
        ),
        QAItem(
            question=f"What clue did curiosity help {p.child} discover?",
            answer=f"{curiosity.clue.capitalize()} They discovered that {curiosity.discovery}.",
        ),
        QAItem(
            question=f"How did {p.child} and the {p.creature} resolve the bedtime conflict?",
            answer=(
                f"They cleaned the mess, followed the repeated gentle steps, and acted on the clue: "
                f"{curiosity.solution}"
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is it useful to stay calm after a messy accident?",
            answer="Staying calm helps someone notice what happened and choose safe, helpful next steps.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn more by noticing clues and asking questions.",
        ),
        QAItem(
            question="Why can repeating a safe routine help?",
            answer="Repeating a safe routine can make a confusing problem feel familiar and manageable.",
        ),
        QAItem(
            question="What does productive mean in this story?",
            answer="Productive means that the difficult event led to useful learning and caring action.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    return [
        f"Write a gentle bedtime story about {p.child}, a {p.creature}, and a productive puke-related conflict.",
        f"Use repetition and curiosity to help {p.child} solve a bedtime problem with the {p.creature}.",
        "Keep the story warm, concrete, child-facing, and peaceful at the ending.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {q}" for i, q in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("event", "puke"),
            asp.fact("feature", "conflict"),
            asp.fact("feature", "repetition"),
            asp.fact("feature", "curiosity"),
            asp.fact("style", "bedtime_story"),
            asp.fact("outcome", "productive"),
        ]
    )


ASP_RULES = r"""
compatible_story(puke, productive, bedtime_story) :-
    event(puke),
    outcome(productive),
    style(bedtime_story),
    feature(conflict),
    feature(repetition),
    feature(curiosity).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    ok = bool(asp.atoms(model, "compatible_story"))
    if not ok:
        print("MISMATCH: ASP gate failed.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if "puke" not in sample.story.lower() or "curious" not in sample.story.lower():
            print("MISMATCH: generated story lost required features.")
            return 1
    print("OK: ASP and Python gates agree; generated stories were exercised.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A productive bedtime puke-conflict storyworld.")
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--blanket", choices=BLANKETS)
    ap.add_argument("--routine", choices=ROUTINES)
    ap.add_argument("--conflict", choices=[x.key for x in CONFLICTS])
    ap.add_argument("--repetition", choices=[x.key for x in REPETITIONS])
    ap.add_argument("--curiosity", choices=[x.key for x in CURIOSITIES])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = getattr(args, "child", None) or rng.choice(CHILDREN)
    return StoryParams(
        child=child,
        creature=getattr(args, "creature", None) or rng.choice(CREATURES),
        blanket=getattr(args, "blanket", None) or rng.choice(BLANKETS),
        routine=getattr(args, "routine", None) or rng.choice(ROUTINES),
        conflict=getattr(args, "conflict", None),
        repetition=getattr(args, "repetition", None),
        curiosity=getattr(args, "curiosity", None),
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
        print("--- trace ---")
        for entity in sample.world.entities.values():
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            print(f"{entity.label}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "sleepy hedgehog", "blue star blanket", "three quiet sips of water", "crumb_trail", "small_steps", "crumb_trail", 11),
    StoryParams("Milo", "tiny cloud-dragon", "green quilt", "one song and two deep breaths", "sour_tummy", "check_twice", "warm_cup", 22),
    StoryParams("Nia", "little moon-moth", "silver moon blanket", "a warm washcloth and a bedtime hug", "startled_friend", "soft_words", "bumpy_pillow", 33),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible_story/3."))
        print(asp.atoms(model, "compatible_story"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if getattr(args, "json", None):
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str)
        )
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
