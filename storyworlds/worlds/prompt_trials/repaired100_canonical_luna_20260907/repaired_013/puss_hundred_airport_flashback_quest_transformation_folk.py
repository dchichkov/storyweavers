#!/usr/bin/env python3
"""
A folk tale at an airport about Puss, a hundred lost feathers, and a quest
that transforms a hurried traveler into a patient helper.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the airport"
    hero: str = "Puss"
    companion: str = "Nell"
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
    "the airport": {
        "tags": {"airport", "travel", "folk_tale"},
        "mood": "bright, noisy, and full of waiting feet",
    }
}


@dataclass(frozen=True)
class QuestArc:
    title: str
    premise: str
    trouble: str
    flashback: str
    choice: str
    action: str
    transformation: str
    ending: str
    trouble_answer: str
    flashback_answer: str
    transformation_answer: str


ARCS = [
    QuestArc(
        title="Puss and the Hundred Feathers",
        premise="At the busiest airport in the kingdom, Puss kept a little red suitcase and promised never to miss a flight.",
        trouble="Just before the last evening plane, a storm blew a hundred silver feathers from a sky messenger's traveling cloak and scattered them through the airport.",
        flashback="Puss remembered how his grandmother once said, \"A journey is measured by the people you help, not by the miles you cross.\"",
        choice="Puss wanted to board at once, but Nell pointed to the lonely messenger and said, \"A hundred small troubles still make one large sorrow.\"",
        action="So Puss and Nell began a quest through the baggage hall, the quiet gate, and the echoing food court, counting every feather and returning each one.",
        transformation="By the time the final feather was found beneath a luggage cart, Puss was no longer the cat who feared being late; he had become a patient guide who noticed everyone in need.",
        ending="The sky messenger lifted the hundred feathers, and they rose like a shining staircase above the airport while Puss's plane waited kindly at the gate.",
        trouble_answer="A storm scattered a hundred silver feathers from a sky messenger's cloak throughout the airport before the last evening flight.",
        flashback_answer="Puss remembered his grandmother's lesson that a journey is measured by the people someone helps, not by distance.",
        transformation_answer="Helping with the quest changed Puss from a traveler afraid of being late into a patient guide who noticed and helped others.",
    ),
    QuestArc(
        title="The Gate of One Hundred Whispers",
        premise="Puss arrived at the airport carrying a bell that could open any gate, but the bell had forgotten its song.",
        trouble="A hundred travelers whispered different directions, and the frightened bell grew quieter after each voice.",
        flashback="Puss recalled a tale from long ago in which his mother found the right road by listening to one small bird.",
        choice="Instead of shouting over the crowd, Puss asked Nell to help him hear the softest voice.",
        action="They followed the whisper of a child searching for her father, then helped one traveler at a time until the airport grew calm.",
        transformation="The bell learned a new song from their kindness, and Puss changed from a noisy leader into a careful listener.",
        ending="When the gate opened, a hundred travelers stepped through in peace, and the bell chimed once for every helping hand.",
        trouble_answer="A magical bell lost its song while a hundred travelers gave it too many different directions.",
        flashback_answer="Puss remembered that his mother found the right road by listening carefully to one small bird.",
        transformation_answer="Puss became a careful listener instead of a noisy leader, and the bell regained its song through kindness.",
        ),
    QuestArc(
        title="The Red Suitcase's Hundred Roads",
        premise="Puss owned a red suitcase that showed a new road whenever someone at the airport felt lost.",
        trouble="One morning it displayed a hundred roads at once, and the signs tangled above the travelers' heads.",
        flashback="Puss remembered a village elder saying, \"A road becomes clear when a friend takes the first step beside you.\"",
        choice="Puss could have chosen the shortest road for himself, but Nell asked him to begin with the smallest traveler.",
        action="They led children, grandparents, and tired pilots along the roads in gentle groups until every sign pointed home.",
        transformation="Puss's hurried paws slowed into brave, steady steps, and the suitcase became a map for sharing rather than escaping.",
        ending="The hundred roads folded into one bright path leading to a warm waiting room where strangers sat together.",
        trouble_answer="Puss's suitcase showed a hundred tangled roads, confusing everyone in the airport.",
        flashback_answer="Puss remembered that a road becomes clear when a friend takes the first step beside someone.",
        transformation_answer="Puss changed from a hurried traveler into a steady guide, and his suitcase became a tool for sharing.",
        ),
]


OPENINGS = [
    "In the old days, when airports had no magic maps, Puss lived beneath the great clock of {setting}.",
    "Listen well to the folk tale of Puss, who traveled through {setting} with a red suitcase and a brave little heart.",
    "Long ago, Puss came to {setting} just as the evening lights began to glow.",
]


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.companion))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:]


def build_story(world: World) -> str:
    f = world.facts
    arc: QuestArc = f["arc"]
    opening = fill(OPENINGS[f["opening_variant"]], f)
    premise = fill(arc.premise, f)
    trouble = fill(arc.trouble, f)
    flashback = fill(arc.flashback, f)
    choice = fill(arc.choice, f)
    action = fill(arc.action, f)
    transformation = fill(arc.transformation, f)
    ending = fill(arc.ending, f)
    hero = f["hero"]
    companion = f["companion"]

    structures = [
        [
            f"{opening} This is the tale called \"{arc.title}.\"",
            f"{premise} {trouble}",
            f"{flashback} \"What shall we do?\" {companion} asked. {choice}",
            action,
            f"{transformation} \"I thought being first was everything,\" {hero} said.",
            f"At last, {ending}",
        ],
        [
            opening,
            f"\"Why is everyone hurrying?\" {companion} asked. {premise}",
            sentence_start(trouble),
            f"{hero} looked toward the departure board. {flashback}",
            f"\"Then we will help before we fly,\" said {hero}. {choice}",
            f"{action} {transformation}",
            f"After that, {ending}",
        ],
        [
            f"The elders still tell \"{arc.title}\" whenever a traveler grows impatient. {opening}",
            f"First came the trouble: {trouble}",
            f"{companion} asked, \"Will the quest take too long?\" {hero} answered, \"A good journey has time for a friend.\" {flashback}",
            choice,
            action,
            transformation,
            f"That night, {ending}",
        ],
        [
            f"{opening} Neither traveler knew that the airport was waiting to teach them a lesson.",
            premise,
            sentence_start(trouble),
            f"\"We can leave this for someone else,\" said {hero}. \"But should we?\" asked {companion}. {flashback}",
            f"{choice} {action}",
            f"The quest changed more than the airport: {transformation}",
            f"Then {ending}",
        ],
    ]
    return "\n\n".join(structures[f["structure_variant"]])


ASP_RULES = r"""
setting(airport).
feature(flashback).
feature(quest).
feature(transformation).
can_tell_story(airport) :-
    setting(airport),
    feature(flashback),
    feature(quest),
    feature(transformation).
