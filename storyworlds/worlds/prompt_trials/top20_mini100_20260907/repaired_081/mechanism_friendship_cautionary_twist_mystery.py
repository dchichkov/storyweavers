#!/usr/bin/env python3
"""
A small mystery story world about a mechanism, friendship, caution, and a twist.

The domain is intentionally tiny: two friends discover that a little machine has
stopped behaving as expected. They investigate, speak with each other, test
carefully, and uncover a surprising but gentle twist that changes what they
thought the mechanism was doing.
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
    kind: str
    label: str
    phrase: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    setting: str = "workshop"
    hero_name: str = "Mina"
    friend_name: str = "Toby"
    mechanism: str = "clockwork drawer"
    twist: str = "it was helping"
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "workshop": "the small back room full of shelves and toolboxes",
    "library": "the quiet reading nook beside the tall bookshelves",
    "greenhouse": "the warm room with damp pots and window light",
    "attic": "the dusty attic with a round window and old trunks",
    "station": "the little station office with a humming lamp",
}

HERO_NAMES = ["Mina", "Levi", "Iris", "Noah", "Pia"]
FRIEND_NAMES = ["Toby", "Sana", "Jae", "Lina", "Omar"]

MECHANISMS = {
    "clockwork drawer": {
        "premise": "A small drawer kept sliding open by itself, even after Mina shut it carefully.",
        "mistake": "At first, Mina pushed it harder, but the drawer popped open again with the same soft click.",
        "clue": "Toby noticed a ribbon thread caught in the side gear and saw that the drawer only moved when the thread tugged.",
        "change": "They cleaned the gear, freed the thread, and set a tiny stop so the mechanism would close and stay shut.",
        "result": "The drawer rested still, and the tools inside stayed neatly in place.",
        "ending": "When the room went quiet, the repaired drawer stayed closed like it had kept a secret.",
    },
    "wind-up lamp": {
        "premise": "A wind-up lamp flickered on and off whenever anyone passed the table.",
        "mistake": "Mina wound it again and again, but the light only shivered more loudly.",
        "clue": "Toby saw that the lamp's little key brushed a hanging tag each time the table shook.",
        "change": "They moved the tag away and wrapped the key with a soft sleeve so the mechanism could turn smoothly.",
        "result": "The lamp glowed steadily and lit the whole corner without blinking.",
        "ending": "The lamp ended the night with a warm circle of light and no more flickers.",
    },
    "toy door latch": {
        "premise": "A toy door latch kept catching, so the miniature door would not open for the playroom animals.",
        "mistake": "Mina pulled it fast, which only made the latch scrape and jam harder.",
        "clue": "Toby held a pencil beside the latch and saw that one bent pin was scraping the frame.",
        "change": "They straightened the pin with care, oiled the hinge, and tested the latch with slow, gentle pushes.",
        "result": "The tiny door swung open and shut as smoothly as a storybook page.",
        "ending": "The toy door clicked softly, no longer trapped by its own little puzzle.",
    },
    "music box": {
        "premise": "A music box had started to play only one note, no matter how carefully Mina turned the key.",
        "mistake": "Mina turned the key farther, but the same note rang out like a stubborn bell.",
        "clue": "Toby found a speck of dust under the comb teeth, hiding where the song should have changed.",
        "change": "They brushed the comb clean, reset the wheel, and let the song try again from the beginning.",
        "result": "The music box sang a whole tune, bright and clear.",
        "ending": "Its last note floated through the room like a tiny surprise.",
    },
    "garden pump": {
        "premise": "The little garden pump gave a weak squirt and then stopped, leaving the seedlings thirsty.",
        "mistake": "Mina pressed the handle faster, but the pump still wheezed and stalled.",
        "clue": "Toby saw a pebble blocking the valve and heard water trying to move behind it.",
        "change": "They lifted out the pebble, rinsed the valve, and pumped slowly until the water flowed again.",
        "result": "The seedlings got a steady splash, and the pump worked without choking.",
        "ending": "A neat stream of water glittered over the leaves after the mystery was solved.",
    },
}

TWISTS = {
    "it was helping": "The mechanism had not been broken at all; it had been trying to keep something from getting damaged.",
    "it was signaling": "The mechanism had been making a quiet signal, warning them that something nearby needed attention.",
    "it was protecting": "The mechanism had been catching and slowing a thing that might have broken another part.",
    "it was remembering": "The mechanism had been holding a tiny setting in place, like a note remembered from a careful hand.",
}

ASP_RULES = r"""
friendship(X,Y) :- friend(X,Y).
caution_needed(M) :- mystery_item(M), tricky(M).
resolved(M) :- fixed(M), understood(M).
twist(M) :- twist_kind(M).
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("friend", "hero", "friend"),
        asp.fact("friend", "friend", "hero"),
        asp.fact("mystery_item", "mechanism"),
        asp.fact("twist_kind", "twist"),
        asp.fact("tricky", "mechanism"),
        asp.fact("fixed", "mechanism"),
        asp.fact("understood", "mechanism"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show friendship/2.\n#show caution_needed/1.\n#show resolved/1.\n#show twist/1."
        )
    )
    got = set()
    for sym in model:
        args = []
        for a in sym.arguments:
            if a.type.name == "String":
                args.append(a.string)
            elif a.type.name == "Number":
                args.append(a.number)
            else:
                args.append(a.name)
        got.add((sym.name, tuple(args)))
    want = {
        ("friendship", ("hero", "friend")),
        ("friendship", ("friend", "hero")),
        ("caution_needed", ("mechanism",)),
        ("resolved", ("mechanism",)),
        ("twist", ("twist",)),
    }
    if got != want:
        print("MISMATCH between ASP and Python reasoning.")
        print("ASP:", sorted(got))
        print("PY :", sorted(want))
        return 1
    print("OK: ASP and Python parity looks good.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery story world about a mechanism and a twist.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--mechanism", choices=MECHANISMS.keys())
    ap.add_argument("--twist", choices=TWISTS.keys())
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    if hero == friend:
        raise StoryError("The friend should be a different character from the hero.")
    mechanism = args.mechanism or rng.choice(list(MECHANISMS))
    twist = args.twist or rng.choice(list(TWISTS))
    return StoryParams(setting=setting, hero_name=hero, friend_name=friend, mechanism=mechanism, twist=twist)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.mechanism not in MECHANISMS:
        raise StoryError(f"Unknown mechanism: {params.mechanism}")
    if params.twist not in TWISTS:
        raise StoryError(f"Unknown twist: {params.twist}")

    rng = random.Random(params.seed if params.seed is not None else f"{params.setting}:{params.hero_name}:{params.friend_name}:{params.mechanism}:{params.twist}")
    world = World(params)

    hero = world.add(Entity("hero", "character", params.hero_name, "the curious child", memes={"worry": 0.3, "hope": 0.4}))
    friend = world.add(Entity("friend", "character", params.friend_name, "the careful friend", memes={"worry": 0.2, "hope": 0.5}))
    mechanism = world.add(Entity("mechanism", "object", params.mechanism, f"the {params.mechanism}", meters={"motion": 1.0, "noise": 0.7}, memes={"mystery": 1.0, "risk": 0.6}))

    opening = f"{hero.label} found a problem in {SETTINGS[params.setting]}: {MECHANISMS[params.mechanism]['premise']}"
    world.say(opening)
    world.say(f"{hero.label} and {friend.label} stood beside the {params.mechanism} and listened to its odd little sound.")
    world.say(f'“Do you think it is broken?” {hero.label} whispered.')
    world.say(f'“Not yet,” {friend.label} said. “Let us look before we guess.”')

    world.say(MECHANISMS[params.mechanism]["mistake"])
    world.say(f'“I can make it stop,” {hero.label} said, reaching in.')
    world.say(f'“Careful,” {friend.label} replied. “If we pull too hard, we might make a small problem into a bigger one.”')

    world.say(MECHANISMS[params.mechanism]["clue"])
    world.say(f'“Oh,” {hero.label} said. “It was hiding a clue.”')
    world.say(f'“And we found it because we worked together,” {friend.label} said with a small smile.')

    twist_text = TWISTS[params.twist]
    world.say(twist_text)
    world.say(f'“So it was not being troublesome after all?” {hero.label} asked.')
    world.say(f'“No,” {friend.label} said. “It was trying to help.”')

    world.say(MECHANISMS[params.mechanism]["change"])
    mechanism.meters["motion"] = 0.0
    mechanism.meters["noise"] = 0.1
    mechanism.memes["mystery"] = 0.0
    mechanism.memes["risk"] = 0.1
    hero.memes["worry"] = 0.0
    hero.memes["hope"] = 0.9
    friend.memes["hope"] = 0.9

    world.say(MECHANISMS[params.mechanism]["result"])
    world.say(f'{hero.label} nodded. “The safest fix was the careful one.”')
    world.say(f'{friend.label} answered, “And the best clue was the one we almost missed.”')
    world.say(MECHANISMS[params.mechanism]["ending"])

    story = world.render()

    prompts = [
        f"Write a child-facing mystery story in {SETTINGS[params.setting]} about a {params.mechanism}.",
        f"Include a cautious friendship exchange between {params.hero_name} and {params.friend_name}.",
        f"Use a twist where the {params.mechanism} was really {params.twist}.",
    ]

    story_qa = [
        QAItem(
            question=f"What strange thing happened with the {params.mechanism}?",
            answer=MECHANISMS[params.mechanism]["premise"],
        ),
        QAItem(
            question="What did the friends say before they made a guess?",
            answer=f'{params.friend_name} said, “Let us look before we guess.”',
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=MECHANISMS[params.mechanism]["clue"],
        ),
        QAItem(
            question="What was the twist?",
            answer=TWISTS[params.twist],
        ),
        QAItem(
            question="How did the story end?",
            answer=MECHANISMS[params.mechanism]["ending"],
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, open, play, or change in a useful way.",
        ),
        QAItem(
            question="Why should children be cautious around small machines?",
            answer="Small machines can pinch fingers, jam if pushed too hard, or break if someone rushes the repair.",
        ),
        QAItem(
            question="What does friendship do in a mystery story?",
            answer="Friendship helps characters listen, share ideas, and stay brave enough to solve the problem together.",
        ),
    ]

    world.facts.update(
        hero=hero,
        friend=friend,
        mechanism=mechanism,
        twist=params.twist,
        resolved=True,
        caution=True,
    )

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, ent in sample.world.entities.items():
            print(f"{key}: {ent.label} meters={ent.meters} memes={ent.memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show friendship/2.\n#show caution_needed/1.\n#show resolved/1.\n#show twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for mechanism in MECHANISMS:
            params = StoryParams(mechanism=mechanism, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
