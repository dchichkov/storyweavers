#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/intense_sharing_friendship_transformation_mystery.py
====================================================================================

A standalone story world for a tiny mystery about intense feelings, sharing,
friendship, and a quiet transformation.

Premise:
- Two children notice a strange, intense mystery in a small shared place.
- One child wants to keep a found object private; the other wants to share.
- A small clue, a kind choice, and a careful reveal turn suspicion into trust.
- The ending shows that sharing transformed the mood and the friendship.

This script follows the Storyweavers contract:
- self-contained stdlib
- imports storyworlds/results.py eagerly
- provides StoryParams, registries, build_parser, resolve_params, generate,
  emit, main
- supports --all, --seed, -n, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and an inline ASP twin
- uses simulated world state to drive story and QA
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    dark: str
    clue_spot: str
    shared: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MysteryObject:
    id: str
    label: str
    phrase: str
    found_where: str
    clue: str
    value: int
    shares_well: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareChoice:
    id: str
    sense: int
    warmth: int
    text: str
    reveal: str
    lesson: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    if world.get("riddle").meters["mystery"] < THRESHOLD:
        return out
    sig = ("tension",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.characters():
        e.memes["worry"] += 1
    out.append("__tension__")
    return out


def _r_share_soften(world: World) -> list[str]:
    out: list[str] = []
    if world.get("gift").meters["shared"] < THRESHOLD:
        return out
    sig = ("soften",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.characters():
        e.memes["trust"] += 1
        e.memes["warmth"] += 1
    out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("tension", "social", _r_tension), Rule("soften", "social", _r_share_soften)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            ss = rule.apply(world)
            if ss:
                changed = True
                produced.extend(s for s in ss if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness(place: Place, obj: MysteryObject, choice: ShareChoice) -> bool:
    return obj.shares_well and choice.sense >= SENSE_MIN and "mystery" in place.tags


def clue_prediction(world: World, obj: MysteryObject) -> dict:
    sim = world.copy()
    sim.get("gift").meters["shared"] += 1
    propagate(sim, narrate=False)
    return {
        "softened": sim.get("gift").meters["shared"] >= THRESHOLD,
        "trust": sim.get("friend").memes["trust"] + 1,
    }


def setup(world: World, a: Entity, b: Entity, place: Place, obj: MysteryObject) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"On an intense evening, {a.id} and {b.id} crept into {place.label}, where "
        f"{place.dark} made every sound feel like a clue."
    )
    world.say(
        f"Near {place.clue_spot}, they found {obj.phrase}. {obj.clue}"
    )


def wonder(world: World, a: Entity, b: Entity, obj: MysteryObject) -> None:
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    world.say(
        f"{a.id} whispered that the find felt strange and important. "
        f"{b.id} leaned closer, wondering if the mystery wanted to be solved."
    )


def want_keep(world: World, a: Entity, obj: MysteryObject) -> None:
    a.memes["possession"] += 1
    world.say(
        f'"It is mine," {a.id} said, holding the {obj.label} tight. '
        f'The idea of sharing seemed too hard in that moment.'
    )


def urge_share(world: World, b: Entity, a: Entity, obj: MysteryObject) -> None:
    b.memes["kindness"] += 1
    world.say(
        f'"Let us share it," {b.id} said softly. "Mysteries get clearer when '
        f'we look together."'
    )
    world.say(
        f"{a.id} looked down, still unsure, but the invitation stayed in the air."
    )


def reveal(world: World, a: Entity, b: Entity, obj: MysteryObject, choice: ShareChoice) -> None:
    world.get("gift").meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last, {a.id} opened {obj.label_word if hasattr(obj, 'label_word') else 'the thing'}"
    )
    world.say(
        f"{b.id} gasped, and the truth was simple: {choice.text.replace('{object}', obj.label)}."
    )


def transform(world: World, a: Entity, b: Entity, obj: MysteryObject, choice: ShareChoice) -> None:
    a.memes["trust"] += 2
    b.memes["trust"] += 2
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.get("room").meters["mystery"] = 0
    world.say(
        f"They shared the {obj.label}, and the little secret changed shape. "
        f"It was not scary anymore; it became a story they could carry together."
    )
    world.say(
        f"{a.id} and {b.id} smiled at each other, and their friendship felt "
        f"new and stronger, like a lamp switched on in a dark room."
    )
    world.say(
        f"By the end, even the room seemed different: the intense hush had turned "
        f"into calm light."
    )


def tell(place: Place, obj: MysteryObject, choice: ShareChoice,
         a_name: str = "Mila", a_type: str = "girl",
         b_name: str = "Jonah", b_type: str = "boy") -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_type, role="main"))
    b = world.add(Entity(id=b_name, kind="character", type=b_type, role="friend"))
    room = world.add(Entity(id="room", type="room", label=place.label))
    riddle = world.add(Entity(id="riddle", type="thing", label=obj.label))
    gift = world.add(Entity(id="gift", type="thing", label=obj.label))
    gift.meters["shared"] = 0
    room.meters["mystery"] = 1
    riddle.meters["mystery"] = 1

    setup(world, a, b, place, obj)
    world.para()
    wonder(world, a, b, obj)
    want_keep(world, a, obj)
    urge_share(world, b, a, obj)
    if not reasonableness(place, obj, choice):
        raise StoryError("(No story: this mystery setup does not support a sensible sharing turn.)")
    world.para()
    reveal(world, a, b, obj, choice)
    transform(world, a, b, obj, choice)

    world.facts.update(
        hero=a, friend=b, place=place, object_cfg=obj, choice=choice,
        outcome="shared", room=room, gift=gift, riddle=riddle
    )
    return world


