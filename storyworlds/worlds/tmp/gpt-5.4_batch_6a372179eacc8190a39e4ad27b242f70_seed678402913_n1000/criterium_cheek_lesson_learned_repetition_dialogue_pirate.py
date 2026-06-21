#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/criterium_cheek_lesson_learned_repetition_dialogue_pirate.py
=========================================================================================

A standalone storyworld for a small pirate-play tale. Two children build a
pretend pirate course and argue about the "captain's criterium" for winning a
treasure token: cross carefully, keep your balance, and ask for help if the
bridge wobbles. One child gets cheeky, tries a risky shortcut, slips, and
learns that the same brave-looking move is not the same as a safe move. A calm
grown-up helps them turn the game into a better pirate test.

The world is simulated with typed entities carrying physical meters and
emotional memes. Story text is rendered from state and history rather than from
a fixed template. A small ASP twin mirrors the reasonableness gate and outcome
logic so --verify can compare declarative parity with the Python model.

Run it
------
    python storyworlds/worlds/gpt-5.4/criterium_cheek_lesson_learned_repetition_dialogue_pirate.py
    python storyworlds/worlds/gpt-5.4/criterium_cheek_lesson_learned_repetition_dialogue_pirate.py --bridge couch_gap --shortcut armrest
    python storyworlds/worlds/gpt-5.4/criterium_cheek_lesson_learned_repetition_dialogue_pirate.py --bridge rug_path --shortcut leap
    python storyworlds/worlds/gpt-5.4/criterium_cheek_lesson_learned_repetition_dialogue_pirate.py --all
    python storyworlds/worlds/gpt-5.4/criterium_cheek_lesson_learned_repetition_dialogue_pirate.py --qa --json
    python storyworlds/worlds/gpt-5.4/criterium_cheek_lesson_learned_repetition_dialogue_pirate.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    stable: bool = False
    risky: bool = False
    protective: bool = False
    # shared axes
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


@dataclass
class Theme:
    id: str
    scene: str
    props: str
    title_a: str
    title_b: str
    treasure: str
    sendoff: str


@dataclass
class Bridge:
    id: str
    label: str
    phrase: str
    surface: str
    stable: bool
    wobble: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Shortcut:
    id: str
    label: str
    boast: str
    risky: bool
    rash: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    steadiness: int
    text: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_wobble_fear(world: World) -> list[str]:
    out: list[str] = []
    bridge = world.entities.get("bridge")
    child = world.entities.get("captain")
    if not bridge or not child:
        return out
    if bridge.meters["wobbling"] < THRESHOLD:
        return out
    sig = ("wobble_fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__wobble__")
    return out


def _r_slip_bruise(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("captain")
    if not child:
        return out
    if child.meters["slipping"] < THRESHOLD:
        return out
    sig = ("slip_bruise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["bruise"] += 1
    child.meters["cheek_red"] += 1
    child.memes["embarrassed"] += 1
    out.append("__slip__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble_fear", tag="physical", apply=_r_wobble_fear),
    Rule(name="slip_bruise", tag="physical", apply=_r_slip_bruise),
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


def hazard_at_risk(bridge: Bridge, shortcut: Shortcut) -> bool:
    return (not bridge.stable) or shortcut.risky


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def challenge_severity(bridge: Bridge, shortcut: Shortcut) -> int:
    return bridge.wobble + shortcut.rash


def is_controlled(bridge: Bridge, shortcut: Shortcut, fix: Fix) -> bool:
    return fix.steadiness >= challenge_severity(bridge, shortcut)


def explain_rejection(bridge: Bridge, shortcut: Shortcut) -> str:
    return (
        f"(No story: {bridge.label} is already steady and {shortcut.label} is not a risky shortcut, "
        f"so there is no honest pirate problem to fix.)"
    )


def explain_fix(fid: str) -> str:
    fx = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fx.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_slip(world: World) -> dict:
    sim = world.copy()
    captain = sim.get("captain")
    bridge = sim.get("bridge")
    bridge.meters["wobbling"] += 1
    captain.meters["slipping"] += 1
    propagate(sim, narrate=False)
    return {
        "slip": captain.meters["slipping"] >= THRESHOLD,
        "bruise": captain.meters["bruise"] >= THRESHOLD,
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme, bridge: Bridge) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One afternoon, {a.id} and {b.id} turned the living room into {theme.scene}. "
        f"{theme.props}"
    )
    world.say(
        f'"{theme.title_a} {a.id}! {theme.title_b} {b.id}!" {a.id} cried. '
        f'"The treasure chest is waiting across {bridge.phrase}!"'
    )


def set_criterium(world: World, b: Entity, theme: Theme, bridge: Bridge) -> None:
    b.memes["care"] += 1
    world.say(
        f"{b.id} pointed at {bridge.surface} and made up the captain's criterium. "
        f'"One pirate rule, one pirate rule, one pirate rule," {b.pronoun()} said. '
        f'"Walk slow, keep your balance, and if the bridge wobbles, call a grown-up before anyone reaches {theme.treasure}."'
    )


def boast(world: World, a: Entity, shortcut: Shortcut) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} gave a cheeky grin and tapped {a.pronoun("possessive")} own cheek. '
        f'"{shortcut.boast}"'
    )


