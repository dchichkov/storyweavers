#!/usr/bin/env python3
"""
A small cautionary folk-tale world about profit, labels, and kindness.

A miller discovers that a clever descriptor can make ordinary goods seem
valuable. When profit becomes more important than honest kindness, a hungry
traveler teaches the village that a fair measure is worth more than a grand
sermon.
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
import copy
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "World":
        clone = World(copy.deepcopy(self.setting))
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


TALES = [
    {
        "place": "the village market",
        "good": "a basket of plain apples",
        "descriptor": "sun-caught orchard jewels",
        "profit": "three bright coins",
        "traveler": "a tired shepherd",
        "cause": "the grand label made hungry buyers pay for ordinary apples",
        "repair": "weighed the apples honestly and gave the shepherd a full one",
        "image": "the market scale rested level while an apple shone in the shepherd's palm",
    },
    {
        "place": "the riverside fair",
        "good": "a bundle of brown wool",
        "descriptor": "cloud-soft mountain fleece",
        "profit": "a pouch of silver",
        "traveler": "a cold child with her grandmother",
        "cause": "the fancy description hid that the wool was damp and thin",
        "repair": "dried the wool, lowered the price, and shared a warm blanket",
        "image": "steam rose from the cleaned wool as the child smiled beneath the blanket",
    },
    {
        "place": "the old bridge market",
        "good": "a jar of cloudy honey",
        "descriptor": "golden moon nectar",
        "profit": "a golden ring",
        "traveler": "a quiet woodcutter",
        "cause": "the sparkling words persuaded people to ignore the honey's sour smell",
        "repair": "tasted the honey first and gave the woodcutter fresh bread instead",
        "image": "bees hummed over a clean jar while bread cooled beside the bridge",
    },
    {
        "place": "the hilltop bakehouse",
        "good": "a loaf with a cracked crust",
        "descriptor": "the baker's sunburst loaf",
        "profit": "four copper pennies",
        "traveler": "an old woman",
        "cause": "the proud name made the baker forget to check whether the loaf was stale",
        "repair": "admitted the mistake, baked a fresh loaf, and shared the cracked one with birds",
        "image": "a warm loaf steamed on the table while crumbs fed sparrows outside",
    },
    {
        "place": "the lantern quay",
        "good": "a small blue lamp",
        "descriptor": "a beacon of royal night",
        "profit": "a chest of coins",
        "traveler": "a boatman lost in the fog",
        "cause": "the grand descriptor raised the price while the lamp's wick stayed too short",
        "repair": "trimmed a proper wick and lent the lamp freely for the crossing",
        "image": "the little blue lamp guided boats home without asking for a coin",
    },
    {
        "place": "the meadow road",
        "good": "a sack of common grain",
        "descriptor": "harvest fit for a king",
        "profit": "a silver buckle",
        "traveler": "a widow and her son",
        "cause": "the boastful title tempted the merchant to charge more than the grain could feed",
        "repair": "measured a fair share and carried it to the widow's cottage",
        "image": "new bread rose in the widow's oven beneath a quiet morning star",
    },
    {
        "place": "the cedar-town square",
        "good": "a wooden stool",
        "descriptor": "the throne of sturdy comfort",
        "profit": "a purse of brass",
        "traveler": "a limping pilgrim",
        "cause": "the merchant praised the stool but never noticed its loose leg",
        "repair": "fixed the leg before selling it and offered the pilgrim a seat",
        "image": "the pilgrim rested safely while the repaired stool stood firm in the square",
    },
    {
        "place": "the moonlit herb stall",
        "good": "a handful of dried mint",
        "descriptor": "green stars of healing",
        "profit": "a polished pearl",
        "traveler": "a coughing potter",
        "cause": "the beautiful words mattered less than whether the herbs were fresh and useful",
        "repair": "checked the leaves, brewed tea, and charged nothing for the first cup",
        "image": "mint steam curled upward as the potter's cough grew softer",
    },
    {
        "place": "the orchard gate",
        "good": "a basket of small pears",
        "descriptor": "royal drops of autumn",
        "profit": "a red ribbon",
        "traveler": "a hungry messenger",
        "cause": "the noble title turned a simple snack into a costly prize",
        "repair": "gave the messenger two pears and sold the rest at a plain fair price",
        "image": "the messenger carried the royal-looking ribbon on his hat and pears in his pouch",
    },
    {
        "place": "the stone fountain",
        "good": "a blue clay cup",
        "descriptor": "a goblet for moon kings",
        "profit": "a gold button",
        "traveler": "a thirsty mason",
        "cause": "the merchant praised the cup's story while ignoring its tiny leak",
        "repair": "sealed the crack and let the mason drink before discussing payment",
        "image": "clear water filled the mended cup, and the mason drank with relief",
    },
]


def build_world(params: "StoryParams") -> World:
    tale = TALES[params.tale_index % len(TALES)]
    world = World(Setting(tale["place"], {"trade", "weigh", "share"}))

    seller = world.add(Entity(
        "seller",
        kind="character",
        type="merchant",
        label=params.seller,
        location=tale["place"],
        meters={"stock": 1.0, "coins": 0.0},
        memes={"ambition": 1.0, "kindness": 0.0, "shame": 0.0, "wisdom": 0.0},
    ))
    traveler = world.add(Entity(
        "traveler",
        kind="character",
        type="traveler",
        label=tale["traveler"],
        location=tale["place"],
        meters={"hunger": 1.0, "need": 1.0},
        memes={"hope": 1.0, "trust": 0.0},
    ))
    world.add(Entity(
        "good",
        kind="object",
        type="merchandise",
        label=tale["good"],
        owner="seller",
        location=tale["place"],
        meters={"quality": 0.5, "fair_value": 0.5},
        memes={"reputation": 0.0},
    ))
    world.facts.update(
        tale=tale,
        seller=seller,
        traveler=traveler,
        descriptor=tale["descriptor"],
        profit=tale["profit"],
        offered=False,
        honest=False,
        kindness=False,
        resolved=False,
    )
    return world


def propagate(world: World) -> None:
    if world.facts.get("offered") and not world.facts.get("honest"):
        if ("warning",) not in world.fired:
            world.fired.add(("warning",))
            world.say("The painted words grew taller than the truth beneath them.")
    if world.facts.get("honest") and world.facts.get("kindness"):
        world.facts["resolved"] = True
        if ("resolution",) not in world.fired:
            world.fired.add(("resolution",))
            world.facts["seller"].memes["wisdom"] += 1.0
            world.facts["seller"].memes["kindness"] += 1.0
            world.facts["traveler"].memes["trust"] += 1.0


def tell(params: "StoryParams") -> World:
    world = build_world(params)
    tale = world.facts["tale"]
    seller: Entity = world.facts["seller"]
    traveler: Entity = world.facts["traveler"]

    openings = [
        f"In {tale['place']}, {seller.label} sold {tale['good']}.",
        f"Long ago, {seller.label} kept a busy stall in {tale['place']}.",
        f"At dawn in {tale['place']}, {seller.label} polished a basket of goods.",
        f"The people of {tale['place']} knew {seller.label} as a clever trader.",
        f"Near the fountain of {tale['place']}, {seller.label} arranged {tale['good']}.",
    ]
    world.say(openings[params.route % len(openings)])
    world.say(
        f"One morning, {seller.label} painted a new descriptor on the sign: "
        f"'{tale['descriptor']}'."
    )
    world.say(
        f"The proud words promised {tale['profit']}, though the goods were still "
        f"{tale['good']}."
    )
    world.para()

    world.facts["offered"] = True
    seller.meters["coins"] += 1.0
    world.say(
        f"Buyers admired the sign, and {seller.label} began to dream of profit "
        f"larger than the village could see."
    )
    world.say(
        f"Then {traveler.label} arrived, tired and hungry, and asked, "
        f'"Could I have a fair portion before I walk on?"'
    )
    world.say(
        f'"A fair portion?" {seller.label} replied. '
        f'"These are {tale["descriptor"]}. Their price is {tale["profit"]}."'
    )
    world.say(
        f'{traveler.label} looked at the sign and then at the goods. '
        f'"A fine descriptor cannot fill an empty stomach," {traveler.label} said.'
    )
    world.para()

    world.say(
        f"Those words troubled {seller.label}. The merchant lifted the goods, "
        f"checked their quality, and smelled the air instead of the sign."
    )
    world.say(f"The truth became clear: {tale['cause']}.")
    world.say(
        f'"You are right," {seller.label} said. "I chased profit and forgot the person before me."'
    )
    world.say(
        f'"Then let the measure speak plainly," {traveler.label} answered.'
    )
    world.facts["honest"] = True
    world.facts["kindness"] = True
    traveler.meters["hunger"] = 0.0
    traveler.meters["need"] = 0.0
    world.say(f"With a kind heart, {seller.label} {tale['repair']}.")
    propagate(world)
    world.para()

    world.say(
        f"That evening, {seller.label} replaced the boastful sign with a simple one: "
        f"'{tale["good"].capitalize()} — honestly measured.'"
    )
    world.say(
        f"The village repeated the old sermon: profit may buy a coin, but kindness "
        f"buys trust."
    )
    world.say(f"By moonrise, {tale['image']}.")
    return world


def generation_prompts(world: World) -> list[str]:
    tale = world.facts["tale"]
    return [
        f"Write a cautionary folk tale in {world.setting.place} about profit and the descriptor '{tale['descriptor']}'.",
        f"Tell a kindness story where a merchant learns that {tale['cause']}.",
        "Write a child-friendly sermon-like ending showing why honest measures matter more than grand words.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale = world.facts["tale"]
    seller: Entity = world.facts["seller"]
    traveler: Entity = world.facts["traveler"]
    return [
        QAItem(
            question=f"What did {seller.label} hope to gain?",
            answer=f"{seller.label} hoped to gain {tale['profit']} by using the impressive descriptor '{tale['descriptor']}' to make the goods seem more valuable.",
        ),
        QAItem(
            question=f"Why did {traveler.label} challenge the merchant?",
            answer=f"{traveler.label} was hungry and needed a fair portion. The traveler reminded the merchant that a beautiful description could not replace useful, honestly measured goods.",
        ),
        QAItem(
            question="What changed the merchant's mind?",
            answer=f"The merchant stopped trusting the grand sign, checked the goods themselves, and understood that {tale['cause']}.",
        ),
        QAItem(
            question="How did kindness solve the problem?",
            answer=f"The merchant admitted the mistake and {tale['repair']}. This helped the traveler and restored trust in the market.",
        ),
        QAItem(
            question="What sermon did the village remember?",
            answer="The village remembered that profit may buy a coin, but kindness buys trust. Honest words and fair measures matter more than proud labels.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is profit?",
            answer="Profit is what remains after someone receives more from a sale than the cost of making or obtaining the thing sold.",
        ),
        QAItem(
            question="What is a descriptor?",
            answer="A descriptor is a word or phrase that tells people what something is like.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating others with care and helping when help is needed.",
        ),
        QAItem(
            question="What is a cautionary tale?",
            answer="A cautionary tale is a story that warns people about a harmful choice and shows a wiser way.",
        ),
        QAItem(
            question="What is a sermon?",
            answer="A sermon is a talk that teaches a moral or spiritual lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.type:11}) "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    seller: str
    tale_index: int = 0
    route: int = 0
    seed: Optional[int] = None


SELLERS = ["Mara", "Oren", "Tilda", "Perrin", "Sela", "Bram", "Nell", "Ansel"]


ASP_RULES = r"""
warning :- offered, not honest.
resolved :- honest, kindness.
fair_trade :- resolved.
#show warning/0.
#show resolved/0.
#show fair_trade/0.
"""


def asp_facts(world: Optional[World] = None) -> str:
    import asp

    facts = [
        asp.fact("offered"),
        asp.fact("honest"),
        asp.fact("kindness"),
    ]
    return "\n".join(facts)


def asp_program(world: Optional[World] = None) -> str:
    return f"{asp_facts(world)}\n{ASP_RULES}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cautionary folk tale about profit, descriptors, sermons, and kindness."
    )
    parser.add_argument("--seller")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seller = args.seller or rng.choice(SELLERS)
    return StoryParams(seller=seller)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def asp_verify() -> int:
    import asp

    world = tell(StoryParams(seller="Mara"))
    model = asp.one_model(asp_program(world))
    names = {symbol.name for symbol in model}
    expected = {"resolved", "fair_trade"}
    if expected.issubset(names) and "warning" not in names:
        print("OK: ASP twin matches the Python kindness resolution.")
        return 0
    print("MISMATCH: ASP twin did not match the resolved Python state.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP atoms:", " ".join(sorted(symbol.name for symbol in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    count = len(TALES) if args.all else args.n
    seen: set[str] = set()
    for index in range(max(0, count)):
        seed = base_seed + index
        rng = random.Random(seed)
        params = resolve_params(args, rng)
        params.seed = seed
        params.tale_index = seed % len(TALES)
        params.route = (seed // len(TALES)) % 5
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)

    if not samples:
        raise StoryError("no stories requested; use -n with a positive number")

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
