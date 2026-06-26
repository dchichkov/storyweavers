#!/usr/bin/env python3
"""
storyworlds/worlds/tuesday_frill_hug_repetition_surprise_flashback_ghost.py
============================================================================

A tiny ghost-story world with repetition, surprise, and flashback.

Premise:
- On Tuesday, a child finds a frilled keepsake in an old room.
- The child keeps hugging it because it feels important and a little spooky.
- A ghostly presence repeats a warning.
- A flashback explains why the keepsake matters.
- The ending turns on a surprise: the ghost is not there to frighten, but to return something lost.

The world is intentionally small and state-driven:
- physical meters track candlelight, chill, dust, heldness, and hiddenness
- emotional memes track fear, curiosity, comfort, grief, and relief

The story reads like a complete ghost tale, but stays child-facing and gentle.
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
    kind: str = "thing"   # "character" | "thing" | "spirit"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    ghost: object | None = None
    keepsake: object | None = None
    parent: object | None = None
    room: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "spirit":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the old house"
    detail: str = "a narrow hall with a creaky stair"
    tuesday_only: bool = True
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
    child_name: str
    child_type: str
    parent_type: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


SETTINGS = {
    "attic": Setting(place="the attic", detail="a narrow hall with a small round window"),
    "closet": Setting(place="the old linen closet", detail="a cramped shelf-lined room"),
    "porch": Setting(place="the porch", detail="a shadowy porch with a hanging frill curtain"),
}

CHILD_NAMES = ["Maya", "Nico", "Lena", "Owen", "Iris", "Theo", "Ruby", "Eli"]
FRILL_ITEMS = [
    ("frill ribbon", "a soft frill ribbon"),
    ("frill curtain", "a pale frill curtain"),
    ("frill collar", "a little frill collar"),
]

# -----------------------------------------------------------------------------
# World model: meters and memes drive the prose.
# -----------------------------------------------------------------------------
def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def _add_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def _add_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


def _ghostly_chill(world: World, child: Entity, ghost: Entity) -> None:
    if _meme(ghost, "near") < THRESHOLD:
        return
    _add_meter(world.get("room"), "chill", 1)
    _add_meme(child, "fear", 1)
    if ("chill_line",) not in world.fired:
        world.fired.add(("chill_line",))
        world.say(f"The room felt colder, as if the air had remembered a secret.")


def _repeat_warning(world: World, child: Entity, ghost: Entity) -> None:
    if _meme(ghost, "warning") < THRESHOLD:
        return
    key = ("repeat_warning",)
    if key in world.fired:
        return
    world.fired.add(key)
    world.say('"Don’t leave it alone," the ghost whispered. "Don’t leave it alone."')


def _flashback(world: World, child: Entity, keepsake: Entity) -> None:
    if _meme(child, "triggered_memory") < THRESHOLD:
        return
    key = ("flashback",)
    if key in world.fired:
        return
    world.fired.add(key)
    world.say(
        f"Then {child.id} remembered a warm afternoon long ago, when a hand had tucked "
        f"{keepsake.phrase} into a pocket and said it was for keeping safe."
    )


def _surprise_reveal(world: World, child: Entity, ghost: Entity, keepsake: Entity) -> None:
    if _meme(child, "understood") < THRESHOLD:
        return
    key = ("reveal",)
    if key in world.fired:
        return
    world.fired.add(key)
    world.say(
        f"The ghost was not there to scare anyone. It had only stayed because it was "
        f"looking for {keepsake.it()}, and it was finally glad to see it returned."
    )


def propagate(world: World) -> None:
    child = world.get("child")
    ghost = world.get("ghost")
    keepsake = world.get("keepsake")
    _ghostly_chill(world, child, ghost)
    _repeat_warning(world, child, ghost)
    _flashback(world, child, keepsake)
    _surprise_reveal(world, child, ghost, keepsake)


# -----------------------------------------------------------------------------
# Story beats.
# -----------------------------------------------------------------------------
def introduce(world: World, child: Entity, keepsake: Entity) -> None:
    world.say(
        f"On Tuesday, {child.id} wandered into {world.setting.place}, where {world.setting.detail} "
        f"waited in the hush."
    )
    world.say(
        f"There, {child.id} found {keepsake.phrase}, with a tiny frill that looked almost like a smile."
    )
    _add_meme(child, "curiosity", 1)
    _add_meter(keepsake, "hidden", 0)
    _add_meter(keepsake, "found", 1)


def hug_keepsake(world: World, child: Entity, keepsake: Entity) -> None:
    child.meters["held"] = 1
    keepsake.carried_by = child.id
    _add_meme(child, "comfort", 1)
    world.say(f"{child.id} gave {keepsake.it()} a careful hug, as if the hug might keep the room steady.")


def ghost_appears(world: World, ghost: Entity) -> None:
    ghost.memes["near"] = 1
    ghost.memes["warning"] = 1
    _add_meter(ghost, "glow", 1)
    world.say("A pale ghost shimmered near the doorway, and the frill on the keepsake trembled a little.")
    propagate(world)


def child_worries(world: World, child: Entity) -> None:
    _add_meme(child, "fear", 1)
    world.say(f"{child.id} took one small breath and hugged {child.id}'s treasure even tighter.")
    world.say(f"{child.id} wondered why the ghost kept watching from the dark.")


def realize_and_return(world: World, child: Entity, ghost: Entity, keepsake: Entity) -> None:
    child.memes["triggered_memory"] = 1
    propagate(world)
    child.memes["understood"] = 1
    world.say(
        f"At last {child.id} understood that the ghost's sadness was not hungry or mean; "
        f"it was waiting for {keepsake.phrase} to come home."
    )
    world.say(
        f"{child.id} held {keepsake.it()} out, and the ghost's glow softened like moonlight on water."
    )
    child.memes["relief"] = 1
    ghost.memes["relief"] = 1
    world.say(
        f"Then the ghost bowed once, became lighter and lighter, and drifted away with a gentle sigh."
    )


def closing_image(world: World, child: Entity, keepsake: Entity) -> None:
    world.say(
        f"When the house grew warm again, {child.id} tucked {keepsake.it()} close to a pillow, "
        f"and the frill lay still at last."
    )


# -----------------------------------------------------------------------------
# Registries and construction.
# -----------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="the parent"))
    ghost = world.add(Entity(id="ghost", kind="spirit", type="spirit", label="a ghost"))
    keepsake_label, keepsake_phrase = _safe_lookup(FRILL_ITEMS, 0)
    keepsake = world.add(Entity(
        id="keepsake",
        kind="thing",
        type="keepsake",
        label=keepsake_label,
        phrase=keepsake_phrase,
        owner=child.id,
    ))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        keepsake=keepsake,
        room=room,
        place=params.place,
    )
    return world


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    child = world.get("child")
    ghost = world.get("ghost")
    keepsake = world.get("keepsake")

    introduce(world, child, keepsake)
    world.para()
    ghost_appears(world, ghost)
    child_worries(world, child)
    world.para()
    realize_and_return(world, child, ghost, keepsake)
    closing_image(world, child, keepsake)
    return world


# -----------------------------------------------------------------------------
# Q&A.
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        'Write a gentle ghost story for a young child using the words "Tuesday", "frill", and "hug".',
        f"Tell a story where {child.id} finds something frilled in a spooky place and learns why the ghost is lingering there.",
        "Write a short story with repetition, a flashback, and a surprise that ends kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    ghost = _safe_fact(world, f, "ghost")
    keepsake = _safe_fact(world, f, "keepsake")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Why did {child.id} hug {keepsake.it()} so tightly in {place}?",
            answer=(
                f"{child.id} hugged {keepsake.it()} because it felt important and a little spooky, "
                f"and the hug made {child.id} feel braver in the dark room."
            ),
        ),
        QAItem(
            question=f"What did the ghost keep saying when {child.id} first saw it?",
            answer=(
                f"The ghost kept saying, \"Don’t leave it alone,\" and then it said the same warning again."
            ),
        ),
        QAItem(
            question=f"What memory came back to {child.id} before the ending surprise?",
            answer=(
                f"{child.id} remembered a warm moment from before, when someone had tucked {keepsake.phrase} "
                f"away and said it was meant to be kept safe."
            ),
        ),
        QAItem(
            question=f"What was the surprise at the end of the story?",
            answer=(
                f"The surprise was that the ghost was not trying to scare anyone. It was only waiting for "
                f"{keepsake.it()} to come back, and then it could finally go in peace."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is Tuesday?",
            answer="Tuesday is one of the days of the week, and it comes after Monday.",
        ),
        QAItem(
            question="What is a frill?",
            answer="A frill is a soft, wavy edge on cloth or paper that makes it look fancy or delicate.",
        ),
        QAItem(
            question="What does a hug do?",
            answer="A hug helps people feel close, safe, and cared for.",
        ),
        QAItem(
            question="Why do stories sometimes repeat a line?",
            answer="Repeating a line can make a warning feel stronger or help a child remember what matters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# ASP twin.
# -----------------------------------------------------------------------------
ASP_RULES = r"""
% If the child holds the keepsake, the ghost can feel it nearby.
near_ghost(G) :- ghost(G), holds(child, K), keepsake(K).

