#!/usr/bin/env python3
"""
A standalone adventure storyworld about a village vote, a shared trail,
and a conflict resolved by listening across an ethnic festival.

Seed words: ethnic, vote
Narrative instruments: repetition, conflict, inner monologue.
"""

from __future__ import annotations

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
setting(hill_village).
has_vote(hill_village).
has_conflict(hill_village).
has_adventure(hill_village).
uses_repetition(hill_village).
uses_inner_monologue(hill_village).
ethnic_community(hill_village).
fair_vote(hill_village) :- has_vote(hill_village), has_conflict(hill_village),
    listens(hill_village), shared_path(hill_village).
good_adventure(hill_village) :- fair_vote(hill_village), has_adventure(hill_village).
"""


PLACE = "Hill Village"


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
    companion: str
    community: str
    landmark: str
    tool: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    first_vote: str
    clue: str
    conflict_line: str
    inner_thought: str
    repeated_call: str
    repair: str
    result: str
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
            lines.append(
                f"  {entity.id:10} ({entity.kind:10}) "
                f"label={entity.label!r} {' '.join(details)}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


NAMES = ["Luna", "Mira", "Tavi", "Noor", "Ari", "Sela", "Jonah", "Pia"]
COMPANIONS = ["Kito", "Mara", "Suri", "Tomas", "Nia", "Bram"]
COMMUNITIES = ["river people", "forest people", "mountain people", "desert people"]
LANDMARKS = ["Echo Bridge", "red canyon", "Moon Gate", "wind tower"]
TOOLS = ["rope", "lantern", "compass", "wooden staff"]


SCENARIOS = [
    Scenario(
        key="broken_bridge_vote",
        premise="was carrying the village vote box toward the old mountain path",
        trouble="The bridge ahead had lost two planks, and the people behind Luna could not cross safely.",
        first_vote="most travelers voted to turn back, while a smaller group voted to cross at once",
        clue="fresh rope marks showed that a repair crew had used the bridge only yesterday",
        conflict_line='"Our people always cross first," a traveler from the river people declared. "We cannot wait for theirs."',
        inner_thought="Luna thought, I want my side to win, but a winning vote that leaves someone in danger is not fair.",
        repeated_call="Listen first, listen twice, then choose together.",
        repair="asked each ethnic group to name one safe idea, tied the rope around the strongest post, and tested a new crossing one step at a time",
        result="The bridge held, and the vote box reached the hilltop without anyone being left behind.",
        ending="At sunset, every group added a bright thread to the repaired rope.",
    ),
    Scenario(
        key="foggy_fork",
        premise="was guiding the community vote along a trail above the cloud line",
        trouble="Fog covered the fork, and two stone arrows pointed in opposite directions.",
        first_vote="one side voted for the steep trail, while another voted for the long trail beside the cliffs",
        clue="small blue shells marked a safe route toward the echoing bell",
        conflict_line='"The old path belongs to us," said a guide from the mountain people. "Your signs should not decide for everyone."',
        inner_thought="Luna wondered, If I speak louder, will anyone hear the truth beneath the fear?",
        repeated_call="Check the clue, check the map, check one another.",
        repair="shared the compass, compared every group's landmarks, and voted again only after all voices had been heard",
        result="The new vote chose the shell-marked path, which led safely around the cliff.",
        ending="The village bell rang through the fog as the travelers arrived together.",
    ),
    Scenario(
        key="fallen_gate",
        premise="was leading the vote toward a forest gate that opened only at midday",
        trouble="A fallen tree blocked the gate, and the opening hour was drawing near.",
        first_vote="half the travelers voted to climb over the tree, while the others voted to search for a side path",
        clue="green leaves bent beneath the trunk showed that a narrow passage ran around it",
        conflict_line='"You always choose the slow way," a forest guide complained. "You do not trust our path."',
        inner_thought="Luna told herself, A quick answer can still be the wrong answer.",
        repeated_call="Look closely, speak kindly, decide safely.",
        repair="let each community inspect the leaves, used the wooden staff to test the ground, and took the narrow passage",
        result="They reached the gate before noon and opened it without breaking a single branch.",
        ending="The gate swung wide, and sunlight painted every traveler in the same golden stripe.",
    ),
    Scenario(
        key="storm_marker",
        premise="was bringing a shared vote to a high meadow before a storm arrived",
        trouble="Wind tore the trail marker from its post and sent it tumbling toward a ravine.",
        first_vote="some voters chose to chase it, while others voted to shelter under the rocks",
        clue="the marker's red cord was still tied to a low bush near the safe ground",
        conflict_line='"Your people lost the marker," someone shouted. "Now your choice should not count."',
        inner_thought="Luna felt her cheeks grow hot, but she thought, Blame cannot tie a cord or guide a traveler.",
        repeated_call="Name the danger, share the work, return to the question.",
        repair="sent two adults after the loose sign, kept children under shelter, and held the vote again after the marker was secured",
        result="The path became clear, and the final vote sent everyone toward the meadow shelter.",
        ending="Rain drummed on the roof while the repaired marker pointed steadily home.",
    ),
    Scenario(
        key="cave_lantern",
        premise="was carrying the village vote into a cave where an old spring supplied every neighborhood",
        trouble="The only lantern flickered, and a narrow ledge crossed a dark pool.",
        first_vote="one group voted to hurry across, while another voted to wait for more light",
        clue="white chalk dots appeared at shoulder height along the safe wall",
        conflict_line='"Your custom says to wait," a visitor snapped. "Our families have no time for waiting."',
        inner_thought="Luna thought, Courage is not the same as rushing.",
        repeated_call="One light, one step, one careful choice.",
        repair="held the lantern high, followed the chalk dots, and let every group vote on each difficult step",
        result="The travelers reached the spring, filled their jars, and returned before the flame went out.",
        ending="The lantern glowed beside the spring as every family's jar shone with water.",
    ),
    Scenario(
        key="split_trail",
        premise="was taking the first vote of the day toward a far watchtower",
        trouble="A landslide split the trail into a narrow upper path and a muddy lower path.",
        first_vote="the first count ended in a tie, and both sides began claiming that the other side had cheated",
        clue="old boot prints crossed the upper path in pairs, showing that it had held travelers recently",
        conflict_line='"Count again until we get our answer," said one group. "No, count until you get ours," answered another.',
        inner_thought="Luna thought, A vote cannot be a rope for pulling friends apart.",
        repeated_call="Count fairly, hear clearly, walk together.",
        repair="showed the boot prints to everyone, asked two neutral helpers to count, and held one open revote",
        result="The upper path won by one careful vote, and the group crossed it in a single line.",
        ending="At the watchtower, the old flag rose above a trail made peaceful by patience.",
    ),
]


OPENINGS = [
    "At dawn, Luna climbed the hill toward the meeting fire.",
    "The first sunbeam touched the trail just as Luna reached the village square.",
    "Beyond the last garden, an adventure waited for Luna and the morning travelers.",
    "Luna woke to the sound of drums calling every neighborhood to the hill.",
    "A silver trail curled beyond the village, and Luna carried an important vote toward it.",
    "Before the clouds lifted, Luna met the travelers beside the old map stone.",
]


REACTIONS = [
    "Luna raised one hand and asked everyone to pause before the argument grew larger.",
    "Luna took a breath and looked from one worried face to another.",
    "Instead of shouting over the conflict, Luna asked what danger each side could see.",
    "Luna stepped between the angry voices, not to choose a side, but to make room for the truth.",
    "The argument pulled at Luna like two ropes, yet Luna remembered that every traveler mattered.",
]


PLANS = [
    "They placed the vote box where everyone could see it and named the safety question aloud.",
    "They agreed that every ethnic community would offer one observation before anyone voted again.",
    "They marked the safe ground, counted the travelers, and gave the youngest listeners a clear place near the fire.",
    "They divided the work so that no single group carried the risk alone.",
]


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        companion=rng.choice(COMPANIONS),
        community=rng.choice(COMMUNITIES),
        landmark=rng.choice(LANDMARKS),
        tool=rng.choice(TOOLS),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The adventurer needs a name.")
    if not params.companion.strip():
        raise StoryError("The adventurer needs a companion.")
    if params.community not in COMMUNITIES:
        raise StoryError("The ethnic community must come from the village registry.")
    if params.landmark not in LANDMARKS:
        raise StoryError("The landmark must be a registered adventure landmark.")
    if params.tool not in TOOLS:
        raise StoryError("The tool must be safe and useful on a trail.")


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "hill_village"),
            asp.fact("has_vote", "hill_village"),
            asp.fact("has_conflict", "hill_village"),
            asp.fact("has_adventure", "hill_village"),
            asp.fact("uses_repetition", "hill_village"),
            asp.fact("uses_inner_monologue", "hill_village"),
            asp.fact("ethnic_community", "hill_village"),
            asp.fact("listens", "hill_village"),
            asp.fact("shared_path", "hill_village"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adventure storyworld about a fair village vote."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--community", choices=COMMUNITIES)
    parser.add_argument("--landmark", choices=LANDMARKS)
    parser.add_argument("--tool", choices=TOOLS)
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
    for field_name in ("name", "companion", "community", "landmark", "tool"):
        value = getattr(args, field_name)
        if value:
            setattr(params, field_name, value)
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity("hero", "adventurer", params.name))
    world.add(Entity("companion", "companion", params.companion))
    world.add(Entity("community", "ethnic community", params.community))
    world.add(Entity("landmark", "landmark", params.landmark))
    world.add(Entity("tool", "tool", params.tool, owner=params.name))
    world.facts.update(
        place=PLACE,
        hero=world.get("hero"),
        companion=world.get("companion"),
        community=world.get("community"),
        landmark=world.get("landmark"),
        tool=world.get("tool"),
        has_vote=True,
        has_conflict=True,
        adventure=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    opening = rng.choice(OPENINGS)
    reaction = rng.choice(REACTIONS)
    plan = rng.choice(PLANS)

    hero = world.get("hero")
    companion = world.get("companion")
    community = world.get("community")
    landmark = world.get("landmark")
    tool = world.get("tool")

    hero.bump_meter("steps", 1)
    hero.bump_meme("courage", 1)
    companion.bump_meme("trust", 1)

    world.say(f"{opening} {hero.label} traveled with {companion.label}.")
    world.say(
        f"The travelers represented many neighborhoods, including the {community.label}. "
        f"They were headed toward {landmark.label}, and {hero.label} {scenario.premise}."
    )
    world.para()

    world.say(scenario.trouble)
    world.say(f"At the first count, {scenario.first_vote}.")
    world.say(reaction)
    world.say(f'{hero.label} said, "Before we choose, let us hear every voice."')
    world.para()

    world.say(f"Then they found a clue: {scenario.clue}.")
    world.say(scenario.conflict_line)
    world.say(f"{companion.label} answered, '" + "We can be brave without pushing anyone aside."')
    world.say(scenario.inner_thought)
    world.say(f"{hero.label} repeated the village rule: {scenario.repeated_call}")
    world.say(f'"{scenario.repeated_call}" {companion.label} repeated.')
    world.para()

    world.bump_meter("votes", 2)
    world.bump_meme("listening", 1)
    world.say(plan)
    world.say(
        f"{hero.label} used the {tool.label} to make the next step safer, while "
        f"{companion.label} watched the ground."
    )
    world.say(f"Together, they {scenario.repair}.")
    world.say(scenario.result)
    world.para()

    hero.bump_meter("steps", 3)
    hero.bump_meme("wisdom", 1)
    companion.bump_meme("joy", 1)
    world.say(
        f"The conflict softened because the vote answered a shared danger instead of dividing "
        f"the travelers into winners and losers."
    )
    world.say(f"{hero.label} told {companion.label}, '" + "A fair adventure leaves a path for everyone."')
    world.say(f"{scenario.ending} {hero.label} carried the vote safely home.")
    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        first_vote=scenario.first_vote,
        clue=scenario.clue,
        conflict_line=scenario.conflict_line,
        inner_thought=scenario.inner_thought,
        repeated_call=scenario.repeated_call,
        repair=scenario.repair,
        result=scenario.result,
        ending=scenario.ending,
        resolved=True,
        fair_vote=True,
        listened=True,
        shared_path=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write an adventure about {facts['hero'].label} carrying a vote through a dangerous trail.",
        "Include the words ethnic and vote in a child-friendly story about a community conflict.",
        "Use repetition and inner monologue while showing how listening makes a fair decision.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    companion = facts["companion"].label
    tool = facts["tool"].label
    return [
        QAItem(
            question="What danger interrupted the travelers' adventure?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question=f"What clue did {hero} and {companion} discover?",
            answer=f"They discovered that {facts['clue']}.",
        ),
        QAItem(
            question="What caused the conflict among the travelers?",
            answer=str(facts["conflict_line"]),
        ),
        QAItem(
            question=f"How did {hero} help make the vote fair?",
            answer=(
                f"{hero} repeated the rule, listened to every group, and used the {tool} "
                f"while the travelers worked together to {facts['repair']}."
            ),
        ),
        QAItem(
            question="What showed that the adventure ended well?",
            answer=str(facts["ending"]),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vote?",
            answer="A vote is a way for people to choose between options by giving their opinion.",
        ),
        QAItem(
            question="What does ethnic mean?",
            answer="Ethnic describes a group of people who share parts of a culture, history, language, or family heritage.",
        ),
        QAItem(
            question="Why should people listen during a conflict?",
            answer="Listening helps people understand the danger, needs, and ideas behind different sides before they decide what to do.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition is when a word, phrase, or action appears again to make an idea clear or memorable.",
        ),
    ]


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


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show fair_vote/1.\n#show good_adventure/1."
    )
    model = asp.one_model(program)
    found = {
        (symbol.name, tuple(asp_value.name for asp_value in symbol.arguments))
        for symbol in model
        if symbol.name in {"fair_vote", "good_adventure"}
    }
    expected = {
        ("fair_vote", ("hill_village",)),
        ("good_adventure", ("hill_village",)),
    }
    if found != expected:
        print("MISMATCH between ASP and Python reasonableness gate.")
        print("ASP:", sorted(found))
        print("PY :", sorted(expected))
        return 1

    sample = generate(
        StoryParams(
            name="Luna",
            companion="Kito",
            community="river people",
            landmark="Echo Bridge",
            tool="rope",
            seed=7,
        )
    )
    required = ["vote", "ethnic", "listen", "fair"]
    lowered = sample.story.lower()
    if not all(word in lowered for word in required):
        print("MISMATCH: generated story does not exercise the requested narrative domain.")
        return 1

    print("OK: ASP twin and generated story checks passed.")
    return 0


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_adventure/1."))
    return sorted(asp.atoms(model, "good_adventure"))


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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Kito", "river people", "Echo Bridge", "rope", 11),
    StoryParams("Mira", "Suri", "mountain people", "red canyon", "compass", 23),
    StoryParams("Tavi", "Nia", "forest people", "Moon Gate", "wooden staff", 37),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show fair_vote/1.\n#show good_adventure/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        print("ASP-compatible adventure facts:")
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
        while len(samples) < max(0, args.n) and attempts < max(50, args.n * 50):
            params = resolve_params(
                args, random.Random(rng.randrange(2**31))
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
