#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/exhibition_shaker_pharaoh_teamwork_nursery_rhyme.py
===================================================================================

A small story world built from the seed words ``exhibition``, ``shaker``, and
``pharaoh``.

Premise:
- A child-centered museum exhibition has a tall pharaoh display.
- A tiny shaker is needed to complete the exhibit's song-and-rhythm corner.
- The children must work together to place the shaker safely and make the
  exhibition feel lively.

Style:
- Nursery-rhyme-like, short lines, gentle repetition, concrete images.

The simulation models:
- a display that can wobble,
- a shaky item that can be steadied,
- teamwork that reduces wobble and adds delight,
- a calm ending image showing the exhibition is improved by shared effort.

The script follows the Storyweavers contract:
- stdlib only
- eager results import
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python reasonableness gate and inline ASP twin
- story-grounded QA from world state, not rendered text parsing
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
WOBBLE_LIMIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wobble": 0.0, "care": 0.0, "joy": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"teamwork": 0.0, "worry": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Exhibition:
    id: str
    scene: str
    rhyme: str
    ending: str
    label: str = "the exhibition"

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
class Shaker:
    id: str
    label: str
    phrase: str
    sound: str
    safe: bool = True

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
class Pharaoh:
    id: str
    label: str
    phrase: str
    height: str
    material: str

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
class TeamworkMove:
    id: str
    sense: int
    wobble_fix: float
    joy_gain: float
    text: str
    qa_text: str

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
    exhibition: Exhibition
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
        clone = World(self.exhibition)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

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


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    display = world.get("display")
    if child.memes["teamwork"] >= THRESHOLD and helper.memes["teamwork"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            display.meters["wobble"] = max(0.0, display.meters["wobble"] - 1.0)
            display.meters["joy"] += 1.0
            out.append("__teamwork__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    display = world.get("display")
    if display.meters["wobble"] < WOBBLE_LIMIT:
        sig = ("settle",)
        if sig not in world.fired:
            world.fired.add(sig)
            display.meters["tidy"] += 1.0
            out.append("__settled__")
    return out


CAUSAL_RULES = [Rule("teamwork", _r_teamwork), Rule("settle", _r_settle)]


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


def reasonableness_gate(exhibition: Exhibition, shaker: Shaker, pharaoh: Pharaoh) -> bool:
    return bool(exhibition.scene and shaker.safe and pharaoh.material in {"cardboard", "cloth", "paint"})


def can_teamwork_fix(move: TeamworkMove, display_wobble: float) -> bool:
    return move.wobble_fix >= display_wobble


def safe_move() -> TeamworkMove:
    return max(MOVES.values(), key=lambda m: (m.sense, m.wobble_fix))


def predict_turn(world: World, move: TeamworkMove) -> dict:
    sim = world.copy()
    child = sim.get("child")
    helper = sim.get("helper")
    child.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    sim.get("display").meters["wobble"] += 1.0
    propagate(sim, narrate=False)
    if can_teamwork_fix(move, sim.get("display").meters["wobble"]):
        sim.get("display").meters["wobble"] = 0.0
    return {
        "wobble": sim.get("display").meters["wobble"],
        "joy": sim.get("display").meters["joy"],
    }


def intro(world: World, child: Entity, helper: Entity, exhibition: Exhibition) -> None:
    world.say(
        f"Come one, come all, to the {exhibition.label}, so bright and grand. "
        f"{child.id} and {helper.id} walked in hand in hand."
    )
    world.say(
        f"The room was a song of colors and cheer, with {exhibition.scene} near."
    )


def show_pharaoh(world: World, pharaoh: Pharaoh) -> None:
    display = world.get("display")
    display.meters["wobble"] += 1.0
    world.say(
        f"There stood a {pharaoh.label}, tall and gold, {pharaoh.phrase}, brave and bold."
    )
    world.say(
        f"Up on the shelf, with a tiny sway, the exhibit looked a bit away."
    )


def need_help(world: World, child: Entity, helper: Entity, shaker: Shaker) -> None:
    world.say(
        f'{child.id} tapped the glass and gave a sigh. "{shaker.label} would make '
        f'this corner sing sky-high."'
    )
    world.say(
        f"{helper.id} nodded soft, with a thoughtful grin: "
        f'"Let us work together and tuck it in."'
    )


def teamwork(world: World, child: Entity, helper: Entity, shaker: Shaker, move: TeamworkMove) -> None:
    child.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    child.meters["care"] += 1
    helper.meters["care"] += 1
    world.say(
        f"{child.id} held the base, and {helper.id} held tight; "
        f"they moved the {shaker.label} just right."
    )
    world.say(move.text)
    propagate(world, narrate=False)


def finish(world: World, child: Entity, helper: Entity, exhibition: Exhibition, shaker: Shaker) -> None:
    display = world.get("display")
    child.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"The {shaker.label} gave a soft little shake, and the whole room seemed "
        f"to wake."
    )
    world.say(
        f"The {exhibition.label} stood neat and fine, with the {pharaoh.label} "
        f"glowing in the line."
    )
    world.say(exhibition.ending)
    if display.meters["wobble"] <= 0:
        world.say("So hand in hand, the helpers smiled, and the exhibit stayed calm and mild.")


def tell(exhibition: Exhibition, shaker: Shaker, pharaoh: Pharaoh,
         child_name: str = "Mina", helper_name: str = "Noah",
         child_type: str = "girl", helper_type: str = "boy") -> World:
    world = World(exhibition)
    child = world.add(Entity("child", kind="character", type=child_type, label=child_name, role="helper"))
    helper = world.add(Entity("helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    display = world.add(Entity("display", type="display", label="the display"))
    world.add(Entity("shaker", type="object", label=shaker.label))
    world.add(Entity("pharaoh", type="object", label=pharaoh.label))
    display.meters["wobble"] = 1.0
    intro(world, child, helper, exhibition)
    world.para()
    show_pharaoh(world, pharaoh)
    need_help(world, child, helper, shaker)
    world.para()
    move = safe_move()
    teamwork(world, child, helper, shaker, move)
    finish(world, child, helper, exhibition, shaker)
    world.facts.update(
        child=child, helper=helper, display=display, exhibition=exhibition,
        shaker=shaker, pharaoh=pharaoh, move=move, outcome="steady"
    )
    return world


THEMES = {
    "nursery": Exhibition(
        id="nursery",
        scene="paper stars, ribbon rows, and bright toy boats",
        rhyme="A little room of rhyme and light, where every corner felt just right.",
        ending="And the children clapped, for the little display shone proud and bright.",
    ),
    "gallery": Exhibition(
        id="gallery",
        scene="painted moons, small drums, and twinkling strings",
        rhyme="A gallery of bells and tune, under a smiling paper moon.",
        ending="And the bells went ting, and the children all went home with sing-song hearts.",
    ),
    "museum": Exhibition(
        id="museum",
        scene="golden cards, toy maps, and tiny flags",
        rhyme="A museum lane of story time, with every shelf in gentle rhyme.",
        ending="And the museum stayed neat and warm, like a nest that kept the charm.",
    ),
}

SHAKERS = {
    "seed": Shaker("seed", "shaker", "a little seed-shaped shaker", "shh-shh", True),
    "star": Shaker("star", "star shaker", "a star-shaped shaker with tiny beads", "tink-tink", True),
    "moon": Shaker("moon", "moon shaker", "a moon-shaped shaker", "clink-clink", True),
}

PHARAOHS = {
    "sand": Pharaoh("sand", "pharaoh", "a small sand pharaoh made from paper and glue", "tall", "cardboard"),
    "cloth": Pharaoh("cloth", "pharaoh", "a cloth pharaoh with a paper crown", "grand", "cloth"),
    "paint": Pharaoh("paint", "pharaoh", "a painted pharaoh with a soft smile", "shining", "paint"),
}

MOVES = {
    "steady": TeamworkMove("steady", 3, 2.0, 2.0,
                           "Together they steadied the shelf, and the wobble went away.",
                           "steady the shelf together"),
    "brace": TeamworkMove("brace", 2, 1.5, 1.0,
                          "One lifted low, and one lifted high; the little shelf held steady in the sky.",
                          "brace the shelf together"),
    "tidy": TeamworkMove("tidy", 1, 1.0, 1.0,
                         "They tidied the corner with careful care, and the shaker sat safe right there.",
                         "tidy the corner together"),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ruby", "Zara", "Maya"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Owen", "Finn", "Leo"]


@dataclass
@dataclass
class StoryParams:
    exhibition: str
    shaker: str
    pharaoh: str
    move: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for ex in THEMES:
        for sh in SHAKERS:
            for ph in PHARAOHS:
                if reasonableness_gate(THEMES[ex], SHAKERS[sh], PHARAOHS[ph]):
                    for mv in MOVES:
                        if can_teamwork_fix(MOVES[mv], 2.0):
                            combos.append((ex, sh, ph, mv))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme exhibition story world with teamwork.")
    ap.add_argument("--exhibition", choices=THEMES)
    ap.add_argument("--shaker", choices=SHAKERS)
    ap.add_argument("--pharaoh", choices=PHARAOHS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
              if (args.exhibition is None or c[0] == args.exhibition)
              and (args.shaker is None or c[1] == args.shaker)
              and (args.pharaoh is None or c[2] == args.pharaoh)
              and (args.move is None or c[3] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ex, sh, ph, mv = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if child_type == "girl" else "girl")
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (GIRL_NAMES if helper_type == "girl" else BOY_NAMES) if n != child_name])
    return StoryParams(ex, sh, ph, mv, child_name, child_type, helper_name, helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.exhibition], SHAKERS[params.shaker], PHARAOHS[params.pharaoh],
                 params.child_name, params.helper_name, params.child_type, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ex, sh, ph = f["exhibition"], f["shaker"], f["pharaoh"]
    return [
        f'Write a nursery-rhyme style story about an exhibition where a {sh.label} and a {ph.label} are part of the scene, and two children work together.',
        f"Tell a gentle story with the words exhibition, shaker, and pharaoh, where {f['child'].label} and {f['helper'].label} solve a small problem by teamwork.",
        f'Write a short rhyming museum story for young children that includes a {sh.label}, a {ph.label}, and a happy teamwork ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper = f["child"], f["helper"]
    ex, sh, ph = f["exhibition"], f["shaker"], f["pharaoh"]
    display = f["display"]
    move = f["move"]
    return [
        ("Who worked together in the story?",
         f"{child.label} and {helper.label} worked together, and their teamwork helped the exhibition stay calm and bright."),
        ("What problem did they solve?",
         f"They steadied the display so it would stop wobbling. That mattered because the pharaoh showpiece was tall, and the shaker corner needed to stay safe."),
        ("How did they solve it?",
         f"They used {move.qa_text} and then the wobble went down. The fix worked because both children helped at the same time."),
        ("How did the story end?",
         f"The exhibition ended neat and shining, with the pharaoh display standing proud. The shaker stayed in place, and the children felt pleased together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an exhibition?",
         "An exhibition is a show where people look at interesting things, pictures, or displays."),
        ("What is a shaker?",
         "A shaker is a little object with beads or seeds inside that makes a rattling sound when you shake it."),
        ("Who was a pharaoh?",
         "A pharaoh was an ancient ruler in Egypt, and stories often show pharaohs wearing crowns and looking grand."),
        ("What is teamwork?",
         "Teamwork means people help each other and do a job together instead of trying to do it all alone."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} {e.type:10} meters={e.meters} memes={e.memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(E, S, P, M) :- exhibition(E), shaker(S), pharaoh(P), move(M),
                     safe_shaker(S), stable_pharaoh(P), teamwork_move(M).
outcome(steady) :- valid(_,_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for e in THEMES:
        lines.append(asp.fact("exhibition", e))
    for s, v in SHAKERS.items():
        lines.append(asp.fact("shaker", s))
        if v.safe:
            lines.append(asp.fact("safe_shaker", s))
    for p, v in PHARAOHS.items():
        lines.append(asp.fact("pharaoh", p))
        if v.material in {"cardboard", "cloth", "paint"}:
            lines.append(asp.fact("stable_pharaoh", p))
    for m in MOVES:
        lines.append(asp.fact("move", m))
        lines.append(asp.fact("teamwork_move", m))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between clingo and valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            exhibition=None, shaker=None, pharaoh=None, move=None,
            child_name=None, helper_name=None, child_type=None, helper_type=None
        ), random.Random(7)))
        assert sample.story
    except Exception as err:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    else:
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False)
        print("OK: generation and emit smoke test passed.")
    return rc


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
    StoryParams("nursery", "seed", "sand", "steady", "Mina", "girl", "Noah", "boy"),
    StoryParams("gallery", "star", "cloth", "brace", "Lily", "girl", "Eli", "boy"),
    StoryParams("museum", "moon", "paint", "tidy", "Maya", "girl", "Finn", "boy"),
]


def asp_main_list() -> None:
    combos = asp_valid_combos()
    print(f"{len(combos)} compatible stories:")
    for combo in combos:
        print("  ", combo)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_main_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
