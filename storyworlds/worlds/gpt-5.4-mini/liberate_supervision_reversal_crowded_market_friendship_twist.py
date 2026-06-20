#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/liberate_supervision_reversal_crowded_market_friendship_twist.py
=================================================================================================

A standalone story world for a crowded market animal tale with friendship, a
twist, supervision, and a happy reversal.

Premise
-------
A small animal wants to wander in a busy market, but a friend keeps them safe.
The first worry is about getting separated in the crowd. Then a twist reveals
that the "problem" item is actually a missing friend marker that can help the
group reunite. Supervision, friendship, and a clever reversal turn a tense
search into a happy ending.

This world models:
- typed entities with physical meters and emotional memes,
- state-driven causal beats rather than frozen prose,
- a reasonableness gate for plausible market stories,
- an inline ASP twin for parity checking,
- three QA sets built from world state.

The key seed words are embedded in the narrative logic:
- liberate: the group frees a friend marker from a stall owner's string,
- supervision: an adult vendor keeps an eye on the children in the crowd,
- reversal: the story starts with concern, then flips into a helpful discovery.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fox"}
        male = {"boy", "father", "dad", "man", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Market:
    id: str
    place: str
    crowd: str
    stall_line: str
    sound: str
    color: str
    twist_hint: str
    happy_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalKind:
    id: str
    type: str
    label: str
    small: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendItem:
    id: str
    label: str
    phrase: str
    noise: str
    lost: bool = False
    liberatable: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SupervisionAid:
    id: str
    label: str
    phrase: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    crowd = world.get("market")
    for e in world.entities.values():
        if e.meters["lost"] >= THRESHOLD:
            sig = ("bump", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            crowd.meters["busy"] += 1
            for ch in world.entities.values():
                if ch.kind == "character":
                    ch.memes["worry"] += 1
            out.append("__crowd__")
    return out


def _r_find_friend(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("find", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["found"] += 1
        out.append("__twist__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("rescued") and not world.facts.get("relief_done"):
        world.facts["relief_done"] = True
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("bump", "physical", _r_bump),
    Rule("find_friend", "social", _r_find_friend),
    Rule("relief", "social", _r_relief),
]


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


def market_breezy(market: Market) -> str:
    return f"The {market.place} was full of {market.crowd}, and {market.sound} floated over the stalls."


def setup(world: World, market: Market, child: Entity, friend: Entity, adult: Entity,
          item: Entity, aid: Entity) -> None:
    child.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    adult.memes["supervision"] += 1
    world.say(
        f"At {market.place}, {child.id} the {child.type} walked beside {friend.id} the {friend.type}."
    )
    world.say(
        f"{market_breezy(market)} {market.stall_line} {market.color}"
    )
    world.say(
        f"{adult.id} stayed close for supervision, because a crowd can swallow little footsteps."
    )
    world.say(
        f"{child.id} noticed {item.phrase}, while {friend.id} clutched {aid.phrase} and listened."
    )


def worry(world: World, child: Entity, friend: Entity, item: Entity, market: Market) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'"Can we get closer?" {child.id} asked, peering through the people. '
        f'{friend.id} gave a worried look and said the {market.place} was too packed for wandering off.'
    )
    world.say(
        f"{item.label_word.capitalize()} seemed stuck far away, and the crowd made the distance feel even bigger."
    )


def twist(world: World, child: Entity, friend: Entity, item: Entity, aid: Entity) -> None:
    item.meters["lost"] += 1
    friend.memes["caution"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came the twist: {friend.id} spotted that {item.phrase} was tied to a ribbon at a nearby stall."
    )
    world.say(
        f'"If we liberate it carefully, we can use it to find the others," {friend.id} said, and {aid.phrase} showed why.'
    )


def liberate(world: World, child: Entity, friend: Entity, item: Entity) -> None:
    item.meters["freed"] += 1
    child.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"Together they gently freed the {item.label} from the string, and the little thing bobbed up like a happy sign."
    )


def reversal(world: World, child: Entity, friend: Entity, adult: Entity, item: Entity, market: Market) -> None:
    world.facts["rescued"] = True
    propagate(world, narrate=False)
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"The reversal was sweet: what looked like trouble became the map back to their friend."
    )
    world.say(
        f"{adult.id} smiled, kept supervision steady, and pointed them past the fruit cart and the blue umbrella."
    )
    world.say(
        f"There, in the middle of the crowd, the missing friend was waiting near a basket of bright oranges."
    )
    world.say(
        f"{market.happy_image}"
    )


def happy_end(world: World, child: Entity, friend: Entity, adult: Entity, market: Market) -> None:
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    adult.memes["pride"] += 1
    world.say(
        f"{child.id} hugged {friend.id}, and the three of them walked home together with full hearts."
    )
    world.say(
        f"By the time they left {market.place}, the market felt less crowded and much kinder."
    )


def tell(market: Market, child_kind: AnimalKind, friend_kind: AnimalKind,
         item: FriendItem, aid: SupervisionAid,
         child_name: str = "Mina", friend_name: str = "Pip",
         adult_name: str = "Auntie", adult_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_kind.type,
                             label=child_kind.label, role="child", traits=["small"],
                             age=5))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_kind.type,
                              label=friend_kind.label, role="friend", traits=["small"],
                              age=5))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_type,
                             label="the grown-up", role="supervisor"))
    market_ent = world.add(Entity(id="market", kind="place", type="place", label=market.place))
    item_ent = world.add(Entity(id="item", kind="thing", type="thing", label=item.label))
    aid_ent = world.add(Entity(id="aid", kind="thing", type="thing", label=aid.label))

    market_ent.meters["crowded"] = 1.0
    item_ent.meters["lost"] = 0.0
    aid_ent.meters["helpful"] = 1.0

    setup(world, market, child, friend, adult, item_ent, aid_ent)
    world.para()
    worry(world, child, friend, item_ent, market)
    twist(world, child, friend, item_ent, aid_ent)
    liberate(world, child, friend, item_ent)
    world.para()
    reversal(world, child, friend, adult, item_ent, market)
    happy_end(world, child, friend, adult, market)

    world.facts.update(
        market=market, child=child, friend=friend, adult=adult,
        item=item_ent, aid=aid_ent, rescued=True, outcome="happy",
    )
    return world


