#!/usr/bin/env python3
"""
A small superhero story world about Alec Proper, repetition, and a happy ending.

Seed tale:
---
Alec Proper was a careful little hero who lived in a bright city with a tall clock tower.
Every morning, he checked his cape, his gloves, and his tiny rescue kit before patrol.
One day, a gust of wind kept knocking the same parcel down the same alley.
Alec tried once, then again, then again. The parcel kept slipping away.
He noticed the alley had a loose drain cover that made the wheel of his cart wobble.
Alec fixed the drain cover, lifted the parcel properly, and carried it to the bakery.
The baker smiled, the street stayed tidy, and Alec Proper felt proud because he had solved the problem the right way.

World model:
---
- Physical meters: wind, wobble, dirt, damage, crowd_safety, parcel_safety, repair, pride
- Emotional memes: patience, confidence, concern, relief, joy, repetition

Narrative instruments:
---
- Repetition: the hero makes several attempts before noticing the real cause.
- Happy ending: the final state visibly improves and the city is safe again.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"boy", "man", "hero"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
            if self.type in {"girl", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the city"
    detail: str = "bright streets and a tall clock tower"


@dataclass
class StoryParams:
    name: str = "Alec Proper"
    title: str = "proper"
    seed: Optional[int] = None
    scenario: str = "parcel"
    place: str = "city"
    beat: int = 0
    refrain: int = 0
    approach: int = 0
    ending: int = 0
    patrol: int = 0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class StoryBeat:
    beneficiary: str
    target: str
    setup: str
    trouble: str
    danger: str
    attempts: tuple[str, str, str]
    setbacks: tuple[str, str, str]
    clue: str
    cause: str
    fix: str
    resolution: str
    ending_images: tuple[str, str, str, str]


@dataclass(frozen=True)
class Scenario:
    id: str
    repeated_action: str
    beats: tuple[StoryBeat, ...]


SCENARIOS = {
    "parcel": Scenario(
        id="parcel",
        repeated_action="deliver an important parcel",
        beats=(
            StoryBeat(
                beneficiary="Mina the baker",
                target="a parcel of birthday candles",
                setup="Mina the baker needed a parcel of birthday candles before the afternoon party",
                trouble="her little delivery cart kept veering toward a rattling drain cover",
                danger="the parcel could tumble into a puddle and ruin every candle",
                attempts=(
                    "steer the cart with both hands",
                    "brace the wobbly wheel with his boot",
                    "carry the parcel while pulling the empty cart",
                ),
                setbacks=(
                    "the wheel bumped sideways and the parcel tipped",
                    "the cover rocked again and splashed his boot",
                    "the cart snagged his cape and made him set the parcel down",
                ),
                clue="a bright button rolling into the same narrow gap",
                cause="one corner of the drain cover was loose",
                fix="set the cover into its frame and lock it with the safety catch",
                resolution="the cart crossed smoothly, and the candles reached the bakery dry and straight",
                ending_images=(
                    "The candles glowed on a berry cake while the repaired cover lay quiet outside.",
                    "Mina tied a blue ribbon around the dry parcel, and not one wheel rattled in the lane.",
                    "Children counted the bright candles as the steady cart waited neatly by the door.",
                    "In the bakery window, the finished cake shone above a tiny card that read, 'Thank you, Alec.'",
                ),
            ),
            StoryBeat(
                beneficiary="Nurse Jo",
                target="a parcel of warm mittens",
                setup="Nurse Jo was waiting for a parcel of warm mittens for the chilly children at the clinic",
                trouble="each gust pushed the light parcel off Alec's rescue wagon",
                danger="the mittens could blow across the road and be lost",
                attempts=(
                    "hold the parcel down with one gloved hand",
                    "walk beside the wagon and shield it with his cape",
                    "tuck the parcel beneath the wagon's rail",
                ),
                setbacks=(
                    "a gust lifted the lid and sent a mitten fluttering",
                    "the wind curled around his cape and nudged the box again",
                    "the loose rail bounced, and the parcel began to slide",
                ),
                clue="three fallen leaves spinning upward beside the wagon",
                cause="the wagon's canvas cover had been fastened backward, making it catch the wind",
                fix="turn the canvas around and buckle all four corners snugly",
                resolution="the cover shed the wind, and every warm mitten arrived at the clinic",
                ending_images=(
                    "Soon red, green, and yellow mittens waved from the clinic steps.",
                    "Nurse Jo closed the empty parcel while the wagon's snug canvas barely stirred.",
                    "A row of warm hands tapped a happy rhythm on the clinic window.",
                    "As the wind swept past, the correctly buckled cover stayed smooth as a superhero shield.",
                ),
            ),
            StoryBeat(
                beneficiary="Mr. Chen the librarian",
                target="a parcel of new picture books",
                setup="Mr. Chen the librarian needed a parcel of picture books for story hour",
                trouble="the parcel kept sliding to the back of Alec's tilted handcart",
                danger="its corners could split and bend the new books",
                attempts=(
                    "push the handcart very slowly",
                    "hold the parcel against the front rail",
                    "pad the back of the cart with his folded cape",
                ),
                setbacks=(
                    "the box slid backward at the first paving stone",
                    "the front rail shook while the box pulled away from him",
                    "the cape slipped, and the box leaned toward the curb",
                ),
                clue="a marble that rolled to the same back corner and stayed there",
                cause="one rear wheel had been fitted smaller than the other",
                fix="fit the spare wheel beneath the short axle until the handcart stood level",
                resolution="the handcart stood level, and every picture book reached story hour unbent",
                ending_images=(
                    "That evening, children turned crisp pages beneath the library's round lamp.",
                    "The level cart rested by the book return while a dragon gleamed from the top new cover.",
                    "Mr. Chen opened the first book, and a semicircle of children leaned close.",
                    "Alec watched one last marble sit perfectly still on the repaired cart.",
                ),
            ),
        ),
    ),
    "kite": Scenario(
        id="kite",
        repeated_action="rescue a runaway kite",
        beats=(
            StoryBeat(
                beneficiary="Lulu",
                target="a silver star kite",
                setup="Lulu's silver star kite was dancing beautifully when its spool began jerking from her hands",
                trouble="the kite kept diving toward a fence with one sharp, broken slat",
                danger="the silver paper could tear before Lulu's kite show",
                attempts=(
                    "catch the line near the path",
                    "stand on a bench and lift the line clear",
                    "guide the kite away with his cape held wide",
                ),
                setbacks=(
                    "the line snapped taut and skipped over his glove",
                    "another dive pulled it below the bench",
                    "the cape slowed the kite; still, it turned toward the fence once more",
                ),
                clue="the spool clicking at exactly the same point on every dive",
                cause="a knot inside the spool was catching once each turn",
                fix="open the spool, loosen the hidden knot, and rewind the line evenly",
                resolution="the spool turned freely, and the star kite climbed well above the fence",
                ending_images=(
                    "The silver star floated beside the first evening cloud while Lulu held the smooth-running spool.",
                    "At the kite show, the star traced a calm circle high over Alec's red cape.",
                    "The repaired spool hummed softly as the kite's silver tail flashed in the sun.",
                    "Lulu and Alec watched the kite hang steady above the now-mended fence.",
                ),
            ),
            StoryBeat(
                beneficiary="Omar",
                target="a dragon kite",
                setup="Omar was teaching his little sister to fly a green dragon kite",
                trouble="the dragon kept spinning down toward the water's edge",
                danger="its long paper tail could soak through and sink",
                attempts=(
                    "pull the line gently to straighten the dragon",
                    "run sideways to bring it over open ground",
                    "ask Omar to give the spool more line",
                ),
                setbacks=(
                    "the dragon made another dizzy circle",
                    "it followed him briefly, then twisted back toward the water",
                    "the extra line only made the next spin wider",
                ),
                clue="one tail ribbon hanging lower than all the others",
                cause="rainwater had made the last ribbon heavy on one side",
                fix="replace the wet ribbon with two light, matching ribbons",
                resolution="the balanced dragon sailed straight over open ground, safely away from the water",
                ending_images=(
                    "Two green ribbons fluttered evenly as Omar's sister took her first turn with the spool.",
                    "The dragon's shadow glided over the ground without touching the bright water.",
                    "Omar laughed as the balanced kite bowed once above the water birds.",
                    "At sunset, the dry dragon rested on a bench with both new ribbons side by side.",
                ),
            ),
            StoryBeat(
                beneficiary="Priya",
                target="a rainbow kite",
                setup="Priya's rainbow kite carried a tiny paper message for her grandfather",
                trouble="the kite rose a little and then sagged toward a row of young trees",
                danger="the message could snag where no one could reach it",
                attempts=(
                    "lift the kite from the highest safe step",
                    "run with Priya along the open path",
                    "shorten the line and toss the kite carefully upward",
                ),
                setbacks=(
                    "the rainbow rose, shivered, and sank again",
                    "it followed them for five steps before drooping",
                    "the kite climbed higher, then leaned toward the same tree",
                ),
                clue="the top blue panel wrinkling while every other color stayed smooth",
                cause="one crossed support stick had slipped out of its paper pocket",
                fix="slide the support back into place and tie its center firmly",
                resolution="the kite held its shape and carried Priya's message high above the trees",
                ending_images=(
                    "The rainbow message sailed overhead as Priya's grandfather waved from the path.",
                    "All seven colors curved smoothly against the clear sky.",
                    "Priya reeled in the message at dusk, still crisp beneath the steady kite.",
                    "The straight support sticks made a neat cross in the rainbow's sunset shadow.",
                ),
            ),
        ),
    ),
    "toy": Scenario(
        id="toy",
        repeated_action="rescue a runaway toy",
        beats=(
            StoryBeat(
                beneficiary="Benji",
                target="a little red race car",
                setup="Benji was testing a little red race car on a cardboard ramp",
                trouble="every launch sent the car turning toward a deep crack in the path",
                danger="the car could lose a wheel where Benji could not reach it",
                attempts=(
                    "point the ramp farther from the crack",
                    "build a block wall beside the dangerous edge",
                    "give the car a slower, gentler start",
                ),
                setbacks=(
                    "the car curved right and rattled near the crack",
                    "it bounced off one block and headed for the gap again",
                    "even the slow roll bent toward the same spot",
                ),
                clue="a dab of blue clay stuck beneath the car's front axle",
                cause="the clay was pressing one front wheel so it could not spin freely",
                fix="lift away the clay and test both front wheels with one careful flick",
                resolution="both wheels spun evenly, and the red car raced straight into Benji's hands",
                ending_images=(
                    "Benji parked the red car on a chalk finish line, with all four wheels shining.",
                    "The race car zipped between two block towers and stopped beneath Alec's waiting glove.",
                    "Alec and Benji drew a safe new track while the clean axle spun freely.",
                    "The little car rested on the winner's box, far from the covered crack.",
                ),
            ),
            StoryBeat(
                beneficiary="Mei",
                target="a wind-up tin robot",
                setup="Mei's wind-up tin robot was meant to lead the children's toy parade",
                trouble="the robot marched three steps and toppled beside the same curb",
                danger="its painted antenna could bend before the parade began",
                attempts=(
                    "set the robot upright on the smoothest stone",
                    "wind its key only halfway",
                    "walk beside it with one hand ready to catch it",
                ),
                setbacks=(
                    "after three steps, it leaned left and fell",
                    "it moved more slowly and still tipped to the same side",
                    "Alec caught it as its third step went crooked again",
                ),
                clue="a tiny click missing whenever the robot moved its left foot",
                cause="a paper star from the parade had folded around the left ankle joint",
                fix="unwind the paper star and oil the stiff joint",
                resolution="the robot marched in a straight line, its antenna bobbing safely",
                ending_images=(
                    "The tin robot led the parade between rows of clapping children.",
                    "Mei pinned the rescued paper star to the robot's little parade flag.",
                    "Its feet clicked an even left-right rhythm all the way under the bunting.",
                    "At parade's end, the robot stood straight beside Alec's polished boots.",
                ),
            ),
            StoryBeat(
                beneficiary="Tomas",
                target="a wooden toy boat",
                setup="Tomas set a wooden toy boat in a shallow fountain race",
                trouble="the boat kept circling instead of crossing to the finish bell",
                danger="it could drift beneath the fountain ledge and become trapped",
                attempts=(
                    "turn the sail toward the breeze",
                    "start the boat from the other side of the fountain",
                    "make a gentle current with his gloved hand",
                ),
                setbacks=(
                    "the boat drew another small circle",
                    "it crossed halfway, then curled back on itself",
                    "the current sped it up without straightening it",
                ),
                clue="one dark wet patch spreading along the boat's right side",
                cause="a loose wooden rail had soaked up water and made that side heavy",
                fix="dry the rail, press it back into place, and seal it with rescue wax",
                resolution="the balanced boat crossed the fountain and rang the tiny finish bell",
                ending_images=(
                    "The bell gave one bright ding as Tomas lifted the dry, balanced boat.",
                    "A neat wake followed the boat straight across the fountain's reflected sky.",
                    "Tomas set the winner beside the fountain, where its sealed rail gleamed.",
                    "At the final race, the boat reached Alec's red-gloved hand without making a single circle.",
                ),
            ),
        ),
    ),
}

SETTINGS = {
    "city": Setting(place="the city", detail="bright streets, a bakery lane, and a tall clock tower"),
    "harbor": Setting(place="the harbor", detail="quiet docks, gulls overhead, and a long wooden pier"),
    "park": Setting(place="the park", detail="wide paths, a fountain, and a row of old trees"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: Alec Proper, repetition, and a happy ending.")
    ap.add_argument("--name", choices=["Alec Proper", "Alec"], default="Alec Proper")
    ap.add_argument("--scenario", choices=SCENARIOS, default=None)
    ap.add_argument("--place", choices=SETTINGS, default=None)
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
    scenario = args.scenario or rng.choice(list(SCENARIOS))
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name
    if name == "Alec":
        name = "Alec Proper"
    return StoryParams(
        name=name,
        title="proper",
        seed=args.seed,
        scenario=scenario,
        place=place,
        beat=rng.randrange(len(SCENARIOS[scenario].beats)),
        refrain=rng.randrange(5),
        approach=rng.randrange(5),
        ending=rng.randrange(4),
        patrol=rng.randrange(5),
    )


def reasonableness_gate(params: StoryParams, scenario: Scenario) -> None:
    if not params.name.strip():
        raise StoryError("A hero name is required.")
    if scenario.id not in SCENARIOS:
        raise StoryError("Unknown scenario.")
    if "Proper" not in params.name and params.name != "Alec":
        raise StoryError("This world is about Alec Proper; use Alec or Alec Proper.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if not 0 <= params.beat < len(scenario.beats):
        raise StoryError("Unknown scenario beat.")
    if not 0 <= params.refrain < 5 or not 0 <= params.approach < 5:
        raise StoryError("Unknown repetition style.")
    if not 0 <= params.ending < 4 or not 0 <= params.patrol < 5:
        raise StoryError("Unknown story style.")


ASP_RULES = r"""
hero(alec).
hero(proper).

