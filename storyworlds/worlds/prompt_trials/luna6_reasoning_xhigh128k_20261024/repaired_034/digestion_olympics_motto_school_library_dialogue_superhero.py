#!/usr/bin/env python3
"""
A small storyworld about a superhero, the Digestion Olympics, and a school-library motto.

The characters face a problem at a science display, listen to one another, and use
library clues to make a better plan. Their contest teaches a few basic facts about
digestion through a child-friendly model.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional


_candidate = os.path.abspath(os.path.dirname(__file__))
while True:
    if os.path.isfile(os.path.join(_candidate, "results.py")):
        _storyworlds_dir = _candidate
        break
    _parent = os.path.dirname(_candidate)
    if _parent == _candidate:
        raise RuntimeError("Could not locate storyworlds/results.py.")
    _candidate = _parent

sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


SETTING = "the school library"

HERO_NAMES = ["Maya", "Theo", "Zuri", "Leo", "Asha", "Ben"]
COMPANION_NAMES = ["Theo", "Asha", "Ben", "Maya", "Ivy", "Nico"]
LIBRARIAN_NAMES = ["Ms. Lin", "Mr. Bell", "Mrs. Rivera", "Ms. Okafor"]

MOTTOS = [
    "Every step helps the whole.",
    "Small parts can do mighty work.",
    "Learn the path, then lend a hand.",
]

OPENINGS = [
    "Rain tapped on the tall windows while a quiet afternoon settled over the shelves",
    "Sunlight made bright squares on the carpet between the science and story books",
    "A soft chime marked the start of activity hour in the school library",
    "The school library smelled of paper, pencils, and the orange peel in a lunch bag",
    "Pages rustled as the library's long science table became a little arena",
]


ARCS = {
    "scattered_cards": {
        "problem": "a playful puff from the ceiling fan sent the route cards skittering across the science table",
        "stake": "Without their order, no team could show the journey food takes during digestion.",
        "temptation": "slap the cards down in a hurry and hope the order looked right",
        "dialogue": "The arrows in the open science book still show the mouth, esophagus, stomach, and intestines in order.",
        "reply": "Then let's follow the arrows, not guess. Hold the page while I match the cards.",
        "method": "{hero} set the science book beside the board while {companion} held its pages flat; together they matched each picture to an arrow.",
        "twist": "the curled small-intestine card had slipped beneath the atlas, and its tiny loops showed where most nutrients are absorbed",
        "turn": "With the hidden card back in place, the route curved instead of pretending the intestines were a straight hallway.",
        "learning": "food travels through the esophagus to the stomach and intestines, and the small intestine absorbs most nutrients",
        "question": "What helped the team put the digestion cards in the right order?",
        "answer": "The open science book's arrows showed the route from the mouth through the esophagus and stomach to the intestines.",
        "ending": "A blue ribbon curled around the restored cards, and the gold paper medal rested beside the open science book.",
        "gear": "an open science book, an atlas, and picture cards",
        "material": "paper cards and a blue ribbon",
    },
    "nutrient_star": {
        "problem": "a gold paper star marked NUTRIENTS had been placed beside the stomach on the game board",
        "stake": "The teams were beginning to think the stomach sent most nutrients straight into the body.",
        "temptation": "claim the star and call the stomach the finish line before anyone checked",
        "dialogue": "The book says the stomach mixes food first. The small intestine absorbs most nutrients.",
        "reply": "Then the star belongs by the small intestine. Let's move it and tell the teams why.",
        "method": "{hero} moved the star to the small-intestine square while {companion} added a label explaining its job.",
        "twist": "the star was not a finish marker after all; it reminded everyone that nutrients pass into the body mainly from the small intestine",
        "turn": "The teams changed the scorecard from 'reach the star' to 'explain what each part does.'",
        "learning": "the stomach mixes food, while the small intestine absorbs most nutrients from it",
        "question": "Where did the team move the paper star marked NUTRIENTS?",
        "answer": "They moved the star from the stomach to the small-intestine square, where most nutrients are absorbed.",
        "ending": "The gold star shone by the small-intestine card, and the medal lay beside a scorecard full of careful explanations.",
        "gear": "a science book, a paper star, and a scorecard",
        "material": "paper labels and a gold paper star",
    },
    "ribbon_route": {
        "problem": "the blue ribbon marking the model's route had slipped under the board, leaving a bare gap after the stomach",
        "stake": "Without a path through the intestines, the teams could not follow the model from start to finish.",
        "temptation": "tape a straight shortcut across the bare board and start the race",
        "dialogue": "This picture shows a long, coiled small intestine. We need enough ribbon to make those loops.",
        "reply": "Let's lift the board's paper edge and see if the ribbon is caught underneath.",
        "method": "{hero} lifted the edge of the display while {companion} gently pulled the ribbon free and curved it into loops.",
        "twist": "the missing length had been tucked under a folded corner of the paper model, and it was just long enough to show the intestine's coils",
        "turn": "When the pretend food token followed the longer, winding route, no station had to be skipped.",
        "learning": "the small intestine is long and folded into coils, and it absorbs most nutrients during digestion",
        "question": "How did the team repair the model's route?",
        "answer": "They freed the blue ribbon from under a folded edge and curved it into loops to show the small intestine.",
        "ending": "The blue ribbon wound neatly through the model, and the paper medal gleamed beside the newly complete route.",
        "gear": "a display board and the blue route ribbon",
        "material": "paper and blue ribbon",
    },
    "swapped_labels": {
        "problem": "the labels for the small intestine and large intestine had been switched on the display",
        "stake": "The teams were mixing up where most nutrients are absorbed and where water is absorbed.",
        "temptation": "flip the labels back by color alone without checking the facts",
        "dialogue": "Let's look it up: the small intestine absorbs most nutrients, and the large intestine absorbs water.",
        "reply": "Good idea. We'll check the book, then put each label where it belongs.",
        "method": "{hero} opened a library science book while {companion} compared its diagram with the two labels.",
        "twist": "the large intestine's job mattered too: it absorbs water as the leftover material is formed into waste",
        "turn": "They switched the labels only after checking the book, then asked each team to explain the difference.",
        "learning": "the small intestine absorbs most nutrients, while the large intestine absorbs water",
        "question": "What did the team learn about the two intestine labels?",
        "answer": "They learned that the small intestine absorbs most nutrients and the large intestine absorbs water.",
        "ending": "The two labels sat in their proper places, and the open book and paper medal shared the pool of lamplight.",
        "gear": "a library science book and two intestine labels",
        "material": "paper labels and a book diagram",
    },
    "team_relay": {
        "problem": "the scoreboard gave points only to the fastest speaker, so quiet readers stopped raising their hands",
        "stake": "Good science clues were going unheard, and the contest was leaving helpful teammates out.",
        "temptation": "answer every question alone and win the medal for being the loudest hero",
        "dialogue": "Our motto says, '{motto}' Maybe each teammate can explain one station in a relay.",
        "reply": "Yes. Let's make it a relay of facts, not a race for one fast guess.",
        "method": "{hero} asked {companion} to share the route cards and invited every teammate to explain one station in turn.",
        "twist": "when the quietest reader spoke, the last clue fell into place: the large intestine absorbs water",
        "turn": "The librarian changed the round so teams earned points for clear explanations and listening, not just speed.",
        "learning": "food passes from the mouth through the esophagus and stomach to the intestines; the small intestine absorbs most nutrients, and the large intestine absorbs water",
        "question": "How did the team make the contest fairer for quiet readers?",
        "answer": "They turned it into a relay, inviting each teammate to explain one station, and the librarian gave points for clear explanations and listening.",
        "ending": "The route cards formed a circle around the medal, while every teammate had a place at the library table.",
        "gear": "route cards, a scoreboard, and the motto banner",
        "material": "paper route cards and a banner",
    },
}


@dataclass
class StoryParams:
    hero: str = "Maya"
    companion: str = "Theo"
    librarian: str = "Ms. Lin"
    motto: str = MOTTOS[0]
    arc: str = "scattered_cards"
    setting: str = SETTING
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
    librarian: Entity
    display: Entity
    reference_book: Entity
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

    def entities(self) -> list[Entity]:
        return [self.hero, self.companion, self.librarian, self.display, self.reference_book]


def reasonableness_gate(params: StoryParams) -> None:
    """Reject combinations that cannot describe a sensible story in this world."""
    if params.hero not in HERO_NAMES:
        raise StoryError(f"Unknown hero {params.hero!r}; choose a registered student hero.")
    if params.companion not in COMPANION_NAMES:
        raise StoryError(f"Unknown companion {params.companion!r}; choose a registered teammate.")
    if params.librarian not in LIBRARIAN_NAMES:
        raise StoryError(f"Unknown librarian {params.librarian!r}; choose a registered librarian.")
    if params.motto not in MOTTOS:
        raise StoryError(f"Unknown motto {params.motto!r}; choose one of the registered library mottos.")
    if params.arc not in ARCS:
        raise StoryError(f"Unknown challenge {params.arc!r}; choose a registered Digestion Olympics challenge.")
    if params.setting != SETTING:
        raise StoryError(f"This storyworld is set in {SETTING}, not {params.setting!r}.")
    if len({params.hero, params.companion, params.librarian}) != 3:
        raise StoryError("The hero, teammate, and librarian must be different people.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about digestion in the school-library Olympics."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--companion", choices=COMPANION_NAMES)
    parser.add_argument("--librarian", choices=LIBRARIAN_NAMES)
    parser.add_argument("--motto", choices=MOTTOS)
    parser.add_argument("--arc", choices=list(ARCS))
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
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    possible_companions = [name for name in COMPANION_NAMES if name != hero]
    companion = getattr(args, "companion", None) or rng.choice(possible_companions)
    params = StoryParams(
        hero=hero,
        companion=companion,
        librarian=getattr(args, "librarian", None) or rng.choice(LIBRARIAN_NAMES),
        motto=getattr(args, "motto", None) or rng.choice(MOTTOS),
        arc=getattr(args, "arc", None) or rng.choice(list(ARCS)),
        setting=SETTING,
        seed=getattr(args, "seed", None),
    )
    reasonableness_gate(params)
    return params


def choose(rng: random.Random, options: list[str]) -> str:
    return rng.choice(options)


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(
            name=params.hero,
            kind="student_hero",
            meters={"paper_cape_length_cm": 54.0, "table_distance_cm": 80.0},
            memes={"curiosity": 0.7, "haste": 0.65, "confidence": 0.45},
        ),
        companion=Entity(
            name=params.companion,
            kind="student_teammate",
            meters={"book_reach_cm": 63.0},
            memes={"curiosity": 0.7, "confidence": 0.55, "trust": 0.6},
        ),
        librarian=Entity(
            name=params.librarian,
            kind="librarian",
            meters={"table_height_cm": 74.0},
            memes={"patience": 0.9, "hope": 0.65},
        ),
        display=Entity(
            name="Digestion Olympics display",
            kind="teaching_model",
            meters={"board_width_cm": 92.0, "route_length_cm": 46.0, "ribbon_length_cm": 68.0},
            memes={"readiness": 0.35, "clarity": 0.3},
        ),
        reference_book=Entity(
            name="open library science book",
            kind="reference_book",
            meters={"page_width_cm": 21.0, "open_width_cm": 42.0},
            memes={},
        ),
    )


def simulate(world: World) -> None:
    params = world.params
    hero = world.hero
    companion = world.companion
    librarian = world.librarian
    display = world.display
    arc = ARCS[params.arc]
    rng = random.Random(params.seed)

    world.facts.update(
        {
            "setting": params.setting,
            "challenge": "Digestion Olympics",
            "motto": params.motto,
            "problem": arc["problem"],
            "risk": arc["stake"],
            "method": arc["method"].format(hero=hero.name, companion=companion.name),
            "gear": arc["gear"],
            "helper": companion.name,
            "location": params.setting,
            "material": arc["material"],
            "ownership": "shared school-library display",
            "turn": arc["twist"],
            "consequence": arc["ending"],
            "resolved": False,
        }
    )

    opening = choose(rng, OPENINGS)
    world.say(f"{opening}.")
    world.say(
        f"In the school library, librarian {librarian.name} had turned the long science table "
        "into a friendly arena for the Digestion Olympics."
    )
    world.say(
        f"{hero.name}, wearing a red paper cape, volunteered as a superhero team captain, "
        f"and {companion.name} joined as teammate and clue-finder."
    )
    world.say(
        "On the board, a pretend bite of food traveled from the mouth through the esophagus "
        "and stomach to the small and large intestines."
    )
    world.say(f"Above the display, a bright banner carried the motto, “{params.motto}”")
    world.para()

    world.say(f"Just before the first round, {arc['problem']}. {arc['stake']}")
    world.say(f"For a moment, {hero.name} wanted to {arc['temptation']}.")
    world.say(f'{companion.name} said, “{arc["dialogue"].format(motto=params.motto)}”')
    world.say(f'{hero.name} answered, “{arc["reply"]}”')
    world.para()

    method = arc["method"].format(hero=hero.name, companion=companion.name)
    world.say(f"That answer changed the plan. {method}")
    world.say(f'Then came a surprise: {arc["twist"]}.')
    world.say(f'{arc["turn"]}')
    world.para()

    learning = arc["learning"]
    world.say(
        f"At the next station, {hero.name} and {companion.name} explained that {learning}."
    )
    world.say(
        f"{librarian.name} awarded their team the gold paper medal for clear thinking, "
        "not for rushing."
    )
    world.say(
        f"“{params.motto}” {hero.name} said as the team set the medal beside the display."
    )
    world.say(arc["ending"])

    hero.memes.update({"haste": 0.12, "focus": 0.9, "confidence": 0.82, "team_trust": 0.9})
    companion.memes.update({"confidence": 0.86, "curiosity": 0.9, "heard": 1.0})
    librarian.memes.update({"hope": 0.95, "relief": 0.82})
    display.memes.update({"readiness": 1.0, "clarity": 0.94})
    display.meters["route_length_cm"] = 64.0 if params.arc == "ribbon_route" else 52.0
    world.facts["resolved"] = True
    world.facts["solution"] = method
    world.facts["lesson"] = learning
    world.facts["medal_awarded_for"] = "clear explanations and teamwork"


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]

    prompts = [
        f"Write a child-friendly superhero story about {params.hero} at the Digestion Olympics in the school library.",
        f"Include a real conversation between {params.hero} and {params.companion} that changes their plan.",
        f"Use the motto “{params.motto}” and explain this challenge: {arc['problem']}.",
    ]
    story_qa = [
        QAItem(
            question=f"What shortcut did {params.hero} first consider?",
            answer=f"{params.hero} first considered trying to {arc['temptation']}, but listened to {params.companion} before acting.",
        ),
        QAItem(
            question=arc["question"],
            answer=arc["answer"],
        ),
        QAItem(
            question=f"What surprise helped {params.hero} and {params.companion} solve the problem?",
            answer=f"They discovered that {arc['twist']}, which changed how they approached the challenge.",
        ),
        QAItem(
            question=f"What did {params.hero} learn about digestion?",
            answer=f"{params.hero} explained that {arc['learning']}.",
        ),
        QAItem(
            question=f"What did the Digestion Olympics motto help the team remember?",
            answer=f"The motto, “{params.motto}” reminded the team to work together and value every part of the task.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is digestion?",
            answer="Digestion is the process of breaking food down so the body can take in nutrients and use them.",
        ),
        QAItem(
            question="What does the small intestine do?",
            answer="The small intestine absorbs most nutrients from digested food.",
        ),
        QAItem(
            question="What does the large intestine do?",
            answer="The large intestine absorbs water from what remains as the body forms waste.",
        ),
        QAItem(
            question="What is a motto?",
            answer="A motto is a short saying that expresses an idea or helps a group remember what matters.",
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
    for entity in world.entities():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.name:32} ({entity.kind:18}) meters={meters} memes={memes}")
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
valid(story) :-
    selected_hero(H), hero(H),
    selected_companion(C), companion(C),
    selected_librarian(L), librarian(L),
    selected_motto(M), motto(M),
    selected_arc(A), arc(A),
    selected_setting(S), setting(S),
    H != C, H != L, C != L.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("domain", "school_library_digestion_olympics"),
        asp.fact("feature", "dialogue"),
        asp.fact("style", "superhero_story"),
    ]
    facts.extend(asp.fact("hero", name) for name in HERO_NAMES)
    facts.extend(asp.fact("companion", name) for name in COMPANION_NAMES)
    facts.extend(asp.fact("librarian", name) for name in LIBRARIAN_NAMES)
    facts.extend(asp.fact("motto", motto) for motto in MOTTOS)
    facts.extend(asp.fact("arc", arc) for arc in ARCS)
    facts.append(asp.fact("setting", SETTING))
    return "\n".join(facts)


def asp_program(show: str = "#show valid/1.", params: Optional[StoryParams] = None) -> str:
    if params is None:
        params = StoryParams()
    selected = "\n".join(
        [
            f'importantly_not_used("{params.hero}").'
            if False
            else "",
        ]
    )
    import storyworlds.asp as asp

    selected_facts = "\n".join(
        [
            asp.fact("selected_hero", params.hero),
            asp.fact("selected_companion", params.companion),
            asp.fact("selected_librarian", params.librarian),
            asp.fact("selected_motto", params.motto),
            asp.fact("selected_arc", params.arc),
            asp.fact("selected_setting", params.setting),
        ]
    )
    del selected
    return f"{asp_facts()}\n{selected_facts}\n{ASP_RULES}\n{show}\n"


def asp_is_valid(params: StoryParams) -> bool:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program(params=params))
    return asp.atoms(model, "valid") == [("story",)]


CURATED = [
    StoryParams(
        hero="Maya",
        companion="Theo",
        librarian="Ms. Lin",
        motto=MOTTOS[0],
        arc="scattered_cards",
        seed=113,
    ),
    StoryParams(
        hero="Zuri",
        companion="Ivy",
        librarian="Mr. Bell",
        motto=MOTTOS[1],
        arc="nutrient_star",
        seed=227,
    ),
    StoryParams(
        hero="Leo",
        companion="Ben",
        librarian="Mrs. Rivera",
        motto=MOTTOS[2],
        arc="ribbon_route",
        seed=331,
    ),
    StoryParams(
        hero="Asha",
        companion="Nico",
        librarian="Ms. Okafor",
        motto=MOTTOS[0],
        arc="swapped_labels",
        seed=449,
    ),
    StoryParams(
        hero="Theo",
        companion="Maya",
        librarian="Mr. Bell",
        motto=MOTTOS[1],
        arc="team_relay",
        seed=557,
    ),
]


def asp_verify() -> int:
    import storyworlds.asp as asp

    cases = list(CURATED)
    cases.extend(
        [
            replace(CURATED[0], companion=CURATED[0].hero),
            replace(CURATED[0], motto="Keep the whole medal."),
            replace(CURATED[0], arc="unregistered_challenge"),
            replace(CURATED[0], setting="the playground"),
        ]
    )

    for params in cases:
        try:
            reasonableness_gate(params)
            python_valid = True
        except StoryError:
            python_valid = False
        asp_valid = asp_is_valid(params)
        if python_valid != asp_valid:
            print(f"MISMATCH: Python and ASP disagree for {params!r}.")
            return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story.strip():
            print("MISMATCH: a curated story was empty.")
            return 1
        if "Digestion Olympics" not in sample.story or SETTING not in sample.story:
            print("MISMATCH: a generated story missed its domain or setting.")
            return 1
        if sample.story.count("“") < 3 or sample.story.count("”") < 3:
            print("MISMATCH: a generated story did not contain its dialogue.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("MISMATCH: a generated story was missing its questions.")
            return 1
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: a generated world did not reach its resolution.")
            return 1

    print("OK: ASP/Python parity holds, and all curated stories resolve with dialogue and grounded questions.")
    return 0


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
    if args.n < 0:
        raise StoryError("The number of requested stories cannot be negative.")

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.show_asp or args.asp:
        rng = random.Random(base_seed)
        params = resolve_params(args, rng)
        params.seed = base_seed
        if args.show_asp:
            print(asp_program(params=params))
            return
        import storyworlds.asp as asp

        model = asp.one_model(asp_program(params=params))
        print(asp.atoms(model, "valid"))
        return

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        limit = max(args.n * 30, 30)
        while len(samples) < args.n and attempts < limit:
            rng = random.Random(base_seed + attempts)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempts
            attempts += 1
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
