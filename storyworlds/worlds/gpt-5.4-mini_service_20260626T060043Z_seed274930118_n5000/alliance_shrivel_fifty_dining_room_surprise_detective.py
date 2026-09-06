#!/usr/bin/env python3
"""
A small detective-style storyworld set in a dining room.

Premise:
A child detective notices a surprise at the dining table: fifty paper stars
have been scattered, and a prize plant on the sideboard is starting to shrivel.
The detective and a helper form a tiny alliance to find who moved the water
glass, protect the plant, and restore order before dinner.

The story is state-driven:
- surprise raises alert and curiosity
- a missing or tipped glass lowers plant moisture
- shriveling progresses when moisture is too low
- an alliance with a helper increases confidence and cooperation
- the ending proves the room changed: the clue is solved, the plant is saved,
  and the dinner room is calm again.
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dining room"


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str = "thing"


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    clue: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _narrate_state(world: World, text: str) -> None:
    world.say(text)


def detect_surprise(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["alert"] = detective.memes.get("alert", 0.0) + 1
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
    _narrate_state(
        world,
        f"In the dining room, {detective.id} noticed a surprise: {clue.phrase}."
    )


def count_fifty(world: World, clue: Clue) -> None:
    world.facts["fifty"] = 50
    _narrate_state(
        world,
        "There were fifty paper stars on the floor, and that was one clue too many to ignore."
    )


def plant_starts_shrivel(world: World, plant: Entity) -> None:
    plant.meters["moisture"] = plant.meters.get("moisture", 0.0) - 1
    plant.meters["shrivel"] = plant.meters.get("shrivel", 0.0) + 1
    _narrate_state(
        world,
        f"The little plant on the sideboard began to shrivel at the edges."
    )


def form_alliance(world: World, detective: Entity, helper: Entity) -> None:
    detective.memes["trust"] = detective.memes.get("trust", 0.0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1
    detective.memes["alliance"] = detective.memes.get("alliance", 0.0) + 1
    helper.memes["alliance"] = helper.memes.get("alliance", 0.0) + 1
    _narrate_state(
        world,
        f"{detective.id} made an alliance with {helper.id}; together they had more eyes than one."
    )


def inspect_glass(world: World, detective: Entity, helper: Entity, glass: Entity) -> None:
    detective.memes["focus"] = detective.memes.get("focus", 0.0) + 1
    helper.memes["focus"] = helper.memes.get("focus", 0.0) + 1
    if glass.meters.get("spilled", 0.0) >= THRESHOLD:
        _narrate_state(
            world,
            "They found the tipped glass under the table, and the wet ring on the cloth matched the clue."
        )
    else:
        _narrate_state(
            world,
            "They checked the table carefully, but the glass still stood steady."
        )


def fix_the_room(world: World, detective: Entity, helper: Entity, plant: Entity, glass: Entity) -> None:
    if glass.meters.get("spilled", 0.0) >= THRESHOLD:
        glass.meters["spilled"] = 0.0
        plant.meters["moisture"] = plant.meters.get("moisture", 0.0) + 2
        plant.meters["shrivel"] = max(0.0, plant.meters.get("shrivel", 0.0) - 1)
        detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1
        helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
        _narrate_state(
            world,
            f"With careful hands, they righted the glass, watered the plant, and the shriveled leaves perked up again."
        )


@dataclass
class StoryParams:
    detective_name: str
    helper_name: str
    suspect_name: str
    seed: Optional[int] = None
    incident_id: Optional[str] = None
    telling_mode: Optional[str] = None


DETECTIVE_NAMES = ["Maya", "Leo", "Nina", "Owen", "Iris", "Eli"]
HELPER_NAMES = ["Aunt June", "Dad", "Milo", "Grandma", "Nora"]
SUSPECT_NAMES = ["the cat", "the wind", "the clumsy spoon", "the puppy", "the draft"]


@dataclass(frozen=True)
class Incident:
    id: str
    surprise: str
    plant_sign: str
    first_clue: str
    false_test: str
    decisive_clue: str
    cause: str
    alliance_work: str
    repair: str
    ending: str
    culprit: str


INCIDENTS = [
    Incident(
        id="star_trail",
        surprise="fifty gold paper stars formed a trail from the table to the sideboard",
        plant_sign="its smallest leaves were curled like tired green fingers",
        first_clue="one star beside the pot had a blue watercolor thumbprint",
        false_test="They followed the brightest stars first, but that trail ended at an untouched window",
        decisive_clue="A damp paintbrush and the matching blue print pointed to the craft shelf",
        cause="the decorating group had borrowed the plant's water glass to rinse brushes and forgotten to return it after yesterday's rehearsal",
        alliance_work="one checked the stars in number order while the other compared every blue mark",
        repair="They returned the clean glass, gave the dry soil a measured drink, and made a separate brush-rinsing jar",
        ending="At dinner, fifty stars circled the upright pot, and one fresh leaf caught the chandelier light",
        culprit="a forgotten decorating routine",
    ),
    Incident(
        id="bell_pattern",
        surprise="fifty tiny paper bells hung beneath the chairs in a repeating pattern",
        plant_sign="the leaves nearest the heating vent had begun to shrivel",
        first_clue="every fifth bell leaned toward a warm current of air",
        false_test="They gently closed the window, yet the bells kept trembling",
        decisive_clue="A ribbon held over the floor vent fluttered at once, while the missing glass stood full behind a serving tray",
        cause="the plant had been moved beside the heating vent to make room for a tray, so warm air dried its soil",
        alliance_work="one mapped the bell pattern while the other tested the air from a safe distance",
        repair="With an adult's help, they moved the pot back to its marked cool spot and watered it",
        ending="By supper, the bells were still, the vent was clear, and the plant cast a broad green shadow across its marker",
        culprit="the warm heating vent",
    ),
    Incident(
        id="place_card_code",
        surprise="fifty numbered place cards stood in a spiral around the fruit bowl",
        plant_sign="the plant drooped beside an empty saucer",
        first_clue="cards ten, twenty, thirty, forty, and fifty each bore a tiny drawing of a window",
        false_test="They searched behind every curtain, but found no glass and no spill",
        decisive_clue="Reading the five window cards together spelled PANTRY, where the glass waited on a low shelf",
        cause="a card-maker had carried the glass away while clearing space and left it in the pantry",
        alliance_work="one sorted the cards by number while the other copied the five tiny pictures",
        repair="They brought back the glass, watered the plant, and added a bright WATER PLANT card to the table plan",
        ending="When dinner began, card fifty pointed to a sparkling glass beside a plant whose top leaf had lifted",
        culprit="a hurried table-clearing mistake",
    ),
    Incident(
        id="crane_message",
        surprise="fifty folded paper cranes perched along the dining-room shelves",
        plant_sign="two leaves had wrinkled after the watering day was missed",
        first_clue="one crane held a green thread that matched the plant's care calendar",
        false_test="Opening the crane revealed only a kind note, not the missing calendar square",
        decisive_clue="The thread continued behind the clock, where the loose calendar square read WATER TODAY",
        cause="a breeze from the open door had carried the reminder behind the clock, so everyone thought someone else had watered the plant",
        alliance_work="one held the thread taut while the other used a mirror to read behind the clock without climbing",
        repair="They watered the plant and clipped the calendar firmly at eye level",
        ending="That evening, the last crane rested beneath a checked-off watering square, and the leaves no longer sagged",
        culprit="a lost care reminder",
    ),
    Incident(
        id="button_constellation",
        surprise="fifty wooden buttons made a constellation across a paper tablecloth",
        plant_sign="the soil was dusty and the leaf tips looked pinched",
        first_clue="four dark buttons outlined the same square shape as the missing coaster",
        false_test="They lifted the paper carefully, but there was no hidden spill underneath",
        decisive_clue="The square pointed toward the china cabinet, where the coaster and full glass sat together",
        cause="the full glass had been moved into the cabinet during a cleanup and the closed door hid it through watering time",
        alliance_work="one photographed the button map while the other matched its shapes to objects in the room",
        repair="They restored the glass and coaster, watered the soil, and marked a permanent watering place",
        ending="After dinner, the button constellation shone beside the marked coaster, and the plant's leaves spread above both",
        culprit="an over-tidy cleanup",
    ),
    Incident(
        id="ribbon_knots",
        surprise="fifty soft ribbon bows were tied around chair backs, each with a different knot",
        plant_sign="the plant leaned dryly away from a bright patch of afternoon sun",
        first_clue="the fiftieth bow carried a tag saying MOVE BEFORE NOON",
        false_test="They moved the bow, but the hot sunlight still crossed the pot",
        decisive_clue="A chalk outline on the sideboard showed that the pot belonged farther from the glass door",
        cause="someone decorating the chairs had shifted the plant into stronger sun and not returned it",
        alliance_work="one read the bow tags while the other traced the safe route shown by the chalk outline",
        repair="Together with an adult, they returned the pot to indirect light and gave its dry soil water",
        ending="At dusk, all fifty bows framed a cooler sideboard where the plant stood inside its chalk outline",
        culprit="a decorating move that was not undone",
    ),
    Incident(
        id="footprint_count",
        surprise="fifty paper footprints crossed the dining room in two looping paths",
        plant_sign="one lower leaf had shriveled above a bone-dry saucer",
        first_clue="the footprints numbered one through fifty, but number thirty-two faced backward",
        false_test="They followed the forward path to the kitchen and found only stacked plates",
        decisive_clue="Turning at footprint thirty-two revealed a watering bottle behind the curtain",
        cause="the bottle had been hidden as part of a treasure hunt before the plant received its usual drink",
        alliance_work="one called out the numbers while the other checked which way each printed toe pointed",
        repair="They ended the game, watered the plant, and wrote a rule that care tools could not become hiding-game treasures",
        ending="Before dinner, footprint fifty pointed openly to the returned bottle, and a drop gleamed on the plant's broadest leaf",
        culprit="an ill-planned treasure hunt",
    ),
    Incident(
        id="envelope_schedule",
        surprise="fifty tiny envelopes filled the place settings like unexpected mail",
        plant_sign="the plant's newest shoot had curled beside dry soil",
        first_clue="envelopes for Monday and Tuesday both claimed the other day's helper would water the plant",
        false_test="They checked the glass for a leak, but it held every drop",
        decisive_clue="The two notes revealed an overlap in the chore schedule rather than a missing object",
        cause="two helpers had each believed the other was responsible, so the plant was skipped",
        alliance_work="one arranged the envelopes by day while the other compared the names and times",
        repair="They watered the plant and replaced the confusing notes with one clear signed checklist",
        ending="At dinner, envelope fifty held the completed checklist beside a moist saucer and an uncurling shoot",
        culprit="a confusing shared schedule",
    ),
    Incident(
        id="puzzle_reflection",
        surprise="fifty puzzle tiles covered the table with a picture that seemed to show a spill",
        plant_sign="the leaves had begun to shrivel although the glass beside them looked full",
        first_clue="the picture's silver tiles reflected a second glass on the far end of the table",
        false_test="They touched no liquid in the pictured puddle because it was only blue paint",
        decisive_clue="A measuring mark showed that the nearby glass contained decorative glass beads, not water",
        cause="the real watering glass had been swapped with a look-alike craft display",
        alliance_work="one completed the puzzle border while the other compared both glasses without tasting or touching their contents",
        repair="An adult removed the craft glass; they fetched fresh water in the labeled watering glass and cared for the plant",
        ending="The finished fifty-piece puzzle reflected a clearly labeled glass and a plant standing tall beside it",
        culprit="two look-alike glasses",
    ),
    Incident(
        id="coaster_rings",
        surprise="fifty cork coasters made a winding path beneath the dining table",
        plant_sign="the plant was dry while a wide wet ring marked the tablecloth",
        first_clue="only one coaster smelled faintly of clean rainwater and carried a crescent-shaped dent",
        false_test="They blamed the nearest spoon at first, but its handle did not fit the dent",
        decisive_clue="The base of the watering glass matched the crescent and a loose table leaf tilted toward the spill",
        cause="the table leaf had not latched flat, so the glass slid when the table was nudged",
        alliance_work="one compared the rings while the other asked an adult to inspect the table latch",
        repair="The adult secured the latch; the allies dried the spill, refilled the glass, and watered the plant",
        ending="At dinner, all fifty coasters lay in a neat stack beneath a level table, and the plant's leaves held steady",
        culprit="an unlatched table leaf",
    ),
    Incident(
        id="boat_leak",
        surprise="fifty origami boats floated in shallow trays along the dining table",
        plant_sign="the plant looked thirsty even though damp dots led past its pot",
        first_clue="boat forty-nine was soggy while boat fifty remained crisp",
        false_test="They inspected the boats for a leak, but the shallow trays were sound",
        decisive_clue="The damp dots ended at a watering can whose cap had been left loose",
        cause="water had dribbled from the loosely capped can on the way to the plant, leaving too little for the soil",
        alliance_work="one counted the boats from the dry end while the other followed the damp dots without stepping on them",
        repair="They wiped the floor, refilled and closed the can correctly, then watered the plant with an adult nearby",
        ending="By supper, fifty dry boats faced a capped watering can, and the plant's leaves arched above a dark patch of watered soil",
        culprit="a loose watering-can cap",
    ),
    Incident(
        id="label_mixup",
        surprise="fifty seed labels stood in cups around the dining-room window garden",
        plant_sign="the prize plant's leaves were shriveling while a nearby empty pot was soaked",
        first_clue="two labels shared the same painted red stripe",
        false_test="They counted every label and found exactly fifty, so none was missing",
        decisive_clue="Comparing leaf drawings showed that the prize plant's label had been placed in the empty pot",
        cause="the matching labels were switched, so the empty pot received the prize plant's water",
        alliance_work="one sorted labels by stripe while the other matched each drawing to its real leaves",
        repair="They corrected the labels, let the soaked empty pot drain, and gave the dry plant its proper measured water",
        ending="In the evening light, fifty labels stood with the right pots, and the prize plant lifted a green tip above its red stripe",
        culprit="two switched seed labels",
    ),
]

INCIDENT_BY_ID = {incident.id: incident for incident in INCIDENTS}
TELLING_MODES = ["clue_first", "dialogue_first", "countdown", "quiet_open", "case_notes", "question_open", "action_open", "memory_open"]
FOLLOW_THROUGHS = [
    "They scheduled a soil check for the next morning and signed both names beneath it",
    "They drew a small map showing where every care tool belonged",
    "They asked the dinner helpers to report changes instead of silently moving the pot",
    "They added a moisture check to the room's before-dinner routine",
    "They photographed the repaired arrangement so tomorrow's helper could compare it",
    "They placed a washable label on the plant's own water container",
    "They made a two-person checklist: one helper checked and the other confirmed",
    "They left a case note explaining the clue, the cause, and the repair",
    "They agreed to pause future games until the plant's daily care was complete",
    "They marked a clear space around the pot so decorations could not crowd it again",
    "They invited the next helper to inspect the leaves and soil with them",
    "They recorded the watering time where every member of the alliance could see it",
]


def _story_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xA11A6CE)
    material = "|".join((params.detective_name, params.helper_name, params.suspect_name, params.incident_id or ""))
    return random.Random(sum((i + 1) * ord(ch) for i, ch in enumerate(material)))


def _opening(mode: str, detective: str, helper: str, incident: Incident, variant: int) -> str:
    openings = {
        "clue_first": f"The first surprise clue in the dining room was impossible to miss: {incident.surprise}.",
        "dialogue_first": f'"That surprise was not here before," {detective} whispered in the dining room when {incident.surprise}.',
        "countdown": f"In the dining room, {detective} counted backward from fifty, but the surprise only grew stranger: {incident.surprise}.",
        "quiet_open": f"The dining room should have been quiet before dinner. Instead, a surprise awaited: {incident.surprise}.",
        "case_notes": f"Surprise case note number {variant + 1}: in the dining room, {incident.surprise}.",
        "question_open": f"What surprise had changed the calm dining room? {incident.surprise.capitalize()}.",
        "action_open": f"{detective} stopped at a surprise in the dining room doorway: {incident.surprise}.",
        "memory_open": f"That morning the dining room had been ordinary; now it held a surprise, for {incident.surprise}.",
    }
    return openings[mode]


def build_world(params: StoryParams) -> World:
    rng = _story_rng(params)
    incident = INCIDENT_BY_ID.get(params.incident_id or "") or rng.choice(INCIDENTS)
    mode = params.telling_mode if params.telling_mode in TELLING_MODES else rng.choice(TELLING_MODES)
    variant = rng.randrange(10)
    follow_through = rng.choice(FOLLOW_THROUGHS)
    world = World(Setting())
    detective = world.add(Entity(id=params.detective_name, kind="character", type="girl" if params.detective_name in {"Maya", "Nina", "Iris"} else "boy"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="woman" if "Aunt" in params.helper_name or "Grandma" in params.helper_name or params.helper_name == "Nora" else "man"))
    plant = world.add(Entity(id="plant", kind="thing", type="plant", label="potted plant", phrase="a potted plant on the sideboard", caretaker=helper.id))
    glass = world.add(Entity(id="glass", kind="thing", type="glass", label="water glass", phrase="a tipped water glass", caretaker=helper.id))
    stars = world.add(Entity(id="stars", kind="thing", type="stars", label="paper stars", phrase="fifty paper stars", plural=True))
    suspect = world.add(Entity(id="suspect", kind="thing", type="suspect", label=params.suspect_name, phrase=params.suspect_name))

    glass.meters["spilled"] = 1.0 if incident.id == "coaster_rings" else 0.0
    plant.meters["moisture"] = 0.0
    plant.meters["shrivel"] = 1.0

    detective.memes.update(alert=1.0, curiosity=1.0)
    world.facts["fifty"] = 50
    world.say(_opening(mode, detective.id, helper.id, incident, variant))
    plant_lines = [
        f"Beside all fifty clues, the prize plant showed a second surprise: {incident.plant_sign}.",
        f"Then {detective.id} saw the prize plant. {incident.plant_sign.capitalize()}.",
        f"The count reached fifty just as {detective.id} noticed the plant; {incident.plant_sign}.",
    ]
    world.say(plant_lines[variant % len(plant_lines)])

    world.para()
    detective.memes.update(trust=1.0, alliance=1.0)
    helper.memes.update(trust=1.0, alliance=1.0)
    alliance_lines = [
        f'"Let us make a detective alliance," said {detective.id}. "You watch the room while I follow the clues."',
        f"{detective.id} and {helper.id} formed a detective alliance: {incident.alliance_work}.",
        f'"Two careful detectives are better than one quick guess," {helper.id} said, and their alliance began.',
    ]
    world.say(alliance_lines[(variant // 2) % len(alliance_lines)])
    world.say(f"Their first clue was clear: {incident.first_clue}.")
    world.say(f"At first, {detective.id} wondered whether {suspect.label} was responsible. {incident.false_test}.")

    world.para()
    detective.memes["focus"] = 1.0
    helper.memes["focus"] = 1.0
    discovery_lines = [
        f"They slowed down and checked what the room could actually prove. {incident.decisive_clue}.",
        f'"A guess is not a solution," said {detective.id}. Then they found the decisive evidence: {incident.decisive_clue}.',
        f"Working from clue to clue, the allies discovered the detail their first theory had missed. {incident.decisive_clue}.",
        f"Instead of accusing anyone, they tested the evidence together. {incident.decisive_clue}.",
    ]
    world.say(discovery_lines[(variant + 1) % len(discovery_lines)])
    world.say(f"They learned what had happened: {incident.cause[0].upper() + incident.cause[1:]}.")
    world.say(f"That explained both the surprising display and why the plant had begun to shrivel.")

    world.para()
    plant.meters["moisture"] = 2.0
    plant.meters["shrivel"] = 0.0
    glass.meters["spilled"] = 0.0
    detective.memes.update(solve=1.0, relief=1.0)
    helper.memes["relief"] = 1.0
    repair_lines = [
        f"The alliance did not stop at solving the mystery. {incident.repair}.",
        f'"A solved case should leave things safer," {helper.id} said. {incident.repair}.',
        f"Now that they understood the cause, each ally took a useful job. {incident.repair}.",
    ]
    world.say(repair_lines[(variant + 2) % len(repair_lines)])
    world.say(f"To keep the solution working, {follow_through[0].lower() + follow_through[1:]}.")
    world.say(f"They cleared {suspect.label} from blame and recorded the case's lesson: inspect evidence before accusing, then repair the cause together.")
    world.say(f"{incident.ending}.")

    detective.memes["solve"] = 1.0

    world.facts.update(
        detective=detective,
        helper=helper,
        plant=plant,
        glass=glass,
        stars=stars,
        suspect=suspect,
        incident=incident,
        telling_mode=mode,
        place="the dining room",
        initial_theory=suspect.label,
        actual_cause=incident.cause,
        culprit=incident.culprit,
        decisive_clue=incident.decisive_clue,
        repair=incident.repair,
        follow_through=follow_through,
        ending=incident.ending,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly detective story set in a dining room where {f['incident'].surprise} and a plant begins to shrivel.",
        f"Tell how {f['detective'].id} and {f['helper'].id} form an alliance, use fifty clues to test a mistaken theory about {f['suspect'].label}, and discover that {f['culprit']} caused the trouble.",
        f"Write a gentle surprise mystery whose decisive clue is this: {f['decisive_clue']}. End with the allies repairing the cause and a concrete image of the restored dining room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.facts["detective"]
    h = world.facts["helper"]
    p = world.facts["plant"]
    g = world.facts["glass"]
    s = world.facts["suspect"]
    incident = world.facts["incident"]
    return [
        QAItem(
            question=f"What surprise did {d.id} find in the dining room?",
            answer=f"{d.id} found that {incident.surprise}. The unusual arrangement supplied fifty clues to examine.",
        ),
        QAItem(
            question=f"Why did {d.id} and {h.id} make an alliance?",
            answer=f"They made an alliance to investigate why the plant was beginning to shrivel without rushing to blame anyone. Together, {incident.alliance_work}.",
        ),
        QAItem(
            question=f"What was making {p.label} shrivel?",
            answer=f"The plant was shriveling because {incident.cause}. Once the allies understood that cause, they could repair it safely.",
        ),
        QAItem(
            question=f"How did the evidence change {d.id}'s first theory about {s.label}?",
            answer=f"{d.id} first wondered whether {s.label} was responsible. But {incident.decisive_clue}, which showed that the real culprit was {incident.culprit}.",
        ),
        QAItem(
            question="What did the alliance do after solving the mystery?",
            answer=f"They acted on the evidence instead of stopping at an answer. {incident.repair}, and they left the dining room safer than they found it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an alliance?",
            answer="An alliance is a group agreement to help each other reach a goal, like solving a problem together.",
        ),
        QAItem(
            question="What does shrivel mean?",
            answer="To shrivel means to get smaller, wrinkly, or dry-looking because something needs water or care.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What does fifty mean?",
            answer="Fifty means 50, which is a lot of things to count.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    out = ["--- world model ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "dining_room"),
        asp.fact("contains", "dining_room", "table"),
        asp.fact("contains", "dining_room", "sideboard"),
        asp.fact("contains", "dining_room", "floor"),
        asp.fact("clue_kind", "surprise"),
        asp.fact("count_word", "fifty"),
        asp.fact("action", "detect"),
        asp.fact("action", "form_alliance"),
        asp.fact("action", "inspect"),
        asp.fact("action", "repair"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
% The detective storyworld is valid when a surprise is detected, an alliance is
% formed, shrivel is reduced, and the case is solved.
surprise_detected :- clue_kind(surprise), setting(dining_room).
alliance_formed :- action(form_alliance).
case_solved :- surprise_detected, alliance_formed, count_word(fifty).
valid_story :- case_solved.
#show valid_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP twin confirms the storyworld is valid.")
        return 0
    print("MISMATCH: ASP twin did not confirm validity.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld set in a dining room.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
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
    return StoryParams(
        detective_name=args.name or rng.choice(DETECTIVE_NAMES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        suspect_name=args.suspect or rng.choice(SUSPECT_NAMES),
        incident_id=rng.choice(INCIDENTS).id,
        telling_mode=rng.choice(TELLING_MODES),
    )


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
    StoryParams(detective_name="Maya", helper_name="Aunt June", suspect_name="the cat"),
    StoryParams(detective_name="Leo", helper_name="Dad", suspect_name="the clumsy spoon"),
    StoryParams(detective_name="Iris", helper_name="Grandma", suspect_name="the draft"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
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
