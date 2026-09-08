#!/usr/bin/env python3
"""A child-facing superhero quest about Luna, a grizzly, and a brave choice."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    weather: str
    mood: str


@dataclass
class StoryParams:
    place: str
    mission: str
    name: str
    helper: str
    threat: str
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class Quest:
    lost: str
    danger: str
    first_plan: str
    setback: str
    clue: str
    truth: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "cloud_canyon": Scene("Cloud Canyon", "golden wind", "bright and echoing"),
    "moon_forest": Scene("Moon Forest", "cool silver rain", "quiet and sparkling"),
    "sunny_harbor": Scene("Sunny Harbor", "warm sea air", "busy and cheerful"),
}

MISSIONS = {
    "rescue_beacon": "the rescue beacon",
    "save_bridge": "the little sky bridge",
    "return_star": "the fallen star lantern",
    "protect_village": "the village's bell",
}

HEROES = {"Luna": "girl", "Milo": "boy", "Ari": "child", "Nova": "girl"}
HELPERS = {"Pip": "fox", "Bramble": "rabbit", "Echo": "bird", "Tess": "girl"}
THREATS = {"grizzly": "grizzly", "storm": "storm", "shadow": "shadow beast"}

ROUTES = (
    "map_first",
    "question_first",
    "quiet_first",
    "signal_first",
    "promise_first",
    "race_clock",
)

QUESTS = {
    "rescue_beacon": Quest(
        lost="the rescue beacon had gone dark",
        danger="a frightened grizzly guarded the rocky path",
        first_plan="planned to fly over the canyon and grab the beacon",
        setback="thick clouds hid the safe landing stones",
        clue="deep paw marks circled a patch of crushed blue flowers",
        truth="the grizzly had carried the beacon away from falling rocks and was trapped beside it",
        repair="calmed the grizzly, cleared the stones, and carried the beacon home together",
        lesson="a scary guard may also be a worried helper",
        ending="the beacon flashed three friendly lights across the canyon",
    ),
    "save_bridge": Quest(
        lost="the little sky bridge had broken in the middle",
        danger="a grizzly stood beneath the broken ropes",
        first_plan="planned to leap across and tie a new rope",
        setback="the first rope was too short to reach the far post",
        clue="fresh claw marks pointed toward a fallen cedar",
        truth="the grizzly had pulled the cedar away from the bridge but needed help moving the last branch",
        repair="worked with the grizzly to drag the branch aside and weave a strong bridge",
        lesson="strength becomes kindness when it is shared",
        ending="children crossed the mended bridge while the grizzly watched from the sunny bank",
    ),
    "return_star": Quest(
        lost="the fallen star lantern had vanished into a dark ravine",
        danger="a grizzly's deep growl echoed below",
        first_plan="planned to shine a cape-light into the ravine",
        setback="the narrow beam showed only drifting dust",
        clue="a warm golden glow gleamed beneath a pile of pine needles",
        truth="the grizzly had covered the lantern to protect it from rain",
        repair="thanked the grizzly, uncovered the lantern, and carried it back in a soft basket",
        lesson="care can look mysterious until we learn its reason",
        ending="the star lantern glowed above the village like a tiny new moon",
    ),
    "protect_village": Quest(
        lost="the village's bell had stopped ringing",
        danger="a grizzly blocked the bell tower steps",
        first_plan="planned to use a super-strength jump to reach the bell",
        setback="the tower shook before the jump could begin",
        clue="a trail of honey led from the bell rope to a loose wooden beam",
        truth="the grizzly had climbed up to pull the rope loose after smelling honey on the beam",
        repair="removed the sticky beam, fixed the rope, and shared a safer honey treat",
        lesson="a careful question can prevent a dangerous mistake",
        ending="the village bell rang gently while the grizzly danced below",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero quest with Luna and a grizzly.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--mission", choices=sorted(MISSIONS))
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("--threat", choices=sorted(THREATS))
    parser.add_argument("--route", choices=ROUTES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mission) for place in sorted(PLACES) for mission in sorted(MISSIONS)]


ASP_RULES = """
valid(Place,Mission) :- place(Place), mission(Mission).
safe_mission(Mission) :- mission(Mission), not impossible(Mission).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            *(asp.fact("place", place) for place in PLACES),
            *(asp.fact("mission", mission) for mission in MISSIONS),
        ]
    )


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    symbols = asp.one_model(asp_program())
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = set(asp_valid_combos())
    if python_pairs != asp_pairs:
        print("MISMATCH:", sorted(python_pairs - asp_pairs), sorted(asp_pairs - python_pairs))
        return 1
    print(f"OK: ASP gate matches valid_combos() ({len(python_pairs)} combos).")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if not args.place or pair[0] == args.place
    ]
    if args.mission:
        choices = [pair for pair in choices if pair[1] == args.mission]
    if not choices:
        raise StoryError("No valid superhero quest fits those options.")
    place, mission = rng.choice(choices)
    name = args.name or "Luna"
    helper_choices = [item for item in sorted(HELPERS) if item != name] or sorted(HELPERS)
    return StoryParams(
        place=place,
        mission=mission,
        name=name,
        helper=args.helper or rng.choice(helper_choices),
        threat=args.threat or rng.choice(sorted(THREATS)),
        route=args.route or rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.mission,
            params.name,
            params.helper,
            params.threat,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    quest = QUESTS[params.mission]
    rng = story_rng(params)
    world = World(scene)
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=HEROES.get(params.name, "child"),
            meters={"bravery": 0.6, "energy": 0.8},
            memes={"hope": 0.7},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type=HELPERS[params.helper],
            meters={"care": 0.8},
            memes={"trust": 0.6},
        )
    )
    threat = world.add(
        Entity(
            id=params.threat,
            kind="character" if params.threat == "grizzly" else "force",
            type=THREATS[params.threat],
            memes={"fear": 0.4},
        )
    )

    openings = {
        "map_first": (
            f"{hero.id} drew a map of {scene.place}. The map showed {quest.lost}, "
            f"a winding trail, and the place where {params.threat} had been seen."
        ),
        "question_first": (
            f'"What happened here?" {hero.id} asked at {scene.place}. '
            f"{quest.lost.capitalize()}, and the trail disappeared near the trees."
        ),
        "quiet_first": (
            f"{scene.place} was {scene.mood} under {scene.weather}. "
            f"Then {hero.id} discovered that {quest.lost}."
        ),
        "signal_first": (
            f"A weak signal blinked above {scene.place}. It meant that {quest.lost}, "
            f"so {hero.id} tightened the bright cape and began the quest."
        ),
        "promise_first": (
            f"{hero.id} made a promise beside {scene.place}: no one would be left alone. "
            f"The promise mattered because {quest.lost}."
        ),
        "race_clock": (
            f"The morning clock was ticking at {scene.place}. Before sunset, "
            f"{hero.id} had to solve the problem: {quest.lost}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"{helper.id} joined {hero.id} with a coil of silver rope and a calm voice.",
                f"{hero.id} and {helper.id} packed a lantern, a snack, and a soft blanket.",
                f"{helper.id} checked the path while {hero.id} listened for a safe way forward.",
            ]
        )
    )
    world.para()

    world.say(f"The danger was clear: {quest.danger}.")
    world.say(
        rng.choice(
            [
                f"{hero.id} felt a nervous flutter. Inner monologue whispered, 'A real hero can be brave and still stop to think.'",
                f"Inside, {hero.id} thought, 'If I rush, I may make the danger worse. I need a kinder plan.'",
                f"{hero.id} told themself, 'My cape is bright, but careful listening is my strongest power.'",
            ]
        )
    )
    world.say(
        f'"Should we charge ahead?" {helper.id} asked. "{hero.id}, what do you notice?"'
    )
    world.say(
        rng.choice(
            [
                f'"I notice the fear, but not the reason for it," {hero.id} replied. "Let us scour the path for clues."',
                f'"No rushing," {hero.id} said. "We will scour the ground and ask before we act."',
                f'"We need the whole story," {hero.id} answered. "Let us scour the trail together."',
            ]
        )
    )
    hero.memes["patience"] = 1
    world.para()

    world.say(f"At first, the superhero {quest.first_plan}.")
    world.say(f"But the plan failed because {quest.setback}.")
    hero.meters["energy"] -= 0.2
    world.say(
        rng.choice(
            [
                f"{hero.id} landed safely and admitted, 'That plan will not work. I am glad we tested it before someone got hurt.'",
                f"{helper.id} held the rope while {hero.id} changed the plan instead of pretending the first idea was perfect.",
                f"The setback did not end the quest. It gave the heroes a better question to ask.",
            ]
        )
    )
    world.say(f"Then their careful search found a decisive clue: {quest.clue}.")
    world.say(
        f"The clue changed what {hero.id} knew. The {params.threat} was not simply blocking the quest; something important had happened."
    )
    world.para()

    world.say(f"The truth was that {quest.truth}.")
    threat.memes["fear"] = 0.0
    threat.memes["trust"] = 0.8
    hero.memes["compassion"] = 1
    hero.meters["bravery"] = 1.0
    world.say(
        f'"We thought you were the danger," {hero.id} told the {params.threat}. '
        f'"We are sorry. Can we help?"'
    )
    world.say(
        f'The {params.threat} gave a slow nod, and {helper.id} said, "A hero listens before choosing blame."'
    )
    world.say(f"Together, they {quest.repair}.")
    world.say(f"{hero.id} wrote the lesson in the quest notebook: {quest.lesson}.")
    world.say(
        rng.choice(
            [
                f"At sunset, {quest.ending}.",
                f"When the quest was complete, {quest.ending}.",
                f"The happy ending arrived when {quest.ending}.",
            ]
        )
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        threat=threat,
        scene=scene,
        quest=quest,
        mission=params.mission,
        truth=quest.truth,
        repair=quest.repair,
        lesson=quest.lesson,
        ending=quest.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    quest = facts["quest"]
    return [
        f"Write a child-friendly superhero story about {facts['hero'].id} completing a quest in {facts['scene'].place}.",
        f"Include a grizzly, an inner monologue, a careful search, and a happy ending where {quest.ending}.",
        f"Show how {facts['hero'].id} learns that {quest.lesson}, then resolves the danger by choosing to {quest.repair}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    quest = facts["quest"]
    hero = facts["hero"].id
    helper = facts["helper"].id
    threat = facts["threat"].id
    return [
        QAItem(
            question=f"What quest did {hero} begin in {facts['scene'].place}?",
            answer=f"{hero} began a quest because {quest.lost}.",
        ),
        QAItem(
            question=f"Why did {hero} stop and scour the path instead of rushing toward the {threat}?",
            answer=f"{hero} realized that {quest.danger}. Careful searching revealed the clue that explained the {threat}'s actions.",
        ),
        QAItem(
            question=f"What did the heroes learn from the clue?",
            answer=f"They learned that {quest.truth}. The {threat} was not simply an enemy.",
        ),
        QAItem(
            question=f"How did {helper} help {hero} finish the quest?",
            answer=f"{helper} helped {hero} stay calm and work with the {threat}; together they {quest.repair}.",
        ),
        QAItem(
            question=f"What lesson made the ending happy?",
            answer=f"{hero} learned that {quest.lesson}, and the happy ending showed that {quest.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can an inner monologue help a hero?",
            answer="An inner monologue lets a hero notice feelings, consider choices, and decide on a safe and kind action.",
        ),
        QAItem(
            question="What should someone do before blaming a frightening animal?",
            answer="They should keep a safe distance, ask what happened, look for evidence, and get a trusted adult or trained helper.",
        ),
        QAItem(
            question="What makes a superhero ending happy?",
            answer="A happy ending shows that the danger is resolved, people or animals are safer, and the characters have learned or repaired something together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = [
        "== prompts ==",
        *(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1)),
        "",
        "== story qa ==",
    ]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  truth={world.facts['truth']}")
    lines.append(f"  repair={world.facts['repair']}")
    return "\n".join(lines)


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="cloud_canyon",
        mission="rescue_beacon",
        name="Luna",
        helper="Pip",
        threat="grizzly",
        route="question_first",
        seed=101,
    ),
    StoryParams(
        place="moon_forest",
        mission="return_star",
        name="Luna",
        helper="Echo",
        threat="grizzly",
        route="quiet_first",
        seed=202,
    ),
    StoryParams(
        place="sunny_harbor",
        mission="protect_village",
        name="Nova",
        helper="Tess",
        threat="grizzly",
        route="signal_first",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combinations = asp_valid_combos()
        print(f"{len(combinations)} compatible combos:\n")
        for place, mission in combinations:
            print(f"  {place:16} {mission}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        limit = max(args.n * 50, 50)
        while len(samples) < args.n and attempts < limit:
            current_seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(current_seed))
            except StoryError as error:
                print(error)
                return
            params.seed = current_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
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

    for index, sample in enumerate(samples):
        header = "### curated story" if args.all else (
            f"### variant {index + 1}" if len(samples) > 1 else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
