#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/coral_lord_macaw_surprise_mystery_to_solve.py
=========================================================================

A small fable-like storyworld about a fussy reef lord, a missing coral treasure,
and a clever macaw who solves the mystery with humor instead of blame.

The domain is intentionally tight. A coral object goes missing from Lord
Brindle's little court. A clue points toward one plausible innocent culprit.
Mica the macaw follows the clue, discovers what really happened, and helps the
lord end the day with an apology and a laugh.

Run it
------
    python storyworlds/worlds/gpt-5.4/coral_lord_macaw_surprise_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/coral_lord_macaw_surprise_mystery_to_solve.py --thing trumpet --culprit seal_pup
    python storyworlds/worlds/gpt-5.4/coral_lord_macaw_surprise_mystery_to_solve.py --thing cushion --culprit crab
    python storyworlds/worlds/gpt-5.4/coral_lord_macaw_surprise_mystery_to_solve.py --all --qa
    python storyworlds/worlds/gpt-5.4/coral_lord_macaw_surprise_mystery_to_solve.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "lady"}
        male = {"boy", "man", "lord"}
        bird = {"macaw", "parrot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male or self.type in bird:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"octopus", "seal", "turtle", "crab"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    label: str
    opening: str
    search_path: str
    habitats: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    kept_on: str
    desire: str
    weight: int
    driftable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    type: str
    habitat: str
    can_carry: int
    likes: set[str] = field(default_factory=set)
    signatures: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    signature: str
    text: str
    follow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    thing: str
    culprit: str
    clue: str
    lord_name: str
    macaw_name: str
    parent_word: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "arch": Setting(
        id="arch",
        label="the Coral Arch Court",
        opening="At the edge of a warm blue sea stood the Coral Arch Court, where every shell seemed polished and every wave looked as if it had been asked to bow first.",
        search_path="through the coral arch and down a ribbon of bright sea grass",
        habitats={"cave", "shore", "sand_lane", "current_lane"},
        tags={"coral", "reef"},
    ),
    "garden": Setting(
        id="garden",
        label="the Coral Garden Terrace",
        opening="On a sunny shelf of reef lay the Coral Garden Terrace, neat as a comb and pink as dawn.",
        search_path="past the coral pots and along the pebble border",
        habitats={"cave", "shore", "sand_lane", "current_lane"},
        tags={"coral", "garden"},
    ),
    "balcony": Setting(
        id="balcony",
        label="the Tide Balcony",
        opening="Above the tide pools hung the Tide Balcony, a coral ledge where the waves liked to clap against the rocks below.",
        search_path="under the balcony steps and beside the foamy pools",
        habitats={"cave", "shore", "sand_lane", "current_lane"},
        tags={"coral", "tide"},
    ),
}

THINGS = {
    "crown": MissingThing(
        id="crown",
        label="coral crown",
        phrase="a small coral crown with five rosy points",
        kept_on="a velvet clam stand",
        desire="shiny",
        weight=2,
        driftable=False,
        tags={"coral", "shiny"},
    ),
    "trumpet": MissingThing(
        id="trumpet",
        label="coral trumpet",
        phrase="a curly coral trumpet that could make a grand burbly toot",
        kept_on="a hook by the gate",
        desire="noisy",
        weight=1,
        driftable=True,
        tags={"coral", "sound"},
    ),
    "comb": MissingThing(
        id="comb",
        label="coral comb",
        phrase="a coral comb with tiny pearl teeth",
        kept_on="a silver dish",
        desire="shiny",
        weight=1,
        driftable=True,
        tags={"coral", "shiny"},
    ),
    "cushion": MissingThing(
        id="cushion",
        label="coral cushion",
        phrase="a puffy coral cushion sewn from sea silk",
        kept_on="the lord's round stool",
        desire="cozy",
        weight=2,
        driftable=False,
        tags={"coral", "cozy"},
    ),
}

