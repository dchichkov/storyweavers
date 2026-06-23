#!/usr/bin/env python3
"""
storyworlds/worlds/tamale_bugle_flashback_happy_ending_fairy_tale.py
====================================================================

A small fairy-tale storyworld about a royal feast, a missing tamale, and a bugle
call that brings back a memory. The stories are built from simulated state:
characters have physical meters and emotional memes, the world tracks objects,
and a flashback lets the tale remember how the tamale was made.

Seed premise:
- A child or helper wants to bring a tamale to a feast.
- A bugle is used to call everyone together.
- A flashback explains where the tamale came from or why it matters.
- The story ends happily with the tamale shared and the bugle sounding again.

The world is intentionally small and child-facing, with a fairy-tale tone.
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    helper: str = ""
    carries: str = ""
    makes_sound: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "princess", "woman"}
        male = {"boy", "father", "king", "prince", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = False
    uses: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    container: str
    special: str
    at_risk: str
    favored_by: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    phrase: str
    purpose: str
    carries: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_used = False

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.flashback_used = self.flashback_used
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_memory(world: World) -> list[str]:
    out: list[str] = []
    if not world.flashback_used:
        return out
    for ent in world.characters():
        if ent.memes["remember"] < THRESHOLD:
            continue
        sig = ("remember", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hope"] += 1
        out.append("__flashback__")
    return out


def _r_shared(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("sharing_done"):
        return out
    if world.facts.get("meal_ready") and world.facts.get("tamale_present"):
        world.facts["sharing_done"] = True
        for ent in world.characters():
            ent.memes["joy"] += 1
        out.append("__share__")
    return out


CAUSAL_RULES = [Rule("memory", "social", _r_memory), Rule("shared", "social", _r_shared)]


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


def prize_at_risk(treat: Treat, place: Place) -> bool:
    return treat.special in place.uses


def select_signal(treat: Treat, place: Place) -> Optional[Signal]:
    for sig in SIGNALS:
        if treat.special in sig.tags and place.label in sig.tags:
            return sig
    return None


def setup_flashback(world: World, hero: Entity, elder: Entity, treat: Treat) -> None:
    hero.memes["remember"] += 1
    world.flashback_used = True
    world.say(
        f"Long ago, in the warm kitchen of the old cottage, {hero.id} had watched "
        f"{elder.id} fold corn dough around the savory filling."
    )
    world.say(
        f"The memory smelled like steam and butter, and that was why {hero.id} "
        f"loved {treat.label} so much."
    )
    propagate(world, narrate=True)


def gather(world: World, hero: Entity, signal: Signal, place: Place) -> None:
    hero.meters["distance"] += 1
    world.say(
        f"At the palace door, {hero.id} lifted the {signal.label} and blew a bright note. "
        f"The bugle called everyone to the hall."
    )
    world.say(
        f"The note floated over {place.label}, like a ribbon of gold."
    )


def worry(world: World, elder: Entity, hero: Entity, treat: Treat) -> None:
    elder.memes["care"] += 1
    hero.memes["want"] += 1
    world.say(
        f"{elder.id} worried that the feast would be too late if the {treat.label} "
        f"grew cold, but {hero.id} promised to hurry."
    )


def carry_treat(world: World, hero: Entity, treat: Treat) -> None:
    hero.meters["careful"] += 1
    treat_entity = world.get("tamale")
    treat_entity.meters["warmth"] += 1
    world.facts["tamale_present"] = True
    world.say(
        f"{hero.id} carried the {treat.label} in a little cloth wrap, so it stayed warm."
    )


def feast_turn(world: World, hero: Entity, elder: Entity, place: Place) -> None:
    world.facts["meal_ready"] = True
    world.say(
        f"Inside the hall, lanterns glowed, the table was set, and the guests waited kindly."
    )
    world.say(
        f"When {hero.id} arrived, the room felt as happy as a song."
    )


def ending(world: World, hero: Entity, elder: Entity, signal: Signal, treat: Treat) -> None:
    hero.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f"{hero.id} opened the cloth wrap, and the {treat.label} was still warm."
    )
    world.say(
        f"{elder.id} smiled, and {hero.id} blew the {signal.label} once more."
    )
    world.say(
        f"The happy note rang above the feast while everyone shared the {treat.label} "
        f"and ate with bright, buttery smiles."
    )


def tell(place: Place, treat: Treat, signal: Signal, hero_name: str, hero_type: str,
         elder_name: str, elder_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, label=elder_name))
    tamale = world.add(Entity(id="tamale", type="food", label=treat.label, phrase=treat.phrase))
    bugle = world.add(Entity(id="bugle", type="signal", label=signal.label, phrase=signal.phrase, makes_sound=True))

    world.facts = {
        "hero": hero,
        "elder": elder,
        "tamale": tamale,
        "bugle": bugle,
        "place": place,
        "treat": treat,
        "signal": signal,
        "tamale_present": False,
        "meal_ready": False,
        "sharing_done": False,
    }

    world.say(
        f"Once upon a time, {hero.id} lived in {place.label}, where the banners fluttered and the bells were kind."
    )
    world.say(
        f"{hero.id} loved the {treat.label}, a {treat.phrase}, because {elder.id} had made it with care."
    )

    world.para()
    setup_flashback(world, hero, elder, treat)
    gather(world, hero, signal, place)
    worry(world, elder, hero, treat)
    carry_treat(world, hero, treat)

    world.para()
    feast_turn(world, hero, elder, place)
    if prize_at_risk(treat, place):
        world.say(
            f"Even so, the {treat.label} was safe, because it stayed wrapped until the last moment."
        )
    ending(world, hero, elder, signal, treat)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "castle": Place(id="castle", label="the castle hall", indoor=True, uses={"warm", "shared"}),
    "garden": Place(id="garden", label="the rose garden", indoor=False, uses={"warm", "shared"}),
    "cottage": Place(id="cottage", label="the little cottage", indoor=True, uses={"warm", "shared"}),
}

TAMALES = {
    "cheese": Treat(id="cheese", label="cheese tamale", phrase="soft cheese tamale", container="cloth wrap", special="warm", at_risk="cold", favored_by={"girl", "boy"}),
    "bean": Treat(id="bean", label="bean tamale", phrase="bean tamale with green sauce", container="cloth wrap", special="warm", at_risk="cold", favored_by={"girl", "boy"}),
    "sweet": Treat(id="sweet", label="sweet tamale", phrase="sweet tamale with cinnamon", container="cloth wrap", special="warm", at_risk="cold", favored_by={"girl", "boy"}),
}

SIGNALS = [
    Signal(id="bugle", label="bugle", phrase="a brass bugle", purpose="call the feast together", carries="sound", tags={"warm", "castle", "garden", "cottage"}),
    Signal(id="trumpet", label="bugle", phrase="a bright bugle", purpose="call the feast together", carries="sound", tags={"warm", "castle", "garden", "cottage"}),
]

GIRL_NAMES = ["Mira", "Luna", "Ivy", "Nora", "Elsa", "Rose"]
BOY_NAMES = ["Finn", "Pax", "Theo", "Eli", "Robin", "Gus"]


@dataclass
class StoryParams:
    place: str
    tamale: str
    signal: str
    hero_name: str
    hero_type: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, s.id) for p in SETTINGS for t in TAMALES for s in SIGNALS if s.id == "bugle" and prize_at_risk(TAMALES[t], SETTINGS[p])]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale about {f["hero"].id} in {f["place"].label} with a {f["signal"].label}, and include the word "tamale".',
        f"Tell a happy fairy tale where {f['elder'].id} makes a {f['tamale'].label} and a {f['hero'].id} uses a {f['signal'].label} to gather the court.",
        f"Write a short story with a flashback, a bugle, and a warm {f['tamale'].label} shared at the feast.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, tamale, signal, place = f["hero"], f["elder"], f["tamale"], f["signal"], f["place"]
    return [
        QAItem(
            question=f"Who is the story about when {hero.id} brings the {tamale.label} to {place.label}?",
            answer=f"It is about {hero.id} and {elder.id}. {hero.id} carries the {tamale.label} through {place.label} for the feast.",
        ),
        QAItem(
            question=f"Why did the story pause for a flashback?",
            answer=f"It paused to remember how the {tamale.label} was made in the old cottage. The memory explains why {hero.id} cared so much about bringing it safely to the hall.",
        ),
        QAItem(
            question=f"What did the {signal.label} do in the story?",
            answer=f"The {signal.label} called everyone together with a bright sound. It helped the guests gather for the happy feast.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the {tamale.label}?",
            answer=f"The story ended happily because the {tamale.label} stayed warm and was shared at the feast. {hero.id} blew the {signal.label} again, and everyone smiled at the bright note.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tamale?",
            answer="A tamale is a warm food made with soft corn dough around a filling. People often wrap it so it stays cozy until mealtime.",
        ),
        QAItem(
            question="What is a bugle?",
            answer="A bugle is a brass horn that makes a loud, clear note. It can be used to call people to gather.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that goes back to something that happened before. It helps explain why a character feels the way they do now.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts: {{'tamale_present': {world.facts.get('tamale_present')}, 'meal_ready': {world.facts.get('meal_ready')}, 'sharing_done': {world.facts.get('sharing_done')}}}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="castle", tamale="cheese", signal="bugle", hero_name="Mira", hero_type="girl", elder_name="Queen Alma", elder_type="queen"),
    StoryParams(place="garden", tamale="bean", signal="bugle", hero_name="Finn", hero_type="boy", elder_name="King Rowan", elder_type="king"),
    StoryParams(place="cottage", tamale="sweet", signal="bugle", hero_name="Nora", hero_type="girl", elder_name="Grandma June", elder_type="woman"),
]


ASP_RULES = r"""
world_place(P) :- place(P).
has_tamale(T) :- tamale(T).
has_signal(S) :- signal(S).
valid(P,T,S) :- world_place(P), has_tamale(T), has_signal(S), place_works(P,T).
place_works(P,T) :- warm_place(P), tamale_warm(T).
flashback_story :- valid(_,_,_).
happy_end :- flashback_story.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("warm_place", pid))
    for tid, t in TAMALES.items():
        lines.append(asp.fact("tamale", tid))
        lines.append(asp.fact("tamale_warm", tid))
    for sid, s in SIGNALS:
        lines.append(asp.fact("signal", sid))
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
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH in valid_combos:")
        if cl - py:
            print(" only in clingo:", sorted(cl - py))
        if py - cl:
            print(" only in python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, tamale=None, signal=None), random.Random(7)))
        _ = sample.story
    except Exception as ex:
        ok = False
        print(f"SMOKE FAILED: {ex}")
    if ok:
        print(f"OK: ASP matches Python for {len(py)} combos; smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld of a tamale, a bugle, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tamale", choices=TAMALES)
    ap.add_argument("--signal", choices=["bugle"])
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (args.tamale is None or c[1] == args.tamale)
              and (args.signal is None or c[2] == args.signal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tamale, signal = rng.choice(list(combos))
    hero_type = rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    elder_type = rng.choice(["queen", "king", "woman", "man"])
    elder_name = args.elder or rng.choice(["Queen Alma", "King Rowan", "Grandma June", "Old Tom"])
    return StoryParams(place=place, tamale=tamale, signal=signal, hero_name=hero_name, hero_type=hero_type, elder_name=elder_name, elder_type=elder_type)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.tamale not in TAMALES:
        raise StoryError(f"Unknown tamale: {params.tamale}")
    if params.signal != "bugle":
        raise StoryError(f"Unknown signal: {params.signal}")
    world = tell(SETTINGS[params.place], TAMALES[params.tamale], SIGNALS[0], params.hero_name, params.hero_type, params.elder_name, params.elder_type)
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
        for p, t, s in combos:
            print(f"  {p:8} {t:8} {s}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
