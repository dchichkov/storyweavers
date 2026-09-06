#!/usr/bin/env python3
"""Dialogue-rich slice-of-life StoryWorld about a cold warehouse aisle."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("wet", "mess", "cold", "order", "risk"):
            self.meters.setdefault(key, 0.0)
        for key in ("calm", "worry", "joy", "surprise", "trust"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Aisle:
    place: str = "warehouse aisle"
    has_freezer_cart: bool = True
    has_break_table: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    lunch: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    task: str
    warning: str
    guess: str
    clue: str
    test: str
    cause: str
    action: str
    repair: str
    result: str
    lesson: str
    ending: str


INCIDENTS = [
    Incident("silver drip marks", "matching soup labels to insulated crates", "three silver drops below an icicle on the freezer canopy", "the lunch container leaked", "the linguine bag was dry but the drops were icy", "compared the dry bag with the trail from beyond the yellow line", "warm air from a loading-door check loosened canopy frost", "coned off the aisle and called the facilities lead", "dried the floor after the lead removed the ice from a platform lift", "a delivery waited two minutes, but nobody slipped and no food was spoiled", "A small delay is better than a guess beneath overhead ice", "the last drop shone in a catch tray while steam curled from two bowls"),
    Incident("humming freezer cart", "counting napkins for packing tables", "an icicle trembling whenever a freezer cart hummed", "a loose wheel needed tightening", "the wheel stayed still while a compressor light blinked amber", "logged each hum and blink from the protected aisle end", "a worn rubber mount carried compressor vibration into the canopy", "redirected coworkers and radioed maintenance", "waited while maintenance replaced the mount and safely cleared the ice", "the napkin count finished elsewhere and the cart returned quietly", "Patterns are evidence, but trained people repair machinery", "the amber light turned green as forks twirled quiet ribbons of pasta"),
    Incident("tilted book carton", "checking picture books for a reading room", "a narrow carton leaning near a small overhead icicle", "they should straighten the top carton quickly", "a crushed corner showed that the bottom carton had softened", "read the stack label outside the taped boundary", "a damp lower carton could no longer support the stack", "closed the route and showed the label to the stock supervisor", "let the stock team unload from the stable side after facilities cleared the ice", "every book stayed dry, although lunch began a little later", "Understand what supports a stack before touching it", "the straight cartons cast square shadows beside a bright bookmark"),
    Incident("missing route card", "routing donated art paper", "an icicle warning closing the shortest aisle as a route card vanished", "someone forgot to return the card", "a blue corner showed beneath the clear detour sign", "asked the marshal to inspect it after the overhead check", "the card slid under the sign when both were placed on one desk", "used the posted detour and waited outside the closure", "clipped the recovered card into a holder and made a backup", "the paper arrived by the longer route with every sheet flat", "Coinciding events may be a mix-up rather than a mystery", "the blue card clicked into place beside tomato-bright sauce"),
    Incident("chilly barcode", "scanning garden-club seed cartons", "a scanner failing beside a canopy icicle", "cold air had frozen the scanner", "its battery was full but clear tape wrinkled over each barcode", "scanned a printed backup code at a safe dry desk", "glare from wrinkled tape hid the bars", "reported the ice and kept the freezer aisle closed", "reprinted the labels while facilities handled the overhead ice", "the right seeds shipped and the scanner needed no repair", "Test a safe explanation before blaming the nearest odd thing", "seed names glowed on the screen beside covered lemon linguine"),
    Incident("echoing clink", "sorting reusable school lunch trays", "a sharp clink near a hanging icicle", "the icicle had fallen behind the cart", "the ice remained overhead and the clink returned with the fan", "timed the sounds against the fan light from behind cones", "moving air made a loose tray divider tap its rack", "reported both hazards and waited for facilities", "had the stock lead secure the divider after the ice was cleared", "the strange sound stopped and every tray reached the school", "A sound suggests a clue without proving its cause", "the silent rack stood firm as forks made a friendlier clink"),
    Incident("fogged cabinet", "checking yogurt cartons in a cold cabinet", "an icicle above a suddenly cloudy window", "the freezer was failing", "the temperature display stayed steady and fog covered only the outside", "read the remote temperature log without opening the cabinet", "humid cleaning air condensed on cold outer glass", "closed the icy area and called facilities and food-safety staff", "let staff clear the ice, dry the glass, and verify the log", "the yogurt stayed cold and needless waste was avoided", "Reliable records can calm worry better than a hurried assumption", "the clear window revealed tidy cartons beside divided linguine"),
    Incident("red mitten", "locating winter-clothing donation boxes", "a red mitten beside cones guarding an icicle", "a child visitor had crossed the boundary", "the mitten bore a staff laundry tag", "called the desk to account for visitors while staying outside", "a staff mitten fell while the cones were placed", "kept the route shut and asked the supervisor for help", "paired the mitten after facilities removed the ice", "the donation van left complete and everyone was accounted for", "Take a worrying clue seriously, then verify its meaning", "the paired mittens topped the last box beside warm linguine"),
    Incident("double delivery bell", "preparing blankets for a shelter", "the bell ringing twice as icicle meltwater reached a catch tray", "two trucks had arrived together", "the board listed one truck and the second ring matched a radio alert", "confirmed the driver by radio behind the barrier", "the desk radio happened to share the loading bell's tone", "sent the driver to another supervised door", "changed the radio tone after facilities cleared the canopy", "the blankets loaded on time without crowding the closed route", "Two sounds that coincide need not be two events", "the cart rolled under a green light while parmesan softened"),
    Incident("wandering label", "matching wooden puzzles to shelf tickets", "a label fluttering toward an icicle-marked aisle", "they had to catch it before it vanished", "its magnetic back caught the metal cone sign", "read its number safely and checked the inventory tablet", "a crowded clipboard bent the label until moving air lifted it", "waited for the marshal instead of chasing it", "flattened it in a holder after the aisle was declared clear", "the puzzles were shelved correctly without anyone crossing the line", "No label is worth entering a closed hazard area", "bright puzzle pieces showed through a window beside basil-flecked pasta"),
    Incident("stopped clock", "checking a library pallet pickup", "the clock stopping when an icicle alarm sounded", "the alarm cut power to the aisle", "lights stayed on while the second hand quivered", "compared the clock with the dispatch tablet behind the barrier", "the clock battery died during an unrelated alarm", "followed the alarm route and redirected the pallet", "replaced the battery after facilities reopened the aisle", "the pallet met pickup because the tablet kept correct time", "Events that coincide do not always share a cause", "the clock ticked past noon as the last noodle curled around a fork"),
    Incident("paper snowflake", "packing after-school craft kits", "a white shape drifting from a shelf during an icicle inspection", "a chip of ice had blown past the cones", "the shape did not melt and had six scissor cuts", "viewed it through the aisle camera during the overhead check", "an unsealed envelope released a paper snowflake", "treated it as ice until the facilities lead confirmed safety", "resealed the kits after the real icicle was removed", "every kit kept its shapes and caution cost less than a minute", "Caution first and curiosity second can work together", "a paper snowflake decorated the desk beside two empty bowls"),
]


@dataclass(frozen=True)
class Route:
    opening: str
    turn: str
    reflection: str


ROUTES = [
    Route("Two clocks offered the same break time.", "Lunch became an evidence puzzle before either lid opened.", "An ordinary shift had taught careful thinking without becoming a grand adventure."),
    Route("Warm pasta and a cold warning sign shared one unlikely morning.", "Lunch could wait; the clue deserved a careful look.", "Patience, not luck, had kept the small problem small."),
    Route("At first the aisle held only wheels, labels, and the smell of lunch.", "Then one detail refused to fit their first explanation.", "They saved that detail in the handover note for the next team."),
    Route("A warehouse tells stories in tiny sounds and marks.", "They compared what they could observe instead of filling silence with guesses.", "The modest answer made their shared meal memorable."),
    Route("The break table was close, but the safe route to it was changing.", "They traded impatience for questions and treated the boundary as part of the solution.", "The detour became a useful story about noticing before acting."),
    Route("Neither worker expected linguine to enter the safety log.", "Their neat first idea gave way when physical evidence pointed elsewhere.", "They laughed at the guess, then recorded the better explanation."),
    Route("Two routine schedules crossed in the coldest aisle.", "What looked like one problem separated into two when they checked the timing.", "That distinction turned worry into a calm plan."),
    Route("The aisle rewarded speed, but its cold bay rewarded care.", "They slowed down, named what they knew, and left risky work to trained hands.", "Nothing dramatic happened, exactly as a good safety decision intended."),
    Route("A coincidence gave the coworkers time together; a clue tested how they used it.", "One question led to another until the shortcut made no sense.", "Their conversation ended with a practical lesson instead of blame."),
    Route("Before noon, the aisle held a lunch-sized mystery.", "They treated it like real work: observe, check, report, resolve.", "The answer was simple enough to discuss between forkfuls."),
]


class World:
    def __init__(self, aisle: Aisle):
        self.aisle = aisle
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


HEROES = ["Mina", "Jules", "Tara", "Nico", "Leah", "Omar"]
FRIENDS = ["Omar", "Ivy", "Sam", "Noah", "Priya", "Lena"]
LUNCHES = ["linguine", "tomato linguine", "buttered linguine", "lemon linguine"]


def _selection(seed: Optional[int]) -> tuple[Incident, Route]:
    value = seed or 0
    return INCIDENTS[value % len(INCIDENTS)], ROUTES[(value // len(INCIDENTS)) % len(ROUTES)]


def tell_story(params: StoryParams) -> World:
    incident, route = _selection(params.seed)
    world = World(Aisle(place=params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type="adult coworker"))
    friend = world.add(Entity(id=params.friend, kind="character", type="adult coworker"))
    lunch = world.add(Entity(id="lunch", type="food", label=params.lunch, owner=hero.id))
    icicle = world.add(Entity(id="icicle", type="overhead ice", label="icicle"))
    hero.memes.update(joy=1.0, worry=1.0)
    friend.memes["surprise"] = 1.0
    icicle.meters.update(cold=1.0, risk=1.0)

    world.say(route.opening)
    world.say(f"In the {params.place}, {hero.id} was {incident.task}. {friend.id} arrived carrying covered {lunch.label}.")
    world.say(f'"Our breaks coincide," {friend.id} said. "We can share this linguine after we finish safely."')
    world.say(f"They then noticed {incident.warning}.")
    world.say(f'"My first guess is that {incident.guess}," {hero.id} said. "But a guess is not permission to cross the cones."')
    world.say(route.turn)
    world.say(f"From the open aisle, they saw that {incident.clue}.")
    world.say(f'"Let us check without going under the icicle," {friend.id} replied. Together they {incident.test}.')
    world.say(f"The evidence showed that {incident.cause}.")
    world.say(f"They {incident.action}. Trained facilities and stock staff handled overhead ice and unstable stock while both coworkers stayed protected.")
    world.say(f"Afterward, they {incident.repair}. As a result, {incident.result}.")
    world.say(f'"{incident.lesson}," {hero.id} said.')
    world.say(route.reflection)
    world.say(f"At the break table, {incident.ending}, and the linguine was still warm.")

    hero.memes.update(worry=0.0, calm=1.0)
    friend.memes["trust"] = 1.0
    icicle.meters["risk"] = 0.0
    world.facts.update(hero=hero, friend=friend, lunch=lunch, icicle=icicle, incident=incident,
                       clue=incident.clue, cause=incident.cause, action=incident.action,
                       result=incident.result, lesson=incident.lesson, resolved=True, child_safe=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    i = f["incident"]
    return [
        'Write a child-safe slice-of-life story set in a warehouse aisle using "coincide," "linguine," and "icicle."',
        f'Tell a dialogue-rich story in which {f["hero"].id} and {f["friend"].id} investigate the incident called "{i.title}" from behind a safety boundary.',
        f"Write an evidence-and-teamwork story whose key clue is that {i.clue}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, friend, lunch, i = f["hero"], f["friend"], f["lunch"], f["incident"]
    return [
        QAItem(f"What were {h.id} and {friend.id} doing when their breaks coincided?", f"{h.id} was {i.task}, and {friend.id} brought {lunch.label}. They planned to share the linguine after making the aisle safe."),
        QAItem(f"What clue changed {h.id}'s first explanation?", f"The clue was that {i.clue}. It pointed them toward a safe test instead of a hurried guess."),
        QAItem(f"What caused {i.title}?", f"They discovered that {i.cause}. The clue and test established the cause, not timing alone."),
        QAItem("How did the coworkers respond to the icicle hazard?", f"They {i.action}. They stayed behind the boundary while trained facilities and stock staff handled overhead ice and unstable stock."),
        QAItem(f"What changed because {h.id} and {friend.id} acted carefully?", f"{i.result.capitalize()}. They also learned that {i.lesson.lower()}.")
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a warehouse aisle?", "A warehouse aisle is a marked route between storage areas. Workers keep it clear and obey closures so people and carts can move safely."),
        QAItem("What is linguine?", "Linguine is a long, flat pasta. Here it is covered and eaten at a break table away from warehouse work."),
        QAItem("Why stay away from a hanging icicle?", "An icicle can fall without warning. People should keep back, report it, and let trained adults remove overhead ice with proper equipment."),
        QAItem("What does coincide mean?", "To coincide means to happen at the same time. Coinciding events do not necessarily cause one another."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *sample.prompts, "", "== story questions =="]
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines += ["", "== world questions =="]
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: kind={entity.kind} type={entity.type} meters={meters} memes={memes}")
    lines.append(f'incident: {world.facts["incident"].title}')
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life warehouse aisle storyworld.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = rng.choice(HEROES)
    return StoryParams(place="warehouse aisle", hero=hero,
                       friend=rng.choice([name for name in FRIENDS if name != hero]),
                       lunch=rng.choice(LUNCHES))


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


ASP_RULES = """place(warehouse_aisle).\ntheme(coincide).\ntheme(linguine).\ntheme(icicle).\nstyle(slice_of_life).\nfeature(dialogue).\nsafe_route :- place(warehouse_aisle), theme(icicle)."""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", "warehouse_aisle"), asp.fact("theme", "coincide"),
                      asp.fact("theme", "linguine"), asp.fact("theme", "icicle"),
                      asp.fact("feature", "dialogue"), asp.fact("style", "slice_of_life")])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    source = asp_program("#show safe_route/0.")
    return 0 if all(x in source for x in ("place(warehouse_aisle).", "theme(icicle).", "safe_route")) else 1


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.show_asp or args.asp:
        print(asp_program("#show place/1.\n#show safe_route/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.all:
        samples = [
            generate(StoryParams(place="warehouse aisle", hero="Mina", friend="Omar", lunch="linguine", seed=0)),
            generate(StoryParams(place="warehouse aisle", hero="Tara", friend="Lena", lunch="buttered linguine", seed=11)),
        ]
    else:
        samples = []
        for offset in range(args.n):
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa,
             header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
