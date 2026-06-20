#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grate_suspense_folk_tale.py
===========================================================

A standalone story world for a tiny folk-tale style suspense domain.

Premise:
- A child and a helper are in an old cottage.
- A low grate in the floor or wall conceals a small hidden place.
- Suspense comes from a strange sound, a missing key, or a trapped breeze.
- The helper predicts the risk, chooses a safe method, and the ending proves the place changed.

This world is intentionally small and state-driven:
typed entities carry physical meters and emotional memes, the simulated world
drives the prose, and QA is grounded in the generated world state.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



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
    mood: str
    hiding_spot: str
    sound: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Mystery:
    id: str
    label: str
    hidden_item: str
    risk: str
    clue: str
    danger: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
            value = __import__("collections").defaultdict(float)
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


def _r_unease(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["strange"] < THRESHOLD:
            continue
        sig = ("unease", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in list(world.entities.values()):
            if e.role in {"child", "helper"}:
                e.memes["worry"] += 1
        out.append("__unease__")
    return out


def _r_release(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["opened"] < THRESHOLD:
            continue
        sig = ("release", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["blocked"] = 0.0
        out.append(f"The hidden place breathed out at last.")
    return out


CAUSAL_RULES = [Rule("unease", "social", _r_unease), Rule("release", "physical", _r_release)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_response(resp: Response) -> bool:
    return resp.sense >= SENSE_MIN


def predict_opening(world: World, target_id: str) -> dict:
    sim = world.copy()
    sim.get(target_id).meters["opened"] += 1
    propagate(sim, narrate=False)
    target = sim.get(target_id)
    return {"opened": target.meters["opened"] >= THRESHOLD, "worry": sum(e.memes["worry"] for e in sim.entities.values())}


def tell(setting: Setting, mystery: Mystery, response: Response, child_name: str,
         child_gender: str, helper_name: str, helper_gender: str, elder_name: str,
         elder_gender: str, delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder", label="the old teller"))
    grate = world.add(Entity(id="grate", type="thing", label="the grate"))
    hidden = world.add(Entity(id="hidden", type="thing", label=mystery.hidden_item))
    child.memes["curiosity"] = 1.0
    helper.memes["calm"] = 1.0

    world.say(
        f"In an old cottage by the lane, {child.id} and {helper.id} listened to {setting.mood} while the wind slipped through {setting.hiding_spot}."
    )
    world.say(
        f"Near the hearth sat {setting.place}, and under it the {mystery.label} made a soft sound like someone tapping from far away."
    )
    world.say(
        f'"Did you hear that?" {child.id} whispered. {helper.id} nodded and leaned closer, because folk tales grow quiet before they grow strange.'
    )

    world.para()
    child.memes["fear"] += 1
    helper.memes["worry"] += 1
    world.say(
        f'{child.id} wanted to lift the {mystery.label} at once, but {helper.id} had a steadier thought. '
        f'"If we rush, we may miss the clue," {helper.id} said, watching the dark seam around the grate.'
    )
    pred = predict_opening(world, "hidden")
    world.facts["predicted_worry"] = pred["worry"]
    world.facts["mystery"] = mystery
    world.facts["setting"] = setting
    world.facts["response"] = response
    world.facts["delay"] = delay
    if delay > 0:
        hidden.meters["strange"] += float(delay)

    if not reasonable_response(response):
        raise StoryError(f"(Refusing response '{response.id}': too weak for a suspense story.)")

    world.para()
    if pred["worry"] >= 1:
        world.say(
            f'{helper.id} fetched a lantern and the old key from the shelf. '
            f'{helper.id} said the grate might hide a draft, or something caught behind it, and it was wiser to open it slowly.'
        )
    else:
        world.say(
            f'{helper.id} touched the cool iron and smiled a little. '
            f'There was danger in the waiting, but also a puzzle, and puzzles needed care.'
        )

    world.para()
    grate.meters["opened"] += 1
    hidden.meters["opened"] += 1
    hidden.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{mystery.clue} Then {helper.id} used {response.text.replace('{target}', mystery.label)}."
    )
    world.say(
        f"The grate gave way with a small creak, and the hidden place was no longer shut tight."
    )

    world.para()
    if hidden.meters["opened"] >= THRESHOLD:
        world.say(
            f"Inside, they found {mystery.hidden_item}, not a monster at all, but the thing that had been trapped behind the iron."
        )
        world.say(
            f"{elder.id} smiled from the doorway. '{response.qa_text.replace('{target}', mystery.label)},' {elder.id} said, and the room felt warm again."
        )
    else:
        world.say(
            f"The grate still held fast, but the sound had changed; the children knew now that the mystery was not cruel, only stuck."
        )

    world.para()
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In the end, {child.id} and {helper.id} left the cottage with the lantern shining on the path, and the grate behind them no longer seemed scary."
    )

    world.facts.update(child=child, helper=helper, elder=elder, grate=grate, hidden=hidden, outcome="opened")
    return world


SETTINGS = {
    "cottage": Setting("cottage", "the old cottage", "a hush of winter", "the stones", "a tapping sound"),
    "mill": Setting("mill", "the old mill", "a hush of river water", "the floorboards", "a low rattling"),
    "barn": Setting("barn", "the old barn", "a hush of straw and mice", "the rafters", "a little rustle"),
}

MYSTERIES = {
    "wind": Mystery("wind", "grate", "a hidden bird nest", "a draft", "a bit of moss and straw", "the grate could jam the nest", tags={"grate", "wind"}),
    "treasure": Mystery("treasure", "grate", "a tin box of old coins", "a loose board", "a rusty ring key", "the grate might hide a secret room", tags={"grate", "treasure"}),
    "candle": Mystery("candle", "grate", "a candle stub", "a stuck latch", "a warm puff of smoke", "the grate could hide a fire danger", tags={"grate", "candle"}),
}

RESPONSES = {
    "lantern": Response("lantern", 3, 3, "lifted the lantern higher and peered through the bars", "shook the lantern, but the dark stayed dark", "lifted the lantern higher and peered through the bars", tags={"light"}),
    "key": Response("key", 3, 4, "slid the old key into the side latch and turned it gently", "tried the key, but the latch would not budge", "slid the old key into the side latch and turned it gently", tags={"key"}),
    "brush": Response("brush", 2, 2, "used a stiff brush to sweep the grit away from the edge", "brushed at the edge, but the seam stayed clogged", "used a stiff brush to sweep the grit away from the edge", tags={"brush"}),
    "breathe": Response("breathe", 1, 1, "waited and breathed slowly until the hidden place seemed less tight", "waited, but waiting alone did not open it", "waited and breathed slowly until the hidden place seemed less tight", tags={"calm"}),
}

GIRL_NAMES = ["Mara", "Elsa", "Anya", "Nina", "Tessa", "Rosa"]
BOY_NAMES = ["Jon", "Oren", "Perrin", "Milo", "Rafe", "Cedric"]
TRAITS = ["careful", "curious", "quiet", "brave", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for rid, resp in RESPONSES.items():
                if reasonable_response(resp):
                    combos.append((sid, mid, rid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    elder: str
    elder_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


KNOWLEDGE = {
    "grate": [("What is a grate?", "A grate is a piece of iron with bars that lets air or water through while keeping larger things out.")],
    "lantern": [("What is a lantern?", "A lantern is a light you can carry so you can see in the dark.")],
    "key": [("What does a key do?", "A key opens a lock, which can help turn something that is shut into something open.")],
    "calm": [("Why is it good to stay calm?", "Staying calm helps you think clearly and choose a safe plan instead of rushing.")],
}
KNOWLEDGE_ORDER = ["grate", "lantern", "key", "calm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a suspenseful folk tale for a young child that includes the word "grate" and an old cottage mystery.',
        f"Tell a gentle suspense story where {f['child'].id} and {f['helper'].id} hear a strange sound by a grate and solve it carefully.",
        f"Write a folk-tale scene with a creaking grate, a worried child, and a calm helper who opens a hidden place safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, elder, mystery, response = f["child"], f["helper"], f["elder"], f["mystery"], f["response"]
    qa = [
        QAItem(f"Who are the main characters?", f"The main characters are {child.id} and {helper.id}, with {elder.id} as the old teller who helps at the end."),
        QAItem("What made the story feel suspenseful?", f"The suspense came from the strange sound near the grate and the waiting before anyone knew what was trapped behind it."),
        QAItem("How did the helper act?", f"{helper.id} stayed calm and chose a careful way to open the hidden place instead of rushing."),
        QAItem("What changed by the end?", f"The hidden place was opened safely, and the scary little sound turned out to be something trapped behind the grate."),
    ]
    qa.append(QAItem(
        f"What did {helper.id} do to solve the mystery?",
        f"{helper.id} used {response.qa_text} so the grate could be opened without causing harm. That careful method let the children find out what was inside."
    ))
    if f["hidden"].meters["opened"] >= THRESHOLD:
        qa.append(QAItem(
            "What was behind the grate?",
            f"Behind the grate was {mystery.hidden_item}. It had been hidden from view, which is why the sound seemed so mysterious."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["response"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cottage", "wind", "lantern", "Mara", "girl", "Jon", "boy", "Grandma", "grandmother", "careful", 0),
    StoryParams("mill", "treasure", "key", "Cedric", "boy", "Anya", "girl", "Grandpa", "grandfather", "patient", 1),
    StoryParams("barn", "candle", "brush", "Nina", "girl", "Milo", "boy", "Grandma", "grandmother", "quiet", 0),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def outcome_of(params: StoryParams) -> str:
    return "opened"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("topic", mid, t))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S, M, R) :- setting(S), mystery(M), sensible(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid_combos()")
        rc = 1
    if set(asp_sensible()) == {r for r, rr in RESPONSES.items() if rr.sense >= SENSE_MIN}:
        print("OK: sensible responses match.")
    else:
        print("MISMATCH in sensible responses.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, response=None, child=None, child_gender=None, helper=None, helper_gender=None, elder=None, elder_gender=None, trait=None, delay=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke-tested generation.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspenseful folk-tale grate world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["grandmother", "grandfather"])
    ap.add_argument("--trait", choices=["careful", "curious", "quiet", "brave", "patient"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, response = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    elder_gender = args.elder_gender or rng.choice(["grandmother", "grandfather"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != child])
    elder = args.elder or (rng.choice(["Grandma", "Grandpa"]))
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, mystery, response, child, child_gender, helper, helper_gender, elder, elder_gender, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], RESPONSES[params.response],
                 params.child, params.child_gender, params.helper, params.helper_gender,
                 params.elder, params.elder_gender, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, m, r in asp_valid_combos():
            print(f"  {s:8} {m:8} {r}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
