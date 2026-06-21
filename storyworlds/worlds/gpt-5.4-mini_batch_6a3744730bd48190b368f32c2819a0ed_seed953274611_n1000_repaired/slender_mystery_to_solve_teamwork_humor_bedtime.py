#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slender_mystery_to_solve_teamwork_humor_bedtime.py
===================================================================================

A small bedtime-style storyworld about a tiny mystery in a quiet room:
someone loses a little bedtime object, the children search together, and
their teamwork and humor turn worry into giggles. The world is built as a
stateful simulation with physical meters and emotional memes, and it includes
a slender clue in every story.

The story premise is simple:
- a cozy bedtime scene
- a small mystery to solve
- teamwork between children and a grown-up
- a funny misunderstanding that softens the mood
- a calm ending image that proves the mystery was solved

The world is intentionally small and child-facing.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
TEAM_MIN = 1.0


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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    cozy: str
    darkness: str
    allows: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    slender: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Mystery:
    id: str
    missing: str
    hiding_place: str
    mixup: str
    reveal: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class TeamMove:
    id: str
    idea: str
    joke: str
    action: str
    success: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_misplace(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["searching"] < THRESHOLD:
            continue
        sig = ("searching", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__search__")
    return out


def _r_team(world: World) -> list[str]:
    out = []
    if sum(1 for e in world.characters() if e.memes["helping"] >= THRESHOLD) >= 2:
        sig = ("team",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        for e in world.characters():
            if e.memes["helping"] >= THRESHOLD:
                e.memes["joy"] += 1
                e.memes["bravery"] += 1
        out.append("__team__")
    return out


CAUSAL_RULES = [Rule("misplace", _r_misplace), Rule("team", _r_team)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def clue_is_relevant(mystery: Mystery, clue: Clue) -> bool:
    return clue.slender and clue.id in mystery.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for mystery_id, mystery in MYSTERIES.items():
            for clue_id, clue in CLUES.items():
                if clue_is_relevant(mystery, clue) and setting_id in mystery.tags:
                    combos.append((setting_id, mystery_id, clue_id))
    return combos


def explain_rejection(mystery: Mystery, clue: Clue) -> str:
    return (
        f"(No story: the clue '{clue.label}' does not fit this mystery. "
        f"The story needs a slender clue that can honestly point toward {mystery.missing}.)"
    )


def predict(world: World, mystery: Mystery, clue: Clue, move: TeamMove) -> dict:
    sim = world.copy()
    sim.get("child").meters["searching"] += 1
    sim.get("parent").meters["searching"] += 1
    propagate(sim, narrate=False)
    solved = sim.facts.get("found", False)
    return {"solved": solved, "team": sum(e.memes["joy"] for e in sim.characters())}


def setup(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["love"] += 1
    parent.memes["love"] += 1
    world.say(
        f"At bedtime, {child.id} and {parent.id} tucked themselves into {setting.place}. "
        f"{setting.cozy}"
    )
    world.say(
        f"The room was very {setting.darkness}, and the night felt soft and still."
    )


def mystery_nudge(world: World, child: Entity, mystery: Mystery, clue: Clue) -> None:
    child.meters["searching"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"Then a small mystery began: {mystery.mixup}. "
        f"{child.id} spotted a {clue.label} clue that was as {clue.phrase}."
    )


def worry(world: World, parent: Entity, mystery: Mystery) -> None:
    parent.memes["worry"] += 1
    world.say(
        f"{parent.id} frowned a little. \"If {mystery.missing} is missing, we should look "
        f"together,\" {parent.pronoun()} said."
    )


def joke_and_team(world: World, child: Entity, parent: Entity, move: TeamMove) -> None:
    child.memes["helping"] += 1
    parent.memes["helping"] += 1
    world.say(
        f'{child.id} giggled and said, "{move.joke}" '
        f"Then {child.id} and {parent.id} tried {move.idea}."
    )
    propagate(world, narrate=True)


def solve(world: World, child: Entity, parent: Entity, mystery: Mystery, clue: Clue, move: TeamMove) -> None:
    world.facts["found"] = True
    child.meters["found"] += 1
    parent.meters["found"] += 1
    child.memes["relief"] += 1
    parent.memes["relief"] += 1
    world.say(
        f"Together they followed the tiny clue, and at last {mystery.reveal}."
    )
    world.say(
        f"{parent.id} lifted {mystery.hiding_place} with one hand, and there was {mystery.missing}, "
        f"safe and waiting all along."
    )
    world.say(
        f'{child.id} laughed, "{move.success}!" and the room felt cozy again.'
    )


def end_image(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    world.say(
        f"At the end, {child.id} was sleepy and smiling, and {parent.id} was smiling too. "
        f"The {mystery.missing} lay on the blanket like a tiny treasure, and the night went quiet again."
    )


def tell(setting: Setting, mystery: Mystery, clue: Clue, move: TeamMove,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    world.add(Entity(id="clue", kind="thing", type="clue", label=clue.label))
    world.facts["mystery"] = mystery
    world.facts["clue"] = clue
    world.facts["move"] = move

    setup(world, child, parent, setting)
    world.para()
    mystery_nudge(world, child, mystery, clue)
    worry(world, parent, mystery)
    world.para()
    joke_and_team(world, child, parent, move)
    solve(world, child, parent, mystery, clue, move)
    world.para()
    end_image(world, child, parent, mystery)

    world.facts.update(child=child, parent=parent, setting=setting, solved=True)
    return world


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        place="the bedroom",
        cozy="A small lamp made a sleepy gold circle on the rug.",
        darkness="blue-dark",
        allows={"search"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the hallway",
        cozy="A nightlight blinked like a tiny star by the door.",
        darkness="moon-dark",
        allows={"search"},
    ),
    "nursery": Setting(
        id="nursery",
        place="the nursery",
        cozy="A stuffed bear watched over the pillows.",
        darkness="lamp-soft",
        allows={"search"},
    ),
}

MYSTERIES = {
    "missing_sock": Mystery(
        id="missing_sock",
        missing="the missing sock",
        hiding_place="the pillow fort",
        mixup="one sock had vanished from the laundry basket",
        reveal="the sock had slipped under the pillow fort",
        tags={"bedroom", "sock", "search"},
    ),
    "lost_rattle": Mystery(
        id="lost_rattle",
        missing="the rattle",
        hiding_place="the blanket pile",
        mixup="the rattle had rolled away with a soft clink",
        reveal="the rattle was tucked in the blanket pile",
        tags={"nursery", "rattle", "search"},
    ),
    "tiny_book": Mystery(
        id="tiny_book",
        missing="the tiny book",
        hiding_place="the teddy bear basket",
        mixup="the book was missing from the bedtime stack",
        reveal="the tiny book was waiting in the teddy bear basket",
        tags={"hallway", "book", "search"},
    ),
}

CLUES = {
    "slender_thread": Clue(
        id="slender_thread",
        label="slender thread",
        phrase="slender and shiny",
        slender=True,
        tags={"sock", "book", "search"},
    ),
    "crumb": Clue(
        id="crumb",
        label="cookie crumb",
        phrase="tiny and crumbly",
        slender=False,
        tags={"snack"},
    ),
    "ribbon": Clue(
        id="ribbon",
        label="narrow ribbon",
        phrase="thin and twisty",
        slender=True,
        tags={"rattle", "search"},
    ),
}

MOVES = {
    "peek_together": TeamMove(
        id="peek_together",
        idea="peeking under the pillows together",
        joke="Maybe the sock went on a pillow adventure!",
        action="peek",
        success="We found it by looking together",
        tags={"team", "humor"},
    ),
    "tickle_torch": TeamMove(
        id="tickle_torch",
        idea="using the flashlight like a funny nose",
        joke="This flashlight looks like a sleepy little dragon!",
        action="shine",
        success="Our teamwork was quicker than a yawn",
        tags={"team", "humor"},
    ),
    "sneak_search": TeamMove(
        id="sneak_search",
        idea="tiptoeing with careful hands",
        joke="We are sneaky bedtime detectives!",
        action="tiptoe",
        success="Teamwork made the mystery small enough to solve",
        tags={"team", "humor"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Eli", "Noah", "Theo"]
PARENT_NAMES = ["Mom", "Dad", "Mama", "Papa"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    clue: str
    move: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child about {f["mystery"].missing}, a slender clue, teamwork, and a funny moment.',
        f"Tell a cozy mystery where {f['child'].id} and {f['parent'].id} solve a tiny problem together and laugh along the way.",
        f'Write a gentle bedtime story that includes the word "slender" and ends with a calm, solved mystery.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    mystery = f["mystery"]
    clue = f["clue"]
    move = f["move"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.id}, who were getting ready for bed. They shared a little mystery and solved it together."),
        ("What was the mystery?",
         f"{mystery.mixup}. Together they found that {mystery.reveal}."),
        ("What was slender in the story?",
         f"The {clue.label} was slender. It mattered because it helped point them toward the missing thing."),
        ("How did teamwork help?",
         f"{child.id} and {parent.id} looked together and used {move.idea}. That teamwork made the mystery easier to solve and kept the mood gentle."),
        ("What made the story funny?",
         f"{move.joke} was the funny part. It turned the searching into a game and helped everyone relax."),
        ("How did the story end?",
         f"It ended with {mystery.missing} found and everyone calm in the cozy room. The ending image shows the night settling down again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does slender mean?",
         "Slender means thin and narrow, like a little thread or ribbon. In a bedtime mystery, a slender clue can be easy to miss if you are not looking closely."),
        ("Why do people work together in a mystery?",
         "Working together helps because two pairs of eyes can notice more than one. Teamwork also makes a small problem feel less scary."),
        ("Why can a story be funny at bedtime?",
         "A funny moment can turn worry into giggles. That makes the room feel safe and cozy again before sleep."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
slender_clue(C) :- clue(C), slender(C).
teamwork :- helping(child), helping(parent).
humor :- joke(M).
solved :- found(missing).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact(t, mid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.slender:
            lines.append(asp.fact("slender", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for mid, mv in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("joke", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime mystery storyworld with slender clues, teamwork, and humor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, clue = rng.choice(sorted(combos))
    move = args.move or rng.choice(sorted(MOVES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent_name = args.parent_name or ("Mom" if parent_gender == "mother" else "Dad")
    return StoryParams(
        setting=setting,
        mystery=mystery,
        clue=clue,
        move=move,
        child_name=child_name,
        child_gender=child_gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.clue not in CLUES or params.move not in MOVES:
        raise StoryError("Invalid parameters.")
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    clue = CLUES[params.clue]
    move = MOVES[params.move]
    if not clue_is_relevant(mystery, clue):
        raise StoryError("The clue does not fit the mystery.")
    world = tell(setting, mystery, clue, move, params.child_name, params.child_gender, params.parent_name, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


CURATED = [
    StoryParams(setting="bedroom", mystery="missing_sock", clue="slender_thread", move="peek_together",
                child_name="Mia", child_gender="girl", parent_name="Mom", parent_gender="mother"),
    StoryParams(setting="nursery", mystery="lost_rattle", clue="ribbon", move="tickle_torch",
                child_name="Leo", child_gender="boy", parent_name="Dad", parent_gender="father"),
    StoryParams(setting="hallway", mystery="tiny_book", clue="slender_thread", move="sneak_search",
                child_name="Nora", child_gender="girl", parent_name="Mom", parent_gender="mother"),
]


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
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, m, c in combos:
            print(f"  {s:8} {m:14} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
