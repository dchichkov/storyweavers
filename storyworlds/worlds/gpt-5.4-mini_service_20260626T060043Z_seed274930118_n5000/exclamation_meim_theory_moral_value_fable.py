#!/usr/bin/env python3
"""
A standalone storyworld script for a tiny fable-like domain about
exclamation, meim, theory, and moral value.

The world is a small meadow where one animal wants a shiny meim, another
animal offers a thoughtful theory, and the ending shows that the kinder path
is worth more than a loud exclamation.
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


MORAL_VALUES = ["kindness", "honesty", "patience", "fairness", "sharing"]
PLACES = ["meadow", "pond", "oak tree", "lantern path"]
CHARACTER_KINDS = ["mouse", "sparrow", "rabbit", "turtle", "fox", "badger"]
NAMES = {
    "mouse": ["Milo", "Nina", "Pip"],
    "sparrow": ["Skye", "Lark", "Bea"],
    "rabbit": ["Tilly", "Harey", "Moss"],
    "turtle": ["Toma", "Shelly", "Dawn"],
    "fox": ["Finn", "Vera", "Rook"],
    "badger": ["Bram", "Dot", "Wren"],
}



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
    carries: Optional[str] = None
    traded_for: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    challenger: object | None = None
    claimant: object | None = None
    meim: object | None = None
    def __post_init__(self) -> None:
        for k in ["value", "need", "noise", "trust", "pride", "gladness"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

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
    place: str
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
class Claim:
    id: str
    label: str
    phrase: str
    value: str
    reason: str
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
    claimant: str
    challenger: str
    value: str
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
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _moral_gain(world: World, actor: Entity, amount: float, kind: str) -> None:
    actor.memes[kind] += amount
    actor.meters["value"] += amount


def _noise_after_exclamation(world: World, speaker: Entity) -> None:
    if speaker.meters["noise"] < 1:
        return
    sig = ("noise", speaker.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    speaker.memes["pride"] += 1
    world.say(f"Their loud exclamation echoed over the grass, but it did not make the meim any more theirs.")


def _trust_after_honesty(world: World, speaker: Entity, listener: Entity) -> None:
    if speaker.memes["trust"] < 1:
        return
    sig = ("trust", speaker.id, listener.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    listener.memes["trust"] += 1
    world.say(f"That careful thought made {listener.label} trust {speaker.label} a little more.")


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for e in list(world.entities.values()):
            before = (e.memes["trust"], e.memes["pride"])
            _noise_after_exclamation(world, e)
            after = (e.memes["trust"], e.memes["pride"])
            if after != before:
                changed = True


def choose_name(kind: str, rng: random.Random) -> str:
    return rng.choice(_safe_lookup(NAMES, kind))


def tell(setting: Setting, claimant_kind: str, challenger_kind: str, value: str,
         claimant_name: Optional[str] = None, challenger_name: Optional[str] = None) -> World:
    world = World(setting)

    claimant_name = claimant_name or choose_name(claimant_kind, random.Random())
    challenger_name = challenger_name or choose_name(challenger_kind, random.Random())

    claimant = world.add(Entity(
        id=claimant_name, kind="character", type=claimant_kind, label=claimant_name,
    ))
    challenger = world.add(Entity(
        id=challenger_name, kind="character", type=challenger_kind, label=challenger_name,
    ))
    meim = world.add(Entity(
        id="meim", kind="thing", type="meim", label="meim",
        phrase=f"a bright {value} meim", owner=challenger.id,
    ))
    claimant.traded_for = meim.id

    world.say(
        f"Once in the {setting.place}, {claimant.label} and {challenger.label} found "
        f"{meim.phrase} under a leaf."
    )
    _moral_gain(world, claimant, 1, "need")
    claimant.memes["trust"] += 1
    world.say(
        f"{claimant.label} wanted it at once, because the little meim looked too fine to leave behind."
    )

    world.para()
    world.say(
        f"Then {challenger.label} raised a sharp exclamation and said, "
        f"“That meim is mine!”"
    )
    challenger.meters["noise"] += 1
    challenger.memes["pride"] += 1
    propagate(world)

    world.say(
        f"{claimant.label} had a quick theory: maybe the loudest voice should decide."
    )
    claimant.memes["pride"] += 1
    claimant.meters["noise"] += 1
    propagate(world)

    world.para()
    world.say(
        f"But an old turtle nearby asked a better question: “Who can explain how the meim was lost?”"
    )
    claimant.memes["trust"] += 1
    challenger.memes["trust"] += 1
    world.say(
        f"Both animals looked again, and they noticed the meim had been caught in the roots all along."
    )

    world.para()
    world.say(
        f"{claimant.label} gently pulled it free and gave it back with a small smile."
    )
    challenger.owner = challenger.id
    claimant.memes["trust"] += 1
    challenger.memes["gladness"] += 1
    claimant.memes["gladness"] += 1
    _moral_gain(world, claimant, 2, value)
    _moral_gain(world, challenger, 1, value)
    world.say(
        f"{challenger.label} lowered the loud voice and said thank you. "
        f"The meim shone all the brighter when it was shared with honesty."
    )

    world.facts.update(
        setting=setting,
        claimant=claimant,
        challenger=challenger,
        meim=meim,
        value=value,
    )
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"find", "speak"}),
    "pond": Setting(place="the pond", affords={"find", "speak"}),
    "oak": Setting(place="the oak tree", affords={"find", "speak"}),
    "path": Setting(place="the lantern path", affords={"find", "speak"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for claimant in CHARACTER_KINDS:
            for challenger in CHARACTER_KINDS:
                if claimant != challenger:
                    for value in MORAL_VALUES:
                        out.append((place, claimant, challenger, value))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-like storyworld.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--claimant", choices=CHARACTER_KINDS)
    ap.add_argument("--challenger", choices=CHARACTER_KINDS)
    ap.add_argument("--value", choices=MORAL_VALUES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    claimant = getattr(args, "claimant", None) or rng.choice(CHARACTER_KINDS)
    challenger = getattr(args, "challenger", None) or rng.choice([k for k in CHARACTER_KINDS if k != claimant])
    value = getattr(args, "value", None) or rng.choice(MORAL_VALUES)
    return StoryParams(place=place, claimant=claimant, challenger=challenger, value=value)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable about a {f['claimant'].type} and a {f['challenger'].type} in {f['setting'].place} involving a meim and a moral lesson.",
        f"Tell a child-friendly story where an exclamation causes trouble, but a theory and a kind choice resolve it.",
        f"Write a simple moral tale about {f['value']} in which a meim is returned instead of fought over.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = _safe_fact(world, f, "claimant")
    ch = _safe_fact(world, f, "challenger")
    value = _safe_fact(world, f, "value")
    return [
        QAItem(
            question=f"Who found the meim in {f['setting'].place}?",
            answer=f"{c.label} and {ch.label} found it together, but they did not agree at first about who should keep it.",
        ),
        QAItem(
            question=f"What did {ch.label} say when the meim was discovered?",
            answer=f"{ch.label} made a loud exclamation and claimed the meim as their own.",
        ),
        QAItem(
            question=f"What lesson did the story show about {value}?",
            answer=f"It showed that {value} matters more than winning an argument, and that honesty can turn a fight into peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an exclamation?",
            answer="An exclamation is a loud or excited word or sentence, often used when someone is surprised.",
        ),
        QAItem(
            question="What is a theory?",
            answer="A theory is an idea about how something might work or what might be true.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of acting, such as kindness, honesty, or fairness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
value_story(P,C,H,V) :- place(P), claimant(C), challenger(H), moral(V), C != H.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for k in CHARACTER_KINDS:
        lines.append(asp.fact("claimant", k))
        lines.append(asp.fact("challenger", k))
    for v in MORAL_VALUES:
        lines.append(asp.fact("moral", v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.claimant, params.challenger, params.value)
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
    StoryParams(place="meadow", claimant="mouse", challenger="fox", value="honesty"),
    StoryParams(place="pond", claimant="sparrow", challenger="turtle", value="patience"),
    StoryParams(place="oak", claimant="rabbit", challenger="badger", value="fairness"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show value_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            samples.append(generate(p))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
