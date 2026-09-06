#!/usr/bin/env python3
"""
storyworlds/worlds/rascal_bilge_ambidextrous_lesson_learned_suspense_space.py
=============================================================================

A small space-adventure storyworld about a rascal, a bilge leak, and an
ambidextrous repair crew member who learns the right lesson under suspense.

Premise:
- A tiny ship is drifting between moons.
- A mischievous rascal sneaks into the bilge and causes a mess.
- The crew must act fast before the ship's lights and life support fail.

Turn:
- The ambidextrous crew member can work with either hand and can fix the leak
  quickly.
- Suspense comes from the ticking meter, the darkening corridor, and the need
  to choose the right tool before the bilge floods.

Resolution:
- The repair succeeds.
- The rascal learns a lesson about tampering with ship systems.
- The ship glides on, safe again, with a brighter ending image.

The story is intentionally small, classical, and state-driven.
"""

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

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str = "the little comet skiff"
    place: str = "the bilge corridor"
    dangerous: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    hand: str
    fixes: set[str]
    covers: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    ship_name: str = "the little comet skiff"
    hero_name: str = "Nova"
    hero_type: str = "crew"
    rascal_name: str = "Mink"
    rascal_type: str = "rascal"
    place: str = "the bilge corridor"
    tool: str = "patch_clamp"
    scenario_id: int = 0
    telling_mode: int = 0
    detail_variant: int = 0


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
TOOLS = {
    "patch_clamp": Tool(
        id="patch_clamp",
        label="patch clamp",
        phrase="a patch clamp with a bright red grip",
        hand="either",
        fixes={"leak"},
        covers={"pipe"},
    ),
    "bilge_pump": Tool(
        id="bilge_pump",
        label="bilge pump",
        phrase="a small bilge pump with a long hose",
        hand="either",
        fixes={"flood"},
        covers={"floor"},
    ),
    "insulated_glove": Tool(
        id="insulated_glove",
        label="insulated glove",
        phrase="an insulated glove for hot cables",
        hand="either",
        fixes={"spark"},
        covers={"hand"},
    ),
}

WORLD_KNOWLEDGE = {
    "bilge": [
        QAItem(
            question="What is a bilge on a ship?",
            answer="The bilge is the lowest part of a ship, where water can collect if something leaks.",
        )
    ],
    "rascal": [
        QAItem(
            question="What is a rascal?",
            answer="Rascal can mean a playful troublemaker. In this story, RASCAL is a robot class name, not an insulting label for a person.",
        )
    ],
    "ambidextrous": [
        QAItem(
            question="What does ambidextrous mean?",
            answer="Ambidextrous means someone can use both hands well.",
        )
    ],
    "space": [
        QAItem(
            question="Why do ships in space still need careful repairs?",
            answer="Even in space, a ship needs working pipes, power, and air so the crew can stay safe.",
        )
    ],
    "suspense": [
        QAItem(
            question="What makes a story feel suspenseful?",
            answer="A story feels suspenseful when something important might go wrong and everyone must wait to see what happens.",
        )
    ],
}

ASP_RULES = r"""
% A repair is reasonable when the tool matches the problem and the hero can use
% it with the needed hand.
can_fix(T, P) :- tool(T), problem(P), fixes(T, P).
has_reasonable_repair(P) :- can_fix(_, P).

valid_story(Problem, Tool) :- problem(Problem), can_fix(Tool, Problem), ambi(hero).
"""

SHIP_NAMES = [
    "the little comet skiff",
    "the moon-skipper",
    "the lantern ark",
    "the starling shuttle",
]

HERO_NAMES = ["Nova", "Jax", "Rin", "Pip", "Mira", "Tess"]
RASCAL_NAMES = ["Mink", "Nip", "Sly", "Skitter", "Bramble"]
TRAITS = ["curious", "brave", "careful", "quick", "steady"]

