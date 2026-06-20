#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whosejigger_impersonate_sound_effects_surprise_adventure.py
=============================================================================================

A tiny adventure storyworld for a child's playful expedition with a strange
whosejigger, lots of sound effects, and a surprise reveal. The domain is built
around one concrete premise: a child wants to explore a pretend adventure route,
uses a curious gadget called a whosejigger, tries to impersonate jungle or cave
sounds, and gets a surprise that changes the ending from suspenseful to joyful.

The simulated world tracks:
- physical meters: noise, progress, dust, battery, hiddenness, sparkle
- emotional memes: curiosity, confidence, worry, delight, surprise, bravery

The story is not a frozen paragraph with swapped nouns. It follows state:
setup -> temptation -> noisy problem -> surprise turn -> resolution image.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/whosejigger_impersonate_sound_effects_surprise_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/whosejigger_impersonate_sound_effects_surprise_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/whosejigger_impersonate_sound_effects_surprise_adventure.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOUND_MIN = 2


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
    description: str
    path: str
    clue: str
    adventure: str
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
class Gadget:
    id: str
    label: str
    phrase: str
    sound: str
    purpose: str
    battery: int
    surprise: bool = False
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
class SoundAct:
    id: str
    verb: str
    sound_line: str
    noise: int
    curiosity: int
    bravery: int
    consequence: str
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
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
    hero = world.get("hero")
    gadget = world.get("whosejigger")
    if hero.meters["noise"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    gadget.meters["buzz"] += 1
    out.append("__noise__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    hero = world.get("hero")
    if helper.meters["hidden"] < THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["surprise"] += 1
    helper.memes["joy"] += 1
    out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("noise", "physical", _r_noise), Rule("surprise", "social", _r_surprise)]


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


def valid_combo(setting: Setting, act: SoundAct, gadget: Gadget) -> bool:
    return act.noise >= 1 and gadget.battery >= 1 and setting.id in {"cave", "jungle", "attic"}


def sensible_gadgets() -> list[Gadget]:
    return [g for g in GADGETS.values() if g.battery >= SOUND_MIN]


def predict(world: World, act: SoundAct) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["noise"] += act.noise
    hero.memes["curiosity"] += act.curiosity
    propagate(sim, narrate=False)
    return {"noisy": hero.meters["noise"] >= THRESHOLD, "surprised": sim.get("helper").meters["hidden"] >= THRESHOLD}


def do_act(world: World, hero: Entity, act: SoundAct, gadget: Gadget) -> None:
    hero.meters["noise"] += act.noise
    hero.memes["curiosity"] += act.curiosity
    gadget.meters["used"] += 1
    gadget.meters["battery"] -= 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} pressed the {gadget.label}, and it made {act.sound_line}. "
        f"{act.consequence}"
    )


def setup(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    helper.meters["hidden"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} stepped into {setting.place}. "
        f"{setting.description}"
    )
    world.say(
        f"{hero.id} followed {setting.path} because {setting.clue} led toward "
        f"{setting.adventure}."
    )


def tempt(world: World, hero: Entity, act: SoundAct, gadget: Gadget) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} spotted the {gadget.label} and grinned. "
        f'"I can impersonate the wild sounds!" {hero.id} said.'
    )
    world.say(f"{act.verb.capitalize()}, {act.verb} -- {act.sound_line}.")


def warn(world: World, helper: Entity, hero: Entity, act: SoundAct) -> None:
    pred = predict(world, act)
    if pred["noisy"]:
        hero.memes["worry"] += 1
        world.say(
            f"Somewhere ahead, a voice called, '{hero.id}, keep it soft. "
            f"Sound effects can echo and scare the birds.'"
        )


def surprise_turn(world: World, helper: Entity) -> None:
    helper.meters["hidden"] = 0
    helper.meters["sparkle"] += 1
    helper.memes["delight"] += 1
    world.say(
        f"Then the bushes rustled, and a surprise popped out: {helper.id} "
        f"had been there all along with a lantern and a grin."
    )


