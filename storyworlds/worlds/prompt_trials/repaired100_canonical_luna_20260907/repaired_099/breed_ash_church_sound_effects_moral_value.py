#!/usr/bin/env python3
"""
A gentle bedtime-story world about a small dog breed, ash from a church stove,
and the moral value of caring for a shared quiet place.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
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

    def __post_init__(self) -> None:
        for key in ("warmth", "noise", "cleanliness", "distance", "readiness"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "care", "pride", "relief", "kindness", "curiosity"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    friend_name: str = "Milo"
    breed: str = "small silver terrier"
    place: str = "the hilltop church"
    object_name: str = "the old bell rope"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


SCENARIOS = [
    {
        "problem": "a puff of ash had drifted across the church steps and made the bell rope gray",
        "sound": "whuff, whuff",
        "clue": "the ash was light enough to gather with a damp cloth instead of a hard brush",
        "plan": "opened the side window, laid a cloth beneath the rope, and carried the ash to the garden compost",
        "result": "the steps became clean without sending a cloud into the sleeping nave",
        "ending": "the bell gave one soft ding before Luna curled beneath the warm pew",
        "moral": "care for a shared place with a gentle hand",
    },
    {
        "problem": "cold ash had spilled beside the church stove and covered a little wooden cross",
        "sound": "scritch, scritch",
        "clue": "the stove was already cold, but a covered tin would keep the ash from scattering",
        "plan": "asked the keeper to check the stove, then used a small scoop and a covered tin",
        "result": "the floor was safe and the wooden cross was clean again",
        "ending": "the stove rested quietly while moonlight touched the polished cross",
        "moral": "ask for help when a task could be unsafe",
    },
    {
        "problem": "wind had blown ash into the church garden and darkened the white stepping stones",
        "sound": "flutter, hush",
        "clue": "the stones could be rinsed after the loose ash was gathered",
        "plan": "made a little windbreak from boards and swept only after the gusts softened",
        "result": "the ash stayed in one small pile and the stepping stones shone",
        "ending": "a night moth landed on the cleanest stone",
        "moral": "patience can protect the work of many hands",
    },
    {
        "problem": "ash had settled on the choir bench where visitors rested after evening prayers",
        "sound": "tap, tap",
        "clue": "a folded cloth lifted the ash without scratching the old wood",
        "plan": "placed a sign by the door, wiped the bench, and washed the cloth outside",
        "result": "the bench was ready for everyone without making a noisy fuss",
        "ending": "the last candle flickered above the quiet, clean bench",
        "moral": "small acts of care welcome people you may never meet",
    },
]


OPENINGS = [
    "The village was settling down for the night when Luna noticed something unusual.",
    "Just before bedtime, a tiny sound drifted from the hilltop.",
    "Luna loved quiet evenings, especially when the church bell had finished singing.",
    "A silver moon rose above the village, and one small dog found a useful job.",
]


def _validate(params: StoryParams) -> None:
    for field_name in ("hero_name", "friend_name", "breed", "place", "object_name"):
        value = getattr(params, field_name)
        if not value or not value.strip():
            raise StoryError(f"{field_name} must not be empty.")
    if params.hero_name.strip().lower() == params.friend_name.strip().lower():
        raise StoryError("hero_name and friend_name must be different.")
    if params.breed.strip().lower() not in {
        "small silver terrier",
        "little brown spaniel",
        "tiny white shepherd",
        "young black collie",
    }:
        raise StoryError("breed must be one of the registered story breeds.")


def _index(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(ch) for ch in params.hero_name + params.friend_name + params.breed)


def tell(params: StoryParams) -> World:
    _validate(params)
    scenario = SCENARIOS[_index(params) % len(SCENARIOS)]
    opening = OPENINGS[(_index(params) // len(SCENARIOS)) % len(OPENINGS)]
    world = World()

    luna = world.add(Entity(params.hero_name, "character", "dog", params.breed))
    friend = world.add(Entity(params.friend_name, "character", "child", "church helper"))
    church = world.add(Entity("church", "place", "church", params.place))
    ash = world.add(Entity("ash", "material", "ash", "cold gray ash"))
    bell = world.add(Entity("bell", "thing", "bell", "church bell"))
    cloth = world.add(Entity("cloth", "tool", "cloth", "damp cleaning cloth"))

    luna.memes["curiosity"] = 1.0
    friend.memes["care"] = 1.0
    ash.meters["noise"] = 0.0
    church.meters["cleanliness"] = 0.0
    bell.meters["noise"] = 1.0

    world.say(opening)
    world.say(
        f"Luna was a {params.breed} who lived near {params.place}. "
        f"Her friend {params.friend_name} often helped care for the old church before everyone went to sleep."
    )
    world.say(
        f"That evening, {scenario['problem']}. Luna tilted her head, and the little church seemed to whisper, "
        f"'{scenario['sound']}.'"
    )

    world.para()
    world.say(
        f"'We should fix it before morning,' said {params.hero_name}. "
        f"'Yes, but gently,' replied {params.friend_name}. 'The church belongs to everyone.'"
    )
    luna.memes["worry"] = 1.0
    friend.memes["care"] += 1.0
    world.say(
        f"Luna first tried to wag the ash away. It only made a soft gray ring around her paws. "
        f"{params.friend_name} smiled and said, 'Let us look for a better clue.'"
    )
    world.say(f"They discovered that {scenario['clue']}.")
    world.say(
        f"Together they {scenario['plan']}. The work made a tiny sound: {scenario['sound']}, "
        "and then the night grew peaceful again."
    )

    world.para()
    church.meters["cleanliness"] = 1.0
    church.meters["readiness"] = 1.0
    luna.memes["relief"] = 1.0
    luna.memes["kindness"] = 1.0
    friend.memes["pride"] = 1.0
    world.say(f"The plan worked: {scenario['result']}.")
    world.say(
        f"{params.friend_name} thanked Luna. 'What is the moral value of our work?' "
        f"they asked. Luna placed one clean paw on the step. 'We care for shared things because everyone deserves a welcome.'"
    )
    world.say(f"At last, {scenario['ending']}.")
    world.say(
        f"Luna learned that {scenario['moral']}. The quiet church, the clean ash place, and the sleeping village "
        "all seemed to agree."
    )

    world.facts.update(
        params=params,
        scenario=scenario,
        luna=luna,
        friend=friend,
        church=church,
        ash=ash,
        bell=bell,
        cloth=cloth,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write a gentle bedtime story about {params.hero_name}, a {params.breed}, helping at {params.place}.",
        f"Include ash, a church, and the sound effect '{scenario['sound']}' as the problem is solved.",
        f"End with the moral value that {scenario['moral']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    params = facts["params"]
    scenario = facts["scenario"]
    return [
        QAItem(
            "Who was Luna?",
            f"Luna was a {params.breed} who lived near {params.place} and wanted to help."
        ),
        QAItem(
            "What trouble did the ash cause?",
            f"{scenario['problem'].capitalize()}."
        ),
        QAItem(
            "What sound effect appeared in the story?",
            f"The small sounds were '{scenario['sound']}', used to make the quiet cleaning feel vivid."
        ),
        QAItem(
            "How did Luna and her friend solve the problem?",
            f"They {scenario['plan']}. This worked because they used a gentle, safe method."
        ),
        QAItem(
            "What moral value did Luna learn?",
            f"Luna learned that {scenario['moral']}, because the church was a shared place."
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "What is ash?",
        "Ash is the fine, powdery material left after something such as wood has burned and cooled."
    ),
    QAItem(
        "Why should cold ash be handled carefully?",
        "Even ash that looks cold can hide heat or spread into the air, so an adult should check it and use safe tools."
    ),
    QAItem(
        "What is a church?",
        "A church is a place where a religious community may gather for prayer, music, ceremonies, and quiet reflection."
    ),
    QAItem(
        "What does breed mean?",
        "A breed is a group of domesticated animals with shared inherited traits, such as size, shape, or coat."
    ),
    QAItem(
        "Why are sound effects useful in a bedtime story?",
        "Sound effects such as 'ding' or 'scritch' help children imagine an event without making the story confusing."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.type:8}) meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
safe_ash_handling :- adult_checked, covered_tool, resolved.
shared_care :- church, resolved.
moral_value(care) :- shared_care.
quiet_resolution :- sound_effect, resolved.
breed_story :- dog(hero).
"""


