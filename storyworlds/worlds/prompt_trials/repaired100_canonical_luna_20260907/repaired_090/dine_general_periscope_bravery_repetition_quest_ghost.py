#!/usr/bin/env python3
"""
A small ghost-story world about a brave child, a repeating signal, and a
periscope that helps a quiet general find the way to a moonlit dinner.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
    fired: set[str] = field(default_factory=set)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    companion: str
    trait: str
    omen: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Omen:
    title: str
    opening: str
    danger: str
    first_try: str
    clue: str
    action: str
    twist: str
    resolution: str
    lesson: str
    ending: str
    question: str
    answer: str


NAMES = {
    "girl": ["Luna", "Mara", "Iris", "Nell"],
    "boy": ["Leo", "Owen", "Sam", "Pip"],
}
TRAITS = ["curious", "steady", "kind", "watchful", "brave"]
COMPANIONS = ["general", "grandmother", "uncle", "captain"]

OMENS = [
    Omen(
        "the window bell",
        "At the old hill house, a bell rang from an empty dining room.",
        "Luna wanted to dine with her family, but the bell kept calling from beyond a locked door.",
        "She opened the door once, saw only silver chairs, and hurried back when a cold breath touched her cheek.",
        "Through the periscope, she saw the bell's cord looped around a fallen portrait frame.",
        "She repeated the calm steps: look, breathe, lift. Then she moved the frame and freed the cord.",
        "The ghost was not hiding in the room; its repeated ringing was asking someone to notice the trapped cord.",
        "The bell grew quiet, and the family could dine while moonlight rested on the polished table.",
        "Bravery can be a careful choice repeated until fear becomes information.",
        "One last bell note trembled above a table set for everyone, living and unseen.",
        "Why did the bell keep ringing?",
        "Its cord was caught around a fallen portrait frame, so it rang whenever the frame shifted.",
    ),
    Omen(
        "the pale staircase",
        "A pale figure appeared at the top of the staircase each night before dinner.",
        "The general refused to dine until someone discovered why the ghost stood in the same place.",
        "The child called up the stairs, but the figure vanished and returned when the call was repeated.",
        "The periscope showed a bright patch on the wall behind the figure and a loose curtain above it.",
        "The child repeated a slow count while the general pulled the curtain open from the safe landing.",
        "The ghost was a moonlit reflection, repeated by the curtain's sway, not a spirit blocking the stairs.",
        "The staircase became ordinary again, and the general led everyone to dine.",
        "A repeated sight deserves a patient test before a frightened guess.",
        "The curtain hung still, and the last pale shape melted into a square of moonlight.",
        "What made the pale figure appear?",
        "A loose curtain repeated a moonlit reflection on the wall, making it look like a figure.",
    ),
    Omen(
        "the empty chair",
        "One chair at the dinner table slid backward whenever the room grew quiet.",
        "The general believed a ghost wanted the chair, so nobody dared dine near it.",
        "The child pushed it forward, but it rolled back with the same soft scrape.",
        "The periscope revealed a little wheel beneath the chair caught in a groove between floorboards.",
        "The child repeated the movement while the general placed a folded cloth under the wheel.",
        "The ghostly chair had a stubborn wheel; its scrape sounded like a visitor returning.",
        "The chair stayed put, and a warm bowl was set in front of it for the absent guest remembered in the portrait.",
        "Understanding a strange motion can make room for kindness.",
        "The empty chair no longer moved, but a spoon beside it shone in welcome.",
        "Why did the chair slide backward?",
        "A wheel beneath it was caught in a groove between the floorboards.",
    ),
    Omen(
        "the whispering soup",
        "A covered bowl whispered, 'Turn back,' whenever the general tried to dine.",
        "The words repeated so clearly that the general left the table untouched.",
        "The child lifted the lid quickly, but the whisper stopped before anyone could hear its source.",
        "The periscope showed a narrow crack in the serving cart and a reed whistle tucked behind it.",
        "The child repeated the lid lift slowly while the general held the cart still and found the whistle.",
        "The ghostly warning was wind passing through the whistle, repeating the cart's tiny movement.",
        "The soup was served, and the general thanked the strange little sound for pointing to a loose wheel.",
        "Listening closely can turn a frightening message into a useful clue.",
        "Steam curled above the soup while the silent whistle rested beside the salt.",
        "What made the soup seem to whisper?",
        "Wind passing through a hidden reed whistle made the cart repeat a whispering sound.",
    ),
]


def can_story(place: str, activity: str, prize: str) -> bool:
    return place == "manor" and activity == "dine" and prize == "periscope"


ASP_RULES = r"""
place(manor).
activity(dine).
prize(periscope).
feature(bravery).
feature(repetition).
feature(quest).
style(ghost_story).

compatible(P,A,R) :-
    place(P), activity(A), prize(R),
    P = manor, A = dine, R = periscope.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "manor"),
            asp.fact("activity", "dine"),
            asp.fact("prize", "periscope"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "repetition"),
            asp.fact("feature", "quest"),
            asp.fact("style", "ghost_story"),
        ]
    )


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("manor", "dine", "periscope")]


