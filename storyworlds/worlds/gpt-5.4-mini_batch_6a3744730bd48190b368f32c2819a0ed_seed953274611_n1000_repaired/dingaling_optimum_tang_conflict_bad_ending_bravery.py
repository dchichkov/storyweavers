#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dingaling_optimum_tang_conflict_bad_ending_bravery.py
======================================================================================

A tiny standalone storyworld for a rhyming tale about a brave child, a noisy
dingaling, a tense conflict, and a bad ending that teaches a careful lesson.

Premise
-------
A child wants to make the "optimum" sound with a dangling bell-string, but the
string tangles, the conflict grows, and bravery is tested. The story can end in
a bad way when the child chooses to push on instead of asking for help.

This world is intentionally small:
- typed entities with physical ``meters`` and emotional ``memes``
- a state-driven story engine
- a Python reasonableness gate plus an inline ASP twin
- generated prompts, story-grounded QA, and world-knowledge QA
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

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
    sound_space: str
    stage: str
    rhyme_tag: str
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
class Instrument:
    id: str
    name: str
    phrase: str
    action: str
    sound: str
    dangerous: bool = False
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
class TangledThing:
    id: str
    name: str
    phrase: str
    snag: str
    spread: int = 1
    tangled: bool = True
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    bell = world.entities.get("bell")
    cord = world.entities.get("cord")
    if not bell or not cord:
        return out
    if bell.meters["ringing"] < THRESHOLD:
        return out
    sig = ("tangle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cord.meters["tangled"] += 1
    out.append("__tangled__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    if not child or not parent:
        return out
    if child.memes["defiance"] < THRESHOLD or cord_tangled(world) is False:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] += 1
    parent.memes["conflict"] += 1
    out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("tangle", "physical", _r_tangle), Rule("conflict", "social", _r_conflict)]


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


def cord_tangled(world: World) -> bool:
    cord = world.entities.get("cord")
    return bool(cord and cord.meters["tangled"] >= THRESHOLD)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SOUND_MIN]


def reasonableness_gate(instr: Instrument, tang: TangledThing) -> bool:
    return instr.dangerous and tang.tangled


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def estimate_spread(tang: TangledThing, delay: int) -> int:
    return tang.spread + delay


def can_contain(response: Response, tang: TangledThing, delay: int) -> bool:
    return response.power >= estimate_spread(tang, delay)


def predict_problem(world: World, instrument: Instrument) -> dict:
    sim = world.copy()
    _do_action(sim, narrate=False)
    return {
        "tangled": cord_tangled(sim),
        "conflict": sim.get("child").memes["conflict"] >= THRESHOLD,
    }


