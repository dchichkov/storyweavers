#!/usr/bin/env python3
"""
storyworlds/worlds/fluid_illegal_medal_inner_monologue_fable.py
===============================================================

A small, fable-like story world about a prized medal, a sneaky forbidden plan,
and the inner monologue that helps a character choose the honest path.

Seed tale, reimagined as a simulation:
---
In a small meadow village, a young crow found a medal left on a bench after the
summer games. The medal was shiny, heavy, and very important to the old judge
who owned it. A squirrel friend whispered that they could coat the medal with
glossy fluid and claim it as a new prize for themselves. That was illegal, and
the crow knew it. The crow listened to the loud wish inside its own head, then
spoke honestly, returned the medal, and earned trust instead of trouble.

World instruments:
---
- physical meters: shine, fluid, weight, distance, safety
- emotional memes: pride, greed, guilt, fear, trust, relief
- narrative feature: Inner Monologue
- style: Fable
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    kept_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    fluid: object | None = None
    helper: object | None = None
    hero: object | None = None
    judge: object | None = None
    medal: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "swan"}
        male = {"boy", "father", "dad", "man", "crow", "fox", "squirrel", "judge", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    w: object | None = None
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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
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
    seed: Optional[int] = None
    hero: str = "crow"
    helper: str = "squirrel"
    judge: str = "judge"
    place: str = "the meadow court"
    medal_owner: str = "judge"
    hero_name: str = "Cora"
    helper_name: str = "Moss"
    judge_name: str = "Old Bram"
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


HERO_NAMES = ["Cora", "Pip", "Rowan", "Nico", "Tavi", "Luma"]
HELPER_NAMES = ["Moss", "Bramble", "Wren", "Tansy", "Juniper", "Reed"]
JUDGE_NAMES = ["Old Bram", "Lady Alder", "Master Thorne", "Judge Willow"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable story world about a medal, fluid, and an illegal choice.")
    ap.add_argument("--hero", choices=["crow", "fox", "squirrel"])
    ap.add_argument("--helper", choices=["crow", "fox", "squirrel"])
    ap.add_argument("--judge", choices=["judge", "elder"])
    ap.add_argument("--place")
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--judge-name")
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
    hero = getattr(args, "hero", None) or rng.choice(["crow", "fox", "squirrel"])
    helper = getattr(args, "helper", None) or rng.choice([x for x in ["crow", "fox", "squirrel"] if x != hero])
    if getattr(args, "helper", None) and getattr(args, "helper", None) == hero:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(["the meadow court", "the oak path", "the river bridge"])
    if "court" not in place and "bridge" not in place and "path" not in place:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        seed=getattr(args, "seed", None),
        hero=hero,
        helper=helper,
        judge=getattr(args, "judge", None) or "judge",
        place=place,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        helper_name=getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES),
        judge_name=getattr(args, "judge_name", None) or rng.choice(JUDGE_NAMES),
    )


def make_world(params: StoryParams) -> World:
    w = World(params.place)
    hero = w.add(Entity(
        id="hero", kind="character", type=params.hero, label=params.hero_name,
        meters={"distance": 0.0, "safety": 1.0},
        memes={"pride": 1.0, "greed": 0.0, "guilt": 0.0, "fear": 0.0, "trust": 0.2, "relief": 0.0},
    ))
    helper = w.add(Entity(
        id="helper", kind="character", type=params.helper, label=params.helper_name,
        meters={"distance": 0.0}, memes={"curiosity": 0.7, "greed": 0.4, "guilt": 0.0, "trust": 0.2},
    ))
    judge = w.add(Entity(
        id="judge", kind="character", type="judge", label=params.judge_name,
        meters={"distance": 2.0}, memes={"trust": 0.4, "calm": 1.0},
    ))
    medal = w.add(Entity(
        id="medal", kind="thing", type="medal", label="medal",
        phrase="the shining medal",
        owner=judge.id, caretaker=judge.id, kept_by=judge.id,
        meters={"shine": 1.0, "fluid": 0.0, "weight": 1.0, "safety": 1.0},
    ))
    fluid = w.add(Entity(
        id="fluid", kind="thing", type="fluid", label="glossy fluid",
        phrase="the glossy fluid",
        meters={"fluid": 1.0, "shine": 0.8},
    ))
    w.facts.update(hero=hero, helper=helper, judge=judge, medal=medal, fluid=fluid)
    return w


def inner_monologue(world: World, hero: Entity, helper: Entity, medal: Entity) -> None:
    hero.memes["fear"] += 0.4
    world.say(
        f"\"That medal is not mine,\" thought {hero.label}. "
        f"\"It belongs to {medal.owner or 'someone'} and I should not take it.\""
    )
    helper.memes["greed"] += 0.5
    world.say(
        f"Then {helper.label} leaned close and whispered, "
        f"\"If we coat it with fluid, no one will notice.\""
    )
    world.say(
        f"\"But that would be illegal,\" thought {hero.label}. "
        f"\"A shiny trick can still be a wrong one.\""
    )


def risk_medal(world: World, hero: Entity, helper: Entity, medal: Entity, fluid: Entity) -> None:
    helper.memes["greed"] += 0.4
    medal.meters["fluid"] += 1.0
    medal.meters["shine"] += fluid.meters["shine"]
    medal.meters["safety"] -= 0.6
    world.say(
        f"{helper.label} reached for the medal and tilted the bottle of fluid toward it."
    )
    world.say(
        f"{hero.label} felt a tightness in the chest and thought, "
        f"\"If I let this happen, the medal will be spoiled and the judge will be hurt.\""
    )
    world.facts["illegal_plan"] = True
    world.facts["medal_at_risk"] = True


def refuse(world: World, hero: Entity, helper: Entity, judge: Entity, medal: Entity) -> None:
    hero.memes["guilt"] += 0.3
    hero.memes["trust"] += 0.5
    helper.memes["fear"] += 0.3
    world.say(
        f"{hero.label} stood taller and said, \"No. We must return the medal at once.\""
    )
    world.say(
        f"In the quiet that followed, {hero.label} thought, "
        f"\"Honesty is smaller than a parade, but it can carry a whole heart.\""
    )
    medal.kept_by = judge.id
    medal.owner = judge.id
    world.facts["returned"] = True


def resolve(world: World, hero: Entity, judge: Entity, medal: Entity) -> None:
    judge.memes["trust"] += 0.6
    judge.memes["calm"] += 0.2
    hero.memes["relief"] += 0.8
    hero.memes["pride"] += 0.3
    medal.meters["safety"] = 1.0
    medal.meters["fluid"] = 0.0
    world.say(
        f"{hero.label} carried the medal back to {judge.label} and admitted the whole thing."
    )
    world.say(
        f"{judge.label} took the medal, smiled gently, and said the honest one should be trusted."
    )
    world.say(
        f"By sunset, {hero.label} had no prize in its claws, but it had something steadier: a clear name."
    )


def tell(params: StoryParams) -> World:
    w = make_world(params)
    hero = w.get("hero")
    helper = w.get("helper")
    judge = w.get("judge")
    medal = w.get("medal")
    fluid = w.get("fluid")

    w.say(
        f"At {w.place}, {hero.label} found the old medal left alone beside the bench."
    )
    w.say(
        f"It shone like a little sun, and {helper.label} stared at it with hungry eyes."
    )
    w.para()
    inner_monologue(w, hero, helper, medal)
    risk_medal(w, hero, helper, medal, fluid)
    w.para()
    refuse(w, hero, helper, judge, medal)
    resolve(w, hero, judge, medal)

    w.facts.update(
        place=w.place,
        hero_type=hero.type,
        helper_type=helper.type,
        judge_type=judge.type,
        hero_name=hero.label,
        helper_name=helper.label,
        judge_name=judge.label,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child about a {f["hero_type"]} who finds a medal and hears an inner monologue about doing an illegal thing.',
        f"Tell a gentle fable where {f['hero_name']} resists a sneaky plan with fluid and returns the medal to {f['judge_name']}.",
        f'Write a small moral story that includes the words "fluid", "illegal", and "medal".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    judge = _safe_fact(world, f, "judge")
    medal = _safe_fact(world, f, "medal")
    return [
        QAItem(
            question=f"What did {hero.label} find at {world.place}?",
            answer=f"{hero.label} found a medal that belonged to {judge.label}.",
        ),
        QAItem(
            question=f"What illegal idea did {helper.label} whisper about the medal?",
            answer=f"{helper.label} whispered about coating the medal with fluid and keeping it as if it were a new prize.",
        ),
        QAItem(
            question=f"What did {hero.label} think inside its own head before choosing the right thing?",
            answer=f"{hero.label} thought that the medal was not theirs, that the trick would be illegal, and that honesty was the better path.",
        ),
        QAItem(
            question=f"How did the story end for the medal?",
            answer=f"{hero.label} returned the medal to {judge.label}, so the medal was safe again and the wrong plan was stopped.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a medal?",
            answer="A medal is a prize or honor, often a shiny object given for doing something well.",
        ),
        QAItem(
            question="What is fluid?",
            answer="A fluid is a liquid or a substance that can flow and spread from one place to another.",
        ),
        QAItem(
            question="What does illegal mean?",
            answer="Illegal means against the rules or against the law.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.kept_by:
            bits.append(f"kept_by={e.kept_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A medal is at risk when fluid is applied to it.
at_risk(M) :- medal(M), touched_by_fluid(M).

% Illegal plans are those that target a medal not owned by the actor.
illegal_take(H, M) :- hero(H), medal(M), owner(M, O), H != O.

% A sensible refusal happens when an illegal take would be wrong and the hero
% chooses honesty instead.
honest_choice(H) :- hero(H), not illegal_take(H, M), medal(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("judge", "judge"))
    lines.append(asp.fact("medal", "medal"))
    lines.append(asp.fact("owner", "medal", "judge"))
    lines.append(asp.fact("touched_by_fluid", "medal"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show at_risk/1. #show illegal_take/2."))
    atoms = set((sym.name, tuple(arg.name if arg.type != arg.type.Number else arg.number for arg in sym.arguments)) for sym in model)
    expected = {("at_risk", ("medal",)), ("illegal_take", ("hero", "medal"))}
    if atoms == expected:
        print("OK: ASP gate matches the Python world assumptions.")
        return 0
    print("MISMATCH between ASP and Python world assumptions.")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=getattr(args, "seed", None),
        hero=getattr(args, "hero", None) or rng.choice(["crow", "fox", "squirrel"]),
        helper=getattr(args, "helper", None) or rng.choice(["crow", "fox", "squirrel"]),
        judge=getattr(args, "judge", None) or "judge",
        place=getattr(args, "place", None) or rng.choice(["the meadow court", "the oak path", "the river bridge"]),
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        helper_name=getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES),
        judge_name=getattr(args, "judge_name", None) or rng.choice(JUDGE_NAMES),
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


CURATED = [
    StoryParams(hero="crow", helper="squirrel", place="the meadow court", hero_name="Cora", helper_name="Moss", judge_name="Old Bram"),
    StoryParams(hero="fox", helper="crow", place="the oak path", hero_name="Fenn", helper_name="Wren", judge_name="Lady Alder"),
    StoryParams(hero="squirrel", helper="fox", place="the river bridge", hero_name="Pip", helper_name="Tansy", judge_name="Master Thorne"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show at_risk/1. #show illegal_take/2. #show honest_choice/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show at_risk/1. #show illegal_take/2. #show honest_choice/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_story_params(args, random.Random(seed))
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
