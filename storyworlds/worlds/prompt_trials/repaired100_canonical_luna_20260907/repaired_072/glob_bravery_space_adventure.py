#!/usr/bin/env python3
"""
A small space-adventure storyworld about Glob, a brave traveler, and a
stalled moon rover that needs careful teamwork to reach a bright rescue beacon.
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

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    planet: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mission:
    name: str
    sky: str
    trouble: str
    first_guess: str
    clue: str
    action: str
    truth: str
    repair: str
    lesson: str
    ending: str


NAMES = {
    "girl": ["Luna", "Mira", "Asha", "Nia", "Ivy"],
    "boy": ["Leo", "Orin", "Sam", "Theo", "Kai"],
}
COMPANIONS = ["Pip", "Nova", "Tiko", "Bram", "Echo"]
PLANETS = ["Marmalade Moon", "Blue Comet", "Silver Pebble", "Little Saturn"]


MISSIONS = [
    Mission(
        "beacon_bridge",
        "a violet sky filled with slow silver stars",
        "the rover stopped before a gap in the crystal ground",
        "that the rover's engine had simply become tired",
        "a line of blue dust curled toward a folded bridge panel",
        "followed the dust, unfolded the panel, and anchored it to the rover's side rails",
        "a moonquake had shifted the bridge, but its safety panel could still lock into place",
        "crossed slowly while the rover's wheels stayed centered on the repaired bridge",
        "Bravery means taking a careful step even when the path looks frightening",
        "the rover rolled beneath the beacon, and its blue light painted a brave little circle on the ground",
    ),
    Mission(
        "frozen_signal",
        "a dark sky where a green comet blinked like a lantern",
        "the rescue beacon would not answer the ship's calling signal",
        "that the beacon had flown away into the cold night",
        "three warm flashes appeared whenever the signal cable touched a silver stone",
        "asked the companion to hold the cable while they placed the loose connector against the marked stone",
        "ice had covered the connector, and the silver stone was the signal ground",
        "brushed away the ice, secured the cable, and sent the call again",
        "Bravery grows stronger when a friend helps us test a safe idea",
        "the beacon answered with three cheerful flashes, and the ship's windows glowed like stars",
    ),
    Mission(
        "dusty_landing",
        "a copper sunset glowing through a cloud of golden space dust",
        "the landing ship's wheels sank into soft dust near the supply dome",
        "that the ship needed a faster engine",
        "the dust was firm beside a row of small moon rocks",
        "placed the emergency mats from the cargo bay across the firm trail",
        "the rocks marked an old landing path hidden under the dust",
        "guided the ship onto the mats while the companion watched the wheel lights",
        "Real courage listens to clues before rushing ahead",
        "the ship rose from the safe path, leaving neat circles in the golden dust",
    ),
    Mission(
        "shadow_crater",
        "a black sky crowded with stars above a quiet crater",
        "the rover's map screen went dark at the edge of a long shadow",
        "that the map was broken forever",
        "a tiny reflection on the rover's mirror pointed toward a bright power tile",
        "turned the mirror toward the tile and waited for the sunlight to reach the screen",
        "the shadow had covered the rover's solar panel, while the tile marked a sunny place",
        "moved the rover one careful wheel at a time until the panel caught the light",
        "Being brave can mean staying patient while the answer slowly appears",
        "the map brightened, and the crater's rim became a silver road home",
    ),
    Mission(
        "floating_garden",
        "a peach-colored dawn above a garden of floating seed pods",
        "the ship's welcome flag tangled around a tall antenna",
        "that the wind had carried the flag into space",
        "the flag's golden thread was wrapped around the antenna twice, not torn away",
        "held the antenna steady and unwound the thread one loop at a time",
        "a burst of air had twisted the flag around the antenna",
        "freed the flag and tied it to a lower, safer hook",
        "Careful bravery protects both the traveler and the things they love",
        "the welcome flag fluttered below the antenna as the floating garden opened its silver flowers",
    ),
]


def choose_mission(rng: random.Random) -> Mission:
    return MISSIONS[rng.randrange(len(MISSIONS))]


def tell_story(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    mission = choose_mission(rng)
    opening = rng.choice([
        "At the edge of the galaxy",
        "Beyond the last bright star",
        "On the quiet side of the moon",
        "Near a ring of sleeping asteroids",
    ])

    world = World(place=f"the surface of {params.planet}")
    traveler = world.add(Entity(params.name, "character", params.gender))
    companion = world.add(Entity(params.companion, "character", "robot"))
    rover = world.add(Entity("rover", "thing", "moon rover"))
    beacon = world.add(Entity("beacon", "thing", "rescue beacon"))
    glob = world.add(Entity("glob", "thing", "glowing space glob"))

    traveler.memes["bravery"] = 0.0
    companion.memes["trust"] = 1.0
    rover.meters["distance_to_beacon"] = 12.0
    glob.meters["brightness"] = 1.0

    world.say(
        f"{opening}, {params.name} and {params.companion} explored {world.place}. "
        f"The little robot carried a glowing glob in its round tool cup, and a rescue beacon "
        f"shone far away through {mission.sky}."
    )
    world.say(f"They were heading home when {mission.trouble}.")
    world.say(
        f'"We should go back," {params.companion} said. "{mission.first_guess.capitalize()}."'
    )
    world.say(
        f'"We can be brave without being reckless," {params.name} answered. '
        f'"Let us stop, look, and find one safe clue."'
    )

    world.para()
    world.say(
        f"The glob trembled in its cup and cast a soft light over the ground. "
        f"In that glow, {params.name} noticed that {mission.clue}."
    )
    world.say(
        f'"The glob is showing us something," {params.name} said. '
        f'"Will you shine your lamp over here?"'
    )
    world.say(
        f'"I will," {params.companion} replied. "You lead, and I will watch the safe path."'
    )
    world.say(f"Together, they {mission.action}.")

    world.para()
    world.say(
        f"Then they discovered the truth: {mission.truth}. "
        f"{params.name}'s hands felt shaky, but the glob glowed steadily."
    )
    world.say(
        f'"I am still scared," {params.name} admitted. "I can do the next small step."'
    )
    world.say(
        f'"That is bravery," {params.companion} said. "One careful step with a friend."'
    )
    world.say(f"At last, they {mission.repair}.")

    traveler.memes["bravery"] = 1.0
    rover.meters["distance_to_beacon"] = 0.0
    beacon.meters["reached"] = 1.0
    glob.memes["hope"] = 1.0

    world.para()
    world.say(
        f"{params.name} learned that {mission.lesson}. "
        f"The rescue beacon began to sing a gentle electronic tune."
    )
    world.say(
        f"At the end of the adventure, {mission.ending}. "
        f"{params.name}, {params.companion}, and the glowing glob traveled home together."
    )

    world.facts.update(
        traveler=traveler,
        companion=companion,
        rover=rover,
        beacon=beacon,
        glob=glob,
        mission=mission,
        place=world.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    mission: Mission = world.facts["mission"]
    traveler: Entity = world.facts["traveler"]
    return [
        f"Write a child-friendly space adventure about {traveler.id} showing bravery during the {mission.name.replace('_', ' ')} mission.",
        f"Tell a story in which a glowing glob helps a young space traveler notice a clue and solve a problem.",
        "Write a gentle space adventure with a short dialogue exchange, careful courage, and a hopeful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    traveler: Entity = f["traveler"]
    companion: Entity = f["companion"]
    mission: Mission = f["mission"]
    return [
        QAItem(
            question=f"What problem did {traveler.id} and {companion.id} face?",
            answer=f"They faced this problem: {mission.trouble}. It blocked their journey to the rescue beacon.",
        ),
        QAItem(
            question="How did the glob help?",
            answer=f"The glowing glob helped by making it possible to notice that {mission.clue}.",
        ),
        QAItem(
            question=f"What did {traveler.id} first decide to do?",
            answer=f"{traveler.id} decided to stop, look for a safe clue, and avoid rushing into danger.",
        ),
        QAItem(
            question="How did the companions solve the problem?",
            answer=f"Together, they {mission.action}. Then they learned that {mission.truth}.",
        ),
        QAItem(
            question=f"What did {traveler.id} learn about bravery?",
            answer=f"{traveler.id} learned that {mission.lesson}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended when {mission.ending}. The travelers and the glob returned home safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rescue beacon?",
            answer="A rescue beacon is a device that sends or shows a signal so travelers can find help or find their way home.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something careful and worthwhile even when you feel afraid.",
        ),
        QAItem(
            question="Why is teamwork useful in space?",
            answer="Teamwork is useful in space because one traveler can act while another watches, checks clues, or keeps the path safe.",
        ),
        QAItem(
            question="Why should space explorers move carefully?",
            answer="They should move carefully because unfamiliar ground, machinery, shadows, and dust can hide dangers.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
% A brave mission succeeds when the traveler notices the clue,
% works with a companion, and reaches the beacon.
careful_bravery(T) :- traveler(T), notices_clue(T), teamwork(T).
mission_safe :- careful_bravery(T), reaches_beacon(T).

#show careful_bravery/1.
#show mission_safe/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("traveler", "luna"),
        asp.fact("notices_clue", "luna"),
        asp.fact("teamwork", "luna"),
        asp.fact("reaches_beacon", "luna"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mission_safe/0."))
    if asp.atoms(model, "mission_safe"):
        print("OK: ASP reasoning confirms a safe brave mission.")
        return 0
    print("MISMATCH: ASP reasoning did not confirm a safe brave mission.")
    return 1


def validate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if params.gender not in NAMES:
        raise StoryError("gender must be girl or boy")
    if params.companion not in COMPANIONS:
        raise StoryError("companion is not in the registry")
    if params.planet not in PLANETS:
        raise StoryError("planet is not in the registry")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a gentle space adventure about Glob and bravery."
    )
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=sorted(NAMES))
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--planet", choices=PLANETS)
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
    gender = args.gender
    if gender is None and args.name:
        gender = next(
            (kind for kind, names in NAMES.items() if args.name in names),
            None,
        )
    gender = gender or rng.choice(list(NAMES))
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(COMPANIONS)
    planet = args.planet or rng.choice(PLANETS)
    params = StoryParams(name=name, gender=gender, companion=companion, planet=planet)
    validate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    validate(params)
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:10} ({entity.type:14}) {' '.join(details)}".rstrip()
        )
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
    StoryParams("Luna", "girl", "Pip", "Marmalade Moon", 7101),
    StoryParams("Leo", "boy", "Nova", "Blue Comet", 7102),
    StoryParams("Mira", "girl", "Echo", "Silver Pebble", 7103),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show careful_bravery/1. #show mission_safe/0."))
        return

    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        for params in CURATED:
            sample = generate(params)
            if not sample.story.strip() or "bravery" not in sample.story.lower():
                print("MISMATCH: generated story failed the bravery check.")
                sys.exit(1)
        print("OK: generated stories passed the bravery check.")
        return

    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show careful_bravery/1. #show mission_safe/0.")
        )
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
