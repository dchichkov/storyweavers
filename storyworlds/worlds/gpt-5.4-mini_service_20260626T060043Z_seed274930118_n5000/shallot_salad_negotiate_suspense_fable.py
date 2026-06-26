#!/usr/bin/env python3
"""
storyworlds/worlds/shallot_salad_negotiate_suspense_fable.py
=============================================================

A tiny fable-style storyworld about a salad bowl full of ingredients that must
negotiate before supper. The tension comes from suspense: one small shallot
wants to be included, while the other vegetables worry that its sharpness may
overpower the bowl. A fair agreement changes the state of the salad and the
ending image.

Seed tale premise:
- A bowl of salad is being prepared.
- A shallot wants to join.
- The salad ingredients negotiate a compromise.
- The final bowl is balanced, and the shallot is sliced very thin.

This world is intentionally small, concrete, and state-driven.
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bowl: object | None = None
    dress: object | None = None
    leaf: object | None = None
    s: object | None = None
    sh: object | None = None
    tomo: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)
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
    place: str = "the kitchen"
    mood: str = "quiet"
    suspense: bool = True
    bowl_clean: bool = True
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
class Ingredient:
    id: str
    label: str
    phrase: str
    taste: str
    texture: str
    can_bloom: bool = False
    is_allium: bool = False
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
    salad: str
    shallot_style: str
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
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        other = World(copy.deepcopy(self.scene))
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


SETTINGS = {
    "kitchen": Scene(place="the kitchen", mood="quiet", suspense=True),
    "garden": Scene(place="the garden table", mood="windy", suspense=True),
    "picnic": Scene(place="the picnic blanket", mood="bright", suspense=True),
}

SALADS = {
    "green": Ingredient(
        id="salad", label="salad", phrase="a fresh green salad",
        taste="crisp", texture="cool", can_bloom=False
    ),
    "farm": Ingredient(
        id="salad", label="salad", phrase="a garden salad with leaves and tomatoes",
        taste="bright", texture="crunchy", can_bloom=False
    ),
    "feast": Ingredient(
        id="salad", label="salad", phrase="a supper salad with lettuce, cucumber, and herbs",
        taste="gentle", texture="mixed", can_bloom=False
    ),
}

SHALLOTS = {
    "whole": Ingredient(
        id="shallot", label="shallot", phrase="a small shallot",
        taste="sharp", texture="firm", is_allium=True
    ),
    "thin": Ingredient(
        id="shallot", label="shallot", phrase="a small shallot sliced very thin",
        taste="mild", texture="soft", is_allium=True
    ),
    "golden": Ingredient(
        id="shallot", label="shallot", phrase="a shallot with golden rings",
        taste="sweet", texture="tender", is_allium=True
    ),
}

CHARACTERS = {
    "bowl": {"label": "the bowl", "role": "host"},
    "leaf": {"label": "the lettuce leaf", "role": "guest"},
    "tomato": {"label": "the tomato", "role": "guest"},
    "cucumber": {"label": "the cucumber", "role": "guest"},
    "dressing": {"label": "the dressing", "role": "keeper"},
}

ASP_RULES = r"""
% Compatibility is a question of the salad's patience.
can_join(S, Sh) :- salad(S), shallot(Sh), balance_ok(S, Sh).

balance_ok(S, Sh) :- mild(Sh).
balance_ok(S, Sh) :- sweet(Sh), bright_salad(S).

suspense(S, Sh) :- salad(S), shallot(Sh), shallot_status(Sh, whole), not balance_ok(S, Sh).

resolution(S, Sh) :- salad(S), shallot(Sh), balance_ok(S, Sh), accepted(S, Sh).

