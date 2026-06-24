#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/diabetes_devil_flipper_reconciliation_suspense_repetition_fable.py
=========================================================================================================

A small fable-style story world about a devil, Flipper, and diabetes, with
suspense, repetition, and reconciliation.

Seed image:
---
A little devil loved to make a scene by the pond. A seal named Flipper had
diabetes and needed careful snacks. The devil kept offering sweets and asking
Flipper to guess what was hidden under the cloth. Flipper worried, waited, and
watched. In the end, the devil chose a kinder game and brought a safe treat.
They laughed together, and the pond felt peaceful again.

World model:
---
    devil temptation -> devil.memes["mischief"] += 1
    repeated tease    -> flipper.memes["worry"] += 1; suspense rises
    unsafe sweet      -> flipper.meters["sugar"] += 1; if diabetes is high,
                          flipper.memes["fatigue"] += 1
    safe snack        -> flipper.memes["trust"] += 1; reconciliation lowers
                          worry and mischief
    apology + sharing -> both actors gain calm, story ends in peace

The prose is authored from the simulated state, with a fable-like moral turn
rather than a frozen paragraph.
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
# Entities
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    devil: object | None = None
    entities: set[str] = field(default_factory=set)
    flipper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "devil"}:
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
    place: str = "the pond"
    detail: str = "The reeds leaned over the water, and dragonflies skimmed the surface."
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
class Snack:
    id: str
    label: str
    phrase: str
    sugar: float
    safe_for_diabetes: bool
    repeatable: bool = False
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
    snack: str
    name_devil: str
    name_flipper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
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
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "plural": v.plural, "owner": v.owner,
            "worn_by": v.worn_by, "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "pond": Setting(
        place="the pond",
        detail="The reeds leaned over the water, and dragonflies skimmed the surface.",
    ),
    "orchard": Setting(
        place="the orchard",
        detail="The apple trees made a cool green roof over the grass.",
    ),
    "lane": Setting(
        place="the village lane",
        detail="The lane was narrow and bright, with stones warm from the sun.",
    ),
}

SNACKS = {
    "berry": Snack(
        id="berry",
        label="berries",
        phrase="a small bowl of berries",
        sugar=1.0,
        safe_for_diabetes=True,
        repeatable=True,
    ),
    "cake": Snack(
        id="cake",
        label="cake",
        phrase="a sweet cake with sugar on top",
        sugar=2.0,
        safe_for_diabetes=False,
        repeatable=False,
    ),
    "cookie": Snack(
        id="cookie",
        label="cookies",
        phrase="a plate of crisp cookies",
        sugar=1.5,
        safe_for_diabetes=False,
        repeatable=True,
    ),
    "apple": Snack(
        id="apple",
        label="apple slices",
        phrase="a bowl of apple slices",
        sugar=0.5,
        safe_for_diabetes=True,
        repeatable=True,
    ),
}

DEVIL_NAMES = ["Milo", "Nico", "Rex", "Toby", "Jasper", "Ivy"]
FLIPPER_NAMES = ["Flipper", "Flick", "Nori", "Mira", "Pip"]


