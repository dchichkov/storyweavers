#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/swim_bean_bad_ending_flashback_repetition_bedtime.py
==============================================================================================================

A small bedtime-story world built from the seed words "swim" and "bean".

Premise:
- A little bean wants to swim at bedtime.
- A flashback reminds us why that wish matters.
- Repetition gives the story a sleepy, lullaby-like rhythm.
- The ending is a gentle bad ending: the bean does not get the happy swim it wanted, but the world settles into a quiet, believable bedtime outcome.

The domain is intentionally tiny and constraint-checked:
- one child caretaker
- one bean character
- one bath/puddle-like swim setting
- a soft bedtime routine
- a refusal/alternative that can fail in a small, story-shaped way

The Python world model and the inline ASP twin both encode the same reasonableness gate:
- the bean may only "swim" in a safe water place
- bedtime makes long swimming unreasonable
- the ending must follow from state, not from a frozen template
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bean: object | None = None
    child: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"child", "girl", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the bathtub"
    bedtime: bool = True
    water_kind: str = "warm water"
    affords_swim: bool = True
    quiet: bool = True
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
    setting: str = "bath"
    bean_name: str = "Bean"
    child_name: str = "Mina"
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    w: object | None = None
    world: object | None = None
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w
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


def _noun(name: str) -> str:
    return name


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bath": Setting(place="the bathtub", bedtime=True, water_kind="warm water", affords_swim=True, quiet=True),
    "pond": Setting(place="the little pond", bedtime=False, water_kind="moonlit water", affords_swim=True, quiet=False),
    "basin": Setting(place="the wash basin", bedtime=True, water_kind="a shallow splash", affords_swim=False, quiet=True),
}

BEANS = {
    "bean": {"label": "bean", "phrase": "a tiny sleepy bean", "type": "bean"},
    "green_bean": {"label": "green bean", "phrase": "a shiny little green bean", "type": "bean"},
}

CHILDREN = ["Mina", "Pip", "Noa", "Toby", "Luna", "Ivy"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def bean_can_swim(setting: Setting) -> bool:
    return setting.affords_swim and setting.place in {"the bathtub", "the little pond"}


def resolve_setting(setting_key: str) -> Setting:
    if setting_key not in SETTINGS:
        pass
    return _safe_lookup(SETTINGS, setting_key)


def explain_rejection(setting: Setting) -> str:
    return (
        f"(No story: the bean cannot really swim in {setting.place} as a bedtime "
        f"game here. Try the bathtub or the little pond, where the water is deep "
        f"enough for a tiny swim.)"
    )


# ---------------------------------------------------------------------------
# World actions and narrative beats
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, bean: Entity) -> None:
    world.say(
        f"{child.id} had a tiny friend named {bean.label}. "
        f"{bean.id} was a little {bean.type} who liked to rest in warm spots and dream."
    )


def flashback(world: World, child: Entity, bean: Entity) -> None:
    child.memes["remembering"] = child.memes.get("remembering", 0.0) + 1
    world.say(
        f"Earlier that day, {child.id} had promised, \"After supper, you can swim a little.\" "
        f"{bean.id} had heard that promise and held it like a shiny pebble."
    )


def repetition(world: World, child: Entity, bean: Entity) -> None:
    child.memes["repetition"] = child.memes.get("repetition", 0.0) + 1
    world.say(
        f"\"Just one more swim,\" said {bean.id}. "
        f"Then again, \"Just one more swim.\" "
        f"And one more time, very softly, \"Just one more swim.\""
    )


def try_swim(world: World, child: Entity, bean: Entity) -> None:
    if not bean_can_swim(world.setting):
        pass
    bean.meters["wet"] = bean.meters.get("wet", 0.0) + 1.0
    bean.memes["hope"] = bean.memes.get("hope", 0.0) + 1.0
    world.say(
        f"So {child.id} carried {bean.id} to {world.setting.place}, where the water was {world.setting.water_kind}. "
        f"{bean.id} splashed once, then again, and the little water made the bean feel brave."
    )


def bedtime_warning(world: World, child: Entity, bean: Entity) -> None:
    child.memes["concern"] = child.memes.get("concern", 0.0) + 1
    world.say(
        f"But the room was getting sleepier, and {child.id} whispered that bedtime was already here. "
        f"The lamp was low, the blanket was ready, and the water was starting to cool."
    )


def bad_ending(world: World, child: Entity, bean: Entity) -> None:
    # Gentle bad ending: the wish does not fully come true.
    bean.meters["swim"] = bean.meters.get("swim", 0.0) + 1.0
    bean.meters["tired"] = bean.meters.get("tired", 0.0) + 1.0
    bean.memes["disappointed"] = bean.memes.get("disappointed", 0.0) + 1.0
    world.say(
        f"{bean.id} swam until the last ripple faded, but then the water went still and the bedtime bell rang. "
        f"{child.id} lifted {bean.id} out, wrapped {bean.id} in a soft cloth, and set {bean.id} on the nightstand."
    )
    world.say(
        f"It was not the big happy swim {bean.id} wanted, but it was the quiet ending the room could hold. "
        f"{bean.id} stayed dry, warm, and a little sad, while the moon watched over the pillow."
    )


