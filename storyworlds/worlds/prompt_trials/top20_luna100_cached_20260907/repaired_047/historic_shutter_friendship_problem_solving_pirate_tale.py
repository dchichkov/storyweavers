#!/usr/bin/env python3
"""
A standalone pirate-tale storyworld about a historic shutter, friendship,
and problem solving.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
setting(harbor).
has_friendship(harbor).
has_problem_solving(harbor).
historic_shutter(harbor).
good_pirate_turn(S) :- setting(S), has_friendship(S), has_problem_solving(S),
                        historic_shutter(S), solved(S).
useful_tool(T) :- tool(T), careful(T).
"""


PLACE = "the old harbor fort"


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
    captain: str
    mate: str
    tool: str
    treasure: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    trouble: str
    failed_try: str
    clue: str
    mate_line: str
    repair: str
    result: str
    lesson: str
    ending: str


@dataclass
class World:
    place: str = PLACE
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

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
        for entity in self.entities.values():
            details = []
            if entity.meters:
                details.append(f"meters={dict(entity.meters)}")
            if entity.memes:
                details.append(f"memes={dict(entity.memes)}")
            if entity.label:
                details.append(f"label={entity.label!r}")
            lines.append(
                f"  {entity.id:10} ({entity.kind:10}) {' '.join(details)}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


SCENARIOS = [
    Scenario(
        key="stuck_shutter",
        opening="Captain Mara and her first mate Finn were checking the fort before the tide turned.",
        trouble="The historic wooden shutter above the old map room had jammed halfway open, leaving the room exposed to rain.",
        failed_try="pulling together only made the iron hinge groan and shook dust from the stone wall",
        clue="a thin line of salt showed that the lower hinge was resting on a swollen plank",
        mate_line='"The shutter is not stubborn," Finn said. "It is leaning on the wrong place."',
        repair="wedged the plank clear, rubbed the hinge with oil, and lifted the shutter one careful inch at a time",
        result="The shutter swung closed against the rain without cracking its old boards.",
        lesson="good friends listen to the problem before pushing harder",
        ending="the historic shutter guarded the map room while two friends watched the sunset from the dry doorway",
    ),
    Scenario(
        key="missing_latch",
        opening="At dawn, Captain Mara and Finn sailed their small boat to the fort to inspect its ancient rooms.",
        trouble="The historic shutter kept flapping in the sea wind because its brass latch had slipped behind a crate.",
        failed_try="tying it with a rope left a gap wide enough for gulls and rain",
        clue="small scratches on the floor pointed from the shutter to the crate",
        mate_line='"The floor remembers where the latch traveled," Finn said.',
        repair="moved the crate, found the brass latch, and fastened it with a short leather strap",
        result="The shutter held firm while the wind whistled harmlessly outside.",
        lesson="a patient search can beat a hurried guess",
        ending="the old brass latch gleamed on the shutter as the friends shared a warm biscuit",
    ),
    Scenario(
        key="stormy_panes",
        opening="Before a squall reached the harbor, Captain Mara and Finn climbed the fort stairs together.",
        trouble="A cracked pane in the historic shutter rattled above a chest of sea charts.",
        failed_try="stuffing cloth into the crack made the pane press harder against the frame",
        clue="the rattle stopped whenever the shutter was held level",
        mate_line='"Let us support the shutter first," Finn said. "Then the glass can rest."',
        repair="set a wooden brace beneath the shutter, tied the loose pane softly, and moved the charts away",
        result="The charts stayed dry, and the pane stopped rattling before the storm arrived.",
        lesson="solving the cause protects more than hiding the noise",
        ending="rain drummed on the braced shutter while the rescued charts lay safe beneath a lantern",
    ),
    Scenario(
        key="hidden_mark",
        opening="Captain Mara brought Finn to the fort to read a faded mark carved beside the oldest shutter.",
        trouble="The shutter would not open, and the mark seemed to point into a dark corner.",
        failed_try="searching the floor by moonlight found only pebbles and a broken spoon",
        clue="the carving showed a small arrow aimed at the shutter's bottom rail",
        mate_line='"The clue is pointing low, not far away," Finn said.',
        repair="cleared sand from the bottom rail and lifted a hidden wooden peg from its socket",
        result="The shutter opened to reveal a narrow lookout and a safe place for the treasure map.",
        lesson="friends solve mysteries best when each person notices a different detail",
        ending="the treasure map rested in the lookout as the historic shutter opened toward a bright sea",
    ),
    Scenario(
        key="stubborn_wind",
        opening="The harbor bell rang as Captain Mara and Finn prepared the fort for a night of strong wind.",
        trouble="The historic shutter banged against the wall and frightened the young deckhands below.",
        failed_try="holding it with one rope caused the rope to scrape across the old paint",
        clue="two empty rings on the stone wall showed that the shutter once used a pair of ties",
        mate_line='"One rope is doing two jobs," Finn said. "Friends can share the work too."',
        repair="found a second rope, tied both rings evenly, and padded the shutter's edge with sailcloth",
        result="The shutter stayed still, and the deckhands could sleep through the night.",
        lesson="balanced work makes a hard job gentler",
        ending="the sailcloth rested softly against the historic shutter as the harbor lights twinkled below",
    ),
    Scenario(
        key="stuck_by_ivy",
        opening="After a long voyage, Captain Mara and Finn returned to the fort with a chest of rescued books.",
        trouble="Ivy had curled through the historic shutter and blocked the way to the dry storeroom.",
        failed_try="yanking the vines tore leaves but left their tough roots gripping the frame",
        clue="the ivy was thickest where an old drain spilled water beside the wall",
        mate_line='"If we clear the water first, the ivy will loosen," Finn said.',
        repair="opened the clogged drain, clipped the loose vines, and lifted the shutter from the roots",
        result="The storeroom opened, and every rescued book stayed safe from the next rain.",
        lesson="careful friends fix the source instead of fighting only the symptom",
        ending="green leaves curled beside the historic shutter while the rescued books dried in the sun",
    ),
]


NAMES = ["Mara", "Rosa", "Talia", "Nell", "Sora", "Pip", "Jo", "Lena"]
MATES = ["Finn", "Toby", "Milo", "Kit", "Bea", "Owen", "Nico", "Pearl"]
TOOLS = ["rope", "lantern", "wooden brace", "oil flask", "sailcloth"]
TREASURES = ["a brass compass", "a rolled sea map", "a silver key", "a captain's log"]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.captain.strip():
        raise StoryError("The pirate captain needs a name.")
    if not params.mate.strip():
        raise StoryError("The captain needs a named friend aboard the tale.")
    if params.tool not in TOOLS:
        raise StoryError("The tool must be a safe, useful object for an old harbor fort.")
    if params.treasure not in TREASURES:
        raise StoryError("The treasure must be a small story-friendly nautical object.")
    if params.captain.strip().lower() == params.mate.strip().lower():
        raise StoryError("The captain and mate need different names so their friendship is clear.")


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("setting", "harbor"),
        asp.fact("has_friendship", "harbor"),
        asp.fact("has_problem_solving", "harbor"),
        asp.fact("historic_shutter", "harbor"),
        asp.fact("solved", "harbor"),
    ]
    for tool in TOOLS:
        facts.append(asp.fact("tool", tool.replace(" ", "_")))
        facts.append(asp.fact("careful", tool.replace(" ", "_")))
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_tool_choices() -> list[str]:
    return list(TOOLS)


