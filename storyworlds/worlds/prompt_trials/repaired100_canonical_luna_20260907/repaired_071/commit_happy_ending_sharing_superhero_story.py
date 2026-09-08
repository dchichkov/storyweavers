#!/usr/bin/env python3
"""
Standalone storyworld: a child-friendly superhero story about making a commit,
sharing a gift, and earning a happy ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "height", "energy", "brightness", "weight"):
            self.meters.setdefault(key, 0.0)
        for key in ("courage", "worry", "trust", "joy", "generosity", "belonging"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str
    partner: str
    town: str
    mission: str
    gift: str
    seed: Optional[int] = None


HEROES = ["Luna", "Milo", "Nova", "Kai", "Zara", "Theo"]
PARTNERS = ["Pip", "Maya", "Juno", "Sam", "Ivy", "Rafi"]
TOWNS = {
    "Sunbeam City": {"landmark": "the bright clock tower", "weather": "a warm golden afternoon"},
    "Cloudberry Town": {"landmark": "the silver bridge", "weather": "a breezy blue morning"},
    "Moonlit Harbor": {"landmark": "the lighthouse hill", "weather": "a soft violet evening"},
    "Rainbow Village": {"landmark": "the rainbow fountain", "weather": "a clear day after rain"},
}
MISSIONS = {
    "rescue the floating festival banner": {
        "challenge": "a gust lifted the festival banner from its pole",
        "tool": "a ribbon line",
        "result": "the banner floated safely back to the square",
    },
    "carry the lantern home": {
        "challenge": "the last festival lantern rolled toward a steep hill",
        "tool": "a soft rope",
        "result": "the lantern glowed safely beside the town gate",
    },
    "repair the kindness bell": {
        "challenge": "the kindness bell stopped ringing before the sharing parade",
        "tool": "a tiny silver spring",
        "result": "the bell chimed clearly above the cheering street",
    },
}
GIFTS = ["a box of star stickers", "a basket of berry muffins", "a bundle of bright capes"]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join(
        [params.hero, params.partner, params.town, params.mission, params.gift]
    )
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def build_world(params: StoryParams) -> World:
    if params.hero == params.partner:
        raise StoryError("The hero and partner must have different names.")
    if params.town not in TOWNS:
        raise StoryError(f"Unknown town: {params.town}")
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")
    if params.gift not in GIFTS:
        raise StoryError(f"Unknown gift: {params.gift}")

    rng = random.Random(stable_seed(params) ^ 0x51A7)
    mission = MISSIONS[params.mission]
    setting = TOWNS[params.town]

    world = World(params)
    hero = world.add(Entity("hero", "character", "child", params.hero))
    partner = world.add(Entity("partner", "character", "child", params.partner))
    town = world.add(Entity("town", "place", "town", params.town))
    gift = world.add(Entity("gift", "object", "gift", params.gift))
    banner = world.add(Entity("mission_object", "object", "mission", params.mission))

    hero.memes["courage"] = 1.0
    partner.memes["trust"] = 1.0
    town.meters["brightness"] = 0.6
    gift.meters["weight"] = 1.0
    banner.meters["height"] = 8.0

    world.facts.update(
        hero=hero,
        partner=partner,
        town=town,
        gift=gift,
        mission_object=banner,
        mission_data=mission,
        setting=setting,
        commitment=False,
        shared=False,
        resolved=False,
    )

    openings = [
        f"On {setting['weather']}, {hero.label} zipped over {params.town} in a cape made from an old curtain.",
        f"In {params.town}, everyone knew {hero.label} as the small superhero with the biggest promise.",
        f"{hero.label} woke before the festival bells rang, because a superhero mission was waiting in {params.town}.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"Today, {hero.label} had promised to {params.mission}, while {partner.label} carried {params.gift} toward {setting['landmark']}."
    )
    world.say(
        f'"I made a commit to help before the celebration begins," {hero.label} said.'
    )
    world.say(
        f'"Then I will come with you," {partner.label} replied. "A promise is easier to keep when friends share the work."'
    )

    world.para()
    world.say(f"Just then, {mission['challenge']}.")
    world.say(
        f"The trouble rose above {setting['landmark']}, where ordinary hands could not safely reach."
    )
    hero.memes["worry"] = 1.0
    hero.meters["energy"] = 0.4
    world.say(
        f'{hero.label} looked at the problem and whispered, "I committed to this, but I cannot do it alone."'
    )
    world.say(
        f'{partner.label} opened the {params.gift} and answered, "You do not have to. I can share my {mission["tool"]} with you."'
    )
    partner.memes["generosity"] = 1.0
    world.facts["commitment"] = True

    world.para()
    world.say(
        f"Together, the two young heroes made a careful plan. {hero.label} would guide the rescue, and {partner.label} would hold the shared {mission['tool']} steady."
    )
    world.say(
        f"They counted, "One, two, three!" and worked as one team beneath {setting['landmark']}."
    )
    hero.memes["courage"] += 1.0
    partner.memes["trust"] += 1.0
    hero.meters["energy"] += 0.5
    banner.meters["height"] = 0.0
    world.facts["shared"] = True
    world.say(f"The plan worked: {mission['result']}.")
    world.say(
        f'{hero.label} smiled at {partner.label}. "Sharing your help made my commitment possible."'
    )
    world.say(
        f'{partner.label} smiled back. "And keeping a promise feels best when everyone gets to be part of it."'
    )

    world.para()
    hero.memes["joy"] = 1.0
    hero.memes["belonging"] = 1.0
    partner.memes["joy"] = 1.0
    partner.memes["belonging"] = 1.0
    town.meters["brightness"] = 1.0
    world.facts["resolved"] = True
    world.say(
        f"The people of {params.town} clapped as the heroes returned to the square."
    )
    world.say(
        f"{hero.label} shared the remaining {params.gift} with the townspeople, and {partner.label} helped pass each piece around."
    )
    world.say(
        f"At last, the festival began beneath {setting['landmark']}, with every neighbor smiling."
    )
    world.say(
        f"{hero.label} wrote one sentence in the superhero notebook: "
        '"A commitment grows stronger when courage and sharing work together."'
    )
    world.say(
        f"That was the happy ending: {hero.label} and {partner.label} stood side by side while the whole town celebrated their shared victory."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a superhero story about {p.hero} making a commitment in {p.town}.",
        f"Show how {p.hero} and {p.partner} share help during the mission to {p.mission}.",
        "End with a happy celebration that proves teamwork changed the town.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    mission = world.facts["mission_data"]
    return [
        QAItem(
            question=f"What commitment did {p.hero} make?",
            answer=f"{p.hero} committed to {p.mission} before the town celebration began.",
        ),
        QAItem(
            question=f"How did {p.partner} help {p.hero}?",
            answer=f"{p.partner} shared a {mission['tool']} and held it steady while {p.hero} guided the rescue.",
        ),
        QAItem(
            question=f"What happened after the heroes worked together?",
            answer=f"Their plan worked, and {mission['result']}. The people of {p.town} celebrated them.",
        ),
        QAItem(
            question=f"What did {p.hero} share at the happy ending?",
            answer=f"{p.hero} shared the remaining {p.gift} with the townspeople, so everyone could join the celebration.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a commitment?",
            answer="A commitment is a promise to do something and keep working toward it.",
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing lets other people contribute, receive something useful, and enjoy a success together.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the problem has been solved and the characters can celebrate safely together.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: type={entity.type} meters={meters} memes={memes}"
        )
    lines.append(f"facts={{commitment: {world.facts['commitment']}, shared: {world.facts['shared']}, resolved: {world.facts['resolved']}}}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about commitment, sharing, and a happy ending."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--town", choices=list(TOWNS))
    parser.add_argument("--mission", choices=list(MISSIONS))
    parser.add_argument("--gift", choices=GIFTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    choices = [name for name in PARTNERS if name != hero]
    partner = args.partner or rng.choice(choices)
    return StoryParams(
        hero=hero,
        partner=partner,
        town=args.town or rng.choice(list(TOWNS)),
        mission=args.mission or rng.choice(list(MISSIONS)),
        gift=args.gift or rng.choice(GIFTS),
        seed=args.seed,
    )


def valid_combos() -> list[tuple[str, str, str]]:
    return [(town, "commitment", "sharing") for town in TOWNS]


ASP_RULES = r"""
valid_town(T) :- town(T).
valid_story(T) :- valid_town(T).
commitment(commit).
sharing(share).
happy_ending(happy).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [asp.fact("town", town) for town in TOWNS]
        + [asp.fact("commitment", "commit"), asp.fact("sharing", "share"), asp.fact("happy_ending", "happy")]
    )


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_story"))
    expected = {(town,) for town in TOWNS}
    if found != expected:
        print("ASP/Python parity mismatch.")
        print("only in ASP:", sorted(found - expected))
        print("only in Python:", sorted(expected - found))
        return 1
    for i, town in enumerate(TOWNS):
        params = StoryParams(
            hero=HEROES[0],
            partner=PARTNERS[0],
            town=town,
            mission=list(MISSIONS)[i % len(MISSIONS)],
            gift=GIFTS[i % len(GIFTS)],
            seed=100 + i,
        )
        sample = generate(params)
        if not sample.story or "commit" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP gate matches Python registry ({len(found)} towns), and generated stories pass.")
    return 0


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Compatible story towns:")
        for town, _, _ in valid_combos():
            print(f"  {town}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, town in enumerate(TOWNS):
            params = StoryParams(
                hero=HEROES[index % len(HEROES)],
                partner=PARTNERS[index % len(PARTNERS)],
                town=town,
                mission=list(MISSIONS)[index % len(MISSIONS)],
                gift=GIFTS[index % len(GIFTS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
