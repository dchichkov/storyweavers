#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/score_problem_solving_sharing_rhyming_story.py
===============================================================================================================

A standalone storyworld for a tiny rhyming tale about score, sharing, and
problem solving.

Premise:
- Two children are playing a little scoring game.
- A problem appears: they cannot keep score well because their paper can blow
  away or their marker can go missing.
- They solve it by sharing the needed gear and working together.

The world is small, state-driven, and written to read like a complete child-facing
rhyming story.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    marker: object | None = None
    paper: object | None = None
    weight: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    feels: str
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
class Game:
    id: str
    name: str
    verb: str
    gerund: str
    sound: str
    score_goal: int
    needs: set[str]
    rhyme: str
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
class HelpfulItem:
    id: str
    label: str
    phrase: str
    fix: str
    shared: bool = True
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for giver in world.characters():
        for receiver in world.characters():
            if giver.id == receiver.id:
                continue
            sig = ("share", giver.id, receiver.id)
            if sig in world.fired:
                continue
            if giver.memes.get("sharing", 0) >= THRESHOLD and receiver.memes.get("need_help", 0) >= THRESHOLD:
                world.fired.add(sig)
                receiver.memes["hope"] = receiver.memes.get("hope", 0) + 1
                giver.memes["teamwork"] = giver.memes.get("teamwork", 0) + 1
                out.append(f"They shared the needed thing with a smile so bright.")
    return out


def _r_problem_solve(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("problem_solved"):
        return out
    if world.facts.get("paper_kept") and world.facts.get("marker_shared"):
        world.facts["problem_solved"] = True
        out.append("The tricky game was fixed just right.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_share, _r_problem_solve):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "yard": Setting(place="the yard", feels="bright and breezy", affords={"toss"}),
    "porch": Setting(place="the porch", feels="small and cozy", affords={"toss"}),
    "park_bench": Setting(place="the park bench", feels="sunny and warm", affords={"toss"}),
}

GAMES = {
    "bean_toss": Game(
        id="bean_toss",
        name="beanbag toss",
        verb="toss the beanbag",
        gerund="tossing beanbags",
        sound="thump",
        score_goal=5,
        needs={"paper", "marker"},
        rhyme="high and spry",
    ),
    "ring_toss": Game(
        id="ring_toss",
        name="ring toss",
        verb="toss the ring",
        gerund="tossing rings",
        sound="clink",
        score_goal=4,
        needs={"paper", "marker"},
        rhyme="near and clear",
    ),
}

HELPFUL_ITEMS = {
    "blue_marker": HelpfulItem(
        id="blue_marker",
        label="blue marker",
        phrase="a blue marker",
        fix="write the score numbers",
    ),
    "paper_weight": HelpfulItem(
        id="paper_weight",
        label="paper weight",
        phrase="a smooth little paper weight",
        fix="hold the score sheet still",
    ),
}

NAMES = ["Maya", "Noah", "Luna", "Eli", "Zoe", "Ben", "Iris", "Theo"]
TRAITS = ["cheerful", "curious", "brave", "gentle", "spry", "playful"]


@dataclass
class StoryParams:
    place: str
    game: str
    name_a: str
    name_b: str
    trait_a: str
    trait_b: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, game) for place, s in SETTINGS.items() for game in s.affords if game in GAMES]


def reasonableness_gate(place: str, game: str) -> bool:
    return (place, game) in valid_combos()


