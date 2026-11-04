#!/usr/bin/env python3
"""
A small superhero storyworld about digestion, teamwork, and the Digestion Olympics
in a school library.

Young heroes use a library book, careful observation, and a team motto to solve
problems at a hands-on display. The food models are made of paper; nobody eats
or pushes anything through a real person.
"""

from __future__ import annotations

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
    hero: str = "Maya"
    companion: str = "Leo"
    place: str = "the school library"
    motto: str = "Read the clue, then help it through!"
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
    display: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


HERO_NAMES = ["Maya", "Leo", "Pip", "Nia", "Jude", "Tess"]
COMPANION_NAMES = ["Leo", "Nia", "Pip", "Tess", "Jude", "Maya"]
MOTTOS = [
    "Read the clue, then help it through!",
    "Small steps make a strong team!",
    "Follow the path; don't rush!",
    "Every part has a helping job!",
]

ARCS = [
    {
        "id": "route_cards",
        "problem": "a desk fan fluttered the paper food-path cards across the library floor",
        "stake": "Without the cards, the teams could not show the route food takes through the body",
        "temptation": "grab every card at once and guess where they belonged",
        "dialogue_question": "Which card should we find first?",
        "dialogue_answer": "Let's check the book's diagram. Food starts in the mouth, then travels down the esophagus.",
        "clue": "the open digestion book showed the mouth first, followed by the esophagus and stomach",
        "action": "Maya and Leo followed the book's arrows and placed the cards in order, one at a time",
        "twist": "the fan had blown the last card beneath the book, where its picture of the large intestine had kept it flat",
        "lesson": "a clear clue can turn a confusing scramble into a path everyone can follow",
        "ending": "the finished paper path curled neatly across the table, from a smiling mouth to a tidy final card",
        "question": "What helped Maya and Leo put the food-path cards in order?",
        "answer": "Maya and Leo used the arrows in the digestion book to put the cards in order, beginning with the mouth.",
        "world_question": "What is the first place food goes in the digestive system?",
        "world_answer": "Digestion begins in the mouth, where chewing breaks food into smaller pieces.",
        "safety": "paper_cards",
    },
    {
        "id": "esophagus_tunnel",
        "problem": "the paper food model stopped halfway through the display's folded esophagus tube",
        "stake": "The next team was waiting to learn how food travels toward the stomach",
        "temptation": "poke the model through with a ruler",
        "dialogue_question": "Should I push it through?",
        "dialogue_answer": "Let's not force it. The tube is folded; we can open the paper model and see why it stopped.",
        "clue": "a crease had pinched the paper tube shut, even though the model was only a classroom prop",
        "action": "They opened the paper fold gently, then guided the model along the clear path toward the stomach picture",
        "twist": "when the crease opened, a tiny arrow printed inside the fold showed exactly which way the model should travel",
        "lesson": "checking how something works is wiser than trying to force it",
        "ending": "the paper model rested beside the stomach picture, and the opened tube showed its little arrow",
        "question": "Why did the paper food model stop in the esophagus tube?",
        "answer": "A fold pinched the paper tube shut, so Maya and Leo opened the classroom model instead of forcing the paper through.",
        "world_question": "What does the esophagus do?",
        "world_answer": "The esophagus is a tube that carries swallowed food from the mouth toward the stomach.",
        "safety": "gentle_paper_model",
    },
    {
        "id": "nutrient_tokens",
        "problem": "bright nutrient tokens had slipped off the small-intestine station's paper path",
        "stake": "The visitors might miss how the body takes nutrients from digested food",
        "temptation": "sweep the tokens into a pile and call the station finished",
        "dialogue_question": "Where do the nutrients go on our display?",
        "dialogue_answer": "The book says the small intestine absorbs nutrients. Let's follow its winding path and look carefully.",
        "clue": "the diagram showed the small intestine as a long, winding path, with nutrients moving from it into the body",
        "action": "They traced the paper path together and used a paper arrow to return each token to its marked spot",
        "twist": "the missing tokens had caught on the clear sleeve covering the diagram, right beside the arrows showing absorption",
        "lesson": "a patient search can help everyone see what a small detail means",
        "ending": "the bright tokens lined the winding paper intestine, with each arrow pointing toward the body",
        "question": "Where had the nutrient tokens slipped?",
        "answer": "The nutrient tokens had caught on the clear sleeve beside the diagram's arrows.",
        "world_question": "What happens to many nutrients in the small intestine?",
        "world_answer": "The small intestine absorbs many nutrients from digested food so the body can use them.",
        "safety": "paper_tokens",
    },
    {
        "id": "water_drops",
        "problem": "the large-intestine station's blue paper water drops were mixed with its other picture cards",
        "stake": "The display no longer showed one of the large intestine's helpful jobs",
        "temptation": "put all the blue drops in the waste basket picture",
        "dialogue_question": "Do all these blue drops belong at the end?",
        "dialogue_answer": "Let's check the library book. The large intestine absorbs water, so these drops need a different place.",
        "clue": "the book explained that the large intestine absorbs water as the remaining material moves along",
        "action": "They sorted the paper pictures by following the book's arrows and placed the water drops beside the large-intestine card",
        "twist": "one blue drop had been covering the station's small water-absorption label",
        "lesson": "asking a question before sorting can reveal the job hidden in a detail",
        "ending": "the blue drops sat beside their label, and the completed station was ready for the next team",
        "question": "What job of the large intestine did the paper drops help explain?",
        "answer": "The drops helped show that the large intestine absorbs water as the remaining material moves along.",
        "world_question": "What is one job of the large intestine?",
        "world_answer": "The large intestine absorbs water from the remaining material before waste leaves the body.",
        "safety": "paper_picture_cards",
    },
]

