#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/art_tuvwx_kindness_fairy_tale.py
=================================================================

A standalone storyworld for a tiny fairy-tale domain: a child makes a bit of art,
a strange five-letter charm word ("tuvwx") causes a small mistake, and kindness
turns the mistake into a new picture everyone can share.

The world is deliberately small and state-driven:
- a maker and a helper have physical meters and emotional memes,
- a painted thing can be smudged or brightened,
- a gentle repair can restore it,
- the ending image proves that kindness changed the scene.

The script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  main
- supports --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and an inline ASP twin
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
SENSE_MIN = 2
KINDNESS_BONUS = 1.0


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
    colorful: bool = False
    fragile: bool = False
    can_smudge: bool = False
    can_fix: bool = False
    kind_word: str = ""

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "fairy"}
        male = {"boy", "father", "dad", "man", "king", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Realm:
    id: str
    scene: str
    place: str
    art_surface: str
    ending_image: str
    fairytale_tag: str


@dataclass
class ColorCharm:
    id: str
    spoken: str
    effect: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Artwork:
    id: str
    label: str
    surface: str
    kind: str
    fragile: bool = False
    can_smudge: bool = True
    can_fix: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    maker = world.entities.get("maker")
    art = world.entities.get("art")
    if not maker or not art:
        return out
    if maker.meters["mess"] < THRESHOLD or art.meters["on"] < THRESHOLD:
        return out
    sig = ("smudge", art.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    art.meters["smudged"] += 1
    art.memes["sadness"] += 1
    out.append("__smudge__")
    return out


def _r_kindness(world: World) -> list[str]:
    helper = world.entities.get("helper")
    maker = world.entities.get("maker")
    if not helper or not maker:
        return []
    if helper.memes["kindness"] < THRESHOLD:
        return []
    sig = ("kindness", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    maker.memes["hope"] += KINDNESS_BONUS
    helper.memes["warmth"] += 1
    return ["__kindness__"]


CAUSAL_RULES = [
    Rule("smudge", "physical", _r_smudge),
    Rule("kindness", "social", _r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(realm: Realm, art: Artwork, charm: ColorCharm, repair: Repair) -> bool:
    return realm.id in REALMS and art.id in ARTWORKS and charm.id in CHARMS and repair.id in REPAIRS


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def best_repair() -> Repair:
    return max(REPAIRS.values(), key=lambda r: r.sense)


def would_smudge(art: Artwork, charm: ColorCharm) -> bool:
    return art.can_smudge and charm.safe is False


def is_fixed(repair: Repair, art: Artwork, delay: int) -> bool:
    severity = 1 + delay
    return repair.power >= severity


def predict_mistake(world: World) -> dict:
    sim = world.copy()
    _do_charm(sim, narrate=False)
    return {"smudged": sim.get("art").meters["smudged"] >= THRESHOLD,
            "hope": sim.get("maker").memes["hope"]}


def _do_charm(world: World, narrate: bool = True) -> None:
    maker = world.get("maker")
    art = world.get("art")
    charm = world.get("charm")
    maker.meters["mess"] += 1
    maker.memes["wonder"] += 1
    if would_smudge(art.attrs["artwork"], charm.attrs["colorcharm"]):
        propagate(world, narrate=narrate)


def introduce(world: World, maker: Entity, helper: Entity, realm: Realm) -> None:
    maker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Long ago, in {realm.place}, there lived {maker.id} and {helper.id}. "
        f"They loved {realm.scene}, and every bright line of art made the hall feel like a spell."
    )


def show_art(world: World, maker: Entity, art: Entity, realm: Realm) -> None:
    world.say(
        f"{maker.id} had made {art.label} on {realm.art_surface}. "
        f"It was bright, careful, and full of little stars."
    )


def tempt(world: World, maker: Entity, charm: Entity) -> None:
    maker.memes["curiosity"] += 1
    world.say(
        f"Then {maker.id} found the word {charm.kind_word} written on a ribbon. "
        f'"{charm.attrs["spoken"]}!" {maker.id} whispered, and the ribbon seemed to shimmer.'
    )


def warn(world: World, helper: Entity, maker: Entity, art: Entity, charm: Entity) -> None:
    pred = predict_mistake(world)
    helper.memes["kindness"] += 1
    if pred["smudged"]:
        world.say(
            f"{helper.id} bit {helper.pronoun("possessive")} lip. "
            f'"{maker.id}, that word can make the paint slip," {helper.id} said. '
            f'"Let us keep the picture safe."'
        )
    else:
        world.say(
            f"{helper.id} smiled and said, "
            f'"We can use {charm.kind_word} only if we are careful with the art."'
        )


def ignore_warning(world: World, maker: Entity, charm: Entity) -> None:
    maker.memes["defiance"] += 1
    world.say(
        f"But {maker.id} was braver than wise and said the word anyway. "
        f'"{charm.attrs["spoken"]}!"'
    )


def smudge_scene(world: World, art: Entity) -> None:
    art.meters["smudged"] += 1
    art.meters["blemish"] += 1
    world.say(
        f"The paint on {art.label} shivered and a dark little smear bloomed across it."
    )


def gentle_help(world: World, helper: Entity, repair: Repair, art: Entity) -> None:
    art.meters["smudged"] = 0.0
    art.meters["bright"] += 1
    world.get("maker").memes["hope"] += 1
    world.say(
        f"{helper.id} came close and {repair.text.replace('{art}', art.label)}."
    )
    world.say(
        f"The smear faded, and the picture looked bright again."
    )


def hard_fail(world: World, helper: Entity, repair: Repair, art: Entity) -> None:
    world.say(
        f"{helper.id} tried, but {repair.fail.replace('{art}', art.label)}."
    )
    world.say(
        f"The hall stayed gray, and the picture kept its sad little streak."
    )


def ending(world: World, realm: Realm) -> None:
    world.say(realm.ending_image)


def tell(realm: Realm, art_cfg: Artwork, charm_cfg: ColorCharm, repair: Repair,
         maker_name: str = "Mira", maker_gender: str = "girl",
         helper_name: str = "Nico", helper_gender: str = "boy") -> World:
    world = World()
    maker = world.add(Entity(id=maker_name, kind="character", type=maker_gender, role="maker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    charm = world.add(Entity(id="charm", kind="thing", type="thing", kind_word=charm_cfg.id, attrs={"spoken": charm_cfg.spoken}))
    art = world.add(Entity(id="art", kind="thing", type="thing", label=art_cfg.label, fragile=art_cfg.fragile))
    art.attrs["artwork"] = art_cfg
    charm.attrs["colorcharm"] = charm_cfg

    introduce(world, maker, helper, realm)
    world.para()
    show_art(world, maker, art, realm)
    tempt(world, maker, charm)
    warn(world, helper, maker, art, charm)
    ignore_warning(world, maker, charm)

    world.para()
    if would_smudge(art_cfg, charm_cfg):
        smudge_scene(world, art)
    delay = 0
    if is_fixed(repair, art_cfg, delay):
        gentle_help(world, helper, repair, art)
        ending(world, realm)
        outcome = "fixed"
    else:
        hard_fail(world, helper, repair, art)
        ending(world, realm)
        outcome = "stained"

    world.facts.update(
        maker=maker, helper=helper, charm=charm, art=art,
        realm=realm, art_cfg=art_cfg, charm_cfg=charm_cfg, repair=repair,
        outcome=outcome, smudged=art.meters["smudged"] >= THRESHOLD,
        repaired=outcome == "fixed",
    )
    return world


REALMS = {
    "castle": Realm("castle", "a castle hall full of banners", "the castle hall",
                    "a silver table", "At last, the hall shone with a fresh picture of a kind queen and a laughing star.",
                    "castle"),
    "meadow": Realm("meadow", "a meadow fair with songs", "the meadow stage",
                    "a wooden easel", "At the end, the moon rose over a picture of friends sharing red apples.",
                    "meadow"),
    "village": Realm("village", "a village feast with lanterns", "the village wall",
                     "a chalk board", "In the last glow of dusk, the wall held a bright mural of neighbors holding hands.",
                     "village"),
}

CHARMS = {
    "tuvwx": ColorCharm("tuvwx", "tuvwx", "a little slip of paint magic", safe=False, tags={"magic", "art", "tuvwx"}),
    "sparkle": ColorCharm("sparkle", "sparkle", "a harmless shine", safe=True, tags={"art", "kindness"}),
    "rainbow": ColorCharm("rainbow", "rainbow", "a gentle color song", safe=True, tags={"art", "kindness"}),
}

ARTWORKS = {
    "mural": Artwork("mural", "the mural", "wall", "mural", fragile=False, can_smudge=True, can_fix=True, tags={"art"}),
    "banner": Artwork("banner", "the banner", "cloth", "banner", fragile=True, can_smudge=True, can_fix=True, tags={"art"}),
    "panel": Artwork("panel", "the painted panel", "wood", "panel", fragile=False, can_smudge=True, can_fix=True, tags={"art"}),
}

REPAIRS = {
    "careful_wipe": Repair("careful_wipe", 3, 2,
                           "carefully wiped the paint with a soft cloth until the colors breathed again",
                           "wiped and wiped, but the stain had already sunk too deep",
                           "carefully wiped the paint off the {art}"),
    "new_layer": Repair("new_layer", 2, 1,
                        "painted a new layer over the mark with a small, patient brush",
                        "painted, but the new layer was too thin to hide the mark",
                        "painted a new layer over the {art}"),
    "gold_leaf": Repair("gold_leaf", 4, 3,
                        "pressed a little gold leaf over the hurt place so it shone like a star",
                        "pressed gold leaf on it, but the crack still showed through",
                        "pressed gold leaf over the {art}"),
}

GIRL_NAMES = ["Mira", "Elin", "Luna", "Ivy", "Nora", "Tessa", "Ayla", "Rosa"]
BOY_NAMES = ["Nico", "Pip", "Tomas", "Jory", "Ari", "Luca", "Soren", "Theo"]
TRAITS = ["gentle", "curious", "hopeful", "patient", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for realm in REALMS:
        for art in ARTWORKS:
            for charm in CHARMS:
                if reasonableness_gate(REALMS[realm], ARTWORKS[art], CHARMS[charm], best_repair()):
                    combos.append((realm, art, charm))
    return combos


@dataclass
class StoryParams:
    realm: str
    art: str
    charm: str
    repair: str
    maker: str
    maker_gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "art": [("What is art?",
             "Art is something people make to show a feeling, a story, or a lovely idea. It can be a painting, a song, a picture, or a sculpture.")],
    "kindness": [("What is kindness?",
                  "Kindness means being gentle and helpful to someone else. A kind person tries to make another person feel safe, seen, and cared for.")],
    "paint": [("Why can paint be messy?",
               "Paint can be messy because it is wet and can drip, smear, or stick to things before it dries.")],
    "brush": [("What does a brush do?",
               "A brush helps spread paint or glue in a neat way. It lets someone make careful lines and shapes.")],
    "gold": [("What is gold leaf?",
               "Gold leaf is a very thin sheet that shines like gold. People use it to make art look bright and special.")],
    "magic": [("Why should magic words be used carefully in fairy tales?",
               "In fairy tales, magic words can change things very quickly. That is why characters often need wisdom and kindness when they use them.")],
    "tuvwx": [("What is tuvwx in this story?",
               "tuvwx is a made-up charm word in this fairy tale. It is not real magic, but it helps the story show how a mistake can be fixed with kindness.")],
}
KNOWLEDGE_ORDER = ["art", "kindness", "paint", "brush", "gold", "magic", "tuvwx"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a young child that includes the word "art" and the strange charm word "{f["charm_cfg"].id}".',
        f"Tell a gentle story where {f['maker'].id} makes a picture, says a curious magic word, and {f['helper'].id} uses kindness to help.",
        f'Write a story with a castle-and-meadow fairy-tale feeling where kindness keeps the art beautiful after a small mistake.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    maker, helper, art, charm, repair = f["maker"], f["helper"], f["art"], f["charm"], f["repair"]
    out = []
    out.append(QAItem(
        question="Who is the story about?",
        answer=f"It is about {maker.id} and {helper.id}, two children in a fairy-tale place, and the art they were trying to keep beautiful."
    ))
    out.append(QAItem(
        question="What happened when the charm word was spoken?",
        answer=f"The word {f['charm_cfg'].id} made the paint slip, and the picture got smudged. The strange word caused a small problem, not a big disaster."
    ))
    out.append(QAItem(
        question="How did kindness change the story?",
        answer=f"{helper.id} stayed gentle, helped fix the mark, and made {maker.id} feel hopeful again. Because of that kindness, the art ended bright instead of ruined."
    ))
    if f["repaired"]:
        out.append(QAItem(
            question="How did they fix the art?",
            answer=f"They used {repair.id.replace('_', ' ')} ideas in the story: {repair.qa_text.replace('{art}', art.label)}. That careful repair brought the colors back."
        ))
    out.append(QAItem(
        question="How did the story end?",
        answer=f"It ended with the art looking bright again in {f['realm'].ending_image.lower()}. The ending image proves the mistake was turned into something lovely."
    ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["charm_cfg"].tags) | set(world.facts["art_cfg"].tags) | set(world.facts["repair"].tags)
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(q, a))
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("castle", "mural", "tuvwx", "careful_wipe", "Mira", "girl", "Nico", "boy", "gentle"),
    StoryParams("village", "banner", "tuvwx", "new_layer", "Elin", "girl", "Theo", "boy", "hopeful"),
    StoryParams("meadow", "panel", "tuvwx", "gold_leaf", "Luna", "girl", "Pip", "boy", "patient"),
]


def explain_rejection(realm: Realm, art: Artwork, charm: ColorCharm) -> str:
    if charm.safe:
        return "(No story: this charm does not create the small mistake the tale needs.)"
    if not art.can_smudge:
        return "(No story: that artwork would not smudge, so there is no useful turn for kindness.)"
    return "(No story: the combination is not interesting enough for a fairy-tale problem.)"


def outcome_of(params: StoryParams) -> str:
    repair = REPAIRS[params.repair]
    return "fixed" if is_fixed(repair, ARTWORKS[params.art], 0) else "stained"


ASP_RULES = r"""
valid(R, A, C) :- realm(R), art(A), charm(C), can_smudge(A), unsafe(C).
fixed(RP, A) :- repair(RP), power(RP, P), severity(1, S), P >= S.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in REALMS:
        lines.append(asp.fact("realm", rid))
    for aid, a in ARTWORKS.items():
        lines.append(asp.fact("art", aid))
        if a.can_smudge:
            lines.append(asp.fact("can_smudge", aid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if not c.safe:
            lines.append(asp.fact("unsafe", cid))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("severity", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale art storyworld with kindness and a strange charm word.")
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--art", choices=ARTWORKS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--maker")
    ap.add_argument("--maker-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.charm and CHARMS[args.charm].safe:
        raise StoryError("(No story: choose the unsafe charm tuvwx for a meaningful turn.)")
    combos = [c for c in valid_combos()
              if (args.realm is None or c[0] == args.realm)
              and (args.art is None or c[1] == args.art)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    realm, art, charm = rng.choice(sorted(combos))
    repair = args.repair or rng.choice(sorted(REPAIRS))
    art_gender = args.maker_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if art_gender == "girl" else "girl")
    maker = args.maker or rng.choice(GIRL_NAMES if art_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != maker])
    trait = rng.choice(TRAITS)
    return StoryParams(realm, art, charm, repair, maker, art_gender, helper, helper_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(REALMS[params.realm], ARTWORKS[params.art], CHARMS[params.charm], REPAIRS[params.repair],
                 params.maker, params.maker_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(i.question, i.answer) for i in story_qa(world)]],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, art, charm) combos:")
        for row in combos:
            print("  ", row)
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
            header = f"### {p.maker} and {p.helper}: {p.realm}, {p.art}, {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
