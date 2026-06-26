#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/flimsy_flounder_surprise_humor_magic_animal_story.py
==============================================================================================================

A small animal-story world about a timid little flounder, a flimsy plan,
a surprising magic turn, and a humorous happy ending.

The seed suggests the words "flimsy" and "flounder" and the features
Surprise, Humor, and Magic. This world builds a tiny, state-driven story
around an animal cast at a pond-side fair.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"flounder", "fish", "animal"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pond fair"
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_fumble(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character" or actor.meters.get("wobble", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.owner != actor.id or item.region not in world.zone or item.protective:
                continue
            sig = ("fumble", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["tumbled"] = item.meters.get("tumbled", 0.0) + 1
            actor.memes["embarrassed"] = actor.memes.get("embarrassed", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} tipped sideways with a tiny flop.")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character" or actor.memes.get("embarrassed", 0.0) < THRESHOLD:
            continue
        sig = ("laugh", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["humor"] = actor.memes.get("humor", 0.0) + 1
        out.append(f"Even the reeds seemed to giggle a little.")
    return out


CAUSAL_RULES = [
    _r_fumble,
    _r_laugh,
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


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This setting cannot host that activity.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.meters["wobble"] = actor.meters.get("wobble", 0.0) + 1
    actor.memes["excitement"] = actor.memes.get("excitement", 0.0) + 1
    propagate(world, narrate=narrate)


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "tumbled": prize.meters.get("tumbled", 0.0) >= THRESHOLD,
        "humor": actor.memes.get("humor", 0.0),
    }


SETTING = Setting(place="the pond fair", affords={"jump", "tug", "splash", "float"})

ACTIVITIES = {
    "float": Activity(
        id="float",
        verb="float across the lily path",
        gerund="floating across the lily path",
        rush="wobble toward the lily path",
        mess="wet",
        soil="all damp",
        zone={"body"},
        keyword="flounder",
        tags={"water", "humor"},
    ),
    "splash": Activity(
        id="splash",
        verb="splash under the lanterns",
        gerund="splashing under the lanterns",
        rush="flap toward the lanterns",
        mess="wet",
        soil="soaked",
        zone={"body"},
        keyword="surprise",
        tags={"water", "surprise"},
    ),
    "jump": Activity(
        id="jump",
        verb="jump the little gap",
        gerund="jumping the little gap",
        rush="flounder toward the gap",
        mess="muddy",
        soil="mud-spattered",
        zone={"body"},
        keyword="humor",
        tags={"land", "humor"},
    ),
    "tug": Activity(
        id="tug",
        verb="tug the ribbon bell",
        gerund="tugging the ribbon bell",
        rush="twitch toward the ribbon bell",
        mess="wet",
        soil="drenched",
        zone={"body"},
        keyword="magic",
        tags={"magic", "surprise"},
    ),
}

PRIZES = {
    "cap": Prize(label="cap", phrase="a tiny blue cap", type="cap", region="body"),
    "banner": Prize(label="banner", phrase="a bright parade banner", type="banner", region="body"),
    "shell": Prize(label="shell", phrase="a shiny shell crown", type="shell", region="body"),
}

GEAR = [
    Gear(
        id="leaf_boat",
        label="a leaf boat",
        covers={"body"},
        guards={"wet", "muddy"},
        prep="set sail in a leaf boat",
        tail="drifted back in the leaf boat",
    ),
    Gear(
        id="bubble_hat",
        label="a bubble hat",
        covers={"body"},
        guards={"wet"},
        prep="wear a bubble hat first",
        tail="bobbed along in the bubble hat",
    ),
]

GUEST_NAMES = ["Nori", "Finn", "Mina", "Pip", "Moss", "Bram"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in {"pond_fair": SETTING}.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def build_story(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="flounder", label=params.name))
    parent = world.add(Entity(id="Caretaker", kind="character", type="animal", label="old heron"))
    prize = world.add(Entity(
        id="Prize",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=PRIZES[params.prize].region,
    ))
    activity = ACTIVITIES[params.activity]

    world.say(f"{hero.id} was a little flounder with a brave heart and a wobbly tail.")
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}; it made the pond fair feel like a game.")
    world.say(f"One morning, {parent.label} brought {hero.id} {prize.phrase}, and {hero.id} wore {prize.label} like a treasure.")

    world.para()
    world.say(f"At the pond fair, {hero.id} wanted to {activity.verb}.")
    pred = predict(world, hero, activity, prize.id)
    if pred["tumbled"]:
        world.say(f"'{prize.phrase} might get wet,' warned the {parent.label}.")
    world.say(f"{hero.id} tried anyway and began to {activity.rush}.")
    do_activity(world, hero, activity, narrate=True)

    world.para()
    world.say(f"Then something surprising happened: a glow rose from under a lily pad.")
    world.say(f"It was a tiny moon-spark, and it whispered a magic joke that made everyone snort.")
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1

    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No reasonable gear for this story.")
    world.say(f"The {parent.label} smiled and offered {gear.label}.")
    world.say(f"'{gear.prep},' said the heron, 'and then you can still {activity.verb}.'")

    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(f"{hero.id} giggled, nodded, and agreed.")
    world.say(f"They {gear.tail}, and {hero.id} was soon {activity.gerund}, while {prize.label} stayed dry and bright.")
    world.say(f"At the end, the moon-spark twinkled above the pond, and {hero.id} laughed so hard that a bubble popped on the nose of the heron.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize, activity = f["hero"], f["prize"], f["activity"]
    return [
        f'Write a short animal story for a young child about a flounder named {hero.id}, a flimsy plan, and a magic surprise.',
        f"Tell a humorous story where {hero.id} wants to {activity.verb} but must protect {prize.phrase}.",
        f'Write a gentle pond tale that uses the words "flimsy" and "flounder" and ends with a magical happy laugh.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, activity, gear = f["hero"], f["prize"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little flounder who loved to {activity.verb}.",
        ),
        QAItem(
            question=f"What worried the heron about {prize.label}?",
            answer=f"The heron worried that {prize.phrase} would get wet if {hero.id} went to {activity.verb}.",
        ),
        QAItem(
            question=f"What surprising thing happened at the pond fair?",
            answer="A tiny moon-spark rose from under a lily pad and brought a magic joke that made everyone laugh.",
        ),
        QAItem(
            question=f"How did {hero.id} finally play without ruining {prize.label}?",
            answer=f"They used {gear.label}, so {hero.id} could keep {prize.label} safe while still {activity.gerund}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does flimsy mean?",
            answer="Flimsy means weak, thin, or not very sturdy.",
        ),
        QAItem(
            question="What is a flounder?",
            answer="A flounder is a flat fish that lives in water and can seem wobbly when it moves.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you do not know it is coming.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people smile or laugh.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special story power that can make impossible things happen in a playful way.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="pond_fair", activity="float", prize="cap", name="Nori"),
    StoryParams(place="pond_fair", activity="tug", prize="shell", name="Finn"),
    StoryParams(place="pond_fair", activity="jump", prize="banner", name="Mina"),
]


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "pond_fair")]
    for a in sorted(SETTING.affords):
        lines.append(asp.fact("affords", "pond_fair", a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for z in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, z))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with flimsy plans, flounders, magic, and humor.")
    ap.add_argument("--place", choices=["pond_fair"])
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
        raise StoryError("(No valid combination matches the given options.)")
    _, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(GUEST_NAMES)
    return StoryParams(place="pond_fair", activity=activity, prize=prize, name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
        triples = valid_combos_asp()
        print(f"{len(triples)} compatible combos:\n")
        for place, act, prize in triples:
            print(f"  {place:10} {act:8} {prize:8}")
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
            header = f"### {p.name}: {p.activity} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
