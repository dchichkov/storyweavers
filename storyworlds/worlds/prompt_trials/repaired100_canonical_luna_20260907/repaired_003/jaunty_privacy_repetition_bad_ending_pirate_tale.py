#!/usr/bin/env python3
"""
A tiny pirate storyworld about jaunty courage, privacy, repetition, and a
repairable bad ending.

A young deckhand repeats a privacy promise while helping a captain protect a
secret map. The first ending is bad because a noisy parrot nearly blurts out
the secret. The deckhand notices the mistake, changes the plan, and repairs
the ending with a quiet signal and a locked chest.
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
class StoryParams:
    setting: str = "the jaunty ship Starling"
    seed: Optional[int] = None
    child_name: str = "Luna"
    captain_name: str = "Captain Mira"
    parrot_name: str = "Pip"
    promise: str = "A captain's secret stays private."
    style: str = "pirate tale"
    feature: str = "repetition"
    ending_mode: str = "bad ending repaired"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    setting: str
    deckhand: Entity
    captain: Entity
    parrot: Entity
    map: Entity
    chest: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in (
            self.deckhand,
            self.captain,
            self.parrot,
            self.map,
            self.chest,
        ):
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            details = []
            if meters:
                details.append(f"meters={meters}")
            if memes:
                details.append(f"memes={memes}")
            lines.append(
                f"  {entity.id:10} ({entity.kind:10}) {' '.join(details)}"
            )
        lines.append(f"  setting: {self.setting}")
        return "\n".join(lines)


SETTINGS = {
    "deck": "the sunny deck",
    "cabin": "the captain's cabin",
    "cove": "a bright blue cove",
    "harbor": "the bustling harbor",
}

NAMES = ["Luna", "Nico", "Tessa", "Rafi", "Milo"]
CAPTAINS = ["Captain Mira", "Captain Sol", "Captain Bea", "Captain Rowan"]
PARROTS = ["Pip", "Peep", "Jolly", "Skipper"]

OPENINGS = {
    "deck": [
        "{child} skipped across the sunny deck of the Starling while the sails snapped like flags.",
        "On the jaunty ship Starling, {child} danced a little jig as the deck boards hummed beneath the boots.",
    ],
    "cabin": [
        "Below the bright sails, {child} entered the captain's cabin with a jaunty grin.",
        "The Starling bobbed gently while {child} carried a brass key into the captain's tidy cabin.",
    ],
    "cove": [
        "The Starling rested in a bright blue cove, where {child} hopped from stone to stone.",
        "At the quiet cove, {child} helped {captain} lower a little boat beside the jaunty ship.",
    ],
    "harbor": [
        "In the bustling harbor, {child} carried a small chest past barrels, ropes, and cheerful gulls.",
        "The Starling rocked among the harbor boats while {child} marched along the pier with jaunty steps.",
    ],
}

BAD_CLUES = [
    "A folded map showed the route to a hidden garden, but its corner stuck out from the captain's coat.",
    "A silver key opened a secret chest, yet it clinked loudly against the rail.",
    "A tiny note named a peaceful island, and the wind tugged it toward the busy harbor.",
]

REPAIRS = [
    "slipped the map into the locked chest and tucked the key beneath a loose deck board",
    "folded the map into a waterproof tube and placed the tube inside the chest",
    "closed the chest, turned the key twice, and carried it to the captain's private cabin",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A jaunty pirate tale about privacy, repetition, and repairing a bad ending."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--parrot", choices=PARROTS)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Choose a valid pirate setting.")
    if params.feature.lower() != "repetition":
        raise StoryError("This tale requires the Repetition feature.")
    if "bad ending" not in params.ending_mode.lower():
        raise StoryError("This tale requires a Bad Ending that can be repaired.")
    if not params.promise:
        raise StoryError("The privacy promise cannot be empty.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        seed=args.seed,
        child_name=args.name or rng.choice(NAMES),
        captain_name=args.captain or rng.choice(CAPTAINS),
        parrot_name=args.parrot or rng.choice(PARROTS),
    )
    _validate_params(params)
    return params


def make_world(params: StoryParams) -> World:
    return World(
        setting=SETTINGS[params.setting],
        deckhand=Entity(
            id="deckhand",
            kind="character",
            label=params.child_name,
            type="young sailor",
        ),
        captain=Entity(
            id="captain",
            kind="character",
            label=params.captain_name,
            type="captain",
        ),
        parrot=Entity(
            id="parrot",
            kind="animal",
            label=params.parrot_name,
            type="parrot",
        ),
        map=Entity(
            id="map",
            kind="object",
            label="secret map",
            type="private knowledge",
        ),
        chest=Entity(
            id="chest",
            kind="object",
            label="locked chest",
            type="privacy container",
        ),
    )


def _build_story(world: World, params: StoryParams) -> None:
    rng = random.Random((params.seed or 0) + 9187)
    child = world.deckhand
    captain = world.captain
    parrot = world.parrot
    secret_map = world.map
    chest = world.chest

    opening = rng.choice(OPENINGS[params.setting]).format(
        child=child.label,
        captain=captain.label,
    )
    clue = rng.choice(BAD_CLUES)
    repair = rng.choice(REPAIRS)

    child.memes["jaunty"] = 1.0
    child.memes["privacy"] = 0.0
    child.meters["promise_repetitions"] = 0.0
    secret_map.meters["exposed"] = 1.0
    chest.meters["locked"] = 0.0
    parrot.meters["noise"] = 1.0

    world.say(opening)
    world.say(
        f"{captain.label} beckoned and whispered, "
        f'"{params.promise}" '
        f"{child.label} touched two fingers to the cap and listened carefully."
    )
    world.say(clue)

    world.para()
    world.say(
        f'"{params.promise}" repeated {child.label}, '
        f"this time with a jaunty tap of one boot."
    )
    child.inc_meter("promise_repetitions", 1.0)
    captain.inc_meme("trust", 1.0)
    world.say(
        f'"Say it once more, matey," said {captain.label}. '
        f'"A secret is safest when we remember who should hear it."'
    )
    world.say(f'"{params.promise}" said {child.label} again, slower and clearer.')
    child.inc_meter("promise_repetitions", 1.0)

    world.para()
    world.say(
        f"Then {parrot.label} flapped onto the rail and squawked, "
        f'"A secret map! A secret map!"'
    )
    parrot.inc_meter("secret_words", 1.0)
    world.say(
        f"A sailor on the pier turned around. The first ending looked bad: "
        f"the private map might be announced to everyone in the harbor."
    )
    world.facts["bad_ending"] = True

    world.para()
    world.say(
        f"{child.label} did not laugh or shout. Instead, {child.label} repeated "
        f'"{params.promise}" and pointed to the loose map.'
    )
    child.inc_meter("promise_repetitions", 1.0)
    child.inc_meme("privacy", 1.0)
    world.say(
        f'"Good noticing," said {captain.label}. '
        f'"What can we do before the whole harbor hears?"'
    )
    world.say(
        f'"Hide the map and teach {parrot.label} a quieter call," answered '
        f"{child.label}."
    )
    world.say(
        f"Together they {repair}. The captain covered the bright paper, and "
        f"{parrot.label} practiced saying, 'Shh, shipmates.'"
    )
    secret_map.meters["exposed"] = 0.0
    secret_map.meters["protected"] = 1.0
    chest.meters["locked"] = 1.0
    parrot.meters["noise"] = 0.0
    child.inc_meme("privacy", 1.0)
    world.facts["bad_ending"] = False
    world.facts["repaired"] = True

    world.para()
    world.say(
        f"{captain.label} smiled. " 
        f'"You repeated the promise, spotted the trouble, and repaired the ending."'
    )
    world.say(
        f"{child.label} gave a jaunty salute as the Starling sailed toward sunset. "
        f"The map stayed private in its locked chest, and {parrot.label} whispered "
        f"the new quiet call while the waves clapped along."
    )
    world.facts.update(
        repetitions=int(child.meters["promise_repetitions"]),
        repair=repair,
        promise=params.promise,
        setting=params.setting,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a jaunty pirate tale about {world.deckhand.label} protecting a private secret.",
        "Use repetition so a privacy promise changes what the sailor decides to do.",
        "Include a bad ending first, then repair it with a concrete action and a happy final image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.deckhand
    captain = world.captain
    parrot = world.parrot
    return [
        QAItem(
            question="What promise did the sailor repeat?",
            answer=f'{child.label} repeated, "{world.facts["promise"]}"',
        ),
        QAItem(
            question="Why was the first ending bad?",
            answer=(
                f"The first ending was bad because {parrot.label} squawked about the "
                "secret map where someone in the harbor might hear."
            ),
        ),
        QAItem(
            question="How did the sailor repair the ending?",
            answer=(
                f"{child.label} noticed the loose map, asked what to do, and helped "
                f"{captain.label} hide it in a locked chest while teaching "
                f"{parrot.label} a quieter call."
            ),
        ),
        QAItem(
            question="Where was the private map at the end?",
            answer=(
                f"The private map was protected inside the locked chest on the "
                f"{world.setting} ship."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does privacy mean?",
            answer="Privacy means keeping personal information or a secret from people who should not hear it.",
        ),
        QAItem(
            question="Why can repetition help?",
            answer="Repeating an important promise can help someone remember it and make a careful choice.",
        ),
        QAItem(
            question="What makes a pirate tale jaunty?",
            answer="A jaunty pirate tale has lively movement, cheerful courage, playful language, and a bright sense of adventure.",
        ),
        QAItem(
            question="What is a repaired ending?",
            answer="A repaired ending begins with trouble but changes through a thoughtful action so the characters reach a safer, better result.",
        ),
    ]


ASP_RULES = r"""
private_map(M) :- map(M), protected(M).
promise_remembered(C) :- deckhand(C), repetitions(C, N), N >= 2.
ending_repaired(S) :- story(S), private_map(M), promise_remembered(C), quiet_parrot(P).
good_story(S) :- ending_repaired(S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("story", "starling_tale"),
        asp.fact("deckhand", "luna"),
        asp.fact("map", "secret_map"),
        asp.fact("protected", "secret_map"),
        asp.fact("quiet_parrot", "pip"),
        asp.fact("repetitions", "luna", 3),
    ]
    return "\n".join(lines)


