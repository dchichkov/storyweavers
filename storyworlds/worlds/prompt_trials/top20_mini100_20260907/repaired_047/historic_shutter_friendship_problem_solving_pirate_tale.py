#!/usr/bin/env python3
"""
A standalone pirate-tale storyworld about friendship and problem solving.

Seed words:
- historic
- shutter

Style:
- Pirate Tale
- Friendship
- Problem Solving
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[4]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
friendship_story(S) :- setting(S), has_friendship(S), has_problem_solving(S), pirate_tale(S).
good_solution(S) :- friendship_story(S), solved_with_teamwork(S).
shutter_story(S) :- friendship_story(S), has_shutter(S).
"""

PLACE = "harbor inn"

HISTORIC_RELICS = ["old map case", "captain's ledger", "museum key", "wooden compass box"]
PROBLEMS = [
    "a stuck shutter",
    "a jammed locker latch",
    "a creaking cargo door",
    "a crooked window latch",
]
CREW_NAMES = ["Mara", "Finn", "Jory", "Sable", "Pip", "Tessa", "Rook", "Nell"]
SHIPMATES = ["first mate", "deckhand", "lookout", "cook", "helmsman", "young sailor"]
TOOLS = ["oiled cloth", "small wrench", "spare peg", "brass hinge pin", "lantern"]

OPENINGS = [
    "The {place} sat beside the water, and its old walls had seen many tides.",
    "At the edge of the quay, the {place} held a secret from a more historic age.",
    "By lantern light, the {place} looked brave enough for any pirate with a patient heart.",
    "The wind carried salt through the {place}, and the shutters rattled like drumbeats.",
]

TROUBLES = [
    "One shutter would not open, and the whole room grew dim and gloomy.",
    "A shutter jammed fast against the frame, and the sea air could not reach the room.",
    "The wooden shutter stuck tight, making the room hot and awkward for everyone inside.",
    "The old shutter squealed and refused to move, blocking the little breeze they needed.",
]

FAILED_TRIES = [
    "Pulling harder only made the shutter groan louder.",
    "A quick shove shook the frame but did not free the wood.",
    "Hitting the shutter with a palm made it stick even more.",
    "Yanking the handle only tilted it crooked in its frame.",
]

CLUES = [
    "a narrow line of salt had crusted along one hinge",
    "the bottom edge scraped the sill with a tiny white mark",
    "one rusty pin sat half out of the hinge",
    "the wood had swollen where the rain had touched it",
]

REPLIES = [
    "“Easy now,” said {friend}, “let's look before we tug again.”",
    "“A good crew fixes the cause, not just the fuss,” said {friend}.",
    "“Friendship means we solve it together,” said {friend} with a grin.",
    "“Hold fast a moment,” said {friend}, “I think the hinge is the trouble.”",
]

PLANS = [
    "They tried the shutter gently, then checked every hinge one by one.",
    "They shared the work: one held the wood steady while the other cleaned the pin.",
    "They tested the frame, found the jam, and moved only the piece that was truly stuck.",
    "They listened to the creak, followed it to the hinge, and repaired the worn spot first.",
]

RESOLUTIONS = [
    "With the pin reset and the wood eased free, the shutter swung open at last.",
    "After a little cleaning and careful pressing, the shutter opened to the sea breeze.",
    "The fixed hinge gave way, and the shutter moved smooth as a gull in flight.",
    "Once they lined it up again, the shutter opened with a soft wooden sigh.",
]

