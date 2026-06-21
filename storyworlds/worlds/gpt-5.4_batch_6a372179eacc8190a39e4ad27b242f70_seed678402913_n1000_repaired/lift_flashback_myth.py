#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lift_flashback_myth.py
=================================================

A small myth-flavored storyworld about a child who must lift something heavy,
hears an elder's flashback, and learns that strength guided by memory can move
what bare wishing cannot.

The domain stays narrow on purpose. A burden blocks some good thing in the
world: a spring, a path, or a temple door. A hero wants to lift it. An elder
remembers an old lesson in a flashback. The hero then uses a fitting method and
a helper, and the blocked good thing returns.

Run it
------
python storyworlds/worlds/gpt-5.4/lift_flashback_myth.py
python storyworlds/worlds/gpt-5.4/lift_flashback_myth.py --burden spring_lid --method ash_pole --helper ox
python storyworlds/worlds/gpt-5.4/lift_flashback_myth.py --burden sun_branch --method bare_hands --helper crane
python storyworlds/worlds/gpt-5.4/lift_flashback_myth.py --all
python storyworlds/worlds/gpt-5.4/lift_flashback_myth.py --qa --json
python storyworlds/worlds/gpt-5.4/lift_flashback_myth.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
HERO_POWER = 1


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
        female = {"girl", "woman", "grandmother", "sister"}
        male = {"boy", "man", "grandfather", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Burden:
    id: str
    label: str
    phrase: str
    place: str
    problem: str
    need: int
    requires: set[str] = field(default_factory=set)
    release: str = ""
    ending: str = ""
    flashback_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    power: int
    capabilities: set[str] = field(default_factory=set)
    move_text: str = ""
    memory_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    type: str
    power: int
    role_text: str = ""
    memory_text: str = ""
    qa_text: str = ""
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


def _r_unblock(world: World) -> list[str]:
    burden = world.get("burden")
    if burden.meters["lifted"] < THRESHOLD:
        return []
    sig = ("unblock", burden.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("place").meters["blessing"] += 1
    world.get("hero").memes["hope"] += 1
    world.get("elder").memes["pride"] += 1
    helper = world.get("helper")
    helper.memes["glad"] += 1
    return ["__blessing__"]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for sent in _r_unblock(world):
            changed = True
            if not sent.startswith("__"):
                world.say(sent)


def total_power(method: Method, helper: Helper) -> int:
    return HERO_POWER + method.power + helper.power


def capability_match(burden: Burden, method: Method) -> bool:
    return bool(burden.requires & method.capabilities)


def combo_valid(burden: Burden, method: Method, helper: Helper) -> bool:
    return capability_match(burden, method) and total_power(method, helper) >= burden.need


def explain_rejection(burden: Burden, method: Method, helper: Helper) -> str:
    if not capability_match(burden, method):
        return (
            f"(No story: {method.phrase} cannot help lift {burden.phrase}. "
            f"That burden needs a method that can {' or '.join(sorted(burden.requires))}.)"
        )
    have = total_power(method, helper)
    if have < burden.need:
        return (
            f"(No story: {method.phrase} with {helper.phrase} is not enough to lift "
            f"{burden.phrase}. The burden needs strength {burden.need}, but this choice only gives {have}.)"
        )
    return "(No story: that combination does not fit this world.)"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for bid, burden in BURDENS.items():
        for mid, method in METHODS.items():
            for hid, helper in HELPERS.items():
                if combo_valid(burden, method, helper):
                    combos.append((bid, mid, hid))
    return sorted(combos)


def predict_success(method: Method, helper: Helper, burden: Burden) -> dict:
    return {
        "power": total_power(method, helper),
        "need": burden.need,
        "enough": combo_valid(burden, method, helper),
    }


def introduce(world: World, hero: Entity, elder: Entity, burden: Burden) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"In the old days, when hills were said to remember songs, {hero.id} lived beside {burden.place} "
        f"with {hero.pronoun('possessive')} {elder.label_word}."
    )
    world.say(
        f"{hero.id} was a little {hero.type} with a {hero.attrs.get('trait', 'steady')} heart, "
        f"and {hero.pronoun()} listened for the needs of the world."
    )


def trouble(world: World, hero: Entity, burden: Burden) -> None:
    world.get("place").meters["blocked"] += 1
    hero.memes["care"] += 1
    world.say(
        f"One morning, {burden.problem}. There lay {burden.phrase}, and no small hands could lift it."
    )
    world.say(
        f"{hero.id} touched the edge of it and whispered, \"If only I could lift it, the good thing behind it would wake again.\""
    )


def warning(world: World, elder: Entity, hero: Entity, burden: Burden, method: Method, helper: Helper) -> None:
    pred = predict_success(method, helper, burden)
    world.facts["predicted_power"] = pred["power"]
    world.facts["predicted_need"] = pred["need"]
    elder.memes["memory"] += 1
    world.say(
        f"{elder.label_word.capitalize()} shook {elder.pronoun('possessive')} head gently. "
        f"\"Stone and bronze do not move for wishing alone,\" {elder.pronoun()} said."
    )
    if pred["power"] > pred["need"]:
        world.say(
            f"Still, {elder.pronoun()} studied {method.phrase} and {helper.phrase} and saw that together they might be strong enough."
        )
    else:
        world.say(
            f"{elder.pronoun().capitalize()} measured the weight with old eyes and knew that strength would need wisdom beside it."
        )


def flashback(world: World, elder: Entity, burden: Burden, method: Method, helper: Helper) -> None:
    world.say(
        f"Then {elder.label_word} grew quiet, and the room of now opened into a room of long ago."
    )
    world.say(
        f"When {elder.pronoun()} was young, {burden.flashback_image}. "
        f"{method.memory_text} {helper.memory_text}"
    )
    world.say(
        f"\"That day taught me this,\" said {elder.label_word}. "
        f"\"The world lets us lift heavy things when we ask help the right way.\""
    )


def gather(world: World, hero: Entity, method: Method, helper_ent: Entity) -> None:
    hero.memes["courage"] += 1
    helper_ent.memes["trust"] += 1
    world.say(
        f"So {hero.id} fetched {method.phrase}, and {helper_ent.phrase} came near {helper_ent.role_text}."
    )


def lift_attempt(world: World, hero: Entity, burden_ent: Entity, method: Method, helper_ent: Entity, burden: Burden) -> None:
    burden_ent.meters["strain"] += 1
    hero.meters["effort"] += 1
    helper_ent.meters["effort"] += 1
    world.say(
        f"{hero.id} set to work. {method.move_text} {helper_ent.qa_text.capitalize()}."
    )
    burden_ent.meters["lifted"] += 1
    propagate(world)
    world.say(
        f"Slowly, with a groan like an old drum, {burden.label} began to lift."
    )


def blessing(world: World, burden: Burden) -> None:
    world.get("place").meters["blocked"] = 0.0
    world.say(burden.release)
    world.say(
        f"{burden.ending}"
    )


def closing(world: World, hero: Entity, elder: Entity, method: Method, helper_ent: Entity) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"{elder.label_word.capitalize()} laid a warm hand on {hero.id}'s shoulder. "
        f"\"You did not only lift a weight,\" {elder.pronoun()} said. "
        f"\"You lifted it with memory, patience, and help.\""
    )
    world.say(
        f"And after that day, whenever {hero.id} heard the word lift, "
        f"{hero.pronoun()} remembered not just muscles, but {method.label} and {helper_ent.label} working beside a brave heart."
    )


