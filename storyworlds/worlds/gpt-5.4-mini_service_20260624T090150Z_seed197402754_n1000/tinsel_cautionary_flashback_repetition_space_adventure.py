#!/usr/bin/env python3
"""
A standalone story world for a small Space Adventure tale with tinsel,
cautionary flashback, and repetition.

Premise:
- A child astronaut loves a shiny tinsel ribbon in a space cabin.
- The ribbon can drift into vents, buttons, or the moon-rover wheel.
- A cautious helper warns about a past mishap.
- The child remembers the flashback, repeats a safety rule, and fixes the problem.

This world keeps a simple, state-driven model:
- physical meters: drift, snag, blocked, safe, shine
- emotional memes: wonder, worry, relief, pride, caution

The story emerges from simulated state rather than template swapping.
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
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def cap(self, text: str) -> str:
        return text[:1].upper() + text[1:] if text else text


@dataclass
class Setting:
    place: str
    detail: str
    includes: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    risk_zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    label: str
    phrase: str
    purpose: str
    guards: set[str]
    place: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone

    def actors(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    object: str
    prop: str
    seed: Optional[int] = None


SETTINGS = {
    "space_cabin": Setting(
        place="the space cabin",
        detail="A round window showed the starry dark, and the control panels blinked softly.",
        includes={"cabins", "vents", "buttons"},
    ),
    "moon_bay": Setting(
        place="the moon bay",
        detail="The airlock stood beside a quiet rover, and pale dust waited on the floor.",
        includes={"rover", "floor", "panel"},
    ),
    "star_lab": Setting(
        place="the star lab",
        detail="Tiny tools floated near a workbench, and the overhead light made everything gleam.",
        includes={"bench", "tools", "lights"},
    ),
}

OBJECTS = {
    "tinsel": ObjectSpec(
        label="tinsel",
        phrase="a bright silver tinsel ribbon",
        risk_zone="vents",
        tags={"tinsel", "shine"},
    ),
    "star_charm": ObjectSpec(
        label="star charm",
        phrase="a tiny star charm on a string",
        risk_zone="buttons",
        tags={"star", "shine"},
    ),
    "moon_map": ObjectSpec(
        label="moon map",
        phrase="a folded moon map with shiny corners",
        risk_zone="rover",
        tags={"map", "paper"},
    ),
}

PROPS = {
    "clip": Prop(
        label="clip",
        phrase="a little magnetic clip",
        purpose="hold the shiny thing in place",
        guards={"vents", "buttons", "rover"},
        place="anywhere",
    ),
    "pouch": Prop(
        label="pouch",
        phrase="a soft storage pouch",
        purpose="keep loose things from drifting",
        guards={"vents", "buttons", "rover"},
        place="anywhere",
    ),
    "tape": Prop(
        label="tape",
        phrase="a strip of sticky space tape",
        purpose="pin the ribbon to a safe spot",
        guards={"buttons", "rover"},
        place="control panel",
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Nia", "Tessa", "Ivy", "Zora"]
BOY_NAMES = ["Owen", "Kai", "Milo", "Jace", "Leo", "Arlo"]
HELPERS = ["captain", "pilot", "mechanic", "guide"]
TRAITS = ["brave", "curious", "careful", "spirited"]


def choose_story_options(rng: random.Random) -> StoryParams:
    place = rng.choice(list(SETTINGS))
    hero_type = rng.choice(["girl", "boy"])
    helper_type = rng.choice(["captain", "pilot", "mechanic"])
    obj = rng.choice(list(OBJECTS))
    prop = rng.choice(list(PROPS))
    return StoryParams(
        place=place,
        hero=rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES),
        hero_type=hero_type,
        helper=rng.choice(["Nova", "Pip", "Rin"]),
        helper_type=helper_type,
        object=obj,
        prop=prop,
    )


def valid_combo(params: StoryParams) -> bool:
    obj = OBJECTS[params.object]
    prop = PROPS[params.prop]
    return obj.risk_zone in prop.guards


def explain_rejection(params: StoryParams) -> str:
    obj = OBJECTS[params.object]
    prop = PROPS[params.prop]
    return (
        f"(No story: {prop.label} would not really keep the {obj.label} safe from drifting "
        f"into {obj.risk_zone}. The cautionary fix has to match the real risk.)"
    )


def story_setup(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} little astronaut who loved shiny things aboard "
        f"{world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {obj.phrase} because it sparkled like a tiny comet."
    )
    world.say(
        f"{helper.id} kept an eye on the cabin and liked everything neat and safe."
    )


def cautionary_flashback(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    world.para()
    world.say(
        f"One day, {hero.id} reached for the {obj.label}, but {helper.id} lifted a hand."
    )
    world.say(
        f'"Careful," {helper.id} said. "Last time a loose shiny ribbon drifted into a vent, '
        f'and the fans hummed like angry bees."'
    )
    world.say(
        f"{hero.id} remembered that day at once, and the old worry came back like a shadow."
    )
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.facts["flashback"] = True
    world.facts["past_trouble"] = "vent snag"


def repeat_rule(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    world.say(
        f'{hero.id} repeated, "Loose shiny things stay clipped, tucked, or taped."'
    )
    world.say(
        f'{helper.id} nodded and repeated it too: "Clipped, tucked, or taped."'
    )
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0.0) + 0.5
    world.facts["repetition"] = True


def apply_prop(world: World, hero: Entity, helper: Entity, obj: Entity, prop: Prop) -> Entity:
    p = world.add(Entity(
        id=prop.label,
        kind="thing",
        type="tool",
        label=prop.label,
        phrase=prop.phrase,
        owner=helper.id,
        caretaker=helper.id,
    ))
    p.meters["safe"] = 1.0
    world.say(
        f"{helper.id} found {prop.phrase}, and together they used it to hold the {obj.label} in place."
    )
    return p


def resolve_world(world: World, hero: Entity, helper: Entity, obj: Entity, prop: Prop) -> None:
    world.para()
    world.say(
        f"{hero.id} clipped the {obj.label} near the safe panel, far from the {obj.label}'s risky drift zone."
    )
    world.say(
        f"The shiny ribbon stayed still, and the cabin stayed quiet."
    )
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
    world.facts["resolved"] = True
    world.facts["ending_image"] = f"{obj.label} held safe by a {prop.label}"


def tell_story(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.place}")
    if params.object not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object}")
    if params.prop not in PROPS:
        raise StoryError(f"Unknown prop: {params.prop}")
    if not valid_combo(params):
        raise StoryError(explain_rejection(params))

    rng = random.Random(params.seed)
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        traits=[rng.choice(TRAITS), "little"],
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=params.helper_type,
        traits=["careful"],
    ))
    obj_spec = OBJECTS[params.object]
    obj = world.add(Entity(
        id=obj_spec.label,
        kind="thing",
        type="treasure",
        label=obj_spec.label,
        phrase=obj_spec.phrase,
        owner=hero.id,
    ))

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["object"] = obj
    world.facts["setting"] = setting
    world.facts["prop"] = PROPS[params.prop]
    world.facts["params"] = params

    story_setup(world, hero, helper, obj)
    cautionary_flashback(world, hero, helper, obj)
    repeat_rule(world, hero, helper, obj)
    apply_prop(world, hero, helper, obj, PROPS[params.prop])
    resolve_world(world, hero, helper, obj, PROPS[params.prop])
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    obj = world.facts["object"]
    return [
        f"Write a gentle Space Adventure story about {p.hero} and {obj.label} in {world.setting.place}.",
        f"Tell a cautionary tale where a shiny {obj.label} is kept safe with a simple rule.",
        f"Write a story with a flashback and repetition about loose things in a spaceship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    obj = world.facts["object"]
    prop = world.facts["prop"]
    return [
        QAItem(
            question=f"What did {hero.id} love in the story?",
            answer=f"{hero.id} loved {obj.phrase}, which shone like a tiny comet.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {hero.id} about the shiny thing?",
            answer=(
                f"{helper.id} warned {hero.id} because a loose shiny ribbon had once drifted into a vent, "
                f"and that could make the cabin unsafe."
            ),
        ),
        QAItem(
            question=f"How did they keep the {obj.label} safe at the end?",
            answer=(
                f"They used {prop.phrase} to hold the {obj.label} in place, so it stayed away from the risky place."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} repeat to remember the rule?",
            answer='They repeated, "Loose shiny things stay clipped, tucked, or taped."',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tinsel?",
            answer="Tinsel is a thin, shiny decoration that sparkles and can drift around if it is loose.",
        ),
        QAItem(
            question="Why is it important to keep loose things from floating in space?",
            answer="Loose things can drift into vents, buttons, or other equipment, which can cause trouble.",
        ),
        QAItem(
            question="What does a cautionary story do?",
            answer="A cautionary story gives a warning about a danger so someone can make a safer choice.",
        ),
        QAItem(
            question="Why do people repeat safety rules?",
            answer="People repeat safety rules to help everyone remember them when they need them most.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {' '.join(bits) if bits else '(empty)'}")
    lines.append(f"facts={ {k: v for k, v in world.facts.items() if k != 'params'} }")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with tinsel, caution, flashback, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["captain", "pilot", "mechanic"])
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--prop", choices=PROPS)
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
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["captain", "pilot", "mechanic"])
    obj = args.object or rng.choice(list(OBJECTS))
    prop = args.prop or rng.choice(list(PROPS))
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["Nova", "Pip", "Rin"])
    params = StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, object=obj, prop=prop)
    if not valid_combo(params):
        raise StoryError(explain_rejection(params))
    return params


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, spec in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("risk_zone", oid, spec.risk_zone))
        for t in sorted(spec.tags):
            lines.append(asp.fact("tag", oid, t))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        for g in sorted(prop.guards):
            lines.append(asp.fact("guards", pid, g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Obj, Prop) :- object(Obj), prop(Prop), risk_zone(Obj, Z), guards(Prop, Z).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((oid, pid) for oid in OBJECTS for pid in PROPS if OBJECTS[oid].risk_zone in PROPS[pid].guards)
    cl = asp_valid()
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python:", py)
    print("asp:", cl)
    return 1


CURATED = [
    StoryParams(place="space_cabin", hero="Lina", hero_type="girl", helper="Nova", helper_type="captain", object="tinsel", prop="clip"),
    StoryParams(place="moon_bay", hero="Kai", hero_type="boy", helper="Pip", helper_type="pilot", object="tinsel", prop="pouch"),
    StoryParams(place="star_lab", hero="Mara", hero_type="girl", helper="Rin", helper_type="mechanic", object="star_charm", prop="tape"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid()
        for o, p in pairs:
            print(o, p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
