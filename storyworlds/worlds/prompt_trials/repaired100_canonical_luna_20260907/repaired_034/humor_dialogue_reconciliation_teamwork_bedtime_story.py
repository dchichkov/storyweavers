#!/usr/bin/env python3
"""
A gentle bedtime storyworld about Luna, a moonlit mix-up, and teamwork.

The story uses humor, dialogue, reconciliation, and teamwork. A small simulated
world records what each character knows, feels, and does before the quiet ending.
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
    place: str = "the little hill"
    object_name: str = "the sleepy lantern"
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
    lantern: Entity
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


HERO_NAMES = ["Luna", "Mira", "Nell", "Ari", "Wren"]
COMPANION_NAMES = ["Pip", "Toby", "Moss", "Bram", "Dottie"]
PLACES = ["the little hill", "the moon garden", "the quiet porch"]
OBJECTS = ["the sleepy lantern", "the starry blanket", "the bell-shaped pillow"]

ARCS = [
    {
        "premise": "Luna and Pip were getting ready for the village's bedtime picnic",
        "problem": "the sleepy lantern rolled under the old bench",
        "stake": "Without its warm glow, nobody could find the path home",
        "funny": "Pip crawled after it and came out wearing the lantern like a hat",
        "clue": "the lantern chimed whenever someone hummed a lullaby",
        "action": "Luna hummed softly while Pip placed cushions in a careful trail",
        "misunderstanding": "Luna thought Pip had pushed the lantern away on purpose",
        "reconciliation": "Pip explained that his sneeze had startled it, and Luna apologized for blaming him",
        "lesson": "a kind question can turn a mistake into a shared plan",
        "ending": "the lantern glowed beside the path while sleepy neighbors followed its golden puddle of light",
        "question": "Why did Luna and Pip need the lantern?",
        "answer": "They needed the lantern to light the path so the neighbors could find their way home.",
    },
    {
        "premise": "Luna and Pip built a tiny pillow fort for a quiet bedtime story",
        "problem": "the fort's tallest cushion kept leaning toward the teapot",
        "stake": "The whole cozy roof might tumble before the story began",
        "funny": "Pip saluted the cushion and called it Captain Flop",
        "clue": "the cushion stood straight whenever both friends held its corners",
        "action": "They counted to three and tied a soft scarf around the two strongest chairs",
        "misunderstanding": "Pip thought Luna was laughing at his building skills",
        "reconciliation": "Luna said she was laughing at Captain Flop's name, and Pip laughed with her",
        "lesson": "honest words and shared hands can mend a wobbly moment",
        "ending": "the fort stood quietly as moonlight painted a silver window on its blanket roof",
        "question": "How did Luna and Pip steady the pillow fort?",
        "answer": "They held the cushion together and tied a soft scarf between the strongest chairs.",
    },
    {
        "premise": "Luna and Pip were carrying warm cocoa to the sleepy garden mice",
        "problem": "one tiny spoon vanished from the tray",
        "stake": "The cocoa could not be stirred, and the marshmallows were forming a mountain",
        "funny": "Pip found the spoon tucked behind his ear and wondered who had put it there",
        "clue": "a silver trail of cocoa led toward the basket of blankets",
        "action": "They followed the trail together and lifted each blanket one at a time",
        "misunderstanding": "Luna thought Pip had hidden the spoon while making jokes",
        "reconciliation": "Pip admitted he had forgotten placing it behind his ear, and Luna forgave him with a giggle",
        "lesson": "remembering the truth is easier when friends search without scolding",
        "ending": "the mice sipped cocoa beneath the blankets, and the spoon rested safely in its cup",
        "question": "Where was the missing spoon?",
        "answer": "The missing spoon was tucked behind Pip's ear.",
    },
    {
        "premise": "Luna and Pip were hanging paper stars above the quiet porch",
        "problem": "a string of stars became tangled around a sleepy wind chime",
        "stake": "The porch would have no twinkling ceiling for bedtime",
        "funny": "Pip blamed an invisible octopus with very tidy tentacles",
        "clue": "the knot loosened whenever the wind chime sang",
        "action": "They took turns ringing the chime and easing one paper loop at a time",
        "misunderstanding": "Luna believed Pip was pulling the string too fast",
        "reconciliation": "Pip slowed down, Luna thanked him, and they agreed to listen to the chime together",
        "lesson": "patience makes teamwork feel lighter",
        "ending": "the stars floated overhead while the wind chime whispered one last goodnight",
        "question": "What helped loosen the tangled stars?",
        "answer": "The wind chime's gentle sound helped them loosen one paper loop at a time.",
    },
]

OPENINGS = [
    "The evening sky wore a lavender shawl",
    "Moonlight slipped softly across the sleeping roofs",
    "The first star blinked above the quiet houses",
    "A warm breeze curled through the garden",
    "The day folded itself into a calm blue blanket",
]

DIALOGUES = [
    ("Luna said, 'Let us look together.'", "Pip replied, 'Together is better than my usual plan: asking a potato.'"),
    ("Luna asked, 'Did you mean to do that?'", "Pip said, 'I meant to do something. The details are still arriving.'"),
    ("Luna whispered, 'I was worried.'", "Pip answered, 'I was worried too, but I tried to look brave like a very small king.'"),
    ("Luna said, 'Tell me what happened.'", "Pip replied, 'I will, though the story contains one sneeze and zero heroic capes.'"),
]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A bedtime storyworld about Luna, humor, reconciliation, and teamwork."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--companion", choices=COMPANION_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
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
    possible = [name for name in COMPANION_NAMES if name != hero]
    companion = args.companion or rng.choice(possible)
    if hero == companion:
        raise StoryError("The hero and companion must be different characters.")
    return StoryParams(
        hero=hero,
        companion=companion,
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "hero"),
        companion=Entity(params.companion, "companion"),
        lantern=Entity(params.object_name, "object"),
    )


def simulate(world: World) -> None:
    params = world.params
    arc = ARCS[params.arc]
    rng = random.Random(params.seed)

    hero = world.hero
    companion = world.companion

    hero.memes["care"] = 1.0
    hero.memes["worry"] = 0.7
    companion.memes["humor"] = 1.0
    companion.memes["friendship"] = 0.8

    world.facts.update(
        {
            "place": params.place,
            "object": params.object_name,
            "problem": arc["problem"],
            "clue": arc["clue"],
            "resolved": False,
        }
    )

    world.say(
        f"{rng.choice(OPENINGS)}. On {params.place}, {hero.name} and {companion.name} "
        f"were preparing for bedtime."
    )
    world.say(f"{arc['premise']}. The evening was peaceful, except that {arc['problem']}.")
    world.para()

    world.say(f"{arc['stake']}. {companion.name} tried to help.")
    world.say(f"{arc['funny']}.")
    first, second = rng.choice(DIALOGUES)
    world.say(f"{first} {second}")
    world.facts["humor"] = arc["funny"]
    world.facts["tension"] = "The friends misunderstood one another while trying to help."
    world.para()

    world.say(f"Then {hero.name} noticed that {arc['clue']}.")
    world.say(f"{hero.name} asked, 'Can we try one careful step at a time?'")
    world.say(f"{companion.name} answered, 'Yes. I can be careful, even if my elbows have other plans.'")
    world.say(f"Together, they {arc['action'].lower()}.")
    hero.memes["trust"] = 1.0
    companion.memes["teamwork"] = 1.0
    world.facts["solution"] = arc["action"]

    world.para()
    world.say(f"For a moment, they still felt cross. {arc['misunderstanding']}.")
    world.say(f"At last, {arc['reconciliation']}.")
    world.say(f"{hero.name} said, 'I am sorry I guessed instead of asking.'")
    world.say(f"{companion.name} replied, 'I am sorry I joked instead of explaining.'")
    world.say("They shared a small hug, which made the nearby blanket puff up like a sleepy cloud.")
    hero.memes["worry"] = 0.0
    hero.memes["forgiveness"] = 1.0
    companion.memes["embarrassment"] = 0.0
    companion.memes["reconciliation"] = 1.0
    world.facts["reconciled"] = True

    world.para()
    world.say(f"They finished the work side by side. {arc['lesson'].capitalize()}.")
    world.say(f"As the last crickets hummed, {arc['ending']}.")
    world.facts["resolved"] = True
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]

    prompts = [
        f"Write a gentle bedtime story about {params.hero} and {params.companion} solving a problem through teamwork.",
        f"Include humorous dialogue and a reconciliation between {params.hero} and {params.companion}.",
        f"End with a quiet bedtime image at {params.place}.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.companion} face?",
            answer=f"They faced this problem: {arc['problem']}.",
        ),
        QAItem(
            question=f"What humorous thing happened to {params.companion}?",
            answer=f"{params.companion} made everyone smile when {arc['funny'].lower()}.",
        ),
        QAItem(
            question="What clue helped them solve the problem?",
            answer=f"The clue was that {arc['clue']}.",
        ),
        QAItem(
            question="How did the friends reconcile?",
            answer=f"They reconciled when {arc['reconciliation']}. They also apologized to each other.",
        ),
        QAItem(
            question="What did teamwork change?",
            answer=f"Teamwork helped them {arc['action'].lower()}, so the bedtime plan could succeed.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended peacefully: {arc['ending']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people combine their effort and ideas to solve a problem together.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, apologizing, and forgiving.",
        ),
        QAItem(
            question="Why can humor help friends?",
            answer="Gentle humor can ease worry and help friends feel close, as long as it does not hurt anyone's feelings.",
        ),
        QAItem(
            question="What makes a bedtime story feel peaceful?",
            answer="A bedtime story feels peaceful when its danger is resolved and it ends with warmth, safety, and rest.",
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
    for entity in [world.hero, world.companion, world.lantern]:
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.name:18} ({entity.kind:10}) meters={meters} memes={memes}"
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
    feature(dialogue),
    feature(reconciliation),
    feature(teamwork),
    feature(humor),
    style(bedtime_story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("domain", "bedtime_story"),
        asp.fact("feature", "dialogue"),
        asp.fact("feature", "reconciliation"),
        asp.fact("feature", "teamwork"),
        asp.fact("feature", "humor"),
        asp.fact("style", "bedtime_story"),
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
        if not sample.story.strip():
            print("MISMATCH: generated story is empty.")
            return 1
        if params.hero not in sample.story or params.companion not in sample.story:
            print("MISMATCH: generated story omitted its characters.")
            return 1
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated world did not resolve.")
            return 1

    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(
        hero="Luna",
        companion="Pip",
        place="the little hill",
        object_name="the sleepy lantern",
        arc=0,
        seed=101,
    ),
    StoryParams(
        hero="Mira",
        companion="Toby",
        place="the moon garden",
        object_name="the starry blanket",
        arc=1,
        seed=202,
    ),
    StoryParams(
        hero="Nell",
        companion="Dottie",
        place="the quiet porch",
        object_name="the bell-shaped pillow",
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
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

        if not samples:
            raise StoryError("No unique stories could be generated.")

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
