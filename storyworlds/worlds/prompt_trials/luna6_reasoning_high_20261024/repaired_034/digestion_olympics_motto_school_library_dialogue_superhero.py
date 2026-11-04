#!/usr/bin/env python3
"""
A small superhero storyworld set during the Digestion Olympics in a school library.

A speedy student hero and a thoughtful teammate use a library guide to solve a
hands-on digestion challenge. Their dialogue changes the plan, and their motto
and final action show what they have learned.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


for _parent in Path(__file__).resolve().parents:
    if _parent.name == "storyworlds" and (_parent / "results.py").is_file():
        sys.path.insert(0, str(_parent.parent))
        break

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Mira"
    partner: str = "Zee"
    place: str = "the school library"
    arc: str = "arrow_tangle"
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
    librarian: Entity
    model: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


HERO_NAMES = ["Mira", "Theo", "Zara", "Finn", "Asha", "Leo"]
PARTNER_NAMES = ["Mira", "Theo", "Zara", "Finn", "Asha", "Leo"]
PLACES = ["the school library"]

ARCS = {
    "arrow_tangle": {
        "problem": (
            "a fan had scattered the route arrows, and the felt food token sat "
            "beside the stomach instead of at the start"
        ),
        "stake": "The next team might send its token through the organs in the wrong order",
        "urge": "sweep every card into place before the clock blinked",
        "clue": (
            "the library guide shows the mouth first, then the esophagus, stomach, "
            "and intestines"
        ),
        "plan": "check the guide and rebuild the path from the mouth onward",
        "action": (
            "They found arrows under the reading tables and placed each one beside "
            "the organ shown in the guide"
        ),
        "twist": (
            "A tiny arrow stuck beneath the finish mat pointed to the small intestine, "
            "where most nutrients are absorbed"
        ),
        "science": "Most nutrients are absorbed in the small intestine.",
        "resolution": (
            "The judges gave them a bright star for explaining the route, not for "
            "finishing fastest"
        ),
        "ending": (
            "the correct arrow path curled beneath the Digestion Olympics banner, "
            "with the felt token at its true finish"
        ),
        "motto": "Read the clues; follow the route!",
        "question": "Where did the food token need to start?",
        "answer": (
            "The food token needed to start at the mouth, then travel through the "
            "esophagus, stomach, and intestines."
        ),
        "solution_answer": (
            "They used the library guide to put the arrows in order, starting at "
            "the mouth and following the path through the intestines."
        ),
        "start_position_m": 0.78,
        "material": "picture arrows",
    },
    "pinched_esophagus": {
        "problem": (
            "a felt food token was stuck halfway down the model's soft esophagus "
            "tube after a practice squeeze"
        ),
        "stake": "The next team could not show how food moves from the mouth to the stomach",
        "urge": "push the token out with superhero strength",
        "clue": (
            "the guide shows gentle muscle waves in the esophagus moving food toward "
            "the stomach"
        ),
        "plan": "loosen the model tube and try a gentle wave instead of a shove",
        "action": (
            "They eased the pinched tube open, unfolded the felt token, and pressed "
            "gently behind it in a wave"
        ),
        "twist": (
            "The token slid through without any super-strength; the model's gentle "
            "waves showed how muscles help move food"
        ),
        "science": (
            "Muscle waves called peristalsis help move food down the esophagus to "
            "the stomach."
        ),
        "resolution": (
            "The judges placed a teamwork medal beside the clear tube and asked the "
            "pair to show the gentle wave again"
        ),
        "ending": (
            "the felt token rested in the model stomach while a paper wave curled "
            "along the esophagus"
        ),
        "motto": "Gentle waves move food along!",
        "question": "How did the pair move the stuck token?",
        "answer": (
            "They opened the pinched model tube, unfolded the token, and pressed "
            "gently behind it in a wave."
        ),
        "solution_answer": (
            "They loosened the tube and used a gentle wave rather than pushing hard, "
            "just as the guide showed."
        ),
        "start_position_m": 0.53,
        "material": "soft model tubing",
    },
    "mouth_missing": {
        "problem": (
            "a stomach-shaped basket stood at the start of the track while the mouth "
            "station was empty"
        ),
        "stake": "The teams might think digestion begins only after food reaches the stomach",
        "urge": "start at the stomach so the team could race ahead",
        "clue": (
            "the body book shows chewing and saliva beginning digestion before food "
            "is swallowed"
        ),
        "plan": "find the mouth card and put it at the first station",
        "action": (
            "They found the mouth card tucked inside the open body book and returned "
            "it to the first station"
        ),
        "twist": (
            "With the mouth card in place, the pretend food had a real first step: "
            "chewing breaks it into smaller pieces, and saliva starts digesting some foods"
        ),
        "science": (
            "Digestion begins in the mouth, where chewing breaks food into smaller "
            "pieces and saliva starts digesting some foods."
        ),
        "resolution": (
            "The judges let the pair restart the model, and this time the food token "
            "began at the mouth"
        ),
        "ending": (
            "the mouth card stood proudly at the start while the team traced the "
            "whole route together"
        ),
        "motto": "Start at the mouth; learn as you go!",
        "question": "What clue showed that digestion begins in the mouth?",
        "answer": (
            "The body book showed chewing and saliva starting digestion before food "
            "is swallowed."
        ),
        "solution_answer": (
            "They returned the mouth card to the first station, then restarted the "
            "model with the mouth before the stomach."
        ),
        "start_position_m": 0.10,
        "material": "a paper mouth card",
    },
    "nutrient_stars": {
        "problem": (
            "gold paper nutrient stars had been put in the large-intestine basket, "
            "while the small-intestine station sat empty"
        ),
        "stake": "The team could leave the model without showing where most nutrients are absorbed",
        "urge": "dash the stars to the finish basket and hope the judges did not notice",
        "clue": (
            "the guide draws arrows from the small intestine toward the body, where "
            "most nutrients are absorbed"
        ),
        "plan": "move the nutrient stars to the small intestine and trace the arrows",
        "action": (
            "They carried the paper stars to the small-intestine station and traced "
            "its arrows to the paper outline of the body"
        ),
        "twist": (
            "The stars were not finish-line prizes at all; they stood for nutrients "
            "the body takes in from digested food"
        ),
        "science": "Most nutrients from digested food are absorbed in the small intestine.",
        "resolution": (
            "The judges awarded a gold star for the clear explanation and left the "
            "large-intestine basket for the next part of the route"
        ),
        "ending": (
            "gold paper stars gleamed beside the small intestine, and the team’s "
            "route finally matched the guide"
        ),
        "motto": "Find the nutrients; share what you know!",
        "question": "Where did the guide show most nutrients being absorbed?",
        "answer": "The guide showed most nutrients being absorbed in the small intestine.",
        "solution_answer": (
            "They moved the paper nutrient stars to the small-intestine station and "
            "followed its arrows toward the body."
        ),
        "start_position_m": 0.91,
        "material": "gold paper stars",
    },
    "water_drops": {
        "problem": (
            "blue water-drop counters were piled at the small-intestine station, "
            "and the large-intestine cup was empty"
        ),
        "stake": "The teams could miss what happens to some of the water left in the digestive tract",
        "urge": "scoop all the counters into the nearest basket and call the race done",
        "clue": (
            "the library book says the large intestine absorbs much of the remaining "
            "water from material after the small intestine"
        ),
        "plan": "follow the model path and place the water counters by the large intestine",
        "action": (
            "They carried the blue counters along the model path and set them beside "
            "the large-intestine cup"
        ),
        "twist": (
            "The blue counters were not extra nutrient points; they represented "
            "water the body can take back"
        ),
        "science": (
            "The large intestine absorbs much of the remaining water from material "
            "that has passed through the small intestine."
        ),
        "resolution": (
            "The judges nodded at the careful explanation, and the next team could "
            "see why the water cup belonged at the end of the path"
        ),
        "ending": (
            "blue counters made a neat trail to the large-intestine cup, ready for "
            "the next library team to learn from"
        ),
        "motto": "Follow the water; finish together!",
        "question": "What did the blue water-drop counters represent?",
        "answer": (
            "The blue counters represented some of the remaining water that the "
            "large intestine can absorb."
        ),
        "solution_answer": (
            "They followed the model path and placed the blue water counters beside "
            "the large intestine."
        ),
        "start_position_m": 0.87,
        "material": "blue paper counters",
    },
}

ARC_NAMES = list(ARCS)
PARAM_REGISTRIES = {
    "heroes": HERO_NAMES,
    "partners": PARTNER_NAMES,
    "places": PLACES,
    "arcs": ARC_NAMES,
}

OPENINGS = [
    "A sunny stripe crossed the library carpet as the morning bell rang",
    "The quiet shelves seemed to sparkle beneath a fresh paper banner",
    "A red cape fluttered past the book returns as the challenge began",
    "The library smelled of paper and crayons, and excited voices filled the room",
    "At the school library door, a bright banner announced a very unusual contest",
    "Books stood in tidy rows while a felt food token waited on the challenge table",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "A superhero storyworld about digestion, teamwork, and the school "
            "library's Digestion Olympics."
        )
    )
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--partner", choices=PARTNER_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--arc", choices=ARC_NAMES)
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


def validate_params(params: StoryParams) -> bool:
    if params.hero not in HERO_NAMES:
        raise StoryError(f"Unknown hero {params.hero!r}; choose a registered hero.")
    if params.partner not in PARTNER_NAMES:
        raise StoryError(
            f"Unknown partner {params.partner!r}; choose a registered partner."
        )
    if params.hero == params.partner:
        raise StoryError("The hero and partner must be different characters.")
    if params.place not in PLACES:
        raise StoryError(
            f"Unknown setting {params.place!r}; this story takes place in the school library."
        )
    if params.arc not in ARCS:
        raise StoryError(f"Unknown challenge {params.arc!r}; choose a registered challenge.")
    if params.seed is not None and not isinstance(params.seed, int):
        raise StoryError("The seed must be an integer.")
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    partner_options = [name for name in PARTNER_NAMES if name != hero]
    partner = args.partner or rng.choice(partner_options)
    params = StoryParams(
        hero=hero,
        partner=partner,
        place=args.place or rng.choice(PLACES),
        arc=args.arc or rng.choice(ARC_NAMES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(
        params=params,
        hero=Entity(name=params.hero, kind="superhero"),
        partner=Entity(name=params.partner, kind="teammate"),
        librarian=Entity(name="Ms. Vale", kind="librarian"),
        model=Entity(name="digestive-system model", kind="teaching_model"),
    )


def choose(rng: random.Random, options: list[str]) -> str:
    return rng.choice(options)


def simulate(world: World) -> None:
    params = world.params
    hero = world.hero
    partner = world.partner
    librarian = world.librarian
    model = world.model
    arc = ARCS[params.arc]
    rng = random.Random(params.seed)

    hero.meters.update({"position_m": 0.0, "speed_mps": 8.0})
    partner.meters.update({"position_m": 0.35, "reach_m": 0.55})
    librarian.meters.update({"position_m": 1.1})
    model.meters.update(
        {
            "track_length_m": 1.2,
            "token_position_m": float(arc["start_position_m"]),
        }
    )

    hero.memes.update({"hurry": 0.85, "confidence": 0.75, "curiosity": 0.3})
    partner.memes.update({"attention": 0.9, "teamwork": 0.7})
    librarian.memes.update({"patience": 0.9, "encouragement": 0.8})

    world.facts.update(
        {
            "arc": params.arc,
            "setting": params.place,
            "challenge": "Digestion Olympics",
            "problem": arc["problem"],
            "risk": arc["stake"],
            "clue": arc["clue"],
            "method": arc["plan"],
            "helper": partner.name,
            "librarian": librarian.name,
            "material": arc["material"],
            "token_position_before_m": model.meters["token_position_m"],
            "resolved": False,
            "conversation_changed_plan": False,
            "motto": arc["motto"],
            "science": arc["science"],
        }
    )

    opening = choose(rng, OPENINGS)
    world.say(
        f"{opening}. The school library's Digestion Olympics were about to begin, "
        f"and superhero {hero.name} arrived in a fluttering cape."
    )
    world.say(
        "Teams would guide a felt food token through a model of the mouth, "
        "esophagus, stomach, small intestine, and large intestine, then explain "
        "what happens along the way."
    )

    world.para()
    world.say(f"Then {arc['problem']}. {arc['stake']}.")
    if hero.memes["hurry"] > 0.5:
        world.say(
            f"{hero.name} leaned toward the model. “I can use my super-speed to "
            f"{arc['urge']}!”"
        )
    world.say(
        f"{partner.name} pointed to the library guide. “Wait. {arc['clue']}. "
        f"Let's look before we race.”"
    )

    hero.memes["hurry"] = 0.15
    hero.memes["curiosity"] = 0.9
    hero.memes["teamwork"] = 0.9
    partner.memes["teamwork"] = 1.0
    world.facts["conversation_changed_plan"] = True
    world.facts["decision"] = arc["plan"]
    world.say(
        f"{hero.name} stopped and smiled. “You're right. Let's {arc['plan']}.”"
    )

    world.para()
    hero.meters["position_m"] = 0.45
    partner.meters["position_m"] = 0.55
    world.say(
        f"{librarian.name} opened the body book beside them. Working together, "
        f"{hero.name} and {partner.name} made a careful plan."
    )
    world.say(f"{arc['action']}.")
    model.meters["token_position_m"] = model.meters["track_length_m"]
    hero.memes["confidence"] = 0.95
    partner.memes["attention"] = 1.0
    world.say(f"Then came the surprise: {arc['twist']}.")
    world.say(f"The guide confirmed what they had learned: {arc['science']}")

    world.facts["token_position_after_m"] = model.meters["token_position_m"]
    world.facts["resolved"] = True

    world.para()
    world.say(f"{arc['resolution']}.")
    world.say(
        f"Together, they lettered a motto on the scoreboard: “{arc['motto']}”"
    )
    world.say(f"At last, {arc['ending']}.")
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]

    prompts = [
        (
            f"Write a child-friendly superhero story in {params.place} about "
            f"{params.hero} and {params.partner} solving a digestion challenge."
        ),
        (
            "Include the Digestion Olympics, a meaningful conversation, an accurate "
            "digestion fact, and a motto."
        ),
        f"Tell a complete story about this trouble: {arc['problem']}.",
    ]
    story_qa = [
        QAItem(
            question="What trouble did the team face?",
            answer=f"At the Digestion Olympics, {arc['problem']}.",
        ),
        QAItem(question=arc["question"], answer=arc["answer"]),
        QAItem(
            question=f"How did {params.hero} and {params.partner} solve the trouble?",
            answer=arc["solution_answer"],
        ),
        QAItem(
            question=f"What clue helped {params.hero} and {params.partner} change their plan?",
            answer=(
                f"The library guide showed them that {arc['clue']}, so they chose "
                "to understand the problem instead of rushing."
            ),
        ),
        QAItem(
            question="What motto did the teammates put on the scoreboard?",
            answer=f"Their motto was, “{arc['motto']}”",
        ),
        QAItem(
            question="What did the team learn about digestion?",
            answer=arc["science"],
        ),
    ]
    world_qa = [
        QAItem(
            question="What is digestion?",
            answer=(
                "Digestion is the process of breaking food down so the body can use "
                "nutrients from it."
            ),
        ),
        QAItem(
            question="What does the esophagus do?",
            answer=(
                "The esophagus is a tube that carries food from the mouth to the "
                "stomach with help from muscle movements."
            ),
        ),
        QAItem(
            question="What are the Digestion Olympics in this story?",
            answer=(
                "They are friendly library challenges where teams use a model to "
                "learn about digestion and explain what they discover."
            ),
        ),
        QAItem(
            question="What is a motto?",
            answer=(
                "A motto is a short saying that expresses an idea or goal a person "
                "or group wants to remember."
            ),
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
    for entity in (world.hero, world.partner, world.librarian, world.model):
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.name:24} ({entity.kind:14}) "
            f"meters={meters} memes={memes}"
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
valid(story) :-
    selected_hero(H), hero(H),
    selected_partner(P), partner(P), H != P,
    selected_place(L), place(L),
    selected_arc(A), arc(A),
    feature(digestion), feature(olympics), feature(motto), feature(dialogue),
    style(superhero_story).
"""


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")
    return slug or "unknown"


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    lines.extend(asp.fact("hero", _slug(name)) for name in HERO_NAMES)
    lines.extend(asp.fact("partner", _slug(name)) for name in PARTNER_NAMES)
    lines.extend(asp.fact("place", "school_library") for _ in PLACES)
    lines.extend(asp.fact("arc", name) for name in ARC_NAMES)
    lines.extend(
        asp.fact("feature", feature)
        for feature in ("digestion", "olympics", "motto", "dialogue")
    )
    lines.append(asp.fact("style", "superhero_story"))
    return "\n".join(lines)