def tell(
    burden: Burden,
    method: Method,
    helper: Helper,
    hero_name: str = "Nia",
    hero_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "steady",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        attrs={"trait": trait},
    ))
    elder_label = "grandmother" if elder_type == "grandmother" else "grandfather"
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label=elder_label,
        phrase=f"the {elder_label}",
        role="elder",
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character" if helper.type in {"girl", "boy", "sister", "brother"} else "thing",
        type=helper.type,
        label=helper.label,
        phrase=helper.phrase,
        role="helper",
        tags=set(helper.tags),
    ))
    burden_ent = world.add(Entity(
        id="burden",
        type="burden",
        label=burden.label,
        phrase=burden.phrase,
        role="burden",
        tags=set(burden.tags),
    ))
    world.add(Entity(
        id="place",
        type="place",
        label=burden.place,
        phrase=burden.place,
        role="place",
    ))

    introduce(world, hero, elder, burden)
    trouble(world, hero, burden)

    world.para()
    warning(world, elder, hero, burden, method, helper)
    flashback(world, elder, burden, method, helper)

    world.para()
    gather(world, hero, method, helper_ent)
    lift_attempt(world, hero, burden_ent, method, helper_ent, burden)
    blessing(world, burden)

    world.para()
    closing(world, hero, elder, method, helper_ent)

    world.facts.update(
        hero=hero,
        elder=elder,
        helper=helper_ent,
        burden_cfg=burden,
        burden=burden_ent,
        method=method,
        helper_cfg=helper,
        lifted=burden_ent.meters["lifted"] >= THRESHOLD,
    )
    return world


