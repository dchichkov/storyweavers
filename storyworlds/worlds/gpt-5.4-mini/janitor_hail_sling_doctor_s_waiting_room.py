#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/janitor_hail_sling_doctor_s_waiting_room.py
=============================================================================

A standalone story world sketch for a small, child-facing tale set in a doctor's
waiting room: a child, a janitor, a mistaken hailstorm of noise, a sling, and a
twist that turns worry into a calm cleanup. The domain keeps a pirate-tale feel:
the waiting room becomes a ship's cabin, sound effects drum the action forward,
and a final twist proves what changed.

The world is intentionally tiny and constraint-checked:
- typed entities with meters and memes
- state-driven prose, not template swapping
- a Python reasonableness gate and an inline ASP twin
- three QA sets grounded in world state
- verify mode that checks parity and runs a smoke test
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "damage": 0.0, "noise": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "joy": 0.0, "calm": 0.0, "twist": 0.0}

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
        return {"mother": "mom", "father": "dad", "janitor": "janitor", "doctor": "doctor"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    scene: str
    pirate_frame: str
    twist_line: str

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
class Hail:
    id: str
    label: str
    sound: str
    mess: str
    cold: str
    wet: bool = True

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
class Sling:
    id: str
    label: str
    phrase: str
    reason: str
    safe: bool = True
    fragile: bool = True

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _r_wet_floor(world: World) -> list[str]:
    out = []
    jan = world.entities.get("janitor")
    hail = world.entities.get("hail")
    if not jan or not hail:
        return out
    if hail.meters["wet"] < THRESHOLD:
        return out
    sig = ("wet_floor",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jan.memes["calm"] += 1
    out.append("The tiles gleamed slick and cold.")
    return out


def _r_noise(world: World) -> list[str]:
    out = []
    room = world.entities.get("room")
    if not room:
        return out
    if room.meters["noise"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.memes["twist"] += 1
    out.append("The whole waiting room seemed to hold its breath.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_wet_floor, _r_noise):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard(hail: Hail, sling: Sling) -> bool:
    return hail.wet and sling.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def resolve_sound(world: World, hail: Hail) -> None:
    world.say(f"{hail.sound} the hail tapped the window like tiny drumsticks.")


def setup(world: World, child: Entity, janitor: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a gray afternoon, {child.id} and {janitor.id} turned the doctor's waiting room "
        f"into {setting.scene}. {setting.pirate_frame}"
    )


def introduce_hail(world: World, child: Entity, hail: Hail) -> None:
    child.memes["fear"] += 1
    world.say(
        f"Outside the glass, {hail.label} rattled down. {hail.sound} went the little stones, "
        f"and the room felt like a ship in a storm."
    )


def notice_sling(world: World, child: Entity, sling: Sling) -> None:
    world.say(
        f"The child noticed {sling.phrase} resting by the chair. It was there because someone "
        f"at the clinic needed it to rest still."
    )


def twist_warning(world: World, janitor: Entity, child: Entity, hail: Hail, sling: Sling) -> None:
    janitor.memes["calm"] += 1
    world.say(
        f'{janitor.id} tipped {janitor.pronoun("possessive")} head and said, '
        f'"Listen close. That sling is not for swinging, and {hail.label} makes the floor slick. '
        f'We need a careful plan, matey."'
    )


def defy(world: World, child: Entity) -> None:
    child.memes["twist"] += 1
    world.say(f'The child grinned anyway. "I can make this a game!"')


def slip_event(world: World, child: Entity, sling: Sling, hail: Hail) -> None:
    child.meters["wet"] += 1
    child.meters["damage"] += 1
    room = world.get("room")
    room.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Whoop! The sling slipped from careful hands with a soft {hail.sound}, and the child "
        f"nearly slid on the wet floor."
    )


def rescue(world: World, janitor: Entity, child: Entity, response: Response, sling: Sling) -> None:
    sling_ok = response.power >= 1
    if sling_ok:
        child.meters["wet"] = 0.0
    world.say(
        f"{janitor.id} came shuffling over and {response.text.replace('{sling}', sling.label)}."
    )
    world.say(
        f"The wet shine on the floor faded, and the sling stayed where it should, quiet and safe."
    )


def twist_turn(world: World, janitor: Entity, child: Entity, setting: Setting) -> None:
    child.memes["twist"] += 1
    world.say(setting.twist_line)
    world.say(
        f"{janitor.id} showed the child how to use a towel to dry the spot, and the room stopped "
        f"feeling like a storm-tossed deck."
    )


def ending(world: World, child: Entity, janitor: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["calm"] += 1
    world.say(
        f"In the end, the child sat still, listening to the hail, while {janitor.id} kept watch "
        f"like a steady old sailor. The waiting room was quiet again."
    )


def tell(setting: Setting, hail: Hail, sling: Sling, response: Response, child_name: str,
         child_type: str = "boy", janitor_name: str = "Rosa", janitor_type: str = "janitor",
         doctor_type: str = "doctor") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    janitor = world.add(Entity(id=janitor_name, kind="character", type=janitor_type, role="janitor"))
    doctor = world.add(Entity(id="doctor", kind="character", type=doctor_type, role="doctor"))
    room = world.add(Entity(id="room", type="room", label="the waiting room"))
    world.add(Entity(id=hail.id, type="thing", label=hail.label))
    world.add(Entity(id=sling.id, type="thing", label=sling.label))

    setup(world, child, janitor, setting)
    introduce_hail(world, child, hail)
    notice_sling(world, child, sling)
    world.para()
    twist_warning(world, janitor, child, hail, sling)
    defy(world, child)
    slip_event(world, child, sling, hail)
    world.para()
    rescue(world, janitor, child, response, sling)
    twist_turn(world, janitor, child, setting)
    ending(world, child, janitor)

    world.facts.update(
        child=child, janitor=janitor, doctor=doctor, room=room,
        setting=setting, hail=hail, sling=sling, response=response,
        slipped=child.meters["damage"] >= THRESHOLD,
        wet=child.meters["wet"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "waiting_room": Setting(
        id="waiting_room",
        place="the doctor's waiting room",
        scene="a tiny pirate harbor of chairs, magazines, and a fish tank",
        pirate_frame="The chairs were ships, the magazines were maps, and the fish tank glimmered like a storm lamp.",
        twist_line="Then came the twist: the janitor had already put down a dry towel, ready like a rescue raft.",
    )
}

HAILS = {
    "hail": Hail("hail", "hail", "tap-tap-tap", "wet", "cold"),
}

SLINGS = {
    "arm_sling": Sling(
        "arm_sling",
        "sling",
        "a soft sling on the bench",
        "It was meant to hold an arm still while it healed.",
        safe=True,
        fragile=True,
    )
}

RESPONSES = {
    "towel": Response(
        "towel",
        3,
        2,
        "slid the towel under the child and dried the floor with quick, steady hands",
        "tried to dry the floor, but the water kept spreading",
        "slid the towel under the child and dried the floor",
    ),
    "bucket": Response(
        "bucket",
        1,
        1,
        "grabbed a bucket and splashed more water around",
        "made a bigger mess with the bucket",
        "grabbed a bucket",
    ),
}

GIRL_NAMES = ["Mia", "Ava", "Zoe", "Nora"]
BOY_NAMES = ["Leo", "Sam", "Finn", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for hid, hail in HAILS.items():
            for sl_id, sling in SLINGS.items():
                if hazard(hail, sling):
                    combos.append((sid, hid, sl_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    hail: str
    sling: str
    response: str
    child_name: str
    child_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: janitor, hail, sling, and a waiting-room twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hail", choices=HAILS)
    ap.add_argument("--sling", choices=SLINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def explain_rejection() -> str:
    return "(No story: the waiting-room sling and hail are the right kind of trouble here, but the chosen options don't make a sensible tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("(No story: that response is too silly for this problem.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hail is None or c[1] == args.hail)
              and (args.sling is None or c[2] == args.sling)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, hail, sling = rng.choice(combos)
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting, hail, sling, response, name, gender)


def generate(params: StoryParams) -> StorySample:
    w = tell(SETTINGS[params.setting], HAILS[params.hail], SLINGS[params.sling],
             RESPONSES[params.response], params.child_name, params.child_type)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=[QAItem(q, a) for q, a in story_qa(w)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(w)],
        world=w,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate-tale style story for a preschooler set in a doctor\'s waiting room. Include the words "janitor", "hail", and "sling".',
        f"Tell a child-facing story where {f['child'].id} sees {f['hail'].label} outside, notices a sling in the waiting room, and the janitor helps with a twist.",
        "Write a small, calm adventure with sound effects and a final twist that turns a slippery waiting room into a safe place.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    jan = f["janitor"]
    hail = f["hail"]
    sling = f["sling"]
    resp = f["response"]
    return [
        ("Who helped in the waiting room?", f"The janitor helped. {jan.id} stayed calm, used a careful response, and kept the room safe."),
        ("What made the child worry?", f"The hail outside made the room feel stormy, and the sling was tempting to touch. That is why the child needed a reminder to stay careful."),
        ("What was the sling for?", f"It was meant to hold an arm still while it healed. That makes it something for resting, not for swinging like a toy."),
        ("How did the story end?", f"It ended safely, with the floor dried, the sling left in place, and the child calmer than before. The twist was that the janitor was ready all along."),
        ("What did the janitor do after the child slipped?", f"{jan.id} used {resp.qa_text}. That fixed the slippery spot and turned the scary moment into a safe one."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    out.append(("What does a janitor do?", "A janitor cleans rooms and keeps floors safe and tidy. They help stop messes from becoming a problem."))
    out.append(("What is hail?", "Hail is hard little balls of ice that fall from the sky during a storm. They can sound loud when they hit windows."))
    out.append(("What is a sling?", "A sling is a cloth support for an arm or hand that needs to rest and heal. It helps keep the injury still."))
    out.append(("What are sound effects?", "Sound effects are extra words that let a story sound loud, soft, or stormy. They help you hear the action in your head."))
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(H, S) :- hail(H), sling(S).
valid(W, H, S) :- setting(W), hail(H), sling(S), hazard(H, S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HAILS:
        lines.append(asp.fact("hail", hid))
    for sid in SLINGS:
        lines.append(asp.fact("sling", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    return [rid for rid, r in RESPONSES.items() if r.sense >= 2]


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python gate.")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hail=None, sling=None, response=None, name=None, gender=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it is too weak or silly for this story.)" if r.sense < 2 else ""


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
    StoryParams("waiting_room", "hail", "arm_sling", "towel", "Mia", "girl"),
    StoryParams("waiting_room", "hail", "arm_sling", "towel", "Leo", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate-tale style story for a preschooler set in a doctor\'s waiting room. Include the words "janitor", "hail", and "sling".',
        f"Tell a child-facing story where {f['child'].id} sees {f['hail'].label} outside, notices a sling in the waiting room, and the janitor helps with a twist.",
        "Write a small, calm adventure with sound effects and a final twist that turns a slippery waiting room into a safe place.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    jan = f["janitor"]
    hail = f["hail"]
    sling = f["sling"]
    resp = f["response"]
    return [
        ("Who helped in the waiting room?", f"The janitor helped. {jan.id} stayed calm, used a careful response, and kept the room safe."),
        ("What made the child worry?", f"The hail outside made the room feel stormy, and the sling was tempting to touch. That is why the child needed a reminder to stay careful."),
        ("What was the sling for?", f"It was meant to hold an arm still while it healed. That makes it something for resting, not for swinging like a toy."),
        ("How did the story end?", f"It ended safely, with the floor dried, the sling left in place, and the child calmer than before. The twist was that the janitor was ready all along."),
        ("What did the janitor do after the child slipped?", f"{jan.id} used {resp.qa_text}. That fixed the slippery spot and turned the scary moment into a safe one."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a janitor do?", "A janitor cleans rooms and keeps floors safe and tidy. They help stop messes from becoming a problem."),
        ("What is hail?", "Hail is hard little balls of ice that fall from the sky during a storm. They can sound loud when they hit windows."),
        ("What is a sling?", "A sling is a cloth support for an arm or hand that needs to rest and heal. It helps keep the injury still."),
        ("What are sound effects?", "Sound effects are extra words that let a story sound loud, soft, or stormy. They help you hear the action in your head."),
    ]


if __name__ == "__main__":
    main()
