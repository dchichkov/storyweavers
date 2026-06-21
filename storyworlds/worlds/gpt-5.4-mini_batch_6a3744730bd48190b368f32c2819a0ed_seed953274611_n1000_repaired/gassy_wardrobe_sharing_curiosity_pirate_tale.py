#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gassy_wardrobe_sharing_curiosity_pirate_tale.py
===============================================================================

A tiny standalone storyworld about pirate play, a curious peek into a wardrobe,
and a shared, very gassy surprise.

The world is intentionally small: two children are pretending to be pirates in a
bedroom, one is curious about a wardrobe, and a hidden, harmless smell-balloon
gets released. The turn is driven by a simulated world state: curiosity opens the
wardrobe, the smell swells, the children share what they have, and a calm adult
helps them make a fresh, safe ending.

This script follows the Storyweavers contract:
- stdlib-only story engine
- typed entities with meters and memes
- Python reasonableness gate plus inline ASP twin
- three Q&A sets grounded in world state
- --verify exercises both the ASP parity check and a real story generation run
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
SMELL_MIN = 1.0
CURIOUS_MIN = 2
SHARE_MIN = 2


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
    curious: bool = False
    shareable: bool = False
    wardrobe: bool = False
    gassy: bool = False

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    pirate_title: str
    mate_title: str
    quest: str
    hiding_place: str
    ship_word: str
    ending: str
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
class Smell:
    id: str
    label: str
    phrase: str
    source: str
    spread: int
    gassy: bool = True
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
class ShareItem:
    id: str
    label: str
    phrase: str
    helpful: str
    plural: bool = False
    shareable: bool = True
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_smell(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["gassy"] < THRESHOLD:
            continue
        sig = ("smell", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.characters():
            if kid.role in {"captain", "mate"}:
                kid.memes["discomfort"] += 1
        out.append("__smell__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["sharing"] < SHARE_MIN:
            continue
        sig = ("share", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["kindness"] += 1
        out.append("__share__")
    return out


CAUSAL_RULES = [Rule("smell", "physical", _r_smell), Rule("share", "social", _r_share)]


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


def problem_risky(smell: Smell, wardrobe: Entity) -> bool:
    return smell.gassy and wardrobe.wardrobe


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= CURIOUS_MIN]


def fireless_alt(response: Response, smell: Smell, delay: int) -> bool:
    return response.power >= smell.spread + delay


def predict_opening(world: World, smell_id: str) -> dict:
    sim = world.copy()
    _open_wardrobe(sim, sim.get("wardrobe"), narrate=False)
    return {
        "gassy": sim.get(smell_id).meters["gassy"] >= THRESHOLD,
        "discomfort": sum(k.memes["discomfort"] for k in sim.characters()),
    }


def _open_wardrobe(world: World, wardrobe: Entity, narrate: bool = True) -> None:
    wardrobe.meters["open"] += 1
    wardrobe.meters["swing"] += 1
    wardrobe.meters["gassy"] += 1
    propagate(world, narrate=narrate)


def _setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the bedroom into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.pirate_title} {a.id} and {theme.mate_title} {b.id}!" {a.id} '
        f'shouted. "Let\'s find {theme.quest}!"'
    )


def _curiosity(world: World, b: Entity, theme: Theme) -> None:
    b.memes["curiosity"] += 1
    world.say(
        f"But {theme.hiding_place} was dark and shut. {b.id} leaned closer, "
        f"curious about what might be hiding there."
    )
    world.say(f'"I wonder what is inside the wardrobe," {b.id} whispered.')


def _share(world: World, a: Entity, b: Entity, share: ShareItem) -> None:
    a.memes["sharing"] += 1
    b.memes["sharing"] += 1
    world.say(
        f'{a.id} grinned and offered to share {share.phrase}. '
        f"{b.id} nodded and shared the game too."
    )


def _open_and_smell(world: World, wardrobe: Entity, smell: Smell) -> None:
    _open_wardrobe(world, wardrobe)
    world.say(
        f"Click! The wardrobe door swung open, and out came a very {smell.label} "
        f"puff from {smell.source}."
    )
    world.say("For one tiny moment, the whole room wrinkled its nose.")


def _alarm(world: World, b: Entity, smell: Smell, parent: Entity) -> None:
    world.say(f'"{smell.label.capitalize()}!" {b.id} cried. "{parent.label_word.capitalize()}!"')


def _comfort(world: World, parent: Entity, response: Response, smell: Smell, a: Entity, b: Entity) -> None:
    body = response.text.replace("{smell}", smell.label)
    world.say(f"{parent.label_word.capitalize()} came in a hurry and {body}.")
    world.say(
        f"The smell drifted away, the wardrobe closed again, and {a.id} and {b.id} "
        f"could breathe easy."
    )


def _lesson(world: World, parent: Entity, a: Entity, b: Entity, smell: Smell, share: ShareItem) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say("Then everyone laughed softly, because the surprise was silly now that it was safe.")
    world.say(
        f'"Curiosity is good," {parent.id} said, hugging them both. '
        f'"But we share carefully, and we ask before opening things."'
    )
    world.say(
        f'"We promise," {a.id} and {b.id} said together, and {b.id} held up '
        f"{share.phrase} like a treasure map."
    )


def _end(world: World, parent: Entity, theme: Theme, share: ShareItem) -> None:
    world.say(
        f"The next day, {parent.label_word.capitalize()} left {share.phrase} on the "
        f"table, and the pirates played with it in the open air."
    )
    world.say(
        f"This time, they sailed on through {theme.ending} -- sharing, curious, and safe."
    )


def tell(theme: Theme, smell: Smell, share: ShareItem, response: Response,
         instigator: str = "Nia", instigator_gender: str = "girl",
         curious_child: str = "Milo", curious_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type=instigator_gender, role="captain"))
    b = world.add(Entity(id=curious_child, kind="character", type=curious_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    wardrobe = world.add(Entity(id="wardrobe", type="wardrobe", label="the wardrobe", wardrobe=True))
    smell_ent = world.add(Entity(id="smell", type="smell", label=smell.label, gassy=True))
    a.memes["sharing"] = 1.0
    b.memes["curiosity"] = 1.0
    world.facts["delay"] = delay

    _setup(world, a, b, theme)
    world.para()
    _curiosity(world, b, theme)
    _share(world, a, b, share)
    _open_and_smell(world, wardrobe, smell)

    world.para()
    _alarm(world, b, smell, parent)
    contained = fireless_alt(response, smell, delay)
    if contained:
        _comfort(world, parent, response, smell, a, b)
        _lesson(world, parent, a, b, smell, share)
        world.para()
        _end(world, parent, theme, share)
    else:
        world.say(f"{parent.label_word.capitalize()} tried to help, but the smell was too strong to tame quickly.")
        world.say("So they opened the windows, hurried outside, and waited for the fresh air to win.")
        world.say("The pirate game stopped for a while, but everyone stayed safe.")

    world.facts.update(
        instigator=a, curious=b, parent=parent, wardrobe=wardrobe, smell=smell_ent,
        share=share, response=response, theme=theme, outcome="contained" if contained else "escaped",
        gassy=wardrobe.meters["gassy"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a little pirate ship made from blankets and pillows",
        rig="The bed became a ship, a spoon became a spyglass, and a red scarf became a flag.",
        pirate_title="Captain",
        mate_title="Scout",
        quest="the lost shiny shell",
        hiding_place="The wardrobe",
        ship_word="ship",
        ending="a soft moonlit harbor",
    ),
    "island": Theme(
        id="island",
        scene="a stormy island made from chairs and sheets",
        rig="The rug was the beach, a toy cup was a boat, and a string of beads marked the treasure path.",
        pirate_title="Captain",
        mate_title="Navigator",
        quest="the hidden map",
        hiding_place="The wardrobe",
        ship_word="boat",
        ending="a bright tide pool",
    ),
}

SMELLS = {
    "gassy": Smell(id="gassy", label="gassy", phrase="a gassy puff", source="a tucked-away sock", spread=2, gassy=True),
    "stale": Smell(id="stale", label="gassy", phrase="a stale gassy puff", source="a dusty old blanket", spread=1, gassy=True),
}

SHARES = {
    "snacks": ShareItem(id="snacks", label="snacks", phrase="their crackers", helpful="for the game", plural=True),
    "map": ShareItem(id="map", label="map", phrase="the paper map", helpful="for the quest", plural=False),
    "lantern": ShareItem(id="lantern", label="lantern", phrase="the little lantern", helpful="for the cave", plural=False),
}

RESPONSES = {
    "open_windows": Response(
        id="open_windows",
        sense=3,
        power=3,
        text="opened the windows wide and fanned the air until the {smell} puff floated out",
        fail="opened the windows, but the {smell} puff still hung around",
        qa_text="opened the windows wide and fanned the air until the smell floated out",
    ),
    "fresh_sheet": Response(
        id="fresh_sheet",
        sense=2,
        power=2,
        text="covered the source with a fresh sheet and carried the smelly thing out to the hall",
        fail="covered the source, but the {smell} puff escaped anyway",
        qa_text="covered the source with a fresh sheet and carried the smelly thing out",
    ),
    "fan_and_wait": Response(
        id="fan_and_wait",
        sense=2,
        power=1,
        text="fanned the air and waited patiently for the smell to fade",
        fail="fanned the air, but the {smell} puff was too strong",
        qa_text="fanned the air and waited patiently for the smell to fade",
    ),
    "spray_perfume": Response(
        id="spray_perfume",
        sense=1,
        power=1,
        text="sprayed perfume everywhere, which only mixed with the {smell} puff",
        fail="sprayed perfume, but it only made the room more confusing",
        qa_text="sprayed perfume everywhere",
    ),
}


@dataclass
class StoryParams:
    theme: str
    smell: str
    share: str
    response: str
    instigator: str
    instigator_gender: str
    curious_child: str
    curious_gender: str
    parent: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid in THEMES:
        for sid, smell in SMELLS.items():
            for share_id in SHARES:
                if problem_risky(smell, Entity(id="wardrobe", wardrobe=True)):
                    combos.append((tid, sid, share_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale about curiosity, sharing, and a gassy wardrobe.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--smell", choices=SMELLS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response].sense < CURIOUS_MIN:
        raise StoryError(f"(Refusing response '{args.response}': it is too silly for a calm story.)")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.smell is None or c[1] == args.smell)
              and (args.share is None or c[2] == args.share)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, smell, share = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator = rng.choice(["Nia", "Ada", "Luna", "Mara"])
    curious_child = rng.choice([n for n in ["Milo", "Joss", "Theo", "Pip"] if n != instigator])
    instigator_gender = "girl"
    curious_gender = "boy"
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(theme=theme, smell=smell, share=share, response=response,
                       instigator=instigator, instigator_gender=instigator_gender,
                       curious_child=curious_child, curious_gender=curious_gender,
                       parent=parent, delay=rng.randint(0, 1))


def generate(params: StoryParams) -> StorySample:
    for key, table in [("theme", THEMES), ("smell", SMELLS), ("share", SHARES), ("response", RESPONSES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"invalid {key}: {getattr(params, key)}")
    world = tell(THEMES[params.theme], SMELLS[params.smell], SHARES[params.share], RESPONSES[params.response],
                 params.instigator, params.instigator_gender, params.curious_child, params.curious_gender,
                 params.parent, params.delay)
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
        f'Write a pirate tale for a 3-to-5-year-old that includes the words "gassy" and "wardrobe".',
        f"Tell a story where {f['instigator'].id} and {f['curious'].id} share a pirate game, then open a wardrobe out of curiosity and find a gassy surprise.",
        f"Write a gentle pirate story about curiosity, sharing, and a wardrobe smell that gets handled safely by a grown-up.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["instigator"], f["curious"], f["parent"]
    share, smell = f["share"], f["smell"]
    qa = [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, who were playing pirates and exploring the bedroom together. Their grown-up helped when the wardrobe smell turned surprising."),
        ("Why did they open the wardrobe?",
         f"{b.id} was curious and wanted to see what was inside the wardrobe. The curiosity moved the story forward and led to the gassy surprise."),
        ("How did they show sharing?",
         f"{a.id} offered {share.phrase}, and {b.id} shared the game too. Sharing kept the pirate play friendly even when the room got smelly."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "How did the grown-up help?",
            f"{parent.id} opened the windows and helped the smell drift out. That calm choice made the room fresh again and let the children keep playing safely."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a safe pirate game and a fresh room. The children remembered to ask before opening things and kept sharing kindly."
        ))
    else:
        qa.append((
            "What happened after the smell got out?",
            f"The smell was too strong to fix quickly, so the children opened the windows and waited outside. They stayed safe even though the pirate game paused for a while."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a wardrobe?",
         "A wardrobe is a piece of furniture used for storing clothes. It has doors you can open and close."),
        ("What does curious mean?",
         "Curious means wanting to know more about something. A curious child asks questions and looks carefully."),
        ("What does sharing mean?",
         "Sharing means letting someone else use or enjoy something with you. It can make play feel kinder and happier."),
        ("Why can a bad smell be unpleasant?",
         "A bad smell can make people wrinkle their noses and feel uncomfortable. Fresh air helps the room feel better again."),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.wardrobe:
            bits.append("wardrobe=True")
        if e.gassy:
            bits.append("gassy=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(theme="pirates", smell="gassy", share="snacks", response="open_windows",
                instigator="Nia", instigator_gender="girl", curious_child="Milo", curious_gender="boy",
                parent="mother", delay=0),
    StoryParams(theme="island", smell="stale", share="map", response="fresh_sheet",
                instigator="Ada", instigator_gender="girl", curious_child="Theo", curious_gender="boy",
                parent="father", delay=0),
]


ASP_RULES = r"""
gassy(W) :- wardrobe(W), smell(s1), smell_is_gassy(s1).
curious_now(C) :- child(C), curiosity(C, N), N >= curious_min.
shared(C) :- child(C), sharing(C, N), N >= share_min.
outcome(contained) :- gassy(wardrobe), response(R), power(R, P), smell(sp), spread(sp, S), delay(D), P >= S + D.
outcome(escaped) :- gassy(wardrobe), not outcome(contained).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for s, obj in SMELLS.items():
        lines.append(asp.fact("smell", s))
        if obj.gassy:
            lines.append(asp.fact("smell_is_gassy", s))
        lines.append(asp.fact("spread", s, obj.spread))
    for sh in SHARES:
        lines.append(asp.fact("share", sh))
    for r, obj in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("power", r, obj.power))
    lines.append(asp.fact("curious_min", CURIOUS_MIN))
    lines.append(asp.fact("share_min", SHARE_MIN))
    lines.append(asp.fact("wardrobe", "wardrobe"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("", "#show outcome/1.")
    model = asp.one_model(program)
    asp_outcome = asp.atoms(model, "outcome")
    py_outcome = "contained" if fireless_alt(RESPONSES["open_windows"], SMELLS["gassy"], 0) else "escaped"
    if (asp_outcome[0][0] if asp_outcome else "?") != py_outcome:
        print("MISMATCH: ASP outcome does not match Python outcome.")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"MISMATCH: generation smoke test failed: {e}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show gassy/1."))
    return sorted(set(asp.atoms(model, "gassy")))


def resolve_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    name = rng.choice(["Nia", "Ada", "Luna", "Mara"])
    other = rng.choice([n for n in ["Milo", "Joss", "Theo", "Pip"] if n != avoid and n != name])
    return name, other


def explain_rejection() -> str:
    return "(No story: this combination does not make a meaningful wardrobe surprise.)"


def explain_response(rid: str) -> str:
    return f"(Refusing response '{rid}': it is too clumsy for a gentle pirate tale.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is available; simple outcome is driven by a gassy wardrobe.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
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
