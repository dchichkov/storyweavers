#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/legitimate_inner_monologue_rhyming_story.py
===========================================================================

A standalone storyworld for a tiny, child-facing rhyming tale about a child
who wants something special, hears an inner monologue, and chooses the
legitimate way to get it.

Premise
-------
A child finds a shiny pretend pass and wants to use it to enter a rhyme club.
A gentle gatekeeper spots the problem. The child thinks through the choice, tells
the truth, and receives a legitimate pass instead.

The storyworld keeps the prose state-driven:
- wanting a pass raises desire
- using a fake pass raises worry and blocks access
- telling the truth lowers worry and raises trust
- a legitimate pass grants entry and ends the story with a bright image

The generated stories are written in a soft rhyming style, with inner monologue
woven through the middle beat.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

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


@dataclass
class Place:
    id: str
    label: str
    glow: str
    rhyme: str
    locked: bool = False


@dataclass
class Pass:
    id: str
    label: str
    adjective: str
    legitimate: bool = False
    fake: bool = False


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["worry"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("gate").meters["alert"] += 1
    out.append("__gate__")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["honesty"] < THRESHOLD:
        return out
    sig = ("truth",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("keeper").memes["trust"] += 1
    out.append("__truth__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("truth", "social", _r_truth)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for pass_id, p in PASSES.items():
            for route in ROUTES:
                if route.legitimate and p.legitimate:
                    combos.append((place_id, pass_id, route.id))
                if not route.legitimate and p.fake:
                    combos.append((place_id, pass_id, route.id))
    return combos


def reasonableness_gate(pass_obj: Pass, route: "Route") -> bool:
    return (route.legitimate and pass_obj.legitimate) or ((not route.legitimate) and pass_obj.fake)


@dataclass
class Route:
    id: str
    label: str
    entrance: str
    end_image: str
    legitimate: bool = True
    rhyme_word: str = "light"


@dataclass
class StoryParams:
    place: str
    pass_id: str
    route: str
    child_name: str
    child_gender: str
    keeper_name: str
    keeper_gender: str
    seed: Optional[int] = None


def _do_use_pass(world: World, place: Entity, pass_obj: Entity, narrate: bool = True) -> None:
    child = world.get("child")
    if pass_obj.attrs.get("legitimate"):
        child.meters["access"] += 1
        child.memes["relief"] += 1
    else:
        child.meters["worry"] += 1
        child.memes["shame"] += 1
    propagate(world)


def rhyme(a: str, b: str) -> str:
    return f"{a} ... {b}"


def tell(place: Place, pass_cfg: Pass, route: Route,
         child_name: str = "Mia", child_gender: str = "girl",
         keeper_name: str = "Nia", keeper_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, role="child"))
    child.attrs["name"] = child_name
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_gender, role="keeper"))
    keeper.attrs["name"] = keeper_name
    gate = world.add(Entity(id="gate", type="thing", label="the little gate"))
    place_ent = world.add(Entity(id="place", type="thing", label=place.label))
    pass_ent = world.add(Entity(id="pass", type="thing", label=pass_cfg.label, attrs={
        "legitimate": pass_cfg.legitimate,
        "fake": pass_cfg.fake,
    }))
    child.memes["hope"] = 1.0
    child.memes["curiosity"] = 1.0

    world.say(
        f"{child_name} saw {place.label}, a twinkling place, "
        f"where rhyme songs hummed in a silver haze."
    )
    world.say(
        f"{child_name} found a shiny pass and held it near. "
        f'"It looks so neat," {child_name} thought, "so it must be clear."'
    )

    world.para()
    if pass_cfg.fake:
        child.meters["worry"] += 1
        world.say(
            f"{child_name} drifted to the gate with a secret grin, "
            f"but the paper felt wobbly, flimsy, thin."
        )
        world.say(
            f'"Is this a real pass?" asked {keeper_name} in a kind, calm way. '
            f'"I need the legitimate kind to open the day."'
        )
        world.say(
            f'"If I lie now," {child_name} thought, "my chest will feel tight. '
            f'"The honest road is slower, but it may turn bright."'
        )
        child.memes["honesty"] += 1
        world.say(
            f'"I found a pretend one," {child_name} said with care. '
            f'"I want the legitimate pass; I will not cheat here."'
        )
        keeper.memes["trust"] += 1
        pass_ent.attrs["legitimate"] = True
        pass_ent.attrs["fake"] = False
        child.meters["access"] += 1
        world.say(
            f"{keeper_name} smiled and stamped a proper pass today; "
            f"the gate swung open with a cheerful sway."
        )
        world.say(
            f"{child_name} stepped inside with a truer tune, "
            f"where the rhyme bells chimed by the moon-bright moon."
        )
        world.say(
            f"In the end, the night was neat and sweet: "
            f"a legitimate pass, a warm hello, and dancing feet."
        )
    else:
        child.meters["access"] += 1
        child.memes["relief"] += 1
        world.say(
            f"{child_name} showed the legitimate pass with a proud little beam, "
            f"and the gatekeeper nodded, like part of a dream."
        )
        world.say(
            f'"That is the proper one," {keeper_name} said with a smile. '
            f'"You may come in and stay awhile."'
        )
        world.say(
            f"{child_name} went in where the lanterns glowed, "
            f"and the rhyme club sparkled along the road."
        )
        world.say(
            f"The ending was bright as a star in flight: "
            f"legitimate pass in hand, and the whole room alight."
        )

    world.facts.update(
        child=child,
        keeper=keeper,
        gate=gate,
        place=place_ent,
        pass_ent=pass_ent,
        place_cfg=place,
        pass_cfg=pass_cfg,
        route=route,
        outcome="legitimate" if pass_cfg.legitimate else "redeemed",
    )
    return world


