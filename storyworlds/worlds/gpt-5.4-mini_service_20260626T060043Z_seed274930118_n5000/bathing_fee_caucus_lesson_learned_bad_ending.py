#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bathing_fee_caucus_lesson_learned_bad_ending.py
===============================================================================================================

A bedtime-story-style storyworld about bathing, a fee, and a caucus.

Premise:
- A small child wants a soothing bath before bed.
- The local bathhouse asks for a fee.
- A tiny neighborhood caucus decides who may use the warm water.
- Kindness matters, but the ending is a bad one: the child learns a lesson after
  a missed bath and a quiet, sticky bedtime.

The story is intentionally constrained and state-driven:
- physical meters track water, soap, coins, and warmth
- emotional memes track worry, kindness, disappointment, and lesson learned
- the ending is "bad" in that the goal is not fully achieved, but the child
  still learns something gentle and clear
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    soothe: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FeeItem:
    id: str
    label: str
    phrase: str
    amount: int
    currency: str = "coin"


@dataclass
class CaucusRule:
    id: str
    label: str
    kindness_needed: int
    fee_needed: int
    allows_bath: bool


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.state: dict[str, bool] = {"paid": False, "allowed": False, "bathed": False, "lesson": False}

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.state = dict(self.state)
        return c


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    fee_item: str
    caucus: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "bathhouse": Setting(place="the bathhouse", indoor=True, affords={"bathing"}),
    "home": Setting(place="the little bathroom", indoor=True, affords={"bathing"}),
}

ACTIVITIES = {
    "bathing": Activity(
        id="bathing",
        verb="take a bath",
        gerund="bathing in warm water",
        risk="the water could get cold",
        soothe="the warm water would make the sleepiness gentle",
        mess="wet",
        zone={"hands", "feet", "torso"},
        keyword="bathing",
        tags={"bathing", "wet", "soap"},
    ),
}

FEE_ITEMS = {
    "coin": FeeItem(
        id="coin",
        label="a fee",
        phrase="one small coin for the warm tub",
        amount=1,
        currency="coin",
    ),
    "ticket": FeeItem(
        id="ticket",
        label="a fee slip",
        phrase="a tiny fee slip stamped by the desk",
        amount=1,
        currency="ticket",
    ),
}

CAUCUSES = {
    "neighbors": CaucusRule(
        id="neighbors",
        label="the neighbors' caucus",
        kindness_needed=1,
        fee_needed=1,
        allows_bath=True,
    ),
    "towel_club": CaucusRule(
        id="towel_club",
        label="the towel caucus",
        kindness_needed=2,
        fee_needed=1,
        allows_bath=True,
    ),
}

