#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ribbon_kindness_slice_of_life.py
==============================================================================================================

A small slice-of-life storyworld about ribbon, kindness, and everyday care.

The seed image:
---
A child has a special ribbon and wants to use it for a gentle everyday task.
Someone worries it may get wrinkled, lost, or used up.
The child chooses kindness instead of fussing, and the small problem becomes a warm shared moment.
---

This world keeps the domain tiny on purpose:
- one child
- one treasured ribbon
- one ordinary activity
- one kind turning point
- one cozy resolution

The simulated state drives the prose. The ribbon can be worn, shared, tied, straightened,
or saved; kindness can rise, conflict can soften, and the ending proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ribbon:
    label: str = "ribbon"
    phrase: str = "a bright ribbon with a silky bow"
    region: str = "torso"
    color: str = "red"
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Help:
    id: str
    label: str
    action: str
    tail: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.activity: Optional[Activity] = None
        self.facts: dict = {}

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
        clone.activity = self.activity
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    act = world.activity
    if not act:
        return out
    for actor in world.characters():
        if actor.meters.get(act.mess, 0.0) < THRESHOLD:
            continue
        ribbon = next((e for e in world.entities.values() if e.id == "ribbon"), None)
        if ribbon is None or ribbon.worn_by != actor.id:
            continue
        sig = ("tangle", actor.id, act.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ribbon.meters[act.mess] = ribbon.meters.get(act.mess, 0.0) + 1
        ribbon.meters["wrinkled"] = ribbon.meters.get("wrinkled", 0.0) + 1
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"The ribbon came out a little wrinkled.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("kindness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1
        out.append(f"{actor.id} chose a gentle way to help.")
    return out


CAUSAL_RULES = [Rule("tangle", _r_tangle), Rule("kindness", _r_kindness)]


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


def predict(world: World, actor: Entity, act: Activity) -> dict:
    sim = world.copy()
    sim.activity = act
    sim.get(actor.id).meters[act.mess] = 1.0
    propagate(sim, narrate=False)
    ribbon = sim.entities["ribbon"]
    return {
        "wrinkled": ribbon.meters.get("wrinkled", 0.0) >= THRESHOLD,
        "worry": sim.get(actor.id).memes.get("worry", 0.0) >= THRESHOLD,
    }


def setting_detail(setting: Setting, act: Activity) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, everything felt tidy and close."
    return f"{setting.place.capitalize()} felt calm, with room for a small job and a kind choice."


def prize_is_at_risk(act: Activity, ribbon: Ribbon) -> bool:
    return ribbon.region in {"torso"} and act.id in {"help", "decorate", "carry", "wash"}


def select_help(act: Activity, ribbon: Ribbon) -> Optional[Help]:
    for h in HELPERS:
        if act.mess in h.guards:
            return h
    return None


def activity_line(act: Activity) -> str:
    return {
        "help": "helping fold papers",
        "decorate": "decorating a present",
        "carry": "carrying lunch plates",
        "wash": "washing a small bowl",
    }.get(act.id, act.gerund)


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"help", "wash"}),
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"decorate", "help"}),
    "porch": Setting(place="the porch", indoor=False, affords={"carry", "decorate"}),
}

ACTIVITIES = {
    "help": Activity(
        id="help",
        verb="help sort the cards",
        gerund="sorting the cards",
        mess="paper",
        soil="creased",
        risk="the ribbon could get bent",
        keyword="help",
        tags={"kindness", "paper"},
    ),
    "decorate": Activity(
        id="decorate",
        verb="decorate the gift",
        gerund="decorating the gift",
        mess="glitter",
        soil="sparkly and messy",
        risk="the ribbon could get glittery",
        keyword="decorate",
        tags={"kindness", "glitter"},
    ),
    "carry": Activity(
        id="carry",
        verb="carry the lunch plates",
        gerund="carrying the plates",
        mess="sauce",
        soil="spotted",
        risk="the ribbon could get spotted",
        keyword="carry",
        tags={"kindness", "shared"},
    ),
    "wash": Activity(
        id="wash",
        verb="wash a small bowl",
        gerund="washing the bowl",
        mess="water",
        soil="damp",
        risk="the ribbon could get damp",
        keyword="wash",
        tags={"kindness", "water"},
    ),
}

RIBBON = Ribbon()

HELPERS = [
    Help(id="clip", label="a small hair clip", action="pin the ribbon neatly in place", tail="pinned the ribbon neatly in place", guards={"paper"}),
    Help(id="napkin", label="a clean napkin", action="wrap the ribbon away from the water", tail="kept the ribbon dry and safe", guards={"water"}),
    Help(id="tray", label="a little tray", action="carry the ribbon on top", tail="let the ribbon ride along without getting spotted", guards={"sauce"}),
    Help(id="tissue", label="a soft tissue", action="brush the glitter off", tail="made the ribbon look tidy again", guards={"glitter"}),
]

