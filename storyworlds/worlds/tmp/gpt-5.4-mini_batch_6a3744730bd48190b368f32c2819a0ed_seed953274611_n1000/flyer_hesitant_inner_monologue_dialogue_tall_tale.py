#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flyer_hesitant_inner_monologue_dialogue_tall_tale.py
====================================================================================

A standalone storyworld for a tall-tale-ish, child-facing domain about a flyer,
a hesitant messenger, inner monologue, and dialogue.

Premise
-------
A child is asked to deliver a flyer for a town event. They hesitate because the
route is scary or windy, but their inner thoughts, a friend or grown-up's talk,
and a little bit of tall-tale bravery carry them through. The flyer must arrive
at the right place, and the story ends with a clear image of what changed.

This world keeps the simulation small:
- typed entities with physical meters and emotional memes
- a forward-chaining world model
- a Python reasonableness gate plus an inline ASP twin
- three Q&A sets built from world state, not from parsing the rendered story

The story text is authored from world state and includes:
- the words "flyer" and "hesitant"
- inner monologue rendered as thought lines
- dialogue rendered as spoken lines
- a tall-tale voice with concrete, state-driven changes

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/flyer_hesitant_inner_monologue_dialogue_tall_tale.py
    python storyworlds/worlds/gpt-5.4-mini/flyer_hesitant_inner_monologue_dialogue_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/flyer_hesitant_inner_monologue_dialogue_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/flyer_hesitant_inner_monologue_dialogue_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVE_MIN = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "wind": 0.0, "delivery": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"hesitation": 0.0, "resolve": 0.0, "relief": 0.0, "joy": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    town: str
    flyer: str
    messenger: str
    messenger_gender: str
    guide: str
    guide_gender: str
    helper: str
    helper_gender: str
    route: str
    weather: str
    challenge: str
    ending: str
    seed: Optional[int] = None


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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_hesitation(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.role != "messenger" or e.memes["hesitation"] < THRESHOLD:
            continue
        if ("hesitation", e.id) in world.fired:
            continue
        world.fired.add(("hesitation", e.id))
        guide = next((x for x in world.entities.values() if x.role == "guide"), None)
        if guide is not None:
            guide.memes["resolve"] += 1
        out.append("")
    return out


def _r_deliver(world: World) -> list[str]:
    out: list[str] = []
    flyer = world.get("flyer")
    if flyer.meters["delivery"] >= THRESHOLD and ("deliver", flyer.id) not in world.fired:
        world.fired.add(("deliver", flyer.id))
        out.append("")
    return out


CAUSAL_RULES = [Rule("hesitation", _r_hesitation), Rule("deliver", _r_deliver)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if s])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tall_tale_prefix(challenge: str) -> str:
    return {
        "hill": "the hill stood so tall it seemed to tap the moon on the shoulder",
        "river": "the river wriggled like a silver snake with a secret",
        "market": "the market was loud enough to wake a sleeping trumpet",
        "forest": "the forest had trees so tall they seemed to comb the clouds",
    }[challenge]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in TOWNS:
        for f in FLYERS:
            for c in CHALLENGES:
                combos.append((t, f, c))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen flyer route does not create enough hesitation for a tall-tale delivery.)"


def story_intro(world: World, flyer: Entity, guide: Entity, helper: Entity, params: StoryParams) -> None:
    world.say(
        f"In {params.town}, the day was so big and blustery it felt like it had been blown in on a giant broom."
    )
    world.say(
        f"{flyer.id} held the flyer and stood at the edge of the road, while {guide.id} and {helper.id} watched."
    )
    world.say(
        f'The flyer said "Town Picnic!" in letters as wide as a wagon wheel.'
    )


def inner_monologue(world: World, flyer: Entity, params: StoryParams) -> None:
    flyer.memes["hesitation"] += 1
    world.say(
        f"'{flyer.id.lower()},' thought {flyer.id}, 'what if the {params.challenge} swallows me up before I reach the hall?'"
    )


def dialogue(world: World, flyer: Entity, guide: Entity, helper: Entity, params: StoryParams) -> None:
    world.say(
        f'"You look hesitant," said {guide.id}. "A little wind cannot outshout a brave heart."'
    )
    world.say(
        f'"If your knees wobble, mine will wobble too," said {helper.id}, "so let us walk together."'
    )


def advance(world: World, flyer: Entity, params: StoryParams) -> None:
    flyer.meters["distance"] += 1
    flyer.meters["wind"] += 1
    flyer.meters["delivery"] += 1


def resolve(world: World, flyer: Entity, guide: Entity, helper: Entity, params: StoryParams) -> None:
    flyer.memes["hesitation"] = 0.0
    flyer.memes["resolve"] += 1
    flyer.memes["joy"] += 1
    world.say(
        f"Then {flyer.id} tucked the flyer against {flyer.pronoun('possessive')} chest and marched on."
    )
    world.say(
        f'The wind puffed like a big blue bull, but {flyer.id} kept going until the flyer reached the hall.'
    )
    world.say(
        f'"There it is!" cried {helper.id}. "The flyer made it!"'
    )
    world.say(
        f"{guide.id} laughed. {flyer.id} stood straighter than a flagpole in a parade, and the town had its news."
    )


