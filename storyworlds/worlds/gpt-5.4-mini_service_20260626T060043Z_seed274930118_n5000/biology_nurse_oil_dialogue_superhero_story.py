#!/usr/bin/env python3
"""
A small story world about a young superhero helping a nurse clean up an oily
biology-lab mishap through dialogue and a careful, brave rescue.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
STORYWORLDS_ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    role: str
    name: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "she" if self.role in {"girl", "woman", "nurse"} else "he"

    def possessive(self) -> str:
        return "her" if self.role in {"girl", "woman", "nurse"} else "his"


@dataclass
class Location:
    name: str = "the biology wing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    sidekick_name: str
    nurse_name: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Character] = {}
        self.location = Location()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.dialogue_turns: list[tuple[str, str]] = []

    def add(self, ent: Character) -> Character:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.location = _copy.deepcopy(self.location)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.dialogue_turns = list(self.dialogue_turns)
        return w


ASP_RULES = r"""
#show risk/1.
#show fix/1.
risk(oil) :- spill(oil).
fix(oil) :- nurse(nina), hero(harper), tool(towel), tool(soap).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("spill", "oil"),
        asp.fact("nurse", "nina"),
        asp.fact("hero", "harper"),
        asp.fact("tool", "towel"),
        asp.fact("tool", "soap"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero biology-lab story world with dialogue.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
    ap.add_argument("--nurse-name", choices=NURSE_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


HERO_NAMES = ["Nova", "Pulse", "Vector", "Spark", "Comet"]
SIDEKICK_NAMES = ["Milo", "Ruby", "Theo", "Iris", "Zane"]
NURSE_NAMES = ["Nina", "Mara", "June", "Tess", "Lena"]


@dataclass(frozen=True)
class BiologyIncident:
    station: str
    study: str
    spill: str
    danger: str
    clue: str
    hero_action: str
    sidekick_action: str
    nurse_action: str
    result: str
    lesson: str
    ending: str


INCIDENTS = [
    BiologyIncident(
        station="the tide-pool table",
        study="how seaweed shelters tiny shore animals",
        spill="a cracked dropper leaked lamp oil toward a tray of model crabs",
        danger="the oil could coat the models and reach the water samples",
        clue="a rainbow sheen was creeping along the lowest groove",
        hero_action="froze the leading edge inside a ring of cool air",
        sidekick_action="slid absorbent pads between the sheen and the sample jars",
        nurse_action="used tongs to lift the cracked dropper into a sealed tub",
        result="the water samples stayed clear and every model crab remained dry",
        lesson="protecting a habitat begins by stopping pollution before it spreads",
        ending="a clear sample jar caught the sunset and painted a tiny silver wave on the wall",
    ),
    BiologyIncident(
        station="the seed-sprouting bench",
        study="which roots grow fastest toward water",
        spill="a loose hinge knocked plant oil across the numbered seed trays",
        danger="the labels could slide away and ruin the careful comparison",
        clue="tray four's paper label was already drifting toward tray five",
        hero_action="made a gentle shield around the labels without touching the seedlings",
        sidekick_action="copied each tray number onto dry cards from the experiment notebook",
        nurse_action="blotted from the outside inward so the oil could not spread",
        result="the seedlings and their records were saved in the correct order",
        lesson="good biology depends on both living samples and accurate notes",
        ending="one pale root curled beside its rescued number card like a small green question mark",
    ),
    BiologyIncident(
        station="the butterfly observation nook",
        study="how wing patterns help butterflies hide",
        spill="a display lamp tipped and dripped cooling oil beside a resting chrysalis",
        danger="strong fumes and a slippery floor could disturb the fragile insect",
        clue="the chrysalis trembled whenever the warm lamp flickered",
        hero_action="carried the lamp straight up with a ribbon of magnetic light",
        sidekick_action="opened the high vent and quietly guided visitors behind a rope",
        nurse_action="covered the oil with safe mineral granules and swept them into a marked container",
        result="the nook became quiet, cool, and safe for the chrysalis again",
        lesson="sometimes a superhero's bravest rescue is slow and quiet",
        ending="the still chrysalis hung above the clean floor like a gold comma waiting for tomorrow",
    ),
    BiologyIncident(
        station="the skeleton puzzle corner",
        study="how joints let arms and legs bend",
        spill="a rolling cart clipped a bottle of machine oil used on the model's stiff knee",
        danger="the slick path ran toward a doorway crowded with visiting children",
        clue="one shiny trail was thinner, showing which way the cart had rolled",
        hero_action="stretched a bright warning ribbon across the doorway in one swift leap",
        sidekick_action="followed the thin trail and locked the cart's loose wheel",
        nurse_action="sprinkled absorbent powder and tested the floor with a dry cloth",
        result="the doorway reopened safely and the skeleton's knee could bend without a squeak",
        lesson="following evidence can reveal both a problem and its cause",
        ending="the clean skeleton waved one bony hand while the children waved back",
    ),
    BiologyIncident(
        station="the pond-microbe microscope desk",
        study="how tiny organisms move through a drop of pond water",
        spill="a jar of immersion oil rolled beside the microscope slides",
        danger="the oil could blur the slides and spoil the only pond samples",
        clue="the jar had stopped against a pencil, but its cap was slowly loosening",
        hero_action="held the jar steady with a pinpoint beam instead of grabbing the glass",
        sidekick_action="moved the labeled slides into a padded case one row at a time",
        nurse_action="tightened the cap with gloves and cleaned the microscope lens correctly",
        result="the class later watched a bright green microbe spin across the saved slide",
        lesson="the smallest tools require the steadiest teamwork",
        ending="the microscope screen glowed with one living green speck doing a victory twirl",
    ),
    BiologyIncident(
        station="the bird-feather comparison wall",
        study="how different feathers keep birds warm or help them fly",
        spill="a bottle of feather-conditioning oil slipped from an open supply box",
        danger="the oil was flowing under rare labeled feathers",
        clue="a loose shelf peg had tilted the entire supply box",
        hero_action="lifted the feather cards on a cushion of air before the oil reached them",
        sidekick_action="sorted the rescued cards by their colored corner marks",
        nurse_action="plugged the shelf hole, secured the peg, and cleaned the spill",
        result="every feather returned to its proper bird and the shelf stood level",
        lesson="a lasting rescue fixes the cause instead of only cleaning the mess",
        ending="a blue jay feather stood safely upright, bright as a superhero's banner",
    ),
    BiologyIncident(
        station="the honeybee pollination garden",
        study="how pollen travels from flower to flower",
        spill="a bicycle chain left a ribbon of oil across the greenhouse path",
        danger="the nurse could not reach a tired bee while the path was slippery",
        clue="tiny wheel marks led from the oily ribbon to an unlocked delivery bicycle",
        hero_action="made stepping-stones of sturdy light above the slick path",
        sidekick_action="wheeled the bicycle outside and fastened its dripping chain cover",
        nurse_action="carried the bee to a shaded blossom and set down a drop of sugar water",
        result="the path was cleaned and the rested bee flew to a yellow flower",
        lesson="caring for living things includes making their surroundings safe",
        ending="a dusting of golden pollen shone on the bee as it vanished among the blooms",
    ),
    BiologyIncident(
        station="the woodland food-web board",
        study="how plants and animals depend on one another",
        spill="an old projector released a bead of oil above the magnetic animal cards",
        danger="the falling oil could erase the class's carefully built food web",
        clue="a warm humming sound began each time the projector formed another bead",
        hero_action="switched off the projector and caught the bead in a floating glass cup",
        sidekick_action="photographed the food web before moving the cards to a dry table",
        nurse_action="marked the projector unsafe and called the equipment team",
        result="the food web was rebuilt exactly and the faulty machine stayed off",
        lesson="pausing unsafe equipment can be wiser than using a superpower on it",
        ending="the final fox card clicked into place beneath a paper forest glowing in the window",
    ),
    BiologyIncident(
        station="the fish-gill demonstration tank",
        study="how fish take oxygen from water",
        spill="a pump motor coughed out a spot of oil near the tank's air hose",
        danger="the oil must not enter the water where the classroom minnows were breathing",
        clue="the air bubbles slowed whenever the motor gave a rough rattle",
        hero_action="pinched the emergency valve shut with a precise beam of force",
        sidekick_action="started the clean hand pump to keep fresh bubbles moving",
        nurse_action="isolated the oily motor and placed a barrier around the tank",
        result="the minnows kept breathing while a clean replacement pump was fitted",
        lesson="watching an animal's behavior can warn us that its environment is changing",
        ending="three minnows gathered under the new bubbles, their tails flashing like little flags",
    ),
    BiologyIncident(
        station="the compost-creature station",
        study="how worms and fungi turn old leaves into healthy soil",
        spill="a maintenance can dripped oil beside the warm compost bin",
        danger="the oil could soak into the soil where the red worms lived",
        clue="a dry ridge of sawdust was keeping one side of the spill from moving",
        hero_action="extended the sawdust ridge into a complete circle around the oil",
        sidekick_action="carried the worm bin to a clean mat without jostling its layers",
        nurse_action="scooped the contained material into a disposal pail and checked the soil",
        result="the compost stayed clean and the worms burrowed back beneath the leaves",
        lesson="observing what already works can suggest the safest solution",
        ending="one red worm disappeared under a brown leaf as the clean soil settled softly",
    ),
    BiologyIncident(
        station="the lung-and-breathing exhibit",
        study="why lungs need clean air",
        spill="a fan bearing leaked oil onto the floor beneath the breathing model",
        danger="the broken fan was pushing an oily smell toward the visitors",
        clue="a tissue strip beside the left vent fluttered much faster than the others",
        hero_action="sealed the left vent with a broad patch from the emergency kit",
        sidekick_action="guided everyone to the fresh-air courtyard in an orderly line",
        nurse_action="unplugged the fan and checked that each visitor felt well",
        result="fresh air returned before the exhibit reopened with a new fan",
        lesson="biology lessons about breathing matter most when people act on them",
        ending="the repaired lung model rose and fell beside an open window full of morning air",
    ),
    BiologyIncident(
        station="the nocturnal-animal room",
        study="how whiskers help animals find their way in darkness",
        spill="a shadow-lamp hinge leaked oil beside the papier-mache bat cave",
        danger="the oil made the dark walkway unsafe during the demonstration",
        clue="the sidekick's reflection revealed the slick patch before anyone stepped on it",
        hero_action="projected a low red glow that lit the floor without spoiling the dark display",
        sidekick_action="placed textured safety markers along a dry route to the exit",
        nurse_action="closed the walkway and cleaned each shiny patch until it passed inspection",
        result="the visitors returned by the safe route and completed the whisker experiment",
        lesson="using every teammate's senses makes a rescue stronger",
        ending="the paper bats cast crisp shadows above a floor that no longer gleamed",
    ),
]

OPENINGS = [
    "The biology wing was preparing for family science night.",
    "Rain tapped the windows while a small biology lesson began indoors.",
    "A class had just arrived for its first hands-on biology visit.",
    "The biology wing hummed with carts, questions, and careful experiments.",
    "Just before closing time, one final biology demonstration remained.",
]

DIALOGUE_FORMS = [
    ("Freeze where you are; the oil has made a hazard.", "Tell us what you notice, and we will make a plan.", "I see the clue. We can solve the cause, not just the spill."),
    ("Everyone step back from the oil, please.", "We are listening, Nurse. What needs protection first?", "The clue points to our safest first move."),
    ("This is a rescue for calm heads, not hurried feet.", "Then calm heads are the superpower we will use.", "I found the cause. Let us divide the jobs."),
    ("Oil warning! Stop at the blue line.", "Sidekick, observe; I will guard the danger.", "Nurse, check our plan before we begin."),
    ("The living samples come first, and nobody crosses the spill.", "Agreed. We will protect life and keep the evidence clear.", "One clue, three helpers, and no guessing."),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick_name or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    nurse = args.nurse_name or rng.choice(NURSE_NAMES)
    return StoryParams(hero_name=hero, sidekick_name=sidekick, nurse_name=nurse)


def _setup_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Character(id="hero", role="hero", name=params.hero_name))
    sidekick = w.add(Character(id="sidekick", role="sidekick", name=params.sidekick_name))
    nurse = w.add(Character(id="nurse", role="nurse", name=params.nurse_name))
    w.facts.update(hero=hero, sidekick=sidekick, nurse=nurse)
    return w


def _predict_spill(world: World) -> bool:
    sim = world.copy()
    sim.location.meters["oil"] = 1
    return sim.location.meters["oil"] >= 1


def _dialogue(world: World, speaker: Character, line: str) -> None:
    world.dialogue_turns.append((speaker.name, line))
    world.say(f'{speaker.name} said, "{line}"')


def _variation_key(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(ch) for ch in f"{params.hero_name}:{params.sidekick_name}:{params.nurse_name}")


def generate_story(world: World, params: StoryParams) -> None:
    hero: Character = world.facts["hero"]
    sidekick: Character = world.facts["sidekick"]
    nurse: Character = world.facts["nurse"]

    key = _variation_key(params)
    incident_index = key % len(INCIDENTS)
    opening_index = (key // len(INCIDENTS)) % len(OPENINGS)
    cycle_index = (key // (len(INCIDENTS) * len(OPENINGS))) % len(DIALOGUE_FORMS)
    dialogue_index = (incident_index + opening_index + cycle_index) % len(DIALOGUE_FORMS)
    leadership_index = (2 * incident_index + opening_index + cycle_index) % 5
    incident = INCIDENTS[incident_index]
    opening = OPENINGS[opening_index]
    warning, hero_reply, clue_reply = DIALOGUE_FORMS[dialogue_index]
    leadership = [
        f"{hero.name} drew a quick safety map while {sidekick.name} counted the dry steps.",
        f"{sidekick.name} repeated the plan aloud, and {hero.name} checked each part before anyone moved.",
        f"{hero.name} asked two questions first: what was alive, and what was still in danger?",
        f"The three helpers pointed to the danger, the living samples, and the cleanup tools in turn.",
        f"{nurse.name} assigned one careful job to each teammate, and both young heroes repeated it back.",
    ][leadership_index]

    world.facts.update(
        station=incident.station,
        study=incident.study,
        spill=incident.spill,
        danger=incident.danger,
        clue=incident.clue,
        hero_action=incident.hero_action,
        sidekick_action=incident.sidekick_action,
        nurse_action=incident.nurse_action,
        result=incident.result,
        lesson=incident.lesson,
        ending=incident.ending,
        opening=opening,
        warning=warning,
        incident_index=incident_index,
        dialogue_index=dialogue_index,
        leadership_index=leadership_index,
    )

    world.say(opening)
    world.say(
        f"At {incident.station}, Nurse {nurse.name} was showing {hero.name} and {sidekick.name} "
        f"{incident.study}. {hero.name}, a young superhero, wore a bright cape but knew that biology "
        "needed careful eyes more than flashy powers."
    )
    world.say(f"Without warning, {incident.spill}. {incident.danger.capitalize()}.")

    world.para()
    _dialogue(world, nurse, warning)
    _dialogue(world, hero, hero_reply)
    world.say(f"Instead of rushing at the oil, {sidekick.name} looked closely. {incident.clue.capitalize()}.")
    _dialogue(world, sidekick, clue_reply)
    world.say(leadership)

    world.para()
    if _predict_spill(world):
        world.location.meters["oil"] = 0
        world.say(f"First, {hero.name} {incident.hero_action}.")
        world.say(f"At the same time, {sidekick.name} {incident.sidekick_action}.")
        world.say(f"Then Nurse {nurse.name} {incident.nurse_action}.")
        _dialogue(world, nurse, "Check the evidence again. A rescue is finished only when it is truly safe.")
        _dialogue(world, hero, "The oil is contained. Our checks show that everyone is safe.")
        world.say(
            f"The team had not merely hidden a mess: {incident.result}. Together they learned that "
            f"{incident.lesson}."
        )
        world.say(f"Before they left, {incident.ending}.")

    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]
    nurse: Character = world.facts["nurse"]
    sidekick: Character = world.facts["sidekick"]
    return [
        QAItem(
            question=(
                f"Who was the young superhero at {world.facts['station']}, and what was happening "
                "when the story began?"
            ),
            answer=f"The young superhero was {hero.name}. {world.facts['opening']}",
        ),
        QAItem(
            question=(
                f"After Nurse {nurse.name} warned, \"{world.facts['warning']}\" what oil problem "
                f"had happened at {world.facts['station']}?"
            ),
            answer=f"The problem began when {world.facts['spill']}.",
        ),
        QAItem(
            question=f"What clue helped {sidekick.name} understand the accident?",
            answer=f"{sidekick.name} noticed that {world.facts['clue']}.",
        ),
        QAItem(
            question=(
                f"How did {hero.name}, {sidekick.name}, and Nurse {nurse.name} solve the problem, "
                "and what final image showed the change?"
            ),
            answer=(
                f"{hero.name} {world.facts['hero_action']}; {sidekick.name} {world.facts['sidekick_action']}; "
                f"and Nurse {nurse.name} {world.facts['nurse_action']}. At the end, {world.facts['ending']}."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is oil slippery?",
            answer="Oil can make surfaces slippery because it spreads into a slick layer that is hard to stand on.",
        ),
        QAItem(
            question="What does a nurse do?",
            answer="A nurse helps people stay healthy, gives care, and keeps things safe in medical places.",
        ),
        QAItem(
            question="What is biology?",
            answer="Biology is the study of living things like plants, animals, and tiny cells.",
        ),
        QAItem(
            question="Why should a spill be cleaned quickly?",
            answer="A spill should be cleaned quickly so nobody slips and the area stays safe and tidy.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero: Character = world.facts["hero"]
    sidekick: Character = world.facts["sidekick"]
    nurse: Character = world.facts["nurse"]
    return [
        f"Write a child-friendly superhero story about {hero.name}, {sidekick.name}, and Nurse {nurse.name} "
        f"protecting {world.facts['station']} after {world.facts['spill']}.",
        f"Tell a dialogue-heavy biology adventure in which the clue is that {world.facts['clue']}, "
        "and the team responds safely to oil.",
        f"Create a short superhero tale about {world.facts['study']}. End with this concrete image: "
        f"{world.facts['ending']}.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        lines.append(f"  {ent.id}: name={ent.name} role={ent.role} meters={ent.meters} memes={ent.memes}")
    lines.append(f"  location: {world.location.name} meters={world.location.meters}")
    lines.append(f"  dialogue turns: {len(world.dialogue_turns)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(hero_name="Nova", sidekick_name="Milo", nurse_name="Nina"),
    StoryParams(hero_name="Spark", sidekick_name="Ruby", nurse_name="Mara"),
    StoryParams(hero_name="Comet", sidekick_name="Theo", nurse_name="June"),
]


def asp_verify() -> int:
    import asp

    program = asp_program("#show risk/1.\n#show fix/1.")
    model = asp.one_model(program)
    atoms = asp.atoms(model, "risk")
    if ("oil",) in atoms:
        print("OK: ASP marks oil as a risk.")
        return 0
    print("MISMATCH: ASP did not mark oil as a risk.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show risk/1.\n#show fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show risk/1.\n#show fix/1."))
        print("risk:", asp.atoms(model, "risk"))
        print("fix:", asp.atoms(model, "fix"))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