ENDING_IMAGES = [
    "Sunlight poured across the old floorboards, bright as treasure.",
    "A cool breeze sailed through the room, and the crew laughed in relief.",
    "The room filled with salt air, and the old inn felt friendly again.",
    "Light and wind returned together, making the historic walls glow warm and calm.",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    friend: str
    place: str
    problem: str
    relic: str
    tool: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    trouble: str
    failed_try: str
    clue: str
    dialogue: str
    plan: str
    resolution: str
    ending: str


@dataclass
class World:
    place: str = PLACE
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        for e in self.entities.values():
            bits = []
            if e.owner:
                bits.append(f"owner={e.owner!r}")
            if e.meters:
                bits.append(f"meters={dict(e.meters)}")
            if e.memes:
                bits.append(f"memes={dict(e.memes)}")
            if e.label:
                bits.append(f"label={e.label!r}")
            lines.append(f"  {e.id:10} ({e.kind:10}) {' '.join(bits)}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


def valid_problem_choices() -> list[str]:
    return list(PROBLEMS)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("A pirate story needs a named sailor.")
    if not params.friend.strip():
        raise StoryError("A pirate story needs a friend for the crew to help.")
    if params.problem not in PROBLEMS:
        raise StoryError("The problem must be a small, fixable shipboard or harbor trouble.")
    if not params.place.strip():
        raise StoryError("The setting needs a real place for the story to happen.")
    if not params.relic.strip():
        raise StoryError("The tale needs a historic object to ground the pirate world.")
    if not params.tool.strip():
        raise StoryError("The crew needs a simple tool for problem solving.")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "harbor_inn"),
        asp.fact("has_friendship", "harbor_inn"),
        asp.fact("has_problem_solving", "harbor_inn"),
        asp.fact("pirate_tale", "harbor_inn"),
        asp.fact("has_shutter", "harbor_inn"),
        asp.fact("historic", "harbor_inn"),
        asp.fact("problem", "stuck_shutter"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program("#show friendship_story/1.\n#show good_solution/1.\n#show shutter_story/1.")
    model = asp.one_model(program)
    atoms = {(sym.name, tuple(arg.name if arg.type != arg.type.NUMBER else arg.number for arg in sym.arguments)) for sym in model}
    expected = {
        ("friendship_story", ("harbor_inn",)),
        ("good_solution", ("harbor_inn",)),
        ("shutter_story", ("harbor_inn",)),
    }
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld about friendship and problem solving.")
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--place")
    ap.add_argument("--problem", choices=valid_problem_choices())
    ap.add_argument("--relic")
    ap.add_argument("--tool")
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
    params = StoryParams(
        name=rng.choice(CREW_NAMES),
        friend=rng.choice(SHIPMATES),
        place=PLACE,
        problem=rng.choice(PROBLEMS),
        relic=rng.choice(HISTORIC_RELICS),
        tool=rng.choice(TOOLS),
        seed=rng.randrange(2**31),
    )
    if args.name:
        params.name = args.name
    if args.friend:
        params.friend = args.friend
    if args.place:
        params.place = args.place
    if args.problem:
        params.problem = args.problem
    if args.relic:
        params.relic = args.relic
    if args.tool:
        params.tool = args.tool
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World(place=params.place)
    world.add(Entity(id="hero", kind="character", label=params.name))
    world.add(Entity(id="friend", kind="character", label=params.friend))
    world.add(Entity(id="relic", kind="thing", label=params.relic))
    world.add(Entity(id="tool", kind="thing", label=params.tool))
    world.facts.update(
        place=params.place,
        problem=params.problem,
        historic=params.relic,
        tool=params.tool,
        friendship=True,
        problem_solving=True,
        pirate_tale=True,
        resolved=False,
    )
    return world


def pick(rng: random.Random, options: list[str]) -> str:
    return rng.choice(options)


def tell_story(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    relic = world.get("relic")
    tool = world.get("tool")
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = Scenario(
        key=params.problem.replace(" ", "_"),
        trouble=pick(rng, TROUBLES),
        failed_try=pick(rng, FAILED_TRIES),
        clue=pick(rng, CLUES),
        dialogue=pick(rng, REPLIES).format(friend=friend.label),
        plan=pick(rng, PLANS),
        resolution=pick(rng, RESOLUTIONS),
        ending=pick(rng, ENDING_IMAGES),
    )
    opening = pick(rng, OPENINGS).format(place=params.place)

    hero.bump_meme("friendship")
    friend.bump_meme("friendship")

    world.say(opening)
    world.say(
        f"{hero.label} and {friend.label} found the {relic.label} beside the wall, a historic little thing that made the room feel like a captain's memory."
    )
    world.say(f"But then {scenario.trouble}")
    world.para()

    hero.bump_meme("worry")
    friend.bump_meme("care")
    world.say(f"They tried to fix it fast, yet {scenario.failed_try}")
    world.say(scenario.dialogue)
    world.say(
        f"{hero.label} held the {tool.label} while {friend.label} watched the shutter closely, and together they noticed {scenario.clue}."
    )
    world.para()

    hero.bump_meter("work", 1)
    friend.bump_meter("work", 1)
    tool.bump_meter("use", 1)
    world.say(scenario.plan)
    world.say(
        f"Using the {tool.label}, they eased the frame, set the hinge straight, and kept talking until the wood stopped fighting them."
    )
    world.say(f"At last, {scenario.resolution}")
    world.para()

    hero.bump_meme("joy")
    friend.bump_meme("joy")
    world.say(
        f"The two mates laughed like old deck friends, because friendship had helped them solve the problem without breaking the old thing."
    )
    world.say(
        f"{scenario.ending} The {relic.label} stayed safe on the sill, and the once-stuck shutter now opened easy as a sail in the wind."
    )
    world.facts.update(resolved=True, scenario=scenario.key, ending_image=scenario.ending)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a pirate tale about {f['place']} where friendship helps solve a {f['problem']}.",
        f"Tell a child-friendly story that uses the words historic and shutter and ends with a warm solution.",
        f"Write a story about {f['historic']} and {f['tool']} in a {f['place']} with pirate-style dialogue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.get("hero").label
    friend = world.get("friend").label
    relic = world.get("relic").label
    return [
        QAItem(
            question="What problem did the crew have to solve?",
            answer=f"They had to fix {f['problem']}.",
        ),
        QAItem(
            question=f"What historic object did {hero} and {friend} find?",
            answer=f"They found the {relic}.",
        ),
        QAItem(
            question="What clue helped them understand the problem?",
            answer=f"They noticed {self_or_fact(f, 'clue')}.",
        ),
        QAItem(
            question="How did friendship help the story end?",
            answer="The friends worked together, talked through the trouble, and fixed the problem without ruining the old place.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The shutter opened easily and {f['ending_image'].lower()}",
        ),
    ]


def self_or_fact(facts: dict, key: str) -> str:
    return str(facts.get(key, "a helpful clue"))


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help one another, and stay loyal like good shipmates.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a trouble, finding its cause, and choosing a good fix.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means old and important because it belongs to the past and may have a story worth remembering.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return world.trace()


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        name="Mara",
        friend="first mate",
        place=PLACE,
        problem="a stuck shutter",
        relic="captain's ledger",
        tool="oiled cloth",
        seed=11,
    ),
    StoryParams(
        name="Finn",
        friend="lookout",
        place=PLACE,
        problem="a crooked window latch",
        relic="old map case",
        tool="brass hinge pin",
        seed=29,
    ),
    StoryParams(
        name="Nell",
        friend="cook",
        place=PLACE,
        problem="a creaking cargo door",
        relic="museum key",
        tool="small wrench",
        seed=47,
    ),
]


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_solution/1."))
    return sorted(set(asp.atoms(model, "good_solution")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_solution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible pirate tales:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
