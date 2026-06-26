#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lute_gush_flashback_happy_ending_fable.py
================================================================================================

A small fable-like story world about a cherished lute, a sudden gush, and a
flashback that helps the hero solve the trouble in a kind way.

The tale shape:
- beginning: a young fox-bard treasures a lute
- middle: a gush of water threatens the instrument
- flashback: the bard remembers how the lute was first repaired
- ending: the same careful habit saves the day, and the village shares music

This script is self-contained and follows the storyworld contract.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "mouse", "bard"}:
            # bard defaults to he/they-like neutral masculine for simplicity
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village green"
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
    genders: set[str] = field(default_factory=lambda: {"fox", "mouse", "bard"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    seed: Optional[int] = None


SETTINGS = {
    "green": Setting(place="the village green", affords={"gush"}),
    "well": Setting(place="the old well", affords={"gush"}),
    "brook": Setting(place="the brook behind the mill", affords={"gush"}),
}

ACTIVITIES = {
    "gush": Activity(
        id="gush",
        verb="play by the gush of water",
        gerund="playing by the gush",
        rush="run toward the water",
        mess="wet",
        soil="damp and slippery",
        zone={"torso", "hands"},
        keyword="gush",
        tags={"water", "gush", "wet"},
    )
}

PRIZES = {
    "lute": Prize(
        label="lute",
        phrase="a small polished lute",
        type="lute",
        region="torso",
        plural=False,
    )
}

GEAR = [
    Gear(
        id="wrap",
        label="a wool wrap",
        covers={"torso"},
        guards={"wet"},
        prep="wrap the lute in wool first",
        tail="carefully wrapped the lute in wool",
    ),
]


GIRL_NAMES = ["Mira", "Tessa", "Lina"]
BOY_NAMES = ["Arin", "Pip", "Nico"]
TRAITS = ["kind", "patient", "gentle", "thoughtful"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} went near the water and felt the day turn bright.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": actor.meters.get(activity.mess, 0.0) >= THRESHOLD and prize.region in activity.zone}


def introduce(world: World, hero: Entity, trait: str) -> None:
    world.say(f"Once there was a little {trait} fox named {hero.id}, and {hero.id} loved songs more than sleep.")


def prize_intro(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    prize.worn_by = hero.id
    world.say(f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label}, a gift that made every tune feel new.")


def flashback(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"Long ago, {hero.id} had heard how a careful elder dried {prize.it()} by a warm window after a spill, "
        f"and {hero.id} had never forgotten that lesson."
    )
    world.facts["flashback"] = True


def arrive_and_warn(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    world.say(f"One morning, {hero.id} came to {world.setting.place} and saw a bright gush of water sliding over the stones.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} ears twitched at the risk to {prize.it()}.")

    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.say(f'"If I leap in now, my {prize.label} will get {activity.soil}," {hero.pronoun()} said.')
        world.facts["warning"] = True


def remember_and_choose(world: World, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    world.say(f"Then {hero.id} remembered the elder's lesson and paused instead of rushing ahead.")
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    world.say(f"{hero.id} took {gear.label} and did not let the rush touch {prize.it()}.")
    world.facts["gear"] = gear
    return gear


def resolve(world: World, hero: Entity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.0
    world.say(
        f"So {hero.id} {gear.prep}, and after that {hero.id} could enjoy the gush without fear. "
        f"{hero.id} {gear.tail}, then played a small song while {prize.label} stayed dry and safe."
    )
    world.say(
        f"The village listened, and the sound was so sweet that even the water seemed to hush and smile."
    )
    world.facts["happy_ending"] = True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="fox"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
    ))
    trait = "kind"

    introduce(world, hero, trait)
    prize_intro(world, hero, prize)

    world.para()
    arrive_and_warn(world, hero, activity, prize)

    world.para()
    flashback(world, hero, prize)
    gear = remember_and_choose(world, hero, activity, prize)
    if gear is None:
        raise StoryError("No reasonable gear exists for this story world.")
    resolve(world, hero, prize, gear)

    world.facts.update(hero=hero, prize=prize, activity=activity, setting=setting, gear=gear)
    return world


KNOWLEDGE = {
    "lute": [
        ("What is a lute?", "A lute is a stringed instrument with a rounded body, played by plucking the strings."),
    ],
    "water": [
        ("What is a gush of water?", "A gush is a sudden strong flow of water that moves quickly and can splash around."),
    ],
    "wet": [
        ("Why should a wooden instrument stay dry?", "Wood can swell, bend, or sound worse if it gets too wet."),
    ],
    "kind": [
        ("Why do kind people remember lessons?", "Kind people remember good lessons so they can help themselves and others later."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short fable for a young child about {hero.id}, a lute, and a {act.keyword}.',
        f"Tell a gentle story with a flashback where {hero.id} remembers an old lesson before a water problem.",
        f"Write a happy-ending fable in which a fox keeps a lute safe near a sudden gush of water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    qs = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little fox who loved a lute and acted with care.",
        ),
        QAItem(
            question=f"What problem did {hero.id} notice near the {act.keyword}?",
            answer=f"{hero.id} noticed that the gush of water could make the {prize.label} damp and slippery.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered that an elder once dried a {prize.label} carefully after a spill.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} using {gear.label} and playing music while the {prize.label} stayed dry.",
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | {"lute", "kind", "wet"}
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  zone={sorted(world.zone)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="green", activity="gush", prize="lute", hero="Mira"),
    StoryParams(place="well", activity="gush", prize="lute", hero="Arin"),
    StoryParams(place="brook", activity="gush", prize="lute", hero="Tessa"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about a lute, a gush, a flashback, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
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
    if args.place or args.activity or args.prize:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.activity is None or c[1] == args.activity)
            and (args.prize is None or c[2] == args.prize)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.hero)
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


ASP_RULES = r"""
place(green). place(well). place(brook).
activity(gush).
prize(lute).
affords(green,gush). affords(well,gush). affords(brook,gush).
mess_of(gush,wet).
splashes(gush,torso). splashes(gush,hands).
worn_on(lute,torso).
gear(wrap).
guards(wrap,wet).
covers(wrap,torso).

prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
#show valid/3.
#show protects/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for combo in combos:
            print("  ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
