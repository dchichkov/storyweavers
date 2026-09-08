#!/usr/bin/env python3
"""
A small heartwarming church storyworld about a gentle ambient sound, a bad
ending avoided, and the moral value of listening before judging.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

METERS = {"quiet", "worry", "warmth", "help"}
MEMES = {"kindness", "patience", "shame", "trust"}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in METERS:
            self.meters.setdefault(key, 0.0)
        for key in MEMES:
            self.memes.setdefault(key, 0.0)


@dataclass
class ChurchWorld:
    church: Entity
    hero: Entity
    helper: Entity
    objects: dict[str, str] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    helper_name: str
    church_name: str
    place: str
    seed: Optional[int] = None


HERO_NAMES = ["Lena", "Milo", "Nora", "Sam", "Tessa", "Owen"]
HELPER_NAMES = ["Aunt June", "Mr. Ellis", "Mara", "Pastor Rose"]
CHURCH_NAMES = ["Maple Street Church", "Little Bell Church", "Riverside Church"]
PLACES = ["the hillside", "the village square", "the rainy town", "the old neighborhood"]

SCENES = [
    {
        "id": "rain_pipe",
        "sound": "a soft tapping behind the hymn board",
        "source": "a loose rain pipe",
        "danger": "the rainwater would seep into the church wall",
        "task": "find the tapping and protect the wall",
        "complication": "the sound seemed to move whenever the wind blew",
        "turn": "held a candle near the baseboard while the helper checked outside",
        "result": "they tied the loose pipe to the stone drain",
        "ending": "When the rain stopped, the church smelled of clean earth instead of damp plaster",
    },
    {
        "id": "sparrow_roof",
        "sound": "a faint fluttering above the quiet pews",
        "source": "a sparrow caught beneath a roof screen",
        "danger": "the frightened bird might hurt its wing",
        "task": "make a safe way for the bird to leave",
        "complication": "the bird flew from beam to beam and would not come near",
        "turn": "opened the high window and waited without chasing it",
        "result": "the sparrow followed the daylight out",
        "ending": "A small feather rested on the sill while the bird sang from the elm",
    },
    {
        "id": "bell_rope",
        "sound": "a tiny creak inside the bell tower",
        "source": "a frayed bell rope rubbing against the wooden beam",
        "danger": "the rope could snap during the evening service",
        "task": "secure the rope before anyone rang the bell",
        "complication": "the highest knot was too far above the floor",
        "turn": "asked the helper to steady a ladder while carefully replacing the knot",
        "result": "the rope hung safely away from the beam",
        "ending": "The evening bell rang clearly, and every family entered without a fright",
    },
    {
        "id": "lost_lamb",
        "sound": "a muffled bleat near the side door",
        "source": "a lamb hiding behind the church's flower boxes",
        "danger": "the little animal could wander into the busy road",
        "task": "guide the lamb back to its shepherd",
        "complication": "it trembled whenever anyone moved too quickly",
        "turn": "sat on the ground and let the lamb follow a trail of clover",
        "result": "the lamb reached the shepherd's waiting arms",
        "ending": "The shepherd's grateful smile warmed the church steps",
    },
    {
        "id": "heater_click",
        "sound": "an uneven click beneath the fellowship-room floor",
        "source": "a loose cover on the old heater",
        "danger": "a child could touch the hot metal",
        "task": "mark the heater and call an adult before anyone came near",
        "complication": "the room was filling with families for the soup supper",
        "turn": "moved the chairs back and placed a bright scarf around the unsafe spot",
        "result": "the caretaker tightened the cover before supper began",
        "ending": "Children ate warm soup safely while the bright scarf stayed tied to the chair",
    },
]

INTRO_FORMS = [
    "At {place}, {hero} helped at {church}, where even small sounds seemed important.",
    "{hero} loved the peaceful rooms of {church}, especially when the morning light reached the wooden pews.",
    "On a cloudy day in {place}, {hero} arrived early at {church} to arrange flowers and hymn books.",
]

DIALOGUE_FORMS = [
    ('"I hear something," said {hero}.', '"Let us listen before we guess," replied {helper}.'),
    ('"{helper}, may I tell you about this sound?" asked {hero}.', '"Of course," said {helper}. "A careful listener can find a kind solution."'),
    ('"Should we ignore it?" asked {hero}.', '"No," said {helper}. "We will learn what it needs before we act."'),
]

ASP_RULES = r"""
needs_attention(S) :- church(S), ambient_sound(S).
safe_resolution(S) :- needs_attention(S), patient_listener(S), helper_present(S).
valid_story(S) :- safe_resolution(S).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a heartwarming church story about an ambient sound."
    )
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
    parser.add_argument("--church", choices=CHURCH_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero_name=args.name or rng.choice(HERO_NAMES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        church_name=args.church or rng.choice(CHURCH_NAMES),
        place=args.place or rng.choice(PLACES),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name not in HERO_NAMES:
        raise StoryError("The child must be a known church helper.")
    if params.helper_name not in HELPER_NAMES:
        raise StoryError("The trusted helper must be a known adult.")
    if params.church_name not in CHURCH_NAMES:
        raise StoryError("The story needs a known church.")
    if params.place not in PLACES:
        raise StoryError("The church must have a clear setting.")
    if params.hero_name == params.helper_name:
        raise StoryError("The child and helper must be different people.")


def make_world(params: StoryParams) -> ChurchWorld:
    world = ChurchWorld(
        church=Entity("church", "place", params.church_name),
        hero=Entity("hero", "child", params.hero_name),
        helper=Entity("helper", "adult", params.helper_name),
    )
    world.objects["ambient_sound"] = "unidentified"
    world.facts.update({"place": params.place, "resolved": False})
    return world


def tell_story(params: StoryParams) -> ChurchWorld:
    reasonableness_gate(params)
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else params.hero_name)
    scene = rng.choice(SCENES)
    dialogue = rng.choice(DIALOGUE_FORMS)

    world.facts.update(scene)
    world.facts["dialogue"] = dialogue
    world.facts["resolved"] = False
    world.hero.meters["worry"] = 1
    world.hero.memes["patience"] = 0
    world.helper.memes["trust"] = 1
    world.church.meters["quiet"] = 1

    intro = rng.choice(INTRO_FORMS).format(
        place=params.place, hero=params.hero_name, church=params.church_name
    )
    warning = (
        f"Then {scene['sound']} drifted through the church. "
        f"It was an ambient sound, gentle but puzzling, and {params.hero_name} worried "
        f"that {scene['danger']}."
    )
    values = {"hero": params.hero_name, "helper": params.helper_name}
    conversation = " ".join(part.format(**values) for part in dialogue)
    action = (
        f"{params.hero_name} wanted to hurry, but {params.helper_name} reminded "
        f"{params.hero_name} that kindness begins with careful listening. "
        f"Together they tried to {scene['task']}. Then {scene['complication']}. "
        f"Instead of blaming anyone, {params.hero_name} {scene['turn']}."
    )

    world.facts["resolved"] = True
    world.objects["ambient_sound"] = scene["source"]
    world.hero.meters["worry"] = 0
    world.hero.meters["help"] = 1
    world.hero.memes["patience"] = 1
    world.hero.memes["kindness"] = 1
    world.helper.memes["trust"] = 2

    ending = (
        f"{scene['result'].capitalize()}. {scene['ending']}. "
        f"{params.helper_name} smiled and said, "
        f'"The moral is simple: listen with patience, then help with care." '
        f"{params.hero_name} felt warm inside. The bad ending—leaving the warning unheard—"
        f"had been replaced by a safe and loving one."
    )
    world.facts["story"] = "\n\n".join([intro, warning, conversation, action, ending])
    return world


def prompts(world: ChurchWorld) -> list[str]:
    return [
        'Write a heartwarming church story using the words "church" and "ambient".',
        f"Tell a story about {world.hero.label} noticing an ambient sound at {world.church.label}.",
        "Include dialogue, avoid a bad ending, and show the moral value of patient kindness.",
    ]


def story_qa(world: ChurchWorld) -> list[QAItem]:
    return [
        QAItem(
            question=f"What ambient sound did {world.hero.label} notice at {world.church.label}?",
            answer=f"{world.hero.label} noticed {world.facts['sound']} at {world.church.label}.",
        ),
        QAItem(
            question=f"Why could ignoring the sound have caused a bad ending?",
            answer=f"Ignoring it could have meant that {world.facts['danger']}.",
        ),
        QAItem(
            question=f"How did {world.hero.label} and {world.helper.label} solve the problem?",
            answer=f"They tried to {world.facts['task']}. When {world.facts['complication']}, {world.hero.label} {world.facts['turn']}. Then {world.facts['result']}.",
        ),
        QAItem(
            question="What moral value did the story teach?",
            answer="The story taught the moral value of patient kindness: listen carefully before judging, and help in a safe, caring way.",
        ),
    ]


def world_qa(world: ChurchWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a church?",
            answer="A church is a place where people gather for worship, reflection, fellowship, and service.",
        ),
        QAItem(
            question="What does ambient mean?",
            answer="Ambient means surrounding or present in the background, such as a soft sound in a room.",
        ),
        QAItem(
            question="Why is patience valuable?",
            answer="Patience gives people time to understand a problem and choose a thoughtful response instead of rushing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: ChurchWorld) -> str:
    return "\n".join(
        [
            "--- trace ---",
            f"church={world.church.label}",
            f"hero={world.hero.label}",
            f"helper={world.helper.label}",
            f"objects={world.objects}",
            f"facts={{'place': {world.facts['place']!r}, 'resolved': {world.facts['resolved']!r}}}",
            f"hero_meters={world.hero.meters}",
            f"hero_memes={world.hero.memes}",
        ]
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.facts["story"],
        prompts=prompts(world),
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("church", "church"),
            asp.fact("ambient_sound", "church"),
            asp.fact("patient_listener", "hero"),
            asp.fact("helper_present", "church"),
        ]
    )


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program())
    return bool(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    try:
        import asp
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    asp_ok = bool(asp.atoms(model, "valid_story"))
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python gates.")
        return 1
    sample = generate(
        StoryParams(
            hero_name="Lena",
            helper_name="Aunt June",
            church_name="Maple Street Church",
            place="the hillside",
            seed=7,
        )
    )
    assert "church" in sample.story.lower()
    assert "ambient" in sample.story.lower()
    assert "moral" in sample.story.lower()
    assert sample.world is not None and sample.world.facts["resolved"]
    print("OK: ASP and Python gates agree; generated story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP gate: valid_story/1 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Lena", "Aunt June", "Maple Street Church", "the hillside", 11),
            StoryParams("Milo", "Mr. Ellis", "Little Bell Church", "the village square", 22),
            StoryParams("Nora", "Pastor Rose", "Riverside Church", "the old neighborhood", 33),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story in seen:
                params.seed = (params.seed or 0) + 1
                sample = generate(params)
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
