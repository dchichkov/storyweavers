#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lymphatic_index_resolution_humor_lesson_learned_twist.py
========================================================================================================

A small slice-of-life story world about a child, a library project, and a
slightly funny misunderstanding that turns into a useful lesson.

Seed image:
---
A child is trying to finish an index for a little report about the lymphatic
system. The cards get mixed up, the grown-up notices the chaos, and the child
learns that good labels can save a lot of time. The twist is that the "index"
turns out to be for a handmade book, not a test, so the pressure was mostly in
the child's own head.

World shape:
---
- physical state: notes, index cards, tabs, tea stain, poster board
- emotional state: worry, humor, focus, relief, pride
- causal turn: a small mix-up causes a pause, then a simpler method fixes it
- ending image: the finished index sits in order, and the child feels wiser

Narrative instruments:
---
- Humor: a comic card mix-up
- Lesson Learned: label things early, keep a calm system
- Twist: the feared "important index" is not a test after all
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
from typing import Callable, Optional

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mixup(world: World) -> list[str]:
    out: list[str] = []
    kid = world.facts["kid"]
    stack = world.facts["index_stack"]
    if kid.memes["worry"] < THRESHOLD:
        return out
    if stack.meters["mixed"] < THRESHOLD:
        sig = ("mixup", stack.id)
        if sig not in world.fired:
            world.fired.add(sig)
            stack.meters["mixed"] += 1
            out.append("The index cards ended up in a funny little pile.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    kid = world.facts["kid"]
    if kid.memes["focus"] < THRESHOLD:
        return out
    sig = ("calm", kid.id)
    if sig in world.fired:
        return out
    if world.facts["index_stack"].meters["sorted"] >= THRESHOLD:
        world.fired.add(sig)
        kid.memes["relief"] += 1
        out.append("The room felt easier once everything had a label.")
    return out


CAUSAL_RULES = [
    Rule("mixup", "physical", _r_mixup),
    Rule("calm", "social", _r_calm),
]


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world: a child, an index, a funny mix-up, and a lesson learned."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


SETTINGS = {
    "library": Setting(place="the library corner", indoor=True, affords={"index"}),
    "kitchen-table": Setting(place="the kitchen table", indoor=True, affords={"index"}),
    "classroom": Setting(place="the classroom", indoor=True, affords={"index"}),
}

ACTIVITIES = {
    "index": Activity(
        id="index",
        verb="make an index",
        gerund="making an index",
        rush="shuffle the cards faster",
        mess="mixed",
        soil="mixed up",
        zone={"hands"},
        weather="",
        keyword="index",
        tags={"index", "paper", "library"},
    ),
}

PRIZES = {
    "report": Prize(
        label="report",
        phrase="a little report about the lymphatic system",
        type="report",
        region="hands",
        genders={"girl", "boy"},
    ),
    "cards": Prize(
        label="cards",
        phrase="a neat stack of index cards",
        type="cards",
        region="hands",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="tabs",
        label="color tabs",
        covers={"hands"},
        guards={"mixed"},
        prep="add color tabs first",
        tail="finished the cards with color tabs",
        plural=True,
    ),
    Gear(
        id="labels",
        label="sticky labels",
        covers={"hands"},
        guards={"mixed"},
        prep="use sticky labels before sorting",
        tail="kept the cards neat with sticky labels",
        plural=True,
    ),
]

NAMES = ["Mina", "Owen", "Sofia", "Theo", "Lila", "Ben", "Nora", "Eli"]
TRAITS = ["curious", "careful", "bright", "earnest", "playful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                if prize_at_risk(ACTIVITIES[act_id], PRIZES[prize_id]) and select_gear(ACTIVITIES[act_id], PRIZES[prize_id]):
                    out.append((place, act_id, prize_id))
    return out


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} would not realistically scramble {prize.label} in a way that our simple fix can solve.)"


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def make_world(place: str, activity: Activity, prize: Prize, name: str, gender: str, parent: str, trait: str) -> World:
    world = World(SETTINGS[place])
    kid = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait, "thoughtful"]))
    grown = world.add(Entity(id="parent", kind="character", type=parent, label="the parent"))
    index_stack = world.add(Entity(id="index_stack", type="cards", label="index cards", plural=True, owner=kid.id, caretaker=grown.id))
    report = world.add(Entity(id="report", type="report", label="report", phrase=prize.phrase, owner=kid.id, caretaker=grown.id))
    if prize.label == "cards":
        prize_ent = index_stack
    else:
        prize_ent = report

    world.facts.update(kid=kid, parent=grown, index_stack=index_stack, report=report, prize=prize_ent, activity=activity, gear=None)
    world.say(f"{kid.id} was a little {trait} {gender} who liked quiet tasks and tidy corners.")
    world.say(f"{kid.pronoun().capitalize()} was working on {report.phrase} for school, and the most important part was the index.")
    world.say(f"The {place} smelled faintly like paper and pencil shavings.")
    return world


