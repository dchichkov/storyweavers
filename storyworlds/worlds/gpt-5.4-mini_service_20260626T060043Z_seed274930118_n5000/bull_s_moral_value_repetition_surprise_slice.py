#!/usr/bin/env python3
"""
A standalone story world for a small slice-of-life tale about a bull's day,
with moral value, repetition, and a gentle surprise.

Premise:
- A bull lives a calm everyday life in a barnyard.
- He likes doing a small useful task again and again.
- A surprise interrupts the routine.
- The bull chooses a kind, practical response and the day ends warmly.

The world is intentionally small and constraint-driven: the story is only
generated when the surprise is plausible for the routine and the moral turn
feels earned.
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
    kind: str = "thing"  # "character" | "thing"
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
        if self.type in {"bull", "boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"cow", "girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the meadow"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    action_noun: str
    repeat_line: str
    meter: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    kind: str
    trigger: str
    reaction: str
    resolves: bool = True


@dataclass
class Value:
    id: str
    label: str
    action: str
    consequence: str
    moral_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    surprise: str
    value: str
    name: str
    companion: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"gather", "carry", "greet"}),
    "barnyard": Setting(place="the barnyard", affords={"gather", "carry", "greet"}),
    "orchard": Setting(place="the orchard", affords={"gather", "carry", "greet"}),
}

ACTIVITIES = {
    "gather_hay": Activity(
        id="gather_hay",
        verb="gather hay",
        gerund="gathering hay",
        rush="trudge back to the hay pile",
        action_noun="hay",
        repeat_line="He did it again and again, one neat bundle at a time.",
        meter="work",
        weather="",
        keyword="hay",
        tags={"hay", "work", "routine"},
    ),
    "carry_buckets": Activity(
        id="carry_buckets",
        verb="carry water buckets",
        gerund="carrying water buckets",
        rush="hurry to the water trough",
        action_noun="buckets",
        repeat_line="He carried one bucket, then another, then another.",
        meter="help",
        weather="",
        keyword="water",
        tags={"water", "work", "routine"},
    ),
    "greet_neighbors": Activity(
        id="greet_neighbors",
        verb="greet the neighbors",
        gerund="greeting the neighbors",
        rush="step toward the gate",
        action_noun="neighbors",
        repeat_line="He said hello the same friendly way each time someone passed.",
        meter="kindness",
        weather="",
        keyword="hello",
        tags={"people", "kindness", "routine"},
    ),
}

SURPRISES = {
    "baby_goat": Surprise(
        id="baby_goat",
        label="a tiny baby goat",
        phrase="a tiny baby goat with a wobbly tail",
        kind="animal",
        trigger="a soft bleat from behind the fence",
        reaction="he stopped and listened carefully",
        resolves=True,
    ),
    "lost_basket": Surprise(
        id="lost_basket",
        label="a lost picnic basket",
        phrase="a picnic basket with a ribbon handle",
        kind="object",
        trigger="something thumped gently in the grass",
        reaction="he looked around for whoever might need it",
        resolves=True,
    ),
    "sudden_rain": Surprise(
        id="sudden_rain",
        label="a sudden raincloud",
        phrase="a raincloud that drifted over the orchard",
        kind="weather",
        trigger="the sky turned gray in a hurry",
        reaction="he blinked at the sky and shook his ears",
        resolves=True,
    ),
}

VALUES = {
    "kindness": Value(
        id="kindness",
        label="kindness",
        action="help first",
        consequence="everyone feels safer and warmer",
        moral_line="Being kind can turn an ordinary day into a better one.",
    ),
    "patience": Value(
        id="patience",
        label="patience",
        action="slow down and check carefully",
        consequence="mistakes stay small",
        moral_line="Patience helps with jobs that need steady hands.",
    ),
    "responsibility": Value(
        id="responsibility",
        label="responsibility",
        action="finish the small job before wandering off",
        consequence="the little things get done",
        moral_line="Doing what needs doing makes a home feel calm.",
    ),
}

BULL_NAMES = ["Bram", "Buster", "Milo", "Rufus", "Owen", "Toby", "Finn", "Gus"]
COMPANIONS = ["mouse", "calf", "farmer", "duck", "hen", "goat"]
TRAITS = ["steady", "gentle", "curious", "patient", "cheerful", "careful"]


class Rule:
    def __init__(self, name: str, apply) -> None:
        self.name = name
        self.apply = apply


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    bull = world.facts.get("bull")
    act = world.facts.get("activity")
    if not bull or not act:
        return out
    if bull.meters.get(act.meter, 0.0) < THRESHOLD:
        return out
    sig = ("repeat", bull.id, act.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bull.memes["routine"] = bull.memes.get("routine", 0.0) + 1
    out.append(act.repeat_line)
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    bull = world.facts.get("bull")
    surprise = world.facts.get("surprise")
    if not bull or not surprise:
        return out
    if bull.memes.get("routine", 0.0) < THRESHOLD:
        return out
    sig = ("surprise", bull.id, surprise.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bull.memes["surprise"] = bull.memes.get("surprise", 0.0) + 1
    out.append(f"Then {surprise.trigger}.")
    out.append(f"{bull.pronoun().capitalize()} {surprise.reaction}.")
    return out


def _r_moral(world: World) -> list[str]:
    out: list[str] = []
    bull = world.facts.get("bull")
    surprise = world.facts.get("surprise")
    value = world.facts.get("value")
    if not bull or not surprise or not value:
        return out
    if bull.memes.get("surprise", 0.0) < THRESHOLD:
        return out
    sig = ("moral", bull.id, value.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bull.memes["moral_choice"] = bull.memes.get("moral_choice", 0.0) + 1
    out.append(value.moral_line)
    return out


CAUSAL_RULES = [Rule("repeat", _r_repeat), Rule("surprise", _r_surprise), Rule("moral", _r_moral)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_story(activity: Activity, surprise: Surprise, value: Value) -> bool:
    if activity.id == "greet_neighbors" and surprise.kind == "weather":
        return True
    if activity.id in {"gather_hay", "carry_buckets"} and surprise.kind in {"animal", "object"}:
        return True
    if value.id in {"kindness", "responsibility", "patience"}:
        return True
    return False


def _do_activity(world: World, bull: Entity, activity: Activity, narrate: bool = True) -> None:
    bull.meters[activity.meter] = bull.meters.get(activity.meter, 0.0) + 1
    bull.memes["calm"] = bull.memes.get("calm", 0.0) + 1
    world.say(f"{bull.id} spent the morning {activity.gerund}.")
    propagate(world, narrate=narrate)


def tell(place: Setting, activity: Activity, surprise: Surprise, value: Value,
         name: str, companion: str) -> World:
    world = World(place)
    bull = world.add(Entity(
        id=name,
        kind="character",
        type="bull",
        traits=["little", "steady", "gentle"],
    ))
    other = world.add(Entity(
        id="Companion",
        kind="character",
        type=companion if companion in {"mouse", "calf", "farmer", "duck", "hen", "goat"} else "goat",
        label=f"the {companion}",
    ))
    world.facts["bull"] = bull
    world.facts["companion"] = other
    world.facts["activity"] = activity
    world.facts["surprise"] = surprise
    world.facts["value"] = value

    world.say(f"{bull.id} was a little bull who liked quiet mornings at {world.setting.place}.")
    world.say(f"{bull.pronoun().capitalize()} especially liked {activity.gerund}; it felt tidy and useful.")
    world.say(f"Every day, {bull.id} did the same job with the same calm steps.")
    world.para()

    world.say(f"One morning, {bull.id} went to {world.setting.place} to {activity.verb}.")
    _do_activity(world, bull, activity)
    world.say(f"{bull.pronoun().capitalize()} kept going, because the job was simple and good.")
    world.say(f"{bull.pronoun().capitalize()} did it once more.")
    propagate(world)
    world.para()

    if surprise.kind == "weather":
        world.say(f"At the edge of the field, {surprise.phrase} changed the light.")
    elif surprise.kind == "animal":
        world.say(f"Near the fence, {surprise.phrase} waited with bright eyes.")
    else:
        world.say(f"In the grass, {surprise.phrase} looked lonely and small.")
    propagate(world)

    if surprise.kind == "animal":
        world.say(f"{bull.id} gently nudged the little one toward the warm corner by the barn.")
        world.say(f"{other.label.capitalize()} came over and brought a soft blanket.")
        bull.memes["care"] = bull.memes.get("care", 0.0) + 1
    elif surprise.kind == "object":
        world.say(f"{bull.id} carried the basket back to the path where someone could find it.")
        world.say(f"{other.label.capitalize()} smiled, because the ribbon handle was easy to spot.")
        bull.memes["help"] = bull.memes.get("help", 0.0) + 1
    else:
        world.say(f"{bull.id} and {other.label} worked together to tuck the tools under cover.")
        bull.memes["responsibility"] = bull.memes.get("responsibility", 0.0) + 1

    world.say(value.moral_line)
    world.para()
    world.say(f"By the end of the day, {bull.id} had done the same small task more than once,")
    world.say(f"and the surprise had become part of a calm, helpful memory.")
    world.say(f"{world.setting.place.capitalize()} felt peaceful, and {bull.id} looked content.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bull = f["bull"]
    activity = f["activity"]
    surprise = f["surprise"]
    value = f["value"]
    return [
        f'Write a short slice-of-life story about a bull named {bull.id} who keeps {activity.gerund} and then notices {surprise.phrase}.',
        f"Tell a gentle story for young children about repeated chores, a surprise, and {value.label} in {world.setting.place}.",
        f'Write a small, cozy story where "{activity.keyword}" comes up again and again, and a bull makes a kind choice after an unexpected moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bull = f["bull"]
    activity = f["activity"]
    surprise = f["surprise"]
    value = f["value"]
    qa = [
        QAItem(
            question=f"What did {bull.id} like doing over and over at {world.setting.place}?",
            answer=f"{bull.id} liked {activity.gerund}. He kept doing the same small job because it felt calm and useful.",
        ),
        QAItem(
            question=f"What surprised {bull.id} after all that repeating?",
            answer=f"{surprise.phrase} surprised him. The day shifted in a gentle but unexpected way.",
        ),
        QAItem(
            question=f"What good choice did {bull.id} make when the surprise happened?",
            answer=f"He chose {value.action}. That helped turn the surprise into something kind and helpful.",
        ),
        QAItem(
            question=f"How did the story end for {bull.id}?",
            answer=f"It ended with {bull.id} feeling content at {world.setting.place}, after doing a useful job and making a kind choice.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bull?",
            answer="A bull is an adult male cow. Bulls are strong animals, and they can still be gentle and calm.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing something again and again. It can make a job feel steady and familiar.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect. It arrives suddenly and can change what happens next.",
        ),
        QAItem(
            question="What does it mean to be kind?",
            answer="Being kind means helping, sharing, or caring about someone else's needs.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", activity="gather_hay", surprise="baby_goat", value="kindness", name="Bram", companion="goat"),
    StoryParams(place="barnyard", activity="carry_buckets", surprise="lost_basket", value="responsibility", name="Milo", companion="hen"),
    StoryParams(place="orchard", activity="greet_neighbors", surprise="sudden_rain", value="patience", name="Rufus", companion="farmer"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for act_id, act in ACTIVITIES.items():
            for sur_id, sur in SURPRISES.items():
                for val_id, val in VALUES.items():
                    if can_story(act, sur, val):
                        out.append((place, act_id, sur_id, val_id))
    return out


def explain_rejection(activity: Activity, surprise: Surprise, value: Value) -> str:
    return (
        f"(No story: {activity.gerund} and {surprise.phrase} do not make a strong, "
        f"child-friendly slice-of-life turn for {value.label}. Try a different combination.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a bull's calm routine, a surprise, and a kind choice."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.surprise is None or c[2] == args.surprise)
              and (args.value is None or c[3] == args.value)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, act, sur, val = rng.choice(sorted(combos))
    name = args.name or rng.choice(BULL_NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(place=place, activity=act, surprise=sur, value=val, name=name, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        SURPRISES[params.surprise],
        VALUES[params.value],
        params.name,
        params.companion,
    )
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
% An activity-surprise pair is valid when it supports a gentle slice-of-life turn.
valid(Place, A, S, V) :- place(Place), activity(A), surprise(S), value(V),
                          compatible(A, S, V).

compatible(gather_hay, baby_goat, kindness).
compatible(carry_buckets, lost_basket, responsibility).
compatible(greet_neighbors, sudden_rain, patience).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for vid in VALUES:
        lines.append(asp.fact("value", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible stories:")
        for v in vals:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
            header = f"### {p.name}: {p.activity} / {p.surprise} / {p.value}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