OPENINGS = [
    "Rain tapped the tall library windows while a red cape swished past the shelves",
    "A bright banner hung between the library bookcases, and capes fluttered beneath it",
    "The school library smelled of paper and pencil shavings on the morning of the big event",
    "Sunlight made a bright square on the library rug beside the Digestion Olympics sign",
    "Near the quiet-reading corner, a hand-drawn banner announced the Digestion Olympics",
]

REACTIONS = [
    "Leo grinned as the answer clicked into place",
    "Maya's shoulders relaxed, and Leo gave a happy little nod",
    "The two young heroes exchanged a relieved smile",
    "A nearby team leaned closer to see what they had noticed",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about digestion, a school-library Olympics, and a team motto."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--companion", choices=COMPANION_NAMES)
    parser.add_argument("--motto", choices=MOTTOS)
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
    companion_choices = [name for name in COMPANION_NAMES if name != hero]
    companion = args.companion or rng.choice(companion_choices)
    if hero == companion:
        raise StoryError("The hero and companion must be different characters.")
    return StoryParams(
        hero=hero,
        companion=companion,
        place="the school library",
        motto=args.motto or rng.choice(MOTTOS),
        arc=rng.randrange(len(ARCS)),
    )


def choose(rng: random.Random, options: list[str]) -> str:
    return rng.choice(options)


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(name=params.hero, kind="young_superhero"),
        companion=Entity(name=params.companion, kind="teammate"),
        display=Entity(name="Digestion Olympics display", kind="paper_learning_station"),
    )


