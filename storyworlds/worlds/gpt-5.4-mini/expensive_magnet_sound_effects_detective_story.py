#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/expensive_magnet_sound_effects_detective_story.py
=================================================================================

A standalone storyworld for a tiny detective tale built from the seed words
"expensive" and "magnet" with sound effects.

Domain:
- A young detective investigates a missing expensive magnet.
- The case involves a clinking / buzzing / click sound trail.
- A calm helper or parent explains the clue chain.
- The ending proves the magnet was found and the detective learns to keep it
  away from metal scraps and pockets.

The world is deliberately small:
- one detective child
- one helper adult
- one valuable magnet
- one nearby metal place where the magnet can stick
- one sound clue
- one resolution path

The simulation tracks:
- physical meters: attraction, noise, stuckness, search_progress, relief
- emotional memes: curiosity, worry, pride, gratitude, confidence

Contract shape:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify,
  --show-asp
- includes Python gate + inline ASP twin
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"attraction": 0.0, "noise": 0.0, "stuck": 0.0, "search": 0.0, "relief": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "pride": 0.0, "gratitude": 0.0, "confidence": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str
    dark_spot: str
    afford_sound: bool = True

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
class Magnet:
    id: str
    label: str
    phrase: str
    expensive: bool = True
    strong: bool = True

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
class Clue:
    id: str
    sound: str
    source: str
    trail: str
    effect: str

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
class Resolution:
    id: str
    action: str
    success_line: str
    fail_line: str
    lesson: str

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
        self.facts: dict[str, object] = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.meters["search"] >= THRESHOLD and "case" not in world.fired:
        world.fired.add(("noise",))
        detective.memes["curiosity"] += 1
        detective.meters["noise"] += 1
        out.append("__noise__")
    return out


def _r_find(world: World) -> list[str]:
    out: list[str] = []
    magnet = world.get("magnet")
    shelf = world.get("shelf")
    if magnet.meters["stuck"] >= THRESHOLD and ("found",) not in world.fired:
        world.fired.add(("found",))
        shelf.meters["clue"] += 1
        out.append("__found__")
    return out


RULES = [Rule("noise", _r_noise), Rule("find", _r_find)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def investigate(world: World, detective: Entity, clue: Clue, magnet: Magnet, setting: Setting) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} was a little detective who loved tidy clues. "
        f"At {setting.place}, {detective.pronoun()} found a note, a shoeprint, and an empty box."
    )
    world.say(
        f'Then came the sound: "{clue.sound}" from {clue.source}. '
        f"{detective.id} tilted {detective.pronoun('possessive')} head and listened."
    )
    world.say(
        f'"The magnet was very {magnet.label}, so it would not stay lost for long," '
        f'{detective.id} said. "But it could be stuck somewhere metal."'
    )


def worry_and_search(world: World, detective: Entity, helper: Entity, magnet: Magnet, clue: Clue) -> None:
    detective.memes["worry"] += 1
    detective.meters["search"] += 1
    world.say(
        f"{detective.id} peered under a chair, then under a box, and heard "
        f'"{clue.sound}!" again.'
    )
    world.say(
        f"{helper.id} came over and smiled. {helper.pronoun().capitalize()} said "
        f'"Follow the sound, and look for anything that can stick."'
    )


def discover(world: World, detective: Entity, magnet: Magnet, setting: Setting, clue: Clue) -> None:
    magnet_ent = world.get("magnet")
    magnet_ent.meters["stuck"] += 1
    detective.meters["search"] += 1
    detective.memes["pride"] += 1
    world.say(
        f"Behind the filing cabinet, {detective.id} saw a glint and heard "
        f'"{clue.sound}" one more time.'
    )
    world.say(
        f"The {magnet.label} had clung to a bent paper tray with a sharp click."
    )


