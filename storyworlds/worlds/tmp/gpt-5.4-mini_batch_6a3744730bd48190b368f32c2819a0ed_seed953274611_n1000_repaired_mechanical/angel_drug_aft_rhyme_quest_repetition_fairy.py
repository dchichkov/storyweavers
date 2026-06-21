#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/angel_drug_aft_rhyme_quest_repetition_fairy.py
================================================================================

A tiny fairy-tale storyworld about an angel messenger, a healing drug as a
herb-jar, and an aft deck on a little boat.  The world keeps the story small,
state-driven, and child-facing, with rhyme, quest, and repetition woven into the
simulation rather than pasted onto a frozen paragraph.

Seed words: angel, drug, aft
Features: rhyme, quest, repetition
Style: fairy tale
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"angel"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"girl", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    id: str
    place: str
    weather: str
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
class Quest:
    id: str
    title: str
    refrain: str
    destination: str
    promise: str
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
class Remedy:
    id: str
    label: str
    phrase: str
    safe: bool = True
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
class Rhyme:
    id: str
    line1: str
    line2: str
    line3: str
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
    setting: str
    quest: str
    remedy: str
    rhyme: str
    hero: str
    companion: str
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


def _r_calm(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["worry"] >= THRESHOLD and (("calm",) not in world.fired):
            world.fired.add(("calm",))
            e.memes["hope"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("calm", _r_calm)]


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


def ask_quest(world: World, hero: Entity, companion: Entity, quest: Quest) -> None:
    hero.memes["hope"] += 1
    companion.memes["care"] += 1
    world.say(
        f"In a bright little kingdom, {hero.id} the angel set out on a {quest.title}. "
        f"{quest.refrain} {companion.id} said, and {hero.id} answered, "
        f'"{quest.promise}"'
    )


def travel(world: World, setting: Setting, quest: Quest) -> None:
    world.say(
        f"They went to {setting.place}, where the {setting.weather} air was soft and slow. "
        f"Their road led aft, to the aft deck, and the path felt like a song."
    )


def notice(world: World, hero: Entity, companion: Entity, remedy: Remedy) -> None:
    world.say(
        f"Then {companion.id} spotted the little jar of {remedy.label}. "
        f'"We need the drug," {companion.id} whispered, "for the poor lamb in the pale tower."'
    )
    hero.memes["quest"] += 1


def repeat_refrain(world: World, quest: Quest, times: int = 2) -> None:
    for i in range(times):
        world.say(f"Again they sang: {quest.refrain}")


def choose_and_return(world: World, hero: Entity, companion: Entity, remedy: Remedy, quest: Quest) -> None:
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    if remedy.safe:
        world.say(
            f"{hero.id} lifted the drug with careful hands, and the lamb grew warm and well. "
            f"At the aft of the little boat, they shared a smile."
        )
    else:
        world.say(
            f"{hero.id} touched the jar, but the old drug was wrong for the lamb. "
            f"So they turned back aft, sad but wise."
        )


def end_rhyme(world: World, rhyme: Rhyme) -> None:
    world.say(f"{rhyme.line1} {rhyme.line2} {rhyme.line3}")


SETTINGS = {
    "moon_boat": Setting(
        id="moon_boat",
        place="the moon boat",
        weather="silver",
        tags={"aft", "fairy_tale"},
    ),
    "rose_bridge": Setting(
        id="rose_bridge",
        place="the rose bridge",
        weather="golden",
        tags={"fairy_tale"},
    ),
}

QUESTS = {
    "lamb_cure": Quest(
        id="lamb_cure",
        title="quest for the lamb's cure",
        refrain="Step and skip, and never slip,",
        destination="the pale tower",
        promise="I will bring the cure before the star grows dim.",
        tags={"quest", "repetition"},
    ),
    "night_bell": Quest(
        id="night_bell",
        title="quest for the night bell",
        refrain="Sing and ring, and find the thing,",
        destination="the glass hill",
        promise="I will come back with hope and light.",
        tags={"quest", "repetition"},
    ),
}

REMEDIES = {
    "herb_drug": Remedy(
        id="herb_drug",
        label="herb drug",
        phrase="a small jar of herb drug",
        safe=True,
        tags={"drug"},
    ),
    "sweet_syrup": Remedy(
        id="sweet_syrup",
        label="sweet syrup",
        phrase="a sweet healing syrup",
        safe=True,
        tags={"drug"},
    ),
}

RHYMES = {
    "gentle": Rhyme(
        id="gentle",
        line1="Little wings in morning light,",
        line2="carry hope from left to right,",
        line3="aft they go and home they bring the bright.",
        tags={"rhyme"},
    ),
    "lullaby": Rhyme(
        id="lullaby",
        line1="Soft bells jingle, soft birds sing,",
        line2="kind steps make the meadow ring,",
        line3="aft they sail on silvery wing.",
        tags={"rhyme"},
    ),
}

HEROES = ["Ariel", "Mira", "Tali", "Neri"]
COMPANIONS = ["Wren", "Pip", "Lio", "Sage"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for r in REMEDIES:
                for rh in RHYMES:
                    combos.append((s, q, r, rh))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale that includes the words "angel", "drug", and "aft" and follows a gentle quest.',
        f"Tell a repetition-filled story where {f['hero'].id} the angel must bring a drug to help someone, and the journey goes aft on a small boat.",
        f"Write a rhyming quest story with an angel, a healing drug, and a return aft to safety.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    quest = f["quest"]
    remedy = f["remedy"]
    setting = f["setting"]
    rhyme = f["rhyme"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, an angel on a quest with {companion.id}. They travel together through {setting.place} and keep going until the task is done.",
        ),
        QAItem(
            question="What did they need to bring?",
            answer=f"They needed {remedy.phrase}. The drug was the gentle thing that could help the lamb, so the quest had a clear purpose.",
        ),
        QAItem(
            question="How did the story use repetition?",
            answer=f"It repeated the quest refrain, '{quest.refrain}' more than once. That repeated line makes the journey feel like a fairy-tale chant and keeps the goal in mind.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the cure delivered and the travelers smiling aft on the little boat. The last image proves they returned safely after the quest was finished.",
        ),
        QAItem(
            question="What made it rhyme?",
            answer=f"The closing rhyme was: {rhyme.line1} {rhyme.line2} {rhyme.line3}. Those lines sound like a small song and match the fairy-tale mood.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags) | set(world.facts["remedy"].tags) | set(world.facts["rhyme"].tags)
    out: list[QAItem] = []
    if "quest" in tags:
        out.append(QAItem("What is a quest?", "A quest is a journey with a goal. A character sets out to find, deliver, or fix something important."))
    if "drug" in tags:
        out.append(QAItem("What is a drug in this story?", "Here, drug means a healing medicine. It is a safe story word for a remedy that helps someone feel better."))
    if "aft" in tags:
        out.append(QAItem("What does aft mean?", "Aft means toward the back of a boat. If someone goes aft, they walk to the rear end."))
    if "rhyme" in tags:
        out.append(QAItem("What is a rhyme?", "A rhyme is when words sound alike at the end. It makes a story feel musical and easy to remember."))
    return out


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(setting: Setting, quest: Quest, remedy: Remedy, rhyme: Rhyme, hero: str, companion: str) -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type="angel", role="hero"))
    c = world.add(Entity(id=companion, kind="character", type="angel", role="companion"))
    tower = world.add(Entity(id="tower", type="place", label=quest.destination))
    drug = world.add(Entity(id="drug", type="thing", label=remedy.label, attrs={"safe": remedy.safe}))
    aft = world.add(Entity(id="aft", type="place", label="aft deck"))

    world.facts.update(hero=h, companion=c, setting=setting, quest=quest, remedy=remedy, rhyme=rhyme, tower=tower, drug=drug, aft=aft)

    ask_quest(world, h, c, quest)
    world.para()
    travel(world, setting, quest)
    repeat_refrain(world, quest, times=2)
    world.para()
    notice(world, h, c, remedy)
    choose_and_return(world, h, c, remedy, quest)
    world.para()
    end_rhyme(world, rhyme)
    h.memes["joy"] += 1
    c.memes["joy"] += 1
    return world


CURATED = [
    StoryParams(setting="moon_boat", quest="lamb_cure", remedy="herb_drug", rhyme="gentle", hero="Ariel", companion="Wren"),
    StoryParams(setting="rose_bridge", quest="night_bell", remedy="sweet_syrup", rhyme="lullaby", hero="Mira", companion="Pip"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale quest storyworld with rhyme and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    combos = valid_combos()
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.remedy is None or c[2] == args.remedy)
              and (args.rhyme is None or c[3] == args.rhyme)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, remedy, rhyme = rng.choice(combos)
    hero = args.hero or rng.choice(HEROES)
    companion = args.companion or rng.choice([x for x in COMPANIONS if x != hero])
    return StoryParams(setting=setting, quest=quest, remedy=remedy, rhyme=rhyme, hero=hero, companion=companion)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest not in QUESTS or params.remedy not in REMEDIES or params.rhyme not in RHYMES:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], REMEDIES[params.remedy], RHYMES[params.rhyme], params.hero, params.companion)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
valid(S,Q,R,H) :- setting(S), quest(Q), remedy(R), rhyme(H).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r))
    for h in RHYMES:
        lines.append(asp.fact("rhyme", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as ex:
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
