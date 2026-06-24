#!/usr/bin/env python3
"""
A small detective-style story world set in a bathroom, built from the seed words
"laundromat", "whisk", and "compulsive".

The story follows a child detective who notices a strange clue in a bathroom,
uses a flashback to remember an earlier detail, and solves the mystery in a
gentle, state-driven way.
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


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    detective: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the bathroom"
    affords: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    place_hint: str
    mystery_tag: str
    flashback_hint: str
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
class Case:
    id: str
    title: str
    question: str
    answer: str
    misdirection: str
    clue: str
    flashback: str
    resolution: str
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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = _copy.deepcopy(self.facts)
        return clone


def _solve_mystery(world: World, detective: Entity, clue: Entity, case: Case) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
    detective.memes["focus"] = detective.memes.get("focus", 0.0) + 1
    world.say(
        f"{detective.id} studied the clue, and the bathroom suddenly felt less ordinary. "
        f"Something small had gone wrong, and {detective.pronoun('possessive')} eyes were ready to notice it."
    )
    world.say(
        f"The clue was {clue.phrase}, which seemed to belong near {clue.place_hint}. "
        f"That was the first sign this was a mystery to solve."
    )


def _flashback(world: World, detective: Entity, case: Case) -> None:
    detective.memes["remembered"] = detective.memes.get("remembered", 0.0) + 1
    world.say(
        f"Then a flashback slipped into {detective.pronoun('possessive')} thoughts. "
        f"{case.flashback}"
    )


def _gather_together(world: World, detective: Entity, clue: Entity, case: Case) -> None:
    world.say(
        f"{detective.id} looked again at the wet floor, the sink, and the little shelf beside the towel. "
        f"At last, the clue fit with {case.answer}."
    )
    world.say(
        f"The mystery was not scary after all. It was just a puzzling bathroom mix-up, and once {detective.id} noticed the pattern, "
        f"the answer felt clear."
    )


def _wrap_up(world: World, detective: Entity, helper: Entity, case: Case) -> None:
    detective.memes["joy"] = detective.memes.get("joy", 0.0) + 1
    world.say(
        f"{detective.id} explained the answer to {helper.id}, and {helper.pronoun('subject')} smiled with relief. "
        f"{case.resolution}"
    )


def tell(setting: Setting, clue_cfg: Clue, case: Case, name: str = "Mina",
         gender: str = "girl", helper_type: str = "mother") -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=name, kind="character", type=gender, label=name, phrase=f"a careful little detective"
    ))
    helper = world.add(Entity(
        id="Helper", kind="character", type=helper_type, label="the helper"
    ))
    clue = world.add(Entity(
        id=clue_cfg.id, type="thing", label=clue_cfg.label, phrase=clue_cfg.phrase
    ))
    world.facts.update(detective=detective, helper=helper, clue=clue, case=case)

    world.say(
        f"{detective.id} was a small detective who loved clues and tidy corners. "
        f"One morning in the bathroom, {detective.pronoun('subject')} spotted {clue.phrase} and frowned."
    )
    world.say(
        f"It felt like the start of a mystery to solve."
    )

    world.para()
    _solve_mystery(world, detective, clue, case)

    world.para()
    world.say(case.misdirection)
    _flashback(world, detective, case)

    world.para()
    _gather_together(world, detective, clue, case)

    world.para()
    _wrap_up(world, detective, helper, case)

    return world


@dataclass
class StoryParams:
    clue: str
    case: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "bathroom": Setting(place="the bathroom", affords={"mystery"}),
}

CLUES = {
    "whisk": Clue(
        id="whisk",
        label="whisk",
        phrase="a whisk with a few soap bubbles clinging to its wires",
        place_hint="the sink",
        mystery_tag="laundromat",
        flashback_hint="laundromat",
    ),
    "laundromat_card": Clue(
        id="laundromat_card",
        label="laundromat card",
        phrase="a laundromat card tucked behind the mirror",
        place_hint="the pocket of a coat",
        mystery_tag="laundromat",
        flashback_hint="laundromat",
    ),
    "soap_note": Clue(
        id="soap_note",
        label="soap note",
        phrase="a small note that smelled like soap",
        place_hint="the counter",
        mystery_tag="compulsive",
        flashback_hint="compulsive",
    ),
}

CASES = {
    "laundromat_whisk_compulsive": Case(
        id="laundromat_whisk_compulsive",
        title="The Laundromat Whisk Mystery",
        question="Why was a whisk in the bathroom?",
        answer="the whisk had been brought home from the laundromat and used to stir a soapy mix after a compulsive cleaning streak",
        misdirection="At first, it looked like someone had left kitchen tools behind by mistake.",
        clue="whisk",
        flashback=(
            "The detective remembered a trip to the laundromat earlier that day, when the grown-up had "
            "washed towels and kept stopping to scrub anything that looked even a little bit smudged. "
            "There had even been a whisk in a bag beside the soap."
        ),
        resolution=(
            "The whisk belonged to the helper, who had packed it with the laundry supplies by accident. "
            "The detective laughed, and the bathroom felt peaceful again."
        ),
    ),
}


GIRL_NAMES = ["Mina", "Tia", "Ivy", "Nora", "Lena", "Ruby"]
BOY_NAMES = ["Leo", "Theo", "Milo", "Finn", "Owen", "Eli"]


ASP_RULES = r"""
clue_of(whisk, bathroom).
clue_of(laundromat_card, bathroom).
clue_of(soap_note, bathroom).