def _do_action(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    bell = world.get("bell")
    cord = world.get("cord")
    child.meters["reach"] += 1
    bell.meters["ringing"] += 1
    if narrate:
        world.say(f"{child.id} gave the bell-string a swing, and the little dingaling sang.")
    propagate(world, narrate=narrate)
    if cord.meters["tangled"] >= THRESHOLD and narrate:
        world.say(f"The cord got into a knotty tang, and the tune went wrong.")


def tell(setting: Setting, instrument: Instrument, tang: TangledThing,
         response: Response, child_name: str = "Mina", child_type: str = "girl",
         parent_type: str = "mother", delay: int = 1) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="brave"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="helper"))
    bell = world.add(Entity(id="bell", type="instrument", label=instrument.name, attrs={"sound": instrument.sound}))
    cord = world.add(Entity(id="cord", type="thing", label=tang.name))
    child.memes["bravery"] = 2.0
    child.memes["hope"] = 1.0
    child.memes["defiance"] = 0.0

    world.say(f"{child_name} stood on the stage at {setting.place}, where songs could bob and swing.")
    world.say(f"{setting.rhyme_tag} with {instrument.phrase}, the day felt bright and all in a ring.")
    world.say(f'"If I ring it just right, I will make the optimum sound," {child_name} said with delight.')
    world.para()
    world.say(f'But {parent.pronoun("possessive")} {parent.label_word} frowned. "{instrument.name} is not a toy, my dear; keep it in sight."')
    child.memes["defiance"] += 1
    child.memes["bravery"] += 1
    world.say(f"{child_name} felt brave and wanted to prove it, though the warning gave a slight sting.")

    if reasonableness_gate(instrument, tang) and response.sense >= SOUND_MIN:
        _do_action(world)
        world.para()
        world.say(f'The cord made a tang of trouble, and the tune turned thin and sour.')
        world.say(f"{child_name} tried to fix it alone, but the knot only grew by the hour.")
        if can_contain(response, tang, delay):
            world.say(f"Then {parent.label_word} helped neatly, and the mess was gently calmed.")
            world.say(response.text.replace("{tang}", tang.name))
            world.say(f"The ending shone soft, and the day stayed sweet and warm like jam.")
        else:
            world.say(f"Then {parent.label_word} rushed in, but {response.fail.replace('{tang}', tang.name)}")
            world.say("The bell fell quiet, the cord stayed stuck, and the song ended sad and bland.")
            child.memes["bravery"] += 1
            child.memes["loss"] += 1
            parent.memes["concern"] += 1
    else:
        raise StoryError("This setup does not make a believable dingaling-tang conflict.")

    world.facts.update(
        child=child, parent=parent, setting=setting, instrument=instrument,
        tang=tang, response=response, outcome="bad",
        conflict=child.memes["conflict"] >= THRESHOLD,
        brave=child.memes["bravery"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a small child that includes the words "{f["instrument"].name}", "optimum", and "{f["tang"].name}".',
        f"Tell a brave but troubled story where {f['child'].label_word if hasattr(f['child'], 'label_word') else f['child'].label} wants the optimum sound, but the bell-string ends in a tang and the ending is sad.",
        f'Write a short rhyming tale about bravery and conflict with a dingaling and a tangled cord.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    tang = f["tang"]
    instrument = f["instrument"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.label}, who wants to make music, and {parent.label_word}, who tries to keep the play safe."
        ),
        QAItem(
            question="Why did the conflict begin?",
            answer=f"The conflict began because {child.label} wanted the optimum sound and ignored the warning about the {instrument.name}. The bell-string got tangled, so the happy tune turned into a troublesome tang."
        ),
        QAItem(
            question="What happened at the end?",
            answer="The ending was bad. The song fell quiet, the cord stayed knotted, and the child did not get the bright happy finish hoped for at the start."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or hard without giving up. It can be good, but it still needs good sense so nobody gets hurt."
        ),
        QAItem(
            question="What is a tang in a story like this?",
            answer="A tang can mean a sharp little feel or a twisty snag. Here it means the cord got in a knot and made the music go wrong."
        ),
        QAItem(
            question="What is an optimum choice?",
            answer="An optimum choice is the best choice for the goal. It is the one that works well and causes the least trouble."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== World QA ==")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


SETTING_REGISTRY = {
    "hall": Setting(id="hall", place="the hall", sound_space="echoing hall", stage="stage", rhyme_tag="In the echoing hall", tags={"hall", "music"}),
    "yard": Setting(id="yard", place="the yard", sound_space="open yard", stage="bench", rhyme_tag="In the open yard", tags={"yard", "music"}),
}
INSTRUMENT_REGISTRY = {
    "dingaling": Instrument(id="dingaling", name="dingaling", phrase="a bright dingaling", action="ring it", sound="ding-a-ling", dangerous=True, tags={"dingaling", "music"}),
    "bell": Instrument(id="bell", name="bell", phrase="a silver bell", action="swing it", sound="clink-clink", dangerous=True, tags={"bell", "music"}),
}
TANG_REGISTRY = {
    "tang": TangledThing(id="tang", name="tang", phrase="a twisty tang", snag="snag", spread=2, tangled=True, tags={"tang", "conflict"}),
    "knot": TangledThing(id="knot", name="knot", phrase="a tight knot", snag="knot", spread=2, tangled=True, tags={"knot", "conflict"}),
}
RESPONSES = {
    "help": Response(id="help", sense=3, power=1, text="the parent untwisted the cord and helped the song come back", fail="could not untangle the cord in time", tags={"help"}),
    "slow": Response(id="slow", sense=2, power=2, text="the parent slowed the swing, took a breath, and smoothed the knot", fail="was too late to slow the swing", tags={"slow"}),
    "pick_up": Response(id="pick_up", sense=1, power=1, text="lifted the bell away and kept everyone safe", fail="could not lift it away fast enough", tags={"pick_up"}),
}

@dataclass
class StoryParams:
    setting: str
    instrument: str
    tang: str
    response: str
    child_name: str
    child_type: str
    parent_type: str
    delay: int = 1
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


CURATED = [
    StoryParams(
        setting="hall",
        instrument="dingaling",
        tang="tang",
        response="help",
        child_name="Mina",
        child_type="girl",
        parent_type="mother",
        delay=1,
    ),
    StoryParams(
        setting="yard",
        instrument="bell",
        tang="knot",
        response="slow",
        child_name="Arlo",
        child_type="boy",
        parent_type="father",
        delay=2,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTING_REGISTRY.items():
        for iid, instr in INSTRUMENT_REGISTRY.items():
            for tid, tg in TANG_REGISTRY.items():
                if reasonableness_gate(instr, tg):
                    combos.append((sid, iid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about dingaling, optimum, tang, bravery, and a bad ending.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--instrument", choices=INSTRUMENT_REGISTRY)
    ap.add_argument("--tang", choices=TANG_REGISTRY)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.instrument and args.tang:
        instr = INSTRUMENT_REGISTRY[args.instrument]
        tg = TANG_REGISTRY[args.tang]
        if not reasonableness_gate(instr, tg):
            raise StoryError("This story needs a dangerous dingaling and a tangled tang to make a real conflict.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.instrument is None or c[1] == args.instrument)
              and (args.tang is None or c[2] == args.tang)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, instrument, tang = rng.choice(sorted(combos))
    response = args.response or rng.choice(list(RESPONSES))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(["Mina", "Arlo", "Tia", "Jude"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting,
        instrument=instrument,
        tang=tang,
        response=response,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.instrument not in INSTRUMENT_REGISTRY:
        raise StoryError(f"Unknown instrument: {params.instrument}")
    if params.tang not in TANG_REGISTRY:
        raise StoryError(f"Unknown tang: {params.tang}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")

    world = tell(
        setting=SETTING_REGISTRY[params.setting],
        instrument=INSTRUMENT_REGISTRY[params.instrument],
        tang=TANG_REGISTRY[params.tang],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent_type,
        delay=params.delay,
    )
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


ASP_RULES = r"""
dangerous(I) :- instrument(I).
tangled(T) :- tang(T).
valid(S,I,T) :- setting(S), instrument(I), tang(T), dangerous(I), tangled(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for iid in INSTRUMENT_REGISTRY:
        lines.append(asp.fact("instrument", iid))
        if INSTRUMENT_REGISTRY[iid].dangerous:
            lines.append(asp.fact("dangerous", iid))
    for tid in TANG_REGISTRY:
        lines.append(asp.fact("tang", tid))
        if TANG_REGISTRY[tid].tangled:
            lines.append(asp.fact("tangled", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if a - b:
            print("  only in ASP:", sorted(a - b))
        if b - a:
            print("  only in Python:", sorted(b - a))

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample)
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

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
        print(f"{len(combos)} compatible combos:")
        for s, i, t in combos:
            print(f"  {s} {i} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
