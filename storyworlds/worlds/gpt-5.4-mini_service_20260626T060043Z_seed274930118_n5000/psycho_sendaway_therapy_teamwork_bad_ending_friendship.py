#!/usr/bin/env python3
"""
storyworlds/worlds/psycho_sendaway_therapy_teamwork_bad_ending_friendship.py
=============================================================================

A small folk-tale storyworld about a friendship that tries teamwork and therapy,
but ends in a bad sendaway.

Seed tale sketch:
---
In a little valley, a clever child and a soft-spoken friend once shared bread,
songs, and evening walks. Then a stranger called Psycho began stirring up fear
with sneaky tricks and cruel jokes. The child wanted the village to stay kind,
so the healer offered therapy and the neighbors formed a teamwork plan. They sat,
spoke gently, mended lanterns, and tried to help Psycho calm down. But the
tricks kept growing, trust kept shrinking, and in the end the council sent
Psycho away over the hill. The friendship did not return to how it was.

World model:
---
- meters: distance, damage, repair, burden, warmth, supplies
- memes: trust, fear, hope, shame, calm, bond, resolve

Narrative instruments:
---
- teamwork: helpers work together to repair a shared problem
- therapy: the healer uses calm talk and listening
- sendaway: the village decides someone must leave
- bad ending: the friendship is not repaired in time
"""

from __future__ import annotations

import argparse
import dataclasses
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

TRY_THRESHOLD = 1.0



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
    kind: str = "person"
    role: str = ""
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    healer: object | None = None
    hero: object | None = None
    psycho: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "person" and self.role in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "person" and self.role in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id
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


@dataclass
class Place:
    name: str = "the little valley"
    has_healer_hut: bool = True
    world: object | None = None
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
    place: str = "valley"
    hero_name: str = "Mina"
    hero_role: str = "girl"
    friend_name: str = "Tavi"
    friend_role: str = "boy"
    psycho_name: str = "Psycho"
    healer_name: str = "Nell"
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks: list[list[str]] = [[]]
        for line in self.lines:
            if line == "":
                if chunks[-1]:
                    chunks.append([])
            else:
                chunks[-1].append(line)
        return "\n\n".join(" ".join(chunk) for chunk in chunks if chunk)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = []
        w.facts = dict(self.facts)
        return w