def simulate(world: World) -> None:
    params = world.params
    hero = world.hero
    companion = world.companion
    display = world.display
    arc = ARCS[params.arc]
    rng = random.Random(params.seed)

    hero.meters.update({"attention": 0.35, "confidence": 0.45})
    companion.meters.update({"attention": 0.35, "confidence": 0.45})
    display.meters.update({"order": 0.35, "problem_pressure": 0.65})
    hero.memes.update({"curiosity": 1.0, "helpfulness": 0.7})
    companion.memes.update({"curiosity": 0.7, "team_trust": 0.6})

    world.facts.update(
        {
            "arc_id": arc["id"],
            "problem": arc["problem"],
            "clue": arc["clue"],
            "solution": arc["action"],
            "lesson": arc["lesson"],
            "motto": params.motto,
            "setting": params.place,
            "resolved": False,
        }
    )

    opening = choose(rng, OPENINGS)
    world.say(
        f"{opening}. {hero.name} and {companion.name} were helping at the Digestion Olympics, "
        f"a library event where teams used paper models to learn how the digestive system works."
    )
    world.say(
        f"They wore homemade superhero capes, and their team motto was, “{params.motto}” "
        f"At their station, {arc['problem']}."
    )
    world.para()

    world.say(f"{arc['stake']}. For one hurried moment, {hero.name} wanted to {arc['temptation']}.")
    world.say(
        f"“{arc['dialogue_question']}” {hero.name} asked. "
        f"“{arc['dialogue_answer']}” {companion.name} replied."
    )
    hero.meters["attention"] = 0.8
    companion.meters["attention"] = 0.85
    companion.memes["knowledge"] = 1.0
    hero.memes["has_a_plan"] = 1.0
    world.facts["risky_idea"] = arc["temptation"]
    world.facts["dialogue_changed_plan"] = True

    world.para()
    world.say(
        f"They repeated their motto together—“{params.motto}”—and checked the library book before touching the display."
    )
    world.say(f"There was the clue: {arc['clue']}.")
    world.say(f"{arc['action']}.")
    world.say(f"Then came the surprise: {arc['twist']}. {choose(rng, REACTIONS)}.")
    hero.meters["confidence"] = 0.9
    companion.meters["confidence"] = 0.9
    display.meters["order"] = 1.0
    display.meters["problem_pressure"] = 0.0
    hero.memes["teamwork"] = 1.0
    companion.memes["teamwork"] = 1.0
    world.facts["twist"] = arc["twist"]
    world.facts["resolved"] = True
    world.facts["ending_image"] = arc["ending"]

    world.para()
    world.say(
        f"“Our motto helped us slow down and check,” {hero.name} said. "
        f"“And your question helped us notice what the book was teaching,” {companion.name} answered."
    )
    world.say(
        f"The next team gathered around the ready display, while the two caped helpers made room for everyone."
    )
    world.say(f"{arc['ending']}. {hero.name} felt like a real hero—not because of a superpower, but because the team had learned together.")


def lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.companion:
        raise StoryError("The hero and companion must be different characters.")
    if params.place != "the school library":
        raise StoryError("The Digestion Olympics story takes place in the school library.")
    if params.motto not in MOTTOS:
        raise StoryError("Choose a team motto from the available motto registry.")
    if not 0 <= params.arc < len(ARCS):
        raise StoryError(f"The story arc must be between 0 and {len(ARCS) - 1}.")

    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a child-friendly superhero story about {params.hero} and {params.companion} at the Digestion Olympics in the school library.",
        f"Include a spoken conversation that helps {params.hero} and {params.companion} solve this problem: {arc['problem']}.",
        f"Let the heroes use their motto, “{params.motto},” and end with a clear image of what changed.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.companion} face?",
            answer=f"They faced a problem at the Digestion Olympics: {arc['problem']}.",
        ),
        QAItem(
            question=f"What did {params.companion} say that changed {params.hero}'s plan?",
            answer=f"{params.companion} said, “{arc['dialogue_answer']}” That helped {params.hero} check the book and choose a careful plan.",
        ),
        QAItem(
            question=f"What clue helped the two heroes solve the problem?",
            answer=f"The clue was that {arc['clue']}.",
        ),
        QAItem(
            question=arc["question"],
            answer=arc["answer"],
        ),
        QAItem(
            question=f"What did {params.hero} learn from the challenge?",
            answer=f"{params.hero} learned that {arc['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is digestion?",
            answer="Digestion is the process by which the body breaks food down so it can use nutrients from it.",
        ),
        QAItem(
            question="What is the Digestion Olympics in this story?",
            answer="It is a school-library learning event where teams use paper models and activities to learn about digestion.",
        ),
        QAItem(
            question="What is a motto?",
            answer="A motto is a short phrase that expresses an idea or reminder a person or team wants to follow.",
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
    for entity in [world.hero, world.companion, world.display]:
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.name:28} ({entity.kind:22}) meters={meters} memes={memes}")
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


