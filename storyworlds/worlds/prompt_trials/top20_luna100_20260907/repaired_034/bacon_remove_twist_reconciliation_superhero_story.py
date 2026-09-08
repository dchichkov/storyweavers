#!/usr/bin/env python3
"""
A small superhero storyworld about bacon, a hidden twist, and reconciliation.
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
class StoryParams:
    hero: str = "Nova"
    companion: str = "Milo"
    city: str = "Bright City"
    arc: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    companion: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HERO_NAMES = ["Nova", "Captain Comet", "Zara", "Bolt", "Sky"]
COMPANION_NAMES = ["Milo", "Pip", "Ember", "Rae", "Sunny"]
CITIES = ["Bright City", "Maple Metro", "Sunrise Town"]

ARCS = [
    {
        "premise": "The morning bacon festival filled the city square with a delicious smell",
        "problem": "the giant silver pan began sliding toward the fountain",
        "stake": "The hot bacon could spill and frighten the families gathered nearby",
        "temptation": "blast the pan away alone and look like the strongest hero",
        "clue": "the pan slowed whenever the cooks pulled together on its blue safety rope",
        "action": "Nova and Milo asked the cooks to hold the rope while the heroes raised a soft rescue net",
        "twist": "the pan was not being pushed by a villain; a tiny parade robot had tangled its wheels in the rope",
        "reconciliation": "They removed the robot's wheels from the knot, apologized for blaming it, and invited its maker to the festival",
        "lesson": "a hero should investigate before choosing someone to blame",
        "ending": "the robot beeped a happy rhythm while everyone shared crisp bacon beneath the bunting",
        "question": "Why did the heroes need to stop the giant pan?",
        "answer": "They needed to stop it so the hot bacon would not spill near the families in the square.",
    },
    {
        "premise": "A bacon-shaped rescue drone delivered breakfast to firefighters after a long night",
        "problem": "its bacon-shaped signal vanished above the clock tower",
        "stake": "The firefighters might miss the meal and lose a chance to rest together",
        "temptation": "remove the signal by force and claim the rescue alone",
        "clue": "the signal returned whenever someone rang the old tower bell",
        "action": "The heroes climbed carefully, rang the bell, and asked the firefighters to guide the drone from below",
        "twist": "a lonely pigeon had built its nest over the signal lamp",
        "reconciliation": "They moved the lamp gently, made a warm perch for the pigeon, and thanked it for revealing the problem",
        "lesson": "careful help can protect both people and small creatures",
        "ending": "the drone circled the tower as firefighters passed bacon sandwiches from hand to hand",
        "question": "What made the rescue signal disappear?",
        "answer": "A pigeon had built its nest over the drone's signal lamp.",
    },
    {
        "premise": "The city's children prepared a superhero breakfast for a new student",
        "problem": "someone removed the last bacon star from the serving tray",
        "stake": "The new student might think nobody wanted to welcome them",
        "temptation": "point at the nearest suspect and demand the star back",
        "clue": "a trail of crumbs led beneath the welcome table",
        "action": "Nova and Milo followed the crumbs and asked everyone what they had seen",
        "twist": "the missing star had been carried away by a hungry little dog",
        "reconciliation": "They gave the dog a safe treat, made a fresh bacon star, and invited the dog's owner to join the welcome",
        "lesson": "asking gentle questions can repair a problem better than accusing",
        "ending": "the new student smiled as the whole table made room for one more plate",
        "question": "How did the heroes find the missing bacon star?",
        "answer": "They followed a trail of crumbs beneath the welcome table and discovered that a hungry dog had carried it away.",
    },
    {
        "premise": "A bright comet streaked over the city during the annual hero parade",
        "problem": "its glowing tail wrapped around the parade's bacon banner",
        "stake": "The banner could tear while marching children held its ends",
        "temptation": "remove the tail with a flashy power burst before asking anyone for help",
        "clue": "the tail loosened whenever the marching band played softly",
        "action": "The heroes asked the band to play a gentle tune while the children lowered the banner together",
        "twist": "the comet was a lost sky kite carrying a message from a worried child",
        "reconciliation": "They returned the kite, listened to the child's apology, and helped repair the bacon banner",
        "lesson": "listening can turn a frightening surprise into a chance to help",
        "ending": "the repaired banner waved beside the kite as the parade rolled toward its bacon feast",
        "question": "What was the glowing comet really carrying?",
        "answer": "It was a lost sky kite carrying a message from a worried child.",
    },
    {
        "premise": "The mayor invited every hero to a rooftop bacon breakfast",
        "problem": "a gust removed the tablecloth and sent plates skating toward the edge",
        "stake": "The breakfast could fall into the busy street below",
        "temptation": "fly after the plates alone and prove that no one else was needed",
        "clue": "the plates stopped when the gardeners placed flower boxes in a line",
        "action": "The heroes and gardeners made a safe row of boxes and passed each plate back to the table",
        "twist": "the gust came from a friendly fan built by a shy young inventor",
        "reconciliation": "They removed the fan's loose cover, praised the inventor's clever idea, and invited them to test it safely",
        "lesson": "a mistake does not erase the good intention behind it",
        "ending": "the inventor's fan cooled the breakfast while everyone dipped bacon into sunny eggs",
        "question": "How did the heroes keep the plates from falling?",
        "answer": "They made a safe row of flower boxes and passed the plates back to the table.",
    },
]

OPENINGS = [
    "At sunrise, bright windows glittered across",
    "When the first bells rang over",
    "Under a sky as blue as a hero's cape,",
    "By breakfast time,",
    "The rooftops of",
]

DIALOGUE = [
    ("Milo shouted, 'Nova, wait! We do not know the whole story yet.'",
     "Nova answered, 'You are right. We will remove the danger without removing kindness.'"),
    ("'Should we rush in?' Milo asked.",
     "'We should ask first and act together,' Nova replied."),
    ("Milo pointed toward the trouble. 'That looks scary.'",
     "Nova took a breath. 'Then we will be brave enough to listen.'"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about bacon, a twist, and reconciliation."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--companion", choices=COMPANION_NAMES)
    parser.add_argument("--city", choices=CITIES)
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
    hero = args.hero or rng.choice(HERO_NAMES)
    choices = [name for name in COMPANION_NAMES if name != hero]
    companion = args.companion or rng.choice(choices)
    if hero == companion:
        raise StoryError("The hero and companion must be different.")
    return StoryParams(
        hero=hero,
        companion=companion,
        city=args.city or rng.choice(CITIES),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "hero"),
        companion=Entity(params.companion, "companion"),
    )


def simulate(world: World) -> None:
    p = world.params
    arc = ARCS[p.arc]
    rng = random.Random(p.seed)
    hero = world.hero
    companion = world.companion

    hero.memes["courage"] = 1.0
    hero.memes["haste"] = 1.0
    companion.memes["care"] = 1.0
    world.facts.update(
        problem=arc["problem"],
        stake=arc["stake"],
        clue=arc["clue"],
        twist=arc["twist"],
        reconciliation=arc["reconciliation"],
        resolved=False,
    )

    opening = rng.choice(OPENINGS)
    world.say(f"{opening} {p.city} glowed with superhero colors.")
    world.say(f"{arc['premise']}. {hero.name} and {companion.name} watched from a rooftop, ready to help.")
    world.para()

    world.say(f"Suddenly, {arc['problem']}. {arc['stake']}.")
    world.say(f"For one quick moment, {hero.name} wanted to {arc['temptation']}.")
    first, second = rng.choice(DIALOGUE)
    world.say(f"{first} {second}")
    hero.memes["hesitation"] = 1.0
    world.facts["temptation"] = arc["temptation"]
    world.para()

    world.say(f"Instead of guessing, they searched for a clue: {arc['clue']}.")
    world.say(f"{arc['action']}.")
    world.say(f"Then came the twist: {arc['twist']}.")
    world.say(f"For reconciliation, {arc['reconciliation']}.")
    hero.memes["understanding"] = 1.0
    companion.memes["reconciliation"] = 1.0
    world.facts["resolved"] = True
    world.para()

    world.say(f"{hero.name} learned that {arc['lesson']}.")
    world.say(f"At last, {arc['ending']}.")
    world.facts["ending"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]

    prompts = [
        f"Write a superhero story in {params.city} involving bacon and a careful choice to remove danger.",
        f"Tell a child-friendly tale about {params.hero} and {params.companion} discovering a twist and making reconciliation.",
        f"Create a bright superhero adventure where listening changes how a problem is solved: {arc['problem']}.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.companion} face?",
            answer=f"They faced this problem: {arc['problem']}.",
        ),
        QAItem(
            question=f"What risky action did {params.hero} first consider?",
            answer=f"{params.hero} first considered trying to {arc['temptation']}.",
        ),
        QAItem(
            question="What clue helped the heroes?",
            answer=f"The clue was that {arc['clue']}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {arc['twist']}.",
        ),
        QAItem(
            question="How did reconciliation help?",
            answer=f"Reconciliation happened when they {arc['reconciliation'].lower()}",
        ),
        QAItem(
            question="What did the hero learn?",
            answer=f"The hero learned that {arc['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special abilities, courage, or kindness to help others.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising discovery that changes what the characters thought was happening.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, apologizing, and repairing trust.",
        ),
        QAItem(
            question="Why can someone remove an object carefully?",
            answer="Someone can remove an object carefully to take away danger without hurting people, animals, or nearby things.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (world.hero, world.companion):
        lines.append(
            f"  {entity.name:16} ({entity.kind:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
#show resolved/1.
valid(story) :- domain(superhero), feature(bacon), feature(remove),
                 feature(twist), feature(reconciliation), resolved(story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("domain", "superhero"),
            asp.fact("feature", "bacon"),
            asp.fact("feature", "remove"),
            asp.fact("feature", "twist"),
            asp.fact("feature", "reconciliation"),
            asp.fact("resolved", "story"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/1.\n#show resolved/1."))
    valid = asp.atoms(model, "valid")
    resolved = asp.atoms(model, "resolved")
    if valid == [("story",)] and resolved == [("story",)]:
        print("OK: ASP twin is consistent.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


CURATED = [
    StoryParams(hero="Nova", companion="Milo", city="Bright City", arc=0, seed=101),
    StoryParams(hero="Zara", companion="Ember", city="Maple Metro", arc=2, seed=202),
    StoryParams(hero="Bolt", companion="Rae", city="Sunrise Town", arc=4, seed=303),
]


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
        print(asp_program("#show valid/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid/1.\n#show resolved/1."))
        print(asp.atoms(model, "valid"))
        print(asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
