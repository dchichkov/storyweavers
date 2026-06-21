#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/perturb_reconciliation_misunderstanding_pirate_tale.py
======================================================================================

A small storyworld about pirate friends, a curious perturbation, a misunderstanding,
and a warm reconciliation.

A child-friendly pirate tale premise:
- The crew is preparing a tiny treasure hunt.
- A sudden perturbation changes a clue or object position.
- The captain and a crewmate misunderstand each other.
- A calm talk reveals the truth.
- The crew reconciles and sails on with a better plan.

This script is standalone and uses only the Python stdlib plus the shared
storyworlds/results.py and storyworlds/asp.py helpers.
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
SHIP_MIN_SPIRIT = 2.0


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
    image: str
    challenge: str
    route: str
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
class Perturbation:
    id: str
    label: str
    effect: str
    misplace: str
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
class Misunderstanding:
    id: str
    belief: str
    accusation: str
    worry: str
    cleared_by: str
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
class Reconciliation:
    id: str
    talk: str
    apology: str
    hug: str
    promise: str
    ending: str
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


def _r_tension(world: World) -> list[str]:
    out = []
    if world.get("crew").memes["worry"] >= THRESHOLD and "ship" in world.entities:
        ship = world.get("ship")
        if ship.meters["tension"] < THRESHOLD:
            ship.meters["tension"] += 1
            out.append("")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    cap = world.get("captain")
    mate = world.get("mate")
    if cap.memes["soften"] >= THRESHOLD and mate.memes["soften"] >= THRESHOLD:
        if ("reconcile",) not in world.fired:
            world.fired.add(("reconcile",))
            cap.memes["peace"] += 1
            mate.memes["peace"] += 1
            out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("tension", _r_tension), Rule("reconcile", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s and not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def perturb_risk(perturb: Perturbation, setting: Setting) -> bool:
    return perturb.effect == "shift_clue" and "map" in setting.challenge


def would_misunderstand(perturb: Perturbation, misunderstanding: Misunderstanding) -> bool:
    return perturb.label and misunderstanding.belief


def can_reconcile(reconciliation: Reconciliation, ship_spirit: float) -> bool:
    return reconciliation.id in RECONCILIATIONS and ship_spirit >= SHIP_MIN_SPIRIT


def predict(world: World, perturb: Perturbation, misunderstanding: Misunderstanding) -> dict:
    sim = world.copy()
    _do_perturb(sim, sim.get("clue"), perturb, narrate=False)
    _spark_misunderstanding(sim, sim.get("captain"), sim.get("mate"), misunderstanding, narrate=False)
    return {
        "clue_shifted": sim.get("clue").meters["shifted"] >= THRESHOLD,
        "worry": sim.get("captain").memes["worry"] + sim.get("mate").memes["worry"],
    }


def _do_perturb(world: World, clue: Entity, perturb: Perturbation, narrate: bool = True) -> None:
    clue.meters["shifted"] += 1
    clue.meters["scrambled"] += 1
    if narrate:
        world.say(f"The {perturb.label} gave the clue a little twist.")


def _spark_misunderstanding(world: World, captain: Entity, mate: Entity, misunderstanding: Misunderstanding, narrate: bool = True) -> None:
    captain.memes["worry"] += 1
    mate.memes["worry"] += 1
    if narrate:
        world.say(
            f"{captain.id} thought {mate.id} meant {misunderstanding.accusation}, "
            f"and {mate.id} thought {captain.id} was upset about the {misunderstanding.worry}."
        )


def setup(world: World, setting: Setting, captain: Entity, mate: Entity) -> None:
    world.say(
        f"On {setting.place}, the pirate crew gathered by {setting.image}. "
        f"{setting.route.capitalize()}."
    )
    world.say(
        f"{captain.id} and {mate.id} planned a tiny treasure hunt, and the crew felt bright and busy."
    )


def introduce_perturb(world: World, perturb: Perturbation, clue: Entity, setting: Setting) -> None:
    world.say(
        f"Then a small perturbation happened: {perturb.label} nudged the clue. "
        f"{perturb.reveal}."
    )
    world.say(
        f"The map no longer pointed cleanly toward {setting.challenge}."
    )
    _do_perturb(world, clue, perturb, narrate=False)


def misunderstanding_beat(world: World, captain: Entity, mate: Entity, misunderstanding: Misunderstanding) -> None:
    captain.memes["worry"] += 1
    mate.memes["worry"] += 1
    captain.memes["hurt"] += 1
    mate.memes["hurt"] += 1
    world.say(
        f"{captain.id} frowned and said, \"I thought you moved it on purpose.\" "
        f"{mate.id} blinked, because that was not what {mate.pronoun()} meant."
    )
    world.say(
        f"For a moment, the deck went quiet, and both pirates felt a little sad."
    )


def reconciliation_beat(world: World, captain: Entity, mate: Entity, reconciliation: Reconciliation) -> None:
    world.say(reconciliation.talk)
    captain.memes["soften"] += 1
    mate.memes["soften"] += 1
    captain.memes["worry"] = 0.0
    mate.memes["worry"] = 0.0
    propagate(world, narrate=False)
    world.say(reconciliation.apology)
    world.say(reconciliation.hug)
    world.say(reconciliation.promise)
    world.say(reconciliation.ending)


def tell(setting: Setting, perturb: Perturbation, misunderstanding: Misunderstanding, reconciliation: Reconciliation) -> World:
    world = World()
    captain = world.add(Entity(id="Captain Mira", kind="character", type="girl", role="captain"))
    mate = world.add(Entity(id="First Mate Finn", kind="character", type="boy", role="mate"))
    crew = world.add(Entity(id="crew", kind="group", type="group", label="the crew"))
    ship = world.add(Entity(id="ship", kind="thing", type="thing", label="the little ship"))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label="the treasure clue"))

    world.facts.update(
        captain=captain,
        mate=mate,
        crew=crew,
        ship=ship,
        clue=clue,
        setting=setting,
        perturb=perturb,
        misunderstanding=misunderstanding,
        reconciliation=reconciliation,
    )

    setup(world, setting, captain, mate)
    world.para()
    introduce_perturb(world, perturb, clue, setting)
    misunderstanding_beat(world, captain, mate, misunderstanding)
    world.para()
    reconciliation_beat(world, captain, mate, reconciliation)
    crew.memes["joy"] += 2
    ship.meters["peace"] += 1
    world.say(
        f"In the end, the pirates followed the clue together, and the little ship sailed on "
        f"with calmer hearts and a clearer map."
    )
    return world


