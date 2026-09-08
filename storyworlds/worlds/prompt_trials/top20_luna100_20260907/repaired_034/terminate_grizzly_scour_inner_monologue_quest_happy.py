#!/usr/bin/env python3
"""
A small superhero storyworld about Luna's quest to stop a grizzly-shaped storm.

The story uses terminate, grizzly, and scour as story-facing vocabulary while
modeling a brave choice, an inner monologue, a quest, and a happy ending.
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
    hero: str = "Luna"
    companion: str = "Pip"
    place: str = "Starfall City"
    quest: int = 0
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
    city: Entity
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HEROES = ["Luna", "Nova", "Mira", "Zara", "Sol"]
COMPANIONS = ["Pip", "Toby", "Wren", "Kiko", "Bee"]
PLACES = ["Starfall City", "Moonbeam Harbor", "Brightwood Town"]

QUESTS = [
    {
        "problem": "a huge grizzly-shaped cloud began to scour the rooftops with icy rain",
        "stake": "the children at the hilltop school could not get safely home",
        "shortcut": "fly straight into the cloud and terminate it with one bright burst",
        "clue": "the cloud rumbled whenever the old weather bell rang",
        "action": "They climbed the bell tower, tied a silver ribbon to the bell rope, and rang a gentle pattern",
        "twist": "the grizzly cloud was not a monster; it was a lonely storm carrying a lost mountain echo",
        "solution": "The echo followed the bell's friendly rhythm away from the school and into the empty valley",
        "sharing": "Luna invited the children to make a welcome song for the storm instead of chasing it away",
        "ending": "the cloud softened into a pink bear shape and sprinkled the school garden with warm rain",
        "lesson": "a hero can end danger without ending kindness",
        "question": "Why did Luna climb the bell tower?",
        "answer": "Luna climbed the bell tower to use the weather bell's rhythm to guide the dangerous cloud away from the school.",
    },
    {
        "problem": "a runaway grizzly-shaped wind began to scour the market square",
        "stake": "fruit baskets and bright awnings were flying toward the river",
        "shortcut": "terminate the wind by blasting it with her strongest sky beam",
        "clue": "the wind slowed whenever cloth streamers spun together",
        "action": "They linked the market's streamers into a long, colorful spiral",
        "twist": "the wind was dancing around a tiny seed pod that had lost its tree",
        "solution": "They guided the seed pod to a quiet garden, and the wild wind settled beside it",
        "sharing": "Every shopkeeper gave one ribbon to the spiral and one smile to the grateful wind",
        "ending": "a new sapling waved above the square while the rescued awnings fluttered like flags",
        "lesson": "careful listening can turn a fight into a rescue",
        "question": "What made the runaway wind slow down?",
        "answer": "The wind slowed when the streamers were linked and spun together.",
    },
    {
        "problem": "a grizzly-shaped shadow began to scour the library windows at midnight",
        "stake": "the town's story lamps would go dark before the morning parade",
        "shortcut": "terminate the shadow by chasing it with a blazing shield",
        "clue": "the shadow became smaller beside pages covered with moon drawings",
        "action": "They opened the library's picture books and placed silver lamps along the steps",
        "twist": "the shadow belonged to a lost night moth searching for its bright garden",
        "solution": "The moth followed the moon drawings to the rooftop garden and left the windows clear",
        "sharing": "Luna let every reader add a moon to the path",
        "ending": "the library windows shone with a trail of moons, and the moth rested among the flowers",
        "lesson": "the right light helps more when it makes room for another traveler",
        "question": "What was the grizzly-shaped shadow really?",
        "answer": "The shadow was made by a lost night moth looking for its bright garden.",
    },
    {
        "problem": "a grizzly-shaped wave rose to scour the lighthouse steps",
        "stake": "the keeper's small boat could not return through the choppy water",
        "shortcut": "terminate the wave with a thunderclap from Luna's gloves",
        "clue": "the wave curled gently whenever the lighthouse blinked three times",
        "action": "They signaled in a steady pattern and laid floating lanterns across the safe channel",
        "twist": "the wave was guarding a family of seals from a sharp reef",
        "solution": "The lantern path showed the boat a wider channel and gave the seals room to swim",
        "sharing": "The lighthouse keeper shared warm blankets with Luna, Pip, and the tired seals' watchers",
        "ending": "the wave bowed beneath the lighthouse beam as the boat glided home",
        "lesson": "a powerful hero protects every small life in the way",
        "question": "Why did the wave rise near the lighthouse?",
        "answer": "The wave had risen to guard a family of seals from a sharp reef.",
    },
    {
        "problem": "a grizzly-shaped dust cloud began to scour the train station",
        "stake": "the last train could not see the signal lights",
        "shortcut": "terminate the dust cloud by spinning it into the sky",
        "clue": "the dust cleared whenever the station children hummed together",
        "action": "They formed a humming circle and held bright scarves beside the tracks",
        "twist": "the cloud was carrying seeds from a faraway desert garden",
        "solution": "The humming guided the cloud toward the station garden, where the seeds could settle",
        "sharing": "The children shared cups of water with the new sprouts",
        "ending": "green leaves rose beside the tracks as the last train chimed its happy arrival",
        "lesson": "a loud problem may carry a quiet gift",
        "question": "How did the station helpers clear the dust?",
        "answer": "They hummed together and held bright scarves beside the tracks, guiding the dust safely away.",
    },
]

OPENINGS = [
    "Above the rooftops, Luna's starry cape flashed in the morning sun",
    "At sunset, Luna patrolled the glowing streets of the city",
    "The city lights twinkled below Luna as she balanced on the clock tower",
    "A silver moon rose over the busy streets where Luna watched for trouble",
    "The sky turned violet just as Luna heard a strange rumble",
]

THOUGHTS = [
    "I could rush in and look powerful, but a real hero must first learn what needs help",
    "If I blast before I listen, I may make the trouble larger",
    "My cape can carry me quickly, but kindness must choose the direction",
    "I want to end this danger now, yet ending danger does not mean hurting everything nearby",
    "Courage is not only a bright beam; it is also the patience to notice a small clue",
]

DIALOGUES = [
    ("Pip called, 'Luna, wait! The sound is changing.'", "'You are right,' Luna answered. 'Tell me what you hear.'"),
    ("Pip pointed and said, 'That grizzly shape is guarding something.'", "'Then our quest is a rescue,' Luna replied, 'not a battle.'"),
    ("Luna asked, 'Pip, where is the safest path?'", "Pip answered, 'Follow the lights, and let the wind show us what it needs.'"),
    ("Pip cried, 'Your strongest power may not be the best one.'", "'Thank you,' Luna said. 'We will use our gentlest power first.'"),
]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about Luna, a grizzly-shaped danger, and a kind quest."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--quest", type=int, choices=range(len(QUESTS)))
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
    choices = [name for name in COMPANIONS if name != hero]
    companion = args.companion or rng.choice(choices)
    if hero == companion:
        raise StoryError("The hero and companion must be different characters.")
    place = args.place or rng.choice(PLACES)
    quest = args.quest if args.quest is not None else rng.randrange(len(QUESTS))
    return StoryParams(
        hero=hero,
        companion=companion,
        place=place,
        quest=quest,
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "superhero"),
        companion=Entity(params.companion, "helper"),
        city=Entity(params.place, "city"),
    )


def simulate(world: World) -> None:
    p = world.params
    quest = QUESTS[p.quest]
    rng = random.Random(p.seed)

    world.hero.meters["energy"] = 1.0
    world.hero.memes["courage"] = 1.0
    world.hero.memes["impatience"] = 1.0
    world.companion.memes["observation"] = 1.0
    world.facts.update(
        {
            "danger": quest["problem"],
            "stake": quest["stake"],
            "clue": quest["clue"],
            "quest": "rescue",
            "feature_inner_monologue": True,
        }
    )

    opening = rng.choice(OPENINGS)
    world.say(f"{opening}. {p.hero} and {p.companion} watched over {p.place}.")
    world.say(f"Then {quest['problem']}. {quest['stake']}.")
    world.para()

    world.say(f"For one moment, {p.hero} wanted to {quest['shortcut']}.")
    world.say(f"Inside, {p.hero}'s inner monologue grew louder: '{rng.choice(THOUGHTS)}.'")
    first, second = rng.choice(DIALOGUES)
    world.say(f"{first} {second}")
    world.hero.memes["reflection"] = 1.0
    world.facts["temptation"] = quest["shortcut"]

    world.para()
    world.say(f"Together they noticed a clue: {quest['clue']}.")
    world.say(f"That changed the quest from a battle into a rescue. {quest['action']}.")
    world.say(f"Here was the surprising turn: {quest['twist']}.")
    world.say(f"{quest['solution']}.")
    world.companion.memes["helped"] = 1.0
    world.hero.memes["wisdom"] = 1.0
    world.facts["twist"] = quest["twist"]
    world.facts["solution"] = quest["solution"]

    world.para()
    world.say(f"{quest['sharing']}.")
    world.say(f"At last, {quest['ending']}.")
    world.say(
        f"{p.hero} smiled because the happy ending proved that {quest['lesson']}."
    )
    world.hero.memes["joy"] = 1.0
    world.facts["resolved"] = True
    world.facts["happy_ending"] = True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    quest = QUESTS[params.quest]
    prompts = [
        f"Write a child-friendly superhero story about {params.hero} on a rescue quest in {params.place}.",
        f"Include an inner monologue in which {params.hero} chooses listening over a flashy attack.",
        f"Create a happy ending involving this danger: {quest['problem']}.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.hero} first want to do?",
            answer=f"{params.hero} first wanted to {quest['shortcut']}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} and {params.companion}?",
            answer=f"The clue was that {quest['clue']}.",
        ),
        QAItem(
            question="What surprising truth did the heroes discover?",
            answer=f"They discovered that {quest['twist']}.",
        ),
        QAItem(
            question=f"How did {params.hero} complete the quest?",
            answer=f"{params.hero} completed the quest when {quest['solution']}.",
        ),
        QAItem(
            question="Why was the ending happy?",
            answer=f"The ending was happy because {quest['ending']}, and the danger ended without harming the creature or place involved.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special abilities and good judgment to help others.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's spoken or written thoughts that show what the character is considering.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or challenge undertaken to reach an important goal.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to bring something to an end.",
        ),
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear with strong muscles and a distinctive shoulder hump.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="Scour means to search carefully or to clean and wear something by rubbing or rushing over it.",
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
    for entity in [world.hero, world.companion, world.city]:
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.name:16} ({entity.kind:10}) meters={meters} memes={memes}"
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
#show feature/1.
#show resolved/1.

valid(story) :-
    domain(superhero),
    feature(inner_monologue),
    feature(quest),
    feature(happy_ending),
    uses_word(terminate),
    uses_word(grizzly),
    uses_word(scour),
    resolved(story).

resolved(story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("domain", "superhero"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "quest"),
        asp.fact("feature", "happy_ending"),
        asp.fact("uses_word", "terminate"),
        asp.fact("uses_word", "grizzly"),
        asp.fact("uses_word", "scour"),
        asp.fact("resolved", "story"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/1."))
    if asp.atoms(model, "valid") != [("story",)]:
        print("MISMATCH: ASP twin failed.")
        return 1

    for index, params in enumerate(CURATED):
        sample = generate(params)
        if not sample.story or not sample.world.facts.get("happy_ending"):
            print(f"MISMATCH: generated story {index + 1} is incomplete.")
            return 1
        required = ("terminate", "grizzly", "scour")
        if not all(word in sample.story.lower() for word in required):
            print(f"MISMATCH: generated story {index + 1} lacks a seed word.")
            return 1

    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(hero="Luna", companion="Pip", place="Starfall City", quest=0, seed=101),
    StoryParams(hero="Nova", companion="Wren", place="Moonbeam Harbor", quest=1, seed=202),
    StoryParams(hero="Mira", companion="Bee", place="Brightwood Town", quest=2, seed=303),
]


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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid/1."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(20, args.n * 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
