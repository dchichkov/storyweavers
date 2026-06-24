#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T071419Z_seed779406221_n50/humorous_twist_sound_effects_kindness_heartwarming.py
==============================================================================================================================

A small, standalone storyworld about a child in a cozy kitchen who wants to make a
funny sound-effect breakfast, learns a kind twist, and ends with a warm, heartening
gesture.

Premise:
- A child loves noisy play in a tiny kitchen.
- A careful grown-up worries the noise will upset someone or spoil the food.
- The twist is that the "problem" sound becomes part of a kind, helpful plan.
- The ending proves the change through a shared, warm image.

This world uses:
- typed entities with physical meters and emotional memes
- forward-chaining state updates
- a reasonableness gate for valid combinations
- an inline ASP twin for parity checks
- grounded story QA and child-level world QA
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
    sound: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Twist:
    id: str
    label: str
    cause: str
    reveal: str
    helpful: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    twist: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_sound_echo(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["noisy"] < THRESHOLD:
            continue
        sig = ("echo", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper = world.facts["helper"]
        helper.memes["delight"] += 1
        out.append(f"The room answered with a funny echo.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    helper = world.facts["helper"]
    if child.memes["kindness"] >= THRESHOLD and helper.memes["worry"] >= THRESHOLD:
        sig = ("kindness", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["calm"] += 1
            child.memes["pride"] += 1
            out.append("The kind plan worked.")
    return out


CAUSAL_RULES = [Rule(name="sound_echo", apply=_r_sound_echo), Rule(name="kindness", apply=_r_kindness)]


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


def valid_combo(place: str, activity: str, prize: str, twist: str) -> bool:
    a = ACTIVITIES[activity]
    p = PRIZES[prize]
    t = TWISTS[twist]
    return place in SETTINGS and activity in SETTINGS[place].affords and p.region in a.zone and t.cause == activity


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act in SETTINGS[place].affords:
            for prize in PRIZES:
                for twist in TWISTS:
                    if valid_combo(place, act, prize, twist):
                        combos.append((place, act, prize, twist))
    return combos


def make_child(world: World, name: str, gender: str) -> Entity:
    return world.add(Entity(id=name, kind="character", type=gender, label=name))


def tell(setting: Setting, activity: Activity, prize: Prize, twist: Twist,
         child_name: str, child_gender: str, helper_gender: str) -> World:
    world = World(setting)
    child = make_child(world, child_name, child_gender)
    helper_name = "Mom" if helper_gender == "girl" else "Dad"
    helper_type = "mother" if helper_gender == "girl" else "father"
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    snack = world.add(Entity(id="snack", type="thing", label=prize.label, phrase=prize.phrase))
    bowl = world.add(Entity(id="bowl", type="thing", label="bowl", phrase="a bowl"))
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["snack"] = snack
    world.facts["bowl"] = bowl
    world.facts["twist"] = twist
    world.facts["activity"] = activity
    world.facts["setting"] = setting
    world.facts["prize"] = prize

    child.memes["joy"] += 1
    helper.memes["worry"] += 1

    world.say(f"{child.id} was in {setting.place}, where a little breakfast adventure was about to begin.")
    world.say(f"{child.id} loved to {activity.verb}, and the sound went {activity.sound}.")
    world.say(f"{child.id} wanted to make {prize.phrase} look special for {twist.label} day.")

    world.para()
    world.say(f"But {helper.label} frowned a tiny bit. \"That could get loud,\" {helper.pronoun()} said.")
    child.meters["noisy"] += 1
    child.memes["wish"] += 1
    world.say(f"{child.id} gave the snack a careful poke, and it went {activity.sound.lower()}!")
    propagate(world, narrate=True)

    world.para()
    child.memes["kindness"] += 1
    world.say(f"Then came the twist: {twist.reveal}")
    world.say(f"{child.id} decided to be kind and use the funny sound on purpose.")
    helper.memes["worry"] += 1
    if twist.id == "cheer":
        world.say(f"{child.id} tapped the spoon again and made {activity.sound.lower()}, just to cheer {helper.id} up.")
    elif twist.id == "kitten":
        world.say(f"{child.id} heard {activity.sound.lower()} and noticed a small kitten under the chair.")
    else:
        world.say(f"{child.id} heard {activity.sound.lower()} and found a neighbor at the door, smiling shyly.")

    world.para()
    if child.memes["kindness"] >= THRESHOLD:
        world.say(f"{helper.label} smiled as the funny noise turned into a warm little rhythm.")
        world.say(f"Together they finished {prize.label}, and the kitchen smelled sweet and safe.")
        child.memes["love"] += 1
        helper.memes["calm"] += 1
    else:
        world.say(f"{helper.label} kept watching, but the room still felt a bit jumpy.")

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"stir", "tap", "whisk"}),
    "cafe": Setting(place="the tiny cafe", affords={"stir", "tap"}),
    "bakery": Setting(place="the bakery corner", affords={"whisk", "tap"}),
}

ACTIVITIES = {
    "tap": Activity(id="tap", verb="tap the spoon", gerund="tapping spoons", sound="clink-clank", mess="batter", zone={"counter"}, keyword="tap", tags={"sound", "humorous"}),
    "stir": Activity(id="stir", verb="stir the batter", gerund="stirring batter", sound="whirr-whirr", mess="batter", zone={"counter"}, keyword="stir", tags={"sound", "humorous"}),
    "whisk": Activity(id="whisk", verb="whisk the cream", gerund="whisking cream", sound="swish-swish", mess="cream", zone={"counter"}, keyword="whisk", tags={"sound", "humorous"}),
}

PRIZES = {
    "pancakes": Prize(label="pancakes", phrase="a stack of pancakes", region="counter", plural=True),
    "muffins": Prize(label="muffins", phrase="a tray of muffins", region="counter", plural=True),
    "toast": Prize(label="toast", phrase="a little plate of toast", region="counter", plural=True),
}

TWISTS = {
    "cheer": Twist(id="cheer", label="cheer-up", cause="tap", reveal="the sound was just right for cheering up a sleepy helper", helpful="warm"),
    "kitten": Twist(id="kitten", label="kitten-call", cause="stir", reveal="the noise was actually helping a tiny kitten find the door", helpful="gentle"),
    "neighbor": Twist(id="neighbor", label="neighbor-call", cause="whisk", reveal="the funny sound brought a shy neighbor to the doorway", helpful="kind"),
}

GIRL_NAMES = ["Lina", "Mia", "Ada", "Nora", "Tess", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Milo", "Owen", "Noah", "Ben"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming kitchen storyworld with a humorous sound-effect twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize, twist = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        twist=twist,
        child=child,
        child_gender=gender,
        helper=helper_gender,
        helper_gender=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a 3-to-5-year-old where {f["child"].id} makes funny sound effects in {f["setting"].place} and learns a kind twist.',
        f'Tell a humorous but cozy kitchen story where {f["child"].id} goes "{f["activity"].sound}!" and the noise turns into kindness.',
        f'Write a simple story about {f["child"].id}, {f["prize"].label}, and a surprise twist that ends with a warm, happy feeling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    h = world.facts["helper"]
    a = world.facts["activity"]
    p = world.facts["prize"]
    t = world.facts["twist"]
    return [
        QAItem(question=f"Where was {c.id} making the funny sound?", answer=f"{c.id} was making the sound in {world.facts['setting'].place}."),
        QAItem(question=f"What sound did {c.id}'s activity make?", answer=f"It went {a.sound}, which made the scene feel playful and a little silly."),
        QAItem(question=f"What was the twist in the story?", answer=f"The twist was that {t.reveal}."),
        QAItem(question=f"How did the helper feel at first?", answer=f"{h.label} felt a little worried, because the noise seemed like it might be too much."),
        QAItem(question=f"How did kindness change the ending?", answer=f"{c.id} chose kindness, and the funny sound became part of a warm plan instead of a problem."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What are sound effects in a story?", answer="Sound effects are words that help you imagine noises, like clink, bang, or swish."),
        QAItem(question="What does kindness mean?", answer="Kindness means being gentle and helpful to someone else. It can make a worried face turn into a smile."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise that changes what you expect, often in a fun or clever way."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="tap", prize="pancakes", twist="cheer", child="Lina", child_gender="girl", helper="girl", helper_gender="girl"),
    StoryParams(place="cafe", activity="stir", prize="muffins", twist="kitten", child="Leo", child_gender="boy", helper="boy", helper_gender="boy"),
    StoryParams(place="bakery", activity="whisk", prize="toast", twist="neighbor", child="Nora", child_gender="girl", helper="girl", helper_gender="girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], TWISTS[params.twist], params.child, params.child_gender, params.helper_gender)
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
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


ASP_RULES = r"""
valid(P,A,S,T) :- setting(P), affords(P,A), activity(A), prize(S), twist(T).
soundy(A) :- activity(A), sound(A,_).
kind_end(T) :- twist(T), helpful(T,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k, s in SETTINGS.items():
        lines.append(asp.fact("setting", k))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", k, a))
    for k, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", k))
        lines.append(asp.fact("sound", k, a.sound))
    for k in PRIZES:
        lines.append(asp.fact("prize", k))
    for k, t in TWISTS.items():
        lines.append(asp.fact("twist", k))
        lines.append(asp.fact("cause", k, t.cause))
        lines.append(asp.fact("helpful", k, t.helpful))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
