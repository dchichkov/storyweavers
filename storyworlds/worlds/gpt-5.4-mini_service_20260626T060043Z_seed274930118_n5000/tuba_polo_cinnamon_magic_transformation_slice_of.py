#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tuba_polo_cinnamon_magic_transformation_slice_of.py
===============================================================================================================

A small slice-of-life story world about a child, a tuba, a polo shirt, and a
little cinnamon magic that can transform ordinary moments into kinder ones.

Seed-image premise:
- A child is getting ready for a normal day.
- A polo shirt and a tuba are both important to the day.
- Cinnamon is present as an everyday kitchen scent that becomes the hinge for a
  gentle magical transformation.
- The tension is small: a spill, a stain, a worry, or a mismatch between plan
  and outfit.
- The resolution is not flashy; it is a practical, warm transformation that
  makes the day work.

The world supports:
- typed entities with physical meters and emotional memes;
- a tiny causal simulator;
- a Python reasonableness gate;
- an inline ASP twin for parity checking;
- story / QA / trace / JSON / verify outputs.

This is intentionally child-facing and slice-of-life in tone, with magic used as
an ordinary helper rather than a huge fantasy engine.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

# Physical meters we care about narratively.
METER_KEYS = {"clean", "stained", "warm", "ready", "polished", "sweet"}

# Emotional memes.
MEME_KEYS = {"joy", "worry", "love", "pride", "calm", "surprise", "certainty"}

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    magical: bool = False
    transformed_from: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        masculine = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    adult_type: str
    activity: str
    shirt: str
    seed: Optional[int] = None


@dataclass
class Place:
    name: str
    indoors: bool
    affordances: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    spill: str
    tone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Garment:
    id: str
    label: str
    phrase: str
    type: str
    color: str
    wearable: bool = True


@dataclass
class MagicRule:
    id: str
    label: str
    effect: str
    requires: set[str] = field(default_factory=set)
    transforms_to: str = ""


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place(name="the kitchen", indoors=True, affordances={"breakfast", "magic"}),
    "music_room": Place(name="the music room", indoors=True, affordances={"practice", "magic"}),
    "porch": Place(name="the porch", indoors=False, affordances={"practice", "breakfast", "magic"}),
}

ACTIVITIES = {
    "practice": Activity(
        id="practice",
        verb="practice the tuba",
        gerund="practicing the tuba",
        risk="a shirt that feels too plain for the day",
        spill="cinnamon dust",
        tone="quiet",
        tags={"tuba", "music"},
    ),
    "breakfast": Activity(
        id="breakfast",
        verb="eat cinnamon toast",
        gerund="eating cinnamon toast",
        risk="a shirt that can get spotted",
        spill="cinnamon crumbs",
        tone="cozy",
        tags={"cinnamon", "food"},
    ),
}

SHIRTS = {
    "white_polo": Garment(
        id="white_polo",
        label="polo",
        phrase="a neat white polo shirt",
        type="polo",
        color="white",
    ),
    "blue_polo": Garment(
        id="blue_polo",
        label="polo",
        phrase="a soft blue polo shirt",
        type="polo",
        color="blue",
    ),
    "striped_polo": Garment(
        id="striped_polo",
        label="polo",
        phrase="a striped polo shirt",
        type="polo",
        color="striped",
    ),
}

MAGIC = MagicRule(
    id="cinnamon_spark",
    label="cinnamon magic",
    effect="turn something plain into something ready for the day",
    requires={"cinnamon", "polo"},
    transforms_to="festival_polo",
)

FESTIVAL_POLO = Garment(
    id="festival_polo",
    label="festival polo",
    phrase="a warm festival polo with tiny gold buttons",
    type="polo",
    color="gold",
)

