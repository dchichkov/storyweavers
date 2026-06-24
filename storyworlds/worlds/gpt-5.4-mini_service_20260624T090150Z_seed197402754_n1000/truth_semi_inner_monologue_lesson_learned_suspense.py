#!/usr/bin/env python3
"""
A small folk-tale storyworld about telling the truth, with suspense,
an inner monologue beat, and a lesson learned.
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

TRUTHS = {
    "cookie_jar": {
        "setting": "the kitchen",
        "object": "cookie jar",
        "object_phrase": "a shiny cookie jar",
        "mistake": "peeked inside the cookie jar",
        "sound": "a tiny clink",
        "damage": "the lid slipped and bumped the floor",
        "coverup": "said nothing at all",
        "confession": "told the truth",
        "fix": "helped sweep up the pieces and set the jar on the table",
        "lesson": "telling the truth can make a hard moment lighter",
    },
    "blue_ribbon": {
        "setting": "the barn",
        "object": "blue ribbon",
        "object_phrase": "a bright blue ribbon",
        "mistake": "played with the blue ribbon",
        "sound": "a soft tear",
        "damage": "one corner of the ribbon tore",
        "coverup": "tried to hide it under straw",
        "confession": "spoke up honestly",
        "fix": "tied the ribbon into a new knot and showed the tear",
        "lesson": "truth is braver than hiding",
    },
    "little_lamp": {
        "setting": "the cottage",
        "object": "little lamp",
        "object_phrase": "a little brass lamp",
        "mistake": "bumped the little lamp",
        "sound": "a small thud",
        "damage": "the lamp went dark for a moment",
        "coverup": "quietly moved away",
        "confession": "admitted what happened",
        "fix": "fetched a new wick and lit the lamp again",
        "lesson": "honesty helps fix what has gone wrong",
    },
}

NAMES = ["Mira", "Anya", "Tom", "Oren", "Lena", "Pip", "Sage", "Nico"]
COMPANIONS = ["grandmother", "grandfather", "mother", "father", "aunt", "uncle"]



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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class StoryParams:
    seed_word: str
    name: str
    companion: str
    seed: Optional[int] = None
    p: object | None = None
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
    def __init__(self, truth_key: str, name: str, companion: str):
        self.truth_key = truth_key
        self.truth = _safe_lookup(TRUTHS, truth_key)
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

        self.hero = self.add(Entity(id=name, kind="character", type="child"))
        self.elder = self.add(Entity(id=companion.title(), kind="character", type=companion))
        self.valued = self.add(
            Entity(
                id="valued",
                kind="thing",
                type=truth_key,
                label=self.truth["object"],
                phrase=self.truth["object_phrase"],
                caretaker=self.elder.id,
                owner=self.elder.id,
            )
        )
        self.hero.memes["worry"] = 0.0
        self.hero.memes["relief"] = 0.0
        self.hero.memes["guilt"] = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.truth_key, self.hero.id, self.elder.type)
        clone.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label, "phrase": e.phrase,
            "owner": e.owner, "caretaker": e.caretaker,
            "meters": dict(e.meters), "memes": dict(e.memes),
        }) for k, e in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def predict_confession(world: World) -> bool:
    sim = world.copy()
    return simulate_suspense(sim, narrate=False)


def simulate_suspense(world: World, narrate: bool = True) -> bool:
    hero = world.hero
    item = world.valued
    truth = world.truth
    if "mistake" not in world.fired:
        world.fired.add("mistake")
        item.meters["moved"] = 1.0
        hero.meters["caught"] = 1.0
        hero.memes["worry"] += 1.0
        if narrate:
            world.say(
                f"{hero.id} was alone in {truth['setting']}, and {hero.id} {truth['mistake']}."
            )
            world.say(
                f"Then there came {truth['sound']}, and {truth['damage']}."
            )
    if "suspense" not in world.fired:
        world.fired.add("suspense")
        hero.memes["worry"] += 1.0
        if narrate:
            world.say(
                f"{hero.id} looked around. No one had seen it yet, or so it seemed."
            )
            world.say(
                f'In a small voice, {hero.id} thought, "If I keep quiet, maybe no one will know."'
            )
    if narrate:
        world.say(
            f"But the silence sat heavy, and {hero.id}'s heart felt as if it had a stone in it."
        )
    return True


def resolve_truth(world: World) -> None:
    hero = world.hero
    elder = world.elder
    truth = world.truth
    item = world.valued

    if "confession" not in world.fired:
        world.fired.add("confession")
        hero.memes["guilt"] += 1.0
        hero.memes["worry"] += 1.0
        world.say(
            f"{hero.id} took a breath and {truth['confession']}."
        )
        world.say(
            f'"I was afraid," {hero.id} said in a tiny whisper, '
            f'"but hiding it felt worse than telling it."'
        )
        world.say(
            f"In the quiet of {truth['setting']}, that was {hero.id}'s inner thought: "
            f'be brave, tell the truth, and let the day be mended.'
        )

    if "lesson" not in world.fired:
        world.fired.add("lesson")
        hero.memes["relief"] += 1.0
        hero.memes["guilt"] = 0.0
        item.meters["fixed"] = 1.0
        world.say(
            f"{elder.id} did not scold hard. Instead, {elder.pronoun()} listened, then helped."
        )
        world.say(
            f"Together they {truth['fix']}, and soon the house felt calm again."
        )
        world.say(
            f"{hero.id} learned that {truth['lesson']}."
        )


def tale_for(params: StoryParams) -> StorySample:
    truth = _safe_lookup(TRUTHS, params.seed_word)
    world = World(params.seed_word, params.name, params.companion)

    world.say(
        f"Once upon a time, {params.name} lived near {truth['setting']} with {params.companion}."
    )
    world.say(
        f"There was {truth['object_phrase']} there, and everyone knew it was special."
    )
    world.para()

    simulate_suspense(world, narrate=True)
    world.para()

    resolve_truth(world)

    world.facts.update(
        truth_key=params.seed_word,
        name=params.name,
        companion=params.companion,
        setting=truth["setting"],
        object=truth["object"],
        lesson=truth["lesson"],
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    t = world.truth
    return [
        f"Write a folk tale for a small child about {world.hero.id} in {t['setting']} that ends with telling the truth.",
        f"Tell a suspenseful, gentle story where someone thinks about hiding a mistake, then confesses and learns a lesson.",
        f"Write a simple story with an inner monologue about whether to be honest after {t['mistake']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    t = world.truth
    hero = world.hero
    elder = world.elder
    return [
        QAItem(
            question=f"What did {hero.id} do that caused trouble?",
            answer=f"{hero.id} {t['mistake']} and then had to face the worry that followed.",
        ),
        QAItem(
            question=f"What did {hero.id} think about before speaking up?",
            answer=f"{hero.id} thought about hiding the problem, but the quiet made the heart feel heavy, so {hero.id} chose honesty.",
        ),
        QAItem(
            question=f"How did {elder.id} help in the end?",
            answer=f"{elder.id} listened kindly and helped {t['fix']}.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=t["lesson"].capitalize() + ".",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    t = world.truth
    return [
        QAItem(
            question="What is truth?",
            answer="Truth means saying what really happened, even when it is hard.",
        ),
        QAItem(
            question="What is a semi-hidden mistake?",
            answer="A semi-hidden mistake is a problem someone is trying to hide only a little, so it is not fully secret and can still be found out.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting to learn what will happen next.",
        ),
    ]


ASP_RULES = r"""
#show valid/1.
#show story/2.

