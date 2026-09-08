#!/usr/bin/env python3
"""A child-friendly mystery at a pond where a horned visitor leaves a clue."""

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str = "the pond"
    first_name: str = "Luna"
    second_name: str = "Milo"
    mystery: str = "the missing silver bell"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    key: str
    opening: str
    trouble: str
    clue: str
    wrong_guess: str
    method: str
    jobs: tuple[str, str]
    reveal: str
    lesson: str
    ending: str


SETTINGS = {"the pond": True, "the reed pond": True, "the lily pond": True}
NAMES = ["Luna", "Milo", "Iris", "Theo", "Nia", "Pip", "Sora", "Bea"]
MYSTERIES = [
    "the missing silver bell",
    "the vanished blue feather",
    "the lost lily crown",
    "the quiet frog drum",
]

CASES = [
    Case(
        "muddy-hoofprint",
        "They had come to listen for the little bell beside the reeds.",
        "The bell was gone, and a line of muddy marks led away from its empty hook.",
        "The marks had two small points at the front and stopped beside a flat stone.",
        "A duck had carried the bell into the water.",
        "follow the marks without disturbing them, then inspect the stone",
        ("held a twig beside the first print for comparison",
         "knelt near the stone and watched the ripples"),
        "A horned snail had nudged the bell under the stone while searching for shade.",
        "A mystery is solved by careful clues, not the biggest guess.",
        "The silver bell rested on the stone, ringing softly whenever the horned snail passed.",
    ),
    Case(
        "ripple-circle",
        "They were drawing pictures of the pond when the blue feather disappeared.",
        "A round ripple widened beside the lily pads, but no bird stood there.",
        "The ripple began behind a floating leaf and carried one bright down feather.",
        "A fish had swallowed the feather and was hiding below.",
        "watch the water's path and lift only the leaf at the end of the ripple",
        ("counted each ripple from the bank",
         "used a reed to guide the leaf toward the shallow edge"),
        "A horned beetle had fallen onto the leaf and pushed it in circles with its tiny legs.",
        "Good detectives let the trail show them where to look.",
        "The blue feather dried on a warm rock while the horned beetle climbed safely home.",
    ),
    Case(
        "bent-reed",
        "They had made a crown from lily stems for the pond's friendly frog.",
        "The crown vanished between breakfast and their afternoon visit.",
        "One reed was bent toward the muddy bank, and its tip held a golden thread.",
        "The wind had blown the crown into the deep water.",
        "follow the bent reeds and compare the thread with things near the bank",
        ("marked the reeds that leaned toward shore",
         "searched the grass without stepping on the soft mud"),
        "A horned caterpillar had dragged the crown to a leaf shelter, where the golden thread caught on a thorn.",
        "Small evidence can answer a large question when friends share their work.",
        "The lily crown sat on the frog's rock, beside the horned caterpillar's curled leaf.",
    ),
    Case(
        "quiet-drum",
        "They brought a tiny drum to call the frogs for a moonlit song.",
        "The drum made no sound, although its skin looked smooth.",
        "Three damp dots crossed the drum and ended beneath a reed basket.",
        "Rain had filled the drum and ruined its voice.",
        "trace the damp dots and lift the basket slowly",
        ("checked the drum's dry rim",
         "followed the dots with a strip of bark"),
        "A horned toad had sheltered beneath the basket and pressed the drum's loose strap.",
        "A quiet object may be hiding a living cause.",
        "The drum sounded again while the horned toad watched from a dry patch of moss.",
    ),
    Case(
        "moon-shadow",
        "They saw a strange shadow beside the pond and decided to solve its secret.",
        "The shadow had horns, but no creature stood where the moonlight pointed.",
        "A reed bent over the water, making two sharp tips on the mud.",
        "A horned monster was hiding under the dock.",
        "move one lantern and compare the shadow with the reeds",
        ("held the lantern low near the bank",
         "measured the shadow against the bent reed"),
        "The horns belonged to the reed's shadow; a harmless turtle had moved the stalk.",
        "Changing one safe detail can test a frightening idea.",
        "The shadow became an ordinary reed while the turtle blinked beneath the dock.",
    ),
    Case(
        "shell-trail",
        "They found a bright shell beside the pond and wanted to return it.",
        "A trail of pale scratches led away, but the shell's owner was nowhere near.",
        "The scratches curved around a patch of moss and ended at a tiny horned snail.",
        "A crab had taken the shell and left the trail.",
        "match the scratch width to the creatures near the moss",
        ("laid three reeds beside the scratches",
         "observed the snail without touching its shell"),
        "The horned snail had polished the shell by dragging it over the moss.",
        "A clue should fit the creature that made it.",
        "The shell shone beside the horned snail, exactly where the trail ended.",
    ),
]

