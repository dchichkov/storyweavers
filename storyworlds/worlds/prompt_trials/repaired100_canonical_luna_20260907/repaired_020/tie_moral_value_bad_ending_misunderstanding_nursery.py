#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a tie, a mistaken promise, and a kinder
way to finish a troublesome day.
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
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str = "the little nursery"
    has_tie_hook: bool = True


@dataclass
class StoryParams:
    place: str = "nursery"
    hero: str = "Luna"
    friend: str = "Pip"
    keeper: str = "Mabel"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


ARCS = [
    {
        "tie": "a red wool tie with a moon stitched in white",
        "claim": "Pip thought Luna had promised the tie to him forever",
        "truth": "Luna had only promised that Pip could wear it for the puppet parade",
        "tangle": "the tie caught on a rocking horse and pulled the puppet wagon sideways",
        "fix": "Luna stopped the wagon, freed the knot, and asked Pip to help hang the tie on its hook",
        "moral": "A promise should be clear, and a shared thing should be returned with care",
        "ending": "the red tie rested on its hook while the puppets bowed in a tidy row",
    },
    {
        "tie": "a yellow ribbon tie that shone like a little sun",
        "claim": "Pip thought Luna had said he could keep the bright tie",
        "truth": "Luna had said he could keep it on his costume until the song was done",
        "tangle": "the ribbon slipped from the costume and wrapped around a bell cart",
        "fix": "Luna rang the bell once, stopped the cart, and untied the ribbon with Pip",
        "moral": "Kind words must be heard carefully, and borrowed treasures must come home",
        "ending": "the yellow tie slept in its basket as the nursery bell gave one soft ding",
    },
    {
        "tie": "a blue silk tie sprinkled with tiny silver stars",
        "claim": "Pip thought Luna had given him the tie as a present",
        "truth": "Luna had only lent it for the bedtime show",
        "tangle": "the tie dragged through a tray of blocks and scattered them across the floor",
        "fix": "Luna gathered the blocks, loosened the tie, and explained the difference between lend and give",
        "moral": "A careful explanation can mend a mistake before it grows",
        "ending": "the starry tie hung beside the moon lamp while every block slept in its box",
    },
    {
        "tie": "a green striped tie with a button at its tail",
        "claim": "Pip thought Luna had told him to tug the tie as hard as he could",
        "truth": "Luna had only asked him to hold it while she tied a bow",
        "tangle": "the hard tug knocked a tower of wooden cups into a noisy heap",
        "fix": "Luna helped rebuild the tower and showed Pip how gentle hands keep small things safe",
        "moral": "Listening is a kind of helping, especially when hands are busy",
        "ending": "the green tie made a neat bow while the wooden cups stood tall again",
    },
]

OPENINGS = [
    "In the nursery, where the moon-clock ticked and the soft toys rhymed,",
    "By the toy chest, beneath a blanket of stars,",
    "When the sleepy lamps began to glow,",
    "At the nursery door, where tiny shoes marched in a row,",
]

RHYME_DETAILS = [
    "the drum went dum-dum",
    "the little chairs squeaked twice",
    "the lamb toy nodded bright",
    "the clock chimed three",
    "the blocks made a clacking sea",
]


