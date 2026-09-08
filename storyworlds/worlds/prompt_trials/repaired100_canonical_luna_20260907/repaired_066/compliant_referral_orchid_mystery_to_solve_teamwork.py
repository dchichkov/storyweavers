#!/usr/bin/env python3
"""
A standalone space-adventure storyworld about a compliant referral and a mystery
involving an orchid aboard a small research shuttle.

The story models:
- physical meters such as oxygen, light, moisture, signal, and distance
- emotional memes such as worry, curiosity, trust, courage, and relief

Its central pattern is Mystery to Solve plus Teamwork: a careful crew follows a
referral, discovers why a space orchid is fading, and repairs the tiny habitat
before the flower opens toward a new star.
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

_world_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_world_dir, "results.py")):
    _world_dir = os.path.dirname(_world_dir)
sys.path.insert(0, _world_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)


@dataclass
class ShuttleWorld:
    setting: str = "the research shuttle Starling"
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    captain_name: str
    botanist_name: str
    engineer_name: str
    orchid_name: str
    destination: str
    mystery_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    teamwork_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


CAPTAIN_NAMES = ["Luna", "Mira", "Sol", "Ari", "Nia"]
BOTANIST_NAMES = ["Ivo", "Tessa", "Pax", "June", "Ravi"]
ENGINEER_NAMES = ["Bea", "Kito", "Zara", "Oren", "Milo"]
ORCHID_NAMES = ["Starlace", "Moonbell", "Comet Bloom", "Violet Wing"]
DESTINATIONS = ["the Blue Nebula", "Aster Station", "the quiet moon Orin", "the Helix Gate"]

MYSTERIES = [
    {
        "problem": "the orchid's leaves had curled even though its soil was damp",
        "guess": "the flower had grown tired of space",
        "clue": "a silver shadow crossed the habitat sensor each time the leaves curled",
        "referral": "the station botanist's referral said to compare light, moisture, and airflow before changing the plant's water",
        "explanation": "a loose shade panel was blocking the orchid's morning light",
        "action": "tracked the shadow across the habitat window and found the loose shade panel",
        "repair": "secured the panel and turned the lamp toward the plant",
        "result": "the orchid lifted its leaves and began drinking light again",
        "image": "one pale blossom opened beside the window, facing the blue nebula",
        "lesson": "a careful referral can turn a guess into a useful plan",
    },
    {
        "problem": "the orchid's welcome beacon blinked three times and then went dark",
        "guess": "the flower had forgotten how to grow",
        "clue": "the beacon blinked whenever the cargo hatch vibrated",
        "referral": "the referral asked the crew to inspect the beacon's wires before replacing its power cell",
        "explanation": "a seed packet had slipped against the wire connector",
        "action": "followed the blinking pattern and found the seed packet pressed against the connector",
        "repair": "moved the packet, clipped the wire firmly, and tested the beacon together",
        "result": "the welcome beacon shone steadily beside the healthy stem",
        "image": "three blue lights glowed like tiny stars around the open flower",
        "lesson": "teamwork makes a small clue easier to notice and test",
    },
    {
        "problem": "a sweet mist filled the orchid cabinet during the night shift",
        "guess": "the flower was making a secret cloud",
        "clue": "the mist gathered only near a cracked cooling tube",
        "referral": "the referral recommended checking temperature lines with a buddy before opening the cabinet",
        "explanation": "the cooling tube had a hairline crack",
        "action": "used a flashlight and a mirror to inspect the tube without touching the cold metal",
        "repair": "sealed the crack with a safety patch and moved the orchid to a warm backup shelf",
        "result": "the mist cleared while the orchid rested safely under a gentle lamp",
        "image": "a clear cabinet showed bright roots and one bead of harmless water",
        "lesson": "following safety directions helps friends solve a strange problem without rushing",
    },
    {
        "problem": "the orchid's roots pointed toward the floor instead of the sunlamp",
        "guess": "the plant wanted to hide from the crew",
        "clue": "the sunlamp had been rotated toward an empty storage rack",
        "referral": "the referral said to map the lamp's angle before moving the living plant",
        "explanation": "a magnetic tool had nudged the lamp during a supply check",
        "action": "measured the lamp angle, marked the correct setting, and compared the roots' direction",
        "repair": "returned the lamp to its marked angle and placed a soft guard around its switch",
        "result": "the roots turned slowly toward the warm light",
        "image": "new green tips curved upward like tiny arrows toward the stars",
        "lesson": "patient measuring can explain a mystery better than a frightened guess",
    },
]

OPENINGS = [
    "Captain {captain} was guiding the Starling toward {destination} when the cabin alert chimed: {problem}.",
    "The research shuttle sailed between bright stars, but {captain} had a mystery to solve because {problem}.",
    "Near {destination}, {captain} checked the science cabinet and discovered that {problem}.",
    "The crew expected a quiet flight until the orchid alarm reported that {problem}.",
]

DIALOGUES = [
    '"Let us follow the referral before we change anything," {botanist} said.',
    '"I see the problem, but I do not know the cause yet," {captain} said. "We will test it together."',
    '"You watch the sensor, and I will check the habitat," {engineer} offered.',
    '"A mystery is easier when every teammate shares one careful observation," {botanist} said.',
]

TEAMWORK_LINES = [
    "{captain} read the referral aloud while {botanist} watched the leaves and {engineer} checked the controls.",
    "{engineer} held the lamp steady, {botanist} compared the notes, and {captain} kept the shuttle on its safe course.",
    "The three crewmates made a plan: one would observe, one would measure, and one would make only the approved repair.",
    "{captain} asked questions, {botanist} connected the plant's clues, and {engineer} prepared the right tool.",
]

ENDINGS = [
    "By the time the Starling reached {destination}, {result}.",
    "Soon after, {result}. The crew cheered softly inside the quiet shuttle.",
    "The mystery was solved without a risky guess: {result}.",
    "At last, {result}. The repaired habitat hummed peacefully around it.",
]


def valid_combo(params: StoryParams) -> bool:
    if not all([
        params.captain_name.strip(),
        params.botanist_name.strip(),
        params.engineer_name.strip(),
        params.orchid_name.strip(),
        params.destination.strip(),
    ]):
        return False
    if len({params.captain_name.lower(), params.botanist_name.lower(), params.engineer_name.lower()}) < 3:
        return False
    return True


def tell(params: StoryParams) -> ShuttleWorld:
    if not valid_combo(params):
        raise StoryError("crew names and destination must be distinct and nonempty")

    world = ShuttleWorld()
    captain = world.add(Entity(
        "captain", "child", params.captain_name,
        meters={"attention": 1.0, "distance_to_destination": 1.0},
        memes={"worry": 0.3, "courage": 0.8, "trust": 0.5},
    ))
    botanist = world.add(Entity(
        "botanist", "scientist", params.botanist_name,
        meters={"plant_knowledge": 1.0},
        memes={"curiosity": 1.0, "trust": 0.7},
    ))
    engineer = world.add(Entity(
        "engineer", "engineer", params.engineer_name,
        meters={"tool_readiness": 1.0},
        memes={"care": 1.0, "trust": 0.7},
    ))
    orchid = world.add(Entity(
        "orchid", "plant", params.orchid_name,
        meters={"light": 0.3, "moisture": 0.8, "airflow": 0.7, "health": 0.4},
        memes={"welcome": 1.0, "calm": 0.2},
        props={"location": "the glass habitat"},
    ))
    shuttle = world.add(Entity(
        "starling", "shuttle", "the Starling",
        meters={"oxygen": 1.0, "power": 1.0, "signal": 1.0},
        memes={"safety": 1.0},
    ))

    mystery = MYSTERIES[params.mystery_id % len(MYSTERIES)]
    world.facts.update(
        captain=captain,
        botanist=botanist,
        engineer=engineer,
        orchid=orchid,
        shuttle=shuttle,
        mystery=mystery,
        destination=params.destination,
        resolved=False,
        teamwork=True,
        referral=True,
    )

    world.say(
        OPENINGS[params.opening_id % len(OPENINGS)].format(
            captain=params.captain_name,
            destination=params.destination,
            problem=mystery["problem"],
        )
    )
    world.say(
        f"The orchid named {params.orchid_name} trembled in its glass habitat. "
        f"{params.captain_name} wondered whether {mystery['guess']}."
    )
    captain.memes["worry"] += 0.6
    world.para()

    world.say(DIALOGUES[params.dialogue_id % len(DIALOGUES)].format(
        captain=params.captain_name,
        botanist=params.botanist_name,
        engineer=params.engineer_name,
    ))
    world.say(
        f'"I received a referral from the garden team," {params.botanist_name} explained. '
        f'"It says to be compliant with the habitat checklist: {mystery["referral"]}."'
    )
    world.say(
        f'"Then we will not guess or tug at the flower," {params.captain_name} replied. '
        f'"Tell us what you see."'
    )
    world.say(
        f'"The leaves react whenever the sensor changes," {params.botanist_name} said. '
        f'"That gives us a place to begin."'
    )
    world.para()

    world.say(TEAMWORK_LINES[params.teamwork_id % len(TEAMWORK_LINES)].format(
        captain=params.captain_name,
        botanist=params.botanist_name,
        engineer=params.engineer_name,
    ))
    world.say(
        f"Together, the crew noticed that {mystery['clue']}. "
        f"The clue pointed toward {mystery['explanation']}."
    )
    world.say(
        f"{params.captain_name} said, 'I will keep the shuttle steady while we check.' "
        f"{params.engineer_name} answered, 'And I will make the repair only when we agree.'"
    )
    world.say(
        f"Carefully, the team {mystery['action']}. Then they {mystery['repair']}."
    )
    orchid.meters["light"] = 1.0
    orchid.meters["health"] = 1.0
    orchid.memes["calm"] = 1.0
    captain.memes["worry"] = 0.0
    captain.memes["relief"] = 1.0
    botanist.memes["curiosity"] = 1.4
    engineer.memes["pride"] = 1.0
    world.para()

    world.say(ENDINGS[params.ending_id % len(ENDINGS)].format(
        destination=params.destination,
        result=mystery["result"],
    ))
    world.say(f"{mystery['image'].capitalize()}.")
    world.say(
        f"{params.captain_name} smiled at the crew. 'The referral helped us begin, "
        f"but our teamwork helped us understand.'"
    )
    world.say(
        f"The Starling continued toward {params.destination}, carrying a healthy orchid "
        f"and three crewmates who knew that careful questions could make any mystery smaller."
    )
    world.facts["resolved"] = True
    return world


ASP_RULES = r"""
has_referral(orchid).
compliant(crew) :- has_referral(orchid), teamwork(crew).
mystery_solved(orchid) :- compliant(crew), observed_clue(orchid), repaired(orchid).
healthy(orchid) :- mystery_solved(orchid).
#show has_referral/1.
#show compliant/1.
#show mystery_solved/1.
#show healthy/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("has_referral", "orchid"),
        asp.fact("teamwork", "crew"),
        asp.fact("observed_clue", "orchid"),
        asp.fact("repaired", "orchid"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    names = {symbol.name for symbol in model}
    needed = {"has_referral", "compliant", "mystery_solved", "healthy"}
    if needed.issubset(names):
        sample = generate(StoryParams(
            captain_name="Luna",
            botanist_name="Ivo",
            engineer_name="Bea",
            orchid_name="Starlace",
            destination="Aster Station",
        ))
        if "orchid" in sample.story.lower() and "team" in sample.story.lower():
            print("OK: ASP and Python agree that the referral-guided team solves the orchid mystery.")
            return 0
    print("MISMATCH: ASP/Python parity check failed.")
    return 1


def generation_prompts(world: ShuttleWorld) -> list[str]:
    f = world.facts
    mystery = f["mystery"]
    return [
        f"Write a child-friendly Space Adventure about {f['captain'].label} solving this mystery: {mystery['problem']}.",
        f"Use a compliant referral, a space orchid named {f['orchid'].label}, and teamwork to reveal why the problem happened.",
        f"Tell a complete Mystery to Solve story with dialogue, a safe repair, and an ending image near {f['destination']}.",
    ]


def story_qa(world: ShuttleWorld) -> list[QAItem]:
    f = world.facts
    mystery = f["mystery"]
    captain = f["captain"].label
    botanist = f["botanist"].label
    engineer = f["engineer"].label
    orchid = f["orchid"].label
    return [
        QAItem(
            question=f"Why did {captain} worry about {orchid}?",
            answer=f"{captain} worried because {mystery['problem']}. At first, {captain} wondered whether {mystery['guess']}.",
        ),
        QAItem(
            question="What did the referral tell the crew to do?",
            answer=f"The referral told the crew to be compliant with the checklist: {mystery['referral']}.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The key clue was that {mystery['clue']}. It led the crew to understand that {mystery['explanation']}.",
        ),
        QAItem(
            question="How did the crew use teamwork?",
            answer=f"{captain}, {botanist}, and {engineer} shared observations and then {mystery['action']}. They repaired the habitat safely together.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"{mystery['result']}. The ending image is {mystery['image']}.",
        ),
    ]


def world_knowledge_qa(world: ShuttleWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orchid?",
            answer="An orchid is a flowering plant that needs suitable light, water, air, and care to stay healthy.",
        ),
        QAItem(
            question="What is a referral?",
            answer="A referral is guidance that directs someone to useful information, a skilled helper, or a safe next step.",
        ),
        QAItem(
            question="What does compliant mean?",
            answer="Compliant means following a rule, request, or safety instruction carefully.",
        ),
        QAItem(
            question="Why is teamwork useful during a mystery?",
            answer="Teamwork lets people share different observations and skills, so they can test clues more safely and clearly.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A Space Adventure orchid mystery storyworld.")
    parser.add_argument("--captain")
    parser.add_argument("--botanist")
    parser.add_argument("--engineer")
    parser.add_argument("--orchid")
    parser.add_argument("--destination")
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
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    botanist = args.botanist or rng.choice([name for name in BOTANIST_NAMES if name != captain])
    engineer_pool = [name for name in ENGINEER_NAMES if name not in {captain, botanist}]
    engineer = args.engineer or rng.choice(engineer_pool)
    orchid = args.orchid or rng.choice(ORCHID_NAMES)
    destination = args.destination or rng.choice(DESTINATIONS)
    params = StoryParams(
        captain_name=captain,
        botanist_name=botanist,
        engineer_name=engineer,
        orchid_name=orchid,
        destination=destination,
        mystery_id=rng.randrange(len(MYSTERIES)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        teamwork_id=rng.randrange(len(TEAMWORK_LINES)),
        ending_id=rng.randrange(len(ENDINGS)),
        seed=args.seed,
    )
    if not valid_combo(params):
        raise StoryError("captain, botanist, and engineer must have distinct names")
    return params


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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


def dump_trace(world: ShuttleWorld) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.kind:8}) "
            f"meters={entity.meters} memes={entity.memes} props={entity.props}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')} teamwork={world.facts.get('teamwork')}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show healthy/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program())
            print("ASP model:")
            for symbol in model:
                print(symbol)
        except Exception as exc:
            print(f"ASP mode unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams("Luna", "Ivo", "Bea", "Starlace", "Aster Station", 0, 0, 0, 0, 0),
            StoryParams("Mira", "Tessa", "Kito", "Moonbell", "the Blue Nebula", 1, 1, 1, 1, 1),
            StoryParams("Sol", "Pax", "Zara", "Comet Bloom", "the quiet moon Orin", 2, 2, 2, 2, 2),
            StoryParams("Ari", "June", "Oren", "Violet Wing", "the Helix Gate", 3, 3, 3, 3, 3),
        ]
        samples = [generate(params) for params in params_list]
    else:
        samples = []
        seen = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 20):
            rng = random.Random(base_seed + attempts)
            attempts += 1
            try:
                sample = generate(resolve_params(args, rng))
            except StoryError:
                continue
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
        header = ""
        if args.all:
            header = f"### {sample.params.captain_name} and the orchid {sample.params.orchid_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
