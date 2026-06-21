#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/photogenic_dick_repetition_rhyme_magic_fairy_tale.py
================================================================================

A standalone story world for a tiny fairy-tale domain built from the seed words
"photogenic" and "dick". The stories are about a child named Dick who hopes to
stand before a magic mirror for a moonlit portrait, but one concrete trouble
keeps the portrait from shining true. A helper uses a fitting charm -- spoken in
repetition and rhyme -- to fix the real problem, and only then can the mirror
show the ending image.

The domain is intentionally narrow and state-driven:

    desire for portrait + trouble blocks reflection
    helper chooses a charm suited to the trouble's material
    fitting charm removes the trouble and lifts hope
    magic mirror then grants a bright, lasting portrait

The reasonableness gate refuses mismatched fixes. A comb cannot wash off mud; a
dew-cloth cannot quiet a shaking pose. The story therefore depends on live world
state rather than noun swapping.

Run it
------
    python storyworlds/worlds/gpt-5.4/photogenic_dick_repetition_rhyme_magic_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/photogenic_dick_repetition_rhyme_magic_fairy_tale.py --trouble mud --charm dew_cloth
    python storyworlds/worlds/gpt-5.4/photogenic_dick_repetition_rhyme_magic_fairy_tale.py --trouble mud --charm wind_comb
    python storyworlds/worlds/gpt-5.4/photogenic_dick_repetition_rhyme_magic_fairy_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/photogenic_dick_repetition_rhyme_magic_fairy_tale.py --verify
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
        female = {"girl", "woman", "fairy", "queen", "mother"}
        male = {"boy", "man", "king", "father", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"fairy": "fairy", "queen": "queen", "king": "king"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    light: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    kind: str
    meter: str
    hint: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    spell: tuple[str, str, str] = field(default_factory=tuple)
    action: str = ""
    qa_action: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    name: str
    type: str
    entrance: str
    gift: str
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


def _r_blocked_reflection(world: World) -> list[str]:
    out: list[str] = []
    dick = world.get("dick")
    mirror = world.get("mirror")
    if dick.meters["needs_fix"] < THRESHOLD:
        return out
    sig = ("blocked",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mirror.meters["clear"] = 0.0
    dick.memes["worry"] += 1
    out.append("__blocked__")
    return out


def _r_clear_reflection(world: World) -> list[str]:
    out: list[str] = []
    dick = world.get("dick")
    mirror = world.get("mirror")
    if dick.meters["needs_fix"] >= THRESHOLD:
        return out
    if dick.meters["ready"] < THRESHOLD:
        return out
    sig = ("clear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mirror.meters["clear"] += 1
    dick.memes["hope"] += 1
    out.append("__clear__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="blocked_reflection", tag="state", apply=_r_blocked_reflection),
    Rule(name="clear_reflection", tag="state", apply=_r_clear_reflection),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def charm_fits(trouble: Trouble, charm: Charm) -> bool:
    return trouble.kind in charm.fixes


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for trouble_id, trouble in TROUBLES.items():
            for charm_id, charm in CHARMS.items():
                if charm_fits(trouble, charm):
                    for helper_id in HELPERS:
                        combos.append((setting_id, trouble_id, charm_id, helper_id))
    return combos


def explain_rejection(trouble: Trouble, charm: Charm) -> str:
    return (
        f"(No story: {charm.label} does not truly fix {trouble.phrase}. "
        f"In this world, {trouble.label} needs a charm that handles {trouble.kind}, "
        f"so choose one that really matches the problem.)"
    )


def predict_portrait(world: World, trouble: Trouble, charm: Charm) -> dict:
    sim = world.copy()
    dick = sim.get("dick")
    apply_trouble(sim, dick, trouble, narrate=False)
    if charm_fits(trouble, charm):
        apply_charm(sim, sim.get("helper"), dick, trouble, charm, narrate=False)
    mirror = sim.get("mirror")
    return {
        "ready": dick.meters["ready"] >= THRESHOLD,
        "clear": mirror.meters["clear"] >= THRESHOLD,
        "worry": dick.memes["worry"],
    }


def introduce(world: World, dick: Entity, setting: Setting) -> None:
    dick.memes["dream"] += 1
    world.say(
        f"In {setting.place}, where {setting.scene}, there lived a little boy named Dick."
    )
    world.say(
        f"He had a quick smile and bright eyes, and everyone said he looked almost photogenic whenever {setting.light} touched his face."
    )


def announce_portrait(world: World, dick: Entity) -> None:
    world.say(
        f"On the night of the silver portrait, Dick was to stand before the Moon Mirror, which remembered only true and tidy things."
    )
    world.say(
        f'Dick clapped his hands. "I will stand still, stand bright, stand right," he whispered, trying the words once, then again, then once more.'
    )


def apply_trouble(world: World, dick: Entity, trouble: Trouble, narrate: bool = True) -> None:
    dick.meters[trouble.meter] += 1
    dick.meters["needs_fix"] += 1
    dick.meters["ready"] = 0.0
    propagate(world, narrate=False)
    if narrate:
        world.say(trouble.effect)
        world.say(
            f"Soon {trouble.hint}, and the Moon Mirror gave back only a pale, shaky shimmer."
        )


def summon_helper(world: World, helper_cfg: Helper, helper: Entity, trouble: Trouble) -> None:
    helper.memes["care"] += 1
    world.say(
        f"Then {helper_cfg.entrance}, and {helper.id} came with {helper_cfg.gift}."
    )
    world.say(
        f'"Little Dick," said {helper.id}, "a mirror tells no lie. We must mend what {trouble.label} has spoiled before the portrait can shine."'
    )


def apply_charm(
    world: World,
    helper: Entity,
    dick: Entity,
    trouble: Trouble,
    charm: Charm,
    narrate: bool = True,
) -> None:
    if not charm_fits(trouble, charm):
        raise StoryError(explain_rejection(trouble, charm))
    dick.meters[trouble.meter] = 0.0
    dick.meters["needs_fix"] = 0.0
    dick.meters["ready"] += 1
    dick.memes["hope"] += 1
    dick.memes["worry"] = 0.0
    propagate(world, narrate=False)
    if narrate:
        a, b, c = charm.spell
        world.say(
            f'{helper.id} lifted {charm.phrase} and sang, "{a} {b} {c}"'
        )
        world.say(
            f'Once for the first fear, once for the second fear, once for the last fear, {helper.pronoun()} sang it again: "{a} {b} {c}."'
        )
        world.say(charm.action)


def portrait_success(world: World, dick: Entity, setting: Setting) -> None:
    mirror = world.get("mirror")
    if mirror.meters["clear"] < THRESHOLD:
        raise StoryError("(Story state error: the mirror is not clear enough for the portrait ending.)")
    dick.memes["joy"] += 1
    dick.memes["pride"] += 1
    world.say(
        f"When Dick stepped before the Moon Mirror again, it woke with a pearly hum and showed him bright and whole."
    )
    world.say(
        f"There stood Dick in the glass -- calm in his chin, bright in his grin, neat from shoe to hair -- and the portrait shone so kindly that even the moths hovered to look."
    )
    world.say(
        f"From that night on, people in {setting.place} liked to say, 'Bright and right, clear in the light,' whenever they remembered how Dick at last looked wonderfully photogenic."
    )


def tell(setting: Setting, trouble: Trouble, charm: Charm, helper_cfg: Helper) -> World:
    world = World(setting)
    dick = world.add(Entity(id="dick", kind="character", type="boy", label="Dick", role="hero"))
    helper = world.add(
        Entity(
            id=helper_cfg.name,
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.name,
            role="helper",
            tags=set(helper_cfg.tags),
        )
    )
    mirror = world.add(Entity(id="mirror", kind="thing", type="mirror", label="Moon Mirror", role="mirror"))
    world.facts["mirror_name"] = mirror.label

    introduce(world, dick, setting)
    announce_portrait(world, dick)

    world.para()
    apply_trouble(world, dick, trouble, narrate=True)
    summon_helper(world, helper_cfg, helper, trouble)

    world.para()
    apply_charm(world, helper, dick, trouble, charm, narrate=True)

    world.para()
    portrait_success(world, dick, setting)

    world.facts.update(
        setting=setting,
        trouble=trouble,
        charm=charm,
        helper_cfg=helper_cfg,
        dick=dick,
        helper=helper,
        mirror=mirror,
        ready=dick.meters["ready"] >= THRESHOLD,
        clear=mirror.meters["clear"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moon_glen": Setting(
        id="moon_glen",
        place="the Moon Glen",
        scene="blue mushrooms glowed beside the path and a white brook ran like silk",
        light="the moon-silver",
        tags={"moon", "mirror"},
    ),
    "rose_tower": Setting(
        id="rose_tower",
        place="the Rose Tower garden",
        scene="roses climbed the old stones and lantern-seeds floated over the hedges",
        light="the lantern-seed light",
        tags={"garden", "mirror"},
    ),
    "star_pond": Setting(
        id="star_pond",
        place="the Star Pond bank",
        scene="reeds bowed in the breeze and the water held little stars on its back",
        light="the starlight",
        tags={"pond", "mirror"},
    ),
}

TROUBLES = {
    "mud": Trouble(
        id="mud",
        label="mud",
        phrase="mud on his cheek and hands",
        kind="soil",
        meter="muddy",
        hint="a brown smear crossed his cheek and thumb",
        effect="But before he reached the mirror, he slipped by the path and dabbed mud on his cheek and hands.",
        tags={"mud", "dirty"},
    ),
    "tangles": Trouble(
        id="tangles",
        label="tangles",
        phrase="wild tangles in his hair",
        kind="tangle",
        meter="tangled",
        hint="his hair stuck up in prickly whorls",
        effect="But a playful wind danced round him and left wild tangles in his hair.",
        tags={"hair", "comb"},
    ),
    "jitters": Trouble(
        id="jitters",
        label="the jitters",
        phrase="shaking knees and a trembling chin",
        kind="jitters",
        meter="shaky",
        hint="his knees knocked softly, and his chin would not keep still",
        effect="But when the silver hour truly came, Dick felt the jitters in his knees and a tiny tremble in his chin.",
        tags={"calm", "pose"},
    ),
}

CHARMS = {
    "dew_cloth": Charm(
        id="dew_cloth",
        label="the dew-cloth",
        phrase="the dew-cloth",
        fixes={"soil"},
        spell=("Dew away,", "speck away,", "shine and stay!"),
        action="Soft as dawn, the dew-cloth whisked the mud away until Dick's face and hands looked fresh as morning.",
        qa_action="used the dew-cloth to wipe the mud away",
        tags={"dew", "clean"},
    ),
    "wind_comb": Charm(
        id="wind_comb",
        label="the wind-comb",
        phrase="the wind-comb of willow bone",
        fixes={"tangle"},
        spell=("Comb and glide,", "smooth with pride,", "moonbeams guide!"),
        action="The wind-comb hummed through Dick's hair, and every stray lock lay down as neatly as wheat before rain.",
        qa_action="used the wind-comb to smooth his hair",
        tags={"comb", "hair"},
    ),
    "hush_bell": Charm(
        id="hush_bell",
        label="the hush-bell",
        phrase="the hush-bell of pearl",
        fixes={"jitters"},
        spell=("Hush the knee,", "steady be,", "calm as tree!"),
        action="The hush-bell gave three gentle notes, and Dick's knees grew still while his chin settled into a brave little smile.",
        qa_action="rang the hush-bell until he felt calm and still",
        tags={"bell", "calm"},
    ),
}

HELPERS = {
    "thistle_fairy": Helper(
        id="thistle_fairy",
        name="Thistle",
        type="fairy",
        entrance="a ring of thistle-down spun in the air",
        gift="a pocket full of moonlit remedies",
        tags={"fairy", "magic"},
    ),
    "moss_witch": Helper(
        id="moss_witch",
        name="Moss",
        type="woman",
        entrance="a green shawl rustled beneath the hazel leaves",
        gift="a basket of old, kind magic",
        tags={"magic", "wise_helper"},
    ),
    "rook_page": Helper(
        id="rook_page",
        name="Rook",
        type="boy",
        entrance="a black-feathered page came skipping along the wall",
        gift="a silver satchel of charms",
        tags={"magic", "friend"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    trouble: str
    charm: str
    helper: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "mirror": [
        (
            "What is a magic mirror in a fairy tale?",
            "A magic mirror is a mirror with enchantment inside it. In fairy tales, it can show more than an ordinary reflection and sometimes reacts to truth, beauty, or spells.",
        )
    ],
    "mud": [
        (
            "Why does mud make a mess?",
            "Mud is wet earth, so it sticks to skin, shoes, and clothes. That is why it leaves smears and needs wiping away.",
        )
    ],
    "comb": [
        (
            "What does a comb do?",
            "A comb helps smooth and separate hair. It pulls tangles apart so hair can lie neatly.",
        )
    ],
    "calm": [
        (
            "Why is it easier to hold still when you feel calm?",
            "When you are calm, your body stops fidgeting so much. Then you can stand still and do careful things more easily.",
        )
    ],
    "fairy": [
        (
            "What kind of helper is a fairy in a fairy tale?",
            "A fairy is a magical helper who can notice a problem and use enchantment to mend it. Fairy-tale fairies often guide people toward a wiser or kinder ending.",
        )
    ],
    "magic": [
        (
            "What is magic in a fairy tale?",
            "Magic is a special power that can change things in a way ordinary tools cannot. In fairy tales it often works best when it is used for help, healing, or truth.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like light and bright. Rhymes can make a spell or poem easier to remember.",
        )
    ],
    "repetition": [
        (
            "What is repetition in a story?",
            "Repetition is when a word, line, or action comes again and again. It can make a magical moment feel stronger and more memorable.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mirror", "mud", "comb", "calm", "fairy", "magic", "rhyme", "repetition"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    trouble = f["trouble"]
    charm = f["charm"]
    helper = f["helper"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the words "photogenic" and "Dick" and uses repetition, rhyme, and magic.',
        f"Tell a gentle fairy tale set in {setting.place} where a boy named Dick cannot stand for a magic portrait because of {trouble.phrase}, and {helper.id} helps with {charm.label}.",
        f'Write a moonlit story where a child hears a rhyming spell repeated three times and ends with a clear portrait in a magic mirror.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    dick = f["dick"]
    helper = f["helper"]
    trouble = f["trouble"]
    charm = f["charm"]
    setting = f["setting"]
    mirror = f["mirror"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little boy named Dick who wants a portrait in the {mirror.label}. It is also about {helper.id}, the helper who mends the trouble for him.",
        ),
        (
            "What did Dick want at the beginning?",
            f"Dick wanted to stand before the magic mirror and have a bright moonlit portrait made. He hoped the mirror would remember him at his best.",
        ),
        (
            "What went wrong before the portrait?",
            f"{trouble.effect.split(' But ', 1)[-1] if ' But ' in trouble.effect else trouble.effect} This mattered because the Moon Mirror would not shine clearly while {trouble.phrase} was still there.",
        ),
        (
            f"How did {helper.id} help Dick?",
            f"{helper.id} {charm.qa_action}. The charm matched the real problem, so Dick became ready for the portrait instead of staying worried.",
        ),
        (
            "Why did the spell sound repeated and rhyming?",
            f"The helper said the spell once, then again, then again, so the magic felt strong and sure. The lines also rhymed to make the charm easy to remember and gentle to hear.",
        ),
        (
            "How did the story end?",
            f"It ended with Dick stepping before the Moon Mirror again and seeing a bright, clear picture of himself. The ending image proves the change, because the trouble was gone and the portrait could finally shine.",
        ),
    ]
    if trouble.id == "jitters":
        qa.append(
            (
                "Why did calming down help the portrait?",
                "A portrait needs someone to hold still long enough for the magic mirror to catch the right moment. When Dick's knees stopped shaking, the mirror could show him clearly.",
            )
        )
    if trouble.id == "mud":
        qa.append(
            (
                "Why was the mud a problem for the portrait?",
                "The mud covered part of Dick's face and hands, so the mirror could not show him clean and bright. Wiping it away let the true picture appear.",
            )
        )
    if trouble.id == "tangles":
        qa.append(
            (
                "Why did the hair need fixing first?",
                "Dick's hair was sticking up in wild tangles, which made him look unsettled and unready. Once the tangles were smoothed, he could stand proud and still.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"mirror", "magic", "rhyme", "repetition"}
    trouble = world.facts["trouble"]
    charm = world.facts["charm"]
    helper = world.facts["helper"]
    if "mud" in trouble.tags:
        tags.add("mud")
    if "comb" in trouble.tags or "comb" in charm.tags:
        tags.add("comb")
    if "calm" in trouble.tags or "calm" in charm.tags:
        tags.add("calm")
    if "fairy" in helper.tags:
        tags.add("fairy")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="moon_glen", trouble="mud", charm="dew_cloth", helper="thistle_fairy"),
    StoryParams(setting="rose_tower", trouble="tangles", charm="wind_comb", helper="moss_witch"),
    StoryParams(setting="star_pond", trouble="jitters", charm="hush_bell", helper="rook_page"),
    StoryParams(setting="moon_glen", trouble="tangles", charm="wind_comb", helper="thistle_fairy"),
    StoryParams(setting="rose_tower", trouble="jitters", charm="hush_bell", helper="moss_witch"),
]


ASP_RULES = r"""
fits(Trouble, Charm) :- trouble(Trouble), charm(Charm),
                        trouble_kind(Trouble, K), fixes(Charm, K).

valid(Setting, Trouble, Charm, Helper) :-
    setting(Setting), trouble(Trouble), charm(Charm), helper(Helper),
    fits(Trouble, Charm).

outcome(clear_portrait) :- chosen_trouble(T), chosen_charm(C), fits(T, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("trouble_kind", trouble_id, trouble.kind))
    for charm_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", charm_id))
        for fix in sorted(charm.fixes):
            lines.append(asp.fact("fixes", charm_id, fix))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_trouble", params.trouble),
            asp.fact("chosen_charm", params.charm),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def verify_generation_smoke() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("(Verify failed: generated story was empty.)")
    if "photogenic" not in sample.story.lower():
        raise StoryError('(Verify failed: story did not include the word "photogenic".)')
    if "Dick" not in sample.story:
        raise StoryError('(Verify failed: story did not include the word "Dick".)')


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

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        py = "clear_portrait" if charm_fits(TROUBLES[params.trouble], CHARMS[params.charm]) else "?"
        asp_res = asp_outcome(params)
        if py != asp_res:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} ASP outcomes differ.")

    try:
        verify_generation_smoke()
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Dick, a moon portrait, a fitting charm, and a fairy-tale ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.charm:
        trouble = TROUBLES[args.trouble]
        charm = CHARMS[args.charm]
        if not charm_fits(trouble, charm):
            raise StoryError(explain_rejection(trouble, charm))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.charm is None or combo[2] == args.charm)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, trouble_id, charm_id, helper_id = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting_id,
        trouble=trouble_id,
        charm=charm_id,
        helper=helper_id,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        trouble = TROUBLES[params.trouble]
        charm = CHARMS[params.charm]
        helper_cfg = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if not charm_fits(trouble, charm):
        raise StoryError(explain_rejection(trouble, charm))

    world = tell(setting, trouble, charm, helper_cfg)
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, trouble, charm, helper) combos:\n")
        for setting_id, trouble_id, charm_id, helper_id in combos:
            print(f"  {setting_id:10} {trouble_id:8} {charm_id:10} {helper_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting}: {p.trouble} -> {p.charm} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
