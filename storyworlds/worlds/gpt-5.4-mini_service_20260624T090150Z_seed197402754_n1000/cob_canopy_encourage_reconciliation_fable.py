#!/usr/bin/env python3
"""
A small fable-like story world about a shared cob, a canopy, and reconciliation.

Premise:
- Two small neighbors want the same cozy spot under a canopy.
- A corn cob becomes the cause of a split.
- A gentle helper encourages them to talk, share, and mend the hurt.

The world model tracks physical state in meters and feelings in memes so the
story prose is driven by simulated change rather than a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path[:0] = [STORYWORLDS_DIR, os.path.dirname(STORYWORLDS_DIR)]
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "squirrel", "mouse"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old meadow"
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    type: str = "thing"
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    helper: str
    scenario: str = "picnic"
    opening_style: int = 0
    conflict_style: int = 0
    encouragement_style: int = 0
    repair_style: int = 0
    ending_style: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"rest", "talk", "share"}),
    "orchard": Setting(place="the orchard", affords={"rest", "talk", "share"}),
    "lane": Setting(place="the sunny lane", affords={"rest", "talk", "share"}),
}

HEROES = {
    "fox": {"type": "fox", "label": "fox"},
    "rabbit": {"type": "rabbit", "label": "rabbit"},
    "squirrel": {"type": "squirrel", "label": "squirrel"},
    "mouse": {"type": "mouse", "label": "mouse"},
}

FRIENDS = {
    "crow": {"type": "crow", "label": "crow"},
    "hare": {"type": "hare", "label": "hare"},
    "mole": {"type": "mole", "label": "mole"},
    "robin": {"type": "robin", "label": "robin"},
}

HELPERS = {
    "turtle": {"type": "turtle", "label": "turtle"},
    "deer": {"type": "deer", "label": "deer"},
    "owl": {"type": "owl", "label": "owl"},
}

THINGS = {
    "cob": Thing(
        id="cob",
        label="cob",
        phrase="a golden corn cob",
    ),
    "canopy": Thing(
        id="canopy",
        label="canopy",
        phrase="a cool green canopy of leaves",
    ),
}

CURATED = [
    StoryParams(place="meadow", hero="fox", friend="crow", helper="owl", scenario="picnic"),
    StoryParams(place="orchard", hero="rabbit", friend="hare", helper="deer", scenario="garden"),
    StoryParams(place="lane", hero="mouse", friend="mole", helper="turtle", scenario="art"),
]


SCENARIOS = {
    "picnic": {
        "premise": "They had carried one roasted ear of corn for their picnic",
        "trigger": "each believed the other had promised them the last piece",
        "need_hero": "I was saving it because I am still hungry",
        "need_friend": "I thought we agreed to divide it at lunch",
        "cob_role": "It held the corn they brought for their picnic, and they later saved the bare cob for a bird feeder",
        "repair": "broke the corn into two fair portions and counted the kernels on each",
        "outcome": "shared the corn and saved the bare cob for a bird feeder",
        "proof": "Two neat piles of kernels rested on one leaf plate",
    },
    "garden": {
        "premise": "They had found a dry corn cob full of seeds for the spring garden",
        "trigger": "one wanted a sunny row while the other wanted to plant beside the path",
        "need_hero": "I want enough sun for the seedlings",
        "need_friend": "I want us to notice when the seedlings need water",
        "cob_role": "It held the kernels they wanted to plant in their garden",
        "repair": "drew two adjoining garden rows and divided the kernels between them",
        "outcome": "planted one sunny row beside one easy-to-watch row",
        "proof": "Two little rows of fresh soil met at a shared watering stone",
    },
    "art": {
        "premise": "They had brought a clean corn cob to roll patterns in washable paint",
        "trigger": "both wanted their own pattern to fill the festival banner",
        "need_hero": "I hoped to print bright circles",
        "need_friend": "I hoped to leave room for my wavy border",
        "cob_role": "It was a safe printing roller for their washable-paint pattern",
        "repair": "tested both patterns on scrap paper and planned alternating bands",
        "outcome": "rolled circles and waves across the same banner",
        "proof": "The finished banner fluttered with circles beside waves",
    },
    "game": {
        "premise": "They were using a smooth dry cob as the finish marker in a seed-pod race",
        "trigger": "the marker shifted and each accused the other of moving it",
        "need_hero": "I only wanted the finish line to stay fair",
        "need_friend": "I moved it away from a muddy patch so nobody would slip",
        "cob_role": "It marked the finish line in their seed-pod race",
        "repair": "chose a dry patch and marked it with two stones beside the cob",
        "outcome": "restarted the race with a finish line everyone could see",
        "proof": "The cob stood between two stones while both racers crossed laughing",
    },
    "music": {
        "premise": "They had found that a dry cob made a cheerful rasp when stroked with a twig",
        "trigger": "one wanted a quick rhythm while the other kept interrupting with a slow one",
        "need_hero": "The quick beat sounds like dancing feet",
        "need_friend": "The slow beat gives our song a steady heart",
        "cob_role": "It was a simple rhythm instrument that made a rasping sound",
        "repair": "tapped out four quick beats followed by four slow beats",
        "outcome": "played a tune that gave each rhythm a turn",
        "proof": "Seed-pod bells jingled while the cob answered fast, then slow",
    },
    "marker": {
        "premise": "They had set a bright corn cob beneath the canopy as a picnic trail marker",
        "trigger": "each turned it toward a different path and the arriving guests grew confused",
        "need_hero": "My path is shorter for the little guests",
        "need_friend": "My path stays clear of the thorny hedge",
        "cob_role": "It was the bright marker where the picnic-path signs belonged",
        "repair": "walked both routes from the ground and made two clear arrow signs",
        "outcome": "pointed small guests along the short safe path and taller guests around the hedge",
        "proof": "Two painted arrows met beside the golden cob",
    },
    "stall": {
        "premise": "They were minding a vegetable stall under a cloth canopy when one fine cob remained",
        "trigger": "two customers arrived together and each friend promised the cob to someone else",
        "need_hero": "I gave my word to the hedgehog first",
        "need_friend": "I did not hear you, and I gave my word to the badger",
        "cob_role": "It was the last whole ear of corn at their market stall",
        "repair": "apologized to both customers and checked the basket for loose kernels and smaller ears",
        "outcome": "made two mixed corn parcels and wrote down every new promise",
        "proof": "Two equal market parcels sat beside an open promise book",
    },
    "storm": {
        "premise": "A gust had rolled their picnic cob from the blanket toward a puddle",
        "trigger": "each blamed the other for leaving it near the blanket's edge",
        "need_hero": "I thought you were holding the basket",
        "need_friend": "I thought you had tucked the blanket corner down",
        "cob_role": "It was part of their picnic and rolled toward a puddle in the wind",
        "repair": "used a ground-level leaf rake together to guide the cob into a basket",
        "outcome": "secured the blanket corners and washed the rescued cob",
        "proof": "The clean cob dried in its basket while four stones held the blanket",
    },
    "welcome": {
        "premise": "They were preparing corn-cob place markers for a welcome supper",
        "trigger": "both put their name beside the same sheltered seat",
        "need_hero": "That seat helps me hear the stories",
        "need_friend": "That seat keeps the bright sunset out of my eyes",
        "cob_role": "It was one of the name markers for seats at their welcome supper",
        "repair": "turned the table so two sheltered seats faced the storyteller",
        "outcome": "made room for each other and gave the best central place to their new guest",
        "proof": "Three named cobs stood in a welcoming row on the supper table",
    },
    "measure": {
        "premise": "They were using a corn cob as a playful measuring tool for their model bridge",
        "trigger": "their measurements disagreed because one began at the cob's tip",
        "need_hero": "I counted from the pointed end",
        "need_friend": "I counted only the straight middle part",
        "cob_role": "It was the unit they used to measure a model bridge",
        "repair": "placed a pebble at one starting line and measured again side by side",
        "outcome": "agreed on one method and rebuilt the bridge deck evenly",
        "proof": "The little bridge lay straight at exactly four cob-lengths",
    },
    "puppet": {
        "premise": "They were turning a husked corn cob into a puppet for the evening fable",
        "trigger": "one wanted the puppet to be brave while the other wanted it to be gentle",
        "need_hero": "A brave hero can face the storm",
        "need_friend": "A gentle hero can listen before acting",
        "cob_role": "It became the puppet who acted in their evening fable",
        "repair": "rewrote the puppet's choice so courage began with listening",
        "outcome": "performed a fable about a hero who heard everyone and then helped",
        "proof": "The cob puppet bowed between its tiny shield and listening horn",
    },
    "cleanup": {
        "premise": "After lunch, one bare cob and several husks remained on their blanket",
        "trigger": "each insisted that cleaning the picnic spot was the other's job",
        "need_hero": "I carried the food all the way here",
        "need_friend": "I spread the blanket and filled the water cups",
        "cob_role": "It was the leftover middle of their corn and belonged in the compost pail",
        "repair": "listed the jobs already done and chose two final chores apiece",
        "outcome": "put the cob in the compost pail and folded the clean blanket together",
        "proof": "Only smooth grass remained beneath the folded canopy blanket",
    },
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A reconciliation story is valid when a place supports sharing and talking.
valid_place(P) :- place(P), affords(P, talk), affords(P, share).

% The cob is the shared object that can cause a split.
shared_object(cob).

% The canopy is the shaded place where the argument starts.
shared_place(canopy).

% Encourage is the helper action that leads to reconciliation.
help_word(encourage).

valid_story(P, H, F, U) :-
    valid_place(P),
    hero(H),
    friend(F),
    helper(U).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import per contract

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    for uid in HELPERS:
        lines.append(asp.fact("helper", uid))
    lines.append(asp.fact("shared_object", "cob"))
    lines.append(asp.fact("shared_place", "canopy"))
    lines.append(asp.fact("help_word", "encourage"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p, h, f, u) for p in SETTINGS for h in HEROES for f in FRIENDS for u in HELPERS)
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python registry cartesian product ({len(cl)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero_cfg = HEROES[params.hero]
    friend_cfg = FRIENDS[params.friend]
    helper_cfg = HELPERS[params.helper]

    hero = world.add(Entity(id="hero", kind="character", type=hero_cfg["type"], label=hero_cfg["label"]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_cfg["type"], label=friend_cfg["label"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg["type"], label=helper_cfg["label"]))
    cob = world.add(Entity(id="cob", label="cob", phrase="a golden corn cob"))
    canopy = world.add(Entity(id="canopy", label="canopy", phrase="a cool green canopy of leaves"))

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        cob=cob,
        canopy=canopy,
        params=params,
        plan=SCENARIOS[params.scenario],
    )
    return world


def open_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    plan = world.facts["plan"]
    params: StoryParams = world.facts["params"]
    canopy_text = {
        "meadow": "the broad canopy of an old beech tree",
        "orchard": "the orchard's low green canopy",
        "lane": "a striped cloth canopy beside the lane",
    }[params.place]
    openings = [
        f"In {world.setting.place}, a little {hero.label} and a little {friend.label} had made a worktable beneath {canopy_text}.",
        f"Morning light flickered through {canopy_text} as a {hero.label} met a {friend.label} beside their worktable.",
        f"The {hero.label} and the {friend.label} often solved small problems together under {canopy_text}.",
        f"A cool patch beneath {canopy_text} was the {hero.label}'s and the {friend.label}'s favorite meeting place.",
        f"One busy day in {world.setting.place}, the {hero.label} and the {friend.label} spread their supplies on a low table beneath {canopy_text}.",
    ]
    world.say(openings[params.opening_style % len(openings)])
    world.say(f"{plan['premise']}, but {plan['trigger']}.")
    world.facts["canopy_text"] = canopy_text


def start_argument(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    plan = world.facts["plan"]
    params: StoryParams = world.facts["params"]

    hero.memes["want"] = 1
    friend.memes["want"] = 1
    hero.memes["stubborn"] = 1
    friend.memes["stubborn"] = 1
    hero.memes["hurt"] = 1
    friend.memes["hurt"] = 1

    world.para()
    conflicts = [
        f'"{plan["need_hero"]}," said the {hero.label}. "{plan["need_friend"]}," replied the {friend.label}. Neither paused to hear the reason inside the other answer.',
        f"The {hero.label} pointed toward the cob and insisted on one plan. The {friend.label} frowned and insisted on another. Soon they were defending ideas instead of solving the problem.",
        f"First the {hero.label} interrupted; then the {friend.label} spoke even louder. Their disagreement made the friendly shade feel narrow.",
        f'"You never listen!" cried the {hero.label}. "Neither do you!" answered the {friend.label}. The problem waited between them.',
        f"Each repeated the same reason more firmly, but neither heard anything new. Hurt replaced patience, and their shared work stopped.",
    ]
    world.say(conflicts[params.conflict_style % len(conflicts)])
    world.facts["conflict"] = plan["trigger"]


def encourage(world: World) -> None:
    helper: Entity = world.facts["helper"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    plan = world.facts["plan"]
    params: StoryParams = world.facts["params"]

    helper.memes["kind"] = 1
    world.para()
    interventions = [
        f'The {helper.label} listened and said, "A cob cannot tell us what is fair, but each of you can tell the other what you need." The {helper.label} encouraged one friend to speak and the other to repeat what had been heard.',
        f'The {helper.label} placed one leaf beside each friend. "Put an idea on your leaf before you judge the other idea," the helper encouraged. Soon both leaves held something useful.',
        f'"Let us lower our voices and raise our questions," said the {helper.label}. The helper encouraged them to ask why, not merely argue who was right.',
        f'The {helper.label} drew two circles in the dust, with an overlap in the middle. "Show me what each of you needs and what you can share," the helper encouraged.',
        f'The {helper.label} encouraged them to take three calm breaths. Then each friend said one apology and one hope for their shared task.',
    ]
    world.say(interventions[params.encouragement_style % len(interventions)])
    world.facts["helper_action"] = "encouraged both friends to listen, explain their needs, and seek a fair plan"


def reconcile(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    cob: Entity = world.facts["cob"]
    plan = world.facts["plan"]
    params: StoryParams = world.facts["params"]

    if "reconciled" in world.fired:
        return
    world.fired.add("reconciled")

    hero.memes["hurt"] = 0
    friend.memes["hurt"] = 0
    hero.memes["peace"] = 1
    friend.memes["peace"] = 1
    cob.owner = "shared"

    world.para()
    repairs = [
        f'The {hero.label} began, "I am sorry I stopped listening." The {friend.label} apologized for answering sharply. Together they {plan["repair"]}.',
        f"Once each could explain the other's need, the quarrel looked smaller. They {plan['repair']}, checking the plan together at every step.",
        f"The friends compared both needs point by point. Side by side, they {plan['repair']}.",
        f'"Your idea helps with one part," the {hero.label} admitted. "And yours helps with another," said the {friend.label}. So they {plan["repair"]}.',
        f"They named what was fair in each idea and made room for both needs. At last they {plan['repair']}.",
    ]
    world.say(repairs[params.repair_style % len(repairs)])

    endings = [
        f"Then they {plan['outcome']}. {plan['proof']}. Their reconciliation made friendship feel roomy again beneath the canopy.",
        f"Before the helper left, the friends promised to ask before assuming. That reconciliation prepared them to act together. They {plan['outcome']}. At sunset, {plan['proof'].lower()}.",
        f"Their reconciliation gave them a plan they had both shaped. They {plan['outcome']}. When a breeze stirred the canopy, {plan['proof'].lower()}.",
        f"Their disagreement had not vanished by magic; reconciliation had changed what they could do next. They {plan['outcome']}, and {plan['proof'].lower()}.",
        f"From then on, they remembered that reconciliation means returning to the work as friends. After they {plan['outcome']}, {plan['proof'].lower()}.",
    ]
    world.say(endings[params.ending_style % len(endings)])
    world.facts["resolution"] = plan["outcome"]
    world.facts["final_image"] = plan["proof"]


def tell(world: World) -> None:
    open_story(world)
    start_argument(world)
    encourage(world)
    reconcile(world)
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    plan = world.facts["plan"]
    return [
        'Write a short fable about a cob, a canopy, and a gentle reconciliation.',
        f"Tell a child-friendly story in {world.setting.place} where two small animals disagree because {plan['trigger']}, then encourage them to make peace.",
        f"Write a simple moral tale in which friends {plan['outcome']}. Use the words cob, canopy, encourage, and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    helper: Entity = world.facts["helper"]
    plan = world.facts["plan"]

    return [
        QAItem(
            question=f"Who were the little friends in the story?",
            answer=f"The little friends were the {hero.label} and the {friend.label}. They worked together beneath a canopy in {world.setting.place}.",
        ),
        QAItem(
            question="Why did the two friends begin to argue?",
            answer=f"They began to argue because {world.facts['conflict']}. Each friend defended a different need instead of listening.",
        ),
        QAItem(
            question=f"Who helped them calm down?",
            answer=f"The {helper.label} helped them calm down and {world.facts['helper_action']}.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The friends made peace and {world.facts['resolution']}. The ending shows the change: {world.facts['final_image']}.",
        ),
        QAItem(
            question="How did the friends use the cob in this story?",
            answer=f"{plan['cob_role']}. It remained part of the fair solution they made together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a canopy?",
            answer="A canopy is a covering over something. In a forest or orchard, the leaves high above can make a shady canopy.",
        ),
        QAItem(
            question="What is a cob?",
            answer="A cob is the hard middle part of an ear of corn. People can hold the cob after the kernels are taken off.",
        ),
        QAItem(
            question="What does encourage mean?",
            answer="To encourage someone means to help them feel braver, kinder, or ready to try a good choice.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a disagreement and becoming friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.meters:
            parts.append(f"meters={e.meters}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(parts)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about cob, canopy, and reconciliation.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    place = args.place or rng.choice(sorted(SETTINGS))
    hero = args.hero or rng.choice(sorted(HEROES))
    friend = args.friend or rng.choice(sorted(FRIENDS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    if friend == helper:
        helper = rng.choice([h for h in sorted(HELPERS) if h != friend])
    if hero == friend:
        friend = rng.choice([f for f in sorted(FRIENDS) if f != hero])
    return StoryParams(
        place=place,
        hero=hero,
        friend=friend,
        helper=helper,
        scenario=rng.choice(sorted(SCENARIOS)),
        opening_style=rng.randrange(5),
        conflict_style=rng.randrange(5),
        encouragement_style=rng.randrange(5),
        repair_style=rng.randrange(5),
        ending_style=rng.randrange(5),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for t in stories:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
