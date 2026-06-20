#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/actual_literate_dither_conflict_moral_value_humor.py
=====================================================================================

A small detective-story world for child-friendly mystery tales with conflict,
moral value, and a bit of humor. The premise is simple: someone loses an actual
object, a literate little sleuth reads clues, and a dithering suspect delays the
truth until the case resolves with a clear moral turn.

The world model uses physical meters and emotional memes, drives prose from
state changes, and supports a Python reasonableness gate plus an inline ASP twin.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not isinstance(self.meters, dict):
            self.meters = dict(self.meters)
        if not isinstance(self.memes, dict):
            self.memes = dict(self.memes)

    def m(self, key: str) -> float:
        return float(self.meters.get(key, 0.0))

    def n(self, key: str) -> float:
        return float(self.memes.get(key, 0.0))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    afford: set[str]

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
class CaseItem:
    id: str
    label: str
    value: str
    owner: str
    easy_to_misplace: bool = False

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
class ClueSource:
    id: str
    label: str
    reveal: str
    honest: bool = True
    sense: int = 3

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
class Response:
    id: str
    sense: int
    method: str
    fail: str
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


def _r_embarrass(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("trouble", 0.0) < THRESHOLD:
            continue
        sig = ("embarrass", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fluster"] = e.memes.get("fluster", 0.0) + 1
        out.append("__humor__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("argument") and not world.facts.get("resolved"):
        sig = ("conflict", "case")
        if sig not in world.fired:
            world.fired.add(sig)
            for e in list(world.entities.values()):
                if e.role in {"sleuth", "witness", "suspect"}:
                    e.memes["tense"] = e.memes.get("tense", 0.0) + 1
            out.append("__conflict__")
    return out


CAUSAL_RULES = [
    Rule("embarrass", "social", _r_embarrass),
    Rule("conflict", "social", _r_conflict),
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


def reasonable_case(item: CaseItem, setting: Setting) -> bool:
    return item.easy_to_misplace and setting.id in {"library", "station", "classroom", "museum"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for cid, c in CASE_ITEMS.items():
            for rid, r in RESPONSES.items():
                if reasonable_case(c, SETTINGS[sid]) and r.sense >= SENSE_MIN:
                    combos.append((sid, cid, rid))
    return combos


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict_world(world: World, case_id: str) -> dict:
    sim = world.copy()
    _misplace(sim, sim.get("suspect"), sim.get(case_id), narrate=False)
    return {
        "trouble": sim.get(case_id).meters.get("trouble", 0.0),
        "conflict": sim.get("sleuth").memes.get("tense", 0.0),
    }


def _misplace(world: World, suspect: Entity, item: Entity, narrate: bool = True) -> None:
    item.meters["missing"] = 1.0
    item.meters["trouble"] = 1.0
    suspect.memes["dither"] = suspect.memes.get("dither", 0.0) + 1
    propagate(world, narrate=narrate)


def setup(world: World, sleuth: Entity, witness: Entity, suspect: Entity, case: Entity, setting: Setting) -> None:
    sleuth.memes["curious"] = sleuth.memes.get("curious", 0.0) + 1
    witness.memes["worry"] = witness.memes.get("worry", 0.0) + 1
    world.say(
        f"On a bright afternoon, {sleuth.id} and {witness.id} were at {setting.place}, "
        f"where small mysteries loved to hide."
    )
    world.say(
        f"{case.value.capitalize()} was the actual thing everyone was looking for, and "
        f"{sleuth.id} had a literate notebook full of neat clues."
    )


def incident(world: World, suspect: Entity, case: Entity) -> None:
    world.say(
        f"Then {suspect.id} started to dither, peeking under chairs and behind coats "
        f"without saying where {case.label_word if case.label_word else 'it'} had gone."
    )
    world.say(
        f'"I, um, maybe saw something," {suspect.id} mumbled, and the answer got smaller '
        f"each time {suspect.pronoun()} tried to say it."
    )


def warning(world: World, sleuth: Entity, witness: Entity, suspect: Entity, case: Entity) -> None:
    pred = predict_world(world, case.id)
    world.facts["predicted_trouble"] = pred["trouble"]
    world.say(
        f'{sleuth.id} tapped the notebook. "The clue trail says the actual {case.label} '
        f"is close by. If we keep dithering, everyone will get more worried."
    )
    if pred["trouble"] >= THRESHOLD:
        world.say(
            f'{witness.id} nodded. "And the room already feels tense," {witness.pronoun()} '
            f"said. The case needed an honest answer, not more hiding."
        )


def resolve_case(world: World, sleuth: Entity, witness: Entity, suspect: Entity,
                 case: CaseItem, response: Response) -> None:
    world.facts["resolved"] = True
    suspect.memes["dither"] = 0.0
    suspect.memes["relief"] = suspect.memes.get("relief", 0.0) + 1
    case_ent = world.get(case.id)
    case_ent.meters["missing"] = 0.0
    case_ent.meters["found"] = 1.0
    world.say(
        f"In the end, {sleuth.id} used {response.method}, and {suspect.id} finally told "
        f"the actual truth."
    )
    world.say(
        f"The missing {case.label} turned up in the silliest spot, right where everyone "
        f"had already looked twice."
    )


def moral_close(world: World, sleuth: Entity, witness: Entity, suspect: Entity) -> None:
    for e in (sleuth, witness, suspect):
        e.memes["warmth"] = e.memes.get("warmth", 0.0) + 1
    world.say(
        f'{sleuth.id} laughed softly. "A good detective is honest, patient, and literate '
        f'enough to read the clues before leaping to conclusions."'
    )
    world.say(
        f'{suspect.id} smiled, embarrassed but glad, and promised not to dither when a '
        f"simple truth would do."
    )
    world.say(
        f"By sunset, the case was closed, the notebook was full, and the whole room felt "
        f"lighter."
    )


def tell(setting: Setting, case: CaseItem, response: Response,
         sleuth_name: str = "Mina", sleuth_gender: str = "girl",
         witness_name: str = "Owen", witness_gender: str = "boy",
         suspect_name: str = "Pip", suspect_gender: str = "boy") -> World:
    world = World(setting)
    sleuth = world.add(Entity(id=sleuth_name, kind="character", type=sleuth_gender, role="sleuth"))
    witness = world.add(Entity(id=witness_name, kind="character", type=witness_gender, role="witness"))
    suspect = world.add(Entity(id=suspect_name, kind="character", type=suspect_gender, role="suspect"))
    case_ent = world.add(Entity(id=case.id, kind="thing", type="thing", label=case.label))
    case_ent.meters["found"] = 0.0
    case_ent.meters["missing"] = 0.0

    setup(world, sleuth, witness, suspect, case_ent, setting)
    world.para()
    incident(world, suspect, case_ent)
    warning(world, sleuth, witness, suspect, case)
    world.facts["argument"] = True
    propagate(world, narrate=False)
    world.para()
    resolve_case(world, sleuth, witness, suspect, case, response)
    moral_close(world, sleuth, witness, suspect)
    world.facts.update(
        setting=setting,
        case=case,
        response=response,
        sleuth=sleuth,
        witness=witness,
        suspect=suspect,
        outcome="resolved",
    )
    return world


SETTINGS = {
    "library": Setting("library", "the old library", "quiet", {"casebook", "lost"}),
    "station": Setting("station", "the train station", "busy", {"casebook", "lost"}),
    "classroom": Setting("classroom", "the classroom", "bright", {"casebook", "lost"}),
    "museum": Setting("museum", "the museum hall", "echoing", {"casebook", "lost"}),
}

CASE_ITEMS = {
    "glasses": CaseItem("case", "actual glasses", "actual glasses", "Pip", True),
    "badge": CaseItem("case", "actual badge", "actual badge", "Pip", True),
    "book": CaseItem("case", "actual book", "actual book", "Pip", True),
}

RESPONSES = {
    "ask_kindly": Response("ask_kindly", 3, "asked one kind question", "asked too sharply"),
    "check_notes": Response("check_notes", 3, "checked the notes again", "checked the wrong page"),
    "follow_clue": Response("follow_clue", 2, "followed the clearest clue", "followed a silly clue"),
}

GIRL_NAMES = ["Mina", "Ruby", "Ivy", "June", "Nina", "Elsa"]
BOY_NAMES = ["Owen", "Theo", "Pip", "Ezra", "Luca", "Noah"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    case: str
    response: str
    sleuth: str
    sleuth_gender: str
    witness: str
    witness_gender: str
    suspect: str
    suspect_gender: str
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


KNOWLEDGE = {
    "library": [("What is a library?", "A library is a place full of books where people read and learn quietly.")],
    "detective": [("What does a detective do?", "A detective looks for clues and tries to solve a mystery.")],
    "notebook": [("Why does a detective use a notebook?", "A notebook helps a detective remember clues, names, and important facts.")],
    "truth": [("Why is it good to tell the truth?", "Telling the truth helps people solve problems and trust each other.")],
    "dither": [("What does it mean to dither?", "To dither means to hesitate and keep wavering instead of deciding.")],
}

KNOWLEDGE_ORDER = ["library", "detective", "notebook", "truth", "dither"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the words "actual", "literate", and "dither".',
        f"Tell a funny mystery about {f['sleuth'].id}, a literate little detective, who solves a case without being mean.",
        f"Write a short story where a child dithers about a missing {f['case'].label}, but the honest clue trail wins in the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sleuth, witness, suspect = f["sleuth"], f["witness"], f["suspect"]
    case: CaseItem = f["case"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {sleuth.id}, {witness.id}, and {suspect.id} solving a little mystery together."
        ),
        QAItem(
            question="What was missing?",
            answer=f"The actual {case.label} was missing, so everyone had to look carefully and tell the truth."
        ),
        QAItem(
            question="Why did the case become a conflict?",
            answer=f"{suspect.id} kept dithering and not saying the honest answer. That made the others tense, because the clue trail could not finish until someone was truthful."
        ),
        QAItem(
            question="How did the detective solve it?",
            answer=f"{sleuth.id} read the clues from a literate notebook, asked a kind question, and used patience instead of yelling. That helped {suspect.id} stop dithering and point to the real hiding place."
        ),
        QAItem(
            question="What was the moral of the story?",
            answer="Be honest, read the clues carefully, and do not dither when the truth can help everyone."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["setting"].id, "detective", "notebook", "truth", "dither"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, case: CaseItem) -> str:
    return (
        f"(No story: this setting is not a good detective-world fit for {case.label}. "
        f"Pick a place where a missing thing can plausibly hide and spark a clue chase.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def outcome_of(params: StoryParams) -> str:
    return "resolved"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CASE_ITEMS.items():
        lines.append(asp.fact("case", cid))
        if c.easy_to_misplace:
            lines.append(asp.fact("easy_to_misplace", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,C) :- setting(S), case(C), easy_to_misplace(C), sensible(_).
"""

def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, case=None, response=None,
                                                             sleuth=None, sleuth_gender=None,
                                                             witness=None, witness_gender=None,
                                                             suspect=None, suspect_gender=None),
                                          random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: ASP parity and generate() smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with actual clues, literate notes, and a dithered confession.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASE_ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--witness")
    ap.add_argument("--suspect")
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
    if args.setting and args.case:
        if not reasonable_case(CASE_ITEMS[args.case], SETTINGS[args.setting]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], CASE_ITEMS[args.case]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.case is None or c[1] == args.case)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, case, response = rng.choice(sorted((s, c, r) for s, c, r in combos if args.response is None or r == args.response))
    sleuth_gender = "girl"
    witness_gender = "boy"
    suspect_gender = "boy"
    return StoryParams(setting, case, response,
                       args.name or rng.choice(GIRL_NAMES),
                       sleuth_gender,
                       args.witness or rng.choice(BOY_NAMES),
                       witness_gender,
                       args.suspect or rng.choice(BOY_NAMES),
                       suspect_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CASE_ITEMS[params.case], RESPONSES[params.response],
                 params.sleuth, params.sleuth_gender, params.witness, params.witness_gender,
                 params.suspect, params.suspect_gender)
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
    StoryParams("library", "glasses", "ask_kindly", "Mina", "girl", "Owen", "boy", "Pip", "boy"),
    StoryParams("museum", "badge", "check_notes", "June", "girl", "Theo", "boy", "Pip", "boy"),
    StoryParams("classroom", "book", "follow_clue", "Ruby", "girl", "Luca", "boy", "Noah", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"valid combos: {len(asp_valid_combos())}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
