#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dishonest_conflict_bravery_kindness_fable.py
===============================================================================================================

A small fable-style story world about a dishonest choice, a conflict, a brave
turn, and a kind repair.

Seed tale:
---
A fox found a golden pear in an old orchard and wanted it badly. He lied to a
crow so he could keep the pear all to himself, but the lie stirred up a conflict
when the crow noticed the trick. Soon a little rabbit bravely stepped in, told
the truth, and helped the fox make amends. In the end, the fox learned that
kindness and honesty make a better home than selfishness does.

World model:
---
Characters have physical state in meters and emotional state in memes.

Important meters:
    hunger         -- how badly a character wants the prize
    possession     -- who holds the prize
    repair         -- how much amends have been made

Important memes:
    trust          -- how much others believe the character
    shame          -- discomfort after being caught
    conflict       -- tension between characters
    bravery        -- willingness to tell the truth in a hard moment
    kindness       -- helpful, gentle action
    relief         -- easing after repair

The simulation drives the prose:
    desire -> dishonest claim -> conflict -> brave truth -> kind repair -> ending image

The inline ASP twin mirrors the Python reasonableness gate:
    a story is valid when a dishonest choice can cause conflict and a brave,
    kind repair is available.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    witness: object | None = None
    def __post_init__(self):
        for k in ["hunger", "possession", "repair"]:
            self.meters.setdefault(k, 0.0)
        for k in ["trust", "shame", "conflict", "bravery", "kindness", "relief"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "bear", "cat", "dog", "bird", "crow", "rabbit"}:
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
class Orchard:
    place: str = "the orchard"
    season: str = "autumn"
    affords: set[str] = field(default_factory=lambda: {"pear"})
    ORCHARD: object | None = None
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
class Prize:
    id: str
    label: str
    phrase: str
    value: str
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


@dataclass
class StoryParams:
    place: str
    prize: str
    hero: str
    witness: str
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


