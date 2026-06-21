#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slim_parcel_madame_inner_monologue_reconciliation_detective.py
==============================================================================================

A tiny detective-story world for a child-facing mystery with inner monologue and
reconciliation.  The seed words are woven into the world model: a slim clue, a
parcel, and Madame as the central adult witness.

Premise:
- A detective, a worried child, and Madame discover that a parcel has gone
  missing.
- The detective listens to an inner monologue, follows small physical clues,
  and discovers the parcel was not stolen at all.
- A mistaken accusation is repaired by a calm reconciliation, and the parcel is
  returned with an apology.

This script follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- a Python reasonableness gate
- inline ASP twin and asp_facts()
- StoryParams, build_parser, resolve_params, generate, emit, main
- QA sets grounded in world state, not rendered text parsing
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

DETECTIVE_GAIN = 1.0
THRESHOLD = 1.0
SLIM_MAX = 1.6


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
    missing: bool = False
    found: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "madame"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class Scene:
    place: str
    mood: str
    hiding_place: str
    opening_image: str
    ending_image: str
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
    word: str
    kind: str
    help_text: str
    slimness: float
    reveals: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_find(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("parcel_hidden"):
        sig = ("found",)
        if sig not in world.fired:
            world.fired.add(sig)
            detective = world.get("detective")
            detective.memes["certainty"] += 1
            detective.meters["evidence"] += 1
            out.append("__inner__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("accusation") and world.facts.get("explanation"):
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in ("child", "madame"):
                if kid in world.entities:
                    world.get(kid).memes["relief"] += 1
            out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("find", "mystery", _r_find), Rule("reconcile", "social", _r_reconcile)]


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


def reasonableness_gate(scene: Scene, clue: Clue) -> bool:
    return clue.slimness <= SLIM_MAX and scene.place and clue.kind in {"paper", "string", "receipt", "thread"}


def hide_candidate(scene: Scene, clue: Clue) -> bool:
    return reasonableness_gate(scene, clue) and clue.reveals == "parcel"


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def use_clue(world: World, clue: Clue) -> None:
    detective = world.get("detective")
    detective.meters["evidence"] += clue.slimness
    detective.memes["focus"] += 1
    world.facts["used_clue"] = clue.id
    world.say(
        f"The detective picked up a slim {clue.word}, and in the quiet of {world.facts['scene'].place}, "
        f"the clue felt almost lighter than a feather."
    )
    world.say(
        f"Inside, {detective.id}'s inner monologue ticked along: {clue.help_text}."
    )


def suspect(world: World, child: Entity, madame: Entity, clue: Clue) -> None:
    child.memes["worry"] += 1
    world.facts["accusation"] = True
    world.say(
        f'"It must be Madame," {child.id} muttered, staring at the empty shelf. '
        f'"{clue.word} scraps near the parcel mean someone took it."'
    )
    world.say(
        f"But {child.id}'s inner monologue was softer than the accusation: perhaps the room was only messy, not guilty.'
    )


def check(world: World, detective: Entity, clue: Clue, parcel: Entity, madame: Entity) -> None:
    detective.memes["doubt"] += 1
    world.say(
        f"{detective.id} did not rush. {detective.pronoun().capitalize()} followed the {clue.word} trail, "
        f"looked under the table, and checked the little gap behind the blue chair."
    )
    if world.facts.get("parcel_hidden"):
        world.say(
            f"There, tucked in a narrow nook, the parcel waited exactly where the clue pointed."
        )
        parcel.found = True
        parcel.missing = False
        world.facts["found_parcel"] = True


def explain(world: World, madame: Entity, child: Entity, parcel: Entity) -> None:
    world.facts["explanation"] = True
    madame.memes["calm"] += 1
    world.say(
        f'"I did not take it," Madame said kindly. "I moved the parcel so the rain would not soak it, '
        f"and I meant to tell you."'
    )
    world.say(
        f'{child.id} looked again and saw the dry edge of the parcel wrapper. The mistake had been small, '
        f'but the worry had been big.'
    )


def reconcile(world: World, child: Entity, madame: Entity, parcel: Entity) -> None:
    child.memes["shame"] += 1
    child.memes["relief"] += 1
    madame.memes["relief"] += 1
    world.say(
        f'{child.id} lowered {child.pronoun("possessive")} voice. "I was wrong," {child.id} said. '
        f'"I jumped to a conclusion."'
    )
    world.say(
        f'Madame smiled, and the two of them stood beside the parcel like people who had found the last missing piece of a puzzle.'
    )
    world.say(
        f'{child.id} apologized, and Madame accepted it at once. The room felt warm again.'
    )


def finish(world: World, child: Entity, detective: Entity, parcel: Entity, scene: Scene) -> None:
    child.memes["trust"] += 1
    detective.memes["pride"] += 1
    parcel.found = True
    world.say(
        f"At the end, the parcel was back on the table, the lantern made a soft gold pool, and {child.id} remembered "
        f"to listen before accusing."
    )
    world.say(scene.ending_image)


def tell(scene: Scene, clue: Clue, response: Response, child_name: str = "Pip",
         child_gender: str = "boy", detective_name: str = "Inspector Vale",
         detective_gender: str = "man", madame_name: str = "Madame Mirelle",
         delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    madame = world.add(Entity(id=madame_name, kind="character", type="madame", role="witness", label="Madame"))
    parcel = world.add(Entity(id="parcel", kind="thing", type="parcel", label="parcel", missing=True))
    world.facts["scene"] = scene
    world.facts["delay"] = delay
    world.facts["parcel_hidden"] = True
    world.facts["clue"] = clue
    world.facts["response"] = response

    child.memes["worry"] = 1.0
    detective.memes["inner_voice"] = 1.0

    world.say(
        f"In {scene.place}, the case opened with a quiet mood and one missing parcel. {scene.opening_image}"
    )
    world.say(
        f"{child.id} found a slim {clue.word} near the shelf, while {madame_name} watched with steady eyes."
    )
    world.para()
    suspect(world, child, madame, clue)
    use_clue(world, clue)
    check(world, detective, clue, parcel, madame)
    world.para()
    explain(world, madame, child, parcel)
    reconcile(world, child, madame, parcel)
    world.para()
    finish(world, child, detective, parcel, scene)
    world.facts.update(child=child, detective=detective, madame=madame, parcel=parcel, outcome="reconciled")
    return world


SCENES = {
    "station": Scene(
        place="the little station office",
        mood="hushed",
        hiding_place="behind the blue chair",
        opening_image="A brass lamp glowed on the counter, and a damp coat hung by the door.",
        ending_image="The brass lamp shone on the returned parcel, and the blue chair no longer hid any secrets.",
    ),
    "library": Scene(
        place="the back room of the library",
        mood="soft",
        hiding_place="behind the reading stool",
        opening_image="Dust floated in the sunlight, and a bookmark lay like a tiny flag on the floor.",
        ending_image="The returned parcel sat by the books, and the room felt tidy enough to trust again.",
    ),
    "corner_shop": Scene(
        place="Madame's corner shop",
        mood="careful",
        hiding_place="under the counter tray",
        opening_image="The bell over the door had gone quiet, and a tin of biscuits waited unopened.",
        ending_image="The parcel rested beside the biscuits, and the shop smelled only of tea and rain.",
    ),
}

CLUES = {
    "thread": Clue(id="thread", word="thread", kind="string", help_text="A thread this thin could snag on a chair and lead the eye somewhere small", slimness=0.5, reveals="parcel", tags={"slim", "parcel"}),
    "receipt": Clue(id="receipt", word="receipt", kind="paper", help_text="A receipt left at the edge of a table often points to where hands were busy", slimness=0.8, reveals="parcel", tags={"slim", "parcel"}),
    "sliver": Clue(id="sliver", word="sliver", kind="paper", help_text="A sliver of torn paper can tell a detective that something was moved, not stolen", slimness=0.6, reveals="parcel", tags={"slim", "parcel"}),
}

RESPONSES = {
    "gentle": Response(id="gentle", sense=3, power=1, text="spoke gently and checked the room again", fail="spoke gently, but the puzzle stayed tangled", tags={"reconcile"}),
    "patient": Response(id="patient", sense=4, power=2, text="waited, listened, and asked one careful question at a time", fail="waited too long, and the worry grew", tags={"reconcile"}),
    "quick": Response(id="quick", sense=2, power=1, text="called everyone together and asked for calm voices", fail="called out too quickly and only stirred the fear", tags={"reconcile"}),
}

SCENARIO_KEYS = [(s, c, r) for s in SCENES for c in CLUES for r in RESPONSES]


@dataclass
class StoryParams:
    scene: str
    clue: str
    response: str
    child_name: str
    child_gender: str
    detective_name: str
    detective_gender: str
    madame_name: str
    delay: int = 0
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


CURATED = [
    StoryParams(scene="station", clue="thread", response="patient", child_name="Pip", child_gender="boy", detective_name="Inspector Vale", detective_gender="man", madame_name="Madame Mirelle", delay=0),
    StoryParams(scene="library", clue="receipt", response="gentle", child_name="Lina", child_gender="girl", detective_name="Detective Quinn", detective_gender="woman", madame_name="Madame Ciel", delay=0),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SCENES:
        for c in CLUES:
            for r in RESPONSES:
                if hide_candidate(SCENES[s], CLUES[c]):
                    out.append((s, c, r))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    clue: Clue = f["clue"]
    return [
        f"Write a detective story for a child that includes the words slim, parcel, and Madame, set in {scene.place}.",
        f"Tell a mystery where a slim {clue.word} helps solve the case of a missing parcel, and the mistake ends in reconciliation.",
        f"Write a child-friendly detective story with an inner monologue, a wrong suspicion, and a kind apology at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    detective: Entity = f["detective"]
    madame: Entity = f["madame"]
    clue: Clue = f["clue"]
    parcel: Entity = f["parcel"]
    scene: Scene = f["scene"]
    qa = [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a detective story about a missing parcel, a slim clue, and a mistaken suspicion. The case gets calmer because the detective uses careful thinking instead of rushing."
        ),
        QAItem(
            question=f"What did {child.id} think at first?",
            answer=f"{child.id} first thought Madame might have taken the parcel. That idea came from worry, but the story shows it was only a mistake."
        ),
        QAItem(
            question=f"How was the parcel found?",
            answer=f"The detective followed a slim {clue.word} and checked the hiding place in {scene.place}. That careful search revealed the parcel had only been moved to stay dry."
        ),
        QAItem(
            question=f"How did {child.id} and Madame make things right?",
            answer=f"{child.id} apologized, and Madame accepted the apology kindly. Their reconciliation mattered because it turned the misunderstanding into trust again."
        ),
    ]
    if parcel.found:
        qa.append(
            QAItem(
                question="What was the ending image?",
                answer=f"The parcel was back where everyone could see it, and the room felt safe again. The quiet ending proves the case was solved and the worry was repaired."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["clue"].tags)
    out = []
    if "slim" in tags:
        out.append(QAItem(question="What does slim mean?", answer="Slim means narrow or thin. A slim clue is small enough to notice only if you look carefully."))
    if "parcel" in tags:
        out.append(QAItem(question="What is a parcel?", answer="A parcel is a package wrapped up to be carried or delivered. It can hold a gift, a letter, or something important."))
    out.append(QAItem(question="What is a detective for?", answer="A detective looks for clues and tries to solve a mystery. A good detective asks careful questions and notices small details."))
    out.append(QAItem(question="What is reconciliation?", answer="Reconciliation means making peace again after a misunderstanding. People talk kindly, admit mistakes, and begin to trust each other again."))
    out.append(QAItem(question="What is an inner monologue?", answer="An inner monologue is the quiet voice inside a person's mind. It shows what they are thinking even before they say anything aloud."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.missing:
            bits.append("missing=True")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(scene: Scene, clue: Clue) -> str:
    return (
        f"(No story: the clue '{clue.word}' is not reasonable for this detective setup. "
        f"Pick a slim clue that can truly point to the parcel.)"
    )


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("slimness", cid, c.slimness))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,R) :- scene(S), clue(C), response(R), slimness(C,N), N =< 1.6.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, clue=None, response=None, child_name=None, child_gender=None, detective_name=None, detective_gender=None, madame_name=None, delay=None), random.Random(1)))
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")
    else:
        print("OK: ASP parity and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world with inner monologue and reconciliation.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["man", "woman"])
    ap.add_argument("--madame-name")
    ap.add_argument("--delay", type=int, default=0)
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
    if args.scene and args.clue and not hide_candidate(SCENES[args.scene], CLUES[args.clue]):
        raise StoryError(explain_rejection(SCENES[args.scene], CLUES[args.clue]))
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.clue is None or c[1] == args.clue)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, clue, response = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["boy", "girl"])
    detective_gender = args.detective_gender or rng.choice(["man", "woman"])
    return StoryParams(
        scene=scene,
        clue=clue,
        response=response,
        child_name=args.child_name or rng.choice(["Pip", "Lina", "Milo", "Tess"]),
        child_gender=child_gender,
        detective_name=args.detective_name or rng.choice(["Inspector Vale", "Detective Quinn", "Sergeant Moss"]),
        detective_gender=detective_gender,
        madame_name=args.madame_name or rng.choice(["Madame Mirelle", "Madame Ciel", "Madame June"]),
        delay=args.delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.clue not in CLUES or params.response not in RESPONSES:
        raise StoryError("Invalid StoryParams values.")
    world = tell(SCENES[params.scene], CLUES[params.clue], RESPONSES[params.response],
                 child_name=params.child_name, child_gender=params.child_gender,
                 detective_name=params.detective_name, detective_gender=params.detective_gender,
                 madame_name=params.madame_name, delay=params.delay)
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
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible scene/clue/response combos:")
        for item in combos:
            print(" ", item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
