#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/delish_moral_value_magic_reconciliation_detective_story.py
=====================================================================================

A tiny detective-style storyworld about a missing treat, a magical clue, and the
truth that mends a friendship.

The seed asked for:
- the word "delish"
- Moral Value
- Magic
- Reconciliation
- Detective Story style

This world turns that into a small simulation:
two children investigate a missing bake-fair treat with the help of a gentle
magical clue. One child has hidden the treat for an emotional reason. The
detective work reveals not a villain but a mistake, and the ending depends on
whether the treat was kept safely or slightly damaged in hiding. The moral value
is honesty; the resolution is reconciliation.

Run it
------
python storyworlds/worlds/gpt-5.4/delish_moral_value_magic_reconciliation_detective_story.py
python storyworlds/worlds/gpt-5.4/delish_moral_value_magic_reconciliation_detective_story.py --treat moon_tart --place breadbox --motive fear_judged --repair present_together
python storyworlds/worlds/gpt-5.4/delish_moral_value_magic_reconciliation_detective_story.py --treat cream_puff --place windowsill
python storyworlds/worlds/gpt-5.4/delish_moral_value_magic_reconciliation_detective_story.py --all
python storyworlds/worlds/gpt-5.4/delish_moral_value_magic_reconciliation_detective_story.py --qa --json
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when this script is run directly:
# this file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    crumb: str
    frosting: bool = False
    flaky: bool = False
    crisp: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    warm: bool = False
    cramped: bool = False
    damp: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Motive:
    id: str
    label: str
    text: str
    confession: str
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicAid:
    id: str
    label: str
    clue_intro: str
    clue_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    action_text: str
    apology_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


TREATS = {
    "moon_tart": Treat(
        id="moon_tart",
        label="moon tart",
        phrase="a silver-iced moon tart",
        crumb="silver crumbs",
        frosting=True,
        flaky=True,
        tags={"tart", "food"},
    ),
    "cream_puff": Treat(
        id="cream_puff",
        label="cream puff",
        phrase="a cream puff with a sugar cloud on top",
        crumb="tiny sugar dots",
        frosting=True,
        flaky=False,
        tags={"pastry", "food"},
    ),
    "jam_roll": Treat(
        id="jam_roll",
        label="jam roll",
        phrase="a berry jam roll dusted with sugar",
        crumb="ruby jam specks",
        crisp=False,
        flaky=False,
        tags={"roll", "food"},
    ),
    "ginger_cookie": Treat(
        id="ginger_cookie",
        label="ginger cookie",
        phrase="a star-shaped ginger cookie",
        crumb="golden crumbs",
        crisp=True,
        flaky=False,
        tags={"cookie", "food"},
    ),
}

PLACES = {
    "breadbox": HidingPlace(
        id="breadbox",
        label="breadbox",
        phrase="inside the breadbox beside the kitchen wall",
        tags={"kitchen", "box"},
    ),
    "windowsill": HidingPlace(
        id="windowsill",
        label="windowsill",
        phrase="on the sunny windowsill above the sink",
        warm=True,
        tags={"window", "sun"},
    ),
    "coat_pocket": HidingPlace(
        id="coat_pocket",
        label="coat pocket",
        phrase="inside a hanging coat pocket by the back door",
        cramped=True,
        tags={"pocket", "hall"},
    ),
    "flowerpot": HidingPlace(
        id="flowerpot",
        label="flowerpot",
        phrase="behind the wide flowerpot near the watering can",
        damp=True,
        tags={"garden", "damp"},
    ),
}

MOTIVES = {
    "fear_judged": Motive(
        id="fear_judged",
        label="fear of being judged",
        text="worried that everyone would laugh if the bake did not look perfect",
        confession="I hid it because I got scared that people would judge it before tasting it.",
        moral="Being honest is braver than hiding a mistake or a fear.",
        tags={"honesty", "fear"},
    ),
    "jealous": Motive(
        id="jealous",
        label="jealousy",
        text="felt a sharp little pinch of jealousy when the treat looked so beautiful",
        confession="I hid it because I felt jealous, and that was not kind.",
        moral="Jealous feelings can visit anyone, but kindness means telling the truth instead of acting on them.",
        tags={"honesty", "kindness"},
    ),
    "surprise": Motive(
        id="surprise",
        label="misguided surprise",
        text="wanted to make the reveal feel grand and mysterious, but chose the wrong way",
        confession="I meant it as a surprise, but I should have told the truth first.",
        moral="A surprise should never grow out of a secret that makes someone afraid.",
        tags={"honesty", "sharing"},
    ),
}

