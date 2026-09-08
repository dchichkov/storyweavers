#!/usr/bin/env python3
"""
A small superhero storyworld about a quest, an inner monologue, a grizzly, and a happy ending.

The domain is built around a tiny city rescue in which a young hero must
terminate a risky problem, scour the area for clues, and finish with a clear,
hopeful change in the world state.
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
    hero: str = "Nova"
    sidekick: str = "Zip"
    city: str = "Maple Harbor"
    place: str = "the riverside park"
    villain: str = "Grizzle"
    object: str = "a glowing kite"
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
    sidekick: Entity
    villain: Entity
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


HERO_NAMES = ["Nova", "Spark", "Comet", "Mira", "Atlas", "Juno"]
SIDEKICK_NAMES = ["Zip", "Beam", "Pip", "Echo", "Dot", "Bolt"]
CITIES = ["Maple Harbor", "Sunset City", "Clover Bay", "Rivergate"]
PLACES = ["the riverside park", "the old clock tower", "the museum roof", "the harbor bridge"]
VILLAINS = ["Grizzle", "Captain Bristle", "Mr. Thud", "Clawline"]
OBJECTS = ["a glowing kite", "a silver bracelet", "a bright battery", "a rescue whistle"]

SCENES = [
    {
        "premise": "A grizzly-sized shadow had been stealing picnic baskets and hiding them under the bridge",
        "problem": "the stolen baskets were left open, and the park animals were getting blamed",
        "stake": "if the hero did not terminate the theft, the whole city would close the park",
        "quest": "find the bridge hideout, recover the baskets, and clear the animals' names",
        "inner": "I can hurry and smash the first shadow I see, or I can scour for the real trail.",
        "dialogue": ("Zip", "Maybe the answer is not under the biggest paw print."),
        "turn": "the trail led not to a monster den, but to a broken scooter with muddy wheels",
        "reveal": "the supposed grizzly was only a giant puppet pulled by strings from the lampposts",
        "resolution": "they cut the strings, returned every basket, and gave the puppet to the art club",
        "ending": "the park lights came back on, and the squirrels danced beside a picnic quilt full of apples",
        "qa": "Why did the hero scour the bridge path?",
        "qa_answer": "The hero scoured the bridge path to find the real thief and clear the park animals' names.",
    },
    {
        "premise": "A grizzly helmeted robot rolled through the street, scooping up sidewalk chalk drawings",
        "problem": "children thought their pictures had vanished forever",
        "stake": "if the hero failed to terminate the robot's rush, the parade road would be blocked",
        "quest": "follow the robot, find who controlled it, and save the chalk mural",
        "inner": "If I jump first, I may miss the clue. I need to scour the wheels, the wires, and the sky.",
        "dialogue": ("Nova", "Zip, do you hear the robot's hum change near the bakery?"),
        "turn": "the hum changed because the robot stopped to charge under a loose wire",
        "reveal": "a sleepy inventor had set it to gather chalk for a bigger mural but forgot to ask the kids",
        "resolution": "the hero helped the inventor stop the machine and turned the gathered chalk into a giant community picture",
        "ending": "by sunset, a painted dragon and a smiling sun stretched across the street in bright chalk dust",
        "qa": "What did the inventor forget to do?",
        "qa_answer": "The inventor forgot to ask the children before sending the robot to gather their chalk.",
    },
    {
        "premise": "A grizzly storm cloud hovered over the clock tower and kept making the bells ring off time",
        "problem": "the city train used the bells to know when to leave",
        "stake": "if the hero could not terminate the false alarm, the train would miss its passengers",
        "quest": "climb the tower, scour the gears, and fix the clock",
        "inner": "The cloud looks mean, but mean-looking things can hide a simple problem.",
        "dialogue": ("Beam", "Should we chase the cloud or the bells?"),
        "turn": "the hero found a stuck bird whistle tangled in the tower gear",
        "reveal": "the cloud was only copying the whistle because wind was pushing it through the broken window",
        "resolution": "they removed the whistle, mended the window, and set the clock straight again",
        "ending": "the train rolled out on time while the cloud drifted away into a soft, harmless gray",
        "qa": "What caused the bells to ring wrong?",
        "qa_answer": "A stuck bird whistle and the wind made the clock ring at the wrong time.",
    },
    {
        "premise": "A grizzly-looking costume contest had started at the city fair",
        "problem": "one costume had jammed the stage door shut from the inside",
        "stake": "if the hero did not terminate the jam, the prize show would end in tears",
        "quest": "scour the fair, find the trapped performer, and open the door safely",
        "inner": "I know that bulky costume. Someone inside may be frightened, not fierce.",
        "dialogue": ("Nova", "Who is stuck in there?"),
        "turn": "a tiny voice answered that the zipper was caught on a ribbon spool",
        "reveal": "the grizzly costume belonged to a shy child trying to surprise her mother",
        "resolution": "the hero freed the zipper, and the child bowed to a cheering crowd",
        "ending": "the winner's ribbon went to the child, and the mother hugged her beside a tower of lemonade cups",
        "qa": "Who was inside the grizzly costume?",
        "qa_answer": "A shy child was inside the grizzly costume.",
    },
    {
        "premise": "Someone had painted grizzly paw prints all over the library steps",
        "problem": "everyone thought a wild animal had wandered downtown",
        "stake": "if the hero did not terminate the panic, the library would close early",
        "quest": "scour the steps, follow the paint trail, and find the prankster",
        "inner": "The prints are too neat for a real bear. I should think like a detective hero.",
        "dialogue": ("Zip", "Those paws stop at the art room window."),
        "turn": "the trail ended at a bucket of washable paint and a wet brush",
        "reveal": "the librarian's nephew had tried to make a storybook display without asking",
        "resolution": "the hero helped turn the paint into a safe poster for the reading club",
        "ending": "children lined up for picture books while the steps dried under the evening sun",
        "qa": "Why did the library almost close?",
        "qa_answer": "People were afraid a wild animal was downtown, so the library nearly closed early.",
    },
]

OPENINGS = [
    "Late afternoon sunlight flashed between the buildings",
    "A warm wind pushed banners above the sidewalks",
    "The city hummed like a tuning fork before the first alarm",
    "Clouds thinned over the skyline as the hero raced across a rooftop",
    "Neon signs blinked on while pigeons scattered from the square",
    "The streetlights had just clicked awake when trouble began",
]

INNER_LEADS = [
    "Inside, {hero} kept a steady thought like a hidden flashlight",
    "For one breath, {hero} listened to the inner monologue that every good hero needs",
    "{hero}'s mind ran ahead, then circled back to the careful plan",
    "The loud world faded, and a brave thought spoke softly inside {hero}",
    "A smart worry nudged {hero} to slow down and look again",
]

DECISIONS = [
    "'If I rush at the biggest shadow, I may miss the real trail. I should scour the whole scene first.'",
    "'A hero can be fast and still be careful. I'll terminate the danger after I know its source.'",
    "'This looks fierce, but the clues matter more than the size of the noise.'",
    "'I do not need the first answer. I need the true answer.'",
    "'A strong leap is good, but a smarter search can save the day.'",
]

CODAS = [
    "{hero} smiled as the city cheered, because a happy ending feels best when everyone is safe.",
    "By evening, the streets were calm, and {hero} knew the real victory was peace, not applause.",
    "The hero tucked the lesson away: look closely, help kindly, and let the city breathe again.",
    "The sun slid low, and the rescue left behind a bright, hopeful hush.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld with a grizzly clue, an inner monologue, and a quest.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--object", choices=OBJECTS)
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
    sidekick = args.sidekick or rng.choice([x for x in SIDEKICK_NAMES if x != hero])
    city = args.city or rng.choice(CITIES)
    place = args.place or rng.choice(PLACES)
    villain = args.villain or rng.choice(VILLAINS)
    obj = args.object or rng.choice(OBJECTS)
    if hero == sidekick:
        raise StoryError("The hero and sidekick must be different characters.")
    return StoryParams(hero=hero, sidekick=sidekick, city=city, place=place, villain=villain, object=obj, seed=None)


def build_world(params: StoryParams) -> World:
    hero = Entity(name=params.hero, kind="hero")
    sidekick = Entity(name=params.sidekick, kind="sidekick")
    villain = Entity(name=params.villain, kind="villain")
    return World(params=params, hero=hero, sidekick=sidekick, villain=villain)


def choose(rng: random.Random, options: list[str], **values: str) -> str:
    return rng.choice(options).format(**values)


def simulate(world: World) -> None:
    p = world.params
    rng = random.Random(p.seed)
    scene = rng.choice(SCENES)
    opening = choose(rng, OPENINGS, hero=p.hero, sidekick=p.sidekick)
    inner = choose(rng, INNER_LEADS, hero=p.hero, sidekick=p.sidekick)
    decision = choose(rng, DECISIONS, hero=p.hero, sidekick=p.sidekick)
    coda = choose(rng, CODAS, hero=p.hero, sidekick=p.sidekick)

    world.facts["city"] = p.city
    world.facts["place"] = p.place
    world.facts["villain"] = p.villain
    world.facts["object"] = p.object
    world.facts["quest"] = scene["quest"]
    world.facts["ending"] = scene["ending"]

    world.say(f"{opening}, and {p.hero} landed near {p.place} in {p.city}.")
    world.say(f"{p.hero} and {p.sidekick} were on a quest: {scene['quest']}.")
    world.say(f"{scene['premise']}.")
    world.para()

    world.say(f"{scene['problem']}; {scene['stake']}.")
    world.say(f"{inner}. {p.hero} thought, {decision}")
    world.say(f"{p.sidekick} said, 'We can help if we search together.'")
    world.say(f"{p.hero} answered, 'Then let's scour every clue before we leap.'")
    world.facts["inner_monologue"] = True

    world.para()
    world.say(f"Together they {scene['turn']}.")
    world.say(f"That is when the truth showed up: {scene['reveal']}.")
    world.say(f"{p.sidekick} laughed, 'So the grizzly part was only a costume of trouble.'")
    world.say(f"{p.hero} nodded and said, 'Good. Then we can terminate the danger without hurting anyone.'")
    world.facts["twist"] = scene["reveal"]

    world.para()
    world.say(f"They finished the quest by {scene['resolution']}.")
    world.say(f"{coda} {scene['ending']}.")
    world.say(f"{p.sidekick} cheered, 'Happy ending!'")
    world.say(f"{p.hero} grinned, 'And we did it by looking closely and helping kindly.'")
    world.facts["resolved"] = True
    world.facts["happy_ending"] = True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    prompts = [
        f"Write a superhero story about {params.hero} in {params.city} who must terminate a grizzly problem.",
        f"Tell a child-friendly quest story where {params.hero} uses an inner monologue to scour for clues.",
        f"Make a happy-ending rescue tale set at {params.place} with {params.sidekick} helping {params.hero}.",
    ]
    story_qa = [
        QAItem(
            question=f"What quest was {params.hero} trying to finish?",
            answer=f"{params.hero} was trying to {world.facts['quest']}.",
        ),
        QAItem(
            question=f"What did {params.hero}'s inner monologue warn about?",
            answer=f"{params.hero}'s inner monologue warned that rushing could make the hero miss the real clue.",
        ),
        QAItem(
            question=f"How did {params.hero} and {params.sidekick} solve the problem?",
            answer=f"They scoured the scene together, found the true cause, and worked as a team to fix it.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The ending was happy because the danger was terminated, the misunderstanding was cleared up, and everyone was safe.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or mission that characters try to complete.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thoughts, like quiet words inside the mind.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the story finishes with safety, relief, or joy after the problem is solved.",
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
    for ent in [world.hero, world.sidekick, world.villain]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.name:10} ({ent.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
valid(story) :- quest(quest), feature(inner_monologue), feature(happy_ending), feature(scour), feature(terminate), feature(grizzly).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "happy_ending"),
            asp.fact("feature", "terminate"),
            asp.fact("feature", "grizzly"),
            asp.fact("feature", "scour"),
            asp.fact("style", "superhero_story"),
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
    StoryParams(hero="Nova", sidekick="Zip", city="Maple Harbor", place="the riverside park", villain="Grizzle", object="a glowing kite", seed=101),
    StoryParams(hero="Spark", sidekick="Beam", city="Sunset City", place="the old clock tower", villain="Captain Bristle", object="a silver bracelet", seed=202),
    StoryParams(hero="Mira", sidekick="Pip", city="Clover Bay", place="the museum roof", villain="Mr. Thud", object="a bright battery", seed=303),
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
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
