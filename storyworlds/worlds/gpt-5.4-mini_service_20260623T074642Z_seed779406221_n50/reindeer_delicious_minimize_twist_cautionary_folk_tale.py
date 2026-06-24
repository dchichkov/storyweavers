#!/usr/bin/env python3
"""
storyworlds/worlds/reindeer_delicious_minimize_twist_cautionary_folk_tale.py
=============================================================================

A small folk-tale storyworld about a reindeer, a delicious treat, and a plan to
minimize a risky twist.

Premise:
- A reindeer loves a delicious cake, berry pie, or maple sweet.
- A caretaker warns that the treat is meant for the winter feast, not for a
  greedy nibble.
- The reindeer tries a clever twist: to "minimize" the problem by taking only a
  little.
- That shortcut backfires in a folk-tale way: the treat is damaged, the herd is
  sad, and the reindeer learns to repair the harm with a careful, shared fix.

The simulation tracks:
- physical meters: hunger, sweetness, crumbs, spill, repaired, wrapped
- emotional memes: desire, caution, worry, regret, trust, joy

The story only branches into valid, compact variations:
- different reindeer names and roles
- different delicious treats
- different settings and caretakers
- different cautionary lessons
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wrapped: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    herd: object | None = None
    reindeer: object | None = None
    treat: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Setting:
    place: str
    indoors: bool = False
    season: str = "winter"
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
class Treat:
    id: str
    label: str
    phrase: str
    sweetness: str
    crumbs: str
    spill: str
    can_wrap: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class StoryParams:
    place: str
    treat: str
    name: str
    herd_role: str
    caretaker: str
    tone: str
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "cabin": Setting("the little cabin", indoors=True, season="winter"),
    "barn": Setting("the red barn", indoors=True, season="winter"),
    "grove": Setting("the pine grove", indoors=False, season="winter"),
}

TREATS = {
    "cake": Treat("cake", "cake", "a berry cake", "sweet", "crumbly", "crumbs"),
    "pie": Treat("pie", "pie", "a warm berry pie", "sweet", "juicy", "juice"),
    "tart": Treat("tart", "tart", "a maple tart", "rich", "sticky", "sticky syrup"),
    "bun": Treat("bun", "bun", "a cinnamon bun", "sweet", "crumbly", "crumbs"),
}

NAMES = ["Rory", "Nia", "Bram", "Elsa", "Milo", "Tova", "Hank", "Lila"]
HERD_ROLES = ["young", "small", "curious", "cheerful", "hungry"]
CARETAKERS = ["grandmother", "grandfather", "aunt", "uncle", "elder"]
TONES = ["careful", "wary", "gentle", "mischievous", "bashful"]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


def _r_repair(world: World) -> list[str]:
    out = []
    reindeer = world.get("reindeer")
    treat = world.get("treat")
    if treat.meters.get("spilled", 0) >= THRESHOLD and not treat.wrapped:
        if ("repair",) in world.fired:
            return []
        world.fired.add(("repair",))
        treat.meters["repaired"] = 1
        reindeer.memes["regret"] += 1
        reindeer.memes["trust"] += 1
        out.append("They wrapped the treat back up and made it right.")
    return out


def propagate(world: World) -> None:
    while True:
        produced = _r_repair(world)
        if not produced:
            return
        for s in produced:
            world.say(s)


def risk_treat(reindeer: Entity, treat: Entity) -> None:
    reindeer.memes["desire"] += 1
    treat.meters["wrapped"] = 1


def tell(setting: Setting, treat_cfg: Treat, name: str, herd_role: str, caretaker: str, tone: str) -> World:
    world = World(setting)
    reindeer = world.add(Entity(id="reindeer", kind="character", type="reindeer", label=name))
    elder = world.add(Entity(id="caretaker", kind="character", type=caretaker, label=f"the {caretaker}"))
    treat = world.add(Entity(id="treat", type=treat_cfg.id, label=treat_cfg.label, phrase=treat_cfg.phrase, caretaker=elder.id))
    herd = world.add(Entity(id="herd", kind="character", type="reindeer", label="the herd", plural=True))

    reindeer.meters["hunger"] = 1
    treat.meters["sweetness"] = 1
    reindeer.memes["caution"] = 1

    world.say(f"Once in {setting.place}, there lived a {tone} reindeer named {name}.")
    world.say(f"{name} was a {herd_role} reindeer, and {reindeer.pronoun('subject')} loved anything delicious.")
    world.say(f"One day {elder.label} brought out {treat.phrase}, and its smell made {name}'s nose twitch.")

    world.para()
    world.say(f"{name} wanted to taste the {treat.label} at once, but {elder.label} raised a hand.")
    world.say(f'"That {treat.label} is for the winter feast," said {elder.label}. "We must minimize the danger and keep it safe."')

    world.para()
    reindeer.memes["caution"] += 1
    reindeer.memes["worry"] += 1
    world.say(f"{name} tried a twist of cleverness and said, " f'"Then I will only take a tiny bite, so the trouble is small."')
    treat.meters["crumbs"] += 1
    treat.meters["spilled"] += 1
    reindeer.memes["regret"] += 1
    world.say(f"But the tiny bite still made {treat.label} {treat_cfg.crumbs}, and a little {treat_cfg.spill} landed on the cloth.")

    world.para()
    if setting.indoors:
        world.say(f"The cabin grew quiet, because the feast sweet was no longer neat.")
    else:
        world.say(f"The pine grove felt hushed, because even the wind seemed to see the mess.")
    world.say(f"{name} bowed {reindeer.pronoun('possessive')} head and promised to mend the harm.")
    if treat_cfg.can_wrap:
        treat.wrapped = True
    propagate(world)
    world.say(f"At last, {name} helped wrap the treat again, and {elder.label} smiled.")
    world.say(f"The reindeer learned that a clever twist cannot truly minimize a wrong thing; only careful hands can fix it.")

    world.facts.update(
        reindeer=reindeer,
        caretaker=elder,
        treat=treat,
        setting=setting,
        tone=tone,
        herd_role=herd_role,
    )
    return world


def knowledge_qa() -> list[QAItem]:
    return [
        QAItem(
            question="What is a reindeer?",
            answer="A reindeer is a deer that lives in cold places and has wide hooves for snow.",
        ),
        QAItem(
            question="What does delicious mean?",
            answer="Delicious means something tastes very good and makes people want another bite.",
        ),
        QAItem(
            question="What does minimize mean?",
            answer="Minimize means to make something smaller or to reduce it as much as you can.",
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    r, c, t = f["reindeer"], f["caretaker"], f["treat"]
    return [
        QAItem(
            question=f"Who wanted the delicious {t.label}?",
            answer=f"The reindeer named {r.label} wanted it very much.",
        ),
        QAItem(
            question=f"Why did {c.label} warn {r.label} about the treat?",
            answer=f"{c.label} wanted to keep the {t.label} safe for the winter feast, so {r.label} should not spoil it.",
        ),
        QAItem(
            question=f"What was wrong with {r.label}'s twist of minimization?",
            answer=f"{r.label} tried to make the trouble small by taking only a tiny bite, but the treat still got crumbs and spill on it.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{r.label} helped wrap the treat again, and everyone saw that a careful fix was better than a greedy shortcut.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return knowledge_qa()


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary folk tale about a reindeer and a delicious treat.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=CARETAKERS)
    ap.add_argument("--tone", choices=TONES)
    ap.add_argument("--role", choices=HERD_ROLES)
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
    treat = getattr(args, "treat", None) or rng.choice(list(TREATS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    caretaker = getattr(args, "caretaker", None) or rng.choice(CARETAKERS)
    tone = getattr(args, "tone", None) or rng.choice(TONES)
    role = getattr(args, "role", None) or rng.choice(HERD_ROLES)
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, treat=treat, name=name, herd_role=role, caretaker=caretaker, tone=tone)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TREATS, params.treat), params.name, params.herd_role, params.caretaker, params.tone)
    prompts = [
        f"Write a short folk tale about a reindeer named {params.name} and a delicious {params.treat}.",
        f"Tell a cautionary story where a reindeer tries to minimize a problem with a clever twist.",
        f"Write a child-friendly tale set in {params.place} with a gentle lesson about greed and care.",
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("delicious", tid))
    return "\n".join(lines)


ASP_RULES = r"""
% A treat is delicious if marked so in facts.
delight(T) :- delicious(T).

% A cautionary twist means the reindeer wants to take a small bite to minimize risk.
twist(T) :- treat(T), delight(T).

cautionary_story(P, T) :- setting(P), treat(T), twist(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_story(world: World) -> str:
    return world.render()


def main() -> None:
    args = build_parser().parse_args()
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "show_asp", None):
        print(asp_program("#show cautionary_story/2."))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, place in enumerate(SETTINGS):
            params = StoryParams(
                place=place,
                treat=list(TREATS)[i % len(TREATS)],
                name=_safe_lookup(NAMES, i % len(NAMES)),
                herd_role=_safe_lookup(HERD_ROLES, i % len(HERD_ROLES)),
                caretaker=_safe_lookup(CARETAKERS, i % len(CARETAKERS)),
                tone=_safe_lookup(TONES, i % len(TONES)),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
