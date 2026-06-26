#!/usr/bin/env python3
"""
A small rhyming story world about a child resisting medicine, a worried helper,
and a gentle conflict that resolves with a smarter sip.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caregiver: object | None = None
    child: object | None = None
    medicine: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nurse"}
        male = {"boy", "father", "dad", "man", "doctor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    indoors: bool = True
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
class Medicine:
    id: str
    label: str
    phrase: str
    taste: str
    help: str
    sweetness: str
    color: str
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
class ConflictBeat:
    resisted_verb: str
    reason: str
    softening: str
    resolution: str
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
    place: str
    medicine: str
    child_name: str
    child_type: str
    caregiver_type: str
    caregiver_name: str
    seed: Optional[int] = None
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
    "kitchen": Setting(place="the kitchen", indoors=True),
    "bedroom": Setting(place="the bedroom", indoors=True),
    "clinic": Setting(place="the clinic", indoors=True),
    "living_room": Setting(place="the living room", indoors=True),
}

MEDICINES = {
    "cherry_syrup": Medicine(
        id="cherry_syrup",
        label="cherry syrup medicine",
        phrase="a spoon of cherry syrup medicine",
        taste="sweet and cherry",
        help="help the fever feel less severe",
        sweetness="sweet as a berry treat",
        color="red",
    ),
    "honey_mint": Medicine(
        id="honey_mint",
        label="honey mint medicine",
        phrase="a tiny cup of honey mint medicine",
        taste="soft and minty",
        help="help the cough calm down",
        sweetness="sweet and cool",
        color="gold",
    ),
    "apple_drops": Medicine(
        id="apple_drops",
        label="apple drops medicine",
        phrase="apple drops medicine",
        taste="apple-bright",
        help="help the tummy feel better",
        sweetness="sweet like a crisp apple",
        color="green",
    ),
}

BEATS = {
    "cherry_syrup": ConflictBeat(
        resisted_verb="resist the red spoon",
        reason="the spoon looked too strange and too red",
        softening="the caregiver added a straw and a tiny smile",
        resolution="the child sipped it down and the fuss was gone",
    ),
    "honey_mint": ConflictBeat(
        resisted_verb="resist the little cup",
        reason="the cup smelled odd at first",
        softening="the caregiver let the child sniff it and count to three",
        resolution="the child drank it in one brave gulp",
    ),
    "apple_drops": ConflictBeat(
        resisted_verb="resist the apple drops",
        reason="the drops were small and new and not a snack to hold",
        softening="the caregiver mixed them with juice and gave a gentle nod",
        resolution="the child took the dose and felt much more okay",
    ),
}

CHILD_NAMES = ["Mia", "Nora", "Luca", "Ben", "Tia", "Iris", "Owen", "Zoe"]
CAREGIVER_NAMES = ["Mom", "Dad", "Nana", "Papa", "Nurse Joy", "Dr. Lee"]


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}"


def intro_line(child: Entity, medicine: Medicine, setting: Setting) -> str:
    return (
        f"{child.id} had a sore-day snore in {setting.place}, "
        f"and {child.pronoun('possessive')} {medicine.label} waited there with care."
    )


def conflict_line(child: Entity, caregiver: Entity, medicine: Medicine, beat: ConflictBeat) -> str:
    return (
        f"But {child.id} would resist, and make a grumpy twist; "
        f"{beat.reason}, said {caregiver.id}, with a worried wrist."
    )


def turn_line(child: Entity, caregiver: Entity, medicine: Medicine, beat: ConflictBeat) -> str:
    return (
        f"Then {beat.softening}, so the room felt light; "
        f"the medicine looked less scary and a little more right."
    )


def ending_line(child: Entity, caregiver: Entity, medicine: Medicine, beat: ConflictBeat) -> str:
    return (
        f"At last {child.id} chose to sip, and the conflict drifted away; "
        f"{beat.resolution}, and the day grew bright and gay."
    )


def generate_story(world: World) -> str:
    child = world.get("child")
    caregiver = world.get("caregiver")
    med = world.get("medicine")
    beat = _safe_fact(world, world.facts, "beat")

    world.say(intro_line(child, med, world.setting))
    world.say(
        f"{caregiver.id} said, “This {med.taste} {med.label} will help you feel well, "
        f"and make your rough cough stop that spell.”"
    )
    world.para()
    world.say(conflict_line(child, caregiver, med, beat))
    world.say(
        f"{child.id} crossed {child.pronoun('possessive')} arms and wanted to hide; "
        f"the medicine cup sat by the bed, like a tiny tide."
    )
    world.para()
    world.say(turn_line(child, caregiver, med, beat))
    world.say(
        f"{caregiver.id} stayed kind and close, with a patient grin; "
        f"the small cup came back with a gentler spin."
    )
    world.para()
    world.say(ending_line(child, caregiver, med, beat))
    world.say(
        f"Then {child.id} smiled with a rosy glow, and the {med.color} medicine "
        f"helped the whole room flow."
    )
    return world.render()


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    med = _safe_lookup(MEDICINES, params.medicine)
    beat = _safe_lookup(BEATS, params.medicine)
    world = World(setting)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        label=params.child_name,
        meters={"sick": 1.0},
        memes={"resist": 1.0, "worry": 1.0},
    ))
    caregiver = world.add(Entity(
        id=params.caregiver_name,
        kind="character",
        type=params.caregiver_type,
        label=params.caregiver_name,
        meters={"care": 1.0},
        memes={"hope": 1.0},
    ))
    medicine = world.add(Entity(
        id=med.id,
        kind="thing",
        type="medicine",
        label=med.label,
        phrase=med.phrase,
        owner=caregiver.id,
        caretaker=caregiver.id,
        meters={"ready": 1.0},
    ))
    world.add(child)
    world.add(caregiver)
    world.add(medicine)
    world.facts.update(
        child=child,
        caregiver=caregiver,
        medicine=med,
        beat=beat,
        setting=setting,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    caregiver = _safe_fact(world, world.facts, "caregiver")
    med = _safe_fact(world, world.facts, "medicine")
    beat = _safe_fact(world, world.facts, "beat")
    return [
        QAItem(
            question=f"Who had to resist the medicine in the story?",
            answer=f"{child.id} had to resist the medicine at first because it seemed strange."
        ),
        QAItem(
            question=f"Why did {child.id} and {caregiver.id} have a conflict?",
            answer=(
                f"They had a conflict because {child.id} did not want to take "
                f"{med.label} right away, even though {caregiver.id} wanted to help."
            ),
        ),
        QAItem(
            question=f"How did the story solve the conflict?",
            answer=(
                f"The conflict softened when {beat.softening.lower()}, and then "
                f"{child.id} drank the medicine and felt better."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    med = _safe_fact(world, world.facts, "medicine")
    return [
        QAItem(
            question="What is medicine for?",
            answer="Medicine is something people take to help their bodies feel better when they are sick or hurt."
        ),
        QAItem(
            question="Why might a child resist medicine?",
            answer="A child might resist medicine because it can taste strange, look unfamiliar, or feel too different from a snack."
        ),
        QAItem(
            question=f"What does {med.label} do in this story world?",
            answer=f"It is meant to help the child feel better, and it is made to sound gentle and not too scary."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    child = _safe_fact(world, world.facts, "child")
    caregiver = _safe_fact(world, world.facts, "caregiver")
    med = _safe_fact(world, world.facts, "medicine")
    return [
        f'Write a short rhyming story about {child.id} who resists medicine but learns to trust {caregiver.id}.',
        f'Create a gentle tale where the word "resist" appears and a child accepts {med.label} after a conflict.',
        f'Tell a child-friendly rhyming story about medicine, worry, and a caring helper who solves the problem.',
    ]


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
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, med in MEDICINES.items():
        lines.append(asp.fact("medicine", mid))
        lines.append(asp.fact("helps", mid, med.help.replace(" ", "_")))
        lines.append(asp.fact("tastes", mid, med.taste.replace(" ", "_")))
    for bid in BEATS:
        lines.append(asp.fact("beat", bid))
    return "\n".join(lines)


ASP_RULES = r"""
resist_conflict(M) :- medicine(M).
resolved(M) :- medicine(M), resist_conflict(M).

#show resist_conflict/1.
#show resolved/1.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: resist medicine, conflict, and a gentle fix.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--medicine", choices=sorted(MEDICINES))
    ap.add_argument("--name")
    ap.add_argument("--caregiver-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--caregiver-type", choices=["mother", "father", "nurse", "doctor"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    medicine = getattr(args, "medicine", None) or rng.choice(list(MEDICINES))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    caregiver_type = getattr(args, "caregiver_type", None) or rng.choice(["mother", "father", "nurse", "doctor"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    caregiver_name = getattr(args, "caregiver_name", None) or rng.choice(CAREGIVER_NAMES)
    return StoryParams(
        place=place,
        medicine=medicine,
        child_name=name,
        child_type=child_type,
        caregiver_type=caregiver_type,
        caregiver_name=caregiver_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in SETTINGS:
            for medicine in MEDICINES:
                params = StoryParams(
                    place=place,
                    medicine=medicine,
                    child_name=_safe_lookup(CHILD_NAMES, 0),
                    child_type="girl",
                    caregiver_type="mother",
                    caregiver_name=_safe_lookup(CAREGIVER_NAMES, 0),
                )
                samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