CHILD_NAMES = ["Mina", "Nora", "Eli", "Jun", "Lina", "Theo"]
TRAITS = ["sleepy", "gentle", "curious", "soft-spoken", "kind"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def _clean_world(world: World) -> None:
    child = world.get("child")
    child.meters["wet"] = 0
    child.meters["soap"] = 0
    child.memes["calm"] = 1


def _pay_fee(world: World) -> None:
    child = world.get("child")
    desk = world.get("desk")
    fee = world.facts["fee_item"]
    if child.meters["coins"] < fee.amount:
        world.state["paid"] = False
        return
    child.meters["coins"] -= fee.amount
    desk.meters["coins"] += fee.amount
    world.state["paid"] = True
    world.say(f"{child.id} set {fee.amount} coin on the desk and paid the little fee.")


def _caucus_decision(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    caucus = world.facts["caucus"]
    fee_ok = world.state["paid"]
    kindness_ok = child.memes.get("kindness", 0) >= caucus.kindness_needed
    if fee_ok and kindness_ok:
        world.state["allowed"] = True
        world.say(
            f"The {caucus.label} nodded kindly, and {parent.label} said the warm bath could begin."
        )
    else:
        world.state["allowed"] = False
        reason = "the fee was missing" if not fee_ok else "not enough kindness was shown"
        world.say(f"The {caucus.label} whispered together, and their answer was no, because {reason}.")


def _bath(world: World) -> None:
    child = world.get("child")
    if not world.state["allowed"]:
        return
    child.meters["wet"] += 1
    child.meters["soap"] += 1
    child.memes["contentment"] = child.memes.get("contentment", 0) + 1
    world.state["bathed"] = True
    world.say(
        f"{child.id} slipped into the warm water, and the bath felt like a soft blanket around {child.pronoun('object')}."
    )


def _bad_ending(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    if world.state["bathed"]:
        return
    child.memes["disappointment"] = child.memes.get("disappointment", 0) + 1
    child.memes["lesson_learned"] = 1
    world.state["lesson"] = True
    world.say(
        f"So {child.id} went to bed unbathed, and {parent.label} tucked {child.pronoun('object')} in with a gentle reminder to bring the fee next time."
    )
    world.say(
        f"{child.id} learned that kindness helps, but promises and little fees must be ready before the warm water can wait."
    )


def tell(world: World) -> World:
    child = world.add(Entity(id="child", kind="character", type=world.facts["gender"], meters={"coins": 0}, memes={"kindness": 1}))
    parent = world.add(Entity(id="parent", kind="character", type=world.facts["parent"], label=world.facts["parent_label"]))
    desk = world.add(Entity(id="desk", type="thing", label="the desk"))
    towel = world.add(Entity(id="towel", type="thing", label="the towel", owner="child"))
    del towel  # story keeps it implicit

    child.meters["coins"] = 0 if world.facts["fee_item"].id == "ticket" else 0
    child.memes["kindness"] = 1 if world.facts["caucus"].id == "neighbors" else 2
    child.memes["worry"] = 1

    world.say(
        f"{child.id.capitalize()} was a {world.facts['trait']} little {child.type} who liked quiet bedtime baths."
    )
    world.say(
        f"One evening, {child.id} wanted {world.facts['activity'].gerund}, because {world.facts['activity'].soothe}."
    )
    world.para()
    world.say(
        f"But the bathhouse asked for {world.facts['fee_item'].phrase}, and the {world.facts['caucus'].label} would not open the tub without it."
    )
    world.say(
        f"{parent.label} explained that a good plan needed the fee, the kindness, and the right time."
    )
    _pay_fee(world)
    _caucus_decision(world)
    _bath(world)
    world.para()
    _bad_ending(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.

paid(C) :- has_fee(C), coins(C, N), fee_amount(F), N >= F.
kind(C) :- kindness(C, K), need_kind(N), K >= N.
allowed(C) :- caucus_ok, paid(C), kind(C).
valid_story(Place, Activity, Fee, Caucus) :- place(Place), activity(Activity), fee(Fee), caucus(Caucus), allowed(child).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("activity_keyword", aid, a.keyword))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for fid, f in FEE_ITEMS.items():
        lines.append(asp.fact("fee", fid))
        lines.append(asp.fact("fee_amount", f.amount))
    for cid, c in CAUCUSES.items():
        lines.append(asp.fact("caucus", cid))
        lines.append(asp.fact("need_kind", c.kindness_needed))
        if c.allows_bath:
            lines.append(asp.fact("caucus_ok"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(p, a, f, c) for p in SETTINGS for a in ACTIVITIES for f in FEE_ITEMS for c in CAUCUSES}
    got = set(asp_valid_stories())
    if got == expected:
        print(f"OK: ASP gate matches expected story space ({len(got)} combos).")
        return 0
    print("MISMATCH between ASP and expected story space:")
    print(" only in asp:", sorted(got - expected))
    print(" only in python:", sorted(expected - got))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story about a child named {f["name"]} who wants {f["activity"].gerund} but must handle a fee and a caucus.',
        f"Tell a gentle story where kindness matters, the bathhouse asks for {f['fee_item'].phrase}, and the ending is a lesson learned with a bad ending.",
        f'Write a short child-friendly story that includes the words "{f["activity"].keyword}", "fee", and "caucus".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = world.get("child")
    parent = world.get("parent")
    caucus = f["caucus"]
    fee = f["fee_item"]
    activity = f["activity"]
    answers = [
        QAItem(
            question=f"Who wanted to {activity.verb} before bedtime?",
            answer=f"{child.id} wanted to {activity.verb} before bed because {activity.soothe}.",
        ),
        QAItem(
            question=f"What did the bathhouse ask for?",
            answer=f"The bathhouse asked for {fee.phrase}.",
        ),
        QAItem(
            question=f"What did the caucus decide?",
            answer=f"The {caucus.label} decided that the bath could only begin if the fee was ready and kindness was shown.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn at the end?",
            answer=f"{child.id} learned that kindness is good, but a fee must be ready before a plan can work.",
        ),
    ]
    if world.state["bathed"]:
        answers.append(
            QAItem(
                question="Did the child get the bath?",
                answer=f"Yes. {child.id} got the bath after the fee was paid and the caucus allowed it.",
            )
        )
    else:
        answers.append(
            QAItem(
                question="Did the child get the bath?",
                answer=f"No. {child.id} did not get the bath, so the ending stayed a bad one, even though the lesson was learned.",
            )
        )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fee?",
            answer="A fee is a small amount of money or something paid to use a service or join an activity.",
        ),
        QAItem(
            question="What is bathing?",
            answer="Bathing means washing your body in water, often in a tub or a bath.",
        ),
        QAItem(
            question="What is a caucus?",
            answer="A caucus is a small meeting where people talk together and make a choice.",
        ),
        QAItem(
            question="Why can kindness matter in a group?",
            answer="Kindness helps people listen, share, and make fair choices together.",
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"state={world.state}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about bathing, a fee, and a caucus.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--fee-item", choices=FEE_ITEMS)
    ap.add_argument("--caucus", choices=CAUCUSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    fee_item = args.fee_item or rng.choice(list(FEE_ITEMS))
    caucus = args.caucus or rng.choice(list(CAUCUSES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    if activity != "bathing":
        raise StoryError("This world only tells bathing stories.")
    if fee_item not in FEE_ITEMS or caucus not in CAUCUSES:
        raise StoryError("Invalid fee or caucus.")
    return StoryParams(place=place, activity=activity, fee_item=fee_item, caucus=caucus, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    fee = FEE_ITEMS[params.fee_item]
    caucus = CAUCUSES[params.caucus]
    world.facts = {
        "name": params.name,
        "gender": params.gender,
        "parent": params.parent,
        "parent_label": params.parent,
        "trait": params.trait,
        "activity": ACTIVITIES[params.activity],
        "fee_item": fee,
        "caucus": caucus,
    }
    # deterministic world context
    world.add(Entity(id="child", kind="character", type=params.gender, meters={"coins": 0}, memes={"kindness": 1}))
    world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    world.add(Entity(id="desk", type="thing", label="the desk", meters={"coins": 0}))
    # Let the child have just enough moral setup for the caucus to matter.
    sample_world = tell(world)
    return StorySample(
        params=params,
        story=sample_world.render(),
        prompts=generation_prompts(sample_world),
        story_qa=story_qa(sample_world),
        world_qa=world_knowledge_qa(sample_world),
        world=sample_world,
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for t in stories:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for fee_item in FEE_ITEMS:
                for caucus in CAUCUSES:
                    p = StoryParams(
                        place=place,
                        activity="bathing",
                        fee_item=fee_item,
                        caucus=caucus,
                        name="Mina",
                        gender="girl",
                        parent="mother",
                        trait="kind",
                    )
                    samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
