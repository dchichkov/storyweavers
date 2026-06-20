#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fulfill_notice_religion_cautionary_animal_story.py
===================================================================================

A standalone storyworld for a small animal cautionary tale.  The domain is a
pair of animal friends who wander near a quiet place of religion, notice a
dangerous candle, ignore a warning, and then learn to fulfill a promise to stay
safe and respectful.

The simulation keeps the story state-driven: physical meters track things like
smoke, singe, and safe_distance, while emotional memes track curiosity, worry,
relief, and respect.  The ending image proves the change by showing the animals
choosing a safer, calmer action.
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
SENSE_MIN = 2


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
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



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
    quiet: bool = False
    holy: bool = False
    candles: bool = False
    flowers: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Temptation:
    id: str
    label: str
    shine: str
    forbidden: str
    makes_smoke: bool = True
    sense: int = 2
    power: int = 2
    qa_text: str = ""

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
class SafeChoice:
    id: str
    label: str
    action: str
    gives: str

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_smoke(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["singe"] < THRESHOLD:
            continue
        sig = ("smoke", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.characters():
            ch.memes["worry"] += 1
        out.append("__smoke__")
    return out


CAUSAL_RULES = [Rule("smoke", "physical", _r_smoke)]


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


def hazard_at_risk(tempt: Temptation, place: Place) -> bool:
    return tempt.makes_smoke and place.candles


def sensible_choices() -> list[SafeChoice]:
    return [c for c in SAFE_CHOICES.values()]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, tempt in TEMPTATIONS.items():
            if hazard_at_risk(tempt, place):
                combos.append((pid, tid))
    return combos


def smoke_severity(delay: int) -> int:
    return 1 + delay


def is_contained(choice: SafeChoice, delay: int) -> bool:
    return choice.id in {"back_away", "call_grownup", "leave_quietly"} or smoke_severity(delay) <= 2


def predict(world: World, temptation_id: str) -> dict:
    sim = world.copy()
    _do_bad_choice(sim, sim.get("spark"), TEMPTATIONS[temptation_id], narrate=False)
    return {"smoke": sim.get("candle").meters["singe"] >= THRESHOLD, "worry": sim.get("owl").memes["worry"]}


def _do_bad_choice(world: World, actor: Entity, tempt: Temptation, narrate: bool = True) -> None:
    actor.meters["singe"] += 1
    actor.meters["smoke"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f"One bright afternoon, {a.id} and {b.id} went wandering by {place.label}. "
        f"The path was soft, the air was calm, and {place.label} felt peaceful."
    )


def notice(world: World, b: Entity, place: Place) -> None:
    world.say(
        f"{b.id} slowed down and noticed the candles near the little prayer table. "
        f'"This is a place of religion," {b.pronoun()} whispered. "We must be gentle here."'
    )


def tempt(world: World, a: Entity, tempt: Temptation, place: Place) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"Then {a.id} noticed {tempt.label} glowing by the edge of the shrine garden. "
        f'"I want to see if I can {tempt.forbidden}," {a.id} said, with bright eyes.'
    )


def warn(world: World, b: Entity, a: Entity, place: Place, tempt: Temptation) -> None:
    pred = predict(world, tempt.id)
    b.memes["care"] += 1
    if pred["smoke"] or pred["worry"] >= 1:
        world.say(
            f'"No," {b.id} said quickly. "If you touch that candle, it can make smoke, '
            f"and smoke does not belong near a holy place."
        )


def defy(world: World, a: Entity, tempt: Temptation) -> None:
    a.memes["defiance"] += 1
    world.say(f'"But I want to," {a.id} said, and reached a paw toward it.')


def ignite(world: World, place: Place, tempt: Temptation) -> None:
    _do_bad_choice(world, world.get("spark"), tempt)
    place.meters["smoke"] += 1
    world.say(
        f"The candle gave a tiny pop, then a curl of smoke drifted up between the flowers. "
        f"The sweet quiet felt suddenly worried."
    )


def alarm(world: World, b: Entity, a: Entity) -> None:
    world.say(f'"{a.id}!" {b.id} cried. "Stop! Come back!"')


def rescue(world: World, grownup: Entity, choice: SafeChoice, a: Entity, b: Entity) -> None:
    world.get("candle").meters["singe"] = 0.0
    grownup.memes["calm"] += 1
    world.say(
        f"{grownup.id} came over at once and gently moved the animals away. "
        f"{grownup.pronoun().capitalize()} {choice.action}, and the smoke cleared."
    )
    world.say(
        f"The flowers stayed safe, and the little altar was left neat and still."
    )


def lesson(world: World, grownup: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["respect"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"Then {grownup.id} knelt down and said, "
        f'"We can enjoy a place of religion by being quiet, watching carefully, and '
        f"fulfilling our promise to keep hands off candles."
    )
    world.say(f"{a.id} and {b.id} nodded, looking sheepish but safe.")


def safe_finish(world: World, a: Entity, b: Entity, choice: SafeChoice, place: Place) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After that, {a.id} and {b.id} stepped onto the path again. "
        f"They chose to {choice.gives} instead, and they left {place.label} calm, "
        f"quiet, and shining in the late light."
    )


def tell(place: Place, tempt: Temptation, choice: SafeChoice, kind_a: str = "mouse",
         kind_b: str = "rabbit", grownup_kind: str = "owl", a_name: str = "Milo",
         b_name: str = "Pippa", grownup_name: str = "Orla", delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(a_name, "character", kind_a, role="instigator"))
    b = world.add(Entity(b_name, "character", kind_b, role="cautioner"))
    grownup = world.add(Entity(grownup_name, "character", grownup_kind, role="grownup"))
    world.add(Entity("spark", "thing", "candle"))
    world.add(Entity("candle", "thing", "candle"))
    world.add(Entity("prayer_table", "thing", "prayer table"))
    world.facts["place"] = place
    world.facts["tempt"] = tempt
    world.facts["choice"] = choice
    world.facts["delay"] = delay

    opening(world, a, b, place)
    notice(world, b, place)
    world.para()
    tempt(world, a, tempt, place)
    warn(world, b, a, place, tempt)
    defy(world, a, tempt)
    ignite(world, place, tempt)
    alarm(world, b, a)
    world.para()
    rescue(world, grownup, choice, a, b)
    lesson(world, grownup, a, b)
    world.para()
    safe_finish(world, a, b, choice, place)
    world.facts.update(a=a, b=b, grownup=grownup, outcome="contained")
    return world


PLACES = {
    "temple_garden": Place("temple_garden", "the temple garden", quiet=True, holy=True, candles=True, flowers=True),
    "chapel_path": Place("chapel_path", "the chapel path", quiet=True, holy=True, candles=True, flowers=True),
    "festival_corner": Place("festival_corner", "the festival corner", quiet=True, holy=True, candles=True, flowers=True),
}

TEMPTATIONS = {
    "candle": Temptation("candle", "a small candle", "glowed", "touch the candle flame", makes_smoke=True, sense=2, power=2,
                         qa_text="It made a small flame that could turn to smoke if touched."),
    "lantern": Temptation("lantern", "a tiny lantern", "glowed", "touch the lantern wick", makes_smoke=True, sense=2, power=2,
                          qa_text="It could smoke if mishandled, so it needed a careful grown-up."),
}

SAFE_CHOICES = {
    "back_away": SafeChoice("back_away", "back away", "moved the animals back", "looked quietly from the path"),
    "call_grownup": SafeChoice("call_grownup", "call a grown-up", "called the grown-up over", "waited by the gate"),
    "leave_quietly": SafeChoice("leave_quietly", "leave quietly", "guided everyone away", "walked on to the pond"),
}

GIRL_NAMES = ["Pippa", "Luna", "Mina", "Rosie", "Mabel"]
BOY_NAMES = ["Milo", "Finn", "Toby", "Otis", "Jasper"]
ANIMALS = ["mouse", "rabbit", "kitten", "fox", "puppy", "duck"]
GROWNUPS = ["owl", "deer", "badger"]


@dataclass
@dataclass
class StoryParams:
    place: str
    temptation: str
    choice: str
    a_name: str
    b_name: str
    grownup_name: str
    a_kind: str
    b_kind: str
    grownup_kind: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a cautionary animal story that includes the words "fulfill", "notice", and "religion".',
        f"Tell a gentle animal story where {f['a'].id} and {f['b'].id} notice a dangerous candle near {f['place'].label} and choose a safer way.",
        "Write a child-friendly story about animals learning to be respectful in a place of religion.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, grownup, place, tempt, choice = f["a"], f["b"], f["grownup"], f["place"], f["tempt"], f["choice"]
    return [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two small animals, and {grownup.id}, who helped keep them safe."),
        ("What did they notice?",
         f"They noticed {tempt.label} near {place.label}. {b.id} also noticed that it was a place of religion and reminded {a.id} to be gentle."),
        ("What happened when the first animal reached for the candle?",
         f"The candle made smoke and everyone got worried. That is why the story turns into a cautionary lesson instead of more play."),
        ("How did they fulfill the lesson?",
         f"They fulfilled the lesson by stepping back, calling the grown-up, and choosing to {choice.label}. They stayed respectful and safe."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is religion?",
         "Religion is a set of beliefs and practices that people use to worship, pray, and show respect. In a story, that means some places should be treated quietly and carefully."),
        ("Why are candles watched carefully?",
         "Candles have a real flame, so they can make smoke or start a fire if they are touched or tipped over."),
        ("What should you do in a quiet holy place?",
         "You should walk softly, use gentle voices, and keep your hands to yourself unless a grown-up says it is okay."),
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("temple_garden", "candle", "back_away", "Milo", "Pippa", "Orla", "mouse", "rabbit", "owl", 0),
    StoryParams("chapel_path", "lantern", "call_grownup", "Luna", "Milo", "Orla", "kitten", "duck", "deer", 0),
]


def explain_rejection(place: Place, tempt: Temptation) -> str:
    if not hazard_at_risk(tempt, place):
        return "(No story: that combination does not create a real cautionary problem.)"
    return "(No story: the requested options do not fit the storyworld's reasonableness gate.)"


def outcome_of(params: StoryParams) -> str:
    return "contained"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("candles", pid))
    for tid in TEMPTATIONS:
        lines.append(asp.fact("temptation", tid))
        lines.append(asp.fact("makes_smoke", tid))
    for cid in SAFE_CHOICES:
        lines.append(asp.fact("choice", cid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P, T) :- place(P), temptation(T), candles(P), makes_smoke(T).
sensible(C) :- choice(C).
valid(P, T) :- hazard(P, T), sensible(_).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show hazard/2."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP/Python gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal cautionary storyworld with religion, notice, fulfill.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--choice", choices=SAFE_CHOICES)
    ap.add_argument("--a-name")
    ap.add_argument("--b-name")
    ap.add_argument("--grownup-name")
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
    combos = valid_combos()
    if args.place and args.temptation and (args.place, args.temptation) not in combos:
        raise StoryError(explain_rejection(PLACES[args.place], TEMPTATIONS[args.temptation]))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, temptation = rng.choice(sorted(combos))
    choice = args.choice or rng.choice(sorted(SAFE_CHOICES))
    a_name = args.a_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    b_name = args.b_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != a_name])
    grownup_name = args.grownup_name or rng.choice(["Orla", "Mira", "Tavi"])
    a_kind = rng.choice(ANIMALS)
    b_kind = rng.choice([k for k in ANIMALS if k != a_kind])
    grownup_kind = rng.choice(GROWNUPS)
    delay = 0
    return StoryParams(place, temptation, choice, a_name, b_name, grownup_name, a_kind, b_kind, grownup_kind, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TEMPTATIONS[params.temptation], SAFE_CHOICES[params.choice],
                 params.a_kind, params.b_kind, params.grownup_kind, params.a_name, params.b_name, params.grownup_name, params.delay)
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
        print(asp_program(show="#show hazard/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, t in asp_valid_combos():
            print(f"  {p} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
