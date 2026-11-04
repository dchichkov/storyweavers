#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# This script lives several directories below the repository root.
_here = os.path.abspath(__file__)
for _parent in (_here, *[os.path.join(os.path.dirname(_here), *([]))]):
    pass
_root = os.path.dirname(_here)
while _root != os.path.dirname(_root):
    if os.path.isfile(os.path.join(_root, "storyworlds", "results.py")):
        break
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    first_name: str
    second_name: str
    place: str
    gift: str
    seed: Optional[int] = None


NAMES = [
    "Eilidh",
    "Hamish",
    "Isla",
    "Fergus",
    "Mairi",
    "Rowan",
    "Catriona",
    "Alasdair",
    "Skye",
    "Finlay",
]

PLACES = {
    "highland_cottage": "a stone cottage above a quiet loch in the Scottish Highlands",
    "island_croft": "a whitewashed croft on a small Scottish island",
    "pine_glen_house": "a little house beside a pine-dark Scottish glen",
}

GIFT_PROFILES = {
    "knitted_lamb": {
        "gift_label": "a soft knitted lamb with a tiny brass bell on its ribbon",
        "sound": "brrr... ting!",
        "misheard_as": "a lamb bleating inside the parcel",
        "misheard_noun": "lamb",
        "cause": "the tiny brass bell on the knitted lamb's ribbon tapped the parcel's wooden tag",
        "clue": "Each gentle tilt ended with the same bright metal ting, and the sound stopped when the parcel lay flat.",
        "intro": [
            "A parcel from Gran waited by the door, tied with blue wool and smelling faintly of lavender.",
            "Gran had promised them a surprise, and now a blue-wool parcel sat on the doorstep.",
        ],
        "denial": "There was no lamb inside after all.",
        "note": "For my two careful listeners: may this wee lamb keep you company.",
        "ending": [
            "The knitted lamb rested beside their pillows, its bell giving one last sleepy ting as moonlight silvered the loch.",
            "Soon the little lamb sat between the beds, and its tiny bell glimmered softly in the Scottish night.",
        ],
    },
    "wooden_puffin": {
        "gift_label": "a painted wooden puffin with folded paper wings",
        "sound": "scritch-whirr!",
        "misheard_as": "a mouse scratching inside the parcel",
        "misheard_noun": "mouse",
        "cause": "one folded paper wing brushed the puffin's wooden side",
        "clue": "The scrape came only while the parcel was tilted; when they set it flat, it stopped.",
        "intro": [
            "A parcel from Gran waited by the door, wrapped in blue paper with a neat string bow.",
            "Gran's little parcel sat on the doorstep, its brown paper corners glowing in the lamplight.",
        ],
        "denial": "There was no mouse inside after all.",
        "note": "For my two good explorers: here is a puffin to watch over your dreams.",
        "ending": [
            "The wooden puffin perched on the windowsill, its paper wings still at last as the Scottish night grew quiet.",
            "They placed the puffin beside the bed, where its folded wings made a small shadow in the moonlight.",
        ],
    },
    "moon_music_box": {
        "gift_label": "a crescent-moon music box with a tiny winding key",
        "sound": "hoo-oo, plink!",
        "misheard_as": "a little owl calling from inside the parcel",
        "misheard_noun": "owl",
        "cause": "a wind-up tune inside the crescent-moon music box",
        "clue": "The same three notes came in exactly the same order each time, then stopped when the parcel lay still.",
        "intro": [
            "An owl called once from the dark pines, and a parcel from Gran waited by the door.",
            "Gran's parcel arrived just as an owl called from somewhere beyond the little house.",
        ],
        "denial": "There was no owl inside after all.",
        "note": "For my two night owls: wind this little moon only when you want a tune.",
        "ending": [
            "The moon-shaped music box played one soft tune, then rested beside their pillows beneath a sky full of stars.",
            "After one last gentle tune, they set the music box by the window and let the real moon keep watch.",
        ],
    },
}


FEATURES = ("parcel", "scottish", "misunderstanding", "sound_effects", "conflict", "bedtime")


def _python_profile_is_reasonable(key: str) -> bool:
    profile = GIFT_PROFILES.get(key)
    if profile is None:
        return False
    required = (
        "gift_label",
        "sound",
        "misheard_as",
        "misheard_noun",
        "cause",
        "clue",
        "intro",
        "denial",
        "note",
        "ending",
    )
    return all(profile.get(field) for field in required)