def resolve(world: World, helper: Entity, detective: Entity, magnet: Magnet, res: Resolution) -> None:
    magnet_ent = world.get("magnet")
    magnet_ent.meters["stuck"] = 0.0
    world.get("shelf").meters["relief"] += 1
    detective.meters["relief"] += 1
    detective.memes["confidence"] += 1
    helper.memes["gratitude"] += 1
    world.say(
        f"{helper.id} gently lifted the tray, and with a soft {res.action}, the magnet came free."
    )
    world.say(res.success_line)
    world.say(
        f"{detective.id} grinned. The case was solved, and the expensive magnet was safe again."
    )
    world.say(res.lesson)


def tell(setting: Setting, magnet: Magnet, clue: Clue, res: Resolution,
         detective_name: str = "Milo", detective_gender: str = "boy",
         helper_name: str = "Aunt June", helper_gender: str = "woman") -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name, kind="character", type=detective_gender, role="detective",
        traits=["curious", "careful"],
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_gender, role="helper",
        traits=["calm", "kind"],
    ))
    world.add(Entity(id="shelf", kind="thing", type="place", label="the shelf"))
    world.add(Entity(id="magnet", kind="thing", type="object", label=magnet.label))
    world.add(Entity(id="cabinet", kind="thing", type="object", label="the filing cabinet"))

    detective.meters["search"] = 0.0
    detective.memes["curiosity"] = 1.0

    world.say(
        f"At {setting.place}, {detective.id} opened the case of the missing {magnet.label}."
    )
    world.say(
        f"It was not an ordinary magnet. It was {magnet.phrase}, and the whole room "
        f"felt quieter because it was gone."
    )
    world.para()
    investigate(world, detective, clue, magnet, setting)
    worry_and_search(world, detective, helper, magnet, clue)
    world.para()
    discover(world, detective, magnet, setting, clue)
    resolve(world, helper, detective, magnet, res)

    world.facts.update(
        setting=setting,
        magnet=magnet,
        clue=clue,
        resolution=res,
        detective=detective,
        helper=helper,
        found=True,
    )
    return world


SETTINGS = {
    "office": Setting("office", "the old office", "the filing cabinet", True),
    "museum": Setting("museum", "the tiny museum room", "the display shelf", True),
    "attic": Setting("attic", "the dusty attic", "the metal trunk", True),
}

MAGNETS = {
    "horseshoe": Magnet("horseshoe", "horseshoe magnet", "an expensive horseshoe magnet"),
    "disc": Magnet("disc", "disc magnet", "a very expensive disc magnet"),
}

CLUES = {
    "clink": Clue("clink", "clink-clink", "the shelf", "a trail of tiny metal clips", "attracted"),
    "bzz": Clue("bzz", "bzzzt", "the lamp cord", "a humming wire and a metal tray", "buzzed"),
}

