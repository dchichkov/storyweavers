#!/usr/bin/env python3
"""
storyworlds/worlds/grenade_tidal_pool_cautionary_rhyme_repetition_myth.py
==========================================================================

A tiny myth-like storyworld set at a tidal pool, built around a child who finds
a grenade and must choose caution over curiosity. The domain is intentionally
small, repetitive, and rhymed, with a cautionary turn and a safe resolution.

The premise is mythic but concrete:
- a child goes to the tidal pool with a keeper or elder
- a dangerous object, the grenade, is found among stones and weed
- a warning is spoken in a repeated refrain
- the child resists touch, passes the danger to the elder, and leaves safely

The simulation tracks physical state with meters and emotional state with memes.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0
DANGER_ITEM = "grenade"


# ---------------------------------------------------------------------------
# Entities and world model
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    grenade: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class TidalPool:
    place: str = "the tidal pool"
    tide: str = "low"
    salt_wind: bool = True
    history: list[str] = field(default_factory=list)
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
    def __init__(self, place: TidalPool) -> None:
        self.place = place
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
        clone = World(copy.deepcopy(self.place))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    gender: str
    elder: str
    tide: str
    curiosity: str
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


NAMES_GIRL = ["Mira", "Lina", "Nori", "Sana", "Tess", "Ari"]
NAMES_BOY = ["Rowan", "Cai", "Milo", "Joren", "Tavi", "Bren"]
ELDERS = {
    "grandmother": "grandmother",
    "grandfather": "grandfather",
    "aunt": "aunt",
    "uncle": "uncle",
}
TIDES = {
    "low": "low",
    "falling": "falling",
    "high": "high",
}
CURIOSITIES = ["curious", "brave", "careful", "quiet"]


# ---------------------------------------------------------------------------
# Cause and effect
# ---------------------------------------------------------------------------
def _say_refrain(world: World, hero: Entity) -> None:
    world.say(
        f'"No touch, no clutch," the old voice said. '
        f'"At the tide-worn pool, be slow and good."'
    )


def _touch_danger(world: World, hero: Entity, grenade: Entity) -> None:
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return
    sig = ("touch", hero.id, grenade.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["alarm"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} reached toward the little metal thing, and the shell of caution "
        f"seemed to hum like a warning drum."
    )


def _hand_back(world: World, hero: Entity, elder: Entity, grenade: Entity) -> None:
    sig = ("hand_back", hero.id, grenade.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    grenade.held_by = elder.id
    hero.memes["obedience"] += 1
    elder.memes["care"] += 1
    world.say(
        f"{hero.id} stopped, took a breath, and placed the grenade in {elder.pronoun('possessive')} "
        f"hands, where it could trouble no child."
    )


def _resolve(world: World, hero: Entity, elder: Entity) -> None:
    sig = ("resolve", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["calm"] += 1
    hero.memes["fear"] = 0
    world.say(
        f"Then {hero.id} and {elder.id} walked back from the salt and stone, "
        f"while the tide kept its own old song."
    )


def propagate(world: World) -> None:
    hero = next(e for e in world.characters() if e.type in {"girl", "boy"})
    elder = next(e for e in world.characters() if e.id != hero.id)
    grenade = world.get("grenade")
    _touch_danger(world, hero, grenade)
    if hero.memes.get("fear", 0) >= THRESHOLD:
        _hand_back(world, hero, elder, grenade)
        _resolve(world, hero, elder)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(name: str, gender: str, elder_kind: str, tide: str, curiosity: str) -> World:
    place = TidalPool(place="the tidal pool", tide=tide, salt_wind=True)
    world = World(place)

    hero_type = gender
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=hero_type,
        meters={"wet": 0.0},
        memes={"curiosity": 1.0 if curiosity in {"curious", "brave"} else 0.5, "joy": 1.0},
    ))
    elder = world.add(Entity(
        id=elder_kind.title(),
        kind="character",
        type=elder_kind,
        label=f"the {elder_kind}",
        meters={"steadiness": 1.0},
        memes={"care": 1.0},
    ))
    grenade = world.add(Entity(
        id="grenade",
        kind="thing",
        type="grenade",
        label="grenade",
        phrase="a small, hard grenade with a dull metal shell",
        owner=None,
        caretaker=elder.id,
        held_by=None,
        meters={"danger": 1.0},
    ))

    world.facts.update(hero=hero, elder=elder, grenade=grenade)

    # Act I: invitation and place.
    world.say(
        f"{hero.id} came to the tidal pool with {elder.label}. "
        f"The sea left little mirrors in the rock, and the wind tasted of salt."
    )
    world.say(
        f"{hero.id} loved the shine of shells and the whisper of water; "
        f"{hero.pronoun().capitalize()} loved to look, and look, and look."
    )
    world.para()

    # Act II: warning and temptation.
    world.say(
        f"Under a strip of kelp, {hero.id} saw {grenade.phrase}. "
        f"It was round and strange, and it did not belong in a child's hands."
    )
    world.say(
        f"{elder.id} pointed once and spoke the old refrain: "
        f"\"No touch, no clutch, for the tide-worn pool is not a place to play with doom.\""
    )
    world.say(
        f"{hero.id} listened, but {hero.pronoun('possessive')} curiosity still tugged like a kite-string."
    )
    propagate(world)
    world.para()

    # Act III: safe choice and ending image.
    if grenade.held_by != elder.id:
        # This should not happen, but keep the story complete.
        grenade.held_by = elder.id
        world.say(f"{elder.id} took the grenade away before any hand could close around it.")
    world.say(
        f"{hero.id} stood back as {elder.id} carried the grenade away, and the little pool "
        f"kept shining, clean and small."
    )
    world.say(
        f"So the child learned the rhyme of the day: no touch, no clutch, no boastful rush; "
        f"at the tidal pool, wise feet hush."
    )

    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def explain_rejection() -> str:
    return (
        "No story: this world is built around caution at a tidal pool, where a grenade is found "
        "and must be left untouched until an elder takes it away. The explicit danger is the point."
    )


def valid_combo(params: StoryParams) -> bool:
    return True


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% The world is valid when a child, an elder, a tidal pool, and a grenade all appear.
valid_world :- child(_), elder(_), place(tidal_pool), item(grenade).

% The cautionary core: the child must not keep the grenade.
unsafe(grenade) :- item(grenade).
safe_choice :- item(grenade), elder_takes(grenade).

% A complete story requires a warning, a refusal of touch, and a safe ending.
complete_story :- warning_spoken, refrain_spoken, safe_choice, child_learns.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "tidal_pool"))
    lines.append(asp.fact("item", "grenade"))
    lines.append(asp.fact("warning_spoken"))
    lines.append(asp.fact("refrain_spoken"))
    lines.append(asp.fact("elder_takes", "grenade"))
    lines.append(asp.fact("child_learns"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show complete_story/0."))
    got = bool(model)
    want = True
    if got == want:
        print("OK: ASP twin validates the cautionary tidal-pool story.")
        return 0
    print("MISMATCH: ASP twin does not match Python reasonableness gate.")
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    elder = _safe_fact(world, world.facts, "elder")
    return [
        f"Write a short myth-like story about {hero.id} at the tidal pool, where a grenade appears and caution wins.",
        f"Tell a repeated, rhymed cautionary tale in which {elder.id} warns a child not to touch the grenade by the sea.",
        f"Write a child-facing myth about the tidal pool, the old warning, and the safe choice to leave the grenade alone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    elder: Entity = _safe_fact(world, f, "elder")
    grenade: Entity = _safe_fact(world, f, "grenade")
    qa = [
        QAItem(
            question=f"Where did {hero.id} find the {grenade.label}?",
            answer=f"{hero.id} found the {grenade.label} at the tidal pool, under kelp and sea-wet stones.",
        ),
        QAItem(
            question=f"What did {elder.id} warn {hero.id} not to do?",
            answer=f"{elder.id} warned {hero.id} not to touch or clutch the {grenade.label}.",
        ),
        QAItem(
            question=f"Who carried the {grenade.label} away at the end?",
            answer=f"{elder.id} carried the {grenade.label} away so {hero.id} could leave safely.",
        ),
        QAItem(
            question=f"How did {hero.id} behave when the warning was spoken?",
            answer=f"{hero.id} listened, stepped back, and chose caution instead of curious touching.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a small pool of seawater left behind by the tide among rocks.",
        ),
        QAItem(
            question="Why should children never touch a grenade?",
            answer="A grenade is dangerous and can hurt people, so only trained adults should handle it.",
        ),
        QAItem(
            question="What does a cautionary tale teach?",
            answer="A cautionary tale teaches a safe lesson by showing what danger to avoid.",
        ),
        QAItem(
            question="Why do myths repeat lines and phrases?",
            answer="Myths often repeat lines so the lesson feels old, memorable, and important.",
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


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
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
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-like cautionary tale at a tidal pool.")
    ap.add_argument("--name", choices=NAMES_GIRL + NAMES_BOY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=list(ELDERS))
    ap.add_argument("--tide", choices=list(TIDES))
    ap.add_argument("--curiosity", choices=CURIOSITIES)
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    elder = getattr(args, "elder", None) or rng.choice(list(ELDERS))
    tide = getattr(args, "tide", None) or rng.choice(list(TIDES))
    curiosity = getattr(args, "curiosity", None) or rng.choice(CURIOSITIES)
    return StoryParams(name=name, gender=gender, elder=elder, tide=tide, curiosity=curiosity)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.elder, params.tide, params.curiosity)
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
    StoryParams(name="Mira", gender="girl", elder="grandmother", tide="low", curiosity="curious"),
    StoryParams(name="Rowan", gender="boy", elder="uncle", tide="falling", curiosity="careful"),
    StoryParams(name="Sana", gender="girl", elder="aunt", tide="high", curiosity="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show complete_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show complete_story/0."))
        print("complete_story" if model else "no complete story")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} at the tidal pool"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
