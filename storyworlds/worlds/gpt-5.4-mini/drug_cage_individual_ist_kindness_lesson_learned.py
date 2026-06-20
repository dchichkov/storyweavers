#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/drug_cage_individual_ist_kindness_lesson_learned.py
====================================================================================

A standalone story world for a tiny whodunit-style kindness tale.

Premise
-------
A child notices a strange, locked cage in a clinic and hears the odd word
"individual-ist." The child first suspects a lost drug bottle is the problem,
then remembers a flashback: someone had been carefully feeding a frightened
bird by hand. The "mystery" turns into a kindness lesson, because the cage was
not for a villain at all; it was a safe temporary home while a grown-up kept a
medicine bottle away from a curious pet and helped an injured bird recover.

This world keeps the story small, concrete, and state-driven:
- typed entities with physical meters and emotional memes,
- forward causal rules,
- a prediction beat,
- a flashback beat,
- a kindness resolution,
- a lesson learned ending.

The required seed words appear as world vocabulary:
- drug
- cage
- individual-ist

The story style aims at a child-friendly whodunit: suspicion, clue, flashback,
reveal, and a gentle lesson learned.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/drug_cage_individual_ist_kindness_lesson_learned.py
    python storyworlds/worlds/gpt-5.4-mini/drug_cage_individual_ist_kindness_lesson_learned.py --qa
    python storyworlds/worlds/gpt-5.4-mini/drug_cage_individual_ist_kindness_lesson_learned.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    quiet: bool = True
    locked_room: bool = False

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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    dangerous: bool = False
    flammable: bool = False
    tool: bool = False
    kind_word: str = ""

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
@dataclass
class StoryParams:
    place: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    drug: str
    cage: str
    individual: str
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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["suspicion"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        child.memes["worry"] += 1
        out.append("The little mystery made the room feel extra quiet.")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    helper = world.get("helper")
    if helper.meters["kindness"] >= THRESHOLD and ("kind",) not in world.fired:
        world.fired.add(("kind",))
        helper.memes["warmth"] += 1
        out.append("A gentle clue started to make sense.")
    return out


RULES = [
    Rule("worry", _r_worry),
    Rule("kindness", _r_kindness),
]


def predict_story(world: World) -> dict:
    sim = world.copy()
    return {
        "cage_is_safe": sim.get("cage").meters["safe"] >= THRESHOLD,
        "drug_is_suspicious": sim.get("drug").meters["suspicion"] >= THRESHOLD,
    }


def setup_scene(world: World, p: Place, child: Entity, helper: Entity, parent: Entity) -> None:
    world.say(
        f"On a rainy afternoon, {child.id} followed {helper.id} into {p.label}, "
        f"where everything was neat, bright, and very still."
    )
    world.say(
        f"Near the back wall stood a locked {world.facts['cage_label']}, and on the desk "
        f"sat a tiny bottle labeled {world.facts['drug_label']}."
    )


def suspicion(world: World, child: Entity, drug: Entity, cage: Entity) -> None:
    child.meters["suspicion"] += 1
    drug.meters["suspicion"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} pointed. "That {drug.label} looks like the clue," {child.pronoun()} said. '
        f'"And why is there a {cage.label}?"'
    )
    world.say(
        f"For a moment, {child.id} thought somebody must have hidden something bad inside."
    )


def flashback(world: World, helper: Entity, child: Entity, bird: Entity, cage: Entity) -> None:
    helper.meters["kindness"] += 1
    bird.meters["hurt"] += 1
    world.say(
        f"Then {child.id} remembered a flashback: yesterday, {helper.id} had knelt beside "
        f"a little bird and spoken softly so it would not panic."
    )
    world.say(
        f"In that memory, the {cage.label} was only a safe rest place, and {helper.id} had "
        f"fed the bird by hand because its wing was sore."
    )


def reveal(world: World, helper: Entity, parent: Entity, drug: Entity, cage: Entity, bird: Entity) -> None:
    world.say(
        f"{parent.label_word.capitalize()} smiled and explained the clue. "
        f'The {drug.label} was a grown-up medicine, not a secret bad thing.'
    )
    world.say(
        f"The {cage.label} was there to keep the injured bird calm while it healed, and "
        f"{helper.id} had been careful, not cruel."
    )
    bird.meters["safe"] += 1
    cage.meters["safe"] += 1


def lesson(world: World, child: Entity, helper: Entity, parent: Entity, drug: Entity) -> None:
    child.memes["understanding"] += 1
    child.memes["kindness"] += 1
    world.say(
        f'{parent.label_word.capitalize()} patted {child.id} on the shoulder. '
        f'"A good guess is fine, but kindness means asking before you blame," '
        f"{parent.pronoun()} said."
    )
    world.say(
        f'{child.id} nodded. "I get it now," {child.pronoun()} said. '
        f'"The {drug.label} was medicine, and the real clue was how gentle '
        f'{helper.id} had been."'
    )
    world.say(
        "The lesson learned was simple: in a mystery, a soft heart can be the best clue of all."
    )


