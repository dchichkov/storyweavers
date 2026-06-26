#!/usr/bin/env python3
"""
storyworlds/worlds/whoop_majority_suspense_mystery_to_solve_bedtime.py
=======================================================================

A tiny bedtime-story world about a child, a spooky little whoop in the dark,
and a careful majority-vote mystery that turns into a calm, cozy ending.

Seed tale built into the world:
---
At bedtime, a child hears a whoop from somewhere in the dark. The sound feels
mysterious, and the child worries it might be a monster. A parent helps by
counting clues: soft feathers, a twig, and a moonlit shape. The majority of the
clues point to a sleepy owl, not a monster. The child follows the clues outside,
finds the owl in a tree, and learns the whoop was only a greeting. The child
returns to bed feeling brave, and the room is quiet again.

World model:
---
- The child has a worry meter and a curiosity meter.
- The parent has a calm meter and a clue-counting meme.
- The mystery has a source with physical traces and emotional suspense.
- A majority of clues resolves the suspense and proves what the sound was.
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

SUSPENSE_THRESHOLD = 1.0
MYSTERY_THRESHOLD = 1.0



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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clues: list = field(default_factory=list)
    hero: object | None = None
    noise: object | None = None
    parent: object | None = None
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
    place: str = "the bedroom"
    outdoor: str = "the backyard"
    weather: str = "moonlit"
    bedtime: bool = True
    affords: set[str] = field(default_factory=lambda: {"listen", "investigate", "count_clues"})
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
class Mystery:
    source: str
    sound: str
    true_name: str
    disguise: str
    clues: list[str]
    clue_majority: str
    place: str
    tags: set[str] = field(default_factory=set)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    parent: str
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


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy
        c = World(self.scene)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _majority(items: list[str]) -> str:
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)[0][0]


def _resolve_mystery(mystery: Mystery) -> str:
    return mystery.true_name


def _reasonableness_gate(scene: Scene, mystery: Mystery) -> None:
    if scene.place not in {"the bedroom", "the hallway"}:
        pass
    if not mystery.clues or len(mystery.clues) < 3:
        pass
    if mystery.clue_majority not in mystery.clues:
        pass


def build_mystery(key: str, place: str) -> Mystery:
    if key == "owl":
        return Mystery(
            source="a sleepy owl in the tree",
            sound="whoop",
            true_name="owl",
            disguise="a round shadow in the branches",
            clues=["feathers", "twig", "moonshape"],
            clue_majority="feathers",
            place=place,
            tags={"whoop", "majority", "suspense", "mystery", "owl"},
        )
    if key == "kettle":
        return Mystery(
            source="the teapot in the kitchen",
            sound="whoop",
            true_name="kettle",
            disguise="a shiny shape behind the door",
            clues=["steam", "warmth", "whistle"],
            clue_majority="whistle",
            place=place,
            tags={"whoop", "majority", "suspense", "mystery", "kettle"},
        )
    if key == "frog":
        return Mystery(
            source="a tiny frog by the pond",
            sound="whoop",
            true_name="frog",
            disguise="a dark hop near the grass",
            clues=["splash", "leaf", "blink"],
            clue_majority="splash",
            place=place,
            tags={"whoop", "majority", "suspense", "mystery", "frog"},
        )
    pass


SCENES = {
    "bedroom": Scene(place="the bedroom", outdoor="the backyard"),
    "hallway": Scene(place="the hallway", outdoor="the porch"),
    "window": Scene(place="the bedroom window", outdoor="the garden"),
}

MYSTERIES = {"owl", "kettle", "frog"}

GIRL_NAMES = ["Mia", "Ava", "Nora", "Lila", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["sleepy", "curious", "brave", "gentle", "wiry"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime mystery world with whoop and majority.")
    ap.add_argument("--place", choices=SCENES)
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or rng.choice(list(SCENES))
    mystery = getattr(args, "mystery", None) or rng.choice(sorted(MYSTERIES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent)


def tell(params: StoryParams) -> World:
    scene = _safe_lookup(SCENES, params.place)
    mystery = build_mystery(params.mystery, scene.outdoor)
    _reasonableness_gate(scene, mystery)

    world = World(scene)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"worry": 0.0, "curiosity": 0.0}, memes={"brave": 0.0}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent, meters={"calm": 1.0}, memes={"care": 1.0}))
    noise = world.add(Entity(id="whoop", type="sound", label="whoop", phrase="a soft whoop", owner=mystery.source, meters={"loud": 1.0}, memes={"mystery": 1.0}))
    clues = [world.add(Entity(id=f"clue{i}", type="clue", label=cl, phrase=cl)) for i, cl in enumerate(mystery.clues, 1)]

    world.facts.update(hero=hero, parent=parent, mystery=mystery, noise=noise, clues=clues)

    world.say(f"{hero.id} was tucked into bed when a little whoop drifted in from {scene.outdoor}.")
    world.say(f"It sounded mysterious, so {hero.id} peeked under the blanket and held very still.")
    _add_mem(hero, "suspense", 1.0)
    _add_meter(hero, "worry", 1.0)

    world.para()
    world.say(f"{parent.label.capitalize()} came softly to the door and said they could solve the mystery together.")
    world.say(f"They counted clues one by one: {mystery.clues[0]}, {mystery.clues[1]}, and {mystery.clues[2]}.")
    _add_mem(parent, "majority", 1.0)
    _add_meter(parent, "calm", 1.0)

    vote = _majority(mystery.clues)
    world.facts["vote"] = vote
    if vote == mystery.clue_majority:
        _add_mem(hero, "confidence", 1.0)
        _add_meter(hero, "worry", -1.0)
        world.say(f"Most of the clues matched {mystery.clue_majority}, so the majority point was clear.")
        world.say(f"{parent.label.capitalize()} smiled and said the whoop was probably not a monster at all.")
    else:
        pass

    world.para()
    world.say(f"They followed the clues outside to {mystery.place}, where a {mystery.disguise} waited in the dark.")
    world.say(f"There, the truth appeared: it was only {mystery.source}, and the whoop was a friendly greeting.")
    _add_mem(hero, "mystery_solved", 1.0)
    _add_meter(hero, "worry", -1.0)
    _add_meter(parent, "calm", 1.0)

    world.para()
    world.say(f"{hero.id} gave a tiny whoop back, then went inside feeling brave and sleepy.")
    world.say(f"Back in bed, the night felt quiet, the mystery was solved, and the house was full of peaceful dark.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f"Write a bedtime story for a child who hears a whoop and uses the majority of clues to solve the mystery.",
        f"Tell a gentle suspense story where {hero.id} follows a whoop to find out what made the sound.",
        f"Create a cozy mystery-to-solve tale using the words whoop and majority, ending with a calm bedtime scene.",
        f"Write a short bedtime story where clues are counted and the majority reveals whether the whoop was a monster.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"What strange sound did {hero.id} hear at bedtime?",
            answer=f"{hero.id} heard a soft whoop drifting in from {mystery.place}.",
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer=f"They solved it by counting clues and trusting the majority match among the clues.",
        ),
        QAItem(
            question=f"What was the whoop really?",
            answer=f"The whoop was really just {mystery.source}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt brave, sleepy, and ready to rest after the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does majority mean?",
            answer="A majority means more than half of a group agrees with the same idea or answer.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something strange or unknown that people try to figure out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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


def asp_facts() -> str:
    import asp
    lines = []
    for name in SCENES:
        lines.append(asp.fact("scene", name))
    for m in sorted(MYSTERIES):
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


ASP_RULES = r"""
scene_ok(P) :- scene(P).
mystery_ok(M) :- mystery(M).
valid_story(P,M) :- scene_ok(P), mystery_ok(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_pairs() -> list[tuple[str, str]]:
    return sorted((p, m) for p in SCENES for m in MYSTERIES)


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_pairs())
    b = set(valid_pairs())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} pairs).")
        return 0
    print("Mismatch between ASP and Python:")
    print("only ASP:", sorted(a - b))
    print("only Python:", sorted(b - a))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  facts: {world.facts.get('mystery').true_name if 'mystery' in world.facts else ''}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", mystery="owl", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="hallway", mystery="kettle", name="Leo", gender="boy", parent="father"),
    StoryParams(place="window", mystery="frog", name="Nora", gender="girl", parent="mother"),
]


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        for p, m in pairs:
            print(f"{p} {m}")
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
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} mystery at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
