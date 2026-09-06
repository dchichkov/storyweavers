#!/usr/bin/env python3
"""A child-facing animal mystery about a coop, an architect, and Pappy."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Creature:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str = "coop"
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Mystery:
    clue: str
    answer: str
    solved: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    coop_name: str = "sunny coop"
    architect_name: str = "Milo"
    architect_species: str = "owl"
    pappy_name: str = "Pappy"
    pappy_species: str = "goat"
    mystery_clue: str = "a missing latch"
    mystery_answer: str = "the wind had pushed the gate open"
    case: str = "gate_latch"
    route: str = "clue_first"


@dataclass(frozen=True)
class MysteryCase:
    missing_or_wrong: str
    worry: str
    first_test: str
    failed_reason: str
    decisive_clue: str
    cause: str
    brave_action: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    coop: Place
    architect: Creature
    pappy: Creature
    mystery: Mystery
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


COOPS = {
    "sunny coop": Place(name="the sunny coop"),
    "red coop": Place(name="the red coop"),
    "hill coop": Place(name="the hill coop"),
}
ARCHITECTS = [("Milo", "owl"), ("Nina", "beaver"), ("Tess", "sparrow")]
PAPPYS = [("Pappy", "goat"), ("Pappy", "dog"), ("Pappy", "horse")]

# Pappy is an affectionate name for the coop's older caretaker, not a stereotype
# or an assumption about anyone's family relationship.
CASES = {
    "gate_latch": MysteryCase(
        "the gate latch had vanished", "the youngest chicks could wander toward the lane",
        "compared the screw holes with the spare latch in the plan chest",
        "the holes were intact, so nobody had unscrewed the latch",
        "a crescent scratch climbed from the gate to the rain barrel",
        "a wind-tugged bucket cord had lifted the latch and dropped it behind the barrel",
        "stood where the gate blocked the wind and used a mirror to look behind the barrel",
        "retrieved the latch with a long hook, added a retaining pin, and tested the closed gate",
        "bravery can mean staying near a safe boundary while evidence is checked",
        "the pinned latch shone above a row of chicks asleep behind the secure gate"),
    "crooked_beam": MysteryCase(
        "a roof beam looked crooked", "the coop roof might sag before the afternoon rain",
        "measured both ends from the floor with a marked paper strip",
        "both heights matched, so the beam itself was not leaning",
        "a bent sun-shadow crossed the beam whenever the grapevine moved",
        "a loose vine trellis outside had tilted and cast a crooked shadow through the slats",
        "admitted the shadow had frightened them and asked Pappy to inspect outside",
        "kept everyone indoors while Pappy braced the trellis and the architect rechecked the beam",
        "a careful measurement can separate a frightening appearance from a real danger",
        "a straight gold stripe of sunset lay across the measured beam"),
    "wall_rattle": MysteryCase(
        "a rattle sounded inside the wall", "something might be chewing the coop boards",
        "listened at three marked spots while Pappy tapped the floor once",
        "the sound moved after each tap, unlike an animal hiding in one place",
        "three oat grains rolled from beneath a hollow feed scoop",
        "a scoop left against the wall held loose grain that clicked whenever footsteps shook it",
        "waited through the uneasy silence and repeated the listening test",
        "emptied the scoop into its bin, hung it on a padded peg, and checked the quiet wall",
        "repeating a safe test is braver than pretending not to hear a worrying sound",
        "the padded scoop hung still while one chick pecked the final oat grain"),
    "warm_floor": MysteryCase(
        "one patch of floor felt strangely warm", "hidden heat might hurt the nesting birds",
        "mapped the warm patch with the back of a wooden spoon instead of touching it",
        "the patch cooled when a cloud passed, ruling out a buried heater",
        "a bright triangle entered through a newly polished window",
        "the window was focusing noon sunlight onto one dark floorboard",
        "spoke up about the heat even though the others were preparing a celebration",
        "closed the shade, moved the nest baskets, and added a pale heat-safe floor cover",
        "bravery includes interrupting fun when a quiet hazard needs attention",
        "cool straw covered the board as the window shade fluttered above it"),
    "vanishing_water": MysteryCase(
        "the drinking trough kept losing water", "the birds might have nothing to drink by noon",
        "filled the trough to a chalk line and watched the dry floor beneath it",
        "no drip crossed the chalk dust, so a crack was not the answer",
        "a damp feather trail ended at a low notch in the rim",
        "a tilted perch pressed the rim down whenever several hens landed together",
        "stayed beside the restless flock and counted each change in the water line",
        "leveled the perch, raised the low rim, refilled the trough, and watched it hold",
        "patient observation can reveal a cause that appears only when several events meet",
        "the water line stayed blue and level beneath three peacefully balanced hens"),
    "night_knocks": MysteryCase(
        "three knocks came from the roof each night", "a stranger might be trying to enter the coop",
        "recreated the evening breeze with a hand fan while everyone stayed inside",
        "the roof remained silent, so ordinary wind alone could not explain the knocks",
        "a strand of red kite ribbon appeared only when the weather vane turned east",
        "a lost paper kite in the nearby pear tree tapped the roof at one wind angle",
        "named the fear aloud and helped mark a safe indoor listening station",
        "asked the gardener to remove the kite at daylight and fitted a soft guard to the roof edge",
        "being brave does not require going outside in the dark to prove a guess",
        "moonlight rested on a quiet roof while the rescued kite dried by the garden shed"),
    "cold_nest": MysteryCase(
        "the corner nesting box turned cold", "a draft could chill the smallest eggs",
        "held light ribbons near each seam to show where air moved",
        "none stirred at the wall cracks everyone first suspected",
        "one ribbon lifted beside a round feed-delivery tube",
        "the tube's outer cap had stuck open after a seed husk jammed its hinge",
        "crawled no closer to the machinery and called Pappy before the temperature fell further",
        "closed and cleaned the cap from outside, then lined the nest with fresh dry straw",
        "asking an experienced caretaker for help can be the bravest and smartest action",
        "the ribbons hung still above eggs tucked into a bowl of golden straw"),
    "missing_blueprint": MysteryCase(
        "the architect's safety blueprint was missing", "nobody could check the new perch spacing",
        "searched every flat shelf where a rolled plan might rest",
        "only a narrow strip of blue paper appeared, too small to be the rolled plan",
        "matching blue fibers clung to the wheel of a toy cart",
        "the cart had rolled over the plan and wrapped it neatly around its axle",
        "stopped the hurried building work even when everyone groaned at the delay",
        "unwound the plan, copied it, stored both copies in tubes, and measured every perch",
        "bravery sometimes means pausing a popular plan until it can be made safe",
        "two blueprints rested in labeled tubes above a row of evenly spaced perches"),
    "muddy_prints": MysteryCase(
        "muddy prints appeared beside the feed bins", "a hungry wild animal might be inside",
        "traced the prints backward without stepping across them",
        "they stopped at a solid wall, which no visiting animal could have crossed",
        "each print repeated the flower shape carved under Pappy's watering can",
        "rainwater had carried muddy can-bottom stamps across the floor as the can swung on its hook",
        "protected the birds first, then calmly challenged the rumor about a wild visitor",
        "dried the floor, moved the hook, and set the can in a tray that caught drips",
        "evidence should be used to correct a scary rumor, not merely solve a puzzle",
        "one clean flower stamp remained in the tray beside a floor swept bright"),
    "flickering_lamp": MysteryCase(
        "the safe battery lamp flickered at feeding time", "the flock could panic in sudden darkness",
        "swapped in a tested battery while Pappy kept the birds calm",
        "the flicker continued, proving the battery was not at fault",
        "a tiny glint pulsed where the lamp clip touched a painted support",
        "thick paint prevented the clip from closing fully whenever the feed door moved",
        "kept testing slowly despite each surprising blink and the birds' worried rustle",
        "moved the clip to its proper bracket, secured it, and tested the feed door ten times",
        "courage grows when a mystery is divided into small, safe tests",
        "the steady lamp made a warm circle around ten quiet feeding bowls"),
    "soft_ceiling": MysteryCase(
        "a ceiling panel seemed soft", "rain might have soaked the roof unseen",
        "asked Pappy to press it with an inspection pole while the architect watched from the floor",
        "the moisture card stayed dry, so a roof leak did not fit",
        "pale dust on the pole smelled faintly of clean flour",
        "a flour sack on the loft shelf had puffed powder through a vent and coated the firm panel",
        "resisted climbing up for a closer look and chose the safe floor-level evidence",
        "had Pappy seal the flour sack, vacuum the vent, and confirm the panel was sound",
        "bravery means respecting a height hazard even when curiosity pulls upward",
        "the clean firm panel framed a vent with no white dust drifting from it"),
    "echoing_peeps": MysteryCase(
        "one chick's peep seemed to come from two places", "a chick might be trapped behind a partition",
        "counted every chick before following the second sound",
        "the count was complete, so a hidden chick could not explain the echo",
        "the extra peep grew louder beside a curved metal grain shield",
        "the shield reflected the real chick's call toward the empty storage corner",
        "trusted the complete head count while still checking the troubling sound",
        "added a soft backing behind the shield and repeated the count and call test",
        "bravery can hold worry and reliable evidence at the same time",
        "a single peep answered from beneath the hen while the padded shield stayed silent"),
}

MYSTERIES = [
    ("a missing latch", "the wind had pushed the gate open", "gate_latch"),
    ("a crooked beam", "a tilted trellis had cast a crooked shadow", "crooked_beam"),
    ("a noisy rattle", "loose grain in a scoop was tapping the wall", "wall_rattle"),
    ("a warm floorboard", "focused noon sunlight had heated the dark board", "warm_floor"),
    ("a falling water line", "a tilted perch had pressed down the trough rim", "vanishing_water"),
    ("three roof knocks", "a paper kite was tapping the roof", "night_knocks"),
    ("a cold nesting box", "a feed-tube cap had stuck open", "cold_nest"),
    ("a strip of blue paper", "a toy cart axle had rolled up the blueprint", "missing_blueprint"),
    ("muddy flower-shaped prints", "a swinging watering can had stamped the floor", "muddy_prints"),
    ("a flickering battery lamp", "paint kept the lamp clip from closing", "flickering_lamp"),
    ("a soft-looking ceiling panel", "flour dust had coated a firm dry panel", "soft_ceiling"),
    ("an echoing chick peep", "a curved grain shield had reflected the sound", "echoing_peeps"),
]
ROUTES = (
    "clue_first", "dialogue_first", "plan_first", "night_memory", "countdown",
    "two_theories", "pappy_first", "quiet_first", "ending_first", "question_first",
)


ASP_RULES = r"""
brave(A) :- architect(A), sees_mystery(A), chooses_safe_action(A).
solved(C) :- mystery(C), answer(C, _).
valid_story(C) :- brave(architect), mystery(C), solved(C).
"""


def mystery_id(clue: str) -> str:
    return "case_" + "".join(ch if ch.isalnum() else "_" for ch in clue.lower()).strip("_")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("architect", "architect"),
        asp.fact("sees_mystery", "architect"),
        asp.fact("chooses_safe_action", "architect"),
    ]
    for clue, answer, _ in MYSTERIES:
        cid = mystery_id(clue)
        lines.extend((asp.fact("mystery", cid), asp.fact("answer", cid, answer)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    asp_solved = set(asp.atoms(model, "solved"))
    py_solved = {(mystery_id(clue),) for clue, _, _ in MYSTERIES}
    if asp_solved == py_solved:
        print(f"OK: clingo gate matches python reasoning ({len(py_solved)} mysteries).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(asp_solved))
    print("python:", sorted(py_solved))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(value) for value in (
        params.seed, params.coop_name, params.architect_name, params.architect_species,
        params.pappy_name, params.pappy_species, params.case, params.route,
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.coop_name not in COOPS:
        raise StoryError(f"Unknown coop: {params.coop_name}")
    coop_template = COOPS[params.coop_name]
    return World(
        coop=Place(name=coop_template.name, kind=coop_template.kind),
        architect=Creature(
            name=params.architect_name,
            species=params.architect_species,
            role="architect",
        ),
        pappy=Creature(
            name=params.pappy_name,
            species=params.pappy_species,
            role="older caretaker called Pappy",
        ),
        mystery=Mystery(clue=params.mystery_clue, answer=params.mystery_answer),
    )


def tell_story(world: World, params: StoryParams) -> None:
    a, p, coop, mystery = world.architect, world.pappy, world.coop, world.mystery
    case = CASES[params.case]
    rng = story_rng(params)
    a.memes.update(curiosity=1, bravery=0)
    p.memes.update(warmth=1, patience=1)

    openings = {
        "clue_first": f"{mystery.clue.capitalize()} waited at {coop.name} before breakfast. {a.name} the {a.species}, the coop's architect, knew it might explain why {case.missing_or_wrong}.",
        "dialogue_first": f'"Something is wrong, but we will not guess," {a.name} said at {coop.name}. {case.missing_or_wrong.capitalize()}, and the first clue was {mystery.clue}.',
        "plan_first": f"On a plan of {coop.name}, {a.name} marked the door, roof, nests, and {mystery.clue}. The young {a.species} needed the drawing because {case.missing_or_wrong}.",
        "night_memory": f"Later, {a.name} would remember how quiet {coop.name} became when everyone learned that {case.missing_or_wrong}. At the time, all the architect had was {mystery.clue}.",
        "countdown": f"There was little time before the flock returned to {coop.name}. {case.missing_or_wrong.capitalize()}, and {a.name} found {mystery.clue} while checking the structure.",
        "two_theories": f"Two theories divided {coop.name} after {case.missing_or_wrong}: something had broken, or an ordinary object had moved. {a.name}, a careful {a.species} architect, began between them with {mystery.clue}.",
        "pappy_first": f"Pappy was the affectionate name of {p.name}, the older {p.species} caretaker at {coop.name}. When {case.missing_or_wrong}, Pappy called the architect, {a.name}, to examine {mystery.clue}.",
        "quiet_first": f"The birds grew quiet at {coop.name}. {case.missing_or_wrong.capitalize()}, and near the uneasy flock {a.name} noticed {mystery.clue}.",
        "ending_first": f"By sunset, {case.ending}. That peaceful picture began with a mystery at {coop.name}: {case.missing_or_wrong}, beside {mystery.clue}.",
        "question_first": f'"What could make {mystery.clue} and also explain why {case.missing_or_wrong}?" asked {a.name}, the {a.species} architect of {coop.name}.',
    }
    world.say(openings[params.route])
    world.say(rng.choice([
        f"The clue mattered because {case.worry}.",
        f"Nobody laughed at the worry: {case.worry}.",
        f"Pappy kept the birds away from the clue, for {case.worry}.",
        f"The mystery was more than a puzzle. If ignored, {case.worry}.",
    ]))
    world.say(rng.choice([
        f'"Pappy is simply what everyone calls me," {p.name} said. "My job today is to keep the flock calm while you think."',
        f'{p.name} lowered their voice. "I will mind the birds. You can mind the evidence."',
        f'"An architect checks how things fit and stay safe," {a.name} explained. {p.name} nodded and cleared a working space.',
        f'{a.name} felt afraid of being wrong. {p.name} replied, "Brave does not mean certain. It means careful enough to check."',
    ]))

    world.para()
    world.say(f"First, {a.name} {case.first_test}.")
    world.say(rng.choice([
        f"That idea failed: {case.failed_reason}.",
        f"The result contradicted the easy theory; {case.failed_reason}.",
        f'"Our first answer does not fit," {a.name} admitted, because {case.failed_reason}.',
        f"Instead of hiding the failed test, the architect recorded that {case.failed_reason}.",
    ]))
    world.say(rng.choice([
        f"A second look revealed the decisive clue: {case.decisive_clue}.",
        f"Then Pappy pointed without touching. {case.decisive_clue.capitalize()}.",
        f"They compared the plan with the real coop and noticed that {case.decisive_clue}.",
        f"The frightened guess gave way to evidence when they saw that {case.decisive_clue}.",
    ]))
    world.say(f"It all fit: {case.cause}. That was the fuller explanation behind the report that {mystery.answer}.")

    world.para()
    world.say(rng.choice([
        f"{a.name}'s knees still trembled, but the architect {case.brave_action}.",
        f'"I am worried, and I can still choose the safe next step," {a.name} said, then {case.brave_action}.',
        f"Bravery changed the next action, not the size of the danger: {a.name} {case.brave_action}.",
        f"Rather than performing a daring stunt, {a.name} {case.brave_action}.",
    ]))
    a.memes["bravery"] = 1
    a.meters["tests_completed"] = 2
    world.say(rng.choice([
        f"Working from the architect's plan, they {case.repair}.",
        f"Pappy handled the caretaker's part while {a.name} checked each measurement; together they {case.repair}.",
        f"The solution matched the cause. They {case.repair}.",
        f'"Now fix what the evidence actually showed," Pappy said, and they {case.repair}.',
    ]))
    mystery.solved = True
    p.memes["pride"] = 1
    coop.meters["safety_checked"] = 1

    world.para()
    world.say(rng.choice([
        f"In the mystery notebook, {a.name} wrote: {case.lesson}.",
        f'Pappy offered no magic rhyme, only a true one: "Check what you know; then safely go." {a.name} added the lesson that {case.lesson}.',
        f'"What made that brave?" Pappy asked. {a.name} answered, "{case.lesson.capitalize()}."',
        f"The solved mystery left a useful rule for the next architect: {case.lesson}.",
    ]))
    world.say(rng.choice([
        f"At dusk, {case.ending}.",
        f"When the last measurement was checked, {case.ending}.",
        f"The change could be seen without a speech: {case.ending}.",
        f"Before closing the coop, they looked back. {case.ending.capitalize()}.",
    ]))

    world.facts.update(
        architect=a, pappy=p, coop=coop, mystery=mystery, case=case,
        cause=case.cause, repair=case.repair, lesson=case.lesson,
        ending=case.ending, solved=True, bravery=a.memes["bravery"],
    )


def generation_prompts(world: World) -> list[str]:
    f, case = world.facts, world.facts["case"]
    return [
        f"Write a gentle animal mystery about {f['architect'].name}, the architect of {f['coop'].name}, investigating {f['mystery'].clue}.",
        f"Tell a child-facing story in which an architect and an older caretaker called Pappy discover that {case.cause}.",
        f"Write a bravery mystery set in a coop. Show the characters solving it as follows: they {case.repair}. End on this image: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f, case = world.facts, world.facts["case"]
    a, p, coop, mystery = f["architect"], f["pappy"], f["coop"], f["mystery"]
    return [
        QAItem(
            question=f"What problem did {a.name} investigate after finding {mystery.clue} at {coop.name}?",
            answer=f"{a.name} investigated why {case.missing_or_wrong}. It mattered because {case.worry}."),
        QAItem(
            question=f"Why did {a.name}'s first test fail to solve the mystery?",
            answer=f"{a.name} {case.first_test}. That did not solve it because {case.failed_reason}."),
        QAItem(
            question=f"Which clue allowed {a.name} and {p.name} to discover the real cause?",
            answer=f"They discovered that {case.decisive_clue}. That evidence showed that {case.cause}."),
        QAItem(
            question=f"How did {a.name} show bravery without taking an unsafe risk?",
            answer=f"{a.name} {case.brave_action}. The brave choice kept the investigation within a safe boundary."),
        QAItem(
            question=f"How did the architect and Pappy make {coop.name} safe again?",
            answer=f"They {case.repair}. {a.name} recorded the lesson that {case.lesson}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coop?",
            answer="A coop is a shelter where chickens or other birds can rest and stay protected."),
        QAItem(
            question="What does an architect do?",
            answer="An architect plans and checks how places can be useful, sturdy, and safe."),
        QAItem(
            question="Can asking an experienced adult for help be brave?",
            answer="Yes. Bravery includes naming a worry and choosing qualified help instead of attempting an unsafe action."),
        QAItem(
            question="Why should a mystery solver test an early theory?",
            answer="A first guess can be wrong. A safe test helps separate what merely looks connected from what actually caused the problem."),
        QAItem(
            question="What does Pappy mean in this story world?",
            answer="Pappy is the affectionate name used by the coop's older caretaker. It does not imply a particular family relationship."),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal mystery: coop, architect, Pappy, and bravery.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--coop", choices=sorted(COOPS))
    ap.add_argument("--architect-name")
    ap.add_argument("--pappy-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    coop_name = args.coop or rng.choice(sorted(COOPS))
    architect_name, architect_species = rng.choice(ARCHITECTS)
    pappy_name, pappy_species = rng.choice(PAPPYS)
    clue, answer, case = rng.choice(MYSTERIES)
    return StoryParams(
        seed=args.seed,
        coop_name=coop_name,
        architect_name=args.architect_name or architect_name,
        architect_species=architect_species,
        pappy_name=args.pappy_name or pappy_name,
        pappy_species=pappy_species,
        mystery_clue=clue,
        mystery_answer=answer,
        case=case,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.coop, world.architect, world.pappy):
        lines.append(f"{entity.name}: meters={entity.meters} memes={getattr(entity, 'memes', {})}")
    lines.append(
        f"mystery: clue={world.mystery.clue!r} answer={world.mystery.answer!r} "
        f"solved={world.mystery.solved} cause={world.facts['cause']!r}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    count = 3 if args.all else args.n
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

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
