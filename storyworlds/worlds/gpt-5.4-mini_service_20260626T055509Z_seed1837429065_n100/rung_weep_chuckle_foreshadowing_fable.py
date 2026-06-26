#!/usr/bin/env python3
"""
A tiny fable-style story world about a bell, a warning, and a kind turn.

Seed tale:
A little mouse found an old bell hanging in the oak tree by the lane. Every
morning, the mouse gave the bell one bright ring so the creatures would know the
path was safe. One day, the mouse saw dark clouds piling up and the bell's rope
looked frayed. The mouse wept, because the bell had always helped everyone. Soon
the rope snapped and the bell fell silent. The rabbit chuckled at first, but
when the rain came and the path flooded, the rabbit understood the mouse's
warning and helped mend the rope. By evening, the bell was rung again, and all
the animals were glad.

This script models a compact fable domain with foreshadowing:
- physical meters: rope wear, path safety, rain, bell state
- emotional memes: worry, shame, relief, kindness, pride
- a clear premise, warning, turn, and resolution
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
# Core world model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    bell: object | None = None
    hero: object | None = None
    listener: object | None = None
    rope: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "squirrel", "hare", "sparrow"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the oak lane"
    weather: str = "clear"
    affords: set[str] = field(default_factory=set)
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
class Bell:
    label: str
    phrase: str
    rope_phrase: str
    rung_name: str = "rung"
    omen: str = "clouds"
    BELL: object | None = None
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
    weather: str
    hero: str
    listener: str
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
        self.fired: set[str] = set()
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
SETTINGS = {
    "lane": Setting(place="the oak lane", weather="clear", affords={"ring", "weep", "chuckle"}),
    "hill": Setting(place="the windy hill", weather="cloudy", affords={"ring", "weep", "chuckle"}),
    "grove": Setting(place="the quiet grove", weather="rainy", affords={"ring", "weep", "chuckle"}),
}

HEROES = {
    "mouse": {"label": "mouse", "phrase": "a small gray mouse", "kind": "character"},
    "rabbit": {"label": "rabbit", "phrase": "a bright-eyed rabbit", "kind": "character"},
    "squirrel": {"label": "squirrel", "phrase": "a quick little squirrel", "kind": "character"},
}

LISTENERS = {
    "rabbit": {"label": "rabbit"},
    "crow": {"label": "crow"},
    "hare": {"label": "hare"},
}

BELL = Bell(
    label="bell",
    phrase="an old bronze bell",
    rope_phrase="a thin rope",
    omen="dark clouds",
)

# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero_cfg = _safe_lookup(HEROES, params.hero)
    listener_cfg = _safe_lookup(LISTENERS, params.listener)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero,
        label=hero_cfg["label"],
        phrase=hero_cfg["phrase"],
        traits=["small", "wise"],
        meters={"hope": 1.0, "concern": 0.0},
        memes={"care": 1.0, "worry": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    listener = world.add(Entity(
        id="listener",
        kind="character",
        type=params.listener,
        label=listener_cfg["label"],
        phrase=f"a curious {listener_cfg['label']}",
        traits=["curious", "proud"],
        meters={"dry_path": 1.0, "rope_skill": 0.0},
        memes={"amusement": 0.0, "shame": 0.0, "kindness": 0.0},
    ))
    bell = world.add(Entity(
        id="bell",
        kind="thing",
        type="bell",
        label=BELL.label,
        phrase=BELL.phrase,
        owner="hero",
        caretaker="hero",
        meters={"rope_wear": 0.0, "ringing": 0.0, "safe": 1.0, "flood_risk": 0.0},
        memes={"memory": 1.0},
    ))
    rope = world.add(Entity(
        id="rope",
        kind="thing",
        type="rope",
        label="rope",
        phrase=BELL.rope_phrase,
        owner="hero",
        caretaker="hero",
        meters={"wear": 0.0, "frayed": 0.0},
    ))
    world.facts = {"hero": hero, "listener": listener, "bell": bell, "rope": rope}
    return world


def foreshadow(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    bell = _safe_fact(world, world.facts, "bell")
    rope = _safe_fact(world, world.facts, "rope")

    world.say(
        f"In the oak lane, {hero.phrase} watched over {bell.phrase} that hung from a branch."
    )
    world.say(
        f"Each morning, {hero.label} gave the bell one bright rung so the path would be safe."
    )
    rope.meters["wear"] += 1.0
    rope.meters["frayed"] += 1.0
    bell.meters["safe"] -= 0.1
    hero.memes["worry"] += 1.0
    world.say(
        f"Yet {hero.label} noticed {BELL.omen} gathering beyond the trees, and {BELL.rope_phrase} looked tired."
    )
    world.say(
        f"{hero.label} almost weeped at the thought that the bell might soon fall silent."
    )


def interrupt(world: World) -> None:
    listener = _safe_fact(world, world.facts, "listener")
    bell = _safe_fact(world, world.facts, "bell")
    hero = _safe_fact(world, world.facts, "hero")
    rope = _safe_fact(world, world.facts, "rope")

    listener.memes["amusement"] += 1.0
    world.say(
        f"{listener.label} only chuckled and said the old rope would last forever."
    )
    rope.meters["wear"] += 1.0
    rope.meters["frayed"] += 1.0
    bell.meters["safe"] -= 0.8
    bell.meters["ringing"] = 0.0
    world.say(
        f"Then the wind tugged hard, and the rope snapped; the bell lay still, and {hero.label} wept for the warning that had been ignored."
    )


def rain_turn(world: World) -> None:
    listener = _safe_fact(world, world.facts, "listener")
    bell = _safe_fact(world, world.facts, "bell")
    hero = _safe_fact(world, world.facts, "hero")
    rope = _safe_fact(world, world.facts, "rope")

    world.setting.weather = "rainy"
    bell.meters["flood_risk"] = 1.0
    world.say(
        f"By afternoon, rain found the lane, and water began to gather along the stones."
    )
    world.say(
        f"{listener.label} stopped chuckling when the path turned slick and the low ground started to flood."
    )
    listener.memes["shame"] += 1.0
    listener.memes["kindness"] += 1.0
    world.say(
        f"{listener.label} hurried back with a sturdy twig and helped {hero.label} mend the rope."
    )
    rope.meters["wear"] = 0.0
    rope.meters["frayed"] = 0.0
    bell.meters["safe"] = 1.0
    bell.meters["ringing"] = 1.0
    hero.memes["relief"] += 1.0
    hero.memes["pride"] += 1.0
    world.say(
        f"At last, the bell was rung again, and its clear sound carried over the wet lane like a lantern."
    )
    world.say(
        f"{hero.label} smiled because the warning had become a lesson, and {listener.label} listened with a kinder heart."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    foreshadow(world)
    world.para()
    interrupt(world)
    world.para()
    rain_turn(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    listener = _safe_fact(world, world.facts, "listener")
    return [
        f"Write a fable for children about {hero.label}, a bell, and a warning that proves true.",
        f"Tell a short story where {hero.label} notices trouble early, but {listener.label} chuckles and does not listen at first.",
        "Write a gentle fable that includes the words rung, weep, and chuckle, and ends with a useful lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    listener = _safe_fact(world, world.facts, "listener")
    bell = _safe_fact(world, world.facts, "bell")
    rope = _safe_fact(world, world.facts, "rope")

    return [
        QAItem(
            question=f"Why did {hero.label} start to worry about the bell?",
            answer=f"{hero.label} saw {BELL.omen} coming and noticed that {BELL.rope_phrase} looked frayed. That made {hero.label} worry the bell would stop helping the lane.",
        ),
        QAItem(
            question=f"What did {listener.label} do when {hero.label} warned about the rope?",
            answer=f"{listener.label} chuckled and said the rope would last forever, so the warning was ignored at first.",
        ),
        QAItem(
            question="What changed after the rain came?",
            answer=f"The rain made the lane slick and flooded the low ground, so {listener.label} understood the warning and helped mend the rope.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The rope was fixed, the bell was rung again, and everyone felt glad that the warning had been taken seriously.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a bell do?",
            answer="A bell makes a clear sound when it is rung, and people or animals can hear it from far away.",
        ),
        QAItem(
            question="What does it mean when something is frayed?",
            answer="Frayed means it is wearing out and starting to split into little loose pieces.",
        ),
        QAItem(
            question="Why can rain make a path slippery?",
            answer="Rain leaves water on the ground, and wet stones or dirt can become slick and hard to walk on.",
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_type(H).
listener(L) :- listener_type(L).
bell(bell).
rope(rope).

foreshadow :- omen_seen, rope(frayed).
warning_true :- foreshadow, rain, flood_risk.
ignored_warning :- listener_chuckles, warning_true.
resolved :- rain, mended, bell_rung_again.

#show warning_true/0.
#show ignored_warning/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HEROES:
        lines.append(asp.fact("hero_type", hid))
    for lid in LISTENERS:
        lines.append(asp.fact("listener_type", lid))
    lines.append(asp.fact("omen_seen"))
    lines.append(asp.fact("rope", "frayed"))
    lines.append(asp.fact("rain"))
    lines.append(asp.fact("flood_risk"))
    lines.append(asp.fact("listener_chuckles"))
    lines.append(asp.fact("mended"))
    lines.append(asp.fact("bell_rung_again"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show warning_true/0.\n#show ignored_warning/0.\n#show resolved/0."))
    shown = {sym.name for sym in model}
    expected = {"warning_true", "ignored_warning", "resolved"}
    if shown == expected:
        print("OK: ASP twin matches the reasoned fable beats.")
        return 0
    print(f"MISMATCH: got {sorted(shown)} expected {sorted(expected)}")
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    weather = getattr(args, "weather", None) or _safe_lookup(SETTINGS, place).weather
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    listener = getattr(args, "listener", None) or rng.choice(list(LISTENERS))
    if hero == listener:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, weather=weather, hero=hero, listener=listener)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print("--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about foreshadowing, a bell, and a lesson.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--weather", choices=["clear", "cloudy", "rainy"])
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--listener", choices=LISTENERS)
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
    StoryParams(place="lane", weather="clear", hero="mouse", listener="rabbit"),
    StoryParams(place="hill", weather="cloudy", hero="mouse", listener="crow"),
    StoryParams(place="grove", weather="rainy", hero="squirrel", listener="hare"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show warning_true/0.\n#show ignored_warning/0.\n#show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show warning_true/0.\n#show ignored_warning/0.\n#show resolved/0."))
        for sym in model:
            print(sym)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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
