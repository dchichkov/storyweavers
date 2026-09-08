#!/usr/bin/env python3
"""
A gentle fairy-tale world about kibble, a magical plant, and a lop-eared
rabbit who learns that clever problem solving must include caution.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def __post_init__(self) -> None:
        for key in ("hunger", "growth", "magic", "risk", "readiness"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "curiosity", "care", "pride", "relief", "wisdom"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Lop"
    friend_name: str = "Mina"
    place: str = "the moonlit garden"
    task: str = "feed the hungry garden animals"
    magic_style: str = "silver"
    caution_level: str = "gentle"


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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SCENARIOS = [
    {
        "problem": "the kibble jar was empty before supper",
        "mistake": "Lop whispered a spell over a single crumb and made a tower of kibble rise from the soil",
        "danger": "the tower grew so quickly that its crunchy pieces tumbled toward the pond",
        "clue": "the plant's leaves curled whenever the spell was spoken too loudly",
        "plan": "counted three seeds, placed them around the plant, and asked the garden keeper for permission before using a quiet rhyme",
        "result": "the plant grew one small bowl of fresh kibble, just enough for the hungry animals",
        "ending": "the magical plant held a single golden bowl beneath its leaves",
    },
    {
        "problem": "a rainstorm had soaked the evening kibble",
        "mistake": "Lop tried to dry every piece with a fiery charm",
        "danger": "the kibble popped like tiny stars and rolled beneath the hedges",
        "clue": "the plant leaned toward the warm but gentle lantern light",
        "plan": "spread the kibble on a clean tray and used the plant's shade to shield it while the lantern warmed the air",
        "result": "the food dried safely without sparks or scorched paws",
        "ending": "the dry kibble clicked softly into a row of waiting bowls",
    },
    {
        "problem": "a little fox had wandered away while carrying a pouch of kibble",
        "mistake": "Lop summoned a giant arrow made of blue smoke without checking where it pointed",
        "danger": "the arrow spun around and tangled itself in the plant's vines",
        "clue": "the plant's flowers opened whenever the fox called from the west path",
        "plan": "followed the flowers one at a time and used a small listening charm instead of a loud command",
        "result": "they found the fox beside the old well and brought the pouch back safely",
        "ending": "the plant's west-facing flowers glowed like a careful trail home",
    },
    {
        "problem": "the garden mice needed kibble, but the storehouse door was locked",
        "mistake": "Lop tried to turn the key into a dragon",
        "danger": "the tiny dragon sneezed and scattered the key into the compost",
        "clue": "the plant's roots had lifted a loose stone beside the door",
        "plan": "looked beneath the stone, retrieved the key, and asked the mice to carry only small bowls",
        "result": "the storehouse opened, and everyone shared the food without making a mess",
        "ending": "the old key rested on a leaf while the mice nibbled in peace",
    },
]


def _scenario_index(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed % len(SCENARIOS)
    return sum(ord(c) for c in params.hero_name + params.friend_name) % len(SCENARIOS)


def tell(params: StoryParams) -> World:
    if not params.hero_name.strip() or not params.friend_name.strip():
        raise StoryError("hero_name and friend_name must not be empty")
    if params.hero_name.lower() == params.friend_name.lower():
        raise StoryError("hero_name and friend_name must be different")

    scenario = SCENARIOS[_scenario_index(params)]
    w = World()
    hero = w.add(Entity(params.hero_name, "character", "lop-eared rabbit"))
    friend = w.add(Entity(params.friend_name, "character", "garden keeper"))
    kibble = w.add(Entity("kibble", "thing", "kibble", owner=friend.id))
    plant = w.add(Entity("plant", "thing", "enchanted kibble plant"))

    hero.memes["curiosity"] = 2
    hero.meters["readiness"] = 1
    friend.memes["care"] = 2
    plant.meters["magic"] = 2
    plant.meters["risk"] = 1
    kibble.meters["hunger"] = 2

    w.say(
        f"Beyond {params.place}, where stars hung like silver buttons, lived {hero.id}, "
        f"a lop-eared rabbit with a pocket full of questions."
    )
    w.say(
        f"One evening, {friend.id} asked {hero.id} to {params.task}. "
        f"The garden animals waited politely beside the enchanted plant."
    )
    w.para()

    w.say(
        f"The trouble was that {scenario['problem']}. "
        f"{hero.id} wanted to solve everything before anyone could blink."
    )
    hero.memes["curiosity"] += 1
    hero.meters["risk"] += 1
    w.say(
        f"'I know a magic trick!' cried {hero.id}. "
        f"{scenario['mistake']}, and {scenario['danger']}."
    )
    w.say(
        f"'Magic can help,' said {friend.id}, 'but a spell is still a tool. "
        "A tool needs a careful plan.'"
    )
    w.para()

    friend.memes["worry"] += 1
    hero.memes["worry"] += 1
    w.say(
        f"They watched instead of rushing. The useful clue was that {scenario['clue']}."
    )
    w.say(
        f"'What should we check first?' asked {hero.id}. "
        f"'The danger, the amount we need, and who might be hurt,' answered {friend.id}."
    )
    w.say(f"Together they {scenario['plan']}.")
    hero.meters["risk"] = 0
    hero.meters["readiness"] += 2
    hero.memes["wisdom"] += 1

    w.para()
    w.say(f"The careful plan worked: {scenario['result']}.")
    plant.meters["growth"] += 1
    plant.meters["risk"] = 0
    kibble.meters["hunger"] = 0
    friend.memes["relief"] += 1
    hero.memes["pride"] += 1
    w.say(
        f"{hero.id} learned that problem solving is more than finding a powerful answer. "
        "It means noticing clues, measuring the risk, and choosing a small enough step."
    )
    w.say(f"At moonrise, {scenario['ending']}.")
    w.say(
        f"{hero.id} tucked the spellbook away and promised {friend.id} to ask before "
        "using magic again. The plant rustled as if it agreed."
    )

    w.facts.update(
        hero=hero,
        friend=friend,
        kibble=kibble,
        plant=plant,
        scenario=scenario,
        params=params,
        resolved=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        f"Write a fairy tale about {p.hero_name}, a lop-eared rabbit, solving a kibble problem with careful magic.",
        f"Include an enchanted plant, a dangerous first spell, and the clue that {s['clue']}.",
        "Show that caution improves problem solving instead of making the hero helpless.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        QAItem(
            "Who was the main character?",
            f"The main character was {p.hero_name}, a lop-eared rabbit who wanted to help the garden animals."
        ),
        QAItem(
            "What problem did the garden have?",
            f"The problem was that {s['problem']}. The animals needed a safe way to get food."
        ),
        QAItem(
            "What went wrong with the first magic trick?",
            f"{p.hero_name} {s['mistake']}, and {s['danger']}. The spell was too rushed and risky."
        ),
        QAItem(
            "What clue helped solve the problem?",
            f"They noticed that {s['clue']}. That observation showed them how to use the plant more gently."
        ),
        QAItem(
            "How did the characters solve the problem?",
            f"Together they {s['plan']}. As a result, {s['result']}."
        ),
        QAItem(
            "What lesson did Lop learn?",
            "Lop learned that good problem solving includes checking danger, listening to a helper, and using only as much magic as needed."
        ),
    ]


KNOWLEDGE = [
    QAItem(
        "What is kibble?",
        "Kibble is small, dry pieces of food often given to pets or animals."
    ),
    QAItem(
        "What is a plant?",
        "A plant is a living thing that usually grows from the ground and uses light, water, and air."
    ),
    QAItem(
        "What does caution mean?",
        "Caution means slowing down to notice danger and choosing a safer action."
    ),
    QAItem(
        "What is magic in a fairy tale?",
        "Magic in a fairy tale is an imagined power that can change events, objects, or nature."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        if entity.owner:
            details.append(f"owner={entity.owner}")
        lines.append(f"  {entity.id:10} ({entity.type}) {' '.join(details)}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_plan :- observed_clue, checked_risk, resolved.
resolved :- used_small_spell.
checked_risk :- asked_helper.
observed_clue :- noticed_plant.
used_small_spell :- resolved.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("lop", "hero"),
            asp.fact("kibble", "food"),
            asp.fact("plant", "enchanted"),
            asp.fact("asked_helper"),
            asp.fact("noticed_plant"),
            asp.fact("checked_risk"),
            asp.fact("used_small_spell"),
            asp.fact("resolved"),
        ]
    )


def asp_program(show: str = "#show safe_plan/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    if "safe_plan" in names:
        print("OK: ASP and Python agree that the cautious plan is safe.")
        return 0
    print("MISMATCH: ASP did not derive safe_plan.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fairy-tale kibble plant problem-solving world.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--place")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero_name=args.hero_name or rng.choice(["Lop", "Pipkin", "Nettle", "Bramble"]),
        friend_name=args.friend_name or rng.choice(["Mina", "Tess", "Orla", "Juniper"]),
        place=args.place or rng.choice(
            ["the moonlit garden", "the whispering meadow", "the castle courtyard"]
        ),
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
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(seed=0, hero_name="Lop", friend_name="Mina"),
    StoryParams(seed=1, hero_name="Pipkin", friend_name="Orla"),
    StoryParams(seed=2, hero_name="Nettle", friend_name="Tess"),
    StoryParams(seed=3, hero_name="Bramble", friend_name="Juniper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + index)))
            for index in range(args.n)
        ]
        for index, sample in enumerate(samples):
            sample.params.seed = base_seed + index

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
