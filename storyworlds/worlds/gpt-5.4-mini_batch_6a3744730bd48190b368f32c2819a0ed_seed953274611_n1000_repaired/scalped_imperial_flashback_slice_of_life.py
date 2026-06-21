#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scalped_imperial_flashback_slice_of_life.py
===========================================================================

A small slice-of-life storyworld built from the seed words "scalped" and
"imperial", with a flashback instrument.

Premise
-------
A child goes to a neighborhood barber for a simple trim, worries that the cut
will be too short, remembers an old imperial parade photo from home, and ends up
leaving with a gentler, happier haircut and a calmer mood.

The domain is intentionally small and grounded:
- typed entities with physical meters and emotional memes
- a state-driven narrative with premise -> tension -> flashback -> resolution
- a Python reasonableness gate plus an inline ASP twin
- three QA sets generated from the simulated world state

The story text is authored from the simulation state, not from a frozen template
with swapped nouns.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/scalped_imperial_flashback_slice_of_life.py
    python storyworlds/worlds/gpt-5.4-mini/scalped_imperial_flashback_slice_of_life.py --qa
    python storyworlds/worlds/gpt-5.4-mini/scalped_imperial_flashback_slice_of_life.py --trace
    python storyworlds/worlds/gpt-5.4-mini/scalped_imperial_flashback_slice_of_life.py --verify
