#!/usr/bin/env python3
"""
A standalone slice-of-life storyworld about smooth thinking, good sense, and humor.

Luna wants to help prepare a small neighborhood breakfast, but a wobbly table,
a runaway bowl, and a misunderstood joke make the morning untidy. By listening,
measuring, and laughing kindly, Luna turns the trouble into a shared solution.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

ENTITY_HUMAN = "human"
ENTITY_OBJECT = "object"
ENTITY_ANIMAL = "animal"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    owner: Optional[str] = None


@dataclass
class World:
    setting: str
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    neighbor: str
    recipe: str
    opening_style: int = 0
    joke_style: int = 0
    repair_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    food: str
    plan: str
    trouble: str
    clue: str
    first_try: str
    need: str
    repair: str
    invitation: str
    helpful_action: str
    ending: str
    lesson: str


SETTINGS = {
    "apartment courtyard": "the apartment courtyard",
    "community room": "the community room",
    "front porch": "the front porch",
    "small park": "the small park",
}

HERO_NAMES = ["Luna", "Mara", "Nia", "Suri", "Tess", "Ari"]
HELPER_NAMES = ["Pip", "Jo", "Milo", "Bea", "Ren"]
NEIGHBOR_NAMES = ["Mr. Vale", "Auntie June", "Sam", "Inez", "Theo"]

RECIPES = {
    "pancakes": Scenario(
        food="pancakes",
        plan="stacked a warm tower of pancakes for everyone to share",
        trouble="the syrup bowl slid across the table and made a shiny river toward the napkins",
        clue="noticed one table leg rocking whenever the wind touched the tablecloth",
        first_try="pressed a folded napkin under the leg, but the napkin slowly squeezed out like a tired tongue",
        need="was trying to keep the heavy syrup bowl away from the table's weak corner",
        repair="used a wooden spoon as a brace and moved the bowl to the steady middle",
        invitation="Tell me before you push something; we can make the table steady together",
        helpful_action="held the spoon brace while Luna tucked a cork beneath the leg",
        ending="The final pancake stayed perfectly still, although Pip gave it a solemn little bow.",
        lesson="Good sense means looking for the cause of a mess before blaming the nearest helper.",
    ),
    "fruit salad": Scenario(
        food="fruit salad",
        plan="made a bright bowl of fruit for the first sunny breakfast of spring",
        trouble="a strawberry rolled away and led three blueberries under the serving table",
        clue="heard a faint squeak whenever the serving tray moved",
        first_try="chased the berries with a plate, which sent a grape bouncing into a flowerpot",
        need="was trying to warn everyone that a loose wheel made the tray unsafe",
        repair="placed a smooth cloth beneath the tray and tightened its little wheel",
        invitation="Show me the squeak, and we will make the tray safe before we carry it",
        helpful_action="pointed to the loose wheel while Luna held the tray steady",
        ending="The fruit bowl gleamed in the sun, and the runaway strawberry became the first bite.",
        lesson="A small warning can be more useful than a big hurry.",
    ),
    "muffins": Scenario(
        food="blueberry muffins",
        plan="set out blueberry muffins with paper flags naming each flavor",
        trouble="the flags spun loose and landed in the batter bowl like tiny sails",
        clue="saw that the fan above the counter was blowing much harder than usual",
        first_try="turned every flag upside down, which made the names even more confusing",
        need="was trying to show that the fan was rattling and might drop dust into the food",
        repair="switched off the fan, covered the batter, and tied the flags with smooth ribbon",
        invitation="You found an important problem. Help me make the labels safe and clear",
        helpful_action="held the ribbon while Luna tied each flavor flag firmly",
        ending="The muffins cooled beneath their neat flags, and one label proudly read BLUEBERRY.",
        lesson="A funny-looking mistake may carry sensible information.",
    ),
    "toast": Scenario(
        food="toast",
        plan="served toast with little bowls of honey and apple slices",
        trouble="the toast popped high, and a honey spoon landed in the flower box",
        clue="noticed the toaster lever was stuck halfway down",
        first_try="tapped it with a butter knife, which made the toaster give a dramatic pop",
        need="was copying the stuck lever because it thought the toaster was asking for help",
        repair="unplugged the toaster, waited, and used a wooden stick only after the adults checked it",
        invitation="Funny popping is not a safe game, but your warning helped us notice the lever",
        helpful_action="pointed from the toaster to the stuck lever while everyone kept a safe distance",
        ending="The next slice rose quietly, as if it had learned table manners.",
        lesson="Humor is welcome, but safety gets the first turn.",
    ),
    "oatmeal": Scenario(
        food="oatmeal",
        plan="served oatmeal with cinnamon shapes on top",
        trouble="the cinnamon shaker dropped a brown mustache across the table",
        clue="saw a tiny crack around the shaker lid",
        first_try="covered the crack with a napkin, which became a cinnamon ghost",
        need="was trying to stop the lid from falling into the oatmeal",
        repair="replaced the cracked lid and gave the shaker a clean, smooth top",
        invitation="You were right to stop the shaker. Let us fix it before breakfast continues",
        helpful_action="held the bowl while Luna changed the lid and wiped the table",
        ending="Each oatmeal bowl had a cinnamon smile, and none of them had a cinnamon ghost.",
        lesson="A careful repair can turn a silly spill into a calmer morning.",
    ),
}

OPENINGS = [
    "{hero} liked mornings that began with small jobs and ended with everyone sitting close.",
    "At breakfast time, {hero} believed even a crooked table could become part of the story.",
    "{hero} arrived early, carrying a recipe card, a cloth, and a very serious spoon.",
    "The morning was ordinary in the best way: warm food, familiar neighbors, and {hero} ready to help.",
    "{hero} had learned that a shared breakfast needed less perfection than patience.",
]

JOKES = [
    "The table looked as if it were practicing a tiny dance.",
    "Pip inspected the syrup with the grave face of a detective who had found a very sweet clue.",
    "For one moment, the napkins formed a white parade across the floor.",
    "The spoon landed so neatly that everyone wondered whether it had planned the trip.",
    "The bowl made a slow turn, like a plate pretending to be a merry-go-round.",
    "Even the flowerpot seemed surprised to receive a grape.",
]

REPAIRS = [
    "Luna took one breath, then looked underneath the trouble instead of only at its mess.",
    "Luna set down the joke and picked up the practical question.",
    "Luna smiled, but she did not rush; smooth solutions often began with a pause.",
    "Luna knelt beside the table so the small problem was easier to see.",
    "Luna asked everyone to keep their hands still for a moment while she checked the cause.",
]

ASP_RULES = r"""
% The breakfast is unstable when the serving surface rocks.
unstable(S) :- setting(S), rocks(table), bowl_on(table).

