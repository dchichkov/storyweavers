#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/senator_orthodontics_belief_suspense_twist_kindness_space.py
=============================================================================================

A small standalone storyworld for a space-adventure tale about a nervous child,
a senator, and an orthodontics mishap that turns into a kindness surprise.

Seed words:
- senator
- orthodontics
- belief

Features:
- suspense
- twist
- kindness

Style:
- space adventure
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "senator"}
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
    atmosphere: str
    has_airlock: bool = False
    has_clinic: bool = False


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    important: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    item: str
    response: str
    child: str
    child_gender: str
    senator_name: str
    senator_gender: str
    trait: str
    seed: Optional[int] = None


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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("item")
    if child.memes["worry"] >= THRESHOLD and item.meters["lost"] >= THRESHOLD:
        sig = ("suspense",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            out.append("__tension__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense)]


def place_detail(place: Place) -> str:
    return {
        "orbital_clinic": "The little clinic floated beside a blue window, with star stickers on the walls and soft straps on every chair.",
        "moon_station": "The station hummed over the moon, and the corridor lights blinked like slow little comets.",
        "cargo_hub": "The cargo hub rattled gently, with crates tied down and a bright view of the spinning Earth.",
    }[place.id]


def can_afford_suspense(item: Item) -> bool:
    return item.fragile and item.important


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def predict_loss(world: World, item_id: str) -> dict:
    sim = world.copy()
    _lose_item(sim, sim.get(item_id), narrate=False)
    return {
        "lost": sim.get(item_id).meters["lost"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"],
    }


def _lose_item(world: World, item: Entity, narrate: bool = True) -> None:
    item.meters["lost"] += 1
    item.memes["drift"] += 1
    propagate(world, narrate=narrate)


def _find_item(world: World, item: Entity) -> None:
    item.meters["lost"] = 0.0
    item.meters["found"] += 1


def intro(world: World, child: Entity, senator: Entity, place: Place) -> None:
    child.memes["belief"] += 1
    world.say(
        f"{child.id} had a small belief that a trip to the {place.label} would be easy, "
        f"even though {child.pronoun('possessive')} smile-braces had been wobbling all day."
    )
    world.say(
        f"At the {place.label}, {senator.id} was waiting in a silver suit, and the station air smelled like clean metal and lemon soap."
    )


def incident(world: World, child: Entity, item: Entity, place: Place) -> None:
    child.memes["worry"] += 1
    world.say(
        f"Then, with a tiny click, the orthodontics case slipped from {child.id}'s hands and spun toward a narrow vent."
    )
    world.say(
        f"For one breath, it looked as if the case would vanish into the dark tube beyond the clinic lights."
    )


def warn(world: World, child: Entity, senator: Entity, item: Entity) -> None:
    pred = predict_loss(world, "item")
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"Wait," {child.id} whispered. "{item.label.capitalize()}!" '
        f"{senator.id} turned at once, and {senator.pronoun()} saw the worry on {child.id}'s face."
    )


def twist_help(world: World, senator: Entity, child: Entity, item: Entity, response: Response) -> None:
    world.say(
        f"Then came the twist: {senator.id} smiled and pulled a tiny magnet wand from a pocket, saying, "
        f'"I came because I believed you might need help today."'
    )
    world.say(
        f"In one careful sweep, {senator.pronoun()} {response.text.replace('{item}', item.label)}."
    )
    _find_item(world, item)
    child.memes["relief"] += 1
    child.memes["belief"] += 1


def kindness_ending(world: World, senator: Entity, child: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{senator.id} crouched beside {child.id} and said that braces, clips, and crooked teeth were nothing to be ashamed of."
    )
    world.say(
        f"{child.id} nodded, and the little case rested safely in {child.pronoun('possessive')} hand again as the stars drifted by the window."
    )
    world.say(
        f"Before they left the {place.label}, {child.id} felt brave enough to believe that help could arrive exactly when it was needed."
    )


def fail_ending(world: World, child: Entity, place: Place, item: Entity, response: Response) -> None:
    world.say(
        f"The vent swallowed the case before anyone could catch it, and even {response.fail.replace('{item}', item.label)} could not stop the loss."
    )
    world.say(
        f"{child.id} stood very still under the blinking lights of the {place.label}, sad and quiet, while the station rolled on above the moon."
    )


def tell(place: Place, item: Item, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         senator_name: str = "Senator Vale", senator_gender: str = "senator",
         trait: str = "curious") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    senator = world.add(Entity(id=senator_name, kind="character", type=senator_gender, role="senator"))
    case = world.add(Entity(id="item", kind="thing", type="item", label=item.label))
    world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    child.memes["belief"] = 1.0

    intro(world, child, senator, place)
    world.para()
    world.say(place_detail(place))
    incident(world, child, case, place)
    warn(world, child, senator, case)

    if response.power >= 1:
        world.para()
        twist_help(world, senator, child, case, response)
        kindness_ending(world, senator, child, place)
        outcome = "rescued"
    else:
        world.para()
        fail_ending(world, child, place, case, response)
        outcome = "lost"

    world.facts.update(
        child=child, senator=senator, item=case, place=place, item_cfg=item,
        response=response, outcome=outcome, rescued=(outcome == "rescued"),
    )
    return world


PLACES = {
    "orbital_clinic": Place("orbital_clinic", "orbital orthodontics clinic", "quiet", has_airlock=True, has_clinic=True),
    "moon_station": Place("moon_station", "moon station", "hushed", has_airlock=True, has_clinic=False),
    "cargo_hub": Place("cargo_hub", "cargo hub", "busy", has_airlock=True, has_clinic=False),
}

ITEMS = {
    "brace_case": Item("brace_case", "orthodontics case", "a little orthodontics case", fragile=True, important=True, tags={"orthodontics"}),
    "aligner": Item("aligner", "retainer", "a clear retainer case", fragile=True, important=True, tags={"orthodontics"}),
    "badge": Item("badge", "silver badge", "a silver badge", fragile=False, important=False, tags={"senator"}),
}

RESPONSES = {
    "magnet_wand": Response("magnet_wand", 3, 1, "used a tiny magnet wand to pull the case back from the vent", "used a tiny magnet wand", "used a tiny magnet wand to pull the case back", tags={"kindness"}),
    "glove_reach": Response("glove_reach", 2, 1, "reached in with a long glove and pulled the case free", "reached in with a long glove", "reached in with a long glove and pulled the case free", tags={"kindness"}),
    "too_weak": Response("too_weak", 1, 0, "tried to reach the case, but the wind kept pushing it away", "tried to reach the case, but the wind kept pushing it away", "tried to reach the case", tags={"suspense"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        if not place.has_airlock:
            continue
        for iid, item in ITEMS.items():
            if not can_afford_suspense(item):
                continue
            for rid, response in RESPONSES.items():
                if response.sense >= 2:
                    combos.append((pid, iid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about orthodontics, belief, suspense, twist, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--senator")
    ap.add_argument("--senator-gender", default="senator")
    ap.add_argument("--trait", choices=["curious", "brave", "careful", "hopeful"])
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("(Refusing response: it is too weak for a good suspense rescue.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, response = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(["Mia", "Luna", "Theo", "Finn", "Ava", "Noah"])
    senator = args.senator or rng.choice(["Senator Vale", "Senator Orion", "Senator Marin"])
    trait = args.trait or rng.choice(["curious", "brave", "careful", "hopeful"])
    response = args.response or response
    return StoryParams(place, item, response, child, child_gender, senator, args.senator_gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story for a child that includes the words "senator", "orthodontics", and "belief".',
        f"Tell a suspenseful story where {f['child'].id} is on a moon station for orthodontics and gets help from {f['senator'].id}.",
        f"Write a twist ending story where a senator turns out to be kind and saves a drifting orthodontics case.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, senator, item, place = f["child"], f["senator"], f["item"], f["place"]
    ans1 = (
        f"The story is about {child.id} and {senator.id} at the {place.label}. "
        f"{child.id} is there because of orthodontics, and the trip becomes suspenseful when the case slips away."
    )
    ans2 = (
        f"{item.label.capitalize()} almost drifted into a vent. "
        f"{senator.id} then helped in a gentle, careful way, which turned the scary moment into a kind one."
    )
    ans3 = (
        f"At the end, {child.id} got {item.label} back and felt braver about the trip. "
        f"The ending proves the twist: the senator was there to help, not to make trouble."
    )
    return [
        QAItem("Who is the story about?", ans1),
        QAItem("What made the story suspenseful?", ans2),
        QAItem("How did the story end?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is orthodontics?",
            "Orthodontics is the part of dentistry that helps teeth grow straighter. People may wear braces or retainers to guide their teeth into a better line.",
        ),
        QAItem(
            "What is a senator?",
            "A senator is a person who helps make laws for a country or a state. Senators often talk with people and vote on important rules.",
        ),
        QAItem(
            "What is belief?",
            "Belief means trusting that something is true or will happen. A belief can help a character keep going when the day feels uncertain.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
    return "\n".join(lines)


CURATED = [
    StoryParams("orbital_clinic", "brace_case", "magnet_wand", "Mia", "girl", "Senator Vale", "senator", "curious"),
    StoryParams("moon_station", "aligner", "glove_reach", "Theo", "boy", "Senator Orion", "senator", "hopeful"),
    StoryParams("cargo_hub", "brace_case", "magnet_wand", "Ava", "girl", "Senator Marin", "senator", "careful"),
]


ASP_RULES = r"""
suspense_case(P, I, R) :- place(P), item(I), response(R), fragile(I), important(I), sense(R, S), sense_min(M), S >= M.
rescued(P, I) :- suspense_case(P, I, R), response(R), power(R, PWR), PWR >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.fragile:
            lines.append(asp.fact("fragile", iid))
        if item.important:
            lines.append(asp.fact("important", iid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show suspense_case/3."))
    return sorted(set(asp.atoms(model, "suspense_case")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python combo sets differ.")
    else:
        print(f"OK: ASP and Python combo sets match ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, item=None, response=None, child=None, child_gender=None, senator=None, senator_gender="senator", trait=None), random.Random(0)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ITEMS[params.item],
        RESPONSES[params.response],
        params.child,
        params.child_gender,
        params.senator_name,
        params.senator_gender,
        params.trait,
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
        print(asp_program("", "#show suspense_case/3.\n#show rescued/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print("  ", t)
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
