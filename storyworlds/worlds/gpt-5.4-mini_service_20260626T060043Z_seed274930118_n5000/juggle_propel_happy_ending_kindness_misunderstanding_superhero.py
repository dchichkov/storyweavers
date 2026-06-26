#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/juggle_propel_happy_ending_kindness_misunderstanding_superhero.py

A standalone story world for a small superhero tale:
- a hero with a useful power
- a misunderstanding that causes trouble
- kindness that fixes the mistake
- a happy ending image that proves what changed

The seed words are preserved in the domain:
- juggle
- propel

The story style stays close to a bright superhero story: concrete action,
clear feelings, and a tidy ending.
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
class City:
    name: str
    place_detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    label: str
    verb: str
    gerund: str
    effect: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectItem:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    city: str
    power: str
    item: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy
        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


CITIES = {
    "downtown": City("downtown", "the bright downtown square", {"juggle", "propel"}),
    "harbor": City("harbor", "the windy harbor roof", {"juggle", "propel"}),
    "rooftop": City("rooftop", "the tall rooftop garden", {"juggle", "propel"}),
    "museum": City("museum", "the quiet museum plaza", {"juggle", "propel"}),
}

POWERS = {
    "juggle": Power(
        id="juggle",
        label="juggle-light",
        verb="juggle glowing orbs",
        gerund="juggling glowing orbs",
        effect="kept the orbs dancing in a safe, tidy circle",
        mess="dropped",
        zone={"hands", "arms"},
        keyword="juggle",
        tags={"juggle", "kindness"},
    ),
    "propel": Power(
        id="propel",
        label="propel-burst",
        verb="propel a rescue disk",
        gerund="propelling a rescue disk",
        effect="sent the disk zipping where it was needed",
        mess="blown",
        zone={"hands", "air"},
        keyword="propel",
        tags={"propel", "rescue"},
    ),
}

ITEMS = {
    "cape": ObjectItem("cape", "a shiny red cape", "back", False),
    "boots": ObjectItem("boots", "blue rescue boots", "feet", True),
    "mask": ObjectItem("mask", "a bright silver mask", "face", False),
    "gloves": ObjectItem("gloves", "soft hero gloves", "hands", True),
}

