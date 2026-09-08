#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about Lot and Pappo, suspense, teamwork,
and an inner monologue beneath a moonlit hill.
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
    hero: str = "Lot"
    companion: str = "Pappo"
    place: str = "the Whispering Wood"
    treasure: str = "a moonseed"
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


HERO_NAMES = ["Lot", "Lumi", "Taro", "Mira", "Nell", "Odo"]
COMPANION_NAMES = ["Pappo", "Bibi", "Roon", "Fenn", "Mallow", "Pip"]
PLACES = [
    "the Whispering Wood",
    "the silver hill",
    "the old moon garden",
    "the valley of blue bells",
]
TREASURES = [
    "a moonseed",
    "a sleeping dragonfly",
    "a bell made of starlight",
    "a crystal acorn",
]

ARCS = [
    {
        "premise": "The queen of the fairies had planted a moonseed in a tiny golden pot",
        "problem": "a black wind carried the pot into a hollow where the shadows moved",
        "stake": "Without the moonseed, the village lanterns would go dark before winter",
        "temptation": "to creep into the hollow alone and snatch the pot before anyone could stop them",
        "clue": "the shadows froze whenever two lanterns shone together",
        "action": "Lot and Pappo tied their scarves into a long line and carried two lanterns side by side",
        "twist": "the moving shadows were only shy mushrooms opening and closing beneath the pot",
        "sharing": "They lifted the moonseed together and planted it where every cottage could see its light",
        "lesson": "courage grows steadier when friends bring their lights together",
        "ending": "a silver sprout rose above the village, and its glow painted two small shadows hand in hand",
        "question": "Why did Lot and Pappo need to recover the moonseed?",
        "answer": "They needed to recover it so the village lanterns would not go dark before winter.",
    },
    {
        "premise": "Pappo found a royal map tucked inside a singing leaf",
        "problem": "the map pointed toward a bridge that vanished whenever someone crossed alone",
        "stake": "The fairy baker could not reach the flour mill before dawn",
        "temptation": "to hurry over the bridge first and win the king's golden button",
        "clue": "the bridge appeared whenever two voices sang the same note",
        "action": "Lot and Pappo joined hands and sang one clear note as they stepped together",
        "twist": "the bridge was not made of stone; it was woven from the echo of their friendship",
        "sharing": "They led the baker across and taught the whole village the bridge song",
        "lesson": "some paths appear only when people trust one another",
        "ending": "at dawn, the bridge shimmered over the stream while flour-white birds sang below",
        "question": "How did Lot and Pappo make the bridge appear?",
        "answer": "They joined hands and sang the same clear note while stepping together.",
    },
    {
        "premise": "Lot was asked to carry a tiny star to the sleeping giant's tower",
        "problem": "the stairway became steeper each time the star trembled",
        "stake": "The giant would wake in darkness and mistake the village for a dream",
        "temptation": "to hide the star in a pocket and climb quickly without help",
        "clue": "the star grew calm whenever Pappo spoke a gentle counting rhyme",
        "action": "Pappo counted each step while Lot shielded the star with both hands",
        "twist": "the star was not afraid of the tower; it was afraid of being carried by only one person",
        "sharing": "They placed the star in a little basket and passed it carefully between them",
        "lesson": "a heavy hope becomes lighter when care is shared",
        "ending": "the giant opened one kind eye beneath a ceiling full of stars",
        "question": "What calmed the trembling star?",
        "answer": "Pappo's gentle counting rhyme calmed the star as they climbed.",
    },
    {
        "premise": "A fairy fox invited Lot and Pappo to find a ruby hidden under the wishing tree",
        "problem": "a ring of thorny vines closed around the tree at sunset",
        "stake": "The tree would lose its wishes if the ruby stayed buried",
        "temptation": "to cut through the vines alone and claim the ruby as a brave prize",
        "clue": "the thorns bent away whenever someone thanked them",
        "action": "They thanked each vine and carefully loosened the roots together",
        "twist": "the ruby was a seed that had been waiting for kind words before it could grow",
        "sharing": "They planted it beside the tree and invited every child to make one gentle wish",
        "lesson": "kindness can open doors that strength cannot",
        "ending": "ruby flowers opened around the wishing tree, one for every grateful voice",
        "question": "What made the thorny vines bend away?",
        "answer": "The vines bent away whenever Lot and Pappo thanked them.",
    },
]


OPENINGS = [
    "At twilight, when the first star blinked awake",
    "Once, beneath a lavender moon",
    "At the edge of a forest where the moss wore silver",
    "On a night when the fireflies flew in a secret pattern",
    "Long ago, when wishes still had wings",
]

THOUGHTS = [
    "Lot's thoughts fluttered like a moth near a candle",
    "Inside Lot's mind, a small brave voice whispered",
    "Lot felt one thought pull forward and another tug back",
    "For a moment, Lot's heart beat louder than the forest",
    "Lot wondered whether bravery meant rushing or listening",
]

DECISIONS = [
    "'If I hurry alone, I may make the dark grow wider. I will ask Pappo what he sees.'",
    "'A true hero need not be first. A true hero helps the whole path become safe.'",
    "'My fear is loud, but our plan can be louder. I will not leave my friend behind.'",
    "'One pair of eyes may miss a secret. Two caring friends may find it.'",
]

REACTIONS = [
    "Pappo's ears lifted in surprise",
    "Pappo gave a tiny gasp and squeezed Lot's hand",
    "The fairy fox clapped beneath its silver hood",
    "Even the moon seemed to lean closer",
    "The dark made a soft, surprised sigh",
]

