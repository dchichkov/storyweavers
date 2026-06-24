#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/core_problem_solving_repetition_superhero_story.py
=============================================================================================================

A small superhero storyworld about a hero, a city core, repeated attempts, and
a final clever fix.

The seed idea:
---
A young superhero tries to save a city power core that keeps going dim. The hero
tries one fix, then another, and learns that the core needs a careful reset
instead of brute force. Repetition matters: the hero makes several attempts,
each one closer to the right answer, before the core shines again.

Design:
---
- Physical meters model charge, damage, and repair progress.
- Emotional memes model worry, courage, and relief.
- The story is driven by a small simulated problem-solving loop.
- The repeated attempts are not decorative; they change the world state.
- The ending proves the problem was solved by showing the core bright again.

This world keeps the style close to a superhero story:
capes, alarms, rooftops, teamwork, and a hopeful rescue.
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

CORE_THRESHOLD = 1.0



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    core: object | None = None
    hero: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "hero"}:
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
class Scene:
    place: str
    weather: str
    afford: str
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
    method: str
    clue: str
    effect: str
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
    hero_name: str
    hero_type: str
    sidekick_name: str
    core: str
    tool: str
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
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.attempts: int = 0
        self.fixed: bool = False
        self.trace_steps: list[str] = []

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
        clone = World(self.scene)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.attempts = self.attempts
        clone.fixed = self.fixed
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld about a core, repetition, and problem solving.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--core", choices=sorted(CORES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
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


SETTINGS = {
    "city": Scene(place="the city", weather="stormy", afford="roof"),
    "tower": Scene(place="the watch tower", weather="windy", afford="platform"),
    "harbor": Scene(place="the harbor", weather="foggy", afford="dock"),
}

TOOLS = {
    "hammer": Tool("hammer", "a heavy hammer", "hit", "too much force", "the core shakes but does not open"),
    "scanner": Tool("scanner", "a bright scanner", "scan", "a hidden latch", "the core reveals a pattern"),
    "gloves": Tool("gloves", "insulated gloves", "hold", "safe handling", "the core can be reset without sparking"),
    "beam": Tool("beam", "a silver beam wand", "shine", "the reset mark", "the core lights up the right way"),
}

CORES = {
    "city_core": {
        "label": "city power core",
        "phrase": "the city power core",
        "problem": "going dim",
        "fix": "reset",
    },
    "signal_core": {
        "label": "signal core",
        "phrase": "the signal core",
        "problem": "flickering",
        "fix": "steady",
    },
    "heart_core": {
        "label": "harbor heart core",
        "phrase": "the harbor heart core",
        "problem": "humming weakly",
        "fix": "reawaken",
    },
}

GIRL_NAMES = ["Nova", "Mira", "Zia", "Iris", "Ada", "Luna"]
BOY_NAMES = ["Kai", "Theo", "Finn", "Arlo", "Max", "Leo"]
SIDEKICKS = ["Pip", "Bean", "Jules", "Zed", "Tia"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, scene in SETTINGS.items():
        for core in CORES:
            for tool in TOOLS:
                combos.append((place, core, tool))
    return combos


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for cid, c in CORES.items():
        lines.append(asp.fact("core", cid))
        lines.append(asp.fact("problem", cid, c["problem"]))
        lines.append(asp.fact("fix", cid, c["fix"]))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("method", tid, t.method))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P, C, T) :- place(P), core(C), tool(T).
repetition(C, N) :- core(C), N = 3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def scene_detail(scene: Scene) -> str:
    return {
        "the city": "Dark clouds pressed over the streets, and sirens blinked like tiny stars.",
        "the watch tower": "Wind tugged at the tower flags while the lamps flickered softly.",
        "the harbor": "Fog curled over the water, and the docks glimmered with salt and rain.",
    }[scene.place]


def _attempt(world: World, hero: Entity, core: Entity, tool: Tool) -> str:
    world.attempts += 1
    attempt = world.attempts
    if attempt == 1:
        core.meters["damage"] += 1
        hero.memes["worry"] += 1
        world.trace_steps.append("first attempt failed")
        return f"{hero.id} tried {tool.label}, but {core.label} only flashed and stayed {_safe_lookup(CORES, core.type)['problem']}."
    if attempt == 2:
        core.meters["damage"] = max(0.0, core.meters["damage"] - 0.5)
        core.meters["clue"] += 1
        hero.memes["focus"] += 1
        world.trace_steps.append("second attempt found the clue")
        return f"{hero.id} tried again, and {tool.label} revealed a small clue on {core.label}."
    core.meters["damage"] = 0.0
    core.meters["charge"] = 1.0
    hero.memes["relief"] += 1
    core.memes["safe"] += 1
    world.fixed = True
    world.trace_steps.append("third attempt solved it")
    return f"On the third try, {hero.id} used {tool.label} the careful way, and {core.label} woke up bright and safe."


