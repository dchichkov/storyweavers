#!/usr/bin/env python3
"""
A small heartwarming storyworld about a parade, a sailor, and an infantry band.

The simulation follows a sailor who wants to lead a bright parade, meets an
unexpected problem, listens to an infantry helper, and discovers a kinder way
to celebrate.
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
    sailor: str = "Luna"
    infantry_friend: str = "Mara"
    parade_place: str = "the riverside square"
    banner: str = "the blue harbor banner"
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
    sailor: Entity
    infantry_friend: Entity
    parade: Entity
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


SAILORS = ["Luna", "Theo", "Pia", "Niko", "Sami", "Rose"]
INFANTRY_FRIENDS = ["Mara", "Jo", "Inez", "Cal", "Bea", "Owen"]
PLACES = [
    "the riverside square",
    "the old market road",
    "the sunny station yard",
    "the town garden",
]
BANNERS = [
    "the blue harbor banner",
    "the red sunrise flag",
    "the green hill pennant",
    "the golden star banner",
]

ARCS = [
    {
        "premise": "The town was preparing a welcome parade for sailors returning from a long voyage",
        "problem": "a strong breeze tore the parade banner from its pole",
        "stake": "The returning crew might pass the square without seeing the welcome",
        "temptation": "run ahead alone and claim the honor of saving the parade",
        "clue": "the torn cloth still carried a row of tiny stitched stars",
        "action": "They invited the infantry band to hold the pole while families joined the sailors in sewing the cloth",
        "twist": "the banner had been stitched by children who had never met the returning sailors",
        "sharing": "The sailors carried the repaired banner at the front, and every child who helped walked beneath it",
        "lesson": "a welcome becomes brighter when everyone has a hand in making it",
        "ending": "the banner fluttered above the parade, patched with many colors and waving like a friendly sky",
        "question": "Why did the town need to repair the banner?",
        "answer": "The town needed to repair the banner so the returning sailors could see their welcome.",
    },
    {
        "premise": "An infantry band was leading a parade through the village after helping rebuild a footbridge",
        "problem": "the youngest drummer lost the beat when the crowd grew noisy",
        "stake": "The nervous child wanted to leave before the parade reached the bridge",
        "temptation": "march faster and let the band finish without waiting",
        "clue": "the child's fingers tapped softly whenever a sailor hummed a sea song",
        "action": "The sailors hummed a steady tune while the infantry players shaped their drums around it",
        "twist": "the lost beat was not gone; it had become the beginning of a new song",
        "sharing": "The young drummer led the final verse, with sailors and infantry marching beside them",
        "lesson": "patience can help a quiet gift find its brave voice",
        "ending": "the new song rolled over the bridge while the smallest drum shone in the afternoon sun",
        "question": "How did the band help the young drummer?",
        "answer": "The sailors hummed a steady tune so the young drummer could find a comfortable beat again.",
    },
    {
        "premise": "Sailors and infantry families gathered for a lantern parade at dusk",
        "problem": "the parade's lanterns began to go dark one by one",
        "stake": "The walkers could not safely find the winding path through the garden",
        "temptation": "keep the last bright lantern for the front of the parade",
        "clue": "a little mirror under each lantern still reflected a warm spark",
        "action": "They placed the lanterns in a circle and passed one candle flame carefully from light to light",
        "twist": "the dark lanterns were not broken; their wicks had been trimmed too short",
        "sharing": "The infantry carried spare wicks while sailors shared oil from their ship's lamp",
        "lesson": "a small supply can shine far when careful hands share it",
        "ending": "the parade wound through the garden as a necklace of lanterns, each glow borrowed from another",
        "question": "What helped the lanterns shine again?",
        "answer": "The group shared oil and spare wicks, then carefully relit the lanterns.",
    },
    {
        "premise": "A sailor's parade cart carried bread for everyone who had gathered to celebrate",
        "problem": "one wheel stuck in a muddy rut beside the road",
        "stake": "The warm bread might cool before the hungry families received it",
        "temptation": "pull the cart alone and prove that a sailor needed no help",
        "clue": "the infantry boots left deep, even marks in the soft mud",
        "action": "The infantry formed a steady line while sailors laid boards beneath the wheel",
        "twist": "the rut had been made by a small wagon carrying flowers for the parade",
        "sharing": "They freed both carts and placed bread beside the flowers at every doorstep",
        "lesson": "strength is most useful when it makes room for another person's need",
        "ending": "bread and bright flowers traveled together through the town on two rolling carts",
        "question": "How did the group free the bread cart?",
        "answer": "The infantry made a steady pulling line while the sailors placed boards beneath the stuck wheel.",
    },
    {
        "premise": "The annual parade honored people who had cared for the town during a hard winter",
        "problem": "the empty chair for an elderly flag maker stood at the front",
        "stake": "The parade felt cheerful, but its guest of honor could not walk to the square",
        "temptation": "continue with the music and pretend the missing chair did not matter",
        "clue": "a folded note said the flag maker could hear bells from the hill",
        "action": "The sailor and infantry friend carried the chair up the hill and brought the parade to the window",
        "twist": "the flag maker had made a small flag for every person in the parade",
        "sharing": "Everyone raised a handmade flag and waved them together from the hillside",
        "lesson": "celebration is kindest when it travels to someone who cannot come",
        "ending": "the hilltop window filled with waving flags, and the old flag maker smiled behind the glass",
        "question": "Why did the parade go up the hill?",
        "answer": "The parade went up the hill so the elderly flag maker could hear the bells and join the celebration from the window.",
    },
    {
        "premise": "A sailor and an infantry friend practiced a quiet morning parade for shy children",
        "problem": "the brass trumpet sounded too loudly near the sleeping houses",
        "stake": "The children wanted to watch, but they covered their ears and hid indoors",
        "temptation": "play even louder so everyone would notice the parade",
        "clue": "the children smiled when the drum was tapped with a soft cloth",
        "action": "They wrapped the instruments gently and invited the children to choose the parade's quiet rhythm",
        "twist": "the children had been waiting to hear a parade made for their little brother's nap",
        "sharing": "The musicians played softly, and the children carried ribbons instead of noisy flags",
        "lesson": "a celebration can be joyful without making everyone share the same kind of joy",
        "ending": "ribbons floated down the street while a sleeping baby dreamed through the gentlest parade",
        "question": "How did the musicians make the parade quieter?",
        "answer": "They wrapped the instruments with soft cloth and played a gentle rhythm chosen with the children.",
    },
]

OPENINGS = [
    "Morning light painted the rooftops gold",
    "A fresh breeze skipped along the road",
    "The town woke to bells and bright ribbons",
    "Sunshine spilled across the square",
    "The river glittered beside the waiting crowd",
    "At first light, boots and shoes gathered in a cheerful line",
]

DIALOGUE_OPENERS = [
    ("'We can hurry,' said {sailor}, 'but we should not leave anyone behind.'",
     "'Then let us listen first,' said {friend}."),
    ("'I want this parade to be perfect,' said {sailor}.",
     "'Perfect can still make room for kindness,' replied {friend}."),
    ("'What do you notice?' asked {friend}.",
     "'I notice that the smallest clue is pointing us somewhere,' said {sailor}."),
    ("'Should we go on?' asked {sailor}.",
     "'Not until the people we came to celebrate are with us,' said {friend}."),
]

REFLECTIONS = [
    "{sailor} felt the wish to be praised grow smaller than the wish to help",
    "{sailor} took a slow breath and looked past the bright uniforms",
    "The sailor's proud thought softened when the quiet clue became clear",
    "{sailor} remembered that a parade was made of people, not only music",
]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming parade storyworld about a sailor and infantry."
    )
    parser.add_argument("--sailor", choices=SAILORS)
    parser.add_argument("--infantry-friend", choices=INFANTRY_FRIENDS)
    parser.add_argument("--parade-place", choices=PLACES)
    parser.add_argument("--banner", choices=BANNERS)
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
    sailor = args.sailor or rng.choice(SAILORS)
    friend_choices = [name for name in INFANTRY_FRIENDS if name != sailor]
    friend = args.infantry_friend or rng.choice(friend_choices)
    if sailor == friend:
        raise StoryError("The sailor and infantry friend must be different characters.")
    return StoryParams(
        sailor=sailor,
        infantry_friend=friend,
        parade_place=args.parade_place or rng.choice(PLACES),
        banner=args.banner or rng.choice(BANNERS),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    sailor = Entity(name=params.sailor, kind="sailor")
    friend = Entity(name=params.infantry_friend, kind="infantry")
    parade = Entity(name="the parade", kind="parade")
    return World(params=params, sailor=sailor, infantry_friend=friend, parade=parade)


def simulate(world: World) -> None:
    params = world.params
    sailor = world.sailor
    friend = world.infantry_friend
    arc = ARCS[params.arc]
    rng = random.Random(params.seed)

    sailor.meters["distance_to_parade"] = 0.0
    sailor.memes["pride"] = 1.0
    sailor.memes["kindness"] = 0.4
    friend.memes["patience"] = 1.0
    world.facts.update(
        {
            "place": params.parade_place,
            "banner": params.banner,
            "problem": arc["problem"],
            "clue": arc["clue"],
            "stake": arc["stake"],
            "resolved": False,
        }
    )

    opening = rng.choice(OPENINGS)
    world.say(
        f"{opening}. At {params.parade_place}, {sailor.name}, a sailor home from the sea, "
        f"stood beside {friend.name}, an infantry musician, as the parade gathered."
    )
    world.say(f"They had polished {params.banner} until it shone like a small piece of sunlight.")
    world.say(f"{arc['premise']}.")
    world.para()

    world.say(f"Then {arc['problem']}. {arc['stake']}.")
    world.say(f"For a moment, {sailor.name} wanted to {arc['temptation']}.")
    dialogue = rng.choice(DIALOGUE_OPENERS)
    world.say(dialogue[0].format(sailor=sailor.name, friend=friend.name))
    world.say(dialogue[1].format(sailor=sailor.name, friend=friend.name))
    world.say(rng.choice(REFLECTIONS).format(sailor=sailor.name, friend=friend.name))
    world.facts["temptation"] = arc["temptation"]
    sailor.memes["pride"] = 0.6
    sailor.memes["listening"] = 1.0
    world.para()

    world.say(f"{friend.name} pointed out that {arc['clue']}.")
    world.say(f"Together, they decided to act: {arc['action']}.")
    world.say(f"Then came the twist: {arc['twist']}.")
    world.say(
        f"'So this welcome belongs to more than us,' said {sailor.name}. "
        f"'Yes,' said {friend.name}. 'That is why it can reach so far.'"
    )
    friend.memes["helping"] = 1.0
    sailor.memes["kindness"] = 1.0
    world.facts["twist"] = arc["twist"]
    world.facts["solution"] = arc["action"]
    world.para()

    world.say(f"{arc['sharing']}.")
    world.say(f"{arc['lesson'].capitalize()}.")
    world.say(f"As the afternoon softened, {arc['ending']}.")
    world.facts["resolved"] = True
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]

    prompts = [
        f"Write a heartwarming parade story about sailor {params.sailor} and infantry helper {params.infantry_friend}.",
        f"Tell a child-friendly story set in {params.parade_place} with a surprising twist.",
        f"Make a gentle story about this parade problem: {arc['problem']}.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem interrupted {params.sailor}'s parade?",
            answer=f"The parade was interrupted because {arc['problem']}.",
        ),
        QAItem(
            question=f"What did {params.sailor} first want to do?",
            answer=f"{params.sailor} first wanted to {arc['temptation']}.",
        ),
        QAItem(
            question=f"What clue did {params.infantry_friend} notice?",
            answer=f"{params.infantry_friend} noticed that {arc['clue']}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {arc['twist']}.",
        ),
        QAItem(
            question=f"What did {params.sailor} learn?",
            answer=f"{params.sailor} learned that {arc['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized group of people moving together while music, flags, or other signs help celebrate something.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works and travels on a boat or ship, helping care for it and the people aboard.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers trained to travel and work on foot.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that reveals something the characters did not expect.",
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
    for entity in [world.sailor, world.infantry_friend, world.parade]:
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.name:18} ({entity.kind:9}) meters={meters} memes={memes}"
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
    domain(parade),
    role(sailor),
    role(infantry),
    feature(twist),
    value(heartwarming).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("domain", "parade"),
            asp.fact("role", "sailor"),
            asp.fact("role", "infantry"),
            asp.fact("feature", "twist"),
            asp.fact("value", "heartwarming"),
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
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story verification failed.")
            return 1
        if "parade" not in sample.story.lower():
            print("MISMATCH: parade vocabulary missing.")
            return 1
        if "sailor" not in sample.story.lower():
            print("MISMATCH: sailor vocabulary missing.")
            return 1
        if "infantry" not in sample.story.lower():
            print("MISMATCH: infantry vocabulary missing.")
            return 1

    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(
        sailor="Luna",
        infantry_friend="Mara",
        parade_place="the riverside square",
        banner="the blue harbor banner",
        arc=0,
        seed=101,
    ),
    StoryParams(
        sailor="Theo",
        infantry_friend="Jo",
        parade_place="the town garden",
        banner="the golden star banner",
        arc=2,
        seed=202,
    ),
    StoryParams(
        sailor="Pia",
        infantry_friend="Inez",
        parade_place="the old market road",
        banner="the red sunrise flag",
        arc=4,
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
        raise StoryError("The number of stories must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 30, 30):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

        if len(samples) < args.n:
            raise StoryError("Could not generate the requested number of distinct stories.")

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
