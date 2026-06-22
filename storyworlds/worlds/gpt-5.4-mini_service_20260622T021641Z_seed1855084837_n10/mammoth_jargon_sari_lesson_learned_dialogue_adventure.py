#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T021641Z_seed1855084837_n10/mammoth_jargon_sari_lesson_learned_dialogue_adventure.py
=============================================================================================================

A small adventure storyworld about a child explorer, a lost mammoth path, a sari,
and the lesson learned from confusing jargon with clear talk.

Seed tale:
---
Nina loved adventure stories. One windy morning, she and her uncle Amir climbed
the hill path behind the village to look for the old blue kite that had blown
away.

At the stone arch, they found a giant woolly mammoth-shaped statue with a faded
sign full of jargon. Amir read it carefully and laughed. "It just says the trail
is safe if you stay left and don't step on the soft grass," he said.

Then they heard a rustle. A real baby mammoth was tangled in the kite string
near a berry bush. Beside it stood a woman in a bright sari, calling softly,
"Easy, little one. Stay calm."

Nina wanted to dash over, but Amir told her, "Use simple words. The mammoth is
scared, not mean." Nina nodded, spoke gently, and helped guide the baby mammoth
free. The woman thanked them and gave Nina a ribbon for the kite.

Lesson learned: clear words help more than noisy jargon.

