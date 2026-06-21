#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lawner_ten_outlandish_dialogue_teamwork_transformation_space.py
===========================================================================================

A standalone storyworld for a tiny Space Adventure domain built from the seed
words "lawner", "ten", and "outlandish", with Dialogue, Teamwork, and
Transformation at its core.

Premise
-------
A child captain and a friend care for a space garden with the help of ten
small "lawner" robots. When an outlandish obstacle blocks the garden, the ten
lawners transform together into the one shape that truly fits the problem.
Because the crew talks, plans, and works as a team, the garden changes from
troubled to bright and blooming.

Run it
------
python storyworlds/worlds/gpt-5.4/lawner_ten_outlandish_dialogue_teamwork_transformation_space.py
python storyworlds/worlds/gpt-5.4/lawner_ten_outlandish_dialogue_teamwork_transformation_space.py --obstacle crystal_drift --transform fan_wing
python storyworlds/worlds/gpt-5.4/lawner_ten_outlandish_dialogue_teamwork_transformation_space.py --obstacle vine_loop --transform bridge_line
python storyworlds/worlds/gpt-5.4/lawner_ten_outlandish_dialogue_teamwork_transformation_space.py --all
python storyworlds/worlds/gpt-5.4/lawner_ten_outlandish_dialogue_teamwork_transformation_space.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/lawner_ten_outlandish_dialogue_teamwork_transformation_space.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    view: str
    floor: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    need: str
    bloom: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    blocks: str
    solved_by: str
    threat: str
    aftermath: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transform:
    id: str
    label: str
    phrase: str
    ability: str
    move: str
    help_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "dome": Setting(
        id="dome",
        place="the moon-glass garden dome",
        view="Beyond the clear roof, rings of blue Saturn light floated past.",
        floor="The silver floor held neat rows of soft space grass and flower beds.",
        tags={"space_garden", "space"},
    ),
    "deck": Setting(
        id="deck",
        place="the starship's green deck",
        view="Past the wide window, stars streamed by like tiny sparks.",
        floor="The deck had long planting trays, warm lamps, and a path of humming tiles.",
        tags={"space_garden", "space"},
    ),
    "crater": Setting(
        id="crater",
        place="the little crater greenhouse",
        view="Outside the round walls, the dusty moon looked quiet and far away.",
        floor="Inside, bright pipes fed water under beds of moss and moonflowers.",
        tags={"space_garden", "space"},
    ),
}

PLANTS = {
    "moonlily": Plant(
        id="moonlily",
        label="moonlilies",
        phrase="a bed of moonlilies",
        need="fresh water",
        bloom="opened silver petals that shone like little spoons of light",
        tags={"plants", "flowers"},
    ),
    "comet_moss": Plant(
        id="comet_moss",
        label="comet moss",
        phrase="a patch of comet moss",
        need="clear air and light",
        bloom="puffed up into a soft green cloud with sparkly tips",
        tags={"plants", "moss"},
    ),
    "rocket_tulip": Plant(
        id="rocket_tulip",
        label="rocket tulips",
        phrase="a row of rocket tulips",
        need="a clear path for pollen drones",
        bloom="popped open in bright red cups that pointed toward the ceiling",
        tags={"plants", "flowers"},
    ),
}

OBSTACLES = {
    "vine_loop": Obstacle(
        id="vine_loop",
        label="outlandish vine loop",
        phrase="an outlandish loop of jumping vine",
        blocks="the watering rail",
        solved_by="clip",
        threat="Without the rail, the plants would stay thirsty.",
        aftermath="The cut vines curled into a sleepy heap beside the path.",
        tags={"vine", "problem"},
    ),
    "crystal_drift": Obstacle(
        id="crystal_drift",
        label="outlandish crystal drift",
        phrase="an outlandish drift of floating crystal dust",
        blocks="the grow-lamps",
        solved_by="fan",
        threat="Without the lamps, the garden would dim and droop.",
        aftermath="The glittering dust sailed away and the lamps shone clear again.",
        tags={"crystal", "problem"},
    ),
    "gap_ripple": Obstacle(
        id="gap_ripple",
        label="outlandish floor gap",
        phrase="an outlandish ripple where three floor tiles had folded apart",
        blocks="the pollen path",
        solved_by="bridge",
        threat="Without the path, the tiny pollen drones could not reach the flowers.",
        aftermath="The path lay smooth again, and the little drones zipped across safely.",
        tags={"bridge", "problem"},
    ),
}