def asp_program(params: Optional[StoryParams] = None) -> str:
    import storyworlds.asp as asp

    selected = ""
    if params is not None:
        selected = "\n".join(
            (
                asp.fact("selected_hero", _slug(params.hero)),
                asp.fact("selected_partner", _slug(params.partner)),
                asp.fact("selected_place", "school_library"),
                asp.fact("selected_arc", _slug(params.arc)),
            )
        )
    return f"{asp_facts()}\n{selected}\n{ASP_RULES}\n#show valid/1.\n"


CURATED = [
    StoryParams("Mira", "Zee", "the school library", arc, 2101 + index)
    for index, arc in enumerate(ARC_NAMES)
]


def asp_verify() -> int:
    import storyworlds.asp as asp

    test_cases = [(params, True) for params in CURATED]
    test_cases.extend(
        [
            (
                StoryParams("Mira", "Mira", "the school library", "arrow_tangle", 99),
                False,
            ),
            (
                StoryParams("Theo", "Asha", "the school library", "not_a_challenge", 100),
                False,
            ),
        ]
    )

    for params, expected in test_cases:
        try:
            python_valid = validate_params(params)
        except StoryError:
            python_valid = False
        model = asp.one_model(asp_program(params))
        asp_valid = asp.atoms(model, "valid") == [("story",)]
        if python_valid != expected or asp_valid != expected:
            print(
                "MISMATCH: Python/ASP reasonableness parity failed for "
                f"{params!r} (Python={python_valid}, ASP={asp_valid})."
            )
            return 1

    for params in CURATED:
        sample = generate(params)
        world = sample.world
        has_dialogue = "“" in sample.story and "”" in sample.story
        if (
            world is None
            or not world.facts.get("resolved")
            or not world.facts.get("conversation_changed_plan")
            or "Digestion Olympics" not in sample.story
            or "motto" not in sample.story.lower()
            or not has_dialogue
            or not sample.story_qa
        ):
            print(f"MISMATCH: Generated story exercise failed for arc {params.arc}.")
            return 1

    print("OK: ASP/Python parity holds, and every curated story passes its checks.")
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

    try:
        if args.show_asp:
            print(asp_program())
            return
        if args.verify:
            raise SystemExit(asp_verify())

        if args.n < 0:
            raise StoryError("The number of stories must be zero or greater.")

        base_seed = args.seed if args.seed is not None else random.randrange(2**31)

        if args.asp:
            params = resolve_params(args, random.Random(base_seed))
            params.seed = base_seed
            import storyworlds.asp as asp

            model = asp.one_model(asp_program(params))
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
                print(
                    json.dumps(
                        [sample.to_dict() for sample in samples],
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            return

        for index, sample in enumerate(samples):
            header = f"### variant {index + 1}" if len(samples) > 1 else ""
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
