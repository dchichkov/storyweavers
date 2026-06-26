#!/usr/bin/env python3
"""
A standalone story world for a tall-tale prank with inner monologue and teamwork.

The premise is simple:
a boastful child plans a prank, worries privately about getting caught, and then
teams up with a friend to turn the prank into a harmless surprise that ends in
laughter instead of trouble.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["sneaky", "fear", "joy", "pride", "shame", "confusion", "trust", "teamwork"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    afford: set[str] = field(default_factory=set)


@dataclass
class Prank:
    id: str
    noun: str
    verb: str
    inner: str
    teamwork: str
    reveal: str
    harmless: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    needed_for: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "barn": Setting(place="the old red barn", afford={"prank"}),
    "schoolyard": Setting(place="the schoolyard", afford={"prank"}),
    "orchard": Setting(place="the apple orchard", afford={"prank"}),
    "porch": Setting(place="the wide porch", afford={"prank"}),
}

PRANKS = {
    "bucket": Prank(
        id="bucket",
        noun="bucket trick",
        verb="tip a bucket of feathers over the doorway",
        inner="What if the feathers land on the wrong head?",
        teamwork="one kid could hold the ladder while the other balanced the bucket",
        reveal="the feathers burst like a snowy cloud",
        tags={"feathers", "doorway", "harmless"},
    ),
    "ribbon": Prank(
        id="ribbon",
        noun="ribbon prank",
        verb="tie bright ribbons around the gate",
        inner="What if the gate creaks and wakes the dog?",
        teamwork="one friend could watch for footsteps while the other tied the knots",
        reveal="the ribbons fluttered like rainbow tails",
        tags={"ribbons", "gate", "harmless"},
    ),
    "bell": Prank(
        id="bell",
        noun="bell trick",
        verb="hide a tin bell in the hay",
        inner="What if the bell rings too soon?",
        teamwork="one friend could cover the sound while the other tucked it in",
        reveal="the bell jingled once and then settled like a sleepy cricket",
        tags={"bell", "hay", "harmless"},
    ),
}

PROPS = {
    "feathers": Prop(id="feathers", label="feather pile", phrase="a pillowcase full of feathers", region="torso"),
    "ribbons": Prop(id="ribbons", label="ribbons", phrase="a long spool of bright ribbons", region="hands", plural=True),
    "bell": Prop(id="bell", label="tin bell", phrase="a little tin bell", region="hands"),
}

NAMES = {
    "girl": ["Mabel", "Sadie", "Nell", "Ruby", "June", "Poppy"],
    "boy": ["Otis", "Hank", "Bram", "Eli", "Wes", "Clay"],
}
SIDEKICK_NAMES = ["Luna", "Toby", "Mina", "Jasper", "Ivy", "Bo"]
TRAITS = ["bold", "quick-witted", "bouncy", "spirited", "mischievous", "bright-eyed"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    prank: str
    name: str
    gender: str
    sidekick: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------

def title_case_place(place: str) -> str:
    return place


def open_scene(world: World, hero: Entity, pal: Entity, prank: Prank) -> None:
    world.say(
        f"{hero.id} was a {hero.pronoun('possessive')} own kind of tall-tale kid, "
        f"the sort who could hear a whisper from three fields away."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved the idea of a prank, especially "
        f"{prank.noun}, because it sounded as grand as a thunderclap in a bucket."
    )
    hero.memes["pride"] += 1
    hero.memes["sneaky"] += 1
    pal.memes["trust"] += 1


def inner_monologue(world: World, hero: Entity, prank: Prank) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"Still, {hero.id} kept a private thought tucked behind {hero.pronoun('possessive')} teeth: "
        f'"{prank.inner}"'
    )


def build_teamwork(world: World, hero: Entity, pal: Entity, prank: Prank) -> None:
    hero.memes["teamwork"] += 1
    pal.memes["teamwork"] += 1
    world.say(
        f"Then {hero.id} leaned close to {pal.id} and shared the whole notion, because "
        f"{prank.teamwork}."
    )
    world.say(
        f"{pal.id} grinned and nodded, and the two of them worked together like a pair "
        f"of sparrows hauling one shiny straw."
    )


def cause_reveal(world: World, hero: Entity, pal: Entity, prank: Prank) -> None:
    hero.memes["joy"] += 1
    pal.memes["joy"] += 1
    world.say(
        f"They went to {world.setting.place}, quiet as moonlight on a fence rail."
    )
    world.say(
        f"At the last second, {hero.id} and {pal.id} changed the prank so nobody would be scared."
    )
    world.say(
        f"When the moment came, {prank.reveal}, and even the grumpiest grown-up had to laugh."
    )


def ending_image(world: World, hero: Entity, pal: Entity, prank: Prank) -> None:
    world.say(
        f"By the end, {hero.id} was laughing so hard {hero.pronoun('possessive')} shoulders shook, "
        f"and {pal.id} was laughing right beside {hero.pronoun('object')}."
    )
    world.say(
        f"The prank was still a prank, but it had turned into a friendly surprise, "
        f"and the whole place felt brighter than a lantern in a jar."
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def tell(setting: Setting, prank: Prank, hero_name: str, hero_type: str, sidekick_name: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    pal = world.add(Entity(id=sidekick_name, kind="character", type="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))

    hero.memes["pride"] += 1
    pal.memes["trust"] += 1
    parent.memes["watchful"] = 1.0

    open_scene(world, hero, pal, prank)
    world.para()
    inner_monologue(world, hero, prank)
    world.say(f"{hero.id} kept {hero.pronoun('possessive')} grin small, just in case.")
    world.para()
    build_teamwork(world, hero, pal, prank)
    world.say(f"They gathered what they needed and slipped away to {world.setting.place}.")
    world.para()
    cause_reveal(world, hero, pal, prank)
    ending_image(world, hero, pal, prank)

    world.facts.update(
        hero=hero,
        pal=pal,
        parent=parent,
        prank=prank,
        setting=setting,
        trait=trait,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story_combo(place: str, prank_id: str) -> bool:
    return place in SETTINGS and prank_id in PRANKS and "prank" in SETTINGS[place].afford


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.prank and not valid_story_combo(args.place, args.prank):
        raise StoryError("(No story: that prank doesn't fit this place for a harmless tall-tale surprise.)")

    places = [args.place] if args.place else list(SETTINGS)
    prank_ids = [args.prank] if args.prank else list(PRANKS)

    combos = [(p, k) for p in places for k in prank_ids if valid_story_combo(p, k)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, prank_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != name])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        place=place,
        prank=prank_id,
        name=name,
        gender=gender,
        sidekick=sidekick,
        parent=parent,
        trait=trait,
    )


# ---------------------------------------------------------------------------
# Question answering
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prank = f["hero"], f["prank"]
    return [
        f'Write a short tall-tale story for a child about a prank, inner thoughts, and teamwork that includes "{prank.id}".',
        f"Tell a funny story where {hero.id} wants to pull a {prank.noun} but worries inside before teaming up with a friend.",
        f'Write a gentle prank story set at {world.setting.place} with a secret thought and a shared plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, pal, prank = f["hero"], f["pal"], f["prank"]
    place = world.setting.place
    trait = f["trait"]

    return [
        QAItem(
            question=f"What kind of story is this about {hero.id} and {pal.id} at {place}?",
            answer=(
                f"It is a tall-tale-style prank story. {hero.id} first thinks about the prank alone, "
                f"then {hero.id} and {pal.id} work together to turn it into a harmless surprise."
            ),
        ),
        QAItem(
            question=f"What private thought did {hero.id} have before trying the prank?",
            answer=f"{hero.id} wondered: \"{prank.inner}\" That was the little worried voice in {hero.pronoun('possessive')} head.",
        ),
        QAItem(
            question=f"How did {hero.id} and {pal.id} use teamwork?",
            answer=(
                f"They shared the job, watched out for trouble, and moved together like a tiny two-person crew. "
                f"Because of that teamwork, the prank could happen without hurting anyone."
            ),
        ),
        QAItem(
            question=f"How did {trait} {hero.id} feel at the end?",
            answer=(
                f"{hero.id} felt happy and relieved. The prank turned into laughter, so the last picture is "
                f"{hero.id} laughing beside {pal.id} instead of feeling scared."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "prank": [
        QAItem(
            question="What is a prank?",
            answer="A prank is a playful trick meant to make people surprised or amused, not hurt or upset.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means two or more people help each other to get a job done together.",
        )
    ],
    "inner": [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice in a character's head that tells their thoughts and worries.",
        )
    ],
    "tall tale": [
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a very exaggerated, lively story that makes ordinary things sound bigger and more dramatic.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["prank"],
        *WORLD_KNOWLEDGE["teamwork"],
        *WORLD_KNOWLEDGE["inner"],
        *WORLD_KNOWLEDGE["tall tale"],
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prank_place(P) :- place(P).
teamwork_story(P, K) :- prank_place(P), prank(K), safe_prank(K).
valid_story(P, K) :- teamwork_story(P, K).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(setting.afford):
            lines.append(asp.fact("affords", pid, a))
    for kid, prank in PRANKS.items():
        lines.append(asp.fact("prank", kid))
        if prank.harmless:
            lines.append(asp.fact("safe_prank", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = {(p, k) for p in SETTINGS for k in PRANKS if valid_story_combo(p, k)}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


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
# Shared interface
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    prank: str
    name: str
    gender: str
    sidekick: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a prank, inner monologue, and teamwork in a tall tale style."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prank", choices=PRANKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        PRANKS[params.prank],
        params.name,
        params.gender,
        params.sidekick,
        params.parent,
        params.trait,
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


CURATED = [
    StoryParams(place="barn", prank="bucket", name="Mabel", gender="girl", sidekick="Toby", parent="mother", trait="bold"),
    StoryParams(place="schoolyard", prank="ribbon", name="Otis", gender="boy", sidekick="Luna", parent="father", trait="quick-witted"),
    StoryParams(place="orchard", prank="bell", name="Ruby", gender="girl", sidekick="Bo", parent="mother", trait="bouncy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, prank) combos:\n")
        for place, prank in stories:
            print(f"  {place:12} {prank}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.prank} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