CULPRITS = {
    "octopus": Culprit(
        id="octopus",
        label="an octopus",
        phrase="Old Inky the octopus",
        type="octopus",
        habitat="cave",
        can_carry=2,
        likes={"shiny", "cozy"},
        signatures={"ink"},
        tags={"octopus"},
    ),
    "seal_pup": Culprit(
        id="seal_pup",
        label="a seal pup",
        phrase="Pip the seal pup",
        type="seal",
        habitat="shore",
        can_carry=2,
        likes={"noisy", "cozy"},
        signatures={"splash"},
        tags={"seal"},
    ),
    "crab": Culprit(
        id="crab",
        label="a crab",
        phrase="Tippet the crab",
        type="crab",
        habitat="sand_lane",
        can_carry=1,
        likes={"shiny"},
        signatures={"sideways"},
        tags={"crab"},
    ),
    "current": Culprit(
        id="current",
        label="the tide current",
        phrase="a cheeky tide current",
        type="thing",
        habitat="current_lane",
        can_carry=1,
        likes={"drift"},
        signatures={"seaweed"},
        tags={"current"},
    ),
}

CLUES = {
    "ink": Clue(
        id="ink",
        label="ink spots",
        signature="ink",
        text="On the pale stone beside the stand, Mica saw three neat ink spots, as if someone with too many elbows had sneezed politely.",
        follow="The spots led toward a cool cave where rainbow light wobbled on the wall.",
        tags={"ink", "mystery"},
    ),
    "splash": Clue(
        id="splash",
        label="wet splashes",
        signature="splash",
        text="By the gate lay a line of wet splashes and one silly whisker mark, the sort of clue that looked as if it had barked at itself.",
        follow="The splashes skipped toward the shore pool where young creatures liked to practice looking important.",
        tags={"splash", "mystery"},
    ),
    "sideways": Clue(
        id="sideways",
        label="sideways tracks",
        signature="sideways",
        text="Across the sand ran a zigzag of sideways tracks, neat and bossy, as though two tiny commas had marched off with a secret.",
        follow="The tracks pointed toward a sand lane tucked between coral stones.",
        tags={"tracks", "mystery"},
    ),
    "seaweed": Clue(
        id="seaweed",
        label="a seaweed trail",
        signature="seaweed",
        text="A soft string of seaweed clung to the empty place, and the hook still dripped as if the sea itself had borrowed the thing without asking.",
        follow="The trail curled toward a narrow lane where the tide liked to tug at loose treasures.",
        tags={"seaweed", "mystery"},
    ),
}

LORD_NAMES = ["Brindle", "Tassel", "Ruffle", "Pebble"]
MACAW_NAMES = ["Mica", "Rico", "Jasper", "Pico"]


def plausible_culprit(thing: MissingThing, culprit: Culprit, setting: Setting) -> bool:
    if culprit.habitat not in setting.habitats:
        return False
    if culprit.id == "current":
        return thing.driftable and thing.weight <= culprit.can_carry
    return thing.weight <= culprit.can_carry and thing.desire in culprit.likes


def clue_matches(culprit: Culprit, clue: Clue) -> bool:
    return clue.signature in culprit.signatures


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for thing_id, thing in THINGS.items():
            for culprit_id, culprit in CULPRITS.items():
                if not plausible_culprit(thing, culprit, setting):
                    continue
                for clue_id, clue in CLUES.items():
                    if clue_matches(culprit, clue):
                        combos.append((setting_id, thing_id, culprit_id, clue_id))
    return combos


def explain_rejection(thing: MissingThing, culprit: Culprit, setting: Setting, clue: Optional[Clue] = None) -> str:
    if culprit.habitat not in setting.habitats:
        return (
            f"(No story: {culprit.label} does not fit {setting.label}. "
            f"The mystery needs a culprit who could really be nearby.)"
        )
    if culprit.id == "current":
        if not thing.driftable:
            return (
                f"(No story: {thing.label} is not loose enough for the tide current to carry. "
                f"Choose a lighter, driftable thing.)"
            )
        if thing.weight > culprit.can_carry:
            return (
                f"(No story: {thing.label} is too heavy for the tide current in this tiny world.)"
            )
    else:
        if thing.weight > culprit.can_carry:
            return (
                f"(No story: {culprit.label} could not reasonably carry {thing.label}. "
                f"The mystery needs a plausible mover.)"
            )
        if thing.desire not in culprit.likes:
            likes = ", ".join(sorted(culprit.likes))
            return (
                f"(No story: {culprit.label} has no good reason to take {thing.label}. "
                f"In this world, that culprit goes for {likes} things.)"
            )
    if clue is not None and not clue_matches(culprit, clue):
        return (
            f"(No story: {clue.label} does not point to {culprit.label}. "
            f"The clue and culprit must match.)"
        )
    return "(No story: the chosen mystery does not fit this world.)"