CHILD_NAMES = ["Milo", "Nora", "June", "Ellis", "Theo", "Maya", "Owen", "Ruby"]
ADULT_TYPES = ["mother", "father", "grandmother", "grandfather"]
CHILD_TYPES = ["boy", "girl"]
TRAITS = ["careful", "cheerful", "curious", "gentle", "spirited"]

CURATED = [
    StoryParams(place="kitchen", child_name="Milo", child_type="boy", adult_type="mother", activity="breakfast", shirt="white_polo"),
    StoryParams(place="music_room", child_name="Nora", child_type="girl", adult_type="father", activity="practice", shirt="blue_polo"),
    StoryParams(place="porch", child_name="Theo", child_type="boy", adult_type="grandmother", activity="practice", shirt="striped_polo"),
]


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def activity_needs_magic(activity: Activity, shirt: Garment) -> bool:
    return shirt.type == "polo" and activity.id in {"practice", "breakfast"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for act_id, act in ACTIVITIES.items():
            if act_id not in place.affordances:
                continue
            for shirt_id in SHIRTS:
                if activity_needs_magic(act, SHIRTS[shirt_id]):
                    combos.append((place_id, act_id, shirt_id))
    return combos


def explain_rejection(place: Place, activity: Activity, shirt: Garment) -> str:
    return (
        f"(No story: {place.name} can host {activity.gerund}, but this shirt choice "
        f"doesn't create a meaningful cinnamon-magic transformation. "
        f"Pick one of the polos that can become festive.)"
    )


def predict_transform(world: World, child: Entity, activity: Activity, shirt_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(child.id), activity, narrate=False)
    shirt = sim.entities[shirt_id]
    return {
        "stained": shirt.meters.get("stained", 0.0) >= THRESHOLD,
        "transformed": shirt.id == "festival_polo",
    }


# ---------------------------------------------------------------------------
# Causal simulation
# ---------------------------------------------------------------------------

def _do_activity(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    if activity.id == "practice":
        child.meters["ready"] = child.meters.get("ready", 0.0) + 1
    else:
        child.meters["warm"] = child.meters.get("warm", 0.0) + 1

    for ent in world.entities.values():
        if ent.type == "polo" and ent.worn_by == child.id:
            ent.meters["stained"] = ent.meters.get("stained", 0.0) + 1
            ent.memes["worry"] = ent.memes.get("worry", 0.0) + 1

    if narrate:
        pass


def apply_magic(world: World, child: Entity, adult: Entity, shirt: Entity, activity: Activity) -> bool:
    if shirt.type != "polo":
        return False
    if shirt.meters.get("stained", 0.0) < THRESHOLD and activity.id != "practice":
        return False
    if "cinnamon" not in world.facts:
        return False

    sig = ("magic", shirt.id, activity.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)

    transformed = world.add(Entity(
        id=FESTIVAL_POLO.id,
        kind="thing",
        type=FESTIVAL_POLO.type,
        label=FESTIVAL_POLO.label,
        phrase=FESTIVAL_POLO.phrase,
        owner=child.id,
        caretaker=adult.id,
        worn_by=child.id,
        transformed_from=shirt.id,
    ))
    transformed.meters["clean"] = 1
    transformed.meters["ready"] = 1
    transformed.meters["polished"] = 1
    transformed.memes["calm"] = 1
    shirt.worn_by = None
    child.memes["certainty"] = child.memes.get("certainty", 0.0) + 1
    adult.memes["pride"] = adult.memes.get("pride", 0.0) + 1
    return True


# ---------------------------------------------------------------------------
# Narrative functions
# ---------------------------------------------------------------------------

def intro(world: World, child: Entity, adult: Entity, shirt: Entity, activity: Activity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who liked ordinary days that still felt special."
    )
    world.say(
        f"{child.id}'s {shirt.label} was {shirt.phrase}, and {child.id} liked how neat it looked."
    )
    world.say(
        f"On this {activity.tone} morning, {child.id} wanted to {activity.verb}, and "
        f"{adult.pronoun('possessive')} {adult.type} was making the day feel calm."
    )


def tension(world: World, child: Entity, adult: Entity, shirt: Entity, activity: Activity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(
        f"Then a little cinnamon spill landed on the {shirt.label} and left a small stain."
    )
    world.say(
        f"{adult.id} frowned softly, because a spotted {shirt.label} looked wrong for the plan."
    )
    world.say(
        f"{child.id} still wanted to {activity.verb}, but now {child.pronoun('possessive')} "
        f"polo felt too plain and too messy at the same time."
    )


def turn(world: World, child: Entity, adult: Entity, shirt: Entity, activity: Activity) -> None:
    world.say(
        f"{adult.id} opened a tiny tin of cinnamon and tapped it once over the shirt."
    )
    world.say(
        f"The cinnamon twinkled like warm sugar, and the plain cloth began to change."
    )
    if apply_magic(world, child, adult, shirt, activity):
        world.say(
            f"In a blink, the old polo became a warm festival polo, bright enough for the day."
        )


def resolution(world: World, child: Entity, adult: Entity, shirt: Entity, activity: Activity) -> None:
    if FESTIVAL_POLO.id in world.entities:
        polo = world.get(FESTIVAL_POLO.id)
        world.say(
            f"{child.id} wore the new polo and went back to {activity.verb} with a lighter step."
        )
        world.say(
            f"{adult.id} smiled, and the kitchen music of the morning felt easy again."
        )
        world.say(
            f"By the end, the cinnamon smell still floated in the air, and {child.id}'s shirt was ready for the whole day."
        )
    else:
        world.say(
            f"{child.id} took a careful breath and kept the day gentle, even if the shirt stayed plain."
        )


# ---------------------------------------------------------------------------
# World builder
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    activity = ACTIVITIES[params.activity]
    shirt_cfg = SHIRTS[params.shirt]
    world = World(place)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
    ))
    adult = world.add(Entity(
        id=params.adult_type.capitalize(),
        kind="character",
        type=params.adult_type,
    ))
    shirt = world.add(Entity(
        id=shirt_cfg.id,
        kind="thing",
        type=shirt_cfg.type,
        label=shirt_cfg.label,
        phrase=shirt_cfg.phrase,
        owner=child.id,
        caretaker=adult.id,
        worn_by=child.id,
    ))
    cinnamon = world.add(Entity(
        id="cinnamon",
        kind="thing",
        type="cinnamon",
        label="cinnamon",
        phrase="a tiny tin of cinnamon",
        magical=True,
        owner=adult.id,
        held_by=adult.id,
    ))
    tuba = world.add(Entity(
        id="tuba",
        kind="thing",
        type="tuba",
        label="tuba",
        phrase="a shiny tuba",
        owner=child.id,
        caretaker=adult.id,
        held_by=child.id,
    ))

    world.facts.update(
        child=child,
        adult=adult,
        shirt=shirt,
        cinnamon=cinnamon,
        tuba=tuba,
        activity=activity,
        place=place,
    )

    intro(world, child, adult, shirt, activity)
    world.para()
    tension(world, child, adult, shirt, activity)
    world.para()
    turn(world, child, adult, shirt, activity)
    world.para()
    resolution(world, child, adult, shirt, activity)

    world.facts["used_magic"] = FESTIVAL_POLO.id in world.entities
    world.facts["transformed_item"] = FESTIVAL_POLO.id if FESTIVAL_POLO.id in world.entities else shirt.id
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    shirt = f["shirt"]
    return [
        f'Write a short slice-of-life story for a young child named {child.id} that includes a tuba, a polo shirt, and cinnamon magic.',
        f"Tell a gentle story where {child.id} wants to {activity.verb} and a cinnamon spell transforms the {shirt.label} into something nicer.",
        f"Write a cozy story about an everyday morning, a small spill, and a magical transformation that helps the day go on.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    shirt = f["shirt"]
    activity = f["activity"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to do in the story?",
            answer=f"{child.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"What happened to the {shirt.label} after the cinnamon spill?",
            answer=f"The {shirt.label} got a small stain, and then cinnamon magic transformed it into a festival polo.",
        ),
        QAItem(
            question=f"Who helped make the day feel better for {child.id}?",
            answer=f"{adult.id} helped by using cinnamon magic and staying calm.",
        ),
        QAItem(
            question=f"What proved at the end that the transformation worked?",
            answer=f"{child.id} wore the new festival polo and went back to the day feeling ready.",
        ),
    ]
    if world.facts.get("used_magic"):
        qa.append(
            QAItem(
                question=f"Why was the new shirt a better fit for the day?",
                answer=f"It was better because the transformed polo looked neat again and matched the warm, ordinary kind of magic in the story.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "tuba": [
        (
            "What is a tuba?",
            "A tuba is a very big brass instrument that makes low, deep sounds in a band or parade.",
        )
    ],
    "polo": [
        (
            "What is a polo shirt?",
            "A polo shirt is a shirt with a collar and a few buttons near the neck. It is comfy but still looks neat.",
        )
    ],
    "cinnamon": [
        (
            "What is cinnamon?",
            "Cinnamon is a sweet-smelling spice made from tree bark. People often sprinkle it on toast, oatmeal, or baked treats.",
        )
    ],
    "magic": [
        (
            "What is magic in stories?",
            "Magic in stories is when something unusual happens, like a spell or a charm changing the way the world looks or works.",
        )
    ],
    "transformation": [
        (
            "What does transformation mean?",
            "A transformation means something changes into a new form, like a plain thing becoming something special.",
        )
    ],
}

WORLD_KNOWLEDGE_ORDER = ["tuba", "polo", "cinnamon", "magic", "transformation"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in WORLD_KNOWLEDGE_ORDER:
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[key])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.transformed_from:
            bits.append(f"transformed_from={e.transformed_from}")
        lines.append(f"  {e.id:14} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A shirt is at risk when cinnamon spill or breakfast touches it.
at_risk(A, S) :- activity(A), shirt(S), spills(A, cinnamon), worn_by(S, _).

% A magic transformation is valid when the shirt is a polo and cinnamon is present.
can_transform(S) :- shirt(S), polo(S), cinnamon_present, worn_by(S, _).

valid_story(P, A, S) :- place(P), affords(P, A), shirt(S), polo(S), can_transform(S), at_risk(A, S).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affordances):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("spills", aid, "cinnamon"))
    for sid, shirt in SHIRTS.items():
        lines.append(asp.fact("shirt", sid))
        lines.append(asp.fact("polo", sid))
    lines.append(asp.fact("cinnamon_present"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo_set:
        print("  only in python:", sorted(py - clingo_set))
    if clingo_set - py:
        print("  only in clingo:", sorted(clingo_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life magic storyworld about a tuba, a polo shirt, and cinnamon.",
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--shirt", choices=SHIRTS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--adult-type", choices=ADULT_TYPES)
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
    if args.place and args.activity and args.shirt:
        place = PLACES[args.place]
        activity = ACTIVITIES[args.activity]
        shirt = SHIRTS[args.shirt]
        if activity.id not in place.affordances or not activity_needs_magic(activity, shirt):
            raise StoryError(explain_rejection(place, activity, shirt))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.shirt is None or c[2] == args.shirt)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, shirt = rng.choice(sorted(combos))
    child_name = args.name or rng.choice(CHILD_NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    adult_type = args.adult_type or rng.choice(ADULT_TYPES)
    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        adult_type=adult_type,
        activity=activity,
        shirt=shirt,
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, shirt) combos:\n")
        for place, act, shirt in triples:
            print(f"  {place:12} {act:10} {shirt}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.child_name}: {p.activity} at {p.place} (shirt: {p.shirt})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
