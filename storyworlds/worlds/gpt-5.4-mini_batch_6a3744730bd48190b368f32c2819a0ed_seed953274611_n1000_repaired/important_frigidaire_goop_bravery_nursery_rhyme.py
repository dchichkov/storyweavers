#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/important_frigidaire_goop_bravery_nursery_rhyme.py
===================================================================================

A tiny nursery-rhyme style storyworld about a child, a sticky goop spill, an
important appliance, and a brave choice to get help in time.

The seed words are woven into the domain:
- important
- frigidaire
- goop
- bravery

This world keeps the simulation small and concrete:
- a child wants to reach something important near the frigidaire
- goop makes the floor slippery and the helper worried
- bravery is the emotional turn that helps the child ask for aid
- a grown-up responds, cleans safely, and the ending image proves the change

The prose aims to feel like a simple rhyme without forcing meter or full
rhyming every line. It remains state-driven and child-facing.
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
BRAVERY_START = 2.0


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
    scene: str
    rhyme: str
    important: str
    has_frigidaire: bool = True
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
class Mess:
    id: str
    label: str
    sticky: bool
    slippery: bool
    stain: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    setting: str
    mess: str
    response: str
    child: str
    child_gender: str
    helper: str
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


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        scene="a busy little kitchen",
        rhyme="the spoons went clink and the kettle made a din",
        important="the frigidaire",
        tags={"kitchen", "frigidaire"},
    ),
    "pantry": Setting(
        id="pantry",
        place="the pantry",
        scene="a snug little pantry",
        rhyme="the jars stood still in neat and tidy rows",
        important="the frigidaire",
        tags={"pantry", "frigidaire"},
    ),
    "laundry": Setting(
        id="laundry",
        place="the laundry room",
        scene="a humming little laundry room",
        rhyme="the towels hung soft and the dryer hummed along",
        important="the frigidaire",
        tags={"laundry", "frigidaire"},
    ),
}

MESS = {
    "goop": Mess(
        id="goop",
        label="goop",
        sticky=True,
        slippery=True,
        stain="gooey",
        tags={"goop", "sticky"},
    ),
    "jam": Mess(
        id="jam",
        label="jam",
        sticky=True,
        slippery=False,
        stain="sugary",
        tags={"jam", "sticky"},
    ),
    "soap": Mess(
        id="soap",
        label="soap suds",
        sticky=False,
        slippery=True,
        stain="foamy",
        tags={"soap", "slippery"},
    ),
}

RESPONSES = {
    "wipe": Response(
        id="wipe",
        sense=3,
        power=3,
        text="wiped the goop away with a towel and set a dry mat on the floor",
        fail="tried to wipe the goop away, but the spill was too wide to fix",
        qa_text="wiped the goop away with a towel and set a dry mat on the floor",
        tags={"towel", "mat"},
    ),
    "mop": Response(
        id="mop",
        sense=3,
        power=4,
        text="mopped the floor, then set down a dry cloth so the child could step safely",
        fail="mopped, but the floor was still slick and messy afterward",
        qa_text="mopped the floor, then set down a dry cloth so the child could step safely",
        tags={"mop", "cloth"},
    ),
    "call_help": Response(
        id="call_help",
        sense=4,
        power=4,
        text="called for help, fetched a towel, and cleaned the slippery spot before anyone fell",
        fail="called for help, but the spill was already bigger than that one plan",
        qa_text="called for help, fetched a towel, and cleaned the slippery spot before anyone fell",
        tags={"help", "towel"},
    ),
}

