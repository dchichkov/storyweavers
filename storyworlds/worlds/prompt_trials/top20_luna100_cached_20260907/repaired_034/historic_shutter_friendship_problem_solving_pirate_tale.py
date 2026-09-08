#!/usr/bin/env python3
"""
A small pirate storyworld about a historic shutter, friendship, and problem solving.
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
    friend: str = "Pip"
    ship: str = "the Starry Gull"
    island: str = "Whispering Key"
    shutter: str = "the historic blue shutter"
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
    friend: Entity
    ship: Entity
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


HERO_NAMES = ["Luna", "Mara", "Tess", "Cora", "Nell", "Ruby"]
FRIEND_NAMES = ["Pip", "Finn", "Bram", "Jo", "Kit", "Nico"]
SHIPS = ["the Starry Gull", "the Copper Crab", "the Moonlit Minnow"]
ISLANDS = ["Whispering Key", "Lantern Isle", "Old Compass Cay"]

ARCS = [
    {
        "premise": "The pirates sailed to an old lighthouse whose historic shutter had guarded the island bell for many years",
        "problem": "a storm slammed the shutter shut just before the warning bell needed to ring",
        "stake": "boats in the fog might miss the safe channel home",
        "clue": "the shutter hinges squeaked in three different pitches when the wind pressed them",
        "action": "Luna and Pip tapped the matching rhythm while the crew loosened the hinge with warm oil and a spare spoon",
        "twist": "the shutter was not stuck on its own; a tiny crab had built a nest behind it",
        "resolution": "They moved the crab gently, opened the shutter, and rang the bell for every boat",
        "ending": "the lighthouse shone through the open shutter while the little crab waved one claw from a safe patch of sand",
        "lesson": "good friends solve trouble by listening carefully and protecting small neighbors",
        "question": "Why did the pirates need to open the shutter?",
        "answer": "They needed to open the shutter so the lighthouse bell could warn boats about the safe channel.",
    },
    {
        "premise": "The crew visited a historic harbor house where a painted shutter showed the way to a buried water spring",
        "problem": "the shutter had fallen crooked and hid the last part of the painted map",
        "stake": "the crew could run out of fresh water before reaching the next port",
        "clue": "the visible blue stripes lined up with marks on the old harbor stones",
        "action": "Luna held the shutter steady while Pip compared the stripes with the stones and the crew measured the angle with a rope",
        "twist": "the missing mark was not on the wall at all; it was painted on the shutter's back",
        "resolution": "They turned the shutter safely and followed the complete map to the spring",
        "ending": "the crew filled their barrels while the historic shutter rested bright against the harbor house",
        "lesson": "friends can find a hidden answer when they share different ways of looking",
        "question": "Where was the missing map mark?",
        "answer": "The missing map mark was painted on the back of the historic shutter.",
    },
    {
        "premise": "The pirates promised to repair a historic shutter before the island's friendship feast",
        "problem": "the shutter's wooden latch snapped and the strong sea wind kept banging it",
        "stake": "the feast tables and lanterns could be blown into the bay",
        "clue": "a smooth piece of driftwood fit the latch hole exactly",
        "action": "Pip held the wood in place while Luna carved a notch and the neighbors braided a rope strap",
        "twist": "the old shutter had a second hidden latch made for stormy nights",
        "resolution": "They used both latches and tied the shutter closed until the wind passed",
        "ending": "the feast lanterns glowed warmly behind the quiet shutter as friends shared mango cakes",
        "lesson": "a careful team notices that old things may still hold useful surprises",
        "question": "How did the friends keep the shutter from banging?",
        "answer": "They repaired the latch, found its hidden second latch, and tied the shutter closed with a rope strap.",
    },
    {
        "premise": "A historic shutter in the pirate museum held a brass key needed to open the town's story chest",
        "problem": "the key slipped into a crack behind the shutter",
        "stake": "the children would miss the evening tale about the island's first sailors",
        "clue": "the key made a faint jingle whenever Pip hummed an old sea tune",
        "action": "Luna hummed the tune while Pip tilted a cloth sail beneath the crack",
        "twist": "the key was attached to a tiny bell, so sound could guide it toward the cloth",
        "resolution": "The bell jingled down, the key landed on the sail, and the story chest opened",
        "ending": "children listened beneath the historic shutter while the brass key gleamed beside the story chest",
        "lesson": "patience and shared clues can turn a tiny sound into a helpful guide",
        "question": "What helped the friends locate the key?",
        "answer": "Pip's old sea tune made the key's tiny bell jingle, helping them guide it onto the cloth sail.",
    },
    {
        "premise": "The crew found a historic shutter painted with a moon and a silver fish",
        "problem": "the painting had faded, and nobody knew which way the island path went",
        "stake": "the pirates might wander into the thorny mangrove",
        "clue": "the moon pointed toward the evening moonrise, while the fish pointed toward wet footprints",
        "action": "Luna followed the moon and Pip followed the fish, then they compared their tracks at the fork",
        "twist": "both signs led to the same place: a bridge hidden behind the mangroves",
        "resolution": "They crossed the bridge together and marked the safe path with bright shells",
        "ending": "the historic shutter watched over a shell-marked trail where no friend had to wander alone",
        "lesson": "different clues can work together when friends compare them instead of arguing",
        "question": "Why did the pirates compare the moon and fish clues?",
        "answer": "They compared the clues to see whether the two signs pointed toward the same safe path.",
    },
]


OPENINGS = [
    "At sunrise, gulls cried above the salt-blue sea",
    "The tide rolled softly under a sky the color of peaches",
    "Golden light flashed on the ropes and brass bells",
    "A warm breeze filled the sails and teased every pirate hat",
    "The sea sparkled like a chest of tiny coins",
]

DIALOGUE = [
    ("Pip said, 'We can rush in, but we may break the old wood.'",
     "Luna answered, 'Then we will listen first and solve it together.'"),
    ("Luna asked, 'What does the shutter tell us?'",
     "Pip replied, 'It tells us to look closely before we choose.'"),
    ("Pip whispered, 'Friends should share the worry, too.'",
     "Luna said, 'And shared worry can become a shared plan.'"),
    ("Luna cried, 'Do not pull yet!'",
     "Pip nodded. 'You saw something small. I will hold the lantern.'"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale about a historic shutter and friendship.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--island", choices=ISLANDS)
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
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(
        hero=hero,
        friend=friend,
        ship=args.ship or rng.choice(SHIPS),
        island=args.island or rng.choice(ISLANDS),
        arc=rng.randrange(len(ARCS)),
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "pirate"),
        friend=Entity(params.friend, "friend"),
        ship=Entity(params.ship, "ship"),
    )


def simulate(world: World) -> None:
    p = world.params
    arc = ARCS[p.arc]
    rng = random.Random(p.seed)
    h = world.hero
    f = world.friend

    h.memes["curiosity"] = 1.0
    h.memes["courage"] = 1.0
    f.memes["friendship"] = 1.0
    world.facts.update({
        "island": p.island,
        "shutter": p.shutter,
        "problem": arc["problem"],
        "clue": arc["clue"],
        "resolved": False,
    })

    world.say(f"{rng.choice(OPENINGS)}. {h.name} and {f.name} sailed the {p.ship} toward {p.island}.")
    world.say(f"There they found {arc['premise']}. The weather was turning rough, but the two friends stayed close.")
    world.para()

    world.say(f"Then {arc['problem']}. {arc['stake']}.")
    world.say(f"{h.name} reached for the shutter, but {f.name} caught the pirate's sleeve.")
    first, second = rng.choice(DIALOGUE)
    world.say(first + " " + second)
    world.say(f"Together they noticed that {arc['clue']}.")
    world.facts["clue_seen"] = True
    h.memes["problem_solving"] = 1.0
    f.memes["problem_solving"] = 1.0
    world.para()

    world.say(f"They worked side by side. {arc['action']}.")
    world.say(f"Then came the surprising turn: {arc['twist']}.")
    world.facts["twist"] = arc["twist"]
    world.facts["solution"] = arc["resolution"]
    world.say(f"{arc['resolution']}.")
    world.facts["resolved"] = True
    h.memes["friendship"] = 1.0
    world.para()

    world.say(f"{arc['ending']}.")
    world.say(f"{h.name} smiled at {f.name}. They had learned that {arc['lesson']}.")
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a child-friendly pirate tale about {params.hero} and {params.friend} solving a problem with a historic shutter.",
        f"Tell a friendship story on {params.island} where careful clues lead to a surprising turn.",
        f"Make a pirate adventure about this problem: {arc['problem']}.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.friend} face?",
            answer=f"They faced this problem: {arc['problem']}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} and {params.friend}?",
            answer=f"The clue was that {arc['clue']}.",
        ),
        QAItem(
            question="What surprising turn did the friends discover?",
            answer=f"They discovered that {arc['twist']}.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They solved it when {arc['resolution']}.",
        ),
        QAItem(
            question=f"What did {params.hero} learn about friendship?",
            answer=f"{params.hero} learned that {arc['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a wooden or metal cover that can close over a window or opening.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important because it belongs to the past or helps people remember the past.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a difficulty, considering clues, and choosing a careful way to fix it.",
        ),
        QAItem(
            question="What makes a good friendship?",
            answer="A good friendship grows through trust, listening, help, and shared courage.",
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
    for ent in [world.hero, world.friend, world.ship]:
        lines.append(
            f"  {ent.name:16} ({ent.kind:8}) "
            f"meters={dict(ent.meters)} memes={dict(ent.memes)}"
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
#show friendship/1.
#show problem_solving/1.

valid(story) :- historic(shutter), friendship(hero,friend), problem_solving(problem).
friendship(hero,friend) :- friends(hero,friend).
problem_solving(problem) :- clue(problem), solution(problem).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("historic", "shutter"),
        asp.fact("friends", "hero", "friend"),
        asp.fact("clue", "problem"),
        asp.fact("solution", "problem"),
    ])


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    required = {
        ("valid", ("story",)),
        ("friendship", ("hero", "friend")),
        ("problem_solving", ("problem",)),
    }
    found = {(sym.name, tuple(
        a.number if a.type.name == "Number" else
        a.string if a.type.name == "String" else a.name
        for a in sym.arguments
    )) for sym in model}
    if required.issubset(found):
        for params in CURATED:
            sample = generate(params)
            if not sample.story or not sample.world.facts["resolved"]:
                print("MISMATCH: generated story failed verification.")
                return 1
        print("OK: ASP twin and generated stories are consistent.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


CURATED = [
    StoryParams(hero="Luna", friend="Pip", ship="the Starry Gull", island="Whispering Key", arc=0, seed=101),
    StoryParams(hero="Mara", friend="Finn", ship="the Copper Crab", island="Lantern Isle", arc=2, seed=202),
    StoryParams(hero="Tess", friend="Bram", ship="the Moonlit Minnow", island="Old Compass Cay", arc=4, seed=303),
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
        print(asp_program("#show valid/1."))
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
