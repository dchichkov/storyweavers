#!/usr/bin/env python3
"""
A small slice-of-life story world about a pencil, a good procedure, and the
gentle social turn from keeping to sharing.

Seed-inspired premise:
- A child wants to use a favorite pencil.
- Someone else needs it, or the room needs a careful procedure.
- A small piece of foreshadowing hints that sharing will make the task go well.
- The ending proves the procedure worked and the pencil was shared kindly.

The world is intentionally modest and concrete:
- a child
- a helper or classmate
- a pencil
- a task that benefits from a good procedure
- a soft social adjustment from possessive to cooperative
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
# Physical and emotional scales
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    risk_key: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    owner_only: bool = False


@dataclass
class ShareGear:
    id: str
    label: str
    prep: str
    tail: str


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "classroom": Setting(place="the classroom", affords={"math", "drawing", "list"}),
    "library_table": Setting(place="the library table", affords={"drawing", "list"}),
    "kitchen_table": Setting(place="the kitchen table", affords={"list"}),
}

ACTIVITIES = {
    "drawing": Activity(
        id="drawing",
        verb="draw a picture",
        gerund="drawing pictures",
        risk="smudges",
        risk_key="smudged",
        zone={"paper", "hands"},
        keyword="drawing",
        tags={"art", "pencil"},
    ),
    "math": Activity(
        id="math",
        verb="finish the math page",
        gerund="working through numbers",
        risk="mistakes",
        risk_key="careless",
        zone={"paper", "hands"},
        keyword="math",
        tags={"math", "pencil"},
    ),
    "list": Activity(
        id="list",
        verb="make a list",
        gerund="making careful lists",
        risk="tears",
        risk_key="creased",
        zone={"paper", "hands"},
        keyword="list",
        tags={"writing", "pencil"},
    ),
}

PRIZES = {
    "pencil": Prize(
        label="pencil",
        phrase="a good yellow pencil with a bright eraser",
        type="pencil",
        region="hands",
        owner_only=True,
    ),
    "notebook": Prize(
        label="notebook",
        phrase="a clean notebook with neat white pages",
        type="notebook",
        region="hands",
        owner_only=False,
    ),
}

SHARE_GEAR = [
    ShareGear(
        id="extra_pencil",
        label="an extra pencil",
        prep="take turns with an extra pencil",
        tail="shared the pencil until both pages were finished",
    ),
    ShareGear(
        id="sharpener",
        label="a small sharpener",
        prep="keep the point nice and neat",
        tail="used the sharpener when the tip grew dull",
    ),
]

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Eva", "June"],
    "boy": ["Owen", "Milo", "Theo", "Finn", "Leo"],
}
TYPES = {"girl", "boy"}
TRAITS = ["quiet", "kind", "curious", "careful", "cheerful"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def activity_needs_sharing(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_share_plan(activity: Activity, prize: Prize) -> Optional[ShareGear]:
    if prize.label == "pencil":
        return SHARE_GEAR[0]
    return SHARE_GEAR[1] if activity.id == "drawing" else None


def predict_shared_success(world: World, activity: Activity, prize: Prize) -> bool:
    return activity_needs_sharing(activity, prize) and select_share_plan(activity, prize) is not None


def propagate(world: World) -> None:
    actor = world.facts.get("hero")
    item = world.facts.get("prize")
    if not actor or not item:
        return
    if actor.memes.get("sharing", 0) >= THRESHOLD:
        item.meters["used"] = item.meters.get("used", 0) + 1


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str,
    hero_type: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    friend = world.add(Entity(id="Friend", kind="character", type="child", label="the friend", meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the teacher", meters={}, memes={}))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))

    world.facts.update(hero=hero, friend=friend, parent=parent, prize=prize, activity=activity, setting=setting)

    # Act 1: setup and foreshadowing
    world.say(f"{hero_name} was a {trait} little {hero_type} who liked to do things the right way.")
    world.say(f"{hero_name} had {prize.phrase}, and {hero.pronoun('possessive')} favorite thing was how smooth it felt in {hero.pronoun('possessive')} hand.")
    world.say(f"At {setting.place}, there was a good procedure for {activity.gerund}: first share tools, then start quietly, then check the work.")

    # Foreshadowing
    world.para()
    world.say(f"{friend.label if friend.label else 'The friend'} watched the pencil with a hopeful look, because the page was long and the line of desks was already busy.")
    world.say(f"That small look was a hint: this would go best if {hero_name} remembered to share.")

    # Act 2: tension
    world.para()
    hero.memes["wanting_to_keep"] = 1
    world.say(f"{hero_name} wanted to {activity.verb} right away with {prize.label}, but {hero.pronoun('possessive')} fingers held it a little too tight.")
    if activity_needs_sharing(activity, prize_cfg):
        world.say(f"{parent.label} smiled and pointed to the good procedure on the board. \"We share first, so everyone can finish.\"")

    world.say(f"{friend.id} waited politely, which made the room feel extra still.")
    world.say(f"{hero_name} looked at the page, then at {prize.label}, and finally at the quiet line of work ahead.")

    # Act 3: turn and resolution
    world.para()
    plan = select_share_plan(activity, prize_cfg)
    if plan is None:
        raise StoryError("No reasonable sharing plan exists for this story.")
    hero.memes["sharing"] = 1
    propagate(world)
    world.say(f"Then {hero_name} nodded and chose the good procedure.")
    world.say(f"{hero_name} and {friend.id} {plan.prep}, and the pencil moved from one small hand to the other without a fuss.")
    world.say(f"Their page got better and better, because each person knew when to write and when to wait.")
    world.say(f"In the end, {hero_name} {plan.tail}, and the classroom felt calm and proud.")

    world.facts["plan"] = plan
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        'Write a short slice-of-life story for a young child about a pencil, a good procedure, and sharing.',
        f"Tell a gentle classroom story where {hero.id} wants to {activity.verb} with {prize.label} but learns to share.",
        f'Write a calm story that includes the words "pencil", "good", and "procedure" and ends with a happy shared outcome.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    plan = f["plan"]
    place = f["setting"].place

    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place}?",
            answer=f"{hero.id} wanted to {activity.verb} with {prize.label}, but the room had a good procedure for sharing first.",
        ),
        QAItem(
            question=f"Why was the small look from {friend.label if friend.label else 'the friend'} important?",
            answer="It foreshadowed that sharing would help the work go well, because the other child needed a turn too.",
        ),
        QAItem(
            question=f"What did {parent.label} remind everyone about?",
            answer=f"{parent.label} reminded them to follow the good procedure: share tools first, then begin carefully.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} finish the task?",
            answer=f"They shared {prize.label} and followed {plan.prep}, so the work stayed calm and finished nicely.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, {hero.id} was no longer keeping the pencil too tightly; {hero.id} was sharing it kindly instead.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pencil for?",
            answer="A pencil is used for writing or drawing, and its point can make marks on paper.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use something too, or to take turns with it.",
        ),
        QAItem(
            question="What is a procedure?",
            answer="A procedure is a set of steps you follow in order so a job gets done well.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small hint about what may happen later.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Shared tools and simple story logic.
needs_sharing(A,P) :- activity(A), prize(P), zone(A,R), region(P,R).

good_procedure(A,P) :- needs_sharing(A,P), can_share(P).

resolved(A,P) :- good_procedure(A,P), sharing_chosen(A,P).

story_ok(P) :- prize(P), can_share(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        lines.append(asp.fact("can_share", pid))
    for g in SHARE_GEAR:
        lines.append(asp.fact("share_gear", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if activity_needs_sharing(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show needs_sharing/2."))
    return sorted(set(asp.atoms(model, "needs_sharing")))


def asp_verify() -> int:
    py = set((a, p) for _, a, p in valid_combos())
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


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a pencil, a good procedure, and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=sorted(TYPES))
    ap.add_argument("--parent", choices=["mother", "father", "teacher"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(TYPES))
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or "teacher"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
    StoryParams(place="classroom", activity="drawing", prize="pencil", name="Mina", gender="girl", parent="teacher", trait="careful"),
    StoryParams(place="library_table", activity="list", prize="pencil", name="Owen", gender="boy", parent="teacher", trait="kind"),
    StoryParams(place="classroom", activity="math", prize="pencil", name="Nora", gender="girl", parent="teacher", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show needs_sharing/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show needs_sharing/2."))
        combos = sorted(set(asp.atoms(model, "needs_sharing")))
        print(f"{len(combos)} sharing-needed combos:")
        for combo in combos:
            print(combo)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
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