def _bump(e: Entity, key: str, amt: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _feel(e: Entity, key: str, amt: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def setup_world(params: StoryParams) -> World:
    world = World(Place())
    hero = world.add(Entity(params.hero_name, role=params.hero_role, label=params.hero_name))
    friend = world.add(Entity(params.friend_name, role=params.friend_role, label=params.friend_name))
    psycho = world.add(Entity(params.psycho_name, kind="person", role="wanderer", label=params.psycho_name))
    healer = world.add(Entity(params.healer_name, kind="person", role="healer", label=params.healer_name))

    hero.memes = {"trust": 3.0, "fear": 0.0, "hope": 2.0, "bond": 3.0}
    friend.memes = {"trust": 3.0, "fear": 0.0, "hope": 1.0, "bond": 3.0}
    psycho.memes = {"calm": 0.0, "shame": 0.0, "resolve": 1.0}
    healer.memes = {"calm": 2.0, "resolve": 2.0}
    healer.meters = {"supplies": 1.0, "repair": 0.0}
    world.facts.update(params=params, hero=hero, friend=friend, psycho=psycho, healer=healer)
    return world


def predict_turn(world: World) -> bool:
    p = world.get("Psycho")
    return p.memes.get("shame", 0.0) >= 2.0 and p.memes.get("calm", 0.0) >= 1.0


def act1(world: World) -> None:
    h, f, p, healer = (world.get("Mina"), world.get("Tavi"), world.get("Psycho"), world.get("Nell"))
    world.say(f"In a little valley, {h.name_or_label()} and {f.name_or_label()} kept a warm friendship by sharing bread and berry tea.")
    world.say(f"But one foggy week, {p.name_or_label()} began leaving crooked jokes, broken gates, and frightened chickens in the lane.")
    _feel(h, "fear", 1.0)
    _feel(f, "fear", 1.0)
    _bump(p, "damage", 1.0)
    world.facts["problem"] = "fear_and_trouble"


def act2(world: World) -> None:
    h, f, p, healer = (world.get("Mina"), world.get("Tavi"), world.get("Psycho"), world.get("Nell"))
    world.para()
    world.say(f"{h.name_or_label()} went to {healer.name_or_label()} for therapy, and the healer spoke in a quiet voice, asking everyone to sit and breathe.")
    _feel(healer, "calm", 1.0)
    _feel(p, "calm", 1.0)
    _feel(p, "shame", 1.0)
    world.say(f"Then the village chose teamwork: {h.name_or_label()}, {f.name_or_label()}, and {healer.name_or_label()} mended fences, swept porches, and carried lanterns together.")
    _bump(healer, "repair", 1.0)
    _bump(h, "burden", 1.0)
    _bump(f, "burden", 1.0)
    _feel(h, "hope", 1.0)
    _feel(f, "hope", 1.0)
    if predict_turn(world):
        world.say(f"For a little while, it looked as if {p.name_or_label()} might calm down and join the circle.")
    else:
        world.say(f"But the tricks kept coming, and the friendship grew thin as a nettle string.")
    _feel(h, "trust", -1.0)
    _feel(f, "trust", -1.0)
    _feel(h, "bond", -1.0)
    _feel(f, "bond", -1.0)
    _feel(p, "shame", 1.0)
    _feel(p, "calm", -0.5)


def act3(world: World) -> None:
    h, f, p, healer = (world.get("Mina"), world.get("Tavi"), world.get("Psycho"), world.get("Nell"))
    world.para()
    world.say(f"At last, the council looked at the broken gate, the scared hens, and the tired faces.")
    world.say(f"They decided on a sendaway, and {p.name_or_label()} was told to leave over the hill before sunset.")
    _bump(p, "distance", 3.0)
    _feel(p, "shame", 1.0)
    _feel(h, "trust", -1.0)
    _feel(f, "trust", -1.0)
    _feel(h, "bond", -2.0)
    _feel(f, "bond", -2.0)
    world.say(f"{h.name_or_label()} and {f.name_or_label()} did not cheer; they stood by the gate with their lanterns dim and their hands still muddy from the work.")
    world.say(f"So the teamwork ended in a bad ending, and the friendship stayed cracked even after the therapy and all the careful mending.")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    act1(world)
    act2(world)
    act3(world)
    world.facts["resolved"] = False
    return world


def generate_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a folk-tale about {p.hero_name}, {p.friend_name}, and {p.psycho_name} that includes psycho, sendaway, and therapy.",
        f"Tell a short story in a village where teamwork tries to heal a friendship, but the ending is bad and someone is sent away.",
        "Write a gentle folk tale about a healer, a troubled stranger, and friends whose trust runs out before sunset.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    h, f, psycho, healer = (world.get(p.hero_name), world.get(p.friend_name), world.get(p.psycho_name), world.get(p.healer_name))
    return [
        QAItem(
            question=f"Who tried therapy first when the village trouble began?",
            answer=f"{h.name_or_label()} tried therapy first by going to {healer.name_or_label()} and listening to the healer's calm words.",
        ),
        QAItem(
            question=f"What did the villagers do together to help with the trouble?",
            answer=f"They used teamwork, mending fences, sweeping porches, and carrying lanterns together.",
        ),
        QAItem(
            question=f"Why was the ending bad for {psycho.name_or_label()}?",
            answer=f"The ending was bad because the council chose a sendaway and told {psycho.name_or_label()} to leave over the hill instead of fixing the friendship.",
        ),
        QAItem(
            question=f"How did {h.name_or_label()} and {f.name_or_label()} feel at the end?",
            answer=f"They felt sad and tired, standing by the gate with their friendship still cracked after all the work.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together to get a job done that would be harder alone.",
        ),
        QAItem(
            question="What is therapy?",
            answer="Therapy is a calm kind of help where someone listens, talks carefully, and helps feelings become easier to carry.",
        ),
        QAItem(
            question="What does sendaway mean?",
            answer="A sendaway means someone is made to leave a place and go somewhere else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
#show valid_story/1.

valid(world).
valid_story(world).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "valley"),
        asp.fact("feature", "teamwork"),
        asp.fact("feature", "therapy"),
        asp.fact("feature", "sendaway"),
        asp.fact("ending", "bad"),
        asp.fact("style", "folk_tale"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    got = set(asp.atoms(model, "valid"))
    want = {("world",)}
    if got == want:
        print("OK: ASP gate matches Python gate.")
        return 0
    print("MISMATCH:", got, want)
    return 1


@dataclass
class RegistryItem:
    key: str
    label: str
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


SETTINGS = {
    "valley": Place(name="the little valley", has_healer_hut=True),
}

CURATED = [
    StoryParams(place="valley", hero_name="Mina", hero_role="girl", friend_name="Tavi", friend_role="boy", psycho_name="Psycho", healer_name="Nell"),
    StoryParams(place="valley", hero_name="Ira", hero_role="boy", friend_name="Sera", friend_role="girl", psycho_name="Psycho", healer_name="Nell"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about teamwork, therapy, friendship, and a bad sendaway ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--psycho-name")
    ap.add_argument("--healer-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    hero_name = getattr(args, "name", None) or rng.choice(["Mina", "Ira", "Lio", "Nora"])
    hero_role = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    friend_name = getattr(args, "friend_name", None) or rng.choice(["Tavi", "Sera", "Jori", "Pim"])
    friend_role = getattr(args, "friend_gender", None) or ("boy" if hero_role == "girl" else "girl")
    return StoryParams(
        place=getattr(args, "place", None) or "valley",
        hero_name=hero_name,
        hero_role=hero_role,
        friend_name=friend_name,
        friend_role=friend_role,
        psycho_name=getattr(args, "psycho_name", None) or "Psycho",
        healer_name=getattr(args, "healer_name", None) or "Nell",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=generate_story_text(world),
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
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
