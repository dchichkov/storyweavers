#!/usr/bin/env python3
"""
A heartwarming parade story world about a sailor, infantry friends, and a tender twist.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    sailor_name: str
    infantry_name: str
    child_name: str
    parade_place: str
    seed: Optional[int] = None


@dataclass
class World:
    sailor: Person
    infantry: Person
    child: Person
    parade_place: str
    banner_state: str = "ready"
    secret_plan: bool = False
    twist_revealed: bool = False
    heart_state: str = "hopeful"
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Mara", "Pip", "Theo", "Nia", "Sol", "Ari", "June"]
PLACES = [
    "the town square",
    "the riverside road",
    "the schoolyard",
    "the harbor street",
    "the maple avenue",
]

SCENES = [
    {
        "title": "the quiet drum",
        "setup": "the parade drums began to echo between the houses",
        "problem": "the sailor's drum stayed silent",
        "clue": "a tiny ribbon was tied around the drumstick",
        "twist": "the sailor had saved the first beat for a child who could not hear the opening fanfare but could feel a drum against the ground",
        "repair": "set the drum on a wooden platform and invited the child to feel each gentle beat",
        "ending": "the whole parade marched to a rhythm that traveled through the platform and into two smiling hands",
    },
    {
        "title": "the missing flag",
        "setup": "the infantry line gathered beneath bright flags for the parade",
        "problem": "one sailor's blue flag seemed to have vanished",
        "clue": "a blue thread led behind the reviewing stand",
        "twist": "the sailor had not lost the flag; it had been sewn into a blanket for a veteran resting nearby",
        "repair": "carried the blanket carefully and asked the infantry to make room beside the band",
        "ending": "the flag waved from the blanket while the veteran watched the parade from a sunny chair",
    },
    {
        "title": "the late salute",
        "setup": "the sailor and infantry marched toward the town square",
        "problem": "the sailor reached the salute a moment late",
        "clue": "the sailor kept glancing toward a narrow side street",
        "twist": "the sailor was waiting for an elderly neighbor who had once taught the whole crew how to tie safe harbor knots",
        "repair": "paused the line long enough for the neighbor to join the salute",
        "ending": "the parade moved again with the neighbor riding proudly at the front beside the infantry",
    },
    {
        "title": "the crooked banner",
        "setup": "a large welcome banner hung above the parade route",
        "problem": "the banner looked crooked, and everyone thought the sailor had tied it badly",
        "clue": "one corner had been lowered on purpose",
        "twist": "the sailor had made space for a small girl in a wheelchair to see the marching musicians",
        "repair": "asked the infantry to hold the banner higher on the other side",
        "ending": "the banner stayed welcoming, and the girl had a clear view of every shining instrument",
    },
    {
        "title": "the empty place",
        "setup": "the infantry formed a neat line while the parade waited for its sailor escort",
        "problem": "an empty place near the front made the group seem incomplete",
        "clue": "a folded paper boat rested on the empty spot",
        "twist": "the sailor had left the place for a young helper whose parent had once marched there",
        "repair": "opened the line and offered the child a small sailor's cap",
        "ending": "the empty place became the brightest place as the child marched between sailor and infantry",
    },
]

OPENINGS = [
    "On a clear morning,",
    "Before the first brass note,",
    "As sunlight warmed the parade route,",
    "At the edge of a bright town celebration,",
    "While neighbors gathered along the road,",
]

REACTIONS = [
    "Luna frowned, then asked, \"Are we sure that is the whole story?\"",
    "The infantry friend lowered their voice. \"Maybe the pause is helping someone,\" they said.",
    "The child looked closely. \"What is that clue telling us?\"",
    "For a moment everyone worried. Then the sailor said, \"Let us look before we hurry.\"",
]

LESSONS = [
    "The parade taught them that a slower step can make room for someone important.",
    "They learned that kindness may look like a mistake until the hidden reason appears.",
    "The finest salute was not the loudest one, but the one that included another heart.",
    "A parade is made of people, not only uniforms, flags, and marching feet.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming sailor and infantry parade story world.")
    parser.add_argument("--sailor-name", choices=NAMES)
    parser.add_argument("--infantry-name", choices=NAMES)
    parser.add_argument("--child-name", choices=NAMES)
    parser.add_argument("--parade-place", choices=PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    sailor = args.sailor_name or rng.choice(NAMES)
    remaining = [name for name in NAMES if name != sailor]
    infantry = args.infantry_name or rng.choice(remaining)
    remaining = [name for name in remaining if name != infantry]
    child = args.child_name or rng.choice(remaining)
    return StoryParams(
        sailor_name=sailor,
        infantry_name=infantry,
        child_name=child,
        parade_place=args.parade_place or rng.choice(PLACES),
    )


def _reasonableness_gate(params: StoryParams) -> None:
    names = [params.sailor_name, params.infantry_name, params.child_name]
    if len(set(names)) != len(names):
        raise StoryError("The sailor, infantry friend, and child need different names.")
    if params.parade_place not in PLACES:
        raise StoryError("That parade place is not part of this small town world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = rng.choice(SCENES)
    opening = rng.choice(OPENINGS)
    reaction = rng.choice(REACTIONS).replace("Luna", params.child_name)
    lesson = rng.choice(LESSONS)

    sailor = Person(
        params.sailor_name,
        "sailor",
        meters={"distance_to_parade": 0.0, "care": 0.9},
        memes={"loyalty": 1.0, "tenderness": 1.0},
    )
    infantry = Person(
        params.infantry_name,
        "infantry",
        meters={"line_spacing": 1.0, "distance_to_child": 2.0},
        memes={"steadiness": 1.0, "kindness": 0.8},
    )
    child = Person(
        params.child_name,
        "child",
        meters={"distance_to_front": 3.0, "belonging": 0.4},
        memes={"curiosity": 1.0, "hope": 0.8},
    )
    world = World(sailor, infantry, child, params.parade_place)

    lines = [
        f"{opening} {params.parade_place} filled with neighbors waiting for a colorful parade.",
        f"{params.sailor_name}, a sailor with a bright cap, stood beside {params.infantry_name}, who marched with the infantry.",
        f"{params.child_name} watched from the edge of the route, wishing to feel part of the celebration.",
        f"Then {scene['setup']}, but {scene['problem']}.",
        reaction,
        f"{params.infantry_name} noticed {scene['clue']} and held up a hand so nobody would rush.",
        f"The sailor smiled and explained the twist: {scene['twist']}.",
        f"That changed the plan. {params.sailor_name} {scene['repair']}.",
        f"{params.child_name} asked, \"May I join you?\"",
        f"\"Of course,\" said {params.infantry_name}. \"A parade is better when everyone has a place.\"",
        f"{params.sailor_name} nodded. \"And every brave march should carry kindness with it.\"",
        lesson,
        f"At last, {scene['ending']}.",
    ]

    world.banner_state = "shared with the community"
    world.secret_plan = True
    world.twist_revealed = True
    world.heart_state = "included"
    world.facts.update(
        {
            "scene": scene["title"],
            "problem": scene["problem"],
            "clue": scene["clue"],
            "twist": scene["twist"],
            "repair": scene["repair"],
            "ending": scene["ending"],
            "lesson": lesson,
        }
    )
    story = " ".join(lines)
    world.facts["story"] = story

    prompts = [
        f"Write a heartwarming parade story called {scene['title']} with a sailor and infantry friend.",
        f"Tell a story at {params.parade_place} where a parade problem has a kind twist.",
        f"Show how {params.sailor_name}, {params.infantry_name}, and {params.child_name} make room for one another.",
    ]

    story_qa = [
        QAItem(
            question=f"What seemed to go wrong during the parade in {scene['title']}?",
            answer=f"It seemed that {scene['problem']}.",
        ),
        QAItem(
            question="What clue helped the characters slow down and investigate?",
            answer=f"They noticed that {scene['clue']}.",
        ),
        QAItem(
            question="What was the heartwarming twist?",
            answer=f"The twist was that {scene['twist']}.",
        ),
        QAItem(
            question="How did the sailor and infantry repair the situation?",
            answer=f"They {scene['repair']}.",
        ),
        QAItem(
            question="How did the ending show that the child belonged?",
            answer=f"{scene['ending']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized celebration in which people move along a route while others watch, cheer, or join in.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works or travels on a boat or ship and learns how to stay safe on the water.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry means soldiers who serve and move on foot as part of an organized group.",
        ),
        QAItem(
            question="Why can a twist make a story heartwarming?",
            answer="A twist can be heartwarming when it reveals that an apparent problem came from a thoughtful act or leads people to include and care for one another.",
        ),
        QAItem(
            question="What should people do when they do not understand a situation?",
            answer="They should pause, look for clues, ask a respectful question, and avoid blaming someone before they know what happened.",
        ),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        world = sample.world
        print("\n--- trace ---")
        print(f"sailor={world.sailor.name}, kind={world.sailor.kind}, meters={world.sailor.meters}, memes={world.sailor.memes}")
        print(f"infantry={world.infantry.name}, kind={world.infantry.kind}, meters={world.infantry.meters}, memes={world.infantry.memes}")
        print(f"child={world.child.name}, kind={world.child.kind}, meters={world.child.meters}, memes={world.child.memes}")
        print(f"place={world.parade_place}, banner_state={world.banner_state}, secret_plan={world.secret_plan}, twist_revealed={world.twist_revealed}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
valid_place(P) :- place(P).
parade_ready(P) :- valid_place(P).
twist_possible(P) :- parade_ready(P).
included(P) :- twist_possible(P).

#show valid_place/1.
#show parade_ready/1.
#show twist_possible/1.
#show included/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("place", place) for place in PLACES)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    expected = {(place,) for place in PLACES}
    actual = set(asp_valid_places())
    if expected == actual:
        print(f"OK: clingo gate matches parade places ({len(expected)} places).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if expected - actual:
        print("  only in python:", sorted(expected - actual))
    if actual - expected:
        print("  only in clingo:", sorted(actual - expected))
    return 1


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                sailor_name=NAMES[i % len(NAMES)],
                infantry_name=NAMES[(i + 1) % len(NAMES)],
                child_name=NAMES[(i + 2) % len(NAMES)],
                parade_place=place,
            )
            for i, place in enumerate(PLACES)
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show valid_place/1.\n"
            "#show parade_ready/1.\n"
            "#show twist_possible/1.\n"
            "#show included/1."
        ))
        return

    if args.verify:
        result = asp_verify()
        if result == 0:
            for params in generation_params(argparse.Namespace(
                sailor_name=None,
                infantry_name=None,
                child_name=None,
                parade_place=None,
                all=False,
                seed=17,
                n=5,
            )):
                generate(params)
            print("OK: generated stories passed the Python reasonableness gate.")
        sys.exit(result)

    if args.asp:
        import asp
        model = asp.one_model(asp_program(
            "#show valid_place/1.\n"
            "#show parade_ready/1.\n"
            "#show twist_possible/1.\n"
            "#show included/1."
        ))
        for predicate in ("valid_place", "parade_ready", "twist_possible", "included"):
            for atom in sorted(asp.atoms(model, predicate)):
                print(f"{predicate}({atom[0]})")
        return

    params_list = generation_params(args)
    samples = []
    for index, params in enumerate(params_list):
        params.seed = (args.seed if args.seed is not None else 0) + index
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
