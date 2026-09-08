#!/usr/bin/env python3
"""
Standalone story world: the missing silver bell.

A child detective investigates a tiny whodunit at the village garden. A silver
bell meant for the Happy Ending parade disappears, and a Misunderstanding
makes one helper seem guilty. Through careful Dialogue, the child must choose
what really happened and repair the parade.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
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
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    detective_name: str
    detective_gender: str
    helper_name: str
    suspect: str
    setting: str
    object_name: str
    scenario: str
    opening_variant: int = 0
    dialogue_variant: int = 0
    ending_variant: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "garden": "the village garden",
    "library": "the little library courtyard",
    "square": "the sunny town square",
}

SUSPECTS = {
    "gardener": {
        "name": "Mrs. Green",
        "role": "gardener",
        "detail": "green soil on her gloves",
        "truth": "She moved the bell to the potting shed so it would not get wet.",
    },
    "baker": {
        "name": "Baker Ben",
        "role": "baker",
        "detail": "flour on his sleeves",
        "truth": "He carried the bell to the picnic table while bringing the parade buns.",
    },
    "librarian": {
        "name": "Librarian Lila",
        "role": "librarian",
        "detail": "a blue book under her arm",
        "truth": "She placed the bell beside the reading blanket so the children could hear it.",
    },
}

OBJECTS = {
    "silver_bell": "the small silver bell",
    "blue_ribbon": "the blue parade ribbon",
    "brass_key": "the shiny brass key",
}

SCENARIOS = {
    "garden_bell": {
        "clue": "a trail of damp leaves curved from the flower bed toward the potting shed",
        "hidden_place": "the potting shed",
        "witness": "a sleepy tortoise",
        "ending": "the bell rang over the flowers as everyone marched beneath a rainbow of ribbons",
    },
    "courtyard_bell": {
        "clue": "three floury footprints crossed the stones beside the picnic table",
        "hidden_place": "the picnic table",
        "witness": "a sparrow on the fountain",
        "ending": "the bell chimed while warm buns were passed around the courtyard",
    },
    "square_bell": {
        "clue": "a blue thread caught on the latch of the reading blanket",
        "hidden_place": "the reading blanket",
        "witness": "a small cat beneath the bench",
        "ending": "the bell led a cheerful circle around the square",
    },
}

OPENINGS = [
    "The morning of the Happy Ending parade began quietly in {place}.",
    "At noon, {detective} arrived in {place} just as the parade flags fluttered.",
    "A bright poster promised a Happy Ending party, but {detective} noticed one empty hook in {place}.",
]

DIALOGUES = [
    '"I did not take it," said {suspect}. "I only moved something heavy." '
    '"Then tell me where you went," said {detective}. The answer pointed toward {hidden_place}.',
    '{detective} asked, "What were you carrying?" '
    '{suspect} replied, "A basket, not the bell. I thought someone else had it." '
    'That Misunderstanding gave {detective} a new clue.',
    '"Please tell the whole story," {detective} said. '
    '"I was afraid you would blame me," admitted {suspect}. '
    'When the two spoke calmly, the missing piece became clear.',
]

ENDINGS = [
    "The Misunderstanding melted away, and {detective} chose kindness as well as the truth. {ending}.",
    "Everyone apologized for guessing too soon. {detective} rang the bell, and {ending}.",
    "The real thief was no thief at all: the wind had knocked the bell from its hook, and a helpful person had moved it. {ending}.",
]

GIRL_NAMES = ["Luna", "Mia", "Nora", "Ivy"]
BOY_NAMES = ["Leo", "Eli", "Noah", "Milo"]


def valid_combo(setting: str, suspect: str, scenario: str) -> bool:
    if setting not in SETTINGS:
        return False
    if suspect not in SUSPECTS:
        return False
    if scenario not in SCENARIOS:
        return False
    return True


def explain_rejection(setting: str, suspect: str, scenario: str) -> str:
    return (
        f"No story: setting={setting}, suspect={suspect}, scenario={scenario} "
        "does not form a playable missing-object mystery."
    )


def tell(params: StoryParams) -> World:
    if not valid_combo(params.setting, params.suspect, params.scenario):
        raise StoryError(explain_rejection(params.setting, params.suspect, params.scenario))

    place = SETTINGS[params.setting]
    suspect = SUSPECTS[params.suspect]
    plan = SCENARIOS[params.scenario]
    world = World(place)

    detective = world.add(Entity(
        "detective",
        "character",
        params.detective_name,
        meters={"curiosity": 1.0},
        memes={"care": 1.0},
    ))
    helper = world.add(Entity(
        "helper",
        "character",
        params.helper_name,
        meters={"patience": 1.0},
        memes={"trust": 1.0},
    ))
    accused = world.add(Entity(
        "suspect",
        "character",
        suspect["name"],
        meters={"worry": 1.0},
        memes={"embarrassment": 1.0},
    ))
    bell = world.add(Entity(
        "bell",
        "thing",
        OBJECTS[params.object_name],
        meters={"visibility": 0.0},
        memes={"importance": 1.0},
    ))

    opening = OPENINGS[params.opening_variant % len(OPENINGS)].format(
        place=place, detective=detective.label
    )
    world.say(opening)
    world.say(
        f"The parade's {bell.label} was missing from its hook. "
        f"Without it, the children could not begin the final song."
    )
    world.say(
        f"{detective.label} became the young detective. "
        f"{helper.label} handed over a notebook and said, "
        f'"A good mystery needs careful eyes, not quick guesses."'
    )

    world.para()
    world.say(
        f"{accused.label} stood nearby with {suspect['detail']}. "
        f"That looked suspicious, but {detective.label} remembered that a clue is not proof."
    )
    world.say(
        f"{detective.label} followed {plan['clue']} and noticed the path ended near "
        f"{plan['hidden_place']}."
    )
    world.facts["clue"] = plan["clue"]
    world.facts["hidden_place"] = plan["hidden_place"]
    world.facts["witness"] = plan["witness"]
    world.fired.add("clue_found")

    world.para()
    dialogue = DIALOGUES[params.dialogue_variant % len(DIALOGUES)].format(
        detective=detective.label,
        suspect=accused.label,
        hidden_place=plan["hidden_place"],
    )
    world.say(dialogue)
    world.say(
        f"The conversation revealed the Misunderstanding: {suspect['truth']} "
        f"The bell had been moved to keep it safe, not stolen."
    )
    world.facts["misunderstanding"] = True
    world.facts["truth"] = suspect["truth"]
    world.fired.add("dialogue_truth")

    world.para()
    world.say(
        f"{detective.label} had to choose what to do. "
        f"Instead of shouting an accusation, {detective.label} invited everyone to search together."
    )
    world.say(
        f"Behind the nearest crate, the children found {bell.label}. "
        f"It was dusty, but its little clapper still worked."
    )
    bell.meters["visibility"] = 1.0
    bell.memes["relief"] = 1.0
    accused.memes["relief"] = 1.0
    detective.memes["wisdom"] = 1.0
    helper.memes["trust"] = 2.0
    world.fired.add("bell_found")

    world.para()
    ending = ENDINGS[params.ending_variant % len(ENDINGS)].format(
        detective=detective.label,
        ending=plan["ending"],
    )
    world.say(ending)
    world.say(
        f"{helper.label} smiled and said, "
        f'"You solved it because you listened." '
        f"{detective.label} knew that a happy ending could include the truth and a kind repair."
    )
    world.fired.add("happy_ending")

    world.facts.update(
        detective=detective,
        helper=helper,
        suspect=accused,
        bell=bell,
        setting=place,
        resolved=True,
        choice="listen and search together",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly Whodunit with a missing silver bell, a Misunderstanding, careful Dialogue, and a Happy Ending.",
        f"Tell how {f['detective'].label} follows the clue '{f['clue']}' instead of blaming {f['suspect'].label}.",
        f"Show the choice that lets {f['detective'].label} discover the truth: {f['truth']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Why did {f['detective'].label} begin an investigation?",
            answer=f"{f['detective'].label} investigated because {f['bell'].label} was missing and the Happy Ending parade could not begin without it.",
        ),
        QAItem(
            question=f"What made {f['suspect'].label} seem suspicious?",
            answer=f"{f['suspect'].label} seemed suspicious because {SUSPECTS[next(k for k, v in SUSPECTS.items() if v['name'] == f['suspect'].label)]['detail']} was visible, but that was only a misleading clue.",
        ),
        QAItem(
            question="What did the Dialogue reveal?",
            answer=f"The Dialogue revealed the Misunderstanding: {f['truth']}",
        ),
        QAItem(
            question=f"What did {f['detective'].label} choose to do?",
            answer=f"{f['detective'].label} chose to listen carefully and search with everyone instead of shouting an accusation.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The bell was found, everyone repaired the Misunderstanding, and {f['detective'].label} helped the parade have a Happy Ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story in which someone investigates what happened and who caused it.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is a mistake in what someone thinks another person said, meant, or did.",
        ),
        QAItem(
            question="Why is dialogue useful in a mystery?",
            answer="Dialogue lets characters share information, correct mistakes, and change what the detective decides.",
        ),
        QAItem(
            question="What makes an ending happy?",
            answer="An ending is happy when the problem is solved and people feel safer, wiser, or kinder afterward.",
        ),
        QAItem(
            question="Why should a detective check clues before choosing?",
            answer="A detective should check clues because one detail can look suspicious while having an innocent explanation.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
setting(garden).
setting(library).
setting(square).
suspect(gardener).
suspect(baker).
suspect(librarian).
object(silver_bell).
missing(silver_bell).
clue_found(silver_bell).
dialogue_used.
misunderstanding.
truth_revealed.
chosen(listen_and_search).
bell_found.
happy_ending.
good_story(S, X) :- setting(S), suspect(X), missing(silver_bell),
    clue_found(silver_bell), dialogue_used, misunderstanding,
    truth_revealed, chosen(listen_and_search), bell_found, happy_ending.
"""


