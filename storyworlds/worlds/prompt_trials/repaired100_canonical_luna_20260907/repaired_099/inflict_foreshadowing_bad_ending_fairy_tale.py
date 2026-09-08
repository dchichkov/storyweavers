#!/usr/bin/env python3
"""
A small fairy-tale storyworld about inflicting a careless curse, noticing its
foreshadowing too late, and learning that a bad ending can grow from an
unrepaired choice.
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
        for key in ("danger", "weariness", "hope", "warmth"):
            self.meters.setdefault(key, 0.0)
        for key in ("fear", "pride", "regret", "kindness", "wonder"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    companion_name: str = "Moss"
    ruler_name: str = "Queen Elira"
    setting: str = "the kingdom of Bellflower"
    object_name: str = "the silver bell"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
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


SCENARIOS = [
    {
        "task": "protect the village from a greedy thorn-witch",
        "danger": "the witch had promised to return when the silver bell rang three times",
        "inflict": "Luna struck the bell in anger, and a shadow-mark spread across Queen Elira's crown",
        "foreshadow": "each bell rope had a black thread tied around it, warning that the bell answered angry hands",
        "choice": "admit what she had done and carry the bell to the Moonwell before sunset",
        "turn": "the Moonwell's clear water loosened the shadow-mark, but only after Luna apologized to the queen and the villagers",
        "ending": "the black threads were removed, and the bell rang softly for a feast instead of a curse",
    },
    {
        "task": "cross the whispering bridge to deliver a healing rose",
        "danger": "the bridge remembered every cruel word spoken upon it",
        "inflict": "Luna shouted at the bridge, and the planks grew cold beneath Moss's feet",
        "foreshadow": "small gray letters on the railing warned, Speak gently, or the road will close",
        "choice": "use kind words and tell the bridge why the rose mattered",
        "turn": "the planks warmed and lowered themselves until the travelers could reach the far bank",
        "ending": "the rose reached the sick gardener, though the bridge kept one cold plank as a lesson",
    },
    {
        "task": "wake the sleeping sun-dragon before winter covered the valley",
        "danger": "the dragon's dream-fire could scorch anyone who startled it",
        "inflict": "Luna threw a stone at its golden horn, and a line of fire burned across the snow",
        "foreshadow": "the cave wall showed old pictures of careful singers waking the dragon with music",
        "choice": "play Moss's tiny flute from a safe distance and wait for the dragon to open one eye",
        "turn": "the dragon breathed a warm sunrise over the valley and cooled the burned snow with a sigh",
        "ending": "spring returned, but the black line in the snow remained until Luna repaired the frightened villagers' fences",
    },
    {
        "task": "find the lost prince beneath the clockwork forest",
        "danger": "the forest's brass roots tightened around anyone who hurried",
        "inflict": "Luna cut a root with a borrowed sword, and every tree began turning backward",
        "foreshadow": "a little wooden owl repeatedly pointed to a sign that said, Patience keeps the hours",
        "choice": "stop cutting, follow the owl's slow path, and return the sword",
        "turn": "the forest clocks began moving forward, revealing the prince inside a quiet green carriage",
        "ending": "the prince was found, but the forest kept one backward hour for every tree Luna had wounded",
    },
]


def _choose_scenario(params: StoryParams) -> dict[str, str]:
    index = params.seed if params.seed is not None else sum(
        ord(c) for c in params.hero_name + params.companion_name
    )
    return SCENARIOS[index % len(SCENARIOS)]


def tell(params: StoryParams) -> World:
    if not params.hero_name.strip() or not params.companion_name.strip():
        raise StoryError("hero_name and companion_name must not be empty")
    scenario = _choose_scenario(params)
    w = World()

    hero = w.add(Entity(params.hero_name, "character", "apprentice", params.hero_name))
    companion = w.add(Entity(params.companion_name, "character", "fox companion", params.companion_name))
    ruler = w.add(Entity("ruler", "character", "queen", params.ruler_name))
    bell = w.add(Entity("bell", "object", "enchanted bell", params.object_name, owner="ruler"))
    omen = w.add(Entity("omen", "object", "foreshadowing sign", "old warning"))

    hero.memes["pride"] = 1
    hero.meters["danger"] = 1
    companion.memes["wonder"] = 1
    ruler.memes["fear"] = 1
    bell.meters["danger"] = 2

    w.say(
        f"Once, in {params.setting}, {params.hero_name} served as an eager apprentice to "
        f"{params.ruler_name}. {params.companion_name}, a clever fox, followed wherever courage was needed."
    )
    w.say(f"The queen asked them to {scenario['task']}.")
    w.say(
        f"'I can solve it at once,' {params.hero_name} declared. "
        f"'First listen,' said {params.companion_name}. 'A fairy-tale danger often whispers before it roars.'"
    )

    w.para()
    hero.memes["pride"] += 1
    ruler.memes["fear"] += 1
    w.say(f"The danger was plain: {scenario['danger']}.")
    w.say(f"Then {scenario['inflict']}.")
    w.say(
        f"{params.companion_name} pointed to the warning. {scenario['foreshadow'].capitalize()} "
        f"'That was foreshadowing,' said the fox. 'It showed what might happen before it happened.'"
    )
    w.say(
        f"'I did not mean to hurt anyone,' {params.hero_name} whispered. "
        f"'Meaning well does not mend an inflicted wound,' replied {params.ruler_name}. "
        "'Choose what you do next.'"
    )

    w.para()
    hero.memes["regret"] += 2
    hero.meters["hope"] += 1
    w.say(f"{params.hero_name} could have hidden the mistake and hurried toward a bad ending.")
    w.say(f"Instead, {params.hero_name} decided to {scenario['choice']}.")
    w.say(
        f"{params.companion_name} stayed beside the apprentice. "
        f"Together they faced the danger, and {scenario['turn']}."
    )

    w.para()
    ruler.memes["fear"] = 0
    ruler.memes["kindness"] = 1
    hero.memes["kindness"] += 2
    hero.meters["hope"] += 2
    w.say(
        f"The kingdom was not perfectly mended. A careless act leaves a mark, and a bad ending "
        f"can begin with one proud moment. Yet {params.hero_name} had stopped the harm from spreading."
    )
    w.say(f"At moonrise, {scenario['ending']}.")
    w.say(
        f"From then on, {params.hero_name} watched for warnings, listened before acting, "
        "and remembered that courage is not only a bright sword but also an honest repair."
    )

    w.facts.update(
        params=params,
        hero=hero,
        companion=companion,
        ruler=ruler,
        bell=bell,
        omen=omen,
        scenario=scenario,
        resolved=True,
        foreshadowing_seen=True,
        bad_ending_avoided=True,
        harm_inflicted=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        f"Write a fairy tale about {p.hero_name} learning not to inflict harm through careless magic.",
        f"Use foreshadowing: {s['foreshadow']}.",
        "Include a possible bad ending, then let an honest repair change the result.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    s = f["scenario"]
    return [
        QAItem(
            "What danger faced the characters?",
            f"The danger was that {s['danger']}.",
        ),
        QAItem(
            f"What did {p.hero_name} inflict?",
            f"{p.hero_name} carelessly inflicted harm when {s['inflict']}.",
        ),
        QAItem(
            "What was the foreshadowing?",
            f"The warning was that {s['foreshadow']}. It hinted at the trouble before the trouble arrived.",
        ),
        QAItem(
            "How was a bad ending avoided?",
            f"The apprentice admitted the mistake and chose to {s['choice']}. Then {s['turn']}.",
        ),
        QAItem(
            "What did the apprentice learn?",
            f"{p.hero_name} learned to watch for warnings, listen before acting, and repair harm honestly.",
        ),
    ]


KNOWLEDGE = [
    QAItem(
        "What is foreshadowing?",
        "Foreshadowing is a clue that hints at something likely to happen later in a story.",
    ),
    QAItem(
        "What does inflict mean?",
        "Inflict means to cause something painful, harmful, or unpleasant to happen to someone or something.",
    ),
    QAItem(
        "What is a bad ending in a fairy tale?",
        "A bad ending is an unhappy result in which the danger wins or the characters fail to repair their mistake.",
    ),
    QAItem(
        "Why can admitting a mistake help?",
        "Admitting a mistake helps people understand the harm, make a better choice, and begin repairing what was damaged.",
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
        lines.append(f"  {entity.id:10} ({entity.type:16}) {' '.join(details)}")
    return "\n".join(lines)


ASP_RULES = r"""
harm_inflicted :- inflicted.
foreshadowing_seen :- warning, danger.
repair_attempted :- admitted, chose_repair.
resolved :- repair_attempted, not bad_ending.
bad_ending :- inflicted, not admitted.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "luna"),
            asp.fact("companion", "moss"),
            asp.fact("ruler", "queen"),
            asp.fact("danger", "active"),
            asp.fact("warning", "present"),
            asp.fact("inflicted"),
            asp.fact("admitted"),
            asp.fact("chose_repair"),
            asp.fact("not_bad_ending"),
        ]
    )