SETTINGS = {
    "harbor": Setting(
        id="harbor",
        place="the harbor",
        image="the blue harbor water",
        challenge="the island with the shell cave",
        route="the dock was lined with ropes and gulls",
    ),
    "cove": Setting(
        id="cove",
        place="a quiet cove",
        image="the sandy cove",
        challenge="the rocky path to the hidden chest",
        route="the tide lapped softly at the stones",
    ),
    "deck": Setting(
        id="deck",
        place="the ship's deck",
        image="the lantern by the mast",
        challenge="the moonlit route to the treasure island",
        route="the sails snapped gently in the breeze",
    ),
}

PERTURBATIONS = {
    "wind": Perturbation(
        id="wind",
        label="a gust of wind",
        effect="shift_clue",
        misplace="blew the clue a little sideways",
        reveal="It had only blown the paper corner loose",
        tags={"perturb", "pirate"},
    ),
    "wave": Perturbation(
        id="wave",
        label="a splash of wave water",
        effect="shift_clue",
        misplace="bent the clue and slid it on the plank",
        reveal="It had only splashed the clue, not stolen it",
        tags={"perturb", "pirate"},
    ),
    "seagull": Perturbation(
        id="seagull",
        label="a curious seagull",
        effect="shift_clue",
        misplace="tugged the ribbon tied to the clue",
        reveal="The gull had been playful, not tricky",
        tags={"perturb", "pirate"},
    ),
}

MISUNDERSTANDINGS = {
    "blame": Misunderstanding(
        id="blame",
        belief="the clue was ruined on purpose",
        accusation="you did that on purpose",
        worry="the broken map",
        cleared_by="the clue was only shifted",
        tags={"misunderstanding"},
    ),
    "secret": Misunderstanding(
        id="secret",
        belief="the mate was hiding the clue",
        accusation="you hid the clue from me",
        worry="the missing turn",
        cleared_by="the clue had slipped away",
        tags={"misunderstanding"},
    ),
    "storm": Misunderstanding(
        id="storm",
        belief="the captain wanted to turn back",
        accusation="you want to give up",
        worry="the dark clouds",
        cleared_by="the plan was still brave",
        tags={"misunderstanding"},
    ),
}

RECONCILIATIONS = {
    "talk": Reconciliation(
        id="talk",
        talk="Mira took a breath and said, \"Let's look carefully before we blame anyone.\"",
        apology="Finn pointed to the clue and said, \"I'm sorry I snapped at you.\"",
        hug="Mira and Finn shared a quick hug.",
        promise="They promised to ask first and listen better next time.",
        ending="Then they laughed, because the treasure hunt felt friendly again.",
        tags={"reconciliation"},
    ),
    "shells": Reconciliation(
        id="shells",
        talk="Finn held up the clue and said, \"The wind only moved it a little.\"",
        apology="Mira nodded and said, \"I'm sorry I thought the worst.\"",
        hug="They bumped shoulders and grinned.",
        promise="They promised to check the clue together whenever it looked odd.",
        ending="After that, the map felt less cranky and more like an invitation.",
        tags={"reconciliation"},
    ),
}

NAMES = ["Mira", "Finn", "Tilda", "Jax", "Ruby", "Pip", "Nico", "Luna"]


