#!/usr/bin/env python3
"""
A small space-adventure storyworld about a cockeyed slipper, an empty supply
locker, and a flashback that helps a young astronaut repair a drifting shuttle.
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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""


@dataclass
class Setting:
    name: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


SCENES = [
    {
        "setting": "the moon-orbit shuttle Starling",
        "missing": "the emergency navigation chip",
        "alarm": "the guidance lights blinked in the wrong order",
        "sound": "BEEP-BEEP... KRRRSH!",
        "slipper": "a silver house slipper",
        "place": "the empty supply locker",
        "cause": "the chip had slipped behind the locker panel during a small engine jolt",
        "repair": "tightened the panel and returned the chip to the guidance console",
        "ending": "the Starling sailed straight toward the blue Earth",
    },
    {
        "setting": "the red-planet rover camp",
        "missing": "the star-map battery",
        "alarm": "the rover compass spun like a tiny planet",
        "sound": "WHIRR... CLANK!",
        "slipper": "a purple house slipper",
        "place": "the empty tool cupboard",
        "cause": "the battery had bounced beneath the cupboard when the rover crossed a ridge",
        "repair": "retrieved the battery with a magnet and secured the cupboard latch",
        "ending": "the rover headlights drew a bright path across the red dust",
    },
    {
        "setting": "the comet research station",
        "missing": "the rescue beacon",
        "alarm": "the station door pointed toward the comet instead of home",
        "sound": "PING... PING... WHOOSH!",
        "slipper": "a blue house slipper",
        "place": "the empty sleeping pod",
        "cause": "the beacon had rolled into the pod after a comet-tail tremor",
        "repair": "rolled the beacon back and fastened it inside a padded case",
        "ending": "the rescue signal twinkled beside the comet's silver tail",
    },
    {
        "setting": "the floating school satellite",
        "missing": "the robot's bright red fuse",
        "alarm": "the classroom robot marched backward into a wall",
        "sound": "DING... DING... ZZZT!",
        "slipper": "a green house slipper",
        "place": "the empty science drawer",
        "cause": "the fuse had jumped from the drawer when the satellite spun once",
        "repair": "found the fuse under the drawer rail and clipped it into the robot",
        "ending": "the robot waved while stars winked beyond the classroom glass",
    },
    {
        "setting": "the tiny asteroid observatory",
        "missing": "the telescope's moon lens",
        "alarm": "every crater looked upside down",
        "sound": "TAP-TAP... VOOOM!",
        "slipper": "an orange house slipper",
        "place": "the empty equipment rack",
        "cause": "the lens had slid behind the rack during a gentle docking bump",
        "repair": "used a soft brush to pull out the lens and fastened the rack",
        "ending": "the moon appeared round and calm above the asteroid",
    },
]


def build_world(params: "StoryParams") -> World:
    scene = SCENES[params.scene_index % len(SCENES)]
    world = World(Setting(scene["setting"], {"inspect", "repair", "remember"}))

    hero = world.add(Entity(
        "hero", "astronaut", params.name,
        meters={"steps": 0.0, "oxygen": 8.0},
        memes={"worry": 1.0, "curiosity": 1.0, "courage": 0.0},
        location="command deck",
    ))
    helper = world.add(Entity(
        "helper", "robot", params.helper,
        meters={"battery": 5.0},
        memes={"helpfulness": 1.0},
        location="command deck",
    ))
    slipper = world.add(Entity(
        "slipper", "object", scene["slipper"],
        meters={"drift": 1.0},
        memes={"mischief": 1.0},
        location=scene["place"],
    ))
    world.add(Entity(
        "ship", "vehicle", "the shuttle",
        meters={"course": 0.0, "hull_strength": 5.0},
        memes={"safety": 0.0},
        location=scene["setting"],
    ))

    world.facts.update(
        scene=scene,
        hero=hero,
        helper=helper,
        slipper=slipper,
        flashback_seen=False,
        sound_heard=False,
        clue_found=False,
        solved=False,
        lesson="A remembered detail can turn a frightening mystery into a careful repair.",
    )

    world.say(
        f"{params.name} was checking {scene['setting']} when {scene['alarm']}. "
        f"The missing item was {scene['missing']}."
    )
    world.say(f"{scene['sound']} The sound bounced through the cabin.")
    world.say(
        f"Near {scene['place']}, {params.name} found {scene['slipper']}. "
        f"It sat at a cockeyed angle, as if it had tried to point at the stars."
    )
    world.para()

    hero.memes["worry"] += 1.0
    world.say(
        f'"The locker is empty, but the ship is not," {params.helper} said. '
        f'"Let us inspect what moved."'
    )
    world.say(
        f'"I remember that sound," {params.name} replied. '
        f'"It happened just after the last little jolt."'
    )
    world.say(
        f"A flashback returned: the slipper had floated past {params.name}'s helmet "
        f"while the locker panel shivered."
    )
    world.facts["flashback_seen"] = True
    hero.memes["courage"] += 1.0
    world.say(
        f"{params.name} nudged the cockeyed slipper aside and noticed a narrow shadow "
        f"behind the locker."
    )
    world.para()

    world.say(
        f'"There!" cried {params.name}. "The {scene["missing"]} is behind the panel."'
    )
    world.say(
        f"{params.helper} held the locker steady while {params.name} reached carefully "
        f"into the narrow space. {scene['sound']} The loose panel answered with a tiny echo."
    )
    world.facts["sound_heard"] = True
    world.facts["clue_found"] = True
    hero.meters["steps"] += 3.0
    world.say(
        f"The flashback and the sound matched: {scene['cause']}. "
        f"No one had stolen anything."
    )
    world.para()

    world.say(
        f"Together they {scene['repair']}. The guidance lights settled into a steady glow."
    )
    world.facts["solved"] = True
    hero.memes["worry"] = 0.0
    hero.memes["courage"] += 1.0
    world.say(
        f'"An empty space can hide a full story," {params.name} said. '
        f'"We only needed to remember and listen."'
    )
    world.say(f"{scene['ending']}.")
    return world


@dataclass
class StoryParams:
    name: str
    helper: str
    scene_index: int = 0
    route: int = 0
    seed: Optional[int] = None


NAMES = ["Luna", "Mara", "Sol", "Niko", "Ari", "Tavi"]
HELPERS = ["Orbit", "Pip", "Nova", "Comet", "Beep"]


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    return [
        f"Write a child-friendly Space Adventure at {world.setting.name} involving a cockeyed slipper and an empty place.",
        f"Use a Flashback and Sound Effects to explain why {scene['missing']} vanished.",
        "Show a young astronaut solving a frightening problem through memory, careful listening, and teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scene = world.facts["scene"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            question=f"What was {hero.label} trying to find?",
            answer=f"{hero.label} was trying to find {scene['missing']} so the spacecraft could work safely again.",
        ),
        QAItem(
            question="How did the flashback help solve the problem?",
            answer=f"The flashback reminded the astronaut that the item moved just after a small jolt, which supported the explanation that {scene['cause']}.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} held the locker steady while the astronaut searched carefully behind the panel.",
        ),
        QAItem(
            question="What did the cockeyed slipper reveal?",
            answer=f"The cockeyed slipper showed that something had drifted near {scene['place']}, so the astronaut inspected that area instead of blaming anyone.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"They repaired the problem, and {scene['ending']}. The empty space was no longer mysterious.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a remembered moment from earlier that helps explain what is happening now.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are written or performed sounds, such as BEEP-BEEP or WHOOSH, that make an action vivid.",
        ),
        QAItem(
            question="Why can an empty space be a clue?",
            answer="An empty space can be a clue because it may show where an object was moved, hidden, or knocked away.",
        ),
        QAItem(
            question="What is a slipper?",
            answer="A slipper is a soft shoe usually worn indoors.",
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
        lines.append(
            f"  {entity.id:8} ({entity.kind:9}) location={entity.location!r} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
moved_item :- flashback_seen, sound_heard, clue_found.
solved :- moved_item.
safe_course :- solved.
"""


