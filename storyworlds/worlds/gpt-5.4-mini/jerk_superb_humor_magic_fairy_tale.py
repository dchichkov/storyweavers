#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jerk_superb_humor_magic_fairy_tale.py
======================================================================

A tiny fairy-tale storyworld about a rude little jerk of a sprite, a superb
spell gone silly, and a kind magic that turns the joke into a gentle lesson.

The world is built from a small simulated model, not from a frozen paragraph.
State changes drive the prose: a prank causes a mess, the court reacts, and a
patient fairy fixes things with humor and a better spell.

Seed words: jerk, superb
Features: Humor, Magic
Style: Fairy Tale
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy", "woman", "princess"}
        male = {"boy", "father", "king", "wizard", "man", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"queen": "queen", "king": "king", "fairy": "fairy", "wizard": "wizard"}.get(self.type, self.type)


@dataclass
class Realm:
    id: str
    place: str
    audience: str
    delight: str
    oddity: str
    ending: str


@dataclass
class Mischief:
    id: str
    label: str
    feat: str
    trick: str
    mess: str
    target: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    spell: str
    effect: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
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
class StoryParams:
    realm: str
    mischief: str
    magic: str
    response: str
    hero: str
    hero_gender: str
    fairy: str
    fairy_gender: str
    ruler: str
    ruler_gender: str
    seed: Optional[int] = None


REALMS = {
    "grove": Realm("grove", "the moonlit grove", "little owl-girls and beetle-boys", "a laugh and a song", "a crooked joke", "a bright ending"),
    "castle": Realm("castle", "the castle hall", "young pages and ribbon-sprites", "a fancy feast", "a silly echo", "a tidy ending"),
    "meadow": Realm("meadow", "the sunny meadow", "tiny foxes and dandelion sprites", "a picnic and a dance", "a windy prank", "a cheerful ending"),
}

MISCHIEFS = {
    "spoon": Mischief("spoon", "a silver spoon", "the spoon", "made the soup jump", "soup on the rug", "the king's supper", {"soup", "humor"}),
    "bell": Mischief("bell", "the dinner bell", "the bell", "rang it a hundred times", "a loud ringing", "the court's ears", {"noise", "humor"}),
    "ink": Mischief("ink", "the ink pot", "the ink pot", "tipped it with a wink", "blue spots everywhere", "the queen's page", {"ink", "humor"}),
}

MAGICS = {
    "tickle": Magic("tickle", "a tickle spell", "tweedle-tap", "made everyone giggle", "turned grumps into grinters", {"humor", "magic"}),
    "glow": Magic("glow", "a glow spell", "little star words", "shone in a warm ring", "mended the dim corners", {"light", "magic"}),
    "bloom": Magic("bloom", "a bloom spell", "petal-pop", "made flowers rise at once", "covered the mess in blooms", {"flowers", "magic"}),
}

RESPONSES = {
    "laugh": Response("laugh", 3, 2, "laughed, twirled the broom, and swept the mess into a neat little pile", "laughed too late, and the mess kept spreading", "laughed and swept the mess into a neat little pile", {"humor"}),
    "clean": Response("clean", 3, 3, "lifted a hand, whispered a tidy charm, and cleaned the hall in a blink", "whispered the charm, but the mess was too big", "whispered a tidy charm and cleaned the hall in a blink", {"magic"}),
    "fix": Response("fix", 2, 2, "used a superb fix-it spell and set everything right again", "tried a fix-it spell, but the jar was already too full of trouble", "used a superb fix-it spell and set everything right again", {"magic", "humor"}),
    "mop": Response("mop", 2, 2, "called for buckets, mops, and a cheerful helper, and put the hall right", "called for buckets, but the mess had grown too wide", "called for buckets and mops and put the hall right", {"humor"}),
    "shush": Response("shush", 1, 1, "shushed the trouble, but that did not fix the mess at all", "shushed the trouble, but the trouble only got louder", "shushed the trouble", {"weak"}),
}

