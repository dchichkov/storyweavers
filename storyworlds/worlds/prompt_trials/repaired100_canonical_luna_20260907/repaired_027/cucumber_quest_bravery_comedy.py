#!/usr/bin/env python3
"""A comic cucumber quest about bravery, teamwork, and one very slippery vegetable."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    region: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("slippery", "distance", "safe", "clean", "secure"):
            self.meters.setdefault(key, 0.0)
        for key in ("bravery", "worry", "pride", "laughter", "trust", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    friend: str = "Pip"
    cucumber: str = "the giant cucumber"
    quest_place: str = "the village picnic"
    bravery: bool = True
    comedy: bool = True


HEROES = ["Luna", "Mara", "Toby", "Nell", "Zig"]
FRIENDS = ["Pip", "Bobo", "Tansy", "Milo", "Wren"]
CUCUMBERS = [
    "the giant cucumber",
    "the royal cucumber",
    "the wobbly cucumber",
    "the champion cucumber",
]
PLACES = [
    "the village picnic",
    "the mayor's lunch table",
    "the Sunny Fair",
    "the garden parade",
]

QUESTS = [
    {
        "start": "The village's prize cucumber had rolled away just before the grand salad contest.",
        "warning": "Follow the cucumber carefully, and do not chase it downhill.",
        "trouble": "the cucumber bounced over a hill and vanished into a squeaky wheelbarrow",
        "clue": "a trail of wet green spots led toward the old windmill",
        "turn": "crawl beneath the wheelbarrow and grab the handle instead of grabbing the cucumber",
        "action": "braced the wheelbarrow while Pip reached through its spokes",
        "result": "the cucumber popped free and landed in a basket rather than in the mayor's hat",
        "ending": "At the picnic, the cucumber was sliced into neat coins, while the mayor wore a clean hat at last.",
        "lesson": "Bravery does not mean rushing; it means helping carefully when a wobbly problem needs you.",
    },
    {
        "start": "The prize cucumber was supposed to lead the garden parade, but a gust rolled it toward a muddy pond.",
        "warning": "Keep your feet steady, and do not jump into mud after a vegetable.",
        "trouble": "the cucumber spun across the bank and stopped on a little raft",
        "clue": "three ducks quacked whenever the raft drifted left",
        "turn": "use the duck sounds as a rowing signal instead of leaping into the pond",
        "action": "tied a scarf to a rake and pulled the raft back from the reeds",
        "result": "the cucumber returned dry, although one duck received an accidental scarf crown",
        "ending": "The parade began with the cucumber in front and a duck proudly wobbling behind it.",
        "lesson": "A brave helper can solve a soggy problem without becoming the soggy part.",
    },
    {
        "start": "The royal cucumber disappeared from the mayor's table during the cheese-cake rehearsal.",
        "warning": "Look for clues before accusing the nearest hungry person.",
        "trouble": "the cucumber had rolled into a trumpet and made every note sound like a burp",
        "clue": "green hairs stuck out of the trumpet's shining mouth",
        "turn": "tell the truth about the strange sound and inspect the trumpet gently",
        "action": "tilted the trumpet over a cloth while Pip played one tiny note",
        "result": "the cucumber slid out with a loud plop, and the band found its missing lunch",
        "ending": "The parade music resumed, though everyone agreed that the cucumber's solo was unforgettable.",
        "lesson": "Bravery includes admitting what you see, even when the truth sounds like a burp.",
    },
    {
        "start": "The champion cucumber was ready for the fair's tallest-vegetable ribbon when a goat began dragging it away.",
        "warning": "Do not pull against a goat that thinks lunch is a trophy.",
        "trouble": "the goat tugged the cucumber beneath a table and became stuck beside three pies",
        "clue": "the goat's bell jingled whenever it backed toward the pie table",
        "turn": "offer a carrot and guide the goat backward instead of wrestling the vegetable",
        "action": "held the carrot high while Pip eased the cucumber out from under the table",
        "result": "the goat let go, the pies survived, and the cucumber stayed impressively unbitten",
        "ending": "The champion cucumber won its ribbon, while the goat received a carrot medal.",
        "lesson": "Bravery can be gentle when patience works better than a tug-of-war.",
    },
]


def make_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity("hero", "character", params.hero, "child", "village"))
    friend = world.add(Entity("friend", "character", params.friend, "child", "village"))
    cucumber = world.add(
        Entity(
            "cucumber",
            "object",
            params.cucumber,
            "vegetable",
            "garden",
            owner="village",
        )
    )
    hero.memes["pride"] = 1.0
    hero.memes["bravery"] = 1.0
    friend.memes["trust"] = 1.0
    cucumber.meters["secure"] = 1.0
    cucumber.meters["slippery"] = 1.0
    return world


def tell(params: StoryParams) -> World:
    if not params.hero.strip() or not params.friend.strip():
        raise StoryError("Hero and friend names must not be empty.")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must have different names.")

    world = make_world(params)
    hero = world.get("hero")
    friend = world.get("friend")
    cucumber = world.get("cucumber")

    value = params.seed
    if value is None:
        value = sum(ord(ch) for ch in "|".join(vars(params).values() if False else [
            params.hero,
            params.friend,
            params.cucumber,
            params.quest_place,
        ]))
    quest = QUESTS[value % len(QUESTS)]
    rhythm = value % 3

    world.say(
        f"{params.hero} and {params.friend} lived near {params.quest_place}, where "
        f"{params.cucumber} was famous for being large, green, and extremely difficult to keep still."
    )
    world.say(quest["start"])
    world.para()
    world.say(f"{params.friend} pointed at the rolling vegetable. \"{quest['warning']}\"")
    world.say(
        f"{params.hero} puffed up bravely. \"I can handle one cucumber,\" {params.hero} said. "
        f"Then {params.hero} took one step and slipped sideways like a dancing spoon."
    )

    hero.memes["pride"] += 1.0
    hero.memes["worry"] += 1.0
    cucumber.meters["distance"] = 1.0
    cucumber.meters["secure"] = 0.0
    world.say(f"Unfortunately, {quest['trouble']}.")
    world.say(f"The only useful clue was that {quest['clue']}.")
    world.para()

    if rhythm == 0:
        world.say(
            f"\"I am scared,\" admitted {params.hero}, \"but I will not hide behind a cabbage.\" "
            f"\"Good,\" said {params.friend}. \"Cabbages are terrible hiding places.\""
        )
    elif rhythm == 1:
        world.say(
            f"{params.friend} asked, \"Are you ready to be brave?\" "
            f"\"I am ready to be brave very quietly,\" said {params.hero}. "
            f"\"Quiet bravery is still bravery,\" said {params.friend}."
        )
    else:
        world.say(
            f"\"What is the plan?\" asked {params.friend}. "
            f"\"A sensible one,\" said {params.hero}. \"That is disappointing, but sensible.\""
        )

    world.say(f"Instead of making a wild grab, {params.hero} decided to {quest['turn']}.")
    hero.memes["bravery"] += 2.0
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.meters["safe"] = 1.0

    world.say(
        f"Together, {params.hero} and {params.friend} {quest['action']}. "
        f"The cucumber wiggled once, twice, and then made a noise like a tiny trumpet."
    )
    friend.memes["trust"] += 1.0
    hero.memes["relief"] += 1.0
    cucumber.meters["secure"] = 1.0
    cucumber.meters["distance"] = 0.0
    cucumber.meters["clean"] = 1.0
    world.say(f"At last, {quest['result']}.")
    world.para()
    world.say(f"{params.hero} laughed. \"I thought bravery would look grander.\"")
    world.say(f"{params.friend} grinned. \"It usually looks more like helping and less like falling.\"")
    world.say(quest["ending"])
    world.say(f"{params.hero} remembered: {quest['lesson']}")

    world.facts.update(
        hero=hero,
        friend=friend,
        cucumber=cucumber,
        params=params,
        quest=quest,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    cucumber: Entity = world.facts["cucumber"]  # type: ignore[assignment]
    quest: dict[str, str] = world.facts["quest"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Who went on the cucumber quest with {params.friend}?",
            f"{params.hero} went on the quest with {params.friend}. They worked together to recover {cucumber.label}.",
        ),
        QAItem(
            f"Why did {params.hero} and {params.friend} need to find {cucumber.label}?",
            f"{quest['start']} The cucumber had to be recovered before the celebration could continue.",
        ),
        QAItem(
            f"What clue helped {params.hero} and {params.friend}?",
            f"They noticed that {quest['clue']}. That clue showed them where the cucumber had gone.",
        ),
        QAItem(
            f"How did {params.hero} show bravery?",
            f"{params.hero} admitted being scared but chose to {quest['turn']}. The brave choice was careful and helpful rather than reckless.",
        ),
        QAItem(
            f"How did {params.friend} help {params.hero}?",
            f"{params.friend} encouraged {params.hero} and then helped when they {quest['action']}. Their teamwork brought the cucumber back safely.",
        ),
        QAItem(
            "What changed by the end of the story?",
            f"{quest['result']}. The cucumber was safe, the celebration could continue, and the friends learned that {quest['lesson'].lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a cucumber?",
            "A cucumber is a green vegetable that is often crisp, cool, and shaped like a long cylinder.",
        ),
        QAItem(
            "What does bravery mean?",
            "Bravery means doing something helpful or right even when you feel afraid.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is a purposeful journey or task in which someone tries to reach a goal.",
        ),
        QAItem(
            "Why is teamwork useful?",
            "Teamwork is useful because people can share ideas, strength, and care while solving a problem together.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    quest: dict[str, str] = world.facts["quest"]  # type: ignore[assignment]
    return [
        f"Write a funny cucumber quest about {params.hero} and {params.friend}, using bravery to recover {params.cucumber}.",
        f"Tell a child-friendly comedy in which {params.hero} follows the clue that {quest['clue']}.",
        f"Create a short adventure where teamwork saves {params.cucumber} without reckless rushing.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:9} ({entity.type:9}) meters={meters} memes={memes}"
        )
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
brave(hero) :- feels_worry(hero), chooses_help(hero).
quest_done(hero) :- brave(hero), friend_helps(friend), cucumber_safe(cucumber).
comic(hero) :- quest_done(hero), slips(hero).
resolved(hero) :- quest_done(hero), cucumber_safe(cucumber).

#show brave/1.
#show quest_done/1.
#show comic/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("feels_worry", "hero"),
            asp.fact("chooses_help", "hero"),
            asp.fact("friend_helps", "friend"),
            asp.fact("cucumber_safe", "cucumber"),
            asp.fact("slips", "hero"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program())
    actual = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in symbols}
    expected = {"brave/1", "quest_done/1", "comic/1", "resolved/1"}
    if actual == expected:
        sample = generate(StoryParams(seed=17))
        if "cucumber" not in sample.story.lower() or "brav" not in sample.story.lower():
            print("MISMATCH: generated story lacks required domain language")
            return 1
        print("OK: ASP twin and generated cucumber quest agree.")
        return 0
    print("MISMATCH:", sorted(actual), "expected", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A comic cucumber quest about bravery."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--cucumber", choices=CUCUMBERS)
    parser.add_argument("--quest-place", choices=PLACES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    friend = args.friend or rng.choice(FRIENDS)
    if hero == friend:
        friend = next(name for name in FRIENDS if name != hero)
    return StoryParams(
        seed=args.seed,
        hero=hero,
        friend=friend,
        cucumber=args.cucumber or rng.choice(CUCUMBERS),
        quest_place=args.quest_place or rng.choice(PLACES),
        bravery=True,
        comedy=True,
    )


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


CURATED = [
    StoryParams(
        seed=0,
        hero="Luna",
        friend="Pip",
        cucumber="the giant cucumber",
        quest_place="the village picnic",
    ),
    StoryParams(
        seed=1,
        hero="Mara",
        friend="Bobo",
        cucumber="the royal cucumber",
        quest_place="the garden parade",
    ),
    StoryParams(
        seed=2,
        hero="Toby",
        friend="Tansy",
        cucumber="the wobbly cucumber",
        quest_place="the Sunny Fair",
    ),
    StoryParams(
        seed=3,
        hero="Nell",
        friend="Wren",
        cucumber="the champion cucumber",
        quest_place="the mayor's lunch table",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        print(" ".join(str(symbol) for symbol in asp.one_model(asp_program())))
        return

    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for index in range(args.n):
            seed = base_seed + index
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
