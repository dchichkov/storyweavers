#!/usr/bin/env python3
"""
storyworlds/worlds/upright_evolution_teamwork_twist_superhero_story.py
======================================================================

A small superhero story world about teamwork, a surprising twist, and two
words that must appear in the rendered tales: "upright" and "evolution".

The seed tale behind this world:
A junior hero wants to keep a city garden upright after a blustery storm bends
a statue and topples a signal beacon. A second hero thinks the job is just a
simple rescue, but the twist is that the statue's base holds tiny training
gears that can only be unlocked when both heroes work together. Their teamwork
brings the beacon back on, the statue back upright, and a shy sidekick through
an evolution from nervous helper to confident partner.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class District:
    id: str
    label: str
    outdoors: bool = True
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HeroRole:
    id: str
    label: str
    title: str
    power: str
    recovery: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TwistDevice:
    id: str
    label: str
    reveal: str
    unlock: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    district: str = ""
    hero: str = ""
    partner: str = ""
    twist: str = ""
    seed: Optional[int] = None


DISTRICTS = {
    "city_garden": District(
        id="city_garden",
        label="the city garden",
        outdoors=True,
        supports={"storm", "rescue", "beacon"},
        tags={"garden", "city"},
    ),
    "roof_plaza": District(
        id="roof_plaza",
        label="the rooftop plaza",
        outdoors=True,
        supports={"storm", "rescue", "beacon"},
        tags={"roof", "city"},
    ),
    "metro_atrium": District(
        id="metro_atrium",
        label="the metro atrium",
        outdoors=False,
        supports={"rescue", "beacon"},
        tags={"metro", "city"},
    ),
}

HEROES = {
    "spark": HeroRole(
        id="spark",
        label="Sparkwing",
        title="junior hero",
        power="light bridges",
        recovery="a brighter signal",
        tags={"light", "teamwork"},
    ),
    "moss": HeroRole(
        id="moss",
        label="Mossguard",
        title="steady hero",
        power="steady hands",
        recovery="a stable landing",
        tags={"steady", "teamwork"},
    ),
    "pulse": HeroRole(
        id="pulse",
        label="Pulsebolt",
        title="quick hero",
        power="signal bursts",
        recovery="a clear call",
        tags={"signal", "teamwork"},
    ),
}

TWISTS = {
    "seed_bots": TwistDevice(
        id="seed_bots",
        label="seed bots",
        reveal="tiny seed bots hidden in the statue base",
        unlock="only both heroes could turn the old dial at once",
        tags={"seed", "twist", "evolution"},
    ),
    "mirror_map": TwistDevice(
        id="mirror_map",
        label="mirror map",
        reveal="a mirror map tucked beneath the beacon plate",
        unlock="the map only glowed when the two heroes stood side by side",
        tags={"mirror", "twist", "evolution"},
    ),
    "training_gears": TwistDevice(
        id="training_gears",
        label="training gears",
        reveal="little training gears inside the fallen pedestal",
        unlock="the gears snapped together only when the pair moved in step",
        tags={"gear", "twist", "evolution"},
    ),
}

GIRL_NAMES = ["Ava", "Maya", "Nora", "Zoe", "Lina", "Iris"]
BOY_NAMES = ["Leo", "Theo", "Noah", "Eli", "Finn", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for d in DISTRICTS:
        for h in HEROES:
            for p in HEROES:
                if h != p:
                    combos.append((d, h, p))
    return combos


def explain_rejection() -> str:
    return "(No story: this combination does not leave room for teamwork and a twist.)"


class World:
    def __init__(self, district: District) -> None:
        self.district = district
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paras: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paras[-1].append(text)

    def para(self) -> None:
        if self.paras[-1]:
            self.paras.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paras if p)

    def copy(self) -> "World":
        import copy
        w = World(self.district)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paras = [[]]
        return w


def setup_story(world: World, hero: Entity, partner: Entity, twist: TwistDevice) -> None:
    hero.memes.setdefault("hope", 0.0)
    hero.memes.setdefault("teamwork", 0.0)
    hero.memes.setdefault("joy", 0.0)
    hero.memes.setdefault("worry", 0.0)
    partner.memes.setdefault("hope", 0.0)
    partner.memes.setdefault("teamwork", 0.0)
    partner.memes.setdefault("joy", 0.0)
    partner.memes.setdefault("worry", 0.0)
    world.say(
        f"{hero.id} was {hero.label_word}, a {hero.type} hero who kept the city moving."
    )
    world.say(
        f"{partner.id} was {partner.label_word}, and together they watched over {world.district.label}."
    )
    world.say(
        f"After a storm bent the main beacon, they hurried to the plaza to keep it upright."
    )


def predict_twist(world: World, twist: TwistDevice) -> bool:
    return True if twist.id in TWISTS else False


def apply_bend(world: World, hero: Entity, partner: Entity) -> None:
    world.get("beacon").meters["tilt"] += 1
    hero.memes["worry"] += 1
    partner.memes["worry"] += 1
    world.say(
        f"The beacon swayed on its broken mount, and {hero.id} saw that one hero alone could not fix it."
    )


def warn_of_twist(world: World, partner: Entity, twist: TwistDevice) -> None:
    world.say(
        f"{partner.id} pointed at {twist.reveal} and said the problem was bigger than a quick lift."
    )
    world.say(
        f'"We need teamwork," {partner.id} said, "because {twist.unlock}."'
    )
    partner.memes["teamwork"] += 1


def work_together(world: World, hero: Entity, partner: Entity, twist: TwistDevice) -> None:
    hero.memes["teamwork"] += 1
    hero.memes["hope"] += 1
    partner.memes["hope"] += 1
    world.get("beacon").meters["tilt"] = 0.0
    world.get("statue").meters["upright"] = 1.0
    world.get("sidekick").memes["growth"] += 1
    world.say(
        f"So they worked side by side: one held the base, the other turned the dial, and the twist clicked open."
    )
    world.say(
        f"Inside, {twist.unlock}; the hidden parts helped the statue stand upright again."
    )


def evolution_turn(world: World, hero: Entity, partner: Entity) -> None:
    sidekick = world.get("sidekick")
    sidekick.memes["growth"] += 1
    sidekick.memes["confidence"] += 1
    sidekick.meters["upright"] = 1.0
    world.say(
        f"The shy sidekick stepped forward too, and that was an evolution from timid helper to brave partner."
    )
    world.say(
        f"By the end, {hero.id} and {partner.id} were smiling while the whole square glowed clean and bright."
    )


def tell(district: District, hero_cfg: HeroRole, partner_cfg: HeroRole, twist: TwistDevice,
         hero_name: str, hero_type: str, partner_name: str, partner_type: str) -> World:
    world = World(district)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_cfg.label))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_type, label=partner_cfg.label))
    world.add(Entity(id="beacon", kind="object", type="beacon", label="the beacon", meters={"tilt": 0.0}))
    world.add(Entity(id="statue", kind="object", type="statue", label="the statue", meters={"upright": 0.0}))
    world.add(Entity(id="sidekick", kind="character", type="hero", label="the sidekick", memes={"growth": 0.0, "confidence": 0.0}, meters={"upright": 0.0}))
    world.facts["district"] = district
    world.facts["hero_cfg"] = hero_cfg
    world.facts["partner_cfg"] = partner_cfg
    world.facts["twist"] = twist
    setup_story(world, hero, partner, twist)
    world.para()
    apply_bend(world, hero, partner)
    warn_of_twist(world, partner, twist)
    world.para()
    work_together(world, hero, partner, twist)
    evolution_turn(world, hero, partner)
    world.facts["hero"] = hero
    world.facts["partner"] = partner
    world.facts["resolved"] = True
    world.facts["upright"] = True
    world.facts["evolution"] = True
    return world


def knowledge_qa() -> list[QAItem]:
    return [
        QAItem("What does teamwork mean?", "Teamwork means people help each other and use their different strengths together. The job gets easier because everyone does a part."),
        QAItem("What is a twist in a story?", "A twist is a surprising change that makes the story go in a new direction. It often reveals something the characters did not expect."),
        QAItem("What does upright mean?", "Upright means standing straight and not leaning over. Something upright is steady and ready to stay in place."),
        QAItem("What does evolution mean in a story like this?", "Here, evolution means a big change over time. A shy helper can grow into a confident partner by the end."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero_cfg"]
    partner = f["partner_cfg"]
    twist = f["twist"]
    district = f["district"]
    return [
        f'Write a superhero story for a young child about {hero.label} and {partner.label} at {district.label}, and include the words "upright" and "evolution".',
        f"Tell a short teamwork story where two heroes fix a bent beacon, then discover a surprise twist hidden in the base.",
        f'Write a gentle superhero tale about teamwork, a twist, and a character growing through an evolution from shy to brave.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    twist = f["twist"]
    district = f["district"]
    return [
        QAItem(
            f"Who were the heroes in {district.label}?",
            f"{hero.id} and {partner.id} were the heroes watching over {district.label}. They worked together to fix the bent beacon and protect the square.",
        ),
        QAItem(
            "Why did they need teamwork?",
            "They needed teamwork because one hero could hold the base, but both heroes were needed to unlock the hidden parts. That was the only way to bring the beacon back upright.",
        ),
        QAItem(
            f"What was the twist in the story?",
            f"The twist was {twist.reveal}. It changed the problem from a simple repair into a puzzle that only teamwork could solve.",
        ),
        QAItem(
            "How did the sidekick change?",
            "The sidekick became more confident by the end. That was an evolution from shy helper to brave partner because the heroes welcomed the extra help.",
        ),
        QAItem(
            "What proved the problem was solved?",
            "The beacon stood upright again, and the statue stayed straight too. That ending image showed that the rescue changed the whole place.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out = [
        QAItem("What is a superhero team?", "A superhero team is a group of heroes who help each other use their powers for a good job. Together they can do things one hero could not do alone."),
        QAItem("Why do heroes work together?", "Heroes work together because different jobs need different strengths. One can hold, one can turn, and one can watch for danger."),
    ]
    return out + knowledge_qa()


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(district="city_garden", hero="spark", partner="moss", twist="training_gears"),
    StoryParams(district="roof_plaza", hero="pulse", partner="spark", twist="seed_bots"),
    StoryParams(district="metro_atrium", hero="moss", partner="pulse", twist="mirror_map"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.district and args.hero and args.partner and args.hero == args.partner:
        raise StoryError("The two heroes must be different so teamwork can happen.")
    filtered = [
        c for c in combos
        if (args.district is None or c[0] == args.district)
        and (args.hero is None or c[1] == args.hero)
        and (args.partner is None or c[2] == args.partner)
    ]
    if not filtered:
        raise StoryError(explain_rejection())
    district, hero, partner = rng.choice(sorted(filtered))
    twist = args.twist or rng.choice(sorted(TWISTS))
    return StoryParams(district=district, hero=hero, partner=partner, twist=twist)


def generate(params: StoryParams) -> StorySample:
    if params.district not in DISTRICTS or params.hero not in HEROES or params.partner not in HEROES or params.twist not in TWISTS:
        raise StoryError("Unknown story parameters.")
    if params.hero == params.partner:
        raise StoryError("Teamwork stories need two different heroes.")
    world = tell(
        DISTRICTS[params.district],
        HEROES[params.hero],
        HEROES[params.partner],
        TWISTS[params.twist],
        hero_name=random.choice(GIRL_NAMES + BOY_NAMES),
        hero_type="hero",
        partner_name=random.choice(GIRL_NAMES + BOY_NAMES),
        partner_type="hero",
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world with teamwork and a twist.")
    ap.add_argument("--district", choices=DISTRICTS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--partner", choices=HEROES)
    ap.add_argument("--twist", choices=TWISTS)
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


ASP_RULES = r"""
hero(H) :- hero_cfg(H).
partner(P) :- partner_cfg(P).
twist(T) :- twist_cfg(T).
teamwork_story(D,H,P,T) :- district(D), hero(H), partner(P), H != P, twist(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for d in DISTRICTS:
        lines.append(asp.fact("district", d))
    for h in HEROES:
        lines.append(asp.fact("hero_cfg", h))
    for p in HEROES:
        lines.append(asp.fact("partner_cfg", p))
    for t in TWISTS:
        lines.append(asp.fact("twist_cfg", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show teamwork_story/4."))
    return sorted(set(asp.atoms(model, "teamwork_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP:")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print(f"OK: ASP matches Python ({len(py)} combos) and smoke generation worked.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show teamwork_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} teamwork combos")
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if args.all:
            p = sample.params
            header = f"### {p.district}: {p.hero} + {p.partner} ({p.twist})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
