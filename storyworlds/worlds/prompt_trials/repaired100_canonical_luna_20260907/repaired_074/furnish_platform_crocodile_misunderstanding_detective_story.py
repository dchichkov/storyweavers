#!/usr/bin/env python3
"""
A small detective story world about furnishing a platform, a crocodile, and a
misunderstanding solved by careful clues.
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
    kind: str
    label: str
    location: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("fear", "confusion", "comfort", "risk", "trust", "curiosity"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)


@dataclass(frozen=True)
class Case:
    key: str
    platform: str
    furnishing: str
    clue: str
    misunderstanding: str
    crocodile_action: str
    detective_question: str
    reveal: str
    repair: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    detective: str
    helper: str
    crocodile: str = "Cora"
    case: str = "lantern_platform"
    style: str = "detective"
    variation: int = 0
    seed: Optional[int] = None


CASES = [
    Case(
        "lantern_platform",
        "the riverside platform",
        "three striped cushions and a brass lantern",
        "muddy half-moon prints stopped beside the missing lantern hook",
        "the villagers thought the crocodile had stolen the lantern because its tail marks crossed the boards",
        "Cora hid beneath the platform, nudging the loose hook with her nose",
        "Why would a hungry crocodile carry a lantern past the water?",
        "The prints belonged to Cora, but the lantern had fallen through a gap and was glowing under the platform.",
        "The detective tied the hook tight, placed the lantern on a high shelf, and furnished the platform with a safe basking mat.",
        "At sunset, Cora rested beside the warm mat while the lantern shone above her.",
        "A frightening clue can have a gentle explanation.",
    ),
    Case(
        "market_platform",
        "the floating market platform",
        "a blue rug, two stools, and a basket of apples",
        "one apple sat beside a neat row of tooth-shaped dents",
        "the fruit sellers believed the crocodile had eaten the whole basket",
        "Cora had pushed the basket away from a dripping roof",
        "Why were the apples dry when the crocodile's snout was wet?",
        "Rain had rolled the basket, while Cora's teeth had marked the wooden rim as she moved it.",
        "The detective furnished the platform with a covered table and a sign asking visitors to leave fruit for animals.",
        "The sellers shared one apple with Cora, and the floating market bobbed peacefully.",
        "A mark may show what happened without proving why it happened.",
    ),
    Case(
        "music_platform",
        "the little music platform",
        "a red bench, a drum, and a velvet music stand",
        "the drumbeat stopped whenever green scales appeared near the steps",
        "the musicians thought the crocodile was chasing them away",
        "Cora had been following a loose drum strap that dragged into the reeds",
        "What did Cora follow before the music stopped?",
        "The strap belonged to the drum, and Cora was trying to pin it beneath her foot.",
        "The detective repaired the strap and furnished a quiet corner where Cora could listen from a distance.",
        "The band played a soft tune, and Cora blinked along with the beat.",
        "Understanding an action means looking for its object.",
    ),
    Case(
        "bridge_platform",
        "the bridge-watch platform",
        "a rain coat, a telescope, and a wooden chair",
        "the telescope pointed at the river while three claw marks circled the chair",
        "the bridge keeper thought the crocodile had been spying on travelers",
        "Cora had leaned against the chair to reach a fish-shaped weather vane",
        "Could a crocodile's short legs really look through the high telescope?",
        "The chair had moved in the wind, and Cora had only bumped it while chasing the vane's shadow.",
        "The detective furnished the platform with a low viewing box and fastened the chair to the floor.",
        "Cora watched the river from the low box as boats passed safely below.",
        "A witness should check the size and reach of the suspect.",
    ),
]

NAMES = ["Mara", "Theo", "Iris", "Niko", "Jules", "Pia", "Ren", "Sol"]


class World:
    def __init__(self, params: StoryParams, case: Case) -> None:
        self.params = params
        self.case = case
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def setup_world(params: StoryParams) -> World:
    case = next((item for item in CASES if item.key == params.case), None)
    if case is None:
        raise StoryError(f"Unknown detective case: {params.case}")
    world = World(params, case)
    world.add(Entity(params.detective, "character", params.detective, case.platform))
    world.add(Entity(params.helper, "character", params.helper, case.platform))
    world.add(Entity(params.crocodile, "animal", params.crocodile, "riverbank"))
    world.add(Entity("platform", "place", case.platform, case.platform))
    world.add(Entity("furnishings", "things", case.furnishing, case.platform))
    return world


def tell_story(world: World) -> None:
    p = world.params
    c = world.case
    detective = world.entities[p.detective]
    helper = world.entities[p.helper]
    crocodile = world.entities[p.crocodile]

    detective.memes["curiosity"] += 1
    helper.memes["curiosity"] += 0.5
    crocodile.meters["fear"] += 0.5
    crocodile.meters["comfort"] += 0.5

    world.say(
        f"{p.detective} was a careful detective, and {p.helper} was a quick helper."
    )
    world.say(
        f"Together they had been asked to furnish {c.platform} with {c.furnishing}."
    )
    world.say(
        f"But before the work began, someone cried, 'The crocodile did it!' "
        f"{p.crocodile} was resting near the river, and a strange clue waited on the boards."
    )

    world.para()
    world.say(c.clue + ".")
    world.say(
        f"The villagers pointed at {p.crocodile}. {c.misunderstanding.capitalize()}."
    )
    world.say(
        f'"Cora looks scary," said {p.helper}, "but what exactly did she do?"'
    )
    world.say(
        f'"I do not know yet," said {p.detective}. "A detective asks before deciding."'
    )
    helper.meters["confusion"] += 1
    crocodile.meters["fear"] += 1
    world.say(f"{p.crocodile} gave a low rumble and slipped behind the platform.")

    world.para()
    world.say(f"{p.detective} examined the boards, the river mud, and the furnishings.")
    world.say(f"The first question was simple: {c.detective_question}")
    world.say(f"{p.helper} crouched down and found that {c.crocodile_action}.")
    world.say(f'"Look!" said {p.helper}. "The clue points somewhere else."')
    world.say(
        f'"Then we should follow the clue, not the rumor," said {p.detective}.'
    )
    detective.memes["trust"] += 1
    helper.memes["trust"] += 1
    crocodile.meters["fear"] -= 0.5
    world.say(c.reveal)

    world.para()
    world.say(c.repair)
    world.say(
        f"{p.detective} explained, 'We mistook a nearby mark for proof. "
        f"A real answer must fit every clue.'"
    )
    world.say(f"{p.helper} nodded. 'And {p.crocodile} needed help, not blame.'")
    crocodile.meters["comfort"] += 1
    crocodile.memes["trust"] += 1
    world.say(c.ending)
    world.say(c.lesson)

    world.facts.update(
        detective=detective,
        helper=helper,
        crocodile=crocodile,
        clue=c.clue,
        misunderstanding=c.misunderstanding,
        question=c.detective_question,
        action=c.crocodile_action,
        reveal=c.reveal,
        repair=c.repair,
        ending=c.ending,
        lesson=c.lesson,
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    c = world.case
    return [
        QAItem(
            "Who solved the misunderstanding?",
            f"{p.detective} solved it with help from {p.helper}.",
        ),
        QAItem(
            "What was being furnished?",
            f"They were furnishing {c.platform} with {c.furnishing}.",
        ),
        QAItem(
            "Why did people blame the crocodile?",
            c.misunderstanding.capitalize() + ".",
        ),
        QAItem(
            "What question did the detective ask?",
            c.detective_question,
        ),
        QAItem(
            "What was the crocodile really doing?",
            c.crocodile_action.capitalize() + ".",
        ),
        QAItem(
            "How was the mystery resolved?",
            c.reveal + " " + c.repair,
        ),
        QAItem(
            "What changed at the end?",
            c.ending,
        ),
        QAItem(
            "What lesson did the detective learn?",
            c.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a platform?",
            "A platform is a raised or floating place where people or objects can stand.",
        ),
        QAItem(
            "What does furnish mean?",
            "To furnish a place means to supply it with useful or pleasant things.",
        ),
        QAItem(
            "What is a crocodile?",
            "A crocodile is a large reptile with a long body, strong jaws, and a tail.",
        ),
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gives a wrong meaning to words, actions, or clues.",
        ),
        QAItem(
            "What does a detective do?",
            "A detective studies clues and asks careful questions to discover what happened.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        "Write a child-friendly detective story about furnishing a platform where a crocodile is blamed because of a misunderstanding.",
        "Tell a short mystery in which a detective follows physical clues instead of trusting a rumor about a crocodile.",
        "Create a gentle detective tale with a platform, furnishings, a crocodile, dialogue, and a resolved misunderstanding.",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective story world about furnishing a platform and solving a crocodile misunderstanding."
    )
    parser.add_argument("--detective")
    parser.add_argument("--helper")
    parser.add_argument("--crocodile", default="Cora")
    parser.add_argument("--case", choices=[case.key for case in CASES])
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective = args.detective
    helper = args.helper
    if detective and helper and detective == helper:
        raise StoryError("The detective and helper must have different names.")
    if not detective or not helper:
        chosen = rng.sample(NAMES, 2)
        detective = detective or chosen[0]
        helper = helper or chosen[1]
    if detective == args.crocodile:
        raise StoryError("The detective and crocodile must have different names.")
    return StoryParams(
        detective=detective,
        helper=helper,
        crocodile=args.crocodile,
        case=args.case or rng.choice(CASES).key,
        variation=rng.getrandbits(63),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: kind={entity.kind} location={entity.location} "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
character(X) :- detective(X).
character(X) :- helper(X).
animal(cora).
place(platform).
misunderstanding :- blamed(cora), nearby_mark.
resolved :- misunderstanding, checked_clue, explained.
safe_platform :- resolved, furnished.
#show misunderstanding/0.
#show resolved/0.
#show safe_platform/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("detective", "mara"),
            asp.fact("helper", "theo"),
            asp.fact("blamed", "cora"),
            asp.fact("nearby_mark"),
            asp.fact("checked_clue"),
            asp.fact("explained"),
            asp.fact("furnished"),
        ]
    )


def asp_program(show: str = "#show.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        model = asp.one_model(asp_program("#show safe_platform/0."))
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if any(symbol.name == "safe_platform" for symbol in model):
        for params in (
            StoryParams("Mara", "Theo", case="lantern_platform", variation=1),
            StoryParams("Iris", "Niko", case="market_platform", variation=2),
        ):
            sample = generate(params)
            if "misunderstanding" not in sample.story.lower():
                print("MISMATCH: generated story lacks the misunderstanding.")
                return 1
        print("OK: ASP and Python both resolve the detective world.")
        return 0
    print("MISMATCH: ASP twin did not produce a safe platform.")
    return 1


CURATED = [
    StoryParams("Mara", "Theo", case="lantern_platform", variation=11),
    StoryParams("Iris", "Niko", case="market_platform", variation=22),
    StoryParams("Jules", "Pia", case="music_platform", variation=33),
    StoryParams("Ren", "Sol", case="bridge_platform", variation=44),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/0.\n#show resolved/0.\n#show safe_platform/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp

            model = asp.one_model(asp_program("#show misunderstanding/0.\n#show resolved/0."))
            print("ASP model:")
            for symbol in model:
                print(symbol)
            return
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(1, args.n)):
            rng = random.Random(seed + index)
            samples.append(generate(resolve_params(args, rng)))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
