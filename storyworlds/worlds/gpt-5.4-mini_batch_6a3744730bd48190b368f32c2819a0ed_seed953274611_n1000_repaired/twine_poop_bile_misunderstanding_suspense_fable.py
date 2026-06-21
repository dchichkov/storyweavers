#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/twine_poop_bile_misunderstanding_suspense_fable.py
===================================================================================

A small fable-style storyworld about a barnyard misunderstanding:
a careful child or young animal finds twine, sees poop and bile-like mess,
and thinks something dreadful has happened. Suspense builds while the world
model tracks what is actually happening, then a wise helper clears up the mix-up
and the ending proves the change.

The story aims for a child-facing fable tone: concrete animals, a small lesson,
a tense middle, and a calm ending image.
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
        female = {"girl", "mother", "woman", "hen", "goat"}
        male = {"boy", "father", "man", "ram", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class ObjectCfg:
    id: str
    label: str
    smell: str = ""
    use: str = ""
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
class CreatureCfg:
    id: str
    label: str
    type: str
    role: str
    traits: list[str] = field(default_factory=list)
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
class SituationCfg:
    id: str
    place: str
    nook: str
    weather: str
    lesson: str
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
    place: str
    child: str
    child_type: str
    child_role: str
    helper: str
    helper_type: str
    helper_role: str
    object_id: str
    mess_id: str
    twist: str
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["fear"] >= THRESHOLD and ("fear", e.id) not in world.fired:
            world.fired.add(("fear", e.id))
            out.append(f"{e.id} held still, listening to the barn’s small creaks.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child and child.memes["misread"] >= THRESHOLD and ("misread", child.id) not in world.fired:
        world.fired.add(("misread", child.id))
        child.memes["worry"] += 1
        out.append("__misunderstanding__")
    return out


RULES = [Rule("suspense", _r_suspense), Rule("misunderstanding", _r_misunderstanding)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                lines.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in lines:
            world.say(s)
    return lines


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SITUATIONS:
        for child_id in CHILDREN:
            for obj_id in OBJECTS:
                if place == "pond" and obj_id == "twine" and child_id != "goat":
                    combos.append((place, child_id, obj_id))
                if place == "barn" and obj_id in {"twine", "bile"}:
                    combos.append((place, child_id, obj_id))
    return combos


def reasonableness_gate(place: str, child_id: str, obj_id: str) -> bool:
    return (place, child_id, obj_id) in valid_combos()


def is_misunderstanding(obj: ObjectCfg, mess: ObjectCfg) -> bool:
    return obj.id == "twine" and mess.id in {"poop", "bile"}


def situation_text(place: str) -> str:
    return SITUATIONS[place].place


def predict(world: World, obj_id: str, mess_id: str) -> dict:
    sim = world.copy()
    sim.get("child").memes["misread"] += 1
    sim.get("child").meters["fear"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").meters["fear"],
        "worry": sim.get("child").memes["worry"],
    }


def tell_setup(world: World, child: Entity, helper: Entity, place: SituationCfg) -> None:
    child.memes["curious"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At {place.place}, {child.id} found a thin piece of twine near {place.nook}. "
        f"The air was quiet, and even the hens seemed to be listening."
    )
    world.say(
        f"Then {child.id} saw {world.facts['mess'].label} beside it, and a bitter smell of bile drifted by."
    )


def worry(world: World, child: Entity, obj: ObjectCfg, mess: ObjectCfg, place: SituationCfg) -> None:
    child.meters["fear"] += 1
    child.memes["misread"] += 1
    world.say(
        f"{child.id}'s heart jumped. 'Oh no,' {child.pronoun()} whispered, 'the twine must have tied up the mess.'"
    )
    world.say(
        f"The little one thought the twine had caused the {mess.id}, and that made the barn feel suddenly large."
    )


def calm_helper(world: World, helper: Entity, child: Entity, obj: ObjectCfg, mess: ObjectCfg) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"But {helper.id} stepped closer with slow hooves and a steady voice. "
        f"'Look again,' {helper.pronoun()} said. 'Twine is just twine. It can tie hay, not make a sickness.'"
    )
    world.say(
        f"{helper.id} pointed to the {mess.id}. 'This is only a messy accident, and the bile came from a queasy stomach, not from the string.'"
    )


def reveal(world: World, child: Entity, helper: Entity, place: SituationCfg) -> None:
    child.memes["misread"] = 0.0
    child.meters["fear"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f"{child.id} blinked, then breathed out. The twine was harmless after all, and the scary thought shrank away."
    )
    world.say(
        f"Together they washed the spot, coiled the twine neatly, and left {place.nook} quiet again."
    )


def lesson(world: World, child: Entity, helper: Entity, place: SituationCfg) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{helper.id} smiled. 'A hasty guess can make a small problem look huge,' {helper.pronoun()} said. "
        f"'First look, then worry.'"
    )
    world.say(
        f"So {child.id} learned to ask before fearing. By sunset, the barn smelled of straw instead of alarm."
    )


def tell(place: SituationCfg, child_cfg: CreatureCfg, helper_cfg: CreatureCfg,
         obj: ObjectCfg, mess: ObjectCfg, twist: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_cfg.type, role=child_cfg.role, traits=child_cfg.traits))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, role=helper_cfg.role, traits=helper_cfg.traits))
    world.add(Entity(id="twine", type="thing", label="twine"))
    world.add(Entity(id="poop", type="thing", label="poop"))
    world.add(Entity(id="bile", type="thing", label="bile"))
    world.facts.update(place=place, child=child_cfg, helper=helper_cfg, object=obj, mess=mess, twist=twist)

    tell_setup(world, child, helper, place)
    world.para()
    worry(world, child, obj, mess, place)
    propagate(world, narrate=False)
    world.para()
    calm_helper(world, helper, child, obj, mess)
    reveal(world, child, helper, place)
    lesson(world, child, helper, place)
    world.facts.update(outcome="resolved", promised=True)
    return world