def culprit_place(culprit: Culprit) -> str:
    return {
        "octopus": "a little cave",
        "seal_pup": "the sunny shore pool",
        "crab": "a sand lane",
        "current": "a curl of sea grass",
    }[culprit.id]


def innocent_use(thing: MissingThing, culprit: Culprit) -> str:
    if culprit.id == "octopus":
        if thing.desire == "shiny":
            return f"had hung the {thing.label} where it tossed rainbow dots across the cave ceiling"
        return f"had borrowed the {thing.label} for the softest nap in the reef"
    if culprit.id == "seal_pup":
        if thing.desire == "noisy":
            return f"was using the {thing.label} as a bubble horn and tooting so proudly that even the minnows were giggling"
        return f"had balanced the {thing.label} on their nose and turned the shore pool into a one-creature circus"
    if culprit.id == "crab":
        return f"had set the {thing.label} in the sand and was admiring their reflection in it as if it were a moonlit mirror"
    return f"had rolled the {thing.label} into sea grass and tucked it where the tide could swish around it"

def surprise_image(thing: MissingThing, culprit: Culprit) -> str:
    if culprit.id == "octopus":
        return f"The missing {thing.label} was not hidden at all; it was glowing above the cave like a silly little sunrise."
    if culprit.id == "seal_pup":
        return f"There sat the missing {thing.label}, wobbling on a whiskery nose between two proud flippers."
    if culprit.id == "crab":
        return f"There, in the sand, the missing {thing.label} shone while a crab tilted from side to side like a judge praising a mirror."
    return f"There the missing {thing.label} rested in sea grass, bobbing so gently that it looked as if the sea had rocked it to sleep."


def opening(world: World, lord: Entity, macaw: Entity, thing: Entity, thing_cfg: MissingThing) -> None:
    lord.memes["pride"] += 1
    macaw.memes["cheer"] += 1
    world.say(world.setting.opening)
    world.say(
        f"Its master was Lord {lord.id}, a reef lord who liked neat rows, polished shells, "
        f"and especially {thing_cfg.phrase}, which he kept on {thing_cfg.kept_on}."
    )
    world.say(
        f"Each morning {macaw.id} the macaw flew in from the fig tree above the shore, "
        f"bright as a spilled paint box and twice as talkative."
    )


def loss(world: World, lord: Entity, macaw: Entity, thing: Entity, thing_cfg: MissingThing) -> None:
    thing.meters["missing"] += 1
    lord.memes["worry"] += 1
    world.say(
        f"But one dawn Lord {lord.id} blinked at {thing_cfg.kept_on}. It was empty. "
        f'"My {thing_cfg.label} is gone!" he cried.'
    )
    world.say(
        f'"Gone, gone, terribly gone," echoed {macaw.id}, then tipped his head. '
        f'"Or only somewhere else?"'
    )


def bluster(world: World, lord: Entity, culprit_cfg: Culprit) -> None:
    lord.memes["blame"] += 1
    if culprit_cfg.id == "current":
        world.say(
            f'Lord {lord.id} puffed himself up. "A thief with wet fingers has done this!" he declared, '
            f'although no one knew what wet fingers a tide current might have.'
        )
    else:
        world.say(
            f'Lord {lord.id} puffed himself up. "It must have been {culprit_cfg.label}!" he declared, '
            f'before he had looked for so much as a pebble of proof.'
        )


def investigate(world: World, macaw: Entity, clue_cfg: Clue) -> None:
    macaw.memes["curiosity"] += 1
    world.say(
        f'{macaw.id} hopped closer instead of arguing. {clue_cfg.text}'
    )
    world.say(
        f'"Mysteries do not like shouting," said the macaw. "{clue_cfg.label.capitalize()} first, guesses later."'
    )


