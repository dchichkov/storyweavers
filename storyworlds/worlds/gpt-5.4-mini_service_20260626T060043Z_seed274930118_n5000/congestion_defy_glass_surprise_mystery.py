#!/usr/bin/env python3
"""
A standalone storyworld for a small mystery about a surprise, a defiance, and a
glass object caught in congestion.

The source tale imagined here:
---
A child named Nora is helping her grandmother run a tiny library cart through a
crowded station hall. The hallway is congested, and a glass paperweight from the
library display keeps catching Nora's eye because it reflects the lamps like a
secret clue. Her grandmother tells Nora not to hurry into the packed crowd, but
Nora defies the warning and slips ahead.

Then a surprise happens: the paperweight rolls from the cart and stops beside a
boot print. Nora notices that the crowded hall, the broken path of light, and
the little clues all fit together. She slows down, asks for help, and the
surprise turns into a careful discovery instead of a disaster.
"""

from __future__ import annotations

import argparse
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "nora"}
        male = {"boy", "father", "dad", "man", "grandfather", "sam"}
        if self.type in female or self.id.lower() in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male or self.id.lower() in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the station hall"
    label: str = "station hall"
    crowded: bool = True
    detail: str = "The station hall was busy, and people moved in short, careful steps."


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    can_break: bool = False
    can_reflect: bool = False


@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        return c


def _narrate_mystery_clue(world: World, obj: Entity) -> list[str]:
    out = []
    if obj.meters.get("shined", 0) >= THRESHOLD and ("glow", obj.id) not in world.fired:
        world.fired.add(("glow", obj.id))
        out.append(f"Light slipped off the glass and landed on the floor like a clue.")
    return out


def _narrate_congestion(world: World, actor: Entity) -> list[str]:
    out = []
    if actor.memes.get("impatient", 0) >= THRESHOLD and ("crowd", actor.id) not in world.fired:
        world.fired.add(("crowd", actor.id))
        out.append(f"The crowded hall made it hard to see who was ahead.")
    return out


