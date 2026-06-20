#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/litter_maker_muddy_slope_misunderstanding_bad_ending.py
======================================================================================

A standalone storyworld for a small mystery on a muddy slope.

Premise:
- A child sees litter on a muddy slope.
- A misunderstanding makes them blame the wrong "maker".
- The search for the supposed maker goes wrong.
- The ending is bad: the litter stays, the slope gets worse, and the child learns a sad lesson.

This world is intentionally small and classical:
- typed entities
- physical meters and emotional memes
- forward-chained causal rules
- a reasonableness gate
- inline ASP twin
- grounded prompts, story QA, and world-knowledge QA

Run it:
    python storyworlds/worlds/gpt-5.4-mini/litter_maker_muddy_slope_misunderstanding_bad_ending.py
    python storyworlds/worlds/gpt-5.4-mini/litter_maker_muddy_slope_misunderstanding_bad_ending.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/litter_maker_muddy_slope_misunderstanding_bad_ending.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    slope: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Litter:
    id: str
    label: str
    phrase: str
    type: str
    can_blame: bool = True
    dirty: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Maker:
    id: str
    label: str
    phrase: str
    type: str
    makes_litter: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Mistake:
    id: str
    label: str
    clue: str
    action: str
    wrong_thought: str
    bad_turn: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_spotting(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["noticed"] < THRESHOLD:
            continue
        sig = ("spotting", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["curiosity"] += 1
        out.append("__spot__")
    return out


def _r_misread(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue_text", "")
    if clue and world.facts.get("misread") and not world.facts.get("blame_set"):
        world.facts["blame_set"] = True
        detective = world.get(world.facts["detective"])
        detective.memes["certainty"] += 1
        out.append("__misread__")
    return out


def _r_trouble(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("wrong_search"):
        return out
    slope = world.get("slope")
    litter = world.get("litter")
    if ("trouble",) in world.fired:
        return out
    world.fired.add(("trouble",))
    slope.meters["mud"] += 1
    slope.meters["mess"] += 1
    litter.meters["scattered"] += 1
    out.append("__trouble__")
    return out


CAUSAL_RULES = [
    Rule("spotting", "mind", _r_spotting),
    Rule("misread", "mind", _r_misread),
    Rule("trouble", "physical", _r_trouble),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_combo(setting: Setting, litter: Litter, maker: Maker, mistake: Mistake) -> bool:
    return setting.id == "muddy_slope" and litter.can_blame and maker.makes_litter and mistake.id in {"misunderstanding", "bad_ending"}


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [("muddy_slope", "paper_litter", "trash_maker", "misunderstanding")]


@dataclass
@dataclass
class StoryParams:
    setting: str
    litter: str
    maker: str
    mistake: str
    detective: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "muddy_slope": Setting("muddy_slope", "the muddy slope", "quiet and gray", "steep", {"mud", "slope"}),
}

LITTERS = {
    "paper_litter": Litter("paper_litter", "litter", "a torn paper cup and a chip bag", "trash", tags={"litter", "trash"}),
    "plastic_litter": Litter("plastic_litter", "litter", "a crumpled wrapper and a small bottle", "trash", tags={"litter", "trash"}),
}

MAKERS = {
    "trash_maker": Maker("trash_maker", "maker", "the person who dropped the litter", "person", tags={"maker"}),
    "wind_maker": Maker("wind_maker", "maker", "the wind that blew the trash loose", "wind", tags={"maker"}),
}

MISTAKES = {
    "misunderstanding": Mistake(
        "misunderstanding",
        "misunderstanding",
        "a muddy footprint and a broken twig",
        "look for the maker",
        "thought the wrong maker left the litter",
        "walked into a worse spot and lost the trail",
        tags={"mystery", "misunderstanding"},
    ),
    "bad_ending": Mistake(
        "bad_ending",
        "bad ending",
        "the litter kept sliding down the slope",
        "chase the clue",
        "tried to fix the mystery without help",
        "made the muddy slope even messier",
        tags={"bad_ending"},
    ),
}

GROWNUPS = ["mother", "father"]
NAMES = ["Mia", "Noah", "Lena", "Kai", "Ivy", "Owen"]


def clue_from_world(world: World) -> str:
    litter = world.facts["litter_cfg"]
    return f"{litter.label} near a muddy footprint"


def predict_badness(world: World) -> dict:
    sim = world.copy()
    sim.get("detective").meters["noticed"] += 1
    sim.get("litter").meters["scattered"] += 1
    sim.get("slope").meters["mud"] += 1
    return {
        "mess": sim.get("slope").meters["mess"],
        "scattered": sim.get("litter").meters["scattered"],
    }


def open_scene(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"On a gray afternoon, {child.id} and {parent.label_word} went to "
        f"{world.setting.place}. The slope looked quiet, but the ground was slick "
        f"with mud and small bits of trash."
    )
    world.say(
        f"{child.id} noticed {world.facts['litter_cfg'].phrase} near a muddy print. "
        f"It felt like a mystery, and {child.id} wanted to know who left it there."
    )


def misread_signs(world: World, child: Entity, litter: Litter, maker: Maker) -> None:
    child.meters["noticed"] += 1
    child.memes["curiosity"] += 1
    world.facts["clue_text"] = clue_from_world(world)
    world.say(
        f"{child.id} pointed at the clue. \"That has to be from the {maker.label},\" "
        f"{child.pronoun()} whispered. The words sounded sure, but the trail was only "
        f"a wet print and a bend in the mud."
    )
    world.say(
        f"{child.id} thought the {maker.label} was hiding nearby, and the little mystery "
        f"turned into a wrong guess."
    )


def warn(parent: Entity, child: Entity, litter: Litter, mistake: Mistake) -> None:
    parent.memes["concern"] += 1
    world_text = (
        f'{parent.id} frowned. "Wait," {parent.pronoun()} said. "A muddy print does not '
        f"prove who made the litter. Let's go slowly."
    )
    if mistake.id == "misunderstanding":
        world_text = (
            f'{parent.id} frowned. "Wait," {parent.pronoun()} said. "A muddy print does not '
            f"prove who made the litter. That guess could be wrong."
        )
    parent.memes["warning"] += 1
    return world_text


def search_wrongly(world: World, child: Entity, maker: Maker, mistake: Mistake) -> None:
    world.facts["wrong_search"] = True
    child.memes["defiance"] += 1
    world.say(
        f'\"No, I know it,\" {child.id} said. {child.pronoun().capitalize()} ran after the '
        f"clue and tried to {mistake.action}."
    )
    world.say(
        f"But the path bent the wrong way, and the supposed {maker.label} was only a shadow "
        f"in the wet brush."
    )


def ending_bad(world: World, child: Entity, parent: Entity, litter: Litter, mistake: Mistake) -> None:
    propagate(world, narrate=False)
    child.memes["sadness"] += 2
    parent.memes["sadness"] += 1
    world.say(
        f"Then the slope gave a soft slide under {child.pronoun('possessive')} shoes. "
        f"The chase left the litter scattered lower down, and the muddy track grew wider."
    )
    world.say(
        f"{parent.label_word.capitalize()} held {child.id}'s hand and said the mystery "
        f"should have been handled more carefully. But the litter stayed there, and the "
        f"wrong guess made everything worse."
    )
    world.say(
        f"In the end, nobody solved the little mystery. The muddy slope kept its secret, "
        f"and the litter maker was never found."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.detective, kind="character", type="boy" if params.detective in {"Noah", "Owen", "Kai"} else "girl"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    world.add(Entity(id="slope", type="place", label="the muddy slope"))
    litter = world.add(Entity(id="litter", type="litter", label="litter"))
    maker = world.add(Entity(id="maker", type="maker", label="maker"))
    world.facts.update(litter_cfg=LITTERS[params.litter], maker_cfg=MAKERS[params.maker], mistake_cfg=MISTAKES[params.mistake], detective=child.id)

    open_scene(world, child, parent)
    world.para()
    misread_signs(world, child, LITTERS[params.litter], MAKERS[params.maker])
    world.say(
        f'{parent.id} said, "Maybe the {maker.label} is not a person at all. Maybe it is '
        f"just a clue we do not understand yet."
    )
    search_wrongly(world, child, MAKERS[params.maker], MISTAKES[params.mistake])
    world.para()
    ending_bad(world, child, parent, LITTERS[params.litter], MISTAKES[params.mistake])

    world.facts.update(
        outcome="bad",
        child=child,
        parent=parent,
        litter=litter,
        maker=maker,
        misread=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a 3-to-5-year-old on a muddy slope that includes the words "{f["litter_cfg"].label}" and "maker".',
        f"Tell a short mystery where {f['detective']} sees {f['litter_cfg'].phrase} and makes a wrong guess about the maker.",
        "Write a sad mystery with a misunderstanding, muddy slope, and a bad ending where the wrong clue makes things worse.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    litter = f["litter_cfg"]
    maker = f["maker_cfg"]
    mistake = f["mistake_cfg"]
    return [
        QAItem(
            question="What was the child trying to figure out?",
            answer=f"{child.id} was trying to figure out who left the litter on the muddy slope. It seemed like a mystery because there was only a small clue and no clear answer.",
        ),
        QAItem(
            question="Why was the guess a misunderstanding?",
            answer=f"{child.id} blamed the {maker.label}, but the clue was only a muddy footprint and a broken path. That was not enough to prove who made the litter, so the guess was a misunderstanding.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly. The child chased the wrong clue, the slope got messier, and nobody found a good answer in time.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is litter?",
            answer="Litter is trash that people leave on the ground instead of putting it in a bin. It can make places look messy and unsafe.",
        ),
        QAItem(
            question="What is a muddy slope?",
            answer="A muddy slope is a hill with wet, slippery mud on it. People can slide on it if they are not careful.",
        ),
        QAItem(
            question="What does a maker mean in a mystery?",
            answer="A maker is the one who made or left something behind. In a mystery, people try to learn who the maker was.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for lid in LITTERS:
        lines.append(asp.fact("litter", lid))
        lines.append(asp.fact("can_blame", lid))
    for mid in MAKERS:
        lines.append(asp.fact("maker", mid))
        lines.append(asp.fact("makes_litter", mid))
    for mid in MISTAKES:
        lines.append(asp.fact("mistake", mid))
    lines.append(asp.fact("muddy_slope", "muddy_slope"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, L, M, K) :- setting(S), litter(L), maker(M), mistake(K), S = muddy_slope, can_blame(L), makes_litter(M).
bad_outcome(K) :- mistake(K), K = misunderstanding.
bad_outcome(K) :- mistake(K), K = bad_ending.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_bad_outcomes() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show bad_outcome/1."))
    return sorted(x for (x,) in asp.atoms(model, "bad_outcome"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python valid_combos().")
        rc = 1
    if set(asp_bad_outcomes()) != {"misunderstanding", "bad_ending"}:
        print("MISMATCH: ASP bad outcomes differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small muddy-slope mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--litter", choices=LITTERS)
    ap.add_argument("--maker", choices=MAKERS)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--detective", choices=NAMES)
    ap.add_argument("--parent", choices=GROWNUPS)
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
    combos = valid_combos()
    if args.setting and args.setting != "muddy_slope":
        raise StoryError("This storyworld only supports a muddy slope.")
    if not combos:
        raise StoryError("No valid combos.")
    setting, litter, maker, mistake = rng.choice(combos)
    detective = args.detective or rng.choice(NAMES)
    parent = args.parent or rng.choice(GROWNUPS)
    return StoryParams(setting, litter, maker, mistake, detective, parent)


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
    StoryParams("muddy_slope", "paper_litter", "trash_maker", "misunderstanding", "Mia", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4.\n#show bad_outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng_base + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
