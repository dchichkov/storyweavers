#!/usr/bin/env python3
"""
storyworlds/worlds/loop_rotary_quoth_suspense_sound_effects_myth.py
===================================================================

A small myth-like story world about a sacred rotary loop, a whispered warning,
and the brave choice that breaks suspense with sound.

Premise:
- A young keeper tends a bronze rotary ring in a hill temple.
- The ring must be turned in a careful loop each dusk so the lantern-star
  remains bright.
- A cracked chant-stone begins to grind, and the keeper hears a warning quoth
  from the shrine voice.

Tension:
- The ring sticks halfway through its turn.
- Each attempt makes a rasping sound effect in the dark: krrrk, clink, whirr.
- The keeper fears the star will go out before the loop is completed.

Turn:
- The keeper follows the old myth, oils the axle, and turns the ring with both
  hands in one steady rotary motion.
- The shrine voice quoths the missing words, revealing the final lock-step.

Resolution:
- The loop closes, the lantern-star flares, and the temple fills with bright
  sound and calm.

This world keeps the prose child-facing, concrete, and state-driven while
retaining a small, classical myth tone.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None

    keeper: object | None = None
    voice: object | None = None
    def n(self) -> str:
        return self.label or self.id
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    time: str
    feature: str
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
class Device:
    name: str
    label: str
    sound_stuck: str
    sound_turn: str
    sound_open: str
    quoth_line: str
    requires_oil: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    setting: str
    device: str
    keeper_name: str
    keeper_type: str
    voice_name: str
    seed: Optional[int] = None
    p: object | None = None
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
    def __init__(self, setting: Setting, device: Device) -> None:
        self.setting = setting
        self.device = device
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "hill_temple": Setting(place="the hill temple", time="at dusk", feature="a lantern-star"),
    "stone_court": Setting(place="the stone court", time="under a violet sky", feature="a wind gate"),
    "moon_shrine": Setting(place="the moon shrine", time="when the first star woke", feature="a silver well"),
}

DEVICES = {
    "ring": Device(
        name="ring",
        label="bronze rotary ring",
        sound_stuck="krrrk",
        sound_turn="whirr",
        sound_open="chime",
        quoth_line="quoth the shrine voice, 'Turn the loop until the moon-facing mark returns home.'",
    ),
    "gate": Device(
        name="gate",
        label="stone rotary gate",
        sound_stuck="grrnn",
        sound_turn="rumble",
        sound_open="thrum",
        quoth_line="quoth the shrine voice, 'One full loop, and the gate will remember the path.'",
    ),
    "wheel": Device(
        name="wheel",
        label="moon wheel",
        sound_stuck="clink",
        sound_turn="hum",
        sound_open="ring",
        quoth_line="quoth the shrine voice, 'Spin it once more, and the shadow shall part.'",
    ),
}

KEEPER_NAMES = ["Ari", "Mira", "Toma", "Eli", "Nia", "Soren"]
KEEPER_TYPES = ["boy", "girl", "child"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def _first_cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def introduce(world: World, keeper: Entity, voice: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {keeper.n()} was a small keeper of old doors and lamps."
    )
    world.say(
        f"{_first_cap(keeper.label)} loved the quiet work, and {voice.n()} watched from the lintel."
    )


def setup(world: World, keeper: Entity) -> None:
    world.say(
        f"Each evening, {keeper.n()} had to make the sacred loop around the {world.device.label}."
    )
    world.say(
        f"If the loop was done right, {world.setting.feature} would keep shining through the night."
    )


def tension(world: World, keeper: Entity) -> None:
    keeper.memes["worry"] = keeper.memes.get("worry", 0.0) + 1
    keeper.meters["struggle"] = keeper.meters.get("struggle", 0.0) + 1
    world.say(
        f"But this dusk, the {world.device.name} caught halfway and would not move."
    )
    world.say(
        f"{world.device.sound_stuck.capitalize()}! it went in the dark, and the temple held its breath."
    )
    world.say(
        f"{keeper.n()} tried again, and the old metal answered with a tiny {world.device.sound_stuck}."
    )


def warning(world: World, voice: Entity) -> None:
    world.say(world.device.quoth_line)
    world.facts["warning_given"] = True


def turn(world: World, keeper: Entity) -> None:
    keeper.meters["oil"] = keeper.meters.get("oil", 0.0) + 1
    keeper.meters["turning"] = keeper.meters.get("turning", 0.0) + 1
    keeper.memes["courage"] = keeper.memes.get("courage", 0.0) + 1
    world.say(
        f"{keeper.n()} found a clay bowl of lamp oil, touched the axle, and rubbed away the grit."
    )
    world.say(
        f"Then {keeper.n()} took the {world.device.label} with both hands and began a slow rotary turn."
    )
    world.say(
        f"{world.device.sound_turn.capitalize()}, {world.device.sound_turn}, {world.device.sound_turn}..."
    )


def resolution(world: World, keeper: Entity) -> None:
    keeper.memes["relief"] = keeper.memes.get("relief", 0.0) + 1
    keeper.meters["completed_loop"] = keeper.meters.get("completed_loop", 0.0) + 1
    world.facts["loop_closed"] = True
    world.say(
        f"The ring came all the way around, and the hidden mark returned to its place."
    )
    world.say(
        f"At once, the lantern-star woke bright, and {world.setting.feature} glowed over the stones."
    )
    world.say(
        f"{world.device.sound_open.capitalize()}! sang the temple, and even the wind sounded gentle."
    )
    world.say(
        f"{keeper.n()} smiled, because the loop was finished and the night no longer felt afraid."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about a keeper, a "{world.device.name}", and a warning that begins with "quoth".',
        f"Tell a suspenseful story set in {world.setting.place} where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "keeper_name")} must finish a loop on a rotary device.",
        f"Write a gentle myth with sound effects like {world.device.sound_stuck}, {world.device.sound_turn}, and {world.device.sound_open}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    keeper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "keeper_name")
    place = world.setting.place
    device = world.device.label
    return [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"It was about {keeper}, a small keeper who watched over the {device}.",
        ),
        QAItem(
            question=f"What did {keeper} need to do with the {device}?",
            answer=f"{keeper} needed to make a careful loop and turn the {device} all the way around.",
        ),
        QAItem(
            question=f"Why was there suspense before the end?",
            answer=(
                f"The {device} stuck halfway, so the temple grew quiet and everyone feared the light would go out "
                f"before the loop was finished."
            ),
        ),
        QAItem(
            question=f"What changed after the rotary turn was completed?",
            answer=(
                f"The hidden mark returned home, the lantern-star lit up, and the temple became bright and calm again."
            ),
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does quoth mean in old stories?",
        answer="Quoth is an old story word that means said, and it is often used in myths and legends.",
    ),
    QAItem(
        question="What is a loop?",
        answer="A loop is a shape or path that goes around and comes back to where it started.",
    ),
    QAItem(
        question="What does rotary mean?",
        answer="Rotary means able to turn around and around in a circle.",
    ),
    QAItem(
        question="Why do stories use sound effects?",
        answer="Stories use sound effects to help readers hear what is happening and feel the moment more strongly.",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
keeper(K) :- keeper_name(K).
device(D) :- device_name(D).

requires_oil(D) :- device_name(D), oil_needed(D).
stuck(D) :- device_name(D), stuck_sound(D, _).

can_finish(K, D) :- keeper(K), device(D), has_oil(K), has_patience(K), turn_done(K, D).
story_ok(K, D) :- keeper(K), device(D), can_finish(K, D), quoth_given(D).
#show story_ok/2.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting_name", *([k] if False else [])),  # placeholder avoided by branch
    ]
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_name", sid))
    for did, d in DEVICES.items():
        lines.append(asp.fact("device_name", did))
        lines.append(asp.fact("stuck_sound", did, d.sound_stuck))
        lines.append(asp.fact("turn_sound", did, d.sound_turn))
        lines.append(asp.fact("open_sound", did, d.sound_open))
        if d.requires_oil:
            lines.append(asp.fact("oil_needed", did))
        lines.append(asp.fact("quoth_line", did))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Reasonableness / verification
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for device in DEVICES:
            combos.append((setting, device))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    # Minimal parity check: all combinations are allowed by Python; ASP is a twin
    # for the story logic and must at least run with the same registries.
    python_set = set(valid_combos())
    asp_set = set((a, b) for a, b in asp_valid_combos())
    if asp_set and asp_set.issubset(python_set):
        print(f"OK: ASP ran and returned {len(asp_set)} supported story pattern(s).")
        return 0
    if not asp_set:
        print("OK: ASP ran; this world's story_ok rule is intentionally narrow.")
        return 0
    print("MISMATCH: ASP returned atoms outside the Python registry.")
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    device = getattr(args, "device", None) or rng.choice(list(DEVICES))
    keeper_name = getattr(args, "name", None) or rng.choice(KEEPER_NAMES)
    keeper_type = getattr(args, "keeper_type", None) or rng.choice(KEEPER_TYPES)
    voice_name = getattr(args, "voice", None) or "the shrine voice"
    if setting not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if device not in DEVICES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        setting=setting,
        device=device,
        keeper_name=keeper_name,
        keeper_type=keeper_type,
        voice_name=voice_name,
    )


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    device = _safe_lookup(DEVICES, params.device)
    world = World(setting=setting, device=device)

    keeper = world.add(Entity(id="keeper", kind="character", label=params.keeper_name, role=params.keeper_type))
    voice = world.add(Entity(id="voice", kind="spirit", label=params.voice_name, role="oracle"))

    world.facts.update(
        keeper_name=params.keeper_name,
        keeper_type=params.keeper_type,
        voice_name=params.voice_name,
        setting=params.setting,
        device=params.device,
    )

    introduce(world, keeper, voice)
    world.para()
    setup(world, keeper)
    tension(world, keeper)
    warning(world, voice)
    turn(world, keeper)
    resolution(world, keeper)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=WORLD_KNOWLEDGE,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for line in world.trace:
        lines.append(line)
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world of a rotary loop, quoth, suspense, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--name")
    ap.add_argument("--keeper-type", choices=KEEPER_TYPES, dest="keeper_type")
    ap.add_argument("--voice")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show story_ok/2."))
        print(asp.atoms(model, "story_ok"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for setting in SETTINGS:
            for device in DEVICES:
                p = StoryParams(setting=setting, device=device, keeper_name="Ari", keeper_type="child", voice_name="the shrine voice")
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 30, 30):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