SCENARIOS = [
    {
        "title": "the hidden ice bead",
        "opening": "a silver bead of ice rolled from an air recycler and vanished through a deck grate",
        "cause": "the bead melted beside a bilge valve and made its seal slip",
        "signal": "a thin hiss answered each blink of the blue pressure lamp",
        "stakes": "water could reach the recycler cable and stop fresh air from circulating",
        "mistake": "RASCAL reached for the loud emergency lever, which would have shut every recycler at once",
        "clue": "a wavering reflection showed that the water was coming from one loose seal, not the tank",
        "left": "held a light beneath the pipe with the left hand",
        "right": "closed the patch clamp over the seal with the right",
        "line": "One leak, one repair. We do not have to darken the whole ship",
        "repair": "The hiss narrowed to a sigh, and the recycler fan spun steadily again",
        "lesson": "check where a problem begins before choosing the biggest control",
        "ending": "one last ice bead rested harmlessly in a cup while two moons shone through the grate",
        "problem": "leak",
    },
    {
        "title": "the comet-dust clog",
        "opening": "after the ship skimmed a comet tail, pearly dust began pattering inside the bilge filter",
        "cause": "RASCAL had opened a sample hatch before the collection sleeve was fastened",
        "signal": "the pump coughed three times, then the deck gauge crept toward amber",
        "stakes": "a clogged return pipe would let cleaning water rise around the cargo batteries",
        "mistake": "RASCAL tried to sweep the glittering dust deeper into the grate",
        "clue": "the pump grew quiet whenever the sample hatch was covered",
        "left": "pinched the loose sleeve closed with the left hand",
        "right": "secured the patch clamp around its torn coupling with the right",
        "line": "Dust belongs in the sample jar, not in the ship's veins",
        "repair": "The gauge slid back to green as the filter gave a cheerful burble",
        "lesson": "finish a safety step before rushing toward an exciting discovery",
        "ending": "sealed comet dust sparkled in a jar above a clean, dry grate",
        "problem": "clog",
    },
    {
        "title": "the upside-down maintenance map",
        "opening": "during night watch, RASCAL followed a maintenance map while holding it upside down",
        "cause": "the robot loosened the gray waste valve instead of testing the green drinking-water valve",
        "signal": "drip, pause, drip echoed from behind a wall panel no one could see through",
        "stakes": "the hidden trickle could fill the sensor box before the next watch arrived",
        "mistake": "RASCAL insisted the map arrow must be wrong and reached for a second valve",
        "clue": "tiny printed stars on the map matched the ceiling only when the page was turned around",
        "left": "held the corrected map and traced the pipe route with the left hand",
        "right": "tightened the gray valve's patch clamp with the right",
        "line": "A map can guide us only after we learn which way it faces",
        "repair": "The hidden dripping stopped, and the sensor box remained dry",
        "lesson": "pause to orient instructions instead of blaming them when they seem strange",
        "ending": "the map hung right-side up beside a single dry silver pipe",
        "problem": "wrong valve",
    },
    {
        "title": "the bouncing moon melon",
        "opening": "a moon melon escaped the galley net when a small gravity wobble made every loose thing float",
        "cause": "RASCAL chased it into the bilge and bumped a rinse-water joint with a cargo pole",
        "signal": "round drops drifted like glass marbles while the gravity alarm counted down",
        "stakes": "when gravity returned, every floating drop would fall onto the navigation relay",
        "mistake": "RASCAL batted at the drops, scattering them into smaller spheres",
        "clue": "all the droplets streamed from a hairline gap whenever the pipe flexed",
        "left": "caught the wandering moon melon in a net with the left hand",
        "right": "locked the patch clamp across the flexing joint with the right",
        "line": "Catch the cause first; the drops can wait inside the net",
        "repair": "The joint held just as gravity returned, and the trapped water settled safely into a bucket",
        "lesson": "chasing a funny accident can worsen it unless the real danger is handled first",
        "ending": "the rescued moon melon floated in its net above a bucket that held every shining drop",
        "problem": "floating water",
    },
    {
        "title": "the singing pipe",
        "opening": "a low musical note began humming through the bilge during the ship's quiet hour",
        "cause": "RASCAL had clipped a toy sound vane to a pipe, and its vibration loosened a coupling",
        "signal": "the note climbed higher whenever a pale wet ring widened around the joint",
        "stakes": "the vibrating pipe could split before the ship completed its turn around the moon",
        "mistake": "RASCAL wanted to tune the vane until the note sounded prettier",
        "clue": "the pitch fell when the crew member pressed one finger against the loose coupling",
        "left": "steadied the trembling pipe with the left hand",
        "right": "ratcheted the patch clamp shut with the right",
        "line": "That song is a warning. Let us make the pipe quiet before we make music",
        "repair": "The dangerous note faded, leaving only the ship's gentle engine hum",
        "lesson": "an unusual sound should be investigated before it becomes entertainment",
        "ending": "the toy vane chimed safely from a hook while the repaired pipe stayed silent",
        "problem": "vibration",
    },
    {
        "title": "the missing inspection firefly",
        "opening": "an inspection light shaped like a firefly failed to return from the bilge maze",
        "cause": "RASCAL had sent it through an unmarked side pipe, where it wedged against a soft hose",
        "signal": "its red beacon blinked beneath the floor as the hose slowly bent around it",
        "stakes": "a pinched coolant hose could make the observation dome too warm",
        "mistake": "RASCAL tugged the light's guide thread, pulling the knot tighter",
        "clue": "the beacon shifted whenever cool water pulsed through the neighboring line",
        "left": "eased the guide thread backward with the left hand",
        "right": "braced the bent hose with the open patch clamp in the right",
        "line": "Gentle hands solve knots that hard pulling only tightens",
        "repair": "The firefly light slid free, and the coolant hose rounded out without leaking",
        "lesson": "when something is stuck, study how it is caught before pulling harder",
        "ending": "the little inspection firefly blinked green beside a cool clear dome",
        "problem": "pinched hose",
    },
    {
        "title": "the false meteor alarm",
        "opening": "a bang beneath the deck made RASCAL announce that a meteor had pierced the ship",
        "cause": "a storage tin had fallen onto the bilge pipe and cracked a drain collar",
        "signal": "the alarm screen showed no hull breach, yet a puddle crept toward the red boundary stripe",
        "stakes": "crossing that stripe would wet the motor that opened the safety doors",
        "mistake": "RASCAL began stuffing spacesuit cloth against the outer wall",
        "clue": "the puddle rippled after each drip from the dented drain collar",
        "left": "slid an empty tray under the drip with the left hand",
        "right": "fixed the cracked collar with the patch clamp in the right",
        "line": "The bang was real, but our first guess was not. Follow the evidence",
        "repair": "The puddle stopped short of the stripe, and the safety doors passed their test",
        "lesson": "a frightening guess should not replace careful evidence",
        "ending": "the dented tin became a flowerpot, far from the dry red stripe",
        "problem": "cracked drain",
    },
    {
        "title": "the frozen drain",
        "opening": "in the shadow of an ice moon, frost feathers spread across the bilge drain",
        "cause": "RASCAL had turned the warming ribbon off to save a tiny bit of power",
        "signal": "meltwater pooled behind the ice while the ship's tilt meter ticked upward",
        "stakes": "an uneven pool could unbalance the skiff during its narrow docking approach",
        "mistake": "RASCAL raised a metal hammer to break the frozen drain",
        "clue": "the frost thinned wherever the dormant warming ribbon crossed the pipe",
        "left": "switched the warming ribbon to its low setting with the left hand",
        "right": "held the patch clamp around a seam softened by the cold with the right",
        "line": "Slow warmth will free the drain without breaking what protects us",
        "repair": "Water whispered through the thawed drain, and the tilt meter returned to center",
        "lesson": "saving resources is useful only when essential safety systems stay protected",
        "ending": "a lace of harmless frost framed the centered green tilt light",
        "problem": "frozen drain",
    },
    {
        "title": "the seed-pod roots",
        "opening": "roots from the science garden appeared in a place no roots belonged: the bilge grate",
        "cause": "RASCAL had poured leftover seed water into the grate instead of the garden recycler",
        "signal": "a pump light winked yellow as white roots curled around its intake",
        "stakes": "the blocked pump could not clear ordinary condensation from the lower deck",
        "mistake": "RASCAL started yanking the roots, risking a tear in the intake mesh",
        "clue": "the whole root bundle lifted when its floating seed pod was gently raised",
        "left": "guided the seed pod into a garden cup with the left hand",
        "right": "shielded the pipe seam with the patch clamp in the right",
        "line": "The plant is not the trouble; putting it in the wrong system was",
        "repair": "The roots slipped free intact, and the pump light settled into green",
        "lesson": "living things and machines both need the right place and kind of care",
        "ending": "the rescued pod opened one green leaf while the clean bilge grate gleamed below",
        "problem": "root blockage",
    },
    {
        "title": "the echoing tool box",
        "opening": "every few seconds, a hollow knock traveled through the bilge like footsteps",
        "cause": "RASCAL had left a magnetic tool box unlatched, and it bumped a pressure pipe at each engine pulse",
        "signal": "the knocks came faster as the pressure needle climbed",
        "stakes": "one more hard strike could loosen the pipe above the reserve-water tank",
        "mistake": "RASCAL ran after the echoes instead of checking what moved with the engine",
        "clue": "a trail of crescent dents ended beneath the swinging tool box",
        "left": "latched the tool box to the wall with the left hand",
        "right": "reinforced the dented pipe with the patch clamp in the right",
        "line": "Echoes tell us where sound traveled; dents tell us where trouble began",
        "repair": "The next engine pulse passed in silence, and the pressure needle steadied",
        "lesson": "secure every tool, because small loose things gain force when a ship moves",
        "ending": "the closed tool box cast a neat square shadow over an unmarked floor",
        "problem": "impact damage",
    },
    {
        "title": "the soap-star foam",
        "opening": "blue foam shaped like tiny stars began rising through the bilge grate",
        "cause": "RASCAL had poured concentrated cleaning soap into the rinse return",
        "signal": "each pump cycle lifted the foam closer to an air-quality sensor",
        "stakes": "soap on the sensor could trigger a needless evacuation alarm",
        "mistake": "RASCAL blew on the foam, sending bubbles toward the sensor faster",
        "clue": "the bubbles stopped growing whenever the rinse-return valve was held still",
        "left": "covered the sensor with a dry guard using the left hand",
        "right": "sealed the wobbling return valve with the patch clamp in the right",
        "line": "Pretty bubbles can still point to a serious mistake",
        "repair": "Fresh rinse water carried the foam into a sealed recovery jar before it reached the sensor",
        "lesson": "read a label and measure cleaners instead of guessing",
        "ending": "one blue soap star shimmered inside the jar beneath a calm green sensor",
        "problem": "foam overflow",
    },
    {
        "title": "the borrowed robot wheel",
        "opening": "the bilge inspection cart began circling one drain instead of following its track",
        "cause": "RASCAL had borrowed one grip wheel for a game and replaced it backward",
        "signal": "the circling cart nudged a flexible pipe closer to a sharp deck bracket each time around",
        "stakes": "another circuit could scrape a hole in the pipe and spill reserve water",
        "mistake": "RASCAL tried to block the cart with a boot, but it simply turned toward the bracket sooner",
        "clue": "one wheel's arrow pointed opposite all the others",
        "left": "lifted the cart clear of the track with the left hand",
        "right": "snapped the patch clamp over the pipe's scraped spot with the right",
        "line": "Borrowing means returning a thing correctly, not merely putting it back",
        "repair": "With its wheel reversed, the cart rolled straight and the protected pipe held firm",
        "lesson": "return shared equipment in working order and admit changes before they cause harm",
        "ending": "the cart traced one perfect silver circle around the dry drain, then parked itself",
        "problem": "scraped pipe",
    },
]

