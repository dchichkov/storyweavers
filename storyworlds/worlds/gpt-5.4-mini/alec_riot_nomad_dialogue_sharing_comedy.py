#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/alec_riot_nomad_dialogue_sharing_comedy.py
=========================================================================

A standalone storyworld about three kids -- Alec, Riot, and Nomad -- who meet
at a snack table, bicker a little in funny dialogue, and end up sharing the
good stuff instead of hoarding it.

The world model is small and concrete:
- typed entities with physical meters and emotional memes
- a tiny forward rule engine
- a reasonableness gate
- an inline ASP twin
- story-grounded QA generated from world state, not by parsing English

The vibe is comedy: quick dialogue, a silly misunderstanding, and a cheerful
ending image that proves the sharing changed the room.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    props: str
    comedic: str
    share_spot: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    shared: str
    tempting: str
    small: bool = False
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    host = world.get("host")
    bowl = world.get("bowl")
    if host.meters["sharing"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if bowl.meters["full"] >= THRESHOLD:
        bowl.meters["full"] -= 1
        for kid in world.characters():
            kid.memes["joy"] += 1
        out.append("__share__")
    return out


def _r_unclench(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.memes["share_hunger"] < THRESHOLD:
            continue
        sig = ("unclench", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["greed"] = max(0.0, kid.memes["greed"] - 1)
        out.append(f"{kid.id} stopped staring at the bowl like it owed {kid.pronoun('object')} rent.")
    return out


CAUSAL_RULES = [Rule("share", "social", _r_share), Rule("unclench", "social", _r_unclench)]


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


def reasonable_item(item: Item) -> bool:
    return item.small or item.shared == "yes"


def reasonable_combo(setting: Setting, item: Item) -> bool:
    return reasonable_item(item) and setting.id in {"picnic", "plaza", "porch"}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            if reasonable_combo(setting, item):
                combos.append((sid, iid))
    return combos


def _do_take(world: World, kid: Entity, item: Entity) -> None:
    kid.memes["want"] += 1
    item.meters["held"] += 1


def predict_share(world: World) -> dict:
    sim = world.copy()
    host = sim.get("host")
    bowl = sim.get("bowl")
    host.meters["sharing"] = 1
    propagate(sim, narrate=False)
    return {"shared": bowl.meters["full"] < 2, "joy": sum(k.memes["joy"] for k in sim.characters())}


def setup(world: World, alec: Entity, riot: Entity, nomad: Entity) -> None:
    world.say(
        f"On a bright day at the {world.setting.place}, {alec.id}, {riot.id}, "
        f"and {nomad.id} gathered around the snack table. {world.setting.props}"
    )
    world.say(
        f'{alec.id} grinned. "Welcome to our very serious comedy club," '
        f'{alec.id} said, and {riot.id} snorted because that sounded too official.'
    )
    world.say(
        f'{nomad.id} peeked at the snacks. "I have crossed many roads," '
        f'{nomad.id} said, "and I have learned that the best road is the one that leads to crackers."'
    )


def tease(world: World, riot: Entity, bowl: Entity, item: Item) -> None:
    riot.memes["greed"] += 1
    riot.memes["share_hunger"] += 1
    world.say(
        f'{riot.id} pointed at the bowl. "{item.label}? That is clearly mine now," '
        f'{riot.id} announced.'
    )
    world.say(
        f'{alec_id(world)} blinked. "Your name is not written on the bowl," '
        f'{alec_id(world)} said. "Only on your shoes, somehow."'
    )


def alec_id(world: World) -> str:
    return world.get("alec").id


def warn(world: World, nomad: Entity, riot: Entity, bowl: Entity, item: Item) -> None:
    nomad.memes["wisdom"] += 1
    pred = predict_share(world)
    world.facts["predicted_shared"] = pred["shared"]
    world.say(
        f'"If you keep guarding the bowl," {nomad.id} said, '
        f'"it will become a very lonely bowl. Even bowls deserve friends."'
    )
    world.say(
        f'{nomad.id} tapped the rim. "Also, I have seen {item.label} disappear '
        f'into pockets before. Pockets are sneaky."'
    )


def comedy_mixup(world: World, alec: Entity, riot: Entity, nomad: Entity, bowl: Entity) -> None:
    world.say(
        f'{alec.id} lifted the spoon like a tiny conductor. "Ladies and gentlemen, '
        f'we are now opening the snack symphony."'
    )
    world.say(
        f'{riot.id} gasped. "I knew the snacks were famous!"'
    )
    world.say(
        f'{nomad.id} said, "No, friend. He means we are all getting a turn."'
    )


def share_turn(world: World, host: Entity, bowl: Entity, item: Item) -> None:
    host.memes["sharing"] += 1
    bowl.meters["full"] = max(0.0, bowl.meters["full"] - 1)
    propagate(world, narrate=False)
    world.say(
        f'{host.id} laughed. "Fine. One cracker for the hungry, one for the '
        f'curious, and one for the very dramatic."'
    )
    world.say(
        f'{host.id} passed the bowl around the table. '
        f'{item.shared.capitalize()} snacks moved from hand to hand instead of hiding in one lap.'
    )


def ending(world: World, alec: Entity, riot: Entity, nomad: Entity, bowl: Entity, item: Item) -> None:
    for kid in (alec, riot, nomad):
        kid.memes["joy"] += 1
        kid.memes["calm"] += 1
    world.say(
        f'By the end, {riot.id} was laughing, {nomad.id} had crumbs on {nomad.pronoun("possessive")} chin, '
        f'and {alec.id} was holding the last {item.label} up like a prize from a very polite treasure hunt.'
    )
    world.say(
        f'The bowl stayed in the middle of the {world.setting.share_spot}, and nobody needed to guard it anymore.'
    )


def tell(setting: Setting, item: Item, host_name: str = "Alec") -> World:
    world = World(setting)
    alec = world.add(Entity("alec", kind="character", type="boy", role="host"))
    riot = world.add(Entity("riot", kind="character", type="boy", role="guest"))
    nomad = world.add(Entity("nomad", kind="character", type="boy", role="guest"))
    bowl = world.add(Entity("bowl", label=item.label, kind="thing"))
    bowl.meters["full"] = 2
    _ = host_name
    setup(world, alec, riot, nomad)
    world.para()
    tease(world, riot, bowl, item)
    warn(world, nomad, riot, bowl, item)
    comedy_mixup(world, alec, riot, nomad, bowl)
    world.para()
    share_turn(world, alec, bowl, item)
    ending(world, alec, riot, nomad, bowl, item)
    world.facts.update(alec=alec, riot=riot, nomad=nomad, bowl=bowl, item=item, setting=setting)
    return world


SETTINGS = {
    "picnic": Setting("picnic", "the picnic blanket", "A little basket sat on the blanket beside a paper cup tower.", "The wind kept trying to steal napkins for applause.", "center of the blanket"),
    "plaza": Setting("plaza", "the town plaza", "A snack cart stood under a striped awning, looking important.", "A pigeon marched like it owned the square.", "middle of the table"),
    "porch": Setting("porch", "the front porch", "A bowl of crackers sat beside two wobbly lemonades.", "The porch swing creaked like it was telling jokes too.", "middle of the porch"),
}

ITEMS = {
    "crackers": Item("crackers", "crackers", "a bowl of crackers", "yes", "tempting crumbs", small=True, tags={"food", "sharing"}),
    "grapes": Item("grapes", "grapes", "a bunch of grapes", "yes", "tempting fruit", small=True, tags={"food", "sharing"}),
    "cookies": Item("cookies", "cookies", "a plate of cookies", "yes", "tempting sweets", small=True, plural=True, tags={"food", "sharing"}),
}

NAMES = ["Alec", "Riot", "Nomad", "Mina", "Pip", "June"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    setting = f["setting"]
    return [
        f"Write a funny story about alec, riot, and nomad sharing {item.label} at {setting.place}.",
        f"Tell a comedy with dialogue where alec invites riot and nomad to share {item.phrase} instead of hoarding it.",
        f"Write a child-friendly sharing story that includes the words alec, riot, and nomad and ends with everyone laughing together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item = f["item"]
    setting = f["setting"]
    qa = [
        ("Who are the story about?", "The story is about Alec, Riot, and Nomad. They meet at the snack table and try to figure out what to do with the food."),
        ("What did they want to do with the snacks?", f"They wanted to handle {item.label} at first, but the argument turned into a sharing game. In the end, they passed the bowl around instead of keeping it all in one place."),
        ("How did the story end?", f"It ended with the snacks being shared at {setting.share_spot}. The bowl stayed in the middle, and everyone was laughing."),
    ]
    if f["bowl"].meters["full"] < 2:
        qa.append(("What changed during the story?", "The snacks stopped feeling like one kid's private treasure and became something everyone could enjoy. That change made the table calmer and much funnier."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does sharing mean?", "Sharing means letting other people have some of what you have. It is a kind way to make sure everyone gets a turn."),
        ("Why do snacks need to be shared?", "Snacks can be shared so everyone at the table gets something and nobody feels left out. Sharing also makes group time more fun."),
        ("What is a dialogue?", "Dialogue is when characters talk to each other in a story. It helps the reader hear their voices and their feelings."),
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
    for e in list(world.entities.values()):
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


CURATED = [
    StoryParams("picnic", "crackers"),
    StoryParams("plaza", "grapes"),
    StoryParams("porch", "cookies"),
]


def valid_outcome(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.item in ITEMS and reasonable_combo(SETTINGS[params.setting], ITEMS[params.item])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos() if (args.setting is None or c[0] == args.setting) and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item = rng.choice(sorted(combos))
    return StoryParams(setting, item)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, iid) for sid in SETTINGS for iid in ITEMS if reasonable_combo(SETTINGS[sid], ITEMS[iid])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world about alec, riot, and nomad sharing snacks.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
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


ASP_RULES = r"""
shared :- host_shares.
valid(S, I) :- setting(S), item(I), reasonable(S, I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("reasonable", sid, "crackers"))
        lines.append(asp.fact("reasonable", sid, "grapes"))
        lines.append(asp.fact("reasonable", sid, "cookies"))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.to_json()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    else:
        print("OK: generate/serialize smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
