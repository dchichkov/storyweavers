#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/upholstery_dialogue_sound_effects_surprise_tall_tale.py
======================================================================================

A standalone storyworld for a tall-tale style story about upholstery, dialogue,
sound effects, and a surprise.

Domain premise
--------------
A child and a grandparent are trying to fix a sagging old chair or sofa. The
upholstery is torn or loose, the room is full of noisy, oversized tools, and the
repair turns into a bigger, stranger adventure than expected. The story stays
child-facing, concrete, and state-driven: cloth tightens, stuffing shifts, sound
effects happen, and a final surprise proves what changed.

The world supports:
- complete story generation
- three separate QA sets grounded in the world state
- trace output
- JSON output
- an inline ASP twin and a Python reasonableness gate
- verification that the Python and ASP checks match and that generation works
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



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
    room: str

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
class UpholsteryItem:
    id: str
    label: str
    phrase: str
    material: str
    can_sag: bool = True
    can_tighten: bool = True
    can_hide: bool = False

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
class Tool:
    id: str
    label: str
    sound: str
    effect: str
    risky: bool = False

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
class Surprise:
    id: str
    label: str
    reveal: str
    outcome: str

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    tool: str
    surprise: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
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


SETTINGS = {
    "parlor": Setting("parlor", "the parlor", "warm and dusty", "old family room"),
    "porch": Setting("porch", "the porch", "windy and bright", "screened porch"),
    "attic": Setting("attic", "the attic", "hot and creaky", "storage loft"),
}

UPHOLSTERY = {
    "sofa": UpholsteryItem("sofa", "sofa", "the sofa", "plush cloth"),
    "chair": UpholsteryItem("chair", "chair", "the big chair", "velvet"),
    "bench": UpholsteryItem("bench", "bench", "the long bench", "striped canvas"),
}

TOOLS = {
    "needle": Tool("needle", "needle and thread", "fsssst-fsssst", "stitches the seam"),
    "tacker": Tool("tacker", "staple tacker", "clack-clack-CLAP", "pins the cloth tight", risky=True),
    "glue": Tool("glue", "glue pot", "glub-glub", "sticks the edge down"),
}

SURPRISES = {
    "kitten": Surprise("kitten", "kitten", "a tiny kitten was sleeping in the cushions", "the kitten blinked and made everyone laugh"),
    "coin": Surprise("coin", "coin", "a shiny old coin rolled out from under the stuffing", "the coin turned the repair into a treasure hunt"),
    "puppet": Surprise("puppet", "puppet", "a little sock puppet popped up from a torn seam", "the puppet became the new helper"),
}

CHILD_NAMES = ["Mabel", "Milo", "Ruby", "Otis", "Nell", "Eli", "June", "Ivy"]
ELDER_NAMES = ["Gran", "Grandpa", "Aunt Rose", "Uncle Joe", "Mrs. Bell"]

