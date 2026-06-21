#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/salmon_boat_ramp_cautionary_curiosity_kindness_superhero.py
==========================================================================================

A standalone storyworld script for a tiny superhero-style cautionary tale set at
a boat ramp: a curious child wants to help salmon at the water's edge, a
cautionary companion warns about slippery rocks and rushing boats, and a kind
adult super-helps with a safer plan. The world simulates a small domain where
physical meters and emotional memes drive the prose, Q&A, and verification.

The story shape:
- premise: a child spots salmon near a boat ramp and wants to get closer
- tension: curiosity and eagerness pull them toward a risky spot
- turn: caution flags the danger, and kindness offers a safer way to help
- resolution: they protect the salmon without stepping into harm's way

Run it:
    python storyworlds/worlds/gpt-5.4-mini/salmon_boat_ramp_cautionary_curiosity_kindness_superhero.py
    python storyworlds/worlds/gpt-5.4-mini/salmon_boat_ramp_cautionary_curiosity_kindness_superhero.py --all
    python storyworlds/worlds/gpt-5.4-mini/salmon_boat_ramp_cautionary_curiosity_kindness_superhero.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/salmon_boat_ramp_cautionary_curiosity_kindness_superhero.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
RISK_MIN = 1.0
CautionTraits = {"cautionary", "careful", "watchful", "steady"}
KindTraits = {"kindness", "kind", "gentle", "helpful"}
CuriousTraits = {"curiosity", "curious", "eager", "wondering"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    shore: str
    hazard: str
    safe_spot: str

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
class CharacterRole:
    id: str
    title: str
    trait: str
    job: str

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
class SalmonEvent:
    id: str
    label: str
    movement: str
    danger: str
    rescue_phrase: str
    tags: set[str] = field(default_factory=set)

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
class SafetyTool:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def hazard_at_risk() -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hero in HEROES:
            for tool in TOOLS:
                combos.append((setting, hero, tool))
    return combos


def reasonableness_gate(hero_role: CharacterRole, tool: SafetyTool) -> bool:
    return "safe" in tool.tags or hero_role.id == "hero"


def tell_warning(world: World, child: Entity, scout: Entity, salmon: SalmonEvent) -> None:
    child.memes["curiosity"] += 1
    scout.memes["caution"] += 1
    world.say(
        f"At the boat ramp, {child.id} spotted the {salmon.label} flashing in the shallows "
        f"and wanted to get closer."
    )
    world.say(
        f'"Look," {child.id} whispered, "the {salmon.label} are like river heroes."'
    )
    world.say(
        f"{scout.id} touched {scout.pronoun('possessive')} chest and said, "
        f'"Maybe, but the stones are slick and the boats can come fast. We should stay back."'
    )


def predict_risk(world: World, salmon: SalmonEvent) -> dict:
    sim = world.copy()
    sim.get("child").meters["edge"] += 1
    sim.get("child").meters["slip"] += 1
    return {"slip": sim.get("child").meters["slip"] >= THRESHOLD}


def step_toward_edge(world: World, child: Entity) -> None:
    child.meters["edge"] += 1
    child.memes["bold"] += 1


def slip_alarm(world: World, child: Entity, salmon: SalmonEvent) -> None:
    child.meters["risk"] += 1
    world.say(
        f"{child.id} edged too close, and the wet ramp stones glittered under {child.pronoun('possessive')} shoes."
    )
    world.say(
        f"Just then, a wave splashed the ramp, and the salmon swam in a quick silver rush."
    )


def kind_rescue(world: World, adult: Entity, tool: SafetyTool, salmon: SalmonEvent) -> None:
    adult.memes["kindness"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came in like a real superhero, not with a cape, but with {tool.phrase}."
    )
    world.say(
        f"{adult.pronoun().capitalize()} used it to make a safer place to watch the fish: {tool.use}."
    )


def make_safety_plan(world: World, child: Entity, scout: Entity, adult: Entity, tool: SafetyTool, salmon: SalmonEvent) -> None:
    child.memes["relief"] += 1
    scout.memes["relief"] += 1
    world.say(
        f"Then {adult.label_word} showed them the safe spot by the railing, where they could watch without slipping."
    )
    world.say(
        f"{child.id} and {scout.id} waved to the salmon, and the silver fish kept gliding toward deeper water."
    )
    world.say(
        f"This time, the ramp stayed dry enough, the salmon stayed safe, and the little team felt like a superhero crew."
    )


def tell(setting: Setting, hero_role: CharacterRole, scout_role: CharacterRole,
         salmon: SalmonEvent, tool: SafetyTool, child_name: str = "Maya",
         scout_name: str = "Finn", adult_name: str = "Ava") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl", role="hero",
                             traits=[hero_role.trait]))
    scout = world.add(Entity(id=scout_name, kind="character", type="boy", role="scout",
                             traits=[scout_role.trait]))
    adult = world.add(Entity(id=adult_name, kind="character", type="woman", role="adult",
                             label="the grown-up", traits=["kind", "steady"]))

    world.say(
        f"On a bright day at the {setting.place}, {child.id} and {scout.id} stood near the water and watched for {salmon.label}."
    )
    world.say(
        f"The boat ramp led down to the shore, and the {salmon.label} flashed like tiny superhero shields in the water."
    )

    world.para()
    tell_warning(world, child, scout, salmon)
    if predict_risk(world, salmon)["slip"]:
        step_toward_edge(world, child)
        world.say(
            f'{child.id} wanted to help the fish up close, because {child.pronoun("subject")} was full of curiosity.'
        )
        world.say(
            f'But {scout.id} kept {scout.pronoun("possessive")} feet planted and reminded {child.pronoun("object")} that caution can be kind.'
        )

    world.para()
    slip_alarm(world, child, salmon)
    kind_rescue(world, adult, tool, salmon)
    make_safety_plan(world, child, scout, adult, tool, salmon)

    world.facts.update(
        child=child,
        scout=scout,
        adult=adult,
        setting=setting,
        salmon=salmon,
        tool=tool,
        outcome="safe",
        touched_edge=child.meters["edge"] >= THRESHOLD,
    )
    return world


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


