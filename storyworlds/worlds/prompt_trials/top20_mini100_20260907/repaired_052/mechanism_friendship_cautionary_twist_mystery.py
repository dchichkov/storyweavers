#!/usr/bin/env python3
"""
A small mystery storyworld about a mechanism, friendship, a cautionary twist,
and a careful ending.

The world simulates a few children, a curious mechanism, and the changing
feelings that move the story from worry to trust.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str
    friend: str
    place: str
    mechanism_name: str
    seed: Optional[int] = None
    scenario: Optional[str] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.id in {"mina", "iris", "ella", "rose", "sana", "nora"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.id in {"ben", "owen", "leo", "noah", "eli", "max"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    clue: str
    hasty_action: str
    hasty_result: str
    twist_reveal: str
    repair_action: str
    ending: str
    lesson: str


HERO_NAMES = ["Mina", "Iris", "Ella", "Rose", "Sana", "Nora"]
FRIEND_NAMES = ["Ben", "Owen", "Leo", "Noah", "Eli", "Max"]
PLACES = [
    "the library hall",
    "the creek path",
    "the attic room",
    "the garden shed",
    "the old clock tower",
    "the school stage",
]

MECHANISMS = [
    "a brass mechanism with tiny silver teeth",
    "a wooden mechanism with a glass eye",
    "a boxy mechanism with a copper lever",
    "a wall mechanism with a round keyhole",
    "a small mechanism that clicked like rain",
]

SCENARIOS = [
    Scenario(
        key="hidden_note",
        opening="found a quiet mechanism tucked behind a stack of books",
        clue="the little clicks matched the tapping from the window ledge",
        hasty_action="pulled the lever at once",
        hasty_result="the mechanism opened a drawer that released a puff of dust and one torn note",
        twist_reveal="the note was not a warning at all; it was a thank-you note hidden for a lost friend",
        repair_action="used tape and careful hands to mend the note, then wound the mechanism slowly",
        ending="the drawer stayed open, and inside sat two matching ribbons tied together like a promise",
        lesson="a strange thing can look alarming before it is understood",
    ),
    Scenario(
        key="garden_alarm",
        opening="was guarding a mechanism beside the garden gate after the flowers began to tremble",
        clue="the gears moved only when the wind chimes sang softly",
        hasty_action="rang the alarm bell too loudly",
        hasty_result="the flowers bent flat, and the mechanism snapped shut with a sharp clang",
        twist_reveal="the mechanism was not an alarm at all; it was a seed feeder that waited for gentle sound",
        repair_action="lowered the bell cord and sang the chimes back into rhythm with a friend",
        ending="the feeder clicked open and sprinkled seeds like gold crumbs across the soil",
        lesson="caution helps friendship when it keeps hands gentle",
    ),
    Scenario(
        key="clock_key",
        opening="noticed a mechanism in the clock tower that had stopped at moonrise",
        clue="a thin scratch on the keyhole pointed toward the rooftop",
        hasty_action="forced the key and made the gears grind",
        hasty_result="the clock gave a groan, and every bell in the tower fell silent",
        twist_reveal="the mechanism was built to pause whenever a bird slept above the tower",
        repair_action="waited for the bird to wake, then set the clock by moonlight with a friend",
        ending="the bells rang again, and the bird flew out with a bright, sleepy yawn",
        lesson="patience can solve what force only damages",
    ),
    Scenario(
        key="stage_secret",
        opening="found a mechanism under the school stage before the evening play",
        clue="its smallest wheel carried a smudge of paint from the costume room",
        hasty_action="opened the panel without asking anyone",
        hasty_result="the curtain dropped and sent everyone into a startled silence",
        twist_reveal="the mechanism was a backstage helper that lifted props for the shy performers",
        repair_action="closed the panel, apologized, and asked a friend to help test the ropes",
        ending="the curtain rose again just in time, and the shyest actor bowed first",
        lesson="friendship grows when curiosity is matched with respect",
    ),
    Scenario(
        key="shed_map",
        opening="came upon a mechanism in the garden shed beside a folded map",
        clue="its dial pointed toward the old plum tree every time the door creaked",
        hasty_action="turned the dial all the way to the left",
        hasty_result="the shed light blinked off, and the map blew into a muddy corner",
        twist_reveal="the mechanism was a map box that only opened when two friends turned it together",
        repair_action="shared the dial with a friend and turned it back to the middle",
        ending="the box opened to show a secret trail lined with lantern bugs",
        lesson="some doors are built for two hands, not one",
    ),
    Scenario(
        key="river_latch",
        opening="spotted a mechanism on the creek bridge while the water rushed below",
        clue="the latch hummed whenever two pebbles tapped in a pattern",
        hasty_action="snapped the latch shut",
        hasty_result="the bridge rail locked tight, and a basket of apples tipped sideways",
        twist_reveal="the mechanism was a rescue latch meant to hold the bridge only during river fog",
        repair_action="reset the latch with a friend and listened for the humming pattern again",
        ending="the bridge settled safely, and the apples rolled back into the basket",
        lesson="a cautionary sign can be a kindness, not a threat",
    ),
]

WORLD_NAMES = ["the little brass town", "the quiet green street", "the moonlit schoolyard"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with friendship, caution, and a twist.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mechanism-name", choices=MECHANISMS)
    ap.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
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
    hero = args.hero or rng.choice(HERO_NAMES)
    friend_pool = [n for n in FRIEND_NAMES if n != hero]
    friend = args.friend or rng.choice(friend_pool)
    place = args.place or rng.choice(PLACES)
    mechanism_name = args.mechanism_name or rng.choice(MECHANISMS)
    scenario = args.scenario or rng.choice(SCENARIOS).key
    return StoryParams(
        hero=hero,
        friend=friend,
        place=place,
        mechanism_name=mechanism_name,
        scenario=scenario,
    )


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("feature", "friendship"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "twist"),
            asp.fact("style", "mystery"),
            asp.fact("seed_word", "mechanism"),
        ]
    )


ASP_RULES = r"""
feature(friendship).
feature(cautionary).
feature(twist).
style(mystery).
seed_word(mechanism).