% A sensible repair makes the table safe and lets the meal continue.
reasonable(S) :- setting(S), unstable(S), brace_used(table), bowl_safe(bowl).

% Humor remains kind when it accompanies listening rather than blame.
kind_humor(S) :- reasonable(S), joke_shared(hero, helper).
valid_story(S) :- kind_humor(S).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines.extend(
        [
            asp.fact("rocks", "table"),
            asp.fact("bowl_on", "table"),
            asp.fact("brace_used", "table"),
            asp.fact("bowl_safe", "bowl"),
            asp.fact("joke_shared", "hero", "helper"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    found = set(asp.atoms(model, "valid_story"))
    expected = {("apartment_courtyard",), ("community_room",), ("front_porch",), ("small_park",)}
    # ASP constants use underscores only when explicitly emitted that way.
    if found == expected:
        print(f"OK: ASP model covers {len(expected)} settings.")
        return 0
    print("MISMATCH between Python and ASP setting coverage.")
    print("expected:", sorted(expected))
    print("found:", sorted(found))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A smooth slice-of-life story about sense, humor, and breakfast."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--neighbor")
    parser.add_argument("--recipe", choices=RECIPES)
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
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        neighbor=args.neighbor or rng.choice(NEIGHBOR_NAMES),
        recipe=args.recipe or rng.choice(list(RECIPES)),
        opening_style=rng.randrange(len(OPENINGS)),
        joke_style=rng.randrange(len(JOKES)),
        repair_style=rng.randrange(len(REPAIRS)),
    )


def validate(params: StoryParams) -> None:
    names = [params.hero, params.helper, params.neighbor]
    lowered = [name.strip().lower() for name in names]
    if len(set(lowered)) != len(lowered):
        raise StoryError("The hero, helper, and neighbor need different names so the dialogue is clear.")
    if not params.hero.strip():
        raise StoryError("The hero needs a name.")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}.")
    if params.recipe not in RECIPES:
        raise StoryError(f"Unknown breakfast recipe: {params.recipe}.")


