#!/usr/bin/env python3
"""
storyworlds/worlds/define_twist_folk_tale.py
============================================

A small, self-contained folk-tale storyworld about a humble child, a village
problem, and a gentle twist that turns danger into a better ending.

Premise:
- A child hears a tale about a hidden "define" charm: a way of naming a thing
  clearly so it can be handled wisely.
- The child wants to fetch or carry something precious through a risky place.
- An elder warns that the first plan would spoil the prize or cause trouble.
- The story turns on a twist: a smarter, kinder method that respects the risk
  and lets the child succeed.

The world is intentionally tiny, classical, and state-driven: physical meters
track risk and spoilage, while memes track fear, courage, and trust.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    carried_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "muddy": 0.0, "lost": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "trust": 0.0, "courage": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "sister"}
        male = {"boy", "father", "man", "grandfather", "brother"}
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
    risk: str
    mess: str
    zone: set[str]
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


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
        self.zone: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

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


def _risk_rule(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD and actor.meters["muddy"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if not (item.region in world.zone):
                continue
            sig = ("risk", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += actor.meters["wet"]
            item.meters["muddy"] += actor.meters["muddy"]
            item.meters["lost"] += 0.0
            out.append(f"{item.label.capitalize()} got caught in the trouble.")
    return out


def _loss_rule(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["wet"] + item.meters["muddy"] < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("loss", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["fear"] += 1
        out.append(f"That would mean extra work for the elder.")
    return out


RULES = [_risk_rule, _loss_rule]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"ruined": bool(prize.meters["wet"] + prize.meters["muddy"] >= THRESHOLD),
            "fear": sim.get(world.facts["elder"].id).memes["fear"] if "elder" in world.facts else 0.0}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} cannot support {activity.id}.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["courage"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"Once in a small village, {hero.id} was a little {hero.type} who loved "
        f"to listen when older folk told a story."
    )


def define(world: World, elder: Entity) -> None:
    elder.memes["trust"] += 1
    world.say(
        f"The old {elder.type} said a word could be powerful if it was well chosen: "
        f"to define a thing was to name it clearly, so folk could handle it wisely."
    )


def want(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} and carry {hero.pronoun('possessive')} "
        f"{prize.label} home before sunset."
    )


def warning(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_risk(world, hero, activity, prize.id)
    if not pred["ruined"]:
        return False
    elder.memes["fear"] += 1
    world.facts["predicted_ruin"] = activity.risk
    world.say(
        f'"If you go to {activity.verb}, your {prize.label} will get {activity.risk}," '
        f'said the old {elder.type}. "A wise child first defines the danger."'
    )
    return True


def twist(world: World, hero: Entity, elder: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        protective=True,
        covers=set(gear_def.covers),
        owner=hero.id,
        caretaker=elder.id,
    ))
    gear.carried_by = hero.id
    world.say(
        f"Then the old {elder.type} made a twist in the tale: "
        f'"How about we {gear_def.prep} first, and then {activity.verb}?"'
    )
    hero.memes["trust"] += 1
    hero.memes["fear"] = 0.0
    world.facts["gear"] = gear


def accept(world: World, hero: Entity, elder: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"{hero.id} smiled, took the {gear_def.label}, and agreed. "
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"and {prize.label} stayed clean."
    )
    world.say(
        f"In the end, the child learned that a good define and a kind twist could both save the day."
    )


def render_setting(setting: Setting) -> str:
    return {
        "forest": "The forest path was dark with roots and moss.",
        "river": "The riverbank gleamed, and the water ran quick and cold.",
        "hill": "The hill was windy, with grass bowing like a crowd of little listeners.",
    }[setting.place]


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         elder_type: str, gear_def: Gear) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type))
    prize = world.add(Entity(
        id="Prize",
        type="thing",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=elder.id,
    ))
    world.facts.update(hero=hero, elder=elder, prize=prize, activity=activity, setting=setting)

    introduce(world, hero)
    define(world, elder)
    world.say(render_setting(setting))
    want(world, hero, activity, prize)

    world.para()
    warning(world, elder, hero, activity, prize)
    twist(world, hero, elder, activity, prize, gear_def)

    world.para()
    accept(world, hero, elder, activity, prize, gear_def)
    return world


SETTINGS = {
    "forest": Setting("forest", affords={"mend_cape", "fetch_honey", "cross_stream"}),
    "river": Setting("river", affords={"mend_cape", "fetch_honey", "cross_stream"}),
    "hill": Setting("hill", affords={"mend_cape", "fetch_honey", "cross_stream"}),
}

ACTIVITIES = {
    "mend_cape": Activity(
        id="mend_cape",
        verb="mend the torn cape",
        gerund="mending the torn cape",
        rush="run to the needle grass",
        risk="frayed",
        mess="muddy",
        zone={"torso"},
        keyword="define",
    ),
    "fetch_honey": Activity(
        id="fetch_honey",
        verb="fetch the honey jar",
        gerund="fetching the honey jar",
        rush="hurry to the bee tree",
        risk="sticky",
        mess="wet",
        zone={"hands"},
        keyword="twist",
    ),
    "cross_stream": Activity(
        id="cross_stream",
        verb="cross the little stream",
        gerund="crossing the little stream",
        rush="dash through the water",
        risk="soaked",
        mess="wet",
        zone={"feet", "legs"},
        keyword="define",
    ),
}

PRIZES = {
    "cape": Prize("cape", "a bright old cape", "torso"),
    "jar": Prize("jar", "a small honey jar", "hands"),
    "shoes": Prize("shoes", "worn village shoes", "feet", plural=True),
}

GEAR = [
    Gear("needle", "a stout needle and thread", {"torso"}, {"muddy"}, "sit down with a stout needle and thread", "sat by the fire and mended the cape"),
    Gear("gloves", "bee gloves", {"hands"}, {"wet"}, "put on bee gloves", "tied on the bee gloves"),
    Gear("boots", "water boots", {"feet", "legs"}, {"wet"}, "put on water boots", "laced up the water boots"),
]

HEROES = [("Mara", "girl"), ("Tomas", "boy"), ("Anya", "girl"), ("Pell", "boy")]
ELDERS = ["grandmother", "grandfather"]
TRAITS = ["curious", "kind", "brave", "quiet"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize) is not None:
                    combos.append((place, act_id, prize_id))
    return combos


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if select_gear(act, pr) is None:
            raise StoryError("No reasonable twist exists for that activity and prize.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    hero_name, gender = args.name, args.gender
    if not hero_name or not gender:
        hero_name, gender = rng.choice(HEROES)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=hero_name, gender=gender, elder=elder, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale that uses the word "define" and ends with a gentle twist.',
        f"Tell a child-sized story about {f['hero'].id} and an old {f['elder'].type} who helps "
        f"{f['hero'].id} {f['activity'].verb} without ruining the {f['prize'].label}.",
        f"Write a simple village tale where a wise elder defines the danger before the child chooses a safer way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, activity = f["hero"], f["elder"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who helped {hero.id} think about the problem before the trip?",
            answer=f"The old {elder.type} helped {hero.id} think clearly and define the danger before they left.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label}?",
            answer=f"{hero.id} wanted to {activity.verb} and bring the {prize.label} home safely.",
        ),
        QAItem(
            question=f"What was the twist in the tale?",
            answer=f"The twist was that the elder offered the right gear first, so the child could still go and the {prize.label} stayed clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to define something?",
            answer="To define something means to say clearly what it is or what it does.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a change that turns the story in a surprising new way.",
        ),
        QAItem(
            question="Why do people use protective gear?",
            answer="People use protective gear to keep their clothes, hands, or feet safe from rain, mud, or other mess.",
        ),
    ]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    hero_name, gender = params.name, params.gender
    hero_type = "girl" if gender == "girl" else "boy"
    gear_def = select_gear(ACTIVITIES[params.activity], PRIZES[params.prize])
    if gear_def is None:
        raise StoryError("No gear can make this tale reasonable.")
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], hero_name, hero_type, params.elder, gear_def)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about define, twist, and a gentle village ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
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


ASP_RULES = r"""
place(P) :- setting(P).
act(A) :- activity(A).
prize(P) :- prize(P).

risk(A, Pz) :- act(A), prize(Pz), splashes(A, R), worn_on(Pz, R).
fix(A, Pz) :- risk(A, Pz), gear(G), guards(G, M), mess_of(A, M), covers(G, R), worn_on(Pz, R).
valid(P, A, Pz) :- setting(P), affords(P, A), risk(A, Pz), fix(A, Pz).
#show valid/3.
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
    for pr_id, pr in PRIZES.items():
        lines.append(asp.fact("prize", pr_id))
        lines.append(asp.fact("worn_on", pr_id, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(valid_combos_asp()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


CURATED = [
    StoryParams("forest", "cross_stream", "shoes", "Mara", "girl", "grandmother", "curious"),
    StoryParams("river", "fetch_honey", "jar", "Tomas", "boy", "grandfather", "brave"),
    StoryParams("hill", "mend_cape", "cape", "Anya", "girl", "grandmother", "kind"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: nothing in the little world can keep a {prize.label} safe during {activity.verb}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if select_gear(act, pr) is None:
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice([h[0] for h in HEROES])
    gender = args.gender or ("girl" if name in {"Mara", "Anya"} else "boy")
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, activity, prize, name, gender, elder, trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = valid_combos_asp()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
