#!/usr/bin/env python3
"""
A small fable storyworld about a wolf who learns that kindness is funnier,
stronger, and more useful than frightening others.
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
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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
    companion: str
    trait: str
    incident: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    trouble: str
    failed_plan: str
    clue: str
    repair: str
    twist: str
    resolution: str
    lesson: str
    ending: str
    question: str
    answer: str


INCIDENTS = [
    Incident(
        "the upside-down howl",
        "Wolf wanted the forest animals to admire his loudest howl.",
        "He howled at a hollow log, but the log answered with a wobbling fart-like puff.",
        "A tiny mouse pointed out that the sound was coming from the log, not from Wolf's mighty throat.",
        "Wolf laughed at himself, helped the mouse clear leaves from the log, and invited everyone to make music together.",
        "The joke was not Wolf's booming howl but the hollow log's silly reply.",
        "The animals laughed with Wolf, and the cleared log became a cheerful drum for the forest band.",
        "A kind heart can turn an embarrassing noise into shared laughter.",
        "At sunset, the mouse tapped the log while Wolf howled in a gentle, musical rhythm.",
        "What made the funny puffing sound?",
        "The hollow log made the funny puffing sound when Wolf howled into it.",
    ),
    Incident(
        "the berry basket",
        "Wolf found a basket of berries that a rabbit had dropped beside the path.",
        "He planned to hide it and announce that a mysterious berry monster had stolen it.",
        "The berries left a red trail leading toward a worried rabbit under a fern.",
        "Wolf followed the trail, returned the basket, and carried the heaviest berries for the rabbit.",
        "The supposed berry monster was only Wolf's own muddy pawprint beside the basket.",
        "The rabbit shared a few berries, and Wolf became the forest's official basket carrier.",
        "Returning what is lost is better than making a grand trick from someone else's worry.",
        "The empty basket swung from Wolf's paw as the rabbit skipped safely beside him.",
        "Why was the rabbit worried?",
        "The rabbit was worried because the basket of berries had been dropped and could not be found.",
    ),
    Incident(
        "the tiny bridge",
        "Wolf wanted to cross a stream before the squirrels finished counting their acorns.",
        "He charged onto a little branch bridge, which bent until his tail pointed at the sky.",
        "A beaver showed him that the bridge had been built for small paws, not large ones.",
        "Wolf backed away, helped the beaver place strong branches, and waited while the bridge was repaired.",
        "The twist was that Wolf's proud tail made the best bridge marker in the whole forest.",
        "Everyone crossed safely, and Wolf used his tail to signal where the sturdy boards began.",
        "Strength includes knowing when to slow down and help rebuild.",
        "The new bridge stood firm while Wolf's tail waved like a bright flag beside it.",
        "Why did Wolf stop charging across the bridge?",
        "The beaver showed that the little branch bridge was made for small paws and could not safely hold Wolf.",
    ),
    Incident(
        "the missing giggle",
        "The forest planned a humor contest, but a young owl sat silently beneath a pine.",
        "Wolf tried a frightening face, then slipped on a pinecone and landed in a bed of soft moss.",
        "The owl admitted that loud jokes made her nervous, but gentle silliness felt safe.",
        "Wolf told a quiet joke about a squirrel losing an acorn in its own pocket.",
        "The twist was that Wolf's softest joke made the owl giggle more than his grandest growl.",
        "The owl joined the contest, and every animal shared one joke that made another animal comfortable.",
        "Good humor opens a door only when kindness holds it open.",
        "The owl's first giggle fluttered through the branches like a small silver bell.",
        "What kind of joke helped the owl laugh?",
        "A quiet, gentle joke about a squirrel losing an acorn in its own pocket helped the owl laugh.",
    ),
]


NAMES = ["Luna", "Milo", "Nora", "Pip", "Tavi"]
COMPANIONS = ["rabbit", "mouse", "owl", "beaver"]
TRAITS = ["boisterous", "curious", "playful", "proud"]
OPENINGS = [
    "In a green forest where every stump had a story, a wolf named {name} loved a good joke.",
    "Long ago, when the moon was a silver button, {name} the wolf practiced being funny.",
    "A wolf named {name} lived beside a laughing stream and wanted every creature to smile.",
    "The forest knew {name} as a loud wolf with a louder sense of humor.",
]


def can_story(place: str, activity: str, prize: str) -> bool:
    return place == "forest" and activity == "help" and prize == "kindness"


ASP_RULES = r"""
place(forest).
activity(help).
prize(kindness).
feature(humor).
feature(kindness).

compatible(P,A,R) :-
    place(P), activity(A), prize(R),
    P = forest, A = help, R = kindness.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "forest"),
            asp.fact("activity", "help"),
            asp.fact("prize", "kindness"),
            asp.fact("feature", "humor"),
            asp.fact("feature", "kindness"),
        ]
    )


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("forest", "help", "kindness")]


