#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tummy_dialogue_misunderstanding_tall_tale.py
=============================================================================

A standalone storyworld for a tall-tale misunderstanding about a tummy ache,
where dialogue drives the plot and a comic mix-up turns into a gentle fix.

Premise:
- A child says their tummy feels "like a drum."
- Another character misunderstands and thinks the drum means a real drum,
  then a tall-tale chain of exaggerated guesses follows.
- The misunderstanding is resolved when a calm helper asks the right questions
  and offers a simple remedy.

The world model tracks physical meters and emotional memes so the story is not
just a fixed paragraph with swapped names.
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
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
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


@dataclass
class Setting:
    id: str
    place: str
    details: str
    indoors: bool = False
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


@dataclass
class Complaint:
    id: str
    phrase: str
    cause_hint: str
    severity: int = 1
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Misunderstanding:
    id: str
    guess: str
    mistaken_noun: str
    exaggeration: str
    dialogue_line: str
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


@dataclass
class Remedy:
    id: str
    text: str
    calm_text: str
    effect: str
    power: int = 1
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_worry(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes["worry"] >= THRESHOLD and ("worry", e.id) not in world.fired:
            world.fired.add(("worry", e.id))
            out.append(f"{e.label_word.capitalize()} started pacing like a windmill in a storm.")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes["relief"] >= THRESHOLD and ("relief", e.id) not in world.fired:
            world.fired.add(("relief", e.id))
            out.append(f"{e.label_word.capitalize()} could finally breathe easy again.")
    return out


CAUSAL_RULES: list[Callable[[World], list[str]]] = [_r_worry, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mixup(world: World, complaint: Complaint, misunderstanding: Misunderstanding) -> dict:
    sim = world.copy()
    tell_misunderstanding(sim, sim.get("child"), sim.get("listener"), complaint, misunderstanding, narrate=False)
    return {"worry": sim.get("listener").memes["worry"], "confusion": sim.get("listener").memes["confusion"]}


def tell_setup(world: World, child: Entity, listener: Entity, setting: Setting, complaint: Complaint) -> None:
    child.memes["unease"] += 1
    child.meters["tummy"] += complaint.severity
    world.say(
        f"In {setting.place}, under a sky as broad as a wagon wheel, {child.id} patted {child.pronoun('possessive')} tummy and sighed, "
        f'"My tummy feels {complaint.phrase}."'
    )
    world.say(
        f"{listener.id} blinked. {listener.pronoun().capitalize()} had never heard a tummy complain in such a high-and-wide voice."
    )


def tell_misunderstanding(world: World, child: Entity, listener: Entity,
                           complaint: Complaint, misunderstanding: Misunderstanding,
                           narrate: bool = True) -> None:
    listener.memes["confusion"] += 1
    world.say(
        f'"Do you mean {misunderstanding.guess}?" {listener.id} asked. '
        f'"I can hear a beat in the room, and I thought your {complaint.cause_hint} was calling for music."'
    )
    world.say(
        f"{child.id} stared. {child.pronoun().capitalize()} pointed at {child.pronoun('possessive')} middle. "
        f'"No, I mean my tummy, not a {misunderstanding.mistaken_noun}!"'
    )
    if narrate:
        propagate(world, narrate=True)


def tall_tale_chain(world: World, listener: Entity, misunderstanding: Misunderstanding) -> None:
    listener.memes["wonder"] += 1
    world.say(
        f'"That settles it," {listener.id} said. "A tummy with a drum-beat must be a mighty thing. '
        f'I once met a fisher cat whose sneeze could whistle a fence into a fiddle!"'
    )
    world.say(
        f'{listener.id} waved both hands and went on: "{misunderstanding.exaggeration}"'
    )


def clarify(world: World, child: Entity, listener: Entity, remedy: Remedy) -> None:
    listener.memes["confusion"] = 0
    listener.memes["worry"] += 0
    world.say(
        f'Then a calm helper named {world.get("helper").id} came by and said, "{remedy.text}"'
    )
    world.say(
        f'"Oh!" {listener.id} said. "{child.id} means a tummy, not a {world.facts["misunderstanding"].mistaken_noun}."'
    )


def remedy_and_end(world: World, child: Entity, listener: Entity, remedy: Remedy) -> None:
    child.meters["tummy"] = max(0.0, child.meters["tummy"] - remedy.power)
    child.memes["relief"] += 1
    listener.memes["relief"] += 1
    world.say(
        f"{world.get('helper').id} {remedy.calm_text}. {child.id} sipped a little water, rested, and held {child.pronoun('possessive')} belly with a grin."
    )
    world.say(
        f"By sunset, the whole town could tell the difference between a music drum and a tummy drum, and the only beat left was a happy one."
    )


def tell_story(setting: Setting, complaint: Complaint, misunderstanding: Misunderstanding, remedy: Remedy,
               child_name: str = "Mabel", child_type: str = "girl",
               listener_name: str = "Uncle Ned", listener_type: str = "man",
               helper_name: str = "Nurse June", helper_type: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    listener = world.add(Entity(id="listener", kind="character", type=listener_type, label=listener_name, role="listener"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))

    world.facts.update(setting=setting, complaint=complaint, misunderstanding=misunderstanding, remedy=remedy)
    tell_setup(world, child, listener, setting, complaint)
    world.para()
    tell_misunderstanding(world, child, listener, complaint, misunderstanding)
    tall_tale_chain(world, listener, misunderstanding)
    world.para()
    clarify(world, child, listener, remedy)
    remedy_and_end(world, child, listener, remedy)

    world.facts.update(child=child, listener=listener, helper=helper)
    return world


SETTINGS = {
    "porch": Setting(id="porch", place="on the porch", details="The boards creaked like old ships.", indoors=False),
    "kitchen": Setting(id="kitchen", place="in the kitchen", details="The kettle ticked like a tiny clock.", indoors=True),
    "fair": Setting(id="fair", place="at the county fair", details="The banners snapped in the breeze like sails.", indoors=False),
}

COMPLAINTS = {
    "grumble": Complaint(id="grumble", phrase="as grumbly as thunder", cause_hint="thunder", severity=2),
    "twist": Complaint(id="twist", phrase="twisty like a rope knot", cause_hint="a rope knot", severity=1),
    "growl": Complaint(id="growl", phrase="loud as a bear in boots", cause_hint="a bear in boots", severity=2),
}

MISUNDERSTANDINGS = {
    "drum": Misunderstanding(
        id="drum",
        guess="a drum",
        mistaken_noun="drum",
        exaggeration="I once heard a whale beat time on a biscuit tin, and the whole harbor danced!",
        dialogue_line="I thought your tummy was making music.",
    ),
    "horn": Misunderstanding(
        id="horn",
        guess="a horn",
        mistaken_noun="horn",
        exaggeration="I knew a cart-horse whose yawn could salute the moon and wake a barn full of geese!",
        dialogue_line="I thought your tummy was sounding a horn.",
    ),
}

REMEDIES = {
    "water": Remedy(id="water", text="Did you mean your tummy feels funny?", calm_text="smiled, fetched a cup of water, and pulled up a chair", effect="comfort", power=1),
    "cracker": Remedy(id="cracker", text="Your tummy needs a quiet snack and a rest, not a parade.", calm_text="brought a plain cracker and sat beside them", effect="settle", power=1),
    "rest": Remedy(id="rest", text="That sounds like a tummy that wants rest more than riddles.", calm_text="opened the window, dimmed the room, and let the worry drift away", effect="rest", power=1),
}

GIRL_NAMES = ["Mabel", "June", "Ivy", "Ada", "Elsie"]
BOY_NAMES = ["Benny", "Otis", "Jasper", "Will", "Hugo"]
TALL_TALE_WORLDS = ["porch", "kitchen", "fair"]


@dataclass
class StoryParams:
    setting: str
    complaint: str
    misunderstanding: str
    remedy: str
    child_name: str
    child_type: str
    listener_name: str
    listener_type: str
    helper_name: str
    helper_type: str
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
    StoryParams(setting="porch", complaint="grumble", misunderstanding="drum", remedy="cracker",
                child_name="Mabel", child_type="girl", listener_name="Uncle Ned", listener_type="man",
                helper_name="Nurse June", helper_type="woman"),
    StoryParams(setting="fair", complaint="twist", misunderstanding="horn", remedy="rest",
                child_name="Will", child_type="boy", listener_name="Aunt Rosie", listener_type="woman",
                helper_name="Dr. Finn", helper_type="man"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in COMPLAINTS:
            for m in MISUNDERSTANDINGS:
                for r in REMEDIES:
                    combos.append((s, c, m, r))
    return combos


def explain_rejection() -> str:
    return "(No story: invalid parameters for this small tummy-tale world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale tummy misunderstanding storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--complaint", choices=COMPLAINTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--listener-name")
    ap.add_argument("--listener-type", choices=["man", "woman"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["man", "woman"])
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
        raise StoryError(explain_rejection())
    setting = args.setting or rng.choice(list(SETTINGS))
    complaint = args.complaint or rng.choice(list(COMPLAINTS))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    listener_type = args.listener_type or rng.choice(["man", "woman"])
    listener_name = args.listener_name or rng.choice(["Uncle Ned", "Aunt Rosie", "Captain Pike", "Mrs. Bell"])
    helper_type = args.helper_type or rng.choice(["man", "woman"])
    helper_name = args.helper_name or rng.choice(["Nurse June", "Dr. Finn", "Old Sal", "Mr. Pike"])
    return StoryParams(
        setting=setting,
        complaint=complaint,
        misunderstanding=misunderstanding,
        remedy=remedy,
        child_name=child_name,
        child_type=child_type,
        listener_name=listener_name,
        listener_type=listener_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale style story for a young child that includes the word "tummy" and a funny misunderstanding.',
        f"Tell a dialogue-driven story where {f['child'].label_word} says their tummy feels strange, {f['listener'].label_word} misunderstands, and a helper clears it up.",
        f"Write a short story with an exaggerated, playful misunderstanding about a tummy and a gentle ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    l = world.facts["listener"]
    h = world.facts["helper"]
    comp = world.facts["complaint"]
    mis = world.facts["misunderstanding"]
    rem = world.facts["remedy"]
    return [
        QAItem(question="Who had the tummy problem?", answer=f"{c.id} did. {c.id} said {c.pronoun('possessive')} tummy felt {comp.phrase}, which started the whole mix-up."),
        QAItem(question="What did the listener misunderstand?", answer=f"{l.id} misunderstood and thought the tummy was {mis.guess}. That is why the first guess sounded so silly."),
        QAItem(question="How was the misunderstanding fixed?", answer=f"{h.id} stepped in and helped explain that it was a tummy, not {mis.guess}. Then {rem.effect} made everything calm and small again."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a tummy?", answer="A tummy is the soft part of your body where your stomach helps you digest food. Sometimes people call that area their tummy when it aches or feels funny."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone thinks a word or situation means one thing, but it really means something else. A good question can clear it up."),
        QAItem(question="What is a tall tale?", answer="A tall tale is a story with big, playful exaggerations. The details are stretched on purpose to make the story funny and lively."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
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
        parts.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(parts)


ASP_RULES = r"""
complaint(c1). misunderstanding(m1). remedy(r1).
valid(c1,m1,r1).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in COMPLAINTS:
        lines.append(asp.fact("complaint", c))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    ok = clingo_set == python_set
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, complaint=None, misunderstanding=None, remedy=None,
            child_name=None, child_type=None, listener_name=None, listener_type=None,
            helper_name=None, helper_type=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        return 1
    if ok:
        print(f"OK: ASP matches Python valid_combos() ({len(clingo_set)} combos).")
        print("OK: generation smoke test passed.")
        return 0
    print("MISMATCH between ASP and Python valid_combos().")
    return 1


def generate(params: StoryParams) -> StorySample:
    for key, table in [
        ("setting", SETTINGS),
        ("complaint", COMPLAINTS),
        ("misunderstanding", MISUNDERSTANDINGS),
        ("remedy", REMEDIES),
    ]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell_story(
        SETTINGS[params.setting],
        COMPLAINTS[params.complaint],
        MISUNDERSTANDINGS[params.misunderstanding],
        REMEDIES[params.remedy],
        child_name=params.child_name,
        child_type=params.child_type,
        listener_name=params.listener_name,
        listener_type=params.listener_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
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
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
