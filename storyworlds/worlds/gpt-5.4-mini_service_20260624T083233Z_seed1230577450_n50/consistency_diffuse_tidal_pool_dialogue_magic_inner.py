#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "queen", "priestess"}
        male = {"boy", "father", "dad", "man", "brother", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the tidal pool"
    affords: set[str] = field(default_factory=set)


@dataclass
class Rite:
    id: str
    name: str
    whisper: str
    action: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    type: str
    needed: str
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    holds: set[str]
    steadies: set[str]
    prep: str
    finish: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.tide: str = "low"
        self.magic_kind: str = ""

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.tide = self.tide
        w.magic_kind = self.magic_kind
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


def _r_diffuse(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("magic", 0.0) < THRESHOLD:
            continue
        if e.location != world.setting.place:
            continue
        if e.meters.get("consistency", 0.0) >= THRESHOLD:
            continue
        sig = ("diffuse", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["magic"] = max(0.0, e.meters.get("magic", 0.0) - 1.0)
        e.meters["diffuse"] = e.meters.get("diffuse", 0.0) + 1.0
        out.append(f"The spell thinned like mist.")
    return out


def _r_steady(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("consistency", 0.0) < THRESHOLD:
            continue
        sig = ("steady", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["magic"] = e.meters.get("magic", 0.0) + 1.0
        e.memes["resolve"] = e.memes.get("resolve", 0.0) + 1.0
        out.append(f"The charm held its shape.")
    return out


def _r_tide_turn(world: World) -> list[str]:
    for e in world.characters():
        if e.memes.get("doubt", 0.0) >= THRESHOLD and e.memes.get("guidance", 0.0) >= THRESHOLD:
            sig = ("turn", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["doubt"] = 0.0
            e.memes["resolve"] = e.memes.get("resolve", 0.0) + 1.0
            return ["__turn__"]
    return []


CAUSAL_RULES = [
    ("diffuse", _r_diffuse),
    ("steady", _r_steady),
    ("tide_turn", _r_tide_turn),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__turn__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    name: str
    guide: str
    rite: str
    charm: str
    seed: Optional[int] = None


SETTING = Setting(place="the tidal pool", affords={"binding", "whispering"})
RITES = {
    "binding": Rite(
        id="binding",
        name="binding the moon-salt",
        whisper="the moon-salt must be bound before the tide returns",
        action="bind the moon-salt",
        risk="diffuse away",
        keyword="consistency",
        tags={"consistency", "diffuse", "magic"},
    ),
    "whispering": Rite(
        id="whispering",
        name="whispering to the shell",
        whisper="the shell will answer only if the voice stays calm",
        action="whisper to the shell",
        risk="scatter like foam",
        keyword="diffuse",
        tags={"diffuse", "magic"},
    ),
}
CHARMS = {
    "moon-salt": Charm(
        id="moon-salt",
        label="moon-salt",
        phrase="a small bowl of moon-salt",
        type="salt",
        needed="binding",
        plural=False,
    ),
    "tidal-paste": Charm(
        id="tidal-paste",
        label="tidal paste",
        phrase="a cup of tidal paste",
        type="paste",
        needed="binding",
        plural=False,
    ),
}
AIDS = [
    Aid(
        id="shell-spoon",
        label="a shell spoon",
        phrase="a shell spoon with a deep curve",
        holds={"moon-salt", "tidal-paste"},
        steadies={"binding"},
        prep="lift the shell spoon into the mixture",
        finish="They kept stirring with the shell spoon until the paste thickened",
    ),
    Aid(
        id="reed-staff",
        label="a reed staff",
        phrase="a reed staff wrapped with kelp thread",
        holds={"moon-salt"},
        steadies={"whispering"},
        prep="rest the reed staff beside the bowl",
        finish="The reed staff helped the words stay gentle",
    ),
]

NAMES = ["Nera", "Mira", "Ari", "Lio", "Sera", "Tavi"]
GUIDES = ["grandmother", "aunt", "uncle", "old priestess", "harbor keeper"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rite_id, rite in RITES.items():
        for charm_id, charm in CHARMS.items():
            if charm.needed == rite_id:
                combos.append((SETTING.place, rite_id, charm_id))
    return combos


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    world.magic_kind = "mythic"
    hero = world.add(Entity(id=params.name, kind="character", type="girl", traits=["young", "solemn"]))
    guide = world.add(Entity(id="Guide", kind="character", type="priestess", label=params.guide))
    charm = world.add(Entity(id="Charm", type=CHARMS[params.charm].type, label=CHARMS[params.charm].label,
                             phrase=CHARMS[params.charm].phrase, owner=hero.id, caretaker=guide.id))
    aid_def = next(a for a in AIDS if a.steadies.__contains__(params.rite))
    aid = world.add(Entity(id=aid_def.id, type="tool", label=aid_def.label, phrase=aid_def.phrase,
                           owner=hero.id, caretaker=guide.id, plural=aid_def.plural))
    aid.carried_by = hero.id
    charm.carried_by = hero.id
    world.tide = "falling"

    # Act 1
    world.say(f"{hero.id} was a little keeper of the tidal pool, where the rocks shone like old silver.")
    world.say(f"{hero.id} loved the tidepool because it listened when the wind and water spoke together.")
    world.say(f"One dusk, {params.guide} came with a bowl and said, \"{RITES[params.rite].whisper}.\"")
    world.say(f"{hero.id} held {charm.phrase} and thought, \"If the magic stays thick, the sea cannot steal it.\"")
    charm.meters["consistency"] = 0.0
    charm.meters["magic"] = 1.0
    hero.memes["doubt"] = 0.0
    hero.memes["guidance"] = 1.0

    world.para()

    # Act 2
    world.say(f"The tidepool breathed in and out; bubbles rose like tiny moons between the stones.")
    world.say(f"{hero.id} began to {RITES[params.rite].action} as the guide watched carefully.")
    if params.rite == "binding":
        world.say(f"But the water was sly, and the charm wanted to diffuse into the salt-blue light.")
    else:
        world.say(f"But the old shell drank in the sound, and the words seemed ready to scatter.")
    charm.meters["magic"] += 1.0
    propagate(world)
    hero.memes["doubt"] += 1.0
    world.say(f"{hero.id} thought, \"Will the old sea let me keep this vow?\"")

    world.para()

    # Act 3
    world.say(f'The guide said, "{aid_def.prep}."')
    charm.meters["consistency"] = 1.0
    aid.meters["steadiness"] = 1.0
    hero.memes["guidance"] += 1.0
    world.say(f"{hero.id} obeyed and pressed the {aid.label} into the bowl.")
    propagate(world)
    world.say(f"{aid_def.finish}, and the magic grew steady as a drumbeat under the waves.")
    world.say(f"{hero.id} whispered once more, and this time the charm did not diffuse; it shimmered in one bright shape.")
    world.say(f"Then the tidepool answered with a silver glow, and {hero.id} smiled as the moon returned to the water.")

    world.facts.update(
        hero=hero,
        guide=guide,
        charm=charm,
        aid=aid,
        rite=RITES[params.rite],
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    rite = f["rite"]
    charm = f["charm"]
    return [
        f'Write a short myth for a child about "{rite.keyword}" at a tidal pool.',
        f"Tell a gentle story where {hero.id} must keep {charm.label} from drifting away while the tide rises.",
        f"Write a mythic scene with dialogue, magic, and inner monologue in a tidal pool, ending with the charm becoming steady.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    charm = f["charm"]
    rite = f["rite"]
    return [
        QAItem(
            question=f"Who is the story about in the tidal pool?",
            answer=f"It is about {hero.id}, a young keeper who is learning old magic at the tidal pool.",
        ),
        QAItem(
            question=f"What did {guide.label} ask {hero.id} to do?",
            answer=f"{guide.label.capitalize()} asked {hero.id} to {rite.action}.",
        ),
        QAItem(
            question=f"What problem made the magic hard at first?",
            answer=f"At first, {charm.label} could diffuse into the salt water, so the charm would not stay thick and steady.",
        ),
        QAItem(
            question=f"How did {hero.id} help the spell work?",
            answer=f"{hero.id} used {world.get('shell-spoon').label} and kept the mix consistent, so the magic held its shape.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"In the end, the charm shone clearly in the tidal pool, and {hero.id} saw that the magic could stay together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a little pool of seawater left behind among the rocks when the tide goes out.",
        ),
        QAItem(
            question="What does diffuse mean?",
            answer="Diffuse means to spread out and become less tightly gathered, like mist thinning in the air.",
        ),
        QAItem(
            question="What is consistency?",
            answer="Consistency means how thick, steady, or even something is. A thick paste has more consistency than watery soup.",
        ),
        QAItem(
            question="Why do people stir a mixture when they make magic or food?",
            answer="People stir to mix the parts together evenly so the result stays smooth and does not separate too quickly.",
        ),
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired) if world.fired else []}")
    return "\n".join(lines)


ASP_RULES = r"""
place(tidal_pool).
rite(binding).
rite(whispering).

charm(moon_salt).
charm(tidal_paste).

needed(binding, moon_salt).
needed(binding, tidal_paste).

risk_of(binding, diffuse).
risk_of(whispering, scatter).

valid_story(P, R, C) :- place(P), rite(R), charm(C), needed(R, C).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "tidal_pool")]
    for r in RITES:
        lines.append(asp.fact("rite", r))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    for rid, rite in RITES.items():
        lines.append(asp.fact("risk_of", rid, "diffuse" if rid == "binding" else "scatter"))
        lines.append(asp.fact("needed", rid, "moon_salt" if rid == "binding" else "tidal_paste"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic tidal-pool story world.")
    ap.add_argument("--place", choices=["tidal_pool"], default="tidal_pool")
    ap.add_argument("--rite", choices=list(RITES))
    ap.add_argument("--charm", choices=list(CHARMS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--guide", choices=GUIDES)
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
    if args.rite and args.charm and (args.place, args.rite, args.charm) not in combos:
        raise StoryError("No valid tidal-pool myth matches those choices.")
    place, rite, charm = rng.choice(combos)
    if args.rite:
        rite = args.rite
    if args.charm:
        charm = args.charm
    name = args.name or rng.choice(NAMES)
    guide = args.guide or rng.choice(GUIDES)
    return StoryParams(name=name, guide=guide, rite=rite, charm=charm)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(name="Nera", guide="old priestess", rite="binding", charm="moon-salt"),
    StoryParams(name="Mira", guide="aunt", rite="whispering", charm="tidal-paste"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.rite} / {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