CHILD_NAMES = ["Mia", "Nora", "Lily", "Tia", "Elsie", "Ruby", "Finn", "Bennie", "Toby", "Owen"]
HELPER_NAMES = ["Mom", "Dad", "Mum", "Pop", "Auntie", "Uncle"]
SETTINGS_ORDER = ["kitchen", "pantry", "laundry"]
MESS_ORDER = ["goop", "jam", "soap"]
RESP_ORDER = ["wipe", "mop", "call_help"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for s in SETTINGS.values():
        if not s.has_frigidaire:
            continue
        for m in MESS.values():
            if m.sticky or m.slippery:
                out.append((s.id, m.id))
    return out


def reasonableness_gate(setting: Setting, mess: Mess, response: Response) -> bool:
    return setting.has_frigidaire and (mess.sticky or mess.slippery) and response.sense >= 3


def spill_hazard(mess: Mess) -> bool:
    return mess.sticky or mess.slippery


def is_big_enough(response: Response, mess: Mess, delay: int) -> bool:
    severity = 2 + delay if mess.slippery else 1 + delay
    return response.power >= severity


def _make_spill(world: World, child: Entity, mess: Mess) -> None:
    child.meters["messy"] += 1
    child.meters[mess.id] += 1
    child.memes["worry"] += 1
    if mess.slippery:
        world.get("floor").meters["slippery"] += 1


def _propagate(world: World) -> None:
    if world.get("floor").meters["slippery"] >= THRESHOLD and ("fall", "child") not in world.fired:
        world.fired.add(("fall", "child"))
        world.get("child").memes["worry"] += 1


def predict(world: World, mess: Mess) -> dict:
    sim = world.copy()
    _make_spill(sim, sim.get("child"), mess)
    _propagate(sim)
    return {
        "slippery": sim.get("floor").meters["slippery"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"],
    }


def tell(setting: Setting, mess: Mess, response: Response,
         child_name: str, child_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    floor = world.add(Entity(id="floor", type="floor", label="the floor"))
    fridge = world.add(Entity(id="frigidaire", type="appliance", label="the frigidaire"))

    child.memes["bravery"] = BRAVERY_START
    helper.memes["care"] = 2.0
    world.facts["setting"] = setting
    world.facts["mess"] = mess
    world.facts["response"] = response
    world.facts["child"] = child
    world.facts["helper"] = helper

    world.say(f"In {setting.place}, the day was warm and bright, and {setting.rhyme}.")
    world.say(
        f"{child_name} found something important near {setting.important}, "
        f"but a little {mess.label} made the floor shine and slide."
    )

    world.para()
    pred = predict(world, mess)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"{child_name} looked at the sticky spot and felt the brave little tug of bravery."
    )
    world.say(
        f'"{helper_name}, I need help," {child_name} said, and that was the important part.'
    )

    world.para()
    _make_spill(world, child, mess)
    _propagate(world)
    world.say(
        f"{helper_name} came at once. {helper_name} {response.text}."
    )
    if is_big_enough(response, mess, 0):
        world.say(
            f"The goop was gone, the floor was dry, and {child_name} could stand near {setting.important} safely."
        )
        world.say(
            f"{child_name} smiled at the bright frigidaire, brave enough to ask, brave enough to wait."
        )
        outcome = "fixed"
    else:
        world.say(
            f"The first try was not enough, so {helper_name} used a better cloth and made the floor safe at last."
        )
        outcome = "rescued"

    world.facts["outcome"] = outcome
    world.facts["slippery"] = world.get("floor").meters["slippery"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    mess = f["mess"]
    child = f["child"]
    helper = f["helper"]
    return [
        f'Write a nursery-rhyme style story that includes the words "important", "frigidaire", and "{mess.label}".',
        f"Tell a little story where {child.label} has bravery, sees {mess.label} near the frigidaire, and asks {helper.label} for help.",
        f"Write a child-friendly rhyme about something important near {setting.place} with a sticky or slippery mess.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    mess = f["mess"]
    out = [
        ("Who is the story about?",
         f"It is about {child.label} and {helper.label} in {setting.place}. The little scene centers on a brave child and a helpful grown-up."),
        ("What made the floor tricky?",
         f"A bit of {mess.label} made the floor slippery and messy. That was why the child needed to slow down and ask for help."),
        ("Why was bravery important?",
         f"Bravery helped {child.label} speak up instead of trying to handle the spill alone. That brave choice brought the grown-up in before anyone fell."),
        ("What happened at the end?",
         f"{helper.label} cleaned the spill and made the floor safe again. After that, {child.label} could stay near the important frigidaire without worry."),
    ]
    if f.get("outcome") == "rescued":
        out.append((
            "How did the helper fix the problem?",
            f"{helper.label} used a better cloth after the first try was not enough. That kept the spill from being a danger near {setting.important}."))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mess = f["mess"]
    out = [
        ("What is goop?",
         "Goop is a sticky, messy blob that can smear and spread on things. It can make a floor hard to trust if it is left alone."),
        ("What does bravery mean?",
         "Bravery means doing the right thing even when you feel a little scared. In this story, bravery meant asking for help."),
        ("Why should you keep a spill off the floor?",
         "A spill can make the floor slippery, and slippery floors can make someone fall. Cleaning it up makes the room safer."),
    ]
    if mess.id != "goop":
        out.append((
            f"What kind of mess was {mess.label}?",
            f"{mess.label.capitalize()} was the kind of mess that could make a child worry and call for help. It still needed a careful cleanup."
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
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", mess="goop", response="wipe", child="Nora", child_gender="girl", helper="Mom", helper_gender="woman"),
    StoryParams(setting="pantry", mess="jam", response="mop", child="Owen", child_gender="boy", helper="Dad", helper_gender="man"),
    StoryParams(setting="laundry", mess="soap", response="call_help", child="Mia", child_gender="girl", helper="Auntie", helper_gender="woman"),
]


def explain_rejection(setting: Setting, mess: Mess, response: Optional[Response] = None) -> str:
    if response and response.sense < 3:
        return f"(No story: '{response.id}' is too weak a response for this little emergency.)"
    if not setting.has_frigidaire:
        return f"(No story: the setting needs a frigidaire to match the seed.)"
    if not spill_hazard(mess):
        return f"(No story: {mess.label} is not a spill hazard here.)"
    return "(No story: that combination doesn't make a strong enough nursery-rhyme problem.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 3:
        raise StoryError(explain_rejection(SETTINGS[args.setting] if args.setting else SETTINGS["kitchen"], MESS[args.mess] if args.mess else MESS["goop"], RESPONSES[args.response]))
    settings = [k for k in SETTINGS if args.setting is None or k == args.setting]
    messes = [k for k in MESS if args.mess is None or k == args.mess]
    responses = [k for k in RESPONSES if args.response is None or k == args.response]
    combos = [(s, m, r) for s in settings for m in messes for r in responses if reasonableness_gate(SETTINGS[s], MESS[m], RESPONSES[r])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mess, response = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, mess=mess, response=response, child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mess not in MESS or params.response not in RESPONSES:
        raise StoryError("(Invalid params for this world.)")
    world = tell(
        SETTINGS[params.setting],
        MESS[params.mess],
        RESPONSES[params.response],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MESS.items():
        lines.append(asp.fact("mess", mid))
        if m.sticky:
            lines.append(asp.fact("sticky", mid))
        if m.slippery:
            lines.append(asp.fact("slippery", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("needs", "frigidaire"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,R) :- setting(S), mess(M), response(R), needs(frigidaire), sticky(M), sense(R,X), X >= 3.
valid(S,M,R) :- setting(S), mess(M), response(R), needs(frigidaire), slippery(M), sense(R,X), X >= 3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set((a, b) for a, b, *_ in asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo gate.")
        print("  only in python:", sorted(py - cl))
        print("  only in ASP:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about bravery, goop, and a frigidaire.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mess", choices=MESS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
        for s, m, r in combos:
            print(f"  {s:8} {m:6} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.helper}: {p.setting}, {p.mess}, {p.response}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
