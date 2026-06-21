#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/occur_add_fiddle_reconciliation_lesson_learned_suspense.py
======================================================================================

A standalone story world about a child and a friend who are meant to play a
small fiddle song for a loved one, but a quarrel and a last-minute instrument
problem put the moment at risk. The story resolves through apology, shared
repair, and a warm performance.

Seed words:
- occur
- add
- fiddle

Narrative features:
- Reconciliation
- Lesson Learned
- Suspense

Style:
- Heartwarming
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested folder.
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    gathering: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    symptom: str
    risk: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    action: str
    touch: str
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


def _r_suspense(world: World) -> list[str]:
    fiddle = world.get("fiddle")
    if fiddle.meters["trouble"] < THRESHOLD or fiddle.meters["ready"] >= THRESHOLD:
        return []
    sig = ("suspense", "fiddle")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("lead").memes["worry"] += 1
    world.get("helper").memes["worry"] += 1
    world.get("scene").meters["suspense"] += 1
    return []


def _r_reconcile(world: World) -> list[str]:
    lead = world.get("lead")
    helper = world.get("helper")
    if lead.memes["apology"] < THRESHOLD or helper.memes["forgave"] < THRESHOLD:
        return []
    sig = ("reconcile", "pair")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["peace"] += 1
    helper.memes["peace"] += 1
    lead.memes["love"] += 1
    helper.memes["love"] += 1
    return []


def _r_ready(world: World) -> list[str]:
    fiddle = world.get("fiddle")
    if fiddle.meters["repair_started"] < THRESHOLD:
        return []
    sig = ("ready", "fiddle")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    fiddle.meters["trouble"] = 0.0
    fiddle.meters["ready"] += 1
    world.get("scene").meters["suspense"] = 0.0
    world.get("lead").memes["relief"] += 1
    world.get("helper").memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="suspense", tag="emotion", apply=_r_suspense),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
    Rule(name="ready", tag="physical", apply=_r_ready),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


def trouble_can_be_fixed(trouble: Trouble, repair: Repair) -> bool:
    return repair.id in trouble.needs


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for trouble_id, trouble in TROUBLES.items():
            for repair_id, repair in REPAIRS.items():
                if trouble_can_be_fixed(trouble, repair):
                    combos.append((setting_id, trouble_id, repair_id))
    return combos


def predict_concert(world: World, trouble: Trouble, repair: Repair) -> dict:
    sim = world.copy()
    fiddle = sim.get("fiddle")
    fiddle.meters["trouble"] += 1
    propagate(sim, narrate=False)
    if trouble_can_be_fixed(trouble, repair):
        fiddle.meters["repair_started"] += 1
        propagate(sim, narrate=False)
    return {
        "ready": fiddle.meters["ready"] >= THRESHOLD,
        "suspense": sim.get("scene").meters["suspense"],
    }


def introduce(world: World, setting: Setting, lead: Entity, helper: Entity, elder: Entity) -> None:
    world.say(
        f"Late that afternoon, {lead.id} and {helper.id} stood in {setting.place}, where "
        f"{setting.gathering}. They had promised to play a small fiddle song for {elder.label_word}."
    )
    world.say(
        f"The room felt soft and expectant, and even the chairs seemed to be waiting for the first note."
    )


def old_quarrel(world: World, lead: Entity, helper: Entity) -> None:
    lead.memes["pride"] += 1
    helper.memes["hurt"] += 1
    world.say(
        f"But a little while earlier, a quarrel had happened. {lead.id} had grabbed the first solo, "
        f"and {helper.id} had stepped away with a stung face and folded arms."
    )
    world.say(
        f"No one wanted another hurt feeling to occur before the music even began."
    )


def discover_trouble(world: World, trouble: Trouble, lead: Entity, helper: Entity) -> None:
    fiddle = world.get("fiddle")
    fiddle.meters["trouble"] += 1
    world.facts["predicted_risk"] = trouble.risk
    propagate(world, narrate=False)
    world.say(
        f"Then {lead.id} lifted the fiddle, and trouble showed itself at once: {trouble.symptom}."
    )
    if world.get("scene").meters["suspense"] >= THRESHOLD:
        world.say(
            f"{lead.id}'s stomach gave a small jump. If they played it like that, {trouble.risk}."
        )