PLACES = {
    "attic": Place("attic", "the attic", "the dark rafters", "an old trunk", "shared dust", {"mystery"}),
    "garden": Place("garden", "the garden", "the hush behind the bushes", "a stone bench", "shared leaves", {"mystery"}),
    "hall": Place("hall", "the old hall", "the echoing hallway", "a long mirror", "shared whispers", {"mystery"}),
}

OBJECTS = {
    "box": MysteryObject("box", "box", "a tiny brass box", "under the bench", "A faint click came from inside.", 3, True, {"box", "mystery"}),
    "shell": MysteryObject("shell", "shell", "a smooth white shell", "near the roots", "It felt warm, like it had a secret song.", 2, True, {"shell", "mystery"}),
    "key": MysteryObject("key", "key", "a little silver key", "beside the trunk", "It had a ribbon tied around it, as if someone wanted it found.", 4, True, {"key", "mystery"}),
}

CHOICES = {
    "share": ShareChoice("share", 3, 3,
                         "decided to open the {object} together and see what it held",
                         "the mystery became a shared clue instead of a secret",
                         "sharing turned worry into trust",
                         {"share", "friendship", "transformation"}),
    "show": ShareChoice("show", 2, 2,
                        "held the {object} out so the friend could look too",
                        "the object looked kinder once both children could see it",
                        "showing made the friendship brighter",
                        {"show", "friendship", "transformation"}),
    "divide": ShareChoice("divide", 2, 2,
                          "split the {object}'s clues between them and solved it together",
                          "the clues fit together like two halves of one map",
                          "working together transformed the mystery",
                          {"divide", "friendship", "transformation"}),
}

GIRLS = ["Mila", "Nina", "Lena", "Sara", "Ivy", "Rosa"]
BOYS = ["Jonah", "Theo", "Evan", "Omar", "Noah", "Luca"]
TRAITS = ["curious", "gentle", "intense", "careful", "kind"]


@dataclass
class StoryParams:
    place: str
    object: str
    choice: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for o in OBJECTS:
            for c in CHOICES:
                if reasonableness(PLACES[p], OBJECTS[o], CHOICES[c]):
                    out.append((p, o, c))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world about intense sharing and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.object is None or c[1] == args.object)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, choice = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRLS if hero_gender == "girl" else BOYS)
    friend = args.friend or rng.choice([n for n in (GIRLS if friend_gender == "girl" else BOYS) if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, obj, choice, hero, hero_gender, friend, friend_gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that uses the word "intense" and shows '
        f'how sharing can transform friendship in {f["place"].label}.',
        f"Tell a gentle mystery where {f['hero'].id} and {f['friend'].id} find a clue and "
        f"learn that sharing it makes the friendship stronger.",
        f'Write a story about a strange little object, a careful reveal, and a warm ending '
        f'where a friendship changes because the children share.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["hero"], f["friend"]
    place = f["place"]
    obj = f["object_cfg"]
    choice = f["choice"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.id} and {b.id}, two friends who find a mystery in {place.label}. The story follows how they handle the clue together."
        ),
        QAItem(
            question=f"Why was the moment intense?",
            answer=f"The moment felt intense because the children found something strange and did not know what it meant at first. Sharing the clue made the worry shrink and turned the moment calmer."
        ),
        QAItem(
            question="How did the friendship change?",
            answer=f"Their friendship became stronger because they chose {choice.lesson}. They ended up trusting each other more after they shared the mystery."
        ),
        QAItem(
            question=f"What did {a.id} do with the {obj.label}?",
            answer=f"{a.id} first wanted to keep the {obj.label} close, but then {a.id} let {b.id} see it too. That choice let them solve the mystery together."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is sharing?", "Sharing means letting someone else use, see, or enjoy something with you. It often helps people trust each other more."),
        QAItem("What is friendship?", "Friendship is a kind relationship between people who care about each other and help each other."),
        QAItem("What is a mystery?", "A mystery is something that is not understood right away. People look for clues to figure it out."),
        QAItem("What does transformation mean?", "Transformation means something changes into a new form or a new feeling. It can be a big change or a small one."),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "box", "share", "Mila", "girl", "Jonah", "boy", "intense"),
    StoryParams("garden", "shell", "show", "Nina", "girl", "Theo", "boy", "kind"),
    StoryParams("hall", "key", "divide", "Luca", "boy", "Ivy", "girl", "careful"),
]


def outcome_of(params: StoryParams) -> str:
    return "shared" if reasonableness(PLACES[params.place], OBJECTS[params.object], CHOICES[params.choice]) else "invalid"


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], OBJECTS[params.object], CHOICES[params.choice],
                 params.hero, params.hero_gender, params.friend, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(P,O,C) :- place(P), object(O), choice(C), shares_well(O), sense(C,S), sense_min(M), S >= M.
outcome(shared) :- valid(_,_,_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.shares_well:
            lines.append(asp.fact("shares_well", oid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
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
        assert sample.story.strip()
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


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
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