#show can_join/2.
#show suspense/2.
#show resolution/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("salad_scene", s))
    for s in SALADS.values():
        lines.append(asp.fact("salad", s.id))
        if "bright" in s.taste:
            lines.append(asp.fact("bright_salad", s.id))
    for sh_name, sh in SHALLOTS.items():
        lines.append(asp.fact("shallot", sh.id))
        lines.append(asp.fact("shallot_status", sh.id, sh_name))
        if sh.taste in {"mild", "sweet"}:
            lines.append(asp.fact("mild", sh.id))
        if sh.taste == "sweet":
            lines.append(asp.fact("sweet", sh.id))
    lines.append(asp.fact("accepted", "green", "thin"))
    lines.append(asp.fact("accepted", "farm", "golden"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_join/2.\n#show suspense/2.\n#show resolution/2."))
    can_join = set(asp.atoms(model, "can_join"))
    suspense = set(asp.atoms(model, "suspense"))
    resolution = set(asp.atoms(model, "resolution"))
    py = set()
    for salad_id, salad in SALADS.items():
        for sh_id, sh in SHALLOTS.items():
            if balance_ok_py(salad, sh):
                py.add((salad_id, sh_id))
    if can_join != py:
        print("MISMATCH between ASP and Python can_join:")
        print("  asp:", sorted(can_join))
        print("  py :", sorted(py))
        return 1
    if not suspense:
        print("Warning: no suspense atoms found.")
    if not resolution:
        print("Warning: no resolution atoms found.")
    print(f"OK: ASP parity verified ({len(py)} compatible pairs).")
    return 0


def balance_ok_py(salad: Ingredient, shallot: Ingredient) -> bool:
    return shallot.taste in {"mild", "sweet"} or (shallot.taste == "sharp" and salad.label == "salad" and salad.phrase.startswith("a garden"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about a shallot and a salad negotiating suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--salad", choices=SALADS)
    ap.add_argument("--shallot-style", choices=SHALLOTS)
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
    salad = getattr(args, "salad", None) or rng.choice(list(SALADS))
    shallot_style = getattr(args, "shallot_style", None) or rng.choice(list(SHALLOTS))
    salad_obj = _safe_lookup(SALADS, salad)
    shallot_obj = _safe_lookup(SHALLOTS, shallot_style)
    if not balance_ok_py(salad_obj, shallot_obj):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, salad=salad, shallot_style=shallot_style)


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    salad = _safe_lookup(SALADS, params.salad)
    shallot = _safe_lookup(SHALLOTS, params.shallot_style)
    bowl = world.add(Entity(id="bowl", kind="thing", label="the bowl", role="host", meters={"clean": 1.0}, memes={"hunger": 1.0}))
    s = world.add(Entity(id="salad", kind="thing", label=salad.label, phrase=salad.phrase, role="meal", meters={"ready": 0.5}, memes={"calm": 1.0}))
    sh = world.add(Entity(id="shallot", kind="thing", label=shallot.label, phrase=shallot.phrase, role="guest", meters={"sharpness": 1.0 if shallot.taste == "sharp" else 0.5}, memes={"hope": 1.0}))
    leaf = world.add(Entity(id="leaf", kind="thing", label="the lettuce leaf", role="guest", meters={"fresh": 1.0}, memes={"worry": 0.2}))
    tomo = world.add(Entity(id="tomato", kind="thing", label="the tomato", role="guest", meters={"red": 1.0}, memes={"worry": 0.2}))
    dress = world.add(Entity(id="dressing", kind="thing", label="the dressing", role="keeper", meters={"sweetness": 1.0}, memes={"patience": 1.0}))
    world.facts.update(salad=salad, shallot=shallot, bowl=bowl, leaf=leaf, tomato=tomo, dressing=dress, params=params)
    return world


def predict(world: World) -> dict:
    sim = world.copy()
    sh = sim.get("shallot")
    sa = sim.get("salad")
    if sh.phrase.endswith("very thin"):
        sa.meters["balance"] = sa.meters.get("balance", 0.0) + 1.0
    else:
        sa.meters["balance"] = sa.meters.get("balance", 0.0) + 0.1
    return {"balanced": sa.meters["balance"] >= THRESHOLD}


def tell(world: World) -> None:
    p = _safe_fact(world, world.facts, "params")
    salad = _safe_fact(world, world.facts, "salad")
    shallot = _safe_fact(world, world.facts, "shallot")
    bowl = _safe_fact(world, world.facts, "bowl")
    leaf = _safe_fact(world, world.facts, "leaf")
    tomato = _safe_fact(world, world.facts, "tomato")
    dressing = _safe_fact(world, world.facts, "dressing")

    world.say(f"At {world.scene.place}, {bowl.label} waited for supper, and {salad.phrase} rested nearby.")
    world.say(f"A small shallot came close and asked to join the bowl, for it longed to become part of the meal.")
    world.para()
    world.say(f"The lettuce leaf frowned a little, and the tomato went quiet. They liked peace, but they feared the shallot's sharp bite.")
    world.say(f"Then the dressing held still, and the kitchen filled with suspense while everyone listened.")
    shallot.memes["hope"] = shallot.memes.get("hope", 0.0) + 1.0
    salad.memes["calm"] = salad.memes.get("calm", 0.0) - 0.3
    world.say(f"The salad and the shallot began to negotiate. The leaf asked for balance, and the tomato asked for gentleness.")
    world.para()
    if p.shallot_style == "whole":
        world.say(f"The shallot finally understood that a whole shallot would be too strong for this little fable.")
        world.say(f"It agreed to be sliced very thin, so its sharpness could soften like a secret told kindly.")
        shallot.phrase = "a small shallot sliced very thin"
        shallot.meters["sharpness"] = 0.2
        dressing.meters["sweetness"] = dressing.meters.get("sweetness", 0.0) + 0.4
    elif p.shallot_style == "thin":
        world.say(f"The shallot was already thin, so it could join at once without frightening the leaves.")
        world.say(f"The bowl welcomed it, and the dressing promised to carry the flavor gently through the salad.")
        shallot.meters["sharpness"] = 0.3
    else:
        world.say(f"The shallot wore golden rings and promised to be kind to the rest of the bowl.")
        world.say(f"With a little patience, even its bright flavor became a sweet note instead of a loud one.")
        shallot.meters["sharpness"] = 0.4
    world.say(f"At last, {bowl.label} held the salad in harmony, and the once-worried ingredients shared the meal in peace.")
    salad.meters["balance"] = 1.0
    salad.memes["calm"] = 1.0
    world.scene.bowl_clean = True
    world.facts["balanced"] = True
    world.facts["suspense"] = True
    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short fable for children about a shallot and a salad that must negotiate in suspense at {p.place}.',
        f'Tell a gentle story where a {p.shallot_style} shallot wants to join the salad, and the bowl finds a fair compromise.',
        "Write a tiny moral tale about patience, flavor, and sharing a salad bowl.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    shallot = _safe_fact(world, world.facts, "shallot")
    salad = _safe_fact(world, world.facts, "salad")
    return [
        QAItem(
            question="Who wanted to join the salad bowl?",
            answer=f"The small shallot wanted to join the salad bowl at {p.place}.",
        ),
        QAItem(
            question="Why was there suspense in the kitchen?",
            answer="There was suspense because the lettuce leaf and the tomato were unsure whether the shallot would be too sharp for the bowl.",
        ),
        QAItem(
            question="What changed so the salad could welcome the shallot?",
            answer=f"The shallot became {shallot.phrase} and its sharpness softened, so the salad could balance the flavor.",
        ),
        QAItem(
            question="What happened at the end of the fable?",
            answer="The ingredients negotiated a fair compromise, and the salad ended in harmony with the shallot included.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shallot?",
            answer="A shallot is a small onion-like vegetable with a mild or sharp flavor, often used to add taste to food.",
        ),
        QAItem(
            question="What is salad?",
            answer="Salad is a dish made from raw vegetables or fruits, often served cold with dressing.",
        ),
        QAItem(
            question="What does negotiate mean?",
            answer="To negotiate means to talk and make an agreement that works for everyone.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.phrase:
            parts.append(f"phrase={e.phrase!r}")
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:5}) {' '.join(parts)}")
    lines.append(f"  scene: place={world.scene.place!r} suspense={world.scene.suspense} bowl_clean={world.scene.bowl_clean}")
    return "\n".join(lines)


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


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_join/2.\n#show suspense/2.\n#show resolution/2."))
    return sorted(set(asp.atoms(model, "can_join")))


def asp_verify_gate() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_join/2.\n#show suspense/2.\n#show resolution/2."))
    asp_pairs = set(asp.atoms(model, "can_join"))
    py_pairs = set((sid, hid) for sid, s in SALADS.items() for hid, h in SHALLOTS.items() if balance_ok_py(s, h))
    if asp_pairs == py_pairs:
        print(f"OK: clingo gate matches balance_ok_py() ({len(py_pairs)} pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in ASP:", sorted(asp_pairs - py_pairs))
    print("  only in PY :", sorted(py_pairs - asp_pairs))
    return 1


def balance_ok_py(salad: Ingredient, shallot: Ingredient) -> bool:
    if shallot.taste in {"mild", "sweet"}:
        return True
    return salad.phrase.startswith("a garden")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for salad in SALADS:
            for sh in SHALLOTS:
                if balance_ok_py(_safe_lookup(SALADS, salad), _safe_lookup(SHALLOTS, sh)):
                    combos.append((place, salad, sh))
    return combos


CURATED = [
    StoryParams(place="kitchen", salad="green", shallot_style="thin"),
    StoryParams(place="garden", salad="farm", shallot_style="whole"),
    StoryParams(place="picnic", salad="feast", shallot_style="golden"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    salad = getattr(args, "salad", None) or rng.choice(list(SALADS))
    shallot_style = getattr(args, "shallot_style", None) or rng.choice(list(SHALLOTS))
    if not balance_ok_py(_safe_lookup(SALADS, salad), _safe_lookup(SHALLOTS, shallot_style)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, salad=salad, shallot_style=shallot_style)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show can_join/2.\n#show suspense/2.\n#show resolution/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_gate())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show can_join/2.\n#show suspense/2.\n#show resolution/2."))
        triples = sorted(set(asp.atoms(model, "can_join")))
        print(f"{len(triples)} compatible salad/shallot pairs:\n")
        for pair in triples:
            print(f"  {pair[0]} {pair[1]}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.place}: {p.salad} with {p.shallot_style} shallot"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
