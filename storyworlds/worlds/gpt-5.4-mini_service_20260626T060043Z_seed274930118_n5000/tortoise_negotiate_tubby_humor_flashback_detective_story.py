#!/usr/bin/env python3
"""
Standalone storyworld: tortoise detective negotiates a clue, with humor and a
flashback. The story is child-facing, state-driven, and built from a small
simulation.

Seed premise:
- A tortoise detective must negotiate over a tubby little clue-holder.
- A flashback explains why the clue matters.
- The story resolves with a clever, funny compromise.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memory: list[str] = field(default_factory=list)

    clue: object | None = None
    detective: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"tortoise"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"cat", "mouse", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the lamp-lit pier"
    weather: str = "foggy"
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
class Clue:
    id: str
    label: str
    phrase: str
    weight: float
    funny: str
    flashback_trigger: str
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
    place: str = "pier"
    clue: str = "cookie_tin"
    detective_name: str = "Toby"
    suspect_name: str = "Mina"
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
        self.fired: set[tuple] = set()
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get(world.facts["detective"])
    clue = world.get(world.facts["clue"])
    if detective.memes.get("bemused", 0.0) >= THRESHOLD and ("humor", clue.id) not in world.fired:
        world.fired.add(("humor", clue.id))
        clue.memes["comic_weight"] = clue.memes.get("comic_weight", 0.0) + 1
        out.append(f"The clue looked so silly that even the detective snorted a tiny laugh.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get(world.facts["detective"])
    clue = world.get(world.facts["clue"])
    if detective.memes.get("memory_tick", 0.0) >= THRESHOLD and ("flashback", clue.id) not in world.fired:
        world.fired.add(("flashback", clue.id))
        detective.memory.append(clue.flashback_trigger)
        detective.memes["certainty"] = detective.memes.get("certainty", 0.0) + 1
        out.append("He remembered the old night when the clue had first gone missing.")
    return out


def _r_negotiate(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get(world.facts["detective"])
    suspect = world.get(world.facts["suspect"])
    clue = world.get(world.facts["clue"])
    if detective.memes.get("ask", 0.0) >= THRESHOLD and suspect.memes.get("wary", 0.0) >= THRESHOLD:
        sig = ("negotiate", detective.id, suspect.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["calm"] = detective.memes.get("calm", 0.0) + 1
            suspect.memes["trust"] = suspect.memes.get("trust", 0.0) + 1
            out.append(f"The tortoise detective spoke gently, and the tubby suspect listened.")
    return out


CAUSAL_RULES = [_r_humor, _r_flashback, _r_negotiate]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_setting(place: str) -> Setting:
    return Setting(place=f"the {place}", weather="foggy", affords={"questioning", "negotiation"})


CLUES = {
    "cookie_tin": Clue(
        id="cookie_tin",
        label="a tin of cookies",
        phrase="a round tin of cookies with a crooked lid",
        weight=2.0,
        funny="It gave a cheerful clink-clink whenever it rolled.",
        flashback_trigger="the smell of cinnamon cookies",
    ),
    "balloon": Clue(
        id="balloon",
        label="a squeaky balloon",
        phrase="a shiny balloon tied to a tiny string",
        weight=0.5,
        funny="It kept wiggling like it had a secret joke.",
        flashback_trigger="the bright pop of a party",
    ),
    "pie": Clue(
        id="pie",
        label="a pie plate",
        phrase="a pie plate with one lonely crumb",
        weight=1.5,
        funny="It was so flat and serious that it looked offended.",
        flashback_trigger="a kitchen window full of warm light",
    ),
}

PLACES = ["pier", "alley", "museum", "garden"]
NAMES = ["Toby", "Tessa", "Theo", "Milo", "Mina", "Pip"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            combos.append((place, clue))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("funny_clue", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Clue) :- place(Place), clue(Clue).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tortoise detective negotiates a clue with humor and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=tuple(CLUES))
    ap.add_argument("--name")
    ap.add_argument("--suspect")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue = rng.choice(list(combos))
    return StoryParams(
        place=place,
        clue=clue,
        detective_name=getattr(args, "name", None) or rng.choice(NAMES),
        suspect_name=getattr(args, "suspect", None) or rng.choice([n for n in NAMES if n != getattr(args, "name", None)]),
    )


def tell(params: StoryParams) -> World:
    world = World(build_setting(params.place))
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type="tortoise",
        label="tortoise detective",
        traits=["patient", "clever", "tubby"],
        memes={"bemused": 0.0, "memory_tick": 0.0, "ask": 0.0},
    ))
    suspect = world.add(Entity(
        id=params.suspect_name,
        kind="character",
        type="child",
        label="tubby suspect",
        traits=["wary", "tubby"],
        memes={"wary": 0.0, "trust": 0.0},
    ))
    clue = world.add(Entity(
        id=params.clue,
        kind="thing",
        type="clue",
        label=_safe_lookup(CLUES, params.clue).label,
        phrase=_safe_lookup(CLUES, params.clue).phrase,
        memes={"comic_weight": 0.0},
    ))
    world.facts = {"detective": detective.id, "suspect": suspect.id, "clue": clue.id}

    world.say(f"{detective.label.capitalize()} Toby worked the foggy pier like a real detective.")
    world.say(f"He found {clue.phrase}. {_safe_lookup(CLUES, params.clue).funny}")
    detective.memes["bemused"] += 1
    detective.memes["memory_tick"] += 1
    propagate(world)

    world.para()
    world.say(f"A tubby little suspect named {suspect.id} stood nearby and hugged {clue.pronoun('possessive')} pockets.")
    suspect.memes["wary"] += 1
    detective.memes["ask"] += 1
    world.say(f"Toby wanted to ask questions, but the clue made the case feel bigger than it looked.")
    propagate(world)

    world.para()
    world.say("Then came a flashback.")
    world.say(f"Toby remembered {clue.flashback_trigger}, and that was why the clue mattered so much.")
    world.say(f'He said, "Let us negotiate."')
    world.say(f'"You keep the clue dry," Toby told the suspect, "and I will tell everyone your honest part in the story."')
    propagate(world)

    world.para()
    detective.memes["ask"] += 1
    suspect.memes["wary"] += 1
    suspect.memes["trust"] += 1
    world.say(f"The suspect blinked, then nodded. That was a funny deal, but it was fair.")
    world.say(f"Toby got the clue back, the suspect got credit, and the foggy pier felt lighter at the end.")
    world.say(f"The tortoise detective tucked the tin away and waddled home, pleased that the mystery had turned into a grin.")

    world.facts.update(params=params, clue_obj=clue)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a short detective story about a tortoise named {p.detective_name} who must negotiate over {_safe_lookup(CLUES, p.clue).label}.",
        f"Tell a funny story with a flashback on {world.setting.place} where a tubby suspect helps solve a case.",
        f"Write a child-friendly mystery that includes a tortoise, negotiation, humor, and a memory from the past.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    clue = _safe_lookup(CLUES, p.clue)
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {p.detective_name}, a tortoise who worked the case patiently.",
        ),
        QAItem(
            question=f"What did Toby have to negotiate about?",
            answer=f"He had to negotiate about {clue.label} on {world.setting.place}. The clue was funny-looking, but it still mattered.",
        ),
        QAItem(
            question=f"Why was there a flashback?",
            answer=f"There was a flashback because Toby remembered {clue.flashback_trigger}, and that helped him understand why the clue mattered.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a fair deal: Toby got the clue back, the suspect got credit, and the mystery turned into a happy, funny ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    clue = CLUES[world.facts["params"].clue]
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to figure out what happened.",
        ),
        QAItem(
            question="What is negotiation?",
            answer="Negotiation is when people talk calmly and try to make a fair agreement that works for everyone.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that shows or remembers something that happened earlier.",
        ),
        QAItem(
            question=f"Why can {clue.label} be funny in a story?",
            answer=f"It can be funny because {clue.funny.lower()} That kind of detail makes the mystery feel playful.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id}: type={e.type} meters={meters} memes={memes} memory={e.memory}")
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="pier", clue="cookie_tin", detective_name="Toby", suspect_name="Mina"),
    StoryParams(place="museum", clue="pie", detective_name="Tessa", suspect_name="Pip"),
    StoryParams(place="garden", clue="balloon", detective_name="Theo", suspect_name="Milo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
