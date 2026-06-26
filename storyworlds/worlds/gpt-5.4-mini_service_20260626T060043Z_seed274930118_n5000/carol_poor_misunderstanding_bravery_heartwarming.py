#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_service_20260626T060043Z_seed274930118_n5000/carol_poor_misunderstanding_bravery_heartwarming.py
=================================================================================================

A small heartwarming storyworld about Carol, a poor child, and a misunderstanding
that is healed by bravery, kindness, and a shared song.

Premise:
- Carol is a poor child who loves winter carols.
- A notice about the neighborhood carol night is hard to read.
- Carol misunderstands the notice and thinks she is not welcome.
- Carol finds the courage to go anyway.
- The misunderstanding is cleared up, and the night ends warmly.

This script follows the storyworld contract:
- self-contained stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- inline ASP twin and Python reasonableness gate
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    emotional_value: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    tension: str
    turn: str
    resolution: str
    keyword: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = "cold"

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.weather = self.weather
        return clone


@dataclass
class StoryParams:
    setting: str
    event: str
    item: str
    name: str = "Carol"
    seed: Optional[int] = None


SETTINGS = {
    "street": Setting(place="the snowy street", indoors=False, affords={"carol_night"}),
    "hall": Setting(place="the warm community hall", indoors=True, affords={"carol_night"}),
    "porch": Setting(place="the front porch", indoors=False, affords={"carol_night"}),
}

EVENTS = {
    "carol_night": Event(
        id="carol_night",
        verb="sing carols",
        tension="Carol thought the music was for someone else",
        turn="Carol took a brave step toward the lighted door",
        resolution="the leader explained the notice and welcomed her inside",
        keyword="carol",
        tags={"carol", "song", "bravery", "misunderstanding"},
    )
}

ITEMS = {
    "basket": Item(
        id="basket",
        label="bread basket",
        phrase="a small bread basket",
        type="basket",
        emotional_value="comfort",
        tags={"poor", "bread", "sharing"},
    ),
    "scarf": Item(
        id="scarf",
        label="wool scarf",
        phrase="a soft wool scarf",
        type="scarf",
        emotional_value="warmth",
        tags={"cold", "warm"},
    ),
    "lantern": Item(
        id="lantern",
        label="paper lantern",
        phrase="a tiny paper lantern",
        type="lantern",
        emotional_value="hope",
        tags={"light", "bravery"},
    ),
}

PEOPLE = {
    "Carol": {"girl", "kind", "quiet", "brave"},
    "Mina": {"girl", "kind", "gentle", "smiling"},
    "MrBell": {"man", "kind", "patient"},
    "Grandma": {"grandmother", "kind", "warm"},
}

