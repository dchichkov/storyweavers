#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/enthusiasm_sled_problem_solving_surprise_inner_monologue.py
===========================================================================================

A standalone story world for a small comedic TinyStories-style domain.

Premise
-------
A child is bursting with enthusiasm about a sled, but the sled cannot move on a
grass hill. The story turns on problem solving, a surprise fix, and brief inner
monologue that stays child-facing and concrete.

This world is intentionally tiny:
- typed entities with meters and memes
- a forward-chained world update
- a Python reasonableness gate plus inline ASP twin
- story + three Q&A sets derived from world state, not from rendered English
- CLI support matching the Storyweavers contract
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
PROBLEM_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
class Place:
    id: str
    label: str
    surface: str
    helps: set[str] = field(default_factory=set)
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
class Sled:
    id: str
    label: str
    phrase: str
    needs: set[str] = field(default_factory=set)
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
class Fix:
    id: str
    label: str
    phrase: str
    surprise: str
    solve_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["stuck"] >= THRESHOLD and (("humor",) not in world.fired):
            world.fired.add(("humor",))
            for kid in list(world.entities.values()):
                if kid.role == "child":
                    kid.memes["confused"] += 1
            out.append("__humor__")
    return out


CAUSAL_RULES = [Rule("humor", "social", _r_humor)]


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


def problem_exists(place: Place, sled: Sled) -> bool:
    return "flat" not in place.helps and "snow" not in place.helps and "sliding" in sled.needs


def chosen_fix(place: Place, sled: Sled) -> Optional[Fix]:
    for fix in FIXES.values():
        if sled.needs.issubset(place.helps | {fix.id}) or sled.needs & place.helps:
            if "sliding" in place.helps or "ice" in place.tags or fix.id in place.helps:
                return fix
    for fix in FIXES.values():
        if "snow" in fix.tags and "snow" in sled.needs:
            return fix
    return None


def predict_problem(world: World, fix: Fix) -> dict:
    sim = world.copy()
    _attempt(sim, narrate=False)
    return {"stuck": sim.get("sled").meters["stuck"] >= THRESHOLD, "joy": sim.get("kid").memes["joy"]}


def _attempt(world: World, narrate: bool = True) -> None:
    sled = world.get("sled")
    if world.get("hill").attrs.get("surface") == "grass":
        sled.meters["stuck"] += 1
        world.get("kid").memes["tension"] += 1
        propagate(world, narrate=narrate)


