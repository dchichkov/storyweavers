#!/usr/bin/env python3
"""
A tiny storyworld about a conductor, a curious child, and a shared little treasure.
The prose aims for a nursery-rhyme cadence with a gentle inner monologue and a
clear sharing turn.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "conductor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the station"
    affords: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    treasured: bool = True


@dataclass
class StoryParams:
    setting: str
    gift: str
    child_name: str
    child_type: str
    conductor_name: str
    conductor_type: str = "conductor"
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "station": Setting(place="the station", affords={"sharing"}),
    "car": Setting(place="the train car", affords={"sharing"}),
    "platform": Setting(place="the platform", affords={"sharing"}),
}

GIFTS = {
    "lantern": Gift(id="lantern", label="lantern", phrase="a little brass lantern"),
    "apple": Gift(id="apple", label="apple", phrase="a red sweet apple"),
    "blanket": Gift(id="blanket", label="blanket", phrase="a soft blue blanket"),
    "book": Gift(id="book", label="book", phrase="a tiny picture book"),
}

NAMES = ["Mila", "Nina", "Poppy", "Theo", "Finn", "June", "Luna", "Owen"]
TRAITS = ["curious", "bright-eyed", "gentle", "spry", "cheery"]


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def _share_spreads(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    gift = world.entities.get("gift")
    conductor = world.entities.get("conductor")
    if not child or not gift or not conductor:
        return out
    if child.memes.get("sharing", 0) < THRESHOLD:
        return out
    sig = ("share", gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gift.shared_with.add(child.id)
    gift.shared_with.add(conductor.id)
    conductor.memes["warmth"] = conductor.memes.get("warmth", 0) + 1
    out.append(f"The little {gift.label} passed from hand to hand with a kindly glow.")
    return out


def _curiosity_softens(world: World) -> list[str]:
    child = world.entities.get("child")
    if not child:
        return []
    if child.memes.get("curiosity", 0) < THRESHOLD:
        return []
    sig = ("curious", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    return [f"{child.id} leaned in to see, with a whisper in a wondering mind."]


RULES = [_share_spreads, _curiosity_softens]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rhyme_opening(child: Entity, conductor: Entity, gift: Gift, place: str) -> str:
    return (
        f"At {place}, on a bright, bright day, little {child.id} came to play. "
        f"There stood {conductor.id}, neat and grand, with {gift.phrase} in hand."
    )


def inner_monologue(child: Entity, gift: Gift) -> str:
    return (
        f"{child.id} thought, 'I wonder, wonder, what is it for? "
        f"Will it light the night, or open a door?'"
    )


def check_reasonable(setting: str, gift: str) -> None:
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if gift not in GIFTS:
        raise StoryError("Unknown gift.")
    if "sharing" not in SETTINGS[setting].affords:
        raise StoryError("This setting does not support a sharing story.")


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------

def tell(setting: Setting, gift_def: Gift, child_name: str, child_type: str,
         conductor_name: str, conductor_type: str) -> World:
    world = World(setting)

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        meters={},
        memes={"curiosity": 1.0, "sharing": 0.0, "joy": 0.0},
    ))
    conductor = world.add(Entity(
        id=conductor_name,
        kind="character",
        type=conductor_type,
        label=conductor_name,
        meters={},
        memes={"kindness": 1.0, "joy": 0.0, "warmth": 0.0},
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type=gift_def.id,
        label=gift_def.label,
        phrase=gift_def.phrase,
        owner=conductor.id,
        shared_with=set(),
        meters={},
        memes={"shine": 1.0},
    ))

    world.say(rhyme_opening(child, conductor, gift_def, setting.place))
    world.say(
        f"{child.id} peeped at the {gift.label} and felt a flutter of curiosity. "
        f"{inner_monologue(child, gift_def)}"
    )

    world.para()
    world.say(
        f"{conductor.id} saw the curious face and smiled a kind, kind smile. "
        f"'{gift.phrase} is for sharing,' {conductor.id} said, 'if you wish to stay awhile.'"
    )
    child.memes["curiosity"] += 1
    child.memes["sharing"] += 1
    child.memes["joy"] += 1
    conductor.memes["joy"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"So {child.id} held out small hands, and {conductor.id} shared the treasure too. "
        f"They used it together, side by side, as happy friends often do."
    )
    if gift.label == "lantern":
        world.say("The lantern made a little gold pool on the floor, and both of them laughed softly.")
    elif gift.label == "apple":
        world.say("The apple was crisp and sweet, and they took turns with polite little bites.")
    elif gift.label == "blanket":
        world.say("The blanket was spread between them like a cloud, warm as a hug.")
    else:
        world.say("The picture book opened wide, and they counted colors and stars on every page.")

    world.facts.update(
        child=child,
        conductor=conductor,
        gift=gift,
        setting=setting,
        shared=gift.shared_with,
        curiosity=child.memes["curiosity"] >= THRESHOLD,
        sharing=child.memes["sharing"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    conductor = f["conductor"]
    gift = f["gift"]
    return [
        f"Write a nursery-rhyme story about a conductor named {conductor.id} and a child named {child.id} who share {gift.phrase}.",
        f"Tell a gentle little tale where curiosity helps {child.id} ask about the {gift.label} and the conductor shares it kindly.",
        f"Write a short rhyme with a conductor, sharing, and a wondering child at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    conductor = f["conductor"]
    gift = f["gift"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who was curious about the {gift.label} at {place}?",
            answer=f"{child.id} was curious, and {child.id} kept wondering what the {gift.label} might be for.",
        ),
        QAItem(
            question=f"What did {conductor.id} do when {child.id} looked at the {gift.label}?",
            answer=f"{conductor.id} shared the {gift.label} kindly and let {child.id} enjoy it too.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and {conductor.id}?",
            answer=f"They ended up happy together, using the {gift.label} side by side at {place}.",
        ),
    ]


WORLD_QA = {
    "sharing": [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use, hold, or enjoy something with you.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more.",
        )
    ],
    "inner": [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice of a character thinking to themself.",
        )
    ],
    "conductor": [
        QAItem(
            question="What does a conductor do?",
            answer="A conductor helps guide a train or a group and keeps things orderly and on time.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_QA["sharing"] + WORLD_QA["curiosity"] + WORLD_QA["inner"] + WORLD_QA["conductor"]


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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(station). setting(car). setting(platform).
affords(station,sharing). affords(car,sharing). affords(platform,sharing).

gift(lantern). gift(apple). gift(blanket). gift(book).

reasonable(S,G) :- affords(S,sharing), gift(G).
#show reasonable/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, a))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return set(asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    py = {(s, g) for s in SETTINGS for g in GIFTS if "sharing" in SETTINGS[s].affords}
    cl = asp_reasonable()
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about sharing and curiosity.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--gift", choices=GIFTS.keys())
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--conductor-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    gift = args.gift or rng.choice(list(GIFTS))
    check_reasonable(setting, gift)
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(NAMES)
    conductor_name = args.conductor_name or "Conductor Clem"
    return StoryParams(
        setting=setting,
        gift=gift,
        child_name=child_name,
        child_type=child_type,
        conductor_name=conductor_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        GIFTS[params.gift],
        params.child_name,
        params.child_type,
        params.conductor_name,
        params.conductor_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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
    StoryParams(setting="station", gift="lantern", child_name="Mila", child_type="girl", conductor_name="Conductor Clem"),
    StoryParams(setting="car", gift="apple", child_name="Theo", child_type="boy", conductor_name="Conductor June"),
    StoryParams(setting="platform", gift="blanket", child_name="Luna", child_type="girl", conductor_name="Conductor Bea"),
    StoryParams(setting="station", gift="book", child_name="Finn", child_type="boy", conductor_name="Conductor Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable/2."))
        combos = sorted(set(asp.atoms(model, "reasonable")))
        print(f"{len(combos)} reasonable setting/gift combos:")
        for s, g in combos:
            print(f"  {s:9} {g}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.gift} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