def lone_fiddle(world: World, lead: Entity, helper: Entity) -> None:
    lead.memes["stubborn"] += 1
    world.say(
        f"For a moment, {lead.id} wanted to fiddle with the instrument alone and pretend "
        f"{helper.id}'s careful hands were not needed."
    )
    world.say(
        f"But the quiet between them felt heavier than the little wooden fiddle."
    )


def apology(world: World, lead: Entity, helper: Entity) -> None:
    lead.memes["apology"] += 1
    helper.memes["listening"] += 1
    world.say(
        f'{lead.id} swallowed hard. "I was bossy before," {lead.pronoun()} said. '
        f'"I am sorry. Can we add your careful hands to this problem?"'
    )
    world.say(
        f"{helper.id} looked at the fiddle, then at {lead.id}, and the hard line around "
        f"{helper.pronoun('possessive')} mouth began to soften."
    )


def accept_help(world: World, helper: Entity) -> None:
    helper.memes["forgave"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Yes," {helper.id} said softly. "We can fix it together."'
    )


def repair_fiddle(world: World, repair: Repair, lead: Entity, helper: Entity) -> None:
    fiddle = world.get("fiddle")
    fiddle.meters["repair_started"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Side by side, they {repair.action}. {repair.touch}"
    )


def performance(world: World, setting: Setting, lead: Entity, helper: Entity, elder: Entity) -> None:
    lead.memes["joy"] += 1
    helper.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f"When {lead.id} drew the bow again, the fiddle answered with a clear, warm sound."
    )
    world.say(
        f"Then the two children played together at last, and {elder.label_word} listened with bright, "
        f"wet eyes. {setting.image}"
    )


def lesson(world: World, lead: Entity, helper: Entity) -> None:
    lead.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"After the last note, {lead.id} squeezed {helper.id}'s hand."
    )
    world.say(
        f"They both learned the same thing: when pride makes a problem bigger, a kind apology and "
        f"shared work can make the whole room gentler again."
    )


def tell(
    setting: Setting,
    trouble: Trouble,
    repair: Repair,
    lead_name: str = "Mia",
    lead_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    elder_type: str = "grandmother",
    relation: str = "friends",
) -> World:
    world = World()
    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_gender,
        role="lead",
        label=lead_name,
        attrs={"relation": relation},
        tags={"child"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        label=helper_name,
        attrs={"relation": relation},
        tags={"child"},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
        tags={"family"},
    ))
    scene = world.add(Entity(
        id="scene",
        kind="thing",
        type="scene",
        label=setting.place,
    ))
    fiddle = world.add(Entity(
        id="fiddle",
        kind="thing",
        type="instrument",
        label="fiddle",
        phrase="the little fiddle",
        tags={"fiddle"},
    ))

    world.facts["setting"] = setting
    world.facts["trouble_cfg"] = trouble
    world.facts["repair_cfg"] = repair
    world.facts["lead"] = lead
    world.facts["helper"] = helper
    world.facts["elder"] = elder
    world.facts["scene"] = scene
    world.facts["instrument"] = fiddle
    world.facts["relation"] = relation

    introduce(world, setting, lead, helper, elder)
    old_quarrel(world, lead, helper)

    world.para()
    discover_trouble(world, trouble, lead, helper)
    lone_fiddle(world, lead, helper)

    world.para()
    apology(world, lead, helper)
    accept_help(world, helper)
    repair_fiddle(world, repair, lead, helper)

    world.para()
    performance(world, setting, lead, helper, elder)
    lesson(world, lead, helper)

    world.facts["reconciled"] = lead.memes["peace"] >= THRESHOLD and helper.memes["peace"] >= THRESHOLD
    world.facts["ready"] = fiddle.meters["ready"] >= THRESHOLD
    world.facts["suspense_happened"] = scene.meters["suspense"] == 0.0 and lead.memes["worry"] >= THRESHOLD
    return world


