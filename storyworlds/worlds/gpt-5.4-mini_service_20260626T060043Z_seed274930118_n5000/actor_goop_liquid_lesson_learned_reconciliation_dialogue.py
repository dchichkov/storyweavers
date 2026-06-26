#!/usr/bin/env python3
"""
A small storyworld about an actor, a sticky goop, and a liquid lesson learned.

Premise:
An actor in a tiny theater gets splashed by goop while trying to clean a prop.
The actor and a helper talk, learn from the mess, and reconcile by choosing a
safer, cleaner plan.

The story is written in a rhyming, child-facing style, but the state still drives
the plot: mess spreads, tempers rise, then dialogue and a repair plan resolve it.
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
# World model
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("messy", "wet", "sticky", "clean", "workload"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "frustration", "calm", "reconciliation", "lesson_learned"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"actor", "child", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = "backstage"
    actor_name: str = "Milo"
    helper_name: str = "Lina"
    prop: str = "paint pot"
    seed: Optional[int] = None


SETTINGS = {
    "backstage": {
        "place": "backstage",
        "detail": "behind the curtain where the stage lights glow",
    },
    "greenroom": {
        "place": "the greenroom",
        "detail": "beside a mirror with warm, sleepy lights",
    },
    "prop_room": {
        "place": "the prop room",
        "detail": "near shelves of hats and a box of strings",
    },
}

PROPS = {
    "paint pot": {
        "label": "paint pot",
        "phrase": "a tiny paint pot",
        "wet": True,
        "goop_risk": True,
    },
    "glitter jar": {
        "label": "glitter jar",
        "phrase": "a bright glitter jar",
        "wet": False,
        "goop_risk": True,
    },
    "script page": {
        "label": "script page",
        "phrase": "a crinkly script page",
        "wet": True,
        "goop_risk": False,
    },
}

GOOPS = {
    "stage goop": {
        "label": "stage goop",
        "mess": "sticky",
        "soil": "sticky and dim",
    },
    "jam goop": {
        "label": "jam goop",
        "mess": "sticky",
        "soil": "sticky and sweet",
    },
    "soap goop": {
        "label": "soap goop",
        "mess": "wet",
        "soil": "wet and shiny",
    },
}

LIQUIDS = {
    "water": {
        "label": "water",
        "verse": "Water can rinse and make things clean.",
        "lesson": "When things get messy, water and patience can help.",
    },
    "lemonade": {
        "label": "lemonade",
        "verse": "Lemonade can splash, but not every splash is neat.",
        "lesson": "Sweet drinks should stay in cups, not on costumes.",
    },
    "oil": {
        "label": "oil",
        "verse": "Oil can slide and slip in a shiny gleam.",
        "lesson": "Some liquids make a mess that needs careful cleanup.",
    },
}

ACTOR_TYPES = ["actor"]
HELPER_TYPES = ["helper", "friend"]


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def _propagate(world: World) -> None:
    actor = world.get("actor")
    prop = world.get("prop")
    goop = world.get("goop")
    helper = world.get("helper")

    # Mess spreads when the actor handles the goop near the prop.
    if actor.meters["messy"] >= THRESHOLD and ("soak", prop.id) not in world.fired:
        world.fired.add(("soak", prop.id))
        prop.meters["messy"] += 1
        prop.meters["clean"] = 0
        world.say(f"The prop got a streak of goop, a sticky little drop.")

    # Wet goop increases worry and frustration if it touches the prop.
    if prop.meters["messy"] >= THRESHOLD and ("worry", actor.id) not in world.fired:
        world.fired.add(("worry", actor.id))
        actor.memes["worry"] += 1
        actor.memes["frustration"] += 1
        world.say(f"The actor frowned and sighed, with worry in the tide.")

    # Dialogue and reconciliation emerge when helper speaks with care.
    if actor.memes["worry"] >= THRESHOLD and helper.memes["calm"] >= THRESHOLD:
        if ("reconcile", actor.id) not in world.fired:
            world.fired.add(("reconcile", actor.id))
            actor.memes["reconciliation"] += 1
            helper.memes["reconciliation"] += 1
            actor.memes["calm"] += 1
            actor.memes["worry"] = 0
            world.say("They talked things through with gentle tone, and made a kinder plan their own.")

    # Lesson learned after the cleanup plan succeeds.
    if actor.memes["reconciliation"] >= THRESHOLD and ("lesson", actor.id) not in world.fired:
        world.fired.add(("lesson", actor.id))
        actor.memes["lesson_learned"] += 1
        prop.meters["clean"] += 1
        prop.meters["messy"] = 0
        world.say("The shine came back, the mess took flight, and both felt wiser by the light.")


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.prop not in PROPS:
        raise StoryError(f"Unknown prop: {params.prop}")

    world = World(setting=params.setting)
    actor = world.add(Entity(id="actor", kind="character", type="actor", label=params.actor_name))
    helper = world.add(Entity(id="helper", kind="character", type="helper", label=params.helper_name))
    prop = world.add(Entity(
        id="prop",
        kind="thing",
        type="prop",
        label=PROPS[params.prop]["label"],
        phrase=PROPS[params.prop]["phrase"],
        caretaker=helper.id,
    ))
    goop = world.add(Entity(
        id="goop",
        kind="thing",
        type="goop",
        label="goop",
        phrase="a wobbling gob of goop",
    ))
    liquid = world.add(Entity(
        id="liquid",
        kind="thing",
        type="liquid",
        label="liquid",
        phrase="a bright little puddle of liquid",
    ))

    world.facts.update(actor=actor, helper=helper, prop=prop, goop=goop, liquid=liquid)
    return world


def narrate_story(world: World) -> None:
    actor = world.get("actor")
    helper = world.get("helper")
    prop = world.get("prop")
    goop = world.get("goop")
    liquid = world.get("liquid")
    setting = SETTINGS[world.setting]

    world.say(
        f"Backstage in {setting['place']}, {actor.label} the actor kept a tidy show."
    )
    world.say(
        f"{actor.label} loved the little prop, {prop.phrase}, and polished it to glow."
    )
    world.say(
        f"But then came {goop.label}, a wobbling blob, with {liquid.label} inside that liked to hop."
    )
    actor.meters["messy"] += 1
    actor.memes["worry"] += 1
    world.say(
        f"{actor.label} reached out fast, but the goop went splash, and made a slick, silly mash."
    )
    _propagate(world)

    world.say(
        f"{helper.label} stepped in near the mirror bright and said, “Let’s slow down and make this right.”"
    )
    helper.memes["calm"] += 1
    helper.memes["calm"] += 1
    world.say(
        f'{actor.label} said, “I rushed that job; my hands were quick, and now the prop feels icky-stick.”'
    )
    world.say(
        f'{helper.label} replied, “A lesson learned is not a curse; next time we rinse and clean first.”'
    )
    _propagate(world)

    world.say(
        f"They found a cloth and cup of water, and cleaned the prop a little better."
    )
    if liquid.label == "water":
        prop.meters["clean"] += 1
        prop.meters["messy"] = 0
        world.say(
            f"The water swirled in a gentle gleam, and swept away the sticky seam."
        )
    else:
        world.say(
            f"The liquid still helped in part, because careful hands can steady heart."
        )
    helper.memes["reconciliation"] += 1
    actor.memes["reconciliation"] += 1
    actor.memes["lesson_learned"] += 1
    _propagate(world)

    world.say(
        f"In the end, they smiled and nodded near, and chose a slower, safer gear."
    )
    world.say(
        f"{actor.label} kept the goop away from the prop, and the whole small stage felt bright and top."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story about an {f["actor"].type} who meets {f["goop"].label} and learns a lesson about {f["liquid"].label}.',
        f'Tell a child-friendly backstage story where {f["actor"].label} and {f["helper"].label} use dialogue to reconcile after a messy mistake.',
        f'Write a tiny story with the words "actor", "goop", and "liquid" that ends with a lesson learned and a cleaner prop.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    actor, helper, prop, liquid = f["actor"], f["helper"], f["prop"], f["liquid"]
    return [
        QAItem(
            question=f"What did {actor.label} do that made the prop messy?",
            answer=(
                f"{actor.label} reached for the goop too fast, and the sticky splash "
                f"spotted the prop. That rush caused the mess."
            ),
        ),
        QAItem(
            question=f"How did {helper.label} help after the sticky accident?",
            answer=(
                f"{helper.label} stayed calm, talked kindly, and helped choose a safer "
                f"cleanup plan. The dialogue led to reconciliation."
            ),
        ),
        QAItem(
            question=f"What lesson did {actor.label} learn by the end?",
            answer=(
                f"{actor.label} learned to slow down, use water carefully, and keep the "
                f"goop away from the prop so the stage could stay clean."
            ),
        ),
        QAItem(
            question=f"Which liquid helped clean the mess in the story?",
            answer=(
                f"{liquid.label.capitalize()} helped the most because it could rinse away "
                f"the sticky goop and leave the prop shiny again."
            ),
        ),
    ]


KNOWLEDGE = {
    "actor": [
        QAItem(
            question="What is an actor?",
            answer="An actor is a person who pretends to be a character in a play or story on a stage.",
        )
    ],
    "goop": [
        QAItem(
            question="What is goop?",
            answer="Goop is a sticky, gooey stuff that can smear, drip, or make a mess.",
        )
    ],
    "liquid": [
        QAItem(
            question="What is a liquid?",
            answer="A liquid is a kind of matter that can pour, splash, and flow into a container.",
        )
    ],
    "water": [
        QAItem(
            question="Why is water useful for cleaning?",
            answer="Water is useful for cleaning because it can loosen dirt and wash sticky things away.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE["actor"] + KNOWLEDGE["goop"] + KNOWLEDGE["liquid"] + KNOWLEDGE["water"])


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
actor(a). helper(h). prop(p). goop(g). liquid(l).

messy_after_goop(a) :- touches(a,g), sticky(g).
needs_dialogue(a) :- messy_after_goop(a).
reconcile(a) :- needs_dialogue(a), calm(h).
lesson_learned(a) :- reconcile(a), cleaned(p).

#show messy_after_goop/1.
#show needs_dialogue/1.
#show reconcile/1.
#show lesson_learned/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("touches", "a", "g"),
        asp.fact("sticky", "g"),
        asp.fact("calm", "h"),
        asp.fact("cleaned", "p"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reconcile/1.\n#show lesson_learned/1.\n"))
    atoms = set((s.name, tuple(a.name if a.type != a.type.Number else a.number for a in s.arguments)) for s in model)
    expected = {("reconcile", ("a",)), ("lesson_learned", ("a",))}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP atoms:", sorted(atoms))
    print("Expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Parser, resolution, generation, emit
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: actor, goop, liquid, lesson learned.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--prop", choices=sorted(PROPS))
    ap.add_argument("--actor-name")
    ap.add_argument("--helper-name")
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
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        actor_name=args.actor_name or rng.choice(["Milo", "Nia", "Tess", "Otto", "June"]),
        helper_name=args.helper_name or rng.choice(["Lina", "Pip", "Rae", "Mina", "Sol"]),
        prop=args.prop or rng.choice(sorted(PROPS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts.append(f"{e.id}: meters={meters} memes={memes}")
    parts.append(f"fired={sorted(world.fired)}")
    return "\n".join(parts)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reconcile/1.\n#show lesson_learned/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="backstage", actor_name="Milo", helper_name="Lina", prop="paint pot"),
            StoryParams(setting="greenroom", actor_name="Nia", helper_name="Pip", prop="glitter jar"),
            StoryParams(setting="prop_room", actor_name="Tess", helper_name="Rae", prop="script page"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            p = sample.params
            print(f"### variant {i + 1}: {p.actor_name} in {p.setting} with {p.prop}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
