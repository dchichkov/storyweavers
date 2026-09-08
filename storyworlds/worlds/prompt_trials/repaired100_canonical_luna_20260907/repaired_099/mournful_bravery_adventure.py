#!/usr/bin/env python3
"""
A small adventure storyworld about Luna learning that bravery can carry sadness
without hiding it.

The world models:
- physical meters such as distance, light, fatigue, and danger
- emotional memes such as grief, courage, trust, and relief
- a mournful journey to return a lost bell to an old hill shrine
"""

from __future__ import annotations

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
        for key in ("distance", "light", "fatigue", "danger", "readiness"):
            self.meters.setdefault(key, 0.0)
        for key in ("grief", "courage", "trust", "relief", "hope"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    guide_name: str = "Ari"
    place: str = "the blue mountain trail"
    destination: str = "the old hill shrine"
    keepsake: str = "a little silver bell"


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
        "opening": "The mountain road was bright with snow, but Luna carried a mournful silence beside her.",
        "loss": "the bell had belonged to her grandmother, who used to ring it whenever the family returned home",
        "obstacle": "a narrow bridge had lost two of its wooden boards above a rushing stream",
        "clue": "red trail ribbons tied by earlier travelers marked a safer crossing higher up the slope",
        "plan": "they followed the ribbons, tested each stone with the walking staff, and crossed one careful step at a time",
        "turn": "halfway across, Luna heard the bell's faint chime beneath a fallen pine",
        "result": "Luna crawled beneath the branches while Ari held a rope, and together they freed the bell without stepping near the broken bridge",
        "ending": "At the shrine, Luna hung the silver bell in the evening wind, and its clear note carried her sadness toward the stars.",
        "joke": "Ari whispered that even the mountain seemed to be holding its breath.",
    },
    {
        "opening": "Clouds rolled over the high pass as Luna began an adventure with a heavy heart.",
        "loss": "her grandmother had once carried the bell on every spring journey to the hill shrine",
        "obstacle": "a sudden fog swallowed the path and made every gray rock look like the next",
        "clue": "small brass markers on the trees still glimmered whenever Luna held up her lantern",
        "plan": "they walked from marker to marker, keeping the lantern low and their hands joined",
        "turn": "the fog opened for one moment, revealing the shrine far above them",
        "result": "Luna chose the next marker, and Ari trusted her directions until the path rose clear of the fog",
        "ending": "When Luna rang the bell at the shrine, the sound was mournful at first, then warm and steady.",
        "joke": "Ari said the fog had been a terrible guide but an excellent curtain.",
    },
    {
        "opening": "Luna climbed into the wild valley where old paths curled between cliffs.",
        "loss": "the bell reminded her of a loved one who would not make this journey again",
        "obstacle": "rain had turned the trail into slippery brown ribbons",
        "clue": "flat stepping stones formed a safer line beside the roots",
        "plan": "they wrapped the bell in a scarf, shortened their steps, and used the stones instead of the muddy slope",
        "turn": "a gust tore the scarf loose, and the bell rolled toward the ravine",
        "result": "Luna reached it with a hooked branch while Ari anchored her safely from behind",
        "ending": "The bell rested above the ravine, shining with rain as Luna gave it one brave, gentle ring.",
        "joke": "Ari declared that the muddy trail had tried to become a river and failed.",
    },
]


def _scenario(params: StoryParams) -> dict[str, str]:
    index = params.seed if params.seed is not None else sum(ord(c) for c in params.hero_name)
    return SCENARIOS[index % len(SCENARIOS)]


