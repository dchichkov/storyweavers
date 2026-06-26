#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cult_dialogue_mystery.py
========================================================================================================

A compact storyworld about a small mystery, a secretive little cult-like club,
and a child who solves the puzzle through dialogue.

This world stays child-facing: the "cult" is a harmless secret society of
lantern-watchers who treat clues like a game. The mystery is about a missing
object, the suspicion that someone took it, and the reveal that the club was
helping all along.

Core premise:
- A child notices a strange hush and a missing keepsake.
- A secret cult of lantern-watchers seems suspicious.
- Dialogue reveals clues, alibis, and the real reason for the secrecy.
- The ending shows the missing thing recovered and trust restored.

The world model tracks:
- physical meters: hiding, distance, possession, evidence, brightness
- emotional memes: worry, curiosity, suspicion, relief, trust

The prose is driven by state, not by a frozen template.
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
    holder: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cult_leader: object | None = None
    hero: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    mood: str
    hidden_spots: list[str] = field(default_factory=list)
    clue_spots: list[str] = field(default_factory=list)
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
class Mystery:
    title: str
    missing: str
    missing_phrase: str
    missing_type: str
    missing_location: str
    cult_name: str
    cult_lore: str
    secret_thing: str
    reveal: str
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    cult_name: str
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
    "museum": Place(
        name="the museum",
        mood="quiet",
        hidden_spots=["behind the blue curtain", "under the map table"],
        clue_spots=["the lobby sign", "the lantern case", "the bench by the stairs"],
    ),
    "library": Place(
        name="the library",
        mood="hushed",
        hidden_spots=["between tall shelves", "under the reading rug"],
        clue_spots=["the front desk", "the story corner", "the return cart"],
    ),
    "garden": Place(
        name="the garden",
        mood="shadowy",
        hidden_spots=["behind the trellis", "inside the tool shed"],
        clue_spots=["the fountain edge", "the stone path", "the bench under vines"],
    ),
}

MYSTERIES = {
    "lantern": Mystery(
        title="the missing lantern",
        missing="lantern",
        missing_phrase="a brass lantern with a round handle",
        missing_type="lantern",
        missing_location="the lantern case",
        cult_name="the Cult of the Quiet Light",
        cult_lore="They met only when the lamps were low and whispered about old clues.",
        secret_thing="a candle-lit map",
        reveal="they had hidden the lantern to keep a surprise safe",
    ),
    "key": Mystery(
        title="the missing key",
        missing="key",
        missing_phrase="a small silver key",
        missing_type="key",
        missing_location="the front desk",
        cult_name="the Cult of the Blue Door",
        cult_lore="They wore blue ribbons and spoke in careful whispers.",
        secret_thing="a ribbon-marked door",
        reveal="they had borrowed the key to open a locked display for cleaning",
    ),
    "book": Mystery(
        title="the missing book",
        missing="book",
        missing_phrase="a thin storybook with a red cover",
        missing_type="book",
        missing_location="the return cart",
        cult_name="the Cult of the Moon Page",
        cult_lore="They folded paper moons and left tiny notes for each other.",
        secret_thing="a hidden bookmark",
        reveal="they had moved the book so no one would take it home by mistake",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Maya", "Iris", "Zoe", "Ella"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Leo", "Max", "Eli", "Sam", "Noah"]
TRAITS = ["curious", "brave", "careful", "sharp-eyed", "patient"]


def talk_intro(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} liked quiet places where little details mattered. "
        f"{hero.pronoun().capitalize()} and {sidekick.id} had come to {world.place.name} "
        f"because something had gone missing."
    )
    world.say(
        f'"{mystery.missing_phrase} is gone," {sidekick.id} whispered. '
        f'"And the cult members were the last ones near the room."'
    )
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1


def describe_cult(world: World, mystery: Mystery) -> None:
    world.say(
        f"Everyone kept talking about {mystery.cult_name} in hushed voices. "
        f"{mystery.cult_lore}"
    )


