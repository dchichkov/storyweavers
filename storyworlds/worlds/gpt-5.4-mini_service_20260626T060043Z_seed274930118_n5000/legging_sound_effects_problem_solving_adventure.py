#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/legging_sound_effects_problem_solving_adventure.py
================================================================================================

A small adventure storyworld about a child, a noisy route, and a careful fix.

Seed tale:
---
A curious child named Mina wanted to cross the windy boardwalk to reach a kite
shop. She wore her favorite striped leggings, but the path ahead had loose
sticks, rattling signs, and a stuck gate. Mina listened for clues, solved each
problem one by one, and kept going until the kite shop's chime rang ahead.

World shape:
---
- The hero must travel through a place with one or more sound cues.
- The path contains a problem the child can solve with a specific tool.
- The child keeps favorite leggings clean and safe by using the right fix.
- The ending proves progress with a concrete sound image and a changed state.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    implement: object | None = None
    leggings: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str
    indoors: bool = False
    sounds: list[str] = field(default_factory=list)
    hazards: list[str] = field(default_factory=list)
    destination: str = ""
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
class Tool:
    id: str
    label: str
    use: str
    fixes: str
    sound: str
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
    setting: str
    name: str
    gender: str
    parent: str
    tool: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.rang: set[str] = set()

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
    "boardwalk": Setting(
        place="the windy boardwalk",
        sounds=["whoosh", "clatter", "creak", "ding"],
        hazards=["loose sticks", "a rattling sign", "a stuck gate"],
        destination="the kite shop",
    ),
    "forest_path": Setting(
        place="the pine trail",
        sounds=["rustle", "snap", "tap", "ping"],
        hazards=["a fallen branch", "a muddy puddle", "a rope gate"],
        destination="the lookout tower",
    ),
    "harbor": Setting(
        place="the harbor pier",
        sounds=["splash", "clink", "clang", "honk"],
        hazards=["a tangled rope", "a crate stack", "a jammed hatch"],
        destination="the ferry bell",
    ),
}

TOOLS = {
    "string": Tool(id="string", label="a coil of string", use="tie and guide things", fixes="tied the loose sign", sound="zip"),
    "stick": Tool(id="stick", label="a sturdy stick", use="poke and lift things", fixes="lifted the stuck gate latch", sound="tap"),
    "cloth": Tool(id="cloth", label="a bright cloth", use="wrap and wave it", fixes="marked the safe path", sound="flap"),
}

NAMES = {
    "girl": ["Mina", "Lina", "Tara", "Nora", "Ivy"],
    "boy": ["Owen", "Ravi", "Eli", "Noah", "Finn"],
}
PARENTS = {"girl": ["mother", "mom"], "boy": ["father", "dad"]}


def build_world(setting: Setting, name: str, gender: str, parent: str, tool: Tool) -> World:
    w = World(setting)
    hero = w.add(Entity(id=name, kind="character", type=gender))
    guide = w.add(Entity(id="Guide", kind="character", type=parent, label=parent))
    leggings = w.add(Entity(
        id="leggings",
        type="leggings",
        label="leggings",
        phrase="striped leggings",
        owner=hero.id,
        worn_by=hero.id,
        region="legs",
        plural=True,
    ))
    implement = w.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        phrase=tool.label,
        owner=hero.id,
    ))
    w.facts.update(hero=hero, guide=guide, leggings=leggings, tool=implement)
    return w


def tell_story(w: World) -> None:
    hero = w.facts["hero"]
    guide = w.facts["guide"]
    leggings = w.facts["leggings"]
    tool = w.facts["tool"]

    w.say(
        f"{hero.id} was a curious child who loved adventure and the swish-swish of {leggings.label}."
    )
    w.say(
        f"On the way to {w.setting.destination}, {hero.id} and {guide.label} heard "
        f"{w.setting.sounds[0]} and {w.setting.sounds[1]} from {w.setting.place}."
    )

    w.para()
    hazard1, hazard2, hazard3 = w.setting.hazards
    w.say(
        f"Then {hazard1} blocked the path, and the next step went {w.setting.sounds[1]} underfoot."
    )
    w.say(
        f"{hero.id} listened hard, noticed the problem, and said, "
        f'"We can solve this."'
    )
    w.say(
        f"Using {tool.label}, {hero.id} {tool.fixes} with a careful {tool.sound}."
    )

    w.para()
    w.say(
        f"That helped make room for the next challenge: {hazard2}."
    )
    w.say(
        f"{guide.label} pointed to a safe side step, and {hero.id} followed the clue."
    )
    w.say(
        f"The last barrier was {hazard3}, but {hero.id} used the same calm thinking again."
    )
    w.say(
        f"At last, the path opened and the air rang with a cheerful {w.setting.sounds[-1]} "
        f"from {w.setting.destination} ahead."
    )

    w.facts["solved"] = True
    w.facts["ending_sound"] = w.setting.sounds[-1]
    w.facts["tool_name"] = tool.label
    w.facts["leggings_clean"] = True


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    return [
        f'Write a short adventure story for a young child with the sound "{w.setting.sounds[0]}" in it.',
        f"Tell a story where {f['hero'].id} wears leggings, hears tricky sounds, and solves problems on the way to {w.setting.destination}.",
        f'Write a gentle adventure about "{f["tool_name"]}" helping a child stay steady on a noisy path.',
    ]