def build_world(params: StoryParams) -> World:
    validate(params)
    scenario = RECIPES[params.recipe]
    world = World(SETTINGS[params.setting])

    hero = world.add(
        Entity(
            id="hero",
            kind=ENTITY_HUMAN,
            type="child",
            label=params.hero,
            phrase=f"{params.hero}, who liked useful jokes",
            memes={"sense": 0.5, "worry": 0.0, "joy": 0.5},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind=ENTITY_HUMAN,
            type="neighbor-child",
            label=params.helper,
            phrase=f"{params.helper}, a quick and cheerful helper",
            meters={"speed": 1.0},
            memes={"worry": 0.5, "pride": 0.0},
            location="serving table",
        )
    )
    neighbor = world.add(
        Entity(
            id="neighbor",
            kind=ENTITY_HUMAN,
            type="neighbor",
            label=params.neighbor,
            phrase=f"{params.neighbor}, the breakfast neighbor",
            memes={"patience": 1.0, "joy": 0.5},
            location="kitchen door",
        )
    )
    table = world.add(
        Entity(
            id="table",
            kind=ENTITY_OBJECT,
            type="folding table",
            label="table",
            phrase="the folding table",
            meters={"smooth": 0.0, "stable": 0.0},
            location="center of the setting",
        )
    )
    bowl = world.add(
        Entity(
            id="bowl",
            kind=ENTITY_OBJECT,
            type="serving bowl",
            label=scenario.food,
            phrase=f"a bowl of {scenario.food}",
            meters={"safe": 0.0, "moving": 0.0},
            location="table corner",
        )
    )

    world.facts.update(
        params=params,
        scenario=scenario,
        hero=hero,
        helper=helper,
        neighbor=neighbor,
        table=table,
        bowl=bowl,
        cause_found=False,
        repair_done=False,
        dialogue_changed=False,
        resolved=False,
    )
    return world


def predict_stability(world: World) -> dict[str, bool]:
    simulation = world.copy()
    table = simulation.get("table")
    bowl = simulation.get("bowl")
    unstable = table.meters.get("stable", 0.0) < 1.0 and bowl.location == "table corner"
    return {"unstable": unstable, "safe": not unstable}


def act_opening(world: World) -> None:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    world.say(OPENINGS[params.opening_style].format(hero=params.hero))
    world.say(
        f"In {world.setting}, {params.hero} {scenario.plan} while "
        f"{params.helper} arranged cups and {params.neighbor} warmed the room with a hello."
    )


def act_trouble(world: World) -> None:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    table = world.get("table")
    bowl = world.get("bowl")
    helper = world.get("helper")
    table.meters["stable"] = 0.0
    bowl.meters["moving"] = 1.0
    helper.memes["worry"] = 1.0
    world.say(f"Then {scenario.trouble}.")
    world.say(JOKES[params.joke_style])
    world.say(f'"I can catch it!" said {helper.label}.')
    world.say(f'"Wait," said {params.hero}. "Let us see why it is moving."')
    world.facts["dialogue_changed"] = True


def act_sense(world: World) -> None:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    hero = world.get("hero")
    table = world.get("table")
    world.say(REPAIRS[params.repair_style])
    world.say(f"{params.hero} {scenario.clue}.")
    world.say(
        f'That changed the plan. "{scenario.need.capitalize()}," '
        f'{params.hero} told {params.helper}.'
    )
    world.say(f'"So the table is the problem, not the bowl?" asked {params.helper}.')
    world.say(
        f'"Exactly," said {params.hero}. "Good sense can make a smooth path out of a silly moment."'
    )
    hero.memes["sense"] = 1.0
    table.meters["stable"] = 0.5
    world.facts["cause_found"] = True


def act_repair(world: World) -> None:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    table = world.get("table")
    bowl = world.get("bowl")
    helper = world.get("helper")
    world.say(f"Together, they {scenario.repair}.")
    world.say(f'"{scenario.invitation}," said {params.hero}.')
    world.say(f'"I can do the steady part," said {helper.label}.')
    world.say(f"{helper.label} {scenario.helpful_action}.")
    table.meters["smooth"] = 1.0
    table.meters["stable"] = 1.0
    bowl.meters["moving"] = 0.0
    bowl.meters["safe"] = 1.0
    bowl.location = "steady middle of the table"
    helper.memes["worry"] = 0.0
    helper.memes["pride"] = 1.0
    world.facts["repair_done"] = True


