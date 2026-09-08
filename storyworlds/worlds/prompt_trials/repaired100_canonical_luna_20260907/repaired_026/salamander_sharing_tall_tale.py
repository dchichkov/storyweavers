#!/usr/bin/env python3
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "salamander"
    helper: str = "frog"
    place: str = "the thunder valley"
    hero_name: str = "Luna"
    helper_name: str = "Bramble"
    feast: str = "the moonlit berry feast"


HERO_NAMES = ["Luna", "Ember", "Saffron", "Mica", "Puddle", "Cinder"]
HELPER_NAMES = ["Bramble", "Moss", "Tumble", "Wisp", "Nettle", "Pebble"]
PLACES = [
    "the thunder valley",
    "the upside-down orchard",
    "the singing marsh",
    "the mountain of blue rain",
    "the hollow beneath the giant moon",
]
FEASTS = [
    "the moonlit berry feast",
    "the sunrise soup supper",
    "the festival of enormous pancakes",
    "the valley's warm-cocoa banquet",
]


ARCS = [
    {
        "object": "a basket of sunberries",
        "amount": "three baskets",
        "problem": "a storm had washed away the travelers' breakfast",
        "share": "carried the berries across the valley in one enormous leap",
        "result": "every traveler received a bright handful, and the empty basket began to sing",
        "ending": "the shared berries glowed like a second sunrise beneath the moon",
        "lesson": "A small share can feed a very large hope.",
    },
    {
        "object": "a steaming stone-pot of soup",
        "amount": "a whole river of soup",
        "problem": "the mountain climbers were cold enough to make icicles shiver",
        "share": "pushed the pot up the slope with her broad tail and invited everyone to take a bowl",
        "result": "the climbers thawed so quickly that their laughter melted the frost",
        "ending": "the soup pot warmed the valley until even the snow applauded",
        "lesson": "Warmth grows when everyone gets a place beside it.",
    },
    {
        "object": "a sack of silver mushrooms",
        "amount": "a mountain-sized sack",
        "problem": "the village baker had no filling for the great festival pies",
        "share": "split the mushrooms into equal piles and rolled each pile to a hungry kitchen",
        "result": "the bakers made enough pies to circle the valley twice",
        "ending": "the last pie rose so high that a cloud asked for a slice",
        "lesson": "What is shared can become bigger than anyone imagined.",
    },
    {
        "object": "a jar of firefly honey",
        "amount": "one glowing jar",
        "problem": "the night travelers had lost their way in the dark reeds",
        "share": "opened the jar and let its golden glow guide every traveler home",
        "result": "the path shone so brightly that the moon followed it",
        "ending": "the whole marsh twinkled with lights borrowed from one generous jar",
        "lesson": "A light shared with others never becomes dimmer.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Tall Tale storyworld about Luna the salamander and sharing."
    )
    parser.add_argument("--hero", default=None, choices=["salamander"])
    parser.add_argument("--helper", default=None, choices=["frog", "newt", "mouse"])
    parser.add_argument("--place", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--helper-name", default=None)
    parser.add_argument("--feast", default=None)
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
    helper = args.helper or rng.choice(["frog", "newt", "mouse"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    place = args.place or rng.choice(PLACES)
    feast = args.feast or rng.choice(FEASTS)
    if hero_name == helper_name:
        raise StoryError("hero and helper must have different names")
    if not place.strip():
        raise StoryError("place must not be empty")
    return StoryParams(
        seed=args.seed,
        hero="salamander",
        helper=helper,
        place=place,
        hero_name=hero_name,
        helper_name=helper_name,
        feast=feast,
    )


def make_world(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(
        Entity(
            "hero",
            "character",
            "salamander",
            params.hero_name,
            meters={"leap": 1.0, "warmth": 0.8, "share": 0.0},
            memes={"pride": 0.5, "generosity": 0.8, "joy": 0.2},
        )
    )
    helper = world.add(
        Entity(
            "helper",
            "character",
            params.helper,
            params.helper_name,
            meters={"leap": 0.4},
            memes={"worry": 0.7, "trust": 0.5},
        )
    )
    travelers = world.add(
        Entity(
            "travelers",
            "group",
            "travelers",
            "the stranded travelers",
            meters={"hunger": 1.0, "cold": 0.6},
            memes={"hope": 0.2},
        )
    )
    world.facts.update(hero=hero, helper=helper, travelers=travelers)
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    seed = params.seed if params.seed is not None else sum(map(ord, params.hero_name + params.place))
    rng = random.Random(seed ^ 0x5A1A)
    arc = rng.choice(ARCS)
    hero = world.get("hero")
    helper = world.get("helper")
    travelers = world.get("travelers")

    treasure = world.add(
        Entity(
            "treasure",
            "food",
            "shared_food",
            arc["object"],
            meters={"amount": 1.0, "warmth": 0.5},
            memes={"comfort": 0.6},
            owner=hero.id,
        )
    )
    world.facts.update(
        arc=arc,
        object=treasure,
        object_name=arc["object"],
        amount=arc["amount"],
        problem=arc["problem"],
        share_action=arc["share"],
        result=arc["result"],
        ending=arc["ending"],
        lesson=arc["lesson"],
        shared=False,
        place=params.place,
        feast=params.feast,
    )

    world.say(
        f"In {params.place}, Luna the salamander was famous for one thing: "
        f"she could make an ordinary kindness taller than a castle."
    )
    world.say(
        f"One morning, while preparing for {params.feast}, {hero.label} discovered "
        f"{arc['object']} beside a stone that was wider than a wagon."
    )
    world.para()
    world.say(
        f"Just then, {helper.label} hurried in. \"We have a problem,\" "
        f"{helper.label} said. \"{arc['problem'].capitalize()}.\""
    )
    world.say(
        f"{hero.label} curled her tail around {arc['object']}. "
        f"\"It belongs at our feast,\" she said. \"But a feast is not much of a feast "
        f"if hungry friends cannot reach it.\""
    )
    world.say(
        f"\"Do you mean to share it?\" asked {helper.label}. "
        f"\"Even though there are {arc['amount']}?\""
    )
    world.say(
        f"\"Especially because there are {arc['amount']}!\" {hero.label} replied."
    )
    world.para()
    world.say(
        f"With one mighty hop, {hero.label} {arc['share']}. "
        f"The leap was so grand that three clouds moved aside to watch."
    )
    world.say(
        f"The travelers gasped. \"Will there be enough for us?\" one asked."
    )
    world.say(
        f"\"There will be enough when we share carefully,\" said {hero.label}. "
        f"{helper.label} divided the food while {hero.label} welcomed everyone to the feast."
    )
    world.say(f"{arc['result'].capitalize()}.")
    world.para()
    world.say(
        f"When the feast began, {helper.label} raised a bowl. "
        f"\"Luna, you could have kept this treasure for yourself,\" "
        f"{helper.label} said. \"Why did you give it away?\""
    )
    world.say(
        f"{hero.label} smiled. \"Because one happy belly is good, but many happy "
        f"hearts can shake the stars.\""
    )
    world.say(
        f"By sunset, {arc['ending']}. The travelers were safe, the feast was full, "
        f"and {hero.label}'s generosity had become the tallest wonder in the valley."
    )

    hero.meters["share"] = 1.0
    hero.memes["joy"] = 1.0
    hero.memes["generosity"] = 1.0
    helper.memes["worry"] = 0.0
    helper.memes["trust"] = 1.0
    travelers.meters["hunger"] = 0.0
    travelers.meters["cold"] = 0.0
    travelers.memes["hope"] = 1.0
    treasure.meters["amount"] = 0.0
    treasure.owner = None
    world.facts["shared"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a Tall Tale for children about Luna the salamander sharing {f['object_name']} in {f['place']}.",
        f"Tell a huge, playful story in which a salamander shares food with travelers even though {f['problem']}.",
        f"Create a child-friendly Tall Tale showing how sharing makes {f['object_name']} help an entire valley.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.get("hero")
    helper = world.get("helper")
    return [
        QAItem(
            question=f"What did {hero.label} find before {f['feast']}?",
            answer=f"{hero.label} found {f['object_name']} beside a huge stone and planned to bring it to the feast.",
        ),
        QAItem(
            question=f"What problem did {helper.label} tell {hero.label} about?",
            answer=f"{helper.label} explained that {f['problem']}.",
        ),
        QAItem(
            question=f"How did {hero.label} share the treasure?",
            answer=f"{hero.label} {f['share_action']}, and the food was divided carefully among the travelers and feast guests.",
        ),
        QAItem(
            question="What changed after the sharing?",
            answer=f"{f['result'].capitalize()} The travelers became safe and hopeful instead of hungry and worried.",
        ),
        QAItem(
            question="What lesson did the Tall Tale show?",
            answer=f"The story showed that {f['lesson'].lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a salamander?",
            answer="A salamander is a small amphibian with a long body and tail; many salamanders like damp places.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, enjoy, or receive part of something that you have.",
        ),
        QAItem(
            question="Why can sharing help a group?",
            answer="Sharing can help a group because resources and happiness are spread so more people can take part.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 3) for k, v in entity.meters.items()}
        memes = {k: round(v, 3) for k, v in entity.memes.items()}
        lines.append(
            f"  {entity.id}: type={entity.type}, meters={meters}, memes={memes}, owner={entity.owner}"
        )
    lines.append(f"  shared={world.facts.get('shared')}")
    return "\n".join(lines)


ASP_RULES = r"""
fed(food).
has(hero,food).
needs(travelers,food).
shared(food) :- fed(food), has(hero,food), needs(travelers,food), chose_sharing(hero).
helped(travelers) :- shared(food).
chose_sharing(hero).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("food", "food"),
            asp.fact("travelers", "travelers"),
            asp.fact("fed", "food"),
            asp.fact("has", "hero", "food"),
            asp.fact("needs", "travelers", "food"),
            asp.fact("chose_sharing", "hero"),
        ]
    )


def asp_program(show: str = "#show shared/1. #show helped/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    found = {
        (symbol.name, tuple(
            arg.number if arg.type.name == "Number" else arg.name
            for arg in symbol.arguments
        ))
        for symbol in model
        if symbol.name in {"shared", "helped"}
    }
    expected = {("shared", ("food",)), ("helped", ("travelers",))}
    if found != expected:
        print("MISMATCH between ASP and Python sharing assumptions.")
        print("got:", sorted(found))
        print("expected:", sorted(expected))
        return 1

    sample = generate(StoryParams(seed=7))
    if "share" not in sample.story.lower() or "salamander" not in sample.story.lower():
        print("MISMATCH: generated story lacks required domain evidence.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


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
    StoryParams(
        seed=101,
        hero="salamander",
        helper="frog",
        place="the thunder valley",
        hero_name="Luna",
        helper_name="Bramble",
        feast="the moonlit berry feast",
    ),
    StoryParams(
        seed=202,
        hero="salamander",
        helper="newt",
        place="the singing marsh",
        hero_name="Ember",
        helper_name="Moss",
        feast="the sunrise soup supper",
    ),
    StoryParams(
        seed=303,
        hero="salamander",
        helper="mouse",
        place="the upside-down orchard",
        hero_name="Saffron",
        helper_name="Tumble",
        feast="the festival of enormous pancakes",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show shared/1. #show helped/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print("ASP atoms:")
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            try:
                params = resolve_params(local_args, random.Random(seed))
            except StoryError:
                continue
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