def tell_story(params: StoryParams) -> World:
    if params.hero == params.friend:
        raise StoryError("The hero and friend must have different names.")
    if not params.place:
        raise StoryError("A nursery place is required.")

    world = World(Place())
    hero = world.add(Entity(params.hero, "character", "girl", params.hero))
    friend = world.add(Entity(params.friend, "character", "boy", params.friend))
    keeper = world.add(Entity(params.keeper, "character", "woman", params.keeper))

    hero.memes["honesty"] = 1.0
    friend.memes["eagerness"] = 1.0
    keeper.memes["patience"] = 1.0
    hero.meters["care"] = 1.0
    friend.meters["care"] = 0.0

    seed = params.seed or 0
    arc = ARCS[seed % len(ARCS)]
    opening = OPENINGS[(seed // len(ARCS)) % len(OPENINGS)]
    detail = RHYME_DETAILS[(seed // 3) % len(RHYME_DETAILS)]

    world.facts.update(
        hero=hero,
        friend=friend,
        keeper=keeper,
        tie=arc["tie"],
        claim=arc["claim"],
        truth=arc["truth"],
        tangle=arc["tangle"],
        fix=arc["fix"],
        moral=arc["moral"],
        ending=arc["ending"],
        misunderstanding=True,
        bad_ending_avoided=True,
        moral_value="honest and careful sharing",
    )

    world.say(
        f"{opening} {hero.label} found {arc['tie']} beside the toy chest, "
        f"and {detail}. {keeper.label} smiled while {friend.label} practiced a puppet dance."
    )
    world.say(
        f"{hero.label} said, \"{friend.label}, you may wear the tie for the parade, then it comes back to its hook.\" "
        f"{friend.label} heard only the first part and thought, \"The tie is mine to keep.\""
    )
    world.facts["misunderstanding"] = True
    world.para()

    world.say(
        f"So {friend.label} skipped away with the tie, while {hero.label} called, "
        f"\"Wait, Pip, I meant for today!\" The words sounded small beneath the nursery rhyme, "
        f"and no one noticed the mistake until {arc['tangle']}."
    )
    world.facts["danger"] = True
    friend.meters["care"] = -1.0
    hero.memes["worry"] = 1.0

    world.say(
        f"For a moment, the day might have ended badly: toys could break, tempers could flare, "
        f"and the bright parade could turn into a sorry affair."
    )
    world.facts["bad_ending"] = True
    world.para()

    world.say(
        f"But {keeper.label} tapped the clock and said, \"Ask, do not guess. What did each of you mean?\" "
        f"{hero.label} replied, \"{arc['truth'].capitalize()}.\" "
        f"{friend.label} blinked and said, \"I thought you gave it to me.\""
    )
    world.say(
        f"{hero.label} nodded. \"I should have said it twice.\" Together, they {arc['fix']}."
    )
    world.facts["truth_told"] = True
    world.facts["tie_safe"] = True
    world.facts["bad_ending"] = False
    world.facts["misunderstanding"] = False
    friend.meters["care"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0
    world.para()

    world.say(
        f"Then {keeper.label} taught the nursery rhyme: \"Say what you mean, and share with care; "
        f"clear little words make kindness fair.\" {arc['moral']}."
    )
    world.say(
        f"At bedtime, {arc['ending']}. {hero.label} and {friend.label} bowed together, "
        f"and the moon-clock chimed, \"Home, home, home.\""
    )
    return world


NAMES = ["Luna", "Nora", "Mira", "Tilly", "Pip", "Ben", "Ollie", "Sam"]
FRIENDS = ["Pip", "Ben", "Ollie", "Tom", "Finn"]
KEEPERS = ["Mabel", "Nell", "Ada", "Rose", "Mina"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle nursery-rhyme story about a tie, a misunderstanding, and a repaired friendship.",
        f"Tell a rhyming nursery story in which {f['hero'].label} explains clearly what the tie may be used for.",
        f"Write a child-facing story where a bad ending is avoided because someone asks what was really meant.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    keeper: Entity = f["keeper"]
    return [
        QAItem(
            question=f"What was special about the tie in {hero.label}'s nursery story?",
            answer=f"It was {f['tie']}. {hero.label} let {friend.label} wear it for the parade, but it was meant to return to its hook.",
        ),
        QAItem(
            question=f"What did {friend.label} misunderstand?",
            answer=f"{friend.label} thought {hero.label} had given him the tie to keep, but {hero.label} had only lent it for the day.",
        ),
        QAItem(
            question="What bad ending almost happened?",
            answer="The tie caused a tangle that could have broken toys, upset the friends, and spoiled the parade.",
        ),
        QAItem(
            question=f"How did {hero.label} and {friend.label} fix the trouble?",
            answer=f"They listened to each other, clarified the promise, and {f['fix']}.",
        ),
        QAItem(
            question=f"What moral value did {keeper.label}'s rhyme teach?",
            answer=f"It taught that {f['moral'].lower()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tie?",
            answer="A tie is a strip of cloth used as clothing or to fasten something together.",
        ),
        QAItem(
            question="Why is it helpful to ask when someone is confused?",
            answer="Asking helps people learn what was really meant instead of making the misunderstanding larger.",
        ),
        QAItem(
            question="What does it mean to borrow something?",
            answer="To borrow something means to use it for a while and return it to its owner.",
        ),
    ]


ASP_RULES = r"""
tied_item(tie).
misunderstanding :- tie_worn, not promise_clear.
promise_clear :- words_repeated.
danger :- tie_worn, misunderstanding.
bad_ending :- danger, not truth_told.
safe_ending :- truth_told, tie_returned.
moral_value(careful_sharing) :- promise_clear, tie_returned.
#show misunderstanding/0.
#show bad_ending/0.
#show safe_ending/0.
#show moral_value/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("tied_item", "tie"),
            asp.fact("tie_worn"),
            asp.fact("words_repeated"),
            asp.fact("truth_told"),
            asp.fact("tie_returned"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> dict[str, list[tuple]]:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/0.\n#show bad_ending/0.\n#show safe_ending/0.\n#show moral_value/1."))
    return {
        "misunderstanding": asp.atoms(model, "misunderstanding"),
        "bad_ending": asp.atoms(model, "bad_ending"),
        "safe_ending": asp.atoms(model, "safe_ending"),
        "moral_value": asp.atoms(model, "moral_value"),
    }


def asp_verify() -> int:
    outcome = asp_outcome()
    if outcome["misunderstanding"] == [] and outcome["bad_ending"] == [] and outcome["safe_ending"] == [()] and outcome["moral_value"] == [("careful_sharing",)]:
        sample = generate(StoryParams(seed=17))
        if "misunderstanding" in sample.story.lower() and "tie" in sample.story.lower():
            print("OK: ASP and Python agree, and generated prose was exercised.")
            return 0
    print(f"MISMATCH: {outcome}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nursery-rhyme tie storyworld.")
    parser.add_argument("--place", choices=["nursery"])
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--keeper", choices=KEEPERS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Nora", "Mira", "Tilly"])
    friend_choices = [name for name in FRIENDS if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    keeper_choices = [name for name in KEEPERS if name not in {hero, friend}]
    keeper = args.keeper or rng.choice(keeper_choices)
    return StoryParams(
        place=args.place or "nursery",
        hero=hero,
        friend=friend,
        keeper=keeper,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


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
        print(asp_program("#show misunderstanding/0.\n#show bad_ending/0.\n#show safe_ending/0.\n#show moral_value/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(json.dumps(asp_outcome(), indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(
                StoryParams(
                    place="nursery",
                    hero="Luna",
                    friend="Pip",
                    keeper="Mabel",
                    seed=base_seed + index,
                )
            )
            for index in range(len(ARCS))
        ]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
