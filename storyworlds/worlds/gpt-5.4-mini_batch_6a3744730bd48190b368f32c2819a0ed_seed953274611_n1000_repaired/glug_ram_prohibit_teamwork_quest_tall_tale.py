#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/glug_ram_prohibit_teamwork_quest_tall_tale.py
=============================================================================

A standalone story world in a tall-tale register: two helpers chase a quest,
ignore a prohibition, make a noisy mistake, and then succeed by working
together in a safer way. The required seed words are woven in as nouns/verbs:
glug, ram, prohibit.

The domain is a tiny harbor-and-reef adventure with:
- a quest for a hidden bell
- teamwork as the core turning force
- a guardian who prohibits the risky shortcut
- a comical mishap involving a glugging barrel
- a final, cooperative resolution that proves what changed

This script follows the Storyweavers contract:
- self-contained stdlib script
- imports results eagerly
- imports asp lazily
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, main
- supports --all, --seed, -n, --trace, --qa, --json, --asp, --verify,
  --show-asp
- includes Python validity gates plus an inline ASP twin
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    makes_noise: bool = False
    blocks: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "captain", "farmer"}
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
class Place:
    id: str
    label: str
    setting_line: str
    quest_name: str
    dark_spot: str
    has_glug_barrel: bool = False
    quest_risk: str = "depth"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
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
class Quest:
    id: str
    title: str
    prize: str
    verb: str
    route: str
    ending_image: str
    requires_teamwork: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    job: str
    safe: bool
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
class Guardian:
    id: str
    label: str
    warns: str
    forbids: str
    reason: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
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


