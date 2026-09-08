#!/usr/bin/env python3
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    name: str
    affords: set[str]


@dataclass
class Task:
    id: str
    name: str
    object_name: str


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    helper: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Arc:
    opening: str
    omen: str
    problem: str
    clue: str
    twist: str
    action: str
    result: str
    ending: str
    lesson: str
    cause: str


SETTINGS = {
    "hill": Setting("hill", "the hill of three winds", {"ring_bell", "light_beacon"}),
    "grove": Setting("grove", "the moonlit grove", {"ring_bell", "wake_tree"}),
    "shore": Setting("shore", "the shell shore", {"light_beacon", "wake_tree"}),
}

TASKS = {
    "ring_bell": Task("ring_bell", "ring the dawn bell", "bronze bell"),
    "light_beacon": Task("light_beacon", "light the hill beacon", "star lamp"),
    "wake_tree": Task("wake_tree", "wake the sleeping tree", "silver seed"),
}

HEROES = ["Luna", "Mira", "Tavi", "Nia", "Orin"]
HELPERS = ["the fox", "the old raven", "the river spirit", "a young giant"]

ARCS = [
    Arc(
        "Long ago, Luna climbed the hill where the first dawn was kept in a clay jar.",
        "Before she reached the shrine, the sky changed from black to violet, but the sacred bell made no sound.",
        "The bell's rope had vanished, and without its call the sun would not know where to rise.",
        "Tiny golden threads led from the empty hook toward a nest tucked under the shrine roof.",
        "The missing rope was not stolen by a monster; a mother bird had borrowed it to hold her nest together.",
        "Luna loosened the rope gently, replaced it with a strong vine, and left a coil of soft grass for the bird.",
        "The bell rang across the hill, and the dawn poured out of the clay jar.",
        "The bird's nest shone like a little crown while the first sunbeam touched Luna's face.",
        "A thing may be sacred and still be needed by someone small; wisdom begins when we look for both needs.",
        "The bird had borrowed the bell rope to mend her nest.",
    ),
    Arc(
        "At moonrise, Mira carried a star lamp to the old stones that marked the road home.",
        "The lamp flickered three times, and every shadow pointed toward the dark marsh.",
        "Its flame would not stay lit because a bright crystal inside had cracked.",
        "When Mira held the crystal near the moon, she saw a second glow shining through its broken edge.",
        "The cracked crystal was not useless; it had become a lens that could guide moonlight.",
        "Mira turned the crystal toward the sky and sheltered its small flame with her cloak.",
        "The lamp blazed brighter than before and drew a silver path around the marsh.",
        "Travelers followed the new path, while the broken crystal glittered at the lamp's heart.",
        "A broken gift can become a new kind of gift when we stop asking it to be what it was.",
        "The cracked crystal gathered moonlight and made the lamp a guide.",
    ),
    Arc(
        "In the moonlit grove, Tavi came to wake the ancient tree before the forest festival.",
        "He placed the silver seed at the roots, but the sleeping tree sighed and folded its leaves tighter.",
        "The tree's roots were thirsty, though a shining pool stood only a few steps away.",
        "The pool was covered by a smooth stone, and a narrow trail of damp earth ran beneath it.",
        "The stone was not a lid placed by an enemy; it was the tree's own root pressing up to protect a hidden spring.",
        "Tavi moved the loose soil aside, guided the water into a shallow channel, and planted the seed there.",
        "The tree woke with a deep green rustle and opened flowers shaped like moons.",
        "Every flower held a drop of water, and the grove sang without anyone striking a drum.",
        "Before asking a sleeping heart to open, learn what it has been protecting.",
        "The tree's root had covered the spring and kept its thirst hidden.",
    ),
    Arc(
        "On the shell shore, Nia carried the beacon's lamp to the edge of the world.",
        "A red wave rose like a wall, and the beacon's guiding flame went out.",
        "The beacon seemed empty, but its glass was filled with cloudy seawater.",
        "Inside the water floated a tiny pearl that pulsed whenever the tide pulled back.",
        "The sea had not extinguished the beacon; it had placed a pearl inside to show where the safe channel lay.",
        "Nia cleaned the glass, set the pearl above the wick, and waited for the tide to turn.",
        "The beacon shone blue and white, pointing ships toward calm water.",
        "Far out at sea, the waves parted like curtains around a road of light.",
        "A frightening change may carry a message if we are patient enough to read it.",
        "The tide left a guiding pearl inside the darkened beacon.",
    ),
    Arc(
        "Orin found the dawn bell hanging in a valley where echoes were said to become giants.",
        "When he struck it, no note came out, yet a deep roar rolled through the stones.",
        "The bell's voice was trapped under the valley floor.",
        "A line of pebbles trembled in time with Orin's heartbeat and led to a sealed crack.",
        "The roar was not a giant waking; it was the bell's echo traveling through a buried tunnel.",
        "Orin opened the crack with a fallen branch and struck the bell once more.",
        "Its clear note crossed the valley and turned the echo into music.",
        "Even the stones seemed to bow as the mountain answered with a gentle song.",
        "What sounds frightening from far away may become beautiful when we find its true path.",
        "The bell's echo had traveled through a hidden tunnel beneath the valley.",
    ),
]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


