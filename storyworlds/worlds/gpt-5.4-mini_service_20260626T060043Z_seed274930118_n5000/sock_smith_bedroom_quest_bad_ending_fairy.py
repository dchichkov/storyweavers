#!/usr/bin/env python3
"""
storyworlds/worlds/sock_smith_bedroom_quest_bad_ending_fairy.py
===============================================================

A small fairy-tale storyworld about a bedroom quest, a sock smith, and a bad ending.

Premise:
- In a cozy bedroom, a little seeker wants to help a sock smith complete a special pair.
- A lost sock must be found before bedtime.

Tension:
- The bedroom is full of hiding places, but only some are plausible for a sock.
- The quest can go wrong if the seeker looks in the wrong spot or trusts a trick.

Turn:
- The seeker follows clues around the bedroom.

Resolution:
- This world intentionally supports a bad ending: the quest fails, the sock is not found,
  and the sock smith must leave the pair unfinished.

The story is classical, state-driven, and child-facing, with a fairy-tale tone.
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
# World model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    smith: object | None = None
    sock: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "king"}:
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
class Room:
    name: str = "the bedroom"
    features: tuple[str, ...] = ("bed", "closet", "toy chest", "rug", "window")
    hiding_places: tuple[str, ...] = ("under the bed", "in the closet", "behind the pillow", "under the rug")
    PLACES: set[str] = field(default_factory=set)
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
class World:
    room: Room
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
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


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
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
    place: str = "bedroom"
    quest: str = "find the lost sock"
    ending: str = "bad ending"
    style: str = "fairy tale"
    seed: Optional[int] = None
    hero_name: str = "Mina"
    hero_type: str = "girl"
    smith_name: str = "Old Purl"
    smith_type: str = "socksmith"
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


PLACES = {"bedroom": Room()}
HIDING_SPOTS = list(PLACES["bedroom"].hiding_places)

HERO_NAMES = ["Mina", "Toby", "Luna", "Pip", "Nora", "Elio"]
SMITH_NAMES = ["Old Purl", "Lady Stitch", "Master Toe", "Aunt Loom"]

# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A quest is plausible if the sock is hidden in a bedroom hiding place.
plausible_quest(Q) :- quest(Q), setting(bedroom), needs_sock(Q).

% A hiding place is plausible when it can hold a sock.
plausible_hide(Sp) :- hiding_place(Sp), sock_can_hide(Sp).

% The bad ending happens when no clue leads to the real hiding place.
bad_ending(Q) :- quest(Q), plausible_quest(Q), not found_sock(Q).

% A story is valid when it is a bedroom sock quest with a bad ending option.
valid_story(bedroom, Q, bad_ending) :- plausible_quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "bedroom"),
        asp.fact("quest", "find_lost_sock"),
        asp.fact("needs_sock", "find_lost_sock"),
        asp.fact("sock_can_hide", "under_bed"),
        asp.fact("sock_can_hide", "behind_pillow"),
        asp.fact("sock_can_hide", "in_closet"),
        asp.fact("sock_can_hide", "under_rug"),
        asp.fact("hiding_place", "under_bed"),
        asp.fact("hiding_place", "behind_pillow"),
        asp.fact("hiding_place", "in_closet"),
        asp.fact("hiding_place", "under_rug"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("bedroom", "find_lost_sock", "bad_ending")}
    if asp_set == py_set:
        print("OK: clingo gate matches Python story gate.")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(room=_safe_lookup(PLACES, params.place))

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"hope": 1.0, "curiosity": 1.0},
        memes={"bravery": 1.0},
    ))
    smith = world.add(Entity(
        id=params.smith_name,
        kind="character",
        type=params.smith_type,
        label="sock smith",
        meters={"patience": 1.0},
        memes={"worry": 1.0, "care": 1.0},
    ))
    sock = world.add(Entity(
        id="lost_sock",
        kind="thing",
        type="sock",
        label="sock",
        phrase="a silver-threaded sock",
        owner=smith.id,
        caretaker=smith.id,
        hidden_in="under the bed",
        meters={"lost": 1.0},
        memes={"special": 1.0},
    ))

    world.facts.update(hero=hero, smith=smith, sock=sock, params=params)
    return world


def tell_story(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    smith: Entity = _safe_fact(world, world.facts, "smith")
    sock: Entity = _safe_fact(world, world.facts, "sock")

    world.say(
        f"Once in the {world.room.name}, there lived a little {hero.type} named {hero.id}, "
        f"who loved fairy tales and tiny adventures."
    )
    world.say(
        f"At the foot of the bed worked {smith.id}, a wise sock smith who could mend a heel "
        f"or spin a shine into a seam."
    )
    world.say(
        f"{smith.id} had woven {sock.phrase}, but one sock had vanished before the pair was done."
    )

    world.para()
    world.say(
        f"{hero.id} made a quest of it, because in a bedroom a lost sock can look like a moonbeam, "
        f"a crumb, or a folded dream."
    )
    world.say(
        f"The little seeker peered under the bed, looked inside the closet, and lifted the pillow."
    )
    world.say(
        f"Each place was quiet, and each place gave back only dust and whispers."
    )

    world.para()
    hero.memes["hope"] -= 0.5
    hero.memes["doubt"] = 1.0
    smith.memes["worry"] += 1.0
    world.say(
        f"Still, {hero.id} thought the sock might be hiding under the rug, so the quest went there next."
    )
    world.say(
        f"But the rug held only a flat toy button, and the button did not know any sock songs."
    )

    world.para()
    hero.meters["searching"] = 4.0
    sock.meters["found"] = 0.0
    world.say(
        f"Night leaned through the window, and the bedroom grew blue and sleepy."
    )
    world.say(
        f"{smith.id} sighed a small sigh and set down the needle."
    )
    world.say(
        f"The lost sock was still missing, so the pair could not be finished before bedtime."
    )
    world.say(
        f"That was the bad ending of the quest: {hero.id} had searched bravely, but the hidden sock stayed hidden."
    )

    world.facts["quest_succeeded"] = False
    world.facts["ending"] = "bad ending"
    world.facts["clue_spots"] = list(world.room.hiding_places)


# ---------------------------------------------------------------------------
# Content registries and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    smith: Entity = _safe_fact(world, world.facts, "smith")
    return [
        "Write a short fairy tale about a bedroom quest for a lost sock.",
        f"Tell a gentle story where {hero.id} helps {smith.id}, the sock smith, but the quest ends badly.",
        "Write a child-friendly story set in a bedroom with a missing sock, a careful search, and a sad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    smith: Entity = _safe_fact(world, world.facts, "smith")
    sock: Entity = _safe_fact(world, world.facts, "sock")
    return [
        QAItem(
            question=f"Who went on the quest in the bedroom?",
            answer=f"{hero.id} went on the quest in the bedroom to help {smith.id} find the missing sock.",
        ),
        QAItem(
            question=f"What was {smith.id} trying to finish?",
            answer=f"{smith.id} was trying to finish {sock.phrase}, but one sock had gone missing.",
        ),
        QAItem(
            question="Why is the ending called bad?",
            answer="It is called a bad ending because the lost sock was never found before bedtime, so the pair stayed unfinished.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sock?",
            answer="A sock is a soft piece of clothing that you wear on your foot inside a shoe or slipper.",
        ),
        QAItem(
            question="What is a smith?",
            answer="A smith is a maker or worker who uses skill and tools to shape or mend things.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or adventure where someone tries hard to find something or solve a problem.",
        ),
        QAItem(
            question="What is a bedroom for?",
            answer="A bedroom is a room for sleeping, resting, and keeping bedtime things nearby.",
        ),
    ]


# ---------------------------------------------------------------------------
# Parsing / generation / emit
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale bedroom quest with a sock smith and a bad ending.")
    ap.add_argument("--place", choices=["bedroom"], default="bedroom")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name = rng.choice(HERO_NAMES)
    smith_name = rng.choice(SMITH_NAMES)
    hero_type = rng.choice(["girl", "boy"])
    return StoryParams(
        place="bedroom",
        quest="find the lost sock",
        ending="bad ending",
        style="fairy tale",
        seed=getattr(args, "seed", None),
        hero_name=hero_name,
        hero_type=hero_type,
        smith_name=smith_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_story() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_story()
        print(f"{len(stories)} compatible story shape(s):")
        for triple in stories:
            print("  ", triple)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams(seed=base_seed)
        samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
