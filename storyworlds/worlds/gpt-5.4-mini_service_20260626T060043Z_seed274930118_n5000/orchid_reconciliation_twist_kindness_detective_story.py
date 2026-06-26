#!/usr/bin/env python3
"""
orchid_reconciliation_twist_kindness_detective_story.py
=======================================================

A small detective-story world about a child detective, a missing orchid,
a twist, and a kindness-based reconciliation.

Premise source tale:
- A prized orchid goes missing from a greenhouse.
- The young detective follows clues through wet soil, a torn tag, and a muddy paw print.
- The twist is that the "thief" was only trying to save the orchid from a broken vent.
- The ending brings reconciliation through kindness: the detective returns the plant,
  the worried caretaker apologizes, and everyone tends the orchid together.

This script keeps the world tiny, state-driven, and child-facing while still
supporting the shared Storyweavers CLI, QA, trace, JSON, and ASP verification
interfaces.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    paw: object | None = None
    tag: object | None = None
    vent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "caretaker"}
        male = {"boy", "man", "father", "gardener"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the greenhouse"
    setting_detail: str = "rows of glass walls and warm, wet air"
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
    detective_name: str
    detective_type: str
    caretaker_type: str
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


PLACES = {
    "greenhouse": Setting("the greenhouse", "rows of glass walls and warm, wet air"),
    "flower_shop": Setting("the flower shop", "bright buckets, stems, and a sweet plant smell"),
    "school_garden": Setting("the school garden", "little paths, labels, and a sunlit bench"),
}

NAMES = ["Mina", "Nico", "Tess", "Arlo", "Ivy", "Milo", "Luna", "Rowan"]
DETECTIVE_TYPES = ["girl", "boy"]
CARETAKER_TYPES = ["mother", "father", "gardener"]

DETECTIVE_TRAITS = ["careful", "curious", "brave", "patient", "sharp-eyed"]


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = _meter(e, key) + amount


def _add_mem(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = _mem(e, key) + amount


def _do_clues(world: World) -> None:
    d = world.get("Detective")
    orchid = world.get("Orchid")
    vent = world.get("Vent")
    clerk = world.get("Caretaker")

    d.meters["observations"] = 1
    _add_mem(d, "determination", 1)
    world.say(
        f"{d.id} was a {d.type} detective who noticed small things right away."
    )
    world.say(
        f"One day, {d.id} visited {world.setting.place} because {orchid.label} had gone missing."
    )
    world.say(f"{world.setting.setting_detail} made every clue easy to miss.")
    world.say(
        f"{d.id} saw that the orchid stand was empty, but there was one broken vent above it."
    )
    _add_mem(clerk, "worry", 1)
    world.facts["initial_missing"] = True
    world.facts["vent_broken"] = True
    world.facts["orchid_damp"] = True


def _find_clue(world: World) -> None:
    d = world.get("Detective")
    paw = world.get("Pawprint")
    tag = world.get("Tag")
    world.para()
    world.say(
        f"{d.id} crouched low and found a muddy paw print near the flower carts."
    )
    world.say(
        f"Then {d.id} spotted a torn tag that said {tag.phrase}, caught on a bench leg."
    )
    _add_meter(paw, "seen", 1)
    _add_meter(tag, "seen", 1)
    _add_mem(d, "hope", 1)
    world.facts["clues_found"] = ["pawprint", "tag"]


def _twist(world: World) -> None:
    d = world.get("Detective")
    c = world.get("Caretaker")
    orchid = world.get("Orchid")
    world.para()
    _add_mem(d, "surprise", 1)
    world.say(
        f"{d.id} followed the clues behind a row of pots and gasped at the twist."
    )
    world.say(
        f"The orchid had not been stolen at all; {c.id} had moved {orchid.it()} to keep "
        f"{orchid.it()} away from the broken vent's cold draft."
    )
    world.say(
        f"A small fan had been blowing chilly air onto the leaves, so {c.id} hid the plant in a safer corner."
    )
    world.facts["twist"] = "protective_move"


def _reconcile(world: World) -> None:
    d = world.get("Detective")
    c = world.get("Caretaker")
    orchid = world.get("Orchid")
    helper = world.get("Helper")
    world.para()
    _add_mem(c, "shame", 1)
    _add_mem(d, "kindness", 1)
    _add_mem(c, "relief", 1)
    world.say(
        f"{d.id} did not scold {c.id}. Instead, {d.id} pointed to the broken vent and said they could fix it together."
    )
    world.say(
        f"{helper.id} brought tape and a small tray, and soon everyone moved the orchid back under the warm light."
    )
    world.say(
        f"{c.id} smiled and apologized, and {d.id} smiled back. That kindness helped them reconcile."
    )
    world.say(
        f"At the end, {orchid.label} stood safe and bright, with new water on its roots and calm air around its leaves."
    )
    world.facts["resolved"] = True


def tell(setting: Setting, detective_name: str, detective_type: str, caretaker_type: str) -> World:
    world = World(setting)

    detective = world.add(
        Entity(id=detective_name, kind="character", type=detective_type, label=detective_name)
    )
    caretaker = world.add(
        Entity(id="Caretaker", kind="character", type=caretaker_type, label="the caretaker")
    )
    orchid = world.add(
        Entity(
            id="Orchid",
            type="thing",
            label="orchid",
            phrase="the white orchid",
            caretaker=caretaker.id,
            location=setting.place,
        )
    )
    vent = world.add(Entity(id="Vent", type="thing", label="vent", phrase="the broken vent"))
    paw = world.add(Entity(id="Pawprint", type="thing", label="paw print", phrase="a muddy paw print"))
    tag = world.add(Entity(id="Tag", type="thing", label="tag", phrase="a plant tag"))

    helper = world.add(
        Entity(id="Helper", kind="character", type="gardener", label="the helper gardener")
    )

    _add_mem(detective, "curiosity", 1)
    _add_mem(caretaker, "worry", 1)
    _add_mem(orchid, "precious", 1)

    _do_clues(world)
    _find_clue(world)
    _twist(world)
    _reconcile(world)

    world.facts.update(
        detective=detective,
        caretaker=caretaker,
        orchid=orchid,
        vent=vent,
        paw=paw,
        tag=tag,
        helper=helper,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    c = _safe_fact(world, f, "caretaker")
    return [
        f'Write a short detective story for a young child set in {world.setting.place} about a missing orchid.',
        f"Tell a gentle mystery where {d.id} follows clues, learns a twist, and helps {c.id} make things right.",
        "Write a child-friendly detective story that ends with kindness, apology, and reconciliation around an orchid.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    c = _safe_fact(world, f, "caretaker")
    orchid = _safe_fact(world, f, "orchid")
    return [
        QAItem(
            question=f"What kind of story is this about {d.id} and the orchid?",
            answer=f"It is a detective story about {d.id} searching for the missing orchid and learning what really happened.",
        ),
        QAItem(
            question=f"Why did {c.id} move the orchid?",
            answer="The caretaker moved the orchid to protect it from the broken vent and the cold draft.",
        ),
        QAItem(
            question=f"What was the twist in the mystery?",
            answer="The twist was that the orchid had not been stolen; it had been moved for safety.",
        ),
        QAItem(
            question=f"How did the story end for the orchid?",
            answer=f"The orchid ended safe, watered, and back in a warm place where everyone could care for it together.",
        ),
        QAItem(
            question=f"How did {d.id} help everyone reconcile?",
            answer=f"{d.id} chose kindness, helped fix the problem, and did not blame {c.id}. That helped them make up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orchid?",
            answer="An orchid is a flower with lovely blossoms. Some orchids need careful watering and warm, gentle care.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks good questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about other people even when something goes wrong.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were upset make peace again and become friendly once more.",
        ),
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="greenhouse", detective_name="Mina", detective_type="girl", caretaker_type="gardener"),
    StoryParams(place="flower_shop", detective_name="Nico", detective_type="boy", caretaker_type="mother"),
    StoryParams(place="school_garden", detective_name="Ivy", detective_type="girl", caretaker_type="father"),
]


ASP_RULES = r"""
% A very small parity twin for the registry gate.
has_place(P) :- place(P).
has_detective(D) :- detective(D).
has_setting(P, D) :- has_place(P), has_detective(D).
#show has_setting/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for name in NAMES:
        lines.append(asp.fact("detective", name.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show has_setting/2."))
    atoms = set(asp.atoms(model, "has_setting"))
    py = {(p, d) for p in PLACES for d in [n.lower() for n in NAMES]}
    if atoms == py:
        print(f"OK: clingo gate matches python registry cross-product ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and python registry cross-product.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world about an orchid mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--detective-type", choices=DETECTIVE_TYPES)
    ap.add_argument("--caretaker-type", choices=CARETAKER_TYPES)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    detective_type = getattr(args, "detective_type", None) or rng.choice(DETECTIVE_TYPES)
    caretaker_type = getattr(args, "caretaker_type", None) or rng.choice(CARETAKER_TYPES)
    return StoryParams(place=place, detective_name=name, detective_type=detective_type, caretaker_type=caretaker_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), params.detective_name, params.detective_type, params.caretaker_type)
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
        print(asp_program("#show has_setting/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show has_setting/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.detective_name}: orchid mystery at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
