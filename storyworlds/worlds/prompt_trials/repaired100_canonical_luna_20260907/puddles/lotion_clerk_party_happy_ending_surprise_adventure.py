#!/usr/bin/env python3
"""Luna's lotion-clerk party adventure."""

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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Clerk:
    name: str
    lotion: str
    ready: bool = False
    helped: bool = False
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: str
    clerk: Clerk
    place: str
    party: str
    paragraphs: list[str] = field(default_factory=list)
    history: list[tuple[str, str, str]] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    surprise: str = ""

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def event(self, kind: str, cause: str, result: str, text: str) -> None:
        self.history.append((kind, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


@dataclass
class StoryParams:
    hero: str = "Luna"
    clerk: str = "Mara"
    lotion: str = "sunflower lotion"
    place: str = "the little shop beside the park"
    party: str = "a garden party"
    seed: int | None = None


HEROES = ["Luna", "Milo", "Nia", "Theo", "Pia"]
CLERKS = ["Mara", "Owen", "Tess", "Ari"]
LOTION = ["sunflower lotion", "mint lotion", "orange-blossom lotion"]
PARTIES = ["a garden party", "a moonlight party", "a picnic party"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A small lotion-clerk party adventure.")
    parser.add_argument("--hero")
    parser.add_argument("--clerk")
    parser.add_argument("--lotion")
    parser.add_argument("--party")
    parser.add_argument("--place", default="the little shop beside the park")
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
    hero = args.hero or rng.choice(HEROES)
    clerk = args.clerk or rng.choice(CLERKS)
    lotion = args.lotion or rng.choice(LOTION)
    party = args.party or rng.choice(PARTIES)
    if hero == clerk:
        raise StoryError("The hero and clerk need different names.")
    return StoryParams(hero=hero, clerk=clerk, lotion=lotion, party=party,
                       place=args.place, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.clerk:
        raise StoryError("The hero and clerk need different names.")
    if not params.lotion.endswith("lotion"):
        raise StoryError("The shop must offer a lotion.")
    clerk = Clerk(params.clerk, params.lotion, memes={"care": 1.0})
    world = World(
        hero=params.hero,
        clerk=clerk,
        place=params.place,
        party=params.party,
        meters={"coins": 1.0, "lotion": 0.0, "party_ready": 0.0},
        memes={"hope": 1.0, "courage": 0.0, "joy": 0.0},
    )

    world.event(
        "arrival",
        f"{params.hero} needed a kind idea before {params.party}.",
        f"{params.hero} entered {params.place}.",
        f"{params.hero} hurried to {params.place}, carrying a tiny invitation to {params.party}. "
        f"The party was close, but one problem made the invitation feel heavy: "
        f"the guest of honor had no lotion for the sunny walk.",
    )
    world.event(
        "request",
        f"The party needed care, and the shop had a helpful clerk.",
        f"{params.clerk} offered {params.lotion}.",
        f'"Could you help me?" {params.hero} asked. '
        f'"I can," said {params.clerk}, the cheerful clerk behind the counter. '
        f'"Tell me what the party needs." {params.hero} explained the sunny path, '
        f'and {params.clerk} reached for a bottle of {params.lotion}.',
    )
    world.meters["lotion"] = 1.0
    world.meters["coins"] = 0.0
    world.memes["courage"] = 1.0
    world.event(
        "mixup",
        "A gust of wind swept the party invitation under a shelf.",
        "The route to the party disappeared from sight.",
        f'Just then, a gust whisked the invitation under a shelf. '
        f'"Oh no! Now we do not know where to go," {params.hero} said. '
        f'"Look for a clue," {params.clerk} replied. {params.hero} spotted a yellow ribbon '
        f'tied around the {params.lotion} bottle. It matched ribbons on the shop door.',
    )
    world.surprise = (
        f"The ribbon was a secret party marker, and {params.clerk} had been invited too."
    )
    world.memes["joy"] = 1.0
    world.meters["party_ready"] = 1.0
    clerk.ready = True
    clerk.helped = True
    world.event(
        "surprise",
        "The lotion bottle carried the party's hidden yellow ribbon.",
        f"{params.hero} and {params.clerk} found the party together.",
        f'"That ribbon is our path!" {params.hero} cried. '
        f'{params.clerk} laughed. "It is also a surprise. I was invited to help lead the games!" '
        f'Together they followed the ribbons past the flowers and found {params.party} glowing '
        f'under a tree. The lotion was shared before anyone began the sunny adventure.',
    )
    world.event(
        "ending",
        "The helper, the lotion, and the hidden clue solved the problem.",
        "Everyone entered the party smiling.",
        f'{params.hero} held the door for {params.clerk}, and the guests cheered. '
        f'They played a ribbon hunt, shared fruit, and followed a trail of bright flags. '
        f'At sunset, {params.hero} looked at the empty lotion bottle and smiled: '
        f'the little shop adventure had led to the happiest surprise of the day.'
    )

    prompts = [
        f"Write an Adventure story about {params.hero}, a clerk, lotion, and {params.party}.",
        "Include a surprise clue that helps the characters reach a happy ending.",
    ]
    story_qa = [
        QAItem("Why did the hero visit the shop?",
                f"{params.hero} visited {params.place} because the party needed lotion for the sunny walk."),
        QAItem("How did the characters find the party?",
                f"They followed the yellow ribbons, including the hidden ribbon tied to the lotion bottle."),
        QAItem("What was the surprise?",
                f"The clerk was invited to the party and became a leader of the games."),
        QAItem("How did the story end?",
                f"{params.hero} and the clerk reached the party, shared the lotion, and enjoyed games with everyone."),
    ]
    world_qa = [
        QAItem("What does lotion do?",
                "Lotion can help protect or soften skin when it is spread gently over it."),
        QAItem("What does a clerk do?",
                "A clerk helps people in a shop by answering questions and finding things they need."),
        QAItem("Why can a party feel special?",
                "A party feels special because people gather to celebrate, play, share, and enjoy one another's company."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts,
                        story_qa=story_qa, world_qa=world_qa, world=world)


ASP_RULES = r"""
helpful(clerk).
has_lotion(shop) :- lotion(lotion).
happy_ending(story) :- reaches_party(hero), shared_lotion(hero, clerk).
surprise(story) :- hidden_ribbon(lotion), invited(clerk).
valid_story :- helpful(clerk), has_lotion(shop), happy_ending(story), surprise(story).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("clerk", "clerk"),
        asp.fact("lotion", "lotion"),
        asp.fact("shop", "shop"),
        asp.fact("hero", "hero"),
        asp.fact("reaches_party", "hero"),
        asp.fact("shared_lotion", "hero", "clerk"),
        asp.fact("hidden_ribbon", "lotion"),
        asp.fact("invited", "clerk"),
    ])


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n#show valid_story/0.\n"


def dump_trace(world: World) -> str:
    return (
        "--- world model state ---\n"
        f"  hero: {world.hero}\n"
        f"  clerk: {world.clerk.name}, helped={world.clerk.helped}\n"
        f"  meters: {world.meters}\n"
        f"  memes: {world.memes}\n"
        f"  surprise: {world.surprise}\n"
        "--- events ---\n" +
        "\n".join(f"  {kind}: {cause} -> {result}"
                  for kind, cause, result in world.history)
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


def verify() -> int:
    sample = generate(StoryParams())
    if "lotion" not in sample.story or "clerk" not in sample.story or "party" not in sample.story:
        return 1
    if "surprise" not in sample.story.lower() and "surprise" not in sample.world.surprise.lower():
        return 1
    if sample.world.meters["party_ready"] != 1.0:
        return 1
    try:
        import asp
        model = asp.one_model(asp_program())
        if not asp.atoms(model, "valid_story"):
            return 1
    except ImportError:
        pass
    print("OK: lotion-clerk party story verified.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.verify:
        raise SystemExit(verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program())
            print("valid_story:", bool(asp.atoms(model, "valid_story")))
        except ImportError as exc:
            raise SystemExit("ASP mode requires clingo.") from exc
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    params_list = []
    for i in range(len(CURATED) if args.all else args.n):
        if args.all:
            params_list.append(CURATED[i])
        else:
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            params_list.append(params)

    samples = [generate(p) for p in params_list]
    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa,
             header=f"### adventure {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


CURATED = [
    StoryParams("Luna", "Mara", "sunflower lotion",
                "the little shop beside the park", "a garden party"),
    StoryParams("Milo", "Owen", "mint lotion",
                "the bright shop near the square", "a picnic party"),
    StoryParams("Nia", "Tess", "orange-blossom lotion",
                "the tiny shop by the hill", "a moonlight party"),
]


if __name__ == "__main__":
    main()