MAGIC = {
    "glow_crumbs": MagicAid(
        id="glow_crumbs",
        label="glow crumbs",
        clue_intro="When the children whispered their detective promise, the crumbs on the plate began to glow pale blue.",
        clue_line='The glowing crumbs twinkled in a thin trail, as if saying, "This way, little detectives."',
        ending_image="A last blue crumb winked and went dark, as if the magic itself was pleased the truth had been spoken.",
        tags={"magic", "clue"},
    ),
    "whisper_teapot": MagicAid(
        id="whisper_teapot",
        label="whispering teapot",
        clue_intro="The old teapot on the counter gave a polite little rattle and began to whisper clues in a steam-soft voice.",
        clue_line='It puffed one sweet-smelling breath toward the trail and seemed to murmur, "Follow where the sugar settled."',
        ending_image="The teapot let out one happy ping and settled into silence.",
        tags={"magic", "teapot"},
    ),
    "lantern_moth": MagicAid(
        id="lantern_moth",
        label="lantern moth",
        clue_intro="A tiny lantern moth fluttered from the cupboard, carrying a spark of gold on its wings.",
        clue_line='The lantern moth bobbed through the room and paused wherever the missing treat had brushed the air.',
        ending_image="The lantern moth circled once above their heads and drifted back into the warm light.",
        tags={"magic", "moth"},
    ),
}