SETTINGS = {
    "boat_ramp": Setting("boat_ramp", "boat ramp", "shore", "slippery stones", "railing"),
}

HEROES = {
    "curiosity": CharacterRole("curiosity", "Curiosity", "curious", "wants to get closer"),
    "cautionary": CharacterRole("cautionary", "Cautionary", "careful", "warns about danger"),
    "kindness": CharacterRole("kindness", "Kindness", "kind", "helps in a gentle way"),
}

TOOLS = {
    "binoculars": SafetyTool("binoculars", "binoculars", "the binoculars", "watch from the safe railing", tags={"safe", "watch"}),
    "net": SafetyTool("net", "a wide fish net", "a wide fish net", "guide water away from the feet", tags={"safe", "help"}),
    "sign": SafetyTool("sign", "a bright sign", "a bright sign", "mark the safe spot and warn walkers", tags={"safe", "warn"}),
}

SALMONS = {
    "salmon": SalmonEvent("salmon", "salmon", "swift silver flashes", "slick water", "guided salmon trail", tags={"salmon", "fish"}),
}

GIRL_NAMES = ["Maya", "Lila", "Nora", "Ava", "Zoe", "Mina"]
BOY_NAMES = ["Finn", "Eli", "Noah", "Theo", "Leo", "Max"]
ADULT_NAMES = ["Ava", "June", "Mira", "Iris"]



@dataclass
class StoryParams:
    setting: str
    primary: str
    caution: str
    kindness: str
    tool: str
    child: str
    scout: str
    adult: str
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