def follow_clue(world: World, setting: Setting, clue_cfg: Clue) -> None:
    world.say(
        f"So Lord Brindle and the macaw went {setting.search_path}. {clue_cfg.follow}"
    )


def reveal(world: World, lord: Entity, macaw: Entity, thing: Entity, thing_cfg: MissingThing,
           culprit: Entity, culprit_cfg: Culprit) -> None:
    thing.meters["found"] += 1
    thing.meters["missing"] = 0.0
    lord.memes["surprise"] += 1
    culprit.memes["innocent"] += 1
    world.say(surprise_image(thing_cfg, culprit_cfg))
    world.say(
        f"{culprit_cfg.phrase} {innocent_use(thing_cfg, culprit_cfg)}."
    )
    if culprit_cfg.id == "seal_pup":
        world.say(
            f'Toot! went the {thing_cfg.label}, and {macaw.id} nearly laughed off his perch.'
        )
    elif culprit_cfg.id == "octopus":
        world.say(
            f'The cave walls flashed pink and gold, and even Lord {lord.id} had to blink twice before he could remember to look annoyed.'
        )
    elif culprit_cfg.id == "crab":
        world.say(
            f'"Handsome," said Tippet to the shiny coral, and then, after a pause, "I mean the coral, of course."'
        )
    else:
        world.say(
            f'The tide gave one innocent slosh, which sounded very much like a shrug.'
        )


def apology(world: World, lord: Entity, macaw: Entity, culprit: Entity, culprit_cfg: Culprit, thing_cfg: MissingThing) -> None:
    lord.memes["embarrassment"] += 1
    lord.memes["wisdom"] += 1
    if culprit_cfg.id == "current":
        world.say(
            f'Lord {lord.id} lowered his voice. "So nobody stole it at all. I blamed the world before I asked what the water had done."'
        )
    else:
        world.say(
            f'Lord {lord.id} lowered his voice. "I am sorry, {culprit_cfg.phrase}. I blamed you before I knew the truth."'
        )
    world.say(
        f'{macaw.id} fluffed his green wings. "A loud guess is not the same as an answer," he said. "It only makes the answer wait longer."'
    )
    world.say(
        f'Lord {lord.id} carried the {thing_cfg.label} home more gently than before.'
    )


def ending(world: World, lord: Entity, macaw: Entity, thing_cfg: MissingThing) -> None:
    lord.memes["calm"] += 1
    macaw.memes["pride"] += 1
    world.say(
        f"That evening the coral court looked softer than usual. Lord {lord.id} set the {thing_cfg.label} back in its place, "
        f"then tied it with a little ribbon so it would not wander so easily again."
    )
    world.say(
        f"After that, whenever something went missing, the reef heard Lord {lord.id} clear his throat and ask, "
        f'"What are the clues?" before he asked, "Who did it?"'
    )
    world.say(
        f"And {macaw.id} the macaw would grin from above and say, "
        f'"Good. A careful question has a shorter beak than a foolish accusation."'
    )


def tell(setting: Setting, thing_cfg: MissingThing, culprit_cfg: Culprit, clue_cfg: Clue,
         lord_name: str, macaw_name: str) -> World:
    world = World(setting)
    lord = world.add(Entity(id=lord_name, kind="character", type="lord", label=f"Lord {lord_name}", role="lord"))
    macaw = world.add(Entity(id=macaw_name, kind="character", type="macaw", label=f"{macaw_name} the macaw", role="solver"))
    culprit = world.add(Entity(id=culprit_cfg.id, kind="character", type=culprit_cfg.type, label=culprit_cfg.label, role="culprit"))
    thing = world.add(Entity(id="thing", kind="thing", type="treasure", label=thing_cfg.label, phrase=thing_cfg.phrase, role="missing"))

    opening(world, lord, macaw, thing, thing_cfg)
    world.para()
    loss(world, lord, macaw, thing, thing_cfg)
    bluster(world, lord, culprit_cfg)
    investigate(world, macaw, clue_cfg)
    world.para()
    follow_clue(world, setting, clue_cfg)
    reveal(world, lord, macaw, thing, thing_cfg, culprit, culprit_cfg)
    world.para()
    apology(world, lord, macaw, culprit, culprit_cfg, thing_cfg)
    ending(world, lord, macaw, thing_cfg)

    world.facts.update(
        setting=setting,
        thing_cfg=thing_cfg,
        culprit_cfg=culprit_cfg,
        clue_cfg=clue_cfg,
        lord=lord,
        macaw=macaw,
        culprit=culprit,
        thing=thing,
        moral="Look for clues before you blame.",
    )
    return world