BURDENS = {
    "spring_lid": Burden(
        id="spring_lid",
        label="the spring-stone",
        phrase="a round stone lid over the thirsty hill spring",
        place="the foot of the blue hill",
        problem="the village spring had gone silent, because a round stone lid had slipped over its mouth",
        need=4,
        requires={"lever"},
        release="The spring burst free at once, silver and laughing, and the jars of the village were no longer empty.",
        ending="Water ran around the hero's ankles like bright ribbon, and even the dry herbs by the path lifted their heads.",
        flashback_image="a flood had rolled a stone across the very same spring",
        tags={"spring", "water", "stone"},
    ),
    "sun_branch": Burden(
        id="sun_branch",
        label="the goldwood branch",
        phrase="a storm-fallen branch of goldwood lying across the lamb path",
        place="the meadow below the temple fig tree",
        problem="the lamb path to the meadow was closed, because a storm-fallen branch of goldwood lay across it",
        need=2,
        requires={"hands", "rope"},
        release="The path opened again, and the lambs skipped through as if little bells were tied inside their wool.",
        ending="Dust shone in the sunlight, and the meadow looked once more like a green rug spread for morning.",
        flashback_image="a shining branch had trapped the first lambs of spring",
        tags={"path", "branch", "lambs"},
    ),
    "moon_bar": Burden(
        id="moon_bar",
        label="the bronze moon-bar",
        phrase="a bronze bar fallen across the small temple door",
        place="the white steps of the moon shrine",
        problem="the little temple stayed dark, because a bronze bar had fallen across its door",
        need=3,
        requires={"lever", "rope"},
        release="The temple door opened, and lamplight rolled out in a soft gold sheet over the steps.",
        ending="The white stones of the shrine gleamed again, as if the moon herself had polished them with her sleeve.",
        flashback_image="the shrine door had once been shut after a wind from the sea",
        tags={"temple", "bronze", "door"},
    ),
}

METHODS = {
    "ash_pole": Method(
        id="ash_pole",
        label="an ash pole",
        phrase="an ash pole smooth from many hands",
        power=2,
        capabilities={"lever"},
        move_text="With both hands, the child slid the ash pole under the burden's lip and leaned on the long wood as the earth leaned back.",
        memory_text="In that old hour, a plain ash pole had done what proud tugging could not.",
        qa_text="the helper leaned in at the same time",
        tags={"lever", "pole"},
    ),
    "woven_rope": Method(
        id="woven_rope",
        label="a woven rope",
        phrase="a woven rope of river reeds",
        power=1,
        capabilities={"rope"},
        move_text="The child looped the reed rope around the burden and pulled in a steady rhythm instead of one sharp jerk.",
        memory_text="In that old hour, a reed rope had turned scattered pulling into one patient pull.",
        qa_text="the helper pulled with the child in one rhythm",
        tags={"rope", "reed"},
    ),
    "bare_hands": Method(
        id="bare_hands",
        label="bare hands",
        phrase="bare hands and a deep breath",
        power=1,
        capabilities={"hands"},
        move_text="The child crouched low, found a true grip, and lifted with knees, back, and breath all together.",
        memory_text="In that old hour, the elder learned that even bare hands must lift with care, not with rushing anger.",
        qa_text="the helper steadied the weight so it would not twist away",
        tags={"hands", "strength"},
    ),
}

