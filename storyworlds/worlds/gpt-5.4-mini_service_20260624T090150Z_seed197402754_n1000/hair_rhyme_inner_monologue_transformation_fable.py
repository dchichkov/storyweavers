#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/hair_rhyme_inner_monologue_transformation_fable.py
===============================================================================================================================

A tiny fable-like storyworld about hair, a windy day, a rhyme, an inner
monologue, and a transformation that changes both the world and the protagonist.

Seed tale:
---
A small hare with a shaggy mop of hair wanted to race through a windy meadow.
The wind kept tugging the hair into knots, and the hare felt embarrassed.
A wise tortoise suggested tying the hair with a ribbon before the race.
The hare listened, loved the neat feeling, and discovered that looking after
the hair helped the hare feel brave too.
---

World model:
- Physical meters track wind-tangle, neatness, and shine.
- Emotional memes track shame, courage, relief, and pride.
- The story is driven by a small causal turn:
  wind -> tangled hair -> worried inner monologue -> ribbon -> transformation.

Features:
- Rhyme: short child-friendly rhyme lines appear at the turning points.
- Inner monologue: the protagonist thinks in first person before changing.
- Transformation: hair becomes neat, and the protagonist becomes confident.
- Fable style: concise, gentle, and moral-like.

The script follows the storyworld contract with:
- StoryParams
- registries
- build_parser / resolve_params / generate / emit / main
- a reasonableness gate and inline ASP twin
- asp_facts()
- --verify parity
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

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_m(self, key: str, amount: float) -> None:
        self.meters[key] = self.m(key) + amount

    def add_e(self, key: str, amount: float) -> None:
        self.memes[key] = self.e(key) + amount

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hare", "rabbit", "girl", "boy"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
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
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"any"})


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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "meadow": Setting(place="the meadow", indoor=False, affords={"wind"}),
}

ACTIVITIES = {
    "wind": Activity(
        id="wind",
        verb="run through the wind",
        gerund="running through the wind",
        rush="dash into the windy grass",
        mess="tangled",
        soil="full of tangles",
        zone={"head"},
        weather="breezy",
        keyword="wind",
        tags={"wind", "hair"},
    ),
}

PRIZES = {
    "hair": Prize(
        label="hair",
        phrase="long curly hair",
        type="hair",
        region="head",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="ribbon",
        label="a blue ribbon",
        covers={"head"},
        guards={"tangled"},
        prep="tie the hair with a blue ribbon",
        tail="walked back to the gate to tie the hair with a blue ribbon",
        plural=False,
    ),
]