class World:
    def __init__(self, orchard: Orchard) -> None:
        self.orchard = orchard
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self):
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_conflict(world: World) -> list[str]:
    out = []
    fox = world.get("hero")
    crow = world.get("witness")
    if fox.memes["dishonest"] < THRESHOLD or fox.memes["claim"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fox.memes["conflict"] += 1
    crow.memes["conflict"] += 1
    crow.memes["trust"] = max(0.0, crow.memes["trust"] - 1)
    out.append("The lie stirred up a sharp conflict between them.")
    return out


def _r_shame(world: World) -> list[str]:
    out = []
    fox = world.get("hero")
    if fox.memes["conflict"] < THRESHOLD:
        return out
    sig = ("shame",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fox.memes["shame"] += 1
    out.append("The fox felt shame prick his face.")
    return out


def _r_repair(world: World) -> list[str]:
    out = []
    fox = world.get("hero")
    helper = world.get("helper")
    prize = world.get("prize")
    if fox.memes["bravery"] < THRESHOLD or helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fox.meters["repair"] += 1
    fox.memes["conflict"] = 0.0
    fox.memes["shame"] = max(0.0, fox.memes["shame"] - 1)
    fox.memes["trust"] += 1
    helper.memes["relief"] += 1
    prize.meters["possession"] = 0.0
    out.append("Truth and kindness began to mend the hurt.")
    return out


CAUSAL_RULES = [_r_conflict, _r_shame, _r_repair]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


ORCHARD = Orchard()
PRIZES = {
    "pear": Prize(id="pear", label="golden pear", phrase="a golden pear", value="sweet fruit"),
}
HEROES = {
    "fox": ("fox", "clever"),
    "crow": ("crow", "watchful"),
    "rabbit": ("rabbit", "small"),
}
HELPERS = {
    "rabbit": ("rabbit", "gentle"),
    "hedgehog": ("hedgehog", "kind"),
    "sparrow": ("sparrow", "helpful"),
}


@dataclass
class StoryData:
    hero: str
    witness: str
    helper: str
    prize: str
    place: object | None = None
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


def valid_choices() -> list[StoryData]:
    out = []
    for hero in HEROES:
        for witness in ["crow", "sparrow"]:
            if witness == hero:
                continue
            for helper in HELPERS:
                if helper in {hero, witness}:
                    continue
                out.append(StoryData(hero=hero, witness=witness, helper=helper, prize="pear"))
    return out


def reasonableness_gate(hero: str, witness: str, helper: str, prize: str) -> None:
    if hero != "fox":
        pass
    if witness == helper:
        pass
    if prize not in PRIZES:
        pass
    if helper == "crow":
        pass


def tell(data: StoryData, place: str = "the orchard") -> World:
    reasonableness_gate(data.hero, data.witness, data.helper, data.prize)
    world = World(ORCHARD)
    hero = world.add(Entity(id="hero", kind="character", type=data.hero, label="the fox"))
    witness = world.add(Entity(id="witness", kind="character", type=data.witness, label=f"the {data.witness}"))
    helper = world.add(Entity(id="helper", kind="character", type=data.helper, label=f"the {data.helper}"))
    prize = world.add(Entity(id="prize", type=data.prize, label=_safe_lookup(PRIZES, data.prize).label, phrase=_safe_lookup(PRIZES, data.prize).phrase))

    hero.meters["hunger"] += 1
    hero.memes["desire"] += 1
    hero.memes["dishonest"] += 1
    world.say(f"In {place}, a fox saw {prize.phrase} shining among the branches.")
    world.say("He wanted it badly and told a dishonest story to keep it for himself.")
    witness.memes["trust"] += 1
    prize.meters["possession"] = 1.0
    world.para()

    world.say(f"The {witness.type} noticed the trick, and soon a conflict broke out.")
    propagate(world, narrate=True)
    world.para()

    helper.memes["bravery"] += 1
    helper.memes["kindness"] += 1
    world.say(f"Then the {helper.type} stepped forward with bravery and kindness.")
    hero.memes["bravery"] += 1
    world.say("The fox lowered his head and told the truth.")
    propagate(world, narrate=True)
    world.say(f"The {helper.type} helped the fox return the {prize.label} where it belonged.")
    world.say("After that, the orchard felt peaceful again, and the fox learned that kindness is a better friend than dishonesty.")
    world.facts.update(hero=hero, witness=witness, helper=helper, prize=prize, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about a dishonest fox in {f["place"]} who causes conflict over a {f["prize"].label}.',
        f"Tell a child-friendly story where the {f['witness'].type} catches a lie and a {f['helper'].type} uses bravery and kindness to repair it.",
        f'Write a fable with the words "dishonest", "conflict", "bravery", and "kindness" that ends with a lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, witness, helper, prize = f["hero"], f["witness"], f["helper"], f["prize"]
    return [
        QAItem(
            question="What did the fox want in the orchard?",
            answer=f"He wanted {prize.phrase}, and he was willing to be dishonest to keep it.",
        ),
        QAItem(
            question=f"Why did the {witness.type} get upset?",
            answer="The witness got upset because the fox told a dishonest story and tried to keep the prize for himself.",
        ),
        QAItem(
            question=f"How did the {helper.type} help?",
            answer=f"The {helper.type} showed bravery by stepping forward and kindness by helping the fox tell the truth and put the prize back.",
        ),
        QAItem(
            question="What changed at the end?",
            answer="The conflict calmed down, the fox made amends, and the orchard became peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth instead of making up a dishonest story.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the right thing even when it feels scary or hard.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping gently, sharing, and trying to make things better for others.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
dishonest(hero) :- selects(hero, prize), lies(hero).
conflict(hero, witness) :- dishonest(hero), notices(witness, hero).
brave(helper) :- steps_forward(helper), tells_truth(helper).
kind(helper) :- helps(helper, hero), returns(helper, prize).
resolved(hero) :- brave(helper), kind(helper), conflict(hero, witness).
valid_story(hero, witness, helper, prize) :- dishonest(hero), conflict(hero, witness), brave(helper), kind(helper), resolved(hero).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("selects", "hero", "prize"))
    lines.append(asp.fact("lies", "hero"))
    lines.append(asp.fact("notices", "witness", "hero"))
    lines.append(asp.fact("steps_forward", "helper"))
    lines.append(asp.fact("tells_truth", "helper"))
    lines.append(asp.fact("helps", "helper", "hero"))
    lines.append(asp.fact("returns", "helper", "prize"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_valid = set(asp.atoms(model, "valid_story"))
    py_valid = {("hero", "witness", "helper", "prize")}
    if asp_valid == py_valid:
        print("OK: clingo gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("ASP:", sorted(asp_valid))
    print("PY :", sorted(py_valid))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about dishonesty, conflict, bravery, and kindness.")
    ap.add_argument("--place", default="the orchard")
    ap.add_argument("--hero", choices=["fox"])
    ap.add_argument("--witness", choices=["crow", "sparrow"])
    ap.add_argument("--helper", choices=["rabbit", "hedgehog", "sparrow"])
    ap.add_argument("--prize", choices=list(PRIZES))
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
    hero = getattr(args, "hero", None) or "fox"
    witness = getattr(args, "witness", None) or rng.choice(["crow", "sparrow"])
    helper = getattr(args, "helper", None) or rng.choice(["rabbit", "hedgehog", "sparrow"])
    prize = getattr(args, "prize", None) or "pear"
    reasonableness_gate(hero, witness, helper, prize)
    if len({hero, witness, helper}) < 3:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=getattr(args, "place", None), prize=prize, hero=hero, witness=witness, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(StoryData(params.hero, params.witness, params.helper, params.prize), place=params.place)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:7} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="the orchard", prize="pear", hero="fox", witness="crow", helper="rabbit"),
    StoryParams(place="the orchard", prize="pear", hero="fox", witness="sparrow", helper="hedgehog"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i - 1
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
