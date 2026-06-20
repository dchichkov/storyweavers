#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/convince_sharing_bravery_folk_tale.py
======================================================================

A standalone storyworld for a tiny folk-tale domain about a child who must be
convinced to share a precious thing and find a braver way to help the village.

Premise
-------
A folk-tale child wants to keep a special good for themself. A patient elder
tries to convince the child that sharing will help someone in need. The child
must choose between pride and bravery, and the ending shows that sharing makes
the whole village warmer, kinder, or safer.

Domain idea
-----------
The shared object is usually a loaf of bread, a cloak, a basket of apples, or a
small bell. The need is simple: a neighbor is cold, hungry, lost, or scared.
The tension is whether the child will share. Bravery here is not fighting; it is
being bold enough to give, speak up, or walk into the dark with help.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- forward-chained world model
- Python reasonableness gate plus inline ASP twin
- three QA sets from world state, not rendered English
- robust direct execution from repo root
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_MIN = 1.0


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
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class ObjectItem:
    id: str
    label: str
    phrase: str
    precious: bool = False
    shareable: bool = False
    helper: bool = False
    comfort: str = ""
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
class Need:
    id: str
    label: str
    phrase: str
    urgency: int
    kind: str
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
class Gift:
    id: str
    label: str
    phrase: str
    cheer: str
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


