#!/usr/bin/env python3
"""
A child-friendly fairy-tale storyworld about a boondocks customer, a comic
transformation, and a conflict solved by listening.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = STORYWORLDS_ROOT.parent
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str
    customer: str
    fairy: str
    place: str
    object_name: str
    reward: str
    seed: Optional[int] = None
    scenario: str = "backward_bakery"
    telling_mode: int = 0
    variant: int = 0


HERO_NAMES = ["Luna", "Mara", "Pip", "Tobin", "Nell", "Orin"]
CUSTOMER_NAMES = ["Bramble", "Clover", "Gus", "Muffin", "Tansy", "Wicket"]
FAIRY_NAMES = ["Fizzlewing", "Dame Dandelion", "Pock", "Twinkletoe"]

SCENARIOS: dict[str, dict[str, str]] = {
    "backward_bakery": {
        "premise": "the village bakery sold loaves that hopped back into the oven",
        "trouble": "an impatient customer had been transformed into a giant talking turnip",
        "clue": "a silver crumb on the turnip's leaf pointed toward the shop's wishing oven",
        "risk": "pulling the turnip by its leaves could make the transformation last forever",
        "cause": "the customer had demanded a bargain, tossed a coin into the wishing oven, and shouted the wrong wish",
        "hero_action": "read the tiny oven inscription aloud",
        "helper_action": "held a bowl beneath the turnip's leaves and asked the customer what they had truly wanted",
        "solution": "the oven changed the turnip back into a person wearing a floury crown",
        "repair": "swept the silver crumbs into a jar and paid fairly for the bread",
        "lesson": "A true wish begins with honest words.",
        "ending": "After sunset, the bakery's loaves marched normally, and everyone shared warm rolls.",
    },
    "crooked_market": {
        "premise": "every carrot in the market stood up and bowed to the moon",
        "trouble": "a customer had been transformed into a squeaky blue goose",
        "clue": "one market bell rang whenever the goose said the word bargain",
        "risk": "chasing the goose would send it into the enchanted river",
        "cause": "the customer had mocked a peddler's careful prices and accepted a prankish magic receipt",
        "hero_action": "placed a ribbon around the bell instead of grabbing the goose",
        "helper_action": "asked the goose to explain the purchase in three honest honks",
        "solution": "the bell fell silent, and the goose became a customer again",
        "repair": "returned the magic receipt and thanked the peddler for fair dealing",
        "lesson": "Respect can untangle a spell faster than shouting.",
        "ending": "The carrots bowed once more, this time to the smiling peddler.",
    },
    "thimble_forest": {
        "premise": "the forest paths had shrunk until squirrels needed maps",
        "trouble": "a customer had become a pocket-sized giant with a voice like a drum",
        "clue": "the giant's hat contained a button marked with the fairy's shop sign",
        "risk": "a loud argument could shake loose every tiny tree",
        "cause": "the customer had demanded a grand cloak from a fairy tailor and laughed at the small fitting",
        "hero_action": "measured the giant's shadow with a vine",
        "helper_action": "invited the customer to describe a comfortable cloak rather than a grand one",
        "solution": "the shadow shrank gently, and the customer returned to ordinary size",
        "repair": "helped sew a useful cloak with pockets for acorns",
        "lesson": "The right size for a gift is the size that helps.",
        "ending": "Squirrels carried the finished cloak through the little forest like a royal banner.",
    },
    "sleepy_castle": {
        "premise": "the castle's flags yawned whenever the drawbridge opened",
        "trouble": "a customer had transformed into a snoring stone statue beside the royal shop",
        "clue": "the statue's stone toes pointed toward a jar labeled patience",
        "risk": "hammering the statue would wake the whole castle and crack the bridge",
        "cause": "the customer had tried to skip the fairy's waiting line and swallowed a patience pebble",
        "hero_action": "read the line number carved on the statue's heel",
        "helper_action": "sat beside the statue and described each customer who had been waiting",
        "solution": "the stone softened into a person who apologized before yawning",
        "repair": "returned the patience pebble and made a clear waiting line",
        "lesson": "Waiting kindly is part of receiving a good thing.",
        "ending": "The castle flags stopped yawning and fluttered above a peaceful shop.",
    },
}

OPENINGS = [
    "Once, beyond the last paved road in the boondocks, {hero} kept a little lantern shop.",
    "In a fairy-tale village tucked deep in the boondocks, {hero} opened the shutters each morning.",
    "At the edge of the boondocks stood a tiny shop where {hero} repaired enchanted things.",
    "The boondocks had no palace, but they had {hero}, who knew every road and every odd spell.",
    "On a hill beyond the boondocks, {hero} sold useful charms to travelers and customers.",
]

DIALOGUE = [
    '"Please do not tug," said {hero}. "Tell me what happened."',
    '"I wanted the best bargain!" cried {customer}. "I did not want to become this!"',
    '"A spell listens to meaning," said {fairy}. "It may laugh at careless words."',
    '"Then ask me plainly," said {hero}. "{customer}, what do you really need?"',
    '"I need help, not a grand show," said {customer}.',
]

TURN_LINES = [
    "At last, the silly spell revealed its serious lesson.",
    "The joke of the transformation pointed toward the cure.",
    "The strange clue turned the quarrel into a question.",
    "The fairy's humor had hidden a careful test.",
]


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, str] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fairy-tale boondocks customer transformation world.")
    parser.add_argument("--hero")
    parser.add_argument("--customer")
    parser.add_argument("--fairy")
    parser.add_argument("--place")
    parser.add_argument("--object-name")
    parser.add_argument("--reward")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def validate_params(params: StoryParams) -> None:
    if not params.hero.strip() or not params.customer.strip():
        raise StoryError("Hero and customer names cannot be empty.")
    if params.hero.casefold() == params.customer.casefold():
        raise StoryError("Hero and customer must be different characters.")
    if params.scenario not in SCENARIOS:
        raise StoryError(f"Unknown scenario: {params.scenario}")
    if not params.object_name.strip() or not params.reward.strip():
        raise StoryError("The enchanted object and reward must be named.")


def generate_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params.place)
    world.add(Entity("hero", "character", params.hero, "helper", memes={"patience": 0.7}))
    world.add(Entity("customer", "character", params.customer, "customer", memes={"frustration": 0.8}))
    world.add(Entity("fairy", "character", params.fairy, "fairy", memes={"humor": 0.9}))
    world.add(Entity("object", "thing", params.object_name, "enchanted_object", owner="fairy"))
    world.add(Entity("reward", "thing", params.reward, "reward", owner="customer"))
    return world


def tell(world: World, params: StoryParams) -> World:
    case = SCENARIOS[params.scenario]
    rng = random.Random((params.seed or 0) ^ params.variant ^ 0xA045)
    hero = world.get("hero")
    customer = world.get("customer")
    fairy = world.get("fairy")
    opening = OPENINGS[params.telling_mode % len(OPENINGS)].format(hero=params.hero)

    world.say(opening)
    world.say(f"{params.fairy} had given {params.hero} a curious {params.object_name} to mind.")
    world.say(f"One morning, {case['premise']}.")
    world.say(f"Then {params.customer}, a customer from the far road, arrived and discovered the trouble: {case['trouble']}.")

    world.para()
    world.say(f"{params.hero} noticed that {case['clue']}.")
    world.say(rng.choice(DIALOGUE).format(hero=params.hero, customer=params.customer, fairy=params.fairy))
    world.say(rng.choice(DIALOGUE).format(hero=params.hero, customer=params.customer, fairy=params.fairy))
    world.say(f"{params.hero} warned, 'Careful. {case['risk'].capitalize()}.'")
    world.say(f"{params.fairy} fluttered from a teacup and confessed, 'The trouble began because {case['cause']}.'")

    world.para()
    world.say(f"{params.hero} chose a calm plan. {params.hero} {case['hero_action']}.")
    world.say(f"Meanwhile, {params.fairy} {case['helper_action']}.")
    world.say(f"{params.customer} blinked. 'I suppose I can answer honestly,' they said.")
    world.say(f"{case['turn_line'] if 'turn_line' in case else rng.choice(TURN_LINES)}")
    world.say(f"Because the customer spoke plainly, {case['solution']}.")

    world.para()
    world.say(f"{params.customer} bowed and said, 'I am sorry for making the conflict worse.'")
    world.say(f"Together, they {case['repair']}.")
    world.say(f"{case['lesson']}")
    world.say(case["ending"])

    customer.meters["transformation"] = 0.0
    customer.meters["honesty"] = 1.0
    customer.memes["gratitude"] = 0.9
    hero.memes["patience"] = 1.0
    fairy.memes["humor"] = 1.0
    world.fired.update({"transformation_reversed", "conflict_resolved", "customer_changed"})
    world.facts = {
        "hero": params.hero,
        "customer": params.customer,
        "fairy": params.fairy,
        "place": params.place,
        "object_name": params.object_name,
        "reward": params.reward,
        "premise": case["premise"],
        "trouble": case["trouble"],
        "clue": case["clue"],
        "risk": case["risk"],
        "cause": case["cause"],
        "hero_action": case["hero_action"],
        "helper_action": case["helper_action"],
        "solution": case["solution"],
        "repair": case["repair"],
        "lesson": case["lesson"],
        "ending": case["ending"],
    }
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a fairy tale in the boondocks about {facts['hero']} helping customer {facts['customer']} after a transformation.",
        f"Tell a humorous conflict story where the clue '{facts['clue']}' leads to a safe cure.",
        f"Write a child-friendly fairy tale with dialogue, a customer, a fairy, and the lesson '{facts['lesson']}'",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("Who was transformed?", f"{f['customer']} was transformed by the fairy-tale spell."),
        QAItem("What clue helped solve the conflict?", f"The clue was that {f['clue']}."),
        QAItem("Why did the transformation happen?", f"It happened because {f['cause']}."),
        QAItem("What did the hero do?", f"{f['hero']} {f['hero_action']}."),
        QAItem("How was the transformation reversed?", f"{f['solution']}."),
        QAItem("How did the customer make amends?", f"The customer helped the group {f['repair']}."),
        QAItem("What lesson did the story teach?", f"The story taught that {f['lesson']}"),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a transformation?", "A transformation is a change from one form or condition into another."),
        QAItem("What is a customer?", "A customer is a person who buys something or receives a service."),
        QAItem("What is conflict?", "Conflict is a problem or disagreement that characters must work through."),
        QAItem("What is humor?", "Humor is something that makes people smile or laugh."),
        QAItem("What is a fairy tale?", "A fairy tale is a story that may include magic, unusual creatures, and a lesson."),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("setting", "boondocks"),
            asp.fact("role", "customer"),
            asp.fact("feature", "transformation"),
            asp.fact("feature", "humor"),
            asp.fact("feature", "conflict"),
            asp.fact("style", "fairy_tale"),
            asp.fact("resolution", "honest_words"),
        ]
    )


ASP_RULES = r"""
safe_story :- setting(boondocks), role(customer), feature(transformation),
              feature(humor), feature(conflict), style(fairy_tale),
              resolution(honest_words).
