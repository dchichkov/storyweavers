#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    label: str
    features: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    label: str
    route: str
    object_label: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


SETTINGS = {
    "hill_village": Setting(
        "hill_village",
        "the hill village",
        {"headed", "happy_ending", "problem_solving", "curiosity", "folk_tale"},
    )
}

ACTIVITIES = {
    "deliver_bread": Activity(
        "deliver_bread",
        "carry warm bread to the old mill",
        "the crooked road over the hill",
        "a basket of warm bread",
    ),
    "find_lost_bell": Activity(
        "find_lost_bell",
        "seek the bell beneath the hill",
        "the path beside the whispering brook",
        "the village bell",
    ),
    "guide_goats_home": Activity(
        "guide the goats home",
        "the bramble lane around the hill",
        "a little herd of goats",
    ),
}

HEROES = [
    ("Luna", "girl"),
    ("Mara", "girl"),
    ("Tomas", "boy"),
    ("Niko", "boy"),
    ("Pia", "child"),
]

TRAITS = ["curious", "patient", "clever", "kind", "brave"]

SCENARIOS = {
    "mistaken_sign": {
        "opening": "One bright morning, Luna was headed along the crooked road when she found two wooden signs pointing in opposite directions.",
        "problem": "The first sign promised a short road, but its arrow had turned toward a thorny ravine.",
        "clue": "Luna noticed fresh wheel marks leading to the brook, while no marks crossed the ravine.",
        "plan": "She wanted to follow the short sign at once.",
        "turn": "Then curiosity made her ask an old shepherd what he had seen.",
        "helper": "The shepherd showed her that the brook path was safe and that the wind had twisted the sign during the night.",
        "solution": "Luna and the shepherd set the sign upright, tied it with a strong cord, and marked the safe road with smooth white stones.",
        "proof": "Soon every traveler could see the arrow pointing safely toward the mill.",
        "ending": "Luna reached the old mill with the bread still warm, and the miller shared a golden loaf with everyone.",
        "lesson": "A curious question can turn a puzzling road into a wise choice.",
    },
    "blocked_bridge": {
        "opening": "At sunrise, Luna was headed toward the market when she found the little bridge covered by fallen branches.",
        "problem": "The market road was blocked, and the river below was too quick for anyone to wade across.",
        "clue": "Luna saw that the branches had fallen from one cracked tree, while the stones upstream made a dry crossing.",
        "plan": "She first tried to pull the largest branch away by herself.",
        "turn": "When the branch did not move, she stopped and studied the river instead of tugging harder.",
        "helper": "A carpenter came with a rope, and Luna showed him the dry stones and the cracked tree.",
        "solution": "Together they looped the rope around the branches, moved them away from the bridge, and placed a warning rail beside the cracked tree.",
        "proof": "The bridge stood clear, and the warning rail kept children away from the weak trunk.",
        "ending": "Luna reached the market, where the thankful baker gave her a honey cake shaped like a bridge.",
        "lesson": "Good problem solving begins when rushing gives way to looking closely.",
    },
    "missing_lantern": {
        "opening": "One evening, Luna was headed home from the far pasture when the village lantern vanished from its post.",
        "problem": "Without the lantern, travelers could miss the narrow turn and wander into the dark marsh.",
        "clue": "A trail of tiny wax drops led away from the post and ended near the bell tower.",
        "plan": "Luna thought the wind had carried the lantern straight into the marsh.",
        "turn": "Curiosity led her to follow the wax drops before making a guess.",
        "helper": "The bell keeper helped her search the tower steps, where a loose rope had caught the lantern.",
        "solution": "They freed the lantern, trimmed its bent hook, and hung it from a lower, steadier peg.",
        "proof": "Its warm light shone across the narrow turn and reached the first marsh stones.",
        "ending": "Luna headed home beneath the golden glow, while the bell keeper rang once to celebrate the safe return.",
        "lesson": "Small clues can guide a careful heart toward a happy ending.",
    },
    "goat_gate": {
        "opening": "At noon, Luna was headed toward the upper pasture when she found the gate open and three goats missing.",
        "problem": "The goats had wandered toward the steep hillside, where loose stones could slide beneath their hooves.",
        "clue": "Luna heard faint bells below and saw chewed clover beside a narrow path.",
        "plan": "She nearly chased the goats downhill.",
        "turn": "Instead, she wondered why the goats had chosen that path and followed the clover trail from a safe distance.",
        "helper": "The goatherd arrived, and Luna told him about the bells, the clover, and the loose stones.",
        "solution": "They placed fresh clover near the broad path, called softly, and closed the gate with a new wooden peg.",
        "proof": "The goats followed the safe food trail back to the pasture without one stone slipping.",
        "ending": "The goatherd thanked Luna with a warm cup of milk, and the goats slept peacefully beside the fence.",
        "lesson": "Understanding a problem can be kinder and safer than chasing it.",
    },
}