def python_reasonable(arc: dict) -> bool:
    """The Python-side reasonableness gate mirrored by ASP_RULES."""
    return (
        arc.get("safety") in {"paper_cards", "gentle_paper_model", "paper_tokens", "paper_picture_cards"}
        and bool(arc.get("problem"))
        and bool(arc.get("clue"))
        and bool(arc.get("action"))
        and bool(arc.get("dialogue_question"))
        and bool(arc.get("dialogue_answer"))
        and bool(arc.get("ending"))
    )


ASP_RULES = r"""
valid_arc(A) :-
    arc(A),
    safe_arc(A),
    setting(school_library),
    feature(digestion),
    feature(olympics),
    feature(motto),
    feature(dialogue),
    style(superhero_story).

#show valid_arc/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("setting", "school_library"),
        asp.fact("feature", "digestion"),
        asp.fact("feature", "olympics"),
        asp.fact("feature", "motto"),
        asp.fact("feature", "dialogue"),
        asp.fact("style", "superhero_story"),
    ]
    for arc in ARCS:
        facts.append(asp.fact("arc", arc["id"]))
        if python_reasonable(arc):
            facts.append(asp.fact("safe_arc", arc["id"]))
    return "\n".join(facts)


def asp_program(show: str = "#show valid_arc/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    actual = {row[0] for row in asp.atoms(model, "valid_arc")}
    expected = {arc["id"] for arc in ARCS if python_reasonable(arc)}
    if actual != expected:
        print(f"MISMATCH: Python accepts {sorted(expected)}, ASP accepts {sorted(actual)}.")
        return 1

    for index, arc in enumerate(ARCS):
        if not python_reasonable(arc):
            print(f"MISMATCH: curated arc {arc['id']} failed the Python reasonableness gate.")
            return 1
        params = StoryParams(
            hero="Maya",
            companion="Leo",
            place="the school library",
            motto=MOTTOS[index % len(MOTTOS)],
            arc=index,
            seed=900 + index,
        )
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print(f"MISMATCH: generated story {arc['id']} did not resolve its problem.")
            return 1
        if params.motto not in sample.story or "“" not in sample.story or "”" not in sample.story:
            print(f"MISMATCH: generated story {arc['id']} is missing its motto or spoken dialogue.")
            return 1
        if arc["ending"] not in sample.story:
            print(f"MISMATCH: generated story {arc['id']} is missing its ending image.")
            return 1

    print("OK: ASP and Python accept the same arcs; every generated story has dialogue, a motto, and a resolution.")
    return 0


CURATED = [
    StoryParams(hero="Maya", companion="Leo", motto=MOTTOS[0], arc=0, seed=101),
    StoryParams(hero="Pip", companion="Nia", motto=MOTTOS[1], arc=1, seed=202),
    StoryParams(hero="Jude", companion="Tess", motto=MOTTOS[2], arc=2, seed=303),
    StoryParams(hero="Tess", companion="Maya", motto=MOTTOS[3], arc=3, seed=404),
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

        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid_arc"))
        return
    if not args.all and args.n < 1:
        raise StoryError("The number of stories must be at least one.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 30, 30):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
        if len(samples) < args.n:
            raise StoryError("Could not produce the requested number of distinct stories.")

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
