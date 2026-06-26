#!/usr/bin/env python3
"""
A standalone storyworld for a small detective story set around a temple and a
nearby mountain range.

Premise:
A child detective notices a temple bell has gone missing. Clues are scattered
between the temple courtyard and the mountain range above it. The detective uses
foreshadowing and a little humor to follow the trail, discover who moved the
bell, and restore the peaceful evening ceremony.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    sidekick: object | None = None
    suspect: object | None = None
    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount
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


class World:
    def __init__(self, setting: "Setting") -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paras: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    paras.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            paras.append(" ".join(buf))
        return "\n\n".join(paras)


@dataclass
class Setting:
    place: str = "the temple courtyard"
    nearby_range: str = "the cedar range"
    indoors: bool = False
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
    range_name: str
    suspect: str
    detective_name: str
    sidekick_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
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


SETTINGS = {
    "temple": Setting(place="the temple courtyard", nearby_range="the cedar range"),
    "shrine": Setting(place="the shrine steps", nearby_range="the blue range"),
    "hall": Setting(place="the old temple hall", nearby_range="the stone range", indoors=True),
}

SUSPECTS = {
    "monkey": {
        "label": "a noisy monkey",
        "humor": "It had a banana peel stuck to one ear like a tiny hat.",
        "motive": "it liked shiny things and had mistaken the bell for a toy",
    },
    "goat": {
        "label": "a stubborn goat",
        "humor": "It had a beard that bounced like a broom when it walked.",
        "motive": "it had wandered in looking for salt and pushed the bell by accident",
    },
    "kite": {
        "label": "a tangled kite",
        "humor": "It was draped over a tree branch like a sleepy scarf.",
        "motive": "the wind had carried it across the yard and wrapped it around the clue path",
    },
}

DETECTIVE_TRAITS = ["careful", "curious", "brave", "sharp-eyed", "patient"]
SIDEKICK_TRAITS = ["cheerful", "silly", "chatty", "quick-footed"]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.

valid(P, R, S) :- place(P), range(R), suspect(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for r in {"cedar", "blue", "stone"}:
        lines.append(asp.fact("range", f"{r}_range"))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for rng in ["cedar", "blue", "stone"]:
            for suspect in SUSPECTS:
                combos.append((place, rng, suspect))
    return combos

def explain_invalid(place: Optional[str], rng: Optional[str], suspect: Optional[str]) -> str:
    return (
        "No story: the chosen temple, range, and suspect do not fit the detective "
        "setup, or there are not enough clues to make a satisfying mystery."
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def intro_detective(world: World, detective: Entity, sidekick: Entity) -> None:
    world.say(
        f"{detective.id} was a {random.choice(DETECTIVE_TRAITS)} little detective "
        f"who loved solving mysteries near {world.setting.place}."
    )
    world.say(
        f"{sidekick.id} was {random.choice(SIDEKICK_TRAITS)} and always carried a notebook "
        f"that had more doodles than notes."
    )

def set_scene(world: World) -> None:
    world.say(
        f"At dusk, {world.setting.place} glowed softly, and {world.setting.nearby_range} "
        f"stood dark against the sky."
    )
    world.say(
        f"An old bell was supposed to ring for evening prayers, but tonight the rope "
        f"swung empty."
    )

def foreshadow(world: World) -> None:
    world.say(
        "A little silver trail on the stone steps caught the detective's eye. "
        "It looked like nothing important, which was exactly why it felt important."
    )
    world.say(
        "The sidekick joked that the clue was probably a worm in fancy shoes, but "
        "the detective only smiled and kept looking."
    )
    world.facts["foreshadowing"] = True

def investigate(world: World, detective: Entity, sidekick: Entity, suspect: Entity) -> None:
    detective.bump_meme("focus", 1)
    world.say(
        f"{detective.id} followed the silver marks past the prayer wall and up toward "
        f"{world.setting.nearby_range}."
    )
    world.say(
        f"Near a windy ledge, they found {suspect.phrase}, and {suspect.label} made the "
        f"whole trail feel a little less scary and a little more silly."
    )
    world.say(suspect.meters.get("clue", 0) and "")
    world.say(
        f"{suspect.label.capitalize()} left a trail because {suspect.motive}."
    )
    world.facts["suspect_label"] = suspect.label
    world.facts["suspect_motive"] = suspect.motive

def reveal(world: World, detective: Entity, sidekick: Entity, suspect: Entity) -> None:
    world.say(
        f"Then {detective.id} noticed the truth: the bell had not been stolen at all."
    )
    world.say(
        f"{suspect.label.capitalize()} had nudged it onto a padded cart during cleaning, "
        f"and the cart had rolled to the storage shed below the path."
    )
    world.say(
        f"The mystery was funny after all; the great missing bell had been hiding "
        f"two doors away like a sleepy cat."
    )

def resolve(world: World, detective: Entity, sidekick: Entity) -> None:
    world.say(
        f"{detective.id} and {sidekick.id} rolled the bell back, and the temple rang "
        f"warm and clear across the range."
    )
    world.say(
        f"The priest thanked them, the suspect looked embarrassed, and the sidekick "
        f"said the best clues were the ones that rang a bell in the end."
    )
    world.facts["resolved"] = True

def tell_story(setting: Setting, suspect_key: str, detective_name: str, sidekick_name: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", label="detective"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", label="sidekick"))
    suspect = world.add(Entity(
        id=suspect_key,
        kind="character" if suspect_key in {"monkey", "goat"} else "thing",
        label=_safe_lookup(SUSPECTS, suspect_key)["label"],
        phrase=_safe_lookup(SUSPECTS, suspect_key)["label"],
        location=setting.place,
    ))
    world.facts["setting"] = setting
    world.facts["suspect_key"] = suspect_key
    world.facts["detective"] = detective
    world.facts["sidekick"] = sidekick
    world.facts["suspect"] = suspect

    intro_detective(world, detective, sidekick)
    world.para()
    set_scene(world)
    foreshadow(world)
    world.para()
    investigate(world, detective, sidekick, suspect)
    world.para()
    reveal(world, detective, sidekick, suspect)
    resolve(world, detective, sidekick)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: Setting = _safe_fact(world, world.facts, "setting")  # type: ignore[assignment]
    suspect_key: str = (world.facts.get("suspect_key") if hasattr(world.facts, "get") else _safe_fact(world, world.facts, "suspect_key"))  # type: ignore[assignment]
    return [
        f"Write a short detective story set at {p.place} near {p.nearby_range} about a missing bell and {_safe_lookup(SUSPECTS, suspect_key)['label']}.",
        "Tell a child-friendly mystery with foreshadowing, a funny clue, and a clear ending.",
        f"Create a story where a detective follows clues from a temple to a mountain range and solves the puzzle.",
    ]

def story_qa(world: World) -> list[QAItem]:
    p: Setting = _safe_fact(world, world.facts, "setting")  # type: ignore[assignment]
    suspect: Entity = _safe_fact(world, world.facts, "suspect")  # type: ignore[assignment]
    detective: Entity = _safe_fact(world, world.facts, "detective")  # type: ignore[assignment]
    sidekick: Entity = _safe_fact(world, world.facts, "sidekick")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {detective.id} look for clues first?",
            answer=f"{detective.id} looked first at {p.place}, because the missing bell was supposed to ring there.",
        ),
        QAItem(
            question="What small clue helped foreshadow the answer?",
            answer="A silver trail on the stone steps hinted that the bell had been moved, even though the clue looked tiny at first.",
        ),
        QAItem(
            question=f"Who or what turned out to be part of the mystery?",
            answer=f"{suspect.label.capitalize()} turned out to be part of the mystery, but not because of a real theft.",
        ),
        QAItem(
            question=f"How did {sidekick.id} add humor to the story?",
            answer="The sidekick made a funny joke about the clue, which kept the mystery light and child-friendly.",
        ),
        QAItem(
            question="What was the ending image?",
            answer="The bell was rolled back, the temple rang clearly, and the range echoed with a peaceful sound.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a temple?",
            answer="A temple is a special building where people go to pray, reflect, or take part in ceremonies.",
        ),
        QAItem(
            question="What is a mountain range?",
            answer="A mountain range is a group of mountains lined up across the land.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small hint early on about something important that will happen later.",
        ),
        QAItem(
            question="What is humor in a story?",
            answer="Humor is something funny or playful that makes a story feel light and enjoyable.",
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
# Params and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective storyworld set around a temple and a range.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--range-name", dest="range_name", choices=["cedar", "blue", "stone"])
    ap.add_argument("--suspect", choices=SUSPECTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    range_name = getattr(args, "range_name", None) or rng.choice(["cedar", "blue", "stone"])
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS.keys()))
    detective_name = getattr(args, "name", None) or rng.choice(["Mina", "Ivo", "Nia", "Tari", "Lina", "Jae"])
    sidekick_name = getattr(args, "sidekick", None) or rng.choice(["Pip", "Momo", "Bea", "Zuri", "Toto"])
    if (getattr(args, "place", None) or getattr(args, "range_name", None) or getattr(args, "suspect", None)) and (place, range_name, suspect) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, range_name=range_name, suspect=suspect,
                       detective_name=detective_name, sidekick_name=sidekick_name)

def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    world = tell_story(setting, params.suspect, params.detective_name, params.sidekick_name)
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
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} label={e.label} location={e.location} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="temple", range_name="cedar", suspect="monkey", detective_name="Mina", sidekick_name="Pip"),
    StoryParams(place="shrine", range_name="blue", suspect="goat", detective_name="Ivo", sidekick_name="Bea"),
    StoryParams(place="hall", range_name="stone", suspect="kite", detective_name="Nia", sidekick_name="Toto"),
]

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print("  ", t)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
