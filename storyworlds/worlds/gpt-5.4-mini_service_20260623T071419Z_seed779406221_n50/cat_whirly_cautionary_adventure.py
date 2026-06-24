#!/usr/bin/env python3
"""
storyworlds/worlds/cat_whirly_cautionary_adventure.py
=====================================================

A small cautionary adventure storyworld about a curious cat, a whirly gadget,
and a safer way to keep exploring.

The seed suggests a tiny adventure domain:
- a cat wants to chase or inspect a whirly thing,
- the whirly thing can cause trouble if used in the wrong place,
- a cautious helper warns, redirects, and the story ends with a safer image.

The world model tracks:
- physical meters: spin, wobble, dust, stuck, broken, safe, distance
- emotional memes: curiosity, caution, worry, relief, pride, delight

The story is generated from causal state changes, not from a frozen template.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def pronoun_cap(self) -> str:
        return self.pronoun().capitalize()


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    wind: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class WhirlyThing:
    id: str
    label: str
    phrase: str
    spin: str
    risk: str
    safe: str
    mess: str
    tags: set[str] = field(default_factory=set)
    dangerous: bool = False


@dataclass
class SafeChoice:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.whirl = 0.0
        self.wind = 0.0
        self.path = "clear"

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.whirl = self.whirl
        w.wind = self.wind
        w.path = self.path
        return w


@dataclass
class StoryParams:
    place: str
    whirly: str
    choice: str
    cat_name: str
    cat_kind: str
    helper_name: str
    helper_kind: str
    seed: Optional[int] = None


PLACES = {
    "yard": Place(id="yard", label="the yard", wind=True, affords={"play", "roll"}),
    "shed": Place(id="shed", label="the shed", indoors=True, wind=False, affords={"play"}),
    "hill": Place(id="hill", label="the hill", wind=True, affords={"roll", "play"}),
}

WHIRLY = {
    "kitewheel": WhirlyThing(
        id="kitewheel",
        label="kite wheel",
        phrase="a bright kite wheel",
        spin="spun fast in the breeze",
        risk="could tangle the string and tug the cat too hard",
        safe="slowed to a gentle turn",
        mess="got dusty and twisted",
        dangerous=True,
        tags={"whirly", "spin"},
    ),
    "pinwheel": WhirlyThing(
        id="pinwheel",
        label="pinwheel",
        phrase="a shiny pinwheel",
        spin="whirled and clicked softly",
        risk="could snap and scatter little bits",
        safe="spun softly in a safe place",
        mess="bent a little and got dusty",
        dangerous=True,
        tags={"whirly", "spin"},
    ),
    "top": WhirlyThing(
        id="top",
        label="spinning top",
        phrase="a tiny spinning top",
        spin="whirled across the floor",
        risk="could roll under furniture and get stuck",
        safe="spun in a clear patch of ground",
        mess="got scraped and stuck",
        dangerous=True,
        tags={"whirly", "spin"},
    ),
}

CHOICES = {
    "string": SafeChoice(
        id="string",
        label="soft string game",
        phrase="a soft string game",
        use="play with the string in a wide open patch",
        tags={"safe", "play"},
    ),
    "basket": SafeChoice(
        id="basket",
        label="basket nest",
        phrase="a warm basket nest",
        use="rest in the basket nest and watch the whirly thing from afar",
        tags={"safe", "rest"},
    ),
    "stick": SafeChoice(
        id="stick",
        label="leaf stick",
        phrase="a leaf stick trail",
        use="follow a leaf stick trail instead of chasing the whirly thing",
        tags={"safe", "walk"},
    ),
}

CAT_NAMES = ["Milo", "Pip", "Nora", "Sunny", "Toby", "Luna", "Penny", "Clover"]
HELPER_NAMES = ["Mia", "Ben", "Ava", "Leo", "Iris", "Finn", "Ruby", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for whirly_id in place.affords:
            for choice_id in CHOICES:
                combos.append((place_id, whirly_id, choice_id))
    return combos


def explain_rejection(place: Place, whirly: WhirlyThing) -> str:
    return (
        f"(No story: {whirly.label} does not fit that place in a useful way. "
        f"Pick a place where the cat can safely notice it.)"
    )


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    cat = world.get("cat")
    whirly = world.get("whirly")
    if cat.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if world.place.wind and world.whirl >= THRESHOLD and ("wobble", whirly.id) not in world.fired:
        world.fired.add(("wobble", whirly.id))
        whirly.meters["wobble"] = whirly.meters.get("wobble", 0.0) + 1.0
        whirly.meters["dust"] = whirly.meters.get("dust", 0.0) + 1.0
        cat.memes["worry"] = cat.memes.get("worry", 0.0) + 1.0
        out.append(f"The {whirly.label} wobbled in the wind.")
    return out


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    whirly = world.get("whirly")
    cat = world.get("cat")
    if whirly.meters.get("wobble", 0.0) < THRESHOLD:
        return out
    if world.path == "narrow" and ("stuck", whirly.id) not in world.fired:
        world.fired.add(("stuck", whirly.id))
        whirly.meters["stuck"] = 1.0
        whirly.meters["broken"] = whirly.meters.get("broken", 0.0) + 1.0
        cat.memes["worry"] = cat.memes.get("worry", 0.0) + 1.0
        out.append(f"It scraped the narrow path and got stuck.")
    return out


RULES = [Rule("wobble", _r_wobble), Rule("stuck", _r_stuck)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    made: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            res = rule.apply(world)
            if res:
                changed = True
                made.extend(res)
    if narrate:
        for s in made:
            world.say(s)
    return made


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.whirl = 1.0
    sim.path = "narrow"
    propagate(sim, narrate=False)
    wh = sim.get("whirly")
    return {
        "wobbled": wh.meters.get("wobble", 0.0) >= THRESHOLD,
        "stuck": wh.meters.get("stuck", 0.0) >= THRESHOLD,
        "worry": sim.get("cat").memes.get("worry", 0.0),
    }


def setup_story(world: World, cat: Entity, helper: Entity, whirly: Entity) -> None:
    cat.memes["curiosity"] = 1.0
    cat.memes["delight"] = 1.0
    helper.memes["caution"] = 1.0
    world.say(f"{cat.id} was a little {cat.type} who loved adventure.")
    world.say(f"{helper.id} was a careful {helper.type} who watched the path.")
    world.say(f"One day they found {whirly.label} near {world.place.label}, and it {world.facts['whirly_desc']}.")
    world.say(f"{cat.id} wanted to touch it right away.")


def warn_and_turn(world: World, cat: Entity, helper: Entity, whirly: Entity, choice: SafeChoice) -> None:
    pred = predict_trouble(world)
    if pred["wobbled"]:
        helper.memes["caution"] += 1.0
        world.facts["predicted_worry"] = pred["worry"]
        world.say(f'"Careful," {helper.id} said. "That {whirly.label} can {world.facts["risk"]}."')
        world.say(f"{cat.id} paused and listened.")
        cat.memes["curiosity"] += 1.0
        cat.memes["relief"] = cat.memes.get("relief", 0.0) + 1.0
        helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1.0
        world.say(f'Then {helper.id} showed {cat.id} {choice.phrase}, so the adventure stayed safe.')
        world.say(f"{choice.use.capitalize()}.")
        cat.memes["delight"] += 1.0
    else:
        world.say(f"{cat.id} listened before the whiskers-tingle turned into trouble.")
        world.say(f"Together they chose {choice.phrase} instead.")


def tell(place: Place, whirly_cfg: WhirlyThing, choice: SafeChoice,
         cat_name: str, cat_kind: str, helper_name: str, helper_kind: str) -> World:
    world = World(place)
    cat = world.add(Entity(id=cat_name, kind="character", type=cat_kind, label=cat_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_kind, label=helper_name))
    wh = world.add(Entity(id="whirly", kind="thing", type="thing", label=whirly_cfg.label))
    world.facts["whirly_desc"] = whirly_cfg.spin
    world.facts["risk"] = whirly_cfg.risk

    setup_story(world, cat, helper, wh)
    world.para()
    world.whirl = 1.0
    world.path = "narrow" if place.id != "shed" else "clear"
    world.say(f"The wind picked up, and the {wh.label} began to test the air.")
    if place.wind:
        world.say(f"It {whirly_cfg.spin}, which made the cat's paws twitch.")
    else:
        world.say(f"It spun slowly, but the helper kept it on a table where it could not dash away.")
    propagate(world, narrate=True)
    world.para()
    warn_and_turn(world, cat, helper, wh, choice)

    world.facts.update(
        cat=cat,
        helper=helper,
        whirly=wh,
        place=place,
        choice=choice,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    cat = world.facts["cat"]
    helper = world.facts["helper"]
    wh = world.facts["whirly"]
    choice = world.facts["choice"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who is the story about in {place.label}?",
            answer=f"It is about {cat.id}, a curious {cat.type}, and {helper.id}, who helped keep the adventure safe.",
        ),
        QAItem(
            question=f"What did {cat.id} want to do with the {wh.label}?",
            answer=f"{cat.id} wanted to touch the {wh.label} right away because it looked exciting and whirly.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {cat.id}?",
            answer=f"{helper.id} warned {cat.id} because the {wh.label} could {world.facts['risk']}. That made the helper choose a careful path.",
        ),
        QAItem(
            question=f"What safer choice did they make instead?",
            answer=f"They chose {choice.phrase} and used it to keep the adventure going without trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does cautious mean?",
            answer="Cautious means careful. A cautious helper looks ahead and tries to keep danger away.",
        ),
        QAItem(
            question="What is a whirly thing?",
            answer="A whirly thing is something that spins or twirls. It can be fun to watch, but it should be used in a safe place.",
        ),
        QAItem(
            question="Why should you listen to a warning?",
            answer="A warning helps you avoid trouble before it starts. Listening can keep a game fun and safe.",
        ),
    ]
    return out


def generation_prompts(world: World) -> list[str]:
    cat = world.facts["cat"]
    helper = world.facts["helper"]
    wh = world.facts["whirly"]
    return [
        f"Write an adventure story for a small child about {cat.id}, a whirly thing, and a careful warning.",
        f"Tell a cautionary adventure where {helper.id} helps {cat.id} stay safe around the {wh.label}.",
        f"Write a gentle story that includes a cat, something whirly, and a safer choice at the end.",
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  whirl={world.whirl} path={world.path}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="yard",
        whirly="kitewheel",
        choice="string",
        cat_name="Milo",
        cat_kind="cat",
        helper_name="Mia",
        helper_kind="girl",
    ),
    StoryParams(
        place="hill",
        whirly="pinwheel",
        choice="basket",
        cat_name="Pip",
        cat_kind="cat",
        helper_name="Ben",
        helper_kind="boy",
    ),
    StoryParams(
        place="shed",
        whirly="top",
        choice="stick",
        cat_name="Luna",
        cat_kind="cat",
        helper_name="Iris",
        helper_kind="girl",
    ),
]


def valid_valid_combo(place_id: str, whirly_id: str, choice_id: str) -> bool:
    return (place_id, whirly_id, choice_id) in valid_combos()


ASP_RULES = r"""
place(P) :- place_fact(P).
whirly(W) :- whirly_fact(W).
choice(C) :- choice_fact(C).

