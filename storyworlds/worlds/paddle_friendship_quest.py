#!/usr/bin/env python3
"""
storyworlds/worlds/paddle_friendship_quest.py
=============================================

A standalone story world for the seed:

    Words: paddle
    Features: Conflict, Friendship, Quest
    Style: Heartwarming

The tiny domain is a child and a friend on a creek quest.  A desired object is
on the far side, the boat can only move if the chosen paddle can handle the
water, and the story is refused when the "fix" does not actually help.  Physical
meters (drift, distance, current) and emotional memes (worry, conflict,
friendship, trust) accumulate on entities and drive both the prose and Q&A.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    carried_by: str = ""
    reach: int = 0
    power: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    id: str
    name: str
    water: str
    launch: str
    current: int
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    target: str
    far_side: str
    clue: str
    reward: str
    need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Paddle:
    id: str
    label: str
    phrase: str
    reach: int
    strength: int
    style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Friend:
    id: str
    gender: str
    trait: str
    help_style: str


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_drift(world: World) -> list[str]:
    boat = world.entities.get("boat")
    paddle = world.entities.get("paddle")
    if not boat or not paddle:
        return []
    if boat.meters["launched"] < THRESHOLD:
        return []
    if paddle.power >= world.place.current:
        return []
    sig = ("drift", boat.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["drift"] += 1
    for c in world.characters():
        c.memes["worry"] += 1
    return ["__drift__"]


def _r_cross(world: World) -> list[str]:
    boat = world.entities.get("boat")
    paddle = world.entities.get("paddle")
    quest = world.entities.get("quest")
    if not boat or not paddle or not quest:
        return []
    if boat.meters["launched"] < THRESHOLD:
        return []
    if paddle.power < world.place.current or paddle.reach < quest.reach:
        return []
    sig = ("cross", boat.id, quest.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["crossed"] += 1
    quest.meters["found"] += 1
    for c in world.characters():
        c.memes["joy"] += 1
    return ["__cross__"]


def _r_friendship(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return []
    if hero.memes["accepted_help"] < THRESHOLD or friend.memes["offered_help"] < THRESHOLD:
        return []
    sig = ("friendship", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    hero.memes["conflict"] = 0.0
    friend.memes["conflict"] = 0.0
    return ["__friendship__"]


CAUSAL_RULES = [
    Rule("drift", "physical", _r_drift),
    Rule("cross", "physical", _r_cross),
    Rule("friendship", "social", _r_friendship),
]


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


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
        for sent in produced:
            world.say(sent)
    return produced


def paddle_reaches(quest: Quest, paddle: Paddle) -> bool:
    return paddle.reach >= REQUIRED_REACH[quest.need]


def paddle_strong_enough(place: Place, paddle: Paddle) -> bool:
    return paddle.strength >= place.current


def compatible(place: Place, quest: Quest, paddle: Paddle) -> bool:
    return quest.id in place.affords and paddle_reaches(quest, paddle) and paddle_strong_enough(place, paddle)


def predict_crossing(world: World, paddle: Paddle, quest: Quest) -> dict:
    sim = world.copy()
    sim.add(Entity("paddle", type="paddle", label=paddle.label, reach=paddle.reach, power=paddle.strength))
    _launch(sim, narrate=False)
    boat = sim.get("boat")
    target = sim.get("quest")
    return {
        "crossed": boat.meters["crossed"] >= THRESHOLD,
        "drift": boat.meters["drift"] >= THRESHOLD,
        "found": target.meters["found"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"Once upon a time, there was {article(hero.traits[0])} {hero.traits[0]} {hero.type} named {hero.id}. "
        f"{hero.pronoun().capitalize()} had a {friend.traits[0]} friend named {friend.id}."
    )


def hear_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["quest"] += 1
    world.say(
        f"One bright morning, {hero.id} found a crinkly map that showed {quest.target} "
        f"near {quest.far_side}. The map promised {quest.reward}."
    )


def arrive(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} and {friend.id} hurried to {world.place.name}, where {world.place.water} "
        f"curled past {world.place.launch}."
    )


def argue(world: World, hero: Entity, friend: Entity, quest: Quest, paddle: Paddle) -> None:
    pred = predict_crossing(world, paddle, quest)
    world.facts["prediction"] = pred
    hero.memes["stubborn"] += 1
    friend.memes["caution"] += 1
    if pred["crossed"]:
        warning = "the paddle is right, but one of us still needs to watch the water"
    elif pred["drift"]:
        warning = "the current will spin us before we reach the far bank"
    else:
        warning = f"it cannot reach {quest.far_side}"
    world.say(
        f'{hero.id} grabbed {paddle.phrase}. "I can paddle there myself," '
        f'{hero.pronoun()} said. {friend.id} touched the boat rope. '
        f'"Wait," {friend.pronoun()} said, "{warning}."'
    )
    hero.memes["conflict"] += 1
    friend.memes["conflict"] += 1


def offer_help(world: World, hero: Entity, friend: Entity, paddle: Paddle) -> None:
    friend.memes["offered_help"] += 1
    world.say(
        f"{friend.id} did not laugh or walk away. {friend.pronoun().capitalize()} "
        f"offered to sit in front, watch the ripples, and call, \"left, right, left,\" "
        f"while {hero.id} used {paddle.label}."
    )


def accept_help(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["accepted_help"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id}'s cheeks grew warm. Then {hero.pronoun()} nodded and said, "
        f"\"A quest is better with a friend.\""
    )


def _launch(world: World, narrate: bool = True) -> None:
    boat = world.get("boat")
    boat.meters["launched"] += 1
    propagate(world, narrate=narrate)


def cross(world: World, hero: Entity, friend: Entity, quest: Quest, paddle: Paddle) -> None:
    _launch(world, narrate=False)
    boat = world.get("boat")
    if boat.meters["crossed"] >= THRESHOLD:
        world.say(
            f"Together they pushed off. {hero.id} dipped {paddle.label} into the water, "
            f"and {friend.id} counted the strokes until the boat slid safely to {quest.far_side}."
        )
    else:
        world.say(f"The boat wobbled, and the quest had to wait.")


def finish(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    qent = world.get("quest")
    if qent.meters["found"] >= THRESHOLD and hero.memes["friendship"] >= THRESHOLD:
        world.say(
            f"Behind a bent reed they found {quest.target}. Inside was {quest.reward}. "
            f"{hero.id} shared it with {friend.id}, and their friendship felt bigger "
            f"than the whole creek."
        )


def tell(place: Place, quest: Quest, paddle: Paddle, hero_name: str,
         hero_gender: str, friend_cfg: Friend, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity("hero", kind="character", type=hero_gender,
                            label=hero_name, traits=[trait], role="hero"))
    hero.id = hero_name
    world.entities["hero"] = hero
    friend = world.add(Entity("friend", kind="character", type=friend_cfg.gender,
                              label=friend_cfg.id, traits=[friend_cfg.trait], role="friend"))
    friend.id = friend_cfg.id
    world.entities["friend"] = friend
    world.add(Entity("boat", type="boat", label="the little boat"))
    world.add(Entity("quest", type="quest", label=quest.target, reach=REQUIRED_REACH[quest.need]))
    world.add(Entity("paddle", type="paddle", label=paddle.label, reach=paddle.reach, power=paddle.strength))

    introduce(world, hero, friend)
    hear_quest(world, hero, quest)
    world.para()
    arrive(world, hero, friend)
    argue(world, hero, friend, quest, paddle)
    world.para()
    offer_help(world, hero, friend, paddle)
    accept_help(world, hero, friend)
    cross(world, hero, friend, quest, paddle)
    finish(world, hero, friend, quest)
    world.facts.update(hero=hero, friend=friend, place=place, quest=quest, paddle=paddle,
                       crossed=world.get("boat").meters["crossed"] >= THRESHOLD,
                       found=world.get("quest").meters["found"] >= THRESHOLD,
                       friendship=hero.memes["friendship"] >= THRESHOLD)
    return world


PLACES = {
    "meadow_creek": Place("meadow_creek", "Meadow Creek", "a gentle creek", "a mossy bank", 1,
                          {"lost_ribbon", "bell_island"}, {"creek", "current"}),
    "willow_bend": Place("willow_bend", "Willow Bend", "a quick green stream", "a willow root", 2,
                         {"lost_ribbon", "lantern_cove"}, {"creek", "current"}),
    "wide_pond": Place("wide_pond", "the wide pond", "still pond water", "a flat stone", 1,
                       {"bell_island", "frog_note"}, {"pond"}),
    "rocky_run": Place("rocky_run", "Rocky Run", "a fast narrow run", "a gravel shore", 3,
                       {"lantern_cove"}, {"creek", "current"}),
}

QUESTS = {
    "lost_ribbon": Quest("lost_ribbon", "Grandma's blue ribbon", "the far bank",
                         "a blue loop on the map", "a hug and a tiny silver button",
                         "bank", {"map", "quest"}),
    "bell_island": Quest("bell_island", "the tiny wishing bell", "the little island",
                         "three drawn reeds", "a bell that rang like laughter",
                         "island", {"map", "bell"}),
    "lantern_cove": Quest("lantern_cove", "the lost paper lantern", "Lantern Cove",
                          "a star beside the cove", "a lantern they could hang at home",
                          "cove", {"map", "lantern"}),
    "frog_note": Quest("frog_note", "a note from the pond keeper", "the lily-pad dock",
                       "a green smudge", "a thank-you note with a painted frog",
                       "dock", {"map", "pond"}),
}

REQUIRED_REACH = {"bank": 1, "island": 2, "cove": 3, "dock": 2}

PADDLES = {
    "short_paddle": Paddle("short_paddle", "the short paddle", "a short wooden paddle", 1, 1,
                           "quick little strokes", {"paddle"}),
    "long_paddle": Paddle("long_paddle", "the long paddle", "a long smooth paddle", 2, 2,
                          "steady strokes", {"paddle"}),
    "sturdy_paddle": Paddle("sturdy_paddle", "the sturdy paddle", "a sturdy red paddle", 3, 3,
                            "deep strong strokes", {"paddle"}),
    "toy_paddle": Paddle("toy_paddle", "the toy paddle", "a tiny toy paddle", 0, 0,
                         "pretend strokes", {"paddle"}),
}

FRIENDS = {
    "Mia": Friend("Mia", "girl", "patient", "counts the strokes"),
    "Tom": Friend("Tom", "boy", "kind", "watches the ripples"),
    "Nora": Friend("Nora", "girl", "brave", "holds the rope"),
    "Eli": Friend("Eli", "boy", "gentle", "keeps the map dry"),
}
GIRL_NAMES = ["Lily", "Ava", "Zoe", "Ella", "Rose"]
BOY_NAMES = ["Sam", "Ben", "Leo", "Finn", "Theo"]
TRAITS = ["eager", "curious", "hopeful", "bold", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for qid, quest in QUESTS.items():
            for pad_id, paddle in PADDLES.items():
                if compatible(place, quest, paddle):
                    out.append((pid, qid, pad_id))
    return sorted(out)


@dataclass
class StoryParams:
    place: str
    quest: str
    paddle: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "paddle": [("What is a paddle?",
                "A paddle is a tool with a broad end that pushes against water. People use it to move small boats.")],
    "creek": [("What is a creek?",
               "A creek is a small stream of water. It can be gentle or quick depending on the rain and slope.")],
    "current": [("What is a current?",
                 "A current is water moving in one direction. A strong current can push a boat sideways.")],
    "map": [("Why do people use maps on a quest?",
             "A map helps people see where to go. It can show paths, water, and places to look.")],
    "friendship": [("Why is teamwork helpful?",
                    "Teamwork lets friends share jobs and notice different things. That can make a hard task safer and kinder.")],
}
KNOWLEDGE_ORDER = ["paddle", "creek", "current", "map", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, quest, paddle = f["hero"], f["friend"], f["quest"], f["paddle"]
    return [
        f'Write a heartwarming quest story for young children that includes the word "paddle".',
        f"Tell a story where {hero.id} and {friend.id} have a conflict during a creek quest, "
        f"then use {paddle.label} and friendship to find {quest.target}.",
        "Write a simple adventure about learning that a quest is better when friends help each other.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, place, quest, paddle = f["hero"], f["friend"], f["place"], f["quest"], f["paddle"]
    pred = f.get("prediction", {})
    why = f"even with {paddle.label}, one friend needed to paddle while the other watched the water"
    if pred.get("drift"):
        why = f"{paddle.label} was not strong enough for the current at {place.name}"
    elif not pred.get("crossed"):
        why = f"{paddle.label} could not reach {quest.far_side}"
    return [
        ("Who went on the quest?",
         f"{hero.id} and {friend.id} went on the quest together. They were friends, even though they argued for a moment."),
        ("What were they trying to find?",
         f"They were trying to find {quest.target}. The map said it was near {quest.far_side}."),
        ("Why did the friends have a conflict?",
         f"{hero.id} wanted to paddle by {hero.pronoun('object')}self, but {friend.id} warned that {why}. The warning came from imagining the crossing before they launched."),
        ("How did friendship help?",
         f"{friend.id} offered help instead of teasing, and {hero.id} accepted it. That cleared the conflict and let them paddle safely together."),
        ("What did they learn?",
         f"They learned that a quest can feel braver and happier when friends share the work."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"friendship"} | set(world.facts["place"].tags) | set(world.facts["quest"].tags) | set(world.facts["paddle"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
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
        if e.reach:
            bits.append(f"reach={e.reach}")
        if e.power:
            bits.append(f"power={e.power}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow_creek", "lost_ribbon", "short_paddle", "Lily", "girl", "Tom", "eager"),
    StoryParams("willow_bend", "lost_ribbon", "long_paddle", "Sam", "boy", "Mia", "curious"),
    StoryParams("wide_pond", "bell_island", "long_paddle", "Ava", "girl", "Eli", "hopeful"),
    StoryParams("rocky_run", "lantern_cove", "sturdy_paddle", "Leo", "boy", "Nora", "bold"),
]


def explain_rejection(place: Place, quest: Quest, paddle: Paddle) -> str:
    if quest.id not in place.affords:
        return f"(No story: {quest.target} is not reachable from {place.name}, so the quest does not belong there.)"
    if not paddle_reaches(quest, paddle):
        return f"(No story: {paddle.label} cannot reach {quest.far_side}; the paddle must fit the quest.)"
    if not paddle_strong_enough(place, paddle):
        return f"(No story: {paddle.label} is too weak for the current at {place.name}; the crossing would drift.)"
    return "(No story: this paddle quest is not compatible.)"


ASP_RULES = r"""
reachable(P,Q) :- affords(P,Q).
reaches(Pad,Q) :- paddle_reach(Pad,R), quest_reach(Q,N), R >= N.
strong(Pad,Place) :- paddle_strength(Pad,S), current(Place,C), S >= C.
valid(Place,Q,Pad) :- place(Place), quest(Q), paddle(Pad),
                      reachable(Place,Q), reaches(Pad,Q), strong(Pad,Place).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("current", pid, place.current))
        for q in sorted(place.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_reach", qid, REQUIRED_REACH[quest.need]))
    for pid, paddle in PADDLES.items():
        lines.append(asp.fact("paddle", pid))
        lines.append(asp.fact("paddle_reach", pid, paddle.reach))
        lines.append(asp.fact("paddle_strength", pid, paddle.strength))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: paddle, friendship, quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--paddle", choices=PADDLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--name")
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
    if args.place and args.quest and args.paddle:
        place, quest, paddle = PLACES[args.place], QUESTS[args.quest], PADDLES[args.paddle]
        if not compatible(place, quest, paddle):
            raise StoryError(explain_rejection(place, quest, paddle))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.paddle is None or c[2] == args.paddle)]
    if not combos:
        raise StoryError("(No valid paddle quest matches the given options.)")
    place, quest, paddle = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(sorted(fid for fid in FRIENDS if fid != name))
    trait = rng.choice(TRAITS)
    return StoryParams(place, quest, paddle, name, gender, friend, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], PADDLES[params.paddle],
                 params.name, params.gender, FRIENDS[params.friend], params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, paddle) combos:\n")
        for place, quest, paddle in combos:
            print(f"  {place:13} {quest:13} {paddle}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name} and {p.friend}: {p.quest} with {p.paddle}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