def valid_treasure_choices() -> list[str]:
    return list(TREASURES)


def valid_params(rng: random.Random) -> StoryParams:
    captain = rng.choice(NAMES)
    mate = rng.choice([name for name in MATES if name.lower() != captain.lower()])
    return StoryParams(
        captain=captain,
        mate=mate,
        tool=rng.choice(TOOLS),
        treasure=rng.choice(TREASURES),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Historic shutter pirate friendship storyworld."
    )
    parser.add_argument("--captain")
    parser.add_argument("--mate")
    parser.add_argument("--tool", choices=valid_tool_choices())
    parser.add_argument("--treasure", choices=valid_treasure_choices())
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = valid_params(rng)
    if args.captain:
        params.captain = args.captain
    if args.mate:
        params.mate = args.mate
    if args.tool:
        params.tool = args.tool
    if args.treasure:
        params.treasure = args.treasure
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    captain = world.add(
        Entity(id="captain", kind="character", label=params.captain)
    )
    mate = world.add(Entity(id="mate", kind="character", label=params.mate))
    tool = world.add(Entity(id="tool", kind="tool", label=params.tool))
    treasure = world.add(
        Entity(id="treasure", kind="treasure", label=params.treasure)
    )
    shutter = world.add(
        Entity(id="shutter", kind="historic object", label="historic shutter")
    )
    world.facts.update(
        captain=captain,
        mate=mate,
        tool=tool,
        treasure=treasure,
        shutter=shutter,
        place=PLACE,
        friendship=True,
        problem_solving=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)

    captain = world.get("captain")
    mate = world.get("mate")
    tool = world.get("tool")
    treasure = world.get("treasure")
    shutter = world.get("shutter")

    captain.bump_meme("friendship")
    mate.bump_meme("trust")
    shutter.bump_meter("age", 100)
    treasure.bump_meme("importance")

    world.say(scenario.opening)
    world.say(
        f"{captain.label} carried {treasure.label}, while {mate.label} carried the "
        f"{tool.label}. They trusted each other as they crossed the stones."
    )
    world.para()

    world.say(scenario.trouble)
    world.say(
        f"At first, {captain.label} tried to hurry, but {scenario.failed_try}."
    )
    world.say(
        f'{captain.label} lowered the treasure and said, "Let us think before we tug again."'
    )
    world.say(scenario.mate_line)
    world.para()

    mate.bump_meme("cleverness")
    captain.bump_meme("patience")
    world.say(f"Together they studied the shutter. {scenario.clue}.")
    world.say(
        f"They made a plan: {captain.label} would guide the {tool.label}, while "
        f"{mate.label} watched the hinge and called out each safe movement."
    )
    world.para()

    tool.bump_meter("use", 1)
    shutter.bump_meter("care", 1)
    world.say(
        f"Working as a team, {captain.label} used the {tool.label} carefully, and "
        f"{mate.label} {scenario.repair}."
    )
    world.say(scenario.result)
    world.para()

    captain.bump_meme("joy")
    mate.bump_meme("joy")
    world.say(
        f"{mate.label} grinned. 'We found the answer because we listened to one another,' "
        f"{mate.label} said."
    )
    world.say(
        f"{captain.label} nodded and replied, 'A clever crew is stronger than a strong rope.'"
    )
    world.say(f"They learned that {scenario.lesson}.")
    world.say(
        f"With the {treasure.label} safe and the fort ready for the night, "
        f"{scenario.ending}."
    )

    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        failed_try=scenario.failed_try,
        clue=scenario.clue,
        repair=scenario.repair,
        result=scenario.result,
        lesson=scenario.lesson,
        ending_image=scenario.ending,
        tool_action=f"used the {tool.label} carefully",
        resolved=True,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    captain = facts["captain"].label
    mate = facts["mate"].label
    tool = facts["tool"].label
    scenario = str(facts["scenario"]).replace("_", " ")
    return [
        f"Write a pirate tale in which {captain} and {mate} solve a problem together.",
        "Tell a child-friendly story using the words historic and shutter, with friendship and problem solving.",
        f"Write a harbor adventure about a {scenario} problem and a careful repair using a {tool}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    captain = facts["captain"].label
    mate = facts["mate"].label
    tool = facts["tool"].label
    treasure = facts["treasure"].label
    return [
        QAItem(
            question="What problem did the friends face at the old harbor fort?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question=f"What clue did {captain} and {mate} notice?",
            answer=f"They noticed that {facts['clue']}.",
        ),
        QAItem(
            question=f"How did the {tool} help solve the problem?",
            answer=f"{captain} used the {tool} carefully while {mate} helped them carry out the repair: {facts['repair']}.",
        ),
        QAItem(
            question="What changed after the friends worked together?",
            answer=str(facts["result"]),
        ),
        QAItem(
            question=f"What showed that the pirate tale ended happily for {captain} and {mate}?",
            answer=f"The {treasure} was safe, and {facts['ending_image']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a historic object?",
            answer="A historic object is something old that helps people remember how people lived or worked long ago.",
        ),
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a wooden or metal cover that can open or close over a window or opening.",
        ),
        QAItem(
            question="How can friendship help solve a problem?",
            answer="Friendship helps because people can listen, share ideas, divide the work, and encourage one another.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong, finding useful clues, and choosing careful steps to make things better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show good_pirate_turn/1.\n#show useful_tool/1."
    )
    model = asp.one_model(program)
    actual = set()
    for symbol in model:
        if symbol.name == "good_pirate_turn":
            actual.add((symbol.name, tuple(arg.name for arg in symbol.arguments)))
        elif symbol.name == "useful_tool":
            actual.add((symbol.name, tuple(arg.name for arg in symbol.arguments)))

    expected = {("good_pirate_turn", ("harbor",))}
    expected.update(("useful_tool", (tool.replace(" ", "_"),)) for tool in TOOLS)

    if actual == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_pirate_turn/1."))
    return sorted(asp.atoms(model, "good_pirate_turn"))


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


CURATED = [
    StoryParams(
        captain="Mara",
        mate="Finn",
        tool="rope",
        treasure="a brass compass",
        seed=17,
    ),
    StoryParams(
        captain="Rosa",
        mate="Toby",
        tool="lantern",
        treasure="a rolled sea map",
        seed=31,
    ),
    StoryParams(
        captain="Talia",
        mate="Bea",
        tool="wooden brace",
        treasure="a silver key",
        seed=53,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_pirate_turn/1.\n#show useful_tool/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP-compatible historic shutter pirate stories:")
        for item in asp_list():
            print(item)
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and attempts < limit:
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

    if not samples:
        raise StoryError("No stories could be generated.")

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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