valid(cookie_jar).
valid(blue_ribbon).
valid(little_lamp).

story(cookie_jar, truth).
story(blue_ribbon, truth).
story(little_lamp, truth).

"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([asp.fact("truthy", k) for k in TRUTHS])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    return {a[0] for a in asp.atoms(model, "valid")}


def asp_verify() -> int:
    py = set(TRUTHS)
    cl = asp_valid()
    if py == cl:
        print(f"OK: clingo gate matches Python registry ({len(py)} items).")
        return 0
    print("MISMATCH")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world about truth, suspense, and a lesson learned.")
    ap.add_argument("--truth", choices=TRUTHS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    truth_word = getattr(args, "truth", None) or rng.choice(list(TRUTHS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    if name.lower() == companion.lower():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(seed_word=truth_word, name=name, companion=companion, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    return tale_for(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for ent in sample.world.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            print(ent.id, ent.kind, ent.type, meters, memes)
    if qa:
        print()
        for title, items in [("Generation prompts", sample.prompts), ("Story Q&A", sample.story_qa), ("World Q&A", sample.world_qa)]:
            print(f"== {title} ==")
            if title == "Generation prompts":
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
            print()


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(sorted(asp_valid()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, truth_key in enumerate(TRUTHS):
            p = StoryParams(seed_word=truth_key, name=_safe_lookup(NAMES, i % len(NAMES)), companion=_safe_lookup(COMPANIONS, i % len(COMPANIONS)), seed=base_seed + i)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
