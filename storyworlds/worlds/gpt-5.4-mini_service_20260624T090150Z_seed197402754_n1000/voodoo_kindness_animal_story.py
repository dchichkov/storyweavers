#!/usr/bin/env python3
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

THRESHOLD = 1.0



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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "fox", "cat", "dog", "bear", "mouse", "owl"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    place: str
    animal: str
    helper: str
    charm: str
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


PLACES = {
    "barn": "the barn",
    "garden": "the garden",
    "pond": "the pond",
    "meadow": "the meadow",
}

ANIMALS = {
    "rabbit": {"type": "rabbit", "label": "little rabbit", "name": "Ruby"},
    "fox": {"type": "fox", "label": "small fox", "name": "Finn"},
    "cat": {"type": "cat", "label": "tiny cat", "name": "Mimi"},
    "dog": {"type": "dog", "label": "young dog", "name": "Buster"},
}

HELPERS = {
    "owl": {"type": "owl", "label": "old owl"},
    "deer": {"type": "deer", "label": "gentle deer"},
    "badger": {"type": "badger", "label": "kind badger"},
}

CHARMS = {
    "voodoo doll": {
        "label": "voodoo doll",
        "phrase": "a tiny voodoo doll with a stitched smile",
    },
}


@dataclass
class WorldFacts:
    hero: str
    helper: str
    charm: str
    place: str
    worry: str
    fix: str
    facts: object | None = None
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


ASP_RULES = r"""
hero(X) :- animal(X).
kind(X) :- helper(X).
worry(H, C) :- hero(H), charm(C).
solution(H, C) :- kindness(C), worry(H, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
        lines.append(asp.fact("kindness", h))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solution/2."))
    asp_set = set(asp.atoms(model, "solution"))
    py_set = {(p.animal, p.charm) for p in CURATED}
    if asp_set == py_set:
        print(f"OK: ASP gate matches curated kindness stories ({len(asp_set)} items).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in Python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story: voodoo kindness and a small gentle fix.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--charm", choices=CHARMS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, c) for p in PLACES for a in ANIMALS for c in CHARMS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [x for x in combos if x[0] == getattr(args, "place", None)]
    if getattr(args, "animal", None):
        combos = [x for x in combos if x[1] == getattr(args, "animal", None)]
    if getattr(args, "charm", None):
        combos = [x for x in combos if x[2] == getattr(args, "charm", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, animal, charm = (list(rng.choice(combos)) + [None, None, None])[:3]
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(place=place, animal=animal, helper=helper, charm=charm)


def tell(params: StoryParams) -> World:
    world = World(setting=_safe_lookup(PLACES, params.place))
    animal_info = _safe_lookup(ANIMALS, params.animal)
    helper_info = _safe_lookup(HELPERS, params.helper)
    charm_info = _safe_lookup(CHARMS, params.charm)

    hero = world.add(Entity(id="hero", kind="character", type=animal_info["type"], label=animal_info["label"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_info["type"], label=helper_info["label"]))
    charm = world.add(Entity(
        id="charm",
        kind="thing",
        type="charm",
        label=charm_info["label"],
        phrase=charm_info["phrase"],
        owner=hero.id,
        caretaker=helper.id,
    ))

    hero.memes["worry"] += 1
    helper.memes["kindness"] += 1

    world.say(f"Once, {animal_info['label']} named {animal_info['name']} lived near {world.setting}.")
    world.say(f"{animal_info['name']} found {charm.phrase} and held it close, because {charm.label} felt special.")
    world.para()
    world.say(f"One day, {animal_info['name']} saw a scared little sparrow by {world.setting}.")
    world.say(
        f"{animal_info['name']} wanted to help, but did not know how. "
        f"Then the {helper_info['label']} came by and smiled."
    )
    world.para()
    world.say(
        f'"Kindness is stronger than any spooky trick," said the {helper_info["label"]}. '
        f'"Let the little {charm.label} remind you to be gentle."'
    )
    hero.memes["kindness"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{animal_info['name']} nodded, tucked the {charm.label} safely near their nest, "
        f"and shared seeds with the sparrow. The sparrow chirped happily."
    )

    world.facts = WorldFacts(
        hero=animal_info["name"],
        helper=helper_info["label"],
        charm=charm.label,
        place=world.setting,
        worry="scared",
        fix="kindness",
    ).__dict__
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Animal Story about a {f["hero"]} with a voodoo doll learning kindness at {f["place"]}.',
        f"Tell a gentle story where {f['hero']} is worried about helping a frightened bird, and {f['helper']} teaches kindness.",
        f'Write a simple animal tale that includes the word "voodoo" and ends with a kind act.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who learned to be kind in the story?",
            answer=f"{f['hero']} learned to be kind after meeting the {f['helper']}.",
        ),
        QAItem(
            question=f"What special object did {f['hero']} keep close?",
            answer=f"{f['hero']} kept a {f['charm']} close.",
        ),
        QAItem(
            question=f"What did the helper teach about the spooky-looking charm?",
            answer=f"The helper said kindness was stronger than any spooky trick, and the charm could remind {f['hero']} to be gentle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
        QAItem(
            question="What is a voodoo doll in a harmless story?",
            answer="In a harmless story, a voodoo doll can be a tiny toy or charm that a character keeps as a reminder, not something used to hurt anyone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: type={e.type} labels={e.label} memes={dict(e.memes)} meters={dict(e.meters)}")
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
    StoryParams(place="garden", animal="rabbit", helper="owl", charm="voodoo doll"),
    StoryParams(place="meadow", animal="fox", helper="deer", charm="voodoo doll"),
    StoryParams(place="pond", animal="cat", helper="badger", charm="voodoo doll"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show solution/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show solution/2."))
        print(sorted(asp.atoms(model, "solution")))
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.animal} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