def warn(world: World, b: Entity, a: Entity, bridge: Bridge, shortcut: Shortcut, parent: Entity) -> None:
    pred = predict_slip(world)
    world.facts["predicted_slip"] = pred["slip"]
    world.facts["predicted_bruise"] = pred["bruise"]
    b.memes["caution"] += 1
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, that is not the criterium," '
        f'{b.pronoun()} said. "The brave way is the careful way. '
        f'If you rush on {bridge.surface} and try {shortcut.label}, you could slip and bump your cheek. '
        f'Let\'s ask {parent.label_word} to make the bridge safer."'
    )


def defy(world: World, a: Entity, shortcut: Shortcut) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"I can do it, I can do it, I can do it," {a.id} said, and dashed toward {shortcut.label}.'
    )


def accident(world: World, a: Entity, bridge_ent: Entity, bridge: Bridge, shortcut: Shortcut) -> None:
    bridge_ent.meters["wobbling"] += 1
    a.meters["slipping"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {bridge.surface} gave a little wobble. {a.id}'s foot skidded, {a.pronoun()} sat down with a soft thump, "
        f"and one red spot bloomed on {a.pronoun('possessive')} cheek."
    )
    world.say(
        f"For a moment, the treasure game stopped feeling bold and started feeling real."
    )


def cry_for_help(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.capitalize()}! {parent.label_word.capitalize()}! {parent.label_word.capitalize()}!" {b.id} called.')
    world.say(f"{b.id} knelt beside the bridge and kept very still.")


def fix_bridge(world: World, parent: Entity, bridge_ent: Entity, bridge: Bridge, fix: Fix) -> None:
    bridge_ent.meters["wobbling"] = 0.0
    bridge_ent.meters["steady"] += 1
    bridge_ent.stable = True
    world.say(
        f"{parent.label_word.capitalize()} came in quickly and {fix.text}"
    )
    world.say(
        f'Soon {bridge.phrase} looked less like a tipping plank and more like a real path to {world.facts["theme"].treasure}.'
    )


def comfort_and_lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["lesson"] += 1
    b.memes["trust"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside {a.id} and touched {a.pronoun("possessive")} shoulder. '
        f'"Are you hurt badly?" {parent.pronoun()} asked.'
    )
    world.say(
        f'"No, just my cheek," {a.id} whispered.'
    )
    world.say(
        f'"Then this is a small bump and a big lesson," {parent.pronoun()} said. '
        f'"A pirate does not prove bravery by rushing. A pirate proves bravery by following the criterium, listening, and asking for help before a wobble becomes a fall."'
    )


def second_try(world: World, a: Entity, b: Entity, theme: Theme, bridge: Bridge) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["confidence"] += 1
    world.say(
        f"The children tried again. "
        f'"Walk slow, keep your balance, ask for help," {b.id} said.'
    )
    world.say(
        f'"Walk slow, keep your balance, ask for help," {a.id} repeated, this time without the cheeky grin.'
    )
    world.say(
        f"Step by step, they crossed {bridge.phrase}, reached {theme.treasure}, and lifted the shoebox lid as if it were a chest full of gold."
    )
    world.say(
        f"{theme.sendoff}"
    )


