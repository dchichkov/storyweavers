#!/usr/bin/env python3
"""
A child-facing detective storyworld about a strange noxious smell, a muddy clue,
and a teamwork-powered transformation.
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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    open_gate: bool = True
    garden_safe: bool = False


@dataclass
class StoryParams:
    place: str = "lantern_garden"
    detective: str = "Luna"
    helper: str = "Milo"
    gardener: str = "Sana"
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


ARC_DATA = [
    {
        "routine": "polished the brass key to the garden shed",
        "alarm": "a noxious puff drifted from behind the rose wall",
        "clue": "three muddy pawprints crossed the pale stones",
        "fear": "someone had poured poison into the garden pond",
        "cause": "a tipped compost pail had trapped a wet sack of onion skins beneath it",
        "fix": "lifted the pail together, moved the sack, and washed the stones with clean water",
        "object": "a green compost pail",
        "ending": "fresh mint leaves covered the clean stones",
    },
    {
        "routine": "introduced a new brass magnifying glass to the garden club",
        "alarm": "a noxious green fog curled from the tool shed",
        "clue": "a muddy wheel mark led away from the shed door",
        "fear": "a hidden machine was leaking something dangerous",
        "cause": "a rain barrel had rolled onto a bag of old seaweed fertilizer",
        "fix": "worked as a team to roll the barrel aside and seal the fertilizer in a dry bin",
        "object": "a blue rain barrel",
        "ending": "the barrel stood steady beside a row of labeled bins",
    },
    {
        "routine": "counted sunflower seeds beside the little fountain",
        "alarm": "a noxious smell rose when the fountain coughed",
        "clue": "muddo—a thick brown smear—marked the fountain handle",
        "fear": "a stranger had tampered with the water",
        "cause": "a muddy frog had wedged a fallen leaf into the filter",
        "fix": "freed the frog, removed the leaf, and rinsed the filter",
        "object": "a copper fountain handle",
        "ending": "the fountain sparkled while the frog rested under a fern",
    },
    {
        "routine": "hung name cards for a new garden introduction",
        "alarm": "a noxious stink burst from the welcome table",
        "clue": "muddo clung to one missing name card",
        "fear": "the new visitor had brought a secret bottle",
        "cause": "a warm lunch pouch had leaked beneath the tablecloth",
        "fix": "followed the muddy smear, found the pouch, and carried it to the cool kitchen",
        "object": "a striped lunch pouch",
        "ending": "the name cards fluttered above a clean table",
    },
    {
        "routine": "measured water for the seedlings",
        "alarm": "a noxious whiff slipped through the greenhouse",
        "clue": "a muddy line curved toward a loose floor tile",
        "fear": "a pipe under the greenhouse had burst",
        "cause": "a jar of fermented plant food had tipped into a shallow drain",
        "fix": "lifted the tile with a ruler, poured the mixture into a sealed bucket, and aired the room",
        "object": "a clay plant-food jar",
        "ending": "new seedlings stood in bright rows beneath the open windows",
    },
    {
        "routine": "prepared a welcome ribbon for the garden's first new member",
        "alarm": "a noxious odor stopped the introduction before it began",
        "clue": "muddo spotted the ribbon with dark fingerprints",
        "fear": "someone had ruined the welcome gift",
        "cause": "a curious mole had tunneled beneath the ribbon box and stirred damp soil into it",
        "fix": "shared clues, opened the box carefully, and moved the ribbon to a clean shelf",
        "object": "a yellow ribbon box",
        "ending": "the ribbon shone from the new member's watering can",
    },
    {
        "routine": "sketched the garden map on a folding board",
        "alarm": "a noxious scent came from the map cabinet",
        "clue": "muddo formed a small arrow toward the bottom drawer",
        "fear": "the garden map had hidden a dangerous secret",
        "cause": "a wet pair of boots had been stored beside a packet of old bulbs",
        "fix": "read the arrow, opened the drawer with a cloth, and carried the boots outside",
        "object": "a red map cabinet",
        "ending": "the finished map showed a sunny path around the aired cabinet",
    },
    {
        "routine": "placed tiny flags beside the herb beds",
        "alarm": "a noxious smell made the flags tremble in the breeze",
        "clue": "muddo dotted the flag that said BASIL",
        "fear": "the herb bed had been spoiled",
        "cause": "a cracked sack of mushroom soil had slid against the basil flag",
        "fix": "joined hands to move the sack and covered the soil before the rain",
        "object": "a white basil flag",
        "ending": "the basil leaves lifted toward the sun under their neat flag",
    },
]

NAMES = ["Luna", "Milo", "Sana", "Nia", "Theo", "Pia"]
HELPERS = ["Milo", "Theo", "Pia", "Oren"]
GARDENERS = ["Sana", "Nia", "Iris", "Ada"]


def tell_story(params: StoryParams) -> World:
    if params.detective == params.helper or params.detective == params.gardener:
        raise StoryError("The detective, helper, and gardener must be different people.")
    world = World(Place("the Lantern Garden"))
    detective = world.add(Entity(params.detective, "character", params.detective))
    helper = world.add(Entity(params.helper, "character", params.helper))
    gardener = world.add(Entity(params.gardener, "character", params.gardener))
    for ent in (detective, helper, gardener):
        ent.memes["curiosity"] = 1.0
        ent.memes["trust"] = 1.0

    seed = params.seed or 0
    arc = ARC_DATA[seed % len(ARC_DATA)]
    object_name = arc["object"]
    world.add(Entity("clue", "object", object_name))
    world.facts.update(
        detective=detective,
        helper=helper,
        gardener=gardener,
        arc=arc,
        clue_object=object_name,
        danger=arc["fear"],
        cause=arc["cause"],
        fix=arc["fix"],
        transformed=False,
    )

    world.say(
        f"{detective.label} was the young detective of the Lantern Garden. "
        f"One bright morning, {detective.label} {arc['routine']}, while "
        f"{gardener.label} checked the gate and {helper.label} carried a notebook."
    )
    world.say(
        f"It was also the day of an important introduction: {gardener.label} was welcoming "
        f"a new garden helper. Then {arc['alarm']}. Everyone stopped."
    )
    world.para()
    world.say(
        f"{detective.label} knelt beside the path. There was {arc['clue']}. "
        f"The muddy mark, called muddo by the gardeners, pointed toward {object_name}."
    )
    world.say(
        f"\"The smell is scary, but the clue can speak,\" said {detective.label}. "
        f"\"We should not touch anything alone,\" answered {helper.label}. "
        f"{gardener.label} nodded. \"Teamwork first.\""
    )
    world.say(
        f"They feared {arc['fear']}. The garden's small bell seemed to tick louder as "
        f"{detective.label} compared the footprints, {helper.label} held the lantern, "
        f"and {gardener.label} watched the safe path."
    )
    world.para()
    world.say(
        f"Together they discovered that {arc['cause']}. "
        f"\"So the mystery is not a monster,\" said {helper.label}. "
        f"\"No,\" said {detective.label}, \"but it still needs a careful fix.\""
    )
    world.say(f"They {arc['fix']}. The noxious smell faded, and the muddy clue became a useful lesson.")
    for ent in (detective, helper, gardener):
        ent.memes["confidence"] = 2.0
        ent.memes["relief"] = 1.0
    world.facts["transformed"] = True
    world.place.garden_safe = True
    world.say(
        f"The introduction could finally begin. {gardener.label} welcomed the new helper, "
        f"and {detective.label} explained how each teammate had solved one part of the case."
    )
    world.para()
    world.say(
        f"At sunset, {arc['ending']}. The garden was not merely less smelly; "
        f"it had been transformed into a place where clues, care, and teamwork made everyone braver."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly detective story about a noxious smell and a muddy muddo clue.",
        f"Show {f['detective'].label}, {f['helper'].label}, and {f['gardener'].label} using teamwork to solve a garden mystery.",
        "Include an introduction, a transformation, a brief dialogue exchange, and a final image showing the place became safer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    arc = f["arc"]
    return [
        QAItem(
            question=f"What was {f['detective'].label} doing before the noxious smell appeared?",
            answer=f"{f['detective'].label} was {arc['routine']} while {f['gardener'].label} checked the gate and {f['helper'].label} carried a notebook.",
        ),
        QAItem(
            question="What clue did the detectives find?",
            answer=f"They found that {arc['clue']}. The muddy mark, called muddo, pointed toward {arc['object']}.",
        ),
        QAItem(
            question="What did the team fear had happened?",
            answer=f"They feared {arc['fear']}. They did not rush; they examined the clue together.",
        ),
        QAItem(
            question="What caused the noxious smell?",
            answer=f"They discovered that {arc['cause']}.",
        ),
        QAItem(
            question="How did teamwork transform the garden?",
            answer=f"They {arc['fix']}. The smell faded, the introduction continued, and {arc['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does noxious mean?", "Noxious means harmful, unpleasant, or unhealthy."),
        QAItem("What is teamwork?", "Teamwork is when people cooperate and share jobs to reach a goal."),
        QAItem("What is a transformation?", "A transformation is a change from one condition or form into another."),
        QAItem("What is an introduction?", "An introduction is a first meeting or a way of presenting someone or something."),
        QAItem("What is muddo in this story?", "Muddo is the gardeners' name for the thick muddy clue left on the path or an object."),
    ]


ASP_RULES = r"""
safe_garden :- teamwork, cause_found, careful_fix.
cause_found :- clue_examined, noxious_source_identified.
careful_fix :- shared_jobs, safe_tools.
transformed :- safe_garden.
introduction_ready :- transformed.
#show transformed/0.
#show introduction_ready/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("teamwork"),
            asp.fact("clue_examined"),
            asp.fact("noxious_source_identified"),
            asp.fact("shared_jobs"),
            asp.fact("safe_tools"),
        ]
    )