CODAS = [
    "Lot learned that a brave heart is not a heart without fear, but a heart that makes room for a friend.",
    "From that night on, Lot and Pappo carried two lanterns whenever a path looked uncertain.",
    "The village remembered their adventure whenever someone said that a small team could not change a large night.",
    "And the moonseed taught everyone that light is happiest when it is shared.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fairy-tale storyworld about Lot, Pappo, suspense, and teamwork."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--companion", choices=COMPANION_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--treasure", choices=TREASURES)
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
        treasure=args.treasure or rng.choice(TREASURES),
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
    params = world.params
    hero = world.hero
    companion = world.companion
    arc = ARCS[params.arc]
    rng = random.Random(params.seed)

    hero.memes["curiosity"] = 1.0
    hero.memes["fear"] = 1.0
    companion.memes["steadiness"] = 1.0
    world.facts.update(
        {
            "place": params.place,
            "treasure": params.treasure,
            "problem": arc["problem"],
            "stake": arc["stake"],
            "clue": arc["clue"],
            "resolved": False,
        }
    )

    opening = rng.choice(OPENINGS)
    world.say(
        f"{opening}, {hero.name} and {companion.name} lived near {params.place}. "
        f"They were small enough to fit beneath a fern, yet curious enough to notice "
        f"secrets beneath the roots."
    )
    world.say(f"{arc['premise']}, and its precious gift was {params.treasure}.")
    world.para()

    world.say(f"Then {arc['problem']}. {arc['stake']}.")
    world.say(
        f"For one tense moment, {hero.name} wanted {arc['temptation']}."
    )
    world.say(f"{rng.choice(THOUGHTS)}. {hero.name} thought, {rng.choice(DECISIONS)}")
    world.facts["temptation"] = arc["temptation"]
    hero.memes["hesitation"] = 1.0

    world.para()
    world.say(
        f'{companion.name} whispered, "Let us look together before we step into the dark." '
        f'{hero.name} answered, "Together, then. Tell me what you notice."'
    )
    world.say(f"They listened, and {arc['clue']}.")
    world.say(f"{arc['action']}.")
    world.say(f"At the darkest instant, {arc['twist']}. {rng.choice(REACTIONS)}.")
    world.facts["twist"] = arc["twist"]
    world.facts["solution"] = arc["action"]
    hero.memes["trust"] = 1.0
    companion.memes["trust"] = 1.0

    world.para()
    world.say(f"{arc['sharing']}.")
    world.say(
        f"{rng.choice(CODAS)} {hero.name} and {companion.name} smiled at one another."
    )
    world.say(f"By morning, {arc['ending']}.")
    world.facts["resolved"] = True
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.companion:
        raise StoryError("A story needs two different friends for teamwork.")
    if not 0 <= params.arc < len(ARCS):
        raise StoryError("The chosen fairy-tale arc does not exist.")

    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]

    prompts = [
        f"Write a suspenseful fairy tale about {params.hero} and {params.companion} using teamwork.",
        f"Tell a child-friendly story in {params.place} about finding {params.treasure}.",
        f"Show {params.hero}'s inner monologue before the friends choose a safer plan.",
    ]

    story_qa = [
        QAItem(
            question=f"What danger did {params.hero} and {params.companion} face?",
            answer=f"They faced a danger because {arc['problem']}.",
        ),
        QAItem(
            question=f"What did {params.hero} first consider doing?",
            answer=f"{params.hero} first considered trying {arc['temptation']}.",
        ),
        QAItem(
            question=f"What clue helped the friends?",
            answer=f"The clue was that {arc['clue']}.",
        ),
        QAItem(
            question=f"What surprising truth did they discover?",
            answer=f"They discovered that {arc['twist']}.",
        ),
        QAItem(
            question=f"What lesson did {params.hero} learn?",
            answer=f"{params.hero} learned that {arc['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people combine their efforts and help one another reach a goal.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen while a character faces uncertainty or danger.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private stream of thoughts shown to the reader.",
        ),
        QAItem(
            question="What makes a fairy tale?",
            answer="A fairy tale is a story that often includes wonder, magic, brave choices, and a meaningful ending.",
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
            f"  {entity.name:10} ({entity.kind:10}) "
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
valid(story) :-
    domain(fairy_tale),
    feature(suspense),
    feature(teamwork),
    feature(inner_monologue),
    requires(lot),
    requires(pappo).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("domain", "fairy_tale"),
        asp.fact("feature", "suspense"),
        asp.fact("feature", "teamwork"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("requires", "lot"),
        asp.fact("requires", "pappo"),
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

    for params in CURATED:
        sample = generate(params)
        if not sample.story or "Lot" not in sample.story and "Pappo" not in sample.story:
            print("MISMATCH: generated story is incomplete.")
            return 1
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: Python simulation did not resolve.")
            return 1

    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(
        hero="Lot",
        companion="Pappo",
        place="the Whispering Wood",
        treasure="a moonseed",
        arc=0,
        seed=101,
    ),
    StoryParams(
        hero="Lumi",
        companion="Bibi",
        place="the silver hill",
        treasure="a bell made of starlight",
        arc=1,
        seed=202,
    ),
    StoryParams(
        hero="Taro",
        companion="Roon",
        place="the old moon garden",
        treasure="a crystal acorn",
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
        raise SystemExit(asp_verify())
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
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
