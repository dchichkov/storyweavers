#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent))
        break
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


FEATURES = ("curiosity", "felt", "mystery")

PLACES = {
    "moonbeam nook": {
        "setting": "the Moonbeam reading nook",
        "clues": ("window_draft",),
        "description": "a snug room lined with picture books",
    },
    "willow puppet room": {
        "setting": "the Willow puppet room",
        "clues": ("curtain_snag", "hidden_ting"),
        "description": "a little room with a cloth puppet backdrop",
    },
    "maple craft corner": {
        "setting": "the Maple craft corner",
        "clues": ("window_draft", "hidden_ting"),
        "description": "a bright room with a low shelf for story props",
    },
}

CASES = {
    "window_draft": {
        "name": "the missing felt moon",
        "clue_type": "window_draft",
        "item": "blue felt moon",
        "item_type": "felt_moon",
        "weight": 0.2,
        "setup": "the blue felt moon had vanished from the night-sky quilt just before story time",
        "guess": "Maybe someone borrowed the moon for another game",
        "clue": "a blue thread clung to the open window latch, and the curtain puffed inward",
        "question": "Could a breeze have lifted it?",
        "reply": "Let's check behind the curtain before we decide",
        "discovery": "a gentle draft had lifted the light moon from the quilt and blown it onto the curtain's low loop",
        "action": "closed the window and gently unhooked the moon",
        "result": "the quilt's sky was whole again, and the children began their shadow story",
        "ending": "The blue moon shone on the quilt while raindrops made tiny silver dots on the closed window.",
        "found_location": "curtain loop",
        "fixture": ("window", "open window", "window", "open"),
    },
    "curtain_snag": {
        "name": "the missing felt star",
        "clue_type": "curtain_snag",
        "item": "gold felt star",
        "item_type": "felt_star",
        "weight": 0.15,
        "setup": "the gold felt star had disappeared from the evening-sky cloth backdrop",
        "guess": "Maybe someone took the star to decorate a puppet",
        "clue": "a few gold fibers caught on the backdrop's wooden tie, and the cloth was pulled slightly to one side",
        "question": "Could the tie have caught it when the backdrop moved?",
        "reply": "Let's lift the tie gently and see",
        "discovery": "the star's loose loop had snagged on a rough spot on the wooden tie as the backdrop was drawn",
        "action": "lifted the tie and freed the star without tugging its soft stitches",
        "result": "the star returned to the backdrop, ready to shine over the puppet show",
        "ending": "When the curtain opened, the gold star gleamed above Beebee's little felt wings.",
        "found_location": "wooden backdrop tie",
        "fixture": ("backdrop", "cloth puppet backdrop", "wooden_tie", "slightly_shifted"),
    },
    "hidden_ting": {
        "name": "the missing felt bell",
        "clue_type": "hidden_ting",
        "item": "red felt bell",
        "item_type": "felt_bell",
        "weight": 0.3,
        "setup": "the little red felt bell was missing from the shelf of story props",
        "guess": "Maybe it rolled into the toy basket",
        "clue": "a faint ting came from behind the closed storybook box whenever the shelf gave a small wobble",
        "question": "Could it be hiding behind the book box?",
        "reply": "Let's move the light box together, slowly",
        "discovery": "the bell's tiny brass clapper had chimed from the narrow space between the box and the wall",
        "action": "slid the light box aside and picked up the bell",
        "result": "the prop shelf was tidy again, and Beebee could ring the bell to start the story",
        "ending": "The red felt bell gave one bright ting beside the open storybook.",
        "found_location": "space behind storybook box",
        "fixture": ("storybook box", "closed storybook box", "box", "closed"),
    },
}

HELPERS = {
    "Milo": "a mouse puppet with a button nose",
    "Pip": "a rabbit puppet with long cloth ears",
    "Tansy": "a fox puppet with a rust-red tail",
    "Lulu": "a lamb puppet with a woolly head",
}

MOODS = ("patient", "eager", "thoughtful")

ATMOSPHERES = (
    "Rain tapped softly on the roof while the room waited for story time.",
    "A stripe of late sunlight crossed the floor beside the story props.",
    "The room smelled of paper, clean cloth, and yesterday's craft glue.",
    "Outside, a bird gave one small chirp, then the room grew quiet again.",
)

REFLECTIONS = (
    "Beebee tucked the clue into a little notebook so the next mystery could begin with evidence.",
    "Milo smiled at the recovered prop; asking a careful question had saved everyone a needless worry.",
    "They put the prop back in its place and agreed to check the room together before the next show.",
    "Beebee felt the pleasant warmth of a puzzle solved by looking closely and listening kindly.",
)

