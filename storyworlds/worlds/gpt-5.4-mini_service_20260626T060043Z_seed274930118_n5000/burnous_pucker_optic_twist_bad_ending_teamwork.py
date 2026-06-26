#!/usr/bin/env python3
"""
A small pirate-tale storyworld with a twist, a bad-ending risk, and a teamwork
turn that keeps the crew together.

This world is built around three seed words:
- burnous
- pucker
- optic

The tale uses a pirate-style setting with a lookout, a stormy coast, and a
problem that only a coordinated crew can handle in time.
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
        if not self.meters:
            self.meters = {"wet": 0.0, "torn": 0.0, "lost": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "teamwork": 0.0, "relief": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pirate", "mate", "deckhand", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    stormy: bool = False
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
    weather: str = ""
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0
MESS_KINDS = {"wet", "torn"}


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                out.append(f"{actor.id}'s {item.label} got {mess}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["teamwork"] = e.memes.get("teamwork", 0.0) + 1
        out.append("The crew leaned closer and started helping one another.")
    return out


CAUSAL_RULES = [
    _r_soak,
    _r_worry,
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get("wet", 0.0) >= THRESHOLD or prize.meters.get("torn", 0.0) >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} cannot host {activity.id}.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little pirate deckhand who never stopped looking toward the sea."
    )


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, especially when the wind made the deck feel like a game."
    )


def show_prize(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label}, and {hero.pronoun()} wore {prize.it()} like a badge."
    )


def arrive(world: World, hero: Entity, crew: Entity, activity: Activity) -> None:
    world.say(
        f"One stormy dusk, {hero.id} and {hero.pronoun('possessive')} crew climbed to the cove lookout."
    )
    world.say(
        f"The air was salty and dark, and {hero.id} could already see the spray where {activity.keyword} would matter."
    )


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb} right away.")


def warn(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.say(
            f'"If you rush out now," {captain.id} said, "your {prize.label} will get {activity.soil}."'
        )


def twist(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"Then came the twist: the glint in the fog was not treasure at all, but a reef biting up from the black water."
    )
    world.say(
        f"{hero.id} gasped, because the pucker in the sail line meant the ship could snag if nobody moved fast."
    )


def teamwork(world: World, hero: Entity, captain: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=captain.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 2
    hero.memes["worry"] = 0.0
    world.say(
        f"{captain.id} pointed one mate to the rope, another to the tiller, and another to {gear_def.prep}."
    )
    world.say(
        f"{hero.id} held the {prize.label}, and together they got through the pucker in the line."
    )
    world.say(
        f"They {gear_def.tail}, and the crew worked as one to keep the ship from the reef."
    )


def bad_ending(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"The ending was still a bad one for the treasure-hunters, because the reef swallowed the chest before anyone could reach it."
    )
    world.say(
        f"But {hero.id} stood steady on deck, {hero.pronoun('possessive')} {prize.label} safe, while the crew counted themselves lucky to be together."
    )


SETTINGS = {
    "cove": Setting(place="the cove lookout", stormy=True, affords={"watch"}),
    "deck": Setting(place="the ship deck", stormy=True, affords={"haul"}),
    "harbor": Setting(place="the harbor pier", stormy=False, affords={"sort"}),
}

ACTIVITIES = {
    "watch": Activity(
        id="watch",
        verb="scan the waves",
        gerund="scanning the waves",
        rush="stare into the fog",
        mess="wet",
        soil="sprayed with salt water",
        zone={"torso"},
        weather="stormy",
        keyword="optic",
        tags={"optic", "sea", "storm"},
    ),
    "haul": Activity(
        id="haul",
        verb="haul the sail",
        gerund="hauling the sail",
        rush="pull the line",
        mess="torn",
        soil="frayed and soaked",
        zone={"torso", "arms"},
        weather="stormy",
        keyword="pucker",
        tags={"pucker", "rope", "storm"},
    ),
    "sort": Activity(
        id="sort",
        verb="sort the crates",
        gerund="sorting the crates",
        rush="move the boxes",
        mess="wet",
        soil="damp and grimy",
        zone={"hands"},
        weather="",
        keyword="burnous",
        tags={"burnous", "harbor"},
    ),
}

PRIZES = {
    "burnous": Prize("burnous", "a long sea-brown burnous", "burnous", "torso"),
    "optic": Prize("optic", "a brass optic spyglass", "optic", "torso"),
    "pucker": Prize("pucker", "a stitched sail pucker patch", "pucker", "torso"),
}

GEAR = [
    Gear("oilcloth", "an oilcloth wrap", {"torso"}, {"wet"}, "wrap the optic in oilcloth", "wrapped the optic in oilcloth"),
    Gear("seamkit", "a seam kit", {"torso"}, {"torn"}, "patch the sail seam", "patched the sail seam"),
    Gear("hood", "a dry hood", {"torso"}, {"wet", "torn"}, "put on a dry hood", "put on a dry hood"),
]

NAMES = ["Mira", "Ned", "Ivy", "Jon", "Tess", "Bo"]
ROLES = ["captain", "mate", "deckhand"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    role: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale storyworld with a twist and a teamwork ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        role=args.role or rng.choice(ROLES),
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=role))
    captain = world.add(Entity(id="Cap", kind="character", type="captain", label="the captain"))
    crew = world.add(Entity(id="Crew", kind="character", type="mate", label="the crew"))
    prize = world.add(Entity(
        id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=captain.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    introduce(world, hero)
    loves_activity(world, hero, activity)
    show_prize(world, hero, prize)
    world.para()
    arrive(world, hero, crew, activity)
    wants(world, hero, activity)
    warn(world, captain, hero, activity, prize)
    twist(world, hero, activity)
    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No reasonable teamwork gear exists for this story.")
    teamwork(world, hero, captain, activity, prize, gear_def)
    bad_ending(world, hero, prize, activity)
    world.facts.update(hero=hero, captain=captain, crew=crew, prize=prize, activity=activity, setting=setting, gear=gear_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short pirate story for a child that includes the word "{act.keyword}".',
        f"Tell about {hero.id}, a pirate who wants to {act.verb} while protecting {prize.phrase}.",
        f"Write a sea story with a twist where teamwork helps the crew, even though the ending is bad for the treasure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, act = f["hero"], f["captain"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do first?",
            answer=f"{hero.id} wanted to {act.verb} first, because the sea looked exciting from the lookout.",
        ),
        QAItem(
            question=f"Why did {captain.label} warn {hero.id} about the {prize.label}?",
            answer=f"{captain.label} warned {hero.id} because the storm could leave the {prize.label} {act.soil}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The glint in the fog was not treasure. It was a reef, and that changed the crew's plan at once.",
        ),
        QAItem(
            question="How did teamwork help the crew?",
            answer=f"They split the jobs, fixed the problem together, and got the ship through the pucker in the line.",
        ),
        QAItem(
            question="What made the ending bad?",
            answer="The treasure chest was lost to the reef, so the ending was bad for the treasure-hunters even though the crew survived.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spyglass used for?",
            answer="A spyglass helps you see faraway things, like ships, rocks, or islands on the horizon.",
        ),
        QAItem(
            question="What is a burnous?",
            answer="A burnous is a loose cloak with a hood that can help keep a person warm or dry.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do different jobs together to reach the same goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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
        lines.append(asp.fact("place", pid))
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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: that prize is not actually at risk in this activity.)"
    return "(No story: no reasonable gear in this world can protect that prize from this activity.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.role)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [
            StoryParams("cove", "watch", "optic", "Mira", "captain"),
            StoryParams("deck", "haul", "pucker", "Ned", "deckhand"),
            StoryParams("harbor", "sort", "burnous", "Ivy", "mate"),
        ]:
            samples.append(generate(p))
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
