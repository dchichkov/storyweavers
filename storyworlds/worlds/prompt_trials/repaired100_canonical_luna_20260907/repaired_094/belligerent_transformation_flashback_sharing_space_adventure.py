#!/usr/bin/env python3
"""
A small space-adventure storyworld about a belligerent asteroid bot, a
transformation, a flashback, and the sharing that saves a moon station.
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
import copy
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
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    region: str = ""
    carried_by: Optional[str] = None


@dataclass
class Setting:
    place: str
    hazard: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "World":
        clone = World(copy.deepcopy(self.setting))
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


SCENES = [
    {
        "place": "Lumen Moon Station",
        "hazard": "a meteor shower was marching toward the station's solar sails",
        "memory": "a lonely repair drone once shut its hatch because no one shared power with it",
        "resource": "the last bright power cell",
        "repair": "split the cell's charge between the station and the stranded bot",
        "ending": "the station lights blinked on while the bot's new blue beacon glowed beside them",
    },
    {
        "place": "the Ring of Comets",
        "hazard": "a comet tail was filling the navigation lane with glittering ice",
        "memory": "a frightened pilot had once survived by asking a whole crew to pass one small map from hand to hand",
        "resource": "one pocket of clear starlight",
        "repair": "share the clear route with every nearby ship",
        "ending": "ships sailed through the shining gap in a peaceful silver line",
    },
    {
        "place": "Aurora Dock",
        "hazard": "the dock's cooling fans were failing beneath a red-hot engine cloud",
        "memory": "a young robot had once learned that a cool corner was safer when friends made room",
        "resource": "the last ice capsule",
        "repair": "open the capsule so the dock and the bot could cool together",
        "ending": "frost feathered the windows, and everyone had a safe place to breathe",
    },
    {
        "place": "the Quiet Nebula Lab",
        "hazard": "a wave of purple dust was covering the lab's telescope mirrors",
        "memory": "an old explorer had once turned a broken signal into a welcome by answering it kindly",
        "resource": "the final clean signal beam",
        "repair": "aim the beam across the nebula for both the lab and the lost bot",
        "ending": "the mirrors cleared, and a friendly beam stitched the stars together",
    },
]


def build_world(params: "StoryParams") -> World:
    scene = SCENES[params.scene_index % len(SCENES)]
    setting = Setting(
        place=scene["place"],
        hazard=scene["hazard"],
        affordances={"share_power", "remember", "transform"},
    )
    world = World(setting)

    luna = world.add(Entity(
        id="luna",
        kind="character",
        type="girl",
        label=params.name,
        meters={"steps": 0.0, "shared_energy": 0.0},
        memes={"courage": 1.0, "curiosity": 1.0, "worry": 0.0, "trust": 0.0},
        region=setting.place,
    ))
    nova = world.add(Entity(
        id="nova",
        kind="character",
        type="helper",
        label=params.helper,
        meters={"fuel": 1.0},
        memes={"patience": 1.0, "kindness": 1.0},
        region=setting.place,
    ))
    bot = world.add(Entity(
        id="bot",
        kind="character",
        type="robot",
        label="the belligerent asteroid bot",
        meters={"metal_charge": 1.0, "distance": 0.0},
        memes={"anger": 1.0, "fear": 0.0, "trust": 0.0},
        region="the shadowed crater",
    ))
    cell = world.add(Entity(
        id="cell",
        kind="tool",
        type="power_cell",
        label=scene["resource"],
        meters={"charge": 1.0},
        memes={"useful": 1.0},
        region=setting.place,
    ))

    world.facts.update(
        scene=scene,
        luna=luna,
        helper=nova,
        bot=bot,
        cell=cell,
        transformation="the bot's armor unfolded into a gentle rescue beacon",
        flashback=scene["memory"],
        shared=False,
        transformed=False,
        safe=False,
        lesson="Sharing a small resource can make room for trust and safety.",
    )
    return world


def propagate(world: World) -> None:
    bot: Entity = world.facts["bot"]
    luna: Entity = world.facts["luna"]
    if world.facts.get("shared") and not world.facts.get("transformed"):
        world.facts["transformed"] = True
        bot.memes["anger"] = 0.0
        bot.memes["fear"] = 0.0
        bot.memes["trust"] = 1.0
        bot.meters["metal_charge"] = 0.5
        luna.memes["trust"] += 1.0
    if world.facts.get("transformed") and not world.facts.get("safe"):
        world.facts["safe"] = True
        luna.memes["courage"] += 1.0
        luna.meters["shared_energy"] = 1.0


def tell(params: "StoryParams") -> World:
    world = build_world(params)
    scene = world.facts["scene"]
    luna: Entity = world.facts["luna"]
    nova: Entity = world.facts["helper"]
    bot: Entity = world.facts["bot"]
    cell: Entity = world.facts["cell"]

    openings = [
        f"{luna.label} piloted a tiny silver shuttle above {world.setting.place}.",
        f"At {world.setting.place}, {luna.label} watched the stars wheel past the window.",
        f"The adventure began when {luna.label} heard a hard clang beyond the moon station.",
        f"{luna.label} and {nova.label} were checking their supplies in orbit.",
    ]
    world.say(openings[params.route % len(openings)])
    world.say(f"Then {scene['hazard']}.")
    world.say(f"From a shadowed crater came {bot.label}, waving its metal arms and shouting, \"Keep away! This is mine!\"")
    bot.memes["anger"] += 1.0
    luna.memes["worry"] += 1.0
    world.para()

    world.say(f"{luna.label} floated closer, but the {bot.type} blocked the route. It was belligerent because its warning lights were fading.")
    world.say(f'"We do not have to fight," {luna.label} said. "{nova.label}, what can we share?"')
    world.say(f'"We have {cell.label}," {nova.label} replied. "A little help may reach all of us."')
    world.say(f"The words reminded {luna.label} of a flashback: {scene['memory']}.")
    world.say(f"She understood that the bot's loud anger was covering a quiet fear.")
    bot.memes["fear"] = 1.0
    world.para()

    world.say(f"{luna.label} held up {cell.label}. \"I will not take your power,\" she said. \"I will share it so we can all get home.\"")
    world.say(f"The bot hesitated. \"You would share with me?\" it asked.")
    world.say(f'"Yes," said {luna.label}. "{nova.label} can guide the current, and you can guide us through the crater."')
    world.say(f"Together they {scene['repair']}.")
    world.facts["shared"] = True
    cell.meters["charge"] = 0.5
    bot.region = world.setting.place
    propagate(world)
    world.say(f"The sharing caused a transformation: {world.facts['transformation']}.")
    world.say(f"The bot's voice softened. \"I thought everyone would leave me in the dark,\" it said.")
    world.say(f'"Not today," {nova.label} answered. "Space is wide enough for another friend."')
    world.para()

    world.say(f"The danger passed, and {scene['ending']}.")
    world.say(f"{luna.label} smiled at the transformed bot. The flashback had shown her an old truth, but sharing had made it real in the present.")
    world.say(f"She tucked the lesson into her captain's log: {world.facts['lesson']}")
    return world


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    return [
        f"Write a child-friendly Space Adventure at {world.setting.place} featuring a belligerent asteroid bot.",
        f"Use Transformation, Flashback, and Sharing to show how the danger of {scene['hazard']} is solved.",
        f"Tell how a young space captain shares {scene['resource']} and turns fear into trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scene = world.facts["scene"]
    luna: Entity = world.facts["luna"]
    bot: Entity = world.facts["bot"]
    return [
        QAItem(
            question=f"Why was {bot.label} belligerent?",
            answer=f"The bot acted belligerently because its power was fading and it feared being left alone in the danger caused by {scene['hazard']}.",
        ),
        QAItem(
            question=f"What did {luna.label} remember in the flashback?",
            answer=f"{luna.label} remembered that {scene['memory']}. The memory helped her see fear beneath the bot's angry behavior.",
        ),
        QAItem(
            question="What did the characters share?",
            answer=f"They shared {scene['resource']}. Sharing enough energy helped both the station and the stranded bot.",
        ),
        QAItem(
            question="What transformation happened?",
            answer=f"The bot stopped acting like an enemy and {world.facts['transformation']}. Its anger changed into trust.",
        ),
        QAItem(
            question="How did the adventure end?",
            answer=f"It ended when they {scene['repair']}, the danger passed, and {scene['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a meaningful change in shape, behavior, or condition.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a moment in a story that shows something that happened earlier.",
        ),
        QAItem(
            question="Why can sharing help during an adventure?",
            answer="Sharing can spread a useful resource, reduce loneliness, and help people solve a danger together.",
        ),
        QAItem(
            question="What does belligerent mean?",
            answer="Belligerent means acting ready to argue or fight, often because of anger or fear.",
        ),
        QAItem(
            question="What is a space station?",
            answer="A space station is a place built in space where people or machines can live, work, and conduct missions.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:8} ({entity.type:10}) region={entity.region!r} "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    scene_index: int = 0
    route: int = 0
    seed: Optional[int] = None


GIRL_NAMES = ["Luna", "Mira", "Zara", "Nia", "Ari", "Tala"]
BOY_NAMES = ["Leo", "Kai", "Orin", "Sam", "Theo", "Jules"]
HELPERS = ["Captain Sol", "Aunt Vega", "Uncle Ray", "Pilot Noor", "Commander Bea"]


ASP_RULES = r"""
shared :- shared_power.
transformed :- shared, trust_gained.
safe :- transformed, hazard_passed.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("shared_power"),
        asp.fact("trust_gained"),
        asp.fact("hazard_passed"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Space Adventure about a belligerent bot, transformation, flashback, and sharing."
    )
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--helper")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, gender=gender, helper=helper)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
    program = asp_program("#show shared/0.\n#show transformed/0.\n#show safe/0.")
    model = asp.one_model(program)
    names = {symbol.name for symbol in model}
    expected = {"shared", "transformed", "safe"}
    if expected.issubset(names):
        sample = generate(StoryParams("Luna", "girl", "Captain Sol", 0, 0, 1))
        if "belligerent" in sample.story and "share" in sample.story.lower():
            print("OK: ASP/Python parity and story exercise passed.")
            return 0
    print("MISMATCH: ASP twin or generated story failed verification.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show shared/0.\n#show transformed/0.\n#show safe/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show shared/0.\n#show transformed/0.\n#show safe/0."))
        print("ASP atoms:", " ".join(sorted(symbol.name for symbol in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        count = len(SCENES)
        for index in range(count):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.scene_index = index
            params.route = index % 4
            params.seed = seed
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n) and attempt < max(30, args.n * 30):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.scene_index = seed % len(SCENES)
            params.route = (seed // len(SCENES)) % 4
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
