#!/usr/bin/env python3
"""
Standalone story world: a small space adventure about push-dim bravery and kindness.

Luna must push a dim little signal lamp through a shadowed moon station. Her
inner monologue tells the truth about her fear, but a kind choice helps another
traveler and changes what she does.
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
    place: str
    affordances: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    companion_name: str
    companion_role: str
    mission: str
    obstacle: str
    opening_variant: int = 0
    response_variant: int = 0
    ending_variant: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "moon_station": Setting(
        id="moon_station",
        place="the Moon's quiet repair station",
        affordances={"low_gravity", "dim_corridors", "emergency_lamps", "kind_help"},
    ),
}

MISSIONS = {
    "guide_signal": {
        "label": "guide the lost supply robot",
        "object": "a little supply robot",
        "need": "its navigation light has gone dark",
        "goal": "carry a push-dim signal lamp to the far docking door",
        "result": "the robot can see the docking stripe and rolls safely home",
    },
    "deliver_star_map": {
        "label": "deliver a star map",
        "object": "a young stargazer",
        "need": "the viewing dome has lost its last working lamp",
        "goal": "push a dim signal lamp across the shadowed passage",
        "result": "the stargazer finds the blue star marked on the map",
    },
    "wake_beacon": {
        "label": "wake the rescue beacon",
        "object": "a tired rescue pilot",
        "need": "the beacon room is dark and its switch is far away",
        "goal": "push a dim lamp through the drifting dust",
        "result": "the rescue beacon blinks across the silent crater",
    },
}

OBSTACLES = {
    "meteor_dust": "a soft cloud of meteor dust swirled across the passage",
    "loose_crates": "two loose cargo crates slid toward the airlock",
    "shadow_bridge": "the bridge lights flickered until only a narrow path remained",
    "moon_rope": "a safety rope floated loose above the floor",
}

CHILD_NAMES = {
    "girl": ["Luna", "Mira", "Nia", "Zara"],
    "boy": ["Leo", "Milo", "Ari", "Kai"],
}

COMPANIONS = [
    ("Nova", "older sister"),
    ("Juno", "station guide"),
    ("Sol", "friendly pilot"),
    ("Tess", "robot helper"),
]

OPENINGS = [
    "{child} arrived at {place} while the stars shone through the round windows.",
    "The Moon's repair station hummed softly when {child} floated into the main hall.",
    "Beyond the airlock, {child} saw Earth shining like a blue marble.",
    "A silver alarm blinked once as {child} entered {place}.",
]

RESPONSES = [
    '"I am scared," {child} whispered. "But I can still choose the kind next step."',
    '{child} thought, "Bravery is not feeling nothing. It is helping while fear is here."',
    '"Stay close," said {companion}. {child} answered, "I will help first and worry while I move."',
    '{child} took a slow breath. Inside, a small brave voice said, "Push gently. Someone needs you."',
]

ENDINGS = [
    "The dim lamp glowed beside the safe doorway, and {child} felt bravery warm as a tiny star.",
    "When the station lights returned, {child} smiled at the quiet proof that kindness can guide a whole crew.",
    "Outside the window, Earth turned slowly while {child} learned that a brave heart can be gentle.",
    "The last light was small, but it was enough; everyone followed it home.",
]

WORLD_KNOWLEDGE = [
    QAItem(
        "What is a space station?",
        "A space station is a place in space where people and machines can live, work, and study.",
    ),
    QAItem(
        "What is bravery?",
        "Bravery is choosing a helpful or careful action even when something feels frightening.",
    ),
    QAItem(
        "What is an inner monologue?",
        "An inner monologue is the private stream of thoughts a character has inside their mind.",
    ),
    QAItem(
        "What does kindness mean?",
        "Kindness means noticing what someone needs and choosing to help without hurting them.",
    ),
    QAItem(
        "Why would a lamp be useful in a dark station?",
        "A lamp helps people and machines see paths, doors, and dangers in the dark.",
    ),
]


def valid_combo(setting: str, mission: str, obstacle: str) -> bool:
    return setting in SETTINGS and mission in MISSIONS and obstacle in OBSTACLES


def explain_rejection(setting: str, mission: str, obstacle: str) -> str:
    return (
        f"Invalid story choice: {setting}, {mission}, and {obstacle} do not form "
        "a supported space-station problem."
    )


def tell(params: StoryParams) -> World:
    if not valid_combo(params.setting, params.mission, params.obstacle):
        raise StoryError(explain_rejection(params.setting, params.mission, params.obstacle))

    setting = SETTINGS[params.setting]
    mission = MISSIONS[params.mission]
    obstacle = OBSTACLES[params.obstacle]
    world = World(setting)

    child = world.add(
        Entity(
            params.child_name,
            "character",
            params.child_name,
            meters={"fear": 0.4, "care": 1.0},
            memes={"bravery": 0.0, "kindness": 1.0},
        )
    )
    companion = world.add(
        Entity(
            params.companion_name,
            "character",
            params.companion_name,
            meters={"calm": 1.0},
            memes={"trust": 1.0},
        )
    )
    lamp = world.add(
        Entity(
            "push_dim_lamp",
            "tool",
            "a push-dim signal lamp",
            meters={"brightness": 0.3, "weight": 0.2},
            memes={"hope": 1.0},
        )
    )
    traveler = world.add(
        Entity(
            "traveler",
            "helper",
            mission["object"],
            meters={"need": 1.0},
            memes={"worry": 1.0},
        )
    )

    child_pronoun = "she" if params.child_gender == "girl" else "he"
    child_object = "her" if params.child_gender == "girl" else "him"

    world.say(
        OPENINGS[params.opening_variant % len(OPENINGS)].format(
            child=params.child_name, place=setting.place
        )
    )
    world.say(
        f"{params.child_name} was on a mission to {mission['goal']}. "
        f"Nearby, {mission['object']} waited because {mission['need']}."
    )
    world.say(
        f"{params.companion_name} pointed to the push-dim signal lamp. "
        f"It was not bright, but its soft glow could mark a safe route."
    )

    world.para()
    world.say(f"Then {obstacle}. The lamp bumped against a rail and its glow grew dimmer.")
    world.say(
        f"{params.child_name} felt {child_object} hands tremble. "
        f"Inside, {child_pronoun} thought, "
        f'"What if I cannot cross? What if I make the dark worse?"'
    )
    world.say(
        f"{params.companion_name} called, “We can turn back.” "
        f"{params.child_name} answered, “You are right that it is scary, but {mission['object']} still needs help.”"
    )
    world.facts["problem"] = obstacle
    world.facts["inner_monologue"] = True
    world.fired.add("fear_named")

    world.para()
    world.say(
        RESPONSES[params.response_variant % len(RESPONSES)].format(
            child=params.child_name, companion=params.companion_name
        )
    )
    world.say(
        f"{params.child_name} pushed the lamp slowly instead of throwing it ahead. "
        f"{params.companion_name} held the rope, and together they made a safe little line of light."
    )
    world.say(
        f"When the lamp reached {mission['object']}, {params.child_name} gave away "
        f"the warmest side of the glow and waited until the traveler was steady."
    )
    world.say(f"Because of that kindness, {mission['result']}.")
    child.meters["fear"] = 0.1
    child.meters["care"] = 2.0
    child.memes["bravery"] = 1.0
    child.memes["kindness"] = 2.0
    traveler.meters["need"] = 0.0
    traveler.memes["relief"] = 1.0
    lamp.meters["brightness"] = 0.5
    world.facts["resolved"] = True
    world.fired.update({"push_dim", "kindness", "mission_complete"})

    world.para()
    world.say(
        ENDINGS[params.ending_variant % len(ENDINGS)].format(child=params.child_name)
    )
    world.facts.update(
        child=child,
        companion=companion,
        lamp=lamp,
        traveler=traveler,
        mission=mission,
        obstacle=obstacle,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        "Write a child-friendly Space Adventure about a push-dim lamp, Bravery, Inner Monologue, and Kindness.",
        f"Show how {child.id} feels afraid in a dark space station, thinks privately, and chooses a helpful action.",
        f"Tell a complete story in which a dim lamp helps {f['traveler'].label} reach safety.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    companion = f["companion"]
    traveler = f["traveler"]
    mission = f["mission"]
    return [
        QAItem(
            f"What was {child.id}'s mission?",
            f"{child.id} had to {mission['goal']} because {traveler.label} needed help. "
            f"The push-dim signal lamp marked the route.",
        ),
        QAItem(
            "What made the mission frightening?",
            f"{f['obstacle'].capitalize()}. The lamp grew dim, so the passage looked unsafe and "
            f"the child had to name the fear instead of pretending it was not there.",
        ),
        QAItem(
            f"What did {child.id} think inside?",
            f"{child.id} had an inner monologue about being afraid and wondering whether the dark "
            "would become worse. That honest thought helped the child choose a careful next step.",
        ),
        QAItem(
            f"How did {child.id} show bravery and kindness?",
            f"{child.id} pushed the lamp slowly, accepted {companion.id}'s help, and shared the "
            f"lamp's glow with {traveler.label}. The traveler reached safety because the child helped first.",
        ),
        QAItem(
            "What changed by the end?",
            f"The traveler was safe, the route was marked, and the child's fear became smaller. "
            "The story showed that bravery can include careful kindness.",
        ),
    ]


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    lines.append(asp.fact("tool", "push_dim"))
    lines.append(asp.fact("feature", "bravery"))
    lines.append(asp.fact("feature", "inner_monologue"))
    lines.append(asp.fact("feature", "kindness"))
    return "\n".join(lines)


ASP_RULES = r"""
supported_setting(moon_station).
supported_mission(guide_signal).
supported_mission(deliver_star_map).
supported_mission(wake_beacon).
supported_obstacle(meteor_dust).
supported_obstacle(loose_crates).
supported_obstacle(shadow_bridge).
supported_obstacle(moon_rope).

