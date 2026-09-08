#!/usr/bin/env python3
"""
A small fable world about a tricycle in a museum gallery, where a twist
teaches that looking again can reveal a better way forward.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the museum gallery"
    hero: str = "Luna"
    helper: str = "Pip"
    curator: str = "the curator"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "the museum gallery": {
        "tags": {"museum", "gallery", "history"},
        "mood": "quiet and golden",
    },
    "the old museum hall": {
        "tags": {"museum", "gallery", "echo"},
        "mood": "wide and echoing",
    },
    "the children's museum gallery": {
        "tags": {"museum", "gallery", "play"},
        "mood": "bright and curious",
    },
}


@dataclass(frozen=True)
class FableArc:
    title: str
    premise: str
    problem: str
    twist: str
    action: str
    result: str
    ending: str
    problem_answer: str
    twist_answer: str
    result_answer: str


ARCS = [
    FableArc(
        title="The Wheel That Pointed Backward",
        premise="In the museum gallery stood a small red tricycle whose brass bell had not rung for many years.",
        problem="When Luna tried to roll it toward the exit, one wheel turned backward and blocked the narrow display path.",
        twist="Pip noticed that the backward wheel was not broken at all: it pointed toward a dusty button beneath the display case.",
        action="Luna pressed the button, and the tricycle's front lamp shone on a fallen label that belonged to a lost photograph.",
        result="The curator returned the label to the photograph, and the tricycle rolled forward as easily as a leaf in a breeze.",
        ending="the red tricycle rested beneath its photograph, with its bell giving one bright ring",
        problem_answer="A wheel on the red tricycle turned backward and blocked the display path.",
        twist_answer="Pip discovered that the backward wheel was pointing toward a hidden button and a lost museum label.",
        result_answer="Finding the lost label restored the exhibit, and the tricycle rolled forward again.",
    ),
    FableArc(
        title="The Bell Behind the Painting",
        premise="A silver tricycle waited beside a large painting of a rainy village.",
        problem="Visitors heard a bell whenever they passed, but no one could find who was ringing it.",
        twist="Luna turned the tricycle around and saw that its rear wheel was touching the frame of the painting.",
        action="She moved the tricycle gently, and a tiny bell hidden behind the painting rang to reveal a loose corner of canvas.",
        result="The curator repaired the painting, while the tricycle became the first clue in the gallery's mystery tour.",
        ending="children followed a trail of small brass bells from the tricycle to the smiling village in the painting",
        problem_answer="A mysterious bell rang near the silver tricycle, but visitors could not find its source.",
        twist_answer="Luna saw that the tricycle's rear wheel was touching the painting's frame.",
        result_answer="Moving the tricycle revealed a hidden bell and helped the curator repair the painting.",
    ),
    FableArc(
        title="The Three-Wheeled Shortcut",
        premise="A green tricycle stood before a long row of paintings in the museum gallery.",
        problem="Luna wanted to see every picture, but a velvet rope made the usual path too crowded for her and Pip.",
        twist="Instead of squeezing ahead, Pip looked behind the rope and found a round viewing mirror facing the paintings.",
        action="They used the mirror to see the pictures from a quiet corner beside the tricycle.",
        result="They noticed a tiny painted bird that appeared in every scene, and the curator explained that it was the artist's secret signature.",
        ending="the tricycle's three wheels shone in the mirror beside three painted birds",
        problem_answer="A crowded velvet-rope path made it difficult for Luna and Pip to see every painting.",
        twist_answer="Pip found a viewing mirror that offered a new way to see the paintings from a quiet corner.",
        result_answer="The mirror helped them discover the artist's bird signature in every painting.",
    ),
    FableArc(
        title="The Tricycle and the Sleeping Clock",
        premise="An old blue tricycle sat beneath a clock that had stopped at noon.",
        problem="The gallery lights were about to dim, and the curator feared visitors would miss the clock's story.",
        twist="Luna saw that the tricycle's handlebar shadow pointed exactly at a small winding key.",
        action="She asked permission to use the key, and Pip held the lamp while the curator wound the clock.",
        result="The clock began ticking, and its gentle chime guided everyone safely through the dim gallery.",
        ending="the blue tricycle waited under a clock that now counted every bright hour",
        problem_answer="A stopped clock threatened to leave visitors without the story of the gallery's oldest exhibit.",
        twist_answer="The tricycle's handlebar shadow pointed to a hidden winding key.",
        result_answer="With permission and teamwork, the key restarted the clock and guided visitors through the gallery.",
    ),
    FableArc(
        title="The Smallest Guide",
        premise="A yellow tricycle was the smallest object in a gallery filled with enormous machines.",
        problem="Luna and Pip could not find the room where the museum kept its oldest map.",
        twist="The tricycle's tiny tire tracks led away from the large machines and toward a low door behind a curtain.",
        action="They followed the tracks instead of choosing the grandest hallway.",
        result="Behind the door they found the map, and learned that small clues can guide people through big places.",
        ending="the yellow tricycle stood beside the old map, its little tracks drawn in dust like a path",
        problem_answer="Luna and Pip could not find the room containing the museum's oldest map.",
        twist_answer="Tiny tire tracks from the tricycle led to a low door hidden behind a curtain.",
        result_answer="Following the small clue led them to the map and taught them to value quiet signs.",
    ),
    FableArc(
        title="The Wheel of Patience",
        premise="A wooden tricycle had one wheel that squeaked whenever someone hurried past it.",
        problem="The squeak annoyed visitors, and the curator planned to move the tricycle into storage.",
        twist="Luna slowed down and discovered that the squeak sounded only when the wheel crossed a loose floorboard.",
        action="She told the curator, who lifted the board and found a child's forgotten marble beneath it.",
        result="After the floor was repaired, the tricycle became quiet, and the marble returned to the child who had lost it.",
        ending="the wooden tricycle rolled silently while a blue marble gleamed beside its wheel",
        problem_answer="A squeaky wheel annoyed visitors, and the curator considered putting the wooden tricycle away.",
        twist_answer="Luna learned that the squeak came from a loose floorboard, not from the tricycle itself.",
        result_answer="Repairing the floor stopped the squeak and returned a lost marble to its owner.",
    ),
    FableArc(
        title="The Mirror's Second Story",
        premise="A polished tricycle stood before a mirror that seemed to show an empty gallery.",
        problem="Pip thought the mirror was cracked because the tricycle appeared in it without its handlebars.",
        twist="Luna stepped to the side and saw that the mirror showed the tricycle from behind, where the handlebars were hidden.",
        action="They changed places with the mirror, then found a small painted message on the back of the handlebars.",
        result="The message told them where to find the museum's missing friendship medal.",
        ending="the tricycle faced the mirror, and both reflections seemed ready to share a ride",
        problem_answer="Pip thought a mirror was cracked because it showed the tricycle without its handlebars.",
        twist_answer="Luna realized that the mirror was showing the tricycle from behind.",
        result_answer="Changing their viewpoint revealed a message that led to the missing friendship medal.",
    ),
    FableArc(
        title="The Curator's Quiet Race",
        premise="A bright tricycle rested in the center of the gallery as part of an exhibit about old games.",
        problem="Luna and Pip argued about who should push it first, and their voices made the nearby glass cases tremble.",
        twist="The curator placed two ribbons on the floor and explained that the race was not against each other but against their impatience.",
        action="The children took turns pushing the tricycle slowly, stopping whenever the bell rang.",
        result="They reached the finish together and learned that careful teamwork could be faster than a quarrel.",
        ending="two ribbons crossed beneath the tricycle, and both children held the bell rope",
        problem_answer="Luna and Pip argued over who should push the tricycle, disturbing the nearby exhibits.",
        twist_answer="The curator changed the race into a challenge against impatience rather than against each other.",
        result_answer="Taking turns let the children finish together and work more smoothly than they had while arguing.",
    ),
    FableArc(
        title="The Exhibit That Moved",
        premise="A black tricycle stood beside a sign that said, 'Please do not touch.'",
        problem="A breeze moved the sign until it covered the name of the artist.",
        twist="Pip noticed that the sign was meant to protect the artwork, not hide its name, and asked the curator for help.",
        action="The curator secured the sign and invited the children to look closely without touching the tricycle.",
        result="They read the artist's name and saw that the tricycle had been made for a child who loved exploring.",
        ending="the black tricycle remained untouched, while its artist's name shone clearly beside it",
        problem_answer="A breeze pushed the museum sign over the artist's name beside the black tricycle.",
        twist_answer="Pip understood that the sign protected the exhibit but had accidentally hidden its name.",
        result_answer="With the curator's help, they secured the sign and learned the tricycle's personal history.",
    ),
]


OPENINGS = [
    "One quiet morning, {hero} and {helper} entered {setting}.",
    "In {setting}, where old things waited for new eyes, {hero} walked beside {helper}.",
    "The lamps glowed softly in {setting} when {hero} noticed a tricycle near the center of the room.",
    "A fable began in {setting}, with {hero}, {helper}, and a tricycle that seemed to know more than it said.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.helper, params.curator))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _lower(text: str) -> str:
    return text[:1].lower() + text[1:]


def _story_lines(world: World) -> list[str]:
    f = world.facts
    arc: FableArc = f["arc"]
    opening = _fill(OPENINGS[f["opening_variant"]], f)
    premise = _fill(arc.premise, f)
    problem = _fill(arc.problem, f)
    twist = _fill(arc.twist, f)
    action = _fill(arc.action, f)
    result = _fill(arc.result, f)
    ending = _fill(arc.ending, f)
    hero = f["hero"]
    helper = f["helper"]
    curator = f["curator"]

    structures = [
        [
            opening,
            f"{premise} {problem}",
            f"\"Something is wrong,\" said {hero}. {twist}",
            f"\"Then we should look again,\" said {helper}. {action}",
            f"{result} {curator.capitalize()} smiled and said, \"A careful eye can find a kind answer.\"",
            f"At closing time, {ending}. The gallery remembered that a twist can open a new path.",
        ],
        [
            opening,
            f"The trouble began quietly. {problem} {premise}",
            f"\"Should we give up?\" asked {helper}. \"Not yet,\" said {hero}. {_cap(twist)}",
            action,
            f"{result} The curator thanked them for changing their view instead of blaming the old exhibit.",
            f"After that day, {ending}.",
        ],
        [
            f"{opening} They did not know that the day would become a favorite fable.",
            premise,
            f"Then came the puzzle: {problem}",
            f"{hero} frowned, but {helper} pointed to a detail everyone else had missed. {twist}",
            f"\"Let's try the gentle way,\" said {hero}. {action}",
            f"{result} The lesson was plain: a twist is not always a setback; sometimes it is an invitation to notice more.",
            f"That evening, {ending}.",
        ],
        [
            f"The oldest guide in {setting} begins with {hero} and {helper} standing near a tricycle.",
            f"{_cap(premise)} Soon, {_lower(problem)}",
            f"{curator.capitalize()} asked, \"What will you do when the first answer seems wrong?\"",
            f"{hero} answered, \"We will look from another side.\" {twist}",
            action,
            f"{result} Everyone saw the exhibit differently after that.",
            f"The final picture showed that {ending}.",
        ],
        [
            opening,
            f"Many visitors hurried past. {premise} But {problem}",
            f"\"Wait,\" said {helper}. \"The tricycle may be showing us something.\" {twist}",
            action,
            f"{result} The curator placed a small card nearby: \"Look twice, care once.\"",
            f"By sunset, {ending}. That was how the museum learned a fable about patience and a useful twist.",
        ],
    ]
    return structures[f["structure_variant"]]


ASP_RULES = r"""
setting(museum_gallery).
setting(old_museum_hall).
setting(childrens_museum_gallery).