OPENINGS = [
    "At dawn, {a} and {b} met beside {setting} with curious eyes.",
    "A pale mist hovered over {setting} when {a} and {b} began their investigation.",
    "Near {setting}, {a} noticed something unusual before the frogs began to sing.",
    "The pond was still, and that made {a} and {b} notice every tiny sound.",
    "One silver glint beside {setting} was enough to start a mystery.",
    "Before breakfast, {a} and {b} brought their detective notebooks to {setting}.",
]

DIALOGUE = [
    "'What do you see?' asked {a}. 'Only what the clue tells us,' said {b}.",
    "'Should we guess?' whispered {b}. 'Not yet,' replied {a}. 'We need one more sign.'",
    "{a} pointed at the trail. 'This mark matters.' {b} nodded. 'Then we will follow it gently.'",
    "'I am a little worried,' said {b}. 'We can be careful together,' answered {a}.",
    "'The pond is telling us a story,' said {a}. 'We just need to listen,' said {b}.",
]

REFLECTIONS = [
    "They paused instead of rushing toward the first exciting answer.",
    "Their question changed from 'Who did it?' to 'What made this mark?'",
    "The friends compared the clue before deciding what it meant.",
    "Careful looking made the mystery feel smaller and clearer.",
    "They agreed that a good detective protects the pond while searching.",
    "Each friend noticed a different part of the same trail.",
]


