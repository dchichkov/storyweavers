#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/die_happy_ending_folk_tale.py
===========================================================================================================

A small folk-tale story world about a child, a lucky die, a worry, and a
happy ending.

Premise:
- A child treasures a small carved die from an elder.
- The child wants to play in a place or weather that could ruin a prized item.
- A parent or guardian notices the risk, warns them, and offers a safer way.
- The child accepts, and the tale ends with the object safe and the child glad.

The world is intentionally compact and state-driven:
- physical meters track wet/muddy/battered wear
- emotional memes track joy, desire, worry, stubbornness, and relief
- the narrative is authored from world state, not from a frozen template

This is a standalone script under the Storyweavers contract.
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
    carried_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("wet", "muddy", "battered", "dirty", "workload"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "love", "desire", "worry", "stubbornness", "relief", "conflict"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
        self.zone: set[str] = set()
        self.weather: str = ""
        self.paragraphs: list[list[str]] = [[]]
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

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

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
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "cottage": Setting("the cottage", indoor=True, affords={"dice_game"}),
    "green": Setting("the village green", indoor=False, affords={"rain_walk", "dice_game"}),
    "mill": Setting("the old mill", indoor=False, affords={"rain_walk"}),
    "orchard": Setting("the orchard", indoor=False, affords={"rain_walk", "dice_game"}),
    "market": Setting("the market square", indoor=False, affords={"rain_walk", "dice_game"}),
}

ACTIVITIES = {
    "rain_walk": Activity(
        id="rain_walk",
        verb="walk in the rain",
        gerund="walking in the rain",
        rush="dash into the rain",
        mess="wet",
        soil="soaked through",
        zone={"torso", "legs", "feet"},
        weather="rainy",
        keyword="rain",
        tags={"rain", "wet"},
    ),
    "dice_game": Activity(
        id="dice_game",
        verb="play the dice game",
        gerund="playing the dice game",
        rush="run to the games and clutch the die",
        mess="muddy",
        soil="splashed with mud",
        zone={"hands", "legs", "feet"},
        weather="rainy",
        keyword="die",
        tags={"die", "mud"},
    ),
}

PRIZES = {
    "cloak": Prize("cloak", "a wool cloak with a bright clasp", "cloak", "torso"),
    "boots": Prize("boots", "stout little boots", "boots", "feet", plural=True),
    "shirt": Prize("shirt", "a clean shirt", "shirt", "torso"),
}

GEAR = [
    Gear(
        id="hood",
        label="a rain hood",
        covers={"torso"},
        guards={"wet"},
        prep="put on a rain hood first",
        tail="took the rain hood from the peg",
    ),
    Gear(
        id="cloakwrap",
        label="a waxed cloak wrap",
        covers={"torso", "legs"},
        guards={"wet", "muddy"},
        prep="wrap up in a waxed cloak",
        tail="wrapped the cloak around the child",
    ),
    Gear(
        id="haversack",
        label="a cloth haversack",
        covers={"hands"},
        guards={"muddy"},
        prep="carry the die in a cloth haversack",
        tail="tied the die safely in the haversack",
    ),
]

GIRL_NAMES = ["Elsie", "Mara", "Nell", "Lina", "Anya", "Ivy", "Tilda", "Rose"]
BOY_NAMES = ["Owen", "Perrin", "Jasper", "Tobin", "Edric", "Milo", "Robin", "Bram"]
TRAITS = ["brave", "curious", "gentle", "stubborn", "cheerful", "bright"]


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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if prize.region in g.covers and activity.mess in g.guards:
            return g
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
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    for item in world.worn_items(actor):
        if item.protective or item.region not in world.zone or world.covered(actor, item.region):
            continue
        if activity.mess == "wet":
            item.meters["wet"] += 1
            item.meters["dirty"] += 1
        if activity.mess == "muddy":
            item.meters["muddy"] += 1
            item.meters["dirty"] += 1


def predict(world: World, actor: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {"soiled": sim.get(prize.id).meters["dirty"] >= THRESHOLD}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"Once upon a time, there was a little {hero.pronoun('possessive')} sort of child named {hero.id}, and {hero.pronoun()} kept a lucky die in {hero.pronoun('possessive')} pocket.")


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, for the folk path and the wind made every day feel like a story.")


