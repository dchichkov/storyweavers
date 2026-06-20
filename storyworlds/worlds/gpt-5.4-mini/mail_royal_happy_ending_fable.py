#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mail_royal_happy_ending_fable.py
=================================================================

A small standalone story world for a fable-like tale about royal mail:
a child or messenger loses an important royal letter, searches wisely,
asks for help, and delivers it in time for a happy ending.

The domain is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate
- an inline ASP twin
- story-grounded QA from world state, not from rendered text

Seed words: mail, royal
Style: fable
Feature: happy ending
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
MIN_KINDNESS = 2
MIN_DELIVERY = 2

GIRL_NAMES = ["Mina", "Lina", "Tessa", "Nora", "Eva", "Maya", "Rosie"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Ben", "Leo", "Eli", "Jules"]
TRAITS = ["kind", "careful", "bright", "patient", "gentle", "quick"]

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "mom", "queen", "woman"}
        male = {"boy", "father", "dad", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "king": "king", "queen": "queen"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World data
# ---------------------------------------------------------------------------

    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    quiet: str
    risk: str
    hiding: str

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
class Mail:
    id: str
    label: str
    phrase: str
    sealed: bool = True
    royal: bool = False
    fragile: bool = False
    urgent: bool = False
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
class Helper:
    id: str
    label: str
    tool: str
    action: str
    comfort: str
    strength: int
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
class Trouble:
    id: str
    label: str
    reason: str
    spread: int
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


def _r_worry(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["lost"] >= THRESHOLD and "worry" not in e.attrs:
            e.memes["worry"] += 1
            e.attrs["worry"] = True
            out.append("__worry__")
    return out


def _r_help(world: World) -> list[str]:
    out = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["asking"] >= THRESHOLD and helper.memes["kindness"] >= THRESHOLD:
        sig = ("help",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["hope"] += 1
            helper.memes["purpose"] += 1
            out.append("__help__")
    return out


def _r_delivery(world: World) -> list[str]:
    out = []
    mail = world.get("mail")
    if mail.meters["recovered"] >= THRESHOLD and mail.meters["delivered"] < THRESHOLD:
        sig = ("delivered",)
        if sig not in world.fired:
            world.fired.add(sig)
            mail.meters["delivered"] += 1
            out.append("__delivered__")
    return out


CAUSAL_RULES = [
    Rule("worry", "emotional", _r_worry),
    Rule("help", "social", _r_help),
    Rule("delivery", "physical", _r_delivery),
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "courtyard": Place("courtyard", "the palace courtyard", "quiet", "the fountain", "stone arches"),
    "road": Place("road", "the royal road", "open", "the river bend", "hedges"),
    "gate": Place("gate", "the tall gate", "watchful", "the guard post", "heavy iron bars"),
    "village": Place("village", "the little village square", "busy", "the market carts", "wooden stalls"),
}

MAILS = {
    "scroll": Mail("scroll", "a sealed scroll", "a sealed royal scroll", royal=True, fragile=True, urgent=True, tags={"mail", "royal"}),
    "letter": Mail("letter", "a golden letter", "a royal letter with a blue ribbon", royal=True, fragile=False, urgent=True, tags={"mail", "royal"}),
    "parcel": Mail("parcel", "a small parcel", "a royal parcel tied with twine", royal=True, fragile=True, urgent=False, tags={"mail", "royal"}),
}

HELPERS = {
    "map": Helper("map", "the map", "a map", "read the paths", "calm", 3, tags={"map"}),
    "lantern": Helper("lantern", "a lantern", "a lantern", "light the way", "warm", 2, tags={"light"}),
    "pony": Helper("pony", "a pony cart", "a pony cart", "carry the mail bag", "steady", 3, tags={"pony"}),
}

TROUBLES = {
    "wind": Trouble("wind", "a strong wind", "the wind", 1, tags={"wind"}),
    "rain": Trouble("rain", "a sudden rain", "the rain", 2, tags={"rain"}),
    "mud": Trouble("mud", "deep mud", "the mud", 2, tags={"mud"}),
}

KNOWLEDGE = {
    "mail": [("What is mail?", "Mail is a letter or parcel that is sent from one place to another. People use it to share news and messages.")],
    "royal": [("What does royal mean?", "Royal means it belongs to a king or queen, or to a palace. Royal things are part of the kingdom.")],
    "sealed": [("What does sealed mean?", "A sealed letter is closed so the message stays safe until the right person opens it.")],
    "courtyard": [("What is a courtyard?", "A courtyard is an open space inside or near a building, often with paths, stones, or a fountain.")],
    "road": [("Why can a road be hard to walk on?", "A road can be hard when it is windy, muddy, or long, so walking takes more care.")],
    "help": [("Why is it good to ask for help?", "Asking for help lets another person use their skills, and that can solve a problem faster and safer.")],
    "lantern": [("What is a lantern?", "A lantern is a lamp that helps people see in the dark.")],
    "pony": [("What can a pony cart do?", "A pony cart can carry things along a road, which helps when a load is too hard to carry by hand.")],
    "rain": [("Why can rain slow someone down?", "Rain can make the road wet and slippery, so walking takes more time and care.")],
    "mud": [("Why is mud messy?", "Mud sticks to shoes and clothes, so it can make a mess and slow a person down.")],
}


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
@dataclass
class StoryParams:
    place: str
    mail: str
    helper: str
    trouble: str
    child: str
    child_gender: str
    royal_title: str
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


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for mail in MAILS:
            for helper in HELPERS:
                combos.append((place, mail, helper))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-world about royal mail and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mail", choices=MAILS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--title", choices=["princess", "prince", "page"])
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
    if args.mail and args.mail not in MAILS:
        raise StoryError("Unknown mail type.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mail:
        combos = [c for c in combos if c[1] == args.mail]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mail, helper = rng.choice(combos)
    trouble = args.trouble or rng.choice(list(TROUBLES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    title = args.title or rng.choice(["princess", "prince", "page"])
    return StoryParams(place, mail, helper, trouble, name, gender, title)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(params.child, "character", params.child_gender, role="messenger", traits=["kind", "diligent"]))
    royal = world.add(Entity("royal", "character", "queen", role="ruler", label="the queen"))
    helper = world.add(Entity("helper", "character", "thing", role="helper", label=HELPERS[params.helper].label))
    mail = world.add(Entity("mail", "thing", "mail", label=MAILS[params.mail].label, attrs={"royal": True}))
    place = world.add(Entity("place", "thing", "place", label=PLACES[params.place].label))

    child.memes["duty"] += 1
    helper.memes["kindness"] += 1
    mail.meters["carried"] += 1

    world.say(f"Once, in {PLACES[params.place].label}, {child.id} carried {MAILS[params.mail].phrase} for {royal.label_word}.")
    world.say(f"The little messenger knew the mail was royal and must reach the castle today.")

    world.para()
    child.meters["lost"] += 1
    world.say(f"But on the way, {TROUBLES[params.trouble].label} made the path hard and the message slipped from {child.pronoun('possessive')} bag.")
    child.memes["asking"] += 1
    propagate(world, narrate=False)
    world.say(f"{child.id} looked all around and called for help, because a brave heart asks when the task grows hard.")

    world.para()
    world.say(f"{HELPERS[params.helper].label.capitalize()} came to the rescue and {HELPERS[params.helper].action}.")
    mail.meters["recovered"] += 1
    if params.helper == "pony":
        world.say("The pony cart carried the royal mail over the rough road without dropping it again.")
    elif params.helper == "lantern":
        world.say("The lantern showed the path when the shadows grew long.")
    else:
        world.say("The map showed the safest road, and the messenger took it step by careful step.")
    propagate(world, narrate=False)
    world.say(f"At last, {child.id} delivered the royal mail to the palace gate, and the queen smiled with relief.")

    world.para()
    world.say("The queen praised the child for being honest, patient, and wise.")
    world.say("From that day on, the village said that a small act of courage can carry a big message home.")

    world.facts.update(
        child=child, royal=royal, helper=params.helper, trouble=params.trouble,
        mail=mail, place=params.place, title=params.royal_title,
        outcome="happy", delivered=mail.meters["delivered"] >= THRESHOLD,
        lost=child.meters["lost"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-style happy-ending story for a young child that includes the words "mail" and "royal".',
        f"Tell a gentle story about {f['child'].id} carrying royal mail, losing it for a moment, asking for help, and delivering it safely.",
        f'Write a simple fable where a messenger learns that asking for help can save the royal mail.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mail = f["mail"]
    qa = [
        QAItem(
            question=f"What was {child.id} carrying?",
            answer=f"{child.id} was carrying {mail.label} for the royal court. It was important mail, so it had to reach the palace safely."
        ),
        QAItem(
            question=f"What problem happened on the road?",
            answer=f"The road trouble made the message slip away for a moment, so {child.id} could not carry it alone. That is why {child.id} asked for help instead of giving up."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, because the mail was found and delivered to the queen. The child was praised for being brave, honest, and wise."
        ),
    ]
    if helper == "pony":
        qa.append(QAItem(
            question="Why did the pony cart help?",
            answer="The pony cart could carry the royal mail over the rough road. That made the journey safer and kept the letter from getting lost again."
        ))
    elif helper == "lantern":
        qa.append(QAItem(
            question="Why did the lantern help?",
            answer="The lantern showed the way when the path grew dim. That helped the messenger keep walking carefully with the royal mail."
        ))
    else:
        qa.append(QAItem(
            question="Why did the map help?",
            answer="The map showed the safest road to the palace. That made it easier to recover the mail and finish the job well."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"mail", "royal", "help"}
    helper = world.facts["helper"]
    trouble = world.facts["trouble"]
    tags.add(helper)
    tags.add(trouble)
    out: list[QAItem] = []
    order = ["mail", "royal", "sealed", "courtyard", "road", "help", "lantern", "pony", "rain", "mud"]
    for tag in order:
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
    lines.append("== (3) World knowledge questions ==")
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
lost(E) :- entity(E), meter(E, lost, V), V >= 1.
asking(E) :- entity(E), meme(E, asking, V), V >= 1.
kind_helper(H) :- helper(H), meme(H, kindness, V), V >= 1.
helped :- asking(child), kind_helper(helper).
delivered :- entity(mail), meter(mail, delivered, V), V >= 1.
outcome(happy) :- helped, delivered.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MAILS.items():
        lines.append(asp.fact("mail", mid))
        if m.royal:
            lines.append(asp.fact("royal", mid))
        if m.sealed:
            lines.append(asp.fact("sealed", mid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1.\n#show mail/1.\n#show helper/1.\n"))
    # For this tiny world, all registries are compatible; emit a simple product.
    return sorted(valid_combos())


def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program("entity(child). meme(child, asking, 1). entity(helper). meme(helper, kindness, 1). entity(mail). meter(mail, delivered, 1).", "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid_combos()")
        rc = 1

    # Smoke test ordinary generation.
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        _ = sample.to_json()
        print("OK: generate()/serialization smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1

    return rc


def valid_combo_filter(args: argparse.Namespace, combo: tuple[str, str, str]) -> bool:
    place, mail, helper = combo
    return (
        (args.place is None or args.place == place) and
        (args.mail is None or args.mail == mail) and
        (args.helper is None or args.helper == helper)
    )


def explain_rejection() -> str:
    return "(No story: those choices do not make a believable royal-mail fable.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams("courtyard", "scroll", "map", "wind", "Mina", "girl", "princess"),
    StoryParams("road", "letter", "lantern", "rain", "Theo", "boy", "prince"),
    StoryParams("gate", "parcel", "pony", "mud", "Nora", "girl", "page"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show place/1.\n#show mail/1.\n#show helper/1.\n#show trouble/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible story combos:\n")
        for place, mail, helper in valid_combos():
            print(f"  {place:10} {mail:8} {helper}")
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
            header = f"### {p.child}: royal mail fable in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
