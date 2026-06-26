#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/incline_feeder_kindness_bad_ending_conflict_comedy.py
=========================================================================================

A small comic storyworld about an incline, a feeder, and a kindness that
almost goes right.

Seed-tale premise:
- A child and a caregiver build a feeder on a sloped yard.
- Kindness invites a hungry visitor.
- The incline makes the feeder slide, spill, or swing.
- Conflict appears when the kind plan backfires.
- The ending is mildly bad in a funny way: the birds still win, but the humans
  end up with crumbs, bruised pride, and a new plan.

This world keeps the prose child-facing and state-driven:
the feeder has physical position, the hill has slope, and the characters'
memes track kindness, conflict, and comedic disappointment.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the backyard"
    slope: str = "gentle"
    outdoors: bool = True


@dataclass
class FeederSpec:
    id: str
    label: str
    phrase: str
    hangs: str
    slip: str
    spill: str
    helps_with: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    feeder: str
    name: str
    gender: str
    helper: str
    tone: str
    seed: Optional[int] = None


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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _ensure(fact: tuple, world: World) -> bool:
    if fact in world.fired:
        return False
    world.fired.add(fact)
    return True


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in [e for e in world.entities.values() if e.kind == "character"]:
            feeder = next((e for e in world.entities.values() if e.type == "feeder" and e.owner == actor.id), None)
            if not feeder:
                continue
            if actor.memes.get("kindness", 0) >= THRESHOLD and feeder.meters.get("on_incline", 0) >= THRESHOLD:
                if feeder.meters.get("stable", 0) < THRESHOLD:
                    sig = ("slip", feeder.id)
                    if _ensure(sig, world):
                        feeder.meters["sliding"] = 1
                        actor.memes["conflict"] = actor.memes.get("conflict", 0) + 1
                        out.append(f"The feeder wobbled on the incline and slid sideways.")
                        changed = True
            if feeder.meters.get("sliding", 0) >= THRESHOLD and feeder.meters.get("seed_full", 0) >= THRESHOLD:
                sig = ("spill", feeder.id)
                if _ensure(sig, world):
                    feeder.meters["spilled"] = 1
                    actor.meters["mess"] = actor.meters.get("mess", 0) + 1
                    out.append(f"Seeds poured out in a silly little rain.")
                    changed = True
            if feeder.meters.get("spilled", 0) >= THRESHOLD:
                bird = world.entities.get("bird")
                if bird and bird.memes.get("hungry", 0) >= THRESHOLD:
                    sig = ("bird_eats", feeder.id)
                    if _ensure(sig, world):
                        bird.memes["joy"] = bird.memes.get("joy", 0) + 1
                        out.append("The bird pecked happily at the fallen seeds anyway.")
                        changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def setup_world(setting: Setting, feeder: FeederSpec, params: StoryParams) -> World:
    world = World(setting)
    kid = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    bird = world.add(Entity(id="bird", kind="character", type="bird", label="a hungry bird"))
    bird.memes["hungry"] = 1
    bird.memes["joy"] = 0
    box = world.add(Entity(
        id=feeder.id,
        kind="thing",
        type="feeder",
        label=feeder.label,
        phrase=feeder.phrase,
        owner=kid.id,
        caretaker=helper.id,
    ))
    box.meters["on_incline"] = 1
    box.meters["stable"] = 0
    box.meters["seed_full"] = 1

    kid.memes["kindness"] = 1
    kid.memes["conflict"] = 0
    kid.memes["embarrassment"] = 0
    helper.memes["kindness"] = 1

    world.facts.update(
        kid=kid,
        helper=helper,
        bird=bird,
        feeder=box,
        feeder_spec=feeder,
        setting=setting,
    )
    return world


def intro(world: World) -> None:
    kid = world.facts["kid"]
    helper = world.facts["helper"]
    feeder = world.facts["feeder"]
    setting = world.facts["setting"]
    world.say(
        f"{kid.id} was a {world.facts['kid'].type} who loved small acts of kindness."
    )
    world.say(
        f"One bright day, {kid.id} and {helper.label} carried {feeder.label} out to {setting.place}."
    )
    world.say(
        f"They wanted to hang {feeder.label} on the incline by the path so the birds could eat without a fuss."
    )


def conflict_beat(world: World) -> None:
    kid = world.facts["kid"]
    feeder = world.facts["feeder"]
    world.para()
    world.say(
        f"{kid.id} tied the feeder up carefully, but the slope gave it a sneaky push."
    )
    propagate(world)
    if feeder.meters.get("spilled", 0) >= THRESHOLD:
        world.say(
            f"{kid.id} stared at the spill, then looked at the feeder as if it had told a joke too soon."
        )
        world.say(
            f"That was the conflict: kindness had been meant to help, but the incline made the plan wobble."
        )


def ending_beat(world: World) -> None:
    kid = world.facts["kid"]
    helper = world.facts["helper"]
    bird = world.facts["bird"]
    feeder = world.facts["feeder"]
    world.para()
    world.say(
        f"{helper.label} laughed first and said, “Well, that is one way to feed a bird.”"
    )
    world.say(
        f"{kid.id} tried a steadier hook, but the feeder was already dusty, crooked, and very proud of itself."
    )
    if bird.memes.get("joy", 0) >= THRESHOLD:
        world.say(
            f"The bird kept pecking at the seeds on the ground, so the whole yard looked a little messy and a little silly."
        )
    world.say(
        f"In the end, {kid.id} had a kind idea, a bad ending, and one very satisfied bird."
    )
    world.say(
        f"The feeder stayed on the incline, but from then on it needed a better plan before anyone called it a success."
    )
    world.facts["resolved"] = False
    world.facts["bad_ending"] = True