def story_qa(w: World) -> list[QAItem]:
    hero = w.facts["hero"]
    guide = w.facts["guide"]
    qas = [
        QAItem(
            question=f"What did {hero.id} wear on {hero.id}'s legs during the trip?",
            answer=f"{hero.id} wore striped leggings while going along the path.",
        ),
        QAItem(
            question=f"What did {hero.id} and {guide.label} hear first at {w.setting.place}?",
            answer=f"They heard {w.setting.sounds[0]} first, then other sounds as they walked.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the first problem on the path?",
            answer=f"{hero.id} used {w.facts['tool_name']} and solved the problem with careful thinking.",
        ),
        QAItem(
            question=f"What sound came from {w.setting.destination} at the end?",
            answer=f"The ending sound was {w.facts['ending_sound']}, which showed they had reached the destination.",
        ),
    ]
    return qas


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are leggings?",
            answer="Leggings are stretchy clothes that cover the legs and help a child move comfortably.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a smart way to make the trouble go away or work around it.",
        ),
        QAItem(
            question="Why do sound effects matter in a story?",
            answer="Sound effects help the reader imagine the world by showing what things sound like, like whoosh, clatter, or ding.",
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


def dump_trace(w: World) -> str:
    e = w.facts["leggings"]
    return (
        "--- world model state ---\n"
        f"  hero={w.facts['hero'].id}\n"
        f"  guide={w.facts['guide'].label}\n"
        f"  setting={w.setting.place}\n"
        f"  destination={w.setting.destination}\n"
        f"  leggings_worn_by={e.worn_by}\n"
        f"  solved={w.facts.get('solved')}\n"
        f"  ending_sound={w.facts.get('ending_sound')}"
    )


ASP_RULES = r"""
setting(boardwalk).
setting(forest_path).
setting(harbor).

sound(boardwalk,whoosh).
sound(boardwalk,clatter).
sound(boardwalk,creak).
sound(boardwalk,ding).

sound(forest_path,rustle).
sound(forest_path,snap).
sound(forest_path,tap).
sound(forest_path,ping).

sound(harbor,splash).
sound(harbor,clink).
sound(harbor,clang).
sound(harbor,honk).

hazard(boardwalk,loose_sticks).
hazard(boardwalk,rattling_sign).
hazard(boardwalk,stuck_gate).

hazard(forest_path,fallen_branch).
hazard(forest_path,muddy_puddle).
hazard(forest_path,rope_gate).

hazard(harbor,tangled_rope).
hazard(harbor,crate_stack).
hazard(harbor,jammed_hatch).

tool(string,sign).
tool(stick,gate).
tool(cloth,path).

solvable(S,T) :- hazard(S,sign), tool(T,sign).
solvable(S,T) :- hazard(S,gate), tool(T,gate).
solvable(S,T) :- hazard(S,path), tool(T,path).

adventure(S,T) :- setting(S), tool(T), solvable(S,T).
#show adventure/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for s in _safe_lookup(SETTINGS, sid).sounds:
            lines.append(asp.fact("sound", sid, s))
        for h in _safe_lookup(SETTINGS, sid).hazards:
            lines.append(asp.fact("hazard", sid, h))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "adventure")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for tid, tool in TOOLS.items():
            ok = False
            if "sign" in s.hazards and tool.fixes.endswith("sign"):
                ok = True
            if "gate" in s.hazards and tool.fixes.endswith("gate"):
                ok = True
            if "path" in s.hazards and tool.fixes.endswith("path"):
                ok = True
            if ok:
                out.append((sid, tid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with sound effects and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "mom", "father", "dad"])
    ap.add_argument("--tool", choices=TOOLS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[1] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, tool = rng.choice(combos)
    if getattr(args, "gender", None):
        gender = getattr(args, "gender", None)
    else:
        gender = rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(_safe_lookup(PARENTS, gender))
    return StoryParams(setting=setting, name=name, gender=gender, parent=parent, tool=tool)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    tool = _safe_lookup(TOOLS, params.tool)
    w = build_world(setting, params.name, params.gender, params.parent, tool)
    tell_story(w)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        for setting, tool in combos:
            print(f"{setting}\t{tool}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for setting, tool in valid_combos():
            gender = "girl"
            name = _safe_lookup(NAMES, gender)[0]
            parent = _safe_lookup(PARENTS, gender)[0]
            params = StoryParams(setting=setting, name=name, gender=gender, parent=parent, tool=tool, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(getattr(args, "n", None) * 50, 50)):
            if len(samples) >= getattr(args, "n", None):
                break
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
