#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/companion_pyjamas_reverse_sharing_flashback_teamwork_fairy.py
=============================================================================================

A small fairy-tale story world about a child, a companion, pyjamas, a reverse
spell, sharing, flashback, and teamwork.

The core premise is simple: at bedtime, a child and a companion need to prepare
for a moonlit fairy errand. The child wants to keep a special pair of pyjamas,
but the companion remembers a lesson from an earlier night, and together they
use teamwork and sharing to undo a backward spell and make the night safe.

The world is designed to support short, complete stories with a clear beginning,
a state-driven turn, and a gentle ending image that proves what changed.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy"}
        male = {"boy", "father", "king", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    mood: str
    hiding_spot: str
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    sharing: bool = False
    wearable: bool = False
    reverseable: bool = False
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
class ReverseSpell:
    id: str
    label: str
    phrase: str
    strength: int
    break_text: str
    fix_text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_seen: bool = False

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
        clone.flashback_seen = self.flashback_seen
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


def _r_flashback(world: World) -> list[str]:
    out = []
    if world.facts.get("flashback_triggered") and not world.flashback_seen:
        world.flashback_seen = True
        out.append("__flashback__")
    return out


def _r_reverse(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    spell = world.entities.get("spell")
    companion = world.entities.get("companion")
    robe = world.entities.get("robe")
    if not child or not spell or not companion or not robe:
        return out
    if child.memes["teamwork"] < THRESHOLD:
        return out
    if companion.memes["sharing"] < THRESHOLD:
        return out
    if spell.meters["twisted"] < THRESHOLD:
        return out
    sig = ("reverse",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spell.meters["twisted"] = 0.0
    spell.meters["reversed"] = 1.0
    robe.meters["neat"] = 1.0
    child.memes["hope"] += 1
    companion.memes["hope"] += 1
    out.append("__reverse__")
    return out


CAUSAL_RULES = [Rule("flashback", _r_flashback), Rule("reverse", _r_reverse)]


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


def predict_reverse(world: World) -> bool:
    sim = world.copy()
    sim.facts["flashback_triggered"] = True
    sim.get("spell").meters["twisted"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("spell").meters["reversed"] >= THRESHOLD


def tell(setting: Setting, item: Item, spell: ReverseSpell,
         child_name: str = "Elin", child_gender: str = "girl",
         companion_name: str = "Pip", companion_gender: str = "fairy",
         parent_name: str = "Queen Mira", parent_gender: str = "queen") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    companion = world.add(Entity(id="companion", kind="character", type=companion_gender, label=companion_name, role="companion"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_gender, label=parent_name, role="parent"))
    robe = world.add(Entity(id="robe", kind="thing", type="robe", label=item.label))
    spell_ent = world.add(Entity(id="spell", kind="thing", type="spell", label=spell.label))
    child.memes["curiosity"] = 1.0
    companion.memes["sharing"] = 1.0
    child.memes["teamwork"] = 0.0
    companion.memes["teamwork"] = 0.0

    world.say(
        f"In {setting.place}, under a {setting.mood} moon, {child.label} and {companion.label} "
        f"made ready for a fairy errand. {child.label} wore {item.phrase}, and a silver lamp "
        f"glimmered near {setting.hiding_spot}."
    )
    world.say(
        f'"We must keep {item.label} safe," said {parent.label}. "A shared light is better than a lonely flame."'
    )

    world.para()
    child.memes["desire"] += 1
    companion.memes["sharing"] += 1
    world.say(
        f"{child.label} wanted to keep the pyjamas close, but the night air was chilly and the lamp was dim. "
        f"{companion.label} smiled and offered a half of {item.label} to share."
    )
    world.say(
        f'That was when {child.label} remembered a flashback: the night {setting.id} had gone backward, '
        f"and {parent.label_word} had taught them to hold hands and speak the spell together."
    )
    world.facts["flashback_triggered"] = True
    propagate(world, narrate=False)
    world.say(
        f'"I remember now," said {child.label}. "We reverse it by teamwork."'
    )
    world.say(
        f"{companion.label} nodded, and together they lifted the lamp, shared the light, and began the rhyme."
    )

    world.para()
    child.memes["teamwork"] += 1
    companion.memes["teamwork"] += 1
    child.memes["sharing"] += 1
    companion.memes["sharing"] += 1
    spell_ent.meters["twisted"] = 1.0
    if predict_reverse(world):
        propagate(world, narrate=False)
        world.say(
            f"{spell.break_text}. Then the spell unwound in a neat silver line, and the pyjamas stopped slipping backward."
        )
        world.say(
            f"{setting.hiding_spot} looked gentle again, and the two companions laughed as they tucked the shared blanket around their knees."
        )
    else:
        raise StoryError("This pairing cannot reverse the spell safely.")
    world.facts.update(
        child=child,
        companion=companion,
        parent=parent,
        robe=robe,
        spell=spell_ent,
        setting=setting,
        item=item,
        reverse_spell=spell,
        outcome="fixed",
    )
    return world


SETTINGS = {
    "tower": Setting(id="tower", place="the moonlit tower", mood="kind", hiding_spot="the stairs"),
    "garden": Setting(id="garden", place="the rose garden", mood="soft", hiding_spot="the hedge"),
    "cottage": Setting(id="cottage", place="the little cottage", mood="warm", hiding_spot="the hearth"),
}

ITEMS = {
    "pyjamas": Item(id="pyjamas", label="pyjamas", phrase="a pair of starry pyjamas", type="clothes", sharing=True, wearable=True, tags={"pyjamas", "sharing"}),
    "cloak": Item(id="cloak", label="cloak", phrase="a blue velvet cloak", type="clothes", sharing=False, wearable=True, tags={"cloak"}),
}

SPELLS = {
    "reverse": ReverseSpell(id="reverse", label="reverse spell", phrase="a backward spell", strength=1, break_text="The reverse spell listened", fix_text="the spell was undone", tags={"reverse"}),
    "mirror_reverse": ReverseSpell(id="mirror_reverse", label="mirror reverse", phrase="a mirror-turn spell", strength=1, break_text="The mirror-turn spell shivered", fix_text="the mirror righted itself", tags={"reverse"}),
}

GIRL_NAMES = ["Elin", "Mira", "Ivy", "Rose", "Nia"]
BOY_NAMES = ["Finn", "Pip", "Otis", "Jory", "Tomas"]


@dataclass
class StoryParams:
    setting: str
    item: str
    spell: str
    child_name: str
    child_gender: str
    companion_name: str
    companion_gender: str
    parent_name: str
    parent_gender: str
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
    StoryParams(setting="tower", item="pyjamas", spell="reverse", child_name="Elin", child_gender="girl", companion_name="Pip", companion_gender="fairy", parent_name="Queen Mira", parent_gender="queen"),
    StoryParams(setting="garden", item="pyjamas", spell="mirror_reverse", child_name="Finn", child_gender="boy", companion_name="Ivy", companion_gender="fairy", parent_name="King Arlo", parent_gender="king"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid, item in ITEMS.items():
            for spid in SPELLS:
                if item.sharing and "reverse" in spid:
                    combos.append((sid, iid, spid))
    return combos


def explain_rejection(item: Item, spell: ReverseSpell) -> str:
    if not item.sharing:
        return f"(No story: {item.label} does not support sharing, so the fairy-tale teamwork has nowhere to land.)"
    if "reverse" not in spell.id:
        return f"(No story: this spell is not a reverse spell, and the seed asks for a backward-turn story.)"
    return "(No story: this combination does not fit the fairy tale world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about companion, pyjamas, reverse, sharing, flashback, teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--parent")
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
    if args.item and args.spell:
        if (args.setting or next(iter(SETTINGS)), args.item, args.spell) not in valid_combos():
            raise StoryError(explain_rejection(ITEMS[args.item], SPELLS[args.spell]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.spell is None or c[2] == args.spell)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, spell = rng.choice(sorted(combos))
    child_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    companion_name = args.companion or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child_name])
    parent_name = args.parent or rng.choice(["Queen Mira", "King Arlo", "Lady June"])
    child_gender = "girl" if child_name in GIRL_NAMES else "boy"
    companion_gender = "fairy"
    return StoryParams(setting=setting, item=item, spell=spell, child_name=child_name, child_gender=child_gender,
                       companion_name=companion_name, companion_gender=companion_gender, parent_name=parent_name, parent_gender="queen")


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.item not in ITEMS or params.spell not in SPELLS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], ITEMS[params.item], SPELLS[params.spell],
                 child_name=params.child_name, child_gender=params.child_gender,
                 companion_name=params.companion_name, parent_name=params.parent_name, parent_gender=params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a small child that includes the words "{f["item"].label}", "companion", and "reverse".',
        f"Tell a bedtime fairy story about a companion who helps reverse a spell by sharing light and working together.",
        f"Write a gentle tale with flashback and teamwork where pyjamas matter and the ending feels warm and safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    c = world.facts["child"]
    comp = world.facts["companion"]
    item = world.facts["item"]
    spell = world.facts["reverse_spell"]
    setting = world.facts["setting"]
    return [
        ("Who is the story about?", f"It is about {c.label} and {comp.label}, two companions in {setting.place}. They work together in a fairy-tale night."),
        (f"What special item was in the story?", f"The special item was {item.phrase}. It mattered because the story needed sharing and careful bedtime preparation."),
        ("Why did they remember the flashback?", f"They remembered an earlier night when the lesson had already been learned. That memory helped them choose teamwork instead of panic."),
        ("How did they solve the problem?", f"They shared the light, spoke the reverse spell together, and used teamwork to untwist the backward magic. Because they helped each other, the pyjamas stayed neat and the night became calm."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is sharing?", "Sharing means letting someone else use or enjoy something with you. In a story, it often helps friends work together kindly."),
        ("What is a flashback?", "A flashback is a moment in a story that goes back to something that happened before. It helps a character remember an important lesson."),
        ("What is teamwork?", "Teamwork is when people help each other to do something together. The job gets easier when everyone does a little part."),
        ("What does reverse mean?", "Reverse means to turn something the other way or put it back the way it was. In fairy tales, a reverse spell can undo a mistake or a trick."),
        ("What are pyjamas for?", "Pyjamas are soft clothes people wear for sleeping. They help bedtime feel cozy and warm."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(s) :- fact_setting(s).
item(i) :- fact_item(i), shares(i).
spell(sp) :- fact_spell(sp), reverseish(sp).
valid(S,I,SP) :- setting(S), item(I), spell(SP).
reverseish(reverse).
reverseish(mirror_reverse).
shares(pyjamas).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("fact_setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("fact_item", iid))
        if item.sharing:
            lines.append(asp.fact("shares", iid))
    for spid in SPELLS:
        lines.append(asp.fact("fact_spell", spid))
        if "reverse" in spid:
            lines.append(asp.fact("reverseish", spid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: ASP parity and generate smoke test passed.")
    return rc


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
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
