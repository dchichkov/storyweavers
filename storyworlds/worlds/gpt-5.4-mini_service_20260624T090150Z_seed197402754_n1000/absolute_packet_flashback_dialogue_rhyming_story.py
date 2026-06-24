#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/absolute_packet_flashback_dialogue_rhyming_story.py
==============================================================================================

A tiny storyworld about a child, an absolute rule, and a packet that must stay
safe. The story uses a flashback and dialogue, and the prose aims for a gentle
rhyming-story feel.

Seed tale sketch:
---
Mina loved to skip along the garden lane with her little paper packet. One day
her mother warned her that rain could soak it right through. Mina flashed back
to the time her packet had torn and the tiny seeds had spilled. So she chose a
wax pouch, kept the packet dry, and still danced home in the drizzle.

The world model keeps track of:
- a child and a parent,
- a packet of seeds,
- wetness risk from rain,
- a protective fix that actually covers the packet,
- a flashback memory that changes the child's choice,
- dialogue that resolves the tension.

The prose is generated from state, not from a frozen paragraph template.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("wet", "torn", "safe"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "memory", "relief", "fear"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool = True
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
    weather: str = "rainy"
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
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
        self.weather: str = ""
        self.flashback: bool = False
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self):
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity):
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.weather = self.weather
        w.flashback = self.flashback
        w.paragraphs = [[]]
        return w


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("wet", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet in the rain.")
    return out


def _r_safe(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.protective and item.worn_by and item.meters["safe"] < THRESHOLD:
            sig = ("safe", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["safe"] += 1
            out.append(f"The cover kept {item.label} safe and sound.")
    return out


CAUSAL_RULES = [_r_wet, _r_safe]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters["wet"] >= THRESHOLD


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("That place cannot support that action.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    propagate(world, narrate=narrate)


def rhyme_join(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def intro(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} with a bright, bold hop, "
        f"and a heart that could not easily stop."
    )


def loves(world: World, child: Entity, activity: Activity, prize: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} loved to {activity.verb} with a merry little twirl, "
        f"and {child.pronoun('possessive')} {prize.label} was the loveliest swirl."
    )


def bought(world: World, parent: Entity, child: Entity, prize: Entity) -> None:
    world.say(
        f"One day {parent.pronoun('subject') if parent.type != 'mother' else 'she'} bought {child.pronoun('object')} "
        f"{prize.phrase}, with seeds tucked inside so neat."
    )


def remembers(world: World, child: Entity, prize: Entity) -> None:
    child.memes["memory"] += 1
    world.flashback = True
    world.say(
        f"Then came a flashback, quick as a spark: once {prize.label} had ripped in the dark."
    )
    world.say(
        f"The tiny seeds fell out with a patter and plink, and {child.id} had cried, "
        f'“Oh no, not a shrink!”'
    )


def arrive(world: World, child: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"On a rainy day, {child.id} and {parent.id} went to {world.setting.place}, "
        f"where puddles could sing and mud could make a trace."
    )


def wants(world: World, child: Entity, activity: Activity) -> None:
    child.memes["worry"] += 1
    world.say(
        f'{child.id} said, "I want to {activity.verb}!" with a skip and a swing, '
        f'but {child.pronoun("possessive")} pocket felt flimsy, a not-so-safe thing.'
    )


def warn(world: World, parent: Entity, child: Entity, activity: Activity, prize: Entity) -> bool:
    if not predict_damage(world, child, activity, prize.id):
        return False
    world.say(
        f'{parent.id} said, "An absolute rule is easy to see: '
        f'keep {child.pronoun("possessive")} {prize.label} dry, and it will stay free."'
    )
    return True


def answer(world: World, child: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f'{child.id} replied, "I remember the tear and the sad little fall; '
        f"let's find a dry helper that can cover it all!""
    )


def fix(world: World, child: Entity, parent: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = None
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            gear = g
            break
    if gear is None:
        return None
    g = world.add(Entity(id=gear.id, type="thing", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    g.worn_by = child.id
    if predict_damage(world, child, activity, prize.id):
        g.worn_by = None
        del world.entities[g.id]
        return None
    world.say(
        f'{parent.id} smiled and said, "{gear.prep}."'
    )
    return gear


def resolve(world: World, child: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f'{child.id} grinned and gave {parent.pronoun("object")} a squeeze so tight, '
        f'for the safe little plan felt perfectly right.'
    )
    world.say(
        f"They {gear.tail}, and {child.id} kept {prize.label} tucked and dry; "
        f"then danced through the drizzle beneath the gray sky."
    )
    world.say(
        f"At day’s end the packet was dry, snug, and sound, "
        f"and {child.id} went home with a bounce in the ground."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    world.weather = activity.weather
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="packet", type="packet", label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))

    intro(world, child)
    loves(world, child, activity, prize)
    bought(world, parent, child, prize)
    remembers(world, child, prize)
    world.para()
    arrive(world, child, parent, activity)
    wants(world, child, activity)
    warn(world, parent, child, activity, prize)
    answer(world, child, parent, activity)
    world.para()
    gear = fix(world, child, parent, activity, prize)
    if gear:
        resolve(world, child, parent, activity, prize, gear)

    world.facts.update(hero=child, parent=parent, prize=prize, activity=activity, gear=gear, setting=setting)
    return world


SETTINGS = {
    "lane": Setting(place="the garden lane", outdoors=True, affords={"rain_walk"}),
    "porch": Setting(place="the porch", outdoors=True, affords={"rain_walk"}),
    "market": Setting(place="the market path", outdoors=True, affords={"rain_walk"}),
}

ACTIVITIES = {
    "rain_walk": Activity(
        id="rain_walk",
        verb="dance in the rain",
        gerund="dancing in the rain",
        rush="race through the raindrops",
        mess="wet",
        soil="soaked",
        zone={"hands", "torso"},
        weather="rainy",
        keyword="rain",
        tags={"rain", "wet"},
    )
}

PRIZES = {
    "packet": Prize(
        id="packet",
        label="packet",
        phrase="a paper packet of seeds",
        region="hands",
    )
}

GEAR = [
    Gear(
        id="wax_pouch",
        label="a wax pouch",
        covers={"hands"},
        guards={"wet"},
        prep="put the packet in a wax pouch first",
        tail="slipped the packet into the wax pouch",
    )
]

NAMES = ["Mina", "Pip", "Nora", "Luca", "Tia", "Jo"]
TRAITS = ["brave", "cheery", "curious", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and any(act.mess in g.guards and prize.region in g.covers for g in GEAR):
                    combos.append((place, act_id, prize_id))
    return combos


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a rhyming story about a child named {hero.id}, an absolute rule, and a {prize.label}.',
        f'Tell a gentle flashback story where {hero.id} wants to {act.verb} but {parent.id} worries about the {prize.label}.',
        f'Write a child-friendly dialogue story using the words "absolute" and "packet".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act, gear = f["hero"], f["parent"], f["prize"], f["activity"], f["gear"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the rain?",
            answer=f"{hero.id} wanted to {act.verb}, even though {parent.id} worried about the {prize.label}.",
        ),
        QAItem(
            question=f"Why did {parent.id} call the rule about the {prize.label} an absolute rule?",
            answer=f"{parent.id} called it an absolute rule because the {prize.label} had to stay dry and safe.",
        ),
        QAItem(
            question=f"What flashback did {hero.id} remember?",
            answer=f"{hero.id} remembered a time when the {prize.label} tore and the seeds spilled out.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.id} keep the {prize.label} safe?",
            answer=f"They used {gear.label} first, so the {prize.label} stayed dry while {hero.id} played.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a packet?",
            answer="A packet is a small package or pouch that holds something inside it.",
        ),
        QAItem(
            question="What does absolute mean?",
            answer="Absolute means complete or total, with no parts left out.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly looks back at something that happened before.",
        ),
        QAItem(
            question="Why do people use a pouch in the rain?",
            answer="People use a pouch in the rain to help keep paper or tiny items dry.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  flashback={world.flashback}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about an absolute rule and a packet.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [StoryParams("lane", "rain_walk", "packet", "Mina", "girl", "mother", "curious")]:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
