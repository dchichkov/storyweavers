#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rifle_transformation_magic_sharing_mystery.py
=============================================================================

A standalone story world for a small mystery about an old rifle-shaped prop,
a little bit of magic, a change in form, and a sharing lesson.

This world is intentionally child-facing and keeps the "rifle" as a harmless
antique prop in a locked case at a museum of old stage costumes. The mystery
is that the prop changes shape when two children share it kindly and solve the
puzzle of who the missing sparkle belongs to.

The simulated world uses typed entities, physical meters, emotional memes,
forward-chained causal rules, a reasonableness gate, QA generation from state,
and an inline ASP twin for parity checks.
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
MYSTERY_MIN = 1
MAGIC_MIN = 1
SHARING_MIN = 1


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
    magical: bool = False
    transformable: bool = False
    sharable: bool = False

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
        return self.label or self.type
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
class MysteryItem:
    id: str
    label: str
    phrase: str
    transformed_into: str
    clue: str
    tags: set[str] = field(default_factory=set)
    sharable: bool = True
    transformable: bool = True
    magical: bool = True
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
class Setting:
    id: str
    place: str
    dark_spot: str
    keeper: str
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
class Spell:
    id: str
    incantation: str
    effect: str
    share_needed: bool
    clarity: int
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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery_seen") and not world.facts.get("clue_shared"):
        for kid in world.characters():
            kid.memes["wonder"] += 1
        sig = ("tension",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__tension__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("spell_used"):
        return out
    relic = world.get("rifle")
    if relic.meters["spark"] < THRESHOLD:
        return out
    sig = ("transform", relic.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    relic.meters["changed"] += 1
    out.append("__transform__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("shared"):
        return out
    for kid in world.characters():
        kid.memes["trust"] += 1
        kid.memes["joy"] += 1
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__share__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("tension", "social", _r_tension),
    Rule("transform", "magic", _r_transform),
    Rule("share", "social", _r_share),
]


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


def reasonableness_gate(item: MysteryItem, spell: Spell) -> bool:
    return item.transformable and item.magical and spell.clarity >= MAGIC_MIN


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for item_id, item in ITEMS.items():
        for spell_id, spell in SPELLS.items():
            if reasonableness_gate(item, spell):
                combos.append((item_id, spell_id))
    return combos


def setting_setup(world: World, setting: Setting, child1: Entity, child2: Entity, keeper: Entity) -> None:
    child1.memes["curiosity"] += 1
    child2.memes["curiosity"] += 1
    world.say(
        f"On a windy afternoon, {child1.id} and {child2.id} wandered into "
        f"{setting.place}. In the dim room, a glass case stood near {setting.dark_spot}, "
        f"and {keeper.label_word} watched over the old things."
    )
    world.say(
        f"Inside the case was a strange little rifle-shaped prop, old enough to feel "
        f"like a clue instead of a toy."
    )


def notice_mystery(world: World, child1: Entity, child2: Entity, item: MysteryItem) -> None:
    world.facts["mystery_seen"] = True
    child1.memes["mystery"] += 1
    child2.memes["mystery"] += 1
    world.say(
        f"{child1.id} leaned closer. \"Why is the {item.label} here?\" "
        f"{child2.id} whispered that it looked like something from a puzzle box."
    )


def find_clue(world: World, child2: Entity, item: MysteryItem) -> None:
    child2.memes["hope"] += 1
    world.say(
        f"Under the case, {child2.id} spotted a tiny note: {item.clue}. "
        f"It felt like the room was waiting for someone to read it out loud."
    )


def share_spell(world: World, child1: Entity, child2: Entity, spell: Spell, item: MysteryItem) -> None:
    world.facts["shared"] = True
    world.facts["spell_used"] = True
    child1.meters["holding"] += 1
    child2.meters["holding"] += 1
    world.get("rifle").meters["spark"] += 1
    world.say(
        f'"Maybe if we share it," {child1.id} said. {child2.id} nodded, and together '
        f'they spoke the words: "{spell.incantation}."'
    )
    world.say(
        f"The old prop gave a soft glimmer, as if it had been listening."
    )


def transform(world: World, item: MysteryItem, spell: Spell) -> None:
    relic = world.get("rifle")
    relic.label = item.transformed_into
    relic.attrs["form"] = item.transformed_into
    world.say(
        f"Then the {item.label} changed shape. The rifle-like prop folded into "
        f"{item.transformed_into}, and the mystery finally made sense."
    )


def explain_sharing(world: World, keeper: Entity, child1: Entity, child2: Entity, item: MysteryItem) -> None:
    child1.memes["relief"] += 1
    child2.memes["relief"] += 1
    child1.memes["sharing"] += 1
    child2.memes["sharing"] += 1
    world.facts["clue_shared"] = True
    world.say(
        f"{keeper.label_word.capitalize()} came over smiling. \"You found the clue by sharing,\" "
        f"{keeper.pronoun()} said. \"When two people carry a mystery together, it gets clearer.\""
    )
    world.say(
        f"The note meant the prop was meant to change shape only when it was handled kindly "
        f"and shared between friends."
    )


def ending_image(world: World, child1: Entity, child2: Entity, item: MysteryItem) -> None:
    world.say(
        f"{child1.id} and {child2.id} set the transformed {item.transformed_into} back on the table, "
        f"one on each side, grinning at the solved puzzle. The room felt bright again, "
        f"and the old rifle-shaped mystery had become a shared secret instead of a worry."
    )


def tell(setting: Setting, item: MysteryItem, spell: Spell, name1: str, name2: str) -> World:
    world = World()
    kid1 = world.add(Entity(id=name1, kind="character", type="girl", role="finder"))
    kid2 = world.add(Entity(id=name2, kind="character", type="boy", role="helper"))
    keeper = world.add(Entity(id=setting.keeper, kind="character", type="woman", role="keeper", label="the keeper"))
    relic = world.add(Entity(id="rifle", kind="thing", type="prop", label=item.label, magical=True, transformable=True, sharable=True))

    setting_setup(world, setting, kid1, kid2, keeper)
    world.para()
    notice_mystery(world, kid1, kid2, item)
    find_clue(world, kid2, item)
    share_spell(world, kid1, kid2, spell, item)
    propagate(world, narrate=False)
    world.para()
    transform(world, item, spell)
    explain_sharing(world, keeper, kid1, kid2, item)
    world.para()
    ending_image(world, kid1, kid2, item)

    world.facts.update(
        setting=setting,
        item=item,
        spell=spell,
        kid1=kid1,
        kid2=kid2,
        keeper=keeper,
        rifle=relic,
        shared=True,
        transformed=True,
        mystery_seen=True,
        clue_shared=True,
    )
    return world


SETTINGS = {
    "museum": Setting(id="museum", place="the little museum of costumes", dark_spot="a dusty side hall", keeper="MsGray"),
    "attic": Setting(id="attic", place="the attic room above the stage shop", dark_spot="a stack of old trunks", keeper="MrBell"),
    "library": Setting(id="library", place="the back room of the town library", dark_spot="a shelf of locked display boxes", keeper="MrsGreen"),
}

ITEMS = {
    "rifle_prop": MysteryItem(
        id="rifle_prop",
        label="rifle-shaped prop",
        phrase="an old rifle-shaped prop",
        transformed_into="a silver key",
        clue="the key opens what the picture cannot",
        tags={"rifle", "mystery", "transformation", "sharing"},
    ),
    "rifle_toy": MysteryItem(
        id="rifle_toy",
        label="rifle-shaped toy",
        phrase="a toy rifle from the costume chest",
        transformed_into="a brass whistle",
        clue="the whistle is for the one who shares",
        tags={"rifle", "magic", "sharing"},
    ),
    "rifle_riddle": MysteryItem(
        id="rifle_riddle",
        label="old rifle-shaped puzzle",
        phrase="a puzzling little rifle",
        transformed_into="a lantern charm",
        clue="two hands are better than one",
        tags={"rifle", "mystery", "magic"},
    ),
}

SPELLS = {
    "sharelight": Spell(id="sharelight", incantation="Share the light, show the right", effect="glow", share_needed=True, clarity=2, tags={"magic", "sharing"}),
    "kindswap": Spell(id="kindswap", incantation="Kind hands, change plans", effect="shape", share_needed=True, clarity=2, tags={"magic", "transformation"}),
    "puzzlegleam": Spell(id="puzzlegleam", incantation="Puzzle gleam, shared dream", effect="reveal", share_needed=True, clarity=3, tags={"mystery", "magic", "sharing"}),
}

GIRL_NAMES = ["Mina", "June", "Lia", "Sara", "Nora", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Max", "Eli", "Noel"]
TRAITS = ["careful", "curious", "thoughtful", "brave"]


@dataclass
class StoryParams:
    setting: str
    item: str
    spell: str
    name1: str
    name2: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    spell = f["spell"]
    return [
        f'Write a mystery story for a 3-to-5-year-old that includes the word "rifle" and ends with a shared discovery.',
        f"Tell a gentle magical mystery where {f['kid1'].id} and {f['kid2'].id} find {item.phrase}, say {spell.incantation}, and learn to share it.",
        f"Write a story about transformation and sharing in a small mysterious room, with a harmless rifle-shaped clue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item = f["item"]
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    keeper = f["keeper"]
    rifle = f["rifle"]
    qa = [
        ("What did the children find?",
         f"They found {item.phrase} in a mysterious room. It looked important because it had a note and a strange magical feeling."),
        ("What did they do together?",
         f"They shared the clue, spoke the spell together, and listened to each other. That is what let the mystery start to open up."),
        ("What happened to the rifle-shaped object?",
         f"It transformed into {item.transformed_into}. The change proved the magic only worked when the children were kind and shared."),
        ("Who explained the mystery?",
         f"{keeper.label_word.capitalize()} did. {keeper.pronoun().capitalize()} said the clue got clearer when two people carried it together."),
    ]
    qa.append((
        "How did the story end?",
        f"It ended with {kid1.id} and {kid2.id} smiling beside the transformed object. The puzzle was solved, and the rifle-shaped clue became a shared secret instead of a worry."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["item"].tags) | set(f["spell"].tags)
    out = []
    if "rifle" in tags:
        out.append(("What is a rifle?",
                     "A rifle is a kind of gun in real life, but stories for children should keep it safe and non-scary. In this story it is only a harmless prop that changes shape by magic."))
    if "magic" in tags:
        out.append(("What is magic in a story?",
                     "Magic in a story is when something impossible happens, like an object changing shape or a clue appearing. It helps the mystery feel surprising."))
    if "sharing" in tags:
        out.append(("What does sharing mean?",
                     "Sharing means letting someone else have a turn or helping them hold something together. It can make hard things easier and kinder."))
    if "mystery" in tags:
        out.append(("What is a mystery?",
                     "A mystery is a puzzle with a hidden answer. People look for clues and pay attention until the answer is found."))
    if "transformation" in tags:
        out.append(("What is transformation?",
                     "Transformation means something changes into a different form. In a story, that change can be magical or surprising."))
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.magical:
            bits.append("magical")
        if e.transformable:
            bits.append("transformable")
        if e.sharable:
            bits.append("sharable")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="museum", item="rifle_prop", spell="puzzlegleam", name1="Mina", name2="Owen"),
    StoryParams(setting="attic", item="rifle_toy", spell="sharelight", name1="Lia", name2="Finn"),
    StoryParams(setting="library", item="rifle_riddle", spell="kindswap", name1="June", name2="Theo"),
]


def explain_rejection(item: MysteryItem, spell: Spell) -> str:
    if not reasonableness_gate(item, spell):
        return "(No story: this mystery needs a magical, transformable clue and a clear shared spell.)"
    return "(No story: this combination is not reasonable.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.transformable:
            lines.append(asp.fact("transformable", iid))
        if item.magical:
            lines.append(asp.fact("magical", iid))
    for spid, sp in SPELLS.items():
        lines.append(asp.fact("spell", spid))
        if sp.share_needed:
            lines.append(asp.fact("share_needed", spid))
        lines.append(asp.fact("clarity", spid, sp.clarity))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,I,P) :- setting(S), item(I), spell(P), transformable(I), magical(I), clarity(P,C), C >= 1.
shared_outcome(I) :- item(I), spell(P), share_needed(P).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in combo gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with magic, transformation, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.spell is None or c[2] == args.spell)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, spell = rng.choice(sorted(combos))
    if args.item and args.spell and not reasonableness_gate(ITEMS[args.item], SPELLS[args.spell]):
        raise StoryError(explain_rejection(ITEMS[args.item], SPELLS[args.spell]))
    n1 = args.name1 or rng.choice(GIRL_NAMES)
    n2 = args.name2 or rng.choice([n for n in BOY_NAMES if n != n1])
    return StoryParams(setting=setting, item=item, spell=spell, name1=n1, name2=n2)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.item not in ITEMS or params.spell not in SPELLS:
        raise StoryError("(Invalid params for this storyworld.)")
    world = tell(SETTINGS[params.setting], ITEMS[params.item], SPELLS[params.spell], params.name1, params.name2)
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
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
