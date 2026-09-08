#!/usr/bin/env python3
"""
A gentle slice-of-life storyworld about a psychiatric clinic, a worried visitor,
and the small sounds that help a difficult morning become manageable.

Narrative instruments:
- Suspense
- Inner Monologue
- Sound Effects
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


METERS = {"anxiety", "calm", "time", "connection", "safety"}
MEMES = {"worry", "hope", "trust", "shame", "relief"}


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
class Clinic:
    name: str
    place: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in METERS:
            self.meters.setdefault(key, 0.0)
        for key in MEMES:
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    visitor_name: str
    visitor_type: str
    counselor_name: str
    clinic_name: str
    place: str
    seed: Optional[int] = None


VISITOR_NAMES = ["Luna", "Mara", "Theo", "Iris", "Nico", "June", "Sam"]
COUNSELOR_NAMES = ["Dr. Vale", "Ms. Rowan", "Dr. Chen", "Nurse Ellis"]
CLINIC_NAMES = ["Willow Street Clinic", "Harbor House", "The Lantern Center", "Maple Room"]
PLACES = ["a quiet neighborhood", "the corner of town", "a tree-lined street", "the market district"]

VISITOR_TYPES = {
    "Luna": "girl",
    "Mara": "girl",
    "Theo": "boy",
    "Iris": "girl",
    "Nico": "boy",
    "June": "girl",
    "Sam": "boy",
}


@dataclass(frozen=True)
class SCENE:
    id: str
    ordinary_detail: str
    warning: str
    sound: str
    worry: str
    action: str
    interruption: str
    turn: str
    ending: str
    object_name: str


SCENES = [
    SCENE(
        "waiting_room",
        "Luna counted the blue squares in the waiting-room rug",
        "the appointment card was missing from the pocket where she had placed it",
        "Click-click, the wall clock moved toward the hour",
        "without the card, she feared she might explain everything badly",
        "check the front pocket of her bag and ask the receptionist for help",
        "the automatic door opened with a sudden hiss",
        "she named the worry aloud instead of letting it grow in secret",
        "the card appeared beneath her library book, and the waiting room felt less like a trap",
        "appointment card",
    ),
    SCENE(
        "rainy_hall",
        "Luna shook rain from her yellow umbrella by the clinic door",
        "a soft alarm began blinking near the hallway",
        "Beep... beep... the sound paused, then returned",
        "she wondered whether the alarm meant she had to leave before her visit",
        "ask the receptionist what the alarm meant and wait beside the green chair",
        "a cart squeaked around the corner and blocked the hallway",
        "the receptionist explained that the alarm marked a low battery in a supply cabinet",
        "the alarm stopped, and Luna kept her umbrella open to dry beside the warm radiator",
        "yellow umbrella",
    ),
    SCENE(
        "tea_table",
        "Luna stirred honey into a paper cup of tea",
        "the last spoon on the table clattered to the floor",
        "Clink! The spoon spun beneath the chairs",
        "she feared everyone had noticed how shaky her hands were",
        "pick up the spoon slowly and tell the counselor that the morning felt difficult",
        "the cup trembled when a truck rumbled past outside",
        "she put both feet on the floor and let the counselor listen without rushing",
        "the tea cooled beside her while her hands grew steadier",
        "paper cup",
    ),
    SCENE(
        "front_desk",
        "Luna watched a receptionist place colored stickers on folders",
        "her name did not appear on the first list the receptionist checked",
        "Whirr, the printer fed out another pale sheet",
        "she wondered if she had come on the wrong day",
        "show the text reminder on her phone and ask the counselor to confirm the appointment",
        "the phone screen dimmed just as she held it out",
        "the receptionist checked one more page and found Luna's name",
        "a fresh green sticker marked the folder waiting for her",
        "phone reminder",
    ),
    SCENE(
        "quiet_room",
        "Luna sat beneath a window where a small plant leaned toward the light",
        "a key turned somewhere beyond the closed counseling-room door",
        "Krrr... the old hinge sighed",
        "she imagined a hard conversation waiting on the other side",
        "tell the counselor she needed a slow beginning and choose the chair near the plant",
        "the lights flickered once above the quiet room",
        "the counselor lowered the lamp and invited Luna to begin with one ordinary fact",
        "the plant's new leaf shone in the softer light",
        "small plant",
    ),
    SCENE(
        "bus_arrival",
        "Luna arrived early and watched buses wash silver light over the windows",
        "the bus she planned to take home rolled away before her appointment began",
        "Hiss! The bus doors closed and the engine sighed",
        "she feared being stranded after a tiring visit",
        "ask the counselor to help her write down another route",
        "the route map folded along the wrong crease",
        "they found a later bus and wrote its number on a small card",
        "the new route card rested safely beside her appointment reminder",
        "route card",
    ),
]


ASP_RULES = r"""
needs_support(V) :- visitor(V), anxious(V), appointment(V).
can_begin(V) :- needs_support(V), helper(H), offers_time(H).
valid_story(V) :- can_begin(V), safe_place.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("visitor", "visitor"),
            asp.fact("anxious", "visitor"),
            asp.fact("appointment", "visitor"),
            asp.fact("helper", "counselor"),
            asp.fact("offers_time", "counselor"),
            asp.fact("safe_place"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return bool(asp.atoms(model, "valid_story"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a suspenseful slice-of-life story in a psychiatric clinic."
    )
    parser.add_argument("--name", choices=VISITOR_NAMES)
    parser.add_argument("--counselor", choices=COUNSELOR_NAMES)
    parser.add_argument("--clinic", choices=CLINIC_NAMES)
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
    name = args.name or rng.choice(VISITOR_NAMES)
    return StoryParams(
        visitor_name=name,
        visitor_type=VISITOR_TYPES[name],
        counselor_name=args.counselor or rng.choice(COUNSELOR_NAMES),
        clinic_name=args.clinic or rng.choice(CLINIC_NAMES),
        place=args.place or rng.choice(PLACES),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.visitor_name not in VISITOR_NAMES:
        raise StoryError("The visitor must have a name from the clinic registry.")
    if params.counselor_name not in COUNSELOR_NAMES:
        raise StoryError("The counselor must be a registered clinic helper.")
    if params.clinic_name not in CLINIC_NAMES:
        raise StoryError("The clinic must be a registered place.")
    if params.place not in PLACES:
        raise StoryError("The story needs a recognizable neighborhood setting.")


def make_world(params: StoryParams) -> Clinic:
    clinic = Clinic(params.clinic_name, params.place)
    clinic.entities["visitor"] = Entity("visitor", "person", params.visitor_name)
    clinic.entities["counselor"] = Entity("counselor", "person", params.counselor_name)
    clinic.meters["anxiety"] = 1.0
    clinic.meters["calm"] = 0.0
    clinic.meters["time"] = 1.0
    clinic.meters["connection"] = 0.0
    clinic.meters["safety"] = 1.0
    clinic.memes["worry"] = 1.0
    clinic.memes["hope"] = 0.5
    clinic.memes["trust"] = 0.0
    clinic.facts.update(
        {
            "visitor_name": params.visitor_name,
            "counselor_name": params.counselor_name,
            "clinic_name": params.clinic_name,
            "place": params.place,
            "resolved": False,
        }
    )
    return clinic


def inner_monologue(clinic: Clinic) -> str:
    visitor = clinic.facts["visitor_name"]
    thought = clinic.facts["thought"]
    clinic.memes["worry"] += 0.5
    return f"{visitor} thought, *{thought}*."


def begin_scene(clinic: Clinic) -> str:
    scene: SCENE = clinic.facts["scene"]
    clinic.meters["anxiety"] += 0.5
    clinic.memes["worry"] += 0.5
    return f"{scene.ordinary_detail.capitalize()}. Then {scene.warning}."


def exchange(clinic: Clinic) -> str:
    scene: SCENE = clinic.facts["scene"]
    visitor = clinic.facts["visitor_name"]
    counselor = clinic.facts["counselor_name"]
    clinic.meters["connection"] += 0.5
    clinic.memes["trust"] += 0.5
    clinic.memes["hope"] += 0.5
    return (
        f'"I am not sure what that means," {visitor} said. '
        f'"We can check it together," said {counselor}. '
        f'"Tell me what you noticed, and we will take one small step."'
    )


def resolve(clinic: Clinic) -> str:
    scene: SCENE = clinic.facts["scene"]
    visitor = clinic.facts["visitor_name"]
    counselor = clinic.facts["counselor_name"]
    clinic.meters["anxiety"] = 0.5
    clinic.meters["calm"] = 1.0
    clinic.meters["connection"] = 1.0
    clinic.meters["safety"] = 1.0
    clinic.memes["worry"] = 0.5
    clinic.memes["trust"] = 1.0
    clinic.memes["relief"] = 1.0
    clinic.facts["resolved"] = True
    return (
        f"{visitor} followed the plan: {scene.turn}. {scene.ending.capitalize()}. "
        f'"You did not have to solve the whole morning alone," {counselor} said. '
        f'"You asked, and we made it clearer together."'
    )


def tell_story(params: StoryParams) -> Clinic:
    clinic = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = rng.choice(SCENES)
    thoughts = [
        "Maybe the sound is a warning meant only for me",
        "I can stay for one minute and see what happens",
        "If I say the worry plainly, someone may understand it",
        "I do not need perfect words to ask for help",
    ]
    clinic.facts["scene"] = scene
    clinic.facts["thought"] = rng.choice(thoughts)

    intro = (
        f"On a regular morning in {params.place}, {params.visitor_name} walked to "
        f"{params.clinic_name} for a psychiatric appointment with {params.counselor_name}."
    )
    start = begin_scene(clinic)
    thought = inner_monologue(clinic)
    sound = f"{scene.sound} The familiar sound made the quiet clinic feel suddenly suspenseful."
    talk = exchange(clinic)
    middle = (
        f"{params.visitor_name} decided to {scene.action}. "
        f"Before the worry could settle, {scene.interruption}. "
        f"{params.visitor_name} paused, listened, and kept one hand on the {scene.object_name}."
    )
    ending = resolve(clinic)

    arrangements = [
        [intro, start, thought, sound, talk, middle, ending],
        [intro + " " + start, thought, sound + " " + talk, middle, ending],
        [intro, start + " " + thought, talk, sound + " " + middle, ending],
    ]
    story = "\n\n".join(rng.choice(arrangements))
    clinic.facts["story"] = story
    clinic.facts["scene_id"] = scene.id
    return clinic


def prompts(clinic: Clinic) -> list[str]:
    return [
        'Write a slice-of-life psychiatric clinic story using suspense, inner monologue, and sound effects.',
        (
            f"Tell a story about {clinic.facts['visitor_name']} visiting "
            f"{clinic.name}, where an ordinary sound makes a small worry feel urgent."
        ),
        "Include a brief exchange in which asking a question changes what the visitor decides to do.",
    ]


def story_qa(clinic: Clinic) -> list[QAItem]:
    scene: SCENE = clinic.facts["scene"]
    visitor = clinic.facts["visitor_name"]
    counselor = clinic.facts["counselor_name"]
    return [
        QAItem(
            question=f"Why did {visitor} visit {clinic.name}?",
            answer=(
                f"{visitor} visited {clinic.name} in {clinic.place} for a psychiatric "
                f"appointment with {counselor}."
            ),
        ),
        QAItem(
            question=f"What made the ordinary moment suspenseful for {visitor}?",
            answer=(
                f"The suspense began when {scene.warning}. The sound, {scene.sound}, "
                f"made {visitor} worry that the visit might go wrong."
            ),
        ),
        QAItem(
            question=f"How did speaking with {counselor} change what {visitor} did?",
            answer=(
                f"{counselor} invited {visitor} to describe what was noticed and take "
                f"one small step, so {visitor} chose to {scene.action}."
            ),
        ),
        QAItem(
            question=f"What showed that the problem had eased by the end?",
            answer=(
                f"{scene.ending.capitalize()}. The counselor also reminded {visitor} "
                "that asking for help had made the morning clearer."
            ),
        ),
    ]


def world_qa(clinic: Clinic) -> list[QAItem]:
    return [
        QAItem(
            question="What does psychiatric mean?",
            answer=(
                "Psychiatric relates to mental health, including feelings, thoughts, "
                "behavior, and the care people may receive from trained professionals."
            ),
        ),
        QAItem(
            question="Why can a familiar sound feel suspenseful?",
            answer=(
                "A familiar sound can feel suspenseful when someone is already worried "
                "and does not yet know what the sound means."
            ),
        ),
        QAItem(
            question="Why can saying a worry aloud help?",
            answer=(
                "Saying a worry aloud can help another person understand it, check the "
                "facts, and work with the speaker on a manageable next step."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(clinic: Clinic) -> str:
    return "\n".join(
        [
            "--- trace ---",
            f"clinic={clinic.name}",
            f"place={clinic.place}",
            f"scene={clinic.facts.get('scene_id')}",
            f"meters={clinic.meters}",
            f"memes={clinic.memes}",
            f"resolved={clinic.facts.get('resolved')}",
        ]
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    clinic = tell_story(params)
    return StorySample(
        params=params,
        story=clinic.facts["story"],
        prompts=prompts(clinic),
        story_qa=story_qa(clinic),
        world_qa=world_qa(clinic),
        world=clinic,
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


def asp_verify() -> int:
    import asp

    python_ok = True
    asp_ok = asp_valid()
    if python_ok != asp_ok:
        print("MISMATCH between ASP and Python gates.")
        return 1

    sample = generate(
        StoryParams(
            visitor_name="Luna",
            visitor_type="girl",
            counselor_name="Dr. Vale",
            clinic_name="Willow Street Clinic",
            place="a quiet neighborhood",
            seed=17,
        )
    )
    if "psychiatric" not in sample.story:
        raise AssertionError("Generated story omitted the domain word.")
    if not any(sound in sample.story for sound in ["Click-click", "Beep", "Clink", "Whirr", "Krrr", "Hiss"]):
        raise AssertionError("Generated story omitted sound effects.")
    if not sample.world.facts["resolved"]:
        raise AssertionError("Generated story did not resolve.")
    print("OK: ASP and Python gates agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP gate: valid_story/1 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(
                visitor_name="Luna",
                visitor_type="girl",
                counselor_name="Dr. Vale",
                clinic_name="Willow Street Clinic",
                place="a quiet neighborhood",
                seed=101,
            ),
            StoryParams(
                visitor_name="Theo",
                visitor_type="boy",
                counselor_name="Ms. Rowan",
                clinic_name="Harbor House",
                place="a tree-lined street",
                seed=202,
            ),
            StoryParams(
                visitor_name="Iris",
                visitor_type="girl",
                counselor_name="Dr. Chen",
                clinic_name="The Lantern Center",
                place="the corner of town",
                seed=303,
            ),
        ]
        samples = [generate(params) for params in params_list]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(50, target * 50):
            rng = random.Random(base_seed + index)
            index += 1
            params = resolve_params(args, rng)
            try:
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
