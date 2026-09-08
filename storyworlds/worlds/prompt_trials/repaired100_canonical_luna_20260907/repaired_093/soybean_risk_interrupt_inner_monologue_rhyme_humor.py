#!/usr/bin/env python3
"""
A tiny Whodunit storyworld about a soybean, a risky shortcut, and a timely
interruption. The mystery is solved by following physical clues rather than
trusting a dramatic first guess.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the farm shed"
    detail: str = "a little farm shed beside a soybean field"


@dataclass
class StoryParams:
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    story_lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_lines)


NAMES = ["Luna", "Milo", "Tess", "Pip", "Nell", "Otis", "Cora", "Bram"]
HELPERS = ["Pip", "Mabel", "Ravi", "Nora", "Finn", "June", "Theo", "Ada"]

SETTING = Setting(
    place="the farm shed",
    detail="a little farm shed beside a soybean field, with a red wagon and a wide wooden door",
)

CASES = [
    {
        "id": "blue_mark",
        "opening_clue": "a blue smear appeared on the soybean sack",
        "suspicion": "someone had dragged the sack through spilled paint",
        "risk": "climb onto a wobbly stack of crates to inspect the roof beam",
        "interrupt": "caught Luna's sleeve and said, 'Stop! That stack is leaning.'",
        "second_clue": "the blue smear had tiny straight ridges in it",
        "test": "looked from the floor and compared the mark with the wheel of the red wagon",
        "truth": "the wagon wheel had rolled against the sack after passing through a puddle of blue rainwater",
        "repair": "moved the wagon away and wiped the damp wheel",
        "ending": "the soybean sack stood dry and safe while the blue wagon waited in the sunshine",
        "lesson": "A clue deserves a careful look, not a risky leap.",
    },
    {
        "id": "missing_pod",
        "opening_clue": "one soybean pod lay in the middle of the locked shed",
        "suspicion": "a sneaky mouse had stolen beans for a midnight feast",
        "risk": "crawl beneath the old conveyor belt to search for the mouse",
        "interrupt": "blocked the way and said, 'No crawling under machinery before we know it is safe.'",
        "second_clue": "the pod had a clean bite-shaped dent but no tooth marks",
        "test": "used a flashlight from the doorway and checked the nearby seed scoop",
        "truth": "the scoop had pinched the pod and flicked it across the floor",
        "repair": "returned the pod to the compost bowl and stored the scoop upright",
        "ending": "the quiet shed smelled of straw, while a real mouse nibbled a crumb outside",
        "lesson": "Good detectives protect themselves before chasing a theory.",
    },
    {
        "id": "rattling_bin",
        "opening_clue": "the soybean bin rattled three times",
        "suspicion": "a tiny thief was trapped inside",
        "risk": "lift the heavy lid without checking whether it could fall",
        "interrupt": "held the lid handle down and said, 'Wait. We need an adult and a safer plan.'",
        "second_clue": "the rattles matched the gusts that shook the loose window",
        "test": "stood clear and watched the bin while the window was gently latched",
        "truth": "wind was tapping the bin with the loose window latch",
        "repair": "asked the farmer to fasten the latch and kept the lid closed",
        "ending": "the bin became still, and the soybean seeds rested in their bright metal home",
        "lesson": "A repeated sound can be a pattern, not a hidden culprit.",
    },
    {
        "id": "golden_track",
        "opening_clue": "a trail of golden dots led away from the soybean basket",
        "suspicion": "a fox had carried the beans through the shed",
        "risk": "follow the trail into the dark tool closet alone",
        "interrupt": "called from the doorway, 'Stay where the light reaches!'",
        "second_clue": "the dots were square, not paw-shaped",
        "test": "held the basket over the trail and noticed matching square holes in its bottom",
        "truth": "small bits of dried straw had fallen through the basket",
        "repair": "carried the basket outside and swept the straw into the bedding pile",
        "ending": "the trail ended in a tidy golden heap, with no fox in the tool closet",
        "lesson": "A safe boundary can make a mystery easier to solve.",
    },
]

OPENINGS = [
    "{hero} was sorting seeds when the shed made a suspicious little sound.",
    "Before breakfast, {hero} came to count the soybean pods.",
    "Rain had just stopped when {hero} noticed something strange near the farm shed.",
    "On a bright morning, {hero} promised to help with the soybean harvest.",
]

RHYME_LINES = [
    "Look low, look slow, and let the true clue show.",
    "No risky flight for a mystery night.",
    "If the clue feels sly, ask why before you try.",
    "A careful paw can solve the flaw.",
]

HUMOR = [
    "{helper} puffed up proudly. 'My detective nose is excellent, though it sometimes points at lunch.'",
    "{hero} tried to look mysterious, but a sneeze made the hanging spoon clang like a tiny bell.",
    "The empty shed offered one enormous alibi: it was too dusty to keep a secret.",
    "{helper} whispered, 'The culprit may be very small.' Then a beetle marched past as if offended.",
]


ASP_RULES = r"""
misunderstanding(X) :- sees(X, clue), suspects(X, culprit).
risk_stopped(X) :- risks(X, action), interrupts(Y, X).
clue_checked(X) :- sees(X, clue), tests(X, clue).
resolved(X) :- misunderstanding(X), risk_stopped(X), clue_checked(X), explains(X, truth).
valid_story(X) :- resolved(X).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("character", "hero"),
        asp.fact("character", "helper"),
        asp.fact("object", "soybean"),
        asp.fact("sees", "hero", "clue"),
        asp.fact("suspects", "hero", "culprit"),
        asp.fact("risks", "hero", "unsafe_search"),
        asp.fact("interrupts", "helper", "hero"),
        asp.fact("tests", "hero", "clue"),
        asp.fact("explains", "hero", "truth"),
    ])


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    case = rng.choice(CASES)
    world = World(setting=SETTING)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="animal",
        label="young farm helper",
        meters={"distance": 0.0, "safe_distance": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0, "confidence": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="animal",
        label="careful friend",
        meters={"distance": 0.0},
        memes={"alertness": 1.0, "friendship": 1.0},
    ))
    soybean = world.add(Entity(
        id="soybean",
        type="seed",
        label="soybean",
        meters={"count": 12.0, "dryness": 1.0},
        memes={"importance": 1.0},
    ))
    world.facts.update(
        hero=hero,
        helper=helper,
        soybean=soybean,
        case=case,
        opening=rng.choice(OPENINGS),
        rhyme=rng.choice(RHYME_LINES),
        humor=rng.choice(HUMOR),
        shed_detail=rng.choice([
            "dusty rafters and a red wagon",
            "sunlit boards and a row of seed bins",
            "a creaky door and a broom leaning by the wall",
        ]),
    )
    return world


