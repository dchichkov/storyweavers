#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mucus_slurp_teamwork_moral_value_rhyming_story.py
=================================================================================================

A small, standalone storyworld about a sniffly day, a slippery slurp, and a
teamwork fix with a gentle moral.

Premise:
- A child wants to slurp a bowl of soup while having lots of mucus from a cold.
- The adult worries the slurp will make a mess and make more work.
- A helper joins in, and together they solve the problem kindly.

The story is written in a light rhyming-story style, with simple child-facing
language and a state-driven turn from mess to teamwork.

Seed words:
- mucus
- slurp

Features:
- Teamwork
- Moral Value

This file is self-contained except for the shared result containers in
``storyworlds/results.py`` and the optional ASP helper in ``storyworlds/asp.py``.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mucus": 0.0, "mess": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "teamwork": 0.0, "moral_value": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess_kind: str
    zone: set[str]
    keyword: str
    rhyme: str


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class HelperPlan:
    label: str
    tool: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"slurp"}),
    "table": Setting(place="the little table", affords={"slurp"}),
    "bedroom": Setting(place="the bedroom", affords={"slurp"}),
}

ACTIVITIES = {
    "slurp": Activity(
        id="slurp",
        verb="slurp the soup",
        gerund="slurping soup",
        rush="rush for the spoon",
        mess_kind="mucus",
        zone={"mouth", "chest"},
        keyword="slurp",
        rhyme="slurp and chirp",
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean blue shirt", region="chest"),
    "pajamas": Prize(label="pajamas", phrase="fresh striped pajamas", region="chest", plural=True),
}

HELPERS = {
    "towel": HelperPlan(
        label="a soft towel",
        tool="towel",
        prep="set a soft towel under the bowl",
        tail="set the towel under the bowl and laughed",
    ),
    "napkin": HelperPlan(
        label="a neat napkin",
        tool="napkin",
        prep="place a neat napkin by the bowl",
        tail="placed the napkin by the bowl and smiled",
    ),
}

NAMES = ["Milo", "Nina", "Toby", "Pia", "Benny", "Luna", "Owen", "Ruby"]
TRAITS = ["gentle", "cheerful", "curious", "brave", "playful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rhyming_color(activity: Activity) -> str:
    return {
        "slurp": "A sip and a slip can make a messy blip, but teamwork can keep the day in trim and tip.",
    }.get(activity.id, "The day can start with a mess, then end with success.")


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def choose_helper(activity: Activity, prize: Prize) -> Optional[HelperPlan]:
    if activity.id == "slurp" and prize.region in {"chest"}:
        return HELPERS["towel"]
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} would not really threaten {prize.label} here, "
        f"so there is no honest worry, no teamwork turn, and no moral lesson to show.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def propagate(world: World) -> None:
    for actor in world.characters():
        if actor.meters["mucus"] >= THRESHOLD and actor.meters["mess"] < THRESHOLD:
            sig = ("mess", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.meters["mess"] += 1
                actor.memes["worry"] += 1
                world.say(f"A drippy bit of mucus made {actor.id}'s day feel all slippery.")
        if actor.meters["mess"] >= THRESHOLD and actor.memes["teamwork"] >= THRESHOLD:
            sig = ("fix", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.meters["mess"] = 0.0
                actor.meters["clean"] += 1
                actor.memes["joy"] += 1
                actor.memes["worry"] = 0.0
                world.say(f"With teamwork, the sticky spot got cleaned right up.")


def do_slurp(world: World, hero: Entity, activity: Activity) -> None:
    world.zone = set(activity.zone)
    hero.meters["mucus"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, because {activity.rhyme} felt fun.")
    propagate(world)


def warn(world: World, parent: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f'"Careful," {parent.pronoun("subject").capitalize()} said, '
        f'"your {prize.label} could get messy if you {activity.verb} too fast."'
    )
    hero.memes["worry"] += 1


def teamwork_offer(world: World, helper: Entity, hero: Entity, plan: HelperPlan) -> None:
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"Then {helper.id} came close and said, "
        f'"Let\'s {plan.prep} and share the care."'
    )


def accept_and_finish(world: World, hero: Entity, parent: Entity, helper: Entity,
                      activity: Activity, prize: Entity, plan: HelperPlan) -> None:
    hero.memes["joy"] += 1
    hero.memes["moral_value"] += 1
    parent.memes["moral_value"] += 1
    helper.memes["moral_value"] += 1
    world.say(
        f"{hero.id} smiled, then {plan.tail}. "
        f"{hero.id} could {activity.verb}, and {prize.label} stayed neat and bright."
    )
    world.say(
        f"The little room felt warm and fine, because sharing the work was the kindest line."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, helper_key: str,
         hero_name: str = "Milo", hero_type: str = "boy",
         parent_type: str = "mother", trait: str = "gentle") -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    helper = world.add(Entity(id="Helper", kind="character", type="sister", label="helper"))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))

    world.say(f"{hero.id} was a {trait} little {hero.type} in {setting.place}.")
    world.say(
        f"{hero.id} loved {activity.gerund}, and the day had a bouncy, rhymy way."
    )
    world.say(f"{hero.id} wore {prize.phrase} and felt smart and bright.")

    world.para()
    world.say(f"One day at {setting.place}, {hero.id} reached for a bowl.")
    do_slurp(world, hero, activity)
    warn(world, parent, hero, prize, activity)

    world.para()
    helper_plan = choose_helper(activity, prize)
    if helper_plan is None:
        raise StoryError(explain_rejection(activity, prize))
    teamwork_offer(world, helper, hero, helper_plan)
    accept_and_finish(world, hero, parent, helper, activity, prize, helper_plan)

    world.facts = {
        "hero": hero,
        "parent": parent,
        "helper": helper,
        "prize": prize,
        "activity": activity,
        "setting": setting,
        "helper_plan": helper_plan,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short rhyming story for a child about "{act.keyword}" and teamwork.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but a grown-up worries about {prize.label}.",
        f'Write a child-facing story that includes the words "mucus" and "{act.keyword}" and ends kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    helper = f["helper"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{hero.id} wanted to {act.verb} while feeling sniffly and excited.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about {prize.label}?",
            answer=f"{parent.pronoun('subject').capitalize()} worried because {act.verb} could make {prize.label} messy.",
        ),
        QAItem(
            question=f"How did {helper.id} help the day go better?",
            answer=f"{helper.id} joined in, offered a simple plan, and helped {hero.id} keep things tidy.",
        ),
        QAItem(
            question="What moral value was shown at the end?",
            answer="The story showed kindness and teamwork, because everyone shared the work and helped each other.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mucus?",
            answer="Mucus is a sticky liquid your body makes, often in your nose, to help trap dust and germs.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to do something well.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good rule for how to treat people, like being kind, honest, or helpful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
has_fix(A, P) :- helper_ok(A, P).
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
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    lines.append(asp.fact("helper_ok", "slurp", "shirt"))
    lines.append(asp.fact("helper_ok", "slurp", "pajamas"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and choose_helper(act, prize) is not None:
                    combos.append((place, act_id, prize_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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


# ---------------------------------------------------------------------------
# Params, generation, emit, main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming teamwork storyworld about mucus and a slurp.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=list(HELPERS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.activity is not None and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.prize is not None and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")

    combos = []
    for place, act_id, prize_id in valid_combos():
        if args.place and place != args.place:
            continue
        if args.activity and act_id != args.activity:
            continue
        if args.prize and prize_id != args.prize:
            continue
        combos.append((place, act_id, prize_id))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    helper = args.helper or "towel"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name,
                       gender=gender, parent=parent, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.helper,
        hero_name=params.name,
        hero_type=params.gender,
        parent_type=params.parent,
        trait=params.trait,
    )
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
        lines.append(
            f"  {e.id:8} ({e.type:8}) meters={dict((k, v) for k, v in e.meters.items() if v)} "
            f"memes={dict((k, v) for k, v in e.memes.items() if v)}"
        )
    lines.append(f"  setting={world.setting.place}")
    return "\n".join(lines)


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
    StoryParams(place="kitchen", activity="slurp", prize="shirt", name="Milo", gender="boy", parent="mother", helper="towel", trait="gentle"),
    StoryParams(place="table", activity="slurp", prize="pajamas", name="Nina", gender="girl", parent="father", helper="towel", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