def tell(place: Place, sled: Sled, fix: Fix, child_name: str = "Milo",
         child_gender: str = "boy", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    hill = world.add(Entity(id="hill", type="place", label=place.label, attrs={"surface": place.surface}))
    sled_ent = world.add(Entity(id="sled", type="sled", label=sled.label))
    world.add(Entity(id="fix", type="tool", label=fix.label))

    child.memes["enthusiasm"] = 2.0
    child.memes["hope"] = 1.0
    world.facts["place"] = place
    world.facts["sled_cfg"] = sled
    world.facts["fix_cfg"] = fix

    world.say(
        f"{child.id} had so much enthusiasm that even the air seemed to bounce. "
        f"{child.id} had a sled, and {child.pronoun('possessive')} eyes kept darting to the hill."
    )
    world.say(
        f"The hill looked funny and plain. It was {place.surface}, not the sort of hill that would help a sled behave."
    )
    world.say(
        f'"This will be easy," {child.id} told {child.pronoun("object")}self, which was exactly the kind of sentence that made trouble grin.'
    )

    world.para()
    child.memes["inner_monologue"] += 1
    world.say(
        f'Inside {child.pronoun("possessive")} head, {child.id} thought, '
        f'"Maybe the sled just needs a little encouragement. Or a tiny miracle. Preferably the funny kind."'
    )
    world.say(
        f'{child.id} gave the sled a push. It made a dramatic little squeak, then stopped as if it had remembered something important.'
    )

    world.para()
    _attempt(world)
    if world.get("sled").meters["stuck"] >= THRESHOLD:
        world.say(
            f'"Uh-oh," {child.id} whispered. "That sled is doing the opposite of sled things."'
        )
        world.say(
            f'{parent.label_word.capitalize()} came over, looked once, and did not laugh too hard. That was the first surprise.'
        )
        fix_used = fix
        world.say(
            f'{parent.label_word.capitalize()} pointed at {fix_used.phrase} and said, '
            f'"What if we try {fix_used.solve_text}?"'
        )
        world.say(
            f'{child.id} blinked. That was the second surprise, because {child.id} had been expecting a lecture, not a rescue plan.'
        )
        world.say(
            f'In {child.pronoun("possessive")} head, {child.id} thought, "Oh. We are not defeated. We are inventing."'
        )
        world.para()
        child.memes["problem_solving"] += 1
        child.memes["surprise"] += 1
        world.get("sled").meters["stuck"] = 0.0
        world.say(
            f'They tried the new idea. At once, the sled stopped sulking, started sliding, and skittered down the hill with a zippy whoosh.'
        )
        world.say(
            f'{child.id} laughed so hard {child.id} had to hold {child.pronoun("possessive")} belly. '
            f'The hill had not changed much, but the plan had.'
        )
        world.say(
            f'By the end, the sled was flying, the problem was solved, and {child.id} was glowing with the kind of enthusiasm that comes back even bigger after a good surprise.'
        )
    else:
        world.say(
            f'To everyone\'s surprise, the sled moved at once. The plan worked so well that {child.id} looked as shocked as a cat hearing a teacup fall.'
        )

    world.facts.update(
        child=child,
        parent=parent,
        hill=hill,
        sled=sled_ent,
        fix=fix,
        outcome="solved" if world.get("sled").meters["stuck"] < THRESHOLD else "stuck",
        solved=world.get("sled").meters["stuck"] < THRESHOLD,
    )
    return world


PLACES = {
    "grasshill": Place("grasshill", "the grassy hill", "grass", helps=set(), tags={"grass"}),
    "snowbank": Place("snowbank", "the snowy hill", "snow", helps={"snow", "sliding"}, tags={"snow"}),
    "icepath": Place("icepath", "the icy slope", "ice", helps={"ice", "sliding"}, tags={"ice"}),
}

SLEDS = {
    "sled": Sled("sled", "sled", "a little red sled", needs={"sliding"}, tags={"sled"}),
    "bigsled": Sled("bigsled", "sled", "a bright blue sled", needs={"sliding"}, tags={"sled"}),
}

FIXES = {
    "wax": Fix("wax", "wax paper", "wax paper", "that was the funny surprise", "wax the runners", tags={"sliding"}),
    "rope": Fix("rope", "a rope tow", "a rope tow", "the grown-up surprise", "tie on a rope tow", tags={"sliding"}),
    "snow": Fix("snow", "packed snow", "packed snow", "the snowy surprise", "pack some snow first", tags={"snow", "sliding"}),
}

NAMES = ["Milo", "Nina", "Ava", "Theo", "Zoe", "Ben"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Finn", "Leo"]
GIRL_NAMES = ["Nina", "Ava", "Zoe", "Maya", "Ella"]
PARENTS = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for sid, sled in SLEDS.items():
            for fid, fix in FIXES.items():
                if pid == "grasshill" and fid in {"wax", "rope"}:
                    combos.append((pid, sid, fid))
                if pid in {"snowbank", "icepath"}:
                    combos.append((pid, sid, fid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    sled: str
    fix: str
    name: str
    gender: str
    parent: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child that includes the words "enthusiasm" and "sled".',
        f"Tell a comedy story where {f['child'].id}'s enthusiasm outruns the sled, then a surprise fix solves the problem.",
        f"Write a story with inner monologue, a problem, and a surprising solution about a sled that gets stuck.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    fix = f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who was full of enthusiasm, and {parent.label_word}."),
        ("What problem happened?",
         f"The sled got stuck on the hill. The hill was not the kind that helped a sled slide, so the first push did not work."),
        ("What surprised {0}?".format(child.id),
         f"{parent.label_word.capitalize()} did not give a lecture. Instead, {parent.label_word} offered {fix.phrase}, which turned the problem into a new plan."),
    ]
    if f["solved"]:
        qa.append((
            "How did the story end?",
            f"The sled started sliding, and {child.id} laughed all the way down the hill. The ending shows that the new plan worked better than the old one."
        ))
        qa.append((
            f"What did {child.id} think to {child.pronoun('object')}self?",
            f"{child.id} thought that maybe the sled needed encouragement or a tiny miracle. Then {child.id} realized the real answer was problem solving."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["fix_cfg"].tags) | set(world.facts["sled_cfg"].tags) | set(world.facts["place"].tags)
    out: list[tuple[str, str]] = []
    if "sled" in tags:
        out.append(("What is a sled?",
                    "A sled is a toy or vehicle you sit on and slide over snow or another slippery surface."))
    if "sliding" in tags:
        out.append(("What does sliding mean?",
                    "Sliding means moving smoothly over a surface instead of stopping or bouncing."))
    if "snow" in tags:
        out.append(("Why does snow help a sled?",
                    "Snow can be slippery, so a sled can glide over it more easily."))
    if "grass" in tags:
        out.append(("Why is grass hard for a sled?",
                    "Grass is not slippery enough, so a sled can slow down and get stuck."))
    out.append(("What is enthusiasm?",
                "Enthusiasm means having a lot of excited energy about something you want to do."))
    out.append(("What is problem solving?",
                "Problem solving means noticing what is wrong and trying a smart new plan."))
    return out


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        bits.append(f"type={e.type}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("grasshill", "sled", "wax", "Milo", "boy", "mother"),
    StoryParams("grasshill", "bigsled", "rope", "Nina", "girl", "father"),
    StoryParams("snowbank", "sled", "snow", "Theo", "boy", "mother"),
]


def explain_rejection(place: Place, sled: Sled) -> str:
    return f"(No story: {sled.label} needs a slippery surface, and {place.label} is not a compatible problem.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.surface:
            lines.append(asp.fact("surface", pid, p.surface))
        for h in sorted(p.helps):
            lines.append(asp.fact("helps", pid, h))
    for sid, s in SLEDS.items():
        lines.append(asp.fact("sled", sid))
        for n in sorted(s.needs):
            lines.append(asp.fact("needs", sid, n))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for t in sorted(f.tags):
            lines.append(asp.fact("tag", fid, t))
    return "\n".join(lines)


ASP_RULES = r"""
problem(P, S) :- place(P), sled(S), surface(P, grass), needs(S, sliding).
valid(P, S, F) :- problem(P, S), fix(F), tag(F, sliding).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos() differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, sled=None, fix=None, name=None, gender=None, parent=None), random.Random(777)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: generation smoke test failed: {exc}")
        return 1
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: emit smoke test failed: {exc}")
        return 1
    print(f"OK: verify smoke test passed; {len(valid_combos())} valid combos.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy story world about enthusiasm and a sled.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sled", choices=SLEDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.place and args.sled:
        if not problem_exists(PLACES[args.place], SLEDS[args.sled]):
            raise StoryError(explain_rejection(PLACES[args.place], SLEDS[args.sled]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.sled is None or c[1] == args.sled)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, sled, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place, sled, fix, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SLEDS[params.sled], FIXES[params.fix], params.name, params.gender, params.parent)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place}, {p.sled}, {p.fix}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