def act_resolution(world: World) -> None:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    neighbor = world.get("neighbor")
    neighbor.memes["joy"] = 1.0
    world.say(
        f"{params.neighbor} carried the {scenario.food} to the steady table, "
        f"and everyone made room without bumping elbows."
    )
    world.say(f'"That was a smooth save," said {params.neighbor}.')
    world.say(
        f'"A sensible save," corrected {params.hero}, and {params.helper} made the joke even sillier by saluting the table.'
    )
    world.say(scenario.ending)
    world.say(scenario.lesson)
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_opening(world)
    world.para()
    act_trouble(world)
    act_sense(world)
    act_repair(world)
    world.para()
    act_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write a child-friendly slice-of-life story about {params.hero} preparing {scenario.food} in {world.setting}.",
        f"Show how {params.hero} uses good sense to discover the cause behind a funny breakfast problem.",
        f"Include smooth, kind humor and a brief dialogue between {params.hero} and {params.helper}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        QAItem(
            question=f"What was {params.hero} preparing in {world.setting}?",
            answer=f"{params.hero} was preparing {scenario.food}: {scenario.plan}.",
        ),
        QAItem(
            question=f"What trouble happened during the breakfast?",
            answer=f"{scenario.trouble.capitalize()}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} understand the problem?",
            answer=f"{params.hero} {scenario.clue}. That clue showed that the trouble came from the serving setup rather than from the food.",
        ),
        QAItem(
            question=f"How did the conversation change what {params.helper} did?",
            answer=f"{params.hero} asked {params.helper} to look for the cause instead of rushing to catch the bowl, so {params.helper} helped steady the table.",
        ),
        QAItem(
            question="How was the breakfast problem repaired?",
            answer=f"Together, they {scenario.repair}. Then the bowl stayed safely in the smooth, steady middle of the table.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"{scenario.ending} The neighbors shared breakfast after the repair.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does smooth mean in this story world?",
            answer="Smooth can describe a surface without bumps, or a calm process that moves without sudden trouble.",
        ),
        QAItem(
            question="What does good sense mean?",
            answer="Good sense means noticing important facts, thinking about safety, and choosing a practical response.",
        ),
        QAItem(
            question="How can humor help?",
            answer="Kind humor can help people relax and notice a problem, but it should not hide danger or make fun of someone who needs help.",
        ),
        QAItem(
            question="What is a slice-of-life story?",
            answer="A slice-of-life story follows an ordinary moment and shows why that small moment matters.",
        ),
        QAItem(
            question="Why did the characters talk before repairing the trouble?",
            answer="They talked so they could understand the cause, avoid a rushed mistake, and choose a safe repair together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        if entity.location:
            details.append(f"location={entity.location}")
        lines.append(f"{entity.id}: {entity.label} ({entity.type}) {' '.join(details)}")
    lines.append(f"facts: {world.facts['cause_found']=}, {world.facts['repair_done']=}, {world.facts['resolved']=}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        setting="apartment courtyard",
        hero="Luna",
        helper="Pip",
        neighbor="Mr. Vale",
        recipe="pancakes",
        opening_style=0,
        joke_style=1,
        repair_style=2,
    ),
    StoryParams(
        setting="community room",
        hero="Mara",
        helper="Jo",
        neighbor="Inez",
        recipe="fruit salad",
        opening_style=1,
        joke_style=4,
        repair_style=0,
    ),
    StoryParams(
        setting="front porch",
        hero="Suri",
        helper="Milo",
        neighbor="Auntie June",
        recipe="muffins",
        opening_style=2,
        joke_style=2,
        repair_style=3,
    ),
    StoryParams(
        setting="small park",
        hero="Tess",
        helper="Bea",
        neighbor="Theo",
        recipe="oatmeal",
        opening_style=3,
        joke_style=5,
        repair_style=1,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        try:
            result = asp_verify()
        except ImportError:
            print("ASP verification requires clingo.")
            result = 1
        if result == 0:
            for params in CURATED:
                try:
                    sample = generate(params)
                except StoryError as exc:
                    print(f"Generated story failed: {exc}")
                    result = 1
                    break
                if not sample.story.strip() or len(sample.story_qa) < 3:
                    print("Generated story failed basic content checks.")
                    result = 1
                    break
                if '"' not in sample.story:
                    print("Generated story failed dialogue check.")
                    result = 1
                    break
            if result == 0:
                print("OK: generated stories passed story checks.")
        sys.exit(result)

    if args.asp:
        try:
            values = asp_valid()
        except ImportError:
            print("ASP mode requires clingo.")
            return
        print("Compatible ASP story settings:")
        for value in values:
            print(f"  {value[0]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for params in CURATED:
            params.seed = base_seed
            samples.append(generate(params))
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n:
            seed = base_seed + attempt
            attempt += 1
            if attempt > max(100, args.n * 50):
                raise StoryError("Could not generate enough distinct stories.")
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
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
            params = sample.params
            header = f"### {params.hero} / {params.helper} / {params.recipe} in {params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
