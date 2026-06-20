#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cola_wolf_reconciliation_space_adventure.py
============================================================================

A standalone story world for a tiny space-adventure reconciliation tale:
two young space explorers argue over a cola, a wolf-like companion causes
trouble or worry, and the crew ends by making peace and sharing the ship
safely.

The world keeps state in typed entities with physical meters and emotional
memes. The prose is driven by simulation: a lost cola, a snapped promise,
a misunderstanding with a wolf, a calm apology, and a repaired friendship.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/cola_wolf_reconciliation_space_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/cola_wolf_reconciliation_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/cola_wolf_reconciliation_space_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/cola_wolf_reconciliation_space_adventure.py --verify
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "wolf":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    scene: str
    ship: str
    dark_place: str
    destination: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Cola:
    id: str
    label: str
    phrase: str
    fizzy: str = "sparkled in the cup"
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class WolfCompanion:
    id: str
    label: str
    phrase: str
    tone: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class ReconcileTool:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        c = World(self.setting)
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
            value = defaultdict(float)
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


def _r_spill(world: World) -> list[str]:
    out = []
    cup = world.entities.get("cola")
    if not cup or cup.meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("pilot", "navigator", "wolf"):
        if eid in world.entities:
            world.get(eid).memes["upset"] += 1
    out.append("__spill__")
    return out