CURATED = [
    StoryParams("boat_ramp", "curiosity", "cautionary", "kindness", "binoculars", "Maya", "Finn", "Ava"),
    StoryParams("boat_ramp", "curiosity", "cautionary", "kindness", "sign", "Lila", "Theo", "June"),
    StoryParams("boat_ramp", "cautionary", "kindness", "curiosity", "net", "Nora", "Max", "Iris"),
]



def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero-style story for a young child set at a {f["setting"].place} that includes the word "salmon".',
        f"Tell a gentle cautionary story where {f['child'].id} is curious about salmon at the boat ramp, {f['scout'].id} warns about danger, and a kind grown-up helps."
        ,
        f"Write a story about curiosity, cautionary advice, and kindness leading to a safer way to watch salmon.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, scout, adult = f["child"], f["scout"], f["adult"]
    salmon = f["salmon"]
    tool = f["tool"]
    return [
        ("Who is the story about?", f"It is about {child.id}, {scout.id}, and {adult.id} at the boat ramp. They work together to keep the {salmon.label} safe."),
        ("Why did the child want to move closer?", f"{child.id} was full of curiosity and wanted a better look at the salmon. That curiosity made the edge of the ramp feel tempting."),
        ("How did the warning help?", f"{scout.id} noticed the slippery stones and warned {child.id} before anyone slipped. The warning mattered because the ramp was a risky place near moving water."),
        ("How did the grown-up help?", f"{adult.id} came with {tool.label} and made a safer place to watch the salmon. That kind help turned the scary moment into a safe plan."),
        ("How did the story end?", f"It ended safely, with everyone watching the salmon from the railing. The fish kept going, and the children felt like a superhero team."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a salmon?", "A salmon is a fish that swims in rivers and the ocean. People often see salmon moving quickly through the water."),
        ("Why can a boat ramp be slippery?", "A boat ramp gets wet from the water, so the stones or concrete can be slick. Wet surfaces can make a person slide if they are not careful."),
        ("What does caution mean?", "Caution means being careful and thinking about danger before you move. A cautionary person helps keep everyone safe."),
        ("What does kindness mean?", "Kindness means helping in a gentle, thoughtful way. A kind helper makes things safer without being mean."),
        ("What does curiosity mean?", "Curiosity is the feeling that makes someone want to look, ask, and learn more. Curiosity can be wonderful when it is guided safely."),
        ("What should you do near slippery water?", "Stay with a grown-up, keep back from the edge, and use the safe viewing spot. Careful choices help prevent slips."),
    ]


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HEROES:
        lines.append(asp.fact("role", hid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("safe", tid))
    lines.append(asp.fact("threshold", THRESHOLD))
    lines.append(asp.fact("risk_min", RISK_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
safe_tool(T) :- tool(T), safe(T).
valid_story(S, H, T) :- setting(S), role(H), safe_tool(T).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python combo sets differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"Story generation failed: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero-style salmon storyworld at a boat ramp.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--primary", choices=HEROES)
    ap.add_argument("--caution", choices=HEROES)
    ap.add_argument("--kindness", choices=HEROES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--scout")
    ap.add_argument("--adult")
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
    setting = args.setting or "boat_ramp"
    primary = args.primary or rng.choice(list(HEROES))
    caution = args.caution or "cautionary"
    kindness = args.kindness or "kindness"
    tool = args.tool or rng.choice(list(TOOLS))
    child = args.child or rng.choice(GIRL_NAMES)
    scout = args.scout or _pick_name(rng, BOY_NAMES, avoid="")
    adult = args.adult or rng.choice(ADULT_NAMES)
    if tool not in TOOLS:
        raise StoryError("Unknown tool.")
    return StoryParams(setting, primary, caution, kindness, tool, child, scout, adult)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HEROES[params.primary], HEROES[params.caution], HEROES[params.kindness], TOOLS[params.tool], params.child, params.scout, params.adult)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
