#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gown_gruesome_dentist_transformation_animal_story.py
====================================================================================

A small animal-story world about a worried animal, a strange dentist visit, a
gown, and a transformation that turns a gruesome mess into a neat, brave ending.

The seed words are woven in directly:
- gown
- gruesome
- dentist

The world is built as a tiny causal simulation with typed entities, physical
meters, emotional memes, a reasonableness gate, and an inline ASP twin.

Premise
-------
An animal arrives at the dentist in a gown because something in its mouth looks
gruesome. The dentist helps, a careful transformation happens, and the animal
leaves changed: cleaned up, calmer, and smiling.

The world intentionally stays small and child-facing. The transformation is not
magic for its own sake; it is the simulated state change from fearful, messy,
gruesome-to-look-at teeth into a bright, healthy smile after treatment.
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
SENSE_MIN = 2
FEAR_LIMIT = 6.0


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
    nervous: bool = False
    caring: bool = False
    shiny: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cat", "rabbit", "fox", "squirrel"}
        male = {"boy", "father", "dad", "man", "dog", "bear", "lion", "mouse"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class AnimalKind:
    id: str
    label: str
    sound: str
    habitat: str
    coat: str
    plural: bool = False
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
class Place:
    id: str
    label: str
    adjective: str
    has_chair: bool = True
    has_light: bool = True
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
class Concern:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    treatment: str
    reveal: str
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
class Transformation:
    id: str
    label: str
    before: str
    after: str
    change: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["pain"] >= THRESHOLD and ("fear", e.id) not in world.fired:
            world.fired.add(("fear", e.id))
            e.memes["fear"] += 1
            out.append("")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    patient = world.get("patient")
    if patient.meters["treated"] >= THRESHOLD and ("transform", patient.id) not in world.fired:
        world.fired.add(("transform", patient.id))
        patient.meters["clean"] = 1.0
        patient.meters["pain"] = 0.0
        patient.meters["smile"] = 1.0
        patient.memes["relief"] += 2
        patient.memes["joy"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("transform", "physical", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def treatment_safe(concern: Concern, trans: Transformation) -> bool:
    return concern.sense >= SENSE_MIN and concern.power >= 1 and trans.id == "treated_to_clean"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for animal in ANIMALS:
        for place in PLACES:
            for concern in CONCERNS:
                if treatment_safe(concern, TRANSFORMATIONS["treated_to_clean"]):
                    combos.append((animal, place, concern.id))
    return combos


@dataclass
class StoryParams:
    animal: str
    place: str
    concern: str
    gown_color: str = "blue"
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


ANIMALS = {
    "cat": AnimalKind("cat", "cat", "meow", "home", "soft fur"),
    "dog": AnimalKind("dog", "dog", "woof", "yard", "shaggy fur"),
    "rabbit": AnimalKind("rabbit", "rabbit", "squeak", "meadow", "fluffy fur"),
    "fox": AnimalKind("fox", "fox", "yip", "forest", "rusty fur"),
}

PLACES = {
    "clinic": Place("clinic", "the dentist clinic", "bright"),
    "office": Place("office", "the dentist office", "clean"),
}

CONCERNS = {
    "toothache": Concern("toothache", "toothache", "a sore tooth", 3, 1, "cleaned the tooth", "looked better", {"teeth"}),
    "grime": Concern("grime", "grime", "gruesome grime", 3, 1, "scrubbed the mouth", "looked cleaner", {"teeth"}),
    "wiggle": Concern("wiggle", "wiggle", "a loose tooth", 2, 1, "checked the tooth", "settled down", {"teeth"}),
}

TRANSFORMATIONS = {
    "treated_to_clean": Transformation(
        id="treated_to_clean",
        label="transformation",
        before="gruesome",
        after="bright and neat",
        change="the mouth went from gruesome to bright and neat",
        tags={"transform", "clean"},
    )
}

GOWN_COLORS = ["blue", "green", "yellow", "white", "pink"]
NAMES = {
    "cat": ["Mimi", "Nora", "Luna", "Pebble"],
    "dog": ["Bingo", "Milo", "Pip", "Rex"],
    "rabbit": ["Bunny", "Tilly", "Moss", "Poppy"],
    "fox": ["Foxy", "Nova", "Tango", "Ruby"],
}


def choose_name(rng: random.Random, animal: str) -> str:
    return rng.choice(NAMES[animal])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about a dentist, a gown, and a transformation.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--concern", choices=CONCERNS)
    ap.add_argument("--gown-color", choices=GOWN_COLORS)
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


def explain_rejection(concern: Concern) -> str:
    return f"(No story: the concern '{concern.id}' is too small to support a real transformation.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.concern and args.concern not in CONCERNS:
        raise StoryError(explain_rejection(Concern(args.concern, args.concern, args.concern, 0, 0, "", "")))
    animal = args.animal or rng.choice(list(ANIMALS))
    place = args.place or rng.choice(list(PLACES))
    concern = args.concern or rng.choice(list(CONCERNS))
    gown_color = args.gown_color or rng.choice(GOWN_COLORS)
    return StoryParams(animal=animal, place=place, concern=concern, gown_color=gown_color)


def tell(params: StoryParams) -> World:
    world = World()
    animal = world.add(Entity(id="animal", kind="character", type=params.animal, role="patient", label=ANIMALS[params.animal].label, nervous=True))
    dentist = world.add(Entity(id="dentist", kind="character", type="mouse", role="dentist", label="the dentist", caring=True, shiny=True))
    gown = world.add(Entity(id="gown", kind="thing", type="gown", label=f"{params.gown_color} gown"))
    patient = world.add(Entity(id="patient", kind="thing", type="mouth", label="the mouth"))
    concern = CONCERNS[params.concern]

    animal.memes["nervous"] = 1
    animal.meters["pain"] = 1.0
    patient.meters["pain"] = 1.0
    world.facts.update(animal=animal, dentist=dentist, gown=gown, patient=patient, concern=concern, place=PLACES[params.place], trans=TRANSFORMATIONS["treated_to_clean"], params=params)

    world.say(f"{animal.label.title()} the {animal.type} came to {PLACES[params.place].label} wearing a {params.gown_color} gown.")
    world.say(f"The {concern.phrase} looked gruesome, and {animal.label} held still while the dentist listened carefully.")
    world.para()
    world.say(f'"I can help," said the dentist, and the little room felt calm and bright.')
    world.say(f"The dentist cleaned the tooth, and the transformation began right there in the chair.")
    patient.meters["treated"] = 1.0
    propagate(world, narrate=False)
    world.para()
    world.say(f"At last, the mouth looked {TRANSFORMATIONS['treated_to_clean'].after}, and {animal.label} smiled.")
    world.say(f"The {gown.label} was no longer needed; the brave animal hopped out feeling proud and clean.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story that includes the words "gown", "gruesome", and "dentist", and ends with a transformation.',
        f"Tell a gentle story about {f['animal'].label} the {f['animal'].type} visiting a dentist in a gown and feeling less scared after help.",
        "Write a child-friendly animal story where something gruesome gets fixed by a dentist and turns into a neat ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal = f["animal"]
    concern = f["concern"]
    return [
        ("Who went to the dentist?", f"{animal.label} the {animal.type} went to the dentist in a gown."),
        ("Why did the animal need help?", f"The mouth had {concern.phrase}, which looked gruesome and made the animal nervous."),
        ("What changed by the end?", "The painful, gruesome look was transformed into a clean, bright smile after the dentist helped."),
        ("Why did the animal feel brave at the end?", "The dentist helped calmly, and the scary feeling faded once the tooth was treated. That is why the animal could leave smiling."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a dentist?", "A dentist is a grown-up who helps keep teeth healthy and clean."),
        ("What is a gown?", "A gown is a loose piece of clothing that people can wear over their clothes."),
        ("What does transformation mean?", "A transformation is a change from one form or state into another."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(animal, place, concern) :- animal(animal), place(place), concern(concern), safe_concern(concern).
safe_concern(toothache).
safe_concern(grime).
safe_concern(wiggle).
outcome(transformed) :- treated.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CONCERNS:
        lines.append(asp.fact("concern", c))
    for c in CONCERNS:
        lines.append(asp.fact("safe_concern", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(animal=None, place=None, concern=None, gown_color=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS or params.place not in PLACES or params.concern not in CONCERNS:
        raise StoryError("Invalid params.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(animal="cat", place="clinic", concern="grime", gown_color="blue"),
    StoryParams(animal="rabbit", place="office", concern="toothache", gown_color="green"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for triple in asp_valid_combos():
            print(" ", triple)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
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

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