def gift(world: World, elder: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"Long before that day, {elder.label} had given {hero.id} {hero.pronoun('object')} {prize.phrase}, and {hero.id} treasured {prize.it()} dearly.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    weather = "One rainy day" if world.weather == "rainy" else "One day"
    world.say(f"{weather}, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(f"The path was slick, and the crows watched from the fence posts.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, and {hero.pronoun()} reached for the little die as if it were a charm.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize)
    if not pred["soiled"]:
        return False
    parent.memes["worry"] += 1
    world.say(f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," {parent.label} said. "Then it would need washing, and the day would turn sour."')
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubbornness"] += 1
    world.say(f"{hero.id} still wished to rush ahead, but the mud tugged at {hero.pronoun('possessive')} boots and the wish began to wobble.")


def offer(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    if gear.id == "haversack":
        item = world.add(Entity(id="diepouch", type="pouch", label="cloth haversack", protective=True, covers={"hands"}))
        item.worn_by = hero.id
    else:
        item = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
        item.worn_by = hero.id
    if predict(world, hero, activity, prize)["soiled"]:
        item.worn_by = None
        del world.entities[item.id]
        return None
    world.say(f"Then {parent.label} smiled and said, \"How about we {gear.prep} and go on with care?\"")
    return gear


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["conflict"] = 0
    world.say(f"{hero.id}'s face lit up. {hero.pronoun().capitalize()} hugged {hero.pronoun('possessive')} {parent.label}, and the two of them took the safer way.")
    world.say(f"They {gear.tail}, and soon {hero.id} was {activity.gerund}, with {prize.label} safe and sound.")
    world.say(f"In the end, the little die stayed dry, the cloak stayed clean, and the child went home laughing under a sky that had grown kindly.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mara", hero_type: str = "girl", parent_type: str = "mother", hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    world.weather = activity.weather if not setting.indoor else ""

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    hero.memes["joy"] = 1
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mother" if parent_type == "mother" else "father"))
    elder = world.add(Entity(id="Elder", kind="character", type="woman", label="the old grandmother"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))

    introduce(world, hero)
    loves(world, hero, activity)
    gift(world, elder, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defy(world, hero, activity)

    world.para()
    gear = offer(world, parent, hero, activity, prize)
    if gear:
        accept(world, hero, parent, activity, prize, gear)

    world.facts = {
        "hero": hero,
        "parent": parent,
        "elder": elder,
        "prize": prize,
        "activity": activity,
        "setting": setting,
        "gear": gear,
        "resolved": gear is not None,
        "conflict": True,
    }
    return world


KNOWLEDGE = {
    "die": [
        ("What is a die?", "A die is a small object with numbered sides that people roll in games to choose a number."),
        ("Why do people roll a die?", "People roll a die to let chance pick a number for a game or story choice."),
    ],
    "rain": [
        ("Where does rain come from?", "Rain falls from clouds when the clouds are full of tiny drops of water."),
    ],
    "mud": [
        ("What is mud?", "Mud is wet dirt that can stick to shoes and clothes."),
    ],
    "cloak": [
        ("What is a cloak?", "A cloak is a loose covering you wear over your clothes to keep warm or dry."),
    ],
    "boots": [
        ("What are boots for?", "Boots help keep your feet dry and safe in wet or muddy places."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short folk tale for a young child about {hero.id}, a lucky die, and a safe choice in the rain.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {parent.label} worries about {prize.phrase}.",
        f'Write a happy-ending story in a village setting that includes the word "die" and ends with a safer plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f["gear"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the village?",
            answer=f"{hero.id} wanted to {act.verb}, but the rain and mud made the choice risky.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label} worried because {prize.label} could get {act.soil} if {hero.id} went ahead.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"They chose a safer way to play, so {gear.label if gear else 'the gear'} kept the trouble away and {prize.label} stayed clean.",
        ),
        QAItem(
            question=f"What little object did the child treasure?",
            answer="The child treasured a small die that had been given by an elder.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label} protected the right part of the child's clothing, so {act.mess} could not spoil {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("die")
    tags.add(world.facts["prize"].type)
    out: list[QAItem] = []
    for tag in ["die", "rain", "mud", "cloak", "boots"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {prize.label} would not be at risk in that activity.)"
    return f"(No story: no reasonable gear in this small world protects {prize.label} from {activity.gerund}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale world with a lucky die and a happy ending.")
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
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, [params.trait])
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
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
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
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="green", activity="rain_walk", prize="cloak", name="Mara", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="orchard", activity="dice_game", prize="shirt", name="Bram", gender="boy", parent="father", trait="stubborn"),
    StoryParams(place="market", activity="rain_walk", prize="boots", name="Elsie", gender="girl", parent="mother", trait="bright"),
]


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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