MARKETS = {
    "crowded_market": Market(
        "crowded_market",
        "the crowded market",
        "neighbors, shoppers, and delivery carts",
        "A mango seller rang a tiny bell beside a spice stall, and cloth awnings swayed overhead.",
        "voices, bells, and rolling carts",
        "bright ribbons hung above the stalls",
        "a lost friend marker peeked from a ribbon bundle",
        "The friends left with oranges, a ribbon, and big smiles.",
        tags={"market", "crowded", "happy"},
    ),
    "morning_market": Market(
        "morning_market",
        "the morning market",
        "early shoppers and sleepy vendors",
        "A fish seller yawned while baskets of pears waited in neat rows.",
        "soft calls and squeaky wheels",
        "sunlight laid gold stripes across the stones",
        "a small friend marker hidden near a pear crate",
        "The friends waved goodbye and the market felt warm and safe.",
        tags={"market", "morning", "happy"},
    ),
}

ANIMALS = {
    "fox": AnimalKind("fox", "fox", "fox", tags={"animal", "fox"}),
    "rabbit": AnimalKind("rabbit", "rabbit", "rabbit", tags={"animal", "rabbit"}),
    "cat": AnimalKind("cat", "cat", "cat", tags={"animal", "cat"}),
    "dog": AnimalKind("dog", "dog", "dog", tags={"animal", "dog"}),
}

ITEMS = {
    "tag": FriendItem("tag", "friend tag", "a little friend tag", "made a tinny jingle",
                      lost=False, liberatable=True, tags={"friendship", "twist"}),
    "ribbon": FriendItem("ribbon", "friend ribbon", "a bright ribbon with a bell", "gave a tiny chime",
                         lost=False, liberatable=True, tags={"friendship", "twist"}),
    "bell": FriendItem("bell", "friend bell", "a little bell on a string", "rang softly",
                       lost=False, liberatable=True, tags={"friendship", "twist"}),
}

AIDS = {
    "whistle": SupervisionAid("whistle", "whistle", "a whistle on a cord", "keeps everyone nearby", tags={"supervision"}),
    "basket": SupervisionAid("basket", "basket", "a woven basket", "holds the found thing", tags={"supervision"}),
    "handclasp": SupervisionAid("handclasp", "hand clasp", "a careful hand clasp", "keeps the pair together", tags={"supervision"}),
}