good_story(S, M, O) :-
    setting(S),
    mission(M),
    obstacle(O),
    tool(push_dim),
    feature(bravery),
    feature(inner_monologue),
    feature(kindness),
    supported_setting(S),
    supported_mission(M),
    supported_obstacle(O).
"""


def asp_program(show: str = "#show good_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = sorted(
        (setting, mission, obstacle)
        for setting in SETTINGS
        for mission in MISSIONS
        for obstacle in OBSTACLES
        if valid_combo(setting, mission, obstacle)
    )
    clingo = asp_valid_combos()
    if py != clingo:
        print("MISMATCH between Python and ASP gates")
        print("python:", py)
        print("asp:", clingo)
        return 1
    sample = generate(
        StoryParams(
            setting="moon_station",
            child_name="Luna",
            child_gender="girl",
            companion_name="Nova",
            companion_role="older sister",
            mission="guide_signal",
            obstacle="meteor_dust",
        )
    )
    if "push-dim" not in sample.story or "bravery" not in sample.story.lower():
        print("Generated story exercise failed.")
        return 1
    print(f"OK: ASP/Python parity holds ({len(py)} combinations); story exercised.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space Adventure about a push-dim lamp, bravery, inner monologue, and kindness."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--mission", choices=MISSIONS)
    parser.add_argument("--obstacle", choices=OBSTACLES)
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--role")
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
    setting = args.setting or "moon_station"
    mission = args.mission or rng.choice(list(MISSIONS))
    obstacle = args.obstacle or rng.choice(list(OBSTACLES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES[gender])
    companion_name, companion_role = rng.choice(COMPANIONS)
    if args.companion:
        companion_name = args.companion
    if args.role:
        companion_role = args.role
    if not valid_combo(setting, mission, obstacle):
        raise StoryError(explain_rejection(setting, mission, obstacle))
    return StoryParams(
        setting=setting,
        child_name=name,
        child_gender=gender,
        companion_name=companion_name,
        companion_role=companion_role,
        mission=mission,
        obstacle=obstacle,
        opening_variant=rng.randrange(len(OPENINGS)),
        response_variant=rng.randrange(len(RESPONSES)),
        ending_variant=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=list(WORLD_KNOWLEDGE),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            f"{entity.id}: kind={entity.kind}, meters={meters}, memes={memes}"
        )
    lines.append(f"fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(
            setting="moon_station",
            child_name="Luna",
            child_gender="girl",
            companion_name="Nova",
            companion_role="older sister",
            mission="guide_signal",
            obstacle="meteor_dust",
        ),
        StoryParams(
            setting="moon_station",
            child_name="Leo",
            child_gender="boy",
            companion_name="Juno",
            companion_role="station guide",
            mission="deliver_star_map",
            obstacle="shadow_bridge",
        ),
        StoryParams(
            setting="moon_station",
            child_name="Mira",
            child_gender="girl",
            companion_name="Sol",
            companion_role="friendly pilot",
            mission="wake_beacon",
            obstacle="loose_crates",
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
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
        header = ""
        if args.all:
            header = (
                f"### {sample.params.child_name}: "
                f"{sample.params.mission} in {sample.params.setting}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
