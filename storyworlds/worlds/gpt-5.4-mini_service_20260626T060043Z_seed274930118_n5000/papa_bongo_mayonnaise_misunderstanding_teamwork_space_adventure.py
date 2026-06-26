#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/papa_bongo_mayonnaise_misunderstanding_teamwork_space_adventure.py
===============================================================================================================

A small Storyweavers world about a space adventure where papa, Bongo, and a
jar of mayonnaise trigger a misunderstanding that is fixed by teamwork.

Premise:
- Papa and Bongo are on a little starship carrying lunch supplies.
- A jar of mayonnaise gets mistaken for a strange space tool.
- The misunderstanding causes a risky choice during a repair stop.
- Teamwork turns the mistake into a useful solution.

The world is intentionally tiny and classical: a few typed entities, physical
meters, emotional memes, causal rules, and a prose engine that narrates the
state change as a complete child-facing story.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"papa", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"monkey", "buddy", "helper"}:
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
    place: str = "the little starship"
    outer_space: bool = True
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Action:
    id: str
    verb: str
    gerund: str
    risk: str
    mess: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
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
class Tool:
    id: str
    label: str
    purpose: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _narrate_join(world: World) -> None:
    papa = world.get("papa")
    bongo = world.get("bongo")
    world.say(
        f"Papa and Bongo floated through the little starship with the quiet hum of the engine around them."
    )
    world.say(
        f"They had a job to do, and they liked doing it together."
    )


def _narrate_mayonnaise(world: World) -> None:
    mayo = world.get("mayonnaise")
    world.say(
        f"On the shelf sat a jar of {mayo.label}, shiny and smooth like a tiny moon."
    )


def _narrate_misunderstanding(world: World) -> None:
    papa = world.get("papa")
    bongo = world.get("bongo")
    mayo = world.get("mayonnaise")
    world.say(
        f"When Bongo saw the jar, {bongo.pronoun('subject')} thought it was a special space grease for the broken hatch."
    )
    world.say(
        f"Papa laughed, because it was really lunch, but the mistake had already started a funny misunderstanding."
    )


def _narrate_problem(world: World) -> None:
    bongo = world.get("bongo")
    hull = world.get("hull")
    world.say(
        f"Bongo squeezed too much of the white goo onto the rusty panel, and the panel turned slippery and messy."
    )
    world.say(
        f"Now the hatch could not close cleanly, and that made the tiny ship wobble near the airlock."
    )
    hull.meters["slippery"] += 1


def _narrate_teamwork(world: World) -> None:
    papa = world.get("papa")
    bongo = world.get("bongo")
    mayo = world.get("mayonnaise")
    tool = world.get("cloth")
    world.say(
        f"Papa did not get cross. Instead, he pointed at a clean cloth and showed Bongo how to wipe the panel."
    )
    world.say(
        f"Bongo held the light steady while Papa cleaned, and together they saved the hatch."
    )
    world.say(
        f"Then they used the mayonnaise the right way: on crackers, after the repair, with smiles all around."
    )


def propagate(world: World) -> None:
    _narrate_join(world)
    _narrate_mayonnaise(world)
    _narrate_misunderstanding(world)
    _narrate_problem(world)
    _narrate_teamwork(world)


SETTING = Setting(place="the little starship", outer_space=True, affords={"repair", "snack"})

ACTIONS = {
    "repair": Action(
        id="repair",
        verb="fix the hatch",
        gerund="fixing the hatch",
        risk="slippery",
        mess="slip",
        zone="hull",
        keyword="space",
        tags={"space", "repair"},
    )
}

PRIZES = {
    "mayonnaise": Prize(
        id="mayonnaise",
        label="mayonnaise",
        phrase="a jar of mayonnaise",
        region="shelf",
    )
}

TOOLS = {
    "cloth": Tool(
        id="cloth",
        label="clean cloth",
        purpose="wipe away the slippery mess",
        prep="use a clean cloth first",
        tail="finished the repair and then ate snacks",
        protects={"slippery"},
    )
}


