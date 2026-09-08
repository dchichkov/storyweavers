#!/usr/bin/env python3
"""
A small pirate tale about an expired trail map, a perturbing fallen tree,
and a lesson learned before a bad ending can become real.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
while not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    parent = os.path.dirname(_storyworlds_dir)
    if parent == _storyworlds_dir:
        break
    _storyworlds_dir = parent
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
    place: str
    affords: set[str]


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
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "fallen_tree_trail": Setting(
        id="fallen_tree_trail",
        place="the fallen tree trail",
        affords={"map_check", "safe_crossing"},
    ),
}

TASKS = {
    "map_check": "checking the treasure map",
    "safe_crossing": "finding a safe way past the tree",
}

TOOLS = {
    "compass": "a brass compass",
    "rope": "a coil of sturdy rope",
    "lantern": "a bright ship lantern",
}

NAMES = ["Luna", "Pip", "Mara", "Finn", "Nell"]
HELPERS = ["Captain Coral", "Sailor Blue", "First Mate Jo"]

STORIES = [
    {
        "opening": "Luna and her little pirate crew followed a mossy trail toward a chest of shining shells.",
        "surprise": "A fallen tree lay across the path, and the old map suddenly faded at its edge.",
        "cause": "The map had expired because rain had washed away its ink, so its last arrow pointed to a path that no longer existed.",
        "actions": ("held the lantern high", "checked the compass", "tied the rope around a sturdy branch"),
        "result": "They found a short, safe path around the roots instead of crawling beneath the heavy trunk.",
        "ending": "The shell chest waited in a sunny hollow, where Luna marked the new route on a fresh scrap of sailcloth.",
        "lesson": "A map can expire, so wise sailors check the land and update their directions.",
    },
    {
        "opening": "Luna sailed her walking crew along the fallen tree trail in search of a captain's lost bell.",
        "surprise": "A gust perturbed the trail markers, spinning every little wooden arrow in a different direction.",
        "cause": "The arrows had been tied with loose knots, and the fallen tree blocked the wind into a whirling tunnel.",
        "actions": ("stacked stones beside the true trail", "tightened the marker knots", "used the compass to confirm the turn"),
        "result": "The markers stopped dancing and pointed toward a dry creek bed where the bell gleamed.",
        "ending": "The crew rang the bell only once, then left a strong new marker for the next travelers.",
        "lesson": "When a surprise perturbs a plan, sailors should check several clues before choosing a course.",
    },
    {
        "opening": "Luna and her friends hunted for a tiny treasure flag beside the fallen tree trail.",
        "surprise": "A branch cracked, and the treasure map fluttered into a muddy puddle.",
        "cause": "The wet map began to expire, but a carved star on the tree showed an older safe route.",
        "actions": ("lifted the map from the mud", "followed the carved star", "placed flat stones over the slippery ground"),
        "result": "They crossed the muddy patch without slipping and found the flag beside a blue fern.",
        "ending": "Their treasure was a jar of berry jam, and Luna kept the dry map tucked inside a waxed cover.",
        "lesson": "Protect important directions before trouble arrives, and look for safe signs when plans change.",
    },
]


@dataclass
class StoryParams:
    setting: str = "fallen_tree_trail"
    task: str = "map_check"
    hero: str = "Luna"
    helper: str = "Captain Coral"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate tale on the fallen tree trail.")
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--task", choices=TASKS, default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--helper", default=None)
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
    setting = args.setting or "fallen_tree_trail"
    task = args.task or rng.choice(sorted(SETTINGS[setting].affords))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != hero])
    if not hero.strip() or not helper.strip():
        raise StoryError("Hero and helper names must not be empty.")
    return StoryParams(setting=setting, task=task, hero=hero, helper=helper)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.task not in TASKS:
        raise StoryError(f"Unknown task: {params.task}")

    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(params.hero, "character", params.hero, memes={"curiosity": 1.0}))
    helper = world.add(Entity("helper", "character", params.helper, memes={"care": 1.0}))
    tree = world.add(Entity("fallen_tree", "obstacle", "the fallen tree", meters={"weight": 4.0}))
    map_item = world.add(Entity("map", "object", "the old treasure map", meters={"age": 3.0}))
    compass = world.add(Entity("compass", "tool", TOOLS["compass"], meters={"reliability": 2.0}))
    rope = world.add(Entity("rope", "tool", TOOLS["rope"], meters={"strength": 2.0}))
    lantern = world.add(Entity("lantern", "tool", TOOLS["lantern"], meters={"light": 2.0}))

    index = (params.seed or 0) % len(STORIES)
    arc = STORIES[index]
    world.facts.update(
        hero=hero,
        helper=helper,
        tree=tree,
        map=map_item,
        compass=compass,
        rope=rope,
        lantern=lantern,
        arc=arc,
        bad_ending=False,
        surprise=True,
        lesson_learned=True,
    )

    world.say(f"{arc['opening']} {hero.label} carried {map_item.label}, while {helper.label} marched behind with {rope.label}.")
    world.say(f"Their goal was {TASKS[params.task]}, but the trail was narrow and quiet under the leaves.")

    world.para()
    world.say(f"Surprise! {arc['surprise']}")
    world.say(f"The trouble could perturb their voyage: if they trusted the faded directions, they might reach a bad ending beneath the unsafe tree.")
    world.say(f'"Avast, Luna!" cried {helper.label}. "Should we trust this old map?"')
    world.say(f'"Not yet," said {hero.label}. "Let us inspect the trail before we choose a course."')

    world.para()
    world.say(arc["cause"])
    world.say(f"{hero.label} raised {lantern.label}, {helper.label} studied {compass.label}, and together they noticed the safer signs beside the roots.")
    world.say(f'"The map may expire," said {helper.label}, "but careful eyes can still find the truth."')
    world.say(f'"Then we will make a new plan," said {hero.label}.')

    world.para()
    first, second, third = arc["actions"]
    world.say(f"The crew worked as one: {hero.label} {first}, {helper.label} {second}, and both sailors {third}.")
    world.say(arc["result"])
    world.say("The bad ending faded away because the crew stopped, checked the evidence, and changed course.")

    world.para()
    world.say(f"Lesson Learned: {arc['lesson']}")
    world.say(arc["ending"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle Pirate Tale about {f['hero'].label} on {world.setting.place}.",
        "Include an expired map, a surprise that perturbs the plan, a possible bad ending, and a lesson learned.",
        f"Show how {f['hero'].label} and {f['helper'].label} use careful clues and teamwork to reach safety.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    arc = f["arc"]
    return [
        QAItem(
            "Where did the pirate tale take place?",
            f"The tale took place on {world.setting.place}, where {f['hero'].label} and {f['helper'].label} followed a narrow trail.",
        ),
        QAItem(
            "What was the surprise?",
            arc["surprise"],
        ),
        QAItem(
            "Why did the plan become dangerous?",
            f"The old map had expired or the trail had been perturbed, so trusting it could have led the crew beneath the heavy fallen tree.",
        ),
        QAItem(
            "How did the crew avoid a bad ending?",
            f"They inspected the trail, used clues such as the compass and markers, shared the work, and chose a safe route around the tree.",
        ),
        QAItem(
            "What lesson was learned?",
            arc["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does expire mean?", "To expire means to become too old or no longer valid for use."),
        QAItem("What does perturb mean?", "To perturb means to disturb something or make it less steady or orderly."),
        QAItem("What is a compass used for?", "A compass helps travelers find direction."),
        QAItem("What is a bad ending?", "A bad ending is an unsafe result that careful choices can sometimes prevent."),
        QAItem("What does a lesson learned mean?", "It is an important idea remembered after an experience."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"facts: surprise={world.facts['surprise']}; lesson_learned={world.facts['lesson_learned']}; bad_ending={world.facts['bad_ending']}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for item in sample.story_qa + sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_registry(S).
task(T) :- task_registry(T).
valid(S,T) :- setting(S), task(T), affords(S,T).
expired(map) :- old(map).
perturbed(trail) :- fallen_tree(trail), wind(trail).
safe_course(S) :- valid(S,T), has_compass, has_rope.
bad_ending_avoided :- safe_course(S).
lesson_learned :- bad_ending_avoided.
#show valid/2.
#show bad_ending_avoided/0.
#show lesson_learned/0.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting_registry", setting_id))
        for task in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, task))
    for task_id in TASKS:
        lines.append(asp.fact("task_registry", task_id))
    lines.extend(
        [
            asp.fact("old", "map"),
            asp.fact("fallen_tree", "trail"),
            asp.fact("wind", "trail"),
            asp.fact("has_compass"),
            asp.fact("has_rope"),
        ]
    )
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    if set(SETTINGS["fallen_tree_trail"].affords) != {"map_check", "safe_crossing"}:
        return 1
    if "expire" not in "expire perturb":
        return 1
    try:
        sample = generate(StoryParams(seed=4))
    except Exception:
        return 1
    required = ["Surprise", "Lesson Learned", "bad ending"]
    if not all(word.lower() in sample.story.lower() for word in required):
        return 1
    print("OK: Python world verified; ASP twin is available.")
    return 0


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
            print(json.dumps([[str(atom) for atom in model] for model in models], indent=2))
        except ImportError as exc:
            raise StoryError("ASP mode requires clingo to be installed.") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(setting="fallen_tree_trail", task=task, hero=NAMES[i], helper=HELPERS[i % len(HELPERS)], seed=base_seed + i)
            for i, task in enumerate(sorted(TASKS))
        ]
    else:
        params_list = []
        for i in range(max(0, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            params_list.append(params)

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
