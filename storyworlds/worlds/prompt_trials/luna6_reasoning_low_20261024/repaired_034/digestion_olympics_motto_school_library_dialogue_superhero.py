#!/usr/bin/env python3
"""A small superhero storyworld about digestion, a school-library Olympics, and a motto."""

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
    hero: str = "Luna"
    partner: str = "Theo"
    place: str = "the school library"
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
    partner: Entity
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


HERO_NAMES = ["Luna", "Milo", "Tia", "Pip", "Rory", "Nia"]
PARTNER_NAMES = ["Theo", "Asha", "Bea", "Kai", "June", "Pax"]
PLACES = ["the school library", "the bright school library", "the library reading room"]

ARCS = [
    {
        "event": "the Library Olympics' digestion relay",
        "problem": "the picture cards showing how food travels through the body were scattered across the reading tables",
        "stake": "the teams could not put the journey in order before the final round",
        "clue": "a tiny arrow on each card matched the next body's stop",
        "plan": "Luna and Theo read the arrows aloud and placed each card beside the matching stop in their big paper-body map",
        "turn": "the winning clue was not speed at all: the arrows made a clear path only when the team listened to one another",
        "resolution": "They invited every team to walk the map together, from mouth to stomach and onward through the intestines.",
        "ending": "Their paper-body map stood open beside the shelves, its winding path marked by colorful cards.",
        "question": "What helped the team put the digestion cards in order?",
        "answer": "Small arrows on the cards showed which body stop came next.",
        "lesson": "careful teamwork can make a tricky path easier to follow",
        "motto": "Learn the path, lend a hand!",
    },
    {
        "event": "the Library Olympics' healthy-habit challenge",
        "problem": "the teams rushed to grab books and forgot to read the directions for their digestion model",
        "stake": "their model showed food going straight from the mouth to the feet",
        "clue": "a labeled library book showed that food passes through several organs as the body digests it",
        "plan": "Luna asked everyone to pause while Theo found a clear diagram, then they checked each model step against the book",
        "turn": "the mistake became a useful discovery when the children noticed how many different body parts help with digestion",
        "resolution": "They corrected the models and made a quiet reading station where teams could check facts before racing.",
        "ending": "The corrected models lined the library table, each one showing a careful, winding journey.",
        "question": "What did the teams use to correct their digestion models?",
        "answer": "They checked the steps against a library book's labeled diagram.",
        "lesson": "pausing to check a fact is a strong kind of courage",
        "motto": "Read, check, then charge ahead!",
    },
    {
        "event": "the Library Olympics' food-journey puzzle",
        "problem": "a gust from the open window blew the stomach and intestine labels off the paper model",
        "stake": "the teams might mix up the parts while trying to finish first",
        "clue": "the labels had different shapes that fit matching outlines on the model",
        "plan": "Luna held the paper steady while Theo matched the shapes, and the other teams took turns checking the labels",
        "turn": "the teams discovered that their different observations fit together like the shapes on the model",
        "resolution": "They fixed the labels in place and made a shared guide so nobody had to guess.",
        "ending": "The guide rested beneath the model, with every team’s notes pointing along the same path.",
        "question": "How did the children match the loose labels to the model?",
        "answer": "They matched each label's shape to the outline for the correct body part.",
        "lesson": "many careful eyes can solve a puzzle better than one hurried guess",
        "motto": "Many eyes, one wise plan!",
    },
    {
        "event": "the Library Olympics' digestion quiz",
        "problem": "Luna knew the mouth began digestion but could not remember what happened next",
        "stake": "she was tempted to guess and lead her team the wrong way",
        "clue": "Theo found a book explaining that the stomach churns food and the intestines take in useful nutrients",
        "plan": "Luna asked Theo to read the passage, then repeated the journey in her own words for the team",
        "turn": "her honest question helped everyone learn more than a quick, confident guess would have",
        "resolution": "The team used the book to make a simple quiz trail, with a question at each stop along the journey.",
        "ending": "A trail of question cards curled between the shelves, ready for the next curious reader.",
        "question": "What did Luna do when she could not remember the next step?",
        "answer": "She asked Theo to help her find the answer in a library book.",
        "lesson": "asking a question can be a brave first step toward understanding",
        "motto": "Ask, learn, and help the team!",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about a school-library Olympics and digestion."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--partner", choices=PARTNER_NAMES)
    parser.add_argument("--place", choices=PLACES)
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
    available = [name for name in PARTNER_NAMES if name != hero]
    partner = args.partner or rng.choice(available)
    place = args.place or rng.choice(PLACES)
    params = StoryParams(hero=hero, partner=partner, place=place, arc=rng.randrange(len(ARCS)))
    if hero == partner:
        raise StoryError("The superhero and partner must be different characters.")
    if place not in PLACES:
        raise StoryError(f"Choose a school-library setting from: {', '.join(PLACES)}.")
    return params


def check_params(params: StoryParams) -> None:
    if params.hero not in HERO_NAMES:
        raise StoryError(f"Unknown hero: {params.hero}.")
    if params.partner not in PARTNER_NAMES:
        raise StoryError(f"Unknown partner: {params.partner}.")
    if params.hero == params.partner:
        raise StoryError("The superhero and partner must be different characters.")
    if params.place not in PLACES:
        raise StoryError(f"Choose a school-library setting from: {', '.join(PLACES)}.")
    if not isinstance(params.arc, int) or not 0 <= params.arc < len(ARCS):
        raise StoryError(f"The story arc must be between 0 and {len(ARCS) - 1}.")


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "superhero"),
        partner=Entity(params.partner, "partner"),
    )


