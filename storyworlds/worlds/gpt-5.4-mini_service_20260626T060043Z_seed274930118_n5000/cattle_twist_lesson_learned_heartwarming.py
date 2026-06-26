#!/usr/bin/env python3
"""
Storyworld: cattle_twist_lesson_learned_heartwarming
====================================================

A small heartwarming story domain about a child, a few cattle, a helpful adult,
and a lesson learned after a gentle twist.

The seed premise:
- A child helps with cattle on a little farm.
- The child expects a simple chore to be annoying or disappointing.
- A small twist reveals the cattle were responding to something kind or useful.
- The story ends with the child learning a lesson and feeling closer to the
  cattle, the helper, and the farm.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports results eagerly
- ASP helper imported lazily
- supports generation, QA, JSON, trace, ASP, verify, show-asp
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
    kind: str = "thing"  # "character" | "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    where: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    pasture: bool
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
    keyword: str
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
class Twist:
    id: str
    reveal: str
    helper_action: str
    lesson: str
    ending_image: str
    resolution_word: str = "heartwarming"


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    twist: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "animal"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "barn": Setting(place="the barn", pasture=True, affords={"hay", "brush", "bell"}),
    "pasture": Setting(place="the pasture", pasture=True, affords={"hay", "brush", "bell"}),
    "yard": Setting(place="the farmyard", pasture=False, affords={"brush", "bell"}),
}

ACTIVITIES = {
    "hay": Activity(
        id="hay",
        verb="feed the cattle",
        gerund="feeding the cattle",
        rush="run to the hay pile",
        mess="dusty",
        soil="dusty",
        zone={"hands", "clothes"},
        keyword="hay",
        tags={"cattle", "hay", "feed"},
    ),
    "brush": Activity(
        id="brush",
        verb="brush the cattle",
        gerund="brushing the cattle",
        rush="grab the brush",
        mess="muddy",
        soil="muddy",
        zone={"hands", "clothes"},
        keyword="brush",
        tags={"cattle", "brush"},
    ),
    "bell": Activity(
        id="bell",
        verb="look for the missing bell",
        gerund="searching for the bell",
        rush="run after the gate",
        mess="tired",
        soil="tired",
        zone={"hands"},
        keyword="bell",
        tags={"cattle", "bell"},
    ),
}

PRIZES = {
    "boots": Prize(label="boots", phrase="new red boots", type="boots", region="feet", plural=True),
    "overalls": Prize(label="overalls", phrase="clean overalls", type="overalls", region="clothes", plural=True),
    "shirt": Prize(label="shirt", phrase="a bright shirt", type="shirt", region="clothes"),
}

TWISTS = {
    "calf_lost": Twist(
        id="calf_lost",
        reveal="a small calf had wandered behind the hay bales and was calling for its mother",
        helper_action="the mother cow answered with a low moo, and the whole herd walked softly toward the calf",
        lesson="the child learned that cattle do not need shouting; they do best with patience and a calm voice",
        ending_image="Soon the calf was nestled beside its mother, and the child was smiling beside the quiet herd.",
    ),
    "bell_ring": Twist(
        id="bell_ring",
        reveal="the missing bell was tied to the gate, where the wind kept nudging it with a gentle ring",
        helper_action="the parent showed the child how to tie the bell safely so the cattle would not bump it loose again",
        lesson="the child learned that a small problem can have a simple fix when someone stops and looks carefully",
        ending_image="The bell stayed still at last, and the cattle wandered on while the child felt proud and calm.",
    ),
    "mud_help": Twist(
        id="mud_help",
        reveal="the cattle were not making a mess for fun; they were stepping carefully around a muddy patch so the little calf would not slip",
        helper_action="the child brought a board to the muddy spot, and the herd crossed it one by one",
        lesson="the child learned that what looks noisy or messy can sometimes be a sign that everyone is trying to help",
        ending_image="The calf crossed safely, and the child watched the herd with warmer eyes than before.",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Theo", "Max", "Noah"]
TRAITS = ["curious", "gentle", "stubborn", "cheerful", "quiet", "helpful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                for twist_id in TWISTS:
                    if prize_id == "boots" and act_id == "bell":
                        combos.append((place, act_id, prize_id, twist_id))
                    elif prize_id != "boots":
                        combos.append((place, act_id, prize_id, twist_id))
    return combos


def reasonableness_gate(activity: Activity, prize: Prize, twist: Twist) -> bool:
    if activity.id == "bell" and prize.label == "boots":
        return True
    if activity.id in {"hay", "brush"} and prize.region == "clothes":
        return True
    return True


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), affects(A,R), worn_on(P,R).
compatible(A,P) :- prize_at_risk(A,P), fixable(A,P).
valid(Place,A,P,T) :- affords(Place,A), compatible(A,P), twist(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.pasture:
            lines.append(asp.fact("pasture", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("affects", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
        lines.append(asp.fact("fixable", "hay", "boots"))
        lines.append(asp.fact("fixable", "brush", "shirt"))
        lines.append(asp.fact("fixable", "bell", "boots"))
        lines.append(asp.fact("fixable", "bell", "shirt"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming cattle story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--twist", choices=TWISTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.twist is None or c[3] == args.twist)]
    if not combos:
        raise StoryError("(No valid cattle story matches the given options.)")
    place, activity, prize, twist = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    prize_obj = PRIZES[prize]
    if args.gender and args.gender not in prize_obj.genders:
        raise StoryError("That prize does not fit the chosen child.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, twist=twist,
                       name=name, gender=gender, parent=parent, trait=trait)


def _say_start(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.memes.get('trait_word', 'curious')} {hero.type} who loved the farm.")
    world.say(f"{hero.pronoun().capitalize()} liked the cattle most of all, especially when {hero.pronoun('possessive')} {parent.type} let {hero.pronoun('object')} help.")
    world.say(f"That morning, {hero.id} wore {hero.pronoun('possessive')} {prize.label}, and {hero.pronoun('possessive')} {parent.type} smiled at how neat {hero.pronoun('object')} looked.")


def generate_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    prize = world.add(Entity(id="Prize", type=params.prize, label=PRIZES[params.prize].label,
                             phrase=PRIZES[params.prize].phrase, owner=hero.id))
    twist = TWISTS[params.twist]
    herd = world.add(Entity(id="Herd", kind="animal", type="cattle", label="the cattle", plural=True))

    hero.memes["trait_word"] = params.trait
    prize.where = "worn"

    _say_start(world, hero, parent, prize)
    world.para()
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to {setting.place}.")
    if params.activity == "hay":
        world.say(f"{hero.id} wanted to feed the cattle, but the hay pile looked taller than {hero.id} expected.")
    elif params.activity == "brush":
        world.say(f"{hero.id} wanted to brush the cattle, but the brush was tucked far back on a shelf.")
    else:
        world.say(f"{hero.id} wanted to look for the missing bell, but the gate had a sly little way of hiding things.")

    world.para()
    world.say(f"{hero.id} frowned and started {ACTIVITIES[params.activity].gerund}.")
    world.say(f"Then came the twist: {twist.reveal}.")
    world.say(twist.helper_action)
    world.para()
    world.say(twist.lesson.capitalize() + ".")
    world.say(twist.ending_image)
    world.say(f"{hero.id} went home feeling a little wiser, and {hero.pronoun('possessive')} {parent.type} gave {hero.pronoun('object')} a proud hug.")

    world.facts.update(hero=hero, parent=parent, prize=prize, twist=twist, activity=ACTIVITIES[params.activity], setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about a child helping with cattle at {f["setting"].place}.',
        f"Tell a gentle tale where {f['hero'].id} expects a small problem with the cattle but learns a kind lesson instead.",
        f'Write a story with a twist and a lesson learned, using the word "cattle" and ending with a warm family moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, twist, act = f["hero"], f["parent"], f["prize"], f["twist"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the cattle at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} wear while helping on the farm?",
            answer=f"{hero.id} wore {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=twist.reveal.capitalize() + ".",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer=twist.lesson.capitalize() + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are cattle?",
            answer="Cattle are large farm animals such as cows and bulls. People care for them, feed them, and keep them safe."
        ),
        QAItem(
            question="Why do farmers use a gate?",
            answer="A gate helps people open and close an entrance to a field or barn, so animals can stay where they should be."
        ),
        QAItem(
            question="Why should you be gentle with farm animals?",
            answer="Farm animals can be startled by loud noises or rough movements, so gentle hands and calm voices help them feel safe."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    StoryParams(place="barn", activity="hay", prize="overalls", twist="calf_lost", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="pasture", activity="brush", prize="shirt", twist="mud_help", name="Leo", gender="boy", parent="father", trait="helpful"),
    StoryParams(place="yard", activity="bell", prize="boots", twist="bell_ring", name="Nora", gender="girl", parent="mother", trait="gentle"),
]


def asp_show_program() -> str:
    return asp_program("#show valid/4.")


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(" ", row)
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.twist})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
