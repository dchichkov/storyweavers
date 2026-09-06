#!/usr/bin/env python3
"""
A small bedtime-story world set in a storm drain, with humor and a brief
flashback. A child or small creature wants to use a laser toy near a hidden
yam in the drain, learns a gentle lesson, and ends with a cozy resolution.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    companion: str
    prize: str
    setting: str = "storm drain"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.flashback_used = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


NAMES = ["Milo", "Pia", "Nora", "Otto", "Luna", "Ivy", "Finn", "June"]
COMPANIONS = ["mouse", "cat", "sparrow", "puppy", "frog"]
PRIZES = ["yam", "sweet yam", "tiny yam", "golden yam"]

SETTINGS = {
    "storm drain": {
        "place_fact": "storm_drain",
        "has_water": True,
        "echo": True,
        "safe_end": True,
    }
}

SCENARIOS = [
    {
        "key": "leaf_jam",
        "premise": "a curbside garden cart had tipped, and one yam rolled beside a leaf-clogged grate",
        "problem": "Rain began pooling because the leaves covered the drain slots",
        "mistake": "At first, {name} tried to point out every leaf with the laser, but the dancing dot only made the {companion} chase shadows",
        "memory": "that afternoon, a crossing guard had said that a tool helps only when it makes the next safe step clearer",
        "clue": "a dry crescent around one slot showed where water still slipped through",
        "dialogue": "'The dot can show the dry edge, but our hands stay away from the grate,' {name} said",
        "action": "An adult used a long-handled rake from the sidewalk while {name} held a flashlight and counted the clearing slots",
        "result": "The puddle spiraled down, and the cart owner reclaimed the clean yam instead of treating drain water as a pantry",
        "ending": "A single leaf sailed through the gutter like a tiny green boat while the grate gave a bubbly chuckle",
        "lesson": "good humor can settle a worried team, but a safe plan does the useful work",
    },
    {
        "key": "label_mixup",
        "premise": "a produce-delivery label marked YAM had stuck to the storm-drain sign after a gust",
        "problem": "Neighbors thought the label meant a yam was trapped below and crowded around the curb",
        "mistake": "{name} swept the toy laser across the sign like a detective, which made the letters look even more mysterious",
        "memory": "last week, {name} had mistaken an upside-down lunch label for a secret map until the {companion} nudged it straight",
        "clue": "the label's torn corner matched an empty crate on the garden cart",
        "dialogue": "'It is a traveling sticker, not a drain menu,' {name} said, and everyone chuckled",
        "action": "With the laser switched off, {name} asked an adult to peel up the litter and place it in the bin",
        "result": "The cart owner checked the crate, found every yam accounted for, and thanked the careful investigators",
        "ending": "The clean sign shone under the streetlamp, and the empty crate rattled home on the cart",
        "lesson": "checking ordinary evidence is wiser than making a dramatic guess",
    },
    {
        "key": "echo_count",
        "premise": "a harvest-game yam had bounced from a chalk circle and stopped safely on the pavement beside the storm drain",
        "problem": "A hollow plink below sounded like a second yam falling into the pipe",
        "mistake": "{name} aimed the laser at a cardboard target near the curb and counted each returning echo as another lost vegetable",
        "memory": "during music club, three claps near a wall had sounded like six until the teacher explained echoes",
        "clue": "one gentle tap on the target made the same double plink even though the yam did not move",
        "dialogue": "'One sound went down and one came back,' {name} explained; the {companion} answered with a comic squeak",
        "action": "They moved the game well back from the curb and marked a new throwing line with adult permission",
        "result": "The single clean yam returned to the harvest basket, and no one reached into or entered the drain",
        "ending": "Their final chuckle came back faint and round, then rain softened it into silence",
        "lesson": "a funny echo can be a clue when someone tests it carefully",
    },
    {
        "key": "reflection",
        "premise": "a yam-shaped festival lantern cast a brown reflection into a shallow puddle beside the storm drain",
        "problem": "The {companion} mistook the reflection for food under the grate and crept too close to traffic",
        "mistake": "{name} wiggled a low-power laser dot on a closed practice board, hoping to lure the {companion} back, but the extra motion caused confusion",
        "memory": "earlier, an animal-care volunteer had taught {name} never to shine a laser toward an animal or use one to tease it",
        "clue": "when the lantern swayed left, the puddle-yam swayed left at exactly the same time",
        "dialogue": "'That yam is made of reflected light,' {name} said, turning the laser off",
        "action": "An adult blocked the curb while {name} called the {companion} toward a familiar treat placed far from the road",
        "result": "The animal returned safely, and the lantern was tied where its reflection could not tempt anyone toward the drain",
        "ending": "The real lantern glowed above them while its harmless twin trembled in a flowerpot saucer",
        "lesson": "kindness means changing a clever idea when it unsettles someone else",
    },
    {
        "key": "survey_marks",
        "premise": "a gardener set a prize yam on a bench while volunteers measured rainwater near the storm drain",
        "problem": "Their chalk measurements vanished whenever a new shower crossed the pavement",
        "mistake": "{name} tried using the laser as a lasting mark, then chuckled on realizing light disappears as soon as it is switched off",
        "memory": "at a science table that morning, a beam had shown a point clearly but had left no mark on the paper",
        "clue": "a row of removable blue tabs remained readable above the wet curb",
        "dialogue": "'The laser can point while an adult places a tab, but it cannot save the measurement,' {name} said",
        "action": "From the sidewalk, the team recorded each water line on a clipboard and kept every person away from the opening",
        "result": "The measurements helped the gardener choose a safer rain-barrel spot, and the yam became the winner's supper at home",
        "ending": "Blue tabs made a tiny staircase above the drying gutter as the volunteers shared one last chuckle",
        "lesson": "the right tool depends on whether a clue must merely be shown or carefully recorded",
    },
    {
        "key": "paper_boat",
        "premise": "a paper boat named Yam sailed along the gutter during a supervised rain experiment",
        "problem": "The boat snagged on a twig before the storm drain, carrying its drawn-on smile toward the grate",
        "mistake": "{name} flashed the laser on a wall-mounted target as a pretend lighthouse, but light could not push the boat sideways",
        "memory": "on a previous rainy day, {name} had learned that even shallow moving water can pull harder than it looks",
        "clue": "water curled around the upstream side of each pebble and left a calm pocket behind it",
        "dialogue": "'We stay on dry pavement and redirect the water, not ourselves,' {name} told the {companion}",
        "action": "An adult used a long grabber to lift the boat while {name} placed cones to keep the game far from the drain",
        "result": "The soggy Yam boat was rescued for recycling, and the next boats floated in a tub instead",
        "ending": "In the tub, a new paper boat bobbed beneath a lamp and wore a yam-colored flag",
        "lesson": "pretend adventure is funniest when its boundaries keep everyone safe",
    },
    {
        "key": "mural_shadow",
        "premise": "a mural beside the storm drain showed a heroic yam wearing boots and a purple cape",
        "problem": "A loose branch cast a moving shadow that made the painted yam appear to kick passing feet",
        "mistake": "{name} blamed the mural and challenged it with a laser dot on the blank wall beside it",
        "memory": "at bedtime yesterday, a coat on a chair had looked like a monster until the room light came on",
        "clue": "the yam's painted boot stayed still whenever the wind stopped moving the branch",
        "dialogue": "'The hero is innocent; the branch is doing the dancing,' {name} announced, and the {companion} gave a chuckle-like chirp",
        "action": "They switched off the laser, stepped back from the curb, and asked a park worker to secure the branch",
        "result": "The shadow stopped kicking, and visitors could admire the humorous mural without stumbling",
        "ending": "Moonlight rested on the painted cape, perfectly still above the whispering drain",
        "lesson": "a surprising shadow deserves observation before accusation",
    },
    {
        "key": "recipe_card",
        "premise": "a recipe card for yam soup fluttered from a tote and landed on the dry grate above the storm drain",
        "problem": "Every breeze edged the card closer to a narrow slot",
        "mistake": "{name} used the laser to circle the card's picture from a safe distance, then admitted that pointing was not rescuing",
        "memory": "a librarian had once shown {name} how chasing loose pages can push them farther away",
        "clue": "the card paused whenever the {companion} stood between it and the wind",
        "dialogue": "'Be the windbreak, not the whirlwind,' {name} said with a chuckle",
        "action": "An adult held a flat basket over the card, lifted both together, and returned the recipe without touching the grate",
        "result": "The family cooked their clean yams at home and copied the recipe onto sturdier paper",
        "ending": "Steam drew a soft cloud above the soup while the rescued card dried beneath a cookbook",
        "lesson": "calm teamwork can protect something fragile better than a flashy signal",
    },
    {
        "key": "maintenance_tag",
        "premise": "a maintenance worker hung a yellow tag near the storm drain, beside a lunch bag printed with a smiling yam",
        "problem": "{name} thought the tag was a treasure clue and nearly interrupted the worker's inspection",
        "mistake": "A laser dot on {name}'s own clipboard became a pretend treasure pointer, making the guess feel more certain than it was",
        "memory": "during a museum visit, {name} had learned that work tags are instructions, not decorations or invitations",
        "clue": "the tag said KEEP CLEAR and carried the same number as the worker's safety cone",
        "dialogue": "'The yam is only on the lunch bag; the real message is to give the worker room,' {name} said",
        "action": "They put the laser away, moved behind the cones, and helped remind walkers to use the other side of the path",
        "result": "The worker cleared the inspection safely and later showed them the lunch-bag picture from a comfortable distance",
        "ending": "The cone tops gleamed in the sunset, and the printed yam seemed to chuckle from the departing bag",
        "lesson": "curiosity grows stronger when it respects signs and other people's work",
    },
    {
        "key": "shadow_show",
        "premise": "a neighborhood shadow show used a cardboard yam puppet on a screen set well away from the storm drain",
        "problem": "A gust toppled one screen leg, tilting the show toward the wet curb",
        "mistake": "{name} kept the laser's stage dot moving for one extra joke before noticing the sagging corner",
        "memory": "during rehearsal, the director had said that performers stop the scene whenever scenery becomes unsafe",
        "clue": "the puppet's round shadow stretched longer each time the screen leaned farther",
        "dialogue": "'Pause the chuckle; the stage needs us,' {name} called, switching the laser off",
        "action": "Adults carried the screen to level ground while the children gathered puppets and checked every weighted foot",
        "result": "The show resumed safely, and the yam puppet's rescue joke earned a bigger laugh because the team had earned it",
        "ending": "A crisp yam shadow bowed on the steady screen as rainwater murmured far behind the cones",
        "lesson": "humor can wait while a team fixes a real hazard",
    },
    {
        "key": "glow_sticker",
        "premise": "a glow-in-the-dark yam sticker clung to a rain gauge beside the storm drain",
        "problem": "Its green glow made the {companion} give an alarmed call whenever the gauge filled",
        "mistake": "{name} added a red laser dot to test the reaction, then stopped immediately when the {companion} became more worried",
        "memory": "an earlier flashlight game had taught {name} that animals do not know when a moving light is only a joke",
        "clue": "covering the sticker with a notebook made the {companion} relax even while the rain gauge kept dripping",
        "dialogue": "'Mystery solved, and no more light tricks for our friend,' {name} said",
        "action": "An adult moved the sticker to a bedroom star chart and left the working gauge plainly marked outside",
        "result": "The measurements continued without frightening the animal, and the laser stayed packed away",
        "ending": "That night the little yam glowed among paper stars while the {companion} slept in a round, quiet curl",
        "lesson": "a joke stops being funny when another creature feels afraid",
    },
    {
        "key": "seedling_delivery",
        "premise": "a school garden delivery included one sprouting yam and a route past the storm drain",
        "problem": "A broken wagon wheel left the plant tray wobbling beside the curb as rain approached",
        "mistake": "{name} traced a shortcut on a map with the toy laser, forgetting that the shortest route crossed the slickest pavement",
        "memory": "on the last garden trip, a teacher had praised the longer dry path because roots dislike sudden tumbles",
        "clue": "chalk arrows on the covered walkway remained bright while the curbside arrows had washed away",
        "dialogue": "'The yam needs the dry route, even if our feet take more steps,' {name} said with a relieved chuckle",
        "action": "The group put away the laser, transferred the tray to an adult's sturdy cart, and followed the covered path",
        "result": "The sprouting yam reached its raised bed upright and the damaged wagon went to the repair shed",
        "ending": "One purple-green leaf lifted above fresh soil while raindrops ticked safely on the garden roof",
        "lesson": "a careful detour can bring a small living thing safely home",
    },
]

TELLINGS = [
    ("Just after the rain eased", "The odd moment tugged open a flashback", "By the time the clouds thinned"),
    ("Before the streetlamps blinked on", "A memory returned as clearly as a picture", "When the first star appeared"),
    ("During a silver, drizzly afternoon", "That was when yesterday's lesson came back", "After the last drop fell"),
    ("At the start of a neighborhood walk", "The puzzle reminded {name} of something important", "At the walk's quiet end"),
    ("While gutters made plinking music", "For a moment, the present folded into a flashback", "Once the gutter song softened"),
    ("Under a row of bright umbrellas", "A useful memory interrupted the commotion", "As the umbrellas closed"),
    ("Near the end of a gentle shower", "Then an earlier scene replayed in {name}'s mind", "In the clean-smelling evening"),
    ("As puddles reflected the evening sky", "One clue unlocked a flashback", "When the reflections grew still"),
    ("On a calm walk after supper", "The mystery suddenly rhymed with an older mistake", "Before it was time for bed"),
    ("While a distant drainpipe went plink-plonk", "A flashback supplied the missing piece", "As the last plink faded"),
]

ASP_RULES = r"""
#show valid/1.
#show story_ok/1.