def generate_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("The mystery must take place at a supported pond.")
    if params.first_name == params.second_name:
        raise StoryError("The two young detectives must have different names.")
    world = World(params.setting)
    first = world.add(Entity("detective_a", "character", params.first_name))
    second = world.add(Entity("detective_b", "character", params.second_name))
    mystery = world.add(Entity("mystery", "object", params.mystery))
    visitor = world.add(Entity("visitor", "animal", "the horned visitor"))

    value = abs(params.seed or 0)
    case = CASES[value % len(CASES)]
    opening = OPENINGS[(value // len(CASES)) % len(OPENINGS)]
    dialogue = DIALOGUE[(value // 17) % len(DIALOGUE)]
    reflection = REFLECTIONS[(value // 31) % len(REFLECTIONS)]

    world.say(opening.format(a=first.label, b=second.label, setting=params.setting))
    world.say(case.opening)
    world.say(f"They were searching for {mystery.label}, the small object that made their pond visits special.")
    world.say(dialogue.format(a=first.label, b=second.label))
    world.para()

    world.say(case.trouble)
    world.say(f"Near the water, they found a clue: {case.clue}")
    world.say(f"{first.label} wondered aloud, 'Could it be true that {case.wrong_guess[0].lower() + case.wrong_guess[1:]}?'")
    world.say(f"{second.label} shook their head. 'Let us test that idea safely.'")
    world.say(reflection)
    world.para()

    world.say(f"Their plan was to {case.method}.")
    world.say(f"{first.label} {case.jobs[0]}, while {second.label} {case.jobs[1]}.")
    world.say(f"Together they discovered the answer: {case.reveal}")
    world.say(f"The horned visitor was not a villain. It had simply been part of the pond's small, busy life.")
    world.para()

    world.say(f"{first.label} smiled. 'Now we know what happened.'")
    world.say(f"{second.label} replied, 'And we did not harm the pond while finding out.'")
    world.say(f"They returned {mystery.label} to its proper place. {case.ending}")
    world.say(f"Their mystery lesson was clear: {case.lesson}")

    first.memes.update(curiosity=1.0, care=1.0)
    second.memes.update(curiosity=1.0, teamwork=1.0)
    mystery.meters.update(found=1.0, returned=1.0)
    visitor.memes.update(harmless=1.0)
    world.facts.update(
        first=first.label,
        second=second.label,
        mystery=mystery.label,
        case=case.key,
        trouble=case.trouble,
        clue=case.clue,
        wrong_guess=case.wrong_guess,
        method=case.method,
        first_job=case.jobs[0],
        second_job=case.jobs[1],
        reveal=case.reveal,
        lesson=case.lesson,
        ending=case.ending,
        found=True,
        returned=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    return [
        QAItem(
            question=f"What mystery did {facts['first']} and {facts['second']} investigate?",
            answer=f"They investigated the disappearance of {facts['mystery']}. They searched near the pond for a clue instead of simply guessing.",
        ),
        QAItem(
            question="What clue helped the detectives?",
            answer=f"The important clue was that {facts['clue']}. It gave them a trail to test.",
        ),
        QAItem(
            question="What did the detectives first wonder?",
            answer=f"They wondered whether {facts['wrong_guess']}. They did not accept that guess until they checked the evidence.",
        ),
        QAItem(
            question="How did the two friends solve the mystery?",
            answer=f"They planned to {facts['method']}. {facts['first']} {facts['first_job']}, while {facts['second']} {facts['second_job']}.",
        ),
        QAItem(
            question="What did they learn at the end?",
            answer=f"They learned that {facts['lesson']} In the ending image, {facts['ending']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something not yet understood. People solve it by collecting clues and testing careful explanations.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a detail that helps explain what happened, such as a mark, a sound, or a changed object.",
        ),
        QAItem(
            question="Why should pond detectives be gentle?",
            answer="They should be gentle so animals, plants, water, and evidence are not harmed or disturbed.",
        ),
        QAItem(
            question="What does horned mean?",
            answer="Horned means having horns or horn-like points. A horned animal may use them for defense, display, or identification.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a child-friendly pond mystery about {facts['first']} and {facts['second']} finding {facts['mystery']}.",
        f"Create a dialogue mystery in which the clue is that {facts['clue']}.",
        "Tell a gentle mystery story about a horned pond visitor, careful evidence, and a satisfying ending.",
    ]


ASP_RULES = r"""
mystery_solved(M) :- mystery(M), clue_found(M), found(M), returned(M).
careful_search(A,B) :- detective(A), detective(B), A != B, shared_plan(A,B).
safe_resolution(M) :- mystery_solved(M), careful_search(_, _), harmless_visitor.
#show mystery_solved/1.
#show careful_search/2.
#show safe_resolution/1.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("detective", "luna"),
        asp.fact("detective", "milo"),
        asp.fact("mystery", "silver_bell"),
        asp.fact("clue_found", "silver_bell"),
        asp.fact("found", "silver_bell"),
        asp.fact("returned", "silver_bell"),
        asp.fact("shared_plan", "luna", "milo"),
        asp.fact("harmless_visitor"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program("#show mystery_solved/1. #show safe_resolution/1."))
    solved = asp.atoms(symbols, "mystery_solved")
    safe = asp.atoms(symbols, "safe_resolution")
    if solved and safe:
        print("OK: ASP found a careful, safe mystery resolution.")
        return 0
    print("MISMATCH: ASP did not find the expected resolution.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--first-name")
    parser.add_argument("--second-name")
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    first = args.first_name or rng.choice(NAMES)
    second = args.second_name or rng.choice([name for name in NAMES if name != first])
    if first == second:
        raise StoryError("The two young detectives must have different names.")
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        first_name=first,
        second_name=second,
        mystery=args.mystery or rng.choice(MYSTERIES),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("the pond", "Luna", "Milo", "the missing silver bell", 7),
    StoryParams("the reed pond", "Iris", "Theo", "the vanished blue feather", 19),
    StoryParams("the lily pond", "Nia", "Pip", "the lost lily crown", 33),
]


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        facts = sample.world.facts
        print(
            f"\n--- world model state ---\n"
            f"case={facts['case']} found={facts['found']} returned={facts['returned']}"
        )
    if qa:
        for index, item in enumerate(sample.story_qa, 1):
            print(f"Q{index}: {item.question}\nA{index}: {item.answer}")
        for index, item in enumerate(sample.world_qa, 1):
            print(f"W{index}: {item.question}\nA{index}: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery_solved/1. #show careful_search/2. #show safe_resolution/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base + index))
            params.seed = base + index
            samples.append(generate(params))

    if args.asp:
        import asp

        symbols = asp.one_model(asp_program("#show mystery_solved/1."))
        if not asp.atoms(symbols, "mystery_solved"):
            raise StoryError("ASP reasonableness check failed.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], ensure_ascii=False, indent=2))
        return

    for index, sample in enumerate(samples):
        emit(sample, args.trace, args.qa, f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
