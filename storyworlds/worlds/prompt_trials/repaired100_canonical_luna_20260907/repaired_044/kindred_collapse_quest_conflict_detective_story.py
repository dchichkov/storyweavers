#!/usr/bin/env python3
"""
A small Detective Story world about a kindred quest interrupted by a collapse.

Luna and a trusted companion investigate why a bridge of stacked stones collapsed
near the old orchard. Clues first point toward a rival, but careful detective
work reveals that a hidden burrow weakened the stones. The detectives repair the
crossing and restore trust between kindred neighbors.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from storyworlds.results import QAItem, StoryError, StorySample
except ImportError:
    from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("stability", "distance", "weight", "visibility"):
            self.meters.setdefault(key, 0.0)
        for key in ("trust", "worry", "curiosity", "courage", "conflict"):
            self.memes.setdefault(key, 0.0)


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    feature: str


@dataclass(frozen=True)
class Case:
    id: str
    opening: str
    collapse: str
    clue: str
    false_lead: str
    discovery: str
    repair: str
    ending: str
    lesson: str


PLACES = {
    "orchard": Place("orchard", "the old orchard", "a stone footbridge"),
    "hill": Place("hill", "the lantern hill", "a little lookout tower"),
    "garden": Place("garden", "the kindred garden", "a wooden gate"),
    "creek": Place("creek", "the whispering creek", "a plank crossing"),
}

KINDS = {
    "rabbit": "rabbit",
    "fox": "fox",
    "badger": "badger",
    "mouse": "mouse",
    "otter": "otter",
}

NAMES = ["Luna", "Milo", "Tess", "Nico", "Pip", "Rhea", "Clover", "Jasper"]

CASES = [
    Case(
        "loose_mortar",
        "Luna was asked to find out why the crossing had failed before sunset.",
        "At dawn, the middle stones collapsed with a dusty clatter.",
        "A pale thread caught on a thorn led away from the broken stones.",
        "The thread looked like the scarf of a proud fox who lived nearby.",
        "Under the lowest stone, they found a tunnel packed with fresh earth and tiny claw marks.",
        "They filled the tunnel, set flat stones across it, and rebuilt the crossing with a strong wooden rail.",
        "When the repaired crossing held, the fox carried the first basket safely to the other side.",
        "A good detective follows evidence, not the first suspicion.",
    ),
    Case(
        "missing peg",
        "Luna promised to discover what had made the lookout platform unsafe.",
        "One wooden support slipped, and the little tower leaned toward the moon.",
        "A bright blue peg lay beside the fallen support.",
        "The peg matched a toy cart owned by a visiting mouse, so several neighbors blamed the mouse.",
        "A trail of damp moss showed that rain had loosened the ground beneath the support.",
        "They dried the boards, replaced the peg, and braced the tower with two fresh beams.",
        "The mouse used the safe tower to hang a blue flag for everyone to see.",
        "A clue can explain a problem without proving who caused it.",
    ),
    Case(
        "hidden_water",
        "Luna set out to learn why the garden gate had stopped closing.",
        "The gate collapsed into a bed of mint just as the kindred neighbors arrived.",
        "Small wet footprints crossed the mud beside the hinge.",
        "The footprints seemed to point toward an otter who had been carrying reeds.",
        "A buried spring had softened the earth around the hinge, and the otter had only been fetching water.",
        "They redirected the spring, packed the earth, and hung the gate on a smooth new hinge.",
        "The otter held the gate open while kindred friends carried baskets through.",
        "A fair investigator asks what a clue means before assigning blame.",
    ),
    Case(
        "shaken_planks",
        "Luna began a quest to find why the creek crossing had broken before the picnic.",
        "Three planks buckled and fell into the shallow water.",
        "A line of acorn shells marked the edge of the crossing.",
        "The shells made it seem that a playful squirrel had tampered with the planks.",
        "The shells were actually packed around a beaver's hidden water channel beneath the bank.",
        "They cleared the channel, dried the planks, and tied them down with vine rope.",
        "The squirrel placed a sign beside the crossing: WALK SLOWLY.",
        "A strange pattern may be a warning instead of a confession.",
    ),
]


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


@dataclass
class StoryParams:
    place: str
    case: str
    detective: str
    detective_kind: str
    partner: str
    partner_kind: str
    seed: Optional[int] = None


ASP_RULES = r"""
reason(P) :- place(P).
case_ready(C) :- case(C), quest(C), conflict(C), clue(C), repair(C).
valid_story(P,C) :- reason(P), case_ready(C).
#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts: list[str] = []
    for place in PLACES:
        facts.append(asp.fact("place", place))
    for case_id, case in CASES_BY_ID.items():
        facts.extend(
            [
                asp.fact("case", case_id),
                asp.fact("quest", case_id),
                asp.fact("conflict", case_id),
                asp.fact("clue", case_id),
                asp.fact("repair", case_id),
            ]
        )
    return "\n".join(facts)