scenario(parcel; kite; toy).

repeats(parcel) :- scenario(parcel).
repeats(kite) :- scenario(kite).
repeats(toy) :- scenario(toy).

happy_end(parcel) :- repeats(parcel).
happy_end(kite) :- repeats(kite).
happy_end(toy) :- repeats(toy).

valid_story(H, S) :- hero(H), scenario(S), repeats(S), happy_end(S).
#show valid_story/2.
#show repeats/1.
#show happy_end/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("hero", "alec"))
    lines.append(asp.fact("hero", "proper"))
    for sid in SCENARIOS:
        lines.append(asp.fact("scenario", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {(hero, sid) for hero in ("alec", "proper") for sid in SCENARIOS}
    if atoms == py:
        print(f"OK: clingo matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH")
    print("clingo:", sorted(atoms))
    print("python:", sorted(py))
    return 1


def build_world(params: StoryParams, scenario: Scenario, setting: Setting) -> World:
    beat = scenario.beats[params.beat]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", label=params.name, type="hero"))
    target = world.add(Entity(id="target", label=beat.target, type=scenario.id))
    beneficiary = world.add(Entity(id="beneficiary", kind="character", label=beat.beneficiary, type="person"))
    place = world.add(Entity(id="place", label=setting.place, type="place"))

    hero.memes.update({"patience": 0.0, "confidence": 0.0, "concern": 0.0, "relief": 0.0, "joy": 0.0, "repetition": 0.0})
    target.meters.update({"safety": 0.4, "damage": 0.0})
    place.meters.update({"danger": 0.0, "crowd_safety": 1.0, "repair": 0.0, "pride": 0.0})

    patrol_openings = (
        f"Before each patrol, {params.name} checked every buckle on the cape and every tool in the rescue kit.",
        f"{params.name} began each patrol by testing the gloves, folding the cape, and counting the rescue tools twice.",
        f"A place for every tool and every tool in its place was {params.name}'s rule before patrol.",
        f"Each morning, {params.name} polished the hero badge and packed the rescue kit in careful rows.",
        f"No patrol began until {params.name} had checked the cape, the gloves, and the little silver toolkit.",
    )
    world.say(f"{params.name} was a careful little superhero who watched over {setting.place}.")
    world.say(patrol_openings[params.patrol])
    world.say(f"Around the hero were {setting.detail}.")
    world.para()

    hero.memes["concern"] += 1
    place.meters["danger"] += 1
    world.say(f"One day, {beat.setup}.")
    world.say(f"The trouble was that {beat.trouble}. If it continued, {beat.danger}.")

    refrains = (
        "Try, check, and try once more",
        "Carefully again",
        "One more proper try",
        "I will not give up, but I will pay attention",
        "Again, with eyes open",
    )
    transitions = ("First", "Next", "For the third try")
    for transition, attempt, setback in zip(transitions, beat.attempts, beat.setbacks):
        hero.memes["repetition"] += 1
        world.say(f'"{refrains[params.refrain]}," {params.name} said. {transition}, he tried to {attempt}. But {setback}.')
    world.para()

    approaches = (
        f"This time, {params.name} did not rush. He knelt beside {beat.target} and spotted {beat.clue}.",
        f"Instead of trying a fourth time, {params.name} watched the whole problem from beginning to end. He noticed {beat.clue}.",
        f"{params.name} asked {beat.beneficiary} what looked the same on every try. Together they noticed {beat.clue}.",
        f"{params.name} laid out the rescue tools, then traced the trouble backward. The trail led to {beat.clue}.",
        f"{params.name} closed the rescue kit and listened, looked, and waited through one more cycle. That revealed {beat.clue}.",
    )
    hero.memes["confidence"] += 1
    hero.memes["patience"] += 1
    world.say(approaches[params.approach])
    world.say(f"Now the real cause made sense: {beat.cause}.")
    world.say(f"He opened the rescue kit and carefully worked to {beat.fix}.")
    target.meters["safety"] = 1.0
    target.meters["damage"] = 0.0
    place.meters["danger"] = 0.0
    place.meters["crowd_safety"] += 1
    place.meters["repair"] += 1
    place.meters["pride"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.para()

    world.say(f"At last, {beat.resolution}.")
    world.say(f'{beat.beneficiary} thanked him: "You kept trying, and then you stopped to understand."')
    world.say(beat.ending_images[params.ending])
    world.say(f"As {setting.place} grew calm again, {params.name} packed each tool away, knowing the same problem would not return.")

    world.facts.update(
        hero=hero,
        parcel=target,
        target=target,
        beneficiary=beneficiary,
        city=place,
        place=place,
        scenario=scenario,
        beat=beat,
        setting=setting,
        refrain=refrains[params.refrain],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scenario: Scenario = f["scenario"]
    return [
        f'Write a superhero story for a young child about {f["hero"].label}, repetition, and a happy ending.',
        f"Tell a gentle story where a proper hero keeps trying to {scenario.repeated_action} until the real cause is found.",
        f'Write a simple story that repeats the trouble three times and ends with a safe, happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    beat: StoryBeat = f["beat"]
    hero: Entity = f["hero"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.label}, a proper little superhero who protects {setting.place}.",
        ),
        QAItem(
            question=f"What kept happening again and again?",
            answer=f"{beat.trouble[0].upper() + beat.trouble[1:]}. {hero.label} made three different attempts, but the same trouble returned each time.",
        ),
        QAItem(
            question=f"How did {hero.label} discover the real cause?",
            answer=f"He changed from repeating attempts to investigating and noticed {beat.clue}. That showed him that {beat.cause}.",
        ),
        QAItem(
            question=f"What did {hero.label} do after finding the cause?",
            answer=f"He used his rescue kit to {beat.fix}. Because he fixed the cause, {beat.resolution}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {beat.resolution}. {f['beneficiary'].label} thanked {hero.label}, and {setting.place} was calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a superhero do?",
            answer="A superhero helps people, solves problems, and tries to keep others safe.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means the story does the same action or idea more than once on purpose, so readers notice it.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets fixed and the characters feel safe, glad, or proud.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    scenario = SCENARIOS.get(params.scenario)
    if scenario is None:
        raise StoryError("Unknown scenario.")
    reasonableness_gate(params, scenario)
    setting = SETTINGS[params.place]
    world = build_world(params, scenario, setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for scenario_id, scenario in SCENARIOS.items():
            for place_id in SETTINGS:
                rng = random.Random(base_seed + len(samples))
                params = StoryParams(
                    name="Alec Proper",
                    title="proper",
                    seed=base_seed + len(samples),
                    scenario=scenario_id,
                    place=place_id,
                    beat=rng.randrange(len(scenario.beats)),
                    refrain=rng.randrange(5),
                    approach=rng.randrange(5),
                    ending=rng.randrange(4),
                    patrol=rng.randrange(5),
                )
                samples.append(generate(params))
    else:
        for i in range(max(1, args.n)):
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
