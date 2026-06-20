#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tot_reconciliation_comedy.py
=======================================================

A standalone storyworld for a tiny comedy about a **tot**, a silly quarrel, and
a reconciliation that actually fits the problem.

Reference seed idea
-------------------
A small child and another child are getting ready for a funny pretend show.
They both want the same special prop. The quarrel grows noisy and ridiculous,
something mildly messy happens, and a calm grown-up helps them make up. The fix
must match the kind of problem: some props can be shared by taking turns, some
need a matching second copy, and some only become fair when the children change
the act so both get a starring role. The ending image proves they are friends
again.

World-model constraint
----------------------
The storyworld refuses weak reconciliations. A repair only counts when it
addresses the real snag in the simulated world:

* single-use prop + good waiting skills -> taking turns can work
* prop has materials for a second version -> making a copy can work
* theme supports duet roles -> changing to a two-part act can work

A forced or mismatched fix is rejected with a StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/tot_reconciliation_comedy.py
    python storyworlds/worlds/gpt-5.4/tot_reconciliation_comedy.py --theme parade --prop horn
    python storyworlds/worlds/gpt-5.4/tot_reconciliation_comedy.py --repair copy
    python storyworlds/worlds/gpt-5.4/tot_reconciliation_comedy.py --all
    python storyworlds/worlds/gpt-5.4/tot_reconciliation_comedy.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/tot_reconciliation_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/tot_reconciliation_comedy.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so add storyworlds/ itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Theme:
    id: str
    place: str
    setup: str
    show_name: str
    opening: str
    ending: str
    duet_line: str
    supports_duet: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str                 # "sound" | "wearable" | "vehicle"
    goofy: str
    mishap: str
    possessive_use: str
    copyable: bool
    needs_single_user: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    needs_waiting: bool
    needs_copyable: bool
    needs_duet: bool
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


THEMES = {
    "parade": Theme(
        "parade",
        "the living room",
        "Couch cushions became parade floats, a blanket turned into a finish-line banner, and a spoon tapped on a pot like a tiny drum.",
        "the Funny Feet Parade",
        "They marched in circles until even the lamp looked dizzy.",
        "They looped around the rug like a real parade route, both grinning again.",
        "If the parade had two stars instead of one, there was room for everyone to shine.",
        supports_duet=True,
        tags={"parade", "pretend"},
    ),
    "circus": Theme(
        "circus",
        "the den",
        "A laundry basket became a lion cage, a striped towel became a circus curtain, and the footstool was announced as the Big Top Stage.",
        "the Giggle Circus",
        "Every grand entrance was much wobblier than the last.",
        "They bowed so hard that they nearly toppled into the blanket pile.",
        "A circus could always use two stars, especially if one honked and one bowed.",
        supports_duet=True,
        tags={"circus", "pretend"},
    ),
    "restaurant": Theme(
        "restaurant",
        "the kitchen",
        "A row of cups became a fancy counter, a dish towel became an apron, and a cereal box was promoted to the menu board.",
        "the Noodle Nook Show",
        "They whispered in serious chef voices while making very silly faces.",
        "They served invisible soup to the chairs and thanked each other with a bow.",
        "A restaurant show worked better when one child welcomed guests and the other delivered the big finish.",
        supports_duet=True,
        tags={"restaurant", "pretend"},
    ),
}

PROPS = {
    "horn": Prop(
        "horn",
        "rubber horn",
        "a squeaky rubber horn",
        "sound",
        "Every squeeze made a rude little bweep that was impossible to ignore.",
        "it let out such a sudden bweep that both children jumped and one almost sat on the blanket banner",
        "to lead the loudest part of the show",
        copyable=True,
        needs_single_user=True,
        tags={"horn", "sound"},
    ),
    "hat": Prop(
        "hat",
        "tall hat",
        "a tall wobbly hat with a paper star",
        "wearable",
        "It leaned to one side like it had its own opinion.",
        "it tipped over one child's eyes, and the other laughed for one shocked second before getting cross again",
        "to look like the grand star",
        copyable=True,
        needs_single_user=True,
        tags={"hat", "wearable"},
    ),
    "wagon": Prop(
        "wagon",
        "red wagon",
        "a red wagon with squeaky wheels",
        "vehicle",
        "Each turn of the wheels made a tiny eeek-eeek song.",
        "the wagon rolled just enough to bump the ottoman, and everyone froze at the comic little bonk",
        "to ride at the front like the grand marshal",
        copyable=False,
        needs_single_user=True,
        tags={"wagon", "vehicle"},
    ),
}

