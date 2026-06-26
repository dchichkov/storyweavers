#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/flower_reconciliation_kindness_bad_ending_comedy.py
==============================================================================================================

A small storyworld about a flower, a kind apology, a silly reconciliation,
and a bad ending told with a comic tone.

Seed premise:
---
A child wants to take a flower to someone they love. A small argument pops up
because the flower is delicate and the plan is clumsy. Kind words calm the
moment, the characters make up, and the flower still ends up ruined in a funny
way.

World shape:
---
- One flower-centered outing.
- A tiny emotional conflict that can be resolved by kindness.
- A bad ending for the flower itself, but a reconciled ending for the people.
- Comedy comes from slapstick mishaps, not from cruelty.
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
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        masculine = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    has_wind: bool = False
    has_steps: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    fragile: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    guards: set[str]
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("bumps", 0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.owner != actor.id or not item.fragile:
                continue
            sig = ("drop", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["broken"] = item.meters.get("broken", 0) + 1
            item.meters["petal_loss"] = item.meters.get("petal_loss", 0) + 1
            out.append(f"{item.label.capitalize()} went floppy from the bump.")
    return out


def _r_apology(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("kindness", 0) < THRESHOLD:
            continue
        if actor.memes.get("hurt", 0) < THRESHOLD:
            continue
        sig = ("reconcile", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["reconciled"] = 1
        out.append("__reconcile__")
    return out


RULES = [_r_drop, _r_apology]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            res = rule(world)
            if res:
                changed = True
                for s in res:
                    if s != "__reconcile__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.fragile and prize.label == "flower" and activity.id in {"carry", "share"}


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.keyword in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid, act in ACTIVITIES.items():
            for pid, pr in PRIZES.items():
                if prize_at_risk(act, pr) and select_gear(act, pr):
                    combos.append((place, aid, pid))
    return combos


def setting_line(world: World) -> str:
    if world.setting.has_wind:
        return "The wind kept trying to nudge everything into a new joke."
    return f"{world.setting.place.capitalize()} looked calm enough for a careful walk."


def tell(setting: Setting, activity: Activity, prize: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    sibling = world.add(Entity(id="sibling", kind="character", type="sister", label="the sibling"))
    flower = world.add(Entity(
        id="flower",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=parent.id,
        fragile=True,
    ))
    hero.memes["joy"] = 1
    hero.memes["desire"] = 1

    world.say(f"{hero_name} was a little {hero_type} who loved the smell of fresh flowers.")
    world.say(f"{hero.pronoun().capitalize()} wanted to bring {hero.pronoun('object')} a {prize.phrase} as a surprise.")
    world.say(f"That morning, {hero_name} and {hero.pronoun('possessive')} {parent_type} went to {world.setting.place}.")
    world.say(setting_line(world))
    world.say(f"{hero_name} planned to {activity.verb}, but the flower was so delicate that everybody had to tiptoe.")

    world.para()
    world.say(f"Then {sibling.label} giggled and said, \"Careful, or the {prize.label} will do a tiny somersault.\"")
    hero.memes["hurt"] = 1
    hero.memes["annoyed"] = 1
    world.say(f"{hero_name} frowned and tried to {activity.rush}.")
    if world.setting.has_steps:
        hero.meters["bumps"] = 1
    propagate(world, narrate=True)

    world.para()
    hero.memes["kindness"] = 1
    sibling.memes["kindness"] = 1
    world.say(f"Then {hero_name} heard {sibling.label}'s sorry voice and slowed down.")
    world.say(f"{sibling.label} said, \"I was being silly. I did not mean to poke at your plan.\"")
    world.say(f"{hero_name} sighed, then smiled anyway. \"I forgive you,\" {hero.pronoun()} said, because the day was too funny to stay mad.")
    world.say(f"They both looked at the flower, and the flower looked extremely unimpressed.")
    world.say("Together they made a joke about the flower needing a tiny little helmet.")

    flower.meters["broken"] = 1
    flower.meters["petal_loss"] = 1
    hero.memes["reconciled"] = 1
    sibling.memes["reconciled"] = 1
    world.say(f"In the end, the {prize.label} bent sadly and lost a petal, so the surprise was ruined.")
    world.say(f"But {hero_name} and {sibling.label} walked home side by side, laughing at the world's worst parade float.")

    world.facts.update(
        hero=hero,
        parent=parent,
        sibling=sibling,
        flower=flower,
        activity=activity,
        prize=prize,
        setting=setting,
        bad_ending=True,
        reconciled=True,
    )
    return world


SETTINGS = {
    "garden": Setting(place="the garden", has_wind=True, has_steps=False),
    "porch": Setting(place="the porch", has_wind=True, has_steps=True),
    "kitchen": Setting(place="the kitchen", has_wind=False, has_steps=False),
}

ACTIVITIES = {
    "carry": Activity(
        id="carry",
        verb="carry the flower to the neighbor",
        gerund="carrying the flower",
        rush="dash across the little path",
        risk="a bump from the windy steps",
        mess="bent petals",
        zone={"hands", "feet"},
        keyword="flower",
        tags={"flower", "kindness"},
    ),
    "share": Activity(
        id="share",
        verb="share the flower with the family",
        gerund="sharing the flower",
        rush="hurry to show everyone",
        risk="a funny sneeze from the pollen",
        mess="scattered petals",
        zone={"hands", "face"},
        keyword="flower",
        tags={"flower", "reconciliation"},
    ),
}

PRIZES = {
    "flower": Prize(
        label="flower",
        phrase="a bright pink flower",
        type="flower",
        fragile=True,
    )
}

GEAR = [
    Gear(
        id="cup",
        label="a paper cup",
        guards={"flower"},
        prep="put the flower in a paper cup",
        tail="carefully carried the flower in a paper cup",
    ),
    Gear(
        id="wrap",
        label="soft wrapping paper",
        guards={"flower"},
        prep="wrap the flower in soft paper",
        tail="carefully wrapped the flower in soft paper",
    ),
]

NAMES = ["Mila", "Noah", "Pia", "Theo", "Luna", "Ezra"]
TYPES = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["cheerful", "curious", "silly", "gentle"]


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
    ap = argparse.ArgumentParser(description="A comedy storyworld about flowers, kindness, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=TYPES)
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


def explain_rejection() -> str:
    return "(No story: this flower world needs a risky flower trip and a comic fix.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError(explain_rejection())
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(TYPES)
    parent = args.parent or rng.choice(PARENTS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=rng.choice(TRAITS))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short comedy story for a child where a {hero.type} named {hero.id} tries to {act.verb}.',
        "Tell a gentle but funny story about a flower, a mistake, and two people making up.",
        "Write a small story that ends with a ruined flower and a repaired friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    flower = f["flower"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the flower?",
            answer=f"{hero.id} wanted to {act.verb} with {flower.phrase}.",
        ),
        QAItem(
            question=f"Why did {hero.id} get upset at first?",
            answer=f"{hero.id} got upset because {sibling.label} made a silly remark and the flower was delicate and easy to mess up.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The people made up and laughed together, but the flower itself ended badly after losing a petal and bending over.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do flowers need gentle handling?",
            answer="Flowers are fragile, so rough bumps can bend the stem or make petals fall off.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make up after an argument.",
        ),
        QAItem(
            question="Why can kindness help after a mistake?",
            answer="Kindness can calm hurt feelings, make apology easier, and help people move on together.",
        ),
        QAItem(
            question="What makes a comedy story funny?",
            answer="A comedy story uses silly surprises, awkward moments, and harmless mix-ups to make people laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== Story QA =="]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, act.keyword))
    for gid in GEAR:
        lines.append(asp.fact("gear", gid.id))
        for g in sorted(gid.guards):
            lines.append(asp.fact("guards", gid.id, g))
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A,P) :- activity(A), prize(P), keyword(A,"flower").
has_fix(A,P) :- at_risk(A,P), gear(G), guards(G,"flower").
valid(Place,A,P) :- place(Place), at_risk(A,P), has_fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_combos_asp())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in Python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
    StoryParams(place="porch", activity="carry", prize="flower", name="Mila", gender="girl", parent="mother", trait="silly"),
    StoryParams(place="garden", activity="share", prize="flower", name="Noah", gender="boy", parent="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = valid_combos_asp()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