Contract beats in this world:
- Dialogue matters: characters speak in short, concrete lines.
- Lesson learned matters: confusion drops when characters choose clear speech.
- Adventure style: a small journey, a discovery, a careful risk, and a resolved ending.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    terrain: str
    affords: set[str] = field(default_factory=set)
    danger_spots: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    noun: str
    jargon: str
    risk: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    event: str
    child_name: str
    child_gender: str
    adult_gender: str
    sari_color: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.focus_zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.focus_zone = set(self.focus_zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("confusion", 0.0) < THRESHOLD:
            continue
        sig = ("confusion", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] = ent.memes.get("worry", 0.0) + 1
        out.append(f"{ent.label or ent.id} looked puzzled.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("simple_words_used") and not world.facts.get("lesson_learned"):
        return out
    for ent in world.entities.values():
        if ent.memes.get("confusion", 0.0) < THRESHOLD:
            continue
        sig = ("calm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["confusion"] = 0.0
        ent.memes["confidence"] = ent.memes.get("confidence", 0.0) + 1
        out.append(f"{ent.label or ent.id} understood better after that.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("confusion", "mental", _r_confusion),
    Rule("calm", "mental", _r_calm),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def event_at_risk(event: Event, place: Place) -> bool:
    return bool(event.zone & place.danger_spots)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for eid, ev in EVENTS.items():
            if event_at_risk(ev, place):
                combos.append((pid, eid))
    return combos


def predict_world(world: World, child: Entity, event: Event) -> dict:
    sim = world.copy()
    child_sim = sim.get(child.id)
    child_sim.memes["confusion"] += 1
    propagate(sim, narrate=False)
    return {
        "confusion": child_sim.memes.get("confusion", 0.0),
        "worry": child_sim.memes.get("worry", 0.0),
    }


def setup(world: World, child: Entity, adult: Entity, event: Event) -> None:
    child.memes["curiosity"] = 1
    child.memes["joy"] = 1
    adult.memes["calm"] = 1
    world.say(
        f"{child.id} loved adventure and wanted to {event.verb} near {world.place.label}."
    )
    world.say(
        f"{adult.id} wore a sari and carried a patient smile."
    )


def arrive(world: World, child: Entity, adult: Entity, event: Event) -> None:
    world.say(
        f"One breezy morning, {child.id} and {adult.id} walked to {world.place.label}."
    )
    world.say(
        f"The path felt {world.place.terrain}, and a sign nearby was full of jargon."
    )


def warn(world: World, adult: Entity, child: Entity, event: Event) -> None:
    pred = predict_world(world, child, event)
    adult.memes["care"] = adult.memes.get("care", 0.0) + 1
    world.facts["predicted_confusion"] = pred["confusion"]
    world.say(
        f'"Use simple words," {adult.id} said. "The sign is noisy, but the trail only needs care."'
    )


def story_risk(world: World, child: Entity, event: Event) -> None:
    child.memes["confusion"] += 1
    world.facts["simple_words_used"] = False
    if event.id == "mammoth":
        world.say(
            f"{child.id} paused by a woolly mammoth marker and felt unsure."
        )
    else:
        world.say(
            f"{child.id} paused by the {event.noun} and listened closely."
        )


def dialogue_turn(world: World, child: Entity, adult: Entity, event: Event) -> None:
    world.say(
        f'"What does that mean?" {child.id} asked.'
    )
    world.say(
        f'"It means stay left, keep off the soft grass, and speak plainly," {adult.id} said.'
    )


def resolve(world: World, child: Entity, adult: Entity, event: Event, sari_color: str) -> None:
    child.memes["joy"] += 1
    child.memes["confidence"] = child.memes.get("confidence", 0.0) + 1
    child.memes["confusion"] = 0.0
    world.facts["lesson_learned"] = True
    world.facts["simple_words_used"] = True
    world.say(
        f"Then they found a real baby mammoth near a berry bush, and a woman in a {sari_color} sari spoke softly."
    )
    world.say(
        f'"Easy, little one," she said. "Stay calm."'
    )
    world.say(
        f"{child.id} nodded, used clear words, and helped guide the little mammoth free."
    )
    world.say(
        f"The woman thanked {child.id} and tied a ribbon to the kite as a gift."
    )
    world.say(
        f"By the end, {child.id} knew that clear talk could help more than jargon."
    )


def tell(place: Place, event: Event, child_name: str, child_gender: str, adult_gender: str, sari_color: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, label=child_name, role="child", meters={"meters": 0.0}, memes={"curiosity": 0.0, "joy": 0.0, "confusion": 0.0, "confidence": 0.0}))
    adult = world.add(Entity(id="Amir", kind="character", type=adult_gender, label="Amir", role="guide", meters={"meters": 0.0}, memes={"care": 0.0, "calm": 0.0}))
    mammoth = world.add(Entity(id="mammoth", kind="thing", type="thing", label="baby mammoth", role="wild", meters={"meters": 0.0}, memes={"fear": 0.0}))
    sari = world.add(Entity(id="sari", kind="thing", type="thing", label=f"{sari_color} sari", role="clothing", meters={"meters": 0.0}, memes={"brightness": 0.0}))
    world.facts.update(child=child, adult=adult, mammoth=mammoth, sari=sari, event=event, place=place, sari_color=sari_color, simple_words_used=False, lesson_learned=False)
    setup(world, child, adult, event)
    world.para()
    arrive(world, child, adult, event)
    warn(world, adult, child, event)
    story_risk(world, child, event)
    dialogue_turn(world, child, adult, event)
    world.para()
    resolve(world, child, adult, event, sari_color)
    return world


PLACES = {
    "hill_path": Place(id="hill_path", label="the hill path", terrain="windy", affords={"mammoth"}, danger_spots={"trail", "grass"}),
    "stone_arch": Place(id="stone_arch", label="the stone arch", terrain="rocky", affords={"mammoth"}, danger_spots={"trail", "grass"}),
    "river_bend": Place(id="river_bend", label="the river bend", terrain="muddy", affords={"mammoth"}, danger_spots={"water", "bank"}),
}

EVENTS = {
    "mammoth": Event(id="mammoth", verb="follow the mammoth trail", noun="mammoth trail", jargon="jargon", risk="confusing sign", zone={"trail", "grass"}, tags={"mammoth", "jargon", "adventure"}),
}

COLORS = ["blue", "red", "gold", "green", "purple"]

GIRL_NAMES = ["Nina", "Asha", "Maya", "Lina", "Tia"]
BOY_NAMES = ["Arun", "Ravi", "Milo", "Kian", "Omar"]


def valid_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


@dataclass
class StoryParams:
    place: str
    event: str
    child_name: str
    child_gender: str
    adult_gender: str
    sari_color: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: mammoth, jargon, sari, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-gender", choices=["woman", "man"])
    ap.add_argument("--sari-color", choices=COLORS)
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
              if (args.place is None or c[0] == args.place)
              and (args.event is None or c[1] == args.event)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, event = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    child_name = args.name or valid_name(child_gender, rng)
    sari_color = args.sari_color or rng.choice(COLORS)
    return StoryParams(place=place, event=event, child_name=child_name, child_gender=child_gender, adult_gender=adult_gender, sari_color=sari_color)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "mammoth", "jargon", and "sari".',
        f"Tell a story where {f['child'].id} meets a mammoth trail, asks what the jargon means, and learns from a calm guide in a sari.",
        f"Write a short adventurous scene with dialogue and a clear lesson learned about using simple words.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    place = f["place"]
    out = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.id}, who goes on an adventure with {adult.id} to {place.label}. They meet a scary-looking but helpful trail and learn something new.",
        ),
        QAItem(
            question=f"Why did {child.id} ask what the jargon meant?",
            answer=f"{child.id} saw a sign full of confusing jargon and did not understand it right away. {adult.id} explained the message in simple words so the path felt easier and safer.",
        ),
        QAItem(
            question=f"What helped {child.id} guide the baby mammoth free?",
            answer=f"Clear talk helped. {child.id} listened, used gentle words, and stayed calm while the woman in the sari spoke softly beside the bush.",
        ),
    ]
    if f.get("lesson_learned"):
        out.append(QAItem(
            question=f"What lesson did {child.id} learn by the end?",
            answer=f"{child.id} learned that clear words help more than jargon. The lesson mattered because simple speech helped everyone calm down and solve the problem.",
        ))
    return out


