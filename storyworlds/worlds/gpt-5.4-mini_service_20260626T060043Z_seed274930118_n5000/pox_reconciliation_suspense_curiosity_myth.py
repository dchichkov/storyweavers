#!/usr/bin/env python3
"""
A mythic story world about a child, a pox-mark, a curious mistake, and a
reconciliation with the village.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    group: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    sacred: bool = False
    allows: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    effect: str
    uses: set[str] = field(default_factory=set)
    is_ritual: bool = False


@dataclass
class StoryParams:
    place: str
    omen: str
    charm: str
    name: str
    gender: str
    kin: str
    trait: str
    seed: Optional[int] = None


THRESHOLD = 1.0


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.events: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.events = set(self.events)
        w.lines = [[]]
        w.facts = dict(self.facts)
        return w


PLACES = {
    "village": Place("the village", sacred=False, allows={"pox", "cure", "reconcile"}),
    "well": Place("the old well", sacred=True, allows={"curiosity", "pox", "cure"}),
    "grove": Place("the moonlit grove", sacred=True, allows={"curiosity", "reconcile"}),
    "gate": Place("the city gate", sacred=False, allows={"pox", "suspense", "reconcile"}),
}

CHARMS = {
    "ash": Charm("ash", "a bowl of ash", "soothe the skin", uses={"pox"}),
    "water": Charm("water", "votive water", "cool the fever", uses={"pox", "cure"}),
    "song": Charm("song", "an old song", "soften hard hearts", uses={"reconcile"}, is_ritual=True),
    "lantern": Charm("lantern", "a lantern", "show the hidden path", uses={"suspense", "curiosity"}),
}

OMENS = {
    "pox": {
        "mark": "pox spots",
        "look": "small pale spots",
        "feels": "itchy and strange",
        "risk": "the villagers would stare and keep away",
    },
    "blush": {
        "mark": "blush marks",
        "look": "pink freckles",
        "feels": "warm and shy",
        "risk": "the child would feel embarrassed in public",
    },
}

GIRL_NAMES = ["Lina", "Mira", "Sera", "Asha", "Nora", "Ila"]
BOY_NAMES = ["Taro", "Kellan", "Milo", "Dara", "Eli", "Ronan"]
TRAITS = ["curious", "gentle", "brave", "restless", "dreaming"]


def intro(world: World, hero: Entity, kin: Entity, omen: str) -> None:
    world.say(
        f"{hero.id} was a {next(t for t in hero.meters.keys() if False) if False else ''}".strip()
    )


def tell_story(world: World, hero: Entity, kin: Entity, charm: Charm, omen_key: str) -> None:
    omen = OMENS[omen_key]
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.meters["mark"] = 1
    world.say(
        f"In the days when the moon listened to every footstep, {hero.id} was known in the village for being {hero.memes.get('trait', 0) and ''}".strip()
    )


def _apply_state(world: World) -> None:
    hero = next(e for e in world.entities.values() if e.kind == "character" and e.type in {"girl", "boy"})
    kin = next(e for e in world.entities.values() if e.id == "Kin")
    mark = world.facts["omen"]
    if hero.meters.get(mark["mark"], 0) >= THRESHOLD and hero.memes.get("curiosity", 0) >= THRESHOLD:
        key = ("suspense", hero.id)
        if key not in world.events:
            world.events.add(key)
            hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
            world.say(
                f"At dusk, {hero.id} saw the {mark['look']} on {hero.pronoun('possessive')} wrist, and wonder made {hero.pronoun('object')} follow the lantern-light toward the sacred place."
            )


def set_scene(world: World, hero: Entity, kin: Entity, charm: Charm, omen_key: str) -> None:
    omen = OMENS[omen_key]
    world.say(
        f"{hero.id} lived in {world.place.name}, where old stories said every mark on the skin had a meaning."
    )
    world.say(
        f"{hero.id} was {hero.pronoun('possessive')} {kin.group} child, and {hero.pronoun()} liked to ask questions no one else thought to ask."
    )
    world.say(
        f"One morning, {hero.id} noticed {hero.pronoun('possessive')} {omen['mark']}—{omen['look']} that felt {omen['feels']}."
    )
    hero.meters[omen['mark']] = 1


def curiosity_turn(world: World, hero: Entity, kin: Entity, charm: Charm, omen_key: str) -> None:
    omen = OMENS[omen_key]
    world.para()
    world.say(
        f"{hero.id} wanted to know whether the old well could answer the question, so {hero.pronoun()} crept away with only {charm.label} and a lantern for company."
    )
    world.say(
        f"The path was quiet, and every shadow seemed to hold its breath."
    )
    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
    if omen_key == "pox":
        world.say(
            f"{hero.id} thought, if the water could not heal the {omen['mark']}, perhaps it could at least tell the truth."
        )


def confrontation(world: World, hero: Entity, kin: Entity, charm: Charm, omen_key: str) -> None:
    omen = OMENS[omen_key]
    world.para()
    world.say(
        f"At the well, {kin.id} found {hero.id} first and gasped at the {omen['look']} on {hero.pronoun('possessive')} skin."
    )
    kin.memes["fear"] = kin.memes.get("fear", 0) + 1
    hero.memes["hurt"] = hero.memes.get("hurt", 0) + 1
    world.say(
        f"\"Come back,\" {kin.pronoun()} begged, \"or the village will only remember your {omen['mark']}.\""
    )
    world.say(
        f"{hero.id} looked down, suddenly very small."
    )


def reconciliation(world: World, hero: Entity, kin: Entity, charm: Charm, omen_key: str) -> None:
    omen = OMENS[omen_key]
    world.para()
    world.say(
        f"Then {kin.id} saw how frightened {hero.id} was, and {kin.pronoun()} laid aside fear like an old cloak."
    )
    world.say(
        f"\"I should not have hidden from you,\" {kin.pronoun()} said. \"Let us carry this together.\""
    )
    world.say(
        f"{kin.id} washed {hero.pronoun('possessive')} hands with {charm.label}, and the two of them walked back to the village as the moon climbed high."
    )
    hero.memes["reconciled"] = hero.memes.get("reconciled", 0) + 1
    kin.memes["reconciled"] = kin.memes.get("reconciled", 0) + 1
    world.say(
        f"By the fire, the elder named the marks as part of a passing pox, not a curse, and the village learned to speak gently before it spoke loudly."
    )
    world.say(
        f"In the morning, {hero.id} still had {hero.pronoun('possessive')} {omen['mark']}, but now {hero.pronoun()} also had {kin.pronoun('possessive')} hand in {hero.pronoun('object')} own."
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    omen = OMENS[params.omen]
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    kin = world.add(Entity(id="Kin", kind="character", type=params.kin, group="older"))
    charm = CHARMS[params.charm]
    world.facts = {
        "hero": hero,
        "kin": kin,
        "charm": charm,
        "omen": omen,
        "place": place,
        "trait": params.trait,
    }
    hero.memes["curiosity"] = 1
    hero.memes["trait"] = 1
    set_scene(world, hero, kin, charm, params.omen)
    curiosity_turn(world, hero, kin, charm, params.omen)
    confrontation(world, hero, kin, charm, params.omen)
    reconciliation(world, hero, kin, charm, params.omen)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short myth for children about {f['hero'].id}, a {f['trait']} child, and a mysterious mark that leads to reconciliation.",
        f"Tell a gentle mythic story in which {f['hero'].id} follows curiosity to {world.place.name} and learns the truth about {f['omen']['mark']}.",
        f"Write a story with suspense, curiosity, and reconciliation where a child returns from {world.place.name} with {f['charm'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, kin, omen, charm = f["hero"], f["kin"], f["omen"], f["charm"]
    return [
        QAItem(
            question=f"What did {hero.id} notice on {hero.pronoun('possessive')} skin?",
            answer=f"{hero.id} noticed {hero.pronoun('possessive')} {omen['mark']}, which looked like {omen['look']} and felt {omen['feels']}.",
        ),
        QAItem(
            question=f"Why did {hero.id} go to {world.place.name}?",
            answer=f"{hero.id} went there because curiosity pulled {hero.pronoun('object')} toward the old well, and {hero.pronoun()} wanted to know what the mark meant.",
        ),
        QAItem(
            question=f"How did {hero.id} and {kin.id} make peace at the end?",
            answer=f"{kin.id} stopped fearing the mark, helped wash {hero.pronoun('possessive')} hands with {charm.label}, and walked back together so the village could understand rather than turn away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more, even when the answer is hidden at first.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset or apart come back together in peace.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story that explains a world idea, a custom, or a mystery in a memorable way.",
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    out.append(f"events={sorted(world.events)}")
    return "\n".join(out)


ASP_RULES = r"""
character(C) :- hero(C).
character(C) :- kin(C).