valid(P) :- params(P), setting(P, storm_drain), prize(P, yam), companion(P, _).

story_ok(P) :- valid(P), humored(P), flashback(P), resolved(P).
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime Story world: a humorous flashback in a storm drain.")
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--prize", choices=PRIZES)
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
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    prize = args.prize or rng.choice(PRIZES)
    if "yam" not in prize:
        raise StoryError("This world only tells stories about a yam in the storm drain.")
    return StoryParams(name=name, companion=companion, prize=prize)


def aspire() -> str:
    import asp
    facts = [
        asp.fact("setting", "p1", "storm_drain"),
        asp.fact("prize", "p1", "yam"),
        asp.fact("companion", "p1", "mouse"),
        asp.fact("params", "p1"),
        asp.fact("humored", "p1"),
        asp.fact("flashback", "p1"),
        asp.fact("resolved", "p1"),
        asp.fact("valid", "p1"),
        asp.fact("story_ok", "p1"),
    ]
    return "\n".join(facts) + "\n" + ASP_RULES


def asp_facts() -> str:
    import asp
    lines = []
    for _name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", "p1", setting["place_fact"]))
    lines.append(asp.fact("prize", "p1", "yam"))
    for c in COMPANIONS:
        lines.append(asp.fact("companion", "p1", c))
    lines.append(asp.fact("params", "p1"))
    lines.append(asp.fact("humored", "p1"))
    lines.append(asp.fact("flashback", "p1"))
    lines.append(asp.fact("resolved", "p1"))
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    program = asp_facts() + "\n" + ASP_RULES
    model = asp.one_model(program)
    valid_atoms = set(asp.atoms(model, "valid"))
    story_ok_atoms = set(asp.atoms(model, "story_ok"))
    if ("p1",) in valid_atoms and ("p1",) in story_ok_atoms:
        print("OK: ASP rules produce a valid bedtime story.")
        return 0
    print("Mismatch: ASP rules did not accept the sample story.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    child = world.add(Entity(name=params.name, kind="character", label=params.name))
    companion = world.add(Entity(name=params.companion, kind="creature", label=f"the {params.companion}"))
    yam = world.add(Entity(name="yam", kind="object", label=params.prize))

    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum(ord(ch) for ch in f"{params.name}|{params.companion}|{params.prize}")
    route = stable_seed % (len(SCENARIOS) * len(TELLINGS))
    scenario = SCENARIOS[route % len(SCENARIOS)]
    opening, memory_lead, closing_lead = TELLINGS[route // len(SCENARIOS)]
    values = {
        "name": params.name,
        "companion": params.companion,
        "prize": params.prize,
    }
    detail = {key: value.format(**values) for key, value in scenario.items() if key != "key"}
    opening = opening.format(**values)
    memory_lead = memory_lead.format(**values)
    closing_lead = closing_lead.format(**values)

    child.memes["curious"] = 1.0
    child.memes["humor"] = 1.0
    child.memes["careful"] = 1.0
    yam.meters["safe"] = 1.0
    world.facts["setting"] = "storm drain"
    world.facts["scenario"] = scenario["key"]
    world.facts["problem"] = detail["problem"]
    world.facts["clue"] = detail["clue"]
    world.facts["safe_action"] = detail["action"]
    world.facts["outcome"] = detail["result"]
    world.facts["lesson"] = detail["lesson"]
    world.facts["laser_switched_off"] = True
    world.facts["entered_storm_drain"] = False
    world.facts["humored"] = True
    world.facts["flashback"] = True
    world.facts["resolved"] = True

    world.say(
        f"{opening}, {params.name} and a {params.companion} stopped on the sidewalk near a storm drain. "
        f"There, {detail['premise']}. The sight was so unexpected that {params.name} let out a small chuckle."
    )
    world.say(
        f"The humor did not hide the problem for long. {detail['problem']}. "
        f"{detail['mistake']}."
    )
    world.say(
        f"{memory_lead}: {detail['memory']}. In the flashback, the lesson had seemed ordinary; "
        f"beside the wet curb, it suddenly mattered."
    )
    world.say(
        f"Instead of rushing closer, {params.name} watched from the dry sidewalk. "
        f"The useful clue was this: {detail['clue']}. {detail['dialogue']}."
    )
    world.say(
        f"The toy laser was switched off and kept pointed away from faces and animals. {detail['action']}. "
        f"No child entered the storm drain or reached through its grate."
    )
    world.say(
        f"The plan changed what happened next. {detail['result']}. {params.name} understood that {detail['lesson']}."
    )
    world.say(
        f"{closing_lead}, the danger and the fuss were over. {detail['ending']}. "
        f"That quiet picture, not the laser's bright dot, was the part {params.name} carried into bedtime."
    )

    world.facts.update(
        child=child,
        companion=companion,
        yam=yam,
    )
    story_qa = [
        QAItem(
            question=f"What problem did {params.name} notice near the storm drain?",
            answer=f"The problem {params.name} noticed was this: {detail['problem']}. This made the group pause instead of treating the moment as only a joke.",
        ),
        QAItem(
            question=f"What clue helped {params.name} understand the situation?",
            answer=f"The key clue was that {detail['clue']}. It pointed the team toward the real cause of the problem.",
        ),
        QAItem(
            question=f"What did {params.name} remember in the flashback?",
            answer=f"{params.name} remembered that {detail['memory']}. That memory helped with the choice made in the present.",
        ),
        QAItem(
            question="How did the group act safely around the storm drain and laser?",
            answer=f"They switched off the toy laser and kept it away from faces and animals. {detail['action']}. No child entered the drain or reached through its grate.",
        ),
        QAItem(
            question=f"What changed because of {params.name}'s plan?",
            answer=f"{detail['result']}. The concrete result showed that the careful plan worked.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=f"The story taught that {detail['lesson']}. The ending showed that lesson through what the group chose to do.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a storm drain?",
            answer="A storm drain is a street opening that helps rainwater flow away so puddles do not stay everywhere.",
        ),
        QAItem(
            question="How should a toy laser be used safely?",
            answer="A toy laser should be used only with adult permission and pointed at a safe target, never at eyes, faces, animals, vehicles, or aircraft.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short part of the story that shows something that happened earlier.",
        ),
        QAItem(
            question="Why can humor help at bedtime?",
            answer="Humor can help at bedtime because a small laugh can make a child feel calm and safe before sleep.",
        ),
    ]
    prompts = [
        f"Write a gentle story in which {params.name} solves the {scenario['key'].replace('_', ' ')} problem near a storm drain.",
        f"Tell a child-safe story about {params.name}, a {params.companion}, a {params.prize}, and a toy laser that gets switched off.",
        "Tell a humorous story with a useful flashback, a cause-and-effect solution, and a calm final image.",
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.name}: kind={e.kind}, meters={e.meters}, memes={e.memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(aspire())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_facts() + "\n" + ASP_RULES)
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Milo", companion="mouse", prize="yam"),
            StoryParams(name="Luna", companion="frog", prize="tiny yam"),
            StoryParams(name="Pia", companion="cat", prize="sweet yam"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
