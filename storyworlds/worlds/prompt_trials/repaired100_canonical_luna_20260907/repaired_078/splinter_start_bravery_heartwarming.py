#!/usr/bin/env python3
"""A heartwarming, state-driven StoryWorld about a splinter, a brave start, and care."""

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
sys.path.insert(0, str(STORYWORLDS_DIR.parent))
from results import QAItem, StoryError, StorySample  # noqa: E402


TITLE = "The Splinter's Brave Start"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    child_name: str = "Lina"
    helper_name: str = "Grandma Jo"
    place: str = "the little garden shed"
    project: str = "a birdhouse"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    name: str
    material: str
    problem: str
    clue: str
    first_try: str
    consequence: str
    brave_words: str
    care_plan: str
    resolution: str
    ending: str


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


INCIDENTS = [
    Incident(
        "rough pine",
        "rough pine",
        "a tiny splinter slipped into Lina's palm when she held the rough board",
        "the splinter pointed toward a pale line in the wood",
        "pulled at the splinter with her fingernail",
        "the sharp tip bent and made her hand sting more",
        '"I am scared, but I can make a careful start."',
        "Grandma Jo washed the hand, brought a clean pair of tweezers, and asked Lina to breathe and look",
        "the splinter came out in one gentle pull",
        "Lina finished the birdhouse, and a sparrow soon balanced on its little roof",
    ),
    Incident(
        "wobbly bench",
        "old cedar",
        "a splinter hid beneath the edge of the bench where Lina wanted to sit",
        "a bright thread from her sleeve caught on one rough spot",
        "slid her hand across the edge to find the sharp place",
        "the thread tugged harder and the hidden splinter stayed put",
        '"I can begin with one safe look instead of a rushed grab."',
        "Grandma Jo placed the bench in the sunlight, brushed away dust, and showed Lina the exact raised grain",
        "the splinter lifted safely after the wood was steadied",
        "the repaired bench stood beneath the apple tree, ready for neighbors and their stories",
    ),
    Incident(
        "wooden kite",
        "light willow",
        "a splinter caught in Lina's finger while she tied a string to the wooden kite frame",
        "the loose end of the string rested beside the tiny brown point",
        "pulled the string quickly and hoped the splinter would follow",
        "the knot tightened while her finger still hurt",
        '"Bravery can sound like, ‘Please help me take the next small step.’"',
        "Grandma Jo loosened the knot, washed the spot, and held the frame while Lina watched",
        "the splinter was removed and the string was tied without a pinch",
        "the kite rose over the meadow, carrying Lina's brave smile into the warm afternoon",
    ),
    Incident(
        "painted crate",
        "painted fir",
        "a splinter poked through a chipped patch on the crate Lina was carrying",
        "the blue paint had lifted around one narrow crack",
        "covered the spot with her thumb and kept carrying",
        "the crate wobbled and the sharp place pressed deeper",
        '"I do not have to hide a hurt before I ask for care."',
        "Grandma Jo set down the crate, marked the crack, and brought a soft cloth and tweezers",
        "the splinter came free before the crate was carried again",
        "the blue crate held tomatoes at supper, and Lina's hand felt calm beside the warm table",
    ),
    Incident(
        "window frame",
        "sunny maple",
        "a small splinter caught Lina as she opened the old window for fresh air",
        "a thin silver line showed where the frame had dried",
        "pushed the window harder instead of stopping",
        "the frame stuck and the prick grew sore",
        '"A brave start is stopping when something says, ‘Be gentle.’"',
        "Grandma Jo closed the window, checked the frame, and let Lina choose the safest place to sit",
        "the splinter was lifted and the frame was smoothed with sandpaper",
        "fresh air filled the room, and the curtains danced around the newly gentle window",
    ),
    Incident(
        "story stool",
        "warm beech",
        "a splinter hid under the seat of the stool Lina used during story time",
        "a tiny wood curl clung to the blanket beside the stool",
        "rubbed the seat to make the curl disappear",
        "the rubbing made the sore spot harder to see",
        '"I can be brave and careful at the same time."',
        "Grandma Jo turned the stool over, found the raised grain, and kept Lina's hand still",
        "the splinter came out, and the rough place was sanded smooth",
        "Lina sat beside Grandma Jo and read the first page aloud from the safe, smooth stool",
    ),
    Incident(
        "garden gate",
        "weathered oak",
        "a splinter caught Lina when she opened the garden gate for a sleepy puppy",
        "the gate's loose latch pointed toward a rough board",
        "opened the gate with a fast tug",
        "the puppy paused while Lina's hand began to throb",
        '"I will start again slowly, because the puppy and I both need care."',
        "Grandma Jo held the gate steady, moved the puppy back, and checked the board in daylight",
        "the splinter was removed and the latch was tightened",
        "the puppy trotted through the gate, and Lina welcomed it with a gentle pat",
    ),
    Incident(
        "little toolbox",
        "smooth-looking ash",
        "a nearly invisible splinter entered Lina's finger while she reached for a wooden ruler",
        "the ruler had one rough corner beside its bright brass mark",
        "picked up every tool at once to finish quickly",
        "the ruler slid and the splinter became harder to see",
        '"Courage begins when I tell the truth about what hurts."',
        "Grandma Jo cleared the tools, washed Lina's finger, and used the brass mark to find the rough corner",
        "the splinter was removed and the ruler was sanded",
        "the toolbox closed with a soft click, holding tools that were ready for careful work",
    ),
]


