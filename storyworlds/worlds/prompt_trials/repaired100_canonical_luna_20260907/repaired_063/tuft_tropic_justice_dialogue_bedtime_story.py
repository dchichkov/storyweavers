#!/usr/bin/env python3
"""
A standalone bedtime storyworld about a tuft, a tropic garden, and gentle justice.

Luna discovers that a bright tuft has been taken from the garden's sleeping nest.
With help from a careful friend, she learns that justice means listening to every
side and repairing harm with kindness.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the Moonlit Tropic Garden"


@dataclass
class StoryParams:
    name: str
    friend_name: str
    elder_name: str
    case_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTING = Setting()

NAMES = ["Luna", "Milo", "Nia", "Tavi", "Suri", "Eli"]
FRIENDS = ["Pip", "Mara", "Sol", "Bibi", "Cato"]
ELDERS = ["Auntie Noor", "Grandma Tala", "Uncle Ivo", "Gran Miri"]

CASES = [
    {
        "tuft": "a soft silver tuft from the moon-palm",
        "missing": "the tuft had vanished from the nest beside the warm pond",
        "clue": "small damp footprints led from the nest to a reed shelter",
        "truth": "a young river bird had borrowed the tuft to line a chilly nest",
        "repair": "the children returned the tuft only after the bird had a safer bundle of fallen grass",
        "image": "The bird slept under a moon-palm leaf while the new grass nest held one silver strand like a tiny star.",
    },
    {
        "tuft": "a bright orange tuft from the sunset parrot's feather pillow",
        "missing": "the tuft was gone just before the garden's bedtime bell",
        "clue": "orange fibers rested beside a crooked bridge and a basket of dry leaves",
        "truth": "a gust had carried the tuft away, and a shy crab had tucked it into its hiding place",
        "repair": "the children moved the basket from the windy bridge and gave the crab a safe leaf shelter",
        "image": "The parrot pillow was whole again, and the crab's leaf shelter glowed quietly beneath the bridge.",
    },
    {
        "tuft": "a blue tuft of kapok from the story tent",
        "missing": "someone had pulled the tuft from the tent's soft roof",
        "clue": "blue threads crossed the path toward the watering jars",
        "truth": "a thirsty lizard had used the tuft to shade its eggs from the hot tropic sun",
        "repair": "the children built a leaf shade for the eggs and stitched the tuft back into the tent",
        "image": "The tent roof was smooth again, while three tiny lizards rested beneath a broad green leaf.",
    },
    {
        "tuft": "a golden tuft from the garden's welcome cushion",
        "missing": "the cushion looked ragged when the sleepy visitors arrived",
        "clue": "golden fibers clung to a thorn bush beside a narrow path",
        "truth": "a night moth had caught the tuft while escaping a startled gecko",
        "repair": "the children freed the moth, removed the thorn safely with an adult, and mended the cushion",
        "image": "The moth fluttered over the flowers, and the golden cushion welcomed everyone by the lantern.",
    },
]

OPENINGS = [
    "When the first stars appeared above the tropic trees,",
    "At the quiet edge of bedtime,",
    "After the warm tropic rain had stopped,",
    "As the garden lanterns began to glow,",
]

DIALOGUES = [
    (
        '"Someone took the tuft," said {hero}. "We should ask before we accuse." '
        '"I saw footprints by the pond," said {friend}. "Let us follow them gently."'
    ),
    (
        '"It is not justice to blame the nearest creature," said {hero}. '
        '"Then we must listen to whoever left the clues," replied {friend}.'
    ),
    (
        '"Could the tuft have moved by itself?" asked {friend}. '
        '"The wind may explain it," said {hero}, "but we will check every side."'
    ),
    (
        '"I feel cross," whispered {hero}. "You can feel cross and still be fair," said {friend}.'
    ),
]

ENDINGS = [
    "Luna tucked the lesson into her bedtime thoughts: justice begins with listening.",
    "The friends promised that a fair answer should leave every small neighbor safer than before.",
    "The garden grew quiet, and the children understood that kindness could be careful as well as warm.",
    "Under the patient stars, the repaired place felt peaceful because the truth had made room for everyone.",
]

JUSTICE_EXPLANATION = (
    "Justice means treating people fairly, listening to the facts, and helping repair harm."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bedtime storyworld about a tuft, a tropic garden, and justice."
    )
    parser.add_argument("--name")
    parser.add_argument("--friend-name")
    parser.add_argument("--elder-name")
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice(FRIENDS),
        elder_name=args.elder_name or rng.choice(ELDERS),
        case_id=rng.randrange(len(CASES)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        ending_id=rng.randrange(len(ENDINGS)),
    )


def _build_world(params: StoryParams) -> World:
    case = CASES[params.case_id % len(CASES)]
    world = World(SETTING)
    hero = world.add(Entity("hero", "child", params.name))
    friend = world.add(Entity("friend", "child", params.friend_name))
    elder = world.add(Entity("elder", "elder", params.elder_name))
    tuft = world.add(Entity("tuft", "tuft", case["tuft"]))
    garden = world.add(Entity("garden", "setting", SETTING.place))
    clue = world.add(Entity("clue", "evidence", case["clue"]))

    hero.memes["curiosity"] = 1
    friend.memes["fairness"] = 1
    elder.memes["wisdom"] = 1
    tuft.meters["found"] = 0
    tuft.meters["returned"] = 0
    clue.meters["observed"] = 1

    world.facts.update(
        hero=hero,
        friend=friend,
        elder=elder,
        tuft=tuft,
        garden=garden,
        clue=clue,
        case=case,
        params=params,
        truth_known=False,
        harm_repaired=False,
    )
    return world


def tell(world: World) -> None:
    facts = world.facts
    hero: Entity = facts["hero"]  # type: ignore[assignment]
    friend: Entity = facts["friend"]  # type: ignore[assignment]
    elder: Entity = facts["elder"]  # type: ignore[assignment]
    tuft: Entity = facts["tuft"]  # type: ignore[assignment]
    case: dict[str, str] = facts["case"]  # type: ignore[assignment]
    params: StoryParams = facts["params"]  # type: ignore[assignment]

    opening = OPENINGS[params.opening_id % len(OPENINGS)]
    dialogue = DIALOGUES[params.dialogue_id % len(DIALOGUES)].format(
        hero=hero.label, friend=friend.label
    )
    ending = ENDINGS[params.ending_id % len(ENDINGS)]

    world.say(
        f"{opening} {hero.label} walked through {SETTING.place} with "
        f"{friend.label}, carrying a little lantern."
    )
    world.say(f"Near the warm pond, they noticed that {case['missing']}.")
    world.say(f"The missing piece was {tuft.label}.")
    world.say(dialogue)

    world.para()
    world.say(
        f"{elder.label} joined them and said, "
        f'"{JUSTICE_EXPLANATION} Let us learn what happened before we choose a blame."'
    )
    world.say(f"Together they looked from the safe path and found that {case['clue']}.")
    world.say(
        f"{hero.label} said, \"That clue tells us where the tuft went, "
        "but not why.\""
    )
    world.say(
        f"{friend.label} answered, \"Then we should listen for the reason, too.\""
    )
    world.say(f"The careful search revealed that {case['truth']}.")

    world.para()
    world.say(
        f"The children did not scold the small creature. Instead, {case['repair']}."
    )
    world.say(
        f"{elder.label} nodded. \"That is justice,\" the elder said. "
        "\"We found the truth, protected our neighbor, and repaired what was missing.\""
    )
    world.say(f"{hero.label} placed the tuft back gently, and the garden grew quiet.")
    world.say(ending)
    world.say(case["image"])

    tuft.meters["found"] = 1
    tuft.meters["returned"] = 1
    facts["truth_known"] = True
    facts["harm_repaired"] = True
    hero.memes["patience"] = 1
    friend.memes["care"] = 1


def generation_prompts(world: World) -> list[str]:
    case: dict[str, str] = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        "Write a gentle bedtime story containing the words tuft, tropic, and justice.",
        f"Tell how {hero.label} investigates {case['tuft']} without making a quick accusation.",
        "Create a child-facing story with dialogue, fair listening, a repaired harm, and a peaceful ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero: Entity = facts["hero"]  # type: ignore[assignment]
    friend: Entity = facts["friend"]  # type: ignore[assignment]
    case: dict[str, str] = facts["case"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What tuft did {hero.label} find missing?",
            answer=f"The missing item was {case['tuft']}.",
        ),
        QAItem(
            question=f"What clue did {hero.label} and {friend.label} observe?",
            answer=f"They observed that {case['clue']}.",
        ),
        QAItem(
            question="What had really happened to the tuft?",
            answer=f"{case['truth']}.",
        ),
        QAItem(
            question="How did the children repair the harm?",
            answer=f"{case['repair']}.",
        ),
        QAItem(
            question="What did justice mean in the story?",
            answer=JUSTICE_EXPLANATION,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tuft?",
            answer="A tuft is a small bunch or clump of hairs, fibers, feathers, or grass.",
        ),
        QAItem(
            question="What does tropic mean?",
            answer="Tropic describes places near the warm regions around the middle of Earth.",
        ),
        QAItem(
            question="What is justice?",
            answer=JUSTICE_EXPLANATION,
        ),
        QAItem(
            question="Why should people listen before blaming someone?",
            answer="Listening helps people learn the facts and avoid hurting someone with an unfair guess.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        lines.append(
            f"  {entity.id:8} ({entity.type:10}) {' '.join(details)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
truth_found :- clue(observed), listening(practiced).
harm_repaired :- truth_found, repair(done).
good_story :- tuft(present), tropic(setting), justice(value), harm_repaired.
#show good_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("tuft", "present"),
            asp.fact("tropic", "setting"),
            asp.fact("justice", "value"),
            asp.fact("clue", "observed"),
            asp.fact("listening", "practiced"),
            asp.fact("repair", "done"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show good_story/0."))
    good = any(symbol.name == "good_story" for symbol in model)
    if not good:
        print("MISMATCH: ASP twin did not find good_story.")
        return 1

    params = StoryParams("Luna", "Pip", "Auntie Noor")
    sample = generate(params)
    required = ("tuft", "tropic", "justice")
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story is missing a required seed word.")
        return 1
    if len(sample.story_qa) < 3:
        print("MISMATCH: generated story has too few story questions.")
        return 1

    print("OK: ASP twin agrees with the Python story model.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if not params.name.strip() or not params.friend_name.strip() or not params.elder_name.strip():
        raise StoryError("Character names must not be empty.")
    if params.case_id < 0 or params.case_id >= len(CASES):
        raise StoryError("case_id must select a known tuft case.")

    world = _build_world(params)
    tell(world)
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
    StoryParams("Luna", "Pip", "Auntie Noor", case_id=0, opening_id=0, dialogue_id=0, ending_id=0),
    StoryParams("Milo", "Mara", "Grandma Tala", case_id=1, opening_id=1, dialogue_id=1, ending_id=1),
    StoryParams("Nia", "Sol", "Uncle Ivo", case_id=2, opening_id=2, dialogue_id=2, ending_id=2),
    StoryParams("Tavi", "Bibi", "Gran Miri", case_id=3, opening_id=3, dialogue_id=3, ending_id=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show good_story/0."))
        print("good_story" if any(symbol.name == "good_story" for symbol in model) else "(none)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {sample.params.name} in the Tropic Garden"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