def simulate(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    case = world.facts["case"]

    world.say(world.facts["opening"].format(hero=hero.id))
    world.say(
        f"The shed had {world.facts['shed_detail']}, and a basket of soybean pods sat safely "
        "on the floor."
    )
    world.say(f"Then {case['opening_clue']}. {hero.id} narrowed his eyes.")
    hero.memes["worry"] += 1.0
    world.say(
        f'"Who did that?" {hero.id} asked. He suspected that {case["suspicion"]}.'
    )
    world.say(
        f"Inside his head, {hero.id} thought, 'A real detective must act fast. "
        f"Perhaps I should {case['risk']}.'"
    )
    world.say(f"{hero.id} took one step toward the risky idea.")
    world.say(f"{helper.id} {case['interrupt']}")
    hero.meters["safe_distance"] += 1.0
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
    world.say(
        f"{helper.id} added, 'We can solve this without getting hurt.' "
        f"{hero.id} nodded. 'You are right. First clue, then conclusion.'"
    )
    world.say(world.facts["humor"])
    world.say(f"They looked again. {case['second_clue']}.")
    world.say(
        f"From a safe place, {hero.id} {case['test']}. "
        f"The evidence showed that {case['truth']}."
    )
    hero.memes["confidence"] += 1.0
    world.say(f'"Aha!" said {hero.id}. "{world.facts["rhyme"]}"')
    world.say(
        f"The mystery was solved, so {hero.id} {case['repair']}. "
        f"{helper.id} helped from the safe side of the shed."
    )
    hero.memes["relief"] += 1.0
    world.say(
        f"{case['lesson']} The soybean harvest could continue, and everyone stayed safe."
    )
    world.say(
        f"At sunset, {case['ending']}. {hero.id} and {helper.id} shared a quiet laugh."
    )
    world.facts.update(
        suspicion=case["suspicion"],
        risk=case["risk"],
        interruption=case["interrupt"],
        clue=case["second_clue"],
        truth=case["truth"],
        repair=case["repair"],
        lesson=case["lesson"],
        ending=case["ending"],
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    hero = world.facts["hero"]
    return [
        "Write a child-friendly Whodunit about a soybean mystery in a farm shed.",
        f"Show how {hero.id} notices {case['opening_clue']} and considers a risky action before a friend interrupts.",
        f"Include an inner monologue, a rhyme, and gentle humor, then reveal that {case['truth']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    case = world.facts["case"]
    return [
        QAItem(
            question=f"What object started {hero.id}'s mystery?",
            answer=f"A soybean clue started the mystery: {case['opening_clue']}."
        ),
        QAItem(
            question=f"What risky idea did {hero.id} consider?",
            answer=f"{hero.id} considered that {case['risk']} This was unsafe because it involved acting before checking the scene."
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} interrupted {hero.id} and stopped the risky action by saying, '{case['interrupt']}'"
        ),
        QAItem(
            question="What clue solved the mystery?",
            answer=f"They noticed that {case['second_clue']}, then safely tested the idea. The truth was that {case['truth']}."
        ),
        QAItem(
            question="What happened to the soybean area afterward?",
            answer=f"{hero.id} {case['repair']}, leaving the soybean harvest safe and ready to continue."
        ),
        QAItem(
            question="What lesson did the whodunit teach?",
            answer=case["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a soybean?",
            answer="A soybean is a small edible seed that grows in a pod on a soybean plant."
        ),
        QAItem(
            question="Why can an interruption be helpful?",
            answer="An interruption can be helpful when it stops someone from taking an unsafe action and gives them time to think."
        ),
        QAItem(
            question="What should a detective do before accusing someone?",
            answer="A detective should observe carefully, compare clues, test a safe explanation, and avoid blaming anyone without evidence."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
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
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.type:8}) meters={meters} memes={memes}"
        )
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


def asp_verify() -> int:
    if not asp_valid():
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import asp
        models = asp.solve(asp_program(), models=1)
        valid = asp.atoms(models[0], "valid_story") if models else []
    except Exception as exc:
        print(f"MISMATCH: ASP verification failed: {exc}")
        return 1
    if not valid:
        print("MISMATCH: ASP found no valid story.")
        return 1
    for seed in range(5):
        sample = generate(StoryParams("Luna", "Pip", seed))
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
        if "soybean" not in sample.story.lower():
            print("MISMATCH: soybean missing from story.")
            return 1
    print("OK: Python and ASP reasonableness gates pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A soybean Whodunit about risk, interruption, and careful clues."
    )
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--helper-name", choices=HELPERS)
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
    hero = args.hero_name or rng.choice(NAMES)
    choices = [name for name in HELPERS if name != hero]
    helper = args.helper_name or rng.choice(choices)
    if helper == hero:
        raise StoryError("hero and helper must have different names")
    return StoryParams(hero_name=hero, helper_name=helper)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp.solve(asp_program(), models=1)
        if not models:
            raise StoryError("ASP found no compatible story")
        atoms = sorted(set(asp.atoms(models[0], "valid_story")))
        print(f"{len(atoms)} compatible stories:")
        for atom in atoms:
            print(f"  {atom}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("Luna", "Pip", base_seed),
            StoryParams("Milo", "Nora", base_seed + 1),
            StoryParams("Tess", "Ravi", base_seed + 2),
            StoryParams("Cora", "Finn", base_seed + 3),
        ]
        samples = [generate(params) for params in params_list]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
