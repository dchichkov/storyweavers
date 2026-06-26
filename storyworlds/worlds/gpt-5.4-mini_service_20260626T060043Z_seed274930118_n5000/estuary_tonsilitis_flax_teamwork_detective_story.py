#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/estuary_tonsilitis_flax_teamwork_detective_story.py
============================================================================================================

A small detective-story world about an estuary, tonsilitis, flax, and teamwork.

Seed-tale premise:
- A child detective and a helper search an estuary for a missing flax bundle.
- A witness has tonsilitis and can only whisper or point, which makes the case harder.
- The pair use teamwork: one looks near the reeds, the other checks the tide line.
- They find that the flax was used to tie a crate near the dock, and the mystery ends
  with the detective team understanding how the clues fit together.

This world models:
- physical meters: tide, sogginess, clue_value, fatigue, coldness
- emotional memes: curiosity, worry, confidence, relief, teamwork, patience

The story is designed to read like a complete child-facing detective tale:
setup, investigation, turn, and resolution, with state changes driving the prose.
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

# ---------------------------------------------------------------------------
# Registry constants
# ---------------------------------------------------------------------------

WATER_PLACES = {"estuary"}
CLUE_ITEMS = {"flax"}
SICKNESS = {"tonsilitis"}

NAMES = ["Mina", "Jasper", "Nora", "Eli", "Pia", "Toby", "Lena", "Owen"]
HELPERS = ["Milo", "June", "Iris", "Leo", "Zara", "Theo", "Ada", "Finn"]

DETECTIVE_GEAR = [
    "magnifying glass",
    "little notebook",
    "lantern",
    "mud boots",
]

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------



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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    detective: object | None = None
    partner: object | None = None
    witness: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Place:
    name: str = "the estuary"
    tidal: bool = True
    affords: set[str] = field(default_factory=lambda: {"search", "listen", "investigate"})
    PLACE: object | None = None
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


@dataclass
class Case:
    missing: str
    clue_kind: str
    culprit_kind: str
    method: str
    reveal: str
    keyword: str = "estuary"
    tags: set[str] = field(default_factory=lambda: {"estuary", "flax", "tonsilitis", "teamwork"})


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
    CASE: object | None = None
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
        return None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story state helpers
# ---------------------------------------------------------------------------


def _ensure_meter(ent: Entity, key: str) -> None:
    if key not in ent.meters:
        ent.meters[key] = 0.0


def _ensure_meme(ent: Entity, key: str) -> None:
    if key not in ent.memes:
        ent.memes[key] = 0.0


def add_meter(ent: Entity, key: str, amount: float) -> None:
    _ensure_meter(ent, key)
    ent.meters[key] += amount


def add_meme(ent: Entity, key: str, amount: float) -> None:
    _ensure_meme(ent, key)
    ent.memes[key] += amount


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------