"""

from __future__ import annotations

import argparse
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
DISCOMFORT_LIMIT = 2.0
FLASHBACK_TRIGGER = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad", "barber": "barber"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    smell: str
    comfort: str
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
class Haircut:
    id: str
    label: str
    trim: int
    style: str
    safe: bool = True
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
class Memory:
    id: str
    label: str
    image: str
    lesson: str
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
class StoryParams:
    place: str
    haircut: str
    memory: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    caregiver: str
    seed: Optional[int] = None
    flashback: bool = True
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


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


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["comforted"] >= THRESHOLD and ("comfort", "child") not in world.fired:
        world.fired.add(("comfort", "child"))
        child.memes["calm"] += 1
        out.append("The child breathed more easily.")
    return out


CAUSAL_RULES = [Rule("comfort", "social", _r_comfort)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


def looks_too_short(haircut: Haircut, child_hair: int) -> bool:
    return haircut.trim >= child_hair


def would_cut_too_close(haircut: Haircut) -> bool:
    return haircut.trim >= 3


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for haircut in HAIRCUTS:
            for memory in MEMORIES:
                if place in {"barbershop", "kitchen_table"} and HAIRCUTS[haircut].safe:
                    combos.append((place, haircut, memory))
    return combos


def introduction(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"On a quiet afternoon, {child.id} and {helper.id} went to {place.label}. "
        f"It smelled like {place.smell}, and the room felt {place.comfort}."
    )


def want_trim(world: World, child: Entity, haircut: Haircut) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} had come for {haircut.label}, just a small change to feel neat "
        f"again."
    )


def tension(world: World, child: Entity, haircut: Haircut) -> None:
    if haircut.trim >= 3:
        child.memes["worry"] += 2
        child.meters["unease"] += 1
        world.say(
            f"Then the chair made a tiny squeak, and {child.id} stared at the cape. "
            f"{child.pronoun().capitalize()} was afraid the cut would come out scalped."
        )


def flashback(world: World, child: Entity, memory: Memory, helper: Entity) -> None:
    if child.meters["unease"] < FLASHBACK_TRIGGER:
        return
    child.meters["flashback"] += 1
    child.memes["remembering"] += 1
    world.para()
    world.say(
        f"For a second, {child.id} remembered {memory.image}. {memory.lesson} "
        f"{helper.id} noticed {child.pronoun('possessive')} face and waited."
    )


def reassure(world: World, helper: Entity, child: Entity, haircut: Haircut) -> None:
    helper.memes["kindness"] += 1
    child.meters["comforted"] += 1
    world.say(
        f'{helper.id} smiled and said, "We can keep it gentle. A neat haircut does '
        f"not have to be a scalped one.""
    )


def resolve(world: World, child: Entity, helper: Entity, caregiver: Entity, haircut: Haircut) -> None:
    child.memes["joy"] += 1
    child.memes["calm"] += 1
    child.meters["unease"] = 0
    world.say(
        f'{caregiver.label_word.capitalize()} nodded from the doorway. {caregiver.pronoun().capitalize()} '
        f"liked the careful plan, and {helper.id} snipped only a little at a time."
    )
    world.say(
        f"In the mirror, {child.id}'s hair looked tidy and soft, not scalped at all. "
        f"{child.id} touched {child.pronoun('possessive')} head and grinned."
    )


def tell(place: Place, haircut: Haircut, memory: Memory, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, caregiver_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=caregiver_type, role="caregiver"))
    world.add(Entity(id="place", kind="place", type="place", label=place.label))
    world.add(Entity(id="memory", kind="memory", type="memory", label=memory.label))
    child.meters["hair_length"] = 4
    child.meters["unease"] = 0
    introduction(world, child, helper, place)
    world.para()
    want_trim(world, child, haircut)
    tension(world, child, haircut)
    flashback(world, child, memory, helper)
    reassure(world, helper, child, haircut)
    world.para()
    resolve(world, child, helper, caregiver, haircut)
    world.facts.update(
        child=child, helper=helper, caregiver=caregiver, place=place, haircut=haircut,
        memory=memory, outcome="gentle", flashback=bool(child.meters["flashback"]),
    )
    return world


PLACES = {
    "barbershop": Place(id="barbershop", label="the corner barbershop", smell="soap and warm towels",
                        comfort="bright and familiar", tags={"slice_of_life", "barber"}),
    "kitchen_table": Place(id="kitchen_table", label="the kitchen table", smell="toast and tea",
                           comfort="small and homey", tags={"slice_of_life", "home"}),
}

HAIRCUTS = {
    "trim": Haircut(id="trim", label="a trim", trim=1, style="short and neat", tags={"hair"}),
    "buzz": Haircut(id="buzz", label="a very short cut", trim=3, style="close and tidy", tags={"hair", "short"}),
    "bangs": Haircut(id="bangs", label="a careful bang trim", trim=1, style="soft and tidy", tags={"hair"}),
}

MEMORIES = {
    "imperial_photo": Memory(
        id="imperial_photo",
        label="an old photo",
        image="the family album with an imperial parade hat and a smiling grandparent",
        lesson="It was only a memory, but it made the room feel bigger for a moment.",
        tags={"imperial", "flashback"},
    ),
    "school_day": Memory(
        id="school_day",
        label="a school picture",
        image="the desk by the window and the shiny lunchbox from first grade",
        lesson="Sometimes a small worry can grow when a person remembers being little.",
        tags={"flashback"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Ava", "Zoe", "Nina", "Ella"]
BOY_NAMES = ["Noah", "Theo", "Milo", "Eli", "Ben", "Finn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--haircut", choices=HAIRCUTS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    haircut = args.haircut or rng.choice(list(HAIRCUTS))
    memory = args.memory or rng.choice(list(MEMORIES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != child])
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    if haircut == "buzz" and place != "barbershop":
        raise StoryError("That cut needs the barbershop setting for a believable story.")
    return StoryParams(place=place, haircut=haircut, memory=memory, child=child,
                       child_gender=child_gender, helper=helper,
                       helper_gender=helper_gender, caregiver=caregiver)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.haircut not in HAIRCUTS or params.memory not in MEMORIES:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(PLACES[params.place], HAIRCUTS[params.haircut], MEMORIES[params.memory],
                 params.child, params.child_gender, params.helper, params.helper_gender,
                 params.caregiver)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story that includes the words "scalped" and "imperial".',
        f"Tell a story about {f['child'].id} getting a haircut, feeling a little worried, "
        f"and remembering {f['memory'].label} in a flashback.",
        f"Write a calm everyday story where a helper notices a child is afraid the haircut will be scalped, "
        f"and the child leaves feeling better.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    caregiver: Entity = f["caregiver"]
    haircut: Haircut = f["haircut"]
    memory: Memory = f["memory"]
    qa = [
        ("What is the story about?",
         f"It is about {child.id} getting {haircut.label} with help from {helper.id} and {caregiver.label_word}."),
        ("Why did the child get worried?",
         f"{child.id} worried the haircut might be scalped because the cut seemed very short at first. The worry faded when {helper.id} promised to keep it gentle."),
        ("What did the flashback show?",
         f"It showed {memory.image}. That memory made the moment feel bigger for a second, and then {helper.id} waited kindly."),
        ("How did the story end?",
         f"{child.id} left with a neat haircut and a calmer mood. The ending proves the cut stayed soft instead of scalped."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["haircut"].tags) | set(f["memory"].tags)
    out = []
    if "imperial" in tags:
        out.append(("What does imperial mean here?",
                    "Imperial means something connected to an emperor or empire. In this story it appears in an old family memory, not as something scary or grand."))
    if "flashback" in tags:
        out.append(("What is a flashback?",
                    "A flashback is when a story briefly remembers something from before. It helps show why a character feels the way they do now."))
    if "hair" in tags:
        out.append(("Why do people get haircuts?",
                    "People get haircuts to keep their hair neat, comfortable, and easy to manage. A haircut can be small and gentle, not dramatic."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
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
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return params.place in PLACES and params.haircut in HAIRCUTS and params.memory in MEMORIES


def valid_combos_python() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for haircut in HAIRCUTS:
            for memory in MEMORIES:
                if place == "barbershop" or haircut != "buzz":
                    combos.append((place, haircut, memory))
    return combos


ASP_RULES = r"""
valid(P,H,M) :- place(P), haircut(H), memory(M), not too_short(P,H).
too_short(kitchen_table,buzz).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in HAIRCUTS:
        lines.append(asp.fact("haircut", h))
    for m in MEMORIES:
        lines.append(asp.fact("memory", m))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(valid_combos_python()) != set(asp_valid_combos()):
        rc = 1
        print("ASP/Python mismatch in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, haircut=None, memory=None,
                                                             child=None, child_gender=None, helper=None,
                                                             helper_gender=None, caregiver=None),
                                        random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"Smoke test failed: {e}")
        return 1
    print("OK")
    return rc


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
    StoryParams(place="barbershop", haircut="trim", memory="imperial_photo", child="Mina", child_gender="girl", helper="Noah", helper_gender="boy", caregiver="mother"),
    StoryParams(place="barbershop", haircut="buzz", memory="imperial_photo", child="Theo", child_gender="boy", helper="Lily", helper_gender="girl", caregiver="father"),
    StoryParams(place="kitchen_table", haircut="bangs", memory="school_day", child="Ava", child_gender="girl", helper="Eli", helper_gender="boy", caregiver="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
        if idx:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