def asp_program(show: str = "#show transformed/0.\n#show introduction_ready/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    names = {str(symbol) for symbol in model}
    return sorted(name for name in names if name in {"transformed", "introduction_ready"})


def asp_verify() -> int:
    expected = ["introduction_ready", "transformed"]
    actual = asp_outcome()
    if actual == expected:
        print("OK: ASP and Python agree that the garden transformed and the introduction is ready.")
        return 0
    print(f"MISMATCH: python={expected} asp={actual}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A teamwork detective story about muddo and a noxious mystery.")
    parser.add_argument("--place", choices=["lantern_garden"], default=None)
    parser.add_argument("--detective", choices=NAMES, default=None)
    parser.add_argument("--helper", choices=HELPERS, default=None)
    parser.add_argument("--gardener", choices=GARDENERS, default=None)
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
    detective = args.detective or rng.choice(NAMES)
    helper_options = [x for x in HELPERS if x != detective]
    helper = args.helper or rng.choice(helper_options)
    gardener_options = [x for x in GARDENERS if x not in {detective, helper}]
    gardener = args.gardener or rng.choice(gardener_options)
    return StoryParams(
        place=args.place or "lantern_garden",
        detective=detective,
        helper=helper,
        gardener=gardener,
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
            f"  {entity.id}: kind={entity.kind}, label={entity.label}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  place: {world.place.name}, garden_safe={world.place.garden_safe}")
    lines.append(f"  facts: {world.facts}")
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
        samples = [
            generate(
                StoryParams(
                    place="lantern_garden",
                    detective="Luna",
                    helper="Milo",
                    gardener="Sana",
                    seed=base_seed + i,
                )
            )
            for i in range(len(ARC_DATA))
        ]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            seed = base_seed + index
            index += 1
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