REPAIRS = {
    "turns": Repair(
        "turns",
        "take turns",
        needs_waiting=True,
        needs_copyable=False,
        needs_duet=False,
        text="set a fair count of 'one parade lap each' so both children would get the special part without snatching",
        qa_text="helped them take turns with a fair count",
        tags={"turns", "sharing"},
    ),
    "copy": Repair(
        "copy",
        "make a second one",
        needs_waiting=False,
        needs_copyable=True,
        needs_duet=False,
        text="found scrap paper and tape and quickly made a second version, so neither child had to lose the joke",
        qa_text="made a second matching prop from simple materials",
        tags={"copy", "sharing"},
    ),
    "duet": Repair(
        "duet",
        "change the act",
        needs_waiting=False,
        needs_copyable=False,
        needs_duet=True,
        text="changed the show into a two-star act, giving each child a different important part so the argument no longer had one winner and one loser",
        qa_text="changed the show into a two-part act with room for both children",
        tags={"duet", "reconciliation"},
    ),
}

TOT_NAMES = ["Toby", "Mimi", "Pip", "Lulu", "Beni", "Tess"]
KID_NAMES = ["Nora", "Max", "Ivy", "Leo", "June", "Finn", "Ava", "Sam"]
TOT_TRAITS = ["bouncy", "earnest", "small", "busy", "cheerful"]
KID_TRAITS = ["patient", "dramatic", "helpful", "proud", "funny", "careful"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"tot", "pal"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_argument(world: World) -> list[str]:
    prop = world.get("prop")
    kids = world.kids()
    if len(kids) != 2:
        return []
    if not all(k.memes["want_prop"] >= THRESHOLD for k in kids):
        return []
    sig = ("argument", prop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in kids:
        kid.memes["cross"] += 1
    world.get("room").memes["tension"] += 1
    return ["__argument__"]


def _r_snatch(world: World) -> list[str]:
    prop = world.get("prop")
    holder = prop.owner
    if not holder:
        return []
    other = [k for k in world.kids() if k.id != holder]
    if not other:
        return []
    other = other[0]
    if other.memes["cross"] < THRESHOLD:
        return []
    sig = ("snatch", holder, other.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prop.meters["tugged"] += 1
    for kid in world.kids():
        kid.memes["embarrassed"] += 1
    return ["__snatch__"]


def _r_mishap(world: World) -> list[str]:
    prop = world.get("prop")
    if prop.meters["tugged"] < THRESHOLD:
        return []
    sig = ("mishap", prop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prop.meters["wobble"] += 1
    world.get("room").meters["mess"] += 1
    return ["__mishap__"]


CAUSAL_RULES = [
    Rule("argument", "social", _r_argument),
    Rule("snatch", "social", _r_snatch),
    Rule("mishap", "physical", _r_mishap),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s == "__argument__":
                tot = world.facts["tot"]
                pal = world.facts["pal"]
                prop = world.facts["prop_cfg"]
                world.say(
                    f"In one blink, both reached for {prop.phrase} at once. "
                    f'"Mine!" said {tot.id}. "I was using it!" said {pal.id}.'
                )
            elif s == "__snatch__":
                prop = world.facts["prop_cfg"]
                world.say(
                    f"Hands tugged, faces puffed up, and the room went prickly with cross feelings."
                )
            elif s == "__mishap__":
                prop = world.facts["prop_cfg"]
                world.say(
                    f"Then {prop.mishap}. For a beat, the quarrel looked so silly that even the grown-up had to hide a smile."
                )
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def can_turns(waiting_skill: int) -> bool:
    return waiting_skill >= 1


def repair_fits(theme: Theme, prop: Prop, repair: Repair, waiting_skill: int) -> bool:
    if repair.needs_waiting and not can_turns(waiting_skill):
        return False
    if repair.needs_copyable and not prop.copyable:
        return False
    if repair.needs_duet and not theme.supports_duet:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id, theme in THEMES.items():
        for prop_id, prop in PROPS.items():
            for repair_id, repair in REPAIRS.items():
                if repair.id == "turns":
                    for waiting_skill in (0, 1, 2):
                        if repair_fits(theme, prop, repair, waiting_skill):
                            combos.append((theme_id, prop_id, repair_id))
                            break
                elif repair_fits(theme, prop, repair, 0):
                    combos.append((theme_id, prop_id, repair_id))
    return sorted(set(combos))


def explain_repair(theme: Theme, prop: Prop, repair: Repair, waiting_skill: int) -> str:
    if repair.id == "turns" and not can_turns(waiting_skill):
        return ("(No story: taking turns is not a real reconciliation here, because the children "
                "are too stirred up to wait even a little. Pick a copy or duet fix, or allow better waiting.)")
    if repair.id == "copy" and not prop.copyable:
        return (f"(No story: {prop.phrase} cannot reasonably get a matching second version in this little world, "
                "so 'make a copy' would feel fake. Try turns or a duet.)")
    if repair.id == "duet" and not theme.supports_duet:
        return ("(No story: this show frame does not support two clear starring roles, so changing it to a duet "
                "would not solve the quarrel honestly.)")
    return "(No story: that repair does not fit this quarrel.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_repair(theme: Theme, prop: Prop, repair: Repair, waiting_skill: int) -> dict:
    return {
        "works": repair_fits(theme, prop, repair, waiting_skill),
        "copyable": prop.copyable,
        "supports_duet": theme.supports_duet,
        "waiting_skill": waiting_skill,
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def setup_show(world: World, tot: Entity, pal: Entity, theme: Theme, prop: Prop) -> None:
    for kid in (tot, pal):
        kid.memes["joy"] += 1
    world.say(
        f"One afternoon, {tot.id}, a little tot with a {tot.attrs['trait']} bounce, and {pal.id} turned {theme.place} into {theme.show_name}. {theme.setup}"
    )
    world.say(theme.opening)
    world.say(
        f"The best prop of all was {prop.phrase}. {prop.goofy}"
    )


def claim_prop(world: World, tot: Entity, pal: Entity, prop: Prop) -> None:
    tot.memes["want_prop"] += 1
    pal.memes["want_prop"] += 1
    world.get("prop").owner = pal.id
    world.say(
        f"{pal.id} picked up the {prop.label} {prop.possessive_use}. Then {tot.id} lifted both hands and decided, very suddenly, that the same idea was perfect."
    )
    propagate(world, narrate=True)


def escalate(world: World, tot: Entity, pal: Entity) -> None:
    propagate(world, narrate=True)
    if world.get("room").memes["tension"] >= THRESHOLD:
        world.say(
            f"{tot.id}'s lower lip stuck out. {pal.id} hugged the prop close. Neither one looked happy anymore."
        )


def adult_steps_in(world: World, grown: Entity, theme: Theme, prop: Prop, repair: Repair, waiting_skill: int) -> None:
    pred = predict_repair(theme, prop, repair, waiting_skill)
    world.facts["prediction"] = pred
    world.say(
        f"{grown.label_word.capitalize()} came in at the comic little noise, looked at the two cross faces, and understood that the real trouble was not the show at all. It was one special prop and two children who both wanted to feel important."
    )


def reconcile(world: World, grown: Entity, tot: Entity, pal: Entity,
              theme: Theme, prop: Prop, repair: Repair, waiting_skill: int) -> None:
    if not repair_fits(theme, prop, repair, waiting_skill):
        raise StoryError(explain_repair(theme, prop, repair, waiting_skill))

    if repair.id == "turns":
        world.say(
            f'"I hear two good ideas bumping into each other," {grown.label_word} said. {grown.pronoun().capitalize()} {repair.text}.'
        )
        world.say(
            f'{pal.id} got the first lap, and {tot.id} counted with a very serious finger. Then the horn passed over, and the waiting felt short enough to bear.'
            if prop.id == "horn" else
            f'{pal.id} got the first turn, and {tot.id} counted with a very serious finger. Then the prop passed over, and the waiting felt short enough to bear.'
        )
    elif repair.id == "copy":
        noun = "horn" if prop.id == "horn" else ("hat" if prop.id == "hat" else "prop")
        world.say(
            f'"What if the joke gets bigger instead of meaner?" {grown.label_word} asked. {grown.pronoun().capitalize()} {repair.text}.'
        )
        world.say(
            f"Soon there were two funny {noun}s instead of one. The children stared, surprised that the problem had shrunk so fast."
        )
    elif repair.id == "duet":
        world.say(
            f'"No one has to be the only star," {grown.label_word} said. {theme.duet_line} {grown.pronoun().capitalize()} {repair.text}.'
        )
        if prop.id == "wagon":
            world.say(
                f"{pal.id} became the grand puller of the wagon, and {tot.id} became the grand waver standing beside it. Suddenly the whole game had room."
            )
        elif prop.id == "horn":
            world.say(
                f"{pal.id} led the march, and {tot.id} gave the comic honks at the finish of each lap. Suddenly the whole act felt better than before."
            )
        else:
            world.say(
                f"{pal.id} wore the tall hat for the bow, and {tot.id} got to announce the act with a booming little voice. Suddenly the whole act felt better than before."
            )

    for kid in (tot, pal):
        kid.memes["cross"] = 0.0
        kid.memes["embarrassed"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.get("room").memes["tension"] = 0.0
    world.facts["reconciled"] = True


def ending(world: World, tot: Entity, pal: Entity, theme: Theme, prop: Prop, repair: Repair) -> None:
    world.para()
    laugh_bit = {
        "horn": "The loudest bweep came at exactly the wrong moment, which made it the funniest moment of all.",
        "hat": "The tall hat slid sideways again, and this time both children laughed instead of arguing.",
        "wagon": "The wagon answered with one last eeek-eeek, as if it wanted to join the joke.",
    }[prop.id]
    world.say(
        f"After that, the show went on. {laugh_bit}"
    )
    world.say(
        f"{theme.ending} By the end, {tot.id} and {pal.id} were leaning into each other again, proud of the same silly show instead of cross about the same old prop."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(theme: Theme, prop: Prop, repair: Repair,
         tot_name: str = "Pip", tot_gender: str = "boy",
         pal_name: str = "Nora", pal_gender: str = "girl",
         parent_type: str = "mother", waiting_skill: int = 1,
         tot_trait: str = "bouncy", pal_trait: str = "patient") -> World:
    world = World()
    tot = world.add(Entity(
        id=tot_name, kind="character", type=tot_gender, role="tot",
        traits=[tot_trait], attrs={"trait": tot_trait}
    ))
    pal = world.add(Entity(
        id=pal_name, kind="character", type=pal_gender, role="pal",
        traits=[pal_trait], attrs={"trait": pal_trait}
    ))
    grown = world.add(Entity(
        id="Parent", kind="character", type=parent_type, role="grown",
        label="the parent"
    ))
    prop_ent = world.add(Entity(
        id="prop", type=prop.kind, label=prop.label, role="prop"
    ))
    world.add(Entity(id="room", type="room", label=theme.place))

    world.facts.update(
        tot=tot,
        pal=pal,
        grown=grown,
        theme=theme,
        prop_cfg=prop,
        repair=repair,
        waiting_skill=waiting_skill,
    )

    setup_show(world, tot, pal, theme, prop)
    world.para()
    claim_prop(world, tot, pal, prop)
    escalate(world, tot, pal)
    world.say(
        f'"This is a silly fight," said {grown.label_word} from the doorway, though {grown.pronoun()} said it kindly.'
    )
    world.para()
    adult_steps_in(world, grown, theme, prop, repair, waiting_skill)
    reconcile(world, grown, tot, pal, theme, prop, repair, waiting_skill)
    ending(world, tot, pal, theme, prop, repair)

    world.facts["outcome"] = "reconciled" if world.facts.get("reconciled") else "stuck"
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    theme: str
    prop: str
    repair: str
    tot_name: str
    tot_gender: str
    pal_name: str
    pal_gender: str
    parent: str
    waiting_skill: int
    tot_trait: str
    pal_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "horn": [(
        "What is a rubber horn?",
        "A rubber horn is a squeeze toy that makes a loud funny sound. It is often used for jokes or pretend shows."
    )],
    "hat": [(
        "Why can a costume hat be funny?",
        "A costume hat can look funny because it wobbles or sits too tall. When something looks a little ridiculous, people often laugh."
    )],
    "wagon": [(
        "What is a wagon?",
        "A wagon is a small cart with wheels that can carry toys or children. Some wagons squeak and rattle when they roll."
    )],
    "turns": [(
        "What does taking turns mean?",
        "Taking turns means one person goes first and another person goes next. It helps people share one thing fairly."
    )],
    "copy": [(
        "Why does making a second copy sometimes solve an argument?",
        "If two children both need the same kind of thing, a second copy can remove the fight. Then nobody has to lose the whole joke or game."
    )],
    "duet": [(
        "How can changing the game help children make up?",
        "Sometimes the best fix is to change the game so both children have a good part. That way the argument itself stops making sense."
    )],
    "reconciliation": [(
        "What does reconciliation mean?",
        "Reconciliation means people who were upset make peace again. They stop fighting and begin treating each other kindly."
    )],
}
KNOWLEDGE_ORDER = ["horn", "hat", "wagon", "turns", "copy", "duet", "reconciliation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tot = f["tot"]
    pal = f["pal"]
    theme = f["theme"]
    prop = f["prop_cfg"]
    repair = f["repair"]
    return [
        'Write a short comedy for a 3-to-5-year-old that includes the word "tot" and ends in reconciliation.',
        f"Tell a funny pretend-play story where a little tot named {tot.id} and {pal.id} quarrel over {prop.phrase} during {theme.show_name}, and a grown-up helps them make up.",
        f"Write a gentle reconciliation story in a comic style where the solution is to {repair.label} instead of forcing one child to give up.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tot, pal, grown = f["tot"], f["pal"], f["grown"]
    theme, prop, repair = f["theme"], f["prop_cfg"], f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little tot named {tot.id}, {pal.id}, and their {grown.label_word}. The children were trying to put on {theme.show_name}."
        ),
        (
            f"Why did {tot.id} and {pal.id} start fighting?",
            f"They both wanted {prop.phrase} for the same show at the same time. The quarrel was really about both children wanting to feel like the important star."
        ),
        (
            "What funny thing happened in the middle of the story?",
            f"When they tugged over the prop, {prop.mishap}. The comic mishap showed that the fight had become silly as well as upsetting."
        ),
        (
            f"How did the {grown.label_word} help them reconcile?",
            f"The {grown.label_word} noticed that one special prop was causing the problem and {repair.qa_text}. That fix matched the real reason for the quarrel, so the children could stop being cross and enjoy the game again."
        ),
        (
            "How did the story end?",
            f"It ended with the pretend show going on and both children laughing again. The final image proves the reconciliation because they were proud of the same silly show instead of fighting over the prop."
        ),
    ]
    if repair.id == "turns":
        qa.append((
            "Why did taking turns work in this story?",
            f"It worked because the waiting was short and clear enough for the children to manage. A fair count made each child trust that a turn was really coming."
        ))
    elif repair.id == "copy":
        qa.append((
            "Why did making a second prop work in this story?",
            f"It worked because the prop could reasonably have a matching second version. Once there were two, the children no longer had to fight over one small joke."
        ))
    else:
        qa.append((
            "Why did changing the act work in this story?",
            f"It worked because the new act gave each child a different important role. The problem stopped being 'Who wins the prop?' and became 'How can both children shine?'"
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["prop_cfg"].tags) | set(f["repair"].tags) | {"reconciliation"}
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    if "prediction" in world.facts:
        lines.append(f"  predicted repair: {world.facts['prediction']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("parade", "horn", "copy", "Pip", "boy", "Nora", "girl", "mother", 0, "bouncy", "dramatic"),
    StoryParams("circus", "hat", "turns", "Mimi", "girl", "Leo", "boy", "father", 2, "busy", "patient"),
    StoryParams("parade", "wagon", "duet", "Toby", "boy", "June", "girl", "mother", 0, "cheerful", "helpful"),
    StoryParams("restaurant", "horn", "duet", "Lulu", "girl", "Finn", "boy", "father", 0, "earnest", "funny"),
    StoryParams("circus", "hat", "copy", "Beni", "boy", "Ava", "girl", "mother", 0, "small", "proud"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
repair_fits(T,P,turns,W) :- theme(T), prop(P), waiting_skill(W), W >= 1.
repair_fits(T,P,copy,W)  :- theme(T), prop(P), waiting_skill(W), copyable(P).
repair_fits(T,P,duet,W)  :- theme(T), prop(P), waiting_skill(W), supports_duet(T).

valid(T,P,R) :- chosen_waiting(W), repair_fits(T,P,R,W).

works :- chosen_theme(T), chosen_prop(P), chosen_repair(R), chosen_waiting(W), repair_fits(T,P,R,W).
outcome(reconciled) :- works.
bad_reason(waiting)  :- chosen_repair(turns), chosen_waiting(W), W < 1.
bad_reason(copyable) :- chosen_repair(copy), chosen_prop(P), not copyable(P).
bad_reason(duet)     :- chosen_repair(duet), chosen_theme(T), not supports_duet(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, t in THEMES.items():
        lines.append(asp.fact("theme", tid))
        if t.supports_duet:
            lines.append(asp.fact("supports_duet", tid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.copyable:
            lines.append(asp.fact("copyable", pid))
    for rid in REPAIRS:
        lines.append(asp.fact("repair", rid))
    for w in (0, 1, 2):
        lines.append(asp.fact("waiting_skill", w))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos(waiting_skill: int = 1) -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(f"chosen_waiting({waiting_skill}).", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> tuple[str, list[str]]:
    import asp
    extra = "\n".join([
        f"chosen_theme({params.theme}).",
        f"chosen_prop({params.prop}).",
        f"chosen_repair({params.repair}).",
        f"chosen_waiting({params.waiting_skill}).",
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1.\n#show bad_reason/1."))
    out = asp.atoms(model, "outcome")
    reasons = [r for (r,) in asp.atoms(model, "bad_reason")]
    return (out[0][0] if out else "invalid", sorted(reasons))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos(1))
    py_wait1 = {c for c in py if c[2] != "turns" or True}
    if asp_set == py_wait1:
        print(f"OK: ASP gate matches waiting-skill-1 valid set ({len(asp_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_wait1:
            print("  only in asp:", sorted(asp_set - py_wait1))
        if py_wait1 - asp_set:
            print("  only in python:", sorted(py_wait1 - asp_set))

    cases = list(CURATED)
    for s in range(30):
        rng = random.Random(s)
        try:
            p = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    bad = 0
    for p in cases:
        py_ok = repair_fits(THEMES[p.theme], PROPS[p.prop], REPAIRS[p.repair], p.waiting_skill)
        asp_out, _reasons = asp_outcome(p)
        asp_ok = asp_out == "reconciled"
        if py_ok != asp_ok:
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python repair gate on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differ.")

    # Smoke-test normal generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tot, a funny quarrel, and a fitted reconciliation."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--waiting-skill", type=int, choices=[0, 1, 2],
                    help="0 means too stirred up for turns; 1-2 means turns can work")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (theme, prop, repair) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, pool: list[str], avoid: str = "") -> str:
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    waiting_skill = args.waiting_skill if args.waiting_skill is not None else rng.choice([0, 1, 2])

    if args.theme and args.prop and args.repair:
        theme = THEMES[args.theme]
        prop = PROPS[args.prop]
        repair = REPAIRS[args.repair]
        if not repair_fits(theme, prop, repair, waiting_skill):
            raise StoryError(explain_repair(theme, prop, repair, waiting_skill))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.prop is None or c[1] == args.prop)
        and (args.repair is None or c[2] == args.repair)
        and repair_fits(THEMES[c[0]], PROPS[c[1]], REPAIRS[c[2]], waiting_skill)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, prop_id, repair_id = rng.choice(sorted(combos))
    tot_gender = rng.choice(["girl", "boy"])
    pal_gender = rng.choice(["girl", "boy"])
    tot_name = _pick_name(rng, tot_gender, TOT_NAMES)
    pal_name = _pick_name(rng, pal_gender, KID_NAMES, avoid=tot_name)
    parent = args.parent or rng.choice(["mother", "father"])
    tot_trait = rng.choice(TOT_TRAITS)
    pal_trait = rng.choice(KID_TRAITS)
    return StoryParams(
        theme_id, prop_id, repair_id,
        tot_name, tot_gender, pal_name, pal_gender,
        parent, waiting_skill, tot_trait, pal_trait
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        THEMES[params.theme],
        PROPS[params.prop],
        REPAIRS[params.repair],
        params.tot_name,
        params.tot_gender,
        params.pal_name,
        params.pal_gender,
        params.parent,
        params.waiting_skill,
        params.tot_trait,
        params.pal_trait,
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
        print(asp_program("chosen_waiting(1).", "#show valid/3.\n#show outcome/1.\n#show bad_reason/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        waiting_skill = args.waiting_skill if args.waiting_skill is not None else 1
        combos = asp_valid_combos(waiting_skill)
        print(f"{len(combos)} compatible (theme, prop, repair) combos for waiting_skill={waiting_skill}:\n")
        for theme, prop, repair in combos:
            print(f"  {theme:10} {prop:8} {repair}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.tot_name} and {p.pal_name}: {p.prop} in {p.theme} ({p.repair})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