CASES_BY_ID = {case.id: case for case in CASES}


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("That setting is not part of the detective world.")
    if params.case not in CASES_BY_ID:
        raise StoryError("That case is not part of the detective world.")
    if params.detective_kind not in KINDS:
        raise StoryError("The detective must have a known kindred form.")
    if params.partner_kind not in KINDS:
        raise StoryError("The detective's partner must have a known kindred form.")
    if params.detective == params.partner:
        raise StoryError("The detective and partner must be different characters.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else repr(params))
    place = PLACES[params.place]
    case = CASES_BY_ID[params.case]
    world = World(place)

    detective = world.add(
        Entity(
            params.detective,
            "character",
            params.detective,
            memes={"curiosity": 2.0, "courage": 1.0, "trust": 1.0},
        )
    )
    partner = world.add(
        Entity(
            params.partner,
            "character",
            params.partner,
            memes={"curiosity": 1.0, "courage": 1.0, "trust": 2.0},
        )
    )
    crossing = world.add(
        Entity(
            "collapsed_structure",
            "structure",
            place.feature,
            meters={"stability": 0.0, "distance": 2.0, "weight": 4.0, "visibility": 2.0},
        )
    )
    hidden_cause = world.add(
        Entity(
            "hidden_cause",
            "clue",
            "the hidden cause",
            meters={"visibility": 0.0, "distance": 1.0, "weight": 1.0},
        )
    )

    world.say(
        f"In {place.name}, {params.detective} the {params.detective_kind} worked as a careful detective."
    )
    world.say(
        f"One morning, {params.partner} the {params.partner_kind} arrived with a quest: {case.opening}"
    )
    world.say(
        f"They hurried to {place.feature}, where the collapse had blocked the path between their kindred homes."
    )
    world.para()

    world.say(f"{case.collapse} Dust covered the ground, but the broken place still held clues.")
    detective.memes["curiosity"] += 1.0
    detective.meters["visibility"] += 1.0
    crossing.meters["stability"] = 0.0
    world.say(
        f'"What should we inspect first?" asked {params.partner}. "{case.clue}"'
    )
    world.say(
        f'"We will record every clue before we choose a culprit," said {params.detective}.'
        f' "That is how detectives protect their kindred."'
    )
    world.para()

    world.say(f"The conflict grew when {case.false_lead}")
    detective.memes["conflict"] = 1.0
    partner.memes["worry"] = 1.0
    world.say(
        f'{params.partner} frowned. "Then perhaps we should ask that neighbor at once."'
    )
    world.say(
        f'{params.detective} shook their head. "A suspicion is not a solved case. Let us follow the trail."'
    )
    world.say(f"They compared the marks, the dust, and the shape of the fallen pieces.")
    world.para()

    world.say(f"The careful search changed the case: {case.discovery}")
    hidden_cause.meters["visibility"] = 3.0
    crossing.meters["stability"] = 1.0
    detective.memes["conflict"] = 0.0
    detective.memes["courage"] += 1.0
    partner.memes["trust"] += 1.0
    world.say(
        f'"Now we know what happened," said {params.partner}. "The collapse was not a neighbor\'s trick."'
    )
    world.say(
        f'"And now we know what to do," replied {params.detective}. "Let us repair the path together."'
    )
    world.say(f"{case.repair}")
    crossing.meters["stability"] = 3.0
    world.para()

    world.say(
        f"The kindred neighbors gathered without fear. {case.ending} "
        f"{case.lesson}"
    )

    world.facts.update(
        place=params.place,
        place_name=place.name,
        case=params.case,
        feature=place.feature,
        detective=params.detective,
        detective_kind=params.detective_kind,
        partner=params.partner,
        partner_kind=params.partner_kind,
        collapse=case.collapse,
        clue=case.clue,
        false_lead=case.false_lead,
        discovery=case.discovery,
        repair=case.repair,
        ending=case.ending,
        lesson=case.lesson,
        resolved=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    f = world.facts
    prompts = [
        f"Write a Detective Story about {f['detective']} investigating a collapse at {f['place_name']}.",
        f"Tell a child-friendly Quest story where {f['detective']} and {f['partner']} follow this clue: {f['clue']}.",
        f"Write a kindred Conflict story that resolves when {f['discovery']}",
    ]
    story_questions = [
        QAItem(
            f"Where did {f['detective']} investigate the collapse?",
            f"{f['detective']} investigated it at {f['place_name']}, near {f['feature']}.",
        ),
        QAItem(
            "What was the detective's quest?",
            f"The quest was to discover why {f['feature']} had collapsed and how to make the path safe again.",
        ),
        QAItem(
            "What clue did the detectives follow?",
            f"They followed this clue: {f['clue']}.",
        ),
        QAItem(
            "What caused the conflict?",
            f"The conflict began because {f['false_lead']}",
        ),
        QAItem(
            "What did the detectives discover?",
            f"They discovered that {f['discovery']}",
        ),
        QAItem(
            "How was the problem resolved?",
            f"They resolved it when {f['repair']}",
        ),
        QAItem(
            "What lesson did the kindred neighbors learn?",
            f"They learned that {f['lesson']}",
        ),
    ]
    world_questions = [
        QAItem(
            "What is a detective?",
            "A detective is someone who studies clues to understand what happened.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is a purposeful journey to find, learn, or accomplish something.",
        ),
        QAItem(
            "What is a conflict?",
            "A conflict is a problem or disagreement that characters must work through.",
        ),
        QAItem(
            "What does kindred mean?",
            "Kindred means closely connected, like family members or friends who care for one another.",
        ),
        QAItem(
            "What is a collapse?",
            "A collapse happens when something loses support and falls down.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_questions,
        world_qa=world_questions,
        world=world,
    )


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
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"- {prompt}" for prompt in sample.prompts)
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective Story world about a kindred quest and a collapse."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--case", choices=sorted(CASES_BY_ID))
    parser.add_argument("--detective")
    parser.add_argument("--detective-kind", choices=sorted(KINDS))
    parser.add_argument("--partner")
    parser.add_argument("--partner-kind", choices=sorted(KINDS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective = args.detective or rng.choice(NAMES)
    partner = args.partner or rng.choice([name for name in NAMES if name != detective])
    detective_kind = args.detective_kind or rng.choice(sorted(KINDS))
    partner_kind = args.partner_kind or rng.choice(sorted(KINDS))
    params = StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        case=args.case or rng.choice(sorted(CASES_BY_ID)),
        detective=detective,
        detective_kind=detective_kind,
        partner=partner,
        partner_kind=partner_kind,
    )
    reasonableness_gate(params)
    return params


CURATED = [
    StoryParams("orchard", "loose_mortar", "Luna", "rabbit", "Milo", "fox"),
    StoryParams("hill", "missing_peg", "Tess", "badger", "Nico", "mouse"),
    StoryParams("garden", "hidden_water", "Rhea", "otter", "Clover", "rabbit"),
    StoryParams("creek", "shaken_planks", "Jasper", "fox", "Pip", "badger"),
]


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = {(place, case) for place in PLACES for case in CASES_BY_ID}
    if actual != expected:
        print("MISMATCH between ASP and Python story registry.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "collapse" not in sample.story:
            print("MISMATCH: generated story failed its narrative check.")
            return 1
    print(f"OK: ASP/Python parity and generated-story checks passed ({len(actual)} combinations).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} valid story shapes:")
        for place, case in values:
            print(f"  {place} / {case}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= max(args.n, 1):
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(exc)
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
            header = (
                f"### {sample.params.detective} / "
                f"{sample.params.partner} at {sample.params.place}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
