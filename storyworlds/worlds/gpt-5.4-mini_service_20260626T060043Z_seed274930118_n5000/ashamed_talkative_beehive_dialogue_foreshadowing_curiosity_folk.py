#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ashamed_talkative_beehive_dialogue_foreshadowing_curiosity_folk.py
====================================================================================================

A small folk-tale story world about curiosity near a beehive, where a talkative
child grows ashamed after ignoring a warning, then finds a gentler way to be
brave.

The world is built to support:
- Dialogue
- Foreshadowing
- Curiosity
- Folk-tale style

Seed tale sketch:
---
A curious child kept asking questions near a village garden. An old gardener
warned that the beehive hummed loudly before trouble. The child, talkative and
eager, leaned too close anyway. The bees rose up, the child felt ashamed, and
the gardener helped them step back, speak softly, and make a careful apology.
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
REGIONS = {"hands", "face", "torso", "head"}


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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


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
    mess: str
    soil: str
    zone: set[str]
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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


def _r_buzz(world: World) -> list[str]:
    out: list[str] = []
    hive = world.entities.get("hive")
    if not hive:
        return out
    for actor in world.characters():
        if actor.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("buzz", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["buzz"] += 1
        hive.meters["buzz"] += 1
        out.append("The hive gave a low hum, as if it were keeping an old secret.")
    return out


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    hive = world.entities.get("hive")
    if not hive:
        return out
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        sig = ("alarm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hive.meters["alarm"] += 1
        actor.meters["alarm"] += 1
        out.append("The bees rose in a little cloud, unhappy at the noise.")
    return out


def _r_sting(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["alarm"] < THRESHOLD:
            continue
        for region in ("hands", "face"):
            if region not in world.zone:
                continue
            if world.covered(actor, region):
                continue
            sig = ("sting", actor.id, region)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["sting"] += 1
            actor.memes["ashamed"] += 1
            out.append(f"{actor.id} got a sharp sting on {region}.")
    return out


def _r_shame(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["sting"] < THRESHOLD or actor.memes["ashamed"] >= THRESHOLD:
            continue
        sig = ("shame", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["ashamed"] += 1
        out.append(f"{actor.id} went quiet, ashamed of not listening.")
    return out


CAUSAL_RULES = [
    Rule("buzz", "physical", _r_buzz),
    Rule("alarm", "physical", _r_alarm),
    Rule("sting", "physical", _r_sting),
    Rule("shame", "social", _r_shame),
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


def predict_mess(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {
        "sting": bool(sim.entities[actor.id].meters["sting"] >= THRESHOLD),
        "ashamed": bool(sim.entities[actor.id].memes["ashamed"] >= THRESHOLD),
    }


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["noise"] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"Once in a little village, there lived a little {trait} child named {hero.id}.")


def loves_hive(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} was the sort who asked one question after another, "
        f"for {hero.pronoun('subject')} liked to watch the beehive hum."
    )


def foreshadow(world: World, elder: Entity) -> None:
    world.say(
        f'"A hive that hums low is not a hive to poke," {elder.id} said. '
        f'"Listen first, and the day will listen back."'
    )


def arrive(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"One bright morning, {hero.id} and {hero.pronoun('possessive')} {elder.label_word} went to {world.setting.place}."
    )


def wants(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} wanted to {activity.verb}, because curiosity was tugging at {hero.pronoun('possessive')} sleeves."
    )


def warn(world: World, elder: Entity, hero: Entity, activity: Activity) -> None:
    pred = predict_mess(world, hero, activity)
    if pred["sting"]:
        world.say(
            f'"Be gentle near that hive," {elder.id} warned. '
            f'"Too much noise can bring the bees out in a temper."'
        )


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["noise"] += 1
    hero.memes["curiosity"] += 1
    hero.memes["talkative"] += 1
    world.say(
        f"But {hero.id} was talkative, and the questions kept spilling out. "
        f'{hero.id} leaned in and tried to {activity.rush}.'
    )


def steady(world: World, elder: Entity, hero: Entity) -> None:
    world.say(
        f'Then {elder.id} held up a hand and said, "Slow feet, soft mouth." '
        f"{hero.id} stopped at once."
    )


def offer_gear(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Prize) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=elder.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity)["sting"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'The {elder.label_word} brought out {gear_def.label} and said, '
        f'"If you still wish to look, let us look the careful way."'
    )
    return gear


def resolve(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Prize, gear: Gear) -> None:
    hero.memes["ashamed"] = 0.0
    hero.memes["calm"] += 1
    world.say(
        f"{hero.id} nodded, feeling ashamed but wiser. "
        f'"I am sorry," {hero.id} said softly, "I should have listened."'
    )
    world.say(
        f'The {elder.label_word} smiled. "A child can be curious and still be gentle." '
        f"Together they used the {gear.label}, and soon {hero.id} was {activity.gerund}, "
        f"while {prize.label} stayed safe and the hive kept its quiet secret."
    )


SETTINGS = {
    "village_garden": Setting(place="the village garden", affords={"peek"}),
    "sunny_lane": Setting(place="the sunny lane by the orchard", affords={"peek"}),
    "old_wall": Setting(place="the old stone wall behind the cottage", affords={"peek"}),
}

ACTIVITIES = {
    "peek": Activity(
        id="peek",
        verb="peek at the beehive",
        gerund="peeking at the beehive",
        rush="run right up to the hive",
        mess="noise",
        soil="troubled the bees",
        zone={"hands", "face"},
        keyword="beehive",
        tags={"beehive", "curiosity", "dialogue", "foreshadowing"},
    )
}

PRIZES = {
    "apron": Prize(
        label="apron",
        phrase="a blue apron",
        type="apron",
        region="torso",
    ),
    "hat": Prize(
        label="hat",
        phrase="a straw hat",
        type="hat",
        region="head",
    ),
    "basket": Prize(
        label="basket",
        phrase="a little basket of berries",
        type="basket",
        region="hands",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="veil",
        label="a beekeeper's veil",
        covers={"face", "head"},
        guards={"noise"},
        prep="put on the veil first",
        tail="had put on the veil and stood back",
    ),
    Gear(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        guards={"noise"},
        prep="wear soft gloves first",
        tail="wore the soft gloves and kept a careful distance",
    ),
]

CHILD_NAMES = ["Mina", "Nell", "Toby", "Rowan", "Pip", "Lina", "Jasper", "Sage"]
ELDER_NAMES = ["Grandma Wren", "Old Marta", "Grandpa Birch", "Auntie Mara"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, act, prize = f["hero"], f["elder"], f["activity"], f["prize_cfg"]
    return [
        f'Write a folk tale for a child named {hero.id} who is curious about a {act.keyword}.',
        f"Tell a gentle story where {hero.id} is talkative, {elder.id} gives a warning, and a beehive must be treated carefully.",
        f"Write a short story with dialogue and foreshadowing about {hero.id}, {prize.phrase}, and a hive that hums before trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, act = f["hero"], f["elder"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who was the curious child in the story?",
            answer=f"The curious child was {hero.id}, who kept asking questions near the beehive.",
        ),
        QAItem(
            question=f"What warning did {elder.id} give before anyone went too close?",
            answer=(
                f"{elder.id} warned that a hive that hums low should not be poked, "
                f"and that too much noise could bring the bees out."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} want to do near the hive?",
            answer=(
                f"{hero.id} wanted to {act.verb}. That wish was strong because {hero.id} was "
                f"curious and very talkative."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} feel after being stung and scolded by the bees?",
            answer=(
                f"{hero.id} felt ashamed after the sting, because {hero.id} had not listened "
                f"when {elder.id} gave the warning."
            ),
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help the child in the end?",
                answer=(
                    f"The {gear.label} helped by covering the right parts, so {hero.id} could "
                    f"look at the beehive more safely without troubling the bees again."
                ),
            )
        )
        qa.append(
            QAItem(
                question=f"What changed for {hero.id} by the end of the story?",
                answer=(
                    f"By the end, {hero.id} was calmer and more careful. "
                    f"{hero.id} learned that curiosity is best when it listens first."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beehive?",
            answer="A beehive is the home where bees live and keep their honey and young bees safe.",
        ),
        QAItem(
            question="Why should someone be quiet near a beehive?",
            answer="Being quiet helps the bees stay calm, because loud noise can make them feel bothered or alarmed.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more, asking questions, and looking closely at things.",
        ),
        QAItem(
            question="What does ashamed mean?",
            answer="Ashamed means feeling sorry and embarrassed after doing something you should not have done.",
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, gender: str, elder_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, traits=["little", "curious", "talkative"]))
    elder = world.add(Entity(id=elder_name, kind="character", type="grandmother", label="the elder"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=elder.id, region=prize_cfg.region, plural=prize_cfg.plural))
    hive = world.add(Entity(id="hive", type="thing", label="the beehive", phrase="the beehive"))
    world.facts.update(hero=hero, elder=elder, prize=prize, activity=activity, prize_cfg=prize_cfg, setting=setting, hive=hive)

    introduce(world, hero)
    loves_hive(world, hero)
    foreshadow(world, elder)
    world.para()
    arrive(world, hero, elder)
    wants(world, hero, activity)
    warn(world, elder, hero, activity)
    defy(world, hero, activity)
    steady(world, elder, hero)
    world.para()
    gear = offer_gear(world, elder, hero, activity, prize)
    if gear:
        resolve(world, elder, hero, activity, prize, gear)
    world.facts["gear"] = gear
    world.facts["resolved"] = gear is not None
    return world


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {noun} is not in the part of the body that this beehive scene affects.)"
    return f"(No story: no protective gear in this world covers {noun} well enough for the beehive scene.)"


CURATED = [
    StoryParams(place="village_garden", activity="peek", prize="hat", name="Pip", gender="boy", elder="Grandma Wren"),
    StoryParams(place="sunny_lane", activity="peek", prize="apron", name="Mina", gender="girl", elder="Old Marta"),
    StoryParams(place="old_wall", activity="peek", prize="basket", name="Toby", gender="boy", elder="Grandpa Birch"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about curiosity, shame, and a beehive.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDER_NAMES)
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.prize is None or c[1] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize_id = rng.choice(sorted(combos))
    activity = args.activity or "peek"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.elder)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protected(G,A,P) :- gear(G), at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protected(_,A,P).
valid(Place,Prize) :- affords(Place,peek), at_risk(peek,Prize), has_fix(peek,Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
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
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
