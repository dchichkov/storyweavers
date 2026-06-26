#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a hallow observatory, old animosity,
teamwork, and a lesson learned after a bad ending turns into a better one.

The world is intentionally tiny and constraint-checked:
- a child-facing tale about two caretakers or apprentices at an observatory
- a sacred/hallowed observatory that needs care
- one conflict driven by animosity
- one repair path that requires teamwork
- a brief bad ending image that motivates the lesson learned
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the hallow observatory"
    night: bool = True
    affords: set[str] = field(default_factory=lambda: {"polish", "share", "listen"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tag: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name_a: str
    name_b: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.zone = set(self.zone)
        return c


def _r_animosity(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("A")
    b = world.get("B")
    if a.memes.get("animosity", 0) >= THRESHOLD and b.memes.get("animosity", 0) >= THRESHOLD:
        sig = ("animosity",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["hurt"] = a.memes.get("hurt", 0) + 1
            b.memes["hurt"] = b.memes.get("hurt", 0) + 1
            out.append("Their sharp words made the little tower feel colder.")
    return out


def _r_breakage(world: World) -> list[str]:
    out: list[str] = []
    glass = world.get("lens")
    if world.get("A").meters.get("clumsy", 0) >= THRESHOLD and world.get("B").meters.get("watchful", 0) < THRESHOLD:
        sig = ("breakage",)
        if sig not in world.fired:
            world.fired.add(sig)
            glass.meters["cracked"] = glass.meters.get("cracked", 0) + 1
            out.append("The big lens cracked with a sad little ping.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("A")
    b = world.get("B")
    lens = world.get("lens")
    if a.memes.get("teamwork", 0) >= THRESHOLD and b.memes.get("teamwork", 0) >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            if lens.meters.get("cracked", 0) >= THRESHOLD:
                lens.meters["fixed"] = 1
                out.append("Together, they fit the glass back into place and wiped away the dust.")
            a.memes["peace"] = a.memes.get("peace", 0) + 1
            b.memes["peace"] = b.memes.get("peace", 0) + 1
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_animosity, _r_breakage, _r_teamwork):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "observatory": Setting(),
}

ACTIVITIES = {
    "polish": Activity(
        id="polish",
        verb="polish the lens",
        gerund="polishing the lens",
        rush="scrub the glass alone",
        mess="smudge",
        soil="cloudy with smudges",
        tag="observatory",
    ),
    "share": Activity(
        id="share",
        verb="share the star chart",
        gerund="sharing the star chart",
        rush="snatch the chart first",
        mess="tear",
        soil="torn and wrinkled",
        tag="teamwork",
    ),
    "listen": Activity(
        id="listen",
        verb="listen to the owl bells",
        gerund="listening to the owl bells",
        rush="shout over the bells",
        mess="noise",
        soil="full of noise",
        tag="lesson",
    ),
}

PRIZES = {
    "star_map": Prize(
        label="star map",
        phrase="a bright star map with silver dots",
        type="map",
        location="table",
    ),
    "lens": Prize(
        label="lens",
        phrase="a clear round lens",
        type="lens",
        location="tower",
    ),
    "lantern": Prize(
        label="lantern",
        phrase="a little brass lantern",
        type="lantern",
        location="shelf",
    ),
}

NAMES = ["Mina", "Tobin", "Elia", "Perrin", "Lila", "Jasper", "Nora", "Oren"]
TRAITS = ["gentle", "curious", "stubborn", "brave", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for prize in PRIZES:
                if prize == "lens" or act in {"polish", "share"}:
                    combos.append((place, act, prize))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not fit with the {prize.label} in a way that can create a clear lesson.)"


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    a = world.add(Entity(id="A", kind="character", type="girl", label=params.name_a))
    b = world.add(Entity(id="B", kind="character", type="boy", label=params.name_b))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label,
                             phrase=PRIZES[params.prize].phrase, caretaker="A"))
    lens = world.add(Entity(id="lens", type="lens", label="lens", phrase="the tower lens"))
    a.memes["animosity"] = 1
    b.memes["animosity"] = 1
    a.meters["clumsy"] = 1 if params.activity == "polish" else 0
    b.meters["watchful"] = 1 if params.activity != "polish" else 0
    a.memes["teamwork"] = 0
    b.memes["teamwork"] = 0
    world.facts = {"hero_a": a, "hero_b": b, "prize": prize, "lens": lens, "activity": ACTIVITIES[params.activity]}
    return world


def tell(world: World) -> World:
    a = world.get("A")
    b = world.get("B")
    prize = world.get("prize")
    act = world.facts["activity"]

    world.say(f"In the hallow observatory, {a.label} and {b.label} kept watch under a moon-pale dome.")
    world.say(f"They both loved the {prize.label}, but old animosity had made their words turn prickly.")
    world.say(f"One night, {a.label} wanted to {act.verb}, and {b.label} wanted to help, but neither wanted to ask first.")

    world.para()
    world.say(f"{a.label} tried to {act.rush}, and the lonely hurry made the {prize.label} go out of balance.")
    if act.id == "polish":
        world.get("lens").meters["cracked"] = 1
        world.say("The crystal lens slipped and cracked, and the stars looked blurred and far away.")
        world.say("That was the bad ending for a moment: the observatory could not sing its star-song.")
    elif act.id == "share":
        world.say("The star chart wrinkled in the tug-of-war, and the bright lines bent out of shape.")
        world.say("That was the bad ending for a moment: the map no longer pointed the children home.")
    else:
        world.say("The bells rang too loudly, and the room filled with noise instead of wisdom.")
        world.say("That was the bad ending for a moment: no one could hear the owl-silver lesson.")
    propagate(world, narrate=True)

    world.para()
    world.say("Then the two children grew still.")
    world.say("They saw that being proud only made the trouble bigger, and they learned a lesson at last.")
    a.memes["teamwork"] = 1
    b.memes["teamwork"] = 1
    a.memes["animosity"] = 0
    b.memes["animosity"] = 0
    world.say("They decided to use teamwork instead of spite.")
    world.say(f"Together they cleaned, held, and steadied the work until the {prize.label} was safe again.")
    propagate(world, narrate=True)
    world.say("By dawn, the hallow observatory shone softly, and the children stood side by side like two small lanterns.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["hero_a"].label
    b = f["hero_b"].label
    act = f["activity"]
    prize = f["prize"].label
    return [
        f'Write a fairy-tale story about {a}, {b}, and the {prize} in a hallow observatory.',
        f'Tell a child-friendly story where animosity becomes teamwork after a bad ending, and the lesson is learned.',
        f'Write a short tale that includes the word "observatory" and ends with the children working together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["hero_a"].label
    b = world.facts["hero_b"].label
    prize = world.facts["prize"].label
    act = world.facts["activity"].verb
    return [
        QAItem(question=f"Who were the two children in the observatory?", answer=f"They were {a} and {b}, two small keepers of the hallow observatory."),
        QAItem(question=f"What did they want to do with the {prize}?", answer=f"They wanted to {act} and care for the {prize}."),
        QAItem(question="What changed after the bad ending?", answer="Their animosity faded, they learned a lesson, and they chose teamwork instead."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an observatory?",
            answer="An observatory is a place where people look at the sky, stars, and moon through special tools.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people do a job together and help one another so the work goes better.",
        ),
        QAItem(
            question="What is animosity?",
            answer="Animosity is strong dislike or mean-feeling between people, and it can make working together hard.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:7} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("tagged", a, ACTIVITIES[a].tag))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,R) :- setting(P), activity(A), prize(R), compatible(A,R).
compatible(polish,lens).
compatible(polish,star_map).
compatible(share,star_map).
compatible(share,lens).
compatible(listen,lantern).
compatible(listen,star_map).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
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
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: animosity, hallow observatory, teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name_a=args.name_a or rng.choice(NAMES),
        name_b=args.name_b or rng.choice([n for n in NAMES if n != args.name_a]),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell(world)
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


CURATED = [
    StoryParams(place="observatory", activity="polish", prize="lens", name_a="Mina", name_b="Tobin"),
    StoryParams(place="observatory", activity="share", prize="star_map", name_a="Nora", name_b="Oren"),
    StoryParams(place="observatory", activity="listen", prize="lantern", name_a="Elia", name_b="Jasper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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
            header = f"### {p.name_a} and {p.name_b}: {p.activity} in {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
