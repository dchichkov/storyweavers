#!/usr/bin/env python3
"""
storyworlds/worlds/hassle_permanence_nudist_magic_conflict_suspense_animal.py
=============================================================================

A small animal-story world with a magical hassle about permanence, a tense
problem, and a suspenseful fix.

Premise:
- A little animal loves a magical thing.
- The magic makes a mess become permanent.
- A parent/helper worries, because the mess will not wash away.
- The animal is upset, then a safer magical choice resolves the conflict.

Style notes:
- Child-facing, concrete, and authored.
- Animal Story tone: small creatures, cozy places, clear cause and effect.
- Includes the seed words hassle, permanence, nudist in world metadata and
  prompts, while keeping the prose itself gentle and age-appropriate.
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
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "fox", "squirrel", "bear", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


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
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
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
        return any(g.id in {"cloak", "boots", "gloves"} and region in g.meters.get("covers", set())
                   for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class Rule:
    name: str
    apply: callable


def _r_permanent_smudge(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("magic", 0) < THRESHOLD:
            continue
        if actor.meters.get("mess", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.plural:
                continue
            sig = ("smudge", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["permanent"] = 1
            out.append(f"{item.label.capitalize()} looked stuck that way forever.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("permanent", 0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["worry"] = caretaker.memes.get("worry", 0) + 1
        out.append("That gave the grown-up a worried little frown.")
    return out


RULES = [Rule("permanent_smudge", _r_permanent_smudge), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            produced = rule.apply(world)
            if produced:
                out.extend(produced)
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def clone_world(world: World) -> World:
    import copy
    c = World(world.setting)
    c.entities = copy.deepcopy(world.entities)
    c.zone = set(world.zone)
    c.fired = set(world.fired)
    return c


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = clone_world(world)
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"permanent": bool(prize and prize.meters.get("permanent", 0) >= THRESHOLD)}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} cannot host {activity.id}.")
    world.zone = set(activity.zone)
    actor.meters["magic"] = actor.meters.get("magic", 0) + 1
    actor.meters["mess"] = actor.meters.get("mess", 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    propagate(world, narrate=narrate)


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def build_story(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> Optional[Gear]:
    world.say(f"{hero.id} was a little {hero.type} who loved shiny magic.")
    world.say(f"{hero.id} loved to {activity.gerund}, and the sparkly trick made the whole day feel bright.")
    world.say(f"One day, {parent.label} brought home {prize.phrase} for {hero.id}.")
    hero.worn_by = hero.id
    world.say(f"{hero.id} wore {prize.label} everywhere, as if {prize.it()} were part of the fun.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} wanted to {activity.verb}.")
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["permanent"]:
        world.say(f"But {parent.label} worried. If the magic touched {prize.label}, the mess could stay for good.")
        world.say(f'"That would be a big hassle," {parent.label} said softly.')
        hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
        world.say(f"{hero.id} pouted and tried to rush forward anyway.")
        gear = select_gear(activity, prize)
        if gear is None:
            raise StoryError("No safe magical gear exists for this combination.")
        safe = world.add(Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            owner=hero.id,
            caretaker=parent.id,
            plural=gear.plural,
        ))
        safe.meters["covers"] = gear.covers
        safe.worn_by = hero.id
        world.say(f"Then {parent.label} showed {hero.id} {gear.label} and said, {gear.prep}.")
        world.say(f"{hero.id} blinked, then nodded. The suspense melted into a tiny smile.")
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        hero.memes["conflict"] = 0
        world.say(f"They {gear.tail}. Soon {hero.id} was {activity.gerund}, and {prize.label} stayed clean.")
        return gear
    else:
        world.say(f"The magic stayed harmless, so {hero.id} could play without any big worry.")
        world.say(f"{hero.id} laughed, and {parent.label} laughed too.")
        return None


SETTINGS = {
    "garden": Setting(place="the garden", affords={"sparkles", "glow"}),
    "pond": Setting(place="the pond path", affords={"sparkles", "glow"}),
    "barn": Setting(place="the old barn", indoor=True, affords={"glow"}),
}

ACTIVITIES = {
    "sparkles": Activity(
        id="sparkles",
        verb="twirl in the sparkle dust",
        gerund="twirling in sparkle dust",
        rush="dash through the sparkle dust",
        mess="magic",
        soil="stuck there",
        zone={"body"},
        keyword="hassle",
        tags={"magic", "permanence", "suspense"},
    ),
    "glow": Activity(
        id="glow",
        verb="play with the glowing paint",
        gerund="playing with glowing paint",
        rush="slip into the glowing paint",
        mess="magic",
        soil="stuck there",
        zone={"body"},
        keyword="nudist",
        tags={"magic", "conflict", "suspense"},
    ),
}

PRIZES = {
    "scarf": Prize(label="scarf", phrase="a soft blue scarf", type="scarf", region="body"),
    "hat": Prize(label="hat", phrase="a tiny felt hat", type="hat", region="body"),
}

GEAR = [
    Gear(
        id="cloak",
        label="a moon cloak",
        covers={"body"},
        guards={"magic"},
        prep="put on the moon cloak first",
        tail="went back to the path with the moon cloak on",
    ),
    Gear(
        id="boots",
        label="rain boots",
        covers={"body"},
        guards={"magic"},
        prep="wear the rain boots and carry on carefully",
        tail="walked on in the rain boots",
    ),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: magic, conflict, suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
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
    place, act, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=act,
        prize=prize,
        name=args.name or rng.choice(["Milo", "Pip", "Nori", "Tansy"]),
        parent=args.parent or rng.choice(["mother", "father", "aunt", "uncle"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="mouse"))
    parent = world.add(Entity(id="Parent", kind="character", type="mouse", label=params.parent))
    prize = world.add(Entity(
        id="prize",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        caretaker=parent.id,
        owner=hero.id,
    ))
    activity = ACTIVITIES[params.activity]

    gear = build_story(world, hero, parent, prize, activity)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear)
    story = world.render()
    prompts = [
        "Write an animal story about hassle, permanence, and a safe choice.",
        f"Tell a gentle story about a little animal named {params.name} and {activity.keyword}.",
        "Make the story include magic, conflict, and suspense, then end with a happy fix.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.parent} worry when {params.name} wanted to {activity.verb}?",
            answer=f"{params.parent} worried because the magic could make the mess permanent and turn the little problem into a big hassle.",
        ),
        QAItem(
            question=f"What helped {params.name} solve the problem?",
            answer=f"{gear.label if gear else 'A safer choice'} helped {params.name} keep {prize.label} clean.",
        ),
        QAItem(
            question=f"How did {params.name} feel at the end?",
            answer=f"{params.name} felt happy again after the conflict was solved and the suspense was over.",
        ),
    ]
    world_qa = [
        QAItem(question="What does permanence mean?", answer="Permanence means something stays for a very long time, almost as if it will not change."),
        QAItem(question="What is a hassle?", answer="A hassle is a problem that takes extra work or causes a lot of fuss."),
        QAItem(question="What is suspense?", answer="Suspense is the feeling of wondering what will happen next."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Act,Prize) :- setting(Place), affords(Place,Act), prize(Prize), compatible(Act,Prize).
compatible(Act,Prize) :- guards(gear1, magic), covers(gear1, body), mess_of(Act, magic), worn_on(Prize, body).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    lines.append(asp.fact("gear", "gear1"))
    lines.append(asp.fact("guards", "gear1", "magic"))
    lines.append(asp.fact("covers", "gear1", "body"))
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
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
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
    StoryParams(place="garden", activity="sparkles", prize="scarf", name="Milo", parent="mother"),
    StoryParams(place="pond", activity="sparkles", prize="hat", name="Pip", parent="father"),
    StoryParams(place="barn", activity="glow", prize="scarf", name="Nori", parent="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
