#!/usr/bin/env python3
"""
A small space-adventure storyworld about a usual sweater, a special skill,
and a friendship tested by a surprising twist.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO_ROOT = os.path.dirname(ROOT)
for path in (REPO_ROOT, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Scene:
    place: str
    mission: str
    specialty: str
    sweater_color: str


@dataclass
class World:
    scene: Scene
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
    place: str
    mission: str
    specialty: str
    sweater_color: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


PLACES = {
    "moon_orbit": Scene(
        place="the moon's quiet orbit",
        mission="deliver a weather beacon",
        specialty="reading tiny star maps",
        sweater_color="red",
    ),
    "asteroid_belt": Scene(
        place="the glittering asteroid belt",
        mission="repair a listening satellite",
        specialty="building clever signal tools",
        sweater_color="blue",
    ),
    "mars_station": Scene(
        place="a bright station above Mars",
        mission="carry a seed capsule",
        specialty="growing plants in small spaces",
        sweater_color="gold",
    ),
}

CHILD_NAMES = ["Luna", "Milo", "Nia", "Theo", "Aria", "Sol"]
FRIEND_NAMES = ["Comet", "Pip", "Ravi", "Zia", "Tess", "Orion"]
GIRL_NAMES = {"Luna", "Nia", "Aria", "Zia", "Tess"}
ROBOT_NAMES = {"Comet", "Pip", "Orion"}


@dataclass(frozen=True)
class Arc:
    need: str
    premise: str
    obstacle: str
    twist: str
    action: str
    lesson: str
    ending: str


ARCS = (
    Arc(
        need="wanted to prove that a usual day could hold a real adventure",
        premise="{friend} asked {child} to wear the usual {color} sweater for luck.",
        obstacle="A burst of moon dust spun their navigation cards away from the shuttle.",
        twist="{child} discovered that the sweater's loose silver thread was actually a trail left by a tiny repair drone.",
        action="Instead of chasing the cards, the friends followed the thread and found the drone holding them beside the beacon.",
        lesson="They learned that an ordinary sweater could hide an extraordinary clue, but careful friendship mattered more than luck.",
        ending="The usual sweater floated gently in the cabin while the repaired beacon blinked like a new star.",
    ),
    Arc(
        need="felt nervous about using a special skill in front of a friend",
        premise="{child} packed the usual {color} sweater while {friend} praised {child}'s specialty.",
        obstacle="The station's star compass began pointing in three directions at once.",
        twist="{friend} admitted that the compass was not broken; a shy space whale was nudging it toward a hidden ice garden.",
        action="{child} used the specialty to read the whale's pattern, while {friend} kept the garden safe with a soft signal.",
        lesson="They learned that a specialty grows stronger when it is shared, and friendship makes a frightening mystery gentler.",
        ending="The ice garden opened its crystal flowers as the {color} sweater glowed beside the quiet compass.",
    ),
    Arc(
        need="was afraid a mistake would end a new friendship",
        premise="{friend} offered to help {child} cross the usual meteor trail in a warm {color} sweater.",
        obstacle="A wrong button sent their little rover drifting toward a dark crater.",
        twist="The button had not caused the trouble; a hidden moon mouse had pressed it while searching for warmth.",
        action="They welcomed the mouse into the rover, then used {child}'s specialty to guide everyone back to the path.",
        lesson="They learned that blaming someone too quickly can hide the real problem, while patience gives friendship room to grow.",
        ending="The moon mouse slept in the sweater's pocket as the rover rolled safely beneath the stars.",
    ),
    Arc(
        need="hoped to make one perfect space mission",
        premise="{child} brought the usual {color} sweater, and {friend} brought a specialty tool for the mission.",
        obstacle="Their delivery pod landed beside the wrong glowing tower.",
        twist="The wrong tower was a beacon for a lonely comet family, not a mistake at all.",
        action="{friend} used the tool to send a welcome pulse while {child} shared the pod's warm blanket.",
        lesson="They learned that a mission can change shape without failing, especially when friends notice who needs help.",
        ending="The comet family sailed onward, and the sweater's bright sleeve waved goodbye through the pod window.",
    ),
)


DIALOGUES = (
    '"Are you sure we can do this?" {child} asked. "Not alone," {friend} replied. "Together."',
    '"I have a specialty," {child} said softly. {friend} smiled. "Then I will be your teammate."',
    '"Wait before we decide," {friend} urged. "Good idea," said {child}. "Let us look closer."',
    '"The stars changed!" cried {child}. "Then our plan can change too," said {friend}.',
)


def choose_type(name: str) -> str:
    if name in ROBOT_NAMES:
        return "robot"
    return "girl" if name in GIRL_NAMES else "boy"


def render(text: str, world: World, child: Entity, friend: Entity) -> str:
    return text.format(
        child=child.id,
        friend=friend.id,
        color=world.scene.sweater_color,
    )


def simulate(params: StoryParams) -> World:
    scene = PLACES[params.place]
    world = World(scene)
    child = world.add(
        Entity(params.child_name, "character", params.child_type, params.child_name)
    )
    friend = world.add(
        Entity(params.friend_name, "character", params.friend_type, params.friend_name)
    )
    sweater = world.add(
        Entity(
            "usual_sweater",
            "thing",
            "sweater",
            f"a usual {scene.sweater_color} sweater",
            meters={"worn": 0.0, "clue": 0.0},
            memes={"comfort": 1.0},
        )
    )
    beacon = world.add(
        Entity(
            "mission_beacon",
            "thing",
            "beacon",
            "the mission beacon",
            meters={"safe": 0.0, "delivered": 0.0},
        )
    )

    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = rng.choice(ARCS)
    dialogue = rng.choice(DIALOGUES)

    world.facts.update(
        child=child,
        friend=friend,
        sweater=sweater,
        beacon=beacon,
        arc=arc,
        dialogue=dialogue,
        resolved=False,
    )

    world.say(
        f"On {scene.place}, {child.id} {arc.need}. "
        f"{friend.id} was waiting beside a small space shuttle."
    )
    world.say(
        f"The friends were on a mission to {scene.mission}, and "
        f"{child.id} carried {child.id}'s specialty like a secret tool."
    )
    world.say(render(arc.premise, world, child, friend))
    sweater.meters["worn"] = 1.0
    world.para()

    world.say(render(arc.obstacle, world, child, friend))
    child.memes["worried"] = 1.0
    friend.memes["loyal"] = 1.0
    world.say(render(dialogue, world, child, friend))
    world.para()

    world.say(render(arc.twist, world, child, friend))
    sweater.meters["clue"] = 1.0
    child.memes["curious"] = 1.0
    world.say(render(arc.action, world, child, friend))
    beacon.meters["delivered"] = 1.0
    beacon.meters["safe"] = 1.0
    world.para()

    world.say(render(arc.lesson, world, child, friend))
    child.memes["confident"] = 1.0
    friend.memes["happy"] = 1.0
    world.say(render(arc.ending, world, child, friend))
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    scene = world.scene
    child = world.facts["child"]
    friend = world.facts["friend"]
    return [
        f"Write a space adventure about {child.id} and {friend.id}, a usual sweater, and {scene.specialty}.",
        f"Tell a friendship story during a mission to {scene.mission}, with a surprising twist and a lesson learned.",
        f"Write a child-friendly story set in {scene.place} where careful teamwork changes the mission.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    friend: Entity = world.facts["friend"]
    sweater: Entity = world.facts["sweater"]
    arc: Arc = world.facts["arc"]
    return [
        QAItem(
            question=f"Why did {child.id} and {friend.id} travel through space?",
            answer=f"They traveled through {world.scene.place} to {world.scene.mission}, while using {child.id}'s specialty and helping each other.",
        ),
        QAItem(
            question=f"What problem interrupted {child.id} and {friend.id}'s mission?",
            answer=render(arc.obstacle, world, child, friend),
        ),
        QAItem(
            question=f"What was the surprising twist involving {sweater.label}?",
            answer=render(arc.twist, world, child, friend),
        ),
        QAItem(
            question="What lesson did the friends learn?",
            answer=arc.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do astronauts wear special clothing?",
            answer="Astronaut clothing helps protect people from cold, heat, dust, and other dangers in space.",
        ),
        QAItem(
            question="How can friendship help during a difficult mission?",
            answer="Friends can listen, share skills, notice problems, and make brave choices together.",
        ),
        QAItem(
            question="What is a specialty?",
            answer="A specialty is a skill or kind of knowledge that someone has practiced and can use to help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(C,F,S,B) :- child(C), friend(F), specialty(S), sweater(B),
    uses_specialty(C,S), wears(F,B), mission(C).
twist_ready(B) :- sweater(B), clue(B).
friendship_resolved(C,F) :- child(C), friend(F), helps(C,F), helps(F,C).
mission_complete(C) :- child(C), beacon_delivered(C), friendship_resolved(C,F).
#show reasonable/4.
#show twist_ready/1.
#show friendship_resolved/2.
#show mission_complete/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for place_id, scene in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("mission", place_id, scene.mission.replace(" ", "_")))
    lines.extend(
        [
            asp.fact("child", "child"),
            asp.fact("friend", "friend"),
            asp.fact("specialty", "specialty"),
            asp.fact("sweater", "usual_sweater"),
            asp.fact("uses_specialty", "child", "specialty"),
            asp.fact("wears", "friend", "usual_sweater"),
            asp.fact("mission", "child"),
            asp.fact("clue", "usual_sweater"),
            asp.fact("helps", "child", "friend"),
            asp.fact("helps", "friend", "child"),
            asp.fact("beacon_delivered", "child"),
        ]
    )
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    if not model:
        print("ASP verification failed: no model.")
        return 1
    shown = set(sym.name for sym in model)
    required = {"reasonable", "twist_ready", "friendship_resolved", "mission_complete"}
    if not required.issubset(shown):
        print("ASP verification failed: missing shown predicates.")
        return 1
    print("OK: ASP/Python storyworld parity verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Space adventure sweater friendship storyworld.")
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--specialty", choices=[s.specialty for s in PLACES.values()])
    parser.add_argument("--sweater-color", choices=["red", "blue", "gold"])
    parser.add_argument("--child-name", choices=CHILD_NAMES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    scene = PLACES[place]
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    if child_name == friend_name:
        raise StoryError("The explorer and friend must have different names.")
    specialty = args.specialty or scene.specialty
    color = args.sweater_color or scene.sweater_color
    return StoryParams(
        place=place,
        mission=scene.mission,
        specialty=specialty,
        sweater_color=color,
        child_name=child_name,
        child_type=choose_type(child_name),
        friend_name=friend_name,
        friend_type=choose_type(friend_name),
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: {entity.type}; "
                f"meters={entity.meters}; memes={entity.memes}"
            )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(
                place="moon_orbit",
                mission=PLACES["moon_orbit"].mission,
                specialty=PLACES["moon_orbit"].specialty,
                sweater_color="red",
                child_name="Luna",
                child_type="girl",
                friend_name="Comet",
                friend_type="robot",
                seed=101,
            ),
            StoryParams(
                place="asteroid_belt",
                mission=PLACES["asteroid_belt"].mission,
                specialty=PLACES["asteroid_belt"].specialty,
                sweater_color="blue",
                child_name="Theo",
                child_type="boy",
                friend_name="Zia",
                friend_type="girl",
                seed=202,
            ),
            StoryParams(
                place="mars_station",
                mission=PLACES["mars_station"].mission,
                specialty=PLACES["mars_station"].specialty,
                sweater_color="gold",
                child_name="Aria",
                child_type="girl",
                friend_name="Pip",
                friend_type="robot",
                seed=303,
            ),
        ]
    else:
        params_list = [
            resolve_params(args, random.Random(seed + i))
            for i in range(max(0, args.n))
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
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