WORLD_KNOWLEDGE = {
    "mammoth": [
        ("What is a mammoth?", "A mammoth was a huge elephant-like animal with thick fur and long tusks. It lived a very long time ago, and people still talk about it in stories."),
    ],
    "jargon": [
        ("What is jargon?", "Jargon is special or fancy language that can be hard to understand. Simple words are often better when you want everyone to follow along."),
    ],
    "sari": [
        ("What is a sari?", "A sari is a long piece of cloth worn by many women in South Asia. It is wrapped in a special way and can be bright and beautiful."),
    ],
    "adventure": [
        ("What is an adventure story?", "An adventure story is about a journey, a discovery, or a challenge. The characters explore something new and learn as they go."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(q, a) for key in ("adventure", "mammoth", "jargon", "sari") for q, a in WORLD_KNOWLEDGE[key]]


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


ASP_RULES = r"""
risk(P,E) :- place(P), event(E), danger_spot(P,S), event_zone(E,S).
valid(P,E) :- risk(P,E).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for d in sorted(p.danger_spots):
            lines.append(asp.fact("danger_spot", pid, d))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        for z in sorted(e.zone):
            lines.append(asp.fact("event_zone", eid, z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and python valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, event=None, name=None, child_gender=None, adult_gender=None, sari_color=None), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=False, qa=False)
    return rc


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        me = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if me:
            bits.append(f"memes={me}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.event not in EVENTS:
        raise StoryError("invalid story params")
    place = PLACES[params.place]
    event = EVENTS[params.event]
    world = tell(place, event, params.child_name, params.child_gender, params.adult_gender, params.sari_color)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
    StoryParams(place="hill_path", event="mammoth", child_name="Nina", child_gender="girl", adult_gender="man", sari_color="blue"),
    StoryParams(place="stone_arch", event="mammoth", child_name="Asha", child_gender="girl", adult_gender="woman", sari_color="red"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
