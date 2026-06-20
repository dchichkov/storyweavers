#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thicken_destroy_problem_solving_moral_value_bad.py
===================================================================================

A standalone story world about a small kitchen mishap:
a child tries to fix a snack problem, accidentally makes the mixture too thick,
and then chooses a morally good, if unfortunate, solution that leads to a bad
ending. The comedy comes from the children's earnestness, the silly object
problem, and the absurdly oversized response that destroys the treat.

This world keeps the classical storyworld shape:
- typed entities with physical meters and emotional memes
- a causal simulation that drives prose
- three Q&A sets grounded in world state
- a Python reasonableness gate and an inline ASP twin
- verify / trace / qa / json / asp / show-asp support
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

# Make the shared result containers importable when this script is run directly.
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

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Scenario:
    id: str
    place: str
    container: str
    mixture: str
    tool: str
    fix: str
    snack: str
    splash: str
    badness: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_thicken(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    snack = world.get("snack")
    if kid.meters["stirring"] >= THRESHOLD and snack.meters["mixing"] >= THRESHOLD:
        sig = ("thicken",)
        if sig not in world.fired:
            world.fired.add(sig)
            snack.meters["thick"] += 1
            out.append("The mixture got thicker and thicker.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    snack = world.get("snack")
    table = world.get("table")
    if snack.meters["thick"] >= THRESHOLD and kid.meters["nudging"] >= THRESHOLD:
        sig = ("spill",)
        if sig not in world.fired:
            world.fired.add(sig)
            table.meters["sticky"] += 1
            kid.memes["oops"] += 1
            out.append("The bowl tipped, and the table got sticky.")
    return out


def _r_destroy(world: World) -> list[str]:
    out: list[str] = []
    snack = world.get("snack")
    if snack.meters["sticky"] >= THRESHOLD and snack.meters["saved"] < THRESHOLD:
        sig = ("destroy",)
        if sig not in world.fired:
            world.fired.add(sig)
            snack.meters["ruined"] += 1
            out.append("__destroy__")
    return out


CAUSAL_RULES = [
    Rule("thicken", "mixing", _r_thicken),
    Rule("spill", "mess", _r_spill),
    Rule("destroy", "ending", _r_destroy),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(scn: Scenario, resp: Response) -> bool:
    return scn.badness >= 2 and resp.sense >= 2 and ("fix" in scn.tags or "spoon" in scn.tags)


def can_save(resp: Response, scn: Scenario) -> bool:
    return resp.power >= scn.badness


def predict(world: World) -> dict:
    sim = world.copy()
    _do_problem(sim, narrate=False)
    return {"ruined": sim.get("snack").meters["ruined"] >= THRESHOLD}


def _do_problem(world: World, narrate: bool = True) -> None:
    kid = world.get("kid")
    snack = world.get("snack")
    kid.meters["stirring"] += 1
    snack.meters["mixing"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, kid: Entity, parent: Entity, scn: Scenario) -> None:
    kid.memes["hope"] += 1
    world.say(
        f"On a noisy afternoon, {kid.id} and {parent.label_word} stood in the kitchen, "
        f"where {scn.place} felt ready for a silly little mission."
    )
    world.say(
        f"{kid.id} wanted to make {scn.snack}, but the bowl already looked determined to be dramatic."
    )


def problem(world: World, kid: Entity, scn: Scenario) -> None:
    world.say(
        f"{kid.id} tried to stir the mixture until it would {scn.mixture}, but the spoon kept making a goofy plop."
    )
    kid.meters["stirring"] += 1
    world.get("snack").meters["mixing"] += 1
    propagate(world)


def warn(world: World, parent: Entity, kid: Entity, scn: Scenario) -> bool:
    if not predict(world)["ruined"]:
        return False
    parent.memes["care"] += 1
    world.say(
        f'"If it gets much thicker, it will {scn.splash}," {parent.id} said. '
        f'"Then we will need a smarter fix."'
    )
    return True


def solve(world: World, kid: Entity, parent: Entity, scn: Scenario, resp: Response) -> None:
    if not can_save(resp, scn):
        return
    kid.memes["determination"] += 1
    world.say(
        f'{kid.id} took a breath and chose the sensible idea: {resp.text}.'
    )
    snack = world.get("snack")
    snack.meters["saved"] += 1
    snack.meters["ruined"] = 0.0
    world.get("table").meters["sticky"] = 0.0
    world.say(
        f"The kitchen calmed down, and the bowl finally sat still."
    )


def bad_ending(world: World, kid: Entity, parent: Entity, scn: Scenario, resp: Response) -> None:
    snack = world.get("snack")
    snack.meters["ruined"] += 1
    world.say(
        f"But {resp.fail}. The mixture plopped over the edge, and the whole snack was ruined."
    )
    world.say(
        f"{parent.id} sighed, then helped {kid.id} clean up the sticky mess while the timer beeped like it was mocking them."
    )
    world.say(
        f"In the end, there was no {scn.snack}, only a sad bowl and a very quiet kitchen."
    )


def tell(scn: Scenario, resp: Response) -> World:
    world = World()
    kid = world.add(Entity("Pip", kind="character", type="boy", role="child"))
    parent = world.add(Entity("Mia", kind="character", type="mother", role="parent"))
    table = world.add(Entity("table", type="thing", label="the table"))
    snack = world.add(Entity("snack", type="thing", label=scn.snack))
    world.facts["scenario"] = scn
    world.facts["response"] = resp

    setup(world, kid, parent, scn)
    world.para()
    problem(world, kid, scn)
    warned = warn(world, parent, kid, scn)
    world.para()
    if reasonableness_gate(scn, resp):
        solve(world, kid, parent, scn, resp)
        if not can_save(resp, scn):
            bad_ending(world, kid, parent, scn, resp)
        elif snack.meters["ruined"] >= THRESHOLD:
            bad_ending(world, kid, parent, scn, resp)
        else:
            world.say(
                f'{kid.id} grinned at the neat fix, and {parent.label_word} laughed because the plan was absurdly good.'
            )
    else:
        bad_ending(world, kid, parent, scn, resp)

    world.facts.update(
        kid=kid, parent=parent, table=table, snack=snack, warned=warned,
        ended_bad=snack.meters["ruined"] >= THRESHOLD,
    )
    return world


SCENARIOS = {
    "sauce": Scenario("sauce", "the stove", "thicken", "destroy", "stir", "add water",
                      "tomato sauce", "splatter the counter", 3, tags={"fix", "spoon", "kitchen"}),
    "pudding": Scenario("pudding", "the counter", "thicken", "destroy", "whisk", "pour in milk",
                        "banana pudding", "splash onto the shirt", 4, tags={"fix", "spoon", "kitchen"}),
    "paint": Scenario("paint", "the craft table", "thicken", "destroy", "mix", "add a little water",
                      "blue paint", "blot the paper", 2, tags={"fix", "spoon", "craft"}),
}

RESPONSES = {
    "water": Response("water", 3, 2, "poured in a little water and stirred gently",
                      "poured in water, but the splash was already too wild",
                      "poured in a little water and stirred gently",
                      tags={"fix"}),
    "milk": Response("milk", 3, 3, "added milk and used a careful whisk",
                     "added milk, but the bowl still tipped and made a mess",
                     "added milk and used a careful whisk",
                     tags={"fix"}),
    "scrape": Response("scrape", 2, 4, "scraped the bowl clean and started again",
                       "scraped the bowl, but the snack had already been destroyed",
                       "scraped the bowl clean and started again",
                       tags={"fix"}),
}

KID_NAMES = ["Pip", "Bea", "Milo", "Nia", "Ollie", "Tess"]
TRAITS = ["careful", "curious", "earnest", "sensible"]


@dataclass
@dataclass
class StoryParams:
    scenario: str
    response: str
    name: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, scn in SCENARIOS.items():
        for rid, resp in RESPONSES.items():
            if reasonableness_gate(scn, resp):
                combos.append((sid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy story world about thickening and destroying a snack.")
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--response", choices=RESPONSES)
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
    combos = [c for c in valid_combos()
              if (args.scenario is None or c[0] == args.scenario)
              and (args.response is None or c[1] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, rid = rng.choice(sorted(combos))
    name = args.name or rng.choice(KID_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(sid, rid, name, trait)


def generation_prompts(world: World) -> list[str]:
    scn = world.facts["scenario"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "{scn.mixture}" and "{scn.tool}".',
        f"Tell a comedy story where {world.facts['kid'].id} tries to fix {scn.snack}, but the problem becomes bigger before it gets smaller.",
        f"Write a short story with a moral lesson where a child solves a kitchen problem, but the ending is still a little sad.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scn = world.facts["scenario"]
    kid = world.facts["kid"]
    parent = world.facts["parent"]
    resp = world.facts["response"]
    qa = [
        QAItem(
            question=f"What was {kid.id} trying to make?",
            answer=f"{kid.id} was trying to make {scn.snack}. The kitchen problem started when the mixture got too thick and needed help."
        ),
        QAItem(
            question="Why did the parent warn about the bowl?",
            answer=f"{parent.id} warned because the mixture could {scn.splash} if it kept getting thicker. That would make the snack harder to save."
        ),
        QAItem(
            question="What was the sensible fix?",
            answer=f"The sensible fix was to {resp.qa_text}. It was a calm way to solve the problem, even though the ending was still bad."
        ),
    ]
    if world.facts["ended_bad"]:
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended badly: the snack was destroyed, and there was only a sticky kitchen left. The child still helped clean up, which showed a good moral choice."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    scn = world.facts["scenario"]
    items = [
        QAItem(
            question="What does it mean to thicken something?",
            answer="To thicken something means it becomes less runny and more heavy or sticky."
        ),
        QAItem(
            question="What does it mean to destroy something?",
            answer="To destroy something means to ruin it so badly that it does not work or look right anymore."
        ),
        QAItem(
            question="Why is it good to clean up after a mess?",
            answer="Cleaning up is a good thing to do because it helps other people and leaves the place nicer than you found it."
        ),
    ]
    if "craft" in scn.tags:
        items.append(QAItem(
            question="What helps when paint gets too thick?",
            answer="A little water can help paint become easier to spread again."
        ))
    return items


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if bits:
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENARIOS[params.scenario], RESPONSES[params.response], )
    # tell() uses defaults for kid/parent names, but we need deterministic params;
    # patch the visible entity ids for the chosen story by rerendering with params.
    # Rebuild with selected name.
    world = World()
    scn = SCENARIOS[params.scenario]
    resp = RESPONSES[params.response]
    kid = world.add(Entity(params.name, kind="character", type="boy", role="child", traits=[params.trait]))
    parent = world.add(Entity("Mia", kind="character", type="mother", role="parent"))
    table = world.add(Entity("table", type="thing", label="the table"))
    snack = world.add(Entity("snack", type="thing", label=scn.snack))
    world.facts["scenario"] = scn
    world.facts["response"] = resp
    setup(world, kid, parent, scn)
    world.para()
    problem(world, kid, scn)
    warned = warn(world, parent, kid, scn)
    world.para()
    solve(world, kid, parent, scn, resp)
    bad_ending(world, kid, parent, scn, resp)
    world.facts.update(kid=kid, parent=parent, table=table, snack=snack, warned=warned, ended_bad=True)
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
valid(S, R) :- scenario(S), response(R), sense(R, X), sense_min(M), X >= M.
destroys(S) :- scenario(S), badness(S, B), B >= 2.
"""
def asp_facts() -> str:
    import asp
    lines = []
    for sid, scn in SCENARIOS.items():
        lines.append(asp.fact("scenario", sid))
        lines.append(asp.fact("badness", sid, scn.badness))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
    # smoke test
    try:
        sample = generate(StoryParams(*valid_combos()[0], name="Pip", trait="careful"))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/2.\n#show destroys/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for sid, rid in asp_valid_combos():
            print(f"  {sid} {rid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, r, "Pip", "careful")) for s, r in valid_combos()]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
