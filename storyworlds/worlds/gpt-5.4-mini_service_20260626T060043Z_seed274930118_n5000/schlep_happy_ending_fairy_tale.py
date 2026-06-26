#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a helper who must schlep a heavy bundle
through the woods, discovering that the hard errand becomes a happy ending when
kindness and teamwork light the load.

The seed word is "schlep": a character carries something awkward, long, or
weighty for someone else. The domain keeps a fairy-tale tone, with a small
cast, physical burdens, emotional strain, and a warm resolution.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "maid", "witch", "fairy", "princess", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "wizard", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    path: str
    has_bridge: bool = False
    has_cart: bool = False


@dataclass
class Burden:
    id: str
    label: str
    phrase: str
    weight: str
    awkward: bool
    can_share: bool
    mess: str
    destination: str
    keyword: str = "schlep"


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps_with: set[str] = field(default_factory=set)
    reduces: set[str] = field(default_factory=set)
    cooperative: bool = True
    plural: bool = False


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def make_meter() -> dict[str, float]:
    return {"burden": 0.0, "tired": 0.0, "mess": 0.0, "worry": 0.0, "hope": 0.0, "kindness": 0.0, "relief": 0.0}


def make_meme() -> dict[str, float]:
    return {"joy": 0.0, "fear": 0.0, "love": 0.0, "resolve": 0.0, "gratitude": 0.0, "worry": 0.0}


