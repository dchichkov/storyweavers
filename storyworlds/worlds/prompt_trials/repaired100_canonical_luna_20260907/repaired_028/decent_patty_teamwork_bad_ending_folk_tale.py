#!/usr/bin/env python3
"""
A small folk tale about Patty, a decent child, and the trouble caused by
trying to finish a hard task alone.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"hill": 0.0, "barn": 0.0})
    memes: dict[str, float] = field(
        default_factory=lambda: {"kindness": 0.0, "pride": 0.0, "worry": 0.0, "trust": 0.0}
    )


@dataclass
class Object:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: {"weight": 0.0, "height": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"value": 0.0, "safety": 0.0})


@dataclass
class World:
    setting: str
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, Object] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
    hero_name: str = "Patty"
    helper_name: str = "Nell"
    friend_name: str = "Tom"
    setting: str = "the village hill"
    prize: str = "a warm berry patty"


@dataclass(frozen=True)
class Arc:
    key: str
    task: str
    rush: str
    bad: str
    question: str
    teamwork: str
    result: str
    ending: str
    lesson: str


ARCS = [
    Arc(
        "hill_cart",
        "carry a little cart of berry patties up the steep hill for the village feast",
        "Patty seized both handles and pulled without waiting for anyone",
        "the cart rolled sideways, the patties tumbled into the dusty road, and the feast bell rang before supper was ready",
        "What if we push from the back while you guide the front?",
        "Patty held the handles, Nell steadied the baskets, and Tom placed flat stones beneath the wheels",
        "With three pairs of hands, the cart climbed safely to the feast tent",
        "At sunset, every villager ate a warm patty beneath the red-gold sky",
        "a decent heart is strongest when it makes room for other hands",
    ),
    Arc(
        "broken_bridge",
        "bring a basket of patties across the little creek before the evening meal",
        "Patty tried to carry the basket while hopping over the bridge's loose middle plank",
        "the plank cracked, the basket tipped, and the supper patties floated downstream",
        "Who can hold the basket while we mend the crossing?",
        "Patty carried the food only after Nell tied a rope and Tom braced the bridge with two branches",
        "They crossed one careful step at a time and saved enough patties for every table",
        "The repaired bridge shone with dew while neighbors shared the last sweet bite",
        "asking for help can save both a meal and a friendship",
    ),
    Arc(
        "windmill_sail",
        "raise a new cloth sail on the old windmill before the flour ran out",
        "Patty climbed alone with the heavy cloth tucked beneath one arm",
        "the cloth caught the wind, the ladder swayed, and Patty dropped the village bell rope",
        "Who can hold the ladder while we lift the sail together?",
        "Nell anchored the ladder, Tom pulled the rope, and Patty tied each knot slowly",
        "The windmill turned again and ground enough grain for the village bread",
        "The bell rang clearly because every helper had a safe part to play",
        "brave work becomes wise work when it is shared",
    ),
]


HERO_NAMES = ["Patty", "Mara", "Pip", "Della"]
HELPER_NAMES = ["Nell", "Ruth", "Anya", "Milo"]
FRIEND_NAMES = ["Tom", "Bram", "Jo", "Sela"]
PRIZES = ["a warm berry patty", "a honey patty", "a golden oat patty", "a little apple patty"]


def build_world(params: StoryParams) -> World:
    if params.setting != "the village hill":
        raise StoryError("This folk tale belongs on the village hill.")
    if params.hero_name == params.helper_name or params.hero_name == params.friend_name:
        raise StoryError("The three village helpers must have different names.")

    world = World(setting=params.setting)
    hero = Character(params.hero_name, "decent village child")
    helper = Character(params.helper_name, "careful neighbor")
    friend = Character(params.friend_name, "strong friend")
    feast = Object(params.prize, "shared food")
    world.characters = {hero.name: hero, helper.name: helper, friend.name: friend}
    world.objects = {feast.name: feast}
    world.facts.update(hero=hero, helper=helper, friend=friend, feast=feast)
    return world


def narrate(world: World, seed: int) -> None:
    rng = random.Random(seed ^ 0xA17E)
    arc = rng.choice(ARCS)
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    friend: Character = world.facts["friend"]
    feast: Object = world.facts["feast"]

    hero.memes["kindness"] = 1.0
    hero.memes["pride"] = 1.0
    helper.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0

    world.facts.update(arc=arc, failure=arc.bad, teamwork=arc.teamwork)

    world.say(
        f"Long ago, on the village hill, {hero.name} was known as a decent child who shared bread, "
        f"returned lost buttons, and never left a neighbor to carry a burden alone."
    )
    world.say(
        f"One bright morning, the village elder asked {hero.name} to {arc.task}. "
        f"The reward would be {feast.name} at the evening feast."
    )
    world.say(f"{hero.name} smiled, but pride puffed up like a little sail.")
    world.say(f'"I can do it myself," {hero.name} said.')
    world.say(f'"A hard task is lighter with friends," {helper.name} warned.')
    world.say(f'"I will call you when I need you," {hero.name} replied, and hurried away.')

    world.para()
    world.say(f"At first, {hero.name} worked quickly. Then {hero.name} {arc.rush}.")
    world.say(f"The work grew heavy, and the first shortcut brought a bad ending: {arc.bad}.")
    hero.memes["worry"] = 1.0
    world.say(
        f"{hero.name} sat in the dust, listening to the village feast bell ring far away. "
        f"The decent child felt worry, because a promise had been made and broken."
    )

    world.para()
    world.say(f"{helper.name} and {friend.name} came along the path.")
    world.say(f'"Do not hide your trouble," said {helper.name}. "Tell us what happened."')
    world.say(f'{hero.name} lowered their eyes. "{arc.question}"')
    world.say(f'"Yes," said {friend.name}. "Your work is not a wall around you. It is a bridge to us."')
    world.say(f"Together they {arc.teamwork}.")
    hero.memes["trust"] = 1.0
    hero.memes["pride"] = 0.0
    helper.memes["trust"] = 2.0
    friend.memes["trust"] = 2.0

    world.para()
    feast.memes["safety"] = 1.0
    feast.memes["value"] = 1.0
    world.say(f"The plan worked. {arc.result}.")
    world.say(
        f"{hero.name} thanked {helper.name} and {friend.name}, then divided {feast.name} into fair pieces."
    )
    world.say(f'"I thought asking for help would make me small," {hero.name} said.')
    world.say(f'"It made the whole village strong," {helper.name} answered.')
    world.say(f"{arc.ending}.")
    world.say(f"And that is why the old villagers still say: {arc.lesson}.")


def generation_prompts(world: World) -> list[str]:
    hero: Character = world.facts["hero"]
    feast: Object = world.facts["feast"]
    return [
        f"Write a child-friendly folk tale about a decent child named {hero.name}.",
        f"Make {hero.name} learn teamwork after a bad ending threatens a shared {feast.name}.",
        "Use a clear beginning, failed solo attempt, spoken dialogue, teamwork, and a changed ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    friend: Character = world.facts["friend"]
    feast: Object = world.facts["feast"]
    arc: Arc = world.facts["arc"]
    return [
        QAItem(
            f"Why was {hero.name} considered decent?",
            f"{hero.name} was considered decent because they shared bread, returned lost buttons, and usually helped neighbors.",
        ),
        QAItem(
            f"What happened when {hero.name} tried to do the task alone?",
            f"The rushed solo attempt caused a bad ending: {arc.bad}.",
        ),
        QAItem(
            f"Who helped {hero.name}?",
            f"{helper.name} and {friend.name} helped by sharing the work and making the task safe.",
        ),
        QAItem(
            "How did teamwork change the outcome?",
            f"Together they {arc.teamwork}, so {arc.result}.",
        ),
        QAItem(
            "What lesson did the folk tale teach?",
            f"It taught that {arc.lesson}. The shared food was divided fairly at the end.",
        ),
        QAItem(
            f"What was shared at the feast?",
            f"The villagers shared {feast.name}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is teamwork?",
            "Teamwork is people cooperating, sharing jobs, and helping one another reach a goal.",
        ),
        QAItem(
            "Why can trying to work alone be risky?",
            "Trying to work alone can be risky when a task is heavy, high, fragile, or too difficult for one person to manage safely.",
        ),
        QAItem(
            "What is a bad ending in a story?",
            "A bad ending is an unwanted result caused by a mistake, danger, or problem before the characters find a better path.",
        ),
        QAItem(
            "What does decent mean?",
            "Decent means kind, fair, honest, and willing to treat other people well.",
        ),
    ]


ASP_RULES = r"""
person(hero).
person(helper).
person(friend).
food(shared_food).
setting(village_hill).

