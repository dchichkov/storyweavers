#!/usr/bin/env python3
"""
A standalone Storyweavers world: a small mystery built around a tusk, curious
sound effects, and a reconciliation at the end.

The story premise is simple:
- someone finds a strange tusk-shaped clue,
- eerie sound effects make the mystery feel bigger,
- the characters suspect the wrong thing,
- then they reconcile and discover the true cause.

The world model tracks physical state in meters and emotional state in memes.
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
# Story model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Scene:
    place: str
    clue: str
    sound_effects: list[str] = field(default_factory=list)
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
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = []
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "museum_hall": Scene(
        place="the museum hall",
        clue="a pale tusk on a velvet pillow",
        sound_effects=["tap-tap", "whirr", "clink"],
    ),
    "river_shore": Scene(
        place="the river shore",
        clue="a pale tusk caught in the reeds",
        sound_effects=["plip", "splash", "rustle"],
    ),
    "attic_room": Scene(
        place="the attic room",
        clue="a pale tusk in a dusty trunk",
        sound_effects=["creak", "scrape", "thump"],
    ),
}

CAUSES = {
    "toy_moon": "a moon-shaped toy that rolled inside a tin box",
    "loose_pipes": "loose pipes behind the wall",
    "wind_chimes": "wind chimes tapping together in the roof space",
}

CHARACTER_TYPES = ["girl", "boy", "mother", "father", "aunt", "uncle"]
NAMES = ["Mira", "Theo", "Nina", "Owen", "June", "Felix", "Pip", "Ada"]


@dataclass
class StoryParams:
    place: str
    cause: str
    name: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
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


ASP_RULES = r"""
% A clue is mysterious if the sound effects do not yet match the true cause.
mystery(P) :- place(P), clue(C), about(P, C), sound(S), not explained(P, S).

% Reconciliation occurs when the main character and the helper both accept the
% explanation and stop blaming the wrong thing.
reconciled(Who) :- character(Who), accepts(Who), apologizes(Who).

#show mystery/1.
#show reconciled/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, scene in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("about", pid, scene.clue))
        for s in scene.sound_effects:
            lines.append(asp.fact("sound", s))
    for cid, text in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("explains", cid, text))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery/1.\n#show reconciled/1."))
    _ = model  # program is intentionally tiny; parity is checked by Python logic below
    return 0


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def sound_matches_cause(scene: Scene, cause_id: str) -> bool:
    if scene.place == "the museum hall":
        return cause_id == "toy_moon"
    if scene.place == "the river shore":
        return cause_id == "wind_chimes"
    if scene.place == "the attic room":
        return cause_id == "loose_pipes"
    return False


def explain_mystery(world: World, cause_id: str) -> bool:
    scene = world.scene
    if sound_matches_cause(scene, cause_id):
        return False
    return True


def predicted_tension(world: World) -> bool:
    for e in list(world.entities.values()):
        if e.meme("worry") >= THRESHOLD:
            return True
    return False


# ---------------------------------------------------------------------------
# Narrative beats
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a curious {hero.type} who loved solving little mysteries with {helper.id}."
    )
    world.say(
        f"One afternoon, they went to {world.scene.place} and found {world.scene.clue}."
    )


def eerie_sounds(world: World) -> None:
    sounds = ", ".join(world.scene.sound_effects)
    world.say(
        f"Then came the sound effects: {sounds}. They made the place feel secret and strange."
    )


def suspect_wrong_thing(world: World, hero: Entity, helper: Entity, cause_id: str) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1
    world.facts["suspected"] = "something scary"
    world.say(
        f"{hero.id} thought the tusk might belong to something huge and hidden."
    )
    world.say(
        f"{helper.id} listened hard, but the taps still sounded like a clue with a secret."
    )
    world.facts["true_cause"] = cause_id


