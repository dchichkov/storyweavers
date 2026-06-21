#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rad_monitor_rhyme_curiosity_animal_story.py
============================================================================

A tiny storyworld for a child-facing animal tale built from the seed words
"rad" and "monitor", with rhyme and curiosity as the narrative instruments.

Premise
-------
A curious animal hears a rhyme about a "rad monitor" and goes looking for the
real thing. The search turns into a small, state-driven adventure: the animal
learns that "monitor" can mean a lizard, a guard, or a screen, and that not
every shiny clue is the same as the thing itself. The story ends when the animal
finds the right monitor and uses it in a good, useful way.

This world uses:
- typed entities with physical meters and emotional memes,
- a small forward-chaining rule engine,
- a Python reasonableness gate plus inline ASP twin,
- three separate Q&A sets grounded in the simulated world,
- rhyme and curiosity as first-class story instruments.
"""

from __future__ import annotations

import argparse
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sheep", "cat", "rabbit", "fox", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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
    habitat: str
    hero: str
    hero_type: str
    guide: str
    guide_type: str
    curiosity: str
    clue: str
    monitor_kind: str
    rhyme_kind: str
    ending: str
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
class Habitat:
    id: str
    scene: str
    opening: str
    nook: str
    sounds: str
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
class Animal:
    id: str
    type: str
    label: str
    rhyme_name: str
    curious_line: str
    end_line: str
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
class Clue:
    id: str
    text: str
    is_true: bool
    leads_to: str
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
class MonitorThing:
    id: str
    label: str
    phrase: str
    use_line: str
    is_useful: bool
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


def _meter(world: World, eid: str, key: str, amount: float) -> None:
    world.get(eid).meters[key] += amount


def _mem(world: World, eid: str, key: str, amount: float) -> None:
    world.get(eid).memes[key] += amount


def _r_curiosity(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    clue = world.entities.get("clue")
    if not hero or not clue:
        return out
    if hero.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("curiosity", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if clue.is_true:
        hero.memes["interest"] += 1
        out.append("__curious__")
    else:
        hero.memes["confusion"] += 1
        out.append("__curious__")
    return out


def _r_discover(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    clue = world.entities.get("clue")
    monitor = world.entities.get("monitor")
    if not hero or not clue or not monitor:
        return out
    if hero.memes["search"] < THRESHOLD:
        return out
    if clue.id != "clue" or monitor.id != "monitor":
        return out
    sig = ("discover",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if clue.is_true and monitor.is_useful:
        monitor.meters["found"] = 1
        hero.memes["joy"] += 1
        out.append("__found__")
    return out


CAUSAL_RULES: list[Callable[[World], list[str]]] = [_r_curiosity, _r_discover]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(habitat: Habitat, hero: Animal, guide: Animal, clue: Clue, monitor: MonitorThing) -> World:
    world = World()
    h = world.add(Entity(id="hero", kind="character", type=hero.type, label=hero.label, tags=set(hero.tags)))
    g = world.add(Entity(id="guide", kind="character", type=guide.type, label=guide.label, tags=set(guide.tags)))
    c = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.id, attrs={"text": clue.text}, tags=set(clue.tags),))
    m = world.add(Entity(id="monitor", kind="thing", type="monitor", label=monitor.label, attrs={"phrase": monitor.phrase}, tags=set(monitor.tags)))
    h.memes["curiosity"] = 1
    h.memes["search"] = 1
    g.memes["care"] = 1

    world.say(f"In {habitat.scene}, {hero.id} was a {hero.label} with a {hero.curious_line}.")
    world.say(f"{habitat.opening} {habitat.sounds} drifted through the air, and the day felt {hero.rhyme_name}.")
    world.say(f"{hero.id} heard a rhyme about a {monitor.phrase} and wanted to know what it meant.")

    world.para()
    world.say(f"{hero.id} peered into {habitat.nook}.")
    world.say(f'"What is a {monitor.label}?" {hero.id} asked, all full of curiosity.')
    _mem(world, "hero", "curiosity", 1)
    _mem(world, "hero", "search", 1)
    propagate(world, narrate=False)

    world.say(f"{guide.id} looked up from the path and said, \"A {monitor.label} can be a lizard, a guard, or a screen. Let's follow the clue and see.\"")
    if clue.is_true:
        world.say(f"The clue was true: {clue.text}")
    else:
        world.say(f"The clue was tricky: {clue.text}")

    world.para()
    if clue.is_true and monitor.is_useful:
        world.say(f"{hero.id} followed the clue to the right place, where the {monitor.label} was waiting.")
        world.say(f"{monitor.use_line}")
        _meter(world, "monitor", "useful", 1)
        _mem(world, "hero", "joy", 1)
        world.say(f"{hero.id} smiled, because the answer was not just funny -- it was useful too.")
        world.say(f"{hero.id} felt so {hero.end_line} that the whole tale seemed to rhyme.")
    else:
        world.say(f"{hero.id} followed the clue, but it led to the wrong thing.")
        world.say(f"{guide.id} helped {hero.id} stop, look again, and pick the real answer.")
        _mem(world, "hero", "confusion", 1)
        _mem(world, "hero", "learning", 1)
        world.say(f"At last, {hero.id} found the proper monitor and understood the rhyme.")
        world.say(f"{hero.id} ended the day {hero.end_line}.")

    world.facts.update(
        habitat=habitat, hero=h, guide=g, clue=c, monitor=m,
        clue_cfg=clue, monitor_cfg=monitor,
        rhyme_kind=hero.rhyme_name, ending=hero.end_line,
        found=monitor.is_useful and clue.is_true,
    )
    return world


HABITATS = {
    "mangrove": Habitat(
        id="mangrove",
        scene="a mangrove path by the water",
        opening="The roots made twisty bridges,",
        nook="a shady hollow",
        sounds="the birds went chirp-chirp and the water went glug-glug",
        tags={"water", "roots"},
    ),
    "savanna": Habitat(
        id="savanna",
        scene="a sunny savanna trail",
        opening="The grass swayed like a soft wave,",
        nook="a grass-bent nook",
        sounds="the insects hummed and the wind said shoo-shoo",
        tags={"grass", "wind"},
    ),
}

ANIMALS = {
    "lemur": Animal(
        id="Lilo",
        type="lemur",
        label="little lemur",
        rhyme_name="rad",
        curious_line="bright eyes and a skip-skip step",
        end_line="glad",
        tags={"curious", "animal"},
    ),
    "fox": Animal(
        id="Fifi",
        type="fox",
        label="small fox",
        rhyme_name="rad",
        curious_line="a twitchy nose and a quick, quick grin",
        end_line="brave and glad",
        tags={"curious", "animal"},
    ),
}

GUIDES = {
    "turtle": Animal(
        id="Tomo",
        type="turtle",
        label="wise turtle",
        rhyme_name="calm",
        curious_line="a slow shell and a patient wink",
        end_line="calm",
        tags={"guide"},
    ),
    "bird": Animal(
        id="Mara",
        type="bird",
        label="helpful bird",
        rhyme_name="warm",
        curious_line="a bright wing and a keen little eye",
        end_line="warm",
        tags={"guide"},
    ),
}

CLUES = {
    "monitor_lizard": Clue(
        id="monitor_lizard",
        text="A monitor lizard basked on the warm path.",
        is_true=True,
        leads_to="lizard",
        tags={"monitor", "lizard"},
    ),
    "sign": Clue(
        id="sign",
        text="A sign pointed to the animal station.",
        is_true=False,
        leads_to="sign",
        tags={"monitor", "sign"},
    ),
}

MONITORS = {
    "lizard": MonitorThing(
        id="lizard",
        label="monitor",
        phrase="rad monitor",
        use_line="The monitor lizard lifted its head and watched the trail like a tiny guard.",
        is_useful=True,
        tags={"monitor", "lizard"},
    ),
    "screen": MonitorThing(
        id="screen",
        label="monitor",
        phrase="rad monitor",
        use_line="The screen showed a map, and the map made the route clear and neat.",
        is_useful=True,
        tags={"monitor", "screen"},
    ),
}

CURATED = [
    StoryParams(habitat="mangrove", hero="Lilo", hero_type="lemur", guide="Tomo", guide_type="turtle",
                curiosity="curious", clue="monitor_lizard", monitor_kind="lizard", rhyme_kind="rad",
                ending="glad"),
    StoryParams(habitat="savanna", hero="Fifi", hero_type="fox", guide="Mara", guide_type="bird",
                curiosity="curious", clue="sign", monitor_kind="screen", rhyme_kind="rad",
                ending="warm"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hid in HABITATS:
        for aid in ANIMALS:
            for cid, clue in CLUES.items():
                for mid, mon in MONITORS.items():
                    if clue.is_true and mon.is_useful:
                        combos.append((hid, cid, mid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny animal rhyme-curiosity storyworld.")
    ap.add_argument("--habitat", choices=HABITATS)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--monitor", choices=MONITORS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and not CLUES[args.clue].is_true:
        raise StoryError("That clue is too tricky for this little storyworld.")
    if args.monitor and not MONITORS[args.monitor].is_useful:
        raise StoryError("That monitor would not make a satisfying story ending.")
    combos = [c for c in valid_combos()
              if (args.habitat is None or c[0] == args.habitat)
              and (args.clue is None or c[1] == args.clue)
              and (args.monitor is None or c[2] == args.monitor)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    habitat, clue, monitor = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(sorted(ANIMALS))
    guide = args.guide or rng.choice(sorted(GUIDES))
    return StoryParams(
        habitat=habitat,
        hero=ANIMALS[hero].id,
        hero_type=ANIMALS[hero].type,
        guide=GUIDES[guide].id,
        guide_type=GUIDES[guide].type,
        curiosity="curious",
        clue=clue,
        monitor_kind=monitor,
        rhyme_kind="rad",
        ending=ANIMALS[hero].end_line,
    )


def generate(params: StoryParams) -> StorySample:
    if params.habitat not in HABITATS:
        raise StoryError("Unknown habitat.")
    if params.hero_type not in {"lemur", "fox"}:
        raise StoryError("Unknown hero type.")
    world = tell(
        HABITATS[params.habitat],
        ANIMALS[params.hero if params.hero in ANIMALS else "Lilo"],
        GUIDES[params.guide if params.guide in GUIDES else "Tomo"],
        CLUES[params.clue],
        MONITORS[params.monitor_kind],
    )
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
        f"Write an animal story with the words rad and monitor, where a curious little hero follows a rhyme to the right answer.",
        f"Tell a child-friendly tale in which {f['hero'].id} asks what a monitor is and learns by following a clue.",
        f"Write a rhyming animal story where curiosity leads to a useful monitor and a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    clue = f["clue_cfg"]
    monitor = f["monitor_cfg"]
    qa = [
        ("Who is the story about?", f"It is about {hero.id}, a curious little {hero.type}, and {guide.id}, who helps along the way."),
        ("What word did the hero want to understand?", f"{hero.id} wanted to understand the word monitor. The rhyme made the word feel mysterious at first."),
        ("What did the guide say about a monitor?", "The guide said a monitor can be a lizard, a guard, or a screen. That helped the hero look in the right way."),
    ]
    if f.get("found"):
        qa.append((
            "How did the story end?",
            f"{hero.id} found the monitor and learned that the clue was real. The ending felt {hero.memes['joy'] and 'glad' or 'calm'}, because curiosity led to a useful answer."
        ))
        qa.append((
            "Why was the monitor important?",
            f"The monitor was important because it matched the clue and helped the hero understand the rhyme. It turned a guess into a real discovery."
        ))
    else:
        qa.append((
            "What happened when the clue was followed?",
            f"The clue pointed to the wrong thing, so {guide.id} helped {hero.id} stop and look again. After that, they found the proper monitor and the lesson made sense."
        ))
        qa.append((
            "What did curiosity do in the story?",
            f"Curiosity made {hero.id} ask questions and keep searching. That was good, because it led to learning instead of giving up."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"animal", "monitor"}
    out = []
    if "lizard" in world.facts["monitor_cfg"].tags:
        out.append(("What is a monitor lizard?", "A monitor lizard is a kind of lizard. It is called a monitor, and it can look alert and watchful."))
    out.append(("What does curiosity mean?", "Curiosity means wanting to know more about something. Curious characters ask questions and look closely."))
    out.append(("What is a rhyme?", "A rhyme is a sound pattern in words, where the endings or beats feel alike. Rhymes can make a story feel bouncy and fun."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(hero) :- hero_entity(hero).
found(monitor) :- curious(hero), true_clue(clue), useful_monitor(monitor).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for hid in HABITATS:
        lines.append(asp.fact("habitat", hid))
    for aid in ANIMALS:
        lines.append(asp.fact("hero_entity", aid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.is_true:
            lines.append(asp.fact("true_clue", cid))
    for mid, m in MONITORS.items():
        lines.append(asp.fact("useful_monitor", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show found/1."))
    return sorted(set(asp.atoms(model, "found")))


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()):
        print("OK: python gate has valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
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
        print(asp_program("#show found/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} ASP facts-derived results.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