#show safe_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show safe_story/0."))
    found = set(asp.atoms(model, "safe_story"))
    expected = {()}
    if found == expected:
        print("OK: ASP fairy-tale gate matches Python.")
        return 0
    print(f"ASP mismatch: expected {expected}, got {found}")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== Generation prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def generate(params: StoryParams) -> StorySample:
    world = tell(generate_world(params), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("Luna", "Bramble", "Fizzlewing", "the Boondocks", "a moonlit kettle", "warm honey cakes", 11, "backward_bakery", 0, 11),
    StoryParams("Mara", "Clover", "Dame Dandelion", "the Boondocks", "a silver thimble", "a blue ribbon", 29, "crooked_market", 1, 29),
    StoryParams("Pip", "Gus", "Pock", "the Boondocks", "a singing key", "a basket of pears", 47, "thimble_forest", 2, 47),
    StoryParams("Nell", "Tansy", "Twinkletoe", "the Boondocks", "a patient clock", "a star cookie", 83, "sleepy_castle", 3, 83),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    customer_choices = [name for name in CUSTOMER_NAMES if name.casefold() != hero.casefold()]
    return StoryParams(
        hero=hero,
        customer=args.customer or rng.choice(customer_choices),
        fairy=args.fairy or rng.choice(FAIRY_NAMES),
        place=args.place or "the Boondocks",
        object_name=args.object_name or rng.choice(["a moonlit kettle", "a silver thimble", "a singing key"]),
        reward=args.reward or rng.choice(["warm honey cakes", "a blue ribbon", "a basket of pears"]),
        seed=rng.randrange(2**31),
        scenario=rng.choice(list(SCENARIOS)),
        telling_mode=rng.randrange(len(OPENINGS)),
        variant=rng.randrange(1_000_000_000),
    )


def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_story/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        print(format_json(samples))
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
