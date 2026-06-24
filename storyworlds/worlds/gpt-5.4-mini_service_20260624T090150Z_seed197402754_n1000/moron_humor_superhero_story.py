#!/usr/bin/env python3
"""
moron_humor_superhero_story.py
==============================

A small superhero humor story world.

Seed tale:
---
Milo was a tiny, eager superhero who wanted to save the city. He had a shiny cape,
a sticker-covered sidekick robot, and a very important button that made his boots
go fast.

One day, Captain Snip, a very silly villain, snuck into the city square with the
moron magnet, a joke machine that made people drop what they were doing and stare.
Milo tried to stop him, but the magnet made his thoughts feel wobbly. His robot
kept calling the machine "a moron trick," which made Milo laugh at the wrong time.

Then Milo noticed the magnet worked through metal. He swapped his metal belt for
a cloth sash, used a rubber spoon to push the switch, and turned the moron magnet
off. Captain Snip tripped over his own cape and landed in a fountain. Milo and the
robot laughed, and the city cheered.

State model:
---
hero courage -> helps hero act despite wobble
villain prank -> increases city confusion
villain confusion + hero calm -> lets hero notice a non-metal workaround
cloth/rubber gear -> blocks the magnet's silly pull
rescue -> city relief rises, confusion falls
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    blocks: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gadget: object | None = None
    gear_ent: object | None = None
    hero: object | None = None
    sidekick: object | None = None
    villain: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"shiny": 0.0}
        if not self.memes:
            self.memes = {"courage": 0.0, "wobble": 0.0, "joy": 0.0, "confusion": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    place: str = "the city square"
    inside: bool = False
    affords: set[str] = field(default_factory=lambda: {"prank", "rescue"})
    SETTINGS: set[str] = field(default_factory=set)
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
class Gear:
    id: str
    label: str
    blocks: set[str]
    prep: str
    tail: str
    plural: bool = False
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
class Threat:
    id: str
    name: str
    effect: str
    clue: str
    counter: str
    requires: str
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


@dataclass
class StoryParams:
    threat: str
    gear: str
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {"city": Setting()}
THREATS = {
    "moron_magnet": Threat(
        id="moron_magnet",
        name="the moron magnet",
        effect="made everyone stare and forget their jobs",
        clue="It only tugged at metal things.",
        counter="use something non-metal to press the switch",
        requires="cloth or rubber",
    ),
    "giggle_glue": Threat(
        id="giggle_glue",
        name="the giggle glue",
        effect="made boots stick to the sidewalk",
        clue="It stayed away from dry paper and wooden sticks.",
        counter="use a wooden lever",
        requires="wood",
    ),
    "zap_zipper": Threat(
        id="zap_zipper",
        name="the zap zipper",
        effect="made capes spark and flutter wild",
        clue="It liked shiny zippers but not plain cloth ties.",
        counter="tie the cape with cloth",
        requires="cloth",
    ),
}

GEAR = {
    "sash": Gear("sash", "a cloth sash", {"cloth"}, "swap his metal belt for a cloth sash", "swapped the belt for a cloth sash"),
    "spoon": Gear("spoon", "a rubber spoon", {"rubber"}, "use a rubber spoon to press the switch", "used a rubber spoon"),
    "stick": Gear("stick", "a wooden stick", {"wood"}, "grab a wooden stick to nudge the lever", "used a wooden stick"),
}

HERO_NAMES = ["Milo", "Pia", "Rex", "Nia", "Toby", "Luna"]
SIDEKICK_NAMES = ["Bolt", "Nib", "Zip", "Dot", "Echo"]

ASP_RULES = r"""
threat(T) :- threat_id(T).
gear(G) :- gear_id(G).

needs_block(T, B) :- threat_requires(T, B).
has_fix(T, G) :- needs_block(T, B), gear_blocks(G, B).

valid(T, G) :- threat(T), gear(G), has_fix(T, G).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", "city"), asp.fact("inside", "city")]
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat_id", tid))
        lines.append(asp.fact("threat_name", tid, t.name))
        lines.append(asp.fact("threat_requires", tid, t.requires))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear_id", gid))
        for b in sorted(g.blocks):
            lines.append(asp.fact("gear_blocks", gid, b))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))

def python_valid() -> list[tuple]:
    out = []
    for tid, t in THREATS.items():
        for gid, g in GEAR.items():
            if t.requires in g.blocks:
                out.append((tid, gid))
    return sorted(out)

def asp_verify() -> int:
    a, p = set(asp_valid()), set(python_valid())
    if a == p:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(a - p))
    print("only in Python:", sorted(p - a))
    return 1

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous superhero story world.")
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--gear", choices=GEAR)
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

