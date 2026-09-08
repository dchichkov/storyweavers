#!/usr/bin/env python3
"""
A small superhero storyworld about safe motion, a raven, and a difficult choice.
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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def pronoun(self) -> str:
        if self.kind in {"girl", "woman"}:
            return "she"
        if self.kind in {"boy", "man"}:
            return "he"
        return "it"


@dataclass
class Setting:
    name: str
    hazard: str
    safe_place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    history: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SCENES = [
    {
        "setting": "the rooftop garden above Brightbridge",
        "hazard": "a storm had loosened the garden's glass windmill",
        "safe_place": "the sturdy stairwell",
        "object": "the signal crystal",
        "motion": "a spinning metal vane",
        "raven_clue": "black feathers caught on the windmill's axle",
        "cause": "the raven had carried a bright ribbon into the windmill, and the ribbon pulled the crystal loose",
        "repair": "shut down the windmill, guided the raven away with seeds, and fastened the crystal to a lower bracket",
        "image": "the repaired crystal glowed softly while the raven watched from a dry railing",
    },
    {
        "setting": "the sky-tram platform over Harbor City",
        "hazard": "a runaway maintenance cart was rolling toward the edge",
        "safe_place": "the marked rescue platform",
        "object": "the emergency beacon",
        "motion": "a cart with one flashing wheel",
        "raven_clue": "a raven's silver tag was caught in the cart's brake cord",
        "cause": "the raven had tugged the shiny tag free, and the cord released the cart's brake",
        "repair": "blocked the track with a safety wedge and freed the tag without stepping onto the moving rail",
        "image": "the beacon blinked above the stopped cart as the raven flew safely toward the harbor tower",
    },
    {
        "setting": "the moonlit plaza beside the hero academy",
        "hazard": "a training drone was zigzagging through the crowd",
        "safe_place": "the quiet fountain steps",
        "object": "the blue rescue badge",
        "motion": "a fast, wobbling drone",
        "raven_clue": "a raven feather rested inside the drone's open fan guard",
        "cause": "the raven had brushed the drone while chasing a ribbon, and the loose feather made its fan wobble",
        "repair": "called the drone to a landing pad, kept everyone still, and removed the feather with a long-handled tool",
        "image": "the blue badge shone on the landing pad while the raven perched beyond the safety line",
    },
    {
        "setting": "the old clock tower in Silver Square",
        "hazard": "the giant minute hand was swinging below its loose hinge",
        "safe_place": "the protected clock room",
        "object": "the hero alarm bell",
        "motion": "a heavy golden hand",
        "raven_clue": "a raven's red thread was wrapped around the hinge",
        "cause": "the raven had pulled a bright thread through the open clock face, and the thread jammed the hinge",
        "repair": "stopped the clock, cleared the room, and loosened the thread from the protected side",
        "image": "the alarm bell rang once as the clock hand began its steady, safe motion",
    },
    {
        "setting": "the river rescue dock",
        "hazard": "a motorboat was circling without a pilot",
        "safe_place": "the high dock behind the yellow rail",
        "object": "the rescue flare",
        "motion": "a looping motorboat",
        "raven_clue": "a raven's bright button lay beside the loose throttle cord",
        "cause": "the raven had dropped the button into the throttle, locking it forward",
        "repair": "cut the engine from the dock panel and used a boat hook to pull the craft toward the quiet bank",
        "image": "the rescue flare stood ready while the raven shook river drops from its wings",
    },
]


def make_world(params: "StoryParams") -> World:
    scene = SCENES[params.scene_index % len(SCENES)]
    setting = Setting(
        name=scene["setting"],
        hazard=scene["hazard"],
        safe_place=scene["safe_place"],
        affords={"observe", "warn", "slow", "rescue"},
    )
    world = World(setting)
    hero = world.add(
        Entity(
            id="hero",
            kind=params.gender,
            label=params.name,
            location=setting.name,
            meters={"distance": 0.0, "safe_motion": 0.0},
            memes={"courage": 1.0, "worry": 0.0, "judgment": 0.0, "relief": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="adult",
            label=params.helper,
            location=setting.name,
            meters={"distance": 0.0},
            memes={"patience": 1.0, "trust": 1.0},
        )
    )
    raven = world.add(
        Entity(
            id="raven",
            kind="bird",
            label="the raven",
            location=setting.name,
            meters={"wingbeats": 1.0},
            memes={"curiosity": 1.0, "startled": 0.0},
        )
    )
    world.add(
        Entity(
            id="hazard",
            kind="machine",
            label=scene["motion"],
            location=setting.name,
            meters={"motion": 1.0},
            memes={"danger": 1.0},
        )
    )
    world.facts.update(
        scene=scene,
        hero=hero,
        helper=helper,
        raven=raven,
        object=scene["object"],
        tension=True,
        warned=False,
        safe=True,
        conflict_resolved=False,
        lesson="Brave heroes do not rush toward danger; they make motion safe before they move.",
    )
    return world


def validate(world: World) -> None:
    if not world.facts.get("safe"):
        raise StoryError("The story cannot resolve because the rescue is not safe.")
    if not world.facts.get("warned"):
        raise StoryError("The hero must warn others before approaching the moving hazard.")
    if not world.facts.get("conflict_resolved"):
        raise StoryError("The central conflict has not been resolved.")
    hero: Entity = world.facts["hero"]
    if hero.memes.get("judgment", 0) < 1:
        raise StoryError("The hero needs a careful decision before the ending.")


def tell(params: "StoryParams") -> World:
    world = make_world(params)
    scene = world.facts["scene"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    raven: Entity = world.facts["raven"]

    world.say(
        f"{hero.label} was the newest superhero in {world.setting.name}, where every rescue began with a careful look."
    )
    world.say(
        f"Then {scene['hazard']}. The {scene['object']} was needed, but rushing toward danger could make the trouble worse."
    )
    world.say(
        f"The {raven.label} fluttered above {scene['motion']}, and {scene['raven_clue']}."
    )
    world.para()

    hero.memes["worry"] += 1
    world.say(f'"I can stop it!" {hero.label} said, taking one quick step.')
    world.say(
        f'"Not yet," {helper.label} replied. "First make the motion safe. A superhero protects people before chasing a prize."'
    )
    world.say(
        f"{hero.label} looked again, noticed {scene['raven_clue']}, and raised a hand to warn everyone away from the hazard."
    )
    world.facts["warned"] = True
    hero.memes["judgment"] += 1
    hero.meters["safe_motion"] += 1
    world.para()

    world.say(
        f"The conflict became clear: {scene['cause']}. The raven was frightened, and the machine was still moving."
    )
    world.say(
        f'"Stay behind the line, little friend," {hero.label} called to the raven. "We will solve this without frightening you."'
    )
    world.say(
        f'"And we will use the calm plan," {helper.label} answered. "Watch, slow, then rescue."'
    )
    world.say(
        f"{hero.label} followed the plan: {scene['repair']}."
    )
    hero.meters["safe_motion"] += 1
    raven.memes["startled"] = 0
    world.facts["tension"] = False
    world.facts["conflict_resolved"] = True
    hero.memes["relief"] += 1
    world.para()

    world.say(
        f"When the danger stopped, {scene['image']}. {hero.label} had saved the day without turning courage into a careless rush."
    )
    validate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    return [
        f"Write a superhero story in {world.setting.name} where safe motion matters during {scene['hazard']}.",
        f"Create a cautionary adventure with a raven, a moving hazard, and dialogue that changes the hero's decision.",
        f"Tell a child-friendly conflict story in which a superhero rescues the {scene['object']} by slowing down instead of rushing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scene = world.facts["scene"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            question=f"What danger did {hero.label} face?",
            answer=f"{hero.label} faced {scene['hazard']}. The moving hazard threatened the {scene['object']}.",
        ),
        QAItem(
            question=f"Why did {helper.label} tell {hero.label} not to rush?",
            answer=f"{helper.label} knew that rushing could make the moving danger worse. The hero needed to warn people and make the motion safe first.",
        ),
        QAItem(
            question="How was the raven connected to the problem?",
            answer=f"The raven was connected because {scene['cause']}. It was part of the accident, not a villain.",
        ),
        QAItem(
            question="How did the hero solve the conflict?",
            answer=f"The hero solved it by warning everyone, staying behind a safe boundary, and then {scene['repair']}.",
        ),
        QAItem(
            question="What cautionary lesson did the hero learn?",
            answer=world.facts["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does safe motion mean?",
            answer="Safe motion means moving carefully, checking for danger, and keeping people away from anything that could strike or crush them.",
        ),
        QAItem(
            question="What is a raven?",
            answer="A raven is a clever black bird with strong wings and a loud call.",
        ),
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story shows a danger or mistake and teaches readers how to make a wiser choice.",
        ),
        QAItem(
            question="Why is dialogue useful in a story?",
            answer="Dialogue lets characters share information and advice, so their words can change what someone decides or does.",
        ),
        QAItem(
            question="What makes someone a superhero?",
            answer="A superhero uses courage and special skills to help others, while also taking responsibility for safety.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:8} ({entity.kind:7}) location={entity.location!r} "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  facts: {world.facts}")
    lines.append("  history:")
    lines.extend(f"    - {line}" for line in world.history)
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    scene_index: int = 0
    route: int = 0
    seed: Optional[int] = None


GIRL_NAMES = ["Luna", "Mira", "Zoe", "Nia", "Tara", "Aya"]
BOY_NAMES = ["Leo", "Kai", "Milo", "Ezra", "Noah", "Jude"]
HELPERS = ["Captain Vale", "Aunt Sol", "Coach Mira", "Uncle Reed", "Professor May"]


ASP_RULES = r"""
safe_rescue :- warned, safe_motion(2), not danger_active.
danger_active :- moving_hazard, not conflict_resolved.
safe_motion(2) :- careful_step, safe_motion(1).
safe_motion(1) :- warned.
"""


def asp_facts(world: Optional[World] = None) -> str:
    import asp

    lines = [
        asp.fact("warned"),
        asp.fact("careful_step"),
        asp.fact("safe_motion", 1),
        asp.fact("safe_motion", 2),
    ]
    if world is not None and not world.facts.get("tension", True):
        lines.append(asp.fact("conflict_resolved"))
    else:
        lines.append(asp.fact("moving_hazard"))
    return "\n".join(lines)


def asp_program(world: Optional[World] = None, show: str = "") -> str:
    return f"{asp_facts(world)}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about safe motion, a raven, and careful courage."
    )
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--helper")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return StoryParams(
        name=args.name or rng.choice(names),
        gender=gender,
        helper=args.helper or rng.choice(HELPERS),
        scene_index=rng.randrange(len(SCENES)),
        route=rng.randrange(4),
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


def asp_verify() -> int:
    import asp

    world = tell(
        StoryParams(
            name="Luna",
            gender="girl",
            helper="Captain Vale",
            scene_index=0,
            seed=1,
        )
    )
    model = asp.one_model(
        asp_program(
            world,
            "#show safe_rescue/0.\n#show danger_active/0.\n#show conflict_resolved/0.",
        )
    )
    names = {symbol.name for symbol in model}
    if "safe_rescue" not in names:
        print("MISMATCH: ASP did not derive safe_rescue.")
        return 1
    if "danger_active" in names:
        print("MISMATCH: ASP still reports an active danger.")
        return 1
    if "conflict_resolved" not in names:
        print("MISMATCH: ASP did not preserve the resolved conflict.")
        return 1
    for index in range(len(SCENES)):
        params = StoryParams(
            name="Luna",
            gender="girl",
            helper="Captain Vale",
            scene_index=index,
            seed=index,
        )
        sample = generate(params)
        if not sample.story or "raven" not in sample.story:
            print("MISMATCH: generated story failed its required domain check.")
            return 1
    print("OK: Python and ASP agree that careful motion resolves the conflict safely.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show safe_rescue/0.\n#show danger_active/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(show="#show safe_rescue/0.\n#show danger_active/0.")
        )
        print("ASP atoms:", " ".join(sorted(str(symbol) for symbol in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        count = len(SCENES)
    else:
        count = max(1, args.n)

    seen: set[str] = set()
    attempt = 0
    while len(samples) < count:
        seed = base_seed + attempt
        attempt += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        if args.all:
            params.scene_index = len(samples) % len(SCENES)
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
        if attempt > max(100, count * 20):
            break

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
