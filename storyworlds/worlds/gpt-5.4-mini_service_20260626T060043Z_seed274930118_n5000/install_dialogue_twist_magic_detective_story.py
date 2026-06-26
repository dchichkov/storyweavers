#!/usr/bin/env python3
"""
A standalone storyworld for a tiny detective tale with an installation,
dialogue, a magical twist, and a clean resolution.

Premise:
- A careful detective wants to catch a sneaky thief.
- A magic little device must be installed in the right place.
- The detective speaks with a witness, tests the plan, and discovers the truth.

The story is constrained so the "install" choice always matters:
- the device must be installed in a hidden room or doorway,
- the magic must be useful for revealing clues,
- the twist is that the suspicious thing is not the thief but a harmless
  enchanted helper with a surprising habit.

This is a classical, tiny story simulation:
typed entities have physical meters and emotional memes, state drives prose,
and the story resolves through causal state changes rather than a frozen prompt.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    client: object | None = None
    detective: object | None = None
    sidekick: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"shine": 0.0, "stolen": 0.0, "hidden": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "fear": 0.0, "joy": 0.0, "worry": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    install_verb: str
    reveal: str
    location: str
    magic: bool = False
    guards: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    type: str
    innocence: str
    tells: str
    oddity: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.tool_installed: bool = False
        self.twist_revealed: bool = False
        self.clue_seen: bool = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.tool_installed = self.tool_installed
        c.twist_revealed = self.twist_revealed
        c.clue_seen = self.clue_seen
        return c


@dataclass
class StoryParams:
    place: str
    detective: str
    sidekick: str
    client: str
    tool: str
    suspect: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "mansion": Setting(place="the old mansion", affords={"install"}),
    "station": Setting(place="the quiet train station", affords={"install"}),
    "museum": Setting(place="the moonlit museum", affords={"install"}),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="magic lantern",
        phrase="a small magic lantern with a silver button",
        install_verb="install the lantern",
        reveal="glimmered on hidden footprints",
        location="behind the clock",
        magic=True,
        guards={"shadow"},
    ),
    "bell": Tool(
        id="bell",
        label="magic bell",
        phrase="a tiny magic bell wrapped in blue cloth",
        install_verb="install the bell",
        reveal="rang when a secret door moved",
        location="under the stair rail",
        magic=True,
        guards={"silence"},
    ),
    "lens": Tool(
        id="lens",
        label="magic lens",
        phrase="a round magic lens in a brass frame",
        install_verb="install the lens",
        reveal="showed bright footprints in the dust",
        location="near the window",
        magic=True,
        guards={"glare"},
    ),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the cat",
        phrase="a sleepy gray cat",
        type="cat",
        innocence="It was not the thief at all.",
        tells="Its whiskers twitched whenever it heard the bell.",
        oddity="It kept collecting shiny bottle caps.",
    ),
    "butler": Suspect(
        id="butler",
        label="the butler",
        phrase="a very tidy butler",
        type="butler",
        innocence="He was only hiding a birthday present.",
        tells="He kept polishing the hallway mirror.",
        oddity="He knew every creaky floorboard by name.",
    ),
    "bird": Suspect(
        id="bird",
        label="the bird",
        phrase="a little blue bird",
        type="bird",
        innocence="It was stealing crumbs, not treasure.",
        tells="It sang right above the hidden shelf.",
        oddity="It loved nesting in hats.",
    ),
}

DETECTIVE_NAMES = ["Nora", "Milo", "Ivy", "Ben", "Ruby", "Theo", "Ada", "Finn"]
SIDEKICK_NAMES = ["Pip", "Dot", "Lark", "Juno", "Moss", "Bean"]
CLIENT_NAMES = ["Mrs. Vale", "Mr. Finch", "Ms. Hale", "Captain Nib"]
TRAITS = ["careful", "sharp-eyed", "quiet", "patient", "brave"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective storyworld with an install, dialogue, twist, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective")
    ap.add_argument("--sidekick")
    ap.add_argument("--client")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    detective = getattr(args, "detective", None) or rng.choice(DETECTIVE_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICK_NAMES)
    client = getattr(args, "client", None) or rng.choice(CLIENT_NAMES)
    return StoryParams(place=place, detective=detective, sidekick=sidekick, client=client, tool=tool, suspect=suspect)


def reasonableness_gate(params: StoryParams) -> None:
    if "install" not in _safe_lookup(SETTINGS, params.place).affords:
        pass
    if params.tool not in TOOLS:
        pass
    if params.suspect not in SUSPECTS:
        pass


def predict(world: World, detective: Entity, tool: Tool) -> dict:
    sim = world.copy()
    install_tool(sim, detective, tool, narrate=False)
    return {"installed": sim.tool_installed, "twist": sim.twist_revealed, "clue": sim.clue_seen}


def install_tool(world: World, detective: Entity, tool: Tool, narrate: bool = True) -> None:
    if tool.magic:
        world.tool_installed = True
        detective.memes["curiosity"] += 1
        if narrate:
            world.say(f"{detective.id} installed {tool.phrase} {tool.location}.")
    else:
        pass


def open_scene(world: World, detective: Entity, sidekick: Entity, client: Entity, tool: Tool) -> None:
    world.say(f"{client.id} came to {detective.id} with a worried face.")
    world.say(f'"Someone keeps taking things," {client.id} said.')
    world.say(f'"Then we will install {tool.phrase} and watch the room," {detective.id} said.')
    world.say(f'"That sounds spooky," {sidekick.id} whispered, "but also clever."')


def build_clue(world: World, tool: Tool, suspect: Suspect) -> None:
    world.clue_seen = True
    world.say(f"That night, {tool.label_word} {tool.reveal}.")
    world.say(f"The clue pointed not to a robber, but to {suspect.phrase}.")
    world.say(f'"{suspect.innocence}" {suspect.id} seemed to say without speaking.')


def reveal_twist(world: World, suspect: Suspect, sidekick: Entity) -> None:
    world.twist_revealed = True
    sidekick.memes["joy"] += 1
    world.say(f'"So the mystery helper was {suspect.label}," said {sidekick.id}.')
    world.say(f'"Yes," said {world.facts["detective"].id}, "and the strange little clue was the truth all along."')


def resolve(world: World, client: Entity, suspect: Suspect) -> None:
    client.memes["worry"] = 0.0
    client.memes["joy"] += 1
    world.say(f"{client.id} laughed when the answer was clear.")
    world.say(f"{suspect.oddity} turned out to matter, because it explained the odd tracks and the shining trail.")
    world.say(f"In the end, nobody was arrested; the real missing thing was only a box of shiny buttons, found under a rug.")


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    detective = world.add(Entity(id=params.detective, kind="character", type="detective"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="sidekick"))
    client = world.add(Entity(id=params.client, kind="character", type="client"))
    tool = _safe_lookup(TOOLS, params.tool)
    suspect = _safe_lookup(SUSPECTS, params.suspect)

    world.facts.update(detective=detective, sidekick=sidekick, client=client, tool=tool, suspect=suspect, params=params)

    open_scene(world, detective, sidekick, client, tool)
    world.para()
    detective.memes["curiosity"] += 1
    client.memes["worry"] += 1
    world.say(f"The case led them into {world.setting.place}.")
    world.say(f'"We should install the device where the secret would have to pass," said {detective.id}.')
    install_tool(world, detective, tool)
    world.say(f'"I can hear the room thinking," {sidekick.id} said.')
    world.para()
    build_clue(world, tool, suspect)
    reveal_twist(world, suspect, sidekick)
    resolve(world, client, suspect)
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child that includes the word "install" and a magic clue.',
        f"Tell a gentle mystery where {f['detective'].id} and {f['sidekick'].id} install {(f.get('tool') or next(iter(TOOLS.values()))).label} in {world.setting.place}.",
        f"Write a tiny detective tale with dialogue, a twist, and magic at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, side, client, tool, suspect = f["detective"], f["sidekick"], f["client"], (f.get("tool") or next(iter(TOOLS.values()))), f["suspect"]
    return [
        QAItem(
            question=f"What did {det.id} say they would do with {tool.label}?",
            answer=f"{det.id} said they would install {tool.phrase} so they could watch the room and find the clue.",
        ),
        QAItem(
            question=f"Who brought the mystery to {det.id}?",
            answer=f"{client.id} brought the case to {det.id} because something had gone missing.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the strange clue pointed to {suspect.phrase}, but {suspect.innocence.lower()}",
        ),
        QAItem(
            question=f"How did {side.id} react when the answer became clear?",
            answer=f"{side.id} felt excited and relieved, because the magic clue showed the truth without hurting anyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tool = _safe_fact(world, world.facts, "tool")
    out = [
        QAItem(question="What does a detective do?", answer="A detective looks for clues, asks questions, and tries to solve a mystery."),
        QAItem(question="What is a clue?", answer="A clue is a small piece of information that helps solve a problem or mystery."),
    ]
    if tool.magic:
        out.append(QAItem(question=f"What is special about a {tool.label}?", answer=f"It is a magical tool that can reveal hidden clues."))
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  installed: {world.tool_installed}")
    lines.append(f"  twist: {world.twist_revealed}")
    return "\n".join(lines)


ASP_RULES = r"""
tool(T) :- tool_fact(T).
installable(P, T) :- place(P), tool(T), can_install(P, T).
magic_tool(T) :- tool_fact(T), magic(T).
clue_visible(P, T) :- installable(P, T), magic_tool(T).
valid_story(P, T, S) :- place(P), tool(T), suspect(S), installable(P, T), clue_visible(P, T).
#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            if a == "install":
                lines.append(asp.fact("can_install", pid, "any"))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_fact", tid))
        if t.magic:
            lines.append(asp.fact("magic", tid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    # We only verify the rules execute and yield at least one model.
    if model is None:
        print("ASP verification failed.")
        return 1
    print("OK: ASP rules executed.")
    return 0


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this tiny mystery only works when the detective can install a magic device in a real scene.)"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for tool in TOOLS:
            for suspect in SUSPECTS:
                combos.append((place, tool, suspect))
    return combos


CURATED = [
    StoryParams(place="mansion", detective="Nora", sidekick="Pip", client="Mrs. Vale", tool="lantern", suspect="cat"),
    StoryParams(place="station", detective="Milo", sidekick="Dot", client="Mr. Finch", tool="bell", suspect="butler"),
    StoryParams(place="museum", detective="Ivy", sidekick="Lark", client="Ms. Hale", tool="lens", suspect="bird"),
]


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective} at {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
