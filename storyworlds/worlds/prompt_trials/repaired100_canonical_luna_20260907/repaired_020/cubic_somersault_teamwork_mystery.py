#!/usr/bin/env python3
"""
A small cubic somersault teamwork mystery.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.id


@dataclass
class Place:
    name: str = "the old gym"
    floor_safe: bool = True


@dataclass
class StoryParams:
    place: str = "gym"
    hero: str = "Luna"
    partner: str = "Milo"
    coach: str = "Tara"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


ARCS = [
    {
        "object": "a small cubic puzzle block",
        "clue": "one corner carried a smear of silver chalk",
        "fear": "someone had moved the block and hidden the missing practice key",
        "cause": "the block had rolled beneath the spring mat when a loose floorboard lifted",
        "action": "they raised the mat together and followed the chalk mark to the board",
        "dialogue": '"You watch the mark while I lift," Luna said. "Together," Milo replied.',
        "ending": "the cubic block sat beside the recovered key, its silver corner shining",
    },
    {
        "object": "a cubic wooden marker",
        "clue": "three tiny feathers were caught under its lowest edge",
        "fear": "a bird had flown into the locked equipment room",
        "cause": "the marker had been nudged by a draft from a cracked high window",
        "action": "they checked the window, found the draft, and returned the marker to its painted square",
        "dialogue": '"The feathers point upward," Tara said. "Then the window is our next step," Luna answered.',
        "ending": "the cubic marker rested under the closed window while sunlight crossed the floor",
    },
    {
        "object": "a bright cubic lantern",
        "clue": "its shadow pointed toward the folded mats instead of the door",
        "fear": "someone had entered during the blackout",
        "cause": "the lantern had spun during a somersault and cast a misleading shadow",
        "action": "they replayed the movement slowly and found a loose strap beneath the mat",
        "dialogue": '"Slow steps reveal more," Milo said. "And every teammate sees a different piece," Luna replied.',
        "ending": "the lantern glowed beside the secured mat strap",
    },
]


def tell_story(params: StoryParams) -> World:
    if params.hero == params.partner or params.hero == params.coach:
        raise StoryError("The gymnast, partner, and coach must have different names.")
    world = World(Place(name="the old gym"))
    hero = world.add(Entity(params.hero, "character", "girl", params.hero))
    partner = world.add(Entity(params.partner, "character", "boy", params.partner))
    coach = world.add(Entity(params.coach, "character", "woman", params.coach))
    hero.memes["curiosity"] = 1.0
    partner.memes["care"] = 1.0
    coach.memes["patience"] = 1.0

    seed = params.seed or 0
    arc = ARCS[seed % len(ARCS)]
    world.facts["arc"] = arc
    world.say(
        f"{hero.id} and {partner.id} practiced a careful somersault in {world.place.name} while "
        f"{coach.id} watched from the edge of the blue mat. Beside the balance line sat {arc['object']}."
    )
    world.para()
    world.say(
        f"After one smooth turn, the practice key vanished. {hero.id} noticed that {arc['clue']}. "
        f"For a moment, they feared {arc['fear']}."
    )
    hero.memes["tension"] = 1.0
    partner.memes["tension"] = 1.0
    coach.memes["tension"] = 1.0
    world.say(
        f"Nobody blamed anyone. {coach.id} asked each teammate to describe what they had seen, "
        f"and the clues formed a quiet mystery."
    )
    world.say(f"They discovered that {arc['cause']}. Then {arc['action']}. {arc['dialogue']}")
    hero.memes["tension"] = 0.0
    partner.memes["tension"] = 0.0
    coach.memes["tension"] = 0.0
    world.para()
    world.say(
        f"The missing key was found, and the team marked the loose spot with a red ribbon. "
        f"{coach.id} explained that teamwork had solved the mystery because everyone shared one small observation."
    )
    world.say(
        f"At the end of practice, {hero.id} performed the somersault again, this time with the team watching the mat, "
        f"the window, and the cubic marker together. {arc['ending']}."
    )
    world.facts.update(
        hero=hero,
        partner=partner,
        coach=coach,
        clue=arc["clue"],
        feared=arc["fear"],
        cause=arc["cause"],
        action=arc["action"],
        ending=arc["ending"],
    )
    return world


NAMES = ["Luna", "Mira", "Nia", "Sora", "Pia", "Tess"]
PARTNERS = ["Milo", "Noah", "Leo", "Finn", "Owen"]
COACHES = ["Tara", "Asha", "Rina", "Cleo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-facing mystery about a cubic object, a somersault, and teamwork.",
        f"Tell how {f['hero'].id} solved a gym mystery by examining this clue: {f['clue']}.",
        "Write a gentle story where teammates share observations instead of blaming one another.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"What were {f['hero'].id} and {f['partner'].id} practicing?",
            f"They were practicing a careful somersault in the old gym.",
        ),
        QAItem(
            "What clue began the mystery?",
            f"The clue was that {f['clue']}.",
        ),
        QAItem(
            "What did the teammates fear?",
            f"They feared that {f['feared']}.",
        ),
        QAItem(
            "What really happened?",
            f"They discovered that {f['cause']}.",
        ),
        QAItem(
            "How did teamwork help?",
            f"Everyone shared a small observation, and together they {f['action']}.",
        ),
        QAItem(
            "What showed that the mystery had been solved?",
            f"{f['ending'].capitalize()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a cubic shape?", "A cubic shape has the form of a cube, with six square faces."),
        QAItem("What is a somersault?", "A somersault is a movement in which a person rolls the body over."),
        QAItem("What is teamwork?", "Teamwork is when people cooperate and combine their efforts to solve a problem."),
        QAItem("What is a clue?", "A clue is a sign or piece of information that helps someone discover an answer."),
    ]


ASP_RULES = r"""
tension(mystery) :- missing_key.
clue_found :- missing_key, silver_mark.
teamwork :- clue_found, shared_observations.
solved :- teamwork, loose_spot_found.
chosen(solved) :- solved.
#show chosen/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("missing_key"),
            asp.fact("silver_mark"),
            asp.fact("shared_observations"),
            asp.fact("loose_spot_found"),
        ]
    )


def asp_program(show: str = "#show chosen/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "chosen")))


def asp_verify() -> int:
    expected = [("solved",)]
    actual = asp_outcome()
    if actual != expected:
        print(f"MISMATCH: python=solved asp={actual}")
        return 1
    for seed in range(5):
        sample = generate(StoryParams(seed=seed))
        if "somersault" not in sample.story or "cubic" not in sample.story:
            print("MISMATCH: required seed words missing")
            return 1
    print("OK: ASP, Python, and generated stories agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cubic somersault teamwork mystery storyworld.")
    parser.add_argument("--place", choices=["gym"])
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--coach", choices=COACHES)
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
    hero = args.hero or rng.choice(NAMES)
    partner_choices = [x for x in PARTNERS if x != hero]
    coach_choices = [x for x in COACHES if x not in {hero, args.partner}]
    return StoryParams(
        place=args.place or "gym",
        hero=hero,
        partner=args.partner or rng.choice(partner_choices),
        coach=args.coach or rng.choice(coach_choices),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_outcome())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(seed=base_seed)
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 20):
            if len(samples) >= max(args.n, 1):
                break
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
