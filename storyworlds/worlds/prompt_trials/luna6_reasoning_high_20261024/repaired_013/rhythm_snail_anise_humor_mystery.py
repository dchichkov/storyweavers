#!/usr/bin/env python3
"""
A small comic mystery world about a snail, anise, and a rhythm that leads
careful young detectives to the truth.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


for _parent in Path(__file__).resolve().parents:
    if (_parent / "results.py").is_file():
        sys.path.insert(0, str(_parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the Moonbell herb garden"
    case: str = "watering_can"
    detective: str = "Iris"
    helper: str = "Bo"
    snail: str = "Mallow"
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

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent


SETTING_REGISTRY = {
    "the Moonbell herb garden": {
        "id": "moonbell_garden",
        "tags": {"can", "rack", "herbs"},
        "mood": "dewy and full of sleepy bees",
    },
    "the old glasshouse": {
        "id": "old_glasshouse",
        "tags": {"bamboo", "rack", "herbs"},
        "mood": "warm, leafy, and echoey",
    },
    "the village tea garden": {
        "id": "village_tea_garden",
        "tags": {"can", "rack", "herbs"},
        "mood": "bright with little garden tables",
    },
}


@dataclass(frozen=True)
class MysteryCase:
    title: str
    required_tag: str
    object_name: str
    opening: str
    trouble: str
    clue: str
    first_exchange: str
    snail_exchange: str
    reveal: str
    action: str
    ending: str
    problem_answer: str
    clue_answer: str
    solution_answer: str


CASE_REGISTRY = {
    "watering_can": MysteryCase(
        title="The Three Plinks",
        required_tag="can",
        object_name="the anise biscuit",
        opening=(
            "At {setting}, {detective} set an anise biscuit beside the tea. "
            "Before anyone could pour, the plate was empty, and a dry "
            "watering can rang, plink-plink-plink."
        ),
        trouble=(
            "The strange rhythm continued, although the garden breeze had "
            "stopped. No one had seen the biscuit leave the table."
        ),
        clue=(
            "A crooked dusting of anise crossed the sloping serving board "
            "and ended at the can. Beside it, {snail}'s silver trail led "
            "from the lettuce to a board propped on one short cork."
        ),
        first_exchange=(
            "“That shiny trail points to {snail},” said {helper}. "
            "“A trail is a clue, not a verdict,” {detective} replied. "
            "“Let's follow the anise dust.”"
        ),
        snail_exchange=(
            "“I nudged the board to reach the lettuce,” {snail} said. "
            "“I didn't mean to send lunch sailing.” “Will you help us "
            "check the can?” asked {detective}. “Gladly. I have excellent "
            "can manners,” said the snail."
        ),
        reveal=(
            "Inside the dry can lay the biscuit, still whole. The tilted "
            "board had sent it rolling, and {snail}'s shell had made the "
            "three plinks while the snail followed its anise scent."
        ),
        action=(
            "{detective} and {helper} tipped the can over a clean plate, "
            "then leveled the board with its missing cork. They gave "
            "{snail} a lettuce leaf for the trouble."
        ),
        ending=(
            "the biscuit sat safely on the level plate while {snail} "
            "tapped the empty can once, very politely, before tea"
        ),
        problem_answer=(
            "An anise biscuit disappeared from the tea table, and a dry "
            "watering can began making a three-plink rhythm."
        ),
        clue_answer=(
            "Anise dust led from a sloping board to the can, while "
            "{snail}'s silver trail showed that the snail had nudged the "
            "board while reaching for lettuce."
        ),
        solution_answer=(
            "The tilted board sent the biscuit rolling into the dry can. "
            "{snail}'s shell tapped the can as the snail followed the "
            "biscuit's scent, making the mysterious rhythm."
        ),
    ),
    "bamboo_cane": MysteryCase(
        title="The Marching Anise Tin",
        required_tag="bamboo",
        object_name="the anise seed tin",
        opening=(
            "In {setting}, the little tin of anise seeds had vanished from "
            "a shelf. A hollow bamboo cane under the bench answered with "
            "a soft tuk-tuk-pause-tuk."
        ),
        trouble=(
            "The rhythm sounded like a very small marching band, but no "
            "musician was anywhere in sight."
        ),
        clue=(
            "A round scrape interrupted the dust on the shelf, and "
            "{snail}'s silver trail crossed a stack of pots toward the "
            "open end of the bamboo cane. The strongest anise smell came "
            "from inside it."
        ),
        first_exchange=(
            "“The shelf is marching,” said {helper}. “Shelves don't have "
            "feet,” {detective} answered. “Let's see where the scrape "
            "and that rhythm lead.”"
        ),
        snail_exchange=(
            "“I climbed the pots to reach the cool lettuce,” {snail} said. "
            "“The tin rolled after me, and the cane seemed to applaud.” "
            "“Then let's look inside the cane,” said {detective}. "
            "“I do enjoy an audience,” the snail replied."
        ),
        reveal=(
            "The anise tin had rolled into the hollow cane when "
            "{snail} bumped the shelf. As the snail nudged the cane, the "
            "tin knocked against its hollow sides and made the marching "
            "rhythm."
        ),
        action=(
            "{detective} held a cloth beneath the cane while {helper} "
            "raised one end. The tin slid out safely, and they put it on "
            "a wide, steady shelf. {snail} received a cool lettuce leaf."
        ),
        ending=(
            "the anise tin rested safely on its broad shelf, and the "
            "bamboo cane stayed quiet while {snail} crunched lettuce"
        ),
        problem_answer=(
            "The anise seed tin disappeared from a shelf, while a hollow "
            "bamboo cane made a puzzling marching rhythm."
        ),
        clue_answer=(
            "A round scrape marked the dusty shelf, and {snail}'s trail "
            "led toward the cane, where the anise smell was strongest."
        ),
        solution_answer=(
            "{snail} bumped the shelf while climbing toward lettuce, "
            "sending the tin into the hollow cane. When the snail nudged "
            "the cane, the tin knocked inside it and made the rhythm."
        ),
    ),
    "overturned_pot": MysteryCase(
        title="The Pot That Kept Time",
        required_tag="rack",
        object_name="the anise seed heads",
        opening=(
            "At {setting}, the anise seed heads had disappeared from the "
            "drying rack. An overturned flowerpot answered with a "
            "rat-a-tap rhythm."
        ),
        trouble=(
            "The beat went on after the breeze stopped, as if the garden "
            "had hired a drummer and forgotten to tell anyone."
        ),
        clue=(
            "The drying mat had curled at one edge, and a few loose anise "
            "seeds lay beside {snail}'s silver trail. The trail ended at "
            "the flowerpot, which rocked just a little."
        ),
        first_exchange=(
            "“Perhaps the pot is trying to tell us something,” said "
            "{helper}. “Let's listen, then look,” replied {detective}. "
            "“The curled mat and those seeds are clues too.”"
        ),
        snail_exchange=(
            "“I crossed the mat looking for a cool, damp place,” {snail} "
            "said. “It curled, and the seed heads slid under the pot. "
            "Then I tapped the pot to see if it was awake.” “We found "
            "them,” said {detective}. “And the pot may sleep now.”"
        ),
        reveal=(
            "The curled mat had tipped the anise seed heads into the "
            "overturned pot when {snail} crossed it. The snail's shell "
            "tapped the rocking pot, keeping the rhythm going."
        ),
        action=(
            "{detective} and {helper} lifted the pot and gathered the "
            "seed heads back onto the rack. They pinned the mat flat and "
            "placed a broad leaf nearby so {snail} could find shade "
            "without crossing it."
        ),
        ending=(
            "the anise seed heads dried safely on the flat rack while "
            "{snail} rested beneath a leaf beside the now-quiet pot"
        ),
        problem_answer=(
            "Anise seed heads vanished from the drying rack, and an "
            "overturned flowerpot kept a strange rhythm."
        ),
        clue_answer=(
            "The curled drying mat, loose anise seeds, and {snail}'s trail "
            "all pointed to the rocking flowerpot."
        ),
        solution_answer=(
            "When {snail} crossed the curled mat, the anise seed heads "
            "slid under the pot. The snail's shell tapped the rocking pot "
            "and made the rhythm."
        ),
    ),
}


FEATURES = {"mystery", "humor"}
SEED_WORDS = {"rhythm", "snail", "anise"}
DETECTIVE_NAMES = ["Iris", "Nico", "Tavi", "Lena", "Oren"]
HELPER_NAMES = ["Bo", "Mira", "Jun", "Pip", "Suki"]
SNAIL_NAMES = ["Mallow", "Dot", "Noodle", "Button", "Slowpoke"]


def _valid_pairs() -> list[tuple[str, str]]:
    pairs = []
    for setting, setting_data in SETTING_REGISTRY.items():
        for case_id, case in CASE_REGISTRY.items():
            if case.required_tag in setting_data["tags"]:
                pairs.append((setting, case_id))
    return sorted(pairs)


def _validate_name(value: str, role: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 26 or not re.fullmatch(r"[A-Za-z][A-Za-z '-]*", cleaned):
        raise StoryError(
            f"The {role} name must be 1–26 simple letters, spaces, apostrophes, or hyphens."
        )
    return cleaned


def _validate_params(params: StoryParams) -> MysteryCase:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting!r}.")
    if params.case not in CASE_REGISTRY:
        raise StoryError(f"Unknown mystery case: {params.case!r}.")
    case = CASE_REGISTRY[params.case]
    if case.required_tag not in SETTING_REGISTRY[params.setting]["tags"]:
        raise StoryError(
            f"The {case.title} mystery needs a place with a {case.required_tag} feature; "
            f"{params.setting} does not have one."
        )

    names = [
        _validate_name(params.detective, "detective"),
        _validate_name(params.helper, "helper"),
        _validate_name(params.snail, "snail"),
    ]
    if len({name.casefold() for name in names}) != len(names):
        raise StoryError("The detective, helper, and snail must have different names.")
    return case


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join(
        (params.setting, params.case, params.detective, params.helper, params.snail)
    )
    return sum((index + 1) * ord(char) for index, char in enumerate(text))


def _template(text: str, params: StoryParams) -> str:
    return text.format(
        setting=params.setting,
        detective=params.detective,
        helper=params.helper,
        snail=params.snail,
    )


def _build_world(params: StoryParams, case: MysteryCase) -> World:
    setting_data = SETTING_REGISTRY[params.setting]
    world = World(setting=params.setting)
    world.add(
        Entity(
            name=params.setting,
            kind="place",
            meters={"light": 0.7, "shelter": 0.8},
            memes={"mood": 1.0},
        )
    )
    detective = world.add(
        Entity(
            name=params.detective,
            kind="child detective",
            meters={"attention": 0.8, "confidence": 0.5},
            memes={"curiosity": 1.0, "fairness": 1.0},
        )
    )
    helper = world.add(
        Entity(
            name=params.helper,
            kind="child helper",
            meters={"attention": 0.7},
            memes={"imagination": 1.0, "care": 1.0},
        )
    )
    snail = world.add(
        Entity(
            name=params.snail,
            kind="snail",
            meters={"speed": 0.05, "trail_shine": 0.8},
            memes={"patience": 1.0, "humor": 0.8},
        )
    )
    target = world.add(
        Entity(
            name=case.object_name,
            kind="anise food or plant",
            meters={"found": 0.0, "scent": 0.9},
            memes={"importance": 0.8},
        )
    )
    rhythm = world.add(
        Entity(
            name="the puzzling rhythm",
            kind="sound",
            meters={"beats_per_pattern": 3.0, "mystery_level": 1.0},
            memes={"clue": 1.0},
        )
    )
    anise = world.add(
        Entity(
            name="the anise scent",
            kind="herb scent",
            meters={"strength": 0.9},
            memes={"clue": 1.0},
        )
    )

    detective.memes["careful_reasoning"] = 1.0
    helper.memes["helpful_observation"] = 1.0
    snail.memes["willing_helper"] = 1.0
    target.meters["found"] = 1.0
    rhythm.meters["mystery_level"] = 0.0
    world.facts.update(
        case_title=case.title,
        case_id=params.case,
        setting_mood=setting_data["mood"],
        required_setting_feature=case.required_tag,
        solved=True,
        culprit=params.snail,
        solution=_template(case.reveal, params),
        method="followed the anise scent and checked the physical clues",
        helper=helper.name,
        detective=detective.name,
        target=target.name,
        rhythm="three-beat clue",
        anise="present",
    )
    return world


def _story_lines(params: StoryParams, case: MysteryCase, seed: int) -> list[str]:
    opening = _template(case.opening, params)
    trouble = _template(case.trouble, params)
    clue = _template(case.clue, params)
    first_exchange = _template(case.first_exchange, params)
    snail_exchange = _template(case.snail_exchange, params)
    reveal = _template(case.reveal, params)
    action = _template(case.action, params)
    ending = _template(case.ending, params)

    structures = [
        [
            f'{opening} The neighbors later called it “{case.title}.”',
            trouble,
            first_exchange,
            clue,
            snail_exchange,
            reveal,
            action,
            f"By tea time, {ending}.",
        ],
        [
            f'The first clue in “{case.title}” was a rhythm no one could explain. {opening}',
            clue,
            first_exchange,
            trouble,
            snail_exchange,
            f"That was when the clues fit together: {reveal}",
            action,
            f"At last, {ending}.",
        ],
        [
            f'{opening} “What could make a rhythm like that?” asked {params.helper}.',
            f"“We can find out by looking carefully,” said {params.detective}. {clue}",
            first_exchange,
            snail_exchange,
            f"The answer was simple once they tested the clues. {reveal}",
            action,
            f"The garden grew quiet again, and {ending}.",
        ],
    ]
    return structures[seed % len(structures)]


def generate(params: StoryParams) -> StorySample:
    case = _validate_params(params)
    seed = _stable_seed(params)
    world = _build_world(params, case)
    story = "\n\n".join(_story_lines(params, case, seed))

    prompts = [
        f"Write a gentle mystery about {params.detective}, {params.helper}, and a snail in {params.setting}.",
        "Let anise and a puzzling rhythm provide fair clues, with humor in the dialogue.",
        "Show the detectives solving the problem by noticing what the snail and the clues reveal.",
    ]
    story_qa = [
        QAItem(
            question=f"What went missing in “{case.title}”?",
            answer=_template(case.problem_answer, params),
        ),
        QAItem(
            question="Which clues helped the detectives investigate?",
            answer=_template(case.clue_answer, params),
        ),
        QAItem(
            question=f"What explained the mystery in “{case.title}”?",
            answer=_template(case.solution_answer, params),
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The story ends with { _template(case.ending, params) }.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling event that people investigate by noticing clues and testing explanations.",
        ),
        QAItem(
            question="What is anise?",
            answer="Anise is a fragrant plant whose seeds have a sweet, distinctive smell and taste.",
        ),
        QAItem(
            question="How does a snail move?",
            answer="A snail glides slowly on its soft, muscular foot and often leaves a shiny trail of mucus.",
        ),
        QAItem(
            question="What is rhythm?",
            answer="Rhythm is a pattern of sounds or movements that repeats in time.",
        ),
        QAItem(
            question="How can humor help a mystery story?",
            answer="A funny remark can make a tense puzzle feel friendly while the characters keep looking for the truth.",
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
can_tell_story(S,C) :-
    setting(S),
    mystery_case(C),
    needs(C,F),
    has_tag(S,F),
    feature(mystery),
    feature(humor),
    seed_word(rhythm),
    seed_word(snail),
    seed_word(anise).
#show can_tell_story/2.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting, data in SETTING_REGISTRY.items():
        setting_id = data["id"]
        lines.append(asp.fact("setting", setting_id))
        for tag in sorted(data["tags"]):
            lines.append(asp.fact("has_tag", setting_id, tag))
    for case_id, case in CASE_REGISTRY.items():
        lines.append(asp.fact("mystery_case", case_id))
        lines.append(asp.fact("needs", case_id, case.required_tag))
    for feature in sorted(FEATURES):
        lines.append(asp.fact("feature", feature))
    for word in sorted(SEED_WORDS):
        lines.append(asp.fact("seed_word", word))
    return "\n".join(lines)


def asp_program(show: str = "#show can_tell_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A humorous little mystery about rhythm, a snail, and anise."
    )
    ap.add_argument("--setting", choices=list(SETTING_REGISTRY))
    ap.add_argument("--case", choices=list(CASE_REGISTRY))
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--snail")
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
    if args.case:
        case_id = args.case
        compatible_settings = [
            setting
            for setting, candidate in _valid_pairs()
            if candidate == case_id
        ]
        setting = args.setting or rng.choice(compatible_settings)
    else:
        setting = args.setting or rng.choice(list(SETTING_REGISTRY))
        compatible_cases = [
            candidate for place, candidate in _valid_pairs() if place == setting
        ]
        case_id = rng.choice(compatible_cases)

    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    if args.helper:
        helper = args.helper
    else:
        helper = rng.choice([name for name in HELPER_NAMES if name.casefold() != detective.casefold()])
    if args.snail:
        snail = args.snail
    else:
        taken = {detective.casefold(), helper.casefold()}
        snail = rng.choice([name for name in SNAIL_NAMES if name.casefold() not in taken])

    params = StoryParams(
        setting=setting,
        case=case_id,
        detective=detective,
        helper=helper,
        snail=snail,
    )
    _validate_params(params)
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
        for ent in sample.world.entities.values():
            print(
                f"{ent.name}: kind={ent.kind}, meters={dict(ent.meters)}, "
                f"memes={dict(ent.memes)}"
            )
        print(f"world facts: {sample.world.facts}")
    if qa:
        print()
        print("== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    try:
        python_pairs = {
            (SETTING_REGISTRY[setting]["id"], case_id)
            for setting, case_id in _valid_pairs()
        }
        clingo_pairs = set(_asp_valid())
    except Exception as exc:
        print(f"ASP verification could not run: {exc}")
        return 2

    if python_pairs != clingo_pairs:
        print("Mismatch between the Python reasonableness gate and ASP:")
        print("Python only:", sorted(python_pairs - clingo_pairs))
        print("ASP only:", sorted(clingo_pairs - python_pairs))
        return 1

    checked = 0
    for index, (setting, case_id) in enumerate(_valid_pairs()):
        params = StoryParams(
            setting=setting,
            case=case_id,
            detective="Iris",
            helper="Bo",
            snail="Mallow",
            seed=100 + index,
        )
        try:
            sample = generate(params)
        except StoryError as exc:
            print(f"Generated-story check failed for {setting}, {case_id}: {exc}")
            return 1
        story = sample.story.casefold()
        if not all(word in story for word in ("rhythm", "snail", "anise")):
            print(f"Generated story omitted a seed word for {setting}, {case_id}.")
            return 1
        if "“" not in sample.story or "”" not in sample.story:
            print(f"Generated story omitted spoken dialogue for {setting}, {case_id}.")
            return 1
        if not sample.world or not sample.world.facts.get("solved"):
            print(f"Generated world did not resolve for {setting}, {case_id}.")
            return 1
        if not sample.story_qa or not all(item.answer.strip() for item in sample.story_qa):
            print(f"Generated story QA was incomplete for {setting}, {case_id}.")
            return 1
        checked += 1

    print(
        f"OK: ASP matches the Python gate ({len(python_pairs)} valid setting/case pairs); "
        f"{checked} generated stories passed."
    )
    return 0


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()

    if args.n < 1:
        ap.error("-n must be at least 1")

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            for setting_id, case_id in _asp_valid():
                print(f"{setting_id}: {case_id}")
        except Exception as exc:
            print(f"ASP query could not run: {exc}", file=sys.stderr)
            raise SystemExit(2)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, (setting, case_id) in enumerate(_valid_pairs()):
            params = StoryParams(
                setting=setting,
                case=case_id,
                detective="Iris",
                helper="Bo",
                snail="Mallow",
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(exc, file=sys.stderr)
                raise SystemExit(2)
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
