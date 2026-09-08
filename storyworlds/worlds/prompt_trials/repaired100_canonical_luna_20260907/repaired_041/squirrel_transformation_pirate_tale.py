#!/usr/bin/env python3
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
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "pirate tale"
SEED_WORDS = {"squirrel"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        for key in ("height", "speed", "shine", "fear"):
            self.meters.setdefault(key, 0.0)
        for key in ("courage", "curiosity", "trust", "joy", "worry"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    captain: str = "Luna"
    squirrel: str = "Pip"
    parrot: str = "Mango"
    island: int = 0
    transformation: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Adventure:
    treasure: str
    trouble: str
    clue: str
    false_lead: str
    transformation: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending: str


ADVENTURES = [
    Adventure(
        treasure="a moon-pearl compass",
        trouble="the compass began to glow, and a storm pulled the ship toward a reef",
        clue="three silver acorn shells arranged beside the broken wheel",
        false_lead="a black flag fluttering near the reef",
        transformation="the squirrel grew a tiny captain's coat and a tail shaped like a ship's sail",
        discovery="found the compass inside a hollow mast beam",
        cause="had hidden the compass while trying to keep it safe from the storm",
        repair="steered by the compass while the squirrel's sail-tail caught the calm wind",
        proof="the ship passed the reef and the compass pointed steadily home",
        lesson="A surprising change can become useful when friends understand it and work together.",
        ending="At sunset, the little sail-tail fluttered above the deck like a golden flag.",
    ),
    Adventure(
        treasure="a chest of cinnamon coins",
        trouble="the treasure map washed overboard just as the tide turned the ship in circles",
        clue="a trail of acorn shells leading from the map table to the warm galley oven",
        false_lead="a sea monster's shadow beneath the waves",
        transformation="the squirrel changed into a round, bright-eyed lookout with whiskers long enough to feel the breeze",
        discovery="spotted the map drying beneath a galley cloth",
        cause="had carried the map away from splashing waves and forgotten where it placed it",
        repair="followed the whiskers' wind-sense and sailed back toward the marked cove",
        proof="the crew reached the cove before dark and found the cinnamon coins safe",
        lesson="A helper's unusual gift matters when it is used with care.",
        ending="The cinnamon coins jingled while the transformed lookout watched the first star rise.",
    ),
    Adventure(
        treasure="a bottle holding a friendly sea breeze",
        trouble="the bottle cracked, and the ship lost its wind beside a quiet island",
        clue="a tuft of gray fur caught on the bottle's cork",
        false_lead="a bright trail of fish leading around the island",
        transformation="the squirrel became a tiny cloud with a fluffy tail and a rumbling little voice",
        discovery="found the missing cork tucked under a coil of rope",
        cause="had tugged the rope to pull the cork loose while chasing a falling nut",
        repair="used the cloud-tail to puff the breeze back into the bottle",
        proof="the sail filled, the crack stopped spreading, and the ship moved again",
        lesson="Taking responsibility turns an accident into a chance to help.",
        ending="The ship sailed on beneath a small friendly cloud that smelled of pine nuts.",
    ),
    Adventure(
        treasure="a silver key to the captain's cabin",
        trouble="the key vanished before the crew could open a mysterious locked chest",
        clue="tiny pawprints crossing a smear of blue paint near the anchor winch",
        false_lead="a brass button glittering beside the cabin door",
        transformation="the squirrel turned blue from nose to tail and could blend into the painted deck",
        discovery="noticed the key shining beneath the anchor rope",
        cause="had carried the key while exploring and dropped it when the anchor clattered",
        repair="used the blue transformation to reach safely beneath the rope and lift the key",
        proof="the chest opened to reveal a letter thanking the whole crew",
        lesson="A mistake is easier to fix when everyone searches kindly instead of blaming.",
        ending="The blue squirrel grinned beside the open chest, where the silver key gleamed.",
    ),
]


@dataclass
class World:
    captain: Entity
    squirrel: Entity
    parrot: Entity
    ship: Entity
    treasure: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def build_world(params: StoryParams, adventure: Adventure) -> World:
    captain = Entity(
        params.captain,
        "character",
        "captain",
        "the captain",
        memes={"courage": 1.0, "curiosity": 1.0, "trust": 1.0},
        location="deck",
    )
    squirrel = Entity(
        params.squirrel,
        "character",
        "squirrel",
        "the squirrel",
        memes={"curiosity": 2.0, "worry": 1.0},
        location="deck",
    )
    parrot = Entity(
        params.parrot,
        "character",
        "parrot",
        "the parrot",
        memes={"trust": 1.0, "joy": 1.0},
        location="mast",
    )
    ship = Entity(
        "seastar",
        "vehicle",
        "ship",
        "the ship",
        meters={"height": 8.0, "speed": 1.0},
        location="sea",
    )
    treasure = Entity(
        "treasure",
        "object",
        "treasure",
        adventure.treasure,
        meters={"shine": 2.0},
        location="hidden",
    )
    return World(captain, squirrel, parrot, ship, treasure)


def tell(params: StoryParams) -> World:
    if params.captain == params.squirrel:
        raise StoryError("The captain and squirrel must have different names.")
    if params.parrot in {params.captain, params.squirrel}:
        raise StoryError("The parrot must have a different name from the other characters.")

    adventure = ADVENTURES[params.island % len(ADVENTURES)]
    world = build_world(params, adventure)
    c, s, p = world.captain, world.squirrel, world.parrot

    c.memes["worry"] += 1
    s.memes["curiosity"] += 1
    world.ship.meters["speed"] = 0.0

    openings = [
        f"Captain {c.id} sailed the little ship Seastar across the blue sea with {s.id} the squirrel and {p.id} the parrot.",
        f"On a bright morning, Captain {c.id} called the crew together: {s.id} the squirrel and {p.id} the parrot were ready for a treasure voyage.",
        f"The Seastar danced over the waves while Captain {c.id}, {s.id}, and {p.id} searched the horizon for adventure.",
        f"Captain {c.id} kept the wheel steady as {s.id} the squirrel guarded the map and {p.id} watched from the mast.",
    ]
    world.say(openings[params.dialogue % len(openings)])
    world.say(f"They were sailing toward {adventure.treasure}, but {adventure.trouble}.")
    world.say(f"The ship slowed, and the crew could not tell whether the treasure or the vessel was in greater danger.")

    world.para()
    world.say(f"On the deck, they found {adventure.clue}. Nearby, {adventure.false_lead}.")
    thoughts = [
        f"Captain {c.id} said, 'The acorn shells are close to our tools, so they may explain what happened.'",
        f"'A shadow can frighten us,' Captain {c.id} said, 'but the clue on our deck can guide us.'",
        f"{p.id} squawked, 'Look down before you look far away!' Captain {c.id} listened carefully.",
        f"{s.id} whispered, 'I know something about this.' Captain {c.id} answered, 'Tell us, and we will solve it together.'",
    ]
    world.say(thoughts[params.transformation % len(thoughts)])
    world.say(f"{p.id} flapped down and asked, 'Should I search the mast?' 'Yes,' said Captain {c.id}, 'while {s.id} and I check the deck.'")
    world.say(f"The crew split up so that {p.id} could inspect the rigging while the others followed the clue.")

    world.para()
    world.say("The first search found only salt and loose rope. Then the clue changed the search: the shells marked a place where small paws had worked.")
    world.say(f"{s.id} trembled, and a shimmer ran from its ears to its tail. In a blink, {adventure.transformation}.")
    s.meters["height"] = 1.0
    s.meters["speed"] = 2.0
    s.memes["worry"] = 0.0
    s.memes["courage"] += 2.0
    world.say(f"Captain {c.id} did not run away. 'You are still our friend,' Captain {c.id} said. '{s.id}, can your new shape help us?'")
    world.say(f"'I think so,' said {s.id}. 'I can try.' The transformation gave the squirrel a new way to notice the hidden path.")
    world.say(f"Working together, the crew {adventure.discovery}.")
    world.say(f"{s.id} lowered its head and admitted, 'I {adventure.cause}. I wanted to help, but I should have told you sooner.'")
    world.say(f"Captain {c.id} replied, 'Thank you for telling the truth. Now let us use what we know.'")

    world.para()
    c.memes["trust"] += 2.0
    s.memes["trust"] += 2.0
    p.memes["trust"] += 1.0
    world.ship.meters["speed"] = 2.0
    world.say(f"The crew {adventure.repair}.")
    world.say(f"They tested the plan: {adventure.proof}.")
    world.say(f"{p.id} gave a proud squawk, and Captain {c.id} tied a soft ribbon around {s.id}'s new tail.")
    world.say(f"They agreed that the transformation was not a curse or a joke. It was a change they could understand and use wisely.")
    world.say(f"The captain's lesson was simple: {adventure.lesson}")

    world.para()
    endings = [
        adventure.ending,
        f"The crew cheered, and {adventure.ending}",
        f"Even the waves seemed to clap. {adventure.ending}",
        f"With the ship safe and the treasure near, {adventure.ending}",
    ]
    world.say(endings[params.ending % len(endings)])

    world.facts.update(
        adventure=adventure,
        treasure=adventure.treasure,
        trouble=adventure.trouble,
        clue=adventure.clue,
        transformation=adventure.transformation,
        discovery=adventure.discovery,
        cause=adventure.cause,
        repair=adventure.repair,
        proof=adventure.proof,
        lesson=adventure.lesson,
        ending=adventure.ending,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, s, p = world.captain.id, world.squirrel.id, world.parrot.id
    return [
        QAItem(
            question=f"What trouble did Captain {c} and the crew face?",
            answer=f"They faced this danger: {f['trouble']}. The trouble stopped the ship from safely reaching {f['treasure']}.",
        ),
        QAItem(
            question=f"What clue helped {c} understand the mystery?",
            answer=f"The useful clue was {f['clue']}. It was stronger than the distracting false lead because it was directly connected to the ship's deck and the missing object.",
        ),
        QAItem(
            question=f"How did {s} change during the adventure?",
            answer=f"{s} transformed in this way: {f['transformation']}. The new form helped the squirrel {f['repair']}.",
        ),
        QAItem(
            question=f"What did {s} admit after the treasure was found?",
            answer=f"{s} admitted, 'I {f['cause']}.' The squirrel had made a mistake while trying to help and then chose to tell the truth.",
        ),
        QAItem(
            question="What did the crew learn?",
            answer=f"They learned that {f['lesson']} The captain's trust helped everyone solve the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a squirrel?",
            answer="A squirrel is a small animal with a bushy tail that often gathers nuts and climbs trees.",
        ),
        QAItem(
            question="What is a pirate tale?",
            answer="A pirate tale is an adventure story about sailors, ships, treasure, storms, and brave choices.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form, appearance, or condition into another.",
        ),
        QAItem(
            question="Why is it important to tell the truth after an accident?",
            answer="Telling the truth helps friends understand what happened, repair the damage, and make a safer plan.",
        ),
        QAItem(
            question="What does a captain do on a ship?",
            answer="A captain guides the crew, makes careful decisions, and helps keep the ship and its passengers safe.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly pirate tale about {world.squirrel.id} the squirrel, a ship, and {f['treasure']}.",
        f"Tell a transformation story in which {world.squirrel.id} changes form and uses the change to solve this problem: {f['trouble']}.",
        f"Create a gentle sea adventure with Captain {world.captain.id}, {world.squirrel.id} the squirrel, and {world.parrot.id} the parrot. Include dialogue, an honest admission, and a hopeful ending.",
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
    for entity in (world.captain, world.squirrel, world.parrot, world.ship, world.treasure):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) location={entity.location!r} "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(pirate_tale).
feature(pirate_tale, transformation).
requires(pirate_tale, squirrel).
valid_story(S) :- setting(S), feature(S, transformation), requires(S, squirrel).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("setting", "pirate_tale"),
            asp.fact("feature", "pirate_tale", "transformation"),
            asp.fact("requires", "pirate_tale", "squirrel"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(atom.name == "valid_story" for atom in model)
    if not ok:
        print("MISMATCH: ASP rules did not recognize the pirate transformation story.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if "squirrel" not in sample.story.lower():
            print("MISMATCH: generated story omitted squirrel.")
            return 1
        if "transformed" not in sample.story.lower() and "changed" not in sample.story.lower():
            print("MISMATCH: generated story omitted transformation.")
            return 1
        if not sample.story_qa:
            print("MISMATCH: generated story omitted story QA.")
            return 1
    print("OK: ASP and Python recognize the pirate transformation story domain.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate transformation tale with a squirrel crew member.")
    parser.add_argument("--captain", default=None)
    parser.add_argument("--squirrel", default=None)
    parser.add_argument("--parrot", default=None)
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    captain = args.captain or rng.choice(["Luna", "Mara", "Cleo", "Nora"])
    squirrel = args.squirrel or rng.choice(["Pip", "Nutmeg", "Acorn", "Tumble"])
    parrot = args.parrot or rng.choice(["Mango", "Skipper", "Pearl", "Sunny"])
    if len({captain, squirrel, parrot}) != 3:
        raise StoryError("Captain, squirrel, and parrot must have different names.")
    offset = sample_seed - base_seed
    return StoryParams(
        captain=captain,
        squirrel=squirrel,
        parrot=parrot,
        island=offset % len(ADVENTURES),
        transformation=(offset // len(ADVENTURES)) % 4,
        dialogue=(offset // (len(ADVENTURES) * 4)) % 4,
        ending=(offset // (len(ADVENTURES) * 4 * 4)) % 4,
        seed=sample_seed,
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
    StoryParams(captain="Luna", squirrel="Pip", parrot="Mango", island=0, transformation=0),
    StoryParams(captain="Mara", squirrel="Acorn", parrot="Pearl", island=1, transformation=1),
    StoryParams(captain="Cleo", squirrel="Nutmeg", parrot="Sunny", island=2, transformation=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n) and index < max(50, args.n * 50):
            sample_seed = base_seed + index
            params = resolve_params(args, random.Random(sample_seed), sample_seed, base_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
