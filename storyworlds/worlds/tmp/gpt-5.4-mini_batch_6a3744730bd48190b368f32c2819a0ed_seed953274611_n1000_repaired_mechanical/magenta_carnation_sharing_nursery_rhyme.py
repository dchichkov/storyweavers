#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/magenta_carnation_sharing_nursery_rhyme.py
==========================================================================

A small standalone storyworld for a nursery-rhyme-style sharing tale.

Premise
-------
A child has a bright magenta carnation that they want to keep, but a friend or
sibling needs a part of it for a simple shared game. The story turns on a
concrete act of sharing: a ribbon, a petal, a vase, a song, or a garden space
is divided fairly, and the ending shows the shared thing becoming more lovely,
not less.

The storyworld keeps state in two axes:
- physical meters: blossom, bloom, water, neatness, crinkle, and glow
- emotional memes: want, worry, kindness, joy, and sharing

It supports:
- default run
- -n
- --all
- --seed
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp

The prose style is child-facing and lightly rhyming, with simple rhythmic
repetition rather than forced couplets.
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
SHARING_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"bloom": 0.0, "water": 0.0, "tidy": 0.0, "crinkle": 0.0}
        if not self.memes:
            self.memes = {"want": 0.0, "worry": 0.0, "kindness": 0.0, "joy": 0.0, "sharing": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Theme:
    id: str
    scene: str
    opening: str
    sharing_need: str
    ending: str
    refrain: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Flower:
    id: str
    color: str
    kind: str
    label: str
    scent: str
    petals: int
    shareable: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class ShareMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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


def _r_bloom(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "flower":
            continue
        if e.meters["water"] >= THRESHOLD and ("bloom", e.id) not in world.fired:
            world.fired.add(("bloom", e.id))
            e.meters["bloom"] += 1
            e.meters["tidy"] += 1
            out.append("__bloom__")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    friend = world.entities.get("friend")
    flower = world.entities.get("flower")
    if not child or not friend or not flower:
        return out
    if child.memes["sharing"] >= SHARING_MIN and friend.memes["joy"] >= THRESHOLD:
        sig = ("sharing",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        flower.meters["crinkle"] += 0.5
        child.memes["joy"] += 1
        friend.memes["joy"] += 1
        out.append("__sharing__")
    return out


CAUSAL_RULES = [_r_bloom, _r_sharing]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for flower in FLOWERS:
            if not FLOWERS[flower].shareable:
                continue
            for move in SHARES:
                if SHARES[move].sense >= SHARE_SENSE_MIN:
                    combos.append((theme, flower, move))
    return combos


def rhyme(word: str) -> str:
    return {
        "magenta": "magenta",
        "carnation": "carnation",
        "sharing": "sharing",
    }.get(word, word)


def predict(world: World, move_id: str) -> dict:
    sim = world.copy()
    _do_share(sim, sim.get("child"), sim.get("friend"), sim.get("flower"), SHARES[move_id], narrate=False)
    return {
        "bloom": sim.get("flower").meters["bloom"],
        "joy": sim.get("friend").memes["joy"],
    }


def _do_share(world: World, child: Entity, friend: Entity, flower: Entity, move: ShareMove, narrate: bool = True) -> None:
    flower.meters["water"] += 1
    child.memes["sharing"] += 1
    friend.memes["joy"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, theme: Theme, child: Entity, friend: Entity, flower: Entity) -> None:
    world.say(
        f"{theme.opening} {child.id} had a {flower.color} {flower.kind}, bright as a day-sweet song."
    )
    world.say(
        f"{friend.id} came by to play, and the two of them danced in the {theme.scene} all along."
    )


def desire(world: World, child: Entity, flower: Entity, theme: Theme) -> None:
    child.memes["want"] += 1
    world.say(
        f'"Oh, mine, mine, mine," {child.id} said, holding the {flower.color} {flower.kind} tight. '
        f'But {theme.sharing_need}.'
    )


def ask_share(world: World, friend: Entity, child: Entity, move: ShareMove, flower: Flower) -> None:
    friend.memes["worry"] += 0.5
    world.say(
        f'"May I share?" asked {friend.id}. "Just a little bit, just a little bit, '
        f'of the {flower.color} {flower.kind}?"'
    )
    world.say(f"{child.id} thought of the little hurt and the little want, and the little yes of kindness.")


def choose_share(world: World, child: Entity, friend: Entity, move: ShareMove, flower: Flower) -> None:
    child.memes["kindness"] += 1
    child.memes["sharing"] += 1
    world.say(
        f'"Yes," said {child.id}, soft and slow. "{move.text.format(flower=flower.label)}."'
    )


def finish(world: World, child: Entity, friend: Entity, theme: Theme, flower: Flower) -> None:
    world.say(
        f"{theme.ending} The {flower.color} {flower.kind} shone with watered bloom, "
        f"and {child.id} and {friend.id} shared the glow."
    )
    world.say(
        f"{theme.refrain} A share for you, a share for me, and the garden kept its sweet melody."
    )


def tell(theme: Theme, flower: Flower, move: ShareMove, child_name: str = "Mina", friend_name: str = "Nico") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type="girl", role="holder"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", role="asker"))
    flower_ent = world.add(Entity(id="flower", kind="flower", type="thing", label=flower.label, tags=flower.tags))
    opening(world, theme, child, friend, flower_ent)
    world.para()
    desire(world, child, flower_ent, theme)
    ask_share(world, friend, child, move, flower)
    choose_share(world, child, friend, move, flower)
    _do_share(world, child, friend, flower_ent, move, narrate=True)
    world.para()
    finish(world, child, friend, theme, flower)
    world.facts.update(theme=theme, flower=flower, move=move, child=child, friend=friend, outcome="shared")
    return world


THEMES = {
    "nursery": Theme(
        id="nursery",
        scene="nursery-green grass",
        opening="In a little garden,",
        sharing_need="there was only one flower for two small hearts",
        ending="And so the day went soft and bright.",
        refrain="Round and round the petals went, like a merry little tent.",
    ),
    "window": Theme(
        id="window",
        scene="window-side sill",
        opening="By a sunny window,",
        sharing_need="the vase was only small enough for one blossom at first",
        ending="Then the sill looked like a tiny parade.",
        refrain="One for you and one for me, like a tune in a nursery tree.",
    ),
    "path": Theme(
        id="path",
        scene="stone-paved path",
        opening="Along the little path,",
        sharing_need="the ribbon was tied tight, and both wanted the same bright bow",
        ending="The path grew merry under the shared shine.",
        refrain="Tippy-tap, tippy-tap, sharing makes a happy clap.",
    ),
}

FLOWERS = {
    "magenta": Flower(
        id="magenta",
        color="magenta",
        kind="carnation",
        label="magenta carnation",
        scent="sweet and peppery",
        petals=12,
        shareable=True,
        tags={"magenta", "carnation", "flower"},
    ),
    "rose": Flower(
        id="rose",
        color="pink",
        kind="rose",
        label="pink rose",
        scent="soft and rosy",
        petals=8,
        shareable=True,
        tags={"flower"},
    ),
    "daisy": Flower(
        id="daisy",
        color="white",
        kind="daisy",
        label="white daisy",
        scent="fresh and clean",
        petals=20,
        shareable=True,
        tags={"flower"},
    ),
}

SHARES = {
    "vase": ShareMove(
        id="vase",
        sense=3,
        power=2,
        text="together we will place the {flower} in the vase and take turns admiring it",
        fail="tried to take turns, but the vase was too small and the petals bent",
        qa_text="placed the flower in the vase and took turns admiring it",
        tags={"sharing", "vase"},
    ),
    "ribbon": ShareMove(
        id="ribbon",
        sense=3,
        power=2,
        text="we will tie a ribbon round the {flower} and both hold one end",
        fail="tried to tie the ribbon, but it slipped and tangled",
        qa_text="tied a ribbon round the flower and both held one end",
        tags={"sharing", "ribbon"},
    ),
    "petals": ShareMove(
        id="petals",
        sense=2,
        power=1,
        text="we will share the petals in a little ring and make a flower crown",
        fail="tried to share the petals, but they crumpled before the song was done",
        qa_text="shared the petals in a little ring",
        tags={"sharing", "petals"},
    ),
}

SHARE_SENSE_MIN = 2


@dataclass
class StoryParams:
    theme: str
    flower: str
    share: str
    child: str
    friend: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style sharing story that includes the words "{f["flower"].color}" and "{f["flower"].kind}".',
        f"Tell a gentle little story where {f['child'].id} and {f['friend'].id} share a {f['flower'].label} in a sweet, musical way.",
        f'Write a child-friendly rhyme about sharing a {f["flower"].label} with a happy ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, friend, flower, theme, move = f["child"], f["friend"], f["flower"], f["theme"], f["move"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {friend.id}, two children sharing a {flower.label}."),
        ("What did they share?",
         f"They shared a {flower.label} in a small, gentle way, and that made the play feel sweeter."),
        ("How did the story end?",
         f"It ended happily, with {child.id} and {friend.id} sharing together and the {flower.label} looking brighter."),
        ("Why was sharing kind?",
         f"Sharing was kind because both children wanted the same lovely thing, and {child.id} chose to let {friend.id} enjoy it too."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What color is magenta?",
         "Magenta is a bright pink-purple color that stands out very clearly."),
        ("What is a carnation?",
         "A carnation is a flower with ruffled petals and a sweet smell."),
        ("What does sharing mean?",
         "Sharing means letting someone else use, enjoy, or have part of something too."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(theme="nursery", flower="magenta", share="vase", child="Mina", friend="Nico"),
    StoryParams(theme="window", flower="magenta", share="ribbon", child="Lila", friend="Toby"),
    StoryParams(theme="path", flower="magenta", share="petals", child="Pia", friend="Ben"),
]


def explain_rejection(flower: Flower, move: ShareMove) -> str:
    return f"(No story: the sharing move '{move.id}' is not reasonable for {flower.label}.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for fid, f in FLOWERS.items():
        lines.append(asp.fact("flower", fid))
        if f.shareable:
            lines.append(asp.fact("shareable", fid))
    for mid, m in SHARES.items():
        lines.append(asp.fact("sharemove", mid))
        lines.append(asp.fact("sense", mid, m.sense))
        lines.append(asp.fact("power", mid, m.power))
    lines.append(asp.fact("share_min", SHARE_SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(M) :- sharemove(M), sense(M,S), share_min(Min), S >= Min.
valid(T,F,M) :- theme(T), flower(F), sharemove(M), shareable(F), reasonable(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_reasonable() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable/1."))
    return sorted(m for (m,) in asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP/Python combo parity.")
        rc = 1
    else:
        print(f"OK: ASP matches Python valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: normal generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if sample.story and sample.prompts and sample.story_qa and sample.world_qa:
        print("OK: generated story contains prose and QA.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme storyworld about magenta carnation sharing."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--child")
    ap.add_argument("--friend")
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
    if args.flower and args.share:
        if SHARES[args.share].sense < SHARE_SENSE_MIN:
            raise StoryError(explain_rejection(FLOWERS[args.flower], SHARES[args.share]))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.flower is None or c[1] == args.flower)
              and (args.share is None or c[2] == args.share)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, flower, share = rng.choice(sorted(combos))
    child = args.child or rng.choice(["Mina", "Lila", "Pia", "Tess"])
    friend = args.friend or rng.choice(["Nico", "Toby", "Ben", "Noa"])
    return StoryParams(theme=theme, flower=flower, share=share, child=child, friend=friend)


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.flower not in FLOWERS or params.share not in SHARES:
        raise StoryError("(Invalid params: unknown theme, flower, or share move.)")
    theme = THEMES[params.theme]
    flower = FLOWERS[params.flower]
    move = SHARES[params.share]
    world = tell(theme, flower, move, params.child, params.friend)
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
        print(asp_program("#show valid/3.\n#show reasonable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"reasonable moves: {', '.join(asp_reasonable())}")
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t, f, m in asp_valid_combos():
            print(f"  {t:8} {f:10} {m}")
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.friend}: {p.flower} via {p.share} ({p.theme})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