HELPERS = {
    "ox": Helper(
        id="ox",
        label="the little ox",
        phrase="the little ox from the yard",
        type="animal",
        power=2,
        role_text="snorting softly as if it already understood the task",
        memory_text="And a patient little ox had lowered its head and shared the burden without boasting.",
        qa_text="the little ox put its sturdy shoulder to the work",
        tags={"animal", "ox"},
    ),
    "crane": Helper(
        id="crane",
        label="the white crane",
        phrase="a white crane from the reeds",
        type="animal",
        power=1,
        role_text="with bright eyes and careful steps",
        memory_text="And a white crane had tapped and tugged until the right angle appeared, as if cleverness itself had grown feathers.",
        qa_text="the white crane pecked and tugged at just the right moment",
        tags={"bird", "crane"},
    ),
    "sister": Helper(
        id="sister",
        label="big sister",
        phrase="big sister with her rolled sleeves",
        type="sister",
        power=1,
        role_text="smiling the smile that means work will be shared",
        memory_text="And an older sister had taken hold without teasing, so the weight was borne by two hearts instead of one.",
        qa_text="big sister pulled and braced beside the child",
        tags={"family", "sister"},
    ),
}


GIRL_NAMES = ["Nia", "Tala", "Iris", "Mira", "Dara", "Luma", "Rhea", "Sena"]
BOY_NAMES = ["Ari", "Theo", "Milo", "Orin", "Damon", "Eli", "Niko", "Tarin"]
TRAITS = ["steady", "gentle", "bright", "patient", "brave", "careful"]


@dataclass
class StoryParams:
    burden: str
    method: str
    helper: str
    hero: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        burden="spring_lid",
        method="ash_pole",
        helper="ox",
        hero="Nia",
        gender="girl",
        elder="grandmother",
        trait="patient",
    ),
    StoryParams(
        burden="sun_branch",
        method="bare_hands",
        helper="sister",
        hero="Ari",
        gender="boy",
        elder="grandfather",
        trait="brave",
    ),
    StoryParams(
        burden="moon_bar",
        method="woven_rope",
        helper="ox",
        hero="Mira",
        gender="girl",
        elder="grandmother",
        trait="steady",
    ),
    StoryParams(
        burden="sun_branch",
        method="woven_rope",
        helper="crane",
        hero="Theo",
        gender="boy",
        elder="grandfather",
        trait="bright",
    ),
]