def reasonableness(params: StoryParams) -> None:
    """Reject parameter combinations that cannot describe this small story domain."""
    if not isinstance(params, StoryParams):
        raise StoryError("Story parameters must be a StoryParams instance.")
    if not params.first_name.strip() or not params.second_name.strip():
        raise StoryError("Both children need names.")
    if params.first_name.strip().casefold() == params.second_name.strip().casefold():
        raise StoryError("The two children need different names so their dialogue is clear.")
    if params.place not in PLACES:
        raise StoryError(f"Unknown Scottish setting: {params.place!r}.")
    if not _python_profile_is_reasonable(params.gift):
        raise StoryError(f"Unknown or incomplete parcel gift: {params.gift!r}.")
    if any(feature not in FEATURES for feature in ("parcel", "scottish", "bedtime")):
        raise StoryError("The story is missing a required bedtime-story feature.")


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, str] = {}
        self.conflict_active = True
        self.misunderstanding_active = True
        self.resolved = False

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    stable = "|".join((params.first_name, params.second_name, params.place, params.gift))
    seed = int.from_bytes(hashlib.sha256(stable.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def tell(params: StoryParams) -> World:
    reasonableness(params)
    rng = _rng_for(params)
    profile = GIFT_PROFILES[params.gift]
    first_name = params.first_name.strip()
    second_name = params.second_name.strip()
    place = PLACES[params.place]
    world = World(params)

    first = world.add(
        Entity(
            id=first_name,
            kind="character",
            type="child",
            label="first child",
            meters={"listening": 0.0, "care": 0.7},
            memes={"worry": 0.2, "confidence": 0.5, "trust": 0.7},
        )
    )
    second = world.add(
        Entity(
            id=second_name,
            kind="character",
            type="child",
            label="second child",
            meters={"listening": 0.0, "care": 0.8},
            memes={"worry": 0.1, "caution": 0.7, "trust": 0.7},
        )
    )
    parcel = world.add(
        Entity(
            id="parcel",
            kind="object",
            type="wrapped_parcel",
            label="Gran's parcel",
            owner="Gran",
            meters={"sealed": 1.0, "opened": 0.0, "tilts": 0.0, "sound_repeats": 0.0},
            memes={"mystery": 0.8},
        )
    )
    gift = world.add(
        Entity(
            id="gift",
            kind="object",
            type="bedtime_gift",
            label=profile["gift_label"],
            owner="parcel",
            meters={"safe": 1.0, "revealed": 0.0},
            memes={"comfort": 0.6},
        )
    )
    sound = world.add(
        Entity(
            id="sound",
            kind="event",
            type="sound_effect",
            label=profile["sound"],
            meters={"heard": 0.0, "volume": 0.35},
            memes={"mystery": 0.8},
        )
    )

    intro = rng.choice(profile["intro"])
    world.say(
        f"At bedtime, {first_name} and {second_name} were getting ready for sleep in {place}. {intro}"
    )
    world.para()

    if params.gift == "moon_music_box":
        world.say(
            f"Then the parcel answered the owl with a soft “{profile['sound']}” from inside. "
            "The sound seemed so close that both children stared at the blue paper."
        )
    else:
        world.say(
            f"From inside came “{profile['sound']}” The sound was small, but in the quiet house it seemed to fill the room."
        )
    sound.meters["heard"] = 1.0
    first.memes["worry"] = 0.75
    world.para()

    worry_line = (
        f"“I think it's {profile['misheard_as']}. We have to open it now!” {first_name} whispered."
    )
    caution_line = (
        f"“Let's not tear Gran's parcel,” {second_name} replied. “We can listen first, and then decide together.”"
    )
    world.say(worry_line + " " + caution_line)
    first.memes["confidence"] = 0.25
    second.memes["caution"] = 0.85
    world.para()

    world.say(
        f"{second_name} spread a quilt on the floor. {first_name} tipped one corner of the parcel just a little, "
        f"then set it down. It made “{profile['sound']}” again. They tried once more, gently."
    )
    parcel.meters["tilts"] = 2.0
    parcel.meters["sound_repeats"] = 1.0
    first.meters["listening"] = 1.0
    second.meters["listening"] = 1.0
    world.say(profile["clue"])
    world.para()

    world.say(
        f"“Now I hear a pattern, not a creature,” {first_name} said. "
        f"“Will you help me undo the bow slowly?”"
    )
    world.say(
        f"“Yes. You hold the parcel steady, and I'll loosen the string,” {second_name} answered."
    )
    first.memes["confidence"] = 0.65
    second.memes["caution"] = 0.55
    world.para()

    world.say(
        f"Together they slipped off the bow and unfolded the paper. Nothing frightened or hurt sprang out. "
        f"Inside lay {profile['gift_label']}. The little sound had come from {profile['cause']}."
    )
    parcel.meters["sealed"] = 0.0
    parcel.meters["opened"] = 1.0
    gift.meters["revealed"] = 1.0
    gift.owner = "the children"
    world.para()

    world.say(
        f"Under the gift was a card from Gran: “{profile['note']}” "
        f"{first_name} smiled. “{profile['denial']} I was worried, and you were right to help me listen.”"
    )
    world.say(
        f"“We were both trying to be kind,” {second_name} said. “Next time, we'll listen together first.” "
        "The misunderstanding faded, and their small disagreement softened into a shared smile."
    )
    first.memes["worry"] = 0.1
    first.memes["trust"] = 0.95
    second.memes["caution"] = 0.35
    second.memes["trust"] = 0.95
    world.conflict_active = False
    world.misunderstanding_active = False
    world.resolved = True
    world.para()

    world.say(rng.choice(profile["ending"]))
    world.facts = {
        "first": first,
        "second": second,
        "parcel": parcel,
        "gift": gift,
        "sound": sound,
        "profile": profile,
        "setting": place,
        "problem_event": f"The parcel made “{profile['sound']},” so {first_name} thought {profile['misheard_as']}.",
        "clue_event": profile["clue"],
        "cause_event": f"The sound came from {profile['cause']}.",
        "gift_event": f"Inside was {profile['gift_label']}.",
        "resolution_event": (
            f"{first_name} and {second_name} listened together, opened the parcel gently, "
            "and settled their misunderstanding and disagreement."
        ),
    }
    return world


def generate_prompts(world: World) -> list[str]:
    first = world.facts["first"].id
    second = world.facts["second"].id
    return [
        "Write a gentle Scottish bedtime story about a parcel that makes a puzzling sound.",
        f"Tell a child-friendly story in which {first} and {second} misunderstand a sound, disagree, and listen together before opening a parcel.",
        "End with a cozy image showing how careful listening turns a nighttime worry into comfort.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    first = facts["first"].id
    second = facts["second"].id
    return [
        QAItem(
            question="Why did the parcel make the children worried?",
            answer=facts["problem_event"],
        ),
        QAItem(
            question=f"What clue helped {first} and {second} understand the sound?",
            answer=facts["clue_event"],
        ),
        QAItem(
            question="What was making the sound inside the parcel?",
            answer=facts["cause_event"],
        ),
        QAItem(
            question=f"How did {first} and {second} settle their disagreement?",
            answer=facts["resolution_event"],
        ),
        QAItem(
            question="What had Gran packed in the parcel?",
            answer=facts["gift_event"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parcel?",
            answer="A parcel is a wrapped package that can be sent from one person to another.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a written sound, such as a tap, a rustle, or a bright little ting, that helps a reader imagine what is happening.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or sees something but guesses the wrong meaning. Asking questions and checking clues can help clear it up.",
        ),
        QAItem(
            question="What does bedtime mean?",
            answer="Bedtime is the quiet part of the day when people get ready to rest and sleep.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        lines.append(f"  {entity.id:12} ({entity.type:16}) {' '.join(state)}")
    lines.append(f"  conflict_active={world.conflict_active}")
    lines.append(f"  misunderstanding_active={world.misunderstanding_active}")
    lines.append(f"  resolved={world.resolved}")
    return "\n".join(lines)


ASP_RULES = r"""
required(parcel).
required(scottish).
required(misunderstanding).
required(sound_effects).
required(conflict).
required(bedtime).

valid_profile(G) :-
    gift(G),
    sound_profile(G,_),
    mistaken_meaning(G,_),
    physical_cause(G,_),
    listening_clue(G,_),
    resolution(G,_).

valid_story(P,G) :-
    place(P),
    valid_profile(G),
    required(parcel),
    required(scottish),
    required(misunderstanding),
    required(sound_effects),
    required(conflict),
    required(bedtime).

#show valid_profile/1.
#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts: list[str] = []
    for feature in FEATURES:
        facts.append(asp.fact("required", feature))
    for place in PLACES:
        facts.append(asp.fact("place", place))
    for key, profile in GIFT_PROFILES.items():
        facts.extend(
            [
                asp.fact("gift", key),
                asp.fact("sound_profile", key, profile["sound"]),
                asp.fact("mistaken_meaning", key, profile["misheard_as"]),
                asp.fact("physical_cause", key, profile["cause"]),
                asp.fact("listening_clue", key, profile["clue"]),
                asp.fact("resolution", key, profile["denial"]),
            ]
        )
    return "\n".join(facts)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    symbols = asp.one_model(asp_program())
    asp_profiles = {row[0] for row in asp.atoms(symbols, "valid_profile")}
    asp_pairs = set(asp.atoms(symbols, "valid_story"))
    python_profiles = {key for key in GIFT_PROFILES if _python_profile_is_reasonable(key)}
    python_pairs = {
        (place, gift)
        for place in PLACES
        for gift in python_profiles
        if place in PLACES
    }
    if asp_profiles != python_profiles or asp_pairs != python_pairs:
        print("MISMATCH: ASP and Python disagree about reasonable parcel stories.")
        print(f"  Python profiles: {sorted(python_profiles)}")
        print(f"  ASP profiles:    {sorted(asp_profiles)}")
        print(f"  Python pairs:    {sorted(python_pairs)}")
        print(f"  ASP pairs:       {sorted(asp_pairs)}")
        return 1

    for index, gift_key in enumerate(sorted(python_profiles)):
        params = StoryParams(
            first_name="Eilidh",
            second_name="Hamish",
            place=list(PLACES)[index % len(PLACES)],
            gift=gift_key,
            seed=700 + index,
        )
        try:
            sample = generate(params)
        except StoryError as exc:
            print(f"MISMATCH: Python rejected a registry story: {exc}")
            return 1
        world = sample.world
        if (
            world is None
            or not world.resolved
            or world.conflict_active
            or world.misunderstanding_active
            or world.entities["parcel"].meters["opened"] != 1.0
            or world.entities["gift"].meters["revealed"] != 1.0
            or params.gift not in GIFT_PROFILES
            or "parcel" not in sample.story.lower()
            or "bedtime" not in sample.story.lower()
            or sample.story.count("“") < 6
            or not sample.story.strip().endswith((".", "!", "?”", ".”"))
        ):
            print(f"MISMATCH: generated story did not complete its world state for {gift_key}.")
            return 1
        if any("{" in item.answer or "}" in item.answer for item in sample.story_qa):
            print(f"MISMATCH: unresolved text appeared in story QA for {gift_key}.")
            return 1

    print("OK: ASP and Python agree, and generated parcel stories resolve their bedtime conflicts.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Scottish bedtime-story world about a puzzling parcel."
    )
    parser.add_argument("--first-name", help="Name of the first child.")
    parser.add_argument("--second-name", help="Name of the second child.")
    parser.add_argument("--place", choices=sorted(PLACES), help="Scottish bedtime setting.")
    parser.add_argument("--gift", choices=sorted(GIFT_PROFILES), help="What Gran packed.")
    parser.add_argument("-n", type=int, default=1, help="Number of stories to generate.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true", help="Show one story for each parcel gift.")
    parser.add_argument("--trace", action="store_true", help="Show the simulated world state.")
    parser.add_argument("--qa", action="store_true", help="Show prompts and questions.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    parser.add_argument("--asp", action="store_true", help="List ASP-compatible story patterns.")
    parser.add_argument("--verify", action="store_true", help="Check Python and ASP parity.")
    parser.add_argument("--show-asp", action="store_true", help="Print the ASP twin.")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    first_name = args.first_name or rng.choice(NAMES)
    if args.second_name:
        second_name = args.second_name
    else:
        second_name = rng.choice([name for name in NAMES if name.casefold() != first_name.casefold()])
    params = StoryParams(
        first_name=first_name,
        second_name=second_name,
        place=args.place or rng.choice(list(PLACES)),
        gift=args.gift or rng.choice(list(GIFT_PROFILES)),
    )
    reasonableness(params)
    return params


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.n < 1:
        parser.error("-n must be at least 1.")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}", file=sys.stderr)
            raise SystemExit(1)
        symbols = asp.one_model(asp_program())
        pairs = sorted(asp.atoms(symbols, "valid_story"))
        print(f"{len(pairs)} compatible Scottish parcel bedtime-story patterns:")
        for place, gift in pairs:
            print(f"- {PLACES[place]}; Gran's parcel holds {GIFT_PROFILES[gift]['gift_label']}.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    try:
        if args.all:
            curated = [
                StoryParams("Eilidh", "Hamish", "highland_cottage", "knitted_lamb", base_seed),
                StoryParams("Isla", "Fergus", "island_croft", "wooden_puffin", base_seed + 1),
                StoryParams("Mairi", "Rowan", "pine_glen_house", "moon_music_box", base_seed + 2),
            ]
            samples = [generate(params) for params in curated]
        else:
            for index in range(args.n):
                seed = base_seed + index
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                samples.append(generate(params))
    except StoryError as exc:
        print(f"StoryError: {exc}", file=sys.stderr)
        raise SystemExit(2)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