TRANSFORMS = {
    "cutter_crown": Transform(
        id="cutter_crown",
        label="cutter crown",
        phrase="a spinning cutter crown",
        ability="clip",
        move="snipped the wild vine into soft pieces",
        help_text="Their tiny trim-arms were perfect for clipping plants without hurting the flowers.",
        tags={"transform", "clip"},
    ),
    "fan_wing": Transform(
        id="fan_wing",
        label="fan wing",
        phrase="a wide fan wing",
        ability="fan",
        move="blew the crystal dust in one shining stream toward the air vent",
        help_text="Their joined fans could move the dusty cloud all at once.",
        tags={"transform", "fan"},
    ),
    "bridge_line": Transform(
        id="bridge_line",
        label="bridge line",
        phrase="a bright bridge line",
        ability="bridge",
        move="locked wheel to wheel and made a safe little road across the gap",
        help_text="Their strong linked frames could hold still while the drones crossed over.",
        tags={"transform", "bridge"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    plant: str
    obstacle: str
    transform: str
    captain: str
    captain_gender: str
    friend: str
    friend_gender: str
    guide: str
    guide_gender: str
    seed: Optional[int] = None


CAPTAIN_NAMES = {
    "girl": ["Mira", "Zuri", "Lina", "Nova", "Tess", "Ava"],
    "boy": ["Leo", "Finn", "Milo", "Arin", "Theo", "Max"],
}
FRIEND_NAMES = {
    "girl": ["Pia", "Nora", "Skye", "Ivy", "Kira", "June"],
    "boy": ["Bo", "Rex", "Owen", "Kai", "Jude", "Nico"],
}
GUIDE_NAMES = {
    "girl": ["Captain Sol", "Engineer Mae", "Guide Luma"],
    "boy": ["Captain Orion", "Engineer Pax", "Guide Renn"],
}


def valid_combo(obstacle_id: str, transform_id: str) -> bool:
    return (
        obstacle_id in OBSTACLES
        and transform_id in TRANSFORMS
        and OBSTACLES[obstacle_id].solved_by == TRANSFORMS[transform_id].ability
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for plant_id in PLANTS:
            for obstacle_id in OBSTACLES:
                for transform_id in TRANSFORMS:
                    if valid_combo(obstacle_id, transform_id):
                        combos.append((setting_id, plant_id, obstacle_id, transform_id))
    return combos


def explain_rejection(obstacle_id: str, transform_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    transform = TRANSFORMS[transform_id]
    return (
        f"(No story: {transform.label} solves '{transform.ability}' problems, but "
        f"{obstacle.label} needs '{obstacle.solved_by}'. The transformation must "
        f"fit the obstacle in a sensible way.)"
    )


def tell(
    setting: Setting,
    plant: Plant,
    obstacle: Obstacle,
    transform: Transform,
    captain_name: str,
    captain_gender: str,
    friend_name: str,
    friend_gender: str,
    guide_name: str,
    guide_gender: str,
) -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide"))
    lawner_team = world.add(
        Entity(
            id="lawners",
            kind="thing",
            type="robots",
            label="ten lawners",
            phrase="ten little lawner robots",
            role="team",
        )
    )
    garden = world.add(Entity(id="garden", kind="thing", type="garden", label="garden"))

    captain.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    lawner_team.memes["ready"] += 1
    garden.meters["healthy"] += 1

    world.say(
        f"{captain_name} and {friend_name} hurried into {setting.place} at the start of their morning space adventure. "
        f"{setting.view} {setting.floor}"
    )
    world.say(
        f"Beside them rolled {lawner_team.phrase}, each one no bigger than a lunch box, with round wheels and blinking green eyes."
    )
    world.say(
        f'Today they were caring for {plant.phrase}. The plants needed {plant.need}, and the whole place smelled clean and bright.'
    )

    world.para()
    garden.meters["blocked"] += 1
    garden.meters["risk"] += 1
    captain.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"Then the crew stopped. An {obstacle.phrase} had twisted itself across {obstacle.blocks}. "
        f"{obstacle.threat}"
    )
    world.say(f'"That is very outlandish," said {friend_name}.')
    world.say(f'"And very bad timing," said {captain_name}, kneeling beside the nearest robot.')
    world.say(
        f'The ten lawners beeped together. "{obstacle.blocks.capitalize()} blocked," they chirped. "Please choose teamwork mode."'
    )

    world.para()
    world.say(
        f'{captain_name} put a hand on one smooth metal shell. "We can do this together," {captain.pronoun()} said.'
    )
    world.say(
        f'"What shape do we need?" asked {friend_name}.'
    )
    world.say(
        f'"{transform.label.capitalize()}," said {guide_name}. "{transform.help_text}"'
    )
    lawner_team.meters["transformed"] += 1
    lawner_team.attrs["mode"] = transform.id
    captain.memes["calm"] += 1
    friend.memes["calm"] += 1
    captain.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    lawner_team.memes["teamwork"] += 1
    world.say(
        f'The ten lawners rolled into a ring, flashed blue, and transformed into {transform.phrase}.'
    )
    world.say(
        f'"Ready, crew," said {captain_name}. "Three, two, one!"'
    )

    world.para()
    garden.meters["blocked"] = 0.0
    garden.meters["risk"] = 0.0
    garden.meters["healthy"] += 1
    garden.meters["saved"] += 1
    lawner_team.memes["pride"] += 1
    captain.memes["joy"] += 1
    friend.memes["joy"] += 1
    plant_ent = world.add(Entity(id="plants", kind="thing", type="plants", label=plant.label))
    plant_ent.meters["helped"] += 1
    plant_ent.meters["bloomed"] += 1

    world.say(
        f"Together the transformed lawners {transform.move}. {obstacle.aftermath}"
    )
    world.say(
        f'Light spilled over the beds again, and {plant.phrase} {plant.bloom}.'
    )
    world.say(
        f'"We did it!" shouted {friend_name}.'
    )
    world.say(
        f'"Not me alone," said {captain_name}. "All ten lawners, all of us."'
    )

    world.para()
    captain.memes["gratitude"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f"{guide_name} smiled at the shining robots. "
        f'"A good space crew talks, listens, and changes when the job changes," {guide.pronoun()} said.'
    )
    world.say(
        f"The ten lawners returned to their little round shapes and hummed through the clean rows of grass, while the happy garden glowed under the stars."
    )

    world.facts.update(
        setting=setting,
        plant=plant,
        obstacle=obstacle,
        transform=transform,
        captain=captain,
        friend=friend,
        guide=guide,
        lawners=lawner_team,
        garden=garden,
        teamwork=lawner_team.meters["transformed"] >= THRESHOLD,
        transformed=lawner_team.meters["transformed"] >= THRESHOLD,
        success=garden.meters["saved"] >= THRESHOLD,
        robot_count=10,
    )
    return world


KNOWLEDGE = {
    "space_garden": [
        (
            "What is a space garden?",
            "A space garden is a place on a ship or station where people grow plants away from Earth. The plants need light, water, and careful help because space can be a hard place to grow things.",
        )
    ],
    "transform": [
        (
            "What does it mean for a robot to transform?",
            "It means the robot changes shape or changes the tools it is using so it can do a new job. A good transformation matches the problem instead of being random.",
        )
    ],
    "teamwork": [
        (
            "Why is teamwork helpful on a space mission?",
            "Teamwork helps because one person or one robot may not be enough for a hard job. When everyone shares the plan and helps at the same time, the problem can be solved faster and more safely.",
        )
    ],
    "vine": [
        (
            "Why can vines be a problem in a garden machine path?",
            "A vine can wrap around rails and moving parts, so water or tools may not reach the plants. Cutting the vine carefully can open the path again.",
        )
    ],
    "crystal": [
        (
            "Why would floating crystal dust block a lamp?",
            "If a dusty cloud hangs in front of a lamp, the light cannot shine through well. Clearing the dust lets the light reach the plants again.",
        )
    ],
    "bridge": [
        (
            "Why is a bridge useful over a gap?",
            "A bridge gives wheels or tiny flying helpers a safe way to cross. Without it, they might have to stop before they reach the other side.",
        )
    ],
    "flowers": [
        (
            "Why do flowers need help in a greenhouse?",
            "Flowers need the right water, light, and air to stay healthy. If one part of the greenhouse is blocked, the flowers can droop until the problem is fixed.",
        )
    ],
}

KNOWLEDGE_ORDER = ["space_garden", "teamwork", "transform", "vine", "crystal", "bridge", "flowers"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    plant = f["plant"]
    obstacle = f["obstacle"]
    transform = f["transform"]
    captain = f["captain"]
    friend = f["friend"]
    return [
        'Write a short space adventure for a 3-to-5-year-old that uses the words "lawner", "ten", and "outlandish".',
        f"Tell a gentle story where {captain.id} and {friend.id} lead ten lawner robots in {setting.place}, talk through a problem, and solve it with teamwork and transformation.",
        f"Write a story about {plant.label} in danger because of {obstacle.label}, where the turn comes when the robots become {transform.label} and the ending shows the garden changed for the better.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    friend = f["friend"]
    guide = f["guide"]
    setting = f["setting"]
    plant = f["plant"]
    obstacle = f["obstacle"]
    transform = f["transform"]
    robot_count = f["robot_count"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {captain.id}, {friend.id}, and {robot_count} little lawner robots working in {setting.place}. They are caring for {plant.phrase} during a space adventure.",
        ),
        (
            "What problem did the crew find?",
            f"They found {obstacle.phrase} blocking {obstacle.blocks}. That mattered because {obstacle.threat.lower()}",
        ),
        (
            "How did dialogue help in the story?",
            f"The characters stopped to talk instead of rushing blindly. {friend.id} asked what shape they needed, and {guide.id} explained the right plan, so the crew could choose a sensible transformation.",
        ),
        (
            "How did the ten lawners solve the problem?",
            f"The ten lawners transformed into {transform.phrase} and together {transform.move}. They could fix it because that shape matched the obstacle's real problem.",
        ),
        (
            "Why was teamwork important?",
            f"Teamwork mattered because the job was too big for one child or one robot acting alone. The captain, the friend, and all ten lawners shared one plan and moved at the same moment.",
        ),
        (
            "How did the garden change at the end?",
            f"At the end, the obstacle was gone and {plant.phrase} {plant.bloom}. The bright ending image proves the crew truly fixed what was wrong.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["setting"].tags) | set(f["plant"].tags) | set(f["transform"].tags) | set(f["obstacle"].tags) | {"teamwork"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="dome",
        plant="moonlily",
        obstacle="vine_loop",
        transform="cutter_crown",
        captain="Mira",
        captain_gender="girl",
        friend="Bo",
        friend_gender="boy",
        guide="Captain Sol",
        guide_gender="girl",
    ),
    StoryParams(
        setting="deck",
        plant="comet_moss",
        obstacle="crystal_drift",
        transform="fan_wing",
        captain="Leo",
        captain_gender="boy",
        friend="Skye",
        friend_gender="girl",
        guide="Engineer Pax",
        guide_gender="boy",
    ),
    StoryParams(
        setting="crater",
        plant="rocket_tulip",
        obstacle="gap_ripple",
        transform="bridge_line",
        captain="Nova",
        captain_gender="girl",
        friend="Kai",
        friend_gender="boy",
        guide="Guide Luma",
        guide_gender="girl",
    ),
]


ASP_RULES = r"""
solves(O, T) :- obstacle(O), transform(T), needs(O, A), has_ability(T, A).
valid(S, P, O, T) :- setting(S), plant(P), obstacle(O), transform(T), solves(O, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for plant_id in PLANTS:
        lines.append(asp.fact("plant", plant_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.solved_by))
    for transform_id, transform in TRANSFORMS.items():
        lines.append(asp.fact("transform", transform_id))
        lines.append(asp.fact("has_ability", transform_id, transform.ability))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_name(rng: random.Random, gender: str, pool: dict[str, list[str]], avoid: str = "") -> str:
    names = [n for n in pool[gender] if n != avoid]
    return rng.choice(names)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: ten lawner robots, an outlandish space-garden problem, and a teamwork transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--captain")
    ap.add_argument("--friend")
    ap.add_argument("--guide")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.transform and not valid_combo(args.obstacle, args.transform):
        raise StoryError(explain_rejection(args.obstacle, args.transform))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.plant is None or combo[1] == args.plant)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.transform is None or combo[3] == args.transform)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, plant_id, obstacle_id, transform_id = rng.choice(sorted(combos))

    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or rng.choice(["girl", "boy"])

    captain = args.captain or _pick_name(rng, captain_gender, CAPTAIN_NAMES)
    friend = args.friend or _pick_name(rng, friend_gender, FRIEND_NAMES, avoid=captain)
    guide = args.guide or _pick_name(rng, guide_gender, GUIDE_NAMES)

    return StoryParams(
        setting=setting_id,
        plant=plant_id,
        obstacle=obstacle_id,
        transform=transform_id,
        captain=captain,
        captain_gender=captain_gender,
        friend=friend,
        friend_gender=friend_gender,
        guide=guide,
        guide_gender=guide_gender,
    )


def generate(params: StoryParams) -> StorySample:
    missing = []
    if params.setting not in SETTINGS:
        missing.append(f"setting={params.setting}")
    if params.plant not in PLANTS:
        missing.append(f"plant={params.plant}")
    if params.obstacle not in OBSTACLES:
        missing.append(f"obstacle={params.obstacle}")
    if params.transform not in TRANSFORMS:
        missing.append(f"transform={params.transform}")
    if missing:
        raise StoryError("(Invalid params: " + ", ".join(missing) + ")")
    if not valid_combo(params.obstacle, params.transform):
        raise StoryError(explain_rejection(params.obstacle, params.transform))

    world = tell(
        setting=SETTINGS[params.setting],
        plant=PLANTS[params.plant],
        obstacle=OBSTACLES[params.obstacle],
        transform=TRANSFORMS[params.transform],
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        guide_name=params.guide,
        guide_gender=params.guide_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    rc = 0
    try:
        clingo_set = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP verification failed to run clingo: {exc}")
        return 1

    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "lawner" not in sample.story.lower() or "outlandish" not in sample.story.lower():
            raise StoryError("smoke test story missing required seed language")
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, plant, obstacle, transform) combos:\n")
        for setting_id, plant_id, obstacle_id, transform_id in combos:
            print(f"  {setting_id:8} {plant_id:12} {obstacle_id:14} {transform_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain} and {p.friend}: {p.obstacle} with {p.transform} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
