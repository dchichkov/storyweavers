#!/usr/bin/env python3
"""
A small ghost-story world about a teen, a graze, and a poppy surprise that
ends in reconciliation through problem solving.

The seed premise:
- A teen gets a small graze near a poppy patch.
- A surprising ghostly event startles everyone.
- The teen, a helper, and a worried grown-up solve the problem together.
- The ending proves the fear eased and the hurt was cared for.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    seen_ghost: bool = False
    helpful: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "teen-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def cap(self, case: str = "subject") -> str:
        return self.pronoun(case).capitalize()


@dataclass
class Place:
    name: str
    kind: str = "yard"
    eerie: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    name: str
    verb: str
    surprise: str
    cause: str
    fix_hint: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    action: str
    why: str
    solves: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    teen_name: str
    teen_type: str
    adult_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


PLACES = {
    "graveyard": Place(name="the old graveyard", kind="graveyard", eerie=True, affords={"graze"}),
    "garden": Place(name="the moonlit garden", kind="garden", eerie=True, affords={"graze"}),
    "lane": Place(name="the quiet lane", kind="lane", eerie=True, affords={"graze"}),
}

PROBLEMS = {
    "graze": Problem(
        id="graze",
        name="a small graze",
        verb="graze a knee",
        surprise="a cold surprise in the dark",
        cause="the teen slipped on a root",
        fix_hint="clean it and cover it",
        zone="knee",
        keyword="graze",
        tags={"graze", "hurt"},
    ),
    "poppy": Problem(
        id="poppy",
        name="a poppy surprise",
        verb="disturb the poppy patch",
        surprise="a hush of red petals",
        cause="the teen brushed too close to the flowers",
        fix_hint="move carefully and set things right",
        zone="hands",
        keyword="poppy",
        tags={"poppy", "flower"},
    ),
    "surprise": Problem(
        id="surprise",
        name="a ghostly surprise",
        verb="startle a hidden watcher",
        surprise="a pale shape in the mist",
        cause="something whispered from the dark",
        fix_hint="speak gently and check the path",
        zone="heart",
        keyword="surprise",
        tags={"surprise", "ghost"},
    ),
}

AIDS = {
    "lantern": Aid(
        id="lantern",
        label="a small lantern",
        action="held up the lantern",
        why="it made the path bright enough to see the root and the flowers",
        solves={"surprise", "poppy"},
    ),
    "cloth": Aid(
        id="cloth",
        label="a clean cloth",
        action="pressed the cloth over the graze",
        why="it kept the scrape clean and calm",
        solves={"graze"},
    ),
    "tea": Aid(
        id="tea",
        label="warm tea",
        action="shared warm tea",
        why="it helped everyone breathe slowly and talk kindly",
        solves={"surprise", "graze", "poppy"},
    ),
}

GHOST_WHISPERS = [
    "a whisper rustled the leaves",
    "something white drifted near the fence",
    "the air went still as a pale shape turned",
    "a soft moan slipped through the poppies",
]


def valid_combo(place: Place, problem: Problem) -> bool:
    return problem.id in place.affords


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            if valid_combo(place, prob):
                out.append((pid, prob_id))
    return out


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    prob = PROBLEMS[params.problem]
    world = World(place)
    teen = world.add(Entity(
        id=params.teen_name,
        kind="character",
        type=params.teen_type,
        traits=["teen", "quiet", "brave"],
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=params.adult_type,
        label="the grown-up",
        traits=["careful", "gentle"],
    ))
    ghost = world.add(Entity(
        id="Ghost",
        kind="character",
        type="thing",
        label="the ghost",
        traits=["pale", "watchful"],
        helpful=False,
    ))
    poppy = world.add(Entity(
        id="PoppyPatch",
        kind="thing",
        type="poppy patch",
        label="poppy patch",
        phrase="a bed of red poppies",
    ))
    wound = world.add(Entity(
        id="Graze",
        kind="thing",
        type="graze",
        label="graze",
        phrase="a small scrape on the knee",
        caretaker=adult.id,
    ))
    world.facts.update(teen=teen, adult=adult, ghost=ghost, poppy=poppy, wound=wound, problem=prob)
    return world


def tell(world: World) -> None:
    teen: Entity = world.facts["teen"]
    adult: Entity = world.facts["adult"]
    ghost: Entity = world.facts["ghost"]
    poppy: Entity = world.facts["poppy"]
    wound: Entity = world.facts["wound"]
    problem: Problem = world.facts["problem"]

    teen.memes["curiosity"] = 1
    teen.memes["unease"] = 0
    adult.memes["worry"] = 1

    world.say(
        f"On a hush-dark evening, {teen.id} walked beside {world.place.name}. "
        f"{teen.cap()} had the restless feeling that old places were listening."
    )
    world.say(
        f"Near the {poppy.label}, {problem.surprise} appeared. "
        f"{random.choice(GHOST_WHISPERS).capitalize()}, and {teen.id} froze."
    )

    if problem.id == "graze":
        teen.meters["graze"] = 1
        teen.memes["shock"] = 1
        wound.meters["dirty"] = 1
        world.say(
            f"{teen.id} slipped on a root and got {problem.name} on {wound.phrase}. "
            f"{teen.cap()} bit back a yelp, because the night felt suddenly sharp."
        )
    elif problem.id == "poppy":
        teen.memes["guilt"] = 1
        poppy.meters["bent"] = 1
        world.say(
            f"{teen.id} brushed the poppies by mistake, and one red stem bent low. "
            f"The flowers looked startled, as if the garden had breathed in too fast."
        )
    else:
        teen.memes["shock"] = 1
        ghost.seen_ghost = True
        world.say(
            f"{teen.id} heard a whisper and saw a pale shape in the mist. "
            f"For one small moment, {teen.pronoun()} thought the graveyard had answered back."
        )

    world.say(
        f"{adult.label} hurried over with a lantern. {adult.cap()} did not laugh; "
        f"{adult.pronoun('subject')} only looked from {teen.id} to the dark path and waited."
    )
    teen.memes["fear"] = 1
    adult.memes["care"] = 1

    if problem.id in {"surprise", "poppy"}:
        ghost.seen_ghost = True

    world.say(
        f"Then {adult.id} said, \"Let's solve this step by step.\" "
        f"{adult.id} {AIDS['lantern'].action}, and the shadows shrank enough to show the way."
    )

    if problem.id == "graze":
        world.say(
            f"{adult.id} {AIDS['cloth'].action}, because {AIDS['cloth'].why}. "
            f"{teen.id} watched the scrape stop stinging little by little."
        )
    elif problem.id == "poppy":
        world.say(
            f"{adult.id} knelt by the flowers and set them straight, because {AIDS['tea'].why}. "
            f"{teen.id} helped, touching only the stems that needed help."
        )
    else:
        world.say(
            f"{adult.id} {AIDS['tea'].action}, because {AIDS['tea'].why}. "
            f"The ghostly shape turned out to be only mist curling over stone."
        )

    teen.memes["understood"] = 1
    adult.memes["relief"] = 1
    teen.memes["fear"] = 0
    adult.memes["worry"] = 0
    teen.memes["peace"] = 1

    world.say(
        f"At last, {teen.id} and {adult.id} stood together beside the poppies. "
        f"The surprise was still there, but it had become harmless, like a story told softly."
    )
    if problem.id == "graze":
        world.say(
            f"{teen.id}'s knee was clean and bandaged, and the lantern made the path look kind again."
        )
    elif problem.id == "poppy":
        world.say(
            f"The poppies stood straight, and their red petals glowed like tiny safe flames."
        )
    else:
        world.say(
            f"The quiet shape in the mist was only the wind, and the path no longer felt haunted."
        )

    world.facts["resolved"] = True
    world.facts["ghost_real"] = problem.id == "surprise" and False


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    teen: Entity = f["teen"]
    prob: Problem = f["problem"]
    return [
        f'Write a gentle ghost story for a child about {teen.id}, {prob.keyword}, and a helpful grown-up.',
        f"Tell a small spooky story where {teen.id} faces {prob.name} and learns to solve the problem calmly.",
        f"Write a story with a surprise in the dark, a careful fix, and a peaceful ending by the poppies.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    teen: Entity = f["teen"]
    adult: Entity = f["adult"]
    prob: Problem = f["problem"]
    place: Place = world.place
    qa = [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {teen.id}, a quiet teen walking near {place.name}.",
        ),
        QAItem(
            question=f"What problem happened near the poppies?",
            answer=f"{teen.id} got {prob.name} near the poppy patch, and that made the evening feel scary for a moment.",
        ),
        QAItem(
            question=f"How did {adult.label} help?",
            answer=f"{adult.label} brought light, stayed calm, and helped solve the problem step by step.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(QAItem(
            question="What changed by the end?",
            answer=f"By the end, {teen.id} felt calmer, the problem was fixed, and the night felt peaceful again.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "graze": [
        QAItem(
            question="What is a graze?",
            answer="A graze is a small, shallow scrape on the skin. It usually needs cleaning and a little covering so it can heal.",
        )
    ],
    "poppy": [
        QAItem(
            question="What is a poppy?",
            answer="A poppy is a flower with bright petals, often red or orange. Poppies can grow in gardens and fields.",
        )
    ],
    "surprise": [
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected. It can make you gasp for a moment, even if it is not dangerous.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    prob: Problem = world.facts["problem"]
    out = list(WORLD_KNOWLEDGE.get(prob.id, []))
    out.append(QAItem(
        question="What does reconciliation mean?",
        answer="Reconciliation means two people stop feeling upset with each other and come back together kindly.",
    ))
    out.append(QAItem(
        question="What is problem solving?",
        answer="Problem solving means looking carefully at a trouble and choosing steps that make it better.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.seen_ghost:
            bits.append("seen_ghost=True")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"events={len(world.events)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(graveyard). place(garden). place(lane).
problem(graze). problem(poppy). problem(surprise).

affords(graveyard, graze).
affords(garden, graze).
affords(lane, graze).

valid(P, Pr) :- place(P), problem(Pr), affords(P, Pr).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for prob_id in PROBLEMS:
        lines.append(asp.fact("problem", prob_id))
    for pid, place in PLACES.items():
        for prob_id in place.affords:
            lines.append(asp.fact("affords", pid, prob_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world about a teen, a graze, and poppies.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--teen-type", choices=["girl", "boy", "teen-boy", "teen-girl"], default="teen")
    ap.add_argument("--adult-type", choices=["mother", "father", "woman", "man"], default="mother")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.problem:
        if not valid_combo(PLACES[args.place], PROBLEMS[args.problem]):
            raise StoryError("That place and problem do not make a reasonable ghost story here.")
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, problem = rng.choice(sorted(combos))
    teen_name = args.name or rng.choice(["Mina", "Noah", "June", "Ezra", "Lia", "Theo"])
    return StoryParams(
        place=place,
        problem=problem,
        teen_name=teen_name,
        teen_type=args.teen_type,
        adult_type=args.adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for place, prob in combos:
            print(f"{place} {prob}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="graveyard", problem="graze", teen_name="Mina", teen_type="girl", adult_type="mother"),
            StoryParams(place="garden", problem="poppy", teen_name="Noah", teen_type="boy", adult_type="father"),
            StoryParams(place="lane", problem="surprise", teen_name="June", teen_type="girl", adult_type="woman"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