TRAITS = ["kind", "quiet", "brave", "gentle", "small", "thoughtful"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.meters.get("cold", 0) >= THRESHOLD and ("cold", e.id) not in world.fired:
            world.fired.add(("cold", e.id))
            e.memes["worry"] = e.memes.get("worry", 0) + 0.5
            out.append(f"{e.id} tucked {e.pronoun('possessive')} hands closer to {e.pronoun('possessive')} chest.")
    return out


def _r_understood(world: World) -> list[str]:
    out: list[str] = []
    carol = world.entities.get("Carol")
    if not carol:
        return out
    if carol.memes.get("bravery", 0) >= THRESHOLD and carol.memes.get("misunderstanding", 0) >= THRESHOLD:
        sig = ("understood", "Carol")
        if sig in world.fired:
            return out
        world.fired.add(sig)
        carol.memes["understanding"] = carol.memes.get("understanding", 0) + 1
        carol.memes["worry"] = max(0.0, carol.memes.get("worry", 0) - 1)
        out.append("The mistake began to melt away once Carol heard the kind explanation.")
    return out


RULES = [Rule("cold", _r_cold), Rule("understood", _r_understood)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(setting: Setting, event: Event, item: Item) -> bool:
    return setting.affords == {"carol_night"} and event.id == "carol_night" and item.type in {"scarf", "lantern", "basket"}


def aspire(carol: Entity, event: Event) -> None:
    carol.memes["joy"] = carol.memes.get("joy", 0) + 0.5
    carol.memes["love"] = carol.memes.get("love", 0) + 0.5


def predict(world: World) -> dict:
    sim = world.copy()
    carol = sim.get("Carol")
    carol.memes["misunderstanding"] = carol.memes.get("misunderstanding", 0) + 1
    carol.memes["bravery"] = carol.memes.get("bravery", 0) + 1
    propagate(sim, narrate=False)
    return {
        "understood": carol.memes.get("understanding", 0) > 0,
        "worry": carol.memes.get("worry", 0),
    }


def tell(setting: Setting, event: Event, item: Item, name: str = "Carol") -> World:
    world = World(setting)
    world.weather = "cold" if not setting.indoors else "warm"
    carol = world.add(Entity(id=name, kind="character", type="girl"))
    elder = world.add(Entity(id="Grandma", kind="character", type="grandmother"))
    leader = world.add(Entity(id="Mina", kind="character", type="girl"))
    basket = world.add(Entity(id="basket", type=item.type, label=item.label, phrase=item.phrase))
    lantern = world.add(Entity(id="lantern", type="lantern", label="paper lantern", phrase="a tiny paper lantern"))

    carol.meters["cold"] = 1.0 if not setting.indoors else 0.0
    carol.memes["poor"] = 1.0
    carol.memes["worry"] = 1.0
    aspire(carol, event)

    world.say(f"{carol.id} was a poor little girl who loved to {event.verb}.")
    world.say(f"She kept {basket.phrase} close because {basket.label} meant supper could stretch a little farther.")
    world.say(f"On a cold evening, {carol.id} found a notice for carol night by {setting.place}.")
    world.say(f"The writing was smudged, and {carol.id} misunderstood it.")
    world.say(f"She thought the song was only for families with bright coats and full tables.")

    world.para()
    carol.memes["misunderstanding"] = 1.0
    world.say(f"Still, {carol.id} held {lantern.phrase} in {lantern.pronoun('possessive')} hands and took a brave breath.")
    carol.memes["bravery"] = 1.0
    world.say(f"{carol.id} walked to {setting.place} anyway, even though {carol.pronoun('subject')} felt small and shy.")
    world.say(f"That brave step made the doorway seem less scary.")
    propagate(world, narrate=True)

    world.para()
    pred = predict(world)
    world.facts.update(
        carol=carol,
        elder=elder,
        leader=leader,
        basket=basket,
        lantern=lantern,
        event=event,
        item=item,
        setting=setting,
        predicted=pred,
    )
    world.say(f"At the door, {leader.id} smiled and said the notice had only been hard to read.")
    world.say(f"It was an invitation for everyone, especially for neighbors who needed a warm song.")
    carol.memes["understanding"] = 1.0
    carol.memes["joy"] = carol.memes.get("joy", 0) + 1
    carol.memes["worry"] = 0
    world.say(f"{carol.id} felt her cheeks warm, and the misunderstanding disappeared like breath in the cold.")
    world.say(f"Then {carol.id} joined the singing, and the little room turned bright with voices.")

    world.para()
    world.say(f"After the song, the neighbors shared soup, and the bread basket was passed from hand to hand.")
    world.say(f"{carol.id} was still poor, but she was no longer alone.")
    world.say(f"{carol.id} went home with a full heart, {lantern.phrase} glowing softly, and the carol still humming in her head.")

    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for e in EVENTS:
            for i in ITEMS:
                if reasonableness_gate(SETTINGS[s], EVENTS[e], ITEMS[i]):
                    combos.append((s, e, i))
    return combos


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    carol = f["carol"]
    return [
        "Write a heartwarming story about a poor child, a misunderstanding, and a brave choice.",
        f"Tell a gentle story where {carol.id} thinks she is not welcome, but then discovers the truth and feels brave.",
        "Write a child-friendly winter story that includes carol singing, kindness, and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    carol = f["carol"]
    item = f["item"]
    setting = f["setting"]
    event = f["event"]
    qa = [
        QAItem(
            question="Who is the story mainly about?",
            answer=f"The story is mainly about {carol.id}, a poor little girl who was brave enough to go to {setting.place}.",
        ),
        QAItem(
            question="What did Carol misunderstand?",
            answer="Carol misunderstood the notice for carol night. She thought she might not be welcome, but the note was really for everyone.",
        ),
        QAItem(
            question="Why was Carol brave?",
            answer=f"Carol was brave because she went to {setting.place} even while she felt poor, cold, and worried. She wanted to {event.verb} anyway.",
        ),
        QAItem(
            question="What helped Carol feel better at the end?",
            answer="A kind explanation helped Carol understand the mistake, and then the singing and shared soup made the night feel warm.",
        ),
        QAItem(
            question=f"What special thing did Carol carry with her?",
            answer=f"Carol carried {item.phrase}, which helped her feel steady and hopeful on the walk.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone gets the wrong idea about what is happening or what another person means.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something even when you feel scared, worried, or shy.",
        ),
        QAItem(
            question="Why can a warm song help people?",
            answer="A warm song can help people feel closer, calmer, and less lonely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
carol_night_story(S, E, I) :- setting(S), event(E), item(I), valid(S, E, I).
valid(S, E, I) :- carol_night_setting(S), carol_night_event(E), gentle_item(I).

carol_night_setting(street).
carol_night_setting(hall).
carol_night_setting(porch).

carol_night_event(carol_night).

gentle_item(scarf).
gentle_item(lantern).
gentle_item(basket).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for eid, event in EVENTS.items():
        lines.append(asp.fact("event", eid))
        for t in sorted(event.tags):
            lines.append(asp.fact("tag", eid, t))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for t in sorted(item.tags):
            lines.append(asp.fact("tag", iid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show carol_night_story/3."))
    return sorted(set(asp.atoms(model, "carol_night_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about Carol, a misunderstanding, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name", default="Carol")
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.event is None or c[1] == args.event)
        and (args.item is None or c[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, event, item = rng.choice(sorted(combos))
    return StoryParams(setting=setting, event=event, item=item, name=args.name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], EVENTS[params.event], ITEMS[params.item], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
    StoryParams(setting="hall", event="carol_night", item="lantern", name="Carol"),
    StoryParams(setting="porch", event="carol_night", item="scarf", name="Carol"),
    StoryParams(setting="street", event="carol_night", item="basket", name="Carol"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show carol_night_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible stories:\n")
        for s, e, i in triples:
            print(f"  {s:8} {e:12} {i}")
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
            header = f"### {p.name}: {p.setting} / {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
