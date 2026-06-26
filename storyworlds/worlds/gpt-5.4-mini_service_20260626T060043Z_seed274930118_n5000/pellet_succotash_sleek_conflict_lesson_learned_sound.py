#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a sleek little critter, a bumpy pellet,
and a bowl of succotash.

Seed image:
- A neat, sleek child or animal wants a shiny snack.
- A crunchy pellet causes a small conflict.
- A wiser helper offers succotash instead.
- The story ends with a learned lesson and bright sound effects.

The story is kept small and state-driven:
physical meters track crumbs, spill, and neatness;
emotional memes track desire, conflict, calm, and delight.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sunny kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    mess: str
    soil: str
    sound: str
    edible: bool = True


@dataclass
class Lesson:
    id: str
    label: str
    phrase: str
    calm_sound: str
    fix_word: str


class World:
    def __init__(self, setting: Setting) -> None:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for eater in world.characters():
        if eater.meters.get("nibble", 0) < THRESHOLD:
            continue
        snack_id = world.facts.get("snack_id")
        if not snack_id:
            continue
        snack = world.entities[snack_id]
        if snack.meters.get("spill", 0) >= THRESHOLD:
            continue
        sig = ("spill", eater.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        snack.meters["spill"] = 1.0
        snack.meters["mess"] = 1.0
        eater.memes["conflict"] = eater.memes.get("conflict", 0) + 1
        out.append(f"Crunch-a-bunch, the pellet tumbled and made a little mess.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for eater in world.characters():
        if eater.memes.get("conflict", 0) < THRESHOLD:
            continue
        sig = ("calm", eater.id)
        if sig in world.fired:
            continue
        lesson_id = world.facts.get("lesson_id")
        if not lesson_id:
            continue
        world.fired.add(sig)
        eater.memes["lesson"] = 1.0
        eater.memes["calm"] = 1.0
        out.append("Shhh, said the helper, and the little room grew soft and still.")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("calm", _r_calm)]


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


def sound_effect(token: str) -> str:
    return {
        "pellet": "plink-plink!",
        "succotash": "sip-sip, mmm!",
        "lesson": "softly, softly, hush-hush.",
    }.get(token, "tick-tock!")


def tell(world: World, hero: Entity, helper: Entity, pellet: Entity, succotash: Entity, lesson: Entity) -> World:
    world.say(f"Little {hero.id} was a sleek young {hero.type} with a bright, neat tail.")
    world.say(f"{hero.pronoun().capitalize()} loved shiny bites and listened for the prettiest sounds.")
    world.say(f"On the table sat a pellet and a warm bowl of succotash, both waiting in {world.setting.place}.")
    world.say(f"{sound_effect('pellet')} went the pellet, and {sound_effect('succotash')} went the bowl.")

    world.para()
    hero.meters["nibble"] = 1.0
    hero.memes["desire"] = 1.0
    world.say(f"{hero.id} reached for the pellet first, because it looked tiny and fancy.")
    world.say(f"But the pellet clinked and skittered, and that brought a frown and a tiny conflict.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then the helper smiled and slid over the succotash.")
    world.say(f'"Try this kindly bowl," {helper.id} said. "It is a better bite for a sleek little tummy."')
    world.say(f"{sound_effect('succotash')} went the spoon as {hero.id} took a careful taste.")
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["conflict"] = 0.0
    hero.meters["nibble"] = 0.0
    succotash.meters["shared"] = 1.0
    lesson.meters["learned"] = 1.0
    world.say(f"The bowl was warm and gold, and the little room felt merry once more.")

    world.para()
    world.say(f"At the end, {hero.id} remembered the lesson: when one bite makes a fuss, choose the kind food.")
    world.say(f"{sound_effect('lesson')} {hero.id} smiled, and the succotash stayed neat and bright.")
    world.facts.update(
        hero=hero, helper=helper, pellet=pellet, succotash=succotash, lesson=lesson
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the sunny kitchen", affords={"nibble"}),
    "table": Setting(place="the wooden table", affords={"nibble"}),
    "porch": Setting(place="the little porch", affords={"nibble"}),
}

PEOPLE = {
    "squirrel": ("squirrel", "girl"),
    "mouse": ("mouse", "boy"),
    "bunny": ("bunny", "girl"),
}

SNACKS = {
    "pellet": Snack(
        id="pellet", label="pellet", phrase="a shiny pellet", mess="crumbly",
        soil="crumbly and scattered", sound="plink-plink!"
    ),
    "succotash": Snack(
        id="succotash", label="succotash", phrase="a warm bowl of succotash", mess="splashed",
        soil="soft and tidy", sound="sip-sip, mmm!"
    ),
}

LESSONS = {
    "lesson": Lesson(
        id="lesson", label="lesson", phrase="a little lesson learned", calm_sound="hush-hush.",
        fix_word="kind"
    )
}

GENDERS = ["girl", "boy"]
NAMES = {
    "girl": ["Mia", "Lily", "Nina", "Zoe", "Tia"],
    "boy": ["Ben", "Theo", "Max", "Leo", "Pip"],
}
TRAITS = ["sleek", "cheerful", "brave", "curious", "tiny"]


@dataclass
class StoryParams:
    place: str
    child_kind: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="kitchen", child_kind="squirrel", name="Mia", gender="girl", trait="sleek"),
    StoryParams(place="table", child_kind="mouse", name="Theo", gender="boy", trait="curious"),
    StoryParams(place="porch", child_kind="bunny", name="Zoe", gender="girl", trait="sleek"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme-style story about a sleek little {f["child_kind"]} named {f["hero"].id}, a pellet, and succotash.',
        f"Tell a gentle story where {f['hero'].id} starts a tiny conflict over a pellet, then learns a lesson from succotash.",
        f'Write a child-friendly story with sound effects like "{SNACKS["pellet"].sound}" and "{SNACKS["succotash"].sound}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    pellet: Entity = f["pellet"]
    succotash: Entity = f["succotash"]
    qa = [
        QAItem(
            question=f"Who was the sleek little one in the story?",
            answer=f"The sleek little one was {hero.id}, who wanted a shiny snack in {world.setting.place}.",
        ),
        QAItem(
            question=f"What caused the little conflict?",
            answer=f"The conflict began when {hero.id} reached for the pellet and it made a crumbly little mess.",
        ),
        QAItem(
            question=f"What food helped solve the problem?",
            answer=f"The helper offered {succotash.phrase}, and that calmer choice helped {hero.id} settle down.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that when one bite makes a fuss, it is better to choose the kind food.",
        ),
    ]
    if pellet.meters.get("spill", 0) >= THRESHOLD:
        qa.append(QAItem(
            question="What happened to the pellet?",
            answer="The pellet tumbled and spilled, so the tiny mess made the room feel less neat.",
        ))
    if hero.memes.get("calm", 0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} helped by offering succotash and speaking softly until the conflict faded.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is succotash?",
            answer="Succotash is a warm food bowl, often soft and cozy, with sweet, kind bites that are easy to share.",
        ),
        QAItem(
            question="What does sleek mean?",
            answer="Sleek means smooth and neat, like something that shines and looks tidy.",
        ),
        QAItem(
            question="What kind of sound can a tiny pellet make?",
            answer="A tiny pellet can make a little plink or clink sound when it drops or rolls.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
spilled(H) :- nibble(H), pellet(P), mess(P, crumbly).
conflict(H) :- spilled(H).
lesson_learned(H) :- conflict(H), succotash(S), kind(S).
resolved(H) :- lesson_learned(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for sid, sn in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("mess", sid, sn.mess))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show spilled/1.\n#show conflict/1.\n#show lesson_learned/1.\n#show resolved/1."))
    shown = set(asp.atoms(model, "spilled")) | set(asp.atoms(model, "conflict")) | set(asp.atoms(model, "lesson_learned")) | set(asp.atoms(model, "resolved"))
    if shown:
        print("OK: ASP reasoning emitted atoms:", sorted(shown))
        return 0
    print("MISMATCH: ASP reasoning produced no visible atoms")
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, "pellet") for p in SETTINGS for c in PEOPLE]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: pellet, succotash, sleek, conflict, lesson learned, sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child-kind", choices=PEOPLE)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    gender = args.gender or rng.choice(GENDERS)
    child_kind = args.child_kind or rng.choice(list(PEOPLE))
    if args.name is None:
        name = rng.choice(NAMES[gender])
    else:
        name = args.name
    trait = args.trait or "sleek"
    place = args.place or rng.choice(list(SETTINGS))
    return StoryParams(place=place, child_kind=child_kind, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    helper = world.add(Entity(id="Helper", kind="character", type="mother" if params.gender == "girl" else "father"))
    pellet = world.add(Entity(id="pellet", type="pellet", label="pellet", phrase="a shiny pellet", meters={"spill": 0.0}, memes={}))
    succotash = world.add(Entity(id="succotash", type="succotash", label="succotash", phrase="a warm bowl of succotash", meters={"shared": 0.0}, memes={}))
    lesson = world.add(Entity(id="lesson", type="lesson", label="lesson", phrase="a lesson learned", meters={"learned": 0.0}, memes={}))

    world.facts.update(child_kind=params.child_kind, hero=hero, helper=helper, pellet=pellet, succotash=succotash, lesson=lesson, snack_id="pellet", lesson_id="lesson")

    tell(world, hero, helper, pellet, succotash, lesson)
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
        print(asp_program("#show spilled/1.\n#show conflict/1.\n#show lesson_learned/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show spilled/1.\n#show conflict/1.\n#show lesson_learned/1.\n#show resolved/1."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.child_kind} / {p.trait}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