def select_helpful_items(game: Game) -> list[HelpfulItem]:
    return [HELPFUL_ITEMS["blue_marker"], HELPFUL_ITEMS["paper_weight"]] if game.needs == {"paper", "marker"} else []


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    game = _safe_lookup(GAMES, params.game)
    world = World(setting)

    a = world.add(Entity(id=params.name_a, kind="character", type="girl" if params.name_a in {"Maya", "Luna", "Zoe", "Iris"} else "boy"))
    b = world.add(Entity(id=params.name_b, kind="character", type="girl" if params.name_b in {"Maya", "Luna", "Zoe", "Iris"} else "boy"))
    a.memes["want_score"] = 1
    b.memes["need_help"] = 1

    marker = world.add(Entity(id="marker", type="thing", label="blue marker"))
    paper = world.add(Entity(id="paper", type="thing", label="score sheet"))
    weight = world.add(Entity(id="weight", type="thing", label="paper weight"))

    world.say(f"In {setting.place}, with {setting.feels} air, two friends met to play.")
    world.say(f"{params.name_a} was {params.trait_a}, and {params.name_b} was {params.trait_b}, ready for the game of the day.")
    world.say(f"They loved {game.gerund}, with each little throw and each happy sway.")

    world.para()
    world.say(f"Their {game.name} was lively and merry, all bounce and blur and cheer.")
    world.say(f"But the score sheet slid and skittered, and the marker was nowhere near.")
    world.facts["problem"] = "score sheet slipped away"
    world.facts["paper_kept"] = False
    world.facts["marker_shared"] = False

    world.para()
    world.say(f"{params.name_a} looked left, then right, then said, “We need a fix to stay.”")
    world.say(f"{params.name_b} found the marker and paper weight, then shared them right away.")
    marker.worn_by = params.name_b
    paper.worn_by = params.name_a
    weight.worn_by = params.name_b
    a.memes["sharing"] = 1
    b.memes["sharing"] = 1
    world.facts["marker_shared"] = True
    world.facts["paper_kept"] = True

    propagate(world, narrate=True)

    world.para()
    score = 0
    for i in range(1, game.score_goal + 1):
        score += 1
    a.meters["score"] = score
    b.meters["score"] = score
    world.facts["score"] = score
    world.say(f"Together they held the paper flat, and the numbers stayed in a neat little line.")
    world.say(f"They kept on tossing with laughing hearts, and the score climbed fine by fine.")
    world.say(f"At last they reached their goal score, {game.score_goal}, and clapped in the shine of the day.")
    world.say(f"Their shared helper bits made the problem small, and the game could sing and sway.")

    world.facts.update(
        game=game,
        setting=setting,
        helper_marker=marker,
        helper_paper=paper,
        helper_weight=weight,
        protagonist=a,
        friend=b,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    game: Game = _safe_fact(world, f, "game")
    return [
        f'Write a short rhyming story for little kids about {game.name}, score, and sharing.',
        f"Tell a gentle rhyming tale where two children solve a score problem by sharing a marker and a paper weight.",
        f'Write a child-friendly story with a clear problem, a shared fix, and the word "score" in it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = _safe_fact(world, f, "protagonist")
    b: Entity = _safe_fact(world, f, "friend")
    game: Game = _safe_fact(world, f, "game")
    setting: Setting = _safe_fact(world, f, "setting")
    score = _safe_fact(world, f, "score")
    return [
        QAItem(
            question=f"Who played the game at {setting.place}?",
            answer=f"{a.id} and {b.id} played together at {setting.place}. They took turns and kept the score as they went.",
        ),
        QAItem(
            question="What problem did they have with the score?",
            answer="Their score sheet slid around, and the marker was hard to use, so they could not keep score neatly at first.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer="They shared the blue marker and the paper weight, which kept the score sheet still so they could write the numbers clearly.",
        ),
        QAItem(
            question="What score did they reach?",
            answer=f"They reached a score of {score}, which was the goal for their {game.name} game.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use something too, like a marker, toy, or snack.",
        ),
        QAItem(
            question="What is a score in a game?",
            answer="A score is the number of points or wins someone gets in a game.",
        ),
        QAItem(
            question="Why can a paper weight help?",
            answer="A paper weight helps by holding paper down so it does not slide or blow away.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="yard", game="bean_toss", name_a="Maya", name_b="Noah", trait_a="cheerful", trait_b="curious"),
    StoryParams(place="porch", game="ring_toss", name_a="Luna", name_b="Eli", trait_a="spry", trait_b="gentle"),
]


def explain_rejection(place: str, game: str) -> str:
    return f"(No story: {game} is not a reasonable match for {place} in this tiny world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld about score, sharing, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--trait-a", choices=TRAITS)
    ap.add_argument("--trait-b", choices=TRAITS)
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
              and (getattr(args, "game", None) is None or c[1] == getattr(args, "game", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, game = rng.choice(combos)
    names = rng.sample(NAMES, 2)
    return StoryParams(
        place=place,
        game=game,
        name_a=getattr(args, "name_a", None) or names[0],
        name_b=getattr(args, "name_b", None) or names[1],
        trait_a=getattr(args, "trait_a", None) or rng.choice(TRAITS),
        trait_b=getattr(args, "trait_b", None) or rng.choice(TRAITS),
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


ASP_RULES = r"""
place(yard). place(porch). place(park_bench).
game(bean_toss). game(ring_toss).
affords(yard,bean_toss). affords(porch,ring_toss). affords(park_bench,bean_toss). affords(park_bench,ring_toss).

needs(bean_toss,paper). needs(bean_toss,marker).
needs(ring_toss,paper). needs(ring_toss,marker).

helpful(blue_marker,marker).
helpful(paper_weight,paper).

valid(Place,Game) :- affords(Place,Game), needs(Game,paper), needs(Game,marker), helpful(blue_marker,marker), helpful(paper_weight,paper).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for g in sorted(s.affords):
            lines.append(asp.fact("affords", place, g))
    for gid, g in GAMES.items():
        lines.append(asp.fact("game", gid))
        for need in sorted(g.needs):
            lines.append(asp.fact("needs", gid, need))
    for iid, item in HELPFUL_ITEMS.items():
        lines.append(asp.fact("helpful", iid, "marker" if "marker" in item.label else "paper"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, game) combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name_a} and {p.name_b} at {p.place} ({p.game})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