HEROES = ["Nova", "Pip", "Mira", "Zane", "Luna", "Tao", "Ruby", "Orin"]
SIDEKICKS = ["Bea", "Fin", "Juno", "Kai", "Milo", "Tess"]
GENDERS = ["girl", "boy"]
CITY_ORDER = ["downtown", "harbor", "rooftop", "museum"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for city_id, city in CITIES.items():
        for power_id in city.affords:
            for item_id, item in ITEMS.items():
                power = POWERS[power_id]
                if item.region in power.zone:
                    combos.append((city_id, power_id, item_id))
    return combos


def reason_invalid(city: City, power: Power, item: ObjectItem) -> str:
    if item.region not in power.zone:
        return (
            f"(No story: {power.gerund} does not affect the {item.label} on the {item.region}. "
            f"Try an item worn on {sorted(power.zone)}.)"
        )
    return "(No story: that combination is not reasonable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with juggle, propel, kindness, and a happy ending.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    if args.power and args.item:
        power = POWERS[args.power]
        item = ITEMS[args.item]
        if item.region not in power.zone:
            raise StoryError(reason_invalid(CITIES[args.city or "downtown"], power, item))

    combos = [c for c in valid_combos()
              if (args.city is None or c[0] == args.city)
              and (args.power is None or c[1] == args.power)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    city_id, power_id, item_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    hero_name = args.name or rng.choice(HEROES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(
        city=city_id,
        power=power_id,
        item=item_id,
        hero_name=hero_name,
        hero_gender=gender,
        sidekick_name=sidekick,
    )


def predict_misunderstanding(world: World, hero: Entity, power: Power, item: Entity) -> bool:
    sim = world.copy()
    _use_power(sim, sim.get(hero.id), power, narrate=False)
    target = sim.get(item.id)
    return target.memes.get("troubled", 0.0) >= THRESHOLD


def _use_power(world: World, hero: Entity, power: Power, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if power.id == "juggle":
        hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
        world.entities["crowd"].memes["surprised"] = world.entities["crowd"].memes.get("surprised", 0.0) + 1
        out.append(f"{hero.id} kept the glowing orbs moving with careful hands.")
    elif power.id == "propel":
        world.entities["crowd"].memes["helped"] = world.entities["crowd"].memes.get("helped", 0.0) + 1
        out.append(f"{hero.id} sent the rescue disk forward with a bright burst of speed.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def setup(world: World, hero: Entity, sidekick: Entity, item: Entity, power: Power) -> None:
    world.say(f"{hero.id} was a brave little hero who loved {power.gerund}.")
    world.say(f"{hero.id} always carried {item.phrase}, because it made the rescue suit feel complete.")
    world.say(f"{sidekick.id} stayed close and watched every move with wide eyes.")


def misunderstanding_scene(world: World, hero: Entity, sidekick: Entity, item: Entity, power: Power) -> None:
    world.para()
    world.say(f"One afternoon, a rumor raced through {world.city.place_detail}.")
    if power.id == "juggle":
        world.say(f"{sidekick.id} saw the spinning orbs and thought {hero.id} was showing off instead of helping.")
    else:
        world.say(f"{sidekick.id} saw the fast rescue disk and thought {hero.id} was trying to scare the crowd.")
    item.memes["troubled"] = item.memes.get("troubled", 0.0) + 1
    world.say(f"{item.label.capitalize()} felt the awkward silence grow around it.")
    if predict_misunderstanding(world, hero, power, item):
        world.say(f"{hero.id} noticed the worried faces and felt a lump of misunderstanding in the air.")


def kindness_turn(world: World, hero: Entity, sidekick: Entity, item: Entity, power: Power) -> None:
    world.para()
    world.say(f"Instead of getting angry, {hero.id} slowed down and spoke kindly.")
    world.say(f"“I am not showing off,” {hero.id} said. “I am trying to help.”")
    world.say(f"{sidekick.id} looked at the rescue gear, then at the worried crowd, and chose kindness too.")
    if power.id == "juggle":
        world.say(f"{sidekick.id} handed over the last loose orb, and together they made the orbs dance in a calm line.")
    else:
        world.say(f"{sidekick.id} cleared the path, and together they let the rescue disk propel the supply bag to the roof.")
    item.memes["trust"] = item.memes.get("trust", 0.0) + 1
    item.memes["troubled"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1


def happy_ending(world: World, hero: Entity, sidekick: Entity, item: Entity, power: Power) -> None:
    world.para()
    world.say(f"After that, the misunderstanding melted away.")
    world.say(f"{hero.id} used {power.gerund} the right way, and {power.effect}.")
    if power.id == "juggle":
        world.say(f"The glowing orbs lit the square like tiny stars, and the crowd cheered as the path stayed safe and clear.")
    else:
        world.say(f"The rescue disk zipped past the chimneys, and the needed bag landed safely in waiting hands.")
    world.say(f"{sidekick.id} smiled at {hero.id}, because kindness had turned a mix-up into a happy ending.")
    world.say(f"At the end, {item.label} looked proud and bright, and the city felt safe again.")


def tell(city: City, power: Power, item_cfg: ObjectItem, hero_name: str, hero_gender: str, sidekick_name: str) -> World:
    world = World(city)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="boy" if hero_gender == "girl" else "girl"))
    crowd = world.add(Entity(id="crowd", kind="group", type="people"))
    item = world.add(Entity(id=item_cfg.label, type=item_cfg.label, label=item_cfg.label, phrase=item_cfg.phrase, plural=item_cfg.plural))
    world.facts.update(hero=hero, sidekick=sidekick, crowd=crowd, item=item, power=power, city=city)

    setup(world, hero, sidekick, item, power)
    misunderstanding_scene(world, hero, sidekick, item, power)
    kindness_turn(world, hero, sidekick, item, power)
    happy_ending(world, hero, sidekick, item, power)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    power = f["power"]
    item = f["item"]
    city = f["city"]
    return [
        f"Write a superhero story for a young child set in {city.name} with {hero.id}, {power.keyword}, and {item.label}.",
        f"Tell a gentle story where a hero is misunderstood, then answers with kindness and saves the day.",
        f"Write a short happy ending story that uses the words juggle and propel in a superhero adventure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    power = f["power"]
    item = f["item"]
    city = f["city"]
    return [
        QAItem(
            question=f"Who was the story about in {city.name}?",
            answer=f"It was about {hero.id}, a brave little superhero who loved {power.gerund}.",
        ),
        QAItem(
            question=f"What did {hero.id} use during the rescue?",
            answer=f"{hero.id} used {power.gerund} to help people and keep the day moving safely.",
        ),
        QAItem(
            question=f"Why did {sidekick.id} feel unsure at first?",
            answer=f"{sidekick.id} misunderstood what {hero.id} was doing and thought it might cause trouble.",
        ),
        QAItem(
            question=f"How did the problem get fixed?",
            answer=f"It got fixed when {hero.id} and {sidekick.id} chose kindness, explained the plan, and worked together.",
        ),
        QAItem(
            question=f"What was the ending like?",
            answer=f"It was a happy ending: the mistake was cleared up, the rescue worked, and everyone felt safer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    power = f["power"]
    out = [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a made-up hero who uses special powers to help other people.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring even when something goes wrong.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about what another person means.",
        ),
    ]
    if power.id == "juggle":
        out.append(QAItem(
            question="What does it mean to juggle?",
            answer="To juggle means to keep more than one thing moving in the air by using careful hands.",
        ))
    if power.id == "propel":
        out.append(QAItem(
            question="What does propel mean?",
            answer="To propel something means to push or send it forward with force or speed.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(h1).
sidekick(s1).

power(juggle).
power(propel).

item(cape, back).
item(boots, feet).
item(mask, face).
item(gloves, hands).

city(downtown).
city(harbor).
city(rooftop).
city(museum).

affords(downtown, juggle).
affords(downtown, propel).
affords(harbor, juggle).
affords(harbor, propel).
affords(rooftop, juggle).
affords(rooftop, propel).
affords(museum, juggle).
affords(museum, propel).

zone(juggle, hands).
zone(juggle, arms).
zone(propel, hands).
zone(propel, air).

valid(City, Power, Item) :- affords(City, Power), item(Item, Region), zone(Power, Region).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for city_id, city in CITIES.items():
        lines.append(asp.fact("city", city_id))
        for p in sorted(city.affords):
            lines.append(asp.fact("affords", city_id, p))
    for power_id, power in POWERS.items():
        lines.append(asp.fact("power", power_id))
        for z in sorted(power.zone):
            lines.append(asp.fact("zone", power_id, z))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id, item.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    if args.all:
        params_list = [
            StoryParams(city="downtown", power="juggle", item="gloves", hero_name="Nova", hero_gender="girl", sidekick_name="Bea"),
            StoryParams(city="harbor", power="propel", item="cape", hero_name="Pip", hero_gender="boy", sidekick_name="Juno"),
            StoryParams(city="rooftop", power="juggle", item="mask", hero_name="Mira", hero_gender="girl", sidekick_name="Kai"),
            StoryParams(city="museum", power="propel", item="boots", hero_name="Zane", hero_gender="boy", sidekick_name="Tess"),
        ]
        return [generate(p) for p in params_list]

    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        rng = random.Random(base_seed + i)
        i += 1
        params = resolve_params(args, rng)
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def generate(params: StoryParams) -> StorySample:
    world = tell(CITIES[params.city], POWERS[params.power], ITEMS[params.item], params.hero_name, params.hero_gender, params.sidekick_name)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    samples = build_samples(args)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
