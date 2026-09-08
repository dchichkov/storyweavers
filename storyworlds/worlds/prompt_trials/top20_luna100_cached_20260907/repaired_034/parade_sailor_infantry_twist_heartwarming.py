#!/usr/bin/env python3
"""
A heartwarming storyworld about a parade, a sailor, and an infantry band
whose surprising twist turns a march into a welcome for everyone.
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
    companion: str = "Mara"
    place: str = "the harbor square"
    prize: str = "the golden parade ribbon"
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
    sailor: Entity
    infantry: Entity
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


HERO_NAMES = ["Luna", "Pip", "Nora", "Tavi", "Milo", "Sia"]
COMPANION_NAMES = ["Mara", "Theo", "Bea", "Jon", "Ivy", "Oren"]
PLACES = [
    "the harbor square",
    "the lighthouse green",
    "the old town avenue",
    "the sunny market street",
]
PRIZES = [
    "the golden parade ribbon",
    "a bright brass badge",
    "the mayor's blue pennant",
    "a silver bell for the lead drum",
]

ARCS = [
    {
        "premise": "The town was preparing its spring parade beside the harbor",
        "problem": "the infantry band's small drummer could not find the beat after a gust scattered the music pages",
        "stake": "Without a steady rhythm, the sailors and marching families might lose their way through the crowded street",
        "temptation": "rush to the front and win the golden parade ribbon alone",
        "clue": "the sailor's rope bell rang in the same slow pattern as the drummer's first three notes",
        "action": "Luna tied the pages together, while Mara rang the bell and the infantry listened for the shared rhythm",
        "twist": "the lost pages had blown beneath a bench where a shy child was using them to draw pictures of the parade",
        "sharing": "The child returned the pages, and the band left a blank one for a new parade picture",
        "lesson": "a celebration grows brighter when everyone is given a place in it",
        "ending": "the parade rolled on with music, flags, and one fresh drawing held high above the sailor's cap",
        "question": "Why did the parade need a steady rhythm?",
        "answer": "The parade needed a steady rhythm so the sailors, infantry, and families could move safely together.",
    },
    {
        "premise": "The harbor town held a welcome parade for sailors returning from a long voyage",
        "problem": "the welcome arch leaned toward the marching path",
        "stake": "The arch could fall just as the infantry band and sailors came through",
        "temptation": "pull it upright alone and receive all the praise",
        "clue": "the arch became steadier whenever two flag ropes were held at opposite corners",
        "action": "Luna asked the sailors for spare cord, and Mara guided the infantry into a careful circle around the arch",
        "twist": "the arch was not broken; a nest of tiny birds had made one corner too heavy",
        "sharing": "They moved the nest gently to a nearby tree and decorated both places with soft blue ribbons",
        "lesson": "careful help can protect a welcome without hurting the smallest neighbors",
        "ending": "the birds chirped above the arch while the returning sailors marched underneath it",
        "question": "What made the welcome arch lean?",
        "answer": "A nest of tiny birds had made one corner of the arch too heavy.",
    },
    {
        "premise": "The infantry band practiced a gentle march for the town's lantern parade",
        "problem": "the lead sailor's lantern went dark before sunset",
        "stake": "The parade route would be hard to see along the river bend",
        "temptation": "hide the brightest lantern and carry it at the front",
        "clue": "small reflections trembled inside the empty lantern whenever people stood close",
        "action": "The sailors polished their buttons, the infantry lifted their lamps, and everyone gathered the little lights together",
        "twist": "the lantern had not lost its flame; it was a mirror lantern meant to collect many lights",
        "sharing": "They carried it in the middle so every marcher could lend a glow",
        "lesson": "some lights are made to gather what others freely give",
        "ending": "one lantern shone like a little moon as the parade crossed the river bend",
        "question": "How did the parade brighten the mirror lantern?",
        "answer": "The marchers gathered around it and shared the light from their smaller lamps and polished buttons.",
    },
    {
        "premise": "A sailor had sewn bright flags for the annual infantry parade",
        "problem": "the largest flag caught on a rooftop weather vane",
        "stake": "The flag might tear before it could lead the parade",
        "temptation": "climb quickly without telling anyone and become the hero of the day",
        "clue": "the flag loosened whenever the marching drum paused",
        "action": "Luna asked the infantry to stop the beat, while sailors raised a soft rope from below",
        "twist": "the weather vane had caught only a loose thread, and the flag's cloth had formed a tiny heart",
        "sharing": "They trimmed the thread and stitched the heart onto a banner for the town's children",
        "lesson": "a pause can reveal a beautiful answer that haste would miss",
        "ending": "the heart-shaped banner fluttered above the parade, stitched from the flag's lucky thread",
        "question": "Why did the infantry stop the drum?",
        "answer": "They stopped the drum so the flag would stop tugging and the sailors could free it safely.",
    },
    {
        "premise": "The town planned a parade to thank sailors and infantry helpers after a storm",
        "problem": "the thank-you cards were soaked by rain",
        "stake": "The children feared their messages of thanks would disappear",
        "temptation": "save only the card with the biggest drawing",
        "clue": "the wet ink left clear marks when pressed against dry cloth",
        "action": "The sailors stretched clean flags as drying cloth, and the infantry carried each card carefully between them",
        "twist": "the ink had made faint copies on the flags, turning the whole parade into a moving thank-you wall",
        "sharing": "They displayed every card and invited the children to march beside the people they had thanked",
        "lesson": "kind words can travel farther when people carry them together",
        "ending": "the parade flags waved with hundreds of small thank-you messages in the afternoon sun",
        "question": "What happened to the wet thank-you cards?",
        "answer": "Their words copied faintly onto the dry flags and became a moving thank-you wall.",
    },
    {
        "premise": "An old sailor led the town parade while the infantry played beside him",
        "problem": "he forgot which street led to the square",
        "stake": "The parade could split apart before reaching its celebration",
        "temptation": "pretend to know the way and keep marching proudly",
        "clue": "each neighborhood child remembered a different sound from the square",
        "action": "Luna asked the children to call out their sounds, and the infantry answered each one with a soft note",
        "twist": "the sailor had not forgotten the route; he had slowed down so a little wheelchair could join the parade",
        "sharing": "Everyone changed the pace, and the children became cheerful guides beside the wheels",
        "lesson": "the best leader makes room for every traveler",
        "ending": "the old sailor reached the square last, smiling as the whole parade arrived with him",
        "question": "Why had the old sailor slowed the parade?",
        "answer": "He had slowed down so a little wheelchair could safely join the parade.",
    },
    {
        "premise": "The harbor parade featured an infantry drum and a sailor's tiny whistle",
        "problem": "the two instruments seemed to be playing different songs",
        "stake": "The marchers could not tell when to turn at the fountain",
        "temptation": "silence the whistle and let the drum lead alone",
        "clue": "the whistle answered whenever the drum left a quiet space",
        "action": "Mara asked the musicians to trade short phrases instead of playing over one another",
        "twist": "the instruments were not arguing; they were making a call-and-response song for the parade",
        "sharing": "The musicians taught the pattern to the crowd, who answered with claps",
        "lesson": "listening turns separate voices into one welcoming song",
        "ending": "the fountain echoed with drum, whistle, and a thousand gentle claps",
        "question": "What was the whistle doing?",
        "answer": "The whistle was answering the drum in a call-and-response song.",
    },
    {
        "premise": "Sailors and infantry volunteers carried a giant paper sun in the town parade",
        "problem": "the paper sun folded in the middle of the route",
        "stake": "The children behind it could no longer see the sunny picture",
        "temptation": "keep carrying the unbroken edge and leave the middle behind",
        "clue": "the sun opened whenever children held its rays from both sides",
        "action": "Luna invited the children to take the paper handles while the sailors supported the frame",
        "twist": "the fold had hidden a second picture of the moon on the back",
        "sharing": "They turned the sun from side to side so the whole crowd could see both pictures",
        "lesson": "a surprise may give a celebration more than one beautiful face",
        "ending": "the parade carried sun and moon together beneath the first evening star",
        "question": "What picture was hidden behind the paper sun?",
        "answer": "A picture of the moon was hidden on the back of the folded paper sun.",
    },
]


OPENINGS = [
    "Morning bells rang above the bright harbor",
    "Sunlight spilled across the square and warmed every flag",
    "A soft breeze carried music down the old avenue",
    "The town woke to polished buttons, colorful ribbons, and smiling faces",
    "Gulls circled while parade drums practiced a gentle beat",
    "Along the market street, neighbors gathered with flowers in their hands",
]

DIALOGUE_PAIRS = [
    ("Mara asked, 'Should we hurry to the front?'", "'Only if we can bring everyone with us,' Luna replied."),
    ("The sailor called, 'What do you hear?'", "'A clue hiding beneath the parade noise,' Luna answered."),
    ("Mara whispered, 'Do you still want the prize?'", "'I want the parade to arrive safely more,' Luna said."),
    ("The infantry drummer asked, 'Can you help us find the beat?'", "'Listen to the bell with me,' Luna replied."),
    ("A child asked, 'May I join the march?'", "'Yes,' Luna said. 'Your step belongs beside ours.'"),
]

TWIST_REACTIONS = [
    "Mara's eyes grew wide, and then she smiled",
    "The sailor placed a hand over his heart",
    "The infantry band lowered its instruments in happy surprise",
    "The crowd grew quiet so the new truth could be heard",
    "Luna laughed softly when the hidden answer appeared",
]

CODAS = [
    "Luna learned that a true parade carries kindness as carefully as it carries flags.",
    "From then on, the town measured a fine march by the number of people who felt welcome.",
    "The prize mattered less than the warm feeling that moved from one neighbor to the next.",
    "Everyone went home with tired feet and bright hearts.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming parade storyworld with sailors, infantry, and a twist."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--companion", choices=COMPANION_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--prize", choices=PRIZES)
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
    companion = args.companion or rng.choice(
        [name for name in COMPANION_NAMES if name != hero]
    )
    if hero == companion:
        raise StoryError("The hero and companion must be different characters.")
    return StoryParams(
        hero=hero,
        companion=companion,
        place=args.place or rng.choice(PLACES),
        prize=args.prize or rng.choice(PRIZES),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "hero"),
        companion=Entity(params.companion, "companion"),
        sailor=Entity("the sailor", "sailor"),
        infantry=Entity("the infantry", "infantry"),
    )


def simulate(world: World) -> None:
    params = world.params
    hero = world.hero
    companion = world.companion
    arc = ARCS[params.arc]
    rng = random.Random(params.seed)

    hero.memes["curiosity"] = 1.0
    hero.memes["want_prize"] = 1.0
    world.sailor.memes["welcome"] = 1.0
    world.infantry.memes["steadiness"] = 1.0

    world.facts.update(
        {
            "place": params.place,
            "prize": params.prize,
            "problem": arc["problem"],
            "clue": arc["clue"],
            "resolved": False,
        }
    )

    opening = rng.choice(OPENINGS)
    world.say(
        f"{opening}. In {params.place}, {hero.name} and {companion.name} "
        f"helped a sailor and the infantry prepare a joyful parade."
    )
    world.say(
        f"The town promised {params.prize} to the person who helped the parade shine brightest. "
        f"{arc['premise']}."
    )
    world.para()

    world.say(f"Then {arc['problem']}. {arc['stake']}.")
    world.say(
        f"For a moment, {hero.name} wanted to {arc['temptation']}. "
        "The prize glittered, but the parade needed care more than speed."
    )
    first, second = rng.choice(DIALOGUE_PAIRS)
    world.say(f"{first} {second}")
    hero.memes["hesitation"] = 1.0
    world.facts["temptation"] = arc["temptation"]

    world.para()
    world.say(
        f"Instead of rushing, {hero.name} and {companion.name} paused. "
        f"They noticed that {arc['clue']}."
    )
    world.say(f"{arc['action']}.")
    world.say(f"Then came the twist: {arc['twist']}.")
    world.say(f"{rng.choice(TWIST_REACTIONS)}.")
    hero.memes["understanding"] = 1.0
    hero.memes["sharing"] = 1.0
    companion.memes["sharing"] = 1.0
    world.facts["twist"] = arc["twist"]
    world.facts["solution"] = arc["action"]

    world.para()
    world.say(f"{arc['sharing']}.")
    world.say(f"{hero.name} understood that {arc['lesson']}.")
    world.say(f"{rng.choice(CODAS)}")
    world.say(f"As the afternoon faded, {arc['ending']}.")
    world.facts["resolved"] = True
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]

    prompts = [
        f"Write a heartwarming parade story about {params.hero}, a sailor, and the infantry.",
        f"Tell a child-friendly story in {params.place} with a surprising twist.",
        f"Show how a parade problem is solved through listening and kindness.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} face during the parade?",
            answer=f"{params.hero} faced this problem: {arc['problem']}.",
        ),
        QAItem(
            question=f"What risky choice did {params.hero} first consider?",
            answer=f"{params.hero} first considered trying to {arc['temptation']}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} choose a better plan?",
            answer=f"The clue was that {arc['clue']}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {arc['twist']}.",
        ),
        QAItem(
            question=f"What did {params.hero} learn?",
            answer=f"{params.hero} learned that {arc['lesson']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended when {arc['ending']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized walk or march where people celebrate with music, flags, and decorations.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works or travels on a boat or ship.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who serve and move on foot.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that reveals the situation in a new way.",
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
    for entity in [world.hero, world.companion, world.sailor, world.infantry]:
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.name:14} ({entity.kind:10}) meters={meters} memes={memes}"
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
valid(story) :- domain(parade), role(sailor), role(infantry), feature(twist), style(heartwarming).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("domain", "parade"),
            asp.fact("role", "sailor"),
            asp.fact("role", "infantry"),
            asp.fact("feature", "twist"),
            asp.fact("style", "heartwarming"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/1."))
    if asp.atoms(model, "valid") != [("story",)]:
        print("MISMATCH: ASP twin failed.")
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story or "parade" not in sample.story.lower():
            print("MISMATCH: generated story is incomplete.")
            return 1
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated world did not resolve.")
            return 1

    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(
        hero="Luna",
        companion="Mara",
        place="the harbor square",
        prize="the golden parade ribbon",
        arc=0,
        seed=101,
    ),
    StoryParams(
        hero="Pip",
        companion="Theo",
        place="the lighthouse green",
        prize="a bright brass badge",
        arc=3,
        seed=202,
    ),
    StoryParams(
        hero="Nora",
        companion="Bea",
        place="the old town avenue",
        prize="a silver bell for the lead drum",
        arc=6,
        seed=303,
    ),
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

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 30, 30):
            rng = random.Random(base_seed + index)
            index += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
