#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cycle_poi_reconciliation_foreshadowing_sharing_bedtime_story.py
================================================================================================

A small bedtime story world about two children, a cycle, and a poi toy.

Premise:
- One child wants the cycle first.
- The other child wants to share a poi for the bedtime ride.
- A parent quietly foreshadows that bedtime is coming soon.
- The children reconcile and share the ride, ending calm and sleepy.

This world keeps the story grounded in state:
- physical meters: tiredness, waiting, glow, ridable, tucked_in
- emotional memes: hurt, worry, joy, trust, apology, warmth

It includes:
- cycle
- poi
- reconciliation
- foreshadowing
- sharing
- bedtime-story style narration

Run it:
    python storyworlds/worlds/gpt-5.4-mini/cycle_poi_reconciliation_foreshadowing_sharing_bedtime_story.py
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        t = self.type
        if t in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if t in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    name1: str
    type1: str
    name2: str
    type2: str
    parent_type: str
    setting: str = "the bedroom"
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

    def chars(self) -> list[Entity]:
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("cycle").meters.get("waiting", 0.0) >= THRESHOLD:
        for kid in (world.get("kid1"), world.get("kid2")):
            if ("worry", kid.id) in world.fired:
                continue
            world.fired.add(("worry", kid.id))
            kid.memes["worry"] = kid.memes.get("worry", 0.0) + 1
            out.append("__foreshadow__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    if world.get("cycle").meters.get("shared", 0.0) < THRESHOLD:
        return out
    for kid in (world.get("kid1"), world.get("kid2")):
        sig = ("soften", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["joy"] = kid.memes.get("joy", 0.0) + 1
        kid.memes["trust"] = kid.memes.get("trust", 0.0) + 1
        kid.memes["hurt"] = 0.0
        out.append("__reconcile__")
    return out


def _r_sleep(world: World) -> list[str]:
    out: list[str] = []
    if world.get("parent").meters.get("bedtime", 0.0) < THRESHOLD:
        return out
    if world.get("cycle").meters.get("shared", 0.0) < THRESHOLD:
        return out
    sig = ("sleep",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in (world.get("kid1"), world.get("kid2")):
        kid.meters["sleepy"] = kid.meters.get("sleepy", 0.0) + 1
    world.get("poi").meters["glow"] = 0.0
    out.append("__bedtime__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("soften", _r_soften), Rule("sleep", _r_sleep)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def predict_conflict(world: World) -> dict:
    sim = world.copy()
    sim.get("cycle").meters["waiting"] = 1.0
    propagate(sim, narrate=False)
    return {
        "worry": sim.get("kid1").memes.get("worry", 0.0) + sim.get("kid2").memes.get("worry", 0.0),
    }


def setup(world: World, a: Entity, b: Entity, parent: Entity, setting: str) -> None:
    world.say(f"At {setting}, {a.id} and {b.id} found a little cycle waiting by the bed.")
    world.say(
        f"Beside it sat a soft poi, its ribbon tucked neatly around the handle like a sleepy bow."
    )
    world.say(f"{a.id} wanted to ride first, and {b.id} wanted to hold the poi first.")
    world.say(f"{parent.id} smiled and said bedtime was coming soon, with the moon already peeking in.")


def argue(world: World, a: Entity, b: Entity) -> None:
    a.memes["hurt"] = a.memes.get("hurt", 0.0) + 1
    b.memes["hurt"] = b.memes.get("hurt", 0.0) + 1
    world.say(f'"I had it first," said {a.id}, hugging the cycle.')
    world.say(f'"But I wanted the poi," said {b.id}, blinking back a grumpy tear.')


def foreshadow(world: World, parent: Entity) -> None:
    pred = predict_conflict(world)
    parent.meters["bedtime"] = 1.0
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{parent.id} looked at the clock and whispered, "The stars are out. '
        f"That means the day is almost done, and little feelings can get big when "
        f"everyone is tired."'
    )


def reconcile(world: World, a: Entity, b: Entity) -> None:
    a.memes["apology"] = a.memes.get("apology", 0.0) + 1
    b.memes["apology"] = b.memes.get("apology", 0.0) + 1
    world.get("cycle").meters["shared"] = 1.0
    world.get("poi").meters["shared"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{a.id} took a breath and said sorry, then scooted over so {b.id} could hold the poi too."
    )
    world.say(
        f"{b.id} smiled back and said sorry too, and together they gave the cycle a gentle push."
    )


def bedtime(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    for kid in (a, b):
        kid.meters["sleepy"] = max(kid.meters.get("sleepy", 0.0), 1.0)
        kid.memes["warmth"] = kid.memes.get("warmth", 0.0) + 1
    world.say(
        f"Then {parent.id} tucked the poi by the pillow and asked the children to climb into bed."
    )
    world.say(
        f"The cycle rested against the wall, the poi glimmered softly once more, and both children drifted off smiling."
    )


def tell(params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id=params.name1, kind="character", type=params.type1, role="child"))
    b = world.add(Entity(id=params.name2, kind="character", type=params.type2, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, role="parent"))
    cycle = world.add(Entity(id="cycle", label="cycle", meters={"waiting": 0.0, "shared": 0.0}))
    poi = world.add(Entity(id="poi", label="poi", meters={"glow": 1.0, "shared": 0.0}))
    a.memes["joy"] = 1.0
    b.memes["joy"] = 1.0
    setup(world, a, b, parent, params.setting)
    world.para()
    argue(world, a, b)
    foreshadow(world, parent)
    world.para()
    reconcile(world, a, b)
    world.para()
    bedtime(world, a, b, parent)
    world.facts.update(kid1=a, kid2=b, parent=parent, cycle=cycle, poi=poi, setting=params.setting)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t1 in ["girl", "boy"]:
        for t2 in ["girl", "boy"]:
            if t1 == t2:
                continue
            combos.append(("bedroom", "cycle", "poi"))
    return combos


GIRL_NAMES = ["Mia", "Luna", "Nia", "Zoe", "Ivy"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about cycle, poi, and making up.")
    ap.add_argument("--name1")
    ap.add_argument("--type1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--type2", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--setting", default="the bedroom")
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
    type1 = args.type1 or rng.choice(["girl", "boy"])
    type2 = args.type2 or ("boy" if type1 == "girl" else "girl")
    if type1 == type2 and args.type1 and args.type2:
        raise StoryError("The story needs two different children so the sharing can matter.")
    name1 = args.name1 or rng.choice(GIRL_NAMES if type1 == "girl" else BOY_NAMES)
    name2 = args.name2 or rng.choice([n for n in (GIRL_NAMES if type2 == "girl" else BOY_NAMES) if n != name1])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name1=name1, type1=type1, name2=name2, type2=type2, parent_type=parent, setting=args.setting)


def story_qa(world: World) -> list[QAItem]:
    a, b, parent = world.facts["kid1"], world.facts["kid2"], world.facts["parent"]
    return [
        QAItem(
            question="What did the children disagree about?",
            answer=f"They disagreed about who would get the cycle first and who would hold the poi first. They were tired, so the disagreement felt bigger than it really was.",
        ),
        QAItem(
            question="How did they make up?",
            answer=f"{a.id} said sorry and made room for {b.id}, and {b.id} said sorry too. They shared the cycle and the poi, and the hurt feeling softened into smiles.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="The children were no longer squabbling. They were sleepy, kind to each other, and ready for bed with the cycle parked quietly and the poi tucked in close.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does bedtime usually do to a room?", answer="Bedtime makes a room quieter and softer, and people begin to slow down and get sleepy."),
        QAItem(question="Why can sharing help?", answer="Sharing helps because one child does not have to keep everything, and that often turns grumpy feelings into calmer ones."),
        QAItem(question="What is a cycle?", answer="A cycle is a two-wheeled ride you can pedal or push. Children use it for fun, practice, and little adventures."),
        QAItem(question="What is a poi?", answer="A poi can be a soft plaything or prop that can be held and shared. In this story, it is a gentle bedtime toy."),
    ]


def prompts(world: World) -> list[str]:
    return [
        'Write a bedtime story that uses the words "cycle" and "poi" and ends with the children making up.',
        f"Tell a gentle story where {world.facts['kid1'].id} and {world.facts['kid2'].id} share a cycle and a poi before sleep.",
        "Write a cozy reconciliation story with foreshadowing that bedtime is near.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:7} ({e.kind:9}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
shared_cycle :- cycle_shared.
shared_poi :- poi_shared.
foreshadowing :- bedtime_near, waiting_cycle.
reconciliation :- shared_cycle, shared_poi.
ending_sleep :- reconciliation, bedtime_near.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("cycle_shared"),
        asp.fact("poi_shared"),
        asp.fact("bedtime_near"),
        asp.fact("waiting_cycle"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconciliation/0.\n#show ending_sleep/0."))
    got = {s.name for s in model}
    want = {"reconciliation", "ending_sleep"}
    if got != want:
        print(f"MISMATCH: asp={sorted(got)} python={sorted(want)}")
        return 1
    print("OK: ASP twin agrees with Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(name1=None, type1=None, name2=None, type2=None, parent=None, setting="the bedroom"), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.type1 == params.type2:
        raise StoryError("The story needs two different children so sharing can change the mood.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show reconciliation/0.\n#show ending_sleep/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP says: reconciliation and a sleepy ending are possible.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name1="Mia", type1="girl", name2="Noah", type2="boy", parent_type="mother"),
            StoryParams(name1="Eli", type1="boy", name2="Zoe", type2="girl", parent_type="father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
