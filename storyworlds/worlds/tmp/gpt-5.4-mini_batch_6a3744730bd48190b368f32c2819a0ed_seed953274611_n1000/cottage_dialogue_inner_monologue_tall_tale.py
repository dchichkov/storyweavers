#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cottage_dialogue_inner_monologue_tall_tale.py
=============================================================================

A standalone storyworld for a tall-tale cottage adventure with dialogue and
inner monologue.

Premise:
- A small cottage sits on the edge of a windy moor.
- A child or helper worries the cottage will wobble, rattle, or lose something
  important.
- They talk it through aloud, think bravely to themselves, and solve the
  problem with a clever, larger-than-life fix.
- The ending proves the change in the world: the cottage is steadier, safer,
  and still a place for warm light.

This world is built to satisfy the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose, not a frozen paragraph
- a Python reasonableness gate plus an inline ASP twin
- three Q&A sets derived from world state, not parsed from rendered English
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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


@dataclass
class StoryParams:
    character: str
    character_gender: str
    helper: str
    helper_gender: str
    helper_relation: str
    cottage: str
    wind: str
    object: str
    fix: str
    seed: Optional[int] = None


@dataclass
class CottageCfg:
    id: str
    label: str
    scene: str
    weather: str
    thing_that_wobbles: str
    hidden_worry: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class WindCfg:
    id: str
    label: str
    phrase: str
    sound: str
    force: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    risk: str
    loss: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FixCfg:
    id: str
    label: str
    action: str
    result: str
    power: int
    sense: int
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    cottage = next((e for e in world.entities.values() if e.role == "cottage"), None)
    wind = next((e for e in world.entities.values() if e.role == "wind"), None)
    if not cottage or not wind:
        return out
    if cottage.meters["strain"] < THRESHOLD:
        return out
    sig = ("wobble", cottage.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cottage.meters["wobble"] += 1
    for ent in world.entities.values():
        if ent.kind == "character":
            ent.memes["worry"] += 1
    if wind:
        wind.meters["howl"] += 1
    out.append("__wobble__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    obj = next((e for e in world.entities.values() if e.role == "object"), None)
    cottage = next((e for e in world.entities.values() if e.role == "cottage"), None)
    if not obj or not cottage:
        return out
    if cottage.meters["wobble"] < THRESHOLD:
        return out
    sig = ("loss", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obj.meters["lost"] += 1
    out.append("__loss__")
    return out


CAUSAL_RULES = [
    Rule("wobble", "physical", _r_wobble),
    Rule("loss", "physical", _r_loss),
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
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for cottage in COTTAGES:
        for wind in WINDS:
            for obj in OBJECTS:
                if hazard_at_risk(COTTAGES[cottage], WINDS[wind], OBJECTS[obj]):
                    combos.append((cottage, wind, obj))
    return combos


def hazard_at_risk(cottage: CottageCfg, wind: WindCfg, obj: ObjectCfg) -> bool:
    return wind.force >= 3 and obj.id in {"roof_tile", "chimney_smoke", "window_latch"}


def reasoned_fix(cottage: CottageCfg, wind: WindCfg, obj: ObjectCfg) -> FixCfg | None:
    for fix in FIXES.values():
        if wind.force <= fix.power and obj.id in fix.tags:
            return fix
    return None


def fix_severity(wind: WindCfg) -> int:
    return wind.force


def is_contained(fix: FixCfg, wind: WindCfg) -> bool:
    return fix.power >= fix_severity(wind)


def predict_break(world: World, cottage_id: str) -> dict:
    sim = world.copy()
    cottage = sim.get(cottage_id)
    cottage.meters["strain"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": cottage.meters["wobble"] >= THRESHOLD,
        "lost": any(e.meters["lost"] >= THRESHOLD for e in sim.entities.values()),
    }


def setup(world: World, child: Entity, helper: Entity, cottage: CottageCfg, wind: WindCfg) -> None:
    child.memes["wonder"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On the edge of the moor stood {cottage.label}, small as a teacup and brave as a drum. "
        f"{cottage.scene}"
    )
    world.say(
        f"{child.id} listened to {wind.sound} in the grass and thought, "
        f'"A house can tell a tall tale if the wind tries hard enough."'
    )


def inner_thought(world: World, child: Entity, cottage: CottageCfg) -> None:
    child.memes["worry"] += 1
    world.say(
        f"In {child.id}'s own head, a little voice whispered, "
        f'"What if the {cottage.thing_that_wobbles} lets go?"'
    )


def dialogue(world: World, child: Entity, helper: Entity, wind: WindCfg, obj: ObjectCfg) -> None:
    world.say(
        f'"Did you hear that?" {child.id} asked.'
    )
    world.say(
        f'"I did," said {helper.id}, "and I am not letting a silly breeze turn this {obj.label} into a memory."'
    )
    world.say(
        f"{child.id} swallowed hard and thought, "
        f'"If we can mend it, the cottage can stay put.'"
    )


def warning(world: World, helper: Entity, cottage: CottageCfg, wind: WindCfg, obj: ObjectCfg) -> None:
    pred = predict_break(world, "cottage")
    helper.memes["caution"] += 1
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_loss"] = pred["lost"]
    world.say(
        f'"This wind is strong enough to make the {cottage.thing_that_wobbles} shake," '
        f"said {helper.id}. "
        f'"And if the {obj.label} comes loose, it could go skittering off like a cat on a roof."'
    )


def defy(world: World, child: Entity, obj: ObjectCfg) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} stared at the {obj.label} and thought, "
        f'"I have seen bigger troubles in smaller boots."'
    )
    world.say(
        f"Then {child.id} climbed toward the trouble with {obj.phrase} in hand."
    )


def do_fix(world: World, helper: Entity, fix: FixCfg, cottage: CottageCfg, obj: ObjectCfg) -> None:
    cottage_ent = world.get("cottage")
    cottage_ent.meters["strain"] = 0
    cottage_ent.meters["steady"] += 1
    if obj.id in fix.tags:
        world.say(
            f'{helper.id} said, "{fix.action.capitalize()}; hold fast!" '
            f"and {fix.result}."
        )
    else:
        world.say(
            f'{helper.id} said, "{fix.action.capitalize()}; hold fast!" '
            f"and somehow the cottage answered with a deep, pleased creak."
        )


def ending(world: World, child: Entity, helper: Entity, cottage: CottageCfg, fix: FixCfg) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last, the wind could snarl all it liked, but the cottage stood stout and square."
    )
    world.say(
        f"{child.id} looked out at the moon and thought, "
        f'"Well, that was a mountain in a teacup."'
    )
    world.say(
        f"{helper.id} laughed and said, "
        f'"Aye, and now the teacup has a lid."'
    )
    world.say(cottage.ending_image)


def tell(cottage: CottageCfg, wind: WindCfg, obj: ObjectCfg, fix: FixCfg,
         character: str = "Mara", character_gender: str = "girl",
         helper: str = "Gran", helper_gender: str = "woman",
         helper_relation: str = "grandparent") -> World:
    world = World()
    child = world.add(Entity(id=character, kind="character", type=character_gender, role="child"))
    helper_ent = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    cottage_ent = world.add(Entity(id="cottage", kind="thing", type="place", label=cottage.label, role="cottage"))
    wind_ent = world.add(Entity(id="wind", kind="thing", type="weather", label=wind.label, role="wind"))
    obj_ent = world.add(Entity(id="object", kind="thing", type="thing", label=obj.label, role="object"))

    world.facts.update(cottage=cottage, wind=wind, object=obj, fix=fix, child=child, helper=helper_ent)

    setup(world, child, helper_ent, cottage, wind)
    inner_thought(world, child, cottage)
    world.para()
    dialogue(world, child, helper_ent, wind, obj)
    warning(world, helper_ent, cottage, wind, obj)
    if fix.id == "bad_fix":
        raise StoryError("This fix is not sensible for the cottage and wind.")
    world.para()
    defy(world, child, obj)
    cottage_ent.meters["strain"] += wind.force
    propagate(world, narrate=False)
    if is_contained(fix, wind):
        do_fix(world, helper_ent, fix, cottage, obj)
        ending(world, child, helper_ent, cottage, fix)
        outcome = "contained"
    else:
        world.say(
            f"{helper.id} tried to help, but the wind had already made a long, wild joke of things."
        )
        world.say(
            f"In the end, everyone got inside, and the cottage was left with a rattled roof and a loud story."
        )
        outcome = "burned"
    world.facts["outcome"] = outcome
    return world


COTTAGES = {
    "blue_cottage": CottageCfg(
        id="blue_cottage",
        label="the blue cottage",
        scene="Its blue shutters clicked like castanets, and a little porch lantern winked at the dark.",
        weather="windy",
        thing_that_wobbles="chimney cap",
        hidden_worry="the chimney cap might dance off",
        ending_image="By dawn, the blue cottage sat calm under the clouds, its lantern warm and its roof tied down like a circus tent.",
        tags={"cottage"},
    ),
    "apple_cottage": CottageCfg(
        id="apple_cottage",
        label="the apple cottage",
        scene="A crooked apple tree leaned over it, and the windows shone like two slices of pie.",
        weather="blustery",
        thing_that_wobbles="roof tile",
        hidden_worry="one roof tile might sail away",
        ending_image="By dawn, the apple cottage stood snug, with every roof tile in its place and the apple tree bowing politely beside it.",
        tags={"cottage"},
    ),
    "lantern_cottage": CottageCfg(
        id="lantern_cottage",
        label="the lantern cottage",
        scene="A round lantern burned in the window, steady as a star, though the grass bent nearly double.",
        weather="stormy",
        thing_that_wobbles="window latch",
        hidden_worry="the window latch might chatter open",
        ending_image="By dawn, the lantern cottage glowed steady, with its windows latched and the moor tamed by light.",
        tags={"cottage"},
    ),
}

WINDS = {
    "breezy": WindCfg(id="breezy", label="the breezy wind", phrase="a breezy wind", sound="whisper-whirr", force=3, tags={"wind"}),
    "blustery": WindCfg(id="blustery", label="the blustery wind", phrase="a blustery wind", sound="hooo-hah", force=4, tags={"wind"}),
    "stormwind": WindCfg(id="stormwind", label="the storm wind", phrase="a storm wind", sound="WHOOO-ROAR", force=5, tags={"wind"}),
}

OBJECTS = {
    "roof_tile": ObjectCfg(id="roof_tile", label="roof tile", phrase="a stone roof tile", risk="roof", loss="skittering away", tags={"roof_tile"}),
    "chimney_smoke": ObjectCfg(id="chimney_smoke", label="chimney cap", phrase="the chimney cap", risk="chimney", loss="tumbling into the grass", tags={"chimney"}),
    "window_latch": ObjectCfg(id="window_latch", label="window latch", phrase="the iron window latch", risk="window", loss="snapping open", tags={"window"}),
}

FIXES = {
    "rope": FixCfg(id="rope", label="rope", action="pull down the ladder and loop rope around the roof beam", result="the cottage gave one proud shake and stayed put", power=5, sense=3, tags={"roof_tile", "chimney", "window"}),
    "plank": FixCfg(id="plank", label="plank", action="brace the loose place with a stout plank", result="the roof stopped rattling at once", power=4, sense=3, tags={"roof_tile", "window"}),
    "tune": FixCfg(id="tune", label="lantern tune", action="tighten the latch and sing to the old wood", result="the latch settled with a satisfied click", power=5, sense=4, tags={"window", "chimney"}),
    "bad_fix": FixCfg(id="bad_fix", label="bad fix", action="wave a hand and hope", result="nothing helpful happened", power=1, sense=1, tags=set()),
}

NAMES = ["Mara", "Nell", "Ivy", "June", "Tom", "Owen", "Jasper", "Ada"]
HELPERS = ["Gran", "Aunt Bess", "Uncle Will", "Old Ben"]


def story_valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for cid, cottage in COTTAGES.items():
        for wid, wind in WINDS.items():
            for oid, obj in OBJECTS.items():
                if hazard_at_risk(cottage, wind, obj) and reasoned_fix(cottage, wind, obj):
                    combos.append((cid, wid, oid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale cottage storyworld with dialogue and inner monologue.")
    ap.add_argument("--cottage", choices=COTTAGES)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--helper-relation", choices=["grandparent", "neighbor", "uncle", "aunt"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def explain_rejection(cottage: CottageCfg, wind: WindCfg, obj: ObjectCfg) -> str:
    return (
        f"(No story: {wind.label} can trouble a cottage, but {obj.label} is not the right weak point for a tale here. "
        f"Pick one of: {', '.join(sorted(OBJECTS))}.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and args.fix not in FIXES:
        raise StoryError("Unknown fix.")
    if args.cottage and args.wind and args.object:
        cot, win, obj = COTTAGES[args.cottage], WINDS[args.wind], OBJECTS[args.object]
        if not hazard_at_risk(cot, win, obj):
            raise StoryError(explain_rejection(cot, win, obj))
        if not reasoned_fix(cot, win, obj):
            raise StoryError("No sensible fix exists for that combination.")
    combos = [c for c in story_valid_combos()
              if (args.cottage is None or c[0] == args.cottage)
              and (args.wind is None or c[1] == args.wind)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    cid, wid, oid = rng.choice(sorted(combos))
    fix = args.fix or reasoned_fix(COTTAGES[cid], WINDS[wid], OBJECTS[oid]).id
    return StoryParams(
        character=args.name or rng.choice(NAMES),
        character_gender=args.gender or rng.choice(["girl", "boy"]),
        helper=args.helper or rng.choice(HELPERS),
        helper_gender=args.helper_gender or rng.choice(["woman", "man"]),
        helper_relation=args.helper_relation or rng.choice(["grandparent", "neighbor", "uncle", "aunt"]),
        cottage=cid,
        wind=wid,
        object=oid,
        fix=fix,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child that includes the word "cottage" and uses dialogue and inner monologue.',
        f"Tell a windy cottage story where {f['child'].id} talks with {f['helper'].id} and thinks bravely to {f['child'].pronoun('possessive')}self.",
        f"Write a story about {f['cottage'].label} standing up to {f['wind'].label} and ending with a clever fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    cottage = f["cottage"]
    wind = f["wind"]
    obj = f["object"]
    fix = f["fix"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {helper.id}, who watched over {cottage.label} when the wind got wild. They used their words and their wits to handle the trouble together.",
        ),
        QAItem(
            question="What was the problem in the story?",
            answer=f"The wind was strong enough to make {cottage.thing_that_wobbles} shake, and {obj.label} might have come loose. That meant the cottage needed help before the trouble could grow bigger.",
        ),
        QAItem(
            question="How did the characters solve the problem?",
            answer=f"{helper.id} used {fix.label} and a steady voice, and {child.id} helped by listening and thinking bravely. The fix held the cottage firm so the wind could not bully it anymore.",
        ),
    ]
    if f.get("outcome") == "contained":
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with {cottage.label} steady again and looking proud in the moonlight. The ending image shows that the cottage stayed safe and warm after the repair.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set()
    tags |= f["cottage"].tags
    tags |= f["wind"].tags
    tags |= f["object"].tags
    tags |= f["fix"].tags
    knowledge = {
        "cottage": QAItem("What is a cottage?", "A cottage is a small house. People often think of it as cozy, simple, and full of warm light."),
        "wind": QAItem("What does wind do?", "Wind is moving air. It can rattle doors, rustle grass, and make loose things wobble."),
        "roof_tile": QAItem("What is a roof tile?", "A roof tile is a piece that helps cover a roof. It keeps rain and wind out when it is in place."),
        "chimney": QAItem("What does a chimney cap do?", "A chimney cap helps cover the top of a chimney. It can keep wind and rain from getting in too easily."),
        "window": QAItem("What does a window latch do?", "A window latch helps keep a window closed. That keeps a window from swinging open when the wind blows."),
    }
    out = []
    for tag in ["cottage", "wind", "roof_tile", "chimney", "window"]:
        if tag in tags and tag in knowledge:
            out.append(knowledge[tag])
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(C, W, O) :- cottage(C), wind(W), object(O), strong(W), weak_point(O).
sensible_fix(F, O) :- fix(F), fix_power(F, P), object_tag(O, T), fix_tag(F, T), sense(F, S), S >= sense_min(M), P >= 3.
valid(C, W, O) :- hazard(C, W, O), sensible_fix(F, O).
outcome(contained) :- chosen_fix(F), fix_power(F, P), chosen_wind(W), wind_force(W, WF), P >= WF.
outcome(broken) :- chosen_fix(F), chosen_wind(W), wind_force(W, WF), fix_power(F, P), P < WF.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in COTTAGES:
        lines.append(asp.fact("cottage", cid))
    for wid, w in WINDS.items():
        lines.append(asp.fact("wind", wid))
        lines.append(asp.fact("wind_force", wid, w.force))
        if w.force >= 3:
            lines.append(asp.fact("strong", wid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("object_tag", oid, oid))
        if oid in {"roof_tile", "chimney_smoke", "window_latch"}:
            lines.append(asp.fact("weak_point", oid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_power", fid, f.power))
        lines.append(asp.fact("sense", fid, f.sense))
        for t in f.tags:
            lines.append(asp.fact("fix_tag", fid, t))
    lines.append(asp.fact("sense_min", 3))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_fix", params.fix), asp.fact("chosen_wind", params.wind)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(story_valid_combos()):
        print("OK: gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test story generation works.")
    except Exception as exc:
        return 1 if not isinstance(exc, StoryError) else 1
    return rc


def generate(params: StoryParams) -> StorySample:
    keys = (params.cottage, params.wind, params.object, params.fix)
    if params.cottage not in COTTAGES or params.wind not in WINDS or params.object not in OBJECTS or params.fix not in FIXES:
        raise StoryError("Invalid StoryParams.")
    cottage = COTTAGES[params.cottage]
    wind = WINDS[params.wind]
    obj = OBJECTS[params.object]
    fix = FIXES[params.fix]
    if not hazard_at_risk(cottage, wind, obj):
        raise StoryError("That combination is not a real cottage hazard.")
    if not reasoned_fix(cottage, wind, obj) or fix.id != reasoned_fix(cottage, wind, obj).id:
        raise StoryError("That fix does not make sense for the problem.")
    world = tell(cottage, wind, obj, fix, params.character, params.character_gender, params.helper, params.helper_gender, params.helper_relation)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(character="Mara", character_gender="girl", helper="Gran", helper_gender="woman", helper_relation="grandparent", cottage="blue_cottage", wind="breezy", object="chimney_smoke", fix="rope"),
    StoryParams(character="Tom", character_gender="boy", helper="Old Ben", helper_gender="man", helper_relation="neighbor", cottage="apple_cottage", wind="blustery", object="roof_tile", fix="plank"),
    StoryParams(character="Ivy", character_gender="girl", helper="Aunt Bess", helper_gender="woman", helper_relation="aunt", cottage="lantern_cottage", wind="stormwind", object="window_latch", fix="tune"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