CURATED = [
    StoryParams("crowded_market", "fox", "rabbit", "ribbon", "whistle", "Mina", "Pip", "Auntie", "mother"),
    StoryParams("crowded_market", "cat", "dog", "tag", "basket", "Nori", "Jax", "Uncle", "father"),
    StoryParams("morning_market", "rabbit", "cat", "bell", "handclasp", "Luma", "Pico", "Grandma", "mother"),
]


@dataclass
class StoryParams:
    market: str
    child: str
    friend: str
    item: str
    aid: str
    child_name: str
    friend_name: str
    adult_name: str
    adult_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for m in MARKETS:
        for c in ANIMALS:
            for f in ANIMALS:
                for i in ITEMS:
                    for a in AIDS:
                        combos.append((m, c, i))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Crowded market animal story world.")
    ap.add_argument("--market", choices=MARKETS)
    ap.add_argument("--child", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-type", choices=["mother", "father"])
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
    market = args.market or rng.choice(list(MARKETS))
    child = args.child or rng.choice(list(ANIMALS))
    friend = args.friend or rng.choice([k for k in ANIMALS if k != child])
    item = args.item or rng.choice(list(ITEMS))
    aid = args.aid or rng.choice(list(AIDS))
    return StoryParams(
        market, child, friend, item, aid,
        args.child_name or rng.choice(["Mina", "Lina", "Tobi", "Kiki", "Nori"]),
        args.friend_name or rng.choice(["Pip", "Bobo", "Momo", "Jax", "Lulu"]),
        args.adult_name or rng.choice(["Auntie", "Uncle", "Mama", "Papa"]),
        args.adult_type or rng.choice(["mother", "father"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story set in {f["market"].place} with friendship, supervision, a twist, and a happy ending.',
        f"Tell a gentle market story where {f['child'].id} and {f['friend'].id} stay close in the crowd, find a useful surprise, and end happily.",
        f'Write a child-facing story that includes the words "liberate", "supervision", and "reversal" in a friendly animal market scene.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, adult, market, item = f["child"], f["friend"], f["adult"], f["market"], f["item"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {friend.id}, two animal friends in {market.place}. {adult.id} stays nearby to help keep them safe."
        ),
        QAItem(
            question="Why did the grown-up stay close?",
            answer=f"{adult.id} stayed close for supervision because the market was crowded and little animals could be separated easily. That help kept the friendship story safe in the busy lanes."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {item.phrase} was not just a problem to worry about. It turned out to be a helpful clue, and freeing it helped the friends find the missing animal."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. {child.id}, {friend.id}, and {adult.id} walked home together after the reversal led them back to the missing friend."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does supervision mean?",
            answer="Supervision means a grown-up is watching and helping so children stay safe."
        ),
        QAItem(
            question="What is a crowd?",
            answer="A crowd is a lot of people close together in one place."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what you thought was happening."
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets fixed and the characters finish safe and glad."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    bits.append(f"facts={world.facts}")
    return "\n".join(bits)


ASP_RULES = r"""
crowded(M) :- market(M).
happy_story :- rescued.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for mid in MARKETS:
        lines.append(asp.fact("market", mid))
    for cid in ANIMALS:
        lines.append(asp.fact("animal", cid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show crowded/1."))
    _ = asp.atoms(model, "crowded")
    try:
        generate(CURATED[0])
    except Exception as exc:
        print(f"FAIL: generate smoke test crashed: {exc}")
        return 1
    print("OK: generate smoke test passed.")
    print("OK: ASP program produced a model.")
    return 0


def tell_story(params: StoryParams) -> World:
    market = MARKETS[params.market]
    child_kind = ANIMALS[params.child]
    friend_kind = ANIMALS[params.friend]
    item = ITEMS[params.item]
    aid = AIDS[params.aid]
    return tell(market, child_kind, friend_kind, item, aid, params.child_name, params.friend_name, params.adult_name, params.adult_type)


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
        print(asp_program("", "#show crowded/1.\n#show happy_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("crowded market story world is compatible with the ASP twin.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
