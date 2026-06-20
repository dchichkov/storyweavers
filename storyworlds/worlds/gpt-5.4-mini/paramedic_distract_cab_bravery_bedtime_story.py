#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/paramedic_distract_cab_bravery_bedtime_story.py
================================================================================

A small bedtime-story world about a brave child, a cab ride, and a paramedic
who arrives to help after a scary little mishap. The core premise is simple:
nighttime travel becomes frightening, a child uses bravery to distract a worried
passenger, and a calm paramedic turns the moment into a safe ending.

The domain is intentionally narrow and state-driven:
- a child and a younger companion are riding in a cab at night,
- something small goes wrong near the curb,
- a paramedic helps,
- the brave child distracts the scared companion until the worry settles,
- the final image proves the ride ended safely.

This script is standalone, stdlib-only, and follows the Storyweavers contract.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
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
class Setting:
    id: str
    place: str
    weather: str
    night: bool = True


@dataclass
class Trigger:
    id: str
    event: str
    risk: str
    note: str
    serious: bool = False


@dataclass
class Response:
    id: str
    text: str
    qa_text: str
    power: int
    sense: int


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    utility: str


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["startled"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["bravery"] < THRESHOLD:
            continue
        sig = ("bravery", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["calm"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("bravery", _r_bravery)]


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


def should_call_paramedic(trigger: Trigger) -> bool:
    return trigger.serious


def outcome_of(trigger: Trigger) -> str:
    return "helped" if trigger.serious else "oops"


def _do_trigger(world: World, trigger: Trigger, narrate: bool = True) -> None:
    child = world.get("child")
    companion = world.get("companion")
    child.meters["startled"] += 1
    companion.meters["hurt"] += 1
    if trigger.serious:
        world.get("street").meters["concern"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, trigger: Trigger, response: Response, comfort: Comfort,
         child_name: str = "Mia", child_gender: str = "girl",
         companion_name: str = "Ben", companion_gender: str = "boy",
         parent_name: str = "Mom", parent_gender: str = "girl") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent", label="the parent"))
    paramedic = world.add(Entity(id="paramedic", kind="character", type="woman", role="helper", label="the paramedic"))
    cab = world.add(Entity(id="cab", type="thing", label="the cab"))
    street = world.add(Entity(id="street", type="place", label="the curb"))
    world.facts["cab"] = cab
    world.facts["comfort"] = comfort
    world.facts["trigger"] = trigger
    world.facts["response"] = response
    world.facts["parent"] = parent
    world.facts["paramedic"] = paramedic

    child.memes["bravery"] = 2.0
    companion.memes["fear"] = 0.0
    child.attrs["comfort"] = comfort.label

    world.say(
        f"On a soft night, {child.id} and {companion.id} rode home in a cab while "
        f"{setting.weather} rain tapped gently on the windows. {child.id} hugged "
        f"{comfort.phrase} and watched the street lights blink by."
    )
    world.say(
        f"{child.id} was trying to be brave, because the dark city felt big and new. "
        f"{companion.id} stayed close and whispered, \"I'm a little scared.\""
    )

    world.para()
    world.say(
        f"Then the cab slowed by the curb, and a bumping little mishap made "
        f"{companion.id} stumble when the door opened."
    )
    _do_trigger(world, trigger, narrate=False)
    world.say(
        f"{companion.id} winced and held {companion.pronoun('possessive')} ankle. "
        f"{child.id}'s heart jumped, but {child.id} took a breath and stood tall."
    )

    if should_call_paramedic(trigger):
        world.para()
        world.say(
            f"{child.id} waved to a passing paramedic, and the paramedic knelt by the cab "
            f"with a calm smile. {parent.id} stayed close while {child.id} tried to distract "
            f"{companion.id} with a tiny story about the moon."
        )
        child.memes["bravery"] += 1
        companion.memes["fear"] += 1
        world.say(
            f'\"Look,\" {child.id} said softly, \"the moon is a silver coin and the clouds '
            f'are sleep blankets.\" {companion.id} sniffled, then listened.'
        )
        companion.memes["fear"] = 0.0
        world.say(
            f"The paramedic checked the ankle, wrapped it neatly, and said it would be "
            f"all right. The cab waited quietly, and the whole street seemed to breathe again."
        )
        world.para()
        world.say(
            f"By the time the ride started again, {companion.id} was leaning on {child.id}'s "
            f"{comfort.label}, and {child.id} felt brave enough to smile at the dark."
        )
        world.say(
            f"At home, {parent.id} tucked them into bed, and the cab's red tail lights "
            f"glowed like two little embers disappearing down the street."
        )
        ending = "helped"
    else:
        world.para()
        world.say(
            f"{child.id} did not need to call anyone, and the cab rolled on in the quiet night."
        )
        world.say(
            f"{companion.id} kept holding the {comfort.label}, and {child.id} kept watch "
            f"until the house came into view."
        )
        ending = "calm"

    world.facts.update(
        child=child,
        companion=companion,
        setting=setting,
        ending=ending,
        outcome=outcome_of(trigger),
    )
    return world


SETTINGS = {
    "rainy_street": Setting("rainy_street", "the street", "gentle"),
    "sleepy_avenue": Setting("sleepy_avenue", "the avenue", "warm"),
}

TRIGGERS = {
    "stub_toe": Trigger("stub_toe", "stubbed a toe", "pain", "a little curb bump", serious=True),
    "scared_sound": Trigger("scared_sound", "heard a scary sound", "fear", "a clatter by the door", serious=False),
}

RESPONSES = {
    "wrap_ankle": Response(
        "wrap_ankle",
        "wrapped the ankle and checked it carefully",
        "wrapped the ankle and checked it carefully",
        3,
        3,
    ),
    "reassure": Response(
        "reassure",
        "smiled and said it was going to be all right",
        "smiled and said it was going to be all right",
        1,
        2,
    ),
}

COMFORTS = {
    "teddy": Comfort("teddy", "teddy bear", "a soft teddy bear", "comfort"),
    "blanket": Comfort("blanket", "blanket", "a small blanket", "comfort"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Rose"]
BOY_NAMES = ["Ben", "Tom", "Leo", "Noah", "Max"]


@dataclass
class StoryParams:
    setting: str
    trigger: str
    response: str
    comfort: str
    child: str
    child_gender: str
    companion: str
    companion_gender: str
    parent: str
    parent_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TRIGGERS:
            for r in RESPONSES:
                combos.append((s, t, r))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    comp = f["companion"]
    trig = f["trigger"]
    return [
        f'Write a bedtime story for a young child that includes the words "paramedic", "cab", and "distract".',
        f"Tell a gentle nighttime story where {child.id} rides in a cab, helps {comp.id}, and a paramedic comes to help after a small scare.",
        f"Write a calm story about bravery where a child distracts a worried companion while a paramedic tends a small injury beside a cab.",
        f"Make the ending cozy and safe, with the cab ride becoming calm again after {trig.note}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    comp = f["companion"]
    parent = f["parent"]
    paramedic = f["paramedic"]
    trigger = f["trigger"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {comp.id}, and {parent.id}, with a paramedic who helps when the ride turns scary."),
        ("What happened near the cab?",
         f"{comp.id} got hurt a little near the curb, and {child.id} became brave enough to keep the moment calm. That is why the cab scene changed from ordinary travel into a small emergency."),
        ("What did {0} do to help {1}?".format(child.id, comp.id),
         f"{child.id} tried to distract {comp.id} with a moon story until the paramedic finished checking the ankle. The distraction helped {comp.id} stop worrying and listen."),
    ]
    if f["ending"] == "helped":
        qa.append((
            "How did the paramedic help?",
            f"The paramedic checked the ankle, wrapped it neatly, and said it would be all right. Because the help was calm and quick, the cab ride could continue safely."
        ))
        qa.append((
            "How did bravery matter in the story?",
            f"{child.id} felt scared but still spoke up, waved for help, and distracted {comp.id}. That bravery kept everyone calm until the paramedic arrived."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    trigger = f["trigger"]
    out = [
        ("What is a paramedic?",
         "A paramedic is a trained helper who comes to people in an emergency and gives first aid before they get more help."),
        ("What is a cab?",
         "A cab is a car that gives people a ride from one place to another, often in a city."),
        ("What does it mean to distract someone?",
         "To distract someone means to help move their mind away from fear or worry by giving them something calm to think about."),
        ("Why is bravery useful?",
         "Bravery helps a person stay kind and helpful even when they feel nervous or scared."),
    ]
    if trigger.serious:
        out.append((
            "Why should someone call a paramedic for an injury?",
            "A paramedic can check the injury and help keep it from getting worse. Quick help is important when someone is hurt."
        ))
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rainy_street", "stub_toe", "wrap_ankle", "teddy", "Mia", "girl", "Ben", "boy", "Mom", "girl"),
    StoryParams("sleepy_avenue", "stub_toe", "reassure", "blanket", "Leo", "boy", "Nora", "girl", "Dad", "boy"),
]


def explain_rejection(trigger: Trigger) -> str:
    return f"(No story: this tiny world only tells bedtime scenes with a clear little emergency or scare; {trigger.note} does not fit the chosen shape.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TRIGGERS.items():
        lines.append(asp.fact("trigger", tid))
        if t.serious:
            lines.append(asp.fact("serious", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, R) :- setting(S), trigger(T), response(R).
helped(T) :- trigger(T), serious(T).
outcome(helped) :- helped(T).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print(" only in python:", sorted(py - cl))
        print(" only in clingo:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: paramedic, cab, bravery, and a gentle distraction.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["girl", "boy"])
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
    if args.trigger and args.trigger not in TRIGGERS:
        raise StoryError("(Unknown trigger.)")
    setting = args.setting or rng.choice(list(SETTINGS))
    trigger = args.trigger or rng.choice(list(TRIGGERS))
    response = args.response or rng.choice(list(RESPONSES))
    comfort = args.comfort or rng.choice(list(COMFORTS))

    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or ("boy" if child_gender == "girl" else "girl")
    parent_gender = args.parent_gender or rng.choice(["girl", "boy"])

    child_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    companion_pool = BOY_NAMES if companion_gender == "boy" else GIRL_NAMES
    parent_pool = GIRL_NAMES if parent_gender == "girl" else BOY_NAMES

    child = args.child or rng.choice(child_pool)
    companion_choices = [n for n in companion_pool if n != child] or companion_pool
    companion = args.companion or rng.choice(companion_choices)
    parent = args.parent or rng.choice(parent_pool)

    return StoryParams(setting, trigger, response, comfort, child, child_gender, companion, companion_gender, parent, parent_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TRIGGERS[params.trigger],
        RESPONSES[params.response],
        COMFORTS[params.comfort],
        params.child,
        params.child_gender,
        params.companion,
        params.companion_gender,
        params.parent,
        params.parent_gender,
    )
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
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, trigger, response) combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.child} / {p.trigger} / {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