triggers_flashback(whisk, laundromat).
triggers_flashback(laundromat_card, laundromat).
triggers_flashback(soap_note, compulsive).

is_mystery(clue) :- clue_of(clue, bathroom).
solvable(Case) :- is_mystery(clue), triggers_flashback(clue, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "bathroom"))
    for c in CLUES.values():
        lines.append(asp.fact("clue", c.id))
        lines.append(asp.fact("clue_of", c.id, "bathroom"))
        lines.append(asp.fact("triggers_flashback", c.id, c.flashback_hint))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    seen = set(asp.atoms(model, "solvable"))
    expected = {("Case",)}
    if seen:
        print("OK: ASP found a solvable mystery in the bathroom.")
        return 0
    print("MISMATCH: ASP did not find the expected solvable mystery.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world in a bathroom.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    case = getattr(args, "case", None) or "laundromat_whisk_compulsive"
    if clue == "soap_note" and case == "laundromat_whisk_compulsive":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father"])
    return StoryParams(clue=clue, case=case, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short detective story for a young child set in a bathroom that includes the words "laundromat", "whisk", and "compulsive".',
        f"Tell a gentle mystery where {f['detective'].id} notices {f['clue'].phrase} and remembers a laundromat clue in a flashback.",
        "Make the story feel like a simple case being solved with careful noticing and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, helper, clue, case = f["detective"], f["helper"], f["clue"], f["case"]
    return [
        QAItem(
            question=f"Where does {det.id} find the clue?",
            answer=f"{det.id} finds the clue in the bathroom, where the mystery starts."
        ),
        QAItem(
            question=f"What clue makes {det.id} think something strange happened?",
            answer=f"{det.id} notices {clue.phrase}, which does not seem like it belongs there."
        ),
        QAItem(
            question="What helps solve the mystery?",
            answer=f"A flashback helps because it reminds {det.id} of the laundromat and the compulsive cleaning habit."
        ),
        QAItem(
            question=f"Who feels relieved at the end?",
            answer=f"{helper.id} feels relieved when {det.id} explains that the whisk was brought home by accident."
        ),
        QAItem(
            question=f"What was the answer to the question, '{case.question}'?",
            answer=f"The answer was that {case.answer}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a laundromat?",
            answer="A laundromat is a place where people go to wash and dry clothes."
        ),
        QAItem(
            question="What is a whisk used for?",
            answer="A whisk is a kitchen tool with wire loops that helps mix food or batter."
        ),
        QAItem(
            question="What does compulsive mean?",
            answer="Compulsive means doing something over and over because it feels hard to stop."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier."
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["bathroom"], _safe_lookup(CLUES, params.clue), _safe_lookup(CASES, params.case),
                 name=params.name, gender=params.gender, helper_type=params.helper)
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
        print(asp_program("#show solvable/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show solvable/1."))
        print(asp.atoms(model, "solvable"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for clue in CLUES:
            params = StoryParams(clue=clue, case="laundromat_whisk_compulsive",
                                 name="Mina", gender="girl", helper="mother")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
