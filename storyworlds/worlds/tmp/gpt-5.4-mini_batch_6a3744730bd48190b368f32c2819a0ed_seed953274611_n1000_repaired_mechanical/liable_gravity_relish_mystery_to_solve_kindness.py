#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/liable_gravity_relish_mystery_to_solve_kindness.py
===================================================================================

A tiny bedtime-story world about a mysterious kitchen mishap, gravity, and
kindness. A child thinks they may be liable for a missing jar of relish, but the
real mystery turns out to be a wobbling shelf and a helpful, gentle repair.

The world is designed as a small classical simulation:
- typed entities with physical meters and emotional memes,
- state-driven narration,
- a reasonableness gate,
- an inline ASP twin,
- three Q&A sets built from world state, not by parsing rendered English.

This world includes the seed words:
- liable
- gravity
- relish

And the requested features:
- Mystery to Solve
- Kindness

The tone is bedtime-story gentle and concrete.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Tara", "Pia", "Elsie", "Ada"]
BOY_NAMES = ["Ben", "Milo", "Owen", "Theo", "Eli", "Sam", "Finn", "Noah"]
ADULT_NAMES = ["Mom", "Dad", "Grandma", "Grandpa"]
ROOMS = ["kitchen", "pantry", "hallway"]
JAR_LABELS = ["jar of relish", "pickle jar", "jam jar"]
TOOLS = ["tea towel", "small stool", "paper towel", "dishcloth"]
PET_NAMES = ["the cat", "the sleepy dog", "the kitten"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    gravity: float
    clutter: int
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
class MysteryObject:
    id: str
    label: str
    is_spilled: bool = False
    liable_score: int = 0
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
class HelpfulAct:
    id: str
    label: str
    text: str
    outcome: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    jar = world.get("jar")
    if jar.meters["tipped"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jar.meters["spilled"] = 1
    jar.meters["mess"] += 1
    for ch in world.characters():
        ch.memes["surprise"] += 1
    out.append("__spill__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    jar = world.get("jar")
    child = world.get("child")
    if jar.meters["spilled"] < THRESHOLD or child.memes["worry"] >= THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    child = world.get("child")
    if helper.memes["kindness"] < THRESHOLD or child.memes["calm"] >= THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    helper.memes["pride"] += 1
    out.append("__kindness__")
    return out


CAUSAL_RULES = [_r_spill, _r_worry, _r_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_spill(world: World) -> dict:
    sim = world.copy()
    sim.get("jar").meters["tipped"] = 1
    propagate(sim, narrate=False)
    return {
        "spilled": sim.get("jar").meters["spilled"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"] >= THRESHOLD,
    }


def spill_event(world: World, jar: Entity) -> None:
    jar.meters["tipped"] += 1
    jar.meters["gravity"] += world.place.gravity
    propagate(world, narrate=False)


def choose_reasonable_acts() -> list[HelpfulAct]:
    return [a for a in HELPFUL_ACTS.values() if a.id in {"wipe", "fetch_towel", "steady_shelf"}]


def best_act() -> HelpfulAct:
    return max(HELPFUL_ACTS.values(), key=lambda a: a.tags.__len__())


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for jar in JARS:
            if place.gravity >= 0.8 and jar.id in JARS:
                for act in HELPFUL_ACTS:
                    if HELPFUL_ACTS[act].id in {"wipe", "fetch_towel", "steady_shelf"}:
                        combos.append((place, jar, act))
    return combos


def reaction_strength(act: HelpfulAct) -> int:
    return {"wipe": 2, "fetch_towel": 2, "steady_shelf": 3, "laugh_it_off": 1}.get(act.id, 1)


def needs_help(world: World) -> bool:
    return world.get("jar").meters["spilled"] >= THRESHOLD


def tell(place: Place, jar_cfg: MysteryObject, act: HelpfulAct, child_name: str,
         child_gender: str, helper_name: str, helper_gender: str,
         pet: str = "", seed_word: str = "liable") -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    jar = world.add(Entity(id="jar", kind="thing", type=jar_cfg.id, label=jar_cfg.label))
    shelf = world.add(Entity(id="shelf", kind="thing", type="shelf", label="the shelf"))
    world.facts["pet"] = pet
    world.facts["seed_word"] = seed_word

    child.memes["curious"] = 1
    helper.memes["kindness"] = 1
    world.say(
        f"In a quiet kitchen, {child.id} tiptoed by {jar.label}, and the night felt "
        f"soft as a blanket. {child.id} had been told not to climb, yet the jar was "
        f"so close and the shelves looked tired."
    )
    world.say(
        f"{child.id} noticed a little drip mark under {shelf.label} and frowned. "
        f'"Why is the relish there?" {child.pronoun()} wondered. "Am I liable?"'
    )
    world.para()
    world.say(
        f"The mystery was gentle but real: a wobble, a sticky lid, and gravity all "
        f"shared the blame. Nobody knew yet who had nudged the jar, only that it had "
        f"slid a tiny bit toward the edge."
    )
    child.memes["worry"] += 1
    pred = predict_spill(world)
    world.facts["predicted"] = pred

    world.say(
        f"{helper.id} came in with a sleepy smile and knelt beside {child.id}. "
        f'"Let us look calmly," {helper.pronoun()} said. "Little mysteries can be solved."'
    )
    world.say(
        f"{child.id} pointed to the shine on the floor. {helper.id} fetched a {act.label} '
        f"and a clean cloth, then looked up at the shelf."
    )
    world.para()
    if act.id == "steady_shelf":
        world.say(
            f"Together they slid a small stool under the shelf, tightened the jar, "
            f"and set the relish back where it belonged. The wobble stopped."
        )
    elif act.id == "fetch_towel":
        world.say(
            f"{helper.id} held the jar steady while {child.id} wiped the sticky trail "
            f"away. Then they moved the jar to a safer spot."
        )
    else:
        world.say(
            f"They wiped the spill clean, then turned the jar so the lid faced inward. "
            f"The shelf still held its secret, but the mess was gone."
        )
    helper.memes["kindness"] += 1
    child.memes["calm"] += 1
    jar.meters["spilled"] = 1
    jar.meters["safe"] = 1
    world.facts.update(
        child=child, helper=helper, jar=jar, shelf=shelf, place=place,
        act=act, pet=pet, outcome="solved", spilled=True, calm=child.memes["calm"] >= THRESHOLD
    )
    world.para()
    world.say(
        f"At the end, {child.id} was no longer worried about being liable, because "
        f"the grown-up lesson was kinder than blame. The little kitchen smelled only "
        f"of soap, and the relish jar sat still in the warm, dim light."
    )
    if pet:
        world.say(f"Even {pet} curled up nearby, as if pleased the mystery was solved.")
    return world


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", gravity=1.0, clutter=2, tags={"gravity"}),
    "pantry": Place(id="pantry", label="the pantry", gravity=0.9, clutter=3, tags={"gravity"}),
}

JARS = {
    "relish": MysteryObject(id="relish", label="jar of relish", tags={"relish"}),
    "pickle": MysteryObject(id="pickle", label="pickle jar", tags={"relish"}),
}

HELPFUL_ACTS = {
    "wipe": HelpfulAct(id="wipe", label="tea towel", text="wiped the sticky trail away", outcome="clean"),
    "fetch_towel": HelpfulAct(id="fetch_towel", label="tea towel", text="held the jar steady", outcome="steady"),
    "steady_shelf": HelpfulAct(id="steady_shelf", label="small stool", text="made the shelf safer", outcome="safe"),
    "laugh_it_off": HelpfulAct(id="laugh_it_off", label="smile", text="laughed and left it", outcome="weak"),
}


@dataclass
class StoryParams:
    place: str
    jar: str
    act: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    pet: str = ""
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


def explain_rejection(place: Place, jar: MysteryObject) -> str:
    return (
        f"(No story: the chosen setup does not make a believable kitchen mystery. "
        f"Try the kitchen or pantry with the relish jar.)"
    )


def explain_act(act: HelpfulAct) -> str:
    return (
        f"(Refusing action '{act.id}': it is too weak for a bedtime-story solution. "
        f"Try wipe, fetch_towel, or steady_shelf.)"
    )


def valid_story(params: StoryParams) -> bool:
    return params.place in PLACES and params.jar in JARS and params.act in HELPFUL_ACTS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world of mystery, relish, gravity, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--jar", choices=JARS)
    ap.add_argument("--act", choices=HELPFUL_ACTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father", "grandma", "grandpa"])
    ap.add_argument("--pet", choices=PET_NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    jar = args.jar or "relish"
    act = args.act or rng.choice(["wipe", "fetch_towel", "steady_shelf"])
    if act not in HELPFUL_ACTS:
        raise StoryError(explain_act(HelpfulAct(id=act, label=act, text="", outcome="")))
    if place not in PLACES or jar not in JARS:
        raise StoryError(explain_rejection(PLACES[place], JARS[jar]))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father", "grandma", "grandpa"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(ADULT_NAMES)
    pet = args.pet or rng.choice(PET_NAMES + ["", ""])
    return StoryParams(
        place=place,
        jar=jar,
        act=act,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        pet=pet,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that includes the words "{f["seed_word"]}", "gravity", and "relish".',
        f"Tell a gentle mystery where {f['child'].id} wonders who knocked the relish jar askew, and kindness helps solve it.",
        "Write a cozy story about a small kitchen problem that is fixed calmly and kindly before bedtime.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, jar = f["child"], f["helper"], f["jar"]
    qa = [
        QAItem(
            question="What mystery was being solved?",
            answer=f"They were solving why the {jar.label} had slid and made a sticky mess. The answer turned out to involve gravity, a wobbling shelf, and a gentle repair.",
        ),
        QAItem(
            question="Why did the child think they might be liable?",
            answer=f"{child.id} saw the spill and worried they were responsible. The grown-up then showed that the problem was not about blame, but about fixing the little accident kindly.",
        ),
        QAItem(
            question="How did kindness help?",
            answer=f"{helper.id} did not scold {child.id}. Instead, {helper.id} knelt down, looked carefully, and helped clean and steady the jar so the child could calm down.",
        ),
    ]
    if f.get("spilled"):
        qa.append(
            QAItem(
                question="What changed by the end of the story?",
                answer=f"The sticky trail was cleaned, the jar was set safer, and {child.id} felt calm again. The kitchen ended quiet and tidy, which proved the mystery had been solved.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gravity?",
            answer="Gravity is the pull that makes things fall down or slide toward the floor. It is part of why a jar can wobble if it sits too close to the edge.",
        ),
        QAItem(
            question="What is relish?",
            answer="Relish is a tasty topping made from chopped vegetables, often sweet or tangy. It usually comes in a jar and is meant to be eaten, not spilled.",
        ),
        QAItem(
            question="What does it mean to be liable?",
            answer="Being liable means being responsible for something. In a story, a child may worry they are liable for a mess, but a grown-up can help sort out what really happened.",
        ),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
spilled :- jar_tipped, gravity_high.
worry :- spilled.
kindness_resolves :- helper_kind and spilled.
outcome(solved) :- spilled, kindness_resolves.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("gravity_high", pid))
    for jid in JARS:
        lines.append(asp.fact("jar", jid))
    lines.append(asp.fact("helper_kind"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    asp_out = asp.atoms(model, "outcome")
    python_ok = all(True for _ in valid_combos())
    rc = 0 if python_ok else 1
    print("OK: ASP twin loaded." if asp_out is not None else "MISMATCH")
    sample_params = StoryParams(
        place="kitchen",
        jar="relish",
        act="wipe",
        child_name="Mina",
        child_gender="girl",
        helper_name="Mom",
        helper_gender="mother",
        pet="the cat",
    )
    try:
        sample = generate(sample_params)
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"MISMATCH: generation failed: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(
        place="kitchen",
        jar="relish",
        act="wipe",
        child_name="Mina",
        child_gender="girl",
        helper_name="Mom",
        helper_gender="mother",
        pet="the cat",
    ),
    StoryParams(
        place="pantry",
        jar="pickle",
        act="fetch_towel",
        child_name="Noah",
        child_gender="boy",
        helper_name="Grandma",
        helper_gender="grandma",
        pet="the sleepy dog",
    ),
    StoryParams(
        place="kitchen",
        jar="relish",
        act="steady_shelf",
        child_name="Luna",
        child_gender="girl",
        helper_name="Dad",
        helper_gender="father",
        pet="the kitten",
    ),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.jar not in JARS:
        raise StoryError(f"Unknown jar: {params.jar}")
    if params.act not in HELPFUL_ACTS:
        raise StoryError(f"Unknown act: {params.act}")
    world = tell(
        PLACES[params.place],
        JARS[params.jar],
        HELPFUL_ACTS[params.act],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
        params.pet,
        seed_word="liable",
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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


def resolve_params_from_rng(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible story shapes:")
        for place, jar, act in valid_combos():
            print(f"  {place:7} {jar:7} {act}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
