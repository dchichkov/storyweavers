#!/usr/bin/env python3
"""
A small space-adventure storyworld about sleaze, muddo, and a protective choice
that leads to a happy ending.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Astronaut:
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"oxygen": 1.0, "distance_to_beacon": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"protective": 0.0, "courage": 0.0, "trust": 0.0}
    )
    inventory: list[str] = field(default_factory=list)


@dataclass
class SpaceStation:
    name: str
    location: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"hull_safety": 1.0, "signal_strength": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"welcoming": 0.0, "hope": 0.0}
    )


@dataclass
class Muddo:
    name: str = "Muddo"
    kind: str = "small moon creature"
    safe: bool = False
    warmed: bool = False
    hidden: bool = False
    meters: dict[str, float] = field(
        default_factory=lambda: {"body_heat": 0.2, "distance_to_shelter": 1.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"fear": 1.0, "trust": 0.0, "happiness": 0.0}
    )


@dataclass
class StoryParams:
    hero_name: str = "Luna"
    companion_name: str = "Orin"
    station_name: str = "Starling Station"
    moon_name: str = "Vesper Moon"
    scenario_id: int = 0
    dialogue_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    opening: str
    danger: str
    sleaze_meaning: str
    clue: str
    action: str
    resolution: str
    lesson: str
    ending_image: str


SCENARIOS = (
    Scenario(
        opening="Luna and Orin were mapping the silver caves of Vesper Moon when a weak chirp came through their helmets.",
        danger="A dust storm was racing across the moon, and a tiny creature was stranded beside a broken beacon.",
        sleaze_meaning="the station's old warning screen called the storm sleaze, a word for a dirty, dangerous mess of dust",
        clue="the chirp repeated three times whenever the beacon light flickered",
        action="carried a heat lamp through the blowing dust while Orin guided the creature toward the rover",
        resolution="Luna wrapped the creature in a thermal blanket, repaired the beacon, and brought it safely to Starling Station",
        lesson="being protective means noticing someone who cannot protect themselves yet",
        ending_image="Muddo curled beside a warm window and watched the stars sparkle above the quiet moon",
    ),
    Scenario(
        opening="Near the rings of Vesper Moon, Luna piloted a small repair ship with Orin beside her.",
        danger="A loose cargo pod spun toward an unknown little passenger clinging to its silver handle.",
        sleaze_meaning="the sticky black grease on the pod was called sleaze by the mechanics because it made every repair slippery",
        clue="a tiny handprint appeared on the pod's clean observation window",
        action="held the ship steady while Orin used the rescue arm to lift the passenger away from the grease",
        resolution="They sealed the pod, washed the little traveler, and gave it a safe seat in the ship's warm cabin",
        lesson="careful protection can turn a frightening machine into a safe path home",
        ending_image="Muddo pressed one clean paw to the cabin glass as the repaired pod drifted peacefully behind them",
    ),
    Scenario(
        opening="Luna and Orin were collecting moon crystals for Starling Station when they found a blinking trail in the dust.",
        danger="The trail led to Muddo, who had hidden beneath a rock while a sharp meteor shower crossed the sky.",
        sleaze_meaning="the dark dust left by the meteors looked like sleaze, a grimy coat that covered the moon's bright stones",
        clue="Muddo copied Luna's gentle three-tap signal from beneath the rock",
        action="placed the rover between Muddo and the meteors while Orin opened the rover's shelter hatch",
        resolution="The shower passed, and Luna carried Muddo into the shelter where warm soup and soft lights were waiting",
        lesson="a protective friend makes room for trust even during a noisy storm",
        ending_image="When the sky cleared, Muddo rode home beside Luna beneath a ribbon of blue stars",
    ),
)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, key: str, entity: object) -> object:
        self.entities[key] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(group) for group in self.paragraphs if group)


def tell(params: StoryParams) -> World:
    if params.scenario_id < 0 or params.scenario_id >= len(SCENARIOS):
        raise StoryError("scenario_id must select an existing space adventure.")
    if params.hero_name.strip().lower() == params.companion_name.strip().lower():
        raise StoryError("hero_name and companion_name must be different astronauts.")

    world = World(params)
    hero = world.add(
        "hero",
        Astronaut(
            name=params.hero_name,
            role="protective pilot",
            inventory=["thermal blanket", "rescue beacon"],
        ),
    )
    companion = world.add(
        "companion",
        Astronaut(
            name=params.companion_name,
            role="signal engineer",
            inventory=["repair kit", "warm soup"],
        ),
    )
    station = world.add(
        "station",
        SpaceStation(name=params.station_name, location="in orbit above Vesper Moon"),
    )
    muddo = world.add("muddo", Muddo())
    scenario = SCENARIOS[params.scenario_id]

    hero.memes["protective"] = 1.0
    companion.memes["trust"] = 0.5

    world.say(scenario.opening)
    world.say(
        f"{params.station_name} shone above them like a small lantern, while "
        f"{scenario.sleaze_meaning}."
    )

    world.para()
    world.say(scenario.danger)
    world.say(
        f"Luna whispered, 'We cannot leave Muddo there.' "
        f"Orin answered, 'Then we will make a safe way back.'"
    )
    world.say(
        f"The first clue was simple: {scenario.clue}. "
        "It told the astronauts that the frightened traveler was still listening."
    )
    world.events.extend(["signal_heard", "danger_noticed", "clue_understood"])

    world.para()
    world.say(
        f"Luna chose to be protective. She {scenario.action}, while Orin kept the "
        "rescue signal bright."
    )
    world.say(
        f"'Stay close, Muddo,' Luna said. 'The stars are wide, but you are not alone.'"
    )
    world.say(
        f"'I see you,' Orin called. 'Follow the warm light.'"
    )
    world.say(
        "Muddo followed the voices. Its fear loosened when the astronauts kept their promise."
    )
    world.events.extend(["protective_choice", "rescue_started", "trust_grew"])

    muddo.safe = True
    muddo.warmed = True
    muddo.hidden = False
    muddo.meters["body_heat"] = 1.0
    muddo.meters["distance_to_shelter"] = 0.0
    muddo.memes["fear"] = 0.0
    muddo.memes["trust"] = 1.0
    muddo.memes["happiness"] = 1.0

    hero.meters["oxygen"] = 0.72
    hero.meters["distance_to_beacon"] = 0.0
    hero.memes["courage"] = 1.0
    companion.memes["trust"] = 1.0
    station.meters["signal_strength"] = 1.0
    station.memes["welcoming"] = 1.0
    station.memes["hope"] = 1.0

    world.say(scenario.resolution)
    world.events.extend(["muddo_safe", "shelter_reached", "happy_ending"])

    world.para()
    endings = (
        f"At last, everyone could breathe easily. {scenario.ending_image}.",
        f"The rescue lights faded, but the happy ending remained: {scenario.ending_image}.",
        f"Luna smiled through her helmet. {scenario.ending_image}.",
        f"Orin logged the mission as a success. {scenario.ending_image}.",
    )
    world.say(endings[params.ending_mode % len(endings)])
    world.say(
        f"Luna understood that {scenario.lesson}. "
        "The smallest traveler had found a safe place among the stars."
    )

    world.facts.update(
        hero=hero,
        companion=companion,
        station=station,
        muddo=muddo,
        scenario=scenario,
        danger=scenario.danger,
        clue=scenario.clue,
        action=scenario.action,
        resolution=scenario.resolution,
        lesson=scenario.lesson,
        ending_image=scenario.ending_image,
        sleaze=scenario.sleaze_meaning,
        protective=True,
        happy_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Astronaut = f["hero"]
    muddo: Muddo = f["muddo"]
    return [
        f"Write a Space Adventure about {hero.name} protecting {muddo.name} from this danger: {f['danger']}",
        f"Use this clue to turn the rescue: {f['clue']}",
        f"End with a Happy Ending in which {muddo.name} is safe and trusted.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Astronaut = f["hero"]
    companion: Astronaut = f["companion"]
    muddo: Muddo = f["muddo"]
    return [
        QAItem(
            question=f"What danger did {hero.name} and {companion.name} discover?",
            answer=f"They discovered that {f['danger']}",
        ),
        QAItem(
            question=f"What clue helped the astronauts understand {muddo.name}?",
            answer=f"The clue was that {f['clue']}. It showed that {muddo.name} was listening and needed help.",
        ),
        QAItem(
            question=f"How did {hero.name} protect {muddo.name}?",
            answer=f"{hero.name} {f['action']}. The astronauts worked together so {muddo.name} could reach shelter safely.",
        ),
        QAItem(
            question="What happened at the end of the space adventure?",
            answer=f"{f['resolution']}. The Happy Ending was shown when {f['ending_image']}.",
        ),
        QAItem(
            question=f"What did {hero.name} learn?",
            answer=f"{hero.name} learned that {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does protective mean?",
            answer="Protective means trying to keep another person or creature safe from harm.",
        ),
        QAItem(
            question="What is a space station?",
            answer="A space station is a place built in space where travelers can live, work, repair equipment, and rest.",
        ),
        QAItem(
            question="What is a beacon?",
            answer="A beacon is a light or signal that helps someone find a place or ask for help.",
        ),
        QAItem(
            question="What does sleaze mean in this story?",
            answer="In this story, sleaze is a grimy or unpleasant substance connected with a dangerous space problem.",
        ),
        QAItem(
            question="What is Muddo?",
            answer="Muddo is a small moon creature who becomes safe, warm, trusting, and happy after the astronauts rescue it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
safe(M) :- muddo(M), rescued(M), warm(M).
happy(M) :- safe(M), trusted(M).
protective(H) :- hero(H), chose_protection(H).
rescue_success(H,M) :- protective(H), muddo(M), safe(M).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero", "luna"),
            asp.fact("muddo", "muddo"),
            asp.fact("rescued", "muddo"),
            asp.fact("warm", "muddo"),
            asp.fact("trusted", "muddo"),
            asp.fact("chose_protection", "luna"),
        ]
    )


def asp_program(show: str = "#show safe/1. #show happy/1. #show protective/1. #show rescue_success/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space Adventure storyworld with sleaze, Muddo, and a protective Happy Ending."
    )
    parser.add_argument("--hero-name", default=None)
    parser.add_argument("--companion-name", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_names = ["Luna", "Nova", "Ari", "Sol"]
    companion_names = ["Orin", "Pax", "Mira", "Tavi"]
    hero = args.hero_name or rng.choice(hero_names)
    companion = args.companion_name or rng.choice(
        [name for name in companion_names if name.lower() != hero.lower()]
    )
    return StoryParams(
        hero_name=hero,
        companion_name=companion,
        station_name=rng.choice(["Starling Station", "Comet Harbor", "Aurora Dock"]),
        moon_name=rng.choice(["Vesper Moon", "Blueglass Moon", "Morrow Moon"]),
        scenario_id=rng.randrange(len(SCENARIOS)),
        dialogue_mode=rng.randrange(3),
        ending_mode=rng.randrange(4),
        seed=args.seed,
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
    hero: Astronaut = world.entities["hero"]
    companion: Astronaut = world.entities["companion"]
    muddo: Muddo = world.entities["muddo"]
    station: SpaceStation = world.entities["station"]
    return "\n".join(
        [
            "--- world trace ---",
            f"station: {station.name} location={station.location} meters={station.meters} memes={station.memes}",
            f"hero: {hero.name} role={hero.role} meters={hero.meters} memes={hero.memes}",
            f"companion: {companion.name} role={companion.role} meters={companion.meters} memes={companion.memes}",
            f"muddo: safe={muddo.safe} warmed={muddo.warmed} hidden={muddo.hidden} meters={muddo.meters} memes={muddo.memes}",
            f"events: {world.events}",
        ]
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
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    model = asp.one_model(asp_program())
    required = {
        ("muddo",): "safe",
    }
    if ("muddo",) not in set(asp.atoms(model, "safe")):
        print("MISMATCH: ASP did not derive that Muddo is safe.")
        return 1
    if ("muddo",) not in set(asp.atoms(model, "happy")):
        print("MISMATCH: ASP did not derive the Happy Ending.")
        return 1
    if ("luna", "muddo") not in set(asp.atoms(model, "rescue_success")):
        print("MISMATCH: ASP did not derive rescue success.")
        return 1

    sample = generate(StoryParams())
    if "Muddo" not in sample.story or "Happy Ending" not in sample.story:
        print("MISMATCH: generated story lacks required narrative facts.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            raise SystemExit(1)
        model = asp.one_model(asp_program())
        print("safe:", asp.atoms(model, "safe"))
        print("happy:", asp.atoms(model, "happy"))
        print("protective:", asp.atoms(model, "protective"))
        print("rescue_success:", asp.atoms(model, "rescue_success"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(hero_name="Luna", companion_name="Orin", scenario_id=0),
            StoryParams(hero_name="Nova", companion_name="Pax", scenario_id=1),
            StoryParams(hero_name="Ari", companion_name="Mira", scenario_id=2),
        ]
    else:
        params_list = [
            resolve_params(args, random.Random(base_seed + index))
            for index in range(max(1, args.n))
        ]

    samples = [generate(params) for params in params_list]

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