NAMES = ["Nora", "Mina", "Tess", "Pip", "Lumi", "Ivy"]
TRAITS = ["small", "gentle", "careful", "brave", "quick", "quiet"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


def _act_start(world: World, hero: Entity, act: Activity, prize: Entity) -> None:
    hero.add_m("wind", 1)
    hero.add_e("restless", 1)
    world.zone = set(act.zone)
    world.say(
        f"In {world.setting.place}, {hero.id} loved {act.gerund}, "
        f"for the breeze made the grass dance."
    )
    world.say(
        f"At home, {hero.id} had always cherished {hero.pronoun('possessive')} {prize.label}."
    )


def _inner_monologue(world: World, hero: Entity, act: Activity, prize: Entity) -> None:
    hero.add_e("shame", 1)
    world.say(
        f'{hero.id} felt the wind snag at every strand. '
        f'"I want to {act.verb}, but my {prize.label} will turn into a tumble of knots," '
        f"{hero.pronoun()} thought."
    )


def _rhyme(world: World, hero: Entity, act: Activity) -> None:
    world.say(
        f'Whirl and twirl, little curl; do not make the world a whirl.'
    )
    world.say(
        f"But the wind only sang back and made the hair lift and curl."
    )


def _warn_and_pause(world: World, parent: Entity, hero: Entity, prize: Entity, act: Activity) -> None:
    if hero.e("shame") >= THRESHOLD:
        world.say(
            f'"If you rush on now, your {prize.label} will get {act.soil}," '
            f"said the wise tortoise at the path's bend."
        )
        world.say(
            f"{hero.id} stopped at once and listened."
        )


def _offer_gear(world: World, hero: Entity, act: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(act, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if prize_at_risk(act, prize) and act.mess not in gear_def.guards:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'The tortoise suggested, "{gear_def.prep}."'
    )
    return gear


def _transform(world: World, hero: Entity, prize: Entity, act: Activity, gear: Gear) -> None:
    hero.add_m("neatness", 1)
    hero.add_e("courage", 1)
    hero.memes["shame"] = 0.0
    hero.add_e("pride", 1)
    world.say(
        f'{hero.id} tied the ribbon, and at once the hair settled into a neat little bow.'
    )
    world.say(
        f'Then {hero.id} ran through the wind again, and the tale changed with {hero.pronoun("possessive")} hair.'
    )
    world.say(
        f'No more wild knots, no more worried thoughts; {hero.id} felt bright as morning dew.'
    )


def _finish(world: World, hero: Entity, prize: Entity, act: Activity) -> None:
    world.say(
        f"By the end, {hero.id}'s {prize.label} stayed neat, and {hero.id} was no longer shy."
    )
    world.say(
        f"That is how the smallest ribbon helped the smallest courage grow."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str) -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(Entity(id=hero_name, kind="character", type="hare"))
    parent = world.add(Entity(id="Tortoise", kind="character", type="tortoise", label="the tortoise"))
    prize = world.add(Entity(
        id="hair",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
    ))

    _act_start(world, hero, activity, prize)
    world.para()
    _inner_monologue(world, hero, activity, prize)
    _rhyme(world, hero, activity)
    _warn_and_pause(world, parent, hero, prize, activity)
    gear = _offer_gear(world, hero, activity, prize)
    if gear is not None:
        _transform(world, hero, prize, activity, gear)
        _finish(world, hero, prize, activity)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=gear is not None,
    )
    return world


KNOWLEDGE = {
    "hair": [(
        "What is hair?",
        "Hair is the soft strands that grow on the heads of people and animals."
    )],
    "wind": [(
        "What can wind do to hair?",
        "Wind can blow hair around and make it tangle or flutter."
    )],
    "ribbon": [(
        "What is a ribbon for?",
        "A ribbon can tie hair, gifts, or other things together in a neat way."
    )],
    "tangle": [(
        "What is a tangle?",
        "A tangle is when threads or hair twist together into a messy knot."
    )],
    "neatness": [(
        "What does neat mean?",
        "Neat means tidy, smooth, and in a good order."
    )],
}

KNOWLEDGE_ORDER = ["hair", "wind", "tangle", "ribbon", "neatness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short fable for a young child about {hero.id}, {act.gerund}, and a ribbon that saves {hero.pronoun("possessive")} {prize.label}.',
        f'Tell a gentle rhyme-story in which {hero.id} thinks, worries, and then grows brave in the wind.',
        f'Write a tiny moral tale about hair, a windy meadow, and a transformation from messy to neat.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, act = f["hero"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the meadow?",
            answer=f"{hero.id} wanted to {act.verb}, even though the wind was tugging at {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} think might happen to the {prize.label}?",
            answer=f"{hero.id} thought the {prize.label} would get {act.soil} if {hero.pronoun()} kept rushing ahead.",
        ),
        QAItem(
            question=f"How did the tortoise help {hero.id}?",
            answer="The tortoise suggested tying the hair with a ribbon so the wind would stop making it wild.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What changed after the ribbon was tied?",
            answer=f"The hair became neat, and {hero.id} became braver and happier.",
        ))
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} running happily through the wind, with neat hair and a proud heart.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", activity="wind", prize="hair", name="Nora", trait="gentle"),
    StoryParams(place="meadow", activity="wind", prize="hair", name="Mina", trait="brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the wind would not touch the prize enough to make a real warning.)"
    if select_gear(activity, prize) is None:
        return "(No story: there is no gear that honestly helps in this situation.)"
    return "(No story: the requested combination is not reasonable.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
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
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable storyworld about hair, wind, rhyme, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name)
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
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