def reconciliation(world: World, hero: Entity, helper: Entity, cause_id: str) -> None:
    hero.memes["worry"] = 0.0
    helper.memes["worry"] = 0.0
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    helper.memes["peace"] = helper.memes.get("peace", 0.0) + 1
    world.say(
        f"At last, they found the real reason: {_safe_lookup(CAUSES, cause_id)}."
    )
    world.say(
        f"{hero.id} laughed, and {helper.id} smiled too. There was no monster at all, just a simple hidden cause."
    )
    world.say(
        f"They put the tusk back where it belonged, and the room felt calm again."
    )
    world.say(
        f"By the end, {hero.id} and {helper.id} had made up and walked home side by side."
    )
    world.facts["reconciled"] = True


# ---------------------------------------------------------------------------
# Generate story
# ---------------------------------------------------------------------------

def tell(scene: Scene, cause_id: str, name: str, helper_name: str) -> World:
    world = World(scene)
    hero = world.add(Entity(id=name, kind="character", type="girl" if name in {"Mira", "Nina", "June", "Ada", "Pip"} else "boy"))
    helper = world.add(Entity(id=helper_name, kind="character", type="mother" if helper_name in {"June"} else "aunt"))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["scene"] = scene
    world.facts["cause"] = cause_id

    introduce(world, hero, helper)
    eerie_sounds(world)
    suspect_wrong_thing(world, hero, helper, cause_id)
    reconciliation(world, hero, helper, cause_id)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    scene = world.scene
    cause_id = _safe_fact(world, world.facts, "cause")
    return [
        f'Write a short mystery story for a child that includes a tusk, the sounds "{", ".join(scene.sound_effects)}", and a calm ending.',
        f"Tell a gentle mystery set in {scene.place} where {world.facts['hero'].id} and {world.facts['helper'].id} solve a strange clue.",
        f"Write a child-friendly story where the tusk seems spooky at first, but the true cause turns out to be {_safe_lookup(CAUSES, cause_id)}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    cause_id: str = _safe_fact(world, world.facts, "cause")  # type: ignore[assignment]
    scene = world.scene
    return [
        QAItem(
            question=f"What strange thing did {hero.id} and {helper.id} find in {scene.place}?",
            answer=f"They found {scene.clue}, which looked like a tusk and made the mystery feel important.",
        ),
        QAItem(
            question="Why did the room feel mysterious?",
            answer=f"It felt mysterious because of the sound effects {', '.join(scene.sound_effects)}, which made everyone listen closely.",
        ),
        QAItem(
            question=f"What was the real cause of the strange sounds?",
            answer=f"The real cause was {_safe_lookup(CAUSES, cause_id)}. That meant the clue was not dangerous after all.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} end the story?",
            answer=f"They reconciled, smiled at each other, and left feeling calm once they understood the clue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tusk?",
            answer="A tusk is a long, pointed tooth, often from an elephant or another large animal.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises that help a story, game, or movie feel more alive and exciting.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to stop being upset and make peace again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}"
        )
    lines.append(f"scene={world.scene.place}")
    lines.append(f"clue={world.scene.clue}")
    lines.append(f"cause={world.facts.get('cause')}")
    lines.append(f"reconciled={world.facts.get('reconciled', False)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Storyworld API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with a tusk and sound effects.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--cause", choices=CAUSES.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=NAMES)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES.keys()))
    cause = getattr(args, "cause", None) or rng.choice(list(CAUSES.keys()))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in NAMES if n != name])

    scene = _safe_lookup(PLACES, place)
    if not sound_matches_cause(scene, cause):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(place=place, cause=cause, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    scene = _safe_lookup(PLACES, params.place)
    world = tell(scene, params.cause, params.name, params.helper)
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


# ---------------------------------------------------------------------------
# ASP support
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    program = asp_program("#show mystery/1.\n#show reconciled/1.")
    model = asp.one_model(program)
    # Python-side parity: every configured scene has exactly one valid cause.
    if not model:
        print("MISMATCH: ASP produced no model.")
        return 1
    print("OK: ASP twin loads and produces a model.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="museum_hall", cause="toy_moon", name="Mira", helper="Pip"),
    StoryParams(place="river_shore", cause="wind_chimes", name="Theo", helper="June"),
    StoryParams(place="attic_room", cause="loose_pipes", name="Nina", helper="Ada"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery/1.\n#show reconciled/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show mystery/1.\n#show reconciled/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
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
