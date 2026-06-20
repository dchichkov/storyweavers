#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wicket_tamper_pinch_curiosity_repetition_friendship_adventure.py
================================================================================================

A standalone storyworld for a tiny adventure about curiosity, repetition,
friendship, and a mysterious wicket.

Seed words:
- wicket
- tamper
- pinch

Style:
- Adventure

This world models a small trail-side scene: two friends keep coming back to a
little wicket gate, one child gets curious about a latch and a treasure clue,
and a pinch of bad tampering can either be gently corrected or cause a mess.
The story engine uses typed entities with physical meters and emotional memes,
forward-chained causal rules, and a reasonableness gate that only allows
plausible adventure setups.
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    repeated_spot: str
    hidden_spot: str
    adventure_word: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    makes_mess: bool = False
    can_tamper: bool = False
    can_pinch: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    sense: int
    success: str
    fail: str
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
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["curiosity"] < THRESHOLD or e.meters["visits"] < 2:
            continue
        sig = ("repeat", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["resolve"] += 1
        out.append("__repeat__")
    return out


def _r_tamper(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["tamper"] < THRESHOLD:
            continue
        sig = ("tamper", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "gate" in world.entities:
            world.get("gate").meters["misaligned"] += 1
        out.append("__tamper__")
    return out


def _r_pinch(world: World) -> list[str]:
    out: list[str] = []
    if "gate" not in world.entities:
        return out
    gate = world.get("gate")
    if gate.meters["misaligned"] < THRESHOLD or "friend" not in world.entities:
        return out
    sig = ("pinch", gate.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend = world.get("friend")
    friend.memes["worry"] += 1
    out.append("__pinch__")
    return out


CAUSAL_RULES = [
    Rule("repeat", "social", _r_repeat),
    Rule("tamper", "physical", _r_tamper),
    Rule("pinch", "social", _r_pinch),
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


def reasonableness_ok(place: Place, item: Item, plan: Plan) -> bool:
    return item.can_tamper and item.makes_mess and plan.sense >= SENSE_MIN


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def best_plan() -> Plan:
    return max(PLANS.values(), key=lambda p: p.sense)


def predict_tamper(world: World, child_id: str) -> dict:
    sim = world.copy()
    child = sim.get(child_id)
    child.meters["tamper"] += 1
    if "gate" in sim.entities:
        sim.get("gate").meters["misaligned"] += 1
    return {
        "misaligned": bool(sim.entities.get("gate") and sim.get("gate").meters["misaligned"] >= THRESHOLD),
    }


def start(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {friend.id} set out like little adventurers at {place.label}. "
        f"{place.scene}"
    )


def discover(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.meters["visits"] += 1
    friend.meters["visits"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"They found a small wicket near {place.hidden_spot}. The wicket stood between them and the next turn of the trail."
    )
    world.say(f"{hero.id} peered closer. \"I wonder what is behind it,\" {hero.pronoun()} said.")


def repeat_walk(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.meters["visits"] += 1
    friend.meters["visits"] += 1
    world.say(
        f"So they walked back to the wicket again, and then again, because adventure often begins with looking twice."
    )
    world.say(f"Each time, {friend.id} laughed and counted the steps to the wicket gate.")


def tamper_attempt(world: World, hero: Entity, item: Item) -> None:
    hero.meters["tamper"] += 1
    hero.memes["boldness"] += 1
    world.say(
        f"{hero.id} reached for the latch and tried to tamper with it, just a tiny bit, to see if it would open faster."
    )
    world.say(f"{hero.id} gave the latch a pinch and a twist.")


def warn(world: World, friend: Entity, hero: Entity, item: Item) -> None:
    friend.memes["care"] += 1
    pred = predict_tamper(world, hero.id)
    extra = " It might pinch your fingers." if pred["misaligned"] else ""
    world.say(
        f"{friend.id} frowned. \"Don't tamper with the wicket,\" {friend.pronoun()} said. "
        f"\"It could stick and pinch us both.\"{extra}"
    )


def choose_plan(world: World, guide: Entity, hero: Entity, plan: Plan) -> None:
    world.say(
        f"{guide.id} pointed to a better way: {plan.success}."
    )


def fix_and_open(world: World, hero: Entity, friend: Entity, place: Place, item: Item, plan: Plan) -> None:
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} listened at once. Together they followed the safe step and {plan.success}."
    )
    world.say(
        f"The wicket swung open with a soft creak, and the path beyond looked bright and friendly."
    )


def pinch_story(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    gate = world.get("gate")
    world.say(
        f"Then the wicket gave one stubborn pinch of its own and caught {hero.id}'s sleeve for a moment."
    )
    world.say(f"{friend.id} laughed, helped {hero.id} free, and both children stepped back safely.")


def ending(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After that, they went on together, hand in hand, with the wicket behind them and the adventure ahead."
    )
    world.say(
        f"By the time the sun dipped low, {hero.id} and {friend.id} had learned that curious friends can keep a story moving without tampering with what should stay still."
    )


def tell(place: Place, item: Item, plan: Plan, hero_name: str = "Mina",
         hero_type: str = "girl", friend_name: str = "Jasper",
         friend_type: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    gate = world.add(Entity(id="gate", type="thing", label="the wicket"))
    clue = world.add(Entity(id="clue", type="thing", label="the trail clue"))

    world.facts["place"] = place
    world.facts["item"] = item
    world.facts["plan"] = plan
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["gate"] = gate
    world.facts["clue"] = clue

    start(world, hero, friend, place)
    discover(world, hero, friend, place)
    world.para()
    repeat_walk(world, hero, friend, place)
    warn(world, friend, hero, item)
    if plan.id == "safe_open":
        choose_plan(world, friend, hero, plan)
        world.para()
        fix_and_open(world, hero, friend, place, item, plan)
    else:
        tamper_attempt(world, hero, item)
        propagate(world, narrate=True)
        world.para()
        pinch_story(world, hero, friend, place)
        ending(world, hero, friend, place)
    return world


PLACES = {
    "trail": Place("trail", "the forest trail", "The trail curled between pine trunks and sparkled with little sun-patches.", "the little wicket at the bend", "the gate tucked in the ferns", "adventure"),
    "harbor": Place("harbor", "the harbor path", "The harbor path smelled of salt and rope, and gulls cried overhead.", "the wicket near the dock fence", "the gate by the tall reeds", "adventure"),
    "orchard": Place("orchard", "the orchard lane", "Rows of trees made a green tunnel, and apples shone like tiny lanterns.", "the wicket beside the apple cart", "the gate by the stone wall", "adventure"),
}

ITEMS = {
    "latch": Item("latch", "latch", "a small brass latch", "tool", makes_mess=True, can_tamper=True, can_pinch=True, tags={"wicket", "tamper", "pinch"}),
    "pin": Item("pin", "pin", "a tiny pin", "tool", makes_mess=False, can_tamper=True, can_pinch=True, tags={"pinch"}),
    "rope": Item("rope", "rope", "a loose rope loop", "tool", makes_mess=False, can_tamper=True, can_pinch=False, tags={"rope"}),
}

PLANS = {
    "safe_open": Plan("safe_open", 3, "untied the latch gently and asked an adult to show the right way", "tried to force the wicket"),
    "peek": Plan("peek", 2, "looked through the bars and followed the clue on the ground", "pushed harder"),
    "tamper_more": Plan("tamper_more", 1, "twisted the latch until it squeaked", "kept tampering"),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Tess", "Ruby"]
BOY_NAMES = ["Jasper", "Theo", "Finn", "Owen", "Eli", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for item_id, item in ITEMS.items():
            for plan_id, plan in PLANS.items():
                if reasonableness_ok(PLACES[place], item, plan):
                    combos.append((place, item_id, plan_id))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    plan: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "wicket": [("What is a wicket?", "A wicket is a small gate or door in a fence. It can open and close so people can pass through.")],
    "tamper": [("What does tamper mean?", "To tamper means to meddle with something that should be left alone, often in a rough or risky way.")],
    "pinch": [("What does pinch mean?", "To pinch is to squeeze something tightly, or to catch a little bit of skin or cloth by accident.")],
    "curiosity": [("What is curiosity?", "Curiosity is the feeling that makes you want to know more and look closely at new things.")],
    "repetition": [("What is repetition?", "Repetition means doing the same thing again and again. It can help you learn or notice something important.")],
    "friendship": [("What is friendship?", "Friendship is when people care about each other, help each other, and have fun together.")],
    "adventure": [("What is an adventure?", "An adventure is an exciting trip or experience where you discover new places and things.")],
}
KNOWLEDGE_ORDER = ["wicket", "tamper", "pinch", "curiosity", "repetition", "friendship", "adventure"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child that includes the words "wicket", "tamper", and "pinch".',
        f"Tell a friendship story where {f['hero'].id} and {f['friend'].id} keep coming back to a wicket because they are curious.",
        f"Write a gentle adventure where repetition helps two friends solve a small problem without making the wicket worse.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, place, item, plan = f["hero"], f["friend"], f["place"], f["item"], f["plan"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two friends on an adventure at {place.label}. They keep each other company the whole time."),
        ("Why did they keep going back to the wicket?",
         f"They were curious and wanted to see what was beyond it. The repetition of walking back made the wicket feel more important and more mysterious."),
        ("What did {0} try to do?".format(hero.id),
         f"{hero.id} tried to tamper with the wicket latch. {item.phrase} seemed like a quick shortcut, but it caused trouble instead of helping."),
    ]
    if f["plan"].id == "safe_open":
        qa.append((
            "How did they solve the problem?",
            f"They stopped tampering and chose the safe way instead. {friend.id} suggested a calmer plan, and that let them open the wicket without getting hurt."
        ))
        qa.append((
            "How did the story end?",
            f"The wicket opened softly, and the friends went on together. The ending feels brave and happy because they used patience instead of forcing the latch."
        ))
    else:
        qa.append((
            "What happened after the tampering?",
            f"The wicket gave a little pinch and caught {hero.id}'s sleeve for a moment. {friend.id} helped {hero.id} back, and they continued safely, but more carefully than before."
        ))
        qa.append((
            "What did the children learn?",
            f"They learned that curiosity is good, but tampering can cause a pinch or a snag. Friendship helped them stop, laugh, and choose a safer next step."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item"].tags) | {"curiosity", "repetition", "friendship", "adventure"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("trail", "latch", "safe_open", "Mina", "girl", "Jasper", "boy"),
    StoryParams("harbor", "pin", "peek", "Theo", "boy", "Luna", "girl"),
    StoryParams("orchard", "rope", "tamper_more", "Ivy", "girl", "Finn", "boy"),
]


def explain_rejection(item: Item, plan: Plan) -> str:
    return f"(No story: this setup would not make a sensible adventure about a wicket, because the chosen item or plan does not plausibly lead to a pinch or a fix.)"


def outcome_of(params: StoryParams) -> str:
    return "safe" if params.plan == "safe_open" else "pinch"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if it.makes_mess:
            lines.append(asp.fact("makes_mess", iid))
        if it.can_tamper:
            lines.append(asp.fact("can_tamper", iid))
        if it.can_pinch:
            lines.append(asp.fact("can_pinch", iid))
    for pid, pl in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, pl.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, I, N) :- place(P), item(I), plan(N), can_tamper(I), makes_mess(I), sense(N, S), sense_min(M), S >= M.
outcome(safe) :- plan(safe_open).
outcome(pinch) :- plan(X), X != safe_open.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    return outcome_of(params)


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure storyworld about a wicket, curiosity, repetition, and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    if args.item and args.plan and not reasonableness_ok(PLACES[args.place or combos[0][0]], ITEMS[args.item], PLANS[args.plan]):
        raise StoryError(explain_rejection(ITEMS[args.item], PLANS[args.plan]))
    place, item, plan = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (BOY_NAMES + GIRL_NAMES) if n != hero])
    return StoryParams(place, item, plan, hero, hero_gender, friend, friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ITEMS[params.item], PLANS[params.plan], params.hero, params.hero_gender, params.friend, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero} & {p.friend}: {p.place}, {p.item}, {p.plan} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
