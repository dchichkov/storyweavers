#!/usr/bin/env python3
"""
A small, standalone Adventure storyworld about a pewter signal bell, repeated
messages, kind choices, and the thoughts that help an explorer choose safely.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_STORYWORLDS_ROOT = next(
    (
        parent
        for parent in Path(__file__).resolve().parents
        if parent.name == "storyworlds" and (parent / "results.py").is_file()
    ),
    None,
)
if _STORYWORLDS_ROOT is not None and str(_STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(_STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        forms = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return forms[case]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    hero: str
    companion: str
    place: str
    scenario: str
    telling_mode: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Adventure:
    key: str
    destination: str
    deadline: str
    obstacle_location: str
    obstacle: str
    danger: str
    signal_text: str
    reply: str
    find_location: str
    traveler: str
    traveler_speaker: str
    reveal: str
    safe_plan: str
    kindness_action: str
    outcome: str
    ending: str
    signal_repeats: int = 3
    route_is_safe: bool = True
    kindness_is_concrete: bool = True
    has_complete_ending: bool = True
    risk: float = 0.85


HERO_NAMES = ["Eval", "Mira", "Tavi", "Noor", "Ari"]
COMPANION_NAMES = ["Nia", "Bram", "Luz", "Pip", "Kit"]
PLACES = [
    "the Fern Ridge trail",
    "the Silver Pine Pass",
    "the Bluebell Highlands",
    "the Windward Range",
]
TELLING_MODES = ["arrival", "warning", "promise", "question", "mystery"]

ADVENTURES = [
    Adventure(
        key="bridge_signal",
        destination="Fernwatch Lookout",
        deadline="before evening fog filled the pass",
        obstacle_location="the gorge crossing",
        obstacle="the footbridge had twisted sideways, and one handrope sagged above the gorge",
        danger="A rushed step could send them slipping toward the rocks below.",
        signal_text="Three knocks, a pause, and three more knocks came from the far bank.",
        reply="A lantern blinked from the old shelter across the gorge.",
        find_location="the old shelter",
        traveler="a young trail keeper",
        traveler_speaker="The keeper",
        reveal="the keeper had been sheltering there since the wind twisted the bridge",
        safe_plan=(
            "{hero} and {companion} followed the keeper's directions along a marked "
            "ridge path, then used their climbing rope as a handline at its narrow turn."
        ),
        kindness_action=(
            "{hero} and {companion} wrapped the shivering keeper in their spare wool "
            "blanket and waited until the keeper's fingers could grip the rope."
        ),
        outcome=(
            "Together, they reached Fernwatch Lookout before the fog closed the pass, "
            "and the keeper could guide the next hikers."
        ),
        ending=(
            "At Fernwatch, the pewter bell caught the last strip of sunlight, and the "
            "keeper's lantern answered from the ridge below."
        ),
        risk=0.9,
    ),
    Adventure(
        key="flooded_ford",
        destination="Alder Camp",
        deadline="before dusk",
        obstacle_location="the Willow Creek crossing",
        obstacle="rain had hidden the stepping stones beneath a fast, swollen creek",
        danger="The middle of the current was too strong for a safe crossing.",
        signal_text=(
            "Three clicks against a rock, a pause, and three more clicks came from "
            "beyond the rushing water."
        ),
        reply="A courier lifted a blue parcel from a gravel hump beyond the current.",
        find_location="the gravel hump",
        traveler="a young post courier",
        traveler_speaker="The courier",
        reveal=(
            "the courier had reached the gravel hump when the stepping stones "
            "disappeared under the rising creek"
        ),
        safe_plan=(
            "{hero} and {companion} walked upstream to the broad rescue bend, anchored "
            "their climbing rope to a red stake, and tossed its loop across."
        ),
        kindness_action=(
            "{hero} and {companion} offered the courier dry mittens and waited until "
            "the courier could hold the rope firmly."
        ),
        outcome=(
            "The courier crossed through the shallows, well away from the fast current, "
            "and reached Alder Camp with the parcel dry."
        ),
        ending=(
            "At Alder Camp, the pewter bell shone beside the dry parcel as a pale sunset "
            "opened over the creek."
        ),
        risk=0.95,
    ),
    Adventure(
        key="snowbound_shepherd",
        destination="North Lantern Shelter",
        deadline="before nightfall",
        obstacle_location="the high switchback",
        obstacle="fresh snow had buried the painted trail markers beneath the ridge",
        danger="The exposed ridge was steep, and the new snow hid its edges.",
        signal_text=(
            "Three mirror flashes, a pause, and three more flashes appeared beyond "
            "the snow-covered ridge."
        ),
        reply="A small lamp appeared in a stone hut below the ridge.",
        find_location="the stone hut",
        traveler="an old shepherd",
        traveler_speaker="The shepherd",
        reveal=(
            "the shepherd had stayed inside after new snow buried the marked "
            "switchback"
        ),
        safe_plan=(
            "{hero} and {companion} followed the pines down to a sheltered hollow, "
            "marking each turn with chalk and staying off the exposed ridge."
        ),
        kindness_action=(
            "{hero} shared the flask of berry tea while {companion} wrapped the "
            "shepherd in a spare scarf and listened to the shepherd's directions."
        ),
        outcome=(
            "They led the shepherd along the sheltered trail to North Lantern Shelter "
            "before nightfall."
        ),
        ending=(
            "At North Lantern Shelter, the pewter bell chimed under clear stars while "
            "three bright tracks wound safely through the snow."
        ),
        risk=0.8,
    ),
]

ADVENTURE_BY_KEY = {adventure.key: adventure for adventure in ADVENTURES}
FEATURES = ["Repetition", "Kindness", "Inner Monologue", "Adventure"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adventure storyworld about a pewter signal bell and a kind rescue."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--companion", choices=COMPANION_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--scenario", choices=sorted(ADVENTURE_BY_KEY))
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
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


def python_reasonableness_gate(adventure: Adventure) -> bool:
    """Require a repeated clue, a safe route, a concrete kindness, and an ending."""
    return bool(
        adventure.signal_repeats >= 2
        and adventure.route_is_safe
        and adventure.kindness_is_concrete
        and adventure.has_complete_ending
        and "pewter" in adventure.ending.lower()
        and adventure.obstacle
        and adventure.danger
        and adventure.signal_text
        and adventure.reply
        and adventure.safe_plan
        and adventure.kindness_action
        and adventure.outcome
    )


def validate_params(params: StoryParams) -> Adventure:
    if params.hero not in HERO_NAMES:
        raise StoryError(f"Unknown hero {params.hero!r}; choose a registered explorer.")
    if params.companion not in COMPANION_NAMES:
        raise StoryError(
            f"Unknown companion {params.companion!r}; choose a registered trailmate."
        )
    if params.hero == params.companion:
        raise StoryError("The hero and companion must be different people.")
    if params.place not in PLACES:
        raise StoryError(f"Unknown trail setting {params.place!r}.")
    if params.telling_mode not in TELLING_MODES:
        raise StoryError(f"Unknown telling mode {params.telling_mode!r}.")
    if params.seed is not None and not isinstance(params.seed, int):
        raise StoryError("The seed must be an integer or None.")
    adventure = ADVENTURE_BY_KEY.get(params.scenario)
    if adventure is None:
        raise StoryError(f"Unknown adventure scenario {params.scenario!r}.")
    if not python_reasonableness_gate(adventure):
        raise StoryError(
            f"Scenario {adventure.key!r} has no reasonable, kind, and safe resolution."
        )
    return adventure


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    companion_choices = [name for name in COMPANION_NAMES if name != hero]
    companion = args.companion or rng.choice(companion_choices)
    params = StoryParams(
        hero=hero,
        companion=companion,
        place=args.place or rng.choice(PLACES),
        scenario=args.scenario or rng.choice(ADVENTURES).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )
    validate_params(params)
    return params


def asp_facts() -> str:
    import asp

    lines = [asp.fact("feature", feature) for feature in FEATURES]
    for adventure in ADVENTURES:
        lines.append(asp.fact("scenario", adventure.key))
        if adventure.signal_repeats >= 2:
            lines.append(asp.fact("repeated_signal", adventure.key))
        if adventure.route_is_safe:
            lines.append(asp.fact("safe_route", adventure.key))
        if adventure.kindness_is_concrete:
            lines.append(asp.fact("kindness_plan", adventure.key))
        if "pewter" in adventure.ending.lower():
            lines.append(asp.fact("pewter_bell", adventure.key))
        if adventure.has_complete_ending and adventure.outcome:
            lines.append(asp.fact("complete_ending", adventure.key))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S) :-
    scenario(S),
    repeated_signal(S),
    safe_route(S),
    kindness_plan(S),
    pewter_bell(S),
    complete_ending(S).

#show reasonable/1.
#show feature/1.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n\n{ASP_RULES}\n"


def _asp_reasonable_scenarios() -> tuple[list[str], list[str]]:
    import asp

    model = asp.one_model(asp_program())
    scenarios = sorted(item[0] for item in asp.atoms(model, "reasonable"))
    features = sorted(item[0] for item in asp.atoms(model, "feature"))
    return scenarios, features


def asp_verify() -> int:
    try:
        asp_scenarios, asp_features = _asp_reasonable_scenarios()
    except Exception as exc:
        print(f"ASP verification could not run: {exc}")
        return 1

    python_scenarios = sorted(
        adventure.key
        for adventure in ADVENTURES
        if python_reasonableness_gate(adventure)
    )
    if asp_scenarios != python_scenarios:
        print("MISMATCH: the ASP and Python reasonableness gates disagree.")
        print(f"Python: {python_scenarios}")
        print(f"ASP:    {asp_scenarios}")
        return 1
    if asp_features != sorted(FEATURES):
        print("MISMATCH: the ASP feature registry is incomplete.")
        print(f"Expected: {sorted(FEATURES)}")
        print(f"ASP:      {asp_features}")
        return 1

    for index, adventure in enumerate(ADVENTURES, 1):
        params = StoryParams(
            hero="Eval",
            companion="Nia",
            place=PLACES[index % len(PLACES)],
            scenario=adventure.key,
            telling_mode=TELLING_MODES[index % len(TELLING_MODES)],
            seed=700 + index,
        )
        try:
            sample = generate(params)
        except StoryError as exc:
            print(f"FAILED: could not generate {adventure.key}: {exc}")
            return 1
        story = sample.story
        if (
            "pewter" not in story.lower()
            or "thought, *" not in story
            or "said." not in story
            or "replied." not in story
            or adventure.destination not in story
            or not sample.story_qa
            or not sample.world_qa
            or sample.world is None
            or sample.world.facts.get("story_end") != "safe_and_reconciled"
        ):
            print(f"FAILED: generated {adventure.key} did not meet the story contract.")
            return 1
        if any(not item.question or not item.answer for item in sample.story_qa):
            print(f"FAILED: generated {adventure.key} has incomplete story QA.")
            return 1

    invalid = StoryParams(
        hero="Unknown",
        companion="Nia",
        place=PLACES[0],
        scenario=ADVENTURES[0].key,
        telling_mode=TELLING_MODES[0],
    )
    try:
        generate(invalid)
    except StoryError:
        pass
    else:
        print("FAILED: an invalid hero choice was not rejected.")
        return 1

    print(
        "OK: ASP and Python agree, and every registered adventure generates "
        "a complete story."
    )
    return 0


def _opening(params: StoryParams, adventure: Adventure, rng: random.Random) -> list[str]:
    hero = params.hero
    companion = params.companion
    place = params.place
    destination = adventure.destination
    deadline = adventure.deadline

    if params.telling_mode == "warning":
        return [
            f'"Keep the bell dry," {companion} called as they climbed {place}.',
            f"The little pewter signal bell was bound for {destination} {deadline}.",
        ]
    if params.telling_mode == "promise":
        return [
            f"{hero} had promised to bring a pewter signal bell to {destination} {deadline}.",
            f"{companion} checked the climbing rope as they started along {place}.",
        ]
    if params.telling_mode == "question":
        return [
            f'"Do you think our pewter bell can reach {destination}?" {companion} asked.',
            f'"We will find out together," {hero} replied as they set off along {place} {deadline}.',
        ]
    if params.telling_mode == "mystery":
        return [
            f"A silver haze curled over {place} as {hero} and {companion} began their climb.",
            f"In {hero}'s pack, the pewter bell was meant to guide hikers at {destination} {deadline}.",
        ]
    return [
        f"{hero} and {companion} started along {place}, carrying a little pewter signal bell.",
        f"They were taking it to {destination} {deadline}.",
    ]


def _format_plan(text: str, hero: str, companion: str) -> str:
    return text.format(hero=hero, companion=companion)


def generate(params: StoryParams) -> StorySample:
    adventure = validate_params(params)
    rng = random.Random(params.seed)
    world = World()

    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type="explorer",
            label="young explorer",
            phrase=params.hero,
            location=params.place,
            meters={"stamina": 0.82, "alertness": 0.45},
            memes={"determination": 0.75, "concern": 0.2},
            traits=["curious", "steady"],
        )
    )
    companion = world.add(
        Entity(
            id=params.companion,
            kind="character",
            type="trailmate",
            label="trailmate",
            phrase=params.companion,
            location=params.place,
            meters={"stamina": 0.86, "alertness": 0.55},
            memes={"attentiveness": 0.65, "kindness": 0.7},
            traits=["observant", "helpful"],
        )
    )
    bell = world.add(
        Entity(
            id="signal_bell",
            kind="thing",
            type="pewter_bell",
            label="signal bell",
            phrase="the pewter bell",
            owner=hero.id,
            location="inside the explorer's pack",
            meters={"ring_count": 0.0, "condition": 1.0},
            memes={"purpose": 0.8},
        )
    )
    hazard = world.add(
        Entity(
            id="trail_hazard",
            kind="place",
            type="trail_obstacle",
            label="blocked trail",
            phrase=adventure.obstacle,
            location=adventure.obstacle_location,
            meters={"risk": adventure.risk, "safe_passage": 0.0},
            memes={"uncertainty": 0.9},
        )
    )
    traveler = world.add(
        Entity(
            id="stranded_traveler",
            kind="character",
            type="traveler",
            label=adventure.traveler,
            phrase=adventure.traveler,
            location=adventure.find_location,
            meters={"warmth": 0.25, "safety": 0.0},
            memes={"worry": 0.9, "hope": 0.25},
        )
    )

    world.facts.update(
        scenario=adventure.key,
        destination=adventure.destination,
        obstacle=adventure.obstacle,
        risk=adventure.danger,
        repeated_signal=adventure.signal_text,
        safe_method=adventure.safe_plan,
        helper=companion.id,
        material="pewter",
        story_end="in_progress",
    )

    for sentence in _opening(params, adventure, rng):
        world.say(sentence)
    world.say(
        rng.choice(
            [
                f"At {adventure.obstacle_location}, their direct trail ended: {adventure.obstacle}.",
                f"The map's neat line stopped at {adventure.obstacle_location}, where {adventure.obstacle}.",
                f"Then the trail changed at {adventure.obstacle_location}: {adventure.obstacle}.",
            ]
        )
    )
    world.say(adventure.danger)
    world.para()

    world.say(adventure.signal_text)
    hero.meters["alertness"] = 0.95
    companion.memes["attentiveness"] = 1.0
    world.facts["signal_heard"] = True
    world.say(
        f'"That pattern came again," {companion.id} said. "Someone is trying to reach us."'
    )
    world.say(
        f'{hero.id} wanted to hurry toward the destination. Then {hero.id} thought, '
        '"*The lookout can wait. Someone is out there, and we can help without rushing.*"'
    )
    world.say(
        f'"Let us answer with the bell," {companion.id} said. '
        f'"Three notes, a pause, and three more."'
    )
    world.say(
        f'"I will ring it, and we will wait for their reply," {hero.id} replied.'
    )
    bell.meters["ring_count"] = 6.0
    bell.location = "in the explorer's hand"
    world.facts["signal_answered"] = True
    world.say(
        f"{hero.id} rang the pewter bell three times, paused, and repeated the pattern."
    )
    world.say(adventure.reply)
    hero.memes["careful_choice"] = 1.0
    world.facts["reply_received"] = True
    world.para()

    world.say(
        f"The reply led them to {adventure.find_location}, where they found "
        f"{adventure.traveler}."
    )
    world.say(f"They learned that {adventure.reveal}.")
    world.say(
        f'"I thought I was alone," {traveler.pronoun("subject")} said.'
    )
    world.say(
        f'"You are not alone now," {hero.id} replied. '
        '"We will find the safe way together."'
    )
    traveler.memes["hope"] = 0.8
    world.facts["traveler_found"] = True
    world.para()

    safe_plan = _format_plan(adventure.safe_plan, hero.id, companion.id)
    kindness_action = _format_plan(adventure.kindness_action, hero.id, companion.id)
    world.say(safe_plan)
    hazard.meters["risk"] = 0.3
    hazard.meters["safe_passage"] = 0.8
    hazard.location = "a safely marked route"
    world.facts["safe_route_chosen"] = True
    world.say(kindness_action)
    traveler.meters["warmth"] = 0.8
    traveler.memes["worry"] = 0.25
    traveler.memes["reassurance"] = 1.0
    world.facts["kindness_given"] = True
    world.say(adventure.outcome)

    traveler.meters["safety"] = 1.0
    traveler.location = adventure.destination
    hero.location = adventure.destination
    companion.location = adventure.destination
    bell.location = adventure.destination
    bell.memes["purpose"] = 1.0
    hero.memes["relief"] = 1.0
    companion.memes["shared_pride"] = 1.0
    world.facts.update(
        stage="resolved",
        traveler_safe=True,
        bell_delivered=True,
        story_end="safe_and_reconciled",
    )
    world.para()
    world.say(adventure.ending)

    inner_thought = (
        "The lookout can wait. Someone is out there, and we can help without rushing."
    )
    prompts = [
        (
            f"Write an Adventure about {params.hero} and {params.companion}, who use a "
            f"pewter signal bell to help {adventure.traveler} at {adventure.destination}."
        ),
        (
            "Tell a child-friendly story where a repeated signal, a kind choice, and an "
            "inner thought help explorers find a safe route."
        ),
        (
            f"Write a story set on {params.place} whose ending shows how the characters "
            "helped one another."
        ),
    ]
    story_qa = [
        QAItem(
            question="What made the explorers' direct route dangerous?",
            answer=(
                f"The direct route was dangerous because {adventure.obstacle}. "
                f"{adventure.danger} They stopped instead of rushing ahead."
            ),
        ),
        QAItem(
            question="How did the repeated signal help the explorers?",
            answer=(
                f"They heard the repeated pattern: {adventure.signal_text} "
                f"After they answered with three pewter-bell notes, {adventure.reply} "
                f"That reply led them to {adventure.find_location}."
            ),
        ),
        QAItem(
            question="What did the inner thought change about their choice?",
            answer=(
                f"{params.hero} thought, “{inner_thought}” That thought helped "
                f"{params.hero} stop hurrying, answer the signal, and choose a safer "
                "way to help."
            ),
        ),
        QAItem(
            question="How did the explorers show kindness to the stranded traveler?",
            answer=(
                f"{kindness_action} Their care helped the traveler feel warmer and "
                "ready to continue along the safe route."
            ),
        ),
        QAItem(
            question="How did they get the traveler to safety?",
            answer=(
                f"{safe_plan} {adventure.outcome} Their careful route kept them away "
                "from the danger on the direct trail."
            ),
        ),
        QAItem(
            question="What final image shows that the adventure ended well?",
            answer=(
                f"{adventure.ending} The bell reached its destination, and the traveler "
                "was no longer alone or in danger."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="How can repetition help someone send a signal?",
            answer=(
                "A repeated pattern is easier to recognize than a single sound or "
                "flash, so someone listening can tell that it was sent on purpose."
            ),
        ),
        QAItem(
            question="What does kindness look like during an adventure?",
            answer=(
                "Kindness means noticing what another person needs and offering help "
                "that makes the next step safer or less frightening."
            ),
        ),
        QAItem(
            question="What is an inner monologue?",
            answer=(
                "An inner monologue is a character's private thought. It can help a "
                "character pause, understand a problem, and choose what to do."
            ),
        ),
        QAItem(
            question="What is pewter?",
            answer=(
                "Pewter is a soft, silvery metal traditionally made mostly from tin. "
                "In this adventure, a pewter bell carries a signal across the trail."
            ),
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
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            details = []
            if entity.location:
                details.append(f"location={entity.location}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} {' '.join(details)}")
        print(f"  story facts: {sample.world.facts}")

    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
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
        raise SystemExit(asp_verify())

    try:
        if not args.all and args.n < 1:
            raise StoryError("The number of stories must be at least one.")

        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []

        if args.all:
            curated = [
                StoryParams(
                    hero="Eval",
                    companion="Nia",
                    place=PLACES[0],
                    scenario="bridge_signal",
                    telling_mode="arrival",
                    seed=101,
                ),
                StoryParams(
                    hero="Mira",
                    companion="Bram",
                    place=PLACES[1],
                    scenario="flooded_ford",
                    telling_mode="question",
                    seed=202,
                ),
                StoryParams(
                    hero="Tavi",
                    companion="Luz",
                    place=PLACES[2],
                    scenario="snowbound_shepherd",
                    telling_mode="mystery",
                    seed=303,
                ),
            ]
            samples = [generate(params) for params in curated]
        else:
            seen: set[str] = set()
            attempts = 0
            max_attempts = max(50, args.n * 20)
            while len(samples) < args.n and attempts < max_attempts:
                attempts += 1
                attempt_seed = base_seed + attempts
                params = resolve_params(args, random.Random(attempt_seed))
                params.seed = attempt_seed
                sample = generate(params)
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)

        asp_note = ""
        if args.asp:
            try:
                asp_scenarios, _ = _asp_reasonable_scenarios()
            except Exception as exc:
                raise StoryError(f"ASP check could not run: {exc}") from exc
            requested = sorted({sample.params.scenario for sample in samples})
            rejected = [key for key in requested if key not in asp_scenarios]
            if rejected:
                raise StoryError(
                    "The ASP reasonableness gate rejected: " + ", ".join(rejected)
                )
            asp_note = (
                "ASP gate accepted the generated scenario(s): "
                + ", ".join(requested)
                + "."
            )

        if args.json:
            if asp_note:
                print(asp_note, file=sys.stderr)
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(
                    json.dumps(
                        [sample.to_dict() for sample in samples],
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            return

        if asp_note:
            print(asp_note)
        for index, sample in enumerate(samples):
            header = ""
            if args.all:
                header = (
                    f"### {sample.params.hero} and {sample.params.companion} "
                    f"at {sample.params.place}"
                )
            elif len(samples) > 1:
                header = f"### adventure {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
