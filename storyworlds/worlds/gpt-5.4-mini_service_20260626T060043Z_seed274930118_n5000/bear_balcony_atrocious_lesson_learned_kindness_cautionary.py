#!/usr/bin/env python3
"""
Bear Balcony Atrocious Lesson Learned Kindness Cautionary
=========================================================

A small storyworld in a ghost-story mood: a child hears about a bear on a
balcony, fears an atrocious-looking shadow, then learns a kinder lesson about
care, caution, and asking before panicking.

The world is intentionally narrow so that every generated story has a clear
beginning, a spooky middle turn, and a resolution image that proves the lesson
changed the characters' choices.
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

    balcony: object | None = None
    bear: object | None = None
    child: object | None = None
    lantern: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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
    name: str
    gender: str
    parent: str
    place: str
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


PLACES = {
    "old_house": "the old house",
    "moon_apartment": "the moonlit apartment",
    "windy_row": "the windy row of homes",
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lena", "Rose"]
BOY_NAMES = ["Theo", "Eli", "Milo", "Finn", "Jasper"]
PARENTS = {"mother": "mom", "father": "dad"}
TRAITS = ["careful", "curious", "brave", "sleepy", "gentle"]

ASP_RULES = r"""
% A story is reasonable when the child can see the bear's shadow, but the ending
% turns on kindness and caution rather than harm.
spooky(P) :- place(P), balcony(P), shadow(P).
lesson(P) :- spooky(P), bear(P), kindness(P), caution(P).
valid_story(P, G) :- lesson(P), gender_ok(G).
"""


@dataclass
class StoryWorldState:
    child: Entity
    parent: Entity
    bear: Entity
    balcony: Entity
    lantern: Entity
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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "old_house"),
        asp.fact("balcony", "old_house"),
        asp.fact("shadow", "old_house"),
        asp.fact("bear", "old_house"),
        asp.fact("kindness", "old_house"),
        asp.fact("caution", "old_house"),
        asp.fact("gender_ok", "girl"),
        asp.fact("gender_ok", "boy"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = {("old_house", "girl"), ("old_house", "boy")}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python expectations ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python expectations:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story world about a bear, a balcony, and a kinder lesson."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    return StoryParams(name=name, gender=gender, parent=parent, place=place)


def make_world(params: StoryParams) -> StoryWorldState:
    world = World(_safe_lookup(PLACES, params.place))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", "careful"]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=_safe_lookup(PARENTS, params.parent)))
    bear = world.add(Entity(id="bear", kind="character", type="bear", label="the bear"))
    balcony = world.add(Entity(id="balcony", type="balcony", label="the balcony"))
    lantern = world.add(Entity(id="lantern", type="thing", label="a little lantern"))
    world.facts.update(params=params, child=child, parent=parent, bear=bear, balcony=balcony, lantern=lantern)
    return StoryWorldState(child=child, parent=parent, bear=bear, balcony=balcony, lantern=lantern), world


def tell(params: StoryParams) -> World:
    state, world = make_world(params)
    child, parent, bear, balcony, lantern = state.child, state.parent, state.bear, state.balcony, state.lantern

    child.memes["curiosity"] += 1
    child.memes["fear"] += 1
    child.meters["attention"] += 1

    world.say(
        f"One cold evening, {child.id} lived in {world.place}. "
        f"The windows whispered, and the hallway kept making tiny creak sounds."
    )
    world.say(
        f"{child.id} liked listening for strange things, even when {child.pronoun()} felt a little shivery."
    )

    world.para()
    child.memes["wonder"] += 1
    world.say(
        f"Then {child.id} saw a shadow on {balcony.label_word if hasattr(balcony, 'label_word') else 'the balcony'}. "
        f"It was long, hunched, and looked atrocious in the moonlight."
    )
    world.say(
        f"{child.pronoun().capitalize()} clutched {child.pronoun('possessive')} blanket and thought a ghosty bear might be waiting outside."
    )

    bear.memes["gentleness"] += 1
    bear.meters["standing"] += 1
    child.memes["fear"] += 2
    world.say(
        f"But the bear was only leaning over the railing to keep a frightened kitten from tumbling off the edge."
    )
    world.say(
        f"When {child.id}'s {parent.label} came to the door with a lantern, the warm light showed the bear's careful paws and soft, worried eyes."
    )

    world.para()
    parent.memes["calm"] += 1
    child.memes["shame"] += 1
    child.memes["kindness"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    world.say(
        f"{parent.label.capitalize()} said, \"Not every big, strange thing is cruel. Sometimes it is just trying to help.\""
    )
    world.say(
        f"{child.id} took a slow breath and saw that the atrocious-looking shadow was only a bear making room for the kitten to climb to safety."
    )
    world.say(
        f"{child.id} opened the window, spoke politely, and helped slide a small bowl of milk onto the balcony for the tired kitten."
    )

    child.memes["lesson"] += 1
    bear.memes["relief"] += 1
    world.say(
        f"The bear nodded once, like a sleepy guard at the gate, and the kitten finally curled beside its mother in the light."
    )
    world.say(
        f"That night, {child.id} learned a cautionary lesson: if something looks terrible in the dark, first ask what it is before deciding it is a monster."
    )

    world.facts.update(
        child=child,
        parent=parent,
        bear=bear,
        balcony=balcony,
        lantern=lantern,
        lesson="ask first",
        caution=True,
        kindness=True,
        spooky=True,
    )
    return world


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


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a gentle ghost story for a young child about {p.name}, a bear, and a balcony.',
        f"Tell a spooky-but-kind story where {p.name} thinks a shadow is atrocious, then learns the truth.",
        "Write a cautionary bedtime story that ends with a lesson about kindness and asking first.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    bear: Entity = _safe_fact(world, f, "bear")
    qa = [
        QAItem(
            question=f"Why did {child.id} feel scared when {child.id} looked at the balcony?",
            answer=(
                f"{child.id} saw a long, hunched shadow in the moonlight and thought it looked atrocious. "
                f"At first {child.id} believed a ghostly bear might be waiting outside."
            ),
        ),
        QAItem(
            question=f"What was the bear really doing on the balcony?",
            answer=(
                "The bear was carefully keeping a frightened kitten from falling off the railing. "
                "It was being protective, not threatening."
            ),
        ),
        QAItem(
            question=f"What lesson did {child.id} learn by the end of the story?",
            answer=(
                f"{child.id} learned to ask first before assuming something is bad. "
                f"The story also showed that kindness can make a scary-looking moment safe."
            ),
        ),
        QAItem(
            question=f"How did {parent.label} help {child.id} understand the bear?",
            answer=(
                f"{parent.label.capitalize()} came with a lantern and explained that not every strange-looking thing is cruel. "
                f"That calm voice helped {child.id} notice the bear's careful paws and kind action."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a balcony?",
            answer="A balcony is a small platform that sticks out from a building, often with a railing around it.",
        ),
        QAItem(
            question="Why can shadows look spooky at night?",
            answer="Shadows can look spooky at night because there is less light, so shapes can seem bigger or stranger than they really are.",
        ),
        QAItem(
            question="Why is kindness important?",
            answer="Kindness helps living things feel safe, cared for, and less alone.",
        ),
        QAItem(
            question="Why should you ask before making a guess?",
            answer="Asking first can stop a mistake, because the truth may be kinder and safer than the first scary idea.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


def valid_names(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combos:")
        for s in stories:
            print(" ", s)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(name="Mina", gender="girl", parent="mother", place="old_house"),
            StoryParams(name="Theo", gender="boy", parent="father", place="moon_apartment"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {i + 1}: {p.name} at {p.place}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
