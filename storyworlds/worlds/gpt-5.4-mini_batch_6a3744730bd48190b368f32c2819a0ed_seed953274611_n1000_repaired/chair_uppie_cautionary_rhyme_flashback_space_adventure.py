#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chair_uppie_cautionary_rhyme_flashback_space_adventure.py
==========================================================================================

A small standalone storyworld for a space-adventure cautionary rhyme with a
flashback beat. The story includes the seed words "chair" and "uppie" and keeps
the simulation honest: a child wants to reach something high in a spaceship,
a grown-up warns them, a flashback recalls a past tumble, and the ending proves
the safer choice changed the world.

The world is intentionally compact:
- physical meters: wobble, bump, reach, spark, calm
- emotional memes: excitement, caution, fear, relief, pride
- one clear premise, one warning, one remembered lesson, one safe resolution

Supported modes:
- default generation
- -n / --all / --seed
- --trace / --qa / --json
- --asp / --verify / --show-asp
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
CAUTION_MIN = 2.0


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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Ship:
    id: str
    scene: str
    deck: str
    high_spot: str
    safe_ladder: str
    sky_view: str
    rhyme_cue: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Dares:
    id: str
    attempt: str
    risk: str
    safe_alternative: str
    flashback_hook: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    ship: str
    dare: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    adult: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"child", "helper"}]

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
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_wobble(world: World) -> list[str]:
    out = []
    child = world.get("child")
    chair = world.get("chair")
    if child.meters["climb"] >= THRESHOLD and chair.meters["stable"] < THRESHOLD:
        sig = ("wobble",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        chair.meters["wobble"] += 1
        child.memes["fear"] += 1
        out.append("__wobble__")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    if world.get("child").memes["caution"] >= THRESHOLD:
        sig = ("calm",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.get("child").memes["excitement"] = max(0.0, world.get("child").memes["excitement"] - 1)
        world.get("helper").memes["pride"] += 1
        out.append("__calm__")
    return out


RULES = [Rule("wobble", _r_wobble), Rule("calm", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def cautionary_valid(ship: Ship, dare: Dares) -> bool:
    return "chair" in dare.risk and "safe" in dare.safe_alternative


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure cautionary rhyme with flashback.")
    ap.add_argument("--ship", choices=list(SHIPS))
    ap.add_argument("--dare", choices=list(DARES_REG))
    ap.add_argument("--adult", choices=["mom", "dad"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [(s, d) for s in SHIPS for d in DARES_REG if cautionary_valid(SHIPS[s], DARES_REG[d])]
    if args.ship and args.dare:
        if not cautionary_valid(SHIPS[args.ship], DARES_REG[args.dare]):
            raise StoryError("That dare is not a safe enough space-adventure for this world.")
    candidates = [c for c in choices
                  if (args.ship is None or c[0] == args.ship)
                  and (args.dare is None or c[1] == args.dare)]
    if not candidates:
        raise StoryError("(No valid combination matches the given options.)")
    ship, dare = rng.choice(sorted(candidates))
    child_name = rng.choice(["Mira", "Noah", "Tia", "Leo"])
    helper_name = rng.choice([n for n in ["Pip", "Zed", "Ari", "Juno"] if n != child_name])
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(["mom", "dad"])
    return StoryParams(ship=ship, dare=dare, child_name=child_name, child_gender=child_gender,
                       helper_name=helper_name, helper_gender=helper_gender, adult=adult)


def tell(ship: Ship, dare: Dares, params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = w.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    adult = w.add(Entity(id="Adult", kind="character", type=params.adult, role="adult", label=f"the {params.adult}"))
    chair = w.add(Entity(id="chair", kind="thing", type="chair", label="chair"))
    uppie = w.add(Entity(id="uppie", kind="thing", type="toy", label="uppie"))
    ship_ent = w.add(Entity(id="ship", kind="thing", type="ship", label=ship.scene))

    child.memes["excitement"] = 2
    helper.memes["caution"] = 2
    chair.meters["stable"] = 0.5
    w.facts.update(ship=ship, dare=dare, child=child, helper=helper, adult=adult, chair=chair, uppie=uppie, ship_ent=ship_ent)

    w.say(f"On the starship deck, {child.id} and {helper.id} turned the quiet cabin into {ship.scene}.")
    w.say(f"The {ship.deck} had a {ship.high_spot}, a {ship.safe_ladder}, and a bright {ship.sky_view}.")

    w.para()
    child.memes["excitement"] += 1
    child.meters["climb"] += 1
    w.say(f'{child.id} pointed at the {ship.high_spot} and grinned. "{dare.attempt}," {child.id} said.')
    w.say(f'"{ship.rhyme_cue}," {helper.id} replied, making it sound like a rhyme instead of a race.')

    w.para()
    helper.memes["caution"] += 1
    w.say(f'{helper.id} shook {helper.pronoun("possessive")} head. "{dare.risk}. Chair high, feet fly."')
    w.say(f'"{dare.flashback_hook}," {helper.id} added, and {child.id} got very still.')
    flashback(w, child)

    if child.memes["caution"] < CAUTION_MIN:
        child.memes["reckless"] += 1
        w.say(f'"But I want the view," {child.id} said, reaching for the {chair.label}.')
        chair.meters["wobble"] += 1
        propagate(w, narrate=False)
        child.memes["fear"] += 1
        w.para()
        w.say(f"{adult.label_word.capitalize()} came in at once, caught the chair, and lifted {child.id} down.")
        w.say(f'"{dare.safe_alternative}," {adult.pronoun()} said, pointing at the {ship.safe_ladder}.')
        child.memes["relief"] += 1
        helper.memes["relief"] += 1
    else:
        child.memes["caution"] += 1
        w.say(f'{child.id} blinked, let go, and whispered, "No chair uppie for me."')
        w.say(f"Instead, {helper.id} handed over the {uppie.label} and both children climbed the {ship.safe_ladder}.")
        child.meters["climb"] += 1
        chair.meters["wobble"] = 0
        child.memes["relief"] += 1
        helper.memes["pride"] += 1

    w.para()
    end_line(w, ship, dare, child, helper, adult, chair, uppie)
    w.facts["outcome"] = "safe"
    return w


def flashback(world: World, child: Entity) -> None:
    child.memes["fear"] += 1
    world.say(f"Flashback: once, {child.id} had stood on a chair and felt it shimmy like jelly.")
    world.say(f"The memory came back quick as a blink: one wobble, then a thump, then tears and dust.")
    world.say("That was why the warning mattered now.")


def end_line(world: World, ship: Ship, dare: Dares, child: Entity, helper: Entity, adult: Entity, chair: Entity, uppie: Entity) -> None:
    if chair.meters["wobble"] >= THRESHOLD:
        world.say(f"The chair stayed on the deck, quiet and safe, while the {ship.safe_ladder} did the climbing.")
    else:
        world.say(f"The chair stayed for sitting, and the {uppie.label} rode safely in little hands.")
    world.say(f"Up high they could see {ship.sky_view}, and the ship felt brave because no one took a foolish uppie.")
    world.say(f"{child.id} smiled at {helper.id} and {adult.label_word}. The rhyme had turned into a lesson, and the lesson into a safe adventure.")


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, adult, dare, ship = f["child"], f["helper"], f["adult"], f["dare"], f["ship"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id} on a starship, with {adult.label_word} nearby to help. The children's choices drive the whole adventure."),
        ("What did {0} want to do?".format(child.id),
         f"{child.id} wanted to {dare.attempt}. That sounded exciting, but it was not safe on a chair."),
        ("Why did {0} warn {1}?".format(helper.id, child.id),
         f"{helper.id} warned {child.id} because {dare.risk}. The helper also remembered a past tumble, so the warning came from care."),
        ("How did the story end?",
         f"It ended with the safer choice: they used the {ship.safe_ladder} and kept the {chair.label} for sitting. The ending proves the warning changed what happened."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a chair for?",
         "A chair is for sitting. It is not made for climbing high in a space cabin."),
        ("What is uppie?",
         "Uppie is a playful word for being lifted up or carried. It can be fun, but it should still be done safely."),
        ("Why do grown-ups give warnings?",
         "Grown-ups give warnings to help children stay safe. A warning can stop a small mistake before it becomes a hurt."),
    ]


def prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, dare, ship = f["child"], f["helper"], f["dare"], f["ship"]
    return [
        f'Write a space-adventure rhyme for a child named {child.id} that includes the words "chair" and "uppie".',
        f"Tell a cautionary story where {helper.id} remembers a bad fall and stops {child.id} from using a chair the wrong way.",
        f"Write a flashback story on a spaceship where the children choose the safe ladder instead of a chair uppie.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


SHIPS = {
    "relay": Ship(id="relay", scene="a silver relay station", deck="relay deck", high_spot="signal chair", safe_ladder="folding ladder", sky_view="the blue Earth spinning below", rhyme_cue="Step and keep; climb is steep"),
    "moonbase": Ship(id="moonbase", scene="a moonbase command room", deck="command room", high_spot="window nook", safe_ladder="hatch steps", sky_view="the round moon shining at the porthole", rhyme_cue="Feet stay low; up you go slowly"),
    "rocket": Ship(id="rocket", scene="a little rocket ship", deck="rocket deck", high_spot="map shelf", safe_ladder="cargo step", sky_view="the stars glittering like sugar", rhyme_cue="Low and slow, safe to know"),
}

DARES_REG = {
    "reach": Dares(id="reach", attempt="reach the star map with a chair uppie", risk="A chair can tip if you climb it", safe_alternative="use the safe ladder instead", flashback_hook="Remember the chair wobble from last time?", tags={"chair", "uppie"}),
    "look": Dares(id="look", attempt="get an uppie so I can look out the window", risk="Uppie on a chair makes you too high and too wobbly", safe_alternative="look from the ladder steps with help", flashback_hook="Remember how the chair rocked and scared you?", tags={"chair", "uppie"}),
    "wave": Dares(id="wave", attempt="wave from the chair uppie to the moon", risk="A chair is not a safe place for a big stretch", safe_alternative="wave from the floor with the safe ladder nearby", flashback_hook="Remember the thump after the wobble?", tags={"chair", "uppie"}),
}

CURATED = [
    StoryParams(ship="relay", dare="reach", child_name="Mira", child_gender="girl", helper_name="Pip", helper_gender="boy", adult="mom", seed=1),
    StoryParams(ship="moonbase", dare="look", child_name="Leo", child_gender="boy", helper_name="Ari", helper_gender="girl", adult="dad", seed=2),
    StoryParams(ship="rocket", dare="wave", child_name="Tia", child_gender="girl", helper_name="Juno", helper_gender="girl", adult="mom", seed=3),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, d) for s in SHIPS for d in DARES_REG if cautionary_valid(SHIPS[s], DARES_REG[d])]


ASP_RULES = r"""
valid(S,D) :- ship(S), dare(D), chair_word(chair), uppie_word(uppie).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SHIPS:
        lines.append(asp.fact("ship", s))
    for d in DARES_REG:
        lines.append(asp.fact("dare", d))
    lines.append(asp.fact("chair_word", "chair"))
    lines.append(asp.fact("uppie_word", "uppie"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(ship=None, dare=None, adult=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.ship not in SHIPS or params.dare not in DARES_REG:
        raise StoryError("Invalid ship or dare.")
    world = tell(SHIPS[params.ship], DARES_REG[params.dare], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for s, d in asp_valid_combos():
            print(f"  {s} {d}")
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        for i in range(args.n):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            if p.story if False else False:
                pass
            sample = generate(p)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(json.dumps(samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