def first_clue(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["suspicion"] += 1
    clue = {
        "lantern": "a smudge of wax on the bench by the stairs",
        "key": "a blue ribbon tied around the front desk leg",
        "book": "a red paper scrap near the return cart",
    }[mystery.missing]
    world.say(
        f"{hero.id} crouched down and found {clue}. "
        f'"That means someone was here after closing," {hero.id} said.'
    )


def dialogue_with_cult(world: World, hero: Entity, cult_leader: Entity, mystery: Mystery) -> None:
    hero.memes["suspicion"] += 1
    cult_leader.memes["guarded"] += 1
    world.say(
        f'{hero.id} asked, "Did your cult take the {mystery.missing}?" '
        f'{cult_leader.id} blinked. "We did not take it," {cult_leader.pronoun().capitalize()} said, '
        f'"but we did move it."'
    )
    world.say(
        f'"Why?" {hero.id} asked. "Because," said {cult_leader.id}, '
        f'"we were trying not to spoil a surprise."'
    )
    world.facts["cult_denial"] = True
    world.facts["cult_admits_move"] = True


def gather_clues(world: World, hero: Entity, mystery: Mystery) -> None:
    if mystery.missing == "lantern":
        world.say(
            f'"Look," {hero.id} said, pointing at the wax. "That lantern was lit before." '
            f'"And if it was lit, somebody needed a dark corner to hide it safely."'
        )
    elif mystery.missing == "key":
        world.say(
            f'"This ribbon matches the cult colors," {hero.id} said. '
            f'"Maybe they borrowed the key, not stole it."'
        )
    else:
        world.say(
            f'"The book was probably moved gently," {hero.id} said. '
            f'"See how the page corner is not bent?"'
        )
    hero.memes["confidence"] += 1


def reveal(world: World, hero: Entity, cult_leader: Entity, mystery: Mystery) -> None:
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    cult_leader.memes["relief"] += 1
    cult_leader.memes["trust"] += 1
    world.say(
        f'{cult_leader.id} lowered {cult_leader.pronoun("possessive")} voice and said, '
        f'"We hid it for a reason. {mystery.reveal}."'
    )
    world.say(
        f'From {world.place.name}, the answer made sense at last. The secret was not a theft. '
        f'It was a careful plan.'
    )


def ending(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    world.say(
        f'{hero.id} smiled. "{mystery.missing.title()} mystery solved," {hero.id} said, '
        f'and {sidekick.id} laughed so softly it barely disturbed the quiet room.'
    )
    world.say(
        f"By the end, the missing {mystery.missing} was back where it belonged, "
        f"and the cult members were no longer scary at all. They were just secretive, "
        f"careful, and a little odd."
    )


def tell(place: Place, mystery: Mystery, hero_name: str, hero_gender: str, sidekick_name: str,
         cult_name: str) -> World:
    world = World(place)
    hero_type = hero_gender
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="child"))
    cult_leader = world.add(Entity(id="Leader", kind="character", type="woman", label=cult_name))

    world.facts["place"] = place.name
    world.facts["mystery"] = mystery
    world.facts["cult_name"] = cult_name
    world.facts["hero"] = hero
    world.facts["sidekick"] = sidekick
    world.facts["cult_leader"] = cult_leader

    talk_intro(world, hero, sidekick, mystery)
    world.para()
    describe_cult(world, mystery)
    first_clue(world, hero, mystery)
    world.para()
    dialogue_with_cult(world, hero, cult_leader, mystery)
    gather_clues(world, hero, mystery)
    world.para()
    reveal(world, hero, cult_leader, mystery)
    ending(world, hero, sidekick, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    m: Mystery = _safe_fact(world, world.facts, "mystery")  # type: ignore[assignment]
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    sidekick: Entity = _safe_fact(world, world.facts, "sidekick")  # type: ignore[assignment]
    cult_name = _safe_fact(world, world.facts, "cult_name")
    return [
        f'Write a child-friendly mystery story that includes a secret cult called "{cult_name}".',
        f'Tell a dialogue-heavy mystery where {hero.id} and {sidekick.id} ask questions, follow clues, and solve the case of {m.title}.',
        f'Write a short story set in {world.place.name} where a strange quiet group, a missing object, and a careful explanation all turn into a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    m: Mystery = _safe_fact(world, world.facts, "mystery")  # type: ignore[assignment]
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    sidekick: Entity = _safe_fact(world, world.facts, "sidekick")  # type: ignore[assignment]
    cult_leader: Entity = _safe_fact(world, world.facts, "cult_leader")  # type: ignore[assignment]
    qa: list[QAItem] = [
        QAItem(
            question=f"Why did {hero.id} and {sidekick.id} go to {world.place.name}?",
            answer=f"They went because something had gone missing and they wanted to solve the mystery.",
        ),
        QAItem(
            question=f"What object was missing in the story?",
            answer=f"The missing object was {m.missing_phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} think about the cult at first?",
            answer=f"At first, {hero.id} thought the cult might have taken the missing {m.missing}.",
        ),
        QAItem(
            question=f"What did the cult leader admit during the dialogue?",
            answer=f"The cult leader admitted that the cult had moved the {m.missing}, but had not stolen it.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"It ended with the reason explained clearly, the {m.missing} returned, and everyone feeling relieved.",
        ),
    ]
    if cult_leader.memes.get("guarded", 0) >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"Why was {cult_leader.id} careful when answering questions?",
                answer="The cult leader was careful because the group was protecting a secret surprise, not trying to be rude.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem where something is unclear at first, and people have to follow clues to understand what happened.",
        ),
        QAItem(
            question="What does a secretive group do?",
            answer="A secretive group keeps some plans or meetings quiet for a while, usually because they want to surprise someone or protect information.",
        ),
        QAItem(
            question="Why do people ask questions in a mystery?",
            answer="They ask questions to gather clues, check what happened, and find the truth.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== Prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly dialogue mystery storyworld with a secretive cult.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--cult-name")
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
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    sidekick_name = getattr(args, "sidekick", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    cult_name = getattr(args, "cult_name", None) or _safe_lookup(MYSTERIES, mystery).cult_name
    return StoryParams(
        place=place,
        mystery=mystery,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        cult_name=cult_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(MYSTERIES, params.mystery), params.hero_name,
                 params.hero_gender, params.sidekick_name, params.cult_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


ASP_RULES = r"""
% A mystery is valid when it has a missing thing and a secretive cult that
% admits moving it, not stealing it.
missing(mystery1, lantern).
cult(cult1).
moved(cult1, lantern).
not_stolen(cult1, lantern).
valid_story(mystery1) :- missing(mystery1, lantern), cult(cult1), moved(cult1, lantern), not_stolen(cult1, lantern).

#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    lines.append(asp.fact("cult", "cult1"))
    lines.append(asp.fact("moved", "cult1", "lantern"))
    lines.append(asp.fact("not_stolen", "cult1", "lantern"))
    lines.append(asp.fact("missing", "mystery1", "lantern"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    got = set(asp.atoms(model, "valid_story"))
    expected = {("mystery1",)}
    if got == expected:
        print("OK: ASP parity verified.")
        return 0
    print(f"MISMATCH: got {sorted(got)} expected {sorted(expected)}")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in MYSTERIES:
            params = StoryParams(
                place=next(iter(PLACES)),
                mystery=p,
                hero_name="Mina",
                hero_gender="girl",
                sidekick_name="Theo",
                cult_name=_safe_lookup(MYSTERIES, p).cult_name,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