def asp_program(show: str = "#show resolved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    resolved = any(symbol.name == "resolved" for symbol in model)
    python_ok = True
    sample = generate(StoryParams(seed=7))
    python_ok = bool(sample.world and sample.world.facts["resolved"])
    if resolved and python_ok:
        print("OK: ASP and Python agree that the repaired tale is resolved.")
        return 0
    print("MISMATCH: ASP and Python disagree about resolution.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fairy-tale foreshadowing storyworld.")
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
    parser.add_argument("--companion-name")
    parser.add_argument("--ruler-name")
    parser.add_argument("--setting")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero_name=args.hero_name or rng.choice(["Luna", "Mira", "Elian", "Tessa"]),
        companion_name=args.companion_name or rng.choice(["Moss", "Pip", "Bram", "Nettle"]),
        ruler_name=args.ruler_name or rng.choice(["Queen Elira", "King Rowan", "Queen Maelin"]),
        setting=args.setting or rng.choice(
            ["the kingdom of Bellflower", "the valley of Seven Moons", "the village beyond the silver wood"]
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
    sections = ["== (1) Generation prompts =="]
    sections.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    sections.append("")
    sections.append("== (2) Story questions ==")
    for item in sample.story_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    sections.append("")
    sections.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(sections)


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
    StoryParams(hero_name="Luna", companion_name="Moss", ruler_name="Queen Elira"),
    StoryParams(hero_name="Mira", companion_name="Nettle", ruler_name="King Rowan", seed=1),
    StoryParams(hero_name="Tessa", companion_name="Bram", ruler_name="Queen Maelin", seed=2),
    StoryParams(hero_name="Elian", companion_name="Pip", ruler_name="Queen Elira", seed=3),
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
        samples = [generate(params) for params in CURATED]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + i)))
            for i in range(max(1, args.n))
        ]
        for i, sample in enumerate(samples):
            sample.params.seed = base_seed + i

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
