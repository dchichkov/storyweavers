#!/usr/bin/env python3
"""
storyworlds/worlds/peroxide_misunderstanding_folk_tale.py
==========================================================

A small folk-tale storyworld about a misunderstanding involving peroxide.

Seed tale:
---
In a little village, a kind grandmother kept a bottle of peroxide for cleaning
scrapes and brightening cloth. One day, a curious child saw the bubbly liquid
and thought it was a magic potion for making muddy wool white again. The child
poured it on a lamb's dirty fleece, which frightened the lamb and worried the
grandmother, because the bottle was for careful cleaning, not for a whole bath.
The grandmother explained that peroxide only belonged on tiny spots and cloth,
and she showed the child how to use a damp rag instead. The child apologized,
helped wash the fleece gently, and learned that good folk remedies still need
good listening.

This script turns that premise into a constraint-checked simulation with a
single misunderstanding-driven turn and a gentle resolution.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "grandmother", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "grandfather", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    elder_name: str
    animal: str
    object_name: str
    seed: Optional[int] = None


PLACES = {
    "village_green": "the village green",
    "barn": "the old barn",
    "cottage": "the cottage kitchen",
}

CHILD_NAMES = ["Mina", "Toby", "Nora", "Pip", "Lena", "Owen"]
ELDER_NAMES = ["Grandma Rose", "Grandpa Will", "Aunt Hilda", "Uncle Bram"]
ANIMALS = [
    ("lamb", "a woolly lamb"),
    ("goat", "a shy goat"),
    ("duckling", "a tiny duckling"),
]
OBJECTS = [
    ("wool", "a bundle of muddy wool"),
    ("cloth", "a stained cloth"),
    ("kerchief", "a pale kerchief"),
]

KNOWLEDGE_ORDER = ["peroxide", "wool", "cloth", "mud", "clean", "rag"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    object_ = world.get("object")
    elder = world.get("elder")
    if child.memes.get("misread", 0) >= THRESHOLD and object_.meters.get("soaked", 0) >= THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            elder.memes["worry"] = elder.memes.get("worry", 0) + 1
            out.append(f"{elder.pronoun().capitalize()} looked worried.")
    return out


def _r_sting(world: World) -> list[str]:
    out = []
    child = world.get("child")
    object_ = world.get("object")
    if object_.meters.get("peroxide", 0) >= THRESHOLD and not object_.protective:
        sig = ("sting",)
        if sig not in world.fired:
            world.fired.add(sig)
            object_.memes["fright"] = object_.memes.get("fright", 0) + 1
            out.append(f"The {object_.label} flinched at the bubbly splash.")
    return out


RULES = [Rule("worry", _r_worry), Rule("sting", _r_sting)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_belief_error(world: World, child: Entity, object_: Entity, narrate: bool = True) -> None:
    child.memes["curious"] = child.memes.get("curious", 0) + 1
    child.memes["misread"] = child.memes.get("misread", 0) + 1
    object_.meters["peroxide"] = object_.meters.get("peroxide", 0) + 1
    object_.meters["soaked"] = object_.meters.get("soaked", 0) + 1
    propagate(world, narrate=narrate)


def tell_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    elder = world.add(Entity(id="elder", kind="character", type="grandmother" if "Grandma" in params.elder_name else "grandfather", label=params.elder_name))
    animal_type, animal_phrase = next(a for a in ANIMALS if a[0] == params.animal)
    animal = world.add(Entity(id="animal", kind="character", type=animal_type, label=animal_type, phrase=animal_phrase))
    object_type, object_phrase = next(o for o in OBJECTS if o[0] == params.object_name)
    obj = world.add(Entity(id="object", type=object_type, label=object_type, phrase=object_phrase, caretaker=elder.id))
    world.facts.update(child=child, elder=elder, animal=animal, object=obj)

    world.say(f"In {world.place}, {elder.label} kept a little bottle of peroxide on a high shelf.")
    world.say(f"{child.label} liked helping in the old folk way, and {child.pronoun()} listened to stories about careful cleaning.")
    world.say(f"One day, {child.label} saw {obj.phrase} beside {animal.phrase} and thought the bubbly bottle was a magic whitening wash.")

    world.para()
    world.say(f"{child.label} wanted to make everything bright at once, so {child.pronoun()} poured a little peroxide over the {obj.label}.")
    _do_belief_error(world, child, obj, narrate=True)
    world.say(f"The {animal_type} backed away, and {elder.label} hurried over with a surprised look.")

    world.para()
    child.memes["ashamed"] = child.memes.get("ashamed", 0) + 1
    world.say(f"{elder.label} gently explained that peroxide is for tiny scrapes and careful spots, not for a whole bath.")
    world.say(f"Then {elder.label} brought a damp rag and showed how to wipe the {obj.label} clean without frightening anyone.")
    obj.meters["cleaning"] = obj.meters.get("cleaning", 0) + 1
    obj.meters["peroxide"] = 0
    obj.meters["clean"] = obj.meters.get("clean", 0) + 1
    animal.memes["calm"] = animal.memes.get("calm", 0) + 1
    child.memes["kind"] = child.memes.get("kind", 0) + 1
    world.say(f"{child.label} apologized, held the rag, and helped finish the job the gentle way.")
    world.say(f"By evening, the {obj.label} was clean again, the bottle of peroxide was back on the shelf, and everyone had learned to ask before guessing.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    animal = f["animal"]
    obj = f["object"]
    return [
        'Write a short folk tale for a young child that includes peroxide, a mistake, and a kind correction.',
        f"Tell a gentle story where {child.label} misunderstands what peroxide is for and {elder.label} sets things right.",
        f"Write a simple village story about {animal.label}, {obj.label}, and a bottle of peroxide.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    animal = f["animal"]
    obj = f["object"]
    return [
        QAItem(
            question=f"Why did {child.label} use peroxide on the {obj.label}?",
            answer=f"{child.label} misunderstood the bubbly peroxide and thought it was a magic wash that could make the {obj.label} bright again.",
        ),
        QAItem(
            question=f"What did {elder.label} say peroxide was for?",
            answer=f"{elder.label} explained that peroxide is for tiny scrapes and careful spots, not for soaking a whole {obj.label}.",
        ),
        QAItem(
            question=f"How was the {obj.label} cleaned at the end?",
            answer=f"The {obj.label} was cleaned gently with a damp rag after {child.label} apologized and helped the careful way.",
        ),
        QAItem(
            question=f"How did the {animal.label} feel during the mistake?",
            answer=f"The {animal.label} felt frightened when the bubbly liquid splashed, but it calmed down once the gentle cleaning began.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag == "peroxide":
            out.append(QAItem(
                question="What is peroxide used for in a house?",
                answer="Peroxide is often kept for carefully cleaning small scrapes or spots, and people use it with care.",
            ))
        elif tag == "wool":
            out.append(QAItem(
                question="What is wool?",
                answer="Wool is a soft fiber from sheep, and people use it to make warm cloth and yarn.",
            ))
        elif tag == "cloth":
            out.append(QAItem(
                question="Why can cloth get stained?",
                answer="Cloth can get stained when mud, paint, or other messy things soak into it.",
            ))
        elif tag == "mud":
            out.append(QAItem(
                question="What is mud?",
                answer="Mud is wet dirt, and it can stick to shoes, cloth, and fur.",
            ))
        elif tag == "clean":
            out.append(QAItem(
                question="Why do people clean carefully around animals?",
                answer="People clean carefully around animals so they do not scare them or hurt their soft fur and feathers.",
            ))
        elif tag == "rag":
            out.append(QAItem(
                question="What is a rag for?",
                answer="A rag is a small cloth used for wiping up spills or cleaning spots by hand.",
            ))
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child can be fooled by the shine of peroxide.
misunderstands(C) :- curious(C), sees(C, peroxide), shiny(peroxide).

% If peroxide touches a whole woolly object, it is not the gentle use.
too_much(peroxide, O) :- woolly(O), soaked(O, peroxide).

% A kind correction happens when an elder explains the right use and a rag is chosen.
resolved(C, O) :- elder(E), misunderstands(C), too_much(peroxide, O), explains(E), rag_used(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("peroxide"), asp.fact("shiny", "peroxide")]
    lines.append(asp.fact("elder"))
    lines.append(asp.fact("explains"))
    lines.append(asp.fact("rag_used", "object"))
    lines.append(asp.fact("woolly", "object"))
    lines.append(asp.fact("soaked", "object", "peroxide"))
    lines.append(asp.fact("curious", "child"))
    lines.append(asp.fact("sees", "child", "peroxide"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_validity() -> bool:
    import asp
    model = asp.one_model(asp_program("#show resolved/2.\n#show misunderstands/1.\n#show too_much/2."))
    atoms = set()
    for sym in model:
        atoms.add((sym.name, tuple(str(a) for a in sym.arguments)))
    expected = {("misunderstands", ("child",)), ("too_much", ("peroxide", "object")), ("resolved", ("child", "object"))}
    return expected.issubset(atoms)


def asp_verify() -> int:
    ok = asp_validity()
    py_ok = True
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, name=None, gender=None, all=False, seed=1, n=1,
            trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False
        ), random.Random(1)))
        py_ok = "peroxide" in sample.story
    except Exception:
        py_ok = False
    if ok and py_ok:
        print("OK: ASP gate and Python story generation both look reasonable.")
        return 0
    print("Mismatch in ASP/Python verification.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about peroxide and misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDER_NAMES)
    ap.add_argument("--animal", choices=[a[0] for a in ANIMALS])
    ap.add_argument("--object", dest="object_name", choices=[o[0] for o in OBJECTS])
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
    place = args.place or rng.choice(list(PLACES))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    elder_name = args.elder or rng.choice(ELDER_NAMES)
    animal = args.animal or rng.choice([a[0] for a in ANIMALS])
    object_name = args.object_name or rng.choice([o[0] for o in OBJECTS])
    return StoryParams(place=place, child_name=child_name, child_gender=child_gender, elder_name=elder_name, animal=animal, object_name=object_name)


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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

    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/2.\n#show misunderstands/1.\n#show too_much/2."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            params = StoryParams(
                place=place,
                child_name=CHILD_NAMES[0],
                child_gender="girl",
                elder_name=ELDER_NAMES[0],
                animal=ANIMALS[0][0],
                object_name=OBJECTS[0][0],
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
