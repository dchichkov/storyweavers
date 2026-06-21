#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dam_bemoan_shallot_cautionary_magic_quest_whodunit.py
====================================================================================

A standalone story world for a small whodunit-style magic quest.

Premise:
- A child-led quest investigates a puzzling missing shallot near a dam.
- Magic is present, but the story is cautionary: spells are useful only when used
  carefully, and grown-ups keep everyone safe.
- The whodunit shape comes from clues, suspects, and a reveal driven by world
  state rather than frozen prose.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes Python valid-combos gating and inline ASP twin
- generates story-grounded QA and world-knowledge QA from world state
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
SENSE_MIN = 2

NAME_POOL = [
    "Mina", "Pip", "Nora", "Elio", "Tess", "Lena", "Owen", "Bram", "Ada", "Jules"
]
GENDERS = ["girl", "boy"]
TRAITS = ["careful", "curious", "patient", "thoughtful", "steady", "brave"]


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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    clue_line: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Quest:
    id: str
    goal: str
    quest_noun: str
    search_word: str
    end_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    safe: bool
    power: int
    sense: int
    action: str
    hint: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    clue: str
    alibi: str
    suspicious: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_clue(world: World) -> list[str]:
    out = []
    if world.facts.get("seen_peel") and not world.facts.get("pieced_together"):
        sig = ("clue", "peel")
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["pieced_together"] = True
            out.append("__clue__")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    if world.facts.get("case_solved") and not world.facts.get("relief_spoken"):
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["relief_spoken"] = True
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("clue", "mystery", _r_clue),
    Rule("relief", "social", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
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


def cautious_gate(tool: MagicTool) -> bool:
    return tool.sense >= SENSE_MIN and tool.safe


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUESTS:
            for tid in TOOLS:
                if cautious_gate(TOOLS[tid]):
                    combos.append((sid, qid, tid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    tool: str
    investigator: str
    investigator_gender: str
    helper: str
    helper_gender: str
    witness: str
    witness_gender: str
    suspect: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a cautionary magic whodunit quest around a dam and a shallot."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--investigator")
    ap.add_argument("--helper")
    ap.add_argument("--witness")
    ap.add_argument("--suspect", choices=SUSPECTS)
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


def _pick_name(rng: random.Random, used: set[str] = set()) -> tuple[str, str]:
    gender = rng.choice(GENDERS)
    pool = [n for n in NAME_POOL if n not in used]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and not cautious_gate(TOOLS[args.tool]):
        raise StoryError(f"(No story: {args.tool} is not a cautious enough magic tool.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, tool = rng.choice(sorted(combos))
    inv = args.investigator or rng.choice(NAME_POOL)
    helper = args.helper or rng.choice([n for n in NAME_POOL if n != inv])
    witness = args.witness or rng.choice([n for n in NAME_POOL if n not in {inv, helper}])
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    return StoryParams(
        setting=setting,
        quest=quest,
        tool=tool,
        investigator=inv,
        investigator_gender=rng.choice(GENDERS),
        helper=helper,
        helper_gender=rng.choice(GENDERS),
        witness=witness,
        witness_gender=rng.choice(GENDERS),
        suspect=suspect,
    )


def predict(world: World, quest: Quest, suspect: Suspect) -> dict:
    sim = world.copy()
    sim.facts["seen_peel"] = suspect.suspicious
    propagate(sim, narrate=False)
    return {"solved": sim.facts.get("pieced_together", False)}


def tell(setting: Setting, quest: Quest, tool: MagicTool, suspect: Suspect,
         investigator: Entity, helper: Entity, witness: Entity, captain: Entity) -> World:
    world = World()
    world.add(investigator)
    world.add(helper)
    world.add(witness)
    world.add(captain)

    investigator.memes["curiosity"] += 1
    helper.memes["care"] += 1
    witness.memes["watchfulness"] += 1

    world.say(
        f"At {setting.place}, {investigator.id} and {helper.id} began a {quest.quest_noun} for the lost shallot."
    )
    world.say(
        f"The old dam sat nearby, and the air felt {setting.mood}; {setting.clue_line}"
    )
    world.say(
        f'{investigator.id} held {tool.phrase} and said, "{tool.hint}"'
    )

    world.para()
    world.say(
        f"{witness.id} noticed a clue near the stone path: a peeled bit of onion skin."
    )
    world.facts["seen_peel"] = suspect.suspicious
    if not suspect.suspicious:
        world.say(
            f"But {suspect.label} had an alibi: {suspect.alibi}."
        )
    else:
        world.say(
            f"{suspect.label} looked suspicious, because {suspect.clue}."
        )

    world.para()
    pred = predict(world, quest, suspect)
    if pred["solved"]:
        world.say(
            f'{helper.id} bemoaned the missing shallot at first, but then pointed to the clue and said, "The peel means someone carried it away."'
        )
        world.say(
            f"{investigator.id} used {tool.action} carefully, not to cast a wild spell but to brighten the damp stones."
        )
        world.facts["case_solved"] = True
        world.facts["mystery_answer"] = suspect.label
        propagate(world, narrate=False)
        world.say(
            f"At last, the truth came clear: {suspect.label} had taken the shallot to the kitchen basket, safe from the river spray."
        )
        world.say(
            f"{captain.label_word.capitalize()} smiled and said the best magic was the kind that helped, not the kind that rushed."
        )
        world.para()
        world.say(
            f"{quest.end_image} The quest ended with the shallot returned, the dam quiet, and everyone walking home with clean boots and lighter hearts."
        )
    else:
        world.say(
            f"The clue led nowhere, and the children had to call for a grown-up to keep the quest safe."
        )
        world.say(
            f"In the end, they still learned to use the magic carefully and never guess too quickly."
        )
        world.facts["case_solved"] = False

    world.facts.update(
        setting=setting, quest=quest, tool=tool, suspect=suspect,
        investigator=investigator, helper=helper, witness=witness, captain=captain
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a cautionary magic whodunit for a child that includes the words dam, bemoan, and shallot.",
        f"Tell a small quest story where {f['investigator'].id} and {f['helper'].id} search for a missing shallot near a dam and solve the mystery with careful magic.",
        f"Write a mystery story for a young child in which the clue is a peeled bit of onion skin and the ending shows the shallot returned safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    suspect = f["suspect"]
    inv = f["investigator"]
    helper = f["helper"]
    qa = [
        QAItem(
            question="What were the children trying to find?",
            answer="They were trying to find the missing shallot. The whole quest began because it had gone missing near the dam."
        ),
        QAItem(
            question="What clue helped them solve the mystery?",
            answer="A peeled bit of onion skin helped them think it through. That clue showed that someone had carried the shallot away, so they stopped guessing and looked more carefully."
        ),
        QAItem(
            question=f"Why did {helper.id} bemoan the missing shallot?",
            answer=f"{helper.id} bemoaned it because the shallot was gone and the search had become confusing. The worry made the mystery feel bigger until the clue gave them a steadier path."
        ),
        QAItem(
            question=f"Who took the shallot?",
            answer=f"{suspect.label} took the shallot, but not in a mean way. The clue and the alibi showed that {suspect.label} had moved it to the kitchen basket to keep it safe."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dam?",
            answer="A dam is a wall or barrier built across water to hold it back or control how it flows."
        ),
        QAItem(
            question="What is a shallot?",
            answer="A shallot is a small onion with a mild taste. People often use it in cooking."
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it gives a warning or lesson about being careful. A cautionary story helps children notice what to avoid."
        ),
        QAItem(
            question="What does whodunit mean?",
            answer="A whodunit is a mystery story where you have to figure out who did something. It usually includes clues, guesses, and a reveal at the end."
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something impossible or special that happens in a story. In a careful story, magic should help solve problems without making things unsafe."
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
            bits.append(f"attrs={ {k: v for k, v in e.attrs.items() if v} }")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


SETTINGS = {
    "riverbank": Setting("riverbank", "the riverbank beside the dam", "cool and misty", "A wet stone path curved under the old railings."),
    "kitchen": Setting("kitchen", "the kitchen with the open window", "warm and busy", "A cutting board waited on the table near a bowl of herbs."),
    "garden": Setting("garden", "the garden path by the dam", "fresh and quiet", "The onions had been gathered in a wicker basket earlier."),
}

QUESTS = {
    "search": Quest("search", "find the missing shallot", "search", "look for clues", "The last lantern glow touched the water."),
    "rescue": Quest("rescue", "rescue the shallot from the mystery", "rescue", "follow the trail", "The little basket sat safely by the step."),
}

TOOLS = {
    "glowstone": MagicTool("glowstone", "glowstone", "a glowstone lantern", True, 2, 3, "glow with a soft gold light", "It can light a path without flaring up."),
    "mirror": MagicTool("mirror", "polished mirror charm", "a polished mirror charm", True, 2, 2, "bounce light into the shadows", "It helps them see clues without touching anything dangerous."),
    "bubble": MagicTool("bubble", "bubble charm", "a bubble charm", True, 3, 2, "raise a careful bubble of light", "It makes a harmless shimmer for finding clues."),
}

SUSPECTS = {
    "mouse": Suspect("mouse", "the mouse", "scout", "there were tiny pawprints near the basket", "it had been nibbling crumbs by the stove", suspicious=False),
    "cook": Suspect("cook", "the cook", "helper", "the cook had flour on the sleeves and a basket nearby", "the cook was making soup and had moved the onion pieces for supper", suspicious=True),
    "cat": Suspect("cat", "the cat", "watcher", "the cat had been curled under the chair all morning", "the cat never climbed the counter", suspicious=False),
}


def valid_suspect_for_story(setting: Setting, suspect: Suspect) -> bool:
    return True


CURATED = [
    StoryParams("garden", "search", "glowstone", "Mina", "girl", "Pip", "boy", "Nora", "girl", "cook"),
    StoryParams("riverbank", "rescue", "mirror", "Elio", "boy", "Tess", "girl", "Bram", "boy", "mouse"),
    StoryParams("kitchen", "search", "bubble", "Ada", "girl", "Owen", "boy", "Jules", "boy", "cook"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.safe:
            lines.append(asp.fact("safe", tid))
        lines.append(asp.fact("sense", tid, t.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
cautious(T) :- tool(T), safe(T), sense(T, S), sense_min(M), S >= M.
valid(S, Q, T) :- setting(S), quest(Q), cautious(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show cautious/1."))
    return sorted(t for (t,) in asp.atoms(model, "cautious"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) == {t for t, x in TOOLS.items() if cautious_gate(x)}:
        print("OK: cautious tools match.")
    else:
        rc = 1
        print("MISMATCH in cautious tools.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, quest=None, tool=None, investigator=None, helper=None,
            witness=None, suspect=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def resolve_name(rng: random.Random) -> tuple[str, str]:
    return _pick_name(rng, set())


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    tool = TOOLS[params.tool]
    suspect = SUSPECTS[params.suspect]

    inv = Entity(params.investigator, kind="character", type=params.investigator_gender, role="investigator")
    helper = Entity(params.helper, kind="character", type=params.helper_gender, role="helper")
    witness = Entity(params.witness, kind="character", type=params.witness_gender, role="witness")
    captain = Entity("Captain", kind="character", type="mother", role="grownup", label="the captain")

    world = tell(setting, quest, tool, suspect, inv, helper, witness, captain)
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
        print(asp_program("", "#show valid/3.\n#show cautious/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("cautious tools:", ", ".join(asp_sensible()))
        print()
        for s, q, t in asp_valid_combos():
            print(f"{s:10} {q:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.investigator} & {p.helper}: {p.quest} / {p.tool} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