def tell(params: StoryParams) -> World:
    incident = INCIDENTS[int(params.incident.rsplit("_", 1)[1])]
    opening = OPENINGS[(params.seed or 0) % len(OPENINGS)].format(name=params.name)

    world = World()
    wolf = world.add(Entity("wolf", "animal", params.name))
    companion = world.add(Entity("companion", "animal", params.companion))
    wolf.memes.update(humor=1.0, pride=1.0, kindness=0.0)
    companion.memes.update(safety=1.0, trust=0.0)
    world.facts.update(wolf=wolf, companion=companion, incident=incident)

    world.say(opening)
    world.say(
        f"He was {params.trait}, quick with a joke, and certain that the best laugh "
        f"was the one that followed his biggest growl."
    )
    world.say(
        f"His forest friend, a {params.companion}, often reminded him that a joke should "
        f"make room for kindness."
    )
    world.para()

    world.say(incident.trouble)
    world.say(incident.failed_plan)
    world.say(f'"Was that funny?" {params.name} asked. "It was meant to be!"')
    world.say(
        f'"A joke is better when nobody feels small," said the {params.companion}. '
        f'"Let us look for the real trouble."'
    )
    world.para()

    world.say(incident.clue)
    wolf.meters["embarrassment"] = 1.0
    wolf.memes["pride"] = 0.0
    wolf.memes["kindness"] = 1.0
    companion.memes["trust"] = 1.0
    world.fired.add("pride_softened")
    world.say(incident.repair)
    world.say(incident.twist)
    world.say(
        f'"I can be funny without frightening anyone," {params.name} said. '
        f'"And I can help while I laugh."'
    )
    world.para()

    wolf.meters["embarrassment"] = 0.0
    wolf.memes["joy"] = 1.0
    world.say(incident.resolution)
    world.say(f"The forest learned the lesson: {incident.lesson}")
    world.say(incident.ending)

    world.facts.update(
        title=incident.title,
        clue=incident.clue,
        twist=incident.twist,
        resolution=incident.resolution,
        lesson=incident.lesson,
        ending=incident.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    wolf = world.facts["wolf"]
    incident = world.facts["incident"]
    return [
        "Write a child-friendly fable about a wolf who learns to use humor with kindness.",
        f"Tell a forest fable in which {wolf.label} faces {incident.title} and changes his plan.",
        f"Use this clue to create the turning point: {incident.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    wolf = world.facts["wolf"]
    companion = world.facts["companion"]
    incident = world.facts["incident"]
    return [
        QAItem(
            question=f"What did {wolf.label} want the forest animals to enjoy?",
            answer=f"{wolf.label} wanted the forest animals to enjoy his humor, but he learned that their safety and feelings mattered too.",
        ),
        QAItem(
            question=incident.question,
            answer=incident.answer,
        ),
        QAItem(
            question=f"What did the {companion.kind} tell {wolf.label}?",
            answer=f"The {companion.kind} told {wolf.label} that a joke is better when nobody feels small.",
        ),
        QAItem(
            question=f"What changed in {wolf.label} during {incident.title}?",
            answer=f"{wolf.label} stopped chasing a laugh through pride and chose to help with kindness instead.",
        ),
        QAItem(
            question="What final image showed that the problem was solved?",
            answer=incident.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is humor?",
            answer="Humor is something amusing that can make people laugh or smile.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating others gently, helping them, and caring about their feelings.",
        ),
        QAItem(
            question="What makes a joke kind?",
            answer="A joke is kind when it is funny without frightening, hurting, or humiliating someone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.kind:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random, seed: int) -> StoryParams:
    if args.place and args.place != "forest":
        raise StoryError("This fable takes place in the forest.")
    if args.activity and args.activity != "help":
        raise StoryError("The supported activity is helping someone.")
    if args.prize and args.prize != "kindness":
        raise StoryError("The fable's prize is kindness.")
    if args.name and not args.name.strip():
        raise StoryError("The wolf's name cannot be empty.")
    if args.companion and args.companion not in COMPANIONS:
        raise StoryError("The companion must be a rabbit, mouse, owl, or beaver.")
    if args.trait and args.trait not in TRAITS:
        raise StoryError("Choose a listed wolf trait.")

    return StoryParams(
        place="forest",
        activity="help",
        prize="kindness",
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        trait=args.trait or rng.choice(TRAITS),
        incident=f"incident_{seed % len(INCIDENTS):02d}",
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        description="A fable storyworld about a wolf, humor, and kindness."
    )
    parser.add_argument("--place", choices=["forest"])
    parser.add_argument("--activity", choices=["help"])
    parser.add_argument("--prize", choices=["kindness"])
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
    py = set(valid_combos())
    try:
        clingo_combos = set(asp_valid_combos())
    except ImportError:
        print("ASP verification requires the optional clingo dependency.")
        return 1
    if py != clingo_combos:
        print("MISMATCH between Python and ASP compatibility gates.")
        print("Only in Python:", sorted(py - clingo_combos))
        print("Only in ASP:", sorted(clingo_combos - py))
        return 1
    for seed in range(4):
        params = resolve_params(argparse.Namespace(
            place=None,
            activity=None,
            prize=None,
            name=None,
            companion=None,
            trait=None,
        ), random.Random(seed), seed)
        sample = generate(params)
        if not sample.story or "wolf" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        try:
            print(asp_valid_combos())
        except ImportError:
            raise SystemExit("ASP mode requires the optional clingo dependency.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed), base_seed)
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        for index in range(max(1, args.n)):
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
