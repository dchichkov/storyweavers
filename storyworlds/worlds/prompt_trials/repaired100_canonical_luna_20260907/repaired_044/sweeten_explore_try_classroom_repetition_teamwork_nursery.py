#!/usr/bin/env python3
"""
A small nursery-rhyme classroom world about trying, exploring, and sweetening
a difficult task through repetition and teamwork.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("confidence", "order", "noise", "clarity"):
            self.meters.setdefault(key, 0.0)
        for key in ("joy", "frustration", "curiosity", "trust", "patience"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Place:
    name: str
    indoor: bool = True


@dataclass(frozen=True)
class Trial:
    id: str
    object_name: str
    challenge: str
    first_mistake: str
    clue: str
    repeated_action: str
    discovery: str
    sweetener: str
    ending: str
    lesson: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


PLACES = {
    "classroom": Place("the classroom"),
}

STUDENTS = {
    "Luna": {"kind": "rabbit", "trait": "bright"},
    "Milo": {"kind": "mouse", "trait": "thoughtful"},
    "Nia": {"kind": "fox", "trait": "curious"},
    "Pip": {"kind": "sparrow", "trait": "cheerful"},
    "Tess": {"kind": "turtle", "trait": "steady"},
}

TRIALS = {
    "paper_star": Trial(
        id="paper_star",
        object_name="a paper star",
        challenge="folded a paper star whose points would not meet",
        first_mistake="folded faster and made the corners flap like little wings",
        clue="one crease was leaning left while all the others leaned right",
        repeated_action="opened the star, matched one crease at a time, and tried the fold again",
        discovery="the paper became a star when every small crease joined its neighbor",
        sweetener="a golden dab of paste and a song with the same line repeated",
        ending="The paper star shone above the reading rug, with five neat points waving in the warm classroom air.",
        lesson="Small tries become strong when patient friends repeat them together.",
    ),
    "seed_box": Trial(
        id="seed_box",
        object_name="a tiny seed box",
        challenge="made a seed box that would close without spilling its beans",
        first_mistake="pressed the lid hard and sent three beans rolling under the desks",
        clue="the box had one tab tucked beneath the wrong flap",
        repeated_action="retrieved the beans, moved the tab, and tried the lid again",
        discovery="the little box held firm when the tabs took turns",
        sweetener="a cheerful label and a gentle counting chant",
        ending="The seed box rested on the windowsill, guarding its beans while sunlight painted squares on the floor.",
        lesson="Teamwork gives every small part a turn.",
    ),
    "rhythm_card": Trial(
        id="rhythm_card",
        object_name="a rhythm card",
        challenge="arranged a rhythm card for the class drum",
        first_mistake="tapped every mark at once until the beat became a tumble",
        clue="the quiet mark was meant to be a pause, not another tap",
        repeated_action="read the marks aloud, paused at the quiet sign, and tried the beat again",
        discovery="the rhythm sounded clear when listening came between the taps",
        sweetener="a soft humming line and three careful practice rounds",
        ending="The class drum gave a gentle boom, and every child joined on the final bright beat.",
        lesson="A pause can help a good idea speak clearly.",
    ),
    "rainbow_map": Trial(
        id="rainbow_map",
        object_name="a rainbow map",
        challenge="drew a rainbow map to the classroom book corner",
        first_mistake="colored the arrows in a hurry and pointed them all toward the supply shelf",
        clue="the footprints began beside the window, not beside the shelf",
        repeated_action="followed the footprints, erased one arrow, and tried the route again",
        discovery="the map worked when each arrow followed a real clue",
        sweetener="a bright border and a rhyme about looking twice",
        ending="The rainbow map led everyone to the book corner, where a blue book waited like a small sky.",
        lesson="Careful exploring turns a mixed-up path into a friendly guide.",
    ),
}


ASP_RULES = r"""
reason(P) :- classroom(P).
has_trial(T) :- trial(T).
has_repeat(T) :- repeats(T).
has_teamwork(T) :- teamwork(T).
has_sweeten(T) :- sweetens(T).
valid_story(P,T) :- reason(P), has_trial(T), has_repeat(T), has_teamwork(T), has_sweeten(T).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("classroom", place_id) for place_id in PLACES]
    for trial_id in TRIALS:
        lines.extend(
            [
                asp.fact("trial", trial_id),
                asp.fact("repeats", trial_id),
                asp.fact("teamwork", trial_id),
                asp.fact("sweetens", trial_id),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


@dataclass
class StoryParams:
    place: str
    trial: str
    hero: str
    helper: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("The chosen setting is not the classroom.")
    if params.trial not in TRIALS:
        raise StoryError("The chosen classroom trial is not available.")
    if params.hero not in STUDENTS:
        raise StoryError("The chosen hero is not one of the classroom children.")
    if params.helper not in STUDENTS:
        raise StoryError("The chosen helper is not one of the classroom children.")
    if params.hero == params.helper:
        raise StoryError("The hero and helper must be different children.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else repr(params))
    trial = TRIALS[params.trial]
    place = PLACES[params.place]
    world = World(place)

    hero_info = STUDENTS[params.hero]
    helper_info = STUDENTS[params.helper]
    hero = world.add(Entity(params.hero, "student", params.hero))
    helper = world.add(Entity(params.helper, "student", params.helper))
    project = world.add(Entity("project", "classroom_object", trial.object_name))

    openings = [
        f"In {place.name}, Luna's class began the day with a bright little try.",
        f"At {place.name}, {params.hero} the {hero_info['kind']} opened the craft basket with a hop.",
        f"Morning bells rang in {place.name}, where {params.hero} and {params.helper} chose a classroom challenge.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"{params.hero} the {hero_info['kind']} and {params.helper} the {helper_info['kind']} "
        f"{trial.challenge}."
    )
    world.say(
        f"They sang, “Try, try, try once more; explore the clue beside the door!” "
        f"Then they placed the {trial.object_name} on the teamwork table."
    )
    world.para()

    hero.memes["curiosity"] += 1
    hero.memes["frustration"] += 1
    project.meters["noise"] += 1
    world.say(f"But the first try went crooked: {trial.first_mistake}.")
    world.say(f'"It will not work!" cried {params.hero}. "{trial.challenge.capitalize()} is too tricky."')
    world.say(
        f'"Let us not quit," said {params.helper}. '
        f'"We can explore one clue, try one change, and repeat the good part."'
    )
    world.para()

    helper.memes["patience"] += 1
    helper.memes["trust"] += 1
    hero.memes["frustration"] = 0
    hero.memes["curiosity"] += 1
    world.say(f"{params.helper} noticed that {trial.clue}.")
    world.say(
        f"Together they repeated the small classroom rhyme: "
        f"“Look, then try; try, then see; kind hands make a team of three!”"
    )
    world.say(f"They {trial.repeated_action}.")
    world.say(f"After the next try, they discovered that {trial.discovery}.")
    world.para()

    hero.meters["confidence"] += 2
    helper.meters["confidence"] += 2
    project.meters["clarity"] += 2
    hero.memes["joy"] += 2
    helper.memes["joy"] += 2
    world.say(
        f"The children decided to sweeten the task with {trial.sweetener}. "
        f"They smiled when the repeated words made the hard part feel smaller."
    )
    world.say(
        f'"We did not need one giant try," said {params.hero}. '
        f'"We needed many tiny tries."'
    )
    world.say(
        f'"And helping hands," added {params.helper}. '
        f'"That is what makes exploring feel safe."'
    )
    world.say(f"They cheered, “Try and explore, then sweeten the day; teamwork will show us the careful way!”")
    world.say(f"{trial.ending}")

    world.facts.update(
        place=params.place,
        trial=params.trial,
        hero=params.hero,
        helper=params.helper,
        hero_kind=hero_info["kind"],
        helper_kind=helper_info["kind"],
        object_name=trial.object_name,
        challenge=trial.challenge,
        first_mistake=trial.first_mistake,
        clue=trial.clue,
        repeated_action=trial.repeated_action,
        discovery=trial.discovery,
        sweetener=trial.sweetener,
        ending=trial.ending,
        lesson=trial.lesson,
        repetition=True,
        teamwork=True,
        explored=True,
        tried=True,
        sweetened=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a Nursery Rhyme-style classroom story about {f['hero']} and {f['helper']} trying to make {f['object_name']}.",
        f"Tell a child-friendly story where teamwork and repetition help {f['hero']} explore the clue that {f['clue']}.",
        f"Write a story using the words sweeten, explore, and try, ending with {f['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What were {f['hero']} and {f['helper']} trying to make?",
            answer=f"They were trying to make {f['object_name']}.",
        ),
        QAItem(
            question="What went wrong on the first try?",
            answer=f"On the first try, {f['first_mistake']}.",
        ),
        QAItem(
            question=f"What clue did {f['helper']} notice?",
            answer=f"{f['helper']} noticed that {f['clue']}.",
        ),
        QAItem(
            question="How did repetition and teamwork help?",
            answer=f"They {f['repeated_action']}, and the project improved because they worked together.",
        ),
        QAItem(
            question="How did the children sweeten the task?",
            answer=f"They sweetened it with {f['sweetener']}.",
        ),
        QAItem(
            question="What lesson did the classroom rhyme teach?",
            answer=f"It taught that {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying something again so it can become clearer or easier.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people helping one another toward the same goal.",
        ),
        QAItem(
            question="Why is it useful to explore a problem?",
            answer="Exploring helps us notice clues and understand what to try next.",
        ),
        QAItem(
            question="What does it mean to sweeten a difficult task?",
            answer="It means adding kindness, play, or encouragement so the task feels easier to face.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = ", ".join(
            f"{key}={value:g}" for key, value in entity.meters.items() if value
        )
        memes = ", ".join(
            f"{key}={value:g}" for key, value in entity.memes.items() if value
        )
        lines.append(f"{entity.id}: meters={{{meters}}} memes={{{memes}}}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery Rhyme classroom world about trying, exploring, repetition, and teamwork."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--trial", choices=sorted(TRIALS))
    parser.add_argument("--hero", choices=sorted(STUDENTS))
    parser.add_argument("--helper", choices=sorted(STUDENTS))
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
    hero = args.hero or rng.choice(sorted(STUDENTS))
    helper_choices = [name for name in sorted(STUDENTS) if name != hero]
    helper = args.helper or rng.choice(helper_choices)
    params = StoryParams(
        place=args.place or "classroom",
        trial=args.trial or rng.choice(sorted(TRIALS)),
        hero=hero,
        helper=helper,
    )
    reasonableness_gate(params)
    return params


CURATED = [
    StoryParams("classroom", "paper_star", "Luna", "Milo"),
    StoryParams("classroom", "seed_box", "Nia", "Tess"),
    StoryParams("classroom", "rhythm_card", "Pip", "Luna"),
    StoryParams("classroom", "rainbow_map", "Milo", "Nia"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_story"))
    expected = {(place, trial) for place in PLACES for trial in TRIALS}
    if found != expected:
        print("MISMATCH between ASP and Python registry gate.")
        print("ASP:", sorted(found))
        print("PY :", sorted(expected))
        return 1

    for params in CURATED:
        sample = generate(params)
        required = ("sweeten", "explore", "try")
        if not all(word in sample.story.lower() for word in required):
            print("MISMATCH: generated story omitted a required seed word.")
            return 1
        if "team" not in sample.story.lower():
            print("MISMATCH: generated story omitted teamwork language.")
            return 1

    print(f"OK: ASP gate and generated stories verified ({len(found)} story shapes).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} valid classroom story shapes:")
        for place, trial in values:
            print(f"  {place} / {trial}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = max(args.n * 20, 20)
        for offset in range(attempts):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            params.seed = seed
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
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.hero} and {params.helper} / {params.trial}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