TENSION_LINES = [
    "For three heartbeats, only the warning light moved.",
    "The next chime sounded closer than the last.",
    "Nobody knew whether there was time for a second attempt.",
    "Beyond the hull, silent stars made the small danger feel enormous.",
    "A countdown bar lost one bright square.",
    "The deck trembled, and everyone waited for the reading to change.",
    "A shadow crossed the gauge just before it touched amber.",
    "The corridor went so quiet that one falling drop sounded loud.",
]

REFLECTIONS = [
    "Quick is useful only after careful becomes clear.",
    "Being able to use both hands did not mean acting without thought.",
    "Skill mattered most when it served evidence instead of panic.",
    "A good repair began with noticing, not grabbing.",
    "Courage was staying curious while the warning light blinked.",
    "Two capable hands still needed one calm plan.",
]


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    fallback_seed = sum(ord(ch) for ch in f"{params.ship_name}|{params.hero_name}|{params.rascal_name}")
    rng = random.Random(params.seed if params.seed is not None else fallback_seed)
    raw_scene = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    tension = TENSION_LINES[params.detail_variant % len(TENSION_LINES)]
    reflection = REFLECTIONS[(params.detail_variant + params.telling_mode) % len(REFLECTIONS)]
    world = World(Ship(name=params.ship_name, place=params.place))
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type="crew",
        label=params.hero_name,
        traits=["ambidextrous", rng.choice(TRAITS)],
        meters={"stress": 0.0, "skill": 1.0},
        memes={"hope": 1.0, "worry": 0.0, "lesson": 0.0},
    ))
    rascal = world.add(Entity(
        id="rascal",
        kind="character",
        type="robot",
        label=params.rascal_name,
        traits=["RASCAL-class", "curious", "inexperienced"],
        meters={"mess": 0.0},
        memes={"guilt": 0.0, "trouble": 1.0, "lesson": 0.0},
    ))
    tool = TOOLS[params.tool]
    world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        held_by=hero.id,
        meters={"usefulness": 1.0},
    ))
    scene = {
        key: value.replace("RASCAL", rascal.label) if isinstance(value, str) else value
        for key, value in raw_scene.items()
    }

    intros = [
        f"Aboard {world.ship.name}, {hero.label} watched a quiet lane of space unroll between two moons.",
        f"{world.ship.name.capitalize()} was halfway across a field of blue stars when the bilge watch changed.",
        f"On the smallest ship in that corner of space, {hero.label} knew every hum that belonged and every knock that did not.",
        f"The windows of {world.ship.name} held a wide view of space, but {hero.label}'s work led down to {world.ship.place}.",
    ]
    robot_intro = (
        f"{rascal.label} was a RASCAL-class helper robot, a machine-category name rather than an insult for a person. "
        f"The eager little robot was still learning when curiosity needed permission on a ship in space."
    )
    skill_intro = (
        f"{hero.label} was ambidextrous and could use either hand equally well, a useful skill in the bilge's narrow passages."
    )
    world.say(intros[params.detail_variant % len(intros)])
    if params.telling_mode % 3 == 1:
        world.say(skill_intro)
        world.say(robot_intro)
    else:
        world.say(robot_intro)
        world.say(skill_intro)

    world.para()
    incident = f"That watch, {scene['opening']}."
    cause = f"The cause soon became clear: {scene['cause']}."
    signal = f"In {world.ship.place}, {scene['signal']}."
    if params.telling_mode % 4 == 0:
        world.say(signal)
        world.say(incident)
    elif params.telling_mode % 4 == 1:
        world.say(incident)
        world.say(signal)
    elif params.telling_mode % 4 == 2:
        world.say(f"First, {scene['signal']}. Moments earlier, {scene['opening']}.")
    else:
        world.say(f'"That should not be happening," {hero.label} said.')
        world.say(f"In the bilge, {scene['signal']}.")
        world.say(incident)
    world.say(cause)
    world.say(f"If they delayed, {scene['stakes']}.")
    world.say(tension + " The waiting filled the small ship with suspense.")

    rascal.meters["mess"] += 1.0
    hero.memes["worry"] += 1.0
    world.para()
    world.say(f"At first, {scene['mistake']}.")
    world.say(f"{hero.label} stopped the attempt and looked for a clue. {scene['clue'].capitalize()}.")
    world.say(f'"{scene["line"]}," {hero.label} said.')
    if params.telling_mode % 2:
        world.say(
            f"Working ambidextrously, {hero.label} {scene['right']}, while {hero.pronoun()} {scene['left']}."
        )
    else:
        world.say(
            f"Working ambidextrously, {hero.label} {scene['left']}; at the same time, {hero.pronoun()} {scene['right']}."
        )
    world.say(f"{scene['repair']}.")

    world.para()
    hero.meters["skill"] += 1.0
    hero.memes["hope"] += 1.0
    rascal.memes["guilt"] += 1.0
    rascal.memes["lesson"] += 1.0
    hero.memes["lesson"] += 1.0
    apologies = [
        f'"I changed the system without asking," {rascal.label} admitted. "I will report it and help check the bilge."',
        f'{rascal.label} recorded the mistake in the repair log and said, "Next time I will ask before I touch ship equipment."',
        f'"I was curious, but I was not careful," {rascal.label} said, then helped return every tool to its marked place.',
        f'{rascal.label} did not hide the error. The robot explained it to the crew and volunteered for a supervised safety check.',
    ]
    world.say(apologies[(params.detail_variant + params.scenario_id) % len(apologies)])
    world.say(f"The lesson learned was simple: {scene['lesson'].capitalize()}.")
    world.say(f"{hero.label} carried a lesson forward too: {reflection.lower()}")
    endings = [
        f"When the ship resumed its course, {scene['ending']}.",
        f"Later, beneath the porthole's slow-turning stars, {scene['ending']}.",
        f"The warning light went dark. In its place, {scene['ending']}.",
        f"As {world.ship.name} glided onward through space, {scene['ending']}.",
    ]
    world.say(endings[(params.telling_mode + params.detail_variant) % len(endings)])

    world.facts.update(
        hero=hero,
        rascal=rascal,
        tool=tool,
        ship=world.ship,
        suspense=True,
        resolved=True,
        leak_fixed=True,
        scenario=scene,
        clue=scene["clue"],
        stakes=scene["stakes"],
        lesson=scene["lesson"],
        ending=scene["ending"],
    )
    return world


