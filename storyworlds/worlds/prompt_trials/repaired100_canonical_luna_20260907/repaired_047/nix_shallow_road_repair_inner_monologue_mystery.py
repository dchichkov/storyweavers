#!/usr/bin/env python3
"""
A standalone folk-tale storyworld for a small road repair:
- setting: road repair
- seed words: nix, shallow
- narrative instruments: inner monologue, mystery to solve, foreshadowing
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
road_story(S) :- setting(S), has_mystery(S), has_foreshadowing(S), has_inner_monologue(S).
safe_fix(S) :- road_story(S), shallow_ditch(S), found_cause(S), repaired(S).
kind_ending(S) :- safe_fix(S), shared_road(S).
"""


PLACE = "road repair"


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
    helper: str
    tool: str
    road_material: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    first_clue: str
    failed_try: str
    warning: str
    helper_line: str
    mystery: str
    cause: str
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

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


NAMES = ["Luna", "Mara", "Tobin", "Nell", "Pip", "Sora", "Wren", "Odo"]
HELPERS = [
    "old badger",
    "village baker",
    "young crow",
    "kind goat",
    "bridge keeper",
    "little fox",
]
TOOLS = ["rake", "wooden shovel", "hand cart", "mallet", "lantern"]
ROAD_MATERIALS = ["gravel", "flat stones", "clay", "sand"]