KNOWLEDGE = {
    "coral": [
        (
            "What is coral?",
            "Coral is made by tiny sea animals that build hard shapes together. Those shapes can look like branches, fans, or little stone gardens under the sea."
        )
    ],
    "macaw": [
        (
            "What is a macaw?",
            "A macaw is a large, colorful parrot with a strong curved beak. Macaws are bright, noisy birds and very good at noticing things around them."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Good detectives notice clues before they decide what happened."
        )
    ],
    "apology": [
        (
            "What is an apology?",
            "An apology is when you say you are sorry for something wrong you did. A real apology shows you understand the hurt and want to do better."
        )
    ],
    "current": [
        (
            "What is a tide current?",
            "A tide current is moving sea water. It can push light things along even when nobody touches them."
        )
    ],
}
KNOWLEDGE_ORDER = ["coral", "macaw", "clue", "apology", "current"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    thing = f["thing_cfg"]
    culprit = f["culprit_cfg"]
    clue = f["clue_cfg"]
    lord = f["lord"]
    macaw = f["macaw"]
    return [
        f'Write a short fable for a young child that includes the words "coral", "lord", and "macaw", and centers on a missing {thing.label}.',
        f"Tell a humorous mystery-to-solve story where Lord {lord.id} blames too quickly, but {macaw.id} the macaw follows {clue.label} and finds the truth.",
        f"Write a gentle surprise story in a fable style where {culprit.phrase} turns out not to be wicked at all, and the ending teaches that clues should come before accusations.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lord = f["lord"]
    macaw = f["macaw"]
    thing = f["thing_cfg"]
    culprit = f["culprit_cfg"]
    clue = f["clue_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Lord {lord.id}, a fussy reef lord; {macaw.id} the macaw, who solves the mystery; and the missing {thing.label}. The story is also about the one who really moved it."
        ),
        (
            f"What went missing?",
            f"The missing object was the {thing.label}. Lord {lord.id} loved it and noticed at once when its place was empty."
        ),
        (
            f"How did {macaw.id} begin solving the mystery?",
            f"{macaw.id} did not start by arguing. He looked for {clue.label} first, because the clue could show what had really happened."
        ),
        (
            f"What was the surprise at the end of the search?",
            f"The surprise was that the {thing.label} had not been taken out of meanness. {culprit.phrase} had it for an innocent reason, so the mystery ended with relief and laughter instead of a punishment."
        ),
        (
            f"Why did Lord {lord.id} have to apologize?",
            f"He accused someone before he had proof. When the clue led to the true answer, he saw that his loud guess had been unfair."
        ),
        (
            "What is the lesson of the story?",
            f"The lesson is: {f['moral']} The lord learns this because the clue tells the truth better than his temper does."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"coral", "macaw", "clue", "apology"}
    if world.facts["culprit_cfg"].id == "current":
        tags.add("current")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
plausible(S, T, C) :- setting(S), thing(T), culprit(C), habitat(C, H), allows(S, H),
                      not current(C), carry(C, Cap), weight(T, W), W <= Cap,
                      desire(T, D), likes(C, D).

plausible(S, T, C) :- setting(S), thing(T), culprit(C), habitat(C, H), allows(S, H),
                      current(C), driftable(T), carry(C, Cap), weight(T, W), W <= Cap.

valid(S, T, C, Cl) :- plausible(S, T, C), clue(Cl), signature(C, Sig), clue_sig(Cl, Sig).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for habitat in sorted(setting.habitats):
            lines.append(asp.fact("allows", setting_id, habitat))
    for thing_id, thing in THINGS.items():
        lines.append(asp.fact("thing", thing_id))
        lines.append(asp.fact("weight", thing_id, thing.weight))
        lines.append(asp.fact("desire", thing_id, thing.desire))
        if thing.driftable:
            lines.append(asp.fact("driftable", thing_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("habitat", culprit_id, culprit.habitat))
        lines.append(asp.fact("carry", culprit_id, culprit.can_carry))
        if culprit_id == "current":
            lines.append(asp.fact("current", culprit_id))
        for like in sorted(culprit.likes):
            lines.append(asp.fact("likes", culprit_id, like))
        for sig in sorted(culprit.signatures):
            lines.append(asp.fact("signature", culprit_id, sig))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_sig", clue_id, clue.signature))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        setting="arch",
        thing="trumpet",
        culprit="seal_pup",
        clue="splash",
        lord_name="Brindle",
        macaw_name="Mica",
        parent_word="narrator",
    ),
    StoryParams(
        setting="garden",
        thing="crown",
        culprit="octopus",
        clue="ink",
        lord_name="Tassel",
        macaw_name="Rico",
        parent_word="narrator",
    ),
    StoryParams(
        setting="balcony",
        thing="comb",
        culprit="crab",
        clue="sideways",
        lord_name="Ruffle",
        macaw_name="Jasper",
        parent_word="narrator",
    ),
    StoryParams(
        setting="arch",
        thing="trumpet",
        culprit="current",
        clue="seaweed",
        lord_name="Pebble",
        macaw_name="Pico",
        parent_word="narrator",
    ),
    StoryParams(
        setting="garden",
        thing="cushion",
        culprit="seal_pup",
        clue="splash",
        lord_name="Brindle",
        macaw_name="Mica",
        parent_word="narrator",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fable-like storyworld about a coral mystery, a reef lord, and a clever macaw."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--lord-name")
    ap.add_argument("--macaw-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid mystery combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.thing and args.culprit:
        setting = SETTINGS[args.setting]
        thing = THINGS[args.thing]
        culprit = CULPRITS[args.culprit]
        clue = CLUES[args.clue] if args.clue else None
        if not plausible_culprit(thing, culprit, setting):
            raise StoryError(explain_rejection(thing, culprit, setting, clue))
        if clue is not None and not clue_matches(culprit, clue):
            raise StoryError(explain_rejection(thing, culprit, setting, clue))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.thing is None or combo[1] == args.thing)
        and (args.culprit is None or combo[2] == args.culprit)
        and (args.clue is None or combo[3] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, thing_id, culprit_id, clue_id = rng.choice(sorted(combos))
    lord_name = args.lord_name or rng.choice(LORD_NAMES)
    macaw_name = args.macaw_name or rng.choice([n for n in MACAW_NAMES if n != lord_name])
    return StoryParams(
        setting=setting_id,
        thing=thing_id,
        culprit=culprit_id,
        clue=clue_id,
        lord_name=lord_name,
        macaw_name=macaw_name,
        parent_word="narrator",
    )


def validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.thing not in THINGS:
        raise StoryError(f"(Unknown thing: {params.thing})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    setting = SETTINGS[params.setting]
    thing = THINGS[params.thing]
    culprit = CULPRITS[params.culprit]
    clue = CLUES[params.clue]
    if not plausible_culprit(thing, culprit, setting) or not clue_matches(culprit, clue):
        raise StoryError(explain_rejection(thing, culprit, setting, clue))


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        thing_cfg=THINGS[params.thing],
        culprit_cfg=CULPRITS[params.culprit],
        clue_cfg=CLUES[params.clue],
        lord_name=params.lord_name,
        macaw_name=params.macaw_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def asp_verify() -> int:
    rc = 0
    try:
        clingo_set = set(asp_valid_combos())
    except Exception as err:
        print(f"VERIFY FAIL: ASP execution crashed: {err}")
        return 1

    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP valid combos match Python ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"VERIFY FAIL: smoke generation crashed: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if "macaw" not in sample.story.lower() or "lord" not in sample.story.lower() or "coral" not in sample.story.lower():
            raise StoryError("Generated story missed required seed words.")
        print("OK: default random generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"VERIFY FAIL: default generation crashed: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, thing, culprit, clue) combos:\n")
        for setting_id, thing_id, culprit_id, clue_id in combos:
            print(f"  {setting_id:8} {thing_id:8} {culprit_id:10} {clue_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### Lord {p.lord_name}: {p.thing} / {p.culprit} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
