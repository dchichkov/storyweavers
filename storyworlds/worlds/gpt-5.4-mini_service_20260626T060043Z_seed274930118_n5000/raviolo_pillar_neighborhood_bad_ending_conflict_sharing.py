#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORYWORLDS_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "queen", "goddess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "king", "god"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    name: str = "the neighborhood"
    glow: str = "soft lamplight"


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    sacred: bool = False


@dataclass
class StoryParams:
    setting: str
    treasure: str
    name_a: str
    name_b: str
    role_a: str
    role_b: str
    incident: str = "windy_awning"
    telling_mode: str = "straight"
    sharing_plan: str = "two_plates"
    follow_through: str = "practice_run"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: callable


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("A")
    b = world.entities.get("B")
    t = world.entities.get("treasure")
    if not a or not b or not t:
        return out
    if a.memes.get("want", 0) >= 1 and b.memes.get("want", 0) >= 1:
        sig = ("tension",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["conflict"] = a.memes.get("conflict", 0) + 1
            b.memes["conflict"] = b.memes.get("conflict", 0) + 1
            incident = world.facts["incident"]
            out.append(incident["tension"])
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    t = world.entities.get("treasure")
    if not t or t.held_by is None:
        return out
    holder = world.entities[t.held_by]
    if holder.memes.get("conflict", 0) >= 1 and holder.meters.get("shake", 0) >= 1:
        sig = ("drop",)
        if sig not in world.fired:
            world.fired.add(sig)
            t.held_by = None
            t.meters["fallen"] = 1
            t.meters["shareable"] = 0
            out.append(world.facts["incident"]["loss"])
    return out


def _r_bad_ending(world: World) -> list[str]:
    out: list[str] = []
    t = world.entities.get("treasure")
    if not t or t.meters.get("fallen", 0) < 1:
        return out
    sig = ("bad_end",)
    if sig not in world.fired:
        world.fired.add(sig)
        out.append(world.facts["incident"]["consequence"])
    return out


RULES = [Rule("tension", _r_tension), Rule("drop", _r_drop), Rule("bad_end", _r_bad_ending)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            msgs = rule.apply(world)
            if msgs:
                changed = True
                produced.extend(msgs)
    if narrate:
        for msg in produced:
            world.say(msg)
    return produced


def predict_fall(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    t = sim.entities["treasure"]
    return t.meters.get("fallen", 0) >= 1


def build_story(setting: Setting, treasure: Treasure, params: StoryParams) -> World:
    world = World(setting)
    a = world.add(Entity(id="A", kind="character", type=params.role_a, label=params.name_a))
    b = world.add(Entity(id="B", kind="character", type=params.role_b, label=params.name_b))
    t = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure.type,
        label=treasure.label,
        phrase=treasure.phrase,
        owner=a.id,
        caretaker=b.id,
        held_by=a.id,
    ))
    incident = INCIDENTS[params.incident]
    mode = TELLING_MODES[params.telling_mode]
    plan = SHARING_PLANS[params.sharing_plan]
    world.facts.update(
        hero_a=a,
        hero_b=b,
        treasure=t,
        setting=setting,
        treasure_cfg=treasure,
        incident=incident,
        incident_key=params.incident,
        telling_mode=params.telling_mode,
        sharing_plan=plan,
        sharing_plan_key=params.sharing_plan,
        follow_through=FOLLOW_THROUGHS[params.follow_through],
        follow_through_key=params.follow_through,
    )

    opening = mode["opening"].format(
        setting=setting.name,
        glow=setting.glow,
        a=a.label,
        b=b.label,
        premise=incident["premise"],
    )
    world.say(opening)
    world.say(
        f"Beside the old pillar waited {t.phrase}. The neighborhood had provided it for "
        f"{plan['purpose']}, so it was meant to be shared."
    )
    world.para()
    world.say(incident["conflict"].format(a=a.label, b=b.label))
    world.say("What began as a question about portions became a conflict about sharing.")
    world.say(mode["thought"].format(a=a.label, b=b.label, clue=incident["clue"]))
    a.memes["want"] = 1
    b.memes["want"] = 1
    propagate(world, narrate=True)
    world.para()
    a.meters["shake"] = 1
    if predict_fall(world):
        world.say(incident["dialogue"].format(a=a.label, b=b.label))
        world.say(
            f"{b.label} proposed {plan['proposal']}, but {a.label} tried {incident['mistake']} instead."
        )
        world.say(incident["clue_action"].format(a=a.label, b=b.label))
        a.meters["shake"] = 1
        propagate(world, narrate=True)
    world.para()
    world.say(incident["safe_response"].format(a=a.label, b=b.label))
    world.say(
        f"They could not undo the lost raviolo. That was the bad ending for this little feast, "
        f"and neither figure pretended otherwise."
    )
    world.say(mode["reflection"].format(a=a.label, b=b.label, lesson=incident["lesson"]))
    world.para()
    world.say(incident["repair"].format(a=a.label, b=b.label, plan=plan["repair"]))
    world.say(FOLLOW_THROUGHS[params.follow_through].format(a=a.label, b=b.label))
    world.say(mode["ending"].format(image=incident["ending_image"], a=a.label, b=b.label))
    a.memes["sharing"] = 1
    b.memes["sharing"] = 1
    a.memes["lesson_learned"] = 1
    b.memes["lesson_learned"] = 1
    world.facts.update(
        clue=incident["clue"],
        bad_ending=incident["bad_ending"],
        lesson=incident["lesson"],
        safe_action=incident["safe_action"],
        follow_through_text=FOLLOW_THROUGHS[params.follow_through].format(a=a.label, b=b.label),
    )
    return world


SETTINGS = {
    "neighborhood": Setting(name="the neighborhood", glow="soft lamplight"),
    "courtyard": Setting(name="the courtyard", glow="moonlit air"),
}

TREASURES = {
    "raviolo": Treasure(label="raviolo", phrase="one golden raviolo", type="raviolo", sacred=True),
}

ROLES = ["girl", "boy", "mother", "father", "child", "hermit"]
NAMES = ["Mira", "Jon", "Sela", "Tarin", "Ivo", "Nia", "Pero", "Luma"]


INCIDENTS = {
    "windy_awning": {
        "premise": "a block supper began just as a gust worried the striped awning",
        "conflict": "{a} wanted to carry the raviolo indoors; {b} insisted the serving turn should begin outside.",
        "clue": "the awning cord was snapping in the wind",
        "tension": "Their disagreement grew louder while the awning cord snapped above the table.",
        "dialogue": '"The wind is the real problem," said {b}. "We can decide fairly once the food is sheltered."',
        "mistake": "to guard the plate with one elbow while gripping the whole raviolo",
        "clue_action": "{a} looked up at the whipping cloth, but the delayed choice had already left the plate exposed.",
        "loss": "A gust flipped the paper plate, and the raviolo rolled into a rain grate.",
        "consequence": "The grate was closed and the food was dirty, so a responsible adult marked it for disposal.",
        "safe_response": "{a} and {b} stepped away from the grate and asked adults to secure the awning; neither reached into the drain.",
        "repair": "Together they posted a wind plan and {plan} before the next block supper.",
        "ending_image": "the secured awning resting quietly above two empty, equal place mats",
        "bad_ending": "the raviolo blew into a rain grate and could not be eaten",
        "lesson": "fairness starts with noticing a shared danger before defending a share",
        "safe_action": "step away from the grate and ask adults to secure the awning",
    },
    "rain_gutter": {
        "premise": "neighbors gathered after a shower while water ticked through a gutter",
        "conflict": "{a} claimed the dry seat; {b} said the raviolo should go first to whoever moved the table.",
        "clue": "drops were landing closer and closer to the serving cloth",
        "tension": "They argued about credit while a dark wet circle spread across the cloth.",
        "dialogue": '"Listen to the drip," said {b}. "The plate needs a dry place before either of us chooses."',
        "mistake": "to slide the dish alone without setting it down",
        "clue_action": "{b} pointed to the widening wet circle and called for an adult to check the gutter.",
        "loss": "A cold splash struck the open pasta, soaking it with roof runoff.",
        "consequence": "The raviolo was no longer safe to eat, and the planned tasting had to be canceled.",
        "safe_response": "They left the gutter and pillar untouched, moved behind the marked dry line, and told the building caretaker.",
        "repair": "They drew a rain-day table map and {plan} for the next meal.",
        "ending_image": "raindrops tapping an empty covered dish beneath a freshly inspected gutter",
        "bad_ending": "roof runoff spoiled the raviolo and canceled the tasting",
        "lesson": "sharing includes protecting food together instead of arguing over who deserves it",
        "safe_action": "move behind the dry line and notify the building caretaker",
    },
    "chalk_queue": {
        "premise": "a chalk festival filled the pavement with arrows and bright squares",
        "conflict": "{a} read one arrow as a first-place mark; {b} read it as the start of the sharing queue.",
        "clue": "the arrow connected to a faded circle labeled WAIT",
        "tension": "Each defended a different reading, and their voices crowded out the festival music.",
        "dialogue": '"Let us trace the whole sign before we decide," said {b}. "One arrow is not the whole message."',
        "mistake": "to lift the raviolo as proof that the arrow pointed to one winner",
        "clue_action": "{a} followed the chalk line too late and found the faded waiting circle.",
        "loss": "The tilted plate sent the raviolo onto a patch of chalk dust and shoe grit.",
        "consequence": "The food had to be discarded, and the festival's tasting bell rang without them.",
        "safe_response": "They set the dirty food aside for an adult to discard and kept everyone from stepping on it.",
        "repair": "They redrew the full queue with the organizer and {plan} for future tastings.",
        "ending_image": "a clear chalk path curling around the pillar toward two waiting spots",
        "bad_ending": "the raviolo landed in chalk dust and missed the tasting",
        "lesson": "a partial clue should be checked before it becomes a reason to quarrel",
        "safe_action": "set the dirty food aside and ask the festival organizer for help",
    },
    "wobbly_table": {
        "premise": "the neighborhood book swap included a tiny refreshment table",
        "conflict": "{a} wanted the raviolo beside the adventure books; {b} wanted it near the picture books.",
        "clue": "one table leg clicked whenever somebody leaned near it",
        "tension": "Their tug over the table hid the small click coming from its loose folding leg.",
        "dialogue": '"Stop moving it," said {b}. "That click means we need the organizer."',
        "mistake": "to steady the plate while continuing to pull the table",
        "clue_action": "{a} finally heard the click and let go, but the folding leg had already shifted.",
        "loss": "The tabletop dipped, and the raviolo slid onto the dusty book-return mat.",
        "consequence": "The snack was lost, and the refreshment table closed until an adult replaced it.",
        "safe_response": "{a} and {b} backed away, warned the next visitor, and asked the organizer to fold and remove the faulty table.",
        "repair": "They made a shared display plan and {plan} beside a stable replacement table.",
        "ending_image": "returned books standing neatly beside a folded OUT OF USE sign",
        "bad_ending": "a loose table leg sent the raviolo onto a dusty mat",
        "lesson": "winning a location matters less than stopping when equipment gives a warning",
        "safe_action": "back away and ask the organizer to remove the faulty table",
    },
    "ant_trail": {
        "premise": "a garden-club meeting paused beside the pillar for a snack",
        "conflict": "{a} wanted to save the raviolo for later; {b} wanted to divide it before the meeting resumed.",
        "clue": "a thin ant trail curved toward the uncovered plate",
        "tension": "The longer they debated, the closer the ants came to the uncovered food.",
        "dialogue": '"Cover it first," said {b}. "Then we can choose without feeding the whole ant trail."',
        "mistake": "to carry the uncovered plate away while still arguing",
        "clue_action": "{a} noticed the moving black line and stopped, but one startled turn tipped the plate.",
        "loss": "The raviolo landed beside the ant trail in loose garden soil.",
        "consequence": "It could not be served, and the club finished its meeting without the promised snack.",
        "safe_response": "They did not spray or disturb the ants; they marked the spot and asked an adult to handle the food safely.",
        "repair": "They added covered containers to the club checklist and {plan} for the next snack.",
        "ending_image": "ants continuing along their path beneath a firmly closed food cover",
        "bad_ending": "the raviolo fell into garden soil beside an ant trail",
        "lesson": "protecting a shared thing should happen before debating when to use it",
        "safe_action": "leave the ants undisturbed and ask an adult to handle the spoiled food",
    },
    "delivery_mixup": {
        "premise": "two neighborhood meetings ended at once on opposite sides of the pillar",
        "conflict": "{a} believed the raviolo belonged to the music group; {b} believed it belonged to the garden group.",
        "clue": "the delivery card had two room numbers written on top of each other",
        "tension": "They pulled the card back and forth instead of asking the delivery volunteer.",
        "dialogue": '"The writing overlaps," said {b}. "We need the volunteer, not a louder guess."',
        "mistake": "to carry the plate toward one doorway while reading the card",
        "clue_action": "{a} compared both room signs and realized neither guess was certain.",
        "loss": "The card caught under the plate, and the raviolo slid onto the entry mat.",
        "consequence": "The delivery could not be served, so both groups went home without tasting it.",
        "safe_response": "They blocked no doorway and touched no pillar fittings; they asked the volunteer to remove the spoiled food.",
        "repair": "They designed one-card-at-a-time labels and {plan} whenever deliveries were shared.",
        "ending_image": "two clearly labeled baskets waiting on opposite sides of the quiet pillar",
        "bad_ending": "an overlapping delivery card caused the raviolo to fall on the entry mat",
        "lesson": "uncertain ownership calls for checking, not grabbing",
        "safe_action": "keep the doorway clear and ask the delivery volunteer to resolve the label",
    },
    "parade_ribbon": {
        "premise": "a small parade wound through the neighborhood square",
        "conflict": "{a} wanted to eat before marching; {b} wanted to save the raviolo for the finish.",
        "clue": "a loose parade ribbon was drifting toward the serving stand",
        "tension": "Their timing dispute continued as the ribbon curled around the table leg.",
        "dialogue": '"Hands off the ribbon until the marshal comes," said {b}. "Let us cover the food and step back."',
        "mistake": "to hold the plate and nudge the ribbon with a shoe",
        "clue_action": "{a} stopped when the table trembled and called to the parade marshal.",
        "loss": "The caught ribbon tugged the stand, dropping the raviolo onto the parade route.",
        "consequence": "The marshal closed that patch for cleanup, and the shared treat was gone.",
        "safe_response": "They stepped behind the barrier while adults cleared the ribbon and food from the route.",
        "repair": "They created a covered snack station and {plan} after future parades.",
        "ending_image": "a coiled ribbon in a safety basket beside two unused napkins",
        "bad_ending": "a loose parade ribbon pulled the raviolo onto the route",
        "lesson": "a celebration stays joyful when people pause for safety and decide together",
        "safe_action": "step behind the barrier and let parade adults clear the route",
    },
    "notice_board": {
        "premise": "the neighborhood notice board announced a one-raviolo recipe contest",
        "conflict": "{a} thought the winner should eat it; {b} thought every entrant should receive a share.",
        "clue": "a second page of the rules was folded behind the first",
        "tension": "They argued over one visible sentence while the hidden page fluttered behind it.",
        "dialogue": '"There is more paper back there," said {b}. "We should ask the judge to unfold it."',
        "mistake": "to point with the plate while quoting the incomplete rule",
        "clue_action": "{a} saw the folded corner just as a paper clip snagged the napkin.",
        "loss": "The tugged napkin spun the raviolo onto the gritty pavement.",
        "consequence": "The contest ended without a tasting, and the judge recorded the disappointing result.",
        "safe_response": "They left the board and its pillar mount alone and asked the judge to unfold the rules and clear the food.",
        "repair": "They helped print complete rules and {plan} for the next contest.",
        "ending_image": "two full rule pages clipped flat above an empty silver plate",
        "bad_ending": "an incomplete rule dispute ended with the raviolo on gritty pavement",
        "lesson": "fair decisions require the complete rule, not the fragment that favors you",
        "safe_action": "leave the mounted board alone and ask the contest judge for the full rules",
    },
    "stray_ball": {
        "premise": "a courtyard game continued near the neighborhood supper",
        "conflict": "{a} wanted the last raviolo immediately; {b} wanted to pause until the play area was separated.",
        "clue": "a soft ball had already bounced near the food table twice",
        "tension": "The argument kept both figures beside the exposed plate as another ball rolled close.",
        "dialogue": '"Food first or game first is not the question," said {b}. "We need separate spaces."',
        "mistake": "to clutch the plate and kick the rolling ball aside",
        "clue_action": "{a} missed the ball, bumped the table, and understood the warning too late.",
        "loss": "The raviolo bounced from the plate and landed under a bench.",
        "consequence": "Dust and grit ruined it, and supper ended with one empty serving dish.",
        "safe_response": "They stopped the game, kept hands out from under the heavy bench, and called an adult to retrieve the mess.",
        "repair": "They marked separate game and meal zones and {plan} at the next supper.",
        "ending_image": "a bright boundary line between the silent ball and the empty food table",
        "bad_ending": "a stray ball led to the raviolo landing under a dusty bench",
        "lesson": "shared spaces need boundaries before a disagreement turns into an accident",
        "safe_action": "stop the game and ask an adult to retrieve food from under the bench",
    },
    "warm_plate": {
        "premise": "the bakery delivered a raviolo on a warming plate for the neighborhood elders",
        "conflict": "{a} wanted to present it personally; {b} wanted to wait for the adult server.",
        "clue": "the red heat marker on the plate was still glowing",
        "tension": "Their contest over presenting the dish distracted them from the glowing heat marker.",
        "dialogue": '"Red means we do not lift it," said {b}. "The server has the mitts and the sharing list."',
        "mistake": "to tug the cool edge of the cloth beneath the plate",
        "clue_action": "{a} released the cloth at once, but the covered stand had already shifted.",
        "loss": "The raviolo slid from the warming plate into its insulated carrying box.",
        "consequence": "Its filling spilled inside the box, so the special presentation was canceled.",
        "safe_response": "They kept away from the warm plate and called the adult server, who unplugged and cleared it with proper mitts.",
        "repair": "They made a wait-for-the-server sign and {plan} for cool dishes only.",
        "ending_image": "the dark heat marker beside two safely folded oven mitts",
        "bad_ending": "the warm dish spilled inside its carrying box and could not be presented",
        "lesson": "patience and safety are more important than receiving public credit",
        "safe_action": "stay away from the warm plate and call the adult server",
    },
    "pillar_check": {
        "premise": "a tiny line appeared in the paint on the old pillar before a neighborhood meal",
        "conflict": "{a} called it harmless; {b} wanted the area checked before anyone sat nearby.",
        "clue": "a fresh pinch of paint dust lay below the line",
        "tension": "Their dispute about the mark delayed the simple choice to move the meal away.",
        "dialogue": '"We do not test a pillar ourselves," said {b}. "We move back and tell the building manager."',
        "mistake": "to carry the raviolo closer for a better look",
        "clue_action": "{a} noticed the fresh dust and finally stepped back without touching the structure.",
        "loss": "During the hurried retreat, the uncovered raviolo tipped into a planter.",
        "consequence": "The food was lost, and the gathering moved indoors while a professional inspected the pillar.",
        "safe_response": "They kept everyone beyond the temporary boundary and left all pillar inspection to the building professional.",
        "repair": "They added a move-first, report-second rule and {plan} at a different safe table.",
        "ending_image": "a professional inspection tag fluttering above an untouched planter",
        "bad_ending": "the raviolo fell into a planter while the gathering moved to safety",
        "lesson": "possible structural damage is never a contest for children to settle themselves",
        "safe_action": "move everyone back and leave pillar inspection to a professional",
    },
    "power_outage": {
        "premise": "the neighborhood lights blinked out during an evening potluck",
        "conflict": "{a} wanted to find the raviolo by touch; {b} wanted everyone to wait for safe lighting.",
        "clue": "chairs and bags had shifted around the pillar before the room went dark",
        "tension": "Their whispers became a conflict while unseen footsteps moved around the serving area.",
        "dialogue": '"Stay where you are," said {b}. "An adult has a flashlight and can clear a path."',
        "mistake": "to feel along the crowded table edge for the plate",
        "clue_action": "{a} heard a chair scrape and pulled both hands back, but the tablecloth had moved.",
        "loss": "The raviolo slid into a closed recycling tray beneath the table.",
        "consequence": "It was crushed among used paper cups, and the potluck lost its final shared dish.",
        "safe_response": "They stayed still, called an adult, and followed the flashlight path without leaning on or circling the pillar.",
        "repair": "They prepared a clear emergency route and {plan} only after the lights returned.",
        "ending_image": "two flashlights shining along an empty, obstacle-free path past the pillar",
        "bad_ending": "the raviolo slid into recycling during the outage and was crushed",
        "lesson": "in darkness, waiting for a safe path protects people better than rescuing a treat",
        "safe_action": "stay still and follow an adult's flashlight along a cleared path",
    },
}


TELLING_MODES = {
    "straight": {
        "opening": "In {setting}, under {glow}, {a} and {b} met beside an old pillar; {premise}.",
        "thought": "{a} noticed that {clue}, yet {a} kept thinking about the disputed share.",
        "reflection": "{a} said the lesson plainly: {lesson}. {b} agreed to remember it.",
        "ending": "At closing time, the last image was {image}.",
    },
    "question": {
        "opening": "How could one raviolo trouble {setting}? Under {glow}, {a} and {b} found out when {premise}.",
        "thought": "Could the clue matter more than being first? {b} asked after noticing that {clue}.",
        "reflection": '"What should we remember?" asked {b}. {a} answered, "{lesson}."',
        "ending": "The neighborhood's answer was visible in {image}.",
    },
    "flash_forward": {
        "opening": "Later, everyone would remember the empty plate. Earlier, in {setting}, {a} and {b} met as {premise}.",
        "thought": "Neither yet understood why {clue} would decide the afternoon.",
        "reflection": "Looking back, {b} understood that {lesson}; {a} wrote it into their new plan.",
        "ending": "Long after the quarrel, neighbors could still see {image}.",
    },
    "witness": {
        "opening": "The neighborhood baker saw it begin: under {glow}, {a} and {b} met while {premise}.",
        "thought": "From across the square, the baker saw that {clue}, though the two figures were watching each other.",
        "reflection": "When the baker asked what changed, {a} replied that {lesson}; {b} nodded.",
        "ending": "The baker closed the stall with one quiet picture in view: {image}.",
    },
    "countdown": {
        "opening": "Three choices remained in the {setting}: protect the meal, settle the share, or ignore the warning. {a} and {b} faced them as {premise}.",
        "thought": "Two choices remained when {b} noticed that {clue}; still, the conflict continued.",
        "reflection": "One lesson remained after the loss: {lesson}. Both figures accepted it.",
        "ending": "Then the counting stopped at {image}.",
    },
    "neighborhood_chorus": {
        "opening": '"A shared place needs shared care," neighbors often said. Under {glow}, {a} and {b} tested that saying when {premise}.',
        "thought": '"Look wider," called a neighbor, for {clue}; {a} and {b} finally listened.',
        "reflection": "Together they gave the neighborhood a better saying: {lesson}.",
        "ending": "That evening, every passerby paused at {image}.",
    },
    "quiet": {
        "opening": "Everything in {setting} was unusually quiet beneath {glow}. Then {a} and {b} arrived as {premise}.",
        "thought": "A small clue became hard to ignore: {clue}. {a} noticed it beneath the argument.",
        "reflection": "In a quieter voice, {b} observed that {lesson}. {a} listened without interrupting.",
        "ending": "Silence returned around {image}.",
    },
    "ledger": {
        "opening": "The neighborhood log records that {a} and {b} met beside the pillar under {glow} when {premise}.",
        "thought": "Its next line notes the overlooked evidence: {clue}.",
        "reflection": "The final written finding was that {lesson}; both figures signed beneath it.",
        "ending": "A sketch at the bottom showed {image}.",
    },
}


SHARING_PLANS = {
    "two_plates": {"purpose": "two young helpers", "proposal": "cutting it onto two clean plates with an adult", "repair": "set out two labeled plates"},
    "turn_tokens": {"purpose": "the block's helpers", "proposal": "drawing turn tokens before serving", "repair": "placed two turn tokens beside the dish"},
    "half_now_half_later": {"purpose": "the afternoon and evening crews", "proposal": "covering half for the later crew", "repair": "labeled a covered portion for each crew"},
    "table_vote": {"purpose": "everyone at the community table", "proposal": "asking the table to choose a fair division", "repair": "posted the table's agreed sharing rule"},
    "helper_portions": {"purpose": "the volunteers who finished cleanup", "proposal": "having an adult portion it for all helpers", "repair": "listed every helper before portions were served"},
    "neighbor_slice": {"purpose": "a neighbor who could not attend", "proposal": "saving one covered piece and dividing the rest", "repair": "prepared one covered neighbor portion first"},
    "paired_jobs": {"purpose": "the setup and cleanup teams", "proposal": "giving equal portions to both teams", "repair": "matched every portion to a completed team job"},
    "share_circle": {"purpose": "the children's sharing circle", "proposal": "waiting for the circle leader to divide it", "repair": "marked equal places around the sharing circle"},
}


FOLLOW_THROUGHS = {
    "practice_run": "Before the next event, {a} and {b} rehearsed the new plan with an empty plate and corrected one confusing step.",
    "picture_card": "{a} drew the safe steps as pictures, and {b} tested whether a younger neighbor could follow them.",
    "two_helpers": "At the next setup, {a} watched the surroundings while {b} checked the sharing list; then they traded jobs.",
    "adult_review": "They asked the event organizer to review their plan and changed the part that lacked adult help.",
    "accessible_copy": "{a} made a large-print copy of the plan, while {b} added simple symbols beside every instruction.",
    "weather_check": "They added a weather and equipment check before food could be uncovered at any outdoor gathering.",
    "pause_phrase": 'Together they practiced saying, "Pause, protect, then share," whenever a warning interrupted a decision.',
    "feedback_round": "After the next meal, they invited every helper to name one part of the system that could be fairer.",
    "backup_place": "They marked a second safe serving place so a problem near the pillar would never force a hurried choice.",
    "cleanup_roles": "{a} listed the setup jobs, {b} listed the cleanup jobs, and both checked that every worker received a turn.",
    "covered_sample": "They kept a covered practice dish nearby to demonstrate the plan without risking real food.",
    "neighbor_check": "One week later, a neighbor tested the instructions without hints, and the two planners clarified the one uncertain line.",
}


def valid_combos() -> list[tuple[str, str]]:
    return [("neighborhood", "raviolo"), ("courtyard", "raviolo")]


def explain_rejection(setting: str, treasure: str) -> str:
    return f"(No story: only the raviolo myth is supported here, and the chosen setting must be a small shared place.)"


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    lines.append(asp.fact("shared_place", "neighborhood"))
    lines.append(asp.fact("shared_place", "courtyard"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T) :- setting(S), treasure(T), shared_place(S).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(p - a))
    print("only in clingo:", sorted(a - p))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, t = f["hero_a"], f["hero_b"], f["treasure"]
    return [
        f'Write a child-facing neighborhood story about {a.label} and {b.label}, a shared {t.label}, and this clue: {f["clue"]}.',
        f'Tell a conflict story near a pillar in which {f["bad_ending"]}, then show a safe community repair.',
        f'Write a story using "raviolo", "pillar", "neighborhood", and "sharing" whose lesson is that {f["lesson"]}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, t = f["hero_a"], f["hero_b"], f["treasure"]
    return [
        QAItem(
            question=f"Who were the two figures in the neighborhood myth?",
            answer=f"They were {a.label} and {b.label}, two figures standing by the pillar in {f['setting'].name}.",
        ),
        QAItem(
            question="What was meant to be shared?",
            answer=f"The shared treasure was {t.phrase}, a raviolo meant to be shared.",
        ),
        QAItem(
            question=f"What clue did {a.label} and {b.label} overlook during their conflict?",
            answer=f"They overlooked that {f['clue']}. That warning mattered more than deciding who went first.",
        ),
        QAItem(
            question="Why did this feast have a bad ending?",
            answer=f"The feast had a bad ending because {f['bad_ending']}. Their conflict delayed a safer choice.",
        ),
        QAItem(
            question="What safe action did the two figures take afterward?",
            answer=f"They chose to {f['safe_action']}. They did not inspect, climb, or alter the pillar themselves.",
        ),
        QAItem(
            question="What lesson did they learn about conflict and sharing?",
            answer=f"They learned that {f['lesson']}. Their new neighborhood plan put that lesson into practice.",
        ),
        QAItem(
            question="How did they test or strengthen their new plan?",
            answer=f["follow_through_text"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pillar?",
            answer="A pillar is a tall stone or wooden column that can stand like a marker or support.",
        ),
        QAItem(
            question="What is a neighborhood?",
            answer="A neighborhood is a part of a town or city where people live close to one another.",
        ),
        QAItem(
            question="What is a raviolo?",
            answer="A raviolo is a pasta pocket, often filled with soft food and served as part of a meal.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person enjoy the same thing in turn or together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} held_by={e.held_by} meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic neighborhood storyworld about a raviolo, a pillar, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--role-a", choices=ROLES)
    ap.add_argument("--role-b", choices=ROLES)
    ap.add_argument("--incident", choices=INCIDENTS)
    ap.add_argument("--telling-mode", choices=TELLING_MODES)
    ap.add_argument("--sharing-plan", choices=SHARING_PLANS)
    ap.add_argument("--follow-through", choices=FOLLOW_THROUGHS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "neighborhood"
    treasure = args.treasure or "raviolo"
    if setting not in SETTINGS or treasure not in TREASURES:
        raise StoryError("(No valid combination matches the given options.)")
    if (setting, treasure) not in valid_combos():
        raise StoryError(explain_rejection(setting, treasure))
    role_a = args.role_a or rng.choice(["girl", "boy", "child"])
    role_b = args.role_b or rng.choice(["girl", "boy", "child"])
    name_a = args.name_a or rng.choice(NAMES)
    name_b = args.name_b or rng.choice([n for n in NAMES if n != name_a])
    incident = args.incident or rng.choice(list(INCIDENTS))
    telling_mode = args.telling_mode or rng.choice(list(TELLING_MODES))
    sharing_plan = args.sharing_plan or rng.choice(list(SHARING_PLANS))
    follow_through = args.follow_through or rng.choice(list(FOLLOW_THROUGHS))
    return StoryParams(
        setting=setting,
        treasure=treasure,
        name_a=name_a,
        name_b=name_b,
        role_a=role_a,
        role_b=role_b,
        incident=incident,
        telling_mode=telling_mode,
        sharing_plan=sharing_plan,
        follow_through=follow_through,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(SETTINGS[params.setting], TREASURES[params.treasure], params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, treasure) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, (setting, treasure) in enumerate(valid_combos()):
            params = StoryParams(
                setting=setting,
                treasure=treasure,
                name_a=NAMES[i % len(NAMES)],
                name_b=NAMES[(i + 3) % len(NAMES)],
                role_a="child",
                role_b="child",
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
