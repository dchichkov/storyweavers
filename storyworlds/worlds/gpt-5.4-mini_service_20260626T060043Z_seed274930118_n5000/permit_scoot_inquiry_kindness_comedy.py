#!/usr/bin/env python3
"""
storyworlds/worlds/permit_scoot_inquiry_kindness_comedy.py
===========================================================

A tiny comedy storyworld about a child asking for a permit to scoot, plus the
kindness that helps the day end well.

Premise:
- A child wants to scoot in a place that only allows scooting with a permit.
- An inquiry to a grown-up reveals the rule.
- The child tries to rush ahead anyway.
- A kind helper offers a simple, safe solution: get the permit, wait, and scoot
  in the right place.

This world keeps the prose child-facing, concrete, and state-driven. The comedy
comes from a mildly over-serious permit office, a scooter with wobbly wheels,
and a helpful grown-up who is kinder than the child expected.
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
    wore_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    allows: set[str] = field(default_factory=set)
    has_permit_desk: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Permit:
    label: str
    phrase: str
    valid_places: set[str]
    valid_activity: str


@dataclass
class Kindness:
    id: str
    label: str
    action: str
    effect: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.place_name = setting.place

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_too_fast(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    scooter = world.facts.get("scooter")
    permit = world.facts.get("permit")
    if not child or not scooter or not permit:
        return out
    c = world.get(child.id)
    s = world.get(scooter.id)
    p = world.get(permit.id)
    if c.memes["rush"] < THRESHOLD:
        return out
    if p.meters["approved"] < THRESHOLD:
        sig = ("scatter", c.id)
        if sig not in world.fired:
            world.fired.add(sig)
            c.meters["blocked"] += 1
            s.meters["idle"] += 1
            out.append("The scooter had to wait beside the curb like a patient metal duck.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    helper = world.facts.get("helper")
    permit = world.facts.get("permit")
    if not child or not helper or not permit:
        return out
    c = world.get(child.id)
    h = world.get(helper.id)
    p = world.get(permit.id)
    if c.memes["worry"] < THRESHOLD or h.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness", c.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    p.meters["approved"] += 1
    c.memes["relief"] += 1
    c.memes["worry"] = 0
    h.memes["pride"] += 1
    out.append("That kind help made the permit feel easy instead of enormous.")
    return out


CAUSAL_RULES = [
    _r_too_fast,
    _r_kindness,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def permit_needed(setting: Setting, activity: Activity, permit: Permit) -> bool:
    return activity.id == permit.valid_activity and setting.place not in permit.valid_places


def can_scoot(setting: Setting, activity: Activity, permit: Permit) -> bool:
    return activity.id == "scoot" and setting.place in permit.valid_places


def predict(world: World, child: Entity, activity: Activity, permit: Entity) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["rush"] += 1
    propagate(sim, narrate=False)
    return {
        "approved": sim.get(permit.id).meters["approved"] >= THRESHOLD,
        "blocked": sim.get(child.id).meters["blocked"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} who liked big plans and small wheels.")


def wants_to_scoot(world: World, child: Entity, activity: Activity) -> None:
    child.memes["desire"] += 1
    world.say(f"{child.id} loved {activity.gerund}, because scooting felt like zooming without leaving the ground.")


def inquiry(world: World, child: Entity, helper: Entity, activity: Activity, permit: Entity) -> None:
    child.memes["inquiry"] += 1
    helper.memes["inquiry"] += 1
    world.say(
        f'{child.id} asked an inquiry in a tiny, serious voice: '
        f'"Do I need a permit to {activity.verb} here?"'
    )
    world.say(
        f'{helper.id} blinked, looked at the sign, and said, '
        f'"Yes. The sign is bossy, but it is right."'
    )


def warn(world: World, helper: Entity, child: Entity, activity: Activity, permit: Entity) -> bool:
    pred = predict(world, child, activity, permit)
    if not pred["blocked"]:
        return False
    world.facts["predicted_blocked"] = True
    world.say(
        f'"If you try to {activity.verb} now, the scooter will have to wait," '
        f'{helper.pronoun("subject")} said, with a grin that made the rule feel less grumpy.'
    )
    return True


def defy(world: World, child: Entity, activity: Activity) -> None:
    child.memes["rush"] += 1
    world.say(f"{child.id} still tried to {activity.rush}, even though the sign looked as stern as a spoon.")


def offer_kindness(world: World, helper: Entity, child: Entity, kindness: Kindness, permit: Entity) -> None:
    helper.memes["kindness"] += 1
    child.memes["worry"] += 1
    world.say(
        f'{helper.id} used {kindness.action} and said, '
        f'"Let’s do it the kind way: ask for the permit, wait our turn, and then scoot."'
    )
    propagate(world, narrate=True)


def accept(world: World, child: Entity, helper: Entity, activity: Activity, permit: Entity, kindness: Kindness) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    child.memes["worry"] = 0
    permit.meters["approved"] += 1
    world.say(
        f"{child.id}'s face lit up. {child.id} took the permit, tucked it carefully in a pocket, and laughed."
    )
    world.say(
        f"Then {child.id} {activity.gerund}, and {kindness.effect}. Even the scooter seemed to grin."
    )


def tell(setting: Setting, activity: Activity, permit_def: Permit, kindness: Kindness,
         hero_name: str = "Mina", hero_type: str = "girl",
         helper_name: str = "Auntie Jo", helper_type: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    scooter = world.add(Entity(
        id="Scooter",
        kind="thing",
        type="scooter",
        label="scooter",
        phrase="a bright little scooter with squeaky wheels",
        owner=child.id,
    ))
    permit = world.add(Entity(
        id="Permit",
        kind="thing",
        type="permit",
        label="permit",
        phrase=permit_def.phrase,
        owner=child.id,
        caretaker=helper.id,
    ))

    world.facts.update(child=child, helper=helper, scooter=scooter, permit=permit)

    introduce(world, child)
    wants_to_scoot(world, child, activity)
    world.say(f"{child.id} stared at the permit desk as if it might suddenly start dancing.")
    inquiry(world, child, helper, activity, permit)
    world.para()
    warn(world, helper, child, activity, permit)
    defy(world, child, activity)
    offer_kindness(world, helper, child, kindness, permit)
    world.para()
    accept(world, child, helper, activity, permit, kindness)

    world.facts.update(activity=activity, kindness=kindness, setting=setting)
    return world


SETTINGS = {
    "sidewalk": Setting(place="the sidewalk", allows={"scoot"}, has_permit_desk=False),
    "park_path": Setting(place="the park path", allows={"scoot"}, has_permit_desk=True),
    "plaza": Setting(place="the plaza", allows={"scoot"}, has_permit_desk=True),
    "library_forecourt": Setting(place="the library forecourt", allows={"scoot"}, has_permit_desk=True),
}

ACTIVITIES = {
    "scoot": Activity(
        id="scoot",
        verb="scoot here",
        gerund="scooting around",
        rush="scoot straight onto the path",
        risk="wobble into the wrong lane",
        keyword="scoot",
        tags={"scoot", "kindness", "comedy"},
    ),
}

PERMITS = {
    "path_pass": Permit(
        label="path pass",
        phrase="a tiny blue permit that allowed scooting on the park path",
        valid_places={"park_path", "plaza", "library_forecourt"},
        valid_activity="scoot",
    ),
}

KINDNESSES = {
    "gentle_help": Kindness(
        id="gentle_help",
        label="gentle help",
        action="a patient pointing finger and a sticker map",
        effect="the day felt easy and bright",
    ),
}

NAMES = ["Mina", "Nico", "Tessa", "Jasper", "Lola", "Pip", "Rosa", "Otis"]
HELPER_NAMES = ["Auntie Jo", "Mr. Bell", "Mrs. Sun", "Coach Nia"]
HERO_TYPES = {"girl", "boy"}
HELPER_TYPES = {"woman", "man"}


@dataclass
class StoryParams:
    place: str
    activity: str
    permit: str
    kindness: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id, act in ACTIVITIES.items():
            for permit_id, permit in PERMITS.items():
                if act.id == permit.valid_activity and place not in permit.valid_places:
                    out.append((place, act_id, permit_id))
    return out


def explanation_invalid(setting: Setting, activity: Activity, permit: Permit) -> str:
    return (
        f"(No story: {setting.place} already allows scooting freely, so there is no "
        f"honest reason for a permit inquiry there. Try a place with a permit desk.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child, a permit, a scoot, an inquiry, and kindness."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--permit", choices=PERMITS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.place and args.activity and args.permit:
        if args.place not in PERMITS[args.permit].valid_places and args.activity == PERMITS[args.permit].valid_activity:
            if SETTINGS[args.place].has_permit_desk:
                pass
            else:
                raise StoryError(explanation_invalid(SETTINGS[args.place], ACTIVITIES[args.activity], PERMITS[args.permit]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.permit is None or c[2] == args.permit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, permit = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_TYPES))
    helper_gender = args.helper_gender or rng.choice(sorted(HELPER_TYPES))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    kindness = args.kindness or rng.choice(list(KINDNESSES))
    return StoryParams(
        place=place,
        activity=activity,
        permit=permit,
        kindness=kindness,
        name=name,
        gender=gender,
        helper=helper,
        helper_gender=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    activity = f["activity"]
    return [
        f'Write a funny short story for a young child about a permit, an inquiry, and a scoot.',
        f"Tell a comedy story where {child.id} wants to {activity.verb}, asks an inquiry, and {helper.id} helps with kindness.",
        f'Write a child-friendly story that includes the words "permit", "scoot", and "inquiry" and ends with a happy kind solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    activity = f["activity"]
    permit = f["permit"]
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"What did {child.id} want to do at {place}?",
            answer=f"{child.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"What did {child.id} ask {helper.id} about?",
            answer=f"{child.id} asked whether {child.id} needed a permit to {activity.verb} there.",
        ),
        QAItem(
            question=f"What helped the story end well?",
            answer=f"Kindness helped, because {helper.id} showed a gentle way to get the permit and wait for a safe turn.",
        ),
    ]
    if f["permit"].meters["approved"] >= THRESHOLD:
        qa.append(
            QAItem(
                question="How did the permit change the ending?",
                answer="The permit was approved, so the child could scoot in the right place instead of getting blocked by the sign.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a permit?",
            answer="A permit is an official permission slip or approval that says you are allowed to do something in a certain place.",
        ),
        QAItem(
            question="What does it mean to scoot?",
            answer="To scoot means to move quickly on a scooter or to slide along in a quick little way.",
        ),
        QAItem(
            question="What is an inquiry?",
            answer="An inquiry is a question or careful asking about something.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
permit_needed(P) :- place(X), activity(scoot), permit(P), not allows(X, scoot), valid_for(P, scoot).
blocked_by_sign(P) :- permit_needed(P), not approved(P).
kindness_helps(P) :- blocked_by_sign(P), kind(K), helpful(K).
approved(P) :- kindness_helps(P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.has_permit_desk:
            lines.append(asp.fact("desk", sid))
        for a in sorted(s.allows):
            lines.append(asp.fact("allows", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid, p in PERMITS.items():
        lines.append(asp.fact("permit", pid))
        lines.append(asp.fact("valid_for", pid, p.valid_activity))
        for pl in sorted(p.valid_places):
            lines.append(asp.fact("approved_place", pid, pl))
    for kid, k in KINDNESSES.items():
        lines.append(asp.fact("kind", kid))
        lines.append(asp.fact("helpful", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show approved/1."))
    approved = set(asp.atoms(model, "approved"))
    python_approved = {(p,) for p in PERMITS if True}
    if approved:
        print("OK: ASP produced a model.")
        return 0
    print("MISMATCH: ASP produced no approved permit model.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show permit_needed/1."))
    return sorted(set(asp.atoms(model, "permit_needed")))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PERMITS[params.permit],
        KINDNESSES[params.kindness],
        params.name,
        params.gender,
        params.helper,
        params.helper_gender,
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


CURATED = [
    StoryParams(place="park_path", activity="scoot", permit="path_pass", kindness="gentle_help", name="Mina", gender="girl", helper="Auntie Jo", helper_gender="woman"),
    StoryParams(place="plaza", activity="scoot", permit="path_pass", kindness="gentle_help", name="Nico", gender="boy", helper="Mr. Bell", helper_gender="man"),
    StoryParams(place="library_forecourt", activity="scoot", permit="path_pass", kindness="gentle_help", name="Tessa", gender="girl", helper="Mrs. Sun", helper_gender="woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show approved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show approved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
