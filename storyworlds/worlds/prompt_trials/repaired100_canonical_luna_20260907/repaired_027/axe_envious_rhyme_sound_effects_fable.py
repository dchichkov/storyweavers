#!/usr/bin/env python3
"""
A child-facing fable about an envious axe that learns what tools are for.

The small world tracks an axe, a woodcutter, trees, a lantern, and a shared
forest path. Physical meters and emotional memes change as envy causes trouble
and honest cooperation repairs it. The prose uses gentle rhyme and concrete
sound effects.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def __post_init__(self) -> None:
        for key in ("sharp", "secure", "blocked", "mended", "heavy"):
            self.meters.setdefault(key, 0.0)
        for key in ("envy", "pride", "worry", "shame", "patience", "trust", "relief"):
            self.memes.setdefault(key, 0.0)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    axe_name: str = "Brisk"
    woodcutter: str = "Mara"
    forest: str = "Whispering Wood"
    task: str = "clear the path for the village"
    rhyme: bool = True
    sound_effects: bool = True
    style: str = "fable"


AXE_NAMES = ["Brisk", "Chop-Chop", "Rededge", "Little Bite", "Tock"]
WOODCUTTERS = ["Mara", "Tomas", "Nell", "Oren", "Pia"]
FORESTS = ["Whispering Wood", "Mossy Grove", "Brightleaf Forest", "Thistle Vale"]
TASKS = [
    "clear the path for the village",
    "gather dry wood for the winter hearth",
    "open a safe trail to the river",
    "free a young pine from fallen branches",
]

@dataclass(frozen=True)
class Arc:
    warning: str
    envy_trigger: str
    consequence: str
    clue: str
    repair: str
    result: str
    lesson: str
    ending: str


ARCS = [
    Arc(
        warning="A good tool helps the work that needs it, not the work that earns the loudest praise",
        envy_trigger="The axe watched a silver saw shine beside the woodpile and wished every eye would admire its own blade",
        consequence="It bit into a living sapling merely to make a grander cut, and the little tree bent toward the mud",
        clue="a robin fluttered around the sapling's torn green crown",
        repair="laid its pride aside while Mara tied the sapling gently to a straight stick",
        result="the young tree stood safely until its roots could hold it again",
        lesson="Envy makes another tool's gift look like a rival's insult, but every useful gift has its proper work",
        ending="By sunset, the saw sang softly and the axe rested near the healed sapling, proud to be useful rather than praised",
    ),
    Arc(
        warning="A sharp edge is for splitting fallen wood, never for chasing another tool's glory",
        envy_trigger="The axe heard a bright new saw sing through a log and grew envious of its smooth music",
        consequence="It swung too quickly at a crooked branch, sending chips across the path and hiding a small fox den",
        clue="two frightened eyes blinked beneath the scattered chips",
        repair="stopped its boasting while Tomas brushed the chips away and marked the den with yellow leaves",
        result="the fox family found quiet shelter, and the path was cleared without another wild swing",
        lesson="A tool that envies a neighbor forgets to notice the living things around its work",
        ending="The foxes peeked from their den as the axe and saw rested together beneath one calm tree",
    ),
    Arc(
        warning="Do not cut what should be guided, and do not envy what can teach you",
        envy_trigger="The axe envied a gentle pruning knife and tried to prove that a heavy blade could do every job",
        consequence="It hacked a young apple branch instead of trimming it, and green fruit tumbled into the grass",
        clue="one unripe apple rolled beside a sign scratched with the orchard keeper's name",
        repair="accepted the knife's careful example while Nell bound the branch and gathered the fallen fruit",
        result="the wounded branch held firm and the orchard still promised fruit for autumn",
        lesson="Strength is not wisdom by itself; good work begins when a tool respects the task",
        ending="The small apples rested in a basket while the axe stood quietly beside the patient knife",
    ),
    Arc(
        warning="A shared path belongs to every paw and foot, so make room for every helper",
        envy_trigger="The axe envied a broad shovel that cleared leaves in great golden waves",
        consequence="It shoved a fallen trunk toward the path without checking, and the trunk blocked the bridge",
        clue="a child's red mitten lay on the far side where the morning walkers could not reach it",
        repair="asked the shovel to guide the trunk while Mara rolled it with a rope",
        result="the bridge opened again, and the lost mitten returned to its waiting hand",
        lesson="Envy builds a wall when cooperation could build a road",
        ending="The child waved from the bridge, and the axe heard a friendly tap from the shovel",
    ),
    Arc(
        warning="A tool grows valuable by doing its own work well, not by copying another tool",
        envy_trigger="The axe watched a hammer ring bright nails into a shelter and wished to make the same proud music",
        consequence="It struck a plank sideways, splitting the board that the shelter needed for its roof",
        clue="rain clouds gathered above the unfinished rafters",
        repair="admitted the mistake while Oren measured a sound board and the hammer fixed it in place",
        result="the roof closed before the rain, and the shelter stayed warm and dry",
        lesson="The best tool is not the one that does every job, but the one that does its own job faithfully",
        ending="Rain drummed on the finished roof while the axe guarded a neat stack of dry logs",
    ),
    Arc(
        warning="When a friend succeeds, listen for a lesson instead of a threat",
        envy_trigger="The axe grew envious when an old hatchet freed a tangled root with one patient tap",
        consequence="It attacked the root in haste and loosened stones beside the creek",
        clue="the creek water began to swirl brown around a nest of tiny eggs",
        repair="copied the hatchet's slow rhythm while Pia placed stones back along the bank",
        result="the water ran clear again and the eggs stayed safely tucked in their gravel bed",
        lesson="Another tool's success can be a lesson to borrow, not a light to snuff out",
        ending="The creek whispered clear notes, and the two blades shared the quiet shade",
    ),
]

OPENINGS = [
    "In a green forest where every branch had a story, a little axe lived in a woodcutter's shed.",
    "At the edge of a friendly forest, an axe rested beside ropes, saws, and a bright red wheelbarrow.",
    "Each morning, tools woke to the sounds of the forest: drip, rustle, chirp, and the patient call of work.",
    "Near a village path stood a shed where every tool had a task, though one axe wanted every task to be its own.",
]

RHYME_LINES = [
    "A boast may gleam, a boast may glow, but careful hands make good work grow.",
    "Chip by chip and choice by choice, kindness gives the tools a voice.",
    "Do not race for cheers or fame; steady work earns a brighter name.",
    "A neighbor's shine need not grow dim; shared success can welcome him.",
    "Slow is wise when harm is near; honest words make pathways clear.",
]

DIALOGUES = [
    "\"I wanted everyone to notice me,\" said {axe}. \"Can you show me what this work needs?\"",
    "{woodcutter} asked, \"Are you angry at the other tool, or worried you have no gift?\" \"Both,\" said {axe}, \"but I can choose better.\"",
    "\"Stop!\" cried {axe}. \"I made the danger. Tell me how to help.\" \"First, look closely,\" said {woodcutter}.",
    "\"The saw is not stealing your work,\" said {woodcutter}. \"Then I will stop competing and start listening,\" answered {axe}.",
]


def make_world(params: StoryParams) -> World:
    world = World()
    axe = world.add(Entity("axe", "tool", "axe", params.axe_name, owner="woodcutter"))
    woodcutter = world.add(Entity("woodcutter", "character", "woodcutter", params.woodcutter))
    saw = world.add(Entity("saw", "tool", "saw", "the silver saw", owner="woodcutter"))
    forest = world.add(Entity("forest", "place", "forest", params.forest))
    path = world.add(Entity("path", "place", "path", "the village path"))
    axe.meters["sharp"] = 1.0
    axe.memes["envy"] = 1.0
    axe.memes["pride"] = 1.0
    woodcutter.memes["trust"] = 1.0
    saw.memes["patience"] = 1.0
    forest.meters["secure"] = 1.0
    path.meters["blocked"] = 0.0
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    axe = world.get("axe")
    woodcutter = world.get("woodcutter")
    saw = world.get("saw")
    forest = world.get("forest")

    value = params.seed
    if value is None:
        value = sum(ord(ch) for ch in "|".join((params.axe_name, params.woodcutter, params.forest, params.task)))
    arc = ARCS[value % len(ARCS)]
    opening = OPENINGS[(value // len(ARCS)) % len(OPENINGS)]
    rhyme = RHYME_LINES[(value // 3) % len(RHYME_LINES)]
    dialogue = DIALOGUES[(value // 5) % len(DIALOGUES)].format(
        axe=axe.label, woodcutter=woodcutter.label
    )

    world.say(
        f"In {forest.label}, {woodcutter.label} kept {axe.label}, an axe, in a small shed beside {saw.label}."
    )
    world.say(opening)
    world.say(f"The day's task was to {params.task}, so every tool had a part to play.")
    world.para()

    world.say(f"{woodcutter.label} warned, \"{arc.warning}.\"")
    world.say(arc.envy_trigger)
    axe.memes["envy"] += 1.0
    axe.memes["pride"] += 1.0
    world.say(f"{axe.label} wanted to outshine {saw.label}, though {saw.label} had never asked for a contest.")

    axe.meters["sharp"] = 1.0
    axe.meters["secure"] = 0.0
    axe.meters["blocked"] = 1.0
    world.say(f"Whack! {arc.consequence}.")
    woodcutter.memes["worry"] += 1.0
    forest.meters["secure"] = 0.0
    world.para()

    world.say(f"Then {axe.label} noticed that {arc.clue}.")
    world.say(dialogue)
    world.say(rhyme)
    axe.memes["worry"] += 1.0
    axe.memes["shame"] += 1.0

    world.say(
        f"The axe chose to stop competing with {saw.label} and help with the work that truly mattered."
    )
    axe.memes["patience"] += 2.0
    axe.memes["trust"] += 1.0
    axe.memes["envy"] = max(0.0, axe.memes["envy"] - 1.0)
    axe.memes["shame"] = max(0.0, axe.memes["shame"] - 1.0)
    axe.meters["blocked"] = 0.0
    axe.meters["mended"] = 1.0
    forest.meters["secure"] = 1.0
    world.say(f"Together, {arc.repair}.")
    world.say(f"Tap, tap; swish, swish. {arc.result}.")
    woodcutter.memes["relief"] += 1.0
    axe.memes["relief"] += 1.0
    world.para()

    world.say(f"{woodcutter.label} smiled, but praised the axe for its change of heart, not for making the biggest noise.")
    world.say(f"The axe learned this lesson: {arc.lesson}.")
    world.say(arc.ending)

    world.facts.update(
        axe=axe,
        woodcutter=woodcutter,
        saw=saw,
        forest=forest,
        params=params,
        arc=arc,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    axe: Entity = world.facts["axe"]
    woodcutter: Entity = world.facts["woodcutter"]
    saw: Entity = world.facts["saw"]
    params: StoryParams = world.facts["params"]
    arc: Arc = world.facts["arc"]
    return [
        QAItem(
            f"Who is the fable mainly about in {params.forest}?",
            f"It is about {axe.label}, an axe owned by {woodcutter.label}. The axe becomes envious of {saw.label}, causes trouble, and learns to work cooperatively.",
        ),
        QAItem(
            f"Why did {axe.label} become envious?",
            f"{axe.label} wanted the praise given to another tool. The axe began treating {saw.label}'s useful gift as if it were a contest.",
        ),
        QAItem(
            f"What trouble did {axe.label}'s envy cause?",
            f"{arc.consequence}. The axe acted too quickly because it wanted to outshine another tool.",
        ),
        QAItem(
            f"What clue helped {axe.label} understand the danger?",
            f"{axe.label} noticed that {arc.clue}. That clue showed that the axe's proud action was hurting something that needed care.",
        ),
        QAItem(
            f"How did {axe.label} repair the mistake?",
            f"The axe {arc.repair}. By listening and cooperating, the axe helped ensure that {arc.result}.",
        ),
        QAItem(
            f"What lesson did the envious axe learn?",
            f"{arc.lesson} The axe learned that being useful matters more than receiving the loudest praise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an axe?",
            "An axe is a tool with a handle and a strong blade, commonly used to split or cut wood safely when handled by a careful person.",
        ),
        QAItem(
            "What does envious mean?",
            "Envious means wishing you had another person's praise, skill, or possession instead of appreciating your own gifts.",
        ),
        QAItem(
            "Why should tools be used for the right job?",
            "Using a tool for the right job makes work safer and more effective, while using the wrong tool can damage things or hurt someone.",
        ),
        QAItem(
            "What is a fable?",
            "A fable is a short story that often gives animals or objects human qualities and ends with a clear lesson.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    axe: Entity = world.facts["axe"]
    arc: Arc = world.facts["arc"]
    return [
        f"Write a child-friendly fable in rhyme about {axe.label}, an envious axe in {params.forest}.",
        f"Tell a fable where an axe envies another tool, causes a danger, and repairs it through cooperation.",
        f"Use sound effects such as 'Whack!' and 'Tap, tap; swish, swish' to show how the axe learns its lesson.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:10} ({entity.type:11}) meters={meters} memes={memes}"
        )
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
% The axe becomes troublesome when envy leads it away from its proper work.
envy(axe).
wrong_job(axe).
trouble(axe) :- envy(axe), wrong_job(axe).

% Listening and cooperation create a repaired ending.
listens(axe).
cooperates(axe).
resolved(axe) :- listens(axe), cooperates(axe), trouble(axe).

#show trouble/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("envy", "axe"),
            asp.fact("wrong_job", "axe"),
            asp.fact("listens", "axe"),
            asp.fact("cooperates", "axe"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program())
    actual = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in symbols}
    expected = {"trouble/1", "resolved/1"}
    if actual == expected:
        print("OK: ASP twin matches the axe fable logic.")
        return 0
    print("MISMATCH:", sorted(actual), "expected", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming fable about an envious axe."
    )
    parser.add_argument("--axe-name", choices=AXE_NAMES)
    parser.add_argument("--woodcutter", choices=WOODCUTTERS)
    parser.add_argument("--forest", choices=FORESTS)
    parser.add_argument("--task", choices=TASKS)
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
        seed=args.seed,
        axe_name=args.axe_name or rng.choice(AXE_NAMES),
        woodcutter=args.woodcutter or rng.choice(WOODCUTTERS),
        forest=args.forest or rng.choice(FORESTS),
        task=args.task or rng.choice(TASKS),
    )


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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        axe_name="Brisk",
        woodcutter="Mara",
        forest="Whispering Wood",
        task="clear the path for the village",
    ),
    StoryParams(
        axe_name="Tock",
        woodcutter="Nell",
        forest="Mossy Grove",
        task="open a safe trail to the river",
    ),
    StoryParams(
        axe_name="Little Bite",
        woodcutter="Oren",
        forest="Brightleaf Forest",
        task="gather dry wood for the winter hearth",
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
        import asp
        model = asp.one_model(asp_program())
        print(" ".join(str(symbol) for symbol in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated from the requested options.")

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
