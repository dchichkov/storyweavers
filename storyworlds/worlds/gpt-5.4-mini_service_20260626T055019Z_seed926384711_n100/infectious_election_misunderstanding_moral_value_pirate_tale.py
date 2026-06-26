#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/infectious_election_misunderstanding_moral_value_pirate_tale.py
==========================================================================================================

A small pirate-tale story world about an election that goes wrong because of a
misunderstanding, then turns on a moral choice that settles the crew.

Premise:
- A pirate crew is docked at a tiny island port.
- They are holding an election for who will steer the ship on the next voyage.
- A rumor about something "infectious" spreads through the deckhands.
- The rumor causes a misunderstanding about who is allowed to vote and why.

Tension:
- The crew thinks the election itself might be unsafe or unfair.
- A character interprets the rumor as proof that one person should be excluded.
- The captain has to decide whether to let fear guide the vote.

Turn:
- The misunderstanding is explained.
- The crew recognizes that the infectious thing is not a curse or secret plot,
  but a simple sickness alert / caution that needs care, not blame.

Resolution:
- The crew chooses a moral value: fairness and kindness.
- The election is held cleanly and everyone eligible votes.
- The ending image shows the ship ready to sail with trust restored.

This script follows the Storyweavers contract:
- self-contained stdlib script
- eagerly imports results.py
- lazy ASP import inside helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    voted_for: Optional[str] = None
    is_voter: bool = False
    is_candidate: bool = False
    in_quarantine: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    challenger: object | None = None
    mate: object | None = None
    rumor_ent: object | None = None
    value_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess"}
        male = {"boy", "man", "father", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    place: str
    harbors: bool = False
    affords: set[str] = field(default_factory=set)
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
class CrewRole:
    id: str
    title: str
    trait: str
    can_vote: bool = True
    speaks_for: str = ""
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
class Rumor:
    id: str
    word: str
    true_meaning: str
    effect: str
    spreads_as: str
    false_guess: str
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
class MoralValue:
    id: str
    label: str
    lesson: str
    action: str
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
        self.rumor_active: bool = False
        self.vote_open: bool = False
        self.misunderstood: bool = False
        self.election_done: bool = False
        self.winner: Optional[str] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.rumor_active = self.rumor_active
        clone.vote_open = self.vote_open
        clone.misunderstood = self.misunderstood
        clone.election_done = self.election_done
        clone.winner = self.winner
        return clone


SETTINGS = {
    "dock": Setting(place="the dock", harbors=True, affords={"election"}),
    "ship": Setting(place="the ship", harbors=False, affords={"election"}),
    "island": Setting(place="the island port", harbors=True, affords={"election"}),
}

ROLES = {
    "captain": CrewRole(id="captain", title="captain", trait="steady"),
    "first_mate": CrewRole(id="first_mate", title="first mate", trait="brave"),
    "boatswain": CrewRole(id="boatswain", title="boatswain", trait="quick"),
    "cook": CrewRole(id="cook", title="cook", trait="kind"),
}

RUMORS = {
    "infectious": Rumor(
        id="infectious",
        word="infectious",
        true_meaning="a sickness warning that can spread from person to person if they crowd too close",
        effect="made the crew nervous about gathering",
        spreads_as="a whispered warning",
        false_guess="a curse or a secret plot",
    ),
}

MORAL_VALUES = {
    "fairness": MoralValue(
        id="fairness",
        label="fairness",
        lesson="everyone who belongs should get a real chance to vote",
        action="keep the election open and honest",
    ),
    "kindness": MoralValue(
        id="kindness",
        label="kindness",
        lesson="fear should not turn into blame",
        action="listen before accusing anyone",
    ),
    "courage": MoralValue(
        id="courage",
        label="courage",
        lesson="a crew can do the right thing even when it feels awkward",
        action="speak the truth plainly",
    ),
}

NAMES = {
    "captain": ["Mara", "Nell", "Rook", "Sable", "Ivy"],
    "first_mate": ["Jory", "Finn", "Bram", "Tide", "Quill"],
    "boatswain": ["Pip", "Cove", "Merrin", "Jax", "Roam"],
    "cook": ["Wren", "Mina", "Bix", "Lark", "Suri"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for role_id in ROLES:
            for moral_id in MORAL_VALUES:
                if "election" in setting.affords:
                    combos.append((place, role_id, moral_id))
    return combos


@dataclass
class StoryParams:
    place: str
    leader: str
    challenger: str
    rumor: str
    moral: str
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


def tell(setting: Setting, leader_role: CrewRole, challenger_role: CrewRole,
         rumor: Rumor, moral: MoralValue, leader_name: str, challenger_name: str) -> World:
    world = World(setting)

    captain = world.add(Entity(
        id=leader_name,
        kind="character",
        type="captain",
        label="captain",
        traits=["little", leader_role.trait, "careful"],
        is_voter=True,
    ))
    challenger = world.add(Entity(
        id=challenger_name,
        kind="character",
        type="pirate",
        label=challenger_role.title,
        traits=["little", challenger_role.trait, "bold"],
        is_voter=True,
        is_candidate=True,
    ))
    mate = world.add(Entity(
        id="CrewMate",
        kind="character",
        type="pirate",
        label="crew mate",
        traits=["little", "busy", "watchful"],
        is_voter=True,
    ))
    rumor_ent = world.add(Entity(
        id=rumor.id,
        kind="thing",
        type="rumor",
        label=rumor.word,
        phrase=rumor.true_meaning,
    ))
    value_ent = world.add(Entity(
        id=moral.id,
        kind="thing",
        type="moral_value",
        label=moral.label,
        phrase=moral.lesson,
    ))

    world.say(f"{captain.id} was a little steady captain who kept the ship neat and the crew listening.")
    world.say(f"{challenger.id} was the {challenger_role.title} with a brave grin and a loud laugh.")
    world.say(f"The crew knew the word {rumor.word}, but not everyone knew what it truly meant.")
    world.say(f"On the island port, they were preparing an election so the ship could choose its next steering voice.")

    world.para()
    world.vote_open = True
    world.say(f"At {setting.place}, the pirates gathered around a crate for the election.")
    world.say(f"Then someone whispered that the {rumor.word} warning was spreading.")
    world.rumor_active = True
    world.say(f"The whisper made the deck feel tight, because the rumor sounded like {rumor.false_guess}.")

    if rumor.id == "infectious":
        world.misunderstood = True
        captain.memes["worry"] = captain.memes.get("worry", 0) + 1
        challenger.memes["hurt"] = challenger.memes.get("hurt", 0) + 1
        world.say(
            f"Some pirates thought that because something was infectious, the election itself must be unsafe."
        )
        world.say(
            f"One worried mate even said {challenger.id} should be kept away, as if caution meant exile."
        )
        challenger.in_quarantine = False

    world.para()
    world.say(
        f"{captain.id} lifted a hand and asked the crew to stop and think."
    )
    world.say(
        f"{captain.id} explained that infectious did not mean cursed; it meant the crew should take care and not crowd together."
    )
    world.say(
        f"That cleared the misunderstanding, and the crew saw that fear had been steering the talk more than truth."
    )
    world.say(
        f"Then they chose {moral.label}: {moral.lesson}."
    )

    world.election_done = True
    captain.memes["trust"] = captain.memes.get("trust", 0) + 1
    challenger.memes["trust"] = challenger.memes.get("trust", 0) + 1
    mate.memes["relief"] = mate.memes.get("relief", 0) + 1
    world.winner = challenger.id
    challenger.voted_for = challenger.id
    captain.voted_for = challenger.id
    mate.voted_for = challenger.id

    world.say(
        f"The pirates held the election cleanly, with space between them and honest votes counted one by one."
    )
    world.say(
        f"{challenger.id} won the steering role, not because of noise, but because the crew chose fairness over rumor."
    )
    world.say(
        f"By sunset, the ship was ready to sail, and the deck felt lighter than a gull's wing."
    )

    world.facts.update(
        setting=setting,
        leader=captain,
        challenger=challenger,
        mate=mate,
        rumor=rumor_ent,
        moral=value_ent,
        rumor_def=rumor,
        moral_def=moral,
        misunderstood=world.misunderstood,
        election_done=world.election_done,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the word "{f["rumor_def"].word}" and ends with a fair election.',
        f"Tell a short story about pirates at {f['setting'].place} who misunderstand something infectious and then choose {f['moral_def'].label}.",
        f"Write a gentle pirate story where a crew fixes a misunderstanding about an election and everyone learns to be fair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    leader = _safe_fact(world, f, "leader")
    challenger = _safe_fact(world, f, "challenger")
    rumor = _safe_fact(world, f, "rumor_def")
    moral = _safe_fact(world, f, "moral_def")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"What kind of event were the pirates holding at {place}?",
            answer="They were holding an election to choose who would steer the ship next.",
        ),
        QAItem(
            question=f"What did the word {rumor.word} make some pirates wrongly think?",
            answer=f"They wrongly thought the election itself was unsafe or that someone should be blamed, but that was a misunderstanding.",
        ),
        QAItem(
            question=f"How did {leader.id} help the crew after the misunderstanding?",
            answer=f"{leader.id} explained the real meaning of the warning and reminded the crew to act with {moral.label}.",
        ),
        QAItem(
            question=f"Who won the election in the end?",
            answer=f"{challenger.id} won the election after the crew chose fairness over fear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an election?",
            answer="An election is a way for people to choose someone by voting.",
        ),
        QAItem(
            question="What does infectious mean?",
            answer="Infectious means something can spread from one person to another, like a sickness or a warning that makes people careful.",
        ),
        QAItem(
            question="What is fairness?",
            answer="Fairness means treating people in a just way and giving everyone a proper chance.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.voted_for:
            bits.append(f"voted_for={e.voted_for}")
        if e.is_voter:
            bits.append("voter=True")
        if e.is_candidate:
            bits.append("candidate=True")
        if e.in_quarantine:
            bits.append("quarantine=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  rumor_active={world.rumor_active} vote_open={world.vote_open} misunderstood={world.misunderstood}")
    lines.append(f"  election_done={world.election_done} winner={world.winner}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="dock", leader="captain", challenger="first_mate", rumor="infectious", moral="fairness"),
    StoryParams(place="ship", leader="captain", challenger="cook", rumor="infectious", moral="kindness"),
    StoryParams(place="island", leader="captain", challenger="boatswain", rumor="infectious", moral="courage"),
]


def explain_rejection(place: str) -> str:
    return f"(No story: {place} cannot host the election in this little pirate tale.)"


def valid_story(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.leader in ROLES and params.challenger in ROLES and params.moral in MORAL_VALUES and params.rumor in RUMORS


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.harbors:
            lines.append(asp.fact("harbor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for rid in ROLES:
        lines.append(asp.fact("role", rid))
    for rid, r in RUMORS.items():
        lines.append(asp.fact("rumor", rid))
        lines.append(asp.fact("spreads_as", rid, r.spreads_as))
    for mid, m in MORAL_VALUES.items():
        lines.append(asp.fact("moral", mid))
        lines.append(asp.fact("lesson", mid, m.action))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, L, C, R, M) :- affords(P, election), role(L), role(C), rumor(R), moral(M), L != C.
misunderstanding(R) :- rumor(R).
election_event(P) :- affords(P, election).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, l, c, r, m) for (p, l, c) in valid_combos() for r in RUMORS for m in MORAL_VALUES}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_story() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate tale story world about an infectious misunderstanding and a fair election."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--leader", choices=ROLES)
    ap.add_argument("--challenger", choices=ROLES)
    ap.add_argument("--rumor", choices=RUMORS)
    ap.add_argument("--moral", choices=MORAL_VALUES)
    ap.add_argument("--name")
    ap.add_argument("--name2")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "leader", None) is None or c[1] == getattr(args, "leader", None))
              and (getattr(args, "challenger", None) is None or c[2] == getattr(args, "challenger", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, leader, challenger = rng.choice(list(combos))
    rumor = getattr(args, "rumor", None) or "infectious"
    moral = getattr(args, "moral", None) or rng.choice(sorted(MORAL_VALUES))
    return StoryParams(place=place, leader=leader, challenger=challenger, rumor=rumor, moral=moral)


def generate(params: StoryParams) -> StorySample:
    leader_name = params.name or random.choice(_safe_lookup(NAMES, params.leader))
    challenger_name = params.name2 or random.choice(_safe_lookup(NAMES, params.challenger))
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ROLES, params.leader),
        _safe_lookup(ROLES, params.challenger),
        _safe_lookup(RUMORS, params.rumor),
        _safe_lookup(MORAL_VALUES, params.moral),
        leader_name,
        challenger_name,
    )
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
        print(asp_program("#show valid_story/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combos:\n")
        for item in stories:
            print("  ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.place}: {p.leader} vs {p.challenger} ({p.rumor}, {p.moral})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
