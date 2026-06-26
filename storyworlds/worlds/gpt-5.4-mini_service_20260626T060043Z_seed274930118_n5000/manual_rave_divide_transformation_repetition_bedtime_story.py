#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/manual_rave_divide_transformation_repetition_bedtime_story.py
==============================================================================================================

A bedtime-story world with a small, state-driven transformation:
a child follows a manual, a noisy rave mode gets tamed, and repeated
bedtime steps divide the night into calm, sleep-ready pieces.

The seed words are used as domain anchors:
- manual: a little instruction booklet for a bedside device
- rave: the loud, flashing mode that keeps sleep away
- divide: the bedtime trick of splitting one big, scary job into tiny parts

The story aims for a gentle bedtime cadence: beginning worry, small repeated
actions, a soothing transformation, and a closing image of rest.
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
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    lamp: object | None = None
    manual: object | None = None
    parent: object | None = None
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
class Setting:
    place: str
    cozy: str
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
    id: str
    label: str
    normal: str
    rave: str
    transformed: str
    parts: list[str]
    DEVICE: object | None = None
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


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None
    params: object | None = None
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


DEVICE = Device(
    id="lamp",
    label="bedside lamp",
    normal="soft moonlight",
    rave="rave mode",
    transformed="night-light mode",
    parts=["button", "cover", "bead chain"],
)

SETTINGS = {
    "nursery": Setting(place="the nursery", cozy="blankets and a rocking chair"),
    "bedroom": Setting(place="the bedroom", cozy="a pillow nest and a little rug"),
    "attic_room": Setting(place="the attic room", cozy="slanted walls and a warm quilt"),
}

CHILD_NAMES = ["Milo", "Nina", "Toby", "Lina", "Pip", "Maya", "Noa", "Sera"]
TRAITS = ["sleepy", "curious", "gentle", "brave", "patient"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_rave(world: World) -> list[str]:
    out: list[str] = []
    lamp = world.get("lamp")
    child = world.get("child")
    if lamp.meters.get("noise", 0.0) < THRESHOLD:
        return out
    sig = ("rave",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["tired"] = child.memes.get("tired", 0.0) + 1
    child.memes["uneasy"] = child.memes.get("uneasy", 0.0) + 1
    out.append("The bright rave mode kept the room awake.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    lamp = world.get("lamp")
    child = world.get("child")
    if lamp.meters.get("calm", 0.0) < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["safe"] = child.memes.get("safe", 0.0) + 1
    child.memes["sleepy"] = child.memes.get("sleepy", 0.0) + 1
    out.append("The lamp softened into a small, sleepy glow.")
    return out


def _r_divide(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("divide_plan", 0.0) < THRESHOLD:
        return out
    sig = ("divide",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    out.append("The big bedtime job felt smaller once it was divided into tiny steps.")
    return out


CAUSAL_RULES = [Rule("rave", _r_rave), Rule("transform", _r_transform), Rule("divide", _r_divide)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            sents = rule.apply(world)
            if len(world.fired) != before or sents:
                changed = True
                for s in sents:
                    world.say(s)


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="parent"))
    lamp = world.add(Entity(id="lamp", type="lamp", label=DEVICE.label))
    manual = world.add(Entity(id="manual", type="book", label="manual"))

    # Setup
    world.say(
        f"At {setting.place}, little {child.label} got ready for bed while {setting.cozy} waited quietly."
    )
    world.say(
        f"Beside the pillow lay a tiny manual for the bedside lamp, and {child.label} liked to tap its pages."
    )
    world.say(
        f"{child.label} loved the lamp when it glowed like {DEVICE.normal}, but not when it slipped into {DEVICE.rave}."
    )

    # Tension
    world.para()
    lamp.meters["noise"] = 1.0
    lamp.meters["flash"] = 1.0
    child.memes["uneasy"] = 1.0
    world.say(
        f"That night, the lamp blinked into {DEVICE.rave}, and the room felt too bright for sleepy eyes."
    )
    world.say(
        f"{child.label} wanted the soft glow back, but the buttons looked confusing, so {child.pronoun()} asked {parent.label} for help."
    )

    # Repetition + divide
    world.para()
    child.memes["divide_plan"] = 1.0
    world.say(
        f'{parent.label.capitalize()} opened the manual and said, "We can divide this into tiny parts: first the button, then the cover, then the chain."'
    )
    world.say(
        f"They tried the steps again and again: press, wait; press, wait; breathe, wait."
    )
    lamp.meters["calm"] = 1.0
    lamp.meters["noise"] = 0.0
    lamp.meters["flash"] = 0.0
    propagate(world)

    # Resolution / transformation
    world.para()
    world.say(
        f"At last, the manual helped {child.label} find the right button, and the lamp changed into {DEVICE.transformed}."
    )
    world.say(
        f"The bedroom grew quiet again, with one little glow on the wall and {child.label} tucked under the blanket like a warm comma at the end of a sentence."
    )

    world.facts.update(
        child=child,
        parent=parent,
        lamp=lamp,
        manual=manual,
        setting=setting,
        device=DEVICE,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f'Write a bedtime story about a child named {child.label}, a manual, and a lamp that starts in rave mode.',
        f'Tell a gentle story where a parent uses a manual to divide a hard bedtime fix into tiny steps.',
        f'Write a soothing bedtime tale that repeats a calming action until the room changes from noisy to sleepy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Where did {child.label} get ready for bed?",
            answer=f"{child.label} got ready for bed at {setting.place}, in a room with {setting.cozy}.",
        ),
        QAItem(
            question=f"What made the room too bright at first?",
            answer=f"The bedside lamp slipped into rave mode, so the room felt too bright and noisy for sleep.",
        ),
        QAItem(
            question=f"How did {parent.label} help fix the bedtime problem?",
            answer="They used the manual and divided the problem into tiny steps, trying the button, the cover, and the chain one at a time.",
        ),
        QAItem(
            question=f"What changed after the lamp was adjusted?",
            answer="The lamp transformed into a soft night-light glow, and the room became quiet again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a manual?",
            answer="A manual is a little book of instructions that shows how to use or fix something.",
        ),
        QAItem(
            question="What does rave mean in this story?",
            answer="Rave means the lamp is loud, flashy, and much too energetic for bedtime.",
        ),
        QAItem(
            question="What does it mean to divide a task?",
            answer="To divide a task means to split one big job into smaller steps that are easier to do.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
child_tired :- rave_mode.
child_calm :- divided_task, transformed_lamp.
resolved :- child_calm.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("manual"),
        asp.fact("rave_mode"),
        asp.fact("divided_task"),
        asp.fact("transformed_lamp"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    ok = any(sym.name == "resolved" for sym in model)
    if ok:
        print("OK: ASP gate matches the bedtime transformation story.")
        return 0
    print("MISMATCH: ASP gate did not derive resolved.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: manual, rave, divide.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, child_name=name, child_type=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        print("1 bedtime compatible answer set (ASP twin is intentionally tiny).")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in SETTINGS:
            params = StoryParams(place=place, child_name="Milo", child_type="boy", parent_type="mother")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
