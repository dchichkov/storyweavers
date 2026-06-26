#!/usr/bin/env python3
"""
Standalone storyworld: compromise, duplo, and punk in a tiny fairy-tale problem-solving domain.

A little story premise:
- A punkish child wants to build a duplo castle.
- A friend or sibling has the last special piece and is using it for another build.
- The characters solve the problem with a compromise, with sound effects and a bit of rhyme.
- The ending shows the new shared build and the calmer feelings.

This world keeps the prose child-facing, concrete, and state-driven.
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
# Core world model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    friend: object | None = None
    helper: object | None = None
    hero: object | None = None
    special: object | None = None
    tower: object | None = None
    def __post_init__(self) -> None:
        for k in ("blocked", "built", "shared", "loud", "messy"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "hope", "stubborn", "kindness", "pride", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    nw: object | None = None
    world: object | None = None
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
        nw = World(self.setting)
        nw.entities = _copy.deepcopy(self.entities)
        nw.paragraphs = [[]]
        nw.fired = set(self.fired)
        nw.facts = dict(self.facts)
        return nw


# ---------------------------------------------------------------------------
# Story ingredients
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
    setting: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    helper: str
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


SETTINGS = {
    "toy cottage": {
        "opening": "the little toy cottage",
        "sound": "clack-clack",
        "rhyme": "Brick by brick and block by block, the little tower found its rock.",
    },
    "garden shed": {
        "opening": "the garden shed",
        "sound": "tap-tap",
        "rhyme": "Brick by brick and block by block, the tiny walls went tickety-tock.",
    },
    "moonlit playroom": {
        "opening": "the moonlit playroom",
        "sound": "plink-plink",
        "rhyme": "Brick by brick and block by block, the castle rose beside the clock.",
    },
}

NAMES_BOY = ["Pip", "Toby", "Finn", "Noel", "Milo"]
NAMES_GIRL = ["Mira", "Luna", "Tess", "Nina", "Poppy"]
HELPERS = ["Mouse", "Robin", "Aunt June", "Grandma Brim", "Captain Hush"]

TRAITS = ["punk", "brave", "bright", "merry", "spiky"]


# ---------------------------------------------------------------------------
# Reasoning rules
# ---------------------------------------------------------------------------

def _build_blocked(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    tower = world.get("tower")
    special = world.get("special_block")
    if special.worn_by is not None:
        return out
    if hero.memes["worry"] < THRESHOLD:
        return out
    if ("blocked", hero.id) in world.fired:
        return out
    world.fired.add(("blocked", hero.id))
    hero.meters["blocked"] += 1
    tower.meters["blocked"] += 1
    out.append("The castle plan went still, as if a cloud had sat on it.")
    return out


def _shared_solution(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    tower = world.get("tower")
    special = world.get("special_block")
    if hero.memes["hope"] < THRESHOLD:
        return out
    if ("shared", hero.id) in world.fired:
        return out
    if special.worn_by != friend.id:
        return out
    world.fired.add(("shared", hero.id))
    hero.meters["built"] += 1
    friend.meters["shared"] += 1
    tower.meters["built"] += 1
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    friend.memes["kindness"] += 1
    out.append("The plan clicked into place like a puzzle piece finding home.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_build_blocked, _shared_solution):
            lines = fn(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def sound_of(setting: str) -> str:
    return _safe_lookup(SETTINGS, setting)["sound"]


def rhyme_line() -> str:
    return random.choice([
        "Brick by brick and block by block, the little tower found its rock.",
        "Block by block and song by song, the shared-up castle grew up strong.",
        "Brick by brick and tune by tune, the bright new tower sang to the moon.",
    ])


def introduce(world: World, hero: Entity, friend: Entity, helper: Entity) -> None:
    world.say(
        f"Once in {_safe_lookup(SETTINGS, world.setting)['opening']}, there lived a little {hero.type} named {hero.id}, "
        f"who was a {hero.traits[0]} {hero.traits[1]} little punk with a heart that liked to drum."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} loved duplo blocks, for they made happy little roads, walls, and castles."
    )
    world.say(
        f"Nearby lived {friend.id}, a {friend.traits[0]} {friend.traits[1]} {friend.type}, and {helper.id}, who listened like a wise old tale-tree."
    )


def desire(world: World, hero: Entity, tower: Entity) -> None:
    hero.memes["hope"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} wanted to build a grand duplo castle. "
        f"{hero.pronoun('subject').capitalize()} stacked one block, then another, and the blocks answered {sound_of(world.setting)}."
    )
    world.say(rhyme_line())


def problem(world: World, hero: Entity, friend: Entity, special: Entity) -> None:
    hero.memes["worry"] += 1
    friend.meters["loud"] += 1
    world.say(
        f"Then {hero.id} saw the last special {special.label}, but {friend.id} was using it for a small bridge."
    )
    world.say(
        f'"Oh dear," said {hero.id}. "Without that block, my castle will not stand proud."'
    )
    world.say(
        f"The room went {sound_of(world.setting)}-quiet, and {hero.id}'s shoulders drooped like wet ribbons."
    )
    propagate(world)


def problem_solve(world: World, hero: Entity, friend: Entity, helper: Entity, special: Entity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{helper.id} came close and said, " +
        f'"A good fix can be kind. Let one build now, and let one build next."'
    )
    world.say(
        f"{hero.id} looked at the bridge, then at the castle plan, and had a clever little thought."
    )
    world.say(
        f'"What if we make the bridge become my tower gate?" {hero.id} asked. '
        f'"Then your block can stay where it is, and my castle can still begin."'
    )
    special.worn_by = friend.id
    friend.meters["shared"] += 1
    hero.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    hero.memes["hope"] += 1
    propagate(world)
    world.say(
        f'{friend.id} smiled and said, "Yes, that is fair. We can share and spare the square!"'
    )
    world.say(
        f"{sound_of(world.setting).capitalize()}! The bridge became a gate, and the gate became part of the castle."
    )
    world.say(rhyme_line())


def ending(world: World, hero: Entity, friend: Entity, helper: Entity, special: Entity) -> None:
    world.say(
        f"In the end, {hero.id} was building again, not alone but side by side with {friend.id}."
    )
    world.say(
        f"The duplo castle stood taller than before, with the special block holding the gate like a bright tiny crown."
    )
    world.say(
        f"{hero.id} felt joyful and light, {friend.id} felt proud and kind, and {helper.id} nodded as if the moon itself had approved."
    )


def tell(params: StoryParams) -> World:
    world = World(params.setting)
    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        traits=["punk", "small", "determined"],
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type=params.friend_type,
        traits=["gentle", "careful", "helpful"],
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="owl",
        traits=["wise", "soft", "ancient"],
    ))
    tower = world.add(Entity(id="tower", type="tower", label="tower"))
    special = world.add(Entity(id="special_block", type="duplo_block", label="duplo block", plural=False))
    world.facts.update(hero=hero, friend=friend, helper=helper, tower=tower, special=special)

    introduce(world, hero, friend, helper)
    world.para()
    desire(world, hero, tower)
    problem(world, hero, friend, special)
    world.para()
    problem_solve(world, hero, friend, helper, special)
    world.para()
    ending(world, hero, friend, helper, special)
    return world


# ---------------------------------------------------------------------------
# Registries and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hero_type in ("boy", "girl"):
            for friend_type in ("boy", "girl"):
                combos.append((setting, hero_type, friend_type))
    return combos


def explain_rejection() -> str:
    return "No story: this world needs at least two child characters so a compromise can happen."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about duplo, punk, and compromise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--friend-type", choices=["boy", "girl"])
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--helper")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["boy", "girl"])
    friend_type = getattr(args, "friend_type", None) or rng.choice(["boy", "girl"])
    hero = getattr(args, "hero", None) or rng.choice(NAMES_BOY if hero_type == "boy" else NAMES_GIRL)
    friend = getattr(args, "friend", None) or rng.choice([n for n in (NAMES_BOY + NAMES_GIRL) if n != hero])
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    if hero == friend:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type, helper=helper)


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
    return [
        f"Write a fairy tale about a punk child, duplo blocks, and a kind compromise in {world.setting}.",
        "Tell a child-friendly story with sound effects, a problem, and a shared solution.",
        "Write a short rhyming story where two children solve a building problem by sharing a duplo piece.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    friend: Entity = _safe_fact(world, world.facts, "friend")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    return [
        QAItem(
            question=f"Who wanted to build the duplo castle?",
            answer=f"{hero.id} did. {hero.pronoun('subject').capitalize()} was the little punk child who loved duplo blocks.",
        ),
        QAItem(
            question=f"What problem stopped {hero.id} at first?",
            answer=f"{friend.id} was using the last special duplo block, so the castle could not be finished right away.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"{helper.id} suggested a compromise, and {hero.id} and {friend.id} changed the bridge into part of the castle gate so both builds could continue.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and relieved because the castle could be built and the special block was still being used well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are duplo blocks?",
            answer="Duplo blocks are big building blocks for small children. They fit together to make towers, houses, bridges, and castles.",
        ),
        QAItem(
            question="What is a compromise?",
            answer="A compromise is a fair choice where people each give a little so they can solve a problem together.",
        ),
        QAItem(
            question="What does punk mean here?",
            answer="In this story, punk means a bold, spiky style and attitude, like a child who likes lively clothes and brave ideas.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects help make a story feel lively and fun, like clack-clack or tap-tap when blocks snap together.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.plural:
            bits.append("plural=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
friend(F) :- friend_name(F).
helper(X) :- helper_name(X).

problem(H,F) :- hero(H), friend(F), blocked_piece(F).
compromise_possible(H,F) :- problem(H,F), helper(_).

solution(H,F) :- problem(H,F), compromise_possible(H,F), shared_plan(H,F).
resolved(H) :- solution(H,_).

#show problem/2.
#show compromise_possible/2.
#show solution/2.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for n in NAMES_BOY + NAMES_GIRL:
        lines.append(asp.fact("name", n))
    for h in NAMES_BOY + NAMES_GIRL:
        lines.append(asp.fact("hero_name", h))
    for f in NAMES_BOY + NAMES_GIRL:
        lines.append(asp.fact("friend_name", f))
    for x in HELPERS:
        lines.append(asp.fact("helper_name", x))
    lines.append(asp.fact("blocked_piece", "friend"))
    lines.append(asp.fact("shared_plan", "hero", "friend"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set((s.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", None) for a in s.arguments)) for s in model)
    expected = {("problem", ("hero", "friend")), ("compromise_possible", ("hero", "friend")), ("solution", ("hero", "friend")), ("resolved", ("hero",))}
    if atoms >= expected:
        print("OK: ASP twin is producing the expected shape.")
        return 0
    print("MISMATCH between ASP twin and expected shape.")
    print(sorted(atoms))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="toy cottage", hero="Pip", hero_type="boy", friend="Mira", friend_type="girl", helper="Mouse"),
    StoryParams(setting="garden shed", hero="Luna", hero_type="girl", friend="Finn", friend_type="boy", helper="Robin"),
    StoryParams(setting="moonlit playroom", hero="Toby", hero_type="boy", friend="Poppy", friend_type="girl", helper="Grandma Brim"),
]


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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.hero} and {p.friend} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