def valid_pairs():
    return python_valid()

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_pairs()
              if (getattr(args, "threat", None) is None or c[0] == getattr(args, "threat", None))
              and (getattr(args, "gear", None) is None or c[1] == getattr(args, "gear", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    threat, gear = rng.choice(list(combos))
    return StoryParams(threat=threat, gear=gear)

def _do_prank(world: World, hero: Entity, villain: Entity, threat: Threat) -> None:
    hero.memes["wobble"] += 1
    villain.memes["confusion"] += 1
    world.facts["clue"] = threat.clue
    world.say(f"{villain.label} set off {threat.name}, and the whole square got silly at once.")

def _use_gear(world: World, hero: Entity, gear: Gear, threat: Threat) -> bool:
    if gear.blocks and threat.requires not in gear.blocks:
        return False
    hero.meters["shiny"] += 0.0
    world.say(f"Then {hero.id} {gear.prep}.")
    return True

def tell(threat: Threat, gear: Gear, hero_name: str, sidekick_name: str) -> World:
    world = World(SETTINGS["city"])
    hero = world.add(Entity(hero_name, kind="character", type="boy", label=hero_name))
    sidekick = world.add(Entity(sidekick_name, kind="character", type="robot", label=sidekick_name))
    villain = world.add(Entity("villain", kind="character", type="villain", label="Captain Snip"))
    gadget = world.add(Entity(threat.id, type="thing", label=threat.name, phrase=threat.name))
    gear_ent = world.add(Entity(gear.id, type="thing", label=gear.label, protective=True, blocks=set(gear.blocks)))

    hero.memes["courage"] += 1
    world.say(f"{hero.id} was a tiny superhero with a bright cape and a big heart.")
    world.say(f"{sidekick.id} was a sticker-covered sidekick robot who liked to say, \"That is a moron trick!\"")
    world.say(f"One day, {villain.label} rolled into {world.setting.place} with {gadget.label}.")
    world.para()
    _do_prank(world, hero, villain, threat)
    world.say(f"{threat.clue} {hero.id} felt {threat.effect}, but {hero.id} still looked for a plan.")
    world.say(f"{sidekick.id} pointed at the machine and said the answer was to {threat.counter}.")
    world.para()
    if _use_gear(world, hero, gear_ent, threat):
        hero.memes["joy"] += 1
        hero.memes["wobble"] = 0.0
        villain.memes["confusion"] += 1
        world.say(f"{hero.id} used the trick and turned the moron magnet off.")
        world.say(f"{villain.label} tripped over {villain.pronoun('possessive')} own cape and splashed into the fountain.")
        world.say(f"{hero.id} and {sidekick.id} laughed, and the city cheered because the silly trouble was gone.")
    world.facts.update(hero=hero, sidekick=sidekick, villain=villain, threat=threat, gear=gear_ent)
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short superhero story for a child that includes the word "moron" in a funny way.',
        f"Tell a humorous superhero tale where {f['hero'].id} stops {f['threat'].name} with {f['gear'].label}.",
        f"Write a bright, kid-friendly rescue story in {world.setting.place} with a silly villain and a clever fix.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who saved the city from {f['threat'].name}?",
            answer=f"{f['hero'].id} saved the city with help from {f['sidekick'].id}."
        ),
        QAItem(
            question=f"What was funny about {f['threat'].name}?",
            answer=f"It was called the moron magnet, and it made everyone stare and act wobbly."
        ),
        QAItem(
            question=f"How did {f['hero'].id} stop the trouble?",
            answer=f"{f['hero'].id} used {f['gear'].label} to do the job without touching the machine with metal."
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave helper who uses special skills or gear to protect people."
        ),
        QAItem(
            question="What does a cape do?",
            answer="A cape is a piece of clothing that can make a hero look dramatic and fast."
        ),
        QAItem(
            question="What is a magnet?",
            answer="A magnet is something that pulls certain metal things toward it."
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.blocks:
            bits.append(f"blocks={sorted(e.blocks)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)

CURATED = [
    StoryParams("moron_magnet", "spoon"),
    StoryParams("giggle_glue", "stick"),
    StoryParams("zap_zipper", "sash"),
]

def generate(params: StoryParams) -> StorySample:
    threat = _safe_lookup(THREATS, params.threat)
    gear = GEAR[params.gear]
    rng = random.Random(params.seed or 0)
    hero = rng.choice(HERO_NAMES)
    sidekick = rng.choice(SIDEKICK_NAMES)
    world = tell(threat, gear, hero, sidekick)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} compatible threat/gear pairs:")
        for t, g in vals:
            print(f"  {t:14} {g}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
