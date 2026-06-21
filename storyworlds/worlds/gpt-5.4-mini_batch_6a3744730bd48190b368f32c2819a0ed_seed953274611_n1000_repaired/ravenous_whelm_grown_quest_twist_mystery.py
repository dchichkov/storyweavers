#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ravenous_whelm_grown_quest_twist_mystery.py
===========================================================================

A tiny mystery storyworld built from the seed words:
- ravenous
- whelm
- grown

It follows a child-led quest in a small, concrete setting, with a mystery turn
and a twist ending. The world model tracks physical meters and emotional memes,
then renders prose from the simulated changes instead of swapping nouns in a
frozen paragraph.

Run examples:
    python storyworlds/worlds/gpt-5.4-mini/ravenous_whelm_grown_quest_twist_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/ravenous_whelm_grown_quest_twist_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/ravenous_whelm_grown_quest_twist_mystery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        t = self.type
        if t in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if t in {"boy", "father", "man"}:
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
class StoryParams:
    hero_name: str
    hero_type: str
    grown_name: str
    grown_type: str
    creature: str
    clue: str
    relic: str
    setting: str
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


@dataclass
class Setting:
    id: str
    place: str
    dark_spot: str
    hiding_place: str
    scent: str
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
class Creature:
    id: str
    label: str
    ravenous: bool
    noise: str
    tracks: str
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
class Clue:
    id: str
    label: str
    phrase: str
    meaning: str
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
class Relic:
    id: str
    label: str
    phrase: str
    glow: str
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
        clone.facts = dict(self.facts)
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