def _r_tired(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["burden"] < THRESHOLD:
            continue
        sig = ("tired", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["tired"] += 1
        out.append(f"{e.id} grew tired from the heavy schlep.")
    return out


def _r_mess(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["burden"] < THRESHOLD:
            continue
        sig = ("mess", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["mess"] += 1
        out.append(f"The long carry left {e.id}'s cloak dusty and rumpled.")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["burden"] >= THRESHOLD or e.memes["resolve"] < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["relief"] += 1
        e.memes["joy"] += 1
        out.append(f"{e.id} felt light as a feather at last.")
    return out


CAUSAL_RULES = [
    _r_tired,
    _r_mess,
    _r_relief,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_burden(world: World, hero: Entity, burden: Burden) -> dict:
    sim = world.copy()
    do_schlep(sim, sim.get(hero.id), burden, narrate=False)
    target = sim.get(burden.id)
    return {
        "tired": bool(hero.meters["tired"] >= THRESHOLD),
        "messed": bool(hero.meters["mess"] >= THRESHOLD),
        "delivered": bool(target.meters.get("delivered", 0) >= THRESHOLD),
    }


def setting_line(setting: Setting) -> str:
    if setting.has_bridge:
        return f"A little bridge crossed the stream, and the path curled toward the castle gate."
    if setting.has_cart:
        return f"A peasant cart waited by the lane, with room for a basket or two."
    return f"The path wound through the woods like a ribbon under the trees."


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"Once in a green little kingdom, {hero.id} was a {hero.type} who loved to help {helper.label}."
    )
    world.say(
        f"{helper.id} was known for a brave heart, a kind smile, and a talent for carrying what was hard to carry."
    )


def love_reason(world: World, hero: Entity, burden: Burden) -> None:
    hero.memes["love"] += 1
    world.say(
        f"On market day, {hero.id} was given {burden.phrase}, and {hero.pronoun('possessive')} eyes grew wide with wonder."
    )
    world.say(
        f"{hero.id} wanted to {burden.keyword} it all the way to {burden.destination} without complaint."
    )


def do_schlep(world: World, hero: Entity, burden: Burden, narrate: bool = True) -> None:
    hero.meters["burden"] += 1
    burden_ent = world.get(burden.id)
    burden_ent.carried_by = hero.id
    if narrate:
        world.say(
            f"So {hero.id} took a deep breath and began to schlep {burden_ent.phrase} along the path."
        )
    if burden.awkward:
        hero.memes["worry"] += 1
        if narrate:
            world.say(
                f"It was awkward and lopsided, and every few steps {hero.id} had to stop and adjust {hero.pronoun('possessive')} grip."
            )
    propagate(world, narrate=narrate)


def warning(world: World, helper: Entity, hero: Entity, burden: Burden) -> None:
    pred = predict_burden(world, hero, burden)
    helper.memes["worry"] += 1
    if pred["messed"]:
        world.say(
            f'"Careful," {helper.id} said. "If you keep going like that, you will get dusty and worn out."'
        )
    else:
        world.say(
            f'"Careful," {helper.id} said. "That load is tricky, but I can see your strong heart."'
        )


def struggle(world: World, hero: Entity, burden: Burden) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} kept going, but the bundle tugged and bumped, and the road seemed much longer than before."
    )


def offer_aid(world: World, helper: Entity, hero: Entity, burden: Burden, aid: Aid) -> Optional[Aid]:
    if burden.keyword not in aid.helps_with and not burden.can_share:
        return None
    if burden.mess in aid.reduces or burden.can_share:
        world.say(
            f"Then {helper.id} smiled and brought {aid.phrase}."
        )
        world.say(
            f'"We can share the schlep," {helper.id} said. "You do not have to carry this alone."'
        )
        return aid
    return None


def accept_help(world: World, hero: Entity, helper: Entity, burden: Burden, aid: Aid) -> None:
    hero.memes["resolve"] += 1
    hero.memes["joy"] += 1
    helper.memes["love"] += 1
    burden_ent = world.get(burden.id)
    burden_ent.carried_by = helper.id
    world.say(
        f"{hero.id} nodded, and together they lifted the bundle into the {aid.label}."
    )
    world.say(
        f"The road still wound on, but now the load rode steadier, and the two friends walked side by side."
    )


def resolution(world: World, hero: Entity, helper: Entity, burden: Burden) -> None:
    burden_ent = world.get(burden.id)
    burden_ent.meters["delivered"] = 1
    hero.memes["gratitude"] += 1
    helper.meters["relief"] += 1
    world.say(
        f"At last they reached {burden.destination}, and the burden was delivered safely."
    )
    world.say(
        f"{hero.id} laughed with relief, and {helper.id} laughed too, because the hard errand had become a happy deed."
    )
    world.say(
        f"In the end, the kingdom felt brighter, and even the dusty path seemed pleased to have helped tell the tale."
    )


@dataclass
class StoryParams:
    place: str
    burden: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    aid: str
    seed: Optional[int] = None


SETTINGS = {
    "forest": Setting(place="the forest road", path="a mossy path", has_bridge=True),
    "village": Setting(place="the village lane", path="a cobbled lane", has_cart=True),
    "hill": Setting(place="the windy hill path", path="a steep path"),
}

BURDENS = {
    "basket": Burden(
        id="basket",
        label="basket",
        phrase="a big basket of apples",
        weight="heavy",
        awkward=True,
        can_share=True,
        mess="dust",
        destination="the baker's cottage",
    ),
    "bundle": Burden(
        id="bundle",
        label="bundle",
        phrase="a bundled stack of bed quilts",
        weight="bulky",
        awkward=True,
        can_share=True,
        mess="dust",
        destination="the miller’s house",
    ),
    "jar": Burden(
        id="jar",
        label="jar",
        phrase="a jar of moonlit honey",
        weight="delicate",
        awkward=False,
        can_share=False,
        mess="spill",
        destination="the queen's pantry",
    ),
    "lantern": Burden(
        id="lantern",
        label="lantern",
        phrase="a bright lantern for the night watch",
        weight="careful",
        awkward=False,
        can_share=False,
        mess="smudge",
        destination="the castle gate",
    ),
}

AIDS = {
    "cart": Aid(
        id="cart",
        label="cart",
        phrase="a tiny handcart",
        helps_with={"schlep"},
        reduces={"dust", "spill", "smudge"},
    ),
    "rope": Aid(
        id="rope",
        label="rope sling",
        phrase="a rope sling and a soft cloth",
        helps_with={"schlep"},
        reduces={"dust", "spill"},
    ),
    "barrow": Aid(
        id="barrow",
        label="wheelbarrow",
        phrase="a wheelbarrow with a sturdy wheel",
        helps_with={"schlep"},
        reduces={"dust"},
    ),
}

HERO_NAMES = ["Mira", "Elsa", "Nico", "Tobin", "Anya", "Pippa"]
HELPER_NAMES = ["Old Nan", "Bran", "Marla", "Sir Pippin", "Moss", "Wren"]
TYPES = ["girl", "boy", "princess", "prince", "child", "page"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for burden_id, burden in BURDENS.items():
            for aid_id, aid in AIDS.items():
                if burden.keyword in aid.helps_with or burden.can_share:
                    combos.append((place, burden_id, aid_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale schlep storyworld with a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--helper-type", choices=["woman", "man", "fairy", "witch", "knight", "old woman", "old man"])
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


def explain_rejection(burden: Burden, aid: Aid) -> str:
    return f"(No story: {aid.label} does not reasonably help with a {burden.weight} schlep in this tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.burden and args.aid:
        burden, aid = BURDENS[args.burden], AIDS[args.aid]
        if not (burden.keyword in aid.helps_with or burden.can_share):
            raise StoryError(explain_rejection(burden, aid))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.burden is None or c[1] == args.burden)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, burden_id, aid_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(TYPES)
    helper_type = args.helper_type or rng.choice(["woman", "man", "fairy", "knight", "old woman", "old man"])
    return StoryParams(
        place=place,
        burden=burden_id,
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type=hero_type,
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        helper_type=helper_type,
        aid=aid_id,
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    burden = BURDENS[params.burden]
    aid = AIDS[params.aid]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, meters=make_meter(), memes=make_meme()))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label=params.helper_name, meters=make_meter(), memes=make_meme()))
    burden_ent = world.add(Entity(id=burden.id, type=burden.label, label=burden.label, phrase=burden.phrase, owner=hero.id, caretaker=helper.id, meters={"delivered": 0.0}, memes={}))
    world.say(f"Once upon a time, in {setting.place}, the day began softly.")
    world.say(setting_line(setting))
    introduce(world, hero, helper)
    world.para()
    love_reason(world, hero, burden)
    do_schlep(world, hero, burden)
    world.para()
    warning(world, helper, hero, burden)
    struggle(world, hero, burden)
    aid_used = offer_aid(world, helper, hero, burden, aid)
    if aid_used:
        accept_help(world, hero, helper, burden, aid_used)
    world.para()
    resolution(world, hero, helper, burden)
    world.facts.update(hero=hero, helper=helper, burden=burden, aid=aid, setting=setting, resolved=True)
    return world


ASP_RULES = r"""
burdened(H) :- carries(H,_).
tired(H) :- burdened(H).
messy(H) :- burdened(H).
needs_help(H) :- burdened(H), awkward(H).
shared(H) :- needs_help(H), aid(A), helps(A, schlep).
happy(H) :- shared(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_bridge:
            lines.append(asp.fact("bridge", sid))
        if s.has_cart:
            lines.append(asp.fact("cart_path", sid))
    for bid, b in BURDENS.items():
        lines.append(asp.fact("burden", bid))
        lines.append(asp.fact("awkward", bid) if b.awkward else asp.fact("not_awkward", bid))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for x in sorted(a.helps_with):
            lines.append(asp.fact("helps", aid, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show burdened/1."))
    return sorted(set(asp.atoms(model, "burdened")))


def asp_verify() -> int:
    py = {(b,) for _, b, _ in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} burdens).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, burden, aid = f["hero"], f["helper"], f["burden"], f["aid"]
    return [
        QAItem(
            question=f"What did {hero.id} have to carry in the story?",
            answer=f"{hero.id} had to schlep {burden.phrase} toward {burden.destination}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the heavy errand?",
            answer=f"{helper.id} helped by bringing {aid.phrase}, so they could share the load.",
        ),
        QAItem(
            question=f"Why did the story end happily?",
            answer=f"It ended happily because {hero.id} was not alone anymore, the burden was delivered safely, and the friends reached the destination together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to schlep something?",
            answer="To schlep something means to carry it along, especially when it is awkward, heavy, or tiring.",
        ),
        QAItem(
            question="Why is a handcart useful?",
            answer="A handcart is useful because wheels can help move heavy things with less carrying.",
        ),
        QAItem(
            question="What is a happy ending in a fairy tale?",
            answer="A happy ending is when the worry is solved, the important task is done, and the characters finish safely and glad.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, burden = f["hero"], f["helper"], f["burden"]
    return [
        f"Write a fairy tale about {hero.id} who must schlep {burden.phrase} and learns to accept help.",
        f"Tell a gentle story where {helper.id} helps {hero.id} with a hard errand and the ending is happy.",
        f"Write a short child-friendly fairy tale with a long road, a heavy load, and a cheerful ending.",
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
    lines.append("== (3) World questions ==")
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest", burden="basket", hero_name="Mira", hero_type="girl", helper_name="Old Nan", helper_type="old woman", aid="cart"),
    StoryParams(place="village", burden="bundle", hero_name="Nico", hero_type="boy", helper_name="Bran", helper_type="man", aid="rope"),
    StoryParams(place="hill", burden="jar", hero_name="Anya", hero_type="princess", helper_name="Wren", helper_type="fairy", aid="barrow"),
]


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


def asp_valid_stories() -> list[tuple]:
    return []


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show burdened/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"{len(asp_valid_combos())} compatible burden kinds")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: schlep of {p.burden} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