ASP_RULES = r"""
feature(curiosity).
feature(felt).
feature(mystery).

compatible(P, C) :-
    setting(P),
    place_clue(P, T),
    mystery_case(C, T),
    mystery_material(C, felt),
    curiosity_case(C).

compatible_story(P, C) :-
    compatible(P, C),
    feature(curiosity),
    feature(felt),
    feature(mystery).

#show compatible/2.
#show compatible_story/2.
"""


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    case: str
    helper: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _slug(value: str) -> str:
    return value.replace(" ", "_").replace("-", "_")


def python_compatibilities() -> set[tuple[str, str]]:
    pairs = set()
    for place, place_meta in PLACES.items():
        for case, case_meta in CASES.items():
            if (
                case_meta["clue_type"] in place_meta["clues"]
                and "felt" in FEATURES
                and "curiosity" in FEATURES
            ):
                pairs.add((_slug(place), _slug(case)))
    return pairs


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place!r}. Choose a registered story setting.")
    if params.case not in CASES:
        raise StoryError(f"Unknown mystery: {params.case!r}. Choose a registered felt-object mystery.")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper!r}. Choose a registered puppet friend.")
    if params.mood not in MOODS:
        raise StoryError(f"Unknown mood: {params.mood!r}. Choose a gentle curiosity mood.")
    case = CASES[params.case]
    if case["clue_type"] not in PLACES[params.place]["clues"]:
        clue_name = case["clue_type"].replace("_", " ")
        raise StoryError(
            f"{PLACES[params.place]['setting']} has no suitable {clue_name} clue for {case['name']}."
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle curiosity mystery about Beebee and a missing felt story prop."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("-n", type=int, default=1, help="number of stories to make")
    parser.add_argument("--all", action="store_true", help="make one story for every reasonable place-mystery pair")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="print the ASP compatibility model")
    parser.add_argument("--verify", action="store_true", help="check ASP parity and exercise generated stories")
    parser.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    pairs = python_compatibilities()
    candidates = [
        (place, case)
        for place, case in sorted(pairs)
        if (args.place is None or _slug(args.place) == place)
        and (args.case is None or _slug(args.case) == case)
    ]
    if not candidates:
        if args.place and args.case:
            place_meta = PLACES[args.place]
            case_meta = CASES[args.case]
            raise StoryError(
                f"{case_meta['name'].capitalize()} needs a {case_meta['clue_type'].replace('_', ' ')} "
                f"clue, which is not available in {place_meta['setting']}."
            )
        raise StoryError("No registered setting has the clues needed for that mystery.")
    place_key, case_key = rng.choice(candidates)
    place = place_key.replace("_", " ")
    case = case_key.replace("_", " ")
    # Registry keys are already space-separated except for the ASP slug.
    place = next(key for key in PLACES if _slug(key) == place_key)
    case = next(key for key in CASES if _slug(key) == case_key)
    return StoryParams(
        place=place,
        case=case,
        helper=args.helper or rng.choice(list(HELPERS)),
        mood=args.mood or rng.choice(MOODS),
    )


def asp_facts() -> str:
    from storyworlds import asp

    lines = []
    for place, meta in PLACES.items():
        place_id = _slug(place)
        lines.append(asp.fact("setting", place_id))
        for clue in meta["clues"]:
            lines.append(asp.fact("place_clue", place_id, clue))
    for case, meta in CASES.items():
        case_id = _slug(case)
        lines.append(asp.fact("mystery_case", case_id, meta["clue_type"]))
        lines.append(asp.fact("mystery_material", case_id, "felt"))
        lines.append(asp.fact("curiosity_case", case_id))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    suffix = f"\n{show}" if show else ""
    return f"{asp_facts()}\n{ASP_RULES}{suffix}\n"


def asp_compatibilities() -> set[tuple[str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "compatible"))


