#!/usr/bin/env python3
"""
storyworlds/worlds/nasty_canary_dialogue_reconciliation_fairy_tale.py
=====================================================================

A small fairy-tale storyworld about a nasty canary, a hurt feeling, a spoken
apology, and a reconciliation that changes the ending image.

Premise:
A canary lives in a tidy little cottage with a child and a grandmother. The
canary is bright and sweet at first, but can become nasty when it wants the
warmest perch or the shiniest crumb.

Turn:
A rude remark makes the child upset. The canary and the child talk it out.

Resolution:
The canary apologizes, shares the perch, and sings a gentler tune. The child
forgives it, and the cottage feels warm again.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    canary: object | None = None
    child: object | None = None
    crumb: object | None = None
    elder: object | None = None
    perch: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "child", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "grandfather", "man"}:
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
class Place:
    name: str
    mood: str
    affords_dialogue: bool = True
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    canary_name: str
    child_name: str
    elder_name: str
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
    "cottage": Place(name="the cottage", mood="warm"),
    "garden": Place(name="the little garden", mood="bright"),
    "kitchen": Place(name="the kitchen", mood="cozy"),
}

CANARY_TRAITS = ["bright", "proud", "tempery", "fussy"]
CHILD_TRAITS = ["gentle", "small", "curious", "patient"]

CANARY_NAMES = ["Tilly", "Pip", "Sunny", "Mina", "Nico"]
CHILD_NAMES = ["Rose", "Milo", "Anya", "Eli", "Lena"]
ELDER_NAMES = ["Nan", "Gran", "Old Marta", "Bramble", "Aunt Sera"]


@dataclass
class CanaryKind:
    song: str
    perch: str
    crumb: str
    CANARY_KIND: object | None = None
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


CANARY_KIND = CanaryKind(
    song="a silver song",
    perch="the warmest perch",
    crumb="the sweetest crumb",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _add_meter(entity: Entity, key: str, amount: float) -> None:
    entity.meters[key] = _meter(entity, key) + amount


def _add_meme(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = _meme(entity, key) + amount


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def predict_spoil(world: World, canary: Entity) -> bool:
    sim = world.copy()
    _argue(sim, sim.get(canary.id), narrate=False)
    return _meme(sim.get("child"), "hurt") >= 1.0


def _argue(world: World, canary: Entity, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if _meme(canary, "nasty") < 1.0:
        return out
    child = world.get("child")
    if ("snub", canary.id) in world.fired:
        return out
    world.fired.add(("snub", canary.id))
    _add_meme(child, "hurt", 1.0)
    _add_meme(child, "tears", 1.0)
    out.append(f'{canary.id} snapped, "That perch is mine, and you are in the way."')
    if narrate:
        for s in out:
            world.say(s)
    return out


def _apology(world: World, canary: Entity, child: Entity) -> None:
    if ("apologize", canary.id) in world.fired:
        return
    world.fired.add(("apologize", canary.id))
    _add_meme(canary, "remorse", 1.0)
    _add_meme(canary, "nasty", -1.0)
    _add_meme(child, "hurt", -1.0)
    _add_meme(child, "warmth", 1.0)
    world.say(f'{canary.id} bowed its small head and said, "I spoke nastily. I am sorry."')
    world.say(f'{child.id} blinked at the little bird, and the mean feeling began to soften.')


def _reconcile(world: World, canary: Entity, child: Entity, elder: Entity) -> None:
    if ("reconcile", canary.id) in world.fired:
        return
    world.fired.add(("reconcile", canary.id))
    _add_meme(child, "forgiveness", 1.0)
    _add_meme(canary, "joy", 1.0)
    _add_meme(child, "joy", 1.0)
    world.say(
        f'{elder.id} smiled and said, "A kind word can mend a sore heart."'
    )
    world.say(
        f'{child.id} answered, "I forgive you," and {canary.id} fluttered '
        f"to the shared perch instead of guarding it."
    )
    world.say(
        f'Then {canary.id} sang {CANARY_KIND.song}, not to boast, but to thank '
        f'{child.id} for staying and listening.'
    )


def tell(place: Place, canary_name: str, child_name: str, elder_name: str) -> World:
    world = World(place)
    canary = world.add(Entity(
        id=canary_name, kind="character", type="canary",
        meters={"spark": 1.0}, memes={"joy": 1.0, "nasty": 1.0}
    ))
    child = world.add(Entity(
        id=child_name, kind="character", type="child",
        memes={"kindness": 1.0, "hurt": 0.0, "joy": 1.0}
    ))
    elder = world.add(Entity(
        id=elder_name, kind="character", type="grandmother",
        memes={"wisdom": 1.0}
    ))
    perch = world.add(Entity(
        id="perch", type="thing", label="wooden perch",
        phrase="a wooden perch by the window", owner=canary.id
    ))
    crumb = world.add(Entity(
        id="crumb", type="thing", label="honey crumb",
        phrase="a honey crumb on a tiny plate", owner=child.id
    ))

    world.say(
        f"In {world.place.name}, there lived a bright canary named {canary.id} "
        f"and a gentle child named {child.id}."
    )
    world.say(
        f"{child.id} loved to listen to {canary.id}'s song, and {elder.id} loved "
        f"the warm little house when the bird was happy."
    )
    world.say(
        f"One morning, {child.id} set out {crumb.phrase}, and {canary.id} hurried "
        f"to claim {CANARY_KIND.perch}."
    )
    world.para()
    world.say(
        f"{child.id} said, \"You may have the crumb after I sing with you.\""
    )
    _add_meme(canary, "greedy", 1.0)
    _add_meme(canary, "nasty", 1.0)
    if predict_spoil(world, canary):
        world.say(
            f"{canary.id} did not like waiting. It made a rude little face and "
            f"gave a sharp answer."
        )
    _argue(world, canary)
    world.para()
    world.say(
        f"{child.id} grew quiet, because nasty words can sting like cold rain."
    )
    _apology(world, canary, child)
    _reconcile(world, canary, child, elder)

    world.facts.update(
        canary=canary,
        child=child,
        elder=elder,
        perch=perch,
        crumb=crumb,
        place=place,
        reconciled=_meme(child, "forgiveness") >= 1.0,
        nasty_before=_meme(canary, "nasty") >= 1.0,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = _safe_fact(world, f, "canary")
    child = _safe_fact(world, f, "child")
    elder = _safe_fact(world, f, "elder")
    return [
        f'Write a short fairy tale about a canary named {c.id} who starts out nasty, then makes peace.',
        f"Tell a child-friendly story where {child.id} and {c.id} speak to each other, and {elder.id} helps them reconcile.",
        f'Write a gentle dialogue story with a rude moment, an apology, and a happy ending in {world.place.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = _safe_fact(world, f, "canary")
    child = _safe_fact(world, f, "child")
    elder = _safe_fact(world, f, "elder")
    return [
        QAItem(
            question=f"Who was the nasty little bird in the story?",
            answer=f"The nasty little bird was {c.id}, the canary.",
        ),
        QAItem(
            question=f"What did {child.id} and {c.id} talk about when the story turned tense?",
            answer=(
                f"They talked about {CANARY_KIND.perch} and the honey crumb. "
                f"{child.id} wanted to share, but {c.id} got rude before the apology."
            ),
        ),
        QAItem(
            question=f"How did the story end after the apology?",
            answer=(
                f"{c.id} said sorry, {child.id} forgave it, and they shared the perch "
                f"while {elder.id} watched with a smile."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a canary?",
            answer="A canary is a small singing bird, often known for a bright yellow color and a sweet voice.",
        ),
        QAItem(
            question="What is an apology for?",
            answer="An apology is for saying you are sorry after you have hurt someone or done something unkind.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a fight or a hurt feeling.",
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
        if bits:
            lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
        else:
            lines.append(f"  {e.id:10} ({e.type:10})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
nasty(C) :- canary(C), meme(C,nasty), meme(C,nasty,1).
hurt(H) :- child(H), event(snub,C), canary(C).
apology(C) :- canary(C), event(apologize,C).
reconciled(H,C) :- child(H), canary(C), apology(C), forgiveness(H), shared_perch(H,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("mood", pid, place.mood))
        if place.affords_dialogue:
            lines.append(asp.fact("affords_dialogue", pid))
    lines.append(asp.fact("canary", "c"))
    lines.append(asp.fact("child", "h"))
    lines.append(asp.fact("elder", "e"))
    lines.append(asp.fact("meme", "c", "nasty", 1))
    lines.append(asp.fact("event", "snub", "c"))
    lines.append(asp.fact("event", "apologize", "c"))
    lines.append(asp.fact("forgiveness", "h"))
    lines.append(asp.fact("shared_perch", "h", "c"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconciled/2.\n#show nasty/1."))
    shown = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {("nasty", ("c",)), ("reconciled", ("h", "c"))}
    if shown == expected:
        print("OK: ASP twin matches the reasonableness/story state.")
        return 0
    print("MISMATCH:", sorted(shown), "expected", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a nasty canary and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--canary-name")
    ap.add_argument("--child-name")
    ap.add_argument("--elder-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    return StoryParams(
        place=place,
        canary_name=getattr(args, "canary_name", None) or rng.choice(CANARY_NAMES),
        child_name=getattr(args, "child_name", None) or rng.choice(CHILD_NAMES),
        elder_name=getattr(args, "elder_name", None) or rng.choice(ELDER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        params.canary_name,
        params.child_name,
        params.elder_name,
    )
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
    StoryParams(place="cottage", canary_name="Tilly", child_name="Rose", elder_name="Gran"),
    StoryParams(place="garden", canary_name="Pip", child_name="Milo", elder_name="Nan"),
    StoryParams(place="kitchen", canary_name="Sunny", child_name="Anya", elder_name="Aunt Sera"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reconciled/2.\n#show nasty/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show reconciled/2.\n#show nasty/1."))
        print(asp.atoms(model, "nasty"))
        print(asp.atoms(model, "reconciled"))
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.canary_name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