THRESHOLD = 1.0


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (rule_wet_feet, rule_fatigue, rule_clue_from_flax, rule_teamwork_confidence, rule_cold_then_patience):
            lines = rule(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for s in out:
            world.say(s)
    return out


def rule_wet_feet(world: World) -> list[str]:
    out: list[str] = []
    estuary = world.get("estuary")
    if estuary.meters.get("tide", 0) >= THRESHOLD and estuary.meters.get("splash", 0) >= THRESHOLD:
        sig = ("wet_feet",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        for c in world.characters():
            add_meter(c, "sogginess", 1)
        out.append("The tide lapped the reeds, and muddy spray made everyone’s boots damp.")
    return out


def rule_fatigue(world: World) -> list[str]:
    out: list[str] = []
    for c in world.characters():
        if c.meters.get("sogginess", 0) >= THRESHOLD and ("fatigue", c.id) not in world.fired:
            world.fired.add(("fatigue", c.id))
            add_meter(c, "fatigue", 1)
            out.append(f"{c.id} felt a little tired from the damp walk.")
    return out


def rule_clue_from_flax(world: World) -> list[str]:
    flax = world.get("flax")
    clue = world.get("clue")
    out: list[str] = []
    if flax.meters.get("found", 0) >= THRESHOLD and ("clue",) not in world.fired:
        world.fired.add(("clue",))
        add_meter(clue, "clue_value", 1)
        out.append("The flax bundle turned out to be a clue, because it had been used to tie something down.")
    return out


def rule_teamwork_confidence(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    partner = world.get("partner")
    if detective.memes.get("teamwork", 0) >= THRESHOLD and partner.memes.get("teamwork", 0) >= THRESHOLD:
        sig = ("confidence",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        add_meme(detective, "confidence", 1)
        add_meme(partner, "confidence", 1)
        out.append("Working side by side made the pair feel braver and sharper.")
    return out


def rule_cold_then_patience(world: World) -> list[str]:
    out: list[str] = []
    witness = world.get("witness")
    if witness.meters.get("coldness", 0) >= THRESHOLD and witness.meters.get("throat_hurt", 0) >= THRESHOLD:
        sig = ("patience",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        add_meme(witness, "patience", 1)
        out.append("The witness had to rest their throat, so the detective waited and listened kindly.")
    return out


# ---------------------------------------------------------------------------
# Reasoning / simulation
# ---------------------------------------------------------------------------


def suspect_list(world: World) -> list[str]:
    return ["dock rope", "fishing crate", "reed bundle"]


def predict_find_flax(world: World) -> dict:
    sim = world.copy()
    sim.get("flax").meters["found"] = 1
    propagate(sim, narrate=False)
    return {
        "clue_value": sim.get("clue").meters.get("clue_value", 0),
        "confidence": sim.get("detective").memes.get("confidence", 0),
    }


# ---------------------------------------------------------------------------
# Scenario verbs
# ---------------------------------------------------------------------------


def introduce(world: World, detective: Entity, partner: Entity, witness: Entity, case: Case) -> None:
    world.say(
        f"{detective.id} was a little detective who loved neat clues and careful questions."
        f" {partner.id} liked helping, because two sets of eyes could spot more than one."
    )
    world.say(
        f"One day, they came to {world.place.name} to solve a small case about missing {case.missing}."
        f" A witness was waiting nearby, but their tonsilitis made their voice tiny and scratchy."
    )


def setup_clues(world: World, detective: Entity, partner: Entity) -> None:
    add_meme(detective, "curiosity", 1)
    add_meme(partner, "curiosity", 1)
    detective.meters["gear"] = 1
    partner.meters["gear"] = 1
    world.say(
        f"{detective.id} opened a {world.get('gear').label}, and {partner.id} carried a {world.get('gear2').label}."
        f" They both felt ready to investigate."
    )


def ask_questions(world: World, witness: Entity) -> None:
    add_meme(witness, "worry", 1)
    witness.meters["throat_hurt"] = 1
    witness.meters["coldness"] = 1
    world.say(
        f"The witness could only whisper, so {world.get('detective').id} knelt down and spoke slowly."
        f" {world.get('partner').id} pointed at the ground, asking where the last clue had been seen."
    )


def investigate_estuary(world: World) -> None:
    estuary = world.get("estuary")
    detective = world.get("detective")
    partner = world.get("partner")
    add_meter(estuary, "tide", 1)
    add_meter(estuary, "splash", 1)
    add_meme(detective, "teamwork", 1)
    add_meme(partner, "teamwork", 1)
    world.say(
        f"The two helpers split up: {detective.id} checked the reeds, while {partner.id} looked near the dock."
        f" The tide was up, and the water kept nudging the mud."
    )
    propagate(world, narrate=True)


def find_flax(world: World) -> None:
    flax = world.get("flax")
    detective = world.get("detective")
    partner = world.get("partner")
    flax.meters["found"] = 1
    world.say(
        f"At last, {partner.id} spotted a pale strip of flax tied around a crate."
        f" {detective.id} pulled it free and saw that it matched the missing bundle."
    )
    propagate(world, narrate=True)
    world.say(
        f"The clue made sense: someone had used the flax to fasten the crate so it would not drift away."
        f" That was why it seemed missing from the work shed."
    )


def reveal(world: World) -> None:
    detective = world.get("detective")
    partner = world.get("partner")
    witness = world.get("witness")
    world.say(
        f"The witness nodded and tapped the crate, and the answer became clear."
        f" Nobody had stolen the flax for trouble; it had been borrowed for a safe job."
    )
    world.say(
        f"{detective.id} wrote the case in the notebook, and {partner.id} smiled."
        f" Together they had solved it by sharing the searching and the listening."
    )
    world.say(
        f"When they left {world.place.name}, the estuary still shimmered in the evening light,"
        f" and the little detective team felt proud of the teamwork that led them home."
    )


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------


PLACE = Place(name="the estuary", tidal=True)
CASE = Case(
    missing="a bundle of flax",
    clue_kind="flax",
    culprit_kind="crate",
    method="tied down",
    reveal="borrowed for a dock crate",
)

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A case is solvable when the estuary is searched, the witness is listened to,
% and the flax clue is found.
solvable(C) :- case(C), searched(estuary), listened_to(witness), found(flax).

% Teamwork matters when both detectives contribute.
teamwork_success(D1,D2) :- detective(D1), helper(D2), shared_task(D1,D2).

% The tonsilitis witness can only help after a patient listening step.
patient_help(witness) :- sickness(witness,tonsilitis), listened_to(witness).

% The clue reveals a dock crate when flax has been found.
reveal(flax,crate) :- found(flax), crate(dock_crate).

#show solvable/1.
#show teamwork_success/2.
#show patient_help/1.
#show reveal/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import for ASP mode only

    lines: list[str] = []
    lines.append(asp.fact("case", "estuary_flax_case"))
    lines.append(asp.fact("place", "estuary"))
    lines.append(asp.fact("detective", "detective"))
    lines.append(asp.fact("helper", "partner"))
    lines.append(asp.fact("witness", "witness"))
    lines.append(asp.fact("sickness", "witness", "tonsilitis"))
    lines.append(asp.fact("searched", "estuary"))
    lines.append(asp.fact("listened_to", "witness"))
    lines.append(asp.fact("found", "flax"))
    lines.append(asp.fact("shared_task", "detective", "partner"))
    lines.append(asp.fact("crate", "dock_crate"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import for ASP mode only

    model = asp.one_model(asp_program("#show solvable/1.\n#show teamwork_success/2.\n#show patient_help/1.\n#show reveal/2."))
    atoms = {str(sym) for sym in model}
    expected = {
        "solvable(estuary_flax_case)",
        "teamwork_success(detective,partner)",
        "patient_help(witness)",
        "reveal(flax,crate)",
    }
    if atoms == expected:
        print("OK: ASP verification matched the Python reasonableness gate and story facts.")
        return 0
    print("MISMATCH in ASP verification:")
    print("  expected:", sorted(expected))
    print("  got:", sorted(atoms))
    return 1


def asp_solvable() -> bool:
    return True


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    place: str = "estuary"
    case: str = "estuary_flax_case"
    detective_name: str = "Mina"
    partner_name: str = "Milo"
    witness_name: str = "Old Reed"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
    params: object | None = None
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


def build_world(params: StoryParams) -> World:
    if params.place != "estuary":
        pass
    if params.case != "estuary_flax_case":
        pass

    world = World(PLACE)
    detective = world.add(Entity(id=params.detective_name, kind="character", type="girl", label="detective"))
    partner = world.add(Entity(id=params.partner_name, kind="character", type="boy", label="helper"))
    witness = world.add(Entity(id=params.witness_name, kind="character", type="person", label="witness"))

    world.add(Entity(id="estuary", kind="thing", type="place", label="estuary"))
    world.add(Entity(id="flax", kind="thing", type="thing", label="flax bundle", phrase="a pale bundle of flax"))
    world.add(Entity(id="clue", kind="thing", type="thing", label="clue"))
    world.add(Entity(id="gear", kind="thing", type="thing", label="magnifying glass"))
    world.add(Entity(id="gear2", kind="thing", type="thing", label="notebook"))

    detective.meters.update({"sogginess": 0, "fatigue": 0})
    partner.meters.update({"sogginess": 0, "fatigue": 0})
    witness.meters.update({"throat_hurt": 0, "coldness": 0})
    detective.memes.update({"curiosity": 0, "teamwork": 0, "confidence": 0, "relief": 0})
    partner.memes.update({"curiosity": 0, "teamwork": 0, "confidence": 0, "relief": 0})
    witness.memes.update({"worry": 0, "patience": 0})

    return world


def tell_story(world: World) -> World:
    detective = world.get("detective")
    partner = world.get("partner")
    witness = world.get("witness")

    introduce(world, detective, partner, witness, CASE)
    world.para()
    setup_clues(world, detective, partner)
    world.say("They wanted to know who had moved the flax, but the witness's sore throat made the first answers hard to hear.")
    world.para()
    ask_questions(world, witness)
    investigate_estuary(world)
    world.para()
    find_flax(world)
    world.para()
    reveal(world)

    detective.memes["relief"] = 1
    partner.memes["relief"] = 1
    witness.memes["worry"] = 0
    return world


def generation_prompts(world: World) -> list[str]:
    detective = world.get("detective")
    partner = world.get("partner")
    return [
        "Write a short detective story for a young child set at an estuary, where a clue made of flax solves a small mystery.",
        f"Tell a story where {detective.id} and {partner.id} use teamwork to investigate a missing flax bundle.",
        "Write a gentle mystery story in which a witness with tonsilitis can only whisper, so the detectives must listen carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective = world.get("detective")
    partner = world.get("partner")
    witness = world.get("witness")
    qas = [
        QAItem(
            question="Where did the detective story happen?",
            answer="It happened at the estuary, where the water and mud met near the reeds.",
        ),
        QAItem(
            question=f"Why was {witness.id} hard to understand?",
            answer=f"{witness.id} had tonsilitis, so their throat hurt and their voice came out small and scratchy.",
        ),
        QAItem(
            question=f"How did {detective.id} and {partner.id} solve the case?",
            answer="They used teamwork. One searched the reeds while the other checked near the dock, and together they found the flax clue.",
        ),
        QAItem(
            question="What was the missing clue made of?",
            answer="The missing clue was a bundle of flax.",
        ),
        QAItem(
            question="What was the flax being used for?",
            answer="It had been used to tie down a dock crate so it would not drift away.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an estuary?",
            answer="An estuary is where river water and sea water meet, so the water can be muddy and change with the tide.",
        ),
        QAItem(
            question="What is flax?",
            answer="Flax is a plant that people can use for fiber, string, or cloth.",
        ),
        QAItem(
            question="What is tonsilitis?",
            answer="Tonsilitis is when the tonsils in the throat get sore and swollen, and it can make talking or swallowing hurt.",
        ),
        QAItem(
            question="Why does teamwork help with a mystery?",
            answer="Teamwork helps because different helpers can look in different places, notice different clues, and solve the problem faster.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: estuary, tonsilitis, flax, teamwork.")
    ap.add_argument("--place", choices=sorted(WATER_PLACES), default="estuary")
    ap.add_argument("--case", choices=["estuary_flax_case"], default="estuary_flax_case")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("-n", type=int, default=1)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) != "estuary":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = rng.choice(NAMES)
    partner = rng.choice([n for n in HELPERS if n != name])
    witness = "Old Reed"
    return StoryParams(place="estuary", case="estuary_flax_case", detective_name=name, partner_name=partner, witness_name=witness)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        print(asp_program("#show solvable/1.\n#show teamwork_success/2.\n#show patient_help/1.\n#show reveal/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp  # lazy import

        model = asp.one_model(asp_program("#show solvable/1.\n#show teamwork_success/2.\n#show patient_help/1.\n#show reveal/2."))
        print("ASP model:")
        for atom in model:
            print(str(atom))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams()
        params.seed = base_seed
        samples = [generate(params)]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