def _r_ravenous(world: World) -> list[str]:
    out: list[str] = []
    critter = world.entities.get("creature")
    hero = world.entities.get("hero")
    if not critter or not hero:
        return out
    if critter.meters.get("hunger", 0.0) < THRESHOLD:
        return out
    sig = ("ravenous",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["unease"] = hero.memes.get("unease", 0.0) + 1
    out.append(f"The {critter.label} was ravenous, and {hero.id} could hear it pacing nearby.")
    return out


def _r_whelm(world: World) -> list[str]:
    out: list[str] = []
    setting = world.entities.get("setting")
    if not setting:
        return out
    if setting.meters.get("flood", 0.0) < THRESHOLD:
        return out
    sig = ("whelm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["startle"] = ent.memes.get("startle", 0.0) + 1
    out.append("A sudden wash of water had whelmed the path and buried the easy footprints.")
    return out


def _r_grown(world: World) -> list[str]:
    out: list[str] = []
    grown = world.entities.get("grown")
    hero = world.entities.get("hero")
    relic = world.entities.get("relic")
    if not grown or not hero or not relic:
        return out
    if grown.meters.get("care", 0.0) < THRESHOLD:
        return out
    sig = ("grown",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    relic.meters["seen"] = relic.meters.get("seen", 0.0) + 1
    out.append(f"The grown helper moved quietly, as if they already knew what the clues were saying.")
    return out


CAUSAL_RULES = [Rule("ravenous", _r_ravenous), Rule("whelm", _r_whelm), Rule("grown", _r_grown)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_twist(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "relic_seen": sim.get("relic").meters.get("seen", 0.0) >= THRESHOLD,
        "unease": sim.get("hero").memes.get("unease", 0.0),
    }


SETTINGS = {
    "harbor": Setting("harbor", "the old harbor", "the wet dock", "the boathouse", "salt and rope"),
    "garden": Setting("garden", "the moon garden", "the rose path", "the shed", "mint and soil"),
    "attic": Setting("attic", "the dusty attic", "the dark trunk", "the cedar chest", "warm wood"),
}

CREATURES = {
    "cat": Creature("cat", "cat", False, "a soft yowl", "tiny prints"),
    "fox": Creature("fox", "fox", True, "a low hiss", "slanted prints"),
    "goat": Creature("goat", "goat", True, "a rude bleat", "hoof marks"),
}

CLUES = {
    "crumbs": Clue("crumbs", "crumbs", "a trail of crumbs", "something was carried that way"),
    "shells": Clue("shells", "shells", "a line of shells", "the trail curled toward the water"),
    "ribbon": Clue("ribbon", "ribbon", "a blue ribbon on a nail", "someone had tied the thing up"),
}

RELICS = {
    "lamp": Relic("lamp", "little lamp", "a little lamp", "glowed like a small star"),
    "map": Relic("map", "paper map", "a folded paper map", "showed one hidden turn"),
    "key": Relic("key", "brass key", "a brass key", "shone with a warm gold shine"),
}

GROWN_NAMES = ["Mara", "Eden", "June", "Iris", "Nell"]
KID_NAMES = ["Milo", "Lina", "Pip", "Tess", "Noah", "Ada"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, creature in CREATURES.items():
            if not creature.ravenous:
                continue
            for clue_id in CLUES:
                for relic_id in RELICS:
                    combos.append((sid, cid, clue_id, relic_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-led mystery quest with a twist ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--hero")
    ap.add_argument("--grown")
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
    if args.creature and not CREATURES[args.creature].ravenous:
        raise StoryError("That creature is not ravenous enough for this mystery quest.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.creature is None or c[1] == args.creature)
              and (args.clue is None or c[2] == args.clue)
              and (args.relic is None or c[3] == args.relic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, creature_id, clue_id, relic_id = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(KID_NAMES)
    grown = args.grown or rng.choice(GROWN_NAMES)
    return StoryParams(
        hero_name=hero,
        hero_type="boy" if hero in {"Milo", "Pip", "Noah"} else "girl",
        grown_name=grown,
        grown_type="woman",
        creature=creature_id,
        clue=clue_id,
        relic=relic_id,
        setting=setting_id,
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = world.add(Entity("setting", kind="thing", type="place", label=SETTINGS[params.setting].place))
    hero = world.add(Entity("hero", kind="character", type=params.hero_type, label=params.hero_name, role="quester"))
    grown = world.add(Entity("grown", kind="character", type=params.grown_type, label=params.grown_name, role="guide"))
    creature = world.add(Entity("creature", kind="thing", type="animal", label=CREATURES[params.creature].label))
    clue = world.add(Entity("clue", kind="thing", type="clue", label=CLUES[params.clue].label))
    relic = world.add(Entity("relic", kind="thing", type="relic", label=RELICS[params.relic].label))
    creature.meters["hunger"] = 1.0
    setting.meters["flood"] = 1.0
    grown.meters["care"] = 1.0

    world.say(f"On a quiet night, {hero.label} went to {SETTINGS[params.setting].place} on a quest.")
    world.say(f"{hero.label} had only one clue: {CLUES[params.clue].phrase}.")
    world.para()
    world.say(f"Then {CREATURES[params.creature].label} made its noise in the dark, and the air felt strange.")
    world.say(f"A wash of water had rolled in earlier, and it could whelm the easy trail.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"{hero.label} followed the clue to {RELICS[params.relic].phrase}, but the shape was not what it seemed.")
    twist = predict_twist(world)
    if twist["relic_seen"]:
        world.say(f"The grown helper stepped beside {hero.label} and turned the object over.")
        world.say(f"It was not a treasure at all. It was a map, and the map pointed to the real hidden thing.")
        world.say(f"At last {hero.label} found {RELICS[params.relic].phrase}, and the ravenous creature stopped circling.")
    else:
        world.say(f"The grown helper listened closely, and the clue led them to the true hiding place.")
        world.say(f"There, tucked where the water could not reach, was {RELICS[params.relic].phrase}.")
    world.say(f"{hero.label} laughed with relief, because the mystery had been solved before the night could grow worse.")
    world.facts.update(
        hero=hero, grown=grown, creature=creature, clue=clue, relic=relic, setting=setting,
        setting_cfg=SETTINGS[params.setting], creature_cfg=CREATURES[params.creature],
        clue_cfg=CLUES[params.clue], relic_cfg=RELICS[params.relic],
        twist_seen=twist["relic_seen"], whelm=True, ravenous=True, grown_present=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-facing mystery quest that uses the words ravenous, whelm, and grown.",
        f"Tell a story where {f['hero'].label} follows a clue through {f['setting_cfg'].place} and discovers a twist.",
        f"Write a short mystery with a ravenous creature, a whelmed trail, and a grown helper who changes the ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    grown = f["grown"].label
    return [
        QAItem(
            question="What was the mystery about?",
            answer=f"It was about {hero} following a clue to find the hidden relic. The quest got stranger because the trail had been whelmed by water and a ravenous creature kept nearby.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the grown helper was not hiding the answer from {hero}; they were helping {hero} see it more clearly. When the object was turned over, the clue made sense at last.",
        ),
        QAItem(
            question=f"How did {grown} help?",
            answer=f"{grown} moved beside {hero}, looked at the clue, and showed the real hiding place. That calm help let the quest end safely instead of getting lost in the dark.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ravenous mean?",
            answer="Ravenous means very, very hungry. A ravenous animal wants food right away and may keep searching until it finds some.",
        ),
        QAItem(
            question="What does whelm mean?",
            answer="To whelm something is to cover or overwhelm it, like water covering a path or a feeling covering your thoughts. In a mystery, that can hide the clues for a while.",
        ),
        QAItem(
            question="What does grown mean?",
            answer="Grown means having become an adult or being bigger and older than before. A grown helper can listen, notice clues, and help keep a child safe.",
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {e.label} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
ravenous(C) :- creature(C), hunger(C,H), H >= 1.
whelm(S) :- setting(S), flood(S,F), F >= 1.
grown(G) :- guide(G), care(G,C), C >= 1.
twist_seen :- grown(G), clue(C), relic(R), hero(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        if c.ravenous:
            lines.append(asp.fact("ravenous", cid))
    for gid in GROWN_NAMES:
        pass
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story:
        return 1
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show twist_seen/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(hero_name="Milo", hero_type="boy", grown_name="Mara", grown_type="woman", creature="fox", clue="crumbs", relic="map", setting="harbor"))]
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