# ---------------------------------------------------------------------------
# Story QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    rascal = f["rascal"]
    tool = f["tool"]
    scene = f["scenario"]
    return [
        "Write a child-friendly space adventure about a RASCAL-class robot, a bilge emergency, and an ambidextrous crew member.",
        f"Tell a suspenseful story where {hero.label} follows evidence during {scene['title']} and {rascal.label} learns a safety lesson.",
        f"Create a spaceship story involving the bilge, {tool.label}, and the danger that {scene['stakes']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rascal = f["rascal"]
    tool = f["tool"]
    scene = f["scenario"]
    return [
        QAItem(
            question=f"What danger did {hero.label} prevent in the bilge?",
            answer=f"{hero.label} prevented the danger that {scene['stakes']}. The repair used a {tool.label} while the evidence guided each step.",
        ),
        QAItem(
            question="Which clue revealed what the crew should do?",
            answer=f"The useful clue was that {scene['clue']}. It pointed to the cause instead of the first frightening guess.",
        ),
        QAItem(
            question=f"What lesson did {rascal.label} learn?",
            answer=f"{rascal.label} learned this: {scene['lesson'].capitalize()}. The robot also admitted the mistake instead of hiding it.",
        ),
        QAItem(
            question=f"How did being ambidextrous help {hero.label}?",
            answer=f"Being ambidextrous meant {hero.label} could use both hands equally well. During the repair, the crew member {scene['left']} and {scene['right']}.",
        ),
        QAItem(
            question="What image showed that the emergency was over?",
            answer=f"At the end, {scene['ending']}. That concrete image showed that the bilge and ship were safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["bilge"])
    out.extend(WORLD_KNOWLEDGE["rascal"])
    out.extend(WORLD_KNOWLEDGE["ambidextrous"])
    out.extend(WORLD_KNOWLEDGE["space"])
    out.extend(WORLD_KNOWLEDGE["suspense"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_facts() -> str:
    import asp

    lines = []
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        for p in sorted(t.fixes):
            lines.append(asp.fact("fixes", t.id, p))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
    lines.append(asp.fact("problem", "leak"))
    lines.append(asp.fact("problem", "flood"))
    lines.append(asp.fact("ambi", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("leak", "patch_clamp"), ("flood", "bilge_pump")}
    if asp_set == py_set:
        print("OK: ASP gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("  ASP:", sorted(asp_set))
    print("  PY :", sorted(py_set))
    return 1


def python_reasonable(params: StoryParams) -> None:
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.hero_name == params.rascal_name:
        raise StoryError("The hero and the rascal must be different characters.")
    if params.tool != "patch_clamp":
        raise StoryError("This story only makes sense with the patch clamp as the repair.")
    if not params.hero_name or not params.rascal_name:
        raise StoryError("Both hero and rascal need names.")


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld about a rascal, the bilge, and an ambidextrous repair.")
    ap.add_argument("--ship-name", choices=SHIP_NAMES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--rascal-name", choices=RASCAL_NAMES)
    ap.add_argument("--tool", choices=TOOLS)
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
    ship_name = args.ship_name or rng.choice(SHIP_NAMES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    rascal_name = args.rascal_name or rng.choice(RASCAL_NAMES)
    tool = args.tool or "patch_clamp"
    params = StoryParams(
        seed=None,
        ship_name=ship_name,
        hero_name=hero_name,
        rascal_name=rascal_name,
        tool=tool,
        scenario_id=rng.randrange(len(SCENARIOS)),
        telling_mode=rng.randrange(8),
        detail_variant=rng.randrange(48),
    )
    python_reasonable(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(ship_name="the little comet skiff", hero_name="Nova", rascal_name="Mink", tool="patch_clamp"),
    StoryParams(ship_name="the moon-skipper", hero_name="Rin", rascal_name="Skitter", tool="patch_clamp"),
    StoryParams(ship_name="the lantern ark", hero_name="Pip", rascal_name="Nip", tool="patch_clamp"),
]


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
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible story pattern(s):")
        for p in vals:
            print(" ", p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