def tell(params: StoryParams) -> World:
    omen = OMENS[int(params.omen.rsplit("_", 1)[1])]
    world = World()
    child = world.add(
        Entity(
            "child",
            "character",
            params.name,
            memes={"bravery": 0.0, "fear": 1.0, "patience": 0.0},
        )
    )
    companion = world.add(
        Entity(
            "companion",
            "character",
            params.companion,
            memes={"trust": 0.0, "fear": 0.0},
        )
    )
    scope = world.add(
        Entity(
            "periscope",
            "instrument",
            "the brass periscope",
            meters={"clarity": 0.0},
        )
    )
    world.facts.update(child=child, companion=companion, periscope=scope, omen=omen)

    world.say("The old manor had a dining room where moonlight gathered like pale water.")
    world.say(
        f"{params.name}, a {params.trait} child, had promised to help the {params.companion} dine there."
    )
    world.say(
        "On the sideboard rested a brass periscope, an odd little instrument for looking around corners."
    )
    world.say(f'"If the house has a ghost, we can still find the truth," {params.name} said.')
    world.say(f'"And if we find it, we will not tease it," the {params.companion} replied.')
    world.para()

    world.say(omen.opening)
    world.say(omen.danger)
    world.say(
        f'"I am afraid," {params.name} admitted. "But I can take one careful step, then another."'
    )
    world.say(omen.first_try)
    child.memes["fear"] = 2.0
    child.memes["bravery"] = 1.0
    world.fired.add("fear_named")
    world.say(
        f'"Use the periscope," the {params.companion} said. "Look before you cross the dark."'
    )
    world.para()

    world.say(omen.clue)
    scope.meters["clarity"] = 1.0
    child.memes["patience"] = 1.0
    world.fired.add("periscope_clue")
    world.say(f'"I see something ordinary inside the scary thing," {params.name} said.')
    world.say(f'"Then repeat the test," said the {params.companion}. "Careful steps make a strong quest."')
    world.say(omen.action)
    world.fired.add("repetition")
    child.memes["bravery"] = 2.0
    child.memes["fear"] = 1.0
    world.para()

    world.say(omen.twist)
    world.say(
        f'"Bravery was not being unafraid," {params.name} said. '
        '"It was looking again without letting fear choose for me."'
    )
    world.say(omen.resolution)
    world.say(f"The quest left a lesson behind: {omen.lesson}")
    world.say(omen.ending)
    world.facts.update(
        title=omen.title,
        clue=omen.clue,
        twist=omen.twist,
        resolution=omen.resolution,
        lesson=omen.lesson,
        ending=omen.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    omen = world.facts["omen"]
    return [
        "Write a child-friendly Ghost Story about a brave quest to dine in an old manor.",
        f"Tell a story where {child.label} uses a periscope, Bravery, and Repetition to investigate {omen.title}.",
        f"Make the ghostly mystery change when this clue appears: {omen.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    companion = world.facts["companion"]
    omen = world.facts["omen"]
    return [
        QAItem(
            f"Why did {child.label} bring the periscope?",
            f"{child.label} used the brass periscope to look around corners and inspect the ghostly mystery safely.",
        ),
        QAItem(
            f"What did the {companion.label} tell {child.label} to do?",
            f"The {companion.label} told {child.label} to use the periscope and repeat the careful test.",
        ),
        QAItem(omen.question, omen.answer),
        QAItem(
            f"What was the Twist in {omen.title}?",
            omen.twist,
        ),
        QAItem(
            f"What did {child.label} learn during the quest?",
            omen.lesson,
        ),
        QAItem(
            "What final image showed that the mystery was settled?",
            omen.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a periscope?",
            "A periscope is an instrument that lets someone look over or around an obstacle.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery is choosing a careful, helpful action even when something feels frightening.",
        ),
        QAItem(
            "Why can repetition help solve a mystery?",
            "Repeating a careful test can show which part of a strange event stays the same and reveal its cause.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is a purposeful journey or search with a problem to solve.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.kind:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random, seed: int) -> StoryParams:
    if args.place and args.place != "manor":
        raise StoryError("This storyworld uses the old manor dining room.")
    if args.activity and args.activity != "dine":
        raise StoryError("This storyworld's activity must be dine.")
    if args.prize and args.prize != "periscope":
        raise StoryError("The quest requires the brass periscope.")
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Gender must be girl or boy.")
    if args.companion and args.companion not in COMPANIONS:
        raise StoryError("Choose a companion from the registered companions.")
    if args.trait and args.trait not in TRAITS:
        raise StoryError("Choose a registered child trait.")

    gender = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(
        place="manor",
        activity="dine",
        prize="periscope",
        name=args.name or rng.choice(NAMES[gender]),
        gender=gender,
        companion=args.companion or rng.choice(COMPANIONS),
        trait=args.trait or rng.choice(TRAITS),
        omen=f"omen_{seed % len(OMENS):02d}",
        seed=seed,
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
        description="A Ghost Story storyworld about dining, a general, and a periscope."
    )
    parser.add_argument("--place", choices=["manor"])
    parser.add_argument("--activity", choices=["dine"])
    parser.add_argument("--prize", choices=["periscope"])
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--name")
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--trait", choices=TRAITS)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if python_combos != asp_combos:
        print("MISMATCH between Python and ASP compatibility gates.")
        if python_combos - asp_combos:
            print("  only in Python:", sorted(python_combos - asp_combos))
        if asp_combos - python_combos:
            print("  only in ASP:", sorted(asp_combos - python_combos))
        return 1

    for seed in range(12):
        params = resolve_params(
            build_parser().parse_args(["--seed", str(seed)]),
            random.Random(seed),
            seed,
        )
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print("Generated-story verification failed.")
            return 1
        if "periscope" not in sample.story.lower():
            print("Generated-story verification failed: missing periscope.")
            return 1
        if '"' not in sample.story:
            print("Generated-story verification failed: missing dialogue.")
            return 1

    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed), base_seed)
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed), seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