SITUATIONS = {
    "barn": SituationCfg(id="barn", place="the old barn", nook="the hayloft", weather="still", lesson="look before fear", tags={"barn"}),
    "yard": SituationCfg(id="yard", place="the farmyard", nook="the gatepost", weather="cool", lesson="look before fear", tags={"yard"}),
    "orchard": SituationCfg(id="orchard", place="the orchard shed", nook="the apple crates", weather="soft", lesson="look before fear", tags={"orchard"}),
}

CHILDREN = {
    "lamb": CreatureCfg(id="lamb", label="lamb", type="girl", role="young one", traits=["curious", "gentle"], tags={"child"}),
    "goat": CreatureCfg(id="goat", label="goat", type="boy", role="young one", traits=["suspicious", "quick"], tags={"child"}),
}

HELPERS = {
    "donkey": CreatureCfg(id="donkey", label="donkey", type="thing", role="elder helper", traits=["patient", "wise"], tags={"helper"}),
    "hen": CreatureCfg(id="hen", label="hen", type="girl", role="elder helper", traits=["wise", "calm"], tags={"helper"}),
}

OBJECTS = {
    "twine": ObjectCfg(id="twine", label="twine", smell="dry straw", use="tie hay", tags={"twine"}),
    "poop": ObjectCfg(id="poop", label="poop", smell="sharp", use="mess", tags={"poop"}),
    "bile": ObjectCfg(id="bile", label="bile", smell="bitter", use="mess", tags={"bile"}),
}