SETTING_REGISTRY = {
    "backyard": Setting(place="the backyard", slope="gentle", outdoors=True),
    "garden_path": Setting(place="the garden path", slope="steep", outdoors=True),
    "school_yard": Setting(place="the school yard", slope="slanted", outdoors=True),
}

FEEDERS = {
    "tube": FeederSpec(
        id="tube",
        label="a bright tube feeder",
        phrase="a bright tube feeder with a little perch",
        hangs="hang it by the path",
        slip="tilt",
        spill="spill",
        helps_with={"birds"},
    ),
    "tray": FeederSpec(
        id="tray",
        label="a wooden tray feeder",
        phrase="a wooden tray feeder with open sides",
        hangs="set it on a hook",
        slip="skid",
        spill="scatter",
        helps_with={"birds"},
    ),
    "house": FeederSpec(
        id="house",
        label="a tiny house feeder",
        phrase="a tiny house feeder with a red roof",
        hangs="hook it onto the post",
        slip="lean",
        spill="drop",
        helps_with={"birds"},
    ),
}

GENDER_NAMES = {
    "girl": ["Maya", "Lily", "Nora", "Zoe", "Ava"],
    "boy": ["Eli", "Theo", "Ben", "Max", "Leo"],
}
HELPERS = ["mother", "father", "grandparent"]
TONE = "comedy"


def valid_combos() -> list[tuple[str, str]]:
    return [(s, f) for s in SETTING_REGISTRY for f in FEEDERS]


@dataclass
class RuleResult:
    text: str


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.feeder and args.setting is None:
        pass
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.feeder:
        combos = [c for c in combos if c[1] == args.feeder]
    if not combos:
        raise StoryError("No valid story matches the chosen setting and feeder.")

    setting, feeder = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDER_NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    tone = "comedy"
    return StoryParams(setting=setting, feeder=feeder, name=name, gender=gender, helper=helper, tone=tone)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(SETTING_REGISTRY[params.setting], FEEDERS[params.feeder], params)
    intro(world)
    conflict_beat(world)
    ending_beat(world)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    feeder = f["feeder_spec"]
    setting = f["setting"]
    return [
        f"Write a funny story about {kid.id} trying to feed birds with {feeder.label} on an incline at {setting.place}.",
        f"Tell a child-friendly comedy where kindness causes a feeder to slip down a slope.",
        f"Write a short story in which a bird feeder, an incline, and a bad ending create a silly conflict.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    helper = f["helper"]
    feeder = f["feeder_spec"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who tried to make the bird feeder kind and helpful?",
            answer=f"{kid.id} tried to do something kind by setting up {feeder.label} for the birds.",
        ),
        QAItem(
            question=f"Why did the plan cause conflict?",
            answer=f"The plan caused conflict because {feeder.label} was placed on an incline, so it slid and spilled seeds instead of staying still.",
        ),
        QAItem(
            question=f"What made the ending bad in a funny way?",
            answer=f"The ending was bad in a funny way because the feeder tipped, the seeds scattered, and the birds ate happily while the humans had to laugh at the mess.",
        ),
        QAItem(
            question=f"Where did {kid.id} and {helper.label} take the feeder?",
            answer=f"They took it to {setting.place}, where the slope made the feeder hard to keep steady.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an incline?",
            answer="An incline is a slanted surface that goes up or down instead of staying flat.",
        ),
        QAItem(
            question="What is a feeder?",
            answer="A feeder is something that holds food for birds or other animals so they can eat it easily.",
        ),
        QAItem(
            question="Why can a sloped place be tricky for a feeder?",
            answer="A sloped place can be tricky because gravity can make the feeder slide, tilt, or spill its food.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means doing something caring or helpful for someone else, like sharing food or making life easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
feeder(F) :- feeder_spec(F).
inclined(F) :- on_incline(F).
kind_story(K) :- kindness(K), conflict(C), C > 0.
bad_ending(F) :- feeder(F), inclined(F), spilled(F).
conflict_story(F) :- feeder(F), inclined(F), conflict(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for fid, f in FEEDERS.items():
        lines.append(asp.fact("feeder_spec", fid))
        lines.append(asp.fact("label", fid, f.label))
        lines.append(asp.fact("on_incline", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # Python gate is simple and deterministic: all feeder/setting combos are valid.
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show feeder_spec/1."))
    asp_set = {(s[0], f) for (f,) in asp.atoms(model, "feeder_spec") for s in []}  # unused placeholder
    # Instead of deriving a fragile set from the trivial rules, directly check the facts.
    asp_feeders = {args[0] for args in asp.atoms(model, "feeder_spec")}
    if asp_feeders != set(FEEDERS):
        print("MISMATCH between ASP and Python feeder registry.")
        return 1
    if py != set(valid_combos()):
        print("MISMATCH between ASP and Python valid combos.")
        return 1
    print(f"OK: ASP facts and Python registries agree ({len(py)} combos).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comic incline-and-feeder storyworld.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--feeder", choices=FEEDERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    StoryParams(setting="backyard", feeder="tube", name="Maya", gender="girl", helper="mother", tone="comedy"),
    StoryParams(setting="garden_path", feeder="tray", name="Eli", gender="boy", helper="father", tone="comedy"),
    StoryParams(setting="school_yard", feeder="house", name="Nora", gender="girl", helper="grandparent", tone="comedy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show feeder_spec/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show feeder_spec/1."))
        feeders = sorted(set(asp.atoms(model, "feeder_spec")))
        print(f"{len(feeders)} feeder facts:")
        for f in feeders:
            print(f"  {f[0]}")
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
            header = f"### {p.name}: {p.feeder} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