def resolve(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    hero.memes["surprise"] += 1
    hero.memes["delight"] += 1
    world.say(
        f"{helper.id} clapped softly and showed a hidden trail marker. "
        f'"You can make adventure sounds, but keep the path gentle," {helper.id} said.'
    )
    world.say(
        f"{hero.id} laughed, tucked the {world.get('whosejigger').label} into "
        f"{hero.pronoun('possessive')} pocket, and walked on with quieter feet."
    )
    world.say(
        f"At the end of the trail, {setting.adventure} looked even bigger, and "
        f"the surprise lantern made the leaves glow like tiny stars."
    )


def tell(setting: Setting, act: SoundAct, gadget: Gadget,
         hero_name: str = "Mina", hero_gender: str = "girl",
         helper_name: str = "Pip", helper_gender: str = "boy",
         parent_name: str = "Aunt June") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother", role="parent", label="Aunt June"))
    wj = world.add(Entity(id="whosejigger", kind="thing", type="tool", label=gadget.label, role="gadget"))
    hero.memes["bravery"] = 4.0
    helper.meters["hidden"] = 1.0
    world.facts.update(setting=setting, act=act, gadget=gadget, hero=hero, helper=helper, parent=parent)
    setup(world, hero, helper, setting)
    world.para()
    tempt(world, hero, act, gadget)
    warn(world, helper, hero, act)
    do_act(world, hero, act, gadget)
    world.para()
    surprise_turn(world, helper)
    resolve(world, hero, helper, setting)
    world.facts["outcome"] = "surprise"
    world.facts["gadget"] = wj
    return world


SETTINGS = {
    "cave": Setting("cave", "the echo cave", "The tunnel walls were damp and shiny, and every drip sounded like a drum.", "a winding path", "a carved arrow", "the treasure hall", {"echo", "adventure"}),
    "jungle": Setting("jungle", "the green jungle", "The vines hung thick, and the path smelled like rain and warm leaves.", "a narrow trail", "a painted stone", "the old lookout", {"birds", "adventure"}),
    "attic": Setting("attic", "the dusty attic", "The rafters creaked, and sunbeams made little gold squares on the floor.", "a tiny ladder", "a chalk star", "the blanket fort", {"dust", "adventure"}),
}

GADGETS = {
    "whistlebox": Gadget("whistlebox", "whosejigger", "a funny whistle and a hollow boom", "whoo-OO-ooo", "help with signal sounds", 2, surprise=False, tags={"sound"}),
    "clangcap": Gadget("clangcap", "whosejigger", "a clang, a click, and a tiny drumroll", "clang-clang!", "help with brave adventure sounds", 3, surprise=True, tags={"sound", "surprise"}),
    "rattlebell": Gadget("rattlebell", "whosejigger", "a rattle and a bright bell jingle", "jingle-jangle!", "help with trail signals", 2, surprise=True, tags={"sound", "surprise"}),
}

ACTS = {
    "echo": SoundAct("echo", "Impersonate the cave echo", "a long, rolling echo", 1, 1, 1, "The cave answered back with a soft shiver.", {"sound"}),
    "roar": SoundAct("roar", "Impersonate a roaring lion", "a big ROAR!", 2, 2, 1, "The leaves trembled and the birds lifted off at once.", {"sound"}),
    "drum": SoundAct("drum", "Impersonate a marching drummer", "a tum-ta-ta drumbeat", 1, 1, 2, "The path felt like a parade for a moment.", {"sound"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    act: str
    gadget: str
    hero: str
    hero_gender: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS.values():
        for a in ACTS.values():
            for g in GADGETS.values():
                if valid_combo(s, a, g):
                    out.append((s.id, a.id, g.id))
    return out


KNOWLEDGE = {
    "sound": [
        ("What is a sound effect?", "A sound effect is a made-up or acted-out sound that helps a story feel lively. In an adventure, sound effects can make footsteps, echoes, or animal noises feel real."),
        ("Why do echoes happen?", "An echo happens when sound bounces off a wall or cliff and comes back to your ears. Caves often have echoes because their walls are hard and close by."),
    ],
    "surprise": [
        ("What is a surprise?", "A surprise is something unexpected that suddenly appears or happens. A good surprise can make a person gasp, laugh, or smile really big."),
        ("Why can a surprise make a story exciting?", "A surprise changes what the reader thought would happen. It can turn a quiet scene into an exciting moment very quickly."),
    ],
    "adventure": [
        ("What makes a story feel like an adventure?", "An adventure usually has a path to follow, a goal to find, and a feeling that something exciting is just ahead."),
    ],
    "whosejigger": [
        ("What is a whosejigger?", "A whosejigger is a made-up gadget name for a strange little tool. In this storyworld it is a playful object that makes sounds and helps the adventure feel magical."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the words "{f["gadget"].label}" and "impersonate".',
        f"Tell a short story where {f['hero'].id} uses a whosejigger to impersonate sound effects on a trail, then gets a surprise.",
        f"Write a child-friendly adventure with sound effects, a surprise turn, and a bright ending in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    act = f["act"]
    q = [
        ("Who is the story about?", f"It is about {hero.id}, who goes on a little adventure in {setting.place}. {helper.id} joins the story as the surprise helper."),
        ("What did {0} try to do?".format(hero.id), f"{hero.id} tried to impersonate {act.sound_line} with the whosejigger. The sound made the adventure feel bigger and more exciting."),
        ("What happened after the noisy part?", f"A surprise happened when {helper.id} appeared with a lantern. That changed the story from noisy guessing into a happier, clearer adventure."),
        ("How did the story end?", f"It ended with {hero.id} walking on more quietly, while the trail glowed with a surprise lantern. The ending shows that the adventure became safer and brighter."),
    ]
    return q


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["setting"].tags) | set(world.facts["gadget"].tags) | set(world.facts["act"].tags)
    out: list[tuple[str, str]] = []
    for key in ["whosejigger", "sound", "surprise", "adventure"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cave", "echo", "clangcap", "Mina", "girl", "Pip", "boy"),
    StoryParams("jungle", "roar", "rattlebell", "Toby", "boy", "Mira", "girl"),
    StoryParams("attic", "drum", "whistlebox", "Nia", "girl", "Leo", "boy"),
]


def explain_rejection() -> str:
    return "(No story: this adventure needs a sound-making act and a gadget that can carry the surprise.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTS.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("noise", aid, a.noise))
        lines.append(asp.fact("curiosity", aid, a.curiosity))
        lines.append(asp.fact("bravery", aid, a.bravery))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        lines.append(asp.fact("battery", gid, g.battery))
        if g.surprise:
            lines.append(asp.fact("surprise_gadget", gid))
    lines.append(asp.fact("sound_min", SOUND_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,G) :- setting(S), act(A), gadget(G), noise(A,N), N >= 1, battery(G,B), B >= sound_min(M), M >= 2.
surprise_path(G) :- surprise_gadget(G).
outcome(surprise) :- surprise_path(_).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    import asp
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: whosejigger, impersonate, sound effects, surprise, adventure.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.act is None or c[1] == args.act)
              and (args.gadget is None or c[2] == args.gadget)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, act, gadget = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(["Mina", "Toby", "Nia", "Rex", "Luna"])
    helper = args.helper or rng.choice([n for n in ["Pip", "Mira", "Leo", "June", "Finn"] if n != hero])
    return StoryParams(setting, act, gadget, hero, "girl" if hero in {"Mina", "Nia", "Luna"} else "boy", helper, "girl" if helper in {"Mira", "June"} else "boy")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTS[params.act], GADGETS[params.gadget], params.hero, params.hero_gender, params.helper, params.helper_gender)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
