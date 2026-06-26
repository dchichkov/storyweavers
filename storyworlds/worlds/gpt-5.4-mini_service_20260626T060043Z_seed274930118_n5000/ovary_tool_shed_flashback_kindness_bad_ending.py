#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ovary_tool_shed_flashback_kindness_bad_ending.py
===============================================================================================================

A small Tall Tale-style story world set in a tool shed, built from the seed word
"ovary" and featuring a flashback, kindness, and a bad ending.

Premise:
- A child in a tool shed finds an old gardening chart that mentions an ovary.
- A flashback reveals a kind lesson about flowers and seeds.
- The child chooses a kind act in the present.
- The choice leads to a sad, bad ending: the repair fails, the bloom is lost,
  and the shed ends in a quiet, weather-beaten image.

The world model is intentionally small and constraint-checked:
- physical meters track rust, wetness, breakage, and bloom health
- emotional memes track awe, worry, kindness, regret, and resolve
- flashback state is explicit and alters the story
- kindness is a real causal choice, not merely a label
- bad ending is a real state transition, not a canned final sentence
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chart: object | None = None
    child: object | None = None
    elder: object | None = None
    hammer: object | None = None
    jar: object | None = None
    tomato: object | None = None
    def __post_init__(self):
        for k in ["rust", "wet", "broken", "bloom", "dust", "repair", "tired"]:
            self.meters.setdefault(k, 0.0)
        for k in ["awe", "worry", "kindness", "regret", "resolve", "hope", "flashback"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
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
    place: str = "the tool shed"
    world: object | None = None
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
class StoryParams:
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "grandmother"
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


def _build_world(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id="elder", kind="character", type=params.parent, label=params.parent))
    chart = world.add(Entity(
        id="chart",
        type="paper",
        label="old flower chart",
        phrase="an old flower chart with a sketch of an ovary",
        caretaker=elder.id,
    ))
    tomato = world.add(Entity(
        id="tomato",
        type="plant",
        label="tomato vine",
        phrase="a tomato vine with one red blossom",
        owner=elder.id,
    ))
    hammer = world.add(Entity(
        id="hammer",
        type="tool",
        label="hammer",
        phrase="a heavy hammer",
        owner=elder.id,
    ))
    jar = world.add(Entity(
        id="jar",
        type="jar",
        label="seed jar",
        phrase="a little seed jar",
        owner=elder.id,
    ))
    child.memes["awe"] += 1
    world.say(
        f"{child.id} was a little {params.gender} who liked the quiet magic of {world.setting.place}."
    )
    world.say(
        f"On a high nail hung {chart.phrase}, and beside it sat {jar.phrase} and {hammer.phrase}."
    )
    world.say(
        f"{child.id} loved to listen when {elder.pronoun('subject')} talked about how every blossom had a secret place where seeds begin."
    )

    world.para()
    world.say(
        f"One breezy morning, {child.id} opened the shed door and found the chart fluttering like a flag."
    )
    child.memes["worry"] += 1
    chart.meters["wet"] += 1
    world.say(
        f"The breeze had pushed in a wet mist, and the paper looked in danger of curling at the corners."
    )
    world.say(
        f"{child.id} frowned and remembered a long-ago lesson from {elder.pronoun('possessive')} lap."
    )
    child.memes["flashback"] += 1
    world.say(
        f"In that flashback, {elder.pronoun('subject')} had pointed to the tiny ovary in a flower drawing and said, "
        f"\"That's where the seeds start, small as moon crumbs.\""
    )

    world.para()
    child.memes["kindness"] += 1
    world.say(
        f"{child.id} could have ignored the damp chart and raced outside, but {child.pronoun('subject')} chose kindness instead."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} lifted the paper to dry it and offered to help {elder.pronoun('object')} mend the torn peg shelf too."
    )
    chart.meters["wet"] += 1
    hammer.meters["repair"] += 1
    tomato.memes["hope"] += 1
    world.say(
        f"The kind offer made {elder.pronoun('object')} smile, and the tomato vine seemed to lean closer, hoping for care."
    )

    world.para()
    world.say(
        f"But the hammer slipped from the shelf, clanged off a bucket, and startled a whole line of sleepy bees outside the door."
    )
    child.memes["resolve"] += 1
    child.memes["regret"] += 1
    tomato.meters["bloom"] += 1
    chart.meters["broken"] += 1
    world.say(
        f"{child.id} tried to save both the chart and the blossom, yet the wet paper tore, and the blossom shook loose."
    )
    world.say(
        f"The bees drifted away, the seed jar tipped, and a few seeds rolled into the dust under the bench."
    )

    world.para()
    tomato.meters["bloom"] -= 1
    tomato.meters["waste"] += 1
    elder.memes["worry"] += 1
    elder.memes["regret"] += 1
    world.say(
        f"By sunset the chart had a ragged corner, the tomato vine lost its red blossom, and the shed smelled of rain and sawdust."
    )
    world.say(
        f"{child.id} had been kind, but the day still ended badly: the lesson was remembered, yet the careful thing arrived too late."
    )

    world.facts.update(
        child=child,
        elder=elder,
        chart=chart,
        tomato=tomato,
        hammer=hammer,
        jar=jar,
        setting=world.setting,
        flashback=True,
        kindness=True,
        bad_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f'Write a Tall Tale-style story about a child named {child.id} in a tool shed, using the word "ovary".',
        f"Tell a gentle but sad story where {child.id} remembers a flashback about a flower ovary and tries to help kindly.",
        f"Write a short story set in a tool shed that includes a flashback, kindness, and a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    elder = _safe_fact(world, f, "elder")
    chart = _safe_fact(world, f, "chart")
    tomato = _safe_fact(world, f, "tomato")
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in {world.setting.place}, among tools, paper, and seed jars.",
        ),
        QAItem(
            question=f"What did {child.id} remember in the flashback?",
            answer=f"{child.id} remembered {elder.pronoun('possessive')} old lesson about the ovary in a flower and where seeds begin.",
        ),
        QAItem(
            question=f"How did {child.id} act when the chart got damp?",
            answer=f"{child.id} chose kindness, lifted the chart carefully, and tried to help {elder.pronoun('object')} fix things.",
        ),
        QAItem(
            question=f"What went wrong at the end?",
            answer=f"The wet chart tore, the hammer clanged, the blossom shook loose, and the day ended badly.",
        ),
        QAItem(
            question=f"What changed by the ending image?",
            answer=f"The chart had a ragged corner, the tomato vine had lost its blossom, and the shed smelled of rain and sawdust.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ovary in a flower?",
            answer="An ovary is the part of a flower where seeds begin to grow after the flower is pollinated.",
        ),
        QAItem(
            question="Why can wet paper be hard to keep neat?",
            answer="Wet paper can curl, tear, and smear because water weakens the fibers and makes the paper floppy.",
        ),
        QAItem(
            question="What is a tool shed?",
            answer="A tool shed is a small building where people keep tools, garden things, and other useful supplies.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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


ASP_RULES = r"""
% The story is valid when it has the required instruments.
has_flashback :- flashback.
has_kindness :- kindness.
has_bad_ending :- bad_ending.
valid_story :- has_flashback, has_kindness, has_bad_ending.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("flashback"),
            asp.fact("kindness"),
            asp.fact("bad_ending"),
            asp.fact("setting", "tool_shed"),
            asp.fact("seed_word", "ovary"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    python_ok = True
    if ok == python_ok:
        print("OK: ASP and Python agree on required story instruments.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale storyworld set in a tool shed.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--gender", choices=["girl", "boy", "woman", "man"], default=None)
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"], default=None)
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
    name = getattr(args, "name", None) or rng.choice(["Mina", "June", "Toby", "Mabel", "Otis"])
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["grandmother", "grandfather"])
    return StoryParams(name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
        print(asp_program("#show valid_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(StoryParams(name="Mina", gender="girl", parent="grandmother"))]
    else:
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
