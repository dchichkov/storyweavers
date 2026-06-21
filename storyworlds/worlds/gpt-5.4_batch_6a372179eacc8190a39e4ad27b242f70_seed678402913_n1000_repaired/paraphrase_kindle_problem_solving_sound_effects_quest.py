#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/paraphrase_kindle_problem_solving_sound_effects_quest.py
====================================================================================

A standalone story world for a small mystery quest: a child and a helper must
solve a gentle, spooky puzzle to find a missing object. The world is built
around three concrete supports:

* a SOUND cue that makes the mystery feel alive ("tick-tick", "drip... drip...",
  "flutter-flutter"),
* a CLUE that must be paraphrased into plain words before the children can act,
* a TOOL that must truly fit the hiding place.

The seed words "paraphrase" and "kindle" are woven into the story itself.
"Paraphrase" appears in the clue-solving beat, and "kindle" appears in the
resolution as courage and hope are rekindled.

The model refuses weak combinations. A story is only valid when:
1) the setting can host the hiding place,
2) the chosen sound cue plausibly belongs near that place,
3) the clue really points to that place, and
4) the chosen tool can reach or open it.

Run it
------
    python storyworlds/worlds/gpt-5.4/paraphrase_kindle_problem_solving_sound_effects_quest.py
    python storyworlds/worlds/gpt-5.4/paraphrase_kindle_problem_solving_sound_effects_quest.py --place library --hiding vent --sound tick --tool magnet
    python storyworlds/worlds/gpt-5.4/paraphrase_kindle_problem_solving_sound_effects_quest.py --hiding rafters --tool magnet
    python storyworlds/worlds/gpt-5.4/paraphrase_kindle_problem_solving_sound_effects_quest.py --all --qa
    python storyworlds/worlds/gpt-5.4/paraphrase_kindle_problem_solving_sound_effects_quest.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "librarian"}
        male = {"boy", "father", "man", "uncle", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    mission: str
    keeper_role: str
    affords: set[str] = field(default_factory=set)


@dataclass
class LostItem:
    id: str
    label: str
    phrase: str
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    access: str
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundCue:
    id: str
    onomat: str
    line: str
    source: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueCard:
    id: str
    text: str
    plain: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    access_tags: set[str] = field(default_factory=set)
    method: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_understand(world: World) -> list[str]:
    clue = world.entities.get("clue")
    hero = world.entities.get("hero")
    if clue is None or hero is None:
        return []
    if clue.meters["decoded"] < THRESHOLD:
        return []
    sig = ("understand",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confidence"] += 1
    return ["__understood__"]


def _r_courage(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.meters["close_to_answer"] < THRESHOLD:
        return []
    sig = ("courage",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    hero.memes["hope"] += 1
    return ["__courage__"]


def _r_recovered(world: World) -> list[str]:
    item = world.entities.get("lost")
    if item is None:
        return []
    if item.meters["recovered"] < THRESHOLD:
        return []
    sig = ("recovered",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["relief"] += 1
    return ["__recovered__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="understand", tag="mind", apply=_r_understand),
    Rule(name="courage", tag="emotion", apply=_r_courage),
    Rule(name="recovered", tag="resolution", apply=_r_recovered),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def sound_matches_place(sound: SoundCue, place: HidingPlace) -> bool:
    return bool(set(sound.tags) & set(place.tags))


def clue_matches_place(clue: ClueCard, place: HidingPlace) -> bool:
    return bool(set(clue.tags) & set(place.tags))


def tool_fits_place(tool: Tool, place: HidingPlace) -> bool:
    return place.access in tool.access_tags


def valid_story_combo(setting: Setting, sound: SoundCue, clue: ClueCard,
                      place: HidingPlace, tool: Tool) -> bool:
    return (
        place.id in setting.affords
        and sound_matches_place(sound, place)
        and clue_matches_place(clue, place)
        and tool_fits_place(tool, place)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for sound_id, sound in SOUNDS.items():
            for clue_id, clue in CLUES.items():
                for hiding_id, hiding in HIDING_PLACES.items():
                    for tool_id, tool in TOOLS.items():
                        if valid_story_combo(setting, sound, clue, hiding, tool):
                            combos.append((place_id, sound_id, clue_id, hiding_id, tool_id))
    return combos


def predict_solution(world: World, clue: ClueCard, hiding: HidingPlace, tool: Tool) -> dict:
    sim = world.copy()
    _paraphrase_clue(sim, clue, hiding, narrate=False)
    solved = False
    if sim.get("clue").meters["decoded"] >= THRESHOLD and tool_fits_place(tool, hiding):
        sim.get("hero").meters["close_to_answer"] += 1
        propagate(sim, narrate=False)
        sim.get("lost").meters["recovered"] += 1
        propagate(sim, narrate=False)
        solved = True
    return {
        "decoded": sim.get("clue").meters["decoded"] >= THRESHOLD,
        "solved": solved,
        "hope": sim.get("hero").memes["hope"],
    }


def introduce(world: World, hero: Entity, helper: Entity, keeper: Entity, item: LostItem) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["steadiness"] += 1
    world.say(
        f"After supper, {hero.id} followed {helper.id} into {world.setting.place}, "
        f"where the shadows felt long and the air smelled like old paper and rain. "
        f"{keeper.id}, the {world.setting.keeper_role}, was worried because {item.phrase} was missing."
    )
    world.say(
        f'"Without it," {keeper.id} said, "the {world.setting.mission} cannot begin." '
        f"That was all {hero.id} needed to hear. A quest had started."
    )


def hear_sound(world: World, hero: Entity, helper: Entity, sound: SoundCue) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"Before anyone could make a plan, a strange sound slipped through the quiet: "
        f'{sound.onomat}! {sound.line}. {hero.id} stopped so fast that even {helper.id} listened harder.'
    )


def vow(world: World, hero: Entity, helper: Entity, item: LostItem) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f'"We will find {item.label}," {hero.id} whispered. {helper.id} gave a brave nod, '
        f"and together they began the little mystery quest."
    )


def find_clue(world: World, keeper: Entity, clue: ClueCard) -> None:
    world.say(
        f"On a reading table lay a folded card in {keeper.label_word}'s neat hand. "
        f'It said, "{clue.text}"'
    )


def _paraphrase_clue(world: World, clue: ClueCard, hiding: HidingPlace, narrate: bool = True) -> None:
    clue_ent = world.get("clue")
    if clue_matches_place(clue, hiding):
        clue_ent.meters["decoded"] += 1
        world.get("hero").meters["close_to_answer"] += 1
        propagate(world, narrate=False)
        if narrate:
            world.say(
                f'{world.get("helper").id} tapped the card and said, "Can you paraphrase it?" '
                f'{world.get("hero").id} thought for a moment, then said, '
                f'"It means {clue.plain}."'
            )
    else:
        if narrate:
            world.say(
                f'{world.get("helper").id} asked for a paraphrase, but the clue still felt foggy and unfinished.'
            )


def decide_path(world: World, hero: Entity, helper: Entity, sound: SoundCue,
                hiding: HidingPlace, tool: Tool) -> None:
    prediction = predict_solution(world, CLUES[world.facts["clue"].id], hiding, tool)
    world.facts["predicted_solved"] = prediction["solved"]
    if prediction["decoded"]:
        world.say(
            f"Now the rhyme no longer sounded like a riddle. It pointed them toward {hiding.phrase}, "
            f"and the {sound.source} made the path feel real."
        )
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    hero.memes["hope"] += 1
    world.say(
        f"Step by careful step, they followed the sound through {hiding.scene}. "
        f"Each little noise made the mystery tighter and clearer at the same time."
    )


def retrieve(world: World, hero: Entity, helper: Entity, item: LostItem,
             hiding: HidingPlace, tool: Tool, sound: SoundCue) -> None:
    hero.meters["close_to_answer"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last they reached {hiding.phrase}. {helper.id} passed over {tool.phrase}, "
        f"and {hero.id} {tool.method}."
    )
    world.say(
        f"{sound.onomat} went the little hidden thing one last time. Then out came {item.phrase}, "
        f"{item.shine}."
    )
    world.get("lost").meters["recovered"] += 1
    propagate(world, narrate=False)


def return_item(world: World, keeper: Entity, hero: Entity, helper: Entity, item: LostItem) -> None:
    hero.memes["pride"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{keeper.id}'s face softened with relief when {hero.id} placed {item.label} back into {keeper.pronoun('possessive')} hands. "
        f'"You solved it," {keeper.pronoun()} said.'
    )
    world.say(
        f"A warm glow seemed to kindle in the dim room. The mystery was over, but the courage it woke in "
        f"{hero.id} and {helper.id} stayed bright."
    )


def ending_image(world: World, hero: Entity, helper: Entity, item: LostItem) -> None:
    world.say(
        f"When they stepped outside again, the night no longer felt spooky. "
        f"It felt like the kind of dark that keeps secrets only until kind, patient children come looking."
    )
    world.say(
        f"{hero.id} walked home smiling, still hearing the tiny echoes of the quest and thinking about how a good paraphrase had helped bring {item.label} home."
    )


def tell(setting: Setting, item_cfg: LostItem, sound: SoundCue, clue: ClueCard,
         hiding: HidingPlace, tool: Tool, hero_name: str = "Mina",
         hero_type: str = "girl", helper_name: str = "Owen", helper_type: str = "boy",
         keeper_type: str = "librarian") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    keeper = world.add(Entity(id="Keeper", kind="character", type=keeper_type, role="keeper", label=setting.keeper_role))
    item = world.add(Entity(id="lost", type="item", label=item_cfg.label, phrase=item_cfg.phrase, tags=set(item_cfg.tags)))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.id, phrase=clue.text, tags=set(clue.tags)))
    world.add(Entity(id="tool", type="tool", label=tool.label, phrase=tool.phrase, tags=set(tool.tags)))
    world.add(Entity(id="place", type="place", label=hiding.label, phrase=hiding.phrase, tags=set(hiding.tags)))
    world.add(Entity(id="sound", type="sound", label=sound.id, phrase=sound.line, tags=set(sound.tags)))

    introduce(world, hero, helper, keeper, item_cfg)
    hear_sound(world, hero, helper, sound)
    vow(world, hero, helper, item_cfg)

    world.para()
    find_clue(world, keeper, clue)
    _paraphrase_clue(world, clue, hiding)
    decide_path(world, hero, helper, sound, hiding, tool)

    world.para()
    retrieve(world, hero, helper, item_cfg, hiding, tool, sound)
    return_item(world, keeper, hero, helper, item_cfg)
    ending_image(world, hero, helper, item_cfg)

    world.facts.update(
        setting=setting,
        item_cfg=item_cfg,
        sound=sound,
        clue=clue,
        hiding=hiding,
        tool=tool,
        hero=hero,
        helper=helper,
        keeper=keeper,
        solved=item.meters["recovered"] >= THRESHOLD,
        paraphrased=clue_ent.meters["decoded"] >= THRESHOLD,
        mission=setting.mission,
    )
    return world


SETTINGS = {
    "library": Setting(
        id="library",
        place="the old library",
        mood="hushed and shadowy",
        mission="lantern parade",
        keeper_role="librarian",
        affords={"vent", "atlas_shelf"},
    ),
    "museum": Setting(
        id="museum",
        place="the little town museum",
        mood="echoing and moonlit",
        mission="night exhibit",
        keeper_role="caretaker",
        affords={"display_case", "rafters"},
    ),
    "bookshop": Setting(
        id="bookshop",
        place="the crooked bookshop",
        mood="cozy and puzzling",
        mission="midnight story hour",
        keeper_role="shopkeeper",
        affords={"umbrella_stand", "atlas_shelf"},
    ),
}

ITEMS = {
    "key": LostItem(
        id="key",
        label="the brass key",
        phrase="the brass key with a moon stamped on it",
        shine="cool and gold in the flashlight beam",
        tags={"key", "metal"},
    ),
    "badge": LostItem(
        id="badge",
        label="the star badge",
        phrase="the star badge for the night's guide",
        shine="sparkling with a tiny silver edge",
        tags={"badge", "metal"},
    ),
    "compass": LostItem(
        id="compass",
        label="the pocket compass",
        phrase="the pocket compass with a glass face",
        shine="glimmering as its needle trembled",
        tags={"compass", "metal"},
    ),
}

HIDING_PLACES = {
    "vent": HidingPlace(
        id="vent",
        label="floor vent",
        phrase="the brass floor vent by the map table",
        access="narrow",
        scene="the longest row of dusty shelves",
        tags={"metal", "tick", "narrow"},
    ),
    "atlas_shelf": HidingPlace(
        id="atlas_shelf",
        label="atlas shelf",
        phrase="the highest atlas shelf",
        access="high",
        scene="a corner stacked with giant maps and sleepy globes",
        tags={"paper", "flutter", "high"},
    ),
    "umbrella_stand": HidingPlace(
        id="umbrella_stand",
        label="umbrella stand",
        phrase="the deep umbrella stand by the door",
        access="deep",
        scene="the creaky front hall where raindrops still gleamed on the mat",
        tags={"drip", "deep", "door"},
    ),
    "display_case": HidingPlace(
        id="display_case",
        label="display case",
        phrase="the old display case with the loose latch",
        access="open",
        scene="the moonlit hall of little treasures",
        tags={"glass", "tick", "open"},
    ),
    "rafters": HidingPlace(
        id="rafters",
        label="rafters",
        phrase="the dark rafters above the dinosaur room",
        access="high",
        scene="the tall museum gallery where every footstep echoed",
        tags={"flutter", "high", "wood"},
    ),
}

SOUNDS = {
    "tick": SoundCue(
        id="tick",
        onomat="tick-tick",
        line="Something tiny tapped against metal, then went quiet",
        source="tapping sound",
        tags={"tick", "metal", "glass"},
    ),
    "flutter": SoundCue(
        id="flutter",
        onomat="flutter-flutter",
        line="A soft rustle shivered overhead like nervous pages or wings",
        source="fluttering sound",
        tags={"flutter", "paper", "high", "wood"},
    ),
    "drip": SoundCue(
        id="drip",
        onomat="drip... drip...",
        line="Rainwater plinked somewhere near the door and made the silence count the seconds",
        source="dripping sound",
        tags={"drip", "door", "deep"},
    ),
}

CLUES = {
    "metal_rhyme": ClueCard(
        id="metal_rhyme",
        text="Find what ticks where cold lines meet and careful fingers cannot squeeze.",
        plain="the missing thing is near metal slats, in a place too narrow for a hand",
        tags={"metal", "narrow", "tick"},
    ),
    "high_rhyme": ClueCard(
        id="high_rhyme",
        text="Look where restless whispers stir above the tallest books.",
        plain="the clue points up high, where a fluttering sound is above the shelves",
        tags={"high", "flutter", "paper"},
    ),
    "door_rhyme": ClueCard(
        id="door_rhyme",
        text="Near the last wet footprints, the answer waits below a cluster of handles.",
        plain="the hidden thing is by the door, down deep where umbrellas are kept",
        tags={"door", "deep", "drip"},
    ),
    "glass_rhyme": ClueCard(
        id="glass_rhyme",
        text="Where moonlight taps the quiet panes, a patient hand should try the latch.",
        plain="it is in the case with glass, and the latch must be opened gently",
        tags={"glass", "open", "tick"},
    ),
}

TOOLS = {
    "magnet": Tool(
        id="magnet",
        label="magnet wand",
        phrase="the little magnet wand",
        access_tags={"narrow"},
        method="slid it through the slats and drew the lost thing close",
        tags={"magnet", "metal"},
    ),
    "stool": Tool(
        id="stool",
        label="rolling stool",
        phrase="the rolling stool",
        access_tags={"high"},
        method="climbed carefully and reached into the shadows",
        tags={"stool", "reach"},
    ),
    "hook": Tool(
        id="hook",
        label="curved umbrella hook",
        phrase="the curved umbrella hook",
        access_tags={"deep"},
        method="lowered it gently and lifted the hidden thing out",
        tags={"hook", "reach"},
    ),
    "latch_key": Tool(
        id="latch_key",
        label="latch key",
        phrase="the tiny latch key on a ribbon",
        access_tags={"open"},
        method="turned it slowly until the old latch clicked",
        tags={"key", "open"},
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Tessa", "Lena", "Ruby", "Ada", "Cora"]
BOY_NAMES = ["Owen", "Jules", "Milo", "Theo", "Ben", "Eli", "Arlo", "Finn"]


@dataclass
class StoryParams:
    place: str
    item: str
    sound: str
    clue: str
    hiding: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    keeper_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "tick": [(
        "Why can a tiny ticking sound help in a mystery?",
        "A repeated sound can tell you where something is hiding because it leads your ears toward one spot. In a mystery, small clues matter when your eyes cannot see everything at once."
    )],
    "flutter": [(
        "What can a fluttering sound tell you?",
        "A fluttering sound often means something light is moving, like paper, cloth, or wings. It can also tell you to look up, because the noise may be above your head."
    )],
    "drip": [(
        "Why is a dripping sound easy to follow?",
        "A drip repeats again and again, so it helps you notice where the noise is coming from. That makes it useful as a clue."
    )],
    "paraphrase": [(
        "What does paraphrase mean?",
        "To paraphrase means to say the same idea in simpler or different words. It helps you show that you really understand what a clue means."
    )],
    "quest": [(
        "What is a quest?",
        "A quest is a journey with a goal, like finding something important or solving a problem. A quest usually takes courage and careful thinking."
    )],
    "magnet": [(
        "What does a magnet do?",
        "A magnet can pull some metal things toward it without your hand touching them. That makes it helpful for getting small metal objects out of tight places."
    )],
    "stool": [(
        "Why is a stool useful for reaching high places?",
        "A stool lifts you a little higher, so you can safely reach something above you. Grown-ups should still help with climbing."
    )],
    "hook": [(
        "What is a hook good for in a problem?",
        "A hook can catch or lift something from deep inside a container. It helps when your hand cannot reach the bottom."
    )],
    "open": [(
        "What does a latch do?",
        "A latch keeps a door or case shut until someone opens it. If it is loose or unlocked, it can be opened carefully."
    )],
    "mystery": [(
        "What makes a mystery feel exciting instead of scary?",
        "A mystery feels exciting when the clues make sense little by little and someone keeps helping you. Then the unknown starts to feel like a puzzle instead of a danger."
    )],
}
KNOWLEDGE_ORDER = ["paraphrase", "quest", "tick", "flutter", "drip", "magnet", "stool", "hook", "open", "mystery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    sound = f["sound"]
    setting = f["setting"]
    hiding = f["hiding"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the words "paraphrase" and "kindle".',
        f"Tell a quest story where {hero.id} follows a {sound.source} through {setting.place} to find {item.label}, and solving the clue depends on paraphrasing it.",
        f"Write a child-facing mystery in which a strange sound leads to {hiding.phrase}, and the ending should kindle courage instead of fear.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    keeper = f["keeper"]
    item = f["item_cfg"]
    sound = f["sound"]
    clue = f["clue"]
    hiding = f["hiding"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {helper.id}, who went on a small mystery quest in {f['setting'].place}. They were trying to find {item.label} for {keeper.label_word}."
        ),
        (
            f"What started the quest?",
            f"The quest began because {item.label} was missing, and it was needed for the {f['mission']}. That problem gave the children a clear reason to search instead of just wandering."
        ),
        (
            "What strange clue did they notice first?",
            f"They first noticed {sound.onomat}, the {sound.source} in the quiet room. The sound made the mystery feel real and helped guide them toward the right place."
        ),
        (
            "How did paraphrasing help them?",
            f"{helper.id} asked {hero.id} to paraphrase the card, and {hero.id} put the riddle into plain words: {clue.plain}. That turned a spooky-sounding clue into a usable plan."
        ),
        (
            f"Where was {item.label} hidden?",
            f"It was hidden at {hiding.phrase}. The clue and the sound both pointed to that same place, which is why the children searched there."
        ),
        (
            f"How did they get {item.label} out?",
            f"They used {tool.phrase}, and {hero.id} {tool.method}. The tool worked because it truly fit that hiding place."
        ),
        (
            "How did the story end?",
            f"They returned {item.label} and solved the mystery. By the end, the room felt warm instead of spooky, and the adventure seemed to kindle courage in both children."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"paraphrase", "quest", "mystery"}
    sound = f["sound"]
    tool = f["tool"]
    tags |= set(sound.tags)
    tags |= set(tool.tags)
    if f["hiding"].access == "open":
        tags.add("open")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="library",
        item="key",
        sound="tick",
        clue="metal_rhyme",
        hiding="vent",
        tool="magnet",
        hero_name="Mina",
        hero_type="girl",
        helper_name="Owen",
        helper_type="boy",
        keeper_type="librarian",
    ),
    StoryParams(
        place="bookshop",
        item="badge",
        sound="flutter",
        clue="high_rhyme",
        hiding="atlas_shelf",
        tool="stool",
        hero_name="Ruby",
        hero_type="girl",
        helper_name="Finn",
        helper_type="boy",
        keeper_type="librarian",
    ),
    StoryParams(
        place="bookshop",
        item="compass",
        sound="drip",
        clue="door_rhyme",
        hiding="umbrella_stand",
        tool="hook",
        hero_name="Ada",
        hero_type="girl",
        helper_name="Milo",
        helper_type="boy",
        keeper_type="caretaker",
    ),
    StoryParams(
        place="museum",
        item="badge",
        sound="tick",
        clue="glass_rhyme",
        hiding="display_case",
        tool="latch_key",
        hero_name="Theo",
        hero_type="boy",
        helper_name="Ivy",
        helper_type="girl",
        keeper_type="caretaker",
    ),
    StoryParams(
        place="museum",
        item="compass",
        sound="flutter",
        clue="high_rhyme",
        hiding="rafters",
        tool="stool",
        hero_name="Nora",
        hero_type="girl",
        helper_name="Arlo",
        helper_type="boy",
        keeper_type="caretaker",
    ),
]


def explain_rejection(setting: Setting, sound: SoundCue, clue: ClueCard,
                      hiding: HidingPlace, tool: Tool) -> str:
    if hiding.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not contain {hiding.phrase}, so the quest has nowhere sensible to go.)"
        )
    if not sound_matches_place(sound, hiding):
        return (
            f"(No story: the sound '{sound.id}' does not fit {hiding.phrase}. The noise clue must plausibly belong near the hiding place.)"
        )
    if not clue_matches_place(clue, hiding):
        return (
            f"(No story: the clue '{clue.id}' does not actually point to {hiding.phrase}. A paraphrase should lead to the right place, not a random one.)"
        )
    if not tool_fits_place(tool, hiding):
        return (
            f"(No story: {tool.label} does not fit {hiding.phrase}. The solution tool must truly reach or open the hiding place.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
sound_matches(S, H) :- sound(S), hiding(H), sound_tag(S, T), hiding_tag(H, T).
clue_matches(C, H)  :- clue(C), hiding(H), clue_tag(C, T), hiding_tag(H, T).
tool_fits(Tool, H)  :- tool(Tool), hiding(H), access(H, A), fits(Tool, A).

valid(P, S, C, H, T) :- setting(P), sound(S), clue(C), hiding(H), tool(T),
                        affords(P, H), sound_matches(S, H), clue_matches(C, H), tool_fits(T, H).

solved :- chosen_place(P), chosen_sound(S), chosen_clue(C), chosen_hiding(H), chosen_tool(T),
          valid(P, S, C, H, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hiding in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, hiding))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        lines.append(asp.fact("access", hid, hiding.access))
        for tag in sorted(hiding.tags):
            lines.append(asp.fact("hiding_tag", hid, tag))
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        for tag in sorted(sound.tags):
            lines.append(asp.fact("sound_tag", sid, tag))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for tag in sorted(clue.tags):
            lines.append(asp.fact("clue_tag", cid, tag))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for access in sorted(tool.access_tags):
            lines.append(asp.fact("fits", tid, access))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_sound", params.sound),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_hiding", params.hiding),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show solved/0."))
    return bool(asp.atoms(model, "solved"))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases: list[StoryParams] = list(CURATED)
    for seed in range(12):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed in smoke test for seed {seed}.")
            continue

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if not asp_solved(params):
                raise StoryError("ASP says scenario is not solved")
        except Exception as err:
            rc = 1
            print(f"ERROR: smoke generation failed for {params}: {err}")

    if rc == 0:
        print(f"OK: generated and verified {len(smoke_cases)} smoke-test stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle mystery quest storyworld with clue paraphrasing, sound effects, and a tool that must truly fit."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--keeper-type", choices=["librarian", "caretaker"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.sound and args.clue and args.hiding and args.tool:
        if not valid_story_combo(
            SETTINGS[args.place],
            SOUNDS[args.sound],
            CLUES[args.clue],
            HIDING_PLACES[args.hiding],
            TOOLS[args.tool],
        ):
            raise StoryError(explain_rejection(
                SETTINGS[args.place],
                SOUNDS[args.sound],
                CLUES[args.clue],
                HIDING_PLACES[args.hiding],
                TOOLS[args.tool],
            ))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sound is None or combo[1] == args.sound)
        and (args.clue is None or combo[2] == args.clue)
        and (args.hiding is None or combo[3] == args.hiding)
        and (args.tool is None or combo[4] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, sound_id, clue_id, hiding_id, tool_id = rng.choice(sorted(combos))
    item_id = args.item or rng.choice(sorted(ITEMS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    helper_name = args.helper_name or _pick_name(rng, helper_type, avoid=hero_name)
    keeper_type = args.keeper_type or SETTINGS[place_id].keeper_role
    return StoryParams(
        place=place_id,
        item=item_id,
        sound=sound_id,
        clue=clue_id,
        hiding=hiding_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        keeper_type=keeper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Invalid item: {params.item})")
    if params.sound not in SOUNDS:
        raise StoryError(f"(Invalid sound: {params.sound})")
    if params.clue not in CLUES:
        raise StoryError(f"(Invalid clue: {params.clue})")
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Invalid hiding place: {params.hiding})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")

    setting = SETTINGS[params.place]
    sound = SOUNDS[params.sound]
    clue = CLUES[params.clue]
    hiding = HIDING_PLACES[params.hiding]
    tool = TOOLS[params.tool]
    if not valid_story_combo(setting, sound, clue, hiding, tool):
        raise StoryError(explain_rejection(setting, sound, clue, hiding, tool))

    world = tell(
        setting=setting,
        item_cfg=ITEMS[params.item],
        sound=sound,
        clue=clue,
        hiding=hiding,
        tool=tool,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        keeper_type=params.keeper_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sound, clue, hiding, tool) combos:\n")
        for place_id, sound_id, clue_id, hiding_id, tool_id in combos:
            print(f"  {place_id:8} {sound_id:8} {clue_id:12} {hiding_id:14} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.hero_name} & {p.helper_name}: {p.hiding} in {p.place} ({p.sound}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
