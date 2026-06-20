#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mum_transformation_tall_tale.py
===============================================================

A standalone storyworld for a tall-tale transformation about a child and mum.
The premise is small and concrete: a child wants to impress mum with a grand
act, but the ordinary thing in the room gets transformed into something wildly
bigger, safer, and more useful. The story keeps the transformation grounded in
world state: wonder grows, fear drops, the transformed object changes function,
and the ending image proves the new shape matters.

Domain sketch:
- A child and mum are in a small homely setting.
- One ordinary object is chosen for a transformation.
- The transformation is dramatic but harmless.
- Mum responds with warmth and wonder, and the child learns that big magic can
  still be kind and practical.

The world supports:
- seedable random generation
- -n / --all / --seed / --trace / --qa / --json / --asp / --verify / --show-asp
- a Python reasonableness gate
- an inline ASP twin
- three Q&A sets grounded in simulated state, not by parsing the final story

This script is intentionally self-contained and stdlib-only.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

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
        return {"mother": "mum", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    scene: str
    opening: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    id: str
    label: str
    ordinary_use: str
    transformed_use: str
    size: str
    transform_verb: str
    is_transformable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    trigger: str
    glow: str
    result_label: str
    result_use: str
    marvel: str
    tags: set[str] = field(default_factory=set)


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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_wonder(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    obj = world.get("object")
    if child.memes["wonder"] < THRESHOLD:
        return out
    sig = ("wonder", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] += 1
    out.append("")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    obj = world.get("object")
    trans = world.facts["transformation"]
    if obj.meters["shimmer"] < THRESHOLD:
        return out
    sig = ("transform", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obj.attrs["transformed"] = "yes"
    obj.attrs["new_label"] = trans.result_label
    obj.attrs["new_use"] = trans.result_use
    obj.meters["magic"] += 1
    out.append("")
    return out


CAUSAL_RULES = [Rule("wonder", _r_wonder), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def reasonableness_gate(setting: Setting, obj: ObjectSpec, trans: Transformation) -> bool:
    return setting.id in SETTINGS and obj.is_transformable and bool(trans.result_label)


def choose_ending(trans: Transformation) -> str:
    return trans.marvel


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("object").meters["shimmer"] += 1
    propagate(sim, narrate=False)
    obj = sim.get("object")
    return {
        "transformed": obj.attrs.get("transformed") == "yes",
        "magic": obj.meters["magic"],
    }


def tell(setting: Setting, objspec: ObjectSpec, trans: Transformation,
         child_name: str = "Milo", child_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, role="child"))
    mum = world.add(Entity(id="mum", kind="character", type="mother", role="parent", label="mum"))
    obj = world.add(Entity(id="object", type="thing", label=objspec.label, attrs={"use": objspec.ordinary_use}))
    world.facts["setting"] = setting
    world.facts["object_spec"] = objspec
    world.facts["transformation"] = trans
    world.facts["child_name"] = child_name
    world.facts["child_gender"] = child_gender

    child.memes["wonder"] = 0.0
    child.memes["joy"] = 0.0
    mum.memes["pride"] = 0.0

    world.say(f"On a bright day in {setting.scene}, {child_name} and mum were busy with an ordinary little thing.")
    world.say(setting.opening)
    world.say(f"{child_name} loved the {objspec.label} for {objspec.ordinary_use}, but dreamed it could do {objspec.transformed_use}.")
    world.para()

    child.memes["wonder"] += 1
    world.say(f"Then {child_name} whispered a tall-tale promise: \"If I give it a shine, it might just grow into {trans.result_label}!\"")
    world.say(f"Mum chuckled, because in a tall tale, a good heart can make the smallest thing behave like a marvel.")
    obj.meters["shimmer"] += 1
    predict(world)
    propagate(world, narrate=False)

    obj.attrs["transformed"] = "yes"
    obj.attrs["new_label"] = trans.result_label
    obj.attrs["new_use"] = trans.result_use

    world.para()
    world.say(f"A warm sparkle ran over the {objspec.label}; it stretched, brightened, and became {trans.result_label}.")
    world.say(f"Now it could {trans.result_use}, and the change was so grand it felt like the room had learned to sing.")
    mum.memes["pride"] += 1
    child.memes["joy"] += 1
    world.say(f"Mum clapped softly and said, \"That is the sort of magic that helps a home.\"")
    world.para()
    world.say(f"By supper time, the new {trans.result_label} was still shining, and {choose_ending(trans)}.")
    world.say(f"{setting.ending_image}")

    world.facts.update(
        child=child,
        mum=mum,
        object=obj,
        transformed=obj.attrs.get("transformed") == "yes",
        ending_image=setting.ending_image,
    )
    return world


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        scene="a little kitchen with a tick-tock clock and a sunny window",
        opening="The table held a floury bowl, a wooden spoon, and a crusty little loaf waiting on the sill.",
        ending_image="In the windowlight, the loaf's crust glowed like a tiny sunrise.",
        tags={"kitchen", "home"},
    ),
    "garden": Setting(
        id="garden",
        scene="a garden behind a crooked fence and a row of bean poles",
        opening="A bent wheelbarrow sat beside a patch of dirt, and a clay pot waited by the gate.",
        ending_image="Across the fence, the transformed thing cast a long, cheerful shadow over the beans.",
        tags={"garden", "home"},
    ),
    "barn": Setting(
        id="barn",
        scene="a red barn with rafters high as a storybook sky",
        opening="There was a straw hat on a peg, a broom in the corner, and a milk pail near the door.",
        ending_image="Under the rafters, the new marvel shone as if the barn had grown a second moon.",
        tags={"barn", "home"},
    ),
}

OBJECTS = {
    "loaf": ObjectSpec("loaf", "little loaf", "feeding the ducks", "feeding a whole parade", "small", "shimmer", True, {"food"}),
    "wheelbarrow": ObjectSpec("wheelbarrow", "wheelbarrow", "carrying soil", "carrying a mountain of roses", "big", "sparkle", True, {"yard"}),
    "hat": ObjectSpec("hat", "straw hat", "shading a brow", "shading a whole summer field", "small", "glow", True, {"clothing"}),
}

TRANSFORMATIONS = {
    "sunburst": Transformation("sunburst", "shine", "golden", "sunburst lantern", "light the whole room", "so bright it could wake the moon", {"light"}),
    "helper": Transformation("helper", "wish", "silver", "helper cart", "carry the heaviest load without a groan", "so strong it seemed built by the wind", {"utility"}),
    "songbird": Transformation("songbird", "hum", "bright", "songbird wheel", "turn every bump into music", "so merry it made the dust dance", {"music"}),
}

CHILD_NAMES = ["Milo", "Nell", "Ruben", "Ada", "Ivy", "Pip", "Toby", "June"]
GENDERS = ["girl", "boy"]


@dataclass
class StoryParams:
    setting: str
    obj: str
    transformation: str
    child_name: str
    child_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for o in OBJECTS:
            for t in TRANSFORMATIONS:
                combos.append((s, o, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about mum and a transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="obj", choices=OBJECTS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--child-name", dest="child_name")
    ap.add_argument("--child-gender", choices=GENDERS)
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
    if args.setting and args.obj and args.transformation:
        if not reasonableness_gate(SETTINGS[args.setting], OBJECTS[args.obj], TRANSFORMATIONS[args.transformation]):
            raise StoryError("This transformation setup is not reasonable.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.obj is None or c[1] == args.obj)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, transformation = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(GENDERS)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    return StoryParams(setting, obj, transformation, child_name, child_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a small child that includes the word "mum" and a magical transformation in {f["setting"].scene}.',
        f"Tell a warm, exaggerated story where {f['child_name']} makes a humble {f['object_spec'].label} turn into {f['transformation'].result_label}.",
        f"Write a simple tall tale about mum, a shiny change, and a finish that proves the transformed thing is useful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mum = f["mum"]
    objspec = f["object_spec"]
    trans = f["transformation"]
    setting = f["setting"]
    obj = f["object"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {f['child_name']} and mum in {setting.scene}. The child and mum are the two people who watch the small wonder happen.",
        ),
        QAItem(
            question=f"What happened to the {objspec.label}?",
            answer=f"It changed into {obj.attrs.get('new_label', trans.result_label)}. The story treats the change as a tall-tale transformation, so the ordinary thing becomes something grand and useful.",
        ),
        QAItem(
            question="Why did mum smile at the end?",
            answer=f"Mum smiled because the new thing could {obj.attrs.get('new_use', trans.result_use)}. It was still the same story-world object, but it now helped the home in a bigger way.",
        ),
    ]
    if f.get("transformed"):
        qa.append(QAItem(
            question="How did the ending show that the change worked?",
            answer=f"The ending image shows the transformed thing still shining in {setting.scene}. That matters because it proves the change was not just pretend; it stayed real in the world.",
        ))
    return qa


KNOWLEDGE = {
    "mum": [("Who is mum?",
             "Mum is a child's mother. In many stories, mum is the grown-up who keeps the home warm, wise, and safe.")],
    "transformation": [("What is a transformation?",
                        "A transformation is a change from one thing into another. In stories, it can be magical, surprising, or very big.")],
    "lantern": [("What is a lantern?",
                 "A lantern is a light that can glow brightly and help people see in the dark.")],
    "barn": [("What is a barn?",
              "A barn is a big building on a farm where tools, hay, or animals might be kept.")],
    "garden": [("What grows in a garden?",
                 "A garden can grow flowers, beans, herbs, and many other plants.")],
    "kitchen": [("What do people do in a kitchen?",
                 "People cook food, wash dishes, and gather together in a kitchen.")],
}
KNOWLEDGE_ORDER = ["mum", "transformation", "lantern", "barn", "garden", "kitchen"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["setting"].tags) | set(world.facts["transformation"].tags) | {"mum"}
    out: list[QAItem] = []
    for k in KNOWLEDGE_ORDER:
        if k in tags:
            for q, a in KNOWLEDGE[k]:
                out.append(QAItem(q, a))
    return out


ASP_RULES = r"""
compatible(S,O,T) :- setting(S), object(O), transformation(T).
outcome(transformed) :- chosen_object(O), shimmer(O), not blocked(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo sets differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} attrs={e.attrs}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS[params.obj], TRANSFORMATIONS[params.transformation],
                 params.child_name, params.child_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def _pick_random(rng: random.Random) -> tuple[str, str, str]:
    return rng.choice(list(valid_combos()))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(s, o, t, "Milo", "boy")) for s, o, t in valid_combos()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
