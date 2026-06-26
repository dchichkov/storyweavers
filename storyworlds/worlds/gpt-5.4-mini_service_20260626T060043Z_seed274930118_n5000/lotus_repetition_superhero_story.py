#!/usr/bin/env python3
"""
storyworlds/worlds/lotus_repetition_superhero_story.py
======================================================

A small superhero story world centered on a lotus pond, where a hero uses
careful repetition to turn a tense moment into a calm rescue.

The seed tale idea:
- A superhero watches over a lotus pond.
- A troublesome gust, splash, or wobble keeps upsetting the lotus.
- The hero cannot fix it with a single dramatic burst; the answer is repetition:
  steady breaths, repeated shield-fly laps, or a repeated helping motion.
- The ending image proves the change: the lotus opens, the water settles, and
  the hero stands proud beside the pond.

This script follows the Storyworld contract:
- one self-contained stdlib script
- shared result containers imported eagerly from storyworlds/results.py
- ASP helper imported lazily only inside ASP helpers
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus an inline ASP twin
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    skyline: str
    crowd: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    danger: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
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
        return any(item.protective and region in item.meters.get("covers", set()) for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _inc(d: dict[str, float], key: str, amt: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amt


def _r_bother(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meter("wobble") < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id:
                continue
            if item.protective:
                continue
            if "feet" not in world.zone and "hands" not in world.zone and "torso" not in world.zone:
                continue
            sig = ("bother", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _inc(item.meters, "damp", 1.0)
            out.append(f"{item.label.capitalize()} got damp in the commotion.")
    return out


def _r_restore_calm(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meter("calm") < THRESHOLD or actor.meter("repeat") < THRESHOLD:
            continue
        sig = ("restore", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["stabilized"] = 1.0
        out.append(f"The steady rhythm finally held everything still.")
    return out


CAUSAL_RULES = [
    _r_bother,
    _r_restore_calm,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Entity) -> bool:
    return prize.meters.get("region") in activity.zone if isinstance(prize.meters.get("region"), str) else False


def select_tool(activity: Activity, prize: Entity) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.risk in tool.guards and prize.meters.get("region") in tool.covers:
            return tool
    return None


def predict_failure(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "damp": bool(prize and prize.meter("damp") >= THRESHOLD),
        "stabilized": bool(sim.get(hero.id).meter("stabilized") >= THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"(No story: {world.setting.place} cannot host {activity.id}.)")
    world.zone = set(activity.zone)
    _inc(actor.meters, "wobble", 1.0)
    _inc(actor.meters, "repeat", 1.0)
    _inc(actor.memes, "determination", 1.0)
    propagate(world, narrate=narrate)


def lead_in(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little superhero who watched over {world.setting.place} "
        f"from the bright edge of the city."
    )


def loves_lotus(world: World, hero: Entity, lotus: Entity) -> None:
    _inc(hero.memes, "love", 1.0)
    world.say(
        f"{hero.id} loved the lotus because its pink petals looked like a tiny crown "
        f"floating on the pond."
    )


def danger_arrives(world: World, hero: Entity, activity: Activity, lotus: Entity) -> None:
    world.say(
        f"One day, {world.setting.crowd} rushed past the water, and a rough breeze began to "
        f"{activity.verb} near the pond."
    )
    world.say(
        f"The lotus would not stay open if the breeze kept going, and {hero.id} could see the risk at once."
    )


def warn(world: World, mentor: Entity, hero: Entity, activity: Activity, lotus: Entity) -> bool:
    pred = predict_failure(world, hero, activity, lotus.id)
    if not pred["damp"]:
        return False
    world.facts["predicted_damp"] = True
    world.say(
        f'"If you rush in once, the lotus will get soaked," {mentor.label} warned. '
        f'"A steady answer will work better."'
    )
    return True


def answer_with_repetition(world: World, hero: Entity, mentor: Entity, activity: Activity) -> None:
    _inc(hero.memes, "resolve", 1.0)
    world.say(
        f"{hero.id} nodded, tucked in {hero.pronoun('possessive')} cape, and chose repetition instead of a single flash."
    )
    world.say(
        f"{hero.pronoun().capitalize()} flew one careful lap, then another, then another, "
        f"keeping the wind in a gentle circle."
    )
    _do_activity(world, hero, activity, narrate=False)


def resolve(world: World, hero: Entity, lotus: Entity, tool: Optional[Tool]) -> None:
    _inc(hero.memes, "joy", 1.0)
    _inc(lotus.meters, "open", 1.0)
    _inc(lotus.meters, "safe", 1.0)
    world.say(
        f"The repeated shield-ride did the trick. The pond settled, the breeze lost its bite, "
        f"and the lotus opened wide again."
    )
    if tool is not None:
        world.say(
            f"{tool.tail.capitalize()}, and the hero stood beside the pond while the lotus shone like a small lamp."
        )
    else:
        world.say(
            f"{hero.id} smiled at the calm water, proud that careful repetition had saved the day."
        )


def tell(setting: Setting, activity: Activity, hero_name: str, hero_type: str, mentor_type: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, label="the coach"))
    lotus = world.add(
        Entity(
            id="lotus",
            type="flower",
            label="lotus",
            phrase="a lotus flower",
            owner=None,
            caretaker=mentor.id,
            meters={"region": "water"},
        )
    )

    lead_in(world, hero)
    loves_lotus(world, hero, lotus)
    world.para()
    danger_arrives(world, hero, activity, lotus)
    warn(world, mentor, hero, activity, lotus)
    answer_with_repetition(world, hero, mentor, activity)
    world.para()
    resolve(world, hero, lotus, None)

    world.facts.update(hero=hero, mentor=mentor, lotus=lotus, activity=activity, setting=setting)
    return world


SETTINGS = {
    "pond": Setting(
        place="the lotus pond",
        skyline="the city skyline",
        crowd="the street crowd",
        affords={"circle"},
    ),
    "roof": Setting(
        place="the rooftop garden",
        skyline="the towers",
        crowd="the rooftop wind",
        affords={"circle"},
    ),
    "courtyard": Setting(
        place="the lantern courtyard",
        skyline="the tall walls",
        crowd="the evening market",
        affords={"circle"},
    ),
}

ACTIVITIES = {
    "circle": Activity(
        id="circle",
        verb="circle",
        gerund="circling",
        risk="wind",
        danger="too much wind",
        zone={"water"},
        keyword="lotus",
        tags={"lotus", "repeat", "wind"},
    ),
}

TOOLS = [
    Tool(
        id="shield",
        label="a bright shield",
        covers={"water"},
        guards={"wind"},
        prep="make three calm shield passes",
        tail="the coach smiled because the shield passes had turned the wind aside",
    )
]

HERO_NAMES = ["Nova", "Sky", "Bright", "Pulse", "Aster", "Comet"]
HERO_TYPES = ["hero", "hero"]
MENTOR_TYPES = ["coach", "captain", "mentor"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    hero_type: str
    mentor_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            combos.append((place, act))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short superhero story for a young child that includes the word "lotus" and shows repetition solving a problem.',
        f"Tell a gentle superhero story where {hero.id} saves a lotus by doing {act.gerund} again and again.",
        f"Write a small heroic story in which repeated careful action helps a lotus stay safe and calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    act = f["activity"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {hero.id}, a little superhero who watched over the lotus at {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} keep doing to help the lotus?",
            answer=f"{hero.id} kept {act.gerund}, again and again, until the water settled down.",
        ),
        QAItem(
            question=f"Why did the coach warn {hero.id} before the rescue?",
            answer="The coach warned that a single rushed try would not be enough, and that repetition would work better.",
        ),
        QAItem(
            question="What changed at the end?",
            answer="The wind calmed, the pond settled, and the lotus opened wide and looked safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lotus?",
            answer="A lotus is a water flower that grows on a pond and opens its petals above the surface.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing something again and again. Sometimes repeating a steady action helps more than doing one big action.",
        ),
        QAItem(
            question="Why can wind make water plants wobble?",
            answer="Wind pushes on leaves and petals, so a water plant can wobble or close up when the air is rough.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="pond", activity="circle", name="Nova", hero_type="hero", mentor_type="coach"),
    StoryParams(place="roof", activity="circle", name="Sky", hero_type="hero", mentor_type="captain"),
    StoryParams(place="courtyard", activity="circle", name="Bright", hero_type="hero", mentor_type="mentor"),
]


def explain_rejection(place: str, activity: str) -> str:
    return f"(No story: {place} cannot host the needed repeated rescue for {activity}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small superhero lotus story world built around repetition."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=sorted(set(HERO_TYPES)))
    ap.add_argument("--mentor-type", choices=sorted(set(MENTOR_TYPES)))
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
    if args.place and args.activity:
        if args.activity not in SETTINGS[args.place].affords:
            raise StoryError(explain_rejection(args.place, args.activity))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        name=args.name or rng.choice(HERO_NAMES),
        hero_type=args.hero_type or "hero",
        mentor_type=args.mentor_type or rng.choice(MENTOR_TYPES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        params.name,
        params.hero_type,
        params.mentor_type,
    )
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
place(pond). place(roof). place(courtyard).
activity(circle).
affords(pond,circle). affords(roof,circle). affords(courtyard,circle).
risk(circle,wind).
zone(circle,water).
prize(lotus). wears(lotus,water).
tool(shield). covers(shield,water). guards(shield,wind).

prize_at_risk(A,P) :- risk(A,R), zone(A,Z), R=wind, Z=water, wears(P,water).
has_fix(A,P) :- prize_at_risk(A,P), tool(T), guards(T,wind), covers(T,water).
valid(Place,A) :- affords(Place,A), has_fix(A,lotus).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk", aid, a.risk))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, c))
        for g in sorted(tool.guards):
            lines.append(asp.fact("guards", tool.id, g))
    lines.append(asp.fact("prize", "lotus"))
    lines.append(asp.fact("wears", "lotus", "water"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity) combos:\n")
        for place, act in combos:
            print(f"  {place:10} {act}")
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
            header = f"### {p.name}: repetition at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