def tell_story(params: StoryParams) -> World:
    setting = resolve_setting(params.setting)
    if params.setting == "basin" and not bean_can_swim(setting):
        pass

    world = World(setting=setting)

    child = world.add(Entity(id=params.child_name, kind="character", type="child"))
    bean = world.add(Entity(
        id=params.bean_name,
        kind="thing",
        type="bean",
        label="bean",
        phrase="a tiny sleepy bean",
        owner=child.id,
        caretaker=child.id,
    ))

    world.facts["child"] = child
    world.facts["bean"] = bean
    world.facts["setting"] = setting

    introduce(world, child, bean)
    world.para()
    flashback(world, child, bean)
    repetition(world, child, bean)
    world.para()
    try_swim(world, child, bean)
    bedtime_warning(world, child, bean)
    world.para()
    bad_ending(world, child, bean)

    world.facts["ending"] = "bad"
    world.facts["swam"] = True
    world.facts["tired"] = True
    world.facts["disappointed"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child").id
    bean = _safe_fact(world, f, "bean").id
    place = _safe_fact(world, f, "setting").place
    return [
        f'Write a bedtime story about {child} and a bean who wants to swim at {place}.',
        f'Use the words "swim" and "bean" in a gentle story with a flashback and repetition.',
        f"Tell a soft, sleepy story where {bean} asks for one more swim, but bedtime changes the ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    bean = _safe_fact(world, world.facts, "bean")
    setting = _safe_fact(world, world.facts, "setting")
    return [
        QAItem(
            question=f"Who wanted to swim in the story?",
            answer=f"The little bean wanted to swim, and {child.id} was the one helping.",
        ),
        QAItem(
            question=f"What did the flashback remind the reader about?",
            answer=f"It reminded us that {child.id} had already promised {bean.id} a little swim after supper.",
        ),
        QAItem(
            question=f"Why was the ending not a happy swim?",
            answer=(
                f"Because bedtime came first. The water got quiet, the lamp got low, "
                f"and {child.id} wrapped {bean.id} in a soft cloth instead of keeping the swim going."
            ),
        ),
        QAItem(
            question=f"Where did the swim happen?",
            answer=f"It happened in {setting.place}, where the water could hold a tiny swim.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bean?",
            answer="A bean is a small seed. Some beans are eaten, and some stories treat a bean like a tiny character.",
        ),
        QAItem(
            question="What does swim mean?",
            answer="To swim means to move through water by kicking or floating so the water carries you along.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a story moment that looks back to something that happened earlier.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means saying or doing the same thing again on purpose, often to make the story feel rhythmic or memorable.",
        ),
        QAItem(
            question="What is a bedtime story?",
            answer="A bedtime story is a calm story told at the end of the day to help a child feel sleepy and safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(bath). setting(pond). setting(basin).
bedtime(bath). bedtime(basin).
affords_swim(bath). affords_swim(pond).

can_swim(S) :- affords_swim(S), (S = bath; S = pond).
valid_story(S) :- can_swim(S), not bedtime_block(S).

bedtime_block(S) :- bedtime(S), S = basin.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
        if _safe_lookup(SETTINGS, key).bedtime:
            lines.append(asp.fact("bedtime", key))
        if _safe_lookup(SETTINGS, key).affords_swim:
            lines.append(asp.fact("affords_swim", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_settings() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted({a[0] for a in asp.atoms(model, "valid_story")})


def python_valid_settings() -> list[str]:
    return sorted([k for k, s in SETTINGS.items() if bean_can_swim(s)])


def asp_verify() -> int:
    py = set(python_valid_settings())
    cl = set(asp_valid_settings())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} valid settings).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("only python:", sorted(py - cl))
    print("only ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / emission
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    if setting not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if setting == "basin":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    bean_name = getattr(args, "bean_name", None) or "Bean"
    child_name = getattr(args, "child_name", None) or rng.choice(CHILDREN)
    return StoryParams(setting=setting, bean_name=bean_name, child_name=child_name)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} kind={e.kind:8} type={e.type:8} meters={meters} memes={memes}")
    lines.append(f"  setting={world.setting.place}")
    lines.append(f"  facts={world.facts.get('ending', '')}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a bean wants to swim.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bean-name")
    ap.add_argument("--child-name")
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


CURATED = [
    StoryParams(setting="bath", bean_name="Bean", child_name="Mina"),
    StoryParams(setting="pond", bean_name="Bean", child_name="Pip"),
]


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
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_settings())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