def _narrate_breakrisk(world: World, obj: Entity) -> list[str]:
    out = []
    if obj.meters.get("jostled", 0) >= THRESHOLD and obj.meters.get("glass", 0) >= THRESHOLD:
        sig = ("risk", obj.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(f"The glass wobbled near the edge of the cart.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for e in list(world.entities.values()):
            for s in _narrate_mystery_clue(world, e):
                world.say(s)
                changed = True
            for s in _narrate_congestion(world, e):
                world.say(s)
                changed = True
            for s in _narrate_breakrisk(world, e):
                world.say(s)
                changed = True


SETTINGS = {
    "station": Setting(place="the station hall", label="station hall", crowded=True,
                       detail="The station hall was busy, and people moved in short, careful steps."),
    "market": Setting(place="the market lane", label="market lane", crowded=True,
                      detail="The market lane was packed, with baskets and coats brushing close together."),
    "museum": Setting(place="the museum corridor", label="museum corridor", crowded=True,
                      detail="The museum corridor felt crowded, and every footstep echoed softly."),
}

OBJECTS = {
    "paperweight": ObjectSpec(label="paperweight", phrase="a glass paperweight", type="paperweight",
                              region="hand", can_break=True, can_reflect=True),
    "jar": ObjectSpec(label="jar", phrase="a glass jar with a tight lid", type="jar",
                      region="hand", can_break=True, can_reflect=False),
    "bottle": ObjectSpec(label="bottle", phrase="a glass bottle from the shop", type="bottle",
                         region="hand", can_break=True, can_reflect=False),
}

GIRL_NAMES = ["Nora", "Mina", "Ivy", "Lena", "June", "Rose"]
BOY_NAMES = ["Owen", "Eli", "Finn", "Tate", "Theo", "Noah"]
TRAITS = ["curious", "careful", "spirited", "quiet", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, obj) for place in SETTINGS for obj in OBJECTS if place in {"station", "market", "museum"}]


@dataclass
class WorldState:
    hero: Entity
    helper: Entity
    obj: Entity
    setting: Setting
    surprise: bool = False
    defy: bool = False
    resolved: bool = False
    clue_seen: bool = False


def tell(setting: Setting, obj_spec: ObjectSpec, hero_name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, traits=["little", trait, "mystery-loving"]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    obj = world.add(Entity(id="Object", type=obj_spec.type, label=obj_spec.label, phrase=obj_spec.phrase, owner=helper.id))
    obj.meters["glass"] = 1.0
    obj.meters["shined"] = 1.0 if obj_spec.can_reflect else 0.0
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["obj"] = obj
    world.facts["obj_spec"] = obj_spec
    world.facts["setting"] = setting

    world.say(f"{hero_name} was a little {trait} child who loved noticing small things.")
    world.say(f"{hero.pronoun().capitalize()} and {helper.label} were in {setting.place}.")
    world.say(f"{setting.detail}")
    world.say(f"They were carrying {obj.phrase}, and the glass looked shiny in the light.")
    world.para()

    world.say(f"{hero_name} kept glancing at the glass because it looked like a secret clue.")
    world.say(f"The hall was congested, so every step needed care.")
    hero.memes["curiosity"] = 1.0
    hero.memes["impatient"] = 1.0
    obj.meters["jostled"] = 1.0
    propagate(world)
    world.para()

    hero.memes["defiance"] = 1.0
    world.say(f'“Wait,” {helper.pronoun().capitalize()} said, “don’t hurry into the crowd.”')
    world.say(f"But {hero_name} defied the warning and slipped ahead anyway.")
    world.say(f"That was when a surprise happened: the glass shifted on the cart.")
    world.facts["defy"] = True
    world.facts["surprise"] = True
    world.para()

    if obj_spec.can_break:
        obj.meters["broken"] = 1.0
        world.say(f"The object tipped, caught the light, and stopped near a boot print.")
    else:
        world.say(f"The object tipped, but {hero_name} caught it before it could fall.")
    world.say(f"{hero_name} looked again and understood the clue: the crowded place had caused the problem.")
    world.say(f"{hero_name} slowed down, asked for help, and guided the cart through the gap.")
    world.say(f"In the end, the surprise became a careful discovery instead of a mess.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj = f["obj"]
    return [
        f'Write a short mystery story for a young child about congestion, defiance, and a glass {obj.label}.',
        f"Tell a gentle surprise story where {hero.id} defies {helper.label} and notices a clue in the glass.",
        f'Write a child-friendly mystery that includes the words "congestion", "defy", and "glass".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj = f["obj"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a curious child who is helping {helper.label} in the crowded place.",
        ),
        QAItem(
            question=f"What made the hall feel hard to move through?",
            answer=f"The hall felt hard to move through because it was congested and lots of people were moving close together.",
        ),
        QAItem(
            question=f"What did {hero.id} defy?",
            answer=f"{hero.id} defied {helper.label}'s warning not to hurry into the crowd.",
        ),
        QAItem(
            question=f"What surprise involved the glass object?",
            answer=f"The glass object tipped on the cart and stopped near a boot print, which helped {hero.id} notice the clue.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"It ended with {hero.id} slowing down, asking for help, and turning the surprise into a careful discovery.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does congestion mean?",
            answer="Congestion means a place is crowded, so it is hard to move through easily.",
        ),
        QAItem(
            question="What is glass?",
            answer="Glass is a hard, clear material that can be shiny and break if it is dropped.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect to happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
crowded(place) :- setting(place).
at_risk(O) :- glass(O).
surprise_event :- crowded(_), at_risk(_).
defiance(H) :- defied(H).
resolved_story :- surprise_event, defiance(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.crowded:
            lines.append(asp.fact("crowded", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.can_break:
            lines.append(asp.fact("glass", oid))
        if o.can_reflect:
            lines.append(asp.fact("reflects", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show crowded/1. #show glass/1. #show resolved_story/0."))
    atoms = set((a.name, len(a.arguments)) for a in model)
    want = {("crowded", 1), ("glass", 1)}
    if ("resolved_story", 0) not in atoms:
        print("MISMATCH: ASP did not derive resolved_story.")
        return 1
    if not want.issubset(atoms):
        print("MISMATCH: ASP atoms missing expected facts.")
        return 1
    print("OK: ASP parity gate ran successfully.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about congestion, defiance, glass, and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["grandmother", "mother", "father", "uncle", "aunt"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    obj = args.object or rng.choice(list(OBJECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["grandmother", "mother", "father", "uncle", "aunt"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, object=obj, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBJECTS[params.object], params.name, params.gender, params.helper, params.trait)
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
    StoryParams(place="station", object="paperweight", name="Nora", gender="girl", helper="grandmother", trait="curious"),
    StoryParams(place="market", object="jar", name="Eli", gender="boy", helper="aunt", trait="thoughtful"),
    StoryParams(place="museum", object="bottle", name="Mina", gender="girl", helper="mother", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show crowded/1. #show glass/1. #show resolved_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show crowded/1. #show glass/1. #show resolved_story/0."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