REPAIRS = {
    "present_together": Repair(
        id="present_together",
        label="present together",
        action_text="They carried the treat back together and set it on the fair table side by side.",
        apology_text='Then the hider said sorry, and the two children chose to present the treat together instead of apart.',
        tags={"reconciliation", "truth"},
    ),
    "share_credit": Repair(
        id="share_credit",
        label="share credit",
        action_text="They returned the treat and made a new card with both of their names written neatly on it.",
        apology_text='The apology came with a promise to share credit fairly, and the tight feeling between them finally loosened.',
        tags={"reconciliation", "sharing"},
    ),
    "help_remake": Repair(
        id="help_remake",
        label="help remake",
        action_text="Because the treat had been spoiled a little in hiding, they hurried to the kitchen and remade it together.",
        apology_text='The one who hid it apologized with wet eyes and helpful hands, and the new batch rose warmer than the first.',
        tags={"reconciliation", "repair"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Ava", "Lucy", "Zoe", "Mina", "Ella"]
BOY_NAMES = ["Jules", "Theo", "Ben", "Noah", "Leo", "Finn", "Eli", "Owen"]


def damage_score(treat: Treat, place: HidingPlace) -> int:
    score = 0
    if treat.frosting and place.warm:
        score += 1
    if treat.flaky and place.cramped:
        score += 1
    if treat.crisp and place.damp:
        score += 1
    return score


def repair_fits(motive: Motive, repair: Repair, damage: int) -> bool:
    if damage > 0:
        return repair.id == "help_remake"
    allowed = {
        "fear_judged": {"present_together", "help_remake"},
        "jealous": {"share_credit", "help_remake"},
        "surprise": {"present_together", "share_credit"},
    }
    return repair.id in allowed[motive.id]


def valid_combo_ids() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for treat_id, treat in TREATS.items():
        for place_id, place in PLACES.items():
            damage = damage_score(treat, place)
            if damage > 1:
                continue
            for motive_id, motive in MOTIVES.items():
                for repair_id, repair in REPAIRS.items():
                    if repair_fits(motive, repair, damage):
                        combos.append((treat_id, place_id, motive_id, repair_id))
    return combos


@dataclass
class StoryParams:
    treat: str
    place: str
    motive: str
    magic: str
    repair: str
    detective: str
    detective_gender: str
    baker: str
    baker_gender: str
    hider: str
    hider_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        treat="moon_tart",
        place="breadbox",
        motive="fear_judged",
        magic="glow_crumbs",
        repair="present_together",
        detective="Mira",
        detective_gender="girl",
        baker="Theo",
        baker_gender="boy",
        hider="Lina",
        hider_gender="girl",
        parent="mother",
    ),
    StoryParams(
        treat="cream_puff",
        place="windowsill",
        motive="fear_judged",
        magic="whisper_teapot",
        repair="help_remake",
        detective="Jules",
        detective_gender="boy",
        baker="Ava",
        baker_gender="girl",
        hider="Ben",
        hider_gender="boy",
        parent="father",
    ),
    StoryParams(
        treat="jam_roll",
        place="coat_pocket",
        motive="jealous",
        magic="lantern_moth",
        repair="help_remake",
        detective="Lucy",
        detective_gender="girl",
        baker="Noah",
        baker_gender="boy",
        hider="Mina",
        hider_gender="girl",
        parent="mother",
    ),
    StoryParams(
        treat="ginger_cookie",
        place="breadbox",
        motive="surprise",
        magic="glow_crumbs",
        repair="share_credit",
        detective="Leo",
        detective_gender="boy",
        baker="Nora",
        baker_gender="girl",
        hider="Ella",
        hider_gender="girl",
        parent="father",
    ),
]


def explain_rejection(treat: Treat, place: HidingPlace, motive: Optional[Motive] = None,
                      repair: Optional[Repair] = None) -> str:
    damage = damage_score(treat, place)
    if damage > 1:
        return (
            f"(No story: hiding {treat.phrase} at the {place.label} would ruin it too badly. "
            f"A detective story needs a recoverable mistake, not a hopeless mush.)"
        )
    if motive is not None and repair is not None and not repair_fits(motive, repair, damage):
        if damage > 0:
            return (
                f"(No story: once {treat.label} is slightly spoiled in that hiding place, "
                f"the only honest repair is to help remake it together.)"
            )
        return (
            f"(No story: the repair '{repair.id}' does not match the motive '{motive.id}'. "
            f"The apology must fit the harm that was done.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    treat = TREATS[params.treat]
    place = PLACES[params.place]
    damage = damage_score(treat, place)
    return "remade" if damage > 0 else "found"


def build_world_entities(params: StoryParams) -> World:
    world = World()
    detective = world.add(Entity(
        id=params.detective,
        kind="character",
        type=params.detective_gender,
        role="detective",
        label=params.detective,
    ))
    baker = world.add(Entity(
        id=params.baker,
        kind="character",
        type=params.baker_gender,
        role="baker",
        label=params.baker,
    ))
    hider = world.add(Entity(
        id=params.hider,
        kind="character",
        type=params.hider_gender,
        role="hider",
        label=params.hider,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        role="parent",
        label="the parent",
    ))
    treat = world.add(Entity(
        id="treat",
        kind="thing",
        type="treat",
        label=TREATS[params.treat].label,
    ))
    world.facts.update(
        detective=detective,
        baker=baker,
        hider=hider,
        parent=parent,
        treat_cfg=TREATS[params.treat],
        place_cfg=PLACES[params.place],
        motive_cfg=MOTIVES[params.motive],
        magic_cfg=MAGIC[params.magic],
        repair_cfg=REPAIRS[params.repair],
        treat_ent=treat,
    )
    return world


def opening_scene(world: World) -> None:
    baker = world.facts["baker"]
    detective = world.facts["detective"]
    treat = world.facts["treat_cfg"]
    parent = world.facts["parent"]
    baker.memes["pride"] += 1
    detective.memes["curiosity"] += 1
    world.say(
        f"On the morning of the neighborhood bake fair, {baker.id} carried in {treat.phrase} on a blue plate."
    )
    world.say(
        f'"That looks delish," said {detective.id}, leaning close enough to smell the sugar and spice.'
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled and set the judging table by the sunny hall window."
    )
    world.say(
        f"{baker.id} felt proud, and {detective.id} felt the special sort of excitement that belongs to a good mystery."
    )


def disappearance(world: World) -> None:
    baker = world.facts["baker"]
    hider = world.facts["hider"]
    treat = world.facts["treat_ent"]
    motive = world.facts["motive_cfg"]
    baker.memes["worry"] += 1
    hider.memes["guilt"] += 1
    treat.meters["hidden"] += 1
    world.say(
        f"But when the ribbon for judging was fetched and everyone turned back, the plate was empty."
    )
    world.say(
        f"{baker.id} blinked at the bare plate, and {hider.id} went quiet at once."
    )
    world.say(
        f"No one had seen the missing treat go, yet the room still smelled sweet and warm."
    )
    world.facts["hider_reason_text"] = motive.text


def detective_vow(world: World) -> None:
    detective = world.facts["detective"]
    baker = world.facts["baker"]
    magic = world.facts["magic_cfg"]
    detective.memes["resolve"] += 1
    baker.memes["hope"] += 1
    world.say(
        f'"Detective work begins now," {detective.id} whispered. "{baker.id}, I will help you find it."'
    )
    world.say(magic.clue_intro)
    world.say(magic.clue_line)


def follow_clues(world: World) -> None:
    detective = world.facts["detective"]
    baker = world.facts["baker"]
    place = world.facts["place_cfg"]
    treat = world.facts["treat_cfg"]
    damage = damage_score(treat, place)
    world.say(
        f"The clues were tiny but true: {treat.crumb} on the table edge, one sweet smear on the floor, and a soft trail leading toward {place.phrase}."
    )
    if damage > 0:
        world.say(
            f"{detective.id} narrowed {detective.pronoun('possessive')} eyes. The place was not terrible, but it was not kind to a treat like that either."
        )
    else:
        world.say(
            f"{detective.id} nodded slowly. It looked like a hiding place chosen in a hurry, not a thief's grand escape."
        )
    world.say(
        f"{baker.id} followed close behind, breathing a little easier because a real clue feels better than a dark guess."
    )


def reveal_truth(world: World) -> None:
    baker = world.facts["baker"]
    hider = world.facts["hider"]
    place = world.facts["place_cfg"]
    motive = world.facts["motive_cfg"]
    treat = world.facts["treat_cfg"]
    damage = damage_score(treat, place)

    hider.memes["guilt"] += 1
    hider.memes["shame"] += 1
    baker.memes["hurt"] += 1
    world.say(
        f"When {detective_name(world)} reached toward {place.label}, {hider.id} spoke first."
    )
    world.say(
        f'"Wait," {hider.id} said, cheeks turning pink. "{motive.confession}"'
    )
    world.say(
        f"{hider.id} admitted that {hider.pronoun()} had {motive.text}, and that was why {hider.pronoun()} hid the {treat.label} instead of speaking honestly."
    )
    if damage > 0:
        world.say(
            f"When they looked at it, the treat was still sweet-smelling but a little spoiled from the hiding place."
        )
    else:
        world.say(
            f"When they looked at it, the treat was safe. The real hurt was not in the pastry at all, but in the frightened secret."
        )
    world.facts["damage"] = damage
    world.facts["found_whole"] = damage == 0


def detective_name(world: World) -> str:
    return world.facts["detective"].id


def moral_turn(world: World) -> None:
    detective = world.facts["detective"]
    baker = world.facts["baker"]
    hider = world.facts["hider"]
    motive = world.facts["motive_cfg"]
    detective.memes["care"] += 1
    baker.memes["listening"] += 1
    hider.memes["hope"] += 1
    world.say(
        f'{detective.id} did not shout. "{hider.id}," {detective.pronoun()} said gently, "a mystery gets smaller when the truth steps into the light."'
    )
    world.say(
        f"{baker.id} swallowed hard, then listened. That was the brave part too: not only telling the truth, but making room to hear it."
    )
    world.say(motive.moral)


def reconcile(world: World) -> None:
    baker = world.facts["baker"]
    hider = world.facts["hider"]
    repair = world.facts["repair_cfg"]
    magic = world.facts["magic_cfg"]
    damage = world.facts["damage"]

    baker.memes["forgiveness"] += 1
    hider.memes["relief"] += 1
    hider.memes["trust"] += 1
    baker.memes["trust"] += 1

    world.say(repair.action_text)
    world.say(repair.apology_text)

    if damage > 0:
        world.say(
            f"Soon the kitchen filled with new sugar, warm laughter, and the steady sound of two children fixing what one of them had bent out of shape."
        )
    else:
        world.say(
            f"The tight little knot between them loosened as soon as the truth and the apology were both on the table."
        )
    world.say(magic.ending_image)
    world.say(
        f"When the fair began, the children stood together, and the treat tasted even better because nobody was hiding anymore."
    )


def tell(params: StoryParams) -> World:
    world = build_world_entities(params)
    opening_scene(world)
    world.para()
    disappearance(world)
    detective_vow(world)
    follow_clues(world)
    world.para()
    reveal_truth(world)
    moral_turn(world)
    world.para()
    reconcile(world)
    world.facts["outcome"] = outcome_of(params)
    return world


def generation_prompts(world: World) -> list[str]:
    detective = world.facts["detective"]
    baker = world.facts["baker"]
    treat = world.facts["treat_cfg"]
    motive = world.facts["motive_cfg"]
    magic = world.facts["magic_cfg"]
    outcome = world.facts["outcome"]
    ending = "they remake the treat and mend the friendship" if outcome == "remade" else "the truth is spoken and the friendship is mended"
    return [
        f'Write a detective story for a young child that includes the word "delish", a missing {treat.label}, and gentle magic clues.',
        f"Tell a small mystery where {detective.id} helps {baker.id} investigate a hidden bake-fair treat, and the case ends when {ending}.",
        f'Write a story with moral value, magic, and reconciliation, where {motive.label} causes the trouble and {magic.label} helps reveal the truth.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    detective = world.facts["detective"]
    baker = world.facts["baker"]
    hider = world.facts["hider"]
    parent = world.facts["parent"]
    treat = world.facts["treat_cfg"]
    place = world.facts["place_cfg"]
    motive = world.facts["motive_cfg"]
    repair = world.facts["repair_cfg"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, {baker.id}, and {hider.id} at the neighborhood bake fair. {detective.id} acts like a gentle detective when {baker.id}'s {treat.label} goes missing.",
        ),
        (
            f"What went missing?",
            f"The missing thing was {treat.phrase}. It disappeared from its plate just before judging.",
        ),
        (
            f"How did the children investigate the mystery?",
            f"They followed small clues and also received help from {world.facts['magic_cfg'].label}. The magical clue pointed them toward {place.phrase}.",
        ),
        (
            f"Why did {hider.id} hide the treat?",
            f"{hider.id} hid it because {hider.pronoun()} had {motive.text}. The problem was not hunger or meanness alone, but a feeling that should have been spoken honestly.",
        ),
    ]
    if outcome == "remade":
        qa.append((
            "Was the treat all right when they found it?",
            f"Not quite. The treat had been spoiled a little by the hiding place, so the children had to remake it together. That repair mattered because the apology needed helpful action too.",
        ))
    else:
        qa.append((
            "What was the real problem if the treat was still safe?",
            f"The real problem was the secret and the hurt it caused. Even though the treat was safe, {baker.id} had been frightened and confused until the truth was told.",
        ))
    qa.append((
        "How did the story show reconciliation?",
        f"{repair.action_text} {repair.apology_text} By the end, the children stood together again because honesty made room for forgiveness.",
    ))
    qa.append((
        "What moral did the story teach?",
        f"It taught that honesty is braver than hiding a fearful or jealous feeling. Telling the truth helped fix both the missing-treat mystery and the friendship.",
    ))
    qa.append((
        f"What did {parent.label_word} do in the story?",
        f"{parent.label_word.capitalize()} set up the fair table at the beginning and gave the children a warm place to make things right. The grown-up background made the children's truthful choice feel safe enough to happen.",
    ))
    return qa


KNOWLEDGE = {
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is something impossible in real life, like glowing crumbs or a whispering teapot. Writers use it to make the world feel wondrous and to help hidden feelings come into the open."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and asks careful questions to solve a mystery. A good detective does not only find things; a good detective also tries to understand what really happened."
        )
    ],
    "honesty": [
        (
            "Why is honesty important when you make a mistake?",
            "Honesty helps people understand what happened and begin to fix it. Telling the truth can feel hard for a moment, but hiding the truth usually makes the hurt bigger."
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people come back together after hurt or conflict. It usually needs truth, an apology, and some caring action that shows the relationship matters."
        )
    ],
    "jealousy": [
        (
            "What can you do if you feel jealous?",
            "You can take a breath and tell the truth about the feeling instead of acting on it. Jealousy becomes easier to handle when it is named kindly and honestly."
        )
    ],
    "fear": [
        (
            "What should you do if you are afraid people will laugh at your work?",
            "You can tell a trusted person how you feel and ask for help. Sharing a fear is often the first step toward feeling brave."
        )
    ],
    "baking": [
        (
            "Why do warm places change some treats?",
            "Warm places can melt icing or make soft fillings slump. That is why a hiding place can matter in a food mystery."
        )
    ],
}