@dataclass
class StoryParams:
    setting: str
    perturb: str
    misunderstanding: str
    reconciliation: str
    captain_name: str = "Captain Mira"
    mate_name: str = "First Mate Finn"
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PERTURBATIONS:
            for mid in MISUNDERSTANDINGS:
                for rid in RECONCILIATIONS:
                    if perturb_risk(PERTURBATIONS[pid], SETTINGS[sid]) and would_misunderstand(PERTURBATIONS[pid], MISUNDERSTANDINGS[mid]) and can_reconcile(RECONCILIATIONS[rid], 2.0):
                        combos.append((sid, pid, mid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about perturbation, misunderstanding, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--perturb", choices=PERTURBATIONS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--reconciliation", choices=RECONCILIATIONS)
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
    if args.setting and args.perturb:
        if not perturb_risk(PERTURBATIONS[args.perturb], SETTINGS[args.setting]):
            raise StoryError("That perturbation does not actually change the clue in this setting.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.perturb is None or c[1] == args.perturb)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)
              and (args.reconciliation is None or c[3] == args.reconciliation)]
    if not combos:
        curated = globals().get("CURATED", [])
        explicit = [
            v for k, v in vars(args).items()
            if k not in {"n", "seed", "all", "trace", "qa", "json", "asp", "verify", "show_asp"}
            and v is not None
            and v is not False
        ]
        if curated and not explicit:
            choice = rng.choice(curated)
            return choice if isinstance(choice, StoryParams) else StoryParams(*choice)
        raise StoryError("(No valid combination matches the given options.)")
    setting, perturb, misunderstanding, reconciliation = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        perturb=perturb,
        misunderstanding=misunderstanding,
        reconciliation=reconciliation,
        seed=args.seed,
    )


def prompts_for(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a small child that includes the word "{f["perturb"].id}" and ends with friends making peace.',
        f"Tell a pirate story where {f['captain'].id} and {f['mate'].id} have a misunderstanding after a perturbation, then reconcile.",
        f"Write a gentle treasure-hunt story with a misunderstanding, a talk, and a warm reconciliation on {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    perturb = f["perturb"]
    misunderstanding = f["misunderstanding"]
    reconciliation = f["reconciliation"]
    setting = f["setting"]
    return [
        ("Who is the story about?",
         f"It is about {captain.id} and {mate.id}, two pirates who were trying to follow a treasure clue at {setting.place}."),
        ("What caused the trouble?",
         f"A small perturbation changed the clue. That tiny change made the treasure hunt look wrong for a moment."),
        ("Why did they argue?",
         f"{captain.id} thought {mate.id} had caused {misunderstanding.belief}, and {mate.id} thought {captain.id} was upset about {misunderstanding.worry}."),
        ("How did they fix it?",
         f"They stopped, talked carefully, and apologized. After that, they reconciled and worked together again."),
        ("How did the story end?",
         f"It ended with peace and teamwork. The pirates felt friendly again, and the little ship sailed on with a clearer map."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a perturbation?",
         "A perturbation is a small change or disturbance that nudges something out of place."),
        ("What is a misunderstanding?",
         "A misunderstanding is when people think the wrong thing about each other or about what happened."),
        ("What is reconciliation?",
         "Reconciliation is when people make up, forgive each other, and feel friendly again."),
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
        lines.append(f"  {e.id:18} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.perturb not in PERTURBATIONS or params.misunderstanding not in MISUNDERSTANDINGS or params.reconciliation not in RECONCILIATIONS:
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS[params.setting], PERTURBATIONS[params.perturb], MISUNDERSTANDINGS[params.misunderstanding], RECONCILIATIONS[params.reconciliation])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(setting="harbor", perturb="wind", misunderstanding="blame", reconciliation="talk", seed=1),
    StoryParams(setting="cove", perturb="wave", misunderstanding="secret", reconciliation="shells", seed=2),
]


ASP_RULES = r"""
hazard(P) :- perturb(P).
misunderstanding(M) :- misunderstanding_word(M).
reconcile(R) :- reconciliation(R).
valid(S,P,M,R) :- setting(S), perturb(P), misunderstanding_word(M), reconciliation(R),
                  perturb_effect(P, shift_clue), can_confuse(P, M), can_reconcile(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PERTURBATIONS.items():
        lines.append(asp.fact("perturb", pid))
        lines.append(asp.fact("perturb_effect", pid, p.effect))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding_word", mid))
    for rid in RECONCILIATIONS:
        lines.append(asp.fact("reconciliation", rid))
    lines.append(asp.fact("can_reconcile", "talk"))
    lines.append(asp.fact("can_reconcile", "shells"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, perturb=None, misunderstanding=None, reconciliation=None, seed=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"Smoke test failed: {e}")
        rc = 1
    else:
        print("OK: verify smoke test passed and generation works.")
    return rc


def build_default_args() -> argparse.Namespace:
    return argparse.Namespace(setting=None, perturb=None, misunderstanding=None, reconciliation=None, seed=None)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