def _r_reconcile(world: World) -> list[str]:
    for eid in ("pilot", "navigator", "wolf"):
        if eid not in world.entities:
            continue
        ent = world.get(eid)
        if ent.memes["apology"] < THRESHOLD or ent.memes["forgive"] < THRESHOLD:
            continue
        sig = ("reconcile", eid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["peace"] += 1
        world.get("crew").meters["harmony"] += 1
        return ["__reconcile__"]
    return []


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("reconcile", "social", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def reasonableness_gate(cola: Cola, wolf: WolfCompanion, setting: Setting) -> bool:
    return bool(cola and wolf and setting)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, w) for s in SETTINGS for c in COLAS for w in WOLVES]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in COLAS:
        lines.append(asp.fact("cola", cid))
    for wid in WOLVES:
        lines.append(asp.fact("wolf", wid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, W) :- setting(S), cola(C), wolf(W).
"""


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def setup(world: World, setting: Setting, cola: Cola, wolf: WolfCompanion) -> None:
    pilot = world.add(Entity("pilot", kind="character", type="girl", label="Captain Mira", role="pilot"))
    navigator = world.add(Entity("navigator", kind="character", type="boy", label="Jules", role="navigator"))
    wolf_ent = world.add(Entity("wolf", kind="character", type="wolf", label=wolf.label, role="companion"))
    crew = world.add(Entity("crew", type="crew", label="the crew"))
    bottle = world.add(Entity("cola", type="drink", label=cola.label))
    world.facts.update(pilot=pilot, navigator=navigator, wolf=wolf_ent, crew=crew, cola=bottle, setting=setting, cola_cfg=cola, wolf_cfg=wolf)


def tell(setting: Setting, cola: Cola, wolf: WolfCompanion, tool: ReconcileTool) -> World:
    world = World(setting)
    setup(world, setting, cola, wolf)
    pilot = world.get("pilot")
    navigator = world.get("navigator")
    wolf_ent = world.get("wolf")
    bottle = world.get("cola")
    crew = world.get("crew")

    pilot.memes["curiosity"] += 1
    navigator.memes["curiosity"] += 1
    wolf_ent.memes["watchful"] += 1
    world.say(
        f"Deep in {setting.scene}, {pilot.label_word} and {navigator.label_word} drifted through {setting.ship}. "
        f"The little ship smelled like metal, starlight, and {cola.label}."
    )
    world.say(
        f'"We found the last {cola.label}!" {navigator.label_word} said, holding {cola.phrase}. '
        f'{cola.phrase.capitalize()} {cola.fizzy}.'
    )

    world.para()
    pilot.memes["want"] += 1
    navigator.memes["want"] += 1
    world.say(
        f"But then both children reached for it at once. {pilot.label_word} wanted to keep it for the night watch, "
        f'and {navigator.label_word} wanted a sip right away.'
    )
    world.say(
        f"Nearby, the wolf padded closer with {wolf.tone}, ears high and nose twitching at the sweet smell."
    )

    spill_now = True
    world.para()
    if spill_now:
        bottle.meters["spilled"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{navigator.label_word} bumped the cup, and the {cola.label} splashed across the deck."
        )
        world.say(
            f"The dark floor turned sticky, and the wolf gave a startled yip as the shiny trail slid toward {setting.dark_place}."
        )

    world.para()
    pilot.memes["apology"] += 1
    navigator.memes["apology"] += 1
    wolf_ent.memes["forgive"] += 1
    world.say(
        f"Captain Mira took a breath and said, \"I'm sorry. I was being too grabby.\" "
        f"Jules nodded and added, \"I can share after the stars-on shift.\""
    )
    world.say(
        f"The wolf nosed the cup gently, then backed away like {wolf.tone}."
    )

    world.para()
    tool_line = tool.phrase
    world.get("crew").meters["harmony"] += 1
    pilot.memes["peace"] += 1
    navigator.memes["peace"] += 1
    wolf_ent.memes["peace"] += 1
    world.say(
        f"Together they used {tool_line}, wiped the deck clean, and set the {cola.label} in a safe cradle by the window."
    )
    world.say(
        f'"Let the cola be the moon treat for later," {pilot.label_word} said. '
        f'"For now, let us fly."'
    )
    world.say(
        f"{setting.ending_image} The crew floated on, friends again, with the wolf trotting calmly beside them."
    )

    world.facts.update(outcome="reconciled", spilled=bottle.meters["spilled"] >= THRESHOLD, tool=tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting, cola, wolf = f["setting"], f["cola_cfg"], f["wolf_cfg"]
    return [
        f'Write a space-adventure story for a 3-to-5-year-old that includes the words "{cola.label}" and "{wolf.label}".',
        f"Tell a gentle story where two children on {setting.ship} argue over {cola.phrase}, then make up and keep exploring.",
        f"Write a reconciliation story in space with a wolf companion, a spilled {cola.label}, and a calm ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    setting, cola, wolf = f["setting"], f["cola_cfg"], f["wolf_cfg"]
    pilot, navigator = f["pilot"], f["navigator"]
    qa = [
        ("Who are the main characters?",
         f"It is about {pilot.label_word}, {navigator.label_word}, and the wolf aboard {setting.ship}. They are the little crew at the center of the adventure."),
        ("What caused the argument?",
         f"They argued because both children wanted the last {cola.label} at the same time. That small mistake made the mood turn sticky and tense."),
        ("How did they make up?",
         f"They apologized, cleaned the spill together, and chose to save the {cola.label} for later. The wolf accepted the peace and stayed close without causing more trouble."),
        ("How did the story end?",
         f"It ended with the crew calm again, flying on through space. The ending image shows that the friendship changed from upset to peaceful."),
    ]
    if f.get("spilled"):
        qa.append((
            f"What happened to the {cola.label}?",
            f"It spilled across the deck after they both reached for it. The spill made the ship messy, which is why they had to stop and clean up."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["cola_cfg"].tags) | set(f["wolf_cfg"].tags)
    tags.add("reconciliation")
    out = []
    if "cola" in tags:
        out.append(("What is cola?",
                     "Cola is a fizzy drink. It sparkles and tastes sweet, so people often drink it as a treat."))
    if "wolf" in tags:
        out.append(("What is a wolf?",
                     "A wolf is a wild animal that looks a bit like a big dog. Wolves have sharp ears, strong legs, and a loud howl."))
    out.append(("What does reconciliation mean?",
                 "Reconciliation means making peace after a disagreement. People apologize, listen, and start being kind again."))
    out.append(("Why do spaceships need to stay tidy?",
                 "A tidy spaceship is safer and easier to use. Spills can make the floor slippery and make it harder to move around."))
    return out


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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


SETTINGS = {
    "orbit": Setting("orbit", "the glowing orbit lane", "the starship", "the cargo corner", "Moonport", "The ship drifted on under a bright blue planet."),
    "moonbase": Setting("moonbase", "the moonbase hall", "the little base", "the shadow tunnel", "Moonport", "The base windows shone while the crew smiled again."),
    "cometdeck": Setting("cometdeck", "the comet deck", "the scout ship", "the dark hatchway", "Star Harbor", "The ship swung toward the next star with a gentler crew."),
}

COLAS = {
    "cola": Cola("cola", "cola", "a cold cola"),
    "sparkcola": Cola("sparkcola", "sparkling cola", "a fizzy sparkling cola"),
    "spacecola": Cola("spacecola", "space cola", "a tiny can of space cola"),
}

WOLVES = {
    "wolf": WolfCompanion("wolf", "wolf", "the wolf", "soft and careful"),
    "moonwolf": WolfCompanion("moonwolf", "moon wolf", "the moon wolf", "quiet and watchful"),
    "starwolf": WolfCompanion("starwolf", "star wolf", "the star wolf", "gentle and bright"),
}

TOOLS = {
    "towel": ReconcileTool("towel", "towel", "a soft towel", "wiped the spill away"),
    "mop": ReconcileTool("mop", "mop", "a small mop", "mopped the sticky deck"),
    "cloth": ReconcileTool("cloth", "cloth", "a clean cloth", "made the deck shine again"),
}

GIRL_NAMES = ["Mira", "Luna", "Ivy", "Nia", "Zara", "Nova"]
BOY_NAMES = ["Jules", "Tobin", "Ezra", "Kai", "Leo", "Finn"]
TRAITS = ["brave", "curious", "gentle", "thoughtful"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    cola: str
    wolf: str
    tool: str
    pilot_name: str
    navigator_name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    StoryParams("orbit", "cola", "wolf", "towel", "Mira", "Jules"),
    StoryParams("moonbase", "sparkcola", "moonwolf", "mop", "Luna", "Kai"),
    StoryParams("cometdeck", "spacecola", "starwolf", "cloth", "Nia", "Finn"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure reconciliation story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cola", choices=COLAS)
    ap.add_argument("--wolf", choices=WOLVES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
    if not combos:
        raise StoryError("No valid space-adventure combos.")
    s, c, w = rng.choice(combos)
    tool = args.tool or rng.choice(sorted(TOOLS))
    return StoryParams(
        setting=args.setting or s,
        cola=args.cola or c,
        wolf=args.wolf or w,
        tool=tool,
        pilot_name=args.name1 or rng.choice(GIRL_NAMES),
        navigator_name=args.name2 or rng.choice(BOY_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], COLAS[params.cola], WOLVES[params.wolf], TOOLS[params.tool])
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


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP matches valid_combos() ({len(python_set)} combos).")
    else:
        print("MISMATCH in ASP parity.")
        if python_set - clingo_set:
            print(" only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print(" only in clingo:", sorted(clingo_set - python_set))
        return 1
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: normal generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid space-adventure combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.setting}: {p.cola} / {p.wolf}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
