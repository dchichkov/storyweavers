#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sophisticated_deceased_harrow_sound_effects_rhyming_story.py
========================================================================================

A standalone story world for a rhyming, sound-rich tale about a child who hears
a spooky racket in the yard, worries about it, and then learns the noise has an
ordinary cause. Every story includes the words "sophisticated", "deceased", and
"harrow" naturally inside the domain itself.

The core premise:
- a child hears wind making an old farm tool clatter
- the tool once belonged to a deceased relative or neighbor
- the noise feels spooky at first
- a calm helper investigates
- the helper either secures the rattling parts or moves the tool to a safer,
  quieter place
- the ending image proves the child is no longer afraid

The prose aims for a simple rhyming-story feel with sound effects woven into the
beats: clink, clank, creak, whirr, tap, ping.

Run it
------
python storyworlds/worlds/gpt-5.4/sophisticated_deceased_harrow_sound_effects_rhyming_story.py
python storyworlds/worlds/gpt-5.4/sophisticated_deceased_harrow_sound_effects_rhyming_story.py --source barn_harrow --fix ribbon
python storyworlds/worlds/gpt-5.4/sophisticated_deceased_harrow_sound_effects_rhyming_story.py --source stone_statue
python storyworlds/worlds/gpt-5.4/sophisticated_deceased_harrow_sound_effects_rhyming_story.py --all
python storyworlds/worlds/gpt-5.4/sophisticated_deceased_harrow_sound_effects_rhyming_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/sophisticated_deceased_harrow_sound_effects_rhyming_story.py --verify
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
# This file lives one level deeper (storyworlds/worlds/gpt-5.4/...), so we add
# the package dir (storyworlds/) to sys.path.
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
    loose: bool = False
    wind_moved: bool = False
    portable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "grandmother", "woman"}
        male = {"boy", "father", "uncle", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    ground: str
    tags: set[str] = field(default_factory=set)


@dataclass
class NoiseSource:
    id: str
    label: str
    phrase: str
    relation_phrase: str
    sound: str
    onomatopoeia: str
    loose_part: str
    fixable_by: set[str] = field(default_factory=set)
    movable_by: set[str] = field(default_factory=set)
    portable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    action_text: str
    qa_text: str
    requires_portable: bool = False
    secures: bool = False
    softens: bool = False
    moves_inside: bool = False
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wind_noise(world: World) -> list[str]:
    out: list[str] = []
    weather = world.get("weather")
    source = world.get("source")
    if weather.meters["wind"] < THRESHOLD or not source.loose:
        return out
    sig = ("wind_noise", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["noise"] += 1
    for ent in world.entities.values():
        if ent.role == "child":
            ent.memes["fear"] += 1
            ent.memes["wonder"] += 1
    out.append("__noise__")
    return out


def _r_explain(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    helper = world.get("helper")
    child = world.get("child")
    if helper.memes["investigated"] < THRESHOLD or source.meters["noise"] < THRESHOLD:
        return out
    sig = ("explain", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["understanding"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    out.append("__understood__")
    return out


CAUSAL_RULES = [
    Rule(name="wind_noise", tag="physical", apply=_r_wind_noise),
    Rule(name="explain", tag="social", apply=_r_explain),
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


def valid_fix_for_source(source: NoiseSource, fix: Fix) -> bool:
    if fix.id in source.fixable_by:
        return True
    if fix.id in source.movable_by and not fix.requires_portable:
        return True
    if fix.id in source.movable_by and fix.requires_portable and source.portable:
        return True
    return False


def explain_invalid(source: NoiseSource, fix: Fix) -> str:
    if fix.requires_portable and not source.portable:
        return (
            f"(No story: {source.label} is too big to carry inside, so '{fix.id}' "
            f"is not a believable fix. Choose a way to secure or soften its loose parts instead.)"
        )
    return (
        f"(No story: '{fix.id}' does not sensibly solve the noise made by {source.label}. "
        f"Pick a fix that matches the source of the clatter.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for source_id, source in SOURCES.items():
            for fix_id, fix in FIXES.items():
                if valid_fix_for_source(source, fix):
                    combos.append((setting_id, source_id, fix_id))
    return combos


def predict_noise(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "noisy": sim.get("source").meters["noise"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def introduce(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"In {world.setting.place}, beneath {world.setting.sky}, {child.id} walked with "
        f"{child.pronoun('possessive')} {helper.label_word} by {world.setting.ground} side."
    )
    world.say(
        f"{child.id} liked tidy, clever things and called the old yard rather sophisticated, "
        f"for every gate and pail seemed to glitter and hide."
    )


def reveal_source(world: World, child: Entity, source_cfg: NoiseSource) -> None:
    world.say(
        f"Near the hedge stood {source_cfg.phrase}, a harrow with teeth in a crooked row. "
        f"It had belonged to {source_cfg.relation_phrase}, and still the child liked to know."
    )
    world.say(
        f"The grown-ups said the dear old owner was deceased, gone years before with a kind goodbye, "
        f"yet the tool stayed in the garden under the open sky."
    )


def wind_rises(world: World, source_cfg: NoiseSource) -> None:
    world.say(
        f"Then the evening wind came tiptoe-thin, and the old {source_cfg.label} began to sing: "
        f'"{source_cfg.onomatopoeia}! {source_cfg.sound}!" went the {source_cfg.loose_part} as it shook on its string.'
    )


def fear_beat(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} froze with a wiggle and a swallow. \"Oh my, oh dear, what can that be?\" "
        f'"It sounds like a whispery creature calling to me!"'
    )


def helper_listens(world: World, helper: Entity, child: Entity, source_cfg: NoiseSource) -> None:
    helper.memes["investigated"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {helper.label_word.capitalize()} listened low and slow. "
        f"\"Not every odd sound means fright,\" {helper.pronoun()} said. "
        f"\"Sometimes wind taps old metal instead of a ghost in the night.\""
    )
    world.say(
        f"{helper.label_word.capitalize()} held the wobbling {source_cfg.loose_part} and watched it sway, "
        f"then showed {child.id} how the breeze made the rattly play."
    )


def perform_fix(world: World, helper: Entity, child: Entity, source_cfg: NoiseSource, fix: Fix) -> None:
    source = world.get("source")
    if fix.secures or fix.softens or fix.moves_inside:
        source.loose = False
    if fix.moves_inside:
        source.attrs["inside"] = True
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    child.memes["fear"] = 0.0
    child.memes["understanding"] += 1
    helper.memes["care"] += 1
    source.meters["noise"] = 0.0
    world.say(
        f"So {helper.label_word} {fix.action_text}. Soon the racket lost its might; "
        f'no more "{source_cfg.onomatopoeia}!" startled the garden light.'
    )


def ending(world: World, child: Entity, source_cfg: NoiseSource, fix: Fix) -> None:
    if fix.moves_inside:
        image = "inside the shed, quiet and dry"
    elif fix.softens:
        image = "by the gate, gentle and shy"
    else:
        image = "in the dusk, steady and still"
    world.say(
        f"{child.id} laughed at last. \"So that was all? Just wind with a wobbly will!\" "
        f"{child.pronoun().capitalize()} touched the old harrow {image}."
    )
    world.say(
        f"And home they went with lighter feet, no monster cry to borrow. "
        f"The night said hush instead of hush-a-boo, and even the sophisticated stars looked true."
    )


def tell(
    setting: Setting,
    source_cfg: NoiseSource,
    fix: Fix,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_type: str = "grandmother",
) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", label=child_name))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper"))
    weather = world.add(Entity(id="weather", type="weather", label="wind"))
    weather.meters["wind"] = 1.0
    source = world.add(
        Entity(
            id="source",
            type="harrow",
            label=source_cfg.label,
            phrase=source_cfg.phrase,
            role="source",
            loose=True,
            wind_moved=True,
            portable=source_cfg.portable,
            tags=set(source_cfg.tags),
        )
    )

    introduce(world, child, helper)
    reveal_source(world, child, source_cfg)

    world.para()
    wind_rises(world, source_cfg)
    propagate(world, narrate=False)
    fear_beat(world, child)

    world.para()
    helper_listens(world, helper, child, source_cfg)
    perform_fix(world, helper, child, source_cfg, fix)

    world.para()
    ending(world, child, source_cfg, fix)

    world.facts.update(
        child=child,
        helper=helper,
        source_cfg=source_cfg,
        source=source,
        setting=setting,
        fix=fix,
        noisy=True,
        solved=not source.loose,
        initial_fear=True,
    )
    return world


SETTINGS = {
    "moon_garden": Setting(
        id="moon_garden",
        place="the moonlit garden",
        sky="a pearly sky",
        ground="the mossy path",
        tags={"garden", "night"},
    ),
    "orchard_lane": Setting(
        id="orchard_lane",
        place="the old orchard lane",
        sky="a plum-colored sky",
        ground="the leaf-strewn lane",
        tags={"orchard", "night"},
    ),
    "pumpkin_yard": Setting(
        id="pumpkin_yard",
        place="the pumpkin yard",
        sky="a silver sky",
        ground="the crunchy straw path",
        tags={"yard", "night"},
    ),
}

SOURCES = {
    "barn_harrow": NoiseSource(
        id="barn_harrow",
        label="barn harrow",
        phrase="a rusty barn harrow leaning beside the fence",
        relation_phrase="the deceased great-grandfather",
        sound="clink-clank",
        onomatopoeia="CLINK-CLANK",
        loose_part="one loose chain",
        fixable_by={"ribbon", "wire"},
        movable_by=set(),
        portable=False,
        tags={"harrow", "wind", "metal"},
    ),
    "porch_harrow": NoiseSource(
        id="porch_harrow",
        label="porch harrow",
        phrase="a small hand harrow hanging near the porch post",
        relation_phrase="the deceased neighbor Mr. Vale",
        sound="tap-tap-ping",
        onomatopoeia="TAP-TAP-PING",
        loose_part="its dangling teeth",
        fixable_by={"ribbon", "wire"},
        movable_by={"move_shed"},
        portable=True,
        tags={"harrow", "wind", "metal"},
    ),
    "wagon_harrow": NoiseSource(
        id="wagon_harrow",
        label="wagon harrow",
        phrase="an old seed-wagon harrow resting by the lane",
        relation_phrase="the deceased Aunt June",
        sound="creak-whirr-clink",
        onomatopoeia="CREAK-WHIRR-CLINK",
        loose_part="a swinging wheel strap",
        fixable_by={"wire"},
        movable_by=set(),
        portable=False,
        tags={"harrow", "wind", "wheel"},
    ),
    "stone_statue": NoiseSource(
        id="stone_statue",
        label="stone statue",
        phrase="a heavy stone rabbit statue by the herb bed",
        relation_phrase="the deceased gardener",
        sound="nothing at all",
        onomatopoeia="...",
        loose_part="nothing",
        fixable_by=set(),
        movable_by=set(),
        portable=False,
        tags={"statue"},
    ),
}

FIXES = {
    "ribbon": Fix(
        id="ribbon",
        label="a soft ribbon",
        action_text="wrapped a soft ribbon around the loose part and tied it snug",
        qa_text="tied the loose rattling part with a soft ribbon",
        secures=True,
        softens=True,
        tags={"ribbon", "fix"},
    ),
    "wire": Fix(
        id="wire",
        label="garden wire",
        action_text="looped garden wire through the shaky part and fastened it tight",
        qa_text="fastened the shaky part with garden wire",
        secures=True,
        tags={"wire", "fix"},
    ),
    "move_shed": Fix(
        id="move_shed",
        label="moving it into the shed",
        action_text="carried the small tool into the shed where the wind could not rattle it",
        qa_text="moved the small tool into the shed",
        requires_portable=True,
        moves_inside=True,
        tags={"shed", "fix"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Poppy", "Tessa", "Wren"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Jasper", "Bram", "Ned"]


@dataclass
class StoryParams:
    setting: str
    source: str
    fix: str
    child_name: str
    child_type: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="moon_garden",
        source="barn_harrow",
        fix="ribbon",
        child_name="Mina",
        child_type="girl",
        helper_type="grandmother",
    ),
    StoryParams(
        setting="orchard_lane",
        source="porch_harrow",
        fix="move_shed",
        child_name="Owen",
        child_type="boy",
        helper_type="uncle",
    ),
    StoryParams(
        setting="pumpkin_yard",
        source="wagon_harrow",
        fix="wire",
        child_name="Poppy",
        child_type="girl",
        helper_type="grandfather",
    ),
]


KNOWLEDGE = {
    "harrow": [
        (
            "What is a harrow?",
            "A harrow is a farm tool with metal teeth or parts that scratch and break up the ground. Old harrows can rattle if they are left loose in the wind."
        )
    ],
    "deceased": [
        (
            "What does deceased mean?",
            "Deceased is a gentle word that means someone has died. It is often used respectfully when talking about a person from the past."
        )
    ],
    "wind": [
        (
            "Why do old metal things make noise in the wind?",
            "Wind can push loose parts so they bump and shake against each other. That makes clinks, creaks, and rattles."
        )
    ],
    "ribbon": [
        (
            "How can a ribbon make something quieter?",
            "A soft ribbon can hold a loose part still and also soften its bumps. When the part moves less, it makes less noise."
        )
    ],
    "wire": [
        (
            "What does wire do when something is shaky?",
            "Wire can hold a loose piece tightly in place. If the piece cannot swing and bang around, the clatter stops."
        )
    ],
    "shed": [
        (
            "Why would moving a tool into a shed help?",
            "A shed keeps wind off the tool and gives it a safer place to rest. Without the wind pushing it, the rattling sound can stop."
        )
    ],
}
KNOWLEDGE_ORDER = ["harrow", "deceased", "wind", "ribbon", "wire", "shed"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    source_cfg = f["source_cfg"]
    fix = f["fix"]
    return [
        'Write a rhyming story for a 3-to-5-year-old that includes the words "sophisticated," "deceased," and "harrow," with clear sound effects.',
        f"Tell a gentle spooky-sounding rhyme where {child.id} hears {source_cfg.label} go {source_cfg.onomatopoeia.lower()}, thinks the noise is strange, and then learns what really made it.",
        f"Write a short sound-effects story in rhyme where an old harrow once owned by {source_cfg.relation_phrase} is made quiet by {fix.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    source_cfg = f["source_cfg"]
    fix = f["fix"]
    setting = f["setting"]
    hw = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {hw} in {setting.place}. They were near an old harrow that began to make a noisy fuss."
        ),
        (
            "What scared the child at first?",
            f"{source_cfg.phrase.capitalize()} made a sound like {source_cfg.sound}, so {child.id} thought something spooky might be there. The sudden noise came when the wind shook {source_cfg.loose_part}."
        ),
        (
            "Why did the story use the word deceased?",
            f"The harrow had belonged to {source_cfg.relation_phrase}, and that person was deceased. The word helped explain that the tool came from someone long ago."
        ),
        (
            f"How did {child.id}'s {hw} solve the problem?",
            f"{helper.label_word.capitalize()} {fix.qa_text}. That stopped the loose part from rattling so the scary sound went away."
        ),
        (
            f"How did {child.id} feel at the end?",
            f"{child.id} felt relieved and cheerful instead of frightened. Once {child.pronoun()} understood the wind was the cause, the old garden felt friendly again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"harrow", "deceased", "wind"}
    fix = world.facts["fix"]
    if fix.id == "ribbon":
        tags.add("ribbon")
    elif fix.id == "wire":
        tags.add("wire")
    elif fix.id == "move_shed":
        tags.add("shed")
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
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if entity.loose:
            bits.append("loose=True")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if entity.role:
            bits.append(f"role={entity.role}")
        lines.append(f"  {entity.id:8} ({entity.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, Src, Fx) :- setting(S), source(Src), fix(Fx), solves(Src, Fx), not impossible(Src, Fx).
impossible(Src, Fx) :- portable_required(Fx), not portable(Src).

chosen_valid :- chosen_setting(S), chosen_source(Src), chosen_fix(Fx), valid(S, Src, Fx).
outcome(quieted) :- chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        if source.portable:
            lines.append(asp.fact("portable", source_id))
        for fix_id in sorted(source.fixable_by | source.movable_by):
            lines.append(asp.fact("solves", source_id, fix_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        if fix.requires_portable:
            lines.append(asp.fact("portable_required", fix_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for params in cases:
        py = "quieted" if (params.setting, params.source, params.fix) in python_set else "?"
        cl = asp_outcome(params)
        if py != cl:
            rc = 1
            print(f"MISMATCH in outcome for {params}: python={py} clingo={cl}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming sound-effects story world about a child, an old harrow, and a spooky noise that gets explained."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("--child-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible scenarios from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{args.source}'.)")
    if args.fix and args.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{args.fix}'.)")

    if args.source and args.fix:
        source = SOURCES[args.source]
        fix = FIXES[args.fix]
        if not valid_fix_for_source(source, fix):
            raise StoryError(explain_invalid(source, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.source is None or combo[1] == args.source)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, source_id, fix_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)

    return StoryParams(
        setting=setting_id,
        source=source_id,
        fix=fix_id,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{params.fix}'.)")

    source_cfg = SOURCES[params.source]
    fix = FIXES[params.fix]
    if not valid_fix_for_source(source_cfg, fix):
        raise StoryError(explain_invalid(source_cfg, fix))

    world = tell(
        SETTINGS[params.setting],
        source_cfg,
        fix,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, source, fix) combos:\n")
        for setting_id, source_id, fix_id in combos:
            print(f"  {setting_id:12} {source_id:12} {fix_id}")
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
            header = f"### {p.child_name}: {p.source} at {p.setting} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