TWISTS = {
    "misunderstanding": "misunderstanding",
    "suspense": "suspense",
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable about a child in {f["place"].place} who sees twine, poop, and bile and thinks the twine caused the mess.',
        f"Tell a suspenseful fable where {f['child'].id} misunderstands {f['object'].label} near {f['mess'].label}, and a wise helper clears up the mistake.",
        f'Write a short moral story that includes the words "twine", "poop", and "bile" and ends with a gentle lesson about careful noticing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    obj = f["object"]
    mess = f["mess"]
    place = f["place"]
    return [
        QAItem(
            question="What did the child think at first?",
            answer=f"{child.id} thought the twine had caused the mess. That frightened {child.id}, because the barn felt dark and the bile-smell made the guess seem worse."
        ),
        QAItem(
            question="How did the helper fix the misunderstanding?",
            answer=f"{helper.id} asked for a second look and explained that twine cannot make sickness. The poop and bile were just messes to clean, so the fear could fade."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They cleaned the spot, coiled the twine neatly, and left {place.place} calm again. The child learned to look carefully before making a scary guess."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is twine?",
            answer="Twine is a thin string made for tying things together. People use it to bundle hay, hold packages, or fasten simple things."
        ),
        QAItem(
            question="What is poop?",
            answer="Poop is waste that living things leave behind. It is messy, so it should be cleaned up carefully."
        ),
        QAItem(
            question="What is bile?",
            answer="Bile is a bitter fluid inside animals and people that helps with digestion. If someone feels sick, bile can sometimes come up and smell sharp."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", child="lamb", child_type="girl", child_role="young one", helper="donkey", helper_type="thing", helper_role="elder helper", object_id="twine", mess_id="poop", twist="misunderstanding"),
    StoryParams(place="yard", child="goat", child_type="boy", child_role="young one", helper="hen", helper_type="girl", helper_role="elder helper", object_id="twine", mess_id="bile", twist="suspense"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    places = list(SITUATIONS.keys())
    children = list(CHILDREN.keys())
    helpers = list(HELPERS.keys())
    objects = list(OBJECTS.keys())
    messes = ["poop", "bile"]
    if args.place and args.place not in SITUATIONS:
        raise StoryError("Unknown place.")
    if args.child and args.child not in CHILDREN:
        raise StoryError("Unknown child.")
    if args.helper and args.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if args.object and args.object not in OBJECTS:
        raise StoryError("Unknown object.")
    if args.mess and args.mess not in OBJECTS:
        raise StoryError("Unknown mess.")

    place = args.place or rng.choice(places)
    child_id = args.child or rng.choice(children)
    helper_id = args.helper or rng.choice(helpers)
    obj_id = args.object or "twine"
    mess_id = args.mess or rng.choice(messes)
    if not reasonableness_gate(place, child_id, obj_id):
        raise StoryError("No reasonable misunderstanding here.")
    return StoryParams(
        place=place,
        child=child_id,
        child_type=CHILDREN[child_id].type,
        child_role=CHILDREN[child_id].role,
        helper=helper_id,
        helper_type=HELPERS[helper_id].type,
        helper_role=HELPERS[helper_id].role,
        object_id=obj_id,
        mess_id=mess_id,
        twist=args.twist or "misunderstanding",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SITUATIONS:
        raise StoryError("Invalid place.")
    if params.child not in CHILDREN or params.helper not in HELPERS:
        raise StoryError("Invalid cast.")
    if params.object_id not in OBJECTS or params.mess_id not in OBJECTS:
        raise StoryError("Invalid objects.")
    if not reasonableness_gate(params.place, params.child, params.object_id):
        raise StoryError("The requested combination does not support the fable.")
    if params.object_id != "twine":
        raise StoryError("This world needs twine as the suspicious object.")
    if params.mess_id not in {"poop", "bile"}:
        raise StoryError("This world needs poop or bile as the mess.")

    place = SITUATIONS[params.place]
    child_cfg = CHILDREN[params.child]
    helper_cfg = HELPERS[params.helper]
    obj = OBJECTS[params.object_id]
    mess = OBJECTS[params.mess_id]
    world = tell(place, child_cfg, helper_cfg, obj, mess, params.twist)
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
misunderstanding(C) :- child(C), sees_twine(C), sees_mess(C), thinks_caused(C, twine, C2), mess(C2).
suspense(C) :- fear(C).
resolved(C) :- understanding(C).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for sid in SITUATIONS:
        lines.append(asp.fact("place", sid))
    for cid in CHILDREN:
        lines.append(asp.fact("child", cid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
        if oid == "twine":
            lines.append(asp.fact("seems_suspicious", oid))
    lines.append(asp.fact("reasonableness", "twine"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    # smoke test ordinary generation
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        return 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("FAIL: ASP and Python combo gates diverge.")
        rc = 1
    else:
        print(f"OK: gate parity over {len(valid_combos())} combos.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld about twine, poop, bile, misunderstanding, and suspense.")
    ap.add_argument("--place", choices=SITUATIONS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--mess", choices=["poop", "bile"])
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode not used for listing in this small world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
