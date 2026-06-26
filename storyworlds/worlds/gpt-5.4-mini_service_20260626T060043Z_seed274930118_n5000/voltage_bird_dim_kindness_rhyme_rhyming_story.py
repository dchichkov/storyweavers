#!/usr/bin/env python3
"""
A standalone storyworld for a tiny rhyming tale about a bird, a low-voltage
lamp, and a kind fix.

The domain is deliberately small:
- A little bird keeps a tiny singing light.
- The light runs on voltage.
- When the voltage gets dim, the bird gets worried.
- A kind helper, a rhyme, and a careful recharge bring the brightness back.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- a simulated world that drives the prose
- an inline ASP twin and a Python reasonableness gate
- story QA plus world knowledge QA
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

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

PLACES = {
    "nest": "the nest",
    "garden": "the garden fence",
    "porch": "the porch rail",
    "meadow": "the meadow path",
}

HELPERS = {
    "child": "a child",
    "grandparent": "a grandparent",
    "neighbor": "a neighbor",
}

NAMES = ["Mina", "Toby", "Luna", "Pip", "Mara", "Niko", "Ruby", "Theo"]
BIRD_NAMES = ["Tweet", "Skylark", "Blue", "Pipit", "Wren"]

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather", "child"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ActorSpec:
    name: str
    type: str
    trait: str


@dataclass
class LightSpec:
    label: str
    phrase: str
    type: str
    region: str
    needs: str  # voltage kind it depends on
    plural: bool = False


@dataclass
class FixSpec:
    id: str
    label: str
    phrase: str
    helps: set[str]
    clue: str
    tail: str


@dataclass
class StoryParams:
    place: str
    bird_name: str
    bird_trait: str
    helper_kind: str
    helper_name: str
    light: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# World ingredients
# ---------------------------------------------------------------------------

SETTINGS = {
    "nest": Setting(place=PLACES["nest"], outdoors=True, affords={"humming", "rhyme"}),
    "garden": Setting(place=PLACES["garden"], outdoors=True, affords={"humming", "rhyme"}),
    "porch": Setting(place=PLACES["porch"], outdoors=True, affords={"humming", "rhyme"}),
    "meadow": Setting(place=PLACES["meadow"], outdoors=True, affords={"humming", "rhyme"}),
}

LIGHTS = {
    "lantern": LightSpec(
        label="little lantern",
        phrase="a little lantern with a warm glass face",
        type="lantern",
        region="wing",
        needs="voltage",
    ),
    "glowstone": LightSpec(
        label="glow pebble",
        phrase="a smooth glow pebble",
        type="glowstone",
        region="wing",
        needs="voltage",
    ),
}

FIXES = {
    "battery": FixSpec(
        id="battery",
        label="battery pack",
        phrase="a tiny battery pack",
        helps={"voltage"},
        clue="battery",
        tail="slid the battery pack into place",
    ),
    "kind_word": FixSpec(
        id="kind_word",
        label="kind words",
        phrase="kind words in a soft rhyme",
        helps={"mood"},
        clue="kindness",
        tail="spoke softly and shared a rhyme",
    ),
    "charge_stand": FixSpec(
        id="charge_stand",
        label="charging stand",
        phrase="a little charging stand",
        helps={"voltage"},
        clue="charge",
        tail="rested the lantern on the charging stand",
    ),
}

TRAITS = ["gentle", "curious", "cheerful", "shy", "bright", "kind"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def light_at_risk(light: LightSpec) -> bool:
    return light.needs == "voltage"


def select_fix(light: LightSpec) -> Optional[FixSpec]:
    for fix in (FIXES["battery"], FIXES["charge_stand"]):
        if light.needs in fix.helps:
            return fix
    return None


def explain_rejection(light: LightSpec) -> str:
    return (
        f"(No story: the {light.label} only needs a voltage fix, and the kind-word "
        f"idea would comfort the bird but would not actually light it back up.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------


def rhyme_line(name: str, bird_name: str) -> str:
    return f"{bird_name} gave a hum, and {name} said, “What a sweet little rhyme!”"


def perform_hum(world: World, bird: Entity) -> None:
    bird.memes["hope"] = bird.memes.get("hope", 0.0) + 1
    world.say(f"{bird.id} hummed a tiny tune to keep courage in the air.")


def voltage_drop(world: World, light: Entity, amount: float = 1.0) -> None:
    light.meters["voltage"] = light.meters.get("voltage", 0.0) - amount
    if light.meters["voltage"] < 0:
        light.meters["voltage"] = 0.0


def voltage_rise(world: World, light: Entity, amount: float = 1.0) -> None:
    light.meters["voltage"] = light.meters.get("voltage", 0.0) + amount


def predict_failure(world: World, bird: Entity, light: Entity) -> dict[str, object]:
    sim = world.copy()
    sim_light = sim.get(light.id)
    voltage_drop(sim, sim_light, 1.0)
    dim = sim_light.meters.get("voltage", 0.0) < THRESHOLD
    return {"dim": dim}


def setup(world: World, bird: Entity, helper: Entity, light: Entity) -> None:
    world.say(
        f"{bird.id} was a little {bird.type} with a {bird.meters.get('wing', 0):.0f}-winged dream: "
        f"to keep the {light.label} glowing bright."
    )
    world.say(
        f"{bird.id} liked {world.setting.place}, because the air there felt open and light."
    )
    world.say(
        f"{helper.id} was {HELPERS[helper.type]} who noticed when small things needed care."
    )


def turn(world: World, bird: Entity, helper: Entity, light: Entity) -> None:
    world.para()
    world.say(
        f"One evening, the {light.label} went dim, and its voltage slipped low."
    )
    bird.memes["worry"] = bird.memes.get("worry", 0.0) + 1
    world.say(
        f"{bird.id} looked up and worried, because a dim light can make a tiny song feel sad."
    )
    perform_hum(world, bird)
    world.say(rhyme_line(helper.id, bird.id))


def resolve(world: World, bird: Entity, helper: Entity, light: Entity, fix: FixSpec) -> None:
    world.para()
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    bird.memes["joy"] = bird.memes.get("joy", 0.0) + 1
    if fix.id in {"battery", "charge_stand"}:
        voltage_rise(world, light, 2.0)
    world.say(
        f"{helper.id} saw the low glow and smiled with kindness."
    )
    world.say(
        f'"Let’s help it gently," {helper.id} said, and {fix.tail}.'
    )
    world.say(
        f"The {light.label} brightened at once, and its voltage felt full again."
    )
    world.say(
        f"{bird.id} fluttered close, and the little song ended in a happy shine."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    bird = world.add(Entity(
        id=params.bird_name,
        kind="character",
        type="bird",
        label="bird",
        meters={"wing": 2.0},
        memes={"hope": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_kind,
        label=HELPERS[params.helper_kind],
        memes={"kindness": 1.0},
    ))
    light_spec = LIGHTS[params.light]
    light = world.add(Entity(
        id=light_spec.type,
        kind="thing",
        type=light_spec.type,
        label=light_spec.label,
        phrase=light_spec.phrase,
        owner=bird.id,
        meters={"voltage": 2.0},
    ))

    world.facts.update(
        bird=bird,
        helper=helper,
        light=light,
        light_spec=light_spec,
        fix=select_fix(light_spec),
        place=params.place,
    )

    setup(world, bird, helper, light)
    turn(world, bird, helper, light)
    fix = select_fix(light_spec)
    if fix is None:
        raise StoryError(explain_rejection(light_spec))
    resolve(world, bird, helper, light, fix)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bird = f["bird"]
    helper = f["helper"]
    light_spec = f["light_spec"]
    return [
        f"Write a short rhyming story for a child about {bird.id}, kindness, and a dim {light_spec.label}.",
        f"Tell a gentle story where {helper.id} helps a bird fix low voltage with a rhyme.",
        f"Write a tiny story that includes the words voltage and kindness and ends with a bright light.",
    ]


def story_qa(world: World) -> list[QAItem]:
    bird: Entity = world.facts["bird"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    light: Entity = world.facts["light"]  # type: ignore[assignment]
    place = world.facts["place"]
    qa = [
        QAItem(
            question=f"Who worried when the {light.label} went dim at {place}?",
            answer=f"{bird.id} worried, because the light was getting dim and the voltage was low.",
        ),
        QAItem(
            question=f"What kind thing did {helper.id} do to help?",
            answer=f"{helper.id} showed kindness, spoke softly, and helped fix the low voltage.",
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=f"The {light.label} brightened again, and {bird.id} fluttered close with a happy little song.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question=f"How was the dim light made bright again?",
                answer=f"{helper.id} used a small voltage fix, so the {light.label} could shine again.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "voltage": [
        QAItem(
            question="What is voltage?",
            answer="Voltage is a kind of electrical push that helps power things like lights.",
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone or something.",
        )
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like light and bright.",
        )
    ],
    "bird": [
        QAItem(
            question="What do birds usually do?",
            answer="Birds can fly, hop, sing, and build nests.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [qa for key in ("voltage", "kindness", "rhyme", "bird") for qa in WORLD_KNOWLEDGE[key]]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A light is at risk when it depends on voltage.
at_risk(L) :- light(L), needs(L, voltage).

% A fix is reasonable when it helps voltage.
reasonable_fix(F, L) :- fix(F), light(L), at_risk(L), helps(F, voltage).

valid_story(P, B, H, L) :- place(P), bird(B), helper(H), light(L),
                           affords(P, humming), at_risk(L), reasonable_fix(F, L).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for lid, l in LIGHTS.items():
        lines.append(asp.fact("light", lid))
        lines.append(asp.fact("needs", lid, l.needs))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for h in sorted(f.helps):
            lines.append(asp.fact("helps", fid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))

    py_set = set()
    for place, setting in SETTINGS.items():
        for light_id, light in LIGHTS.items():
            if "humming" in setting.affords and light.needs == "voltage":
                for helper in HELPERS:
                    py_set.add((place, helper, helper, light_id))
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} story shapes).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story params / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: voltage, a dim bird-light, kindness, and rhyme."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--bird-name", dest="bird_name")
    ap.add_argument("--bird-trait", dest="bird_trait", choices=TRAITS)
    ap.add_argument("--helper-kind", dest="helper_kind", choices=sorted(HELPERS))
    ap.add_argument("--helper-name", dest="helper_name")
    ap.add_argument("--light", choices=sorted(LIGHTS))
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
    place = args.place or rng.choice(sorted(SETTINGS))
    bird_name = args.bird_name or rng.choice(BIRD_NAMES)
    bird_trait = args.bird_trait or rng.choice(TRAITS)
    helper_kind = args.helper_kind or rng.choice(sorted(HELPERS))
    helper_name = args.helper_name or rng.choice(NAMES)
    light = args.light or rng.choice(sorted(LIGHTS))

    light_spec = LIGHTS[light]
    if light_spec.needs != "voltage":
        raise StoryError("Only voltage-powered lights are supported in this world.")
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    return StoryParams(
        place=place,
        bird_name=bird_name,
        bird_trait=bird_trait,
        helper_kind=helper_kind,
        helper_name=helper_name,
        light=light,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="nest", bird_name="Pip", bird_trait="gentle", helper_kind="child", helper_name="Mina", light="lantern"),
    StoryParams(place="garden", bird_name="Wren", bird_trait="curious", helper_kind="neighbor", helper_name="Theo", light="glowstone"),
    StoryParams(place="porch", bird_name="Blue", bird_trait="cheerful", helper_kind="grandparent", helper_name="Ruby", light="lantern"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story shapes:\n")
        for p, b, h, l in stories:
            print(f"  {p:8} {b:8} {h:10} {l:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.bird_name} at {p.place} with {p.light}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
