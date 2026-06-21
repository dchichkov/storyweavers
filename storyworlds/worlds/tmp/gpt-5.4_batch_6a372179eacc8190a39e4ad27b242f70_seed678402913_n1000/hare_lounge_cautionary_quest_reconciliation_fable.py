#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hare_lounge_cautionary_quest_reconciliation_fable.py
================================================================================

A standalone story world for a tiny fable-shaped domain:

A hare hurries on a quest to bring something useful to a woodland lounge.
A wiser companion warns against a risky shortcut. Sometimes the hare listens
and the trip stays smooth. Sometimes the hare rushes ahead, trouble follows,
and the companion helps. Either way, the ending proves the lesson: haste is
lighter than apology only when wisdom walks beside it.

Run it
------
    python storyworlds/worlds/gpt-5.4/hare_lounge_cautionary_quest_reconciliation_fable.py
    python storyworlds/worlds/gpt-5.4/hare_lounge_cautionary_quest_reconciliation_fable.py --item tart --hazard slick_stones
    python storyworlds/worlds/gpt-5.4/hare_lounge_cautionary_quest_reconciliation_fable.py --method dash_faster
    python storyworlds/worlds/gpt-5.4/hare_lounge_cautionary_quest_reconciliation_fable.py --all
    python storyworlds/worlds/gpt-5.4/hare_lounge_cautionary_quest_reconciliation_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/hare_lounge_cautionary_quest_reconciliation_fable.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