def tell(
    theme: Theme,
    bridge: Bridge,
    shortcut: Shortcut,
    fix: Fix,
    captain_name: str = "Tom",
    captain_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    captain = world.add(Entity(id="captain", kind="character", type=captain_gender, label=captain_name, role="captain"))
    mate = world.add(Entity(id="mate", kind="character", type=mate_gender, label=mate_name, role="mate"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    bridge_ent = world.add(
        Entity(
            id="bridge",
            kind="thing",
            type="bridge",
            label=bridge.label,
            phrase=bridge.phrase,
            stable=bridge.stable,
            attrs={"surface": bridge.surface},
        )
    )

    world.facts["theme"] = theme
    world.facts["bridge_cfg"] = bridge
    world.facts["shortcut_cfg"] = shortcut
    world.facts["fix_cfg"] = fix

    play_setup(world, captain, mate, theme, bridge)
    set_criterium(world, mate, theme, bridge)

    world.para()
    boast(world, captain, shortcut)
    warn(world, mate, captain, bridge, shortcut, parent)
    defy(world, captain, shortcut)

    world.para()
    accident(world, captain, bridge_ent, bridge, shortcut)
    cry_for_help(world, mate, parent)

    world.para()
    fix_bridge(world, parent, bridge_ent, bridge, fix)
    comfort_and_lesson(world, parent, captain, mate)

    world.para()
    second_try(world, captain, mate, theme, bridge)

    world.facts.update(
        captain=captain,
        mate=mate,
        parent=parent,
        bridge=bridge_ent,
        shortcut=shortcut,
        fix=fix,
        slipped=captain.meters["slipping"] >= THRESHOLD,
        bruised=captain.meters["bruise"] >= THRESHOLD,
        learned=captain.memes["lesson"] >= THRESHOLD,
        repeated_rule=True,
        outcome="learned",
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a windy pirate ship with a paper sail and a blanket sea",
        props="The sofa was the ship, two cushions were barrels, and a shoebox with shiny buttons inside was the treasure chest.",
        title_a="Captain",
        title_b="First Mate",
        treasure="the treasure chest",
        sendoff="They did not race this time. They sailed on in slow, proud pirate steps.",
    ),
    "harbor": Theme(
        id="harbor",
        scene="a busy pirate harbor with rope docks and a hidden chest",
        props="The sofa was the dock, a stool was the lookout post, and a blue blanket puddled around the floor like a sleepy sea.",
        title_a="Captain",
        title_b="Deck Mate",
        treasure="the brass-button treasure",
        sendoff="When they were done, the harbor felt bright, orderly, and ready for one more careful voyage.",
    ),
}

BRIDGES = {
    "couch_gap": Bridge(
        id="couch_gap",
        label="couch gap bridge",
        phrase="the narrow bridge between the sofa and the ottoman",
        surface="the narrow board between the sofa and the ottoman",
        stable=False,
        wobble=2,
        tags={"bridge", "balance"},
    ),
    "book_plank": Bridge(
        id="book_plank",
        label="book plank",
        phrase="the big picture book laid across two cushions",
        surface="the picture-book plank",
        stable=False,
        wobble=1,
        tags={"bridge", "balance"},
    ),
    "rug_path": Bridge(
        id="rug_path",
        label="rug path",
        phrase="the striped rug path",
        surface="the striped rug",
        stable=True,
        wobble=0,
        tags={"path", "balance"},
    ),
}

SHORTCUTS = {
    "armrest": Shortcut(
        id="armrest",
        label="the armrest like a diving rail",
        boast=''"I do not need the slow rule. I can skim along the armrest like the fastest pirate in the world!"'',
        risky=True,
        rash=2,
        tags={"risky", "climb"},
    ),
    "leap": Shortcut(
        id="leap",
        label="a jumping leap over the middle",
        boast=''"I can jump the middle in one hop and land beside the chest!"'',
        risky=True,
        rash=1,
        tags={"risky", "jump"},
    ),
    "march": Shortcut(
        id="march",
        label="a straight pirate march",
        boast=''"I can march across just by keeping my boots lined up."' ,
        risky=False,
        rash=0,
        tags={"careful"},
    ),
}

FIXES = {
    "hold_and_pad": Fix(
        id="hold_and_pad",
        label="held the bridge and padded the landing",
        sense=3,
        steadiness=4,
        text="set a folded cushion by the edge, held the bridge steady with one hand, and showed the children where to put their feet",
        qa_text="made the bridge safer by padding the edge and holding it steady",
        tags={"helper", "cushion", "balance"},
    ),
    "move_treasure": Fix(
        id="move_treasure",
        label="moved the treasure closer",
        sense=2,
        steadiness=2,
        text="moved the treasure chest to the far end of the rug and said the rug could be the new ship's bridge",
        qa_text="changed the game so the children could cross on the rug instead",
        tags={"helper", "rug", "balance"},
    ),
    "just_watch": Fix(
        id="just_watch",
        label="only watched",
        sense=1,
        steadiness=0,
        text="stood nearby and said to be careful, but did not change the bridge at all",
        qa_text="only watched and gave a warning",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]


@dataclass
class StoryParams:
    theme: str
    bridge: str
    shortcut: str
    fix: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="pirates",
        bridge="couch_gap",
        shortcut="armrest",
        fix="hold_and_pad",
        captain_name="Tom",
        captain_gender="boy",
        mate_name="Lily",
        mate_gender="girl",
        parent="mother",
    ),
    StoryParams(
        theme="harbor",
        bridge="book_plank",
        shortcut="leap",
        fix="move_treasure",
        captain_name="Max",
        captain_gender="boy",
        mate_name="Mia",
        mate_gender="girl",
        parent="father",
    ),
    StoryParams(
        theme="pirates",
        bridge="book_plank",
        shortcut="armrest",
        fix="hold_and_pad",
        captain_name="Finn",
        captain_gender="boy",
        mate_name="Nora",
        mate_gender="girl",
        parent="mother",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_fixes():
        return combos
    for theme_id in THEMES:
        for bridge_id, bridge in BRIDGES.items():
            for shortcut_id, shortcut in SHORTCUTS.items():
                if hazard_at_risk(bridge, shortcut):
                    combos.append((theme_id, bridge_id, shortcut_id))
    return combos


KNOWLEDGE = {
    "bridge": [
        (
            "Why should you walk slowly on something narrow?",
            "Walking slowly helps your body keep balance. Quick steps make it easier to wobble or slip."
        )
    ],
    "balance": [
        (
            "What does balance mean?",
            "Balance means keeping your body steady so you do not tip over. You use your feet, arms, and careful steps to help."
        )
    ],
    "helper": [
        (
            "Why is it smart to call a grown-up when a game feels unsafe?",
            "A grown-up can make the place safer or stop the game before someone gets hurt. Asking for help is a brave choice."
        )
    ],
    "cushion": [
        (
            "What does a cushion do if someone bumps into it?",
            "A cushion is soft, so it can make a little bump gentler. It does not make risky play safe all by itself, but it can help."
        )
    ],
    "rug": [
        (
            "Why is a rug safer than a narrow plank for walking games?",
            "A rug lies flat on the floor, so it does not tip the way a raised plank can. Flat ground is easier to cross carefully."
        )
    ],
    "risky": [
        (
            "What does risky mean?",
            "Risky means something could go wrong and someone could get hurt. A risky choice is not the same as a brave choice."
        )
    ],
    "jump": [
        (
            "Why can jumping across furniture be dangerous?",
            "Furniture can slide, tip, or be farther away than it looks. A jump that seems fun can end in a fall."
        )
    ],
    "climb": [
        (
            "Why is climbing on an armrest a bad idea?",
            "An armrest is narrow and not made for walking on. It is easy to slip off the side."
        )
    ],
    "careful": [
        (
            "How can children make pretend play safer?",
            "They can choose steady places to play, move slowly, and listen when someone warns them. Good rules help games stay fun."
        )
    ],
}
KNOWLEDGE_ORDER = ["bridge", "balance", "helper", "cushion", "rug", "risky", "jump", "climb", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    bridge = f["bridge_cfg"]
    shortcut = f["shortcut_cfg"]
    captain = f["captain"]
    mate = f["mate"]
    return [
        f'Write a pirate-play story for a 3-to-5-year-old that includes the words "criterium" and "cheek".',
        f"Tell a story where {captain.label} gets cheeky during a pretend pirate game, ignores {mate.label}'s safety criterium, slips, and learns a lesson.",
        f"Write a dialogue-rich pirate tale with repetition, a wobbling bridge, and a happy ending where the children cross {bridge.phrase} the careful way instead of trying {shortcut.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    parent = f["parent"]
    theme = f["theme"]
    bridge = f["bridge_cfg"]
    shortcut = f["shortcut_cfg"]
    fix = f["fix"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children playing pirates, {captain.label} and {mate.label}, and their {pw} who helps them. They turn the living room into {theme.scene}."
        ),
        (
            "What was the captain's criterium?",
            f"The rule was to walk slowly, keep balance, and call a grown-up if the bridge wobbled. The criterium mattered because the treasure game used a narrow crossing."
        ),
        (
            f"Why did {mate.label} warn {captain.label}?",
            f"{mate.label} knew that rushing across {bridge.surface} and trying {shortcut.label} could lead to a slip. {mate.pronoun().capitalize()} was trying to keep the pirate game fun without anyone getting hurt."
        ),
        (
            f"What happened to {captain.label}'s cheek?",
            f"{captain.label} slipped and got a small bump that left one red spot on {captain.pronoun('possessive')} cheek. The bump was not serious, but it made the danger feel real."
        ),
        (
            f"How did {pw} help?",
            f"{pw.capitalize()} {fix.qa_text}. That changed the game from a risky crossing into a safer pirate challenge."
        ),
        (
            "What lesson did the captain learn?",
            f"{captain.label} learned that bravery is not the same as rushing. {captain.pronoun().capitalize()} learned to follow the criterium, listen to warnings, and ask for help."
        ),
        (
            "How did the story end?",
            f"The children repeated the careful rule together and crossed to the treasure step by step. The ending shows that the game stayed exciting after they changed how they played."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["bridge_cfg"].tags) | set(f["shortcut_cfg"].tags) | set(f["fix_cfg"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.stable:
            bits.append("stable=True")
        if e.risky:
            bits.append("risky=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(B, S) :- unstable(B).
hazard(B, S) :- risky(S).
sensible(F) :- fix(F), sense(F, V), sense_min(M), V >= M.
valid(T, B, S) :- theme(T), bridge(B), shortcut(S), hazard(B, S).

severity(V + R) :- chosen_bridge(B), wobble(B, V), chosen_shortcut(S), rash(S, R).
controlled :- chosen_fix(F), steadiness(F, P), severity(SV), P >= SV.
outcome(learned) :- controlled.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for bid, bridge in BRIDGES.items():
        lines.append(asp.fact("bridge", bid))
        lines.append(asp.fact("wobble", bid, bridge.wobble))
        if not bridge.stable:
            lines.append(asp.fact("unstable", bid))
    for sid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        lines.append(asp.fact("rash", sid, shortcut.rash))
        if shortcut.risky:
            lines.append(asp.fact("risky", sid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("steadiness", fid, fix.steadiness))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join(
        [
            asp.fact("chosen_bridge", params.bridge),
            asp.fact("chosen_shortcut", params.shortcut),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def outcome_of(params: StoryParams) -> str:
    return "learned" if is_controlled(BRIDGES[params.bridge], SHORTCUTS[params.shortcut], FIXES[params.fix]) else "?"


def smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "criterium" not in sample.story or "cheek" not in sample.story:
        raise StoryError("Smoke test failed: generated story missing expected seed words.")
    emit(sample, trace=False, qa=False)


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {f.id for f in sensible_fixes()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible fixes match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if params.fix in FIXES and FIXES[params.fix].sense >= SENSE_MIN:
            if asp_outcome(params) != outcome_of(params):
                bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_generate()
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a pirate-play bridge lesson with criterium, cheek, repetition, and dialogue."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--bridge", choices=BRIDGES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bridge and args.shortcut:
        bridge = BRIDGES[args.bridge]
        shortcut = SHORTCUTS[args.shortcut]
        if not hazard_at_risk(bridge, shortcut):
            raise StoryError(explain_rejection(bridge, shortcut))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.bridge is None or c[1] == args.bridge)
        and (args.shortcut is None or c[2] == args.shortcut)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, bridge_id, shortcut_id = rng.choice(sorted(combos))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    captain_name, captain_gender = _pick_child(rng)
    mate_name, mate_gender = _pick_child(rng, avoid=captain_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme_id,
        bridge=bridge_id,
        shortcut=shortcut_id,
        fix=fix_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in [("theme", THEMES), ("bridge", BRIDGES), ("shortcut", SHORTCUTS), ("fix", FIXES)]:
        key = getattr(params, field_name)
        if key not in registry:
            raise StoryError(f"(Invalid {field_name}: {key})")
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if not hazard_at_risk(BRIDGES[params.bridge], SHORTCUTS[params.shortcut]):
        raise StoryError(explain_rejection(BRIDGES[params.bridge], SHORTCUTS[params.shortcut]))

    world = tell(
        theme=THEMES[params.theme],
        bridge=BRIDGES[params.bridge],
        shortcut=SHORTCUTS[params.shortcut],
        fix=FIXES[params.fix],
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
    )

    # Render using display names, never internal ids.
    story = world.render().replace("captain", params.captain_name).replace("mate", params.mate_name)
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, bridge, shortcut) combos:\n")
        for theme, bridge, shortcut in combos:
            print(f"  {theme:8} {bridge:12} {shortcut}")
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
            header = f"### {p.captain_name} & {p.mate_name}: {p.bridge} + {p.shortcut} ({p.theme})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