task(shared_food).
needs_teamwork(task).
solo_attempt(task).
bad_ending(task) :- solo_attempt(task), needs_teamwork(task).
asks_for_help(task).
teamwork(task) :- asks_for_help(task), needs_teamwork(task).
good_ending(task) :- teamwork(task).

#show bad_ending/1.
#show teamwork/1.
#show good_ending/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("person", "hero"),
            asp.fact("person", "helper"),
            asp.fact("person", "friend"),
            asp.fact("food", "shared_food"),
            asp.fact("setting", "village_hill"),
            asp.fact("task", "shared_food"),
            asp.fact("needs_teamwork", "task"),
            asp.fact("solo_attempt", "task"),
            asp.fact("asks_for_help", "task"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    show = "#show bad_ending/1.\n#show teamwork/1.\n#show good_ending/1."
    model = asp.one_model(asp_program(show))
    found = {(sym.name, tuple(str(a) for a in sym.arguments)) for sym in model}
    expected = {
        ("bad_ending", ("shared_food",)),
        ("teamwork", ("shared_food",)),
        ("good_ending", ("shared_food",)),
    }
    if found == expected:
        sample = generate(StoryParams(seed=17))
        required = ["decent", "bad ending", "teamwork", "Patty", "feast"]
        if all(word.lower() in sample.story.lower() for word in required):
            print("OK: ASP/Python parity and story exercise passed.")
            return 0
        print("MISMATCH: generated story missed required narrative facts.")
        return 1
    print("MISMATCH between ASP and Python facts.")
    print("ASP atoms:", sorted(found))
    print("Expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A folk tale about Patty, teamwork, and a bad ending.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--hero", dest="hero_name", choices=HERO_NAMES)
    parser.add_argument("--helper", dest="helper_name", choices=HELPER_NAMES)
    parser.add_argument("--friend", dest="friend_name", choices=FRIEND_NAMES)
    parser.add_argument("--prize", choices=PRIZES)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
        prize=args.prize or rng.choice(PRIZES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world, params.seed if params.seed is not None else 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def trace_text(world: World) -> str:
    lines = ["--- world trace ---"]
    for character in world.characters.values():
        lines.append(
            f"{character.name}: meters={character.meters} memes={character.memes}"
        )
    for obj in world.objects.values():
        lines.append(f"{obj.name}: meters={obj.meters} memes={obj.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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
        print(trace_text(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/1.\n#show teamwork/1.\n#show good_ending/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program("#show bad_ending/1.\n#show teamwork/1.\n#show good_ending/1.")
        )
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(
                seed=base_seed,
                hero_name="Patty",
                helper_name="Nell",
                friend_name="Tom",
                prize="a warm berry patty",
            ),
            StoryParams(
                seed=base_seed + 1,
                hero_name="Mara",
                helper_name="Ruth",
                friend_name="Bram",
                prize="a honey patty",
            ),
            StoryParams(
                seed=base_seed + 2,
                hero_name="Della",
                helper_name="Anya",
                friend_name="Sela",
                prize="a golden oat patty",
            ),
        ]
    else:
        params_list = []
        for index in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]

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