def asp_facts() -> str:
    import asp

    return "\n".join([
        *(asp.fact("setting", key) for key in SETTINGS),
        *(asp.fact("suspect", key) for key in SUSPECTS),
        asp.fact("object", "silver_bell"),
        asp.fact("missing", "silver_bell"),
        asp.fact("clue_found", "silver_bell"),
        asp.fact("dialogue_used"),
        asp.fact("misunderstanding"),
        asp.fact("truth_revealed"),
        asp.fact("chosen", "listen_and_search"),
        asp.fact("bell_found"),
        asp.fact("happy_ending"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = sorted((setting, suspect) for setting in SETTINGS for suspect in SUSPECTS)
    cl = asp_valid_combos()
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python:", py)
    print("clingo:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Whodunit about a missing bell, a Misunderstanding, and a Happy Ending."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--suspect", choices=SUSPECTS)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--scenario", choices=SCENARIOS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    suspect_key = args.suspect or rng.choice(list(SUSPECTS))
    object_name = args.object_name or "silver_bell"
    scenario = args.scenario or {
        "garden": "garden_bell",
        "library": "courtyard_bell",
        "square": "square_bell",
    }[setting]
    gender = args.gender or rng.choice(["girl", "boy"])
    detective_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(["Aunt May", "Grandpa Sol", "Nurse Jo"])
    return StoryParams(
        detective_name=detective_name,
        detective_gender=gender,
        helper_name=helper_name,
        suspect=suspect_key,
        setting=setting,
        object_name=object_name,
        scenario=scenario,
        opening_variant=rng.randrange(len(OPENINGS)),
        dialogue_variant=rng.randrange(len(DIALOGUES)),
        ending_variant=rng.randrange(len(ENDINGS)),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("Luna", "girl", "Aunt May", "gardener", "garden", "silver_bell", "garden_bell"),
        StoryParams("Leo", "boy", "Grandpa Sol", "baker", "library", "silver_bell", "courtyard_bell"),
        StoryParams("Mia", "girl", "Nurse Jo", "librarian", "square", "silver_bell", "square_bell"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
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
            header = f"### {sample.params.detective_name}: {sample.params.setting} mystery"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
