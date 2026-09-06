#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/transcribe_children_s_museum_misunderstanding_friendship_repetition.py
============================================================================================================

A standalone story world about a children's museum tale, built in a folk-tale
style around misunderstanding, friendship, and repetition.

The seed imagination:
- A child visits a children's museum.
- A small misunderstanding happens around a sign, a whisper, and a repeated
  instruction.
- A friend helps by repeating the message clearly, and the story ends with
  warmth and shared play.

The simulated world tracks:
- physical meters: distance, sound, attention, tidiness, and trustful actions
- emotional memes: confusion, worry, kindness, relief, friendship

The story is generated from the evolving state rather than from a fixed prose
template with swapped nouns.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
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
    place: str = "the children's museum"
    rooms: list[str] = field(default_factory=lambda: ["the gallery", "the water table", "the dress-up corner"])


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    sound: str
    keyword: str
    causes_misunderstanding: bool = True


@dataclass
class Sign:
    id: str
    text: str
    meaning: str


@dataclass(frozen=True)
class Incident:
    id: str
    room: str
    exhibit: str
    sign_text: str
    intended: str
    mistaken_belief: str
    mistaken_action: str
    consequence: str
    clue: str
    failed_attempt: str
    friend_line: str
    repeated_words: str
    shared_action: str
    lesson: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THRESHOLD = 1.0


def _narrate_if(world: World, cond: bool, text: str) -> None:
    if cond:
        world.say(text)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "museum": Setting(),
}

ACTIVITIES = {
    "transcribe": Activity(
        id="transcribe",
        verb="transcribe the exhibit notes",
        gerund="transcribing the exhibit notes",
        sound="soft tapping",
        keyword="transcribe",
        causes_misunderstanding=True,
    ),
    "repeat": Activity(
        id="repeat",
        verb="repeat the exhibit directions",
        gerund="repeating the exhibit directions",
        sound="clear echoing",
        keyword="repeat",
        causes_misunderstanding=False,
    ),
}

