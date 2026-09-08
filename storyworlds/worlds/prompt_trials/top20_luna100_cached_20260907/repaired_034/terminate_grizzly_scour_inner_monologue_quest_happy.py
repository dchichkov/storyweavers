#!/usr/bin/env python3
"""
A tiny superhero storyworld about Luna's quest to stop a grizzly-shaped storm
machine before it can terminate the town's lantern festival.
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
    helper: str = "Pip"
    place: str = "Glowbridge"
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
    helper: Entity
    grizzly: Entity
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


HEROES = ["Luna", "Nova", "Mira", "Zara", "Sol"]
HELPERS = ["Pip", "Theo", "Ivy", "Beau", "Kito"]
PLACES = ["Glowbridge", "Starbell Square", "Moonbeam Harbor"]

QUESTS = [
    {
        "premise": "The town's lantern festival was about to begin",
        "problem": "a giant grizzly-shaped cloud machine rolled from the hills and began sucking the lantern light into its iron belly",
        "stake": "If the machine filled completely, it would terminate the festival and leave every street dark",
        "clue": "the machine's growl softened whenever someone sang beside a lantern",
        "action": "Luna and Pip carried bright lanterns in a circle and sang the old welcome song",
        "twist": "the grizzly machine was not trying to frighten anyone; it was a lonely weather robot searching for its lost cub-shaped beacon",
        "resolution": "Luna placed the beacon on its head, and the machine released the stolen light in a warm golden shower",
        "ending": "the robot bowed like a friendly bear while hundreds of lanterns bloomed above the happy crowd",
        "lesson": "bravery means looking closely before treating a strange thing like an enemy",
    },
    {
        "premise": "A silver alarm rang beneath the old mountain",
        "problem": "a grizzly guardian had awakened and started to scour the tunnels for the town's missing sunstone",
        "stake": "The guardian's stomps could shake the bridge apart before the sunstone was found",
        "clue": "small golden pawprints led away from the loudest tunnel and toward a nest of blue flowers",
        "action": "Luna used her moon-shield to light the pawprints while Pip listened for the gentlest rumble",
        "twist": "the grizzly was protecting a sleepy cub trapped behind a fallen gate",
        "resolution": "They lifted the gate together, and the cub's glow showed the safe path to the sunstone",
        "ending": "the grizzly curled beside the cub as the restored sunstone painted the mountain pink",
        "lesson": "a careful hero can turn a frightening search into a rescue",
    },
    {
        "premise": "The mayor asked Luna to recover the Sky Key before the comet parade",
        "problem": "a runaway grizzly-shaped balloon had carried the key over the rooftops",
        "stake": "Without the key, the parade rockets could not return safely to their launch tower",
        "clue": "the balloon dipped whenever it passed the bakery's warm chimney",
        "action": "Luna and Pip stretched a quilt between two balconies and guided the balloon toward the soft landing place",
        "twist": "the balloon's grizzly face was painted by a child who had hidden inside its basket",
        "resolution": "Luna opened the basket, rescued the child, and returned the Sky Key to the parade captain",
        "ending": "the child rode beside Luna in the first parade rocket, waving at the cheering town",
        "lesson": "a quest is happiest when the rescue includes the person who caused the trouble",
    },
    {
        "premise": "A storm covered the seaside city in purple fog",
        "problem": "a real grizzly had wandered onto the pier while trying to scour the fog for the smell of pine trees",
        "stake": "The frightened bear might knock over the rescue boats or fall into the choppy water",
        "clue": "the bear calmed whenever Luna tapped a slow rhythm on a hollow buoy",
        "action": "Luna and Pip made a path of bell sounds from the pier toward the quiet forest road",
        "twist": "the bear had followed a scent from a pinecone charm dropped by a lost ranger",
        "resolution": "They found the ranger, returned the charm, and guided bear and ranger safely home",
        "ending": "the ranger waved from the forest edge while the grizzly nibbled berries under the moon",
        "lesson": "gentle guidance can be stronger than a loud command",
    },
]

MONOLOGUES = [
    "Luna tightened her silver cape and thought, 'A true hero does not rush at a mystery. A true hero listens.'",
    "Inside Luna's brave heart, a small question glimmered: 'What is this creature really asking for?'",
    "Luna wanted to fly forward, but her inner voice whispered, 'Look first. Someone may need help, not harm.'",
    "For one breath, Luna felt afraid. Then she told herself, 'Courage is fear that chooses a kind next step.'",
]

DIALOGUE = [
    ("Pip called, 'Luna, should we chase it away?'", "'Not yet,' Luna answered. 'Tell me what you notice.'"),
    ("Pip asked, 'What if the grizzly is dangerous?'", "'Then we will stay careful,' Luna said, 'but we will still learn the truth.'"),
    ("Pip pointed and said, 'The clues are leading somewhere!'", "'Good eyes,' Luna replied. 'We can solve this quest together.'"),
    ("Pip whispered, 'I hear a small sound behind the roar.'", "'Then we must follow the small sound,' Luna said."),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld about Luna, a grizzly mystery, and a happy quest.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", type=int, choices=range(len(QUESTS)))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([x for x in HELPERS if x != hero])
    place = args.place or rng.choice(PLACES)
    quest = args.quest if args.quest is not None else rng.randrange(len(QUESTS))
    if hero == helper:
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(hero=hero, helper=helper, place=place, quest=quest)


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "hero"),
        helper=Entity(params.helper, "helper"),
        grizzly=Entity("the grizzly", "grizzly"),
    )


def simulate(world: World) -> None:
    p = world.params
    q = QUESTS[p.quest]
    rng = random.Random(p.seed)
    h, f, g = world.hero, world.helper, world.grizzly

    h.memes["courage"] = 1.0
    h.memes["curiosity"] = 1.0
    f.memes["alertness"] = 1.0
    g.meters["distance"] = 1.0
    world.facts.update(place=p.place, problem=q["problem"], clue=q["clue"], quest=p.quest)

    openings = [
        f"At {p.place}, dawn painted the rooftops gold",
        f"Above {p.place}, clouds curled like capes",
        f"The bells of {p.place} rang bright under a blue sky",
        f"Moonlight still shone over {p.place} when the trouble began",
    ]
    world.say(f"{rng.choice(openings)}. {p.hero}, the town's moon-caped superhero, watched from a clock tower.")
    world.say(f"{q['premise']}. Then {q['problem']}.")
    world.para()

    world.say(f"The danger was clear: {q['stake']}.")
    world.say(rng.choice(MONOLOGUES).replace("Luna", p.hero))
    first, second = rng.choice(DIALOGUE)
    world.say(first.replace("Pip", p.helper).replace("Luna", p.hero) + " " + second.replace("Luna", p.hero))
    world.facts["inner_monologue"] = True
    world.facts["dialogue"] = True
    h.memes["patience"] = 1.0

    world.para()
    world.say(f"Instead of striking, {p.hero} and {p.helper} searched together. They discovered that {q['clue']}.")
    world.say(f"{q['action']}.")
    world.facts["method"] = q["action"]
    world.say(f"Then came the surprise: {q['twist']}.")
    world.facts["twist"] = q["twist"]
    g.memes["trust"] = 1.0
    h.memes["understanding"] = 1.0

    world.para()
    world.say(f"{q['resolution']}. The danger ended without anyone being hurt.")
    world.say(f"Everyone in {p.place} cheered for {p.hero} and {p.helper}.")
    world.say(f"As a happy ending, {q['ending']}.")
    world.facts["resolved"] = True
    world.facts["happy_ending"] = True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    q = QUESTS[params.quest]
    prompts = [
        f"Write a child-friendly superhero story about {params.hero} on a quest in {params.place}.",
        f"Include an inner monologue, a grizzly mystery, and a happy ending where {params.hero} helps instead of rushing.",
        f"Use the problem '{q['problem']}' and show how teamwork solves it.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} face?",
            answer=f"{params.hero} faced this problem: {q['problem']}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} understand the grizzly situation?",
            answer=f"The clue was that {q['clue']}.",
        ),
        QAItem(
            question=f"What surprising truth did {params.hero} discover?",
            answer=f"{params.hero} discovered that {q['twist']}.",
        ),
        QAItem(
            question=f"How did {params.hero} and {params.helper} solve the quest?",
            answer=f"They solved the quest when {q['action']}, and then {q['resolution']}.",
        ),
        QAItem(
            question=f"How did the story end for {params.hero}?",
            answer=f"It ended happily: {q['ending']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special abilities and good choices to help others.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a character has inside their mind.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is an important journey or mission with a goal to complete.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to bring something to an end.",
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
    for ent in [world.hero, world.helper, world.grizzly]:
        lines.append(f"  {ent.name:12} ({ent.kind:9}) meters={ent.meters} memes={ent.memes}")
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
valid(story) :- domain(superhero), feature(inner_monologue),
                 feature(quest), feature(happy_ending),
                 seed(terminate), seed(grizzly), seed(scour).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    facts = [
        asp.fact("domain", "superhero"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "quest"),
        asp.fact("feature", "happy_ending"),
        asp.fact("seed", "terminate"),
        asp.fact("seed", "grizzly"),
        asp.fact("seed", "scour"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    if asp.atoms(model, "valid") != [("story",)]:
        print("MISMATCH: ASP twin failed.")
        return 1
    for quest in range(len(QUESTS)):
        sample = generate(StoryParams(quest=quest, seed=quest + 10))
        if not sample.story or not sample.world.facts.get("happy_ending"):
            print("MISMATCH: generated story failed.")
            return 1
    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(hero="Luna", helper="Pip", place="Glowbridge", quest=0, seed=101),
    StoryParams(hero="Nova", helper="Ivy", place="Starbell Square", quest=1, seed=202),
    StoryParams(hero="Mira", helper="Theo", place="Moonbeam Harbor", quest=2, seed=303),
    StoryParams(hero="Zara", helper="Beau", place="Glowbridge", quest=3, seed=404),
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print(asp.atoms(asp.one_model(asp_program()), "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