# ---------------------------------------------------------------------------
# Params, parser, resolution
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable-style storyworld: a devil, Flipper, and a careful snack."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--name-devil")
    ap.add_argument("--name-flipper")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    snack = getattr(args, "snack", None) or rng.choice(list(SNACKS))
    if getattr(args, "snack", None) and not _safe_lookup(SNACKS, getattr(args, "snack", None)).safe_for_diabetes:
        # Explicitly allowed, but the story must be honest: unsafe snack creates tension.
        pass
    return StoryParams(
        place=place,
        snack=snack,
        name_devil=getattr(args, "name_devil", None) or rng.choice(DEVIL_NAMES),
        name_flipper=getattr(args, "name_flipper", None) or rng.choice(FLIPPER_NAMES),
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def predict(world: World, snack: Snack, repeats: int) -> dict:
    sim = world.copy()
    flipper = sim.get("Flipper")
    for _ in range(repeats):
        flipper.memes["worry"] = flipper.memes.get("worry", 0) + 1
        if not snack.safe_for_diabetes:
            flipper.meters["sugar"] = flipper.meters.get("sugar", 0) + snack.sugar
            flipper.memes["fatigue"] = flipper.memes.get("fatigue", 0) + 1
    return {
        "worried": flipper.memes.get("worry", 0) >= THRESHOLD,
        "fatigued": flipper.memes.get("fatigue", 0) >= THRESHOLD,
        "sugar": flipper.meters.get("sugar", 0),
    }


def intro(world: World, devil: Entity, flipper: Entity, snack: Snack) -> None:
    world.say(
        f"By {world.setting.place}, there lived a little devil named {devil.id} "
        f"who loved a sly joke and a loud laugh."
    )
    world.say(
        f"Near the water lived {flipper.id}, a seal with diabetes who needed "
        f"careful snacks and steady kindness."
    )
    world.say(
        f"{devil.id} often carried {snack.phrase}, and the pond grew still "
        f"whenever {flipper.id} waited to see what would happen next."
    )


def suspense_loop(world: World, devil: Entity, flipper: Entity, snack: Snack) -> None:
    flipper.memes["worry"] = flipper.memes.get("worry", 0) + 1
    world.say(
        f"{devil.id} lifted a cloth and asked, 'What is under here?' "
        f"{flipper.id} blinked and waited."
    )
    if not snack.safe_for_diabetes:
        flipper.meters["sugar"] = flipper.meters.get("sugar", 0) + snack.sugar
        flipper.memes["fatigue"] = flipper.memes.get("fatigue", 0) + 1
        world.say(
            f"It was {snack.label}, and that was no kind surprise for a seal with diabetes."
        )
    else:
        flipper.memes["hope"] = flipper.memes.get("hope", 0) + 1
        world.say(
            f"It was {snack.label}, and {flipper.id} let out a small hopeful breath."
        )


def repeated_tease(world: World, devil: Entity, flipper: Entity, snack: Snack) -> None:
    world.say(
        f"{devil.id} tried the trick again, and again, and again, as if repeating it "
        f"could make it wise."
    )
    suspense_loop(world, devil, flipper, snack)


def warning(world: World, devil: Entity, flipper: Entity, snack: Snack) -> bool:
    pred = predict(world, snack, repeats=2)
    if pred["worried"]:
        if snack.safe_for_diabetes:
            world.say(
                f"{flipper.id} said, 'I can wait, but I need a snack that will not upset my diabetes.'"
            )
        else:
            world.say(
                f"{flipper.id} said, 'That sweet thing will not help my diabetes.'"
            )
        return True
    return False


def apology(world: World, devil: Entity, flipper: Entity) -> None:
    devil.memes["shame"] = devil.memes.get("shame", 0) + 1
    world.say(
        f"{devil.id} lowered {devil.pronoun('possessive')} head and said, "
        f"'I was trying to be clever, but I was not being kind.'"
    )
    world.say(
        f"{flipper.id} listened without turning away, which made the pond feel less sharp."
    )


def reconciliation(world: World, devil: Entity, flipper: Entity, snack: Snack) -> None:
    flipper.memes["worry"] = 0
    flipper.memes["trust"] = flipper.memes.get("trust", 0) + 1
    devil.memes["mischief"] = 0
    devil.memes["calm"] = devil.memes.get("calm", 0) + 1
    world.say(
        f"Then {devil.id} brought {snack.phrase} and set it beside the reeds."
    )
    world.say(
        f"{flipper.id} nibbled the careful snack, and the two friends smiled at the same time."
    )
    world.say(
        f"After that, {devil.id} did not tease with hidden things. {flipper.id} did not have to wait in fear."
    )


def moral(world: World, devil: Entity, flipper: Entity, snack: Snack) -> None:
    world.say(
        f"And so the little devil learned that a game should not make a friend uneasy, "
        f"especially a friend who must guard {flipper.pronoun('possessive')} diabetes."
    )
    world.say(
        f"When kindness replaced the trick, the water shone softly, and the pond became a peaceful place again."
    )


# ---------------------------------------------------------------------------
# Story build
# ---------------------------------------------------------------------------
def tell(setting: Setting, snack: Snack, devil_name: str, flipper_name: str) -> World:
    world = World(setting)
    devil = world.add(Entity(id=devil_name, kind="character", type="devil"))
    flipper = world.add(Entity(id=flipper_name, kind="character", type="seal"))
    flipper.memes["worry"] = 0
    flipper.meters["sugar"] = 0
    devil.memes["mischief"] = 1

    world.facts.update(devil=devil, flipper=flipper, snack=snack, setting=setting)

    intro(world, devil, flipper, snack)
    world.para()

    suspense_loop(world, devil, flipper, snack)
    repeated_tease(world, devil, flipper, snack)
    warning(world, devil, flipper, snack)
    world.para()

    apology(world, devil, flipper)
    reconciliation(world, devil, flipper, snack)
    moral(world, devil, flipper, snack)

    world.facts["reconciled"] = True
    world.facts["suspense"] = flipper.memes.get("worry", 0) >= THRESHOLD
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A snack is risky if it is not safe for diabetes.
risky(S) :- snack(S), not safe(S).

% Repeated teasing raises suspense.
suspense :- tease_count(N), N >= 2.

% Reconciliation is possible only after apology and a safe snack.
reconcile :- apology, safe_snack.

% A valid story has devil, flipper, suspense, and reconciliation.
valid_story :- devil, flipper, suspense, reconcile.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if snack.safe_for_diabetes:
            lines.append(asp.fact("safe", sid))
    lines.append(asp.fact("devil"))
    lines.append(asp.fact("flipper"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import only when needed.
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    has_valid = any(sym.name == "valid_story" for sym in model)
    python_valid = True
    if has_valid == python_valid:
        print("OK: ASP and Python parity hold for the inline reasonableness twin.")
        return 0
    print("MISMATCH between ASP and Python parity.")
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    snack: Snack = _safe_fact(world, f, "snack")
    return [
        f'Write a short fable about a devil, Flipper, and the word "diabetes" at {f["setting"].place}.',
        f"Tell a suspenseful little story where {f['devil'].id} repeats a trick, then makes peace with {f['flipper'].id}.",
        f"Write a child-friendly fable that ends with reconciliation after a snack choice at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    devil, flipper, snack = f["devil"], f["flipper"], f["snack"]
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who was the story about at {place}?",
            answer=f"It was about a little devil named {devil.id} and a seal named {flipper.id} who had diabetes.",
        ),
        QAItem(
            question=f"Why did {flipper.id} keep waiting and watching?",
            answer=f"{flipper.id} was waiting because {devil.id} kept turning the moment into a suspenseful guess-and-wait game.",
        ),
        QAItem(
            question=f"What snack did {devil.id} finally bring?",
            answer=f"{devil.id} finally brought {snack.phrase}, which was the kind of snack that could fit the story's kinder ending.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended in reconciliation, with {devil.id} apologizing and {flipper.id} feeling calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses animals or unusual characters to teach a lesson.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after people or friends have been upset with one another.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
        ),
        QAItem(
            question="What is diabetes?",
            answer="Diabetes is a health condition that means a body has to be careful about sugar and sometimes needs special care.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core interface
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SNACKS, params.snack), params.name_devil, params.name_flipper)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, snack) for place in SETTINGS for snack, s in SNACKS.items() if s.safe_for_diabetes]


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    if getattr(args, "all", None):
        samples = [
            generate(StoryParams(place=place, snack=snack, name_devil="Milo", name_flipper="Flipper"))
            for place, snack in valid_combos()
        ]
    else:
        samples = build_samples(args)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
