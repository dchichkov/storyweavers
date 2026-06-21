#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sweep_curiosity_foreshadowing_fable.py
======================================================================

A small fable-like storyworld about a curious little helper who sweeps a place
clean, notices a small warning sign, and uses it before trouble arrives.

This world is built for the seed words:
- sweep
- Curiosity
- Foreshadowing
- Fable

The story engine keeps a tiny simulated state: dust, worry, curiosity, and a
foreshadowing sign that can be noticed before the ending. The prose is generated
from that state, not from a frozen template.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen", "fox"}
        male = {"boy", "father", "man", "owl"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    kind: str
    dusty: bool = False
    signs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    label: str
    omen: str
    meaning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    label: str
    verb: str
    object_word: str
    goal: str
    cleanup: str
    helps: str
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["sweeping"] < THRESHOLD:
            continue
        sig = ("dust", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        place = world.facts["place"]
        place.dusty = False
        out.append("__dust_removed__")
    return out


def _r_curious(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("curious", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["attention"] += 1
        out.append("__curious_notice__")
    return out


RULES = [Rule("dust", _r_dust), Rule("curious", _r_curious)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(place: Place, action: Action, sign: Sign) -> bool:
    return place.dusty and sign.id in place.signs and action.id in ACTIONS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid in ACTIONS:
            for sid in SIGNS:
                if reasonableness_gate(place, ACTIONS[aid], SIGNS[sid]):
                    combos.append((pid, aid, sid))
    return combos


@dataclass
class StoryParams:
    place: str
    action: str
    sign: str
    hero: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "barn": Place(id="barn", label="the old barn", kind="shed", dusty=True, signs={"leak"}, tags={"barn", "dust"}),
    "mill": Place(id="mill", label="the grain mill", kind="workplace", dusty=True, signs={"mouse", "leak"}, tags={"mill", "dust"}),
    "attic": Place(id="attic", label="the attic room", kind="room", dusty=True, signs={"draft", "leak"}, tags={"attic", "dust"}),
}

SIGNS = {
    "leak": Sign(id="leak", label="a thin wet stain", omen="a thin wet stain on the wall", meaning="rain was coming through the roof", tags={"leak", "rain"}),
    "draft": Sign(id="draft", label="a cold draft", omen="a cold draft under the door", meaning="the door would rattle open", tags={"draft", "wind"}),
    "mouse": Sign(id="mouse", label="tiny paw prints", omen="tiny paw prints in the dust", meaning="a visitor had been there before", tags={"mouse", "tracks"}),
}

ACTIONS = {
    "sweep": Action(id="sweep", label="sweep", verb="sweep", object_word="the floor", goal="make the place neat", cleanup="swept the dust into a tidy little heap", helps="kept the room ready", tags={"sweep", "clean"}),
    "sweep_path": Action(id="sweep_path", label="sweep the path", verb="sweep", object_word="the path", goal="clear a safe path", cleanup="swept the path clear", helps="made walking easier", tags={"sweep", "clean"}),
}

HEROES = [("Mina", "girl"), ("Pip", "boy"), ("Nora", "girl"), ("Toby", "boy")]
HELPERS = [("Owly", "owl"), ("Moss", "mouse"), ("Henna", "hen"), ("Bram", "boy")]


def tell(place: Place, action: Action, sign: Sign, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=["curious"], attrs={"place": place.id}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", traits=["wise"], attrs={"place": place.id}))
    world.facts["place"] = place
    world.facts["action"] = action
    world.facts["sign"] = sign
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["foreshadowing"] = sign.meaning

    hero.memes["curiosity"] = 2
    helper.memes["care"] = 2

    world.say(
        f"In {place.label}, {hero.id} liked to {action.verb} because {hero.pronoun()} "
        f"wanted to {action.goal}."
    )
    world.say(
        f"{helper.id} watched with a calm smile, and the little story felt as bright as a fable."
    )

    world.para()
    hero.meters["sweeping"] += 1
    place.dusty = False
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} began to {action.verb} {action.object_word}. Soon {hero.pronoun('possessive')} "
        f"{action.cleanup}, and the air felt lighter."
    )
    world.say(
        f"While working, {hero.id} noticed {sign.omen}."
    )
    hero.memes["curiosity"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} paused and asked about it. {helper.id} said the sign meant {sign.meaning}."
    )

    world.para()
    if sign.id == "leak":
        place.attrs = {"rain": True}
    if sign.id == "draft":
        place.attrs = {"wind": True}
    hero.memes["wisdom"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"That afternoon, the sign proved useful. When the weather changed, {hero.id} was ready."
    )
    world.say(
        f"So {hero.id} kept sweeping, and {helper.id} kept watch, and the place stayed safe and neat."
    )

    world.facts["outcome"] = "prepared"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable that includes the word 'sweep' and shows curiosity leading to wisdom in {f['place'].label}.",
        f"Tell a child-friendly story where {f['hero'].id} sweeps, notices {f['sign'].label}, and learns what it means before trouble arrives.",
        f"Write a fable with foreshadowing: while {f['hero'].id} is sweeping, a small sign hints at later weather, and the hint matters in the ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, place, sign, action = f["hero"], f["helper"], f["place"], f["sign"], f["action"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, a curious little {hero.type}, and {helper.id}, who helps guide the lesson. The story happens in {place.label}."
        ),
        QAItem(
            question=f"What did {hero.id} do at the start?",
            answer=f"{hero.id} began to {action.verb} {action.object_word}. {hero.pronoun('possessive').capitalize()} work made the place neat and set up the rest of the story."
        ),
        QAItem(
            question="What was the foreshadowing sign?",
            answer=f"The sign was {sign.omen}. It seemed small at first, but it hinted that {sign.meaning}."
        ),
        QAItem(
            question="How did curiosity help?",
            answer=f"Curiosity made {hero.id} stop and ask about the sign instead of ignoring it. That question turned a small clue into useful wisdom."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} still sweeping and now understanding the warning sign. The place stayed neat, and the little clue helped everyone stay ready."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    sign = world.facts["sign"]
    return [
        QAItem(
            question="What is sweeping?",
            answer="Sweeping is moving dust or crumbs into one place with a broom so the floor becomes clean. It is a simple way to care for a room."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue that hints at something important later in the story. It helps the reader notice that the ending is being prepared."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more and ask questions. A curious character pays attention and learns from small clues."
        ),
        QAItem(
            question=f"Why was {sign.label} important?",
            answer=f"{sign.label.capitalize()} mattered because it hinted at a later change in the weather or the room. The warning helped the character prepare before trouble arrived."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if bits:
            lines.append(f"{e.id}: " + " ".join(bits))
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", action="sweep", sign="leak", hero="Mina", helper="Owly"),
    StoryParams(place="mill", action="sweep_path", sign="mouse", hero="Pip", helper="Henna"),
]


def explain_rejection(place: Place, action: Action, sign: Sign) -> str:
    return f"(No story: {place.label} does not fit the chosen clue/action combination.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.action and args.sign:
        if not reasonableness_gate(PLACES[args.place], ACTIONS[args.action], SIGNS[args.sign]):
            raise StoryError(explain_rejection(PLACES[args.place], ACTIONS[args.action], SIGNS[args.sign]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.sign is None or c[2] == args.sign)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, sign = rng.choice(sorted(combos))
    hero_name, hero_type = rng.choice(HEROES)
    helper_name, helper_type = rng.choice(HELPERS)
    return StoryParams(place=place, action=action, sign=sign, hero=hero_name, helper=helper_name)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.action not in ACTIONS or params.sign not in SIGNS:
        raise StoryError("Unknown parameters.")
    world = tell(PLACES[params.place], ACTIONS[params.action], SIGNS[params.sign],
                 params.hero, "girl" if params.hero in {"Mina", "Nora"} else "boy",
                 params.helper, "owl" if params.helper == "Owly" else "hen")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable storyworld about sweep, curiosity, and foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--sign", choices=SIGNS)
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


ASP_RULES = r"""
valid(P,A,S) :- place(P), action(A), sign(S), dusty(P), has_sign(P,S), action_name(A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dusty:
            lines.append(asp.fact("dusty", pid))
        for s in sorted(p.signs):
            lines.append(asp.fact("has_sign", pid, s))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_name", aid))
    for sid in SIGNS:
        lines.append(asp.fact("sign", sid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"MISMATCH: generate smoke test failed: {exc}")
        return 1
    print("OK: verification passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