TELLINGS = ["clue_first", "dialogue_first", "quiet_folk", "question_turn"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    hero_type: str
    trait: str
    scenario: str
    telling: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk-tale storyworld about a headed journey, curiosity, and problem solving."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--activity", choices=ACTIVITIES)
    parser.add_argument("--name")
    parser.add_argument("--hero-type", choices=["boy", "girl", "child"])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--scenario", choices=SCENARIOS)
    parser.add_argument("--telling", choices=TELLINGS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "hill_village":
        raise StoryError("This folk tale takes place only in the hill village.")
    name, hero_type = rng.choice(HEROES)
    if args.name:
        name = args.name
        for known_name, known_type in HEROES:
            if known_name == args.name:
                hero_type = known_type
                break
    if args.hero_type:
        hero_type = args.hero_type
    return StoryParams(
        place="hill_village",
        activity=args.activity or rng.choice(sorted(ACTIVITIES)),
        name=name,
        hero_type=hero_type,
        trait=args.trait or rng.choice(TRAITS),
        scenario=args.scenario or rng.choice(sorted(SCENARIOS)),
        telling=args.telling or rng.choice(TELLINGS),
    )


def tell(params: StoryParams, rng: random.Random) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    scenario = SCENARIOS[params.scenario]
    world = World(setting)

    hero = world.add(
        Entity(
            params.name,
            "character",
            params.hero_type,
            params.name,
            meters={"distance": 0.0, "confidence": 0.0},
            memes={"curiosity": 1.0, "problem_solving": 0.0},
        )
    )
    journey = world.add(
        Entity(
            "journey",
            "thing",
            "journey",
            activity.label,
            meters={"hazard": 1.0, "progress": 0.0},
            memes={},
        )
    )

    openings = [
        "Long ago, when the hills were green and the evenings smelled of woodsmoke,",
        "In a small village tucked beneath three round hills,",
        "Once, in the days when paths were marked with stones,",
        "Near a village where every neighbor knew every bell,",
    ]
    world.say(f"{rng.choice(openings)} {scenario['opening']}")
    world.say(
        f"{hero.id} was a {params.trait} {params.hero_type}, and the goal was to {activity.label}."
    )
    world.para()

    if params.telling == "clue_first":
        world.say(scenario["problem"])
        world.say(scenario["clue"])
    elif params.telling == "question_turn":
        world.say(scenario["problem"])
        world.say(f'"Why did this happen?" {hero.id} asked.')
        world.say(scenario["clue"])
    else:
        world.say(scenario["problem"])
        world.say(scenario["plan"])
        world.say(scenario["clue"])

    hero.meters["distance"] = 1.0
    journey.meters["progress"] = 0.25
    world.facts["problem_seen"] = True
    world.say(f'"What should I do?" {hero.id} asked.')
    world.say(f'"Tell me what you noticed first," said a nearby helper.')
    world.say(f'"I noticed that {scenario["clue"][0].lower() + scenario["clue"][1:]}" replied {hero.id}.')
    world.say("The helper listened, because a good answer often begins with a good question.")
    world.para()

    world.say(scenario["plan"])
    world.say(scenario["turn"])
    world.facts["clue_used"] = True
    world.say(f'"Let us test the safe idea before we hurry," said the helper.')
    world.say(f'"Yes. I can look, think, and try one careful step," said {hero.id}.')
    world.say(scenario["helper"])
    hero.memes["problem_solving"] = 1.0
    hero.meters["confidence"] = 1.0
    journey.meters["progress"] = 0.6
    world.para()

    world.say(scenario["solution"])
    journey.meters["hazard"] = 0.0
    journey.meters["progress"] = 1.0
    world.facts["resolved"] = True
    world.say(scenario["proof"])
    world.para()

    world.say(scenario["ending"])
    world.say(
        f"{hero.id} smiled, because being headed somewhere mattered, but learning how to get there mattered too."
    )
    world.say(f"The villagers remembered the tale: {scenario['lesson']}")
    world.facts.update(hero=hero, journey=journey, activity=activity, scenario=scenario)
    return world


def generate(params: StoryParams) -> StorySample:
    seed = params.seed if params.seed is not None else sum(ord(c) for c in params.name + params.scenario)
    world = tell(params, random.Random(seed ^ 0xBEEF))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Tell a folk tale about {params.name} headed toward {ACTIVITIES[params.activity].label}.",
            "Include curiosity, a problem-solving turn, helpful dialogue, and a happy ending.",
            "Make a small clue change the hero's first plan.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    scenario = world.facts["scenario"]
    activity = world.facts["activity"]
    return [
        QAItem(
            f"Where was {hero.id} headed?",
            f"{hero.id} was headed to {activity.label}.",
        ),
        QAItem(
            "What problem did the traveler discover?",
            scenario["problem"],
        ),
        QAItem(
            "What clue helped change the first plan?",
            scenario["clue"],
        ),
        QAItem(
            f"How did {hero.id} solve the problem?",
            scenario["solution"],
        ),
        QAItem(
            "How did the story end happily?",
            scenario["ending"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is curiosity?",
            "Curiosity is the wish to notice, ask, and learn more about something.",
        ),
        QAItem(
            "What is problem solving?",
            "Problem solving means understanding a difficulty, considering choices, and trying a safe useful answer.",
        ),
        QAItem(
            "What does headed mean?",
            "Headed means traveling or going toward a place.",
        ),
        QAItem(
            "Why can a clue be useful?",
            "A clue can reveal what caused a problem and help someone choose a better action.",
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
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) meters={meters} memes={memes}"
        )
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_choice(H) :- curious(H), clue_used(H), problem_solved(H).
happy_ending(H) :- safe_choice(H), journey_complete(H).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "hill_village"),
            asp.fact("headed", "journey"),
            asp.fact("curious", "hero"),
            asp.fact("clue_used", "hero"),
            asp.fact("problem_solved", "hero"),
            asp.fact("journey_complete", "hero"),
            asp.fact("folk_tale", "hill_village"),
        ]
    )


