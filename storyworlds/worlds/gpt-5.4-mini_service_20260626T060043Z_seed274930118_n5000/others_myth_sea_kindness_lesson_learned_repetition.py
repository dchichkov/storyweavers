#!/usr/bin/env python3
"""
A small comedy storyworld about a sea-side myth, a lesson learned, and
repeated attempts to help the others kindly.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
TIDE_THRESHOLD = 2.0
KINDNESS_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearing: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("tide", "salt", "mud", "clean"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "kindness", "pride", "lesson", "confusion", "laughter"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    sea: bool = False
    myth: bool = False
    affords: set[str] = field(default_factory=set)
    repetition: int = 2


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    attempt: str
    helps: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    region: str
    protects: set[str]
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_tide(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["tide"] < TIDE_THRESHOLD:
            continue
        sig = ("tide", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append(f"The sea kept tickling at {ent.pronoun('possessive')} ankles, which was a little ridiculous.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["kindness"] < KINDNESS_THRESHOLD:
            continue
        sig = ("kind", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["joy"] += 1
        ent.memes["laughter"] += 1
        out.append(f"{ent.id} tried again, this time with a kinder grin and less dramatic sighing.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["lesson"] < THRESHOLD:
            continue
        sig = ("lesson", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{ent.id} finally understood the lesson and stopped arguing with the waves.")
    return out


CAUSAL_RULES = [_r_tide, _r_kindness, _r_lesson]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, action: Action) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters[action.mess] += 1
    sim.get(actor.id).memes["kindness"] += 1
    propagate(sim, narrate=False)
    return {
        "tide": sim.get(actor.id).meters["tide"],
        "joy": sim.get(actor.id).memes["joy"],
        "lesson": sim.get(actor.id).memes["lesson"],
    }


def select_gift(action: Action) -> Optional[Gift]:
    for g in GIFTS:
        if action.mess in g.protects:
            return g
    return None


def setting_line(world: World) -> str:
    if world.place.myth and world.place.sea:
        return f"At the edge of the sea, a silly little myth was always being told and retold."
    if world.place.sea:
        return f"The sea looked shiny and suspicious, like it knew a joke nobody else had heard."
    return f"The place was quiet, but everyone kept talking about a nearby myth as if it were breakfast."


def act_story(world: World, hero: Entity, others: list[Entity], action: Action, gift: Gift) -> None:
    world.say(f"{hero.id} was a {hero.type} who liked helping the others and hearing the old myth.")
    world.say(f"{hero.pronoun().capitalize()} loved {action.gerund}, because it always seemed like a good idea at the time.")
    world.say(f"One day, {', '.join(o.id for o in others)} came along, and {hero.id} promised to help them all.")
    world.para()
    world.say(setting_line(world))
    world.say(f"Then {hero.id} wanted to {action.verb} for the others, even though the sea kept making everything slippery.")
    pred = predict(world, hero, action)
    if pred["tide"] >= TIDE_THRESHOLD:
        hero.memes["worry"] += 1
        world.say(f"That would likely leave {hero.pronoun('object')} soggy, and soggy was not the hero's favorite flavor.")
    hero.meters[action.mess] += 1
    hero.memes["kindness"] += 1
    propagate(world, narrate=True)
    world.say(f"{hero.id} tried once, then tried again, and then one more time, because helping the others had become a whole performance.")
    world.para()
    if gift:
        world.say(f"At last, {hero.id}'s friend handed over {gift.phrase}.")
        world.say(f"That helped {hero.id} {action.helps}, so the others could laugh instead of flounder.")
    hero.memes["lesson"] += 1
    hero.memes["joy"] += 1
    hero.memes["confusion"] = 0
    propagate(world, narrate=True)
    world.say(f"In the end, the sea was still there, the myth was still silly, and {hero.id} had learned a kinder way to help.")
    world.say(f"The others cheered, which was impressive considering one of them was still holding a bucket upside down.")


def tell(place: Place, action: Action, hero_name: str = "Milo") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name, traits=["helpful", "funny"]))
    other1 = world.add(Entity(id="Nia", kind="character", type="girl", label="Nia"))
    other2 = world.add(Entity(id="Oren", kind="character", type="boy", label="Oren"))
    world.add(Entity(id="bucket", kind="thing", type="bucket", label="bucket", phrase="a bright red bucket"))
    gift = select_gift(action)
    if gift:
        world.add(Entity(id=gift.id, kind="thing", type=gift.label, label=gift.label, phrase=gift.phrase))
    world.facts.update(hero=hero, others=[other1, other2], action=action, gift=gift, place=place)
    act_story(world, hero, [other1, other2], action, gift)
    return world


PLACES = {
    "seashore": Place(name="the seashore", sea=True, myth=True, affords={"carry", "gather"}, repetition=3),
    "harbor": Place(name="the harbor", sea=True, myth=True, affords={"carry", "gather"}, repetition=2),
    "cove": Place(name="the cove", sea=True, myth=True, affords={"carry"}, repetition=2),
}

ACTIONS = {
    "carry": Action(
        id="carry",
        verb="carry the others' shells across the wet rocks",
        gerund="carrying shells",
        attempt="try to carry them again",
        helps="carry the shells without dropping them",
        mess="tide",
        zone={"feet"},
        keyword="sea",
        tags={"sea", "others", "kindness", "repetition"},
    ),
    "gather": Action(
        id="gather",
        verb="gather seaweed for the others",
        gerund="gathering seaweed",
        attempt="gather it one more time",
        helps="gather the seaweed without slipping",
        mess="tide",
        zone={"feet"},
        keyword="myth",
        tags={"sea", "myth", "others", "kindness"},
    ),
}

GIFTS = [
    Gift(id="sandals", label="sandals", phrase="a pair of steady sandals", region="feet", protects={"tide"}),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pname, place in PLACES.items():
        for aid, act in ACTIONS.items():
            if act.mess in {"tide"} and select_gift(act):
                combos.append((pname, aid))
    return combos


@dataclass
class StoryParams:
    place: str
    action: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about the sea, myth, others, kindness, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.action:
        combos = [c for c in combos if c[1] == args.action]
    if not combos:
        raise StoryError("No valid sea-side comedy story matches those choices.")
    place, action = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Milo", "Mina", "Pip", "Tess", "Jory"])
    return StoryParams(place=place, action=action, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for young children about "{f["place"].name}", the sea, and a little myth.',
        f"Tell a story where {f['hero'].id} keeps trying to help the others, learns a lesson, and ends up kinder.",
        f"Write a repetitive, funny sea story that includes kindness, others, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    return [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {hero.id}, who keeps trying to help the others near the sea.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that helping the others works better when {hero.pronoun('subject')} is kind and careful instead of rushing.",
        ),
        QAItem(
            question=f"What made the story funny?",
            answer=f"The sea kept making things slippery, so {hero.id} had to try again and again, which made the helping look a little silly.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is the sea?", answer="The sea is a huge body of salt water, and it can be windy, wet, and a little splashy."),
        QAItem(question="What is kindness?", answer="Kindness means doing something helpful or gentle for someone else."),
        QAItem(question="What does repetition mean?", answer="Repetition means doing or saying something more than once."),
        QAItem(question="What is a myth?", answer="A myth is an old story people tell again and again, often about something special or strange."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIONS[params.action], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


ASP_RULES = r"""
place(seashore). place(harbor). place(cove).
action(carry). action(gather).
valid_story(P,A) :- place(P), action(A).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p, a in valid_combos():
            params = StoryParams(place=p, action=a, name="Milo")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