story_ok :- feature(friendship), feature(cautionary), feature(twist), style(mystery), seed_word(mechanism).
#show story_ok/0.
#show feature/1.
#show style/1.
#show seed_word/1.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    seen = sorted(asp.atoms(model, "feature"))
    wanted = [("cautionary",), ("friendship",), ("twist",)]
    if sorted(seen) != wanted:
        print("MISMATCH: ASP feature parity failed.")
        print(seen)
        return 1
    if ("mystery",) not in asp.atoms(model, "style"):
        print("MISMATCH: ASP style parity failed.")
        return 1
    print("OK: ASP parity verified.")
    return 0


def _pick(rng: random.Random, *choices: str) -> str:
    return rng.choice(choices)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    scenario = next((s for s in SCENARIOS if s.key == params.scenario), SCENARIOS[0])

    hero = Entity(
        id=params.hero.lower(),
        kind="child",
        label=params.hero,
        location=params.place,
        meters={"fear": 0.2, "curiosity": 0.8},
        memes={"trust": 0.6, "worry": 0.3},
        traits=["curious", "careful"],
    )
    friend = Entity(
        id=params.friend.lower(),
        kind="child",
        label=params.friend,
        location=params.place,
        meters={"fear": 0.2, "curiosity": 0.7},
        memes={"trust": 0.6, "worry": 0.2},
        traits=["kind", "alert"],
    )
    mechanism = Entity(
        id="mechanism",
        kind="object",
        label=params.mechanism_name,
        location=params.place,
        meters={"stillness": 0.5, "mystery": 0.9, "risk": 0.5},
        memes={"strangeness": 0.8},
        traits=["small", "old"],
    )
    world = type("World", (), {})()
    world.entities = {hero.id: hero, friend.id: friend, mechanism.id: mechanism}

    story_parts: list[str] = []
    story_parts.append(f"At {params.place}, {params.hero} and {params.friend} discovered {params.mechanism_name} that {scenario.opening}.")
    story_parts.append(f'"Do you hear that?" {params.friend} asked. "{scenario.clue.capitalize()}."')
    story_parts.append(f'"Then we should be careful," {params.hero} said, but the mystery made both children lean closer.')
    story_parts.append(f"{params.friend} did not wait long and {scenario.hasty_action}, because the mechanism looked harmless enough.")
    story_parts.append(f"That was the cautionary twist: {scenario.hasty_result}.")
    story_parts.append(f'"We should have checked first," {params.hero} said. "{params.friend}, what does it seem to want?"')
    story_parts.append(f'"Not to be scared of," {params.friend} answered after listening again. "Look, {scenario.twist_reveal}."')
    story_parts.append(f"With friendship and patience, they {scenario.repair_action}.")
    story_parts.append(f"In the end, {scenario.ending}.")
    story_parts.append(f"They walked home together remembering that {scenario.lesson}.")

    hero.meters["fear"] = 0.1
    hero.memes["trust"] = 0.9
    friend.meters["fear"] = 0.1
    friend.memes["trust"] = 0.9
    mechanism.meters["risk"] = 0.0
    mechanism.meters["mystery"] = 0.2
    mechanism.memes["strangeness"] = 0.1

    prompts = [
        f"Write a mystery story about {params.hero} and {params.friend} finding {params.mechanism_name} at {params.place}.",
        f"Make the story child-friendly, with a cautionary mistake and a twist ending.",
        f"Show how friendship helps the children solve the secret of the mechanism.",
    ]

    story_qa = [
        QAItem(
            question="What did the children find?",
            answer=f"They found {params.mechanism_name} at {params.place}. It looked mysterious and made them curious.",
        ),
        QAItem(
            question="What was the cautionary mistake?",
            answer=f"{params.friend} acted too quickly and {scenario.hasty_action}. That made the problem worse instead of better.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {scenario.twist_reveal}. What seemed risky was actually meant to help.",
        ),
        QAItem(
            question="How did friendship help in the end?",
            answer=f"{params.hero} and {params.friend} listened to each other, fixed the problem together, and made the mechanism safe again.",
        ),
        QAItem(
            question="What lesson did they learn?",
            answer=f"They learned that {scenario.lesson}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a thing with moving parts that does a job when it is set in motion correctly.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it gives a warning or teaches people to be careful.",
        ),
        QAItem(
            question="What does a twist do in a mystery?",
            answer="A twist changes what the reader expects and reveals a new truth about the situation.",
        ),
    ]

    return StorySample(
        params=params,
        story=" ".join(story_parts),
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
        print("--- world model state ---")
        for ent in sample.world.entities.values():
            print(f"{ent.label}: location={ent.location} meters={ent.meters} memes={ent.memes}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [
            generate(StoryParams(hero="Mina", friend="Ben", place="the library hall", mechanism_name=MECHANISMS[0], seed=101, scenario="hidden_note")),
            generate(StoryParams(hero="Iris", friend="Leo", place="the garden shed", mechanism_name=MECHANISMS[2], seed=202, scenario="shed_map")),
            generate(StoryParams(hero="Nora", friend="Owen", place="the old clock tower", mechanism_name=MECHANISMS[4], seed=303, scenario="clock_key")),
        ]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n) and attempt < max(50, args.n * 20):
            attempt += 1
            seed = base_seed + attempt
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.friend} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
