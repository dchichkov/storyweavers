#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/moccasin_bad_ending_curiosity_foreshadowing_myth.py
====================================================================================

A small myth-style storyworld about a child who is warned not to enter a sacred
place, keeps poking at a mysterious moccasin, and learns too late why the signs
were there. The world is built to support curiosity, foreshadowing, and a bad
ending that still feels like a complete tiny myth.

The setting is deliberately compact:
- a river shrine with a dim cave and a stone idol
- a child, a guardian, and a river spirit
- a single strange moccasin that should not be touched

The story model tracks physical state in meters and emotional state in memes.
A forward rule engine changes the world when the child ignores the warning.
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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "guardian"}
        male = {"boy", "father", "man", "guardian"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Place:
    id: str
    label: str
    holiness: int = 0
    dark: bool = False
    water_nearby: bool = False
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
class Charm:
    id: str
    label: str
    phrase: str
    warns: str
    forbidden: bool = True
    leads_to: str = "trouble"
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Omen:
    id: str
    label: str
    phrase: str
    hint: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class OutcomeAid:
    id: str
    label: str
    power: int
    text: str
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
class StoryParams:
    place: str = "shrine"
    charm: str = "moccasin"
    omen: str = "owl"
    aid: str = "lamp"
    child_name: str = "Mira"
    child_gender: str = "girl"
    guardian_name: str = "Nana"
    guardian_gender: str = "woman"
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


def _r_spirit_wakes(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["defiance"] < THRESHOLD:
        return out
    if ("spirit", "wake") in world.fired:
        return out
    world.fired.add(("spirit", "wake"))
    world.get("shrine").meters["danger"] += 1
    child.memes["fear"] += 1
    out.append("__omen__")
    return out


def _r_trap_closes(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    charm = world.get("charm")
    shrine = world.get("shrine")
    if charm.meters["touched"] < THRESHOLD or shrine.meters["danger"] < THRESHOLD:
        return out
    if ("trap", "close") in world.fired:
        return out
    world.fired.add(("trap", "close"))
    child.meters["lost"] += 1
    child.memes["regret"] += 1
    out.append("__trap__")
    return out


CAUSAL_RULES = [Rule("spirit_wakes", _r_spirit_wakes), Rule("trap_closes", _r_trap_closes)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for item in produced:
            world.say(item)
    return produced


def hazard_at_risk(charm: Charm, place: Place) -> bool:
    return charm.forbidden and place.dark


def sensible_aids() -> list[OutcomeAid]:
    return [a for a in AIDS.values() if a.power >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, charm in CHARMS.items():
            for aid_id, aid in AIDS.items():
                if hazard_at_risk(charm, place) and aid.power >= 2:
                    combos.append((pid, cid, aid_id))
    return combos


def predict(world: World, touch: bool = False) -> dict:
    sim = world.copy()
    if touch:
        sim.get("charm").meters["touched"] += 1
        propagate(sim, narrate=False)
    return {
        "danger": sim.get("shrine").meters["danger"],
        "lost": sim.get("child").meters["lost"],
    }


def tell_world(place: Place, charm: Charm, omen: Omen, aid: OutcomeAid,
               child_name: str, child_gender: str,
               guardian_name: str, guardian_gender: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="curious child"))
    guardian = world.add(Entity(id="guardian", kind="character", type=guardian_gender, label=guardian_name, role="guardian"))
    shrine = world.add(Entity(id="shrine", kind="place", type="place", label=place.label))
    c = world.add(Entity(id="charm", kind="thing", type="thing", label=charm.label))
    o = world.add(Entity(id="omen", kind="thing", type="thing", label=omen.label))
    a = world.add(Entity(id="aid", kind="thing", type="thing", label=aid.label))

    child.memes["curiosity"] = 2.0
    guardian.memes["care"] = 2.0
    world.facts["omens"] = omen.hint

    world.say(f"Long ago, beside the river, stood {place.label}, where the stones listened and the water kept old secrets.")
    world.say(f"There the child {child_name} found {charm.phrase}. It was small enough to fit in two hands, but strange enough to make the heart itch with questions.")
    world.say(f"Near it waited {omen.phrase}, a sign like a whisper. {omen.hint}")
    world.para()
    world.say(f"The guardian {guardian_name} lifted a hand. \"Do not take what belongs to the shrine,\" {guardian_name} said. \"Some doors open only once.\"")
    world.say(f"But the child only stared harder. Curiosity rose like a bright spark in a dry nest.")
    child.memes["curiosity"] += 1
    child.memes["defiance"] += 1

    world.para()
    if predict(world, touch=True)["danger"] >= THRESHOLD:
        world.say(f"{child_name} reached for {charm.label} anyway, and the river went still as if it were holding its breath.")
        c.meters["touched"] += 1
        propagate(world, narrate=False)
        world.say(f"When the {charm.label} was lifted, the old stones trembled. The hidden door shut with a sound like a deep drum, and the child heard the spirit's anger in the dark.")
        shrine.meters["danger"] += 1
        child.memes["fear"] += 1
        world.para()
        if aid.power >= 2:
            world.say(f"The guardian rushed in with {aid.text}, but the warning had come too late; the seal was already broken.")
            world.say(f"They escaped with their lives, yet the shrine never welcomed {child_name} again. The river kept the {charm.label}, and the child kept the sorrow.")
            child.meters["lost"] += 1
            child.memes["regret"] += 1
        else:
            world.say(f"No clever light could undo it. The child left with empty hands and a heavy heart.")
    else:
        world.say(f"{child_name} listened, and the story would have ended gently; but this world is for the darker turning, so that path is not taken.")

    world.facts.update(
        child=child,
        guardian=guardian,
        shrine=shrine,
        charm=c,
        omen=o,
        aid=a,
        place=place,
        charm_cfg=charm,
        omen_cfg=omen,
        aid_cfg=aid,
        outcome="bad",
        warned=True,
    )
    return world


PLACES = {
    "shrine": Place(id="shrine", label="the river shrine", holiness=3, dark=True, water_nearby=True),
    "cave": Place(id="cave", label="the moon cave", holiness=2, dark=True, water_nearby=False),
}

CHARMS = {
    "moccasin": Charm(id="moccasin", label="moccasin", phrase="a single moccasin on a stone shelf", warns="the moccasin should not be touched", leads_to="a closed door"),
}

OMENS = {
    "owl": Omen(id="owl", label="owl", phrase="an owl on the roof beam", hint="It stared at the child as if it knew the end of the path."),
    "mist": Omen(id="mist", label="mist", phrase="a ribbon of mist over the river", hint="It curled away from the shelf, like breath leaving a sleeping face."),
}

AIDS = {
    "lamp": OutcomeAid(id="lamp", label="lamp", power=1, text="a small lamp"),
    "torch": OutcomeAid(id="torch", label="torch", power=2, text="a bright torch"),
    "lantern": OutcomeAid(id="lantern", label="lantern", power=3, text="a strong lantern"),
}

GIRL_NAMES = ["Mira", "Sana", "Lila", "Nora", "Aya"]
BOY_NAMES = ["Kiran", "Toma", "Bela", "Ravi", "Oren"]  # mixed pool intentionally mythic
TRAITS = ["curious", "bold", "restless", "wondering"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld of curiosity, foreshadowing, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["woman", "man"])
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
    if args.place and args.charm and not hazard_at_risk(CHARMS[args.charm], PLACES[args.place]):
        raise StoryError("No story: this place is not dark enough for the forbidden touch to matter.")
    if args.aid and AIDS[args.aid].power < 2:
        raise StoryError("No story: the chosen aid is too weak for the mythic danger.")
    place = args.place or rng.choice(list(PLACES))
    charm = args.charm or "moccasin"
    omen = args.omen or rng.choice(list(OMENS))
    aid = args.aid or rng.choice([k for k, v in AIDS.items() if v.power >= 2])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["woman", "man"])
    guardian_name = "Nana" if guardian == "woman" else "Taro"
    return StoryParams(place=place, charm=charm, omen=omen, aid=aid,
                       child_name=name, child_gender=gender,
                       guardian_name=guardian_name, guardian_gender=guardian)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child that includes the word "{f["charm_cfg"].label}".',
        f"Tell a story about curiosity and warning signs beside {f['place'].label}, ending badly because the child does not listen.",
        f"Write a short myth with foreshadowing: an omen warns of trouble, but the child still reaches for the {f['charm_cfg'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    charm = f["charm_cfg"]
    place = f["place"]
    omen = f["omen_cfg"]
    return [
        QAItem(
            question=f"What did the child want to touch?",
            answer=f"The child wanted to touch the {charm.label}. It sat on the shrine shelf and looked harmless, which made it tempting.",
        ),
        QAItem(
            question=f"How did the story show foreshadowing?",
            answer=f"It showed foreshadowing with {omen.phrase}. {omen.hint} That sign hinted that the choice would end in trouble before the child reached for the moccasin.",
        ),
        QAItem(
            question=f"Why did the ending turn bad?",
            answer=f"The ending turned bad because {child.label_word} ignored {guardian.label_word}'s warning and took the {charm.label} anyway. Once the old seal broke, the shrine became dangerous and the child lost the chance to return things to the way they were.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {place.label}, beside the river. The place mattered because it was sacred, dark, and full of old rules.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moccasin?",
            answer="A moccasin is a soft shoe made of leather or similar material. In myths, a single strange moccasin can feel like a clue or a warning.",
        ),
        QAItem(
            question="What does an omen do in a story?",
            answer="An omen is a sign that hints that something important may happen later. It helps the reader feel the coming trouble before it arrives.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more and ask questions. It can lead to discovery, but it can also lead to trouble if it ignores a warning.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
hazard(P, C) :- place(P), charm(C), dark(P), forbidden(C).
valid(P, C, A) :- hazard(P, C), aid(A), power(A, N), N >= 2.
bad_end :- hazard(P, C), touch(C), seal_breaks.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.forbidden:
            lines.append(asp.fact("forbidden", cid))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("power", aid, a.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = 1
        print("MISMATCH in the gate:")
        print("  only python:", sorted(py - cl))
        print("  only clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke-tested normal generation.")
    except Exception as err:  # noqa: BLE001
        print(f"FAILED: normal generation crashed: {err}")
        return 1
    return ok


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(place="shrine", charm="moccasin", omen="owl", aid="torch", child_name="Mira", child_gender="girl", guardian_name="Nana", guardian_gender="woman"),
        StoryParams(place="cave", charm="moccasin", omen="mist", aid="lantern", child_name="Kiran", child_gender="boy", guardian_name="Taro", guardian_gender="man"),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.charm not in CHARMS or params.omen not in OMENS or params.aid not in AIDS:
        raise StoryError("Invalid story parameters.")
    world = tell_world(PLACES[params.place], CHARMS[params.charm], OMENS[params.omen], AIDS[params.aid],
                       params.child_name, params.child_gender, params.guardian_name, params.guardian_gender)
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
    StoryParams(place="shrine", charm="moccasin", omen="owl", aid="torch", child_name="Mira", child_gender="girl", guardian_name="Nana", guardian_gender="woman"),
    StoryParams(place="cave", charm="moccasin", omen="mist", aid="lantern", child_name="Kiran", child_gender="boy", guardian_name="Taro", guardian_gender="man"),
]


def explain_rejection() -> str:
    return "No story: this small myth only supports the dark shrine/cave and the forbidden moccasin."


def build_parser_wrapper() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