PLACES = [
    "the little garden shed",
    "the sunny back porch",
    "the neighborhood workshop",
    "the apple-tree corner",
]

PROJECTS = [
    "a birdhouse",
    "a small flower box",
    "a wooden treasure chest",
    "a reading bench",
]

CHILDREN = ["Lina", "Milo", "Nora", "Sam"]
HELPERS = ["Grandma Jo", "Uncle Ravi", "Aunt Mei", "Mr. Ellis"]


def choose_incident(params: StoryParams) -> Incident:
    seed = params.seed if params.seed is not None else 0
    return INCIDENTS[seed % len(INCIDENTS)]


def setup_world(params: StoryParams, incident: Incident) -> World:
    world = World(params.place)
    child = world.add(Entity(
        id="child",
        kind="character",
        type="brave_child",
        label=params.child_name,
        memes={"bravery": 0.0, "trust": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="trusted_helper",
        label=params.helper_name,
        memes={"care": 1.0},
    ))
    hand = world.add(Entity(
        id="hand",
        kind="body",
        type="hand",
        label=f"{params.child_name}'s hand",
        owner=child.id,
        meters={"comfort": 1.0, "hurt": 0.0},
    ))
    splinter = world.add(Entity(
        id="splinter",
        kind="object",
        type="splinter",
        label="the splinter",
        owner=incident.name,
        meters={"embedded": 1.0, "sharpness": 1.0},
    ))
    world.facts.update(
        child=child,
        helper=helper,
        hand=hand,
        splinter=splinter,
        incident=incident,
        project=params.project,
        place=params.place,
    )
    return world


def tell(params: StoryParams) -> World:
    incident = choose_incident(params)
    world = setup_world(params, incident)
    child = world.get("child")
    helper = world.get("helper")
    hand = world.get("hand")
    splinter = world.get("splinter")

    world.say(
        f"In {world.place}, {child.label} and {helper.label} were making {params.project} from {incident.material}."
    )
    world.say(
        f"They had gathered the pieces, swept the floor, and saved one bright patch of sunlight for their work."
    )
    world.para()

    world.say(f"Then {incident.problem}. {incident.clue.capitalize()}.")
    world.say(
        f"{child.label} took a quick breath. \"I want to be brave,\" {child.label} said, "
        f"\"but I do not know where to start.\""
    )
    world.say(f"For one hurried moment, {child.label} {incident.first_try}. As a result, {incident.consequence}.")
    child.memes["bravery"] = 0.25
    hand.meters["hurt"] = 1.0
    hand.meters["comfort"] = 0.0
    splinter.meters["embedded"] = 1.0
    world.fired.add(("hurried_start", incident.name))
    world.para()

    world.say(f"{helper.label} sat beside {child.label} instead of taking over.")
    world.say(
        f'"Bravery does not mean pretending nothing hurts," {helper.label} said. '
        f'"It means telling the truth and taking one safe step."'
    )
    world.say(f"{child.label} nodded. \"{incident.brave_words}\"")
    world.say(f"Together, they made a careful plan: {incident.care_plan}.")
    world.facts.update(
        clue=incident.clue,
        first_try=incident.first_try,
        consequence=incident.consequence,
        brave_words=incident.brave_words,
        care_plan=incident.care_plan,
    )
    child.memes["bravery"] = 0.75
    child.memes["trust"] = 1.0
    world.fired.add(("brave_start", incident.name))
    world.para()

    hand.meters["hurt"] = 0.0
    hand.meters["comfort"] = 1.0
    splinter.meters["embedded"] = 0.0
    splinter.meters["sharpness"] = 0.0
    child.memes["bravery"] = 1.0
    world.say(f"With the safe plan, {incident.resolution}.")
    world.say(
        f"{child.label} looked at the tiny splinter on the cloth. "
        f'"I was afraid," {child.label} said, "and asking for help made me brave."'
    )
    world.say(
        f'{helper.label} smiled. "A brave start can be very small. Sometimes it begins with saying, '
        f"'Please stay with me.'\""
    )
    world.say(f"By evening, {incident.ending}.")
    world.fired.add(("hurt_resolved", incident.name))
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    incident = facts["incident"]
    return [
        f"Write a heartwarming child-friendly story about {facts['child'].label} finding a splinter in {facts['place']}.",
        f"Show how {facts['child'].label} makes a brave start by asking {facts['helper'].label} for careful help.",
        f"Tell a complete story in which the splinter is safely resolved and {facts['project']} has a hopeful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child = facts["child"]
    helper = facts["helper"]
    incident = facts["incident"]
    return [
        QAItem(
            question=f"Where did {child.label} find the splinter?",
            answer=f"{child.label} found the splinter while working with {incident.material} in {world.place}.",
        ),
        QAItem(
            question="What happened when the first hurried attempt did not work?",
            answer=f"{child.label} {facts['first_try']}. Then {facts['consequence']}.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} stayed beside {child.label} and helped make a safe plan: {facts['care_plan']}.",
        ),
        QAItem(
            question="What did bravery mean in the story?",
            answer=f"Bravery meant telling the truth about the hurt, asking for help, and taking one careful step instead of pretending to feel fine.",
        ),
        QAItem(
            question="What changed by the ending?",
            answer=f"{incident.resolution.capitalize()}. {incident.ending.capitalize()}, and {child.label}'s hand was comfortable again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a splinter?",
            answer="A splinter is a tiny sharp piece of wood that can lodge in skin.",
        ),
        QAItem(
            question="What is a brave start?",
            answer="A brave start is a safe first step, such as telling a trusted grown-up when something hurts.",
        ),
        QAItem(
            question="Why should a child ask a trusted grown-up for help with a splinter?",
            answer="A trusted grown-up can help wash the area, look carefully, and decide on a safe way to remove the splinter or get medical help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World knowledge questions =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:9} ({entity.type:14}) {' '.join(details)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("feature", "bravery"),
        asp.fact("object", "splinter"),
        asp.fact("action", "start"),
        asp.fact("need", "care"),
        asp.fact("outcome", "safe"),
    ]
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for project in PROJECTS:
        lines.append(asp.fact("project", project))
    return "\n".join(lines)


ASP_RULES = r"""
brave_start :- feature(bravery), action(start), need(care).
safe_resolution :- object(splinter), brave_start, outcome(safe).
heartwarming_story :- safe_resolution, project(_), place(_).
#show brave_start/0.
#show safe_resolution/0.
#show heartwarming_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show brave_start/0. #show safe_resolution/0. #show heartwarming_story/0."))
    required = ("brave_start", "safe_resolution", "heartwarming_story")
    if all(asp.atoms(model, predicate) for predicate in required):
        for seed in range(8):
            sample = generate(StoryParams(seed=seed))
            if "splinter" not in sample.story.lower() or "brave" not in sample.story.lower():
                print("Story verification failed.")
                return 1
        print("OK: ASP and Python both describe a brave, caring splinter resolution.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming story world about a splinter, a brave start, and care."
    )
    parser.add_argument("--child-name", choices=CHILDREN, default=None)
    parser.add_argument("--helper-name", choices=HELPERS, default=None)
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--project", choices=PROJECTS, default=None)
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
    return StoryParams(
        child_name=args.child_name or rng.choice(CHILDREN),
        helper_name=args.helper_name or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        project=args.project or rng.choice(PROJECTS),
        seed=args.seed,
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


CURATED = [
    StoryParams(
        child_name="Lina",
        helper_name="Grandma Jo",
        place="the little garden shed",
        project="a birdhouse",
        seed=0,
    ),
    StoryParams(
        child_name="Milo",
        helper_name="Uncle Ravi",
        place="the sunny back porch",
        project="a small flower box",
        seed=1,
    ),
    StoryParams(
        child_name="Nora",
        helper_name="Aunt Mei",
        place="the neighborhood workshop",
        project="a wooden treasure chest",
        seed=2,
    ),
    StoryParams(
        child_name="Sam",
        helper_name="Mr. Ellis",
        place="the apple-tree corner",
        project="a reading bench",
        seed=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show brave_start/0. #show safe_resolution/0. #show heartwarming_story/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program(
                "#show brave_start/0. #show safe_resolution/0. #show heartwarming_story/0."
            )
        )
        for predicate in ("brave_start", "safe_resolution", "heartwarming_story"):
            print(asp.atoms(model, predicate))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {params.child_name} / {params.helper_name} / {params.project}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