PLACES = {
    "rhyme_room": Place("rhyme_room", "the rhyme room", "soft lantern glow", "bright"),
    "story_steps": Place("story_steps", "the story steps", "golden paper glow", "neat"),
    "moon_door": Place("moon_door", "the moon door", "pale moon glow", "sweet"),
}

PASSES = {
    "legit_pass": Pass("legit_pass", "a legitimate pass", "proper", legitimate=True),
    "paper_star": Pass("paper_star", "a paper star pass", "sparkly", fake=True),
    "tin_ticket": Pass("tin_ticket", "a tin ticket", "tinny", fake=True),
}

ROUTES = [
    Route("open_mic", "open mic rhyme night", "the bright gate", "moon and light", True, "light"),
    Route("storybook", "storybook reading hour", "the quiet gate", "book and croon", True, "glow"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"].attrs["name"]
    place = f["place_cfg"].label
    pass_label = f["pass_cfg"].label
    route = f["route"].label
    return [
        f'Write a rhyming story for a young child about {child}, a gate, and '
        f'the word "legitimate".',
        f"Tell a gentle inner-monologue story where {child} wants to enter "
        f"{place} with {pass_label}, thinks carefully, and chooses the honest way.",
        f"Write a short rhyming tale where a child hears a gatekeeper say the pass "
        f"must be legitimate, then finds the true way in.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].attrs["name"]
    keeper = f["keeper"].attrs["name"]
    pass_label = f["pass_cfg"].label
    place = f["place_cfg"].label
    route = f["route"].label
    legitimate = f["pass_cfg"].legitimate
    items = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child}, who wanted to enter {place}. {keeper} helped by explaining the right way in.",
        ),
        QAItem(
            question=f"What did {child} want at the gate?",
            answer=f"{child} wanted to use {pass_label} to enter {place}. The child wanted the fun of {route}, but needed a legitimate pass first.",
        ),
    ]
    if legitimate:
        items.append(QAItem(
            question=f"How did {child} get inside?",
            answer=f"{child} showed a legitimate pass, and the gate opened right away. Because the pass was real, there was no need to worry or hide anything.",
        ))
    else:
        items.append(QAItem(
            question=f"What changed when the child told the truth?",
            answer=f"When {child} told the truth, the fake pass stopped mattering and {keeper} gave help instead. That made the pass legitimate and let the child enter safely.",
        ))
    items.append(QAItem(
        question="How did the story end?",
        answer=f"It ended with a bright, happy entrance into {place}. The child went in with a legitimate pass and a lighter heart.",
    ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does legitimate mean?",
            answer="Legitimate means real, proper, and allowed. If something is legitimate, it follows the rules and can be trusted.",
        ),
        QAItem(
            question="What should you do if you find a fake pass?",
            answer="You should not use it. The honest choice is to tell a grown-up or gatekeeper and ask for a real one.",
        ),
        QAItem(
            question="Why is honesty important?",
            answer="Honesty helps people trust you and keeps everyone safe. When you tell the truth, problems can be fixed the right way.",
        ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rhyme_room", "legit_pass", "open_mic", "Mia", "girl", "Nia", "girl"),
    StoryParams("story_steps", "paper_star", "storybook", "Theo", "boy", "Mara", "girl"),
]


def explain_rejection(pass_obj: Pass, route: Route) -> str:
    if route.legitimate and not pass_obj.legitimate:
        return (
            f"(No story: {pass_obj.label} is not legitimate, but {route.label} needs a real pass. "
            f"Pick the legitimate pass or a non-legitimate route.)"
        )
    if (not route.legitimate) and not pass_obj.fake:
        return (
            f"(No story: this route would need a fake pass, but {pass_obj.label} is legitimate. "
            f"Pick a fake pass for that route.)"
        )
    return "(No story: this combination is not reasonable.)"


def valid_route_pairs() -> list[tuple[str, str, str]]:
    combos = []
    for p_id, p in PASSES.items():
        for r in ROUTES:
            if reasonableness_gate(p, r):
                combos.append(("any", p_id, r.id))
    return combos


@dataclass
class StoryParams:
    place: str
    pass_id: str
    route: str
    child_name: str
    child_gender: str
    keeper_name: str
    keeper_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about a legitimate pass and an inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pass", dest="pass_id", choices=PASSES)
    ap.add_argument("--route", choices=ROUTES and [r.id for r in ROUTES])
    ap.add_argument("--child")
    ap.add_argument("--keeper")
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
    if args.pass_id and args.route:
        p = PASSES[args.pass_id]
        r = next(rr for rr in ROUTES if rr.id == args.route)
        if not reasonableness_gate(p, r):
            raise StoryError(explain_rejection(p, r))
    combos = []
    for place_id in PLACES:
        for pass_id, p in PASSES.items():
            for r in ROUTES:
                if reasonableness_gate(p, r):
                    if args.place and place_id != args.place:
                        continue
                    if args.pass_id and pass_id != args.pass_id:
                        continue
                    if args.route and r.id != args.route:
                        continue
                    combos.append((place_id, pass_id, r.id))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, pass_id, route = rng.choice(sorted(combos))
    child_name = args.child or rng.choice(["Mia", "Theo", "Luna", "Noah", "Ava"])
    keeper_name = args.keeper or rng.choice(["Nia", "Mara", "Finn", "June"])
    child_gender = "girl" if child_name in {"Mia", "Luna", "Ava"} else "boy"
    keeper_gender = "girl" if keeper_name in {"Nia", "Mara", "June"} else "boy"
    return StoryParams(place, pass_id, route, child_name, child_gender, keeper_name, keeper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PASSES[params.pass_id], next(r for r in ROUTES if r.id == params.route),
                 params.child_name, params.child_gender, params.keeper_name, params.keeper_gender)
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


ASP_RULES = r"""
legitimate_pass(P) :- pass(P), legitimate(P).
usable_route(R) :- route(R), route_legitimate(R).
valid_combo(Pl, P, R) :- place(Pl), legitimate_pass(P), usable_route(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p_id in PLACES:
        lines.append(asp.fact("place", p_id))
    for p_id, p in PASSES.items():
        lines.append(asp.fact("pass", p_id))
        if p.legitimate:
            lines.append(asp.fact("legitimate", p_id))
        if p.fake:
            lines.append(asp.fact("fake", p_id))
    for r in ROUTES:
        lines.append(asp.fact("route", r.id))
        if r.legitimate:
            lines.append(asp.fact("route_legitimate", r.id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid-combo gates differ.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: ASP gate matches Python gate and generate() smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
