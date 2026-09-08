#!/usr/bin/env python3
"""
A small heartwarming storyworld about Luna, a cray, a cheque, and sharing.

The world models a child, a helpful crayfish, a lost cheque, and a village
market. Sound effects and a brief flashback help the characters remember that
kindness is something to pass along.
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
    animal: str = "a cray"
    place: str = "the riverside market"
    prize: str = "a blue umbrella"
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
    creature: Entity
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


HERO_NAMES = ["Luna", "Mara", "Nell", "Toby", "Ivy", "Rafi"]
COMPANION_NAMES = ["Pip", "Jo", "Mina", "Sol", "Bea", "Oren"]
PLACES = [
    "the riverside market",
    "the little canal fair",
    "the sunny bridge market",
]
PRIZES = ["a blue umbrella", "a warm wool scarf", "a basket of honey cakes"]

ARCS = [
    {
        "premise": "Luna was carrying a cheque from the baker to buy a new roof for the community reading room",
        "problem": "a sudden splash sent the cheque skimming toward the reeds",
        "stake": "Without it, the children might have to read beneath a leaky ceiling",
        "clue": "a tiny claw tapped twice against a tin cup",
        "action": "Luna and Pip made a line of spoons and leaves so the cheque could float safely toward shore",
        "twist": "the helpful swimmer was a cray who had seen the cheque caught beneath a root",
        "sharing": "Luna shared the good news with the baker, and the baker shared the roof money with the reading room",
        "memory": "Luna remembered her grandmother saying that a gift becomes brighter when it reaches more than one pair of hands",
        "ending": "that evening, the new roof shone above the reading room while the cray clicked softly beneath the bridge",
        "question": "Why was Luna carrying the cheque?",
        "answer": "Luna was carrying the cheque to help pay for a new roof for the community reading room.",
    },
    {
        "premise": "Luna brought a cheque to the market to pay for soup ingredients for the neighborhood supper",
        "problem": "the wind lifted the cheque from her basket and dropped it beside the muddy bank",
        "stake": "The neighbors might have no warm supper after the cold rain",
        "clue": "small ripples appeared in a careful zigzag through the mud",
        "action": "Pip held an umbrella while Luna laid flat boards across the mud",
        "twist": "a cray had nudged the cheque onto a dry stone with its bright claws",
        "sharing": "The cooks bought vegetables and filled every bowl, including one small bowl near the water",
        "memory": "Luna recalled a rainy day when strangers had shared their soup with her family",
        "ending": "steam curled from the supper pots as the cray watched the neighbors pass bowls around",
        "question": "How did the neighbors receive help at the end?",
        "answer": "They received help through a shared supper in which every neighbor could enjoy a warm bowl.",
    },
    {
        "premise": "Luna had a cheque for seeds to turn an empty corner beside the river into a garden",
        "problem": "the cheque slipped between two loose planks of the old dock",
        "stake": "The garden plan could be delayed until the next season",
        "clue": "a soft click-click came from under the boards",
        "action": "Luna tied a ribbon to a twig and gently guided it beneath the dock",
        "twist": "the cray had pushed the cheque away from a deep crack before the current could take it",
        "sharing": "The children planted the seeds together and promised to share the first vegetables",
        "memory": "Luna remembered planting one bean with her father and watching it become a row of green vines",
        "ending": "little leaves rose by the river while the cray rested under a garden stone",
        "question": "What was the cheque meant to buy?",
        "answer": "The cheque was meant to buy seeds for a shared riverside garden.",
    },
    {
        "premise": "Luna was bringing a cheque to repair the music cart that visited the village",
        "problem": "the paper slid from her pocket during a noisy market dance",
        "stake": "The cart might stay silent when the children gathered for music",
        "clue": "a sharp clink sounded beneath an overturned bucket",
        "action": "Luna and Pip paused the dance and listened for the sound",
        "twist": "a cray had trapped the cheque between the bucket and a smooth shell",
        "sharing": "The repaired cart played a tune, and every child added a sound to the song",
        "memory": "Luna remembered her first dance, when a patient drummer had invited her into the circle",
        "ending": "clap-clap, tap-tap, the whole market danced while the cray waved one little claw",
        "question": "Why did Luna and Pip stop the dance?",
        "answer": "They stopped the dance so they could listen for the clinking sound that revealed where the cheque was.",
    },
]

OPENINGS = [
    "Morning bells chimed over the water",
    "Sunlight warmed the market tents",
    "The river carried a silver ribbon of light",
    "A gentle breeze stirred the flags",
    "The village woke to bright bird calls",
]

SOUND_EFFECTS = [
    "Plip-plop went the river",
    "Clink-clink answered the tin cups",
    "Swish-swish whispered the reeds",
    "Tap-tap went the little boards",
    "Splash! went one runaway raindrop",
]

FLASHBACK_LEADS = [
    "For a moment, Luna remembered",
    "The sound carried Luna back to a day when",
    "Luna's heart made a quiet turn, and she recalled",
    "A warm memory floated up: Luna remembered",
]

DIALOGUE = [
    ("Pip asked, \"Should we chase it?\"", "\"Not wildly,\" Luna said. \"We can make a safe path together.\""),
    ("Pip called, \"I hear something under the boards!\"", "\"Then we should listen before we lift anything,\" Luna replied."),
    ("Pip said, \"The cheque matters to everyone.\"", "\"Yes,\" Luna answered. \"So everyone can help protect it.\""),
    ("Pip whispered, \"Do you think the little swimmer is helping us?\"", "\"Let's thank it by helping carefully too,\" Luna said."),
]

REACTIONS = [
    "Pip's face brightened",
    "Luna felt a warm flutter in her chest",
    "the nearby shoppers smiled",
    "even the market dog stopped to watch",
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming storyworld about a cray, a cheque, sound effects, and sharing."
    )
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--companion", choices=COMPANION_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
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
    choices = [name for name in COMPANION_NAMES if name != hero]
    companion = args.companion or rng.choice(choices)
    if hero == companion:
        raise StoryError("The hero and companion must be different characters.")
    return StoryParams(
        hero=hero,
        companion=companion,
        animal="a cray",
        place=args.place or rng.choice(PLACES),
        prize=args.prize or rng.choice(PRIZES),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "child"),
        companion=Entity(params.companion, "friend"),
        creature=Entity("the cray", "river_creature"),
    )


def simulate(world: World) -> None:
    p = world.params
    arc = ARCS[p.arc]
    rng = random.Random(p.seed)
    h = world.hero
    c = world.companion

    h.memes["care"] = 1.0
    c.memes["helpfulness"] = 1.0
    world.creature.meters["distance_to_cheque"] = 0.4
    world.creature.memes["helpfulness"] = 1.0
    world.facts.update(
        {
            "place": p.place,
            "cheque": True,
            "animal": "cray",
            "problem": arc["problem"],
            "stake": arc["stake"],
            "clue": arc["clue"],
            "sharing": True,
        }
    )

    world.say(
        f"{rng.choice(OPENINGS)}. At {p.place}, {h.name} and {c.name} prepared for a busy day."
    )
    world.say(f"{arc['premise']}. The cheque was tucked safely inside a small red envelope.")
    world.say(f"{rng.choice(SOUND_EFFECTS)} The river seemed to hum along with them.")
    world.para()

    world.say(f"Then {arc['problem']}. {arc['stake']}.")
    first, second = rng.choice(DIALOGUE)
    world.say(f"{first} {second}")
    world.facts["risk"] = arc["stake"]
    h.memes["worry"] = 1.0

    world.para()
    world.say(f"{rng.choice(FLASHBACK_LEADS)} {arc['memory']}.")
    world.say(f"{c.name} noticed that {arc['clue']}.")
    world.say(f"{arc['action']}.")
    world.say(f"Here came the turn: {arc['twist']}. {rng.choice(REACTIONS).capitalize()}.")
    world.facts["flashback"] = arc["memory"]
    world.facts["solution"] = arc["action"]
    world.facts["twist"] = arc["twist"]
    h.memes["hope"] = 1.0

    world.para()
    world.say(f"{arc['sharing']}.")
    world.say(
        f"{h.name} said, \"A cheque can pay for something important, but kindness is what helps it reach people.\""
    )
    world.say(f"{c.name} answered, \"Then let's keep sharing the good part.\"")
    world.say(f"As evening settled, {arc['ending']}.")
    world.facts["resolved"] = True
    world.facts["ending_image"] = arc["ending"]
    h.memes["joy"] = 1.0
    c.memes["joy"] = 1.0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a heartwarming story about {params.hero} finding a cheque with help from a cray.",
        f"Tell a child-friendly tale in {params.place} using sound effects, a flashback, and sharing.",
        f"Create a story where {params.hero} and {params.companion} solve this problem: {arc['problem']}.",
    ]
    story_qa = [
        QAItem(
            question=f"Why was {params.hero} carrying the cheque?",
            answer=arc["answer"],
        ),
        QAItem(
            question=f"What clue helped {params.hero} and {params.companion}?",
            answer=f"They noticed that {arc['clue']}, which helped them find a safe way to act.",
        ),
        QAItem(
            question="What did the cray do?",
            answer=f"The cray helped by ensuring that {arc['twist'].split(';')[0].lower()}.",
        ),
        QAItem(
            question="What did Luna remember in the flashback?",
            answer=f"Luna remembered that {arc['memory'].lower()}",
        ),
        QAItem(
            question="How did sharing change the ending?",
            answer=f"Sharing allowed the good result to reach more people: {arc['sharing']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a cray?",
            answer="A cray is a small freshwater crustacean with claws, similar to a little river lobster.",
        ),
        QAItem(
            question="What is a cheque?",
            answer="A cheque is a written promise directing a bank to pay money to someone or an organization.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means willingly letting other people use, enjoy, or benefit from something.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that briefly shows an earlier memory or event.",
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
    for ent in [world.hero, world.companion, world.creature]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.name:12} ({ent.kind:15}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
valid(story) :-
    domain(cheque),
    feature(sharing),
    feature(sound_effects),
    feature(flashback),
    creature(cray).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("domain", "cheque"),
            asp.fact("creature", "cray"),
            asp.fact("feature", "sharing"),
            asp.fact("feature", "sound_effects"),
            asp.fact("feature", "flashback"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    if asp.atoms(model, "valid") == [("story",)]:
        print("OK: ASP twin is consistent.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


CURATED = [
    StoryParams(hero="Luna", companion="Pip", place="the riverside market", prize="a blue umbrella", arc=0, seed=101),
    StoryParams(hero="Mara", companion="Jo", place="the little canal fair", prize="a warm wool scarf", arc=1, seed=202),
    StoryParams(hero="Ivy", companion="Sol", place="the sunny bridge market", prize="a basket of honey cakes", arc=3, seed=303),
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
        model = asp.one_model(asp_program("#show valid/1."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
