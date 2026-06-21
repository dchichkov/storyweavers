#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nectarine_shaker_lesson_learned_friendship_adventure.py
======================================================================================

A small adventure storyworld about two friends, a nectarine, and a shaker.
The premise is simple: a child wants to make an adventure snack, a mistake
spills the plan, friends help, and the lesson is learned.

The world uses typed entities with physical meters and emotional memes, a tiny
forward-chaining simulation, a Python reasonableness gate, and an inline ASP
twin. The generated stories are meant to feel like complete TinyStories-style
episodes with a clear beginning, middle turn, and ending image.
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
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    safe_role: str = ""
    edible: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    action: str
    sound: str
    sense: int
    power: int


@dataclass
class StoryParams:
    place: str = "dock"
    item: str = "nectarine"
    device: str = "shaker"
    response: str = "fix"
    hero: str = "Milo"
    hero_gender: str = "boy"
    friend: str = "June"
    friend_gender: str = "girl"
    adult: str = "captain"
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("bowl")
    if bowl.meters["shaken"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fruit = world.get("fruit")
    fruit.meters["dropped"] += 1
    world.get("deck").meters["mess"] += 1
    world.get("hero").memes["surprise"] += 1
    out.append("__spill__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    fruit = world.get("fruit")
    if fruit.meters["dropped"] < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["relief"] += 1
    friend.memes["kindness"] += 1
    out.append("__friendship__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("friendship", _r_friendship)]


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


def valid_combo(place: Place, item: Item, device: Device) -> bool:
    return "adventure" in place.affords and item.edible and device.sense >= SENSE_MIN


def sensible_devices() -> list[Device]:
    return [d for d in DEVICES.values() if d.sense >= SENSE_MIN]


def best_device() -> Device:
    return max(DEVICES.values(), key=lambda d: d.sense)


def predict_spill(world: World) -> dict:
    sim = world.copy()
    sim.get("bowl").meters["shaken"] += 1
    propagate(sim, narrate=False)
    return {"spilled": sim.get("fruit").meters["dropped"] >= THRESHOLD}


def setup(world: World, hero: Entity, friend: Entity, place: Place, item: Item) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright adventure day, {hero.id} and {friend.id} explored {place.label}. "
        f"{place.detail}"
    )
    world.say(
        f"They had a sweet {item.label} ready for the trail, and a little shaker that "
        f"clinked when it moved."
    )


def want_snack(world: World, hero: Entity, friend: Entity, item: Item, device: Device) -> None:
    world.say(
        f'"Let\'s make our snack sparkle," {hero.id} said. "{friend.id}, pass the {device.label}!"'
    )
    world.say(
        f"{friend.id} grinned, but {friend.pronoun()} knew the shaker could make trouble if it was used too hard."
    )


def warn(world: World, friend: Entity, hero: Entity, device: Device) -> None:
    friend.memes["care"] += 1
    pred = predict_spill(world)
    world.facts["predicted_spill"] = pred["spilled"]
    world.say(
        f'"Careful," {friend.id} said. "If you shake that {device.label} too fast, the fruit could spill."'
    )


def do_shake(world: World) -> None:
    world.get("bowl").meters["shaken"] += 1
    world.say("The shaker rattled. One quick shake was fun, but another shake sent the snack wobbling.")
    propagate(world, narrate=False)


def alarm(world: World, hero: Entity, friend: Entity, item: Item, adult: Entity) -> None:
    world.say(f'"Oh no!" {friend.id} cried. "{item.label} is slipping!"')
    world.say(f'"{adult.label_word.capitalize()}!" {hero.id} shouted.')


def fix(world: World, adult: Entity, item: Item) -> None:
    item.meters["dropped"] = 0.0
    world.get("bowl").meters["shaken"] = 0.0
    adult.memes["calm"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came over and steadied the bowl with one hand."
    )
    world.say(
        f"Then {adult.pronoun()} used the {world.get('device').label} the gentle way, "
        f"so the snack stayed neat and ready to eat."
    )


def lesson(world: World, hero: Entity, friend: Entity, device: Device) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say("For a moment, everyone laughed at the wobble.")
    world.say(
        f'"Now we know," {friend.id} said softly. "{device.label}s are for a little shake, not a wild one."'
    )
    world.say(
        f"{hero.id} nodded. The friends shared the snack and kept the shaker beside the map."
    )


def tell(place: Place, item: Item, device: Device, response: Device,
         hero_name: str = "Milo", hero_gender: str = "boy",
         friend_name: str = "June", friend_gender: str = "girl",
         adult_name: str = "Captain") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    adult = world.add(Entity(id="adult", kind="character", type="adult", label=adult_name, role="adult"))
    bowl = world.add(Entity(id="bowl", kind="thing", type="bowl", label=device.label))
    fruit = world.add(Entity(id="fruit", kind="thing", type="fruit", label=item.label))
    deck = world.add(Entity(id="deck", kind="thing", type="place", label=place.label))
    device_ent = world.add(Entity(id="device", kind="thing", type="tool", label=device.label))
    world.facts.update(hero=hero, friend=friend, adult=adult, bowl=bowl, fruit=fruit, deck=deck,
                       place=place, item=item, device=device, response=response)

    setup(world, hero, friend, place, item)
    world.para()
    want_snack(world, hero, friend, item, device)
    warn(world, friend, hero, device)
    do_shake(world)
    if fruit.meters["dropped"] >= THRESHOLD:
        world.para()
        alarm(world, hero, friend, item, adult)
        fix(world, adult, fruit)
        lesson(world, hero, friend, device)
    else:
        world.para()
        world.say("The snack stayed safe, and the friends still learned to move carefully.")

    return world


PLACES = {
    "dock": Place(id="dock", label="the dock", detail="The boards were warm, and the water glittered below.", affords={"adventure"}),
    "garden": Place(id="garden", label="the garden path", detail="The path wound between flowers like a little trail.", affords={"adventure"}),
    "cove": Place(id="cove", label="the quiet cove", detail="The shore curved like a secret map, perfect for a small quest.", affords={"adventure"}),
}

ITEMS = {
    "nectarine": Item(id="nectarine", label="nectarine", phrase="a ripe nectarine", kind="fruit", edible=True),
}

DEVICES = {
    "shaker": Device(id="shaker", label="shaker", phrase="a little shaker", action="shake", sound="clink", sense=3, power=2),
    "tiny_shaker": Device(id="tiny_shaker", label="tiny shaker", phrase="a tiny shaker", action="shake", sound="rattle", sense=2, power=1),
    "maraca": Device(id="maraca", label="maraca", phrase="a bright maraca", action="shake", sound="rattle", sense=3, power=2),
    "noisy_cup": Device(id="noisy_cup", label="cup", phrase="a cup", action="bang", sound="clack", sense=1, power=1),
}

CURATED = [
    StoryParams(place="dock", item="nectarine", device="shaker", response="fix", hero="Milo", hero_gender="boy", friend="June", friend_gender="girl", adult="Captain"),
    StoryParams(place="garden", item="nectarine", device="maraca", response="fix", hero="Nia", hero_gender="girl", friend="Owen", friend_gender="boy", adult="Aunt"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the words "{f["item"].label}" and "{f["device"].label}".',
        f"Tell a friendship story where {f['hero'].label} and {f['friend'].label} make a snack with a {f['device'].label}, learn to be careful, and fix a small mistake together.",
        f"Write a simple adventure about friends on {f['place'].label} that ends with a lesson learned and a shared snack.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, adult = f["hero"], f["friend"], f["adult"]
    place, item, device = f["place"], f["item"], f["device"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.label} and {friend.label}, who went on a small adventure together. Their {adult.label_word if hasattr(adult, 'label_word') else 'grown-up'} stayed nearby to help when needed."
        ),
        QAItem(
            question="What went wrong with the snack?",
            answer=f"The {device.label} was shaken too hard, so the {item.label} spilled out of the bowl. That made the friends stop and ask for help."
        ),
        QAItem(
            question="How was the problem fixed?",
            answer=f"{adult.label_word.capitalize()} steadied the bowl and showed them how to use the {device.label} gently. After that, the snack stayed neat and the friends could enjoy it together."
        ),
        QAItem(
            question="What did the friends learn?",
            answer=f"They learned that a good adventure still needs careful hands. They also learned that friendship means helping each other when a plan goes wobbly."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nectarine?",
            answer="A nectarine is a sweet fruit with smooth skin. People can wash it, slice it, and eat it as a snack."
        ),
        QAItem(
            question="What is a shaker?",
            answer="A shaker is a little object that makes a rattling sound when you move it. People can use it gently to mix or make music."
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means being kind, sharing, and helping each other. Friends listen when someone needs care."
        ),
    ]


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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(place: Place, item: Item, device: Device) -> str:
    if device.sense < SENSE_MIN:
        return f"(No story: {device.label} is too clumsy for a gentle lesson.)"
    if "adventure" not in place.affords:
        return f"(No story: {place.label} does not fit this adventure.)"
    if not item.edible:
        return f"(No story: the selected item is not a snack.)"
    return "(No story: this combination is not reasonable.)"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            for did, device in DEVICES.items():
                if valid_combo(place, item, device):
                    combos.append((pid, iid, did))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.device and DEVICES[args.device].sense < SENSE_MIN:
        raise StoryError(explain_rejection(next(iter(PLACES.values())), next(iter(ITEMS.values())), DEVICES[args.device]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.device is None or c[2] == args.device)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, device = rng.choice(sorted(combos))
    response = args.response or "fix"
    hero_gender = args.hero_gender if hasattr(args, "hero_gender") and args.hero_gender else "boy"
    friend_gender = args.friend_gender if hasattr(args, "friend_gender") and args.friend_gender else "girl"
    hero = args.hero or rng.choice(["Milo", "Nia", "Tess", "Kai"])
    friend = args.friend or rng.choice(["June", "Owen", "Luna", "Rey"])
    adult = args.adult or rng.choice(["Captain", "Aunt", "Uncle", "Guide"])
    return StoryParams(place=place, item=item, device=device, response=response,
                       hero=hero, hero_gender=hero_gender, friend=friend,
                       friend_gender=friend_gender, adult=adult)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.item not in ITEMS or params.device not in DEVICES:
        raise StoryError("(Invalid params: unknown place/item/device.)")
    place, item, device = PLACES[params.place], ITEMS[params.item], DEVICES[params.device]
    if not valid_combo(place, item, device):
        raise StoryError(explain_rejection(place, item, device))
    world = tell(place, item, device, device, params.hero, params.hero_gender,
                 params.friend, params.friend_gender, params.adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(P,I,D) :- place(P), item(I), device(D), adventure_place(P), edible_item(I), sense(D,S), sense_min(M), S >= M.
spill :- chosen_device(D), shake(D), too_fast(D).
friendship :- spill, helper_friend.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("adventure_place", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("edible_item", iid))
    for did, d in DEVICES.items():
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("sense", did, d.sense))
        lines.append(asp.fact("power", did, d.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with nectarine and shaker.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--response", choices=["fix"])
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["boy", "girl"])
    ap.add_argument("--adult")
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
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