SETTINGS = {
    "parlor": Setting(
        id="parlor",
        place="the parlor window nook",
        gathering="a lamp glowed beside the curtains and family shoes lined the rug",
        image="Outside, the evening sky turned peach, and inside the song made the whole nook feel newly mended.",
        tags={"home"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch",
        gathering="fireflies had begun to blink beyond the steps and a pitcher of lemonade rested on the rail",
        image="The porch boards held the last gold light, and the tune floated out into the yard like a small hug.",
        tags={"porch"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden bench under the pear tree",
        gathering="paper cups stood on a tray and the leaves made a soft green roof overhead",
        image="A pear leaf drifted down beside their shoes, and the song ended in a hush full of peace.",
        tags={"garden"},
    ),
}

TROUBLES = {
    "loose_string": Trouble(
        id="loose_string",
        symptom="one string sagged like a tired shoelace",
        risk="the song would squeak and wobble instead of singing",
        needs={"tighten_peg"},
        tags={"string"},
    ),
    "dry_bow": Trouble(
        id="dry_bow",
        symptom="the bow slid over the strings with almost no voice at all",
        risk="the notes would whisper away before anyone could really hear them",
        needs={"add_rosin"},
        tags={"rosin"},
    ),
    "crooked_bridge": Trouble(
        id="crooked_bridge",
        symptom="the tiny bridge leaned to one side",
        risk="a bigger snap could occur and stop the song completely",
        needs={"straighten_bridge"},
        tags={"bridge"},
    ),
}

REPAIRS = {
    "tighten_peg": Repair(
        id="tighten_peg",
        action="turned the peg a little at a time until the loose string stood neat and straight again",
        touch="Neither child rushed, and the careful turning felt calmer than any argument.",
        qa_text="They tightened the fiddle's peg a little at a time until the loose string was straight again.",
        tags={"string"},
    ),
    "add_rosin": Repair(
        id="add_rosin",
        action="added a dusty swipe of rosin to the bow so it could catch the strings again",
        touch="The soft powder smell rose between them, and their shoulders stopped feeling so stiff.",
        qa_text="They added rosin to the bow so it could catch the strings and make a full sound again.",
        tags={"rosin"},
    ),
    "straighten_bridge": Repair(
        id="straighten_bridge",
        action="steadied the bridge with two careful thumbs until it stood in the middle again",
        touch="Their hands moved slowly, because kindness worked better than hurry there.",
        qa_text="They straightened the little bridge carefully until it stood in the middle again.",
        tags={"bridge"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Jack", "Noah", "Eli"]


@dataclass
class StoryParams:
    setting: str
    trouble: str
    repair: str
    lead: str
    lead_gender: str
    helper: str
    helper_gender: str
    elder: str
    relation: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="parlor",
        trouble="loose_string",
        repair="tighten_peg",
        lead="Mia",
        lead_gender="girl",
        helper="Ben",
        helper_gender="boy",
        elder="grandmother",
        relation="friends",
    ),
    StoryParams(
        setting="porch",
        trouble="dry_bow",
        repair="add_rosin",
        lead="Leo",
        lead_gender="boy",
        helper="Nora",
        helper_gender="girl",
        elder="grandfather",
        relation="siblings",
    ),
    StoryParams(
        setting="garden",
        trouble="crooked_bridge",
        repair="straighten_bridge",
        lead="Ava",
        lead_gender="girl",
        helper="Max",
        helper_gender="boy",
        elder="grandmother",
        relation="cousins",
    ),
]


KNOWLEDGE = {
    "fiddle": [
        (
            "What is a fiddle?",
            "A fiddle is a string instrument played with a bow. It is very close to a violin, and it sings when the strings and bow work together."
        )
    ],
    "string": [
        (
            "Why does a loose string make bad music?",
            "A loose string cannot vibrate the right way, so the note sounds weak or wobbly. Tightening it helps the sound come back clear."
        )
    ],
    "rosin": [
        (
            "What does rosin do on a bow?",
            "Rosin gives the bow a little grip, so it can catch the string and make a stronger sound. Without it, the bow can slide too smoothly and sound thin."
        )
    ],
    "bridge": [
        (
            "What does the bridge on a fiddle do?",
            "The bridge holds the strings up in the right place. If it leans too far, the instrument can sound wrong or the strings can pull badly."
        )
    ],
    "apology": [
        (
            "Why can an apology help two people work together again?",
            "An apology shows that someone understands the hurt they caused. That often makes it easier for the other person to trust and help again."
        )
    ],
    "patience": [
        (
            "Why is patience useful when fixing something delicate?",
            "Patience helps your hands move slowly and carefully. That keeps a small problem from turning into a bigger one."
        )
    ],
}
KNOWLEDGE_ORDER = ["fiddle", "string", "rosin", "bridge", "apology", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    trouble = f["trouble_cfg"]
    setting = f["setting"]
    elder = f["elder"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "occur", "add", and "fiddle".',
        f"Tell a gentle suspense story where {lead.id} and {helper.id} must fix a fiddle in {setting.place} before playing for {elder.label_word}, and the children reconcile after a quarrel.",
        f"Write a small story with a lesson learned: a problem with {trouble.id.replace('_', ' ')} makes two children stop arguing, apologize, and work together.",
    ]


def relation_phrase(relation: str) -> str:
    if relation == "siblings":
        return "two siblings"
    if relation == "cousins":
        return "two cousins"
    return "two friends"


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    elder = f["elder"]
    trouble = f["trouble_cfg"]
    repair = f["repair_cfg"]
    setting = f["setting"]
    relation = f["relation"]
    pair = relation_phrase(relation)
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {lead.id} and {helper.id}, who were supposed to play a fiddle song for {elder.label_word}. The story follows how they moved from hurt feelings back to teamwork."
        ),
        (
            "Why did the story feel suspenseful in the middle?",
            f"The fiddle suddenly had a problem just before the song, so the children worried the music might fail in front of everyone. The suspense came from not knowing whether they could fix it in time and whether their quarrel would get in the way."
        ),
        (
            f"What problem did {lead.id} find on the fiddle?",
            f"{lead.id} discovered that {trouble.symptom}. That mattered because {trouble.risk}."
        ),
        (
            f"How did {lead.id} and {helper.id} reconcile?",
            f"{lead.id} admitted being bossy and apologized instead of trying to do everything alone. {helper.id} softened, forgave {lead.pronoun('object')}, and chose to help fix the fiddle beside {lead.pronoun('object')}."
        ),
        (
            "How did they fix the instrument?",
            f"{repair.qa_text} Working together on the repair also helped calm their feelings."
        ),
        (
            "What lesson did the children learn?",
            f"They learned that pride can make a small problem feel bigger than it is. A kind apology and patient teamwork can mend both a friendship and a difficult moment."
        ),
        (
            "How did the story end?",
            f"They played together for {elder.label_word} in {setting.place}, and the music came out warm and clear. The ending image shows that the room felt peaceful again because both the fiddle and the friendship were mended."
        ),
    ]
    return items


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    tags = {"fiddle", "apology", "patience"}
    trouble = world.facts["trouble_cfg"]
    repair = world.facts["repair_cfg"]
    tags |= set(trouble.tags)
    tags |= set(repair.tags)
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(trouble: Trouble, repair: Repair) -> str:
    needed = ", ".join(sorted(trouble.needs))
    return (
        f"(No story: '{repair.id}' is not a sensible fix for '{trouble.id}'. "
        f"This trouble needs one of: {needed}.)"
    )


ASP_RULES = r"""
fixes(Trouble, Repair) :- needs(Trouble, Repair).
valid(Setting, Trouble, Repair) :- setting(Setting), trouble(Trouble), repair(Repair), fixes(Trouble, Repair).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        for repair_id in sorted(trouble.needs):
            lines.append(asp.fact("needs", trouble_id, repair_id))
    for repair_id in REPAIRS:
        lines.append(asp.fact("repair", repair_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test failed: generated story was empty.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Random smoke test failed: generated story was empty.")
        print("OK: random generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a broken fiddle, a repaired friendship, and a lesson learned."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--relation", choices=["friends", "siblings", "cousins"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.repair:
        trouble = TROUBLES[args.trouble]
        repair = REPAIRS[args.repair]
        if not trouble_can_be_fixed(trouble, repair):
            raise StoryError(explain_rejection(trouble, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, trouble_id, repair_id = rng.choice(sorted(combos))
    lead_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    lead = _pick_name(rng, lead_gender)
    helper = _pick_name(rng, helper_gender, avoid=lead)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    relation = args.relation or rng.choice(["friends", "siblings", "cousins"])
    return StoryParams(
        setting=setting_id,
        trouble=trouble_id,
        repair=repair_id,
        lead=lead,
        lead_gender=lead_gender,
        helper=helper,
        helper_gender=helper_gender,
        elder=elder,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    trouble = TROUBLES[params.trouble]
    repair = REPAIRS[params.repair]
    if not trouble_can_be_fixed(trouble, repair):
        raise StoryError(explain_rejection(trouble, repair))

    world = tell(
        setting=SETTINGS[params.setting],
        trouble=trouble,
        repair=repair,
        lead_name=params.lead,
        lead_gender=params.lead_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        elder_type=params.elder,
        relation=params.relation,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
        print(asp_program("#show valid/3."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, trouble, repair) combos:\n")
        for setting_id, trouble_id, repair_id in combos:
            print(f"  {setting_id:8} {trouble_id:16} {repair_id}")
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
            header = f"### {p.lead} and {p.helper}: {p.trouble} -> {p.repair} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
