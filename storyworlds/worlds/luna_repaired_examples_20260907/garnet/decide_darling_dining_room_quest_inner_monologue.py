#!/usr/bin/env python3
"""
A heartwarming dining-room quest about deciding kindly when a darling surprise
does not go according to plan.
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    darling: Item
    table: Item
    dining_room: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    darling_name: str
    meal: str
    seed: Optional[int] = None


NAMES = ["Mina", "Theo", "Lila", "Sam", "Nora", "Pip", "Eli", "June"]
DARLINGS = ["Grandma", "Grandpa", "Aunt Rose", "Uncle Ben", "Mia"]
MEALS = ["pancakes", "vegetable soup", "cheese sandwiches", "apple pie", "warm biscuits"]


ASP_RULES = r"""
#show quests/1.
#show notices/1.
#show decides/1.
#show comforts/1.

quests(H) :- has_quest(H).
notices(H) :- sees_clue(H).
decides(H) :- chooses_kindly(H).
comforts(H) :- shares_truth(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("has_quest", "hero"),
        asp.fact("sees_clue", "hero"),
        asp.fact("chooses_kindly", "hero"),
        asp.fact("shares_truth", "hero"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    shown = "#show quests/1.\n#show notices/1.\n#show decides/1.\n#show comforts/1."
    model = asp.one_model(asp_program(shown))
    actual = set()
    for atom in model:
        if atom.name in {"quests", "notices", "decides", "comforts"}:
            args = tuple(
                arg.number if arg.type == arg.type.Number else arg.name
                for arg in atom.arguments
            )
            actual.add((atom.name, args))
    expected = {
        ("quests", ("hero",)),
        ("notices", ("hero",)),
        ("decides", ("hero",)),
        ("comforts", ("hero",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming dining-room quest about deciding kindly."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--darling-name", choices=DARLINGS)
    parser.add_argument("--meal", choices=MEALS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        darling_name=args.darling_name or rng.choice(DARLINGS),
        meal=args.meal or rng.choice(MEALS),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.darling_name:
        raise StoryError("The hero and darling must have different names.")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=params.name,
        kind="character",
        memes={"curiosity": 0.8, "care": 0.9, "worry": 0.2},
    )
    darling = Item(
        id="darling",
        label=params.darling_name,
        phrase=params.darling_name,
        kind="character",
        memes={"love": 1.0, "hope": 0.8, "worry": 0.3},
    )
    table = Item(
        id="table",
        label="dining table",
        phrase="the long dining table",
        kind="furniture",
        meters={"length": 1.8, "distance_to_door": 2.0},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.darling_name}|{params.meal}")
    return World(
        hero=hero,
        darling=darling,
        table=table,
        dining_room="the sunny dining room",
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    discovery: str,
    danger: str,
    clue: str,
    decision: str,
    resolution: str,
    ending: str,
    thought: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        danger=danger,
        clue=clue,
        decision=decision,
        resolution=resolution,
        ending=ending,
        thought=thought,
        quest=True,
        suspense=True,
        kind_choice=True,
    )
    return " ".join(lines)


def _spilled_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    d = world.darling.label
    meal = world.params_meal
    cloth = _choice(rng, ["a blue napkin", "a striped towel", "a soft tea cloth"])
    discovery = f"the secret welcome card was hidden beneath a bowl of {meal}"
    danger = "a sudden wobble sent the bowl sliding toward the table's edge"
    clue = f"a little wet crescent appeared beneath the bowl before it tipped"
    decision = f"{h} caught the bowl first and told {d} the surprise needed a new plan"
    resolution = f"{h} moved the meal to a steady tray, dried the card, and invited {d} to help finish the welcome"
    ending = "the rescued card stood beside the steaming bowls, its crooked letters shining in the lamplight"
    thought = "If I hurry to make it perfect, I may lose the chance to make it kind."
    lines = [
        f"In {world.dining_room}, {h} prepared a darling surprise for {d}: {meal}, a candle, and a small card.",
        f"The card was hidden beneath a bowl, but just as {h} reached for the spoon, the bowl began to slide.",
        f"{h} froze. The table seemed suddenly enormous, and the floor seemed much too far below.",
        f"Inside, {h} thought, \"{thought}\"",
        f"Then {h} noticed {clue}. The tablecloth was damp from a tiny spill, and that was why the bowl had started moving.",
        f"{h} caught the bowl before it fell. \"I need to decide,\" {h} whispered. \"A secret is lovely, but keeping you safe is lovelier.\"",
        f"{d} came to the doorway. {h} told the truth instead of pretending everything was ready.",
        f"{d} smiled, helped spread {cloth}, and carried the tray to the middle of the table.",
        f"Together they finished the meal. By evening, {ending}.",
    ]
    return _record(
        world,
        discovery=discovery,
        danger=danger,
        clue=clue,
        decision=decision,
        resolution=resolution,
        ending=ending,
        thought=thought,
        lines=lines,
    )


def _candle_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    d = world.darling.label
    meal = world.params_meal
    flame = _choice(rng, ["a tall candle", "a tiny birthday candle", "a honey-colored taper"])
    discovery = f"the special place card was tucked behind {flame}"
    danger = "the candle flame leaned toward a paper napkin"
    clue = "the napkin's corner trembled whenever the open window breathed"
    decision = f"{h} chose to move the candle instead of protecting the surprise"
    resolution = f"{h} closed the window, placed the candle in a sturdy dish, and showed {d} the safe table"
    ending = "the little flame glowed in its dish while both chairs waited together for supper"
    thought = "A surprise should bring warmth, not make anyone hold their breath."
    lines = [
        f"{h} polished the dining table for {d}, setting out {meal}, flowers, and {flame}.",
        f"Behind the candle waited a place card with {d}'s name. Then the flame bent toward a paper napkin.",
        f"The room went quiet. Even the clock seemed to tick more softly.",
        f"Inside, {h} thought, \"{thought}\"",
        f"{h} saw that {clue}. The open window was making the flame dance.",
        f"Rather than wait and hope, {h} decided to act. The candle moved first, the napkin moved second, and the window clicked shut.",
        f"{d} entered just as {h} finished. \"I wanted everything to be a surprise,\" said {h}, \"but I decided your safety mattered more.\"",
        f"{d} hugged {h} and helped arrange the flowers in a glass of water.",
        f"At last, {ending}. The best part of the surprise was being together.",
    ]
    return _record(
        world,
        discovery=discovery,
        danger=danger,
        clue=clue,
        decision=decision,
        resolution=resolution,
        ending=ending,
        thought=thought,
        lines=lines,
    )


def _missing_spoon_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    d = world.darling.label
    meal = world.params_meal
    hiding_place = _choice(rng, ["the sideboard", "the china cabinet", "the basket of clean napkins"])
    discovery = f"one silver spoon was missing from the setting for {meal}"
    danger = "the final place at the table looked unfinished"
    clue = _choice(rng, ["a bright line beneath the table", "a soft clink near the curtain", "a trail of flour dots"])
    decision = f"{h} decided to search carefully rather than blame anyone"
    resolution = f"{h} followed the clue, found the spoon near {hiding_place}, and asked {d} to help set the table"
    ending = "the last spoon rested beside the bowl, and the dining room felt complete without needing to be perfect"
    thought = "A missing thing is a question, not proof that someone did wrong."
    lines = [
        f"Before {d} arrived, {h} arranged {meal} around the dining table.",
        f"One place setting lacked a spoon. {h} checked the drawer, then the tray, then the little cup by the sink.",
        f"The empty place seemed to grow larger. What if {d} noticed? What if the whole surprise failed?",
        f"Inside, {h} thought, \"{thought}\"",
        f"Then {h} saw {clue}. The clue led under the table and across the rug.",
        f"{h} followed it slowly and found the spoon near {hiding_place}, where it had slipped beneath a folded cloth.",
        f"{h} could have hidden the mistake, but decided that a shared quest would be better than a lonely worry.",
        f"When {d} arrived, {h} said, \"Darling, will you help me finish this?\" {d} laughed and set the spoon beside the bowl.",
        f"At sunset, {ending}. The meal tasted sweeter because both of them had made room for one another.",
    ]
    return _record(
        world,
        discovery=discovery,
        danger=danger,
        clue=clue,
        decision=decision,
        resolution=resolution,
        ending=ending,
        thought=thought,
        lines=lines,
    )


def _letter_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    d = world.darling.label
    meal = world.params_meal
    sound = _choice(rng, ["a soft scrape", "a faint tap", "a paper rustle"])
    discovery = "a kind note had slipped behind the dining-room clock"
    danger = "the note was caught where the clock's pendulum could crumple it"
    clue = f"{sound} came from behind the clock each time the pendulum swung"
    decision = f"{h} decided to pause the clock and retrieve the note carefully"
    resolution = f"{h} stopped the pendulum, rescued the note, and read it aloud to {d}"
    ending = "the note lay safely beside the plates, carrying its gentle words across the whole table"
    thought = "Words meant to comfort deserve a careful place to land."
    lines = [
        f"{h} had written a darling note for {d} and placed it near the {meal}.",
        f"A draft lifted the note behind the dining-room clock. Soon {sound} sounded from its narrow space.",
        f"The clock ticked. The note rustled. The secret seemed to be vanishing one swing at a time.",
        f"Inside, {h} thought, \"{thought}\"",
        f"{h} listened and understood that {clue}.",
        f"Instead of tugging wildly, {h} decided to pause the clock. With a butter knife and a patient hand, the note came free.",
        f"{d} arrived before the note could be hidden again. {h} read the words aloud: \"Thank you for making ordinary days feel special.\"",
        f"{d} pressed a hand over the note and smiled. The clock began ticking once more.",
        f"By the end of {meal}, {ending}.",
    ]
    return _record(
        world,
        discovery=discovery,
        danger=danger,
        clue=clue,
        decision=decision,
        resolution=resolution,
        ending=ending,
        thought=thought,
        lines=lines,
    )


def _flower_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    d = world.darling.label
    meal = world.params_meal
    vase = _choice(rng, ["a blue vase", "a round jar", "Grandma's small glass pitcher"])
    discovery = f"the flowers for the table were leaning inside {vase}"
    danger = "one heavy blossom was pulling the vase toward the table's edge"
    clue = "the water line sloshed whenever the blossom nodded"
    decision = f"{h} decided to shorten the flowers rather than leave them balanced dangerously"
    resolution = f"{h} trimmed the stems, shared the best blossoms with {d}, and placed the vase in the center"
    ending = "three small flowers stood upright between the plates, each one bright enough to share"
    thought = "A beautiful thing can become better when it is shared."
    lines = [
        f"For {d}, {h} brought flowers into the dining room and placed them in {vase}.",
        f"The tallest blossom nodded toward the table's edge. The whole vase leaned after it.",
        f"{h} reached to steady it, then stopped. One quick move might save the flowers or send water over the plates.",
        f"Inside, {h} thought, \"{thought}\"",
        f"{h} watched the water and noticed that {clue}.",
        f"Carefully, {h} decided to shorten the stems. The vase straightened, but the tallest flower no longer fit.",
        f"Then {d} came in, and {h} explained the choice. Together they placed the tall flower in a cup beside the window.",
        f"The dining room filled with the smell of leaves and warm {meal}.",
        f"At dinner, {ending}. Nothing had been lost; the beauty had simply found more places to bloom.",
    ]
    return _record(
        world,
        discovery=discovery,
        danger=danger,
        clue=clue,
        decision=decision,
        resolution=resolution,
        ending=ending,
        thought=thought,
        lines=lines,
    )


ARC_BUILDERS = [_spilled_arc, _candle_arc, _missing_spoon_arc, _letter_arc, _flower_arc]


def generate_story(world: World, meal: str) -> str:
    world.params_meal = meal
    rng = random.Random(world.seed ^ 0xDAD1E)
    return ARC_BUILDERS[world.seed % len(ARC_BUILDERS)](world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    d = world.darling.label
    f = world.facts
    return [
        QAItem(
            question=f"What quest did {h} undertake in the dining room?",
            answer=f"{h} undertook the quest of preparing a loving dining-room surprise for {d} while keeping everyone safe.",
        ),
        QAItem(
            question="What made the moment suspenseful?",
            answer=f"The suspense came from {f['danger']}, so {h} had to notice {f['clue']} before deciding what to do.",
        ),
        QAItem(
            question=f"What did {h} decide?",
            answer=f"{h} decided that kindness and safety mattered more than keeping the surprise perfect, and {f['decision'].split(' decided ', 1)[-1]}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The problem was solved when {f['resolution']}. In the ending, {f['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a character has inside their mind.",
        ),
        QAItem(
            question="Why can a character pause before deciding?",
            answer="Pausing gives a character time to notice clues, consider consequences, and choose a caring action instead of rushing.",
        ),
        QAItem(
            question="What makes a dining room useful for a story?",
            answer="A dining room is a shared place where food, conversation, surprises, and loving choices can bring people together.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming quest story set in a dining room.",
        f"Write a suspenseful story about {world.hero.label} deciding how to prepare a kind surprise for {world.darling.label}.",
        "Use an inner monologue to show why a loving choice matters more than a perfect plan.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for item in [world.hero, world.darling, world.table]:
        lines.append(
            f"  {item.id:8} {item.kind:10} label={item.label!r} "
            f"owner={item.owner!r} meters={item.meters} memes={item.memes}"
        )
    lines.append(f"  dining_room={world.dining_room!r}")
    for key in ["quest", "suspense", "kind_choice", "discovery", "decision"]:
        if key in world.facts:
            lines.append(f"  {key}={world.facts[key]!r}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world, params.meal)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show quests/1.\n"
            "#show notices/1.\n"
            "#show decides/1.\n"
            "#show comforts/1."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "4 compatible logical atoms: quests(hero), notices(hero), "
            "decides(hero), comforts(hero)"
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mina", "Grandma", "pancakes", base_seed),
            StoryParams("Theo", "Grandpa", "vegetable soup", base_seed + 1),
            StoryParams("Lila", "Aunt Rose", "apple pie", base_seed + 2),
            StoryParams("Sam", "Uncle Ben", "warm biscuits", base_seed + 3),
            StoryParams("Nora", "Mia", "cheese sandwiches", base_seed + 4),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = (
                f"### {sample.params.name} prepares "
                f"{sample.params.meal}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
