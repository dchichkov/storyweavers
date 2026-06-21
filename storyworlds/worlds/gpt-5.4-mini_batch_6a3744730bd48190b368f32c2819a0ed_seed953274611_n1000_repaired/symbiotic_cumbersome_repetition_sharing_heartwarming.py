#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/symbiotic_cumbersome_repetition_sharing_heartwarming.py
========================================================================================

A small, heartwarming storyworld about a child, a cumbersome watering job,
repetition, and sharing. The story is driven by a tiny simulated garden where
a child keeps trying to carry too-heavy supplies alone, then learns to share
the load with a helper. The ending proves that the plant, the support, and the
people all change together.

Seed words:
- symbiotic
- cumbersome

Features:
- repetition
- sharing

Style:
- heartwarming
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
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
class Garden:
    id: str
    name: str
    scene: str
    plant: str
    support: str
    challenge: str
    finish: str
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
class Load:
    id: str
    label: str
    phrase: str
    cumbersome: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Helper:
    id: str
    label: str
    phrase: str
    share_phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Outcome:
    id: str
    effort: int
    warmth: int
    text: str
    ending: str
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
    garden: str
    load: str
    helper: str
    outcome: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_care(world: World) -> list[str]:
    out = []
    can = world.get("can")
    if can.meters["shared"] < THRESHOLD:
        return out
    if ("care", 1) in world.fired:
        return out
    world.fired.add(("care", 1))
    child = world.get("child")
    elder = world.get("elder")
    child.memes["relief"] += 1
    elder.memes["warmth"] += 1
    out.append("__shared__")
    return out


def _r_growth(world: World) -> list[str]:
    out = []
    plant = world.get("plant")
    can = world.get("can")
    if can.meters["watered"] < THRESHOLD or plant.meters["growing"] >= THRESHOLD:
        return out
    if ("growth", 1) in world.fired:
        return out
    world.fired.add(("growth", 1))
    plant.meters["growing"] += 1
    plant.memes["hope"] += 1
    out.append("__bloom__")
    return out


