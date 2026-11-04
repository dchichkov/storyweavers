#!/usr/bin/env python3
"""A small heartwarming storyworld about a mattress, an orthodontist, and a stake.

Luna is curious about the soft glow beneath her old mattress. With help from her
orthodontist and a little harmless magic, she discovers how to save the moonlit
garden she loves. The “bad ending” is a possible outcome the characters notice
and prevent, rather than a frightening ending for the reader.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.isfile(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "a little house beside a moonlit garden"
SEED_WORDS = ("mattress", "orthodontist", "stake")


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        for key in ("glow", "stability", "dryness"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "kindness", "wonder"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    child: str = "Luna"
    orthodontist: str = "Dr. Rowan"
    case: int = 0
    telling: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    clue: str
    magic: str
    risk: str
    bad_ending: str
    discovery: str
    repair: str
    proof: str
    image: str


CASES = [
    Case(
        clue="a silver-blue glow pulsing beneath the mattress",
        magic="a tiny moon-moth made of light fluttered out from under it",
        risk="if the garden stake tipped, the young moonflower would lie across the wet path",
        bad_ending="the flower might have been crushed before morning",
        discovery="found the garden's little moonstone caught in a loose seam",
        repair="slid the moonstone into a cloth pouch and set the mattress back on its dry frame",
        proof="the glow now rested safely beside the flower, and the mattress no longer sagged",
        image="the moonflower opened beside the steady stake, bright as a small lantern",
    ),
    Case(
        clue="a warm sparkle shining through a tear in the mattress cover",
        magic="a thread of golden light curled around Luna's curious finger",
        risk="a leaning stake could scrape the garden's paper lantern when the wind rose",
        bad_ending="the lantern might tear and leave the path dark",
        discovery="found a glowing seed tucked inside the mattress cover",
        repair="placed the seed in the garden bed and tied the loose lantern safely to its stake",
        proof="the lantern stayed still in the breeze while the seed gave one gentle glow",
        image="a new green shoot stood beneath the lantern, with dew shining on its first leaf",
    ),
    Case(
        clue="three little star-shaped marks on the mattress near the window",
        magic="a blue spark answered when Luna whispered, “Who is there?”",
        risk="the garden stake was wobbling beside a row of sleepy tulips",
        bad_ending="the stake could fall into the tulips and bend their stems",
        discovery="found a small, friendly star spirit hiding in the mattress's old patch",
        repair="helped the star spirit return to the night sky and pressed the stake firmly into the earth",
        proof="the tulips stood untouched, and one star twinkled back through the window",
        image="the tulips nodded beneath a clear sky where a new star shone",
    ),
    Case(
        clue="a quiet chime coming from beneath the mattress whenever the wind blew",
        magic="a soft silver ribbon rose into the air and pointed toward the garden",
        risk="a loose stake near the pond could slip into the water",
        bad_ending="the garden's little bell might disappear in the pond",
        discovery="found the bell's missing clapper tucked beside the mattress frame",
        repair="returned the clapper to the garden bell and secured the stake in firm soil",
        proof="the bell rang once without wobbling, and nothing slid toward the pond",
        image="a clear note drifted over the pond as the first stars appeared",
    ),
]


@dataclass
class World:
    child: Entity
    orthodontist: Entity
    mattress: Entity
    stake: Entity
    garden: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    return World(
        child=Entity(params.child, "character", params.child),
        orthodontist=Entity(params.orthodontist, "character", params.orthodontist),
        mattress=Entity("mattress", "bedroom object", "old mattress", location="bedroom"),
        stake=Entity("stake", "garden tool", "wooden garden stake", location="garden"),
        garden=Entity("garden", "place", "moonlit garden", location="outside"),
    )


def tell(params: StoryParams) -> World:
    if not params.child.strip() or not params.orthodontist.strip():
        raise StoryError("The child and orthodontist need names.")
    if params.child.strip().casefold() == params.orthodontist.strip().casefold():
        raise StoryError("The child and orthodontist must be different people.")
    if not 0 <= params.case < len(CASES):
        raise StoryError(f"case must be between 0 and {len(CASES) - 1}.")
    if params.telling not in range(4):
        raise StoryError("telling must be between 0 and 3.")

    w = build_world(params)
    child, doctor, mattress, stake = w.child, w.orthodontist, w.mattress, w.stake
    case = CASES[params.case]
    child.memes["curiosity"] = 2
    child.memes["worry"] = 1
    mattress.meters["glow"] = 1
    stake.meters["stability"] = 0.3
    stake.location = "beside the young moonflower"

    openings = [
        f"At the edge of {THEME}, {child.id} had just made a soft landing on the old mattress after a visit to {doctor.id}, the friendly orthodontist.",
        f"{child.id} was meant to be asleep, but the old mattress shimmered in the little house beside the moonlit garden. Earlier, {doctor.id}, the orthodontist, had reminded {child.id} to keep a gentle bedtime routine.",
        f"When {doctor.id}, {child.id}'s orthodontist, said good night, a strange sparkle appeared beside the old mattress in the house by the garden.",
        f"The evening was quiet in the little house beside the moonlit garden. {child.id} was settling onto the mattress when {doctor.id}, the orthodontist, noticed a faint glow.",
    ]
    w.say(openings[params.telling])
    w.say(f"{child.id} leaned closer. {case.clue}.")
    w.para()
    child.memes["curiosity"] += 1
    w.say(f"“I wonder what it means,” said {child.id}. “Let’s look carefully, not pull at anything,” said {doctor.id}.")
    w.say(f"Then {case.magic}. The gentle light showed them the garden outside, where {case.risk}.")
    w.say(f"{doctor.id} explained, “If we ignore it, {case.bad_ending}. We can still make things safe.”")
    w.para()
    w.say(f"Together they followed the glow without disturbing the mattress and {case.discovery}.")
    w.say(f"“I thought the sparkle was only a trick,” {child.id} said. “Your question helped us notice what needed care,” {doctor.id} replied.")
    w.say(f"They chose a kind, careful fix: they {case.repair}.")
    mattress.meters["glow"] = 0
    mattress.meters["stability"] = 1
    mattress.location = "dry frame in the bedroom"
    stake.meters["stability"] = 1
    stake.location = "firm soil beside the flower"
    child.memes["worry"] = 0
    child.memes["wonder"] = 2
    doctor.memes["kindness"] = 1
    w.say(f"They checked their work together: {case.proof}.")
    w.para()
    w.say(f"The bad ending they had imagined did not happen. Instead, {case.image}.")
    w.facts.update(
        case=case,
        child=child,
        orthodontist=doctor,
        mattress=mattress,
        stake=stake,
        resolved=True,
    )
    return w


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    child: Entity = world.facts["child"]
    doctor: Entity = world.facts["orthodontist"]
    return [
        QAItem(
            question=f"What made {child.id} curious?",
            answer=f"{child.id} noticed {case.clue}. Following the glow carefully led to a small discovery rather than a guess.",
        ),
        QAItem(
            question="What bad ending did the characters hope to prevent?",
            answer=f"They worried that {case.bad_ending}. They acted in time by making the garden safe.",
        ),
        QAItem(
            question=f"How did {doctor.id} help?",
            answer=f"{doctor.id} listened to {child.id}'s question and helped {child.id} investigate gently. Together they {case.repair}.",
        ),
        QAItem(
            question="How could they tell their solution worked?",
            answer=f"They checked the result and saw that {case.proof}.",
        ),
    ]


def world_knowledge_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an orthodontist do?",
            answer="An orthodontist is a dentist who helps teeth grow and line up in healthy ways, sometimes using braces or other gentle treatments.",
        ),
        QAItem(
            question="What is a mattress?",
            answer="A mattress is the soft, supportive part of a bed that people lie on to rest or sleep.",
        ),
        QAItem(
            question="What is a garden stake used for?",
            answer="A garden stake is a firm stick pushed into the soil to support a plant or hold something in place.",
        ),
        QAItem(
            question="What does curiosity help someone do?",
            answer="Curiosity encourages someone to ask questions and look closely. Careful curiosity can lead to learning without taking unsafe risks.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    return [
        f"Tell a heartwarming, child-friendly story about a mattress, an orthodontist, and a garden stake. Include gentle magic and curiosity.",
        f"Let {case.clue} lead to a careful discovery, and show the characters preventing a bad ending through teamwork.",
        "End with a concrete, peaceful image that proves the problem changed.",
    ]


def format_qa(sample: StorySample) -> str:
    sections = [
        ("== (1) Generation prompts ==", sample.prompts),
        ("== (2) Story questions ==", sample.story_qa),
        ("== (3) World-knowledge questions ==", sample.world_qa),
    ]
    out: list[str] = []
    for title, items in sections:
        out.append(title)
        for i, item in enumerate(items, 1):
            if isinstance(item, QAItem):
                out.extend((f"Q: {item.question}", f"A: {item.answer}"))
            else:
                out.append(f"{i}. {item}")
        out.append("")
    return "\n".join(out).rstrip()


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (world.child, world.orthodontist, world.mattress, world.stake, world.garden):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: kind={entity.kind}; location={entity.location}; "
            f"meters={meters}; memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
required(mattress).
required(orthodontist).
required(stake).
feature(bad_ending).
feature(magic).
feature(curiosity).
style(heartwarming).
valid_story :- required(mattress), required(orthodontist), required(stake),
               feature(bad_ending), feature(magic), feature(curiosity),
               style(heartwarming).
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [asp.fact("required", word) for word in SEED_WORDS]
    facts.extend(asp.fact("feature", feature) for feature in ("bad_ending", "magic", "curiosity"))
    facts.append(asp.fact("style", "heartwarming"))
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    symbols = asp.one_model(asp_program())
    valid = any(atom.name == "valid_story" for atom in symbols)
    py_valid = set(SEED_WORDS) == {"mattress", "orthodontist", "stake"}
    py_valid = py_valid and {"bad_ending", "magic", "curiosity"} == {
        "bad_ending", "magic", "curiosity"
    }
    if not valid or not py_valid:
        print("MISMATCH: ASP/Python story-domain reasonableness gates disagree.")
        return 1
    for i in range(len(CASES)):
        sample = generate(StoryParams(case=i, seed=i))
        if not sample.story or not sample.story.endswith(CASES[i].image + "."):
            print(f"MISMATCH: generated case {i} did not resolve as expected.")
            return 1
        if not any("“" in sample.story and "”" in sample.story for _ in (0,)):
            print(f"MISMATCH: generated case {i} has no spoken exchange.")
            return 1
    print("OK: ASP/Python parity and all generated story cases passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming mattress-and-magic storyworld.")
    parser.add_argument("--name", default=None, help="Name of the curious child.")
    parser.add_argument("--orthodontist", default=None, help="Name of the orthodontist.")
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


def resolve_params(
    args: argparse.Namespace, rng: random.Random, sample_seed: int, base_seed: int
) -> StoryParams:
    child = args.name or rng.choice(["Luna", "Milo", "Nia", "Theo", "Suri"])
    orthodontist = args.orthodontist or rng.choice(
        ["Dr. Rowan", "Dr. Bell", "Dr. Moss", "Dr. Ellis"]
    )
    if child.strip().casefold() == orthodontist.strip().casefold():
        raise StoryError("The child and orthodontist must be different people.")
    offset = sample_seed - base_seed
    return StoryParams(
        child=child,
        orthodontist=orthodontist,
        case=offset % len(CASES),
        telling=(offset // len(CASES)) % 4,
        seed=sample_seed,
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
    sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(child="Luna", orthodontist="Dr. Rowan", case=0),
    StoryParams(child="Milo", orthodontist="Dr. Bell", case=1),
    StoryParams(child="Nia", orthodontist="Dr. Moss", case=2),
    StoryParams(child="Theo", orthodontist="Dr. Ellis", case=3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        print("ASP model:", [str(atom) for atom in asp.one_model(asp_program())])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            sample_seed = base_seed + i
            params = resolve_params(args, random.Random(sample_seed), sample_seed, base_seed)
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        sys.exit(2)