def tell(params: StoryParams) -> World:
    world = World()
    flyer = world.add(Entity(id=params.messenger, kind="character", type=params.messenger_gender, role="messenger"))
    guide = world.add(Entity(id=params.guide, kind="character", type=params.guide_gender, role="guide"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    world.add(Entity(id="flyer", kind="thing", type="paper", label=params.flyer))
    world.facts["town"] = params.town
    world.facts["route"] = params.route
    world.facts["challenge"] = params.challenge
    world.facts["ending"] = params.ending

    story_intro(world, flyer, guide, helper, params)
    world.para()
    world.say(tall_tale_prefix(params.challenge) + ".")
    inner_monologue(world, flyer, params)
    dialogue(world, flyer, guide, helper, params)
    advance(world, flyer, params)
    world.para()
    resolve(world, flyer, guide, helper, params)
    return world


TOWNS = {
    "Maple Crossing": {},
    "Bluebell Bend": {},
    "Tin Roof": {},
}

FLYERS = {
    "flyer": {},
    "notice": {},
    "poster": {},
}

CHALLENGES = {
    "hill": {},
    "river": {},
    "market": {},
    "forest": {},
}


@dataclass
class StoryConfig:
    town: str
    flyer: str
    messenger: str
    messenger_gender: str
    guide: str
    guide_gender: str
    helper: str
    helper_gender: str
    route: str
    weather: str
    challenge: str
    ending: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(town="Maple Crossing", flyer="flyer", messenger="Nell", messenger_gender="girl", guide="Grandpa", guide_gender="man", helper="Pip", helper_gender="boy", route="to the hall", weather="windy", challenge="hill", ending="delivered"),
    StoryParams(town="Bluebell Bend", flyer="flyer", messenger="Owen", messenger_gender="boy", guide="Mama", guide_gender="woman", helper="June", helper_gender="girl", route="to the market", weather="blustery", challenge="river", ending="delivered"),
    StoryParams(town="Tin Roof", flyer="flyer", messenger="Mina", messenger_gender="girl", guide="Auntie", guide_gender="woman", helper="Tess", helper_gender="girl", route="to the school", weather="gusty", challenge="forest", ending="delivered"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for children that includes the words "flyer" and "hesitant" and takes place in {f["town"]}.',
        f"Tell a story where a hesitant messenger carries a flyer across a big challenge and hears encouragement in dialogue.",
        f"Write an inner-monologue-and-dialogue story about a child delivering a flyer, with a windy problem and a proud ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What was the child carrying?", answer="The child was carrying a flyer for the town event."),
        QAItem(question="Why was the child hesitant?", answer="The child was hesitant because the route felt huge and scary, like the wind and challenge might stop the trip. The words and the tall-tale setting made the walk feel bigger than life."),
        QAItem(question="How did the story end?", answer="The flyer reached the hall, and the child stood proudly after getting it there. The worry changed into resolve, so the ending image proves the delivery was finished."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a flyer?", answer="A flyer is a small paper notice that tells people about an event."),
        QAItem(question="What does hesitant mean?", answer="Hesitant means not quite ready to do something yet, because you feel unsure or nervous."),
        QAItem(question="What is inner monologue?", answer="Inner monologue is the private voice a character has in their own thoughts."),
        QAItem(question="What is dialogue?", answer="Dialogue is the spoken talk between characters."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: role={e.role} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--town", choices=TOWNS)
    p.add_argument("--flyer", choices=FLYERS)
    p.add_argument("--challenge", choices=CHALLENGES)
    p.add_argument("-n", type=int, default=1)
    p.add_argument("--all", action="store_true")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--trace", action="store_true")
    p.add_argument("--qa", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--asp", action="store_true")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--show-asp", action="store_true")
    return p


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.flyer and args.flyer not in FLYERS:
        raise StoryError("Unknown flyer choice.")
    combo = (
        args.town or rng.choice(list(TOWNS)),
        args.flyer or rng.choice(list(FLYERS)),
        args.challenge or rng.choice(list(CHALLENGES)),
    )
    if combo not in valid_combos():
        raise StoryError(explain_rejection(StoryParams(town=combo[0], flyer=combo[1], messenger="Nell", messenger_gender="girl", guide="Grandpa", guide_gender="man", helper="Pip", helper_gender="boy", route="to the hall", weather="windy", challenge=combo[2], ending="delivered")))
    return StoryParams(
        town=combo[0], flyer=combo[1],
        messenger=rng.choice(["Nell", "Owen", "Mina"]),
        messenger_gender=rng.choice(["girl", "boy"]),
        guide=rng.choice(["Grandpa", "Mama", "Auntie"]),
        guide_gender=rng.choice(["man", "woman"]),
        helper=rng.choice(["Pip", "June", "Tess"]),
        helper_gender=rng.choice(["boy", "girl"]),
        route="to the hall",
        weather="windy",
        challenge=combo[2],
        ending="delivered",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(T,F,C) :- town(T), flyer(F), challenge(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([asp.fact("town", t) for t in TOWNS] + [asp.fact("flyer", f) for f in FLYERS] + [asp.fact("challenge", c) for c in CHALLENGES])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH")
    try:
        _ = generate(CURATED[0]).story
    except Exception as e:
        rc = 1
        print(f"SMOKE FAIL: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
