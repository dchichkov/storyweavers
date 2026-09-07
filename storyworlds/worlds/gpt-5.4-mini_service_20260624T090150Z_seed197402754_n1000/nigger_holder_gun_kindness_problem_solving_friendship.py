#!/usr/bin/env python3
"""A varied child-safe StoryWorld about repairing useful holders together."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    friend: str
    setting: str
    scenario: str
    opening: int
    dialogue: int
    reflection: int
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {
            key: Entity(**asdict(value)) for key, value in self.entities.items()
        }
        clone.facts = dict(self.facts)
        return clone


@dataclass(frozen=True)
class Scenario:
    key: str
    holder: str
    purpose: str
    occasion: str
    problem: str
    clue: str
    plan: str
    child_action: str
    friend_action: str
    adult_action: str
    proof: str
    ending: str


SETTINGS = {
    "workshop": "the community craft workshop",
    "library": "the library makerspace",
    "classroom": "the sunny classroom",
    "porch": "the covered back porch",
    "garden": "the garden art table",
    "clubhouse": "the neighborhood clubhouse",
}
NAMES = ("Milo", "Pia", "Nora", "Eli", "Tess", "Lina", "Ari", "June")
FRIENDS = ("Finn", "Luca", "Maya", "Sage", "Remy", "Ivy", "Noah", "Clara")

SCENARIOS = (
    Scenario(
        "pencil_cup", "painted pencil holder",
        "keep colored pencils ready for a friendship mural",
        "the children were about to draw a welcome picture for a new neighbor",
        "one wooden side sprang loose, and pencils rolled under the table",
        "a clean line of old glue showed exactly where the side belonged",
        "sort the pencils, fit the side without forcing it, and ask an adult to secure the clean join",
        "fitted the loose side against the old glue line",
        "gathered every runaway pencil by color and held the empty cup steady",
        "checked the fit, used a low-temperature craft glue gun, unplugged it, and set it beyond the children's reach",
        "the repaired cup stood upright even when every bright pencil went back inside",
        "Beside the welcome mural, the pencil tips made a rainbow above the sturdy cup.",
    ),
    Scenario(
        "seed_caddy", "seed-packet holder",
        "carry flower seeds to the children's planting beds",
        "the last dry hour before rain was perfect for planting",
        "a divider leaned over and mixed tall-flower packets with tiny ground-cover seeds",
        "matching leaf pictures revealed which packets belonged in each section",
        "sort by the pictures, mark each section, and repair the divider before carrying the caddy",
        "matched every packet to its sketched leaf",
        "read the picture labels aloud and made two neat packet stacks",
        "aligned the divider, applied craft glue safely, unplugged the glue gun, and waited for the join to cool",
        "each labeled section held its own packets during a careful trip around the table",
        "After the rain, two tidy rows of labels peeked from soil while the caddy dried on its hook.",
    ),
    Scenario(
        "brush_rack", "paintbrush holder",
        "keep wet brushes from staining the tabletop",
        "the art club was making paper lanterns for family night",
        "one support foot tipped, sending three damp brushes toward clean paper",
        "a square of dry wood under the short corner made the rack level again",
        "move the paper, dry the rack, test the wooden square, and let an adult fasten it",
        "tested the square twice and marked its best position",
        "rescued the clean paper and blotted the small blue puddle",
        "secured the fitted square with the craft glue gun, unplugged the tool, and guarded the cooling repair",
        "six wet brushes rested in the rack without a drip reaching the lantern paper",
        "The lanterns glowed that evening, and six brush handles stood like flagpoles in their level rack.",
    ),
    Scenario(
        "recipe_stand", "recipe-card holder",
        "hold directions where every young cook could see them",
        "the group was preparing fruit boats for a shared snack",
        "the back brace slipped, so the recipe card kept flopping face-down",
        "a faint pencil outline showed that the brace had once been attached backward",
        "wash hands, compare the brace with the outline, turn it correctly, and request adult help",
        "turned the brace and lined it up with the pencil marks",
        "kept the fruit station organized and read each preparation step",
        "placed the brace on the outline, joined it with craft glue, unplugged the tool, and let it cool",
        "the card remained upright from peeling bananas through sharing napkins",
        "One last blueberry sailed in a fruit boat beneath the recipe card standing tall in its holder.",
    ),
    Scenario(
        "note_clip", "kindness-note holder",
        "display thank-you notes for community helpers",
        "the children had promised to deliver their notes before the mail carrier arrived",
        "a loose clip spun sideways and hid several names",
        "the clip's flat base matched a pale circle on the wooden stand",
        "put the notes in delivery order, align the clip with its mark, and have an adult reattach it",
        "aligned the clip over the pale circle",
        "found each hidden note and checked that every helper had one",
        "used a low-temperature craft glue gun on the marked base, unplugged it, and kept hands away until it cooled",
        "the clip faced forward and held every note in the chosen order",
        "The mail carrier waved as the final blue envelope left the straight, steady clip.",
    ),
    Scenario(
        "puppet_rest", "puppet holder",
        "keep handmade puppets upright between scenes",
        "a friendship play was minutes from its first rehearsal",
        "the tallest puppet made the narrow base wobble toward the curtain",
        "placing puppets from shortest to tallest balanced the weight but exposed a cracked brace",
        "set the puppets aside, widen their spacing, fit the brace, and ask the director to secure it",
        "fit the brace and planned wider spaces for the puppets",
        "invented a gentle resting order and practiced with the nervous puppeteer",
        "repaired the brace with the craft glue gun, unplugged it, and tested the empty holder first",
        "the puppets stayed upright through every scene change and were easy for both friends to reach",
        "When the curtain closed, the rabbit and moon puppets bowed from steady places in the holder.",
    ),
    Scenario(
        "bookmark_tray", "bookmark holder",
        "offer handmade bookmarks at the library desk",
        "the reading circle had welcomed three younger children",
        "a peeled corner caught the tassels and tangled the bookmarks",
        "the tassels slid freely whenever the lifted corner was pressed flat",
        "untangle without pulling, stack the bookmarks loosely, and let the librarian repair the corner",
        "pressed the empty corner flat and confirmed that nothing caught",
        "freed each tassel one loop at a time and invited the younger children to choose first",
        "fixed the corner with safe craft glue, unplugged the glue gun, and waited until the join was cool",
        "every tassel lifted cleanly while the repaired tray stayed smooth and flat",
        "Three storybooks closed on bright tassels, and the empty holder waited neatly for tomorrow.",
    ),
    Scenario(
        "badge_board", "name-badge holder",
        "help children learn one another's names at a club meeting",
        "two shy newcomers were standing quietly near the door",
        "a broken rail dropped the alphabetized badges into one confusing pile",
        "tiny letter marks along the rail still showed the intended order",
        "welcome the newcomers, sort by letter, fit the rail, and ask the club leader to mend it",
        "fit the rail into its matching notches",
        "learned both new names and sorted badges together with the newcomers",
        "attached the rail using the craft glue gun, unplugged it, and checked the cool repair",
        "every child found a badge quickly, including both newcomers",
        "At circle time, every badge faced outward and the two newest names sat between smiling friends.",
    ),
    Scenario(
        "yarn_basket", "crochet-hook holder",
        "organize blunt craft hooks for a yarn lesson",
        "the group planned soft squares for an animal shelter blanket",
        "a cracked handle tilted the holder and spilled hooks into tangled yarn",
        "the unbroken handle showed how the loose pieces should overlap",
        "pause, count the hooks, copy the sound handle's overlap, and ask an adult to make the join",
        "copied the overlap and held the pieces together while the tool was still unplugged",
        "counted every hook and rolled loose yarn into separate balls",
        "joined the handle with the low-temperature glue gun, unplugged it, and kept the holder still while it cooled",
        "the repaired handle carried all the counted hooks without bending",
        "A soft green square joined the shelter blanket while the hooks rested in their mended holder.",
    ),
    Scenario(
        "plant_label", "plant-label holder",
        "show visitors which herbs grew in a shared garden box",
        "a grandparent was coming to taste the children's mint tea",
        "the frame split at one corner, leaving mint and basil labels crossed",
        "gently smelling a leaf identified the mint without guessing",
        "identify both plants, correct the labels, fit the dry corner, and ask the garden leader to repair it",
        "fit the frame corner and corrected both plant labels",
        "compared the leaves carefully and moved each label to the right row",
        "secured the corner with the craft glue gun, unplugged it, and kept everyone clear while it cooled",
        "the labels stayed straight when a breeze moved through the garden box",
        "Mint leaves bobbed beneath the correct label as two friends carried a fragrant cup to their guest.",
    ),
    Scenario(
        "card_rack", "greeting-card holder",
        "display cheerful cards at a neighborhood swap table",
        "the children were collecting messages for a friend with a broken ankle",
        "one slat came loose and folded the tallest card across its painted sun",
        "a scrap card showed that only the middle gap was too tight",
        "remove the cards, space the slat correctly, and let an adult secure it before rebuilding the display",
        "measured the middle gap with the scrap card",
        "smoothed the folded card beneath a book and arranged the others by height",
        "reset the slat with craft glue, unplugged the glue gun, and waited for a safe, cool join",
        "the painted-sun card slid in and out easily without bending",
        "The bright sun card stood highest in the repaired rack when their friend opened the door.",
    ),
    Scenario(
        "tool_outline", "small-tool holder",
        "store rulers, tape, and child-safe scissors after craft time",
        "cleanup had to finish before a music lesson",
        "a divider popped free, letting the tape roll hide beneath the rulers",
        "outline pictures on the base showed a separate home for each tool",
        "match tools to outlines, fit the divider in its groove, and ask the supervising adult to fasten it",
        "seated the divider in its groove and matched tools to outlines",
        "returned each tool to its pictured place and found the missing tape roll",
        "secured the divider with the craft glue gun, unplugged it, and stored the cooled tool in a locked adult cabinet",
        "a gentle shake left every ruler, tape roll, and pair of scissors in its own section",
        "The first music note rang beside a clear table and a neatly filled holder.",
    ),
)
SCENARIO_BY_KEY = {scenario.key: scenario for scenario in SCENARIOS}

OPENINGS = (
    "At {setting}, {name} and {friend} shared a job that mattered.",
    "Sunlight crossed {setting} when {name} invited {friend} to help.",
    "A busy morning began at {setting}, where {name} and {friend} worked side by side.",
    "At {setting}, a small promise brought {name} and {friend} to the same table.",
    "Before the room filled with voices, {name} met {friend} at {setting}.",
    "One careful project waited for {name} and {friend} at {setting}.",
    "At {setting}, {name} prepared a kind surprise, and {friend} came early to assist.",
    "The day felt full of possibility when {name} and {friend} arrived at {setting}.",
)
DIALOGUES = (
    '"Let us notice what happened before we choose a fix," {friend} said.',
    '"We can go slowly and solve the real problem," {friend} said.',
    '"Helping means listening, checking, and making a safe plan," {friend} said.',
    '"Your project matters to me, so we will work it out together," {friend} said.',
    '"First the clue, then the plan, then a careful test," {friend} said.',
    '"A mistake is easier to mend when friends tell the truth," {friend} said.',
    '"We do not have to hurry past the problem," {friend} said.',
    '"Let us protect the project and each other," {friend} said.',
)
REFLECTIONS = (
    "Kindness had not hidden the problem; it had made room to understand it.",
    "Their friendship grew because each person contributed something useful.",
    "A careful test turned a hopeful idea into a dependable solution.",
    "Solving the cause, instead of covering the mess, made their work last.",
    "Asking a trusted adult for the right help was part of their good plan.",
    "Patient hands and honest words belonged in the same toolbox.",
    "The repair mattered, but noticing each other's ideas mattered too.",
    "Working safely left them proud of both the project and their partnership.",
)

ASP_RULES = r"""
needs_kindness :- kind_act.
needs_problem_solving :- observed_clue, tested_repair.
friendship_grows :- shared_fix.
safe_tool_use :- trusted_adult, unplugged_tool.
"""


def asp_facts() -> str:
    import asp

    return "\n".join((
        asp.fact("kind_act"),
        asp.fact("observed_clue"),
        asp.fact("tested_repair"),
        asp.fact("shared_fix"),
        asp.fact("trusted_adult"),
        asp.fact("unplugged_tool"),
        asp.fact("tool", "low_temperature_craft_glue_gun"),
    ))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-safe story about kindness, problem solving, and friendship."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, seed: int) -> StoryParams:
    rng = random.Random(seed ^ 0x5A17C0DE)
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    if name == friend:
        choices = [candidate for candidate in FRIENDS if candidate != name]
        friend = choices[seed % len(choices)]
    variant = seed & 0x7FFFFFFF
    scenario = SCENARIOS[variant % len(SCENARIOS)]
    variant //= len(SCENARIOS)
    opening = variant % len(OPENINGS)
    variant //= len(OPENINGS)
    dialogue = variant % len(DIALOGUES)
    variant //= len(DIALOGUES)
    reflection = variant % len(REFLECTIONS)
    setting = args.setting or tuple(SETTINGS)[(seed // 7) % len(SETTINGS)]
    return StoryParams(
        name=name, friend=friend, setting=setting, scenario=scenario.key,
        opening=opening, dialogue=dialogue, reflection=reflection, seed=seed,
    )


def make_world(params: StoryParams) -> World:
    scenario = SCENARIO_BY_KEY[params.scenario]
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(
        id="child", kind="character", label=params.name,
        traits=["kind", "observant"],
        memes={"kindness": 0.0, "problem_solving": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id="friend", kind="character", label=params.friend,
        traits=["patient", "helpful"],
        memes={"kindness": 0.0, "problem_solving": 0.0, "friendship": 0.0},
    ))
    holder = world.add(Entity(
        id="holder", kind="thing", label=scenario.holder,
        phrase=f"a {scenario.holder} used to {scenario.purpose}", owner=child.id,
        meters={"damaged": 1.0, "repaired": 0.0, "tested": 0.0},
    ))
    tool = world.add(Entity(
        id="craft_tool", kind="tool", label="low-temperature craft glue gun",
        phrase="an adult-operated low-temperature craft glue gun",
        held_by="trusted_adult",
        meters={"plugged_in": 0.0, "cool": 1.0, "child_access": 0.0},
    ))
    world.facts.update(
        child=child, friend=friend, holder=holder, craft_tool=tool,
        scenario=scenario, trusted_adult=True, tool_used_by="trusted adult",
    )
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    scenario: Scenario = world.facts["scenario"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    holder: Entity = world.facts["holder"]  # type: ignore[assignment]
    tool: Entity = world.facts["craft_tool"]  # type: ignore[assignment]

    world.say(OPENINGS[params.opening].format(
        setting=world.setting, name=child.label, friend=friend.label
    ))
    world.say(
        f"Their {holder.label} was meant to {scenario.purpose}, because {scenario.occasion}."
    )
    world.para()
    world.say(f"But {scenario.problem}.")
    world.say(
        f"Instead of hiding the trouble, {child.label} looked closely. "
        f"{scenario.clue.capitalize()}."
    )
    world.say(DIALOGUES[params.dialogue].format(friend=friend.label))
    child.memes["kindness"] = 1.0
    friend.memes["kindness"] = 1.0
    world.para()
    world.say(f"Together they chose a plan: {scenario.plan}.")
    world.say(f"{child.label} {scenario.child_action}, while {friend.label} {scenario.friend_action}.")
    world.say(f"Then a trusted adult {scenario.adult_action}.")
    world.say(
        f"Only the adult handled the {tool.label}; the children watched from a safe "
        "distance and waited for the repair to cool."
    )
    child.memes["problem_solving"] = 1.0
    friend.memes["problem_solving"] = 1.0
    holder.meters.update(damaged=0.0, repaired=1.0, tested=1.0)
    world.para()
    world.say(f"They tested their solution: {scenario.proof}.")
    world.say(REFLECTIONS[params.reflection])
    world.say(scenario.ending)
    child.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    world.facts.update(
        problem=scenario.problem, clue=scenario.clue, plan=scenario.plan,
        child_action=scenario.child_action, friend_action=scenario.friend_action,
        adult_action=scenario.adult_action, proof=scenario.proof,
        ending=scenario.ending, repair_cooled=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    holder: Entity = world.facts["holder"]  # type: ignore[assignment]
    return [
        "Write a complete story for a young child about kindness, practical problem solving, and friendship.",
        f"Tell how {child.label} and {friend.label} notice evidence, make a safe plan, and repair a {holder.label} with help from a trusted adult.",
        "If a low-temperature craft glue gun is needed, make clear that only the adult handles it, unplugs it, and keeps children away until the repair cools.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    holder: Entity = world.facts["holder"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What went wrong with the {holder.label}?",
            answer=f"{str(world.facts['problem']).capitalize()}. {child.label} did not hide the trouble and looked for a clue.",
        ),
        QAItem(
            question=f"What clue helped {child.label} and {friend.label} choose their plan?",
            answer=f"They noticed that {world.facts['clue']}. That evidence helped them address the cause.",
        ),
        QAItem(
            question="How did the friends solve the problem safely?",
            answer=f"They decided to {world.facts['plan']}. A trusted adult handled and unplugged the craft glue gun while the children stayed back until the repair cooled.",
        ),
        QAItem(
            question=f"How did the friends know the {holder.label} was truly repaired?",
            answer=f"They tested it and saw that {world.facts['proof']}. The test showed that their solution worked.",
        ),
        QAItem(
            question="What final image showed that their work had helped?",
            answer=str(world.facts["ending"]),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    holder: Entity = world.facts["holder"]  # type: ignore[assignment]
    scenario: Scenario = world.facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Why is noticing a clue useful when solving a problem?",
            answer="A clue can reveal what caused the problem. Understanding the cause helps people choose a repair that will last.",
        ),
        QAItem(
            question="Who should handle a low-temperature craft glue gun in this storyworld?",
            answer="Only a trusted adult should handle it. The adult also unplugs it and keeps children away until the glue and tool are cool.",
        ),
        QAItem(
            question=f"What is a {holder.label} used for in this storyworld?",
            answer=f"It is used to {scenario.purpose}. Its purpose is why repairing it carefully matters.",
        ),
        QAItem(
            question="How can teamwork strengthen friendship?",
            answer="Friends can listen to each other's ideas and share useful tasks. Solving a real problem together builds trust.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params, story=world.render(), prompts=generation_prompts(world),
        story_qa=story_qa(world), world_qa=world_qa(world), world=world,
    )


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        parts.append(f"{index}. {prompt}")
    parts.extend(("", "== (2) Story questions =="))
    for item in sample.story_qa:
        parts.extend((f"Q: {item.question}", f"A: {item.answer}"))
    parts.extend(("", "== (3) World-knowledge questions =="))
    for item in sample.world_qa:
        parts.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        details = []
        if entity.traits:
            details.append(f"traits={entity.traits}")
        if entity.owner:
            details.append(f"owner={entity.owner}")
        if entity.held_by:
            details.append(f"held_by={entity.held_by}")
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id}: {entity.kind} {entity.label} {' '.join(details)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        name=NAMES[index % len(NAMES)],
        friend=FRIENDS[(index + 2) % len(FRIENDS)],
        setting=tuple(SETTINGS)[index % len(SETTINGS)],
        scenario=scenario.key,
        opening=index % len(OPENINGS),
        dialogue=(index * 3) % len(DIALOGUES),
        reflection=(index * 5) % len(REFLECTIONS),
        seed=index,
    )
    for index, scenario in enumerate(SCENARIOS)
]


def verify() -> int:
    import asp

    show = "\n".join((
        "#show needs_kindness/0.",
        "#show needs_problem_solving/0.",
        "#show friendship_grows/0.",
        "#show safe_tool_use/0.",
    ))
    model = asp.one_model(asp_program(show))
    shown = {symbol.name for symbol in model}
    expected = {
        "needs_kindness", "needs_problem_solving", "friendship_grows", "safe_tool_use"
    }
    if shown == expected:
        print("OK: ASP twin matches the safe repair and friendship story spine.")
        return 0
    print("Mismatch between ASP and Python gates.")
    print("ASP:", sorted(shown))
    print("PY :", sorted(expected))
    return 1


def emit(
    sample: StorySample,
    *, trace: bool = False,
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


def main() -> None:
    args = build_parser().parse_args()
    show = "\n".join((
        "#show needs_kindness/0.",
        "#show needs_problem_solving/0.",
        "#show friendship_grows/0.",
        "#show safe_tool_use/0.",
    ))
    if args.show_asp:
        print(asp_program(show))
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program(show))
        print("ASP model:", " ".join(sorted(symbol.name for symbol in model)))
        return
    if args.n < 1:
        raise StoryError("The sample count must be at least one.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = [
            generate(resolve_params(args, base_seed + index))
            for index in range(args.n)
        ]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples], indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} with {params.friend}: {params.scenario}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