SENSE_MIN = 2
HARE_HURRY = 6.0
ELDER_BONUS = 3.0
CAREFUL_GUIDES = {"careful", "patient", "steady", "wise"}


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
        female = {"hare_girl", "otter_girl", "mouse_girl", "mole_girl", "doe", "aunt"}
        male = {"hare_boy", "otter_boy", "mouse_boy", "mole_boy", "badger", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Lounge:
    id: str
    label: str
    phrase: str
    gathering: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    purpose: str
    peril_tags: set[str] = field(default_factory=set)
    comfort_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    shortcut: str
    warning: str
    mishap: str
    required_tags: set[str] = field(default_factory=set)
    severity: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    use_line: str
    rescue_line: str
    solve_tags: set[str] = field(default_factory=set)
    sense: int = 2
    power: int = 1
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    hare = world.entities.get("hare")
    item = world.entities.get("item")
    if hare is None or item is None:
        return out
    if hare.meters["stumble"] < THRESHOLD:
        return out
    if item.meters["delivered"] >= THRESHOLD:
        return out
    sig = ("spill", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["troubled"] += 1
    hare.memes["fear"] += 1
    hare.memes["regret"] += 1
    out.append("__mishap__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spill", tag="physical", apply=_r_spill),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def item_at_risk(item: QuestItem, hazard: Hazard) -> bool:
    return bool(item.peril_tags & hazard.required_tags)


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def can_solve(method: Method, hazard: Hazard) -> bool:
    return bool(method.solve_tags & hazard.required_tags)


def best_method_for(hazard: Hazard) -> Method:
    candidates = [m for m in sensible_methods() if can_solve(m, hazard)]
    return max(candidates, key=lambda m: (m.power, m.sense, m.id))


def would_heed(guide_role: str, guide_trait: str) -> bool:
    caution = 5.0 if guide_trait in CAREFUL_GUIDES else 3.0
    if guide_role == "elder":
        caution += ELDER_BONUS
    return caution > HARE_HURRY


def outcome_of(params: "StoryParams") -> str:
    if would_heed(params.guide_role, params.guide_trait):
        return "heeded"
    method = METHODS[params.method]
    hazard = HAZARDS[params.hazard]
    if method.power >= hazard.severity and can_solve(method, hazard):
        return "rescued"
    return "spoiled"


def predict_trouble(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    hare = sim.get("hare")
    hare.meters["stumble"] += 1
    propagate(sim, narrate=False)
    item = sim.get("item")
    return {
        "hare_frightened": hare.memes["fear"] >= THRESHOLD,
        "item_troubled": item.meters["troubled"] >= THRESHOLD,
        "severity": hazard.severity,
    }


def introduce(world: World, hare: Entity, guide: Entity, lounge: Lounge, item: QuestItem) -> None:
    hare.memes["pride"] += 1
    hare.memes["joy"] += 1
    guide.memes["care"] += 1
    world.say(
        f"In the greenwood there stood {lounge.phrase}, where the small creatures liked "
        f"to {lounge.gathering}."
    )
    world.say(
        f"One bright afternoon, {hare.id} the hare promised to bring {item.phrase} there, "
        f"for it would {item.purpose}."
    )
    world.say(
        f'{guide.id}, {hare.id}\'s {guide.attrs.get("relation_word", "friend")}, walked beside '
        f'{hare.pronoun("object")} and listened to the quick little thump of {hare.pronoun("possessive")} feet.'
    )


def quest_call(world: World, hare: Entity, lounge: Lounge, item: QuestItem) -> None:
    world.say(
        f'"If I hurry, I shall reach {lounge.label} before the first lantern bugs wake," '
        f'said {hare.id}.'
    )
    if item.comfort_line:
        world.say(item.comfort_line)


def temptation(world: World, hare: Entity, hazard: Hazard) -> None:
    hare.memes["hurry"] += 1
    world.say(
        f"Before them lay {hazard.shortcut}, which looked shorter than the winding safe road."
    )
    world.say(
        f'"I can fly past {hazard.label} and save a whole handful of minutes," said {hare.id}.'
    )


def warn(world: World, guide: Entity, hare: Entity, hazard: Hazard) -> None:
    pred = predict_trouble(world, hazard)
    guide.memes["caution"] += 1
    world.facts["predicted_item_troubled"] = pred["item_troubled"]
    world.facts["predicted_severity"] = pred["severity"]
    extra = ""
    if guide.attrs.get("role") == "elder":
        extra = " I have seen haste make a feast late and a friend ashamed."
    world.say(
        f'{guide.id} shook {guide.pronoun("possessive")} head. "{hazard.warning}.{extra}"'
    )


def heed(world: World, hare: Entity, guide: Entity, method: Method, lounge: Lounge, item: QuestItem) -> None:
    hare.memes["relief"] += 1
    hare.memes["wisdom"] += 1
    world.say(
        f"{hare.id} twitched her nose, looked again, and let her hurry settle."
    )
    world.say(
        f'Together they {method.use_line}, and by the time they reached {lounge.label}, '
        f'{item.phrase} was still sound and tidy.'
    )


def defy(world: World, hare: Entity, guide: Entity) -> None:
    hare.memes["defiance"] += 1
    world.say(
        f'"I am only a little faster than danger," said {hare.id}, and before {guide.id} '
        f'could stop her, the hare sprang ahead.'
    )


def mishap(world: World, hare: Entity, item_ent: Entity, hazard: Hazard, item: QuestItem) -> None:
    hare.meters["stumble"] += 1
    item_ent.meters["jolted"] += 1
    propagate(world, narrate=False)
    world.say(hazard.mishap.replace("{hare}", hare.id).replace("{item}", item.label))
    if item_ent.meters["troubled"] >= THRESHOLD:
        world.say(
            f"For one sore heartbeat, {hare.id} feared that {item.phrase} would never reach the lounge at all."
        )


def rescue(world: World, hare: Entity, guide: Entity, method: Method, item_ent: Entity, lounge: Lounge) -> None:
    item_ent.meters["saved"] += 1
    item_ent.meters["delivered"] += 1
    hare.memes["gratitude"] += 1
    guide.memes["care"] += 1
    world.say(
        f"{guide.id} did not scold first. {guide.pronoun().capitalize()} {method.rescue_line}."
    )
    world.say(
        f"So they went on together to {lounge.label}, slower than before, but wiser with every step."
    )


def spoil(world: World, hare: Entity, guide: Entity, method: Method, item_ent: Entity, lounge: Lounge, item: QuestItem) -> None:
    item_ent.meters["spoiled"] += 1
    hare.memes["sadness"] += 1
    world.say(
        f"{guide.id} tried to help and {method.rescue_line}, but the harm was already done."
    )
    world.say(
        f"They still carried what they could to {lounge.label}, yet {item.phrase} was no longer fit for its first proud purpose."
    )


def apology(world: World, hare: Entity, guide: Entity) -> None:
    hare.memes["apology"] += 1
    guide.memes["forgiveness"] += 1
    world.say(
        f'At last {hare.id} lowered her ears. "You warned me kindly, and I answered with speed instead of sense," she said.'
    )
    world.say(
        f'{guide.id} touched {hare.id}\'s shoulder and replied, "A quick foot may slip, but a true heart can still come back."'
    )


def ending_heeded(world: World, hare: Entity, guide: Entity, lounge: Lounge, item: QuestItem) -> None:
    world.say(
        f"The creatures in {lounge.label} welcomed them with bright eyes, and {item.phrase} did exactly what it had been meant to do."
    )
    world.say(
        f"Thereafter {hare.id} still ran swiftly, but never so swiftly that she outran good advice; and in {lounge.ending_image}, she was content to lounge a little before boasting again."
    )


def ending_rescued(world: World, hare: Entity, guide: Entity, lounge: Lounge, item: QuestItem) -> None:
    world.say(
        f"When they reached {lounge.label}, the others made room on the moss seats and praised {guide.id}'s patience more than {hare.id}'s speed."
    )
    world.say(
        f"{hare.id} smiled at that and did not mind. In {lounge.ending_image}, hare and friend lounged side by side, and the lesson sat between them like a gentle lantern."
    )


def ending_spoiled(world: World, hare: Entity, guide: Entity, lounge: Lounge, item: QuestItem) -> None:
    world.say(
        f"The company at {lounge.label} shared what could still be shared, and none laughed at {hare.id}'s mistake."
    )
    world.say(
        f"But {hare.id} never forgot the small sorrow of arriving with a spoiled gift. Afterward, when she came to {lounge.ending_image}, she lounged more humbly and listened before leaping."
    )


def tell(
    lounge: Lounge,
    item: QuestItem,
    hazard: Hazard,
    method: Method,
    hare_name: str = "Hazel",
    guide_name: str = "Moss",
    guide_type: str = "mole_boy",
    guide_role: str = "peer",
    guide_trait: str = "careful",
) -> World:
    world = World()
    hare = world.add(Entity(
        id=hare_name,
        kind="character",
        type="hare_girl",
        label="the hare",
        role="hare",
        traits=["quick"],
        attrs={"species": "hare"},
    ))
    relation_word = "elder neighbor" if guide_role == "elder" else "friend"
    guide = world.add(Entity(
        id=guide_name,
        kind="character",
        type=guide_type,
        label="the guide",
        role="guide",
        traits=[guide_trait],
        attrs={"role": guide_role, "relation_word": relation_word},
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="quest_item",
        label=item.label,
        phrase=item.phrase,
        role="item",
        tags=set(item.tags),
    ))
    world.facts["guide_role"] = guide_role

    introduce(world, hare, guide, lounge, item)
    quest_call(world, hare, lounge, item)

    world.para()
    temptation(world, hare, hazard)
    warn(world, guide, hare, hazard)

    if would_heed(guide_role, guide_trait):
        heed(world, hare, guide, method, lounge, item)
        world.para()
        ending_heeded(world, hare, guide, lounge, item)
        outcome = "heeded"
        item_ent.meters["delivered"] += 1
    else:
        defy(world, hare, guide)
        world.para()
        mishap(world, hare, item_ent, hazard, item)
        if method.power >= hazard.severity and can_solve(method, hazard):
            world.para()
            rescue(world, hare, guide, method, item_ent, lounge)
            apology(world, hare, guide)
            world.para()
            ending_rescued(world, hare, guide, lounge, item)
            outcome = "rescued"
        else:
            world.para()
            spoil(world, hare, guide, method, item_ent, lounge, item)
            apology(world, hare, guide)
            world.para()
            ending_spoiled(world, hare, guide, lounge, item)
            outcome = "spoiled"

    world.facts.update(
        hare=hare,
        guide=guide,
        lounge=lounge,
        item_cfg=item,
        item=item_ent,
        hazard=hazard,
        method=method,
        outcome=outcome,
        warned=True,
        reconciled=hare.memes["apology"] >= THRESHOLD or outcome == "heeded",
        guide_trait=guide_trait,
        guide_role=guide_role,
    )
    return world


LOUNGES = {
    "willow": Lounge(
        id="willow",
        label="the willow lounge",
        phrase="a willow lounge woven from low green branches",
        gathering="rest in the cool shade and trade soft evening stories",
        ending_image="the willow lounge under its green curtains",
        tags={"lounge", "forest"},
    ),
    "moss": Lounge(
        id="moss",
        label="the moss lounge",
        phrase="a moss lounge tucked beside an old oak root",
        gathering="sit on springy moss and nibble slow suppers",
        ending_image="the moss lounge with cups of clover tea steaming in a ring",
        tags={"lounge", "forest"},
    ),
    "fern": Lounge(
        id="fern",
        label="the fern lounge",
        phrase="a fern lounge where the fronds bent together like little walls",
        gathering="settle into the green hush and watch evening shine on the brook",
        ending_image="the fern lounge in the silver dusk",
        tags={"lounge", "forest"},
    ),
}

ITEMS = {
    "tart": QuestItem(
        id="tart",
        label="blackberry tart",
        phrase="a small blackberry tart on a flat bark tray",
        purpose="sweeten the evening meal",
        peril_tags={"water", "balance"},
        comfort_line="The smell of berries made her imagine everyone smiling before she even arrived.",
        tags={"food", "berries"},
    ),
    "cushion": QuestItem(
        id="cushion",
        label="reed cushion",
        phrase="a reed cushion tied with blue grass",
        purpose="make the oldest guests sit more softly",
        peril_tags={"snag", "balance"},
        comfort_line="It was not grand, but it was kindly made.",
        tags={"cushion", "craft"},
    ),
    "lamp": QuestItem(
        id="lamp",
        label="glow-leaf lamp",
        phrase="a glow-leaf lamp cupped in a nutshell frame",
        purpose="bring gentle light to the dusk gathering",
        peril_tags={"water", "balance", "wind"},
        comfort_line="Its little leaf-light winked like a promise in her paws.",
        tags={"lamp", "light"},
    ),
    "tea": QuestItem(
        id="tea",
        label="mint tea leaves",
        phrase="a folded packet of mint tea leaves",
        purpose="fill the lounge with a fresh sweet smell",
        peril_tags={"water", "wind"},
        comfort_line="Every step made the packet breathe out a cool garden smell.",
        tags={"tea", "mint"},
    ),
}

HAZARDS = {
    "slick_stones": Hazard(
        id="slick_stones",
        label="the slick stones",
        shortcut="a line of wet stones skipping across the brook",
        warning="Those stones are shiny with brook-water, and one quick step will send your paws and your burden sideways",
        mishap="{hare} sprang onto the stones, but the brook polished them better than pride could grip; her paws slid, and the {item} lurched hard to one side.",
        required_tags={"water", "balance"},
        severity=3,
        tags={"brook", "water"},
    ),
    "thorn_gap": Hazard(
        id="thorn_gap",
        label="the thorn gap",
        shortcut="a narrow thorn gap through the hedge",
        warning="That hedge catches at anything broad or soft, and haste only teaches thorns where to pull",
        mishap="{hare} darted into the thorn gap. In a blink the brambles snatched at the {item}, and she had to kick and twist to free herself.",
        required_tags={"snag"},
        severity=2,
        tags={"thorn", "hedge"},
    ),
    "windy_log": Hazard(
        id="windy_log",
        label="the windy log",
        shortcut="a fallen log lying high above a windy hollow",
        warning="That log shivers under a running foot, and the wind there loves to tip light things out of careful paws",
        mishap="{hare} raced along the log just as a gust climbed out of the hollow. The wood trembled, she skipped sideways, and the {item} bobbed dangerously in the air.",
        required_tags={"wind", "balance"},
        severity=2,
        tags={"wind", "log"},
    ),
    "dry_lane": Hazard(
        id="dry_lane",
        label="the dry lane",
        shortcut="a tidy dry lane between hazel bushes",
        warning="That lane is plain but harmless",
        mishap="{hare} hurried through the dry lane, and nothing at all went wrong.",
        required_tags=set(),
        severity=0,
        tags={"path"},
    ),
}

METHODS = {
    "footbridge": Method(
        id="footbridge",
        label="the footbridge",
        use_line="took the old footbridge and kept to the rail",
        rescue_line="led her down to the old footbridge and steadied the load across the planks",
        solve_tags={"water", "balance"},
        sense=3,
        power=3,
        tags={"bridge", "safe_path"},
    ),
    "carry_together": Method(
        id="carry_together",
        label="carrying it together",
        use_line="slowed down, set their paws together, and carried the burden between them",
        rescue_line="set the burden between them and carried it together, paw by paw",
        solve_tags={"balance", "snag", "wind"},
        sense=3,
        power=2,
        tags={"help", "teamwork"},
    ),
    "long_meadow": Method(
        id="long_meadow",
        label="the long meadow road",
        use_line="went the long way round by the meadow road",
        rescue_line="turned her back to the shortcut and walked her round by the long meadow road",
        solve_tags={"water", "snag", "wind", "balance"},
        sense=3,
        power=3,
        tags={"safe_path", "patience"},
    ),
    "tie_tighter": Method(
        id="tie_tighter",
        label="a tighter knot",
        use_line="stopped to tie everything more tightly before going on",
        rescue_line="retied the load as neatly as he could",
        solve_tags={"snag", "wind"},
        sense=2,
        power=1,
        tags={"knot", "care"},
    ),
    "dash_faster": Method(
        id="dash_faster",
        label="running even faster",
        use_line="simply ran faster and hoped speed would hide the danger",
        rescue_line="urged her to dash again before the trouble could catch up",
        solve_tags=set(),
        sense=1,
        power=0,
        tags={"bad_idea"},
    ),
}

HARE_NAMES = ["Hazel", "Briony", "Pip", "Mira", "Clover", "Nell"]
GUIDE_NAMES = ["Moss", "Tavin", "Purl", "Reed", "Bramble", "Ivo"]
GUIDE_TYPES = ["mole_boy", "mouse_girl", "badger", "otter_girl"]
GUIDE_TRAITS = ["careful", "patient", "steady", "wise", "gentle"]


@dataclass
class StoryParams:
    lounge: str
    item: str
    hazard: str
    method: str
    hare_name: str
    guide_name: str
    guide_type: str
    guide_role: str
    guide_trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for lounge_id in LOUNGES:
        for item_id, item in ITEMS.items():
            for hazard_id, hazard in HAZARDS.items():
                if item_at_risk(item, hazard):
                    combos.append((lounge_id, item_id, hazard_id))
    return combos


KNOWLEDGE = {
    "hare": [
        (
            "What is a hare?",
            "A hare is a fast wild animal with long legs and long ears. Hares can run very quickly, but being quick is not the same as being careful.",
        )
    ],
    "lounge": [
        (
            "What does lounge mean?",
            "To lounge means to rest in an easy, relaxed way. A lounge can also mean a cozy place where friends sit together.",
        )
    ],
    "brook": [
        (
            "Why are wet stones slippery?",
            "Water makes smooth stones hard to grip. Feet can slide on them before you are ready.",
        )
    ],
    "thorn": [
        (
            "Why are thorns a problem?",
            "Thorns are sharp and hook onto fur, cloth, or baskets. When you rush through them, they can catch and pull at what you carry.",
        )
    ],
    "wind": [
        (
            "Why can wind make carrying things hard?",
            "Wind pushes light things and can throw your balance off. That is why people and animals slow down when a path is windy.",
        )
    ],
    "bridge": [
        (
            "Why is a bridge safer than hopping on wet stones?",
            "A bridge gives you a steadier way over water. It is easier to keep your feet and your load balanced on a solid path.",
        )
    ],
    "teamwork": [
        (
            "Why does carrying something together help?",
            "Two friends can steady a load better than one hurrying animal can. Teamwork makes a hard job lighter and safer.",
        )
    ],
    "patience": [
        (
            "Why can taking the long way be wise?",
            "A longer path can still be the better path if it keeps you safe. Saving trouble is often better than saving one minute.",
        )
    ],
    "apology": [
        (
            "What is an apology?",
            "An apology is when you say you were wrong and are sorry for the hurt or trouble you caused. A true apology is honest and tries to mend the friendship too.",
        )
    ],
}
KNOWLEDGE_ORDER = ["hare", "lounge", "brook", "thorn", "wind", "bridge", "teamwork", "patience", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hare = f["hare"]
    guide = f["guide"]
    item = f["item_cfg"]
    lounge = f["lounge"]
    hazard = f["hazard"]
    outcome = f["outcome"]
    if outcome == "heeded":
        return [
            f'Write a short fable for a 3-to-5-year-old that includes the words "hare" and "lounge". Make it about a quest to bring {item.label} to {lounge.label}, where wise advice prevents trouble.',
            f"Tell a cautionary quest story where {hare.id} the hare wants to rush across {hazard.label}, but listens to {guide.id} and arrives safely.",
            f"Write a reconciliation fable where the lesson is learned before disaster, and the ending shows friends resting together in a woodland lounge.",
        ]
    if outcome == "rescued":
        return [
            f'Write a small fable using the words "hare" and "lounge" about a hurried quest, a mistake on a shortcut, and a kind rescue.',
            f"Tell a cautionary story where {hare.id} the hare ignores {guide.id}'s warning on the way to {lounge.label}, then apologizes after being helped.",
            f"Write a quest-and-reconciliation tale where speed causes trouble, patience repairs it, and the ending proves the friendship grew stronger.",
        ]
    return [
        f'Write a gentle cautionary fable that includes "hare" and "lounge", where a hasty quest goes wrong and the gift is spoiled.',
        f"Tell a story where {hare.id} the hare ignores a warning on the way to {lounge.label}, then must apologize and learn humility.",
        f"Write a child-facing reconciliation fable with a sad little loss, a forgiven mistake, and a moral about listening before leaping.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hare = f["hare"]
    guide = f["guide"]
    item = f["item_cfg"]
    lounge = f["lounge"]
    hazard = f["hazard"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hare.id} the hare and {guide.id}, {hare.id}'s {guide.attrs.get('relation_word', 'friend')}. They were traveling to {lounge.label} with {item.phrase}.",
        ),
        (
            f"What was {hare.id}'s quest?",
            f"{hare.id}'s quest was to bring {item.phrase} to {lounge.label}. The gift mattered because it would {item.purpose}.",
        ),
        (
            f"Why did {guide.id} warn {hare.id}?",
            f"{guide.id} warned {hare.id} because {hazard.warning.lower()}. The warning came from seeing that haste could trouble both the hare and the thing she carried.",
        ),
    ]
    if outcome == "heeded":
        qa.append((
            f"What happened after {hare.id} heard the warning?",
            f"{hare.id} listened, let her hurry settle, and chose the safer way. Because she accepted the warning in time, nothing was dropped or spoiled.",
        ))
        qa.append((
            f"How did the story show reconciliation if there was no accident?",
            f"The story showed harmony by having {hare.id} trust {guide.id}'s advice instead of arguing. They reached the lounge together and rested as friends, which proves the bond stayed warm.",
        ))
    elif outcome == "rescued":
        qa.append((
            f"What went wrong on the shortcut?",
            f"{hare.id} rushed ahead and trouble struck at {hazard.label}. The mishap scared her because it seemed {item.phrase} might never reach the lounge safely.",
        ))
        qa.append((
            f"How did {guide.id} help?",
            f"{guide.id} {method.rescue_line}. That patient help turned the mistake into a rescue instead of a total loss.",
        ))
        qa.append((
            f"How did {hare.id} and {guide.id} reconcile?",
            f"{hare.id} apologized for choosing speed instead of sense, and {guide.id} answered gently. Their friendship healed because the apology was honest and the help had already shown kindness.",
        ))
    else:
        qa.append((
            f"Did the quest succeed exactly as {hare.id} hoped?",
            f"No. They still reached {lounge.label}, but {item.phrase} was spoiled for its first purpose. The loss was small, yet it made the lesson feel real.",
        ))
        qa.append((
            f"How did the story still reach reconciliation?",
            f"{hare.id} admitted she was wrong, and {guide.id} forgave her instead of mocking her. The gift was spoiled, but the friendship was mended.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"hare", "lounge", "apology"}
    hazard = f["hazard"]
    method = f["method"]
    if "water" in hazard.required_tags:
        tags.add("brook")
    if "snag" in hazard.required_tags:
        tags.add("thorn")
    if "wind" in hazard.required_tags:
        tags.add("wind")
    if method.id == "footbridge":
        tags.add("bridge")
    if method.id == "carry_together":
        tags.add("teamwork")
    if method.id == "long_meadow":
        tags.add("patience")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        lounge="willow",
        item="tart",
        hazard="slick_stones",
        method="footbridge",
        hare_name="Hazel",
        guide_name="Moss",
        guide_type="mole_boy",
        guide_role="elder",
        guide_trait="wise",
    ),
    StoryParams(
        lounge="moss",
        item="cushion",
        hazard="thorn_gap",
        method="carry_together",
        hare_name="Briony",
        guide_name="Purl",
        guide_type="mouse_girl",
        guide_role="peer",
        guide_trait="patient",
    ),
    StoryParams(
        lounge="fern",
        item="lamp",
        hazard="windy_log",
        method="tie_tighter",
        hare_name="Clover",
        guide_name="Reed",
        guide_type="badger",
        guide_role="peer",
        guide_trait="gentle",
    ),
    StoryParams(
        lounge="moss",
        item="tea",
        hazard="slick_stones",
        method="long_meadow",
        hare_name="Mira",
        guide_name="Ivo",
        guide_type="otter_girl",
        guide_role="peer",
        guide_trait="steady",
    ),
]


def explain_rejection(item: QuestItem, hazard: Hazard) -> str:
    if not hazard.required_tags:
        return (
            f"(No story: {hazard.label} is not really a hazard here. A cautionary quest needs a shortcut that could honestly trouble {item.label}.)"
        )
    return (
        f"(No story: {item.label} is not at risk from {hazard.label}. The warning must fit the thing the hare is carrying.)"
    )


def explain_method(method_id: str, hazard_id: str) -> str:
    method = METHODS[method_id]
    hazard = HAZARDS[hazard_id]
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method_id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Try a safer method such as {better}.)"
        )
    if not can_solve(method, hazard):
        return (
            f"(No story: {method.label} does not honestly solve the problem at {hazard.label}. Pick a method that matches the danger.)"
        )
    return "(No story: this method does not fit the hazard.)"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
at_risk(I, H) :- item(I), hazard(H), item_peril(I, T), hazard_need(H, T).
valid(L, I, H) :- lounge(L), at_risk(I, H).
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
helps(M, H) :- method(M), hazard(H), solve_tag(M, T), hazard_need(H, T).

% --- outcome model ---------------------------------------------------------
careful_now(T) :- guide_trait(T), careful_trait(T).
guide_caution(5) :- careful_now(T), guide_trait(T).
guide_caution(3) :- not careful_now(_).
role_bonus(3) :- guide_role(elder).
role_bonus(0) :- not guide_role(elder).
authority(C + B) :- guide_caution(C), role_bonus(B).
heeded :- authority(A), hurry(H), A > H.

contained :- chosen_method(M), chosen_hazard(H), helps(M, H),
             power(M, P), severity(H, S), P >= S.

outcome(heeded) :- heeded.
outcome(rescued) :- not heeded, contained.
outcome(spoiled) :- not heeded, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lounge_id in LOUNGES:
        lines.append(asp.fact("lounge", lounge_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for tag in sorted(item.peril_tags):
            lines.append(asp.fact("item_peril", item_id, tag))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("severity", hazard_id, hazard.severity))
        for tag in sorted(hazard.required_tags):
            lines.append(asp.fact("hazard_need", hazard_id, tag))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
        for tag in sorted(method.solve_tags):
            lines.append(asp.fact("solve_tag", method_id, tag))
    for trait in sorted(CAREFUL_GUIDES):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("hurry", int(HARE_HURRY)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(name for (name,) in asp.atoms(model, "sensible"))


def asp_helps() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show helps/2."))
    return sorted(set(asp.atoms(model, "helps")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("guide_role", params.guide_role),
        asp.fact("guide_trait", params.guide_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    py_sens = {m.id for m in sensible_methods()}
    cl_sens = set(asp_sensible())
    if py_sens == cl_sens:
        print(f"OK: sensible methods match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(cl_sens)} python={sorted(py_sens)}")

    py_helps = sorted((m.id, h.id) for m in METHODS.values() for h in HAZARDS.values() if can_solve(m, h))
    cl_helps = sorted(asp_helps())
    if py_helps == cl_helps:
        print(f"OK: hazard-solving relations match ({len(py_helps)} pairs).")
    else:
        rc = 1
        print("MISMATCH in helps/2:")
        print("  clingo:", cl_helps)
        print("  python:", py_helps)

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        sink = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = sink
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old_stdout
        print("OK: smoke test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a hare on a quest to a woodland lounge, a risky shortcut, and a lesson about listening."
    )
    ap.add_argument("--lounge", choices=LOUNGES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--guide-role", choices=["peer", "elder"])
    ap.add_argument("--guide-trait", choices=GUIDE_TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and not HAZARDS[args.hazard].required_tags:
        item = ITEMS[args.item] if args.item else next(iter(ITEMS.values()))
        raise StoryError(explain_rejection(item, HAZARDS[args.hazard]))

    if args.item and args.hazard:
        item = ITEMS[args.item]
        hazard = HAZARDS[args.hazard]
        if not item_at_risk(item, hazard):
            raise StoryError(explain_rejection(item, hazard))

    combos = [
        combo for combo in valid_combos()
        if (args.lounge is None or combo[0] == args.lounge)
        and (args.item is None or combo[1] == args.item)
        and (args.hazard is None or combo[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lounge_id, item_id, hazard_id = rng.choice(sorted(combos))
    hazard = HAZARDS[hazard_id]

    if args.method:
        if METHODS[args.method].sense < SENSE_MIN or not can_solve(METHODS[args.method], hazard):
            raise StoryError(explain_method(args.method, hazard_id))
        method_id = args.method
    else:
        candidates = [m.id for m in sensible_methods() if can_solve(m, hazard)]
        if not candidates:
            raise StoryError("(No sensible method can solve the chosen hazard.)")
        method_id = rng.choice(sorted(candidates))

    guide_role = args.guide_role or rng.choice(["peer", "peer", "elder"])
    guide_trait = args.guide_trait or rng.choice(GUIDE_TRAITS)
    hare_name = rng.choice(HARE_NAMES)
    guide_name = rng.choice([n for n in GUIDE_NAMES if n != hare_name])
    guide_type = rng.choice(GUIDE_TYPES)

    return StoryParams(
        lounge=lounge_id,
        item=item_id,
        hazard=hazard_id,
        method=method_id,
        hare_name=hare_name,
        guide_name=guide_name,
        guide_type=guide_type,
        guide_role=guide_role,
        guide_trait=guide_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        lounge = LOUNGES[params.lounge]
        item = ITEMS[params.item]
        hazard = HAZARDS[params.hazard]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if not item_at_risk(item, hazard):
        raise StoryError(explain_rejection(item, hazard))
    if method.sense < SENSE_MIN or not can_solve(method, hazard):
        raise StoryError(explain_method(params.method, params.hazard))

    world = tell(
        lounge=lounge,
        item=item,
        hazard=hazard,
        method=method,
        hare_name=params.hare_name,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
        guide_role=params.guide_role,
        guide_trait=params.guide_trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show helps/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        helps = asp_helps()
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (lounge, item, hazard) combos:\n")
        for lounge, item, hazard in combos:
            methods = sorted(m for (m, h) in helps if h == hazard and m in asp_sensible())
            print(f"  {lounge:7} {item:8} {hazard:12} -> {', '.join(methods)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hare_name}: {p.item} to {p.lounge} by {p.hazard} "
                f"({p.method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
