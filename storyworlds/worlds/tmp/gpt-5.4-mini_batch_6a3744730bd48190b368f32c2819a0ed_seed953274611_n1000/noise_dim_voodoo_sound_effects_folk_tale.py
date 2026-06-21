#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/noise_dim_voodoo_sound_effects_folk_tale.py
=============================================================================

A small, standalone storyworld for a folk-tale-like child story about a noisy
thing, a wise helper, and a magical-but-safe "voodoo" charm that makes the noise
dim down.

Seed words:
- noise-dim
- voodoo

Feature:
- Sound effects

Style:
- Folk tale

The world is intentionally tiny: a child, a helper, a noisy source, and a calm
resolution. The prose is driven by simulated state: noise builds, worry rises,
the helper acts, and the ending image proves the change.

This file follows the shared Storyweavers contract:
- stdlib-only prose engine
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- --verify, --show-asp, --asp, --json, --qa, --trace, --all, -n, --seed
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
NOISE_LIMIT = 2.0
CALM_LIMIT = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class StoryParams:
    village: str
    noise_source: str
    charm: str
    helper_item: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
    elder_type: str
    child_trait: str
    seed: Optional[int] = None


@dataclass
class NoiseSource:
    id: str
    label: str
    sound: str
    place: str
    loudness: int
    can_be_dimmed: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    sound: str
    effect: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperItem:
    id: str
    label: str
    phrase: str
    effect: str
    power: int
    tags: set[str] = field(default_factory=set)


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
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dim_noise(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    source = world.entities.get("noise")
    if not child or not source:
        return out
    if source.meters["noise"] >= NOISE_LIMIT and child.memes["unease"] >= THRESHOLD:
        sig = ("dim",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["hope"] += 1
        out.append("__dim__")
    return out


CAUSAL_RULES = [Rule("dim_noise", "social", _r_dim_noise)]


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


def do_noise(world: World, source: Entity, narrate: bool = True) -> None:
    source.meters["noise"] += 1
    world.get("child").memes["unease"] += 1
    world.get("elder").memes["care"] += 1
    if narrate:
        world.say(f"{source.label_word if hasattr(source, 'label_word') else source.label} went on: {source.attrs.get('sound', 'boom')}.")
    propagate(world, narrate=narrate)


def predict_dim(world: World, source_id: str) -> dict:
    sim = world.copy()
    sim.get(source_id).meters["noise"] += 1
    sim.get("child").memes["unease"] += 1
    propagate(sim, narrate=False)
    return {
        "noise": sim.get(source_id).meters["noise"],
        "unease": sim.get("child").memes["unease"],
        "hope": sim.get("child").memes["hope"],
    }


def setup(world: World, child: Entity, elder: Entity, village: str) -> None:
    child.memes["joy"] += 1
    elder.memes["watchful"] += 1
    world.say(
        f"In {village}, {child.id} and {elder.id} lived by the river where the reeds "
        f"whispered and the evening bells rang soft."
    )


def problem(world: World, child: Entity, noise: NoiseSource) -> None:
    world.get("noise").meters["noise"] += 1
    child.memes["unease"] += 1
    world.say(
        f"But by the gate stood {noise.label}, and every time it stirred it made "
        f"a great {noise.sound} sound."
    )
    world.say(
        f"{child.id} tried to rest, but the noise would not stay small."
    )


def warning(world: World, elder: Entity, child: Entity, noise: NoiseSource) -> None:
    pred = predict_dim(world, "noise")
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_unease"] = pred["unease"]
    world.say(
        f"{elder.id} listened, then said, \"That {noise.label} is too loud for a little one. "
        f"We need to make the noise-dim.\""
    )
    world.say(f"{child.id} nodded, because the clatter made the night feel long.")


def charm_work(world: World, charm: Charm, item: HelperItem, child: Entity, elder: Entity) -> None:
    noise = world.get("noise")
    if item.power + charm.power < noise.meters["noise"]:
        raise StoryError("The chosen charm and helper item are too weak for this noise.")
    noise.meters["noise"] = 0.0
    child.memes["unease"] = 0.0
    child.memes["calm"] += 2
    elder.memes["pride"] += 1
    world.say(
        f'{elder.id} took out {charm.phrase}. {charm.sound} went the little magic, '
        f'and {item.phrase} followed with a quiet {item.effect}.'
    )
    world.say(
        f"Little by little, the noise-dim charm worked. The loudness folded up like a blanket."
    )
    world.say(
        f"{child.id} could hear the river again."
    )


def ending(world: World, child: Entity, elder: Entity, noise: NoiseSource) -> None:
    child.memes["joy"] += 1
    child.memes["calm"] += 1
    elder.memes["calm"] += 1
    world.say(
        f"At last the gate stood still, and {noise.label} was only a sleepy shape in the dusk."
    )
    world.say(
        f"{child.id} smiled at {elder.id}, and the two of them sat by the door while the crickets sang."
    )


NOISE_SOURCES = {
    "drum": NoiseSource(
        id="drum",
        label="the drum by the gate",
        sound="bam-bam",
        place="the gate",
        loudness=2,
        can_be_dimmed=True,
        tags={"drum", "sound"},
    ),
    "rattle": NoiseSource(
        id="rattle",
        label="the rattle on the post",
        sound="clack-clack",
        place="the post",
        loudness=2,
        can_be_dimmed=True,
        tags={"rattle", "sound"},
    ),
    "bell": NoiseSource(
        id="bell",
        label="the iron bell",
        sound="clang-clang",
        place="the tower",
        loudness=3,
        can_be_dimmed=True,
        tags={"bell", "sound"},
    ),
}

CHARMS = {
    "voodoo_doll": Charm(
        id="voodoo_doll",
        label="voodoo doll",
        phrase="a small voodoo doll wrapped in red thread",
        sound="hush-hush",
        effect="shh-shh",
        power=2,
        tags={"voodoo", "magic"},
    ),
    "voodoo_bell": Charm(
        id="voodoo_bell",
        label="voodoo bell",
        phrase="a voodoo bell with a black ribbon",
        sound="ting-ting",
        effect="thin and far away",
        power=3,
        tags={"voodoo", "magic"},
    ),
}

HELPERS = {
    "blanket": HelperItem(
        id="blanket",
        label="blanket",
        phrase="a thick wool blanket",
        effect="thump",
        power=1,
        tags={"blanket"},
    ),
    "feathers": HelperItem(
        id="feathers",
        label="feathers",
        phrase="a bundle of soft feathers",
        effect="fuff",
        power=1,
        tags={"feathers"},
    ),
    "driftwood": HelperItem(
        id="driftwood",
        label="driftwood",
        phrase="a smooth piece of driftwood",
        effect="tap-tap",
        power=2,
        tags={"driftwood"},
    ),
}

VILLAGES = {
    "river": "a river village",
    "hill": "a hill village",
    "forest": "a forest village",
}

GIRL_NAMES = ["Mira", "Nia", "Tala", "Lena", "Suri"]
BOY_NAMES = ["Bram", "Owen", "Jory", "Milo", "Pek"]
ELDER_NAMES = ["Grandma Iva", "Grandpa Rell", "Aunt Siba", "Uncle Tomi"]
TRAITS = ["quiet", "curious", "brave", "gentle", "listening"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for village in VILLAGES:
        for noise_id, noise in NOISE_SOURCES.items():
            if not noise.can_be_dimmed:
                continue
            for charm_id in CHARMS:
                for helper_id in HELPERS:
                    if CHARMS[charm_id].power + HELPERS[helper_id].power >= noise.loudness:
                        out.append((village, noise_id, charm_id + "+" + helper_id))
    return out


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    noise = f["noise_cfg"]
    charm = f["charm"]
    item = f["helper"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {elder.id}, who live in a small village and face a noisy problem together."),
        ("What was making the trouble?",
         f"{noise.label} kept making {noise.sound} sounds, and that noise felt too big for the child to rest beside."),
        ("What did the wise helper do?",
         f"{elder.id} used {charm.phrase} and {item.phrase} to make the noise-dim. The magic and the soft helper work together, so the loudness could settle down."),
        ("How did the story end?",
         f"It ended quietly, with the gate still and the child calm again. The ending image proves the change because the noise was gone and the river could be heard.")
    ]
    if f.get("quieted"):
        qa.append((
            "What changed after the charm worked?",
            f"The noise went down to almost nothing, and {child.id} stopped feeling uneasy. The village became a soft, listening place instead of a clattering one."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["noise_cfg"].tags)
    tags |= set(world.facts["charm"].tags)
    tags |= set(world.facts["helper"].tags)
    out = []
    known = {
        "voodoo": [("What does the word voodoo mean in this story?",
                   "It means a little folk magic tool or charm used by the wise helper. It is part of the tale's magical feeling, not a scary thing.")],
        "sound": [("What is a sound effect?",
                  "A sound effect is a written sound like bam-bam or shh-shh that helps the reader hear the moment in their head.")],
        "drum": [("What does a drum do?",
                 "A drum makes a beat when you tap it, and a fast beat can sound loud in a small place.")],
        "rattle": [("What is a rattle?",
                   "A rattle is a thing that shakes and makes a clacking sound when it moves.")],
        "bell": [("What is a bell?",
                 "A bell makes a ringing sound when it is struck, and the sound can carry far.")],
        "blanket": [("What does a blanket do?",
                    "A blanket covers things up and can make them feel cozy and quieter.")],
        "driftwood": [("What is driftwood?",
                      "Driftwood is wood that has floated in water and been smoothed by waves.")],
        "feathers": [("What are feathers like?",
                     "Feathers are soft and light, so they can help make a thing feel gentle.")],
    }
    order = ["voodoo", "sound", "drum", "rattle", "bell", "blanket", "driftwood", "feathers"]
    for tag in order:
        if tag in tags:
            out.extend(known[tag])
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child that includes the words "noise-dim" and "voodoo" and uses sound effects like bam-bam and shh-shh.',
        f"Tell a gentle village story where {f['child'].id} cannot rest because {f['noise_cfg'].label} is too loud, and {f['elder'].id} calms it with a voodoo charm.",
        f'Write a small magical story in a folk-tale style where a loud sound grows quiet at the end, and the quieting is shown with sound effects.',
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", ""]
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


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    elder = world.add(Entity(id=params.elder_name, kind="character", type=params.elder_type, role="elder"))
    noise = world.add(Entity(id="noise", type="thing", label=NOISE_SOURCES[params.noise_source].label))
    charm = CHARMS[params.charm]
    helper = HELPERS[params.helper_item]

    world.facts["child"] = child
    world.facts["elder"] = elder
    world.facts["noise_cfg"] = NOISE_SOURCES[params.noise_source]
    world.facts["charm"] = charm
    world.facts["helper"] = helper
    world.facts["village"] = VILLAGES[params.village]

    setup(world, child, elder, VILLAGES[params.village])
    world.para()
    problem(world, child, NOISE_SOURCES[params.noise_source])
    warning(world, elder, child, NOISE_SOURCES[params.noise_source])
    world.para()
    charm_work(world, charm, helper, child, elder)
    ending(world, child, elder, NOISE_SOURCES[params.noise_source])

    world.facts["quieted"] = noise.meters["noise"] <= CALM_LIMIT
    return world


def explain_rejection() -> str:
    return "(No story: this combination would not make enough sense for a folk tale. Try a noisy thing plus a charm and helper item that can dim it.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.noise_source and args.noise_source not in NOISE_SOURCES:
        raise StoryError("(Unknown noise source.)")
    if args.charm and args.charm not in CHARMS:
        raise StoryError("(Unknown charm.)")
    if args.helper_item and args.helper_item not in HELPERS:
        raise StoryError("(Unknown helper item.)")
    combos = valid_combos()
    combo_ok = []
    for village, noise_id, pack in combos:
        charm_id, helper_id = pack.split("+")
        if args.village is not None and village != args.village:
            continue
        if args.noise_source is not None and noise_id != args.noise_source:
            continue
        if args.charm is not None and charm_id != args.charm:
            continue
        if args.helper_item is not None and helper_id != args.helper_item:
            continue
        combo_ok.append((village, noise_id, charm_id, helper_id))
    if not combo_ok:
        raise StoryError(explain_rejection())
    village, noise_id, charm_id, helper_id = rng.choice(sorted(combo_ok))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    child_trait = rng.choice(TRAITS)
    return StoryParams(
        village=village,
        noise_source=noise_id,
        charm=charm_id,
        helper_item=helper_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_name=elder_name,
        elder_gender="adult",
        elder_type=elder_type,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.noise_source not in NOISE_SOURCES:
        raise StoryError("Invalid noise source.")
    if params.charm not in CHARMS:
        raise StoryError("Invalid charm.")
    if params.helper_item not in HELPERS:
        raise StoryError("Invalid helper item.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    ap = argparse.ArgumentParser(description="A folk-tale storyworld with noise-dim voodoo sound effects.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--noise-source", choices=NOISE_SOURCES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--helper-item", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather", "aunt", "uncle"])
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
    StoryParams(village="river", noise_source="drum", charm="voodoo_doll", helper_item="blanket",
                child_name="Mira", child_gender="girl", elder_name="Grandma Iva",
                elder_gender="adult", elder_type="grandmother", child_trait="curious"),
    StoryParams(village="forest", noise_source="bell", charm="voodoo_bell", helper_item="driftwood",
                child_name="Bram", child_gender="boy", elder_name="Aunt Siba",
                elder_gender="adult", elder_type="aunt", child_trait="quiet"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for nid, n in NOISE_SOURCES.items():
        lines.append(asp.fact("noise_source", nid))
        lines.append(asp.fact("noise_loudness", nid, n.loudness))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("charm_power", cid, c.power))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper_item", hid))
        lines.append(asp.fact("helper_power", hid, h.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(V,N,C,H) :- village(V), noise_source(N), charm(C), helper_item(H),
                   noise_loudness(N,L), charm_power(C,CP), helper_power(H,HP),
                   CP + HP >= L.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    rc = 0
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and Python gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        print(f"FAIL: generate() smoke test crashed: {exc}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