def asp_verify() -> int:
    from storyworlds import asp

    expected = python_compatibilities()
    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "compatible"))
    story_pairs = set(asp.atoms(model, "compatible_story"))
    parity_ok = expected == actual == story_pairs

    if parity_ok:
        print(f"OK: ASP and Python agree on all {len(actual)} compatible place-mystery pairs.")
    else:
        print("MISMATCH: ASP and Python compatibility gates disagree.")
        print("only in ASP:", sorted(actual - expected))
        print("only in Python:", sorted(expected - actual))
        print("story-rule pairs missing from compatibility:", sorted(actual - story_pairs))
        print("unexpected story-rule pairs:", sorted(story_pairs - actual))

    exercised = 0
    for index, (place_id, case_id) in enumerate(sorted(expected)):
        place = next(key for key in PLACES if _slug(key) == place_id)
        case = next(key for key in CASES if _slug(key) == case_id)
        params = StoryParams(
            place=place,
            case=case,
            helper=list(HELPERS)[index % len(HELPERS)],
            mood=MOODS[index % len(MOODS)],
            seed=9100 + index,
        )
        sample = generate(params)
        if (
            "Beebee" not in sample.story
            or "felt" not in sample.story
            or "?" not in sample.story
            or not sample.story.rstrip().endswith((".", "!", "”", '"'))
            or len(sample.story.split()) < 100
            or not sample.story_qa
            or sample.world is None
            or not sample.world.trace
        ):
            print(f"STORY CHECK FAILED for {place!r} and {case!r}.")
            return 1
        exercised += 1

    print(f"OK: exercised {exercised} generated mysteries with dialogue, clues, and endings.")
    return 0 if parity_ok else 1


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    identity = "|".join((params.place, params.case, params.helper, params.mood))
    return int.from_bytes(hashlib.blake2b(identity.encode("utf-8"), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    case = CASES[params.case]
    place_meta = PLACES[params.place]
    seed = _story_seed(params)
    atmosphere = ATMOSPHERES[seed % len(ATMOSPHERES)]
    reflection = REFLECTIONS[(seed // len(ATMOSPHERES)) % len(REFLECTIONS)]
    helper_description = HELPERS[params.helper]

    hero = Entity(
        id="beebee",
        kind="character",
        type="felt_bee_puppet",
        label="Beebee",
        meters={"attention": 0.55, "stitch_strength": 0.9},
        memes={"curiosity": 0.8, "uncertainty": 0.45, "satisfaction": 0.0},
        location=params.place,
    )
    helper = Entity(
        id=_slug(params.helper),
        kind="character",
        type="puppet_friend",
        label=params.helper,
        meters={"attention": 0.45, "reach": 0.7},
        memes={"curiosity": 0.55, "confidence": 0.4},
        location=params.place,
    )
    artifact = Entity(
        id="missing_felt_prop",
        kind="prop",
        type=case["item_type"],
        label=case["item"],
        meters={"weight": case["weight"], "found": 0.0, "safe": 1.0},
        memes={"story_value": 0.8},
        location="unknown",
    )
    fixture_id, fixture_label, fixture_type, fixture_state = case["fixture"]
    fixture = Entity(
        id=fixture_id,
        kind="fixture",
        type=fixture_type,
        label=fixture_label,
        meters={"movement": 0.2 if fixture_state != "open" else 0.8},
        memes={"familiarity": 0.7},
        location=params.place,
    )
    room = Entity(
        id="setting",
        kind="place",
        type="story_room",
        label=place_meta["setting"],
        meters={"light": 0.7, "quiet": 0.8},
        memes={"safety": 0.9},
        location=params.place,
    )
    world = World(
        place=place_meta["setting"],
        entities={entity.id: entity for entity in (hero, helper, artifact, fixture, room)},
    )

    world.say(atmosphere)
    world.say(
        f"In {place_meta['setting']}, Beebee, a small bee puppet stitched from yellow felt, "
        f"was getting ready for story time with {params.helper}, {helper_description}. "
        f"Beebee's {params.mood} curiosity made every little puzzle worth a closer look."
    )
    world.say(f"Just before the children arrived, {case['setup']}.")
    world.say(f"“{case['guess']}.“ said {params.helper}. “Let's look for a clue before we guess,” Beebee replied.")
    world.para()

    world.say(
        f"They searched {place_meta['description']} without moving anything roughly. "
        f"Then they noticed that {case['clue']}."
    )
    world.say(
        f"“{case['question']}” asked {params.helper}. "
        f"“{case['reply']},” Beebee answered."
    )
    world.say(f"That careful check solved the puzzle: {case['discovery']}.")
    world.para()

    world.say(f"Together, Beebee and {params.helper} {case['action']}.")
    world.say(f"Because they followed the clue instead of blaming anyone, {case['result']}.")
    world.say(reflection)
    world.say(case["ending"])

    hero.meters["attention"] = 1.0
    hero.memes["curiosity"] = 1.0
    hero.memes["uncertainty"] = 0.0
    hero.memes["satisfaction"] = 0.9
    helper.meters["attention"] = 0.9
    helper.memes["confidence"] = 0.85
    artifact.meters["found"] = 1.0
    artifact.location = case["found_location"]
    fixture.meters["movement"] = 0.0
    fixture.memes["familiarity"] = 1.0

    world.trace = [
        f"missing:{case['item']}",
        f"observed:{case['clue']}",
        f"discovered:{case['discovery']}",
        f"recovered:{case['action']}",
        f"restored:{case['result']}",
    ]
    world.facts = {
        "place": params.place,
        "mystery": case["name"],
        "missing_item": case["item"],
        "clue": case["clue"],
        "discovery": case["discovery"],
        "resolution": case["result"],
        "helper": params.helper,
        "material": "felt",
        "feature": "curiosity",
    }

    prompts = [
        f"Write a child-friendly curiosity mystery about Beebee finding the missing {case['item']} in {place_meta['setting']}.",
        f"Show how Beebee and {params.helper} use this clue: {case['clue']}.",
        "Include a brief spoken exchange, a careful discovery, and an ending image that shows what changed.",
    ]
    story_qa = [
        QAItem(
            question=f"What went missing in {params.helper}'s story room?",
            answer=f"The {case['item']} went missing from its story place. Beebee and {params.helper} looked for evidence before deciding what had happened.",
        ),
        QAItem(
            question="Which clue helped Beebee solve the mystery?",
            answer=f"They noticed that {case['clue']}. That observation pointed them toward the real explanation.",
        ),
        QAItem(
            question="What had happened to the missing prop?",
            answer=f"{case['discovery'].capitalize()}. The clue explained how the prop had ended up out of place.",
        ),
        QAItem(
            question="How did Beebee and the helper fix the problem?",
            answer=f"Beebee and {params.helper} {case['action']}. Afterward, {case['result']}.",
        ),
        QAItem(
            question="What did Beebee's curiosity help the friends do?",
            answer="Beebee's curiosity encouraged the friends to notice small clues and check their guesses before acting. That careful search helped them solve the mystery kindly.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is felt?",
            answer="Felt is a soft fabric made by pressing fibers together, rather than weaving them into separate threads.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the wish to learn or find out more about something. It can encourage someone to ask questions and look for clues.",
        ),
        QAItem(
            question="Why do people solve a mystery by looking for clues?",
            answer="Clues are details that can support or challenge a guess. Checking them helps people understand what happened instead of relying only on a first impression.",
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
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            bits = [f"label={entity.label}", f"type={entity.type}"]
            if entity.location:
                bits.append(f"location={entity.location}")
            if entity.meters:
                bits.append(f"meters={entity.meters}")
            if entity.memes:
                bits.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.kind} {' '.join(bits)}")
        for event in sample.world.trace:
            print(f"  event: {event}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def _all_params(args: argparse.Namespace) -> list[StoryParams]:
    pairs = [
        (place_id, case_id)
        for place_id, case_id in sorted(python_compatibilities())
        if (args.place is None or place_id == _slug(args.place))
        and (args.case is None or case_id == _slug(args.case))
    ]
    if not pairs:
        if args.place and args.case:
            reasonableness_gate(
                StoryParams(args.place, args.case, args.helper or next(iter(HELPERS)), args.mood or MOODS[0])
            )
        raise StoryError("No compatible place-mystery pairs match the requested filters.")
    result = []
    for index, (place_id, case_id) in enumerate(pairs):
        place = next(key for key in PLACES if _slug(key) == place_id)
        case = next(key for key in CASES if _slug(key) == case_id)
        result.append(
            StoryParams(
                place=place,
                case=case,
                helper=args.helper or list(HELPERS)[index % len(HELPERS)],
                mood=args.mood or MOODS[index % len(MOODS)],
                seed=(args.seed or 0) + index,
            )
        )
    return result


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        from storyworlds import asp

        model = asp.one_model(asp_program())
        print("compatible:", sorted(asp.atoms(model, "compatible")))
        print("compatible_story:", sorted(asp.atoms(model, "compatible_story")))
        return
    if args.n < 1 and not args.all:
        raise StoryError("The number of stories must be at least one.")

    if args.all:
        samples = [generate(params) for params in _all_params(args)]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        for index in range(args.n):
            story_seed = base_seed + index
            rng = random.Random(story_seed)
            params = resolve_params(args, rng)
            params.seed = story_seed
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
