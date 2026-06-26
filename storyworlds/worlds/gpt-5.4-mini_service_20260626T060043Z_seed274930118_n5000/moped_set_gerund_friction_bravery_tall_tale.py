#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/moped_set_gerund_friction_bravery_tall_tale.py
==============================================================================================================

A small, self-contained story world for a tall-tale style moped adventure:
a brave rider, a stubborn machine, and the friction that must be handled
before the journey can soar.

The seed words guiding this world are moped, set-gerund, friction.
The world leans into bravery and a larger-than-life, child-friendly tall tale
tone while staying state-driven and constraint-checked.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    ridden_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
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
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    friction: str
    weather: str
    zone: set[str] = field(default_factory=set)
    keyword: str = "moped"


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
    prep: str
    tail: str
    fixes: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.weather: str = ""
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
        clone = World(self.setting)
        clone.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes),
                                     traits=list(v.traits)) for k, v in self.entities.items()}
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def _add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _add_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for rider in world.characters():
        if rider.meters.get("friction", 0.0) >= THRESHOLD and not rider.memes.get("brave_fix", 0.0):
            sig = ("slow", rider.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append(f"The moped shuddered and slowed as if the road had tied a knot in its boots.")
        if rider.meters.get("friction", 0.0) >= THRESHOLD and rider.meters.get("oil", 0.0) >= THRESHOLD:
            sig = ("free", rider.id)
            if sig not in world.fired:
                world.fired.add(sig)
                rider.meters["friction"] = 0.0
                out.append(f"The oil slipped into the joints, and the stubborn friction lost its grip.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict(world: World, rider: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(rider.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "stuck": sim.get(rider.id).meters.get("friction", 0.0) >= THRESHOLD,
        "lost": prize.meters.get("dust", 0.0) >= THRESHOLD,
    }


def do_activity(world: World, rider: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} cannot host {activity.verb}.")
    rider.meters["friction"] = rider.meters.get("friction", 0.0) + 1.0
    rider.memes["joy"] = rider.memes.get("joy", 0.0) + 1.0
    world.zone = set(activity.zone)
    _propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         name: str = "Nora", rider_type: str = "girl", helper_type: str = "father",
         trait: str = "brave") -> World:
    world = World(setting)
    world.weather = activity.weather
    rider = world.add(Entity(id=name, kind="character", type=rider_type, traits=["little", trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    prize = world.add(Entity(id="cargo", type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=rider.id, caretaker=helper.id, plural=prize_cfg.plural,
                             meters={"dust": 0.0}))

    world.say(f"{rider.id} was a little {trait} {rider_type} who loved the road and the long singing hum of a {activity.keyword}.")
    world.say(f"{rider.pronoun('possessive').capitalize()} prize was {prize_cfg.phrase}, and {rider.id} rode with it like a star on a kite string.")
    world.para()

    world.say(f"One day at {setting.place}, {rider.id} wanted to {activity.verb}.")
    world.say(f"But the {activity.friction} of the climb and the lane made the moped feel as stubborn as a mule in boots.")
    if predict(world, rider, activity, prize.id)["stuck"]:
        _add_meme(rider, "bravery", 1.0)
        world.say(f'{rider.id} took a deep breath and said, "I am brave enough for this hill."')
        _add_meme(rider, "fear", 1.0)
        world.say(f"Still, the wheels creaked and the moped gave a lopsided groan, as if the whole road were asking for a smarter plan.")
        world.say(f"{helper.label} saw the trouble and reached for a small tin of oil.")
        _add_meter(rider, "oil", 1.0)
        _add_meme(rider, "brave_fix", 1.0)
        world.say(f'"How about we set-gerund the gears," {helper.label} said, meaning they would set the chain right and let the story keep rolling.')
        _propagate(world)
        world.para()
        world.say(f"They rubbed oil on the chain, and the friction let go at last.")
        world.say(f"Then {rider.id} zoomed up the hill, {activity.gerund}, with the prize steady and the wind singing around {rider.pronoun('object')}.")
        world.say(f"By sunset, the moped was purring like a contented cat, and even the tall weeds seemed to bow to {rider.id}'s bravery.")
    else:
        world.say(f"The road was kind that day, and {rider.id} rode on without a worry.")
        world.say(f"By the time the sun tilted low, {rider.id} was {activity.gerund} with a grin wide enough to cross the county.")

    world.facts.update(hero=rider, helper=helper, prize=prize, activity=activity, setting=setting)
    return world


SETTINGS = {
    "hill": Setting(place="the cedar hill", affords={"ride"}),
    "road": Setting(place="the long ribbon road", affords={"ride"}),
    "fair": Setting(place="the county fair lane", affords={"ride"}),
}

ACTIVITIES = {
    "ride": Activity(
        id="ride",
        verb="ride the moped up the hill",
        gerund="riding the moped",
        rush="dash off on the moped",
        friction="friction",
        weather="sunny",
        zone={"wheel", "chain"},
        keyword="moped",
    ),
}

PRIZES = {
    "parcel": Prize(label="parcel", phrase="a wrapped parcel with a red ribbon", region="rack"),
    "milk": Prize(label="milk jug", phrase="a glass milk jug in a wire crate", region="rack"),
    "lantern": Prize(label="lantern", phrase="a bright tin lantern", region="handlebars"),
}

GEAR = [
    Gear(id="oil", label="oil", prep="pour oil on the chain", tail="the chain would hum again", fixes={"friction"}),
]

GIRL_NAMES = ["Nora", "Mabel", "Lulu", "Hazel", "June"]
BOY_NAMES = ["Otis", "Cal", "Benny", "Eli", "Floyd"]
TRAITS = ["brave", "bold", "plucky", "fearless", "steadfast"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, pr) for p, s in SETTINGS.items() for a in s.affords for pr in PRIZES]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: this moped tale needs a prize that can ride along and a friction problem worth solving.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale moped story world with bravery and friction.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    if args.place:
        place = args.place
    if args.activity:
        activity = args.activity
    if args.prize:
        prize = args.prize
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale about a brave child and a moped, using the word "{f["activity"].keyword}".',
        f"Tell a child-friendly story where {f['hero'].id} faces friction on a moped and finds a brave fix with {f['helper'].label}.",
        f'Create a funny, big-hearted moped adventure that ends with the chain running smooth again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, p, a = f["hero"], f["prize"], f["activity"]
    helper = f["helper"].label
    return [
        QAItem(
            question=f"What did {h.id} want to do at {world.setting.place}?",
            answer=f"{h.id} wanted to {a.verb}.",
        ),
        QAItem(
            question=f"What made the moped slow down?",
            answer=f"The friction on the climb and the chain made the moped slow down.",
        ),
        QAItem(
            question=f"How did {helper} help {h.id}?",
            answer=f"{helper.capitalize()} brought oil and helped set the chain right so the moped could roll again.",
        ),
        QAItem(
            question=f"What did {h.id}'s bravery change?",
            answer=f"{h.id}'s bravery helped {h.id} keep going until the friction was fixed and the ride could continue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friction?",
            answer="Friction is the rubbing force that makes moving parts slow down or warm up.",
        ),
        QAItem(
            question="What does oil do for a chain?",
            answer="Oil helps moving parts slide more easily, so there is less friction.",
        ),
        QAItem(
            question="What is a moped?",
            answer="A moped is a small motorized bike that can carry a rider along roads and hills.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary without giving up.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
friction_problem(H) :- hero(H), friction(H), brave(H).
needs_oil(H) :- friction_problem(H).
resolved(H) :- needs_oil(H), gear(oil).
valid_story(P,A,R) :- place(P), activity(A), prize(R), valid_combo(P,A,R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("friction", a))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    lines.append(asp.fact("gear", "oil"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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
    StoryParams(place="hill", activity="ride", prize="parcel", name="Nora", gender="girl", helper="father", trait="brave"),
    StoryParams(place="road", activity="ride", prize="lantern", name="Otis", gender="boy", helper="mother", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