SIGNS = {
    "quiet_sign": Sign(
        id="quiet_sign",
        text="Please use quiet voices and follow the arrows.",
        meaning="The sign asks children to whisper and walk carefully.",
    ),
    "copy_sign": Sign(
        id="copy_sign",
        text="Trace the letters with a finger, then speak the words aloud.",
        meaning="The sign invites children to copy and say the words.",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Tara", "Nora", "Pia", "Ivy"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Milo", "Ezra", "Noah"]
TRAITS = ["curious", "gentle", "brave", "bright", "careful", "lively"]


INCIDENTS = [
    Incident(
        id="echo_map", room="the echo tunnel", exhibit="a map of sound stations",
        sign_text="Transcribe one echo, then pass the pencil on.",
        intended="write down one sound and give the pencil to the next visitor",
        mistaken_belief="copy every echo before anyone else could touch the pencil",
        mistaken_action="filled the whole card while a line of children waited",
        consequence="the line curled around the tunnel and the quietest echoes went unheard",
        clue="a painted hand beside the words was offering the pencil forward",
        failed_attempt="rushed through the last boxes, which only made the line longer",
        friend_line="The hand is passing, not pointing. One echo each means everyone gets a turn.",
        repeated_words="one echo, pass it on",
        shared_action="recorded a plink and a whoosh, then handed the pencil down the line",
        lesson="a shared record can hold many voices when nobody tries to own every space",
        ending="the finished card fluttered beneath twelve different sound-words",
    ),
    Incident(
        id="shadow_labels", room="the shadow theater", exhibit="a wall of animal silhouettes",
        sign_text="Trace your shadow; leave the light clear.",
        intended="outline a shadow and then step away from the lamp",
        mistaken_belief="keep standing in the light so the traced shape would not escape",
        mistaken_action="stayed planted before the lamp after the outline was finished",
        consequence="every new shadow disappeared behind one enormous silhouette",
        clue="three empty footprints led away from the lamp toward the viewing bench",
        failed_attempt="made the shadow smaller by crouching, but still blocked the beam",
        friend_line="Those footprints finish the instruction. Trace, then clear the light.",
        repeated_words="trace, step back, let light through",
        shared_action="outlined a rabbit, stepped aside, and helped two younger children make birds",
        lesson="making room for a friend can reveal something neither person could see alone",
        ending="rabbit ears and paper wings danced together across the bright wall",
    ),
    Incident(
        id="water_notes", room="the water laboratory", exhibit="a channel of spinning gates",
        sign_text="Copy the gate order before releasing the stream.",
        intended="write the gate positions first and open the water afterward",
        mistaken_belief="copy what the water did while it was already rushing",
        mistaken_action="pulled the release lever before noting a single gate",
        consequence="the current spun every marker around and soaked the observation card",
        clue="the numbered pencil boxes came before the blue lever in the diagram",
        failed_attempt="tried to remember the spinning pattern, but each gate had moved twice",
        friend_line="The little numbers show the order: transcribe first, release second.",
        repeated_words="write, check, then flow",
        shared_action="dried the card, reset the gates together, and recorded each position before trying again",
        lesson="careful order turns a muddle into an experiment friends can repeat",
        ending="one silver stream curled neatly through every gate without wetting the new notes",
    ),
    Incident(
        id="market_recipe", room="the pretend market", exhibit="a bakery recipe wall",
        sign_text="Transcribe the recipe; take only a pretend scoop.",
        intended="copy the recipe and measure with the toy scoop",
        mistaken_belief="take the recipe card itself to use as a scoop",
        mistaken_action="folded the display card toward the bin of wooden oats",
        consequence="the old paper creased and the next baker could no longer read the last line",
        clue="a bright red toy scoop hung directly under a matching scoop picture",
        failed_attempt="flattened the card with both elbows, making the crease sharper",
        friend_line="The picture points to the red scoop. The recipe stays here for every baker.",
        repeated_words="copy the card, share the scoop",
        shared_action="smoothed the card under a clear cover and transcribed the missing line from its twin",
        lesson="asking before taking protects things that a whole community shares",
        ending="a wooden loaf sat beside the rescued recipe, dusted with make-believe flour",
    ),
    Incident(
        id="dinosaur_tags", room="the fossil hall", exhibit="a tray of replica dinosaur bones",
        sign_text="Match, transcribe, return each tag.",
        intended="match one label to one bone, copy it, and put the label back",
        mistaken_belief="return every tag to the large dinosaur picture",
        mistaken_action="stacked all the labels beneath the same enormous footprint",
        consequence="a tiny tooth was called a tail and nobody could finish the matching game",
        clue="colored dots on the bones matched dots on the backs of the labels",
        failed_attempt="sorted the tags by word length, which paired claw with crest",
        friend_line="Turn them over. The colors are clues, and return means return each one home.",
        repeated_words="match, write, return",
        shared_action="used the colored dots to restore every label and copied the tooth's real name",
        lesson="good friends test an idea with evidence instead of laughing at a mistake",
        ending="the final green tag rested beside the little tooth like a leaf beside a pebble",
    ),
    Incident(
        id="mail_route", room="the child-size town", exhibit="a post-office route board",
        sign_text="Transcribe the address and repeat it at the window.",
        intended="copy the address, then say it to the postal clerk",
        mistaken_belief="say the word address again and again without reading the actual address",
        mistaken_action="called 'address, address, address' through the brass window",
        consequence="three pretend parcels rolled onto the wrong delivery cart",
        clue="the envelope showed a house number and street name inside a dotted copying box",
        failed_attempt="shouted the single word louder, which did not tell the clerk where to send anything",
        friend_line="Repeat the words inside the box, not the instruction above it.",
        repeated_words="four Garden Lane",
        shared_action="copied the full address, called it clearly together, and rerouted each parcel",
        lesson="repetition helps only when friends first agree on which message matters",
        ending="the smallest parcel clicked into the mailbox marked with a painted sunflower",
    ),
    Incident(
        id="music_pattern", room="the music loft", exhibit="a row of colored handbells",
        sign_text="Transcribe the pattern; repeat after the pause.",
        intended="write the color sequence and play it after a silent beat",
        mistaken_belief="ring each bell continuously until a pause appeared",
        mistaken_action="shook the blue bell through every beat of the tune",
        consequence="the guide's gentle melody vanished beneath one long clang",
        clue="an empty square in the pattern sat between two groups of colored notes",
        failed_attempt="rang more softly without ever stopping, so the missing pause stayed missing",
        friend_line="An empty square is part of music too. It asks us to wait one beat.",
        repeated_words="red, gold, rest, blue",
        shared_action="copied the pattern, counted the quiet beat together, and played the whole phrase",
        lesson="listening to silence can be as important as repeating a sound",
        ending="the last blue note floated alone while both children held perfectly still",
    ),
    Incident(
        id="garden_code", room="the rooftop garden", exhibit="a pollinator observation chart",
        sign_text="Transcribe what lands; do not chase visitors.",
        intended="record insects that land naturally without following them",
        mistaken_belief="treat the instruction as saying museum visitors must not be followed through the garden",
        mistaken_action="waved a family away from the butterfly bed",
        consequence="the family felt unwelcome and the children missed a bumblebee landing",
        clue="tiny wings decorated the word visitors while an arrow pointed to the flower",
        failed_attempt="whispered the same warning more politely, but it was still the wrong warning",
        friend_line="Here, visitors means bees and butterflies. People are welcome beside the path.",
        repeated_words="watch the wings, welcome the people",
        shared_action="apologized to the family and transcribed two bee landings beside them",
        lesson="when a word has two meanings, a picture and a patient friend can settle the question",
        ending="a striped bee rested on a purple flower beside four careful tally marks",
    ),
    Incident(
        id="bubble_message", room="the bubble studio", exhibit="a table for testing bubble wands",
        sign_text="Copy the shape; repeat with one change.",
        intended="draw a wand shape, test it, then alter one feature",
        mistaken_belief="make an exact copy every time and never change anything",
        mistaken_action="bent six identical triangle wands and expected six different bubbles",
        consequence="the wire supply ran low while every bubble still came out round",
        clue="a penciled plus sign joined the second drawing to one extra loop",
        failed_attempt="changed only the wire color, which did not change the wand's structure",
        friend_line="Repeat the test, not the mistake. Add one loop so we can compare fairly.",
        repeated_words="same test, one change",
        shared_action="rebuilt one wand, transcribed both designs, and compared their round bubbles",
        lesson="friends can repeat an experiment while changing one useful thing at a time",
        ending="two bubbles touched above the table and trembled like a pair of glass moons",
    ),
    Incident(
        id="costume_caption", room="the costume workshop", exhibit="a wall of historical hats",
        sign_text="Transcribe a caption; return costumes to their hooks.",
        intended="copy one display caption and hang worn costumes back up",
        mistaken_belief="write a new caption directly on each costume's hook",
        mistaken_action="lifted a marker toward the polished wooden labels",
        consequence="another child grabbed the last paper card and both thought the other was being unfair",
        clue="a stack of blank cards bore the same feather symbol as the captions",
        failed_attempt="argued about who had read the sign first while the marker cap dried",
        friend_line="We both missed the feather. It marks the cards where captions belong.",
        repeated_words="cards for writing, hooks for hats",
        shared_action="split the blank cards, wrote two captions, and returned a velvet hat together",
        lesson="friendship grows when both people can admit the same misunderstanding",
        ending="two fresh captions hung below the hats, their ink drying in the afternoon light",
    ),
    Incident(
        id="building_plan", room="the block workshop", exhibit="a bridge-building table",
        sign_text="Transcribe the plan, then repeat the strongest span.",
        intended="copy the tested design and build another strong bridge section",
        mistaken_belief="repeat the longest row of blocks because longest must mean strongest",
        mistaken_action="extended a thin bridge across the entire table",
        consequence="the center sagged and trapped a wooden ferry underneath",
        clue="three short triangles on the plan carried little weight symbols",
        failed_attempt="added more blocks to the ends, making the weak middle bend further",
        friend_line="The weight marks point to the triangles. Strongest is not the same as longest.",
        repeated_words="triangle, test, repeat",
        shared_action="freed the ferry, transcribed the supports, and rebuilt the center as a team",
        lesson="clear evidence and shared work are stronger than a confident guess",
        ending="the wooden ferry passed under three sturdy arches without brushing a block",
    ),
    Incident(
        id="story_order", room="the puppet nook", exhibit="a table of picture-story tiles",
        sign_text="Transcribe the tale; repeat the ending to your partner.",
        intended="put the pictures in order, write the tale, and retell its ending",
        mistaken_belief="place every repeated picture at the end of the story",
        mistaken_action="moved three pictures of rain behind the sunny final scene",
        consequence="the puppet tale ended with a picnic under a sudden indoor storm",
        clue="small sunrise numbers on the backs showed when each scene occurred",
        failed_attempt="invented an umbrella for the final puppet, but the beginning still made no sense",
        friend_line="Repeated rain can happen in different parts. The sunrise numbers show the order.",
        repeated_words="first clouds, then rain, last sun",
        shared_action="ordered the tiles, transcribed the repaired tale, and performed its ending together",
        lesson="repetition can connect a story when friends also pay attention to what changed",
        ending="the two puppets bowed beneath a paper sun while the rain tiles slept in their proper places",
    ),
]


TELLING_MODES = (
    "question_first", "dialogue_first", "object_first", "motion_first", "memory_first",
    "rule_first", "friend_first", "sound_first", "goal_first", "room_first",
)


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "museum"
    activity: str = "transcribe"
    name: str = "Mina"
    gender: str = "girl"
    friend_name: str = "Owen"
    friend_gender: str = "boy"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness / ASP twin
# ---------------------------------------------------------------------------
def reasonable(params: StoryParams) -> bool:
    return params.place == "museum" and params.activity in ACTIVITIES


def valid_names(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A children's museum storyworld about misunderstanding, friendship, and repetition.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name", dest="friend_name")
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
    place = args.place or "museum"
    activity = args.activity or "transcribe"
    if place != "museum":
        raise StoryError("This storyworld only tells tales set in the children's museum.")
    if activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(valid_names(gender))
    friend_name = args.friend_name or rng.choice(valid_names(friend_gender))
    if name == friend_name:
        raise StoryError("The child and the friend must be different people.")
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, friend_name=friend_name, friend_gender=friend_gender, trait=trait)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def mem(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_gender))
    sign = world.add(Entity(id="sign", type="sign", label="museum sign"))
    activity = ACTIVITIES[params.activity]

    route = params.seed if params.seed is not None else sum(ord(c) for c in child.id + friend.id)
    incident = INCIDENTS[route % len(INCIDENTS)]
    mode = TELLING_MODES[(route // len(INCIDENTS)) % len(TELLING_MODES)]

    openings = {
        "question_first": [
            f'"How can one little sign cause such a big misunderstanding?" {child.id} wondered at the children\'s museum.',
            f"The question followed the {params.trait} child into {incident.room}, where {friend.id} was waiting.",
        ],
        "dialogue_first": [
            f'"Let us transcribe something nobody has noticed," {child.id} told {friend.id}.',
            f"The two friends hurried into {incident.room} at the children's museum.",
        ],
        "object_first": [
            f"At the children's museum, {incident.exhibit} waited in {incident.room}.",
            f"A {params.trait} child named {child.id} approached it with {friend.id} and a pencil.",
        ],
        "motion_first": [
            f"{child.id} and {friend.id} followed painted arrows through the children's museum until they reached {incident.room}.",
            f"{child.id}, always {params.trait}, hurried toward {incident.exhibit}.",
        ],
        "memory_first": [
            f"Long afterward, {child.id} remembered one visit to the children's museum whenever a direction seemed unclear.",
            f"It began in {incident.room}, beside {incident.exhibit}, with {friend.id} close by.",
        ],
        "rule_first": [
            "The children's museum had a friendly rule: read, think, and ask before acting.",
            f"In {incident.room}, {params.trait} {child.id} meant to follow it while {friend.id} studied {incident.exhibit}.",
        ],
        "friend_first": [
            f"{friend.id} saved a place for {child.id} beside {incident.exhibit} in the children's museum.",
            f"When the {params.trait} child arrived at {incident.room}, they promised to solve the activity as friends.",
        ],
        "sound_first": [
            f"{activity.sound.capitalize()} drifted out of {incident.room} and down a hall of the children's museum.",
            f"{params.trait.capitalize()} {child.id} followed it to {incident.exhibit}, where {friend.id} waved.",
        ],
        "goal_first": [
            f"{child.id} had one goal at the children's museum: transcribe a useful clue for the visitor notebook.",
            f"{friend.id} joined the search at {incident.exhibit} in {incident.room}.",
        ],
        "room_first": [
            f"In {incident.room}, every corner of the children's museum seemed to invite a different kind of play.",
            f"There, {params.trait} {child.id} and loyal {friend.id} chose {incident.exhibit}.",
        ],
    }
    for sentence in openings[mode]:
        world.say(sentence)
    world.say(f'The sign said, "{incident.sign_text}"')
    world.say(f"{child.id} wanted to {activity.verb}, but decided the words must mean to {incident.mistaken_belief}.")

    world.para()
    mem(child, "confusion", 1)
    meter(child, "attention", 1)
    world.say(f"Acting on that misunderstanding, {child.id} {incident.mistaken_action}.")
    world.say(f"As a result, {incident.consequence}.")
    mem(friend, "worry", 1)
    if mode in {"question_first", "object_first", "memory_first", "friend_first", "goal_first"}:
        world.say(f"{child.id} tried to fix things alone and {incident.failed_attempt}.")
        world.say(f"{friend.id} did not tease. Instead, the friend pointed out that {incident.clue}.")
    else:
        world.say(f"{friend.id} noticed that {incident.clue}.")
        world.say(f"Before listening, {child.id} {incident.failed_attempt}. That made it clear that guessing again would not help.")

    world.para()
    mem(friend, "kindness", 1)
    mem(friend, "friendship", 1)
    world.say(f'{friend.id} said, "{incident.friend_line}"')
    world.say(f'Together they repeated, "{incident.repeated_words}." They said it once to understand it and once more to remember it.')
    world.say(f"Now {child.id} understood: the sign meant to {incident.intended}.")
    meter(friend, "support", 1)
    meter(child, "understanding", 1)
    mem(child, "relief", 1)
    mem(child, "friendship", 1)
    mem(child, "confusion", -1)

    world.para()
    world.say(f"The friends {incident.shared_action}.")
    if mode in {"dialogue_first", "motion_first", "rule_first", "sound_first", "room_first"}:
        world.say(f'"Repeating is useful when we repeat the right idea," {child.id} said. "And friendship makes it easier to change our minds."')
    else:
        world.say(f"{child.id} thanked {friend.id} for correcting the mistake kindly instead of taking over.")
    world.say("Their friendship felt sturdier because they had listened, checked, and repaired the trouble together.")
    world.say(f"They learned that {incident.lesson}.")
    world.say(f"Before they left {incident.room}, {incident.ending}.")

    world.facts.update(
        child=child,
        friend=friend,
        sign=sign,
        activity=activity,
        incident=incident,
        mode=mode,
        misunderstood=True,
        resolved=True,
        repetition=True,
    )
    return world


def generate_story_text(world: World) -> str:
    return world.render()


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    f = world.facts["friend"]
    act = world.facts["activity"]
    incident = world.facts["incident"]
    return [
        f"Write a child-friendly tale in {incident.room} at a children's museum about a misunderstanding, repetition, and friendship.",
        f"Tell a gentle story where {c.id} wants to {act.verb} at {incident.exhibit}, makes a consequential mistake, and {f.id} helps interpret a clue.",
        f'Write a complete story using the word "transcribe," the repeated phrase "{incident.repeated_words}," and a concrete ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    f = world.facts["friend"]
    incident = world.facts["incident"]
    return [
        QAItem(
            question=f"What did {c.id} think the sign meant at first?",
            answer=f"{c.id} thought it meant to {incident.mistaken_belief}. That misunderstanding led the child to act before checking the whole sign.",
        ),
        QAItem(
            question=f"What evidence helped {f.id} explain the sign?",
            answer=f"{f.id} noticed that {incident.clue}. The friend used that evidence instead of merely insisting that {c.id} was wrong.",
        ),
        QAItem(
            question=f"How did {c.id} and {f.id} repair the problem together?",
            answer=f"The friends {incident.shared_action}. Their cooperation turned the misunderstanding into a stronger friendship.",
        ),
        QAItem(
            question="What lesson did the children learn from repeating the instruction?",
            answer=f"They learned that {incident.lesson}. Repetition worked because they first checked which meaning fit the evidence.",
        ),
        QAItem(
            question="What final image showed that the problem was resolved?",
            answer=f"At the end, {incident.ending}. That concrete image showed the exhibit working peacefully again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a children's museum?",
            answer="A children's museum is a place where children can explore, touch, build, and learn by playing with exhibits and activities.",
        ),
        QAItem(
            question="Why can repetition help when something is misunderstood?",
            answer="Repetition can help because hearing or seeing the same message more than once gives the mind another chance to understand it clearly.",
        ),
        QAItem(
            question="What does friendship look like in a kind story?",
            answer="Friendship looks like helping, listening, and speaking gently so another person feels safe and included.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(C) :- child_name(C).
friend(F) :- friend_name(F).
activity(transcribe).
activity(repeat).

misunderstanding(C) :- child(C), activity(transcribe).
friendship(C,F) :- child(C), friend(F), helps(F,C).
repetition(F) :- friend(F), repeats(F).

resolved(C) :- misunderstanding(C), friendship(C,_), repetition(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "museum"))
    lines.append(asp.fact("activity", "transcribe"))
    lines.append(asp.fact("activity", "repeat"))
    lines.append(asp.fact("child_name", "child"))
    lines.append(asp.fact("friend_name", "friend"))
    lines.append(asp.fact("helps", "friend", "child"))
    lines.append(asp.fact("repeats", "friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Python gate is simple; ASP twin must agree on the same toy structure.
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    asp_resolved = bool(asp.atoms(model, "resolved"))
    py_resolved = True
    if asp_resolved == py_resolved:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH between ASP and Python reasonableness.")
    return 1


# ---------------------------------------------------------------------------
# Emit / trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(place="museum", activity="transcribe", name="Mina", gender="girl", friend_name="Owen", friend_gender="boy", trait="curious"),
        StoryParams(place="museum", activity="transcribe", name="Theo", gender="boy", friend_name="Lily", friend_gender="girl", trait="gentle"),
    ]


def generate(params: StoryParams) -> StorySample:
    if not reasonable(params):
        raise StoryError("This world only supports a children's museum tale with transcribe/repeat.")
    world = tell(params)
    return StorySample(
        params=params,
        story=generate_story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This storyworld's ASP twin only checks the friendship-resolution pattern.")
        sys.exit(0)

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in valid_story_params()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} and {p.friend_name} at the children's museum"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
