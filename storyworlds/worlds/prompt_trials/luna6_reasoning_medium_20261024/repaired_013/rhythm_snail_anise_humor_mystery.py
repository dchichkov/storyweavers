#!/usr/bin/env python3
"""A playful little mystery world of a rhythmic snail and anise-scented clues."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent))
        break

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the crooked clock garden"
    detective: str = "Lina"
    friend: str = "Bo"
    snail: str = "Pip"
    case: str = "missing_clock_beat"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "the crooked clock garden": {
        "key": "clock_garden",
        "mood": "full of leaning clocks and twitchy flowers",
    },
    "the Buttonberry fair": {
        "key": "buttonberry_fair",
        "mood": "bright with bunting and wobbly stalls",
    },
    "the moonlit bakery lane": {
        "key": "moonlit_bakery_lane",
        "mood": "warm with oven smells and silver shadows",
    },
}


@dataclass(frozen=True)
class MysteryCase:
    title: str
    object_name: str
    problem: str
    clue: str
    exchange: str
    investigation: str
    reveal: str
    resolution: str
    ending: str
    problem_answer: str
    clue_answer: str
    reveal_answer: str
    resolution_answer: str


CASE_REGISTRY = {
    "missing_clock_beat": MysteryCase(
        title="The Case of the Missing Middle Beat",
        object_name="the brass garden clock",
        problem=(
            "Just before the flower parade, the brass garden clock lost its middle "
            "beat: tick, tock, ... tick. Without it, the marchers kept stepping "
            "on their own toes."
        ),
        clue=(
            "An anise smell drifted from the clock's open case, and a silvery snail "
            "trail curled up beside one tiny gear."
        ),
        exchange=(
            '“Pip was right by the clock,” said {friend}. “Maybe he swallowed the '
            'beat.” “My shell taps a steady rhythm,” said {detective}. “Let’s find '
            'out what stopped the gear before we blame our snail.”'
        ),
        investigation=(
            "They listened to Pip tap a steady rhythm on his shell, then followed "
            "the anise smell from the clock to the baker’s basket."
        ),
        reveal=(
            "A seed of anise had slipped from a bun and wedged itself between the "
            "clock’s small gears. Pip had followed the delicious smell, not stolen "
            "a single beat."
        ),
        resolution=(
            "Lina lifted out the seed with a twig while Bo held the case steady. "
            "The baker replaced the bun in his basket, and the clock started "
            "ticking evenly again."
        ),
        ending=(
            "Pip led the parade at a snail’s pace, and every marcher finally "
            "stepped on the same beat"
        ),
        problem_answer=(
            "The brass garden clock had lost its middle beat, so the flower "
            "parade could not march together."
        ),
        clue_answer=(
            "The friends noticed an anise smell near the clock and a silvery trail "
            "beside its gears."
        ),
        reveal_answer=(
            "A seed of anise from a baker’s bun had jammed the clock. Pip had only "
            "followed the smell and had not taken the beat."
        ),
        resolution_answer=(
            "Lina removed the seed while Bo steadied the clock case, and the baker "
            "kept his buns safely in his basket. The clock ticked evenly again."
        ),
    ),
    "humming_parade_drum": MysteryCase(
        title="The Drum That Hummed Like a Pigeon",
        object_name="the parade drum",
        problem=(
            "At the Buttonberry fair, the parade drum made a low hum instead of a "
            "bold boom. The dancers tried to follow it, but their feet began "
            "wobbling like pudding."
        ),
        clue=(
            "A sharp anise scent clung to the drum, and Pip’s shiny trail made a "
            "curious little loop beside its wooden stand."
        ),
        exchange=(
            '“Pip has circled the drum,” said {friend}. “Perhaps he is the hum’s '
            'secret drummer.” “He taps a much tidier rhythm than that,” said '
            '{detective}. “Let’s check what the drum is hiding.”'
        ),
        investigation=(
            "They followed the anise scent to a paper wrapper caught beneath the "
            "drum’s rim. Pip tapped twice, paused, and tapped twice again, showing "
            "them where the rim had stopped vibrating."
        ),
        reveal=(
            "An anise biscuit wrapper had blown under the rim and muffled the drum. "
            "Pip had circled it because the wrapper smelled like his favorite "
            "bakery treat."
        ),
        resolution=(
            "Bo eased the wrapper out, and Lina carried it to the rubbish bin. "
            "The drummer gave the skin a gentle test; its clear boom returned."
        ),
        ending=(
            "Pip tapped his shell from the front row while the dancers bounced "
            "along to a proper boom"
        ),
        problem_answer=(
            "The parade drum hummed instead of booming, and the dancers could not "
            "keep their steps together."
        ),
        clue_answer=(
            "The friends found an anise scent on the drum and Pip’s trail looping "
            "beside its stand."
        ),
        reveal_answer=(
            "A paper wrapper from an anise biscuit had blown under the drum’s rim "
            "and muffled its sound. Pip had followed the tasty smell."
        ),
        resolution_answer=(
            "Bo removed the wrapper, and Lina put it in the rubbish bin. The drum "
            "could vibrate freely and make a clear boom again."
        ),
    ),
    "silent_fountain_polka": MysteryCase(
        title="The Fountain’s Vanishing Polka",
        object_name="the little fountain",
        problem=(
            "One evening in the moonlit bakery lane, the little fountain stopped "
            "playing its bubbling polka. Its water wheel turned once, shuddered, "
            "and fell silent."
        ),
        clue=(
            "A faint anise scent floated over the water, and Pip’s trail ended "
            "beside the wheel with a neat pattern of shell taps in the mud."
        ),
        exchange=(
            '“Pip has left a rhythm beside the wheel,” said {friend}. “Could he '
            'have turned it off?” “He can show us where to look,” said '
            '{detective}. “Let’s follow the anise smell and listen carefully.”'
        ),
        investigation=(
            "They listened as Pip tapped a slow, steady rhythm. Each tap matched "
            "the wheel’s one free turn, so they looked between its spokes."
        ),
        reveal=(
            "A crumpled anise wrapper was wedged between two spokes. A gust had "
            "carried it from the bakery lane, and the stuck wheel could not keep "
            "the fountain’s polka going."
        ),
        resolution=(
            "Lina held the wheel still while Bo pulled the wrapper free. They "
            "placed it in a bin, and the water began turning the wheel smoothly."
        ),
        ending=(
            "Pip tapped along beside the bubbling fountain, whose moonlit water "
            "played the polka once more"
        ),
        problem_answer=(
            "The fountain’s water wheel stopped after one turn, and the bubbling "
            "polka went quiet."
        ),
        clue_answer=(
            "The friends noticed anise in the air and found Pip’s trail beside "
            "the wheel."
        ),
        reveal_answer=(
            "A gust had blown an anise wrapper from the bakery lane, and it became "
            "wedged between the fountain wheel’s spokes."
        ),
        resolution_answer=(
            "Lina steadied the wheel while Bo removed the wrapper and put it in a "
            "bin. The wheel turned freely, bringing the fountain’s music back."
        ),
    ),
}


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join(
        (params.setting, params.detective, params.friend, params.snail, params.case)
    )
    return sum((index + 1) * ord(char) for index, char in enumerate(text))


def _valid_python() -> list[str]:
    if not CASE_REGISTRY:
        return []
    return sorted(info["key"] for info in SETTING_REGISTRY.values())


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting!r}. Choose a listed setting.")
    if params.case not in CASE_REGISTRY:
        raise StoryError(f"Unknown mystery case: {params.case!r}. Choose a listed case.")
    names = (params.detective, params.friend, params.snail)
    if any(not name.strip() for name in names):
        raise StoryError("The detective, friend, and snail must each have a name.")
    if len({name.casefold() for name in names}) != len(names):
        raise StoryError("The detective, friend, and snail must have different names.")


def _story_text(world: World) -> str:
    facts = world.facts
    case: MysteryCase = facts["case_data"]
    detective = facts["detective"]
    friend = facts["friend"]
    snail = facts["snail"]
    setting = facts["setting"]
    exchange = case.exchange.format(detective=detective, friend=friend)
    investigation = case.investigation.replace("Pip", snail)
    reveal = case.reveal.replace("Pip", snail)
    ending = case.ending.replace("Pip", snail)

    if facts["prose_variant"] == 0:
        paragraphs = [
            f'At {setting}, {detective} and {friend} were the neighborhood’s '
            f'junior mystery-solvers. Their snail, {snail}, came along at his '
            f'own careful pace. Their newest case was called “{case.title}.”',
            case.problem,
            f"{case.clue} “Anise again,” murmured {detective}.",
            exchange,
            f"{investigation} {reveal}",
            f"{case.resolution} By bedtime, {ending}.",
        ]
    elif facts["prose_variant"] == 1:
        paragraphs = [
            f"The mystery began at {setting}, where {detective}, {friend}, and "
            f"{snail} were enjoying a quiet afternoon. Then came “{case.title}.”",
            case.problem,
            f"{friend} spotted the first clue: {case.clue}",
            exchange,
            f"They worked it out together. {investigation} {reveal} "
            f"{case.resolution}",
            f"At last, {ending}. The strange rhythm was a mystery no longer.",
        ]
    else:
        paragraphs = [
            f"“A mystery!” cried {friend} at {setting}. {detective} opened a "
            f"notebook, and {snail} stretched his feelers toward the sound. "
            f"The case was “{case.title}.”",
            case.problem,
            f"{case.clue} The friends crouched to inspect it.",
            exchange,
            f"Following the clues, they learned the truth. {investigation} "
            f"{reveal}",
            f"{case.resolution} Soon, {ending}. {detective} wrote down the "
            f"answer, though {snail} tried to eat the corner of the page.",
        ]
    return "\n\n".join(paragraphs)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    seed = _stable_seed(params)
    case = CASE_REGISTRY[params.case]
    setting_info = SETTING_REGISTRY[params.setting]

    world = World(setting=params.setting)
    detective = world.add(
        Entity(
            params.detective,
            "child detective",
            meters={"clue_attention": 0.7, "confidence": 0.5},
            memes={"curiosity": 1.0, "fairness": 1.0},
        )
    )
    friend = world.add(
        Entity(
            params.friend,
            "child helper",
            meters={"careful_listening": 0.7},
            memes={"cooperation": 1.0, "humor": 1.0},
        )
    )
    snail = world.add(
        Entity(
            params.snail,
            "snail",
            meters={"shell_tap_rhythm": 0.8, "trail_length": 0.6},
            memes={"patience": 1.0, "curiosity": 0.8},
        )
    )
    mystery_object = world.add(
        Entity(
            case.object_name,
            "mystery object",
            meters={"rhythm_before": 0.2, "rhythm_after": 1.0, "obstruction": 1.0},
            memes={"mystery": 1.0},
        )
    )
    anise = world.add(
        Entity("anise clue", "scented clue", meters={"scent_strength": 0.8}, memes={"evidence": 1.0})
    )
    world.facts.update(
        detective=detective.name,
        friend=friend.name,
        snail=snail.name,
        setting=params.setting,
        setting_mood=setting_info["mood"],
        case=params.case,
        case_data=case,
        mystery_object=mystery_object.name,
        clue=anise.name,
        obstruction_removed=True,
        prose_variant=(seed // max(1, len(CASE_REGISTRY))) % 3,
        outcome="The obstruction was found and removed; the rhythm returned.",
    )
    mystery_object.meters["obstruction"] = 0.0
    mystery_object.meters["rhythm_after"] = 1.0
    detective.meters["clue_attention"] = 1.0
    friend.meters["careful_listening"] = 1.0
    snail.meters["shell_tap_rhythm"] = 1.0

    story = _story_text(world)
    prompts = [
        f"Write a humorous, child-friendly mystery at {params.setting} starring "
        f"{params.detective}, {params.friend}, and a rhythm-loving snail.",
        "Use anise as a real clue, and let a spoken exchange change the "
        "characters’ decision.",
        "End with a concrete image showing that the missing rhythm has returned.",
    ]
    story_qa = [
        QAItem(
            question=f"What went wrong in “{case.title}”?",
            answer=case.problem_answer,
        ),
        QAItem(
            question="What clues helped the friends investigate?",
            answer=case.clue_answer,
        ),
        QAItem(
            question=f"What did {params.detective} and {params.friend} discover?",
            answer=case.reveal_answer,
        ),
        QAItem(
            question="How did the friends put things right?",
            answer=case.resolution_answer,
        ),
        QAItem(
            question="What final image shows that the mystery was solved?",
            answer=f"The story ends with {case.ending.replace('Pip', params.snail)}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is rhythm?",
            answer="Rhythm is a pattern of sounds or movements that repeats in time, like a steady tap or beat.",
        ),
        QAItem(
            question="What is anise?",
            answer="Anise is a fragrant spice with a sweet, distinctive smell that can flavor foods such as biscuits.",
        ),
        QAItem(
            question="How can a snail leave a trail?",
            answer="A snail moves on a soft, moist foot and can leave a shiny trail of mucus behind it.",
        ),
        QAItem(
            question="How do detectives use clues?",
            answer="Detectives notice and compare clues so they can work out what happened instead of guessing.",
        ),
        QAItem(
            question="What makes a mystery humorous?",
            answer="A humorous mystery uses playful surprises or silly moments while still giving a clear answer to the puzzle.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


ASP_RULES = r"""
feature(humor).
case_has_clue(C) :- case(C), clue(C).
can_tell_story(S) :- setting(S), feature(humor), case_has_clue(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("setting", data["key"])
        for data in SETTING_REGISTRY.values()
    ]
    lines.append(asp.fact("feature", "humor"))
    for case_name in CASE_REGISTRY:
        lines.append(asp.fact("case", case_name))
        lines.append(asp.fact("clue", case_name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _asp_valid() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    python_models = {(setting,) for setting in _valid_python()}
    clingo_models = set(_asp_valid())
    if python_models != clingo_models:
        print("MISMATCH between clingo and Python reasonableness gates:")
        print("Python only:", sorted(python_models - clingo_models))
        print("clingo only:", sorted(clingo_models - python_models))
        return 1

    exercised = 0
    for setting in SETTING_REGISTRY:
        for case_name in CASE_REGISTRY:
            params = StoryParams(
                setting=setting,
                detective="Lina",
                friend="Bo",
                snail="Pip",
                case=case_name,
                seed=exercised,
            )
            sample = generate(params)
            required = ("rhythm", "snail", "anise")
            if (
                not all(word in sample.story.lower() for word in required)
                or "said" not in sample.story
                or "{" in sample.story
                or not sample.story_qa
                or sample.world is None
                or sample.world.entities[CASE_REGISTRY[case_name].object_name]
                .meters["obstruction"]
                != 0.0
            ):
                print(f"Generated-story verification failed for {setting}, {case_name}.")
                return 1
            exercised += 1

    print(
        f"OK: clingo gate matches Python ({len(python_models)} settings); "
        f"{exercised} generated stories passed."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A humorous mystery world of anise clues and a rhythmic snail."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--detective")
    parser.add_argument("--friend")
    parser.add_argument("--snail")
    parser.add_argument("--case", choices=list(CASE_REGISTRY))
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
    params = StoryParams(
        setting=args.setting or rng.choice(list(SETTING_REGISTRY)),
        detective=args.detective or rng.choice(["Lina", "Ari", "Nell", "Tavi"]),
        friend=args.friend or rng.choice(["Bo", "Mira", "Oren", "Kit"]),
        snail=args.snail or rng.choice(["Pip", "Moss", "Dot", "Professor Slime"]),
        case=args.case or rng.choice(list(CASE_REGISTRY)),
    )
    reasonableness_gate(params)
    return params


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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )
        print(f"world facts: {sample.world.facts['outcome']}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1 and not (args.all or args.verify or args.asp or args.show_asp):
        raise SystemExit("-n must be at least 1.")

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return
    if args.verify:
        try:
            raise SystemExit(asp_verify())
        except ImportError as error:
            raise SystemExit(f"ASP verification requires clingo: {error}") from error
    if args.asp:
        try:
            for row in _asp_valid():
                print(row[0])
        except ImportError as error:
            raise SystemExit(f"ASP mode requires clingo: {error}") from error
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    try:
        if args.all:
            index = 0
            for setting in SETTING_REGISTRY:
                for case_name in CASE_REGISTRY:
                    samples.append(
                        generate(
                            StoryParams(
                                setting=setting,
                                detective=args.detective or "Lina",
                                friend=args.friend or "Bo",
                                snail=args.snail or "Pip",
                                case=case_name,
                                seed=base_seed + index,
                            )
                        )
                    )
                    index += 1
        else:
            seen: set[str] = set()
            attempt = 0
            while len(samples) < args.n and attempt < max(100, args.n * 100):
                seed = base_seed + attempt
                attempt += 1
                rng = random.Random(seed)
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
                if sample.story not in seen:
                    seen.add(sample.story)
                    samples.append(sample)
            if len(samples) < args.n:
                raise StoryError("Could not make the requested number of distinct stories.")
    except StoryError as error:
        raise SystemExit(str(error)) from error

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
