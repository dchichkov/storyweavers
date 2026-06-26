#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/psycho_marina_kindness_magic_dialogue_heartwarming.py
============================================================================================================

A small, self-contained story world set at a marina. The simulated domain is
built around kindness, a little bit of magic, and gentle dialogue: a child
wants to enjoy the docks and the boats, but worries about getting a favorite
prize wet in the sea spray. A kind parent offers a magical, practical fix so
the child can keep playing and still end with a warm, safe feeling.

The seed word "psycho" is kept as a prompt/world tag only; the child-facing
story remains heartwarming and concrete.
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

SEED_WORD = "psycho"
THRESHOLD = 1.0
WET_MESS = "wet"


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
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

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Marina:
    place: str = "the marina"
    affords: set[str] = field(default_factory=lambda: {"sea_spray", "tide_walk", "dock_visit"})


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
    keyword: str
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
    magical: bool = False
    magic_line: str = ""


class World:
    def __init__(self, setting: Marina) -> None:
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


def _soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meter(WET_MESS) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters[WET_MESS] = item.meter(WET_MESS) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet.")
    return out


CAUSAL_RULES = [_soak]


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


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meter(WET_MESS) >= THRESHOLD}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This marina scene cannot support that activity.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meter(activity.mess) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved the marina's shiny boats and quiet ropes.")


def love_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] = hero.meme("joy") + 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, because the water sounded soft and friendly.")


def buy_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.id}'s {parent.label} bought {hero.pronoun('object')} {prize.phrase}.")


def love_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.meme("love") + 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One breezy day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say("The waves were busy, and tiny drops of water sparkled in the air.")


def want(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.meme("desire") + 1
    world.say(f"{hero.id} wanted to {activity.verb} right away.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," {parent.label} said.')
    return True


def magic_offer(world: World, parent: Entity, hero: Entity, prize: Entity, gear: Gear) -> Gear:
    item = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    item.worn_by = hero.id
    world.say(f'"I have a little magic for that," {parent.label} said.')
    if gear.magic_line:
        world.say(gear.magic_line)
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.meme("joy") + 1
    hero.memes["love"] = hero.meme("love") + 1
    world.say(f"{hero.id} smiled and hugged {hero.pronoun('possessive')} {parent.label}.")
    world.say(
        f'Then they used the {gear.label}, and {hero.id} could {activity.verb} while {prize.label} stayed dry.'
    )
    world.say(
        f"At the end, the marina felt even warmer, because {hero.id} was laughing beside the boats."
    )


def tell(setting: Marina, activity: Activity, prize_cfg: Prize, *, hero_name: str, hero_type: str,
         parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"joy": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        owner=hero.id,
        caretaker=parent.id,
    ))

    intro(world, hero)
    love_activity(world, hero, activity)
    buy_prize(world, parent, hero, prize)
    love_prize(world, hero, prize)
    world.para()
    arrive(world, hero, parent, activity)
    want(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    world.say(f'"Maybe we can be kind and clever," {hero.id} said softly.')
    world.say(f'"Yes," {parent.label} said. "Kindness can help us choose the safe way."')
    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No kind, magical fix exists for that marina problem.")
    magic_offer(world, parent, hero, prize, gear)
    accept(world, parent, hero, activity, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, trait=trait)
    return world


SETTING = Marina()

ACTIVITIES = {
    "sea_spray": Activity(
        id="sea_spray",
        verb="watch the waves from the dock",
        gerund="watching the waves",
        rush="run to the edge of the dock",
        mess=WET_MESS,
        soil="all wet",
        zone={"torso"},
        weather="breezy",
        keyword="water",
        tags={"water", "spray", "marina", "kindness", "magic", "dialogue", SEED_WORD},
    ),
    "tide_walk": Activity(
        id="tide_walk",
        verb="walk along the tide line",
        gerund="walking beside the tide",
        rush="dash down to the water",
        mess=WET_MESS,
        soil="splash-soaked",
        zone={"feet"},
        weather="breezy",
        keyword="tide",
        tags={"water", "tide", "marina", "kindness", "magic", "dialogue"},
    ),
}

PRIZES = {
    "jacket": Prize("jacket", "a bright yellow jacket", "jacket", "torso"),
    "shoes": Prize("shoes", "tiny red shoes", "shoes", "feet", plural=True),
    "hat": Prize("hat", "a soft blue hat", "hat", "torso"),
}

GEAR = [
    Gear(
        id="raincoat",
        label="raincoat",
        covers={"torso"},
        guards={WET_MESS},
        prep="put on the raincoat",
        tail="walked back to the dock with their raincoat on",
        magic_line='The raincoat glimmered once, as if it had listened and liked the kind words.',
    ),
    Gear(
        id="boots",
        label="rain boots",
        covers={"feet"},
        guards={WET_MESS},
        prep="put on rain boots",
        tail="stomped back to the tide with dry feet",
        plural=True,
        magical=True,
        magic_line='The boots gave a tiny cheerful squeak, like they were ready to help.',
    ),
]

NAMES = ["Mina", "Toby", "Luna", "Eli", "Nora", "June", "Arlo", "Maya"]
TRAITS = ["gentle", "curious", "cheerful", "brave"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for act_id, act in ACTIVITIES.items():
        for prize_id, prize in PRIZES.items():
            if prize.region in act.zone and select_gear(act, prize) is not None:
                combos.append((act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not honestly threaten {prize.label}, "
        f"or there is no kind magical fix for that pairing.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize.region in act.zone and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.activity is None or c[0] == args.activity)
              and (args.prize is None or c[1] == args.prize)]
    if not combos:
        raise StoryError("(No valid marina story matches the given options.)")
    activity, prize = rng.choice(sorted(combos))
    prize_obj = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(prize_obj.genders))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming marina story with kindness, magic, and dialogue that includes the word "{SEED_WORD}".',
        f"Tell a gentle story where {f['hero'].id} wants to {f['activity'].verb} at the marina, but {f['parent'].label} worries about {f['prize'].label}.",
        f"Write a short child-friendly story about a marina, a wet problem, and a magical kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    prize: Entity = f["prize"]
    activity: Activity = f["activity"]
    gear: Gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type} who visits the marina with {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the marina?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because the {prize.label} could get {activity.soil} in the sea spray.",
        ),
        QAItem(
            question=f"What magical thing helped?",
            answer=f"The {gear.label} helped, and it made the safe choice feel kind and easy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} happy, the {prize.label} dry, and everyone laughing at the marina.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marina?",
            answer="A marina is a place by the water where boats are kept, tied up, and cared for.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping someone in a gentle way and trying to make them feel safe and cared for.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wonderful or impossible that can happen in a story to help the characters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), splashes(A, R), worn_on(P, R).
has_fix(A, P) :- prize_at_risk(A, P), gear(G), guards(G, wet), covers(G, R), worn_on(P, R).
valid(A, P) :- activity(A), prize(P), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
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
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    import asp
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in python:", sorted(py - clingo))
    print(" only in ASP:", sorted(clingo - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming marina story world with kindness, magic, and dialogue.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTING,
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        hero_name=params.name,
        hero_type=params.gender,
        parent_type=params.parent,
        trait=params.trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        cur = [
            StoryParams("sea_spray", "jacket", "Mina", "girl", "mother", "gentle"),
            StoryParams("tide_walk", "shoes", "Toby", "boy", "father", "curious"),
        ]
        samples = [generate(p) for p in cur]
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
