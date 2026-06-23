#!/usr/bin/env python3
"""
storyworlds/worlds/pitch_ruminant_teamwork_suspense_bad_ending_rhyming.py
=========================================================================

A standalone storyworld for a small rhyming tale about teamwork, suspense,
pitch, and a ruminant -- with a bad ending that still feels like a complete,
state-driven story.

The world is intentionally tiny:
- a place with a few affordances,
- a child pair trying to help,
- a ruminant in some trouble,
- sticky pitch that can spread mess and fear,
- a suspenseful teamwork beat,
- and an ending image proving what changed.

The prose is generated from simulated world state rather than from a fixed
template with swapped nouns.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    key: str
    label: str
    dark: bool = False
    sticky: bool = False
    noisy: bool = False


@dataclass
class Ruminant:
    key: str
    label: str
    sound: str
    fear_word: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    key: str
    label: str
    verb: str
    risk: str
    mess: str
    risk_zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    key: str
    label: str
    verb: str
    finish: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.zone: set[str] = set()

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["pitch"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["sticky"] += 1
        e.memes["worry"] += 1
        out.append(f"{e.label} got sticky with pitch.")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("suspense"):
        return out
    for e in world.characters():
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append(f"{e.label} felt a shiver in the dark.")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("fear", _r_fear)]


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


def predict_mess(world: World, actor: Entity, trouble: Trouble) -> dict[str, object]:
    sim = world.copy()
    sim.get(actor.id).meters["pitch"] += 1
    propagate(sim, narrate=False)
    return {"sticky": sim.get(actor.id).meters["sticky"], "fear": sim.get(actor.id).memes["fear"]}


def valid_combo(place: Place, trouble: Trouble) -> bool:
    if trouble.key == "pitch" and not place.sticky:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES.values():
        for r in RUMINANTS:
            for t in TROUBLES.values():
                if valid_combo(p, t):
                    out.append((p.key, r.key, t.key))
    return out


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def setup(world: World, kid1: Entity, kid2: Entity, animal: Entity, trouble: Trouble) -> None:
    kid1.memes["joy"] += 1
    kid2.memes["joy"] += 1
    world.say(
        f"{kid1.label} and {kid2.label} came with a plan in the moon-bright light, "
        f"to help the poor {animal.label} before the night got tight."
    )
    world.say(
        f"At {world.place.label}, they saw {animal.label} near {trouble.risk}, "
        f"and the dark felt wide and deep."
    )


def teamwork(world: World, kid1: Entity, kid2: Entity, animal: Entity, trouble: Trouble) -> None:
    world.facts["suspense"] = True
    kid1.memes["teamwork"] += 1
    kid2.memes["teamwork"] += 1
    world.say(
        f'"Hold the rope," said {kid1.label}. "You pull, I poke!" said {kid2.label}. '
        f'Their teamwork made a brave little hope.'
    )


def warn(world: World, kid1: Entity, trouble: Trouble, animal: Entity) -> None:
    pred = predict_mess(world, kid1, trouble)
    world.facts["pred"] = pred
    world.say(
        f'"That pitch looks thick," {kid1.label} said, "and slick, and black." '
        f'But the {animal.label} only blinked and stepped back.'
    )


def slip(world: World, kid1: Entity, kid2: Entity, trouble: Trouble) -> None:
    kid1.meters["pitch"] += 1
    kid2.meters["pitch"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They reached too fast, and the pitch went splash; "
        f"their shoes turned slow and their hands went ash."
    )


def ending_bad(world: World, animal: Entity, trouble: Trouble, method: Method) -> None:
    animal.memes["fear"] += 1
    world.say(
        f"The {animal.label} bolted away with a startled hop, and the helpers stood still. "
        f"{method.finish.capitalize()}, but the trail ended in a tearful snarl."
    )
    world.say(
        f"By the fence lay sticky pitch and a lonely puff of dust, "
        f"and the {animal.label} stayed far off in the dusk."
    )


def tell(place: Place, ruminant: Ruminant, trouble: Trouble, method: Method,
         name1: str = "Mina", name2: str = "Toby",
         gender1: str = "girl", gender2: str = "boy") -> World:
    world = World(place)
    a = world.add(Entity(id=name1, kind="character", type=gender1, label=name1))
    b = world.add(Entity(id=name2, kind="character", type=gender2, label=name2))
    animal = world.add(Entity(id="animal", kind="character", type="thing", label=ruminant.label,
                              plural=ruminant.plural, attrs={"ruminant": ruminant.key}))
    world.facts.update(
        kid1=a, kid2=b, animal=animal, place=place, ruminant=ruminant,
        trouble=trouble, method=method
    )
    setup(world, a, b, animal, trouble)
    world.para()
    teamwork(world, a, b, animal, trouble)
    warn(world, a, trouble, animal)
    slip(world, a, b, trouble)
    world.para()
    ending_bad(world, animal, trouble, method)
    return world


SETTINGS = {
    "barn": Place("barn", "the barn", dark=True, sticky=True, noisy=False),
    "yard": Place("yard", "the yard", dark=True, sticky=True, noisy=True),
    "lane": Place("lane", "the lane", dark=True, sticky=True, noisy=False),
}

RUMINANTS = [
    Ruminant("goat", "goat", "bleat", "nervous", tags={"goat", "ruminant"}),
    Ruminant("sheep", "sheep", "baa", "shaky", tags={"sheep", "ruminant"}),
    Ruminant("calf", "calf", "moo", "glum", tags={"calf", "ruminant"}),
]

TROUBLES = {
    "pitch": Trouble("pitch", "pitch", "lift", "stuck in the pitch", "sticky pitch", "ground", tags={"pitch"}),
    "gate": Trouble("gate", "gate", "push", "at the gate", "jammed gate", "gate", tags={"gate"}),
    "ditch": Trouble("ditch", "ditch", "pull", "by the ditch", "dark ditch", "ditch", tags={"ditch"}),
}

METHODS = {
    "rope": Method("rope", "rope pull", "pull", "they tugged and took a bow", 1, tags={"teamwork"}),
    "lift": Method("lift", "lift together", "lift", "they heaved and gave a whirl", 1, tags={"teamwork"}),
    "push": Method("push", "push together", "push", "they shoved with all their might", 1, tags={"teamwork"}),
}

PLACES = SETTINGS

GIRL_NAMES = ["Mina", "Pia", "Lena", "Nora", "Sage"]
BOY_NAMES = ["Toby", "Milo", "Arlo", "Finn", "Owen"]


@dataclass
class StoryParams:
    place: str
    ruminant: str
    trouble: str
    method: str
    name1: str
    gender1: str
    name2: str
    gender2: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story that includes the words "pitch" and "ruminant".',
        f"Tell a suspenseful teamwork story where {f['kid1'].label} and {f['kid2'].label} try to help a {f['ruminant'].label} near {f['place'].label}.",
        f"Write a child-friendly bad-ending rhyme about sticky pitch, brave teamwork, and a {f['ruminant'].label} that gets scared away.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, animal, place, trouble = f["kid1"], f["kid2"], f["animal"], f["place"], f["trouble"]
    return [
        QAItem(
            question=f"Who tried to help the {animal.label} at {place.label}?",
            answer=f"{a.label} and {b.label} tried to help together. They worked as a team, but the dark made the moment feel tense.",
        ),
        QAItem(
            question=f"Why did the pitch make the rescue harder?",
            answer=f"The pitch was sticky and black, so it slowed their shoes and made their hands messy. That made the rescue feel uncertain and gave the story its suspense.",
        ),
        QAItem(
            question=f"What happened to the {animal.label} at the end?",
            answer=f"The {animal.label} got frightened and ran off into the dark. The helpers were left with sticky pitch and an unhappy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pitch?",
            answer="Pitch is a thick, sticky black stuff. It can make shoes and hands messy and hard to clean.",
        ),
        QAItem(
            question="What is a ruminant?",
            answer="A ruminant is an animal that chews its food again later, like a goat, sheep, or cow.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together to do one job. Each helper does a part, and the job can feel easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this tiny world only works in sticky places where pitch can make the rescue tense.)"


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS.values():
        lines.append(asp.fact("place", p.key))
        if p.sticky:
            lines.append(asp.fact("sticky", p.key))
    for r in RUMINANTS:
        lines.append(asp.fact("ruminant", r.key))
    for t in TROUBLES.values():
        lines.append(asp.fact("trouble", t.key))
        if t.key == "pitch":
            lines.append(asp.fact("sticky_trouble", t.key))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,R,T) :- place(P), ruminant(R), trouble(T), sticky(P), sticky_trouble(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    sample = generate(resolve_params(argparse.Namespace(place=None, ruminant=None, trouble=None, method=None, seed=None), random.Random(7)))
    if not sample.story:
        return 1
    if ok:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        print("OK: smoke test story generated.")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about pitch, teamwork, suspense, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ruminant", choices=[r.key for r in RUMINANTS])
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
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
              and (args.ruminant is None or c[1] == args.ruminant)
              and (args.trouble is None or c[2] == args.trouble)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, r, t = rng.choice(sorted(combos))
    method = args.method or rng.choice(sorted(METHODS))
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    gender2 = args.gender2 or ("boy" if gender1 == "girl" else "girl")
    name1 = args.name1 or rng.choice(GIRL_NAMES if gender1 == "girl" else BOY_NAMES)
    name2 = args.name2 or rng.choice([n for n in (GIRL_NAMES if gender2 == "girl" else BOY_NAMES) if n != name1])
    return StoryParams(place=place, ruminant=r, trouble=t, method=method,
                       name1=name1, gender1=gender1, name2=name2, gender2=gender2)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], next(r for r in RUMINANTS if r.key == params.ruminant),
                 TROUBLES[params.trouble], METHODS[params.method],
                 params.name1, params.gender1, params.name2, params.gender2)
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
    StoryParams(place="barn", ruminant="goat", trouble="pitch", method="rope",
                name1="Mina", gender1="girl", name2="Toby", gender2="boy"),
    StoryParams(place="yard", ruminant="sheep", trouble="pitch", method="lift",
                name1="Lena", gender1="girl", name2="Arlo", gender2="boy"),
    StoryParams(place="lane", ruminant="calf", trouble="pitch", method="push",
                name1="Nora", gender1="girl", name2="Finn", gender2="boy"),
    StoryParams(place="barn", ruminant="sheep", trouble="pitch", method="rope",
                name1="Pia", gender1="girl", name2="Owen", gender2="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base + i
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
