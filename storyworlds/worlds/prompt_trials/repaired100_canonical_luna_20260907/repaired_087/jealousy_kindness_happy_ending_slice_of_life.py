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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    object_name: str


@dataclass(frozen=True)
class Gift:
    id: str
    label: str


@dataclass
class World:
    setting: Setting
    hero: str
    friend: str
    helper: str
    gift: Gift
    jealousy: float = 0.0
    kindness: float = 0.0
    shared: bool = False
    repaired: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "kitchen": Setting("kitchen", "the sunny kitchen", "a jar of buttons"),
    "porch": Setting("porch", "the little front porch", "a box of sidewalk chalk"),
    "bedroom": Setting("bedroom", "the shared bedroom", "a basket of colored pencils"),
}

GIFTS = {
    "bookmark": Gift("bookmark", "a blue bookmark with a gold star"),
    "bracelet": Gift("bracelet", "a small bracelet of red and yellow beads"),
    "card": Gift("card", "a hand-drawn card with a smiling moon"),
}

HERO_NAMES = ["Luna", "Mia", "Toby", "Nora"]
FRIEND_NAMES = ["Eli", "Sam", "Bea", "Owen"]
HELPER_NAMES = ["Grandma", "Aunt May", "Dad", "Mrs. Chen"]

SCENES = [
    {
        "object": "button jar",
        "setup": "Luna had spent the afternoon sorting the buttons by color for a craft project.",
        "trigger": "When Eli received the first bright button bracelet, Luna felt a hot little pinch of jealousy.",
        "clue": "She noticed that Eli kept glancing at the empty chair beside him.",
        "kind_line": '"You wanted one too," Eli said softly. "We can make yours together."',
        "repair": "Luna admitted that she had felt left out, and Eli moved the jar between them.",
        "ending": "Soon two bracelets clicked together whenever the children reached for another button.",
        "lesson": "Kindness can make room for another person without making anyone smaller.",
    },
    {
        "object": "chalk box",
        "setup": "Luna had drawn a tiny garden in chalk before Eli came to the porch.",
        "trigger": "Eli added a wonderful purple kite, and jealousy made Luna wish everyone would notice only her garden.",
        "clue": "She saw Eli leave a wide blank space beside the kite.",
        "kind_line": '"There is room for your flowers here," Eli said. "Then the kite can fly over them."',
        "repair": "Luna shared the yellow chalk and asked Eli to help connect the garden to the kite.",
        "ending": "By supper, the porch held one picture with flowers below and a purple kite above.",
        "lesson": "A shared idea can become brighter than either idea alone.",
    },
    {
        "object": "pencil basket",
        "setup": "Luna was making a moon picture when Eli began drawing a shining rocket beside it.",
        "trigger": "The rocket looked so exciting that jealousy made Luna hide her best silver pencil.",
        "clue": "Eli kept the moon empty because he hoped Luna would add its light.",
        "kind_line": '"Your moon is the part that guides my rocket," Eli said. "May we finish it together?"',
        "repair": "Luna returned the silver pencil and showed Eli how to shade a path of moonlight.",
        "ending": "Their picture rested on the wall, with the rocket sailing through the moon's gentle glow.",
        "lesson": "Another person's bright idea does not erase your own light.",
    },
]


@dataclass
class StoryParams:
    setting: str
    gift: str
    name: str
    friend: str
    helper: str
    seed: int | None = None


