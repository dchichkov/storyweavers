#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/granulate_geography_repetition_teamwork_whodunit.py
===================================================================================

A small whodunit-style storyworld for a classroom geography mystery.

Premise:
- A group of children is preparing a geography display.
- Someone knocks over a tray, and tiny granulate-like crumbs and map pins go missing.
- The children solve the mystery through repetition, teamwork, and careful looking.

This world is deliberately tiny and classical:
- typed entities with physical meters and emotional memes
- forward-chained state changes
- reasonableness gates with an inline ASP twin
- three QA sets grounded in the simulated world state
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
SUSPECT_MIN = 1
TEAMWORK_MIN = 2


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
class Setting:
    id: str
    place: str
    display: str
    clues: list[str] = field(default_factory=list)
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
class Tool:
    id: str
    label: str
    use: str
    clue: str
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
class Mystery:
    id: str
    culprit: str
    motive: str
    method: str
    reveal: str
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
        self.scene_clues: list[str] = []

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
        c.scene_clues = list(self.scene_clues)
        c.paragraphs = [[]]
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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["repeat_search"] < THRESHOLD:
            continue
        sig = ("repeat", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["focus"] += 1
        out.append("__repeat__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if sum(1 for e in world.characters() if e.memes["helping"] >= THRESHOLD) >= TEAMWORK_MIN:
        sig = ("teamwork", "help")
        if sig not in world.fired:
            world.fired.add(sig)
            for e in world.characters():
                e.memes["confidence"] += 1
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule("repeat", "social", _r_repeat),
    Rule("teamwork", "social", _r_teamwork),
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


def clue_strength(world: World) -> int:
    return len(world.scene_clues)


def can_solve_with_repetition(world: World, mystery: Mystery) -> bool:
    return clue_strength(world) >= 2 and mystery.culprit in {c.id for c in world.characters()}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for tid in TOOLS:
                if MYSTERIES[mid].culprit and TOOLS[tid].label:
                    combos.append((sid, mid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    detective: str
    helper: str
    detective_gender: str
    helper_gender: str
    narrator: str
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


def assemble_clues(world: World, setting: Setting, mystery: Mystery, tool: Tool) -> None:
    world.scene_clues.extend(setting.clues)
    world.scene_clues.append(tool.clue)
    world.scene_clues.append(mystery.method)
    world.facts["clue_count"] = len(world.scene_clues)


def tell(world: World, setting: Setting, mystery: Mystery, tool: Tool,
         detective: Entity, helper: Entity, narrator: Entity) -> World:
    detective.memes["repeat_search"] = 1
    helper.memes["helping"] = 1
    detective.memes["worry"] = 1
    helper.memes["worry"] = 1

    world.say(
        f"On a bright afternoon, {detective.id} and {helper.id} set up a geography display "
        f"in {setting.place}. The room smelled like paper, pencils, and a little bit of "
        f"granulate sugar from the snack table."
    )
    world.say(
        f"Then the map pins went missing, and everyone wanted to know who had taken them."
    )

    world.para()
    world.say(
        f'"This is a geography mystery," {detective.id} said. "We will look again and again."'
    )
    world.say(
        f'"Again and again?" {helper.id} asked.'
    )
    world.say(
        f'"Again and again," {detective.id} said, and {helper.id} nodded.'
    )
    propagate(world, narrate=False)

    assemble_clues(world, setting, mystery, tool)
    world.facts["repetition"] = 3
    world.facts["teamwork"] = True

    world.para()
    world.say(
        f"They checked the floor, the map board, and the snack table. {setting.display}"
    )
    world.say(
        f"At first, they only found {tool.clue} and a trail of tiny crumbs."
    )
    world.say(
        f"Then they looked again."
    )
    world.say(
        f"Then they looked one more time."
    )

    culprit = world.get(mystery.culprit)
    culprit.memes["nervous"] += 1
    culprit.meters["guilt"] += 1
    if can_solve_with_repetition(world, mystery):
        world.para()
        world.say(
            f"The third look made the answer clear. {culprit.id} had leaned over the table, "
            f"knocked the pins into the sugar bowl, and tried to hide them under the atlas."
        )
        world.say(
            f"{helper.id} pointed to the granulate crumbs, and {detective.id} matched them to "
            f"the sugar on the table. Together they found every pin."
        )
        culprit.memes["relief"] += 1
        detective.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.para()
        world.say(
            f"{culprit.id} admitted it at once. {mystery.reveal} {mystery.motive}."
        )
        world.say(
            f"No one stayed angry for long. The whole group cleaned up together, and the "
            f"geography board looked neat again."
        )
        world.say(
            f"By the end, the children had solved the case by repeating their search and "
            f"helping one another."
        )
    else:
        world.para()
        world.say(
            f"The clues never quite fit together, so the children called a grown-up and kept "
            f"searching side by side until the missing pins turned up."
        )
        world.say(
            f"Even then, the best part was the teamwork: nobody searched alone."
        )

    world.facts.update(
        setting=setting,
        mystery=mystery,
        tool=tool,
        detective=detective,
        helper=helper,
        narrator=narrator,
        culprit=culprit,
        solved=True,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        display="The wall map still hung straight, and the compass rose on the poster seemed to watch everything.",
        clues=["a map pin on the floor", "a little line of sugar crumbs", "a smudge near the atlas"],
    ),
    "library": Setting(
        id="library",
        place="the library corner",
        display="The book cart stood nearby, and the atlas shelf had been left open.",
        clues=["a folded note", "a breadcrumb trail", "a map page with a corner turned up"],
    ),
    "clubroom": Setting(
        id="clubroom",
        place="the geography clubroom",
        display="The globe sat in the middle of the table like a patient witness.",
        clues=["a ruler by the globe", "two crumbs by the map tray", "a pin stuck in a chair cushion"],
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="a magnifying glass",
        use="look closely",
        clue="a round print from the magnifying glass",
        tags={"look"},
    ),
    "chalk": Tool(
        id="chalk",
        label="chalk",
        use="mark clues",
        clue="a chalky white streak",
        tags={"mark"},
    ),
    "string": Tool(
        id="string",
        label="string",
        use="measure the trail",
        clue="a string line across the desk",
        tags={"measure"},
    ),
}

MYSTERIES = {
    "mila": Mystery(
        id="mila",
        culprit="Mila",
        motive="She had been trying to hide that she moved the pins while reaching for the sugar bowl",
        method="She had bumped the tray while carrying snacks",
        reveal="Mila looked down and said she was sorry",
        tags={"whodunit"},
    ),
    "noah": Mystery(
        id="noah",
        culprit="Noah",
        motive="He wanted the display to look perfect before the teacher arrived",
        method="He had shoved the atlas too hard",
        reveal="Noah blushed and explained what happened",
        tags={"whodunit"},
    ),
    "zoe": Mystery(
        id="zoe",
        culprit="Zoe",
        motive="She was helping and forgot the pins were on the edge",
        method="She brushed the tray by accident",
        reveal="Zoe admitted the accident and helped sort the pins back into place",
        tags={"whodunit"},
    ),
}

GIRL_NAMES = ["Mila", "Zoe", "Lina", "Ava", "Nora"]
BOY_NAMES = ["Noah", "Eli", "Owen", "Theo", "Max"]
NARRATORS = ["teacher", "librarian", "helper"]


def explain_rejection(setting: Setting, mystery: Mystery, tool: Tool) -> str:
    return "(No story: this combination does not produce a useful whodunit.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small geography whodunit storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--narrator", choices=NARRATORS)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combinations.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    tool = args.tool or rng.choice(sorted(TOOLS))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if detective_gender == "girl" else "girl")
    detective = args.detective or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != detective]
    helper = args.helper or rng.choice(helper_pool)
    narrator = args.narrator or rng.choice(NARRATORS)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        tool=tool,
        detective=detective,
        helper=helper,
        detective_gender=detective_gender,
        helper_gender=helper_gender,
        narrator=narrator,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    mystery = MYSTERIES.get(params.mystery)
    tool = TOOLS.get(params.tool)
    if setting is None or mystery is None or tool is None:
        raise StoryError("Invalid params.")
    world = World()
    detective = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    narrator = world.add(Entity(id=params.narrator, kind="character", type="adult", role="narrator"))
    story_world = tell(world, setting, mystery, tool, detective, helper, narrator)
    return StorySample(
        params=params,
        story=story_world.render(),
        prompts=generation_prompts(story_world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(story_world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(story_world)],
        world=story_world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit story for a young child that includes the words "granulate" and "geography".',
        f"Tell a classroom mystery where {f['detective'].id} and {f['helper'].id} solve the case by repeating their search.",
        f"Write a teamwork mystery with a geography display, a sugar spill, and a clue that makes the culprit confess.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    culprit = f["culprit"]
    mystery = f["mystery"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        ("What kind of story is this?",
         "It is a whodunit about a classroom mystery. The children work together to find out what happened."),
        ("What subject was the class working on?",
         "They were working on geography, so maps, pins, and the globe were part of the scene."),
        ("Why did the children keep looking again and again?",
         "They kept repeating the search because the first clues were not enough. The repeated looking helped them notice the tiny crumbs and match them to the sugar on the table."),
        ("How did teamwork help?",
         f"{detective.id} and {helper.id} split the job and watched the clues together. Because they worked as a team, they found every pin and solved the mystery faster."),
        ("Who caused the mystery?",
         f"It was {culprit.id}. {mystery.reveal}."),
    ]
    if f.get("solved"):
        qa.append((
            "How did the story end?",
            "The children solved the case, cleaned the geography board, and made the room neat again. The ending feels calm because they used repetition and teamwork instead of giving up."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is geography?",
         "Geography is the study of places, maps, land, water, and how people live in different parts of the world."),
        ("What is a magnifying glass for?",
         "A magnifying glass helps you look at small things more closely."),
        ("Why do people repeat a search in a mystery?",
         "They repeat the search because a second or third look can reveal a clue they missed the first time."),
        ("What does teamwork mean?",
         "Teamwork means people help one another and share the job so they can solve a problem together."),
        ("What is granulate sugar?",
         "Granulate sugar is sugar made of tiny grains. The grains can spill and leave little crumbs that are easy to notice."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clues: {world.scene_clues}")
    lines.append(f"  fired: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
repeated(D) :- detective(D), repeat_search(D).
team_help :- helper(H), helping(H), detective(D), repeat_search(D).
solved :- repeated(_), team_help, clue_count(C), C >= 3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("culprit", m.culprit))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show repeated/1.\n#show solved/0.")
    model = asp.one_model(program)
    ok = True
    if model is None:
        ok = False
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
    except Exception:
        ok = False
    if ok:
        print("OK: ASP twin loads and story generation smoke test succeeded.")
        return 0
    print("FAIL: verify checks did not pass.")
    return 1


def asp_choices() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1.\n#show tool/1."))
    return sorted(set(asp.atoms(model, "setting")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show repeated/1.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="classroom", mystery="mila", tool="magnifier", detective="Mila", helper="Noah", detective_gender="girl", helper_gender="boy", narrator="teacher"),
            StoryParams(setting="library", mystery="noah", tool="chalk", detective="Noah", helper="Zoe", detective_gender="boy", helper_gender="girl", narrator="librarian"),
            StoryParams(setting="clubroom", mystery="zoe", tool="string", detective="Zoe", helper="Eli", detective_gender="girl", helper_gender="boy", narrator="teacher"),
        ]
        samples = [generate(p) for p in curated]
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