def asp_program(show: str = "#show good_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    return (
        params.setting in SETTINGS
        and params.feature.lower() == "repetition"
        and "bad ending" in params.ending_mode.lower()
        and bool(params.promise)
    )


def asp_verify() -> int:
    params = StoryParams()
    if not _python_reasonable(params):
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import storyworlds.asp as asp

        symbols = asp.one_model(asp_program())
        good = bool(asp.atoms(symbols, "good_story"))
    except Exception as exc:
        print(f"ASP unavailable or failed: {exc}")
        return 1
    sample = generate(params)
    if not good or "locked chest" not in sample.story or "private" not in sample.story:
        print("MISMATCH: ASP/Python parity failed.")
        return 1
    print("OK: ASP/Python parity and generated story checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = make_world(params)
    _build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print("\n== Generation prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(setting="deck", child_name="Luna", captain_name="Captain Mira", parrot_name="Pip"),
    StoryParams(setting="cabin", child_name="Nico", captain_name="Captain Sol", parrot_name="Jolly"),
    StoryParams(setting="cove", child_name="Tessa", captain_name="Captain Bea", parrot_name="Peep"),
    StoryParams(setting="harbor", child_name="Rafi", captain_name="Captain Rowan", parrot_name="Skipper"),
]


def build_all_samples() -> list[StorySample]:
    return [generate(params) for params in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp

            symbols = asp.one_model(asp_program())
            print("ASP model:", " ".join(str(symbol) for symbol in symbols))
        except Exception as exc:
            print(f"ASP unavailable or failed: {exc}")
            sys.exit(1)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = build_all_samples()
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
