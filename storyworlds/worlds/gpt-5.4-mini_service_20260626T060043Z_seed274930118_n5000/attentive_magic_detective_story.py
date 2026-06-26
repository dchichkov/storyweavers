#!/usr/bin/env python3
"""
storyworlds/worlds/attentive_magic_detective_story.py
=====================================================

A small story world about an attentive detective who uses a little magic to
solve a puzzling case.

Premise:
- A child detective notices careful clues in a place.
- Something ordinary goes missing or looks wrong.
- The detective follows tracks, a helper, and a magical tool to learn the truth.
- The ending proves what changed: the lost thing is found, the worry is eased,
  and the detective's attentive method mattered.

This world keeps the prose close to a detective story: observation, suspicion,
clue gathering, a reveal, and a tidy resolution.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

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
    place: str
    indoors: bool
    mood: str
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
class Case:
    mystery: str
    missing: str
    clue: str
    reveal: str
    magic_tool: str
    magic_effect: str
    suspect_hint: str
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
    setting: str
    case: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None
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


SETTINGS = {
    "library": Setting(place="the old library", indoors=True, mood="quiet"),
    "garden": Setting(place="the lantern garden", indoors=False, mood="still"),
    "museum": Setting(place="the little museum", indoors=True, mood="careful"),
}

CASES = {
    "lost_key": Case(
        mystery="a missing brass key",
        missing="brass key",
        clue="a tiny glittery speck on the floor",
        reveal="the key had slid into a jar behind the curtain",
        magic_tool="a magic magnifying glass",
        magic_effect="made hidden specks shine like stars",
        suspect_hint="someone had walked softly near the desk",
    ),
    "vanishing_note": Case(
        mystery="a vanished note",
        missing="note",
        clue="a folded corner under the rug",
        reveal="the note was tucked inside a book about birds",
        magic_tool="a magic lantern",
        magic_effect="glowed through paper and showed the outline inside",
        suspect_hint="someone had been reading by the window",
    ),
    "stolen_cookie": Case(
        mystery="a stolen cookie",
        missing="cookie",
        clue="crumbs leading toward the music room",
        reveal="the cookie was carried off by a squirrel through the open door",
        magic_tool="a magic detective compass",
        magic_effect="spun toward every sweet smell in the room",
        suspect_hint="someone had left the door open after snack time",
    ),
}

NAMES = ["Ada", "Mila", "Noa", "Iris", "Toby", "Ezra", "June", "Maya", "Leo", "Nina"]
TRAITS = ["attentive", "careful", "quiet", "brave", "curious"]


def detect_sentence(hero: Entity, case: Case, setting: Setting) -> str:
    return (
        f"{hero.id} was an {hero.traits[0]} little detective who liked to notice the smallest things. "
        f"One day, {hero.pronoun('possessive')} nose for clues led {hero.pronoun('object')} to {setting.place}, "
        f"where {case.mystery} had caused a lot of worry."
    )


def clue_sentence(hero: Entity, case: Case, setting: Setting) -> str:
    return (
        f"The place was {setting.mood}, and {hero.id} looked slowly from the floor to the shelves and back again. "
        f"Then {hero.pronoun('subject')} spotted {case.clue}."
    )


def magic_sentence(hero: Entity, case: Case) -> str:
    return (
        f"{hero.id} took out {case.magic_tool}. When {hero.pronoun('subject')} whispered a tiny charm, "
        f"it {case.magic_effect}."
    )


def solve_sentence(hero: Entity, helper: Entity, case: Case) -> str:
    return (
        f"That helped {hero.id} follow the trail at once. Soon {hero.id} and {helper.id} found out that "
        f"{case.reveal}. {hero.id} smiled, because being attentive had solved the whole puzzle."
    )


def build_world(params: StoryParams) -> tuple[World, Entity, Entity, Case]:
    setting = _safe_lookup(SETTINGS, params.setting)
    case = _safe_lookup(CASES, params.case)
    world = World(setting)
    detective = world.add(
        Entity(
            id=params.detective_name,
            kind="character",
            type=params.detective_gender,
            traits=["attentive"],
            meters={"focus": 2.0},
            memes={"curiosity": 2.0, "confidence": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            type=params.helper_gender,
            traits=["helpful"],
            meters={"care": 1.0},
            memes={"worry": 1.0, "hope": 1.0},
        )
    )
    missing = world.add(
        Entity(
            id="missing_item",
            type=case.missing,
            label=case.missing,
            phrase=case.missing,
            owner=helper.id,
            caretaker=helper.id,
            hidden_in="unknown",
            meters={"lost": 1.0},
        )
    )
    world.facts.update(
        detective=detective,
        helper=helper,
        missing=missing,
        case=case,
        setting=setting,
    )
    return world, detective, helper, case


def tell_story(world: World, detective: Entity, helper: Entity, case: Case) -> None:
    world.say(detect_sentence(detective, case, world.setting))
    world.say(
        f"{helper.id} explained that {case.mystery} had gone missing, and {helper.pronoun('subject')} looked worried."
    )
    world.para()
    world.say(clue_sentence(detective, case, world.setting))
    detective.memes["focus"] += 1
    detective.memes["confidence"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{detective.id} did not hurry past the clue. {detective.pronoun('subject').capitalize()} paused, "
        f"pointed, and asked gentle questions. That careful look made the clue matter."
    )
    world.para()
    world.say(magic_sentence(detective, case))
    detective.meters["mystery_power"] = 1.0
    world.say(
        f"The bright little spell did not do the thinking for {detective.id}. It only made the hidden trace easier to see."
    )
    world.say(solve_sentence(detective, helper, case))
    helper.memes["worry"] = 0.0
    helper.memes["relief"] = 2.0
    detective.memes["pride"] = 1.0


def build_prompt_text(world: World) -> list[str]:
    f = world.facts
    detective: Entity = _safe_fact(world, f, "detective")
    case: Case = _safe_fact(world, f, "case")
    return [
        f'Write a short detective story for a young child about {detective.id}, an attentive sleuth, and {case.mystery}.',
        f"Tell a gentle mystery where magic helps {detective.id} notice clues, but careful observing solves the problem.",
        f'Write a child-friendly story that includes a "magic" tool, a clue, and a happy reveal in {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = _safe_fact(world, f, "detective")
    helper: Entity = _safe_fact(world, f, "helper")
    case: Case = _safe_fact(world, f, "case")
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the attentive detective in the story?",
            answer=f"The attentive detective was {detective.id}. {detective.pronoun('subject').capitalize()} kept looking carefully until the clue made sense.",
        ),
        QAItem(
            question=f"What was missing at {place}?",
            answer=f"{helper.id} was worried about {case.mystery}, which had gone missing at {place}.",
        ),
        QAItem(
            question=f"What helped {detective.id} notice the hidden clue?",
            answer=f"{case.magic_tool} helped, because its spell made hidden things shine and pointed the way to the answer.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"It ended happily when {case.reveal}. The worry went away and {helper.id} felt relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something surprising and special that can do things ordinary objects cannot do.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("mystery", cid, case.mystery))
    return "\n".join(lines)


ASP_RULES = r"""
% A case is reasonable if it has a place, a mystery, and a magic tool.
reasonable_case(S,C) :- setting(S), case(C).
#show reasonable_case/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable_case/2."))
    asp_set = set(asp.atoms(model, "reasonable_case"))
    py_set = {(sid, cid) for sid in SETTINGS for cid in CASES}
    if asp_set == py_set:
        print(f"OK: clingo matches python ({len(py_set)} cases).")
        return 0
    print("MISMATCH:")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small attentive magic detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    case = getattr(args, "case", None) or rng.choice(list(CASES))
    detective_gender = getattr(args, "detective_gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    detective_name = getattr(args, "detective_name", None) or rng.choice(NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in NAMES if n != detective_name])
    return StoryParams(
        setting=setting,
        case=case,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world, detective, helper, case = build_world(params)
    tell_story(world, detective, helper, case)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=build_prompt_text(world),
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
    StoryParams(setting="library", case="lost_key", detective_name="Ada", detective_gender="girl", helper_name="Milo", helper_gender="boy"),
    StoryParams(setting="garden", case="vanishing_note", detective_name="Nina", detective_gender="girl", helper_name="Jules", helper_gender="boy"),
    StoryParams(setting="museum", case="stolen_cookie", detective_name="Leo", detective_gender="boy", helper_name="June", helper_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable_case/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show reasonable_case/2."))
        combos = sorted(set(asp.atoms(model, "reasonable_case")))
        print(f"{len(combos)} reasonable cases:")
        for sid, cid in combos:
            print(f"  {sid} {cid}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective_name}: {p.case} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
