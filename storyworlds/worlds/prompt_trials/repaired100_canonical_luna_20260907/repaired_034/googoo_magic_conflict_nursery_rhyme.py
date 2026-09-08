#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about Googoo, a little magic, and a gentle conflict.
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
    hero: str = "Googoo"
    companion: str = "Lulu"
    place: str = "the moonlit nursery"
    object: str = "a silver spoon"
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
    room: Entity
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


HEROES = ["Googoo", "Mimi", "Bobo", "Nunu", "Pip"]
COMPANIONS = ["Lulu", "Toto", "Dodo", "Fifi", "Momo"]
PLACES = [
    "the moonlit nursery",
    "the little blue bedroom",
    "the candle-bright playroom",
]
OBJECTS = [
    "a silver spoon",
    "a red toy drum",
    "a golden button",
    "a blue wool mitten",
]

ARCS = [
    {
        "premise": "Googoo found a tiny moonbeam hiding beneath the cradle",
        "problem": "the moonbeam had slipped into the night jar and would not come out",
        "stake": "Without it, the sleepy stars could not find the nursery window",
        "temptation": "shake the jar hard and keep the moonbeam all for himself",
        "clue": "the moonbeam trembled whenever a kind song floated near",
        "action": "Googoo and Lulu sang softly and tipped the jar toward the open window",
        "twist": "the moonbeam was not trapped by glass; it was waiting for a friend to sing",
        "resolution": "They let the moonbeam dance across every blanket and brighten every teddy bear",
        "lesson": "magic grows brighter when it is welcomed and shared",
        "ending": "the moonbeam painted silver socks on every sleeping toe",
        "question": "Why did the moonbeam need help?",
        "answer": "It needed help because it was waiting for a gentle song to guide it home.",
    },
    {
        "premise": "Googoo discovered a magic drum beside the toy chest",
        "problem": "the drum beat one loud boom whenever Lulu tried to rest",
        "stake": "Lulu could not settle down for her important nap",
        "temptation": "hide the drum under his pillow and claim its magic beat",
        "clue": "the drum grew quiet when someone tapped a slow heartbeat",
        "action": "Googoo and Lulu took turns making a soft tap-tap rhythm",
        "twist": "the drum was not being naughty; it was copying the fastest heart in the room",
        "resolution": "They slowed their breathing, and the drum hummed a peaceful lullaby",
        "lesson": "a quarrel can soften when everyone listens to the hidden feeling",
        "ending": "the little drum rested by the bed, whispering boom-boom like a dream",
        "question": "Why did the magic drum make loud noises?",
        "answer": "It copied the fastest heartbeat in the room, so it became quiet when everyone slowed down.",
    },
    {
        "premise": "Googoo wore a magic mitten that could catch falling dreams",
        "problem": "one bright dream floated away from Lulu's pillow",
        "stake": "Lulu might wake without the happy dream she had been saving",
        "temptation": "catch it first and keep its sparkle in his own pocket",
        "clue": "the dream drifted toward whoever called its name kindly",
        "action": "Googoo asked Lulu what her dream looked like and followed her careful directions",
        "twist": "the dream belonged to both friends because it showed them building a rainbow tower",
        "resolution": "They caught the dream together and tucked it back beneath Lulu's pillow",
        "lesson": "wonder is safest when its keepers trust one another",
        "ending": "a rainbow tower glowed softly between their beds until morning",
        "question": "How did Googoo and Lulu catch the drifting dream?",
        "answer": "Googoo listened to Lulu's directions, and together they guided the dream back beneath her pillow.",
    },
    {
        "premise": "Googoo found a magic crayon that drew whatever its owner wished",
        "problem": "Googoo and Lulu both reached for it at the same time",
        "stake": "Their tugging could tear the nursery's only picture book",
        "temptation": "pull hard and draw his favorite picture before Lulu could",
        "clue": "the crayon made its brightest colors when two hands held it gently",
        "action": "They agreed to draw one line each and pass the crayon after every rhyme",
        "twist": "their separate pictures joined into one garden full of friendly flowers",
        "resolution": "They filled the book with a shared garden and gave every flower a name",
        "lesson": "taking turns can turn a conflict into a creation",
        "ending": "the picture book bloomed with colors brighter than the dawn",
        "question": "What happened when Googoo and Lulu took turns with the crayon?",
        "answer": "Their separate lines joined together to make one bright garden.",
    },
]

OPENINGS = [
    "Hush-a-bye, the small stars winked",
    "Tiptoe moonlight crossed the floor",
    "Round and round the night clock ticked",
    "Softly sang the sleepy breeze",
    "Under quilts of yellow and blue",
]

DIALOGUE = [
    ("Lulu said, “Googoo, please wait. That is mine to use.”",
     "Googoo answered, “I hear you, Lulu. Let us find a fair way.”"),
    ("“Stop, Googoo,” cried Lulu. “The magic is making me cross.”",
     "“Then tell me what you need,” said Googoo. “I will listen.”"),
    ("Lulu whispered, “Could we share it, please?”",
     "Googoo nodded. “Yes. Your idea may help us both.”"),
    ("“I want a turn,” said Lulu.",
     "“You shall have one,” said Googoo. “We can make a plan together.”"),
]