def asp_program(show: str = "#show happy_ending/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        model = asp.one_model(asp_program())
        endings = asp.atoms(model, "happy_ending")
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if endings != [("hero",)]:
        print(f"MISMATCH: ASP produced {endings!r}.")
        return 1
    params = StoryParams(
        "hill_village",
        "deliver_bread",
        "Luna",
        "girl",
        "curious",
        "mistaken_sign",
        "clue_first",
        7,
    )
    sample = generate(params)
    required = ["headed", "curiosity", "problem", "happy", "said"]
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story lacks required narrative elements.")
        return 1
    print("OK: Python and ASP agree on a curious problem-solving happy ending.")
    return 0


CURATED = [
    StoryParams("hill_village", "deliver_bread", "Luna", "girl", "curious", "mistaken_sign", "clue_first", 11),
    StoryParams("hill_village", "find_lost_bell", "Mara", "girl", "patient", "missing_lantern", "dialogue_first", 29),
    StoryParams("hill_village", "guide_goats_home", "Tomas", "boy", "clever", "goat_gate", "quiet_folk", 43),
    StoryParams("hill_village", "deliver_bread", "Pia", "child", "brave", "blocked_bridge", "question_turn", 61),
]


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

    if args.verify:
        raise SystemExit(asp_verify())

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        try:
            import asp

            model = asp.one_model(asp_program())
            print("ASP happy endings:", asp.atoms(model, "happy_ending"))
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        for index in range(args.n):
            seed = base_seed + index
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
