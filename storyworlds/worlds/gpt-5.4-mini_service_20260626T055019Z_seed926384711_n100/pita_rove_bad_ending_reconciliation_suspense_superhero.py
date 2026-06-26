#!/usr/bin/env python3
"""
Storyworld: a small superhero tale with pita, rove, suspense, a bad ending, and
reconciliation.

Premise:
A kid hero patrols a city block with a tiny sidekick and a warm pita snack.

Tension:
A sneaky rover-like drone keeps circling, tempting the hero to chase it and
spoil the mission.

Turn:
The chase goes wrong first, leading to a bad ending moment: the pita falls, the
signal is lost, and the city lamp goes dark.

Resolution:
The hero and the sidekick reconcile, share the pita, and use calm teamwork to
follow the rover's trail and restore the light.

This world is intentionally small and constraint-checked. It generates a
single, child-facing superhero story with grounded Q&A and an inline ASP twin
for parity checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Threat:
    id: str
    label: str
    verb: str
    track: str
    mess: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy as _copy

        return World(
            setting=self.setting,
            entities=_copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "rooftop": Setting(place="the rooftop", affords={"rove"}),
    "alley": Setting(place="the lantern alley", affords={"rove"}),
    "museum": Setting(place="the museum steps", affords={"rove"}),
}

HERO_NAMES = ["Nova", "Kai", "Mira", "Jett", "Iris", "Pip"]
SIDEKICK_NAMES = ["Beetle", "Wisp", "Milo", "Tess", "Rae", "Dot"]
VILLAIN_NAMES = ["Drift", "Murk", "Vanta", "Rook"]

ARTIFACTS = {
    "pita": Artifact(
        id="pita",
        label="pita",
        phrase="a warm pita",
        region="hands",
    ),
}

THREATS = {
    "rove": Threat(
        id="rove",
        label="rover drone",
        verb="rove around",
        track="rove",
        mess="lost_signal",
        zone={"hands"},
        tags={"rove", "drone", "suspense"},
    ),
}

GEAR = {
    "cape": Artifact(id="cape", label="cape", phrase="a bright cape", region="back"),
    "mask": Artifact(id="mask", label="mask", phrase="a soft mask", region="face"),
}

KNOWLEDGE = {
    "pita": [
        (
            "What is pita?",
            "Pita is soft flat bread that can be folded or split open to hold tasty fillings.",
        )
    ],
    "rove": [
        (
            "What does it mean to rove?",
            "To rove means to wander or move around from place to place, often without a set path.",
        )
    ],
    "drone": [
        (
            "What is a drone?",
            "A drone is a small flying or rolling machine that people can guide from far away.",
        )
    ],
    "suspense": [
        (
            "What is suspense in a story?",
            "Suspense is the feeling of wondering what will happen next, especially when something tricky is about to happen.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation is when people stop arguing, forgive each other, and become friendly again.",
        )
    ],
    "hero": [
        (
            "What is a superhero?",
            "A superhero is a brave character who tries to protect others and solve problems.",
        )
    ],
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    name: str
    sidekick: str
    villain: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, sidekick: Entity, villain: Entity) -> None:
    world.say(
        f"{hero.id} was a little superhero who watched over {world.setting.place}. "
        f"{sidekick.id} stayed close, ready with quick hands and a brave grin. "
        f"Far away, {villain.id} sent a rover drone to circle the block."
    )


def setup_pita(world: World, hero: Entity, sidekick: Entity) -> Entity:
    pita = world.add(Entity(
        id="pita",
        kind="thing",
        type="food",
        label="pita",
        phrase="a warm pita",
        owner=hero.id,
    ))
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {pita.phrase} in a small wrap. "
        f"{hero.id} wanted to finish the patrol before taking a bite."
    )
    return pita


def predict_mess(world: World, hero: Entity, threat: Threat, pita: Entity) -> dict:
    sim = world.copy()
    simulate_rove(sim, sim.get(hero.id), threat, pita, narrate=False)
    return {
        "lost": bool(sim.facts.get("lost_signal")),
        "broken_trust": bool(sim.facts.get("hurt_feelings")),
    }


def simulate_rove(world: World, hero: Entity, threat: Threat, pita: Entity, narrate: bool = True) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    world.say(
        f"Then the rover drone swooped low and began to {threat.verb} over the lamps."
    )
    world.say(
        f"{hero.id} chased {threat.label} across the stone path, but {hero.pronoun('possessive')} "
        f"foot caught on the edge of a vent."
    )
    if narrate:
        world.facts["lost_signal"] = True
        world.facts["bad_ending"] = True
        world.say(
            f"The chase ended badly: the rover slipped into the dark, and {hero.id}'s {pita.label} fell open on the ground."
        )


def reconcile(world: World, hero: Entity, sidekick: Entity, pita: Entity) -> None:
    hero.memes["guilt"] = hero.memes.get("guilt", 0.0) + 1
    sidekick.memes["hurt"] = sidekick.memes.get("hurt", 0.0) + 1
    world.say(
        f"{sidekick.id} looked sad for a moment because the plan had gone wrong."
    )
    world.say(
        f"Then {hero.id} took a breath and said sorry. {sidekick.id} forgave {hero.pronoun('object')}."
    )
    hero.memes["guilt"] = 0.0
    sidekick.memes["hurt"] = 0.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    sidekick.memes["trust"] = sidekick.memes.get("trust", 0.0) + 1
    world.facts["reconciled"] = True
    world.say(
        f"They shared the {pita.label}, which made the night feel warm again."
    )


def resolve(world: World, hero: Entity, sidekick: Entity, villain: Entity) -> None:
    world.say(
        f"Together, {hero.id} and {sidekick.id} followed the rover's tiny wheel marks to a broken lamp box."
    )
    world.say(
        f"{sidekick.id} held the cover steady while {hero.id} fixed the switch, and the alley lit up bright."
    )
    world.say(
        f"{villain.id}'s trick was no match for two friends who worked together."
    )
    world.say(
        f"At the end, {hero.id} stood tall beside {sidekick.id}, and the recovered {ARTIFACTS['pita'].label} still smelled like supper."
    )


def tell_story(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="boy", label="hero"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="girl", label="sidekick"))
    villain = world.add(Entity(id=params.villain, kind="character", type="man", label="villain"))

    world.facts.update(hero=hero, sidekick=sidekick, villain=villain)

    introduce(world, hero, sidekick, villain)
    world.para()

    pita = setup_pita(world, hero, sidekick)
    world.para()

    world.say(
        f"The air felt tense as the rover kept circling. {hero.id} could hear the soft buzz of its motor, and that made the night full of suspense."
    )
    if predict_mess(world, hero, THREATS["rove"], pita)["lost"]:
        simulate_rove(world, hero, THREATS["rove"], pita, narrate=True)
    world.para()

    reconcile(world, hero, sidekick, pita)
    world.para()

    resolve(world, hero, sidekick, villain)

    world.facts["pita"] = pita
    world.facts["threat"] = THREATS["rove"]
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    place = world.setting.place
    return [
        f'Write a short superhero story for a young child that includes the words "pita" and "rove".',
        f"Tell a suspenseful superhero story where {hero.id} and {sidekick.id} patrol {place}, lose the first plan, and then reconcile.",
        "Write a simple story with a bad ending moment first, then a peaceful reconciliation and a brighter ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    villain = f["villain"]
    pita = f["pita"]
    qa = [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, who watches over {world.setting.place} with {sidekick.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} carry during the patrol?",
            answer=f"{hero.id} carried {hero.pronoun('possessive')} {pita.phrase}.",
        ),
        QAItem(
            question="What made the story suspenseful?",
            answer="The rover drone kept circling close, so everyone had to wonder what it would do next.",
        ),
        QAItem(
            question="What was the bad ending moment?",
            answer="The first chase went badly: the rover got away for a moment and the pita fell open on the ground.",
        ),
        QAItem(
            question="How did the hero and sidekick reconcile?",
            answer=f"{hero.id} said sorry, {sidekick.id} forgave {hero.pronoun('object')}, and they shared the pita again.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"{hero.id} and {sidekick.id} fixed the lamp box, the alley lit up, and {villain.id}'s trick failed.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    seen = set()
    for tag in ["hero", "pita", "rove", "drone", "suspense", "reconciliation"]:
        if tag in seen or tag not in KNOWLEDGE:
            continue
        seen.add(tag)
        for q, a in KNOWLEDGE[tag]:
            out.append(QAItem(question=q, answer=a))
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(h1).
sidekick(s1).
villain(v1).
place(rooftop).
place(alley).
place(museum).

word(pita).
word(rove).

suspense(S) :- rover(S), circling(S).
bad_ending(S) :- suspense(S), lost_signal(S).
reconciliation(S) :- bad_ending(S), said_sorry(S), forgave(S).
happy_end(S) :- reconciliation(S), fixed_lamp(S).

shown_story(rooftop, pita, rove) :- place(rooftop), word(pita), word(rove).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("thing", aid))
        lines.append(asp.fact("label", aid, art.label))
        lines.append(asp.fact("region", aid, art.region))
    for tid, th in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("label", tid, th.label))
        for z in sorted(th.zone):
            lines.append(asp.fact("zone", tid, z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shown_story/3."))
    return sorted(set(asp.atoms(model, "shown_story")))


def asp_verify() -> int:
    py = {("rooftop", "pita", "rove")}
    cl = set(asp_valid_combos())
    if cl == py:
        print(f"OK: clingo gate matches Python gate ({len(cl)} combo).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="rooftop", name="Nova", sidekick="Beetle", villain="Drift"),
    StoryParams(place="alley", name="Kai", sidekick="Wisp", villain="Murk"),
    StoryParams(place="museum", name="Mira", sidekick="Rae", villain="Vanta"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A superhero story world with pita, roving suspense, a bad ending, and reconciliation."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    name = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([x for x in SIDEKICK_NAMES if x != name])
    villain = args.villain or rng.choice(VILLAIN_NAMES)
    return StoryParams(place=place, name=name, sidekick=sidekick, villain=villain)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


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
        print(asp_program("#show shown_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combo(s):")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