RHYME_CODAS = [
    "So Googoo learned, as moonbeams gleam, that sharing can mend a troubled dream.",
    "And Lulu smiled beside the light: kind words had made the magic right.",
    "No tug or shout was needed then; a listening heart made friends again.",
    "They sang, “Take turns and care, care, care; the finest magic is the magic we share.”",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery-rhyme storyworld about Googoo, magic, and conflict."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", choices=OBJECTS)
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
    companion = args.companion or rng.choice([name for name in COMPANIONS if name != hero])
    if hero == companion:
        raise StoryError("The hero and companion must be different characters.")
    return StoryParams(
        hero=hero,
        companion=companion,
        place=args.place or rng.choice(PLACES),
        object=args.object or rng.choice(OBJECTS),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "hero"),
        companion=Entity(params.companion, "companion"),
        room=Entity(params.place, "place"),
    )


def simulate(world: World) -> None:
    p = world.params
    h = world.hero
    c = world.companion
    arc = ARCS[p.arc]
    rng = random.Random(p.seed)

    h.memes["curiosity"] = 1.0
    h.memes["magic_want"] = 1.0
    c.memes["trust"] = 1.0
    world.facts.update(
        {
            "place": p.place,
            "object": p.object,
            "problem": arc["problem"],
            "stake": arc["stake"],
            "clue": arc["clue"],
            "resolved": False,
        }
    )

    world.say(f"{rng.choice(OPENINGS)}. In {p.place}, {h.name} and {c.name} played near {p.object}.")
    world.say(f"{arc['premise']}. It shimmered with a tiny bit of magic.")
    world.para()

    world.say(f"But {arc['problem']}. {arc['stake']}.")
    world.say(f"For a moment, {h.name} wanted to {arc['temptation']}.")
    first, second = rng.choice(DIALOGUE)
    world.say(first)
    world.say(second)
    world.facts["conflict"] = True
    world.facts["temptation"] = arc["temptation"]
    h.memes["conflict"] = 1.0
    c.memes["conflict"] = 1.0

    world.para()
    world.say(f"Then {c.name} noticed that {arc['clue']}.")
    world.say(f"{h.name} paused, and the friends chose this plan: {arc['action']}.")
    world.say(f"Here was the magic twist: {arc['twist']}.")
    world.facts["twist"] = arc["twist"]
    world.facts["solution"] = arc["action"]
    h.memes["cooperation"] = 1.0
    c.memes["cooperation"] = 1.0

    world.para()
    world.say(f"{arc['resolution']}.")
    world.say(rng.choice(RHYME_CODAS))
    world.say(f"At bedtime, {arc['ending']}.")
    world.facts["resolved"] = True
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.companion:
        raise StoryError("The hero and companion must be different characters.")
    if not 0 <= params.arc < len(ARCS):
        raise StoryError("The selected rhyme arc does not exist.")

    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]

    prompts = [
        f"Write a nursery rhyme about {params.hero}, magic, and a conflict with {params.companion}.",
        f"Tell a child-friendly story in {params.place} where sharing solves a magical problem.",
        f"Make a rhyming tale about this problem: {arc['problem']}.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.companion} face?",
            answer=f"They faced a problem because {arc['problem']}.",
        ),
        QAItem(
            question=f"What did {params.hero} first want to do?",
            answer=f"{params.hero} first wanted to {arc['temptation']}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} and {params.companion}?",
            answer=f"They noticed that {arc['clue']}.",
        ),
        QAItem(
            question=f"What was the magical twist?",
            answer=f"They discovered that {arc['twist']}.",
        ),
        QAItem(
            question=f"What lesson did {params.hero} learn?",
            answer=f"{params.hero} learned that {arc['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is an impossible or wonderful power that changes what can happen.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a problem or disagreement that characters must work through.",
        ),
        QAItem(
            question="What is a nursery rhyme?",
            answer="A nursery rhyme is a short, playful poem or song with a simple rhythm and often a gentle story.",
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
    for entity in (world.hero, world.companion, world.room):
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.name:24} ({entity.kind:10}) meters={meters} memes={memes}")
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
valid(story) :-
    domain(nursery_rhyme),
    feature(magic),
    feature(conflict),
    has_hero(googoo).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("domain", "nursery_rhyme"),
            asp.fact("feature", "magic"),
            asp.fact("feature", "conflict"),
            asp.fact("has_hero", "googoo"),
        ]
    )


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    if asp.atoms(model, "valid") != [("story",)]:
        print("MISMATCH: ASP twin failed.")
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1

    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(
        hero="Googoo",
        companion="Lulu",
        place="the moonlit nursery",
        object="a silver spoon",
        arc=0,
        seed=101,
    ),
    StoryParams(
        hero="Mimi",
        companion="Toto",
        place="the little blue bedroom",
        object="a red toy drum",
        arc=1,
        seed=202,
    ),
    StoryParams(
        hero="Bobo",
        companion="Fifi",
        place="the candle-bright playroom",
        object="a golden button",
        arc=3,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("The number of stories must be at least one.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 20, 20):
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
