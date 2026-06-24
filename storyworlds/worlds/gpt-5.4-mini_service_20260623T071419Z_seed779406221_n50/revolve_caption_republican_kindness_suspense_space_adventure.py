#!/usr/bin/env python3
"""
storyworlds/worlds/revolve_caption_republican_kindness_suspense_space_adventure.py
=================================================================================

A small space-adventure storyworld about a curious child, a spinning wonder, and
a careful kindness that turns suspense into a safe ending.

Seed-image story:
---
On a bright ship called the Comet Kite, a child loved to watch the station
revolve through the window. One day, a new screen caption blinked on: "Do not
tap the red captain's button." The child wanted to press it anyway, because the
button spun the view and made the whole cabin feel like a tiny planet. But the
grown-up worried it would shake the navigation dish and make the ship drift.

The child felt the suspense of waiting. Then a kind helper showed a safe dial
that could make the little model moon revolve instead. The child laughed, spun
the moon, and the ship kept gliding through the stars.

World contract:
- typed entities with physical meters and emotional memes
- state-driven premise, tension, turn, resolution
- Python reasonableness gate plus inline ASP twin
- grounded QA and trace
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: {"spin": 0.0, "risk": 0.0, "motion": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "suspense": 0.0, "kindness": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Mechanism:
    id: str
    label: str
    phrase: str
    verb: str
    risk: str
    safe_alternative: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Caption:
    id: str
    text: str
    warns: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mechanism: str
    caption: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    adult: str
    adult_type: str
    trait: str = "curious"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _rule_spread(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["spin"] >= THRESHOLD and not e.attrs.get("safe"):
            sig = ("risk", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["risk"] += 1
            out.append(f"The spinning made {e.label or e.id} feel risky.")
    return out


def _rule_suspense(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    if hero and hero.meters["risk"] >= THRESHOLD:
        sig = ("suspense", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["suspense"] += 1
            out.append("The cabin went quiet with suspense.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_spread, _rule_suspense):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mech_id, mech in MECHANISMS.items():
            if mech_id in place.affords:
                for cap_id, cap in CAPTIONS.items():
                    if "warn" in cap.tags and mech.risk in cap.warns:
                        combos.append((place_id, mech_id, cap_id))
    return combos


def build_world(place: Place, mech: Mechanism, cap: Caption,
                hero_name: str, hero_type: str, helper_name: str, helper_type: str,
                adult_name: str, adult_type: str, trait: str) -> World:
    w = World(place)
    hero = w.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper = w.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    adult = w.add(Entity(id="adult", kind="character", type=adult_type, label=adult_name, role="adult"))
    machine = w.add(Entity(id="mechanism", type="machine", label=mech.label, phrase=mech.phrase, attrs={"safe": False}))
    caption = w.add(Entity(id="caption", type="caption", label=cap.text, phrase=cap.text, attrs={"warns": cap.warns}))
    wheel = w.add(Entity(id="moon", type="moon", label="model moon", attrs={"safe": True}))
    hero.memes["joy"] = 1.0
    helper.memes["kindness"] = 1.0
    adult.memes["kindness"] = 1.0
    w.facts.update(hero=hero, helper=helper, adult=adult, mech=machine, caption=caption, moon=wheel, place=place, trait=trait)
    w.say(f"{hero_name} and {helper_name} floated inside {place.label}. {place.scene}")
    w.say(f"{hero_name} loved the way everything could revolve slowly among the stars.")
    return w


def predict_risk(w: World, mech: Mechanism) -> bool:
    sim = w.copy()
    sim.get("mechanism").meters["spin"] += 1
    propagate(sim, narrate=False)
    return sim.get("mechanism").meters["risk"] >= THRESHOLD


def tell(place: Place, mech: Mechanism, cap: Caption,
         hero_name: str, hero_type: str, helper_name: str, helper_type: str,
         adult_name: str, adult_type: str, trait: str) -> World:
    w = build_world(place, mech, cap, hero_name, hero_type, helper_name, helper_type, adult_name, adult_type, trait)
    hero = w.get("hero")
    helper = w.get("helper")
    adult = w.get("adult")
    machine = w.get("mechanism")
    moon = w.get("moon")

    w.para()
    w.say(f"On the control screen, a caption blinked: “{cap.text}”")
    w.say(f"{hero.label} reached toward the {mech.label}, because it promised to {mech.verb}.")
    hero.memes["suspense"] += 1
    if predict_risk(w, mech):
        w.say(f"But {adult.label} noticed the {mech.risk} problem first.")
        adult.memes["kindness"] += 1
        w.say(f"“{cap.warns},” {adult.label} said gently.")
        w.say(f"{helper.label} held up a safe dial and showed how the little moon could revolve instead.")
        helper.memes["kindness"] += 1
        machine.attrs["safe"] = True
        moon.attrs["safe"] = True
        moon.meters["spin"] += 1
        hero.memes["joy"] += 1
        hero.memes["suspense"] = 0.0
        w.say(f"{hero.label} turned the dial, and the model moon began to revolve in a soft silver circle.")
        w.say(f"The ship stayed steady, and the stars kept sliding past the window.")
    else:
        w.say(f"{hero.label} touched the {mech.label}, and it spun happily without any trouble.")
        moon.meters["spin"] += 1
        hero.memes["joy"] += 1
        w.say(f"The little moon revolved while everyone laughed, and the cabin felt bright and safe.")
    propagate(w)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    adult = f["adult"].label
    mech = f["mech"].label
    place = f["place"].label
    return [
        f"Write a tiny space adventure where {hero} wants to use the {mech} at {place}, but {adult} worries and {helper} helps find a safe way.",
        f"Tell a child-friendly story with the words revolve, caption, and republican, ending with kindness and suspense turning into a safe choice.",
        f"Write a short space story where a caption on the screen warns the crew, and the model moon revolves instead of the risky machine.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    adult = f["adult"].label
    mech = f["mech"].label
    place = f["place"].label
    return [
        QAItem(
            question=f"Who wanted to use the {mech.label} at {place.label}?",
            answer=f"{hero} wanted to use it because it looked like a fun way to make the ship revolve.",
        ),
        QAItem(
            question=f"Why did {adult} warn everyone?",
            answer=f"{adult} warned them because the {mech.risk} problem could make the ship feel shaky and unsafe.",
        ),
        QAItem(
            question=f"How did {helper} help?",
            answer=f"{helper} showed a safer dial, so the model moon could revolve without causing trouble.",
        ),
        QAItem(
            question="What changed at the end?",
            answer="The suspense faded, the ship stayed steady, and the crew chose kindness over the risky idea.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does revolve mean?",
            answer="Revolve means to move around in a circle, like a moon going around a planet.",
        ),
        QAItem(
            question="What is a caption?",
            answer="A caption is a short line of words that explains a picture, screen, or scene.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle and helpful to someone else.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the waiting feeling you get when you do not know what will happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: label={e.label!r} meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} } attrs={ {k:v for k,v in e.attrs.items() if v} }")
    return "\n".join(lines)


PLACES = {
    "orbit_lab": Place(id="orbit_lab", label="the orbit lab", scene="The lab windows showed a giant blue planet turning below.", affords={"gyro", "caption"}),
    "star_deck": Place(id="star_deck", label="the star deck", scene="Lights blinked like tiny constellations across the ceiling.", affords={"gyro", "caption"}),
}
MECHANISMS = {
    "gyro": Mechanism(id="gyro", label="gyro wheel", phrase="a shiny wheel", verb="make the station tilt and spin", risk="motion", safe_alternative="moon dial", tags={"spin", "risk"}),
    "caption": Mechanism(id="caption", label="caption panel", phrase="a glowing panel", verb="flash a warning caption", risk="risk", safe_alternative="moon dial", tags={"caption", "warn"}),
}
CAPTIONS = {
    "red": Caption(id="red", text="Do not press the red button", warns="this could make the cabin shake", tags={"warn"}),
    "orbit": Caption(id="orbit", text="Let the model moon revolve only", warns="the motion should stay small", tags={"warn"}),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Zoe", "Luna"]
BOY_NAMES = ["Finn", "Leo", "Eli", "Max", "Noah"]
TRAITS = ["curious", "gentle", "brave", "careful"]

CURATED = [
    StoryParams(place="orbit_lab", mechanism="gyro", caption="red", hero="Luna", hero_type="girl", helper="Finn", helper_type="boy", adult="Captain Reed", adult_type="man", trait="curious"),
    StoryParams(place="star_deck", mechanism="caption", caption="orbit", hero="Mia", hero_type="girl", helper="Noah", helper_type="boy", adult="Commander Hale", adult_type="woman", trait="careful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny space-adventure storyworld about a revolving wonder, a caption, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mechanism", choices=MECHANISMS)
    ap.add_argument("--caption", choices=CAPTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-type", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mechanism is None or c[1] == args.mechanism)
              and (args.caption is None or c[2] == args.caption)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, mech, cap = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    adult = args.adult or ("Captain Reed" if rng.random() < 0.5 else "Commander Hale")
    adult_type = args.adult_type or rng.choice(["woman", "man"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mechanism=mech, caption=cap, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, adult=adult, adult_type=adult_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    mech = MECHANISMS[params.mechanism]
    cap = CAPTIONS[params.caption]
    if (place.id, mech.id, cap.id) not in valid_combos():
        raise StoryError("Invalid story parameters.")
    world = tell(place, mech, cap, params.hero, params.hero_type, params.helper, params.helper_type, params.adult, params.adult_type, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


ASP_RULES = r"""
valid(P,M,C) :- place(P), mechanism(M), caption(C), affords(P,M), warns(C, risk_of(M)).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.id, a))
    for m in MECHANISMS.values():
        lines.append(asp.fact("mechanism", m.id))
        lines.append(asp.fact("risk_of", m.id, m.risk))
    for c in CAPTIONS.values():
        lines.append(asp.fact("caption", c.id))
        for t in sorted(c.tags):
            lines.append(asp.fact("warns", c.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("Mismatch")
        print("python-only", sorted(py - cl))
        print("clingo-only", sorted(cl - py))
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
    if not sample.story:
        return 1
    print("OK")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        for x in asp_valid_combos():
            print(x)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