suspense(C) :- curiosity(C), mark(C).
reconcile(C) :- fear(C), help(C).

show_story(C) :- suspense(C), reconcile(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].sacred:
            lines.append(asp.fact("sacred", pid))
        for a in sorted(PLACES[pid].allows):
            lines.append(asp.fact("allows", pid, a))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
        for u in sorted(CHARMS[cid].uses):
            lines.append(asp.fact("uses", cid, u))
    for oid in OMENS:
        lines.append(asp.fact("omen", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show place/1."))
    if model is None:
        print("ASP solve failed")
        return 1
    print("OK: ASP program loads and solves.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic pox reconciliation story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--omen", choices=OMENS, default="pox")
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--kin", choices=["mother", "father", "sister", "brother"], default="sister")
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
    place = args.place or rng.choice(list(PLACES))
    omen = args.omen or "pox"
    charm = args.charm or rng.choice(list(CHARMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    kin = args.kin or rng.choice(["mother", "father", "sister", "brother"])
    trait = args.trait or rng.choice(TRAITS)
    if charm not in CHARMS[args.charm] if args.charm else False:
        pass
    if omen not in OMENS:
        raise StoryError("Unknown omen.")
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if charm not in CHARMS:
        raise StoryError("Unknown charm.")
    return StoryParams(place=place, omen=omen, charm=charm, name=name, gender=gender, kin=kin, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="well", omen="pox", charm="water", name="Lina", gender="girl", kin="sister", trait="curious"),
    StoryParams(place="gate", omen="pox", charm="ash", name="Taro", gender="boy", kin="father", trait="brave"),
    StoryParams(place="grove", omen="blush", charm="song", name="Mira", gender="girl", kin="mother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show show_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show show_story/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