def asp_facts(world: Optional[World] = None) -> str:
    import asp
    return "\n".join(
        [
            asp.fact("dog", "hero"),
            asp.fact("dog_breed", "small_terrier"),
            asp.fact("church"),
            asp.fact("ash"),
            asp.fact("sound_effect"),
            asp.fact("adult_checked"),
            asp.fact("covered_tool"),
            asp.fact("resolved"),
        ]
    )


def asp_program(world: Optional[World] = None, show: str = "#show.") -> str:
    return f"{asp_facts(world)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(
        asp_program(
            show="#show safe_ash_handling/0.\n#show shared_care/0.\n#show moral_value/1."
        )
    )
    names = {sym.name for sym in model}
    required = {"safe_ash_handling", "shared_care", "moral_value"}
    if not required.issubset(names):
        print("MISMATCH: ASP did not derive the expected story properties.")
        return 1
    for seed in range(8):
        sample = generate(StoryParams(seed=seed))
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story was not resolved.")
            return 1
    print("OK: ASP and Python agree that the stories are safe, shared, and resolved.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bedtime story about Luna, ash, and a church.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--breed")
    parser.add_argument("--place")
    parser.add_argument("--object-name")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero_name=args.hero_name or rng.choice(["Luna", "Nora", "Pip", "Daisy"]),
        friend_name=args.friend_name or rng.choice(["Milo", "Tess", "Owen", "Ivy"]),
        breed=args.breed or rng.choice(
            [
                "small silver terrier",
                "little brown spaniel",
                "tiny white shepherd",
                "young black collie",
            ]
        ),
        place=args.place or "the hilltop church",
        object_name=args.object_name or "the old bell rope",
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    StoryParams(hero_name="Luna", friend_name="Milo", breed="small silver terrier"),
    StoryParams(hero_name="Nora", friend_name="Tess", breed="little brown spaniel"),
    StoryParams(hero_name="Daisy", friend_name="Owen", breed="tiny white shepherd"),
    StoryParams(hero_name="Pip", friend_name="Ivy", breed="young black collie"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show safe_ash_handling/0.\n#show shared_care/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print(
            asp.one_model(
                asp_program(
                    show="#show safe_ash_handling/0.\n#show shared_care/0.\n#show moral_value/1."
                )
            )
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for offset in range(args.n):
            params = resolve_params(args, random.Random(base_seed + offset))
            params.seed = base_seed + offset
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