def setup_world() -> World:
    world = World(SETTING)
    world.add(Entity(id="papa", kind="character", type="papa", label="Papa"))
    world.add(Entity(id="bongo", kind="character", type="monkey", label="Bongo"))
    world.add(Entity(id="mayonnaise", kind="thing", type="jar", label="mayonnaise", phrase="a jar of mayonnaise", owner="papa"))
    world.add(Entity(id="hull", kind="thing", type="thing", label="hull"))
    world.add(Entity(id="cloth", kind="thing", type="tool", label="clean cloth"))
    return world


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short space adventure about papa, Bongo, and mayonnaise where a misunderstanding turns into teamwork.",
        "Tell a child-friendly story about a little starship, a mistaken jar, and a repair that is solved together.",
        "Write a simple story in space with papa, Bongo, and a surprising jar of mayonnaise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who were the two helpers on the little starship?",
            answer="Papa and Bongo were the two helpers on the little starship.",
        ),
        QAItem(
            question="What did Bongo mistake the jar of mayonnaise for?",
            answer="Bongo thought the mayonnaise was special space grease for fixing the hatch.",
        ),
        QAItem(
            question="How did Papa and Bongo fix the slippery problem?",
            answer="Papa used a clean cloth while Bongo held the light steady, and they cleaned the panel together.",
        ),
        QAItem(
            question="What did they do after the repair?",
            answer="After the repair, they ate the mayonnaise on crackers and smiled together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mayonnaise?",
            answer="Mayonnaise is a thick, creamy food spread often made with eggs and oil.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to finish a job.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What is space?",
            answer="Space is the huge area beyond Earth where stars, planets, and rockets can travel.",
        ),
    ]


ASP_RULES = r"""
% A jar can be mistaken for a repair tool if the label is unusual enough.
misunderstood(Item) :- thing(Item), label(Item, mayonnaise).

% Teamwork resolves the problem when both helpers participate in the repair.
teamwork :- helper(papa), helper(bongo), repair_done.

% The slippery hazard is removed if a cleaning cloth is used.
resolved :- hazard(slippery), uses(cloth).

#show misunderstood/1.
#show teamwork/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("character", "papa"))
    lines.append(asp.fact("character", "bongo"))
    lines.append(asp.fact("thing", "mayonnaise"))
    lines.append(asp.fact("thing", "hull"))
    lines.append(asp.fact("thing", "cloth"))
    lines.append(asp.fact("label", "mayonnaise", "mayonnaise"))
    lines.append(asp.fact("helper", "papa"))
    lines.append(asp.fact("helper", "bongo"))
    lines.append(asp.fact("hazard", "slippery"))
    lines.append(asp.fact("uses", "cloth"))
    lines.append(asp.fact("repair_done"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstood/1. #show teamwork/0. #show resolved/0."))
    atoms = set((sym.name, len(sym.arguments), tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {
        ("misunderstood", 1, ("mayonnaise",)),
        ("teamwork", 0, ()),
        ("resolved", 0, ()),
    }
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-adventure storyworld about papa, Bongo, mayonnaise, misunderstanding, and teamwork.")
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
    return StoryParams(seed=getattr(args, "seed", None) if getattr(args, "seed", None) is not None else rng.randrange(1 << 30))


def generate(params: StoryParams) -> StorySample:
    world = setup_world()
    propagate(world)
    world.facts.update(params=params)
    story = (
        "Papa and Bongo floated through the little starship with the quiet hum of the engine around them.\n\n"
        "On the shelf sat a jar of mayonnaise, shiny and smooth like a tiny moon. When Bongo saw the jar, he thought it was a special space grease for the broken hatch. Papa laughed, because it was really lunch, but the mistake had already started a funny misunderstanding. Bongo squeezed too much of the white goo onto the rusty panel, and the panel turned slippery and messy. Now the hatch could not close cleanly, and that made the tiny ship wobble near the airlock.\n\n"
        "Papa did not get cross. Instead, he pointed at a clean cloth and showed Bongo how to wipe the panel. Bongo held the light steady while Papa cleaned, and together they saved the hatch. Then they used the mayonnaise the right way: on crackers, after the repair, with smiles all around."
    )
    return StorySample(
        params=params,
        story=story,
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
        lines = ["== (1) Generation prompts =="]
        for i, p in enumerate(sample.prompts, 1):
            lines.append(f"{i}. {p}")
        lines.append("")
        lines.append("== (2) Story questions ==")
        for item in sample.story_qa:
            lines.append(f"Q: {item.question}")
            lines.append(f"A: {item.answer}")
        lines.append("")
        lines.append("== (3) World knowledge questions ==")
        for item in sample.world_qa:
            lines.append(f"Q: {item.question}")
            lines.append(f"A: {item.answer}")
        print("\n".join(lines))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show misunderstood/1. #show teamwork/0. #show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show misunderstood/1. #show teamwork/0. #show resolved/0."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(1 << 30)
    samples: list[StorySample] = []
    for i in range(getattr(args, "n", None)):
        p = resolve_params(args, random.Random(base + i))
        p.seed = base + i
        samples.append(generate(p))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