CAUSAL_RULES = [Rule("care", "social", _r_care), Rule("growth", "physical", _r_growth)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def predict(world: World) -> dict:
    sim = world.copy()
    _do_attempt(sim, narrate=False)
    return {
        "shared": sim.get("can").meters["shared"] >= THRESHOLD,
        "watered": sim.get("can").meters["watered"] >= THRESHOLD,
    }


def _do_attempt(world: World, narrate: bool = True) -> None:
    child = world.facts.get("child") or world.get("child")
    can = world.facts.get("can") or world.get("can")
    attempt = int(can.meters["carried"])
    child.memes["effort"] += 1
    can.meters["carried"] += 1
    can.meters["cumbersome"] += 1
    if narrate:
        if attempt == 0:
            world.say(f"{child.id} lifted the {can.label}, but it was cumbersome and wobbly.")
        else:
            world.say(f"{child.id} tried the {can.label} again, gripping it with both hands.")
    if can.meters["shared"] < THRESHOLD:
        child.memes["strain"] += 1
        can.meters["spilled"] += 1
        if narrate:
            if attempt == 0:
                world.say(f"The water sloshed over the rim before {child.pronoun('subject')} could reach the soil.")
            else:
                world.say(f"Even the second try spilled, and {child.id} finally stopped to think.")


def tell(garden: Garden, load: Load, helper: Helper, outcome: Outcome,
         child: str = "Mina", child_gender: str = "girl",
         elder: str = "Grandpa", elder_gender: str = "grandfather") -> World:
    world = World()
    kid = world.add(Entity(id=child, kind="character", type=child_gender, role="child"))
    elder_ent = world.add(Entity(id=elder, kind="character", type=elder_gender, role="elder"))
    plant = world.add(Entity(id="plant", kind="thing", type="plant", label=garden.plant))
    support = world.add(Entity(id="support", kind="thing", type="support", label=garden.support))
    can = world.add(Entity(id="can", kind="thing", type="load", label=load.label))

    world.facts["garden"] = garden
    world.facts["load"] = load
    world.facts["helper"] = helper
    world.facts["outcome"] = outcome
    world.facts["child"] = kid
    world.facts["elder"] = elder_ent
    world.facts["can"] = can

    kid.memes["love"] += 1
    elder_ent.memes["love"] += 1
    world.say(f"In {garden.name}, {child} and {elder} worked beside {garden.plant}.")
    world.say(
        f"Their little task was symbiotic: the {garden.plant} needed water, and the "
        f"{garden.support} helped the vine stay tall."
    )
    world.say(
        f"Near the path sat a {load.label} full of water. It was {load.phrase}, and "
        f"carrying it alone was cumbersome."
    )

    world.para()
    world.say(f"{child} tried to help.")
    _do_attempt(world)
    world.say(f"{child} paused, then tried again.")
    _do_attempt(world)
    pred = predict(world)
    world.facts["pred"] = pred
    world.say(
        f'{child} frowned and said, "{helper.phrase}."'
    )
    world.say(
        f'{elder} smiled and said, "{helper.share_phrase}."'
    )
    can.meters["shared"] += 1
    can.meters["watered"] += 1
    propagate(world)
    world.say(
        f"Together they steadied the cumbersome load, and the water finally reached the soil."
    )

    world.para()
    if outcome.id == "bloom":
        plant.meters["bloom"] += 1
        world.say(f"The {garden.plant} climbed the {garden.support} and turned bright and full.")
        world.say(
            f"{child} and {elder} sat side by side, watching the leaves reach up as if they were smiling."
        )
        world.say(
            f"It felt heartwarming, like the whole garden was sharing one happy breath."
        )
    else:
        world.say(
            f"The garden stayed quiet for now, but {child} and {elder} kept sharing the work."
        )
        world.say(
            f"Even on a slow day, the repeated tries made the little corner of earth feel cared for."
        )

    world.facts.update(child=kid, elder=elder_ent, plant=plant, support=support, can=can)
    return world


GARDENS = {
    "bean_patch": Garden(
        id="bean_patch",
        name="the bean patch",
        scene="a small patch of beans",
        plant="bean vine",
        support="trellis",
        challenge="a thirsty bean vine",
        finish="the vine climbed high",
        tags={"garden", "symbiotic"},
    ),
    "sunflower_row": Garden(
        id="sunflower_row",
        name="the sunflower row",
        scene="a sunny row of flowers",
        plant="sunflower",
        support="stake",
        challenge="tall blossoms",
        finish="the flower heads lifted",
        tags={"garden", "sharing"},
    ),
    "herb_box": Garden(
        id="herb_box",
        name="the herb box",
        scene="a little herb box by the porch",
        plant="basil",
        support="little fence",
        challenge="a thirsty herb patch",
        finish="the leaves grew glossy",
        tags={"garden", "repetition"},
    ),
}

LOADS = {
    "bucket": Load(id="bucket", label="bucket", phrase="too big for one small pair of arms", cumbersome=True, tags={"water"}),
    "watering_can": Load(id="watering_can", label="watering can", phrase="heavy with water and hard to balance", cumbersome=True, tags={"water"}),
}

HELPERS = {
    "share_hands": Helper(
        id="share_hands",
        label="share hands",
        phrase="Maybe we can share the load",
        share_phrase="Let's share the can together",
        tags={"sharing"},
    ),
    "take_turns": Helper(
        id="take_turns",
        label="take turns",
        phrase="Let's take turns so nobody has to strain alone",
        share_phrase="We can each hold one side and pour together",
        tags={"sharing", "repetition"},
    ),
}

OUTCOMES = {
    "bloom": Outcome(
        id="bloom",
        effort=2,
        warmth=3,
        text="The shared water helped the plant bloom",
        ending="the vine climbed high and the children smiled",
        tags={"heartwarming"},
    ),
    "steady": Outcome(
        id="steady",
        effort=1,
        warmth=2,
        text="The garden was cared for, even if the bloom was still coming",
        ending="the soil was damp and ready for tomorrow",
        tags={"heartwarming"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for g in GARDENS:
        for l in LOADS:
            for h in HELPERS:
                combos.append((g, l, h))
    return combos


def explain_rejection(_: str) -> str:
    return "(No story: this little world always allows the garden, the load, and the shared helping.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming garden storyworld about repetition and sharing.")
    ap.add_argument("--garden", choices=GARDENS)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"], dest="child_gender")
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["mother", "father", "grandmother", "grandfather"], dest="elder_gender")
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
    garden = args.garden or rng.choice(sorted(GARDENS))
    load = args.load or rng.choice(sorted(LOADS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    outcome = args.outcome or rng.choice(sorted(OUTCOMES))
    return StoryParams(
        garden=garden,
        load=load,
        helper=helper,
        outcome=outcome,
        child=args.child or rng.choice(["Mina", "Iris", "Lena", "Toby", "Noah"]),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        elder=args.elder or rng.choice(["Grandpa", "Grandma"]),
        elder_gender=args.elder_gender or rng.choice(["grandfather", "grandmother"]),
    )


def generation_prompts(world: World) -> list[str]:
    g = world.facts["garden"]
    l = world.facts["load"]
    h = world.facts["helper"]
    return [
        f'Write a heartwarming story that uses the words "symbiotic" and "cumbersome".',
        f"Tell a small garden story where {g.plant} and its support are symbiotic, but a cumbersome {l.label} makes the child stop and ask for help.",
        f"Write a repetition-and-sharing story where a child tries twice, then shares the load and ends with a warm garden image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    g = world.facts["garden"]
    l = world.facts["load"]
    h = world.facts["helper"]
    child = world.facts["child"]
    elder = world.facts["elder"]
    can = world.facts["can"]
    plant = world.facts["plant"]
    return [
        ("What kind of story is this?",
         f"It is a heartwarming garden story about {child.id} and {elder.id}. The story keeps returning to sharing, which is why it feels gentle and kind."),
        ("Why was the load hard to carry?",
         f"The {l.label} was cumbersome because it was full of water and too big to steady alone. That made {child.id} stop, try again, and then ask for help."),
        ("What does symbiotic mean in this story?",
         f"Here, symbiotic means the {plant.label} and the {g.support} help each other. The plant climbs, and the support gives it a place to grow."),
        ("How did sharing change the ending?",
         f"Once {child.id} and {elder.id} shared the {can.label}, the water reached the roots and the garden brightened. Sharing turned a frustrating task into a warm one."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does cumbersome mean?",
         "Cumbersome means something is awkward or hard to carry because it is heavy, bulky, or tricky to handle."),
        ("What does sharing mean?",
         "Sharing means two or more people use, hold, or enjoy something together instead of one person doing it alone."),
        ("Why do plants need water?",
         "Plants need water to stay healthy and keep growing. Water helps roots and leaves do their work."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for gid in GARDENS:
        lines.append(asp.fact("garden", gid))
    for lid, l in LOADS.items():
        lines.append(asp.fact("load", lid))
        if l.cumbersome:
            lines.append(asp.fact("cumbersome", lid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for oid in OUTCOMES:
        lines.append(asp.fact("outcome", oid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(G, L, H) :- garden(G), load(L), helper(H).
shared(L) :- cumbersome(L).
heartwarming(O) :- outcome(O).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos() differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.garden not in GARDENS or params.load not in LOADS or params.helper not in HELPERS or params.outcome not in OUTCOMES:
        raise StoryError("Invalid story parameters.")
    world = tell(
        GARDENS[params.garden],
        LOADS[params.load],
        HELPERS[params.helper],
        OUTCOMES[params.outcome],
        child=params.child,
        child_gender=params.child_gender,
        elder=params.elder,
        elder_gender=params.elder_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


CURATED = [
    StoryParams(garden="bean_patch", load="watering_can", helper="share_hands", outcome="bloom", child="Mina", child_gender="girl", elder="Grandpa", elder_gender="grandfather"),
    StoryParams(garden="herb_box", load="bucket", helper="take_turns", outcome="steady", child="Toby", child_gender="boy", elder="Grandma", elder_gender="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