def tell(scene: Scene, core_id: str, tool_id: str, hero_name: str, hero_type: str, sidekick_name: str) -> World:
    world = World(scene)
    core_cfg = _safe_lookup(CORES, core_id)
    tool = _safe_lookup(TOOLS, tool_id)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="sidekick"))
    core = world.add(Entity(id=core_id, kind="thing", type=core_id, label=core_cfg["label"], phrase=core_cfg["phrase"]))
    core.meters["damage"] = 1.0
    core.meters["charge"] = 0.0
    core.memes["fear"] = 1.0

    world.say(f"{hero.id} was a young superhero who watched over {scene.place}.")
    world.say(f"One night, the alarm rang because {core_cfg['phrase']} was {core_cfg['problem']}.")
    world.say(scene_detail(scene))
    world.say(f"{hero.id} tightened {hero.pronoun('possessive')} cape and said, \"I'll fix this.\"")

    world.para()
    world.say(f"{hero.id} and {sidekick.id} checked the core together.")
    world.say(_attempt(world, hero, core, tool))

    world.para()
    world.say(f"But the problem was still there, so {hero.id} tried again.")
    world.say(_attempt(world, hero, core, tool))

    world.para()
    world.say(f"{sidekick.id} pointed at the clue, and {hero.id} understood the pattern.")
    world.say(_attempt(world, hero, core, tool))
    world.say(f"At last, {core.label} glowed steady, and the city felt calm again.")

    world.facts.update(hero=hero, sidekick=sidekick, core=core, tool=tool, scene=scene, fixed=world.fixed)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story that includes the word "core" and shows a hero solving the same problem more than once.',
        f"Tell a child-friendly story where {f['hero'].id} keeps trying to fix {f['core'].label} until the right method works.",
        f"Write a story about a superhero, a helper, and a broken core, with repetition and a happy rescue at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    core: Entity = _safe_fact(world, f, "core")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a young superhero who tries to save {core.label}.",
        ),
        QAItem(
            question=f"What problem did {hero.id} have to solve?",
            answer=f"{core.label} was {_safe_lookup(CORES, core.type)['problem']}, so {hero.id} had to keep trying until it was fixed.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the problem?",
            answer=f"{sidekick.id} helped by noticing the clue and staying beside {hero.id} through each try.",
        ),
        QAItem(
            question=f"What tool finally helped most?",
            answer=f"{tool.label} helped because it revealed the clue and let {hero.id} use a careful fix.",
        ),
    ]
    if f["fixed"]:
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"It ended with {core.label} glowing bright again, and {hero.id} feeling proud and relieved.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who helps others and tries to stop big problems.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a good way to fix what is wrong.",
        ),
        QAItem(
            question="Why can trying again help?",
            answer="Trying again can help because each new try can teach you something useful.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  attempts: {world.attempts}")
    lines.append(f"  fixed: {world.fixed}")
    lines.append(f"  trace: {world.trace_steps}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    core = getattr(args, "core", None) or rng.choice(sorted(CORES))
    tool = getattr(args, "tool", None) or rng.choice(sorted(TOOLS))
    if (place, core, tool) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_type = getattr(args, "hero_type", None) or rng.choice(["boy", "girl"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    sidekick_name = getattr(args, "sidekick_name", None) or rng.choice(SIDEKICKS)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, sidekick_name=sidekick_name, core=core, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.core, params.tool, params.hero_name, params.hero_type, params.sidekick_name)
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
    StoryParams(place="city", hero_name="Nova", hero_type="girl", sidekick_name="Pip", core="city_core", tool="scanner"),
    StoryParams(place="tower", hero_name="Kai", hero_type="boy", sidekick_name="Jules", core="signal_core", tool="gloves"),
    StoryParams(place="harbor", hero_name="Mira", hero_type="girl", sidekick_name="Tia", core="heart_core", tool="beam"),
]


def build_asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(build_asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_show() -> str:
    return build_asp_program("#show compatible/3.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, core, tool) combos:\n")
        for p, c, t in combos:
            print(f"  {p:8} {c:12} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.core} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