KNOWLEDGE = {
    "lever": [(
        "What is a lever?",
        "A lever is a long thing, like a pole, that helps you lift a heavy weight by giving your hands more power."
    )],
    "rope": [(
        "Why can a rope help move something heavy?",
        "A rope lets people pull together and keep their pull steady. That can make a heavy thing easier to move."
    )],
    "spring": [(
        "What is a spring?",
        "A spring is water that comes out of the ground. People and animals can drink from it."
    )],
    "temple": [(
        "What is a temple in a story?",
        "A temple is a special place where people go quietly, light lamps, and remember holy things."
    )],
    "crane": [(
        "What is a crane?",
        "A crane is a tall bird with long legs and a long neck. It walks carefully in shallow water."
    )],
    "ox": [(
        "What is an ox?",
        "An ox is a strong farm animal. It can help pull or carry heavy things."
    )],
    "memory": [(
        "What is a flashback in a story?",
        "A flashback is when a story pauses the present and remembers something from long ago. The old memory helps explain what happens now."
    )],
    "help": [(
        "Why is asking for help wise?",
        "Asking for help is wise because some jobs are too big for one person alone. Working together can make a hard thing possible."
    )],
}
KNOWLEDGE_ORDER = ["memory", "spring", "temple", "lever", "rope", "crane", "ox", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    burden = f["burden_cfg"]
    method = f["method"]
    helper = f["helper_cfg"]
    elder = f["elder"]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the word "lift" and uses a flashback.',
        f"Tell a gentle myth where {hero.id} wants to lift {burden.phrase}, and {elder.label_word} helps by remembering an older lesson.",
        f"Write a child-facing story in a myth style where {method.label} and {helper.label} help solve a problem after an elder's memory changes the hero's plan.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    helper = f["helper"]
    burden = f["burden_cfg"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type}, {elder.label_word}, and {helper.label}. They worked together around {burden.place}."
        ),
        (
            "What problem did the hero find?",
            f"{hero.id} found {burden.phrase} blocking something good. Because of that, {burden.problem.split('because ', 1)[-1]}."
        ),
        (
            f"Why did {elder.label_word} tell a memory from long ago?",
            f"{elder.label_word.capitalize()} wanted {hero.id} to understand that heavy things do not move by wishing alone. The flashback gave a true lesson from the past, so the child knew how to act in the present."
        ),
        (
            f"How did {hero.id} lift the burden?",
            f"{hero.id} used {method.phrase}, and {helper.qa_text}. They succeeded because the old memory taught them to work with patience instead of rushing."
        ),
        (
            "How did the story end?",
            f"After the burden lifted, {burden.release} {burden.ending} The ending image shows that the world changed for the better."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    burden = f["burden_cfg"]
    method = f["method"]
    helper = f["helper_cfg"]
    tags: set[str] = {"memory", "help"}
    if "spring" in burden.tags or "water" in burden.tags:
        tags.add("spring")
    if "temple" in burden.tags:
        tags.add("temple")
    if "lever" in method.capabilities:
        tags.add("lever")
    if "rope" in method.capabilities:
        tags.add("rope")
    if helper.id == "crane":
        tags.add("crane")
    if helper.id == "ox":
        tags.add("ox")
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
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
can_use(B, M) :- burden(B), method(M), requires(B, C), capability(M, C).
enough(B, M, H) :- burden(B), method(M), helper(H),
                   burden_need(B, N), method_power(M, MP), helper_power(H, HP),
                   hero_power(HR), HR + MP + HP >= N.
valid(B, M, H) :- can_use(B, M), enough(B, M, H).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("hero_power", HERO_POWER)]
    for bid, burden in BURDENS.items():
        lines.append(asp.fact("burden", bid))
        lines.append(asp.fact("burden_need", bid, burden.need))
        for req in sorted(burden.requires):
            lines.append(asp.fact("requires", bid, req))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_power", mid, method.power))
        for cap in sorted(method.capabilities):
            lines.append(asp.fact("capability", mid, cap))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_power", hid, helper.power))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth storyworld: a child tries to lift a burden after an elder's flashback teaches the right way."
    )
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (burden, method, helper) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.burden is not None and args.burden not in BURDENS:
        raise StoryError(f"(Unknown burden: {args.burden})")
    if args.method is not None and args.method not in METHODS:
        raise StoryError(f"(Unknown method: {args.method})")
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {args.helper})")

    if args.burden and args.method and args.helper:
        burden = BURDENS[args.burden]
        method = METHODS[args.method]
        helper = HELPERS[args.helper]
        if not combo_valid(burden, method, helper):
            raise StoryError(explain_rejection(burden, method, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.burden is None or combo[0] == args.burden)
        and (args.method is None or combo[1] == args.method)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    burden_id, method_id, helper_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        burden=burden_id,
        method=method_id,
        helper=helper_id,
        hero=hero,
        gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.burden not in BURDENS:
        raise StoryError(f"(Unknown burden: {params.burden})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    burden = BURDENS[params.burden]
    method = METHODS[params.method]
    helper = HELPERS[params.helper]
    if not combo_valid(burden, method, helper):
        raise StoryError(explain_rejection(burden, method, helper))

    world = tell(
        burden=burden,
        method=method,
        helper=helper,
        hero_name=params.hero,
        hero_gender=params.gender,
        elder_type=params.elder,
        trait=params.trait,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    smoke_cases = list(CURATED)
    for seed in range(5):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError as err:
            rc = 1
            print(f"Smoke setup failed at seed {seed}: {err}")

    try:
        for case in smoke_cases:
            sample = generate(case)
            if "lift" not in sample.story.lower():
                rc = 1
                print(f"Smoke failure: story missing required word 'lift' for {case}.")
            if not sample.story_qa or not sample.world_qa or not sample.prompts:
                rc = 1
                print(f"Smoke failure: missing QA/prompts for {case}.")
        print(f"OK: generated {len(smoke_cases)} smoke-test stories.")
    except Exception as err:
        rc = 1
        print(f"Smoke generation crashed: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (burden, method, helper) combos:\n")
        for burden, method, helper in combos:
            print(f"  {burden:12} {method:11} {helper}")
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
            header = f"### {p.hero}: {p.burden} with {p.method} and {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