SCENARIOS = [
    Scenario(
        key="singing_stones",
        premise="had promised to mend the road before the market carts arrived",
        trouble="By noon, one wheel sank into a shallow hollow that had not been there the day before.",
        first_clue="three bright pebbles lay in a neat line beside the hollow",
        failed_try="filling the hollow at once made the road look smooth, but the next cart dipped even deeper",
        warning="a soft humming came from beneath the road whenever the sun warmed the stones",
        helper_line='"A road can keep a secret under its skin," said the helper.',
        mystery="why did the fresh hollow return after it was filled",
        cause="a buried spring was pushing water upward through a cracked clay pipe",
        repair="following the pebble line, they uncovered the pipe, cleared its blocked mouth, and guided the water into a side ditch",
        result="The ground dried, and the hollow stayed firm beneath the test cart.",
        lesson="a careful listener finds the cause that a hurried hand might hide",
        ending="the market cart rolled over the repaired place while the little spring whispered safely beside the road",
    ),
    Scenario(
        key="vanishing_gravel",
        premise="was spreading a new layer of gravel along the hill road",
        trouble="Each morning, the gravel seemed to vanish from the middle of the road.",
        first_clue="small round tracks crossed the fresh gravel and ended at a thorn bush",
        failed_try="piling on more gravel only gave the unseen visitor a larger feast",
        warning="the thorn bush shook even when there was no wind",
        helper_line='"Something hungry may be carrying our stones away," the helper guessed.',
        mystery="who was taking the gravel each night",
        cause="a badger had opened a low burrow and was dragging stones aside to keep rain from its home",
        repair="they made a sturdy stone border around the burrow and carried the loose gravel back to the road",
        result="The badger kept its dry doorway, and the road kept its strong center.",
        lesson="a shared path grows better when every small home is noticed",
        ending="the repaired road shone gray in the morning, with tiny tracks safely outside its edge",
    ),
    Scenario(
        key="crooked_milepost",
        premise="was setting a new milepost beside a busy fork",
        trouble="The post leaned toward the wrong road and sent travelers toward a muddy marsh.",
        first_clue="a faded blue ribbon was tied around the post's buried end",
        failed_try="turning the sign above the ground made the arrow point correctly for only one direction",
        warning="the old bell at the fork rang whenever the post shifted",
        helper_line='"The bell remembers where the earth moved," said the helper.',
        mystery="why had the milepost sunk crookedly",
        cause="a flat stone beneath one side had cracked over an old animal tunnel",
        repair="they raised the post, packed the base with solid stones, and placed a small marker beside the tunnel",
        result="The arrow stayed true, and travelers could choose the right road.",
        lesson="a sign is trustworthy only when its foundation is sound",
        ending="the blue ribbon fluttered beside the straight milepost as the bell gave one cheerful ring",
    ),
    Scenario(
        key="night_frost",
        premise="was smoothing the road before winter travelers came",
        trouble="A narrow ridge rose across the road every night and vanished after sunrise.",
        first_clue="frost glittered in a line beneath the ridge even on warm mornings",
        failed_try="scraping the ridge flat left the same bump by breakfast",
        warning="a thin crack ran toward the nearby pond",
        helper_line='"The cold is leaving a message in the ground," the helper said.',
        mystery="what made the road lift and settle",
        cause="water beneath the road froze inside a shallow pocket and pushed the stones upward",
        repair="they opened a small drain toward the pond, filled the pocket with dry gravel, and packed the road in layers",
        result="The frost had room to escape, and the ridge did not return.",
        lesson="a lasting repair gives trouble a safe place to go",
        ending="winter sunlight touched a level road while meltwater hurried quietly through the new drain",
    ),
    Scenario(
        key="red_leaf_drain",
        premise="was clearing leaves from the road's narrow drainage ditch",
        trouble="Rainwater ran across the road instead of down the ditch.",
        first_clue="one red leaf spun in a circle beneath the wooden bridge",
        failed_try="sweeping the visible leaves away left the water circling in the same place",
        warning="the bridge plank creaked whenever the rain grew heavy",
        helper_line='"The leaf is pointing, not merely floating," the helper observed.',
        mystery="what hidden bend was trapping the water",
        cause="a fallen branch had wedged below the bridge and blocked the ditch's deeper channel",
        repair="they lifted the branch with the hand cart, cleared the channel, and strengthened the creaking plank",
        result="Rainwater flowed under the bridge without crossing the road.",
        lesson="a small sign may point to a problem hidden out of sight",
        ending="the red leaf sailed through the clean channel as the road stayed dry beneath the rain",
    ),
    Scenario(
        key="warm_stones",
        premise="was replacing loose stones near the village well",
        trouble="The new stones grew warm and shifted whenever the well rope was pulled.",
        first_clue="a circle of tiny ants avoided one particular stone",
        failed_try="wedging that stone tighter made the ground tremble beneath their boots",
        warning="warm air rose through a pinhole beside the well path",
        helper_line='"Do not silence a warning by pressing on it," said the helper.',
        mystery="what was moving the stones from below",
        cause="the well's old overflow tunnel had filled with earth and was forcing water beneath the path",
        repair="they cleared the overflow tunnel, laid a flat cover over it, and reset the stones on firm ground",
        result="The well path became cool and steady again.",
        lesson="when the earth gives a warning, patience is stronger than force",
        ending="the ants crossed the reset stones, and the well rope swung over a quiet, solid path",
    ),
    Scenario(
        key="lost_marker",
        premise="was painting bright marks along the road for travelers in fog",
        trouble="The marker at the bend disappeared each evening and returned at dawn.",
        first_clue="a smear of white paint climbed the bark of a nearby tree",
        failed_try="painting a taller marker only made the white smear appear higher",
        warning="a night bird called whenever the mist touched the bend",
        helper_line='"The fog is lifting more than paint," the helper whispered.',
        mystery="where the marker went after sunset",
        cause="a loose road sign was swinging in the wind and rubbing against the tree",
        repair="they tightened the signpost, moved the marker above the mist line, and painted a second small arrow",
        result="The sign stayed visible through the fog and no longer scraped the tree.",
        lesson="good directions should stand steady for those who need them",
        ending="two white arrows gleamed at the bend while the night bird called from the quiet tree",
    ),
    Scenario(
        key="hollow_echo",
        premise="was checking the road before a wedding procession crossed it",
        trouble="Every hoofbeat near the old oak made a hollow echo beneath the road.",
        first_clue="dust puffed from a hairline crack beside the oak's roots",
        failed_try="covering the crack with dirt made the echo sound deeper",
        warning="the oak dropped one acorn each time the road trembled",
        helper_line='"The tree is knocking on a hidden door," the helper said.',
        mystery="what empty space lay beneath the road",
        cause="an abandoned stone culvert had lost its cap and was pulling soil downward",
        repair="they found the culvert, replaced its cap with flat stones, and packed the road above it",
        result="The road became quiet and strong enough for the procession.",
        lesson="a mystery is best solved by following the signs that agree",
        ending="the wedding horses passed beneath the oak, and not one hoofbeat answered from below",
    ),
]

OPENINGS = [
    "At first light, {name} walked to the road repair yard with a basket of tools.",
    "Beyond the last cottage, {name} found the village road waiting beneath a pale sky.",
    "The folk of the valley trusted {name} to mend roads that had grown tired.",
    "One bright morning, {name} heard a cartwheel complain at the edge of the village.",
    "Before the baker's oven warmed, {name} carried a lantern toward the road repair.",
    "The old road wound between fields, and {name} knew every stone along its way.",
]

INNER_THOUGHTS = [
    '"I should not patch a puzzle before I understand it," {name} thought.',
    '"A shallow mark can hide a deep cause," {name} told themself.',
    '"If the road is speaking, I must listen before I lift my tool," {name} thought.',
    '"The quickest fix may be no fix at all," {name} decided.',
    '"One clue is a beginning, not an answer," {name} reminded themself.',
    '"I will follow the signs together, like stepping-stones," {name} thought.',
]

PLANS = [
    "They agreed to mark the safe edge, study the ground, and change only one thing at a time.",
    "They placed the tools aside, traced the water's path, and compared every clue.",
    "They worked slowly: one friend watched the road while the other tested the ground.",
    "They made a little map in the dust before moving a single stone.",
    "They listened for the warning again, then chose the gentlest repair that could last.",
]

