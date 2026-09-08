#!/usr/bin/env python3
"""
A small superhero story world about a grizzly, a careful search, and a happy ending.
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

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    grizzly_name: str
    setting: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    grizzly: Character
    setting: str
    quest: str = ""
    threat: str = ""
    clue: str = ""
    tool: str = ""
    safe: bool = False
    happy: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


HERO_NAMES = ["Luna", "Nova", "Mira", "Sol", "Pip", "Juno", "Tess"]
GRIZZLY_NAMES = ["Brumble", "Honey", "Granite", "Boulder", "Moss", "Rumble", "Cedar"]
SETTINGS = [
    "the moonlit forest",
    "the bright mountain town",
    "the old ranger station",
    "the cloud bridge",
    "the silver valley",
]

QUESTS = [
    {
        "problem": "a runaway beacon was blinking beside the grizzly's den",
        "risk": "the beacon's hot signal could frighten the grizzly toward the village",
        "clue": "three warm footprints curved away from the beacon and toward a creek",
        "tool": "a cool blue lantern",
        "search": "scoured the trail from the creek back to the beacon",
        "turn": "the beacon was not calling a villain; it was warning of a fallen tree across the bear path",
        "fix": "used the blue lantern to guide the grizzly around the fallen tree, then switched off the beacon",
        "ending": "the grizzly settled beneath a pine while the beacon rested dark and cool",
    },
    {
        "problem": "a storm gate had locked near the grizzly's food meadow",
        "risk": "rising water could trap the grizzly between the gate and the river",
        "clue": "a line of floating leaves showed that the safest dry path led behind the gate",
        "tool": "a silver rescue rope",
        "search": "scoured the gatehouse floor for the missing release pin",
        "turn": "the gate had not jammed by itself; a loose branch had wedged the pin beneath a crate",
        "fix": "pulled the branch free with the rescue rope and opened a quiet path to higher ground",
        "ending": "the river flowed safely below as the grizzly munched berries on the sunny hill",
    },
    {
        "problem": "a loud training robot had rolled into the grizzly's berry patch",
        "risk": "its flashing wheels could make the grizzly charge into a rocky ravine",
        "clue": "the robot's wheel tracks stopped where a small red button had fallen in the grass",
        "tool": "a soft hero cape",
        "search": "scoured the berry patch without stepping on the hidden button",
        "turn": "the robot's roaring voice was only a stuck greeting, not a monster's attack",
        "fix": "covered the wheels with the soft cape, pressed the red button, and led the robot away",
        "ending": "the robot whispered good night while the grizzly picked berries in peace",
    },
    {
        "problem": "a golden bridge charm had vanished from the grizzly's trail",
        "risk": "without the charm, the bridge lights might terminate and leave travelers in the dark",
        "clue": "tiny gold flecks ran from the bridge to a hollow log",
        "tool": "a pocket star compass",
        "search": "scoured the hollow log with the star compass glowing over each fleck",
        "turn": "the charm had not been stolen; a magpie had carried it away to line a nest",
        "fix": "traded the magpie a bright ribbon and returned the charm to the bridge",
        "ending": "the bridge shone again, and the grizzly watched the ribbon dance in its new nest",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero grizzly quest story world.")
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--grizzly-name", choices=GRIZZLY_NAMES)
    parser.add_argument("--setting", choices=SETTINGS)
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
    hero = args.hero_name or rng.choice(HERO_NAMES)
    grizzly = args.grizzly_name or rng.choice([n for n in GRIZZLY_NAMES if n != hero])
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(hero_name=hero, grizzly_name=grizzly, setting=setting)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.grizzly_name:
        raise StoryError("The hero and grizzly need different names.")
    if params.setting not in SETTINGS:
        raise StoryError("That setting is not part of this superhero world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    quest = rng.choice(QUESTS)

    hero = Character(
        name=params.hero_name,
        kind="superhero",
        meters={"energy": 8.0, "distance_to_danger": 4.0},
        memes={"courage": 1.0, "kindness": 1.0, "curiosity": 1.0},
    )
    grizzly = Character(
        name=params.grizzly_name,
        kind="grizzly",
        meters={"calm": 4.0, "distance_to_safe_ground": 3.0},
        memes={"trust": 0.4, "hunger": 0.5},
    )
    world = World(hero=hero, grizzly=grizzly, setting=params.setting)
    world.quest = quest["problem"]
    world.threat = quest["risk"]
    world.clue = quest["clue"]
    world.tool = quest["tool"]

    inner = rng.choice([
        f"{hero.name} thought, \"A real hero must protect the grizzly before chasing glory.\"",
        f"{hero.name} thought, \"I feel worried, but I can slow down and look for a safe clue.\"",
        f"{hero.name} told themself, \"Kindness is my strongest superpower today.\"",
        f"{hero.name} thought, \"I will not rush. I will listen, search, and help.\"",
    ])
    dialogue = rng.choice([
        f"\"Stay behind me, {grizzly.name},\" said {hero.name}. \"Can you show me where the trouble began?\" "
        f"The grizzly sniffed the trail and stepped toward the clue.",
        f"\"Are you hurt?\" asked {hero.name}. \"I will help without frightening you.\" "
        f"{grizzly.name} lowered its head, then pointed the way with one careful paw.",
        f"\"The loud sound is scary,\" said {hero.name}. \"But we can solve it together.\" "
        f"{grizzly.name} gave a deep, gentle huff and waited.",
    ])

    lines = [
        f"In {params.setting}, {hero.name} was a young superhero who watched over every creature.",
        f"One bright morning, {quest['problem']}.",
        f"The trouble was serious because {quest['risk']}.",
        inner,
        dialogue,
        f"Instead of rushing in, {hero.name} carried {quest['tool']} and {quest['search']}.",
        f"The search revealed the important turn: {quest['turn']}.",
        f"\"Now I know what to do,\" said {hero.name}. \"We can make this safe.\"",
        f"{hero.name} {quest['fix']}.",
        "The danger was ended, and the frightened path became peaceful again.",
        f"That evening, {hero.name} smiled because the quest had protected a friend, not merely defeated a threat.",
        f"At last, {quest['ending']}.",
    ]

    world.safe = True
    world.happy = True
    hero.meters["distance_to_danger"] = 0.0
    grizzly.meters["calm"] = 9.0
    grizzly.meters["distance_to_safe_ground"] = 0.0
    world.facts.update({
        "story": " ".join(lines),
        "problem": quest["problem"],
        "risk": quest["risk"],
        "clue": quest["clue"],
        "repair": quest["fix"],
        "ending": quest["ending"],
    })

    prompts = [
        f"Write a Superhero Story about {hero.name} helping {grizzly.name} in {params.setting}.",
        f"Create a quest where a hero must scour the scene, understand the danger, and terminate the threat safely.",
        "Include an inner monologue, a brief dialogue exchange, and a happy ending.",
    ]
    story_qa = [
        QAItem(
            question=f"What danger did {hero.name} discover near {grizzly.name}?",
            answer=f"{hero.name} discovered that {quest['problem']}, and {quest['risk']}.",
        ),
        QAItem(
            question="What did the hero think before acting?",
            answer=inner,
        ),
        QAItem(
            question="What clue changed the hero's plan?",
            answer=f"The clue was that {quest['clue']}.",
        ),
        QAItem(
            question="How did the hero terminate the danger?",
            answer=f"{hero.name} {quest['fix']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily when {quest['ending']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear that needs space, food, and safe wild places.",
        ),
        QAItem(
            question="What does it mean to scour a place?",
            answer="To scour a place means to search it carefully and thoroughly.",
        ),
        QAItem(
            question="What does terminate mean in this story?",
            answer="Here, terminate means to bring the danger or harmful action to an end.",
        ),
        QAItem(
            question="What makes a superhero's quest responsible?",
            answer="A responsible quest protects living creatures, checks clues, and solves danger without creating new harm.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending shows that the danger has passed and the characters are safe, relieved, or joyful.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n--- trace ---")
        w = sample.world
        print(f"hero={w.hero.name}, kind={w.hero.kind}, meters={w.hero.meters}, memes={w.hero.memes}")
        print(f"grizzly={w.grizzly.name}, kind={w.grizzly.kind}, meters={w.grizzly.meters}, memes={w.grizzly.memes}")
        print(f"setting={w.setting}, quest={w.quest}, safe={w.safe}, happy={w.happy}")
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
valid_setting(S) :- setting(S).
safe_quest :- hero(H), grizzly(G), H != G, setting(S), S != "".
happy_ending :- safe_quest.
#show valid_setting/1.
#show safe_quest/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("setting", setting) for setting in SETTINGS]
    facts += [asp.fact("hero", "luna"), asp.fact("grizzly", "brumble")]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    py = {(setting,) for setting in SETTINGS}
    model = asp.one_model(asp_program("#show valid_setting/1."))
    cl = set(asp.atoms(model, "valid_setting"))
    if py != cl:
        print("MISMATCH between Python and ASP settings.")
        return 1
    model = asp.one_model(asp_program("#show safe_quest/0.\n#show happy_ending/0."))
    if not asp.atoms(model, "safe_quest") or not asp.atoms(model, "happy_ending"):
        print("MISMATCH: ASP did not derive the safe happy quest.")
        return 1
    for params in [
        StoryParams("Luna", "Brumble", SETTINGS[0], 1),
        StoryParams("Nova", "Moss", SETTINGS[1], 2),
    ]:
        sample = generate(params)
        if not sample.world or not sample.world.safe or not sample.world.happy:
            print("Generated story failed the safety and happiness check.")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(SETTINGS)} settings).")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(HERO_NAMES[i % len(HERO_NAMES)], GRIZZLY_NAMES[i % len(GRIZZLY_NAMES)], setting)
            for i, setting in enumerate(SETTINGS)
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_setting/1.\n#show safe_quest/0.\n#show happy_ending/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_setting/1."))
        for setting in sorted(asp.atoms(model, "valid_setting")):
            print(setting[0])
        return

    samples = []
    for i, params in enumerate(generation_params(args)):
        params.seed = (args.seed if args.seed is not None else 0) + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