def valid_combos() -> list[tuple[str, str]]:
    return [(place, task) for place, setting in SETTINGS.items() for task in setting.affords]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mythic transition story with a twist and a lesson.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--task", choices=sorted(TASKS))
    parser.add_argument("--hero")
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
    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.task is None or combo[1] == args.task)
    ]
    if not combos:
        raise StoryError("No setting and task combination supports that request.")
    place, task = rng.choice(combos)
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    if hero.lower() == helper.lower():
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(place=place, task=task, hero=hero, helper=helper)


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.task not in TASKS:
        raise StoryError(f"Unknown task: {params.task}")
    if params.task not in SETTINGS[params.place].affords:
        raise StoryError(f"The task {params.task} cannot happen in {params.place}.")
    world = World(SETTINGS[params.place])
    world.add(Entity(params.hero, "character", params.hero, memes={"courage": 1.0}))
    world.add(Entity("helper", "character", params.helper, memes={"wisdom": 1.0}))
    world.add(Entity("relic", "object", TASKS[params.task].object_name, meters={"whole": 1.0}))
    world.facts["task"] = TASKS[params.task]
    world.facts["arc"] = ARCS[(params.seed or 0) % len(ARCS)]
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    arc: Arc = world.facts["arc"]
    task: Task = world.facts["task"]
    hero = params.hero
    helper = params.helper
    story = (
        f"{arc.opening} {arc.opening.split(' ', 1)[0]} had come to {task.name}, "
        f"but the old rite stood at a turning point. {arc.omen} "
        f"{arc.problem} "
        f'"What shall we do?" asked {hero}. '
        f'"We will watch before we judge," answered {helper}. '
        f"{arc.clue} "
        f'"Then the danger is not what it seemed," said {hero}. '
        f'"A twist can hide a kindness," said {helper}. '
        f"{arc.twist} "
        f"{hero} and {helper} worked together. {arc.action} "
        f"{arc.result} "
        f"{arc.ending} "
        f"{arc.lesson}"
    )
    world.tags.update({"transition", "twist", "lesson_learned", "myth"})
    world.facts["completed"] = True
    return StorySample(
        params=params,
        story=story,
        prompts=[
            f"Tell a mythic story about {hero} completing {task.name} during a magical transition.",
            "Include a surprising twist and a clear lesson learned.",
            f"Show how {helper} changes the hero's decision in {world.setting.name}.",
        ],
        story_qa=[
            QAItem("What transition happened in the story?", f"The world moved from an uncertain moment into a new beginning when {hero} completed {task.name}."),
            QAItem("What was the twist?", arc.twist),
            QAItem("How did the characters solve the problem?", f"{hero} and {helper} worked together: {arc.action}"),
            QAItem("What lesson did the hero learn?", arc.lesson),
            QAItem("How did the story end?", arc.ending),
        ],
        world_qa=[
            QAItem("What is a transition?", "A transition is a change from one state, place, or time into another."),
            QAItem("What is a twist in a story?", "A twist is a surprising change in what the reader thought was happening."),
            QAItem("What is a lesson learned?", "A lesson learned is an idea a character understands after an experience."),
            QAItem("What is a myth?", "A myth is a traditional-style tale that uses wonder to explore important ideas."),
        ],
        world=world,
    )


ASP_RULES = r"""
valid(P,T) :- affords(P,T).
transition(P,T) :- valid(P,T).
myth(P,T) :- transition(P,T).
twist(P,T) :- myth(P,T).
lesson_learned(P,T) :- twist(P,T).
#show valid/2.
#show transition/2.
#show twist/2.
#show lesson_learned/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for task in sorted(setting.affords):
            lines.append(asp.fact("affords", place, task))
    for task in TASKS:
        lines.append(asp.fact("activity", task))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        import asp
        model = asp.one_model(asp_program())
        atoms = set(asp.atoms(model, "valid"))
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if atoms != py:
        print(f"ASP/Python mismatch: Python={sorted(py)}, ASP={sorted(atoms)}")
        return 1
    for index, combo in enumerate(sorted(py)):
        params = StoryParams(combo[0], combo[1], HEROES[index % len(HEROES)], HELPERS[index % len(HELPERS)], index)
        sample = generate(params)
        if not sample.story or "twist" not in sample.world.tags:
            return 1
    print(f"OK: ASP/Python parity and story checks passed ({len(py)} combinations).")
    return 0


def dump_trace(world: World) -> str:
    lines = ["--- world ---", f"setting: {world.setting.name}", f"tags: {sorted(world.tags)}"]
    for entity in world.entities.values():
        lines.append(f"{entity.label}: meters={entity.meters}, memes={entity.memes}")
    lines.append(f"facts: completed={world.facts.get('completed', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for item in sample.story_qa + sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("hill", "ring_bell", "Luna", "the old raven", 0),
    StoryParams("grove", "wake_tree", "Mira", "the river spirit", 2),
    StoryParams("shore", "light_beacon", "Tavi", "the fox", 3),
]


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
            models = asp.solve(asp_program(), models=1)
            print(json.dumps([str(atom) for atom in models[0]] if models else []))
        except Exception as exc:
            raise SystemExit(f"ASP error: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for index in range(max(args.n, 1) * 100):
            if len(samples) >= max(args.n, 1):
                break
            rng = random.Random(base_seed + index)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                raise
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        print(json.dumps(
            samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples],
            indent=2,
            ensure_ascii=False,
        ))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