def simulate(world: World) -> None:
    p = world.params
    arc = ARCS[p.arc]
    hero, partner = world.hero, world.partner

    hero.meters.update(knowledge=0.25, teamwork=0.45)
    partner.meters.update(knowledge=0.55, teamwork=0.45)
    hero.memes["curiosity"] = 1.0
    hero.memes["responsibility"] = 0.4
    world.facts.update(
        event=arc["event"],
        problem=arc["problem"],
        clue=arc["clue"],
        motto=arc["motto"],
        place=p.place,
        digestion_path=["mouth", "stomach", "intestines"],
        resolved=False,
    )

    world.say(
        f"In {p.place}, {hero.name} wore a bright cape over a library-helper badge. "
        f"{hero.name} and {partner.name} were ready for {arc['event']}."
    )
    world.say(
        f"The teams had to learn how digestion works while keeping the library quiet enough for readers."
    )
    world.say(f"Then {arc['problem']}. {arc['stake'].capitalize()}.")
    world.say(
        f"{hero.name}'s superhero boots were ready to dash, but a fast guess could make the mix-up worse."
    )
    world.para()

    if p.arc == 3:
        world.say(f'{hero.name} whispered, "I know the mouth starts digestion, but what comes next?"')
        world.say(f'{partner.name} replied, "Let’s find out in a book instead of guessing."')
        world.say(f'"Good idea," said {hero.name}. "I’ll share what we learn with everyone."')
    else:
        world.say(f'{hero.name} asked, "Should we race to fix it before we understand the clues?"')
        world.say(f'{partner.name} answered, "Let’s look closely first. The book and the cards can help us."')
        world.say(f'"You’re right," said {hero.name}. "I’ll use my super-speed to help, not to skip the thinking."')
    world.say(f"{arc['clue'].capitalize()}.")
    world.say(f"{arc['plan']}.")
    world.say(f"That changed the plan: the team slowed down, checked the evidence, and worked together.")
    world.say(f"Then came the surprise: {arc['turn']}.")
    hero.meters["knowledge"] = 0.9
    hero.meters["teamwork"] = 0.95
    hero.memes["responsibility"] = 1.0
    hero.memes["confidence"] = 0.8
    partner.meters["teamwork"] = 0.95
    world.facts["solution"] = arc["plan"]
    world.facts["turn"] = arc["turn"]
    world.facts["resolved"] = True
    world.para()

    world.say(f'Together, they called out the Library Olympics motto: "{arc["motto"]}"')
    world.say(arc["resolution"])
    world.say(
        f"{hero.name} learned that {arc['lesson']}. "
        f"{arc['ending']}"
    )
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    check_params(params)
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a child-friendly superhero story about {params.hero} in {params.place}.",
        f"Include a Library Olympics challenge about digestion and the motto: {arc['motto']}",
        "Use spoken dialogue that helps the characters learn and change their plan.",
    ]
    story_qa = [
        QAItem(
            question="What challenge did the Library Olympics team face?",
            answer=f"The team faced this problem: {arc['problem']}.",
        ),
        QAItem(
            question="What clue helped the team decide what to do?",
            answer=f"The team noticed that {arc['clue']}.",
        ),
        QAItem(
            question=f"What did {params.hero} learn about working with others?",
            answer=f"{params.hero} learned that {arc['lesson']}.",
        ),
        QAItem(
            question="What motto did the team use?",
            answer=f"The team's motto was “{arc['motto']}”",
        ),
        QAItem(
            question="Which organs are part of the digestion journey in this story?",
            answer="The food journey begins in the mouth, continues to the stomach, and then goes through the intestines.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is digestion?",
            answer="Digestion is how the body breaks food down so it can use the nutrients.",
        ),
        QAItem(
            question="What does the stomach do during digestion?",
            answer="The stomach churns food and mixes it with digestive juices.",
        ),
        QAItem(
            question="Why do libraries have quiet reading areas?",
            answer="Quiet reading areas help people concentrate on books and give one another space to learn.",
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
    for entity in (world.hero, world.partner):
        lines.append(
            f"  {entity.name} ({entity.kind}) meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_arc/1.
#show valid_story/0.
valid_arc(A) :- arc(A), clue(A), plan(A), turn(A), resolution(A), motto(A).
valid_story :- domain(digestion_olympics), setting(school_library),
               feature(dialogue), style(superhero_story), arc(A), valid_arc(A).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("domain", "digestion_olympics"),
        asp.fact("setting", "school_library"),
        asp.fact("feature", "dialogue"),
        asp.fact("style", "superhero_story"),
    ]
    for i, arc in enumerate(ARCS):
        facts.extend(
            [
                asp.fact("arc", i),
                asp.fact("clue", i),
                asp.fact("plan", i),
                asp.fact("turn", i),
                asp.fact("resolution", i),
                asp.fact("motto", i),
            ]
        )
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


CURATED = [
    StoryParams(hero="Luna", partner="Theo", place="the school library", arc=0, seed=101),
    StoryParams(hero="Milo", partner="Asha", place="the bright school library", arc=1, seed=202),
    StoryParams(hero="Tia", partner="Kai", place="the library reading room", arc=2, seed=303),
    StoryParams(hero="Rory", partner="June", place="the school library", arc=3, seed=404),
]


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/0. #show valid_arc/1."))
    expected_arcs = [(i,) for i in range(len(ARCS))]
    actual_arcs = sorted(asp.atoms(model, "valid_arc"))
    if asp.atoms(model, "valid_story") != [()] or actual_arcs != expected_arcs:
        print("MISMATCH: ASP and Python registries disagree.")
        return 1
    try:
        for params in CURATED:
            check_params(params)
            sample = generate(params)
            if not sample.story or not sample.world.facts["resolved"]:
                print("MISMATCH: a generated story did not resolve.")
                return 1
    except StoryError as exc:
        print(f"MISMATCH: Python reasonableness gate failed: {exc}")
        return 1
    try:
        check_params(StoryParams(hero="Luna", partner="Luna"))
    except StoryError:
        pass
    else:
        print("MISMATCH: Python reasonableness gate accepted duplicate characters.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


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
    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")
    if args.show_asp:
        print(asp_program("#show valid_story/0. #show valid_arc/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_story/0. #show valid_arc/1."))
        print(asp.atoms(model, "valid_story"))
        print(asp.atoms(model, "valid_arc"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
    try:
        main()
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        sys.exit(2)