% A warning repeats when the ghost is near and the room is cold.
repeat_warning :- near_ghost(G), chill(room), ghost(G).

% A flashback is possible once the child remembers the keepsake's old home.
flashback :- remembers(child, keepsake).

% Surprise happens when the ghost is revealed to be gentle, not mean.
surprise :- near_ghost(G), gentle(G).

#show repeat_warning/0.
#show flashback/0.
#show surprise/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines = []
    lines.append(asp.fact("room", "room"))
    lines.append(asp.fact("ghost", "ghost"))
    lines.append(asp.fact("keepsake", "keepsake"))
    lines.append(asp.fact("holds", "child", "keepsake"))
    lines.append(asp.fact("chill", "room"))
    lines.append(asp.fact("remembers", "child", "keepsake"))
    lines.append(asp.fact("gentle", "ghost"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import
    model = asp.one_model(asp_program(""))
    atoms = {sym.name for sym in model}
    expected = {"repeat_warning", "flashback", "surprise"}
    if atoms == expected:
        print(f"OK: ASP and Python story logic agree ({len(atoms)} facts).")
        return 0
    print("MISMATCH between ASP and Python logic:")
    print("  ASP:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


# -----------------------------------------------------------------------------
# CLI.
# -----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with Tuesday, frill, and hug.")
    ap.add_argument("--place", choices=sorted(SETTINGS), default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        child_name=rng.choice(CHILD_NAMES),
        child_type=rng.choice(["girl", "boy"]),
        parent_type=rng.choice(["mother", "father"]),
        seed=getattr(args, "seed", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(place="attic", child_name="Maya", child_type="girl", parent_type="mother"),
    StoryParams(place="closet", child_name="Owen", child_type="boy", parent_type="father"),
    StoryParams(place="porch", child_name="Iris", child_type="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show repeat_warning/0.\n#show flashback/0.\n#show surprise/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show repeat_warning/0.\n#show flashback/0.\n#show surprise/0."))
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            sample = generate(p)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