def reasonability_gate(setting: Setting, gift: Gift) -> bool:
    if not setting.place or not gift.label:
        raise StoryError("A story needs a real setting and a concrete gift.")
    return True


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.gift not in GIFTS:
        raise StoryError(f"Unknown gift: {params.gift}")
    setting = SETTINGS[params.setting]
    gift = GIFTS[params.gift]
    reasonability_gate(setting, gift)
    scene = SCENES[(params.seed or 0) % len(SCENES)]
    world = World(setting, params.name, params.friend, params.helper, gift)
    world.meters["distance"] = 0.0
    world.memes["trust"] = 0.0

    world.say(f"On an ordinary afternoon in {setting.place}, {params.name} and {params.friend} sat beside {scene['object']}.")
    world.say(scene["setup"])
    world.say(f"{params.helper} had brought {gift.label} for the children to use in their small project.")
    world.say(scene["trigger"])
    world.say(f"Luna's hands became quiet, even though the room was still full of small, familiar sounds.")

    world.para()
    world.say(f"{scene['clue']}")
    world.say(f'"Are you still having fun?" {params.friend} asked.')
    world.say(f'"I am glad for you, but I feel jealous and left out," {params.name} answered.')
    world.say(scene["kind_line"])
    world.say(f"{params.name} looked carefully at {params.friend}, and the answer changed what she decided to do.")
    world.say(scene["repair"])

    world.para()
    world.say(f"{params.helper} smiled and set {gift.label} where both children could reach it.")
    world.say(f"They took turns, offered pieces to each other, and laughed when {scene['object']} made a soft clatter.")
    world.say(scene["ending"])
    world.say(f"At the end of the day, {params.name} no longer had to hide the jealous feeling; kindness had given it somewhere gentle to go.")
    world.say(f"The happy ending was simple: {params.name} and {params.friend} went home proud of something they had made together.")

    world.jealousy = 0.0
    world.kindness = 1.0
    world.shared = True
    world.repaired = True
    world.memes["trust"] = 1.0
    world.facts.update(scene=scene, setting=setting, gift=gift, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    return [
        f"Write a slice-of-life story about {world.hero} feeling jealousy when {world.friend} receives attention.",
        f"Show how kindness helps {world.hero} and {world.friend} share {world.facts['gift'].label}.",
        f"End with a happy ending in {world.setting.place}: {scene['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    scene = world.facts["scene"]
    return [
        QAItem("Who felt jealous?", f"{world.hero} felt jealous when {world.friend}'s idea received attention."),
        QAItem("What did the friend notice?", scene["clue"]),
        QAItem("What did the children say to each other?", f'{world.friend} asked, "Are you still having fun?" {world.hero} answered honestly, and {world.friend} invited shared play.'),
        QAItem("How did kindness repair the moment?", scene["repair"]),
        QAItem("How did the story end?", scene["ending"] + " They went home proud of what they had made together."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is jealousy?", "Jealousy is an uncomfortable feeling that can appear when someone else seems to have something we want, such as attention or praise."),
        QAItem("How can kindness help with jealousy?", "Kindness can help by making space for honest words, sharing attention, and including everyone in a caring activity."),
        QAItem("What makes a happy ending?", "A happy ending shows that a problem has changed for the better and leaves the characters feeling connected or hopeful."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"  place: {world.setting.place}",
        f"  jealousy: {world.jealousy}",
        f"  kindness: {world.kindness}",
        f"  shared: {world.shared}",
        f"  repaired: {world.repaired}",
        f"  memes: {world.memes}",
    ])


ASP_RULES = r"""
jealousy_present :- feeling(jealousy).
kindness_repairs :- feeling(jealousy), action(kindness), shared.
happy_ending :- kindness_repairs, repaired.
valid_story :- jealousy_present, happy_ending.
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("feeling", "jealousy"),
        asp.fact("action", "kindness"),
        asp.fact("shared"),
        asp.fact("repaired"),
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        valid = bool(asp.atoms(model, "valid_story"))
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if not valid:
        print("ASP did not find a valid story.")
        return 1
    sample = generate(StoryParams("kitchen", "bookmark", "Luna", "Eli", "Grandma", 0))
    if "jealous" not in sample.story.lower() or "kindness" not in sample.story.lower():
        print("Generated story failed narrative verification.")
        return 1
    print("OK: ASP and Python story gate agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A slice-of-life world about jealousy, kindness, and a happy ending.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--gift", choices=GIFTS)
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
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
        setting=args.setting or rng.choice(list(SETTINGS)),
        gift=args.gift or rng.choice(list(GIFTS)),
        name=args.name or rng.choice(HERO_NAMES),
        friend=args.friend or rng.choice(FRIEND_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        seed=args.seed,
    )


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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("kitchen", "bookmark", "Luna", "Eli", "Grandma", 0),
    StoryParams("porch", "bracelet", "Luna", "Bea", "Aunt May", 1),
    StoryParams("bedroom", "card", "Luna", "Owen", "Dad", 2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print(asp.atoms(asp.one_model(asp_program()), "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
