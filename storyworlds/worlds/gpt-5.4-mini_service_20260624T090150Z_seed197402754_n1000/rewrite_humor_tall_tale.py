#!/usr/bin/env python3
"""
storyworlds/worlds/rewrite_humor_tall_tale.py
=============================================

A tiny story world for a humorous tall-tale rewrite premise.

Seed tale:
---
A child hears a braggy tall tale about a mighty town rooster, a bent spoon, and a
barn that rang like a bell. The child decides to rewrite the tale in a notebook,
but the first version is so big and silly that it crowds out the facts. A grownup
shows how to trim the exaggeration, keep the joke, and still tell the truth. The
child rewrites the tale, adds a funny ending, and reads it aloud to the whole room.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    written_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    grownup: object | None = None
    notebook: object | None = None
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
class Setting:
    place: str = "the kitchen table"
    world: object | None = None
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
class Tale:
    title: str
    boast: str
    truth: str
    funny_twist: str
    noun: str
    exaggeration: str
    correction: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    grownup_type: str
    tale: str
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


TALES = {
    "rooster": Tale(
        title="The Rooster That Crowed the Moon Awake",
        boast="The rooster crowed so loud that the moon tipped its hat and listened.",
        truth="The rooster crowed at sunrise from the fence, as roosters do.",
        funny_twist="The child rewrote it so the rooster made the coffee steam stand up straight.",
        noun="rooster",
        exaggeration="crowed the moon awake",
        correction="crowed at sunrise",
    ),
    "spoon": Tale(
        title="The Spoon That Bent in a Lightning Lunch",
        boast="The spoon bent like a twig because the soup was telling secrets.",
        truth="The spoon bent a little because it was soft and old.",
        funny_twist="The child rewrote it so the spoon bowed to the soup and asked for an encore.",
        noun="spoon",
        exaggeration="bent like a twig",
        correction="bent a little",
    ),
    "barn": Tale(
        title="The Barn That Rang Like a Bell",
        boast="The barn rang like a giant bell when the wind gave it a polite poke.",
        truth="The barn door rattled in the wind and made a noisy clatter.",
        funny_twist="The child rewrote it so the barn snored once and scared its own chicken.",
        noun="barn",
        exaggeration="rang like a giant bell",
        correction="rattled in the wind",
    ),
}

CHILD_NAMES = ["Maya", "Ben", "Luna", "Theo", "Ivy", "Noah", "Ada", "Finn"]
CHILD_TYPES = {"girl": ["girl"], "boy": ["boy"]}
GROWNUP_TYPES = ["mother", "father", "grandmother", "grandfather"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous tall-tale rewrite story world.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=GROWNUP_TYPES)
    ap.add_argument("--tale", choices=sorted(TALES))
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
    tale = getattr(args, "tale", None) or rng.choice(sorted(TALES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(CHILD_TYPES, gender) if gender in CHILD_TYPES else CHILD_NAMES)
    grownup = getattr(args, "grownup", None) or rng.choice(GROWNUP_TYPES)
    if getattr(args, "gender", None) and getattr(args, "name", None) is None and getattr(args, "gender", None) not in CHILD_TYPES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(child_name=name, child_type=gender, grownup_type=grownup, tale=tale)


ASP_RULES = r"""
#show valid_story/3.
rewrite_needed(T) :- tale(T), boast(T), truth(T), exaggeration(T).
humor_ok(T) :- rewrite_needed(T), has_joke(T), keeps_truth(T).
valid_story(N,T,G) :- child(N), tale(T), grownup(G), humor_ok(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TALES:
        lines.append(asp.fact("tale", tid))
        lines.append(asp.fact("boast", tid))
        lines.append(asp.fact("truth", tid))
        lines.append(asp.fact("exaggeration", tid))
        lines.append(asp.fact("has_joke", tid))
        lines.append(asp.fact("keeps_truth", tid))
    for g in GROWNUP_TYPES:
        lines.append(asp.fact("grownup", g))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("child", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    triples = set(asp_valid_stories())
    py = {(g, t, gd) for g in ["girl", "boy"] for t in TALES for gd in GROWNUP_TYPES}
    if triples == py:
        print(f"OK: clingo gate matches ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python.")
    print("only in clingo:", sorted(triples - py))
    print("only in python:", sorted(py - triples))
    return 1


def choose_tale(params: StoryParams) -> Tale:
    return _safe_lookup(TALES, params.tale)


def tell(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    grownup = world.add(Entity(id="Grownup", kind="character", type=params.grownup_type, label="the grownup"))
    notebook = world.add(Entity(id="Notebook", type="notebook", label="notebook", owner=child.id, written_by=child.id))
    tale = choose_tale(params)
    world.facts.update(child=child, grownup=grownup, notebook=notebook, tale=tale)

    child.memes["curiosity"] = 1
    child.memes["pride"] = 1
    child.memes["joy"] = 0

    world.say(f"{child.id} sat at {world.setting.place} with a notebook and a grin.")
    world.say(f"{child.pronoun('subject').capitalize()} wanted to rewrite '{tale.title}' because it sounded mighty funny.")
    world.say(f"{child.id} began with a tall boast: “{tale.boast}”")

    world.para()
    child.meters["ink"] = 1
    child.memes["excitement"] += 1
    world.say(f"But the first draft got too big and blustery, like a kite in a storm.")
    world.say(f"It said the {tale.noun} {tale.exaggeration}, which was a heap of nonsense.")
    grownup.memes["amused"] = 1
    grownup.memes["guidance"] = 1
    world.say(f"{grownup.label} laughed a little and said the funniest tales still need their feet on the ground.")

    world.para()
    child.memes["embarrassment"] += 1
    world.say(f"{child.id} frowned, then scratched out the giant boasting line.")
    world.say(f"{child.pronoun('subject').capitalize()} kept the joke, but changed the story to the honest part: {tale.truth}")

    world.say(tale.funny_twist)
    child.meters["ink"] += 1
    child.memes["pride"] += 1
    child.memes["joy"] += 2

    world.para()
    world.say(f"At the end, {child.id} read the new version aloud, and everyone chuckled at just the right places.")
    world.say(f"The notebook held the tale neatly now: a funny story with a true laugh inside it.")

    world.facts.update(resolved=True, tale_id=params.tale)
    return world


def generation_prompts(world: World) -> list[str]:
    tale = _safe_fact(world, world.facts, "tale")
    child = _safe_fact(world, world.facts, "child")
    grownup = _safe_fact(world, world.facts, "grownup")
    return [
        f"Write a short funny tall tale about a {tale.noun} and a child named {child.id} who rewrites it.",
        f"Tell a child-facing story where {child.id} fixes an exaggerated story with help from {grownup.type}.",
        f"Write a humorous rewrite tale that keeps the joke but turns the brag into the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale = _safe_fact(world, world.facts, "tale")
    child = _safe_fact(world, world.facts, "child")
    grownup = _safe_fact(world, world.facts, "grownup")
    return [
        QAItem(
            question=f"What did {child.id} want to do with the story at the kitchen table?",
            answer=f"{child.id} wanted to rewrite the tall tale in a notebook.",
        ),
        QAItem(
            question=f"What was wrong with the first version about the {tale.noun}?",
            answer=f"It got too big and silly, saying the {tale.noun} {tale.exaggeration} instead of telling the truth.",
        ),
        QAItem(
            question=f"How did {grownup.label} help the rewrite?",
            answer=f"{grownup.label.capitalize()} reminded {child.id} that a funny story can still stay honest, so {child.id} trimmed the boast and kept the joke.",
        ),
        QAItem(
            question=f"What did the child do at the end?",
            answer=f"{child.id} rewrote the tale, added a funny ending, and read it aloud to everyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tale = _safe_fact(world, world.facts, "tale")
    return [
        QAItem(
            question="What is a rewrite?",
            answer="A rewrite is a new version of a story or text that changes the words, fixes mistakes, or makes it better.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a story with wild, funny exaggerations that are so huge they are meant to make people smile.",
        ),
        QAItem(
            question=f"Why is the {tale.noun} joke funny?",
            answer="It is funny because it stretches the truth in a playful way, but the story still keeps an honest core.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


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


CURATED = [
    StoryParams(child_name="Maya", child_type="girl", grownup_type="grandmother", tale="rooster"),
    StoryParams(child_name="Ben", child_type="boy", grownup_type="father", tale="spoon"),
    StoryParams(child_name="Ivy", child_type="girl", grownup_type="mother", tale="barn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_stories())} compatible stories via clingo.")
        for x in asp_valid_stories():
            print(x)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
