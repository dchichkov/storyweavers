#!/usr/bin/env python3
"""
storyworlds/worlds/psychiatry_sticky_palm_sound_effects_transformation_cautionary.py
===================================================================================

A varied storyworld about botanical mishaps in a starship clinic. A curious
child meets a strange sticky palm, hears odd sound effects, observes a
transformation, and learns to replace a hurried guess with a careful test.

Premise
-------
A child visits the ship's psychiatry room, an ordinary medical space for mental
health care whose observation corner is temporarily helping the crew inspect a
plant. Twelve incidents give the palm different triggers, transformations, and
practical hazards without connecting its fantasy behavior to mental illness.

Turn
----
The child acts before understanding a warning. A concrete consequence follows,
and the child owns the mistake, asks for help, and studies a scenario-specific
clue.

Resolution
----------
A calm clinician and the child use evidence plus a selected safety tool to fix
the actual cause. Each resolution ends with a visible image proving what changed.

The simulated state drives narration:
- meters: stickiness, noise, caution, transformation, calm
- memes: worry, wonder, relief, confidence
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    contains_sticky: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "doctor"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "pilot"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class SpaceBase:
    place: str = "the psychiatry room"
    has_panel: bool = True
    has_locker: bool = True


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    sound: str
    sticky_level: float
    transform_to: str
    caution_needed: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str


@dataclass(frozen=True)
class Scenario:
    id: str
    arrival: str
    temptation: str
    warning_reason: str
    mistake: str
    sound: str
    transformation: str
    danger: str
    clue: str
    safe_action: str
    result: str
    ending: str


class World:
    def __init__(self, base: SpaceBase) -> None:
        self.base = base
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.base)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


CREATURES = {
    "sticky_palm": Creature(
        id="sticky_palm",
        label="sticky palm",
        phrase="a sticky little palm with glossy green fronds",
        sound="squelch-whirr",
        sticky_level=1.0,
        transform_to="lantern palm",
    ),
    "echo_palm": Creature(
        id="echo_palm",
        label="echo palm",
        phrase="a small palm that hummed like a radio",
        sound="ping-ping",
        sticky_level=0.5,
        transform_to="bright palm",
    ),
}

TOOLS = {
    "scoop": Tool(
        id="scoop",
        label="scoop",
        phrase="a long silver scoop",
        purpose="move the plant without touching it",
    ),
    "gloves": Tool(
        id="gloves",
        label="gloves",
        phrase="soft gloves",
        purpose="keep hands from getting sticky",
    ),
}

NAMES = ["Mina", "Tobias", "Lena", "Arin", "Juno", "Sasha"]
ROLES = ["boy", "girl"]
DOCTORS = ["doctor", "psychiatrist", "medic"]
TRAITS = ["curious", "careful", "brave", "small", "thoughtful"]


SCENARIOS = {
    "ceiling_vines": Scenario(
        "ceiling_vines",
        "A cargo robot rolled in a sealed pot found beside the ship's warm engine vents.",
        "One silver seedpod winked like a button that begged to be pressed.",
        "warmth could wake the plant before anyone knew how far its sap could stretch",
        "A loose backpack strap brushed the lowest frond.",
        "SKRITCH-pop-pop!",
        "Its fronds unrolled into glowing vines that raced toward the ceiling lamps.",
        "The vines began shading the clinic's emergency lights.",
        "Each vine curled away from the cool draft under the door.",
        "guided the pot into the cool supply alcove and shaded it with a clean tray",
        "The vines folded back into a tidy crown, leaving every emergency light clear.",
        "Above the closed case, the last vine made a tiny green question mark, then went still.",
    ),
    "echo_melody": Scenario(
        "echo_melody",
        "The botanist delivered a palm that had begun copying the clinic's gentle chime.",
        "Its rhythm sounded almost like an invitation to clap along.",
        "a loud answer might make its sound-sensitive leaves grow too quickly",
        "The child tapped one glove against the beat before the warning was finished.",
        "PING-a-ling, BWONG!",
        "Every leaf widened into a shiny green speaker and echoed the tap ten times louder.",
        "The booming echoes rattled a shelf of breathing-exercise cards.",
        "The leaves softened whenever everyone paused and breathed quietly.",
        "placed the pot on a padded mat, then led three slow, silent breaths",
        "The speaker-leaves narrowed into ordinary fronds and the cards stopped trembling.",
        "In the hush, one leaf chimed a soft good-night note no louder than a raindrop.",
    ),
    "lost_badge": Scenario(
        "lost_badge",
        "A nurse noticed that a visitor badge had vanished beside the new sticky palm.",
        "A blue corner peeped from beneath the plant's glossy leaves.",
        "pulling a trapped object could spray sticky sap across the room",
        "The child tugged the blue corner with two fingers.",
        "THWIP-snap!",
        "The palm flattened into a broad green hand and clamped around the badge.",
        "Its tightening leaves bent the badge and tugged the pot toward the floor.",
        "A drop of water made one gripping leaf relax.",
        "dripped water along the leaf edges and eased the badge free",
        "The broad hand opened, rounded back into a palm, and released the badge unharmed.",
        "The clean badge hung from its hook while three water beads shone on the sleeping leaves.",
    ),
    "rolling_pot": Scenario(
        "rolling_pot",
        "During a gentle turn of the starship, an unsecured plant case rolled into the clinic.",
        "The wobbling pot looked like a toy racing toward the soft chairs.",
        "chasing it by hand could make the frightened plant cling and roll faster",
        "The child grabbed at a frond as the case passed.",
        "RATTLE-squelch-WHEE!",
        "The palm curled into a sticky green wheel and spun between the chairs.",
        "It gathered cushions and paper stars as it rolled toward the doorway.",
        "Its spinning slowed whenever the corridor lights dimmed.",
        "dimmed the panel, blocked the doorway with a cushion, and steadied the pot",
        "The wheel opened leaf by leaf and returned every paper star except one stuck to its crown.",
        "The rescued paper star rested beside the latched case like a small gold moon.",
    ),
    "bubble_sap": Scenario(
        "bubble_sap",
        "The clinic's air filter carried in a palm seed wrapped in a clear bubble of sap.",
        "The bubble showed rainbow colors whenever someone leaned close.",
        "breath or touch might inflate the unknown sap bubble",
        "The child whispered directly against its shimmering surface.",
        "BLOOP-bloop-FWUMP!",
        "The bubble swelled into a wobbling dome with the little palm floating inside.",
        "The dome drifted toward the room's ventilation grille.",
        "A label on the seed packet said that cool cloth safely shrank its sap.",
        "wrapped the dome loosely with a cool clinic cloth and steered it down",
        "The sap shrank to one harmless bead, and the palm settled upright in its pot.",
        "The final rainbow bead slid into the case and sparkled beside a neatly folded cloth.",
    ),
    "mirror_leaves": Scenario(
        "mirror_leaves",
        "A survey team brought back a palm whose leaves reflected faces like tiny mirrors.",
        "One leaf copied every silly expression the child made.",
        "the plant might copy sudden movement as well as faces",
        "The child waved both arms to test the funny reflection.",
        "FLIP-flap-CLACK!",
        "The mirrored leaves became a dozen sticky hands that copied every wave.",
        "The copying hands reached toward medicine drawers that needed to stay closed.",
        "When the clinician lowered one hand slowly, every leaf copied that too.",
        "made one slow lowering motion while the clinician slid the case underneath",
        "The copied motion folded all twelve hands safely into one quiet mirrored palm.",
        "Its last mirror held the reflection of two still hands and the securely closed drawers.",
    ),
    "magnetic_fronds": Scenario(
        "magnetic_fronds",
        "A maintenance worker found a sticky palm clinging to a harmless training magnet.",
        "Its fronds pointed eagerly toward every shiny object in the room.",
        "the magnet might pull the plant toward equipment if the pot was disturbed",
        "The child's metal zipper clicked against a reaching leaf.",
        "TING-ting-ZOOP!",
        "The fronds transformed into long green spirals that tugged spoons and clips through the air.",
        "A flying clip was headed toward the clinic's communication panel.",
        "The spirals ignored the wooden handle of the plant scoop.",
        "moved the training magnet into a padded drawer",
        "Without the magnet, the spirals released every metal object and shortened into soft leaves.",
        "The spoons lay in a straight silver row while the case latch clicked safely shut.",
    ),
    "shadow_bloom": Scenario(
        "shadow_bloom",
        "At rest hour, a palm arrived beneath an opaque cover for observation.",
        "A star-shaped shadow danced under the cloth.",
        "lifting the cover suddenly could startle a plant that changed in bright light",
        "The child peeked by raising one corner too fast.",
        "FWOOSH-tick-tick!",
        "The palm transformed into a wide black-and-green bloom that swallowed the reading lamp's glow.",
        "Its spreading shadow hid the clear path to the clinic door.",
        "A narrow beam from the clinician's penlight made the bloom turn and shrink.",
        "guided the bloom toward its case with the penlight while keeping the path to the door blocked",
        "The bloom folded around the small beam and became a palm no bigger than a mitten.",
        "A safe path of lamplight stretched from the quiet case all the way to the door.",
    ),
    "floating_spores": Scenario(
        "floating_spores",
        "A tiny palm sprouted unexpectedly in the clinic's tray of paper moons.",
        "Soft golden specks floated above it like dust in sunshine.",
        "the specks had not been identified and should not be scattered or breathed in",
        "The child blew at one speck to see whether it would dance.",
        "PUFF-piff-WHIRR!",
        "The palm became a feathery green umbrella and sent the specks swirling toward the vent.",
        "The unknown spores were spreading beyond the observation area.",
        "The feathery leaves leaned toward the clinic's small air collector.",
        "switched on the collector and guided every speck into a sample jar",
        "The umbrella closed, the air cleared, and the sealed jar gave the botanist a safe sample.",
        "One captured speck glowed inside the labeled jar beside a perfectly still green palm.",
    ),
    "warm_cocoa": Scenario(
        "warm_cocoa",
        "Someone set a mug of warm cocoa too near the clinic's newly delivered sticky palm.",
        "The plant leaned toward the sweet steam as if sniffing breakfast.",
        "warm sugary vapor could feed an unfamiliar plant too quickly",
        "The child nudged the mug closer to watch the leaves wiggle.",
        "GLUG-gloop-SPROING!",
        "The palm transformed into a tall syrupy stalk crowned with spinning fronds.",
        "Sticky drops began sailing toward the books and clean blankets.",
        "The stalk bent away when the clinician moved the warm mug behind a screen.",
        "moved the cocoa to a closed cupboard and caught the falling drops in a tray",
        "The stalk shortened, the fronds stopped spinning, and no supplies were spoiled.",
        "A clean blanket and a cooling mug sat far from the palm's dry, folded leaves.",
    ),
    "call_button": Scenario(
        "call_button",
        "The sticky palm was placed beside a disconnected practice call button during a safety lesson.",
        "One curious root curled around the bright red button.",
        "even practice equipment should be checked before a strange plant touched it",
        "The child pressed the button while the root was wrapped around it.",
        "BEEP-beep-SPLAT!",
        "The root transformed into a net of sticky cords that rang every practice bell at once.",
        "The cords tangled around the cart carrying the plant's clear case.",
        "The bells paused whenever the button was covered from the light.",
        "covered the button, loosened each cord, and asked the clinician to unplug the trainer",
        "The bells stopped, the cart rolled free, and the cords tucked themselves beneath the soil.",
        "The unplugged red button rested under its cover while the case stood ready beside it.",
    ),
    "paper_cranes": Scenario(
        "paper_cranes",
        "Children had left paper cranes in the clinic after practicing ways to name worried feelings.",
        "The new palm gently held one crane without tearing it.",
        "a calm-looking plant could still react unpredictably to being handled",
        "The child tried to trade the crane for another by touching a sticky leaf.",
        "CRINKLE-plip-ZIP!",
        "The palm transformed into a green bird shape and gathered every paper crane into its wings.",
        "The heavy paper wings tipped the pot toward the floor.",
        "The plant copied the steady rhythm when the clinician counted slowly to four.",
        "counted four slow breaths, supported the pot, and offered an empty tray",
        "The green bird placed every crane on the tray and unfolded into a balanced little palm.",
        "Twelve paper cranes circled the latched case, each wing smooth and uncreased.",
    ),
}

OPENINGS = [
    "On the morning watch", "Just before quiet hour", "During a routine safety check",
    "While distant stars slid past the window", "After the lunch bell",
    "As the ship crossed a band of blue light", "Near the end of evening watch",
    "When the clinic was calm", "During the crew's plant inspection", "Before story time",
]

REFLECTIONS = [
    "Curiosity is useful when it pauses long enough to gather evidence.",
    "Being brave can mean stopping, listening, and choosing a safer method.",
    "A warning is information to investigate, not a challenge to ignore.",
    "Careful questions can solve a mystery faster than a hurried hand.",
    "Mistakes become lessons when we notice the harm and repair it.",
    "Unknown living things deserve patience, distance, and gentle tools.",
    "Asking for help turned worry into a plan that everyone could follow.",
    "The best next step was not the fastest one, but the one supported by a clue.",
]

RESPONSES = [
    '"I acted before I understood the clue," {name} admitted. "Can we pause and make a plan?"',
    '"That was my mistake," {name} said. "Please help me protect the room and the plant."',
    '{name} took one steady breath. "I heard the warning, but I hurried. What should we observe first?"',
    '"I thought curious meant touching," {name} said, "but curious can mean looking and asking too."',
    '{name} stepped behind the safety line. "I will not chase it. Let us use the evidence."',
    '"The sound startled me," {name} said, "so I am going to slow down and listen now."',
    '{name} lowered both hands. "I caused this change. I want to help repair it safely."',
    '"I guessed instead of checking," {name} said. "Could we test one careful idea together?"',
    '{name} moved away from the danger. "First we make everyone safe; then we solve the mystery."',
    '"I can be responsible for my mistake," {name} said. "Show me how to help without rushing."',
]

OBSERVATION_LEADS = [
    "They watched which part moved first instead of guessing.",
    "They named the immediate danger, then searched for one change they could test safely.",
    "They compared what happened before and after the transformation.",
    "They kept the doorway clear and observed from behind the marked safety line.",
    "They listened for a pattern in the sounds and watched the leaves at the same time.",
    "They checked the room, the plant, and the nearby objects in that order.",
    "They agreed to change only one thing at a time so they could understand the result.",
    "They waited through one quiet moment and noticed a detail that rushing had hidden.",
]


@dataclass
class StoryParams:
    creature: str
    tool: str
    name: str
    role: str
    doctor: str
    trait: str
    scenario: str = "ceiling_vines"
    opening: int = 0
    reflection: int = 0
    response: int = 0
    observation: int = 0
    seed: Optional[int] = None


def _now(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _set(entity: Entity, key: str, val: float) -> None:
    entity.meters[key] = val


def _mem(entity: Entity, key: str, val: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + val


def _do_touch(world: World, hero: Entity, creature: Creature, narrate: bool = True) -> None:
    palm = world.get(creature.id)
    if ("touch", hero.id) in world.fired:
        return
    world.fired.add(("touch", hero.id))
    _mem(hero, "wonder", 1.0)
    _set(palm, "sticky", palm.meters.get("sticky", 0.0) + creature.sticky_level)
    _set(palm, "noise", palm.meters.get("noise", 0.0) + 1.0)
    if narrate:
        world.say(f'{hero.id} reached out, and the room went "{creature.sound}!"')


def _do_transform(world: World, creature: Creature, narrate: bool = True) -> None:
    palm = world.get(creature.id)
    if palm.meters.get("sticky", 0.0) < THRESHOLD:
        return
    if ("transform", palm.id) in world.fired:
        return
    world.fired.add(("transform", palm.id))
    _set(palm, "transforming", 1.0)
    _mem(palm, "restless", 1.0)
    if narrate:
        world.say(
            f"The sticky palm shivered, then changed into a {creature.transform_to} "
            f'with a "zip-zap" sound.'
        )


def _do_caution(world: World, doctor: Entity, hero: Entity, tool: Tool, narrate: bool = True) -> None:
    if ("caution", hero.id) in world.fired:
        return
    world.fired.add(("caution", hero.id))
    _mem(hero, "caution", 1.0)
    _mem(doctor, "calm", 1.0)
    if narrate:
        world.say(
            f'{doctor.id} lifted a calm hand and said, "No bare palms. Use the {tool.label}."'
        )


def _do_safe_move(world: World, hero: Entity, creature: Creature, tool: Tool, narrate: bool = True) -> None:
    if ("safe", hero.id) in world.fired:
        return
    world.fired.add(("safe", hero.id))
    palm = world.get(creature.id)
    _set(palm, "sticky", 0.0)
    _set(palm, "noise", 0.0)
    _set(palm, "caged", 1.0)
    _mem(hero, "relief", 1.0)
    _mem(hero, "confidence", 1.0)
    if narrate:
        world.say(
            f"{hero.id} took the {tool.label} and slid the palm into a clear case. "
            f"The squelch stopped, and the starship felt peaceful again."
        )


def tell(
    creature: Creature,
    tool: Tool,
    name: str,
    role: str,
    doctor_role: str,
    trait: str,
    scenario_id: str = "ceiling_vines",
    opening_id: int = 0,
    reflection_id: int = 0,
    response_id: int = 0,
    observation_id: int = 0,
) -> World:
    scenario = SCENARIOS[scenario_id]
    opening = OPENINGS[opening_id % len(OPENINGS)]
    reflection = REFLECTIONS[reflection_id % len(REFLECTIONS)]
    response = RESPONSES[response_id % len(RESPONSES)].format(name=name)
    observation = OBSERVATION_LEADS[observation_id % len(OBSERVATION_LEADS)]
    world = World(SpaceBase())
    hero = world.add(Entity(id=name, kind="character", type=role))
    doctor = world.add(Entity(id=doctor_role, kind="character", type=doctor_role))
    palm = world.add(Entity(
        id=creature.id,
        kind="thing",
        type=creature.label,
        label=creature.label,
        phrase=creature.phrase,
        contains_sticky=True,
    ))
    world.facts.update(
        hero=hero,
        doctor=doctor,
        palm=palm,
        creature=creature,
        tool=tool,
        scenario=scenario,
        clue=scenario.clue,
        safe_action=scenario.safe_action,
        outcome=scenario.result,
        lesson=reflection,
        response=response,
        observation=observation,
    )

    world.say(
        f"{opening}, {name}, a {trait} {role}, visited the starship's psychiatry room. "
        "It was an ordinary medical room where people could get help with thoughts, "
        "feelings, and ways to cope; today, its clear observation corner was also helping "
        "the crew inspect an unusual plant."
    )
    world.say(scenario.arrival)
    world.say(f"There stood {creature.phrase}. {scenario.temptation}")
    world.para()
    world.say(
        f'"Please wait," said the {doctor_role}. "We do not know this sticky palm yet. '
        f'Use the {tool.label}, because {scenario.warning_reason}."'
    )
    _mem(hero, "caution", 0.5)
    _mem(doctor, "calm", 1.0)
    world.fired.add(("warning", hero.id, scenario.id))
    world.say(scenario.mistake)
    world.say(f'At once the room answered, "{scenario.sound}"')
    _set(palm, "sticky", creature.sticky_level)
    _set(palm, "noise", 1.0)
    _set(palm, "transforming", 1.0)
    _mem(hero, "wonder", 1.0)
    _mem(hero, "worry", 0.5)
    world.fired.add(("mistake", hero.id, scenario.id))
    world.fired.add(("transform", palm.id, scenario.id))
    world.say(scenario.transformation)
    world.say(scenario.danger)
    world.para()
    world.say(f"{name} pulled back. {response}")
    world.say(
        f"The {doctor_role} agreed, and together they looked for evidence. "
        f"{observation} {scenario.clue}"
    )
    if tool.id == "gloves":
        tool_action = (
            f"After the {doctor_role} checked the fit, {name} put on the {tool.phrase}. "
            f"Keeping both hands slow and following the {doctor_role}'s directions, {name} "
        )
    else:
        tool_action = f"Keeping back from the moving leaves, {name} took {tool.phrase} and "
    action = scenario.safe_action
    if tool.id == "gloves":
        action = action.replace("with the scoop", "with a handled tray")
        action = action.replace("the scoop", "a handled tray")
    else:
        action = action.replace("with the scoop", "with it")
        action = action.replace("the scoop", "it")
    world.say(tool_action + action + ".")
    _set(palm, "sticky", 0.0)
    _set(palm, "noise", 0.0)
    _set(palm, "transforming", 0.0)
    _set(palm, "caged", 1.0)
    _mem(hero, "caution", 0.8)
    _mem(hero, "relief", 1.0)
    _mem(hero, "confidence", 0.7)
    world.fired.add(("safe", hero.id, scenario.id, tool.id))
    world.say(scenario.result)
    world.say(
        f'The {doctor_role} nodded. "{reflection}" The lesson was cautionary, but it was '
        f"also hopeful: {name} had repaired the mistake by observing, asking, and acting with care."
    )
    world.para()
    world.say(
        f"The sticky palm's transformation was over, and the clinic was safe again. "
        f"{scenario.ending}"
    )

    world.facts["resolved"] = True
    world.facts["cautionary"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for cid, creature in CREATURES.items():
        for tid, tool in TOOLS.items():
            if creature.sticky_level >= THRESHOLD and tool.id in {"scoop", "gloves"}:
                combos.append((cid, tid))
    return combos


def explain_rejection(creature: Creature, tool: Tool) -> str:
    return (
        f"(No story: the {tool.label} does not create a clear cautionary solution "
        f"for the {creature.label}. Try the scoop or gloves.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.tool:
        if (args.creature, args.tool) not in valid_combos():
            raise StoryError(explain_rejection(CREATURES[args.creature], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.creature is None or c[0] == args.creature)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    creature_id, tool_id = rng.choice(sorted(combos))
    return StoryParams(
        creature=creature_id,
        tool=tool_id,
        name=args.name or rng.choice(NAMES),
        role=args.role or rng.choice(ROLES),
        doctor=args.doctor or rng.choice(DOCTORS),
        trait=args.trait or rng.choice(TRAITS),
        scenario=rng.choice(sorted(SCENARIOS)),
        opening=rng.randrange(len(OPENINGS)),
        reflection=rng.randrange(len(REFLECTIONS)),
        response=rng.randrange(len(RESPONSES)),
        observation=rng.randrange(len(OBSERVATION_LEADS)),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c: Creature = f["creature"]
    s: Scenario = f["scenario"]
    return [
        f'Write a short space-adventure story for a young child about a "{c.label}" and the danger of {s.id.replace("_", " ")}.',
        f"Tell a cautionary story where {f['hero'].id} investigates a sticky palm safely in a psychiatry room on a starship.",
        f"Write a story with the sound effect {s.sound}, a strange transformation, and an evidence-based solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, doctor, palm, creature, tool = f["hero"], f["doctor"], f["palm"], f["creature"], f["tool"]
    scenario: Scenario = f["scenario"]
    return [
        QAItem(
            question=f"Who investigated the sticky palm after this happened: {scenario.arrival.rstrip('.')}?",
            answer=f"{hero.id}, a {hero.type} aboard the starship, investigated it with the {doctor.id}. They treated the plant's behavior as a safety puzzle, not as a judgment about any person.",
        ),
        QAItem(
            question=f"What sound followed when {scenario.mistake.rstrip('.').lower()}?",
            answer=f"The {creature.label} answered with \"{scenario.sound}\" and began its transformation. The sound came from the unusual plant, not from anyone receiving care in the psychiatry room.",
        ),
        QAItem(
            question=f"Why did the {doctor.id} ask {hero.id} to use the {tool.label}?",
            answer=f"The {doctor.id} explained that {scenario.warning_reason}. Using the {tool.label} gave them a safer way to learn what the sticky palm needed.",
        ),
        QAItem(
            question=f"How did the palm's transformation create danger during the {scenario.id.replace('_', ' ')} incident?",
            answer=f"{scenario.transformation} The change created a practical problem: {scenario.danger}",
        ),
        QAItem(
            question=f"Which clue helped {hero.id} choose the action that ended the {scenario.id.replace('_', ' ')} problem?",
            answer=f"{scenario.clue} From that evidence, {hero.id} and the {doctor.id} {scenario.safe_action}.",
        ),
        QAItem(
            question=f"What showed that {hero.id}'s safer plan had repaired the mistake?",
            answer=f"{scenario.result} {scenario.ending}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is psychiatry for?",
            answer="Psychiatry is medical care for mental health. Psychiatrists can help people understand and treat difficulties involving thoughts, feelings, behavior, or coping, just as other clinicians help with physical health.",
        ),
        QAItem(
            question="Why can sticky things be hard to hold?",
            answer="Sticky things cling to surfaces, so they can tug at fingers and make hands pull away slowly.",
        ),
        QAItem(
            question="What is a palm in a plant story?",
            answer="A palm can be a kind of tree or plant with long leaves that spread out like hands.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: meters={meters} memes={memes}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
sticky(X) :- palm(X), has_meter(X, sticky).
noisy(X) :- palm(X), has_meter(X, noise).
transforming(X) :- palm(X), has_meter(X, transforming).
cautionary(X) :- character(X), has_meter(X, caution).

safe_story(Creature, Tool) :- sticky_creature(Creature), safe_tool(Tool).
valid_story(Creature, Tool) :- sticky_creature(Creature), safe_tool(Tool), cautionary_theme.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = ["cautionary_theme."]
    for cid, c in CREATURES.items():
        if c.sticky_level >= THRESHOLD:
            lines.append(asp.fact("sticky_creature", cid))
        lines.append(asp.fact("palm", cid))
        lines.append(asp.fact("sound_of", cid, c.sound))
        lines.append(asp.fact("transforms_to", cid, c.transform_to))
    for tid, t in TOOLS.items():
        if t.id in {"scoop", "gloves"}:
            lines.append(asp.fact("safe_tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CREATURES[params.creature],
        TOOLS[params.tool],
        params.name,
        params.role,
        params.doctor,
        params.trait,
        params.scenario,
        params.opening,
        params.reflection,
        params.response,
        params.observation,
    )
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure cautionary story world.")
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--doctor", choices=DOCTORS)
    ap.add_argument("--trait", choices=TRAITS)
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


CURATED = [
    StoryParams(creature="sticky_palm", tool="scoop", name="Mina", role="girl", doctor="doctor", trait="curious"),
    StoryParams(creature="sticky_palm", tool="gloves", name="Arin", role="boy", doctor="medic", trait="careful"),
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
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
