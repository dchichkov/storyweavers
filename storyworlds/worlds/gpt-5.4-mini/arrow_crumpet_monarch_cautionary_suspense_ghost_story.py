#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/arrow_crumpet_monarch_cautionary_suspense_ghost_story.py
========================================================================================

A standalone storyworld for a tiny cautionary suspense ghost story with a monarch,
an arrow, and a crumpet. The domain is intentionally small: a child hears a spooky
rule, ignores it, triggers a harmless-but-frightening haunting, and then follows a
safer choice that calms the old hall.

The story model is state-driven:
- physical meters: chill, rustle, glow, cracked, sealed
- emotional memes: curiosity, fear, relief, bravado, caution

The default shape is ghost-story-like: quiet beginning, suspenseful middle, a warning,
a turn into danger, and a calm ending that proves what changed.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Prophecy:
    id: str
    label: str
    phrase: str
    omen: str
    gate: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    near: str
    spooky: str
    can_rattle: bool = True
    can_crack: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_haunt(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["glow"] < THRESHOLD and e.meters["rattle"] < THRESHOLD:
            continue
        sig = ("haunt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "hall" in world.entities:
            world.get("hall").meters["chill"] += 1
        for ch in world.characters():
            ch.memes["fear"] += 1
        out.append("__haunt__")
    return out


def _r_crack(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["cracked"] < THRESHOLD:
            continue
        sig = ("crack", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "hall" in world.entities:
            world.get("hall").meters["haunted"] += 1
        out.append("__crack__")
    return out


CAUSAL_RULES = [Rule("haunt", "physical", _r_haunt), Rule("crack", "physical", _r_crack)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def shadow_risk(prophecy: Prophecy, hazard: Hazard) -> bool:
    return prophecy.label == "arrow" and hazard.can_rattle


def fireless_risk(prophecy: Prophecy, hazard: Hazard) -> bool:
    return prophecy.label == "arrow" and hazard.can_rattle


def is_contained(remedy: Remedy, hazard: Hazard, delay: int) -> bool:
    return remedy.power >= (1 + delay if hazard.can_rattle else delay)


def haunt_severity(hazard: Hazard, delay: int) -> int:
    return 1 + delay + (1 if hazard.can_crack else 0)


def predict(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_arrow(sim, sim.get(target_id), narrate=False)
    return {
        "haunted": sim.get("hall").meters["haunted"],
        "chill": sim.get("hall").meters["chill"],
    }


def _do_arrow(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["rattle"] += 1
    target.meters["glow"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, monarch: Entity, scene: str) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a moonless night, {child.id} tiptoed through the old hall beneath "
        f"the painted eyes of the {monarch.label}. The {scene} was quiet enough "
        f"to hear a crumb fall."
    )


def crumpet_offer(world: World, child: Entity, crumpet: Prophecy) -> None:
    world.say(
        f"On a tray beside the hearth sat {crumpet.phrase}, left there for the "
        f"midnight watch. Its warm scent made the silence feel even stranger."
    )


def warning(world: World, child: Entity, helper: Entity, prophecy: Prophecy, hazard: Hazard) -> None:
    pred = predict(world, "arrow")
    helper.memes["caution"] += 1
    world.facts["pred"] = pred
    world.say(
        f'{helper.id} frowned. "{child.id}, do not touch {prophecy.label}. '
        f'It could wake the old hall, and {hazard.phrase} would answer."'
    )


def defy(world: World, child: Entity, prophecy: Prophecy) -> None:
    child.memes["bravado"] += 1
    world.say(
        f'"It is only an old {prophecy.label}," {child.id} whispered, and reached '
        f"for it anyway."
    )


def release_arrow(world: World, prophecy: Prophecy, hazard: Hazard) -> None:
    arrow = world.get("arrow")
    _do_arrow(world, arrow)
    world.say(
        f"The {prophecy.label} twanged from the rafters with a thin, lonely note. "
        f"It struck {hazard.near}, and at once the lantern-glow went cold."
    )


def alarm(world: World, child: Entity, helper: Entity, hazard: Hazard, monarch: Entity) -> None:
    child.memes["fear"] += 1
    world.say(
        f'"{helper.id}!" {child.id} cried. "The hall is whispering!" '
        f"The portrait of the {monarch.label} seemed to watch the shadows move."
    )


def calm_fix(world: World, helper: Entity, remedy: Remedy, hazard: Hazard) -> None:
    hazard_ent = world.get(hazard.id)
    hazard_ent.meters["rattle"] = 0
    hazard_ent.meters["glow"] = 0
    world.get("hall").meters["chill"] = 0
    world.say(
        f"{helper.label_word.capitalize()} came quietly and {remedy.text}. "
        f"The whispering stopped, and the air felt warm again."
    )
    world.say(
        f"The crumpet tray stayed steady, the old arrows stayed in their case, "
        f"and the dark corners of the hall went still."
    )


def lesson(world: World, child: Entity, helper: Entity, prophecy: Prophecy) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {helper.label_word.capitalize()} knelt down and said, "
        f'"Some things are not for games. {prophecy.label}s belong to the keeper, '
        f'and a spooky room is no place to test them."'
    )
    world.say(f'"I promise," whispered {child.id}.')
    world.say(
        f"{child.id} looked once more at the silent tray of {prophecy.phrase} "
        f"and felt brave in a new, careful way."
    )


def safe_ending(world: World, child: Entity, helper: Entity, monarch: Entity) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"The next night, {child.id} carried the crumpet tray by both hands while "
        f"{helper.id} held the lamp. Beneath the watchful face of the {monarch.label}, "
        f"they left the old hall quiet, lit, and safe."
    )


def tell(scene: str, prophecy: Prophecy, hazard: Hazard, remedy: Remedy,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Aunt June", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    monarch = world.add(Entity(id="Monarch", kind="character", type="monarch", label="monarch"))
    hall = world.add(Entity(id="hall", type="place", label="the hall"))
    arrow = world.add(Entity(id="arrow", type="thing", label="arrow"))
    crumpet = world.add(Entity(id="crumpet", type="thing", label="crumpet"))

    opening(world, child, monarch, scene)
    crumpet_offer(world, child, prophecy)
    world.para()
    warning(world, child, helper, prophecy, hazard)
    defy(world, child, prophecy)
    world.para()
    release_arrow(world, prophecy, hazard)
    alarm(world, child, helper, hazard, monarch)
    world.para()
    calm_fix(world, helper, remedy, hazard)
    lesson(world, child, helper, prophecy)
    world.para()
    safe_ending(world, child, helper, monarch)

    world.facts.update(
        child=child, helper=helper, monarch=monarch, hall=hall,
        arrow=arrow, crumpet=crumpet, prophecy=prophecy, hazard=hazard,
        remedy=remedy, scene=scene, warned=True, ended_safe=True,
    )
    return world


SCENES = {
    "castle": "the castle corridor",
    "gallery": "the candlelit gallery",
    "tower": "the high tower stair",
}

PROPHECIES = {
    "arrow": Prophecy("arrow", "arrow", "an old arrow", "thin and cold", "in the wall", tags={"arrow"}),
    "crumpet": Prophecy("crumpet", "crumpet", "a lonely crumpet", "warm and harmless", "on the tray", tags={"crumpet"}),
}

HAZARDS = {
    "chime": Hazard("chime", "chime rope", "the chime rope", "near the window", "it can rattle in the dark", can_rattle=True, can_crack=False, tags={"ghost"}),
    "glass": Hazard("glass", "glass pane", "the glass pane", "by the lantern", "it can crack with a whisper", can_rattle=True, can_crack=True, tags={"ghost"}),
}

REMEDIES = {
    "wrap": Remedy("wrap", 3, 3, "wrapped the arrow case in a heavy cloth and tied it shut", "tried to wrap it, but the hall kept rattling", "wrapped the arrow case in a heavy cloth", tags={"cloth"}),
    "seal": Remedy("seal", 2, 2, "sealed the loose panel with wax and pushed the arrow back into its slot", "sealed it, but the whispering still leaked out", "sealed the loose panel with wax", tags={"wax"}),
    "lamp": Remedy("lamp", 3, 3, "lit the lamp and held it steady until every shadow shrank", "lit the lamp, but the dark still pressed too hard", "lit the lamp and held it steady", tags={"lamp"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for p in PROPHECIES:
            for h in HAZARDS:
                if fireless_risk(PROPHECIES[p], HAZARDS[h]):
                    combos.append((s, p, h))
    return combos


@dataclass
@dataclass
class StoryParams:
    scene: str
    prophecy: str
    hazard: str
    remedy: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a ghost story for a young child set in {f['scene']} that includes the words arrow, crumpet, and monarch.",
        f"Tell a suspenseful cautionary tale where {f['child'].id} is warned not to touch an arrow near a spooky hall, then chooses the safer path.",
        f"Write a short ghost story with a calm ending, a crumpet on a tray, and a monarch watching over the hall.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, prop, hazard, remedy = f["child"], f["helper"], f["prophecy"], f["hazard"], f["remedy"]
    return [
        QAItem(
            question=f"What did {child.id} want to touch?",
            answer=f"{child.id} wanted to touch the {prop.label}. That was the thing the warning was about, because it could wake the hall."
        ),
        QAItem(
            question="What happened when the arrow was touched?",
            answer=f"The arrow made a thin, spooky sound and the hall turned cold. The rattle woke the old place up, so everyone knew to be careful."
        ),
        QAItem(
            question=f"How did {helper.id} fix the problem?",
            answer=f"{helper.id} {remedy.qa_text}. That stopped the whispering and made the room calm again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an arrow?", "An arrow is a pointed stick made for shooting with a bow. It is not a toy for curious hands."),
        QAItem("What is a crumpet?", "A crumpet is a small bread cake that can be warm and tasty, usually eaten with butter."),
        QAItem("What is a monarch?", "A monarch is a ruler like a king or queen. In stories, a monarch can watch over a castle or kingdom."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("castle", "arrow", "glass", "wrap", "Mina", "girl", "Aunt June", "woman"),
    StoryParams("gallery", "arrow", "chime", "seal", "Ivo", "boy", "Uncle Ben", "man"),
    StoryParams("tower", "arrow", "glass", "lamp", "Nora", "girl", "Guard Ada", "woman"),
]


def explain_rejection(prophecy: Prophecy, hazard: Hazard) -> str:
    if prophecy.label != "arrow":
        return "(No story: this world needs the arrow as the risky object.)"
    if not hazard.can_rattle:
        return "(No story: the chosen hazard would not make the hall answer back.)"
    return "(No story: that combination does not create a spooky enough cautionary scene.)"


def outcome_of(params: StoryParams) -> str:
    return "contained"


ASP_RULES = r"""
hazard(A, H) :- prophecy(A), spooky(H).
valid(S, P, H) :- scene(S), prophecy(P), hazard(H), arrow_risk(P, H).
outcome(contained) :- valid(_, _, _).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for p in PROPHECIES:
        lines.append(asp.fact("prophecy", p))
        if PROPHECIES[p].label == "arrow":
            lines.append(asp.fact("arrow_risk", p, "yes"))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
        lines.append(asp.fact("spooky", h))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python.")
    try:
        p = CURATED[0]
        with redirect_stdout(io.StringIO()):
            s = generate(p)
        if not s.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: arrow, crumpet, monarch.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--prophecy", choices=PROPHECIES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prophecy and args.prophecy != "arrow":
        raise StoryError("This ghost story needs the arrow to be the risky object.")
    if args.scene and args.hazard and not shadow_risk(PROPHECIES["arrow"], HAZARDS[args.hazard]):
        raise StoryError(explain_rejection(PROPHECIES["arrow"], HAZARDS[args.hazard]))
    combos = valid_combos()
    if args.scene:
        combos = [c for c in combos if c[0] == args.scene]
    if args.prophecy:
        combos = [c for c in combos if c[1] == args.prophecy]
    if args.hazard:
        combos = [c for c in combos if c[2] == args.hazard]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, prop, haz = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(REMEDIES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(["Mina", "Ivo", "Nora", "Seth"])
    helper_name = args.helper_name or rng.choice(["Aunt June", "Uncle Ben", "Guard Ada", "Old Mara"])
    return StoryParams(scene, prop, haz, remedy, child_name, child_gender, helper_name, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], PROPHECIES[params.prophecy], HAZARDS[params.hazard],
                 REMEDIES[params.remedy], params.child_name, params.child_gender,
                 params.helper_name, params.helper_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