GIRL_NAMES = ["Mina", "Lila", "Ava", "Nora", "Iris", "Pia"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Owen", "Milo"]
TRAITS = ["gentle", "cheerful", "careful", "patient", "bright"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            if select_help(act, RIBBON):
                combos.append((place, act_id))
    return combos


def explain_rejection(act: Activity) -> str:
    return f"(No story: there is no kind fix in this tiny world for {act.gerund}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        if args.activity:
            raise StoryError(explain_rejection(ACTIVITIES[args.activity]))
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, act: Activity, params: StoryParams) -> World:
    world = World(setting)
    world.activity = act
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent"))
    ribbon = world.add(Entity(id="ribbon", type="ribbon", label="ribbon", phrase=RIBBON.phrase, owner=child.id, caretaker=parent.id))
    ribbon.worn_by = child.id

    child.memes["kindness"] = 1.0
    child.memes["love"] = 1.0

    world.say(f"{params.name} was a {params.trait} little {params.gender} who loved a bright ribbon.")
    world.say(f"{params.name} wore the ribbon every day because it made ordinary things feel special.")
    world.say(f"One day, {params.name} went to {setting.place} to {act.verb} with {params.name}'s {params.parent}.")
    world.say(setting_detail(setting, act))

    world.para()
    world.say(f"{params.name} wanted to {act.verb}, but {params.name}'s {params.parent} noticed the ribbon might get {act.soil}.")
    pred = predict(world, child, act)
    world.facts["predicted"] = pred
    if pred["wrinkled"]:
        world.say(f'"If we rush," the {params.parent} said, "the ribbon could get {act.soil}."')
    else:
        world.say(f'"We should be careful," the {params.parent} said, "so the ribbon stays neat."')

    world.say(f"{params.name} paused, then chose kindness over fussing.")
    child.memes["kindness"] += 1.0
    child.meters[act.mess] = 1.0

    helper = select_help(act, RIBBON)
    if helper is not None:
        world.say(f"{params.name} used {helper.label} to {helper.action}.")
        ribbon.meters[act.mess] = 0.0
        ribbon.meters["wrinkled"] = 0.0
        world.say(f"That small help kept the ribbon safe.")
        world.say(f"Then {params.name} could keep going with the task.")
    propagate(world, narrate=True)

    world.para()
    if helper is not None:
        world.say(f"In the end, {params.name} finished {act.gerund}, and the ribbon still looked lovely.")
        world.say(f"The {params.parent} smiled because kindness had made the little job easy to share.")
    else:
        world.say(f"In the end, {params.name} finished the task and tucked the ribbon away with care.")
        world.say(f"It was just a small day, but the ribbon stayed part of the memory.")

    world.facts.update(child=child, parent=parent, ribbon=ribbon, helper=helper, setting=setting, activity=act)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    act = f["activity"]
    return [
        f'Write a short slice-of-life story for a young child about {child.id}, a ribbon, and a kind choice.',
        f"Tell a gentle everyday story where {child.id} wants to {act.verb} but {parent.label} worries about a ribbon.",
        f'Write a cozy story that uses the word "ribbon" and shows kindness turning a small problem into a happy moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    act = f["activity"]
    helper = f["helper"]
    ribbon = f["ribbon"]
    place = world.setting.place
    qas = [
        QAItem(
            question=f"Who is the story about at {place}?",
            answer=f"It is about {child.id}, a little {child.type} who loves a ribbon and tries to be kind during an ordinary day.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with {parent.label}?",
            answer=f"{child.id} wanted to {act.verb}, but the ribbon needed careful handling so it would stay neat.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the ribbon?",
            answer=f"{parent.label} worried because the ribbon could get {act.soil} while {child.id} did the task.",
        ),
    ]
    if helper is not None:
        qas.append(
            QAItem(
                question=f"How did the kind helper idea solve the problem?",
                answer=f"{child.id} used {helper.label} so the ribbon stayed safe, and that let the work go on without a big fuss.",
            )
        )
    qas.append(
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {child.id} had finished {act.gerund} and the ribbon still looked lovely because kindness kept the moment calm.",
        )
    )
    return qas


KNOWLEDGE = {
    "ribbon": [
        QAItem(
            question="What is a ribbon?",
            answer="A ribbon is a long, soft strip of cloth that people often tie into bows or use to make something look pretty.",
        )
    ],
    "kindness": [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and thoughtful so other people feel cared for.",
        )
    ],
    "glitter": [
        QAItem(
            question="Why can glitter be messy?",
            answer="Glitter is tiny shiny pieces that stick to things and can scatter all over the place.",
        )
    ],
    "water": [
        QAItem(
            question="What does water do to paper?",
            answer="Water can make paper soft, bent, or damp, so people try to keep paper dry when they can.",
        )
    ],
    "paper": [
        QAItem(
            question="What is paper used for?",
            answer="Paper can be used for drawing, writing notes, making cards, and many other everyday jobs.",
        )
    ],
    "shared": [
        QAItem(
            question="What is a shared job?",
            answer="A shared job is something two people do together so the work feels lighter and friendlier.",
        )
    ],
}

KNOWLEDGE_ORDER = ["ribbon", "kindness", "paper", "glitter", "water", "shared"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="help", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="bedroom", activity="decorate", name="Eli", gender="boy", parent="father", trait="careful"),
    StoryParams(place="porch", activity="carry", name="Nora", gender="girl", parent="mother", trait="patient"),
    StoryParams(place="kitchen", activity="wash", name="Theo", gender="boy", parent="father", trait="bright"),
]


ASP_RULES = r"""
prize_at_risk(A) :- activity(A), needs_care(A).
kind_fix(A, H) :- activity(A), helper(H), guards(H, M), mess_of(A, M).
valid_story(P, A) :- place(P), affords(P, A), prize_at_risk(A), kind_fix(A, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        lines.append(asp.fact("needs_care", aid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for m in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_storys_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(valid_storys_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about ribbon and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_storys_asp()
        print(f"{len(combos)} compatible (place, activity) combos:\n")
        for place, act in combos:
            print(f"  {place:8} {act}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
