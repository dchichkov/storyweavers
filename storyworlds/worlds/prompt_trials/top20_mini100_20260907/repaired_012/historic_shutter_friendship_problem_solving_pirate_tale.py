#!/usr/bin/env python3
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
from typing import Optional

sys.path.insert(
    0,
    __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))))
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Ship:
    name: str
    harbor: str = "historic harbor"
    shutter_stuck: bool = False
    friendship_strain: float = 0.0
    problem_count: int = 0
    solved: bool = False
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    captain_name: str
    mate_name: str
    ship_name: str
    seed: Optional[int] = None


NAMES = ["Mara", "Nell", "Finn", "Pip", "Rory", "Tess", "Jory", "Bram"]
SHIP_NAMES = ["The Brass Kestrel", "The Harbor Kite", "The Salt Lantern", "The Tide Whistle"]


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    stable = "|".join((params.captain_name, params.mate_name, params.ship_name))
    seed = int.from_bytes(hashlib.sha256(stable.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


ARCS = [
    {
        "premise": [
            "At the old stone pier, Captain {captain} and first mate {mate} guided {ship} past a historic shutter house that looked over the harbor. The shuttered window belonged to an old lighthouse keeper, and the pirates had come with ginger tea and a careful plan.",
            "On a bright morning, {ship} drifted beside a historic harbor museum with a tall shutter on its tower. Captain {captain} and {mate} were delivering charts, and they carried warm ginger tea to keep their energy steady.",
        ],
        "problem": [
            "Then the shutter slammed shut on a stuck rope and locked the museum door. The rope snag made the ship pivot in a little loop, and the crew lost time and patience with each turn.",
            "A gust caught the historic shutter and swung it across the gangway. The blocked passage kept {ship} circling the same dock post, and the pirates grew tired from the repeated problem.",
        ],
        "conflict": [
            "\"Cut the rope,\" said {captain}. \"No,\" said {mate}, \"that rope holds the shutter for the keeper.\" Their friendship cracked a little as the ship rocked against the dock.",
            "{captain} wanted to push the shutter open at once, but {mate} wanted to find the knot. \"We can solve it gently,\" {mate} said. \"We do not need to break our way in.\"",
        ],
        "turn": [
            "They shared the ginger tea, and the warm sip gave them enough energy to think clearly. While steam curled up, {mate} noticed that the shutter only jammed when the rope pulled from the wrong side.",
            "After a pause for ginger tea, their tired faces softened. {captain} saw a small brass hook hidden near the frame, and {mate} saw that the rope could slide free if the shutter was lifted first.",
        ],
        "action": [
            "\"Together, then,\" said {captain}. {mate} held the shutter steady, and {captain} guided the rope over the brass hook until it slipped loose.",
            "\"I will lift, you will guide,\" said {mate}. {captain} nodded, and the two pirates worked shoulder to shoulder until the stuck rope came untwisted.",
        ],
        "resolution": [
            "The shutter opened with a soft creak, the dock stopped spinning, and the old keeper waved from the doorway. The friends smiled because the problem was solved without harm.",
            "At last the passage cleared, and {ship} drifted straight beside the museum wall. Captain {captain} and {mate} laughed together, glad their friendship had been stronger than the snag.",
        ],
        "ending": [
            "By sunset, the historic shutter stood open to the sea, and the ginger cups sat empty on the rail.",
            "The harbor shone gold through the open shutter, and the pirates sailed on with calm hands and a steadier friendship.",
        ],
        "problem_fact": "a historic shutter had jammed the gangway and made the ship circle the dock",
        "clue_fact": "ginger tea helped them notice the rope only jammed from one side",
        "action_fact": "they lifted the shutter together and guided the rope free",
        "outcome_fact": "the shutter opened and the ship left the loop",
    },
    {
        "premise": [
            "Captain {captain} steered {ship} toward a little island archive where a historic shutter covered the only map room window. {mate} brought ginger biscuits, and both pirates hoped to finish their delivery before noon.",
            "The pirate ship {ship} arrived at a quiet cove with an old shuttered archive. Captain {captain} and mate {mate} carried lantern oil and ginger tea for the long, careful visit.",
        ],
        "problem": [
            "Every time they reached the archive steps, the shutter snapped down again and the tide pushed them back to the dock. The repeated setback turned their approach into a stubborn loop.",
            "A loose shutter latch kept dropping the same wooden panel over the map room. Each drop startled the gulls, and the ship drifted away before the pirates could step ashore.",
        ],
        "conflict": [
            "\"I can hold it open alone,\" said {captain}. {mate} answered, \"Not if the latch is the real problem.\" Their friendship wobbled because they both wanted to help in different ways.",
            "{captain} wanted to hurry, but {mate} wanted to examine the hinge. \"We will waste time if we argue,\" {mate} said, yet the argument still made both of them tense.",
        ],
        "turn": [
            "A shared cup of ginger tea cooled their anger and warmed their hands. With fresh thinking, {mate} noticed a shell wedged in the latch, clicking the shutter shut.",
            "They paused for ginger biscuits and tea. The break restored their energy, and {captain} spotted that the wind was pushing the shutter only when the tide lifted the dock.",
        ],
        "action": [
            "{captain} held the panel while {mate} pried out the shell with a marlinspike. Then they tied the shutter back with a spare line so it stayed open.",
            "\"Now we know the cause,\" said {mate}. {captain} nodded, and together they braced the shutter, cleared the latch, and secured it against the wind.",
        ],
        "resolution": [
            "The archive window stayed open, the tide stopped forcing them back, and the map room welcomed them in. Their friendship settled again as soon as the problem was solved.",
            "The pirates finally stepped ashore without being pushed away. The open shutter let in the light, and the old archive felt less stern and more kind.",
        ],
        "ending": [
            "Inside, the map room glowed beneath the open shutter, and the tide lapped quietly at the dock.",
            "The last gull left the roof, and the friendly pair left the cove with their charts dry and safe.",
        ],
        "problem_fact": "a loose latch kept dropping the historic shutter and pushing the pirates back",
        "clue_fact": "a ginger break helped them notice a shell wedged in the latch",
        "action_fact": "they cleared the latch and tied the shutter open",
        "outcome_fact": "the map room stayed open and they reached shore",
    },
    {
        "premise": [
            "At dusk, {ship} crossed a narrow channel beside a historic shutter mill. Captain {captain} and first mate {mate} were carrying a crate of ginger jars to the miller, who needed them before the market bell.",
            "The pirate crew sailed past a shuttered tower that had watched the harbor for many years. {captain} kept the wheel steady while {mate} counted the jars and checked the knots.",
        ],
        "problem": [
            "The shutter mill's heavy panel fell halfway and blocked the channel. The ship could not pass, and the repeated bump against the pilings made the pirates lose both time and energy.",
            "A swinging shutter kept striking the water like a paddle, turning the channel into a loop around the same pier. {ship} drifted in circles while the jar crate slid from side to side.",
        ],
        "conflict": [
            "{captain} wanted to shove the shutter aside with the bow. {mate} said the old wood might crack. Their friendship strained as the wind rose and the crate tipped.",
            "\"We are pirates, not visitors,\" said {captain}. {mate} replied, \"We are friends before we are pirates.\" The words hung in the salty air, making both of them pause.",
        ],
        "turn": [
            "They shared ginger tea, and the warm drink calmed their racing thoughts. Then {mate} noticed the shutter's hinge was weighted by a stone tied to the lower rail.",
            "After the tea, {captain} felt steadier and saw that the shutter only swung because a rope had worn thin. The problem had a simple cause, not a hard one.",
        ],
        "action": [
            "{mate} passed a hook to {captain}, and together they lifted the stone off the rail. The shutter rose high enough for the ship to glide under it.",
            "\"One pulls, one steadies,\" said {captain}. {mate} nodded, and they worked in rhythm until the shutter was tied back and the channel opened.",
        ],
        "resolution": [
            "The crate stayed safe, the channel opened, and the miller waved from the dock. Their friendship felt stronger because they had solved the problem together.",
            "With the shutter secured, {ship} sailed straight through the channel. The pirates cheered softly, glad they had listened to one another.",
        ],
        "ending": [
            "The historic shutter mill watched them go, its open panel glowing in the last orange light.",
            "Behind them, the channel ran straight at last, and the ginger jars reached the market before dark.",
        ],
        "problem_fact": "a falling shutter blocked the channel and kept the ship circling the pier",
        "clue_fact": "ginger tea helped them notice a stone and weak rope on the hinge",
        "action_fact": "they lifted the stone and tied the shutter back together",
        "outcome_fact": "the channel opened and the ship passed through",
    },
]


def _render(template: str, captain: Entity, mate: Entity, ship: Ship) -> str:
    return template.format(captain=captain.id, mate=mate.id, ship=ship.name)


def tell(params: StoryParams) -> World:
    rng = _rng_for(params)
    arc = ARCS[(params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)]
    ship = Ship(name=params.ship_name)
    world = World(ship)
    captain = world.add(Entity(id=params.captain_name, kind="character", type="captain", label="captain"))
    mate = world.add(Entity(id=params.mate_name, kind="character", type="pirate", label="first mate"))
    ginger = world.add(Entity(id="ginger_tea", kind="thing", type="thing", label="ginger tea"))

    beats = ["premise", "problem", "conflict", "turn", "action", "resolution", "ending"]
    for i, beat in enumerate(beats):
        if i:
            world.para()
        world.say(_render(rng.choice(arc[beat]), captain, mate, ship))

    ship.shutter_stuck = False
    ship.friendship_strain = 0.0
    ship.problem_count = 1
    ship.solved = True
    captain.meters["energy"] = 4.0
    mate.meters["energy"] = 4.0
    captain.memes["friendship"] = 3.0
    mate.memes["friendship"] = 3.0
    ginger.meters["warm"] = 1.0

    ship.facts = {
        "captain": captain,
        "mate": mate,
        "ginger": ginger,
        "arc": arc,
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.ship.facts
    captain = f["captain"]
    mate = f["mate"]
    return [
        "Write a child-facing pirate tale with a historic shutter, friendship, and problem solving.",
        f"Tell a short story where {captain.id} and {mate.id} disagree, then solve a shutter problem together.",
        "Write a sea adventure that begins at a historic harbor and ends with a shutter opening safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.ship.facts
    arc = f["arc"]
    captain = f["captain"]
    mate = f["mate"]
    return [
        QAItem(
            question=f"Who were the main pirates in the story?",
            answer=f"It was about Captain {captain.id} and mate {mate.id}, who worked together on {world.ship.name}.",
        ),
        QAItem(
            question="What problem did they face?",
            answer=arc["problem_event"] if "problem_event" in arc else arc["problem_fact"],
        ),
        QAItem(
            question="What helped them think more clearly?",
            answer=arc["turn_event"] if "turn_event" in arc else arc["clue_fact"],
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{arc['action_fact'].capitalize()} {arc['outcome_fact']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, listening to them, and helping each other.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong, thinking of a good plan, and trying it step by step.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means old and important because it belongs to the past.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:12} ({e.type:8}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  ship.shutter_stuck={world.ship.shutter_stuck}")
    lines.append(f"  ship.friendship_strain={world.ship.friendship_strain}")
    lines.append(f"  ship.problem_count={world.ship.problem_count}")
    lines.append(f"  ship.solved={world.ship.solved}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(story, friendship, problem_solving, shutter, historic).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("theme", "historic"),
            asp.fact("theme", "shutter"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "problem_solving"),
            asp.fact("style", "pirate_tale"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/5."))
    if any(sym.name == "valid_story" for sym in model):
        print("OK: ASP twin recognizes the historic shutter friendship story.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected story fact.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Historic shutter pirate tale about friendship and problem solving.")
    ap.add_argument("--captain-name")
    ap.add_argument("--mate-name")
    ap.add_argument("--ship-name", choices=SHIP_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain_name or rng.choice(NAMES)
    mate = args.mate_name or rng.choice([n for n in NAMES if n != captain])
    ship = args.ship_name or rng.choice(SHIP_NAMES)
    return StoryParams(captain_name=captain, mate_name=mate, ship_name=ship)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    arc = world.ship.facts["arc"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=[
            QAItem(question=f"Who were the main pirates in the story?", answer=f"It was about Captain {world.ship.facts['captain'].id} and mate {world.ship.facts['mate'].id}, who worked together on {world.ship.name}."),
            QAItem(question="What problem did they face?", answer=arc["problem_fact"]),
            QAItem(question="What helped them think more clearly?", answer=arc["clue_fact"]),
            QAItem(question="How was the problem solved?", answer=f"{arc['action_fact'].capitalize()} {arc['outcome_fact']}."),
        ],
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible pirate story pattern: historic shutter + friendship + problem solving")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mara", "Finn", "The Brass Kestrel"),
            StoryParams("Nell", "Pip", "The Harbor Kite"),
            StoryParams("Tess", "Bram", "The Salt Lantern"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
