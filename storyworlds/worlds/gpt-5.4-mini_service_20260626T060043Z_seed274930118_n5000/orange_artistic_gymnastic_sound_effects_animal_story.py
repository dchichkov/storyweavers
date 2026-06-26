#!/usr/bin/env python3
"""
Story world: an Animal Story with orange, artistic, and gymnastic motifs,
driven by sound effects.

This world models a small classical tale about an animal character who wants
to do something creative and gymnastic, gets blocked by a practical concern,
and finds a playful compromise. The story is built from a live world model so
the prose reflects state changes rather than a frozen template.
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
# Core registries
# ---------------------------------------------------------------------------

SFX = {
    "paint": "swish",
    "drum": "boom",
    "jump": "boing",
    "slide": "whoosh",
    "tap": "tap-tap",
    "snap": "snap",
    "clap": "clap-clap",
    "crinkle": "crinkle",
}

PLACES = {
    "barn": {
        "label": "the barn",
        "is_indoor": True,
        "supports": {"artistic", "gymnastic"},
    },
    "garden": {
        "label": "the garden",
        "is_indoor": False,
        "supports": {"artistic", "gymnastic"},
    },
    "playground": {
        "label": "the playground",
        "is_indoor": False,
        "supports": {"gymnastic"},
    },
    "studio": {
        "label": "the art studio",
        "is_indoor": True,
        "supports": {"artistic"},
    },
}

ACTIVITIES = {
    "painting": {
        "label": "paint a bright orange picture",
        "gerund": "painting bright orange pictures",
        "attempt": "dash to the paints",
        "kind": "artistic",
        "sfx": "swish",
        "result": "orange paint splashes",
        "tag": "paint",
        "theme": "orange",
        "emotion": "delighted",
    },
    "tumbling": {
        "label": "do a gymnastic tumble",
        "gerund": "doing gymnastic tumbles",
        "attempt": "spring into a tumble",
        "kind": "gymnastic",
        "sfx": "boing",
        "result": "little paws patter and thump",
        "tag": "jump",
        "theme": "gymnastic",
        "emotion": "bouncy",
    },
    "drumming": {
        "label": "make a loud rhythm",
        "gerund": "drumming out a rhythm",
        "attempt": "grab the drumsticks",
        "kind": "artistic",
        "sfx": "boom",
        "result": "the beat bounces across the room",
        "tag": "drum",
        "theme": "artistic",
        "emotion": "excited",
    },
}

COSTUMES = {
    "scarf": {
        "label": "an orange scarf",
        "risk": {"painting", "tumbling", "drumming"},
        "reason": "it could get messy",
        "covers": {"neck"},
    },
    "leotard": {
        "label": "a bright leotard",
        "risk": {"painting"},
        "reason": "paint could stain it",
        "covers": {"torso"},
    },
    "overalls": {
        "label": "orange overalls",
        "risk": {"painting", "drumming"},
        "reason": "they are easy to splash",
        "covers": {"torso", "legs"},
    },
    "ribbon": {
        "label": "an orange ribbon",
        "risk": {"tumbling", "drumming"},
        "reason": "it could slip off during rough play",
        "covers": {"head"},
    },
}

ANIMAL_KINDS = {
    "fox": {"label": "fox", "name": "Foxy", "traits": ["quick", "curious"]},
    "rabbit": {"label": "rabbit", "name": "Ruby", "traits": ["spry", "gentle"]},
    "bear": {"label": "bear", "name": "Benny", "traits": ["warm", "patient"]},
    "cat": {"label": "cat", "name": "Cleo", "traits": ["clever", "pouncy"]},
}

HELPERS = {
    "owl": {"label": "owl", "name": "Oona"},
    "duck": {"label": "duck", "name": "Daisy"},
    "dog": {"label": "dog", "name": "Duke"},
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if case == "subject":
            return "they"
        if case == "object":
            return "them"
        return "their"

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    label: str
    is_indoor: bool
    supports: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    label: str
    gerund: str
    attempt: str
    kind: str
    sfx: str
    result: str
    tag: str
    theme: str
    emotion: str


@dataclass
class Costume:
    id: str
    label: str
    risk: set[str]
    reason: str
    covers: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    sfx_log: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.sfx_log = list(self.sfx_log)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def activity_sound(activity: Activity) -> str:
    return activity.sfx


def place_intro(setting: Setting) -> str:
    if setting.is_indoor:
        return f"{setting.label.capitalize()} was quiet and cozy."
    return f"{setting.label.capitalize()} glowed in the open air."


def animal_intro(animal: Entity) -> str:
    return f"{animal.id} was a little {animal.type} who loved bright colors and lively games."


def loves_activity(animal: Entity, activity: Activity) -> str:
    animal.memes["joy"] = animal.memes.get("joy", 0.0) + 1
    return (
        f"{animal.id} loved {activity.gerund}, and every {activity.sfx} made "
        f"{animal.pronoun('possessive')} tail or ears perk up."
    )


def buy_costume(helper: Entity, child: Entity, costume: Entity) -> str:
    return f"One day, {helper.id} brought {child.id} {costume.phrase}."


def wear_costume(child: Entity, costume: Entity) -> str:
    costume.worn_by = child.id
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    return f"{child.id} loved {costume.label} and wore {costume.it()} everywhere."


def predict_mess(world: World, child: Entity, activity: Activity, costume: Entity) -> bool:
    sim = world.copy()
    sim.get(child.id).meters[activity.kind] = sim.get(child.id).meters.get(activity.kind, 0.0) + 1
    return costume.id in bad_outcome(sim, child, activity)


def bad_outcome(world: World, child: Entity, activity: Activity) -> set[str]:
    ruined = set()
    actor = world.get(child.id)
    if actor.meters.get(activity.kind, 0.0) < THRESHOLD:
        return ruined
    for item in world.worn_items(actor):
        if item.protective:
            continue
        ruined.add(item.id)
    return ruined


def warn(helper: Entity, child: Entity, activity: Activity, costume: Entity, world: World) -> str:
    if not predict_mess(world, child, activity, costume):
        return ""
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    return (
        f'"If you {activity.label}, your {costume.label} could get ruined," '
        f"{helper.id} said."
    )


def defy(child: Entity, activity: Activity) -> str:
    child.memes["stubborn"] = child.memes.get("stubborn", 0.0) + 1
    return f"{child.id} wriggled and tried to {activity.attempt} anyway."


def compromise(helper: Entity, child: Entity, activity: Activity, costume: Entity) -> tuple[str, Optional[Entity]]:
    if activity.kind == "artistic" and costume.id == "overalls":
        gear = Entity(
            id="smock",
            kind="thing",
            type="gear",
            label="an old orange smock",
            phrase="an old orange smock",
            owner=child.id,
            worn_by=child.id,
            protective=True,
            covers={"torso", "legs"},
        )
        return (
            f"{helper.id} smiled. \"How about the smock first?\"",
            gear,
        )
    if activity.kind == "gymnastic" and costume.id == "ribbon":
        gear = Entity(
            id="headband",
            kind="thing",
            type="gear",
            label="a snug orange headband",
            phrase="a snug orange headband",
            owner=child.id,
            worn_by=child.id,
            protective=True,
            covers={"head"},
        )
        return (
            f"{helper.id} clapped. \"Let's tuck the ribbon away and use the headband first.\"",
            gear,
        )
    gear = Entity(
        id="apron",
        kind="thing",
        type="gear",
        label="an orange apron",
        phrase="an orange apron",
        owner=child.id,
        worn_by=child.id,
        protective=True,
        covers={"torso"},
    )
    return (
        f"{helper.id} said, \"Let's put on the apron first and play carefully.\"",
        gear,
    )


def accept(child: Entity, helper: Entity, activity: Activity, costume: Entity, gear: Entity) -> str:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["worry"] = 0.0
    gear.worn_by = child.id
    return (
        f"{child.id} nodded and gave {helper.id} a hug. Soon {child.id} was "
        f"{activity.gerund}, with {gear.label} on, and {costume.label} stayed clean."
    )


def perform_activity(world: World, child: Entity, activity: Activity) -> list[str]:
    lines = []
    child.meters[activity.kind] = child.meters.get(activity.kind, 0.0) + 1
    sound = activity_sound(activity)
    world.sfx_log.append(sound)
    lines.append(f"{sound}! {child.id} began {activity.gerund}.")
    lines.append(activity.result.capitalize() + ".")
    return lines


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    animal: str
    activity: str
    costume: str
    helper: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    setting = Setting(**PLACES[params.place])
    world = World(setting)

    animal_kind = ANIMAL_KINDS[params.animal]
    helper_kind = HELPERS[params.helper]
    activity = Activity(id=params.activity, **ACTIVITIES[params.activity])
    costume_cfg = COSTUMES[params.costume]

    child = world.add(Entity(
        id=animal_kind["name"],
        kind="character",
        type=animal_kind["label"],
        meters={},
        memes={},
    ))
    helper = world.add(Entity(
        id=helper_kind["name"],
        kind="character",
        type=helper_kind["label"],
    ))
    costume = world.add(Entity(
        id=costume_cfg["label"],
        kind="thing",
        type="costume",
        label=costume_cfg["label"],
        phrase=costume_cfg["label"],
        owner=child.id,
        worn_by=child.id,
        covers=set(costume_cfg["covers"]),
    ))

    world.say(animal_intro(child))
    world.say(loves_activity(child, activity))
    world.say(buy_costume(helper, child, costume))
    world.say(wear_costume(child, costume))

    world.para()
    world.say(place_intro(setting))
    world.say(
        f"{child.id} wanted to {activity.label} at {setting.label}, and the air was full of hope."
    )
    warning = warn(helper, child, activity, costume, world)
    if warning:
        world.say(warning)
    world.say(defy(child, activity))

    world.para()
    world.say(f"Then came the fun part: {activity.sfx}!")
    if warning:
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    lines = perform_activity(world, child, activity)
    for line in lines:
        world.say(line)

    helper_line, gear = compromise(helper, child, activity, costume)
    world.say(helper_line)
    if gear is not None:
        world.add(gear)
        gear.worn_by = child.id
        world.say(accept(child, helper, activity, costume, gear))

    world.facts.update(
        child=child,
        helper=helper,
        costume=costume,
        activity=activity,
        gear=gear,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    activity: Activity = f["activity"]
    costume: Entity = f["costume"]
    return [
        f'Write a short animal story with "{activity.theme}" and a gentle sound effect.',
        f"Tell a story about {child.id} the {child.type} who wants to {activity.label} but worries about {costume.label}.",
        f'Write a child-friendly story featuring the word "{activity.theme}" and the sound "{activity.sfx}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    costume: Entity = f["costume"]
    activity: Activity = f["activity"]
    gear: Optional[Entity] = f["gear"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who wanted to {activity.label} at {setting.label}?",
            answer=f"{child.id} the {child.type} wanted to {activity.label} at {setting.label}.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {child.id} about {costume.label}?",
            answer=f"{helper.id} warned {child.id} because {costume.label} could get ruined when {child.id} tried to {activity.label}.",
        ),
        QAItem(
            question=f"What sound effect showed the start of the activity?",
            answer=f"The story started with {activity.sfx}!",
        ),
    ]
    if gear is not None:
        qa.append(
            QAItem(
                question=f"How did the compromise help {child.id} keep playing?",
                answer=f"They used {gear.label} first, so {child.id} could keep {activity.gerund} while {costume.label} stayed safe.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    activity: Activity = f["activity"]
    qa = [
        QAItem(
            question="What is orange?",
            answer="Orange is a bright color between red and yellow. It can make things look sunny and warm.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word that helps you hear the action, like boom, swish, or whoosh.",
        ),
        QAItem(
            question="What does artistic mean?",
            answer="Artistic means making pictures, music, or other creative things.",
        ),
        QAItem(
            question="What does gymnastic mean?",
            answer="Gymnastic means using your body in lively bends, jumps, rolls, and balances.",
        ),
    ]
    if activity.kind == "artistic":
        qa.append(
            QAItem(
                question="Why can paint be messy?",
                answer="Paint can drip and splash, so it can easily get on clothes and hands.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="Why do animals need a safe place for tumbling?",
                answer="They need a safe place so they do not bump into hard things while jumping and rolling.",
            )
        )
    return qa


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    if world.sfx_log:
        lines.append(f"sfx={world.sfx_log}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- activity_fact(A).
costume(C) :- costume_fact(C).

good_combo(P, A, C) :- supports(P, artistic), activity_kind(A, artistic), risk(C, painting).
good_combo(P, A, C) :- supports(P, gymnastic), activity_kind(A, gymnastic), risk(C, tumbling).
good_combo(P, A, C) :- supports(P, artistic), supports(P, gymnastic), activity_kind(A, artistic), risk(C, drumming).
good_combo(P, A, C) :- supports(P, artistic), supports(P, gymnastic), activity_kind(A, gymnastic), risk(C, drumming).

#show good_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, cfg in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for s in cfg["supports"]:
            lines.append(asp.fact("supports", pid, s))
    for aid, cfg in ACTIVITIES.items():
        lines.append(asp.fact("activity_fact", aid))
        lines.append(asp.fact("activity_kind", aid, cfg["kind"]))
    for cid, cfg in COSTUMES.items():
        lines.append(asp.fact("costume_fact", cid))
        for r in cfg["risk"]:
            lines.append(asp.fact("risk", cid, r))
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "good_combo")))


def python_valid_combos() -> list[tuple]:
    combos = []
    for p, pcfg in PLACES.items():
        for a, acfg in ACTIVITIES.items():
            for c, ccfg in COSTUMES.items():
                if acfg["kind"] in pcfg["supports"] and a in ccfg["risk"]:
                    combos.append((p, a, c))
    return sorted(combos)


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(python_valid_combos())
    if a == p:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("Mismatch:")
    if a - p:
        print(" only in ASP:", sorted(a - p))
    if p - a:
        print(" only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="studio", animal="fox", activity="painting", costume="overalls", helper="owl"),
    StoryParams(place="playground", animal="rabbit", activity="tumbling", costume="ribbon", helper="duck"),
    StoryParams(place="garden", animal="bear", activity="drumming", costume="scarf", helper="dog"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with orange, artistic, and gymnastic sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMAL_KINDS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = python_valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.costume is None or c[2] == args.costume)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, costume = rng.choice(combos)
    animal = args.animal or rng.choice(sorted(ANIMAL_KINDS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(place=place, animal=animal, activity=activity, costume=costume, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