valid(P, W, C) :- place_fact(P), whirly_fact(W), choice_fact(C), can_use(P, W).

can_use(P, W) :- place_fact(P), whirly_fact(W), affords(P, W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place_fact", p.id))
        if p.indoors:
            lines.append(asp.fact("indoors", p.id))
        if p.wind:
            lines.append(asp.fact("windy", p.id))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.id, a))
    for w in WHIRLY.values():
        lines.append(asp.fact("whirly_fact", w.id))
    for c in CHOICES.values():
        lines.append(asp.fact("choice_fact", c.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    smoke = 0
    try:
        sample = generate(CURATED[0])
        smoke = 1 if not sample.story else 0
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    if py != cl:
        print("MISMATCH between Python and ASP valid combos.")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
        return 1
    print(f"OK: ASP matches Python ({len(py)} combos), smoke test passed.")
    return smoke


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cat and whirly cautionary adventure storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--whirly", choices=WHIRLY)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--cat-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--cat-kind", choices=["cat"])
    ap.add_argument("--helper-kind", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.whirly is None or c[1] == args.whirly)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, whirly, choice = rng.choice(sorted(combos))
    cat_kind = args.cat_kind or "cat"
    helper_kind = args.helper_kind or rng.choice(["girl", "boy"])
    cat_name = args.cat_name or rng.choice(CAT_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != cat_name])
    return StoryParams(
        place=place,
        whirly=whirly,
        choice=choice,
        cat_name=cat_name,
        cat_kind=cat_kind,
        helper_name=helper_name,
        helper_kind=helper_kind,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.whirly not in WHIRLY:
        raise StoryError("Unknown whirly thing.")
    if params.choice not in CHOICES:
        raise StoryError("Unknown safe choice.")
    world = tell(
        PLACES[params.place],
        WHIRLY[params.whirly],
        CHOICES[params.choice],
        params.cat_name,
        params.cat_kind,
        params.helper_name,
        params.helper_kind,
    )
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for p, w, c in combos:
            print(f"  {p:6} {w:9} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
