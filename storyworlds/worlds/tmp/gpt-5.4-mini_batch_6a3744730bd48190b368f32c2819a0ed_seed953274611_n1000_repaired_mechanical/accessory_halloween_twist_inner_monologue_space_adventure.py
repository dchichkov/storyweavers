#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/accessory_halloween_twist_inner_monologue_space_adventure.py
===========================================================================================

A small storyworld in a space-adventure style: a child astronaut prepares for
a Halloween costume party, loses a special accessory, follows an inner monologue
through the ship, and discovers a twist that changes what the "missing" thing
really was.

This world keeps the simulation tiny but state-driven:
- physical meters: search progress, ship darkness, propulsion readiness, foundness
- emotional memes: worry, courage, delight, relief, embarrassment

The story is built from a causal world model rather than a frozen paragraph.
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
MAX_TRIES = 80


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
    plural: bool = False
    shiny: bool = False
    wearable: bool = False
    accessory: bool = False
    hidden: bool = False

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    ship: str
    dark_zone: str
    mission: str
    sky_view: str
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
class Accessory:
    id: str
    label: str
    phrase: str
    kind: str
    clue: str
    shine: str
    reveals: str
    wearable: bool = True
    accessory: bool = True
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
class CostumeTwist:
    id: str
    reveal_line: str
    truth_line: str
    fix_line: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: str = ""
        self.accessory: Optional[Accessory] = None

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.zone = self.zone
        clone.accessory = self.accessory
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


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    acc = world.get("accessory")
    if hero.meters["searching"] >= THRESHOLD and acc.hidden:
        sig = ("search", acc.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["found"] += 1
            hero.memes["worry"] += 1
            out.append("__found_clue__")
    return out


def _r_darkness(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ship").meters["darkness"] >= THRESHOLD:
        sig = ("dark", world.setting.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["worry"] += 1
            out.append("__dark__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    acc = world.get("accessory")
    if hero.meters["found"] >= THRESHOLD and not acc.hidden:
        sig = ("relief", acc.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            hero.memes["courage"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("search", _r_search), Rule("darkness", _r_darkness), Rule("relief", _r_relief)]


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


def predict_reveal(world: World) -> bool:
    sim = world.copy()
    sim.get("hero").meters["searching"] += 1
    propagate(sim, narrate=False)
    return sim.get("accessory").hidden


def tell(setting: Setting, accessory: Accessory, twist: CostumeTwist, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str, parent_type: str, seed_note: str = "") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent"))
    ship = world.add(Entity(id="ship", type="ship", label=setting.ship))
    acc_ent = world.add(Entity(id="accessory", type=accessory.kind, label=accessory.label,
                               wearable=True, accessory=True, hidden=True))
    world.accessory = accessory

    hero.meters["prepping"] += 1
    hero.memes["delight"] += 1
    hero.memes["worry"] += 0.0

    world.say(
        f"On Halloween night, {hero.id} raced through the space station hallway with a costume "
        f"ready for the launch party. {setting.sky_view}"
    )
    world.say(
        f"Everything looked brave and bright, except for one important accessory: {accessory.phrase}."
    )

    world.para()
    world.say(
        f"{hero.id} checked the bench, the locker, and the little mirror by the airlock."
    )
    hero.meters["searching"] += 1
    ship.meters["darkness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {setting.dark_zone} felt extra dark, like a tiny moon cave."
    )
    world.say(
        f'"I have to find it," {hero.id} thought. "{accessory.clue}? No, that was too silly. '
        f'What if I look wrong and everyone laughs?"'
    )
    world.say(
        f"But then a calmer thought answered inside {hero.pronoun('possessive')} head: '
        f'"Keep going. Space missions do not end because of one missing {accessory.label_word}."'
    )

    world.para()
    world.say(
        f"{helper.id} floated in holding a glow map and a small snack. "
        f'"Maybe your accessory is hiding where costumes get finished," {helper.pronoun()} said.'
    )
    helper.memes["courage"] += 1
    if predict_reveal(world):
        hero.meters["searching"] += 1
        propagate(world, narrate=False)

    world.say(
        f"{hero.id} followed the thought, peered into a drawer, and then froze."
    )

    world.para()
    if accessory.id == "moonbadge":
        world.say(twist.reveal_line)
        world.say(
            f"The shiny thing was not missing at all. It had been tucked behind {hero.pronoun('possessive')} "
            f"collar, and the dark room had made it look lost."
        )
    elif accessory.id == "pumpkinvisor":
        world.say(twist.reveal_line)
        world.say(
            f"The visor was already on the helmet, but it had slid sideways under the cape."
        )
    else:
        world.say(twist.reveal_line)
        world.say(
            f"The last place to look was the costume box itself, where the accessory had been hiding beneath paper stars."
        )

    acc_ent.hidden = False
    hero.meters["found"] += 1
    propagate(world, narrate=False)

    world.say(
        twist.truth_line.replace("{accessory}", accessory.label).replace("{hero}", hero.id)
    )
    world.say(
        f"{hero.id} let out a laugh that turned into a sigh. The worry melted into relief."
    )

    world.para()
    parent.memes["pride"] += 1
    world.say(
        f"{parent.pronoun().capitalize()} came down the corridor and smiled. {twist.fix_line}"
    )
    world.say(
        f"At last, {hero.id} put on {accessory.phrase}, and the costume looked exactly right for Halloween among the stars."
    )
    world.say(
        f"The party lights blinked green and gold as the little spaceship drifted toward the launch bay, "
        f"and {hero.id} walked in feeling clever, brave, and ready."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        accessory=accessory,
        twist=twist,
        setting=setting,
        outcome="found",
        revealed=True,
        seed_note=seed_note,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a 3-to-5-year-old that includes the words "{f["accessory"].label}" and "halloween".',
        f"Tell a story where {f['hero'].id} thinks a Halloween accessory is missing on a spaceship, but the ending has a twist.",
        f"Write a child-friendly outer-space story with an inner monologue, a lost accessory, and a twist that makes the search turn out okay.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    accessory = f["accessory"]
    qa = [
        (
            "What was the story about?",
            f"It was about {hero.id} on a Halloween space adventure, trying to find {hero.pronoun('possessive')} {accessory.label}. "
            f"The missing accessory made the costume feel unfinished until the twist changed what was really happening.",
        ),
        (
            "What was {hero} thinking during the search?".format(hero=hero.id),
            f"{hero.id} kept talking to {hero.pronoun('possessive')}self in {hero.pronoun('possessive')} head and trying not to panic. "
            f"That inner voice helped {hero.id} keep searching instead of giving up.",
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} kept looking in the ship's dark places and then noticed that {accessory.label} was not truly lost. "
            f"The twist was that it had been hiding in plain sight, so the problem was solved by noticing carefully.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    accessory = f["accessory"]
    tags = set(accessory.tags)
    tags.add("halloween")
    tags.add("space")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE.get(tag, []))
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
        if e.hidden:
            bits.append("hidden=True")
        if e.wearable:
            bits.append("wearable=True")
        lines.append(f"  {e.id:9} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", s.id) for s in SETTINGS.values()
    ]
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for aid, a in ACCESSORIES.items():
        lines.append(asp.fact("accessory", aid))
        if a.accessory:
            lines.append(asp.fact("is_accessory", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        for tg in sorted(t.tags):
            lines.append(asp.fact("twist_tag", tid, tg))
    return "\n".join(lines)


ASP_RULES = r"""
valid(A,T) :- accessory(A), twist(T).
reveal(A) :- accessory(A), tag(A,halloween).
inner_monologue(A) :- accessory(A), tag(A,space).
"""

@dataclass
class StoryParams:
    setting: str
    accessory: str
    twist: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    parent_type: str = "mother"
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


SETTINGS = {
    "orbit": Setting(id="orbit", place="a moonlit corridor", ship="Star Lantern", dark_zone="airlock nook", mission="Halloween parade", sky_view="Outside the window, stars blinked like tiny lanterns."),
    "dock": Setting(id="dock", place="a docking bay", ship="Comet Kite", dark_zone="cargo shadow", mission="costume launch", sky_view="The station floated above a silver planet and the windows glowed blue."),
}

ACCESSORIES = {
    "moonbadge": Accessory(id="moonbadge", label="moon badge", phrase="the moon badge", kind="badge", clue="shine, shine, little moon", shine="glinted like a coin", reveals="was tucked behind the collar", tags={"halloween", "space", "badge"}),
    "pumpkinvisor": Accessory(id="pumpkinvisor", label="pumpkin visor", phrase="the pumpkin visor", kind="visor", clue="orange light in the dark", shine="glowed pumpkin bright", reveals="had slid under the cape", tags={"halloween", "space", "visor"}),
    "rocketcapeclip": Accessory(id="rocketcapeclip", label="rocket cape clip", phrase="the rocket cape clip", kind="clip", clue="click together and look again", shine="sparkled like a star", reveals="was hiding in the costume box", tags={"halloween", "space", "clip"}),
}

TWISTS = {
    "plain_sight": CostumeTwist(id="plain_sight", reveal_line="Then the twist arrived: the missing accessory was already there, only hidden by the costume.", truth_line="{hero} blinked and realized {accessory} had been close the whole time.", fix_line="\"Sometimes the dark plays tricks,\" {hero}'s parent said, \"but careful looking wins.\""),
    "misplaced_mirror": CostumeTwist(id="misplaced_mirror", reveal_line="Then the twist arrived: the shiny clue was not the accessory, but its reflection in the mirror.", truth_line="{hero} laughed because {accessory} was on the helmet all along.", fix_line="\"Good eyes,\" {hero}'s helper said, \"you found the truth instead of the trick.\""),
    "box_hiding": CostumeTwist(id="box_hiding", reveal_line="Then the twist arrived: the accessory was hiding in the costume box, snug as a sleepy comet.", truth_line="{hero} opened the box and saw {accessory} smiling back from under the paper stars.", fix_line="\"That was the smartest kind of spooky,\" {hero}'s parent said."),
}

HERO_NAMES = ["Nova", "Milo", "Zara", "Beck", "Luna", "Rico"]
HELPER_NAMES = ["Pip", "Juno", "Tess", "Orion", "Mira", "Echo"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, a, t) for s in SETTINGS for a in ACCESSORIES for t in TWISTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure Halloween storyworld with a lost accessory, inner monologue, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--accessory", choices=ACCESSORIES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.accessory is None or c[1] == args.accessory)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, accessory, twist = rng.choice(combos)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, accessory=accessory, twist=twist,
                       hero_name=hero, hero_type="girl" if hero[0] in "AEIOULZ" else "boy",
                       helper_name=helper, helper_type="girl" if helper[0] in "AEIOU" else "boy",
                       parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.accessory not in ACCESSORIES or params.twist not in TWISTS:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], ACCESSORIES[params.accessory], TWISTS[params.twist],
                 params.hero_name, params.hero_type, params.helper_name, params.helper_type, params.parent_type)
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


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((s, a) for s, a, _ in valid_combos()):
        print("MISMATCH: ASP and Python valid-combo sets differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        _ = sample.to_dict()
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, a, t in valid_combos():
            print(s, a, t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting=s, accessory=a, twist=t, hero_name="Nova", hero_type="girl",
                                        helper_name="Pip", helper_type="boy", parent_type="mother"))
                   for s, a, t in valid_combos()]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < MAX_TRIES:
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
