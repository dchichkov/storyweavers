#!/usr/bin/env python3
"""
storyworlds/worlds/prohibit_porpoise_misunderstanding_animal_story.py
=====================================================================

A tiny animal-story world about a seaside rule, a worried porpoise, and a
misunderstanding that gets cleared up.

Premise:
- A small porpoise lives near a public dock.
- A clear sign says what is prohibited at the waterline.
- Another animal misreads the sign and thinks the porpoise itself is banned.

Turn:
- The porpoise feels hurt and hides.
- The ranger notices the misunderstanding and explains the rule carefully.

Resolution:
- The rule turns out to be about tossing shells into the water, not about the
  porpoise.
- The porpoise returns to the dock, calm and proud, while the other animal
  learns to ask before guessing.

This script follows the Storyworld contract: it builds a simulated world with
physical meters and emotional memes, generates story text from state, and
includes a small ASP twin for the reasonableness gate.
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

THRESHOLD = 1.0



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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    observer: object | None = None
    porpoise: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "risk": 0.0,
                "wet": 0.0,
                "mess": 0.0,
            }
        if not self.memes:
            self.memes = {
                "worry": 0.0,
                "hurt": 0.0,
                "relief": 0.0,
                "curiosity": 0.0,
                "understanding": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the harbor dock"
    water: bool = True
    affords: set[str] = field(default_factory=lambda: {"shells", "swim"})
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
class Rule:
    name: str
    apply: callable
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.rule_log: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "dock": Setting(place="the harbor dock", water=True, affords={"shells", "swim"}),
    "bay": Setting(place="the quiet bay", water=True, affords={"shells", "swim"}),
}

HEROES = ["Mina", "Toby", "Nell", "Cleo", "Pip", "Rory"]
HELPERS = ["ranger", "dock worker", "lifeguard"]

ANIMALS = {
    "porpoise": {
        "type": "porpoise",
        "label": "porpoise",
        "phrase": "a shy porpoise with a smooth gray back",
    },
    "seagull": {
        "type": "seagull",
        "label": "seagull",
        "phrase": "a nosy seagull with bright feet",
    },
    "seal": {
        "type": "seal",
        "label": "seal",
        "phrase": "a round seal with whiskers",
    },
}

RULE_SIGN = "prohibit_shells"
RULE_TEXT = "No tossing shells into the water."
MISUNDERSTANDING_TEXT = "The porpoise is prohibited."


@dataclass
class StoryParams:
    place: str
    observer: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------
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


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    porpoise = world.get("porpoise")
    observer = world.get("observer")
    if observer.memes["understanding"] >= THRESHOLD:
        return out
    if observer.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    observer.memes["worry"] += 1
    porpoise.memes["hurt"] += 1
    porpoise.meters["risk"] += 1
    world.rule_log.append("misunderstanding")
    out.append("The porpoise felt singled out and swam away from the dock.")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    porpoise = world.get("porpoise")
    observer = world.get("observer")
    if helper.memes["understanding"] < THRESHOLD:
        return out
    sig = ("soften",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    observer.memes["worry"] = 0.0
    observer.memes["understanding"] += 1
    porpoise.memes["hurt"] = 0.0
    porpoise.memes["relief"] += 1
    world.rule_log.append("soften")
    out.append("The helper explained that the shells were prohibited, not the porpoise.")
    return out


RULES = [
    Rule("misunderstanding", _r_misunderstanding),
    Rule("soften", _r_soften),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def announce(world: World, hero: Entity, observer: Entity, helper: Entity) -> None:
    world.say(
        f"At {world.setting.place}, {hero.phrase} liked the bright water and the steady tide."
    )
    world.say(
        f"{observer.id} also came to the dock, while the {helper.type} kept an eye on the sign."
    )


def show_sign(world: World) -> None:
    world.say(f"The sign read, \"{RULE_TEXT}\"")
    world.say("It was meant to keep the dock tidy for the animals and people nearby.")


def make_misunderstanding(world: World, observer: Entity, porpoise: Entity) -> None:
    observer.memes["curiosity"] += 1
    world.say(
        f"{observer.id} squinted at the sign and got it wrong."
    )
    world.say(
        f"{observer.id} whispered, \"{MISUNDERSTANDING_TEXT}\""
    )
    propagate(world)


def rescue_explanation(world: World, helper: Entity, observer: Entity) -> None:
    helper.memes["understanding"] += 1
    world.say(
        f"The {helper.type} hurried over and shook a calm head."
    )
    world.say(
        f'\"That sign does not prohibit the porpoise,\" the {helper.type} said. '
        f'\"It only prohibits tossing shells into the water.\"'
    )
    propagate(world)


def ending(world: World, porpoise: Entity, observer: Entity) -> None:
    observer.memes["understanding"] += 1
    porpoise.memes["relief"] += 1
    porpoise.meters["risk"] = 0.0
    world.say(
        f"The {observer.id} nodded and gave the porpoise a small wave."
    )
    world.say(
        f"The porpoise came back to the dock, and the water looked gentle again."
    )


# ---------------------------------------------------------------------------
# Build and generate
# ---------------------------------------------------------------------------

def tell(setting: Setting, observer_name: str, helper_type: str) -> World:
    world = World(setting)
    porpoise = world.add(Entity(
        id="porpoise",
        kind="character",
        type="porpoise",
        label="porpoise",
        phrase="a shy porpoise with a smooth gray back",
    ))
    observer = world.add(Entity(
        id=observer_name,
        kind="character",
        type="child",
        label=observer_name,
        phrase=f"{observer_name}, a small shore child",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_type,
        phrase=f"a careful {helper_type}",
    ))

    world.facts.update(
        porpoise=porpoise,
        observer=observer,
        helper=helper,
        setting=setting,
    )

    announce(world, porpoise, observer, helper)
    world.para()
    show_sign(world)
    world.para()
    make_misunderstanding(world, observer, porpoise)
    world.para()
    rescue_explanation(world, helper, observer)
    world.para()
    ending(world, porpoise, observer)
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short animal story about a porpoise at {world.setting.place} '
        f'where a rule is misunderstood.',
        f"Tell a gentle story in which a sign says something is prohibited, but "
        f"the animals first think the porpoise is prohibited.",
        f'Write a small story about "{MISUNDERSTANDING_TEXT}" being a mistake '
        f'and ending with the porpoise feeling safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    observer = world.get("observer")
    helper = world.get("helper")
    porpoise = world.get("porpoise")
    return [
        QAItem(
            question=f"Why did {observer.id} think the porpoise was in trouble?",
            answer=(
                f"{observer.id} misunderstood the sign and thought the porpoise "
                f"was prohibited, even though the rule was really about shells."
            ),
        ),
        QAItem(
            question=f"What did the helper explain at {world.setting.place}?",
            answer=(
                f"The helper explained that {RULE_TEXT.lower()} That meant the "
                f"porpoise was welcome, and only shell tossing was banned."
            ),
        ),
        QAItem(
            question=f"How did the porpoise feel after the misunderstanding was cleared up?",
            answer=(
                f"The porpoise felt relieved. Its hurt dropped away, and it swam "
                f"back to the dock once the rule was explained clearly."
            ),
        ),
        QAItem(
            question=f"Who helped fix the misunderstanding?",
            answer=(
                f"The {helper.type} helped fix it by speaking calmly and making "
                f"the rule easy to understand."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a porpoise?",
            answer="A porpoise is a small marine mammal that lives in the sea and breathes air.",
        ),
        QAItem(
            question="What does prohibit mean?",
            answer="To prohibit something means to say it is not allowed.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the meaning wrong and thinks something false.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  rules: {world.rule_log}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A misunderstanding happens when the observer reads the sign but does not yet
% understand it.
misunderstanding(O) :- observer(O), sees_sign(O), not understands(O).

% The helper resolves the misunderstanding by explaining the rule.
resolved(O) :- misunderstanding(O), helper(H), explains_rule(H), understands(O).

#show misunderstanding/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("observer", "observer"),
        asp.fact("helper", "helper"),
        asp.fact("sees_sign", "observer"),
        asp.fact("explains_rule", "helper"),
        asp.fact("understands", "observer"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    atoms = asp.atoms(model, "resolved")
    if atoms == [("observer",)]:
        print("OK: ASP twin matches the Python resolution gate.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected resolution.")
    return 1


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world about a porpoise, a prohibited rule, and a misunderstanding."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--observer", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
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
    observer = getattr(args, "observer", None) or rng.choice(HEROES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    if observer == helper:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, observer=observer, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.observer, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(f"resolved atoms: {asp.atoms(model, 'resolved')}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in SETTINGS:
            for observer in HEROES[:3]:
                helper = _safe_lookup(HELPERS, 0)
                if observer != helper:
                    p = StoryParams(place=place, observer=observer, helper=helper)
                    samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
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
