#!/usr/bin/env python3
"""
storyworlds/worlds/approval_warehouse_aisle_reconciliation_moral_value_friendship.py
====================================================================================

A standalone story world about two warehouse helpers, a mistaken thumbs-up, and a
comedy of friendship, moral value, reconciliation, and approval in a warehouse aisle.

Seed premise:
- In a warehouse aisle, two friends argue over whether a wobbly shelf display
  should be left as-is or fixed.
- One friend wants approval from a supervisor; the other cares about doing the
  morally right thing.
- Their bickering makes the task sillier, not harsher.
- A small turn shows that a good apology and a careful fix can restore
  friendship, bring reconciliation, and win honest approval.

The world model uses typed entities with physical meters and emotional memes.
Prose is generated from world state, not from a frozen template with swapped names.
A small forward chain updates the state, and the renderer reads those updates back
into child-facing story text.

This script is self-contained and uses only the standard library plus the shared
results containers. ASP is imported lazily only in the ASP helpers.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the warehouse aisle"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    region: str
    owner_role: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    gives: set[str]
    covers: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("fixed"):
        return out
    if world.facts.get("apology") and world.facts.get("care"):
        sig = ("repair",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["fixed"] = True
            for e in world.characters():
                if e.role in {"friend_a", "friend_b"}:
                    e.memes["friendship"] += 1
                    e.memes["reconciliation"] += 1
                    e.memes["approval"] += 1
                    e.memes["conflict"] = 0.0
            out.append("__repair__")
    return out


CAUSAL_RULES = [Rule("repair", "social", _r_repair)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_pair(activity: Activity, goal: Goal) -> bool:
    return goal.region in activity.zone


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for goal_id, goal in GOALS.items():
                if valid_pair(act, goal):
                    combos.append((place, goal_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    goal: str
    friend_a: str
    friend_a_type: str
    friend_b: str
    friend_b_type: str
    supervisor: str
    supervisor_type: str
    seed: Optional[int] = None


SETTINGS = {
    "aisle": Setting(place="the warehouse aisle", affords={"stack", "sort", "reach"}),
}

ACTIVITIES = {
    "stack": Activity(
        id="stack",
        verb="restack the boxes",
        gerund="restacking the boxes",
        mess="wobbly",
        zone={"shelf"},
        keyword="approval",
        tags={"approval", "comedy", "warehouse"},
    ),
    "sort": Activity(
        id="sort",
        verb="sort the labels",
        gerund="sorting the labels",
        mess="mixed-up",
        zone={"table"},
        keyword="approval",
        tags={"approval", "comedy", "warehouse"},
    ),
    "reach": Activity(
        id="reach",
        verb="reach the top crate",
        gerund="reaching the top crate",
        mess="tippy",
        zone={"shelf"},
        keyword="approval",
        tags={"approval", "comedy", "warehouse"},
    ),
}

GOALS = {
    "shelf": Goal(
        id="shelf",
        label="the shelf display",
        phrase="the shelf display",
        region="shelf",
        owner_role="friend_b",
        tags={"friendship", "moral_value", "reconciliation"},
    ),
    "crate": Goal(
        id="crate",
        label="the top crate",
        phrase="the top crate",
        region="shelf",
        owner_role="friend_a",
        tags={"friendship", "moral_value", "reconciliation"},
    ),
}

AIDS = {
    "brace": Aid("brace", "brace", "a brace and some tape", {"steady"}, {"shelf"}),
    "labeler": Aid("labeler", "labeler", "a labeler and a marker", {"organized"}, {"table"}),
}

GIRL_NAMES = ["Mina", "Tess", "Ivy", "Nia", "Lola", "Ada"]
BOY_NAMES = ["Owen", "Theo", "Leo", "Milo", "Finn", "Jude"]


def explain_rejection(activity: Activity, goal: Goal) -> str:
    return (
        f"(No story: {activity.gerund} does not actually put {goal.phrase} at risk "
        f"in a way this little warehouse world can reconcile. Choose a matching goal.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedy story world set in a warehouse aisle about approval, "
                    "friendship, moral value, and reconciliation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name-a")
    ap.add_argument("--type-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--type-b", choices=["girl", "boy"])
    ap.add_argument("--supervisor")
    ap.add_argument("--supervisor-type", choices=["woman", "man"], default="woman")
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
              and (args.goal is None or c[1] == args.goal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, goal = rng.choice(sorted(combos))
    activity = args.activity or rng.choice(sorted(SETTINGS[place].affords))
    if activity not in SETTINGS[place].affords:
        raise StoryError(explain_rejection(ACTIVITIES[activity], GOALS[goal]))
    name_a = args.name_a or rng.choice(GIRL_NAMES + BOY_NAMES)
    type_a = args.type_a or rng.choice(["girl", "boy"])
    name_b = args.name_b or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name_a])
    type_b = args.type_b or rng.choice(["girl", "boy"])
    supervisor = args.supervisor or rng.choice(["Ms. Park", "Mr. Reed", "Ms. Cole"])
    return StoryParams(
        place=place,
        activity=activity,
        goal=goal,
        friend_a=name_a,
        friend_a_type=type_a,
        friend_b=name_b,
        friend_b_type=type_b,
        supervisor=supervisor,
        supervisor_type=args.supervisor_type,
    )


def _setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity, Goal, Activity, Aid]:
    a = world.add(Entity(id="a", kind="character", type=params.friend_a_type, label=params.friend_a, role="friend_a"))
    b = world.add(Entity(id="b", kind="character", type=params.friend_b_type, label=params.friend_b, role="friend_b"))
    s = world.add(Entity(id="supervisor", kind="character", type=params.supervisor_type, label=params.supervisor, role="supervisor"))
    goal = GOALS[params.goal]
    act = ACTIVITIES[params.activity]
    aid = AIDS["brace" if goal.region == "shelf" else "labeler"]
    world.add(Entity(id="goal", type="thing", label=goal.label, attrs={"region": goal.region}))
    world.add(Entity(id="aid", type="thing", label=aid.label))
    world.facts.update(apology=False, care=False, fixed=False)
    return a, b, s, goal, act, aid


def tell(world: World, a: Entity, b: Entity, s: Entity, goal: Goal, act: Activity, aid: Aid) -> None:
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(
        f"In {world.setting.place}, {a.label} and {b.label} were working along the {world.setting.place} aisle "
        f"when their job turned into a comedy of one very wobbly {goal.label}."
    )
    world.say(
        f"{a.label} wanted {a.pronoun('possessive')} {goal.label} to look perfect and waited for approval, "
        f"while {b.label} cared about the moral value of fixing it right away."
    )
    world.para()
    world.say(
        f"They started {act.gerund}, but the silly little plan made the stack wobble and lean like it was telling a joke."
    )
    world.say(
        f'"If we leave it," said {b.label}, "someone could get a surprise." '
        f'"If we fix it," said {a.label}, "maybe we get approval."'
    )
    world.say(
        f"That made {s.label_word if s.label else s.label} pause, because {s.label} had a face that meant business."
    )
    world.para()
    world.say(
        f"{b.label} sighed, then admitted the moral value of doing the careful thing first."
    )
    world.say(
        f"{a.label} laughed at how serious everyone had become over one shelf, then said sorry."
    )
    world.facts["apology"] = True
    world.facts["care"] = True
    propagate(world, narrate=False)
    a.meters["steady"] += 1
    b.meters["steady"] += 1
    world.say(
        f"Together they used {aid.phrase}, straightened {goal.phrase}, and lined the boxes up so neatly that the shelf stopped wobbling."
    )
    world.say(
        f"{s.label} gave them honest approval and a thumbs-up so enthusiastic it nearly needed its own forklift."
    )
    world.say(
        f"By the end, {a.label} and {b.label} were laughing again, and their friendship fit the aisle better than any box ever could."
    )
    world.facts.update(
        a=a, b=b, supervisor=s, goal=goal, activity=act, aid=aid,
        approved=True, reconciled=True
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.activity not in ACTIVITIES or params.goal not in GOALS:
        raise StoryError("(Invalid params for this world.)")
    if (params.place, params.goal) not in valid_combos():
        raise StoryError(explain_rejection(ACTIVITIES[params.activity], GOALS[params.goal]))
    world = World(SETTINGS[params.place])
    a, b, s, goal, act, aid = _setup(world, params)
    tell(world, a, b, s, goal, act, aid)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, goal, act = f["a"], f["b"], f["goal"], f["activity"]
    return [
        f'Write a funny story for a young child about {a.label} and {b.label} in a {world.setting.place} aisle, using the word "approval".',
        f"Tell a comedy about two warehouse friends who argue over {goal.phrase}, then reconcile and get approval.",
        f"Write a gentle friendship story set in a warehouse aisle where doing the moral thing matters more than looking right.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, s, goal, act, aid = f["a"], f["b"], f["supervisor"], f["goal"], f["activity"], f["aid"]
    return [
        QAItem(
            question=f"Why did {a.label} care about approval in the warehouse aisle?",
            answer=f"{a.label} wanted the job to look neat so the supervisor would approve it. That made {a.label} focus on appearance at first, but it also gave the friends a silly reason to argue.",
        ),
        QAItem(
            question=f"Why did {b.label} want to fix {goal.phrase} right away?",
            answer=f"{b.label} cared about the moral value of doing the safe, careful thing. That choice kept the shelf from wobbling and helped the friends reconcile.",
        ),
        QAItem(
            question=f"What changed after {a.label} said sorry to {b.label}?",
            answer=f"The apology turned the argument into reconciliation. After that, they worked together again and their friendship felt strong and happy.",
        ),
        QAItem(
            question=f"How did {s.label} respond when the shelf was fixed?",
            answer=f"{s.label} gave honest approval with a big thumbs-up. The approval showed that careful work and friendship had both gone in the right direction.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is approval?",
            answer="Approval is a kind of okay signal, like a grown-up saying a job was done well and safely.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means friends stop fighting and make peace again. They listen, apologize, and start being kind to each other.",
        ),
        QAItem(
            question="What is moral value?",
            answer="Moral value is the idea of choosing what is right and fair, even if it is not the flashiest choice.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and stay kind even after a small argument.",
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="aisle",
        activity="stack",
        goal="shelf",
        friend_a="Mina",
        friend_a_type="girl",
        friend_b="Owen",
        friend_b_type="boy",
        supervisor="Ms. Park",
        supervisor_type="woman",
    ),
    StoryParams(
        place="aisle",
        activity="reach",
        goal="crate",
        friend_a="Theo",
        friend_a_type="boy",
        friend_b="Ivy",
        friend_b_type="girl",
        supervisor="Mr. Reed",
        supervisor_type="man",
    ),
]


ASP_RULES = r"""
valid(P,A,G) :- place(P), activity(A), goal(G), affords(P,A), risk(A,G).
reconcile :- apology, care.
approved :- reconcile.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for gid, g in GOALS.items():
        for act_id, act in ACTIVITIES.items():
            if valid_pair(act, g):
                lines.append(asp.fact("risk", act_id, gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH: ASP and Python valid-combos differ.")
            return 1
        sample = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
        print("OK: ASP parity, generation smoke test, and emit smoke test passed.")
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"VERIFY FAILED: {exc}")
        return 1


def build_sample(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, activity, goal) combos:\n")
        for row in combos:
            print("  ", row)
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
            header = f"### {p.friend_a} and {p.friend_b} in the warehouse aisle"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.goal is None or c[1] == args.goal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, goal = rng.choice(sorted(combos))
    activity = args.activity or rng.choice(sorted(SETTINGS[place].affords))
    if (place, goal) not in valid_combos():
        raise StoryError(explain_rejection(ACTIVITIES[activity], GOALS[goal]))
    name_a = args.name_a or rng.choice(GIRL_NAMES + BOY_NAMES)
    type_a = args.type_a or rng.choice(["girl", "boy"])
    name_b = args.name_b or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name_a])
    type_b = args.type_b or rng.choice(["girl", "boy"])
    supervisor = args.supervisor or rng.choice(["Ms. Park", "Mr. Reed", "Ms. Cole"])
    return StoryParams(
        place=place,
        activity=activity,
        goal=goal,
        friend_a=name_a,
        friend_a_type=type_a,
        friend_b=name_b,
        friend_b_type=type_b,
        supervisor=supervisor,
        supervisor_type=args.supervisor_type,
    )


if __name__ == "__main__":
    main()
