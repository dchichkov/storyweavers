#!/usr/bin/env python3
"""
A small mythic storyworld about a heading that remembers an old promise.

The heading is a carved sign above a hill shrine. Its rhyme is a spoken key,
and a flashback reveals why the sign was made. A young keeper must learn that
old words matter only when they guide a present act of courage.
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
        for key in ("weight", "brightness", "distance", "readiness", "danger"):
            self.meters.setdefault(key, 0.0)
        for key in ("fear", "wonder", "memory", "hope", "pride", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    guide_name: str = "Orin"
    place: str = "the hill of seven bells"
    heading: str = "When the Star Falls, Lift the Flame"
    rhyme: str = "Bright in the night, carry the light"


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
        "omen": "a blue star slipped from the evening sky and vanished beyond the ravine",
        "trial": "the shrine flame went out just as a cold wind rose",
        "flashback": "long ago, the first keeper crossed that same ravine during a storm to relight the hill beacon",
        "clue": "the old heading was not a warning to wait for rescue but a promise to carry hope where it was needed",
        "action": "wrapped the ember in a clay cup, tied it beneath a shepherd's cloak, and crossed the safe stone path",
        "result": "the beacon burned again before the mountain villages lost sight of one another",
        "ending": "the carved heading shone above a living flame while dawn touched the valley",
    },
    {
        "omen": "a golden bird circled the shrine three times and dropped a feather beside the bell rope",
        "trial": "the great bell cracked before the festival of first rain",
        "flashback": "the founding queen had once rung a smaller bell by hand to call scattered villagers home",
        "clue": "the heading praised a brave call, not a perfect instrument",
        "action": "made a smaller bell from a bronze cooking bowl and carried it to the ridge",
        "result": "its clear voice reached every house and summoned the people beneath the rain clouds",
        "ending": "the new bell rang under the heading, and every doorway answered",
    },
    {
        "omen": "silver mist covered the path to the moon well",
        "trial": "the well rope snapped before the thirsty travelers arrived",
        "flashback": "an ancestor had followed the sound of underground water by listening to stones beneath her feet",
        "clue": "the rhyme asked for light, but the memory taught Luna to listen as well",
        "action": "placed small lanterns along the safe stones and used a spare rope from the shrine store",
        "result": "the travelers found water without stepping onto the hidden marsh",
        "ending": "lanterns glittered beside the well while the heading kept its ancient watch",
    },
]


def _story_index(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(ch) for ch in params.hero_name + params.guide_name + params.heading)


def tell(params: StoryParams) -> World:
    index = _story_index(params)
    scenario = SCENARIOS[index % len(SCENARIOS)]
    w = World()

    hero = w.add(Entity(
        id=params.hero_name,
        kind="character",
        type="keeper",
        label="young shrine keeper",
    ))
    guide = w.add(Entity(
        id=params.guide_name,
        kind="character",
        type="elder",
        label="elder guide",
    ))
    sign = w.add(Entity(
        id="heading",
        type="carved_sign",
        label=params.heading,
        owner=params.hero_name,
    ))
    flame = w.add(Entity(id="flame", type="beacon_flame", label="hill beacon flame"))
    bell = w.add(Entity(id="bell", type="relic", label="old shrine relic"))

    hero.memes["wonder"] += 1
    hero.memes["fear"] += 1
    guide.memes["memory"] += 1
    sign.meters["weight"] += 2
    flame.meters["brightness"] += 1
    bell.meters["distance"] += 1

    w.say(f"On {params.place}, a stone shrine held a carved heading: “{params.heading}.”")
    w.say(
        f"{params.hero_name}, the young keeper, read it each morning while "
        f"{params.guide_name} swept the steps and watched the valley."
    )
    w.say(f"That evening, {scenario['omen']}. Then {scenario['trial']}.")
    w.say(
        f"{params.hero_name} gripped the shrine key. “Should I wait for a hero?” "
        f"{params.guide_name} answered, “Ask the heading what kind of hero it remembers.”"
    )

    w.para()
    hero.memes["memory"] += 1
    guide.memes["memory"] += 1
    w.say(
        f"{params.guide_name} touched the carved letters and told a flashback: "
        f"{scenario['flashback']}."
    )
    w.say(
        f"The elder spoke the old rhyme: “{params.rhyme}.” "
        f"{params.hero_name} repeated the words, but the meaning had changed."
    )
    w.say(f"Now {scenario['clue']}.")

    w.para()
    hero.meters["readiness"] += 1
    hero.memes["hope"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    w.say(
        f"“I am afraid,” said {params.hero_name}. “Good,” said {params.guide_name}. "
        "“Courage can carry fear without dropping it.”"
    )
    w.say(f"So {params.hero_name} {scenario['action']}.")
    flame.meters["brightness"] += 2
    sign.meters["weight"] = max(0.0, sign.meters["weight"] - 1)
    w.say(f"The old promise became a living deed: {scenario['result']}.")

    w.para()
    hero.memes["pride"] += 1
    hero.memes["relief"] += 1
    guide.memes["relief"] += 1
    w.say(
        f"When {params.hero_name} returned, {params.guide_name} asked, "
        "“What did the heading save?”"
    )
    w.say(
        f"{params.hero_name} looked from the carved words to the bright work below. "
        "“Not the past,” came the answer. “The next person who needed a light.”"
    )
    w.say(f"{scenario['ending']}")

    w.facts.update(
        params=params,
        hero=hero,
        guide=guide,
        heading=sign,
        flame=flame,
        bell=bell,
        scenario=scenario,
        resolved=True,
        flashback_used=True,
        rhyme_used=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        f"Write a myth about {p.hero_name}, a shrine heading, and a promise that must become an action.",
        f"Include the rhyme “{p.rhyme}” and a flashback about {s['flashback']}.",
        "End with a concrete image showing that an old legend changed the present.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    s = f["scenario"]
    return [
        QAItem(
            question=f"What heading did {p.hero_name} read?",
            answer=f'The heading said, “{p.heading}.” It became a reminder to act bravely when the valley needed help.'
        ),
        QAItem(
            question="What trouble came to the shrine?",
            answer=f"{s['omen'].capitalize()}, and then {s['trial']}."
        ),
        QAItem(
            question="What did the flashback reveal?",
            answer=f"It revealed that {s['flashback']}. The old memory showed that the heading had once guided real courage."
        ),
        QAItem(
            question="What rhyme did the keeper speak?",
            answer=f'The keeper spoke, “{p.rhyme},” a rhyme about carrying light through darkness.'
        ),
        QAItem(
            question=f"How did {p.hero_name} solve the problem?",
            answer=f"{p.hero_name} {s['action']}. This worked because the keeper turned the remembered promise into a careful present action."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The heading was no longer only an old carving. {s['ending'].capitalize()} It had become a living guide for hope."
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What is a heading?",
        answer="A heading is a title or line of words placed above a passage, sign, or subject to tell what it is about."
    ),
    QAItem(
        question="What is a rhyme?",
        answer="A rhyme is a pattern in which words have matching or similar ending sounds."
    ),
    QAItem(
        question="What is a flashback in a story?",
        answer="A flashback is a scene that returns to an earlier time so the reader can learn about the past."
    ),
    QAItem(
        question="What is a myth?",
        answer="A myth is a traditional or imaginative story that often explains a value, a mystery, or the deeds of remarkable people."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if abs(v) > 1e-9}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if entity.owner:
            parts.append(f"owner={entity.owner}")
        lines.append(f"  {entity.id:10} ({entity.type:12}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
heading_present :- heading(_).
rhyme_used :- rhyme(_).
flashback_used :- flashback(_).
hero_ready :- readiness(hero).
resolved_story :- heading_present, rhyme_used, flashback_used, hero_ready, resolved.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("heading", "ancient"),
        asp.fact("rhyme", "light"),
        asp.fact("flashback", "founding_keeper"),
        asp.fact("readiness", "hero"),
        asp.fact("resolved"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved_story/0."))
    ok = any(symbol.name == "resolved_story" for symbol in model)
    if not ok:
        print("MISMATCH: ASP did not derive a resolved story.")
        return 1
    for seed in range(6):
        sample = generate(StoryParams(seed=seed))
        if not sample.story or "heading" not in sample.story.lower():
            print(f"MISMATCH: generated story failed for seed {seed}.")
            return 1
        if not sample.world.facts["flashback_used"]:
            print(f"MISMATCH: flashback missing for seed {seed}.")
            return 1
    print("OK: ASP and Python agree; generated stories passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic heading, rhyme, and flashback storyworld.")
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
    parser.add_argument("--guide-name")
    parser.add_argument("--heading")
    parser.add_argument("--rhyme")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    heroes = ["Luna", "Mira", "Sela", "Nara"]
    guides = ["Orin", "Tovan", "Ilyr", "Mael"]
    headings = [
        "When the Star Falls, Lift the Flame",
        "Call the Rain, Guard the Plain",
        "Where Shadows Grow, Let Kindness Show",
        "By Moonlit Stone, No One Walks Alone",
    ]
    rhymes = [
        "Bright in the night, carry the light",
        "Rain on the grain, hope through the pain",
        "Glow as you go, help those below",
        "Stone by stone, bring them home",
    ]
    return StoryParams(
        seed=args.seed,
        hero_name=args.hero_name or rng.choice(heroes),
        guide_name=args.guide_name or rng.choice(guides),
        heading=args.heading or rng.choice(headings),
        rhyme=args.rhyme or rng.choice(rhymes),
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
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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
    StoryParams(
        hero_name="Luna",
        guide_name="Orin",
        heading="When the Star Falls, Lift the Flame",
        rhyme="Bright in the night, carry the light",
    ),
    StoryParams(
        hero_name="Mira",
        guide_name="Tovan",
        heading="Where Shadows Grow, Let Kindness Show",
        rhyme="Glow as you go, help those below",
    ),
    StoryParams(
        hero_name="Sela",
        guide_name="Mael",
        heading="By Moonlit Stone, No One Walks Alone",
        rhyme="Stone by stone, bring them home",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp.one_model(asp_program("#show resolved_story/0.")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
