#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/quiver_kindness_myth.py
========================================================

A small myth-style storyworld about a child, a quiver, and a kind choice.

Premise
-------
A young archer carries a quiver of arrows into a quiet mythic grove. A proud
challenge tempts them to use an arrow in a hurtful way, but a kind helper
shows that the same skill can be used to mend a problem instead. The ending
proves what kindness changed: a scared creature settles, the quiver stays safe,
and the grove grows gentle again.

This is a standalone classical simulation with physical meters and emotional
memes, a Python reasonableness gate, and an inline ASP twin.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nymph"}
        male = {"boy", "father", "dad", "man", "hunter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out = []
    if world.get("sprite").meters["fear"] >= THRESHOLD:
        sig = ("fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("sprite").memes["shy"] += 1
            out.append("__fear__")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    if world.get("sprite").memes["comfort"] >= THRESHOLD:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("grove").meters["peace"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("calm", "social", _r_calm)]


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


@dataclass
class BowChoice:
    id: str
    label: str
    mood: str
    power: int
    kind: str


@dataclass
class Trouble:
    id: str
    label: str
    threat: str
    danger: int
    harmed_by_kindness: bool = True


@dataclass
class KindMove:
    id: str
    label: str
    text: str
    power: int


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    bow: str
    trouble: str
    kind_move: str
    seed: Optional[int] = None


HEROES = [("Ari", "boy"), ("Mira", "girl"), ("Niko", "boy"), ("Lena", "girl")]
HELPERS = [("Eos", "woman"), ("Orin", "man"), ("Iris", "girl"), ("Taro", "boy")]
BOWS = {
    "wood": BowChoice("wood", "a plain ash bow", "proud", 2, "bow"),
    "moon": BowChoice("moon", "a moon-carved bow", "bright", 3, "bow"),
    "reed": BowChoice("reed", "a reed bow", "eager", 1, "bow"),
}
TROUBLES = {
    "boar": Trouble("boar", "a boar in a bramble patch", "the boar keeps charging the saplings", 2),
    "owl": Trouble("owl", "a trapped owl", "the owl is tangled in thorny vines", 1),
    "fox": Trouble("fox", "a frightened fox cub", "the fox cub will not come out of the hollow log", 1),
}
KIND_MOVES = {
    "food": KindMove("food", "offer berries", "set down berries and step back slowly", 2),
    "song": KindMove("song", "sing softly", "sing a soft tune until the air feels safe", 1),
    "gate": KindMove("gate", "open the gate", "open the little gate so the creature can leave", 1),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for h in HEROES:
        for t in TROUBLES:
            for km in KIND_MOVES:
                combos.append((h[0], t, km))
    return combos


def reasonableness_gate(bow: BowChoice, trouble: Trouble) -> bool:
    return bow.power >= trouble.danger


def tell(bow: BowChoice, trouble: Trouble, kind_move: KindMove,
         hero_name: str = "Ari", hero_type: str = "boy",
         helper_name: str = "Eos", helper_type: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(helper_name, kind="character", type=helper_type, role="helper"))
    grove = world.add(Entity("grove", type="place", label="the grove"))
    quiver = world.add(Entity("quiver", type="thing", label="the quiver"))
    sprite = world.add(Entity("sprite", kind="character", type="sprite", label="the sprite"))
    world.facts.update(hero=hero, helper=helper, grove=grove, quiver=quiver, sprite=sprite,
                       bow=bow, trouble=trouble, kind_move=kind_move)

    hero.memes["pride"] = 1.0
    helper.memes["kindness"] = 2.0
    sprite.memes["fear"] = 1.0
    quiver.meters["full"] = 1.0

    world.say(
        f"Long ago, in a grove where the leaves sounded like tiny bells, {hero.id} carried "
        f"{bow.label} and a neat {quiver.label_word} at {hero.pronoun('possessive')} side."
    )
    world.say(
        f"{hero.id} and {helper.id} found {trouble.label}. {trouble.threat}."
    )

    world.para()
    hero.memes["pride"] += 1
    world.say(
        f'{hero.id} lifted {hero.pronoun("possessive")} bow. "I could shoot and scare it away," '
        f'{hero.pronoun()} said, and {hero.pronoun("possessive")} hand began to quiver.'
    )
    helper.memes["kindness"] += 1
    world.say(
        f'{helper.id} touched {helper.pronoun("possessive")} arm gently. "A true hero does not '
        f'hurt a frightened creature," {helper.pronoun()} said. "Kindness can guide the way."'
    )

    if not reasonableness_gate(bow, trouble):
        raise StoryError("This bow is too weak for the trouble; the myth needs a real turn.")

    world.para()
    world.say(
        f"Instead of sending an arrow, {hero.id} listened. {helper.id} {kind_move.text}, "
        f"and the grove grew still."
    )
    sprite.memes["comfort"] += 1
    sprite.meters["safety"] += 1
    if kind_move.id == "food":
        world.say(
            f"The sprite crept forward, sniffed the berries, and stopped trembling."
        )
    elif kind_move.id == "song":
        world.say(
            f"The song floated through the trees, and the sprite blinked away its fear."
        )
    else:
        world.say(
            f"The little gate opened with a soft click, and the sprite found its own way home."
        )
    propagate(world, narrate=False)

    world.para()
    hero.memes["pride"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.id} set the bow back in the {quiver.label_word} and smiled. "
        f"The boar or owl or fox was no longer a threat; the creature had been helped, not hurt."
    )
    world.say(
        f"By dusk, the grove was calm again, the {quiver.label_word} stayed full, and "
        f"{hero.id}'s hands no longer trembled."
    )
    world.facts["outcome"] = "kind"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child that includes the word "quiver" and a lesson about kindness.',
        f"Tell a gentle myth where {f['hero'].id} carries a quiver, meets {f['trouble'].label}, and chooses kindness instead of harm.",
        f"Write a short story in a mythic grove where a helper teaches {f['hero'].id} that real strength can be kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, trouble = f["hero"], f["helper"], f["trouble"]
    bow, km = f["bow"], f["kind_move"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {helper.id}, who meet {trouble.label} in the grove. The story follows how they choose to solve the trouble with kindness."
        ),
        QAItem(
            question=f"What did {hero.id} almost do?",
            answer=f"{hero.id} almost sent an arrow at {trouble.label}. But {helper.id} reminded {hero.pronoun('object')} that a hero can be brave without hurting anyone."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used {km.label} instead of an arrow, and that calmed the frightened creature. The kind choice changed the mood of the whole grove."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a quiver?", "A quiver is a container that holds arrows. Archers carry it so the arrows stay together and ready."),
        QAItem("What is kindness?", "Kindness means choosing to help, comfort, or be gentle with someone. It can calm fear and make a hard moment safer."),
        QAItem("What is a myth?", "A myth is an old story that often features brave people, magical places, and big lessons. Myths often teach how to be wise and good."),
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes} role={e.role}")
    return "\n".join(out)


CURATED = [
    StoryParams("Ari", "boy", "Eos", "woman", "wood", "owl", "song"),
    StoryParams("Mira", "girl", "Iris", "girl", "moon", "fox", "food"),
    StoryParams("Niko", "boy", "Orin", "man", "reed", "boar", "gate"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for hid, _ in HEROES:
        lines.append(asp.fact("hero", hid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for kid in KIND_MOVES:
        lines.append(asp.fact("kind_move", kid))
    for bid, bow in BOWS.items():
        lines.append(asp.fact("bow", bid))
        lines.append(asp.fact("power", bid, bow.power))
    for tid, tr in TROUBLES.items():
        lines.append(asp.fact("danger", tid, tr.danger))
    return "\n".join(lines)


ASP_RULES = r"""
valid(H, T, K) :- hero(H), trouble(T), kind_move(K).
good_bow(B,T) :- bow(B), trouble(T), power(B,P), danger(T,D), P >= D.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generation failed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic quiver kindness storyworld.")
    ap.add_argument("--hero", choices=[h for h, _ in HEROES])
    ap.add_argument("--helper", choices=[h for h, _ in HELPERS])
    ap.add_argument("--bow", choices=BOWS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--kind-move", choices=KIND_MOVES, dest="kind_move")
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
    hero_name, hero_type = rng.choice(HEROES)
    helper_name, helper_type = rng.choice(HELPERS)
    bow = args.bow or rng.choice(list(BOWS))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    kind_move = args.kind_move or rng.choice(list(KIND_MOVES))
    if not reasonableness_gate(BOWS[bow], TROUBLES[trouble]):
        raise StoryError("That bow is too weak for the trouble; choose a stronger one.")
    return StoryParams(args.hero or hero_name, hero_type,
                       args.helper or helper_name, helper_type,
                       bow, trouble, kind_move)


def generate(params: StoryParams) -> StorySample:
    world = tell(BOWS[params.bow], TROUBLES[params.trouble], KIND_MOVES[params.kind_move],
                 params.hero, params.hero_type, params.helper, params.helper_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos[:20]:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
