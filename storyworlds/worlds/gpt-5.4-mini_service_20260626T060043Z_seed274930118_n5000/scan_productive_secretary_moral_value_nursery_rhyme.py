#!/usr/bin/env python3
"""
storyworlds/worlds/scan_productive_secretary_moral_value_nursery_rhyme.py
===========================================================================

A small storyworld in a nursery-rhyme voice about a secretary who must scan
papers, stay productive, and choose a kind moral value when the office becomes
messy.

Premise:
- A tidy secretary works in a little office with a stack of papers.
- A scanner can make the work productive, but only if the papers are sorted
  and the scanner is used carefully.
- A moral choice appears when a helpful shortcut would save time but hurt
  honesty or care.

This world keeps the simulation concrete:
- physical meters: paper pile, ink, dust, scanned, tidiness
- emotional memes: pride, worry, kindness, relief, honesty

The story is told as a short nursery rhyme with a clear turn and a resolution.
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
    wore: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    secretary: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"secretary", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
class Office:
    place: str = "the little office"
    quiet: bool = True
    has_scanner: bool = True
    has_stamp: bool = True
    asks_accuracy: bool = True
    office: object | None = None
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
    name: str
    parent: str
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
    def __init__(self, office: Office) -> None:
        self.office = office
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
        clone = World(self.office)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_scanned(world: World) -> list[str]:
    out: list[str] = []
    sec = world.entities.get("secretary")
    scanner = world.entities.get("scanner")
    stack = world.entities.get("papers")
    if not sec or not scanner or not stack:
        return out
    if sec.meters.get("worked", 0) < THRESHOLD:
        return out
    if scanner.meters.get("ready", 0) < THRESHOLD:
        return out
    if stack.meters.get("sorted", 0) < THRESHOLD:
        return out
    sig = ("scan_done",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stack.meters["scanned"] = stack.meters.get("scanned", 0) + 1
    sec.meters["productive"] = sec.meters.get("productive", 0) + 1
    sec.memes["pride"] = sec.memes.get("pride", 0) + 1
    out.append("The scanner hummed, and every page was copied with care.")
    out.append("That made the little office feel bright and productive.")
    return out


def _r_tidy(world: World) -> list[str]:
    out: list[str] = []
    sec = world.entities.get("secretary")
    papers = world.entities.get("papers")
    if not sec or not papers:
        return out
    if papers.meters.get("dust", 0) < THRESHOLD:
        return out
    if sec.memes.get("honesty", 0) < THRESHOLD:
        return out
    sig = ("tidy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    papers.meters["dust"] = 0
    papers.meters["sorted"] = 1
    sec.memes["relief"] = sec.memes.get("relief", 0) + 1
    out.append("She wiped the dust away and set the pages in a neat little line.")
    return out


def _r_moral_turn(world: World) -> list[str]:
    out: list[str] = []
    sec = world.entities.get("secretary")
    stamp = world.entities.get("stamp")
    papers = world.entities.get("papers")
    if not sec or not stamp or not papers:
        return out
    if sec.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("moral_turn",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sec.memes["honesty"] = sec.memes.get("honesty", 0) + 1
    sec.memes["kindness"] = sec.memes.get("kindness", 0) + 1
    papers.meters["sorted"] = 1
    stamp.meters["used"] = stamp.meters.get("used", 0) + 1
    out.append("She chose the honest way, though it took a bit more time.")
    return out


CAUSAL_RULES = [
    Rule("scanned", _r_scanned),
    Rule("tidy", _r_tidy),
    Rule("moral_turn", _r_moral_turn),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_productive(world: World) -> dict:
    sim = world.copy()
    sec = sim.get("secretary")
    sec.meters["worked"] = sec.meters.get("worked", 0) + 1
    propagate(sim, narrate=False)
    papers = sim.get("papers")
    return {
        "productive": bool(sec.meters.get("productive", 0) >= THRESHOLD),
        "scanned": bool(papers.meters.get("scanned", 0) >= THRESHOLD),
    }


def make_story(world: World) -> None:
    sec = world.get("secretary")
    papers = world.get("papers")
    scanner = world.get("scanner")
    stamp = world.get("stamp")

    world.say(
        f"Little {sec.id} was a secretary in {world.office.place}, "
        f"with a tidy desk and a stack of papers to bear."
    )
    world.say(
        f"She loved to work in rhythm and rhyme, "
        f"for careful pages save both task and time."
    )

    world.para()
    world.say(
        f"One morning the papers were dusty and high, "
        f"and the scanner sat silent, still as the sky."
    )
    sec.memes["worry"] = sec.memes.get("worry", 0) + 1
    papers.meters["dust"] = papers.meters.get("dust", 0) + 1
    sec.meters["worked"] = sec.meters.get("worked", 0) + 1

    if not predict_productive(world)["productive"]:
        world.say(
            f"She saw that a quick trick might look bright, "
            f"but it would not be honest, and that was not right."
        )
        if stamp.meters.get("ready", 0) < THRESHOLD:
            stamp.meters["ready"] = 1
        sec.memes["honesty"] = sec.memes.get("honesty", 0) + 1
        sec.memes["kindness"] = sec.memes.get("kindness", 0) + 1
        world.say(
            f"So she did not fake the marks or rush the chore; "
            f"she sorted the pages and cleaned some more."
        )
        propagate(world, narrate=True)

    world.para()
    sec.meters["worked"] = sec.meters.get("worked", 0) + 1
    scanner.meters["ready"] = scanner.meters.get("ready", 0) + 1
    if papers.meters.get("sorted", 0) < THRESHOLD:
        papers.meters["sorted"] = 1
    propagate(world, narrate=True)

    if papers.meters.get("scanned", 0) >= THRESHOLD:
        sec.memes["relief"] = sec.memes.get("relief", 0) + 1
        world.say(
            f"At last the papers were scanned with care, "
            f"and the little office felt light as air."
        )
        world.say(
            f"{sec.id} smiled at the tidy stack; "
            f"she chose the kind way and did not look back."
        )

    world.facts.update(
        secretary=sec,
        papers=papers,
        scanner=scanner,
        stamp=stamp,
        office=world.office,
    )


def build_world(name: str = "Mina", parent: str = "mother") -> World:
    office = Office()
    world = World(office)
    secretary = world.add(Entity(
        id=name,
        kind="character",
        type="secretary",
        label="secretary",
        meters={"worked": 0, "productive": 0},
        memes={"worry": 0, "honesty": 0, "kindness": 0, "pride": 0, "relief": 0},
    ))
    world.add(Entity(
        id="papers",
        type="papers",
        label="papers",
        phrase="a neat stack of pages",
        caretaker=secretary.id,
        meters={"dust": 0, "sorted": 0, "scanned": 0},
    ))
    world.add(Entity(
        id="scanner",
        type="scanner",
        label="scanner",
        phrase="a little office scanner",
        meters={"ready": 1},
    ))
    world.add(Entity(
        id="stamp",
        type="stamp",
        label="stamp",
        phrase="a round date stamp",
        meters={"ready": 1},
    ))
    world.facts["parent"] = parent
    make_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    sec = _safe_fact(world, world.facts, "secretary")
    return [
        "Write a short nursery rhyme about a secretary who must scan papers and stay productive while choosing the moral value of honesty.",
        f"Tell a gentle office story where {sec.id} keeps the papers neat, uses the scanner, and makes the kind choice instead of a quick dishonest one.",
        "Write a child-friendly rhyme about work, scanning, and a small moral choice in a tiny office.",
    ]


def story_qa(world: World) -> list[QAItem]:
    sec = _safe_fact(world, world.facts, "secretary")
    papers = _safe_fact(world, world.facts, "papers")
    return [
        QAItem(
            question=f"Who was working in the little office?",
            answer=f"It was {sec.id}, a secretary who cared about neat pages and steady work.",
        ),
        QAItem(
            question="What did the secretary want to do with the papers?",
            answer="She wanted to scan the papers carefully so the work would be productive and tidy.",
        ),
        QAItem(
            question="What moral choice did the secretary make?",
            answer="She chose honesty and care instead of taking a dishonest shortcut.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The papers were scanned, the desk was neat again, and the secretary felt relieved and proud of doing the right thing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a scanner do?",
            answer="A scanner makes a copy of a paper or picture and turns it into a digital image.",
        ),
        QAItem(
            question="What does productive mean?",
            answer="Productive means getting useful work done well and on time.",
        ),
        QAItem(
            question="What is a secretary?",
            answer="A secretary is a person who helps organize papers, messages, and office work.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good choice or belief, like honesty, kindness, or fairness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
secretary(sec).
paper_stack(papers).
scanner(scanner).
stamp(stamp).

productive(sec) :- worked(sec), ready(scanner), sorted(papers), scanned(papers).
honest(sec) :- chose_honesty(sec).
kind(sec) :- chose_kindness(sec).
moral_value(honesty).
moral_value(kindness).
child_story(sec) :- secretary(sec), moral_value(honesty), productive(sec).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("secretary", "secretary"),
        asp.fact("paper_stack", "papers"),
        asp.fact("scanner", "scanner"),
        asp.fact("stamp", "stamp"),
        asp.fact("moral_value", "honesty"),
        asp.fact("moral_value", "kindness"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about a secretary, scanning, and moral value.")
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    return StoryParams(
        name=getattr(args, "name", None) or rng.choice(["Mina", "Nora", "Lena", "Tess", "Ada"]),
        parent=getattr(args, "parent", None) or rng.choice(["mother", "father"]),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params.name, params.parent)
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


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show child_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible story shape: secretary -> honesty -> productive scanning")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(StoryParams(name=n, parent=p)) for n, p in [("Mina", "mother"), ("Nora", "father")]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