CURATED = [
    StoryParams("parlor", "sofa", "needle", "kitten", "Mabel", "girl", "Gran", "woman"),
    StoryParams("porch", "chair", "tacker", "coin", "Milo", "boy", "Grandpa", "man"),
    StoryParams("attic", "bench", "glue", "puppet", "Ruby", "girl", "Aunt Rose", "woman"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in UPHOLSTERY:
            for t in TOOLS:
                for su in SURPRISES:
                    combos.append((s, i, t, su))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    item = UPHOLSTERY[params.item]
    tool = TOOLS[params.tool]
    surprise = SURPRISES[params.surprise]
    if item.can_tighten is False:
        raise StoryError("That upholstery item cannot be tightened in this story.")
    if tool.risky and item.id == "bench":
        raise StoryError("The noisy tacker would not fit the gentle bench repair in this world.")
    if surprise.id == "coin" and tool.id == "glue":
        raise StoryError("A coin surprise with glue makes a weak story here; pick a tool that can turn the repair into a discovery.")
    if params.setting == "attic" and tool.id == "needle":
        raise StoryError("The attic is too hot and dusty for that careful repair choice in this world.")


@dataclass
class Rule:
    name: str
    apply: callable

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


def _r_tighten(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.role != "item":
            continue
        if e.meters.get("loose", 0.0) < THRESHOLD:
            continue
        sig = ("tighten", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["fixed"] = 1.0
        out.append("__tightened__")
    return out


def _r_surprise(world: World) -> list[str]:
    out = []
    if world.facts.get("repaired") and not world.facts.get("surprise_seen"):
        world.facts["surprise_seen"] = True
        out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("tighten", _r_tighten), Rule("surprise", _r_surprise)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    collected: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            parts = rule.apply(world)
            if parts:
                changed = True
                collected.extend(p for p in parts if not p.startswith("__"))
    if narrate:
        for s in collected:
            world.say(s)


def tell(setting: Setting, item: UpholsteryItem, tool: Tool, surprise: Surprise,
         child: str, child_gender: str, elder: str, elder_gender: str) -> World:
    world = World(setting)
    child_ent = world.add(Entity(child, "character", child_gender, role="child"))
    elder_ent = world.add(Entity(elder, "character", elder_gender, role="elder"))
    item_ent = world.add(Entity(item.id, "thing", "furniture", label=item.label, role="item"))
    item_ent.meters["loose"] = 1.0
    child_ent.memes["wonder"] = 1.0
    elder_ent.memes["care"] = 1.0

    world.say(f"In {setting.place}, the {setting.room} was as old as a tree stump and twice as creaky.")
    world.say(f"{child_ent.id} ran a hand over the {item.phrase}. 'This old {item.label} is wobblier than a wagon in a thunderstorm,' {child_ent.pronoun()} said.")
    world.say(f"{elder_ent.id} laughed. 'Then let's mend it proper,' {elder_ent.pronoun()} said, lifting {tool.label} with a grin.")
    world.para()

    world.say(f"{tool.sound}! {tool.sound}! The repair began with a song of busy hands and brave hearts.")
    if tool.risky:
        world.say(f"'{tool.label_word if hasattr(tool, 'label_word') else tool.label}' went {tool.sound.lower()}, and the cloth held its breath.")
    world.say(f"The {item.label} sagged once, then started to stand straighter as the stitches went in.")
    item_ent.meters["loose"] = 0.0
    item_ent.meters["fixed"] = 1.0
    world.facts["repaired"] = True
    propagate(world, narrate=False)
    world.para()

    world.say(f"Then came the surprise: {surprise.reveal}.")
    world.say(f"'{surprise.label}!' {child_ent.id} cried. '{surprise.outcome.capitalize()}!'")
    world.say(f"They both chuckled, and the {item.label} looked proud enough to sit up and tell its own tale.")
    world.facts.update(
        child=child_ent,
        elder=elder_ent,
        item=item,
        tool=tool,
        surprise=surprise,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale style story that includes the word "upholstery" and a surprise in the old {f["item"].label}.',
        f"Tell a child-facing story where {f['child'].id} and {f['elder'].id} fix the {f['item'].label} with noisy dialogue and sound effects.",
        f"Write a funny, grand story about upholstery, with a repair that turns into an unexpected discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    item = f["item"]
    surprise = f["surprise"]
    tool = f["tool"]
    return [
        QAItem(
            question="Who was trying to fix the furniture?",
            answer=f"{child.id} and {elder.id} were fixing the {item.label} together. {elder.id} helped with the tools, and {child.id} watched the work with wide eyes."
        ),
        QAItem(
            question="What sound effects happened during the repair?",
            answer=f"The story made room for {tool.sound} sounds while the repair went on. Those sound effects show that the work was lively and busy, not quiet."
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"{surprise.reveal.capitalize()}. That surprise changed the repair from a simple fix into a funny little discovery."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item = f["item"]
    tool = f["tool"]
    return [
        QAItem(
            question="What is upholstery?",
            answer="Upholstery is the cloth or padding that covers furniture like chairs and sofas. It makes the furniture soft, comfy, and nice to sit on."
        ),
        QAItem(
            question=f"What does {tool.label} do in a repair?",
            answer=f"{tool.label.capitalize()} helps put the furniture back together in a careful way. In this story, it made the repair noisy and lively."
        ),
        QAItem(
            question=f"Why would someone mend a {item.label}?",
            answer=f"Someone would mend a {item.label} when the cloth or stuffing gets loose or torn. Fixing it helps the furniture stay strong enough to use again."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:12} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, T, Su) :- setting(S), item(I), tool(T), surprise(Su).
repaired(I) :- valid(S, I, T, Su).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in UPHOLSTERY:
        lines.append(asp.fact("item", i))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for su in SURPRISES:
        lines.append(asp.fact("surprise", su))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    rc = 0
    if python_set != asp_set:
        rc = 1
        print("MISMATCH: ASP and Python valid-combo sets differ.")
        if asp_set - python_set:
            print("  only in ASP:", sorted(asp_set - python_set))
        if python_set - asp_set:
            print("  only in Python:", sorted(python_set - asp_set))
    else:
        print(f"OK: ASP and Python agree on {len(python_set)} valid combos.")

    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale upholstery story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=UPHOLSTERY)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDER_NAMES)
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    item = args.item or rng.choice(list(UPHOLSTERY))
    tool = args.tool or rng.choice(list(TOOLS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    params = StoryParams(
        setting=setting,
        item=item,
        tool=tool,
        surprise=surprise,
        child=args.child or rng.choice(CHILD_NAMES),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        elder=args.elder or rng.choice(ELDER_NAMES),
        elder_gender=args.elder_gender or rng.choice(["woman", "man"]),
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        UPHOLSTERY[params.item],
        TOOLS[params.tool],
        SURPRISES[params.surprise],
        params.child,
        params.child_gender,
        params.elder,
        params.elder_gender,
    )
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