def _r_glug(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("bobbing", 0.0) >= THRESHOLD and e.meters.get("noise", 0.0) < THRESHOLD:
            sig = ("glug", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["noise"] = e.meters.get("noise", 0.0) + 1.0
            out.append("__glug__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    team = [e for e in world.entities.values() if e.role in {"ram", "mapmate"}]
    if not team:
        return out
    if sum(e.memes.get("cooperate", 0.0) for e in team) >= 2.0:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in team:
                e.memes["pride"] = e.memes.get("pride", 0.0) + 1.0
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [Rule("glug", "physical", _r_glug), Rule("teamwork", "social", _r_teamwork)]


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


def predict(world: World, obstacle_id: str) -> dict:
    sim = world.copy()
    sim.get(obstacle_id).meters["bobbing"] = 1.0
    propagate(sim, narrate=False)
    return {
        "noise": sim.get(obstacle_id).meters.get("noise", 0.0),
        "stuck": sim.get("bridge").meters.get("stuck", 0.0),
    }


def reasonableness_ok(place: Place, quest: Quest) -> bool:
    return quest.requires_teamwork and place.quest_name == quest.title and place.has_glug_barrel


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for qid, quest in QUESTS.items():
            if reasonableness_ok(place, quest):
                combos.append((pid, qid))
    return combos


def join_names(a: str, b: str) -> str:
    return f"{a} and {b}"


def tell(place: Place, quest: Quest, leader_name: str, helper_name: str,
         leader_type: str, helper_type: str, tool: Tool, guardian: Guardian) -> World:
    world = World()
    leader = world.add(Entity(
        id=leader_name, kind="character", type=leader_type, role="ram",
        traits=["bold"], attrs={"relation": "partners"}, meters={"resolve": 0.0}, memes={"curiosity": 1.0}
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_type, role="mapmate",
        traits=["steady"], attrs={"relation": "partners"}, meters={"resolve": 0.0}, memes={"care": 1.0}
    ))
    world.add(Entity(id="bridge", type="bridge", label="the old bridge", meters={"stuck": 0.0}))
    world.add(Entity(id="barrel", type="barrel", label="a barrel", meters={"bobbing": 0.0, "noise": 0.0}))
    world.facts.update(place=place, quest=quest, leader=leader, helper=helper, tool=tool, guardian=guardian)

    world.say(
        f"Long ago, on {place.label}, {leader_name} and {helper_name} came striding out like two boots in one story. "
        f"{place.setting_line}"
    )
    world.say(
        f"They were after {quest.prize}, a prize fit for a tall tale, and the way there ran past {place.dark_spot}."
    )

    world.para()
    world.say(
        f"{leader_name} pointed the way and said they would {quest.verb}. "
        f"{helper_name} opened {helper_name}'s map, and the two of them promised to work as one team."
    )
    world.say(
        f"But the old guard {guardian.label} stepped out and said, \"{guardian.warns} "
        f"{guardian.forbids} because {guardian.reason}.\""
    )

    world.para()
    world.say(
        f"{leader_name} tried a shortcut anyway and set the barrel to bobbing while {helper_name} held the rope. "
        f"Then came the great {tool.job}: {tool.phrase}."
    )
    world.get("barrel").meters["bobbing"] = 1.0
    pred = predict(world, "barrel")
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_stuck"] = pred["stuck"]
    propagate(world, narrate=False)
    world.say(
        f"The barrel gave a loud glug, glug, glug, and the bridge shivered like it had heard thunder in a teacup."
    )

    world.para()
    leader.memes["cooperate"] += 1.0
    helper.memes["cooperate"] += 1.0
    world.say(
        f"Then {helper_name} called, {leader_name} answered, and both of them leaned together at once. "
        f"With {join_names(leader_name, helper_name)} pulling and bracing, they used {tool.label} the sensible way."
    )
    world.say(
        f"The barrel was steadied, the bridge was freed, and the path opened like a smile."
    )

    world.para()
    leader.meters["reward"] = 1.0
    helper.meters["reward"] = 1.0
    leader.memes["joy"] = leader.memes.get("joy", 0.0) + 1.0
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
    guardian.memes["relief"] = guardian.memes.get("relief", 0.0) + 1.0
    world.say(
        f"At last they reached {quest.prize} and carried it home in a single shining bundle of teamwork. "
        f"{quest.ending_image}"
    )

    world.facts["outcome"] = "won"
    return world


PLACES = {
    "harbor": Place(
        id="harbor",
        label="the harbor of Gull's End",
        setting_line="The masts stood straight as knitting needles, and the water slapped the docks in a rhythm that sounded half song and half dare.",
        quest_name="The Bell Below the Blue",
        dark_spot="the black water under the far pier",
        has_glug_barrel=True,
        quest_risk="water",
    ),
    "island": Place(
        id="island",
        label="the island of Lantern Tooth",
        setting_line="The palms bowed, the gulls quarreled, and the beach shone white as flour under the noon sun.",
        quest_name="The Bell Below the Blue",
        dark_spot="the cave mouth under the cliff",
        has_glug_barrel=True,
        quest_risk="cave",
    ),
}

QUESTS = {
    "bell": Quest(
        id="bell",
        title="The Bell Below the Blue",
        prize="the silver bell",
        verb="seek the silver bell",
        route="down the pier and past the deep tide",
        ending_image="The silver bell rang once, bright and far, as if the sea itself had winked.",
        requires_teamwork=True,
        tags={"quest", "teamwork"},
    ),
}

TOOLS = {
    "pole": Tool(
        id="pole",
        label="a long pole",
        phrase="the long pole",
        job="ram of the pole",
        safe=False,
        tags={"ram"},
    ),
    "hook": Tool(
        id="hook",
        label="a hooked staff",
        phrase="the hooked staff",
        job="glugging barrel and hook",
        safe=True,
        tags={"glug"},
    ),
}

GUARDIANS = {
    "captain": Guardian(
        id="captain",
        label="Captain Morrow",
        warns="The captain lifted a hand and roared,",
        forbids="Do not ram the barrel through the bridge",
        reason="the old planks would splash, crack, and throw the whole team off balance",
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Tess", "Ada", "June", "Ivy"]
BOY_NAMES = ["Bram", "Gus", "Finn", "Otto", "Reed", "Pax"]
TRAITS = ["steady", "bold", "quick-witted", "bright"]


@dataclass
class StoryParams:
    place: str
    quest: str
    leader: str
    helper: str
    leader_type: str
    helper_type: str
    tool: str
    guardian: str
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
    StoryParams(place="harbor", quest="bell", leader="Bram", helper="Mira", leader_type="boy", helper_type="girl", tool="hook", guardian="captain", seed=1),
    StoryParams(place="island", quest="bell", leader="Nell", helper="Gus", leader_type="girl", helper_type="boy", tool="hook", guardian="captain", seed=2),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale quest story world about teamwork, glug, and a forbidden ram.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--leader")
    ap.add_argument("--helper")
    ap.add_argument("--leader-type", choices=["boy", "girl"])
    ap.add_argument("--helper-type", choices=["boy", "girl"])
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
    if args.place and args.quest and not reasonableness_ok(PLACES[args.place], QUESTS[args.quest]):
        raise StoryError("That place and quest do not fit this story world.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest = rng.choice(sorted(combos))
    leader_type = args.leader_type or rng.choice(["boy", "girl"])
    helper_type = args.helper_type or ("girl" if leader_type == "boy" else "boy")
    leader_pool = BOY_NAMES if leader_type == "boy" else GIRL_NAMES
    helper_pool = GIRL_NAMES if helper_type == "girl" else BOY_NAMES
    leader = args.leader or rng.choice(leader_pool)
    helper = args.helper or rng.choice([n for n in helper_pool if n != leader])
    return StoryParams(
        place=place,
        quest=quest,
        leader=leader,
        helper=helper,
        leader_type=leader_type,
        helper_type=helper_type,
        tool=args.tool or "hook",
        guardian=args.guardian or "captain",
    )


def story_qa(world: World) -> list[tuple[str, str]]:
    p: Place = world.facts["place"]
    q: Quest = world.facts["quest"]
    leader: Entity = world.facts["leader"]
    helper: Entity = world.facts["helper"]
    guardian: Guardian = world.facts["guardian"]
    return [
        ("Who were the story's two helpers?",
         f"It was about {leader.id} and {helper.id}. They traveled like a pair of lanterns that learned how to shine together."),
        ("What were they trying to find?",
         f"They were trying to find {q.prize}. That prize was the heart of their quest, and the whole tale turned toward it."),
        ("What did the guardian forbid?",
         f"{guardian.label} forbade them from using a ram on the bridge. The bridge was old, and the guardian knew a hard shove could make trouble."),
        ("How did they succeed in the end?",
         f"They worked together, steadied the barrel, and used the tool the sensible way. Their teamwork opened the path and let them reach {q.prize}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is teamwork?",
         "Teamwork is when people help one another and use their different strengths together to do a job."),
        ("What is a quest?",
         "A quest is a journey to find something important or solve a big problem."),
        ("What does glug mean?",
         "Glug is the sound something makes when liquid or air moves through it in big bubbly gulps."),
        ("What does ram mean as a verb?",
         "To ram is to push or slam something hard into another thing."),
        ("What does prohibit mean?",
         "To prohibit means to say no and forbid something because it is unsafe or not allowed."),
    ]


def generation_prompts(world: World) -> list[str]:
    p: Place = world.facts["place"]
    q: Quest = world.facts["quest"]
    return [
        f'Write a tall-tale story about {p.label} where two helpers go on a quest for {q.prize}, and include the words "glug", "ram", and "prohibit".',
        f"Tell a child-friendly adventure in which teamwork beats a risky shortcut, and a guardian prohibits the ram but the quest still succeeds.",
        f"Write a story where a glugging barrel causes trouble, but two partners solve the quest together in a brave, old-fashioned tall-tale style.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    for mapping, key in ((PLACES, params.place), (QUESTS, params.quest), (TOOLS, params.tool), (GUARDIANS, params.guardian)):
        if key not in mapping:
            raise StoryError(f"Unknown story parameter: {key}")
    world = tell(
        PLACES[params.place], QUESTS[params.quest], params.leader, params.helper,
        params.leader_type, params.helper_type, TOOLS[params.tool], GUARDIANS[params.guardian]
    )
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_glug_barrel:
            lines.append(asp.fact("glug_barrel", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if q.requires_teamwork:
            lines.append(asp.fact("teamwork_needed", qid))
    lines.append(asp.fact("can_ram", "ram"))
    lines.append(asp.fact("can_prohibit", "guardian"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Q) :- place(P), quest(Q), glug_barrel(P), teamwork_needed(Q).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, quest=None, tool=None, guardian=None, leader=None, helper=None, leader_type=None, helper_type=None), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    return build_parser_impl()


def build_parser_impl() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale teamwork quest story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--leader")
    ap.add_argument("--helper")
    ap.add_argument("--leader-type", choices=["boy", "girl"])
    ap.add_argument("--helper-type", choices=["boy", "girl"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for p, q in asp_valid_combos():
            print(f"{p} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