CELEBRATIONS = [
    "The helper clapped softly, for a repair that lasts needs no grand boast.",
    "The two friends smiled because the road was safe for everyone, not because one of them had guessed first.",
    "They tested the place twice, then shared a warm heel of bread beside the ditch.",
    "A passing traveler thanked them, and the repaired road answered with a steady wheel-song.",
    "They left the worksite tidier than they had found it, with every tool back in its place.",
]

TOOL_ACTIONS = {
    "rake": "used the rake to clear loose soil and reveal the road's hidden edge",
    "wooden shovel": "used the wooden shovel to lift earth without cracking the old stones",
    "hand cart": "rolled the hand cart close so they could move heavy pieces safely",
    "mallet": "tapped the mallet gently, testing each stone before setting it",
    "lantern": "held the lantern low so small cracks and damp places showed clearly",
}


def valid_tools() -> list[str]:
    return list(TOOLS)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("A road repair story needs a named worker.")
    if params.helper not in HELPERS:
        raise StoryError("The helper must be a gentle, believable road-side companion.")
    if params.tool not in TOOLS:
        raise StoryError("The repair tool must be safe and suitable for a small road.")
    if params.road_material not in ROAD_MATERIALS:
        raise StoryError("The road material must be a simple natural repair material.")


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        helper=rng.choice(HELPERS),
        tool=rng.choice(TOOLS),
        road_material=rng.choice(ROAD_MATERIALS),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Folk-tale road repair storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--road-material", choices=ROAD_MATERIALS)
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
    if args.name:
        params.name = args.name
    if args.helper:
        params.helper = args.helper
    if args.tool:
        params.tool = args.tool
    if args.road_material:
        params.road_material = args.road_material
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    worker = world.add(Entity(id="worker", kind="character", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", label=params.helper))
    tool = world.add(Entity(id="tool", kind="tool", label=params.tool))
    material = world.add(Entity(id="material", kind="material", label=params.road_material))
    world.facts.update(
        worker=worker,
        helper=helper,
        tool=tool,
        material=material,
        place=PLACE,
        setting="road repair",
        has_mystery=True,
        has_foreshadowing=True,
        has_inner_monologue=True,
        style="folk tale",
        seed_words=["nix", "shallow"],
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    worker = world.get("worker")
    helper = world.get("helper")
    tool = world.get("tool")
    material = world.get("material")

    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    opening = rng.choice(OPENINGS).format(name=worker.label)
    thought = rng.choice(INNER_THOUGHTS).format(name=worker.label)
    plan = rng.choice(PLANS)
    celebration = rng.choice(CELEBRATIONS)
    tool_action = TOOL_ACTIONS[tool.label]

    worker.bump_meme("patience")
    worker.bump_meme("curiosity")
    helper.bump_meme("wisdom")

    world.say(opening)
    world.say(
        f"{worker.label} worked beside {helper.label}, spreading {material.label} "
        f"and checking each place where the road might trouble a traveler."
    )
    world.say(f"{scenario.premise.capitalize()}.")
    world.para()

    worker.bump_meter("risk_seen")
    world.say(scenario.trouble)
    world.say(f"The first clue was clear: {scenario.first_clue}.")
    world.say(
        f"At first, {worker.label} tried a quick repair, but {scenario.failed_try}."
    )
    world.say(f"Then {scenario.warning}.")
    world.say(thought)
    world.say(f"{worker.label} looked at {helper.label}.")
    world.say(scenario.helper_line)
    world.say(f'"Then the mystery is not the hollow itself. We must learn {scenario.mystery}," {worker.label} replied.')
    world.para()

    worker.bump_meme("care")
    helper.bump_meme("trust")
    world.say(plan)
    world.say(f"Together they discovered that {scenario.cause}.")
    world.say(
        f"{worker.label} {tool_action}, while {helper.label} watched the road edge "
        "and called out each safe place to stand."
    )
    world.para()

    tool.bump_meter("used", 1)
    material.bump_meter("placed", 1)
    worker.bump_meter("repair_complete", 1)
    world.say(
        f"Using the {material.label}, they {scenario.repair}."
    )
    world.say(scenario.result)
    world.say(celebration)
    world.para()

    worker.bump_meme("relief")
    helper.bump_meme("joy")
    world.say(f"They agreed that {scenario.lesson}.")
    world.say(
        f"Thus the road was mended, not merely hidden beneath a fresh layer of {material.label}. "
        f"{scenario.ending}."
    )

    world.facts.update(
        scenario=scenario.key,
        premise=scenario.premise,
        trouble=scenario.trouble,
        first_clue=scenario.first_clue,
        failed_try=scenario.failed_try,
        warning=scenario.warning,
        mystery=scenario.mystery,
        cause=scenario.cause,
        repair=scenario.repair,
        result=scenario.result,
        lesson=scenario.lesson,
        ending_image=scenario.ending,
        thought=thought,
        tool_action=tool_action,
        shallow=True,
        nix=True,
        found_cause=True,
        repaired=True,
        shared_road=True,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    worker = facts["worker"].label
    helper = facts["helper"].label
    tool = facts["tool"].label
    scenario = str(facts["scenario"]).replace("_", " ")
    return [
        f"Write a folk tale set during road repair in which {worker} and {helper} solve a mystery.",
        "Tell a child-friendly road repair story using the words nix and shallow.",
        f"Include inner monologue, foreshadowing, and a mystery to solve about a {scenario} problem.",
        f"Show how a {tool} helps reveal the cause instead of merely hiding the trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    worker = facts["worker"].label
    helper = facts["helper"].label
    tool = facts["tool"].label
    material = facts["material"].label
    return [
        QAItem(
            question="What trouble appeared on the road?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question=f"What early clue helped {worker} and {helper} investigate?",
            answer=f"They noticed that {facts['first_clue']}.",
        ),
        QAItem(
            question=f"What mystery did the road workers need to solve?",
            answer=f"They needed to discover {facts['mystery']}.",
        ),
        QAItem(
            question="What was causing the road trouble?",
            answer=f"The cause was that {facts['cause']}.",
        ),
        QAItem(
            question=f"How did the {tool} and the {material} help?",
            answer=f"{worker} {facts['tool_action']}, and then they used the {material} as they {facts['repair']}.",
        ),
        QAItem(
            question="How did the ending prove that the repair worked?",
            answer=str(facts["ending_image"]),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does shallow mean?",
            answer="Shallow means not very deep, like a small ditch or a thin puddle.",
        ),
        QAItem(
            question="What does nix mean?",
            answer="Nix means to stop, cancel, or refuse something.",
        ),
        QAItem(
            question="Why should a road worker look for a cause instead of only covering a hole?",
            answer="Finding the cause can make the repair last, while covering the hole may let the same trouble return.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early sign or hint that prepares us for something important later.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thoughts, shared so readers can understand what the character is considering.",
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


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("setting", "road_repair"),
        asp.fact("has_mystery", "road_repair"),
        asp.fact("has_foreshadowing", "road_repair"),
        asp.fact("has_inner_monologue", "road_repair"),
        asp.fact("shallow_ditch", "road_repair"),
        asp.fact("found_cause", "road_repair"),
        asp.fact("repaired", "road_repair"),
        asp.fact("shared_road", "road_repair"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show road_story/1.\n"
        "#show safe_fix/1.\n"
        "#show kind_ending/1."
    )
    model = asp.one_model(program)
    actual = {
        (symbol.name, tuple(
            arg.name if arg.type != 1 else arg.string
            for arg in symbol.arguments
        ))
        for symbol in model
        if symbol.name in {"road_story", "safe_fix", "kind_ending"}
    }
    expected = {
        ("road_story", ("road_repair",)),
        ("safe_fix", ("road_repair",)),
        ("kind_ending", ("road_repair",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python reasonableness gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    checks = [
        StoryParams(name="Luna", helper="young crow", tool="rake", road_material="gravel", seed=7),
        StoryParams(name="Mara", helper="old badger", tool="lantern", road_material="flat stones", seed=13),
        StoryParams(name="Tobin", helper="kind goat", tool="wooden shovel", road_material="clay", seed=19),
    ]
    for params in checks:
        sample = generate(params)
        if not sample.story.strip():
            print("Generated story was empty.")
            return 1
        if "nix" not in sample.story or "shallow" not in sample.story:
            print("Generated story omitted a required seed word.")
            return 1
        if not sample.story_qa:
            print("Generated story omitted grounded questions.")
            return 1

    print("OK: ASP twin matches the Python gate and generated stories pass.")
    return 0


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show kind_ending/1."))
    return sorted(set(asp.atoms(model, "kind_ending")))


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


def dump_trace(world: World) -> str:
    return world.trace()


CURATED = [
    StoryParams(
        name="Luna",
        helper="young crow",
        tool="rake",
        road_material="gravel",
        seed=47,
    ),
    StoryParams(
        name="Mara",
        helper="old badger",
        tool="lantern",
        road_material="flat stones",
        seed=71,
    ),
    StoryParams(
        name="Tobin",
        helper="kind goat",
        tool="wooden shovel",
        road_material="clay",
        seed=103,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show road_story/1.\n#show safe_fix/1.\n#show kind_ending/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP-compatible road repair stories:")
        for item in asp_list():
            print(item)
        return

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
            params = resolve_params(
                args,
                random.Random(rng.randrange(2**31)),
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
