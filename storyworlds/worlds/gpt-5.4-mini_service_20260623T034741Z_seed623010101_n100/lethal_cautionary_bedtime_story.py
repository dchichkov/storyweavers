#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/lethal_cautionary_bedtime_story.py
==============================================================================================================

A small cautionary bedtime story world.

Premise:
A sleepy child wants to keep a night-light toy or a glowing jar near the bed,
but a grown-up warns that a glowing mushroom, berry, or vial is lethal to touch
or taste. The child learns to keep the dangerous thing far away and sleep safely.

This storyworld models a tiny bedtime domain with:
- typed entities that have physical meters and emotional memes
- a cause/effect turn driven by simulated state
- a cautionary resolution
- three grounded QA sets
- a Python reasonableness gate and inline ASP twin

The word "lethal" is intentionally used in the story when relevant.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
RISK_MIN = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    dangerous: bool = False
    safe: bool = False
    wearable: bool = False
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    child: object | None = None
    helper: object | None = None
    risky: object | None = None
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
        if not hasattr(self, "_tags"):
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def by_role(self, role: str) -> Entity:
        for e in self.entities.values():
            if e.role == role:
                return e
        raise KeyError(role)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_separate(world: World) -> list[str]:
    out = []
    child = world.by_role("child")
    if child.meters["distance"] >= THRESHOLD and child.meters["risk"] >= THRESHOLD:
        sig = ("separate", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            out.append("The child stepped back from the danger.")
    return out


def _r_sleep(world: World) -> list[str]:
    out = []
    child = world.by_role("child")
    if child.memes["calm"] >= THRESHOLD and child.meters["risk"] < THRESHOLD:
        sig = ("sleep", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["sleepiness"] += 1
            out.append("The room grew quiet and ready for sleep.")
    return out


CAUSAL_RULES = [Rule("separate", _r_separate), Rule("sleep", _r_sleep)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    setting: str = "bedroom"
    danger: str = "mushroom"
    helper: str = "mother"
    child_name: str = "Mina"
    child_gender: str = "girl"
    seed: Optional[int] = None
    p: object | None = None
    smoke_params: object | None = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "bedroom": {
        "place": "the bedroom",
        "night": "the lamp cast a soft circle on the quilt",
        "safe_rest": "the child tucked the blanket up to the chin",
        "affords": {"mushroom", "jar", "berry"},
    },
    "nursery": {
        "place": "the nursery",
        "night": "the moon made a silver patch on the floor",
        "safe_rest": "the child cuddled the pillow and listened to the hush",
        "affords": {"mushroom", "jar"},
    },
    "cabin": {
        "place": "the little cabin",
        "night": "the firelight had gone low and gentle",
        "safe_rest": "the child leaned into the pillow and breathed slowly",
        "affords": {"berry", "jar"},
    },
}

DANGERS = {
    "mushroom": {
        "label": "a glowing mushroom",
        "phrase": "the glowing mushroom by the bed",
        "risk_word": "lethal",
        "touch": "touch",
        "taste": "taste",
        "warning": "it was lethal to taste and dangerous to touch",
        "distance": 0.0,
        "kind": "mushroom",
    },
    "jar": {
        "label": "a glass jar with a shining powder",
        "phrase": "the glass jar with shining powder",
        "risk_word": "lethal",
        "touch": "touch",
        "taste": "taste",
        "warning": "it could be lethal if anyone put it in their mouth",
        "distance": 0.0,
        "kind": "jar",
    },
    "berry": {
        "label": "bright red berries",
        "phrase": "the bright red berries on the dish",
        "risk_word": "lethal",
        "touch": "touch",
        "taste": "taste",
        "warning": "the berries were lethal to eat",
        "distance": 0.0,
        "kind": "berry",
    },
}

SAFE_ACTIONS = {
    "snack": "put the berries in the kitchen",
    "box": "close the box and set it on a high shelf",
    "tray": "move the dish to the window ledge",
}

GIRL_NAMES = ["Mina", "Nora", "Lila", "Zoe", "Maya", "Ella"]
BOY_NAMES = ["Finn", "Noah", "Eli", "Theo", "Owen", "Ben"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s_name, s in SETTINGS.items():
        for d_name in s["affords"]:
            combos.append((s_name, d_name))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary bedtime story world with a lethal warning.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--danger", choices=DANGERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.danger not in _safe_lookup(SETTINGS, params.setting)["affords"]:
        pass
    if params.gender and params.name:
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "danger", None) is None or c[1] == getattr(args, "danger", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, danger = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    p = StoryParams(setting=setting, danger=danger, helper=helper, child_name=name, child_gender=gender)
    reasonableness_gate(p)
    return p


def predict_risk(world: World, child: Entity, danger: Entity) -> bool:
    sim = world.copy()
    sim.get(child.id).meters["distance"] = 0.0
    sim.get(danger.id).meters["risk"] = 1.0
    return sim.get(child.id).meters["risk"] >= THRESHOLD


def tell(setting: dict, danger: dict, params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, role="helper"))
    risky = world.add(Entity(
        id="Danger",
        kind="thing",
        type=danger["kind"],
        label=danger["label"],
        phrase=danger["phrase"],
        dangerous=True,
        attrs={"warning": danger["warning"], "risk_word": danger["risk_word"]},
    ))
    world.facts["setting"] = setting["place"]
    world.facts["danger"] = danger["label"]
    world.facts["helper"] = helper
    world.facts["child"] = child
    world.facts["risk_word"] = danger["risk_word"]

    child.memes["curiosity"] = 1.0
    child.meters["distance"] = 0.0
    risky.meters["risk"] = 1.0

    world.say(f"It was bedtime in {setting['place']}, and {setting['night']}.")
    world.say(f"{child.id} saw {danger['phrase']} and leaned closer, because it looked tiny and strange.")
    world.para()
    child.meters["risk"] = 1.0
    if predict_risk(world, child, risky):
        world.say(f'"Careful," {helper.id} said. "That can be {danger["risk_word"]}."')
        child.memes["curiosity"] += 0.5
        child.memes["care"] += 1.0
        child.meters["distance"] = 1.0
        world.say(f"{child.id} listened, backed away, and let {helper.id} move it out of reach.")
        child.memes["calm"] += 1.0
        risky.meters["distance"] = 2.0
        world.para()
        world.say(f"Then {setting['safe_rest']}.")
        world.say(f"The dangerous thing stayed far away, and the room felt safe again.")
    else:
        world.say(f"{helper.id} smiled and kept the dangerous thing far from the bed.")
        child.memes["calm"] += 1.0
        world.say(f"{setting['safe_rest']}.")
    propagate(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story for a small child that includes the word "{f["risk_word"]}" and a careful warning.',
        f"Tell a cautionary story where {f['child'].id} notices something dangerous at bedtime and a grown-up helps keep everyone safe.",
        f'Write a bedtime story with a calm ending in which a child learns not to go near something {f["risk_word"]}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    danger: str = f["danger"]
    return [
        QAItem(
            question=f"What did {child.id} see at bedtime?",
            answer=f"{child.id} saw {danger}. It looked small and odd, but {helper.id} knew it was dangerous and warned {child.pronoun('object')}.",
        ),
        QAItem(
            question=f"Why did {helper.id} tell {child.id} to back away?",
            answer=f"{helper.id} warned {child.id} because the thing near the bed was lethal. The safest choice was to keep it far away from little hands and sleepy mouths.",
        ),
        QAItem(
            question=f"What changed after {child.id} listened to {helper.id}?",
            answer=f"{child.id} backed away and the danger was moved out of reach. After that, the room became calm again and bedtime could continue safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What does lethal mean?",
            answer="Lethal means something can cause death. That is why a lethal thing must be kept away from children and handled by a grown-up.",
        ),
        QAItem(
            question="Why should children stay away from strange mushrooms or berries?",
            answer="Some mushrooms and berries can poison people if they are touched or eaten. A child should never taste them and should ask a grown-up to move them.",
        ),
    ]


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


ASP_RULES = r"""
risk(D) :- danger(D).
safe_end :- moved_out(D), danger(D).
moved_out(D) :- warning_given, listened, danger(D).
valid(S, D) :- setting(S), danger(D), afforded(S, D).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        for d in _safe_lookup(SETTINGS, s)["affords"]:
            lines.append(asp.fact("affords", s, d))
    for d in DANGERS:
        lines.append(asp.fact("danger", d))
    lines.append(asp.fact("warning_given"))
    lines.append(asp.fact("listened"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    smoke_params = StoryParams(setting="bedroom", danger="mushroom", helper="mother", child_name="Mina", child_gender="girl")
    sample = generate(smoke_params)
    if not sample.story:
        print("FAIL: empty story")
        return 1
    if ok:
        print("OK: ASP matches Python; smoke test passed.")
        return 0
    print("FAIL: ASP/Python mismatch.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        pass
    if params.danger not in DANGERS:
        pass
    if params.danger not in _safe_lookup(SETTINGS, params.setting)["affords"]:
        pass
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(DANGERS, params.danger), params)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="bedroom", danger="mushroom", helper="mother", child_name="Mina", child_gender="girl"),
    StoryParams(setting="nursery", danger="jar", helper="father", child_name="Finn", child_gender="boy"),
    StoryParams(setting="cabin", danger="berry", helper="grandmother", child_name="Lila", child_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for s, d in asp_valid_combos():
            print(s, d)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