def asp_facts(world: World) -> str:
    import asp
    names = []
    if world.facts.get("flashback_seen"):
        names.append(asp.fact("flashback_seen"))
    if world.facts.get("sound_heard"):
        names.append(asp.fact("sound_heard"))
    if world.facts.get("clue_found"):
        names.append(asp.fact("clue_found"))
    return "\n".join(names)


def asp_program(world: World, shown: str = "#show solved/0.\n#show safe_course/0.") -> str:
    return f"{asp_facts(world)}\n{ASP_RULES}\n{shown}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A Space Adventure about memory, sound, and a cockeyed slipper.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
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
        helper=args.helper or rng.choice(HELPERS),
        scene_index=rng.randrange(len(SCENES)),
        route=rng.randrange(4),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    if not world.facts.get("solved"):
        raise StoryError("The story must resolve the spacecraft problem.")
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


def verify() -> int:
    import asp
    params = StoryParams(name="Luna", helper="Orbit", scene_index=0, seed=7)
    sample = generate(params)
    world = sample.world
    if world is None or not world.facts.get("solved"):
        print("MISMATCH: Python story did not solve the problem.")
        return 1
    model = asp.one_model(asp_program(world))
    atoms = {symbol.name for symbol in model}
    if "solved" not in atoms or "safe_course" not in atoms:
        print("MISMATCH: ASP twin did not derive the solved state.")
        return 1
    print("OK: Python and ASP states agree; generated story is resolved.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        params = StoryParams(name="Luna", helper="Orbit")
        print(asp_program(build_world(params)))
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        import asp
        params = StoryParams(name="Luna", helper="Orbit")
        model = asp.one_model(asp_program(build_world(params)))
        print("ASP atoms:", " ".join(sorted(symbol.name for symbol in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(SCENES) if args.all else max(1, args.n)
    samples: list[StorySample] = []
    for index in range(count):
        seed = base_seed + index
        rng = random.Random(seed)
        params = resolve_params(args, rng)
        params.seed = seed
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