KNOWLEDGE_ORDER = ["detective", "magic", "honesty", "reconciliation", "jealousy", "fear", "baking"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    motive = world.facts["motive_cfg"]
    tags = {"detective", "magic", "honesty", "reconciliation", "baking"}
    if motive.id == "jealous":
        tags.add("jealousy")
    if motive.id == "fear_judged":
        tags.add("fear")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    facts = {
        "treat": world.facts["treat_cfg"].id,
        "place": world.facts["place_cfg"].id,
        "motive": world.facts["motive_cfg"].id,
        "magic": world.facts["magic_cfg"].id,
        "repair": world.facts["repair_cfg"].id,
        "damage": world.facts.get("damage", damage_score(world.facts["treat_cfg"], world.facts["place_cfg"])),
        "outcome": world.facts.get("outcome"),
    }
    lines.append(f"  facts={facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% damage from place/treat interaction
damage(T, P, 1) :- frosting(T), warm(P), not flaky(T), not crisp(T).
damage(T, P, 1) :- flaky(T), cramped(P), not frosting(T), not crisp(T).
damage(T, P, 1) :- crisp(T), damp(P), not frosting(T), not flaky(T).
damage(T, P, 1) :- frosting(T), warm(P), not cramped(P).
damage(T, P, 1) :- flaky(T), cramped(P), not warm(P), not damp(P).
damage(T, P, 1) :- crisp(T), damp(P), not warm(P), not cramped(P).

damage(T, P, 2) :- frosting(T), warm(P), flaky(T), cramped(P).
damage(T, P, 2) :- frosting(T), warm(P), crisp(T), damp(P).
damage(T, P, 2) :- flaky(T), cramped(P), crisp(T), damp(P).

safe_place(T, P) :- treat(T), place(P), not damage(T, P, 2).

repair_fits(M, R, T, P) :- damage(T, P, 1), repair(R), R = help_remake, motive(M).
repair_fits(fear_judged, present_together, T, P) :- safe_place(T, P), not damage(T, P, 1).
repair_fits(fear_judged, help_remake, T, P) :- safe_place(T, P), not damage(T, P, 1).
repair_fits(jealous, share_credit, T, P) :- safe_place(T, P), not damage(T, P, 1).
repair_fits(jealous, help_remake, T, P) :- safe_place(T, P), not damage(T, P, 1).
repair_fits(surprise, present_together, T, P) :- safe_place(T, P), not damage(T, P, 1).
repair_fits(surprise, share_credit, T, P) :- safe_place(T, P), not damage(T, P, 1).

valid(T, P, M, R) :- treat(T), place(P), motive(M), repair(R),
                     safe_place(T, P), repair_fits(M, R, T, P).

outcome(T, P, remade) :- valid(T, P, _, _), damage(T, P, 1).
outcome(T, P, found)  :- valid(T, P, _, _), not damage(T, P, 1).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for treat_id, treat in TREATS.items():
        lines.append(asp.fact("treat", treat_id))
        if treat.frosting:
            lines.append(asp.fact("frosting", treat_id))
        if treat.flaky:
            lines.append(asp.fact("flaky", treat_id))
        if treat.crisp:
            lines.append(asp.fact("crisp", treat_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.warm:
            lines.append(asp.fact("warm", place_id))
        if place.cramped:
            lines.append(asp.fact("cramped", place_id))
        if place.damp:
            lines.append(asp.fact("damp", place_id))
    for motive_id in MOTIVES:
        lines.append(asp.fact("motive", motive_id))
    for repair_id in REPAIRS:
        lines.append(asp.fact("repair", repair_id))
    for magic_id in MAGIC:
        lines.append(asp.fact("magic", magic_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(treat_id: str, place_id: str) -> str:
    import asp
    extra = "\n".join([
        f"chosen_treat({treat_id}).",
        f"chosen_place({place_id}).",
        "picked(found) :- chosen_treat(T), chosen_place(P), outcome(T, P, found).",
        "picked(remade) :- chosen_treat(T), chosen_place(P), outcome(T, P, remade).",
    ])
    model = asp.one_model(asp_program(extra, "#show picked/1."))
    atoms = asp.atoms(model, "picked")
    return atoms[0][0] if atoms else "?"


def generate(params: StoryParams) -> StorySample:
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.motive not in MOTIVES:
        raise StoryError(f"(Unknown motive: {params.motive})")
    if params.magic not in MAGIC:
        raise StoryError(f"(Unknown magic: {params.magic})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    treat = TREATS[params.treat]
    place = PLACES[params.place]
    motive = MOTIVES[params.motive]
    repair = REPAIRS[params.repair]
    if (params.treat, params.place, params.motive, params.repair) not in set(valid_combo_ids()):
        raise StoryError(explain_rejection(treat, place, motive, repair))

    world = tell(params)
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


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat and args.place:
        treat = TREATS[args.treat]
        place = PLACES[args.place]
        if damage_score(treat, place) > 1:
            raise StoryError(explain_rejection(treat, place))
    if args.treat and args.place and args.motive and args.repair:
        treat = TREATS[args.treat]
        place = PLACES[args.place]
        motive = MOTIVES[args.motive]
        repair = REPAIRS[args.repair]
        if not repair_fits(motive, repair, damage_score(treat, place)):
            raise StoryError(explain_rejection(treat, place, motive, repair))

    combos = [
        combo for combo in valid_combo_ids()
        if (args.treat is None or combo[0] == args.treat)
        and (args.place is None or combo[1] == args.place)
        and (args.motive is None or combo[2] == args.motive)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treat_id, place_id, motive_id, repair_id = rng.choice(sorted(combos))
    magic_id = args.magic or rng.choice(sorted(MAGIC.keys()))
    detective_gender = rng.choice(["girl", "boy"])
    baker_gender = rng.choice(["girl", "boy"])
    hider_gender = rng.choice(["girl", "boy"])

    used: set[str] = set()
    detective = _pick_name(rng, detective_gender, used)
    used.add(detective)
    baker = _pick_name(rng, baker_gender, used)
    used.add(baker)
    hider = _pick_name(rng, hider_gender, used)
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        treat=treat_id,
        place=place_id,
        motive=motive_id,
        magic=magic_id,
        repair=repair_id,
        detective=detective,
        detective_gender=detective_gender,
        baker=baker,
        baker_gender=baker_gender,
        hider=hider,
        hider_gender=hider_gender,
        parent=parent,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a magical detective mystery about a hidden treat, honesty, and reconciliation."
    )
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combo_ids())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid combos match ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving params at seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params.treat, params.place) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True)
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (treat, place, motive, repair) combos:\n")
        for treat_id, place_id, motive_id, repair_id in combos:
            outcome = asp_outcome(treat_id, place_id)
            print(f"  {treat_id:14} {place_id:12} {motive_id:12} {repair_id:15} [{outcome}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = (
                f"### {p.detective} investigates {p.baker}'s {p.treat} "
                f"({p.place}, {p.motive}, {p.repair}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