feature(tricycle).
feature(twist).
style(fable).

can_tell_story(S) :-
    setting(S),
    feature(tricycle),
    feature(twist),
    style(fable).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.replace("the ", "").replace("children's ", "childrens_").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    lines.extend(
        [
            asp.fact("feature", "tricycle"),
            asp.fact("feature", "twist"),
            asp.fact("style", "fable"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fable about a tricycle and a twist in a museum gallery."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--curator")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Luna", "Milo", "Nia", "Theo", "Ada"])
    helper = args.helper or rng.choice(["Pip", "Bram", "Suki", "Ollie", "Mara"])
    curator = args.curator or rng.choice(
        ["the curator", "Ms. Vale", "the gallery keeper"]
    )
    if hero == helper:
        raise StoryError("The hero and helper must be different characters.")
    if not hero.strip() or not helper.strip():
        raise StoryError("Hero and helper names must not be empty.")
    return StoryParams(
        setting=setting,
        hero=hero,
        helper=helper,
        curator=curator,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown museum setting: {params.setting}")
    if params.hero == params.helper:
        raise StoryError("The hero and helper must be different characters.")

    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(
        Entity(
            name=params.hero,
            kind="child",
            meters={"attention": 0.7, "patience": 0.6},
            memes={"curiosity": 1.0, "care": 0.8},
        )
    )
    helper = world.add(
        Entity(
            name=params.helper,
            kind="child",
            meters={"attention": 0.8, "patience": 0.7},
            memes={"observation": 1.0, "friendship": 0.8},
        )
    )
    curator = world.add(
        Entity(
            name=params.curator,
            kind="adult",
            meters={"knowledge": 1.0},
            memes={"stewardship": 1.0},
        )
    )
    tricycle = world.add(
        Entity(
            name="the museum tricycle",
            kind="artifact",
            meters={"wheels": 3.0, "motion": 0.4, "age": 0.9},
            memes={"memory": 1.0, "clue": 1.0},
        )
    )
    world.add(
        Entity(
            name="the gallery",
            kind="place",
            meters={"room": 1.0, "light": 0.8},
            memes={"history": 1.0, "wonder": 1.0},
        )
    )

    world.facts.update(
        hero=hero.name,
        helper=helper.name,
        curator=curator.name,
        setting=params.setting,
        arc=arc,
        opening_variant=(seed // len(ARCS)) % len(OPENINGS),
        structure_variant=(seed // (len(ARCS) * len(OPENINGS))) % 5,
        problem=_fill(
            arc.problem,
            {
                "hero": hero.name,
                "helper": helper.name,
                "curator": curator.name,
                "setting": params.setting,
            },
        ),
        twist=_fill(
            arc.twist,
            {
                "hero": hero.name,
                "helper": helper.name,
                "curator": curator.name,
                "setting": params.setting,
            },
        ),
        action=_fill(
            arc.action,
            {
                "hero": hero.name,
                "helper": helper.name,
                "curator": curator.name,
                "setting": params.setting,
            },
        ),
        result=_fill(
            arc.result,
            {
                "hero": hero.name,
                "helper": helper.name,
                "curator": curator.name,
                "setting": params.setting,
            },
        ),
        ending=_fill(
            arc.ending,
            {
                "hero": hero.name,
                "helper": helper.name,
                "curator": curator.name,
                "setting": params.setting,
            },
        ),
        theme="tricycle, museum gallery, twist, curiosity, and care",
    )

    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a short fable about {params.hero}, {params.helper}, and a tricycle in {params.setting}.",
        "Tell a child-facing museum story where a twist changes what the characters decide to do.",
        "Write a gentle fable about looking twice before judging an old exhibit.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.helper} face in \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="What twist changed how the characters understood the problem?",
            answer=arc.twist_answer,
        ),
        QAItem(
            question=f"What changed because of the children's careful action?",
            answer=arc.result_answer,
        ),
        QAItem(
            question=f"What final image closes the fable \"{arc.title}\"?",
            answer=f"The fable ends with an image of {world.facts['ending']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a tricycle?",
            answer="A tricycle is a vehicle with three wheels, often moved by pedals."
        ),
        QAItem(
            question="What is a museum gallery?",
            answer="A museum gallery is a room where people can carefully view and learn about exhibits."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change that makes people understand a situation in a new way."
        ),
        QAItem(
            question="Why should people be careful around museum exhibits?",
            answer="People should be careful so old and valuable objects remain safe for everyone to study and enjoy."
        ),
        QAItem(
            question="What lesson does this fable teach?",
            answer="It teaches that looking carefully and considering another possibility can turn a puzzling problem into a helpful discovery."
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )
    if qa:
        print()
        print("== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _valid_python() -> list[str]:
    return sorted(
        setting.replace("the ", "")
        .replace("children's ", "childrens_")
        .replace(" ", "_")
        for setting in SETTING_REGISTRY
    )


def _asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    try:
        python_values = {(setting,) for setting in _valid_python()}
        clingo_values = set(_asp_valid())
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 1

    if python_values != clingo_values:
        print("MISMATCH between clingo and python:")
        print("python only:", sorted(python_values - clingo_values))
        print("clingo only:", sorted(clingo_values - python_values))
        return 1

    rng = random.Random(17)
    for _ in range(3):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story or "tricycle" not in sample.story.lower():
            print("MISMATCH: generated story failed the tricycle content check.")
            return 1

    print(f"OK: clingo gate matches python ({len(python_values)} settings).")
    return 0


def generation_prompts(sample: StorySample) -> list[str]:
    return sample.prompts


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            for item in _asp_valid():
                print(item[0])
        except ImportError:
            print("ASP mode unavailable: clingo is not installed.")
            sys.exit(1)
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            params = StoryParams(
                setting=setting,
                hero="Luna",
                helper="Pip",
                curator="the curator",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and index < limit:
            current_seed = base_seed + index
            index += 1
            rng = random.Random(current_seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            params.seed = current_seed
            sample = generate(params)
            if sample.story in seen:
                continue
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