def _r_shared_relief(world: World) -> list[str]:
    out: list[str] = []
    for kid in list(world.entities.values()):
        if kid.role != "child":
            continue
        if kid.meters["shared"] < THRESHOLD:
            continue
        sig = ("shared_relief", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["joy"] += 1
        kid.memes["bravery"] += 1
        out.append("__shared_relief__")
    return out


def _r_help_arrives(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared") and world.facts.get("need_met"):
        sig = ("need_met",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__need_met__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("shared_relief", "social", _r_shared_relief),
    Rule("help_arrives", "social", _r_help_arrives),
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


def can_convince(obj: ObjectItem, need: Need) -> bool:
    return obj.shareable and not obj.precious and need.urgency >= 1


def predicted_change(obj: ObjectItem, need: Need) -> bool:
    return can_convince(obj, need)


def tell(
    child_name: str,
    child_gender: str,
    elder_name: str,
    elder_gender: str,
    object_item: ObjectItem,
    need: Need,
    gift: Gift,
    place: str,
    seed: Optional[int] = None,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    need_ent = world.add(Entity(id="need", type="need", label=need.label))
    obj = world.add(Entity(id="object", type="object", label=object_item.label))
    child.memes["pride"] = 1.0
    child.memes["bravery"] = 1.0
    elder.memes["patience"] = 1.0
    world.facts["place"] = place
    world.facts["need_label"] = need.label
    world.facts["object_label"] = object_item.label
    world.facts["gift"] = gift
    world.facts["need_ent"] = need_ent
    world.facts["object_ent"] = obj

    world.say(
        f"In a little folk village by {place}, {child.id} found {object_item.phrase} and held it close."
    )
    world.say(
        f"That same day, a {need.kind} need rose in the lane: {need.phrase}."
    )

    world.para()
    world.say(
        f"{elder.id} came with a calm step and tried to convince {child.id} that sharing could help."
    )
    if predicted_change(object_item, need):
        world.say(
            f'"If you share it," {elder.id} said, "the village will not be the same, and that is a good thing."'
        )
    else:
        world.say(
            f'"This little thing can be shared," {elder.id} said, "and it will not be lost by being given."'
        )

    if can_convince(object_item, need):
        child.memes["doubt"] += 1
        child.memes["bravery"] += 1
        world.say(
            f"{child.id} looked down at {object_item.label}, took a deep breath, and chose the braver path."
        )
        world.say(
            f"{child.id} opened {object_item.phrase} and shared it with the one who needed it most."
        )
        child.meters["shared"] += 1
        world.facts["shared"] = True
        world.facts["need_met"] = True
        propagate(world, narrate=False)
        world.para()
        world.say(
            f"{need.phrase.capitalize()} was eased at once, and the lane grew warm with thankful voices."
        )
        world.say(
            f"At the end, {child.id} stood a little taller, and {object_item.label} felt more magical for having been shared."
        )
    else:
        world.say(
            f"{child.id} could not be convinced, and the old plea passed by like wind through reeds."
        )
        world.say(
            f"The village had to wait for help from elsewhere, and {child.id} kept the {object_item.label} tucked away."
        )
        world.facts["shared"] = False
        world.facts["need_met"] = False

    world.facts.update(
        child=child,
        elder=elder,
        object_item=object_item,
        need=need,
        gift=gift,
        seed=seed,
    )
    return world


THEMES = {
    "village": "a small village of thatched roofs",
    "forest": "the edge of an old forest",
    "hill": "a windy hill above the river",
}

OBJECTS = {
    "bread": ObjectItem("bread", "bread", "a warm round loaf of bread", precious=True, shareable=True, tags={"bread", "food"}),
    "cloak": ObjectItem("cloak", "cloak", "a blue wool cloak", precious=False, shareable=True, comfort="warmth", tags={"cloak", "warmth"}),
    "apples": ObjectItem("apples", "apples", "a basket of red apples", precious=False, shareable=True, tags={"apples", "food"}),
    "lantern": ObjectItem("lantern", "lantern", "a tiny brass lantern", precious=True, shareable=True, helper=True, tags={"lantern", "light"}),
}

NEEDS = {
    "hunger": Need("hunger", "hunger", "a hungry child at the gate", urgency=2, kind="hunger", tags={"food"}),
    "cold": Need("cold", "cold", "a shivering traveler on the road", urgency=2, kind="cold", tags={"warmth"}),
    "dark": Need("dark", "dark", "a shepherd lost after dusk", urgency=1, kind="dark", tags={"light"}),
}

GIFTS = {
    "song": Gift("song", "song", "a little song", "cheered the hearth", tags={"song"}),
    "thanks": Gift("thanks", "thanks", "a bright thank-you", "filled the room", tags={"thanks"}),
    "ribbon": Gift("ribbon", "ribbon", "a red ribbon", "looked like a promise", tags={"ribbon"}),
}

GIRL_NAMES = ["Mira", "Lina", "Sana", "Tilda", "Nia", "Elsa"]
BOY_NAMES = ["Jon", "Perrin", "Milo", "Bram", "Tobin", "Oren"]
ELDER_NAMES = ["Grandma Willow", "Old Ansel", "Mother Rowan", "Grandpa Birch"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    object_item: str
    need: str
    gift: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for oid, obj in OBJECTS.items():
            for nid, need in NEEDS.items():
                if can_convince(obj, need):
                    combos.append((theme, oid, nid))
    return combos


def explain_rejection(obj: ObjectItem, need: Need) -> str:
    if obj.precious and need.urgency < 2:
        return f"(No story: {obj.label} is too precious to share for such a small need.)"
    if not obj.shareable:
        return f"(No story: {obj.label} cannot be shared in this tale.)"
    return f"(No story: no reasonable sharing-and-bravery situation fits {obj.label} and {need.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: convince, sharing, bravery, folk tale.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--object", dest="object_item", choices=OBJECTS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-gender", choices=["woman", "man", "grandmother", "grandfather"])
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
    if args.object_item and args.need:
        if not can_convince(OBJECTS[args.object_item], NEEDS[args.need]):
            raise StoryError(explain_rejection(OBJECTS[args.object_item], NEEDS[args.need]))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.object_item is None or c[1] == args.object_item)
              and (args.need is None or c[2] == args.need)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, object_item, need = rng.choice(sorted(combos))
    gift = args.gift or rng.choice(sorted(GIFTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_gender = args.elder_gender or rng.choice(["grandmother", "grandfather", "woman", "man"])
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    return StoryParams(theme, object_item, need, gift, child_name, child_gender, elder_name, elder_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        params.child_name, params.child_gender,
        params.elder_name, params.elder_gender,
        OBJECTS[params.object_item], NEEDS[params.need], GIFTS[params.gift],
        THEMES[params.theme], params.seed,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child that includes the word "convince" and a moment of sharing.',
        f"Tell a gentle village story where {f['child'].id} must decide whether to share {f['object_label']} after {f['elder'].id} speaks kindly.",
        f"Write a short folk-tale scene about bravery, where someone in need is helped because a child chooses to share.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, elder, obj, need = f["child"], f["elder"], f["object_item"], f["need"]
    qas = [
        ("Who is the story about?",
         f"It is about {child.id}, who was trying to decide whether to share {obj.label}. {elder.id} helped guide the choice with a kind warning."),
        ("What did the elder try to do?",
         f"{elder.id} tried to convince {child.id} to share. The elder spoke calmly because sharing was the bravest and kindest answer."),
    ]
    if f.get("shared"):
        qas.append((
            "What happened after the child shared?",
            f"The need was met, and the village became warmer and happier. Sharing turned one small thing into help for someone else."
        ))
        qas.append((
            "How was bravery shown in the story?",
            f"Bravery was shown when {child.id} gave up holding on tightly and shared {obj.label}. It took courage to choose kindness when keeping it would have been easier."
        ))
    else:
        qas.append((
            "How did the story end?",
            f"The child did not share, so the help did not come right away. The village had to look for another way to solve the need."
        ))
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["object_item"].tags) | set(world.facts["need"].tags)
    out = []
    if "food" in tags:
        out.append(("Why do people share food?", "People share food so someone hungry can eat and feel better. Sharing food is a caring thing to do."))
    if "warmth" in tags:
        out.append(("Why can a cloak matter on a cold day?", "A cloak keeps a person warm when the air is cold or windy. It can help someone stay safe and comfortable."))
    if "light" in tags:
        out.append(("Why is a lantern useful at dusk?", "A lantern helps people see when the sun is gone. It makes the dark path less scary and easier to follow."))
    out.append(("What does it mean to convince someone?", "To convince someone means to help them understand and agree with an idea. Kind words and a good reason can do that."))
    out.append(("What is bravery?", "Bravery means doing the right thing even when it feels hard or a little scary. A brave choice can be gentle, too."))
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
shareable(O) :- object(O), shareable_item(O).
can_convince(O, N) :- shareable(O), not precious(O), need(N).
shared_relief(C) :- child(C), shared(C).
outcome(shared) :- shared_relief(_), need_met.
outcome(withheld) :- child(_), not shared(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.precious:
            lines.append(asp.fact("precious", oid))
        if obj.shareable:
            lines.append(asp.fact("shareable_item", oid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show can_convince/2."))
    clingo = set(asp.atoms(model, "can_convince"))
    py = {(o, n) for _, o, n in valid_combos()}
    ok = clingo == py
    print("OK: ASP gate matches valid_combos()." if ok else f"MISMATCH: clingo={sorted(clingo)} python={sorted(py)}")
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, object_item=None, need=None, gift=None, child_name=None, child_gender=None, elder_name=None, elder_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return 0 if ok else 1


def valid_story_filters(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    return [c for c in valid_combos()
            if (args.theme is None or c[0] == args.theme)
            and (args.object_item is None or c[1] == args.object_item)
            and (args.need is None or c[2] == args.need)]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show can_convince/2."))
    return sorted(set(asp.atoms(model, "can_convince")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show can_convince/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible (theme, object, need) combos:\n")
        for theme, obj, need in valid_combos():
            print(f"  {theme:8} {obj:10} {need}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(t, o, n, "song", "Mira", "girl", "Grandma Willow", "grandmother"))
                   for t, o, n in valid_combos()[:5]]
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
