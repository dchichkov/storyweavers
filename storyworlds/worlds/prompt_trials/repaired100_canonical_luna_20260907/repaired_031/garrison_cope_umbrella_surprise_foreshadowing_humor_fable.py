#!/usr/bin/env python3
"""
Standalone story world: the garrison umbrella fable.

A small fable about a young keeper at a hill garrison who must cope with a
surprising storm. Foreshadowing and humor turn an ordinary umbrella into the
tool that helps everyone share shelter.
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
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    helper_name: str
    helper_role: str
    bird: str
    umbrella: str
    scenario: str
    opening_variant: int = 0
    surprise_variant: int = 0
    ending_variant: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "hill_garrison": {
        "place": "the hill garrison",
        "affords": {"watching", "shelter", "helping"},
    }
}

UMBRELLAS = {
    "red": {
        "label": "a red umbrella",
        "color": "red",
        "joke": "It had a handle shaped like a duck, though nobody knew why the duck looked worried.",
    },
    "blue": {
        "label": "a blue umbrella",
        "color": "blue",
        "joke": "Its loose ribs clicked together like tiny marching teeth.",
    },
    "yellow": {
        "label": "a yellow umbrella",
        "color": "yellow",
        "joke": "It was so bright that even the sleepy sentry saluted it.",
    },
}

BIRDS = {
    "crow": {"label": "crow", "call": "caw"},
    "swallow": {"label": "swallow", "call": "twitter"},
    "sparrow": {"label": "sparrow", "call": "chirp"},
}

SCENARIOS = {
    "watchtower": {
        "bird": "crow",
        "premise": "was keeping the morning watch from the old tower",
        "goal": "stay brave and keep the garrison's message flag dry",
        "trouble": "a sudden cloudburst sent rain through every crack, and the flag began to droop",
        "foreshadow": "A line of ants had already marched uphill, carrying crumbs beneath the tower step.",
        "repair": "opened the umbrella over the flag and invited the soaked sentry beneath it",
        "result": "the flag rose again, while the crow shook rain from its feathers",
    },
    "gatehouse": {
        "bird": "swallow",
        "premise": "was helping the gatekeeper count wagons at the stone entrance",
        "goal": "cope with a busy morning without losing the visitor list",
        "trouble": "a wind gust flipped the list into a puddle just as thunder boomed",
        "foreshadow": "The gatehouse cat had dragged a dry cloth toward the door and then hidden from the sky.",
        "repair": "held the umbrella over the list while the helper copied the names onto the dry cloth",
        "result": "the wagons rolled in safely, and the swallow darted beneath the eave",
    },
    "supply_yard": {
        "bird": "sparrow",
        "premise": "was carrying a basket of bread across the garrison supply yard",
        "goal": "deliver breakfast before the hungry guards began inventing recipes",
        "trouble": "rain burst from a clear-looking sky and turned the yard into a puddly maze",
        "foreshadow": "The old well had begun to plink even before the first raindrop fell.",
        "repair": "used the umbrella as a roof while the helper carried the bread basket across the stones",
        "result": "breakfast arrived dry, except for one heroic soggy crust",
    },
    "signal_hill": {
        "bird": "crow",
        "premise": "was practicing the garrison signal from the windy hill",
        "goal": "send a clear warning without frightening everyone",
        "trouble": "the surprise storm tangled the signal ribbons and blew the whistle into a bush",
        "foreshadow": "The grass leaned all one way, although the air had seemed perfectly still.",
        "repair": "covered the ribbons with the umbrella and asked the helper to retrieve the whistle",
        "result": "the signal flew straight, and the crow answered with a proud caw",
    },
}

OPENINGS = [
    "At dawn, the hill garrison glittered above the valley.",
    "The garrison woke to clanking buckets, sleepy boots, and one very serious-looking crow.",
    "On a bright morning, {child} arrived at the hill garrison with an umbrella tucked under one arm.",
    "The stone walls of the garrison had seen many storms, but they still disliked getting wet.",
]

SURPRISES = [
    "Then the sky made a noise like a giant sneezing kettle, and the rain sprang out all at once.",
    "Without asking permission, a dark cloud popped over the hill and emptied itself.",
    "A fat drop landed on {child}'s nose. Then another landed on the flag. Then the whole sky joined in.",
]

ENDINGS = [
    "When the cloud passed, everyone laughed, because the umbrella had sheltered the flag, the helpers, and the garrison's most important duck-shaped handle.",
    "By noon, the sun returned. The garrison learned that courage is not staying dry; it is finding a way to help while getting a little wet.",
    "The bird flew off beneath the brightening sky, and {child} kept the umbrella open until every worried face had smiled.",
]


GIRL_NAMES = ["Luna", "Mira", "Nora", "Ivy"]
BOY_NAMES = ["Leo", "Milo", "Owen", "Finn"]
HELPERS = [
    ("Mara", "captain"),
    ("Tomas", "gatekeeper"),
    ("Suri", "cook"),
    ("Bram", "sentry"),
]


def valid_combo(bird: str, umbrella: str, scenario: str) -> bool:
    return (
        bird in BIRDS
        and umbrella in UMBRELLAS
        and scenario in SCENARIOS
        and SCENARIOS[scenario]["bird"] == bird
    )


def explain_rejection(bird: str, umbrella: str, scenario: str) -> str:
    return (
        f"No story: the {scenario} scene requires a known bird and umbrella, "
        f"but received {bird!r}, {umbrella!r}, and {scenario!r}."
    )


def tell(params: StoryParams) -> World:
    if not valid_combo(params.bird, params.umbrella, params.scenario):
        raise StoryError(explain_rejection(params.bird, params.umbrella, params.scenario))

    plan = SCENARIOS[params.scenario]
    bird_info = BIRDS[params.bird]
    umbrella = UMBRELLAS[params.umbrella]
    world = World()

    child = world.add(Entity(params.child_name, "character", params.child_name))
    helper = world.add(Entity(params.helper_name, "character", params.helper_name))
    bird = world.add(Entity(params.bird, "bird", bird_info["label"]))
    prop = world.add(Entity(params.umbrella, "thing", umbrella["label"]))

    child.meters["responsibility"] = 1.0
    child.memes["confidence"] = 1.0
    helper.memes["patience"] = 1.0
    bird.memes["calm"] = 0.0
    prop.meters["cover"] = 1.0

    opening = OPENINGS[params.opening_variant % len(OPENINGS)].format(
        child=child.label
    )
    world.say(opening)
    world.say(
        f"{child.label} was {plan['premise']}. {child.label} carried {umbrella['label']}. "
        f"{umbrella['joke']}"
    )
    world.say(f"The plan was to {plan['goal']}.")

    world.para()
    world.say(plan["foreshadow"])
    world.say(
        f"{helper.label}, the {params.helper_role}, glanced at the sky and said, "
        f"“That looks too quiet.”"
    )
    world.say(
        f"{child.label} replied, “Quiet skies cannot surprise us.” "
        f"{helper.label} raised one eyebrow. “That is exactly when they try.”"
    )
    world.say(
        SURPRISES[params.surprise_variant % len(SURPRISES)].format(child=child.label)
    )
    world.say(f"Because of that, {plan['trouble']}.")
    child.memes["worry"] = 1.0
    bird.memes["startle"] = 1.0
    world.facts["surprise"] = True
    world.facts["foreshadowing"] = plan["foreshadow"]

    world.para()
    world.say(
        f"{child.label} squeezed the umbrella handle and said, "
        f"“I am not sure I can cope with all this rain.”"
    )
    world.say(
        f"{helper.label} answered, “You do not have to cope alone. "
        f"Make one useful choice.”"
    )
    world.say(f"{child.label} {plan['repair']}.")
    child.memes["worry"] = 0.0
    child.memes["bravery"] = 1.0
    bird.memes["calm"] = 1.0
    helper.memes["helped"] = 1.0
    world.fired.add(("shelter", params.umbrella, params.bird))
    world.say(f"The change worked: {plan['result']}.")

    world.para()
    world.say(
        ENDINGS[params.ending_variant % len(ENDINGS)].format(child=child.label)
    )
    world.say(
        f"The garrison kept one lesson: when the weather makes a joke, "
        f"share the umbrella before laughing."
    )

    world.facts.update(
        child=child,
        helper=helper,
        bird=bird,
        umbrella=prop,
        umbrella_cfg=umbrella,
        plan=plan,
        result=plan["result"],
        resolved=True,
        place="the hill garrison",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly fable set in a garrison, where an umbrella helps someone cope with a surprising storm.",
        f"Show how the foreshadowing — {f['foreshadowing']} — prepares the reader for the surprise.",
        f"Include humorous dialogue and end with the concrete result that {f['result']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What was {f['child'].label} doing at the garrison?",
            answer=f"{f['child'].label} {f['plan']['premise']} and hoped to {f['plan']['goal']}.",
        ),
        QAItem(
            question="What foreshadowed the surprise storm?",
            answer=f"The story foreshadowed the storm by saying, “{f['foreshadowing']}”",
        ),
        QAItem(
            question="What surprising problem happened?",
            answer=f"A sudden rainstorm caused this problem: {f['plan']['trouble']}.",
        ),
        QAItem(
            question="How did the umbrella help?",
            answer=f"{f['child'].label} {f['plan']['repair']}, which helped everyone cope and led to this result: {f['result']}.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="At first, the storm made the bird startled and the child worried. By the end, the umbrella had become shared shelter, and the garrison was safe and cheerful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garrison?",
            answer="A garrison is a place where soldiers live, work, and protect an area.",
        ),
        QAItem(
            question="What does it mean to cope?",
            answer="To cope means to deal with a difficult situation by staying calm and choosing helpful actions.",
        ),
        QAItem(
            question="What is an umbrella?",
            answer="An umbrella is a folding cover held above a person to keep off rain or sunlight.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that suddenly happens or is discovered.",
        ),
        QAItem(
            question="What makes a fable?",
            answer="A fable is a short story that uses simple events, often with animals or personified objects, to teach a lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
needs_shelter(C, B) :- child(C), bird(B), storm.
good_story(C, B, U, S) :-
    child(C), bird(B), umbrella(U), scenario(S),
    needs_shelter(C, B),
    suitable(S, B),
    covered(U).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("child", "child"),
        asp.fact("storm"),
        asp.fact("covered", "red"),
        asp.fact("covered", "blue"),
        asp.fact("covered", "yellow"),
    ]
    for bird in BIRDS:
        lines.append(asp.fact("bird", bird))
    for umbrella in UMBRELLAS:
        lines.append(asp.fact("umbrella", umbrella))
    for scenario, data in SCENARIOS.items():
        lines.append(asp.fact("scenario", scenario))
        lines.append(asp.fact("suitable", scenario, data["bird"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/4."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = sorted(
        ("child", bird, umbrella, scenario)
        for scenario, data in SCENARIOS.items()
        for bird in BIRDS
        for umbrella in UMBRELLAS
        if data["bird"] == bird and valid_combo(bird, umbrella, scenario)
    )
    cl = asp_valid_combos()
    if set(py) != set(cl):
        print("MISMATCH between clingo and Python gates:")
        print("python:", py)
        print("clingo:", cl)
        return 1
    for params in curated_params():
        generate(params)
    print(f"OK: clingo gate matches Python gate ({len(py)} combos), and stories generated.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A garrison fable about coping with a surprising storm and an umbrella."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--role")
    parser.add_argument("--bird", choices=BIRDS)
    parser.add_argument("--umbrella", choices=UMBRELLAS)
    parser.add_argument("--scenario", choices=SCENARIOS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scenario = args.scenario or rng.choice(list(SCENARIOS))
    bird = args.bird or SCENARIOS[scenario]["bird"]
    umbrella = args.umbrella or rng.choice(list(UMBRELLAS))
    if not valid_combo(bird, umbrella, scenario):
        raise StoryError(explain_rejection(bird, umbrella, scenario))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    if args.helper:
        helper_name = args.helper
        helper_role = args.role or "helper"
    else:
        helper_name, helper_role = rng.choice(HELPERS)
        helper_role = args.role or helper_role

    return StoryParams(
        child_name=name,
        child_gender=gender,
        helper_name=helper_name,
        helper_role=helper_role,
        bird=bird,
        umbrella=umbrella,
        scenario=scenario,
        opening_variant=rng.randrange(len(OPENINGS)),
        surprise_variant=rng.randrange(len(SURPRISES)),
        ending_variant=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) meters={meters} memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(
            child_name="Luna",
            child_gender="girl",
            helper_name="Mara",
            helper_role="captain",
            bird="crow",
            umbrella="red",
            scenario="watchtower",
        ),
        StoryParams(
            child_name="Leo",
            child_gender="boy",
            helper_name="Tomas",
            helper_role="gatekeeper",
            bird="swallow",
            umbrella="blue",
            scenario="gatehouse",
        ),
        StoryParams(
            child_name="Mira",
            child_gender="girl",
            helper_name="Suri",
            helper_role="cook",
            bird="sparrow",
            umbrella="yellow",
            scenario="supply_yard",
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.scenario} at the hill garrison"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
