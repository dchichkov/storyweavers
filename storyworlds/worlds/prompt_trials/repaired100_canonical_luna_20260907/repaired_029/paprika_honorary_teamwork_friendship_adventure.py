#!/usr/bin/env python3
"""
A small adventure storyworld about Paprika, an honorary helper, teamwork, and friendship.
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
    location: str = ""

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    landmark: str
    affordance: str


@dataclass(frozen=True)
class Challenge:
    id: str
    obstacle: str
    risk: str
    clue: str
    tool: str
    teamwork: str
    resolution: str
    ending: str


@dataclass
class World:
    setting: Setting
    challenge: Challenge
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "red_canyon": Setting(
        "red_canyon",
        "the Red Canyon",
        "a narrow bridge above a whispering river",
        "follow bright trail marks",
    ),
    "sunlit_ruins": Setting(
        "sunlit_ruins",
        "the Sunlit Ruins",
        "an old stone tower covered with vines",
        "search ancient paths",
    ),
    "whispering_forest": Setting(
        "whispering_forest",
        "the Whispering Forest",
        "a mossy arch where the trees leaned together",
        "listen for hidden directions",
    ),
}

CHALLENGES = {
    "fallen_bridge": Challenge(
        "fallen_bridge",
        "a storm had knocked a wooden bridge loose across the river",
        "one wrong pull could send the bridge spinning into the water",
        "the strongest rope was still tied to a flat stone on the far bank",
        "a coil of red climbing rope",
        "held the rope steady while Paprika guided the bridge plank by plank",
        "the bridge settled safely into its stone hooks",
        "Paprika and the friends crossed together, with the river shining below",
    ),
    "silent_beacon": Challenge(
        "silent_beacon",
        "the tower beacon had gone dark before it could guide lost travelers",
        "climbing too quickly could loosen the cracked stones",
        "three clean mirrors pointed toward a hidden box of dry flint",
        "a brass mirror and a pouch of flint",
        "one friend watched the stones while another turned the mirror toward the beacon",
        "the beacon sprang to life and sent a warm beam over the hills",
        "their light blinked back at a distant traveler who had found the path",
    ),
    "lost_compass": Challenge(
        "lost_compass",
        "the forest compass had slipped beneath a carpet of fallen leaves",
        "rushing through the leaves could bury the compass even deeper",
        "a blue feather marked the place where the leaves had moved",
        "a slender walking stick",
        "searched in small circles while the friends marked every cleared patch",
        "the compass gleamed beside an old root",
        "the recovered needle pointed home as the trees whispered a welcome",
    ),
}

NAMES = ["Luna", "Milo", "Tavi", "Nia", "Orin"]
FRIENDS = ["Pip", "Suri", "Bram", "Kiko", "Mara"]


@dataclass(frozen=True)
class StoryParams:
    setting: str
    challenge: str
    name: str
    friend: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, challenge) for setting in SETTINGS for challenge in CHALLENGES]


def _choose(mapping: dict, value: Optional[str], label: str):
    if value is None:
        return None
    if value not in mapping:
        raise StoryError(f"Unknown {label} '{value}'. Choose one of: {', '.join(mapping)}.")
    return mapping[value]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    challenge = args.challenge or rng.choice(list(CHALLENGES))
    _choose(SETTINGS, setting, "setting")
    _choose(CHALLENGES, challenge, "challenge")
    return StoryParams(
        setting=setting,
        challenge=challenge,
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        seed=args.seed,
    )


def build_world(params: StoryParams, rng: random.Random) -> World:
    setting = SETTINGS[params.setting]
    challenge = CHALLENGES[params.challenge]
    world = World(setting, challenge)

    luna = world.add(Entity("luna", "hero", params.name, location=setting.id))
    friend = world.add(Entity("friend", "friend", params.friend, location=setting.id))
    paprika = world.add(Entity("paprika", "companion", "Paprika", location=setting.id))
    obstacle = world.add(Entity("obstacle", "obstacle", challenge.obstacle, location=setting.id))

    luna.add_meme("curiosity")
    friend.add_meme("friendship")
    paprika.add_meme("loyalty")
    obstacle.add_meter("danger", 1.0)

    world.facts.update(
        hero=luna,
        friend=friend,
        paprika=paprika,
        obstacle=obstacle,
        tool=challenge.tool,
        clue=challenge.clue,
        risk=challenge.risk,
        teamwork=challenge.teamwork,
        resolution=challenge.resolution,
        ending=challenge.ending,
    )

    world.say(
        f"{luna.label} was an adventurous traveler who never ignored a path that led somewhere new."
    )
    world.say(
        f"At {setting.label}, {luna.label} met {friend.label} and Paprika, a small companion with a brave red scarf."
    )
    world.say(
        f"Paprika had been named an honorary member of their team because Paprika always noticed details others missed."
    )
    world.say(
        f"Together they hoped to {setting.affordance}, but {challenge.obstacle}."
    )

    world.paragraph()
    world.say(f'"We can fix it," said {luna.label}. "But we must work together."')
    world.say(f'"I will watch the risky part," said {friend.label}. "Paprika can search for a clue."')
    world.say(f'Paprika chirped, "And you can lead us, {luna.label}!"')
    world.say(
        f"Their words changed the plan. Instead of rushing, they studied the trouble and discovered that {challenge.clue}."
    )
    luna.add_meter("observed")
    paprika.add_meter("noticed_clue")
    friend.add_meme("trust")

    world.paragraph()
    world.say(
        f"Using {challenge.tool}, {luna.label} began carefully. {challenge.teamwork}."
    )
    world.say(
        f"Each friend had a different job, yet every job protected the others."
    )
    luna.add_meme("teamwork")
    friend.add_meme("teamwork")
    paprika.add_meme("teamwork")
    obstacle.meters["danger"] = 0.0
    world.events.append("teamwork_completed")

    world.paragraph()
    world.say(f"Their careful plan worked: {challenge.resolution}.")
    world.say(
        f"{luna.label} smiled at Paprika. \"You are not just honorary,\" she said. \"You are our friend and a real part of the team.\""
    )
    world.say(f"Paprika leaned against {friend.label}, and {friend.label} laughed.")
    world.say(f"In the end, {challenge.ending}.")
    luna.add_meme("joy")
    friend.add_meme("joy")
    paprika.add_meme("belonging")
    world.events.append("friendship_strengthened")

    return world


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else f"{params.name}:{params.setting}:{params.challenge}")
    world = build_world(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    return [
        f"Write an adventure story about {hero.label}, {friend.label}, and Paprika exploring {world.setting.label}.",
        f"Show how teamwork solves this problem: {world.challenge.obstacle}.",
        f"Include friendship and explain why Paprika becomes an honorary member of the team.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    return [
        QAItem(
            f"Where did {hero.label}, {friend.label}, and Paprika go?",
            f"They went to {world.setting.label}, where they hoped to {world.setting.affordance}.",
        ),
        QAItem(
            "What problem did the team face?",
            f"They faced a problem because {world.challenge.obstacle}.",
        ),
        QAItem(
            "What clue helped them make a safe plan?",
            f"They noticed that {world.challenge.clue}.",
        ),
        QAItem(
            "How did teamwork solve the problem?",
            f"{hero.label}, {friend.label}, and Paprika shared different jobs: {world.challenge.teamwork}.",
        ),
        QAItem(
            "Why was Paprika called honorary?",
            f"Paprika was called honorary because Paprika noticed important details, helped the friends, and became a trusted part of their team.",
        ),
        QAItem(
            "How did the adventure end?",
            f"The plan worked because {world.challenge.resolution}; {world.challenge.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is teamwork?",
            "Teamwork is when people share jobs, listen to one another, and work toward the same goal.",
        ),
        QAItem(
            "What is friendship?",
            "Friendship is a caring connection in which friends help, trust, and enjoy time with one another.",
        ),
        QAItem(
            "What does honorary mean?",
            "Honorary means receiving a special title or welcome as a sign of respect, even when the title is not a regular job.",
        ),
        QAItem(
            "What is paprika?",
            "Paprika is a red spice made from dried peppers, and it can also be used as a cheerful name for a story character.",
        ),
        QAItem(
            "What makes an adventure?",
            "An adventure is an exciting journey with a challenge, a choice, and something new to discover.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
            f"  {entity.label:24} kind={entity.kind:10} "
            f"location={entity.location:18} meters={meters} memes={memes}"
        )
    lines.append(f"  events: {world.events}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(S, C) :- setting(S), challenge(C).
honorary_member(paprika).
teamwork(S, C) :- valid(S, C).
friendship(S, C) :- valid(S, C).
adventure(S, C) :- valid(S, C), teamwork(S, C), friendship(S, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for challenge in CHALLENGES:
        lines.append(asp.fact("challenge", challenge))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected != actual:
        print("ASP/Python mismatch.")
        print("Only in ASP:", sorted(actual - expected))
        print("Only in Python:", sorted(expected - actual))
        return 1
    for combo in sorted(expected):
        params = StoryParams(combo[0], combo[1], "Luna", "Pip", seed=7)
        sample = generate(params)
        if "Paprika" not in sample.story or "team" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP matches Python for {len(expected)} combinations, and generated stories passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="An adventure world about Paprika, honorary friendship, and teamwork."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--challenge", choices=sorted(CHALLENGES))
    parser.add_argument("--name")
    parser.add_argument("--friend")
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


CURATED = [
    StoryParams("red_canyon", "fallen_bridge", "Luna", "Pip", 101),
    StoryParams("sunlit_ruins", "silent_beacon", "Milo", "Suri", 202),
    StoryParams("whispering_forest", "lost_compass", "Nia", "Bram", 303),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid adventure combinations:")
        for combo in combos:
            print(" ", combo)
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        for index in range(args.n):
            seed = base_seed + index
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
            sample = generate(params)
            if sample.story not in seen:
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
