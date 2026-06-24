#!/usr/bin/env python3
"""
Standalone storyworld: cedar bus depot suspense in a tall-tale voice.

A small, self-contained simulation about a bus depot, a cedar crate, a looming
problem, and a larger-than-life calm fix. The stories stay grounded in physical
state (meters) and emotional state (memes), with prose driven by the world
trace rather than a frozen paragraph template.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    landmark: str
    echo: str
    sky: str
    mood: str


@dataclass
class Hazard:
    id: str
    label: str
    source: str
    risk: str
    suspense: str
    makes_trouble: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    glow: str
    safe: bool = True


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


@dataclass
class StoryParams:
    setting: str
    hazard: str
    response: str
    item1: str
    item2: str
    cedar_kind: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
    seed: Optional[int] = None


class World:
    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        import copy
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        return other


SETTINGS = {
    "bus_depot": Setting(
        id="bus_depot",
        place="the bus depot",
        landmark="the map board",
        echo="the ticket windows clicked like teeth",
        sky="the gray roof",
        mood="big and waiting",
    )
}

HAZARDS = {
    "loose_gate": Hazard(
        id="loose_gate",
        label="the loose depot gate",
        source="a lopsided iron gate",
        risk="it could swing shut or open all at once",
        suspense="hung half-open like a secret",
    ),
    "stacked_crates": Hazard(
        id="stacked_crates",
        label="the cedar crates",
        source="a stack of cedar crates",
        risk="they could tumble like dominoes",
        suspense="leaned in a wobbling tower",
    ),
    "stuck_bus": Hazard(
        id="stuck_bus",
        label="the stuck bus door",
        source="a blue bus with a jammed door",
        risk="it could trap someone inside",
        suspense="sat silent with one door crooked",
    ),
}

ITEMS = {
    "flashlight": Item("flashlight", "flashlight", "a flashlight", "clicked bright as a star"),
    "lantern": Item("lantern", "lantern", "a little lantern", "glowed warm and steady"),
    "whistle": Item("whistle", "whistle", "a brass whistle", "rang clear and sharp"),
}

RESPONSES = {
    "call_manager": Response("call_manager", 4, 4, "called the depot manager and pointed to the danger", "called, but the danger kept growing", "called the depot manager and pointed to the danger"),
    "steady_gate": Response("steady_gate", 3, 3, "braced the gate with both hands until it stopped wobbling", "braced the gate, but it swung free anyway", "braced the gate until it stopped wobbling"),
    "spread_sand": Response("spread_sand", 2, 2, "spread sand under the bus tire and slowed the roll", "spread sand, but the bus was too heavy to stop", "spread sand under the bus tire and slowed the roll"),
    "water_pail": Response("water_pail", 1, 1, "threw a pail of water at the problem", "threw water, but that only made a bigger mess", "threw a pail of water at the problem"),
}

HEROES = [("Milo", "boy"), ("Ruby", "girl"), ("June", "girl"), ("Otis", "boy"), ("Nell", "girl")]
HELPERS = [("Pip", "boy"), ("Wren", "girl"), ("Iris", "girl"), ("Beau", "boy"), ("Clara", "girl")]
ADULTS = ["the depot manager", "the driver", "the keeper"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale suspense storyworld set in a bus depot.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--item1", choices=ITEMS)
    ap.add_argument("--item2", choices=ITEMS)
    ap.add_argument("--cedar-kind", choices=["cedar crates", "cedar planks", "cedar box"])
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--adult", choices=ADULTS)
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


def sensible_responses():
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos():
    return [(s, h, r) for s in SETTINGS for h in HAZARDS for r in RESPONSES if HAZARDS[h].makes_trouble]


def explain_rejection(hazard: Hazard) -> str:
    return f"(No story: {hazard.label} is not suspenseful enough for this seed.)"


def explain_response(rid: str) -> str:
    return f"(Refusing response '{rid}': it is too weak on common sense.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.hazard:
        combos = [c for c in combos if c[1] == args.hazard]
    if args.response:
        combos = [c for c in combos if c[2] == args.response]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, response = rng.choice(combos)
    item1, item2 = rng.sample(sorted(ITEMS), 2)
    hero, hg = rng.choice(HEROES)
    helper, hg2 = rng.choice([x for x in HELPERS if x[0] != hero])
    adult = args.adult or rng.choice(ADULTS)
    cedar_kind = args.cedar_kind or rng.choice(["cedar crates", "cedar planks", "cedar box"])
    return StoryParams(setting, hazard, response, item1, item2, cedar_kind, hero, hg, helper, hg2, adult)


def outcome_of(params: StoryParams) -> str:
    return "safe" if RESPONSES[params.response].power >= 3 else "near_miss"


def setup_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity("hero", "character", params.hero_gender, params.hero))
    helper = w.add(Entity("helper", "character", params.helper_gender, params.helper))
    adult = w.add(Entity("adult", "character", "adult", params.adult))
    depot = w.add(Entity("depot", "place", "place", SETTINGS[params.setting].place))
    cedar = w.add(Entity("cedar", "thing", "thing", params.cedar_kind))
    hazard = w.add(Entity("hazard", "thing", "thing", HAZARDS[params.hazard].label))
    hero.memes["curiosity"] = 1
    helper.memes["caution"] = 1
    depot.meters["crowded"] = 1
    cedar.meters["stack"] = 1
    w.facts.update(params=params, hero=hero, helper=helper, adult=adult, hazard=hazard, cedar=cedar)
    return w


def tell(params: StoryParams) -> World:
    w = setup_world(params)
    s = SETTINGS[params.setting]
    h = HAZARDS[params.hazard]
    r = RESPONSES[params.response]
    hero = w.facts["hero"]
    helper = w.facts["helper"]
    adult = w.facts["adult"]
    cedar = w.facts["cedar"]
    hazard = w.facts["hazard"]

    hero.memes["wonder"] = 1
    helper.memes["suspense"] = 1
    w.say(f"At {s.place}, {s.echo}. The morning felt big enough to hold a thunderhead.")
    w.say(f"{hero.id.capitalize()} and {helper.id.capitalize()} made a game of shadows near {h.suspense}.")
    w.say(f"They had a {params.cedar_kind} smell in the air, sharp and sweet as a song.")

    w.para()
    w.say(f"Then {hero.id.capitalize()} saw {h.source} and went still as a mouse in a hymn.")
    w.say(f'"That thing looks like trouble," {helper.id} whispered. "It {h.risk}."')
    hero.memes["bravado"] = 1
    helper.memes["fear"] = 1
    w.say(f"{hero.id.capitalize()} reached for {ITEMS[params.item1].phrase}, then paused.")

    w.para()
    if r.sense >= 3:
        w.say(f"{helper.id.capitalize()} pointed to the danger and got {adult}.")
        if r.power >= 3:
            hazard.meters["risk"] = 1
            hazard.meters["stopped"] = 1
            w.say(f"In one swift swing of sense, {adult} {r.text}.")
            w.say(f"{s.place} settled down again, and {h.label} stopped being a prowler in the dark.")
            hero.memes["relief"] = 1
            helper.memes["relief"] = 1
            w.para()
            w.say(f"After that, the children lit {ITEMS[params.item2].phrase} and watched it {ITEMS[params.item2].glow}.")
            w.say(f"The cedar smell stayed, but now it felt like a porch in summer instead of a storm cloud.")
        else:
            hazard.meters["risk"] = 1
            w.say(f"{adult} {r.fail}.")
            w.say(f"The depot held its breath, and {h.label} kept leaning like a rumor.")
            hero.memes["fear"] = 2
            helper.memes["fear"] = 2
            w.para()
            w.say(f"At last the whole place went quiet enough to hear the old roof creak.")
            w.say(f"That was the kind of quiet that makes a tall tale look over its shoulder.")
    else:
        w.say(f"{hero.id.capitalize()} tried {r.text}, but the problem only blinked at it and kept on.")
        w.say(f"{helper.id.capitalize()} gulped so hard the sound sounded like a bucket dropping in a well.")
        hero.memes["fear"] = 2
        helper.memes["fear"] = 2
        w.para()
        w.say(f"Then {adult} arrived, and the depot finally remembered how to be safe.")
        w.say(f"Even the cedar seemed to relax, as if its knots had been holding their own breath.")

    w.facts["outcome"] = outcome_of(params)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    h = HAZARDS[p.hazard]
    return [
        f"Write a tall-tale suspense story set in the bus depot where cedar crates and {h.label} make trouble, but the children get through it safely.",
        f"Tell a child-facing suspense tale in the bus depot that includes cedar, a tense pause, and a brave fix instead of a flat event log.",
        f"Write a tall tale about {p.hero} and {p.helper} at the bus depot, where something along the cedar stack looks scary until a grown-up or helper makes it right.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    h = HAZARDS[p.hazard]
    r = RESPONSES[p.response]
    q = [
        QAItem(question=f"Where is the story set?", answer=f"It is set at {SETTINGS[p.setting].place}."),
        QAItem(question=f"What makes the story suspenseful?", answer=f"{h.source} does, because it {h.risk}."),
        QAItem(question=f"What word ties the story to wood and smell?", answer=f"Cedar. The cedar detail gives the depot a sharp, warm smell and a tall-tale feel."),
    ]
    if r.power >= 3:
        q.append(QAItem(question=f"How was the problem handled?", answer=f"{world.facts['adult']} {r.qa_text}, and the danger settled down."))
    else:
        q.append(QAItem(question=f"What happened after the first attempt?", answer=f"The first attempt was not enough, so {world.facts['adult']} had to step in and make the depot safe."))
    return q


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a bus depot?", answer="A bus depot is a place where buses park, wait, and get ready to go."),
        QAItem(question="Why can cedar be noticed so easily?", answer="Cedar has a strong, fresh smell, so people often notice it right away."),
        QAItem(question="What should you do when something feels unsafe?", answer="Stop, get away from the danger, and call a grown-up for help."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for x in sample.story_qa:
        lines.append(f"Q: {x.question}")
        lines.append(f"A: {x.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for x in sample.world_qa:
        lines.append(f"Q: {x.question}")
        lines.append(f"A: {x.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes} type={e.type} label={e.label}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    w = tell(params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
    )


ASP_RULES = r"""
response_ok(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(setting(S),hazard(H),response(R)) :- setting(S), hazard(H), response_ok(R), makes_trouble(H).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines += [asp.fact("hazard", hid) for hid in HAZARDS]
    for hid, h in HAZARDS.items():
        if h.makes_trouble:
            lines.append(asp.fact("makes_trouble", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos():
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible():
    import asp
    model = asp.one_model(asp_program("", "#show response_ok/1."))
    return sorted(x for (x,) in asp.atoms(model, "response_ok"))


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible response gate matches.")
    else:
        print("MISMATCH: response gate differs.")
        rc = 1
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("bus_depot", "stacked_crates", "call_manager", "flashlight", "lantern", "cedar crates", "Milo", "boy", "Ruby", "girl", "the depot manager"),
    StoryParams("bus_depot", "loose_gate", "steady_gate", "whistle", "flashlight", "cedar planks", "June", "girl", "Otis", "boy", "the driver"),
    StoryParams("bus_depot", "stuck_bus", "spread_sand", "lantern", "whistle", "cedar box", "Nell", "girl", "Pip", "boy", "the keeper"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show response_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid/3."))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        while len(samples) < args.n:
            params = resolve_params(args, rng)
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
