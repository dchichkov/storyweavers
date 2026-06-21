#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/worry_lady_reindeer_flashback_dialogue_quest_myth.py
=====================================================================================

A small storyworld in a mythic style: a worried lady hears an old flashback,
speaks with a reindeer, and goes on a quest to mend what was lost.

The domain is deliberately tiny and classical:
- a Lady carries worry in her heart,
- a Reindeer is both companion and guide,
- a sacred object or place is missing,
- a quest restores calm,
- a flashback explains why the worry began,
- dialogue gives the story its turning points.

The prose engine is driven by state, not by swapping nouns into one frozen text.
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
WORRY_BASE = 2.0


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
        feminine = {"lady", "woman", "queen", "mother"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "reindeer":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    dark: bool = False
    sacred: bool = False
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
class Relic:
    id: str
    label: str
    sacred: bool = True
    lost: bool = True
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
class QuestTool:
    id: str
    label: str
    kind: str
    helps: set[str] = field(default_factory=set)
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
    place: str
    relic: str
    tool: str
    lady_name: str
    reindeer_name: str
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
        self.flashback_done = False

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.flashback_done = self.flashback_done
        return w


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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    lady = world.get("lady")
    relic = world.get("relic")
    if lady.memes["worry"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if relic.meters["lost"] >= THRESHOLD:
        out.append("The lady's worry rose again because the relic was still missing.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    relic = world.get("relic")
    lady = world.get("lady")
    reindeer = world.get("reindeer")
    if relic.meters["found"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lady.memes["worry"] = 0.0
    lady.memes["relief"] += 1
    reindeer.memes["pride"] += 1
    out.append("Relief warmed the lady's chest, and the old worry loosened its grip.")
    return out


CAUSAL_RULES = [Rule("worry", "emotional", _r_worry), Rule("relief", "emotional", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for relic_id, relic in RELICS.items():
            if not place.dark or not relic.sacred:
                continue
            for tool_id, tool in TOOLS.items():
                if relic_id in tool.helps:
                    combos.append((place_id, relic_id, tool_id))
    return combos


def flashback_text(lady: Entity, relic: Relic, place: Place) -> str:
    return (
        f"Long before that night, {lady.id} had once walked the same path and heard "
        f"the bells of {place.label} go quiet. She had promised to keep {relic.label} "
        f"safe, and that promise returned now like an old song."
    )


def tell(place: Place, relic: Relic, tool: QuestTool, lady_name: str, reindeer_name: str) -> World:
    world = World()
    lady = world.add(Entity(id=lady_name, kind="character", type="lady", label="the lady", role="hero"))
    reindeer = world.add(Entity(id=reindeer_name, kind="character", type="reindeer", label="the reindeer", role="guide"))
    shrine = world.add(Entity(id="shrine", kind="thing", type="place", label=place.label, tags=set(place.tags)))
    relic_ent = world.add(Entity(id="relic", kind="thing", type="relic", label=relic.label, tags=set(relic.tags)))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, tags=set(tool.tags)))

    lady.memes["worry"] = WORRY_BASE
    relic_ent.meters["lost"] = 1.0
    world.facts.update(place=place, relic=relic, tool=tool, lady=lady, reindeer=reindeer, shrine=shrine)

    world.say(
        f"At {place.label}, {lady.id} stood under a pale sky and felt worry like a stone in her palm. "
        f"{reindeer.id} waited near her, calm as winter moonlight."
    )
    world.para()
    world.say(f'"What is wrong?" asked {reindeer.id}.')
    world.say(
        f'"{relic.label} is gone," said {lady.id}. "Without it, the old blessing will fade."'
    )
    world.para()
    world.say(flashback_text(lady, relic, place))
    world.say(
        f'"I remember," whispered {lady.id}. "I was told to keep watch, but I looked away."'
    )
    world.para()
    world.say(
        f'{reindeer.id} lowered its head and spoke like a lantern in the dark. '
        f'"Then let us go on a quest," it said. "The path is still waiting."'
    )
    world.say(
        f'"Will the path be kind?" asked {lady.id}. "It will be honest," said {reindeer.id}.'
    )
    world.para()

    # Quest action
    if "map" in tool.kind:
        world.say(
            f"They took the {tool.label} and followed its marks past stones and firs. "
            f"The {tool.label} showed where the wind had hidden the trail."
        )
    elif "horn" in tool.kind:
        world.say(
            f"They took the {tool.label}; its bright call echoed across the snow. "
            f"At last, a hollow tree answered, and the lost thing was near."
        )
    else:
        world.say(
            f"They took the {tool.label} and climbed by moon and hoofprint. "
            f"Every step made the worry smaller."
        )

    relic_ent.meters["found"] = 1.0
    world.say(
        f'At last {lady.id} found {relic.label} beside {place.label}, where frost had hidden it like a secret.'
    )
    propagate(world, narrate=False)
    world.para()
    world.say(
        f'"I found it," said {lady.id}. "And I did not find it alone."'
    )
    world.say(
        f'"That is why quests are sung," said {reindeer.id}. "So the brave heart remembers how it was helped."'
    )
    world.para()
    world.say(
        f"The lady carried {relic.label} home, and the first light on the shrine looked warm again."
    )

    world.facts.update(
        outcome="found",
        worry=lady.memes["worry"],
        relief=lady.memes["relief"],
        pride=reindeer.memes["pride"],
        relic_found=True,
    )
    return world


PLACES = {
    "frost_gate": Place(id="frost_gate", label="the Frost Gate", dark=True, sacred=True, tags={"gate", "dark"}),
    "moon_forest": Place(id="moon_forest", label="the moon forest", dark=True, sacred=True, tags={"forest", "dark"}),
    "stone_hall": Place(id="stone_hall", label="the stone hall", dark=True, sacred=True, tags={"hall", "dark"}),
}

RELICS = {
    "bell": Relic(id="bell", label="the silver bell", sacred=True, lost=True, tags={"bell", "sacred"}),
    "crown": Relic(id="crown", label="the winter crown", sacred=True, lost=True, tags={"crown", "sacred"}),
    "lamp": Relic(id="lamp", label="the star lamp", sacred=True, lost=True, tags={"lamp", "sacred"}),
}

TOOLS = {
    "map": QuestTool(id="map", label="an old map", kind="map", helps={"bell", "crown", "lamp"}, tags={"map"}),
    "horn": QuestTool(id="horn", label="a silver horn", kind="horn", helps={"bell", "crown", "lamp"}, tags={"horn"}),
    "lantern": QuestTool(id="lantern", label="a lantern of pine resin", kind="lantern", helps={"bell", "crown", "lamp"}, tags={"lantern"}),
}

LADY_NAMES = ["Astra", "Mira", "Nera", "Selene", "Iris", "Alia"]
REINDEER_NAMES = ["Brindle", "Snowstep", "Rime", "Northwind", "Comet", "Hearth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story that includes the words "worry", "lady", and "reindeer".',
        f"Tell a short myth where {f['lady'].id} feels worry, speaks with {f['reindeer'].id}, remembers a flashback, and goes on a quest for {f['relic'].label}.",
        f"Write a child-friendly myth with dialogue and a quest that ends when {f['lady'].id} brings back {f['relic'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lady = f["lady"]
    reindeer = f["reindeer"]
    relic = f["relic"]
    place = f["place"]
    return [
        QAItem(
            question="Why was the lady worried at the start?",
            answer=(
                f"She was worried because {relic.label} was missing, and she believed its loss would dim the old blessing. "
                f"The worry started before the quest and gave the story its first tension."
            ),
        ),
        QAItem(
            question="What did the reindeer do for her?",
            answer=(
                f"The reindeer listened, spoke gently, and led her on a quest. "
                f"Its calm voice helped turn her fear into motion."
            ),
        ),
        QAItem(
            question="What did the flashback add to the story?",
            answer=(
                f"The flashback showed that the lady had once promised to guard {relic.label}. "
                f"That memory explained why the missing relic felt so heavy to her."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended with {lady.id} finding {relic.label} at {place.label} and carrying it home again. "
                f"The ending image proves the worry was replaced by relief."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is worry?",
            answer=(
                "Worry is a heavy feeling you get when you fear something may be wrong. "
                "In a story, it often pushes a character to ask for help or search for what is missing."
            ),
        ),
        QAItem(
            question="What is a quest?",
            answer=(
                "A quest is a journey with a goal. "
                "Someone goes out looking for something important and does not stop until the goal is reached."
            ),
        ),
        QAItem(
            question="What is a flashback?",
            answer=(
                "A flashback is a scene that remembers an earlier time. "
                "It helps explain why the present moment matters so much."
            ),
        ),
        QAItem(
            question="Why do stories use dialogue?",
            answer=(
                "Dialogue lets characters speak for themselves. "
                "It makes a story feel alive and shows how the characters change in the moment."
            ),
        ),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(place: Place, relic: Relic) -> str:
    return (
        f"(No story: {place.label} is not a good quest site for a missing sacred thing, "
        f"or {relic.label} is not a suitable relic for this myth.)"
    )


def valid_params(params: StoryParams) -> bool:
    return params.place in PLACES and params.relic in RELICS and params.tool in TOOLS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    keys = list(PLACES)
    relic_keys = list(RELICS)
    tool_keys = list(TOOLS)

    if args.place and args.place not in PLACES:
        raise StoryError("(No story: unknown place.)")
    if args.relic and args.relic not in RELICS:
        raise StoryError("(No story: unknown relic.)")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("(No story: unknown quest tool.)")

    place_id = args.place or rng.choice(keys)
    relic_id = args.relic or rng.choice(relic_keys)
    tool_id = args.tool or rng.choice(tool_keys)

    if not valid_combos() or (place_id, relic_id, tool_id) not in valid_combos():
        if args.place or args.relic or args.tool:
            raise StoryError(explain_rejection(PLACES[place_id], RELICS[relic_id]))

    lady_name = args.lady or rng.choice(LADY_NAMES)
    reindeer_name = args.reindeer or rng.choice(REINDEER_NAMES)
    return StoryParams(
        place=place_id,
        relic=relic_id,
        tool=tool_id,
        lady_name=lady_name,
        reindeer_name=reindeer_name,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_params(params):
        raise StoryError("(No story: invalid parameters.)")
    world = tell(PLACES[params.place], RELICS[params.relic], TOOLS[params.tool], params.lady_name, params.reindeer_name)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld about worry, a lady, a reindeer, and a quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--lady")
    ap.add_argument("--reindeer")
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


CURATED = [
    StoryParams(place="frost_gate", relic="bell", tool="map", lady_name="Astra", reindeer_name="Brindle", seed=None),
    StoryParams(place="moon_forest", relic="crown", tool="horn", lady_name="Mira", reindeer_name="Snowstep", seed=None),
    StoryParams(place="stone_hall", relic="lamp", tool="lantern", lady_name="Selene", reindeer_name="Rime", seed=None),
]


ASP_RULES = r"""
place(P) :- place_fact(P).
relic(R) :- relic_fact(R).
tool(T) :- tool_fact(T).
valid(P,R,T) :- place(P), relic(R), tool(T), dark_place(P), sacred_relic(R), helps(T,R).
found(R) :- quest_started, valid(_,R,_).
relief :- found(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        if p.dark:
            lines.append(asp.fact("dark_place", pid))
        if p.sacred:
            lines.append(asp.fact("sacred_place", pid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic_fact", rid))
        if r.sacred:
            lines.append(asp.fact("sacred_relic", rid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_fact", tid))
        for rel in t.helps:
            lines.append(asp.fact("helps", tid, rel))
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
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid combo sets differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAILED: generate() smoke test crashed: {exc}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for p, r, t in combos:
            print(f"{p} {r} {t}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
