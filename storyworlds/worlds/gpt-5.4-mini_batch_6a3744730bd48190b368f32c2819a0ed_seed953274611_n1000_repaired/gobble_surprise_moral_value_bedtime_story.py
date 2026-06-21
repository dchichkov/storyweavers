#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gobble_surprise_moral_value_bedtime_story.py
============================================================================

A tiny bedtime-story world about a hungry bedtime creature, a surprising missing
snack, and a moral choice that makes the ending warm and calm.

Premise
-------
A child prepares for bed, a little snack goes missing, and a plush midnight
guest reveals itself in a gentle surprise. The story can end in one of two
reasonable ways: the child chooses honesty and shares kindly, or a selfish
choice leads to a small mess that is still repaired before sleep.

This world keeps the prose small, child-facing, and state-driven:
- typed entities with physical meters and emotional memes
- a forward-chained rule engine
- a Python reasonableness gate plus an inline ASP twin
- three Q&A sets grounded in world state, not rendered text

The seed words are reflected in the world:
- "gobble" is the creature's hungry action
- Surprise is the turn beat
- Moral Value is the lesson beat
- bedtime story is the style and ending mood
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
MORAL_MIN = 3
SURPRISE_MIN = 1
GOBBLE_LIMIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    sweet: bool
    shareable: bool
    crumbs: float
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
class Creature:
    id: str
    label: str
    phrase: str
    gobble_power: float
    crumbs_made: float
    surprise_line: str
    moral_line: str
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
class Response:
    id: str
    sense: int
    calm: int
    text: str
    fail: str
    qa_text: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_crumbs(world: World) -> list[str]:
    out: list[str] = []
    sn = world.facts.get("snack_id")
    if not sn or sn not in world.entities:
        return out
    snack = world.get(sn)
    if snack.meters["eaten"] < THRESHOLD:
        return out
    sig = ("crumbs", snack.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    snack.meters["crumbs"] += snack.attrs.get("crumbs", 1.0)
    out.append("__crumbs__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("surprise_seen"):
        return out
    if world.facts.get("snack_missing") and world.facts.get("creature_seen"):
        sig = ("surprise",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child = world.get("child")
        child.memes["surprise"] += 1
        child.memes["attention"] += 1
        out.append("__surprise__")
    return out


def _r_moral(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("moral_ready"):
        return out
    sig = ("moral",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["moral"] += 1
    out.append("__moral__")
    return out


CAUSAL_RULES = [Rule("crumbs", "physical", _r_crumbs), Rule("surprise", "social", _r_surprise), Rule("moral", "social", _r_moral)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def sweet_snacks() -> list[Snack]:
    return [s for s in SNACKS.values() if s.sweet and s.shareable]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, snack in SNACKS.items():
        for cid, creature in CREATURES.items():
            for rid, resp in RESPONSES.items():
                if snack.sweet and creature.gobble_power >= GOBBLE_LIMIT and resp.sense >= MORAL_MIN:
                    combos.append((sid, cid, rid))
    return combos


def predict(world: World, snack_id: str, creature_id: str) -> dict:
    sim = world.copy()
    snack = sim.get(snack_id)
    creature = sim.get(creature_id)
    snack.meters["eaten"] += 1
    creature.meters["gobbled"] += 1
    creature.memes["hunger"] += 1
    return {
        "crumbs": snack.attrs.get("crumbs", 0.0) if snack.meters["eaten"] >= THRESHOLD else 0.0,
        "surprise": True,
    }


def setup(world: World, child: Entity, parent: Entity, creature: Entity, snack: Entity) -> None:
    child.memes["calm"] += 1
    world.say(f"At bedtime, {child.id} tucked {snack.label_word if hasattr(snack, 'label_word') else snack.label} on the little table and yawned.")
    world.say(f"{parent.label_word.capitalize()} kissed {child.id}'s forehead and whispered that the room could stay quiet and cozy.")
    world.say(f"Then a soft bump came from the closet, where {creature.label} was hiding for a snack.")


def worry(world: World, child: Entity, snack: Entity, creature: Entity) -> None:
    child.memes["worry"] += 1
    world.say(f"{child.id} peeked under the blanket. The snack had gone missing, and that made the room feel much bigger.")
    world.say(f"From the dark, {creature.label} gave a sleepy grin and said, \"I gobble when I am hungry.\"")


def surprise_turn(world: World, child: Entity, creature: Entity, snack: Entity) -> None:
    world.facts["surprise_seen"] = True
    world.facts["creature_seen"] = True
    world.say(f"That was a surprise: the tiny night guest was only {creature.phrase}, not a scary monster at all.")
    world.say(f"It had gobbled the snack so fast that even the crumbs seemed to vanish into its cheeks.")


def choose_moral(world: World, child: Entity, response: Response, snack: Entity, creature: Entity) -> None:
    world.facts["moral_ready"] = True
    child.memes["moral"] += 1
    world.say(f"{child.id} took a breath and remembered the kind thing to do.")
    world.say(f'"Let\'s share next time," {child.id} said, and {child.pronoun()} handed over a spare cracker for the little gobbler.')


def moral_end(world: World, parent: Entity, snack: Entity, creature: Entity, response: Response) -> None:
    world.say(f"{parent.label_word.capitalize()} smiled because the room had become gentle again.")
    world.say(f"{parent.pronoun().capitalize()} used a plate and a napkin, and {response.text.replace(\"{snack}\", snack.label)}.")
    world.say(f"Before long, {creature.label} was full, the blanket was smooth again, and everyone felt ready for sleep.")


def selfish_branch(world: World, child: Entity, snack: Entity, creature: Entity) -> None:
    child.memes["mischief"] += 1
    snack.meters["eaten"] += 1
    creature.meters["gobbled"] += 1
    world.say(f"{child.id} tried to hide the last bite, but the cookie left sticky fingers and a little trail of crumbs.")
    world.say(f"{creature.label} gobbled too quickly, then sneezed so softly that the napkin slid to the floor.")
    world.say("So the bedtime surprise became a small mess, and everyone had to clean up before the light could be turned low again.")


def tell(snack: Snack, creature: Creature, response: Response, child_name: str = "Mina", child_gender: str = "girl", parent_type: str = "mother", choose_kindness: bool = True) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", label=child_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    s_ent = world.add(Entity(id="snack", type="snack", label=snack.label, attrs={"crumbs": snack.crumbs}, tags=set(snack.tags)))
    c_ent = world.add(Entity(id="creature", type="creature", label=creature.label, attrs={"phrase": creature.phrase}, tags=set(creature.tags)))
    world.facts.update(snack_id=s_ent.id, creature_id=c_ent.id)
    setup(world, child, parent, c_ent, s_ent)
    world.para()
    worry(world, child, s_ent, c_ent)
    if choose_kindness:
        surprise_turn(world, child, c_ent, s_ent)
        world.para()
        choose_moral(world, child, response, s_ent, c_ent)
        moral_end(world, parent, s_ent, c_ent, response)
    else:
        selfish_branch(world, child, s_ent, c_ent)
        world.para()
        world.say(f"{parent.label_word.capitalize()} did not scold. Instead, {parent.pronoun()} helped everyone wipe the table and breathe slowly.")
        world.say("After that, the room was tidy, the stars looked calmer, and the child knew that kindness makes bedtime easier.")
    world.facts["outcome"] = "kind" if choose_kindness else "messy"
    world.facts["snack"] = s_ent
    world.facts["creature"] = c_ent
    world.facts["response"] = response
    world.facts["child"] = child
    world.facts["parent"] = parent
    return world


SNACKS = {
    "cookie": Snack(id="cookie", label="a honey cookie", phrase="a honey cookie on the table", sweet=True, shareable=True, crumbs=1.0, tags={"sweet", "crumbs"}),
    "toast": Snack(id="toast", label="a buttered toast square", phrase="a buttered toast square on the plate", sweet=False, shareable=True, crumbs=0.5, tags={"toast"}),
    "berries": Snack(id="berries", label="a bowl of berries", phrase="a bowl of berries by the lamp", sweet=True, shareable=True, crumbs=0.25, tags={"berries", "sweet"}),
}

CREATURES = {
    "mouse": Creature(id="mouse", label="a tiny mouse", phrase="a tiny mouse in a moon-striped scarf", gobble_power=2.0, crumbs_made=1.0, surprise_line="a tiny mouse peeked out", moral_line="sharing felt nicer than hiding", tags={"mouse", "night"}),
    "bunny": Creature(id="bunny", label="a sleepy bunny", phrase="a sleepy bunny in a patchwork vest", gobble_power=2.5, crumbs_made=0.8, surprise_line="a sleepy bunny yawned", moral_line="gentle choices make the room soft", tags={"bunny", "night"}),
}

RESPONSES = {
    "share": Response(id="share", sense=4, calm=3, text="set the plate aside and shared the snack kindly", fail="set the plate aside, but the snack was already gone", qa_text="set the plate aside and shared the snack kindly", tags={"kind", "share"}),
    "napkin": Response(id="napkin", sense=3, calm=2, text="placed a napkin under the plate and wiped the crumbs away", fail="placed a napkin down too late to catch the crumbs", qa_text="placed a napkin under the plate and wiped the crumbs away", tags={"clean"}),
    "hide": Response(id="hide", sense=1, calm=1, text="tried to hide the mess under the blanket", fail="tried to hide the mess under the blanket, but it only made the room look lumpier", qa_text="tried to hide the mess under the blanket", tags={"weak"}),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Ada"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Eli", "Finn"]


@dataclass
class StoryParams:
    snack: str
    creature: str
    response: str
    child_name: str
    child_gender: str
    parent: str
    choose_kindness: bool = True
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


CURATED = [
    StoryParams(snack="cookie", creature="mouse", response="share", child_name="Mina", child_gender="girl", parent="mother", choose_kindness=True),
    StoryParams(snack="berries", creature="bunny", response="napkin", child_name="Owen", child_gender="boy", parent="father", choose_kindness=True),
    StoryParams(snack="cookie", creature="mouse", response="napkin", child_name="Luna", child_gender="girl", parent="mother", choose_kindness=False),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it is too weak for the bedtime lesson. Try a kinder, steadier choice.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < MORAL_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos() if (args.snack is None or c[0] == args.snack) and (args.creature is None or c[1] == args.creature) and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    snack, creature, response = rng.choice(sorted(combos))
    sn = SNACKS[snack]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    choose_kindness = True if args.kindness is None else args.kindness
    return StoryParams(snack=snack, creature=creature, response=response, child_name=name, child_gender=gender, parent=parent, choose_kindness=choose_kindness)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sn = SNACKS[f["snack"].id]
    cr = CREATURES[f["creature"].id]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "gobble" and ends with a moral choice.',
        f"Tell a gentle bedtime story where a child finds {sn.label} missing, discovers {cr.label}, and chooses kindness over hiding the crumbs.",
        f'Write a cozy surprise story about a snack, a tiny creature that likes to gobble, and a moral about sharing before sleep.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    snack: Entity = f["snack"]
    creature: Entity = f["creature"]
    resp: Response = f["response"]
    qa = [
        ("Who is the story about?", f"It is about {child.id}, the child at bedtime, and {parent.label_word}."),
        ("What happened to the snack?", f"The snack went missing from the little table, and then the creature gobbled it. That was the surprise that changed the bedtime mood."),
        ("What did the child learn?", f"{child.id} learned that kindness matters more than hiding a mistake. The calm choice made the room easier to sleep in."),
    ]
    if f.get("outcome") == "kind":
        qa.append(("How did the child solve the surprise?", f"{child.id} chose to share and clean up instead of hiding the crumbs. That made the moral lesson clear and kept bedtime peaceful."))
    else:
        qa.append(("What happened after the child made a selfish choice?", f"There was a small mess with crumbs and a wrinkled blanket. The grown-up helped tidy the room, and then the child understood why the kinder choice would have been better."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["snack"].tags) | set(world.facts["creature"].tags) | {"kindness", "bedtime"}
    out = []
    if "sweet" in tags:
        out.append(("Why do some snacks disappear so quickly?", "Sweet snacks can be very tempting, so hungry little creatures or children may gobble them up fast."))
    if "crumbs" in tags:
        out.append(("What are crumbs?", "Crumbs are tiny bits that break off food like cookies or toast. They can fall onto the table or floor."))
    out.append(("What does it mean to share?", "Sharing means giving some of what you have to someone else. It is a kind choice that helps everyone feel cared for."))
    out.append(("Why is bedtime supposed to be calm?", "Bedtime is calm so bodies and minds can rest. A quiet room helps children fall asleep more easily."))
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_story_choices() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
valid(Snack, Creature, Response) :- snack(Snack), creature(Creature), response(Response),
    sweet(Snack), gobble_power(Creature, P), gobble_limit(L), P >= L,
    sense(Response, S), moral_min(M), S >= M.
outcome(kind) :- valid(Snack, Creature, Response).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if s.sweet:
            lines.append(asp.fact("sweet", sid))
        if s.shareable:
            lines.append(asp.fact("shareable", sid))
        lines.append(asp.fact("crumbs", sid, s.crumbs))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("gobble_power", cid, c.gobble_power))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("gobble_limit", GOBBLE_LIMIT))
    lines.append(asp.fact("moral_min", MORAL_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke-tested ordinary generation.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a gobbling surprise and a moral choice.")
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--kindness", dest="kindness", action="store_true")
    ap.add_argument("--no-kindness", dest="kindness", action="store_false")
    ap.set_defaults(kindness=None)
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
    if args.response and RESPONSES[args.response].sense < MORAL_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.snack is None or c[0] == args.snack)
              and (args.creature is None or c[1] == args.creature)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    snack, creature, response = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    choose_kindness = True if args.kindness is None else args.kindness
    return StoryParams(snack=snack, creature=creature, response=response, child_name=name, child_gender=gender, parent=parent, choose_kindness=choose_kindness)


def generate(params: StoryParams) -> StorySample:
    if params.snack not in SNACKS or params.creature not in CREATURES or params.response not in RESPONSES:
        raise StoryError("Invalid params.")
    world = tell(SNACKS[params.snack], CREATURES[params.creature], RESPONSES[params.response], params.child_name, params.child_gender, params.parent, params.choose_kindness)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=[QAItem(q, a) for q, a in story_qa(world)], world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)], world=world)


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
        print(f"{len(combos)} valid combos:")
        for sn, cr, rs in combos:
            print(f"  {sn:8} {cr:8} {rs}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=("### variant %d" % (i + 1)) if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
