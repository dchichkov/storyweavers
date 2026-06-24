#!/usr/bin/env python3
"""
storyworlds/worlds/intelligence_problem_solving_nursery_rhyme.py
===============================================================

A small nursery-rhyme style story world about intelligence and problem solving.

Seed tale idea:
A tiny child or animal wants a prize that is hard to reach. The first try does
not work, so the hero thinks, notices the surroundings, and solves the problem
with a simple tool or helpful arrangement. The ending shows the clever change.
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
    held_by: Optional[str] = None
    reachable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
class Scene:
    place: str
    indoors: bool
    light: str
    challenge: str
    tool_kind: str
    tool_phrase: str
    prize_phrase: str
    prize_label: str
    obstacle: str
    solution_hint: str
    rhyme_tag: str
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
        self.lines: list[str] = []
        self.facts: dict = {}

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy

        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    prize: str
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


PLACES = {
    "nursery": Scene(
        place="the nursery",
        indoors=True,
        light="soft",
        challenge="reach a high shelf",
        tool_kind="stool",
        tool_phrase="a little wooden stool",
        prize_phrase="a shiny cookie",
        prize_label="cookie",
        obstacle="the shelf was too high for little hands",
        solution_hint="the stool could make a tiny step up",
        rhyme_tag="nursery",
    ),
    "kitchen": Scene(
        place="the kitchen",
        indoors=True,
        light="warm",
        challenge="reach the jam jar",
        tool_kind="ladder",
        tool_phrase="a small step ladder",
        prize_phrase="a sweet jam tart",
        prize_label="tart",
        obstacle="the jar sat on a high shelf",
        solution_hint="the ladder could lift the view a little",
        rhyme_tag="kitchen",
    ),
    "garden": Scene(
        place="the garden",
        indoors=False,
        light="bright",
        challenge="cross a little stream",
        tool_kind="plank",
        tool_phrase="a flat wooden plank",
        prize_phrase="a red toy boat",
        prize_label="boat",
        obstacle="the stream was too wide to hop across",
        solution_hint="the plank could bridge the water",
        rhyme_tag="garden",
    ),
}

HERO_NAMES = ["Milo", "Tilly", "Nia", "Pip", "Luna", "Robin", "Ollie", "Faye"]
HERO_TYPES = ["child", "mouse", "kitten", "bunny"]
HELPER_TYPES = ["mother", "father", "sister", "brother", "friend"]
PRIZES = {
    "cookie": "a shiny cookie",
    "tart": "a sweet jam tart",
    "boat": "a red toy boat",
}


@dataclass
class Tale:
    hero: Entity
    helper: Entity
    prize: Entity
    tool: Entity
    scene: Scene
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about intelligence and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper", choices=HELPER_TYPES)
    ap.add_argument("--prize", choices=PRIZES)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    scene = _safe_lookup(PLACES, place)
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if prize != scene.prize_label:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_TYPES)
    if helper == "mother" and hero_type == "mother":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, prize=prize)


def make_world(params: StoryParams) -> World:
    scene = _safe_lookup(PLACES, params.place)
    world = World(scene)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    prize = world.add(Entity(id="prize", kind="thing", type=params.prize, label=params.prize, phrase=_safe_lookup(PRIZES, params.prize), owner=hero.id))
    tool = world.add(Entity(id="tool", kind="thing", type=scene.tool_kind, label=scene.tool_kind, phrase=scene.tool_phrase))
    return world


def predict_solution(world: World) -> bool:
    return True


def tell_story(world: World) -> None:
    s = world.scene
    hero = world.get("hero")
    helper = world.get("helper")
    prize = world.get("prize")
    tool = world.get("tool")

    hero.memes["wonder"] = 1
    hero.memes["intelligence"] = 1
    world.say(f"In {s.place}, little {hero.label} was bright and spry, with a curious mind and a twinkle in the eye.")
    world.say(f"{hero.label} longed for {prize.phrase}, though {s.obstacle}.")
    world.say(f"{helper.label} said, 'Think first, dear one; look around and see.'")

    hero.meters["distance"] = 1
    world.say(f"{hero.label} tiptoed up, but the prize stayed out of reach.")
    hero.memes["frustration"] = 1
    world.say(f"Then {hero.label} sat very still, as quiet as could be, and used {hero.pronoun('possessive')} intelligence to plan carefully.")

    if s.tool_kind == "stool":
        tool.held_by = hero.id
        tool.reachable = True
        hero.meters["height"] = 1
        world.say(f"{hero.label} dragged over {s.tool_phrase}, and climbed with a careful little step.")
    elif s.tool_kind == "ladder":
        tool.held_by = hero.id
        tool.reachable = True
        hero.meters["height"] = 1
        world.say(f"{hero.label} set up {s.tool_phrase}, one rung, then two, and up went the brave little view.")
    else:
        tool.held_by = hero.id
        tool.reachable = True
        hero.meters["reach"] = 1
        world.say(f"{hero.label} laid down {s.tool_phrase}, and the tiny bridge made the way look neat and true.")

    prize.held_by = hero.id
    hero.memes["joy"] = 1
    hero.memes["intelligence"] = 2
    world.say(f"At last {hero.label} reached {prize.phrase}, and {helper.label} clapped in delight.")
    world.say(f"So {hero.label} was merry and wise, and the little world was tidy by and by.")

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        tool=tool,
        scene=s,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    scene = _safe_fact(world, f, "scene")
    return [
        f'Write a nursery-rhyme style story about intelligence in {scene.place}.',
        f"Tell a gentle tale where {hero.label} cannot reach {prize.phrase} at {scene.place}, then solves the problem with a simple tool.",
        f"Write a short rhyme where a small hero uses problem solving and a clever idea to get {prize.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prize = _safe_fact(world, f, "prize")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    scene = _safe_fact(world, f, "scene")
    return [
        QAItem(
            question=f"What problem did {hero.label} have in {scene.place}?",
            answer=f"{hero.label} could not reach {prize.phrase} because {scene.obstacle}.",
        ),
        QAItem(
            question=f"What did {hero.label} use to solve the problem?",
            answer=f"{hero.label} used {tool.phrase} as a clever helper for problem solving.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} reminded {hero.label} to think first and use intelligence instead of giving up.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, {hero.label} reached {prize.phrase} and felt proud and happy.",
        ),
    ]


KNOWLEDGE = {
    "intelligence": [
        (
            "What is intelligence?",
            "Intelligence is the ability to learn, notice things, and solve problems in a smart way.",
        )
    ],
    "problem solving": [
        (
            "What is problem solving?",
            "Problem solving means finding a way to fix a difficulty instead of staying stuck.",
        )
    ],
    "stool": [("What is a stool?", "A stool is a small seat or step that can help someone reach a little higher.")],
    "ladder": [("What is a ladder?", "A ladder is something with steps on it that helps you climb up higher.")],
    "plank": [("What is a plank?", "A plank is a long flat piece of wood that can help make a bridge or path.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["intelligence"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["problem solving"])
    tool = _safe_fact(world, world.facts, "tool")
    if tool.type in KNOWLEDGE:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tool.type])
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.reachable:
            bits.append("reachable=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
solved(Place, Prize) :- place(Place), prize(Prize), obstacle(Place), tool(Place), clever_solution(Place, Prize).
needed_tool(Place, Tool) :- place(Place), tool_kind(Place, Tool).
good_story(Place, Prize) :- solved(Place, Prize).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for place, scene in PLACES.items():
        lines.append(asp.fact("place", place))
        if scene.indoors:
            lines.append(asp.fact("indoors", place))
        lines.append(asp.fact("obstacle", place))
        lines.append(asp.fact("tool_kind", place, scene.tool_kind))
        lines.append(asp.fact("clever_solution", place, scene.prize_label))
        lines.append(asp.fact("prize", scene.prize_label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show good_story/2."))
    symbols = set(asp.atoms(model, "good_story"))
    expected = {(place, scene.prize_label) for place, scene in PLACES.items()}
    if symbols == expected:
        print(f"OK: ASP gate matches Python registry ({len(expected)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(symbols))
    print("PY :", sorted(expected))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
    StoryParams(place="nursery", hero="Milo", hero_type="child", helper="mother", prize="cookie"),
    StoryParams(place="kitchen", hero="Tilly", hero_type="mouse", helper="father", prize="tart"),
    StoryParams(place="garden", hero="Pip", hero_type="kitten", helper="friend", prize="boat"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show good_story/2."))
        items = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(items)} compatible stories:")
        for place, prize in items:
            print(f"  {place}: {prize}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