def predict_mix(world: World, kid: Entity, activity: Activity) -> dict:
    sim = world.copy()
    sim.facts["kid"].memes["worry"] += 1
    propagate(sim, narrate=False)
    return {"mixed": sim.facts["index_stack"].meters["mixed"] >= THRESHOLD}


def tell(world: World, activity: Activity) -> None:
    kid = world.facts["kid"]
    parent = world.facts["parent"]
    stack = world.facts["index_stack"]
    report = world.facts["report"]

    kid.memes["focus"] += 1
    world.para()
    world.say(f"One afternoon, {kid.id} wanted to {activity.verb} for {report.phrase}.")
    world.say(f"{kid.pronoun().capitalize()} spread the cards out, trying to keep the names in order.")

    world.para()
    kid.memes["worry"] += 1
    world.say(f"Then a mug of tea tipped a little, and the cards slipped into a silly pile.")
    propagate(world, narrate=True)
    world.say(f"{kid.id} blinked at the mess and gave a nervous laugh.")

    world.para()
    world.say(f'The parent peeked over and said, "Well, that is one enthusiastic index."')
    world.say(f"{kid.id} laughed too, because the cards looked like a tiny paper parade.")

    world.para()
    gear_def = select_gear(activity, PRIZES["cards"])
    if gear_def is None:
        raise StoryError("No reasonable fix exists for the requested story.")
    if predict_mix(world, kid, activity)["mixed"]:
        gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, protective=True, plural=gear_def.plural))
        gear.worn_by = kid.id
        world.facts["gear"] = gear
        world.say(f'The parent pointed to the colors and said, "How about we {gear_def.prep}?"')
        kid.memes["focus"] += 1
        world.say(f"{kid.id} nodded, lined up the pages by topic, and used the tabs to sort the cards again.")
        stack.meters["sorted"] += 1
        kid.memes["relief"] += 1
        kid.memes["humor"] += 1
        world.say(f"This time the cards stayed neat, and the work went faster than anyone expected.")
        world.say(f"Only then did the twist appear: the index was for a homemade book, not a test.")
        world.say(f"{kid.id} had been worried for nothing serious, but the neat system still made the book better.")
        kid.memes["pride"] += 1
        world.say(f"By the end, the index sat in order, the tea was only a stain on the tablecloth, and {kid.id} felt proud of a small, smart fix.")
    else:
        raise StoryError("The chosen gear did not actually solve the problem.")


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), activity(A), prize(P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    return [
        "Write a gentle slice-of-life story about a child making an index for a report on the lymphatic system.",
        f"Tell a short story where {kid.id} gets a little flustered about an index, then finds a calmer way to finish the job.",
        "Write a story with a funny mix-up, a useful lesson, and a small twist near the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    parent = f["parent"]
    report = f["report"]
    gear = f.get("gear")
    return [
        QAItem(
            question=f"What was {kid.id} trying to make?",
            answer=f"{kid.id} was trying to make an index for {report.phrase}.",
        ),
        QAItem(
            question=f"Why did {kid.id} laugh at the cards?",
            answer=f"{kid.id} laughed because the index cards had slipped into a funny little pile, which looked like a tiny paper parade.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer="The child learned that labels and neat groups can save time, and that a calm system makes the work easier.",
        ),
    ] + (
        [
            QAItem(
                question=f"What helped {kid.id} sort the cards again?",
                answer=f"Color tabs helped {kid.id} sort the cards again and keep the index neat.",
            ),
            QAItem(
                question=f"What twist changed the feeling of the story?",
                answer=f"The twist was that the index was for a homemade book, not a test, so the worry was bigger than the situation really was.",
            ),
        ] if gear else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the lymphatic system?",
            answer="The lymphatic system is a part of the body that helps move fluid and supports the immune system.",
        ),
        QAItem(
            question="What is an index in a book?",
            answer="An index is a list of topics and page numbers that helps a reader find information quickly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", activity="index", prize="report", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="kitchen-table", activity="index", prize="cards", name="Owen", gender="boy", parent="father", trait="careful"),
    StoryParams(place="classroom", activity="index", prize="report", name="Nora", gender="girl", parent="mother", trait="patient"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
    tell(world, ACTIVITIES[params.activity])
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:\n")
        for p, a, r in vals:
            print(f"  {p:12} {a:8} {r:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