def tell(params: StoryParams) -> World:
    if not params.hero_name.strip():
        raise StoryError("hero_name must not be empty")
    if not params.guide_name.strip():
        raise StoryError("guide_name must not be empty")
    if params.hero_name == params.guide_name:
        raise StoryError("hero_name and guide_name must be different")

    scenario = _scenario(params)
    world = World()
    hero = world.add(Entity(params.hero_name, kind="character", type="child", label="brave traveler"))
    guide = world.add(Entity(params.guide_name, kind="character", type="character", label="trusted guide"))
    bell = world.add(Entity("bell", type="keepsake", label=params.keepsake, owner=params.hero_name))
    shrine = world.add(Entity("shrine", type="place", label=params.destination))

    hero.memes["grief"] = 2.0
    hero.memes["courage"] = 0.5
    guide.memes["trust"] = 1.0
    hero.meters["distance"] = 0.0
    hero.meters["danger"] = 1.0
    bell.meters["light"] = 1.0

    world.say(scenario["opening"].replace("Luna", params.hero_name))
    world.say(
        f"In {params.place}, {params.hero_name} carried {params.keepsake} toward "
        f"{params.destination}. {scenario['loss'].replace('her', params.hero_name + \"'s\")}"
    )
    world.say(
        f"{params.guide_name} walked beside {params.hero_name}, carrying a rope and a lantern."
    )

    world.para()
    world.say(
        f"The first trouble came when {scenario['obstacle']}. "
        f"{params.hero_name} stopped at the edge."
    )
    world.say(
        f"'{params.guide_name}, I feel afraid and sad,' {params.hero_name} said. "
        f"'{params.guide_name}, may we turn back?'"
    )
    world.say(
        f"'{params.hero_name}, bravery does not mean feeling nothing,' {params.guide_name} replied. "
        "'It means choosing a careful next step while the feeling comes with you.'"
    )
    hero.memes["courage"] += 1.0
    hero.meters["readiness"] += 1.0
    world.say(f"Then they noticed that {scenario['clue']}.")

    world.para()
    world.say(f"Together they {scenario['plan']}.")
    hero.meters["distance"] += 1.0
    hero.meters["fatigue"] += 1.0
    hero.meters["danger"] = 0.5
    guide.memes["trust"] += 1.0
    world.say(scenario["turn"].replace("Luna", params.hero_name))
    world.say(f"{scenario['result'].replace('Luna', params.hero_name).replace('Ari', params.guide_name)}.")
    hero.memes["courage"] += 1.0
    hero.memes["hope"] += 1.0
    bell.meters["light"] += 1.0

    world.para()
    world.say(
        f"At last, {params.hero_name} reached {params.destination}. "
        f"{scenario['ending'].replace('Luna', params.hero_name)}"
    )
    world.say(
        f"{params.hero_name} still missed her grandmother, but the mournful feeling no longer "
        "made the path impossible. It had traveled with her, while bravery helped her keep going."
    )
    world.say(scenario["joke"].replace("Ari", params.guide_name))
    hero.memes["relief"] += 1.0

    world.facts.update(
        params=params,
        hero=hero,
        guide=guide,
        bell=bell,
        shrine=shrine,
        scenario=scenario,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        f"Write an adventure about {p.hero_name} carrying {p.keepsake} to {p.destination}.",
        f"Show bravery as a careful action while {p.hero_name} feels mournful because {s['loss']}.",
        f"Include the obstacle that {s['obstacle']} and a spoken exchange that changes the plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        QAItem(
            "Who was the adventure about?",
            f"It was about {p.hero_name}, a traveler who carried {p.keepsake} to {p.destination} while feeling mournful.",
        ),
        QAItem(
            "Why was the journey sad for the hero?",
            f"The keepsake reminded {p.hero_name} of a loved one who could not make the journey again, because {s['loss']}.",
        ),
        QAItem(
            "What danger did the travelers meet first?",
            f"They met the danger that {s['obstacle']}. They responded by looking for a safer route instead of rushing.",
        ),
        QAItem(
            "What did the guide teach about bravery?",
            "The guide taught that bravery does not mean feeling nothing; it means choosing a careful next step even while fear or sadness is present.",
        ),
        QAItem(
            "How did the travelers solve the main problem?",
            f"They {s['plan']}, and later {s['result'].lower()}.",
        ),
        QAItem(
            "How did the story end?",
            f"{p.hero_name} reached {p.destination} and rang the keepsake. The mournful feeling remained, but bravery and hope helped the hero continue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is bravery?",
            "Bravery is choosing a thoughtful or helpful action even when a person feels afraid, sad, or uncertain.",
        ),
        QAItem(
            "What does mournful mean?",
            "Mournful means feeling or expressing deep sadness, often because someone or something important has been lost.",
        ),
        QAItem(
            "Why is it useful to speak about fear during an adventure?",
            "Speaking about fear helps companions understand what is happening and can lead to a safer plan.",
        ),
        QAItem(
            "Does bravery require a person to stop feeling sad?",
            "No. A person can feel sad and still act bravely, carefully, and kindly.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if entity.owner:
            parts.append(f"owner={entity.owner}")
        lines.append(f"  {entity.id:10} ({entity.type:10}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
brave_action :- resolved, courage >= 1.
safe_journey :- resolved, danger < 1.
hopeful_end :- resolved, hope >= 1.
mournful_bravery :- resolved, brave_action, grief >= 1.
"""


def asp_facts(world: Optional[World] = None) -> str:
    import asp

    facts = [
        asp.fact("hero", "traveler"),
        asp.fact("guide", "companion"),
        asp.fact("keepsake", "bell"),
        asp.fact("place", "shrine"),
        asp.fact("theme", "mournful"),
        asp.fact("feature", "bravery"),
        asp.fact("resolved"),
        asp.fact("courage", 2),
        asp.fact("grief", 2),
        asp.fact("hope", 1),
        asp.fact("danger", 0),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show mournful_bravery/0."))
    if any(symbol.name == "mournful_bravery" for symbol in model):
        print("OK: ASP and Python agree that the hero showed mournful bravery.")
        return 0
    print("MISMATCH: ASP did not derive mournful_bravery.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mournful bravery adventure storyworld.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--hero-name")
    parser.add_argument("--guide-name")
    parser.add_argument("--place")
    parser.add_argument("--destination")
    parser.add_argument("--keepsake")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero_name=args.hero_name or rng.choice(["Luna", "Mira", "Nell", "Tavi"]),
        guide_name=args.guide_name or rng.choice(["Ari", "Soren", "Mika", "Jo"]),
        place=args.place or rng.choice(
            ["the blue mountain trail", "the whispering valley", "the red cliff path"]
        ),
        destination=args.destination or "the old hill shrine",
        keepsake=args.keepsake or "a little silver bell",
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
    StoryParams(hero_name="Luna", guide_name="Ari", seed=0),
    StoryParams(hero_name="Mira", guide_name="Soren", seed=1),
    StoryParams(hero_name="Nell", guide_name="Mika", seed=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mournful_bravery/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        print(asp.one_model(asp_program("#show mournful_bravery/0.")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