def ending(world: World, child: Entity, helper: Entity, bird: Entity) -> None:
    child.memes["peace"] += 1
    helper.memes["peace"] += 1
    bird.meters["recovered"] += 1
    world.say(
        f"In the end, {child.id} helped water the plant by the window while "
        f"{helper.id} checked on the bird."
    )
    world.say(
        f"The {world.facts['cage_label']} stayed open, the medicine stayed on the shelf, "
        f"and the bird rested safely with a bright feather tucked against its side."
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    child = world.add(Entity(params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(params.helper, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(params.parent, kind="character", type="mother", role="parent", label="the parent"))

    drug = world.add(Entity("drug", type="thing", label=DRUGS[params.drug].label, attrs={"kind": "drug"}))
    cage = world.add(Entity("cage", type="thing", label=CAGES[params.cage].label, attrs={"kind": "cage"}))
    individual = world.add(Entity("individual", type="thing", label=INDIVIDUALS[params.individual].label, attrs={"kind": "individual-ist"}))
    bird = world.add(Entity("bird", type="thing", label="little bird"))

    world.facts.update(
        place=place,
        drug_label=drug.label,
        cage_label=cage.label,
        individual_label=individual.label,
        bird=bird,
        child=child,
        helper=helper,
        parent=parent,
        drug=drug,
        cage=cage,
        individual=individual,
    )

    setup_scene(world, place, child, helper, parent)
    world.para()
    suspicion(world, child, drug, cage)
    world.para()
    flashback(world, helper, child, bird, cage)
    world.para()
    reveal(world, helper, parent, drug, cage, bird)
    lesson(world, child, helper, parent, drug)
    world.para()
    ending(world, child, helper, bird)
    return world


PLACES = {
    "clinic": Place("clinic", "a small clinic"),
    "library": Place("library", "the library hallway"),
    "shed": Place("shed", "the garden shed"),
}

DRUGS = {
    "cough": ObjectCfg("cough", "drug bottle", "a little drug bottle", dangerous=True, kind_word="drug"),
    "pills": ObjectCfg("pills", "drug jar", "a small drug jar", dangerous=True, kind_word="drug"),
}

CAGES = {
    "bird": ObjectCfg("bird", "bird cage", "a bird cage", tool=False, kind_word="cage"),
    "toy": ObjectCfg("toy", "wire cage", "a wire cage", tool=False, kind_word="cage"),
}

INDIVIDUALS = {
    "ist": ObjectCfg("ist", "individual-ist", "an individual-ist sign", kind_word="individual-ist"),
    "note": ObjectCfg("note", "individual-ist note", "an individual-ist note", kind_word="individual-ist"),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Zoe", "Finn"]
HELPER_NAMES = ["Ellie", "Max", "Ruby", "Sam", "Ivy", "Jack"]


@dataclass
class StoryParams:
    place: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    drug: str
    cage: str
    individual: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for d in DRUGS:
            for c in CAGES:
                combos.append((p, d, c))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story that includes the words "{f["drug_label"]}", '
        f'"{f["cage_label"]}", and "individual-ist".',
        f"Tell a mystery where {f['child'].id} suspects a drug bottle and a cage, then "
        f"learns a kindness lesson from a flashback.",
        f"Write a gentle detective story with a flashback, a false suspicion, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What did the child think was suspicious at first?",
            answer=f'{f["child"].id} first thought the {f["drug_label"]} and the {f["cage_label"]} were clues in a bad mystery. But the story later showed that the gentle helper was only keeping something safe.'
        ),
        QAItem(
            question="What did the flashback show?",
            answer="The flashback showed the helper being kind to a hurt bird and feeding it by hand. That memory proved the cage was for safety, not for harm."
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was that kindness matters more than quick blame. In a mystery, it is better to ask and look carefully before judging someone."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cage used for?",
            answer="A cage can be used to keep an animal safe for a short time, like when it is hurt or needs quiet rest."
        ),
        QAItem(
            question="Why should medicine be handled by grown-ups?",
            answer="Medicine must be handled by grown-ups because the right amount and the right timing matter. A child should never guess about medicine."
        ),
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback shows something that happened earlier. It helps the reader understand a clue that was confusing at first."
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("clinic", "Mia", "girl", "Ellie", "girl", "mother", "cough", "bird", "ist"),
    StoryParams("library", "Leo", "boy", "Max", "boy", "father", "pills", "toy", "note"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world about kindness and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--drug", choices=DRUGS)
    ap.add_argument("--cage", choices=CAGES)
    ap.add_argument("--individual", choices=INDIVIDUALS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    drug = args.drug or rng.choice(list(DRUGS))
    cage = args.cage or rng.choice(list(CAGES))
    individual = args.individual or rng.choice(list(INDIVIDUALS))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, child, child_gender, helper, helper_gender, parent, drug, cage, individual)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
kindness(helper) :- helper(X), gentle(X).
mystery(clue) :- drug(D), cage(C), suspicious(D), suspicious(C).
flashback_needed :- mystery(clue), kindness(helper).
lesson_learned :- flashback_needed, kindness(helper).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for d in DRUGS:
        lines.append(asp.fact("drug", d))
        lines.append(asp.fact("suspicious", d))
    for c in CAGES:
        lines.append(asp.fact("cage", c))
    for i in INDIVIDUALS:
        lines.append(asp.fact("individual", i))
    lines.append(asp.fact("gentle", "helper"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import only when needed.
    import asp
    _ = asp.one_model(asp_program("#show kindness/1.\n#show lesson_learned/0."))
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: story generation crashed: {exc}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show kindness/1.\n#show lesson_learned/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This miniature world keeps ASP simple; run --verify for the smoke test.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} at {p.place} ({p.drug}, {p.cage}, individual-ist)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
