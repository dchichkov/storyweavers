#!/usr/bin/env python3
"""
A small standalone storyworld about kitchen animal tales with a magical lesson.

Premise:
- A little animal is in a kitchen, chasing a shiny "router" toy or object.
- The kitchen is missing something it needs, so it feels devoid of warmth/focus.
- An "inning" token becomes a playful rule for turns: each animal gets a chance.
- A small magic act solves the problem, and the story lands on a lesson learned
  with a moral value.

The world is intentionally tiny and classical: one setting, one conflict, one
turn, one ending image that proves what changed.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    helper: object | None = None
    hero: object | None = None
    lesson_token: object | None = None
    moral_token: object | None = None
    router: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "lion", "tiger", "fox", "dog", "rabbit", "bear"}:
            base = {"subject": "he", "object": "him", "possessive": "his"}
        elif self.type in {"hen", "bird", "mouse", "squirrel", "owl"}:
            base = {"subject": "she", "object": "her", "possessive": "her"}
        else:
            base = {"subject": "it", "object": "it", "possessive": "its"}
        return base[case]

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
class Kitchen:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=lambda: {"magic", "sharing", "turns"})
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
class StoryParams:
    animal: str
    helper: str
    lesson: str
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


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.turn: int = 0
        self.magic_lit: bool = False
        self.devoid: bool = True
        self.inning: str = "first"

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ANIMALS = {
    "cat": ("cat", "curious cat", ["curious", "quick"]),
    "rabbit": ("rabbit", "bouncy rabbit", ["gentle", "quick"]),
    "fox": ("fox", "clever fox", ["clever", "proud"]),
    "bear": ("bear", "small bear", ["slow", "kind"]),
    "mouse": ("mouse", "tiny mouse", ["tiny", "eager"]),
    "dog": ("dog", "friendly dog", ["friendly", "loud"]),
}

HELPERS = {
    "owl": ("owl", "wise owl", ["wise"]),
    "hen": ("hen", "busy hen", ["patient"]),
    "squirrel": ("squirrel", "helpful squirrel", ["helpful"]),
}

LESSONS = {
    "share_turns": "sharing turns makes play feel fair",
    "listen_first": "listening first keeps a plan from wobbling",
    "gentle_magic": "gentle magic works best when it helps everyone",
}

MORALS = {
    "kindness": "Kindness makes a small place feel warm",
    "patience": "Patience helps good things happen",
    "sharing": "Sharing can turn a tangle into a smile",
}

MAGIC_OPTIONS = {
    "sparkle": "a soft sparkle of magic",
    "whisper": "a whisper of magic",
    "glow": "a warm glow of magic",
}

STARTERS = [
    "One morning",
    "One quiet afternoon",
    "One bright evening",
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when a kitchen has an animal, a helper, and a lesson,
% and the magic can resolve the devoid kitchen by supporting a fair turn.
reasonable_story(A, H, L, M) :- animal(A), helper(H), lesson(L), moral(M),
                                kitchen(kitchen),
                                can_help_magic(Magic), magic(Magic).

can_help_magic(sparkle).
can_help_magic(whisper).
can_help_magic(glow).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("kitchen", "kitchen")]
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for l in LESSONS:
        lines.append(asp.fact("lesson", l))
    for m in MORALS:
        lines.append(asp.fact("moral", m))
    for mg in MAGIC_OPTIONS:
        lines.append(asp.fact("magic", mg))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/4."))
    clingo_set = set(asp.atoms(model, "reasonable_story"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for a in ANIMALS:
        for h in HELPERS:
            for l in LESSONS:
                for m in MORALS:
                    combos.append((a, h, l, m))
    return combos


def explain_invalid(args: argparse.Namespace) -> str:
    return "(No story: this kitchen tale needs a valid animal, helper, lesson, and moral.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_story(world: World, params: StoryParams) -> None:
    animal_type, animal_label, animal_traits = _safe_lookup(ANIMALS, params.animal)
    helper_type, helper_label, helper_traits = HELPERS["owl"]  # simple default helper

    hero = world.add(Entity(
        id="Hero",
        kind="character",
        type=animal_type,
        label=animal_label,
        traits=list(animal_traits),
        meters={"curiosity": 1.0, "hunger": 0.0},
        memes={"hope": 1.0, "confusion": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label=helper_label,
        traits=list(helper_traits),
        meters={"calm": 1.0},
        memes={"kindness": 1.0},
    ))
    router = world.add(Entity(
        id="Router",
        type="thing",
        label="router",
        phrase="a little router with a blinking light",
        meters={"glow": 0.0},
        memes={"importance": 1.0},
    ))
    lesson_token = world.add(Entity(
        id="Lesson",
        type="thing",
        label="lesson",
        phrase=params.lesson.replace("_", " "),
        meters={"clarity": 0.0},
        memes={"value": 1.0},
    ))
    moral_token = world.add(Entity(
        id="Moral",
        type="thing",
        label="moral value",
        phrase=params.moral.replace("_", " "),
        meters={"warmth": 0.0},
        memes={"value": 1.0},
    ))

    world.facts.update(hero=hero, helper=helper, router=router,
                       lesson_token=lesson_token, moral_token=moral_token,
                       params=params)

    starter = random.choice(STARTERS)
    world.say(
        f"{starter}, a {hero.label} was in {world.kitchen.place}, staring at {router.phrase}."
    )
    world.say(
        f"The kitchen felt devoid of cheer, and even the spoon rack seemed to wait for a kinder plan."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to poke the router because the blinking light looked like a tiny star."
    )

    world.para()
    world.turn = 1
    world.inning = "first"
    hero.memes["confusion"] += 1.0
    world.say(
        f"On the first inning, {hero.label} reached for the router, but {helper.label} stepped closer with a patient smile."
    )
    world.say(
        f'"Let us use {params.lesson.replace("_", " ")}," {helper.pronoun()} said, '
        f'"because {params.moral.replace("_", " ")}."'
    )

    world.para()
    world.turn = 2
    world.inning = "second"
    world.magic_lit = True
    router.meters["glow"] += 1.0
    hero.meters["curiosity"] += 1.0
    world.say(
        f"Then the helper lifted a paw and sent a soft sparkle of magic over the table."
    )
    world.say(
        f"The router light blinked in a friendlier way, as if it had learned how to share the room."
    )
    world.say(
        f"{hero.label} stopped grabbing and started waiting for a turn, which made the kitchen feel less devoid."
    )

    world.para()
    world.turn = 3
    world.inning = "final"
    lesson_token.meters["clarity"] = 1.0
    moral_token.meters["warmth"] = 1.0
    hero.memes["hope"] += 1.0
    world.say(
        f"In the final inning, {hero.label} nodded and let the helper finish first."
    )
    world.say(
        f"That was the lesson learned: {params.lesson.replace('_', ' ')}."
    )
    world.say(
        f"The moral value was clear too: {params.moral.replace('_', ' ')}."
    )
    world.say(
        f"By the end, the kitchen was cozy, the router glowed, and {hero.label} sat beside {helper.label} with a calm little grin."
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    return [
        f'Write a short animal story set in a kitchen that includes the word "router" and ends with a lesson learned.',
        f"Tell a gentle story about a {hero.label} who wants to touch the router, but a helper teaches {p.lesson.replace('_', ' ')}.",
        f"Write a child-friendly animal tale where magic helps turn a devoid kitchen into a warm place with a moral value.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    return [
        QAItem(
            question="Where does the story happen?",
            answer="The story happens in the kitchen.",
        ),
        QAItem(
            question=f"What did {hero.label} want to poke at first?",
            answer=f"{hero.label.capitalize()} wanted to poke the router.",
        ),
        QAItem(
            question="What helped change the kitchen from devoid and sad to warm?",
            answer=f"{helper.label} used gentle magic and a patient lesson to make the kitchen feel warm again.",
        ),
        QAItem(
            question="What lesson learned was named in the story?",
            answer=f"The story said the lesson learned was {p.lesson.replace('_', ' ')}.",
        ),
        QAItem(
            question="What moral value did the story point to?",
            answer=f"The moral value was {p.moral.replace('_', ' ')}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a router?",
            answer="A router is a device that helps send internet signals to different places.",
        ),
        QAItem(
            question="What does devoid mean?",
            answer="Devoid means missing something or having almost nothing of it.",
        ),
        QAItem(
            question="What is an inning?",
            answer="An inning is one round or turn in a game.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is a special, make-believe power that can do surprising things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], ""]
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  turn={world.turn} inning={world.inning} magic_lit={world.magic_lit} devoid={world.devoid}")
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} {e.type:10} label={e.label!r} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling / CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(animal="cat", helper="owl", lesson="share_turns", moral="sharing"),
    StoryParams(animal="rabbit", helper="hen", lesson="listen_first", moral="patience"),
    StoryParams(animal="fox", helper="squirrel", lesson="gentle_magic", moral="kindness"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small animal storyworld set in a kitchen.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--lesson", choices=sorted(LESSONS))
    ap.add_argument("--moral", choices=sorted(MORALS))
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
    combos = valid_combos()
    if getattr(args, "animal", None) and getattr(args, "helper", None) and getattr(args, "lesson", None) and getattr(args, "moral", None):
        if (getattr(args, "animal", None), getattr(args, "helper", None), getattr(args, "lesson", None), getattr(args, "moral", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "animal", None) is None or c[0] == getattr(args, "animal", None))
        and (getattr(args, "helper", None) is None or c[1] == getattr(args, "helper", None))
        and (getattr(args, "lesson", None) is None or c[2] == getattr(args, "lesson", None))
        and (getattr(args, "moral", None) is None or c[3] == getattr(args, "moral", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    a, h, l, m = rng.choice(list(filtered))
    return StoryParams(animal=a, helper=h, lesson=l, moral=m)


def generate(params: StoryParams) -> StorySample:
    world = World(Kitchen())
    build_story(world, params)
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
        print(asp_program("#show reasonable_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show reasonable_story/4."))
        atoms = sorted(set(asp.atoms(model, "reasonable_story")))
        print(f"{len(atoms)} compatible stories:")
        for atom in atoms:
            print(" ", atom)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
