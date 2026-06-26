#!/usr/bin/env python3
"""
A standalone storyworld for a tiny adventure tale about bravery, an encore,
and a sudden pop in a bramble patch.

The world is intentionally small and classical:
- a young explorer wants one more encore after a little performance
- a bramble path blocks the way
- a pop startles everyone
- bravery changes the outcome
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "scratches": 0.0, "blocked": 0.0}
        if not self.memes:
            self.memes = {"bravery": 0.0, "joy": 0.0, "worry": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)
    brambley: bool = False
    pop_risk: bool = False


@dataclass
class Challenge:
    id: str
    action: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tag: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.history: list[str] = []
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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_bramble_scrape(world: World) -> list[str]:
    out: list[str] = []
    if not world.place.brambley:
        return out
    for hero in world.characters():
        if hero.meters["moving"] < THRESHOLD:
            continue
        sig = ("scrape", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["scratches"] += 1
        hero.memes["worry"] += 1
        out.append(f"The brambles snagged {hero.id}'s clothes and made the path feel prickly.")
    return out


def _r_pop_startle(world: World) -> list[str]:
    out: list[str] = []
    if not world.place.pop_risk:
        return out
    for hero in world.characters():
        if hero.meters["startled"] < THRESHOLD:
            continue
        sig = ("pop", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["worry"] += 1
        out.append(f"A sharp pop echoed through the clearing and everyone froze for a moment.")
    return out


def _r_bravery_turn(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["bravery"] < THRESHOLD:
            continue
        sig = ("turn", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["joy"] += 1
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
        hero.memes["relief"] += 1
        out.append(f"Bravery steadied {hero.id}, and the fear became something smaller than before.")
    return out


CAUSAL_RULES = [
    Rule("bramble_scrape", _r_bramble_scrape),
    Rule("pop_startle", _r_pop_startle),
    Rule("bravery_turn", _r_bravery_turn),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny adventure world: bravery, encore, and a pop in the brambles.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["girl", "boy"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def select_rng(seed: Optional[int]) -> random.Random:
    return random.Random(seed if seed is not None else random.randrange(2**31))


PLACES = {
    "woodland": Place("the woodland clearing", affords={"encore", "trail"}, brambley=True, pop_risk=True),
    "garden": Place("the garden path", affords={"encore", "trail"}, brambley=True, pop_risk=True),
    "stage": Place("the little stage", affords={"encore"}, brambley=False, pop_risk=True),
    "camp": Place("the campfire circle", affords={"encore", "trail"}, brambley=False, pop_risk=True),
}

CHALLENGES = {
    "encore": Challenge(
        id="encore",
        action="do an encore",
        gerund="doing an encore",
        rush="hurry back for one more song",
        risk="the brambles and the sudden pop could make the crowd scatter",
        keyword="encore",
        tag="performance",
    ),
    "trail": Challenge(
        id="trail",
        action="follow the trail",
        gerund="following the trail",
        rush="dash through the bramble patch",
        risk="the thorny branches could scratch hands and sleeves",
        keyword="bramble",
        tag="exploration",
    ),
}

ITEMS = {
    "cape": Item(
        id="cape",
        label="a soft cape",
        phrase="a soft blue cape",
        region="torso",
        protective=True,
        covers={"torso"},
        guards={"scratches"},
    ),
    "boots": Item(
        id="boots",
        label="sturdy boots",
        phrase="sturdy red boots",
        region="feet",
        protective=True,
        covers={"feet"},
        guards={"scratches"},
        plural=True,
    ),
    "lantern": Item(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern with a warm glow",
        region="hand",
        protective=False,
        covers=set(),
        guards=set(),
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Lena", "Tia", "Zoe"]
BOY_NAMES = ["Arlo", "Finn", "Theo", "Leo", "Eli"]
TRAITS = ["bold", "curious", "cheerful", "steadfast"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    item: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p_id, place in PLACES.items():
        for c_id, chal in CHALLENGES.items():
            if c_id not in place.affords:
                continue
            for i_id, item in ITEMS.items():
                if chal.id == "trail" and not item.protective:
                    continue
                combos.append((p_id, c_id, i_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, challenge, item = rng.choice(sorted(combos))
    role = args.role or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if role == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, item=item, name=name, role=role, trait=trait, seed=args.seed)


def can_guard(challenge: Challenge, item: Item) -> bool:
    if challenge.id == "trail":
        return item.protective and "scratches" in item.guards
    if challenge.id == "encore":
        return item.protective or item.id == "lantern"
    return False


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.brambley:
            lines.append(asp.fact("brambley", pid))
        if p.pop_risk:
            lines.append(asp.fact("pop_risk", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("keyword", cid, c.keyword))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if it.protective:
            lines.append(asp.fact("protective", iid))
        for r in sorted(it.covers):
            lines.append(asp.fact("covers", iid, r))
        for g in sorted(it.guards):
            lines.append(asp.fact("guards", iid, g))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,C,I) :- affords(P,C), challenge(C), item(I), guards(I,"scratches"), C = trail, protective(I).
compatible(P,C,I) :- affords(P,C), challenge(C), item(I), C = encore.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


def setting_line(place: Place, chal: Challenge) -> str:
    if chal.id == "encore":
        return f"The {place.name.removeprefix('the ')} had a little stage where the crowd waited for one more song."
    return f"The {place.name.removeprefix('the ')} was bright, but the bramble patch made the trail tricky."


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    chal = CHALLENGES[params.challenge]
    item_def = ITEMS[params.item]
    world = World(place)

    hero = world.add(Entity(id=params.name, kind="character", type=params.role, traits=[params.trait, "brave"]))
    companion = world.add(Entity(id="Guide", kind="character", type="adult", label="the guide"))
    item = world.add(Entity(
        id=item_def.id,
        type="thing",
        label=item_def.label,
        phrase=item_def.phrase,
        owner=hero.id,
        carried_by=hero.id,
        plural=item_def.plural,
    ))

    world.say(f"{hero.id} was a {params.trait} little {params.role} who loved adventure.")
    world.say(f"{hero.id} also loved the word encore, because one more try always felt exciting.")
    world.say(setting_line(place, chal))
    world.say(f"On that day, {hero.id} wanted to {chal.action}, carrying {item.phrase} for the journey.")

    world.para()
    if chal.id == "encore":
        world.say(f"The plan was simple: {hero.id} would step out again and do an encore for the friends nearby.")
        world.say(f"Then the path crackled, and a sudden pop made the lantern swing and the crowd gasp.")
        hero.meters["startled"] += 1
        propagate(world, narrate=True)
        hero.memes["worry"] += 1
        world.say(f"{hero.id} paused, because the bramble patch looked sharp and the pop still rang in the air.")
    else:
        world.say(f"{hero.id} wanted to follow the trail, even though the bramble patch made the way rough.")
        hero.meters["moving"] += 1
        propagate(world, narrate=True)
        world.say(f"Then a nearby berry burst with a pop, and {hero.id} jumped back for a moment.")

    world.para()
    hero.memes["bravery"] += 1
    propagate(world, narrate=True)
    if item_def.protective:
        world.say(f"{hero.id} held tight to {item.label} and chose the careful path through the brambles.")
    else:
        world.say(f"{hero.id} did not let the pop win. {hero.pronoun().capitalize()} took a breath and kept going.")

    if chal.id == "encore":
        world.say(f"With bravery leading the way, {hero.id} stepped up and did the encore after all.")
        world.say(f"The little stage lit up with cheers, and the pop was only a memory by the end.")
    else:
        world.say(f"With bravery in {hero.pronoun('possessive')} chest, {hero.id} found the trail beyond the bramble patch.")
        world.say(f"The scratches never grew big enough to stop {hero.id}, and the path opened into sunshine.")

    world.facts.update(hero=hero, companion=companion, item=item, item_def=item_def, challenge=chal, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    chal = f["challenge"]
    place = f["place"]
    return [
        f'Write a short adventure story for young children about {hero.id}, the word "encore", and a surprise pop.',
        f"Tell a brave little story where {hero.id} tries to {chal.action} at {place.name} and does not give up.",
        f"Write a simple story with the words encore, pop, and bramble, ending in a brave choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    chal = f["challenge"]
    place = f["place"]
    item = f["item"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.name}?",
            answer=f"{hero.id} wanted to {chal.action}, and {item.label} was part of the adventure.",
        ),
        QAItem(
            question=f"Why was the path hard for {hero.id}?",
            answer=f"The path was hard because the brambles were prickly and a pop startled everyone.",
        ),
        QAItem(
            question=f"How did {hero.id} finish the story?",
            answer=f"{hero.id} finished with bravery, kept going, and the adventure ended happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bramble?",
            answer="A bramble is a thorny plant with prickly branches that can scratch clothing and skin.",
        ),
        QAItem(
            question="What is an encore?",
            answer="An encore is one more performance after the first one ends, when the audience wants more.",
        ),
        QAItem(
            question="What does a pop sound like?",
            answer="A pop is a short, sudden sound, like a tiny burst or a balloon breaking.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is the courage to keep going even when something feels scary.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="woodland", challenge="encore", item="cape", name="Mia", role="girl", trait="bold"),
    StoryParams(place="garden", challenge="trail", item="boots", name="Finn", role="boy", trait="curious"),
    StoryParams(place="camp", challenge="encore", item="lantern", name="Tia", role="girl", trait="steadfast"),
]


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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        for c in combos:
            print(c)
        return

    rng = select_rng(args.seed)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            local_rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, local_rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.challenge} at {p.place} with {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
