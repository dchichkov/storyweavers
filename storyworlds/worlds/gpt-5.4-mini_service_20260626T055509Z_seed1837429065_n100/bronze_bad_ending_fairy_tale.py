#!/usr/bin/env python3
"""
storyworlds/worlds/bronze_bad_ending_fairy_tale.py
===================================================

A small fairy-tale story world about a child, a bronze thing, a warning,
and a bad ending.

Premise:
- A child treasures a bronze key.
- A parent warns that a wishing well is greedy for shiny things.
- The child ignores the warning, and the key is lost forever.

The story is intentionally a bad ending: no safe compromise exists, so the
child does not get the treasure back. The world model still drives the prose,
emotional beats, and QA.
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    mood: str = "ancient"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("risk", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone:
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            item.meters["lost"] = item.meters.get("lost", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} slipped from {actor.pronoun('possessive')} hand.")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("lost", 0.0) < THRESHOLD:
            continue
        sig = ("loss", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"It was swallowed by the well and never came back.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soil, _r_loss):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_loss(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = World(world.setting)
    import copy
    sim.entities = copy.deepcopy(world.entities)
    sim.zone = set(activity.zone)
    sim.get(actor.id).meters["risk"] = 1.0
    for item in sim.worn_items(sim.get(actor.id)):
        if item.id == prize_id and item.region in sim.zone:
            item.meters["lost"] = 1.0
    propagate(sim, narrate=False)
    return bool(sim.get(prize_id).meters.get("lost", 0.0) >= THRESHOLD)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         child_name: str, child_type: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="bronze_key",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        worn_by=child.id,
    ))

    # Act 1
    world.say(f"Once in a little village, {child.id} was a {child_type} who loved every bright thing that gleamed.")
    world.say(f"{child.pronoun().capitalize()} treasured {child.pronoun('possessive')} {prize.label}, for it shone like a tiny piece of dawn.")
    world.say(f"The old stones around {setting.place} looked silver in the light, and {child.id} wanted to {activity.verb}.")

    # Act 2
    world.para()
    world.say(f"One day at {setting.place}, {parent.label} lifted a careful hand and said, \"Do not {activity.verb}; the well is greedy for shiny things.\"")
    world.say(f"{child.id} heard the warning, but curiosity pulled harder than good sense.")
    child.meters["risk"] = 1.0
    child.memes["defiance"] = 1.0
    world.say(f"{child.pronoun().capitalize()} tried to {activity.rush}, and the bronze key flashed in the dark water.")

    if predict_loss(world, child, activity, prize.id):
        world.say(f"The well gave a soft gulp, and the key slipped from {child.pronoun('possessive')} fingers.")
        world.say(f"{parent.label} reached too late; the water kept the bronze key, and the child could only watch the ripples close.")

    # Act 3 - bad ending
    world.para()
    propagate(world, narrate=True)
    child.memes["sorrow"] = 1.0
    world.say(f"By dusk, {child.id} sat beside {setting.place} with empty hands and wet cheeks.")
    world.say(f"The bronze key was gone, and the little gate it opened stayed shut forever.")

    world.facts.update(
        child=child,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        lost=True,
    )
    return world


SETTINGS = {
    "well": Setting(place="the wishing well", affords={"peek", "reach"}, mood="ancient"),
    "forest": Setting(place="the moonlit forest", affords={"peek", "follow"}, mood="haunted"),
    "castle_gate": Setting(place="the castle gate", affords={"reach", "ring"}, mood="formal"),
}

ACTIVITIES = {
    "peek": Activity(
        id="peek",
        verb="peek into the well",
        gerund="peeking into the well",
        rush="lean over the well",
        mess="lost",
        soil="lost",
        zone={"hands", "torso"},
        keyword="well",
    ),
    "reach": Activity(
        id="reach",
        verb="reach for the shining water",
        gerund="reaching for the shining water",
        rush="stretch over the stones",
        mess="lost",
        soil="lost",
        zone={"hands", "torso"},
        keyword="bronze",
    ),
    "follow": Activity(
        id="follow",
        verb="follow the silver path",
        gerund="following the silver path",
        rush="run after the pale lights",
        mess="lost",
        soil="lost",
        zone={"feet", "hands"},
        keyword="moon",
    ),
    "ring": Activity(
        id="ring",
        verb="ring the old gate bell",
        gerund="ringing the old gate bell",
        rush="pull the bell cord",
        mess="lost",
        soil="lost",
        zone={"hands", "torso"},
        keyword="bell",
    ),
}

PRIZES = {
    "key": Prize(
        label="bronze key",
        phrase="a small bronze key on a blue ribbon",
        type="key",
        region="hands",
    ),
    "buckle": Prize(
        label="bronze buckle",
        phrase="a bright bronze buckle on a sash",
        type="buckle",
        region="torso",
    ),
}

NAMES = ["Ava", "Mina", "Elin", "Nora", "Pip", "Tara", "Lina", "Owen"]
CHILD_TYPES = ["girl", "boy"]
PARENTS = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def explain_rejection() -> str:
    return "(No story: the requested choices do not fit this little fairy-tale world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fairy-tale story world with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=CHILD_TYPES)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError(explain_rejection())
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(CHILD_TYPES)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short fairy tale for a young child about "{prize.label}" and a warning at {f["setting"].place}.',
        f"Tell a gentle but sad story where {child.id} wants to {act.verb} and loses {prize.label}.",
        f'Write a simple story that includes the word "bronze" and ends with a closed gate and an empty hand.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {child.id} treasure in the story?",
            answer=f"{child.id} treasured {prize.phrase}, a little bronze key that shone like dawn.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {child.id} at {setting.place}?",
            answer=f"{parent.label.capitalize()} warned {child.id} because {act.verb} near the wishing well could make the bronze key slip away.",
        ),
        QAItem(
            question=f"What happened when {child.id} ignored the warning?",
            answer=f"{child.id} leaned in anyway, the bronze key fell, and the well kept it forever.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended sadly: {child.id} sat by {setting.place} with empty hands, and the little gate stayed shut.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bronze?",
            answer="Bronze is a metal that often looks warm and golden-brown, like an old statue, bell, or key.",
        ),
        QAItem(
            question="What is a wishing well?",
            answer="A wishing well is a deep stone well where people toss things or make wishes and hope for luck.",
        ),
        QAItem(
            question="Why do shiny things catch a child's eye?",
            answer="Shiny things catch a child's eye because they sparkle and seem special and exciting.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A,P) :- splashes(A,R), worn_on(P,R).
valid_story(Place,A,P) :- affords(Place,A), prize(P), at_risk(A,P).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent)
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
    StoryParams(place="well", activity="peek", prize="key", name="Mina", gender="girl", parent="grandmother"),
    StoryParams(place="well", activity="reach", prize="key", name="Owen", gender="boy", parent="father"),
    StoryParams(place="castle_gate", activity="ring", prize="buckle", name="Lina", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