hundred_feathers(airport).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "airport"),
            asp.fact("feature", "flashback"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "transformation"),
            asp.fact("hundred_feathers", "airport"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk tale about Puss, a hundred feathers, and an airport quest."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--companion")
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
    setting = args.setting or "the airport"
    hero = args.hero or "Puss"
    companion = args.companion or rng.choice(["Nell", "Toma", "Bibi", "Mara"])
    if not hero.strip():
        raise StoryError("The hero must have a name.")
    if not companion.strip():
        raise StoryError("The companion must have a name.")
    if hero.casefold() == companion.casefold():
        raise StoryError("Puss and the companion must be different characters.")
    return StoryParams(setting=setting, hero=hero, companion=companion)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero.casefold() == params.companion.casefold():
        raise StoryError("The hero and companion must be different characters.")

    seed = stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(
        Entity(
            name=params.hero,
            kind="cat",
            meters={"speed": 0.8, "attention": 0.4},
            memes={"impatience": 0.8, "kindness": 0.5},
        )
    )
    companion = world.add(
        Entity(
            name=params.companion,
            kind="traveler",
            meters={"patience": 0.8},
            memes={"empathy": 1.0, "courage": 0.7},
        )
    )
    world.add(
        Entity(
            name="the sky messenger",
            kind="messenger",
            meters={"feathers": 100.0},
            memes={"trust": 0.8},
        )
    )
    world.add(
        Entity(
            name="the red suitcase",
            kind="suitcase",
            meters={"weight": 1.0},
            memes={"memory": 0.8},
        )
    )
    world.add(
        Entity(
            name="the airport",
            kind="place",
            meters={"crowd": 0.9, "noise": 0.8},
            memes={"welcome": 0.7},
        )
    )

    hero.memes["patience"] = 0.2
    world.facts.update(
        hero=params.hero,
        companion=params.companion,
        setting=params.setting,
        arc=arc,
        opening_variant=(seed // len(ARCS)) % len(OPENINGS),
        structure_variant=(seed // (len(ARCS) * len(OPENINGS))) % 4,
        hundred=100,
        theme="flashback, quest, transformation, and kindness",
        final_change=arc.transformation,
    )

    story = build_story(world)
    prompts = [
        f"Tell a folk tale about {params.hero} and {params.companion} at an airport.",
        "Write a child-facing story with a flashback, a quest, and a transformation.",
        "Tell how a hundred lost things can lead one hurried traveler to become kind.",
    ]
    story_qa = [
        QAItem(
            question=f"What trouble did {params.hero} and {params.companion} face at the airport?",
            answer=arc.trouble_answer,
        ),
        QAItem(
            question=f"What flashback helped {params.hero} decide what to do?",
            answer=arc.flashback_answer,
        ),
        QAItem(
            question=f"How did the quest transform {params.hero}?",
            answer=arc.transformation_answer,
        ),
        QAItem(
            question=f"How does the folk tale of {arc.title} end?",
            answer=f"It ends with {fill(arc.ending, world.facts)}",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a moment in a story that shows something remembered from earlier."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a purpose, such as finding something or helping someone."
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a meaningful change in a person, creature, or thing."
        ),
        QAItem(
            question="What happens at an airport?",
            answer="People check in, wait at gates, carry luggage, and travel on airplanes."
        ),
        QAItem(
            question="Why can counting help during a search?",
            answer="Counting helps people track what they have found and notice what is still missing."
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
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _python_gate() -> set[tuple[str]]:
    if (
        "the airport" in SETTING_REGISTRY
        and {"Flashback", "Quest", "Transformation"}
        == {"Flashback", "Quest", "Transformation"}
    ):
        return {("airport",)}
    return set()


def _asp_gate() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return set(asp.atoms(model, "can_tell_story"))


def asp_verify() -> int:
    try:
        python_values = _python_gate()
        asp_values = _asp_gate()
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if python_values == asp_values:
        print("OK: clingo gate matches python (airport story domain).")
        sample = generate(
            StoryParams(setting="the airport", hero="Puss", companion="Nell", seed=13)
        )
        if not sample.story.strip() or "Puss" not in sample.story:
            print("Generated-story verification failed.")
            return 1
        print("OK: generated story exercised.")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(python_values - asp_values))
    print("clingo only:", sorted(asp_values - python_values))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            for item in sorted(_asp_gate()):
                print(item[0])
        except Exception as exc:
            raise SystemExit(f"ASP mode unavailable: {exc}")
        return

    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, companion in enumerate(["Nell", "Toma", "Bibi", "Mara"]):
            params = StoryParams(
                setting="the airport",
                hero="Puss",
                companion=companion,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as exc:
                raise SystemExit(str(exc))
            if sample.story in seen:
                params.seed = seed + 100003
                sample = generate(params)
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
