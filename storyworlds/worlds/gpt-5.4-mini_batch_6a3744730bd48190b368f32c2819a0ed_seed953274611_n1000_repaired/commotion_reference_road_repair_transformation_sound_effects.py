#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/commotion_reference_road_repair_transformation_sound_effects.py
================================================================================================

A tiny fable-style story world about a road repair, a growing commotion,
a useful reference, and a transformation that changes the ending image.

The premise is classical and small:
- a road repair closes a lane and makes a fuss;
- a child or helper finds a reference that explains the work;
- sound effects mark the repair beats;
- the noisy scene transforms into something safe, useful, and calm.

The script is self-contained, uses the shared StorySample/QAItem/StoryError
containers, and provides a Python reasonableness gate plus a matching inline
ASP twin.
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
SOUND_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    road_text: str
    commotion_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class ReferenceBook:
    id: str
    label: str
    phrase: str
    explain: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class RepairTool:
    id: str
    label: str
    phrase: str
    sound: str
    effect: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Transformation:
    id: str
    from_state: str
    to_state: str
    text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_commotion(world: World) -> list[str]:
    out: list[str] = []
    road = world.get("road")
    if road.meters["blocked"] < THRESHOLD:
        return out
    sig = ("commotion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    road.meters["commotion"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["unease"] += 1
    out.append("__commotion__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    road = world.get("road")
    if road.meters["repaired"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    road.meters["clear"] += 1
    road.meters["blocked"] = 0.0
    road.meters["commotion"] = 0.0
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["relief"] += 1
            ent.memes["wonder"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("commotion", "social", _r_commotion),
    Rule("transform", "physical", _r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_gate(reference: ReferenceBook, tool: RepairTool, setting: Setting) -> bool:
    return "road" in setting.tags and "explain" in reference.tags and "sound" in tool.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, ref in REFERENCES.items():
            for tid, tool in TOOLS.items():
                if reasonableness_gate(ref, tool, setting):
                    combos.append((sid, rid, tid))
    return combos


def road_severity(damage: int, delay: int) -> int:
    return damage + delay


def can_transform(tool: RepairTool, damage: int, delay: int) -> bool:
    return tool.effect_power >= road_severity(damage, delay)


def predict_turn(world: World, damage: int, tool: RepairTool) -> dict:
    sim = world.copy()
    sim.get("road").meters["blocked"] = damage
    sim.get("road").meters["repaired"] = 1
    propagate(sim, narrate=False)
    return {
        "cleared": sim.get("road").meters["clear"] >= THRESHOLD,
        "commotion": sim.get("road").meters["commotion"],
    }


def mark_repair(world: World, tool: RepairTool, road: Entity) -> None:
    road.meters["repaired"] += 1
    road.meters["sound"] += 1
    world.say(f"{tool.sound} {tool.effect}.")


def tell_commotion(world: World, child: Entity, helper: Entity, setting: Setting, ref: ReferenceBook) -> None:
    child.memes["curiosity"] += 1
    helper.memes["patience"] += 1
    world.say(
        f"On the road repair street, {setting.road_text} {setting.commotion_text}. "
        f"{child.id} stood on the curb, listening to the fuss and the banging."
    )
    world.say(
        f'"What is all that commotion?" {child.id} asked. {helper.id} smiled and held up '
        f"{ref.phrase}, {ref.explain}."
    )


def start_work(world: World, crew: Entity, road: Entity, tool: RepairTool) -> None:
    road.meters["blocked"] += 1
    crew.memes["focus"] += 1
    world.say(
        f"The workers began at dawn. {tool.sound} went the tool, and {tool.phrase} made the lanes tremble."
    )


def warn_and_predict(world: World, child: Entity, helper: Entity, ref: ReferenceBook, tool: RepairTool) -> None:
    pred = predict_turn(world, 1, tool)
    world.facts["predicted_commotion"] = pred["commotion"]
    child.memes["understanding"] += 1
    world.say(
        f"{helper.id} pointed to {ref.label} again. "
        f'"That is our reference," {helper.pronoun()} said. "It shows why the work makes noise, and why the noise will not last forever."'
    )


def transform_scene(world: World, road: Entity, tool: RepairTool, trans: Transformation) -> None:
    road.meters["repaired"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came the final {tool.sound}: {trans.text}"
    )


def resolve_end(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"By afternoon, the road was no longer a mess of stones and dust. "
        f"Now it was {setting.place}, smooth and safe, and {child.id} waved goodbye to the last truck with a grin."
    )
    world.say(
        f"The commotion had turned into a path people could use, and that was the neatest change of all."
    )


def tell(setting: Setting, ref: ReferenceBook, tool: RepairTool, trans: Transformation,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "The guide", helper_gender: str = "man") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    road = world.add(Entity(id="road", type="thing", label="the road"))
    crew = world.add(Entity(id="crew", kind="character", type="man", role="crew", label="the workers"))

    tell_commotion(world, child, helper, setting, ref)
    world.para()
    start_work(world, crew, road, tool)
    warn_and_predict(world, child, helper, ref, tool)
    if not can_transform(tool, 1, 0):
        world.say("The plan was too small for the job, and the road stayed broken.")
        outcome = "stalled"
    else:
        transform_scene(world, road, tool, trans)
        world.para()
        resolve_end(world, child, helper, setting)
        outcome = "transformed"

    world.facts.update(
        child=child,
        helper=helper,
        road=road,
        setting=setting,
        reference=ref,
        tool=tool,
        transformation=trans,
        outcome=outcome,
    )
    return world


SETTINGS = {
    "road_repair": Setting(
        id="road_repair",
        place="the road became new again",
        road_text="the little road was torn up for repair",
        commotion_text="there was a great commotion of hammers, cones, and trucks",
        tags={"road"},
    ),
    "bridge_repair": Setting(
        id="bridge_repair",
        place="the bridge became strong again",
        road_text="the bridge was under repair",
        commotion_text="there was a great commotion of hammers, cones, and trucks",
        tags={"road"},
    ),
}

REFERENCES = {
    "sign": ReferenceBook(
        id="sign",
        label="the sign",
        phrase="a bright sign by the work zone",
        explain="it showed the street would be open again when the work was done",
        tags={"explain"},
    ),
    "map": ReferenceBook(
        id="map",
        label="the map",
        phrase="a folded map of the block",
        explain="it marked the repair area and the safe way around it",
        tags={"explain"},
    ),
}

TOOLS = {
    "roller": RepairTool(
        id="roller",
        label="roller",
        phrase="a heavy roller",
        sound="Rrrr",
        effect="smoothed the fresh tar",
        tags={"sound"},
    ),
    "drill": RepairTool(
        id="drill",
        label="drill",
        phrase="a loud drill",
        sound="Brrr",
        effect="shook the broken edge loose so it could be fixed",
        tags={"sound"},
    ),
}

TRANSFORMATIONS = {
    "mend": Transformation(
        id="mend",
        from_state="broken",
        to_state="mended",
        text="the broken lane became a smooth ribbon of black tar",
        tags={"transformation"},
    ),
    "brighten": Transformation(
        id="brighten",
        from_state="dusty",
        to_state="bright",
        text="the cones came off and the fresh paint gleamed in the sun",
        tags={"transformation"},
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ivy", "Tia"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Leo", "Finn"]


@dataclass
class StoryParams:
    setting: str
    reference: str
    tool: str
    transformation: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Road repair fable with commotion, reference, sound effects, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--reference", choices=REFERENCES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["man", "woman", "boy", "girl"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.reference and args.reference not in REFERENCES:
        raise StoryError("Unknown reference.")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if args.transformation and args.transformation not in TRANSFORMATIONS:
        raise StoryError("Unknown transformation.")

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.reference is None or c[1] == args.reference)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, reference, tool = rng.choice(sorted(combos))
    transformation = args.transformation or rng.choice(sorted(TRANSFORMATIONS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["man", "woman"])
    helper_name = args.helper_name or rng.choice(["The guide", "The foreman", "The mason"])
    return StoryParams(
        setting=setting,
        reference=reference,
        tool=tool,
        transformation=transformation,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-style road repair story that includes the words "commotion" and "reference".',
        f"Tell a child-friendly tale where {f['child'].id} watches road repair, learns from {f['reference'].label}, and hears the repair sounds turn into a calm ending.",
        f"Write a short fable about a noisy road repair that changes the street into something useful and safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    ref = f["reference"]
    tool = f["tool"]
    trans = f["transformation"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who watch a road repair and talk about what is happening. The child listens while the helper explains the work." ),
        ("Why was there a commotion?",
         f"There was a commotion because the road was being repaired with trucks, cones, and loud tools. That made the whole street noisy until the work was done."),
        ("What reference did the helper show?",
         f"{helper.id} showed {ref.phrase}. It helped explain why the road was closed and where people should go instead."),
        ("What sound effect was part of the repair?",
         f"The repair made sounds like {tool.sound}. Those sounds fit the work and helped the story feel alive."),
    ]
    if f["outcome"] == "transformed":
        qa.append((
            "How did the road change at the end?",
            f"It transformed into {trans.text.lower()}. The noisy work became a safe road people could use again."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with calm and relief. The commotion was gone, and {child.id} could see the road had become useful again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is road repair?",
         "Road repair is when workers fix a broken road so it is safe and smooth to use again."),
        ("What is a reference?",
         "A reference is something you can look at for help or explanation, like a sign or map."),
        ("What are sound effects in a story?",
         "Sound effects are words that show a noise, like bang, rattle, or rumble, so the reader can hear the scene in their mind."),
        ("What is a transformation?",
         "A transformation is a change from one state into another, like a broken road becoming a smooth one."),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="road_repair", reference="sign", tool="roller", transformation="mend", child_name="Mina", child_gender="girl", helper_name="The guide", helper_gender="man"),
    StoryParams(setting="bridge_repair", reference="map", tool="drill", transformation="brighten", child_name="Owen", child_gender="boy", helper_name="The foreman", helper_gender="woman"),
]


def explain_rejection(reference: ReferenceBook, tool: RepairTool, setting: Setting) -> str:
    if "road" not in setting.tags:
        return "(No story: this setting is not really about road repair.)"
    if "explain" not in reference.tags:
        return "(No story: the reference would not explain the road work.)"
    if "sound" not in tool.tags:
        return "(No story: the tool would not give the repair its proper sound effects.)"
    return "(No story: this combination does not make a reasonable road-repair fable.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "road" in s.tags:
            lines.append(asp.fact("road_setting", sid))
    for rid, r in REFERENCES.items():
        lines.append(asp.fact("reference", rid))
        if "explain" in r.tags:
            lines.append(asp.fact("explains", rid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if "sound" in t.tags:
            lines.append(asp.fact("sound_tool", tid))
    for tid, t in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,R,T) :- road_setting(S), reference(R), explains(R), tool(T), sound_tool(T).
story_ready(S,R,T) :- valid(S,R,T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos()")
        print("only in clingo:", sorted(a - b))
        print("only in python:", sorted(b - a))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        return 1 if not print(exc) else 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.reference not in REFERENCES:
        raise StoryError("Invalid reference.")
    if params.tool not in TOOLS:
        raise StoryError("Invalid tool.")
    if params.transformation not in TRANSFORMATIONS:
        raise StoryError("Invalid transformation.")
    world = tell(SETTINGS[params.setting], REFERENCES[params.reference], TOOLS[params.tool], TRANSFORMATIONS[params.transformation], params.child_name, params.child_gender, params.helper_name, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(f"{len(combos)} compatible (setting, reference, tool) combos:")
        for row in combos:
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.reference is None or c[1] == args.reference)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, reference, tool = rng.choice(sorted(combos))
    transformation = args.transformation or rng.choice(sorted(TRANSFORMATIONS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["man", "woman"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(["The guide", "The foreman", "The mason"])
    return StoryParams(
        setting=setting,
        reference=reference,
        tool=tool,
        transformation=transformation,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def valid_combos() -> list[tuple[str, str, str]]:
    return [(sid, rid, tid) for sid in SETTINGS for rid in REFERENCES for tid in TOOLS if reasonableness_gate(REFERENCES[rid], TOOLS[tid], SETTINGS[sid])]


def build_world(setting: Setting) -> World:
    return World(setting)


def tell(setting: Setting, ref: ReferenceBook, tool: RepairTool, trans: Transformation,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = build_world(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    road = world.add(Entity(id="road", type="road", label="the road"))
    world.add(Entity(id="crew", kind="character", type="man", role="crew", label="the workers"))

    tell_commotion(world, child, helper, setting, ref)
    world.para()
    start_work(world, world.get("crew"), road, tool)
    warn_and_predict(world, child, helper, ref, tool)
    road.meters["blocked"] = 1
    if can_transform(tool, 1, 0):
        mark_repair(world, tool, road)
        transform_scene(world, road, tool, trans)
        world.para()
        resolve_end(world, child, helper, setting)
        outcome = "transformed"
    else:
        world.say("The work could not finish, and the road stayed broken.")
        outcome = "stalled"
    world.facts.update(child=child, helper=helper, road=road, reference=ref, tool=tool, transformation=trans, outcome=outcome)
    return world


if __name__ == "__main__":
    main()