GIRL_NAMES = ["Mira", "Luna", "Pippa", "Nina", "Ivy", "Bea"]
BOY_NAMES = ["Toby", "Finn", "Owen", "Theo", "Bram", "Jasper"]
TRAITS = ["kind", "curious", "brave", "cheerful", "clever", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for realm in REALMS:
        for mis in MISCHIEFS:
            for mag in MAGICS:
                if "magic" in MAGICS[mag].tags:
                    out.append((realm, mis, mag))
    return out


def reasonableness_gate(response: Response) -> bool:
    return response.sense >= SENSE_MIN


def should_fix(mischief: Mischief) -> bool:
    return True


def fireless_predict(world: World, magic: Magic, mis: Mischief) -> dict:
    sim = world.copy()
    _do_mischief(sim, sim.get("hero"), mis, narrate=False)
    _do_magic(sim, sim.get("fairy"), magic, narrate=False)
    return {"mess": sim.get("hall").meters["mess"]}


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    hall = world.entities.get("hall")
    if not hall:
        return out
    if hall.meters["mess"] < THRESHOLD:
        return out
    sig = ("mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("ruler").memes["mischief"] += 1
    world.get("fairy").memes["concern"] += 1
    out.append("__mess__")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_mischief(world: World, hero: Entity, mis: Mischief, narrate: bool = True) -> None:
    hero.memes["mischief"] += 1
    world.get("hall").meters["mess"] += 1
    world.get("hall").meters["noise"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(f"{hero.id} was a jerk for a moment and {mis.trick}; {mis.mess} spread across the hall.")


def _do_magic(world: World, fairy: Entity, magic: Magic, narrate: bool = True) -> None:
    world.get("hall").meters["mess"] = max(0.0, world.get("hall").meters["mess"] - 1)
    fairy.memes["delight"] += 1
    if narrate:
        world.say(f"{fairy.id} spoke {magic.spell}, and {magic.effect}.")


def setup(world: World, realm: Realm, hero: Entity, fairy: Entity, ruler: Entity) -> None:
    world.add(Entity("hall", kind="place", type="place", label=realm.place))
    world.say(
        f"Once upon a time in {realm.place}, {hero.id} and {fairy.id} prepared for {realm.audience}. "
        f"The day promised {realm.delight}, though a {realm.oddity} buzzed in the air."
    )
    world.say(f"{hero.id} had a grin that looked almost superb, but {hero.id} also had a jerkish habit of poking trouble.")
    world.say(f"{fairy.id} was patient, and {ruler.id} liked a tidy hall and a fair joke.")


def tease(world: World, hero: Entity, mis: Mischief) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"Look at me," said {hero.id}, and with a jerky bow {hero.id} got hold of {mis.label}. '
        f'"This will be superb," {hero.pronoun()} said, and everyone stared.'
    )


def warn(world: World, fairy: Entity, hero: Entity, mis: Mischief, ruler: Entity) -> None:
    fairy.memes["warning"] += 1
    world.say(
        f'{fairy.id} frowned a little and said, "{hero.id}, that is no royal game. '
        f"It may seem funny, but the {mis.label} belongs back on the table.""
    )


def applaud(world: World, ruler: Entity, fairy: Entity) -> None:
    ruler.memes["approval"] += 1
    world.say(f"{ruler.id} tapped the floor with a staff and said the best magic was the kind that helped everyone.")


def rescue(world: World, ruler: Entity, response: Response, magic: Magic, mis: Mischief) -> None:
    body = response.text
    world.say(f"{ruler.id} came at once and {body}.")
    world.say(f"Then {ruler.id} added {magic.fix}, and the hall looked superb again.")


def lesson(world: World, ruler: Entity, hero: Entity, fairy: Entity, mis: Mischief) -> None:
    hero.memes["relief"] += 1
    fairy.memes["relief"] += 1
    world.say("For a moment, all was quiet.")
    world.say(
        f'Then {ruler.id} smiled and said, "A true fairy-tale joke should make a heart lighter, not the floor sticky. '
        f'{mis.label.capitalize()} are no toys for a jerkish hand."'
    )
    world.say(f"{hero.id} blushed, nodded, and helped set every chair straight.")


def ending(world: World, hero: Entity, fairy: Entity, realm: Realm, magic: Magic) -> None:
    world.say(
        f"After that, {hero.id} tried to be gentler, and {fairy.id} taught a superb little charm that made flowers ring like bells. "
        f"{realm.ending.capitalize()} waited at the door, and the day ended in laughter."
    )


def tell(realm: Realm, mischief: Mischief, magic: Magic, response: Response,
         hero_name: str = "Pip", hero_gender: str = "boy",
         fairy_name: str = "Faye", fairy_gender: str = "girl",
         ruler_name: str = "Queen Della", ruler_gender: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="hero", traits=["sly"]))
    fairy = world.add(Entity(fairy_name, kind="character", type=fairy_gender, role="helper", traits=["patient"]))
    ruler = world.add(Entity(ruler_name, kind="character", type="queen", role="ruler", traits=["wise"]))
    setup(world, realm, hero, fairy, ruler)
    world.para()
    tease(world, hero, mischief)
    warn(world, fairy, hero, mischief, ruler)
    if reasonableness_gate(response):
        _do_mischief(world, hero, mischief)
        world.para()
        rescue(world, ruler, response, magic, mischief)
        lesson(world, ruler, hero, fairy, mischief)
        world.para()
        ending(world, hero, fairy, realm, magic)
        outcome = "fixed"
    else:
        outcome = "refused"
    applaud(world, ruler, fairy)
    world.facts.update(
        hero=hero, fairy=fairy, ruler=ruler, realm=realm, mischief=mischief,
        magic=magic, response=response, outcome=outcome
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a child that includes the words "jerk" and "superb" and uses humor and magic.',
        f"Tell a magical story where {f['hero'].id} acts like a jerk for a moment, then a wise ruler and a fairy fix the trouble in a superb way.",
        f"Write a gentle fairy tale about a rude prank, a silly spell, and a happy ending with magic and humor.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, fairy, ruler = f["hero"], f["fairy"], f["ruler"]
    mis, magic = f["mischief"], f["magic"]
    return [
        ("Who is the story about?", f"It is about {hero.id}, {fairy.id}, and {ruler.id}. {hero.id} starts off rude, but the others help turn the day back into a kind one."),
        (f"What did {hero.id} do wrong?", f"{hero.id} played a jerkish trick with {mis.label}. It made the hall messy and gave everyone a problem to solve."),
        ("How was the problem fixed?", f"{ruler.id} used a {f['response'].qa_text} plan, and {fairy.id} added {magic.fix}. That made the hall superb and peaceful again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a fairy in a fairy tale?", "A fairy is a tiny magical helper who can wave, whisper spells, and help people set things right."),
        ("What does superb mean?", "Superb means really, really wonderful. It is a word for something that is extra good."),
        ("Why are jokes better when they are kind?", "Kind jokes make people smile without hurting anyone. In a fairy tale, that keeps the magic warm and happy."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("castle", "spoon", "fix", "fix", "Pip", "boy", "Faye", "girl", "Queen Della", "woman"),
    StoryParams("grove", "bell", "laugh", "laugh", "Mira", "girl", "Lumi", "girl", "King Bram", "man"),
    StoryParams("meadow", "ink", "clean", "clean", "Owen", "boy", "Nim", "girl", "Queen Della", "woman"),
]


def explain_rejection(response: Response) -> str:
    return f"(No story: response '{response.id}' is too weak for this tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld of humor and magic.")
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--mischief", choices=MISCHIEFS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--fairy")
    ap.add_argument("--ruler")
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
    if args.response and not reasonableness_gate(RESPONSES[args.response]):
        raise StoryError(explain_rejection(RESPONSES[args.response]))
    combos = [c for c in valid_combos()
              if (args.realm is None or c[0] == args.realm)
              and (args.mischief is None or c[1] == args.mischief)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    realm, mis, mag = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    fairy = args.fairy or rng.choice(["Faye", "Lumi", "Tilda", "Moss"])
    ruler = args.ruler or rng.choice(["Queen Della", "King Bram", "Queen Isolde"])
    hero_gender = "girl" if hero in GIRL_NAMES else "boy"
    fairy_gender = "girl"
    ruler_gender = "woman" if ruler.startswith("Queen") else "man"
    return StoryParams(realm, mis, mag, response, hero, hero_gender, fairy, fairy_gender, ruler, ruler_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(REALMS[params.realm], MISCHIEFS[params.mischief], MAGICS[params.magic], RESPONSES[params.response],
                 params.hero, params.hero_gender, params.fairy, params.fairy_gender, params.ruler, params.ruler_gender)
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


ASP_RULES = r"""
valid(R, M, G) :- realm(R), mischief(M), magic(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in REALMS:
        lines.append(asp.fact("realm", r))
    for m in MISCHIEFS:
        lines.append(asp.fact("mischief", m))
    for g in MAGICS:
        lines.append(asp.fact("magic", g))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        for row in asp_valid_combos():
            print("  ", row)
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