RESOLUTIONS = {
    "lift": Resolution(
        "lift",
        "lift",
        "with a careful lift",
        "tried to yank it free, but it did not budge",
        "Magnets are strong, but they can still stick where they should not. It is smarter to use a gentle hand and listen for clues.",
    ),
    "slide": Resolution(
        "slide",
        "slide",
        "with a slow slide",
        "pulled too hard and only made a noisy scrape",
        "A good detective does not rush. Listening to little sounds can lead you to the right place.",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Penny", "Ivy"]
BOY_NAMES = ["Milo", "Theo", "Evan", "Rory", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, c) for s in SETTINGS for m in MAGNETS for c in CLUES]


@dataclass
@dataclass
class StoryParams:
    setting: str
    magnet: str
    clue: str
    resolution: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
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
    ap = argparse.ArgumentParser(description="Detective storyworld with sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magnet", choices=MAGNETS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--helper-gender", choices=["man", "woman"])
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
    if args.resolution and args.resolution not in RESOLUTIONS:
        raise StoryError("Unknown resolution.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    magnet = args.magnet or rng.choice(sorted(MAGNETS))
    clue = args.clue or rng.choice(sorted(CLUES))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    if magnet not in MAGNETS:
        raise StoryError("Unknown magnet.")
    detective_gender = args.gender or rng.choice(["boy", "girl"])
    detective_name = args.name or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper_name = args.helper or rng.choice(["Aunt June", "Uncle Sam", "Ms. Kim", "Mr. Cole"])
    return StoryParams(setting, magnet, clue, resolution, detective_name, detective_gender, helper_name, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mag: Magnet = f["magnet"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the word "{mag.label}" and a sound like "{clue.sound}".',
        f"Tell a short mystery where {f['detective'].id} searches for a very expensive magnet and follows a sound clue.",
        f"Write a child-friendly detective tale where a missing magnet is found by listening carefully for a clue sound.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    magnet: Magnet = f["magnet"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    res: Resolution = f["resolution"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What was the case about?",
            answer=f"It was about a missing {magnet.label}. {detective.id} had to find the expensive magnet by following clues and listening carefully.",
        ),
        QAItem(
            question="What sound helped solve the mystery?",
            answer=f'The sound "{clue.sound}" helped. It came from {clue.source}, and that sound led {detective.id} toward the magnet.',
        ),
        QAItem(
            question=f"What did {helper.id} do to help?",
            answer=f"{helper.id} stayed calm and told {detective.id} to follow the sound and look for something metal. That advice helped the detective find the stuck magnet.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The magnet was lifted free, the case was solved, and everyone felt relieved. The expensive magnet was safe again at the end.",
        ),
        QAItem(
            question="Why was the magnet tricky to find?",
            answer=f"It had stuck to a metal tray, so it blended in with the room instead of sitting on the table. The little sound clue pointed to the right spot.",
        ),
        QAItem(
            question="What lesson did the detective learn?",
            answer=res.lesson,
        ),
    ]


WORLD_QA = {
    "magnet": [
        QAItem("What does a magnet do?", "A magnet pulls on some kinds of metal and can make them stick together."),
        QAItem("Why can a magnet be expensive?", "Some magnets are made very strong or special, so they cost more money."),
    ],
    "sound": [
        QAItem("What is a sound clue?", "A sound clue is a noise that helps you notice where something might be."),
        QAItem("Why do detectives listen carefully?", "They listen because small sounds can point them toward the answer."),
    ],
    "metal": [
        QAItem("Why do magnets like metal?", "Magnets are attracted to some metal objects, so they can stick to them."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_QA["magnet"] + WORLD_QA["sound"] + WORLD_QA["metal"]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:10} ({e.type:8}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MAGNETS[params.magnet],
        CLUES[params.clue],
        RESOLUTIONS[params.resolution],
        params.detective_name,
        params.detective_gender,
        params.helper_name,
        params.helper_gender,
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


ASP_RULES = r"""
stuck(M) :- magnet(M), expensive(M).
noisy(C) :- clue(C).
solved :- stuck(M), clue(C), noisy(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MAGNETS:
        lines.append(asp.fact("magnet", mid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    # smoke test: generate a default story
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, magnet=None, clue=None, resolution=None, name=None,
            helper=None, gender=None, helper_gender=None, seed=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    # parity
    model = asp.one_model(asp_program("", "#show solved/0."))
    solved = bool(asp.atoms(model, "solved"))
    if not solved:
        print("MISMATCH: ASP did not derive solved.")
        return 1
    print("OK: verify passed.")
    return 0


CURATED = [
    StoryParams("office", "horseshoe", "clink", "lift", "Milo", "boy", "Aunt June", "woman"),
    StoryParams("museum", "disc", "bzz", "slide", "Nora", "girl", "Mr. Cole", "man"),
]


def build_story_text(world: World) -> str:
    return world.render()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("", "#show solved/0."))
        model = asp.one_model(asp_program("", "#show solved/0."))
        print("solved:", bool(asp.atoms(model, "solved")))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
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
